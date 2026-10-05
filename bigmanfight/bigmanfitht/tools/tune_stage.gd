extends Node
## 亮度阶梯：从"全关 + 线性色调映射"开始，一级一级打开，把每个环节的乘数钉死。
##
## 为什么必须这么做（这就是写这个工具的理由）：
## 我一开始是"改一个数 → 跑一次 → 对比上一次的数字"，结果数据一直被误读 ——
## 因为每次对比的两组其实同时变了好几个东西（雨幕、辉光、色调映射、雾），
## 于是"幕墙从 171 降到 134 是辉光的功劳"这种结论根本站不住脚。
##
## 正确做法是**控制变量**：先建立一个已知的基准（所有后处理关掉、色调映射切线性），
## 然后每次只加一个环节。每一步的增加量就是那个环节的真实乘数，可以直接和
## 公式算出来的期望值对账 —— 对不上就说明公式里漏了一项，而不是"感觉太亮"。
##
## 用法:
##   godot --path . --resolution 1280x720 res://tools/tune_stage.tscn

## 采样区：用**归一化坐标**（0~1）。
##
## 上一版是硬编码 720p 的像素坐标，结果在 640x360 下跑时 get_pixel 越界，
## 错误刷屏把进程拖死 —— 采样区必须跟着分辨率走。
##   上半屏 = 远景区（幕墙可见的那一段）
##   地平线带 = y ∈ [0.417, 0.486]，实测地平线辉光带落在这一行
##   下半屏 = 近景地面
const PATCH_TOP_N := Rect2(0.008, 0.014, 0.195, 0.319)
const PATCH_HORIZON_N := Rect2(0.008, 0.417, 0.195, 0.069)
const PATCH_BOT_N := Rect2(0.008, 0.694, 0.195, 0.167)
## 竖直剖面用列（归一化 x）
const PROBE_COL_XN := 0.031

var game: Game
var env: Environment
var backdrop: MeshInstance3D
var floor_mi: MeshInstance3D
var rain: Array[Node3D] = []
var fx: ScreenFx
## 保留原始设置，跑完还原
var _keep := {}


func _ready() -> void:
	game = get_parent().get_node_or_null("Main") as Game
	if game == null:
		print("TUNE_FAIL 找不到 Main")
		get_tree().quit(1)
		return

	var we := game.get_node_or_null("Stage/WorldEnvironment") as WorldEnvironment
	if we == null:
		print("TUNE_FAIL 找不到 WorldEnvironment")
		get_tree().quit(1)
		return
	env = we.environment

	var stage := game.get_node_or_null("Stage") as Node3D
	backdrop = stage.get_node_or_null("Backdrop") as MeshInstance3D
	floor_mi = stage.get_node_or_null("Floor") as MeshInstance3D
	fx = game.get_node_or_null("ScreenFx") as ScreenFx
	for c in stage.get_children():
		if c.name.begins_with("Rain"):
			rain.append(c)

	_keep = {
		"fog": env.fog_enabled,
		"glow": env.glow_enabled,
		"tonemap": env.tonemap_mode,
		"exposure": env.tonemap_exposure,
		"ambient": env.ambient_light_energy,
	}

	game.force_fight()
	# **把 HUD 整个藏掉。** 血条是橙色的，正好落在"上半屏"采样框里，
	# 而且它会随时间脉动 —— 于是扫描数据里混进一个会自己变的非场景成分，
	# 表现为"改参数完全没反应"（实测：gain 扫了 60 倍，读数三次一模一样）。
	# 这个工具只看 3D 场景，HUD 不属于被调的对象。
	if game.hud != null:
		game.hud.visible = false
	await _ticks(120)

	print("TUNE_BEGIN")
	print("  图层: 雨幕=%d 幕墙=%s 地面=%s 后处理=%s" % [
		rain.size(), "有" if backdrop != null else "无",
		"有" if floor_mi != null else "无", "有" if fx != null else "无"])
	# 自检：着色器编译失败时 uniform 会全部取不到值，扫描数据会变成垃圾。
	# 所以先确认关键 uniform 真的存在，别拿"编译失败的材质"跑一整轮扫描。
	_check_uniforms()

	# 先全部关掉，建立基准
	_set_rain(false)
	if backdrop != null: backdrop.visible = false
	if fx != null: fx.set_overlay_enabled(false)
	env.fog_enabled = false
	env.glow_enabled = false
	env.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	env.ambient_light_energy = 0.0
	await _step("L0 基准：全关 + 线性 + 无环境光")

	env.ambient_light_energy = float(_keep["ambient"])
	await _step("L1 + 环境光")

	if backdrop != null:
		backdrop.visible = true
	await _step("L2 + 幕墙（线性/无辉光/无雾）")

	env.tonemap_mode = int(_keep["tonemap"])
	env.glow_enabled = true
	if fx != null:
		fx.set_overlay_enabled(true)
	_set_rain(true)
	await _step("L3 + FILMIC + 辉光 + 后处理 + 雨（= 完整画面）")

	env.glow_enabled = false
	await _step("L4 再关辉光（= 完整画面但无辉光）")
	env.glow_enabled = true

	# ---------------------------------------------------------------------
	# 传输函数标定：把幕墙简化成"只剩 haze 一项"，扫 gain，
	# 直接量出"着色器里的线性值 → PNG 里的 sRGB 值"这条曲线。
	#
	# 为什么必须单独做这一步：
	# 上一轮我拿手算值（0.013 线性）和实测值（sRGB 110）对账，差了 13 倍，
	# 于是开始怀疑公式漏项。其实真正的原因是**引擎加载的是旧的着色器** ——
	# `.gdshader` 也有导入步骤，改完不跑 --import 就不生效，
	# 于是 `get_shader_parameter("gain")` 直接返回 Nil（这个 uniform 在旧版里不存在）。
	# 教训：改着色器之后必须重新 --import，否则所有扫描数据都是错的。
	# ---------------------------------------------------------------------
	if backdrop != null:
		var mat := backdrop.material_override as ShaderMaterial
		var _kp := {}
		for k in ["conduit_gain", "grid_gain", "block_gain", "glow_gain", "haze_height", "gain"]:
			_kp[k] = mat.get_shader_parameter(k)
		mat.set_shader_parameter("conduit_gain", 0.0)
		mat.set_shader_parameter("grid_gain", 0.0)
		mat.set_shader_parameter("block_gain", 0.0)
		mat.set_shader_parameter("glow_gain", 0.0)
		# haze_height 拉大 → sqrt(above/height) ≈ 0 → col 恒等于 haze_color（纯均匀色）
		mat.set_shader_parameter("haze_height", 1000.0)
		print("  --- 传输函数标定：只留 haze（均匀色），扫 gain ---")
		for g in [1.0, 0.25, 0.0625, 0.01563]:
			mat.set_shader_parameter("gain", g)
			await _step("T gain=%.5f" % g)
		for k in _kp:
			if _kp[k] != null:
				mat.set_shader_parameter(k, _kp[k])

	# ---------------------------------------------------------------------
	# 定标：分项负责"形状"，gain / glow_gain 负责"亮度"，用实测扫出来。
	# 目标（按 sRGB 读）：
	#   上半屏（远景区底色）绿 ≈ 30~60  —— 暗，但要有东西可看
	#   地平线带       绿 ≈ 150~235 —— 一条明确的高光线
	# ---------------------------------------------------------------------
	if backdrop != null:
		var mat2 := backdrop.material_override as ShaderMaterial
		var keep2: Variant = mat2.get_shader_parameter("glow_gain")
		print("  --- glow_gain 扫描（gain 固定 %.2f）---" % mat2.get_shader_parameter("gain"))
		for b in [0.55, 1.0, 1.4, 2.2]:
			mat2.set_shader_parameter("glow_gain", b)
			await _step("B glow_gain=%.2f" % b)
		if keep2 != null:
			mat2.set_shader_parameter("glow_gain", keep2)

	_restore()
	print("TUNE_END")
	get_tree().quit(0)


func _restore() -> void:
	env.fog_enabled = bool(_keep["fog"])
	env.glow_enabled = bool(_keep["glow"])
	env.tonemap_mode = int(_keep["tonemap"])
	env.tonemap_exposure = float(_keep["exposure"])
	env.ambient_light_energy = float(_keep["ambient"])
	_set_rain(true)
	if backdrop != null: backdrop.visible = true
	if fx != null: fx.set_overlay_enabled(true)
	if game.hud != null: game.hud.visible = true


func _set_rain(on: bool) -> void:
	for n in rain:
		n.visible = on


## 自检：幕墙/地面/雨幕着色器是否真的编译成功、关键 uniform 是否齐全。
##
## 为什么必须查这一下：着色器一旦编译失败（比如多打一个 `}`），Godot 会给出一屏
## 报错，但材质**不会崩** —— 它只是把所有 uniform 都变成取不到值（Nil）。
## 于是 `set_shader_parameter` 静默失效，整轮扫描的每个数字都是垃圾，
## 而表面上看"跑通了、有输出"。这件事真实发生过，浪费了整整两轮扫描。
##
## 注意不能用 get_shader_parameter 判断 —— 它只反映"材质上被显式设过什么"，
## 没设过的 uniform 一律返回 null，跟着色器是否正常无关（第一版自检就是这么写错的，
## 把一个正常工作的着色器报成了失败）。要看 **shader.get_shader_uniform_list()**。
func _check_uniforms() -> void:
	var checks := {
		"Backdrop": [backdrop, ["gain", "glow_gain", "haze_color", "conduit_gain", "grid_gain", "block_gain"]],
		"Floor": [floor_mi, ["view_sin", "cell_size", "line_color"]],
		"Rain": [rain[0] if rain.size() > 0 else null, ["tail_gain", "density", "columns", "rows"]],
	}
	var bad := PackedStringArray()
	var ok := 0
	for tag in checks:
		var pair: Array = checks[tag]
		var mi := pair[0] as MeshInstance3D
		if mi == null:
			continue
		var mat := mi.material_override as ShaderMaterial
		if mat == null or mat.shader == null:
			bad.append("%s(无材质)" % tag)
			continue
		var names := PackedStringArray()
		for u in mat.shader.get_shader_uniform_list(true):
			names.append(String(u["name"]))
		if names.is_empty():
			bad.append("%s(着色器列表为空→编译失败)" % tag)
			continue
		for k in pair[1]:
			if names.has(k):
				ok += 1
			else:
				bad.append("%s.%s" % [tag, k])

	if bad.is_empty():
		print("  [自检] 着色器 uniform 齐全（%d 项）" % ok)
	else:
		print("  [自检-失败] %s" % ", ".join(bad))
		print("           ↑ 着色器很可能编译失败，后面所有数字都不可信")


func _step(label: String) -> void:
	await _ticks(3)
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	print("  %-34s 上半屏=%s 地平线带=%s 下半屏=%s" % [
		label, _patch_mean(img, PATCH_TOP_N),
		_patch_mean(img, PATCH_HORIZON_N), _patch_mean(img, PATCH_BOT_N)])


## 归一化矩形 → 像素均值（3x3 步进，够代表均值又快）
func _patch_mean(img: Image, rn: Rect2) -> String:
	var w := img.get_width()
	var h := img.get_height()
	var x0 := int(rn.position.x * w)
	var x1 := mini(w, int((rn.position.x + rn.size.x) * w))
	var y0 := int(rn.position.y * h)
	var y1 := mini(h, int((rn.position.y + rn.size.y) * h))
	var step := maxi(1, (x1 - x0) / 90)
	var sr := 0
	var sg := 0
	var sb := 0
	var n := 0
	var y := y0
	while y < y1:
		var x := x0
		while x < x1:
			var c := img.get_pixel(x, y)
			sr += int(c.r * 255.0)
			sg += int(c.g * 255.0)
			sb += int(c.b * 255.0)
			n += 1
			x += step
		y += step
	if n == 0:
		return "(--,--,--)"
	return "(%3d,%3d,%3d)" % [sr / n, sg / n, sb / n]


func _ticks(n: int) -> void:
	for _i in n:
		await get_tree().physics_frame
