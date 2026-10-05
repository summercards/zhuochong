extends Node
## 可拾取物探针：把"捡起来 / 拿在手里砸 / 扔出去 / 打碎 / 跳踢 / 纵向躲避"
## 这条链路真跑一遍，并逐项打印实测值。
##
## 为什么要有这个探针（而不是直接写进冒烟）：
##   冒烟跑一遍要一分多钟，而这套机制在调的时候要反复试。
##   探针只跑这一条链路，改一次跑一次，几秒出结果。
##   结论稳定之后，把关键断言搬进 `tools/smoke_probe.gd` 当门禁。
##
## 用法:
##   godot --headless --path . res://tools/probe_props.tscn

const PELVIS := "pelvis"

## 测试用输入源：按脚本逐帧吐 `InputFrame`。用来真跑"连按两次方向"和
## "跑动中按拳脚"这两条**走输入**的路径（内部函数直接调用测不出边沿识别）。
class ScriptedAI extends DummyAI:
	var seq: Array = []
	var i := 0

	func feed(list: Array) -> void:
		seq = []
		for f in list:
			seq.append(f)
		i = 0

	func poll(_me: Node3D, _opponent: Node3D, _delta: float) -> InputFrame:
		if i < seq.size():
			var f: InputFrame = seq[i]
			i += 1
			return f
		return InputFrame.new()


var game: Game
var player: Fighter
var dummy: Fighter
var mgr: CarryableManager

var _fails := 0
var _checks := 0


func _ready() -> void:
	game = get_parent().get_node_or_null("Main") as Game
	if game == null:
		print("PROBE_FAIL 找不到 Main")
		get_tree().quit(1)
		return
	player = game.player
	dummy = game.dummy
	mgr = game.carryables
	_run()


func _run() -> void:
	print("")
	print("=========== 可拾取物链路实测 ===========")
	_section("0. 铺场")
	_quiet()
	await _frames(6)

	_check("场上有 %d 个箱子" % GameDB.PROP_COUNT, mgr.props.size() == GameDB.PROP_COUNT,
		"实得 %d 个" % mgr.props.size())
	var sizes: Array[String] = []
	for p in mgr.props:
		sizes.append("%.2f" % p.size_m)
	print("     边长 = %s m（三档 %s）" % [str(sizes), str(GameDB.prop_sizes.map(
		func(v: float) -> String: return "%.2f" % v))])
	_check("全都在场上躺着（IDLE 可拾取）",
		mgr.pickable_count() == GameDB.PROP_COUNT,
		"%d / %d" % [mgr.pickable_count(), GameDB.PROP_COUNT])
	_check("箱子是确定性分布（同一种子两次结果一致）", _placement_stable(),
		"重铺一次后出生点一致")

	_section("1. 捡起来")
	_only(0, 0.75)                          # 只留 0 号箱，玩家正前方 0.75 m
	var box: Carryable = mgr.props[0]
	_check("0 号箱回到可拾取", box.is_pickable(), "state=%d" % box.state)
	player._start_pick()
	_check("按拾取键起手：进入 GRAB 并播 Grab_Start（复用「伸手取物」那一段）",
		player.state == Fighter.St.GRAB and player.clip_name() == "Grab_Start",
		"状态=%s clip=%s" % [player.label_en(), player.clip_name()])
	await _until(func() -> bool: return player.carrying != null, 2.0, "捡起来")
	_check("判定帧上把箱子拿到了手（carrying 非空）", player.carrying == box,
		"carrying=%s" % ("yes" if player.carrying != null else "null"))
	_check("箱子进入 HELD 状态", box.state == Carryable.CSt.HELD, "state=%d" % box.state)
	await _frames(10)
	var hand := _hand_world()
	var gap: float = (box.global_position - hand).length()
	print("     手骨 %s ；箱子 %s ；差 %.3f m" % [
		_str(hand), _str(box.global_position), gap])
	_check("箱子跟到了手上（手骨附近半个边长以内）", gap < box.size_m * 1.2,
		"差 %.3f m（边长 %.2f）" % [gap, box.size_m])
	_check("拿在手上时不再参与地面/被打查询（碰撞层被置 0）",
		box._area.collision_layer == 0, "layer=%d" % box._area.collision_layer)
	_check("拿在手上的箱子查不出来（自己挥空不会把手上的砸碎）",
		mgr.query_ground(2.0, player.global_position, player.facing, 2.0, 0.85).has(box) == false,
		"查询结果不含手上的那个")

	_section("2. 拿在手里砸")
	_only(0, 0.75)
	player._start_pick()
	await _until(func() -> bool: return player.carrying != null, 2.0, "再捡一个")
	_check("捡到的就是正前方那个（0 号）", player.carrying == box,
		"carrying=%s" % ("0 号" if player.carrying == box else "别的箱子"))
	await _frames(4)
	# 每一下之前都重新钉位：让"这一拳必定落在假人身上"
	_pin(0.95)
	var hp0: int = dummy.hp
	var bhp0: int = box.hp
	player._start_attack("Light_01")
	await _frames(40)
	var dealt: int = hp0 - dummy.hp
	var want: int = GameDB.damage("Light_01") + GameDB.prop_impact_damage
	print("     轻拳伤害 %d ；手持附加 %d ；实得 %d" % [
		GameDB.damage("Light_01"), GameDB.prop_impact_damage, dealt])
	_check("手持砸击：伤害 = 轻拳 %d + 箱子附加 %d = %d" % [
		GameDB.damage("Light_01"), GameDB.prop_impact_damage, want],
		dealt == want, "实得 %d" % dealt)
	_check("手持砸击：手上的箱子掉了一份耐久（同一个冲量）",
		bhp0 - box.hp == GameDB.prop_impact_damage,
		"耐久 %d → %d（掉 %d）" % [bhp0, box.hp, bhp0 - box.hp])
	# 再砸两下应该碎
	var swings := 1
	while swings < 8 and box.state != Carryable.CSt.BROKEN:
		_pin(0.95)
		player._start_attack("Light_01")
		await _frames(40)
		swings += 1
	_check("手持砸击：耐久 63 / 每下 21 ⟹ 第 %d 下碎" % GameDB.PROP_HITS_TO_BREAK,
		box.state == Carryable.CSt.BROKEN and swings == GameDB.PROP_HITS_TO_BREAK,
		"第 %d 下碎了（state=%d）" % [swings, box.state])
	_check("碎掉之后手上自动空出来", player.carrying == null,
		"carrying=%s" % ("yes" if player.carrying != null else "null"))

	_section("2b. 空挥不掉耐久（没撞上东西就没有冲量）")
	_only(0, 0.75)
	player._start_pick()
	await _until(func() -> bool: return player.carrying != null, 2.0, "捡第三个")
	await _frames(4)
	var b3: Carryable = mgr.props[0]
	var hp_before: int = b3.hp
	# 假人拉到够不着的地方，也别踩在别的箱子上
	dummy.reset_fighter(5.0, -1)
	dummy.opponent = player
	player.global_position = Vector3(-0.2, 0.0, 0.0)
	player._start_attack("Light_01")
	await _frames(40)
	_check("空挥一下：箱子耐久一点没掉", b3.hp == hp_before,
		"耐久 %d → %d" % [hp_before, b3.hp])
	_check("空挥之后箱子还在手上", player.carrying == b3,
		"carrying=%s" % ("yes" if player.carrying != null else "null"))

	_section("3. 扔出去")
	_only(0, 0.75)
	player._start_pick()
	await _until(func() -> bool: return player.carrying != null, 2.0, "再捡一个")
	await _frames(4)
	# 先把别的箱子挪开，别让飞出去的箱子先撞上它们
	for i in mgr.props.size():
		if mgr.props[i] != box:
			mgr.props[i].place_at(Vector3(60.0 + float(i) * 2.0, 0.0, 0.0))
	player._start_pick()                    # 手上有物 → 投掷
	_check("手上有物时再按拾取键切进 Throw 段",
		player.state == Fighter.St.GRAB and player.clip_name() == "Throw",
		"clip=%s" % player.clip_name())
	await _until(func() -> bool: return box.state == Carryable.CSt.FLYING, 2.0, "出手")
	_check("在 Throw 自己的判定帧（%s）上出手，箱子进入 FLYING" % str(GameDB.hit_frame("Throw")),
		box.state == Carryable.CSt.FLYING, "state=%d" % box.state)
	_check("投出瞬间手上就空了（引用一起清）", player.carrying == null,
		"carrying=%s" % ("yes" if player.carrying != null else "null"))
	var launch_y: float = box.global_position.y
	# 出手后才知道落点在哪儿 —— 把假人摆到"箱子必经之路"上（往前 0.9 m）。
	# 出手后一共只飞 ~1.76 m 水平距离（初速 3.577 × 落地 0.493 s），
	# 所以不能把靶子摆到 4 m 外 —— 那会落在箱子后方，永远砸不到。
	var target_x: float = box.global_position.x + 0.9
	dummy.reset_fighter(target_x, -1)
	dummy.opponent = player
	dummy.play_waiting()
	var dhp0: int = dummy.hp
	await _frames(20)
	print("     出手高 %.3f m（契约 %.4f）→ 20 帧后 y=%.3f" % [
		launch_y, GameDB.prop_throw_release_height, box.global_position.y])
	_check("出手点高度 = manifest 的 hand.R 高度 %.4f m" % GameDB.prop_throw_release_height,
		absf(launch_y - GameDB.prop_throw_release_height) < 0.06,
		"实得 %.3f" % launch_y)
	await _until(func() -> bool: return box.state != Carryable.CSt.FLYING, 3.0, "落地或砸中")
	var flew: float = absf(box.global_position.x - player.global_position.x)
	var hit_dealt: int = dhp0 - dummy.hp
	print("     飞出 %.2f m 后停下；假人掉血 %d（靶子摆在 +0.9 m）" % [flew, hit_dealt])
	_check("箱子在重力的作用下落地/命中（没有一直飞）",
		box.state == Carryable.CSt.IDLE or box.state == Carryable.CSt.BROKEN,
		"state=%d" % box.state)
	_check("箱子砸中人：伤害 = 容器伤害 %d" % GameDB.prop_impact_damage,
		hit_dealt == GameDB.prop_impact_damage,
		"实得 %d（飞了 %.2f m）" % [hit_dealt, flew])

	_section("4. 空手打碎地上的箱子（多次才坏）")
	player.global_position = Vector3(-0.2, 0.0, 0.0)
	_only(0, 0.65)
	var b2: Carryable = mgr.props[0]
	var hits := 0
	var hp_track: Array[String] = []
	while hits < 10 and b2.state != Carryable.CSt.BROKEN:
		# 每一拳之前把【角色】放回原处：重拳自带向前的 root motion，不还原的话
		# 角色会一拳一拳走过去，最后站到箱子后面 —— 那不是"打不到"，是"走过了"。
		#
		# **不能改成重放箱子**：`place_at()` 会把耐久刷回满，于是永远是 63→42，
		# 10 下也碎不了（第一版就是这么错的 —— 用重放箱子解决漂移，代价是
		# 把"多次才会坏"这条要验的规则本身抹掉了）。
		player.global_position = Vector3(-0.2, 0.0, 0.0)
		player.facing = 1
		var before: int = b2.hp
		player._start_attack("Heavy_01")
		await _frames(int(GameDB.duration("Heavy_01") * 60.0) + 8)
		hits += 1
		hp_track.append("%d→%d" % [before, b2.hp])
	print("     重拳（%d 伤 / 耐久 %d）：%s" % [GameDB.damage("Heavy_01"), b2.max_hp, str(hp_track)])
	_check("站着出拳打得到地上的箱子（贴地带判定生效）", hits < 10,
		"%d 下打碎了" % hits)
	_check("空手打碎：耐久 63 / 重拳 21 ⟹ 正好 %d 下" % GameDB.PROP_HITS_TO_BREAK,
		b2.state == Carryable.CSt.BROKEN and hits == GameDB.PROP_HITS_TO_BREAK,
		"%d 下（期望 %d）" % [hits, GameDB.PROP_HITS_TO_BREAK])
	var lv := GameDB.grab_hold_max * GameDB.PROP_RESPAWN_K
	print("     复位倒计时 = 擒抱上限 %.1f s × %.1f = %.1f s" % [
		GameDB.grab_hold_max, GameDB.PROP_RESPAWN_K, lv])
	_check("碎掉之后会自己回来（复位间隔 = 擒抱上限 × 系数）", b2.state == Carryable.CSt.BROKEN,
		"正在倒计时")
	await _until(func() -> bool: return b2.state != Carryable.CSt.BROKEN, lv + 1.5, "复位")
	_check("倒计时结束回到出生点、满耐久、可再捡",
		b2.state == Carryable.CSt.IDLE and b2.hp == b2.max_hp and b2.is_pickable(),
		"state=%d hp=%d/%d" % [b2.state, b2.hp, b2.max_hp])

	_section("5. 纵向：跳跃时受击体跟着骨盆抬起来")
	_reset_props()
	_far()
	await _frames(40)                        # 让 Idle_01 淡入完成、基准采样到
	var base_y: float = _hurt_shape().position.y
	_check("贴地时受击体就在地面高度上（基线 %.4f m）" % (GameDB.HURTBOX_HEIGHT * 0.5),
		absf(base_y - GameDB.HURTBOX_HEIGHT * 0.5) < 0.01,
		"实得 %.4f m" % base_y)
	player._set_state(Fighter.St.JUMP)
	player._jump_index = 0
	player._jump_air = false
	player._play(Fighter.JUMP_SEQ[0], 0.0)
	var peak := 0.0
	var peak_clip := ""
	for i in 130:
		await get_tree().physics_frame
		var y: float = _hurt_shape().position.y - GameDB.HURTBOX_HEIGHT * 0.5
		if y > peak:
			peak = y
			peak_clip = player.clip_name()
		if player.state != Fighter.St.JUMP and i > 60:
			break
	print("     受击体最高抬起 %.4f m（在 %s 期间）" % [peak, peak_clip])
	_check("跳跃期间受击体抬起（> 1.0 m，够得着'跳起来躲下段'）", peak > 1.0,
		"实得 %.4f m" % peak)
	_check("抬起量来自实测的骨盆弹道（峰值 +1.1236 m 附近）",
		absf(peak - 1.1236) < 0.12, "实得 %.4f m，实测峰值 1.1236 m" % peak)
	await _frames(80)
	_check("落地后受击体回到地面高度", absf(_hurt_shape().position.y
		- GameDB.HURTBOX_HEIGHT * 0.5) < 0.02,
		"实得 %.4f m" % _hurt_shape().position.y)

	_section("6. 连按两次方向 → 起跑")
	_far()
	player.ai = null
	player.is_player = false
	var ai := ScriptedAI.new()
	player.ai = ai
	player._set_state(Fighter.St.IDLE)
	player._play("Idle_01")
	# 第 1 帧按下右 → 松开一帧 → 再按下右
	var f_on := InputFrame.new(); f_on.right = true
	var f_off := InputFrame.new()
	ai.feed([f_off, f_on, f_off, f_off, f_off, f_on, f_on, f_on, f_on])
	await _frames(9)
	_check("连按两次前进 → 进入 RUN", player.state == Fighter.St.RUN,
		"状态=%s clip=%s（第 %d 帧）" % [player.label_en(), player.clip_name(), ai.i])
	player.ai = null
	player.is_player = true

	_section("7. 跑动中按拳脚 → 跳起飞踢")
	_reset_props()
	_put_box(0, 6.0)                          # 挪开，别干扰
	dummy.set_ai(false)
	dummy.reset_fighter(3.2, -1)
	dummy.opponent = player
	player.reset_fighter(-0.2, 1)
	player.opponent = dummy
	player._set_state(Fighter.St.RUN)
	player._play("Run")
	var clip_seq: Array[String] = []
	player._start_run_kick()
	for i in 200:
		await get_tree().physics_frame
		var c := player.clip_name()
		if clip_seq.is_empty() or clip_seq[clip_seq.size() - 1] != c:
			clip_seq.append(c)
		if player.state == Fighter.St.IDLE:
			break
	print("     招式序列：%s" % str(clip_seq))
	_check("跑动跳踢 = 现成四段串起来（Jump_Start → Jump_Up → Air_Heavy → Jump_Land）",
		clip_seq.has("Jump_Start") and clip_seq.has("Jump_Up")
		and clip_seq.has("Air_Heavy") and clip_seq.has("Jump_Land"),
		str(clip_seq))
	_check("飞踢用的是空中重击（空中轻击的判定盒够不到站地上的人）",
		Fighter.JUMP_KICK_CLIP == "Air_Heavy",
		"JUMP_KICK_CLIP=%s" % Fighter.JUMP_KICK_CLIP)
	_check("飞踢会向前推进（动量 = 奔跑速度本身）",
		player.global_position.x > -0.2 + 0.3,
		"x 从 -0.200 推进到 %+.3f" % player.global_position.x)

	_section("8. 收尾")
	_reset_props()
	_far()
	await _frames(10)
	_check("重开一局后所有箱子回到出生点、都在地上",
		mgr.pickable_count() == GameDB.PROP_COUNT,
		"%d / %d" % [mgr.pickable_count(), GameDB.PROP_COUNT])
	_check("双方手上 / 怀里都没有东西",
		player.carrying == null and dummy.carrying == null,
		"p=%s d=%s" % [str(player.carrying), str(dummy.carrying)])

	print("")
	print("PROBE_%s 共 %d 项，失败 %d 项" % ["OK" if _fails == 0 else "FAIL", _checks, _fails])
	get_tree().quit(0 if _fails == 0 else 1)


# ---------------------------------------------------------------------
# 场景摆放工具
# ---------------------------------------------------------------------
func _quiet() -> void:
	dummy.set_ai(false)
	player.set_ai(false)
	dummy.reset_fighter(3.2, -1)
	dummy.opponent = player
	player.reset_fighter(-0.2, 1)
	player.opponent = dummy
	dummy.play_waiting()
	player.play_waiting()


func _far() -> void:
	_quiet()


## 把所有箱子复位，然后清掉手上/怀里。
func _reset_props() -> void:
	player.carrying = null
	dummy.carrying = null
	mgr.reset_all()


func _clear_all() -> void:
	mgr.reset_all()


## 把第 i 号箱子放到玩家正前方 `d` 米处。
func _put_box(i: int, d: float) -> void:
	var p := mgr.props[i]
	p.place_at(Vector3(player.global_position.x + float(player.facing) * d, 0.0, 0.0))


## 只留第 `keep` 号箱在玩家正前方 `d` 米，其余全部挪到场地之外。
##
## **为什么必须这样**：`nearest_pickable` 返回的是"最近的那个"，而出生点里有
## 一个箱子本来就在身边（0.11 m）—— 不挪开的话测试以为捡到了 A，实际捡到的是 B，
## 后面所有断言全在验一个躺在地上的箱子。第一版就是这么错的。
func _only(keep: int, d: float) -> void:
	_reset_props()
	for i in mgr.props.size():
		if i == keep:
			continue
		mgr.props[i].place_at(Vector3(40.0 + float(i) * 2.0, 0.0, 0.0))
	_put_box(keep, d)


## 把双方钉在确定的位置上（箱子会推挤、root motion 会让角色漂，
## 每轮攻击前重新钉一次才能保证"这一下必定够得着"）。
func _pin(dist: float) -> void:
	player.global_position = Vector3(-0.2, 0.0, 0.0)
	dummy.global_position = Vector3(-0.2 + float(player.facing) * dist, 0.0, 0.0)


## 重铺一遍看摆位是不是确定的。
func _placement_stable() -> bool:
	var before: Array[float] = []
	for p in mgr.props:
		before.append(p.home.x)
	var h: Array[Vector3] = []
	for i in mgr._homes.size():
		h.append(mgr._homes[i])
	mgr.reset_all()
	var ok := true
	for i in mgr.props.size():
		if absf(mgr.props[i].home.x - before[i]) > 0.000001:
			ok = false
	return ok


# ---------------------------------------------------------------------
# 读值工具
# ---------------------------------------------------------------------
func _hurt_shape() -> CollisionShape3D:
	return player.get_node_or_null("Hurtbox/HurtShape") as CollisionShape3D


func _hand_world() -> Vector3:
	var sk := player.skeleton()
	var idx := sk.find_bone(Fighter.HAND_BONE)
	return (sk.global_transform * sk.get_bone_global_pose(idx)).origin


func _str(v: Vector3) -> String:
	return "(%.3f, %.3f, %.3f)" % [v.x, v.y, v.z]


func _section(t: String) -> void:
	print("")
	print("--- %s ---" % t)


func _frames(n: int) -> void:
	for _i in n:
		await get_tree().physics_frame


func _until(cond: Callable, t: float, what: String) -> void:
	var left := t
	while left > 0.0:
		if bool(cond.call()):
			return
		await get_tree().physics_frame
		left -= 1.0 / 60.0
	print("     ⚠ 等待超时：%s（%.1f s）" % [what, t])


func _check(name: String, ok: bool, detail: String) -> void:
	_checks += 1
	if not ok:
		_fails += 1
	print("  %s %s\n        %s" % ["[PASS]" if ok else "[FAIL]", name, detail])
