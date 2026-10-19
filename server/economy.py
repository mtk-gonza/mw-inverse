"""Authoritative inventory, crafting and shop rules."""

from collections.abc import Callable
from typing import Any


def consume_item(player: Any, item_id: str, item_definition: Callable[[str], dict], max_energy: int) -> dict[str, Any]:
    definition = item_definition(item_id)
    if definition["kind"] != "consumable" or player.inventory.get(item_id, 0) <= 0:
        return {"ok": False, "reason": "item_not_available"}
    player.inventory[item_id] -= 1
    player.energy = min(max_energy, player.energy + int(definition.get("energy", 0)))
    player.health = min(player.max_health, player.health + int(definition.get("health", 0)))
    if player.inventory[item_id] == 0:
        del player.inventory[item_id]
    return {"ok": True, "item_id": item_id, "energy": player.energy,
            "health": player.health, "inventory": player.inventory.copy()}


def craft_item(player: Any, item_id: str, recipes: dict[str, dict]) -> dict[str, Any]:
    recipe = recipes.get(item_id)
    if recipe is None:
        return {"ok": False, "reason": "unknown_recipe"}
    if player.currency < int(recipe.get("currency", 0)):
        return {"ok": False, "reason": "insufficient_currency"}
    requirements = recipe.get("requires", {})
    if any(player.inventory.get(material, 0) < int(amount) for material, amount in requirements.items()):
        return {"ok": False, "reason": "missing_materials"}
    for material, amount in requirements.items():
        player.inventory[material] -= int(amount)
        if player.inventory[material] <= 0:
            del player.inventory[material]
    player.currency -= int(recipe.get("currency", 0))
    player.inventory[item_id] = player.inventory.get(item_id, 0) + 1
    return {"ok": True, "item_id": item_id, "currency": player.currency,
            "inventory": player.inventory.copy()}


def buy_item(player: Any, item_id: str, item_definition: Callable[[str], dict]) -> dict[str, Any]:
    definition = item_definition(item_id)
    price = int(definition.get("price", 0))
    if definition["kind"] == "unknown" or price <= 0:
        return {"ok": False, "reason": "item_unavailable"}
    if player.currency < price:
        return {"ok": False, "reason": "insufficient_currency"}
    player.currency -= price
    player.inventory[item_id] = player.inventory.get(item_id, 0) + 1
    return {"ok": True, "item_id": item_id, "currency": player.currency,
            "inventory": player.inventory.copy()}


def sell_item(player: Any, item_id: str, amount: int, item_definition: Callable[[str], dict]) -> dict[str, Any]:
    amount = max(1, min(99, amount))
    definition = item_definition(item_id)
    owned = player.inventory.get(item_id, 0)
    if definition["kind"] == "unknown" or owned < amount or int(definition.get("price", 0)) <= 0:
        return {"ok": False, "reason": "item_not_sellable"}
    player.inventory[item_id] = owned - amount
    if player.inventory[item_id] <= 0:
        del player.inventory[item_id]
    player.currency += int(definition["price"]) * amount
    return {"ok": True, "action": "sell", "item_id": item_id, "amount": amount,
            "currency": player.currency, "inventory": player.inventory.copy()}


def equip_item(player: Any, item_id: str, item_definition: Callable[[str], dict]) -> dict[str, Any]:
    definition = item_definition(item_id)
    if definition["kind"] != "weapon" or player.inventory.get(item_id, 0) <= 0:
        return {"ok": False, "reason": "item_not_available"}
    player.equipment[definition["slot"]] = item_id
    player.attack = 10 + sum(item_definition(item).get("attack", 0) for item in player.equipment.values())
    return {"ok": True, "equipment": player.equipment.copy(), "attack": player.attack,
            "inventory": player.inventory.copy()}
