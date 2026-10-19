"""Minimal authoritative local server for the vertical slice.

Protocol: one JSON object per line over TCP. This is intentionally a prototype;
production networking will require authentication, persistence and encryption.
"""

import asyncio
import json
import math
import secrets
import time
import hashlib
import hmac
import os
import ssl
import signal
import base64
import struct
from dataclasses import dataclass, field
from typing import Any

from storage import PlayerStorage
from game_data import RECIPES, item_definition
from quests import QUESTS, initial_quests
from world_data import NPCS, REGIONS, region_snapshot


HOST = os.getenv("MW_INVERSE_HOST", "127.0.0.1")
PORT = int(os.getenv("MW_INVERSE_PORT", "24500"))
PROTOCOL_VERSION = 1
SAVE_STATE_VERSION = 1
SPEED_LIMIT = 8.0
WORLD_LIMIT = 14.0
ATTACK_DISTANCE = 12.0
WORLD_OBSTACLES: tuple[tuple[float, float, float], ...] = ((0.0, 3.5, 1.2), (-6.0, -1.5, 1.0), (6.0, 1.5, 1.0))
SESSION_IDLE_SECONDS = 1800.0
MAX_ENERGY = 100
MAX_MESSAGE_BYTES = 64 * 1024
SKILLS = {
    "arcane_bolt": {"energy": 20, "damage_multiplier": 1.8, "cooldown": 1.0, "cast_seconds": 0.35},
    "guard": {"energy": 15, "damage_multiplier": 0.0, "cooldown": 3.0, "cast_seconds": 0.25},
    "frost_nova": {"energy": 35, "damage_multiplier": 2.4, "cooldown": 4.0, "slow_seconds": 3.0, "cast_seconds": 0.6},
}


@dataclass
class Player:
    player_id: str
    x: float = 0.0
    y: float = 1.1
    z: float = 0.0
    health: int = 100
    max_health: int = 100
    level: int = 1
    experience: int = 0
    attack: int = 10
    currency: int = 100
    equipment: dict[str, str] = field(default_factory=dict)
    region_id: str = "training_meadow"
    party_id: str = ""
    quests: dict[str, dict] = field(default_factory=initial_quests)
    inventory: dict[str, int] = field(default_factory=dict)
    energy: int = MAX_ENERGY
    kills: int = 0
    pvp_enabled: bool = False
    discovered_shrines: list[str] = field(default_factory=list)
    decor: list[dict[str, Any]] = field(default_factory=list)
    referral_code: str = ""
    clan_id: str = ""
    last_chat_at: float = 0.0
    guarded_until: float = 0.0
    skill_ready_at: dict[str, float] = field(default_factory=dict)
    last_seen: float = field(default_factory=time.monotonic, repr=False)
    request_cache: dict[str, dict[str, Any]] = field(default_factory=dict, repr=False)
    movement_locked_until: float = field(default=0.0, repr=False)
    blocked_players: list[str] = field(default_factory=list)

    def snapshot(self) -> dict[str, Any]:
        return {
            "state_version": 1,
            "player_id": self.player_id,
            "position": {"x": self.x, "y": self.y, "z": self.z},
            "health": self.health,
            "max_health": self.max_health,
            "level": self.level,
            "experience": self.experience,
            "attack": self.attack,
            "currency": self.currency,
            "equipment": self.equipment.copy(),
            "region_id": self.region_id,
            "party_id": self.party_id,
            "quests": self.quests.copy(),
            "inventory": self.inventory.copy(),
            "energy": self.energy,
            "kills": self.kills,
            "pvp_enabled": self.pvp_enabled,
            "discovered_shrines": list(self.discovered_shrines),
            "decor": [piece.copy() for piece in self.decor],
            "referral_code": self.referral_code,
            "clan_id": self.clan_id,
            "blocked_players": list(self.blocked_players),
        }


PLAYERS: dict[str, Player] = {}
PARTIES: dict[str, set[str]] = {}
PARTY_COUNTER = 0
CLANS: dict[str, set[str]] = {}
CLAN_COUNTER = 0
TRADE_REQUESTS: dict[str, str] = {}
TRADE_OFFERS: dict[tuple[str, str], dict[str, dict[str, int]]] = {}
SESSION_TOKENS: dict[str, str] = {}
MATCHMAKING_QUEUE: list[str] = []
MATCHES: dict[str, set[str]] = {}
MATCH_COUNTER = 0
REFRESH_TOKENS: dict[str, str] = {}
ENEMY_HEALTH: dict[str, int] = {
    "training_dummy_1": 30,
    "training_dummy_2": 30,
    "training_dummy_3": 30,
    "frost_wisp_1": 45,
    "frost_wisp_2": 45,
    "frost_guardian": 120,
}
ENEMY_POSITIONS: dict[str, dict[str, float]] = {
    "training_dummy_1": {"x": 0.0, "y": 0.8, "z": -4.0},
    "training_dummy_2": {"x": 4.0, "y": 0.8, "z": -5.0},
    "training_dummy_3": {"x": -4.0, "y": 0.8, "z": -5.0},
    "frost_wisp_1": {"x": 8.0, "y": 0.8, "z": -6.0},
    "frost_wisp_2": {"x": -8.0, "y": 0.8, "z": -6.0},
    "frost_guardian": {"x": 0.0, "y": 0.8, "z": -10.0},
}
ENEMY_RESPAWN_AT: dict[str, float] = {}
ENEMY_ATTACK_AT: dict[tuple[str, str], float] = {}
ENEMY_SLOWED_UNTIL: dict[str, float] = {}
STORAGE = PlayerStorage()
ACTIVE_WRITERS: set[asyncio.StreamWriter] = set()
WRITER_PLAYERS: dict[asyncio.StreamWriter, str] = {}
ONLINE_PLAYER_IDS: set[str] = set()
METRICS: dict[str, int] = {"messages": 0, "combat_hits": 0, "auth_success": 0, "auth_failure": 0}


def response(kind: str, **payload: Any) -> dict[str, Any]:
    return {"type": kind, "protocol_version": PROTOCOL_VERSION, **payload}


def _cached_request(player: Player, message: dict[str, Any]) -> dict[str, Any] | None:
    request_id = str(message.get("request_id", "")).strip()[:80]
    if not request_id:
        return None
    return player.request_cache.get(f"{message.get('type', '')}:{request_id}")


def _cache_request(player: Player, message: dict[str, Any], result: dict[str, Any]) -> None:
    request_id = str(message.get("request_id", "")).strip()[:80]
    if not request_id:
        return
    key = f"{message.get('type', '')}:{request_id}"
    player.request_cache[key] = result
    if len(player.request_cache) > 128:
        del player.request_cache[next(iter(player.request_cache))]


def _password_hash(username: str, password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), (username + salt).encode(), 120_000).hex()


def _safe_username(value: Any) -> str:
    return "".join(character for character in str(value).strip().lower() if character.isalnum() or character in "_-.")[:32]


def _mfa_code(secret: str, timestamp: int | None = None) -> str:
    counter = int(time.time() // 30) if timestamp is None else int(timestamp // 30)
    digest = hmac.new(base64.b32decode(secret + "=" * ((8 - len(secret) % 8) % 8)), struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 15
    number = (struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7fffffff) % 1_000_000
    return f"{number:06d}"


def presence_snapshot() -> dict[str, Any]:
    return response(
        "world_snapshot",
        players=[
            {"player_id": player.player_id, "position": {"x": player.x, "y": player.y, "z": player.z}, "party_id": player.party_id,
             "health": player.health, "max_health": player.max_health, "level": player.level}
            for player in PLAYERS.values()
            if player.player_id in ONLINE_PLAYER_IDS
        ],
        enemies=ENEMY_HEALTH.copy(),
        enemy_positions={key: value.copy() for key, value in ENEMY_POSITIONS.items()},
    )


def _region_enemy_snapshot(region_id: str) -> tuple[dict[str, int], dict[str, dict[str, float]]]:
    enemy_ids = set(REGIONS.get(region_id, {}).get("enemies", []))
    return (
        {key: value for key, value in ENEMY_HEALTH.items() if key in enemy_ids},
        {key: value.copy() for key, value in ENEMY_POSITIONS.items() if key in enemy_ids},
    )


def _blocked_by_obstacle(x: float, z: float, radius: float = 0.55) -> bool:
    return any(math.hypot(x - obstacle_x, z - obstacle_z) < obstacle_radius + radius
               for obstacle_x, obstacle_z, obstacle_radius in WORLD_OBSTACLES)


def _has_line_of_sight(start_x: float, start_z: float, end_x: float, end_z: float) -> bool:
    distance = math.hypot(end_x - start_x, end_z - start_z)
    steps = max(1, int(distance / 0.35))
    for index in range(1, steps):
        ratio = index / steps
        if _blocked_by_obstacle(start_x + (end_x - start_x) * ratio,
                                start_z + (end_z - start_z) * ratio, radius=0.0):
            return False
    return True


async def handle_message(player: Player | None, message: dict[str, Any]) -> tuple[Player | None, dict[str, Any]]:
    requested_version = message.get("protocol_version")
    if requested_version is not None and requested_version != PROTOCOL_VERSION:
        return player, response("protocol_error", ok=False, code="unsupported_protocol", expected=PROTOCOL_VERSION, received=requested_version)
    message_type = message.get("type")
    METRICS["messages"] += 1

    if player is not None:
        now = time.monotonic()
        if now - player.last_seen > SESSION_IDLE_SECONDS:
            return None, response("session_event", ok=False, reason="idle_timeout")
        player.last_seen = now

    if message_type == "health_request":
        return player, response("health_event", ok=True, status="ready", online_players=len(ONLINE_PLAYER_IDS), metrics=METRICS.copy())

    if message_type == "login_request":
        player_id = str(message.get("player_id", "local-player"))[:64]
        player = PLAYERS.get(player_id)
        if player is None:
            saved = STORAGE.load(player_id)
            player = Player(player_id=player_id)
            if saved and int(saved.get("state_version", 1)) <= SAVE_STATE_VERSION:
                position = saved.get("position", {})
                player.x = float(position.get("x", player.x))
                player.y = float(position.get("y", player.y))
                player.z = float(position.get("z", player.z))
                player.health = int(saved.get("health", player.health))
                player.max_health = int(saved.get("max_health", player.max_health))
                player.level = int(saved.get("level", player.level))
                player.experience = int(saved.get("experience", player.experience))
                player.attack = int(saved.get("attack", player.attack))
                player.currency = int(saved.get("currency", player.currency))
                player.equipment = dict(saved.get("equipment", {}))
                player.region_id = str(saved.get("region_id", player.region_id))
                player.party_id = str(saved.get("party_id", player.party_id))
                if player.party_id not in PARTIES:
                    player.party_id = ""
                player.quests = dict(saved.get("quests", initial_quests()))
                player.inventory = dict(saved.get("inventory", {}))
                player.energy = max(0, min(MAX_ENERGY, int(saved.get("energy", player.energy))))
                player.kills = max(0, int(saved.get("kills", player.kills)))
                player.pvp_enabled = bool(saved.get("pvp_enabled", player.pvp_enabled))
                player.discovered_shrines = [str(item) for item in saved.get("discovered_shrines", [])][:100]
                player.decor = [dict(piece) for piece in saved.get("decor", []) if isinstance(piece, dict)][:100]
                player.referral_code = str(saved.get("referral_code", ""))[:32]
                player.clan_id = str(saved.get("clan_id", ""))[:64]
                player.blocked_players = [str(item) for item in saved.get("blocked_players", [])][:100]
            PLAYERS[player_id] = player
        token = SESSION_TOKENS.get(player.player_id)
        if token is None:
            token = secrets.token_urlsafe(24)
            SESSION_TOKENS[player.player_id] = token
        return player, response("login_result", ok=True, token=token, state=player.snapshot())

    if message_type == "auth_register":
        username = _safe_username(message.get("username", ""))
        password = str(message.get("password", ""))
        if len(username) < 3 or len(password) < 8:
            METRICS["auth_failure"] += 1
            return None, response("auth_result", ok=False, reason="weak_credentials")
        salt = secrets.token_hex(16)
        password_hash = salt + ":" + _password_hash(username, password, salt)
        player_id = "account-" + username
        refresh = secrets.token_urlsafe(32)
        if not STORAGE.create_account(username, player_id, password_hash, hashlib.sha256(refresh.encode()).hexdigest()):
            return None, response("auth_result", ok=False, reason="username_unavailable")
        REFRESH_TOKENS[username] = refresh
        METRICS["auth_success"] += 1
        return None, response("auth_result", ok=True, username=username, player_id=player_id, refresh_token=refresh)

    if message_type == "auth_login":
        username = _safe_username(message.get("username", ""))
        account = STORAGE.account(username)
        if account is None or ":" not in account["password_hash"]:
            METRICS["auth_failure"] += 1
            return None, response("auth_result", ok=False, reason="invalid_credentials")
        if account.get("mfa_enabled") == "1" and not hmac.compare_digest(
                _mfa_code(account["mfa_secret"]), str(message.get("mfa_code", ""))):
            METRICS["auth_failure"] += 1
            return None, response("auth_result", ok=False, reason="mfa_required")
        salt, expected = account["password_hash"].split(":", 1)
        if not hmac.compare_digest(expected, _password_hash(username, str(message.get("password", "")), salt)):
            METRICS["auth_failure"] += 1
            return None, response("auth_result", ok=False, reason="invalid_credentials")
        player, login = await handle_message(None, {"type": "login_request", "player_id": account["player_id"]})
        refresh = secrets.token_urlsafe(32)
        REFRESH_TOKENS[username] = refresh
        METRICS["auth_success"] += 1
        STORAGE.update_refresh_hash(username, hashlib.sha256(refresh.encode()).hexdigest())
        return player, response("auth_result", ok=True, username=username, refresh_token=refresh,
                                token=login["token"], state=login["state"])

    if message_type == "auth_refresh":
        username = _safe_username(message.get("username", ""))
        account = STORAGE.account(username)
        supplied = str(message.get("refresh_token", ""))
        if account is None or not hmac.compare_digest(account["refresh_hash"], hashlib.sha256(supplied.encode()).hexdigest()):
            METRICS["auth_failure"] += 1
            return None, response("auth_result", ok=False, reason="invalid_refresh_token")
        player, login = await handle_message(None, {"type": "login_request", "player_id": account["player_id"]})
        return player, response("auth_result", ok=True, token=login["token"], state=login["state"])

    if player is None:
        return None, response("error", code="not_authenticated")

    supplied_token = message.get("session_token")
    if supplied_token is not None and supplied_token != SESSION_TOKENS.get(player.player_id):
        return player, response("error", code="invalid_session")

    if message_type == "auth_mfa_setup":
        username = _safe_username(player.player_id.removeprefix("account-"))
        account = STORAGE.account(username)
        if account is None:
            return player, response("auth_result", ok=False, reason="account_not_found")
        secret = base64.b32encode(secrets.token_bytes(10)).decode().rstrip("=")
        STORAGE.update_mfa(username, secret, False)
        return player, response("auth_result", ok=True, state="mfa_pending", secret=secret,
                                code=_mfa_code(secret), username=username)

    if message_type == "auth_mfa_enable":
        username = _safe_username(player.player_id.removeprefix("account-"))
        account = STORAGE.account(username)
        code = str(message.get("code", ""))
        if account is None or not account.get("mfa_secret") or not hmac.compare_digest(_mfa_code(account["mfa_secret"]), code):
            return player, response("auth_result", ok=False, reason="invalid_mfa_code")
        STORAGE.update_mfa(username, account["mfa_secret"], True)
        return player, response("auth_result", ok=True, state="mfa_enabled")

    if message_type == "world_snapshot":
        players = [
            {"player_id": other.player_id, "position": {"x": other.x, "y": other.y, "z": other.z}, "party_id": other.party_id,
             "health": other.health, "max_health": other.max_health, "level": other.level}
            for other in PLAYERS.values()
            if other.region_id == player.region_id
        ]
        enemies, enemy_positions = _region_enemy_snapshot(player.region_id)
        return player, response("world_snapshot", state=player.snapshot(), region=region_snapshot(player.region_id), enemies=enemies, enemy_positions=enemy_positions, players=players)

    if message_type == "enter_region_request":
        region_id = str(message.get("region_id", ""))
        if region_id not in REGIONS:
            return player, response("region_event", ok=False, reason="unknown_region")
        region = REGIONS[region_id]
        if not region["level_min"] <= player.level <= region["level_max"]:
            return player, response("region_event", ok=False, reason="level_restricted")
        player.region_id = region_id
        STORAGE.save(player.player_id, player.snapshot())
        return player, response("region_event", ok=True, region=region_snapshot(region_id))

    if message_type == "npc_interact":
        npc_id = str(message.get("npc_id", ""))
        npc = NPCS.get(npc_id)
        if npc is None or npc["region_id"] != player.region_id:
            return player, response("dialogue_event", ok=False, reason="npc_unavailable")
        return player, response("dialogue_event", ok=True, npc_id=npc_id, name=npc["name"], dialogue=npc["dialogue"])

    if message_type == "exploration_snapshot":
        region = REGIONS[player.region_id]
        return player, response("exploration_event", ok=True, region_id=player.region_id,
                                shrines=region.get("shrines", []), discovered=list(player.discovered_shrines),
                                hunts=[quest_id for quest_id in QUESTS if quest_id in player.quests])

    if message_type == "discover_shrine":
        shrine_id = str(message.get("shrine_id", ""))
        if shrine_id not in REGIONS[player.region_id].get("shrines", []):
            return player, response("exploration_event", ok=False, reason="unknown_shrine")
        if shrine_id not in player.discovered_shrines:
            player.discovered_shrines.append(shrine_id)
            player.experience += 10
            STORAGE.save(player.player_id, player.snapshot())
        return player, response("exploration_event", ok=True, shrine_id=shrine_id,
                                discovered=list(player.discovered_shrines), experience=player.experience)

    if message_type == "decor_place":
        if len(player.decor) >= 100:
            return player, response("decor_event", ok=False, reason="decor_limit")
        try:
            piece = {"piece_id": str(message.get("piece_id", "ice_lamp"))[:64],
                     "x": max(-10.0, min(10.0, float(message.get("x", 0)))),
                     "z": max(-10.0, min(10.0, float(message.get("z", 0)))),
                     "rotation": float(message.get("rotation", 0.0)) % 360.0}
        except (TypeError, ValueError):
            return player, response("decor_event", ok=False, reason="invalid_piece")
        player.decor.append(piece)
        STORAGE.save(player.player_id, player.snapshot())
        return player, response("decor_event", ok=True, decor=[item.copy() for item in player.decor])

    if message_type == "decor_store":
        index = int(message.get("index", -1))
        if index < 0 or index >= len(player.decor):
            return player, response("decor_event", ok=False, reason="invalid_piece")
        player.decor.pop(index)
        STORAGE.save(player.player_id, player.snapshot())
        return player, response("decor_event", ok=True, decor=[item.copy() for item in player.decor])

    if message_type == "referral_create":
        if not player.referral_code:
            player.referral_code = f"MW-{player.player_id[:8].upper()}"
            STORAGE.save(player.player_id, player.snapshot())
        return player, response("referral_event", ok=True, code=player.referral_code)

    if message_type == "matchmake_join":
        if player.player_id not in MATCHMAKING_QUEUE:
            MATCHMAKING_QUEUE.append(player.player_id)
        match_id = _try_create_match()
        if match_id:
            return player, response("matchmaking_event", ok=True, state="matched", match_id=match_id,
                                    opponents=sorted(MATCHES[match_id]))
        return player, response("matchmaking_event", ok=True, state="queued", position=MATCHMAKING_QUEUE.index(player.player_id) + 1)

    if message_type == "matchmake_leave":
        if player.player_id in MATCHMAKING_QUEUE:
            MATCHMAKING_QUEUE.remove(player.player_id)
        return player, response("matchmaking_event", ok=True, state="left")

    if message_type == "matchmake_status":
        match_id = next((mid for mid, members in MATCHES.items() if player.player_id in members), "")
        return player, response("matchmaking_event", ok=True, state="matched" if match_id else "idle", match_id=match_id)

    if message_type == "leaderboard_request":
        entries = sorted(PLAYERS.values(), key=lambda candidate: (candidate.level, candidate.kills, candidate.experience), reverse=True)
        return player, response("leaderboard_event", ok=True, entries=[
            {"player_id": candidate.player_id, "level": candidate.level, "kills": candidate.kills,
             "experience": candidate.experience}
            for candidate in entries[:20]
        ])

    if message_type == "metrics_request":
        return player, response("metrics_event", ok=True, metrics={**METRICS,
            "online_players": len(ONLINE_PLAYER_IDS), "loaded_players": len(PLAYERS)})

    if message_type == "backup_request":
        admin_key = os.getenv("MW_INVERSE_ADMIN_KEY", "")
        if not admin_key or not hmac.compare_digest(str(message.get("admin_key", "")), admin_key):
            return player, response("backup_event", ok=False, reason="admin_required")
        destination = str(message.get("destination", "server/data/backup.sqlite3"))
        if not destination.endswith(".sqlite3") or ":" in destination or destination.startswith("\\"):
            return player, response("backup_event", ok=False, reason="invalid_destination")
        return player, response("backup_event", ok=True, path=STORAGE.backup(destination))

    if message_type == "chat_message":
        now = time.monotonic()
        if now - player.last_chat_at < 0.25:
            return player, response("chat_event", ok=False, reason="rate_limited")
        text = " ".join(str(message.get("text", "")).split())[:200]
        if not text:
            return player, response("chat_event", ok=False, reason="empty_message")
        channel = str(message.get("channel", "local"))
        if channel not in {"local", "party", "clan", "whisper", "system"}:
            return player, response("chat_event", ok=False, reason="invalid_channel")
        recipient_id = str(message.get("recipient_id", "")).strip()[:64] if channel == "whisper" else ""
        if channel == "whisper" and (not recipient_id or recipient_id not in PLAYERS):
            return player, response("chat_event", ok=False, reason="recipient_unavailable")
        player.last_chat_at = now
        return player, response("chat_event", ok=True, player_id=player.player_id, text=text, channel=channel,
                                recipient_id=recipient_id)

    if message_type == "block_player":
        target_id = str(message.get("player_id", "")).strip()[:64]
        if not target_id or target_id == player.player_id:
            return player, response("social_event", ok=False, reason="invalid_player")
        if target_id not in PLAYERS:
            return player, response("social_event", ok=False, reason="player_unavailable")
        if target_id not in player.blocked_players:
            player.blocked_players.append(target_id)
        STORAGE.save(player.player_id, player.snapshot())
        return player, response("social_event", ok=True, action="blocked", player_id=target_id,
                                blocked_players=list(player.blocked_players))

    if message_type == "unblock_player":
        target_id = str(message.get("player_id", "")).strip()[:64]
        if target_id in player.blocked_players:
            player.blocked_players.remove(target_id)
        STORAGE.save(player.player_id, player.snapshot())
        return player, response("social_event", ok=True, action="unblocked", player_id=target_id,
                                blocked_players=list(player.blocked_players))

    if message_type == "consume_request":
        cached = _cached_request(player, message)
        if cached is not None:
            return player, cached
        item_id = str(message.get("item_id", ""))
        definition = item_definition(item_id)
        if definition["kind"] != "consumable" or player.inventory.get(item_id, 0) <= 0:
            return player, response("item_event", ok=False, reason="item_not_available")
        player.inventory[item_id] -= 1
        player.energy = min(MAX_ENERGY, player.energy + int(definition.get("energy", 0)))
        player.health = min(player.max_health, player.health + int(definition.get("health", 0)))
        if player.inventory[item_id] == 0:
            del player.inventory[item_id]
        STORAGE.save(player.player_id, player.snapshot())
        result = response("item_event", ok=True, item_id=item_id, energy=player.energy, health=player.health, inventory=player.inventory.copy())
        _cache_request(player, message, result)
        return player, result

    if message_type == "craft_request":
        item_id = str(message.get("item_id", ""))
        recipe = RECIPES.get(item_id)
        if recipe is None:
            return player, response("craft_event", ok=False, reason="unknown_recipe")
        if player.currency < int(recipe.get("currency", 0)):
            return player, response("craft_event", ok=False, reason="insufficient_currency")
        requirements = recipe.get("requires", {})
        if any(player.inventory.get(material, 0) < int(amount) for material, amount in requirements.items()):
            return player, response("craft_event", ok=False, reason="missing_materials")
        for material, amount in requirements.items():
            player.inventory[material] -= int(amount)
            if player.inventory[material] <= 0:
                del player.inventory[material]
        player.currency -= int(recipe.get("currency", 0))
        player.inventory[item_id] = player.inventory.get(item_id, 0) + 1
        STORAGE.save(player.player_id, player.snapshot())
        return player, response("craft_event", ok=True, item_id=item_id, currency=player.currency, inventory=player.inventory.copy())

    if message_type == "skill_request":
        cached = _cached_request(player, message)
        if cached is not None:
            return player, cached
        skill_id = str(message.get("skill_id", ""))
        skill = SKILLS.get(skill_id)
        if skill is None:
            return player, response("skill_event", ok=False, reason="unknown_skill")
        now = time.monotonic()
        if skill_id != "guard":
            target_id = str(message.get("target_id", ""))
            if target_id not in ENEMY_HEALTH or ENEMY_HEALTH[target_id] <= 0:
                return player, response("skill_event", ok=False, reason="invalid_target")
            enemy_position = ENEMY_POSITIONS.get(target_id, {})
            if math.hypot(player.x - enemy_position.get("x", 0.0), player.z - enemy_position.get("z", 0.0)) > ATTACK_DISTANCE:
                return player, response("skill_event", ok=False, reason="target_out_of_range")
            if not _has_line_of_sight(player.x, player.z, enemy_position.get("x", 0.0), enemy_position.get("z", 0.0)):
                return player, response("skill_event", ok=False, reason="line_of_sight_blocked")
        if player.skill_ready_at.get(skill_id, 0.0) > now:
            return player, response("skill_event", ok=False, reason="cooldown", cooldown_remaining=round(player.skill_ready_at[skill_id] - now, 2))
        cost = int(skill["energy"])
        if player.energy < cost:
            return player, response("skill_event", ok=False, reason="insufficient_energy")
        player.energy -= cost
        player.skill_ready_at[skill_id] = now + float(skill["cooldown"])
        if skill_id == "guard":
            player.guarded_until = now + 3.0
            player.movement_locked_until = now + float(skill.get("cast_seconds", 0.0))
            STORAGE.save(player.player_id, player.snapshot())
            result = response("skill_event", ok=True, skill_id=skill_id, energy=player.energy, guarded=True,
                              cooldown=float(skill["cooldown"]), cast_seconds=float(skill.get("cast_seconds", 0.0)))
            _cache_request(player, message, result)
            return player, result
        damage = max(1, int(player.attack * float(skill["damage_multiplier"])))
        player.movement_locked_until = now + float(skill.get("cast_seconds", 0.0))
        METRICS["combat_hits"] += 1
        defeated = _apply_enemy_damage(player, target_id, damage)
        if skill_id == "frost_nova":
            ENEMY_SLOWED_UNTIL[target_id] = now + float(skill.get("slow_seconds", 0.0))
        if defeated:
            ENEMY_RESPAWN_AT[target_id] = time.monotonic() + 12.0
            _advance_after_defeat(player, target_id)
        loot = _enemy_loot(target_id) if defeated else {}
        STORAGE.save(player.player_id, player.snapshot())
        result = response("skill_event", ok=True, skill_id=skill_id, target_id=target_id, damage=damage,
                          remaining_health=ENEMY_HEALTH[target_id], defeated=defeated,
                          energy=player.energy, cooldown=float(skill["cooldown"]),
                          cast_seconds=float(skill.get("cast_seconds", 0.0)),
                          slow_seconds=float(skill.get("slow_seconds", 0.0)),
                          inventory=player.inventory.copy(), loot=loot, quests=player.quests.copy())
        _cache_request(player, message, result)
        return player, result

    if message_type == "pvp_toggle":
        player.pvp_enabled = bool(message.get("enabled", False))
        STORAGE.save(player.player_id, player.snapshot())
        return player, response("pvp_event", ok=True, enabled=player.pvp_enabled)

    if message_type == "respawn_request":
        player.x, player.y, player.z = 0.0, 1.1, 0.0
        player.health = player.max_health
        player.energy = MAX_ENERGY
        STORAGE.save(player.player_id, player.snapshot())
        return player, response("respawn_event", ok=True, state=player.snapshot())

    if message_type == "party_create":
        global PARTY_COUNTER
        if player.party_id:
            return player, response("party_event", ok=False, reason="already_in_party")
        PARTY_COUNTER += 1
        party_id = f"party-{PARTY_COUNTER}"
        PARTIES[party_id] = {player.player_id}
        player.party_id = party_id
        STORAGE.save(player.player_id, player.snapshot())
        return player, response("party_event", ok=True, party_id=party_id, members=sorted(PARTIES[party_id]))

    if message_type == "party_join":
        party_id = str(message.get("party_id", ""))
        if player.party_id or party_id not in PARTIES:
            return player, response("party_event", ok=False, reason="party_unavailable")
        if len(PARTIES[party_id]) >= 5:
            return player, response("party_event", ok=False, reason="party_full")
        PARTIES[party_id].add(player.player_id)
        player.party_id = party_id
        STORAGE.save(player.player_id, player.snapshot())
        return player, response("party_event", ok=True, party_id=party_id, members=sorted(PARTIES[party_id]))

    if message_type == "clan_create":
        global CLAN_COUNTER
        if getattr(player, "clan_id", ""):
            return player, response("clan_event", ok=False, reason="already_in_clan")
        CLAN_COUNTER += 1
        clan_id = f"clan-{CLAN_COUNTER}"
        CLANS[clan_id] = {player.player_id}
        player.clan_id = clan_id
        STORAGE.save(player.player_id, player.snapshot())
        return player, response("clan_event", ok=True, clan_id=clan_id, members=sorted(CLANS[clan_id]))

    if message_type == "clan_join":
        clan_id = str(message.get("clan_id", ""))
        if getattr(player, "clan_id", "") or clan_id not in CLANS:
            return player, response("clan_event", ok=False, reason="clan_unavailable")
        if len(CLANS[clan_id]) >= 20:
            return player, response("clan_event", ok=False, reason="clan_full")
        CLANS[clan_id].add(player.player_id)
        player.clan_id = clan_id
        STORAGE.save(player.player_id, player.snapshot())
        return player, response("clan_event", ok=True, clan_id=clan_id, members=sorted(CLANS[clan_id]))

    if message_type == "trade_request":
        target_id = str(message.get("target_id", ""))
        target = PLAYERS.get(target_id)
        if target is None or target_id == player.player_id or target.region_id != player.region_id:
            return player, response("trade_event", ok=False, reason="target_unavailable")
        TRADE_REQUESTS[target_id] = player.player_id
        return player, response("trade_event", ok=True, state="requested", target_id=target_id)

    if message_type == "trade_accept":
        requester_id = TRADE_REQUESTS.pop(player.player_id, "")
        if not requester_id or requester_id not in PLAYERS:
            return player, response("trade_event", ok=False, reason="trade_not_found")
        key = tuple(sorted((player.player_id, requester_id)))
        TRADE_OFFERS[key] = {player.player_id: {}, requester_id: {}}
        return player, response("trade_event", ok=True, state="opened", trade_id="|".join(key), partner_id=requester_id)

    if message_type == "trade_offer":
        partner_id = str(message.get("partner_id", ""))
        key = tuple(sorted((player.player_id, partner_id)))
        trade = TRADE_OFFERS.get(key)
        item_id = str(message.get("item_id", ""))
        amount = max(0, min(99, int(message.get("amount", 0))))
        if trade is None or item_id not in player.inventory or amount > player.inventory[item_id]:
            return player, response("trade_event", ok=False, reason="invalid_offer")
        trade[player.player_id] = {item_id: amount}
        return player, response("trade_event", ok=True, state="offered", partner_id=partner_id, offer=trade[player.player_id])

    if message_type == "trade_commit":
        cached = _cached_request(player, message)
        if cached is not None:
            return player, cached
        partner_id = str(message.get("partner_id", ""))
        key = tuple(sorted((player.player_id, partner_id)))
        trade = TRADE_OFFERS.pop(key, None)
        partner = PLAYERS.get(partner_id)
        if trade is None or partner is None:
            return player, response("trade_event", ok=False, reason="trade_not_found")
        _execute_trade(player, partner, trade)
        STORAGE.save(player.player_id, player.snapshot())
        STORAGE.save(partner.player_id, partner.snapshot())
        result = response("trade_event", ok=True, state="completed", inventory=player.inventory.copy())
        _cache_request(player, message, result)
        return player, result

    if message_type == "buy_request":
        cached = _cached_request(player, message)
        if cached is not None:
            return player, cached
        item_id = str(message.get("item_id", ""))
        definition = item_definition(item_id)
        price = int(definition.get("price", 0))
        if definition["kind"] == "unknown" or price <= 0:
            return player, response("shop_event", ok=False, reason="item_unavailable")
        if player.currency < price:
            return player, response("shop_event", ok=False, reason="insufficient_currency")
        player.currency -= price
        player.inventory[item_id] = player.inventory.get(item_id, 0) + 1
        STORAGE.save(player.player_id, player.snapshot())
        result = response("shop_event", ok=True, item_id=item_id, currency=player.currency, inventory=player.inventory.copy())
        _cache_request(player, message, result)
        return player, result

    if message_type == "sell_request":
        cached = _cached_request(player, message)
        if cached is not None:
            return player, cached
        item_id = str(message.get("item_id", ""))
        amount = max(1, min(99, int(message.get("amount", 1))))
        definition = item_definition(item_id)
        owned = player.inventory.get(item_id, 0)
        if definition["kind"] == "unknown" or owned < amount or int(definition.get("price", 0)) <= 0:
            return player, response("shop_event", ok=False, reason="item_not_sellable")
        player.inventory[item_id] = owned - amount
        if player.inventory[item_id] <= 0:
            del player.inventory[item_id]
        player.currency += int(definition["price"]) * amount
        STORAGE.save(player.player_id, player.snapshot())
        result = response("shop_event", ok=True, action="sell", item_id=item_id, amount=amount,
                          currency=player.currency, inventory=player.inventory.copy())
        _cache_request(player, message, result)
        return player, result

    if message_type == "move_intent":
        if time.monotonic() < player.movement_locked_until:
            return player, response("movement_snapshot", ok=False, reason="casting", state=player.snapshot())
        try:
            requested_dx = float(message.get("dx", 0.0))
            requested_dz = float(message.get("dz", 0.0))
        except (TypeError, ValueError):
            return player, response("error", code="invalid_movement")
        if not math.isfinite(requested_dx) or not math.isfinite(requested_dz):
            return player, response("error", code="invalid_movement")
        dx = max(-SPEED_LIMIT, min(SPEED_LIMIT, requested_dx))
        dz = max(-SPEED_LIMIT, min(SPEED_LIMIT, requested_dz))
        next_x = max(-WORLD_LIMIT, min(WORLD_LIMIT, player.x + dx))
        next_z = max(-WORLD_LIMIT, min(WORLD_LIMIT, player.z + dz))
        if _blocked_by_obstacle(next_x, next_z):
            return player, response("movement_snapshot", ok=False, reason="obstacle", state=player.snapshot())
        player.x = next_x
        player.z = next_z
        STORAGE.save(player.player_id, player.snapshot())
        return player, response("movement_snapshot", state=player.snapshot())

    if message_type == "grant_test_item":
        item_id = str(message.get("item_id", "monster_core"))[:64]
        amount = max(0, min(100, int(message.get("amount", 1))))
        player.inventory[item_id] = player.inventory.get(item_id, 0) + amount
        STORAGE.save(player.player_id, player.snapshot())
        return player, response("inventory_event", inventory=player.inventory.copy())

    if message_type == "equip_request":
        item_id = str(message.get("item_id", ""))
        definition = item_definition(item_id)
        if definition["kind"] != "weapon" or player.inventory.get(item_id, 0) <= 0:
            return player, response("equipment_event", ok=False, reason="item_not_available")
        player.equipment[definition["slot"]] = item_id
        player.attack = 10 + sum(item_definition(item).get("attack", 0) for item in player.equipment.values())
        STORAGE.save(player.player_id, player.snapshot())
        return player, response("equipment_event", ok=True, equipment=player.equipment.copy(), attack=player.attack,
                                inventory=player.inventory.copy())

    if message_type == "attack_request":
        cached = _cached_request(player, message)
        if cached is not None:
            return player, cached
        target_id = str(message.get("target_id", ""))
        if target_id not in ENEMY_HEALTH or ENEMY_HEALTH[target_id] <= 0:
            return player, response("combat_event", ok=False, reason="invalid_target")
        enemy_position = ENEMY_POSITIONS.get(target_id, {})
        if math.hypot(player.x - enemy_position.get("x", 0.0), player.z - enemy_position.get("z", 0.0)) > ATTACK_DISTANCE:
            return player, response("combat_event", ok=False, reason="target_out_of_range")
        if not _has_line_of_sight(player.x, player.z, enemy_position.get("x", 0.0), enemy_position.get("z", 0.0)):
            return player, response("combat_event", ok=False, reason="line_of_sight_blocked")
        damage = player.attack
        player.movement_locked_until = time.monotonic() + 0.2
        METRICS["combat_hits"] += 1
        defeated = _apply_enemy_damage(player, target_id, damage)
        level_up = False
        if defeated:
            ENEMY_RESPAWN_AT[target_id] = time.monotonic() + 12.0
            level_up = _advance_after_defeat(player, target_id)
        loot = _enemy_loot(target_id) if defeated else {}
        STORAGE.save(player.player_id, player.snapshot())
        result = response(
            "combat_event",
            ok=True,
            target_id=target_id,
            damage=damage,
            remaining_health=ENEMY_HEALTH[target_id],
            defeated=defeated,
            level=player.level,
            experience=player.experience,
            attack=player.attack,
            level_up=level_up,
            inventory=player.inventory.copy(),
            loot=loot,
            quests=player.quests.copy(),
        )
        _cache_request(player, message, result)
        return player, result

    if message_type == "pvp_attack":
        target_id = str(message.get("target_id", ""))
        target = PLAYERS.get(target_id)
        if (target is None or target_id == player.player_id or not player.pvp_enabled or
                not target.pvp_enabled or target.region_id != player.region_id):
            return player, response("pvp_event", ok=False, reason="pvp_unavailable")
        distance = math.hypot(player.x - target.x, player.z - target.z)
        if distance > 6.0:
            return player, response("pvp_event", ok=False, reason="target_out_of_range")
        damage = max(1, player.attack)
        if target.guarded_until > time.monotonic():
            damage = max(1, damage // 2)
        target.health = max(0, target.health - damage)
        defeated = target.health == 0
        if defeated:
            player.kills += 1
            target.x, target.y, target.z = 0.0, 1.1, 0.0
            target.health = target.max_health
        STORAGE.save(target.player_id, target.snapshot())
        STORAGE.save(player.player_id, player.snapshot())
        return player, response("pvp_event", ok=True, target_id=target_id, damage=damage,
                                defeated=defeated, target_health=target.health)

    if message_type == "world_tick":
        _respawn_enemies()
        attacks = _update_enemy_ai(player)
        return player, response("world_tick", ok=True, enemy_positions={key: value.copy() for key, value in ENEMY_POSITIONS.items()}, enemy_attacks=attacks, health=player.health)

    if message_type == "save_request":
        STORAGE.save(player.player_id, player.snapshot())
        return player, response("save_ack", state=player.snapshot())

    if message_type == "journal_request":
        return player, response("journal_event", ok=True, entries=STORAGE.journal(player.player_id, int(message.get("limit", 10))))

    return player, response("error", code="unknown_message", message_type=message_type)


def _apply_enemy_damage(player: Player, target_id: str, damage: int) -> bool:
    """Apply a validated server-side hit and grant rewards exactly once."""
    was_alive = ENEMY_HEALTH[target_id] > 0
    ENEMY_HEALTH[target_id] = max(0, ENEMY_HEALTH[target_id] - max(1, damage))
    defeated = was_alive and ENEMY_HEALTH[target_id] == 0
    if defeated:
        for item_id, amount in _enemy_loot(target_id).items():
            player.inventory[item_id] = player.inventory.get(item_id, 0) + amount
    return defeated


def _enemy_loot(target_id: str) -> dict[str, int]:
    if target_id == "frost_guardian":
        return {"monster_core": 1, "ice_shard": 4, "frost_core": 1}
    if target_id.startswith("frost_"):
        return {"monster_core": 1, "ice_shard": 2}
    return {"monster_core": 1}


def _respawn_enemies() -> None:
    now = time.monotonic()
    for enemy_id, respawn_at in list(ENEMY_RESPAWN_AT.items()):
        if now < respawn_at:
            continue
        ENEMY_HEALTH[enemy_id] = 120 if enemy_id == "frost_guardian" else 45 if enemy_id.startswith("frost_wisp") else 30
        ENEMY_RESPAWN_AT.pop(enemy_id, None)


def _advance_after_defeat(player: Player, target_id: str) -> bool:
    previous_level = player.level
    player.kills += 1
    player.experience += 25
    for quest_id, quest in QUESTS.items():
        progress = player.quests.setdefault(quest_id, {"progress": 0, "completed": False})
        if not progress["completed"] and target_id.startswith(quest["target"]):
            progress["progress"] = min(quest["goal"], int(progress["progress"]) + 1)
            if progress["progress"] >= quest["goal"]:
                progress["completed"] = True
                player.experience += quest["experience_reward"]
    while player.experience >= player.level * 100:
        player.experience -= player.level * 100
        player.level += 1
        player.max_health += 10
        player.health = player.max_health
        player.attack += 2
    return player.level > previous_level


def _execute_trade(player: Player, partner: Player, trade: dict[str, dict[str, int]]) -> None:
    for owner, recipient in ((player, partner), (partner, player)):
        for item_id, amount in trade.get(owner.player_id, {}).items():
            owner.inventory[item_id] -= amount
            if owner.inventory[item_id] <= 0:
                del owner.inventory[item_id]
            recipient.inventory[item_id] = recipient.inventory.get(item_id, 0) + amount


def _update_enemy_ai(player: Player) -> list[dict[str, Any]]:
    attacks: list[dict[str, Any]] = []
    now = time.monotonic()
    for enemy_id, position in ENEMY_POSITIONS.items():
        if ENEMY_HEALTH.get(enemy_id, 0) <= 0:
            continue
        dx = player.x - position["x"]
        dz = player.z - position["z"]
        distance = math.hypot(dx, dz)
        if 1.5 < distance < 12.0:
            speed_factor = 0.45 if ENEMY_SLOWED_UNTIL.get(enemy_id, 0.0) > now else 1.0
            step = min(0.12 * speed_factor, (distance - 1.5) / max(distance, 0.001))
            position["x"] += dx / distance * step
            position["z"] += dz / distance * step
        if distance <= 1.7:
            cooldown_key = (player.player_id, enemy_id)
            if ENEMY_ATTACK_AT.get(cooldown_key, 0.0) <= now and player.health > 0:
                base_damage = 10 if enemy_id == "frost_guardian" else 4
                damage = base_damage // 2 if player.guarded_until > now else base_damage
                player.health = max(0, player.health - max(1, damage))
                ENEMY_ATTACK_AT[cooldown_key] = now + (2.5 if enemy_id == "frost_guardian" else 1.8)
                attacks.append({"enemy_id": enemy_id, "damage": damage, "health": player.health})
    if attacks:
        STORAGE.save(player.player_id, player.snapshot())
    return attacks


def _try_create_match() -> str:
    global MATCH_COUNTER
    if len(MATCHMAKING_QUEUE) < 2:
        return ""
    first = MATCHMAKING_QUEUE.pop(0)
    second = MATCHMAKING_QUEUE.pop(0)
    MATCH_COUNTER += 1
    match_id = f"arena-{MATCH_COUNTER}"
    MATCHES[match_id] = {first, second}
    return match_id


async def client_connected(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    player: Player | None = None
    try:
        while line := await reader.readline():
            if len(line) > MAX_MESSAGE_BYTES:
                result = response("error", code="message_too_large")
                writer.write((json.dumps(result, separators=(",", ":")) + "\n").encode())
                await writer.drain()
                break
            try:
                message = json.loads(line)
                if not isinstance(message, dict):
                    raise ValueError("message must be an object")
                player, result = await handle_message(player, message)
            except (ValueError, TypeError, json.JSONDecodeError) as error:
                result = response("error", code="invalid_message", detail=str(error))
            if player is not None:
                ACTIVE_WRITERS.add(writer)
                WRITER_PLAYERS[writer] = player.player_id
                ONLINE_PLAYER_IDS.add(player.player_id)
            encoded = (json.dumps(result, separators=(",", ":")) + "\n").encode()
            if result.get("type") == "chat_event" and result.get("ok", False):
                for recipient in list(ACTIVE_WRITERS):
                    recipient_player = PLAYERS.get(WRITER_PLAYERS.get(recipient, ""))
                    if not _chat_recipient_allowed(player, recipient_player, result.get("channel", "local"), result.get("recipient_id", "")):
                        continue
                    try:
                        recipient.write(encoded)
                        await recipient.drain()
                    except (ConnectionError, OSError):
                        ACTIVE_WRITERS.discard(recipient)
            elif result.get("type") == "movement_snapshot":
                writer.write(encoded)
                await writer.drain()
                presence = (json.dumps(presence_snapshot(), separators=(",", ":")) + "\n").encode()
                for recipient in list(ACTIVE_WRITERS):
                    try:
                        recipient.write(presence)
                        await recipient.drain()
                    except (ConnectionError, OSError):
                        ACTIVE_WRITERS.discard(recipient)
            else:
                writer.write(encoded)
                await writer.drain()
    finally:
        ACTIVE_WRITERS.discard(writer)
        WRITER_PLAYERS.pop(writer, None)
        if player is not None and not any(
            session_player == player.player_id for session_player in ONLINE_PLAYER_IDS if session_player != player.player_id
        ):
            ONLINE_PLAYER_IDS.discard(player.player_id)
        writer.close()
        try:
            await writer.wait_closed()
        except (ConnectionError, OSError):
            # The peer may already have closed its socket during shutdown.
            pass


def _chat_recipient_allowed(sender: Player, recipient: Player | None, channel: str, recipient_id: str = "") -> bool:
    if recipient is None:
        return False
    if sender.player_id in recipient.blocked_players:
        return False
    if channel == "system":
        return True
    if channel == "whisper":
        return recipient.player_id in {sender.player_id, recipient_id}
    if channel == "party":
        return bool(sender.party_id and sender.party_id == recipient.party_id)
    if channel == "clan":
        return bool(sender.clan_id and sender.clan_id == recipient.clan_id)
    return sender.region_id == recipient.region_id


async def main() -> None:
    ssl_context = None
    certificate = os.getenv("MW_INVERSE_TLS_CERT", "")
    private_key = os.getenv("MW_INVERSE_TLS_KEY", "")
    if certificate and private_key:
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain(certificate, private_key)
    server = await asyncio.start_server(client_connected, HOST, PORT, ssl=ssl_context)
    addresses = ", ".join(str(sock.getsockname()) for sock in server.sockets or [])
    print(f"MW Inverse server listening on {addresses}")
    shutdown = asyncio.Event()
    loop = asyncio.get_running_loop()
    for shutdown_signal in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(shutdown_signal, shutdown.set)
        except (NotImplementedError, RuntimeError):
            pass
    async with server:
        await shutdown.wait()
    for writer in list(ACTIVE_WRITERS):
        writer.close()
    await asyncio.gather(*(writer.wait_closed() for writer in list(ACTIVE_WRITERS)), return_exceptions=True)
    ACTIVE_WRITERS.clear()
    WRITER_PLAYERS.clear()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
