extends Node3D

var player_id := ""
var target_position := Vector3.ZERO

func setup(id: String) -> void:
	player_id = id
	var mesh_instance := MeshInstance3D.new()
	var mesh := CapsuleMesh.new()
	mesh.radius = 0.4
	mesh.height = 1.6
	mesh_instance.mesh = mesh
	var material := StandardMaterial3D.new()
	material.albedo_color = Color(0.35, 0.85, 0.55, 1)
	mesh_instance.material_override = material
	add_child(mesh_instance)
	var nameplate := Label3D.new()
	nameplate.text = id
	nameplate.position = Vector3(0, 1.8, 0)
	nameplate.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	nameplate.font_size = 32
	nameplate.modulate = Color(0.75, 1, 0.85, 1)
	add_child(nameplate)
	var ring := MeshInstance3D.new()
	var ring_mesh := TorusMesh.new()
	ring_mesh.inner_radius = 0.42
	ring_mesh.outer_radius = 0.5
	ring.mesh = ring_mesh
	ring.rotation_degrees.x = 90
	ring.position.y = -0.8
	var ring_material := StandardMaterial3D.new()
	ring_material.albedo_color = Color(0.25, 1, 0.55, 0.8)
	ring_material.emission_enabled = true
	ring_material.emission = Color(0.05, 0.5, 0.2, 1)
	ring.material_override = ring_material
	add_child(ring)

func apply_snapshot(snapshot: Dictionary) -> void:
	var raw_position: Dictionary = snapshot.get("position", {})
	target_position = Vector3(float(raw_position.get("x", 0.0)), float(raw_position.get("y", 1.0)), float(raw_position.get("z", 0.0)))
	if position == Vector3.ZERO:
		position = target_position

func _process(delta: float) -> void:
	position = position.lerp(target_position, minf(delta * 12.0, 1.0))
