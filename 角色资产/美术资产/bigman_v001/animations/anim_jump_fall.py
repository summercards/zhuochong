"""anim_jump_fall —— A12 `Jump_Fall` 下落。

设计（对着清单「下一支计划 —— A12」逐条落）：
    定位      下落：**身体展开、双腿寻找落点**（清单原文 A12 条目）。
    接 A11    首帧**逐位**等于 `Jump_Up@12`（世界矩阵 max_delta = 0）—— 那一帧就是
              弹道离散顶点（竖速 0.139 mm/帧），所以 A12 全段是**自由落体**。
    时长      24 帧 / 0.400 s @60fps，**非循环**（`loop=False`）。
    结构      FALL_EARLY 0~10  骨盆弹道下落；双腿由收展开（竖距 L 640→739 / R 618→722），
                               向地面"探"落点；双臂从护体架势向外张开找平衡。
              FALL_SEEK  10~20  继续下落；双腿接近伸直（竖距 → L 782 / R 768），
                               双脚略前伸、脚背略勾（准备接触）；双臂外张到最大。
              PRE_LAND   20~24  末段下落；双臂定格；双腿**不许提前屈膝**（屈膝是 A13 的戏）。
    原地      清单 §0.4：Jump 属"普通移动"，**不给 Root Motion**（`root_motion_m=[0,0]`）。

---------------------------------------------------------------------------
本支的六条关键做法

1. **首帧不重算，直接读 A11 已验收的成品**（同 A11 读 A10 的做法）。
   `aim_carry` / `jump_up_aim_carry` 是有状态的 **carry 接力**（基准 = 上一帧已达成
   朝向），单跑一次 `build_pose(12)` 与"从 0 连跑到 12"结果**不同**。
   → `JU.capture_start(arm, actions["Jump_Up"], 12)` 读回全部骨的 euler/location
   + 六根臂骨的世界四元数（当 A12 的 carry 起点）。
   ★ 读后**必须** `arm.animation_data.action = None`：留着 A11 的话，后续
   `view_layer.update()` 会在某些帧把 pelvis 的 f-curve 值重新压回 pose bone，
   尺子被污染（A11 实测 `ik_reach_ok` 因此假红 30.35 mm）。

2. **骨盆 z 不是"再落一点"，是同一组常量的直接续写。**
   `z(f) = TAKEOFF_PELVIS_Z + v₀·(BASE_T+f) − ½g(BASE_T+f)²`，
   `BASE_T = JU.BASE_T + JU.TOTAL = 16 + 12 = 28`（不硬编码 16 / 12）。
   与 A10/A11 共用 `JS.TAKEOFF_PELVIS_Z / JS.TAKEOFF_SPEED / JS.G_PER_FRAME`
   ⟹ "首帧等于 A11 f12" 与 "全段是弹道" 是**同一件事**。
   门禁 `fall_ballistic_ok` 拿同一函数回比（A11 实测误差 0.0001 mm）。

3. **腿仍是"髋-踝竖距"轨，不是独立踝轨迹**（同 A10/A11）。
   空中骨盆按弹道落，若踝另有独立轨，两者速率一旦不同就会把腿拉直或拉穿
   （|髋−踝| 有 0.822 m 上限）。VERT 从 `JU.VERT_END_A11`（L 0.640 / R 0.618）起算、
   收到 `VERT_END_A12`，两个**都从上游取/分开给**（交错架势下同一条曲线对两腿的
   膝角增量不同）。收腿量走 `u = 2s − s²`（单调增、增量单调减）⟹ "越接近地面伸得越慢"
   是构造出来的，末段自然"定格"。
   ★ **腿长上限是本支的真约束**：vert 0.782 时 `|髋−踝| = √(0.782²+0.221²) = 0.813 m`，
   只剩 9 mm 余量（上限 0.822）。所以 VERT_END 不能按"腿完全伸直"给，
   要按**可达性**给 —— 这也是 `ik_reach_ok`（≤5 mm）真正在守的东西。

4. **"双臂外张"量的是两拳世界 X 间距**（清单下一支计划给的判据）。
   为什么不量"拳相对胸骨顶的位移"：骨盆在这 24 帧里落了 813 mm，任何绝对量
   都会被下落淹没（A06 踩坑 5 / A11 口径）。X 间距与下落正交，是干净的尺子。
   实测 A11 末 ≈ 0.28 m（护体架势拳在胸前），A12 末 ≈ 1.1 m（张开到体侧）。

5. **roll 限速器与 `Y_SAFE` 沿用 A11 的成品旋钮**（`JU.jump_up_aim_carry` +
   `JS.Y_SAFE = 28`、`JS.ROLL_RANGE = 150`）。A11 实测 `Y_SAFE` 的拐点就是 28：
   再低只增 roll 用量、不改善 `max_frame_step_deg`。本支摆臂幅度（前臂 110°）
   与 A11（108°）同量级，沿用同一组值。

6. **`decel_smooth_ok` 本支不适用，显式跳过**（清单下一支计划明确要求）。
   它的口径是"末 6 帧角度增量绝对值**单调收敛**"，那是给"收招不许瞬停"写的；
   下落段末段是**加速**，把它当门禁等于要求"越落越慢"—— 与 `accelerating_ok` 互斥。
   同理 `ground_contact_ok` / `no_foot_slide` 全段离地不适用，值记 None 并登记理由
   （A11 的口径：None 计为"不适用"，不是"通过"）。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python anim_jump_fall.py
    SKIP_RENDER=1 只跑门禁（迭代用）。
"""

import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A          # noqa: E402
import anim_idle_01 as I1     # noqa: E402
import anim_walk_f as WF      # noqa: E402
import anim_turn as TURN      # noqa: E402
import anim_crouch as CR      # noqa: E402
import anim_jump_start as JS  # noqa: E402
import anim_jump_up as JU     # noqa: E402

NAME = "Jump_Fall"
TOTAL = 24                    # 0.400 s @ 60 fps
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"

ARM_BONES = JS.ARM_BONES

# ---------------------------------------------------------------- 弹道继承
# 从离地（A10 的 TAKEOFF）算起的帧数。**不许硬编码 16 / 12**：上游改长度自动跟随。
BASE_T = JU.BASE_T + JU.TOTAL            # 16 + 12 = 28（= A11 末帧 = 离散顶点）
T_APEX = JS.TAKEOFF_SPEED / JS.G_PER_FRAME
G_PER_FRAME = JS.G_PER_FRAME


def pelvis_z(frame):
    """骨盆世界 z（米）—— A10/A11 同一解析弹道在 A12 帧号上的续写。"""
    t = BASE_T + frame
    return (JS.TAKEOFF_PELVIS_Z + JS.TAKEOFF_SPEED * t
            - 0.5 * G_PER_FRAME * t * t)


Z_START = pelvis_z(0)
Z_END = pelvis_z(TOTAL)

# ---------------------------------------------------------------- 收腿（髋-踝竖距，米）
VERT_FROM = dict(JU.VERT_END_A11)        # A11 末帧 {L: 0.640, R: 0.618}
# 末端竖距：L 0.640→0.782（+142 mm）、R 0.618→0.768（+150 mm）。
# 上限由 `legs_extend_ok`（总量 ≥140 mm）与**腿长可达性**共同约束 —— 见文件头第 3 条。
VERT_END_A12 = {"L": 0.782, "R": 0.768}

# ---------------------------------------------------------------- 躯干（度）
# 全部 f0 取值 = A11 末键（`JU.XXX[-1][1]` 式取法，不硬编码 → 上游改了自动跟随）。
PELVIS_RX = ((0, JU.PELVIS_RX[-1][1]), (12, 0.9), (TOTAL, 1.5))
SPINE01_RX = ((0, JU.SPINE01_RX[-1][1]), (12, 1.5), (TOTAL, 1.2))
SPINE02_RX = ((0, JU.SPINE02_RX[-1][1]), (12, 1.4), (TOTAL, 1.2))
CHEST_RX = ((0, JU.CHEST_RX[-1][1]), (12, 2.0), (TOTAL, 2.6))
# 头往下找落点：neck 略回、head 前屈加大（rx>0 = 前屈/低头）。
NECK_RX = ((0, JU.NECK_RX[-1][1]), (12, -3.8), (TOTAL, -2.8))
HEAD_RX = ((0, JU.HEAD_RX[-1][1]), (12, 6.0), (TOTAL, 8.0))
# 肩：手臂外张时肩自然打开（rx>0 = 抬），从 A11 末的 −1.0 放到 −7.0。
SHOULDER_RX = ((0, JU.SHOULDER_RX[-1][1]), (12, -4.0), (TOTAL, -7.0))
# 骨盆水平：全程原地（清单 §0.4；下落没有水平运动）。
PELVIS_Y_KEYS = ((0, JU.PELVIS_Y_KEYS[-1][1]), (TOTAL, 0.0))

# ---------------------------------------------------------------- 足尖（度）
# 轴语义（`rig_axis_map` + `world_tip_deg`）：**正 = 脚尖朝下（压脚背/踮脚）**，
# **负 = 脚尖朝上（勾脚）**。清单原文 A12 写「脚背略勾（准备接触）」⟹ 收到负值。
# 起点取 A11 末帧的真值（`JU.TIP_KEYS[-1][1]` = 8.0），不硬编码。
TIP_KEYS = ((0, JU.TIP_KEYS[-1][1]), (10, 2.0), (20, -4.0), (TOTAL, -6.0))

# ---------------------------------------------------------------- 踝的水平前伸
# "双脚略前伸（准备接触）"：踝 y 向前推 30 mm。上限由腿长可达性定 ——
# 前伸每多 10 mm，末帧 |髋−踝| 就多 ~9 mm，而余量只剩 ~9 mm（见文件头第 3 条）。
FORWARD_REACH = 0.030

# ---------------------------------------------------------------- 手臂
# "身体展开、双臂向外张开找平衡（不是完全平举）"。
# 方向语义：骨长方向（肩→肘 / 肘→腕 / 腕→拳）指向的世界单位向量。
# 目标：向前外下方张开 —— 与水平面约成 47°，所以**不是**平举，也**不再**是护体架势。
ARM_SPREAD = {
    "upperarm.L": (0.68, -0.36, -0.64),
    "forearm.L": (0.62, -0.48, -0.62),
    "hand.L": (0.56, -0.58, -0.59),
    "upperarm.R": (-0.68, -0.36, -0.64),
    "forearm.R": (-0.62, -0.48, -0.62),
    "hand.R": (-0.56, -0.58, -0.59),
}
# 张臂过程占用的帧数：0~20 张到最大，20~24 **定格**（PRE_LAND 段）。
ARM_FRAMES = 20

ANKLE_REST = {}
TARGETS = []
TRACE = []


def ankle_target(arm, frame, side):
    """该侧踝的世界目标位置。

    同 A10/A11 的"髋-踝竖距"轨：x 固定、y 随"略前伸"前移、z 由髋高减竖距给出。
    末段（frame > ARM_FRAMES）竖距曲线已趋平（`u` 增量 → 0），姿态自然定格。
    """
    rest = ANKLE_REST[side]
    s = frame / float(TOTAL)
    u = 2.0 * s - s * s                 # 单调增、增量单调减（同 A10 的 air_u）
    vert = VERT_FROM[side] + (VERT_END_A12[side] - VERT_FROM[side]) * u
    hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
    y = rest.y - FORWARD_REACH * u
    return Vector((rest.x, y, hip.z - vert))


def arm_dirs(frame):
    """手臂世界方向：A11 末的护体架势 →（张开）体侧外张。

    定时用 `JS._ease_ramp`（梯形速度剖面，两端速度为 0、中段匀速）。
    两端速度为 0 是关键：A11 的 f9~12 手臂已经**静止**（`u = 2s−s²` 在 s≈1 处
    增量趋 0），若本支 f1 就带速度，接缝上会出现一次速度跳变。
    """
    s = JS._ease_ramp(min(1.0, frame / float(ARM_FRAMES)))
    return {k: JS._slerp(JU.ARM_READY[k], ARM_SPREAD[k], s) for k in ARM_BONES}


# =============================================================== 姿态生成
def build_pose(arm, frame, record=False):
    """按帧构造完整姿态。（`record=True` 时把踝目标登记进 `TARGETS`）"""
    pose = {
        "pelvis": (TURN.track(PELVIS_RX, frame), 0.0, 0.0),
        "spine_01": (TURN.track(SPINE01_RX, frame), 0.0, 0.0),
        "spine_02": (TURN.track(SPINE02_RX, frame), 0.0, 0.0),
        "chest": (TURN.track(CHEST_RX, frame), 0.0, 0.0),
        "neck": (TURN.track(NECK_RX, frame), 0.0, 0.0),
        "head": (TURN.track(HEAD_RX, frame), 0.0, 0.0),
        "shoulder.L": (TURN.track(SHOULDER_RX, frame), 0.0, 0.0),
        "shoulder.R": (TURN.track(SHOULDER_RX, frame), 0.0, 0.0),
        "toe.L": (0.0, 0.0, 0.0),
        "toe.R": (0.0, 0.0, 0.0),
        "@loc": {"pelvis": A.wloc(0.0, TURN.track(PELVIS_Y_KEYS, frame),
                                  pelvis_z(frame) - 0.900)},
    }
    A.apply_pose(arm, pose)

    # 腿：真双骨 IK（A06/A07/A10/A11 的 `leg_to`）。膝弯方向固定世界 −Y（不转身）。
    for side in ("L", "R"):
        target = ankle_target(arm, frame, side)
        if record:
            TARGETS.append((frame, side, tuple(target)))
        TURN.leg_to(arm, pose, side, target, (0.0, -1.0))
    JU._unwrap_legs(arm, pose)

    # 足：先钉平到世界水平（rest 朝向），再绕世界 X 叠 tip 角（A10/A11 同路径）。
    tip = TURN.track(TIP_KEYS, frame)
    for side in ("L", "R"):
        name = "foot." + side
        A.keep_world_orientation(arm, name)
        WF.add_world_rx(arm, name, tip)
        pose[name] = JS._unwrap_xyz(
            JS._PREV_EULER.get(name),
            tuple(math.degrees(v)
                  for v in arm.pose.bones[name].rotation_euler))

    pose.update(A.FIST)
    dirs = arm_dirs(frame)
    # carry 接力（基准 = 上一帧已达成朝向）+ roll 分支搜索 + **roll 限速**
    # —— 直接用 A11 已验收的 `jump_up_aim_carry`，旋钮（Y_SAFE / ROLL_RANGE）同值。
    for bone in ARM_BONES:
        pose[bone] = JU.jump_up_aim_carry(arm, bone, dirs[bone], JU.ROLL_RATE)

    for name, value in pose.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)
    TRACE.append({
        "frame": frame,
        "euler": {b: tuple(round(v, 2) for v in pose[b]) for b in ARM_BONES},
        "quat": {b: arm.pose.bones[b].matrix.to_quaternion() for b in ARM_BONES},
        "roll": dict(JS.ARM_ROLL),
    })
    return pose


# =============================================================== 专属门禁
def vert_series(arm, action, frames):
    """逐帧"髋-踝竖距"（米）。`PROBE_BONES` 里没有 thigh / shin，只能现量。"""
    out = []
    for frame in frames:
        out.append(JU.hip_ankle_vert(arm, action, frame))
    return out


def reach_series(arm, action, frames):
    """逐帧 |髋−踝|（米）。上限 = `L_THIGH + L_SHIN` = 0.822 m，超了就静默截断。"""
    previous = JS._with_action(arm, action)
    out = []
    for frame in frames:
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()
        out.append({side: (Vector(A.bone_world(arm, "thigh." + side, "head"))
                           - Vector(A.bone_world(arm, "foot." + side, "head"))).length
                    for side in ("L", "R")})
    if previous is not None:
        arm.animation_data.action = previous
    return out


def fall_assertions(arm, action, samples, start_mats, sole, target_err, verts,
                    reach):
    res = {}
    frames = [s["frame"] for s in samples]
    pelvis = [Vector(s["pelvis"]) for s in samples]
    zs = [p.z for p in pelvis]
    rates = [(zs[i + 1] - zs[i]) * 1000.0 for i in range(len(zs) - 1)]

    # 0) 首帧必须**逐位**等于 `Jump_Up@12`（世界矩阵，不是 euler）。
    mats = CR.action_world_matrices(arm, action, 0)
    delta = CR.matrix_delta(mats, start_mats)
    res["first_frame_delta"] = float("%.3e" % delta)
    res["first_frame_matches_a11_ok"] = delta <= 1e-6

    # 1) **本支最该守的判据**：骨盆 z 逐帧与同一解析弹道比对。
    #    "下落"就是弹道，没有别的物理。
    err = max(abs(zs[i] - pelvis_z(frames[i])) for i in range(len(frames))) * 1000.0
    res["ballistic_max_err_mm"] = round(err, 4)
    res["fall_ballistic_ok"] = err <= 2.0

    # 2) **下落 == 匀加速**：竖速逐帧**严格递减**（越来越负），且末帧已加速到
    #    ≥1.0 m/s（解析值 −(0.449+24)·g ≈ −66.6 mm/帧）。这是 A11「减速上升」的镜像。
    mono = all(rates[i + 1] < rates[i] + 1e-9 for i in range(len(rates) - 1))
    res["rate_monotone_down"] = bool(mono)
    res["end_rate_mm_per_frame"] = round(rates[-1], 3)
    res["end_rate_mps"] = round(rates[-1] * A.FPS / 1000.0, 3)
    res["accelerating_ok"] = bool(mono) and rates[-1] <= -60.0
    res["accel_mm_per_frame2"] = round(rates[len(rates) // 2] - rates[len(rates) // 2 - 1], 4)
    res["g_mm_per_frame2"] = round(G_PER_FRAME * 1000.0, 4)
    res["start_rate_mm_per_frame"] = round((zs[1] - zs[0]) * 1000.0, 3)
    res["fall_mm"] = round((zs[0] - zs[-1]) * 1000.0, 1)
    res["start_pelvis_z_mm"] = round(zs[0] * 1000.0, 1)
    res["end_pelvis_z_mm"] = round(zs[-1] * 1000.0, 1)
    res["apex_offset_frames"] = round(BASE_T - T_APEX, 3)
    res["no_downward_not_applicable"] = "本支是下落段，A11 的 no_downward_ok 不适用"

    # 3) **双腿寻找落点**：髋-踝竖距全程**单调增**，总量 ≥140 mm。
    gains = {s: verts[-1][s] - verts[0][s] for s in ("L", "R")}
    vmono = {s: all(verts[i + 1][s] >= verts[i][s] - 1e-9
                    for i in range(len(verts) - 1)) for s in ("L", "R")}
    res["vert_start_mm"] = {s: round(verts[0][s] * 1000.0, 1) for s in ("L", "R")}
    res["vert_end_mm"] = {s: round(verts[-1][s] * 1000.0, 1) for s in ("L", "R")}
    res["legs_extend_gain_mm"] = {k: round(v * 1000.0, 1) for k, v in gains.items()}
    res["legs_extend_monotone"] = vmono
    res["legs_extend_ok"] = (all(v * 1000.0 >= 140.0 for v in gains.values())
                             and all(vmono.values()))

    # 3b) **腿长可达性**（本支的真约束，见文件头第 3 条）：末帧 |髋−踝| 与上限之比。
    limit = A.L_THIGH + A.L_SHIN
    res["leg_reach_limit_mm"] = round(limit * 1000.0, 1)
    res["leg_reach_end_mm"] = {s: round(reach[-1][s] * 1000.0, 1)
                               for s in ("L", "R")}
    res["leg_reach_max_mm"] = {s: round(max(r[s] for r in reach) * 1000.0, 1)
                               for s in ("L", "R")}
    res["leg_reach_ratio"] = {s: round(reach[-1][s] / limit, 4)
                              for s in ("L", "R")}
    res["leg_reach_headroom_mm"] = {s: round((limit - reach[-1][s]) * 1000.0, 1)
                                    for s in ("L", "R")}

    # 4) **屈膝留给 A13**：末帧膝弯**不**比 A11 末帧更大。
    bend = CR.knee_series(arm, action, frames)
    res["knee_bend_start_deg"] = {s: round(bend[0][s], 2) for s in ("L", "R")}
    res["knee_bend_end_deg"] = {s: round(bend[-1][s], 2) for s in ("L", "R")}
    res["knee_bend_delta_deg"] = {s: round(bend[-1][s] - bend[0][s], 2)
                                  for s in ("L", "R")}
    res["no_knee_bend_yet_ok"] = all(bend[-1][s] <= bend[0][s] + 1e-6
                                     for s in ("L", "R"))

    # 5) **双臂外张**。
    #    ★ 清单给的判据「两拳世界 X 间距 ≥0.45 m」是**必要不充分**的：它标注
    #    "A11 末 ≈ 0.28 m"，但那是**护体架势**（A01）的数 —— A11 只把手臂从
    #    `ARM_AIR` 收到护体架势的 **55%**（`ARM_GATHER`），实测末帧 X 间距是
    #    **521.3 mm**，本来就已经 > 0.45 m。照抄清单的阈值 ⟹ 手臂**一动不动**
    #    也能判绿（同 A02 踩坑 3 / A06 踩坑 5：尺子选错会假绿）。
    #    → 保留清单的绝对下限 `arms_spread_ok`，另加**增量**判据
    #    `arms_spread_gain_ok`（"张开"是**变化**，不是终态），阈值 350 mm
    #    ≈ 每侧拳外移 175 mm。两个都登记实测值，不放宽、只补上缺的那一半。
    def spread(sample):
        return abs(Vector(sample["hand.L.tail"]).x
                   - Vector(sample["hand.R.tail"]).x) * 1000.0

    res["fist_x_span_start_mm"] = round(spread(samples[0]), 1)
    res["fist_x_span_end_mm"] = round(spread(samples[-1]), 1)
    res["fist_x_span_max_mm"] = round(max(spread(s) for s in samples), 1)
    res["fist_x_span_gain_mm"] = round(spread(samples[-1]) - spread(samples[0]), 1)
    res["arms_spread_ok"] = spread(samples[-1]) >= 450.0
    res["arms_spread_gain_ok"] = res["fist_x_span_gain_mm"] >= 350.0
    res["arms_spread_plan_baseline_note"] = (
        "清单写'A11 末 ≈0.28 m'有误：那是 A01 护体架势的数；A11 只收到护体架势的"
        "55%，实测末帧 X 间距 521.3 mm ⟹ 清单阈值单独用会假绿")

    # 臂的"活着"量：**相对胸骨顶**的位移（不是世界位移 —— 骨盆这 24 帧落了 813 mm，
    # 绝对行程量的是"下落"，量不出"手臂动没动"；同 A06 踩坑 5 的口径）。
    travel = {}
    for side in ("L", "R"):
        base = (Vector(samples[0]["hand." + side + ".tail"])
                - Vector(samples[0]["chest.tail"]))
        travel[side] = max(
            (Vector(s["hand." + side + ".tail"]) - Vector(s["chest.tail"])
             - base).length for s in samples) * 1000.0
    res["fist_rel_travel_mm"] = {k: round(v, 1) for k, v in travel.items()}
    res["arm_travel_ok"] = all(v >= 100.0 for v in travel.values())

    # 6) 全段离地 —— 通用门禁的贴地窗口 [−2, +6] mm 本支**不适用**，显式登记原因。
    lows = [min(sole[i]["L"], sole[i]["R"]) for i in range(len(sole))]
    res["min_sole_all_mm"] = round(min(lows) * 1000.0, 1)
    res["end_sole_clearance_mm"] = round(lows[-1] * 1000.0, 1)
    res["all_airborne_ok"] = min(lows) * 1000.0 >= 200.0
    res["ground_contact_ok"] = None
    res["ground_contact_skipped_reason"] = \
        "全段离地（鞋底最低 %.1f mm），-2~+6 mm 窗口不适用" % (min(lows) * 1000.0)
    res["no_foot_slide_skipped_reason"] = "全段离地，支撑脚不存在"

    # 7) IK 是否到位（腿最长 0.822 m，够不到会静默截断）。
    res["ankle_target_error_mm"] = round(target_err * 1000.0, 3)
    res["ik_reach_ok"] = target_err * 1000.0 <= 5.0

    # 8) 原地：骨盆水平行程（清单 §0.4「防自带位移」）。
    hspan = max(math.hypot(p.x - pelvis[0].x, p.y - pelvis[0].y)
                for p in pelvis) * 1000.0
    hnet = math.hypot(pelvis[-1].x - pelvis[0].x,
                      pelvis[-1].y - pelvis[0].y) * 1000.0
    res["pelvis_span_mm"] = round(hspan, 2)
    res["pelvis_net_mm"] = round(hnet, 3)
    res["pelvis_in_place_ok"] = hspan <= 60.0

    # 9) `decel_smooth_ok` **本支不适用**：末段是**加速**，该判据（末 6 帧角度增量
    #    单调收敛）是给"收招不许瞬停"写的，与 `accelerating_ok` 互斥。
    res["decel_smooth_ok"] = None
    res["decel_smooth_skipped_reason"] = \
        "本支末段是匀加速下落（末帧 %.2f mm/帧），'末 6 帧增量单调收敛'不适用" \
        % rates[-1]

    # 10) 力量传导链（脚→腿→髋→腰→肩→手，六段全非零）。
    #     尺子同 A11：空中无地面反力，按"可见"下限（位移 ≥5 mm / 转角 ≥3°）判，
    #     实测值一并登记。**不放宽、只换对**。
    moved, swing, nonzero = {}, {}, {}
    for segment, names in (("foot", ("foot.L", "foot.R")),
                           ("pelvis", ("pelvis",)),
                           ("chest", ("chest",)),
                           ("shoulder", ("shoulder.L", "shoulder.R")),
                           ("hand", ("hand.L.tail", "hand.R.tail"))):
        big = 0.0
        for name in names:
            points = [Vector(s[name]) for s in samples]
            big = max(big, max((p - points[0]).length for p in points) * 1000.0)
        moved[segment] = round(big, 2)
    for segment, names in (("thigh", ("thigh.L", "thigh.R")),
                           ("shin", ("shin.L", "shin.R"))):
        big = 0.0
        for name in names:
            vals = [s["euler"].get(name, (0.0, 0.0, 0.0))[0] for s in samples]
            big = max(big, max(vals) - min(vals))
        swing[segment] = round(big, 2)
    for name in ("spine_01", "spine_02", "chest", "shoulder.L", "shoulder.R"):
        nonzero[name] = round(max(abs(v) for s in samples
                                  for v in s["euler"].get(name, (0.0, 0.0, 0.0))),
                              2)
    res["power_chain_travel_mm"] = moved
    res["power_chain_swing_deg"] = swing
    res["power_chain_nonzero_deg"] = nonzero
    res["power_chain_ok"] = (all(v >= 5.0 for v in moved.values())
                             and all(v >= 3.0 for v in swing.values())
                             and all(v >= 1.0 for v in nonzero.values()))

    # 11) 给 A13 的交接真值。
    off = None
    for side in ("L", "R"):
        ankle_z = samples[-1]["foot." + side][2]
        sole_z = sole[-1][side]
        value = ankle_z - sole_z
        off = value if off is None else min(off, value)
    res["ankle_to_sole_mm"] = round(off * 1000.0, 1)

    def touchdown_estimate():
        for step in range(TOTAL + 1, TOTAL + 60):
            vert = VERT_END_A12["L"]
            z = pelvis_z(step) - vert - off
            if z <= 0.0:
                return step
        return None

    touch = touchdown_estimate()
    res["touchdown_estimate_frame"] = touch
    res["touchdown_estimate_frames_after_end"] = \
        (touch - TOTAL) if touch is not None else None
    res["end_ankle_mm"] = {
        side: [round(v * 1000.0, 1) for v in samples[-1]["foot." + side]]
        for side in ("L", "R")}
    res["end_vert_mm"] = {s: round(verts[-1][s] * 1000.0, 1) for s in ("L", "R")}
    res["end_sole_mm"] = {s: round(sole[-1][s] * 1000.0, 1) for s in ("L", "R")}
    res["a13_start_rate_mm_per_frame"] = round(rates[-1], 3)
    res["foot_tip_sign_convention"] = \
        "world_tip_deg: + = 脚尖朝下（压脚背）; − = 脚尖朝上（勾脚）"
    return res


# =============================================================== 主流程
def main():
    global ANKLE_REST

    arm, meshes = A.open_animation_project()
    A.setup_scene()

    if "Idle_01" not in bpy.data.actions:
        print("JUMPFALL_BOOTSTRAP 动画工程缺 Idle_01，先补跑 A01")
        I1.main()
        arm, meshes = A.open_animation_project()
        A.setup_scene()
    for module, action_name in ((JS, JS.NAME), (JU, JU.NAME)):
        if action_name not in bpy.data.actions:
            print("JUMPFALL_BOOTSTRAP 动画工程缺 %s，先补跑" % action_name)
            module.main()
            arm, meshes = A.open_animation_project()
            A.setup_scene()

    # ANKLE_REST = A10/A11 用的同一把尺子（Idle_01@0 的 foot.head）。
    I1.idle_pose(arm, 0.0)
    ANKLE_REST = {side: Vector(A.bone_world(arm, "foot." + side, "head"))
                  for side in ("L", "R")}
    A.report("JUMPFALL_ANKLE_REST",
             {s: [round(v * 1000.0, 2) for v in ANKLE_REST[s]]
              for s in ANKLE_REST})

    A.report("JUMPFALL_BALLISTIC", {
        "g_per_frame": G_PER_FRAME,
        "takeoff_speed_mm_per_frame": round(JS.TAKEOFF_SPEED * 1000.0, 3),
        "apex_frames_from_takeoff": round(T_APEX, 4),
        "a12_base_frames_from_takeoff": BASE_T,
        "frames_past_apex_at_f0": round(BASE_T - T_APEX, 4),
        "z_start_mm": round(Z_START * 1000.0, 3),
        "z_end_mm": round(Z_END * 1000.0, 3),
        "fall_mm": round((Z_START - Z_END) * 1000.0, 1),
        "end_rate_mm_per_frame_analytic": round(
            (pelvis_z(TOTAL) - pelvis_z(TOTAL - 1)) * 1000.0, 3),
    })

    # 读 A11 成品（f12 = 离散顶点）当 A12 的 f0，并把 carry 接力接到同一个点上。
    JU.build_arm_targets()
    start_pose, start_quats = JU.capture_start(
        arm, bpy.data.actions[JU.NAME], JU.TOTAL)
    start_mats = CR.action_world_matrices(
        arm, bpy.data.actions[JU.NAME], JU.TOTAL)
    # ★ 必须卸掉 action：否则后续 `view_layer.update()` 会在某些帧把 pelvis 的
    #   f-curve 值重新压回 pose bone，IK 的髋高被污染（A11 踩过，见文件头第 1 条）。
    arm.animation_data.action = None

    JS._PREV_EULER.clear()
    for name, value in start_pose.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)
    JS.ARM_QUAT.clear()
    JS.ARM_ROLL.clear()
    JS.ROLL_MAX.clear()
    for name, quat in start_quats.items():
        JS.ARM_QUAT[name] = quat
    JS.MAX_ABS_EULER_Y = 0.0
    # 沿用 A11 验证过的旋钮（A11 实测 Y_SAFE 的拐点就是 28）。
    JS.ROLL_RANGE = 150.0
    JS.Y_SAFE = float(os.environ.get("JF_YSAFE", "28.0"))

    del TARGETS[:]
    del TRACE[:]
    keyframes = [(0, start_pose)]
    for frame in range(1, TOTAL + 1):
        keyframes.append((frame, build_pose(arm, frame, record=True)))
    A.report("JUMPFALL_ARM_ROLL", {
        "max_abs_euler_y_deg": round(JS.MAX_ABS_EULER_Y, 2),
        "max_abs_roll_deg": {k: round(JS.ROLL_MAX.get(k, 0.0), 1)
                             for k in ARM_BONES},
        "roll_range_deg": JS.ROLL_RANGE,
        "y_safe_deg": JS.Y_SAFE,
        "roll_rate_deg_per_frame": JU.ROLL_RATE,
        "hint": "roll = 绕骨轴自转（只改滚转、不改骨轴方向）；Y = 欧拉中间角",
    })

    meta = {
        "anim_id": NAME,
        "loop": False,
        "category": "基础移动",
        "note": ("下落：接 Jump_Up@12（离散顶点）的同一解析弹道，24 帧落 %.0f mm、"
                 "末帧竖速 %.1f mm/帧；双腿由收展开（竖距 L +%.0f / R +%.0f mm）"
                 "寻找落点、脚背略勾；双臂从护体架势外张到体侧；屈膝留给 A13"
                 % ((Z_START - Z_END) * 1000.0,
                    (pelvis_z(TOTAL) - pelvis_z(TOTAL - 1)) * 1000.0,
                    (VERT_END_A12["L"] - VERT_FROM["L"]) * 1000.0,
                    (VERT_END_A12["R"] - VERT_FROM["R"]) * 1000.0)),
        "antic_frame": None,
        "hit_frame": None,
        "cancel_frame": None,
        "hitstop_frames": 0,
        "root_motion_m": [0.0, 0.0],
        "start_pelvis_z_m": round(Z_START, 6),
        "end_pelvis_z_m": round(Z_END, 6),
        "fall_m": round(Z_START - Z_END, 4),
        "start_vertical_speed_mps": round((pelvis_z(1) - pelvis_z(0)) * A.FPS, 4),
        "end_vertical_speed_mps": round(
            (pelvis_z(TOTAL) - pelvis_z(TOTAL - 1)) * A.FPS, 4),
        "link_prev": "A11 Jump_Up@12（弹道离散顶点）",
        "link_next": ("A13 Jump_Land（从末帧的 %.1f mm/帧 继续，接触后屈膝吸收）"
                      % ((pelvis_z(TOTAL) - pelvis_z(TOTAL - 1)) * 1000.0)),
        "ground_contact_skipped": "全段离地",
        "power_chain_scale_note": ("空中无地面反力：thigh/shin 判据取'可见'下限 3°，"
                                   "A13 落地时必须换回 A10 的蹬地尺子"),
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.add_markers(action, {
        "FALL_START": 0, "EARLY_END": 10, "SEEK_END": 20,
        "PRE_LAND": 20, "FALL_END": TOTAL,
    })

    samples = A.sample_animation(arm, action, 0, TOTAL, meshes)
    # foot_probe 置空：通用门禁的"脚位移 ≤3 mm"量的是 toe 骨，本支脚全在空中。
    report = A.run_common_assertions(samples, meta, foot_probe=())
    report["common_ground_min_all_frames_mm"] = report.get("ground_min_mm")
    report["ground_contact_ok"] = None

    sole = JS.sole_series(arm, action, list(range(0, TOTAL + 1)))
    ankles = JS.ankle_series(arm, action, list(range(0, TOTAL + 1)))
    target_err = 0.0
    pair = {(f, s): Vector(t) for f, s, t in TARGETS}
    for index, frame in enumerate(range(0, TOTAL + 1)):
        if frame == 0:
            continue
        for side in ("L", "R"):
            target_err = max(target_err,
                             (Vector(ankles[index][side])
                              - pair[(frame, side)]).length)

    verts = vert_series(arm, action, list(range(0, TOTAL + 1)))
    reach = reach_series(arm, action, list(range(0, TOTAL + 1)))
    report.update(fall_assertions(
        arm, action, samples, start_mats, sole, target_err, verts, reach))
    report["meta"] = meta
    # 显式登记被跳过的门禁（值 None）：既让 failed 干净，又不静默隐藏。
    report["skipped_gates"] = sorted(
        k for k, v in report.items() if v is None and k.endswith("_ok"))
    failed = sorted(k for k, v in report.items()
                    if (k.endswith("_ok") or k == "no_teleport")
                    and v is not True and v is not None)
    report["failed"] = failed
    A.report("JUMPFALL_REPORT", report)

    if not SKIP_RENDER:
        FALL_SIDE = ("side", (4.8, 0.0, 1.30), (0.0, 0.0, 1.30), 3.80,
                     (760, 1200))
        FALL_FRONT = ("front", (0.0, -5.2, 1.30), (0.0, 0.0, 1.30), 3.80,
                      (760, 1200))
        FALL_3Q = ("three_quarter", (3.4, -3.8, 1.45), (0.0, 0.0, 1.20), 3.80,
                   (760, 1200))
        A.render_pose_sheet(arm, action, [0, 4, 8, 12, 16, 20, TOTAL], "jumpfall",
                            views=(FALL_SIDE,))
        A.render_pose_sheet(arm, action, [0, 12, TOTAL], "jumpfall",
                            views=(FALL_FRONT,))
        A.render_pose_sheet(arm, action, [0, TOTAL], "jumpfall", views=(FALL_3Q,))
        # 存盘/导出只在**出图那一遍**做：SKIP_RENDER 是纯门禁迭代。
        A.save_project()
        A.export_glb(arm)
    print("JUMPFALL_DONE failed=%s" % failed)

    # 诊断：逐帧臂骨 euler 步 + 真世界旋转步（区分"表示跳"与"真扭转变"）。
    detail = []
    for index in range(1, len(TRACE)):
        before, after = TRACE[index - 1], TRACE[index]
        row = {"f": after["frame"]}
        for name in ARM_BONES:
            step = max(abs(a - b) for a, b in
                       zip(before["euler"][name], after["euler"][name]))
            ang = math.degrees(before["quat"][name].rotation_difference(
                after["quat"][name]).angle)
            if ang > 180.0:
                ang = 360.0 - ang
            row[name] = "%d/%d Y%.0f r%.0f" % (
                round(step), round(ang), after["euler"][name][1],
                after["roll"].get(name, 0.0))
        detail.append(row)
    A.report("JUMPFALL_TRACE_DETAIL", detail)


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("JUMPFALL_FAILURE " + traceback.format_exc())
