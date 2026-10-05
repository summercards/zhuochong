extends Node
## 分层诊断：逐个关掉舞台图层，把每层的实际贡献**测**出来。
##
## 为什么需要它：画面偏亮时，"哪一层太亮"是猜不出来的 —— 远景幕墙、数字雨、
## 屏幕后处理都往同一个绿色上叠，人眼分不清谁占大头。把每层单独关掉再采样像素，
## 就能把责任落实到具体某一个 uniform 上。
##
## 用法:
##   godot --path . --resolution 1280x720 res://tools/shot_layers.tscn
## 产物: docs/shots/layers/*.png

const OUT_DIR := "res://docs/shots/layers"

var game: Game


func _ready() -> void:
	game = get_parent().get_node_or_null("Main") as Game
	if game == null:
		print("LAYERS_FAIL 找不到 Main")
		get_tree().quit(1)
		return
	# 定到 FIGHT 阶段、双方站定，避免开场横幅遮挡采样区
	game.force_fight()
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT_DIR))
	await _ticks(120)
	await _run()
	print("LAYERS_END")
	get_tree().quit(0)


func _run() -> void:
	var stage := game.get_node_or_null("Stage") as Node3D
	if stage == null:
		print("LAYERS_FAIL 找不到 Stage")
		return

	var rain: Array[Node3D] = []
	var backdrop: Node3D = null
	for c in stage.get_children():
		var n := c as Node3D
		if n == null:
			continue
		if n.name.begins_with("Rain"):
			rain.append(n)
		elif n.name == "Backdrop":
			backdrop = n

	var fx := game.get_node_or_null("ScreenFx") as ScreenFx

	print("  找到 雨幕=%d 幕墙=%s 后处理=%s" % [
		rain.size(), "有" if backdrop != null else "无", "有" if fx != null else "无"])

	# 全开
	_set_all(rain, true)
	if backdrop != null: backdrop.visible = true
	if fx != null: fx.set_overlay_enabled(true)
	await _shot("A_全开")

	# 只关雨幕
	_set_all(rain, false)
	await _shot("B_无雨幕")

	# 只关幕墙
	_set_all(rain, true)
	if backdrop != null: backdrop.visible = false
	await _shot("C_无幕墙")

	# 只关屏幕后处理
	if backdrop != null: backdrop.visible = true
	if fx != null: fx.set_overlay_enabled(false)
	await _shot("D_无后处理")

	# 三样都关（剩下的就是环境光/雾/地面/天空）
	_set_all(rain, false)
	if backdrop != null: backdrop.visible = false
	await _shot("E_全关")

	# 还原
	_set_all(rain, true)
	if backdrop != null: backdrop.visible = true
	if fx != null: fx.set_overlay_enabled(true)


func _set_all(nodes: Array[Node3D], on: bool) -> void:
	for n in nodes:
		n.visible = on


func _ticks(n: int) -> void:
	for _i in n:
		await get_tree().physics_frame


func _shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	var path := ProjectSettings.globalize_path(OUT_DIR.path_join("%s.png" % name))
	var err := img.save_png(path)
	print("  %s  %s" % ["[OK]  " if err == OK else "[FAIL]", path])
