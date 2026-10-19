class_name ReferenceAssetLibrary
extends RefCounted

var files: Array[String] = []
var by_extension: Dictionary = {}
var by_category: Dictionary = {}
var entries: Dictionary = {}
var texture_cache: Dictionary = {}
var audio_cache: Dictionary = {}
const CACHE_LIMIT := 64

func scan(root := "res://assets/reference-library") -> Dictionary:
	files.clear()
	by_extension.clear()
	by_category.clear()
	entries.clear()
	_scan_directory(root)
	return {"files": files.size(), "by_extension": by_extension.duplicate(), "by_category": by_category.duplicate(), "categories": entries.keys()}

func load_texture(relative_path: String) -> Texture2D:
	if texture_cache.has(relative_path):
		return texture_cache[relative_path] as Texture2D
	var path := _resource_path(relative_path)
	var resource = load(path)
	if resource is Texture2D:
		_cache_resource(texture_cache, relative_path, resource)
		return resource
	return null

func load_audio(relative_path: String) -> AudioStream:
	if audio_cache.has(relative_path):
		return audio_cache[relative_path] as AudioStream
	var path := _resource_path(relative_path)
	var resource = load(path)
	if resource is AudioStream:
		_cache_resource(audio_cache, relative_path, resource)
		return resource
	return null

func _scan_directory(path: String) -> void:
	var directory := DirAccess.open(path)
	if directory == null:
		return
	for entry in directory.get_files():
		var extension := entry.get_extension().to_lower()
		if extension == "import" or entry.ends_with(".json"):
			continue
		var relative_path := path.trim_prefix("res://assets/reference-library/") + "/" + entry
		files.append(relative_path)
		by_extension[extension] = int(by_extension.get(extension, 0)) + 1
		var category := _category_for(entry)
		by_category[category] = int(by_category.get(category, 0)) + 1
		if not entries.has(category):
			entries[category] = []
		entries[category].append(relative_path)
	for entry in directory.get_directories():
		_scan_directory(path + "/" + entry)

func _category_for(file_name: String) -> String:
	var value := file_name.to_lower()
	if value.ends_with(".wav"):
		if value.contains("music") or value.contains("magic_wings") or value.contains("banner"):
			return "audio_music"
		if value.contains("button") or value.contains("confirm") or value.contains("interface"):
			return "audio_ui"
		if value.contains("beast") or value.contains("creature") or value.contains("monster"):
			return "audio_creature"
		return "audio"
	if value.contains("map") or value.contains("background"):
		return "map"
	if value.contains("health") or value.contains("mana") or value.contains("button") or value.contains("panel"):
		return "hud"
	if value.contains("spell") or value.contains("attack") or value.contains("magic") or value.contains("sword"):
		return "combat"
	if value.contains("player") or value.contains("character") or value.contains("wing") or value.contains("avatar"):
		return "character"
	if value.contains("achievement") or value.contains("guild") or value.contains("rank"):
		return "progression"
	if value.contains("effect") or value.contains("particle") or value.contains("glow"):
		return "effects"
	return "unknown"

func category_files(category: String) -> Array:
	return entries.get(category, []).duplicate()

func resolve_texture(category: String, fallback_path: String = "") -> Texture2D:
	for relative_path in category_files(category):
		if str(relative_path).get_extension().to_lower() == "png":
			var texture := load_texture(relative_path)
			if texture != null:
				return texture
	return load_texture(fallback_path) if not fallback_path.is_empty() else null

func resolve_audio(category: String, fallback_path: String = "") -> AudioStream:
	for relative_path in category_files(category):
		if str(relative_path).get_extension().to_lower() == "wav":
			var audio := load_audio(relative_path)
			if audio != null:
				return audio
	return load_audio(fallback_path) if not fallback_path.is_empty() else null

func _resource_path(relative_path: String) -> String:
	return "res://assets/reference-library/" + relative_path.trim_prefix("/")

func _cache_resource(cache: Dictionary, key: String, resource: Resource) -> void:
	cache[key] = resource
	if cache.size() > CACHE_LIMIT:
		cache.erase(cache.keys()[0])
