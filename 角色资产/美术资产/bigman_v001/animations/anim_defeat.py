"""anim_defeat —— E09 `Defeat` 战败（E 族第 9 支 / 全项目第 65 支）。

清单原文：「**跪地后倒下或重重倒地**」。

★★★ 本支与 E01~E08 的**结构性差别**（开工前想清楚，逐条落地）
    前 8 支（E01~E08）都是「循环 / 回位」动作，末帧逐位 = `Idle_01@0`。
    本支是 E 族**第一支带「落地终点」的动作**：
      · **起点 = `Idle_01@0` 逐位**（接缝入）；
      · **终点 = 一个稳定的伏地 Pose**（`dft_final_pose_ok`）—— 「首末同姿」这条
        从 A01 到 E08 一路沿用的接缝铁律在本支**第一次被打破**，改写成
        「起点同 Idle / 终点同「伏地」」，并在此**显式声明**。
    `meta["loop"] = False`（不是循环 ⟹ 通用 `loop_seamless` 报 None）。

★★★ 三段结构 + 两个「命中停顿」（清单 §6：2~4 帧完全停顿）
    f0 ──16──▶ 前摇（下沉、屈膝、重心前移，启动略慢）
    f16 ──28──▶ **跪落**（双膝触地）⟹ `[28, 32]` **4 帧完全冻结**（膝触地顿感）
    f32 ──46──▶ 跪姿停留（上身失力、逐帧只动躯干 —— **骨盆不动 ⟹ 脚不动**）
    f46 ──66──▶ **前扑**（躯干砸向地面，速度单调加速，命中极重）
    f66 ──70──▶ **触地** ⟹ `[66, 70]` **4 帧完全冻结**（砸地顿感）
    f70 ──120─▶ 伏地**呼吸**（2 周期；末帧呼吸归零 ⟹ 逐位 = 伏地终点）

★★★ 四处**实测**（`probe_e09_baseline.py` / `_scan_e09_terminal*.py`，不是公式推的）
    ① 跪姿膝高一（`shin.*` head）≈ **膝网格半径 100.3 mm** ⟹ 骨盆世界降 **392 mm**
       （`hip_z = 508`）时膝**恰好**触地；`shin_rx = 90 − 0 − pelvis_rx(6) = 84`
       时小腿**水平**贴地（头两轮的 `90/96` 都会把踝抬起来）。
    ② 踝 `foot_rx = 28` ⟹ 鞋底 ≈ 0（跪姿脚背朝下、脚在膝后）。
    ③ ★★★ **`Knockdown_F@20` 不能当本支终点**：实测它 `Trouser_R` **陷地 61.54 mm**、
       `Trouser_L` −11.31 mm —— D14 的贴地判据只盯**鞋底**（`sole_clearance`），
       躯干/腿的陷地**从未被任何判据盯过**。直接复用 = 把未验收的缺陷带进 E09
       ⟹ 本支**自己立终点**，并新建**逐件贴地判据** `dft_body_ground_ok` 守住。
       （本支末帧**不是** `Knockdown_F@20`；那条"复用已验证资产"的设想被实测否决。）
    ④ 躺地终点的**贴地**组合由 `_scan_e09_terminal2` 扫出（见 §0 常量注释）。

★★★ 本支新增的**唯一一件基础设施**：`body_low_profile()` ——
    逐件（按网格对象）最低 z，供 `dft_body_ground_ok` / `dft_knee_contact_ok` /
    `dft_no_penetration_ok` 用。它是 D14 那处陷地能溜过去的原因所在，
    本支把它补上（**世界实体的守卫，不是骨架的**）。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python anim_defeat.py
    SKIP_RENDER=1     只跑门禁不渲图（迭代用）
    E09_TRACE=1       逐帧打印包络 / 呼吸 / 脚踝飘移 / 全身最低点

反向验证（`_rv_e09.sh`，十组，每组都必须**真的见红**）：
    E09_TP_SEAM_ZERO=1  ① 首帧改零位        ⟹ `seam_in_ok`
    E09_TP_NOKNEEL=1    ② 抽掉跪落主驱动    ⟹ `seam_in_ok`（实测唯一红）
    E09_TP_NOFALL=1     ③ 抽掉前扑主驱动    ⟹ `dft_prone_ok`（新增兜底判据）
    E09_TP_NOBREATH=1   ④ 不呼吸            ⟹ `dft_breath_ok`
    E09_TP_FOOTSWAY=1   ⑤ 跪姿 hold 内挪踝  ⟹ `dft_kneel_foot_lock_ok`
    E09_TP_KNEEFLOAT=1  ⑥ 跪姿整体抬 60 mm  ⟹ `dft_knee_contact_ok`
    E09_TP_NOHITSTOP=1  ⑦ 两个冻结窗抽掉    ⟹ `dft_hitstop_ok`
    E09_TP_SINK=1       ⑧ 末段整体下沉 60 mm ⟹ `dft_body_ground_ok` / `dft_no_penetration_ok`
    E09_TP_KNEEPLUNGE=1 ⑨ 前扑段抽掉解析反解 ⟹ `dft_knee_path_ok`（膝捅穿地面）
    E09_TP_LIMBJUMP=1   ⑩ f48 给踝目标注入 50 mm 尖峰 ⟹ `dft_limb_step_ok`
"""

import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A          # noqa: E402
import anim_idle_01 as IDLE   # noqa: E402
import probe_d01_guard as PD  # noqa: E402

NAME = "Defeat"
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"
SIDES = ("L", "R")
ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")
ARM_SET = set(ARM_BONES)
ARM_LEN_UP = 0.328
ARM_LEN_LO = 0.224 + 0.098
REACH_MAX_RATIO = 0.9995

# =============================================================== 时间轴
# ★ 帧预算：**沿用 E01 登记的 E 族上界 120 帧 / 2.0 s**（显式声明，不是悄悄超）。
TOTAL = 120
START = 0
END = 120
KNEE = 28          # 双膝触地帧
KNEE_HOLD = 32     # 膝触地定格末
KNEEL_TAIL = 46    # 跪姿停留末（开始前扑）
LAND = 66          # 伏地触地帧
LAND_HOLD = 70     # 触地定格末
BREATH_CYCLES = 2.0

# =============================================================== 姿态常量（实测）
# ★★★ 腿 = **踝目标 + 两骨 IK**（照抄 E02 `lock_feet` 的闭环结构）。
#     为什么不能继续用欧拉混合：`_dump_e09_prof.py` 实测 —— 欧拉线性混合下
#     `foot.rx` 跟着 `shin.rx` 一起转，脚**绕踝关节**旋转，于是鞋尖在过渡段
#     插进地面 **−211.26 mm**（f19/f20）。脚在真实人身上不会绕踝转，而是
#     **踩平贴地、整只鞋向后滑**：踝的世界 z 不变 ⟹ 鞋底自动停在原处。
#     本支改成：**踝目标轨迹（世界）→ IK 解 thigh/shin → 钉脚的世界俯仰**。
KNEEL_PELVIS_RX = 6.0
# 踝世界 y：跪姿需踝在膝后 411 mm（= 小腿水平）+ 髋 z = 512 ⟹ 大腿**恰好竖直**、
# 膝网格（半径 100.3）落在地面 ⟹ 骨盆世界降 388 mm。
KNEEL_ANKLE_Y = 0.411
KNEEL_DROP = 0.388                   # 世界下降（米）⟹ hip_z = 512
KNEEL_ABDUCT = 6.0

SAG_LEAN = 8.0                       # 跪姿停留段的躯干"失力前倾"增量（度）

TERM_PELVIS_RX = 68.0                # 伏地：躯干总俯仰 ≈ 68 + 6*3 = 86
TERM_REST_RX = 6.0
TERM_PELVIS_Y = -0.10                # 骨盆世界 y（米）
TERM_PELVIS_Z = 0.108                # 骨盆世界 z（米）⟹ 伏地时全身最低件 ≈ +4（带内）
TERM_ABDUCT = 8.0
TERM_NECK_RX = 24.0
TERM_HEAD_RX = 14.0
TERM_HEAD_RY = 40.0                  # 头侧转（避免脸直接压地）

# ---- 腿的踝目标（世界坐标；x 一律取站架值 ⟹ 外展角不变）--------------------
# ★★★ 实测重定（`_probe_e09_flat.py` 网格扫描）：伏地末端同时受**三条**判据夹逼
#     —— `dft_knee_path_ok`（膝 z ≥ 100.7）、`dft_body_ground_ok`（全身最低 ∈ [−6,8]）
#     与 `leg_reach_ok`（髋→踝距 ≤ 可达上限）。
#     关键几何事实：`leg_ik` 是**对称两骨链**，膝相对「髋→踝」连线的偏移量
#     h = sqrt(L² − (d/2)²) 只有在 d → L1+L2（全伸）时才趋于 0；d = 800 时 h 已达
#     94 mm ⟹ 想让膝停在 104.7，唯一办法是**把「髋→踝」连线整体抬高**
#     （= 踝目标 z 抬到 170 mm），而不是把踝往后推（那会顶到可达上限）。
#     实测定值（髋 z=108 / 踝 y=716 / 踝 z=170）：
#       · 膝 z = 110.01 mm（判据下限 100.7，余量 9.3）
#       · 全身最低件 = +4.07 mm（带 [−6, 8] 内）
#       · 可达比（按 `leg_reach_ok` 口径）= 0.99816
#     代价 = 踝抬到 170 mm ⟹ 小腿在后扑段微微翘起（「伏地后小腿翘」），
#     这是「膝贴地 + 无穿模 + 腿不全伸」三者同时成立时的**唯一解**，不是取巧。
PRONE_ANKLE_Y = 0.716                # 伏地：踝的后滑终点（闭环伺服只做残余修正）
PRONE_ANKLE_Z = 0.170                # 伏地：踝目标高度（抬线以抬膝，见上）
# ★★★ 实测（`_dump_e09_prof.py`）：**膝网格半径 104.6 mm**。
#     `thigh.head→shin.head` = **410.05 mm**、`shin.head→foot.head` = **411.9 mm**（刚性）。
#     跪姿处髋 z = 512、膝 z = 104.7 ⟹ 大腿**恰好全伸**（奇异位形）。
#     前扑段髋 z 从 512 掉到 100，若踝不跟着后滑，膝就会**捅穿地面**
#     （旧版实测 f56 膝 z = 3.9 ⟹ `Trouser` **−91.7 mm**）。
#     ⟹ 前扑段对**踝目标 y** 做闭环伺服，令**膝关节 z 始终 ≥ KNEE_Z_FALL**。
KNEE_Z_FALL = 0.1047                 # 膝关节 z 目标（= 跪姿实测值，保证连续）
# ★ 原固定增益 0.85（按「Δ踝y 121 ⟹ Δ膝z 148」标定，灵敏度 1.22）**已被实测推翻**：
#   局部灵敏度随腿的屈伸在 0.6 ~ 2.9 mm/mm 间变化 ⟹ 0.85 × 2.9 = 2.5 过冲发散。
#   现改为割线法（每次现量灵敏度），此常量只留作历史标注。
KNEE_SERVO_GAIN = 0.85               # （已弃用，见上）
# 踝目标可达上限（3D）：`leg_reach_ok` 口径是 `|髋→踝| / ((L1+L2)*0.9995) ≤ 1`，
# 这里再留 0.15% 余量 ⟹ 闭环过冲也顶不穿。
D_REACH_SAFE = (A.L_THIGH + A.L_SHIN) * 0.9992   # 实测骨长（刚性）
# ★★★ 腿的 **YZ 投影**实测（`_probe_e09_geom.py`，跪姿 f28 与 f46 逐位相同）。
#     世界骨长 410.000 / 412.000；YZ 投影 **407.301 / 411.960**
#     （等价外展角 **6.60° / 0.80°** —— ★ 两段**不同**）。
#     ★ 旧版一刀切用 `cos(6°)` 算小腿得 409.74，比实测短 **2.2 mm**，
#       正是解析反解在中段系统偏 2~3 mm 的来源
#       （`_probe_e09_geom2.log`：解析式 f58 = 697.57 vs 实测 697.65 —— 用对
#        投影后**逐帧吻合**）。这两个数只在这里出现一次，解析反解与
#        `_fy_terminal` 共用 ⟹ 起点与终点由**同一条几何**给出，不会互相打架。
L1_YZ = 0.407301                     # 大腿 YZ 投影（= 髋→膝 在 YZ 平面内的长度）
L2_YZ = 0.411960                     # 小腿 YZ 投影（= 膝→踝 在 YZ 平面内的长度）
FOOT_FLAT = 0.0                      # 脚世界俯仰：0 = 鞋底平放（站架原朝向）
# ★ 脚**全程**保持 flat：实测「踝 z 不动 + 脚俯仰不动 ⟹ 鞋底一直在原地」，
#   于是过渡段 0→28 与跪姿 hold 的鞋底读数稳定在 −3.6 mm（带内）。
#   前扑段若给脚加俯仰，脚尖会立刻插地（踝只有 80 mm 高，脚长 199 mm）；
#   要摆脚就得先把踝抬起来，那会把整条腿的网格顶离地面。**「脚平放滑行」是本支
#   唯一能同时满足「鞋底贴地 + 无穿模 + 无跳变」的口径**；脚的自然翻倒留给
#   E10 `Death`（尸体那支没有「支撑面」约束）。
FOOT_PRONE = 0.0

KNEEL_POW = 1.7                      # 跪落：启动略慢、末端最重（命中极重）
FALL_POW = 1.8                       # 前扑：同上

# 臂方向（世界单位向量；左肩/右肩镜像）
BASE_DIRS = dict(IDLE.ARM_DIRS)
KNEEL_DIRS = {
    "upperarm.L": (0.32, -0.20, -0.92), "forearm.L": (0.06, -0.42, -0.90),
    "hand.L": (0.03, -0.58, -0.81),
    "upperarm.R": (-0.32, -0.20, -0.92), "forearm.R": (-0.06, -0.42, -0.90),
    "hand.R": (-0.03, -0.58, -0.81),
}
TERM_DIRS = {
    "upperarm.L": (0.44, -0.86, -0.26), "forearm.L": (0.02, -1.00, -0.10),
    "hand.L": (0.00, -1.00, -0.06),
    "upperarm.R": (-0.44, -0.86, -0.26), "forearm.R": (-0.02, -1.00, -0.10),
    "hand.R": (0.00, -1.00, -0.06),
}

# =============================================================== 阈值
KNEEL_FOOT_LOCK_MM = 0.5
KNEEL_BAND = (-6.0, 4.0)          # 跪姿触地带：膝+小腿+鞋 同处地面附近
BODY_BAND = (-6.0, 8.0)           # 伏地带：全身最低点
PENETRATION_MIN_MM = -8.0         # 全程任一帧不许低于
HITSTOP_MAX_DEG = 0.01
BREATH_RANGE = (5.0, 34.0)
BREATH_MIN_CROSS = 3
FINAL_ELEM_MAX = 1e-6
SEAM_POS_MAX_MM = 0.01
SEAM_DIR_MAX_DEG = 0.05
NO_TELEPORT_DEG = 25.0
NO_SNAP_END_DEG = 6.0
CLIP_MAX_MM = 0.0
LEG_THIGH_R = 0.105
LEG_SHIN_R = 0.095
ARM_R = 0.042
PHASE_MATRIX_STEP_DEG = 25.0
KNEE_PATH_TOL_MM = 4.0            # 膝关节 z 允许低于目标 4 mm（闭环残余）
LIMB_STEP_MAX_MM = 60.0           # 膝/踝单帧世界位移上限（= 3.6 m/s @60fps）
# ⑩ 「终点真的是伏地」——本支**存在理由本身**的量化：末段躯干必须**整体落到地面附近**。
#    ★ 为什么必须新开一条：`dft_final_pose_ok` 只证明「末帧 == 触地定格末帧」（自持），
#      **不能**证明那一帧是伏地。`E09_TP_NOFALL=1`（抽掉前扑）实测**全绿**
#      （`_e09_rv_NO_FALL.log`）—— 因为不倒地时 70 与 120 同样是跪姿、同样逐位相同。
#      载体 = **胸骨顶世界 z 在 [KNEEL_TAIL → END] 的落差**（跪姿 1021 → 伏地 219，
#      实测落差 802 mm）+ **骨盆终点高度**（伏地 108 mm）。两个载体一个抓「躯干落下去」、
#      一个抓「骨盆贴地」，任一不成立即红。
TERMINAL_DROP_MIN_MM = 600.0      # 胸骨顶落差下限（实测 802）
TERMINAL_PELVIS_MAX_MM = 200.0    # 终点骨盆 z 上限（实测 108）

# =============================================================== 取景（自己立基准）
VIEW_E09_SIDE = ("side", (4.2, 0.0, 0.70), (0.0, 0.0, 0.70), 2.00, (900, 1000))
VIEW_E09_FRONT = ("front", (0.0, -5.6, 0.70), (0.0, 0.0, 0.70), 2.00, (900, 1000))
VIEW_E09_3Q = ("three_quarter", (3.0, -3.4, 1.00), (0.0, 0.0, 0.85), 2.00,
               (900, 1000))

# =============================================================== 反向验证旋钮
def _b(key):
    return os.environ.get(key, "0").strip() not in ("", "0", "false", "False")


SEAM_ZERO = _b("E09_TP_SEAM_ZERO")
NO_KNEEL = _b("E09_TP_NOKNEEL")
NO_FALL = _b("E09_TP_NOFALL")
NO_BREATH = _b("E09_TP_NOBREATH")
FOOT_SWAY = _b("E09_TP_FOOTSWAY")
FOOT_SWAY_MM = 55.0
KNEE_FLOAT = _b("E09_TP_KNEEFLOAT")
KNEE_FLOAT_MM = 60.0
NO_HITSTOP = _b("E09_TP_NOHITSTOP")
SINK = _b("E09_TP_SINK")
SINK_MM = 60.0
# ⑨ 前扑段抽掉「膝贴地」解析反解（踝停在跪姿位不后滑）⟹ 膝捅穿地面
KNEE_PLUNGE = _b("E09_TP_KNEEPLUNGE")
# ⑩ 在 f48 给踝目标 y 注入 +50 mm 尖峰 ⟹ 肢端单帧世界位移越限
LIMB_JUMP = _b("E09_TP_LIMBJUMP")
LIMB_JUMP_MM = 50.0
LIMB_JUMP_FRAME = 48
TRACE = _b("E09_TRACE")

BASE = {}
KNEEL = {}
TERM = {}
BONE_LIST = []
ANKLE_REST = {}          # 站架踝世界坐标（foot.* head），由 boot() 实测填入


# =============================================================== 包络
def kneel_env(frame):
    if NO_KNEEL:
        return 1.0
    if frame <= START:
        return 0.0
    if frame >= KNEE:
        return 1.0
    return (frame / float(KNEE)) ** KNEEL_POW


def fall_env(frame):
    if NO_FALL:
        return 0.0
    if frame <= KNEEL_TAIL:
        return 0.0
    if frame >= LAND:
        return 1.0
    t = (frame - KNEEL_TAIL) / float(LAND - KNEEL_TAIL)
    return t ** FALL_POW


def sag_env(frame):
    """跪姿停留段的"失力前倾"：`KNEE_HOLD` 起 0 → `KNEEL_TAIL` 到 1。
    ★ 只动**躯干**（绝不动骨盆 / 腿）⟹ 跪姿 hold 的脚锁不受影响。"""
    if frame <= KNEE_HOLD:
        return 0.0
    if frame >= KNEEL_TAIL:
        return 1.0
    x = (frame - KNEE_HOLD) / float(KNEEL_TAIL - KNEE_HOLD)
    return x * x * (3.0 - 2.0 * x)


def break_hitstop(frame):
    """反向验证 ⑦：把两个冻结窗内的姿态**缓慢漂移**（控制组）。"""
    if not NO_HITSTOP:
        return 0.0
    if KNEE <= frame <= KNEE_HOLD:
        return (frame - KNEE) * 1.5
    if LAND <= frame <= LAND_HOLD:
        return (frame - LAND) * 1.5
    return 0.0


def breath_env(frame):
    """伏地呼吸包络 ∈ [0, 1]：**0 = 呼气基线（= 定格姿）**，1 = 吸气顶。

    ★★★ 为什么是**半波**（`(1−cos)/2`）而不是 `sin`：
    `_probe_e09_flat.py` 实测（髋 z=108 / 踝 y=716 / z=170，逐帧扫 70→120）——
      · `br = +0.951`（吸气）：胸骨顶 230.41，最低件 = `Trouser` **+4.07**；
      · `br = −0.951`（呼气）：胸骨顶 208.40，最低件 = `Hair_Mass` **−22.29**。
    即 `sin` 的**负半周**会把整条「背—颈—头」链压向地面（放大倍率 ≈ 2.6×——
    胸骨只降 11 mm，头顶却降 29 mm），f90/f114 两处因此陷地 30 mm。
    ⟹ 呼吸只允许**朝一个方向**做功：吸气时背拱起、头顶抬起；呼气只回到基线
    （基线 = 触地定格姿本身）。这在物理上也更对：伏地呼吸动的是**背**，
    不是把脸往地里按。半波仍满足「端点归零」（f70 与 f120 都是 `br = 0`）。
    """
    if NO_BREATH or frame <= LAND_HOLD:
        return 0.0
    span = float(END - LAND_HOLD)
    return 0.5 * (1.0 - math.cos(2.0 * math.pi * BREATH_CYCLES
                                 * (frame - LAND_HOLD) / span))


# =============================================================== 工具
def _mix_dir(a, b, t):
    va = Vector(a).normalized()
    vb = Vector(b).normalized()
    v = va.lerp(vb, t)
    if v.length < 1e-6:
        return tuple(vb)
    return tuple(v.normalized())


def _blend_pose(pa, pb, t):
    out = {}
    for key in set(pa) | set(pb):
        if key == "@loc":
            locs = {}
            for bone in set(pa.get("@loc", {})) | set(pb.get("@loc", {})):
                va = pa.get("@loc", {}).get(bone, (0.0, 0.0, 0.0))
                vb = pb.get("@loc", {}).get(bone, (0.0, 0.0, 0.0))
                locs[bone] = tuple(x + (y - x) * t for x, y in zip(va, vb))
            out["@loc"] = locs
        else:
            va = pa.get(key, (0.0, 0.0, 0.0))
            vb = pb.get(key, (0.0, 0.0, 0.0))
            out[key] = tuple(x + (y - x) * t for x, y in zip(va, vb))
    return out


# =============================================================== 腿：踝目标 + IK
def keep_foot_pitch(arm, name, fp_deg):
    """把该骨的世界朝向钉成 **rest 朝向再绕世界 X 转 `fp_deg`**，返回解出的 euler。

    与 `A.keep_world_orientation` 同一手法（直接令世界 3×3 = 目标 3×3），
    只是目标不是 rest 本身、而是"rest 再俯仰 `fp_deg`"。

    为什么不用 `foot.rx = 某个角度`：脚的世界俯仰 = `pelvis.rx + thigh.rx +
    shin.rx + foot.rx` 的累积，而 IK 解出的 thigh/shin 每帧都在变；用欧拉累加
    补偿既脆又有累积误差（`A.keep_world_orientation` 的注释里实测过 10 mm 级偏差）。
    钉世界朝向没有这个问题：`fp_deg` 就是"鞋相对地面翘多少度"。
    """
    pose_bone = arm.pose.bones[name]
    rest_basis = pose_bone.bone.matrix_local.to_3x3()
    rot = Matrix.Rotation(math.radians(fp_deg), 3, "X")
    target = (rot @ rest_basis).to_4x4()
    target.translation = pose_bone.matrix.translation   # 只转不挪 ⟹ 踝不脱臼
    pose_bone.matrix = target
    bpy.context.view_layer.update()
    return tuple(math.degrees(v) for v in pose_bone.rotation_euler)


def _fy_terminal(az):
    """解析式在**伏地终点**（p=1）会给出的踝 y —— 用来求回正量。"""
    dy1 = math.sqrt(max(0.0, L1_YZ * L1_YZ
                        - (TERM_PELVIS_Z - KNEE_Z_FALL) ** 2))
    dy2 = math.sqrt(max(0.0, L2_YZ * L2_YZ
                        - (KNEE_Z_FALL - az) ** 2))
    return TERM_PELVIS_Y + dy1 + dy2


def ankle_target(arm, frame, side):
    """本支的踝世界目标（米）。两段语义：

    ① **站架踝 → 跪姿踝**（`k` 段）：踝沿地面后滑、**高度不变**。
       「高度不变」是这条判据族的核心：站架踝 z ≈ 79.8 mm、鞋底 ≈ 0，所以只要
       踝的世界 z 不动、脚的世界俯仰不动，鞋底就一直在原地 ⟹ 过渡段的"脚向后滑"
       不会插进地面（旧欧拉版实测鞋尖 −211.26 mm）。

    ② **前扑段**（`p` > 0）：踝 y 由**「膝贴地」解析反解**，不再是碰运气的插值。
       ★★★ 为什么必须反解（`_probe_e09_flat.py` 实测，本支第三次返工的直接原因）：
       先前的口径是「踝 y 从跪姿位线性滑到伏地位，膝交给闭环伺服去救」。实测
       **救不动**——`ankle y` 对 `knee z` 的局部灵敏度在起步段只有 **0.04 mm/mm**
       （f49：踝 y 推 10 mm，膝只抬 0.42 mm），伺服要推 **+160 mm** 才见效，于是
       f49→f50 踝 y 从 431 瞬跳到 544 ⟹ `dft_limb_step_ok` 见红 114.4 mm/帧；
       而 f48/f49 两帧干脆救不回来（膝 98.5 / 91.9）。
       反解口径：膝必须在世界 z = `KNEE_Z_FALL`（= 跪姿实测值，保证连续），
       于是由髋位置**唯一确定**大腿的水平后移量，再沿小腿方向接上踝：
           drop1 = hip.z − KNEE_Z_FALL      dy1 = sqrt(L1yz² − drop1²)
           drop2 = KNEE_Z_FALL − ankle.z    dy2 = sqrt(L2yz² − drop2²)
           ankle.y = hip.y + dy1 + dy2
       `L1yz / L2yz` = **实测 YZ 投影**（见常量区）。

       ★★★ **第四轮返工：把「短过渡混合」删掉**（`_e09_gate10.log`
       `dft_limb_step_ok` 红 91.41 mm/帧 @f48 的唯一原因）。
       旧版把解析式与跪姿值做 `t = min(1, p/0.04)` 的 smoothstep 过渡，
       本意是「p 极小时解析式与实测跪姿踝差 ~16 mm」。但那是**用错的投影长
       算出来的 16 mm**——换成实测投影后，解析式在 p→0（髋 z = 512）给出
       **412.09 mm**，与实测跪姿踝 **411.00** 只差 **1.1 mm**
       ⟹ **过渡根本不需要**。而 t 混合（f48 时 t = 0.347）把踝目标从解析值
       481.7 硬拽回 435.7（**短 46 mm**）⟹ 膝被拉低 ⟹ 外环伺服按 ±80 mm 的
       单步上限猛推 ⟹ f47→f48 踝 y 冲 512.9、膝冲 111.5，`dft_limb_step_ok`
       见红 91.41。删掉混合后解析轨迹逐帧步长 ≤ 38.5 mm（< 60 上限），
       且**膝由构造恒在 `KNEE_Z_FALL`**，伺服退化为残余修正。
    """
    k = kneel_env(frame)
    p = fall_env(frame)
    rest = ANKLE_REST[side]
    gy = rest.y + (KNEEL_ANKLE_Y - rest.y) * k
    az = rest.z + (PRONE_ANKLE_Z - rest.z) * p
    if p <= 0.0:
        point = Vector((rest.x, gy, rest.z))
    else:
        hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
        drop1 = max(0.0, hip.z - KNEE_Z_FALL)
        dy1 = math.sqrt(max(0.0, L1_YZ * L1_YZ - drop1 * drop1))
        drop2 = KNEE_Z_FALL - az
        dy2 = math.sqrt(max(0.0, L2_YZ * L2_YZ - drop2 * drop2))
        # ★ 2D 反解仍有 ~3 mm 系统偏差（外展随构型变化）。用**实测锚点**
        #   `PRONE_ANKLE_Y` 做线性回正，保证 p=1 时踝正好落在扫描出来的最优位。
        fy = hip.y + dy1 + dy2 + (PRONE_ANKLE_Y - _fy_terminal(PRONE_ANKLE_Z)) * p
        if KNEE_PLUNGE:
            # ⑨ 反向验证：踝不后滑 ⟹ 膝失去支撑、直插地下
            fy = gy
        point = Vector((rest.x, fy, az))
    if LIMB_JUMP and frame == LIMB_JUMP_FRAME:
        # ⑩ 反向验证：单帧给踝目标一个 50 mm 外推尖峰
        point = Vector((point.x, point.y + LIMB_JUMP_MM / 1000.0, point.z))
    if KNEE_FLOAT and KNEE <= frame <= KNEEL_TAIL:
        # ⑥ 反向验证：跪姿整条腿**整体抬 60 mm**。
        #    ★ 必须连**踝目标一起抬**：跪姿下大腿垂直且全伸展（dy1 = 0），
        #      骨盆抬 60 ⟹ 膝自动抬 60；但鞋底由踝目标（钉死）决定，
        #      只抬骨盆时鞋底仍在地面 ⟹ `dft_knee_contact_ok` 的载体会塌回鞋底、
        #      判据反而**全绿**（旧版把抬升加在骨盆 **Y** 轴上，连膝都没抬动，
        #      实测只打出 `dft_body_ground_ok`/`dft_limb_step_ok`）。
        point = Vector((point.x, point.y, point.z + KNEE_FLOAT_MM / 1000.0))
    if FOOT_SWAY and KNEE_HOLD < frame <= KNEEL_TAIL:
        # ⑤ 反向验证：跪姿 hold 段把踝目标整体后挪 ⟹ 脚跟着走 ⟹ 脚锁见红。
        #    ★ 扰动必须**严格落在判据窗口内部**：`dft_kneel_foot_lock_ok` 的基准帧
        #      取的是窗口首帧（`KNEE`）。旧版扰动从 `KNEE` 起（基准帧也被挪了 55 mm），
        #      于是「组内漂移」仍是 0.000 ⟹ 判据**假绿**、只打出 `dft_limb_step_ok`。
        point = Vector((point.x, point.y + FOOT_SWAY_MM / 1000.0, point.z))
    return point


def foot_pitch(frame):
    """脚的世界俯仰（0 = 鞋底平放 = 站架原朝向）。跪姿段保持 0（贴地滑），
    前扑段翻到 `FOOT_PRONE`（脚尖向下、脚掌朝后上）。用 smoothstep 让翻转
    **滞后于踝的上抬**，避免中途鞋尖先着地。"""
    p = fall_env(frame)
    return FOOT_FLAT + (FOOT_PRONE - FOOT_FLAT) * (p * p * (3.0 - 2.0 * p))


def lock_feet(arm, pose, want, fp_deg, iters=8, damp=0.85, knee_z=None):
    """把双踝**闭环**钉在 `want`（世界坐标 dict）上，就地改 `pose` 的腿通道。

    照抄 E02 的结构（x 偏差反馈进 `thigh.rz`、逐轮收缩目标），差别两处：
    ① 本支的 `want` 由 `ankle_target` 给（贴地滑 + 前扑），不是固定锚点；
    ② `knee_z` 给了就再套一层**外环单向伺服**：膝不许入地（控制量 = 踝目标 y）。
       为什么必须有：前扑段髋 z 从 512 掉到 100，而**膝网格半径 104.6 mm**
       ⟹ 膝必须一直停在 z ≈ 104；踝不跟着后滑，膝就捅穿地面（实测 −91.7 mm）。
       增益实测（Δ踝y 121 ⟹ Δ膝z 148），收敛后残余写进 `dft_knee_z_min_mm`。
    """
    goal = {s: Vector(want[s]) for s in SIDES}
    tgt = {s: Vector(want[s]) for s in SIDES}
    rz = {s: pose.get("thigh." + s, (0.0, 0.0, 0.0))[2] for s in SIDES}
    pelvis_rx = pose.get("pelvis", (0.0, 0.0, 0.0))[0]
    fp = fp_deg
    worst = 0.0

    def _solve():
        nonlocal worst
        for side in SIDES:
            tgt[side] = Vector(goal[side])
        for _ in range(iters):
            A.apply_pose(arm, pose)
            for side in SIDES:
                hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
                th, sh = A.leg_ik(hip.y, hip.z, tgt[side].y, tgt[side].z,
                                  tilt_deg=pelvis_rx)
                pose["thigh." + side] = (th, 0.0, rz[side])
                pose["shin." + side] = (sh, 0.0, 0.0)
            A.apply_pose(arm, pose)
            for side in SIDES:
                pose["foot." + side] = keep_foot_pitch(arm, "foot." + side, fp)
            A.apply_pose(arm, pose)
            for side in SIDES:
                err = (Vector(A.bone_world(arm, "foot." + side, "head"))
                       - goal[side])
                tgt[side] = tgt[side] - err * damp
                rz[side] = rz[side] + (1.0 / 0.01309) * err.x * damp
                worst = max(worst, err.length * 1000.0)

    def _knee_min():
        return min(A.bone_world(arm, "shin." + s, "head").z for s in SIDES)

    def _clamp_reach():
        """把踝目标钳在可达上限内（留 0.15% 余量）。

        为什么必须有：`leg_reach_ok` 的口径是 `|髋→踝| / ((L1+L2)*0.9995) ≤ 1`，
        而 `_solve()` 的闭环会**过冲**到 1.00003（实测）。夹在 δ 步之前做，
        保证伺服无论怎么推都不会顶穿可达判据。
        """
        for side in SIDES:
            hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
            v = goal[side] - hip
            if v.length > D_REACH_SAFE:
                goal[side] = hip + v * (D_REACH_SAFE / v.length)

    _clamp_reach()
    _solve()
    if knee_z is not None:
        # ★★★ 灵敏度实测（`_probe_e09_flat.py`）：Δ踝y 15 mm ⟹ Δ膝z 在
        #     **0.6 ~ 2.9 mm/mm** 之间**变号量级地变**（取决于腿的屈伸程度）。
        #     固定增益 0.85 × 灵敏度 2.9 = 2.5 ⟹ **过冲发散**，这正是 f49 膝 z
        #     只能收敛到 99.44（差 5.26 mm）的原因。改成**每次先量局部灵敏度、
        #     再走牛顿步**（割线法），收敛与构型无关。
        # ★★★ 第五轮返工：**单步上限 80 mm → 6 mm**。旧值 80 mm 的前提是
        #     「解析基准轨迹本身就差几十毫米、要靠伺服追」。删掉 t 混合后基准
        #     已把膝钉在 `KNEE_Z_FALL`（构造保证）⟹ 伺服只该做**残余修正**；
        #     此时若还留 80 mm 的单步权限，任何一点数值噪声都会被放大成
        #     「踝瞬移」（`_e09_gate10.log` 的 91.41 mm/帧 就是这么来的）。
        #     6 mm/步 × 8 迭代 = 48 mm 修正量程，对残余足够（实测需 0~3 mm）。
        probe_dy = 0.004                                   # 4 mm 试探步
        for _ in range(8):
            kz0 = _knee_min()
            err = knee_z - kz0
            if err < 2e-4:                                 # 0.2 mm 带内即停
                break
            for side in SIDES:
                goal[side] = Vector((goal[side].x, goal[side].y + probe_dy,
                                     goal[side].z))
            _clamp_reach()
            _solve()
            slope = (_knee_min() - kz0) / probe_dy
            if abs(slope) < 0.05:
                break                                      # 近全伸，踝 y 抬不动膝
            step = max(-0.006, min(0.006, err / slope))    # 单步 ≤ 6 mm
            for side in SIDES:
                goal[side] = Vector((goal[side].x,
                                     goal[side].y - probe_dy + step,
                                     goal[side].z))
            _clamp_reach()
            _solve()
    return worst


def body_low_profile(arm=None):
    """逐网格对象的最低世界 z（毫米）。★ 本支新增的基础设施件。

    为什么要逐件：`lowest_z_by_side` 只回答"最低多少"，回答不了"**是哪个件**"。
    D14 `Knockdown_F@20` 的 `Trouser_R` 陷地 **61.54 mm** 就是这样溜过去的
    —— 它当时只被"鞋底"尺子看着。逐件剖面上线后，任何单件的陷地都会显形。
    """
    depsgraph = bpy.context.evaluated_depsgraph_get()
    out = {}
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        matrix = evaluated.matrix_world
        out[obj.name] = min((matrix @ v.co).z for v in mesh.vertices) * 1000.0
        evaluated.to_mesh_clear()
    return out


# =============================================================== 姿态装配
def dft_pose(arm, frame):
    k = kneel_env(frame)
    p = fall_env(frame)
    br = breath_env(frame)
    drift = break_hitstop(frame)

    pose = _blend_pose(BASE, KNEEL, k)
    pose = _blend_pose(pose, TERM, p)

    # ---- 跪姿停留段的"失力前倾"（只动躯干）------------------------------
    sg = sag_env(frame) * (1.0 - p)
    if sg > 0.0:
        for name, w in (("spine_01", 0.25), ("spine_02", 0.30),
                        ("chest", 0.30), ("neck", 0.10), ("head", 0.05)):
            rx, ry, rz = pose.get(name, (0.0, 0.0, 0.0))
            pose[name] = (rx + SAG_LEAN * w * sg, ry, rz)

    # ---- 伏地呼吸（背拱起 ⟹ 胸骨顶起伏；★ 端点归零）----------------------
    # ★ 两次实测修正：
    #   ① （`_dump_e09_prof.py`）原权重里 `head = −1.5` 在**伏地**姿态下把头顶向
    #      地面 —— f90 实测 `Hair_Mass` −39.91 mm。改成**吸气时颈/头也抬起**
    #      （与胸同向）⟹ 呼吸只让「背—头」这条链整体起伏。
    #   ② （`_probe_e09_flat.py`）即便同向，`sin` 的负半周仍把头顶压到 −22.29。
    #      ⟹ 包络改**半波**（`breath_env`，恒 ≥ 0），呼吸只朝抬升方向做功。
    #   幅度同时抬到 ~17 mm（带 [5, 34] 内），最低件全程留在 `Trouser`（+4.1）。
    if br != 0.0:
        for name, drx in (("chest", -3.2), ("spine_02", -1.3),
                          ("neck", -1.3), ("head", -1.0),
                          ("shoulder.L", 4.3), ("shoulder.R", 4.3)):
            rx, ry, rz = pose.get(name, (0.0, 0.0, 0.0))
            pose[name] = (rx + drx * br, ry, rz)

    if drift != 0.0:
        rx, ry, rz = pose.get("chest", (0.0, 0.0, 0.0))
        pose["chest"] = (rx + drift, ry, rz)

    pose["root"] = (0.0, 0.0, 0.0)
    pose.update(A.FIST)

    # ---- 反向验证旋钮 ----------------------------------------------------
    # ⑤ FOOT_SWAY 已移到 `ankle_target`（腿是 IK 驱动的 ⟹ 摆骨盆会被 IK 补偿掉，
    #    只有**挪踝目标**才真的让脚动）。这里只留膝离地 / 整体下沉两个。
    if KNEE_FLOAT and frame >= KNEE:
        # ⑥ 跪姿整体抬升：**z 轴**（不是 y）+ 窗口只到 `KNEEL_TAIL`
        #    （窗口外的抬升会被算成 60 mm 单帧跳变，那属于另一条判据的靶子）。
        #    `ankle_target` 里同步抬踝目标 —— 两条合起来才是「整条跪姿腿离地」。
        loc = pose["@loc"]["pelvis"]
        if KNEE <= frame <= KNEEL_TAIL:
            pose["@loc"] = {"pelvis": (loc[0], loc[1],
                                       loc[2] + KNEE_FLOAT_MM / 1000.0)}
    if SINK and frame >= LAND_HOLD:
        loc = pose["@loc"]["pelvis"]
        pose["@loc"] = {"pelvis": (loc[0], loc[1] - SINK_MM / 1000.0, loc[2])}

    # ---- 臂：方向插值 + 反解（不插欧拉 ⟹ 无万向节假跳）------------------
    A.apply_pose(arm, pose)
    for bone in ARM_BONES:
        d1 = _mix_dir(BASE_DIRS[bone], KNEEL_DIRS[bone], k)
        d = _mix_dir(d1, TERM_DIRS[bone], p)
        pose[bone] = A.aim_bone(arm, bone, d)

    # ---- 腿：踝目标（世界）+ 两骨 IK（闭环）；前扑段加「膝不入地」外环伺服 ----
    want = {s: ankle_target(arm, frame, s) for s in SIDES}
    knee_z = KNEE_Z_FALL if fall_env(frame) > 0.0 else None
    lock_feet(arm, pose, want, foot_pitch(frame), knee_z=knee_z)

    if TRACE:
        A.apply_pose(arm, pose)
        lows = body_low_profile()
        ankles = {s: [round(A.bone_world(arm, "foot." + s, "head").y * 1000.0, 2),
                      round(A.bone_world(arm, "foot." + s, "head").z * 1000.0, 2),
                      round(A.bone_world(arm, "toe." + s, "tail").z * 1000.0, 2)]
                  for s in SIDES}
        print("E09_TRACE f=%3d k=%.3f p=%.3f sg=%.3f br=%+.3f low=%.2f(%s) "
              "ankle_y/z/tipz=%s" % (frame, k, p, sg, br, min(lows.values()),
                                     min(lows.items(), key=lambda kv: kv[1])[0],
                                     ankles))
    return pose


# =============================================================== 快照
def world_mats(arm, action, frame):
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()
    out = {}
    for name in BONE_LIST:
        if name in arm.pose.bones:
            out[name] = (arm.matrix_world @ arm.pose.bones[name].matrix).copy()
    return out


def _mat_delta(a, b):
    pos = (a.translation - b.translation).length * 1000.0
    dirs = []
    for index in range(3):
        va = a.to_3x3().col[index]
        vb = b.to_3x3().col[index]
        cos = max(-1.0, min(1.0, va.normalized().dot(vb.normalized())))
        dirs.append(math.degrees(math.acos(cos)))
    return pos, max(dirs)


def _worst_step(samples, i0, i1):
    worst, at = 0.0, None
    ea, eb = samples[i0]["euler"], samples[i1]["euler"]
    for name in set(ea) | set(eb):
        va = ea.get(name, (0.0, 0.0, 0.0))
        vb = eb.get(name, (0.0, 0.0, 0.0))
        step = max(abs(x - y) for x, y in zip(va, vb))
        if step > worst:
            worst, at = step, (samples[i1]["frame"], name)
    return worst, at


def limb_clearance(arm):
    pts = []
    for side in SIDES:
        for name in ARM_BONES:
            h = Vector(A.bone_world(arm, name, "head"))
            t = Vector(A.bone_world(arm, name, "tail"))
            for i in range(9):
                pts.append(h.lerp(t, i / 8.0))
    worst = 1e9
    for side in SIDES:
        for bone_name, radius in (("thigh." + side, LEG_THIGH_R),
                                  ("shin." + side, LEG_SHIN_R)):
            a = Vector(A.bone_world(arm, bone_name, "head"))
            b = Vector(A.bone_world(arm, bone_name, "tail"))
            ab = b - a
            for p in pts:
                t = 0.0 if ab.length_squared < 1e-12 else max(
                    0.0, min(1.0, (p - a).dot(ab) / ab.length_squared))
                worst = min(worst, (p - (a + ab * t)).length - radius)
    return worst * 1000.0


# =============================================================== 专属门禁
def dft_assertions(arm, action, samples, meshes):  # noqa: C901
    res = {}
    scene = bpy.context.scene
    frames = [s["frame"] for s in samples]
    hold = [f for f in frames if KNEE <= f <= KNEEL_TAIL]
    landed = [f for f in frames if LAND <= f <= END]

    # ---- ① 跪姿 hold 的脚锁（★ 只在 [KNEE, KNEEL_TAIL] 判）----------------
    ref = {s: Vector(samples[KNEE - START]["foot." + s]) for s in SIDES}
    ref_toe = {s: Vector(samples[KNEE - START]["toe." + s]) for s in SIDES}
    drift = {s: 0.0 for s in SIDES}
    toe_drift = {s: 0.0 for s in SIDES}
    step_travel = {s: 0.0 for s in SIDES}
    for sample in samples:
        for side in SIDES:
            d = (Vector(sample["foot." + side]) - ref[side]).length * 1000.0
            t = (Vector(sample["toe." + side]) - ref_toe[side]).length * 1000.0
            if sample["frame"] in hold:
                drift[side] = max(drift[side], d)
                toe_drift[side] = max(toe_drift[side], t)
            step_travel[side] = max(
                step_travel[side],
                (Vector(sample["foot." + side])
                 - Vector(samples[0]["foot." + side])).length * 1000.0)
    res["dft_kneel_hold_ankle_drift_mm"] = {k: round(v, 4)
                                            for k, v in drift.items()}
    res["dft_kneel_hold_toe_drift_mm"] = {k: round(v, 4)
                                          for k, v in toe_drift.items()}
    res["dft_foot_travel_total_mm"] = {k: round(v, 2)
                                       for k, v in step_travel.items()}
    res["dft_kneel_foot_lock_ok"] = bool(
        max(max(drift.values()), max(toe_drift.values())) <= KNEEL_FOOT_LOCK_MM)
    res["dft_kneel_foot_lock_note"] = (
        "★ 本支的「脚不动」**只在跪姿 hold [%d, %d] 判**：过渡段（0→%d）"
        "本支**故意把双脚收到膝后**（实测单脚行程 %.1f mm），与 E02 同一处口径处理。"
        "★ 守卫是 `E09_TP_FOOTSWAY=1`（给 hold 段骨盆加 ±%.0f mm 世界 Y 摆动）"
        "—— 腿是刚性的，骨盆一动脚就跟着走 ⟹ 该旋钮必须见红。"
        % (KNEE, KNEEL_TAIL, KNEE, res["dft_foot_travel_total_mm"]["L"],
           FOOT_SWAY_MM))

    # ---- ② 力量传导链（脚→腿→髋→腰→肩→手，每段都要有关键帧）--------------
    knee_deg = 0.0
    for sample in samples:
        knee_deg = max(knee_deg, abs(sample["euler"].get(
            "shin.L", (0.0, 0.0, 0.0))[0]))
    pelvis = [Vector(s["pelvis"]) for s in samples]
    hip_travel = max((p - pelvis[0]).length for p in pelvis) * 1000.0
    waist = [abs(s["euler"].get("chest", (0.0, 0.0, 0.0))[0])
             for s in samples]
    waist_deg = (max(waist) - min(waist)) * 180.0 / math.pi
    shoulder = [Vector(s["upperarm.L"]) for s in samples]
    shoulder_mm = max((p - shoulder[0]).length for p in shoulder) * 1000.0
    hand = [Vector(s["hand.L.tail"]) for s in samples]
    hand_mm = max((p - hand[0]).length for p in hand) * 1000.0
    foot_mm = max(step_travel.values())
    res["dft_chain_travel"] = {"foot_mm": round(foot_mm, 3),
                               "knee_deg": round(knee_deg, 3),
                               "hip_mm": round(hip_travel, 3),
                               "waist_deg": round(waist_deg, 3),
                               "shoulder_mm": round(shoulder_mm, 3),
                               "hand_mm": round(hand_mm, 3)}
    res["chain_present_ok"] = bool(
        foot_mm > 20.0 and knee_deg > 0.2 and hip_travel > 2.0
        and waist_deg > 2.0 and shoulder_mm > 1.0 and hand_mm > 20.0)

    # ---- ③ 逐件贴地（★ 本支新增基础设施的用武之地）------------------------
    prof = {}
    for frame in sorted(set(list(range(START, END + 1, 2)) + [KNEE, KNEE_HOLD,
                                                              KNEEL_TAIL,
                                                              LAND, END])):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        prof[frame] = body_low_profile()

    def _worst(frame, keys):
        return min(prof[frame][k] for k in keys if k in prof[frame])

    body_keys = tuple(prof[KNEE].keys())
    knee_keys = ("Trouser_L", "Trouser_R", "Shoe_Sole_L", "Shoe_Sole_R",
                 "Shoe_Upper_L", "Shoe_Upper_R", "Shoe_Toe_Cap_L",
                 "Shoe_Toe_Cap_R")
    kneel_lows = {f: _worst(f, knee_keys) for f in hold if f in prof}
    landed_lows = {f: _worst(f, body_keys) for f in landed if f in prof}
    all_lows = {f: min(prof[f].values()) for f in prof}
    res["dft_kneel_low_min_mm"] = round(min(kneel_lows.values()), 2)
    res["dft_kneel_low_max_mm"] = round(max(kneel_lows.values()), 2)
    res["dft_knee_contact_ok"] = bool(
        KNEEL_BAND[0] <= res["dft_kneel_low_min_mm"]
        and res["dft_kneel_low_max_mm"] <= KNEEL_BAND[1])
    res["dft_body_low_min_mm"] = round(min(landed_lows.values()), 2)
    res["dft_body_low_max_mm"] = round(max(landed_lows.values()), 2)
    res["dft_body_ground_ok"] = bool(
        BODY_BAND[0] <= res["dft_body_low_min_mm"]
        and res["dft_body_low_max_mm"] <= BODY_BAND[1])
    res["dft_worst_part"] = min(prof[END].items(), key=lambda kv: kv[1])[0]
    res["dft_worst_frame"] = min(all_lows.items(), key=lambda kv: kv[1])[0]
    res["dft_global_low_mm"] = round(min(all_lows.values()), 2)
    res["dft_no_penetration_ok"] = bool(
        res["dft_global_low_mm"] >= PENETRATION_MIN_MM)
    res["dft_ground_note"] = (
        "★★★ **本支新建的判据族**（D14 那处 `Trouser_R` 陷地 61.54 mm 正是"
        "「没有判据盯着的约束」）。口径：逐件最低 z（`body_low_profile`）。"
        "① 跪姿带 `dft_knee_contact_ok` ∈ [%.0f, %.0f] mm（膝/小腿/鞋 同处地面附近）；"
        "② 伏地带 `dft_body_ground_ok` ∈ [%.0f, %.0f] mm（**全身最低点**，"
        "与站姿「鞋底 −2~+6」是**不同载体** ⟹ 不同带）；"
        "③ 全程 `dft_no_penetration_ok` ≥ %.0f mm。最险帧 = f%s，最低件 = `%s`。"
        % (KNEEL_BAND[0], KNEEL_BAND[1], BODY_BAND[0], BODY_BAND[1],
           PENETRATION_MIN_MM, res["dft_worst_frame"], res["dft_worst_part"]))

    # ---- ③b 膝不入地 + 无肢体跳变（★ 本支新增两条判据）--------------------
    # 载体：**独立重测**（`scene.frame_set` 逐帧读膝关节 / 踝关节世界坐标），
    #       不复用 `dft_pose` 的内部量 —— 判据必须自己去看世界，不看姿态函数的自述。
    knee_zs, steps, step_at = [], [], None
    prev = None
    for frame in range(START, END + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        cur = {}
        for side in SIDES:
            cur["knee." + side] = Vector(A.bone_world(arm, "shin." + side, "head"))
            cur["foot." + side] = Vector(A.bone_world(arm, "foot." + side, "head"))
        if frame >= KNEE:
            knee_zs.append(min(v.z for k, v in cur.items()
                               if k.startswith("knee")) * 1000.0)
        if prev is not None:
            for key in cur:
                d = (cur[key] - prev[key]).length * 1000.0
                if step_at is None or d > step_at[0]:
                    step_at = (d, frame, key)
                steps.append(d)
        prev = cur
    res["dft_knee_z_min_mm"] = round(min(knee_zs), 2)
    res["dft_knee_z_at"] = KNEE + knee_zs.index(min(knee_zs))
    res["dft_knee_path_ok"] = bool(
        res["dft_knee_z_min_mm"] >= (KNEE_Z_FALL * 1000.0) - KNEE_PATH_TOL_MM)
    res["dft_limb_step_max_mm"] = round(max(steps), 2)
    res["dft_limb_step_at"] = step_at
    res["dft_limb_step_ok"] = bool(max(steps) <= LIMB_STEP_MAX_MM)
    res["dft_knee_path_note"] = (
        "★★★ **本支新增判据 ①**：前扑段（%d→%d）髋 z 从 512 mm 掉到 100 mm，"
        "而膝网格半径 **104.6 mm** ⟹ 膝**必须一直停在 z ≈ %.1f mm**，否则膝捅穿地面"
        "（旧版实测 f56 膝 z = 3.9 ⟹ `Trouser` −91.7 mm）。载体 = **逐帧直读膝关节"
        "世界 z**（不是姿态函数自述）。实测最低 %.2f mm（f%s），容差 %.1f mm。"
        "★ 守卫 = `E09_TP_NOFALL=1` 之外另有 `E09_TP_KNEEFLOAT=1`（膝抬 60 mm）——"
        "它必须让 `dft_knee_contact_ok` 见红。"
        % (KNEEL_TAIL, LAND, KNEE_Z_FALL * 1000.0, res["dft_knee_z_min_mm"],
           res["dft_knee_z_at"], KNEE_PATH_TOL_MM))
    res["dft_limb_step_note"] = (
        "★★★ **本支新增判据 ②**：膝/踝**逐帧世界位移**上限 %.0f mm/帧"
        "（= %.1f m/s @60fps，与前扑段「整体下落 400 mm / 20 帧 = 20 mm/帧」同量级，"
        "留 ~1.5× 余量）。实测峰值 %.2f mm/帧 @f%s `%s`。"
        "为什么必须有：本支是**第一支腿由 IK 驱动**的动作，踝目标是几何反推出来的 ——"
        "闭环解算一旦不收敛就会给出「瞬移的腿」，而**没有任何旧判据盯位移跳变**"
        "（`no_teleport` 只盯旋转、`phase_matrix_step` 只盯相位角）。"
        % (LIMB_STEP_MAX_MM, LIMB_STEP_MAX_MM * 60.0 / 1000.0,
           res["dft_limb_step_max_mm"],
           res["dft_limb_step_at"][1] if res["dft_limb_step_at"] else "?",
           res["dft_limb_step_at"][2] if res["dft_limb_step_at"] else "?"))

    # ---- ④ 两个命中停顿（2~4 帧完全冻结）---------------------------------
    windows = {}
    for tag, a, b in (("knee", KNEE, KNEE_HOLD), ("land", LAND, LAND_HOLD)):
        worst, at = 0.0, None
        for index in range(a - START + 1, b - START + 1):
            step, pos = _worst_step(samples, index - 1, index)
            if step > worst:
                worst, at = step, pos
        windows[tag] = {"frames": [a, b], "worst_step_deg": round(worst, 5),
                        "at": at}
    res["dft_hitstop_windows"] = windows
    res["dft_hitstop_ok"] = bool(all(
        w["worst_step_deg"] <= HITSTOP_MAX_DEG for w in windows.values()))
    res["dft_hitstop_note"] = (
        "★ 两个窗口 [%d,%d] / [%d,%d] 各 **4 帧**（清单 §6 要 2~4 帧）。"
        "载体 = **窗口内逐帧姿态**（不是位移）——`E09_TP_NOHITSTOP=1` 让姿态在窗口内"
        "每帧漂 1.5° ⟹ 必须见红（≥ %.2f°）。" % (KNEE, KNEE_HOLD, LAND,
                                                LAND_HOLD, HITSTOP_MAX_DEG))

    # ---- ⑤ 伏地呼吸（载体 = 胸骨顶 z）------------------------------------
    sternum = [(s["frame"], Vector(s["neck"]).z) for s in samples
               if s["frame"] >= LAND_HOLD]
    zs = [v for _f, v in sternum]
    res["dft_breath_mm"] = round((max(zs) - min(zs)) * 1000.0, 3)
    mean = sum(zs) / float(len(zs))
    dev = [v - mean for v in zs]
    cross = sum(1 for i in range(1, len(dev))
                if (dev[i - 1] > 0.0) != (dev[i] > 0.0))
    res["dft_breath_crossings"] = cross
    res["dft_breath_ok"] = bool(BREATH_RANGE[0] <= res["dft_breath_mm"]
                                <= BREATH_RANGE[1] and cross >= BREATH_MIN_CROSS)
    res["dft_breath_note"] = (
        "★ 伏地呼吸载体 = 胸骨顶（`neck` = chest.tail）世界 z；幅 %.0f~%.0f mm、"
        "过零 ≥ %d（%g 周期 ⟹ 端点归零）。包络是**半波** `(1−cos)/2` ∈ [0,1]"
        "（0 = 呼气基线 = 触地定格姿，1 = 吸气顶）—— 实测 `sin` 的负半周会把"
        "`Hair_Mass` 压到 −22.29 mm，故呼吸只朝**抬升**方向做功。"
        "★ SOUL 铁律：**E09 是「战败但活着」**"
        "—— 倒地后**必须有呼吸证据**，尸体（零微动）是 E10 `Death` 的职责。"
        % (BREATH_RANGE[0], BREATH_RANGE[1], BREATH_MIN_CROSS, BREATH_CYCLES))

    # ---- ⑥ 收招不许瞬停 + 过缝 -------------------------------------------
    snap, snap_at = 0.0, None
    for index in range(max(1, len(samples) - 8), len(samples)):
        step, at = _worst_step(samples, index - 1, index)
        if step > snap:
            snap, snap_at = step, at
    res["no_snap_stop_step_deg"] = round(snap, 4)
    res["no_snap_stop_at"] = snap_at
    res["no_snap_stop_ok"] = bool(snap <= NO_SNAP_END_DEG)

    # ---- ⑦ 穿模（臂 vs 头盒 + 臂 vs 腿）----------------------------------
    worst_clip, clip_at = 0.0, None
    worst_limb, limb_at = 1e9, None
    scan = sorted(set(list(range(START, END + 1, 3)) + [KNEE, KNEEL_TAIL,
                                                        LAND, END]))
    for frame in scan:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        clip = PD.clip_metrics(arm)
        if clip["clip_max_mm"] > worst_clip:
            worst_clip, clip_at = clip["clip_max_mm"], (frame, clip["clip_at"])
        limb = limb_clearance(arm)
        if limb < worst_limb:
            worst_limb, limb_at = limb, frame
    res["clip_max_mm"] = round(worst_clip, 2)
    res["clip_at"] = clip_at
    res["no_face_clip_ok"] = bool(worst_clip <= CLIP_MAX_MM)
    res["hand_leg_clearance_mm"] = round(worst_limb, 2)
    res["hand_leg_clearance_frame"] = limb_at
    res["hand_leg_no_clip_ok"] = bool(worst_limb >= 0.0)

    # ---- ⑧ 可达性（全程）-------------------------------------------------
    worst_leg, worst_leg_at = 0.0, None
    worst_arm, worst_arm_at = 0.0, None
    for frame in range(START, END + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        for side in SIDES:
            hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
            ankle = Vector(A.bone_world(arm, "foot." + side, "head"))
            ratio = (ankle - hip).length / ((A.L_THIGH + A.L_SHIN)
                                            * REACH_MAX_RATIO)
            if ratio > worst_leg:
                worst_leg, worst_leg_at = ratio, (frame, side)
            sh = Vector(A.bone_world(arm, "upperarm." + side, "head"))
            fist = Vector(A.bone_world(arm, "hand." + side, "tail"))
            r2 = (fist - sh).length / ((ARM_LEN_UP + ARM_LEN_LO)
                                       * REACH_MAX_RATIO)
            if r2 > worst_arm:
                worst_arm, worst_arm_at = r2, (frame, side)
    res["leg_reach_ratio_max"] = round(worst_leg, 5)
    res["leg_reach_at"] = worst_leg_at
    res["leg_reach_ok"] = bool(worst_leg <= 1.0)
    res["arm_reach_ratio_max"] = round(worst_arm, 5)
    res["arm_reach_at"] = worst_arm_at
    res["arm_reach_ok"] = bool(worst_arm <= 1.0)

    # ---- ⑨ 相位标记 ------------------------------------------------------
    res["phase_markers"] = {"START": START, "ANTIC_END": 16, "KNEE": KNEE,
                            "KNEE_HOLD_END": KNEE_HOLD,
                            "KNEEL_TAIL": KNEEL_TAIL, "LAND": LAND,
                            "LAND_HOLD_END": LAND_HOLD, "END": END}
    res["phase_note"] = (
        "★ 本支不是攻击，但按 SOUL「动作必须有前摇/命中/后摇」拆："
        "前摇 0→%d（下沉屈膝）、**命中帧 1 = %d**（双膝触地 + 4 帧冻结）、"
        "后摇 %d→%d（跪姿失力）、**命中帧 2 = %d**（伏地触地 + 4 帧冻结）、"
        "**可取消帧 = %d**（触地定格之后即可接 E10/E11）、呼吸尾 %d→%d。"
        % (KNEE, KNEE, KNEE_HOLD, KNEEL_TAIL, LAND, LAND_HOLD + 1,
           LAND_HOLD, END))
    res["hold_window"] = [KNEE, KNEEL_TAIL]

    # ---- ⑩ ★ 终点真的是**伏地**吗？（本支的存在理由本身）------------------
    # 载体两个：① 胸骨顶（`neck`）从跪姿到尾帧的**落差**（抓「躯干整体落下去」）；
    #          ② 尾帧骨盆 z（抓「骨盆贴地」）。
    # ★ 为什么单开：`dft_final_pose_ok` 只证明「末帧 == 触地定格末帧」，是**自持性**，
    #   与「那一帧是不是伏地」正交。`E09_TP_NOFALL=1` 实测在原判据族下**全绿**
    #   （不倒地时 70 与 120 同为跪姿、同样逐位相同）⟹ 必须有本条兜底。
    stern_kneel = Vector(samples[KNEEL_TAIL - START]["neck"]).z
    stern_end = Vector(samples[END - START]["neck"]).z
    pel_end = Vector(samples[END - START]["pelvis"])
    res["dft_terminal_drop_mm"] = round((stern_kneel - stern_end) * 1000.0, 2)
    res["dft_terminal_pelvis_z_mm"] = round(pel_end.z * 1000.0, 2)
    res["dft_prone_ok"] = bool(
        res["dft_terminal_drop_mm"] >= TERMINAL_DROP_MIN_MM
        and res["dft_terminal_pelvis_z_mm"] <= TERMINAL_PELVIS_MAX_MM)
    res["dft_prone_note"] = (
        "★★★ **本支新增判据 ③**：本支是 E 族**第一支「带落地终点」**的动作，"
        "「终点是稳定的伏地姿」就是它相对 E01~E08 的全部差别。载体 = ① 胸骨顶"
        "（`neck` = chest.tail）世界 z 从 f%d 到 f%d 的**落差** ≥ %.0f mm"
        "（实测 %.2f）；② 尾帧骨盆世界 z ≤ %.0f mm（实测 %.2f）。"
        "★ 守卫 = `E09_TP_NOFALL=1` —— 它让本支退回「跪姿自持」，"
        "落差归 0 ⟹ 本判据必须见红（对照：`_e09_rv_NO_FALL.log` 在**旧**判据族下"
        "是全绿的，这正是本条被加进来的原因）。"
        % (KNEEL_TAIL, END, TERMINAL_DROP_MIN_MM, res["dft_terminal_drop_mm"],
           TERMINAL_PELVIS_MAX_MM, res["dft_terminal_pelvis_z_mm"]))

    # ---- ⑪ ★ 模型侧遗留的**量化入册**（不是本支的判据，是本支的告警）--------
    # `_probe_e09_unskinned.py` 实测：`Jacket_Hem` z [903.0, 926.0]、
    # `Jacket_Hem_Line` z [897.5, 901.5]，`vgroups=0` / `parent=None`，
    # f0 / f66 / f120 **逐位恒定** ⟹ 它们**不跟随骨架**（E04 起登记的跨支遗留）。
    # ★ 为什么现在要专门量它：E01~E08 角色全程**直立**，这两片贴在腰上「看起来是衣服」；
    #   本支人**躺平**后它仍停在 z = 0.90 m ⟹ 目检成**浮在空中的薄板**
    #   （`dftkey_three_quarter_f0066.png` 与 `Defeat_side_wide.mp4` 都能直接看到）。
    #   E10 `Death`（全身水平、零微动、且是**永久保持**态）会比本支更严重。
    # ★ 为什么不写成 `_ok` 判据：它是**上游资产缺陷**，本支无权修（§6 硬约束：
    #   绝不回写 `bigman_tpose_v001.blend`），写成门禁只会**红着卡住整条链**而修不好。
    #   按项目既有惯例（E04/E05/E08 对同一对象的处理）：**测量 + 入册 + 显式排除**，
    #   留给主人决策。这里把「悬空高度」量出来，让决策有数字。
    hem_z = min(prof[END].get("Jacket_Hem", 1e9),
                prof[END].get("Jacket_Hem_Line", 1e9))
    res["dft_hem_float_mm"] = round(hem_z - res["dft_body_low_min_mm"], 2)
    res["dft_hem_float_note"] = (
        "★★★ **本支第一次把这条模型侧遗留量化**：`Jacket_Hem` / `Jacket_Hem_Line`"
        "（未蒙皮，`probe_e09_unskinned.py` 实测 `vgroups=0`/`parent=null`/"
        "包围盒 f0=f66=f120 逐位恒定）在末帧悬于**全身最低件之上 %.0f mm**"
        "（衣摆 z = %.1f / 全身最低件 z = %.1f）。"
        "★ E01~E08 全程直立时它读作「衣服的一部分」；本支角色躺平后它读作"
        "**半空中的薄板**（目检证据：`dftkey_three_quarter_f0066.png`、"
        "`Defeat_side_wide.mp4`）。**E10 `Death` 会更严重**（水平尸体 + 零微动 + 永久保持）。"
        "★ 定性：**上游资产缺陷**，动画侧无权修（§6 禁止回写 tpose blend）"
        "⟹ 按 E04/E05/E08 惯例**测量入册 + 排除出像素判据**，升级为"
        "**待主人决策的高优项**（此前它是「美观」，现在是「两支动画的显形穿帮」）。"
        % (res["dft_hem_float_mm"], hem_z, res["dft_body_low_min_mm"]))
    return res


# =============================================================== 主流程
def boot():
    arm, meshes = A.open_animation_project()
    A.setup_scene()
    global BASE, KNEEL, TERM, BONE_LIST, ANKLE_REST
    if SEAM_ZERO:
        BASE = {}
        A.apply_pose(arm, BASE)
    else:
        BASE = IDLE.idle_pose(arm, 0.0)
    BONE_LIST = sorted(arm.pose.bones.keys())

    # ★ 站架踝（= 接缝入 `Idle_01@0` 的踝世界位置）：本支全部踝目标的基准 x/z。
    #   站架下鞋底 ≈ 0（实测 −0.96 ~ +1.1）⟹ **踝 z 不动 = 鞋底贴地不动**。
    A.apply_pose(arm, BASE)
    ANKLE_REST = {s: Vector(A.bone_world(arm, "foot." + s, "head"))
                  for s in SIDES}

    KNEEL = _blend_pose(BASE, {}, 0.0)      # 复制一份 BASE 的键集合
    KNEEL.update({
        "pelvis": (KNEEL_PELVIS_RX, 0.0, 0.0),
        "spine_01": (5.0, 0.0, 0.0), "spine_02": (5.0, 0.0, 0.0),
        "chest": (4.0, 0.0, 0.0),
        "neck": (14.0, 0.0, 0.0), "head": (12.0, 0.0, 0.0),
        "shoulder.L": (-26.0, 0.0, 0.0), "shoulder.R": (-26.0, 0.0, 0.0),
        # ★ 腿的四根骨只给**外展/占位**：rx 由 `lock_feet` 的 IK 逐帧覆盖。
        #   留着它们是为了让关键帧通道完整（`build_action` 取并集）。
        "thigh.L": (0.0, 0.0, -KNEEL_ABDUCT),
        "shin.L": (0.0, 0.0, 0.0),
        "foot.L": (0.0, 0.0, 0.0), "toe.L": (0.0, 0.0, 0.0),
        "thigh.R": (0.0, 0.0, KNEEL_ABDUCT),
        "shin.R": (0.0, 0.0, 0.0),
        "foot.R": (0.0, 0.0, 0.0), "toe.R": (0.0, 0.0, 0.0),
        "@loc": {"pelvis": A.wloc(0.0, 0.0, -KNEEL_DROP)},
    })

    TERM = _blend_pose(BASE, {}, 0.0)
    TERM.update({
        "pelvis": (TERM_PELVIS_RX, 0.0, 0.0),
        "spine_01": (TERM_REST_RX, 0.0, 0.0),
        "spine_02": (TERM_REST_RX, 0.0, 0.0),
        "chest": (TERM_REST_RX, 0.0, 0.0),
        "neck": (TERM_NECK_RX, 0.0, 0.0),
        "head": (TERM_HEAD_RX, TERM_HEAD_RY, 0.0),
        "shoulder.L": (-18.0, 0.0, 0.0), "shoulder.R": (-18.0, 0.0, 0.0),
        # ★ 同上：腿的 rx 由 IK 覆盖，这里只留外展与通道占位。
        "thigh.L": (0.0, 0.0, -TERM_ABDUCT),
        "shin.L": (0.0, 0.0, 0.0),
        "foot.L": (0.0, 0.0, 0.0), "toe.L": (0.0, 0.0, 0.0),
        "thigh.R": (0.0, 0.0, TERM_ABDUCT),
        "shin.R": (0.0, 0.0, 0.0),
        "foot.R": (0.0, 0.0, 0.0), "toe.R": (0.0, 0.0, 0.0),
        "@loc": {"pelvis": A.wloc(0.0, TERM_PELVIS_Y, TERM_PELVIS_Z - 0.900)},
    })
    return arm, meshes


def main():  # noqa: C901
    arm, meshes = boot()
    keyframes = [(frame, dft_pose(arm, frame))
                 for frame in range(START, END + 1)]
    meta = {
        "anim_id": NAME,
        "loop": False,
        "category": "状态与战斗流程",
        "note": ("战败：下沉跪落（膝触地 4 帧冻结）→ 跪姿失力 → 前扑伏地"
                 "（触地 4 帧冻结）→ 伏地呼吸 2 周期。起点 = Idle_01@0 逐位，"
                 "终点 = 稳定伏地 Pose（不是 Idle_01@0）"),
        "frame_bound_note": "★ 沿用 E01 登记的 E 族上界 120 帧 / 2.0 s",
        "hitstop_frames": "knee[28,32] land[66,70]",
        "seam_in": "Idle_01@0",
        "end_pose": "stable_prone_grounded",
        "kneel_drop_mm": round(KNEEL_DROP * 1000.0, 1),
        "terminal_pelvis_m": [TERM_PELVIS_Y, TERM_PELVIS_Z],
        "root_motion_m": [0.0, round(TERM_PELVIS_Y, 3)],
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    markers = {"START": START, "ANTIC_END": 16, "KNEE_HIT": KNEE,
               "KNEE_HOLD_END": KNEE_HOLD, "KNEEL_TAIL": KNEEL_TAIL,
               "LAND_HIT": LAND, "LAND_HOLD_END": LAND_HOLD,
               "CANCEL": LAND_HOLD + 1, "END": END}
    A.add_markers(action, markers)
    A.set_hitstop(action, KNEE, KNEE_HOLD)
    A.set_hitstop(action, LAND, LAND_HOLD)

    samples = A.sample_animation(arm, action, START, END, meshes)
    report = A.run_common_assertions(samples, meta, foot_probe=(),
                                     slide_tolerance_mm=KNEEL_FOOT_LOCK_MM)
    # ★ 通用 `ground_contact_ok` 的口径是「**鞋底** −2 ~ +6 mm」（站姿族）。本支末段
    #   是**伏地**：载体换成「**全身最低点**」⟹ 原判据在本支**不适用**，按项目既有
    #   惯例（非循环动作的 `loop_seamless` 报 `null`）**显式置空**，只把原读数与
    #   口径变更写进备注 —— 不是"删掉红灯"，是**换载体 + 留痕**。
    report["dft_common_ground_contact_raw"] = None
    a_low_sole_raw = report.pop("ground_contact_ok")
    report["dft_common_ground_contact_note"] = (
        "★ 原读数（鞋底口径 `ground_contact_ok`）= %r，**本支置空**：末段伏地时"
        "「鞋底」早已离地，不是本支的支撑面。替代判据 = `dft_body_ground_ok`"
        "（载体换成**全身最低件**，带 [%.0f, %.0f] mm）；跪姿段另有 "
        "`dft_knee_contact_ok`（载体 = 膝/小腿/鞋，带 [%.0f, %.0f] mm）。"
        % (a_low_sole_raw, BODY_BAND[0], BODY_BAND[1],
           KNEEL_BAND[0], KNEEL_BAND[1]))
    report.update(dft_assertions(arm, action, samples, meshes))

    # ---- 接缝入：首帧逐位 = Idle_01@0 ------------------------------------
    upstream = bpy.data.actions["Idle_01"]
    seam = world_mats(arm, upstream, 0)
    mine = world_mats(arm, action, START)
    worst_pos, worst_dir, worst_at = 0.0, 0.0, None
    for bone in BONE_LIST:
        if bone not in seam or bone not in mine:
            continue
        pos, deg = _mat_delta(mine[bone], seam[bone])
        if pos > worst_pos or deg > worst_dir:
            worst_at = bone
        worst_pos = max(worst_pos, pos)
        worst_dir = max(worst_dir, deg)
    report["seam_in_pos_max_mm"] = round(worst_pos, 6)
    report["seam_in_dir_max_deg"] = round(worst_dir, 6)
    report["seam_in_at"] = worst_at
    report["seam_in_ok"] = bool(worst_pos <= SEAM_POS_MAX_MM
                               and worst_dir <= SEAM_DIR_MAX_DEG)

    # ---- 终点自持：末帧 == 末帧（呼吸归零）⟹ 逐位稳定 ---------------------
    first = world_mats(arm, action, LAND_HOLD)
    last = world_mats(arm, action, END)
    end_elem, end_at = 0.0, None
    for bone in BONE_LIST:
        if bone in first and bone in last:
            for r in range(4):
                for c in range(4):
                    d = abs(first[bone][r][c] - last[bone][r][c])
                    if d > end_elem:
                        end_elem, end_at = d, (bone, r, c)
    report["dft_final_pose_elem_max"] = end_elem
    report["dft_final_pose_at"] = end_at
    report["dft_final_pose_ok"] = bool(end_elem <= FINAL_ELEM_MAX)
    report["dft_final_pose_note"] = (
        "★ 末帧（%d）与触地定格末帧（%d）**逐位一致** —— 呼吸在端点归零 ⟹ "
        "「伏地终点」是**稳定姿**（不是「停在半口气」）。"
        "`E09_TP_NOFALL=1` 抽掉前扑后末帧不再是伏地 ⟹ 本判据必须见红。"
        % (END, LAND_HOLD))

    # ---- 相位矩阵步长（防万向节假跳）-------------------------------------
    worst_m, worst_m_at = 0.0, None
    prev = world_mats(arm, action, START)
    for frame in range(START + 1, END + 1):
        cur = world_mats(arm, action, frame)
        for bone in BONE_LIST:
            if bone in prev and bone in cur:
                pos, deg = _mat_delta(cur[bone], prev[bone])
                if deg > worst_m:
                    worst_m, worst_m_at = deg, (frame, bone)
        prev = cur
    report["phase_matrix_step_deg"] = round(worst_m, 4)
    report["phase_matrix_step_at"] = worst_m_at
    report["phase_matrix_step_ok"] = bool(worst_m <= PHASE_MATRIX_STEP_DEG)

    report["meta"] = meta
    failed = sorted(k for k, v in report.items()
                    if k.endswith("_ok") and v is not True and v is not None)
    non_ok = sorted(k for k, v in report.items()
                    if isinstance(v, bool) and v is False)
    report["failed"] = failed
    report["non_ok_bools"] = non_ok
    A.report("E09_REPORT", report)

    if not SKIP_RENDER:
        key = [START, 8, 16, KNEE, KNEE_HOLD, 38, KNEEL_TAIL, 56, LAND,
               LAND_HOLD, 90, END]
        A.render_pose_sheet(arm, action, key, "dftkey",
                            views=(VIEW_E09_SIDE, VIEW_E09_FRONT, VIEW_E09_3Q))
        side = sorted(set(list(range(START, END + 1, 4)) + [END]))
        A.render_pose_sheet(arm, action, side, "dft",
                            views=(VIEW_E09_SIDE,))
        A.save_project()
        A.export_glb(arm)
    print("E09_DONE failed=%s non_ok=%s" % (failed, non_ok))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("E09_FAILURE " + traceback.format_exc())
