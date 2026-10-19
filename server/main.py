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
import base64
import os
import ssl
import signal
from dataclasses import dataclass, field
from typing import Any

from storage import PlayerStorage
from game_data import RECIPES, item_definition
from quests import QUESTS, initial_quests
from auth import mfa_code as _mfa_code
from auth import password_hash as _password_hash
from auth import safe_username as _safe_username
from combat import apply_enemy_damage as _combat_apply_enemy_damage
from combat import enemy_loot as _enemy_loot
from economy import buy_item, consume_item, craft_item, equip_item, sell_item
from exploration import create_referral, discover_shrine, enter_region, place_decor, store_decor
from progression import advance_after_defeat, try_create_match
from pvp import record_attack as _pvp_record_attack
from pvp import status_snapshot as _pvp_status_snapshot
from session import login_request
from social import accept_trade, commit_trade, create_clan, create_party, join_clan, join_party, offer_trade, request_trade
from world_simulation import respawn_enemies, update_enemy_ai
import transport
from world_data import NPCS, REGIONS, region_snapshot
from world_rules import blocked_by_obstacle, has_line_of_sight


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
    pvp_mark_until: float = field(default=0.0, repr=False)
    pvp_skull_until: float = field(default=0.0, repr=False)
    pvp_timeline: list[dict[str, Any]] = field(default_factory=list, repr=False)
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
    exploration_session_generation: int = 0
    exploration_request_versions: dict[str, int] = field(default_factory=dict)

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
            "pvp_status": _pvp_status_snapshot(self),
            "discovered_shrines": list(self.discovered_shrines),
            "decor": [piece.copy() for piece in self.decor],
            "referral_code": self.referral_code,
            "clan_id": self.clan_id,
            "blocked_players": list(self.blocked_players),
            "exploration_session_generation": self.exploration_session_generation,
            "exploration_request_versions": self.exploration_request_versions.copy(),
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
    return blocked_by_obstacle(WORLD_OBSTACLES, x, z, radius)


def _has_line_of_sight(start_x: float, start_z: float, end_x: float, end_z: float) -> bool:
    return has_line_of_sight(WORLD_OBSTACLES, start_x, start_z, end_x, end_z)


async def handle_message(player: Player | None, message: dict[str, Any]) -> tuple[Player | None, dict[str, Any]]:
    global MATCH_COUNTER
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
        player, token = login_request(
            player_id,
            players=PLAYERS,
            session_tokens=SESSION_TOKENS,
            storage=STORAGE,
            player_factory=Player,
            parties=PARTIES,
            save_state_version=SAVE_STATE_VERSION,
            initial_quests=initial_quests,
        )
        player.exploration_session_generation += 1
        player.exploration_request_versions.clear()
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
        result = enter_region(player, region_id, REGIONS)
        if not result["ok"]:
            return player, response("region_event", **result)
        STORAGE.save(player.player_id, player.snapshot())
        return player, response("region_event", **result)

    if message_type == "npc_interact":
        npc_id = str(message.get("npc_id", ""))
        npc = NPCS.get(npc_id)
        if npc is None or npc["region_id"] != player.region_id:
            return player, response("dialogue_event", ok=False, reason="npc_unavailable")
        return player, response("dialogue_event", ok=True, npc_id=npc_id, name=npc["name"], dialogue=npc["dialogue"])

    if message_type == "exploration_snapshot":
        request_version = int(message.get("request_version", 0))
        current_version = player.exploration_request_versions.get("snapshot", 0)
        if request_version and request_version < current_version:
            return player, response("exploration_event", ok=False, reason="stale_request",
                                    session_generation=player.exploration_session_generation,
                                    request_version=current_version)
        if request_version:
            player.exploration_request_versions["snapshot"] = request_version
        region = REGIONS[player.region_id]
        return player, response("exploration_event", ok=True, region_id=player.region_id,
                                shrines=region.get("shrines", []), discovered=list(player.discovered_shrines),
                                hunts=[quest_id for quest_id in QUESTS if quest_id in player.quests],
                                session_generation=player.exploration_session_generation,
                                request_version=player.exploration_request_versions.get("snapshot", 0))

    if message_type == "discover_shrine":
        shrine_id = str(message.get("shrine_id", ""))
        already_discovered = shrine_id in player.discovered_shrines
        result = discover_shrine(player, shrine_id, REGIONS)
        if not result["ok"]:
            return player, response("exploration_event", **result)
        if not already_discovered:
            STORAGE.save(player.player_id, player.snapshot())
        return player, response("exploration_event", **result)

    if message_type == "decor_place":
        result = place_decor(player, message.get("piece_id", "ice_lamp"), message.get("x", 0), message.get("z", 0), message.get("rotation", 0.0))
        if not result["ok"]:
            return player, response("decor_event", **result)
        STORAGE.save(player.player_id, player.snapshot())
        return player, response("decor_event", **result)

    if message_type == "decor_store":
        result = store_decor(player, int(message.get("index", -1)))
        if not result["ok"]:
            return player, response("decor_event", **result)
        STORAGE.save(player.player_id, player.snapshot())
        return player, response("decor_event", **result)

    if message_type == "referral_create":
        had_referral = bool(player.referral_code)
        result = create_referral(player)
        if not had_referral:
            STORAGE.save(player.player_id, player.snapshot())
        return player, response("referral_event", **result)

    if message_type == "matchmake_join":
        if player.player_id not in MATCHMAKING_QUEUE:
            MATCHMAKING_QUEUE.append(player.player_id)
        match_id, MATCH_COUNTER = try_create_match(MATCHMAKING_QUEUE, MATCHES, MATCH_COUNTER)
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
        result = consume_item(player, item_id, item_definition, MAX_ENERGY)
        if not result["ok"]:
            return player, response("item_event", **result)
        STORAGE.save(player.player_id, player.snapshot())
        event = response("item_event", **result)
        _cache_request(player, message, event)
        return player, event

    if message_type == "craft_request":
        item_id = str(message.get("item_id", ""))
        result = craft_item(player, item_id, RECIPES)
        if not result["ok"]:
            return player, response("craft_event", **result)
        STORAGE.save(player.player_id, player.snapshot())
        return player, response("craft_event", **result)

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
            advance_after_defeat(player, target_id, QUESTS)
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
        return player, response("pvp_event", ok=True, enabled=player.pvp_enabled,
                                pvp_status=_pvp_status_snapshot(player))

    if message_type == "respawn_request":
        player.x, player.y, player.z = 0.0, 1.1, 0.0
        player.health = player.max_health
        player.energy = MAX_ENERGY
        STORAGE.save(player.player_id, player.snapshot())
        return player, response("respawn_event", ok=True, state=player.snapshot())

    if message_type == "party_create":
        global PARTY_COUNTER
        result, PARTY_COUNTER = create_party(player, PARTIES, PARTY_COUNTER)
        if not result["ok"]:
            return player, response("party_event", **result)
        STORAGE.save(player.player_id, player.snapshot())
        return player, response("party_event", **result)

    if message_type == "party_join":
        party_id = str(message.get("party_id", ""))
        result = join_party(player, party_id, PARTIES)
        if not result["ok"]:
            return player, response("party_event", **result)
        STORAGE.save(player.player_id, player.snapshot())
        return player, response("party_event", **result)

    if message_type == "clan_create":
        global CLAN_COUNTER
        result, CLAN_COUNTER = create_clan(player, CLANS, CLAN_COUNTER)
        if not result["ok"]:
            return player, response("clan_event", **result)
        STORAGE.save(player.player_id, player.snapshot())
        return player, response("clan_event", **result)

    if message_type == "clan_join":
        clan_id = str(message.get("clan_id", ""))
        result = join_clan(player, clan_id, CLANS)
        if not result["ok"]:
            return player, response("clan_event", **result)
        STORAGE.save(player.player_id, player.snapshot())
        return player, response("clan_event", **result)

    if message_type == "trade_request":
        target_id = str(message.get("target_id", ""))
        result = request_trade(player, target_id, PLAYERS, TRADE_REQUESTS)
        return player, response("trade_event", **result)

    if message_type == "trade_accept":
        result = accept_trade(player, PLAYERS, TRADE_REQUESTS, TRADE_OFFERS)
        return player, response("trade_event", **result)

    if message_type == "trade_offer":
        partner_id = str(message.get("partner_id", ""))
        item_id = str(message.get("item_id", ""))
        amount = int(message.get("amount", 0))
        result = offer_trade(player, partner_id, item_id, amount, TRADE_OFFERS)
        return player, response("trade_event", **result)

    if message_type == "trade_commit":
        cached = _cached_request(player, message)
        if cached is not None:
            return player, cached
        partner_id = str(message.get("partner_id", ""))
        result = commit_trade(player, partner_id, PLAYERS, TRADE_OFFERS)
        if not result["ok"]:
            return player, response("trade_event", **result)
        partner = result.pop("partner")
        STORAGE.save(player.player_id, player.snapshot())
        STORAGE.save(partner.player_id, partner.snapshot())
        event = response("trade_event", **result)
        _cache_request(player, message, event)
        return player, event

    if message_type == "buy_request":
        cached = _cached_request(player, message)
        if cached is not None:
            return player, cached
        item_id = str(message.get("item_id", ""))
        result = buy_item(player, item_id, item_definition)
        if not result["ok"]:
            return player, response("shop_event", **result)
        STORAGE.save(player.player_id, player.snapshot())
        event = response("shop_event", **result)
        _cache_request(player, message, event)
        return player, event

    if message_type == "sell_request":
        cached = _cached_request(player, message)
        if cached is not None:
            return player, cached
        item_id = str(message.get("item_id", ""))
        amount = int(message.get("amount", 1))
        result = sell_item(player, item_id, amount, item_definition)
        if not result["ok"]:
            return player, response("shop_event", **result)
        STORAGE.save(player.player_id, player.snapshot())
        event = response("shop_event", **result)
        _cache_request(player, message, event)
        return player, event

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
        result = equip_item(player, item_id, item_definition)
        if not result["ok"]:
            return player, response("equipment_event", **result)
        STORAGE.save(player.player_id, player.snapshot())
        return player, response("equipment_event", **result)

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
            level_up = advance_after_defeat(player, target_id, QUESTS)
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
        _pvp_record_attack(player, target, damage, defeated)
        STORAGE.save(target.player_id, target.snapshot())
        STORAGE.save(player.player_id, player.snapshot())
        return player, response("pvp_event", ok=True, target_id=target_id, damage=damage,
                                defeated=defeated, target_health=target.health,
                                pvp_status=_pvp_status_snapshot(player),
                                target_pvp_status=_pvp_status_snapshot(target))

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
    return _combat_apply_enemy_damage(ENEMY_HEALTH, player, target_id, damage, _enemy_loot)


def _respawn_enemies() -> None:
    respawn_enemies(ENEMY_HEALTH, ENEMY_RESPAWN_AT)


def _update_enemy_ai(player: Player) -> list[dict[str, Any]]:
    return update_enemy_ai(
        player,
        ENEMY_POSITIONS,
        ENEMY_HEALTH,
        ENEMY_SLOWED_UNTIL,
        ENEMY_ATTACK_AT,
        STORAGE,
    )


async def client_connected(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    await transport.client_connected(
        reader,
        writer,
        handle_message=handle_message,
        response=response,
        presence_snapshot=presence_snapshot,
        chat_recipient_allowed=_chat_recipient_allowed,
        max_message_bytes=MAX_MESSAGE_BYTES,
        active_writers=ACTIVE_WRITERS,
        writer_players=WRITER_PLAYERS,
        online_player_ids=ONLINE_PLAYER_IDS,
        players=PLAYERS,
    )


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
