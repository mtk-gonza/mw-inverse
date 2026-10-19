class_name ContentCatalog
extends RefCounted

var regions: Dictionary = {}
var items: Dictionary = {}
var npcs: Dictionary = {}
var quests: Dictionary = {}

func load_all() -> bool:
	regions = _load_json("res://data/regions.json")
	items = _load_json("res://data/items.json")
	npcs = _load_json("res://data/npcs.json")
	quests = _load_json("res://data/quests.json")
	return not regions.is_empty() and not items.is_empty() and not npcs.is_empty() and not quests.is_empty()

func _load_json(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		push_error("Content file missing: " + path)
		return {}
	var file := FileAccess.open(path, FileAccess.READ)
	var parsed = JSON.parse_string(file.get_as_text())
	return parsed if parsed is Dictionary else {}
