class_name Inventory
extends RefCounted

## Local inventory model for the vertical slice.
## Item ownership and persistence will move to the authoritative server.

var items: Dictionary = {}

func add(item_id: String, amount: int = 1) -> void:
	if amount <= 0:
		return
	items[item_id] = int(items.get(item_id, 0)) + amount

func count(item_id: String) -> int:
	return int(items.get(item_id, 0))
