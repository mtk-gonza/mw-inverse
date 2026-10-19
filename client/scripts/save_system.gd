class_name SaveSystem
extends RefCounted

const SAVE_PATH := "user://mw_inverse_save.json"
const PROFILE_PATH := "user://mw_inverse_targeting.json"

func save_targeting_profile(profile: Dictionary) -> bool:
	var file := FileAccess.open(PROFILE_PATH, FileAccess.WRITE)
	if file == null:
		return false
	file.store_string(JSON.stringify(profile))
	return true

func load_targeting_profile() -> Dictionary:
	if not FileAccess.file_exists(PROFILE_PATH):
		return {}
	var file := FileAccess.open(PROFILE_PATH, FileAccess.READ)
	if file == null:
		return {}
	var parsed = JSON.parse_string(file.get_as_text())
	return parsed if parsed is Dictionary else {}

func save_player(player: CharacterBody3D, inventory: Dictionary) -> bool:
	var payload := {
		"version": 1,
		"position": {
			"x": player.global_position.x,
			"y": player.global_position.y,
			"z": player.global_position.z,
		},
		"inventory": inventory,
		"state": player.export_state(),
	}
	var file := FileAccess.open(SAVE_PATH, FileAccess.WRITE)
	if file == null:
		return false
	file.store_string(JSON.stringify(payload))
	return true

func load_player(player: CharacterBody3D) -> Dictionary:
	if not FileAccess.file_exists(SAVE_PATH):
		return {"ok": false, "reason": "no_save"}
	var file := FileAccess.open(SAVE_PATH, FileAccess.READ)
	if file == null:
		return {"ok": false, "reason": "open_failed"}
	var parsed = JSON.parse_string(file.get_as_text())
	if not parsed is Dictionary or not parsed.has("position"):
		return {"ok": false, "reason": "invalid_save"}
	var saved_position: Dictionary = parsed["position"]
	player.global_position = Vector3(
		float(saved_position.get("x", 0.0)),
		float(saved_position.get("y", 1.1)),
		float(saved_position.get("z", 0.0))
	)
	return {"ok": true, "inventory": parsed.get("inventory", {}), "state": parsed.get("state", {})}
