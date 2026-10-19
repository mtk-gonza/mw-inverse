extends Node3D

const ReferenceOverrideModel = preload("res://scripts/reference_override.gd")

@export var npc_id := "mentor_arin"
var reference_override = ReferenceOverrideModel.new()

func _ready() -> void:
	add_to_group("npcs")
	_build_npc_details()
	var marker := Label3D.new()
	marker.text = "Arin · Mentor" if npc_id == "mentor_arin" else ("Lynn · Intendente" if npc_id == "quartermaster_lynn" else "Sela · Guardiana")
	marker.position = Vector3(0, 2.1, 0)
	marker.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	marker.font_size = 28
	marker.modulate = Color(1, 0.82, 0.35, 1)
	add_child(marker)
	var beacon := OmniLight3D.new()
	beacon.light_color = Color(1, 0.7, 0.25)
	beacon.light_energy = 1.2
	beacon.omni_range = 3.0
	beacon.position = Vector3(0, 1.2, 0)
	add_child(beacon)

func _process(delta: float) -> void:
	var pulse := sin(Time.get_ticks_msec() * 0.003 + global_position.x) * 0.025
	for child in get_children():
		if child is Sprite3D and child.name == "OriginalNpcSprite":
			child.position.y = 0.85 + pulse

func _build_npc_details() -> void:
	var portrait := Sprite3D.new()
	portrait.name = "OriginalNpcSprite"
	portrait.texture = reference_override.load_slot("npc_%s" % npc_id, "res://assets/sprites/characters/player_avatar.svg")
	portrait.pixel_size = 0.008
	portrait.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	portrait.no_depth_test = true
	portrait.position = Vector3(0, 0.85, -0.1)
	portrait.modulate = Color(1.0, 0.78, 0.4, 0.9) if npc_id == "mentor_arin" else (Color(0.4, 1.0, 0.7, 0.9) if npc_id == "quartermaster_lynn" else Color(0.45, 0.75, 1.0, 0.9))
	add_child(portrait)
	var halo := MeshInstance3D.new()
	var halo_mesh := TorusMesh.new()
	halo_mesh.inner_radius = 0.28
	halo_mesh.outer_radius = 0.34
	halo.mesh = halo_mesh
	halo.rotation_degrees.x = 90.0
	halo.position.y = 1.15
	var halo_material := StandardMaterial3D.new()
	halo_material.albedo_color = Color(1.0, 0.74, 0.28, 1.0) if npc_id == "mentor_arin" else (Color(0.35, 1.0, 0.65, 1.0) if npc_id == "quartermaster_lynn" else Color(0.3, 0.72, 1.0, 1.0))
	halo_material.emission_enabled = true
	halo_material.emission = halo_material.albedo_color * 0.7
	halo.material_override = halo_material
	add_child(halo)
	var robe := MeshInstance3D.new()
	var robe_mesh := PrismMesh.new()
	robe_mesh.size = Vector3(0.7, 1.05, 0.35)
	robe.mesh = robe_mesh
	robe.position.y = 0.45
	var robe_material := StandardMaterial3D.new()
	robe_material.albedo_color = Color(0.55, 0.28, 0.12, 1.0) if npc_id == "mentor_arin" else (Color(0.12, 0.5, 0.28, 1.0) if npc_id == "quartermaster_lynn" else Color(0.12, 0.3, 0.52, 1.0))
	robe.material_override = robe_material
	add_child(robe)
