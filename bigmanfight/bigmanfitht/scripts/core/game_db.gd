extends Node
## GameDB —— 全局数据层（autoload）
##
## 职责：把 `assets/characters/bigman/animations/manifest.json` 读进来，
## 并**用实测的动画数据推导出游戏数值**。
##
## 原则：这里不出现任何拍脑袋的数字。凡是能由动画实测数据算出来的，
## 全部写成公式在下面；凡是必须人定的（如 HP 上限），写在 §3 并注明理由。

const MANIFEST_PATH := "res://assets/characters/bigman/animations/manifest.json"

# ---------------------------------------------------------------------
# §0 引擎名修正表 —— 从数据文件读，不从代码里猜
# ---------------------------------------------------------------------
# Godot 的 glTF 导入器会把动画名**结尾的 `_Loop` 去掉**（它把 `_Loop` 当循环标记），
# 但仅当去掉后缀后不撞名时才改。本资产里：
#   D02 `Guard_Loop`  → 引擎里叫 `Guard`（去掉后缀没人和它撞）
#   C08b `Charge_Loop` → 引擎里仍叫 `Charge_Loop`（去掉后缀会撞上已有的 `Charge`）
#
# 这两条由 tools/probe_anim_names.gd 实测，并做过对照实验（改名为 GuardXLoop 就保留原名）。
# 差异表放在 `engine_names.json`，由 tools/verify_assets.py 用同一条规则重算校验 ——
# 所以这里不硬编码，只读文件。文件丢了就 push_error 并退到兜底表（会被 Fighter 的断言炸出来）。
const ENGINE_NAMES_PATH := "res://assets/characters/bigman/animations/engine_names.json"
const ENGINE_NAME_FALLBACK := {"Guard_Loop": "Guard"}

# =====================================================================
# §1 伤害公式
# ---------------------------------------------------------------------
# 三个权重项**全部取自动画的自定义属性**（由 Blender 侧实测写入）：
#   antic_frame     前摇帧数   —— 动作蓄得越久，打得越重
#   hitstop_frames  打击停顿帧 —— 命中停顿越长，说明这一下越"实"
#   root_motion_m   根位移     —— 冲得越远，动能越大
#
#   P_tier = 1.0
#          + antic_frame   / 60.0 * K_ANTIC     (每秒前摇 3.0 档)
#          + hitstop_frames        * K_HITSTOP  (每帧停顿 0.6 档)
#          + |root_motion_m|       * K_MOTION   (每米位移 2.0 档)
#
#   damage = round(P_tier * TIER_TO_DMG)
# =====================================================================
const K_ANTIC := 3.0
const K_HITSTOP := 0.6
const K_MOTION := 2.0
const TIER_TO_DMG := 5.0

# =====================================================================
# §2 移动速度公式
# ---------------------------------------------------------------------
# 由**骨骼实测腿长**与**动画单圈时长**推出，保证脚不打滑的期望值：
#
#   leg_len = thigh.length + shin.length = 0.410 + 0.412 = 0.822 m
#   步幅(走) = leg_len * 0.75   ← 常人的自然步幅约为腿长的 0.7~0.8 倍
#   步幅(跑) = leg_len * 1.50   ← 跑动步幅约为腿长的 1.4~1.6 倍
#
#   walk_speed = leg_len * 0.75 * 2步 / Walk_F.duration_s
#   run_speed  = leg_len * 1.50 * 2步 / Run.duration_s
# =====================================================================
const LEG_LEN_M := 0.822
const WALK_STEP_FACTOR := 0.75
const RUN_STEP_FACTOR := 1.50

# =====================================================================
# §4 判定体尺寸
# ---------------------------------------------------------------------
# 全部来自 `tools/measure_body_box.py` 的实测（把骨架摆到姿态、取变形后网格顶点）。
#
#   姿态        躯干带前后半深   全高
#   Idle_01       0.344         1.732
#   Walk_F        0.324         1.734
#   Crouch_Idle   0.397         1.488
#   Guard_Loop    0.466         1.718
#   Run           0.441         1.689
#
# 受击体半径取**最紧的一档**（行走 0.324）再收 8% → 0.30：
# 受击体是"被判定为身体"的体积，宁可略紧 —— 精度应该由攻击盒主导。
#
# 注意：截面上角色左手侧 = Blender +X → Godot **Z**（朝相机）；
#       对打方向 = 角色前后轴 → Godot **X**。所以受击体在 X 上量的是"前后半深"。
const HURTBOX_RADIUS := 0.30
const HURTBOX_HEIGHT := 1.732          # 待机姿态实测全高
const HURTBOX_HEIGHT_CROUCH := 1.488   # 下蹲姿态实测全高
## 推箱间距：两人前后相贴 → 中心距 = 2 × 半径。不许穿过对手。
const PUSH_SEPARATION := HURTBOX_RADIUS * 2.0

# =====================================================================
# §5 人定的数值（无法从动画推导，理由写在注释里）
# =====================================================================
const MAX_HP := 500
## 击倒阈值：单次伤害 ≥ 此值触发击飞/倒地流程。
## 依据：§1 公式下轻拳约 12、重拳约 21、终结技约 30；
## 取 18 让「重拳以上」进倒地，轻拳不进。
const KNOCKDOWN_DAMAGE := 18
## 防御减伤：举防时伤害 × 此系数，且不进倒地。
const GUARD_DAMAGE_SCALE := 0.15
## 受击僵直按伤害分档：轻/重
const HIT_HEAVY_DAMAGE := 18
## 击退距离 = damage * 此系数（米/点）。让伤害与击退量成正比。
const KNOCKBACK_PER_DAMAGE := 0.012
## 舞台半宽（米）= 7.5 → 舞台横穿 15 m。
## 依据：横穿时间 = 15 / walk_speed(≈1.03 m/s) ≈ 14.6 s，跑步 ≈ 4.9 s。
## 格斗游戏舞台的合理横穿时间在 8~15 s 之间。第一版取 6.0（11.7 s）偏窄，
## 场地两侧几乎是"贴脸就到边"；本轮要"空间扩展一些"，取 7.5 让场地真正有宽度感，
## 同时仍压在 15 s 以内（再宽就得走太久）。
const STAGE_HALF_WIDTH := 7.5

# =====================================================================
# §6 投技（抓取 / 擒抱 / 投掷）
# ---------------------------------------------------------------------
# 这一节只有**三个**人定的数，其余全部由实测数据推出来。
# =====================================================================
## 被抓者挣脱共需累计按下多少次"主动出招键"（拳脚或抓技都算）。
## 依据：Grab_Hold 循环一圈是 2.0 s，正常人手速在 2 s 里能按 6 下以上；
## 所以 6 是一个"手快就能跑掉、发呆就会被投"的阈值。
const GRAB_MASH_BREAK := 6
## 被投出去之后飞多远（米）= 抓住时两人的间距 × 这个系数。
## 依据：投出去至少要把人从"抓住的位置"挪到"抓不到的位置"，
## 所以以抓取间距为基准放大；1.4 倍后约 1.5 m，正好半步到一步开外。
const THROW_FLIGHT_K := 1.4
## 挣脱成功的瞬间双方各往后退开多少米。
## 这是人定的：资产里没有"挣脱"这一段动画，退开量只能定。
## 取 0.30 m ≈ 腿长的三分之一，读起来像"被顶开一步"。
const BREAK_PUSH := 0.30

# --- 运行时推算 ---
## 抓取手能够到的距离（米）—— 取实测的最远抓取点。
var grab_reach := 0.0
## 被擒者中心与抓取者中心的距离（米）= 抓取手可达距离本身。
##
## ---------------------------------------------------------------------------
## **这里第一版是错的，而且错得很隐蔽**（出图才看出来两个人穿模在一起）。
##
## 原来的写法是 `grab_reach − HURTBOX_RADIUS`，理由写的是
## "reach 是手的世界坐标，手够到的是身体的近侧表面，身体中心还要再往里一个半径"。
## 那句话本身没错 —— 但它**减错了对象**：
##
##   · `reach_m` 量的是 hand.R 骨骼的**尾端**（见 measure_hit_points.py 的
##     `pb.tail`），那是手掌的**外缘**，不是手心。手心在它**内侧** ~0.11 m。
##   · 更关键的是：`Grab_Hold` 这个姿势**躯干和手臂都前伸得很厉害** —— 实测
##     胸口在自己原点前 +0.66 m、手在 +1.27 m。也就是说"手到原点"的 1.27 m
##     里，有 0.66 m 是**身体自己前倾**挣来的，不是手臂跨出去的。
##
##   于是"减去一个受击体半径"把对手往里拉了 0.30 m，直接拉进了抓取者的身体里。
##
## 实测（tools/probe_grab.gd）：
##   间距 1.063 m → 骨骼空间里两人 X 区间重叠 **+0.65 m**，手插进对手身体 +0.54 m
##   间距 1.363 m → 手正好按在对手近侧肩臂上（出图确认，见 docs/shots/grab_probe/）
##
## 所以取 **`grab_reach` 本身**：含义是"被擒者站在抓取手刚好够到的边界上"。
## 这个选择不只是好看 —— 它同时保证了 `hold_distance ≤ grab_reach`，
## 也就是"抱着的人一定还在自己能抓到的范围内"，抓取状态自洽。
var grab_hold_distance := 0.0
## 一次擒抱最多能抱多久（秒）= `Grab_Hold` 循环一圈的时长。
## 超时自动投出去 —— 否则玩家可以抱着不放到天荒地老。
var grab_hold_max := 0.0
## 投出去之后被投者滑行的距离（米）。
var throw_flight := 0.0

## 交战距离：由实测的前排起手技可达距离推出（前排 = 轻拳 / 重拳）。
##   engage = (Light_01.reach + Heavy_01.reach) / 2 + HURTBOX_RADIUS
##          = (0.793 + 0.970) / 2 + 0.30 = 1.18 m
## 含义：站在这个距离上，轻拳与重拳都能命中；再远只有冲刺攻击够得着。
var engage_distance := 1.18
## 双方初始间距 = 交战距离（开局站在"刚好够得着"的位置）。
var start_gap := 1.18

# =====================================================================
# §7 可拾取物（地面上的箱子）
# ---------------------------------------------------------------------
# 需求："地面可以拿取的东西，可以丢出去，也可以拿在手里砸，东西可以被打碎，
#       打中后多次也会坏掉。"
#
# 这一节里**所有人定的数只有两个**（尺寸倍率、打几下坏），
# 其余（耐久、容器伤害、投掷弹道、拾取可达）全部由实测数据推出来。
#
# 资产侧没有"箱子"这个对象 —— 所以它是**程序化生成**的（和 Stage / Vfx 同一个路子），
# 不是新增动画、也不是新增资产。
# =====================================================================
## 物体一边的尺寸相对**实测受击体半径**的倍率（三档）。
##
## 受击体半径 0.30 m 量的是"身体的半深"（§4 实测），一个能抱在怀里的箱子，
## 一边大约是它的 1.1 / 1.5 / 1.9 倍 → 0.33 / 0.45 / 0.57 m。
## 三档是刻意的：小件轻、抡起来快；大件重、看得见、砸得狠 —— 一眼能分辨。
const PROP_SIZE_K := [1.1, 1.5, 1.9]
## 打几下会坏。参照物是**重拳**（单发伤害最高的拳脚）：3 下 = 耐久 63。
## 于是实际手感是：重拳 21 伤 → 3 下碎；轻拳 12 伤 → 6 下碎；冲刺 26 伤 → 3 下碎。
## "打中后**多次**也会坏掉"这条要求就落在 63 这个耐久上（不是 1~2 下就碎）。
const PROP_HITS_TO_BREAK := 3
## 碎掉之后多久回来。**以"一次擒抱的时长"为单位**，而不是另填秒数 ——
## 这个游戏里 2.0 s（`Grab_Hold` 一圈）就是"一个动作周期的标准长度"，
## 复位间隔取它的 2 倍 = 4.0 s：比一个动作长（不会刚碎就冒出来）、
## 又不到一轮交战（4 s 足够把 5 个箱子里的某一个忘掉再想起来）。
## 依据：`grab_hold_max = duration("Grab_Hold") = 2.0 s`（见 §6）。
const PROP_RESPAWN_K := 2.0
## 场上同时存在几个箱子。**人定**。
## 依据：舞台加宽后横穿 15 m（§5）。5 个 → 平均每 3 m 一个，
## 走两步就有得捡，又不至于"满地都是方块"把地面网格盖掉。
## 和 `PROP_SIZE_K` 的三档配着看：5 个箱子 = 三档尺寸各出现一次以上，一眼能分大小。
const PROP_COUNT := 5

# --- 运行时推算（道具）---
## 三档边长（米）= HURTBOX_RADIUS × 上面的倍率。
var prop_sizes: Array[float] = []
## 物体耐久 = damage(Heavy_01) × PROP_HITS_TO_BREAK。
## **用"重拳"而不是另填一个数**：重拳是单发最重的拳脚，把它当"一下"最自然。
var prop_max_hp := 0
## 把物体**抡在人身上**时，物体自己贡献的那份伤害（= 一次标准重击的量）。
##
## 为什么是"耐久 ÷ 打几下"而不是另填一个数：这两个数本来就是同一个量 ——
## "打它一下扣多少"与"拿它打人一下多重"在物理上是同一件事（同一个冲量）。
## 所以它 = round(prop_max_hp / PROP_HITS_TO_BREAK) = 21 = 重拳的伤害。
var prop_impact_damage := 0
## 拾取可达距离（米）= **抓取手可达距离本身**。
##
## 理由：拾取用的就是"伸手去抓"那**一个**动作（`Grab_Start`）——
## 所以"手能伸多远"只能有一个出处，不另填一个数。
## （第一版想用 `Low_Attack` 的 0.883 m，理由是"它够向地面"；但那是**高度**上的
## 理由，被下面的 `prop_pickup_height` 接管了。距离上应该和抓取同一个手势。）
##
## 代价要说清：1.36 m 是"抓人"的距离，拿它捡地上的东西其实伸得有点远 ——
## 换来的好处是"按 E 能拿到的东西"和"按 G 能抓到的人"用的是同一份几何，
## 不会出现两个只在几厘米上打架的阈值。
var prop_pickup_reach := 0.0
## 贴地交互带的高度（米）= `Ground_Smash` 的实测手地接触高度 0.2923 m。
##
## 用途：箱子躺在地上（中心高度 = 边长的一半 ≈ 0.17~0.29 m），而**拳脚的判定点
## 都在半身高以上**（轻拳打在胸口）。如果"打箱子"也硬用攻击自己的判定高度，
## 站着出拳永远打不到地上的箱子 —— 用户会觉得"箱子打不碎"。
## 所以和箱子交互一律**换成这条贴地带来判**：带上沿 = 2 × 0.2923 = 0.585 m，
## 正好罩住三档箱子（最大 0.57 m 边长 → 顶面 0.57 m）。
##
## 这个数仍然有出处：它是资产里唯一一处"手够到地面"的实测高度。
var prop_pickup_height := 0.0
## 投掷弹道 —— **全部由 `Throw` 段自己的实测数据推出来**，没有一个是"调"的：
##
##   出手点高度 h = Throw 判定帧上的 hand.R 高度 = 1.1347 m（manifest hit_points[0]）
##   飞行时间   t = 投掷段**剩余**时长 = (frames[1] − hit_frame)/60 = (60−28)/60 = 0.5333 s
##   落地重力   g = 2h / t²  ← 由"平抛出去、恰好在这段时间里落地"唯一解出 = 7.98 m/s²
##   水平速度   v = throw_flight / t = 1.908 / 0.5333 = 3.577 m/s
##
## 也就是说：**扔多远沿用"扔人"的那一个距离**（同一个动作、同一份力气），
## 弧线则由"手的高度"和"剩下的时间"唯一确定 —— 不需要另填一个重力常数。
## （算出来的 7.98 m/s² 顺带是个好证据：它离真实重力 9.8 不远，
##   说明"手在 1.13 m、半秒落地"这件事本来就是按真实物理画出来的。）
var prop_throw_speed := 0.0
var prop_throw_gravity := 0.0
var prop_throw_release_height := 0.0

# =====================================================================
# §8 空间立体化（纵向）
# ---------------------------------------------------------------------
# 需求："地面除了前后还有上下，空间可以扩展一些。"
#
# 横向由 §5 的 STAGE_HALF_WIDTH 负责（6.0 → 7.5）。纵向这一半落到**判定**上：
# 跳跃期间把受击体按动画的骨盆抬升量一起抬上去。
#
# **为什么不给角色加"世界 Y 位移"**：跳跃是动画驱动的（根节点 y 恒为 0，
# 弹道在骨盆上，见 docs/操作说明.md §4.2）。再叠一层世界位移就是双重位移 ——
# 人会飞两倍高。正确做法是让**受击体**跟着骨盆走：身体在哪儿，被打的判定就在哪儿。
#
# 实测（tools/probe_jump.gd，逐帧打印骨盆世界 Y）：
#   骨盆静止位姿 0.9000 m ；Idle_01@0 = 0.8293 m（作为"贴地基准"）
#   起跳蓄力最低 −0.203 m → 最高 **+1.1236 m**（起跳后 0.833 s，在 Jump_Up 末）
#   脚尖离地 62 帧 = 1.033 s
#   空中轻/重击自己那条弹道从 +1.1236 起（= 跳跃顶点），落到 +0.098 / +0.310
#
# 抬起来之后受击体从 [0, 1.732] 变成 [1.124, 2.856]，于是纵向真的成立：
#   · 下段攻击（命中点高 0.389 m）打跳跃中的人 **落空** —— 跳能躲下段
#   · 空中重击（1.578 m）与空中轻击（2.137 m）**刚好落在**抬起的受击体上
#
# ---------------------------------------------------------------------------
# 另一个由纵向带出来的结论：**空中家族里只有一段能打到站在地上的人**。
#
# 判定盒以命中点为中心、高 `HITBOX_HEIGHT = 0.65`，所以它覆盖
# [height − 0.325, height + 0.325]；站立受击体是 [0, 1.732]。
#   空中轻击 2.1369 → [1.812, 2.462] —— **够不到**（1.812 > 1.732）
#   空中重击 1.5775 → [1.253, 1.903] —— 重了 0.48 m ✅
# 于是"跑动跳踢"只能用空中重击（`Fighter.JUMP_KICK_CLIP`），
# 这不是审美选择 —— 用空中轻击会**物理上打不中人**。
#
# 飞踢的向前动量也不另填一个速度：它就是**奔跑速度**（§2 推出的 `run_speed`）。
# 跑动跳踢是"跑动的延续"，动量当然还是跑动的那一个。
# =====================================================================
## 抬升低于此值视为"贴地"（米）。2 cm ≈ 画面上 4.7 px（1 m ≡ 236 px），
## 低于它读不出"浮空"，却会被站姿各段之间的几毫米起伏误触发。
const AIRBORNE_RISE_MIN := 0.02
## 骨盆的"贴地基准"（米）—— 由 Fighter 在 _ready 时实测 Idle_01@0 写入，
## 不在这里写死：写死的话资产一旦调整站姿高度，这里的判据就整体漂了。
## 兜底值 = 探针测到的 0.8293，只在采样失败时用到。
const PELVIS_GROUND_FALLBACK := 0.8293


# --- 运行时数据 ---
var manifest: Dictionary = {}
var clips: Dictionary = {}          # clip_name -> Dictionary（已归一化）
var group_names: Array = []         # ["Locomotion", ...]
var damage_table: Dictionary = {}   # clip_name -> int
## 清单名 -> 引擎名（只含不一致的项）
var engine_name_fixups: Dictionary = ENGINE_NAME_FALLBACK
var walk_speed := 1.0
var run_speed := 3.0
var load_errors: Array[String] = []


func _ready() -> void:
	_load_engine_names()
	_load_manifest()
	_build_tables()
	_report()


func _load_engine_names() -> void:
	if not FileAccess.file_exists(ENGINE_NAMES_PATH):
		load_errors.append("找不到引擎名差异表: %s（退到兜底表）" % ENGINE_NAMES_PATH)
		return
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(ENGINE_NAMES_PATH))
	if typeof(parsed) != TYPE_DICTIONARY:
		load_errors.append("引擎名差异表解析失败: %s" % ENGINE_NAMES_PATH)
		return
	var fx: Variant = (parsed as Dictionary).get("fixups")
	if typeof(fx) != TYPE_DICTIONARY:
		load_errors.append("引擎名差异表缺少 fixups 字段")
		return
	engine_name_fixups = fx


# ---------------------------------------------------------------------
# 装载
# ---------------------------------------------------------------------
func _load_manifest() -> void:
	if not FileAccess.file_exists(MANIFEST_PATH):
		load_errors.append("找不到 manifest: %s" % MANIFEST_PATH)
		return
	var text := FileAccess.get_file_as_string(MANIFEST_PATH)
	var parsed: Variant = JSON.parse_string(text)
	if typeof(parsed) != TYPE_DICTIONARY:
		load_errors.append("manifest 解析失败: %s" % MANIFEST_PATH)
		return
	manifest = parsed
	var raw: Dictionary = manifest.get("clips", {})
	for k in raw.keys():
		clips[k] = _normalise(raw[k])
	group_names = (manifest.get("groups", {}) as Dictionary).keys()


## 把 JSON 里的 null / 字符串 "None" / 数组 统一成 GDScript 好用的形态。
func _normalise(d: Dictionary) -> Dictionary:
	var out := d.duplicate(true)
	out["frames"] = _as_frames(out.get("frames"))
	out["duration_s"] = _as_float(out.get("duration_s"))
	out["loop"] = bool(out.get("loop", false))
	out["antic_frame"] = _as_opt_int(out.get("antic_frame"))
	out["hit_frame"] = _as_opt_int(out.get("hit_frame"))
	out["cancel_frame"] = _as_opt_int(out.get("cancel_frame"))
	out["hitstop_frames"] = _as_opt_int(out.get("hitstop_frames"))
	out["root_motion_m"] = _as_vec2(out.get("root_motion_m"))
	return out


func _as_frames(v: Variant) -> Array:
	if typeof(v) == TYPE_ARRAY and (v as Array).size() >= 2:
		return [float(v[0]), float(v[1])]
	return [0.0, 0.0]


func _as_float(v: Variant) -> float:
	if typeof(v) == TYPE_FLOAT or typeof(v) == TYPE_INT:
		return float(v)
	return 0.0


func _as_opt_int(v: Variant) -> Variant:
	if typeof(v) == TYPE_FLOAT or typeof(v) == TYPE_INT:
		return int(v)
	if typeof(v) == TYPE_ARRAY and (v as Array).size() > 0:
		# 大招这种多段攻击的元数据是一个数组，取最大值当代表值
		var m := 0
		for x in v:
			if typeof(x) == TYPE_FLOAT or typeof(x) == TYPE_INT:
				m = maxi(m, int(x))
		return m
	return null


func _as_vec2(v: Variant) -> Vector2:
	if typeof(v) == TYPE_ARRAY and (v as Array).size() >= 2:
		return Vector2(float(v[0]), float(v[1]))
	return Vector2.ZERO


# ---------------------------------------------------------------------
# 推导
# ---------------------------------------------------------------------
func _build_tables() -> void:
	for name in clips.keys():
		damage_table[name] = _calc_damage(name)

	var walk_dur := duration("Walk_F")
	var run_dur := duration("Run")
	if walk_dur > 0.0:
		walk_speed = LEG_LEN_M * WALK_STEP_FACTOR * 2.0 / walk_dur
	if run_dur > 0.0:
		run_speed = LEG_LEN_M * RUN_STEP_FACTOR * 2.0 / run_dur

	# 交战距离：前排起手技（轻/重）实测可达距离的均值 + 受击体半径
	var lr := _reach("Light_01")
	var hr := _reach("Heavy_01")
	if lr > 0.0 and hr > 0.0:
		engage_distance = (lr + hr) * 0.5 + HURTBOX_RADIUS
	start_gap = engage_distance

	# §6 投技：全部从实测的抓取点推出来（见 §6 的注释）
	var gr := max_reach("Grab_Start")
	if gr > 0.0:
		grab_reach = gr
		# 被擒者站在"抓取手刚好够到的边界"上（= grab_reach 本身）。
		# 别再减受击体半径 —— 那是第一版的 bug，会把对手拉进抓取者身体里。
		# 下限用推箱间距兜住：两个人不许重叠到比"并排站着"还近。
		grab_hold_distance = maxf(gr, PUSH_SEPARATION)
	var gh := duration("Grab_Hold")
	if gh > 0.0:
		grab_hold_max = gh
	throw_flight = grab_hold_distance * THROW_FLIGHT_K

	_build_prop_tables()


## §7 + §8 的推算。**每一条都写清它抄的是哪个实测值**。
func _build_prop_tables() -> void:
	# --- 尺寸：受击体半径 × 三档倍率 ---
	prop_sizes = []
	for k in PROP_SIZE_K:
		prop_sizes.append(HURTBOX_RADIUS * float(k))

	# --- 耐久：重拳伤害 × 打几下 ---
	var heavy: int = _calc_damage("Heavy_01")
	prop_max_hp = heavy * PROP_HITS_TO_BREAK
	# 容器伤害 = 一次标准重击的量（见 §7 的注释：这和"打它一下扣多少"是同一个量）
	prop_impact_damage = int(round(float(prop_max_hp) / float(maxi(1, PROP_HITS_TO_BREAK))))

	# --- 拾取：距离复用"伸手抓取"的实测点；高度复用"手砸到地面"的实测点 ---
	# 两个数各管一维，都不另填（见 §7 上面两段注释）。
	prop_pickup_reach = grab_reach
	prop_pickup_height = first_hit_height("Ground_Smash")

	# --- 投掷弹道：由 Throw 自己的"出手帧 + 剩下的时间"唯一解出 ---
	var hp: float = first_hit_height("Throw")
	var hf: Variant = hit_frame("Throw")
	var frames_len: Array = frames("Throw")
	if hp > 0.0 and hf != null and frames_len.size() >= 2:
		var t: float = (float(frames_len[1]) - float(hf)) / 60.0
		if t > 0.0:
			prop_throw_release_height = hp
			prop_throw_speed = throw_flight / t
			# 平抛、恰好落地：h = g·t²/2 ⟹ g = 2h/t²
			prop_throw_gravity = 2.0 * hp / (t * t)


## 某段动画第一段命中点的前方可达距离（实测值，米）。
func _reach(clip_name: String) -> float:
	var pts: Variant = clip(clip_name).get("hit_points")
	if pts is Array and (pts as Array).size() > 0:
		return absf(float((pts as Array)[0].get("reach_m", 0.0)))
	return 0.0


## 某段动画最远的命中点可达距离（多段取最大）。
func max_reach(clip_name: String) -> float:
	var pts: Variant = clip(clip_name).get("hit_points")
	if not (pts is Array):
		return 0.0
	var m := 0.0
	for p in pts:
		m = maxf(m, absf(float(p.get("reach_m", 0.0))))
	return m


## 某段动画第一段命中点的高度（米，实测）。
##
## 抓取判定要用它：抓取打在 1.13 m（手的高度）而不是 0.9 m（胸口）——
## 判定盒放错高度会让"贴着地蹲着的人反而抓不到"。
func first_hit_height(clip_name: String) -> float:
	var pts: Variant = clip(clip_name).get("hit_points")
	if pts is Array and (pts as Array).size() > 0:
		return float((pts as Array)[0].get("height_m", 1.10))
	return 1.10


func _calc_damage(clip_name: String) -> int:
	var c: Dictionary = clips.get(clip_name, {})
	if c.is_empty():
		return 0
	var antic: float = float(c["antic_frame"]) if c["antic_frame"] != null else 0.0
	var hitstop: float = float(c["hitstop_frames"]) if c["hitstop_frames"] != null else 0.0
	var motion: float = (c["root_motion_m"] as Vector2).length()
	var tier: float = 1.0 \
		+ antic / 60.0 * K_ANTIC \
		+ hitstop * K_HITSTOP \
		+ motion * K_MOTION
	return int(round(tier * TIER_TO_DMG))


func _report() -> void:
	if not load_errors.is_empty():
		for e in load_errors:
			push_error("[GameDB] %s" % e)
		return
	print("[GameDB] 装载 %d 段 clip，%d 个分组" % [clips.size(), group_names.size()])
	print("[GameDB] walk_speed=%.3f m/s  run_speed=%.3f m/s" % [walk_speed, run_speed])
	print("[GameDB] engage=%.3f m  受击体 r=%.2f h=%.3f  舞台半宽=%.1f" % [
		engage_distance, HURTBOX_RADIUS, HURTBOX_HEIGHT, STAGE_HALF_WIDTH])
	print("[GameDB] 引擎名差异表 %d 条 %s" % [
		engine_name_fixups.size(), str(engine_name_fixups)])
	print("[GameDB] 投技 抓取手可达=%.3f m  被擒间距=%.3f m  擒抱上限=%.2f s  投出滑行=%.3f m" % [
		grab_reach, grab_hold_distance, grab_hold_max, throw_flight])
	print("[GameDB] 道具 边长=%s m（受击体半径 × %s）  耐久=%d（重拳 %d × %d 下）  容器伤害=%d  场上 %d 个" % [
		str(prop_sizes), str(PROP_SIZE_K), prop_max_hp,
		damage("Heavy_01"), PROP_HITS_TO_BREAK, prop_impact_damage, PROP_COUNT])
	print("[GameDB] 道具 拾取可达=%.3f m（= 抓取手可达）× 贴地带高 %.4f m（= Ground_Smash 手地高度）" % [
		prop_pickup_reach, prop_pickup_height])
	print("[GameDB] 投掷 出手高=%.4f m（Throw 判定帧）× 剩 %.3f s ⟹ 重力 %.2f m/s²  初速 %.3f m/s" % [
		prop_throw_release_height,
		(duration("Throw") * 60.0 - float(hit_frame("Throw"))) / 60.0,
		prop_throw_gravity, prop_throw_speed])


# ---------------------------------------------------------------------
# 查询接口
# ---------------------------------------------------------------------
func has_clip(n: String) -> bool:
	return clips.has(n)


## 清单名 -> Godot 里 AnimationPlayer 的实际动画名。
## **所有 _play / has_animation 都必须走这里**，不许直接拿清单名去问引擎。
func engine_name(n: String) -> String:
	return String(engine_name_fixups.get(n, n))


func clip(n: String) -> Dictionary:
	return clips.get(n, {})


func duration(n: String) -> float:
	return float(clip(n).get("duration_s", 0.0))


func is_loop(n: String) -> bool:
	return bool(clip(n).get("loop", false))


func frames(n: String) -> Array:
	return clip(n).get("frames", [0.0, 0.0])


func frame_count(n: String) -> float:
	var f: Array = frames(n)
	return f[1] - f[0]


func root_motion(n: String) -> Vector2:
	return clip(n).get("root_motion_m", Vector2.ZERO)


func damage(n: String) -> int:
	return int(damage_table.get(n, 0))


func antic_frame(n: String) -> Variant:
	return clip(n).get("antic_frame")


func hit_frame(n: String) -> Variant:
	return clip(n).get("hit_frame")


func cancel_frame(n: String) -> Variant:
	return clip(n).get("cancel_frame")


func hitstop_frames(n: String) -> Variant:
	return clip(n).get("hitstop_frames")


## 全 clip 名单，按 manifest 的登记顺序（= 清单编号顺序）。
func all_clip_names() -> Array:
	var out: Array = []
	for c in clips.values():
		out.append(c.get("code", ""))
	var pairs: Array = []
	for n in clips.keys():
		pairs.append([str(clips[n].get("code", "")), n])
	pairs.sort_custom(func(a, b): return a[0] < b[0])
	return pairs.map(func(p): return p[1])
