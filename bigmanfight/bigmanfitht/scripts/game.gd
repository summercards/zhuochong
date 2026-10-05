class_name Game
extends Node3D
## 对局管理：回合流程 / 相机 / 命中反馈 / 重开 / 退出。
##
## 分工：
##   Fighter 只负责"我自己的状态机与判定"；
##   Hud     只负责"把状态显示出来"；
##   这里负责把两者接起来，并管**跨角色的东西**：对局阶段、相机、打击停顿同步。
##
## 关于打击停顿：Fighter 命中时会把自己停 `hitstop_frames` 帧。这里在收到
## `landed_hit` 后**再给被打的一方也打上同样的帧数** —— 停顿是双方的，
## 只停一方看起来像掉帧。

enum Phase { INTRO, FIGHT, KO, OVER }

## 开场演出序列。用资产里登记过的流程动画（E05 对战开始）。
const INTRO_SEQ := ["Battle_Start"]
## 开场演出兜底时长（秒）。正常情况由动画播完自己通知。
const INTRO_TIMEOUT := 6.0
## KO 之后多久给出胜负横幅（秒）—— 让死亡动画先播一会儿。
const KO_BANNER_DELAY := 1.1
## 相机
const CAM_Z := 7.0
const CAM_MIN_SIZE := 3.05
## 画面里角色两侧留出的余量（米）
const CAM_FRAME_MARGIN := 2.2
## 俯角（度，负 = 向下看）。
##
## **这个角度不是审美选择，是必要条件。** 正交相机水平看出去时，地面平面是
## 正对着镜头的"边"—— 投影出来只有一条 1 px 的线，地面等于不存在。实测症状：
## 出图里角色像站在虚空里，脚下没有地面。给一点俯角，地面才成为可见的面。
const CAM_PITCH_DEG := -8.0
## 想让画面竖向居中的世界高度（米）—— 取站姿胸口，这样脚和头的留白对称。
const CAM_FOCUS_Y := 0.90
const CAM_LERP := 6.5

## 相机高度由上面三个常量**推**出来，不是另写一个数：
## 让 world y = CAM_FOCUS_Y 恰好落在画面中心 ⟹ cy = CAM_FOCUS_Y + CAM_Z·tan(俯角)。
var _cam_y := 0.0

@export var player_path: NodePath
@export var dummy_path: NodePath
@export var camera_path: NodePath
@export var hud_path: NodePath
@export var stage_path: NodePath
@export var vfx_path: NodePath
@export var carryables_path: NodePath

var player: Fighter
var dummy: Fighter
var cam: Camera3D
var hud: Hud
var stage: Stage
var vfx_root: Node3D
var screen_fx: ScreenFx
var carryables: CarryableManager

# ---------------------------------------------------------------------
# 打击感（屏幕层）
# ---------------------------------------------------------------------
## 抖动的最大位移（米）。取 0.22 —— 正交视野竖向 3.05 m，
## 0.22 m ≈ 7% 的画面高度，是"明显但不晕"的量级。
const SHAKE_MAX_OFFSET := 0.22
## 抖动的最大滚转（度）。纯平移的抖动看起来像镜头在滑动；
## 掺一点滚转才像"被打到"（真实冲击会让取景器歪一下）。
const SHAKE_MAX_ROLL := 2.2
## trauma 每秒衰减
const TRAUMA_DECAY := 2.9
## 伤害 → trauma：满伤给到 0.85 而不是 1.0，留出余量给连击叠加
const TRAUMA_DAMAGE_FULL := 30.0
const TRAUMA_MAX := 0.85
## 缩放冲击的最大幅度（占 cam.size 的比例）
const PUNCH_MAX := 0.085
const PUNCH_DECAY := 5.5
## 屏幕闪色的伤害门槛（低于这个值只有场景反馈，不闪全屏）
const SCREEN_FLASH_MIN_DAMAGE := 18
const SCREEN_FLASH_TIME := 0.13
## 抓中的那一下折算成多少"等效伤害"喂进打击感管线（抓取本身不掉血）。
## 取 8 —— 低于全屏闪色门槛（18），所以抓中只有轻微抖动 + 场景脉动，
## 真正的大反馈留给"摔出去"那一下。这是刻意的：**抓是蓄，摔是放**。
const GRAB_FEEL_DAMAGE := 8

## 抖动强度 0~1。**用 trauma 模型而不是"直接设振幅"**：
## 多个命中能在 trauma 上叠加（取 max 会让连击完全没有累积感），
## 而实际振幅取 trauma² —— 二次曲线让尾段收得飞快，不会拖出"晕船感"。
var _trauma := 0.0
## 缩放冲击残余（0~1）
var _punch := 0.0
## 抖动时钟。用累积时间 + 三角函数而不是 randf()：**确定性**，
## 同一状态重放得到同一组抖动，出图和测试才可比。
var _shake_t := 0.0

var phase: int = Phase.INTRO
var winner: Fighter = null
var _phase_time := 0.0
var _intro_time := 0.0
var _last_hit_damage := 0


func _ready() -> void:
	player = get_node_or_null(player_path) as Fighter
	dummy = get_node_or_null(dummy_path) as Fighter
	cam = get_node_or_null(camera_path) as Camera3D
	hud = get_node_or_null(hud_path) as Hud
	stage = get_node_or_null(stage_path) as Stage
	vfx_root = get_node_or_null(vfx_path) as Node3D
	screen_fx = get_node_or_null("ScreenFx") as ScreenFx
	carryables = get_node_or_null(carryables_path) as CarryableManager

	assert(player != null, "Game: player_path 没指到 Fighter")
	assert(dummy != null, "Game: dummy_path 没指到 Fighter")
	assert(cam != null, "Game: camera_path 没指到 Camera3D")
	assert(hud != null, "Game: hud_path 没指到 Hud")
	assert(stage != null, "Game: stage_path 没指到 Stage")
	assert(vfx_root != null, "Game: vfx_path 没指到特效挂载点")
	assert(carryables != null, "Game: carryables_path 没指到 CarryableManager")

	player.opponent = dummy
	dummy.opponent = player
	dummy.set_ai(true)
	# 特效挂到**舞台根**而不是角色身上：命中火花的落点在世界坐标里，
	# 挂角色会让它跟着人跑，看起来像"火花黏在拳头上"。
	player.vfx_host = vfx_root
	dummy.vfx_host = vfx_root
	# 箱子管理器同样由这里注入（Fighter 不自己去 get_node 兄弟节点 —— 场景路径
	# 是场景的事）。两个角色看到的是**同一个**管理器，所以"谁捡了哪个箱子"
	# 天生只有一份事实。
	player.carryables = carryables
	dummy.carryables = carryables

	# 相机：俯角与高度由常量推出（见 CAM_PITCH_DEG 的注释 —— 水平看地面等于看不见）
	_cam_y = CAM_FOCUS_Y + CAM_Z * tan(deg_to_rad(-CAM_PITCH_DEG))
	cam.rotation = Vector3(deg_to_rad(CAM_PITCH_DEG), 0.0, 0.0)
	cam.size = CAM_MIN_SIZE

	player.landed_hit.connect(_on_landed_hit)
	dummy.landed_hit.connect(_on_landed_hit)
	player.grabbed.connect(_on_grabbed)
	dummy.grabbed.connect(_on_grabbed)
	player.defeated.connect(_on_defeated)
	dummy.defeated.connect(_on_defeated)
	# 砸箱子也走同一套屏幕反馈。箱子不是 Fighter，所以走不了 landed_hit
	# （那条路要给 victim 打 hitstop、要弹伤害数字，都需要一个 Fighter）。
	player.hit_prop.connect(_on_hit_prop)
	dummy.hit_prop.connect(_on_hit_prop)
	# 被扔出去的箱子砸到人 —— 反馈也走同一条管线。
	for p in carryables.props:
		_connect_prop(p)

	hud.bind(player, dummy)
	_start_round()


func _start_round() -> void:
	winner = null
	_last_hit_damage = 0
	# 抖动量要清零：上一回合末尾可能正处在"KO 大抖"里，
	# 不清的话新回合开场镜头是歪的（而且 cam.size 还带着上次的缩放冲击）。
	_trauma = 0.0
	_punch = 0.0
	var gap: float = GameDB.start_gap
	player.reset_fighter(-gap * 0.5, 1)
	dummy.reset_fighter(gap * 0.5, -1)
	# reset 之后 opponent 引用要保持（reset 不动它，这里只是明确一下顺序）
	player.opponent = dummy
	dummy.opponent = player

	# 箱子也复位。**必须在两个角色 reset 之后**：角色那边只清"我不再拿着它"，
	# 箱子这边负责"回到出生点、满耐久、可拾取"。顺序反了会出现
	# "角色还引用着一个已经回出生点的箱子"。
	carryables.reset_all()

	cam.size = CAM_MIN_SIZE
	_snap_camera()

	player.play_sequence(INTRO_SEQ)
	dummy.play_sequence(INTRO_SEQ)
	phase = Phase.INTRO
	_phase_time = 0.0
	_intro_time = 0.0
	hud.clear_banner()
	hud.say("准备", "READY", 0.9)


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("restart"):
		_start_round()
		return
	if event.is_action_pressed("toggle_debug"):
		hud.toggle_debug()
		return
	if event.is_action_pressed("ui_cancel"):
		get_tree().quit()


func _process(delta: float) -> void:
	if player == null:
		return
	_phase_time += delta
	_update_camera(delta)
	_tick_phase(delta)


# ---------------------------------------------------------------------
# 阶段
# ---------------------------------------------------------------------
func _tick_phase(delta: float) -> void:
	match phase:
		Phase.INTRO:
			_intro_time += delta
			var done := _intro_finished(player) and _intro_finished(dummy)
			if done or _intro_time > INTRO_TIMEOUT:
				phase = Phase.FIGHT
				_phase_time = 0.0
				hud.say("开打！", "FIGHT!", 1.0)
		Phase.FIGHT:
			pass
		Phase.KO:
			if _phase_time > KO_BANNER_DELAY:
				phase = Phase.OVER
				_phase_time = 0.0
				if winner == player:
					hud.say("你赢了", "YOU WIN", 3.0)
				else:
					hud.say("你输了", "YOU LOSE", 3.0)
		Phase.OVER:
			pass


func _intro_finished(f: Fighter) -> bool:
	# play_sequence 播完会自己回到 IDLE；没回到说明还在演
	return f.state != Fighter.St.INTRO


# ---------------------------------------------------------------------
# 命中 / 胜负
# ---------------------------------------------------------------------
## 把场上一个箱子的信号接上反馈管线。`build()` 之后调用（箱子是运行时生成的）。
func _connect_prop(p: Carryable) -> void:
	if p == null or not is_instance_valid(p):
		return
	p.struck.connect(_on_prop_struck)
	p.broke.connect(_on_prop_broke)


## 被扔出去的箱子砸在人身上。
## 伤害在 `Carryable` 那边结算（`prop_impact_damage`），这里只负责**屏幕反馈** ——
## 和 `_on_landed_hit` 一样走 `_feed_hit_feel`，所以"被箱子砸"和"被拳头打"
## 在镜头/脉动/闪色上的表现是同一条曲线的。
func _on_prop_struck(_what: Carryable, _attacker: Fighter, victim: Fighter, damage: int) -> void:
	_last_hit_damage = damage
	if hud != null and victim != null:
		hud.show_damage(victim, damage)
	_feed_hit_feel(damage, victim)


## 拳脚砸在箱子上。
func _on_hit_prop(_attacker: Fighter, _prop: Carryable, damage: int) -> void:
	_last_hit_damage = damage
	_feed_hit_feel(damage, null)


## 箱子碎了。
##
## 额外的地面冲击波**不在这里放** —— `Carryable._break()` 自己已经放过一圈了
## （它知道碎点在哪，这里不知道）。这里只补屏幕层的那一份。
func _on_prop_broke(_what: Carryable) -> void:
	if stage != null:
		stage.pulse(0.35)


## 抓中的那一下。它**没有伤害**，所以不能走 `_on_landed_hit`
## （那条路会往 HUD 打一个 "-0" 的伤害数字，也会让血条残影抖一下）。
## 这里只喂一份"轻"的屏幕反馈，让"扣住人"这件事在画面上有分量。
func _on_grabbed(attacker: Fighter, victim: Fighter, _clip: String) -> void:
	if hud != null:
		hud.say("抓住！", "GRAB!", 0.5)
	_feed_hit_feel(GRAB_FEEL_DAMAGE, victim)
	if attacker != null and attacker.state == Fighter.St.GRAB:
		stage.pulse(0.25)


func _on_landed_hit(attacker: Fighter, victim: Fighter, clip: String, damage: int) -> void:
	_last_hit_damage = damage
	# 打击停顿给双方同时打上 —— 用的是动画自己登记的 hitstop_frames
	var hs: Variant = GameDB.hitstop_frames(clip)
	var frames: int = int(hs) if hs != null else 0
	if frames > 0:
		attacker.apply_hitstop(frames)
		victim.apply_hitstop(frames)
	hud.show_damage(victim, damage)
	_feed_hit_feel(damage, victim)


## 一次命中往"屏幕层打击感"里喂多少反馈。
## **为什么统一走这一个函数**：抖动、缩放冲击、场景脉动、全屏闪色这四样
## 必须按同一个伤害数同比例缩放。如果各自散落在调用点上，很容易出现
## "重击抖得很凶但光带没反应"这种不一致 —— 一致性本身就是手感的一部分。
func _feed_hit_feel(damage: int, victim: Fighter) -> void:
	var t: float = clampf(float(damage) / TRAUMA_DAMAGE_FULL, 0.0, 1.0)

	# 1. 抖动：取 max 而不是相加 —— 相邻两帧的连续命中相加会瞬间爆表
	_trauma = minf(TRAUMA_MAX, maxf(_trauma, t * TRAUMA_MAX))
	# 2. 缩放冲击
	_punch = maxf(_punch, t)
	# 3. 场景脉动：让空间对打击有反应（这是"打的是一整个世界"的读法）
	if stage != null:
		stage.pulse(t)
	# 4. 屏幕闪色：只有够重的命中才闪，否则屏幕会一直花
	if screen_fx != null and damage >= SCREEN_FLASH_MIN_DAMAGE:
		# 颜色跟着受击闪白走：被打的人闪什么色，屏幕就闪什么色
		var col := Color(1.0, 0.95, 0.85)
		screen_fx.flash(col, clampf(t * 0.42, 0.0, 0.42), SCREEN_FLASH_TIME)
	# 5. 大命中时把对方身上再补一次闪白（小命中由 Fighter 自己闪）
	if damage >= SCREEN_FLASH_MIN_DAMAGE and victim != null:
		victim.trigger_flash(clampf(t + 0.25, 0.0, 1.0), 0.18)


func _on_defeated(who: Fighter) -> void:
	if phase == Phase.KO or phase == Phase.OVER:
		return
	winner = dummy if who == player else player
	phase = Phase.KO
	_phase_time = 0.0
	hud.say("K.O.", "K.O.", 1.2)
	if winner != null:
		winner.play_victory()


# ---------------------------------------------------------------------
# 相机
# ---------------------------------------------------------------------
func _snap_camera() -> void:
	var mid: float = (player.global_position.x + dummy.global_position.x) * 0.5
	cam.position = Vector3(_clamp_cam_x(mid, cam.size), _cam_y, CAM_Z)
	cam.rotation = Vector3(deg_to_rad(CAM_PITCH_DEG), 0.0, 0.0)


func _update_camera(delta: float) -> void:
	var a: float = player.global_position.x
	var b: float = dummy.global_position.x
	var mid: float = (a + b) * 0.5
	var dist: float = absf(a - b)

	var aspect := 16.0 / 9.0
	var vp := get_viewport().get_visible_rect().size
	if vp.y > 0.0:
		aspect = vp.x / vp.y

	# 正交尺寸 = 竖向可视范围（米）。要同时框住两人 + 余量。
	var want_size: float = maxf(CAM_MIN_SIZE, (dist + CAM_FRAME_MARGIN) / aspect)
	var t: float = 1.0 - exp(-CAM_LERP * delta)
	cam.size = lerpf(cam.size, want_size, t)
	cam.position.x = lerpf(cam.position.x, _clamp_cam_x(mid, cam.size), t)
	cam.position.y = _cam_y
	cam.position.z = CAM_Z

	_apply_hit_feel(delta)


## 把抖动/缩放冲击叠到相机上。
##
## **必须在 lerp 之后单独叠加**：抖动是"瞬时的额外位移"，
## 如果把它写回 cam.position 再参与下一帧的 lerp，平滑会把抖动吃掉，
## 看起来像镜头在缓缓地飘，而不是被揍了一下。
func _apply_hit_feel(delta: float) -> void:
	_shake_t += delta
	_trauma = maxf(0.0, _trauma - TRAUMA_DECAY * delta)
	_punch = maxf(0.0, _punch - PUNCH_DECAY * delta)

	# 缩放冲击：把正交尺寸压小（往里顶）
	if _punch > 0.0:
		cam.size *= 1.0 - _punch * PUNCH_MAX

	if _trauma <= 0.0:
		cam.rotation = Vector3(deg_to_rad(CAM_PITCH_DEG), 0.0, 0.0)
		return

	# trauma²：二次曲线让尾段收得飞快（一次曲线会在末尾拖出"晕船感"）
	var amp: float = _trauma * _trauma
	var wt := _shake_t
	# 三个不同频率的正弦合成 —— 比单一正弦更像噪声，又完全确定性
	var ox: float = (sin(wt * 41.3) + 0.5 * sin(wt * 73.7)) * amp * SHAKE_MAX_OFFSET
	var oy: float = (sin(wt * 57.1) + 0.5 * sin(wt * 31.9)) * amp * SHAKE_MAX_OFFSET * 0.7
	var roll: float = sin(wt * 47.5) * amp * SHAKE_MAX_ROLL

	cam.position.x += ox
	cam.position.y += oy
	cam.rotation = Vector3(deg_to_rad(CAM_PITCH_DEG), 0.0, deg_to_rad(roll))


## 给测试/调试：当前抖动与冲击的量
func hit_feel() -> String:
	return "trauma=%.3f punch=%.3f" % [_trauma, _punch]


## 相机横向不越出舞台：别让画面里出现舞台外的空地。
func _clamp_cam_x(mid: float, size: float) -> float:
	var aspect := 16.0 / 9.0
	var vp := get_viewport().get_visible_rect().size
	if vp.y > 0.0:
		aspect = vp.x / vp.y
	var half_vis: float = size * aspect * 0.5
	var limit: float = maxf(0.0, GameDB.STAGE_HALF_WIDTH + 1.2 - half_vis)
	return clampf(mid, -limit, limit)


# ---------------------------------------------------------------------
# 给外部（调试/自动化）用
# ---------------------------------------------------------------------
func force_fight() -> void:
	phase = Phase.FIGHT
	hud.clear_banner()


func state_text() -> String:
	return "phase=%s p_hp=%d d_hp=%d dist=%.3f" % [
		Phase.keys()[phase], player.hp, dummy.hp,
		absf(player.global_position.x - dummy.global_position.x)]
