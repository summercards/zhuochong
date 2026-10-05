extends Node
## 抓取几何探针：实测算出"抱着的时候两个人该隔多远"。
##
## 为什么要实测而不是推：`grab_reach` 来自 Blender 管线（`-w[1]`，即骨骼尾巴到
## **世界原点**的水平距离），而 Godot 里 root motion 是**另外**叠上去的一层位移。
## 两者是否重复计入了 0.45 m 的前冲，只有真跑一遍才知道。
##
## 探针做两件事：
##   1. 在抓取判定帧那一刻，打印**手的世界坐标**与对手身体的 X 区间 → 算出重叠量；
##   2. 由此反推理想的"被擒间距"，让手正好扣在对手身体近表面。
##
## 用法:
##   godot --headless --path . res://tools/probe_grab.tscn

var game: Game
var player: Fighter
var dummy: Fighter


func _ready() -> void:
	game = get_parent().get_node_or_null("Main") as Game
	if game == null:
		print("PROBE_FAIL 找不到 Main")
		get_tree().quit(1)
		return
	player = game.player
	dummy = game.dummy
	_run()


func _run() -> void:
	dummy.set_ai(false)
	player.set_ai(false)

	# 摆在抓取可达范围内
	var start := GameDB.grab_reach * 0.75
	dummy.reset_fighter(0.0, -1)
	dummy.opponent = player
	player.reset_fighter(-start, 1)
	player.opponent = dummy
	dummy.play_waiting()
	player.play_waiting()

	print("")
	print("=== 抓取几何实测 ===")
	print("清单 grab_reach = %.4f m（Grab_Start 判定帧上 hand.R 到原点的水平距离）" % GameDB.grab_reach)
	print("起手站位：抓取者 x=%+.4f  被擒者 x=%+.4f  间距 %.4f m" % [
		player.global_position.x, dummy.global_position.x,
		absf(dummy.global_position.x - player.global_position.x)])

	player._start_grab()

	# 等到扣住
	var guard := 0
	while player.is_holding() == false and guard < 240:
		await get_tree().physics_frame
		guard += 1
	if player.is_holding() == false:
		print("PROBE_FAIL 240 帧内没抓住")
		get_tree().quit(1)
		return

	# 扣住的瞬间：连 root motion 的滑行也一起看
	var d_after := absf(dummy.global_position.x - player.global_position.x)
	print("扣住后：抓取者 x=%+.4f（前冲了 %+.4f m）  被擒者 x=%+.4f  间距 %.4f m" % [
		player.global_position.x, player.global_position.x + start,
		dummy.global_position.x, d_after])

	# --- 手在哪里 ---
	var hand := _bone_x(player, "hand.R")
	print("抓取者 hand.R 世界 x = %+.4f（距自己原点 %+.4f m）" % [
		hand, hand - player.global_position.x])

	# --- 对手身体的 X 区间（用骨骼端点近似蒙皮范围）---
	var probe := _body_x_range(dummy)
	print("被擒者身体 X 区间 = [%+.4f, %+.4f]（近侧表面 x=%+.4f）" % [
		probe.x, probe.y, probe.x])

	var body := _body_x_range(player)
	print("抓取者身体 X 区间 = [%+.4f, %+.4f]（骨骼端点）" % [body.x, body.y])

	# --- 重叠量 ---
	var overlap: float = body.y - probe.x
	print("")
	print(">>> 两人身体重叠 = %+.4f m（正数 = 互相插进去了）" % overlap)
	print(">>> 手相对对手近侧表面 = %+.4f m（正数 = 手插进对手身体，负数 = 手没够着）" % [
		hand - probe.x])

	# 理想间距 = 当前间距 + 重叠量（把插进去的那部分退出来）
	print(">>> 若要让【身体刚好贴住】，被擒间距应取 %.4f + %.4f = %.4f m" % [
		d_after, overlap, d_after + overlap])
	print(">>> 若要让【手正好落在对手近侧表面】，间距应取 %.4f m" % [
		GameDB.grab_reach + (dummy.global_position.x - probe.x)])
	print("")

	# 再等一会儿，看 Grab_Hold 循环里的姿态（判定帧的姿态不等于抱住的姿态）
	for _i in 5:
		await get_tree().physics_frame
	var h2 := _bone_x(player, "hand.R")
	var p2 := _body_x_range(dummy)
	var b2 := _body_x_range(player)
	print("（Grab_Hold 第 5 帧）手 x=%+.4f  被擒者近侧 x=%+.4f  重叠 %+.4f m" % [
		h2, p2.x, b2.y - p2.x])

	# --- 分部位看：躯干到哪、手臂伸多远。决定"隔多远才像抱着"就靠这个 ---
	print("")
	print("--- 分部位（世界 X）---")
	_report_bones(player, "抓取者", [
		"hips", "spine", "chest", "neck", "head",
		"shoulder.R", "upperarm.R", "forearm.R", "hand.R",
		"foot.L", "foot.R"])
	_report_bones(dummy, "被擒者", [
		"hips", "spine", "chest", "neck", "head",
		"shoulder.R", "upperarm.R", "forearm.R", "hand.R",
		"foot.L", "foot.R"])

	print("")
	print("PROBE_END")
	get_tree().quit(0)


## 逐根骨骼报世界 X（相对自己原点），用来区分"躯干位置"和"手臂伸出多少"。
func _report_bones(f: Fighter, title: String, bones: Array) -> void:
	var sk := f.skeleton()
	if sk == null:
		return
	var o := f.global_position.x
	var parts: Array[String] = []
	for b in bones:
		var i := sk.find_bone(String(b))
		if i < 0:
			continue
		var x := (sk.global_transform * sk.get_bone_global_pose(i)).origin.x
		parts.append("%s=%+.3f" % [b, x - o])
	print("%s（原点 %+.4f）：%s" % [title, o, "  ".join(parts)])


## 某根骨骼的世界 X。
func _bone_x(f: Fighter, bone: String) -> float:
	var sk := f.skeleton()
	if sk == null:
		return 0.0
	var i := sk.find_bone(bone)
	if i < 0:
		return 0.0
	return (sk.global_transform * sk.get_bone_global_pose(i)).origin.x


## 用骨骼端点近似身体的 X 区间，返回 (近侧 x, 远侧 x)。
##
## 蒙皮还会外扩约一层皮厚（~0.1 m），但用来判断"插进去了还是没够着"足够了。
func _body_x_range(f: Fighter) -> Vector2:
	var sk := f.skeleton()
	if sk == null:
		return Vector2.ZERO
	var lo := 1.0e9
	var hi := -1.0e9
	for i in sk.get_bone_count():
		var x := (sk.global_transform * sk.get_bone_global_pose(i)).origin.x
		lo = minf(lo, x)
		hi = maxf(hi, x)
	return Vector2(lo, hi)
