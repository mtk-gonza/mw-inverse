"""Session bootstrap and persisted-player restoration."""

import secrets
import time
from collections.abc import Callable
from typing import Any


def login_request(
    player_id: str,
    *,
    players: dict[str, Any],
    session_tokens: dict[str, str],
    storage: Any,
    player_factory: Callable[..., Any],
    parties: dict[str, set[str]],
    save_state_version: int,
    initial_quests: Callable[[], dict[str, dict[str, Any]]],
) -> tuple[Any, str]:
    """Load or create a player and issue the local session token."""
    player = players.get(player_id)
    if player is None:
        saved = storage.load(player_id)
        player = player_factory(player_id=player_id)
        if saved and int(saved.get("state_version", 1)) <= save_state_version:
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
            if player.party_id not in parties:
                player.party_id = ""
            player.quests = dict(saved.get("quests", initial_quests()))
            player.inventory = dict(saved.get("inventory", {}))
            player.energy = max(0, min(100, int(saved.get("energy", player.energy))))
            player.kills = max(0, int(saved.get("kills", player.kills)))
            player.pvp_enabled = bool(saved.get("pvp_enabled", player.pvp_enabled))
            pvp_status = saved.get("pvp_status", {})
            if isinstance(pvp_status, dict):
                now = time.monotonic()
                player.pvp_mark_until = now + max(0.0, float(pvp_status.get("mark", 0.0)))
                player.pvp_skull_until = now + max(0.0, float(pvp_status.get("skull", 0.0)))
                player.pvp_timeline = [
                    dict(item) for item in pvp_status.get("timeline", [])
                    if isinstance(item, dict)
                ][-128:]
            player.discovered_shrines = [str(item) for item in saved.get("discovered_shrines", [])][:100]
            player.decor = [dict(piece) for piece in saved.get("decor", []) if isinstance(piece, dict)][:100]
            player.referral_code = str(saved.get("referral_code", ""))[:32]
            player.clan_id = str(saved.get("clan_id", ""))[:64]
            player.blocked_players = [str(item) for item in saved.get("blocked_players", [])][:100]
            player.exploration_session_generation = max(
                0, int(saved.get("exploration_session_generation", 0))
            )
            player.exploration_request_versions = {
                str(key): max(0, int(value))
                for key, value in dict(saved.get("exploration_request_versions", {})).items()
            }
        players[player_id] = player

    token = session_tokens.get(player.player_id)
    if token is None:
        token = secrets.token_urlsafe(24)
        session_tokens[player.player_id] = token
    return player, token
