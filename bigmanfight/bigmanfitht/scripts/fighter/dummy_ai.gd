class_name DummyAI
extends RefCounted
## 假人对手：会走过来、挥拳、偶尔举防。
##
## 目的不是"打得好"，是**给模板一个能还手的靶子**，好验证受击/防御/击倒流程。

## 进到这个距离才开始出招（米）。
## **不是拍的值** —— 取 GameDB 的交战距离，由实测的轻/重拳可达距离推出
## （见 game_db.gd §4/运行时推算）。字面兜底 1.2 只在数据缺失时用到。
const ATTACK_RANGE_FALLBACK := 1.2
## 退到比这更近就往后让（米）—— 避免贴脸互推。
const TOO_CLOSE_RATIO := 0.45
## 招式之间的最小间隔（秒），随机浮动。
const ATTACK_COOLDOWN := [0.55, 1.30]
## 每帧举起防御的概率（很低，偶尔为之）。
const GUARD_CHANCE := 0.004
## 防御最多持续（秒）。
const GUARD_MAX_TIME := 0.9

## --- 投技 ---
## 在"贴得够近"时改用抓技而不是拳脚的概率。
##
## 门槛是"抓取可达距离 × 这个系数"：抓取手伸得比拳脚远（实测 1.36 m vs
## 重拳 0.97 m），如果不额外收一收，假人会在中距离乱抓，看起来像在捞空气。
const GRAB_CHANCE := 0.10
const GRAB_RANGE_K := 0.70
## 被抓住之后每帧按挣脱键的概率。
##
## 定这个数的算法：`GRAB_MASH_BREAK` 次按键要在 `Grab_Hold` 一圈（2.0 s = 120 帧）
## 内按完才算"手快"，所以每帧 p 要满足 120·p ≈ 6 ⟹ p ≈ 0.05。
## 取 0.055 让假人**略快于临界**：玩家抓住之后不动手就会看着它跑掉 ——
## 这正是我们要展示的机制，不是缺陷。
const MASH_CHANCE := 0.055


func attack_range() -> float:
	var r := GameDB.engage_distance
	return r if r > 0.0 else ATTACK_RANGE_FALLBACK

enum Mode { APPROACH, STRIKE, GUARD, RECOVER }

var mode: int = Mode.APPROACH
var _mode_time := 0.0
var _cooldown := 0.6
var _rng := RandomNumberGenerator.new()


func _init(seed_value: int = 20261004) -> void:
	_rng.seed = seed_value


func poll(me: Node3D, opponent: Node3D, delta: float) -> InputFrame:
	var f := InputFrame.new()
	var dist := absf(opponent.global_position.x - me.global_position.x)
	var rng_range := attack_range()

	# 被抓住的时候只有一个念头：挣脱。**放在最前面**——
	# 否则下面那些"靠近/出招"的分支会在被擒期间发出方向键，
	# 虽然状态机不接受，但会让"挣脱计数"永远为 0（真踩过）。
	if me is Fighter and (me as Fighter).state == Fighter.St.GRABBED:
		if _rng.randf() < MASH_CHANCE:
			# 拳脚和抓技都算挣脱键，跟真人一样随便拍
			if _rng.randf() < 0.5:
				f.light = true
			else:
				f.grab = true
		return f

	_cooldown = maxf(0.0, _cooldown - delta)
	_mode_time -= delta

	match mode:
		Mode.APPROACH:
			if dist > rng_range:
				# 朝对手走
				if opponent.global_position.x > me.global_position.x:
					f.right = true
				else:
					f.left = true
			else:
				mode = Mode.STRIKE
				_mode_time = 0.0
			if _rng.randf() < GUARD_CHANCE:
				mode = Mode.GUARD
				_mode_time = _rng.randf_range(0.3, GUARD_MAX_TIME)

		Mode.STRIKE:
			if dist > rng_range * 1.25:
				mode = Mode.APPROACH
			elif dist < rng_range * TOO_CLOSE_RATIO:
				# 太贴了，退半步再打
				if opponent.global_position.x > me.global_position.x:
					f.left = true
				else:
					f.right = true
			elif _cooldown <= 0.0:
				# 抓到人的距离上，有一定概率改用抓技（拳脚之外的第二条路）
				var grab_range := GameDB.grab_reach * GRAB_RANGE_K
				if grab_range > 0.0 and dist < grab_range and _rng.randf() < GRAB_CHANCE:
					f.grab = true
					_cooldown = _rng.randf_range(ATTACK_COOLDOWN[0], ATTACK_COOLDOWN[1]) * 1.6
				else:
					# 随机挑一招
					var roll := _rng.randf()
					if roll < 0.45:
						f.light = true
					elif roll < 0.72:
						f.heavy = true
					elif roll < 0.86:
						f.low = true
					else:
						f.upper = true
					_cooldown = _rng.randf_range(ATTACK_COOLDOWN[0], ATTACK_COOLDOWN[1])

		Mode.GUARD:
			f.guard = true
			if _mode_time <= 0.0:
				mode = Mode.RECOVER
				_mode_time = 0.25

		Mode.RECOVER:
			if _mode_time <= 0.0:
				mode = Mode.APPROACH

	return f


func reset() -> void:
	mode = Mode.APPROACH
	_mode_time = 0.0
	_cooldown = 0.6
