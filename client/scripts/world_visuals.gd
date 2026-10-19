extends Node3D

var animated_objects: Array[Node3D] = []
var elapsed := 0.0

func _ready() -> void:
	_build_forest()
	_build_crystals()
	_build_lanterns()
	_build_ice_ridge()
	_build_snow_sparks()
	_build_reference_natural_props()
	_build_region_portals()
	_build_region_landmarks()
	_build_shrines()

func _process(delta: float) -> void:
	elapsed += delta
	for index in animated_objects.size():
		var object := animated_objects[index]
		if is_instance_valid(object):
			object.position.y += sin(elapsed * 1.5 + float(index)) * 0.002

func _material(color: Color, emission := Color(0, 0, 0, 1)) -> StandardMaterial3D:
	var result := StandardMaterial3D.new()
	result.albedo_color = color
	result.roughness = 0.72
	if emission != Color(0, 0, 0, 1):
		result.emission_enabled = true
		result.emission = emission
		result.emission_energy_multiplier = 1.8
	return result

func _mesh(parent: Node3D, mesh: Mesh, material: Material, position: Vector3) -> MeshInstance3D:
	var instance := MeshInstance3D.new()
	instance.mesh = mesh
	instance.material_override = material
	instance.position = position
	parent.add_child(instance)
	return instance

func _build_forest() -> void:
	var positions := [Vector3(-6, 0.7, -5), Vector3(6, 0.7, -5), Vector3(7, 0.7, 2), Vector3(-7, 0.7, 2), Vector3(3, 0.7, 3)]
	for position in positions:
		var tree := Node3D.new()
		tree.name = "ProceduralTree"
		add_child(tree)
		var trunk := CylinderMesh.new()
		trunk.top_radius = 0.18
		trunk.bottom_radius = 0.28
		trunk.height = 1.5
		_mesh(tree, trunk, _material(Color(0.28, 0.16, 0.12)), Vector3(0, 0.75, 0))
		for layer in 3:
			var foliage := CylinderMesh.new()
			foliage.top_radius = 0.05
			foliage.bottom_radius = 1.15 - float(layer) * 0.22
			foliage.height = 1.2
			_mesh(tree, foliage, _material(Color(0.08 + layer * 0.025, 0.32 + layer * 0.03, 0.24)), Vector3(0, 1.5 + layer * 0.65, 0))
		tree.position = position

func _build_crystals() -> void:
	var positions := [Vector3(-5, 0.9, 0), Vector3(5, 0.9, 0), Vector3(2, 0.9, -6), Vector3(-2, 0.9, -6)]
	for index in positions.size():
		var crystal := Node3D.new()
		crystal.name = "IceCrystal"
		add_child(crystal)
		var prism := PrismMesh.new()
		prism.size = Vector3(0.45, 1.8 + float(index % 2) * 0.6, 0.45)
		var shard := _mesh(crystal, prism, _material(Color(0.35, 0.75, 1, 0.9), Color(0.08, 0.3, 0.8)), Vector3.ZERO)
		var reference_fx := Sprite3D.new()
		reference_fx.name = "ReferenceCrystalFx"
		var reference_fx_path := "res://assets/reference-library/Sprite/sharedassets0_fx_rank_rays_0_857.png"
		if ResourceLoader.exists(reference_fx_path):
			reference_fx.texture = load(reference_fx_path) as Texture2D
		reference_fx.pixel_size = 0.004
		reference_fx.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		reference_fx.no_depth_test = true
		reference_fx.modulate = Color(0.35, 0.75, 1.0, 0.55)
		reference_fx.position = Vector3(0, 0.45, 0)
		crystal.add_child(reference_fx)
		shard.rotation_degrees = Vector3(0, index * 37.0, 12)
		crystal.position = positions[index]
		animated_objects.append(crystal)

func _build_lanterns() -> void:
	for position in [Vector3(-7, 0.8, -1), Vector3(7, 0.8, -1), Vector3(0, 0.8, 4)]:
		var lantern := OmniLight3D.new()
		lantern.name = "WarmLantern"
		lantern.position = position + Vector3(0, 1.4, 0)
		lantern.light_color = Color(1, 0.55, 0.22)
		lantern.light_energy = 1.6
		lantern.omni_range = 4.0
		add_child(lantern)

func _build_ice_ridge() -> void:
	var positions := [Vector3(-7.5, 0.55, -6.5), Vector3(-3.5, 0.55, -7.5), Vector3(2.5, 0.55, -7.5), Vector3(7.5, 0.55, -5.5), Vector3(-7.5, 0.55, 5.5), Vector3(0, 0.55, 5.7), Vector3(7.5, 0.55, 5.0)]
	for index in positions.size():
		var chunk := BoxMesh.new()
		chunk.size = Vector3(1.8 + (index % 2), 0.65, 1.1)
		var object := _mesh(self, chunk, _material(Color(0.7, 0.9, 1, 1)), positions[index])
		object.rotation_degrees.y = index * 23.0

func _build_snow_sparks() -> void:
	for index in 18:
		var spark := MeshInstance3D.new()
		var mesh := SphereMesh.new()
		mesh.radius = 0.025
		mesh.height = 0.05
		spark.mesh = mesh
		spark.material_override = _material(Color(0.8, 0.95, 1, 0.8), Color(0.3, 0.55, 1, 1))
		spark.position = Vector3(-8.0 + fmod(float(index * 3), 16.0), 1.2 + float(index % 4) * 0.45, -7.0 + fmod(float(index * 5), 14.0))
		add_child(spark)
		animated_objects.append(spark)

func _build_reference_natural_props() -> void:
	var props := [
		{"mesh": "resources_TFF_Lotus_Flower_01B_461.obj", "position": Vector3(-4.8, 0.35, -1.5), "scale": 0.012},
		{"mesh": "resources_TFF_Lotus_Flower_02A_460.obj", "position": Vector3(4.5, 0.35, 0.8), "scale": 0.012},
		{"mesh": "resources_TFF_Mushroom_01A_01_467.obj", "position": Vector3(-6.0, 0.35, 1.8), "scale": 0.01},
		{"mesh": "resources_TFF_Mushroom_01A_02_466.obj", "position": Vector3(6.2, 0.35, 2.4), "scale": 0.01},
		{"mesh": "resources_TFF_Debris_01A_462.obj", "position": Vector3(2.8, 0.35, -4.2), "scale": 0.012},
	]
	for item in props:
		var mesh := _load_reference_obj("res://assets/reference-library/Mesh/" + item.mesh)
		if mesh == null:
			continue
		var prop := MeshInstance3D.new()
		prop.name = "ReferenceNaturalProp"
		prop.mesh = mesh
		prop.position = item.position
		prop.scale = Vector3.ONE * float(item.scale)
		prop.rotation_degrees.y = randf_range(0.0, 360.0)
		prop.material_override = _material(Color(0.22, 0.48, 0.38), Color(0.04, 0.16, 0.12))
		add_child(prop)

func _load_reference_obj(path: String) -> ArrayMesh:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return null
	var vertices: Array[Vector3] = []
	var normals: Array[Vector3] = []
	var uvs: Array[Vector2] = []
	var surface := SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	while not file.eof_reached():
		var line := file.get_line().strip_edges()
		if line.begins_with("v "):
			var values := line.split(" ", false)
			vertices.append(Vector3(float(values[1]), float(values[2]), float(values[3])))
		elif line.begins_with("vn "):
			var values := line.split(" ", false)
			normals.append(Vector3(float(values[1]), float(values[2]), float(values[3])))
		elif line.begins_with("vt "):
			var values := line.split(" ", false)
			uvs.append(Vector2(float(values[1]), float(values[2])))
		elif line.begins_with("f "):
			var parts := line.split(" ", false)
			for triangle in range(1, parts.size() - 2):
				for part_index in [1, triangle + 1, triangle + 2]:
					var indices := parts[part_index].split("/")
					var vertex_index := int(indices[0]) - 1
					if vertex_index < 0 or vertex_index >= vertices.size():
						continue
					if indices.size() > 1 and not indices[1].is_empty():
						var uv_index := int(indices[1]) - 1
						if uv_index >= 0 and uv_index < uvs.size():
							surface.set_uv(uvs[uv_index])
					if indices.size() > 2 and not indices[2].is_empty():
						var normal_index := int(indices[2]) - 1
						if normal_index >= 0 and normal_index < normals.size():
							surface.set_normal(normals[normal_index])
					surface.add_vertex(vertices[vertex_index])
	var result := surface.commit()
	return result as ArrayMesh

func _build_region_portals() -> void:
	for data in [
		{"position": Vector3(13.5, 1.2, 0), "color": Color(1.0, 0.65, 0.25), "label": "PUERTO"},
		{"position": Vector3(-13.5, 1.2, 0), "color": Color(0.25, 0.75, 1.0), "label": "BOSQUE (Nv. 3)"},
	]:
		var portal := Node3D.new()
		portal.name = "RegionPortal"
		portal.position = data.position
		add_child(portal)
		var ring := MeshInstance3D.new()
		var ring_mesh := TorusMesh.new()
		ring_mesh.inner_radius = 0.72
		ring_mesh.outer_radius = 0.84
		ring.mesh = ring_mesh
		ring.rotation_degrees.x = 90.0
		var material := _material(data.color, data.color * 0.7)
		ring.material_override = material
		portal.add_child(ring)
		var marker := Label3D.new()
		marker.text = data.label
		marker.position = Vector3(0, 1.35, 0)
		marker.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		marker.font_size = 22
		marker.modulate = data.color
		portal.add_child(marker)

func _build_region_landmarks() -> void:
	var harbor := Node3D.new()
	harbor.name = "QuietHarborLandmarks"
	harbor.set_meta("region_id", "quiet_harbor")
	harbor.add_to_group("region_landmarks")
	add_child(harbor)
	var dock := MeshInstance3D.new()
	var dock_mesh := BoxMesh.new()
	dock_mesh.size = Vector3(6.0, 0.28, 1.6)
	dock.mesh = dock_mesh
	dock.position = Vector3(0, 0.65, 5.0)
	dock.material_override = _material(Color(0.32, 0.2, 0.14))
	harbor.add_child(dock)
	for x in [-2.3, 2.3]:
		var post := MeshInstance3D.new()
		var post_mesh := CylinderMesh.new()
		post_mesh.top_radius = 0.12
		post_mesh.bottom_radius = 0.16
		post_mesh.height = 1.7
		post.mesh = post_mesh
		post.position = Vector3(x, 1.0, 5.0)
		post.material_override = _material(Color(0.22, 0.13, 0.1))
		harbor.add_child(post)
	var frost := Node3D.new()
	frost.name = "FrostwoodLandmarks"
	frost.set_meta("region_id", "frostwood")
	frost.add_to_group("region_landmarks")
	add_child(frost)
	for position in [Vector3(-5, 0.9, -7), Vector3(5, 0.9, -7), Vector3(-7, 0.9, 4), Vector3(7, 0.9, 4)]:
		var crystal := MeshInstance3D.new()
		var crystal_mesh := PrismMesh.new()
		crystal_mesh.size = Vector3(0.65, 2.2, 0.65)
		crystal.mesh = crystal_mesh
		crystal.position = position
		crystal.rotation_degrees.y = randf_range(0.0, 180.0)
		crystal.material_override = _material(Color(0.32, 0.72, 1.0, 0.9), Color(0.08, 0.32, 0.9))
		frost.add_child(crystal)

func _build_shrines() -> void:
	var shrines := [
		{"id": "frost_lantern", "region": "training_meadow", "position": Vector3(-1.5, 0.8, 2.5), "color": Color(1.0, 0.65, 0.25)},
		{"id": "harbor_beacon", "region": "quiet_harbor", "position": Vector3(0, 0.8, 3.8), "color": Color(0.25, 0.8, 1.0)},
		{"id": "frostwood_root", "region": "frostwood", "position": Vector3(0, 0.8, -6.5), "color": Color(0.45, 0.65, 1.0)},
	]
	for data in shrines:
		var shrine := Node3D.new()
		shrine.name = str(data.id)
		shrine.set_meta("shrine_id", data.id)
		shrine.set_meta("region_id", data.region)
		shrine.add_to_group("shrines")
		shrine.position = data.position
		add_child(shrine)
		var pedestal := MeshInstance3D.new()
		var pedestal_mesh := CylinderMesh.new()
		pedestal_mesh.top_radius = 0.32
		pedestal_mesh.bottom_radius = 0.48
		pedestal_mesh.height = 0.5
		pedestal.mesh = pedestal_mesh
		pedestal.material_override = _material(Color(0.18, 0.22, 0.35))
		shrine.add_child(pedestal)
		var flame := MeshInstance3D.new()
		var flame_mesh := SphereMesh.new()
		flame_mesh.radius = 0.2
		flame_mesh.height = 0.55
		flame.mesh = flame_mesh
		flame.position.y = 0.55
		flame.material_override = _material(data.color, data.color)
		shrine.add_child(flame)
		var label := Label3D.new()
		label.text = "Santuario"
		label.position.y = 1.25
		label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		label.font_size = 20
		label.modulate = data.color
		shrine.add_child(label)
