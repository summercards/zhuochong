extends Node
## 冒烟测试：真启动一局，用脚本驱动玩家，逐步断言整条链路。
##
## 为什么要"真启动"而不是单元测试：这个模板的绝大多数失败模式是
## **跨组件时序**（动画帧 / 物理帧 / 判定当帧 / 信号顺序），单元测试照不到。
##
## 分步模型：每一步**只执行一次**，需要等就设 `_wait`；需要轮询条件就不推进。
## （第一版写成"每帧都执行当前步"，结果攻击被每帧重放 —— 所以这里显式分开。）

const WAIT_ATTACK := 0.75      # 一段攻击动画播完并结算的等待
const WAIT_KO := 0.60          # KO 后等胜负判定落定


## 测试用 AI：一直按住举防。用来真跑"Guard_Start → Guard_Loop"这段
## （不能靠键盘，headless 没有输入）。
class HoldGuardAI extends DummyAI:
	func poll(_me: Node3D, _opponent: Node3D, _delta: float) -> InputFrame:
		var f := InputFrame.new()
		f.guard = true
		return f


## 测试用 AI：一直按住下蹲。同 Guard，用来真跑"Crouch → Crouch_Idle"。
## 这两段是**同一类 bug** 的两个现场（见 _clip_finished 的注释）。
class HoldCrouchAI extends DummyAI:
	func poll(_me: Node3D, _opponent: Node3D, _delta: float) -> InputFrame:
		var f := InputFrame.new()
		f.crouch = true
		return f


## 测试用 AI：每帧都按一次攻击键。用来真跑"被抓的人连按挣脱"。
## 为什么不用 DummyAI：那个 AI 的挣脱分支是**随机**的，测不出"按键次数累到阈值就断"。
class MashAI extends DummyAI:
	func poll(_me: Node3D, _opponent: Node3D, _delta: float) -> InputFrame:
		var f := InputFrame.new()
		f.light = true
		return f


## 测试用输入源：按脚本**逐帧**吐 `InputFrame`。
## 用来真跑"连按两次方向起跑"这条**走输入边沿**的路径 ——
## 直接调内部函数会把"上帧没按、这帧按下"这个要验的东西绕过去。
class ScriptedAI extends DummyAI:
	var seq: Array = []
	var i := 0

	func feed(list: Array) -> void:
		seq = list.duplicate()
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

var _results: Array = []
var _failed := 0
var _step := 0
var _wait := 0.0
var _elapsed := 0.0
var _since_step := 0.0
var _marks := {}
## 当前这一格已经执行过几次（死循环护栏，见 `_run`）
var _step_runs := 0

# --- 道具 / 跳踢 用例的跨步暂存 ---
## 空手打碎用了多少下（`_smash_loop` 填）
var _smash_hits := 0
## 跳跃期间受击体抬升的峰值（米）与剩余采样帧数
var _jump_peak := 0.0
var _jump_watch := 0
## 开着的时候每帧记一次 `player.clip_name()`（用来验"跳踢是哪几段串起来的"）
var _record_clips := false
var _kick_clips: Array[String] = []


func _ready() -> void:
	game = get_parent().get_node_or_null("Main") as Game
	if game == null:
		_die("找不到 Main 节点")
		return
	player = game.player
	dummy = game.dummy


func _process(delta: float) -> void:
	if game == null:
		return
	_elapsed += delta
	_since_step += delta
	if _record_clips:
		var c := player.clip_name()
		if _kick_clips.is_empty() or _kick_clips[_kick_clips.size() - 1] != c:
			_kick_clips.append(c)
	if _wait > 0.0:
		_wait -= delta
		if _wait > 0.0:
			return
		_wait = 0.0
	_run()


func _advance(wait := 0.0) -> void:
	_step += 1
	_wait = wait
	_since_step = 0.0
	_step_runs = 0


func _run() -> void:
	# 同一格最多执行这么多次 —— 超过就判定为"中途抛错/死循环"。
	# 为什么需要它：一个步骤里在 `_advance()` **之前**抛了错，`_wait` 就留在 0，
	# 下一帧 `_run()` 又从头执行同一格 —— 于是无限重跑，日志被刷爆、
	# 套件既不红也不结束（第一次跑那 3500 行就是这么来的）。
	# 留出的余量给两个**故意自我循环**的步骤用：打碎（≤10 拳）、跳跃采样（≤130 帧）。
	_step_runs += 1
	if _step_runs > 2000:
		_die("第 %d 步重复执行了 %d 次 —— 中途抛错或死循环" % [_step, _step_runs])
		return
	match _step:
		# --- 0. 启动期：数据层与角色 ---
		0:
			_check("GameDB 装载 68 段 clip", GameDB.clips.size() == 68,
				"实得 %d" % GameDB.clips.size())
			_check("manifest 无装载错误", GameDB.load_errors.is_empty(),
				str(GameDB.load_errors))
			_check("玩家满血", player.hp == GameDB.MAX_HP and player.max_hp == 500,
				"hp=%d/%d" % [player.hp, player.max_hp])
			_check("双方朝向相对", player.facing == 1 and dummy.facing == -1,
				"p=%+d d=%+d" % [player.facing, dummy.facing])
			_check("受击体尺寸来自实测", absf(GameDB.HURTBOX_RADIUS - 0.30) < 0.001
				and absf(GameDB.HURTBOX_HEIGHT - 1.732) < 0.001
				and absf(GameDB.HURTBOX_HEIGHT_CROUCH - 1.488) < 0.001,
				"r=%.3f h=%.3f/%.3f" % [GameDB.HURTBOX_RADIUS, GameDB.HURTBOX_HEIGHT,
					GameDB.HURTBOX_HEIGHT_CROUCH])
			_check("交战距离由实测推出（非兜底值）",
				absf(GameDB.engage_distance - 1.18) < 0.06,
				"engage=%.3f m" % GameDB.engage_distance)
			_check("移动速度由腿长与时长推出",
				absf(GameDB.walk_speed - 1.027) < 0.02 and absf(GameDB.run_speed - 3.082) < 0.05,
				"walk=%.3f run=%.3f m/s" % [GameDB.walk_speed, GameDB.run_speed])
			_check("伤害公式：轻拳 = 12", GameDB.damage("Light_01") == 12,
				"实得 %d" % GameDB.damage("Light_01"))
			_check("伤害公式：重拳 = 21", GameDB.damage("Heavy_01") == 21,
				"实得 %d" % GameDB.damage("Heavy_01"))
			_check("轻 < 重 < 冲刺", GameDB.damage("Light_01") < GameDB.damage("Heavy_01")
				and GameDB.damage("Heavy_01") < GameDB.damage("Dash_Attack"),
				"%d < %d < %d" % [GameDB.damage("Light_01"), GameDB.damage("Heavy_01"),
					GameDB.damage("Dash_Attack")])
			# 整张伤害表钉死 —— docs/操作说明.md 里那张表就是这些数，
			# 改了公式或改了动画属性，这里会红，文档也就能被追着一起改。
			#
			# 注意两处临界值（18.5 与 20.5）暴露了一个跨语言的坑：
			# **GDScript 的 round() 是四舍五入（半分远离零），Python 的 round() 是
			# 银行家舍入（半分取偶）。**同一公式在 Python 里算出 18/20，在 GDScript
			# 里是 19/21 —— 写参考实现时必须用 ROUND_HALF_UP，否则对不上。
			var want: Dictionary = {
				"Light_01": 12, "Light_02": 15, "Light_03": 19,
				"Heavy_01": 21, "Dash_Attack": 26,
				"Uppercut": 21, "Low_Attack": 20, "Skill_03": 21,
				"Knockdown_Attack": 28, "Air_Light": 16, "Air_Heavy": 15,
			}
			var drift: Array[String] = []
			for k in want.keys():
				var got: int = GameDB.damage(String(k))
				if got != int(want[k]):
					drift.append("%s 期望 %d 实得 %d" % [k, want[k], got])
			_check("伤害表 11 项与公式一致", drift.is_empty(), str(drift))
			_check("轻拳第 3 段跨过击倒阈值（三段轻拳的最后一下会打倒对手）",
				GameDB.damage("Light_02") < GameDB.KNOCKDOWN_DAMAGE
				and GameDB.damage("Light_03") >= GameDB.KNOCKDOWN_DAMAGE,
				"轻2=%d < 阈值%d ≤ 轻3=%d" % [GameDB.damage("Light_02"),
					GameDB.KNOCKDOWN_DAMAGE, GameDB.damage("Light_03")])
			_check("轴约定：前 = +Z（脚尖）", _axis_ok(),
				"toe_z=%.3f eye_dx=%.3f" % [_toe_z(), _eye_dx()])
			_advance()

		# --- 1. 开场演出 -> FIGHT ---
		1:
			if game.phase == Game.Phase.FIGHT:
				_check("开场演出结束并进入 FIGHT", true, "%.2f s" % _elapsed)
				_advance()
			elif _elapsed > 10.0:
				_die("开场演出 10s 未结束，phase=%s" % Game.Phase.keys()[game.phase])

		# --- 2. 假人 AI 主动出击，应当自己打中玩家 ---
		2:
			if player.hp < player.max_hp:
				_check("假人 AI 能主动命中玩家", true,
					"玩家掉血 %d（%.2f s）" % [player.max_hp - player.hp, _elapsed])
				_advance()
			elif _since_step > 25.0:
				_die("25s 内假人一次都没命中玩家（AI 或判定链路断了）")

		# --- 3. 关掉 AI，改用脚本驱动玩家：轻拳必须命中，且伤害 = 公式值 ---
		3:
			dummy.set_ai(false)          # 假人转为"无输入"，让测试确定性
			_close_in(0.9)
			player._start_attack("Light_01")
			_marks["hp_before"] = dummy.hp
			_advance(WAIT_ATTACK)

		4:
			var dealt: int = int(_marks["hp_before"]) - dummy.hp
			_check("玩家轻拳命中假人", dealt > 0, "掉血 %d" % dealt)
			_check("伤害等于公式值 12", dealt == 12, "实得 %d" % dealt)
			_check("轻拳不进倒地（12 < 阈值 18）",
				dummy.state != Fighter.St.DOWN, "假人状态=%s" % dummy.label_en())
			_advance()

		# --- 5. 重拳：伤害 21 ≥ 阈值 18 → 进倒地流程 ---
		5:
			_close_in(0.8)
			player._start_attack("Heavy_01")
			_advance(WAIT_ATTACK * 2.0)

		6:
			_check("重拳打出倒地流程",
				dummy.state == Fighter.St.DOWN or dummy.state == Fighter.St.IDLE,
				"假人状态=%s hp=%d" % [dummy.label_en(), dummy.hp])
			_advance()

		# --- 7. 推箱：站在对手身体里也要被顶出去 ---
		7:
			dummy.reset_fighter(0.0, -1)
			dummy.opponent = player
			player.reset_fighter(-0.10, 1)
			player.opponent = dummy
			player._move_world(0.0)
			var sep := absf(player.global_position.x - dummy.global_position.x)
			_check("推箱生效：撞不穿对手",
				sep >= GameDB.PUSH_SEPARATION - 0.001,
				"间距 %.4f m，下限 %.4f m" % [sep, GameDB.PUSH_SEPARATION])
			_check("推箱方向正确（没被弹到对手另一侧）",
				player.global_position.x < dummy.global_position.x,
				"p=%+.3f d=%+.3f" % [player.global_position.x, dummy.global_position.x])
			# 舞台边界夹逼
			player.reset_fighter(GameDB.STAGE_HALF_WIDTH + 5.0, 1)
			player.opponent = dummy
			player._move_world(0.0)
			_check("舞台边界夹逼生效",
				absf(player.global_position.x - GameDB.STAGE_HALF_WIDTH) < 0.001,
				"x=%+.4f 上限=%.4f" % [player.global_position.x, GameDB.STAGE_HALF_WIDTH])
			_advance()

		# --- 8. KO 流程 ---
		8:
			dummy.reset_fighter(0.0, -1)
			dummy.opponent = player
			dummy.hp = 1
			player.reset_fighter(-GameDB.engage_distance * 0.9, 1)
			player.opponent = dummy
			player._start_attack("Heavy_01")
			_advance(WAIT_ATTACK * 2.0)

		9:
			_check("KO 触发：进入 KO/OVER 阶段", game.phase >= Game.Phase.KO,
				"phase=%s" % Game.Phase.keys()[game.phase])
			_check("胜者判定为玩家", game.winner == player, "winner=%s" % str(game.winner))
			_check("败者 hp 归零", dummy.hp == 0, "hp=%d" % dummy.hp)
			_advance(WAIT_KO)

		10:
			_check("败者播 Death（DEAD 状态）", dummy.state == Fighter.St.DEAD,
				"假人状态=%s" % dummy.label_en())
			_check("胜者进胜利演出", player.state == Fighter.St.INTRO,
				"玩家状态=%s" % player.label_en())
			_advance()

		# --- 11. 举防：必须真的进到循环防（这是 Guard_Loop 引擎改名 bug 的表面症状）---
		11:
			dummy.set_ai(false)
			_close_in(0.9)
			# 用一个"一直举防"的脚本输入源真跑状态机，而不是直接塞 clip
			player.ai = HoldGuardAI.new()
			player.is_player = false
			player._set_state(Fighter.St.IDLE)
			player._play("Idle_01")
			_advance(1.2)

		12:
			_check("举防进入循环防（Guard_Loop 解析到引擎名 Guard）",
				player.clip_name() == "Guard_Loop",
				"清单名=%s 引擎名=%s 状态=%s" % [
					player.clip_name(), GameDB.engine_name(player.clip_name()),
					player.label_en()])
			_check("引擎名差异表与实测一致",
				GameDB.engine_name("Guard_Loop") == "Guard"
				and GameDB.engine_name("Charge_Loop") == "Charge_Loop",
				"Guard_Loop→%s  Charge_Loop→%s" % [
					GameDB.engine_name("Guard_Loop"), GameDB.engine_name("Charge_Loop")])
			player.ai = null
			player.is_player = true
			player._play("Idle_01")
			player._set_state(Fighter.St.IDLE)
			_advance()

		# --- 13. 重开 ---
		13:
			game._start_round()
			_advance(WAIT_KO)

		14:
			_check("重开后双方满血",
				player.hp == player.max_hp and dummy.hp == dummy.max_hp,
				"p=%d d=%d" % [player.hp, dummy.hp])
			_check("重开后回到开场演出", game.phase == Game.Phase.INTRO,
				"phase=%s" % Game.Phase.keys()[game.phase])
			_advance()

		# --- 15. 下蹲：与举防同一类 bug 的第二个现场 ---
		15:
			game.force_fight()
			dummy.set_ai(false)
			_close_in(1.2)
			player.ai = HoldCrouchAI.new()
			player.is_player = false
			player._set_state(Fighter.St.IDLE)
			player._play("Idle_01")
			_advance(1.0)

		16:
			_check("下蹲进入蹲防循环（Crouch → Crouch_Idle）",
				player.clip_name() == "Crouch_Idle" and player.state == Fighter.St.CROUCH,
				"清单名=%s 状态=%s" % [player.clip_name(), player.label_en()])
			_check("下蹲时受击体变矮（胶囊高度跟着换）",
				absf(_hurt_h() - GameDB.HURTBOX_HEIGHT_CROUCH) < 0.001,
				"胶囊高=%.3f 期望=%.3f" % [_hurt_h(), GameDB.HURTBOX_HEIGHT_CROUCH])
			player.ai = null
			player.is_player = true
			player._set_state(Fighter.St.IDLE)
			player._play("Idle_01")
			_advance(0.5)

		# --- 17. 全 clip 扫描：68 段清单 clip 每一段都要真能播、且引擎名对得上 ---
		17:
			var bad: Array[String] = []
			for n in GameDB.all_clip_names():
				player._play(String(n))
				var want: String = GameDB.engine_name(String(n))
				if player.engine_anim() != want:
					bad.append("%s(期望 %s，实得 %s)" % [n, want, player.engine_anim()])
			_check("68 段清单 clip 全部能播且引擎名一致", bad.is_empty(),
				"共 %d 段，异常 %d 段%s" % [GameDB.clips.size(), bad.size(),
					"" if bad.is_empty() else "：" + str(bad)])
			_check("清单名到引擎名的映射只动了 Guard_Loop 一条",
				GameDB.engine_name_fixups.size() == 1
				and GameDB.engine_name("Guard_Loop") == "Guard",
				"差异表=%s" % str(GameDB.engine_name_fixups))
			_advance(0.2)

		# --- 18. 打击感：屏幕层的三个量都必须跟着伤害走、并且有上限 ---
		18:
			# 直接调 _feed_hit_feel（而不是真打一拳）—— 这里验的是**换算关系**，
			# 用真命中会掺进状态机的时序抖动，测不出曲线本身。
			game._trauma = 0.0
			game._punch = 0.0
			game._feed_hit_feel(12, dummy)
			var lt: float = game._trauma
			var lp: float = game._punch
			var lflash: float = dummy.flash_strength()

			game._trauma = 0.0
			game._punch = 0.0
			game._feed_hit_feel(30, dummy)
			var ht: float = game._trauma
			var hp_: float = game._punch

			_check("打击感：抖动量随伤害递增（12 伤 < 30 伤）",
				ht > lt and lt > 0.0,
				"12 伤=%.3f  30 伤=%.3f" % [lt, ht])
			_check("打击感：缩放冲击随伤害递增",
				hp_ > lp and lp > 0.0,
				"12 伤=%.3f  30 伤=%.3f" % [lp, hp_])
			_check("打击感：抖动量被封顶（连击不爆表）",
				ht <= game.TRAUMA_MAX + 0.0001,
				"实得=%.3f 上限=%.3f" % [ht, game.TRAUMA_MAX])

			# 场景脉动也要被喂到（空间对打击有反应）
			var stage := game.stage
			_check("打击感：命中会触发场景脉动",
				stage != null and stage._pulse > 0.0,
				"pulse=%.3f" % (stage._pulse if stage != null else -1.0))

			# 受击闪白：够重的命中要闪，擦伤不闪
			dummy.clear_flash()
			dummy.trigger_flash(0.7)
			var f_hi: float = dummy.flash_strength()
			# 擦伤：低于阈值必须**完全不改当前状态**
			dummy.trigger_flash(0.05)
			var f_lo: float = dummy.flash_strength()
			_check("打击感：受击闪白会亮，且擦伤不闪（阈值 %.2f）" % Fighter.FLASH_MIN_STRENGTH,
				f_hi > 0.6 and absf(f_lo - f_hi) < 0.0001,
				"0.70 强度→%.3f ；再叠 0.05 强度→%.3f（应保持不变）" % [f_hi, f_lo])
			dummy.clear_flash()
			_check("受击闪白材质挂在全身网格上（一份材质闪全身）",
				player._flash_shape_count > 0 and dummy._flash_shape_count > 0,
				"玩家挂上 %d 个网格，假人 %d 个" % [player._flash_shape_count, dummy._flash_shape_count])

			# 程序化特效：生成 → 到期自动释放
			var vroot := game.vfx_root
			var before: int = Vfx.active_count(vroot)
			Vfx.impact(vroot, player.global_position + Vector3(0.5, 1.0, 0.0), 1.0,
				Vfx.POWER_HEAVY, Vfx.COLOR_HEAVY)
			var after: int = Vfx.active_count(vroot)
			_check("特效库：命中爆点会生成到特效根下",
				after == before + 1,
				"生成前 %d 个 → 生成后 %d 个" % [before, after])
			_check("特效库：命中爆点带着自己的材质实例（不与别的特效共用）",
				vroot.get_child(after - 1).material_override is ShaderMaterial,
				"材质=%s" % str(vroot.get_child(after - 1).material_override))

			# 重新喂一次大抖动，让它在下一步里真的落到相机上。
			# **不能在同一个 _process 里读相机** —— 抖是在 Game._process 里
			# 通过 _apply_hit_feel 叠到 cam 上的，这里同步读到的一定还是旧值
			# （第一版就是这么写的，断言必然失败）。
			game._trauma = 0.0
			game._feed_hit_feel(30, dummy)
			_advance(0.05)

		# --- 19. 打击感/特效的生命周期：全部要能自己收干净 ---
		19:
			# 抖动期间相机必须有滚转（证明抖动真的落到相机上了，不只是变量里有数）
			_check("打击感：抖动真的作用到了相机上（滚转被带偏）",
				absf(game.cam.rotation.z) > 0.0001,
				"命中瞬间相机滚转=%.4f°  trauma=%.3f" % [
					rad_to_deg(game.cam.rotation.z), game._trauma])

			# 等足够久让一切衰减完
			_advance(1.4)

		20:
			_check("打击感：抖动会自己衰减干净（不留永久歪镜头）",
				is_zero_approx(game._trauma) and is_zero_approx(game._punch),
				"trauma=%.4f punch=%.4f" % [game._trauma, game._punch])
			_check("打击感：抖完相机滚转回到 0",
				is_zero_approx(game.cam.rotation.z),
				"滚转=%.5f°" % rad_to_deg(game.cam.rotation.z))
			_check("受击闪白会自己衰减到 0（不留一层洗不掉的白）",
				is_zero_approx(dummy.flash_strength()),
				"闪白强度=%.4f" % dummy.flash_strength())
			_check("特效库：命中爆点到期自动释放（不泄漏节点）",
				Vfx.active_count(game.vfx_root) == 0,
				"残留 %d 个" % Vfx.active_count(game.vfx_root))
			_advance()

		# =================================================================
		# Task #7 投技：抓取 → 擒抱 → 投掷 → 击飞倒地；以及挣脱与代价
		# =================================================================

		# --- 21. 投技几何：四个数全部由实测推出，没有一个是"调"出来的 ---
		21:
			_check("投技：抓取手可达来自实测（Grab_Start 的 hand.R 落点）",
				absf(GameDB.grab_reach - 1.3626) < 0.0005,
				"实得 %.4f m" % GameDB.grab_reach)
			_check("投技：被擒间距 = 抓取手可达本身（被擒者站在手够得到的边界上）",
				absf(GameDB.grab_hold_distance - GameDB.grab_reach) < 0.0005,
				"实得 %.4f = %.4f（第一版多减了一个受击体半径，两人会穿模）" % [
					GameDB.grab_hold_distance, GameDB.grab_reach])
			_check("投技：擒抱上限 = Grab_Hold 循环一圈的时长",
				absf(GameDB.grab_hold_max - GameDB.duration("Grab_Hold")) < 0.0005,
				"实得 %.3f s（Grab_Hold=%.3f s）" % [GameDB.grab_hold_max,
					GameDB.duration("Grab_Hold")])
			_check("投技：投出滑行由被擒间距放大而来（不是另填的数）",
				absf(GameDB.throw_flight - GameDB.grab_hold_distance * 1.4) < 0.0005,
				"实得 %.4f = %.4f × 1.4" % [GameDB.throw_flight, GameDB.grab_hold_distance])
			_advance()

		# --- 22. 贴进抓取手可达范围内，按抓取键起手 ---
		22:
			_place_pair(GameDB.grab_reach * 0.75)
			player._start_grab()
			_check("投技：起手进入 GRAB 状态并播 Grab_Start",
				player.state == Fighter.St.GRAB and player.clip_name() == "Grab_Start",
				"状态=%s clip=%s" % [player.label_en(), player.clip_name()])
			_advance()

		23:
			if player.is_holding():
				_check("投技：贴上对手后扣住（判定帧 28/60 ≈ 0.47 s 到了才抓）",
					player.is_holding() and dummy.is_held(),
					"holding=%s held=%s" % [str(player.is_holding()), str(dummy.is_held())])
				_check("投技：抓中后切进 Grab_Hold 循环等出手",
					player.clip_name() == "Grab_Hold" and dummy.state == Fighter.St.GRABBED,
					"抓取方 clip=%s ；被擒方状态=%s" % [player.clip_name(), dummy.label_en()])
				var sep := absf(player.global_position.x - dummy.global_position.x)
				_check("投技：被擒间距被硬约束到实测值（不是靠物理碰）",
					absf(sep - GameDB.grab_hold_distance) < 0.03,
					"实得 %.4f m，契约 %.4f m" % [sep, GameDB.grab_hold_distance])
				_check("投技：被擒者被摆成面朝抓取者",
					dummy.facing == -player.facing,
					"抓取者 facing=%+d 被擒者 facing=%+d" % [player.facing, dummy.facing])
				_advance()
			elif _since_step > 5.0:
				_check("投技：贴上对手后扣住（判定帧到了才抓）", false,
					"5 s 未抓住（抓取判定 / 可达距离链路断了）")
				_advance()

		# --- 24. 手上有人时再按一次抓取键 → 投掷 ---
		24:
			_marks["throw_hp0"] = dummy.hp
			player._start_grab()          # holding != null → _begin_throw()
			_check("投技：抱着人时再按抓取键切进 Throw 段",
				player.clip_name() == "Throw" and player.is_holding(),
				"clip=%s holding=%s" % [player.clip_name(), str(player.is_holding())])
			_advance()

		25:
			if player.throws_done >= 1:
				var dmg: int = int(_marks["throw_hp0"]) - dummy.hp
				_check("投技：投出瞬间就松开手（两边引用一起清）",
					player.is_holding() == false and dummy.is_held() == false,
					"holding=%s held=%s" % [str(player.is_holding()), str(dummy.is_held())])
				_check("投技：投出伤害 = Throw 的公式值 %d" % GameDB.damage("Throw"),
					dmg == GameDB.damage("Throw") and dmg > 0, "实得 %d" % dmg)
				_check("投技：被投者被打成击飞姿态 Launch_Hit（不是普通受击）",
					dummy.state == Fighter.St.HIT and dummy.clip_name() == "Launch_Hit",
					"状态=%s clip=%s" % [dummy.label_en(), dummy.clip_name()])
				_advance(0.8)
			elif _since_step > 4.0:
				_check("投技：按第二次抓取键把对手投出去", false, "4 s 未到 Throw 的结算帧")
				_advance()

		# --- 26. 击飞 → 倒地（投技的终点必须是对手躺在地上）---
		26:
			if dummy.state == Fighter.St.DOWN:
				_check("投技：被投者落进倒地流程（Launch_Hit → Knockdown → DOWN）",
					true, "状态=%s clip=%s" % [dummy.label_en(), dummy.clip_name()])
				_advance(0.5)
			elif _since_step > 3.0:
				_check("投技：被投者落进倒地流程（Launch_Hit → Knockdown → DOWN）",
					false, "3 s 没倒地，状态=%s clip=%s" % [dummy.label_en(), dummy.clip_name()])
				_advance(0.5)

		# --- 27. 挣脱的对照：不挣扎就不该自己断 ---
		27:
			_place_pair(GameDB.grab_reach * 0.75)
			player._start_grab()
			_advance()

		28:
			if player.is_holding():
				_advance(0.6)             # 静默 0.6 s：没人按键，应该还扣着
			elif _since_step > 5.0:
				_check("投技：挣脱对照 —— 先抓住", false, "5 s 未抓住")
				_advance()

		29:
			_check("投技：被擒者不挣扎就不会自己断（挣脱必须来自输入）",
				player.is_holding() and dummy.is_held(),
				"holding=%s held=%s" % [str(player.is_holding()), str(dummy.is_held())])
			# 换成"每帧按一下攻击键"的输入源 —— 被抓的人要能自己挣脱
			dummy.ai = MashAI.new()
			dummy.is_player = false
			_marks["t_mash"] = _elapsed
			_advance()

		30:
			if not dummy.is_held():
				var dt: float = _elapsed - float(_marks["t_mash"])
				_check("投技：被擒者连按攻击键能挣脱（累到阈值 %d 就断）" % GameDB.GRAB_MASH_BREAK,
					player.is_holding() == false,
					"连按 %.3f s 后两边都松开了" % dt)
				_check("投技：挣脱很快（阈值不是形同虚设）", dt < 0.5,
					"用时 %.3f s（阈值 %d）" % [dt, GameDB.GRAB_MASH_BREAK])
				_check("投技：挣脱不是白赚 —— 抓取方同时失衡",
					player.state == Fighter.St.HIT and dummy.state == Fighter.St.HIT,
					"抓取方=%s 被擒方=%s" % [player.label_en(), dummy.label_en()])
				dummy.ai = null
				dummy.is_player = true
				_advance(0.6)
			elif _since_step > 0.6:
				_check("投技：被擒者连按攻击键能挣脱", false,
					"0.6 s 未挣脱（阈值 %d）" % GameDB.GRAB_MASH_BREAK)
				dummy.ai = null
				dummy.is_player = true
				_advance(0.6)

		# --- 31. 指令投的代价：抱着人的时候被打，必须松手 ---
		31:
			_place_pair(GameDB.grab_reach * 0.75)
			player._start_grab()
			_advance()

		32:
			if player.is_holding():
				player.receive_hit(dummy, 12, "Light_01")
				_check("投技：抓取者挨打会松手（抱着人时最脆 —— 这是指令投的风险）",
					player.is_holding() == false and dummy.is_held() == false,
					"holding=%s held=%s" % [str(player.is_holding()), str(dummy.is_held())])
				_check("投技：松手后被擒者回到站立（不留 GRABBED 幽灵状态）",
					dummy.state == Fighter.St.IDLE, "被擒方状态=%s" % dummy.label_en())
				_advance()
			elif _since_step > 5.0:
				_check("投技：抓取者挨打会松手（抱着人时最脆）", false, "5 s 未抓住")
				_advance()

		# --- 33. 强制重开：两边的抓取引用必须一起清（防"新回合还拎着人"）---
		33:
			_place_pair(GameDB.grab_reach * 0.75)
			player._start_grab()
			_advance()

		34:
			if player.is_holding():
				player.reset_fighter(-2.0, 1)
				dummy.reset_fighter(2.0, -1)
				_check("投技：强制重开后两边引用一起清干净（无幽灵状态）",
					player.holding == null and player.grabbed_by == null
					and dummy.holding == null and dummy.grabbed_by == null,
					"p.holding=%s p.grabbed_by=%s d.holding=%s d.grabbed_by=%s" % [
						str(player.holding), str(player.grabbed_by),
						str(dummy.holding), str(dummy.grabbed_by)])
				_check("投技：重开后双方状态也复位到开场演出",
					player.state == Fighter.St.INTRO and dummy.state == Fighter.St.INTRO,
					"p=%s d=%s" % [player.label_en(), dummy.label_en()])
				_advance()
			elif _since_step > 5.0:
				_check("投技：强制重开后两边引用一起清干净", false, "5 s 未抓住")
				_advance()

		# =================================================================
		# Task #8 技能特效：地面冲击波 + 蓄力 / 大招光环
		# =================================================================

		# --- 35. 蓄力：整段盖一层跟随光环，到签名帧放地面波，演完自己收 ---
		35:
			_far_apart()
			_clear_vfx()
			player._start_special("Charge")
			_check("技能特效：蓄力起手会起一层跟随光环（挂在角色身上）",
				Vfx.active_count(player) >= 1,
				"角色身上 %d 个，场景 %d 个" % [
					Vfx.active_count(player), Vfx.active_count(game.vfx_root)])
			_check("技能特效：光环不挂在场景根下（它要跟着人走）",
				Vfx.active_count(game.vfx_root) == 0,
				"场景特效 %d 个" % Vfx.active_count(game.vfx_root))
			_advance(0.6)

		36:
			_check("技能特效：蓄力过程中光环一直在",
				Vfx.active_count(player) >= 1,
				"角色身上 %d 个" % Vfx.active_count(player))
			_check("技能特效：签名帧之前不放地面波（Charge=%.0f 帧 ≈ %.2f s）" % [
				float(Fighter.GROUND_VFX["Charge"]["frame"]),
				float(Fighter.GROUND_VFX["Charge"]["frame"]) / 60.0],
				Vfx.active_count(game.vfx_root) == 0,
				"0.60 s 时场景特效 %d 个" % Vfx.active_count(game.vfx_root))
			_advance(0.80)                # 累计 1.40 s > 1.20 s 签名帧

		37:
			_check("技能特效：蓄力到签名帧放出地面冲击波（环 + 竖向爆点两层）",
				Vfx.active_count(game.vfx_root) >= 2,
				"场景特效 %d 个" % Vfx.active_count(game.vfx_root))
			_advance(1.6)                 # 累计 3.00 s > Charge 总长 1.833 s

		38:
			_check("技能特效：蓄力演完光环自己收干净（不留常亮）",
				Vfx.active_count(player) == 0 and Vfx.active_count(game.vfx_root) == 0,
				"角色身上 %d 个，场景 %d 个" % [
					Vfx.active_count(player), Vfx.active_count(game.vfx_root)])
			_check("技能特效：蓄力演完回到站立",
				player.state == Fighter.St.IDLE, "状态=%s" % player.label_en())
			_advance()

		# --- 39. 大招：三段连续，全程盖一层更大光环，中段/收尾各放一次地面波 ---
		39:
			_far_apart()
			_clear_vfx()
			player._start_ultimate()
			_check("技能特效：大招起手会起一层更大的光环",
				Vfx.active_count(player) >= 1,
				"角色身上 %d 个" % Vfx.active_count(player))
			_advance(0.6)

		40:
			_check("技能特效：大招第一段（Ultimate_Start）不抢跑地面波",
				Vfx.active_count(game.vfx_root) == 0,
				"场景特效 %d 个" % Vfx.active_count(game.vfx_root))
			_advance(1.80)                # 累计 2.40 s；Ultimate_Attack 签名帧 ≈ 2.10 s

		41:
			_check("技能特效：大招中段到签名帧放出地面冲击波",
				Vfx.active_count(game.vfx_root) >= 2,
				"场景特效 %d 个" % Vfx.active_count(game.vfx_root))
			_advance(2.6)                 # 累计 5.00 s；三段总长 4.233 s，留 0.77 s 余量

		42:
			_check("技能特效：大招三段演完自动收招（回到站立）",
				player.state == Fighter.St.IDLE, "状态=%s" % player.label_en())
			_check("技能特效：大招演完光环收干净",
				Vfx.active_count(player) == 0,
				"角色身上 %d 个" % Vfx.active_count(player))
			_check("技能特效：大招演完场景特效也自己清空",
				Vfx.active_count(game.vfx_root) == 0,
				"场景 %d 个" % Vfx.active_count(game.vfx_root))
			_advance()

		# --- 43. 每个登记的技能都能放出地面波，且同一段只放一次 ---
		43:
			_far_apart()
			_clear_vfx()
			var missing: Array[String] = []
			var repeats: Array[String] = []
			for key in Fighter.GROUND_VFX.keys():
				var c := String(key)
				player._play(c)                       # 让 _clip = 该技能（_play 会复位"只放一次"闩）
				player._fire_ground_vfx(1.0e9)        # 传一个必定过帧的帧号
				var n1: int = Vfx.active_count(game.vfx_root)
				player._fire_ground_vfx(1.0e9)
				var n2: int = Vfx.active_count(game.vfx_root)
				if n1 <= 0:
					missing.append(c)
				if n2 != n1:
					repeats.append(c)
				_clear_vfx()
			_check("技能特效：登记在 GROUND_VFX 的每个技能都能放出地面冲击波",
				missing.is_empty(),
				"共 %d 个技能，未放出：%s" % [Fighter.GROUND_VFX.size(), str(missing)])
			_check("技能特效：同一段招式的冲击波只放一次（不会逐帧重放）",
				repeats.is_empty(), "会重放的：%s" % str(repeats))
			_advance(0.2)

		# --- 44. 可拾取物：数据层契约 + 铺场 ---
		44:
			_check("道具契约：三档边长 = 受击体半径 × [1.1,1.5,1.9]",
				GameDB.prop_sizes.size() == GameDB.PROP_SIZE_K.size()
				and absf(GameDB.prop_sizes[0] - GameDB.HURTBOX_RADIUS * 1.1) < 0.001
				and absf(GameDB.prop_sizes[2] - GameDB.HURTBOX_RADIUS * 1.9) < 0.001,
				str(GameDB.prop_sizes))
			_check("道具契约：耐久 63 = 重拳 21 × 3 下（'多次才坏'的落点）",
				GameDB.damage("Heavy_01") > 0
				and GameDB.prop_max_hp == GameDB.damage("Heavy_01") * GameDB.PROP_HITS_TO_BREAK,
				"耐久 %d = %d × %d" % [GameDB.prop_max_hp, GameDB.damage("Heavy_01"),
					GameDB.PROP_HITS_TO_BREAK])
			_check("道具契约：容器伤害 21 = 一次重拳（同一冲量，所以抡 3 下碎）",
				GameDB.prop_impact_damage == GameDB.damage("Heavy_01"),
				"容器 %d / 重拳 %d" % [GameDB.prop_impact_damage, GameDB.damage("Heavy_01")])
			_check("道具契约：拾取距离 = 抓取距离，投掷出手高 = Throw 手高 1.1347",
				is_equal_approx(GameDB.prop_pickup_reach, GameDB.grab_reach)
				and absf(GameDB.prop_throw_release_height - 1.1347) < 0.001,
				"拾取 %.4f m / 出手高 %.4f m" % [GameDB.prop_pickup_reach,
					GameDB.prop_throw_release_height])
			# 跳踢选段的几何依据（只能选 Air_Heavy，不能选 Air_Light）：
			# 判定盒下沿低于站立受击体顶，才够得到站地上的人。
			var stand_top: float = GameDB.HURTBOX_HEIGHT
			var kick_bottom: float = GameDB.first_hit_height(Fighter.JUMP_KICK_CLIP) \
				- Fighter.HITBOX_HEIGHT * 0.5
			var light_bottom: float = GameDB.first_hit_height("Air_Light") \
				- Fighter.HITBOX_HEIGHT * 0.5
			_check("跳踢=Air_Heavy 是几何上的唯一解（Air_Light 够不到站地上的人）",
				kick_bottom < stand_top and light_bottom >= stand_top,
				"重下沿 %.4f < 站立顶 %.4f ≤ 轻下沿 %.4f" % [
					kick_bottom, stand_top, light_bottom])
			_check("场上铺了 %d 个可拾取物" % GameDB.PROP_COUNT,
				game.carryables != null
				and game.carryables.props.size() == GameDB.PROP_COUNT,
				"%d 个" % (game.carryables.props.size() if game.carryables != null else -1))
			# 先真重置一次再验：前面 40 多步的拳脚已经砸过场上的箱子了
			# （`_do_hit` 会顺带扫贴地带），所以要验的是"重开一局之后的状态"，
			# 而不是"跑了半天之后的残局"。`reset_all()` 就是 `Game._start_round` 调的那个。
			game.carryables.reset_all()
			_check("重开一局后所有物体都躺在地上（IDLE，满耐久，可拾取）",
				game.carryables.pickable_count() == GameDB.PROP_COUNT,
				"%d / %d" % [game.carryables.pickable_count(), GameDB.PROP_COUNT])
			_advance()

		# --- 45. 捡起来（复用 Grab_Start「伸手取物」）---
		45:
			_props_isolate(0, 0.65)
			player._start_pick()
			_advance(0.70)                # Grab_Start 判定帧 28 → 0.467 s
		46:
			var c0: Carryable = player.carrying
			_check("拾取：按拾取键走 Grab_Start 并真的把箱子拿到了手",
				c0 != null and c0.state == Carryable.CSt.HELD,
				"carrying=%s state=%s" % [
					"有" if c0 != null else "null",
					str(c0.state) if c0 != null else "-"])
			var gap: float = _carry_gap()
			_check("拾取：箱子跟到了手上（手骨附近一个边长内）",
				c0 != null and gap < maxf(c0.size_m, 0.33) * 1.2,
				"差 %.3f m（边长 %.2f）" % [gap, c0.size_m if c0 != null else 0.0])
			_check("拾取：拿在手上就不再参与地面/被打查询（碰撞层被置 0）",
				c0 != null and c0._area.collision_layer == 0,
				"layer=%d" % (c0._area.collision_layer if c0 != null else -1))
			_advance(0.1)

		# --- 46. 拿在手里砸人：伤害 = 招式伤害 + 容器伤害，手上的箱子同掉一份耐久 ---
		47:
			player.global_position = Vector3(-0.2, 0.0, 0.0)
			player.facing = 1
			dummy.hp = dummy.max_hp
			dummy.set_ai(false)
			dummy.opponent = player
			dummy.global_position = Vector3(-0.2 + 0.95, 0.0, 0.0)
			_marks["d_hp0"] = dummy.hp
			_marks["box_hp0"] = player.carrying.hp
			player._start_attack("Light_01")
			_advance(0.9)
		48:
			var dealt: int = int(_marks["d_hp0"]) - dummy.hp
			var bhp0: int = int(_marks["box_hp0"])
			var want_swing: int = GameDB.damage("Light_01") + GameDB.prop_impact_damage
			_check("手持砸击：伤害 = 轻拳 %d + 容器 %d = %d" % [
				GameDB.damage("Light_01"), GameDB.prop_impact_damage, want_swing],
				dealt == want_swing, "实得 %d" % dealt)
			_check("手持砸击：手上的箱子同掉一份耐久（砸中才掉）",
				player.carrying != null
				and bhp0 - player.carrying.hp == GameDB.prop_impact_damage,
				"耐久 %d → %d" % [bhp0, player.carrying.hp if player.carrying != null else -1])
			_advance(0.1)

		# --- 47. 空挥不掉耐久（没撞上东西就没有冲量）---
		49:
			dummy.global_position = Vector3(player.global_position.x
				+ float(player.facing) * 7.0, 0.0, 0.0)
			_marks["box_hp1"] = player.carrying.hp
			player._start_attack("Light_01")
			_advance(0.9)
		50:
			var hp1: int = int(_marks["box_hp1"])
			_check("空挥一下：手上箱子耐久一点没掉（物理上没撞上东西）",
				player.carrying != null and player.carrying.hp == hp1,
				"耐久 %d → %d" % [hp1, player.carrying.hp if player.carrying != null else -1])
			_advance(0.1)

		# --- 48. 扔出去（复用 Throw「甩出去」，在它自己的判定帧出手）---
		51:
			player._start_pick()          # 手上有物 → 同键切成投掷
			_advance(0.30)
		52:
			_check("投掷：手上有物时再按拾取键切进 Throw 段",
				player.clip_name() == "Throw" and player.carrying != null,
				"clip=%s" % player.clip_name())
			_advance(0.22)                # 越过判定帧 28 → 0.467 s
		53:
			var rel_want: float = GameDB.prop_throw_release_height
			var flying: Carryable = game.carryables.props[0] \
				if game.carryables.flying_count() > 0 else null
			var rel_y: float = flying.global_position.y if flying != null else -1.0
			_check("投掷：判定帧上出手，物体进入 FLYING，手上同时清空",
				player.carrying == null and game.carryables.flying_count() >= 1,
				"carrying=%s 飞行中 %d 个" % [
					"null" if player.carrying == null else "有",
					game.carryables.flying_count()])
			_check("投掷：出手点高度 = manifest 的 hand.R 高度 %.4f m" % rel_want,
				absf(rel_y - rel_want) < 0.12,
				"实得 %.3f m" % rel_y)
			_advance(1.2)
		54:
			_check("投掷：物体在重力作用下落地（不会一直飞）",
				game.carryables.flying_count() == 0,
				"仍在飞 %d 个" % game.carryables.flying_count())
			_advance(0.1)

		# --- 49. 空手打碎地上的箱子：正好 3 下（每拳把【角色】放回原处，
		#         绝不重放箱子 —— place_at() 会把耐久刷满，"多次才坏"就验不到了）---
		55:
			_far_apart_box()              # 假人挪开，免得走进判定里
			player.reset_fighter(-0.2, 1)
			player.opponent = dummy
			_props_isolate(1, 0.65)
			_smash_hits = 0
			_advance(0.2)
		56:
			var target: Carryable = game.carryables.props[1]
			# 自我循环：一拳一次，打满就往下走。
			# **不 `_advance()`** —— 一 `_advance` 这一格就过去了，剩下的拳头没地方打。
			if target.state != Carryable.CSt.BROKEN and _smash_hits < 10:
				# 重拳自带向前的 root motion，不还原角色位置的话会一拳一拳走过去，
				# 最后站到箱子后面 —— 那不是"打不到"，是"走过了"。
				player.global_position = Vector3(-0.2, 0.0, 0.0)
				player.facing = 1
				player._start_attack("Heavy_01")
				_smash_hits += 1
				_wait = GameDB.duration("Heavy_01") + 0.12
				return
			_check("空手打碎：耐久 %d / 重拳 %d ⟹ 正好 %d 下" % [
				target.max_hp, GameDB.damage("Heavy_01"), GameDB.PROP_HITS_TO_BREAK],
				target.state == Carryable.CSt.BROKEN
				and _smash_hits == GameDB.PROP_HITS_TO_BREAK,
				"%d 下（期望 %d）" % [_smash_hits, GameDB.PROP_HITS_TO_BREAK])
			var respawn: float = GameDB.grab_hold_max * GameDB.PROP_RESPAWN_K
			_advance(respawn + 0.8)
		57:
			var target2: Carryable = game.carryables.props[1]
			_check("打碎后按「擒抱上限 × 系数」自己回来（满耐久、可再捡）",
				target2.state == Carryable.CSt.IDLE and target2.hp == target2.max_hp
				and target2.is_pickable(),
				"state=%d hp=%d/%d" % [target2.state, target2.hp, target2.max_hp])
			_advance(0.1)

		# --- 50. 纵向：跳跃期间受击体跟着骨盆抬起来（空间可以向上扩）---
		58:
			_boxes_far()                  # 所有箱子挪远，只测纵向
			_far_apart_box()
			player.reset_fighter(-0.2, 1)
			player.opponent = dummy
			_advance(0.8)                 # 等 Idle_01 淡入完成、贴地基准采样到
		59:
			var base_y: float = _hurt_pos_y()
			_check("纵向：贴地时受击体就在地面高度上（基线 %.4f m）" % \
				(GameDB.HURTBOX_HEIGHT * 0.5),
				absf(base_y - GameDB.HURTBOX_HEIGHT * 0.5) < 0.01,
				"实得 %.4f m" % base_y)
			_advance(0.1)
		60:
			player._set_state(Fighter.St.JUMP)
			player._jump_index = 0
			player._jump_air = false
			player._play(Fighter.JUMP_SEQ[0], 0.0)
			_advance(0.05)
		61:
			_jump_peak = 0.0
			_jump_watch = 130
			_advance()
		62:
			# 自我循环：不推进步骤，每帧采一次峰，采满/落地才往下走。
			if _jump_watch > 0 and player.state == Fighter.St.JUMP:
				_jump_watch -= 1
				_jump_peak = maxf(_jump_peak, _hurt_pos_y() - GameDB.HURTBOX_HEIGHT * 0.5)
				_wait = 0.0
				return
			_check("纵向：跳跃期间受击体抬起（> 1.0 m，够得着'跳起来躲下段'）",
				_jump_peak > 1.0, "峰值 %.4f m" % _jump_peak)
			_check("纵向：抬起量来自实测的骨盆弹道",
				absf(_jump_peak - Fighter.PELVIS_RISE_PEAK) < 0.15,
				"实得 %.4f m（实测峰值 %.4f m）" % [_jump_peak, Fighter.PELVIS_RISE_PEAK])
			_advance(0.9)
		63:
			_check("纵向：落地后受击体回到地面高度（不留浮空）",
				absf(_hurt_pos_y() - GameDB.HURTBOX_HEIGHT * 0.5) < 0.01,
				"实得 %.4f m" % _hurt_pos_y())
			_advance(0.2)

		# --- 51. 连按两次方向 → 起跑；跑动中按拳脚 → 跳起飞踢 ---
		64:
			_far_apart_box()
			player.reset_fighter(-0.2, 1)
			player.opponent = dummy
			# 走**真输入**：边沿识别（"上帧没按、这帧按下"）只有从 poll 进来才测得到，
			# 直接调内部函数会把要验的东西绕过去。
			player.is_player = false
			var tap := ScriptedAI.new()
			player.ai = tap
			player._set_state(Fighter.St.IDLE)
			player._play("Idle_01")
			var f_on := InputFrame.new()
			f_on.right = true
			# 第 1 帧松开 → 按下 → 松开 → 再按下（这就是"连按两次"），
			# 后面**一路按住** —— 松掉的话 RUN 会立刻转 Run_Stop（BRAKE），
			# 那测到的是"停下来了"而不是"起跑了"（第一版就栽在这 0.2 s 上）。
			var seq: Array = [InputFrame.new(), f_on, InputFrame.new(),
				InputFrame.new(), InputFrame.new(), f_on]
			for i in 60:
				seq.append(f_on)
			tap.feed(seq)
			_advance(0.25)
		65:
			_check("连按两次前进 → 进入 RUN（边沿识别生效）",
				player.state == Fighter.St.RUN,
				"状态=%s clip=%s" % [player.label_en(), player.clip_name()])
			player.ai = null
			player.is_player = true
			_marks["kick_x0"] = player.global_position.x
			_record_clips = true
			_kick_clips.clear()
			player._start_run_kick()                 # 跑动中按拳脚 = 跳踢
			_advance(2.6)
		66:
			_record_clips = false
			var x0: float = float(_marks["kick_x0"])
			_check("跑动跳踢 = 现成四段串起来（不新增动作）",
				_kick_clips.has(Fighter.JUMP_SEQ[0])
				and _kick_clips.has(Fighter.JUMP_KICK_CLIP)
				and _kick_clips.has("Jump_Land"),
				str(_kick_clips))
			_check("跑动跳踢：用的是空中重击（空中轻击够不到站地上的人）",
				_kick_clips.has(Fighter.JUMP_KICK_CLIP),
				"JUMP_KICK_CLIP=%s" % Fighter.JUMP_KICK_CLIP)
			_check("跑动跳踢：向前推进（动量 = 奔跑速度本身）",
				player.global_position.x - x0 > 1.5,
				"推进 %.3f m" % (player.global_position.x - x0))
			_advance(0.2)

		# --- 52. 收尾：所有战斗者回到可玩状态，且没有任何特效泄漏 ---
		67:
			player.reset_fighter(-1.0, 1)
			player.opponent = dummy
			dummy.reset_fighter(1.0, -1)
			dummy.opponent = player
			_clear_vfx()
			game.carryables.reset_all()
			_advance(0.3)

		68:
			_check("收尾：角色身上没有残留特效",
				Vfx.active_count(player) == 0 and Vfx.active_count(dummy) == 0,
				"角色身上 %d + %d 个" % [Vfx.active_count(player), Vfx.active_count(dummy)])
			_check("收尾：场景里没有残留特效",
				Vfx.active_count(game.vfx_root) == 0,
				"场景 %d 个" % Vfx.active_count(game.vfx_root))
			_check("收尾：双方都没拎着 / 被拎着",
				player.holding == null and player.grabbed_by == null
				and dummy.holding == null and dummy.grabbed_by == null,
				"p.holding=%s p.grabbed_by=%s d.holding=%s d.grabbed_by=%s" % [
					str(player.holding), str(player.grabbed_by),
					str(dummy.holding), str(dummy.grabbed_by)])
			_check("收尾：双方手上都没有物体",
				player.carrying == null and dummy.carrying == null,
				"p=%s d=%s" % [str(player.carrying), str(dummy.carrying)])
			_check("收尾：重开一局后所有物体回到出生点、都在地上",
				game.carryables.pickable_count() == GameDB.PROP_COUNT,
				"%d / %d" % [game.carryables.pickable_count(), GameDB.PROP_COUNT])
			_finish()


# ---------------------------------------------------------------------
# 工具
# ---------------------------------------------------------------------
func _close_in(factor: float) -> void:
	var dx := dummy.global_position.x
	player.reset_fighter(dx - GameDB.engage_distance * factor, 1)
	dummy.reset_fighter(dx, -1)
	player.opponent = dummy
	dummy.opponent = player


## 把双方摆成"相距 dist 米、面朝彼此、都站在出生点附近"的干净状态。
## 静默输入（双方都不是玩家输入源）—— 投技要的是确定性，不是随机 AI。
func _place_pair(dist: float) -> void:
	dummy.set_ai(false)
	player.set_ai(false)
	dummy.reset_fighter(0.0, -1)
	dummy.opponent = player
	player.reset_fighter(-dist, 1)
	player.opponent = dummy
	dummy.play_waiting()
	player.play_waiting()


## 把双方拉开到"任何近身招式都够不着"的距离。
## 用来隔离技能的地面冲击波 —— 否则命中爆点会混进计数里，测不出"签名帧放了什么"。
func _far_apart() -> void:
	dummy.set_ai(false)
	player.set_ai(false)
	dummy.reset_fighter(4.6, -1)
	dummy.opponent = player
	player.reset_fighter(0.0, 1)
	player.opponent = dummy
	dummy.play_waiting()
	player.play_waiting()


## 把假人挪到够不着的地方并关掉双方 AI（道具用例要的是确定性）。
##
## **刻意不碰玩家位置**：箱子是相对玩家摆的（见 `_props_isolate`），
## 一挪玩家箱子就错位，"站在箱子前面"这件事当场失效。
func _far_apart_box() -> void:
	dummy.set_ai(false)
	player.set_ai(false)
	dummy.opponent = player
	player.opponent = dummy
	dummy.global_position = Vector3(player.global_position.x + 7.0, 0.0, 0.0)
	dummy.velocity = Vector3.ZERO


## 把所有物体挪到场地之外（隔离用 —— 出生点有一个箱子就贴在身边 0.11 m，
## 不挪开的话"最近的那个"永远是它，测出来的全是另一个箱子）。
func _boxes_far() -> void:
	var mgr := game.carryables
	if mgr == null:
		return
	for i in mgr.props.size():
		mgr.props[i].place_at(Vector3(40.0 + float(i) * 2.0, 0.0, 0.0))


## 只留第 `keep` 号箱在玩家正前方 `d` 米，其余全部挪走。
func _props_isolate(keep: int, d: float) -> void:
	var mgr := game.carryables
	if mgr == null:
		return
	mgr.reset_all()
	_boxes_far()
	mgr.props[keep].place_at(
		Vector3(player.global_position.x + float(player.facing) * d, 0.0, 0.0))


## 手上箱子与手骨世界位置的距离（米）。
func _carry_gap() -> float:
	if player.carrying == null:
		return 1.0e9
	var sk := _skel()
	if sk == null:
		return 1.0e9
	var idx := sk.find_bone(Fighter.HAND_BONE)
	if idx < 0:
		return 1.0e9
	var hand: Vector3 = (sk.global_transform * sk.get_bone_global_pose(idx)).origin
	return hand.distance_to(player.carrying.global_position)


## 受击体碰撞形状的**局部 Y**（= 胶囊中心离地高度）。纵向用例读它。
func _hurt_pos_y() -> float:
	var cs := player.get_node_or_null("Hurtbox/HurtShape") as CollisionShape3D
	return cs.position.y if cs != null else -1.0


## 立刻清掉挂在 host 下的所有特效（同步移除，不等 queue_free 生效 —— 否则
## 同一个 _process 里紧接着的 active_count 会数到已经排队释放的节点）。
func _clear_vfx() -> void:
	for host in [game.vfx_root, player, dummy]:
		if host == null or not is_instance_valid(host):
			continue
		for c in host.get_children():
			if String(c.name).begins_with(Vfx.PREFIX):
				host.remove_child(c)
				c.queue_free()


func _skel() -> Skeleton3D:
	return player.skeleton()


## 受击体胶囊的当前高度（读场景树里真实生效的那个 shape，不是 GameDB 的常量）。
func _hurt_h() -> float:
	var cs := player.get_node_or_null("Hurtbox/HurtShape") as CollisionShape3D
	if cs == null:
		return -1.0
	var cap := cs.shape as CapsuleShape3D
	return cap.height if cap != null else -1.0


func _toe_z() -> float:
	var sk := _skel()
	if sk == null:
		return -99.0
	var a := sk.get_bone_global_rest(sk.find_bone("toe.L")).origin
	var b := sk.get_bone_global_rest(sk.find_bone("toe.R")).origin
	return (a.z + b.z) * 0.5


func _eye_dx() -> float:
	var sk := _skel()
	if sk == null:
		return 0.0
	var a := sk.get_bone_global_rest(sk.find_bone("eye.L")).origin
	var b := sk.get_bone_global_rest(sk.find_bone("eye.R")).origin
	return a.x * b.x


func _axis_ok() -> bool:
	return _toe_z() > 0.05 and _eye_dx() < 0.0


func _check(name: String, ok: bool, detail: String) -> void:
	_results.append([name, ok, detail])
	if not ok:
		_failed += 1
	print("%s %-34s %s" % ["[OK]  " if ok else "[FAIL]", name, detail])


func _die(reason: String) -> void:
	print("[FAIL] 冒烟测试中断：%s" % reason)
	_failed += 1
	_finish()


func _finish() -> void:
	print("")
	print("================ 冒烟测试结果 ================")
	for r in _results:
		print("%s  %s" % ["PASS" if r[1] else "FAIL", r[0]])
	print("---------------------------------------------")
	print("共 %d 项，失败 %d 项，用时 %.2f s" % [_results.size(), _failed, _elapsed])
	print("SMOKE_%s failed=%d" % ["OK" if _failed == 0 else "FAIL", _failed])
	get_tree().quit(0 if _failed == 0 else 1)
