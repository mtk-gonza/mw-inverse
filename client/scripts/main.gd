extends Node3D

const SaveSystemModel = preload("res://scripts/save_system.gd")
const NetworkClientModel = preload("res://scripts/network_client.gd")
const RemotePlayerModel = preload("res://scripts/remote_player.gd")
const ContentCatalogModel = preload("res://scripts/content_catalog.gd")
const ReferenceAssetLibraryModel = preload("res://scripts/reference_asset_library.gd")
const TargetingModel = preload("res://scripts/domain/targeting.gd")
const ReferenceOverrideModel = preload("res://scripts/reference_override.gd")
var save_system = SaveSystemModel.new()
var network = NetworkClientModel.new()
var content = ContentCatalogModel.new()
var reference_assets = ReferenceAssetLibraryModel.new()
var remote_players: Dictionary = {}
var network_send_timer := 0.0
var last_network_position := Vector3.ZERO
var world_tick_timer := 0.0
var music_enabled := false
var reference_gallery: Control
var reference_gallery_image: TextureRect
var reference_gallery_label: Label
var reference_gallery_category: OptionButton
var reference_gallery_index := 0
var reference_gallery_files: Array = []
var reference_preview_player: AudioStreamPlayer
var reference_combat_player: AudioStreamPlayer
var skill_cooldowns: Dictionary = {}
var region_transition_pending := false
var inventory_icon_nodes: Array[TextureRect] = []
var death_overlay: PanelContainer
var settings_overlay: PanelContainer
var party_frames: VBoxContainer
var targeting_profile = TargetingModel.TargetingProfile.new()
var reference_override = ReferenceOverrideModel.new()
var exploration_session_generation := 0
var exploration_request_version := 0

func _ready() -> void:
	print("MW Inverse local exploration scene started")
	targeting_profile.from_dict(save_system.load_targeting_profile())
	_setup_hotbar_icons()
	_setup_reference_ui()
	_setup_reference_audio()
	_setup_reference_combat_audio()
	_setup_audio_buses()
	_setup_reference_world_materials()
	_setup_inventory_icons()
	_setup_death_overlay()
	_setup_settings_overlay()
	_setup_party_frames()
	var asset_summary: Dictionary = reference_assets.scan()
	$Ui/ReferenceAssetStatus.text = "Biblioteca local: %d recursos" % asset_summary.files
	_setup_reference_gallery()
	if content.load_all():
		$Ui/Title.text = "MW Inverse — " + str(content.regions["training_meadow"]["name"])
	$Player.combat_message.connect(_on_combat_message)
	$Player.inventory_changed.connect(_on_inventory_changed)
	$Player.attack_requested.connect(_on_attack_requested)
	$Player.interact_requested.connect(_on_interact_requested)
	$Ui/ChatInput.text_submitted.connect(_on_chat_submitted)
	$Ui/HotbarPanel/Hotbar/Slot1.pressed.connect(_on_hotbar_attack)
	$Ui/HotbarPanel/Hotbar/Slot2.pressed.connect(_on_hotbar_skill)
	$Ui/HotbarPanel/Hotbar/Slot3.pressed.connect(_on_hotbar_guard)
	$Ui/HotbarPanel/Hotbar/Slot4.pressed.connect(_on_hotbar_inventory)
	$Ui/HotbarPanel/Hotbar/Slot5.pressed.connect(_on_hotbar_potion)
	$Ui/HotbarPanel/Hotbar/Slot6.pressed.connect(_on_hotbar_party)
	$Ui/HotbarPanel/Hotbar/Slot7.pressed.connect(_on_hotbar_map)
	$Ui/HotbarPanel/Hotbar/Slot8.pressed.connect(_on_hotbar_menu)
	for slot in $Ui/HotbarPanel/Hotbar.get_children():
		slot.pressed.connect(_play_ui_click)
	$Ui/SaveStatus.text = "F5 guardar · F9 cargar"
	network.connected.connect(_on_network_connected)
	network.disconnected.connect(_on_network_disconnected)
	network.connection_error.connect(_on_network_error)
	network.state_changed.connect(_on_network_state_changed)
	network.message_received.connect(_on_network_message)
	network.connect_to_server()

func _setup_hotbar_icons() -> void:
	if DisplayServer.get_name() == "headless":
		return
	var icons := [
		"res://assets/ui/icons/sword.svg", "res://assets/ui/icons/arcane.svg", "res://assets/ui/icons/shield.svg",
		"res://assets/ui/icons/potion.svg", "res://assets/ui/icons/potion.svg", "res://assets/ui/icons/party.svg",
		"res://assets/ui/icons/map.svg", "res://assets/ui/icons/menu.svg"
	]
	for index in icons.size():
		var slot := $Ui/HotbarPanel/Hotbar.get_child(index) as Button
		var icon = load(icons[index])
		if icon is Texture2D:
			slot.icon = icon

func _setup_reference_ui() -> void:
	if DisplayServer.get_name() == "headless":
		return
	var references := {
		"ReferenceAtmosphere": "res://assets/reference-local/sharedassets0_Background_-_Green_Purple_1304.png",
		"GameLogo": "res://assets/reference-local/sharedassets0_Magic_Wings_Only_Text128_1397.png",
		"HealthIcon": "res://assets/reference-local/sharedassets0_health_865.png",
		"ManaIcon": "res://assets/reference-local/sharedassets0_mana_1482.png",
		"MapPanel/Map/ReferenceMap": "res://assets/reference-local/sharedassets0_Map_1010.png",
		"MapPanel/Map/ReferenceMarker": "res://assets/reference-local/sharedassets0_player-mark-minimap_32x32_1305.png",
	}
	for node_path in references:
		var texture = reference_override.load_texture(references[node_path].get_file(), references[node_path])
		if texture is Texture2D:
			get_node("Ui/" + node_path).texture = texture

func _setup_reference_audio() -> void:
	if DisplayServer.get_name() == "headless":
		return
	var music = load("res://assets/reference-local/audio/resources_Magic_Wings_-_Breeze_Tide.wav")
	if music is AudioStream:
		$MusicPlayer.stream = music
		$MusicPlayer.play()
		music_enabled = true
	var click = load("res://assets/reference-local/audio/resources_1._SFX_Button_Confirm_Magical_Interface_2-2.wav")
	if click is AudioStream:
		$UiClickPlayer.stream = click

func _play_region_music(region_id: String) -> void:
	if DisplayServer.get_name() == "headless":
		return
	var path := "res://assets/reference-local/audio/resources_Magic_Wings_-_Breeze_Tide.wav"
	if region_id == "quiet_harbor":
		path = "res://assets/reference-library/AudioClip/resources_Magic_Wings_-_Golden_Path.wav"
	elif region_id == "frostwood":
		path = "res://assets/reference-library/AudioClip/resources_Magic_Wings_-_Mist_of_the_Isles.wav"
	var stream := _load_optional(path) as AudioStream
	if stream == null:
		return
	if music_enabled:
		var transition := create_tween()
		transition.tween_property($MusicPlayer, "volume_db", -40.0, 0.35)
		transition.tween_callback(func() -> void:
			$MusicPlayer.stream = stream
			$MusicPlayer.volume_db = -18.0
			$MusicPlayer.play()
		)
	else:
		$MusicPlayer.stream = stream

func _setup_reference_combat_audio() -> void:
	if DisplayServer.get_name() == "headless":
		return
	reference_combat_player = AudioStreamPlayer.new()
	reference_combat_player.volume_db = -12.0
	add_child(reference_combat_player)

func _setup_audio_buses() -> void:
	_ensure_audio_bus("Music", -18.0)
	_ensure_audio_bus("SFX", -12.0)
	_ensure_audio_bus("UI", -8.0)
	$MusicPlayer.bus = "Music"
	$UiClickPlayer.bus = "UI"
	if reference_combat_player != null:
		reference_combat_player.bus = "SFX"

func _ensure_audio_bus(bus_name: String, volume_db: float) -> void:
	var index := AudioServer.get_bus_index(bus_name)
	if index < 0:
		AudioServer.add_bus()
		index = AudioServer.get_bus_count() - 1
		AudioServer.set_bus_name(index, bus_name)
	AudioServer.set_bus_volume_db(index, volume_db)

func _setup_reference_world_materials() -> void:
	var island_material := $Island/Mesh.material_override as StandardMaterial3D
	var grass := _load_optional("res://assets/reference-library/Texture2D/resources_grass_fullground_0_191.png") as Texture2D
	if island_material != null and grass != null:
		island_material.albedo_texture = grass
		island_material.uv1_scale = Vector3(8.0, 8.0, 8.0)
		island_material.roughness = 0.92
	for index in 3:
		var tree := get_node_or_null("Tree%d/Mesh" % (index + 1)) as MeshInstance3D
		if tree == null:
			continue
		var tree_material := tree.material_override as StandardMaterial3D
		var foliage := _load_optional("res://assets/reference-library/Texture2D/resources_TFF_Atlas_1A_D_236.png") as Texture2D
		if tree_material != null and foliage != null:
			tree_material.albedo_texture = foliage
			tree_material.albedo_color = Color(0.7, 0.9, 0.78, 1.0)

func _load_optional(path: String) -> Resource:
	var private_texture := reference_override.load_texture(path.get_file())
	if private_texture != null:
		return private_texture
	if not ResourceLoader.exists(path):
		return null
	return load(path)

func _play_reference_combat_audio(skill := false) -> void:
	if reference_combat_player == null:
		return
	var skill_audio := [
		"res://assets/reference-library/AudioClip/resources_Nature_Magic_Spell_4-5.wav",
		"res://assets/reference-library/AudioClip/resources_Magic_Cast_Whoosh_1-1.wav",
		"res://assets/reference-library/AudioClip/resources_Magic_Cast_Whoosh_1-2.wav",
	]
	var hit_audio := [
		"res://assets/reference-library/AudioClip/resources_Advanced_-_Beast_1_Hurt_A.wav",
		"res://assets/reference-library/AudioClip/resources_Advanced_-_Beast_2_Hurt_A.wav",
		"res://assets/reference-library/AudioClip/resources_Advanced_-_Creature_1_Hurt_A.wav",
	]
	var paths: Array = skill_audio if skill else hit_audio
	var path: String = paths[randi() % paths.size()]
	var stream := _load_optional(path)
	if stream is AudioStream:
		reference_combat_player.stream = stream
		reference_combat_player.play()

func _play_ui_click() -> void:
	if $UiClickPlayer.stream:
		$UiClickPlayer.play()

func _setup_reference_gallery() -> void:
	if DisplayServer.get_name() == "headless":
		return
	reference_preview_player = AudioStreamPlayer.new()
	reference_preview_player.volume_db = -10.0
	add_child(reference_preview_player)
	reference_gallery = PanelContainer.new()
	reference_gallery.name = "ReferenceAssetGallery"
	reference_gallery.position = Vector2(300, 72)
	reference_gallery.size = Vector2(680, 570)
	reference_gallery.visible = false
	$Ui.add_child(reference_gallery)
	var layout := VBoxContainer.new()
	layout.add_theme_constant_override("separation", 8)
	reference_gallery.add_child(layout)
	var heading := Label.new()
	heading.text = "Biblioteca de referencia · F8 para cerrar"
	heading.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	layout.add_child(heading)
	reference_gallery_category = OptionButton.new()
	for category in reference_assets.entries.keys():
		reference_gallery_category.add_item(str(category))
	reference_gallery_category.item_selected.connect(_on_reference_category_selected)
	layout.add_child(reference_gallery_category)
	reference_gallery_image = TextureRect.new()
	reference_gallery_image.custom_minimum_size = Vector2(640, 410)
	reference_gallery_image.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	reference_gallery_image.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	reference_gallery_image.mouse_filter = Control.MOUSE_FILTER_IGNORE
	layout.add_child(reference_gallery_image)
	reference_gallery_label = Label.new()
	reference_gallery_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	reference_gallery_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	layout.add_child(reference_gallery_label)
	var controls := HBoxContainer.new()
	controls.alignment = BoxContainer.ALIGNMENT_CENTER
	layout.add_child(controls)
	var previous := Button.new()
	previous.text = "◀ anterior"
	previous.pressed.connect(_on_reference_previous)
	controls.add_child(previous)
	var next := Button.new()
	next.text = "siguiente ▶"
	next.pressed.connect(_on_reference_next)
	controls.add_child(next)
	var play := Button.new()
	play.text = "▶ reproducir audio"
	play.pressed.connect(_play_reference_audio)
	controls.add_child(play)
	_load_reference_gallery_item()

func _toggle_reference_gallery() -> void:
	if reference_gallery == null:
		return
	reference_gallery.visible = not reference_gallery.visible
	if reference_gallery.visible:
		_load_reference_gallery_item()

func _on_reference_category_selected(_index: int) -> void:
	reference_gallery_index = 0
	_load_reference_gallery_item()

func _on_reference_previous() -> void:
	reference_gallery_index -= 1
	_load_reference_gallery_item()

func _on_reference_next() -> void:
	reference_gallery_index += 1
	_load_reference_gallery_item()

func _current_reference_file() -> String:
	if reference_gallery_category == null:
		return ""
	var category := reference_gallery_category.get_item_text(reference_gallery_category.selected)
	reference_gallery_files = reference_assets.category_files(category)
	if reference_gallery_files.is_empty():
		return ""
	reference_gallery_index = posmod(reference_gallery_index, reference_gallery_files.size())
	return str(reference_gallery_files[reference_gallery_index])

func _load_reference_gallery_item() -> void:
	if reference_gallery_label == null:
		return
	var relative_path := _current_reference_file()
	if relative_path.is_empty():
		reference_gallery_image.texture = null
		reference_gallery_label.text = "Categoría vacía"
		return
	var extension := relative_path.get_extension().to_lower()
	if extension == "png":
		reference_gallery_image.texture = reference_assets.load_texture(relative_path)
	else:
		reference_gallery_image.texture = null
	reference_gallery_label.text = "%d/%d · %s" % [reference_gallery_index + 1, reference_gallery_files.size(), relative_path]

func _play_reference_audio() -> void:
	var relative_path := _current_reference_file()
	if relative_path.get_extension().to_lower() != "wav" or reference_preview_player == null:
		return
	var stream := reference_assets.load_audio(relative_path)
	if stream != null:
		reference_preview_player.stream = stream
		reference_preview_player.play()

func _setup_party_frames() -> void:
	party_frames = VBoxContainer.new()
	party_frames.name = "PartyFrames"
	party_frames.position = Vector2(1010, 210)
	party_frames.size = Vector2(250, 140)
	party_frames.add_theme_constant_override("separation", 4)
	$Ui.add_child(party_frames)

func _update_party_frames(players: Array) -> void:
	if party_frames == null:
		return
	for child in party_frames.get_children():
		child.queue_free()
	var own_party := str($Player.state.party_id)
	if own_party.is_empty():
		return
	for snapshot in players:
		if str(snapshot.get("party_id", "")) != own_party:
			continue
		var label := Label.new()
		var position_data: Dictionary = snapshot.get("position", {})
		var member_position := Vector3(float(position_data.get("x", 0.0)), float(position_data.get("y", 0.0)), float(position_data.get("z", 0.0)))
		var distance: float = $Player.global_position.distance_to(member_position)
		label.text = "%s · Nv.%d · %d/%d · %.1fm" % [snapshot.get("player_id", "jugador"), snapshot.get("level", 1), snapshot.get("health", 0), snapshot.get("max_health", 100), distance]
		label.modulate = Color(0.55, 0.85, 1.0, 1.0)
		party_frames.add_child(label)

func _process(delta: float) -> void:
	network.poll(delta)
	_update_skill_cooldowns(delta)
	_check_region_portals()
	_update_minimap()
	world_tick_timer -= delta
	if world_tick_timer <= 0.0 and network.peer.get_status() == StreamPeerTCP.STATUS_CONNECTED:
		network.send_message({"type": "world_tick"})
		world_tick_timer = 0.5
	if network_send_timer > 0.0:
		network_send_timer -= delta
	if network_send_timer <= 0.0 and network.peer.get_status() == StreamPeerTCP.STATUS_CONNECTED:
		var current_position: Vector3 = $Player.global_position
		var movement := current_position - last_network_position
		if movement.length_squared() > 0.0001:
			network.send_message({"type": "move_intent", "dx": movement.x, "dz": movement.z})
			last_network_position = current_position
		network_send_timer = 0.1

func _on_combat_message(message: String) -> void:
	$Ui/CombatStatus.text = message

func _on_inventory_changed(items: Dictionary) -> void:
	var entries: Array[String] = []
	for item_id in items:
		entries.append("%s x%d" % [item_id, items[item_id]])
	$Ui/InventoryStatus.text = "Inventario: " + ", ".join(entries)
	$Ui/InventoryPanel/InventoryGrid.text = _format_inventory_grid(items)
	_update_inventory_icons(items)

func _setup_inventory_icons() -> void:
	var paths := [
		"res://assets/ui/icons/sword.svg",
		"res://assets/ui/icons/potion.svg",
		"res://assets/ui/icons/arcane.svg",
		"res://assets/ui/icons/shield.svg",
	]
	for index in 8:
		var icon := TextureRect.new()
		icon.name = "ReferenceInventoryIcon%d" % index
		icon.position = Vector2(16 + (index % 4) * 54, 42 + (index / 4) * 48)
		icon.size = Vector2(42, 42)
		icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		icon.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var texture_path: String = paths[index % paths.size()]
		icon.texture = _load_optional(texture_path) as Texture2D
		icon.visible = false
		$Ui/InventoryPanel.add_child(icon)
		inventory_icon_nodes.append(icon)

func _update_inventory_icons(items: Dictionary) -> void:
	for icon in inventory_icon_nodes:
		icon.visible = false
	var item_paths := {
		"training_blade": "res://assets/reference-library/Sprite/sharedassets0_eq_swordshield_1422.png",
		"mana_potion": "res://assets/reference-library/Sprite/resources_potion_2274.png",
		"monster_core": "res://assets/reference-library/Sprite/resources_batwing_2281.png",
		"ice_shard": "res://assets/reference-library/Sprite/resources_Magic_Wing_Icon_0_1982.png",
	}
	var index := 0
	for item_id in items:
		if index >= inventory_icon_nodes.size():
			break
		var icon := inventory_icon_nodes[index]
		var texture_path: String = item_paths.get(item_id, "res://assets/ui/icons/potion.svg")
		icon.texture = _load_optional(texture_path) as Texture2D
		icon.tooltip_text = "%s x%d" % [item_id, items[item_id]]
		icon.visible = true
		index += 1

func _on_network_connected() -> void:
	$Ui/NetworkStatus.text = "Servidor: conectado"
	$Player.use_server_combat = true
	last_network_position = $Player.global_position
	network.send_message({"type": "login_request", "player_id": "local-player"})

func _on_network_state_changed(state: String, reason: String) -> void:
	var labels := {
		"connecting": "conectando",
		"connected": "conectado",
		"protected": "sesión protegida",
		"reconnecting": "reconectando",
		"stalled": "sin respuesta",
		"protocol_error": "error de protocolo",
		"closed": "cerrado",
		"disconnected": "desconectado",
	}
	$Ui/NetworkStatus.text = "Servidor: " + str(labels.get(state, state))
	if not reason.is_empty():
		$Ui/NetworkStatus.text += " · " + reason

func _on_network_disconnected() -> void:
	$Ui/NetworkStatus.text = "Servidor: desconectado · modo local"
	$Player.use_server_combat = false

func _on_network_error(message: String) -> void:
	$Ui/NetworkStatus.text = "Servidor: " + message

func _on_network_message(message: Dictionary) -> void:
	var message_type: String = message.get("type", "")
	if message_type == "login_result" and message.get("ok", false):
		network.session_token = str(message.get("token", ""))
		$Player.import_state(message.state)
		exploration_session_generation = int(message.state.get("exploration_session_generation", 0))
		exploration_request_version = 0
		_update_health_status()
		last_network_position = $Player.global_position
		$Ui/NetworkStatus.text = "Servidor: sesión activa"
		network._set_state("protected", "login_ok")
		network.send_message({"type": "world_snapshot"})
	elif message_type == "session_event" and not message.get("ok", false):
		network.session_token = ""
		$Player.use_server_combat = false
		$Ui/NetworkStatus.text = "Sesión expirada: reconecta"
	elif message_type == "world_snapshot":
		_apply_world_snapshot(message.get("enemies", {}), message.get("enemy_positions", {}))
		_apply_player_snapshots(message.get("players", []))
		_update_party_frames(message.get("players", []))
		if message.get("region") is Dictionary:
			_apply_region_visuals(message.region)
	elif message_type == "world_tick":
		_apply_enemy_positions(message.get("enemy_positions", {}))
		if not message.get("enemy_attacks", []).is_empty():
			$Player.state.health = int(message.get("health", $Player.state.health))
			_update_health_status()
			$Ui/CombatStatus.text = "Has recibido daño: %d" % message.enemy_attacks[-1].damage
	elif message_type == "movement_snapshot":
		$Player.import_state(message.state)
		_update_health_status()
		last_network_position = $Player.global_position
	elif message_type == "inventory_event":
		$Player.restore_inventory(message.inventory)
	elif message_type == "combat_event":
		if not message.get("ok", false):
			$Ui/CombatStatus.text = "Ataque rechazado: " + str(message.get("reason", "unknown"))
			return
		$Ui/CombatStatus.text = "Daño confirmado: %d%s" % [message.damage, " · enemigo derrotado" if message.defeated else ""]
		if not message.get("loot", {}).is_empty():
			$Ui/InventoryStatus.text = "Botín: " + ", ".join(message.loot.keys())
		_play_reference_combat_audio()
		_launch_reference_projectile(str(message.target_id), false)
		$Player.apply_progression(message.level, message.experience, message.attack)
		$Player.state.quests = message.quests.duplicate()
		$Ui/ProgressStatus.text = "Nivel %d · EXP %d · Ataque %d · Monedas %d" % [$Player.state.level, $Player.state.experience, $Player.state.attack, $Player.state.currency]
		if message.level_up:
			$Ui/CombatStatus.text += " · ¡subiste de nivel!"
		var quest: Dictionary = message.quests.get("training_hunt", {})
		$Ui/QuestStatus.text = "Misión: práctica %d/3%s" % [quest.get("progress", 0), " · completada" if quest.get("completed", false) else ""]
		$Ui/QuestPanel/QuestText.text = "Derrota enemigos de entrenamiento\nProgreso: %d/3%s" % [quest.get("progress", 0), "\nRecompensa desbloqueada" if quest.get("completed", false) else ""]
	elif message_type == "dialogue_event":
		$Ui/DialogueStatus.text = message.get("name", "NPC") + ": " + message.get("dialogue", "")
	elif message_type == "chat_event" and message.get("ok", false):
		$Ui/DialogueStatus.text = "[%s] %s: %s" % [message.get("channel", "local"), message.get("player_id", "jugador"), message.get("text", "")]
	elif message_type == "party_event":
		if message.get("ok", false):
			$Player.state.party_id = message.party_id
			$Ui/PartyStatus.text = "Grupo %s · miembros: %s" % [message.party_id, ", ".join(message.members)]
		else:
			$Ui/PartyStatus.text = "Grupo: " + str(message.get("reason", "error"))
	elif message_type == "clan_event":
		if message.get("ok", false):
			$Ui/PartyStatus.text = "Clan %s · miembros: %s" % [message.clan_id, ", ".join(message.members)]
		else:
			$Ui/PartyStatus.text = "Clan: " + str(message.get("reason", "error"))
	elif message_type == "exploration_event":
		var generation := int(message.get("session_generation", exploration_session_generation))
		var version := int(message.get("request_version", 0))
		if generation != exploration_session_generation or version < exploration_request_version:
			return
		if message.get("ok", false):
			$Ui/DialogueStatus.text = "Exploración: %d santuario(s) descubierto(s)" % message.get("discovered", []).size()
			$Ui/QuestStatus.text = "Santuarios: " + ", ".join(message.get("discovered", []))
	elif message_type == "matchmaking_event":
		$Ui/PartyStatus.text = "Arena: " + str(message.get("state", "idle")) + (" · " + str(message.get("match_id", "")) if message.get("match_id", "") else "")
	elif message_type == "shop_event":
		if message.get("ok", false):
			$Player.state.currency = message.currency
			$Player.restore_inventory(message.inventory)
			$Ui/DialogueStatus.text = ("Venta realizada: " if message.get("action") == "sell" else "Compra realizada: ") + message.item_id
		else:
			$Ui/DialogueStatus.text = "Compra rechazada: " + str(message.get("reason", "error"))
	elif message_type == "equipment_event":
		if message.get("ok", false):
			$Player.state.equipment = message.equipment.duplicate()
			$Player.state.attack = message.attack
			$Ui/ProgressStatus.text = "Nivel %d · EXP %d · Ataque %d · Monedas %d" % [$Player.state.level, $Player.state.experience, $Player.state.attack, $Player.state.currency]
			$Ui/DialogueStatus.text = "Equipado: training_blade"
		else:
			$Ui/DialogueStatus.text = "Equipamiento rechazado: " + str(message.get("reason", "error"))
		$Player.restore_inventory(message.inventory)
		if message.defeated:
			_hide_defeated_enemy(str(message.target_id))
		if not message.get("loot", {}).is_empty():
			$Ui/InventoryStatus.text = "Botín: " + ", ".join(message.loot.keys())
	elif message_type == "skill_event":
		if not message.get("ok", false):
			if message.get("reason") == "cooldown":
				skill_cooldowns["arcane_bolt"] = float(message.get("cooldown_remaining", 0.0))
			$Ui/CombatStatus.text = "Habilidad rechazada: " + str(message.get("reason", "error"))
			return
		skill_cooldowns[str(message.get("skill_id", ""))] = float(message.get("cooldown", 0.0))
		$Player.state.energy = int(message.get("energy", $Player.state.energy))
		if float(message.get("slow_seconds", 0.0)) > 0.0:
			$Ui/CombatStatus.text = "Nova de hielo: enemigo ralentizado %.1fs" % float(message.slow_seconds)
		_play_reference_combat_audio(true)
		if message.get("guarded", false):
			_show_guard_effect()
		else:
			_launch_reference_projectile(str(message.target_id), true)
		$Ui/EnergyStatus.text = "Energía: %d/100" % $Player.state.energy
		if message.get("skill_id") == "arcane_bolt":
			$Ui/CombatStatus.text = "Rayo arcano: %d de daño" % message.damage
			if message.get("defeated", false):
				_hide_defeated_enemy(str(message.target_id))
		elif message.get("guarded", false):
			$Ui/CombatStatus.text = "Guardia activa"
	elif message_type == "pvp_event":
		if not message.get("ok", false):
			$Ui/CombatStatus.text = "PvP rechazado: " + str(message.get("reason", "error"))
		else:
			var status: Dictionary = message.get("pvp_status", {})
			$Ui/CombatStatus.text = "PvP confirmado · marca %.0fs · skull %.0fs%s" % [
				float(status.get("mark", 0.0)), float(status.get("skull", 0.0)),
				" · derrota" if message.get("defeated", false) else ""]
	elif message_type == "item_event":
		if message.get("ok", false):
			$Player.state.energy = int(message.energy)
			$Player.state.health = int(message.get("health", $Player.state.health))
			$Player.restore_inventory(message.inventory)
			_update_health_status()
		else:
			$Ui/CombatStatus.text = "Objeto rechazado: " + str(message.get("reason", "error"))
	elif message_type == "respawn_event" and message.get("ok", false):
		$Player.import_state(message.state)
		_update_health_status()
		$Ui/CombatStatus.text = "Has regresado al punto de inicio"
	elif message_type == "craft_event":
		if message.get("ok", false):
			$Player.state.currency = int(message.currency)
			$Player.restore_inventory(message.inventory)
			$Ui/DialogueStatus.text = "Fabricado: " + str(message.item_id)
		else:
			$Ui/DialogueStatus.text = "Fabricación rechazada: " + str(message.get("reason", "error"))
	elif message_type == "region_event":
		region_transition_pending = false
		if message.get("ok", false):
			_apply_region_visuals(message.region)
			network.send_message({"type": "world_snapshot"})
			$Ui/DialogueStatus.text = "Has llegado a " + str(message.region.get("name", "nueva región"))
		else:
			$Ui/DialogueStatus.text = "Transición rechazada: " + str(message.get("reason", "error"))

func _on_attack_requested(target_id: String) -> void:
	network.send_message({"type": "attack_request", "target_id": target_id})

func _on_interact_requested(npc_id: String) -> void:
	network.send_message({"type": "npc_interact", "npc_id": npc_id})

func _on_chat_submitted(text: String) -> void:
	if text.strip_edges().is_empty():
		return
	var channel := "local"
	var clean_text := text.strip_edges()
	var recipient_id := ""
	for prefix in ["/party ", "/clan ", "/system "]:
		if clean_text.begins_with(prefix):
			channel = prefix.strip_edges().trim_prefix("/")
			clean_text = clean_text.trim_prefix(prefix).strip_edges()
			break
	if clean_text.begins_with("/w "):
		var whisper_parts := clean_text.trim_prefix("/w ").split(" ", false, 1)
		if whisper_parts.size() < 2:
			return
		channel = "whisper"
		recipient_id = whisper_parts[0]
		clean_text = whisper_parts[1]
	if not network.send_message({"type": "chat_message", "text": clean_text, "channel": channel, "recipient_id": recipient_id}):
		$Ui/DialogueStatus.text = "Chat no disponible: servidor desconectado"
	$Ui/ChatInput.clear()

func _update_health_status() -> void:
	$Ui/HealthStatus.text = "Vida: %d/%d" % [$Player.state.health, $Player.state.max_health]
	$Ui/HealthBar.max_value = $Player.state.max_health
	$Ui/HealthBar.value = $Player.state.health
	$Ui/ExperienceBar.max_value = maxf(float($Player.state.level * 100), 1.0)
	$Ui/ExperienceBar.value = $Player.state.experience
	$Ui/EnergyStatus.text = "Energía: %d/100" % $Player.state.energy
	if death_overlay != null:
		death_overlay.visible = $Player.state.health <= 0

func _setup_death_overlay() -> void:
	death_overlay = PanelContainer.new()
	death_overlay.name = "DeathOverlay"
	death_overlay.position = Vector2(470, 245)
	death_overlay.size = Vector2(340, 150)
	death_overlay.visible = false
	$Ui.add_child(death_overlay)
	var layout := VBoxContainer.new()
	layout.alignment = BoxContainer.ALIGNMENT_CENTER
	death_overlay.add_child(layout)
	var title := Label.new()
	title.text = "HAS CAÍDO"
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	layout.add_child(title)
	var hint := Label.new()
	hint.text = "Regresa al santuario inicial"
	hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	layout.add_child(hint)
	var respawn := Button.new()
	respawn.text = "RESPAWN"
	respawn.pressed.connect(func() -> void:
		network.send_message({"type": "respawn_request"})
	)
	layout.add_child(respawn)

func _setup_settings_overlay() -> void:
	settings_overlay = PanelContainer.new()
	settings_overlay.name = "SettingsOverlay"
	settings_overlay.position = Vector2(430, 170)
	settings_overlay.size = Vector2(420, 360)
	settings_overlay.visible = false
	$Ui.add_child(settings_overlay)
	var layout := VBoxContainer.new()
	layout.add_theme_constant_override("separation", 12)
	settings_overlay.add_child(layout)
	var title := Label.new()
	title.text = "CONFIGURACIÓN · F1 para cerrar"
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	layout.add_child(title)
	_add_volume_control(layout, "Música", $MusicPlayer, -18.0)
	_add_volume_control(layout, "Interfaz", $UiClickPlayer, -8.0)
	_add_volume_control(layout, "Combate", reference_combat_player, -12.0)
	var fullscreen := CheckButton.new()
	fullscreen.text = "Pantalla completa"
	fullscreen.toggled.connect(func(enabled: bool) -> void:
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN if enabled else DisplayServer.WINDOW_MODE_WINDOWED)
	)
	layout.add_child(fullscreen)
	var close := Button.new()
	close.text = "Cerrar"
	close.pressed.connect(func() -> void: settings_overlay.visible = false)
	layout.add_child(close)

func _add_volume_control(parent: VBoxContainer, label_text: String, player: AudioStreamPlayer, initial_db: float) -> void:
	var label := Label.new()
	label.text = label_text
	parent.add_child(label)
	var slider := HSlider.new()
	slider.min_value = -40.0
	slider.max_value = 0.0
	slider.step = 1.0
	slider.value = initial_db
	slider.tooltip_text = label_text
	slider.value_changed.connect(func(value: float) -> void:
		if player != null:
			player.volume_db = value
	)
	parent.add_child(slider)

func _update_skill_cooldowns(delta: float) -> void:
	for skill_id in skill_cooldowns.keys():
		skill_cooldowns[skill_id] = maxf(float(skill_cooldowns[skill_id]) - delta, 0.0)
	var skill_button := $Ui/HotbarPanel/Hotbar/Slot2 as Button
	var guard_button := $Ui/HotbarPanel/Hotbar/Slot3 as Button
	var bolt_remaining := float(skill_cooldowns.get("arcane_bolt", 0.0))
	var guard_remaining := float(skill_cooldowns.get("guard", 0.0))
	skill_button.disabled = bolt_remaining > 0.0
	guard_button.disabled = guard_remaining > 0.0
	skill_button.tooltip_text = "Rayo arcano · %.1fs" % bolt_remaining if bolt_remaining > 0.0 else "Rayo arcano"
	guard_button.tooltip_text = "Guardia · %.1fs" % guard_remaining if guard_remaining > 0.0 else "Guardia"

func _hide_defeated_enemy(target_id: String) -> void:
	for candidate in get_tree().get_nodes_in_group("enemies"):
		if candidate.get("target_id") == target_id:
			_show_loot_effect(candidate.global_position)
			if candidate.has_method("play_defeat"):
				candidate.play_defeat()
			else:
				candidate.visible = false
				candidate.set("is_defeated", true)

func _on_hotbar_skill() -> void:
	var target_id := _nearest_target_id()
	if not target_id.is_empty():
		network.send_message({"type": "skill_request", "skill_id": "arcane_bolt", "target_id": target_id})

func _on_hotbar_guard() -> void:
	network.send_message({"type": "skill_request", "skill_id": "guard"})

func _on_hotbar_potion() -> void:
	var item_id := "health_potion" if $Player.state.health < $Player.state.max_health else "mana_potion"
	network.send_message({"type": "consume_request", "item_id": item_id})

func _nearest_target_id() -> String:
	var target_id := ""
	var best_distance := 16.0
	for candidate in get_tree().get_nodes_in_group("enemies"):
		if not is_instance_valid(candidate) or not candidate.visible or candidate.get("is_defeated"):
			continue
		var distance: float = $Player.global_position.distance_squared_to(candidate.global_position)
		if distance < best_distance:
			best_distance = distance
			target_id = str(candidate.get("target_id"))
	return target_id

func _format_inventory_grid(items: Dictionary) -> String:
	var slots: Array[String] = []
	for item_id in items:
		slots.append("%s x%d" % [item_id, items[item_id]])
	while slots.size() < 8:
		slots.append("— vacío —")
	return "\n".join(slots)

func _update_minimap() -> void:
	var world_position: Vector3 = $Player.global_position
	var marker_x := clampf(100.0 + world_position.x * 12.0, 8.0, 198.0)
	var marker_y := clampf(48.0 + world_position.z * 10.0, 8.0, 94.0)
	$Ui/MapPanel/Map/MapMarker.position = Vector2(marker_x, marker_y)

func _check_region_portals() -> void:
	if region_transition_pending or not network.peer.get_status() == StreamPeerTCP.STATUS_CONNECTED:
		return
	var region_id := str($Player.state.region_id)
	if region_id == "training_meadow" and $Player.global_position.x > 12.0:
		region_transition_pending = true
		network.send_message({"type": "enter_region_request", "region_id": "quiet_harbor"})
	elif region_id == "training_meadow" and $Player.global_position.x < -12.0:
		region_transition_pending = true
		network.send_message({"type": "enter_region_request", "region_id": "frostwood"})

func _apply_region_visuals(region: Dictionary) -> void:
	var region_id := str(region.get("region_id", "training_meadow"))
	$Player.state.region_id = region_id
	$Ui/Title.text = "MW Inverse — " + str(region.get("name", region_id))
	_play_region_music(region_id)
	var active_enemies: Array = region.get("enemies", [])
	for enemy in get_tree().get_nodes_in_group("enemies"):
		var enemy_id := str(enemy.get("target_id"))
		enemy.visible = enemy_id in active_enemies
		enemy.set_physics_process(enemy.visible and not enemy.get("is_defeated"))
	for npc in get_tree().get_nodes_in_group("npcs"):
		var npc_id := str(npc.get("npc_id"))
		npc.visible = (region_id == "training_meadow" and npc_id == "mentor_arin") or (region_id == "quiet_harbor" and npc_id == "quartermaster_lynn") or (region_id == "frostwood" and npc_id == "warden_sela")
	for landmark in get_tree().get_nodes_in_group("region_landmarks"):
		landmark.visible = str(landmark.get_meta("region_id", "")) == region_id
	for shrine in get_tree().get_nodes_in_group("shrines"):
		shrine.visible = str(shrine.get_meta("region_id", "")) == region_id
	if region_id == "quiet_harbor":
		$WorldLight.light_color = Color(1.0, 0.72, 0.48, 1.0)
		$WorldLight.light_energy = 1.1
		$WorldEnvironment.environment.fog_light_color = Color(0.45, 0.3, 0.26, 1.0)
	else:
		$WorldLight.light_color = Color(0.72, 0.84, 1.0, 1.0)
		$WorldLight.light_energy = 1.25
		$WorldEnvironment.environment.fog_light_color = Color(0.22, 0.38, 0.68, 1.0)

func _show_loot_effect(start_position: Vector3) -> void:
	var loot := Sprite3D.new()
	loot.texture = reference_override.load_slot("loot", "res://assets/sprites/effects/loot_orb.svg")
	loot.pixel_size = 0.005
	loot.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	loot.no_depth_test = true
	loot.global_position = start_position + Vector3(0, 1.0, 0)
	add_child(loot)
	var tween := create_tween()
	tween.set_trans(Tween.TRANS_QUAD)
	tween.set_ease(Tween.EASE_IN_OUT)
	tween.tween_property(loot, "global_position", $Player.global_position + Vector3(0, 1.0, 0), 0.55)
	tween.parallel().tween_property(loot, "scale", Vector3(1.5, 1.5, 1.5), 0.55)
	tween.tween_callback(loot.queue_free)

func _show_reference_combat_effect(target_id: String, skill: bool) -> void:
	for candidate in get_tree().get_nodes_in_group("enemies"):
		if str(candidate.get("target_id")) != target_id:
			continue
		var effect := Sprite3D.new()
		effect.texture = reference_override.load_slot("spell_effect" if skill else "hit_spark", "res://assets/ui/icons/arcane.svg" if skill else "res://assets/sprites/effects/hit_spark.svg")
		if effect.texture == null:
			return
		effect.pixel_size = 0.018
		effect.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		effect.no_depth_test = true
		effect.position = candidate.global_position + Vector3(0, 1.25, 0)
		effect.modulate = Color(0.55, 0.8, 1.0, 1.0) if skill else Color(1.0, 0.45, 0.3, 1.0)
		add_child(effect)
		var tween := create_tween()
		tween.set_parallel(true)
		tween.tween_property(effect, "scale", Vector3(2.0, 2.0, 2.0), 0.3)
		tween.tween_property(effect, "modulate", Color(1, 1, 1, 0), 0.3)
		tween.chain().tween_callback(effect.queue_free)
		return

func _launch_reference_projectile(target_id: String, skill: bool) -> void:
	var target: Node3D = null
	for candidate in get_tree().get_nodes_in_group("enemies"):
		if str(candidate.get("target_id")) == target_id and candidate.visible:
			target = candidate
			break
	if target == null:
		_show_reference_combat_effect(target_id, skill)
		return
	var projectile := Sprite3D.new()
	projectile.texture = reference_override.load_slot("spell_projectile" if skill else "attack_projectile", "res://assets/ui/icons/arcane.svg" if skill else "res://assets/ui/icons/sword.svg")
	if projectile.texture == null:
		return
	projectile.pixel_size = 0.009
	projectile.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	projectile.no_depth_test = true
	projectile.modulate = Color(0.45, 0.8, 1.0, 1.0) if skill else Color(1.0, 0.8, 0.35, 1.0)
	projectile.global_position = $Player.global_position + Vector3(0, 1.1, 0)
	add_child(projectile)
	var tween := create_tween()
	tween.set_parallel(true)
	tween.tween_property(projectile, "global_position", target.global_position + Vector3(0, 1.1, 0), 0.22)
	tween.tween_property(projectile, "rotation_degrees", Vector3(0, 0, 360), 0.22)
	tween.chain().tween_callback(func() -> void:
		projectile.queue_free()
		_show_reference_combat_effect(target_id, skill)
	)

func _show_guard_effect() -> void:
	var effect := Sprite3D.new()
	effect.texture = reference_override.load_slot("guard_effect", "res://assets/ui/icons/shield.svg")
	if effect.texture == null:
		return
	effect.pixel_size = 0.012
	effect.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	effect.no_depth_test = true
	effect.modulate = Color(0.35, 0.75, 1.0, 0.9)
	effect.position = Vector3(0, 1.0, 0)
	$Player.add_child(effect)
	var tween := create_tween()
	tween.set_parallel(true)
	tween.tween_property(effect, "scale", Vector3(1.3, 1.3, 1.3), 2.5)
	tween.tween_property(effect, "modulate", Color(0.35, 0.75, 1.0, 0.0), 2.5)
	tween.chain().tween_callback(effect.queue_free)

func _on_hotbar_attack() -> void:
	$Player._attack_nearest()

func _on_hotbar_inventory() -> void:
	$Ui/InventoryPanel.visible = not $Ui/InventoryPanel.visible

func _on_hotbar_party() -> void:
	network.send_message({"type": "party_create"})

func _on_hotbar_map() -> void:
	$Ui/MapPanel.visible = not $Ui/MapPanel.visible

func _on_hotbar_menu() -> void:
	$Ui/QuestPanel.visible = not $Ui/QuestPanel.visible

func _apply_world_snapshot(enemies: Dictionary, positions: Dictionary = {}) -> void:
	for candidate in get_tree().get_nodes_in_group("enemies"):
		var health: int = int(enemies.get(candidate.get("target_id"), 0))
		if candidate.has_method("apply_server_health"):
			candidate.apply_server_health(health)
		else:
			candidate.visible = health > 0
	_apply_enemy_positions(positions)

func _apply_enemy_positions(positions: Dictionary) -> void:
	for candidate in get_tree().get_nodes_in_group("enemies"):
		var position_data: Dictionary = positions.get(str(candidate.get("target_id")), {})
		if not position_data.is_empty():
			candidate.global_position = Vector3(float(position_data.get("x", candidate.global_position.x)), float(position_data.get("y", candidate.global_position.y)), float(position_data.get("z", candidate.global_position.z)))

func _apply_player_snapshots(players: Array) -> void:
	var seen: Dictionary = {}
	for snapshot in players:
		var player_id: String = str(snapshot.get("player_id", ""))
		if player_id.is_empty() or player_id == "local-player":
			continue
		seen[player_id] = true
		var remote = remote_players.get(player_id)
		if remote == null:
			remote = RemotePlayerModel.new()
			remote.setup(player_id)
			add_child(remote)
			remote_players[player_id] = remote
		remote.apply_snapshot(snapshot)
	for player_id in remote_players.keys():
		if not seen.has(player_id):
			remote_players[player_id].queue_free()
			remote_players.erase(player_id)

func _discover_nearest_shrine() -> void:
	var nearest: Node3D = null
	var best_distance := 9.0
	for shrine in get_tree().get_nodes_in_group("shrines"):
		if not shrine.visible:
			continue
		var distance: float = $Player.global_position.distance_squared_to(shrine.global_position)
		if distance < best_distance:
			best_distance = distance
			nearest = shrine
	if nearest == null:
		$Ui/DialogueStatus.text = "No hay un santuario cercano"
		return
	network.send_message({"type": "discover_shrine", "shrine_id": str(nearest.get_meta("shrine_id"))})

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed:
		if event.button_index == MOUSE_BUTTON_WHEEL_UP:
			_adjust_camera_zoom(-1.0)
		elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			_adjust_camera_zoom(1.0)
		elif event.button_index == MOUSE_BUTTON_LEFT:
			_select_target_at_screen_position(event.position)
		return
	if not event is InputEventKey or not event.pressed or event.echo:
		if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
			_select_target_at_screen_position(event.position)
		return
	if event.keycode == KEY_F5:
		if save_system.save_player($Player, $Player.inventory_snapshot()):
			save_system.save_targeting_profile(targeting_profile.to_dict())
			$Ui/SaveStatus.text = "Partida guardada"
		else:
			$Ui/SaveStatus.text = "No se pudo guardar"
	elif event.keycode == KEY_F9:
		var result: Dictionary = save_system.load_player($Player)
		if result.ok:
			if not result.state.is_empty():
				$Player.import_state(result.state)
			else:
				$Player.restore_inventory(result.inventory)
			$Ui/SaveStatus.text = "Partida cargada"
		else:
			$Ui/SaveStatus.text = "No hay partida guardada"
	elif event.keycode == KEY_F2:
		network.send_message({"type": "party_create"})
	elif event.keycode == KEY_F4:
		network.send_message({"type": "buy_request", "item_id": "training_blade"})
	elif event.keycode == KEY_F3:
		network.send_message({"type": "equip_request", "item_id": "training_blade"})
	elif event.keycode == KEY_F6:
		$Player.state.pvp_enabled = not $Player.state.pvp_enabled
		network.send_message({"type": "pvp_toggle", "enabled": $Player.state.pvp_enabled})
		$Ui/CombatStatus.text = "PvP: " + ("activado" if $Player.state.pvp_enabled else "desactivado")
	elif event.keycode == KEY_F7:
		network.send_message({"type": "clan_create"})
	elif event.keycode == KEY_F12:
		exploration_request_version += 1
		network.send_message({"type": "exploration_snapshot", "request_version": exploration_request_version})
	elif event.keycode == KEY_R:
		_discover_nearest_shrine()
	elif event.keycode == KEY_C:
		network.send_message({"type": "craft_request", "item_id": "frost_blade"})
	elif event.keycode == KEY_V:
		network.send_message({"type": "sell_request", "item_id": "monster_core", "amount": 1})
	elif event.keycode == KEY_F10:
		network.send_message({"type": "matchmake_join"})
	elif event.keycode == KEY_F11:
		music_enabled = not music_enabled
		if music_enabled:
			$MusicPlayer.play()
		else:
			$MusicPlayer.stop()
		$Ui/CombatStatus.text = "Música: " + ("activada" if music_enabled else "desactivada")
	elif event.keycode == KEY_F8:
		_toggle_reference_gallery()
	elif event.keycode == KEY_F1:
		if settings_overlay != null:
			settings_overlay.visible = not settings_overlay.visible
	elif event.keycode == KEY_Q:
		$Player/Camera.rotation_degrees.y -= 8.0
	elif event.keycode == KEY_Z:
		$Player/Camera.rotation_degrees.y += 8.0

func _adjust_camera_zoom(amount: float) -> void:
	var camera := $Player/Camera as Camera3D
	var distance := clampf(camera.position.y + amount, 7.0, 18.0)
	var ratio := distance / maxf(camera.position.y, 0.1)
	camera.position.y = distance
	camera.position.z = clampf(camera.position.z * ratio, 5.0, 14.0)

func _select_target_at_screen_position(screen_position: Vector2) -> void:
	var camera := $Player/Camera as Camera3D
	var ray_start := camera.project_ray_origin(screen_position)
	var ray_end := ray_start + camera.project_ray_normal(screen_position) * 100.0
	var query := PhysicsRayQueryParameters3D.create(ray_start, ray_end)
	var hit := get_world_3d().direct_space_state.intersect_ray(query)
	if hit.is_empty():
		return
	var collider: Node = hit.get("collider")
	var candidate := collider.get_parent() if collider != null else null
	if candidate != null and candidate.is_in_group("enemies"):
		$Player.selected_target_id = str(candidate.get("target_id"))
		$Ui/CombatStatus.text = "Objetivo: " + $Player.selected_target_id
