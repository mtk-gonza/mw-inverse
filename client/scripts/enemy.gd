extends CharacterBody3D

@export var target_id := "training_dummy_1"

@export var max_health := 30
@export var health := 30
var is_defeated := false
var health_label: Label3D
var body_material: StandardMaterial3D
var visual_time := 0.0
var visual_core: MeshInstance3D
var visual_rings: Array[MeshInstance3D] = []

func _ready() -> void:
	add_to_group("enemies")
	var body := get_node_or_null("Mesh") as MeshInstance3D
	if body and body.material_override:
		body_material = body.material_override.duplicate()
		body.material_override = body_material
	health_label = Label3D.new()
	health_label.text = "Enemigo · %d/%d" % [health, max_health]
	health_label.position = Vector3(0, 1.5, 0)
	health_label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	health_label.font_size = 24
	health_label.modulate = Color(1, 0.65, 0.55, 1)
	add_child(health_label)
	_build_enemy_visuals()

func _build_enemy_visuals() -> void:
	var core := MeshInstance3D.new()
	visual_core = core
	var core_mesh := SphereMesh.new()
	core_mesh.radius = 0.45 if target_id.begins_with("frost_") else 0.32
	core_mesh.height = core_mesh.radius * 2.0
	core.mesh = core_mesh
	core.position = Vector3(0, 0.55, 0)
	var core_material := StandardMaterial3D.new()
	core_material.albedo_color = Color(0.2, 0.75, 1.0, 0.9) if target_id.begins_with("frost_") else Color(1.0, 0.28, 0.18, 0.9)
	core_material.emission_enabled = true
	core_material.emission = core_material.albedo_color * 0.65
	core.material_override = core_material
	add_child(core)
	for index in 3 if target_id == "frost_guardian" else 1:
		var ring := MeshInstance3D.new()
		var ring_mesh := TorusMesh.new()
		ring_mesh.inner_radius = 0.52 + index * 0.14
		ring_mesh.outer_radius = 0.57 + index * 0.14
		ring.mesh = ring_mesh
		ring.rotation_degrees.x = 90.0
		ring.position.y = 0.55 + index * 0.12
		ring.material_override = core_material
		add_child(ring)
		visual_rings.append(ring)

func _physics_process(delta: float) -> void:
	visual_time += delta
	if visual_core != null:
		visual_core.position.y = 0.55 + sin(visual_time * 3.0 + global_position.x) * 0.08
	for index in visual_rings.size():
		var ring := visual_rings[index]
		ring.rotation_degrees.y = visual_time * (28.0 + index * 9.0)
		ring.position.y = 0.55 + index * 0.12 + sin(visual_time * 2.0 + index) * 0.04


func take_damage(amount: int) -> bool:
	if is_defeated:
		return true
	health = maxi(health - amount, 0)
	_flash_hit()
	_show_damage(amount)
	if health_label:
		health_label.text = "Enemigo · %d/%d" % [health, max_health]
	if health == 0:
		is_defeated = true
		visible = false
		set_physics_process(false)
	return is_defeated

func apply_server_health(value: int) -> void:
	health = clampi(value, 0, max_health)
	is_defeated = health <= 0
	visible = not is_defeated
	set_physics_process(not is_defeated)
	if health_label:
		health_label.text = "Enemigo · %d/%d" % [health, max_health]

func _flash_hit() -> void:
	if not body_material:
		return
	var base_color := body_material.albedo_color
	var tween := create_tween()
	tween.tween_property(body_material, "albedo_color", Color(1, 0.95, 0.35, 1), 0.06)
	tween.tween_property(body_material, "albedo_color", base_color, 0.14)

func _show_damage(amount: int) -> void:
	var damage_label := Label3D.new()
	damage_label.text = "-%d" % amount
	damage_label.position = Vector3(0, 1.9, 0)
	damage_label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	damage_label.font_size = 38
	damage_label.modulate = Color(1, 0.25, 0.2, 1)
	add_child(damage_label)
	var tween := create_tween()
	tween.set_parallel(true)
	tween.tween_property(damage_label, "position", Vector3(0, 2.8, 0), 0.65)
	tween.tween_property(damage_label, "modulate", Color(1, 0.25, 0.2, 0), 0.65)
	tween.chain().tween_callback(damage_label.queue_free)
