class_name Stage
extends Node3D
## 舞台：黑客帝国式虚拟空间。
##
## 尺寸全部从 GameDB.STAGE_HALF_WIDTH 推出来 —— 视觉边界和"角色能被推到多远"
## 必须是同一个数字，否则会出现"人卡在墙里"或"墙外还能走"。
##
## ---------------------------------------------------------------------------
## 空间构成（由远及近）：
##   1. 极暗天空 + 雾        —— 让远景自然溶解，不出现硬边
##   2. 远景幕墙 (z=-7.6)    —— **这块板是整场景的骨架**，理由见下
##   3. 四层数字雨幕         —— 着色器生成，越远的层字符越小（正交相机要靠这个装纵深）
##   4. 一层前景雨           —— 很淡，盖在角色前面，让"雨在整场戏里"而不只在背景
##   5. 发光网格地面         —— 着色器生成，接收角色阴影
##   6. 边界立柱 + 地面亮线  —— 亮绿发光，和物理夹逼范围一致
##
## ---------------------------------------------------------------------------
## 为什么必须要有"远景幕墙"（踩过的坑）：
##
##   正交相机俯视时，地面平面的投影会**铺满整个画面** —— 屏幕上不存在"天空"。
##   上半屏看到的其实也是地面（远处那一段），一片死黑的绿，没有任何信息量。
##
##   第一版的错误是没意识到这点：把远处的地面当成了"背景"，在上面摆数据柱。
##   一根 1.6 m 宽、最高 9 m 的**不透明**方块（x=0.5, z=-5.5）在竖直视野只有
##   3.05 m 的相机里，屏幕上就是一块占满整个画面高度、宽 29% 的**黑墙**。
##
##   解法：在 z = BACKDROP_Z 竖一块**竖直**的板挡住远处那段地面，让屏幕上
##   重新出现清晰的"地平线"，上半屏才有地方放远景。
##
## ---------------------------------------------------------------------------
## 光比环境更重要：一个绿色空间里角色如果也被照成绿的就会糊在一起。
## 所以主光用**偏暖**的白，另加一盏绿色轮廓光把角色从背景里切出来。

# ---------------------------------------------------------------------------
# 数字雨
# ---------------------------------------------------------------------------
## 雨幕底边的高度（米）。**必须放到地面以下** —— 雨幕是竖直板，只有让它
## 探到 y<0，被地面切掉之后剩下的部分才够铺满屏幕。
const RAIN_BOTTOM_Y := -1.0
## 每块雨幕板的高度（米）。
##
## **板必须够高**：正交相机下 1 m 永远是 234 px，而竖直视野有 3.05 m，
## 所以一块 4.4 m 的板看着够高，实际上它的**屏幕覆盖是跟着 z 走的** ——
## 越远的板在屏幕上越靠上。z=-6.4 那块要盖到屏幕顶（ndc=1.0）需要
## 板顶到 y ≈ 5.3。实测 4.4 m 时上半屏是空的，雨只出现在下半屏。
const RAIN_HEIGHT := 7.0
## 雨幕板的横向半宽（米）
const RAIN_HALF_X := 34.0
## 四层雨幕。cell_w / cell_h 是**屏幕上的**字符尺寸（米）：
## 近层字符大、远层字符小。正交相机没有透视缩放，"远"只能靠这个密度差 + 亮度差表达。
##
## 尺寸是按屏幕像素反推的，不是凭感觉：正交相机下 1 m ≡ 720/3.05 ≈ 236 px，
## 所以 0.075 × 0.130 m ≈ **18 × 31 px** —— 这正是"一个字符"该有的像素量。
## 第一版给了 0.17 × 0.30（≈ 40 × 70 px），出图里读起来是"发光方块"而不是字符。
##
## `density` 是背景亮度的第一闸门，不是风格参数。四层叠起来会累加，
## 所以每层都压在 0.10~0.16 —— 第一版给了 0.30~0.42，上半屏直接糊成一片平绿。
const RAIN_LAYERS := [
	{"z": -1.0, "cell_w": 0.075, "cell_h": 0.130, "speed": 0.52, "brightness": 0.85, "density": 0.16},
	{"z": -2.8, "cell_w": 0.065, "cell_h": 0.112, "speed": 0.41, "brightness": 0.66, "density": 0.15},
	{"z": -4.6, "cell_w": 0.056, "cell_h": 0.096, "speed": 0.32, "brightness": 0.50, "density": 0.14},
	{"z": -6.4, "cell_w": 0.048, "cell_h": 0.082, "speed": 0.24, "brightness": 0.36, "density": 0.13},
]
## 前景雨：一层很淡的雨盖在角色前面（z 比角色更靠相机）。
## 让"雨"属于整场戏而不只是背景。亮度压得很低，不然会糊住角色的轮廓。
const RAIN_FOREGROUND := {"z": 2.6, "cell_w": 0.130, "cell_h": 0.230, "speed": 0.78, "brightness": 0.16, "density": 0.10}
## 雨滴拖尾占一个循环周期的比例。太大每列就成了一条长亮条，看不出"一颗颗落"。
const RAIN_TAIL := 0.10
## 拖尾相对亮头的亮度比。**对比度全靠它** —— 0.22 时是"黑底上跑亮字符"，
## 0.55 时（第一版）会退化成一层均匀的绿雾。
const RAIN_TAIL_GAIN := 0.22
const RAIN_SHADER := "res://assets/shared/matrix_rain.gdshader"

# ---------------------------------------------------------------------------
# 远景幕墙
# ---------------------------------------------------------------------------
## 幕墙的 z。**越近，屏幕上属于"天空"的比例越大**：
## 实测 z=-7.6 → 幕墙占画面顶部约 44%，正好是"地平线在画面中偏上"的经典构图。
const BACKDROP_Z := -7.6
## 幕墙底边高度：放到地面以下，保证板与地面之间没有缝
const BACKDROP_BOTTOM_Y := -6.0
## 幕墙高度：要盖住"相机拉远时"露出更多的那部分（size 变大时可见 y 到 ~2.9 m）
const BACKDROP_HEIGHT := 26.0
## 幕墙横向半宽
const BACKDROP_HALF_X := 34.0
const BACKDROP_SHADER := "res://assets/shared/matrix_backdrop.gdshader"

# ---------------------------------------------------------------------------
# 地面
# ---------------------------------------------------------------------------
## 地面靠相机这一侧的边（米）。要大于屏幕底边对应的 z（约 +4.6），否则会看到地板边缘。
const FLOOR_FRONT_Z := 8.0
## 地面沿 -Z 的延伸（米）。-7.6 之后的部分会被幕墙挡住，不用铺到无限远。
const FLOOR_DEPTH := 46.0
## 地面向舞台两侧的额外延伸（米），让边界外不是虚空。
const GROUND_OVERHANG := 16.0
const FLOOR_SHADER := "res://assets/shared/grid_floor.gdshader"

# ---------------------------------------------------------------------------
# 边界
# ---------------------------------------------------------------------------
## 边界立柱高度（米）
const BOUND_POST_H := 2.6
## 地面亮线的长度（米）—— 只铺到幕墙附近，不穿过幕墙
const BOUND_LINE_LEN := 13.0

const MATRIX_GREEN := Color(0.18, 1.0, 0.42)
const RAIN_COLOR := Color(0.20, 1.0, 0.46)

## 幕墙的整体增益（背景亮度总闸门）。由 tools/tune_stage.tscn 实测标定。
const BACKDROP_GAIN := 2.0
## 地平线辉光带的基准增益。
## 峰值 = 本值 × glow_color.g(1.0) × 1.22(ALBEDO+EMISSION) ≈ 1.22，
## 刚好压在 glow_hdr_threshold(1.30) 之下 —— 既不糊屏，也还留着"再加一点就发光"的余量。
const BACKDROP_BAND_GAIN := 1.0
## 命中时地平线额外提亮的幅度（叠加在基准之上）
const BACKDROP_BAND_PULSE := 1.4

## 随命中脉动的节点（边界柱），由 Game 在命中时触发 —— 让空间对打击有反应
var _pulse_nodes: Array[Node3D] = []
## 幕墙材质：命中时让地平线辉光也亮一下（地平线在画面里，比边界柱更容易被看到）
var _backdrop_mat: ShaderMaterial
var _pulse := 0.0


func _ready() -> void:
	_build_environment()
	_build_floor()
	_build_backdrop()
	_build_rain()
	_build_bounds()


# ---------------------------------------------------------------------
# 环境与光照
# ---------------------------------------------------------------------
func _build_environment() -> void:
	var env := Environment.new()

	# 天空：极暗的绿黑。不能用纯黑 —— 纯黑加辉光会显得脏。
	# 注意：因为幕墙挡住了上半屏，天空其实几乎看不到；留着是为了画面边缘和
	# 万一幕墙被关掉时的兜底。
	var sky := ProceduralSkyMaterial.new()
	sky.sky_top_color = Color(0.003, 0.010, 0.008)
	sky.sky_horizon_color = Color(0.010, 0.034, 0.022)
	sky.ground_bottom_color = Color(0.002, 0.007, 0.005)
	sky.ground_horizon_color = Color(0.008, 0.026, 0.017)
	sky.sun_angle_max = 8.0
	env.background_mode = Environment.BG_SKY
	env.sky = Sky.new()
	env.sky.sky_material = sky

	# 环境光：低，偏绿。太高会把网格的发光感冲掉。
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_sky_contribution = 1.0
	env.ambient_light_energy = 0.30
	env.ambient_light_color = Color(0.30, 0.78, 0.50)

	# 雾：远景溶解。可见纵深只有 3~24 m，所以雾要"早开始、早结束"，
	# 否则地平线附近的地面还是亮的，会和幕墙撞出一条硬边。
	env.fog_enabled = true
	env.fog_mode = Environment.FOG_MODE_DEPTH
	env.fog_light_color = Color(0.0035, 0.0130, 0.0080)
	env.fog_light_energy = 1.0
	env.fog_density = 0.026
	env.fog_sky_affect = 0.35
	env.fog_depth_begin = 5.0
	env.fog_depth_end = 22.0

	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.tonemap_exposure = 1.0
	# 辉光是这套场景的主力：网格线、数字雨、地平线辉光全靠它"发光"。
	#
	# ---------------------------------------------------------------------
	# 这里是整个场景最容易搞砸的地方，实测记录：
	#
	# 第一版设 glow_threshold=0.85 / intensity=1.05 / bloom=0.28，出图是上半屏
	# 一片均匀的中绿 (25,167,71)。我一开始归因成"幕墙四项累加太亮"，
	# 但按公式算幕墙只有 0.007 线性绿（≈ sRGB 23），差了 7 倍 —— 对不上。
	#
	# 真正的证据是**它的空间分布**：y=16 处 167、y=300 处 193，越靠近地平线越亮。
	# 一个"均匀的底色"不会长这样 —— 这是**bloom 光晕的衰减剖面**。
	# 地平线辉光带峰值约 1.22 线性，远超阈值，被最宽那几级模糊糊满了整屏。
	#
	# 所以修法有两处，缺一不可：
	#   1. 把最宽的三级模糊关掉（glow_levels）—— 外科手术式，只杀光晕不杀发光；
	#   2. 把辉光带峰值和整体辉光压下来。
	# ---------------------------------------------------------------------
	env.glow_enabled = true
	env.glow_intensity = 0.55
	env.glow_bloom = 0.04
	env.glow_strength = 0.62
	env.glow_hdr_threshold = 1.30
	env.glow_blend_mode = Environment.GLOW_BLEND_MODE_ADDITIVE
	env.glow_normalized = true
	# 逐级模糊强度。1 = 最宽（最糊），7 = 最紧。默认七级全 1.0，
	# 那一级"最宽"就是糊满全屏的元凶。只留最紧的三级：既有霓虹感，又不糊背景。
	for lv in range(1, 8):
		env.set("glow_levels/%d" % lv, 1.0 if lv >= 5 else (0.35 if lv == 4 else 0.0))

	var we := WorldEnvironment.new()
	we.name = "WorldEnvironment"
	we.environment = env
	add_child(we)

	# 主光：偏暖的白。**刻意不用绿色** —— 绿光照绿环境里的绿角色会糊成一团。
	var key := DirectionalLight3D.new()
	key.name = "KeyLight"
	key.light_energy = 1.25
	key.light_color = Color(1.0, 0.97, 0.92)
	key.shadow_enabled = true
	key.rotation_degrees = Vector3(-40.0, 148.0, 0.0)
	add_child(key)

	# 轮廓光：从背后偏右打绿光，把角色的边从背景里切出来。
	var rim := DirectionalLight3D.new()
	rim.name = "RimLight"
	rim.light_energy = 0.85
	rim.light_color = Color(0.40, 1.0, 0.62)
	rim.shadow_enabled = false
	rim.rotation_degrees = Vector3(-14.0, -34.0, 0.0)
	add_child(rim)

	# 补光：从相机侧偏上打冷色，压掉死黑的正面
	var fill := DirectionalLight3D.new()
	fill.name = "FillLight"
	fill.light_energy = 0.32
	fill.light_color = Color(0.50, 0.78, 0.95)
	fill.shadow_enabled = false
	fill.rotation_degrees = Vector3(6.0, 168.0, 0.0)
	add_child(fill)


# ---------------------------------------------------------------------
# 地面
# ---------------------------------------------------------------------
func _build_floor() -> void:
	var half_x: float = GameDB.STAGE_HALF_WIDTH + GROUND_OVERHANG

	# 用 PlaneMesh 而不是 BoxMesh：地面是一张水平面，网格靠着色器按世界坐标画。
	var mesh := PlaneMesh.new()
	mesh.size = Vector2(half_x * 2.0, FLOOR_DEPTH)

	var mat := ShaderMaterial.new()
	var shader: Shader = load(FLOOR_SHADER)
	assert(shader != null, "找不到地面着色器: %s" % FLOOR_SHADER)
	mat.shader = shader
	mat.set_shader_parameter("cell_size", 1.0)
	mat.set_shader_parameter("major_every", 5.0)
	# 俯角的正弦从这里传进去 —— 着色器要靠它补偿 z 方向的透视压缩，
	# 否则横线在屏幕上只有 0.46 px（见着色器头部注释）。
	# 直接读 Game 的常量，保证"相机俯角"只有一处定义。
	mat.set_shader_parameter("view_sin", sin(deg_to_rad(absf(Game.CAM_PITCH_DEG))))
	mat.set_shader_parameter("fade_start", 4.0)
	mat.set_shader_parameter("fade_end", 15.0)
	# 线的亮度收一点：默认 1.0 时横向主线（被 z 方向 1/sin8° 放大过）在屏幕上是
	# 一撮很密的暖色亮线，抢角色的视觉重心。
	mat.set_shader_parameter("line_gain", 0.78)
	mat.set_shader_parameter("major_width", 0.022)

	var mi := MeshInstance3D.new()
	mi.name = "Floor"
	mi.mesh = mesh
	mi.material_override = mat
	# PlaneMesh 躺在 XZ 平面上，y=0 正好是脚底平面。
	# 中心往后放：靠相机那侧到 FLOOR_FRONT_Z，向后铺满整个背景深度。
	mi.position = Vector3(0.0, 0.0, FLOOR_FRONT_Z - FLOOR_DEPTH * 0.5)
	add_child(mi)


# ---------------------------------------------------------------------
# 远景幕墙
# ---------------------------------------------------------------------
## 挡住远处那段地面，让屏幕上重新出现"地平线"。
## 没有它，上半屏就是一片死黑的远处地面（原因见文件头注释）。
func _build_backdrop() -> void:
	var shader: Shader = load(BACKDROP_SHADER)
	assert(shader != null, "找不到远景幕墙着色器: %s" % BACKDROP_SHADER)

	_backdrop_mat = ShaderMaterial.new()
	_backdrop_mat.shader = shader
	_backdrop_mat.set_shader_parameter("horizon_y", 0.0)
	_backdrop_mat.set_shader_parameter("glow_color", RAIN_COLOR)
	# 这两个值由脚本显式设定，不依赖着色器里的默认值 ——
	# 亮度是"设计参数"，应该和相机常量一样只有一处定义、可被审阅。
	_backdrop_mat.set_shader_parameter("gain", BACKDROP_GAIN)
	_backdrop_mat.set_shader_parameter("glow_gain", BACKDROP_BAND_GAIN)

	var mesh := QuadMesh.new()
	mesh.size = Vector2(BACKDROP_HALF_X * 2.0, BACKDROP_HEIGHT)

	var mi := MeshInstance3D.new()
	mi.name = "Backdrop"
	mi.mesh = mesh
	mi.material_override = _backdrop_mat
	mi.position = Vector3(0.0, BACKDROP_BOTTOM_Y + BACKDROP_HEIGHT * 0.5, BACKDROP_Z)
	# 幕墙是**不透明**的：它要靠深度测试挡住后面的地面。
	# （反过来，它自己的下半部分会被更近的地面挡住 —— 这条"接缝"正好当地平线用。）
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(mi)


# ---------------------------------------------------------------------
# 数字雨
# ---------------------------------------------------------------------
func _build_rain() -> void:
	var shader: Shader = load(RAIN_SHADER)
	assert(shader != null, "找不到数字雨着色器: %s" % RAIN_SHADER)

	var layers: Array = RAIN_LAYERS.duplicate()
	layers.append(RAIN_FOREGROUND)

	for i in layers.size():
		var layer: Dictionary = layers[i]
		var h: float = RAIN_HEIGHT
		var name_prefix := "Rain"

		var mat := ShaderMaterial.new()
		mat.shader = shader
		# 每层一份材质：uniform 各自独立，但共用同一个 Shader 资源（不重复编译）
		mat.set_shader_parameter("rain_color", RAIN_COLOR)
		mat.set_shader_parameter("columns", RAIN_HALF_X * 2.0 / float(layer["cell_w"]))
		mat.set_shader_parameter("rows", h / float(layer["cell_h"]))
		mat.set_shader_parameter("speed", float(layer["speed"]))
		mat.set_shader_parameter("brightness", float(layer["brightness"]))
		mat.set_shader_parameter("density", float(layer["density"]))
		mat.set_shader_parameter("tail_len", RAIN_TAIL)
		mat.set_shader_parameter("tail_gain", RAIN_TAIL_GAIN)

		var mesh := QuadMesh.new()
		mesh.size = Vector2(RAIN_HALF_X * 2.0, h)

		var mi := MeshInstance3D.new()
		mi.name = "%s%d_z%d" % [name_prefix, i, int(absf(float(layer["z"]) * 10.0))]
		mi.mesh = mesh
		mi.material_override = mat
		mi.position = Vector3(0.0, RAIN_BOTTOM_Y + h * 0.5, float(layer["z"]))
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		# 雨幕是透明的，永远渲染在不透明物体之后、并且上下都不写深度
		mi.gi_mode = GeometryInstance3D.GI_MODE_DISABLED
		add_child(mi)


# ---------------------------------------------------------------------
# 边界
# ---------------------------------------------------------------------
func _build_bounds() -> void:
	## 边界：一道**看得见**的发光立柱 + 地面亮线。
	## 角色会被 _move_world 夹在 ±STAGE_HALF_WIDTH 内 —— 视觉必须对得上。
	var h: float = GameDB.STAGE_HALF_WIDTH
	for s in [-1.0, 1.0]:
		var tag: String = "R" if s > 0.0 else "L"

		var post := BoxMesh.new()
		post.size = Vector3(0.20, BOUND_POST_H, 0.20)
		var pmat := StandardMaterial3D.new()
		pmat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		pmat.albedo_color = MATRIX_GREEN
		pmat.emission_enabled = true
		pmat.emission = MATRIX_GREEN * 1.35
		var pmi := MeshInstance3D.new()
		pmi.name = "BoundPost%s" % tag
		pmi.mesh = post
		pmi.material_override = pmat
		pmi.position = Vector3(s * h, BOUND_POST_H * 0.5, 0.0)
		pmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(pmi)
		_pulse_nodes.append(pmi)

		# 地面亮线：沿 Z 铺一条，让边界在地面上也能读出来。
		# 长度只到幕墙附近 —— 铺太长会从幕墙里穿出去。
		var line := BoxMesh.new()
		line.size = Vector3(0.10, 0.03, BOUND_LINE_LEN)
		var lmat := StandardMaterial3D.new()
		lmat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		lmat.albedo_color = MATRIX_GREEN
		lmat.emission_enabled = true
		lmat.emission = MATRIX_GREEN * 1.2
		var lmi := MeshInstance3D.new()
		lmi.name = "BoundLine%s" % tag
		lmi.mesh = line
		lmi.material_override = lmat
		lmi.position = Vector3(s * h, 0.02, FLOOR_FRONT_Z - BOUND_LINE_LEN * 0.5)
		lmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(lmi)


# ---------------------------------------------------------------------
# 对打击的反应
# ---------------------------------------------------------------------
## 命中时让空间脉动一下（边界柱 + 地平线辉光变亮）。
## 目的不是好看，是**让空间对战斗有反应** —— 纯静态背景打起来会觉得"没打到东西"。
func pulse(strength: float = 1.0) -> void:
	_pulse = maxf(_pulse, clampf(strength, 0.0, 1.0))


func _process(delta: float) -> void:
	_pulse = maxf(0.0, _pulse - delta * 2.4)

	for n in _pulse_nodes:
		var mi := n as MeshInstance3D
		if mi == null:
			continue
		var m := mi.material_override as StandardMaterial3D
		if m != null:
			m.emission = MATRIX_GREEN * (1.35 + _pulse * 1.8)

	# 地平线辉光跟着亮：这是画面里最容易看到的一处"空间反馈"。
	# 增益上限有硬约束 —— 峰值超过 glow_hdr_threshold 会把整屏糊成一片
	# （见 BACKDROP_BAND_GAIN 的注释）。
	if _backdrop_mat != null:
		_backdrop_mat.set_shader_parameter("glow_gain",
			BACKDROP_BAND_GAIN + _pulse * BACKDROP_BAND_PULSE)
