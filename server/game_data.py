"""Original design data for the independent prototype."""

ITEMS = {
    "training_blade": {"kind": "weapon", "slot": "main_hand", "attack": 5, "price": 50},
    "monster_core": {"kind": "material", "slot": None, "attack": 0, "price": 0},
    "mana_potion": {"kind": "consumable", "slot": None, "energy": 30, "price": 15},
    "ice_shard": {"kind": "material", "slot": None, "attack": 0, "price": 8},
    "frost_core": {"kind": "material", "slot": None, "attack": 0, "price": 20},
    "frost_blade": {"kind": "weapon", "slot": "main_hand", "attack": 12, "price": 180},
    "health_potion": {"kind": "consumable", "slot": None, "health": 35, "price": 25},
}

RECIPES = {
    "frost_blade": {"requires": {"monster_core": 2, "ice_shard": 3}, "currency": 40},
    "health_potion": {"requires": {"ice_shard": 1}, "currency": 5},
}


def item_definition(item_id: str) -> dict:
    return ITEMS.get(item_id, {"kind": "unknown", "slot": None, "attack": 0}).copy()
