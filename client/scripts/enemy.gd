extends CharacterBody3D

const ReferenceOverrideModel = preload("res://scripts/reference_override.gd")

@export var target_id := "training_dummy_1"

@export var max_health := 30
@export var health := 30
var is_defeated := false
var health_label: Label3D
var body_material: StandardMaterial3D
var visual_time := 0.0
var visual_core: MeshInstance3D
var visual_rings: Array[MeshInstance3D] = []
var enemy_sprite: Sprite3D
var hit_recoil := 0.0
var defeat_played := false
var reference_override = ReferenceOverrideModel.new()

func _ready() -> void:
	add_to_group("enemies")
	var body := get_node_or_null("Mesh") as MeshInstance3D
	if body and body.material_override:
		body_material = body.material_override.duplicate()
		body.material_override = body_material
	health_label = Label3D.new()
	health_label.text = _health_text()
	health_label.position = Vector3(0, 1.5, 0)
	health_label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	health_label.font_size = 24
	health_label.modulate = Color(1, 0.65, 0.55, 1)
	add_child(health_label)
	_build_enemy_visuals()

func _build_enemy_visuals() -> void:
	enemy_sprite = Sprite3D.new()
	enemy_sprite.name = "OriginalEnemySprite"
	var slot := "enemy_frost" if target_id.begins_with("frost_") else "enemy_fire"
	var fallback := "res://assets/sprites/enemies/enemy_frost.svg" if target_id.begins_with("frost_") else "res://assets/sprites/enemies/enemy_fire.svg"
	enemy_sprite.texture = reference_override.load_slot(slot, fallback)
	enemy_sprite.pixel_size = 0.008
	enemy_sprite.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	enemy_sprite.no_depth_test = true
	enemy_sprite.position = Vector3(0, 0.7, -0.12)
	enemy_sprite.modulate = Color(1, 1, 1, 0.94)
	add_child(enemy_sprite)
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
	hit_recoil = move_toward(hit_recoil, 0.0, delta * 5.0)
	if enemy_sprite != null:
		enemy_sprite.position.y = 0.7 + sin(visual_time * 3.0 + global_position.x) * 0.07
		enemy_sprite.position.x = hit_recoil
		enemy_sprite.scale = Vector3.ONE * (1.0 + sin(visual_time * 2.0) * 0.035)
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
		health_label.text = _health_text()
	if health == 0:
		play_defeat()
	return is_defeated

func apply_server_health(value: int) -> void:
	var previous_health := health
	var took_damage := value < health
	health = clampi(value, 0, max_health)
	if took_damage:
		_flash_hit()
		_show_damage(maxi(previous_health - health, 1))
	if health <= 0:
		play_defeat()
	else:
		is_defeated = false
		defeat_played = false
		visible = true
		scale = Vector3.ONE
		if enemy_sprite != null:
			enemy_sprite.modulate = Color(1, 1, 1, 0.94)
		set_physics_process(true)
	if health_label:
		health_label.text = _health_text()

func play_defeat() -> void:
	if defeat_played:
		return
	defeat_played = true
	is_defeated = true
	set_physics_process(false)
	var defeat_tween := create_tween()
	defeat_tween.set_parallel(true)
	defeat_tween.set_trans(Tween.TRANS_BACK)
	defeat_tween.set_ease(Tween.EASE_IN)
	defeat_tween.tween_property(self, "scale", Vector3(1.35, 0.12, 1.35), 0.28)
	if enemy_sprite != null:
		defeat_tween.tween_property(enemy_sprite, "modulate", Color(1, 0.55, 0.2, 0), 0.32)
	defeat_tween.chain().tween_callback(func() -> void:
		visible = false
	)

func _health_text() -> String:
	var filled := clampi(int(round(float(health) / maxf(float(max_health), 1.0) * 10.0)), 0, 10)
	return "%s\n%d/%d" % ["■".repeat(filled) + "□".repeat(10 - filled), health, max_health]

func _flash_hit() -> void:
	hit_recoil = -0.16
	_show_hit_spark()
	if enemy_sprite != null:
		enemy_sprite.modulate = Color(1.8, 1.55, 0.75, 1.0)
		var sprite_tween := create_tween()
		sprite_tween.tween_property(enemy_sprite, "modulate", Color(1, 1, 1, 0.94), 0.18)
	if not body_material:
		return
	var base_color := body_material.albedo_color
	var tween := create_tween()
	tween.tween_property(body_material, "albedo_color", Color(1, 0.95, 0.35, 1), 0.06)
	tween.tween_property(body_material, "albedo_color", base_color, 0.14)

func _show_hit_spark() -> void:
	var spark := Sprite3D.new()
	spark.texture = reference_override.load_slot("hit_spark", "res://assets/sprites/effects/hit_spark.svg")
	spark.pixel_size = 0.0045
	spark.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	spark.no_depth_test = true
	spark.position = Vector3(0, 0.9, -0.2)
	add_child(spark)
	var tween := create_tween()
	tween.set_parallel(true)
	tween.tween_property(spark, "scale", Vector3(1.8, 1.8, 1.8), 0.18)
	tween.tween_property(spark, "modulate", Color(1, 0.8, 0.25, 0), 0.18)
	tween.chain().tween_callback(spark.queue_free)

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
