extends Node
## 出图工具：真窗口跑一局，把关键画面存成 PNG。
##
## 为什么必须开窗口：headless 用的是空渲染器，`get_viewport().get_texture()`
## 拿到的是空图 —— 想"亲眼看"就只能真渲染。这里按**物理帧**推进（60 Hz 定步），
## 每一步都等到帧画完再抓，所以拿到的是确定的那一帧。
##
## 用法:
##   godot --path . res://tools/shot.tscn
## 产物: docs/shots/*.png

const OUT_DIR := "res://docs/shots"

var game: Game
var player: Fighter
var dummy: Fighter


## 只按固定输入、不做任何决策的"姿势支架"，用来把某一方定在某个姿态上截图。
class Hold extends DummyAI:
	var hold_guard := false
	var hold_crouch := false
	func poll(_me: Node3D, _opponent: Node3D, _delta: float) -> InputFrame:
		var f := InputFrame.new()
		f.guard = hold_guard
		f.crouch = hold_crouch
		return f


func _ready() -> void:
	game = get_parent().get_node_or_null("Main") as Game
	if game == null:
		print("SHOT_FAIL 找不到 Main")
		get_tree().quit(1)
		return
	player = game.player
	dummy = game.dummy
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT_DIR))
	print("SHOT_BEGIN 产物目录 %s" % ProjectSettings.globalize_path(OUT_DIR))
	await _run()
	print("SHOT_END")
	get_tree().quit(0)


func _run() -> void:
	# 先把相机的实际参数打出来 —— 构图靠它，不能靠猜。
	print("  相机 size=%.3f pos=%s rot=%.1f° 视口=%s" % [
		game.cam.size, str(game.cam.position), game.cam.rotation_degrees.x,
		str(get_viewport().get_visible_rect().size)])

	# --- 01 开场对站（等 E05 开战 1.6 s 演完）---
	await _ticks(130)
	await _shot("01_对站_开场后")

	# --- 02 举防（1P 举防，1.2 s 循环防）---
	# 用 Hold 输入源驱动**玩家**跑状态机（headless 没键盘），比直接塞 clip 真实。
	_detach_ai()
	var hg := Hold.new()
	hg.hold_guard = true
	_reset_pair()
	player.ai = hg
	player.is_player = false
	await _ticks(80)
	await _shot("02_举防_循环防")
	_detach_ai()

	# --- 03 轻拳命中瞬间（B01 命中帧 6）---
	# 往后挪 3 帧再拍：命中特效的寿命是 0.15 s（9 帧），
	# 判帧当帧（progress≈0.11）拍下来只有一个亮点，看不出"环"。
	# 第 9 帧时 progress≈0.33，核心 + 扩散环都在，才是它该有的样子。
	_reset_pair()
	player._start_attack("Light_01")
	await _ticks(9)
	await _shot("03_轻拳_命中帧")

	# --- 04 重拳命中瞬间（B04 命中帧 26）---
	# 同理往后挪 3 帧。重击特效更大（power 2.0 → 尺寸 ×1.42、寿命 ×1.28）。
	_reset_pair()
	player._start_attack("Heavy_01")
	await _ticks(29)
	await _shot("04_重拳_命中帧")

	# --- 05 下蹲（受击体变矮的姿态）---
	_reset_pair()
	var hc := Hold.new()
	hc.hold_crouch = true
	player.ai = hc
	player.is_player = false
	await _ticks(90)
	await _shot("05_下蹲_蹲姿待机")
	_detach_ai()

	# --- 06 大招旋拳（C11 命中帧 46）---
	_reset_pair()
	player._start_attack("Skill_03")
	await _ticks(47)
	await _shot("06_大招_旋转重拳")
	await _ticks(40)

	# --- 07 KO：假人剩 1 血，被重拳打死 ---
	_reset_pair()
	dummy.hp = 1
	dummy.hp_changed.emit(dummy.hp, dummy.max_hp)
	player._start_attack("Heavy_01")
	await _ticks(140)
	await _shot("07_KO_胜利演出")

	# --- 08 调试面板（F1 → hud.toggle_debug）---
	game.hud.toggle_debug()
	await _ticks(10)
	await _shot("08_调试面板")
	game.hud.toggle_debug()

	# --- 09 地面冲击波（砸地类技能的视觉）---
	# 直接生成一个特效来拍：这里要验的是**特效本身长什么样**，
	# 不是"什么条件会触发它"，所以不走技能流程，避免时序噪声。
	#
	# 拍在 progress ≈ 0.33：环已经推开但还很亮。太早环太小（屏幕上只是条短线），
	# 太晚已经淡掉了。
	_reset_pair()
	var mid := Vector3(player.global_position.x + 1.1, 0.0, 0.0)
	Vfx.shockwave(game.vfx_root, mid, Vfx.SHOCK_RADIUS, 0.85, Vfx.COLOR_SHOCK,
		sin(deg_to_rad(absf(Game.CAM_PITCH_DEG))))
	await _ticks(17)
	await _shot("09_地面冲击波")

	# 等它跑完，别把残留带进下一张
	await _ticks(70)

	# --- 10 蓄力光环（持续型特效）---
	# 走**真技能流程**（_start_special("Charge") 里自己起光环），
	# 不再手动 Vfx.aura —— 出图要验的是"技能键真的挂上了光环"，不是"光环好不好看"。
	_reset_pair()
	player._start_special("Charge")
	await _ticks(24)
	await _shot("10_蓄力光环")
	await _ticks(120)

	# --- 11 抓取：判定帧上扣住对手（Grab_Start 判定帧 28/60 ≈ 0.47 s）---
	# 拍在捕获后第 5 帧：hitstop 刚过，抓取火花已经推开（太早只有一个亮点）。
	_reset_pair()
	player._start_grab()
	await _ticks_until(func(): return player.is_holding(), 180)
	await _ticks(5)
	await _shot("11_抓取_扣住对手")

	# --- 12 擒抱：抓住不放（Grab_Hold 循环，实测上限 2.00 s）---
	await _ticks(45)
	await _shot("12_擒抱_GrabHold循环")

	# --- 13 投掷结算：对手被击飞 + 落点地面冲击波 ---
	player._begin_throw()
	await _ticks_until(func(): return player.throws_done >= 1, 180)
	await _ticks(9)
	await _shot("13_投掷_被投者击飞")
	await _ticks(90)

	# --- 14 大招：三段连续，全程光环；中段到签名帧放地面冲击波 ---
	# 站位刻意压到 0.8 m（大招中段 reach 0.54 m）—— 让三段真的打在对手身上，
	# 出图才是"必杀连段"而不是"对着空气挥拳"。
	_reset_pair(0.8)
	player._start_ultimate()
	await _ticks_until(func(): return Vfx.active_count(game.vfx_root) >= 2, 300)
	await _ticks(6)
	await _shot("14_大招_中段冲击波")
	await _ticks(200)
	await _shot("15_大招_收尾光环")


# ---------------------------------------------------------------------
# 工具
# ---------------------------------------------------------------------
## 等 n 个**物理帧**（60 Hz 定步）—— 不跟渲染帧率挂钩。
func _ticks(n: int) -> void:
	for _i in n:
		await get_tree().physics_frame


## 一直等到条件成立（或到上限）。抓取/投掷这类"判帧才发生"的时刻
## 不能用固定帧数硬等 —— hitstop 会把动画帧和物理帧错开，固定帧数会拍偏。
func _ticks_until(cond: Callable, max_ticks: int) -> int:
	var n := 0
	while n < max_ticks:
		if bool(cond.call()):
			return n
		await get_tree().physics_frame
		n += 1
	push_warning("[shot] 条件 %d 帧内没成立 —— 这张图拍到的可能是旧状态" % max_ticks)
	return n


## 等帧画完再抓，否则拿到的是上一帧甚至空图。
func _shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	# 走**绝对路径**写盘：运行中的项目 res:// 只有工程目录才有意义，
	# 导出版本里根本不可写。globalize 之后两端行为一致。
	var path := ProjectSettings.globalize_path(OUT_DIR.path_join("%s.png" % name))
	var err := img.save_png(path)
	print("  %s  %s  %dx%d" % ["[OK]  " if err == OK else "[FAIL]", path,
		img.get_width(), img.get_height()])


## 成对重置。
##
## 只重置一方是个陷阱：另一方如果正处在 `St.ATTACK`，**已经排进 `_pending_hits`
## 的那一击仍然会打出去** —— 出图时表现为"明明没人出招，1P 却掉了 20 血还被击倒"。
## 截图工具必须把双方都摆干净，否则留下的不是游戏状态而是上一次的残影。
##
## `dist < 0` 用默认交战距离；正数则按指定间距摆（大招那种要"打得中"的镜头用）。
##
## 还要**把 phase 复位成 FIGHT 并清掉 HUD 横幅**：第 07 张拍完 KO 之后 phase 停在
## OVER，"你赢了"横幅会一直挂在画面上（它有 3 s 的显示计时），
## 于是第 08 张往后每一张都顶着一条"你赢了" —— 出图里出现过，很难不注意到。
func _reset_pair(dist := -1.0) -> void:
	_detach_ai()
	game.force_fight()
	var gap: float = dist if dist > 0.0 else GameDB.engage_distance * 0.9
	player.reset_fighter(-gap, 1)
	dummy.reset_fighter(0.0, -1)
	player.opponent = dummy
	dummy.opponent = player
	player.state = Fighter.St.IDLE
	dummy.state = Fighter.St.IDLE
	player._play("Idle_01")
	dummy._play("Idle_01")


## 卸掉双方的自定义输入源，让玩家回到键盘控制、假人回到"无输入"。
func _detach_ai() -> void:
	player.ai = null
	player.is_player = true
	dummy.ai = null
	dummy.is_player = false
