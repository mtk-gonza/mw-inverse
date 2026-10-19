extends CharacterBody3D

const InventoryModel = preload("res://scripts/inventory.gd")
const PlayerStateModel = preload("res://scripts/domain/player_state.gd")
const ReferenceOverrideModel = preload("res://scripts/reference_override.gd")

const SPEED := 5.0
const GRAVITY := 18.0
const ATTACK_RANGE_SQUARED := 16.0

signal combat_message(message: String)
signal inventory_changed(items: Dictionary)
signal attack_requested(target_id: String)
signal interact_requested(npc_id: String)

var use_server_combat := false

var inventory = InventoryModel.new()
var state = PlayerStateModel.new()
var target_marker: MeshInstance3D
var animation_time := 0.0
var wing_nodes: Array[MeshInstance3D] = []
var weapon_node: MeshInstance3D
var avatar_sprite: Sprite3D
var camera_base_position := Vector3.ZERO
var reference_override = ReferenceOverrideModel.new()
var action_time := 0.0
var selected_target_id := ""
enum ActionState { IDLE, MOVING, ATTACKING, CASTING, HIT, DEAD }
var action_state: ActionState = ActionState.IDLE

func _ready() -> void:
	state.position = global_position
	$Nameplate.text = "Gurdock\nNv. %d" % state.level
	_build_avatar_details()
	camera_base_position = $Camera.position
	target_marker = MeshInstance3D.new()
	var ring := TorusMesh.new()
	ring.inner_radius = 0.72
	ring.outer_radius = 0.84
	target_marker.mesh = ring
	var marker_material := StandardMaterial3D.new()
	marker_material.albedo_color = Color(0.55, 0.1, 1, 1)
	marker_material.emission_enabled = true
	marker_material.emission = Color(0.25, 0.02, 0.6, 1)
	target_marker.material_override = marker_material
	target_marker.rotation_degrees.x = 90.0
	target_marker.visible = false
	var reference_ring := Sprite3D.new()
	reference_ring.name = "ReferenceTargetRing"
	var reference_ring_path := "res://assets/reference-library/Sprite/resources_AutoTargetRing_2567.png"
	reference_ring.texture = reference_override.load_slot("target_ring", reference_ring_path)
	reference_ring.pixel_size = 0.002
	reference_ring.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	reference_ring.no_depth_test = true
	reference_ring.modulate = Color(0.65, 0.3, 1.0, 0.72)
	reference_ring.position.y = 0.02
	if reference_ring.texture != null:
		target_marker.add_child(reference_ring)
		target_marker.get_child(0).visible = false
	get_parent().call_deferred("add_child", target_marker)

func _build_avatar_details() -> void:
	avatar_sprite = Sprite3D.new()
	avatar_sprite.name = "OriginalAvatarSprite"
	avatar_sprite.texture = reference_override.load_slot("player_avatar", "res://assets/sprites/characters/player_avatar.svg")
	avatar_sprite.pixel_size = 0.0085
	avatar_sprite.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	avatar_sprite.no_depth_test = true
	avatar_sprite.position = Vector3(0, 0.82, -0.12)
	avatar_sprite.modulate = Color(1, 1, 1, 0.96)
	add_child(avatar_sprite)
	var head := MeshInstance3D.new()
	var head_mesh := SphereMesh.new()
	head_mesh.radius = 0.3
	head_mesh.height = 0.6
	head.mesh = head_mesh
	head.position = Vector3(0, 0.95, 0)
	var head_material := StandardMaterial3D.new()
	head_material.albedo_color = Color(0.9, 0.72, 0.58, 1)
	head.material_override = head_material
	add_child(head)
	var aura := MeshInstance3D.new()
	var aura_mesh := TorusMesh.new()
	aura_mesh.inner_radius = 0.5
	aura_mesh.outer_radius = 0.58
	aura.mesh = aura_mesh
	aura.rotation_degrees.x = 90
	aura.position.y = -0.82
	var aura_material := StandardMaterial3D.new()
	aura_material.albedo_color = Color(0.4, 0.7, 1, 0.8)
	aura_material.emission_enabled = true
	aura_material.emission = Color(0.15, 0.35, 0.9, 1)
	aura.material_override = aura_material
	add_child(aura)
	var cloak := MeshInstance3D.new()
	var cloak_mesh := PrismMesh.new()
	cloak_mesh.size = Vector3(0.72, 1.0, 0.22)
	cloak.mesh = cloak_mesh
	cloak.position = Vector3(0, 0.2, 0.18)
	var cloak_material := StandardMaterial3D.new()
	cloak_material.albedo_color = Color(0.12, 0.16, 0.42, 1)
	cloak_material.emission_enabled = true
	cloak_material.emission = Color(0.04, 0.08, 0.25, 1)
	cloak.material_override = cloak_material
	add_child(cloak)
	for side in [-1.0, 1.0]:
		var wing := MeshInstance3D.new()
		var wing_mesh := PrismMesh.new()
		wing_mesh.size = Vector3(0.55, 0.85, 0.12)
		wing.mesh = wing_mesh
		wing.position = Vector3(side * 0.48, 0.45, 0.08)
		wing.rotation_degrees = Vector3(0, side * 18.0, side * 22.0)
		wing.material_override = cloak_material
		add_child(wing)
		wing_nodes.append(wing)
	var sword := MeshInstance3D.new()
	weapon_node = sword
	var blade := BoxMesh.new()
	blade.size = Vector3(0.09, 0.72, 0.06)
	sword.mesh = blade
	sword.position = Vector3(0.58, 0.15, -0.08)
	sword.rotation_degrees = Vector3(0, 0, -22)
	var blade_material := StandardMaterial3D.new()
	blade_material.albedo_color = Color(0.76, 0.9, 1.0, 1)
	blade_material.metallic = 0.85
	blade_material.roughness = 0.18
	sword.material_override = blade_material
	add_child(sword)


func inventory_snapshot() -> Dictionary:
	return inventory.items.duplicate()

func restore_inventory(items: Dictionary) -> void:
	inventory.items = items.duplicate()
	inventory_changed.emit(inventory.items.duplicate())

func export_state() -> Dictionary:
	state.position = global_position
	state.inventory = inventory_snapshot()
	return state.to_dict()

func import_state(data: Dictionary) -> void:
	state.from_dict(data)
	global_position = state.position
	restore_inventory(state.inventory)

func apply_progression(level: int, experience: int, attack: int) -> void:
	state.level = level
	state.experience = experience
	state.attack = attack
	$Nameplate.text = "Gurdock\nNv. %d" % state.level

func _physics_process(delta: float) -> void:
	animation_time += delta
	action_time = maxf(action_time - delta, 0.0)
	var input_vector := Input.get_vector("move_left", "move_right", "move_forward", "move_back")
	var direction := Vector3(input_vector.x, 0.0, input_vector.y)
	velocity.x = direction.x * SPEED
	velocity.z = direction.z * SPEED
	if not is_on_floor():
		velocity.y -= GRAVITY * delta
	else:
		velocity.y = 0.0
	move_and_slide()
	var moving := Vector2(velocity.x, velocity.z).length_squared() > 0.05
	if state.health <= 0:
		action_state = ActionState.DEAD
	elif action_time > 0.0:
		action_state = ActionState.ATTACKING
	else:
		action_state = ActionState.MOVING if moving else ActionState.IDLE
	var bob := sin(animation_time * 9.0) * (0.035 if moving else 0.012)
	$Mesh.position.y = bob
	$Nameplate.position.y = 2.1 + bob
	for index in wing_nodes.size():
		var wing := wing_nodes[index]
		wing.rotation_degrees.x = sin(animation_time * (5.0 if moving else 2.0) + index) * 8.0
		wing.position.y = 0.45 + sin(animation_time * 4.0 + index) * 0.035
	if weapon_node != null:
		weapon_node.rotation_degrees.x = -12.0 if action_time > 0.0 else 0.0
		weapon_node.rotation_degrees.z = -38.0 if action_time > 0.0 else -22.0
	if avatar_sprite != null:
		var motion_bob := sin(animation_time * (11.0 if moving else 4.0)) * (0.035 if moving else 0.012)
		var attack_pulse := clampf(action_time / 0.32, 0.0, 1.0)
		avatar_sprite.position.y = 0.82 + motion_bob + attack_pulse * 0.08
		avatar_sprite.scale = Vector3.ONE * (1.0 + attack_pulse * 0.1)
		avatar_sprite.rotation_degrees.z = sin(animation_time * 8.0) * 2.0 if moving else 0.0
	var camera_bob := sin(animation_time * (8.0 if moving else 2.5)) * (0.035 if moving else 0.012)
	$Camera.position = camera_base_position + Vector3(0, camera_bob, 0)
	state.position = global_position
	_update_target_marker()
	if Input.is_action_just_pressed("attack"):
		_attack_nearest()
	if Input.is_action_just_pressed("interact"):
		_interact_nearest()

func _update_target_marker() -> void:
	if not target_marker or not target_marker.is_inside_tree():
		return
	var nearest: Node3D = null
	if not selected_target_id.is_empty():
		for candidate in get_tree().get_nodes_in_group("enemies"):
			if str(candidate.get("target_id")) == selected_target_id and candidate.visible and not candidate.get("is_defeated"):
				nearest = candidate
				break
	var best_distance := 16.0
	if nearest == null:
		for candidate in get_tree().get_nodes_in_group("enemies"):
			if not is_instance_valid(candidate) or not candidate.visible or candidate.get("is_defeated"):
				continue
			var distance := global_position.distance_squared_to(candidate.global_position)
			if distance < best_distance:
				best_distance = distance
				nearest = candidate
	if nearest:
		target_marker.global_position = nearest.global_position + Vector3(0, 0.05, 0)
		target_marker.visible = true
	else:
		target_marker.visible = false

func _attack_nearest() -> void:
	var target: Node3D = null
	var best_distance := ATTACK_RANGE_SQUARED
	if not selected_target_id.is_empty():
		for candidate in get_tree().get_nodes_in_group("enemies"):
			if str(candidate.get("target_id")) == selected_target_id and candidate.visible and not candidate.get("is_defeated"):
				target = candidate
				break
	for candidate in get_tree().get_nodes_in_group("enemies"):
		if target != null:
			break
		if not is_instance_valid(candidate) or not candidate.visible or candidate.get("is_defeated"):
			continue
		var distance := global_position.distance_squared_to(candidate.global_position)
		if distance < best_distance:
			best_distance = distance
			target = candidate
	if target == null:
		combat_message.emit("No hay un objetivo cercano")
		return
	action_time = 0.32
	action_state = ActionState.ATTACKING
	selected_target_id = str(target.get("target_id"))
	if use_server_combat:
		attack_requested.emit(str(target.get("target_id")))
		combat_message.emit("Ataque enviado al servidor")
		return
	var damage := 10
	var defeated: bool = target.take_damage(damage)
	combat_message.emit("Ataque: %d de daño%s" % [damage, " · enemigo derrotado" if defeated else ""])
	if defeated:
		_add_item("monster_core", 1)

func _add_item(item_id: String, amount: int) -> void:
	inventory.add(item_id, amount)
	inventory_changed.emit(inventory.items.duplicate())

func _interact_nearest() -> void:
	var nearest: Node3D = null
	var best_distance := 9.0
	for npc in get_tree().get_nodes_in_group("npcs"):
		var distance := global_position.distance_squared_to(npc.global_position)
		if distance < best_distance:
			best_distance = distance
			nearest = npc
	if nearest == null:
		combat_message.emit("No hay un NPC cercano")
		return
	interact_requested.emit(str(nearest.get("npc_id")))
