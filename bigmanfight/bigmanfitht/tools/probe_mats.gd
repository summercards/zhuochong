extends Node
## 探针：角色在 Godot 里**实际**拿到的是什么材质。
##
## 背景：GLB 里 91 个 primitive 全部正确绑了 17 个材质（含 Skin / Shirt_White /
## Hair_Black），但出图看角色通体蓝色。那就是导入侧的问题，不能靠猜。

var game: Game
var player: Fighter

var _count := 0
var _by_name := {}
var _no_mat: Array[String] = []
var _overrides: Array[String] = []
var _unskinned: Array[String] = []


func _ready() -> void:
	game = get_parent().get_node_or_null("Main") as Game
	player = game.player
	if player == null:
		print("MAT_FAIL 找不到玩家")
		get_tree().quit(1)
		return
	var sk := player.skeleton()
	if sk == null:
		print("MAT_FAIL 找不到 Skeleton3D")
		get_tree().quit(1)
		return
	# 从**骨架之外**也要走一遍：未蒙皮的那两件是模型根下的兄弟节点，
	# 挂不到 Skeleton3D 子树里 —— 只走骨架会直接漏掉它们（第一版就这么漏的）。
	var visual := player.get_node_or_null("Visual") as Node3D
	if visual != null:
		_visit(visual, 0)
	_visit(sk, 0)
	print("MAT_BEGIN 遍历到 %d 个 MeshInstance3D" % _count)
	var keys := _by_name.keys()
	keys.sort()
	for k in keys:
		print("   %-40s x%d" % [k, _by_name[k]])
	if not _overrides.is_empty():
		print("!! 被 material_override 覆盖的: %s" % str(_overrides))
	if not _no_mat.is_empty():
		print("!! 没有材质的: %s" % str(_no_mat))
	# 未蒙皮（没绑到 Skeleton3D）的网格 —— 它们不会跟骨骼动，会飘在静止位姿上。
	# 这是 GLB 里缺少 JOINTS_0 的那两个 Jacket_Hem 件。
	if not _unskinned.is_empty():
		print("!! 未蒙皮（不跟骨骼动）的网格 %d 个: %s" % [_unskinned.size(), str(_unskinned)])
	print("MAT_END 唯一材质数=%d" % _by_name.size())
	get_tree().quit(0)


func _visit(node: Node, depth: int) -> void:
	if depth > 8:
		return
	var mi := node as MeshInstance3D
	if mi != null:
		_probe_mesh(mi)
	for c in node.get_children():
		_visit(c, depth + 1)


func _probe_mesh(mi: MeshInstance3D) -> void:
	_count += 1
	var nm0 := String(mi.name)
	if nm0.begins_with("Jacket_Hem") or nm0.begins_with("Hem"):
		print("  >>> %s  skeleton=%s  parent=%s  pos=%s" % [
			nm0, str(mi.skeleton), mi.get_parent().get_class(), str(mi.position)])
	if mi.material_override != null:
		_overrides.append(String(mi.name))
	# Godot 的 glTF 导入器只给**蒙皮网格**设置 skeleton 引用。
	if mi.skeleton == null and mi.mesh != null:
		_unskinned.append(String(mi.name))
	var mesh := mi.mesh
	if mesh == null:
		_no_mat.append("%s(无 mesh)" % mi.name)
		return
	for i in mesh.get_surface_count():
		var m := mi.get_active_material(i)
		if m == null:
			_no_mat.append("%s[%d]" % [mi.name, i])
			continue
		var nm: String = m.resource_name
		if nm == "":
			nm = "(无名)"
		if m is StandardMaterial3D:
			var sm := m as StandardMaterial3D
			nm += " albedo=%s" % str(sm.albedo_color)
		_by_name[nm] = int(_by_name.get(nm, 0)) + 1
