"""anim_skill03 —— C11 `Skill_03` 旋转重拳（C 族第一支「世界朝向变化」支）。

目录：`doc/动画制作清单.md` 第 137 行；详细计划见该文件的
「下一支详细制作计划 —— C11 `Skill_03` 旋转重拳」。

================================================================ 本支的物理构造
三段 + 命停 + 收招：

    0 ──4── 起手接合（f0 逐位 = `Idle_01@0`，f1..4 全姿接合）
    4 ──16  ① 蓄力拧身（**反相**：骨盆局部 yaw 0 → −30°，双脚钉死不动）
    16 ─19  反相停顿 3 帧（冻住）
    19 ─23  ② 髋部释放（骨盆局部 yaw −30° → 0°，**拧身角全部交给骨盆自己转**）
    23 ─46  ③ 转体出拳（`root.rotation_euler.y` 0 → 360°，26 步加权角速度剖面）
    46 ─49  命停 4 帧（逐位冻结）
    49 ─104 收招（全姿欧拉仿射回 `Idle_01@0`，root yaw 停在 360°）

==================== 三条前无先例的难点，以及本支用探针实测出来的落法

★ **难点 1：世界朝向真的变了。** 此前 10 支（A/B/C09/C10）世界朝向恒定，
  所有门禁默认"骨的世界轴 = rest 轴"。本支骨盆要转约一整圈。

  落法（`probe_c11_axis.py` 实测确证，不是推断）：
    · `root.rotation_euler.y` **就是世界 yaw**。θ 扫描下 `hand.L/R` 的世界半径
      恒定 800.000 mm、`foot.L/R` 恒定 144.807 mm、z 逐位不变，且
      `root` 的 pose 3×3 = `Rz(θ) @ B0` 逐位吻合 —— 纯绕世界 +Z 的旋转。
      **+θ = 从上方看逆时针 = 角色向自己的左手方向转。**
    · `root.location` 按 `wloc` 在**未旋转的 rest 系**里生效
      （`matrix_basis = T(loc) @ R`）：θ=0 与 θ=90 下喂 `wloc(0.20,−0.10,0.05)`
      实测位移都恰好是 `(200, −100, 50) mm`，误差 `0.0000 mm`。
      ⟹ **绕枢轴补偿有干净闭式解**：`loc = (I − Rz(θ))·(P0 − ROOT_HEAD)`。

★ **难点 2：支撑脚要枢轴、不是滑。** 站姿门禁是"脚钉死 ≤3 mm"，转体时这条
  不可能成立 —— 脚在**转**。C07 第 3 件已经踩过：用 AABB 中心量支点会出
  57 mm 伪影。本支因此把判据换成 **枢轴顶点**（鞋底"最前的最低点"那个网格顶点，
  实测 = `Shoe_Sole_R` 顶点 141，即右鞋前掌球部），量它的**水平**漂移。

  枢轴顶点漂移的实测基线（C11 探针）：`leg_seat(..., ref=None)` 恒定用 Idle
  基准时**与转角无关**（θ = 0/45/90/180/270/360 全部落在同一点上，只有 ~12 mm
  的**常值垂直**偏差，那是 `leg_ik` 与 `leg_seat` 两套解法的落点差，不是旋转伪影）。
  ⟹ 判据定在**水平**漂移 ≤ 30 mm，垂直交给 `ground_contact_ok` 管。

★ **难点 3：动力链要判时序。** C10 的 `power_chain_ok` 只要求每段非零；
  本支要 峰值帧 髋 ≤ 肩 ≤ 拳。世界速度 = ω × r ⟹ 同一 ω 下半径排序天然给出
  髋 < 肩 < 拳，所以这条门禁在"转体主导"的动作里是**构造性成立**的 ——
  但正因如此它**只有同时成立才有意义**，峰值帧必须落在转体段内（否则是假绿）。

============================== 与 C10 的差异（其余全部沿用 C10 的构造）
  · 世界朝向：恒定 → **整圈单向自转**（判据 `spin_turn_ok` / `spin_speed_ok`）
  · 命中点：对手落点 → **自身拳套**（捡回 C09 的 `punch_frontmost_ok`，
    按**网格面**量，骨的 tail 是代理量，与观众看到的差 100 mm 量级）
  · 站姿脚钉死 → **枢轴顶点水平漂移**
  · 动力链只判"非零" → **判峰值帧时序**

============================== 复用件（不重写）
  `anim_lib`：`wloc` / `apply_pose` / `build_action` / `sample_animation` /
    `run_common_assertions` / `foot_lowest_by_side` / `report` / `render_pose_sheet` /
    `save_project` / `export_glb` / `bone_world` / `FIST` / `set_hitstop`
  `anim_run_stop`：`track`（Hermite + 末段切线 0）/ `smooth` / `slerp_dir`
  `anim_jump_start`：`_unwrap_xyz`（欧拉翻转分支）
  `anim_grab04`：`leg_seat` / `arm_seat` / `aim_bone_ref`（逆解 + 滚转基准）
  `anim_skill02`：`_ramp` 的思想（本支换成显式加权角速度剖面 `SPIN_W`）

============================== 调试开关（环境变量，无需改文件）
  SKIP_RENDER=1    跳过渲染 + 存盘 + 导出（单轮 ~60 s，迭代期用）
  C11_TRACE=1      逐帧：骨盆/拳/肩/髋世界坐标、yaw、角速度、腿可达比
  C11_YAW_DIAG=1   逐帧骨盆世界 yaw 与 root/pelvis 分通道贡献
  C11_ARM_DIAG=1   逐帧臂几何（肩→手距离、折叠下限、肘偏轴量）
  C11_BLEND_DIAG=1 打印收招仿射两端（抓欧拉翻转分支用）

运行（正式那一轮）：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python anim_skill03.py
"""

import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A            # noqa: E402
import anim_idle_01 as I1       # noqa: E402
import anim_grab04 as G4        # noqa: E402
import anim_run_stop as RS      # noqa: E402
import anim_jump_start as JS    # noqa: E402

NAME = "Skill_03"
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"
SIDES = ("L", "R")
XOFF = {"L": 1.0, "R": -1.0}          # +X = 角色左（`rig_axis_map.md`）

PIVOT_SIDE = "R"                      # 支撑脚（枢轴脚）
SWING_SIDE = "L"                      # 摆动脚（收腿 + 落地）
PUNCH_SIDE = "R"                      # 出拳手（与枢轴同侧：向左转时右手绕到正面）
GUARD_SIDE = "L"                      # 护身手


def _env_f(key, default):
    return float(os.environ.get(key, default))


def _env_i(key, default):
    return int(os.environ.get(key, default))


# ---------------------------------------------------------------- 帧预算
TOTAL = _env_i("C11_TOTAL", 104)            # 1.733 s @60fps
EASE_END = _env_i("C11_EASE", 4)            # 全姿接合：f1..EASE_END 从 SEAM 平滑到解
COIL_END = _env_i("C11_COIL", 16)           # ① 蓄力拧身末（局部 yaw = −COIL_DEG）
COIL_HOLD = _env_i("C11_COILHOLD", 3)       # 反相停顿帧数
COIL_HOLD_END = COIL_END + COIL_HOLD        # 19
REL_END = _env_i("C11_REL", 23)             # ② 髋部释放完毕 = root 自转起点
HIT = _env_i("C11_HIT", 46)                 # ③ 命中帧
FIRE_HOLD = _env_i("C11_FIREHOLD", 4)       # 命停 4 帧（§0.1 的 2~4）
HOLD_END = HIT + FIRE_HOLD - 1              # 49
PLANT = _env_i("C11_PLANT", 52)             # 摆动脚落地帧
SETTLE = _env_i("C11_SETTLE", 92)           # 收招落定（此后逐位 = Idle_01@0）
CANCEL = _env_i("C11_CANCEL", 96)           # 可取消帧
SPIN_STEPS = HIT - REL_END                  # 23 步

# 转体总量（度）。目标 360°：末帧回到正面，且骨盆世界 yaw 累计 = COIL_DEG + SPIN_TURN
SPIN_TURN = _env_f("C11_TURN", 360.0)
COIL_DEG = _env_f("C11_COIL_DEG", -30.0)    # 反相拧身角（负 = 向右手方向拧）

# 角速度权重表（逐步，不是逐帧累计）。形状要求（`spin_speed_ok`）：
#   · 峰值出现在命中前 1/3 段内 → 峰值下标 5 / 23 = 0.217 ≤ 1/3
#   · 命中帧角速度 ≤ 0.25 × 峰值 → 末步 0.36 / 峰值 1.58 = 0.228
#   · 每帧步长 ≤ 25°（`no_teleport` 量的是欧拉逐帧步长）→ 实测峰值 22.86°
SPIN_W = [float(v) for v in os.environ.get(
    "C11_SPIN_W",
    "0.42,0.78,1.10,1.36,1.52,1.58,1.58,1.55,1.51,1.46,1.40,1.33,"
    "1.26,1.18,1.10,1.02,0.94,0.86,0.78,0.69,0.60,0.50,0.36").split(",")]


def _spin_cum():
    """归一化累积曲线：`cum[k]` = 前 k 步占总量之比（`cum[0] = 0`，`cum[n] = 1`）。"""
    out = [0.0]
    run = 0.0
    for weight in SPIN_W:
        run += weight
        out.append(run)
    total = out[-1]
    return [v / total for v in out]


SPIN_CUM = _spin_cum()

# ---------------------------------------------------------------- 骨盆高度（Δ 相对 SEAM）
# 探针定标：绕枢轴刚性旋转**不拉长**髋-踝距离（三个骨盆高度下比值随 0~360° 完全恒定），
# 所以 `ik_reach_ok` 的威胁不在转体本身，而在**站高**：与 Idle 齐平时腿几乎伸直。
# 坐实的高度（Idle 骨盆 830 mm）：蓄力 −38、转体最深处 −54、命中 −44。
PZ_KEYS = ((0, 0.0), (COIL_END, -38.0), (COIL_HOLD_END, -38.0),
           (REL_END, -50.0), (30, -54.0), (HIT, -44.0), (HOLD_END, -44.0),
           (PLANT, -34.0), (SETTLE, 0.0), (TOTAL, 0.0))

# ---------------------------------------------------------------- 躯干扭转轨道（度）
# 反相蓄力：骨盆 −30 是主动，脊椎再叠 2×(−8) ⟹ 胸腔对世界拧到 −56，而脖子+头
# 各看 +18 ⟹ 头只差 −20（"拧身但眼睛盯着目标"）。
#
# ★ **拧身的释放要「髋先、腰随」**（第 2 轮的实测教训）：
#   首版让脊椎/胸腔在 `COIL_HOLD_END..REL_END` 跟着骨盆**一起**解拧，结果
#   `chain_peak_frame` 测出 髋@29 / 肩@**22** / 拳@33 —— 肩的峰值落在**蓄力释放段**，
#   而髋的峰值在转体段（世界速度 = ω×r，转体段的 ω 是释放段的 2 倍）。
#   两段的几何尺度也不同：枢轴在**右鞋前掌**，而右肩几乎正在枢轴正上方
#   （实测：转体段 `shoulder` 的世界半径 ~70 mm、`hip_R` ~88 mm、`pelvis` ~160 mm），
#   所以"释放段的躯干解拧"给肩带来的世界速度**反而大过**转体段。
#   修法（物理上也更对）：**释放段只放骨盆，拧身留在躯干里**；躯干在转体段
#   0..约 34 帧内把 52° 解开 ⟹ "髋先转、腰随后甩过去"的鞭打，肩的峰值被推到
#   转体段内（≥ 髋的峰值帧、≤ 拳的峰值帧）。
PELVIS_RY = ((0, 0.0), (COIL_END, COIL_DEG), (COIL_HOLD_END, COIL_DEG),
             (REL_END, 0.0), (TOTAL, 0.0))
SPINE_RY = ((0, 0.0), (COIL_END, -8.0), (COIL_HOLD_END, -8.0), (REL_END, -8.0),
            (34, 8.0), (HIT, 8.0), (HOLD_END, 8.0), (SETTLE, 0.0), (TOTAL, 0.0))
CHEST_RY = ((0, 0.0), (COIL_END, -10.0), (COIL_HOLD_END, -10.0),
            (REL_END, -10.0), (34, 10.0), (HIT, 10.0), (HOLD_END, 10.0),
            (SETTLE, 0.0), (TOTAL, 0.0))
NECK_RY = ((0, 0.0), (COIL_END, 18.0), (COIL_HOLD_END, 18.0), (REL_END, 12.0),
           (34, -9.0), (HIT, -11.0), (HOLD_END, -11.0), (SETTLE, 0.0),
           (TOTAL, 0.0))
HEAD_RY = ((0, 0.0), (COIL_END, 18.0), (COIL_HOLD_END, 18.0), (REL_END, 12.0),
           (34, -9.0), (HIT, -11.0), (HOLD_END, -11.0), (SETTLE, 0.0),
           (TOTAL, 0.0))
# 俯仰（rx）：蓄力沉腰、命中收腹压肩
PELVIS_RX = ((0, None), (COIL_END, 9.0), (COIL_HOLD_END, 9.0), (REL_END, 7.0),
             (HIT, 9.0), (HOLD_END, 9.0), (SETTLE, None), (TOTAL, None))
CHEST_RX = ((0, None), (COIL_END, 5.0), (COIL_HOLD_END, 5.0), (REL_END, 3.0),
            (HIT, 11.0), (HOLD_END, 11.0), (SETTLE, None), (TOTAL, None))
NECK_RX = ((0, None), (COIL_END, -9.0), (COIL_HOLD_END, -9.0), (REL_END, -8.0),
           (HIT, -13.0), (HOLD_END, -13.0), (SETTLE, None), (TOTAL, None))
HEAD_RX = ((0, None), (COIL_END, 7.0), (COIL_HOLD_END, 7.0), (REL_END, 6.0),
           (HIT, 11.0), (HOLD_END, 11.0), (SETTLE, None), (TOTAL, None))
SHOULDER_RX = ((0, None), (COIL_END, -12.0), (COIL_HOLD_END, -12.0),
               (REL_END, -10.0), (HIT, -22.0), (HOLD_END, -22.0),
               (SETTLE, None), (TOTAL, None))

TARGET_BONES = ("pelvis", "spine_01", "spine_02", "chest", "neck", "head",
                "shoulder.L", "shoulder.R")

# ---------------------------------------------------------------- 腿：摆动脚收腿轨道
# 体坐标（米）。`rigid()` 把它随体转成世界点 ⟹ "收腿"就是体坐标里把踝拉近躯干。
TUCK_KEYS = {
    "bx": ((0, None), (REL_END, None), (30, 0.100), (HIT, 0.110),
           (50, 0.130), (PLANT, None), (TOTAL, None)),
    "by": ((0, None), (REL_END, None), (30, -0.070), (HIT, -0.090),
           (50, -0.140), (PLANT, None), (TOTAL, None)),
    "bz": ((0, None), (REL_END, None), (30, 0.320), (HIT, 0.300),
           (50, 0.180), (PLANT, None), (TOTAL, None)),
}

# ---------------------------------------------------------------- 手：体坐标目标轨道（米）
# 出拳手（R）：贴身蓄力 → 离心甩出 → 命中前推 → **分级收招**。
# 命中点定标（探针 `hand_reach`：最大无截断比 0.9196 @ 体坐标 y −0.65）：
# 命中体坐标 y 取 −0.65，配胸腔领先 +26° 把右肩送到前，实得比 ≈ 0.89（不截断）。
#
# ★ 收招**不许**让手从命中点 3 帧内弹回 Idle（第 3 轮 `no_teleport` 28.525° @
#   `forearm.R` 的病灶）：命中点体坐标 y = −0.650、Idle 是 −0.273 ⟹ 手要退
#   419 mm。首版把 `(PLANT, None)` 直接写成"落地帧 = Idle 真值"，3 帧退完
#   ⟹ 140 mm/帧、肘角 ~28°/帧。改成 f58 / f70 两个中间关键点，退程拉到
#   HOLD_END→SETTLE（43 帧），每帧 ≤ 17 mm。
PUNCH_KEYS = {
    "bx": ((0, None), (COIL_END, -0.300), (COIL_HOLD_END, -0.300),
           (REL_END, -0.420), (30, -0.500), (38, -0.440), (HIT, -0.300),
           (HOLD_END, -0.300), (58, -0.245), (70, -0.185),
           (SETTLE, None), (TOTAL, None)),
    "by": ((0, None), (COIL_END, 0.060), (COIL_HOLD_END, 0.060),
           (REL_END, -0.050), (30, -0.320), (38, -0.560), (HIT, -0.650),
           (HOLD_END, -0.650), (58, -0.520), (70, -0.365),
           (SETTLE, None), (TOTAL, None)),
    "bz": ((0, None), (COIL_END, 1.240), (COIL_HOLD_END, 1.240),
           (REL_END, 1.300), (30, 1.345), (38, 1.355), (HIT, 1.350),
           (HOLD_END, 1.350), (58, 1.330), (70, 1.310),
           (SETTLE, None), (TOTAL, None)),
}
GUARD_KEYS = {
    "bx": ((0, None), (COIL_END, 0.165), (COIL_HOLD_END, 0.165),
           (REL_END, 0.150), (HIT, 0.105), (HOLD_END, 0.105),
           (62, 0.128), (SETTLE, None), (TOTAL, None)),
    "by": ((0, None), (COIL_END, -0.215), (COIL_HOLD_END, -0.215),
           (REL_END, -0.200), (HIT, -0.255), (HOLD_END, -0.255),
           (62, -0.286), (SETTLE, None), (TOTAL, None)),
    "bz": ((0, None), (COIL_END, 1.345), (COIL_HOLD_END, 1.345),
           (REL_END, 1.330), (HIT, 1.300), (HOLD_END, 1.300),
           (62, 1.283), (SETTLE, None), (TOTAL, None)),
}
ELBOW_PUNCH = ((0, None), (COIL_END, (-0.55, 0.50, -0.67)),
               (COIL_HOLD_END, (-0.55, 0.50, -0.67)),
               (REL_END, (-0.86, 0.16, -0.48)), (30, (-0.90, 0.02, -0.43)),
               (HIT, (-0.45, 0.20, -0.87)), (HOLD_END, (-0.45, 0.20, -0.87)),
               (64, None), (TOTAL, None))
ELBOW_GUARD = ((0, None), (COIL_END, (0.60, 0.36, -0.72)),
               (COIL_HOLD_END, (0.60, 0.36, -0.72)),
               (REL_END, (0.64, 0.14, -0.76)), (HIT, (0.62, 0.10, -0.78)),
               (HOLD_END, (0.62, 0.10, -0.78)), (66, None), (TOTAL, None))

# ---------------------------------------------------------------- 门禁阈值
SOLE_RANGE_MM = (-2.0, 6.0)
NO_TELEPORT_MAX_DEG = 25.0
SEAM_TOL = 1e-6
REACH_MAX_RATIO = 0.995
PLANT_MAX_MM = _env_f("C11_PLANT_MAX", 3.0)
PIVOT_MAX_MM = _env_f("C11_PIVOT_MAX", 30.0)
SPIN_MIN_DEG = _env_f("C11_SPIN_MIN", 300.0)
SPIN_MAX_DEG = _env_f("C11_SPIN_MAX", 400.0)
COIL_MIN_DEG = _env_f("C11_COILMIN", 18.0)
COIL_MAX_DEG = _env_f("C11_COILMAX", 55.0)
WIND_MIN_F = _env_f("C11_WINDMIN", 10.0)
WIND_MAX_F = _env_f("C11_WINDMAX", 14.0)
SPEED_PEAK_FRAC = _env_f("C11_PEAKFRAC", 1.0 / 3.0)
SPEED_DROP_RATIO = _env_f("C11_DROPRATIO", 0.25)
CHAIN_MIN_MMPS = _env_f("C11_CHAINMIN", 800.0)
FRONT_LEAD_MM = _env_f("C11_FRONTLEAD", 80.0)
ROOT_H_MAX_MM = _env_f("C11_ROOTH", 700.0)
ROOT_Z_MAX_MM = _env_f("C11_ROOTZ", 150.0)
SWING_LIFT_MIN_MM = _env_f("C11_SWINGLIFT", 150.0)
END_POSE_TOL_MM = _env_f("C11_ENDTOL", 0.5)
ARM_REF_MAX_DEG = _env_f("C11_REFMAX", 75.0)
ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")
MESH_GLOVE = {"L": "Hand_Palm_L", "R": "Hand_Palm_R"}

# ---------------------------------------------------------------- 观测量
SEAM_POSE = {}
SEAM_EULER = {}
SEAM_360 = {}
Z_SEAM = 0.0
ANKLE_0 = {}
PIVOT0 = None
PIVOT_KEY = None
FOOT0 = {}
IDLE_HAND = {}
IDLE_KNEE_DIR = {}
IDLE_BASIS = {}
IDLE_DIR = {}
IDLE_ELBOW = {}
ARM_LEN = {}
ARM_REF = {}
E0 = {}
E_END_UNW = {}
ARM_CLAMP = {}
LOG = {}
PIVOT_REF = None


# =============================================================== 几何工具
def rot2(x, y, theta_deg):
    c = math.cos(math.radians(theta_deg))
    s = math.sin(math.radians(theta_deg))
    return (x * c - y * s, x * s + y * c)


def rigid(xy, theta_deg):
    """世界 xy 绕枢轴 `PIVOT0` 刚性转 `theta_deg`（绕竖直轴）。"""
    dx, dy = xy[0] - PIVOT0[0], xy[1] - PIVOT0[1]
    rx, ry = rot2(dx, dy, theta_deg)
    return (PIVOT0[0] + rx, PIVOT0[1] + ry)


def rot_dir(d, theta_deg):
    x, y = rot2(d[0], d[1], theta_deg)
    return (x, y, d[2])


def root_loc(theta_deg, extra=(0.0, 0.0, 0.0)):
    """**绕枢轴补偿**的 root 局部位移（闭式解，`probe_c11_axis.py` 已实测）。

    `pose.matrix(root) = M0 @ T(loc) @ R(θ)`，且 loc 在**未旋转的 rest 系**里
    （实测 θ=0/90 位移都恰好是 `wloc` 给的世界向量，误差 0）。世界等效 =
    先绕 `ROOT_HEAD` 转 R(θ)、再整体平移 `B0 @ loc`；要让枢轴顶点 `P0` 不动：

        B0 @ loc = (I − R(θ)) · (P0 − ROOT_HEAD)     （只取 xy）

    `B0^{-1}` 就是 `wloc`（局部 X→世界 X、局部 Y→世界 Z、局部 Z→世界 −Y）。
    """
    dx = PIVOT0[0]
    dy = PIVOT0[1]
    rx, ry = rot2(dx, dy, theta_deg)
    wx = dx - rx + extra[0]
    wy = dy - ry + extra[1]
    wz = extra[2]
    return (wx, wz, -wy)


def keep_foot(arm, side, theta_deg):
    """把鞋的世界朝向钉成「`Idle@01` 的鞋朝向绕世界 Z 转 θ」。

    为什么不用 `A.keep_world_orientation`（钉回 **rest**）：那是 θ=0 的版本，
    转体时鞋就"不跟体转"了（鞋尖永远指同一世界方向）= 悬浮陀螺。
    为什么基准取 **Idle 的鞋朝向**而不是 rest：Idle 站架的鞋有自己的角度，
    θ=0 时本函数必须逐位退化成 Idle ⟹ 收招末帧才能落回 `Idle_01@0`。
    """
    pose_bone = arm.pose.bones["foot." + side]
    target = (Matrix.Rotation(math.radians(theta_deg), 3, "Z")
              @ FOOT0[side]).to_4x4()
    target.translation = pose_bone.matrix.translation
    pose_bone.matrix = target
    bpy.context.view_layer.update()
    return tuple(math.degrees(v) for v in pose_bone.rotation_euler)


def mesh_frontmost(name):
    """某网格对象的**世界最前点**（y 最小）—— 按网格面量，骨 tail 是代理量。"""
    deps = bpy.context.evaluated_depsgraph_get()
    obj = bpy.data.objects.get(name)
    if obj is None:
        return None
    evaluated = obj.evaluated_get(deps)
    mesh = evaluated.to_mesh()
    matrix = evaluated.matrix_world
    best = None
    for vertex in mesh.vertices:
        point = matrix @ vertex.co
        if best is None or point.y < best[1]:
            best = (point.x, point.y, point.z)
    evaluated.to_mesh_clear()
    return best


def foot_vertices(side):
    deps = bpy.context.evaluated_depsgraph_get()
    points = []
    for name in A.FOOT_MESHES[side]:
        obj = bpy.data.objects.get(name)
        if obj is None:
            continue
        evaluated = obj.evaluated_get(deps)
        mesh = evaluated.to_mesh()
        matrix = evaluated.matrix_world
        for vertex in mesh.vertices:
            point = matrix @ vertex.co
            points.append((point.x, point.y, point.z, name, vertex.index))
        evaluated.to_mesh_clear()
    return points


def pivot_vertex(side):
    """鞋底「最前的最低点」顶点（C07 教训 3：AABB 中心会出 57 mm 伪影）。"""
    points = foot_vertices(side)
    if not points:
        return None
    zmin = min(p[2] for p in points)
    band = [p for p in points if p[2] <= zmin + 2.0]
    front = min(band, key=lambda p: p[1])
    return (front[3], front[4], (front[0], front[1], front[2]))


def vertex_world(key):
    deps = bpy.context.evaluated_depsgraph_get()
    obj = bpy.data.objects.get(key[0])
    if obj is None:
        return None
    evaluated = obj.evaluated_get(deps)
    mesh = evaluated.to_mesh()
    point = evaluated.matrix_world @ mesh.vertices[key[1]].co
    evaluated.to_mesh_clear()
    return (point.x, point.y, point.z)


def pelvis_yaw_unwrapped(series):
    """逐帧骨盆**世界 yaw**（用左右髋连线量，退化无关）。

    为什么不用骨方向：骨骼（pelvis/spine/chest）的 rest 方向是 **+Z**，它在 xy
    上的投影恒为 0 —— 用骨方向量 world yaw 是退化测点（C11 探针第一版就栽在这，
    θ=0/30/90/180 得到完全相同的读数）。左右髋连线是**水平**向量，退化无关。
    """
    raw = []
    for row in series:
        vec = Vector(row["hip_L"]) - Vector(row["hip_R"])
        raw.append(math.degrees(math.atan2(vec.y, vec.x)))
    out = [raw[0]]
    for index in range(1, len(raw)):
        value = raw[index]
        while value - out[-1] > 180.0:
            value -= 360.0
        while value - out[-1] < -180.0:
            value += 360.0
        out.append(value)
    return out


# =============================================================== 轨道求值
def pwl(keys, f, base=None):
    """分段 smoothstep 取值：**关键点逐位精确、段内无过冲、天然停顿**。

    `keys[i][1] is None` ⟹ 取 `base` 的值（用于 f0/末帧这些"必须回 Idle 真值"的点）。
    """
    if base is not None:
        keys = [(frame, base if value is None else value) for frame, value in keys]
    if f <= keys[0][0]:
        return keys[0][1]
    if f >= keys[-1][0]:
        return keys[-1][1]
    for index in range(len(keys) - 1):
        fa, va = keys[index]
        fb, vb = keys[index + 1]
        if fa <= f <= fb:
            span = float(fb - fa)
            if span < 1e-9:
                return vb
            return va + (vb - va) * RS.smooth((f - fa) / span)
    return keys[-1][1]


def pwl_vec(keys, f, base=None):
    def one(axis):
        return pwl([(frame, None if value is None else value[axis])
                    for frame, value in keys], f,
                   None if base is None else base[axis])
    return (one(0), one(1), one(2))

def root_yaw(f):
    """root 的世界 yaw（度）。f ≤ REL_END 恒 0（拧身由骨盆局部承担，脚才不滑）。"""
    if f <= REL_END:
        return 0.0
    if f >= HIT:
        return SPIN_TURN
    index = min(SPIN_STEPS, f - REL_END)
    return SPIN_TURN * SPIN_CUM[index]


def body_yaw(f):
    """躯干体坐标系的世界 yaw = root yaw + 骨盆局部 yaw。

    手的目标点定义在这个系里：身体转到哪，拳的**相对位置**不变 ⟹ 轨迹天然是
    一段绕枢轴的圆弧，不需要逐帧重定标。
    """
    return root_yaw(f) + _pelvis_ry(f)


PELVIS_RY_BASE = 0.0


def _pelvis_ry(f):
    if f <= COIL_END:
        return PELVIS_RY_BASE + (COIL_DEG - PELVIS_RY_BASE) * \
            RS.smooth(f / float(COIL_END))
    if f <= COIL_HOLD_END:
        return COIL_DEG
    if f <= REL_END:
        return COIL_DEG * (1.0 - RS.smooth(
            (f - COIL_HOLD_END) / float(REL_END - COIL_HOLD_END)))
    return 0.0


def pz_delta(f):
    return pwl(PZ_KEYS, f) / 1000.0


def q_of(frame):
    """收招进度：0 = `PLANT` 的**落地姿态**，1 = `Idle_01@0`（增量单调递减）。

    为什么收招的仿射起点是 `PLANT` 而不是 `HOLD_END`：命停之后到落地之前这几帧
    仍要**逐帧解姿态**（`leg_seat`）—— 摆动脚必须"踩实"，不能靠欧拉仿射顺带
    放下（仿射放脚的话脚落地会拖到 `SETTLE` 附近，0.7 s 才放下 = 拖沓）。
    落地帧起才切仿射，且此时双脚已在 Idle 的世界位置上 ⟹ 仿射只做微修正。
    """
    if frame <= PLANT:
        return 0.0
    if frame >= SETTLE:
        return 1.0
    u = (frame - PLANT) / float(SETTLE - PLANT)
    return 1.0 - (1.0 - u) ** 1.25


def hand_local(side, frame):
    """某只手在**体坐标系**里的目标点（米）；`rigid()` 再随体转成世界点。"""
    keys = PUNCH_KEYS if side == PUNCH_SIDE else GUARD_KEYS
    base = IDLE_HAND[side]
    return (RS.track([(k, base[i] if v is None else v)
                      for k, v in keys[("bx", "by", "bz")[i]]], frame)
            for i in (0, 1, 2))


def hand_target(side, frame):
    bx, by, bz = hand_local(side, frame)
    wx, wy = rigid((bx, by), body_yaw(frame))
    return (wx, wy, bz)


def elbow_dir(side, frame):
    keys = ELBOW_PUNCH if side == PUNCH_SIDE else ELBOW_GUARD
    base = IDLE_ELBOW[side]
    vec = pwl_vec(keys, frame, base)
    return rot_dir(vec, body_yaw(frame))


# =============================================================== 腿的目标
def is_planted(side, frame):
    """该脚在这一帧是否**承重**（承重才做贴地闭环、才受"不滑"门禁）。"""
    if side == PIVOT_SIDE:
        return True                       # 枢轴脚全程承重（转体时原地转）
    return frame <= REL_END or frame >= PLANT


def ankle_target(side, frame):
    """踝世界目标。

    枢轴脚：`rigid(ANKLE_0, root yaw)` —— 整体随体绕枢轴刚转，**枢轴顶点不动**。
    摆动脚：先钉原位（f ≤ REL_END），再在**体坐标**里收腿抬高（REL_END..HIT），
    最后在 PLANT 帧落回原位（此时 root yaw 已 = 360° ⟹ 落点 = 原世界点，不滑）。
    """
    if side == PIVOT_SIDE:
        xy = rigid((ANKLE_0[side].x, ANKLE_0[side].y), root_yaw(frame))
        return (xy[0], xy[1], ANKLE_0[side].z)
    bx = pwl(TUCK_KEYS["bx"], frame, ANKLE_0[side].x)
    by = pwl(TUCK_KEYS["by"], frame, ANKLE_0[side].y)
    bz = pwl(TUCK_KEYS["bz"], frame, ANKLE_0[side].z)
    xy = rigid((bx, by), root_yaw(frame))
    return (xy[0], xy[1], bz)


# ★ 本支踩到的**第三个**「世界朝向变化」专属坑，比前两个更隐蔽：
#   `knee_dir` 是 `leg_seat` 的**第二个**独立输入（不经过 `seat_ref`）。首版
#   两条分支都直接返回 `IDLE_KNEE_DIR`（**世界**常量），而膝弯方向是**体坐标**
#   特征 —— 体转了 360°，`knee_dir` 却钉在世界里不动。`leg_seat` 的膝位 =
#   两球交线按 `knee_dir` 投影 ⟹ 当 `knee_dir` 与髋-踝轴夹角接近 0/180° 时
#   `bulge` 退化、膝位翻转。实测：`shin.R` 在第 31 帧单帧跳 **88.15°**
#   （修 `seat_ref` 之前是 `thigh.R` 84.394°@29 —— 只把奇点搬了个位置）。
#   **修法：膝向也必须乘 `Rz(root_yaw)`。** 腿骨滚转不影响踝落点，
#   鞋的世界朝向随后被 `keep_foot` 整个覆盖 ⟹ 这一改动不动枢轴、不动贴地。
TUCK_KNEE = (0.42, -0.86, 0.30)       # 摆动脚高抬腿时的膝向（体坐标）
TUCK_FADE = ((0, 0.0), (REL_END, 0.0), (HIT, 1.0), (PLANT, 1.0),
             (PLANT + 12, 0.0), (TOTAL, 0.0))


def knee_dir(side, frame):
    """膝弯方向（世界）——**体坐标**特征绕 `root_yaw` 随体转。

    摆动脚在 `REL_END..PLANT` 收腿高抬（膝往前上方鼓）；落地后 12 帧内淡回 Idle，
    避免收招段膝向突变（突变 = 大腿方向突变 = 欧拉跳帧）。
    """
    base = IDLE_KNEE_DIR[side]
    if side == PIVOT_SIDE:
        return rot_vec(base, root_yaw(frame))
    u = pwl(TUCK_FADE, frame)
    if u <= 1e-9:
        return rot_vec(base, root_yaw(frame))
    return rot_vec(RS.slerp_dir(base, TUCK_KNEE, u), root_yaw(frame))


# =============================================================== 姿态装配
def torso_pose(frame):
    f = frame
    pose = {}
    for name in TARGET_BONES:
        base = SEAM_EULER[name]
        pose[name] = tuple(base)
    pose["pelvis"] = (pwl(PELVIS_RX, f, SEAM_EULER["pelvis"][0]),
                      _pelvis_ry(f),
                      SEAM_EULER["pelvis"][2])
    pose["spine_01"] = (SEAM_EULER["spine_01"][0], pwl(SPINE_RY, f), 0.0)
    pose["spine_02"] = (SEAM_EULER["spine_02"][0], pwl(SPINE_RY, f), 0.0)
    pose["chest"] = (pwl(CHEST_RX, f, SEAM_EULER["chest"][0]),
                     pwl(CHEST_RY, f), 0.0)
    pose["neck"] = (pwl(NECK_RX, f, SEAM_EULER["neck"][0]), pwl(NECK_RY, f), 0.0)
    pose["head"] = (pwl(HEAD_RX, f, SEAM_EULER["head"][0]), pwl(HEAD_RY, f), 0.0)
    for name in ("shoulder.L", "shoulder.R"):
        pose[name] = (pwl(SHOULDER_RX, f, SEAM_EULER[name][0]), 0.0, 0.0)
    pose["root"] = (0.0, root_yaw(f), 0.0)
    # ★ 骨盆局部位移 = `wloc(0, 0, pz_abs − 0.900)`，其中 0.900 是 **rest** 骨盆高度。
    #   首版写成 `wloc(0, 0, pz_delta)` 漏掉了 SEAM 的 −0.070 基线 ⟹ 整条曲线比
    #   Idle 高 70 mm ⟹ 第 1 帧腿被拉直（`leg_reach_ok` 0.99962 恰好顶到截断上限
    #   0.9995）、骨盆 17~21 mm 滑步、动力链峰值帧跑到 f1。**基线必须写进去。**
    pose["@loc"] = {"root": root_loc(root_yaw(f)),
                    "pelvis": A.wloc(0.0, 0.0, Z_SEAM + pz_delta(f) - 0.900)}
    return pose


LEG_BONES = ("thigh.L", "shin.L", "thigh.R", "shin.R")


def rot_basis(matrix, theta_deg):
    """把一套基准 3×3 绕世界 Z 转 θ（`IDLE_*` 都是在 yaw = 0 时量的）。"""
    return Matrix.Rotation(math.radians(theta_deg), 3, "Z") @ matrix


def rot_vec(vec, theta_deg):
    out = Matrix.Rotation(math.radians(theta_deg), 3, "Z") @ Vector(vec)
    return (out.x, out.y, out.z)


def seat_ref(bones, theta_deg):
    """**随体旋转**的逆解基准。

    ★ 这是本支踩到的第二个"世界朝向变化"专属坑，值得写清楚：

    `aim_bone_ref` 的滚转来自「`ref_dir` → `direction` 的**最小旋转**」。
    `ref_dir` 若恒取 Idle 的世界方向，而骨的世界方向随体转了 360°，那么
    中途必然经过「与 `ref_dir` 反向」的奇点 —— 最小旋转在那里病态，滚转翻转
    ⟹ 欧拉表示跳变。实测：`thigh.R` 在第 29 帧单帧跳 **84.394°**
    （`no_teleport` 上限 25°）。这不是"数值噪声"，是表示跳变 = 真闪帧。

    修法：基准本身随体转（`Rz(θ) @ IDLE_BASIS` / `Rz(θ) @ IDLE_DIR`），
    于是「基准方向 → 实际方向」的夹角**恒定等于体坐标内的偏离量**
    （腿 ≈ 0~30°、臂 ≤ ~70°），永远远离 180° 奇点，且**不需要任何就地重取**。

    安全性：腿骨滚转不改变踝的落点（`leg_seat` 是位置逆解），而鞋的世界朝向
    随后被 `keep_foot` 整个覆盖 ⟹ 枢轴顶点位置与腿的滚转**无关**
    （这正是 `foot_pivot_ok` 实测 0.009 mm 的原因）。
    """
    out = {}
    for bone in bones:
        out[bone] = (rot_basis(IDLE_BASIS[bone], theta_deg),
                     rot_vec(IDLE_DIR[bone], theta_deg))
    return out


def build_pose(arm, frame, shift):
    pose = torso_pose(frame)
    A.apply_pose(arm, pose)
    leg_ref = seat_ref(LEG_BONES, root_yaw(frame))
    for side in SIDES:
        target = ankle_target(side, frame)
        extra = shift[side] if is_planted(side, frame) else 0.0
        G4.leg_seat(arm, pose, side,
                    (target[0], target[1], target[2] + extra),
                    knee_dir(side, frame), ref=leg_ref)
    for side in SIDES:
        name = "foot." + side
        pose[name] = JS._unwrap_xyz(
            JS._PREV_EULER.get(name),
            keep_foot(arm, side, root_yaw(frame)))

    arm_ref = seat_ref(ARM_BONES, body_yaw(frame))
    for side in SIDES:
        clamp, dist_mm, limit_mm = G4.arm_seat(
            arm, pose, side, hand_target(side, frame), elbow_dir(side, frame),
            ref=arm_ref)
        info = ARM_CLAMP.setdefault(
            side, {"any": False, "worst_frame": None, "worst_ratio": 0.0,
                   "worst_over_mm": 0.0, "limit_mm": round(limit_mm, 3)})
        ratio = dist_mm / limit_mm
        if ratio > info["worst_ratio"]:
            info["worst_ratio"] = round(ratio, 5)
            info["worst_frame"] = frame
        if clamp:
            info["any"] = True
            info["worst_over_mm"] = round(max(info["worst_over_mm"],
                                              dist_mm - limit_mm), 3)

    if os.environ.get("C11_ARM_DIAG") == "1" and frame in (
            _env_i("C11_ARM_DIAG_A", 0), COIL_END, REL_END, 30, 38, HIT):
        for side in SIDES:
            shoulder = Vector(A.bone_world(arm, "upperarm." + side, "head"))
            want = Vector(hand_target(side, frame))
            got = Vector(A.bone_world(arm, "hand." + side, "tail"))
            print("C11_ARM_DIAG " + json.dumps({
                "f": frame, "s": side,
                "d_mm": round((want - shoulder).length * 1000.0, 2),
                "fold_lo_mm": round(abs(ARM_LEN[side]["upper"]
                                        - ARM_LEN[side]["forearm"]
                                        - ARM_LEN[side]["hand"]) * 1000.0, 2),
                "err_mm": round((got - want).length * 1000.0, 3),
                "hand_euler": [round(math.degrees(v), 3) for v in
                               arm.pose.bones["hand." + side].rotation_euler],
            }))

    # 起手接合（C10 第 5 号教训）：`arm_seat` 隐含"腕直"，而 Idle 戒备是**屈腕**的，
    # 第 1 帧会被掰直 ⟹ 单帧欧拉步长 24.558°（`hand.R`）。f1..EASE_END 把臂欧拉
    # 从 Idle 平滑接到逆解（f0 仍是逐位 Idle，f ≥ EASE_END 即纯逆解）。
    if frame < EASE_END:
        weight = RS.smooth(frame / float(EASE_END))
        for name in ARM_BONES:
            base = SEAM_EULER[name]
            got = JS._unwrap_xyz(base, pose[name])
            pose[name] = tuple(a + (b - a) * weight for a, b in zip(base, got))

    pose.update(A.FIST)
    for name, value in pose.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)
    return pose


def solve_pose(arm, frame, meshes=None):
    """逐帧贴地闭环：**承重脚**鞋底钉到 0 mm（`shift` 并进踝目标，C09 第 6 号）。

    ★ 摆动脚（离地）**不参与闭环** —— 它本来就该在空中，闭环会把"高抬腿"
    硬拽回地面。
    """
    shift = {side: 0.0 for side in SIDES}
    pose = build_pose(arm, frame, shift)
    if meshes is None:
        return pose
    for _step in range(6):
        bpy.context.view_layer.update()
        low = A.foot_lowest_by_side()
        error = {}
        for side in SIDES:
            if not is_planted(side, frame) or low[side] is None:
                continue
            error[side] = 0.0 - low[side][2]
        if not error or max(abs(v) for v in error.values()) < 1e-6:
            break
        for side, value in error.items():
            shift[side] += value
        pose = build_pose(arm, frame, shift)
    return pose


# =============================================================== 收招
# 收招段（f > PLANT）姿势 = 躯干/手臂走**全姿欧拉仿射**，腿**分层**：
#     pose(f) = A.blend(落地姿, 解卷绕后的 `Idle_01@0`(root yaw = 360°), q_of(f))
#     pose(f).腿 = ik_腿 + (仿射腿 − ik_腿) × leg_affine_weight(f)
#
# 为什么用仿射而不是全程重解姿态（C08 第 4 件 / C09 第 5 件）：幅度大时
# 「单段仿射 + 拉长帧数」比换插值路径稳；且末帧能**逐位**落回 Idle。
# root 的 yaw 两端都是 360° ⟹ 不需要额外解卷绕，不会踩翻转分支。
#
# ★ 但腿**不能**跟着仿射走到尾（第 2 轮门禁暴露的真问题）：
#   欧拉空间里的线性插值**不保持踝的高度** —— 误差是二阶的，两端 0、中点最大。
#   实测纯仿射：左鞋在 f68 被压到 **−3.80 mm**（`ground_contact_ok` 只给 −2）、
#   `PLANT..TOTAL` 左踝漂 **4.753 mm**（`plant_ok` 只给 3）。而 q 的中点
#   （f≈69）与观测到的谷底（f68）**逐帧吻合** ⟹ 归因确凿。
#   而**纯 IK** 又不行：`leg_seat` 的膝位构造与 Idle 的欧拉不是同一支解，
#   末帧会和 Idle 差 ~10 mm（`end_pose_ok` 只给 0.5 mm）。
#   ⟹ 分层：**前段纯 IK 钉地，后段淡入仿射保证末帧逐位 = Idle**。
LEG_IK_UNTIL = _env_i("C11_LEGIK", 66)      # f ≤ 此值：腿纯 IK（钉地）


def leg_affine_weight(frame):
    """收招段腿的**欧拉仿射权重**：0 = 纯 IK（贴地），1 = 纯仿射（末帧 = Idle）。"""
    if frame <= LEG_IK_UNTIL:
        return 0.0
    if frame >= SETTLE:
        return 1.0
    return RS.smooth((frame - LEG_IK_UNTIL) / float(SETTLE - LEG_IK_UNTIL))


def recover_pose(arm, frame, pose_a, pose_b):
    """收招段单帧姿态：躯干/臂走仿射，腿按 `leg_affine_weight` 分层。"""
    pose = A.blend(pose_a, pose_b, q_of(frame))
    weight = leg_affine_weight(frame)
    if weight < 0.999:
        shift = {side: 0.0 for side in SIDES}
        solved = None
        for _step in range(8):
            trial = dict(pose)
            A.apply_pose(arm, trial)
            leg_ref = seat_ref(LEG_BONES, root_yaw(frame))
            for side in SIDES:
                target = ANKLE_0[side]
                G4.leg_seat(arm, trial, side,
                            (target[0], target[1], target[2] + shift[side]),
                            knee_dir(side, frame), ref=leg_ref)
            # ★ **必须先把鞋钉住再量鞋底**：`apply_pose` 会把 `foot.*` 归零，
            #   而归零（rest）朝向与 `keep_foot` 钉住的朝向不是一回事 ——
            #   首版漏了这两行，闭环就在"rest 朝向的鞋底"上收敛，真鞋底被顶到
            #   **+6.66 mm 悬空**（`ground_contact_ok` 看不到：右鞋在 0 附近）。
            for side in SIDES:
                name = "foot." + side
                trial[name] = JS._unwrap_xyz(
                    JS._PREV_EULER.get(name),
                    keep_foot(arm, side, root_yaw(frame)))
            solved = trial
            bpy.context.view_layer.update()
            low = A.foot_lowest_by_side()
            error = {s: 0.0 - low[s][2] for s in SIDES if low[s] is not None}
            if max(abs(v) for v in error.values()) < 1e-6:
                break
            for side, value in error.items():
                shift[side] += value
        mixed = {}
        for side in SIDES:
            for bone in ("thigh." + side, "shin." + side):
                affine = pose[bone]
                # 先把 IK 解卷绕到仿射值最近的分支，避免 2π 跳支（混出闪帧）
                ik = JS._unwrap_xyz(affine, solved[bone])
                mixed[bone] = tuple(i + (a - i) * weight
                                    for i, a in zip(ik, affine))
        pose.update(mixed)
    A.apply_pose(arm, pose)
    for side in SIDES:
        name = "foot." + side
        pose[name] = JS._unwrap_xyz(JS._PREV_EULER.get(name),
                                    keep_foot(arm, side, root_yaw(frame)))
    pose.update(A.FIST)
    for name, value in pose.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)
    return pose


# =============================================================== 逐帧实测
def frame_series(arm, action, total):
    scene = bpy.context.scene
    previous = arm.animation_data.action if arm.animation_data else None
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    rows = []
    for frame in range(0, total + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        row = {"frame": frame}
        for name in ("pelvis", "thigh.L", "thigh.R", "upperarm.R", "upperarm.L",
                     "foot.L", "foot.R", "chest", "head"):
            row[name] = tuple(A.bone_world(arm, name, "head"))
        row["hip_L"] = tuple(A.bone_world(arm, "thigh.L", "head"))
        row["hip_R"] = tuple(A.bone_world(arm, "thigh.R", "head"))
        row["fist"] = tuple(A.bone_world(arm, "hand." + PUNCH_SIDE, "tail"))
        row["shoulder"] = tuple(A.bone_world(arm, "upperarm." + PUNCH_SIDE,
                                            "head"))
        row["pivot"] = vertex_world(PIVOT_KEY)
        low = A.foot_lowest_by_side()
        for side in SIDES:
            row["sole_" + side] = None if low[side] is None else low[side][2]
        for side in SIDES:
            row["ankle_" + side] = tuple(A.bone_world(arm, "foot." + side,
                                                      "head"))
            hip = Vector(row["thigh." + side])
            row["reach_" + side] = (
                Vector(row["ankle_" + side]) - hip).length
        rows.append(row)
    if previous is not None:
        arm.animation_data.action = previous
    return rows


def speeds(rows, key):
    """逐帧世界速度（mm/s）：|p(f) − p(f−1)| × FPS。"""
    out = []
    for index in range(1, len(rows)):
        d = (Vector(rows[index][key]) - Vector(rows[index - 1][key])).length
        out.append(d * A.FPS * 1000.0)
    return out


# =============================================================== 专属门禁
def skill03_assertions(arm, action, samples, rows, yaw):
    res = {}
    first, last = samples[0], samples[-1]

    # ---- 0) 首帧：逐位 = `Idle_01@0`
    delta0 = 0.0
    for name, value in SEAM_EULER.items():
        got = first["euler"].get(name, (0.0, 0.0, 0.0))
        delta0 = max(delta0, max(abs(a - b) for a, b in zip(got, value)))
    res["skill_start_delta_deg"] = round(delta0, 8)
    res["skill_start_ok"] = delta0 <= SEAM_TOL

    # ---- 1) 反相蓄力 + 整圈单向自转
    wind = yaw[COIL_END] - yaw[0]
    res["windup_turn_deg"] = round(wind, 3)
    wind_steps = [yaw[i] - yaw[i - 1] for i in range(1, COIL_END + 1)]
    res["windup_monotone_ok"] = all(s <= 1e-6 for s in wind_steps)
    res["windup_turn_ok"] = (COIL_MIN_DEG <= abs(wind) <= COIL_MAX_DEG
                             and res["windup_monotone_ok"])

    spin = yaw[HIT] - yaw[COIL_HOLD_END]
    spin_steps = [yaw[i] - yaw[i - 1] for i in range(COIL_HOLD_END + 1, HIT + 1)]
    res["spin_turn_deg"] = round(spin, 3)
    res["spin_monotone_ok"] = all(s >= -1e-6 for s in spin_steps)
    res["spin_turn_ok"] = (SPIN_MIN_DEG <= spin <= SPIN_MAX_DEG
                           and res["spin_monotone_ok"])
    res["spin_end_yaw_deg"] = round(yaw[-1] % 360.0, 4)
    res["spin_end_yaw_ok"] = abs(yaw[-1] - SPIN_TURN) <= 1.0

    # ---- 2) 角速度剖面：峰值在命中前 1/3、命中帧骤降
    window = spin_steps
    peak = max(window) if window else 0.0
    # 取**最后一个** ≥99% 峰值的步（不是 `index()` 的第一个）—— 消除并列取谁
    # 的歧义，且方向是**更严**：首版 `window.index(peak)` 在 1.58/1.58 并列时
    # 取到较早那一步，会把"峰值帧"报早一帧。
    plateau = [COIL_HOLD_END + 1 + j for j, value in enumerate(window)
               if peak > 1e-9 and value >= 0.99 * peak]
    peak_frame = plateau[-1] if plateau else None
    allow = REL_END + (HIT - REL_END) * SPEED_PEAK_FRAC
    res["spin_peak_step_deg"] = round(peak, 3)
    res["spin_peak_frame"] = peak_frame
    res["spin_peak_plateau"] = plateau
    res["spin_peak_allow_frame"] = round(allow, 2)
    res["spin_peak_early_ok"] = bool(peak_frame is not None
                                     and peak_frame <= allow)
    hit_rate = spin_steps[-1] if spin_steps else 0.0
    res["spin_hit_step_deg"] = round(hit_rate, 3)
    res["spin_hit_ratio"] = round(hit_rate / peak, 4) if peak > 1e-9 else 0.0
    res["spin_decel_ok"] = hit_rate <= SPEED_DROP_RATIO * peak
    res["spin_accel_ok"] = window[0] < peak
    res["spin_speed_ok"] = bool(res["spin_peak_early_ok"]
                                and res["spin_decel_ok"]
                                and res["spin_accel_ok"])

    # ---- 3) 支撑脚枢轴顶点**水平**漂移
    drift = 0.0
    drift_at = None
    for frame in range(COIL_HOLD_END, HIT + 1):
        point = rows[frame]["pivot"]
        if point is None or PIVOT_REF is None:
            continue
        gap = math.hypot(point[0] - PIVOT_REF[0], point[1] - PIVOT_REF[1])
        if gap > drift:
            drift = gap
            drift_at = frame
    res["foot_pivot_drift_mm"] = round(drift * 1000.0, 3)
    res["foot_pivot_drift_at"] = drift_at
    res["foot_pivot_ok"] = drift * 1000.0 <= PIVOT_MAX_MM

    # ---- 4) 承重脚不滑（分段：转体前 / 转体后）
    def slide(side, f0, f1):
        pts = [Vector(rows[f]["ankle_" + side]) for f in range(f0, f1 + 1)]
        return max((p - pts[0]).length for p in pts) * 1000.0

    res["plant_L_pre_mm"] = round(slide("L", 0, REL_END), 3)
    res["plant_R_pre_mm"] = round(slide("R", 0, REL_END), 3)
    res["plant_L_post_mm"] = round(slide("L", PLANT, TOTAL), 3)
    res["plant_R_post_mm"] = round(slide("R", PLANT, TOTAL), 3)
    res["plant_ok"] = (max(res["plant_L_pre_mm"], res["plant_R_pre_mm"],
                           res["plant_L_post_mm"], res["plant_R_post_mm"])
                       <= PLANT_MAX_MM)

    # ---- 5) 动力链时序：髋 ≤ 肩 ≤ 拳，各 ≥ 800 mm/s
    s_hip = speeds(rows, "hip_" + PUNCH_SIDE)
    s_shoulder = speeds(rows, "shoulder")
    s_fist = speeds(rows, "fist")
    pk_hip = max(s_hip) if s_hip else 0.0
    pk_shoulder = max(s_shoulder) if s_shoulder else 0.0
    pk_fist = max(s_fist) if s_fist else 0.0
    f_hip = s_hip.index(pk_hip) + 1 if s_hip else 0
    f_shoulder = s_shoulder.index(pk_shoulder) + 1 if s_shoulder else 0
    f_fist = s_fist.index(pk_fist) + 1 if s_fist else 0
    res["chain_peak_mmps"] = {"hip": round(pk_hip, 1),
                              "shoulder": round(pk_shoulder, 1),
                              "fist": round(pk_fist, 1)}
    res["chain_peak_frame"] = {"hip": f_hip, "shoulder": f_shoulder,
                               "fist": f_fist}
    # 出拳窗口内的峰值（`speeds` 的下标 i 对应帧 i+1）
    win = [index for index in range(len(s_hip))
           if REL_END <= index + 1 <= HOLD_END]

    def peak_in(series):
        best = max(win, key=lambda i: series[i])
        return series[best], best + 1

    w_hip, wf_hip = peak_in(s_hip)
    w_shoulder, wf_shoulder = peak_in(s_shoulder)
    w_fist, wf_fist = peak_in(s_fist)
    res["chain_window_peak_mmps"] = {"hip": round(w_hip, 1),
                                     "shoulder": round(w_shoulder, 1),
                                     "fist": round(w_fist, 1)}
    res["chain_window_frame"] = {"hip": wf_hip, "shoulder": wf_shoulder,
                                 "fist": wf_fist}
    res["chain_order_ok"] = f_hip <= f_shoulder <= f_fist
    res["chain_window_order_ok"] = wf_hip <= wf_shoulder <= wf_fist
    res["chain_magnitude_ok"] = min(pk_hip, pk_shoulder, pk_fist) >= CHAIN_MIN_MMPS
    res["chain_in_window_ok"] = (REL_END <= f_hip and f_fist <= HOLD_END)
    res["punch_chain_ok"] = bool(res["chain_order_ok"]
                                 and res["chain_magnitude_ok"]
                                 and res["chain_in_window_ok"])

    # ---- 6) 命中帧：拳套**网格面**最前，领先护身手 ≥ 80 mm
    scene = bpy.context.scene
    previous = arm.animation_data.action if arm.animation_data else None
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    scene.frame_set(HIT)
    bpy.context.view_layer.update()
    front = {s: mesh_frontmost(MESH_GLOVE[s]) for s in SIDES}
    if previous is not None:
        arm.animation_data.action = previous
    lead = (front[GUARD_SIDE][1] - front[PUNCH_SIDE][1]) * 1000.0 \
        if all(front.values()) else 0.0
    res["hit_glove_front_mm"] = {s: round(front[s][1] * 1000.0, 2)
                                 for s in SIDES if front[s]}
    res["punch_front_lead_mm"] = round(lead, 2)
    res["punch_frontmost_ok"] = bool(all(front.values())
                                     and lead >= FRONT_LEAD_MM)

    # ---- 7) Root Motion：水平 ≤ 700 mm、竖直跨度 ∈[0,150] mm
    pelvis = [Vector(row["pelvis"]) for row in rows]
    span_h = math.hypot(max(p.x for p in pelvis) - min(p.x for p in pelvis),
                        max(p.y for p in pelvis) - min(p.y for p in pelvis))
    span_z = (max(p.z for p in pelvis) - min(p.z for p in pelvis)) * 1000.0
    res["root_span_h_mm"] = round(span_h * 1000.0, 2)
    res["root_span_z_mm"] = round(span_z, 2)
    res["root_motion_ok"] = (span_h * 1000.0 <= ROOT_H_MAX_MM
                             and 0.0 <= span_z <= ROOT_Z_MAX_MM)

    # ---- 8) 前摇时长 + 摆动脚可见抬腿
    res["windup_frames"] = COIL_END - EASE_END
    res["windup_time_ok"] = WIND_MIN_F <= res["windup_frames"] <= WIND_MAX_F
    lift = max((rows[f]["sole_" + SWING_SIDE] or 0.0)
               for f in range(REL_END, PLANT + 1))
    res["swing_lift_mm"] = round(lift * 1000.0, 2)
    res["swing_lift_ok"] = lift * 1000.0 >= SWING_LIFT_MIN_MM

    # ---- 9) 腿可达比（全程不得截断）
    worst = 0.0
    worst_at = None
    limit = A.L_THIGH + A.L_SHIN
    for row in rows:
        for side in SIDES:
            ratio = row["reach_" + side] / limit
            if ratio > worst:
                worst = ratio
                worst_at = [row["frame"], side]
    res["leg_reach_worst_ratio"] = round(worst, 5)
    res["leg_reach_worst_at"] = worst_at
    res["leg_reach_ok"] = worst <= REACH_MAX_RATIO

    # ---- 10) 臂逆解不得截断
    res["arm_clamp"] = {side: dict(info) for side, info in ARM_CLAMP.items()}
    res["arm_reach_ok"] = all(not info["any"] for info in ARM_CLAMP.values())

    # ---- 11) 命停：HIT..HOLD_END 逐位冻结
    frozen = True
    worst_hold = 0.0
    base = samples[HIT]["euler"]
    for frame in range(HIT + 1, HOLD_END + 1):
        cur = samples[frame]["euler"]
        for name in set(base) | set(cur):
            step = max(abs(a - b) for a, b in zip(
                base.get(name, (0.0,) * 3), cur.get(name, (0.0,) * 3)))
            worst_hold = max(worst_hold, step)
            if step > 1e-9:
                frozen = False
    res["hitstop_frames"] = FIRE_HOLD
    res["hitstop_worst_step_deg"] = round(worst_hold, 8)
    res["hitstop_ok"] = bool(frozen and 2 <= FIRE_HOLD <= 4)

    # ---- 12) 末帧落回 `Idle_01@0`（world 位，root 已转 360° ≡ 0）
    res["end_pose_delta_mm"] = 0.0
    for key in A.PROBE_KEYS:
        if key in first and key in last:
            res["end_pose_delta_mm"] = max(
                res["end_pose_delta_mm"],
                (Vector(first[key]) - Vector(last[key])).length * 1000.0)
    res["end_pose_delta_mm"] = round(res["end_pose_delta_mm"], 4)
    res["end_pose_ok"] = res["end_pose_delta_mm"] <= END_POSE_TOL_MM
    return res


# =============================================================== 主流程
def main():
    global SEAM_POSE, SEAM_EULER, SEAM_360, Z_SEAM, ANKLE_0, PIVOT0, PIVOT_KEY
    global FOOT0, IDLE_HAND, IDLE_KNEE_DIR, IDLE_BASIS, IDLE_DIR, IDLE_ELBOW
    global ARM_LEN, ARM_REF, E0, E_END_UNW, PELVIS_RY_BASE, PIVOT_REF

    for store in (SEAM_POSE, SEAM_EULER, SEAM_360, ANKLE_0, FOOT0, IDLE_HAND,
                  IDLE_KNEE_DIR, IDLE_BASIS, IDLE_DIR, IDLE_ELBOW, ARM_LEN,
                  ARM_REF, E0, E_END_UNW, ARM_CLAMP, LOG):
        store.clear()

    arm, meshes = A.open_animation_project()
    A.setup_scene()
    if I1.NAME not in bpy.data.actions:
        print("C11_BOOTSTRAP 缺 %s，先补跑" % I1.NAME)
        I1.main()
        arm, meshes = A.open_animation_project()
        A.setup_scene()

    for side in SIDES:
        ARM_LEN[side] = {
            "upper": arm.pose.bones["upperarm." + side].length,
            "forearm": arm.pose.bones["forearm." + side].length,
            "hand": arm.pose.bones["hand." + side].length}

    # `end_pose_ok` 要按大腿/小腿也核一遍（转体全靠 root，腿骨是最可能留残余的）
    for extra in ("thigh.L", "thigh.R", "shin.L", "shin.R"):
        if extra not in A.PROBE_BONES:
            A.PROBE_BONES = tuple(A.PROBE_BONES) + (extra,)
    A.PROBE_KEYS = A.PROBE_BONES + tuple(n + ".tail" for n in A.PROBE_TAILS)

    # ---- 首帧真值：`Idle_01@0`
    scene = bpy.context.scene
    src = bpy.data.actions[I1.NAME]
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = src
    A._bind_slot(arm, src)
    scene.frame_set(0)
    bpy.context.view_layer.update()
    SEAM_EULER = {b.name: tuple(math.degrees(v) for v in b.rotation_euler)
                  for b in arm.pose.bones}
    SEAM_POSE = dict(SEAM_EULER)
    SEAM_POSE["@loc"] = {"pelvis": tuple(arm.pose.bones["pelvis"].location)}
    SEAM_POSE.update(A.FIST)
    Z_SEAM = A.bone_world(arm, "pelvis", "head").z
    ANKLE_0 = {s: Vector(A.bone_world(arm, "foot." + s, "head")) for s in SIDES}
    FOOT0 = {s: arm.pose.bones["foot." + s].matrix.to_3x3().copy()
             for s in SIDES}
    for side in SIDES:
        IDLE_HAND[side] = tuple(A.bone_world(arm, "hand." + side, "tail"))
        shoulder = Vector(A.bone_world(arm, "upperarm." + side, "head"))
        elbow = Vector(A.bone_world(arm, "upperarm." + side, "tail"))
        IDLE_ELBOW[side] = tuple((elbow - shoulder).normalized())
    PELVIS_RY_BASE = SEAM_EULER["pelvis"][1]

    name, index, world = pivot_vertex(PIVOT_SIDE)
    PIVOT_KEY = (name, index)
    PIVOT0 = world
    PIVOT_REF = world

    # 末姿 = `Idle_01@0`，但 root 的 yaw 停在 360°（≡ 0，正面朝前）
    SEAM_360 = dict(SEAM_EULER)
    SEAM_360["root"] = (SEAM_EULER["root"][0], SPIN_TURN,
                        SEAM_EULER["root"][2])
    SEAM_360["@loc"] = dict(SEAM_POSE["@loc"])
    SEAM_360.update(A.FIST)

    # ---- Idle 骨基座（逆解基准）
    idle = I1.idle_pose(arm, 0.0)
    A.apply_pose(arm, idle)
    bpy.context.view_layer.update()
    for side in SIDES:
        hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
        knee = Vector(A.bone_world(arm, "thigh." + side, "tail"))
        IDLE_KNEE_DIR[side] = (knee - hip).normalized()
        for bone in ("thigh." + side, "shin." + side):
            IDLE_BASIS[bone] = arm.pose.bones[bone].matrix.to_3x3().copy()
            IDLE_DIR[bone] = A.bone_direction(arm, bone)
    for bone in ARM_BONES:
        IDLE_BASIS[bone] = arm.pose.bones[bone].matrix.to_3x3().copy()
        IDLE_DIR[bone] = A.bone_direction(arm, bone)
    for table, source in ((G4.IDLE_BASIS, IDLE_BASIS), (G4.IDLE_DIR, IDLE_DIR),
                         (G4.IDLE_KNEE_DIR, IDLE_KNEE_DIR)):
        table.clear()
        table.update(source)
    G4.ARM_LEN.clear()
    for side in SIDES:
        G4.ARM_LEN[side] = dict(ARM_LEN[side])

    A.report("C11_LAYOUT", {
        "total_frames": TOTAL, "seconds": round(TOTAL / float(A.FPS), 3),
        "ease_end": EASE_END, "coil_end": COIL_END,
        "coil_hold_end": COIL_HOLD_END, "rel_end": REL_END,
        "hit": HIT, "hold_end": HOLD_END, "plant": PLANT,
        "settle": SETTLE, "cancel": CANCEL,
        "spin_steps": SPIN_STEPS, "spin_turn_deg": SPIN_TURN,
        "coil_deg": COIL_DEG,
        "pelvis_world_turn_deg": round(SPIN_TURN - COIL_DEG, 3),
        "pivot_key": [PIVOT_KEY[0], PIVOT_KEY[1]],
        "pivot_world_mm": [round(v * 1000.0, 3) for v in PIVOT0],
        "pelvis_z0_mm": round(Z_SEAM * 1000.0, 3),
        "ankle0_mm": {s: [round(v * 1000.0, 2) for v in ANKLE_0[s]]
                      for s in SIDES},
        "idle_hand_mm": {s: [round(v * 1000.0, 2) for v in IDLE_HAND[s]]
                         for s in SIDES},
        "note": ("旋转重拳：%d 帧反相拧身（骨盆局部 yaw %d° 而头只看 −16°）"
                 "→ 反相停顿 %d 帧 → %d 帧髋部释放 → %d 步转体出拳"
                 "（root yaw 0→%d°，峰值角速度在第 %d 帧）→ 命停 %d 帧"
                 "→ 收招回「战斗待机」。骨盆世界 yaw 累计 %d° 全程单向。"
                 % (COIL_END, int(COIL_DEG), COIL_HOLD, REL_END - COIL_HOLD_END,
                    SPIN_STEPS, int(SPIN_TURN), REL_END + 5, FIRE_HOLD,
                    int(SPIN_TURN - COIL_DEG))),
    })

    # ---- 建片段
    JS._PREV_EULER.clear()
    A.apply_pose(arm, SEAM_POSE)
    bpy.context.view_layer.update()
    for name, value in SEAM_POSE.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)

    keyframes = [(0, SEAM_POSE)]
    solved_hold = None
    for frame in range(1, PLANT + 1):
        pose = solve_pose(arm, frame, meshes)
        keyframes.append((frame, pose))
        if frame == PLANT:
            solved_hold = dict(pose)

    # 命停冻结：HIT..HOLD_END 逐位重复命中帧（§0.1 的"2~4 帧完全停顿"）
    hit_pose = keyframes[HIT][1]
    for frame in range(HIT + 1, HOLD_END + 1):
        keyframes[frame] = (frame, dict(hit_pose))

    # 收招仿射：把 SEAM_360 解卷绕到离落定姿最近的分支，再逐通道滑过去
    E0.clear()
    E0.update({k: tuple(v) for k, v in solved_hold.items()
               if not k.startswith("@")})
    E_END_UNW.clear()
    for bone, value in SEAM_360.items():
        if bone.startswith("@"):
            continue
        E_END_UNW[bone] = JS._unwrap_xyz(E0.get(bone, (0.0, 0.0, 0.0)), value)
    end_pose = dict(E_END_UNW)
    end_pose["@loc"] = dict(SEAM_360["@loc"])

    A.report("C11_BLEND", {
        "delta_deg": {bone: round(max(abs(a - b) for a, b in
                                      zip(E0[bone], E_END_UNW[bone])), 3)
                      for bone in sorted(E0)},
    })

    for frame in range(PLANT + 1, TOTAL + 1):
        keyframes.append((frame, recover_pose(arm, frame, solved_hold, end_pose)))

    meta = {
        "anim_id": NAME,
        "loop": False,
        "category": "连招与特殊技",
        "note": ("旋转重拳：反相拧身 → 髋部释放 → %d° 单向转体出拳 → 命停 %d 帧"
                 "→ 收招。骨盆世界 yaw 累计 %d°。" % (int(SPIN_TURN), FIRE_HOLD,
                                                      int(SPIN_TURN - COIL_DEG))),
        "antic_frame": COIL_END,
        "hit_frame": HIT,
        "cancel_frame": CANCEL,
        "hitstop_frames": FIRE_HOLD,
        "root_motion_m": [0.0, 0.0],
        "inherit_from": None,
        "segments": {"ease": [0, EASE_END], "coil": [EASE_END, COIL_END],
                     "coil_hold": [COIL_END, COIL_HOLD_END],
                     "release": [COIL_HOLD_END, REL_END],
                     "spin": [REL_END, HIT], "hitstop": [HIT, HOLD_END],
                     "recover": [HOLD_END, TOTAL]},
        "spin_axis": "world +Z (root.rotation_euler.y)",
        "spin_turn_deg": SPIN_TURN,
        "pelvis_world_turn_deg": SPIN_TURN - COIL_DEG,
        "pivot_foot": PIVOT_SIDE,
        "pivot_vertex": [PIVOT_KEY[0], PIVOT_KEY[1]],
        "pivot_world_m": [round(v, 6) for v in PIVOT0],
        "punch_side": PUNCH_SIDE,
        "end_pose_deg": {k: [round(v, 4) for v in val]
                         for k, val in sorted(E_END_UNW.items())},
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.add_markers(action, {
        "ENTER": 0, "EASE_END": EASE_END, "COIL": COIL_END,
        "COIL_HOLD_END": COIL_HOLD_END, "RELEASE": REL_END, "HIT": HIT,
        "HOLD_END": HOLD_END, "PLANT": PLANT, "SETTLE": SETTLE,
        "CANCEL": CANCEL, "END": TOTAL,
    })

    samples = A.sample_animation(arm, action, 0, TOTAL, meshes)
    rows = frame_series(arm, action, TOTAL)
    yaw = pelvis_yaw_unwrapped(rows)

    if os.environ.get("C11_YAW_DIAG") == "1":
        for row in rows:
            frame = row["frame"]
            print("C11_YAW_DIAG " + json.dumps({
                "f": frame, "yaw": round(yaw[frame], 3),
                "root": round(root_yaw(frame), 3),
                "pelvis_local": round(_pelvis_ry(frame), 3),
                "step": (None if frame == 0
                         else round(yaw[frame] - yaw[frame - 1], 3))}))
    if os.environ.get("C11_TRACE") == "1":
        limit_mm = (A.L_THIGH + A.L_SHIN) * 1000.0
        for row in rows:
            print("C11_TRACE " + json.dumps({
                "f": row["frame"],
                "pelvis": [round(v * 1000.0, 2) for v in row["pelvis"]],
                "fist": [round(v * 1000.0, 2) for v in row["fist"]],
                "yaw": round(yaw[row["frame"]], 2),
                "sole_L": (None if row["sole_L"] is None
                           else round(row["sole_L"] * 1000.0, 2)),
                "sole_R": (None if row["sole_R"] is None
                           else round(row["sole_R"] * 1000.0, 2)),
                "reach_L": round(row["reach_L"] * 1000.0 / limit_mm, 4),
                "reach_R": round(row["reach_R"] * 1000.0 / limit_mm, 4),
                "pivot": [round(v * 1000.0, 3) for v in row["pivot"]],
            }))

    if os.environ.get("C11_SPEED_DIAG") == "1":
        for part, key in (("hip", "hip_" + PUNCH_SIDE), ("shoulder", "shoulder"),
                          ("fist", "fist"), ("pelvis", "pelvis")):
            series = speeds(rows, key)
            order = sorted(range(len(series)), key=lambda i: -series[i])[:8]
            print("C11_SPEED_DIAG " + json.dumps({
                "part": part,
                "peak_mmps": round(max(series), 1),
                "peak_frame": series.index(max(series)) + 1,
                "top": [[i + 1, round(series[i], 1)] for i in order],
                "window": [[i + 1, round(series[i], 1)]
                           for i in range(REL_END - 6, min(len(series),
                                                           HOLD_END + 4))]}))
    if os.environ.get("C11_PLANT_DIAG") == "1":
        base = {s: Vector(rows[PLANT]["ankle_" + s]) for s in SIDES}
        for frame in range(PLANT, TOTAL + 1):
            row = rows[frame]
            print("C11_PLANT_DIAG " + json.dumps({
                "f": frame,
                "dL": round((Vector(row["ankle_L"]) - base["L"]).length
                            * 1000.0, 3),
                "dR": round((Vector(row["ankle_R"]) - base["R"]).length
                            * 1000.0, 3),
                "zL": round(row["ankle_L"][2] * 1000.0, 3),
                "zR": round(row["ankle_R"][2] * 1000.0, 3),
                "soleL": round(row["sole_L"] * 1000.0, 3),
                "soleR": round(row["sole_R"] * 1000.0, 3)}))
    report = A.run_common_assertions(samples, meta, foot_probe=())
    report.update(skill03_assertions(arm, action, samples, rows, yaw))
    report["low_bad_frames"] = {
        str(s["frame"]): [round(s["low"]["L"] * 1000.0, 2),
                          round(s["low"]["R"] * 1000.0, 2)]
        for s in samples
        if min(s["low"]["L"], s["low"]["R"]) * 1000.0 < -2.0}
    report["meta"] = meta
    report["failed"] = sorted(k for k, v in report.items()
                              if k.endswith("_ok") and v is not True)
    report["non_ok_bools"] = sorted(
        k for k, v in report.items()
        if isinstance(v, bool) and not k.endswith("_ok") and v is not True)
    A.report("C11_REPORT", report)

    if not SKIP_RENDER:
        frames = [0, COIL_END, COIL_HOLD_END, 33, 40, HIT, HOLD_END, 70, TOTAL]
        ratio = 780.0 / 1100.0
        keys = [k for k in samples[0]
                if k != "frame" and isinstance(samples[0][k], tuple)]
        pts = [Vector(s[k]) for s in samples for k in keys if k in s]
        xs = [p.x for p in pts]
        ys = [p.y for p in pts]
        zs = [p.z for p in pts]
        center = (0.5 * (min(xs) + max(xs)), 0.5 * (min(ys) + max(ys)),
                  0.5 * (min(zs) + max(zs)))
        scale = max(2.10, (max(zs) - min(zs)) * 1.15,
                    (max(xs) - min(xs)) * 1.15 / ratio,
                    (max(ys) - min(ys)) * 1.15 / ratio)

        def reframe(view):
            name, location, target, _scale, res = view
            direction = (Vector(location) - Vector(target)).normalized()
            new_target = Vector(center)
            new_location = new_target + direction * 4.6
            return (name, tuple(new_location), tuple(new_target), scale, res)

        A.report("C11_CAMERA", {
            "bbox_min": [round(min(xs), 4), round(min(ys), 4),
                         round(min(zs), 4)],
            "bbox_max": [round(max(xs), 4), round(max(ys), 4),
                         round(max(zs), 4)],
            "center": [round(v, 4) for v in center],
            "ortho_scale": round(scale, 4),
        })
        for base in (A.VIEW_SIDE, A.VIEW_FRONT, A.VIEW_3Q):
            A.render_pose_sheet(arm, action, frames, "skill03",
                                views=(reframe(base),))
    if not SKIP_RENDER:
        A.save_project()
        A.export_glb(arm)
    print("C11_DONE failed=%s" % report["failed"])
    print("C11_DONE non_ok_bools=%s" % report["non_ok_bools"])


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("C11_FAILURE " + traceback.format_exc())
