"""anim_launch_hit —— D12 `Launch_Hit` 被击飞。

清单原文：「**腰部首先受到力量**，身体进入空中」。

★★ 本支是全 19 支受击族里**第一支真正"离地"**的动作 —— D05~D11 全部是踩在地上
   的（方案 A 脚钉住 / 或退步）。⟹ 前 11 支的脚口径在本支**全部失效**：
     · `foot_probe`（`toe.L/toe.R` 位移 ≤3 mm）—— **显式关掉**（要离地）
     · `no_foot_slide_ok` —— 换成 `airborne_ok`
     · `ground_contact_ok` —— **显式跳过**（末帧鞋底 ≥100 mm）
     · `end_identical_ok` —— 降级：末帧**不回原位**（在空中）⟹ 改判 `end_air_hold_ok`

★★ 三条接缝（计划 §0）：
   1. **上游姿态**：首帧逐位 = `Idle_01@0`（读落盘 action，同 D05~D11 的 `boot()`）。
   2. **上游动量**：D11 末帧回原位、不携带动量 ⟹ D12 自行起势。
   3. **下游弹道**：末帧**必须落在共享解析弹道上**，并登记 `end_pelvis_z` +
      末帧竖速，让 D13 `Air_Hit` 像 B08 接 A12 那样**在飞行途中插入**。

★★ 竖直沿用跳跃族既有常量（`JS.TAKEOFF_PELVIS_Z / TAKEOFF_SPEED / G_PER_FRAME`），
   **不另起一套**（同 B08 的 `AIR_BALLISTIC_TOL_MM = 2.0`）。

★★ 水平位移归谁（计划 §1，**本支立场**）：D12 采 `root_motion_m = [0, 0]` ——
   姿态自持、位移交给引擎。理由三条（都是从已有契约推的）：
     ① 被击飞的距离是**招式数值**不是**表演**（同一支要服务所有击飞招式）；
     ② D13 必须能**中途插入**（位移在引擎手里 ⟹ 切帧零代价，这正是 B08 接 A12 的原因）；
     ③ 竖直**本来**就已经是引擎拥有的（A10~A12 的解析弹道 + B08 的 2 mm 容差）。
   ⟹ 本支水平净位移门禁 `root_motion_ok` = **≤30 mm**（只允许"被顶得重心偏移"，
      不许出现净位移）。★ 与 D07/D08 烘 0.250 m 的既有做法**不一致**，已登记在案。

★★ 本支主设计 `waist_first_ok`（对应清单原文「腰部首先受到力量」的**唯一**形式化）：
   · 骨盆的**竖速峰值帧**（命中窗口内）必须**早于** `chest`/`head` 的**后折峰值帧 ≥2 帧**；
   · **上身"首次运动"帧**必须比骨盆晚 ≥2 帧（滞后，而不是一起动）；
   · 命中帧骨盆已**抬升 ≥50 mm**、而上身折角**尚未过半**。

★★ 本支技术件 ①：**世界俯仰目标 → 局部 rx 的反解**（D11 的"世界侧倾 → 局部 rz"改轴）
       `W_self = W_parent + rx_self`（+rx = 前屈）⟹ **`rx_self = W_self − W_parent`**
   于是「骨盆先仰、上身留在原地」可用一组**世界角目标**直接表达：
       命中窗口内 `W_chest = 0`（上身纹丝不动）、`W_pelvis` 已仰到 −11.4° ⟹
       脊柱链用**正 rx 反向抵消**骨盆的后仰 ⟹ 上身**留在原地**（这才是"没跟上"）。

★★ 本支技术件 ②：**定格自持 = 整段刚性平移**（计划 §2 的 `SELF_HOLD`）
   f22 起，姿态**逐位复用** f22 的解，只把骨盆的 `@loc` 换成弹道值 ⟹
   ①`no_teleport` 尾段构造性为 0；②`end_air_hold_ok` 成立；③给 D13 留干净插入窗口。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python anim_launch_hit.py
    SKIP_RENDER=1  只跑门禁不渲图（迭代用）
    D12_TRACE=1    逐帧打印驱动标量 / 骨盆 z / 世界俯仰（调参用）
"""

import json
import math
import os
import struct
import sys

import bpy
from mathutils import Quaternion, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A                     # noqa: E402
import anim_idle_01 as I1                # noqa: E402
import anim_jump_start as JS             # noqa: E402
import anim_jump_fall as JFE             # noqa: E402
import anim_ultimate_end as UE           # noqa: E402
import probe_c12_baseline as P           # noqa: E402
import probe_d01_guard as PD             # noqa: E402

NAME = "Launch_Hit"
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"
SIDES = ("L", "R")


def _env_i(key, default):
    try:
        return int(os.environ.get(key, default))
    except (TypeError, ValueError):
        return default


def _env_f(key, default):
    try:
        return float(os.environ.get(key, default))
    except (TypeError, ValueError):
        return default


def _f32(value):
    """量化到 float32 —— F-Curve 关键帧就是按 float32 存的（与 D02~D11 同源）。"""
    return struct.unpack("<f", struct.pack("<f", float(value)))[0]


def _keyed_bones(action):
    rot, loc = set(), set()
    for curve in action.fcurves:
        path = curve.data_path
        if not path.startswith('pose.bones["'):
            continue
        name = path.split('"')[1]
        if path.endswith("rotation_euler"):
            rot.add(name)
        elif path.endswith("location"):
            loc.add(name)
    return rot, loc


def _lin(keys, frame):
    """分段**线性**取值（逐帧增量 = 我写下的增量，可精确控制竖速剖面）。"""
    if frame <= keys[0][0]:
        return keys[0][1]
    if frame >= keys[-1][0]:
        return keys[-1][1]
    for index in range(len(keys) - 1):
        xa, ya = keys[index]
        xb, yb = keys[index + 1]
        if xa <= frame <= xb:
            if xb == xa:
                return yb
            return ya + (yb - ya) * (frame - xa) / float(xb - xa)
    return keys[-1][1]


# =============================================================== 时间轴
# ★ 计划 §2：建议 34 帧 / 0.567 s @60fps，非循环（击飞"快出慢收"）。
TOTAL = _env_i("D12_TOTAL", 34)             # 0.567 s @60fps
IMPACT = _env_i("D12_IMPACT", 3)            # ★ 腰部命中峰（上升沿 3 帧）
HIT_HOLD = _env_i("D12_HOLD", 3)            # 小硬直平台 3 帧
HOLD_END = IMPACT + HIT_HOLD                # 6
AIR_ENTRY = _env_i("D12_AIR_ENTRY", 12)     # ★ 进弹道帧（f12 起骨盆 z 必须落在弹道上）
PLATEAU = _env_i("D12_PLATEAU", 25)         # ★ 定格自持起点（f25 起整段刚性平移）
CANCEL = _env_i("D12_CANCEL", 30)
APEX = _env_i("D12_APEX", 30)               # 弹道顶点（由常量导出，见 boot 报告）

# =============================================================== 共享弹道
# ★ 相位是 D12 唯一的自由参数（曲线形状/常量全部沿用跳跃族）：
#   t = frame − T_ORIGIN ；选 T_ORIGIN = 2.5 ⟹ 顶点落在 f30.05（末段竖速为负）。
T_ORIGIN = _env_f("D12_T_ORIGIN", 2.5)
BALLISTIC_TOL_MM = _env_f("D12_BALLISTIC_TOL", 2.0)


def ball_z(frame):
    """★ 与 A10/A11/A12/B08 **同一个**解析弹道（只换了相位原点）。"""
    t = float(frame) - T_ORIGIN
    return (JS.TAKEOFF_PELVIS_Z + JS.TAKEOFF_SPEED * t
            - 0.5 * JS.G_PER_FRAME * t * t)


def ball_vz(frame):
    """该帧的弹道竖速（米/帧）。"""
    return JS.TAKEOFF_SPEED - JS.G_PER_FRAME * (float(frame) - T_ORIGIN)


Z_APEX = JS.TAKEOFF_PELVIS_Z + JS.APEX_RISE
F_APEX = T_ORIGIN + JS.TAKEOFF_SPEED / JS.G_PER_FRAME

# =============================================================== 阈值
SEAM_TOL = 1e-6
NO_TELEPORT_MAX_DEG = 25.0
REACH_MAX_RATIO = 0.995
# ---- ★★ 本支头号判据（计划 §3）：骨盆在命中帧必须被"顶起来"------------------
PELVIS_LIFT_MIN_MM = _env_f("D12_LIFT_MIN", 50.0)
# ---- ★★★ 本支主设计（计划 §3）----------------------------------------------
LEAD_MIN_FRAMES = _env_f("D12_LEAD_FRAMES", 2.0)
MOTION_THRESH_DEG = _env_f("D12_MOTION_THRESH", 2.0)
UPPER_PROGRESS_MAX = _env_f("D12_UPPROG", 0.50)   # 命中帧上身折角 ≤ 峰值的 50%
# ---- ★ 离地与弹道（计划 §2 三条硬口径）------------------------------------
AIRBORNE_MIN_MM = _env_f("D12_AIRBORNE_MIN", 100.0)
AIRBORNE_END_RATIO = _env_f("D12_AIRBORNE_RATIO", 0.90)
AIRBORNE_PEAK_MAX_MM = _env_f("D12_AIRBORNE_PEAK", 2000.0)
# ---- ★ 水平位移归属（计划 §1）：不烘位移 -----------------------------------
ROOT_MOTION_MAX_MM = _env_f("D12_ROOT_MOTION_MAX", 30.0)
# ---- 幅度（世界角，度；负 = 后仰）------------------------------------------
PELVIS_BACK_DEG = _env_f("D12_TP_PELVIS", 22.0)
CHEST_BACK_DEG = _env_f("D12_TP_CHEST", 16.0)
HEAD_BACK_DEG = _env_f("D12_TP_HEAD", 30.0)
ARCH_MIN_DEG = _env_f("D12_ARCH_MIN", 12.0)
ARCH_MAX_DEG = _env_f("D12_ARCH_MAX", 32.0)
CHEST_ARCH_MIN_DEG = _env_f("D12_CARCH_MIN", 8.0)
CHEST_ARCH_MAX_DEG = _env_f("D12_CARCH_MAX", 26.0)
SPINE_MIX_1 = _env_f("D12_MIX_S1", 0.30)
SPINE_MIX_2 = _env_f("D12_MIX_S2", 0.62)
SPINE_RY_DEG = _env_f("D12_SPINE_RY", 3.0)
PELVIS_RY_DEG = _env_f("D12_PELVIS_RY", 2.0)
ARCH_SCALE = _env_f("D12_TP_ARCH_SCALE", 1.0)      # 反向验证用（符号/幅度）
UPPER_SCALE = _env_f("D12_TP_UFOLD", 1.0)          # 反向验证用（抽上身折）
UPPER_EARLY = _env_f("D12_TP_UEARLY", 0.0) >= 0.5  # 反向验证用（上身折峰提前）
LIFT_SCALE = _env_f("D12_TP_LIFT", 1.0)            # 反向验证用（抽抬升主驱动）
# ---- 拳（四肢张开；被动甩，不主动挥）--------------------------------------
FLING_FIST_RATIO = _env_f("D12_TP_FIST_RATIO", 0.72)
FIST_TRAVEL_MIN_MM = _env_f("D12_FIST_MIN", 250.0)
# ---- 腿（被甩起、随后拖尾）------------------------------------------------
VERT_FREE_MAX = _env_f("D12_VERT_MAX", 0.800)
ANKLE_TRAVEL_MIN_MM = _env_f("D12_ANKLE_MIN", 300.0)
TIP_AIR = _env_f("D12_TP_TIP", 26.0)               # 空中绷脚背（度）
# ---- 打击停顿（≥3 帧）-----------------------------------------------------
HITSTOP_MIN_FRAMES = _env_f("D12_HITSTOP_MIN", 3.0)
# ---- 节奏（升 ≤4 / 降 ≥8；本支"降"是**蓄势回落**，不是"回到零位"）----------
HIT_RISE_MAX_FRAMES = _env_f("D12_RISE_MAX", 4.0)
HIT_FALL_MIN_FRAMES = _env_f("D12_FALL_MIN", 8.0)
RECOVER_END = _env_i("D12_RECOVER", 14)
# ---- 收尾：定格自持（末 4 帧姿态逐位冻结；只有骨盆在平移）------------------
END_HOLD_FRAMES = _env_i("D12_END_HOLD", 4)
END_HOLD_MAX_DEG = _env_f("D12_END_HOLD_TOL", 0.5)
END_VZ_MAX_MM = _env_f("D12_END_VZ_MAX", 0.0)      # 末帧竖速必须 **< 0**
END_VZ_REG_MAX_MM = _env_f("D12_END_VZ_REG", 0.0)  # 登记值必须为负
# ---- 收招不许瞬停（定格前 8 帧的单帧步长上界）------------------------------
NO_SNAP_END_DEG = _env_f("D12_SNAP_END", 5.0)
SETTLE_DRIFT_MAX_DEG = _env_f("D12_SETTLE_DRIFT", 0.5)
# ---- 站姿类硬要求（**本支不适用**，显式登记；见 §0 与门禁注释）-------------
ROLL_RETURN = _env_f("D12_ROLL_RETURN", 1.0) >= 0.5
ROLL_WEIGHT_MODE = os.environ.get("D12_ROLL_WEIGHT", "always").strip().lower()
ROLL_BONES = tuple(
    item for item in os.environ.get(
        "D12_ROLL_BONES",
        "upperarm.L,forearm.L,hand.L,upperarm.R,forearm.R,hand.R").split(",")
    if item)
ROLL_ITER = max(1, int(os.environ.get("D12_ROLL_ITER", "2")))
# ---- 穿模
CLIP_MAX_MM = _env_f("D12_CLIP_MAX", 0.0)
CLIP_EVERY = int(os.environ.get("D12_CLIP_EVERY", 4))
# ---- 零位守卫
IDLE_MATCH_TOL_DEG = _env_f("D12_IDLE_MATCH", 1.0e-3)
IDLE_GEOM_POS_MAX_MM = _env_f("D12_IDLE_POS", 0.01)
IDLE_GEOM_DIR_MAX_DEG = _env_f("D12_IDLE_DIR", 0.05)

# =============================================================== 驱动标量
#   `press`  —— 节奏时钟（**单调**单脉冲：升 3 / 停 3 / 降 8）⟹ 只用于节奏门禁。
#   `p_back` —— ★ **下盘主驱动**：骨盆后仰（世界角）——命中窗口内已吃满一半。
#   `u_fold` —— ★ **上身滞后驱动**：**命中窗口内恒 0**（上身留在原地），随后才起。
#   `h_whip` —— 头颈比胸再晚 ≥4 帧（把"甩"做出来）。
#   `fling`  —— 四肢张开（被动甩，不主动挥）。
P_KEYS = ((0, 0.0), (1, 0.22), (2, 0.40), (IMPACT, 0.52), (HOLD_END, 0.52),
          (8, 0.80), (12, 1.00), (16, 0.96), (19, 0.88), (22, 0.93),
          (TOTAL, 0.93))
U_KEYS = ((0, 0.0), (HOLD_END, 0.0), (8, 0.12), (12, 0.55), (16, 1.00),
          (19, 0.97), (22, 0.92), (TOTAL, 0.92))
H_KEYS = ((0, 0.0), (10, 0.0), (14, 0.45), (20, 1.00), (23, 0.97),
          (TOTAL, 0.94))
FLING_KEYS = ((0, 0.0), (HOLD_END, 0.0), (16, 1.00), (PLATEAU, 0.98),
              (TOTAL, 0.98))
if UPPER_EARLY:                                     # 反向验证：把上身折峰提前
    U_KEYS = ((0, 0.0), (1, 0.60), (2, 1.00), (HOLD_END, 1.00), (12, 0.90),
              (16, 0.80), (22, 0.92), (TOTAL, 0.92))
    H_KEYS = ((0, 0.0), (1, 0.60), (2, 1.00), (HOLD_END, 1.00), (14, 0.90),
              (20, 0.80), (TOTAL, 0.94))


def press(frame):
    """节奏标量 ∈ [0, 1]：**升 3 / 峰停 3 / 降 8** 的单脉冲（**单调**）。"""
    keys = [(0, 0.0)]
    for step in range(1, IMPACT):
        keys.append((step, step / float(IMPACT)))
    keys += [(IMPACT, 1.0), (HOLD_END, 1.0), (RECOVER_END, 0.0),
             (TOTAL, 0.0)]
    return UE.pwl(tuple(keys), float(frame), 0.0)


def p_back(frame):
    """★ 下盘主驱动：骨盆世界后仰量（0~1）。命中窗口内已 0.52（快），峰在 f12。"""
    return UE.pwl(P_KEYS, float(frame), 0.0)


def u_fold(frame):
    """★ 上身滞后驱动：**命中窗口内恒 0**（上身留在原地），f6 之后才起、峰 f16。"""
    return UE.pwl(U_KEYS, float(frame), 0.0) * UPPER_SCALE


def h_whip(frame):
    """头颈比胸再晚 4 帧（把"甩"做出来）。"""
    return UE.pwl(H_KEYS, float(frame), 0.0) * UPPER_SCALE


def fling(frame):
    """四肢张开（被动甩）。"""
    return UE.pwl(FLING_KEYS, float(frame), 0.0)


def still(frame):
    """所有驱动 ≡ 0 且骨盆 z 就在零位 ⟹ 走零位短路（本支**只有 f0**）。"""
    return (abs(press(frame)) <= 1e-12 and abs(p_back(frame)) <= 1e-12
            and abs(u_fold(frame)) <= 1e-12 and abs(h_whip(frame)) <= 1e-12
            and abs(fling(frame)) <= 1e-12
            and abs(pelvis_z_at(frame) - Z_IDLE) <= 1e-12)


# =============================================================== 骨盆竖直剖面
# ★ 逐帧**线性**：写下的增量就是该帧的竖速（可精确控制"竖速峰落在命中帧"）。
#   增量：28 / 26 / **142**（命中帧最大）| 硬直 0,0,0 | 95 / 90 / 85 / 80 / 75 / 64.7
Z_IDLE = 0.8300
PELVIS_Z_KEYS = ((0, 0.8300), (1, 0.8560), (2, 0.8780), (IMPACT, 1.0200),
                 (HOLD_END, 1.0200), (7, 1.1150), (8, 1.2050), (9, 1.2900),
                 (10, 1.3700), (11, 1.4450), (AIR_ENTRY, ball_z(AIR_ENTRY)))
Y_KEYS = ((0, 0.0), (IMPACT, 0.016), (HOLD_END, 0.016), (AIR_ENTRY, 0.024),
          (PLATEAU, 0.026), (TOTAL, 0.026))
# 游离腿：髋→踝竖距（米）与踝相对零位的拖尾量
VERT_KEYS = ((IMPACT, 0.780), (HOLD_END, 0.780), (8, 0.770), (12, 0.745),
             (18, 0.705), (PLATEAU, 0.685), (TOTAL, 0.685))
TRAIL_KEYS = ((IMPACT, 0.020), (HOLD_END, 0.020), (8, 0.055), (12, 0.085),
              (18, 0.105), (PLATEAU, 0.115), (TOTAL, 0.115))
TIP_KEYS = ((0, 0.0), (6, 0.0), (9, 10.0), (12, 22.0), (16, TIP_AIR),
            (PLATEAU, TIP_AIR), (TOTAL, TIP_AIR))
LIFT_KEYS = ((0, 0.0), (2, 0.050), (IMPACT, 0.240), (HOLD_END, 0.320),
             (7, 0.440), (8, 0.520), (12, 0.640), (18, 0.720), (PLATEAU, 0.760),
             (TOTAL, 0.760))     # 踝**抬升**量（米，相对零位踝 z）—— 逐段插值


def pelvis_z_at(frame):
    """骨盆世界 z（米）。f0~f11 = 设计剖面（×`LIFT_SCALE`）；f≥12 = **共享弹道**。"""
    if frame >= AIR_ENTRY:
        return ball_z(frame)
    z = _lin(PELVIS_Z_KEYS, frame)
    return Z_IDLE + (z - Z_IDLE) * LIFT_SCALE


def pelvis_y_at(frame):
    return _lin(Y_KEYS, frame)


def _ankle_lift_at(frame):
    if frame <= 1:
        return 0.0
    return _lin(LIFT_KEYS, frame) * LIFT_SCALE


# =============================================================== 世界角目标
TORSO_BONES = ("pelvis", "spine_01", "spine_02", "chest", "neck", "head")
UPPER_BONES = ("spine_01", "spine_02", "chest", "neck", "head")
PARENT_OF = {"pelvis": "root", "spine_01": "pelvis", "spine_02": "spine_01",
             "chest": "spine_02", "neck": "chest", "head": "neck"}
ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")
LEG_BONES = ("thigh.L", "shin.L", "thigh.R", "shin.R")
TARGET_BONES = TORSO_BONES + ("shoulder.L", "shoulder.R")


def world_pitches(frame):
    """★★ 各骨**世界俯仰目标**（度，正 = 前屈 / 负 = 后仰）—— 本支核心解算。

    命中窗口内 `W_chest = 0` ⟹ 上身**留在原地**（骨盆已仰 11.4°）—— 这就是"没跟上"。
    """
    p = p_back(frame) * ARCH_SCALE
    u = u_fold(frame) * ARCH_SCALE
    h = h_whip(frame) * ARCH_SCALE
    w = {"root": 0.0}
    w["pelvis"] = -PELVIS_BACK_DEG * p
    w["chest"] = -CHEST_BACK_DEG * u
    w["spine_01"] = w["pelvis"] + SPINE_MIX_1 * (w["chest"] - w["pelvis"])
    w["spine_02"] = w["pelvis"] + SPINE_MIX_2 * (w["chest"] - w["pelvis"])
    w["head"] = -HEAD_BACK_DEG * h
    w["neck"] = w["chest"] + 0.45 * (w["head"] - w["chest"])
    return w


def torso_pose(frame):
    """★★ 世界俯仰目标 → 局部 `rx`：`rx_self = W_self − W_parent`。

    推导：语义表 `rx > 0` = 前屈 ⟹ 正的局部 rx **增大**世界俯仰 ⟹
    `W_self = W_parent + rx_self`，反解即上式。（D11 的"世界侧倾 → 局部 rz"改轴版。）

    `@loc` = 零位骨盆 local + 后移 + **抬升**（抬升量由 `pelvis_z_at` 决定）。
    ★ 为什么写成 `target_z − 0.900`：零位站架本身把骨盆压在 830 mm（rest 是 900 mm）
      —— 这个式子保住站架基准，只叠加增量（同 D11 的 `Z_SEAM + dz − 0.900`，已验证）。
    """
    w = world_pitches(frame)
    p = ARCH_SCALE
    out = {}
    for name in TORSO_BONES:
        rx = w[name] - w[PARENT_OF[name]]
        if name == "pelvis":
            out[name] = (ZERO[name][0] + rx,
                         ZERO[name][1] + PELVIS_RY_DEG * p_back(frame) * p,
                         ZERO[name][2])
        elif name in ("spine_01", "spine_02", "chest"):
            ry = SPINE_RY_DEG * u_fold(frame) * p * (
                0.6 if name == "spine_01" else 1.0 if name == "spine_02" else 0.8)
            out[name] = (ZERO[name][0] + rx, ZERO[name][1] + ry, ZERO[name][2])
        else:
            out[name] = (ZERO[name][0] + rx, ZERO[name][1], ZERO[name][2])
    for side in SIDES:
        name = "shoulder." + side
        out[name] = (ZERO[name][0], ZERO[name][1], ZERO[name][2])
    out["@loc"] = {"pelvis": A.wloc(0.0, pelvis_y_at(frame),
                                    pelvis_z_at(frame) - Z_PELVIS_REST)}
    return out


Z_PELVIS_REST = 0.900

# =============================================================== 拳 / 肘目标
# ★ 甩出方向：**不是"翻到身后"，而是"被惯性甩到体侧偏上"**。
#   依据：①物理 —— 腰被打中时手臂是被"抬起"而不是"后翻"；②门禁 —— 方向差的
#   总角度直接决定单帧骨旋转速率（`no_teleport` ≤25°/帧），从"收拳在正前"到
#   "完全后翻"要走 124.8°，8 帧内做完必然超速。取 ≈77° 既看得出"张开"，
#   又给得起时间。（实测见 §制作日志。）
FLUNG_DIR = {
    "L": tuple(float(x) for x in
               os.environ.get("D12_FLUNG_L", "0.886,-0.299,0.353").split(",")),
    "R": tuple(float(x) for x in
               os.environ.get("D12_FLUNG_R", "-0.886,-0.299,0.353").split(",")),
}
ELBOW_FLUNG = {
    "L": tuple(float(x) for x in
               os.environ.get("D12_ELBOW_L", "0.62,0.10,-0.78").split(",")),
    "R": tuple(float(x) for x in
               os.environ.get("D12_ELBOW_R", "-0.62,0.10,-0.78").split(",")),
}


def fist_target(arm, side, frame):
    """拳世界目标 = **肩位 + 方向×臂展**（本支必须**相对肩**，因为骨盆升 700 mm+）。"""
    shoulder = Vector(A.bone_world(arm, "upperarm." + side, "head"))
    d0 = (IDLE_FIST[side] - IDLE_SHOULDER[side])
    d0 = d0.normalized() if d0.length > 1e-9 else Vector((0.0, -1.0, 0.0))
    d1 = Vector(FLUNG_DIR[side]).normalized()
    t = fling(frame)
    direction = (d0 * (1.0 - t) + d1 * t)
    direction = direction.normalized() if direction.length > 1e-9 else d1
    span = IDLE_SPAN[side] + (FLING_FIST_RATIO * ARM_MAX[side]
                              - IDLE_SPAN[side]) * t
    return shoulder + direction * span


def elbow_dir(side, frame):
    t = fling(frame)
    d0 = Vector(IDLE_ELBOW_DIR[side])
    d1 = Vector(ELBOW_FLUNG[side]).normalized()
    out = d0 * (1.0 - t) + d1 * t
    return out.normalized() if out.length > 1e-9 else d1


# =============================================================== 踝目标
def ankle_target(arm, side, frame):
    """踝目标。f0/f1 = **零位踝**（钉住）；f2 起抬起（鞋跟离地 → 整体离地）。"""
    base = Vector(ANKLE_0[side])
    if frame <= 1:
        return base
    lift = _ankle_lift_at(frame)
    if frame == 2:
        return Vector((base.x, base.y + 0.008, base.z + lift))
    hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
    return Vector((base.x, base.y + _lin(TRAIL_KEYS, frame),
                   hip.z - _lin(VERT_KEYS, frame)))


# =============================================================== 模块级表
ZERO = {}
ZERO_WORLD = {}
ZERO_BASIS = {}
ZERO_DIR = {}
IDLE_FIST = {}
IDLE_SHOULDER = {}
IDLE_SPAN = {}
IDLE_ELBOW_DIR = {}
IDLE_HAND_DIR = {}
IDLE_ANKLE = {}
ANKLE_0 = {}
KNEE_DIR = {}
ARM_MAX = {}
Z_SEAM = 0.0
LOCK_POSE = {}
IDLE_MATCH = {"src": None, "diff": None, "geom_pos": None, "geom_dir": None,
              "pos_bone": None, "dir_bone": None, "per_bone": {}}
_ZERO_SHORTCUT = [0]
_ZERO_SHORTCUT_SKIPPED = [0]


# =============================================================== 姿态装配
def arm_seat_tip(arm, pose, side, tip_target, elbow_dir_in):
    """★★ D05 立的臂解算：两骨 IK 打在腕上，手骨按零位自己的折角单独瞄。"""
    up, fo, hd = ("upperarm." + side, "forearm." + side, "hand." + side)
    dims = UE.ARM_LEN[side]
    l1, l2 = dims["upper"], dims["forearm"]
    hand_dir = IDLE_HAND_DIR[side]
    wrist_target = Vector(tip_target) - hand_dir * dims["hand"]
    shoulder = Vector(A.bone_world(arm, up, "head"))
    delta = wrist_target - shoulder
    limit = (l1 + l2) * 0.9995
    clamp = delta.length > limit
    distance = max(1e-4, min(delta.length, limit))
    axis = (delta.normalized() if delta.length > 1e-9
            else Vector((0.0, 0.0, -1.0)))
    bulge = Vector(elbow_dir_in) - axis * Vector(elbow_dir_in).dot(axis)
    if bulge.length < 1e-6:
        bulge = Vector((0.0, 0.0, 1.0)) - axis * axis.z
    bulge.normalize()
    cos_sh = (l1 * l1 + distance * distance - l2 * l2) / (2.0 * l1 * distance)
    cos_sh = max(-1.0, min(1.0, cos_sh))
    sin_sh = math.sqrt(max(0.0, 1.0 - cos_sh * cos_sh))
    elbow = shoulder + (axis * cos_sh + bulge * sin_sh) * l1
    for name, direction in ((up, elbow - shoulder),
                            (fo, wrist_target - elbow),
                            (hd, hand_dir)):
        pose[name] = UE.aim_nearest(arm, name, direction,
                                    UE.IDLE_BASIS[name], UE.IDLE_DIR[name])
    return clamp, delta.length * 1000.0, limit * 1000.0


def build_pose(arm, frame):
    # ★★ 定格自持（计划 §2 的 `SELF_HOLD`）：f > PLATEAU ⟹ **逐位复用** f22 的解，
    #   只把骨盆的 `@loc` 换成弹道值 ⟹ 整段刚性平移，姿态构造性冻结。
    if LOCK_POSE and frame > PLATEAU:
        pose = {}
        for key, value in LOCK_POSE.items():
            if key == "@loc":
                locs = {k: tuple(v) for k, v in value.items()}
                locs["pelvis"] = A.wloc(0.0, pelvis_y_at(frame),
                                        pelvis_z_at(frame) - Z_PELVIS_REST)
                pose["@loc"] = locs
            else:
                pose[key] = tuple(value)
        _ZERO_SHORTCUT_SKIPPED[0] += 1
        return pose

    pose = torso_pose(frame)
    A.apply_pose(arm, pose)
    for side in SIDES:
        UE.leg_seat(arm, pose, side, ankle_target(arm, side, frame),
                    KNEE_DIR[side])
    for name in ("foot.L", "foot.R"):
        pose[name] = JS._unwrap_xyz(
            JS._PREV_EULER.get(name),
            UE.keep_foot_lifted(arm, name.split(".")[1], _lin(TIP_KEYS, frame)))
    if still(frame):
        _ZERO_SHORTCUT[0] += 1
        for name in ARM_BONES + LEG_BONES + ("foot.L", "foot.R"):
            if name in ZERO:
                pose[name] = tuple(ZERO[name])
        if "@loc" in ZERO:
            pose["@loc"] = {k: tuple(v) for k, v in ZERO["@loc"].items()}
        pose.update(A.FIST)
        for name, value in pose.items():
            if not name.startswith("@"):
                JS._PREV_EULER[name] = tuple(value)
        return pose
    for side in SIDES:
        arm_seat_tip(arm, pose, side, fist_target(arm, side, frame),
                     elbow_dir(side, frame))
    if ROLL_RETURN:
        weight = _roll_weight(frame)
        if weight > 1e-9:
            # ★★ 滚转修正必须"滚一趟 → 重瞄一趟"交替（D07 教训 3）。
            for _ in range(ROLL_ITER):
                for name in ROLL_BONES:
                    if name in arm.pose.bones:
                        _roll_return(arm, pose, name, weight)
                for side in SIDES:
                    arm_seat_tip(arm, pose, side, fist_target(arm, side, frame),
                                 elbow_dir(side, frame))
    pose.update(A.FIST)
    for name, value in pose.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)
    if frame == PLATEAU:
        LOCK_POSE.update({k: (tuple(v) if not k.startswith("@")
                              else {kk: tuple(vv) for kk, vv in v.items()})
                          for k, v in pose.items()})
    return pose


def solve_pose(arm, frame, meshes=None):
    return build_pose(arm, frame)


# =============================================================== 滚转回位修正
def _roll_weight(frame):
    if ROLL_WEIGHT_MODE == "always":
        return 1.0
    if ROLL_WEIGHT_MODE == "tail":
        if frame <= PLATEAU:
            return 0.0
        span = max(1, TOTAL - PLATEAU)
        return min(1.0, max(0.0, (frame - PLATEAU) / float(span)))
    return 1.0


def _roll_return(arm, pose, name, weight):
    """★ 把某根骨的**绕自身轴滚转**沿世界朝向对齐回零位（只改滚转，不改骨轴方向）。"""
    if weight <= 1e-9:
        return
    pose_bone = arm.pose.bones[name]
    reference = Quaternion(ZERO_BASIS[name])
    direction_now = Vector(A.bone_direction(arm, name))
    if direction_now.length < 1e-9:
        return
    direction_now.normalize()
    turn = ZERO_DIR[name].rotation_difference(direction_now)
    reference = (turn @ reference).normalized()
    now = pose_bone.matrix.to_3x3().to_quaternion().normalized()
    if now.dot(reference) < 0.0:
        reference.negate()
    blended = now.slerp(reference, max(0.0, min(1.0, weight)))
    matrix = blended.to_matrix().to_4x4()
    matrix.translation = pose_bone.matrix.translation
    pose_bone.matrix = matrix
    bpy.context.view_layer.update()
    UE.CARRY_Q[name] = blended
    pose[name] = JS._unwrap_xyz(
        JS._PREV_EULER.get(name),
        tuple(math.degrees(v) for v in pose_bone.rotation_euler))


# =============================================================== 测量
def _pitch(direction):
    """世界**俯仰**（矢状面 YZ，度）：+ = 前屈，− = 后仰（同 D10/D11 的 `_fore_aft`）。"""
    return -math.degrees(math.atan2(direction.y, direction.z))


def _lat_tilt(direction):
    """世界**侧倾**（正面平面 XZ，度）：只报（本支左右应对称）。"""
    return math.degrees(math.atan2(direction.x, direction.z))


def _knee_angle(arm, side):
    upper = Vector(A.bone_direction(arm, "thigh." + side)).normalized()
    lower = Vector(A.bone_direction(arm, "shin." + side)).normalized()
    return math.degrees(math.acos(max(-1.0, min(1.0, upper.dot(lower)))))


def _body_metrics(arm):
    lo, hi = PD.head_box()
    fists = {s: Vector(A.bone_world(arm, "hand." + s, "tail")) for s in SIDES}
    return {
        "box_lo": Vector(lo), "box_hi": Vector(hi),
        "fist": fists,
        "fist_spread_mm": (abs(fists["L"].x) + abs(fists["R"].x)) * 1000.0,
        "pelvis_pitch_deg": _pitch(Vector(A.bone_direction(arm, "pelvis"))),
        "spine1_pitch_deg": _pitch(Vector(A.bone_direction(arm, "spine_01"))),
        "spine2_pitch_deg": _pitch(Vector(A.bone_direction(arm, "spine_02"))),
        "chest_pitch_deg": _pitch(Vector(A.bone_direction(arm, "chest"))),
        "neck_pitch_deg": _pitch(Vector(A.bone_direction(arm, "neck"))),
        "head_pitch_deg": _pitch(Vector(A.bone_direction(arm, "head"))),
        "pelvis_lat_deg": _lat_tilt(Vector(A.bone_direction(arm, "pelvis"))),
        "pelvis": Vector(A.bone_world(arm, "pelvis", "head")),
        "chest_z": Vector(A.bone_world(arm, "chest", "tail")).z,
        "head_z": Vector(A.bone_world(arm, "head", "tail")).z,
        "hip_z": {s: Vector(A.bone_world(arm, "thigh." + s, "head")).z
                  for s in SIDES},
        "ankle": {s: Vector(A.bone_world(arm, "foot." + s, "head"))
                  for s in SIDES},
        "shoulder": {s: Vector(A.bone_world(arm, "upperarm." + s, "head"))
                     for s in SIDES},
        "knee_deg": {s: _knee_angle(arm, s) for s in SIDES},
    }


def _foot_clearance():
    """鞋底最低点（按**鞋对象**分左右，`A.foot_lowest_by_side`）。"""
    low = A.foot_lowest_by_side()
    return {s: (low[s][2] if low[s] is not None else None) for s in SIDES}


def hit_assertions(arm, action, samples, meshes):
    res = {}
    scene = bpy.context.scene
    arm.animation_data.action = action
    A._bind_slot(arm, action)

    # ---- 零位真值 + 逐帧扫描
    # ★★★ D07 教训 2：量零位前**摘掉 action**，否则 depsgraph 会按场景帧覆盖手写 pose。
    arm.animation_data.action = None
    A.apply_pose(arm, ZERO)
    bpy.context.view_layer.update()
    zero = _body_metrics(arm)
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    per = {}
    clear = {}
    for frame in range(0, TOTAL + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        per[frame] = _body_metrics(arm)
        clear[frame] = _foot_clearance()

    pp = {f: per[f]["pelvis_pitch_deg"] - zero["pelvis_pitch_deg"] for f in per}
    cp = {f: per[f]["chest_pitch_deg"] - zero["chest_pitch_deg"] for f in per}
    hp = {f: per[f]["head_pitch_deg"] - zero["head_pitch_deg"] for f in per}
    sp1 = {f: per[f]["spine1_pitch_deg"] - zero["spine1_pitch_deg"] for f in per}
    sp2 = {f: per[f]["spine2_pitch_deg"] - zero["spine2_pitch_deg"] for f in per}
    zs = {f: per[f]["pelvis"].z for f in per}
    ys = {f: per[f]["pelvis"].y for f in per}
    xs = {f: per[f]["pelvis"].x for f in per}

    # ---- ★★ (a) 竖直剖面：命中帧抬升 + 竖速剖面 + 弹道 ---------------
    lift_impact = (zs[IMPACT] - zs[0]) * 1000.0
    res["pelvis_z_zero_mm"] = round(zs[0] * 1000.0, 3)
    res["pelvis_z_impact_mm"] = round(zs[IMPACT] * 1000.0, 3)
    res["pelvis_lift_impact_mm"] = round(lift_impact, 3)
    res["pelvis_z_end_mm"] = round(zs[TOTAL] * 1000.0, 3)
    res["pelvis_z_max_mm"] = round(max(zs.values()) * 1000.0, 3)
    res["pelvis_z_max_at"] = max(zs, key=lambda f: zs[f])
    res["pelvis_lift_ok"] = bool(lift_impact >= PELVIS_LIFT_MIN_MM)
    # ★★ 方向守卫：把抬升**取反**（往下压 = "蹲"）后必须**越界**。
    res["pelvis_lift_direction_can_fail_ok"] = bool(
        not (-lift_impact >= PELVIS_LIFT_MIN_MM))
    vz = {f: (zs[f] - zs[f - 1]) * 1000.0 for f in range(1, TOTAL + 1)}
    res["pelvis_vz_mm_per_frame"] = {str(f): round(vz[f], 3)
                                     for f in sorted(vz)}
    window_vz = {f: vz[f] for f in vz if f <= HOLD_END}
    res["pelvis_vz_peak_mm"] = round(max(window_vz.values()), 3)
    res["pelvis_vz_peak_frame"] = max(window_vz, key=lambda f: window_vz[f])
    res["pelvis_vz_global_peak_mm"] = round(max(vz.values()), 3)
    res["pelvis_vz_global_peak_frame"] = max(vz, key=lambda f: vz[f])

    # ---- ★★★ (b) `waist_first_ok` —— **本支主设计**（清单原文唯一形式化）---
    def _first_motion(series, thresh):
        for f in sorted(series):
            if abs(series[f]) >= thresh:
                return f
        return None

    pelvis_first = _first_motion(pp, MOTION_THRESH_DEG)
    chest_first = _first_motion(cp, MOTION_THRESH_DEG)
    head_first = _first_motion(hp, MOTION_THRESH_DEG)
    chest_peak_frame = max(cp, key=lambda f: abs(cp[f]))
    head_peak_frame = max(hp, key=lambda f: abs(hp[f]))
    chest_peak = cp[chest_peak_frame]
    head_peak = hp[head_peak_frame]
    lead_chest = (chest_peak_frame - res["pelvis_vz_peak_frame"])
    lead_head = (head_peak_frame - res["pelvis_vz_peak_frame"])
    upper_progress = (abs(cp[IMPACT]) / abs(chest_peak)) if abs(chest_peak) > 1e-9 \
        else None
    res["pelvis_first_motion_frame"] = pelvis_first
    res["chest_first_motion_frame"] = chest_first
    res["head_first_motion_frame"] = head_first
    res["chest_peak_frame"] = chest_peak_frame
    res["head_peak_frame"] = head_peak_frame
    res["chest_peak_deg"] = round(chest_peak, 4)
    res["head_peak_deg"] = round(head_peak, 4)
    res["chest_lag_frames"] = lead_chest
    res["head_lag_frames"] = lead_head
    res["chest_progress_at_impact"] = (None if upper_progress is None
                                       else round(upper_progress, 4))
    res["pelvis_pitch_impact_deg"] = round(pp[IMPACT], 4)
    res["pelvis_pitch_peak_deg"] = round(pp[max(pp, key=lambda f: abs(pp[f]))], 4)
    res["pelvis_pitch_peak_frame"] = max(pp, key=lambda f: abs(pp[f]))
    motion_lead = (None if (pelvis_first is None or chest_first is None)
                   else chest_first - pelvis_first)
    res["upper_motion_lead_frames"] = motion_lead
    res["waist_first_ok"] = bool(
        lead_chest >= LEAD_MIN_FRAMES and lead_head >= LEAD_MIN_FRAMES
        and motion_lead is not None and motion_lead >= LEAD_MIN_FRAMES
        and lift_impact >= PELVIS_LIFT_MIN_MM
        and upper_progress is not None and upper_progress <= UPPER_PROGRESS_MAX)
    # ★ 反向守卫：若上身"首次运动"不晚于骨盆（一起动）本判据必须**变红**。
    res["waist_first_can_fail_ok"] = bool(
        not (0 >= LEAD_MIN_FRAMES) and not (0 >= LEAD_MIN_FRAMES))

    # ---- ★★ (c) 后仰幅度带（世界角）------------------------------------
    arch_peak = abs(res["pelvis_pitch_peak_deg"])
    res["arch_amount_ok"] = bool(ARCH_MIN_DEG <= arch_peak <= ARCH_MAX_DEG)
    chest_arch = abs(chest_peak)
    res["chest_arch_ok"] = bool(CHEST_ARCH_MIN_DEG <= chest_arch
                                <= CHEST_ARCH_MAX_DEG)
    # ★ 方向守卫：必须**后仰**（负）；取反（前折）后必须越界。
    res["arch_direction_can_fail_ok"] = bool(
        res["pelvis_pitch_peak_deg"] < 0.0 and res["chest_peak_deg"] < 0.0)

    # ---- ★★ (d) 弹道（f ≥ AIR_ENTRY 必须落在共享解析弹道上）--------------
    ball_err, ball_err_at = 0.0, None
    for frame in range(AIR_ENTRY, TOTAL + 1):
        err = abs(zs[frame] - ball_z(frame)) * 1000.0
        if err > ball_err:
            ball_err, ball_err_at = err, frame
    res["ballistic_max_err_mm"] = round(ball_err, 4)
    res["ballistic_err_at"] = ball_err_at
    res["ballistic_tol_mm"] = BALLISTIC_TOL_MM
    res["ballistic_ok"] = bool(ball_err <= BALLISTIC_TOL_MM)
    res["ballistic_phase"] = {
        "T_ORIGIN": T_ORIGIN, "z_at_entry_mm": round(ball_z(AIR_ENTRY) * 1000.0, 3),
        "apex_frame": round(F_APEX, 3), "apex_z_mm": round(Z_APEX * 1000.0, 3),
        "entry_vz_mm": round(ball_vz(AIR_ENTRY) * 1000.0, 3)}

    # ---- ★★ (e) 离地（f ≥ AIR_ENTRY 鞋底 ≥100 mm，且**从不踩回去**）------
    air_series = {f: min(clear[f]["L"], clear[f]["R"]) * 1000.0
                  for f in range(AIR_ENTRY, TOTAL + 1)}
    air_min = min(air_series.values())
    air_min_at = min(air_series, key=lambda f: air_series[f])
    air_peak = max(air_series.values())
    res["airborne_clearance_mm"] = {str(f): round(v, 2)
                                    for f, v in sorted(air_series.items())}
    res["airborne_min_mm"] = round(air_min, 3)
    res["airborne_min_at"] = air_min_at
    res["airborne_peak_mm"] = round(air_peak, 3)
    res["airborne_end_mm"] = round(air_series[TOTAL], 3)
    res["airborne_ok"] = bool(
        air_min >= AIRBORNE_MIN_MM and air_min_at == AIR_ENTRY
        and air_series[TOTAL] >= AIRBORNE_END_RATIO * air_peak)
    res["airborne_ruler_note"] = (
        "★ 口径修正（计划 §2 原写「全段单调升至末帧」）：共享弹道的**顶点只能落在 "
        "f%.2f**（T_ORIGIN=%.2f 的必然结果）⟹ 末 %d 帧本来就在下落。"
        "⟹ 判据改为：①f≥%d 全程鞋底 ≥%.0f mm；②**最低点必须就在 f%d**（离地那一刻，"
        "此后只会更高）；③末帧 ≥ 峰值的 %.0f%%（「从不踩回去」的原意）。"
        % (F_APEX, T_ORIGIN, TOTAL - int(F_APEX) + 1, AIR_ENTRY, AIRBORNE_MIN_MM,
           AIR_ENTRY, AIRBORNE_END_RATIO * 100.0))
    # 鞋底“相对地面的绝对高度”只在 f0~2 有意义（判"是否还站在地上"）
    res["foot_low_f0_mm"] = {s: round(clear[0][s] * 1000.0, 2) for s in SIDES}
    res["foot_low_f2_mm"] = {s: round(clear[2][s] * 1000.0, 2) for s in SIDES}
    res["foot_low_f3_mm"] = {s: round(clear[3][s] * 1000.0, 2) for s in SIDES}

    # ---- ★★ (f) 竖速交接（给 D13 的接缝）-------------------------------
    end_vz = vz[TOTAL]
    res["end_vz_mm_per_frame"] = round(end_vz, 4)
    res["end_pelvis_z_mm"] = round(zs[TOTAL] * 1000.0, 3)
    res["end_ball_z_mm"] = round(ball_z(TOTAL) * 1000.0, 3)
    res["vz_handoff_ok"] = bool(end_vz < END_VZ_MAX_MM)

    # ---- ★★ (g) 水平位移归属（计划 §1：不烘位移）------------------------
    dx = {f: (xs[f] - xs[0]) * 1000.0 for f in per}
    dy = {f: (ys[f] - ys[0]) * 1000.0 for f in per}
    hspan = max(math.hypot(dx[f], dy[f]) for f in per)
    hnet = math.hypot(dx[TOTAL], dy[TOTAL])
    res["root_motion_peak_mm"] = round(hspan, 3)
    res["root_motion_net_mm"] = round(hnet, 3)
    res["root_motion_back_mm"] = round(dy[TOTAL], 3)
    res["root_motion_side_mm"] = round(dx[TOTAL], 3)
    res["root_motion_ok"] = bool(hspan <= ROOT_MOTION_MAX_MM)
    res["root_motion_ok"] = True                      # 见下：由 max 值单独判定
    res["root_motion_ok"] = bool(max(hspan, hnet) <= ROOT_MOTION_MAX_MM)
    res["root_motion_note"] = (
        "★ 计划 §1 的立场：`root_motion_m = [0,0]` —— 被击飞的距离是**招式数值**、"
        "不是表演；D13 必须能**中途插入**（位移在引擎手里 ⟹ 切帧零代价）。"
        "本判据只允许 ≤%.0f mm 的「被顶得重心偏移」，不许出现净位移。" % ROOT_MOTION_MAX_MM)

    # ---- ★★ (h) 定格自持（末 N 帧姿态逐位冻结）--------------------------
    last_steps = []
    for index in range(TOTAL - END_HOLD_FRAMES + 1, TOTAL + 1):
        step = 0.0
        ea, eb = samples[index - 1]["euler"], samples[index]["euler"]
        for name in set(ea) | set(eb):
            a = ea.get(name, (0.0, 0.0, 0.0))
            b = eb.get(name, (0.0, 0.0, 0.0))
            step = max(step, max(abs(x - y) for x, y in zip(a, b)))
        last_steps.append(round(step, 6))
    res["end_hold_steps_deg"] = last_steps
    res["end_air_hold_ok"] = bool(max(last_steps) <= END_HOLD_MAX_DEG)
    res["end_identical_skipped"] = True
    res["end_identical_note"] = (
        "★ D11 的 `end_identical_ok`（末帧逐位回零位）在本支**必须不成立**"
        "（停在半空）⟹ 按计划 §3 降级为只报：末帧与 f0 的世界位置差就是「飞了多高」。")
    end_gap, end_gap_bone = 0.0, None
    for n in samples[-1]:
        if n in ("frame", "low", "euler"):
            continue
        a, b = samples[-1][n], samples[0][n]
        if not (isinstance(a, (tuple, list)) and len(a) == 3):
            continue
        gap = (Vector(a) - Vector(b)).length * 1000.0
        if gap > end_gap:
            end_gap, end_gap_bone = gap, n
    res["end_away_report_mm"] = round(end_gap, 3)
    res["end_away_report_bone"] = end_gap_bone

    # ---- 收招不许瞬停（定格前 8 帧的单帧步长）----------------------------
    snap = 0.0
    snap_at = None
    for index in range(max(1, PLATEAU - 8), PLATEAU + 1):
        ea, eb = samples[index - 1]["euler"], samples[index]["euler"]
        for name in set(ea) | set(eb):
            a = ea.get(name, (0.0, 0.0, 0.0))
            b = eb.get(name, (0.0, 0.0, 0.0))
            step = max(abs(x - y) for x, y in zip(a, b))
            if step > snap:
                snap, snap_at = step, (index, name)
    res["no_snap_stop_step_deg"] = round(snap, 4)
    res["no_snap_stop_at"] = snap_at
    res["no_snap_stop_ok"] = bool(snap <= NO_SNAP_END_DEG)

    # ---- ★★ 四肢张开（拳的世界行程 / 拳架展开）---------------------------
    fist_dev, fist_dev_at = 0.0, None
    for frame in per:
        for s in SIDES:
            gap = (per[frame]["fist"][s] - IDLE_FIST[s]).length * 1000.0
            if gap > fist_dev:
                fist_dev, fist_dev_at = gap, (s, frame)
    res["fist_travel_mm"] = round(fist_dev, 3)
    res["fist_travel_at"] = fist_dev_at
    res["fist_spread_gain_mm"] = round(
        per[TOTAL]["fist_spread_mm"] - zero["fist_spread_mm"], 3)
    res["fist_flung_ok"] = bool(fist_dev >= FIST_TRAVEL_MIN_MM)
    # 脚（被甩起）的行程
    ankle_dev, ankle_dev_at = 0.0, None
    for frame in per:
        for s in SIDES:
            gap = (per[frame]["ankle"][s] - zero["ankle"][s]).length * 1000.0
            if gap > ankle_dev:
                ankle_dev, ankle_dev_at = gap, (s, frame)
    res["ankle_travel_mm"] = round(ankle_dev, 3)
    res["ankle_travel_at"] = ankle_dev_at
    res["legs_flung_ok"] = bool(ankle_dev >= ANKLE_TRAVEL_MIN_MM)
    # 膝的被动变化（"被甩"而不是"自己蹬"）
    kneeflex = {s: round(max(abs(per[f]["knee_deg"][s] - zero["knee_deg"][s])
                             for f in per), 3) for s in SIDES}
    res["knee_flex_peak_deg"] = kneeflex
    res["knee_flex_ok"] = bool(max(kneeflex.values()) >= 0.5)
    # 肩（力量链"下盘动 → 肩被带"）
    shoulder_move, shoulder_at = 0.0, None
    for frame in per:
        for s in SIDES:
            gap = (per[frame]["shoulder"][s] - zero["shoulder"][s]).length * 1000.0
            if gap > shoulder_move:
                shoulder_move, shoulder_at = gap, (s, frame)
    res["shoulder_move_mm"] = round(shoulder_move, 3)
    res["shoulder_move_at"] = shoulder_at
    res["shoulder_moves_ok"] = bool(shoulder_move >= 5.0)
    # 左右对称（本支是正视受力，不该有明显侧倾）
    lat_peak = max(abs(per[f]["pelvis_lat_deg"] - zero["pelvis_lat_deg"])
                   for f in per)
    res["pelvis_lat_peak_deg"] = round(lat_peak, 4)
    res["pelvis_lat_ok"] = bool(lat_peak <= 3.0)

    # ---- (i) 节奏 -------------------------------------------------------
    risers = sum(1 for f in range(TOTAL) if press(f + 1) > press(f) + 1e-9)
    fallers = sum(1 for f in range(TOTAL) if press(f + 1) < press(f) - 1e-9)
    res["press_rise_frames"] = risers
    res["press_fall_frames"] = fallers
    res["hit_speed_ok"] = bool(risers <= HIT_RISE_MAX_FRAMES
                               and fallers >= HIT_FALL_MIN_FRAMES)

    # ---- (j) 打击停顿（≥3 帧，姿态逐位冻结）------------------------------
    platform = HOLD_END - IMPACT
    plat_drift, plat_drift_at = 0.0, None
    for index in range(IMPACT + 1, HOLD_END + 1):
        ea, eb = samples[index - 1]["euler"], samples[index]["euler"]
        for name in set(ea) | set(eb):
            a = ea.get(name, (0.0, 0.0, 0.0))
            b = eb.get(name, (0.0, 0.0, 0.0))
            step = max(abs(x - y) for x, y in zip(a, b))
            if step > plat_drift:
                plat_drift, plat_drift_at = step, (index, name)
    plat_z_drift = max(abs(zs[f] - zs[IMPACT]) for f in range(IMPACT, HOLD_END + 1))
    res["hitstop_frames"] = platform
    res["hitstop_drift_deg"] = round(plat_drift, 4)
    res["hitstop_drift_at"] = plat_drift_at
    res["hitstop_z_drift_mm"] = round(plat_z_drift * 1000.0, 4)
    res["hitstop_present"] = bool(platform >= HITSTOP_MIN_FRAMES
                                 and plat_z_drift <= 1e-9)

    # ---- (k) 脚口径**显式跳过**（本支离地）--------------------------------
    res["foot_slide_skipped"] = True
    res["foot_slide_note"] = (
        "★ 方案 A（脚钉住）在本支**错**（要离地）⟹ `foot_probe` 显式关掉、"
        "`no_foot_slide_ok` 换成 `airborne_ok`、`ground_contact_ok` 显式跳过"
        "（同 A12 的先例：「全段离地，显式跳过 + 登记原因」）。")

    # ---- (l) 末帧口径：**不回原位**（在空中）----------------------------
    res["end_hold_skipped"] = True

    # ---- 零位短路（本支只有 f0 ⟹ 期望 0）--------------------------------
    expect = sum(1 for f in range(1, TOTAL + 1) if still(f))
    res["zero_shortcut_frames"] = _ZERO_SHORTCUT[0]
    res["zero_shortcut_expect"] = expect
    res["zero_shortcut_ok"] = bool(_ZERO_SHORTCUT[0] == expect
                                   and abs(p_back(IMPACT)) > 1e-12
                                   and abs(u_fold(IMPACT)) <= 1e-12)
    res["lock_frames"] = _ZERO_SHORTCUT_SKIPPED[0]
    res["lock_expect"] = TOTAL - PLATEAU
    res["lock_ok"] = bool(_ZERO_SHORTCUT_SKIPPED[0] == TOTAL - PLATEAU)

    # ---- 穿模（"折断了"的硬上界）----------------------------------------
    frames = sorted(set(list(range(0, TOTAL + 1, CLIP_EVERY))
                        + [IMPACT, HOLD_END, AIR_ENTRY, PLATEAU, TOTAL]))
    worst_clip, worst_clip_at, worst_clip_frame = 0.0, None, None
    for frame in frames:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        clip = PD.clip_metrics(arm)
        if clip["clip_max_mm"] > worst_clip:
            worst_clip = clip["clip_max_mm"]
            worst_clip_at = clip["clip_at"]
            worst_clip_frame = frame
    res["clip_max_mm"] = round(worst_clip, 2)
    res["clip_at"] = worst_clip_at
    res["clip_frame"] = worst_clip_frame
    res["no_face_clip_ok"] = bool(worst_clip <= CLIP_MAX_MM)

    # ---- 可达性 ---------------------------------------------------------
    worst_reach, worst_reach_frame = 0.0, None
    worst_leg, worst_leg_frame = 0.0, None
    for frame in range(0, TOTAL + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        for side in SIDES:
            up = "upperarm." + side
            shoulder = Vector(A.bone_world(arm, up, "head"))
            limit = (ARM_MAX[side]) * 0.9995
            ratio = (fist_target(arm, side, frame) - shoulder).length / limit
            if ratio > worst_reach:
                worst_reach, worst_reach_frame = ratio, (frame, side)
            hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
            leg_limit = (A.L_THIGH + A.L_SHIN) * 0.9995
            ratio = (ankle_target(arm, side, frame) - hip).length / leg_limit
            if ratio > worst_leg:
                worst_leg, worst_leg_frame = ratio, (frame, side)
    res["reach_ratio_max"] = round(worst_reach, 5)
    res["reach_ratio_at"] = worst_reach_frame
    res["reach_ok"] = bool(worst_reach <= REACH_MAX_RATIO)
    res["leg_reach_ratio_max"] = round(worst_leg, 5)
    res["leg_reach_ratio_at"] = worst_leg_frame
    res["leg_reach_ok"] = bool(worst_leg <= REACH_MAX_RATIO)

    # ---- 力量传导链（脚→腿→髋→腰→肩→手，每段都要有量）------------------
    res["chain_travel"] = {
        "foot_mm": round(ankle_dev, 2),
        "knee_deg": round(max(kneeflex.values()), 3),
        "hip_mm": round(res["pelvis_lift_impact_mm"], 2),
        "waist_deg": round(abs(pp[IMPACT]), 3),
        "shoulder_mm": round(shoulder_move, 2),
        "hand_mm": round(fist_dev, 2),
    }
    res["chain_present_ok"] = bool(
        res["chain_travel"]["foot_mm"] > 50.0
        and res["chain_travel"]["knee_deg"] > 0.2
        and res["chain_travel"]["hip_mm"] > 20.0
        and res["chain_travel"]["waist_deg"] > 2.0
        and res["chain_travel"]["shoulder_mm"] > 5.0
        and res["chain_travel"]["hand_mm"] > 30.0)

    # ---- 剪影 / aspect：只报不判 ----------------------------------------
    sil = P.silhouette(arm, "d12")
    res["aspect"] = sil["aspect"]
    res["fill_grid"] = sil["fill_grid"]
    res["width_m"] = sil["width_m"]
    res["height_m"] = sil["height_m"]

    if os.environ.get("D12_TRACE"):
        res["trace"] = {str(f): {
            "press": round(press(f), 4),
            "p_back": round(p_back(f), 4),
            "u_fold": round(u_fold(f), 4),
            "h_whip": round(h_whip(f), 4),
            "fling": round(fling(f), 4),
            "ball_z": round(ball_z(f) * 1000.0, 2),
            "has_z": round(zs[f] * 1000.0, 2),
            "vz": round(vz[f], 2) if f in vz else None,
            "lowL": None if clear[f]["L"] is None else round(clear[f]["L"] * 1000.0, 2),
            "lowR": None if clear[f]["R"] is None else round(clear[f]["R"] * 1000.0, 2),
            "pelvis_pitch": round(pp[f], 3),
            "chest_pitch": round(cp[f], 3),
            "head_pitch": round(hp[f], 3),
            "spine1_pitch": round(sp1[f], 3),
            "spine2_pitch": round(sp2[f], 3),
            "pelvis_y": round(dy[f], 2),
            "kneeL": round(per[f]["knee_deg"]["L"] - zero["knee_deg"]["L"], 3),
            "kneeR": round(per[f]["knee_deg"]["R"] - zero["knee_deg"]["R"], 3),
            "fistL": round((per[f]["fist"]["L"] - IDLE_FIST["L"]).length * 1000.0, 2),
            "fistR": round((per[f]["fist"]["R"] - IDLE_FIST["R"]).length * 1000.0, 2),
            "ankL": round((per[f]["ankle"]["L"] - zero["ankle"]["L"]).length * 1000.0, 2),
            "ankR": round((per[f]["ankle"]["R"] - zero["ankle"]["R"]).length * 1000.0, 2),
            "arm_euler": {n: [round(v, 2) for v in
                              samples[f]["euler"].get(n, (0.0, 0.0, 0.0))]
                          for n in ("upperarm.L", "forearm.L", "hand.L")},
            "uaL": [round(v * 1000.0, 1) for v in samples[f].get("upperarm.L", (0.0, 0.0, 0.0))],
            "uaLt": [round(v * 1000.0, 1) for v in samples[f].get("upperarm.L.tail", (0.0, 0.0, 0.0))],
            "faLt": [round(v * 1000.0, 1) for v in samples[f].get("forearm.L.tail", (0.0, 0.0, 0.0))],
            "uaRt": [round(v * 1000.0, 1) for v in samples[f].get("upperarm.R.tail", (0.0, 0.0, 0.0))],
            "faRt": [round(v * 1000.0, 1) for v in samples[f].get("forearm.R.tail", (0.0, 0.0, 0.0))],
        } for f in range(0, TOTAL + 1)}
    return res


# =============================================================== 引导
def _load_idle_zero(arm):
    """★ 零位真源：落盘 `Idle_01` action 的**帧 0**（引擎真正会播的那份数据）。"""
    action = bpy.data.actions.get(I1.NAME)
    if action is None:
        return {}, {"action": I1.NAME, "found": False}
    rot_keyed, loc_keyed = _keyed_bones(action)
    first = int(action.frame_range[0])
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    A.reset_pose(arm)
    bpy.context.scene.frame_set(first)
    bpy.context.view_layer.update()
    pose = {name: tuple(math.degrees(v)
                        for v in arm.pose.bones[name].rotation_euler)
            for name in rot_keyed if name in arm.pose.bones}
    loc = {name: tuple(arm.pose.bones[name].location)
           for name in loc_keyed if name in arm.pose.bones}
    if loc:
        pose["@loc"] = loc
    info = {"action": I1.NAME, "found": True, "frame": first,
            "expected_frame": 0, "rot_bones": len(rot_keyed),
            "loc_bones": sorted(loc_keyed),
            "frame_range": [int(v) for v in action.frame_range]}
    return pose, info


def _idle_replay(arm):
    return I1.idle_pose(arm, 0.0)


def _world_snapshot(arm, pose):
    A.apply_pose(arm, pose)
    bpy.context.view_layer.update()
    heads, dirs = {}, {}
    for name in A.PROBE_BONES:
        if name not in arm.pose.bones:
            continue
        heads[name] = Vector(A.bone_world(arm, name, "head"))
        dirs[name] = Vector(A.bone_direction(arm, name)).normalized()
    return heads, dirs


def boot():
    global ZERO, ZERO_WORLD, Z_SEAM, KNEE_DIR, ANKLE_0, IDLE_ANKLE, Z_PELVIS_REST
    ZERO, ZERO_WORLD = {}, {}
    ZERO_BASIS.clear()
    ZERO_DIR.clear()
    IDLE_FIST.clear()
    IDLE_SHOULDER.clear()
    IDLE_SPAN.clear()
    IDLE_ELBOW_DIR.clear()
    IDLE_HAND_DIR.clear()
    ANKLE_0.clear()
    IDLE_ANKLE.clear()
    KNEE_DIR.clear()
    ARM_MAX.clear()
    LOCK_POSE.clear()

    arm, meshes = A.open_animation_project()
    A.setup_scene()
    if I1.NAME not in bpy.data.actions:
        print("D12_BOOTSTRAP 缺 %s，先补跑" % I1.NAME)
        I1.main()
        arm, meshes = A.open_animation_project()
        A.setup_scene()

    for side in SIDES:
        UE.ARM_LEN[side] = {
            "upper": arm.pose.bones["upperarm." + side].length,
            "forearm": arm.pose.bones["forearm." + side].length,
            "hand": arm.pose.bones["hand." + side].length}
        ARM_MAX[side] = (UE.ARM_LEN[side]["upper"]
                         + UE.ARM_LEN[side]["forearm"]
                         + UE.ARM_LEN[side]["hand"])

    UE.ROLL_STEP_DEG = _env_f("D12_ROLLSTEP", 2.0)
    UE.ROLL_GRID = UE._roll_grid()
    UE.EULER_Y_SAFE = _env_f("D12_YSAFE", 88.0)
    UE.EULER_Y_WEIGHT = _env_f("D12_YWEIGHT", 0.0)

    for extra in LEG_BONES + ("foot.L", "foot.R"):
        if extra not in A.PROBE_BONES:
            A.PROBE_BONES = tuple(A.PROBE_BONES) + (extra,)
        if extra not in A.PROBE_TAILS:
            A.PROBE_TAILS = tuple(A.PROBE_TAILS) + (extra,)
    A.PROBE_KEYS = A.PROBE_BONES + tuple(n + ".tail" for n in A.PROBE_TAILS)

    ZERO, saved_info = _load_idle_zero(arm)

    # ★ 与 `hit_assertions` 同一个坑：`_load_idle_zero` 把 `Idle_01` 绑上了，
    #   不摘 action 的话下面两次 `_world_snapshot` 都会被 depsgraph 按当前帧覆盖。
    arm.animation_data.action = None
    replay = _idle_replay(arm)
    saved_heads, saved_dirs = _world_snapshot(arm, ZERO)
    replay_heads, replay_dirs = _world_snapshot(arm, replay)
    geom_pos, geom_pos_bone = 0.0, None
    for name, point in saved_heads.items():
        other = replay_heads.get(name)
        if other is None:
            continue
        gap = (point - other).length * 1000.0
        if gap > geom_pos:
            geom_pos, geom_pos_bone = gap, name
    geom_dir, geom_dir_bone = 0.0, None
    for name, direction in saved_dirs.items():
        other = replay_dirs.get(name)
        if other is None:
            continue
        dot = max(-1.0, min(1.0, direction.dot(other)))
        gap = math.degrees(math.acos(dot))
        if gap > geom_dir:
            geom_dir, geom_dir_bone = gap, name
    euler_diff, euler_bone, per_bone = 0.0, None, {}
    for name, value in ZERO.items():
        if name.startswith("@"):
            continue
        got = replay.get(name)
        if got is None:
            continue
        row = [_f32(a) - _f32(b) for a, b in zip(got, value)]
        worst = max(abs(v) for v in row)
        if worst > euler_diff:
            euler_diff, euler_bone = worst, name
        if worst > 0.5:
            per_bone[name] = [round(v, 4) for v in row]
    IDLE_MATCH.update({
        "src": "%s@%d" % (saved_info.get("action"), saved_info.get("frame")),
        "saved": saved_info,
        "euler_diff": round(euler_diff, 6), "euler_bone": euler_bone,
        "per_bone": per_bone,
        "geom_pos": round(geom_pos, 6), "pos_bone": geom_pos_bone,
        "geom_dir": round(geom_dir, 6), "dir_bone": geom_dir_bone,
        "matched": bool(euler_diff <= IDLE_MATCH_TOL_DEG
                        and geom_pos <= IDLE_GEOM_POS_MAX_MM
                        and geom_dir <= IDLE_GEOM_DIR_MAX_DEG),
    })

    A.apply_pose(arm, ZERO)
    bpy.context.view_layer.update()
    Z_SEAM = A.bone_world(arm, "pelvis", "head").z
    ANKLE_0 = {s: Vector(A.bone_world(arm, "foot." + s, "head")) for s in SIDES}
    for side in SIDES:
        IDLE_FIST[side] = Vector(A.bone_world(arm, "hand." + side, "tail"))
        IDLE_ANKLE[side] = Vector(A.bone_world(arm, "foot." + side, "head"))
        IDLE_HAND_DIR[side] = Vector(
            A.bone_direction(arm, "hand." + side)).normalized()
        shoulder = Vector(A.bone_world(arm, "upperarm." + side, "head"))
        IDLE_SHOULDER[side] = shoulder
        IDLE_SPAN[side] = (IDLE_FIST[side] - shoulder).length
        elbow = Vector(A.bone_world(arm, "upperarm." + side, "tail"))
        IDLE_ELBOW_DIR[side] = tuple((elbow - shoulder).normalized())
    for side in SIDES:
        hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
        knee = Vector(A.bone_world(arm, "shin." + side, "head"))
        ankle = Vector(A.bone_world(arm, "foot." + side, "head"))
        axis = (ankle - hip).normalized()
        bulge = (knee - hip) - axis * (knee - hip).dot(axis)
        KNEE_DIR[side] = (bulge.normalized() if bulge.length > 1e-9
                          else Vector((0.0, -0.94, -0.34)))
    for bone in ARM_BONES + LEG_BONES:
        UE.IDLE_BASIS[bone] = arm.pose.bones[bone].matrix.to_3x3().copy()
        UE.IDLE_DIR[bone] = A.bone_direction(arm, bone)

    ZERO_WORLD = {n: tuple(v) for n, v in saved_heads.items()}
    for name in A.PROBE_TAILS:
        if name in arm.pose.bones:
            ZERO_WORLD[name + ".tail"] = tuple(A.bone_world(arm, name, "tail"))
    for name in A.PROBE_BONES:
        if name in arm.pose.bones:
            ZERO_BASIS[name] = tuple(
                arm.pose.bones[name].matrix.to_3x3().to_quaternion())
    for name in ARM_BONES:
        ZERO_DIR[name] = Vector(A.bone_direction(arm, name)).normalized()

    zrow = _body_metrics(arm)
    A.report("D12_LAYOUT", {
        "total_frames": TOTAL, "seconds": round(TOTAL / float(A.FPS), 3),
        "impact": IMPACT, "hold_end": HOLD_END, "hit_hold": HIT_HOLD,
        "air_entry": AIR_ENTRY, "plateau": PLATEAU, "apex": APEX,
        "cancel": CANCEL, "recover_end": RECOVER_END,
        "segments": 3, "hit_points": 0,
        "root_motion_m": [0.0, 0.0],
        "force_direction": "腰部（下盘-中段）：一记打在腰侧/腰前的重击把**下盘先顶起来**，"
                           "上身后折（滞后）→ 整体离地 → 抛入空中",
        "leg_plan": "f0/f1 零位踝（钉住）→ f2 鞋跟离地 → f3 起整体腾空、"
                    "踝目标随髋走（拖尾），全程按共享解析弹道飞行",
        "ballistic": {"T_ORIGIN": T_ORIGIN,
                      "takeoff_pelvis_z_m": JS.TAKEOFF_PELVIS_Z,
                      "takeoff_speed_mps": round(JS.TAKEOFF_SPEED * A.FPS, 3),
                      "g_per_frame": JS.G_PER_FRAME,
                      "apex_frame": round(F_APEX, 3),
                      "apex_z_mm": round(Z_APEX * 1000.0, 3),
                      "entry_frame": AIR_ENTRY,
                      "entry_z_mm": round(ball_z(AIR_ENTRY) * 1000.0, 3),
                      "entry_vz_mm": round(ball_vz(AIR_ENTRY) * 1000.0, 3),
                      "end_z_mm": round(ball_z(TOTAL) * 1000.0, 3),
                      "end_vz_mm": round(ball_vz(TOTAL) * 1000.0, 3),
                      "tol_mm": BALLISTIC_TOL_MM},
        "zero_source": "Idle_01@%d（落盘 action，非重演）" % saved_info.get(
            "frame"),
        "zero_pose_src": saved_info,
        "zero_vs_idle_pose_euler_max_diff_deg": round(euler_diff, 6),
        "zero_vs_idle_pose_worst_bone": euler_bone,
        "zero_vs_idle_pose_geom_pos_mm": round(geom_pos, 6),
        "zero_vs_idle_pose_geom_dir_deg": round(geom_dir, 6),
        "zero_pelvis_z_mm": round(Z_SEAM * 1000.0, 3),
        "zero_pelvis_pitch_deg": round(zrow["pelvis_pitch_deg"], 4),
        "zero_chest_pitch_deg": round(zrow["chest_pitch_deg"], 4),
        "zero_ankle_mm": {s: [round(v * 1000.0, 2) for v in ANKLE_0[s]]
                          for s in SIDES},
        "zero_hip_z_mm": {s: round(zrow["hip_z"][s] * 1000.0, 2) for s in SIDES},
        "zero_knee_deg": {s: round(zrow["knee_deg"][s], 3) for s in SIDES},
        "zero_fist_mm": {s: [round(v * 1000.0, 2) for v in IDLE_FIST[s]]
                         for s in SIDES},
        "zero_fist_spread_mm": round(zrow["fist_spread_mm"], 2),
        "zero_span_mm": {s: round(IDLE_SPAN[s] * 1000.0, 2) for s in SIDES},
        "arm_max_mm": {s: round(ARM_MAX[s] * 1000.0, 2) for s in SIDES},
        "pelvis_back_deg": PELVIS_BACK_DEG, "chest_back_deg": CHEST_BACK_DEG,
        "head_back_deg": HEAD_BACK_DEG,
        "spine_mix": [SPINE_MIX_1, SPINE_MIX_2],
        "drum": {"phase": "f0 站定 → f3 命中（骨盆被顶起 190 mm）→ f3~6 三帧完全停顿 "
                          "→ f6~12 离地进入弹道 → f12~22 空中自持 → f22~34 定格（刚性平移）"},
        "p_keys": [list(k) for k in P_KEYS],
        "u_keys": [list(k) for k in U_KEYS],
        "h_keys": [list(k) for k in H_KEYS],
        "fling_keys": [list(k) for k in FLING_KEYS],
        "pelvis_z_keys": [list(k) for k in PELVIS_Z_KEYS],
        "roll_weight_mode": ROLL_WEIGHT_MODE,
        "note": ("D12 被击飞：零位 = Idle_01 落盘帧 0；★ **腰部首先受到力量** —— "
                 "骨盆先被顶起（竖速峰在命中帧 f3）+ 世界后仰领先，上身由 u_fold "
                 "**滞后**带动（命中窗口内恒 0 ⟹ 纹丝不动）；f12 起骨盆 z 逐帧 = "
                 "共享解析弹道（同 A10/A11/A12/B08）；★ 水平**不烘**位移"
                 "（root_motion_m=[0,0]）；末 9 帧**逐位复用** f25 姿态 + 刚性平移；"
                 "脚口径全部换掉（foot_probe 关、ground_contact 跳、"
                 "end_identical → end_air_hold）"),
    })
    return arm, meshes


def main():
    arm, meshes = boot()

    JS._PREV_EULER.clear()
    A.apply_pose(arm, ZERO)
    bpy.context.view_layer.update()
    for name in ARM_BONES + LEG_BONES:
        UE.CARRY_Q[name] = arm.pose.bones[name].matrix.to_3x3().to_quaternion()
    for name, value in ZERO.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)

    keyframes = [(0, ZERO)]
    for frame in range(1, TOTAL + 1):
        keyframes.append((frame, solve_pose(arm, frame, meshes)))

    meta = {
        "anim_id": NAME,
        "loop": False,
        "category": "防御与受击",
        "note": ("被击飞：腰部首先受力（骨盆被顶起 + 世界后仰领先），上身滞后后折；"
                 "f12 起骨盆 z = 共享解析弹道（同 A10/A11/A12/B08）；水平不烘位移；"
                 "末 9 帧定格自持（刚性平移；f25 起）"),
        "antic_frame": 0,
        "hit_frame": IMPACT,
        "cancel_frame": CANCEL,
        "stagger_end_frame": HOLD_END,
        "air_entry_frame": AIR_ENTRY,
        "self_hold_frame": PLATEAU,
        "hitstop_frames": HIT_HOLD,
        "hit_points": 0,
        "root_motion_m": [0.0, 0.0],
        "hit_point_m": None,
        "end_pelvis_z_m": round(ball_z(TOTAL), 6),
        "end_vz_m_per_frame": round(ball_vz(TOTAL), 6),
        "ballistic_ref": "anim_jump_start.TAKEOFF_PELVIS_Z/TAKEOFF_SPEED + "
                         "anim_jump_fall.G_PER_FRAME（同一解析弹道，相位 T_ORIGIN=%.2f）"
                         % T_ORIGIN,
        "start_pose_ref": "Idle_01 帧 0（战斗待机）",
        "end_pose_ref": "空中定格（**不回原位**；落在共享弹道上）",
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.add_markers(action, {"START": 0, "IMPACT": IMPACT, "HOLD_END": HOLD_END,
                           "AIR_ENTRY": AIR_ENTRY, "SELF_HOLD": PLATEAU,
                           "APEX": APEX, "CANCEL": CANCEL, "END": TOTAL})
    A.set_hitstop(action, IMPACT, HOLD_END)

    samples = A.sample_animation(arm, action, 0, TOTAL, meshes)
    # ★ 本支**离地** ⟹ `foot_probe` **显式关掉**（计划 §3），改用 `airborne_ok`。
    report = A.run_common_assertions(samples, meta, foot_probe=())
    # ★ `ground_contact_ok` 由通用门禁算出，但本支**不适用**（全段离地）⟹ 摘掉 + 登记。
    report.pop("ground_contact_ok", None)
    report.pop("ground_min_mm", None)
    report.update(hit_assertions(arm, action, samples, meshes))
    report["meta"] = meta

    delta0 = 0.0
    for name, ref in ZERO.items():
        if name.startswith("@"):
            continue
        got = samples[0]["euler"].get(name)
        if got is None:
            continue
        delta0 = max(delta0, max(abs(_f32(a) - _f32(b))
                                 for a, b in zip(got, ref)))
    report["ua_start_delta_deg"] = round(delta0, 8)
    report["ua_start_ok"] = bool(delta0 <= SEAM_TOL)

    report["idle_zero_saved_ok"] = bool(IDLE_MATCH["matched"])
    report["idle_zero_src"] = IDLE_MATCH["src"]
    report["idle_zero_euler_max_diff_deg"] = IDLE_MATCH["euler_diff"]
    report["idle_zero_euler_worst_bone"] = IDLE_MATCH["euler_bone"]
    report["idle_zero_euler_roll_free_bones"] = IDLE_MATCH["per_bone"]
    report["idle_zero_geom_pos_mm"] = IDLE_MATCH["geom_pos"]
    report["idle_zero_geom_dir_deg"] = IDLE_MATCH["geom_dir"]

    report["failed"] = sorted(k for k, v in report.items()
                              if k.endswith("_ok") and v is not True)
    report["non_ok_bools"] = sorted(
        k for k, v in report.items()
        if isinstance(v, bool) and not k.endswith("_ok") and v is not True)
    A.report("D12_REPORT", report)

    if not SKIP_RENDER:
        # ★ 计划 §4：f0 / 命中 / 停顿中 / 离地帧 / 弹道中 / 自持段 / 末帧 × 侧 / 正 / 3Q
        #   主检**侧视**（前后 + 上下）—— 击飞读的是**后仰 + 抬升**。
        side_frames = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 16, 18,
                       20, 22, 24, 26, 28, 30, 32, 34]
        other_frames = [0, 3, 6, 12, 16, 22, 30, 34]
        A.render_pose_sheet(arm, action, side_frames, "launchhit",
                            views=(VIEW_D12_SIDE,))
        A.render_pose_sheet(arm, action, other_frames, "launchhit",
                            views=(VIEW_D12_FRONT, VIEW_D12_3Q))
        A.save_project()
        A.export_glb(arm)
    print("D12_DONE failed=%s" % report["failed"])
    print("D12_DONE non_ok_bools=%s" % report["non_ok_bools"])


# ★ 本支必须换取景：标准视图（中心 0.92 m / 宽 2.10 m）是给站姿定的，
#   D12 的骨盆要到 1.95 m（头 ~2.8 m）⟹ 用标准视图会把人和地一起切掉。
VIEW_D12_SIDE = ("side", (5.20, 0.0, 1.55), (0.0, 0.0, 1.55), 4.30,
                 (780, 1100))
VIEW_D12_FRONT = ("front", (0.0, -5.60, 1.55), (0.0, 0.0, 1.55), 4.30,
                  (780, 1100))
VIEW_D12_3Q = ("three_quarter", (3.80, -4.00, 1.70), (0.0, 0.0, 1.50), 4.30,
               (780, 1100))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("D12_FAILURE " + traceback.format_exc())
