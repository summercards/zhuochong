class_name Fighter
extends CharacterBody3D
## 横版格斗角色控制器。
##
## 设计要点：
##  1. **轴约定有会失败的断言盯着**（见 `_check_axis_contract`）。角色前向 = Godot +Z，
##     侧面朝向由 `Visual.rotation.y = ±PI/2` 决定（相机在 +Z 看向 -Z 时 屏幕右 = 世界 +X）。
##  2. **跳跃是动画驱动的**：A10→A11→A12→A13 顺序播，角色根节点 y 恒为 0，
##     纵向弹道在动画内部的骨盆上。所以这里不做重力。
##  3. **判定点来自实测**：命中盒位置读 `manifest.json` 的 `hit_points`
##     （由 Blender 把骨架摆到命中帧读肢端世界坐标得出），不是估的。
##  4. **打击停顿真的停**：命中瞬间把 AnimationPlayer 的 speed_scale 打成 0，
##     停 `hitstop_frames` 帧 —— 用的就是动画自己登记的帧数。

const MODEL_PATH := "res://assets/characters/bigman/animations/bigman_anim_v001.glb"

## 资产里**未蒙皮**的件数（GLB 里缺 JOINTS_0 的 primitive）。
##
## 这两个 `Jacket_Hem`（下摆）没绑到骨架，所以它们不跟任何骨骼动 —— 会永远停在
## 模型的静止位姿上，在画面里表现为**悬在胸口高度的一片蓝色圆盘**（实测出图确认）。
## 这是登记在案的资产问题（见 docs/资产归类.md 的问题清单）。
##
## 模板必须能看得过去，但**不能靠名字硬编码去删**（那会让将来真正修好后还在遮）。
## 做法：按"是否绑了 skeleton"这个**可验证的信号**隐藏，并且**数一下**。
## 数量对不上就直接炸 —— 将来重导资产万一多出未蒙皮件，这里会先知道。
const UNSKINNED_MESH_COUNT := 2

signal hp_changed(hp: int, max_hp: int)
signal state_changed(label: String)
signal landed_hit(attacker, victim, clip: String, damage: int)
## 抓中的那一下。**和 landed_hit 分开**：
## 抓取本身不产生伤害（伤害在投出去时才结算），所以不能走 `landed_hit`
## 那条路 —— 那条路会往 HUD 上打一个 "-0" 的伤害数字。
signal grabbed(attacker, victim, clip: String)
signal defeated(who)
## 拳脚砸在地面箱子上（箱子不是 Fighter，走不了 landed_hit —— 那条路要一个 Fighter）。
## 单独开一个口子，让 Game 也能给"砸箱子"喂同一套屏幕反馈。
signal hit_prop(attacker, prop, damage: int)

## 状态
enum St { INTRO, IDLE, WALK, RUN, RUN_STOP, TURN, CROUCH, JUMP, ATTACK, GRAB, GRABBED, GUARD, HIT, DOWN, DEAD }
const ST_LABEL := {
	St.INTRO: "演出", St.IDLE: "待机", St.WALK: "行走", St.RUN: "奔跑",
	St.RUN_STOP: "急停", St.TURN: "转身", St.CROUCH: "下蹲", St.JUMP: "跳跃",
	St.ATTACK: "攻击", St.GRAB: "投技", St.GRABBED: "被擒", St.GUARD: "防御",
	St.HIT: "受击", St.DOWN: "倒地", St.DEAD: "死亡",
}
## 英文对照 —— HUD 在加载不到中文字体时用这份（默认字体不含 CJK 字形）。
const ST_LABEL_EN := {
	St.INTRO: "INTRO", St.IDLE: "IDLE", St.WALK: "WALK", St.RUN: "RUN",
	St.RUN_STOP: "BRAKE", St.TURN: "TURN", St.CROUCH: "CROUCH", St.JUMP: "JUMP",
	St.ATTACK: "ATTACK", St.GRAB: "GRAB", St.GRABBED: "HELD", St.GUARD: "GUARD",
	St.HIT: "HITSTUN", St.DOWN: "DOWN", St.DEAD: "K.O.",
}

## 攻击键 -> 起手 clip（后续段由 _resolve_chain 决定）
const ATTACK_STARTER := {
	"light": "Light_01",
	"heavy": "Heavy_01",
	"dash": "Dash_Attack",
	"upper": "Uppercut",
	"low": "Low_Attack",
	"special": "Skill_03",
}
## 轻拳三段连打
const LIGHT_CHAIN := {"Light_01": "Light_02", "Light_02": "Light_03"}
## 跳跃子序列（全部原地，纵向在动画里）
const JUMP_SEQ := ["Jump_Start", "Jump_Up", "Jump_Fall", "Jump_Land"]
const JUMP_IDX_FALL := 2
const JUMP_IDX_LAND := 3
## 跑动跳踢（飞踢）用哪一段空中招式。
##
## **这不是审美选择，是唯一解。** 判定盒以命中点为中心、高 `HITBOX_HEIGHT = 0.65`，
## 覆盖 `[height − 0.325, height + 0.325]`；站在地上的人受击体是 `[0, 1.732]`：
##   空中轻击 命中点 2.1369 → 判定盒 [1.812, 2.462] —— **够不到**（1.812 > 1.732）
##   空中重击 命中点 1.5775 → 判定盒 [1.253, 1.903] —— 够得到 ✅
## 也就是说，用空中轻击做飞踢会**物理上打不中人**。详见 GameDB §8 的完整推算。
const JUMP_KICK_CLIP := "Air_Heavy"
## 骨骼名。骨盆**不叫 `hips`** —— 这份资产的 57 根关节里叫 `pelvis`
## （`find_bone("hips")` 会静默返回 -1，不报错）。
## 这两个名字同时被 `tools/probe_jump.gd` 用着，是同一份实测的出处。
const PELVIS_BONE := "pelvis"
const HAND_BONE := "hand.R"
## 跳跃期间骨盆的世界 Y 峰值抬升量（米）—— `tools/probe_jump.gd` 实测。
##
## 用途：`tools/smoke_probe.gd` 拿它当"受击体抬起量"的参照。**不能直接拿它当抬升量**
## 用：运行时读到的是"当前这一帧的骨盆高度 − 贴地基准"，峰值时刻与实测那一帧未必重合，
## 所以断言给的是容差区间，而不是相等。有了这个数，才说得清"抬了 1.12 m"
## 到底是"照着实测抬的"还是"随便抬了一个数"。
const PELVIS_RISE_PEAK := 1.1236

## 判定盒尺寸（米）。深度 0.40 ≈ 手腕到指节的活动余量；
## 横向 0.85 覆盖角色厚度；高 0.65 ≈ 头到胸。
const HITBOX_DEPTH := 0.40
const HITBOX_HEIGHT := 0.65
const HITBOX_SPAN := 0.85
const HITBOX_BIAS := 0.05
## 碰撞层（与 project.godot 的 layer_names 对应；位掩码 = 1 << (阶数-1)）
const LAYER_HURTBOX := 1 << 2

## 长按方向多久转成奔跑（秒）
const RUN_HOLD_TIME := 0.32
## 连按方向两次的间隔上限（秒）—— 超过就不算"连按"。
##
## 为什么取 0.32：它**就是** `RUN_HOLD_TIME`。这不是巧合 —— 两个触发方式
## （按住 / 连按两下）描述的是同一个意图"我要跑"，所以它们的判定窗口必须是同一段
## 时间，否则会出现"按快一点能跑、按慢一点不能"这种说不清的边界。
const RUN_TAP_WINDOW := RUN_HOLD_TIME
## 状态间交叉淡化时长（秒）
const BLEND_FAST := 0.06
const BLEND_NORMAL := 0.12

## 狂暴（低血量自动触发，展示 E03 剪辑并加伤）
const RAGE_HP_RATIO := 0.30
const RAGE_DAMAGE_SCALE := 1.25

# ---------------------------------------------------------------------
# 投技（抓取 / 擒抱 / 投掷）
# ---------------------------------------------------------------------
## 抓取类招式的两个时刻（**帧号**）：
##   capture = 手伸到位、能把对手扣住的那一帧
##   deliver = 结算的那一帧（伤害与击飞真正落地）。-1 = 不自动结算，
##             转入 `Grab_Hold` 循环等玩家出手。
##
## 每一项都明写"这个数抄自 manifest 的哪个字段"（`*_src`），
## 由 `_check_carry_contract` 逐条回查 —— **不写 src 的数就是拍脑袋的数**，
## 会被门禁炸出来（第一版 skill_02 的 capture 忘了写 src，当场被这条断言抓住）。
##
##   Grab_Start capture ← hit_frame 28（手.R 的可达点就登记在这一帧）
##   Grab_Start deliver ← 无（标准指令投：抓住之后由玩家决定什么时候投）
##   Skill_02   capture ← antic_frame 3（抱摔前摇极短，前摇一结束手就已经在位）
##   Skill_02   deliver ← hit_frame 68（砸下去的那一帧）
const CARRY_MOVES := {
	"Grab_Start": {
		"capture": 28.0, "capture_src": "hit_frame",
		"deliver": -1.0, "deliver_src": "",
	},
	"Skill_02": {
		"capture": 3.0, "capture_src": "antic_frame",
		"deliver": 68.0, "deliver_src": "hit_frame",
	},
}
## 被擒期间被捕者播的姿势。
##
## **资产里没有"被抓住"这一段动画**（68 段全表里没有，已逐条核对）。
## 所以这里用「正面轻受击」的姿态**播到底停在末帧**来表示"被擒住、挣不动"，
## 这是登记在案的替代方案 —— 资产一旦补了对应的段，改这一个常量即可。
const GRABBED_POSE_CLIP := "Hit_Light_F"
## 挣脱成功时双方播的失衡段（用轻受击，见 GRABBED_POSE_CLIP 的说明）。
const GRAB_BREAK_RECOVER_CLIP := "Hit_Light_F"

# ---------------------------------------------------------------------
# 技能（C 族特殊技）与它们的释放特效
# ---------------------------------------------------------------------
## 技能键 -> 起手 clip。
## `Skill_02`（抱摔）是**抓技型**：它自带"抱起人砸下去"，所以不进 ATTACK 状态，
## 而是走抓技流程（见 `CARRY_MOVES`）—— 同一张判定表，两种入口。
const SPECIAL_MOVES := {
	"skill1": "Skill_01",     # 肩撞
	"skill2": "Skill_02",     # 抱摔（抓技型）
	"smash": "Ground_Smash",  # 地面砸击
}
## 大招三段：起手 → 攻击 → 收尾。一段播完自动接下一段。
## 这是资产里唯一登记为"多段流程"的连招（见动画文档 §4.3）。
const ULTIMATE_SEQ := ["Ultimate_Start", "Ultimate_Attack", "Ultimate_End"]
## 蓄力段。按一次演完一整段（不做"按住蓄力"）。
const CHARGE_CLIP := "Charge"

## 招式 → 在**哪一帧**放一记地面冲击波（招式的视觉签名）。
##
## `frame_src` 明写"这个帧抄自 manifest 的哪个字段"，由 `_check_frame_claim`
## 逐条回查 —— 和 `CARRY_MOVES` 用的是同一套纪律：**写死的帧号必须有出处**。
##
## 为什么要单列一张表而不是散在 tick 里：这些是"每个技能长什么样"的唯一出处，
## 放在一处才看得清全套招式，也才能在资产改帧之后被门禁一次性核对。
const GROUND_VFX := {
	"Ground_Smash":    {"frame": 36.0, "frame_src": "hit_frame", "radius_k": 1.00},
	"Skill_01":        {"frame": 36.0, "frame_src": "hit_frame", "radius_k": 0.80},
	"Skill_03":        {"frame": 46.0, "frame_src": "hit_frame", "radius_k": 0.85},
	"Charge":          {"frame": 72.0, "frame_src": "hit_frame", "radius_k": 1.20},
	"Ultimate_Attack": {"frame": 64.0, "frame_src": "last_hit_point", "radius_k": 1.35},
	"Ultimate_End":    {"frame": 10.0, "frame_src": "antic_frame", "radius_k": 1.50},
}

## 闪白的最低强度：低于这个值的命中不闪（理由见 trigger_flash）
const FLASH_MIN_STRENGTH := 0.12
## 闪白强度 = 伤害 / 这个值（封顶 1.0）。取 30 → 12 伤闪 0.40、21 伤闪 0.70、30 伤满闪。
const FLASH_DAMAGE_FULL := 30.0
## `_build_hit_flash` 挂上的网格数量 —— 存下来供自检打印
var _flash_shape_count := 0

@export var is_player := true
@export var start_facing := 1

var hp := 0
var max_hp := 0
var facing := 1
var state: int = St.INTRO
var opponent: Fighter = null
var ai: DummyAI = null

var _visual: Node3D
var _hurtbox: Area3D
var _hurtbox_shape: CollisionShape3D
## 受击闪白：一份共享材质挂在全身所有 MeshInstance3D 的 material_overlay 上。
## 改这一个 uniform 就能闪全身（理由见 vfx_flash.gdshader 头部）。
var _flash_mat: ShaderMaterial
## 闪白残余时间 / 总时长（秒），以及峰值强度
var _flash_left := 0.0
var _flash_total := 0.0
var _flash_peak := 0.0
## 特效挂载点（由 Game 注入舞台根节点）。为空时退化到自己身上 ——
## 那样特效会跟着角色动，效果差但不会崩。
var vfx_host: Node3D = null
var _ap: AnimationPlayer
var _skeleton: Skeleton3D
var _player_input: PlayerInput

var _clip := ""
var _clip_dur := 0.0
var _pending_hits: Array = []
var _hitstop_left := 0
var _pending_chain := ""
var _root_motion_x := 0.0
var _knockback_x := 0.0
var _hold_dir_time := 0.0
var _jump_index := 0
var _jump_air := false
## 跑动跳踢：起跳时置位，到腾空顶点那一拍切进飞踢（见 `_tick_jump`）。
var _kick_pending := false
var _hit_taken_this_clip := false
var _rage_used := false
var _last_damage := 0
var _intro_queue: Array = []
var _down_pending := false
var _knockdown_clip := "Knockdown_B"
var _turn_wait := 0.0

# --- "连按两次方向"起跑 ---
## 上一帧的水平轴（用来识别"本帧是新按下的那一下"）
var _prev_axis := 0.0
## 记着的上一次点按方向（-1/0/+1）与它还剩多久算数
var _tap_dir := 0
var _tap_left := 0.0
## 本帧是否由"连按两次"触发起跑（由 `_tick_run_tap` 每帧重算，状态机读它）
var _run_tap_fired := false

# --- 可拾取物（箱子）---
## 场上箱子的集中管理器。由 Game 注入（和 `vfx_host` 一样）—— Fighter 不自己去
## `get_node("../Carryables")`：兄弟节点的路径是场景的事，不该写进角色里。
var carryables: CarryableManager = null
## 我手上拿着的箱子（空手为 null）。**只加这一个引用字段，不扩 `St` 枚举** ——
## 手持是"身体状态"的一种修饰，不是一套新的状态机（见 carryable.gd 头部）。
var carrying: Carryable = null
## 本套 `Grab_Start` 抓的是箱子（而不是人）。抓取判定帧上按它分流。
var _carry_prop := false
## 本套 `Throw` 扔的是箱子（而不是人）。结算帧上按它分流。
var _prop_throw := false

# --- 跳跃期间的受击体抬升（GameDB §8）---
## 骨盆骨骼下标 / 手骨下标（`_ready` 里解析一次）
var _pelvis_idx := -1
var _hand_idx := -1
## 骨盆的"贴地基准"世界 Y（米）。**在真正播 Idle_01 的时候采样**，
## 不能拿静止位姿当基准 —— 静止位姿是 0.9000 m，而 Idle_01 是 0.8293 m，
## 差 7 cm 会让站着不动的人也"浮空"7 cm。
var _pelvis_ground_y := GameDB.PELVIS_GROUND_FALLBACK
var _pelvis_sampled := false

# --- 投技状态（St.GRAB / St.GRABBED 共用）---
## 我手上抓着的人（我为抓取方时非空）
var holding: Fighter = null
## 抓着我的人（我为被捕方时非空）。两边必须**互为引用**，
## 任一方解除时都要把对方那一侧清掉 —— 否则会出现"一方以为还抓着、
## 另一方已经跑了"的幽灵状态（推箱胶着、位置抖动都是它的症状）。
var grabbed_by: Fighter = null
## 当前这套抓技正在演的段（清单名）：Grab_Start / Grab_Hold / Throw / Skill_02
var _grab_move := ""
## 抓取判定帧 / 结算帧；-1 = 不适用
var _grab_capture_frame := -1.0
var _grab_deliver_frame := -1.0
## 本套抓技是否已经做过抓取判定（判定只做一次，不能每帧都试）
var _grab_caught := false
## 已经抱了多久（秒）
var _grab_hold := 0.0
## 被捕者已经按了多少下挣脱键
var _grab_mash := 0
## 攻击的取消窗口内按下了抓取键 —— 播完这一段就转抓技
var _pending_grab := false
## 自检用：本局抓中过几次 / 投出去过几次
var grabs_done := 0
var throws_done := 0

# --- 技能（C 族）状态 ---
## 大招播到第几段；-1 = 没在大招里
var _ult_index := -1
var _ult_active := false
## 蓄力/大招的光环节点（挂在**自己**身上，见 Vfx.aura）
var _aura_node: Node3D = null
## 当前光环覆盖哪些段 —— `_play` 切到集合外的段时自动收掉
var _aura_clips: Array[String] = []
## 本段招式的"签名冲击波"是否已经放过（每次 `_play` 重置）
var _ground_vfx_fired := false


func _ready() -> void:
	_visual = get_node_or_null("Visual") as Node3D
	_hurtbox = get_node_or_null("Hurtbox") as Area3D
	assert(_visual != null, "Fighter 缺少 Visual 子节点")
	assert(_hurtbox != null, "Fighter 缺少 Hurtbox 子节点")

	var model: PackedScene = load(MODEL_PATH)
	assert(model != null, "找不到角色模型: %s" % MODEL_PATH)
	var root: Node3D = model.instantiate()
	_visual.add_child(root)

	var ap := _visual.find_child("AnimationPlayer", true, false) as AnimationPlayer
	var sk := _visual.find_child("Skeleton3D", true, false) as Skeleton3D
	assert(ap != null, "模型里没有 AnimationPlayer")
	assert(sk != null, "模型里没有 Skeleton3D")
	_ap = ap
	_skeleton = sk
	# 帧级确定性：状态机跑在 _physics_process，动画也必须跑物理帧。
	# 否则动画跟的是渲染帧，判帧会随帧率漂移 —— 格斗游戏最忌讳这个。
	_ap.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_PHYSICS

	_check_axis_contract()
	_hide_unskinned_meshes(root)
	_apply_loop_modes()
	_check_carry_contract()
	_check_ground_vfx_contract()
	_check_prop_contract()
	_build_hurtbox()
	_hurtbox.set_meta("fighter", self)
	_build_hit_flash(root)
	# 手持挂点与纵向抬升都要读骨骼，这里解析一次。
	# 找不到就保持 -1：所有用到的地方都按"读数 0"退化，不会崩 —— 但会 push_error，
	# 因为那意味着资产换了骨架，是本工程必须知道的事。
	_pelvis_idx = _skeleton.find_bone(PELVIS_BONE)
	_hand_idx = _skeleton.find_bone(HAND_BONE)
	if _pelvis_idx < 0:
		push_error("[Fighter] 找不到骨骼 %s（纵向抬升会失效）" % PELVIS_BONE)
	if _hand_idx < 0:
		push_error("[Fighter] 找不到骨骼 %s（手持挂点会失效）" % HAND_BONE)

	max_hp = GameDB.MAX_HP
	hp = max_hp
	facing = start_facing
	_set_facing(facing)
	hp_changed.emit(hp, max_hp)
	state = St.INTRO


## 隐藏**未蒙皮**的网格（不跟骨骼动的那几件）。
##
## 判据是引擎给的可验证信号：Godot 的 glTF 导入器只给蒙皮网格设置 `skeleton`。
## 没设 = GLB 里缺 JOINTS_0 = 不会跟着任何骨骼动。
##
## 注意：`MeshInstance3D.skeleton` 是 **NodePath**（不是 Node 引用），
## 空值是一个**空 NodePath**，`== null` 恒为 false —— 必须用 `is_empty()`。
## （第一版写成 `== null`，结果一个都没匹配到，被下面那条数量断言当场抓住。）
##
## 为什么不写死名字：资产修好后（把下摆绑进骨架）这些件应该自动回来，
## 而写死名字会一直遮着。判据跟着资产状态走，人不用记得改代码。
func _hide_unskinned_meshes(root: Node) -> void:
	var nodes: Array[MeshInstance3D] = []
	_collect_unskinned(root, nodes)
	var names: Array[String] = []
	for mi in nodes:
		mi.visible = false
		names.append(String(mi.name))
	if nodes.size() != UNSKINNED_MESH_COUNT:
		push_error("[Fighter] 未蒙皮网格从 %d 个变成了 %d 个：%s —— 资产重导过？"
			% [UNSKINNED_MESH_COUNT, nodes.size(), str(names)])
	assert(nodes.size() == UNSKINNED_MESH_COUNT,
		"未蒙皮网格数量变了（期望 %d，实得 %d）：%s" % [
			UNSKINNED_MESH_COUNT, nodes.size(), str(names)])
	print("[Fighter] 已隐藏 %d 个未蒙皮网格（不跟骨骼动）: %s" % [nodes.size(), str(names)])


func _collect_unskinned(node: Node, out: Array[MeshInstance3D]) -> void:
	var mi := node as MeshInstance3D
	if mi != null and mi.mesh != null and mi.skeleton.is_empty():
		out.append(mi)
	for c in node.get_children():
		_collect_unskinned(c, out)


## 会失败的断言：如果哪天导出轴向变了，这里必须炸。
func _check_axis_contract() -> void:
	var names := ["toe.L", "toe.R", "eye.L", "eye.R"]
	var idx := {}
	for n in names:
		idx[n] = _skeleton.find_bone(n)
		if idx[n] < 0:
			push_error("[Fighter] 找不到骨骼 %s，轴向契约无法校验" % n)
			return
	var toe_l: Vector3 = _skeleton.get_bone_global_rest(idx["toe.L"]).origin
	var toe_r: Vector3 = _skeleton.get_bone_global_rest(idx["toe.R"]).origin
	var eye_l: Vector3 = _skeleton.get_bone_global_rest(idx["eye.L"]).origin
	var eye_r: Vector3 = _skeleton.get_bone_global_rest(idx["eye.R"]).origin

	var toe_fwd := (toe_l.z + toe_r.z) * 0.5
	if toe_fwd <= 0.05:
		push_error("轴向契约破裂：脚尖 z=%.3f，应 > 0（角色正面应当是 Godot +Z）" % toe_fwd)
	assert(toe_fwd > 0.05,
		"轴向契约破裂：脚尖 z=%.3f，应 > 0（角色正面应当是 Godot +Z）" % toe_fwd)
	if absf(eye_l.z - eye_r.z) >= 0.02:
		push_error("轴向契约破裂：双眼 z 不等（%.3f vs %.3f）" % [eye_l.z, eye_r.z])
	assert(absf(eye_l.z - eye_r.z) < 0.02, "轴向契约破裂：双眼 z 不等")
	if eye_l.x * eye_r.x >= 0.0:
		push_error("轴向契约破裂：双眼 x 同号，左右没分在 X 轴上")
	assert(eye_l.x * eye_r.x < 0.0, "轴向契约破裂：双眼 x 同号")
	print("[Fighter] 轴向契约通过：前=+Z 左=+X 上=+Y（toe_z=%.3f eye_z=%.3f）" % [toe_fwd, eye_l.z])


## 受击闪白：把一份共享材质挂成**全身所有网格**的 material_overlay。
##
## 这里刻意**不**逐个改材质的 emission，理由见 vfx_flash.gdshader：
## 17 个材质逐个备份/还原太容易出错，而 overlay 是加一层、摘一层，天然可逆。
##
## `apply_overlay` 返回挂上的网格数量，用它做断言 —— 资产重新导出后
## 如果网格结构变了（比如那两件未蒙皮的件被修好合并了），这里会立刻发现。
func _build_hit_flash(root: Node) -> void:
	_flash_mat = Vfx.flash_material()
	assert(_flash_mat != null, "受击闪白材质创建失败（着色器加载不了？）")
	var n := Vfx.apply_overlay(root, _flash_mat)
	assert(n > 0, "受击闪白没有挂到任何网格上 —— 模型结构变了？")
	_flash_shape_count = n


## 触发一次闪白。strength 0~1，duration 是完整衰减时间（秒）。
##
## 阈值：strength < 0.12 直接忽略。擦伤式的小命中如果也闪，屏幕会一直花，
## 反而把重击的闪白淹掉 —— 闪白是**稀缺资源**，只在够重的命中上用。
func trigger_flash(strength: float, duration: float = 0.14) -> void:
	if _flash_mat == null:
		return
	var s := clampf(strength, 0.0, 1.0)
	if s < FLASH_MIN_STRENGTH:
		return
	# 取最大值而不是覆盖：连续被连打时不能让后一记把前一记闪白"缩短"
	if s > _flash_peak or _flash_left <= 0.0:
		_flash_peak = s
		_flash_total = maxf(duration, 0.01)
		_flash_left = _flash_total
		# **立即写 uniform，不等下一个 _tick_flash。**
		# 命中判定发生在 _physics_process 里，如果等到下一帧才亮，
		# 闪白就会比命中晚一帧 —— 打击感里"晚一帧"等于没有。
		_flash_mat.set_shader_parameter("flash", s)


## 立刻清掉闪白。
##
## **回合重开必须调它。** 上一回合末尾角色可能正亮着（KO 那一击的闪白还在衰减），
## 不清的话新回合开场双方是白的 —— 实测就是这个症状（被冒烟用例抓出来）。
func clear_flash() -> void:
	_flash_left = 0.0
	_flash_peak = 0.0
	if _flash_mat != null:
		_flash_mat.set_shader_parameter("flash", 0.0)


## 当前闪白强度（测试/调试用）
func flash_strength() -> float:
	if _flash_mat == null:
		return 0.0
	var v: Variant = _flash_mat.get_shader_parameter("flash")
	return float(v) if v != null else 0.0


func _tick_flash(delta: float) -> void:
	if _flash_mat == null or _flash_left <= 0.0:
		return
	_flash_left = maxf(0.0, _flash_left - delta)
	var t: float = _flash_left / _flash_total
	# pow(,1.7)：前段压住、后段飞快收掉，比线性更像"曝光一下"。
	# 线性的尾段会在角色身上留一层擦不掉的灰白。
	var v: float = 0.0 if _flash_left <= 0.0 else _flash_peak * pow(t, 1.7)
	_flash_mat.set_shader_parameter("flash", v)


## 受击体：尺寸**不由场景里写死**，而是从 GameDB 的实测常量生成。
## 场景里的 Hurtbox 只是一个空 Area3D —— 这样"身体多大"只有一个出处。
func _build_hurtbox() -> void:
	var cap := CapsuleShape3D.new()
	cap.radius = GameDB.HURTBOX_RADIUS
	cap.height = GameDB.HURTBOX_HEIGHT
	_hurtbox_shape = CollisionShape3D.new()
	_hurtbox_shape.name = "HurtShape"
	_hurtbox_shape.shape = cap
	_hurtbox_shape.position = Vector3(0.0, GameDB.HURTBOX_HEIGHT * 0.5, 0.0)
	_hurtbox.add_child(_hurtbox_shape)

	_hurtbox.collision_layer = LAYER_HURTBOX
	_hurtbox.collision_mask = 0
	_hurtbox.monitoring = false      # 判定用直接空间查询，不接 Area 信号
	_hurtbox.monitorable = true


## 下蹲时受击体变矮（用的是下蹲姿态的实测全高），
## 腾空时受击体跟着骨盆抬起来（纵向立体化，见 GameDB §8）。
##
## **抬的是受击体，不是根节点。** 跳跃是动画驱动的：根节点 y 恒为 0，
## 弹道全在骨盆上。如果再给根节点加一份世界位移，人就会飞两倍高。
## 正确做法就是这里 —— 身体在哪儿，被打的判定就在哪儿。
func _sync_hurtbox_height() -> void:
	if _hurtbox_shape == null:
		return
	_sample_pelvis_ground()
	var want: float = GameDB.HURTBOX_HEIGHT_CROUCH if state == St.CROUCH else GameDB.HURTBOX_HEIGHT
	var cap := _hurtbox_shape.shape as CapsuleShape3D
	if cap != null and not is_equal_approx(cap.height, want):
		cap.height = want
	# 位置**每帧写**（不像高度那样只在变了才写）：抬升量是连续变化的，
	# 而且胶囊高度变化时这个式子也要跟着变 —— 与其维护两个"什么时候要更新"的条件，
	# 不如无条件写一个纯函数，永远不会有脏值。
	_hurtbox_shape.position.y = want * 0.5 + _air_lift()


## 当前受击体该被抬高多少（米）。贴地时为 0。
##
## 判据只有一条：**骨盆相对它自己的贴地基准抬了多少**。
## 低于 `AIRBORNE_RISE_MIN` 视为贴地 —— 站姿各段之间有几毫米的起伏，
## 那不该被读成"浮空"。
func _air_lift() -> float:
	if _pelvis_idx < 0:
		return 0.0
	var rise: float = _bone_world_y(_pelvis_idx) - _pelvis_ground_y
	return rise if rise > GameDB.AIRBORNE_RISE_MIN else 0.0


## 采样一次骨盆的贴地基准。
##
## 什么时候采：**真正在播 Idle_01 且已经淡入完成**时。
##   · 不能拿静止位姿（0.9000 m）当基准 —— Idle_01 是 0.8293 m，差 7 cm；
##   · 不能拿刚 `_play` 完那一帧 —— 那时候 `BLEND_NORMAL` 的交叉淡化还没走完，
##     骨架上的姿态是"上一段 ←→ Idle"的混合值，测出来也不是 Idle 的高度。
## 采样一次就够（基准是骨架的属性，跟对局无关），所以用一个 bool 锁住。
func _sample_pelvis_ground() -> void:
	if _pelvis_sampled or _pelvis_idx < 0:
		return
	if state != St.IDLE or _clip != "Idle_01":
		return
	if _current_frame() < BLEND_NORMAL * 60.0:
		return
	_pelvis_ground_y = _bone_world_y(_pelvis_idx)
	_pelvis_sampled = true


## 某根骨骼的**世界** Y（含 Visual 节点的旋转，所以是真·世界坐标）。
func _bone_world_y(idx: int) -> float:
	return _bone_world_pos(idx).y


## 某根骨骼的世界坐标。`global_transform * bone_global_pose` —— 和 `tools/probe_jump.gd`
## 用的是同一个式子（那份探针是所有这些数值的出处，两处必须一致）。
func _bone_world_pos(idx: int) -> Vector3:
	if _skeleton == null or idx < 0:
		return Vector3.ZERO
	return (_skeleton.global_transform * _skeleton.get_bone_global_pose(idx)).origin


## 打击停顿：由 Game 在命中时对**双方**同时调用（对等反馈）。
func apply_hitstop(frames: int) -> void:
	if frames > 0:
		_hitstop_left = maxi(_hitstop_left, frames)


## manifest 是"哪段循环"的权威 —— 覆盖导入时带的 loop 标记。
## 同时这里也是"清单名 → 引擎名"这条隐形契约的**校验点**：
## 只要有一清单 clip 在 AnimationPlayer 里找不到（含修正表），就直接炸。
func _apply_loop_modes() -> void:
	var missing: Array[String] = []
	for name in GameDB.clips.keys():
		var engine := GameDB.engine_name(name)
		if not _ap.has_animation(engine):
			missing.append("%s → %s" % [name, engine])
			continue
		var a: Animation = _ap.get_animation(engine)
		a.loop_mode = Animation.LOOP_LINEAR if GameDB.is_loop(name) else Animation.LOOP_NONE

	# 反向：引擎里有、清单里没有的（多出来的动画没人管）
	var orphan: Array[String] = []
	for engine in _ap.get_animation_list():
		var known := false
		for name in GameDB.clips.keys():
			if GameDB.engine_name(name) == engine:
				known = true
				break
		if not known:
			orphan.append(String(engine))

	if not orphan.is_empty():
		push_warning("[Fighter] 引擎里有清单外的动画: %s" % str(orphan))
	if not missing.is_empty():
		push_error("[Fighter] 清单里有 %d 段动画在引擎里找不到: %s" % [missing.size(), str(missing)])
	assert(missing.is_empty(),
		"清单↔引擎 动画名契约破裂（%d 段）：%s —— 检查 GameDB.ENGINE_NAME_FIXUPS" % [
			missing.size(), str(missing)])
	print("[Fighter] 动画名契约通过：%d 段清单 clip 全部解析到引擎动画（修正 %d 条）" % [
		GameDB.clips.size(), GameDB.engine_name_fixups.size()])


## 会失败的断言：`CARRY_MOVES` 里写死的两个帧号必须等于 manifest 的实测值。
##
## 为什么值得专门盯一下：抓技的"抓住"和"结算"两个时刻如果和动画对不上，
## 表现是**打了人却没抓住**（判定提前于手）或者**手已经收回来了才扣住人**（判定滞后），
## 而且两种症状都不报错 —— 只能靠肉眼。资产一旦重导（帧数变了），这里立刻炸。
func _check_carry_contract() -> void:
	var bad: Array[String] = []
	for clip in CARRY_MOVES.keys():
		var cfg: Dictionary = CARRY_MOVES[clip]
		bad.append_array(_check_frame_claim(clip, cfg, "capture"))
		bad.append_array(_check_frame_claim(clip, cfg, "deliver"))
	if GameDB.grab_reach <= 0.0:
		bad.append("实测抓取距离为 0（manifest 里 Grab_Start 没有 hit_points？）")
	if GameDB.grab_hold_max <= 0.0:
		bad.append("擒抱上限为 0（manifest 里没有 Grab_Hold？）")
	if not bad.is_empty():
		push_error("[Fighter] 抓技契约破裂：%s" % str(bad))
	assert(bad.is_empty(), "抓技契约破裂：%s —— 检查 CARRY_MOVES 与 manifest" % str(bad))
	print("[Fighter] 抓技契约通过：%d 套抓技的判定帧全部对上实测（抓取手可达 %.3f m）" % [
		CARRY_MOVES.size(), GameDB.grab_reach])


## 会失败的断言：`GROUND_VFX` 里每个技能登记的"签名帧"必须等于 manifest 的实测值。
## 理由同 `_check_carry_contract` —— 特效如果比判定早/晚几帧，看起来就是"打空气"。
func _check_ground_vfx_contract() -> void:
	var bad: Array[String] = []
	for clip in GROUND_VFX.keys():
		var cfg: Dictionary = GROUND_VFX[clip]
		bad.append_array(_check_frame_claim(clip, cfg, "frame"))
		# 半径系数是**人定的**（没有数据来源），但必须落在合理区间里：
		# 系数为 0 等于不放，系数太大（>1.6）会盖满整个画面（第一版试过 1.42 就已经满屏）。
		var rk: float = float(cfg.get("radius_k", 1.0))
		if rk <= 0.0 or rk > 1.6:
			bad.append("%s 的冲击波半径系数 %.2f 超出 (0, 1.6]" % [clip, rk])
	if not bad.is_empty():
		push_error("[Fighter] 技能特效契约破裂：%s" % str(bad))
	assert(bad.is_empty(), "技能特效契约破裂：%s —— 检查 GROUND_VFX 与 manifest" % str(bad))
	print("[Fighter] 技能特效契约通过：%d 个技能登记的签名帧全部对上实测" % GROUND_VFX.size())


## 会失败的断言：`§7` 那一整套"道具推算"的每一个数都必须等于它声明的出处。
##
## 为什么值得单列一条：这套数的特点是**全部由别的实测值乘/除出来**——
## 尺寸 = 受击体半径 × 倍率、耐久 = 重拳伤害 × 3、拾取距离 = 抓取距离、
## 投掷弹道 = Throw 的手高与剩余时间反解。既然"来源"是别的实测值，
## 就必须能被机械回查；否则资产一改（帧数变了、手高变了），
## 这里会**悄悄**留下一批不再成立的数（对着旧资产的箱子尺寸、旧手高的弹道），
## 而表现上只是"扔得有点怪"，根本不会报错。
func _check_prop_contract() -> void:
	var bad: Array[String] = []

	# --- 1. 尺寸：受击体半径 × 三档倍率（逐档核） ---
	if GameDB.prop_sizes.size() != GameDB.PROP_SIZE_K.size():
		bad.append("尺寸档数 %d ≠ 倍率档数 %d" % [
			GameDB.prop_sizes.size(), GameDB.PROP_SIZE_K.size()])
	else:
		for i in GameDB.prop_sizes.size():
			var want: float = GameDB.HURTBOX_RADIUS * float(GameDB.PROP_SIZE_K[i])
			if absf(GameDB.prop_sizes[i] - want) > 0.0005:
				bad.append("第 %d 档边长 %.4f ≠ 受击体半径 %.3f × %.1f = %.4f" % [
					i, GameDB.prop_sizes[i], GameDB.HURTBOX_RADIUS,
					float(GameDB.PROP_SIZE_K[i]), want])

	# --- 2. 耐久：重拳伤害 × 打几下（"多次才坏"这条要求的落点） ---
	var heavy: int = GameDB.damage("Heavy_01")
	if GameDB.prop_max_hp != heavy * GameDB.PROP_HITS_TO_BREAK:
		bad.append("耐久 %d ≠ 重拳 %d × %d 下" % [
			GameDB.prop_max_hp, heavy, GameDB.PROP_HITS_TO_BREAK])
	if heavy <= 0:
		bad.append("重拳伤害为 0（manifest 里 Heavy_01 没有命中点？）")
	# 容器伤害必须**正好**是"一下重拳"：这样"打箱子"与"拿箱子打人"是同一个冲量，
	# 也才能保证"重拳 3 下碎"与"手持抡 3 下碎"是同一个数。
	if GameDB.prop_impact_damage != heavy:
		bad.append("容器伤害 %d ≠ 一次重拳 %d（两者本该是同一个冲量）" % [
			GameDB.prop_impact_damage, heavy])

	# --- 3. 拾取几何：距离 = 抓取距离，高度 = 手砸到地面的实测高度 ---
	if not is_equal_approx(GameDB.prop_pickup_reach, GameDB.grab_reach):
		bad.append("拾取距离 %.4f ≠ 抓取距离 %.4f（同一个伸手手势）" % [
			GameDB.prop_pickup_reach, GameDB.grab_reach])
	var smash_h: float = GameDB.first_hit_height("Ground_Smash")
	if not is_equal_approx(GameDB.prop_pickup_height, smash_h):
		bad.append("贴地带高度 %.4f ≠ Ground_Smash 手地接触高度 %.4f" % [
			GameDB.prop_pickup_height, smash_h])
	# 带上沿必须罩得住**最大**那档箱子 —— 否则最大的箱子站着打不碎。
	# （这条是"贴地带"这个设计成立的前提，所以单独断言。）
	if GameDB.prop_sizes.size() > 0:
		var biggest: float = 0.0
		for s in GameDB.prop_sizes:
			biggest = maxf(biggest, s)
		var band_top: float = GameDB.prop_pickup_height * 2.0
		if band_top < biggest:
			bad.append("贴地带带上沿 %.4f 罩不住最大箱子 %.4f" % [band_top, biggest])

	# --- 4. 投掷弹道：出手高 = Throw 的手高；重力由"平抛恰好落地"唯一解出 ---
	var throw_h: float = GameDB.first_hit_height("Throw")
	if not is_equal_approx(GameDB.prop_throw_release_height, throw_h):
		bad.append("出手高 %.4f ≠ Throw 判定帧手高 %.4f" % [
			GameDB.prop_throw_release_height, throw_h])
	var hf: Variant = GameDB.hit_frame("Throw")
	var tf: Array = GameDB.frames("Throw")
	if hf == null or tf.size() < 2:
		bad.append("Throw 缺少 hit_frame 或 frames —— 弹道算不出来")
	elif GameDB.prop_throw_release_height > 0.0:
		var t: float = (float(tf[1]) - float(hf)) / 60.0
		if t <= 0.0:
			bad.append("Throw 出手帧 %.0f 不在 [%s] 之内" % [float(hf), str(tf)])
		else:
			var g_want: float = 2.0 * GameDB.prop_throw_release_height / (t * t)
			if absf(GameDB.prop_throw_gravity - g_want) > 0.02:
				bad.append("重力 %.3f ≠ 2h/t² = 2×%.4f/%.4f² = %.3f" % [
					GameDB.prop_throw_gravity, GameDB.prop_throw_release_height, t, g_want])
			var v_want: float = GameDB.throw_flight / t
			if absf(GameDB.prop_throw_speed - v_want) > 0.02:
				bad.append("初速 %.3f ≠ throw_flight/t = %.4f/%.4f = %.3f" % [
					GameDB.prop_throw_speed, GameDB.throw_flight, t, v_want])

	# --- 5. 跳踢选段：为什么只能是 `JUMP_KICK_CLIP`（几何上的唯一解） ---
	# 判定盒以命中点为中心、高 HITBOX_HEIGHT，所以它覆盖
	# [hit_height − H/2, hit_height + H/2]。站着的人受击体顶在 HURTBOX_HEIGHT。
	# 只有"盒的下沿低于站立顶"的空中招才够得到站地上的人。
	# —— 这条推论就是当初选 Air_Heavy 而不是 Air_Light 的全部理由，
	#    所以它必须被写成断言：资产一改，这里立刻炸而不必靠人回想。
	if not GameDB.clips.has(JUMP_KICK_CLIP):
		bad.append("跳踢段 %s 不在 manifest clips 里" % JUMP_KICK_CLIP)
	else:
		var stand_top: float = GameDB.HURTBOX_HEIGHT
		var kick_bottom: float = _hit_bottom(JUMP_KICK_CLIP)
		if kick_bottom >= stand_top:
			bad.append("跳踢段 %s 判定盒下沿 %.4f ≥ 站立受击体顶 %.4f —— 够不到站地上的人" % [
				JUMP_KICK_CLIP, kick_bottom, stand_top])
		# 反过来确认"唯一解"这个说法：另一个空中拳（Air_Light）确实够不到。
		if GameDB.clips.has("Air_Light"):
			var light_bottom: float = _hit_bottom("Air_Light")
			if light_bottom < stand_top:
				bad.append("Air_Light 判定盒下沿 %.4f < 站立顶 %.4f —— 它其实也够得到，" % [
					light_bottom, stand_top]
					+ "「只能选 %s」这条推论不再成立，注释该改了" % JUMP_KICK_CLIP)

	if not bad.is_empty():
		push_error("[Fighter] 道具契约破裂：%s" % str(bad))
	assert(bad.is_empty(), "道具契约破裂：%s —— 检查 GameDB §7/§8 与 manifest" % str(bad))
	print("[Fighter] 道具契约通过：尺寸 %s m / 耐久 %d(重拳 %d×%d) / 拾取 %.3f m / 出手高 %.4f m / 跳踢 %s" % [
		str(GameDB.prop_sizes), GameDB.prop_max_hp, heavy, GameDB.PROP_HITS_TO_BREAK,
		GameDB.prop_pickup_reach, GameDB.prop_throw_release_height, JUMP_KICK_CLIP])


## 某段动画第一个命中点在**纵向**上覆盖到的下沿（米）= 命中高度 − 判定盒半高。
##
## 用途见 `_check_prop_contract` 第 5 条：判断"这一招在空中够不够得到站地上的人"。
func _hit_bottom(clip: String) -> float:
	return GameDB.first_hit_height(clip) - HITBOX_HEIGHT * 0.5


## 回查一条"写死的帧号"：值必须等于它自己声明的 manifest 字段。
##
## 不写 `_src` 就是拍脑袋的数 —— 会被这里炸出来。
## （第一版 `Skill_02` 的 capture 忘了写来源，当场被这条断言抓住。）
func _check_frame_claim(clip: String, cfg: Dictionary, key: String) -> Array[String]:
	var out: Array[String] = []
	var val: float = float(cfg[key])
	var src: String = String(cfg.get(key + "_src", ""))
	if src == "":
		# -1 表示"不适用"（例如指令投的 deliver = 由玩家决定），不算缺失
		if val >= 0.0:
			out.append("%s.%s = %.0f 没有声明数据来源" % [clip, key, val])
		return out
	var want: Variant = null
	match src:
		"hit_frame": want = GameDB.hit_frame(clip)
		"antic_frame": want = GameDB.antic_frame(clip)
		"cancel_frame": want = GameDB.cancel_frame(clip)
		"first_hit_point": want = _hit_point_frame(clip, 0)
		"last_hit_point": want = _hit_point_frame(clip, -1)
		_:
			out.append("%s.%s 声明了未知来源 %s" % [clip, key, src])
			return out
	if want == null:
		out.append("%s.%s 声明来自 %s，但 manifest 里那个字段是空的" % [clip, key, src])
	elif not is_equal_approx(val, float(want)):
		out.append("%s.%s 写死 %.0f，实测 %s=%s" % [clip, key, val, src, str(want)])
	return out


## 某段动画第 idx 个命中点的帧号（idx 支持负数，-1 = 最后一个）。
func _hit_point_frame(clip: String, idx: int) -> Variant:
	var pts: Variant = GameDB.clip(clip).get("hit_points")
	if not (pts is Array) or (pts as Array).is_empty():
		return null
	var arr: Array = pts
	var i: int = idx if idx >= 0 else arr.size() + idx
	if i < 0 or i >= arr.size():
		return null
	return float(arr[i].get("frame", 0.0))


# =====================================================================
# 主循环
# =====================================================================
func _physics_process(delta: float) -> void:
	if opponent == null:
		return

	_tick_hitstop()
	# 闪白在 hitstop 的提前返回**之前**推进 —— 停顿期间画面是静的，
	# 但这层曝光必须继续衰减，否则 4 帧停顿会把闪白冻成一整块死白。
	_tick_flash(delta)

	var inp := _poll_input(delta)
	if _hitstop_left > 0:
		inp.clear_edges()
		_hold_still()
		return

	_face_opponent()
	_sync_hurtbox_height()
	_tick_run_tap(inp, delta)
	_match_state(inp, delta)
	_tick_carrying(delta)
	_hold_still()


func _hold_still() -> void:
	velocity = Vector3.ZERO
	move_and_slide()


# ---------------------------------------------------------------------
# 起跑：连按两次方向
# ---------------------------------------------------------------------
## "连按两次同一个方向"= 起跑。
##
## **为什么另开这条路**：按住方向不放也能跑（`RUN_HOLD_TIME`），但那只在
## "从站立走到加速"这一条路上成立；格斗游戏里玩家更习惯"点两下 → 立刻冲出去"。
## 两条路通向同一个 `St.RUN`、同一段 `Run` 动画、同一个 `run_speed`
## —— 只是"什么时候允许转"多了一个入口，状态机一行没变。
##
## 实现上刻意**每帧无条件调用一次**（在 `_match_state` 之前）：
## 边沿识别要"每帧都看得到轴向"，如果把它塞进 `_match_state` 的某个分支里，
## 一旦那一帧按了攻击提前返回，这里的 `_prev_axis` 就会漏更新，
## 松开方向后下一帧会被误判成"新按下"。
func _tick_run_tap(inp: InputFrame, delta: float) -> void:
	_run_tap_fired = false
	if _tap_left > 0.0:
		_tap_left = maxf(0.0, _tap_left - delta)
		if _tap_left <= 0.0:
			_tap_dir = 0

	var ax := inp.axis()
	# "本帧新按下" = 这帧有方向、上帧没有
	var fresh := not is_zero_approx(ax) and is_zero_approx(_prev_axis)
	_prev_axis = ax
	if not fresh:
		return

	var d := int(signf(ax))
	if _tap_dir == d:
		# 窗口内同方向第二次 → 起跑，并把窗口清掉（免得三下、四下也一直触发）
		_tap_dir = 0
		_tap_left = 0.0
		_run_tap_fired = true
		return
	_tap_dir = d
	_tap_left = RUN_TAP_WINDOW


# ---------------------------------------------------------------------
# 手持物：每帧跟手
# ---------------------------------------------------------------------
## 手里的箱子跟着手骨走。
##
## 用**手骨的世界坐标**（`hand.R`）而不是"身体前方某个偏移"：
## 清单里 `Grab_Start` / `Throw` / `Heavy_01` 登记的命中点就是在这根骨头上，
## 所以"箱子在哪"和"这一下打在哪"天然是同一个出处，不会出现
## "看起来砸中了、判定却落在别处"。
##
## 平滑交给 `Carryable.follow_hand`（指数逼近，理由写在那儿）。
func _tick_carrying(delta: float) -> void:
	if carrying == null:
		return
	if not is_instance_valid(carrying) or carrying.state != Carryable.CSt.HELD:
		carrying = null
		return
	carrying.follow_hand(_bone_world_pos(_hand_idx), facing, delta)


## 把手上的箱子**放掉**（就地落地）。
##
## 用它而不是直接把 `carrying` 清空：清引用的话箱子会永远停在手上那个位置、
## 永远保持 HELD 状态 —— 那是一个再也捡不起来的幽灵。
## 和 `_release_hold` 是同一条纪律：**解除时要把对方那一侧也一起改回去**。
func _drop_carrying() -> void:
	var p := carrying
	carrying = null
	if p != null and is_instance_valid(p):
		p.drop()


func _poll_input(delta: float) -> InputFrame:
	if is_player:
		if _player_input == null:
			_player_input = PlayerInput.new()
		return _player_input.poll()
	if ai != null:
		return ai.poll(self, opponent, delta)
	return InputFrame.new()


func _tick_hitstop() -> void:
	if _hitstop_left > 0:
		_hitstop_left -= 1
		_ap.speed_scale = 0.0
		if _hitstop_left <= 0:
			_ap.speed_scale = 1.0


## 面向对手（攻击/受击/倒地/演出/投技期间不转，避免抽搐）
func _face_opponent() -> void:
	if state in [St.ATTACK, St.HIT, St.DOWN, St.DEAD, St.INTRO, St.TURN, St.GRAB, St.GRABBED]:
		return
	var d := opponent.global_position.x - global_position.x
	if absf(d) < 0.05:
		return
	var want := 1 if d > 0.0 else -1
	if want == facing:
		return
	var was_standing := state == St.IDLE or state == St.WALK or state == St.RUN
	_set_facing(want)
	if was_standing and _ap.has_animation("Turn"):
		_set_state(St.TURN)
		_play("Turn", BLEND_FAST)
		_turn_wait = GameDB.duration("Turn")


func _set_facing(f: int) -> void:
	facing = f
	if _visual != null:
		# 相机在 +Z 看 -Z：rotation.y = +PI/2 面向世界 +X（屏幕右），-PI/2 面向 -X
		_visual.rotation.y = PI * 0.5 * float(facing)


# =====================================================================
# 状态机
# =====================================================================
func _match_state(inp: InputFrame, delta: float) -> void:
	match state:
		St.INTRO:
			if _clip_finished():
				_advance_intro()

		St.IDLE:
			if _try_common(inp):
				return
			# 连按两次同一个方向 → 直接起跑（和"按住不放"是两条路，见 _tick_run_tap）
			if _run_tap_fired:
				_hold_dir_time = 0.0
				_set_state(St.RUN)
				_play("Run")
				return
			if inp.axis() != 0.0:
				_hold_dir_time = 0.0
				_set_state(St.WALK)
				_play("Walk_F" if inp.axis() == float(facing) else "Walk_B")

		St.WALK:
			if _try_common(inp):
				return
			var ax := inp.axis()
			if ax == 0.0:
				_set_state(St.IDLE)
				_play("Idle_01")
				return
			_hold_dir_time += delta
			if _hold_dir_time > RUN_HOLD_TIME and ax == float(facing):
				_set_state(St.RUN)
				_play("Run")
				return
			var clip := "Walk_F" if ax == float(facing) else "Walk_B"
			if _clip != clip:
				_play(clip)
			_move_world(ax * GameDB.walk_speed * delta)

		St.RUN:
			# 跑动中按拳脚 → 跑动跳踢（起跳 → 空中重击 → 落地）。
			# **必须在 `_try_common` 之前拦**：那条路会把 any_attack 直接吃掉，
			# 变成"站着出拳"，飞踢永远出不来。
			if inp.any_attack():
				_start_run_kick()
				return
			if _try_common(inp):
				return
			var ax := inp.axis()
			if ax == 0.0:
				_set_state(St.RUN_STOP)
				_play("Run_Stop")
				return
			if ax != float(facing):
				_set_state(St.WALK)
				_hold_dir_time = 0.0
				_play("Walk_B")
				return
			_move_world(ax * GameDB.run_speed * delta)

		St.RUN_STOP:
			if _clip_finished():
				_set_state(St.IDLE)
				_play("Idle_01")

		St.TURN:
			_turn_wait -= delta
			if _turn_wait <= 0.0:
				_set_state(St.IDLE)
				_play("Idle_01")

		St.CROUCH:
			# 蹲姿里能出下段攻击（B06）、能起跳、能放开蹲站起来。
			# 注意：**唯一能格挡的状态是 GUARD** —— 蹲不是防御，这里不复现"蹲防"。
			if inp.any_attack():
				_start_attack("Low_Attack")
				return
			if inp.jump:
				_jump_index = 0
				_jump_air = false
				_set_state(St.JUMP)
				_play(JUMP_SEQ[0], BLEND_FAST)
				return
			if not inp.crouch:
				_set_state(St.IDLE)
				_play("Idle_01")
			elif _clip == "Crouch" and _clip_finished():
				_play("Crouch_Idle")

		St.JUMP:
			_tick_jump(inp)

		St.ATTACK:
			_tick_attack(inp)

		St.GRAB:
			_tick_grab(inp, delta)

		St.GRABBED:
			_tick_grabbed(inp, delta)

		St.GUARD:
			if _clip == "Guard_Start" and _clip_finished():
				_play("Guard_Loop", BLEND_FAST)
				return
			if not inp.guard:
				_set_state(St.IDLE)
				_play("Idle_01")

		St.HIT:
			_apply_slide(delta)
			if _clip_finished():
				if _down_pending:
					_begin_knockdown()
				else:
					_set_state(St.IDLE)
					_play("Idle_01")

		St.DOWN:
			_apply_slide(delta)
			if _clip_finished():
				_set_state(St.IDLE)
				_play("Idle_01")

		St.DEAD:
			pass


## 各状态公用的输入响应（攻击 / 跳 / 蹲 / 防）。返回 true 表示已经转走了。
##
## 优先级：攻击 > 跳 > 蹲 > 防。
## 蹲排在防前面，因为"方向按下 + 防守"在格斗里就是蹲 —— 让方向键赢。
func _try_common(inp: InputFrame) -> bool:
	# 优先级：技能 > 抓技 > 拳脚。
	#  技能最"重"（有前摇、有代价），按下去就不该被同帧的轻拳吃掉；
	#  抓技其次（贴上去）；拳脚是默认动作。
	if inp.any_special_key() and _try_special(inp):
		return true
	if inp.grab:
		_start_grab()
		return true
	# 拾取/投掷键。排在抓技之后：两个键都可能"伸手"，但抓技键的语义
	# （贴上去扣人）优先级更高 —— 玩家同时按下时想要的显然是"抓"。
	if inp.pick:
		_start_pick()
		return true
	if inp.any_attack():
		_start_attack(_pick_attack_clip(inp))
		return true
	if inp.jump:
		_jump_index = 0
		_jump_air = false
		_set_state(St.JUMP)
		_play(JUMP_SEQ[0], BLEND_FAST)
		return true
	if inp.crouch:
		_set_state(St.CROUCH)
		_play("Crouch", BLEND_FAST)
		return true
	if inp.guard:
		_set_state(St.GUARD)
		_play("Guard_Start", BLEND_FAST)
		return true
	return false


## 技能键派发。返回 true 表示这一帧确实发出了一个技能。
func _try_special(inp: InputFrame) -> bool:
	if inp.ultimate:
		_start_ultimate()
		return true
	if inp.charge:
		_start_special(CHARGE_CLIP)
		return true
	for key in SPECIAL_MOVES.keys():
		if bool(inp.get(key)):
			_start_special(String(SPECIAL_MOVES[key]))
			return true
	return false


## 发一个技能。**抓技型技能（抱摔）走抓技流程**，其余走普通攻击流程 ——
## 差别不在动作好不好看，而在"伤害什么时候结算"：抱摔要等人抱在手上才算，
## 普通攻击在判定帧上直接打出去。这个区别由 `CARRY_MOVES` 里有没有登记决定。
func _start_special(clip: String) -> void:
	if CARRY_MOVES.has(clip):
		_enter_carry(clip)
		return
	_set_state(St.ATTACK)
	_play(clip, BLEND_FAST)
	if clip == CHARGE_CLIP:
		# 蓄力是有"过程"的招式：整段都该有光环在转（见 vfx_aura.gdshader）
		_start_aura(1.35, 2.30, GameDB.duration(clip))


## 大招：三段连续。整段盖一层更高的光环（它是"必杀"，视觉上要比普通技能重）。
func _start_ultimate() -> void:
	_ult_index = 0
	_ult_active = true
	_set_state(St.ATTACK)
	var total := 0.0
	for c in ULTIMATE_SEQ:
		total += GameDB.duration(c)
	_start_aura(1.80, 2.70, total)
	_play(ULTIMATE_SEQ[0], BLEND_FAST)


func _pick_attack_clip(inp: InputFrame) -> String:
	if inp.light: return ATTACK_STARTER["light"]
	if inp.heavy: return ATTACK_STARTER["heavy"]
	if inp.dash: return ATTACK_STARTER["dash"]
	if inp.upper: return ATTACK_STARTER["upper"]
	if inp.low: return ATTACK_STARTER["low"]
	if inp.special: return ATTACK_STARTER["special"]
	return "Light_01"


func _start_attack(clip: String, is_air := false) -> void:
	_set_state(St.ATTACK)
	_play(clip, BLEND_FAST)
	if is_air:
		_jump_air = false


func _tick_jump(inp: InputFrame) -> void:
	if _clip_finished():
		_jump_index += 1
		# 跑动跳踢：腾空顶点一到就切飞踢，而不是接下落段。
		# 顶点 = `Jump_Up` 播完那一刻 —— 探针实测骨盆最高点就落在这段自己身上
		# （起跳后 0.833 s，见 GameDB §8）。
		if _kick_pending and _jump_index >= JUMP_IDX_FALL:
			_kick_pending = false
			_start_air_kick()
			return
		if _jump_index >= JUMP_SEQ.size():
			_set_state(St.IDLE)
			_play("Idle_01")
			return
		_jump_air = _jump_index == 1 or _jump_index == JUMP_IDX_FALL
		_play(JUMP_SEQ[_jump_index], BLEND_FAST)
		return

	if _jump_air and (inp.light or inp.heavy):
		_start_attack("Air_Light" if inp.light else "Air_Heavy", true)


## 从 RUN 起跳，到顶点接一记飞踢。
##
## 三段动作全部是**现成的段**：`Jump_Start`（蓄力）→ `Jump_Up`（腾空）
## → `Air_Heavy`（飞踢）→ `Jump_Land`（落地，由 `_tick_attack` 的空中分支自动接）。
## 中间没有任何新增动画 —— 用户要求"不要增加新动作"，这里挑的是能表达
## "跑动中腾空一脚踹出去"的现有组合。
func _start_run_kick() -> void:
	_kick_pending = true
	_jump_index = 0
	_jump_air = false
	_set_state(St.JUMP)
	_play(JUMP_SEQ[0], BLEND_FAST)


## 腾空顶点上的那一脚。
##
## 向前动量 = **奔跑速度本身**（`GameDB.run_speed`），不另填一个数：
## 这一脚是"跑动的延续"，它推进得多快就是跑动推进得多快（见 GameDB §8）。
##
## 顺序要紧：`_play` 会把 `_knockback_x` 清零，所以动量必须**写在它之后**。
## `_apply_slide` 把 `_knockback_x` 按 `delta / _clip_dur` 摊到整段上，
## 于是这一整段的平均前进速度恰好 = run_speed。
func _start_air_kick() -> void:
	_jump_air = false
	_set_state(St.ATTACK)
	_play(JUMP_KICK_CLIP, BLEND_FAST)
	_knockback_x = float(facing) * GameDB.run_speed


func _tick_attack(inp: InputFrame) -> void:
	_apply_slide(get_physics_process_delta_time())
	var f := _current_frame()

	# 多段命中：把到点的判定依次打出去（大招有 4 段）
	while not _pending_hits.is_empty() and f >= float(_pending_hits[0]["frame"]):
		var h: Dictionary = _pending_hits.pop_front()
		_do_hit(float(h["reach_m"]), float(h["height_m"]))

	# 招式的"签名"地面冲击波：到点就放。
	# **和命中判定分开** —— 有些招的签名落在一个没有伤害判定的时刻上
	# （大招收尾、蓄力结束），硬挂在命中帧上就永远放不出来。
	_fire_ground_vfx(f)

	# 取消窗口内可以续段
	if _pending_chain == "" and (inp.any_attack() or inp.any_special_key()):
		var cf: Variant = GameDB.cancel_frame(_clip)
		if cf != null and f >= float(cf):
			_pending_chain = _resolve_chain(_clip, inp)

	# 取消窗口内也允许"转抓技"（轻拳点一下 → 抓 → 投）。
	# 和续段分开两个标记：续段是换一段拳脚，转抓技是换一整套流程。
	if not _pending_grab and inp.grab:
		var cf2: Variant = GameDB.cancel_frame(_clip)
		if cf2 != null and f >= float(cf2):
			_pending_grab = true

	if not _clip_finished():
		return

	if _pending_grab:
		_pending_grab = false
		_pending_chain = ""
		_start_grab()
	elif _pending_chain != "":
		var nxt := _pending_chain
		_pending_chain = ""
		_begin_move(nxt)
	elif _ult_active:
		# 大招三段自动续：这是资产里登记为"多段流程"的连招，
		# 玩家不需要在中间按任何键（中间段的取消窗口是留给"想中断"的人）。
		_ult_index += 1
		if _ult_index >= ULTIMATE_SEQ.size():
			_ult_active = false
			_set_state(St.IDLE)
			_play("Idle_01")
		else:
			_play(ULTIMATE_SEQ[_ult_index], BLEND_FAST)
	elif _is_air_clip(_clip):
		# 空中攻击落地：接 A13 落地（资产里空中家族假定的是另一条弹道时间线，
		# 模板不复现它，所以这里直接进落地 —— 见 docs/操作说明.md 的说明）
		_jump_index = JUMP_IDX_LAND
		_jump_air = false
		_set_state(St.JUMP)
		_play(JUMP_SEQ[JUMP_IDX_LAND], BLEND_FAST)
	elif _jump_air:
		_set_state(St.JUMP)
		_play(JUMP_SEQ[JUMP_IDX_FALL], BLEND_FAST)
	else:
		_set_state(St.IDLE)
		_play("Idle_01")


## 按 clip 名派发到正确的流程。**这是两条路的唯一分叉点**：
## 抓技型（抱摔）→ 抓技流程；大招起手 → 大招流程；其余 → 普通攻击。
##
## 单独抽出来是因为它被三个地方调用（起手 / 取消续招 / 测试），
## 散着写迟早会出现"键盘走一条路、取消走另一条路"的分叉。
func _begin_move(clip: String) -> void:
	if CARRY_MOVES.has(clip):
		_enter_carry(clip)
	elif clip == ULTIMATE_SEQ[0]:
		_start_ultimate()
	elif clip == CHARGE_CLIP:
		_start_special(CHARGE_CLIP)
	else:
		_start_attack(clip, _is_air_clip(clip))


func _resolve_chain(from_clip: String, inp: InputFrame) -> String:
	# 技能优先于拳脚（和 _try_common 同一条优先级）
	if inp.any_special_key():
		if inp.ultimate: return ULTIMATE_SEQ[0]
		if inp.charge: return CHARGE_CLIP
		for key in SPECIAL_MOVES.keys():
			if bool(inp.get(key)):
				return String(SPECIAL_MOVES[key])
	if inp.heavy: return "Heavy_01"
	if inp.dash: return "Dash_Attack"
	if inp.upper: return "Uppercut"
	if inp.low: return "Low_Attack"
	if inp.special: return "Skill_03"
	if inp.light:
		return LIGHT_CHAIN.get(from_clip, "Light_01")
	return ""


func _is_air_clip(c: String) -> bool:
	return c.begins_with("Air_")


# =====================================================================
# 投技：抓取 → 擒抱 → 投掷 → 被投者击飞倒地
# =====================================================================
## 起手抓技（或手上已经有人时 = 投出去）。
##
## 抓技的"链"和拳脚不同：拳脚是一段接一段的 clip，抓技是**一套流程**
## （伸手 → 扣住 → 抱着 → 摔），中途的段由这里的状态推进决定，
## 而不是由输入决定。所以它是独立状态，不塞进 ATTACK。
func _start_grab() -> void:
	if state == St.DEAD or state == St.GRABBED:
		return
	# 手上抱着箱子 → 两只手都占着，抓不了人。这一下改成"把箱子扔出去"，
	# 免得按了 G 什么都不发生（玩家读不出"为什么这次不行"）。
	if carrying != null:
		_start_prop_throw()
		return
	# 手上已经抓着人 → 这一下是投掷
	if holding != null:
		_begin_throw()
		return
	# 空中不能抓（被抓者会被摁到地上，弹道会跳变）
	if state == St.JUMP or _jump_air:
		return
	_carry_prop = false
	_enter_carry("Grab_Start")


# ---------------------------------------------------------------------
# 可拾取物：捡起 / 扔出
# ---------------------------------------------------------------------
## 拾取键。**一个键两种语义**，和抓技键是同一种设计：
##   手空着   → 伸手把地上的箱子捡起来
##   手上有物 → 把它扔出去
##   手上有箱、同时抱着人 → 优先扔箱子（两只手先腾出来）
##
## 用的是**同一段 `Grab_Start`**（"伸手取物"）与**同一段 `Throw`**（"甩出去"）——
## 资产里没有"拾取"/"投掷道具"这样的段，这两段是能表达这两个意思的最近动作。
## 用户明确要求"不要增加新动作"，所以这里是复用而不是新增。
func _start_pick() -> void:
	if state == St.DEAD or state == St.GRABBED:
		return
	if carrying != null:
		_start_prop_throw()
		return
	if holding != null:
		_begin_throw()
		return
	# 空中不能捡（弯腰去够地面的动作在腾空时没有意义，弹道也会跳变）
	if state == St.JUMP or _jump_air:
		return
	# 先看脚边有没有东西；没有就整段演完（那就是"蹲下去摸了个空"的后摇，
	# 和抓空同一种处理，不需要另写）
	_carry_prop = true
	_enter_carry("Grab_Start")


## 判定帧上真正把箱子拿起来。
func _grab_prop() -> void:
	var p := _query_prop()
	if p == null:
		return
	carrying = p
	p.pick_up(self)
	# 拿起来这一下给一点反馈：复用抓中人的那套（轻量、不含伤害）
	Vfx.impact(_vfx_host(), p.global_position, 0.0, Vfx.POWER_LIGHT, Vfx.COLOR_GRAB)


## 身前贴地带里最近的、能捡的箱子。
func _query_prop() -> Carryable:
	if carryables == null or not is_instance_valid(carryables):
		return null
	return carryables.nearest_pickable(global_position, facing)


## 把箱子扔出去：走 `Throw` 这一段，在它**自己的命中帧**（实测 28）上出手。
##
## 出手点用 `_hand_pos_for("Throw")` —— 也就是清单登记的 hand.R 高度 1.1347 m。
## 弹道（初速与重力）由 `GameDB §7` 从"这个高度 + 剩下的这段时间落地"反解出来，
## 所以这里一个数都不用填。
func _start_prop_throw() -> void:
	if carrying == null:
		return
	if state == St.JUMP or _jump_air:
		return
	var del: Variant = GameDB.hit_frame("Throw")
	if del == null:
		push_error("[Fighter] Throw 没有 hit_frame —— 箱子扔不出去")
		return
	_prop_throw = true
	_grab_move = "Throw"
	_grab_capture_frame = -1.0
	_grab_deliver_frame = float(del)
	_grab_caught = true
	_grab_hold = 0.0
	_carry_prop = false
	_set_state(St.GRAB)
	_play("Throw", BLEND_FAST)


func _deliver_prop_throw() -> void:
	var p := carrying
	carrying = null
	if p == null or not is_instance_valid(p):
		return
	if p.state != Carryable.CSt.HELD:
		return
	var from := _hand_pos_for("Throw")
	p.launch(from, facing, GameDB.prop_throw_speed, self)
	throws_done += 1
	Vfx.impact(_vfx_host(), from, float(facing), Vfx.POWER_LIGHT, Vfx.COLOR_LIGHT)


## 进入一套抓技。段名决定的只是"这一段怎么演"，
## 判定帧 / 结算帧一律从 `CARRY_MOVES` 取（= manifest 实测值）。
func _enter_carry(clip: String) -> void:
	var cfg: Dictionary = CARRY_MOVES.get(clip, {})
	if cfg.is_empty():
		push_error("[Fighter] %s 不在 CARRY_MOVES 里 —— 抓技必须登记判定帧" % clip)
		return
	_grab_move = clip
	_grab_capture_frame = float(cfg["capture"])
	_grab_deliver_frame = float(cfg["deliver"])
	_grab_caught = false
	_grab_hold = 0.0
	_pending_hits.clear()          # 抓技不走通用命中队列（伤害在结算帧才算）
	_set_state(St.GRAB)
	_play(clip, BLEND_FAST)


func _tick_grab(inp: InputFrame, delta: float) -> void:
	_apply_slide(delta)

	# 被抓的人已经没了（死亡 / 被别的状态抢走）→ 松手，别悬着一份幽灵引用
	if holding != null and (not is_instance_valid(holding) or holding.grabbed_by != self):
		_release_hold()

	var f := _current_frame()

	# --- 1. 抓取判定：只做一次，在实测的判定帧上 ---
	if not _grab_caught and _grab_capture_frame >= 0.0 and f >= _grab_capture_frame:
		_grab_caught = true
		_try_capture()

	# --- 2. 抓到之后：等出手 / 等结算帧 ---
	# 投箱子走的是同一条时间线（同一段 `Throw`、同一个结算帧），只是"手上是谁"
	# 不同 —— 所以两支合在这里判，免得出现"投人走一套时序、投箱子走另一套"。
	if _prop_throw:
		_grab_hold += delta
		if _grab_deliver_frame >= 0.0 and f >= _grab_deliver_frame:
			_deliver_prop_throw()
	elif holding != null:
		_grab_hold += delta
		if _grab_deliver_frame >= 0.0 and f >= _grab_deliver_frame:
			_deliver_carry()
		elif _grab_move == "Grab_Hold":
			# 出手条件：再按一次抓取键 / 任一攻击键 / 抱够 Grab_Hold 一圈的时长
			if inp.grab or inp.any_attack() or _grab_hold >= GameDB.grab_hold_max:
				_begin_throw()
			return

	# 循环段永远不会"播完"，所以这一支只会在非循环段（Grab_Start 落空 / Throw / Skill_02）触发
	if _clip_finished():
		_finish_carry()


## 在判定帧上做一次抓取查询。抓到就扣住，抓不到就什么也不做（让这一段自己演完 ——
## 那就是"抓空"的后摇，不需要另写）。
func _try_capture() -> void:
	if holding != null:
		return
	# 这一套 `Grab_Start` 是"弯腰捡东西"而不是"抓人"：判定帧上找地上的箱子。
	if _carry_prop:
		_grab_prop()
		return
	var victim := _query_grab(GameDB.grab_reach, GameDB.first_hit_height(_grab_move))
	if victim == null or not victim.can_be_grabbed():
		return

	holding = victim
	grabs_done += 1
	victim._be_grabbed(self)

	# 抓中的那一下也要有手感 —— 但不走 landed_hit（那是"造成了伤害"的通道）
	Vfx.impact(_vfx_host(), _hand_pos(), float(facing), Vfx.POWER_LIGHT, Vfx.COLOR_GRAB)
	var hs: Variant = GameDB.hitstop_frames(_grab_move)
	if hs != null and int(hs) > 0:
		_hitstop_left = int(hs)
		victim.apply_hitstop(int(hs))
	grabbed.emit(self, victim, _grab_move)

	# 指令投：抓中的瞬间切进"抓住循环"等玩家决定什么时候投
	if _grab_move == "Grab_Start":
		_grab_move = "Grab_Hold"
		_grab_capture_frame = -1.0
		_grab_deliver_frame = -1.0
		_grab_hold = 0.0
		_play("Grab_Hold", BLEND_FAST)


## 从抱着的状态切进投掷段。伤害在 Throw 自己的判定帧上才结算。
func _begin_throw() -> void:
	if holding == null:
		return
	var cfg: Dictionary = CARRY_MOVES.get("Grab_Start", {})
	# Throw 的结算帧 = 它自己的 hit_frame（实测 28）—— 用同一张表的口径，
	# 不另开一个"投掷用第几帧"的常量。
	var del: Variant = GameDB.hit_frame("Throw")
	if del == null:
		push_error("[Fighter] Throw 没有 hit_frame —— 投掷无法确定结算时刻")
		return
	_grab_move = "Throw"
	_grab_capture_frame = -1.0
	_grab_deliver_frame = float(del)
	_grab_caught = true
	_grab_hold = 0.0
	_play("Throw", BLEND_FAST)
	if cfg.is_empty():
		push_warning("[Fighter] CARRY_MOVES 缺少 Grab_Start（只影响自检）")


## 结算：把抱着的这个人摔出去。
func _deliver_carry() -> void:
	var victim := holding
	holding = null
	if victim == null or not is_instance_valid(victim):
		return
	var clip := _grab_move
	var dmg: int = GameDB.damage(clip)
	var info: Dictionary = victim.receive_throw(self, dmg, clip)
	throws_done += 1

	# 摔在地上 → 地面冲击波。**落点用被投者当前的位置**，
	# 这样"人被砸在哪儿"和"波从哪儿起"永远一致。
	Vfx.shockwave(_vfx_host(), victim.global_position,
		Vfx.SHOCK_RADIUS * 0.78, 0.42, Vfx.COLOR_SHOCK,
		sin(deg_to_rad(absf(Game.CAM_PITCH_DEG))))
	landed_hit.emit(self, victim, clip, int(info["applied"]))


## 一套抓技走完（没抓住 / 已经投出去 / 抱摔演完）→ 回站立。
func _finish_carry() -> void:
	_release_hold()
	_grab_move = ""
	_grab_capture_frame = -1.0
	_grab_deliver_frame = -1.0
	_grab_caught = false
	_carry_prop = false
	_prop_throw = false
	_set_state(St.IDLE)
	_play("Idle_01")


## 松手（不结算）。两边的引用必须一起清 —— 只清一边会留下幽灵状态。
func _release_hold() -> void:
	var v := holding
	holding = null
	if v != null and is_instance_valid(v) and v.grabbed_by == self:
		v.grabbed_by = null
		if v.state == St.GRABBED:
			v._stand_up_from_grab()


# ---------------------------------------------------------------------
# 被捕者一侧
# ---------------------------------------------------------------------
## 被抓者能不能被抓。
##
## **防御状态可以抓** —— 这正是指令投存在的理由：拳脚全被防住的人，
## 只有"贴上去"能治。所以这里**不排除** St.GUARD。
func can_be_grabbed() -> bool:
	if grabbed_by != null:
		return false
	return not (state in [St.DEAD, St.DOWN, St.GRAB, St.GRABBED, St.INTRO, St.JUMP])


func _be_grabbed(attacker: Fighter) -> void:
	# 被扣住的时候手里的东西要掉 —— 两只手都被制住了
	_drop_carrying()
	grabbed_by = attacker
	_grab_mash = 0
	_hitstop_left = 0
	_knockback_x = 0.0
	_root_motion_x = 0.0
	_pending_hits.clear()
	_pending_chain = ""
	_pending_grab = false
	_set_state(St.GRABBED)
	# 这里播的姿势是**替代方案**（资产里没有被擒段），理由见 GRABBED_POSE_CLIP
	_play(GRABBED_POSE_CLIP, BLEND_FAST)
	_sync_grabbed_position()


func _tick_grabbed(inp: InputFrame, delta: float) -> void:
	# 抓我的人没了（被打倒 / 被打断）→ 自己站稳
	if grabbed_by == null or not is_instance_valid(grabbed_by):
		grabbed_by = null
		_stand_up_from_grab()
		return

	_sync_grabbed_position()

	# 挣脱：每按一下主动出招键累加一点。抓我的一方也同时被打断（见 _break_free）。
	if inp.any_action():
		_grab_mash += 1
		if _grab_mash >= GameDB.GRAB_MASH_BREAK:
			_break_free()


## 被擒者的位置 = 抓取者中心 + 朝向 × 实测抓取间距。
##
## 每帧硬设而不是靠物理：这是一个**约束**（"被手扣住"），不是受力结果。
## 交给物理反而会因为推箱和位移互相打架，表现为两个人互相抖。
func _sync_grabbed_position() -> void:
	var a := grabbed_by
	if a == null:
		return
	var d: float = GameDB.grab_hold_distance
	global_position.x = clampf(a.global_position.x + float(a.facing) * d,
		-GameDB.STAGE_HALF_WIDTH, GameDB.STAGE_HALF_WIDTH)
	# 被扣住的人应该面朝抓他的人
	var want := -a.facing
	if facing != want:
		_set_facing(want)


## 挣脱成功 —— **双向**的：抓的人也一起失衡。
##
## 为什么不让挣脱方白赚：如果挣脱没有任何代价，指令投就变成"白送的贴身技"，
## 抓着人反而吃亏。双方一起失衡，投技才有"赌大小"的味道。
func _break_free() -> void:
	var a := grabbed_by
	grabbed_by = null
	_grab_mash = 0
	_set_state(St.HIT)
	_play(GRAB_BREAK_RECOVER_CLIP, BLEND_FAST)
	_knockback_x = -float(facing) * GameDB.BREAK_PUSH
	if a != null and is_instance_valid(a):
		a._on_hold_broken(self)


## 抓取者一侧的"被挣脱"处理（由被捕者调过来）。
func _on_hold_broken(_victim: Fighter) -> void:
	holding = null
	_grab_move = ""
	_grab_capture_frame = -1.0
	_grab_deliver_frame = -1.0
	_grab_caught = false
	_set_state(St.HIT)
	_play(GRAB_BREAK_RECOVER_CLIP, BLEND_FAST)
	_knockback_x = -float(facing) * GameDB.BREAK_PUSH


## 从"被擒"回到站立（对方松手 / 对方消失）。
func _stand_up_from_grab() -> void:
	if state != St.GRABBED:
		return
	_set_state(St.IDLE)
	_play("Idle_01", BLEND_FAST)


## 被投出去：伤害 + 击飞 + 倒地。
##
## **不走 `receive_hit`**，三个理由：
##   1. 投技不吃防御（`receive_hit` 里有 block 分支，那正是投技要绕开的东西）；
##   2. 姿态要用 `Launch_Hit`（被击飞）而不是 `Hit_Heavy_*`；
##   3. 被投者在这一刻还挂在别人手上，要先把这个约束解掉。
## 返回 {applied, blocked, knocked_down}，与 `receive_hit` 同构。
func receive_throw(attacker: Fighter, damage: int, clip: String) -> Dictionary:
	grabbed_by = null
	if state == St.DEAD:
		return {"applied": 0, "blocked": false, "knocked_down": false}

	var from_front := signf(attacker.global_position.x - global_position.x) == signf(float(facing))
	var away := -signf(attacker.global_position.x - global_position.x)
	if is_zero_approx(away):
		away = -float(facing)

	hp = maxi(0, hp - damage)
	_last_damage = damage
	hp_changed.emit(hp, max_hp)
	trigger_flash(float(damage) / FLASH_DAMAGE_FULL, 0.18)

	if hp <= 0:
		_die()
		return {"applied": damage, "blocked": false, "knocked_down": false}

	_set_state(St.HIT)
	_play("Launch_Hit", BLEND_FAST)
	# 击飞的滑行距离由"抓住时两人的间距"放大而来（见 GameDB.THROW_FLIGHT_K）
	_knockback_x = away * GameDB.throw_flight
	_knockdown_clip = "Knockdown_B" if from_front else "Knockdown_F"
	_down_pending = true
	_hit_taken_this_clip = false
	return {"applied": damage, "blocked": false, "knocked_down": true}


# ---------------------------------------------------------------------
# 投技用的小工具
# ---------------------------------------------------------------------
## 手上的位置（世界坐标）—— 抓取的着力点。高度取实测的抓取点高度。
func _hand_pos() -> Vector3:
	return _hand_pos_for("Grab_Start")


## 某一段的"手在世界里的位置"。
##
## 高度取该段**自己的** manifest 命中点高度，横向取 `grab_reach`（手的最远可达）——
## 也就是说这个式子里的两个数都有出处，不是"手大概在这儿"。
## 分离出来是因为它现在有两个用处：抓人的着力点、以及把箱子扔出去的**出手点**
## （`Throw` 的手在 1.1347 m 高，和抓取点不是同一个高度）。
func _hand_pos_for(clip: String) -> Vector3:
	var h: float = GameDB.first_hit_height(clip)
	var r: float = GameDB.grab_reach - HITBOX_BIAS
	return global_position + Vector3(float(facing) * r, h, 0.0)


func _vfx_host() -> Node3D:
	return vfx_host if vfx_host != null else self


## 招式的签名地面冲击波。到帧才放，一段只放一次。
func _fire_ground_vfx(f: float) -> void:
	if _ground_vfx_fired:
		return
	var cfg: Dictionary = GROUND_VFX.get(_clip, {})
	if cfg.is_empty():
		return
	if f < float(cfg["frame"]):
		return
	_ground_vfx_fired = true
	var r: float = Vfx.SHOCK_RADIUS * float(cfg["radius_k"])
	# 落点压在**身体前方半步**：贴着自己的脚放会被人挡住，
	# 放太远又和招式脱节（大招那种大范围除外 —— 由半径系数体现）。
	var ahead: float = 0.45 if r < Vfx.SHOCK_RADIUS else 0.75
	Vfx.shockwave(_vfx_host(),
		Vector3(global_position.x + float(facing) * ahead, 0.0, 0.0),
		r, 0.50, Vfx.COLOR_SHOCK, _view_sin())


## 相机俯角的正弦 = 地面上的圆在屏幕上被压扁的比例。
## 冲击波着色器要拿它把环的粗细补偿回来（见 vfx_shock.gdshader）。
func _view_sin() -> float:
	return sin(deg_to_rad(absf(Game.CAM_PITCH_DEG)))


# ---------------------------------------------------------------------
# 蓄力光环
# ---------------------------------------------------------------------
## 起一层跟随自己的光环，覆盖 `clips` 里列出的段。
##
## `clips` 故意声明成**无类型 Array**：给它默认值 `[]` 时，Godot 会报
## `Trying to assign an array of type "Array" to a variable of type "Array[String]"`
## —— 默认值是在调用点构造的普通 Array，赋不进 `Array[String]` 形参。
## 所以这里收无类型、进门就用 `assign()` 转成有类型的成员。
func _start_aura(width: float, height: float, duration: float,
		clips: Array = []) -> void:
	_stop_aura()
	var src: Array = clips if not clips.is_empty() else [_clip]
	_aura_clips.assign(src)
	_aura_node = Vfx.aura(self, width, height, duration, Vfx.COLOR_AURA)


func _stop_aura() -> void:
	if _aura_node != null and is_instance_valid(_aura_node):
		_aura_node.queue_free()
	_aura_node = null
	_aura_clips = []


## 我现在是不是抓着人（给 Game / 测试用）
func is_holding() -> bool:
	return holding != null


func is_held() -> bool:
	return grabbed_by != null


# =====================================================================
# 剪辑播放
# =====================================================================
func _play(clip: String, blend: float = BLEND_NORMAL) -> void:
	# 清单名 -> 引擎名。绝不拿清单名直接问引擎（见 GameDB §0 的修正表）。
	var engine := GameDB.engine_name(clip)
	if not _ap.has_animation(engine):
		push_error("[Fighter] 没有动画 %s（引擎名 %s）" % [clip, engine])
		return
	# 同一段重播要从头开始（连打同招）。用**清单名 `_clip`** 判断，
	# 不用 `_ap.current_animation` —— 非循环动画播完后引擎会把它清成空串，
	# 拿它当"当前是哪段"的依据会在播完那一帧失效（真踩过，见 _clip_finished）。
	if _clip == clip and _ap.is_playing():
		_ap.stop()
	_clip = clip
	_clip_dur = maxf(GameDB.duration(clip), 0.0001)
	_pending_hits = _collect_hit_events(clip)
	_pending_chain = ""
	_pending_grab = false
	_hit_taken_this_clip = false
	_ground_vfx_fired = false
	# 大招标记只在"还在演大招的段"上保持；切到别的段就自动退出大招流程
	_ult_active = _ult_active and ULTIMATE_SEQ.has(clip)
	if not _ult_active:
		_ult_index = -1
	# 光环只跟着它该跟的那几段走。切走了就收掉 ——
	# 否则蓄力光环会一直挂到下一次攻击，看起来像"人一直在发光"。
	if _aura_node != null and not _aura_clips.has(clip):
		_stop_aura()
	_root_motion_x = _root_motion_world_x(clip)
	_knockback_x = 0.0
	_ap.speed_scale = 1.0
	_ap.play(engine, blend)


## 把 manifest 里实测的命中点转成"第几帧打出去"的事件队列。
func _collect_hit_events(clip: String) -> Array:
	var pts: Variant = GameDB.clip(clip).get("hit_points")
	if pts == null or not (pts is Array):
		return []
	var out: Array = []
	for p in pts:
		out.append({
			"frame": float(p.get("frame", 0.0)),
			"reach_m": float(p.get("reach_m", 0.0)),
			"height_m": clampf(float(p.get("height_m", 1.0)), 0.30, 1.70),
			"limb": p.get("limb", ""),
		})
	out.sort_custom(func(a, b): return a["frame"] < b["frame"])
	return out


## root_motion_m 是 Blender 系的 [x, y]（y 正 = 身后，前方 = -y）。
## 角色在 Godot 里前向 = +Z，视觉绕 Y 转 ±90° ⟹ 世界 X 分量 = facing * (-rm.y)
func _root_motion_world_x(clip: String) -> float:
	var rm: Vector2 = GameDB.root_motion(clip)
	return float(facing) * (-rm.y)


func _apply_slide(delta: float) -> void:
	var total := _root_motion_x + _knockback_x
	if is_zero_approx(total) or _clip_dur <= 0.0:
		return
	_move_world(total * (delta / _clip_dur))


func _move_world(dx: float) -> void:
	var nx := global_position.x + dx
	# 推箱：身体不许互相穿过。最小中心距 = 2 × 实测受击体半径。
	# 用位置直接夹逼而不是靠物理引擎 —— 位移本来就是直接写 global_position 的，
	# 交给 CharacterBody3D 的 move_and_slide 反而管不住。
	if opponent != null:
		var d := nx - opponent.global_position.x
		if absf(d) < GameDB.PUSH_SEPARATION:
			var dir := signf(d)
			if is_zero_approx(dir):
				dir = float(facing)
			nx = opponent.global_position.x + dir * GameDB.PUSH_SEPARATION
	global_position.x = clampf(nx, -GameDB.STAGE_HALF_WIDTH, GameDB.STAGE_HALF_WIDTH)


func _current_frame() -> float:
	return _ap.current_animation_position * 60.0


## 当前这段是否播完。
##
## 两个条件都要，因为 Godot 的行为是：
##   - 非循环动画播到末帧 → AnimationPlayer **停止播放**，`current_animation`
##     被清成空串（实测：0.400 s 那一刻起 engine_anim() == ""）；
##   - 此时 `current_animation_position` 停在末帧不动。
## 所以「位置到时长」与「引擎已停」都算播完；只看其中一个会漏。
func _clip_finished() -> bool:
	if _clip_dur <= 0.0:
		return true
	if not _ap.is_playing():
		return true
	return _ap.current_animation_position >= _clip_dur - 0.0005


# =====================================================================
# 攻击判定
# =====================================================================
func _do_hit(reach: float, height: float) -> void:
	# 手里拿着箱子 → 这一下的着力面是**箱子**，不是拳头。
	if carrying != null:
		_do_swing(reach, height)
		return

	var victim: Fighter = null
	if opponent != null and opponent.state != St.DEAD:
		victim = _query_hit(reach, height)
	if victim != null and victim != self:
		var base: int = GameDB.damage(_clip)
		if _rage_used:
			base = int(round(float(base) * RAGE_DAMAGE_SCALE))
		var info: Dictionary = victim.receive_hit(self, base, _clip)
		var pair := _hit_power_and_color(int(info["applied"]), bool(info["blocked"]))
		_flash_spark(reach, height, float(pair[0]), pair[1] as Color, bool(info["blocked"]))
		landed_hit.emit(self, victim, _clip, int(info["applied"]))

		_hitstop_left = maxi(_hitstop_left, _clip_hitstop())

	# 同一记拳脚也会砸到**地上的箱子**。刻意和"打没打中人"解耦 ——
	# 空挥一拳砸碎脚边的箱子是完全合理的动作。
	_smash_props(reach)


## 手持物砸击：手上那件东西就是这一下的着力面。
##
## 伤害 = `damage(clip) + prop_impact_damage`：
##   · 前一项是"这一拳本身的力"；
##   · 后一项是"多抡了一件东西的额外质量"。
## 而 `prop_impact_damage` **同时**就是箱子自己会掉多少耐久 —— 两者在物理上
## 本来就是同一个冲量（GameDB §7 就是这么定的）。于是"一个箱子能抡几下"
## 天然等于 `PROP_HITS_TO_BREAK`（3 下），这里一个数都不用另填。
func _do_swing(reach: float, height: float) -> void:
	var prop := carrying
	if prop == null or not is_instance_valid(prop):
		carrying = null
		return

	var extra: int = GameDB.prop_impact_damage
	var base: int = GameDB.damage(_clip) + extra
	if _rage_used:
		base = int(round(float(base) * RAGE_DAMAGE_SCALE))

	var hit_something := false
	if opponent != null and opponent.state != St.DEAD:
		var victim := _query_hit(reach, height)
		if victim != null and victim != self:
			var info: Dictionary = victim.receive_hit(self, base, _clip)
			var pair := _hit_power_and_color(int(info["applied"]), bool(info["blocked"]))
			_flash_spark(reach, height, float(pair[0]), pair[1] as Color, bool(info["blocked"]))
			landed_hit.emit(self, victim, _clip, int(info["applied"]))
			hit_something = true

	# 抡着东西也能砸**别的**箱子。手上的那一个不会被卷进来 ——
	# 拿在手里时它的碰撞层被置 0 了（见 Carryable._set_active）。
	if _smash_props(reach, extra):
		hit_something = true

	# 空挥（谁也没碰到）**不掉耐久** —— 没撞上任何东西，就没有冲量。
	# 于是"一个箱子能抡几下"是一次次真砸出来的，不是按挥了几下手数出来的。
	if not hit_something:
		return

	# 砸中了东西 → 手上的箱子也吃下这份冲量，掉一档耐久。
	var broke_now := prop.take_hit(extra, prop.global_position,
		Vfx.POWER_HEAVY, Vfx.COLOR_HEAVY)
	if broke_now:
		carrying = null
	_hitstop_left = maxi(_hitstop_left, _clip_hitstop())


## 拳脚/手持物砸到地上的箱子。返回是否砸到了。
##
## 箱子**不在受击体层**（它有自己的一层 `LAYER_CARRYABLE`），所以拳脚那套
## `_query_box(mask = LAYER_HURTBOX)` 天生找不到它 —— 必须另做一次查询。
## 纵向不用攻击自己的判定高度，而用 `GameDB.prop_pickup_height` 那条**贴地带**：
## 拳脚的判定点都在半身高以上（轻拳打在胸口），硬用会"站着出拳打不到地上的箱子"。
##
## `extra` = 手上那件东西额外贡献的伤害（空手时是 0）。赤手打和抡着东西打
## 对箱子的伤害不该一样 —— 那件东西有质量。
func _smash_props(reach: float, extra: int = 0) -> bool:
	if carryables == null or not is_instance_valid(carryables):
		return false
	# 纵向用**从身体到拳的整段**（深度 = reach），不是手上一小块 ——
	# 和抓取判定同一个理由（见 `_query_grab`）：躺在这一段里的任何位置都该被扫到。
	# 用 `HITBOX_DEPTH`（0.40）的话，只有"恰好站在拳能碰到的那 40 cm 里"才打得到箱子，
	# 表现是"明明贴着箱子出拳却没反应"。
	var found := carryables.query_ground(reach, global_position, facing,
		reach, HITBOX_SPAN)
	# 只砸最近的那一个：判定盒只有 0.85 m 宽，本来也只罩得住一个；
	# 真出现两个时"最近的那个"有确定的语义，不会随查询返回顺序变。
	var best: Carryable = null
	var best_d := INF
	for p in found:
		if not p.can_be_smashed():
			continue
		var d: float = absf(p.global_position.x - global_position.x)
		if d < best_d:
			best_d = d
			best = p
	if best == null:
		return false

	var dmg: int = GameDB.damage(_clip) + maxi(0, extra)
	var pair := _hit_power_and_color(dmg, false)
	var at := global_position + Vector3(float(facing) * (reach + HITBOX_BIAS),
		GameDB.prop_pickup_height, 0.0)
	best.take_hit(dmg, at, float(pair[0]), pair[1] as Color)
	hit_prop.emit(self, best, dmg)
	_hitstop_left = maxi(_hitstop_left, _clip_hitstop())
	return true


## 当前这段自己的打击停顿帧数（0 = 这段不停）。
func _clip_hitstop() -> int:
	var hs: Variant = GameDB.hitstop_frames(_clip)
	return int(hs) if hs != null else 0


## 用直接空间查询（不是 Area 信号）—— 判帧当帧就出结果，没有一帧延迟。
func _query_hit(reach: float, height: float) -> Fighter:
	# 拳脚：判定盒**贴在手的位置**上 —— reach 就是那一下的着力点，
	# 盒子以它为中心、只有 0.4 m 深（所以"打空的拳"是真的差了几厘米）。
	return _query_box(reach - HITBOX_BIAS, HITBOX_DEPTH, height)


## 抓取判定：判定盒**从身体一直铺到手**（深度 = reach），不是手上一小块。
##
## 为什么抓技不能复用拳脚那种"手部小盒"：
##   `Grab_Start` 自带 0.45 m 的前冲（root motion），而判定在小盒里是
##   "中心距落在 [0.81, 1.81] m 才算命中"。前冲把中心距一路压小，
##   于是**只有起手那一瞬间的距离恰好**才抓得到 —— 同一个动作时抓得到时抓不到。
##   实测第一版就是这样：1.02 m 起手，冲到 0.79 m 时手已经越过了对手，判定落空。
##   手扫过的整段区间都该算命中，这才是"伸出胳膊能碰到就抓住"。
##   上限 = grab_reach + 受击体半径，也就是"手能碰到对手身体表面"。
func _query_grab(reach: float, height: float) -> Fighter:
	var d := maxf(reach, 0.60)
	return _query_box(d * 0.5, d, height)


## 在身前 `ahead` 米处放一个 `depth × HITBOX_HEIGHT × HITBOX_SPAN` 的盒做空间查询。
func _query_box(ahead: float, depth: float, height: float) -> Fighter:
	var shape := BoxShape3D.new()
	shape.size = Vector3(maxf(depth, 0.05), HITBOX_HEIGHT, HITBOX_SPAN)
	var params := PhysicsShapeQueryParameters3D.new()
	params.shape = shape
	params.transform = Transform3D(Basis(), global_position + Vector3(
		float(facing) * ahead, height, 0.0))
	params.collision_mask = LAYER_HURTBOX
	params.collide_with_areas = true
	params.collide_with_bodies = false
	params.exclude = [_hurtbox.get_rid()]

	for h in get_world_3d().direct_space_state.intersect_shape(params, 8):
		var col: Object = h.get("collider")
		if col is Area3D and col.has_meta("fighter"):
			var f: Fighter = col.get_meta("fighter")
			if f != self:
				return f
	return null


func _flash_spark(reach: float, height: float, power: float,
		color: Color, blocked: bool) -> void:
	## 命中爆点走程序化特效库（工程里没有可用的特效资产，理由见 vfx.gd 头部）。
	##
	## 位置取**攻击者前方 reach 处**，而不是受害者身上 —— 这一拳的着力点
	## 在这里，火花挂在这儿才读得出"打中了哪个位置"。
	var host: Node3D = vfx_host if vfx_host != null else self
	var pos := global_position + Vector3(float(facing) * (reach + HITBOX_BIAS), height, 0.0)
	var c := Vfx.COLOR_GUARD if blocked else color
	Vfx.impact(host, pos, float(facing), power, c)


## 按伤害选强度档 + 配色。放在这里而不是散在各调用点：
## "多少伤害算重击"只有一处定义（GameDB.HIT_HEAVY_DAMAGE）。
func _hit_power_and_color(damage: int, blocked: bool) -> Array:
	if blocked:
		# 防御也吃伤害，但反馈要"冷"——用蓝白而不是暖橙，一眼能区分
		return [Vfx.POWER_LIGHT, Vfx.COLOR_GUARD]
	if damage >= GameDB.KNOCKDOWN_DAMAGE:
		return [Vfx.POWER_SPECIAL, Vfx.COLOR_HEAVY]
	if damage >= GameDB.HIT_HEAVY_DAMAGE:
		return [Vfx.POWER_HEAVY, Vfx.COLOR_HEAVY]
	return [Vfx.POWER_LIGHT, Vfx.COLOR_LIGHT]


# =====================================================================
# 受击
# =====================================================================
## 返回 {applied, blocked, knocked_down}
func receive_hit(attacker: Fighter, damage: int, clip: String) -> Dictionary:
	# 挨打就松开手上的人：指令投的风险就在这里 —— 抱着人的时候是最脆的。
	# （不松手的话会出现"一边被连打一边还举着人"的荒谬画面。）
	if holding != null:
		_release_hold()
	# 同理：挨打就撒手，箱子掉在地上。手上多一件东西不该变成"免费的护甲"。
	if carrying != null:
		_drop_carrying()

	var from_front := signf(attacker.global_position.x - global_position.x) == signf(float(facing))
	var blocked := state == St.GUARD and from_front
	var applied := damage
	if blocked:
		applied = maxi(1, int(round(float(damage) * GameDB.GUARD_DAMAGE_SCALE)))

	hp = maxi(0, hp - applied)
	_last_damage = applied
	hp_changed.emit(hp, max_hp)

	# 受击闪白：强度跟着伤害走。放在这里（而不是攻击方）是因为
	# **被闪的是挨打的人**，而且防御住的命中也要闪（只是强度低一些）。
	var fs: float = float(applied) / FLASH_DAMAGE_FULL
	trigger_flash(fs, 0.16 if applied >= GameDB.KNOCKDOWN_DAMAGE else 0.12)

	# 倒地补刀
	if state == St.DOWN and not _hit_taken_this_clip and _ap.has_animation("Ground_Hit"):
		_play("Ground_Hit", BLEND_FAST)
		_hit_taken_this_clip = true
		return {"applied": applied, "blocked": false, "knocked_down": false}

	if state == St.DEAD:
		return {"applied": applied, "blocked": false, "knocked_down": false}

	if hp <= 0:
		_die()
		return {"applied": applied, "blocked": blocked, "knocked_down": false}

	if not _rage_used and hp <= int(max_hp * RAGE_HP_RATIO) and _ap.has_animation("Rage"):
		_rage_used = true

	var away := -signf(attacker.global_position.x - global_position.x)
	var knock: float = float(applied) * GameDB.KNOCKBACK_PER_DAMAGE

	if blocked:
		var guard_clip := "Guard_Break" if applied >= GameDB.KNOCKDOWN_DAMAGE else "Guard_Hit"
		_set_state(St.HIT)
		_play(guard_clip, BLEND_FAST)
		_knockback_x = away * knock
		_down_pending = applied >= GameDB.KNOCKDOWN_DAMAGE
		_knockdown_clip = "Knockdown_B" if from_front else "Knockdown_F"
		return {"applied": applied, "blocked": true, "knocked_down": _down_pending}

	var heavy: bool = applied >= GameDB.HIT_HEAVY_DAMAGE
	var hit_clip := ("Hit_Heavy_" if heavy else "Hit_Light_") + ("F" if from_front else "B")
	_set_state(St.HIT)
	_play(hit_clip, BLEND_FAST)
	_knockback_x = away * knock
	# 正面被打飞 -> 向后倒；背后被打 -> 向前倒
	_knockdown_clip = "Knockdown_B" if from_front else "Knockdown_F"
	_down_pending = applied >= GameDB.KNOCKDOWN_DAMAGE
	return {"applied": applied, "blocked": false, "knocked_down": _down_pending}


func _begin_knockdown() -> void:
	_down_pending = false
	_set_state(St.DOWN)
	_play(_knockdown_clip, BLEND_FAST)
	if is_zero_approx(_knockback_x):
		_knockback_x = -float(facing) * 0.35


func _die() -> void:
	# 死了当然要松手（否则尸体会一直"拎着"一个人）
	_release_hold()
	_drop_carrying()
	grabbed_by = null
	_set_state(St.DEAD)
	_play("Death")
	defeated.emit(self)


# =====================================================================
# 演出（由 Game 驱动）
# =====================================================================
func play_sequence(clips: Array) -> void:
	_intro_queue = clips.duplicate()
	_set_state(St.INTRO)
	_set_facing(facing)
	_advance_intro()


func _advance_intro() -> void:
	if _intro_queue.is_empty():
		_set_state(St.IDLE)
		_play("Idle_01")
		return
	_play(String(_intro_queue.pop_front()), BLEND_NORMAL)


func play_victory() -> void:
	if hp <= 0:
		_die()
		return
	var pick := ["Victory_01", "Victory_02", "Victory_03"]
	play_sequence([pick[randi() % pick.size()]])


func play_waiting() -> void:
	_set_state(St.IDLE)
	_play("Idle_01")


func reset_fighter(x: float, face: int) -> void:
	hp = max_hp
	_last_damage = 0
	_rage_used = false
	_hitstop_left = 0
	_down_pending = false
	_knockback_x = 0.0
	_root_motion_x = 0.0
	_hit_taken_this_clip = false
	_jump_air = false
	_jump_index = 0
	_kick_pending = false
	_hold_dir_time = 0.0
	_prev_axis = 0.0
	_tap_dir = 0
	_tap_left = 0.0
	_run_tap_fired = false
	_ap.speed_scale = 1.0
	# 手持物的引用要清。**不在这里把它放回出生点** —— 那是 CarryableManager
	# 的事（`reset_all()` 会把所有箱子一起复位），角色只负责"我不再拿着它"。
	# 两件事分开做才不会出现"角色清空了、箱子还留在 HELD 状态"的错配。
	carrying = null
	_carry_prop = false
	_prop_throw = false
	# 投技的引用要**两边一起清**：重开一局时如果只清一半，
	# 会出现"新回合开场 2P 被扣在 1P 手上"这种幽灵状态。
	holding = null
	grabbed_by = null
	_grab_move = ""
	_grab_capture_frame = -1.0
	_grab_deliver_frame = -1.0
	_grab_caught = false
	_grab_hold = 0.0
	_grab_mash = 0
	_pending_grab = false
	# 闪白必须清掉：上一回合末尾角色可能正亮着（KO 那一击还在衰减），
	# 不清的话新回合开场双方是白的。
	clear_flash()
	state = St.INTRO
	facing = face
	_set_facing(face)
	global_position = Vector3(x, 0.0, 0.0)
	if ai != null:
		ai.reset()
	hp_changed.emit(hp, max_hp)


func set_ai(enabled: bool) -> void:
	is_player = not enabled
	if enabled and ai == null:
		ai = DummyAI.new()


# =====================================================================
# 状态切换与查询
# =====================================================================
func _set_state(s: int) -> void:
	if state == s:
		return
	state = s
	state_changed.emit(label())


func label() -> String:
	return String(ST_LABEL.get(state, "?"))


func label_en() -> String:
	return String(ST_LABEL_EN.get(state, "?"))


func clip_name() -> String:
	return _clip


## 引擎侧当前动画名（**清单名**见 `clip_name()`）。
## 两者在 `Guard_Loop` 上不一致，调试时必须能分别看到 —— 所以单独开一个口子。
func engine_anim() -> String:
	return _ap.current_animation if _ap != null else ""


## 引擎侧当前播放位置（秒）。清单时长见 `GameDB.duration(clip_name())`。
func anim_position_s() -> float:
	return _ap.current_animation_position if _ap != null else 0.0


## 动画是否被打击停顿冻结（speed_scale == 0）。
func anim_frozen() -> bool:
	return _ap != null and is_zero_approx(_ap.speed_scale)


## 暴露骨架给外部校验/调试用（自动化测试读静止位姿核对轴约定）。
func skeleton() -> Skeleton3D:
	return _skeleton


func current_frame() -> float:
	return _current_frame()


func last_damage() -> int:
	return _last_damage


func hp_ratio() -> float:
	return float(hp) / float(maxf(1.0, float(max_hp)))


func is_ko() -> bool:
	return hp <= 0
