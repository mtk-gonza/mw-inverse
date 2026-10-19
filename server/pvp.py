"""Authoritative PvP status and timeline rules for the local vertical slice."""

import time
from typing import Any


COMBAT_MARK_SECONDS = 60.0
SKULL_SECONDS = 60.0 * 60.0
TIMELINE_SECONDS = 24.0 * 60.0 * 60.0


def _now() -> float:
    return time.monotonic()


def _prune(player: Any, now: float) -> None:
    player.pvp_timeline = [
        entry for entry in player.pvp_timeline
        if float(entry.get("at", 0.0)) + TIMELINE_SECONDS >= now
    ][-128:]


def status_snapshot(player: Any, now: float | None = None) -> dict[str, Any]:
    now = _now() if now is None else now
    _prune(player, now)
    return {
        "enabled": bool(player.pvp_enabled),
        "mark": max(0.0, player.pvp_mark_until - now),
        "skull": max(0.0, player.pvp_skull_until - now),
        "timeline": [dict(entry) for entry in player.pvp_timeline],
    }


def record_attack(attacker: Any, target: Any, damage: int, defeated: bool,
                  now: float | None = None) -> dict[str, Any]:
    now = _now() if now is None else now
    attacker.pvp_mark_until = max(attacker.pvp_mark_until, now + COMBAT_MARK_SECONDS)
    target.pvp_mark_until = max(target.pvp_mark_until, now + COMBAT_MARK_SECONDS)
    attacker.pvp_skull_until = max(attacker.pvp_skull_until, now + SKULL_SECONDS)
    event = {"at": now, "attacker_id": attacker.player_id, "target_id": target.player_id,
             "damage": int(damage), "defeated": bool(defeated)}
    attacker.pvp_timeline.append(event)
    target.pvp_timeline.append(event)
    _prune(attacker, now)
    _prune(target, now)
    return event
