class_name Vfx
extends RefCounted
## 程序化特效库：命中爆点 / 地面冲击波 / 蓄力光环 / 受击闪白。
##
## ---------------------------------------------------------------------------
## 为什么全部是程序化的（而不是用特效资产）：
##
##   资产清单里登记过三个特效（`skill_effect_v1` / `green_shooting_effect_v1` /
##   `green_healing_effect_v2`），但它们属于**上一个角色**（business_man），
##   而且**没有 GLB** —— 也就是说工程里其实没有任何可用的特效资产。
##
##   所以这里不假装有资产可用，而是用"四边形 + 着色器 + 一条 Tween"来做：
##     - 横版格斗的相机几乎是正交地盯着 +Z，特效本来就该是朝向相机的一张图；
##     - 所有形状由 `progress` 一个 0→1 的数驱动，时序**完全确定**，
##       于是"第 N 帧长什么样"可以被截图验收 —— 粒子做不到这一点。
##
## ---------------------------------------------------------------------------
## 命名约定：所有特效节点都以 `VFX_` 开头挂在 host 下，
## 靠这条约定就能在测试里数出"当前有几个特效在跑"。

const HIT_SHADER := "res://assets/shared/vfx_hit.gdshader"
const SHOCK_SHADER := "res://assets/shared/vfx_shock.gdshader"
const AURA_SHADER := "res://assets/shared/vfx_aura.gdshader"
const FLASH_SHADER := "res://assets/shared/vfx_flash.gdshader"
const PREFIX := "VFX_"

## 命中爆点的基准尺寸（米）与时长（秒）。power=1 时就用这个值。
const HIT_BASE_SIZE := 0.85
const HIT_BASE_LIFE := 0.15
## 尺寸/时长随 power 的增长系数：size = base * (1 + (power-1)*size_k)
const HIT_SIZE_K := 0.42
const HIT_LIFE_K := 0.28

## 命中强度分级（供外部按伤害选档，避免各调用点自己写魔法数）
const POWER_LIGHT := 1.0
const POWER_HEAVY := 2.0
const POWER_SPECIAL := 3.4

const COLOR_LIGHT := Color(1.0, 0.80, 0.30)
const COLOR_HEAVY := Color(1.0, 0.62, 0.18)
const COLOR_GUARD := Color(0.45, 0.80, 1.0)
## 地面冲击波用**青白**而不是绿：地面本身就是绿的，绿色环叠上去等于隐形
## （第一版实测就是这样，出图里几乎看不出有环）。青白和绿地面拉开色相差，
## 又仍然属于"数字能量"的色系。
const COLOR_SHOCK := Color(0.66, 1.0, 0.96)
## 抓技的爆点用**紫罗兰**：它既不是"打中"的暖橙、也不是"防住"的冷蓝，
## 而是一眼能认出"这是被扣住了"的第三种语义。
const COLOR_GRAB := Color(0.74, 0.60, 1.0)
const COLOR_AURA := Color(0.42, 1.0, 0.62)

## 已编译的着色器缓存：同一个 Shader 资源被很多材质共用，不重复 load。
static var _shaders := {}


# ---------------------------------------------------------------------
# 公共 API
# ---------------------------------------------------------------------
## 命中爆点。`dir` 是命中方向（+1 = 朝 +X 打），用来把火花略微偏向受力方向。
## 返回生成的节点（测试可以拿它做断言），到期自动释放。
static func impact(host: Node3D, pos: Vector3, dir: float,
		power: float = POWER_LIGHT, color: Color = COLOR_LIGHT) -> Node3D:
	if host == null or not is_instance_valid(host):
		return null

	var size: float = HIT_BASE_SIZE * (1.0 + (power - 1.0) * HIT_SIZE_K)
	var life: float = HIT_BASE_LIFE * (1.0 + (power - 1.0) * HIT_LIFE_K)

	var mi := _new_quad(host, "Hit", HIT_SHADER, Vector2(size, size))
	if mi == null:
		return null
	# 火花往受力方向偏一点，读起来"是被这一拳打出来的"而不是凭空出现
	mi.position = pos + Vector3(dir * size * 0.12, 0.0, 0.0)

	var mat := mi.material_override as ShaderMaterial
	mat.set_shader_parameter("color", color)
	mat.set_shader_parameter("hot_color", Color(1.0, 1.0, 0.95))
	# 强度越高，增益越大、尖刺越长
	mat.set_shader_parameter("gain", 0.85 + (power - 1.0) * 0.30)
	mat.set_shader_parameter("spokes", 6 + int(power * 2.0))
	mat.set_shader_parameter("spoke_len", minf(0.55 + power * 0.20, 1.05))
	mat.set_shader_parameter("ring_radius", 0.95)

	_drive(host, mi, mat, life)
	return mi


## 默认冲击波半径（米）。
##
## 这个数要**和相机视野一起看**：竖直视野 3.05 m、横向 5.42 m。
## 半径 2.4 m 时屏幕上宽约 316 px、高约 45 px（俯角压扁）。
## 第一版试过 3.4 m，出图里椭圆几乎铺满整屏 —— 太大反而失去"一圈波"的读法，
## 而且加色叠起来把整个画面糊白了。2.4 m 是"一眼看得出是一圈、又不吃掉画面"的值。
const SHOCK_RADIUS := 2.4
## 抛射爆点的尺寸（米）。**固定值，不跟着半径缩放** ——
## 它是"看得见"的那一层，尺寸要跟着**角色**走（角色高 1.73 m），
## 而不是跟着地面环走。跟着半径缩放会让它在大招里变成一堵白墙。
const SHOCK_BURST_SIZE := Vector2(1.45, 0.80)
const SHOCK_BURST_GAIN := 0.55


## 地面冲击波：躺在地面上扩散的一圈光 + 一记竖向的抛射爆点。
##
## ---------------------------------------------------------------------------
## **为什么必须配一个竖向爆点**（这是这个特效最容易做错的地方）：
##
##   相机俯角只有 8°，地面上的圆投影到屏幕上被压成很扁的椭圆 ——
##   半径 2.4 m 时屏幕上宽 316 px、**高只有 45 px**。
##   我把环的增益从 1.6 提到 3.4、厚度提到半径的 22%，
##   出图里**依然几乎看不见** —— 因为问题不是亮度，是几何：
##   一个 45 px 高的椭圆无论多亮都不像"砸出一圈冲击波"。
##
##   所以这里改成两层：地面环（负责"贴地"） + 竖向抛射（负责"看得见"）。
##   竖向那层朝相机、不受俯角压缩，才是这个特效真正的可读部分。
##   这是机位的物理限制，不是调参能绕过的。
##
## 返回地面环节点；抛射爆点作为兄弟节点一起生成。
static func shockwave(host: Node3D, pos: Vector3, radius: float = SHOCK_RADIUS,
		life: float = 0.48, color: Color = COLOR_SHOCK, view_sin: float = 0.139) -> Node3D:
	if host == null or not is_instance_valid(host):
		return null

	var mi := _new_quad(host, "Shock", SHOCK_SHADER, Vector2(radius * 2.0, radius * 2.0))
	if mi == null:
		return null
	# 四边形立起来 → 躺到 XZ 地面上
	mi.rotation = Vector3(-PI * 0.5, 0.0, 0.0)
	mi.position = Vector3(pos.x, 0.03, pos.z)

	var mat := mi.material_override as ShaderMaterial
	mat.set_shader_parameter("color", color)
	mat.set_shader_parameter("hot_color", Color(1.0, 1.0, 1.0))
	mat.set_shader_parameter("max_radius", radius)
	# 环做厚一点：8° 俯角把圆压成很扁的椭圆，细环在屏幕上几乎不可见
	mat.set_shader_parameter("thickness", radius * 0.20)
	mat.set_shader_parameter("view_sin", view_sin)
	mat.set_shader_parameter("half_size", Vector2(radius, radius))
	mat.set_shader_parameter("center_xz", Vector2(pos.x, pos.z))

	_drive(host, mi, mat, life)

	# --- 竖向抛射：朝向相机，负责"看得见" ---
	# 用 vfx_hit 的着色器，但把尖刺调多调长，读起来像"往上炸开"而不是"被打了一拳"。
	var ej := _new_quad(host, "ShockBurst", HIT_SHADER, SHOCK_BURST_SIZE)
	if ej != null:
		ej.position = Vector3(pos.x, SHOCK_BURST_SIZE.y * 0.42, pos.z)
		var em := ej.material_override as ShaderMaterial
		em.set_shader_parameter("color", color)
		em.set_shader_parameter("hot_color", Color(1.0, 1.0, 1.0))
		em.set_shader_parameter("gain", SHOCK_BURST_GAIN)
		em.set_shader_parameter("spokes", 9)
		em.set_shader_parameter("spoke_len", 1.02)
		em.set_shader_parameter("ring_radius", 0.90)
		_drive(host, ej, em, life * 0.62)

	return mi


## 蓄力光环：挂在 `target` 身上，持续 `duration` 秒。
## 返回节点；调用方可以提前 `stop_aura()` 让它淡出。
##
## 和另外两个特效不同，它是**跟随**的（parent 到角色），因为它表达的是
## "这个人在蓄力"，而不是"那里发生了一次爆炸"。
static func aura(target: Node3D, width: float = 1.5, height: float = 2.3,
		duration: float = 1.5, color: Color = COLOR_AURA) -> Node3D:
	if target == null or not is_instance_valid(target):
		return null

	var mi := _new_quad(target, "Aura", AURA_SHADER, Vector2(width, height))
	if mi == null:
		return null
	mi.position = Vector3(0.0, height * 0.5, 0.0)

	var mat := mi.material_override as ShaderMaterial
	mat.set_shader_parameter("color", color)
	mat.set_shader_parameter("hot_color", Color(0.92, 1.0, 0.96))
	mat.set_shader_parameter("gain", 0.0)
	mat.set_shader_parameter("life", 1.0)

	# 入场：强度 0 → 1（快）；出场：life 1 → 0（慢）
	# Tween 同样绑在光环节点自己身上（理由见 _drive 的注释）。
	var tw := mi.create_tween()
	tw.tween_method(func(v: float) -> void:
		if is_instance_valid(mi):
			(mat as ShaderMaterial).set_shader_parameter("gain", v),
		0.0, 1.0, 0.22).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	# 晃一晃，别像一张静止的贴纸
	tw.parallel().tween_method(func(v: float) -> void:
		if is_instance_valid(mi):
			(mi as Node3D).scale = Vector3(1.0 + v * 0.06, 1.0, 1.0),
		0.0, 1.0, 0.22)

	var hold: float = maxf(duration - 0.5, 0.05)
	var tw2 := mi.create_tween()
	tw2.tween_interval(hold)
	tw2.tween_method(func(v: float) -> void:
		if is_instance_valid(mi):
			(mat as ShaderMaterial).set_shader_parameter("life", v),
		1.0, 0.0, 0.28).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN)
	tw2.tween_callback(func() -> void:
		if is_instance_valid(mi):
			(mi as Node3D).queue_free())
	return mi


## 受击闪白材质。**一份材质闪全身** —— 由 Fighter 在 _ready 时挂成
## 所有 MeshInstance3D 的 `material_overlay`，命中时只改这一个 uniform。
static func flash_material() -> ShaderMaterial:
	var sh := _shader(FLASH_SHADER)
	if sh == null:
		return null
	var m := ShaderMaterial.new()
	m.shader = sh
	m.set_shader_parameter("flash_color", Color(1.0, 1.0, 1.0))
	m.set_shader_parameter("flash", 0.0)
	return m


# ---------------------------------------------------------------------
# 工具
# ---------------------------------------------------------------------
## 数出 host 下正在跑的特效数量（测试用）。
static func active_count(host: Node3D) -> int:
	if host == null or not is_instance_valid(host):
		return 0
	var n := 0
	for c in host.get_children():
		if c.name.begins_with(PREFIX):
			n += 1
	return n


## 把整棵子树上的 material_overlay 换成 `mat`（传 null 即摘下）。
## 返回被改的 MeshInstance3D 数量 —— 调用方可以据此断言"确实挂上了"。
static func apply_overlay(root: Node, mat: Material) -> int:
	var n := 0
	for mi in _collect_meshes(root):
		mi.material_overlay = mat
		n += 1
	return n


static func _collect_meshes(node: Node) -> Array[MeshInstance3D]:
	var out: Array[MeshInstance3D] = []
	var mi := node as MeshInstance3D
	if mi != null and mi.mesh != null:
		out.append(mi)
	for c in node.get_children():
		out.append_array(_collect_meshes(c))
	return out


static func _shader(path: String) -> Shader:
	if not _shaders.has(path):
		_shaders[path] = load(path) as Shader
	return _shaders[path]


static func _new_quad(host: Node3D, tag: String, shader_path: String,
		size: Vector2) -> MeshInstance3D:
	var sh := _shader(shader_path)
	if sh == null:
		push_error("Vfx: 找不到着色器 %s" % shader_path)
		return null

	# 每次新建一份材质：uniform 是**每个特效实例各自的状态**（progress 不同），
	# 共用材质会让所有特效同步播放。着色器资源本身是共用的，不会重复编译。
	var mat := ShaderMaterial.new()
	mat.shader = sh
	mat.set_shader_parameter("progress", 0.0)

	var mesh := QuadMesh.new()
	mesh.size = size

	var mi := MeshInstance3D.new()
	mi.name = "%s%s_%d" % [PREFIX, tag, host.get_child_count()]
	mi.mesh = mesh
	mi.material_override = mat
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	# 特效永远不该写深度：它要能被后面的东西盖住，也不该挡住角色
	mi.gi_mode = GeometryInstance3D.GI_MODE_DISABLED
	host.add_child(mi)
	return mi


## 用一条 Tween 把 progress 0→1 走完，然后释放。
##
## `set_ease(EASE_OUT)` 不是装饰：特效的"啪"感来自**前段快、后段慢**。
## 线性或者 EASE_IN 会让它看起来像"慢慢化开"，完全没有打击感。
##
## Tween 挂在**特效节点自己**身上（不是 host）：
## `create_tween()` 会 bind_node，节点离开场景树时这条 Tween 就随之暂停/销毁。
## 挂 host 的话，提前清特效（`_clear_vfx` / 重开一局）之后 Tween 还在跑，
## 每一步都会去碰已经释放的材质和节点 —— 引擎会连刷
## `Lambda capture at index 0 was freed`。这是真踩过的。
static func _drive(host: Node3D, node: MeshInstance3D, mat: ShaderMaterial,
		life: float) -> void:
	var tw := node.create_tween()
	tw.tween_method(func(v: float) -> void:
		if is_instance_valid(mat):
			mat.set_shader_parameter("progress", v),
		0.0, 1.0, life).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	tw.tween_callback(func() -> void:
		if is_instance_valid(node):
			node.queue_free())
