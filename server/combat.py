"""Pure combat rules shared by the authoritative message handler."""

from collections.abc import Callable
from typing import Any


def enemy_loot(target_id: str) -> dict[str, int]:
    """Return the independent prototype's reward table for an enemy."""
    if target_id == "frost_guardian":
        return {"monster_core": 1, "ice_shard": 4, "frost_core": 1}
    if target_id.startswith("frost_"):
        return {"monster_core": 1, "ice_shard": 2}
    return {"monster_core": 1}


def apply_enemy_damage(
    enemy_health: dict[str, int],
    player: Any,
    target_id: str,
    damage: int,
    loot: Callable[[str], dict[str, int]] = enemy_loot,
) -> bool:
    """Apply one validated hit and grant rewards exactly once."""
    was_alive = enemy_health[target_id] > 0
    enemy_health[target_id] = max(0, enemy_health[target_id] - max(1, damage))
    defeated = was_alive and enemy_health[target_id] == 0
    if defeated:
        for item_id, amount in loot(target_id).items():
            player.inventory[item_id] = player.inventory.get(item_id, 0) + amount
    return defeated
