extends Node
## =====================================================================
## 实机过程录制 —— 脚本化地打一局，交给引擎的影片录制器逐帧写盘
## =====================================================================
##
## 做什么：
##   把 `scenes/main.tscn` 整局实例化（真 HUD、真舞台、真状态机、真特效），
##   用一段**写成数据的剧本**驱动 1P（走的是真正的输入通路，不是直接改状态），
##   2P 仍由 `DummyAI` 自主应战 —— 于是录下来的是**对局**，不是摆姿势。
##
## 为什么用 `--write-movie` 而不是自己 `await frame_post_draw` 抓 PNG：
##   自己抓的话，抓图这一帧的耗时会被算进 `delta`。存一张 1280×720 的 PNG
##   要 ~20 ms，一旦超过 1/30 s，**每个输出帧代表的游戏时间就不再相等** ——
##   成片会莫名其妙地时快时慢。影片录制器把 `delta` 钉死成 `1/fps`，
##   "第 n 帧 ↔ 游戏时间 n/fps" 是恒等式，这才是能拿去和别的片子对齐的东西。
##   附带好处：AVI(MJPEG) 编码 6 ms/帧，比存 PNG 快近 30 倍。
##
## 用法：
##   godot --path . --resolution 1280x720 res://tools/record.tscn \
##         --write-movie <绝对路径>/gameplay_raw.avi --quit-after 4000
##
## 产物：
##   <--write-movie 指定的 avi>              （中间产物，规格 1280×720 / 60 fps / MJPEG）
##   <工作区>/outputs/gameplay_v001/record_trace.txt   剧本实跑记录（逐拍帧数 + 收尾状态）
##
## 纪律：**剧本里出现的每一个"什么时候"都要有依据。**
##   帧数来自 manifest 的 `hit_frame` / `cancel_frame` / `duration_s`（经 GameDB 查询），
##   距离来自 `hit_points[].reach_m` 与判定盒尺寸（经 `_hit_ceiling` 推），
##   不是"试出来的好看数"；只有纯演出节拍（后撤几下、抱多久）允许人定，
##   且都在注释里写明理由。剧本跑完之后 `record_trace.txt` 把每一拍实际耗的帧数
##   记下来 —— 成片里的节奏能对着这张表逐条核。

## 产物目录（相对工作区根）
const OUT_SUBDIR := "outputs/gameplay_v001"
## 看门狗：剧本要是卡住，绝不留一个"窗口开着什么都不做"的僵尸进程。
## 按物理帧计数（影片模式下 wall-clock 和游戏时间不是 1:1，用秒数会失准）。
const WATCHDOG_FRAMES := 4200

## 必杀站位 = 最近命中点上限 × 这个系数。
##
## 为什么必须收得比别的招更狠：必杀四段**都没有位移**（`root_motion_m = [0,0]`），
## 而每段打中都会把对手推开 `伤害 × KNOCKBACK_PER_DAMAGE` = 17 × 0.012 = 0.204 m。
## 于是四段的可达上限（0.9945 / 1.0049 / 1.038 / 1.0737）看起来差不多，
## **实际是一段比一段更难够到** —— 站得离"最远那段"越近，越早的段越容易先落空。
##
## 反推：设起手中心距 d₀，第 n 段打到前对手已被推走约 (n−1)×0.204 m，
## 要求 **(n−1)×0.204 + d₀ ≤ 该段上限**，四段合起来最紧的一条是
##   d₀ ≤ 0.9945 − 0.204 ≈ 0.79（第 2 段）
##   d₀ ≤ 1.038 − 0.408 ≈ 0.63（第 3 段）  ← 最紧
## 取 0.66 倍 → 0.656 m：既在推箱下限 0.60 m 之外（走得进去），
## 又留出余量让前三段稳稳打中。第 4 段打不打得到看运气，不苛求。
const ULT_STAND_K := 0.66

var game: Game
var player: Fighter
var dummy: Fighter

var _script: ScriptedPlayer
## 2P 的 AI 句柄（`HaltableDummy`）—— 终盘要能让它停手，见该类注释。
var _halt_ai: HaltableDummy = null
var _trace_path := ""
var _watch := 0
var _quit_sent := false

# --- 状态变迁日志 ---
# 剧本记录的是"每一拍走了多少帧"，但拍**内部**发生了什么看不到。
# 抓取/投技这种"判定帧才发生"的流程恰恰全在拍内部，出问题时光看拍长查不出来
# （第一版就是：抓取拍了 220 帧、`grabs_done` 却是 1 —— 抓到了却没投出去，
# 只看拍长完全看不出断在哪一步）。所以把 1P/2P 的状态与擒抱关系变迁逐条记下来。
var _last_state := -1
var _last_holding := false
var _last_grabbed := false
var _last_log := 0
var _events: Array[String] = []


# =====================================================================
# 剧本执行器
# ---------------------------------------------------------------------
# 一拍（step）长这样：
#   {
#     "note":  "这一拍在干嘛（会写进 trace）",
#     "hold":  {"right": true},       # 整拍一直按住的键
#     "edge":  {"light": true},       # 只在**第一帧**按下的键（边沿触发）
#     "gate":  Callable,              # 可选：闸门没开就一帧都不发、也不计时
#     "gate_max": 150,                # 闸门最多等几帧，超了就跳过这一拍
#     "min":   1,                     # 最少待几帧（条件早成立也要等够）
#     "max":   70,                    # 最多待几帧（硬上限，卡住也往前走）
#     "until": Callable,              # 可选：成立且已过 min 就进下一拍
#     "on_enter": Callable,           # 可选：成为当前拍时调一次
#   }
# 退出条件：`held >= max`，或者（`held >= min` 且 `until` 成立）。
# 三样都有才够用：只有 `max` 会在"判定帧比预期晚到"时把节奏切碎；
# 只有 `until` 会在条件永不成立时把片子拖死。
# =====================================================================
class ScriptedPlayer extends DummyAI:
	## 没写 `hold` 的拍默认**举防**。
	##
	## 为什么默认是防而不是"什么都不按"：这是演示录像，脚本化的 1P 没有"看到对方出拳
	## 就抬防"的反应能力。不给它默认防，它就会**脸接每一招** —— 而这一版里假人的
	## 重拳/上勾/下段全部 ≥ 击倒阈值 18，于是每挨一下就倒，35 秒里倒 4 次，
	## 剧本里的必杀和技能十有八九演到一半被打断（第一版实测就是这样）。
	## 默认举防后：挨打只吃 15% 伤害、不进倒地，招式能演完，看起来像个会打的玩家。
	##
	## 举防不会吃掉出招：`_try_common` 的优先级是 技能 > 抓技 > 拳脚 > 跳 > 蹲 > 防，
	## 所以"按着防 + 同帧按轻拳"仍然是出拳。但要先**松开一帧**才能从防御状态回到待机
	## —— 见下面"出招前先松防"那一支。
	const DEFAULT_HOLD := {"guard": true}

	var steps: Array = []
	var idx := 0
	## 当前这一拍已经待了几帧
	var held := 0
	## 闸门已经等了多久（开一次就清零）
	var gate_wait := 0
	var done := false
	## 本拍之内**新进入过 ATTACK** 没有（换拍清零）。给 `confirm` 用。
	##
	## 为什么不能直接用"当前是不是在出招"当判据：必杀这种长拍，
	## 招式演完会自然回到待机 —— 于是 `confirm` 会误判成"上次没按上"，
	## 在拍的尾巴上**再放一次必杀**（实测踩过：第一发必杀打到剩 1 血、
	## 第二发把对手直接打死，收尾的突进反而没戏份了）。
	## 记账要的是"这一拍放出去过没有"，不是"此刻正在不在放"。
	var fired := false
	## 上一帧的状态（用来识别"新进入 ATTACK"这个**边沿**）
	var _prev_state := -1
	## 逐拍实跑记录（出一行 = 这一拍走了多少帧 + 交棒瞬间的角色状态）
	var trace: Array = []

	func poll(me: Node3D, opponent: Node3D, _delta: float) -> InputFrame:
		var f := InputFrame.new()
		if done or idx >= steps.size():
			done = true
			return f

		# --- 被擒时不管剧本：只顾挣脱 ---
		# 这不是"容错"，是**剧本里本来就该有的一幕**：真人被抓了也会狂拍键。
		# 排在剧本前面还有个硬性理由 —— 被擒期间发出的方向键状态机不接受，
		# 但会让脚本的帧计数白走（这个坑 DummyAI 的注释里记着）。
		var self_f := me as Fighter
		if self_f != null and self_f.state == Fighter.St.GRABBED:
			# 用物理帧号取模而不是随机：同一份录像重放得到同一串输入
			if (Engine.get_physics_frames() % 4) < 2:
				f.light = true
			else:
				f.grab = true
			return f

		# --- 1. 先判"这一拍走完了没有" ---
		# 用的是**上一帧结束时**的真实状态（`_match_state` 已经处理过上一帧的输入）。
		# 顺序很关键：如果先出帧再判定，那么"按下键"的同一帧里条件就已经读到了
		# 上一拍留下的窗口 —— 状态机要到下一帧才处理这次按键 ——
		# 表现是连段的第二下**一帧就过**、按键被 `_pending_chain` 吃掉，
		# 三连只出两下（第一版实测就是这样，13/1/23 帧，第三下被吞了）。
		if held > 0:
			var cur: Dictionary = steps[idx]
			var mx := int(cur.get("max", 1))
			var mn := int(cur.get("min", 1))
			var adv := held >= mx
			if not adv and held >= mn and cur.has("until"):
				adv = bool((cur["until"] as Callable).call())
			if adv:
				trace.append("%-30s %4d 帧  [%s]" % [
					String(cur.get("note", "?")), held, _snapshot(self_f)])
				idx += 1
				held = 0
				gate_wait = 0
				fired = false
				_prev_state = -1
				if idx >= steps.size():
					done = true
					return f

		var st: Dictionary = steps[idx]

		# --- 2. 闸门：没轮到"角色能动手"就先什么都不发 ---
		# 按键是**边沿触发**的，掉一次就永远没了。没有闸门的话，角色恰好卡在
		# 受击/倒地帧上按下必杀，这一记就**静默消失** —— 而剧本记录上却显示"跑过了"。
		#
		# `held == 0` 这个前置条件是**必须的**，而且踩过一次：
		#   闸门本来问的是"还没开始出招之前，角色能动手吗"。一旦这一拍已经出了招，
		#   角色就必然处在 ATTACK/GRAB 里 —— 此时 `_p_free` 恒为 false。
		#   若还继续拿它卡，`held` 就永远停在 1（被 `return` 挡在自增之前），
		#   `min`/`max`/`until` 全部永远不判 —— 表现是**必杀整段被跳过**、
		#   连段第一下空转 70 帧。闸门只管"起手"，不管"进行中"。
		if held == 0 and st.has("gate") and not bool((st["gate"] as Callable).call()):
			gate_wait += 1
			if gate_wait < int(st.get("gate_max", 150)):
				return f
			trace.append("%-30s   跳过（闸门 %d 帧没开）" % [
				String(st.get("note", "?")), gate_wait])
			idx += 1
			held = 0
			gate_wait = 0
			return f
		gate_wait = 0

		# --- 2b. 记"这一拍出过手没有" ---
		# `held > 0` 是必须的：拍与拍交棒的那一帧，1P 往往还停在上一拍的招式里
		# （连段的第 2 拍接手时，屏幕上还在放第 1 拍的 Light_01）。
		# 不排除这一帧的话，新的一拍会被记成"已经出过手"，于是**永远不按键** ——
		# 三连变一下、技能和必杀整段消失。
		if held > 0 and self_f != null:
			if self_f.state == Fighter.St.ATTACK and _prev_state != Fighter.St.ATTACK:
				fired = true
			elif self_f.state in [Fighter.St.HIT, Fighter.St.DOWN]:
				# 被打进受击/倒地 = 这一记没打完，作废，允许重按
				fired = false
			_prev_state = self_f.state

		# --- 3. 出帧 ---
		var edges: Dictionary = st.get("edge", {})

		# 这一次要不要按键：刚进这一拍（held==0）要按；或者 `confirm` 说"上一次按的
		# 没生效"（被打了 / 没接上）→ 重按。**补刀的可靠性全靠它** ——
		# 边沿触发的键掉一次就没了，没有重按的话"必杀被对方一拳打断"就等于
		# 整段白给，片子收不住尾。
		var want_press := held == 0
		if not want_press and edges.size() > 0 and st.has("confirm"):
			want_press = not bool((st["confirm"] as Callable).call())

		# 出招前先松防：`St.GUARD` 分支只处理"松防回待机"，不调 `_try_common`，
		# 所以防御状态下按拳脚/技能是**完全没反应**的。这一帧什么都不按（等于松手），
		# 下一帧状态回到待机，再按才生效。
		if want_press and edges.size() > 0 and self_f != null and self_f.state == Fighter.St.GUARD:
			return f

		if held == 0:
			_enter(st)
		if want_press:
			for k in edges.keys():
				f.set(k, true)
		# 没写 hold 的拍用默认（举防）
		var hold: Dictionary = st.get("hold", DEFAULT_HOLD)
		for k in hold.keys():
			f.set(k, true)
		held += 1
		return f

	func _enter(st: Dictionary) -> void:
		if st.has("on_enter"):
			(st["on_enter"] as Callable).call()

	func _snapshot(f: Fighter) -> String:
		if f == null:
			return "-"
		return "%s / %s" % [f.label(), f.clip_name()]

	func total_frames() -> int:
		return int(steps.size())


# =====================================================================
# 2P 的 AI —— 可以"停手"的假人
# ---------------------------------------------------------------------
# 为什么非要有这么个东西：
#   剧本化 1P 没有"看到对方起手就改主意"的反应能力。而假人的行为是
#   "进了交战距离就按冷却随机出招"（ATTACK_COOLDOWN 0.55~1.30 s）。
#   必杀起手有 **62 帧（1.03 s）**，正好落在假人的出招冷却里 ——
#   于是每一次必杀都在起手阶段被一拳打断，340 帧的必杀实跑下来
#   **一点伤害都没打出来**（实测：血量从设定值原封不动）。
#
# 这算不算"作弊"：不算。这是**演示录像**，双方输入都是编排的 ——
# 1P 走的是 ScriptedPlayer，2P 走这个。它只决定"对手这一段的输入是什么"，
# 不碰任何规则、数值、状态机。相当于格斗游戏里的"木桩"模式。
#
# 而且它**只停手、不卸防**：被打照样掉血、被击退、被击倒。
# 唯一保留的自主行为是"被抓住时挣扎"，因为那正是投技要展示的机制。
# =====================================================================
class HaltableDummy extends DummyAI:
	var halted := false

	func poll(me: Node3D, opponent: Node3D, delta: float) -> InputFrame:
		if halted:
			# 被擒时照旧挣扎 —— "挣脱"是投技的展示重点，不因为停手被吃掉
			if me is Fighter and (me as Fighter).state == Fighter.St.GRABBED:
				return super.poll(me, opponent, delta)
			return InputFrame.new()
		return super.poll(me, opponent, delta)


# =====================================================================
# 启动
# =====================================================================
func _ready() -> void:
	game = get_parent().get_node_or_null("Main") as Game
	if game == null:
		push_error("[record] 找不到 Main —— record.tscn 必须把 main.tscn 实例成兄弟节点")
		get_tree().quit(1)
		return
	player = game.player
	dummy = game.dummy

	var out_dir := _resolve_out_dir()
	DirAccess.make_dir_recursive_absolute(out_dir)
	_trace_path = out_dir.path_join("record_trace.txt")

	var vp := get_viewport().get_visible_rect().size
	print("[record] 视口 %dx%d  窗口 %s  物理 %d Hz" % [
		int(vp.x), int(vp.y), str(get_window().size),
		Engine.physics_ticks_per_second])
	print("[record] 交战 %.3f m  抓取手可达 %.3f m  被擒间距 %.3f m  投出滑行 %.3f m" % [
		GameDB.engage_distance, GameDB.grab_reach,
		GameDB.grab_hold_distance, GameDB.throw_flight])
	print("[record] 走 %.3f m/s  跑 %.3f m/s  擒抱上限 %.2f s" % [
		GameDB.walk_speed, GameDB.run_speed, GameDB.grab_hold_max])
	print("[record] 必杀单段伤害 %d / 突进 26（收尾血量按它们推，不是拍脑袋）" % [
		GameDB.damage("Ultimate_Attack")])

	# 1P 交给剧本，2P 保持自主 AI。
	# `player.is_player = false` 是**必须的**：不放的话 `_poll_input` 会走
	# `PlayerInput` 去读键盘，`ai` 根本不会被调用（headless / 影片模式下没有键盘，
	# 表现就是"1P 站着不动"）。
	_script = ScriptedPlayer.new()
	_script.steps = _build_sheet()
	player.ai = _script
	player.is_player = false
	dummy.set_ai(true)
	# set_ai(true) 内部会 new 一个普通 DummyAI，这里换成可停手的版本
	_halt_ai = HaltableDummy.new()
	dummy.ai = _halt_ai

	# 把终盘用到的几何一次算清并打出来 —— 站位不是"试出来的"，是这么来的：
	print("[record] 命中上限算法 reach−%.2f+%.2f+%.2f = reach+%.2f" % [
		Fighter.HITBOX_BIAS, Fighter.HITBOX_DEPTH * 0.5, GameDB.HURTBOX_RADIUS,
		-Fighter.HITBOX_BIAS + Fighter.HITBOX_DEPTH * 0.5 + GameDB.HURTBOX_RADIUS])
	print("[record] 必杀命中点 最远上限 %.3f m / 最近上限 %.3f m（四段可达 %.4f~%.4f）" % [
		_hit_ceiling("Ultimate_Attack"), _hit_ceiling_min("Ultimate_Attack"),
		_ult_reach_min(), _ult_reach_max()])
	print("[record] 必杀站位目标 ≤ %.3f m（最近上限 × %.2f，推箱下限 %.2f m）" % [
		_hit_ceiling_min("Ultimate_Attack") * ULT_STAND_K, ULT_STAND_K,
		GameDB.PUSH_SEPARATION])
	print("[record] 击退 %.3f m/段（伤害 %d × %.3f）—— 四段会被推走 %.3f m" % [
		GameDB.damage("Ultimate_Attack") * GameDB.KNOCKBACK_PER_DAMAGE,
		GameDB.damage("Ultimate_Attack"), GameDB.KNOCKBACK_PER_DAMAGE,
		GameDB.damage("Ultimate_Attack") * GameDB.KNOCKBACK_PER_DAMAGE * 4.0])

	await _run()


func _ult_reach_min() -> float:
	var pts: Variant = GameDB.clip("Ultimate_Attack").get("hit_points")
	var m := INF
	for p in pts:
		m = minf(m, absf(float((p as Dictionary).get("reach_m", 0.0))))
	return m


func _ult_reach_max() -> float:
	return GameDB.max_reach("Ultimate_Attack")


func _run() -> void:
	while not _script.done and _watch < WATCHDOG_FRAMES:
		await get_tree().physics_frame
	# 剧本走完后再多录一点：让最后一拍的落地/横幅落干净，不要在动作中途切断
	for _i in 24:
		await get_tree().physics_frame
	_dump_trace()
	if _watch >= WATCHDOG_FRAMES:
		push_warning("[record] 看门狗触发：%d 帧内剧本没跑完" % WATCHDOG_FRAMES)
	_quit(0)


func _physics_process(_delta: float) -> void:
	_watch += 1
	_log_events()
	if _watch >= WATCHDOG_FRAMES and not _quit_sent:
		push_warning("[record] 看门狗：到 %d 帧强制收尾" % WATCHDOG_FRAMES)
		_dump_trace()
		_quit(2)


func _quit(code: int) -> void:
	if _quit_sent:
		return
	_quit_sent = true
	print("[record] 收尾 quit(%d)  共 %d 帧 = %.2f s @60Hz" % [
		code, _watch, float(_watch) / 60.0])
	get_tree().quit(code)


## 记录 1P/2P 的状态变迁，以及"谁在抱谁"的开关。
func _log_events() -> void:
	if player == null or dummy == null:
		return
	var st := player.state
	var h := player.is_holding()
	var g := player.is_held()
	if st == _last_state and h == _last_holding and g == _last_grabbed:
		return
	var hold_txt := ""
	if h:
		hold_txt = " 持=%s(剩 %.2fs)" % [player._grab_move, player._grab_hold]
	_events.append("%5d  %-4s → %-4s  持:%s 被擒:%s%s  2P:%s  距 %.2f  hp %d/%d" % [
		_watch, Fighter.ST_LABEL.get(_last_state, "-"), Fighter.ST_LABEL[st],
		"有" if h else "无", "是" if g else "否", hold_txt,
		dummy.label(), _dist(), dummy.hp, dummy.max_hp])
	_last_state = st
	_last_holding = h
	_last_grabbed = g
	_last_log = _watch


# =====================================================================
# 剧本
# =====================================================================
func _build_sheet() -> Array:
	var s: Array = []

	# --- 00 开场演出 -------------------------------------------------
	# 开局 Game._start_round() 自己会播 E05「对战开始」（1.6 s）并挂"准备/开打！"横幅。
	# 这一拍什么都不按，就把那段演出完整让出来。
	s.append({"min": 150, "max": 150, "note": "开场演出 E05 对战开始 + 开打横幅"})

	# --- 01 后撤半步 -------------------------------------------------
	# 42 帧 = 0.70 s × 走速 1.027 m/s ≈ 0.72 m，正好"半步"。
	# 先把 Walk_B 交代一下，顺带把开局的贴身距离拉开，后面才有"前压"可演。
	s.append({"hold": {"left": true}, "min": 42, "max": 42,
		"note": "后撤半步 Walk_B"})

	# --- 02 前压接敌 -------------------------------------------------
	# `min: 24` 是关键：长按方向超过 RUN_HOLD_TIME(0.32 s = 19 帧) 才转奔跑，
	# 给不够 24 帧就永远拍不到 Run。
	s.append({"hold": {"right": true}, "min": 24, "until": _approach("Light_01"), "max": 200,
		"on_enter": _say("前压接敌", "APPROACH", 0.8),
		"note": "前压接敌 Walk_F → Run"})

	# --- 03~06 三连轻拳 → 重拳 ---------------------------------------
	# 走**真连段**：每一拍在取消窗口内补一下，`_resolve_chain` 自己把
	# Light_01→02→03→Heavy_01 接出来。所以按键的时机不能写死帧数 ——
	# 打击停顿会把动画帧和脚本帧错开（每次命中停 2~4 帧），固定帧数必错位。
	# `_chain_ready()` 直接读"当前 clip 的 cancel_frame"和"有没有已排的续段"，
	# 三个判据全部来自 manifest 实测值。
	s.append({"edge": {"light": true}, "min": 2, "until": _chain_ready, "max": 70,
		"gate": _p_free,
		"on_enter": _say("三连轻拳 → 重拳", "COMBO", 1.0),
		"note": "连段 1/4 轻拳（B01 hit=6 cancel=10）"})
	s.append({"edge": {"light": true}, "min": 2, "until": _chain_ready, "max": 70,
		"note": "连段 2/4 轻拳（B02 hit=8 cancel=13）"})
	s.append({"edge": {"light": true}, "min": 2, "until": _chain_ready, "max": 70,
		"note": "连段 3/4 轻拳（B03 hit=10 cancel=17）"})
	s.append({"edge": {"heavy": true}, "min": 50, "max": 50,
		"note": "连段 4/4 重拳收尾（B04 dur=0.8s，21 伤 ≥18 ⟹ 击倒）"})

	# --- 07 收招观察 -------------------------------------------------
	s.append({"min": 45, "max": 45, "note": "收招观察"})

	# --- 08 举防 -----------------------------------------------------
	s.append({"hold": {"guard": true}, "min": 60, "max": 60,
		"on_enter": _say("举防", "GUARD", 0.8),
		"note": "举防 Guard_Loop 1.0 s"})

	# --- 09~13 投技：抓 → 擒 → 投 → 击飞 ------------------------------
	s.append({"hold": {"right": true}, "min": 1, "until": _grab_range, "max": 220,
		"note": "贴到抓取距离（≤ 抓取手可达 ×0.90）"})
	# 抓取判定在 Grab_Start 的 hit_frame 28（0.47 s），抓到才继续。
	s.append({"edge": {"grab": true}, "min": 2, "until": _holding, "max": 220,
		"gate": _p_free,
		"on_enter": _say("抓取", "GRAB", 0.8),
		"note": "抓取 Grab_Start 判定帧 28"})
	# 抱 0.45 s。
	#
	# 这个数不是"觉得好看"，是**从挣脱概率倒推的**：
	# 假人每帧 5.5% 概率拍挣脱键、凑够 GRAB_MASH_BREAK=6 下就跑（均值 ~109 帧，
	# 标准差 ~43 帧）。而"投掷键按下去"到"伤害真正结算"还要走 Throw 自己的
	# hit_frame 28 帧。所以从扣住到结算的总时长 = 抱的帧数 + 28。
	#   抱 0.85 s（51 帧）→ 总 79 帧 → P(在结算前被挣脱) ≈ 16%
	#   抱 0.45 s（27 帧）→ 总 55 帧 → P(在结算前被挣脱) ≈  7%
	# 第一版用了 0.85 s，实测正好卡在边界上被挣脱（第 82 帧跑掉，结算在第 82 帧）——
	# 抓到了却没投出去。缩短到 0.45 s 把这个窗口挪出危险区。
	s.append({"min": 1, "until": _hold_enough, "max": 90,
		"note": "擒抱 Grab_Hold 循环 0.45 s"})
	# 再按一次抓取键 = 投出去；伤害在 Throw 的 hit_frame 28 结算。
	s.append({"edge": {"grab": true}, "confirm": _in_carry, "min": 1, "until": _thrown, "max": 160,
		"on_enter": _say("投掷", "THROW", 1.0),
		"note": "投掷 Throw 结算帧 28"})
	s.append({"min": 100, "max": 100, "note": "被投者击飞 + 落地冲击波"})

	# --- 14~19 技能：肩撞 / 地面砸击 / 蓄力 ----------------------------
	# **从这里开始 2P 停手**（见 HaltableDummy）。
	# 全片结构是"前半真打、后半收束"：00~13 拍里 2P 全程自主应战
	# （连段、被抓、挣脱、反打都真的会发生）；到这一拍起把它定成木桩，
	# 技能的站位、必杀的起手才不会被"随机挨一拳"打断。
	# 不这么切的话，实测就是：技能和必杀**全部落空**（站位被对手的走位带跑），
	# 35 秒的片子收不出尾。
	s.append({"hold": {"right": true}, "min": 1, "until": _approach("Skill_01"), "max": 180,
		"on_enter": _halt_dummy,
		"note": "重新接敌（站位按 Skill_01 自己的命中点定；2P 自此停手）"})
	# Skill_01 dur=1.6 s、签名帧 36；给 110 帧（1.83 s）连收招演完。
	s.append({"edge": {"skill1": true}, "min": 110, "max": 110,
		"gate": _p_free,
		"on_enter": _say("技能 · 肩撞", "SKILL / SHOULDER", 1.0),
		"note": "技能 Skill_01（C09 dur=1.6s 签名帧 36）"})
	s.append({"hold": {"right": true}, "min": 1, "until": _approach("Ground_Smash"), "max": 180,
		"note": "重新接敌（站位按 Ground_Smash 自己的命中点定）"})
	# Ground_Smash dur=1.0 s、签名帧 36。
	s.append({"edge": {"smash": true}, "min": 100, "max": 100,
		"gate": _p_free,
		"on_enter": _say("技能 · 地面砸击", "SKILL / GROUND SMASH", 1.0),
		"note": "技能 Ground_Smash（C07 dur=1.0s 签名帧 36）"})
	s.append({"min": 1, "until": _p_free, "max": 150, "note": "等角色能动"})
	# Charge dur=1.833 s、签名帧 72（光环整段都在）。
	s.append({"edge": {"charge": true}, "min": 130, "max": 130,
		"gate": _p_free,
		"on_enter": _say("蓄力", "CHARGE", 1.0),
		"note": "蓄力 Charge（C08 dur=1.833s 签名帧 72）"})

	# --- 20~24 必杀收尾 -----------------------------------------------
	# 必杀这一拍要待多少帧：三段时长之和 + 中段每段命中点各自的打击停顿 + 一点余量。
	# 全部来自 manifest —— 三段是三个独立 clip（C12/C13/C14），
	# 帧数不能靠一个"看起来差不多"的常数拍。
	var ult_frames: int = int(round(
		(GameDB.duration("Ultimate_Start") + GameDB.duration("Ultimate_Attack")
			+ GameDB.duration("Ultimate_End")) * 60.0))
	var ult_hs_v: Variant = GameDB.hitstop_frames("Ultimate_Attack")
	var ult_hs: int = int(ult_hs_v) if ult_hs_v != null else 0
	var ult_pts: Variant = GameDB.clip("Ultimate_Attack").get("hit_points")
	var ult_n: int = (ult_pts as Array).size() if ult_pts is Array else 0
	ult_frames += ult_hs * ult_n + 24
	# 先等对手爬起来。技能三连的伤害是 24 / 22 / 19，**全都 ≥ 倒地阈值 18**
	# （阈值来源：GameDB.KNOCKDOWN_DAMAGE，取值理由见该常量注释），
	# 所以三拍下来对手必然躺在第 1 拍留下的那个倒地动画里。
	# 必杀的命中点全在 1.10~1.31 m 高，对着一个还在地上的人起手是白给 ——
	# 等它回到"站着"再压上去，读起来也顺（对手爬起来 → 1P 补上最后一击）。
	s.append({"min": 1, "until": _dummy_upright, "max": 200,
		"note": "等对手起身（倒地 → 待机）"})
	s.append({"hold": {"right": true}, "min": 1,
		"until": _approach_min("Ultimate_Attack", ULT_STAND_K), "max": 220,
		"note": "必杀前压（收到最近命中点上限 ×%.2f，理由见 ULT_STAND_K）" % ULT_STAND_K})
	s.append({"edge": {"ultimate": true}, "confirm": _fired, "min": 2, "until": _dummy_dead,
		"max": ult_frames,
		"gate": _p_free,
		"on_enter": _ultimate_enter,
		"note": "必杀三段（C12+C13+C14，中段 4 段命中点，共 %d 帧）" % ult_frames})
	# 补刀。
	#
	# **为什么不是突进**（第一版用了 `Dash_Attack`，连放四次对手血条一动不动）：
	# `Dash_Attack` 的判定盒在**身前 1.66 m**（上限 2.11 m），而它自己还要前冲 1.0 m。
	# 判定在第 20 帧，那时已经冲了 `1.0 × 20/42 = 0.48 m`，于是命中的充要条件是
	#   d − 0.48 ∈ [1.41 − 0.30, 1.81 + 0.30]  ⟹  **d ∈ [1.59, 2.59] m**
	# —— 它是**远距离追击技**。而必杀演完两人就在 0.9 m 左右（必杀自身无位移，
	# 只有命中把对手推开），站在这个距离放突进是"冲过头从人身上穿过去"。
	# 判据本身没错，错的是"以为可达越远就越容易打中" —— 近身反而打不中。
	#
	# 重拳的可达 0.97 m（上限 1.42 m）正好覆盖必杀收招时的距离，且前冲只有 0.076 m。
	# 于是补刀 = **前压进重拳距离 → 一记重拳**。
	#
	# 为什么留 3 组：起手血是 `必杀单段 × 4 + 1`（见 `_ultimate_enter`），
	# 必杀全中时收招只剩 1 血，一击即倒；但"必杀打中几段"本身不确定，
	# 最坏一段没中就要 ⌈69/21⌉ = 4 拳。3 组是实测够用的冗余，
	# 而且对手已死时整组 3 帧就过（`until: _dummy_dead`），不会拖时间。
	# `confirm` 让"没接上"能自动重来 —— 没有它，一次落空就等于这段白给。
	for i in 3:
		s.append({"hold": {"right": true}, "min": 1,
			"until": _approach("Heavy_01", 0.78), "max": 90,
			"note": "补刀 %d/3 前压（站进重拳上限 %.2f ×0.78）" % [
				(i + 1), _hit_ceiling("Heavy_01")]})
		s.append({"edge": {"heavy": true}, "confirm": _fired, "min": 2,
			"until": _dummy_dead, "max": 70, "gate": _finish_gate,
			"note": "补刀 %d/3 重拳（21 伤 ≥18 ⟹ 倒地即 KO）" % (i + 1)})
	s.append({"min": 260, "max": 260, "note": "KO 演出 + 胜负横幅（K.O.→OVER 3 s）"})

	return s


# =====================================================================
# 剧本条件（全部读真实状态 / manifest，不读脚本自己的计数）
# =====================================================================
func _dist() -> float:
	return absf(player.global_position.x - dummy.global_position.x)


## 某个招式"打得中"的距离上限（米）—— 取该段**最远**的命中点。
##
## = 命中点实测可达 − 判定盒偏移 + 判定盒半深 + 受击体半径。
##
## 逐项对代码（`Fighter._query_hit` → `Fighter._query_box`）：
##   · `_query_hit(reach, h)` 调的是 `_query_box(reach − HITBOX_BIAS, HITBOX_DEPTH, h)`；
##   · `_query_box` 把盒子放在 `自身 + facing × ahead`、沿 X 张 `depth`，
##     于是盒子的世界 X 区间 = [reach − 0.05 − 0.20, reach − 0.05 + 0.20]
##     = [reach − 0.25, reach + 0.15]；
##   · 对手的受击体是半径 `HURTBOX_RADIUS`(0.30) 的胶囊，
##     所以**中心距 ≤ reach − 0.05 + 0.20 + 0.30 = reach + 0.45** 就算命中。
##
## 第一版这里漏抄了 `− HITBOX_BIAS`，把上限算高 5 cm。
## 教训：这种判据本来就是"照着查询函数抄一遍"，抄漏一项，判据就是错的 ——
## 而它错得很安静（只是站位差一点点、第一下偶尔落空）。
func _hit_ceiling(clip: String) -> float:
	return _box_ceiling(GameDB.max_reach(clip))


## 同一套算法，但取该段**最短**的那个命中点。
##
## 多段技必须按最短那段站。必杀的四段可达是 0.5445 / 0.5549 / 0.588 / 0.6237 ——
## 站到"最远那段"够得着的距离（≈1.07 m）上，**第一段(≈0.99 m)反而够不着**，
## 于是整段连不起来、只掉后面的段。按最短那段站位才能四段全中。
func _hit_ceiling_min(clip: String) -> float:
	var pts: Variant = GameDB.clip(clip).get("hit_points")
	if not (pts is Array) or (pts as Array).is_empty():
		return _box_ceiling(0.0)
	var m := INF
	for p in pts:
		m = minf(m, absf(float((p as Dictionary).get("reach_m", 0.0))))
	return _box_ceiling(m)


## `reach_m` → "打得中"的距离上限。全工程只此一处做这个换算，两个入口都走它。
func _box_ceiling(reach_m: float) -> float:
	if reach_m <= 0.0:
		# 没有命中点的段（大招起手、蓄力）拿交战距离兜底
		return GameDB.engage_distance + 0.5
	return reach_m - Fighter.HITBOX_BIAS + Fighter.HITBOX_DEPTH * 0.5 \
		+ GameDB.HURTBOX_RADIUS


## "推到某个招式的有效距离"的判据：进到上限的 `k` 倍就算站好了。
##
## 取 k<1 而不是 1：命中上限是"擦到边"的极限，站那儿打常常第一下就落空；
## 往里收一点才是"稳稳打中"的站位。**每个招式各算各的** —— 必杀（≈1.07 m 上限）
## 和重拳（≈1.42 m 上限）需要的站位差了三成，用一个统一的"交战距离"会顾此失彼。
##
## `k` 默认 0.80；必杀那种"多段 + 会被击退"的招式要再往里收，见调用处。
func _approach(clip: String, k := 0.80) -> Callable:
	var want: float = _hit_ceiling(clip) * k
	return func() -> bool: return _dist() <= want


## 同 `_approach`，但按**最短**命中点算（多段技专用）。
func _approach_min(clip: String, k := 0.80) -> Callable:
	var want: float = _hit_ceiling_min(clip) * k
	return func() -> bool: return _dist() <= want


func _grab_range() -> bool:
	return _dist() <= GameDB.grab_reach * 0.90


func _holding() -> bool:
	return player.is_holding()


func _thrown() -> bool:
	return player.throws_done >= 1


## 抱够了没有：抱到 0.45 s 就走，或者已经被挣脱/掉线也走。
func _hold_enough() -> bool:
	if not player.is_holding():
		return true
	# `_grab_hold` 是 Fighter 自己数的"抱了多久"，直接读它 —— 不要在脚本里另立一个计时器，
	# 那样两边会因为 hitstop / 状态打断而慢慢对不上。
	return player._grab_hold >= 0.45


## 手上还抓着人没有（抓技流程里）。
func _in_carry() -> bool:
	return player.state == Fighter.St.GRAB


## 正在出招没有。
func _attacking() -> bool:
	return player.state == Fighter.St.ATTACK


## 本拍"出手成功且没被打断"没有 —— 给 `confirm` 用。
##
## 用**本拍记账**（`ScriptedPlayer.fired`）而不是"此刻正在不在出招"：
## 后者在长拍（必杀 4.9 s）上会误判 —— 招式演完自然回待机，
## `confirm` 就以为上次没按上、再放一次（实测踩过）。
func _fired() -> bool:
	return _script.fired


## 取消窗口开了没有。
##
## 三个条件缺一不可：
##   1. 正在出招（ATTACK）—— 否则读到的 cancel_frame 是别的段甚至是 null；
##   2. **没有已排好的续段** —— 不看这一条的话，按下之后到"续段真正开始播"之间的
##      那几帧窗口仍然是开的，脚本会连按两次、第二次被 `_pending_chain` 吃掉，
##      表现就是"三连只出了两下"；
##   3. 当前帧 ≥ 这一段自己的 cancel_frame（manifest 实测值）。
func _chain_ready() -> bool:
	if player.state != Fighter.St.ATTACK:
		return false
	if player._pending_chain != "":
		return false
	var cf: Variant = GameDB.cancel_frame(player.clip_name())
	if cf == null:
		return false
	# 用 anim_position_s() 而不是 _current_frame()：前者对 `_ap == null` 有保护
	return player.anim_position_s() * 60.0 >= float(cf)


func _dummy_dead() -> bool:
	return dummy.hp <= 0


## 对手"站着"没有（不在受击/倒地/死亡里）。
##
## 技能三连的伤害全部 ≥ 倒地阈值，所以演完三拍对手一定躺在地上。
## 必杀的命中点都在 1.10 m 以上，对着倒地的人起手必落空 —— 要等它起身。
## 判据直接读状态枚举，不另立计时器（计时器会和状态机慢慢对不上）。
func _dummy_upright() -> bool:
	return dummy.state in [
		Fighter.St.IDLE, Fighter.St.WALK, Fighter.St.RUN, Fighter.St.RUN_STOP,
		Fighter.St.GUARD, Fighter.St.ATTACK,
	]


## 让 2P 停手（见 HaltableDummy）。只在剧本的终盘调用一次。
func _halt_dummy() -> void:
	if _halt_ai == null:
		return
	_halt_ai.halted = true
	print("[record] 第 %d 帧：2P 停手（终盘编排，见 HaltableDummy 注释）" % _watch)


## 角色"能接受新指令"没有。
##
## **必须把 GUARD 算进来**：默认举防之后，角色闲下来就在防御状态里，
## 不认 GUARD 的话所有带闸门的拍都会一直等到 `gate_max` 超时才跳过。
func _p_free() -> bool:
	return player.state in [
		Fighter.St.IDLE, Fighter.St.GUARD, Fighter.St.WALK,
		Fighter.St.RUN, Fighter.St.RUN_STOP,
	]


## 补刀的闸门：对手已经倒了就直接放行（此时 1P 在胜利演出里，按键本来也会被忽略，
## 但闸门放行能让这一拍 2 帧就过，不会白等 150 帧）。
func _finish_gate() -> bool:
	return _dummy_dead() or _p_free()


## 必杀前的一步：把假人血量压到"必杀打不死、补刀能收掉"的水平，顺便打一句横幅。
##
## **这是编排，不是改数值。** 一局真实对打打到 500 血要两分钟，35 秒的短片凑不出收束。
##
## 血量为什么取 `必杀单段 × 4 + 1`：
##   · 必杀中段一共 4 段命中点，如果**全中**，就把血打到只剩 1 ——
##     于是必杀能完整演完（要的就是它能完整演完：中段有地面冲击波这个签名特效），
##     收尾交给后面那一记突进；
##   · 只中一部分也不会卡死：突进 26 伤、被打断就重按，最多三拍必能收掉。
## 4 是 manifest 里 `Ultimate_Attack.hit_points` 的长度，不是编的。
func _ultimate_enter() -> void:
	var ult := GameDB.damage("Ultimate_Attack")
	var pts: Variant = GameDB.clip("Ultimate_Attack").get("hit_points")
	var n: int = (pts as Array).size() if pts is Array else 1
	dummy.hp = maxi(1, ult * maxi(1, n) + 1)
	dummy.hp_changed.emit(dummy.hp, dummy.max_hp)
	print("[record] 收尾设定：假人血量 → %d（= 必杀单段 %d × %d 段 + 1）" % [
		dummy.hp, ult, maxi(1, n)])
	game.hud.say("必杀 · 三段连段", "ULTIMATE", 1.2)


## 生成一个"打一句横幅"的回调（给 on_enter 用）。
## 用 HUD 自己的 say() 而不是另铺一层字幕：录下来的就是玩家真会看到的东西。
func _say(zh: String, en: String, seconds := 1.0) -> Callable:
	return func() -> void:
		game.hud.say(zh, en, seconds)


# =====================================================================
# 产物
# =====================================================================
func _resolve_out_dir() -> String:
	var env := OS.get_environment("REC_OUT")
	if env != "":
		return env
	# 和 reel.gd 同一套算法：从 res:// 往上退两级到工作区根再拼。
	# 产物**不写进 res://**，否则 Godot 会给每张中间图生成 .import。
	var proj := ProjectSettings.globalize_path("res://")
	var parts := proj.replace("\\", "/").split("/", false)
	var root := "/".join(Array(parts).slice(0, maxi(1, parts.size() - 2)))
	return root.path_join(OUT_SUBDIR)


func _dump_trace() -> void:
	var lines: Array[String] = []
	lines.append("# 实机录制剧本实跑记录")
	lines.append("viewport %dx%d  physics %d Hz" % [
		int(get_viewport().get_visible_rect().size.x),
		int(get_viewport().get_visible_rect().size.y),
		Engine.physics_ticks_per_second])
	lines.append("engage=%.3f grab_reach=%.3f grab_hold_distance=%.3f throw_flight=%.3f walk=%.3f run=%.3f" % [
		GameDB.engage_distance, GameDB.grab_reach, GameDB.grab_hold_distance,
		GameDB.throw_flight, GameDB.walk_speed, GameDB.run_speed])
	lines.append("")
	lines.append("%-30s %s" % ["拍", "实耗 / 交棒时的角色状态"])
	lines.append("-".repeat(64))
	for t in _script.trace:
		lines.append(String(t))
	lines.append("-".repeat(64))
	lines.append("剧本拍数 %d / 已走完 %d" % [_script.total_frames(), _script.idx])
	lines.append("总帧数 %d = %.2f s @60Hz" % [_watch, float(_watch) / 60.0])
	lines.append("收尾状态 %s" % game.state_text())
	lines.append("1P 抓取 %d 次 / 投掷 %d 次   2P 血量 %d" % [
		player.grabs_done, player.throws_done, dummy.hp])
	lines.append("")
	lines.append("# 1P 状态变迁（帧号 从 → 到）")
	lines.append("-".repeat(64))
	for e in _events:
		lines.append(String(e))
	var text := "\n".join(lines) + "\n"
	var fh := FileAccess.open(_trace_path, FileAccess.WRITE)
	if fh != null:
		fh.store_string(text)
		fh.close()
	print("[record] trace → %s" % _trace_path)
	print(text)
