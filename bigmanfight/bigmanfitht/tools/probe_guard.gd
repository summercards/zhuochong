extends Node
## 定点探针：只查一件事 —— "举防"能不能从 Guard_Start 进到循环防。
##
## 为什么要单独探：状态机在 IDLE 里**每一物理帧**都会被 `_try_common` 拦一次，
## 只要 guard 一直为真，理论上第一帧就应该进 GUARD。这里逐物理帧打点，
## 把"状态 / 清单名 / 引擎名 / 引擎播放位置 / 是否被 hitstop 冻住"全摊开。

const TICK_MOD := 6          # 每 6 物理帧打一行（≈0.1 s）
const DURATION := 2.0        # 观察 2 秒

var game: Game
var player: Fighter
var dummy: Fighter

var _frames := 0
var _max_frames := 0
var _log: Array[String] = []


class HoldGuardAI extends DummyAI:
	func poll(_me: Node3D, _opponent: Node3D, _delta: float) -> InputFrame:
		var f := InputFrame.new()
		f.guard = true
		return f


func _ready() -> void:
	game = get_parent().get_node_or_null("Main") as Game
	if game == null:
		print("PROBE_FAIL 找不到 Main")
		get_tree().quit(1)
		return
	player = game.player
	dummy = game.dummy
	_max_frames = int(DURATION * Engine.physics_ticks_per_second)

	# 摆位：贴到交战距离上，假人闭嘴不动
	dummy.set_ai(false)
	var dx := dummy.global_position.x
	player.reset_fighter(dx - GameDB.engage_distance * 0.9, 1)
	dummy.reset_fighter(dx, -1)
	player.opponent = dummy
	dummy.opponent = player

	# 真输入源：每帧都返回 guard=true
	player.ai = HoldGuardAI.new()
	player.is_player = false
	player._set_state(Fighter.St.IDLE)
	player._play("Idle_01")

	print("PROBE_BEGIN Guard_Start.duration=%.3f s  Guard_Loop.duration=%.3f s" % [
		GameDB.duration("Guard_Start"), GameDB.duration("Guard_Loop")])
	_line("帧  状态        清单名           引擎名           位置/时长      冻结")
	print("PHYS_DELTA %.4f" % (1.0 / float(Engine.physics_ticks_per_second)))


func _physics_process(_delta: float) -> void:
	_frames += 1
	if _frames % TICK_MOD == 0:
		_line("%4d  %-10s  %-16s  %-16s  %.3f/%.3f  %s" % [
			_frames, player.label_en(), player.clip_name(), player.engine_anim(),
			player.anim_position_s(), GameDB.duration(player.clip_name()),
			"是" if player.anim_frozen() else "否"])
	if _frames >= _max_frames:
		_finish()


func _line(s: String) -> void:
	_log.append(s)
	print(s)


func _finish() -> void:
	print("---------------------------------------------")
	print("末帧：状态=%s 清单名=%s 引擎名=%s 位置=%.3f" % [
		player.label_en(), player.clip_name(), player.engine_anim(),
		player.anim_position_s()])
	var ok := player.engine_anim() == "Guard"
	var seen: Array[String] = []
	for l in _log:
		if l.find("GUARD") >= 0 and not seen.has("GUARD"):
			seen.append("GUARD")
	print("PROBE_%s 进到循环防=%s（引擎名 %s）" % [
		"OK" if ok else "FAIL", str(ok), player.engine_anim()])
	get_tree().quit(0 if ok else 1)
