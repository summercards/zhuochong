extends Node3D
## =====================================================================
## 巡礼专用舞台 —— 为**透视环绕机位**标定的「黑客帝国式虚拟空间」
## =====================================================================
##
## 由 `tools/reel.gd` 用 `preload(...).new()` 实例化，**刻意不声明 class_name**：
## class_name 要靠 `.godot/global_script_class_cache.cfg` 才能按名字解析，
## 而那个缓存只有编辑器扫过才更新 —— 新脚本直接跑会加载失败，
## 表现是"窗口开着但什么都不做"。
##
## 为什么不直接用 `scripts/world/stage.gd`：
##
##   那个舞台是给游戏本体服务的 —— 正交相机、固定 8° 俯角、相机永远在 +Z。
##   它的雨幕是 68 × 16 m 的大板，字符密度按"1 m ≡ 234 px"的世界比例定死；
##   网格地面靠 `1 / sin(俯角)` 这个**常数**补偿 z 向压缩。
##
##   一旦把相机换成透视 + 环绕，这两条前提全没了：
##     · 雨幕字符在近处 3 px、远处 0.4 px —— 缩成亚像素后糊成一片均匀的绿；
##     · 网格的固定补偿把近处横线拉成占满屏幕的粗亮带。
##
## 这一套的三条改动：
##
##   1. **地面**用 `reel_floor.gdshader`：线宽定义在**屏幕空间**（`fwidth` 求导），
##      任何距离、任何角度下都是 1~2 px。
##
##   2. **幕墙与雨幕都"面向相机"（yaw billboard）**，并且按**相机距离**摆放。
##      这样环绕时背景永远正对镜头，不会绕出板子边缘，也不会出现"板子平行于视线"的退化。
##
##   3. **幕墙的位置由"想装下多高的内容"反解**（不是写死距离）：
##         可见高度 = 2 · (相机距离 + 幕墙距离) · tan(fov/2) = BACKDROP_VISIBLE_M
##       ⟹ 幕墙距离 = BACKDROP_VISIBLE_M / (2·tan(fov/2)) − 相机距离
##      于是**无论什么景别，幕墙在画面里的大小恒定** —— 换机位时量别不变。
##
## 光也挂在"相机方位"上（三点光的方位角 = 相机方位角 + 偏移）——
## 环绕时角色永远是被照亮的那个正面，不会绕到背光里去。

const FLOOR_SHADER := "res://assets/shared/reel_floor.gdshader"
const BACKDROP_SHADER := "res://assets/shared/reel_backdrop.gdshader"
const RAIN_SHADER := "res://assets/shared/matrix_rain.gdshader"

## 想让幕墙上"装下"多高的内容（米）。
##
## 原始幕墙设计是给 1.375 m 的可见高度调的（见 matrix_backdrop.gdshader 头注释的推导）。
## 巡礼用透视机位，一帧里装下的幕墙高度大得多，所以这里取 11 m（≈ 8 倍），
## 并把所有长度参数按同一个比例放大 —— 图案还是那套图案，只是"拍得远"。
const BACKDROP_VISIBLE_M := 11.0

const BACKDROP_COLOR := Color(0.20, 1.0, 0.46)
const MATRIX_GREEN := Color(0.18, 1.0, 0.42)

## 地面尺寸（米）。够大就不会看到边 —— 远处靠雾和幕墙收掉。
const FLOOR_SIZE := 420.0

## 雨幕层。`f` = 该层相机距离占幕墙距离的比例（保证永远夹在角色与幕墙之间）。
##   cw / ch  一个"字符"的世界尺寸（米）—— 这是唯一决定"雨滴多大"的参数
##   wspeed   世界下落速度（米/秒）—— 换算成 UV 速度时除以板高，所以放大板不会让雨变快
const RAIN_LAYERS := [
	{"f": 0.68, "cw": 0.130, "ch": 0.240, "wspeed": 3.4, "bright": 0.55, "density": 0.26},
	{"f": 0.84, "cw": 0.120, "ch": 0.220, "wspeed": 3.0, "bright": 0.38, "density": 0.28},
	{"f": 0.97, "cw": 0.115, "ch": 0.210, "wspeed": 2.6, "bright": 0.26, "density": 0.30},
]
## 前景雨：压在角色**前面**（相机距离更近），让"雨在整场戏里"而不只在背景。
## 亮度压得很低，不然会糊住角色轮廓。
const RAIN_FRONT := {"cw": 0.26, "ch": 0.46, "wspeed": 4.4, "bright": 0.10, "density": 0.16}

var _cam: Camera3D
var _floor: MeshInstance3D
var _floor_mat: ShaderMaterial
var _backdrop: MeshInstance3D
var _backdrop_mesh: QuadMesh
var _backdrop_mat: ShaderMaterial
var _rains: Array[MeshInstance3D] = []
var _rain_meshes: Array[QuadMesh] = []
var _rain_mats: Array[ShaderMaterial] = []
var _key: DirectionalLight3D
var _rim: DirectionalLight3D
var _fill: DirectionalLight3D


func setup(cam: Camera3D) -> void:
	_cam = cam
	_build_environment()
	_build_lights()
	_build_floor()
	_build_backdrop()
	_build_rain()


# =====================================================================
# 接环境
# =====================================================================
func _build_environment() -> void:
	var env := Environment.new()

	var sky := ProceduralSkyMaterial.new()
	sky.sky_top_color = Color(0.004, 0.013, 0.010)
	sky.sky_horizon_color = Color(0.016, 0.062, 0.038)
	sky.ground_bottom_color = Color(0.002, 0.007, 0.005)
	sky.ground_horizon_color = Color(0.012, 0.042, 0.028)
	sky.sun_angle_max = 8.0
	env.background_mode = Environment.BG_SKY
	env.sky = Sky.new()
	env.sky.sky_material = sky

	# 环境光用**显式颜色**而不是 SKY：SKY 模式下 ambient_light_color 不生效
	# （游戏本体那边有记录），而巡礼需要能复现的、可调的补光量。
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.34, 0.72, 0.52)
	env.ambient_light_energy = 0.22

	# 雾：远景溶解。相机距离在 2.5~7 m、幕墙在 8~19 m，所以雾要"早开始、够远结束"，
	# 否则幕墙会被雾吃成一片灰绿。
	env.fog_enabled = true
	env.fog_mode = Environment.FOG_MODE_DEPTH
	env.fog_light_color = Color(0.006, 0.024, 0.015)
	env.fog_light_energy = 1.0
	env.fog_density = 1.0
	env.fog_sky_affect = 0.30
	env.fog_depth_begin = 11.0
	env.fog_depth_end = 58.0

	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.tonemap_exposure = 1.0

	# 辉光：只有真正过曝的东西（雨滴亮头、地平线辉光、主线）才发光。
	# 阈值给低了整屏会糊成一团绿 —— 这是这套场景最容易搞砸的一个数。
	env.glow_enabled = true
	env.glow_intensity = 0.55
	env.glow_bloom = 0.06
	env.glow_strength = 0.80
	env.glow_hdr_threshold = 1.25
	env.glow_blend_mode = Environment.GLOW_BLEND_MODE_ADDITIVE

	var we := WorldEnvironment.new()
	we.name = "ReelWorldEnv"
	we.environment = env
	add_child(we)


# =====================================================================
# 光
# =====================================================================
func _build_lights() -> void:
	# 主光：偏暖的白。**刻意不用绿色** —— 绿光照绿环境里的绿角色会糊成一团。
	_key = DirectionalLight3D.new()
	_key.name = "KeyLight"
	_key.light_energy = 1.45
	_key.light_color = Color(1.0, 0.97, 0.93)
	_key.shadow_enabled = true
	add_child(_key)

	# 轮廓光：从背后偏侧打绿光，把角色从背景里切出来。
	_rim = DirectionalLight3D.new()
	_rim.name = "RimLight"
	_rim.light_energy = 1.15
	_rim.light_color = Color(0.42, 1.0, 0.64)
	_rim.shadow_enabled = false
	add_child(_rim)

	# 补光：从相机侧偏下打冷色，压掉死黑的正面。
	_fill = DirectionalLight3D.new()
	_fill.name = "FillLight"
	_fill.light_energy = 0.40
	_fill.light_color = Color(0.52, 0.78, 0.98)
	_fill.shadow_enabled = false
	add_child(_fill)


# =====================================================================
# 地面
# =====================================================================
func _build_floor() -> void:
	var mesh := PlaneMesh.new()
	mesh.size = Vector2(FLOOR_SIZE, FLOOR_SIZE)

	_floor_mat = ShaderMaterial.new()
	var shader: Shader = load(FLOOR_SHADER)
	assert(shader != null, "找不到地面着色器: %s" % FLOOR_SHADER)
	_floor_mat.shader = shader
	_floor_mat.set_shader_parameter("cell_size", 1.0)
	_floor_mat.set_shader_parameter("major_every", 5.0)
	_floor_mat.set_shader_parameter("minor_px", 1.0)
	_floor_mat.set_shader_parameter("major_px", 1.5)
	_floor_mat.set_shader_parameter("fade_start", 8.0)
	_floor_mat.set_shader_parameter("fade_end", 46.0)

	_floor = MeshInstance3D.new()
	_floor.name = "Floor"
	_floor.mesh = mesh
	_floor.material_override = _floor_mat
	_floor.position = Vector3(0.0, 0.0, 0.0)
	add_child(_floor)


# =====================================================================
# 幕墙
# =====================================================================
func _build_backdrop() -> void:
	_backdrop_mesh = QuadMesh.new()
	_backdrop_mesh.size = Vector2(60.0, 40.0)

	var s := BACKDROP_VISIBLE_M / 1.375
	_backdrop_mat = ShaderMaterial.new()
	var shader: Shader = load(BACKDROP_SHADER)
	assert(shader != null, "找不到幕墙着色器: %s" % BACKDROP_SHADER)
	_backdrop_mat.shader = shader
	_backdrop_mat.set_shader_parameter("horizon_y", 0.0)
	_backdrop_mat.set_shader_parameter("glow_color", BACKDROP_COLOR)

	# 长度参数按"装下 11 m 而不是 1.375 m"整体放大 —— 图案不变，只是拍远了。
	_backdrop_mat.set_shader_parameter("glow_width", 0.055 * s)
	# 雾色往上收得更快：原始设计里可见的那 1.375 m **大部分是黑的**，
	# 按同一比例放大后 6.8 m 的渐变会把整块板泡成一层均匀的绿（实测）。
	_backdrop_mat.set_shader_parameter("haze_height", 0.42 * s)
	_backdrop_mat.set_shader_parameter("conduit_pitch", 0.44 * s)
	_backdrop_mat.set_shader_parameter("conduit_width", 0.013 * s)
	_backdrop_mat.set_shader_parameter("conduit_top_min", 0.30 * s)
	_backdrop_mat.set_shader_parameter("conduit_top_max", 1.10 * s)
	_backdrop_mat.set_shader_parameter("conduit_edge", 0.045 * s)
	_backdrop_mat.set_shader_parameter("grid_cell", 0.40 * s)
	_backdrop_mat.set_shader_parameter("grid_width", 0.024 * s)
	# 衰减项指数是"每米衰减多少"，长度放大后必须除以同一个比例，否则会瞬间衰减干净
	_backdrop_mat.set_shader_parameter("grid_falloff", 1.40 / s)
	_backdrop_mat.set_shader_parameter("block_cell", 0.14 * s)
	_backdrop_mat.set_shader_parameter("block_falloff", 1.10 / s)
	_backdrop_mat.set_shader_parameter("glow_gain", 0.46)
	# 网格与数据块在近景里是"纹理"，在 8 倍视野里会变成一层抢戏的亮网 —— 压暗。
	_backdrop_mat.set_shader_parameter("grid_gain", 0.014)
	_backdrop_mat.set_shader_parameter("block_gain", 0.026)
	_backdrop_mat.set_shader_parameter("gain", 0.085)

	_backdrop = MeshInstance3D.new()
	_backdrop.name = "Backdrop"
	_backdrop.mesh = _backdrop_mesh
	_backdrop.material_override = _backdrop_mat
	# 幕墙是**不透明**的：它要靠深度测试挡住后面的地面，那条"接缝"就是地平线。
	_backdrop.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(_backdrop)


# =====================================================================
# 雨幕
# =====================================================================
func _build_rain() -> void:
	var shader: Shader = load(RAIN_SHADER)
	assert(shader != null, "找不到雨幕着色器: %s" % RAIN_SHADER)

	for i in RAIN_LAYERS.size() + 1:
		var mesh := QuadMesh.new()
		var mat := ShaderMaterial.new()
		mat.shader = shader
		mat.set_shader_parameter("rain_color", MATRIX_GREEN)
		mat.set_shader_parameter("tail_len", 0.12)
		mat.set_shader_parameter("tail_gain", 0.20)
		mat.set_shader_parameter("columns", 40.0)
		mat.set_shader_parameter("rows", 40.0)
		mat.set_shader_parameter("edge_fade", 0.08)

		var mi := MeshInstance3D.new()
		mi.name = "RainFront" if i == RAIN_LAYERS.size() else "Rain%d" % i
		mi.mesh = mesh
		mi.material_override = mat
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		mi.gi_mode = GeometryInstance3D.GI_MODE_DISABLED
		add_child(mi)

		_rains.append(mi)
		_rain_meshes.append(mesh)
		_rain_mats.append(mat)


# =====================================================================
# 每帧摆放
# =====================================================================
## 在世界里挪动整个虚拟空间：地面网格跟着焦点走（这样无限大的网格永远铺在脚下，
## 不会出现"走到网格边缘"），幕墙与雨幕按相机距离重摆。
func sync(focus: Vector3, cam_pos: Vector3, fov: float, aspect: float) -> void:
	# 地面只在整数格上跳 —— 小数会让网格在角色脚下"流动"，像在传送带上。
	var gx := roundf(focus.x)
	var gz := roundf(focus.z)
	_floor.position = Vector3(gx, 0.0, gz)

	var to_cam := Vector3(cam_pos.x - focus.x, 0.0, cam_pos.z - focus.z)
	var dist_cam := maxf(to_cam.length(), 0.001)
	to_cam /= dist_cam
	var caz := atan2(to_cam.x, to_cam.z)          # 相机方位角（弧度，0 = 角色正前方）
	var half_v_tan := tan(deg_to_rad(fov) * 0.5)

	# --- 幕墙：位置由"想在画面里装下 11 m"反解 ---
	var l_back := BACKDROP_VISIBLE_M / (2.0 * half_v_tan)
	var d_back := maxf(l_back - dist_cam, 4.0)
	_place_billboard(_backdrop, _backdrop_mesh, focus, to_cam, caz, d_back,
		l_back, focus.y, half_v_tan, aspect, 1.25, -8.0)

	# --- 雨幕 ---
	var layers: Array = RAIN_LAYERS.duplicate()
	layers.append(null)   # 前景雨
	for i in layers.size():
		var mi: MeshInstance3D = _rains[i]
		var mesh: QuadMesh = _rain_meshes[i]
		var mat: ShaderMaterial = _rain_mats[i]
		var is_front := i == layers.size() - 1

		var l: float
		var spec: Dictionary
		var bottom: float
		if is_front:
			l = clampf(dist_cam * 0.50, 0.9, 3.0)
			spec = RAIN_FRONT
			bottom = -3.0
		else:
			spec = layers[i]
			l = l_back * float(spec["f"])
			# 必须夹在角色与幕墙之间，否则雨会跑到角色前面去
			l = clampf(l, dist_cam + 1.2, l_back - 0.8)
			bottom = -4.0

		var d := l - dist_cam
		var placement := _place_billboard(mi, mesh, focus, to_cam, caz, d,
			l, focus.y, half_v_tan, aspect, 1.30, bottom)

		var w: float = placement["w"]
		var h: float = placement["h"]
		mat.set_shader_parameter("columns", maxf(4.0, w / float(spec["cw"])))
		mat.set_shader_parameter("rows", maxf(4.0, h / float(spec["ch"])))
		# UV 速度 = 世界速度 / 板高 —— 板放大时雨不会跟着变快
		mat.set_shader_parameter("speed", float(spec["wspeed"]) / maxf(h, 0.5))
		mat.set_shader_parameter("brightness", float(spec["bright"]))
		mat.set_shader_parameter("density", float(spec["density"]))

	# --- 光跟着相机方位转 ---
	_set_light(_key, caz, -44.0, 36.0)
	_set_light(_rim, caz, -16.0, 158.0)
	_set_light(_fill, caz, 8.0, -26.0)


## 把一块板摆到"相机距离 l、焦点正后方 d 米、并正对相机"的位置，返回它需要的尺寸。
##
## 板尺寸按**实际可见范围**算（含余量），不是写死的 —— 这样同一个函数既能摆
## 幕墙（几十米宽）也能摆前景雨（两三米宽），且都不会露边。
func _place_billboard(node: MeshInstance3D, mesh: QuadMesh,
		focus: Vector3, to_cam: Vector3, caz: float, d: float,
		l: float, focus_y: float, half_v_tan: float, aspect: float,
		margin: float, bottom: float) -> Dictionary:
	var half_v := l * half_v_tan
	var top := focus_y + half_v * margin
	var bot := minf(bottom, focus_y - half_v * margin)
	var h := maxf(top - bot, 1.0)
	var w := maxf(2.0 * half_v * aspect * margin, 1.0)

	mesh.size = Vector2(w, h)
	node.position = focus - to_cam * d
	node.position.y = (top + bot) * 0.5
	# 板默认法线 +Z；让 +Z 指向相机 ⟹ rotation.y = atan2(to_cam.x, to_cam.z)
	node.rotation = Vector3(0.0, caz, 0.0)
	node.visible = true

	return {"w": w, "h": h}


func _set_light(light: DirectionalLight3D, caz: float, pitch: float, offset_deg: float) -> void:
	# 光的方位角 = 相机方位角 + 偏移。rotation.y = 方位角时，光的 −Z 正好
	# 从该方位射向原点（见 DirectionalLight3D 的默认朝向）。
	light.rotation = Vector3(deg_to_rad(pitch), caz + deg_to_rad(offset_deg), 0.0)


## 给外部（调试 / 诊断）用
func floor_material() -> ShaderMaterial:
	return _floor_mat
