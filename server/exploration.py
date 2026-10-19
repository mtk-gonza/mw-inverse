"""Authoritative exploration and persistent-world interactions."""

from typing import Any


def enter_region(player: Any, region_id: str, regions: dict[str, dict]) -> dict[str, Any]:
    if region_id not in regions:
        return {"ok": False, "reason": "unknown_region"}
    region = regions[region_id]
    if not region["level_min"] <= player.level <= region["level_max"]:
        return {"ok": False, "reason": "level_restricted"}
    player.region_id = region_id
    return {"ok": True, "region": {"region_id": region_id, **region}}


def discover_shrine(player: Any, shrine_id: str, regions: dict[str, dict]) -> dict[str, Any]:
    if shrine_id not in regions[player.region_id].get("shrines", []):
        return {"ok": False, "reason": "unknown_shrine"}
    if shrine_id not in player.discovered_shrines:
        player.discovered_shrines.append(shrine_id)
        player.experience += 10
    return {"ok": True, "shrine_id": shrine_id,
            "discovered": list(player.discovered_shrines), "experience": player.experience}


def place_decor(player: Any, piece_id: str, x: Any, z: Any, rotation: Any) -> dict[str, Any]:
    if len(player.decor) >= 100:
        return {"ok": False, "reason": "decor_limit"}
    try:
        piece = {
            "piece_id": str(piece_id)[:64],
            "x": max(-10.0, min(10.0, float(x))),
            "z": max(-10.0, min(10.0, float(z))),
            "rotation": float(rotation) % 360.0,
        }
    except (TypeError, ValueError):
        return {"ok": False, "reason": "invalid_piece"}
    player.decor.append(piece)
    return {"ok": True, "decor": [item.copy() for item in player.decor]}


def store_decor(player: Any, index: int) -> dict[str, Any]:
    if index < 0 or index >= len(player.decor):
        return {"ok": False, "reason": "invalid_piece"}
    player.decor.pop(index)
    return {"ok": True, "decor": [item.copy() for item in player.decor]}


def create_referral(player: Any) -> dict[str, Any]:
    if not player.referral_code:
        player.referral_code = f"MW-{player.player_id[:8].upper()}"
    return {"ok": True, "code": player.referral_code}
