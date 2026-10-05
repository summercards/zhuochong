extends Node
## 抓取间距对比出图：把同一套抓取姿势放在几个候选间距上各拍一张。
##
## 为什么必须出图：`Grab_Hold` 的姿势里躯干和手臂都前伸得很厉害
## （实测胸口在自己原点前 +0.66 m、手在 +1.27 m），光看数字判断不出
## "隔多远才像扣住"。三个候选：当前值 / 中间值 / 公式推出来的值。
##
## 用法:
##   godot --path . res://tools/probe_grab_shots.tscn
## 产物: docs/shots/grab_probe/*.png

const OUT_DIR := "res://docs/shots/grab_probe"

var game: Game
var player: Fighter
var dummy: Fighter


func _ready() -> void:
	game = get_parent().get_node_or_null("Main") as Game
	if game == null:
		print("SHOT_FAIL 找不到 Main")
		get_tree().quit(1)
		return
	player = game.player
	dummy = game.dummy
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT_DIR))
	await _run()
	print("SHOT_END")
	get_tree().quit(0)


func _run() -> void:
	print("清单抓取可达 = %.4f m  受击体半径 = %.4f m" % [
		GameDB.grab_reach, GameDB.HURTBOX_RADIUS])
	print("公式候选 = 可达 + 半径 = %.4f m" % (GameDB.grab_reach + GameDB.HURTBOX_RADIUS))
	print("")

	# 抓起来（用最宽松的方式），之后只改间距，让姿势保持完全一致
	_pair(GameDB.grab_reach * 0.75)
	player._start_grab()
	var guard := 0
	while player.is_holding() == false and guard < 240:
		await get_tree().physics_frame
		guard += 1
	if player.is_holding() == false:
		print("SHOT_FAIL 没抓住")
		get_tree().quit(1)
		return
	# 进到 Grab_Hold 循环的中段，姿势稳定
	await _ticks(30)

	for d in [1.0626, 1.30, 1.45, 1.60, 1.6626, 1.80, 1.95]:
		# 直接改约束值（`_sync_grabbed_position` 每帧都读它），
		# 而不是硬摆坐标 —— 硬摆会被下一帧的约束立刻改回去，拍到的还是旧间距。
		GameDB.grab_hold_distance = float(d)
		await _ticks(8)
		await _shot("间距_%.2f_m" % float(d))
		print("  已拍 间距 %.4f m（实测 %.4f）：手 x=%+.4f  被擒者近侧 x=%+.4f  重叠 %+.4f" % [
			float(d), absf(dummy.global_position.x - player.global_position.x),
			_hand_x(), _near_x(), _hand_x() - _near_x()])


## 只报数，不改位置。
func _hand_x() -> float:
	var sk := player.skeleton()
	if sk == null:
		return 0.0
	var i := sk.find_bone("hand.R")
	return (sk.global_transform * sk.get_bone_global_pose(i)).origin.x if i >= 0 else 0.0


func _near_x() -> float:
	var sk := dummy.skeleton()
	if sk == null:
		return 0.0
	var lo := 1.0e9
	for i in sk.get_bone_count():
		lo = minf(lo, (sk.global_transform * sk.get_bone_global_pose(i)).origin.x)
	return lo


func _pair(dist: float) -> void:
	dummy.set_ai(false)
	player.set_ai(false)
	dummy.reset_fighter(0.0, -1)
	dummy.opponent = player
	player.reset_fighter(-dist, 1)
	player.opponent = dummy
	dummy.play_waiting()
	player.play_waiting()


func _ticks(n: int) -> void:
	for _i in n:
		await get_tree().physics_frame


func _shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	var path := ProjectSettings.globalize_path(OUT_DIR.path_join("%s.png" % name))
	var err := img.save_png(path)
	print("  %s %s" % ["[OK]" if err == OK else "[FAIL]", path])
