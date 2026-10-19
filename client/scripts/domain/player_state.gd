class_name PlayerState
extends RefCounted

## Serializable gameplay state, independent from Godot scene nodes.

var player_id: String = "local-player"
var position := Vector3.ZERO
var health: int = 100
var max_health: int = 100
var level: int = 1
var experience: int = 0
var attack: int = 10
var currency: int = 100
var equipment: Dictionary = {}
var quests: Dictionary = {}
var region_id: String = "training_meadow"
var party_id: String = ""
var inventory: Dictionary = {}
var energy: int = 100
var kills: int = 0
var pvp_enabled: bool = false

func to_dict() -> Dictionary:
	return {
		"player_id": player_id,
		"position": {"x": position.x, "y": position.y, "z": position.z},
		"health": health,
		"max_health": max_health,
		"level": level,
		"experience": experience,
		"attack": attack,
		"currency": currency,
		"equipment": equipment.duplicate(),
		"quests": quests.duplicate(),
		"region_id": region_id,
		"party_id": party_id,
		"inventory": inventory.duplicate(),
		"energy": energy,
		"kills": kills,
		"pvp_enabled": pvp_enabled,
	}

func from_dict(data: Dictionary) -> void:
	player_id = str(data.get("player_id", player_id))
	var raw_position: Dictionary = data.get("position", {})
	position = Vector3(float(raw_position.get("x", 0.0)), float(raw_position.get("y", 1.1)), float(raw_position.get("z", 0.0)))
	health = int(data.get("health", health))
	max_health = int(data.get("max_health", max_health))
	level = int(data.get("level", level))
	experience = int(data.get("experience", experience))
	attack = int(data.get("attack", attack))
	currency = int(data.get("currency", currency))
	equipment = data.get("equipment", {}).duplicate()
	quests = data.get("quests", {}).duplicate()
	region_id = str(data.get("region_id", region_id))
	party_id = str(data.get("party_id", party_id))
	inventory = data.get("inventory", {}).duplicate()
	energy = int(data.get("energy", energy))
	kills = int(data.get("kills", kills))
	pvp_enabled = bool(data.get("pvp_enabled", pvp_enabled))
