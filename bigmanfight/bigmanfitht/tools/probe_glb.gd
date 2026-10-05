extends SceneTree
## 导入探针：实测 GLB 在 Godot 里长什么样（节点树 / 骨骼 / 动画 / 尺寸 / 朝向）。
##
## 用法:
##   godot --headless --path <project> --script res://tools/probe_glb.gd

const GLB := "res://assets/characters/bigman/animations/bigman_anim_v001.glb"


func _initialize() -> void:
	if not ResourceLoader.exists(GLB):
		print("PROBE_FAIL 资源不存在: ", GLB)
		quit(1)
		return

	var ps: PackedScene = load(GLB)
	if ps == null:
		print("PROBE_FAIL load() 返回 null")
		quit(1)
		return

	var root: Node = ps.instantiate()
	get_root().add_child(root)

	print("=== 节点树 ===")
	_walk(root, 0)

	var skels := _find_all(root, "Skeleton3D")
	for s in skels:
		_probe_skeleton(s)

	var aps := _find_all(root, "AnimationPlayer")
	for ap in aps:
		_probe_anim(ap)

	var meshes := _find_all(root, "MeshInstance3D")
	print("=== 网格 ===")
	print("MeshInstance3D 总数: ", meshes.size())
	var total_tris := 0
	for m in meshes:
		if m.mesh != null:
			for i in m.mesh.get_surface_count():
				var arr: Array = m.mesh.surface_get_arrays(i)
				var idx: PackedInt32Array = arr[Mesh.ARRAY_INDEX]
				total_tris += idx.size() / 3
	print("三角面合计: ", total_tris)

	# 世界空间包围盒
	var aabb := _world_aabb(root)
	print("=== 世界包围盒 ===")
	print("min = ", aabb.position)
	print("max = ", aabb.position + aabb.size)
	print("size = ", aabb.size)

	quit(0)


func _walk(n: Node, depth: int) -> void:
	var extra := ""
	if n is Node3D:
		extra = "  pos=%s rot_y=%.4f scale=%s" % [
			Vector3(n.position).snapped(Vector3(0.001, 0.001, 0.001)),
			n.rotation.y, n.scale]
	print("%s%s (%s)%s" % ["  ".repeat(depth), n.name, n.get_class(), extra])
	for c in n.get_children():
		_walk(c, depth + 1)


func _find_all(n: Node, cls: String) -> Array:
	var out: Array = []
	if n.is_class(cls):
		out.append(n)
	for c in n.get_children():
		out.append_array(_find_all(c, cls))
	return out


func _probe_skeleton(s: Skeleton3D) -> void:
	print("=== 骨架 ===")
	print("name=", s.name, "  bone_count=", s.get_bone_count())
	var want := ["root", "pelvis", "chest", "head", "eye.L", "eye.R", "hand.L", "hand.R",
		"thigh.L", "foot.L", "toe.L"]
	for w in want:
		var i := s.find_bone(w)
		if i < 0:
			print("  %-10s <缺失>" % w)
			continue
		var t: Transform3D = s.global_transform * s.get_bone_global_rest(i)
		print("  %-10s idx=%-3d rest_global_origin=%s" % [w, i, t.origin.snapped(Vector3(0.0001, 0.0001, 0.0001))])


func _probe_anim(ap: AnimationPlayer) -> void:
	print("=== 动画 ===")
	var names := ap.get_animation_list()
	print("AnimationPlayer=", ap.name, "  动画数=", names.size())
	var total := 0.0
	for nm in names:
		var a: Animation = ap.get_animation(nm)
		total += a.length
	print("总时长 = %.3f s" % total)
	for nm in names:
		var a: Animation = ap.get_animation(nm)
		print("  %-20s len=%.4f s  tracks=%d  loop=%s" % [
			nm, a.length, a.get_track_count(), str(a.loop_mode)])


func _world_aabb(root: Node) -> AABB:
	var out := AABB()
	var first := true
	for m in _find_all(root, "MeshInstance3D"):
		if m.mesh == null:
			continue
		var local: AABB = m.mesh.get_aabb()
		var xf: Transform3D = m.global_transform
		var corners := [
			Vector3(local.position.x, local.position.y, local.position.z),
			Vector3(local.position.x + local.size.x, local.position.y, local.position.z),
			Vector3(local.position.x, local.position.y + local.size.y, local.position.z),
			Vector3(local.position.x, local.position.y, local.position.z + local.size.z),
			Vector3(local.position.x + local.size.x, local.position.y + local.size.y, local.position.z),
			Vector3(local.position.x + local.size.x, local.position.y, local.position.z + local.size.z),
			Vector3(local.position.x, local.position.y + local.size.y, local.position.z + local.size.z),
			Vector3(local.position.x + local.size.x, local.position.y + local.size.y, local.position.z + local.size.z),
		]
		for c in corners:
			var w: Vector3 = xf * c
			if first:
				out = AABB(w, Vector3.ZERO)
				first = false
			else:
				out = out.expand(w)
	return out
