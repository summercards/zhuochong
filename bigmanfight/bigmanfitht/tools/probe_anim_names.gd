extends SceneTree
## 精确列出 Godot 导入后 AnimationPlayer 的动画名（一行一个，带标记）。
## 可传参覆盖 GLB 路径：--script res://tools/probe_anim_names.gd -- <res://path.glb>

const GLB_DEFAULT := "res://assets/characters/bigman/animations/bigman_anim_v001.glb"


func _initialize() -> void:
	var glb := GLB_DEFAULT
	for a in OS.get_cmdline_user_args():
		if a.ends_with(".glb"):
			glb = a
	print("ANIMNAME_FILE %s" % glb)
	var ps: PackedScene = load(glb)
	if ps == null:
		print("ANIMNAME_FAIL")
		quit(1)
		return
	var root: Node = ps.instantiate()
	var ap := _find_ap(root)
	if ap == null:
		print("ANIMNAME_FAIL 没找到 AnimationPlayer")
		quit(1)
		return
	var names := ap.get_animation_list()
	print("ANIMNAME_COUNT %d" % names.size())
	for n in names:
		var a: Animation = ap.get_animation(n)
		print("ANIMNAME|%s|%.4f|%d" % [n, a.length, a.get_track_count()])
	quit(0)


func _find_ap(n: Node) -> AnimationPlayer:
	if n is AnimationPlayer:
		return n
	for c in n.get_children():
		var r := _find_ap(c)
		if r != null:
			return r
	return null
