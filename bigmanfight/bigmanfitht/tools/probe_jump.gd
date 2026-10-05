extends Node
## 跳跃高度探针：实测算出 `Jump_*` 四段里骨盆到底抬升了多少。
##
## ---------------------------------------------------------------------------
## 为什么必须实测，而不是"看一眼动画觉得挺高"：
##
##   工程纪律是**不新增动画**，而资产里的跳是**动画驱动**的 ——
##   角色根节点 y 恒为 0（`Fighter` 里明确不加重力，见 docs/操作说明.md §4.2），
##   纵向弹道全部在动画内部的**骨盆**上。
##
##   于是"地面除了前后还有上下"这件事，能不能成立、能抬多高、什么时候最高、
##   在空中待多久 —— 全都取决于这个骨盆曲线。这三个数**不能猜**：
##     · 抬升量决定"空中攻击够不够得着对面"（受击体要不要跟着上移、上移多少）
##     · 最高点时刻决定"跑动跳踢"的飞踢落在哪一帧才有意义
##     · 滞空时长决定"跳起来能不能躲开下段攻击"
##
##   探针做的就是逐帧把骨盆/脚尖的**世界 Y** 打印出来。
##
## 用法:
##   godot --headless --path . res://tools/probe_jump.tscn

## 采样帧数上限。Jump 四段总时长 0.6+0.2+0.4+0.5 = 1.7 s = 102 帧 @60fps，
## 多留一倍余量（状态机切换会吃掉一两帧）。
const MAX_FRAMES := 240

var game: Game
var player: Fighter
var dummy: Fighter
var _sk: Skeleton3D
## 骨盆骨骼名。**不是 `hips`** —— 实测这份资产的 57 根关节里叫 `pelvis`
## （`hips` 会静默返回 -1；probe_grab 的 `_report_bones` 就是靠 continue 吞掉了它）。
const PELVIS_BONE := "pelvis"
const TOE_BONE := "toe.L"
var _hips := -1
var _toe := -1


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
	# 拉到两侧，避免推箱夹逼干扰（跳跃本身不调用 _move_world，但保险）
	dummy.reset_fighter(3.0, -1)
	dummy.opponent = player
	player.reset_fighter(-3.0, 1)
	player.opponent = dummy
	dummy.play_waiting()
	player.play_waiting()

	_sk = player.skeleton()
	if _sk == null:
		print("PROBE_FAIL 拿不到骨架")
		get_tree().quit(1)
		return
	_hips = _sk.find_bone(PELVIS_BONE)
	_toe = _sk.find_bone(TOE_BONE)
	if _hips < 0 or _toe < 0:
		var all: Array[String] = []
		for i in _sk.get_bone_count():
			all.append(_sk.get_bone_name(i))
		print("PROBE_FAIL 找不到 %s / %s 骨骼；实有 %d 根：%s" % [
			PELVIS_BONE, TOE_BONE, all.size(), str(all)])
		get_tree().quit(1)
		return

	# 等两帧让 Idle_01 的姿态真正落到骨架上
	for _i in 2:
		await get_tree().physics_frame

	var rest_hips: float = _sk.get_bone_global_rest(_hips).origin.y
	var ground_hips := _bone_y(_hips)
	var ground_toe := _bone_y(_toe)

	print("")
	print("=== 跳跃骨盆抬升实测 ===")
	print("清单：Jump_Start %.2fs(36f) → Jump_Up %.2fs(12f) → Jump_Fall %.2fs(24f) → Jump_Land %.2fs(30f)" % [
		GameDB.duration("Jump_Start"), GameDB.duration("Jump_Up"),
		GameDB.duration("Jump_Fall"), GameDB.duration("Jump_Land")])
	print("骨盆(pelvis) 静止位姿 y = %.4f m" % rest_hips)
	print("Idle_01@0 的 pelvis 世界 y = %.4f m（作为地面基准）" % ground_hips)
	print("Idle_01@0 的 toe.L 世界 y = %.4f m（脚底）" % ground_toe)
	print("")

	# --- 起跳：直接走状态机（和真按一下跳跃键等价）---
	player._set_state(Fighter.St.JUMP)
	player._jump_index = 0
	player._jump_air = false
	player._play(Fighter.JUMP_SEQ[0], 0.0)

	var rows: Array = []
	var prev_clip := ""
	for i in MAX_FRAMES:
		await get_tree().physics_frame
		var clip := player.clip_name()
		var rise: float = _bone_y(_hips) - ground_hips
		var toe_y: float = _bone_y(_toe)
		rows.append({
			"i": i,
			"clip": clip,
			"frame": player.current_frame(),
			"hips": _bone_y(_hips),
			"rise": rise,
			"toe": toe_y,
		})
		if clip != prev_clip:
			print("--- 第 %3d 帧 进入 %-10s（骨盆 y=%+.4f  抬升 %+.4f）" % [
				i, clip, _bone_y(_hips), rise])
			prev_clip = clip
		if player.state != Fighter.St.JUMP:
			print("--- 第 %3d 帧 离开 JUMP（状态回到 %s）" % [i, player.label()])
			break

	# --- 逐帧明细（每 4 帧一行，够看出曲线的形状）---
	print("")
	print("--- 逐帧骨盆抬升（每 4 帧一行）---")
	var line := []
	for r in rows:
		if int(r["i"]) % 4 != 0:
			continue
		line.append("%d:%s%+.3f" % [r["i"], String(r["clip"]).substr(0, 4), r["rise"]])
	print("  ".join(line))

	# --- 结论 ---
	var max_rise := -99.0
	var max_i := -1
	var max_clip := ""
	var air_frames := 0
	var first_air := -1
	var last_air := -1
	for r in rows:
		var rise: float = r["rise"]
		if rise > max_rise:
			max_rise = rise
			max_i = int(r["i"])
			max_clip = String(r["clip"])
		# "离地"判据：脚尖离开地面 3 cm 以上（3 cm 是留的余量，不是阈值参数）
		if r["toe"] > ground_toe + 0.03:
			air_frames += 1
			if first_air < 0:
				first_air = int(r["i"])
			last_air = int(r["i"])

	print("")
	print(">>> 骨盆最高抬升 = %+.4f m（第 %d 帧，%s）" % [max_rise, max_i, max_clip])
	print(">>> 抬升时刻 = 起跳后 %.3f s" % (float(max_i) / 60.0))
	print(">>> 脚尖离地帧 = [%d, %d]，滞空 %d 帧 = %.3f s" % [
		first_air, last_air, air_frames, float(air_frames) / 60.0])
	print(">>> 抬升 = 受击体上移量（根节点 y 仍恒为 0，不做双重位移）")
	print(">>> 空中攻击命中帧的骨盆抬升：")

	for c in ["Air_Light", "Air_Heavy"]:
		var hf: Variant = GameDB.hit_frame(c)
		if hf == null:
			continue
		var hp: Dictionary = {}
		var pts: Variant = GameDB.clip(c).get("hit_points")
		if pts is Array and (pts as Array).size() > 0:
			hp = (pts as Array)[0]
		print("      %-10s 判定帧 %s（%.3f s）  命中点高度 %.4f m  可达 %.4f m" % [
			c, str(hf), float(hf) / 60.0,
			float(hp.get("height_m", 0.0)), float(hp.get("reach_m", 0.0))])

	# --- 空中攻击自己的骨盆曲线 ---
	# 这段曲线决定"空中攻击期间受击体该上移多少"。空中家族是**另一条弹道**，
	# 不能拿跳跃那条的曲线套用 —— 实测一版就看得出来差多少。
	print("")
	print("--- 空中攻击的骨盆曲线（各自从头播一遍）---")
	for c in ["Air_Light", "Air_Heavy"]:
		player._set_state(Fighter.St.ATTACK)
		player._play(c, 0.0)
		var n := int(GameDB.frame_count(c)) + 2
		var first := 0.0
		var peak := -99.0
		var peak_i := -1
		var tail := 0.0
		var acc: Array[String] = []
		for i in n:
			await get_tree().physics_frame
			var r: float = _bone_y(_hips) - ground_hips
			if i == 0:
				first = r
			if r > peak:
				peak = r
				peak_i = i
			tail = r
			if i % 3 == 0:
				acc.append("%d:%+.3f" % [i, r])
		print("  %-10s 起点 %+.4f → 峰值 %+.4f（第 %d 帧）→ 末帧 %+.4f" % [
			c, first, peak, peak_i, tail])
		print("             %s" % "  ".join(acc))

	# --- 手在哪里（手持/投掷的挂点依据）---
	# 清单里已经登记了 hand.R 在判定帧的世界坐标（reach/height/lateral），
	# 这里真跑一遍核对一遍 —— 挂点如果和清单对不上，"手里拿着的东西"就会飘。
	print("")
	print("--- 判定帧上的 hand.R 世界坐标（核对 manifest 的 hit_points）---")
	for spec in [["Grab_Start", 28], ["Throw", 28]]:
		var c := String(spec[0])
		player._set_state(Fighter.St.ATTACK)
		player._play(c, 0.0)
		while player.current_frame() < float(spec[1]):
			await get_tree().physics_frame
		var hand: Vector3 = _bone_pos(_sk.find_bone("hand.R"))
		var hp: Dictionary = (GameDB.clip(c).get("hit_points") as Array)[0]
		print("  %-11s @%d 帧  实测 hand.R = (%.4f, %.4f, %.4f)  相对原点 (%.4f, %.4f, %.4f)" % [
			c, int(spec[1]), hand.x, hand.y, hand.z,
			hand.x - player.global_position.x, hand.y, hand.z])
		print("             manifest 登记 reach=%+.4f height=%+.4f lateral=%+.4f" % [
			float(hp.get("reach_m", 0.0)), float(hp.get("height_m", 0.0)),
			float(hp.get("lateral_m", 0.0))])

	print("")
	print("PROBE_END")
	get_tree().quit(0)


## 某根骨骼的**世界** Y（含 Visual 的旋转，所以是真·世界坐标）。
func _bone_y(idx: int) -> float:
	if _sk == null or idx < 0:
		return 0.0
	return (_sk.global_transform * _sk.get_bone_global_pose(idx)).origin.y


## 某根骨骼的世界坐标。
func _bone_pos(idx: int) -> Vector3:
	if _sk == null or idx < 0:
		return Vector3.ZERO
	return (_sk.global_transform * _sk.get_bone_global_pose(idx)).origin
