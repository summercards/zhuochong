class_name Carryable
extends Node3D
## 可拾取物：地面上一个能被拿起、抡打、扔出去、也会被打碎的箱子。
##
## ---------------------------------------------------------------------------
## 几个刻意的决定：
##
##  1. **程序化生成，不是资产。** 资产 68 段里没有"箱子"，工程里也没有任何可用的
##     道具 GLB。所以它和 `Stage` / `Vfx` 走同一条路：代码搭出来。
##     尺寸/耐久/弹道全部由 `GameDB §7` 的**实测推算**给出，没有一个数是这里拍脑袋的。
##
##  2. **不是 `CharacterBody3D`，只有 Area3D。** 它不推人、也不挡路 ——
##     只用来自报"我在这里"，好让攻击判定和拾取判定找得到它。
##     交给物理反而会引入"角色被箱子卡住"这类和本项目风格无关的麻烦。
##
##  3. **四个状态，不扩 `Fighter.St`。** 物体的状态是它自己的事：
##         待机(躺地上) / 手持 / 飞行 / 已碎
##     角色那一侧只多一个引用 `Fighter.carrying`，状态机一行没改。
##
##  4. **耐久用"被那一击扣掉多少"记，不另开一套血量。** 挨了 12 伤就掉 12 点 ——
##     和角色用的是同一张伤害表（`GameDB.damage(clip)`），所以"重拳三下碎、轻拳六下碎"
##     这个手感是推导出来的，不是调出来的。

signal broke(what: Carryable)
## 飞行中的物体砸到人。
signal struck(what: Carryable, attacker: Fighter, victim: Fighter, damage: int)

enum CSt { IDLE, HELD, FLYING, BROKEN }

## 物理层：可拾取物。与 project.godot 的 layer_names 第 5 条对应（位掩码 = 1 << (5-1)）。
const LAYER_CARRYABLE := 1 << 4

## 损伤档数（外观分三档：完好 / 开裂 / 濒碎）
const DAMAGE_TIERS := 3

## 手持时追手的逼近速率（1/秒）。**人定**，但它不是手感参数 —— 是"收敛速度"：
## 时间常数 = 1/22 ≈ 45 ms ≈ 2.7 帧。两帧半追上手，肉眼看是"被拎起来"而不是"闪过去"，
## 又不会在出拳时明显落后。取 22 的依据就是"2~3 帧"这个量级。
const HAND_FOLLOW_RATE := 22.0

const COL_OK := Color(0.16, 0.62, 0.42)
const COL_HURT := Color(0.62, 0.52, 0.14)
const COL_CRIT := Color(0.72, 0.24, 0.18)
## 自发光增益按损伤档递增 —— 这个世界里"能量感"全靠自发光 + 辉光，
## 箱子也该遵守；而且开了自发光之后"快碎了"一眼就能看出来。
const GAIN_OK := 0.55
const GAIN_HURT := 0.95
const GAIN_CRIT := 1.45

## 三档尺寸对应的边长（米，由 GameDB 推出来）
var size_m := 0.4
## 尺寸档序号（0/1/2）—— 只影响外观配色，方便一眼区分大小件
var tier := 0
var max_hp := 1
var hp := 1
var state: int = CSt.IDLE
## 谁拿着它 / 谁扔的（投掷物要靠它算出"打谁"和"被谁打"）
var held_by: Fighter = null
var thrower: Fighter = null
## 静止位（复位回这里）
var home := Vector3.ZERO
## 飞行速度（米/秒）。由 GameDB 推出来的初速，落地靠 GameDB 推出来的重力。
var velocity := Vector3.ZERO
## 贴地高度 = 半个边长（中心离地）
var _rest_y := 0.2

var _mesh: MeshInstance3D
var _mat: StandardMaterial3D
var _flash_mat: ShaderMaterial
var _area: Area3D
var _shape: CollisionShape3D
var _broken_left := 0.0
var _flash_left := 0.0
var _flash_total := 0.0


func setup(edge: float, tier_index: int) -> void:
	size_m = edge
	tier = tier_index
	max_hp = GameDB.prop_max_hp
	hp = max_hp
	_rest_y = size_m * 0.5


func _ready() -> void:
	_build_visual()
	_build_area()
	_apply_damage_look()
	# 摆位由 `place_at` 负责；这里只保证"刚造出来就在查询里可见"
	_set_active(true)
	set_physics_process(true)


# ---------------------------------------------------------------------
# 搭建
# ---------------------------------------------------------------------
func _build_visual() -> void:
	# 箱体：一个方块。**不写 Vertex shader** —— 角色用的是 StandardMaterial3D，
	# 这里跟着走同一套（`docs/资产归类.md` 的教训：混两套材质体系迟早对不上光）。
	var mesh := BoxMesh.new()
	mesh.size = Vector3(size_m, size_m, size_m)
	_mat = StandardMaterial3D.new()
	_mat.albedo_color = COL_OK
	_mat.emission_enabled = true
	_mat.emission = COL_OK
	_mat.metallic = 0.25
	_mat.roughness = 0.45
	# 尺寸档越大的箱子转得越明显，避免五个方块一模一样
	_mat.uv1_scale = Vector3(1.0 + float(tier) * 0.4, 1.0 + float(tier) * 0.4, 1.0)

	_mesh = MeshInstance3D.new()
	_mesh.name = "Box"
	_mesh.mesh = mesh
	_mesh.material_override = _mat
	add_child(_mesh)

	# 受击闪白：和角色用同一个材质（一份材质闪全身，这里"全身"就是这个方块）
	_flash_mat = Vfx.flash_material()
	if _flash_mat != null:
		Vfx.apply_overlay(self, _flash_mat)


func _build_area() -> void:
	_shape = CollisionShape3D.new()
	_shape.name = "PropShape"
	var box := BoxShape3D.new()
	box.size = Vector3(size_m, size_m, size_m)
	_shape.shape = box

	_area = Area3D.new()
	_area.name = "PropArea"
	_area.collision_layer = LAYER_CARRYABLE
	_area.collision_mask = 0
	_area.monitoring = false        # 判定用直接空间查询（和 Fighter 的 Hurtbox 同一套做法）
	_area.monitorable = true
	_area.add_child(_shape)
	add_child(_area)
	_area.set_meta("carryable", self)


## 位置：站在地面上（中心离地半个边长）
func place_at(p: Vector3) -> void:
	home = Vector3(p.x, _rest_y, p.z)
	global_position = home
	velocity = Vector3.ZERO
	state = CSt.IDLE
	held_by = null
	thrower = null
	_broken_left = 0.0
	hp = max_hp
	_set_active(true)
	_apply_damage_look()
	clear_flash()


# ---------------------------------------------------------------------
# 外观：三档损伤
# ---------------------------------------------------------------------
## 按剩余耐久选档位。**阈值用等分而不是另填**：三档就是 1/3、2/3 两条线，
## 于是"还剩几成就换样子"这件事不需要额外参数。
func _apply_damage_look() -> void:
	if _mat == null:
		return
	var ratio: float = float(hp) / float(maxf(1, max_hp))
	var stage := DAMAGE_TIERS - 1 - int(floor(ratio * float(DAMAGE_TIERS)))
	stage = clampi(stage, 0, DAMAGE_TIERS - 1)
	var col := COL_OK
	var gain := GAIN_OK
	if stage == 1:
		col = COL_HURT
		gain = GAIN_HURT
	elif stage >= 2:
		col = COL_CRIT
		gain = GAIN_CRIT
	_mat.albedo_color = col
	_mat.emission = col * gain
	# 越破越小一点点：读起来像"被削掉了一圈"。系数由档位直接给，不另设参数。
	if _mesh != null:
		var s := 1.0 - 0.06 * float(stage)
		_mesh.scale = Vector3(s, s, s)


func damage_stage() -> int:
	var ratio: float = float(hp) / float(maxf(1, max_hp))
	return clampi(DAMAGE_TIERS - 1 - int(floor(ratio * float(DAMAGE_TIERS))),
		0, DAMAGE_TIERS - 1)


# ---------------------------------------------------------------------
# 拾取 / 手持 / 投掷
# ---------------------------------------------------------------------
## 能不能被捡起来。飞行中、已碎、已经在别人手上都不行。
func is_pickable() -> bool:
	return state == CSt.IDLE


func can_be_smashed() -> bool:
	return state != CSt.BROKEN


func pick_up(f: Fighter) -> void:
	state = CSt.HELD
	held_by = f
	thrower = null
	velocity = Vector3.ZERO
	_set_active(false)          # 拿在手上时不再参与"地面拾取/被打"的查询


## 手持时每物理帧跟着手走。
##
## 位置 = **手骨的世界坐标**（`hand.R`，与 `Grab_Start` / `Throw` / `Heavy_01`
## 登记的命中点同一根骨头）+ 朝向方向半个边长 —— 让物体落在掌心里而不是嵌进手腕。
## 每帧硬设而不是挂成子节点：挂父节点会连旋转一起继承，方块会跟着手腕翻跟头。
##
## 走向用**指数逼近平滑**而不是瞬移：
##   · 捡起来的瞬间，箱子在脚边（贴地带）而手在 1.13 m 高 —— 直接瞬移会"闪一下"；
##   · 出拳时手在几帧里扫过一米多，硬跟会让箱子像焊在铁棍上。
## 平滑只是给了它一点"重量感"，收尾由 `1 − exp(−k·dt)` 保证**永远收敛**（不会飘）。
func follow_hand(hand_world: Vector3, facing: int, delta: float) -> void:
	if state != CSt.HELD:
		return
	var target := Vector3(
		hand_world.x + float(facing) * size_m * 0.5,
		hand_world.y,
		hand_world.z)
	var t: float = 1.0 - exp(-HAND_FOLLOW_RATE * delta)
	global_position = global_position.lerp(target, t)


## 出手：从 `from` 朝 `dir` 方向平抛出去。`by` = 扔它的人（用来"别砸到自己"）。
## 初速与重力都取自 `GameDB §7`（由 Throw 段自己的出手高度与剩余时长解出来）。
func launch(from: Vector3, dir: int, speed: float, by: Fighter) -> void:
	state = CSt.FLYING
	held_by = null
	thrower = by
	global_position = from
	velocity = Vector3(float(dir) * speed, 0.0, 0.0)
	_set_active(true)


## 从手上滑落（被打了、持箱者被击飞）→ 就地掉在地上。
func drop() -> void:
	if state != CSt.HELD:
		return
	state = CSt.IDLE
	held_by = null
	thrower = null
	global_position.y = _rest_y
	velocity = Vector3.ZERO
	_set_active(true)


# ---------------------------------------------------------------------
# 挨打 / 破碎
# ---------------------------------------------------------------------
## 挨一下（damage 就是那一击的公式伤害 —— 和角色用同一张表）。
## 返回是否被打碎。
func take_hit(damage: int, impact_pos: Vector3, power: float, color: Color) -> bool:
	if state == CSt.BROKEN or damage <= 0:
		return false
	hp = maxi(0, hp - damage)
	# 闪白强度 = "这一下打掉了几成耐久"。
	# 一档损伤 = 耐久 / DAMAGE_TIERS = 63/3 = 21 = 重拳伤害 ⟹ 重拳一下闪满、
	# 轻拳（12）闪 0.57。用的是箱子自己的耐久，不是角色的 FLASH_DAMAGE_FULL ——
	# "快碎了"这件事只有箱子自己知道。
	trigger_flash(float(damage) / (float(maxi(1, max_hp)) / float(DAMAGE_TIERS)))
	Vfx.impact(_vfx_host(), impact_pos, 0.0, power, color)
	_apply_damage_look()
	if hp <= 0:
		_break()
		return true
	return false


func trigger_flash(strength: float) -> void:
	if _flash_mat == null:
		return
	# 和角色的闪白用同一条纪律：够重的命中才闪（擦伤不闪）
	if strength < Fighter.FLASH_MIN_STRENGTH:
		return
	_flash_mat.set_shader_parameter("flash", clampf(strength, 0.0, 1.0))
	_flash_total = 0.14
	_flash_left = _flash_total


func clear_flash() -> void:
	_flash_left = 0.0
	if _flash_mat != null:
		_flash_mat.set_shader_parameter("flash", 0.0)


func flash_strength() -> float:
	if _flash_mat == null:
		return 0.0
	var v: Variant = _flash_mat.get_shader_parameter("flash")
	return float(v) if v != null else 0.0


func _break() -> void:
	state = CSt.BROKEN
	held_by = null
	velocity = Vector3.ZERO
	_set_active(false)
	if _mesh != null:
		_mesh.visible = false

	var g := global_position
	# 碎的两层反馈都复用已验证的特效：一记亮爆点（在物体位置）+ 一圈地面波（贴地）
	Vfx.impact(_vfx_host(), Vector3(g.x, size_m, g.z), 0.0, Vfx.POWER_HEAVY, Vfx.COLOR_HEAVY)
	Vfx.shockwave(_vfx_host(), Vector3(g.x, 0.0, g.z),
		Vfx.SHOCK_RADIUS * 0.42, 0.40, Vfx.COLOR_SHOCK,
		sin(deg_to_rad(absf(Game.CAM_PITCH_DEG))))
	# 复位倒计时：复位间隔 = 擒抱上限 × PROP_RESPAWN_K（见 GameDB §7）
	_broken_left = GameDB.grab_hold_max * GameDB.PROP_RESPAWN_K
	broke.emit(self)


# ---------------------------------------------------------------------
# 每帧
# ---------------------------------------------------------------------
func _physics_process(delta: float) -> void:
	_tick_flash(delta)
	match state:
		CSt.IDLE:
			pass
		CSt.HELD:
			pass            # 位置由 Fighter 每帧写（follow_hand）
		CSt.FLYING:
			_tick_flight(delta)
		CSt.BROKEN:
			_broken_left -= delta
			if _broken_left <= 0.0:
				place_at(home)


func _tick_flight(delta: float) -> void:
	# 平抛：只受 GameDB 推出来的那个重力
	velocity.y -= GameDB.prop_throw_gravity * delta
	global_position += velocity * delta

	# 打人：用和角色一样的直接空间查询（当帧出结果，没有一帧延迟）
	var victim := _query_fighter()
	if victim != null:
		_strike(victim)
		return

	# 落地
	if global_position.y <= _rest_y and velocity.y <= 0.0:
		global_position.y = _rest_y
		velocity = Vector3.ZERO
		state = CSt.IDLE
		return

	# 撞到舞台边界 → 就地停下（不做反弹：反弹会引入"在边界上反复弹"的不确定态）
	if absf(global_position.x) >= GameDB.STAGE_HALF_WIDTH:
		global_position.x = clampf(global_position.x,
			-GameDB.STAGE_HALF_WIDTH, GameDB.STAGE_HALF_WIDTH)
		global_position.y = _rest_y
		velocity = Vector3.ZERO
		state = CSt.IDLE


func _strike(victim: Fighter) -> void:
	var atk := thrower
	# 自己砸到地上/停下之前，先把速度清掉 —— 否则下一帧还会"穿过"人继续飞
	velocity = Vector3.ZERO
	global_position.y = _rest_y
	state = CSt.IDLE

	var dmg: int = GameDB.prop_impact_damage
	if atk != null and is_instance_valid(atk):
		victim.receive_hit(atk, dmg, "Throw")
	Vfx.impact(_vfx_host(), global_position, 0.0, Vfx.POWER_HEAVY, Vfx.COLOR_HEAVY)
	struck.emit(self, atk, victim, dmg)

	# 砸到人自己也受损（同一个冲量）。砸碎在哪都行，这里就地判。
	hp = maxi(0, hp - dmg)
	_apply_damage_look()
	if hp <= 0:
		_break()


## 飞行中撞到谁了（排除扔它的人）。
func _query_fighter() -> Fighter:
	if _area == null:
		return null
	var params := PhysicsShapeQueryParameters3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(size_m, size_m, size_m)
	params.shape = box
	params.transform = Transform3D(Basis(), global_position)
	params.collision_mask = Fighter.LAYER_HURTBOX
	params.collide_with_areas = true
	params.collide_with_bodies = false
	for h in get_world_3d().direct_space_state.intersect_shape(params, 4):
		var col: Object = h.get("collider")
		if col is Area3D and col.has_meta("fighter"):
			var f: Fighter = col.get_meta("fighter")
			if f != thrower:
				return f
	return null


func _tick_flash(delta: float) -> void:
	if _flash_mat == null or _flash_left <= 0.0:
		return
	_flash_left = maxf(0.0, _flash_left - delta)
	var t: float = _flash_left / maxf(_flash_total, 0.0001)
	var v: float = 0.0 if _flash_left <= 0.0 else pow(t, 1.7)
	_flash_mat.set_shader_parameter("flash", v)


## 打开/关闭"我在这里"。
##
## **靠 `collision_layer` 开关，不靠 `monitorable`**：`monitorable` 只管
## Area↔Area 的信号检测，直接空间查询（`intersect_shape`）读的是 broadphase 里的
## 碰撞层 —— 只把 monitorable 置 false 的话，"拿在手上的箱子"仍然会被攻击判定找到，
## 表现为"自己挥空也能把手里箱子打碎"。置 0 就没有这个问题。
func _set_active(on: bool) -> void:
	if _area != null:
		_area.collision_layer = LAYER_CARRYABLE if on else 0
	if _mesh != null and state != CSt.BROKEN:
		_mesh.visible = on or state == CSt.HELD


func _vfx_host() -> Node3D:
	# 特效挂到**舞台根**（和角色同一套做法）：挂自己身上的话，被扔飞时
	# 火花会跟着物体一起飞，看起来像"火花黏在箱子上"。
	var parent := get_parent()
	if parent is Node3D:
		return parent
	return self
