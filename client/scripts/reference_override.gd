class_name ReferenceOverride
extends RefCounted

## Private, local-only asset bridge. It never copies reference files into the project.
## Configure user://mw_inverse_reference_override.json with {"root": "..."} or
## set MW_INVERSE_REFERENCE_ROOT before starting Godot.

const CONFIG_PATH := "user://mw_inverse_reference_override.json"
const DEFAULT_PRIVATE_ROOT := "res://assets/reference-private"
const DEFAULT_ROOT := "C:/Users/gonzalo.gonzalez/AppData/Local/MagicWingsBOTeado/current"
const IMAGE_EXTENSIONS := ["png", "jpg", "jpeg", "webp"]
const DEFAULT_SLOTS := {
	"player_avatar": "player.png",
	"npc_mentor_arin": "player.png",
	"npc_quartermaster_lynn": "player.png",
	"npc_warden_sela": "player.png",
	"enemy_fire": "monster.png",
	"enemy_frost": "monster.png",
	"target_ring": "AutoTargetRing.png",
	"hit_spark": "fx_ring_soft.png",
	"spell_effect": "defaultspells.png",
	"spell_projectile": "defaultspells.png",
	"attack_projectile": "autoattack_nearest.png",
	"guard_effect": "shieldAndHeal.png",
	"loot": "batwing.png",
	"portal": "destination.png",
	"shrine": "shrine.png",
}
const PROJECT_SLOTS := {
	"player_avatar": "res://assets/slots/characters/player_avatar.png",
	"npc_mentor_arin": "res://assets/slots/characters/npc_mentor_arin.png",
	"npc_quartermaster_lynn": "res://assets/slots/characters/npc_quartermaster_lynn.png",
	"npc_warden_sela": "res://assets/slots/characters/npc_warden_sela.png",
	"enemy_fire": "res://assets/slots/enemies/enemy_fire.png",
	"enemy_frost": "res://assets/slots/enemies/enemy_frost.png",
	"target_ring": "res://assets/slots/effects/target_ring.png",
	"hit_spark": "res://assets/slots/effects/hit_spark.png",
	"spell_effect": "res://assets/slots/effects/spell_effect.png",
	"spell_projectile": "res://assets/slots/effects/spell_projectile.png",
	"attack_projectile": "res://assets/slots/effects/attack_projectile.png",
	"guard_effect": "res://assets/slots/effects/guard_effect.png",
	"loot": "res://assets/slots/world/loot.png",
	"portal": "res://assets/slots/world/portal.png",
	"shrine": "res://assets/slots/world/shrine.png",
}

var root_path := ""
var slot_files: Dictionary = {}
var _indexed := false
var _files_by_name: Dictionary = {}
var _texture_cache: Dictionary = {}

func _init() -> void:
	slot_files = DEFAULT_SLOTS.duplicate()
	root_path = OS.get_environment("MW_INVERSE_REFERENCE_ROOT")
	if root_path.is_empty() and FileAccess.file_exists(CONFIG_PATH):
		var file := FileAccess.open(CONFIG_PATH, FileAccess.READ)
		var data = JSON.parse_string(file.get_as_text()) if file != null else null
		if data is Dictionary:
			root_path = str(data.get("root", ""))
			if data.get("slots", {}) is Dictionary:
				for slot in data["slots"]:
					slot_files[str(slot)] = str(data["slots"][slot])
	if root_path.is_empty():
		root_path = DEFAULT_PRIVATE_ROOT if _directory_exists(DEFAULT_PRIVATE_ROOT) else DEFAULT_ROOT
	root_path = root_path.replace("\\", "/").trim_suffix("/")

func load_slot(slot: String, fallback_path := "") -> Texture2D:
	var project_path := str(PROJECT_SLOTS.get(slot, ""))
	if not project_path.is_empty() and ResourceLoader.exists(project_path):
		var project_texture = load(project_path)
		if project_texture is Texture2D:
			return project_texture
	var configured := str(slot_files.get(slot, ""))
	if not configured.is_empty():
		var configured_texture := load_texture(configured)
		if configured_texture != null:
			return configured_texture
	return load_texture(fallback_path.get_file(), fallback_path)

func load_texture(file_name: String, fallback_path := "") -> Texture2D:
	var key := file_name.get_file()
	if _texture_cache.has(key):
		return _texture_cache[key] as Texture2D
	var external_path := _find_file(key)
	if not external_path.is_empty():
		if external_path.begins_with("res://"):
			var project_texture = load(external_path)
			if project_texture is Texture2D:
				_texture_cache[key] = project_texture
				return project_texture
		var image := Image.new()
		if image.load(external_path) == OK:
			var texture := ImageTexture.create_from_image(image)
			_texture_cache[key] = texture
			return texture
	if not fallback_path.is_empty() and ResourceLoader.exists(fallback_path):
		var fallback = load(fallback_path)
		if fallback is Texture2D:
			_texture_cache[key] = fallback
			return fallback
	return null

func has_root() -> bool:
	return _directory_exists(root_path)

func _directory_exists(path: String) -> bool:
	if path.is_empty():
		return false
	var directory := DirAccess.open(path)
	return directory != null

func _find_file(file_name: String) -> String:
	if not has_root():
		return ""
	if not _indexed:
		_index_root(root_path)
	return str(_files_by_name.get(file_name.to_lower(), ""))

func _index_root(path: String) -> void:
	_indexed = true
	_index_directory(path)

func _index_directory(path: String) -> void:
	var directory := DirAccess.open(path)
	if directory == null:
		return
	for file_name in directory.get_files():
		var extension := file_name.get_extension().to_lower()
		if extension in IMAGE_EXTENSIONS:
			var key := file_name.to_lower()
			if not _files_by_name.has(key):
				_files_by_name[key] = path.path_join(file_name)
	for child in directory.get_directories():
		_index_directory(path.path_join(child))
