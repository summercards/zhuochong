class_name CarryableManager
extends Node3D
## 地面可拾取物的集中管理：确定性分布、统一查询、重开复位。
##
## ---------------------------------------------------------------------------
## 为什么单独一个管理器，而不是让每个箱子自己管自己：
##
##   三个地方都要问"地上有哪些箱子、哪个在我面前、这一拳扫到的箱子里是谁"：
##   角色的拾取判定、角色的攻击判定、投掷出去的箱子砸到谁。
##   把这份名单放在一处，就能保证**三方看到的是同一份名单**；
##   散在各自身上迟早出现"我这边已经打碎了、你那边还当它活着"。
##
## ---------------------------------------------------------------------------
## 为什么是**确定性**分布（固定种子）而不是 `randi()`：
##
##   这个工程里凡是"每局长什么样"的东西都必须可复现 —— 出图验收、冒烟用例、
##   帧级对比全都依赖"同样输入得到同样画面"。箱子摆位会直接改变战斗走向
##   （哪个箱子在谁那一侧、离谁更近），所以它必须是**常量级的确定**。
##   种子写死在这里，等价于把 5 个箱子当成 5 个固定坐标。

## 分布种子。**人定**，取当天的日期规约（和 `DummyAI` 的 20261004 同一套写法），
## 目的是"有种子但不选种子"—— 换个日子重导会得到另一套摆位，仍然是确定的。
const SEED := 20261005

## 场上全部箱子。**顺序即"第几号箱"**，`_homes` 与它一一对应。
var props: Array[Carryable] = []
## 每个箱子的出生点（复位目标）。与 `props` 同序。
var _homes: Array[Vector3] = []


func _ready() -> void:
	build()


# ---------------------------------------------------------------------
# 生成 / 复位
# ---------------------------------------------------------------------
## 按 `GameDB §7` 的档位与数量铺一遍场地。
##
## 位置怎么定（每一步都有出处）：
##   1. 先把 ±STAGE_HALF_WIDTH 均分成 `PROP_COUNT` 段，每段中心放一个 ——
##      保证横向铺满、且相邻箱子间距相等（不会两个箱子叠在一起）；
##   2. 再让到边界留出一个**推箱间距**（§4 的 `PUSH_SEPARATION`）——
##      否则最边上的箱子会卡在边界亮线里，视觉上和"墙"重叠；
##   3. 最后加一点**确定性抖动**（±半个受击体半径），让它看起来是"散落的"
##      而不是"排队摆的"。抖动幅度用受击体半径当尺子，不另填数。
##
## 档位分配：`i % 三档` —— 5 个箱子会得到 1/2/3/1/2 三档各出现，
## 一眼就能看出"小件 / 中件 / 大件"同时在场上。
func build() -> void:
	_clear()
	var rng := RandomNumberGenerator.new()
	rng.seed = SEED

	var n := maxi(1, GameDB.PROP_COUNT)
	var tiers: Array = GameDB.PROP_SIZE_K
	var half: float = GameDB.STAGE_HALF_WIDTH - GameDB.PUSH_SEPARATION
	var jitter_k: float = GameDB.HURTBOX_RADIUS * 0.5

	for i in n:
		var t: float = (float(i) + 0.5) / float(n)        # 0.1, 0.3, 0.5, 0.7, 0.9
		var x: float = (t * 2.0 - 1.0) * half
		x += rng.randf_range(-jitter_k, jitter_k)

		var tier: int = i % maxi(1, tiers.size())
		var p := Carryable.new()
		p.name = "Prop%d" % i
		# **先 setup 再 add_child**：`_ready` 会按 `size_m` 搭外观和碰撞盒，
		# 所以尺寸必须在入树之前就位（第一版顺序写反，五个箱子全长一个样）。
		p.setup(float(GameDB.prop_sizes[tier]), tier)
		add_child(p)
		p.place_at(Vector3(x, 0.0, 0.0))

		props.append(p)
		_homes.append(p.home)

	print("[Carryables] 铺了 %d 个箱子，边长 %s m，出生点 %s" % [
		props.size(),
		str(props.map(func(p: Carryable) -> float: return p.size_m)),
		str(_homes.map(func(v: Vector3) -> String: return "%.2f" % v.x))])


## 重开一局：所有箱子回到出生点、满耐久、可拾取。
## **必须由 Game 在每个回合开头调用** —— 否则上一局打碎的箱子会把
## "已碎 + 倒计时"的状态带进新回合。
func reset_all() -> void:
	for i in props.size():
		var p := props[i]
		if p != null and is_instance_valid(p):
			p.place_at(_homes[i])


func _clear() -> void:
	for p in props:
		if p != null and is_instance_valid(p):
			p.queue_free()
	props.clear()
	_homes.clear()


# ---------------------------------------------------------------------
# 查询
# ---------------------------------------------------------------------
## 在"贴地交互带"里找箱子 —— 拾取和"打地上的箱子"共用这一条查询。
##
## 带子的定义（见 `GameDB §7` 的两段注释）：
##   · 横向：以 `center` 为原点、朝 `facing` 方向 `reach` 处，厚 `depth`、宽 `span`；
##   · 纵向：`[0, 2 × prop_pickup_height]` —— 从地面到"手够到地面的高度"翻一倍，
##           正好罩住三档箱子。
##
## 为什么纵向要**换成**这条带子、而不是沿用攻击自己的判定高度：
## 拳脚的判定点都在半身高以上（轻拳打在胸口），而箱子躺在地上 ——
## 沿用原高度的话"站着出拳打不到地上的箱子"，用户会认为箱子根本打不碎。
##
## 返回的箱子里**不包含**拿在手上的那个（手持时它的碰撞层被置 0，
## 直接查询就找不到它 —— 见 `Carryable._set_active` 的注释）。
func query_ground(reach: float, center: Vector3, facing: int,
		depth: float, span: float) -> Array[Carryable]:
	var out: Array[Carryable] = []
	var h: float = GameDB.prop_pickup_height * 2.0
	if reach <= 0.0 or h <= 0.0:
		return out

	var box := BoxShape3D.new()
	box.size = Vector3(maxf(depth, 0.05), h, maxf(span, 0.05))
	var params := PhysicsShapeQueryParameters3D.new()
	params.shape = box
	params.transform = Transform3D(Basis(), Vector3(
		center.x + float(facing) * reach * 0.5,
		GameDB.prop_pickup_height,
		center.z))
	params.collision_mask = Carryable.LAYER_CARRYABLE
	params.collide_with_areas = true
	params.collide_with_bodies = false

	for hit in get_world_3d().direct_space_state.intersect_shape(params, 16):
		var col: Object = hit.get("collider")
		if col is Area3D and col.has_meta("carryable"):
			var p: Carryable = col.get_meta("carryable")
			if p != null and is_instance_valid(p) and not out.has(p):
				out.append(p)
	return out


## 距 `from` 最近的那个可拾取箱子（按横向距离），够不着就返回 null。
func nearest_pickable(from: Vector3, facing: int) -> Carryable:
	# reach 传两倍：查询盒是"以 0.5·reach 为中心、长 reach"，所以传 2r 得到 [0, 2r]，
	# 再在这里按实际距离筛 —— "够不够得着"的判据只留一处。
	var found := query_ground(GameDB.prop_pickup_reach * 2.0, from, facing,
		GameDB.prop_pickup_reach * 2.0, Fighter.HITBOX_SPAN)
	var best: Carryable = null
	var best_d := INF
	for p in found:
		if not p.is_pickable():
			continue
		var d: float = absf(p.global_position.x - from.x)
		# 箱子自己也有体积：够到它的近侧棱就算够到（不然大箱子反而更难捡）
		if d - p.size_m * 0.5 > GameDB.prop_pickup_reach:
			continue
		if d < best_d:
			best_d = d
			best = p
	return best


## 当前在地上、可被拾取的箱子数量（测试/调试用）。
func pickable_count() -> int:
	var n := 0
	for p in props:
		if p != null and is_instance_valid(p) and p.is_pickable():
			n += 1
	return n


## 当前还在飞的箱子数量（测试/调试用）。
func flying_count() -> int:
	var n := 0
	for p in props:
		if p != null and is_instance_valid(p) and p.state == Carryable.CSt.FLYING:
			n += 1
	return n
