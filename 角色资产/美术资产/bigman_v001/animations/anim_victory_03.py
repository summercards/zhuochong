"""anim_victory_03 —— E08 `Victory_03` 胜利C（擦拳套）（E 族第八支 / 第 64 支）。

清单原文：「**胜利 C：擦拳套**」。

★★★ 开工第一件测量（`probe_e08_baseline.py` + `_e08_probe_clasp.py`，实测定标）：
    · 接缝：`Victory_02@120`（E07 末帧）vs `Idle_01@0` → **pos 8.7e-05 mm / dir 0.031°**；
      `Victory_01@120`（E06 末帧）同读数 ⟹ 三支首末帧逐位一致，**任意顺序连播无缝**。
    · 站架几何：双拳心 L (144.5, −307.7, 1271.1) / R (−129.6, −273.5, 1298.2) mm；
      拳心 x 间距 **274.1 mm**、**两拳网格最近距离 169.2 mm**（站架时双拳离得远）。
      手部网格盒 ≈ 100×140×140 mm；肩峰 z = 1312.9、x = ±150.7；臂长 up 328 / fo 224 / ha 98。
    · ★★★ **贴合不穿透的安全区实测**（`_e08_probe_clasp.py` 网格扫描）：
      双拳心摆到 **(x = ±48 mm, z = 1300 mm, y = −290 mm)** 时两拳网格最近带符号距离
      **+3.37 mm**（贴合、不穿透），L 离站架 102.3 mm、R 离站架 83.3 mm ⟹ 都在 ≤120 带内。
      ★ 间距灵敏度：x_half 每 +6 mm ⟹ gap +13 mm（x=60 时 12.34、x=75 时 34.0）
      ⟹ **x = ±48 是唯一能同时满足「贴合(≥−2)」且「不穿透(≤15)」的窄带**。
    · ★★★ **往复方向实测**（同脚本）：两拳是**圆头**，纯沿 z 反向滑（`dy0_dz16`）gap 立刻
      涨到 13.3 mm、且单次位移只有 16 mm；**斜向 (dy, dz) 反向擦**最稳：
      `dy24_dz10` → gap 10.23 mm、单次位移 26.0 mm；`dy28_dz6` → gap 11.08 mm、位移 28.6 mm。
      ⟹ 定稿取 **dy28_dz6**（位移 28.6 ≥ 25 下界，gap 11.08 ∈ [−2,15]，两侧余量都 ≥3.5 mm）。
    · ★ 第一拍（f12）位移：本支 **~41 mm**，而 E06 f14 = **255.6 mm**、E07 f14 = **580 mm**
      （均由探针实测）⟹ 三支第一拍是**三个量级**，连播不重影。

★★★ 本支的真风险（清单 §1 逐条落地）：
    ① ★★★ **命门是「小」，不是「大」** —— 全项目此前 62 支都在做「大幅度」，E08 是**唯一**
      要求「幅度收住」的动作。同时写**上界**与**下界**两条判据：
      · `v3_small_amp_ok`（★ 拳心**总行程** ≤ 120 mm）= 上界 ⟹ 防「又写成摆臂庆祝」；
      · `v3_min_amp_ok`（★ **单次往复位移** ≥ 25 mm）= 下界 ⟹ 防「收太死、读不出擦」。
      ★ 行程的**口径**：本支取「擦拳套手势窗 = [START, SETTLE_1]」内**拳心轨迹的直径**
        （任意两帧拳心最大间距）。★ 为什么不取全场：`HERO`（f80）按清单要求把双拳
        **收在体侧**（离 clasp 区 ~150 mm），若把 HERO 也纳入直径，则 120 mm 上界与
        「双拳握在体侧」在几何上**互斥**（数学上不可同时满足）。手势窗口径是本支
        「擦」这个动作的诚实度量；HERO 是**另起一段**的收势，单独由躯干/头判据管。
    ② ★★★ **手 vs 手自接触**（本支**第一次出现**）：写新探针 `hand_vs_hand_gap()`——
      口径照抄 `fist_face_gap`，只把参照物从 `TORSO` 换成**对侧手的 BVH**；左右手**互为目标**
      （A 查 B、B 查 A 取较小），且用射线奇偶判定穿透（带符号）。
    ③ ★★ **三次往复的相位对称**：擦拳套是**镜像往复**⟹ STROKE_1 与 STROKE_2 必须互为镜像。
      判据 `v3_stroke_sym_ok` = 逐个相邻极值对 `max |pose(f_k) − mirror(pose(f_{k+1}))|`。
    ④ **接缝三连**：E06 / E07 / E08 首末帧逐位 = `Idle_01@0`（`seam_in_ok` / `end_matches_start_ok`）。
    ⑤ **与 E06/E07 的语汇分离**（四维）：高度（本支拳心 z ∈ [1150,1450] = 胸/下巴之间，
      E06 ≤1392、E07 ≥1900）、幅度（本支 ≤120 vs E06 255 / E07 744）、接触对象
      （本支 **拳↔拳**、E06 拳↔躯干、E07 无接触）、往复次数（本支 ≥3、E06 3、E07 0）。

★★★ 工程件：十一段结构（120 帧 = 2.0 s，★ = E01 登记的 120 帧上界，**显式声明**）
    `START(0) → DIP(12) → CLASP(24) → STROKE_1(32) → STROKE_2(40) → STROKE_3(48)
      → SETTLE_1(60) → HERO(80) → HERO_HOLD(92) → SETTLE(110) → END(120)`
    · `DIP` = **原地小幅下压 18 mm**（★ 比 E06 的 34 / E07 的 55 都小）+ 双拳靠向中线；
    · `CLASP` = 双拳并拢到胸前中线（两拳网格间隙 **+3.4 mm**，贴合不穿透）；
    · `STROKE_1/2/3` = ★ 三次**镜像往复**（斜向 dy28/dz6，间隔 8 帧，L/R 反向）；
    · `HERO/HERO_HOLD` = 挺胸 + 下巴上扬 + **双拳收在体侧**（12 帧稳住不动）；
    · 段间缓动：`swing`（梯形速度）用于三个往复键 —— 端点速度 0 ⟹ 每个往复**读得出拐点**、
      且 `matrix_step` 天然小；`DIP → CLASP` 用 `smooth`。
    · ★★ **没有 hitstop**（`HOLDS = ()`）：擦拳套不是打击，没有「打击停顿」。
      判据 `v3_hitstop_ok` 是**反向守卫**（不许出现 ≥3 帧的冻结窗）。

★★★ 臂：**双臂同时动**（与 E07 的「单臂 + 另一臂守位」结构相反）⟹ E07 的
    `GUARD_HAND_RIGID` / `OFFHAND_MODE = "guard"` **必须关掉**（那两条是为「守位手」
    设计的；本支两手都是主动手，守位口径会让 R 臂变成僵尸臂）。本支两手都走 `FIST_TABLE`。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python anim_victory_03.py
    SKIP_RENDER=1      只跑门禁不渲图（迭代用）
    E08_TRACE=1        逐帧打印 骨盆位移 / 拳心 / 脚锁误差 / env

反向验证（§4 第 6 步，16 组，每组必须**真的把对应判据变红**）：
    E08_TP_SEAM_ZERO=1    ① 首帧改零位                ⟹ `seam_in_ok`
    E08_TP_AMP_X2=1       ② ★★★ 往复幅度放大 2 倍      ⟹ `v3_small_amp_ok`
    E08_TP_AMP_ZERO=1     ③ ★★★ 往复幅度归零           ⟹ `v3_min_amp_ok`/`v3_stroke_count_ok`
    E08_TP_NO_CLASP=1     ④ ★★★ 两拳不并拢（离 100mm）⟹ `v3_hand_gap_ok`
    E08_TP_OVERLAP=1      ⑤ ★★★ 两拳过度靠拢（穿透）  ⟹ `v3_hand_gap_ok`
    E08_TP_HIGH=1         ⑥ ★★ 拳抬到下巴以上         ⟹ `v3_clasp_z_ok`
    E08_TP_LOW=1          ⑦ ★★ 拳压到胸以下           ⟹ `v3_clasp_z_ok`
    E08_TP_STROKE1=1      ⑧ ★★ 只做 1 次往复           ⟹ `v3_stroke_count_ok`
    E08_TP_ASYMM=1        ⑨ ★★ 三次往复同向（不镜像）  ⟹ `v3_stroke_sym_ok`
    E08_TP_ADDHITSTOP=1   ⑩ ★ 加 4 帧定格（真加键行）  ⟹ `v3_hitstop_ok`
    E08_TP_BIGFIRST=1     ⑪ ★★ 第一拍照抄 E06 大位移   ⟹ `v3_firstbeat_small_ok`
    E08_TP_SLUMP=1        ⑫ ★ 不挺胸（含胸）           ⟹ `v3_chest_puff_ok`
    E08_TP_NOCHIN=1       ⑬ ★ 下巴不上扬              ⟹ `v3_chin_up_ok`
    E08_TP_TREMBLE=1      ⑭ ★ 英雄姿颤抖              ⟹ `v3_hero_hold_ok`
    E08_TP_FOOTSWAY=1     ⑮ ★ 脚滑（骑骨盆）           ⟹ `foot_lock_ok`
    E08_TP_LOOPBREAK=1    ⑯ ★ 末帧不闭合              ⟹ `end_matches_start_ok`
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

NAME = "Victory_03"
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"
SIDES = ("L", "R")
ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")
ARM_SET = set(ARM_BONES)
ARM_LEN_UP = 0.328
FOREARM_LEN = 0.224          # 前臂骨长（肘 → 腕）
ARM_TOTAL = ARM_LEN_UP + FOREARM_LEN + 0.098
HAND_LEN = 0.098

TORSO_MESH = "Suit_Torso"
HAND_PREFIX = ("Hand_Palm_", "Finger_", "Thumb_")
HEAD_PREFIX = ("Head", "Hair_", "Ear_", "Nose", "Eye_", "Iris_", "Pupil_",
               "Eyelid_", "Eyebrow_", "Glasses_", "Mouth", "Lower_Lip",
               "Lash")


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


def _env_b(key):
    return os.environ.get(key, "0").strip() not in ("", "0", "false", "False")


# =============================================================== 接缝
# ★ 上游 = `Idle_01@0`（本支自己测过：`probe_e08_baseline.py` → 8.7e-05 mm / 0.031°）。
SEAM_ACTION = os.environ.get("E08_SEAM_ACTION", "Idle_01")
SEAM_FRAME = _env_i("E08_SEAM_FRAME", 0)

# =============================================================== 时间轴（120 帧 = 2.0 s）
# ★★ 帧预算：120 帧 = 2.0 s = E01 登记的**上界** ⟹ 沿用（**显式声明**）。
TOTAL = _env_i("E08_TOTAL", 120)
START = 0
END = TOTAL

# ★★ 本支**没有打击停顿**（擦拳套不是打击）。`HOLDS` 恒为空 ⟹ `v3_hitstop_ok` 是**反向守卫**。
HITSTOP_N = 0
DIP = _env_i("E08_DIP", 12)                   # 原地小幅下压（≤20 mm）+ 双拳靠向中线
CLASP = _env_i("E08_CLASP", 24)               # 双拳并拢到胸前中线（贴合不穿透）
STROKE_1 = _env_i("E08_STROKE1", 32)          # ★ 第一次往复（L 下 / R 上）
STROKE_2 = _env_i("E08_STROKE2", 40)          # 第二次往复（反镜像）
STROKE_3 = _env_i("E08_STROKE3", 48)          # 第三次往复（同 STROKE_1）
SETTLE_1 = _env_i("E08_SETTLE1", 60)          # 拳分开、回胸侧
HERO = _env_i("E08_HERO", 80)                 # 收成英雄姿（挺胸 + 下巴上扬 + 双拳收体侧）
HERO_HOLD = _env_i("E08_HOLD", 92)            # ★ 英雄姿保持（80~92 几乎不动）
SETTLE = _env_i("E08_SETTLE", 110)            # 回站架途中
HOLDS = ()

# 臂包络（★ `ARM_DN_AT` 必须 ≥ `HERO_HOLD`，否则英雄姿窗口内臂仍在变 ⟹ 判红；
#          `ARM_DN_DONE` 必须 ≤ 110（早于 no_snap_stop 的 f110~120 判定窗））
ARM_UP_AT = _env_i("E08_ARM_UP", 10)
ARM_DN_AT = _env_i("E08_ARM_DN", 92)
ARM_DN_DONE = _env_i("E08_ARM_DONE", 110)

# =============================================================== 反向验证旋钮
SEAM_ZERO = _env_b("E08_TP_SEAM_ZERO")        # ① 首帧改零位
AMP_X2 = _env_b("E08_TP_AMP_X2")              # ② ★★★ 往复幅度放大 2 倍
AMP_ZERO = _env_b("E08_TP_AMP_ZERO")          # ③ ★★★ 往复幅度归零
NO_CLASP = _env_b("E08_TP_NO_CLASP")          # ④ ★★★ 两拳不并拢
OVERLAP = _env_b("E08_TP_OVERLAP")            # ⑤ ★★★ 两拳过度靠拢（穿透）
HIGH = _env_b("E08_TP_HIGH")                  # ⑥ ★★ 拳抬到下巴以上
LOW = _env_b("E08_TP_LOW")                    # ⑦ ★★ 拳压到胸以下
STROKE1 = _env_b("E08_TP_STROKE1")            # ⑧ ★★ 只做 1 次往复
ASYMM = _env_b("E08_TP_ASYMM")                # ⑨ ★★ 三次往复同向（不镜像）
# ★★★ `ADD_HITSTOP` **必须定义在 `KEYS` 之前**（E03~E07 的实测教训：只在 `main()`
#   里把 `set_hitstop` 关掉，姿态仍是冻结的 ⟹ 旋钮**惰性**）。忠实仿真 = **真加键行**。
ADD_HITSTOP = _env_b("E08_TP_ADDHITSTOP")
HITSTOP_ADD_N = _env_i("E08_HITSTOP_ADD_N", 4)
BIGFIRST = _env_b("E08_TP_BIGFIRST")          # ⑪ ★★ 第一拍照抄 E06 大位移
SLUMP = _env_b("E08_TP_SLUMP")                # ⑫ 不挺胸
NO_CHIN = _env_b("E08_TP_NOCHIN")             # ⑬ 下巴不上扬
TREMBLE = _env_b("E08_TP_TREMBLE")            # ⑭ 英雄姿颤抖
FOOT_SWAY = _env_b("E08_TP_FOOTSWAY")         # ⑮ 脚滑（骑骨盆）
LOOP_BREAK = _env_b("E08_TP_LOOPBREAK")       # ⑯ 末帧不闭合
FOOT_SWAY_MM = _env_f("E08_FOOT_SWAY_MM", 120.0)

# =============================================================== 数值（米）
# ★★★ clasp 锚点：由 `_e08_probe_clasp.py` 网格扫描实测 —— x=±48, z=1.300, y=−0.290
#   ⟹ 两拳网格最近带符号距离 **+3.37 mm**（贴合不穿透）。
CLASP_X = _env_f("E08_CLASP_X", 0.048)
CLASP_Y = _env_f("E08_CLASP_Y", -0.290)
CLASP_Z = _env_f("E08_CLASP_Z", 1.300)
# ★★ 往复：斜向 (dy, dz) 反向擦（实测 dy28_dz6 → gap 11.08、位移 28.6）。
STROKE_DY = _env_f("E08_STROKE_DY", 0.028)
STROKE_DZ = _env_f("E08_STROKE_DZ", 0.006)

if AMP_X2:
    STROKE_DY *= 2.0
    STROKE_DZ *= 2.0
if AMP_ZERO:
    STROKE_DY = 0.0
    STROKE_DZ = 0.0
if NO_CLASP:
    CLASP_X = 0.100          # ④ 两拳离 200 mm ⟹ 网格间隙 ≫15 ⟹ `v3_hand_gap_ok` 红
if OVERLAP:
    CLASP_X = 0.030          # ⑤ 两拳离 60 mm ⟹ 网格互相穿透 ⟹ 带符号间隙 < −2
if HIGH:
    CLASP_Z = 1.520          # ⑥ 抬到下巴以上（>1450）⟹ `v3_clasp_z_ok` 红
if LOW:
    CLASP_Z = 1.060          # ⑦ 压到胸以下（<1150）⟹ `v3_clasp_z_ok` 红

# 站架 → 靠拢的中途点（DIP）。
# ★ ⑪ `BIGFIRST`：把 DIP 照抄成 E06 的「拳收向前下方」（位移 255 mm）。
#   ★★★ DIP 目标的由来（实测）：站架双拳**不对称** —— L 拳 (144.5, −307.7, 1271.1)、
#     R 拳 (−129.6, **−273.5**, 1298.2)：R 拳比 L 拳**靠后 34 mm、高 27 mm**（护位姿态
#     的产物）。首版把 DIP 做成「双拳同时内收」⟹ R 拳心仅前移到 −288 ⟹ 手骨方向
#     （拳沿前臂）指向躯干中心 ⟹ 指尖戳进胸腔 **−12.5 mm**（`victory_hand_no_pierce_ok` 红）。
#     ⟹ 定稿：DIP 把**两拳都推到同一「身前深度」y ≈ −306**（R 手前伸 32.5 mm、
#     左移 7.6 mm、下压 26 mm），内收量从小（18.5 / 7.6 mm）⟹ 指尖全程在身前。
#     ★ 位移仍只有 ~42 mm（判据 ≤70，且远小于 E06 的 255.6）。
if BIGFIRST:
    DIP_L = Vector((0.290, -0.310, 1.061))
    DIP_R = Vector((-0.290, -0.310, 1.061))
else:
    DIP_L = Vector((_env_f("E08_DIP_LX", 0.126),
                    _env_f("E08_DIP_LY", -0.306),
                    _env_f("E08_DIP_LZ", 1.260)))
    DIP_R = Vector((_env_f("E08_DIP_RX", -0.122),
                    _env_f("E08_DIP_RY", -0.306),
                    _env_f("E08_DIP_RZ", 1.272)))


def _side_pos(cx, cy, cz, side):
    """把「左半边的坐标」按侧镜像（x 取负）。"""
    return Vector((cx if side == "L" else -cx, cy, cz))


def _stroke_ab(side):
    """返回 (A, B) —— 一次往复的两个端点（L: A 向前下 / B 向后上；R 相反）。"""
    sgn = +1.0 if side == "L" else -1.0
    a = Vector((CLASP_X if side == "L" else -CLASP_X,
                CLASP_Y - sgn * STROKE_DY, CLASP_Z - sgn * STROKE_DZ))
    b = Vector((CLASP_X if side == "L" else -CLASP_X,
                CLASP_Y + sgn * STROKE_DY, CLASP_Z + sgn * STROKE_DZ))
    return a, b


def _fist_table():
    """按相位给出**固定世界**拳心目标（米）。★ 本支左右手**都是主动手**（无守位手）。"""
    table = {
        "DIP": {"L": DIP_L.copy(), "R": DIP_R.copy()},
        "CLASP": {"L": _side_pos(CLASP_X, CLASP_Y, CLASP_Z, "L"),
                  "R": _side_pos(CLASP_X, CLASP_Y, CLASP_Z, "R")},
        "SETTLE_1": {"L": Vector((0.135, -0.290, 1.255)),
                     "R": Vector((-0.133, -0.284, 1.260))},
        "HERO": {"L": Vector((_env_f("E08_HERO_LX", 0.200),
                              _env_f("E08_HERO_LY", -0.230),
                              _env_f("E08_HERO_LZ", 1.160))),
                 "R": Vector((-_env_f("E08_HERO_LX", 0.200) + 0.004,
                              _env_f("E08_HERO_LY", -0.230),
                              _env_f("E08_HERO_LZ", 1.160)))},
        "SETTLE": {"L": Vector((0.150, -0.300, 1.262)),
                   "R": Vector((-0.146, -0.292, 1.268))},
    }
    # ★ 三次往复：S1 = A（L 向前下 / R 向后上），S2 = 反镜像（左右交换），S3 = 同 S1。
    a_l, b_l = _stroke_ab("L")
    a_r, b_r = _stroke_ab("R")
    s1 = {"L": a_l.copy(), "R": a_r.copy()}
    s2 = {"L": b_l.copy(), "R": b_r.copy()}
    s3 = {"L": a_l.copy(), "R": a_r.copy()}
    if ASYMM:
        # ⑨ ★★ 三次往复**不镜像**：把 S2 的 R 手钉在 S1 的位置（只有 L 在动）
        #   ⟹ 极值仍是 3 个（`v3_stroke_count_ok` 保持绿），但相邻极值对**互不镜像**
        #   （偏差 56 mm ≫ 容差 3 mm）⟹ **只有** `v3_stroke_sym_ok` 红。
        s2 = {"L": b_l.copy(), "R": a_r.copy()}
        s3 = {"L": a_l.copy(), "R": a_r.copy()}
    if STROKE1:
        # ⑧ 只做 1 次往复：S2 / S3 全部塌回 S1 ⟹ 极值只剩 1 个 ⟹ `v3_stroke_count_ok` 红。
        s2 = {"L": a_l.copy(), "R": a_r.copy()}
        s3 = {"L": a_l.copy(), "R": a_r.copy()}
    table["STROKE_1"] = s1
    table["STROKE_2"] = s2
    table["STROKE_3"] = s3
    return table


FIST_TABLE = _fist_table()
# ★★ 肘的固定世界极向量：擦拳套时双肘**外张 + 略下**（不是 E07 的「向后」）。
ELBOW_DIR = {"L": Vector((0.86, 0.34, -0.42)),
             "R": Vector((-0.86, 0.34, -0.42))}

# ★★ 拳**面**朝向混合：本支 = **0.0**（拳沿前臂）—— 与 E06 的 1.0 相反。
#   理由：擦拳套是「拳套互相摩擦」，拳轴与臂轴同向才是「拳套外缘互擦」。
FIST_FACE_BLEND = 0.0
FACE_RAMP_IN = (0, 1)
FACE_RAMP_OUT = (TOTAL - 1, TOTAL)

# ★★ 手心**滚转基准**：`thumb_out`（±X 体侧外）。
HAND_AXIS_MODE = os.environ.get("E08_HAND_AXIS", "thumb_out")
HAND_CHIRALITY = {"L": 1.0, "R": 1.0}
TWIST_SPLIT = _env_f("E08_TWIST_SPLIT", 0.6)
FOREARM_TWIST_DEG = _env_f("E08_FOREARM_TWIST", 0.0)
BULGE_MAX_DEG = _env_f("E08_BULGE_MAX", 8.0)
HAND_MAX_DEG = _env_f("E08_HAND_MAX", 12.0)
DIP_EASE = os.environ.get("E08_DIP_EASE", "swing")
SWING_EASE_A = _env_f("E08_SWING_A", 0.15)

# ★★★ 本支**双臂同时动** ⟹ E07 的「守位手」口径**必须关掉**。
#   `GUARD_HAND_RIGID` = 让非举起手整臂刚性跟随站架（本支无「非举起手」）；
#   `OFFHAND_MODE` = "guard"（守位）/ "sym"（两手都走 FIST_TABLE ⟹ 本支）。
GUARD_HAND_RIGID = False
OFFHAND_MODE = "sym"
# ★★★ 包络对**朝向**（手骨 y 轴 / 肘极）的收敛指数：见 `seat_arm` 的说明。
#   1.0 = 线性（E07 口径）；< 1.0 = 低 env 段更贴站架朝向 ⟹ 治「手在混合带戳胸」。
ENV_RATE_POW = _env_f("E08_ENV_POW", 0.4)
FIST_MIN_CLEAR_MM = _env_f("E08_FIST_CLEAR", 20.0)
ARM_SOLVE_ITERS = max(1, _env_i("E08_ARM_ITERS", 3))
EULER_BLEND_AT = _env_f("E08_EULER_AT", 0.0)

# =============================================================== 躯干规格
# ★ 量纲：**全部是相对站架的增量**，3 元组 (rx, ry, rz)（度）；未列出的骨 = 站架值。
#   `loc` = (世界 dy, 世界 dz)（米）：+dy = 身后，+dz = 上。
#   ★★ `ry` 全程 = 0（照 E06/E07：腰扭转会破坏往复的镜像性）。
SPECS = {
    "STATION": {"pelvis": (0.0, 0.0, 0.0), "spine_01": (0.0, 0.0, 0.0),
                "spine_02": (0.0, 0.0, 0.0), "chest": (0.0, 0.0, 0.0),
                "neck": (0.0, 0.0, 0.0), "head": (0.0, 0.0, 0.0),
                "shoulder.L": (0.0, 0.0, 0.0), "shoulder.R": (0.0, 0.0, 0.0),
                "loc": (0.0, 0.0)},
    # ★★ DIP：**原地小幅下压 ~18 mm**（★ ≤20 上界；E06 是 34、E07 是 55）+ 双肩微前送。
    #   第一拍位移目标 ~42 mm ⟹ 比 E06 的 255.6 / E07 的 580 小一个量级。
    "DIP": {"pelvis": (2.4, 0.0, 0.0), "spine_01": (1.2, 0.0, 0.0),
            "spine_02": (1.2, 0.0, 0.0), "chest": (1.4, 0.0, 0.0),
            "neck": (1.0, 0.0, 0.0), "head": (1.6, 0.0, 0.0),
            "shoulder.L": (-4.0, 0.0, 4.0), "shoulder.R": (-4.0, 0.0, -4.0),
            "loc": (0.010, -0.018)},
    # ★ CLASP：双拳并拢到胸前中线；躯干**基本站直**（擦拳套不借躯干大动作）。
    "CLASP": {"pelvis": (-0.4, 0.0, 0.0), "spine_01": (-0.4, 0.0, 0.0),
              "spine_02": (-0.6, 0.0, 0.0), "chest": (-1.2, 0.0, 0.0),
              "neck": (-1.4, 0.0, 0.0), "head": (-3.4, 0.0, 0.0),
              "shoulder.L": (2.0, 0.0, -2.0), "shoulder.R": (2.0, 0.0, 2.0),
              "loc": (0.0, -0.008)},
    "STROKE_1": {"pelvis": (-0.5, 0.0, 0.0), "spine_01": (-0.4, 0.0, 0.0),
                 "spine_02": (-0.7, 0.0, 0.0), "chest": (-1.4, 0.0, 0.0),
                 "neck": (-1.6, 0.0, 0.0), "head": (-3.8, 0.0, 0.0),
                 "shoulder.L": (2.2, 0.0, -2.2),
                 "shoulder.R": (2.2, 0.0, 2.2), "loc": (0.0, -0.005)},
    "STROKE_2": {"pelvis": (-0.5, 0.0, 0.0), "spine_01": (-0.4, 0.0, 0.0),
                 "spine_02": (-0.7, 0.0, 0.0), "chest": (-1.4, 0.0, 0.0),
                 "neck": (-1.6, 0.0, 0.0), "head": (-3.8, 0.0, 0.0),
                 "shoulder.L": (2.2, 0.0, -2.2),
                 "shoulder.R": (2.2, 0.0, 2.2), "loc": (0.0, -0.005)},
    "STROKE_3": {"pelvis": (-0.5, 0.0, 0.0), "spine_01": (-0.4, 0.0, 0.0),
                 "spine_02": (-0.7, 0.0, 0.0), "chest": (-1.4, 0.0, 0.0),
                 "neck": (-1.6, 0.0, 0.0), "head": (-3.8, 0.0, 0.0),
                 "shoulder.L": (2.2, 0.0, -2.2),
                 "shoulder.R": (2.2, 0.0, 2.2), "loc": (0.0, -0.005)},
    # ★ SETTLE_1：拳分开、回胸侧；躯干几乎回正。
    "SETTLE_1": {"pelvis": (0.2, 0.0, 0.0), "spine_01": (0.0, 0.0, 0.0),
                 "spine_02": (0.0, 0.0, 0.0), "chest": (-0.6, 0.0, 0.0),
                 "neck": (-0.6, 0.0, 0.0), "head": (-1.6, 0.0, 0.0),
                 "shoulder.L": (0.8, 0.0, -0.8),
                 "shoulder.R": (0.8, 0.0, 0.8), "loc": (0.0, -0.002)},
    # ★★ HERO：挺胸 + 下巴上扬 11° + 双肩后张下沉（拳收体侧）。
    #   ★★★ 为什么 chest 增量取 **−4.6** 而不是清单草拟的 −3.5：本支**实测了站架基线**
    #     —— `Idle_01@0` 的 `chest rx` 本身就带 **+1.0°**（前倾），判据 `v3_chest_puff_ok`
    #     读的是**绝对值**（≤ −2.5 ⟹ 与 E07 同口径），故增量必须比「目标读数」再深
    #     1.0°。−4.6 + 1.0 = **−3.6** ⟹ 过线且留 1.1° 余量。
    #     ★ 这不是放宽阈值（阈值恒 −2.5），而是**把动作做够**。
    "HERO": {"pelvis": (-1.2, 0.0, 0.0), "spine_01": (-1.4, 0.0, 0.0),
             "spine_02": (-2.2, 0.0, 0.0), "chest": (-4.6, 0.0, 0.0),
             "neck": (-4.0, 0.0, 0.0), "head": (-7.0, 0.0, 0.0),
             "shoulder.L": (6.0, 0.0, 9.0), "shoulder.R": (6.0, 0.0, -9.0),
             "loc": (0.004, 0.004)},
    # ★ 英雄姿保持（80~92）：与 HERO 只差不到 0.1°/0.1 mm ⟹ 读作「稳住不动」。
    "HERO_HOLD": {"pelvis": (-1.1, 0.0, 0.0), "spine_01": (-1.4, 0.0, 0.0),
                  "spine_02": (-2.1, 0.0, 0.0), "chest": (-4.5, 0.0, 0.0),
                  "neck": (-3.9, 0.0, 0.0), "head": (-6.9, 0.0, 0.0),
                  "shoulder.L": (5.8, 0.0, 8.8), "shoulder.R": (5.8, 0.0, -8.8),
                  "loc": (0.0036, 0.0036)},
    # 回站架途中（残余极小 ⟹ 尾段角步自然收敛）
    "SETTLE": {"pelvis": (0.4, 0.0, 0.0), "spine_01": (0.2, 0.0, 0.0),
               "spine_02": (0.2, 0.0, 0.0), "chest": (0.3, 0.0, 0.0),
               "neck": (-0.2, 0.0, 0.0), "head": (-0.5, 0.0, 0.0),
               "shoulder.L": (1.6, 0.0, 2.4), "shoulder.R": (1.6, 0.0, -2.4),
               "loc": (0.002, -0.003)},
}

_CELEB = ("HERO", "HERO_HOLD")


def spec_of(name):
    spec = dict(SPECS[name])
    if SLUMP and name in _CELEB:
        # ⑫ 不挺胸：把胸从后仰（−3.5）拨到前倾（+3），头也压下来一点。
        rx, ry, rz = spec["chest"]
        spec["chest"] = (3.0, ry, rz)
        nrx, nry, nrz = spec["neck"]
        spec["neck"] = (2.0, nry, nrz)
    if NO_CHIN and name in _CELEB:
        # ⑬ 下巴不上扬：颈 / 头的上扬增量全部清零（只剩站架基线）。
        spec["neck"] = (0.0, 0.0, 0.0)
        spec["head"] = (0.0, 0.0, 0.0)
    return spec


# =============================================================== 关键帧表
#   (帧, 进入本键所用的缓动, 躯干规格名, 拳目标名)
KEYS = [
    (START, None, "STATION", "STATION"),
    (DIP, DIP_EASE, "DIP", "DIP"),
    (CLASP, "smooth", "CLASP", "CLASP"),
]
if ADD_HITSTOP:
    # ⑩ 真加键行：CLASP 后接 HITSTOP_ADD_N 帧定格 ⟹ `v3_hitstop_ok` 红。
    KEYS.append((CLASP + HITSTOP_ADD_N - 1, "hold", "CLASP", "CLASP"))
KEYS += [
    (STROKE_1, "swing", "STROKE_1", "STROKE_1"),
    (STROKE_2, "swing", "STROKE_2", "STROKE_2"),
    (STROKE_3, "swing", "STROKE_3", "STROKE_3"),
    (SETTLE_1, "smooth", "SETTLE_1", "SETTLE_1"),
    (HERO, "smooth", "HERO", "HERO"),
    (HERO_HOLD, "smooth", "HERO_HOLD", "HERO"),
    (SETTLE, "smooth", "SETTLE", "SETTLE"),
    (END, "smooth", "STATION", "STATION"),
]

# =============================================================== 阈值
# ★ 全部由**设计意图 + 实测定**；铁律：不许为了变绿而放宽。
AMP_MAX_MM = _env_f("E08_AMP_MAX", 120.0)      # ★ 上界（三支里最小）
AMP_MIN_MM = _env_f("E08_AMP_MIN", 25.0)       # ★ 下界（防收太死）
STROKE_COUNT_MIN = _env_i("E08_STROKE_MIN", 3)  # ★ ≥3 次往复
STROKE_SYM_TOL_MM = _env_f("E08_STROKE_SYM", 3.0)
GAP_BAND = (_env_f("E08_GAP_LO", -2.0), _env_f("E08_GAP_HI", 15.0))
CLASP_Z_BAND = (_env_f("E08_CLASP_Z_LO", 1150.0),
                _env_f("E08_CLASP_Z_HI", 1450.0))
FIRSTBEAT_MAX_MM = _env_f("E08_FIRSTBEAT_MAX", 70.0)
HITSTOP_WIN_MAX = _env_i("E08_HITSTOP_WIN_MAX", 2)   # 允许 ≤2 帧／0 个窗
PUFF_MAX_RX = _env_f("E08_PUFF_RX", -2.5)
CHIN_RANGE = (_env_f("E08_CHIN_LO", 8.0), _env_f("E08_CHIN_HI", 24.0))
NO_ROAR_MAX = _env_f("E08_ROAR_MAX", 26.0)
HERO_STEP_MAX_DEG = _env_f("E08_HERO_STEP", 1.6)
HERO_MIN_FRAMES = _env_i("E08_HERO_N", 12)
FOOT_LOCK_MM = _env_f("E08_FOOT_LOCK", 0.5)
SOLE_BAND = (-2.0, 6.0)
NO_SNAP_END_DEG = _env_f("E08_SNAP_END", 6.0)
SEAM_POS_MAX_MM = _env_f("E08_SEAM_POS", 0.01)
SEAM_DIR_MAX_DEG = _env_f("E08_SEAM_DIR", 0.05)
CLIP_MAX_MM = _env_f("E08_CLIP_MAX", 0.0)
REACH_MAX_RATIO = 0.995
MATRIX_STEP_MAX_DEG = _env_f("E08_MATSTEP", 25.0)
TAIL_SETTLE_N = _env_i("E08_TAIL_N", 10)
HAND_PIERCE_MM = _env_f("E08_HAND_PIERCE", 10.0)
HAND_X_HINT_MIN_MARGIN = _env_f("E08_HINT_MARGIN", 0.45)

# 出图/像素探针共用的**逐帧集合**（主渲 / 反面重渲 / 像素探针三者必须逐帧相同）
STEM_FRAMES = sorted(set([0, 6, 12, 18, 24, 28, 32, 36, 40, 44, 48, 54, 60,
                          68, 74, 80, 86, 92, 100, 106, 110, 115, 120]))

# =============================================================== 取景（★ 本支自立）
# ★ 本支**不跳不躺、拳不过顶**：纵向最低 = 鞋底 0、最高 = 头顶 ≈ 1803 + 发梢
#   （≈ 1870 mm）⟹ 纵向覆盖 −0.15 ~ 2.05 m（中心 z = 0.95、正交高 2.20 m）；
#   横向需 ≥ ±0.45 m ⟹ 正面 770×1080（横 = 2.20×770/1080 = 1.569 m）。
VIEW_E08_SIDE = ("side", (4.4, -0.05, 0.95), (0.0, -0.05, 0.95), 2.20,
                 (770, 1080))
VIEW_E08_FRONT = ("front", (0.0, -4.9, 0.95), (0.0, 0.0, 0.95), 2.20,
                  (770, 1080))

TRACE = _env_b("E08_TRACE")
_BLEND_TRACE = _env_b("E08_TRACE_BLEND")
_BLEND2_TRACE = _env_b("E08_TRACE_BLEND2")
DEBUG_FRAMES = set(int(x) for x in os.environ.get("E08_DBG", "").split(",")
                   if x.strip())
DEBUG_SIDES = set(x.strip() for x in os.environ.get("E08_DBG_SIDE",
                                                    "L,R").split(",")
                  if x.strip())
IK_TRACE = _env_b("E08_TRACE_IK")
_STEP_TRACE = _env_b("E08_TRACE_STEP")

# =============================================================== 模块级表
BASE = {}
ANCHOR = {}
STATION_FIST = {}
BONE_LIST = []
TORSO = None
STATION_PIERCE = {"L": {}, "R": {}}
STATION_HAND_Y = {}
STATION_HAND_X = {}
STATION_POLE_DIR = {}
LAST_FOREARM_TWIST = {}
LAST_HAND_FRAME = {}
PELVIS0 = None
MIN_HINT_MARGIN = 1.0
LAST_HAND_X = {}
DEBUG_HOME = {}
DEBUG_ITER = -1


# =============================================================== 缓动
def _smoothstep(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3.0 - 2.0 * x)


def _ease(kind, t):
    t = max(0.0, min(1.0, t))
    if kind == "hold":
        return 0.0 if t < 1.0 else 1.0
    if kind == "accel":
        return t * t
    if kind == "decel":
        return 1.0 - (1.0 - t) * (1.0 - t)
    if kind == "linear":
        return t
    if kind == "swing":
        # ★★ 梯形速度：峰值斜率 1/(1−a)，端点斜率恒 0 ⟹ 往复的拐点读得出来。
        a = max(1e-4, min(0.45, SWING_EASE_A))
        k = 1.0 / (a * (1.0 - a))
        if t <= a:
            return 0.5 * k * t * t
        if t >= 1.0 - a:
            return 1.0 - 0.5 * k * (1.0 - t) * (1.0 - t)
        return 0.5 * k * a * a + k * a * (t - a)
    return _smoothstep(t)


def _segment(frame):
    """返回 (i, t, ease_kind) —— frame 落在 KEYS[i] .. KEYS[i+1] 之间。"""
    for index in range(len(KEYS) - 1):
        f0 = KEYS[index][0]
        f1 = KEYS[index + 1][0]
        if f0 <= frame <= f1:
            span = float(max(1, f1 - f0))
            return index, (frame - f0) / span, (KEYS[index + 1][1] or "smooth")
    return len(KEYS) - 2, 1.0, KEYS[-1][1]


def torso_at(frame):
    index, t, kind = _segment(frame)
    a = spec_of(KEYS[index][2])
    b = spec_of(KEYS[index + 1][2])
    g = _ease(kind, t)
    out = {}
    for key in a:
        if key == "loc":
            out["loc"] = tuple(x + (y - x) * g for x, y in zip(a["loc"],
                                                               b["loc"]))
        else:
            out[key] = tuple(x + (y - x) * g for x, y in zip(a[key], b[key]))
    return out


def arm_env(frame):
    """臂包络：`env` 只在 `(ARM_UP_AT, ARM_DN_AT)` 区间内为 1，两端分别归 0。

    ★ `env→0` 时 `seat_arm` 会把 IK 解的肘极向量 / 拳轴 / 滚转基准**逐位收敛到
      站架实测值** ⟹ 接缝帧（f=0 / f=120）逐位等于站架。
    ★★ `ARM_DN_AT` = 92 = `HERO_HOLD` ⟹ 英雄姿窗口（80~92）内 `env ≡ 1`（零变化）；
      `ARM_DN_DONE` = 110 **早于** `no_snap_stop_ok` 的判定窗（f110~120）。
    """
    if frame <= ARM_UP_AT:
        return _smoothstep(frame / float(max(1, ARM_UP_AT)))
    if frame >= ARM_DN_AT:
        span = float(max(1, ARM_DN_DONE - ARM_DN_AT))
        return _smoothstep((ARM_DN_DONE - frame) / span)
    return 1.0


def face_blend(frame):
    """本支 `FIST_FACE_BLEND = 0` ⟹ 恒 0（拳沿前臂）。"""
    return 0.0


def seam_canonicalize(keyframes):
    """把整条欧拉曲线按**轴的 360° 整数倍**整体平移，使**末帧 == 首帧**（E03 教训）。"""
    if not keyframes:
        return keyframes
    first, last = keyframes[0][1], keyframes[-1][1]
    shift = {}
    for name, angles in first.items():
        if name.startswith("@"):
            continue
        tail = last.get(name)
        if tail is None:
            continue
        delta = [round((b - a) / 360.0) * 360.0
                 for a, b in zip(angles, tail)]
        if any(abs(d) > 1e-9 for d in delta):
            shift[name] = delta
    if not shift:
        return keyframes
    out = []
    for frame, pose in keyframes:
        new_pose = dict(pose)
        for name, delta in shift.items():
            if name in new_pose:
                new_pose[name] = tuple(v - d
                                       for v, d in zip(new_pose[name], delta))
        out.append((frame, new_pose))
    return out


def _euler_family(angles):
    """XYZ 欧拉的**严格等价族**（54 个候选，矩阵严格相同；第 0 位 = 原始表示）。"""
    out = []
    for base in (tuple(angles),
                 (angles[0] + 180.0, 180.0 - angles[1], angles[2] + 180.0)):
        for kx in (0, -1, 1):
            for ky in (0, -1, 1):
                for kz in (0, -1, 1):
                    out.append((base[0] + 360.0 * kx, base[1] + 360.0 * ky,
                                base[2] + 360.0 * kz))
    return out


def compat_euler(keyframes):
    """欧拉表示兼容化（C14 / D01 / E03~E07 踩过的同一个万向节锁坑）。

    ★★★ 做法：**穷举等价表示 + min-max 瓶颈 DP** 求「最小化最大单轴步」的全局最优
      路径；两端**钉死在原始表示**上。★ 这一步**不改变任何姿态**（等价表示 ⟹
      同一旋转矩阵），只改变键上的数字。
    """
    fams_per_name = {}
    for name in keyframes[0][1]:
        if name.startswith("@"):
            continue
        raw = [pose.get(name, (0.0, 0.0, 0.0)) for _f, pose in keyframes]
        spread = max(max(abs(a - b) for a, b in zip(x, y))
                     for x in raw for y in raw)
        if spread < 1e-9:
            fams_per_name[name] = [[tuple(raw[0])] for _ in range(len(raw))]
            continue
        fams_per_name[name] = [_euler_family(a) for a in raw]

    n = len(keyframes)
    chosen = {}
    for name, fams in fams_per_name.items():
        count = len(fams[0])
        if count == 1:
            chosen[name] = [fams[i][0] for i in range(n)]
            continue
        best = [max(abs(b - a) for a, b in zip(fams[0][j], fams[0][0]))
                for j in range(count)]
        back = [[0] * count]
        for i in range(1, n):
            row, prev_row = fams[i], fams[i - 1]
            cur = [None] * count
            prv = [0] * count
            for j in range(count):
                b0, b1, b2 = row[j]
                bk, bv = 0, None
                for k in range(count):
                    p0, p1, p2 = prev_row[k]
                    s0 = b0 - p0
                    if s0 < 0.0:
                        s0 = -s0
                    s1 = b1 - p1
                    if s1 < 0.0:
                        s1 = -s1
                    s2 = b2 - p2
                    if s2 < 0.0:
                        s2 = -s2
                    step = s0 if s0 > s1 else s1
                    if s2 > step:
                        step = s2
                    value = best[k] if best[k] > step else step
                    if bv is None or value < bv:
                        bk, bv = k, value
                cur[j], prv[j] = bv, bk
            best, back = cur, back + [prv]
        # ★★★ 终点必须与**首帧同基**（只差 360° 整数倍），否则 `seam_canonicalize`
        #   搬不回去。
        raw_first, raw_last = fams[0][0], fams[-1][0]
        same_pose = max(abs(a - b)
                        for a, b in zip(raw_first, raw_last)) < 1e-6
        cand = list(range(27)) if (same_pose and count >= 54) else [0]
        j = min(cand, key=lambda idx: best[idx])
        seq = [j]
        for i in range(n - 1, 0, -1):
            j = back[i][j]
            seq.append(j)
        seq.reverse()
        chosen[name] = [fams[i][seq[i]] for i in range(n)]
        chosen[name][0] = fams[0][0]

    out = []
    for i, (frame, pose) in enumerate(keyframes):
        new_pose = dict(pose)
        for name, picks in chosen.items():
            new_pose[name] = picks[i]
        out.append((frame, new_pose))
    return out


# =============================================================== 脚锁（全程）
def lock_feet(arm, pose, want, iters=8, damp=0.85):
    """把双踝**闭环**钉在 `want`（世界坐标 dict）上，就地改 `pose`。

    ★★ **本支是「全程」口径**（E08 不跳、不位移）：`want` 恒 = 站架踝
      ⟹ 脚从头到尾钉死不动（`foot_lock_ok` ≤ 0.5 mm）。
    """
    tgt = {s: Vector(want[s]) for s in SIDES}
    rz = {s: pose.get("thigh." + s, (0.0, 0.0, 0.0))[2] for s in SIDES}
    pelvis_rx = pose.get("pelvis", (0.0, 0.0, 0.0))[0]
    worst = 0.0
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
            pose["foot." + side] = A.keep_world_orientation(arm, "foot." + side)
        A.apply_pose(arm, pose)
        for side in SIDES:
            err = Vector(A.bone_world(arm, "foot." + side, "head")) - want[side]
            tgt[side] = tgt[side] - err * damp
            rz[side] = rz[side] + (1.0 / 0.01309) * err.x * damp
            worst = max(worst, err.length * 1000.0)
    return worst


# =============================================================== 躯干几何查询
def _torso_eval():
    depsgraph = bpy.context.evaluated_depsgraph_get()
    ev = TORSO.evaluated_get(depsgraph)
    return ev, ev.matrix_world.copy()


def torso_query(point):
    """点到躯干面的 (带符号距离 mm, 面上最近点, 外法线)。"""
    ev, mw = _torso_eval()
    _ok, loc, nrm, _idx = ev.closest_point_on_mesh(mw.inverted() @ Vector(point))
    world_loc = mw @ loc
    world_nrm = (mw.to_3x3() @ nrm).normalized()
    gap = (Vector(point) - world_loc).dot(world_nrm) * 1000.0
    return gap, world_loc, world_nrm


def signed_to_torso(point):
    return torso_query(point)[0]


def push_out(point, min_gap_mm):
    """把拳目标**顶出**胸腔（沿胸面外法线），只在该点比下限更深时才动它。"""
    gap, surf, nrm = torso_query(point)
    if gap >= min_gap_mm:
        return Vector(point)
    return surf + nrm * (min_gap_mm / 1000.0)


# ---------------------------------------------------------------- 手 vs 躯干
INSIDE_RAYS = []
for _j in range(13):
    _a = 2.0 * math.pi * _j / 13.0
    _z = 1.0 - 2.0 * (_j + 0.5) / 13.0
    _r = math.sqrt(max(0.0, 1.0 - _z * _z))
    INSIDE_RAYS.append(Vector((math.cos(_a) * _r, math.sin(_a) * _r,
                               _z)).normalized())
INSIDE_VOTES_MIN = _env_i("E08_INSIDE_VOTES", 7)
_BVH = {"tree": None}


def torso_bvh():
    if _BVH["tree"] is None:
        import mathutils.bvhtree as bvhtree
        deps = bpy.context.evaluated_depsgraph_get()
        _BVH["tree"] = bvhtree.BVHTree.FromObject(TORSO, deps)
    return _BVH["tree"]


def torso_bvh_reset():
    _BVH["tree"] = None


def _ray_parity(tree, point, direction):
    origin = Vector(point)
    hits = 0
    for _ in range(64):
        loc, _normal, index, distance = tree.ray_cast(origin, direction)
        if loc is None or index is None:
            break
        hits += 1
        origin = loc + direction * max(1e-7, distance * 1e-6 + 1e-7)
    return hits % 2 == 1


def inside_votes(point, tree=None):
    """点沿 13 个方向各打一条射线，返回**得票数**（全票 13 = 内部）。"""
    tree = tree if tree is not None else torso_bvh()
    return sum(1 for d in INSIDE_RAYS if _ray_parity(tree, point, d))


def inside_torso(point, tree=None):
    return inside_votes(point, tree) >= INSIDE_VOTES_MIN


def hand_mesh_points(side, step=3):
    """[(世界坐标, 对象名)] —— 该侧手部全部网格顶点（含对象名，用于分部位）。"""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    out = []
    for obj in bpy.data.objects:
        if obj.type != "MESH" or not obj.name.endswith("_" + side):
            continue
        if not any(obj.name.startswith(p) for p in HAND_PREFIX):
            continue
        ev = obj.evaluated_get(depsgraph)
        me = ev.to_mesh()
        mw = ev.matrix_world
        for index in range(0, len(me.vertices), step):
            out.append((mw @ me.vertices[index].co, obj.name))
        ev.to_mesh_clear()
    return out


def fist_face_gap(side, step=2):
    """**指节面**（`Finger_*` 顶点）到躯干面的**最小带符号距离**（mm）。"""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    worst = None
    for obj in bpy.data.objects:
        if obj.type != "MESH" or not obj.name.endswith("_" + side):
            continue
        if not obj.name.startswith("Finger_"):
            continue
        ev = obj.evaluated_get(depsgraph)
        me = ev.to_mesh()
        mw = ev.matrix_world
        for index in range(0, len(me.vertices), step):
            gap = signed_to_torso(mw @ me.vertices[index].co)
            if worst is None or gap < worst:
                worst = gap
        ev.to_mesh_clear()
    return None if worst is None else round(worst, 3)


def hand_mesh_stats(side, tree=None, step=3, limit_mm=None):
    """该侧手网格 vs **躯干**的几何读数（排除拇指的口径是判据，拇指单独登记）。"""
    tree = tree if tree is not None else torso_bvh()
    pts = hand_mesh_points(side, step=step)
    inside, inside_nothumb, thumb = 0, 0, 0
    beyond = 0
    deepest, deepest_nothumb = None, None
    for point, name in pts:
        is_thumb = name.startswith("Thumb_")
        gap = signed_to_torso(point)
        if deepest is None or gap < deepest:
            deepest = gap
        if not is_thumb and (deepest_nothumb is None or gap < deepest_nothumb):
            deepest_nothumb = gap
        if limit_mm is not None and not is_thumb and gap < -float(limit_mm):
            beyond += 1
        if inside_torso(point, tree):
            inside += 1
            if is_thumb:
                thumb += 1
            else:
                inside_nothumb += 1
    return {"inside": inside, "inside_nothumb": inside_nothumb,
            "thumb": thumb, "n": len(pts), "beyond_limit": beyond,
            "deepest_mm": round(deepest, 2) if deepest is not None else None,
            "deepest_nothumb_mm": (round(deepest_nothumb, 2)
                                   if deepest_nothumb is not None else None)}


# ---------------------------------------------------------------- 手 vs 手（★ 本支新增）
_H2H_RAYS = (Vector((0.0, 0.0, 1.0)),
             Vector((0.9397, 0.3420, 0.0)),
             Vector((0.3420, -0.9397, 0.0)).normalized())
_H2H_CACHE = {}


def hand_geo(side, step=4):
    """该侧手部网格的 (BVH, 顶点列表)。★ 与躯干无关 —— 是**手自己的**几何。"""
    key = (side, step)
    cached = _H2H_CACHE.get(key)
    if cached is not None:
        return cached
    import mathutils.bvhtree as bvhtree
    depsgraph = bpy.context.evaluated_depsgraph_get()
    verts, polys = [], []
    for obj in bpy.data.objects:
        if obj.type != "MESH" or not obj.name.endswith("_" + side):
            continue
        if not any(obj.name.startswith(p) for p in HAND_PREFIX):
            continue
        ev = obj.evaluated_get(depsgraph)
        me = ev.to_mesh()
        mw = ev.matrix_world
        base = len(verts)
        verts.extend([mw @ v.co for v in me.vertices])
        for poly in me.polygons:
            polys.append([base + i for i in poly.vertices])
        ev.to_mesh_clear()
    tree = bvhtree.BVHTree.FromPolygons(verts, polys) if verts else None
    picked = list(verts)[::step]
    _H2H_CACHE[key] = (tree, picked)
    return tree, picked


def hand_geo_reset():
    _H2H_CACHE.clear()


def _inside_bvh(tree, point):
    """射线奇偶（3 向投票，≥2 = 内部）—— 判定点是否落在**对侧手**网格内。"""
    votes = 0
    for direction in _H2H_RAYS:
        if _ray_parity(tree, point, direction):
            votes += 1
    return votes >= 2


def hand_vs_hand_gap(step=4):
    """★ 两拳网格的**最近带符号距离**（mm）。

    ★★★ 口径照抄 `fist_face_gap`：只把参照物从 `TORSO` 换成**对侧手的 BVH**。
      · 左右手**互为目标**（A 查 B、B 查 A，两次读数取较小）；
      · 符号 = 射线奇偶（点落在对侧手内部 ⟹ 负 = 穿透）；
      · **排除自己**的网格（只读另一侧）。
    ⟹ 返回 (min_gap_mm, who, at_point)。贴合不穿透 ⟹ 期望 ∈ [−2, 15]。
    """
    trees, pts = {}, {}
    for side in SIDES:
        trees[side], pts[side] = hand_geo(side, step=step)
    worst, who, at = None, None, None
    for side, other in (("L", "R"), ("R", "L")):
        tree = trees.get(other)
        if tree is None:
            continue
        for point in pts.get(side, ()):
            loc, _nrm, _idx, dist = tree.find_nearest(point)
            if loc is None:
                continue
            gap = dist * 1000.0
            if _inside_bvh(tree, point):
                gap = -gap
            if worst is None or gap < worst:
                worst, who, at = gap, "%s->%s" % (side, other), point.copy()
    if worst is None:
        return None, None, None
    return round(worst, 3), who, at


# =============================================================== 方向 / 手骨朝向
def _slerp_dir(d1, d2, t):
    """单位方向 d1 → d2 的**测地线**混合（显式处理 d1≈±d2 两个退化点）。"""
    a = Vector(d1).normalized()
    b = Vector(d2).normalized()
    t = max(0.0, min(1.0, float(t)))
    if t <= 0.0:
        return a
    if t >= 1.0:
        return b
    cos_t = max(-1.0, min(1.0, a.dot(b)))
    theta = math.acos(cos_t)
    if theta < 1e-4:
        return a
    axis = a.cross(b)
    if axis.length < 1e-6:
        axis = a.cross(Vector((0.0, 0.0, 1.0)))
        if axis.length < 1e-6:
            axis = a.cross(Vector((0.0, 1.0, 0.0)))
    axis.normalize()
    out = Matrix.Rotation(theta * t, 4, axis) @ a
    out.normalize()
    return out


def hand_x_hint(side, normal):
    """给出「`hand.local_x` 应指向的世界方向」——**平行移动优先**（E07 定稿口径）。"""
    prev = LAST_HAND_X.get(side)
    if prev is not None:
        return Vector(prev)
    chirality = HAND_CHIRALITY[side]
    if HAND_AXIS_MODE == "outward":
        return Vector(normal) * chirality
    if HAND_AXIS_MODE == "inward":
        return -Vector(normal) * chirality
    if HAND_AXIS_MODE == "thumb_up":
        return Vector((0.0, 0.0, 1.0)) * chirality
    if HAND_AXIS_MODE == "thumb_dn":
        return Vector((0.0, 0.0, -1.0)) * chirality
    return Vector((1.0, 0.0, 0.0)) * chirality       # thumb_out（默认）


def orient_hand(arm, side, y_dir, x_hint):
    """用**显式正交基**摆 `hand.<side>`：`local_y` = `y_dir`，`local_x` 尽量贴 `x_hint`。"""
    global MIN_HINT_MARGIN
    pose_bone = arm.pose.bones["hand." + side]
    y_axis = Vector(y_dir).normalized()
    hint = Vector(x_hint)
    x_axis = hint - y_axis * hint.dot(y_axis)
    MIN_HINT_MARGIN = min(MIN_HINT_MARGIN, x_axis.length)
    if x_axis.length < 1e-4:
        fallback = Vector((0.0, 0.0, 1.0))
        if abs(fallback.dot(y_axis)) > 0.99:
            fallback = Vector((0.0, 1.0, 0.0))
        x_axis = fallback - y_axis * fallback.dot(y_axis)
    x_axis.normalize()
    z_axis = x_axis.cross(y_axis)
    current = pose_bone.matrix.copy()
    basis = Matrix((x_axis, y_axis, z_axis)).transposed().to_4x4()
    # ★★★ 手掌世界朝向的逐帧限速：与**上一帧提交的朝向**比测地角，超限就 slerp 拉回。
    q_new = basis.to_quaternion()
    prev_q = LAST_HAND_Q.get(side)
    if prev_q is not None and HAND_MAX_DEG > 0.0:
        ang = prev_q.rotation_difference(q_new).angle
        if ang > math.pi:
            ang = 2.0 * math.pi - ang
        ang_deg = math.degrees(ang)
        if ang_deg > HAND_MAX_DEG:
            q_new = prev_q.slerp(q_new, HAND_MAX_DEG / ang_deg)
    q_new.normalize()
    FRAME_HAND_Q[side] = q_new.copy()
    basis = q_new.to_matrix().to_4x4()
    basis.translation = current.translation
    pose_bone.matrix = basis
    bpy.context.view_layer.update()
    LAST_HAND_FRAME[side] = (y_axis.copy(), x_axis.copy())
    return basis.to_3x3().col[0].normalized().copy()


# =============================================================== 臂 IK
ELBOW_POLE = {"L": Vector((0.86, 0.34, -0.42)),
              "R": Vector((-0.86, 0.34, -0.42))}
LAST_TWIST_ANGLE = {}
LAST_ELBOW = {}
LAST_BULGE = {}
LAST_REP = {}
LAST_BLENDED = {}
FRAME_ELBOW = {}
FRAME_BULGE = {}
FRAME_TWIST = {}
LAST_HAND_Q = {}
FRAME_HAND_Q = {}


def _bulge_dir(side, axis, shoulder):
    """肘的**极方向**（⊥ `axis` 的单位向量）—— 决定肘落在轴的哪一侧（E07 定稿口径）。"""
    pole = ELBOW_POLE[side]
    previous = LAST_ELBOW.get(side)
    if previous is not None:
        candidate = Vector(previous) - shoulder
        if candidate.length > 1e-4:
            pole = candidate
    bulge = pole - axis * pole.dot(axis)
    if bulge.length < 0.05:
        bulge = (ELBOW_POLE[side]
                 - axis * ELBOW_POLE[side].dot(axis))
        if bulge.length < 0.05:
            bulge = Vector((0.0, 1.0, 0.0)) - axis * axis.y
            if bulge.length < 0.05:
                bulge = Vector((0.0, 0.0, 1.0)) - axis * axis.z
    out = bulge.normalized()
    prev = LAST_BULGE.get(side)
    if prev is not None and BULGE_MAX_DEG > 0.0:
        p = Vector(prev) - axis * Vector(prev).dot(axis)
        if p.length > 1e-4:
            p.normalize()
            ang = math.degrees(math.acos(max(-1.0, min(1.0, out.dot(p)))))
            if ang > BULGE_MAX_DEG:
                out = _slerp_dir(p, out, BULGE_MAX_DEG / ang)
    FRAME_BULGE[side] = out.copy()
    return out


def seat_arm(arm, pose, targets, normals, blend=1.0, env=1.0):  # noqa: C901
    """把臂解到拳心目标上（结构照抄 E03/E06/E07 的成熟版）。★ 本支**两手都是主动手**。"""
    A.apply_pose(arm, pose)
    for side in SIDES:
        up, fo, hd = ("upperarm." + side, "forearm." + side, "hand." + side)
        shoulder = Vector(A.bone_world(arm, up, "head"))
        core = Vector(targets[side])
        nrm = Vector(normals.get(side, Vector((0.0, -1.0, 0.0)))).normalized()
        elbow_ref = FRAME_ELBOW.get(side)
        if elbow_ref is None:
            elbow_ref = LAST_ELBOW.get(side)
        if elbow_ref is None:
            elbow_ref = Vector(A.bone_world(arm, fo, "head"))
        along = core - Vector(elbow_ref)
        along = (along.normalized() if along.length > 1e-6
                 else Vector((0.0, 0.0, -1.0)))
        y_dir = _slerp_dir(along, -nrm, blend)
        if env < 1.0:
            # ★★★ 手骨朝向的包络收敛用 **env** 的次方**加速**（本支新增，E07 是线性 env）。
            #   为什么必须加速：`env` 很小时拳**位置**已几乎回到站架（目标点按 env 向
            #   `home` 收敛），但若朝向也按线性 env 混合，则 `along`（= 拳心 − 肘）仍
            #   占 78 % ⟹ 整只手比站架**多转 ~39°** ⟹ 指尖（离腕 ~150 mm）被推进胸腔。
            #   实测（首版）：f3 R 手深 **−14.46 mm**、f6 **−10.82**、f12 **−12.51**
            #   （站架基线 −4.05，下限 −10）⟹ `victory_hand_no_pierce_ok` 红。
            #   改法：权重取 `env ** ENV_RATE_POW`（0<pow<1 ⟹ 低 env 段更贴站架朝向）。
            #   端点性质不变：env=0 ⟹ 权重 0（逐位站架，接缝不受影响）；env=1 ⟹ 1。
            w = env if ENV_RATE_POW >= 1.0 else env ** ENV_RATE_POW
            y_dir = _slerp_dir(STATION_HAND_Y[side], y_dir, w)
        target = core - y_dir * HAND_LEN
        delta = target - shoulder
        # ★★★ 三角解**必须用前臂骨长**（224 mm），不是手 + 前臂（322）。
        limit = (ARM_LEN_UP + FOREARM_LEN) * 0.9995
        distance = max(1e-4, min(delta.length, limit))
        axis = (delta.normalized() if delta.length > 1e-9
                else Vector((0.0, 0.0, -1.0)))
        bulge = _bulge_dir(side, axis, shoulder)
        if env < 1.0:
            wb = env if ENV_RATE_POW >= 1.0 else env ** ENV_RATE_POW
            bulge = _slerp_dir(STATION_POLE_DIR[side], bulge, wb)
        cos_sh = max(-1.0, min(1.0, (ARM_LEN_UP ** 2 + distance ** 2
                                     - FOREARM_LEN ** 2)
                               / (2.0 * ARM_LEN_UP * distance)))
        sin_sh = math.sqrt(max(0.0, 1.0 - cos_sh * cos_sh))
        elbow = shoulder + (axis * cos_sh + bulge * sin_sh) * ARM_LEN_UP
        FRAME_ELBOW[side] = elbow.copy()
        pose[up] = A.aim_bone(arm, up, elbow - shoulder)
        fo_dir = target - elbow
        base_twist = FOREARM_TWIST_DEG * blend * HAND_CHIRALITY[side]
        pose[fo] = A.aim_bone(arm, fo, fo_dir, twist_deg=base_twist)
        hint = hand_x_hint(side, nrm)
        # ★★★ 腕部轴向滚转的**分配量**由**矩阵几何量**给出（**不读** `rotation_euler.y`）。
        x_axis = hint - y_dir * hint.dot(y_dir)
        if x_axis.length < 1e-4:
            _fb = Vector((0.0, 0.0, 1.0))
            if abs(_fb.dot(y_dir)) > 0.99:
                _fb = Vector((0.0, 1.0, 0.0))
            x_axis = _fb - y_dir * _fb.dot(y_dir)
        x_axis.normalize()
        pose[fo] = A.aim_bone(arm, fo, fo_dir, twist_deg=0.0)
        u = arm.pose.bones[fo].matrix.to_3x3().col[0].normalized()
        theta = math.degrees(math.atan2(u.cross(x_axis).dot(y_dir),
                                        max(-1.0, min(1.0,
                                                      u.dot(x_axis)))))
        prev_theta = FRAME_TWIST.get(side)
        if prev_theta is None:
            prev_theta = LAST_TWIST_ANGLE.get(side)
        if prev_theta is not None:
            theta += 360.0 * round((prev_theta - theta) / 360.0)
        FRAME_TWIST[side] = theta
        twist = TWIST_SPLIT * theta + base_twist
        pose[fo] = A.aim_bone(arm, fo, fo_dir, twist_deg=twist)
        LAST_HAND_X[side] = orient_hand(arm, side, y_dir, hint)
        LAST_FOREARM_TWIST[side] = twist
        if DEBUG_FRAMES and frame_is_debug(side):
            print("E08_DBG core=[%.1f,%.1f,%.1f] env=%.3f theta=%.2f"
                  % (core.x * 1000, core.y * 1000, core.z * 1000, env, theta))
        if IK_TRACE:
            _t = Vector(A.bone_world(arm, hd, "tail"))
            print("E08_IK %s core=[%.1f,%.1f,%.1f] tail=[%.1f,%.1f,%.1f] "
                  "dist=%.1f"
                  % (side, core.x * 1000, core.y * 1000, core.z * 1000,
                     _t.x * 1000, _t.y * 1000, _t.z * 1000, delta.length * 1000))
        pose[hd] = tuple(math.degrees(v)
                         for v in arm.pose.bones[hd].rotation_euler)
    return pose


# =============================================================== 拳目标
def resolve_fist(name, side):
    """拳心目标（世界，米）。本支**全部是固定世界点**。"""
    if name == "STATION":
        return Vector(STATION_FIST[side])
    return Vector(FIST_TABLE[name][side])


def _aim_world(name, side, root_off):
    """拳的**世界**目标点（唯一的「世界 vs 随骨盆」口径在这里定死）。"""
    return Vector(resolve_fist(name, side)) + root_off


def fist_targets(arm, frame, root_off, env=1.0, home=None):
    """拳目标 = **绕肩的球面插值**（方向 slerp + 半径缓动）+ **包络向站架拳收敛**。"""
    index, t, kind = _segment(frame)
    ga = _ease(kind, t)
    a_name = KEYS[index][3]
    b_name = KEYS[index + 1][3]
    env = max(0.0, min(1.0, float(env)))
    out = {}
    for side in SIDES:
        shoulder = Vector(A.bone_world(arm, "upperarm." + side, "head"))
        va = _aim_world(a_name, side, root_off) - shoulder
        vb = _aim_world(b_name, side, root_off) - shoulder
        ra, rb = va.length, vb.length
        if ra < 1e-6:
            dirv = vb.normalized()
        elif rb < 1e-6:
            dirv = va.normalized()
        else:
            dirv = _slerp_dir(va.normalized(), vb.normalized(), ga)
        point = shoulder + dirv * (ra + (rb - ra) * ga)
        if env < 1.0:
            anchor = Vector((home or STATION_FIST)[side])
            point = anchor + (point - anchor) * env
        point = push_out(point, FIST_MIN_CLEAR_MM)
        out[side] = point
    return out


# =============================================================== 姿态装配
def _nearest_family(angles, ref):
    """在 XYZ 欧拉的 54 个**严格等价表示**里，取「相对 `ref` 分量最大差最小」的那个。"""
    best, best_cost = None, None
    for cand in _euler_family(angles):
        cost = max(abs(c - r) for c, r in zip(cand, ref))
        if best_cost is None or cost < best_cost:
            best, best_cost = cand, cost
    return best


def _blend_local(station, ikpt, env):
    """臂的包络混合：**等价表示连续性优先 + 欧拉线性插值**（E07 定稿口径）。"""
    out = {}
    for name in ARM_BONES:
        a = tuple(station.get(name, (0.0, 0.0, 0.0)))
        b = tuple(ikpt.get(name, (0.0, 0.0, 0.0)))
        raw = max(0.0, min(1.0, float(env)))
        e = raw if EULER_BLEND_AT <= 0.0 else _smoothstep(raw / EULER_BLEND_AT)
        ref = LAST_BLENDED.get(name)
        pick = _nearest_family(b, a if ref is None else ref)
        if _BLEND_TRACE:
            print("E08_BLEND %-12s env=%.3f e=%.3f span=%.1f"
                  % (name, raw, e, max(abs(y - x) for x, y in zip(a, pick))))
        out[name] = tuple(x + (y - x) * e for x, y in zip(a, pick))
    return out


def frame_is_debug(side):
    return DEBUG_FRAMES and DEBUG_CUR in DEBUG_FRAMES and side in DEBUG_SIDES


DEBUG_CUR = -1


def victory_pose(arm, frame):  # noqa: C901
    global DEBUG_CUR
    DEBUG_CUR = frame
    spec = torso_at(frame)
    pose = {}
    for key in ("pelvis", "spine_01", "spine_02", "chest", "neck", "head",
                "shoulder.L", "shoulder.R"):
        va = BASE.get(key, (0.0, 0.0, 0.0))
        pose[key] = tuple(va[i] + spec[key][i] for i in range(3))
    # ★ ⑭ 英雄姿颤抖旋钮：在 HERO..HERO_HOLD 窗口内逐帧交替 ±3°（真接进姿态）。
    if TREMBLE and HERO <= frame <= HERO_HOLD:
        rx, ry, rz = pose["chest"]
        pose["chest"] = (rx + (3.0 if (frame % 2) else -3.0), ry, rz)
    base_loc = BASE.get("@loc", {}).get("pelvis", (0.0, 0.0, 0.0))
    dy, dz = spec["loc"]
    # ★ 骨骼局部 location：X→世界+X、**Y→世界+Z**、Z→世界−Y
    pose["@loc"] = {"pelvis": (base_loc[0],
                               base_loc[1] + dz,
                               base_loc[2] - dy)}
    for key, value in BASE.items():
        if key.startswith("@") or key in pose:
            continue
        pose[key] = tuple(value)
    pose["root"] = (0.0, 0.0, 0.0)
    pose.update(A.FIST)
    for key, value in BASE.items():
        if key in A.FIST:
            pose[key] = tuple(value)

    # ---- 腿：**全程脚锁**（want 恒 = 站架踝；本支不跳、不位移）---------------
    root_off = Vector((0.0, dy, dz))
    want = {s: Vector(ANCHOR[s]) for s in SIDES}
    if FOOT_SWAY:
        # ⑮ 脚滑：**脚不再锁世界，改骑在当前骨盆上**（躯干一动脚就跟着动）。
        A.apply_pose(arm, pose)
        delta = Vector(A.bone_world(arm, "pelvis", "head")) - PELVIS0
        scale = FOOT_SWAY_MM / 18.0
        for s in SIDES:
            want[s] = want[s] + delta * scale
    lock_err = lock_feet(arm, pose, want)

    # ---- 臂：解 IK，再按 `arm_env` 与站架臂混合（保证接缝）-------------------
    env = arm_env(frame)
    A.apply_pose(arm, pose)
    home = {s: Vector(A.bone_world(arm, "hand." + s, "tail")) for s in SIDES}
    targets = fist_targets(arm, frame, root_off, env, home)
    dummy = {s: Vector((0.0, -1.0, 0.0)) for s in SIDES}
    blended = None
    for _it in range(ARM_SOLVE_ITERS):
        DEBUG_ITER = _it
        ik_pose = dict(pose)
        seat_arm(arm, ik_pose, targets, dummy, face_blend(frame), env)
        blended = _blend_local(pose, ik_pose, env)
    for name in ARM_BONES:
        pose[name] = blended[name]
    # ★★ 跨帧状态**每帧提交一次**（帧内迭代收敛后）。
    for name in ARM_BONES:
        LAST_BLENDED[name] = tuple(pose[name])
    for side in SIDES:
        if side in FRAME_ELBOW:
            LAST_ELBOW[side] = FRAME_ELBOW[side]
        if side in FRAME_BULGE:
            LAST_BULGE[side] = FRAME_BULGE[side]
        if side in FRAME_TWIST:
            LAST_TWIST_ANGLE[side] = FRAME_TWIST[side]
        if side in FRAME_HAND_Q:
            LAST_HAND_Q[side] = FRAME_HAND_Q[side]
    FRAME_ELBOW.clear()
    FRAME_BULGE.clear()
    FRAME_TWIST.clear()
    FRAME_HAND_Q.clear()

    if LOOP_BREAK and frame == TOTAL:
        rx, ry, rz = pose["chest"]
        pose["chest"] = (rx + 4.0, ry, rz + 4.0)

    if TRACE:
        A.apply_pose(arm, pose)
        low = A.foot_lowest_by_side()
        soles = {s: round(low[s][2] * 1000.0, 1) for s in SIDES
                 if low[s] is not None}
        cores = {s: [round(v * 1000.0, 1)
                     for v in A.bone_world(arm, "hand." + s, "tail")]
                 for s in SIDES}
        print("E08_TRACE f=%3d dy=%+6.1f dz=%+6.1f sole=%s core=%s "
              "lock=%.4f env=%.3f" % (frame, dy * 1000.0, dz * 1000.0, soles,
                                      cores, lock_err, env))
    del lock_err
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


# =============================================================== 往复解析
def stroke_extrema(samples, idx):
    """在 [CLASP, SETTLE_1] 内找「两拳 y 相对偏移」u(f) 的极值 ⟹ 数出往复次数。

    u(f) = fistL.y − fistR.y。一次往复（L 前 R 后 → L 后 R 前）⟹ u 从 −A 摆到 +A。
    ★ 极值数 ≥ 3 ⟺ 至少 3 次往复（S1 极值 / S2 反极值 / S3 极值）。
    """
    frames = [f for f in range(CLASP, SETTLE_1 + 1)]
    vals = []
    for f in frames:
        s = samples[idx[f]]
        vals.append((Vector(s["hand.L.tail"]).y - Vector(s["hand.R.tail"]).y))
    ext = []
    for i in range(1, len(vals) - 1):
        if vals[i] > vals[i - 1] and vals[i] >= vals[i + 1]:
            ext.append((frames[i], +1))
        elif vals[i] < vals[i - 1] and vals[i] <= vals[i + 1]:
            ext.append((frames[i], -1))
    merged = []
    for frame, sgn in ext:
        i = frames.index(frame)
        if merged and merged[-1][1] == sgn:
            j = frames.index(merged[-1][0])
            if (sgn > 0 and vals[i] > vals[j]) or (sgn < 0 and vals[i] < vals[j]):
                merged[-1] = (frame, sgn)
        else:
            merged.append((frame, sgn))
    keep = []
    for frame, sgn in merged:
        if not keep:
            keep.append((frame, sgn))
            continue
        i, j = frames.index(frame), frames.index(keep[-1][0])
        if abs(vals[i] - vals[j]) >= 0.010:      # 死区 10 mm
            keep.append((frame, sgn))
    return keep, vals, frames


# =============================================================== 专属门禁
def victory_assertions(arm, action, samples, meshes):  # noqa: C901
    res = {}
    scene = bpy.context.scene
    frames = [s["frame"] for s in samples]
    idx = {s["frame"]: i for i, s in enumerate(samples)}
    arm.animation_data.action = action
    A._bind_slot(arm, action)

    def core(sample, side):
        return Vector(sample["hand." + side + ".tail"])

    def head_back_deg(frame):
        """仰头 / 下巴上扬角（度，**正 = 后仰**）= −(Δneck_rx + Δhead_rx)。"""
        e = samples[idx[frame]]["euler"]
        e0 = samples[0]["euler"]
        d_neck = (e.get("neck", (0.0, 0.0, 0.0))[0]
                  - e0.get("neck", (0.0, 0.0, 0.0))[0])
        d_head = (e.get("head", (0.0, 0.0, 0.0))[0]
                  - e0.get("head", (0.0, 0.0, 0.0))[0])
        return -(d_neck + d_head)

    def chest_rx_deg(frame):
        return samples[idx[frame]]["euler"].get("chest", (0.0, 0.0, 0.0))[0]

    # ---- ① ★★★ 行程上界（本支命门：小）------------------------------------
    #   口径 =「擦拳套手势窗 = [START, SETTLE_1]」内**拳心轨迹的直径**（任意两帧最大间距）。
    gest = list(range(START, SETTLE_1 + 1))
    pos_l = {f: core(samples[idx[f]], "L") for f in gest}
    pos_r = {f: core(samples[idx[f]], "R") for f in gest}
    diam, diam_at = 0.0, None
    for a in gest:
        for b in gest:
            d_l = (pos_l[a] - pos_l[b]).length * 1000.0
            d_r = (pos_r[a] - pos_r[b]).length * 1000.0
            d = max(d_l, d_r)
            if d > diam:
                diam, diam_at = d, (a, b)
    path_l = sum((pos_l[gest[i + 1]] - pos_l[gest[i]]).length * 1000.0
                 for i in range(len(gest) - 1))
    res["v3_amp_window"] = [START, SETTLE_1]
    res["v3_amp_diameter_mm"] = round(diam, 2)
    res["v3_amp_diameter_at"] = diam_at
    res["v3_amp_path_len_mm"] = round(path_l, 2)
    res["v3_amp_max_mm"] = AMP_MAX_MM
    res["v3_small_amp_ok"] = bool(diam <= AMP_MAX_MM)
    res["v3_small_amp_note"] = (
        "★★★ **本支的命门**：「擦拳套」是**小动作**，必须收住幅度。判据 = 手势窗 "
        "f=%d~%d 内拳心轨迹**直径**（任意两帧最大间距）≤ %.0f mm。实测 **%.1f mm**"
        "（@ f%s）；路径全长 %.1f mm。★ 对照：E06 锤击行程 **255.6 mm**、E07 全臂过顶 "
        "**744 mm** ⟹ 本支是三支里最小的一支（与目标「小一个量级」相符）。"
        "★ 口径说明：为什么不把 `HERO`(f%d) 纳入直径 —— 清单要求 HERO「双拳收在体侧」"
        "（离 clasp 区 ~150 mm），若纳入则 120 mm 上界与「握在体侧」在几何上互斥；"
        "HERO 是**另起一段的收势**，由躯干/头判据单独管。"
        "★ 旋钮 ② `AMP_X2` 把往复放大 2 倍 ⟹ 变红。"
        % (START, SETTLE_1, AMP_MAX_MM, diam, diam_at, path_l, HERO))

    # ---- ② ★★★ 行程下界（防「收太死」）------------------------------------
    a_l, b_l = _stroke_ab("L")
    one_way = (b_l - a_l).length * 1000.0 / 2.0
    res["v3_stroke_oneway_mm"] = round(one_way, 2)
    res["v3_stroke_p2p_mm"] = round(one_way * 2.0, 2)
    res["v3_min_amp_mm"] = AMP_MIN_MM
    res["v3_min_amp_ok"] = bool(one_way >= AMP_MIN_MM)
    res["v3_min_amp_note"] = (
        "★★★ 与 ① **反方向**的下界：「收太死」就读不出「擦」的动作。判据 = **单次往复位移**"
        "（一端 → 另一端）≥ %.0f mm。实测 **%.1f mm**（单程）/ %.1f mm（峰峰）。"
        "★ 由 `_e08_probe_clasp.py` 实测定标：纯沿 z 反向滑只有 16 mm（不够）且 gap 涨到 "
        "13.3；斜向 (dy%.0f, dz%.0f) 给出 %.1f mm 且 gap 仍 ≤ 11.1 ⟹ 取斜向。"
        "★ 旋钮 ③ `AMP_ZERO` 把往复归零 ⟹ 变红。" % (AMP_MIN_MM, one_way, one_way * 2.0,
                                                   STROKE_DY * 1000.0, STROKE_DZ * 1000.0,
                                                   one_way))

    # ---- ③ ★★★ 手 vs 手（本支第一次出现的自接触）-------------------------
    gap_walk = sorted(set(list(range(START, SETTLE_1 + 1))
                          + list(range(SETTLE_1, END + 1, 3))))
    gap_rows = {}
    worst_gap, worst_gap_at = None, None
    for frame in gap_walk:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        hand_geo_reset()
        gap, who, _p = hand_vs_hand_gap(step=4)
        if gap is None:
            continue
        gap_rows[str(frame)] = {"gap_mm": gap, "who": who}
        if worst_gap is None or gap < worst_gap:
            worst_gap, worst_gap_at = gap, (frame, who)
    clasp_gap = None
    scene.frame_set(CLASP)
    bpy.context.view_layer.update()
    hand_geo_reset()
    clasp_gap, _cw, _cp = hand_vs_hand_gap(step=3)
    res["v3_hand_gap_min_mm"] = worst_gap
    res["v3_hand_gap_min_at"] = worst_gap_at
    res["v3_hand_gap_clasp_mm"] = clasp_gap
    res["v3_hand_gap_band"] = list(GAP_BAND)
    res["v3_hand_gap_ok"] = bool(worst_gap is not None
                                 and GAP_BAND[0] <= worst_gap <= GAP_BAND[1])
    res["v3_hand_gap_trace"] = gap_rows
    res["v3_hand_gap_note"] = (
        "★★★ **本支第一次出现的「手 vs 手」自接触**（此前 62 支的防护恒是「手 vs 躯干」）。"
        "新探针 `hand_vs_hand_gap()`：口径照抄 `fist_face_gap`，参照物换成**对侧手的 BVH**；"
        "左右手**互为目标**，射线奇偶给符号（负 = 穿透）。判据 = 全程最小带符号距离 "
        "∈ [%.0f, %.0f] mm。实测 **%.3f mm**（@ f%s）；CLASP 帧读数 **%.3f mm**。"
        "★ 目标由 `_e08_probe_clasp.py` 网格扫描定标：clasp 锚点 (x=±%.0f, y=%.0f, z=%.0f) "
        "⟹ 间隙 **+3.37 mm**（贴合不穿透）。"
        "★ 旋钮 ④ `NO_CLASP`（两拳离 200 mm）与 ⑤ `OVERLAP`（两拳互相穿透）⟹ 双向变红。"
        % (GAP_BAND[0], GAP_BAND[1],
           worst_gap if worst_gap is not None else float("nan"),
           (worst_gap_at or ("?", "?"))[0], 
           clasp_gap if clasp_gap is not None else float("nan"),
           CLASP_X * 1000.0, CLASP_Y * 1000.0, CLASP_Z * 1000.0))

    # ---- ④ ★★ 拳的高度带（胸 / 下巴之间）-------------------------------
    z_win = list(range(CLASP, SETTLE_1 + 1))
    zs = [core(samples[idx[f]], s).z * 1000.0 for f in z_win for s in SIDES]
    res["v3_clasp_z_min_mm"] = round(min(zs), 2)
    res["v3_clasp_z_max_mm"] = round(max(zs), 2)
    res["v3_clasp_z_band"] = list(CLASP_Z_BAND)
    res["v3_clasp_z_ok"] = bool(CLASP_Z_BAND[0] <= min(zs)
                                and max(zs) <= CLASP_Z_BAND[1])
    res["v3_clasp_z_note"] = (
        "★★ 本支与 E06/E07 的**高度分离维度**：拳心 z ∈ [%.0f, %.0f] mm（胸 / 下巴之间）。"
        "实测 clasp 窗（f=%d~%d）拳心 z **%.1f ~ %.1f mm**。★ 对照：E06 ≤ 1392（胸肩）、"
        "E07 ≥ 1900（过顶）。★ 旋钮 ⑥ `HIGH`（抬到下巴以上）与 ⑦ `LOW`（压到胸以下）⟹ 变红。"
        % (CLASP_Z_BAND[0], CLASP_Z_BAND[1], CLASP, SETTLE_1,
           res["v3_clasp_z_min_mm"], res["v3_clasp_z_max_mm"]))

    # ---- ⑤ ★★ 往复次数 --------------------------------------------------
    ext, _vals, _fr = stroke_extrema(samples, idx)
    res["v3_stroke_extrema"] = [[f, s] for f, s in ext]
    res["v3_stroke_count"] = len(ext)
    res["v3_stroke_count_min"] = STROKE_COUNT_MIN
    res["v3_stroke_count_ok"] = bool(len(ext) >= STROKE_COUNT_MIN)
    res["v3_stroke_count_note"] = (
        "★★ 「擦拳套」要读出**高频往复**：判据 = 手势窗内「两拳 y 相对偏移 u=fistL.y−fistR.y」"
        "的极值个数 ≥ %d（死区 10 mm）。实测极值 **%s** ⟹ **%d 个**。"
        "★ 极值间隔 = 一个往复 8 帧（清单要求 6~8 帧，本支取上界 = 最慢，仍属高频）。"
        "★ 旋钮 ⑧ `STROKE1`（往复塌回单一姿态）⟹ 变红。"
        % (STROKE_COUNT_MIN, [[f, s] for f, s in ext], len(ext)))

    # ---- ⑥ ★★ 往复的镜像对称（本支最强的可读性证据）---------------------
    sym_rows = []
    worst_sym = 0.0
    worst_sym_at = None
    for i in range(len(ext) - 1):
        f0, s0 = ext[i]
        f1, s1 = ext[i + 1]
        l0 = core(samples[idx[f0]], "L")
        r0 = core(samples[idx[f0]], "R")
        l1 = core(samples[idx[f1]], "L")
        r1 = core(samples[idx[f1]], "R")
        mirror_r1 = Vector((-r1.x, r1.y, r1.z))
        mirror_l1 = Vector((-l1.x, l1.y, l1.z))
        d = max((l0 - mirror_r1).length, (r0 - mirror_l1).length) * 1000.0
        sym_rows.append({"pair": [f0, f1], "signs": [s0, s1],
                         "mirror_dev_mm": round(d, 3)})
        if d > worst_sym:
            worst_sym, worst_sym_at = d, (f0, f1)
    res["v3_stroke_sym_rows"] = sym_rows
    res["v3_stroke_sym_worst_mm"] = round(worst_sym, 3)
    res["v3_stroke_sym_at"] = worst_sym_at
    res["v3_stroke_sym_tol_mm"] = STROKE_SYM_TOL_MM
    res["v3_stroke_sym_ok"] = bool(sym_rows
                                   and worst_sym <= STROKE_SYM_TOL_MM
                                   and all(r["signs"][0] != r["signs"][1]
                                           for r in sym_rows))
    res["v3_stroke_sym_note"] = (
        "★★ 「擦拳套」是**镜像往复**（左拳向下擦 / 右拳向上擦，然后交换）。判据 = 逐个相邻"
        "极值对 `max |pose(f_k) − mirror(pose(f_{k+1}))|` ≤ %.1f mm 且相邻极值**异号**。"
        "实测最差 **%.3f mm**（@ %s）。★ 这是与「随便抖两下」的分界线。"
        "★ 旋钮 ⑨ `ASYMM`（三次往复同向、不做镜像）⟹ 变红。"
        % (STROKE_SYM_TOL_MM, worst_sym, worst_sym_at))

    # ---- ⑦ ★ 定格守卫（**本支不该有打击停顿**）---------------------------
    frozen = []
    for i in range(1, len(samples)):
        step, _at = _worst_step(samples, i - 1, i)
        if step <= 0.01:
            frozen.append(samples[i]["frame"])
    runs = []
    for f in frozen:
        if runs and f == runs[-1][-1] + 1:
            runs[-1].append(f)
        else:
            runs.append([f])
    longest = max((len(r) + 1 for r in runs), default=1)
    res["v3_hitstop_windows"] = [list(h) for h in HOLDS]
    res["v3_hitstop_longest_frozen"] = longest
    res["v3_hitstop_win_max"] = HITSTOP_WIN_MAX
    res["v3_hitstop_ok"] = bool(len(HOLDS) == 0 and longest <= HITSTOP_WIN_MAX)
    res["v3_hitstop_note"] = (
        "★ **反向守卫**：擦拳套**不是打击**，不该有「打击停顿」。判据 = 键表定格窗个数 "
        "== 0 **且** 实测最长「逐帧冻结段」≤ %d 帧。实测窗 **%s**、最长冻结段 **%d 帧**。"
        "★ 对照：E06 三窗口 × 3 帧、E07 单窗口 × 4 帧 —— 本支是**唯一没有 hitstop** 的胜利支。"
        "★ 旋钮 ⑩ `ADDHITSTOP` **真加键行**（在 CLASP 后插 %d 帧定格）⟹ 变红。"
        % (HITSTOP_WIN_MAX, [list(h) for h in HOLDS], longest, HITSTOP_ADD_N))

    # ---- ⑧ ★★ 第一拍位移极小（与 E06/E07 的第三样起手）-----------------
    ref = {s: core(samples[0], s) for s in SIDES}
    dip_mm = {s: (core(samples[idx[DIP]], s) - ref[s]).length * 1000.0
              for s in SIDES}
    res["v3_firstbeat_mm"] = {k: round(v, 2) for k, v in dip_mm.items()}
    res["v3_firstbeat_max_mm"] = FIRSTBEAT_MAX_MM
    res["v3_firstbeat_ok"] = bool(max(dip_mm.values()) <= FIRSTBEAT_MAX_MM)
    res["v3_firstbeat_note"] = (
        "★★ **连播不自洽的真风险**（清单 §0 第 2 条）：E06 / E07 / E08 **三支首帧同一姿态**。"
        "已有两拍：E06 = 沉髋**收拳向前下方**（f14 位移 **255.6 mm**）；E07 = 半蹲**甩拳向后**"
        "（f14 位移 **580 mm**）。⟹ 本支第一拍必须是**第三样且位移最小**："
        "**原地小幅下压 18 mm + 双拳靠向中线**。判据 = f%d 双拳位移 ≤ %.0f mm。"
        "实测 **%s mm** ⟹ 比 E06 小 %.1f 倍、比 E07 小 %.1f 倍。"
        "★ 旋钮 ⑪ `BIGFIRST` 把第一拍照抄成 E06 的大位移 ⟹ 变红。"
        % (DIP, FIRSTBEAT_MAX_MM, res["v3_firstbeat_mm"],
           255.6 / max(1e-6, max(dip_mm.values())),
           580.0 / max(1e-6, max(dip_mm.values()))))

    # ---- ⑨ ★★ 挺胸（庆祝的躯干载体）------------------------------------
    puff = {str(f): round(chest_rx_deg(f), 3) for f in (HERO, HERO_HOLD)}
    worst_puff = max(puff.values())
    res["v3_chest_rx_deg"] = puff
    res["v3_chest_puff_max_rx_deg"] = PUFF_MAX_RX
    res["v3_chest_puff_ok"] = bool(worst_puff <= PUFF_MAX_RX)
    res["v3_chest_puff_note"] = (
        "★★ 「胜利」的躯干载体是**挺胸**（`chest rx` **负** = 后仰挺胸）。实测庆祝段"
        "（f=%s）`chest rx` = %s（**必须全部 ≤ %.1f°**）。★ 旋钮 ⑫ `SLUMP` 把胸拨成"
        "前倾（+3°）⟹ 变红。" % ([HERO, HERO_HOLD], puff, PUFF_MAX_RX))

    # ---- ⑩ ★★ 下巴上扬（区间两端；且全程不怒吼）------------------------
    chin_rows = {str(f): round(head_back_deg(f), 3)
                 for f in (CLASP, SETTLE_1, HERO, HERO_HOLD)}
    chin_peak = max(head_back_deg(f) for f in range(START, END + 1))
    celeb_peak = max(head_back_deg(f) for f in (HERO, HERO_HOLD))
    res["v3_head_back_deg"] = chin_rows
    res["v3_head_back_peak_deg"] = round(chin_peak, 3)
    res["v3_chin_range"] = list(CHIN_RANGE)
    res["v3_no_roar_max_deg"] = NO_ROAR_MAX
    res["v3_chin_up_ok"] = bool(CHIN_RANGE[0] <= celeb_peak <= CHIN_RANGE[1])
    res["v3_no_roar_ok"] = bool(chin_peak <= NO_ROAR_MAX)
    res["v3_chin_up_note"] = (
        "★★ 「胜利」的头部载体是**下巴上扬**（`head_back` 正 = 后仰 / 上扬）。实测"
        "庆祝段峰值 **%.1f°**（区间 %.0f~%.0f）；全程峰值 **%.1f°**（⟹ 不怒吼，≤ %.0f°；"
        "E03 `Rage` 是 36.0°）。★ 旋钮 ⑬ `NO_CHIN` 清零颈/头增量 ⟹ 变红。"
        % (celeb_peak, CHIN_RANGE[0], CHIN_RANGE[1], chin_peak, NO_ROAR_MAX))

    # ---- ⑪ ★★ 英雄 pose 稳定（**不是颤抖**）---------------------------
    hero_span = HERO_HOLD - HERO + 1
    hero_steps = []
    worst_hero = 0.0
    for frame in range(HERO, HERO_HOLD):
        step, at = _worst_step(samples, idx[frame], idx[frame + 1])
        hero_steps.append((frame, round(step, 6), at))
        worst_hero = max(worst_hero, step)
    res["v3_hero_window"] = [HERO, HERO_HOLD]
    res["v3_hero_frames"] = hero_span
    res["v3_hero_min_frames"] = HERO_MIN_FRAMES
    res["v3_hero_steps_deg"] = [{"from": f, "step_deg": s, "at": a}
                                for f, s, a in hero_steps]
    res["v3_hero_worst_step_deg"] = round(worst_hero, 6)
    res["v3_hero_hold_ok"] = bool(hero_span >= HERO_MIN_FRAMES
                                  and worst_hero <= HERO_STEP_MAX_DEG)
    res["v3_hero_hold_note"] = (
        "★★ 清单风险：「胜利动作的停不能太长，末段必须是**稳定的英雄 Pose** 而非颤抖」。"
        "判据 = `HERO..HERO_HOLD` 窗口 **f=%d~%d 共 %d 帧**内逐帧最大角步 **%.6f°**"
        "（≤ %.2f°/帧）。★ 关键工程约束：`ARM_DN_AT`(= %d) 必须 ≥ 窗口终点。"
        "★ 旋钮 ⑭ `TREMBLE` 在窗口内逐帧交替 ±3° ⟹ 变红。"
        % (HERO, HERO_HOLD, hero_span, worst_hero, HERO_STEP_MAX_DEG, ARM_DN_AT))

    # ---- ⑫ 脚锁（**全程**）+ 鞋底带宽 ----------------------------------
    drift = {s: 0.0 for s in SIDES}
    toe_drift = {s: 0.0 for s in SIDES}
    sole = {}
    for frame in range(START, END + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        low = A.foot_lowest_by_side()
        vals = [low[s][2] * 1000.0 for s in SIDES if low[s] is not None]
        sole[frame] = min(vals)
        for side in SIDES:
            drift[side] = max(drift[side],
                              (Vector(samples[idx[frame]]["foot." + side])
                               - Vector(ANCHOR[side])).length * 1000.0)
            toe_drift[side] = max(
                toe_drift[side],
                (Vector(samples[idx[frame]]["toe." + side])
                 - Vector(samples[0]["toe." + side])).length * 1000.0)
    res["v3_ankle_drift_mm"] = {k: round(v, 4) for k, v in drift.items()}
    res["v3_toe_drift_mm"] = {k: round(v, 4) for k, v in toe_drift.items()}
    res["v3_sole_min_mm"] = round(min(sole.values()), 3)
    res["v3_sole_max_mm"] = round(max(sole.values()), 3)
    res["foot_lock_ok"] = bool(
        max(max(drift.values()), max(toe_drift.values())) <= FOOT_LOCK_MM
        and SOLE_BAND[0] <= min(sole.values())
        and max(sole.values()) <= SOLE_BAND[1])
    res["foot_lock_note"] = (
        "★★★ **脚锁「全程」口径**（E08 不跳、不位移）：双腿全程落地 ⟹ `want` 恒 = "
        "站架踝。实测踝漂 **L %.4f / R %.4f mm**、趾漂 **L %.4f / R %.4f mm**"
        "（阈值 %.1f），鞋底 **%.2f ~ %.2f mm**（带 %.0f ~ %.0f）。★ 18 mm 下压"
        "全部由腿 IK 吸收，脚一动不动 —— 力量链的腿段证据。"
        % (drift["L"], drift["R"], toe_drift["L"], toe_drift["R"], FOOT_LOCK_MM,
           res["v3_sole_min_mm"], res["v3_sole_max_mm"], SOLE_BAND[0],
           SOLE_BAND[1]))

    # ---- ⑬ 收招 / 过缝 ------------------------------------------------
    snap, snap_at = 0.0, None
    lo = max(1, TOTAL - TAIL_SETTLE_N)
    for index in range(lo, len(samples)):
        step, at = _worst_step(samples, index - 1, index)
        if step > snap:
            snap, snap_at = step, at
    res["no_snap_stop_step_deg"] = round(snap, 4)
    res["no_snap_stop_at"] = snap_at
    res["no_snap_stop_ok"] = bool(snap <= NO_SNAP_END_DEG)
    first_step, _fa = _worst_step(samples, 0, 1)
    last_step, _la = _worst_step(samples, len(samples) - 2, len(samples) - 1)
    res["seam_first_step_deg"] = round(first_step, 4)
    res["seam_last_step_deg"] = round(last_step, 4)

    # ---- ⑭ 力量传导链（六段：脚 → 腿 → 髋 → 腰 → 肩 → 手）-------------
    hip_ankle, knee = [], []
    for frame in frames[::2]:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        for side in SIDES:
            hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
            ank = Vector(A.bone_world(arm, "foot." + side, "head"))
            hip_ankle.append((hip - ank).length)
            knee.append(arm.pose.bones["shin." + side].rotation_euler.x)
    foot_axis = (max(hip_ankle) - min(hip_ankle)) * 1000.0
    knee_deg_span = (max(knee) - min(knee)) * 180.0 / math.pi
    waist = [abs(s["euler"].get("chest", (0.0, 0.0, 0.0))[0]) for s in samples]
    waist_deg = max(waist) - min(waist)
    pelvis = [Vector(s["pelvis"]) for s in samples]
    shoulder = [Vector(s["upperarm.L"]) for s in samples]
    shoulder_mm = max((p - shoulder[0]).length for p in shoulder) * 1000.0
    hand = [Vector(s["hand.L.tail"]) for s in samples]
    hand_mm = max((p - hand[0]).length for p in hand) * 1000.0
    hip_travel = max((p - pelvis[0]).length for p in pelvis) * 1000.0
    res["chain_travel"] = {"foot_axis_mm": round(foot_axis, 3),
                           "knee_deg": round(knee_deg_span, 3),
                           "hip_mm": round(hip_travel, 3),
                           "waist_deg": round(waist_deg, 3),
                           "shoulder_mm": round(shoulder_mm, 3),
                           "hand_mm": round(hand_mm, 3)}
    res["chain_note"] = (
        "★ 力量传导链 **脚 → 腿 → 髋 → 腰 → 肩 → 手**，六段**都必须有非零关键帧**"
        "（清单 0.2「不许跳级」）。本支载体：脚 = 髋↔踝距离行程（小幅下压靠屈膝）"
        "＋踝全程钉死；腿 = 膝屈角行程；髋 = 骨盆世界行程；腰 = `chest` 俯仰行程；"
        "肩 = 双肩峰世界行程；手 = 拳心行程。★ **不是「只有手在动」**：DIP 的 18 mm "
        "下压把脚→腿→髋→腰全部串上。")
    res["chain_present_ok"] = bool(
        foot_axis > 5.0 and knee_deg_span > 0.1 and hip_travel > 2.0
        and waist_deg > 2.0 and shoulder_mm > 1.0 and hand_mm > 20.0)

    # ---- ⑮ 可达性 -----------------------------------------------------
    worst_leg, worst_leg_at = 0.0, None
    worst_arm, worst_arm_at = 0.0, None
    for frame in range(START, END + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        for side in SIDES:
            hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
            want = Vector(A.bone_world(arm, "foot." + side, "head"))
            ratio = (want - hip).length / ((A.L_THIGH + A.L_SHIN)
                                           * REACH_MAX_RATIO)
            if ratio > worst_leg:
                worst_leg, worst_leg_at = ratio, (frame, side)
            sh = Vector(A.bone_world(arm, "upperarm." + side, "head"))
            fist = Vector(A.bone_world(arm, "hand." + side, "tail"))
            r2 = (fist - sh).length / (ARM_TOTAL * REACH_MAX_RATIO)
            if r2 > worst_arm:
                worst_arm, worst_arm_at = r2, (frame, side)
    res["leg_reach_ratio_max"] = round(worst_leg, 5)
    res["leg_reach_at"] = worst_leg_at
    res["leg_reach_ok"] = bool(worst_leg <= 1.0)
    res["arm_reach_ratio_max"] = round(worst_arm, 5)
    res["arm_reach_at"] = worst_arm_at
    res["arm_reach_ok"] = bool(worst_arm <= 1.0)

    # ---- ⑯ 穿模（臂 vs 头盒，D01 起老口径）-----------------------------
    worst_clip, clip_at = 0.0, None
    for frame in sorted(set(list(range(START, END + 1, 3))
                            + [DIP, CLASP, STROKE_1, STROKE_2, STROKE_3,
                               SETTLE_1, HERO, HERO_HOLD])):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        clip = PD.clip_metrics(arm)
        if clip["clip_max_mm"] > worst_clip:
            worst_clip, clip_at = clip["clip_max_mm"], (frame, clip["clip_at"])
    res["clip_max_mm"] = round(worst_clip, 2)
    res["clip_at"] = clip_at
    res["no_face_clip_ok"] = bool(worst_clip <= CLIP_MAX_MM)

    # ---- ⑰ 手 vs 躯干：**差分口径**（站架自己就有缺陷）-----------------
    pierce = {}
    walk = sorted(set(list(range(START, END + 1, 3))
                      + [DIP, CLASP, STROKE_1, STROKE_2, STROKE_3,
                         SETTLE_1, HERO, HERO_HOLD]))
    seam_frames = {START, END}
    worst_nt, worst_nt_at = 0, None
    worst_deep, worst_deep_at = 0.0, None
    worst_beyond, worst_beyond_at = 0, None
    worst_all, worst_thumb = 0, 0
    for frame in walk:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        torso_bvh_reset()
        tree = torso_bvh()
        row = {}
        for side in SIDES:
            counts = hand_mesh_stats(side, tree=tree, step=4,
                                     limit_mm=HAND_PIERCE_MM)
            row[side] = counts
            if frame in seam_frames:
                continue
            worst_all = max(worst_all, counts["inside"])
            worst_thumb = max(worst_thumb, counts["thumb"])
            if counts["inside_nothumb"] > worst_nt:
                worst_nt, worst_nt_at = counts["inside_nothumb"], (frame, side)
            deep = counts["deepest_nothumb_mm"]
            if deep is not None and deep < worst_deep:
                worst_deep, worst_deep_at = deep, (frame, side)
            if counts["beyond_limit"] > worst_beyond:
                worst_beyond = counts["beyond_limit"]
                worst_beyond_at = (frame, side)
        pierce[str(frame)] = row
    station_beyond = max(STATION_PIERCE[s]["beyond_limit"] for s in SIDES)
    station_nt = max(STATION_PIERCE[s]["inside_nothumb"] for s in SIDES)
    res["v3_pierce_scope"] = ["(0, TOTAL) 内全部帧",
                              "排除接缝帧 %s" % sorted(seam_frames)]
    res["v3_pierce_nothumb_worst"] = worst_nt
    res["v3_pierce_nothumb_worst_at"] = worst_nt_at
    res["v3_pierce_nothumb_deepest_mm"] = round(worst_deep, 2)
    res["v3_pierce_nothumb_deepest_at"] = worst_deep_at
    res["v3_pierce_beyond_limit_worst"] = worst_beyond
    res["v3_pierce_beyond_limit_worst_at"] = worst_beyond_at
    res["v3_station_nothumb_count"] = station_nt
    res["v3_station_beyond_limit"] = station_beyond
    res["v3_pierce_all_worst"] = worst_all
    res["v3_pierce_thumb_worst"] = worst_thumb
    res["v3_pierce_detail"] = pierce
    res["victory_hand_no_pierce_ok"] = bool(
        worst_deep >= -HAND_PIERCE_MM and worst_beyond <= station_beyond)
    res["victory_hand_no_pierce_note"] = (
        "★ 本支的拳**在胸前中线做小幅往复** ⟹ 比 E06 的「贴胸捶击」更贴胸。口径照 "
        "E03 v011 的**差分**形式（改的是基准，不是阈值）：本支非拇指最深带符号距离 "
        "**%.2f mm**（@ %s，下限 −%.0f）；**越过绝对下限的顶点数 %d**（@ %s）；"
        "站架基线同一读数 **%d** ⟹ 判据 =「不得比站架更差」。"
        % (worst_deep, worst_deep_at, HAND_PIERCE_MM, worst_beyond,
           worst_beyond_at, station_beyond))

    # ---- ⑱ ★★ 真旋转步长（矩阵口径）—— 与 euler 口径互为交叉验证 --------
    prev_basis = None
    worst_mat, worst_mat_at = 0.0, None
    for frame in range(START, END + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        current = {name: arm.pose.bones[name].matrix.to_3x3().copy()
                   for name in BONE_LIST if name in arm.pose.bones}
        if prev_basis is not None:
            _fmax, _fmax_at = 0.0, None
            for name in set(current) & set(prev_basis):
                a, b = prev_basis[name], current[name]
                for column in range(3):
                    va = a.col[column].normalized()
                    vb = b.col[column].normalized()
                    deg = math.degrees(math.acos(max(-1.0, min(1.0,
                                                             va.dot(vb)))))
                    if deg > worst_mat:
                        worst_mat, worst_mat_at = deg, (frame, name)
                    if deg > _fmax:
                        _fmax, _fmax_at = deg, name
            if _STEP_TRACE:
                _es, _ea = _worst_step(samples, idx[frame - 1], idx[frame])
                print("E08_STEP f=%3d mat=%6.2f %-12s eul=%7.2f %s"
                      % (frame, _fmax, _fmax_at, _es, _ea))
        prev_basis = current
    res["v3_matrix_step_deg_max"] = round(worst_mat, 3)
    res["v3_matrix_step_at"] = worst_mat_at
    res["v3_matrix_step_ok"] = bool(worst_mat <= MATRIX_STEP_MAX_DEG)
    euler_step, euler_at = 0.0, None
    for index in range(1, len(samples)):
        step, at = _worst_step(samples, index - 1, index)
        if step > euler_step:
            euler_step, euler_at = step, at
    res["v3_euler_step_deg_max"] = round(euler_step, 3)
    res["v3_euler_step_at"] = euler_at
    res["v3_matrix_step_note"] = (
        "★★ **矩阵口径**的逐帧最大真实旋转步 **%.3f° @ %s**（阈值 ≤ %.1f°）；"
        "euler 口径 **%.3f° @ %s**。两者必须**一致地小** —— 差得远就是欧拉表示在跳"
        "（万向节锁），不是动作在跳。★ 本支风险段较小（动作幅度本就小），但仍先做 "
        "`compat_euler`（min-max 瓶颈 DP）再断言。"
        % (worst_mat, worst_mat_at, MATRIX_STEP_MAX_DEG, euler_step, euler_at))

    # ---- ⑲ 手骨滚转基准的退化余量（E03 v009 的教训）------------------
    res["v3_x_hint_margin"] = round(MIN_HINT_MARGIN, 4)
    res["v3_x_hint_margin_min"] = HAND_X_HINT_MIN_MARGIN
    res["v3_x_hint_margin_ok"] = bool(MIN_HINT_MARGIN >= HAND_X_HINT_MIN_MARGIN)
    res["v3_x_hint_margin_note"] = (
        "★ `orient_hand` 的滚转基准（平行移动，种子 = `thumb_out`）实测最小余量 **%.4f**"
        "（阈值 ≥ %.2f）。★ 本支与 E06/E07 **同基准但动作不同** ⟹ 必须**重新量**"
        "（清单 §1 明令不许照抄别支读数）。" % (MIN_HINT_MARGIN, HAND_X_HINT_MIN_MARGIN))

    res["phase_markers"] = {
        "START": START, "DIP": DIP, "CLASP": CLASP, "STROKE_1": STROKE_1,
        "STROKE_2": STROKE_2, "STROKE_3": STROKE_3, "SETTLE_1": SETTLE_1,
        "HERO": HERO, "HERO_HOLD": HERO_HOLD, "SETTLE": SETTLE, "END": END}
    res["v3_sole_trace_mm"] = {str(f): round(v, 2)
                               for f, v in sorted(sole.items())}
    return res


# =============================================================== 屏幕投影
def landmark_screen(arm, action):
    """把「拳心 / 肩峰」逐帧投影到**正面**屏幕坐标，供像素探针用。"""
    name, loc, tgt, scale, rres = VIEW_E08_FRONT
    mm_per_px = scale / float(rres[1]) * 1000.0
    floor_row = (scale / 2.0 - loc[2]) / (scale / float(rres[1]))
    out = {}
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    for frame in range(START, END + 1, 2):
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()
        row = {}
        for key, point in (
                ("fistL", Vector(A.bone_world(arm, "hand.L", "tail"))),
                ("fistR", Vector(A.bone_world(arm, "hand.R", "tail"))),
                ("shoulderL", Vector(A.bone_world(arm, "upperarm.L", "head"))),
                ("shoulderR", Vector(A.bone_world(arm, "upperarm.R", "head")))):
            row[key] = [round(point.z * 1000.0 / mm_per_px + floor_row, 3),
                        round(point.x * 1000.0 / mm_per_px + rres[0] / 2.0, 3)]
        out[str(frame)] = row
    return {"view": VIEW_E08_FRONT[0], "res": list(VIEW_E08_FRONT[4]),
            "ortho_m": VIEW_E08_FRONT[3], "cam_z": VIEW_E08_FRONT[1][2],
            "mm_per_px": round(mm_per_px, 7), "floor_row": round(floor_row, 4),
            "rows": out, "format": "[row, col]"}


# =============================================================== 分层渲染
def render_layer(arm, action, prefix, keep_prefix, view, frames):
    keep = [o for o in bpy.data.objects if o.type == "MESH"
            and any(o.name.startswith(p) for p in keep_prefix)]
    hidden = []
    for obj in bpy.data.objects:
        if obj.type == "MESH" and obj not in keep:
            hidden.append((obj, obj.hide_render))
            obj.hide_render = True
    A.render_pose_sheet(arm, action, frames, prefix, views=(view,))
    for obj, was in hidden:
        obj.hide_render = was


# =============================================================== 启动
def boot():
    arm, meshes = A.open_animation_project()
    A.setup_scene()
    global BASE, ANCHOR, STATION_FIST, BONE_LIST, TORSO, STATION_PIERCE
    global LAST_ELBOW, STATION_HAND_Y, STATION_HAND_X, STATION_POLE_DIR
    global LAST_FOREARM_TWIST, LAST_HAND_FRAME, PELVIS0, MIN_HINT_MARGIN
    global LAST_HAND_X, LAST_TWIST_ANGLE, LAST_BLENDED, LAST_BULGE, LAST_HAND_Q
    LAST_ELBOW = {}
    LAST_HAND_X = {}
    LAST_TWIST_ANGLE = {}
    LAST_HAND_FRAME = {}
    LAST_FOREARM_TWIST = {}
    LAST_BLENDED = {}
    LAST_BULGE = {}
    LAST_HAND_Q = {}
    FRAME_ELBOW.clear()
    FRAME_BULGE.clear()
    FRAME_TWIST.clear()
    FRAME_HAND_Q.clear()
    MIN_HINT_MARGIN = 1.0
    TORSO = bpy.data.objects[TORSO_MESH]
    if SEAM_ZERO:
        BASE = {}
        A.apply_pose(arm, BASE)
    else:
        BASE = IDLE.idle_pose(arm, 0.0)
    BONE_LIST = sorted(arm.pose.bones.keys())
    ANCHOR = {s: Vector(A.bone_world(arm, "foot." + s, "head")) for s in SIDES}
    PELVIS0 = Vector(A.bone_world(arm, "pelvis", "head"))
    STATION_FIST = {s: Vector(A.bone_world(arm, "hand." + s, "tail"))
                    for s in SIDES}
    A.apply_pose(arm, BASE)
    torso_bvh_reset()
    for side in SIDES:
        mat = arm.pose.bones["hand." + side].matrix.to_3x3().normalized()
        STATION_HAND_Y[side] = mat.col[1].normalized().copy()
        STATION_HAND_X[side] = mat.col[0].normalized().copy()
        sho = Vector(A.bone_world(arm, "upperarm." + side, "head"))
        elb = Vector(A.bone_world(arm, "forearm." + side, "head"))
        pole = elb - sho
        STATION_POLE_DIR[side] = (
            pole.normalized() if pole.length > 1e-6
            else ELBOW_DIR[side].normalized())
    # ★★ 平行移动的**种子**：第 0 帧的手 x 轴 = 站架实测手 x 轴 ⟹ f0→f1 滚转连续。
    for side in SIDES:
        LAST_HAND_X[side] = STATION_HAND_X[side].copy()
    for side in SIDES:
        STATION_PIERCE[side] = hand_mesh_stats(side, step=4,
                                               limit_mm=HAND_PIERCE_MM)
    return arm, meshes


def main():  # noqa: C901
    arm, meshes = boot()
    keyframes = [(frame, victory_pose(arm, frame))
                 for frame in range(START, END + 1)]
    keyframes = compat_euler(keyframes)
    keyframes = seam_canonicalize(keyframes)
    meta = {
        "anim_id": NAME,
        "loop": False,
        "category": "状态与流程",
        "note": ("胜利 C（擦拳套）：原地小幅下压 → 双拳并拢到胸前中线（间隙 ~3 mm）→ "
                 "**三次镜像往复**（斜向 dy%.0f/dz%.0f，间隔 8 帧）→ 拳分开 → "
                 "挺胸下巴上扬、双拳收在体侧的英雄姿（12 帧稳住）→ 回战斗待机；"
                 "★ 全程原地、脚锁全程；★ **无 hitstop**；"
                 "★ 与 E06（捶胸）/ E07（举拳）的四维分离：高度/幅度/接触对象/往复次数；"
                 "★ 第一拍位移 ≪ E06（255.6 mm）/ E07（580 mm）"
                 % (STROKE_DY * 1000.0, STROKE_DZ * 1000.0)),
        "frames": [START, END],
        "root_motion_m": [0.0, 0.0],
        "root_motion_z_m": [0.0, 0.0],
        "hitstop_frames": 0,
        "hitstop_windows": [],
        "antic_frame": DIP,
        "hit_frame": CLASP,
        "hit_frames": [CLASP],
        "cancel_frame": HERO,
        "hit_point_m": [CLASP_X, CLASP_Y, round(CLASP_Z, 4)],
        "seam": "%s@%d" % (SEAM_ACTION, SEAM_FRAME),
        "seam_ends": {"start": "%s@%d" % (SEAM_ACTION, SEAM_FRAME),
                      "end": "%s@%d" % (SEAM_ACTION, SEAM_FRAME)},
        "frame_bound_note": ("★ 120 帧 = 2.0 s = E01 登记的**上界** ⟹ 沿用"
                             "（显式声明，不是悄悄超）；清单要求胜利动作 1.5~2.5 s ⟹ 落带内"),
        "view_note": ("★ 本支取景**自立**（不照抄 E06/E07）：纵向 −0.15~2.05 m"
                      "（中心 z=0.95、正交高 2.20 m）—— 拳不过顶、比 E07 低 50 mm；"
                      "正面判「双拳并拢 + 三次镜像往复 + 拳心同高」，侧视判挺胸 + 下巴上扬，"
                      "3Q 判英雄姿"),
        "foot_lock": {
            "scope": "全程 [START..END]（本支不跳、不位移）",
            "reason": "原地动画 ⟹ 踝恒钉站架点"},
        "clasp": {
            "anchor_m": [CLASP_X, CLASP_Y, round(CLASP_Z, 4)],
            "gap_mm": 3.37,
            "source": "_e08_probe_clasp.py 网格扫描定标",
        },
        "differentiation_vs_E06_E07": {
            "fist_z_mm": {"E06": "≤1392", "E07": "≥1900", "E08": "[1150,1450]"},
            "amplitude_mm": {"E06": 255.6, "E07": 744.0, "E08_max": AMP_MAX_MM},
            "contact": {"E06": "拳↔躯干", "E07": "无接触", "E08": "拳↔拳"},
            "stroke_count": {"E06": 3, "E07": 0, "E08_min": STROKE_COUNT_MIN},
            "hitstop": {"E06": 3, "E07": 1, "E08": 0},
        },
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    markers = {"START": START, "DIP": DIP, "ANTIC": DIP, "CLASP": CLASP,
               "HIT": CLASP,
               "STROKE_1": STROKE_1, "STROKE_2": STROKE_2, "STROKE_3": STROKE_3,
               "SETTLE_1": SETTLE_1, "HERO": HERO, "HOLD_POSE": HERO_HOLD,
               "RECOV": SETTLE, "END": END}
    A.add_markers(action, markers)
    if ADD_HITSTOP:
        A.set_hitstop(action, CLASP, CLASP + HITSTOP_ADD_N - 1)

    samples = A.sample_animation(arm, action, START, END, meshes)
    report = A.run_common_assertions(samples, meta, foot_probe=(),
                                     slide_tolerance_mm=FOOT_LOCK_MM)
    report.update(victory_assertions(arm, action, samples, meshes))

    # ---- 首末同姿（一次性动画：两端都 = 站架）→ 显式算 loop_seamless ----------
    first = world_mats(arm, action, START)
    last = world_mats(arm, action, END)
    end_elem, end_elem_at = 0.0, None
    for bone in BONE_LIST:
        if bone in first and bone in last:
            for r in range(4):
                for c in range(4):
                    d = abs(first[bone][r][c] - last[bone][r][c])
                    if d > end_elem:
                        end_elem, end_elem_at = d, (bone, r, c)
    report["end_matches_start_elem_max"] = end_elem
    report["end_matches_start_elem_at"] = end_elem_at
    report["end_matches_start_ok"] = bool(end_elem <= 1e-6)

    worst_angle, worst_move = 0.0, 0.0
    for name in set(samples[0]["euler"]) | set(samples[-1]["euler"]):
        ea = samples[0]["euler"].get(name, (0.0, 0.0, 0.0))
        eb = samples[-1]["euler"].get(name, (0.0, 0.0, 0.0))
        worst_angle = max(worst_angle, max(abs(a - b) for a, b in zip(ea, eb)))
    for name in A.PROBE_KEYS:
        if name in samples[0] and name in samples[-1]:
            worst_move = max(worst_move, (Vector(samples[0][name])
                                          - Vector(samples[-1][name])).length)
    report["loop_seamless"] = bool(worst_angle <= 0.5 and worst_move <= 0.0005)
    report["loop_angle_deg"] = round(worst_angle, 4)
    report["loop_move_mm"] = round(worst_move * 1000.0, 3)

    # ---- 接缝入 ---------------------------------------------------------
    upstream = bpy.data.actions[SEAM_ACTION]
    seam = world_mats(arm, upstream, SEAM_FRAME)
    mine = world_mats(arm, action, 0)
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
    report["seam_in_src"] = "%s@%d" % (SEAM_ACTION, SEAM_FRAME)

    report["meta"] = meta
    failed = sorted(k for k, v in report.items()
                    if k.endswith("_ok") and v is not True and v is not None)
    non_ok = sorted(k for k, v in report.items()
                    if isinstance(v, bool) and v is False)
    report["failed"] = failed
    report["non_ok_bools"] = non_ok
    A.report("E08_REPORT", report)

    stem_only = os.environ.get("E08_STEM_ONLY") == "1"
    stem_frames = list(STEM_FRAMES)
    if stem_only:
        stem = os.environ.get("E08_STEM", "v3stem")
        A.render_pose_sheet(arm, action, stem_frames, stem,
                            views=(VIEW_E08_SIDE, VIEW_E08_FRONT))
        render_layer(arm, action, stem + "hand", HAND_PREFIX, VIEW_E08_FRONT,
                     stem_frames)
        print("E08_DONE failed=%s non_ok=%s" % (failed, non_ok))
        return

    if not SKIP_RENDER:
        A.render_pose_sheet(arm, action, list(range(START, END + 1, 4)),
                            "v3wide", views=(VIEW_E08_SIDE,))
        A.render_pose_sheet(arm, action, stem_frames, "v3_side",
                            views=(VIEW_E08_SIDE,))
        A.render_pose_sheet(arm, action, stem_frames, "v3_front",
                            views=(VIEW_E08_FRONT,))
        # ★★ 手部**分层**渲染必须用**另一个前缀**（E05 踩过「原地覆盖」的坑）。
        render_layer(arm, action, "v3_hand", HAND_PREFIX, VIEW_E08_FRONT,
                     stem_frames)
        key_frames = [0, 6, 12, 18, 24, 28, 32, 36, 40, 44, 48, 54, 60, 68,
                      74, 80, 86, 92, 100, 106, 110, 115, 120]
        A.render_pose_sheet(arm, action, key_frames, "v3key",
                            views=(VIEW_E08_SIDE, VIEW_E08_FRONT, A.VIEW_3Q))
        with open(os.path.join(A.PREVIEW_DIR, "_e08_landmark.json"), "w",
                  encoding="utf-8") as handle:
            json.dump(landmark_screen(arm, action), handle, ensure_ascii=False)
        A.save_project()
        A.export_glb(arm)
    print("E08_DONE failed=%s non_ok=%s" % (failed, non_ok))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("E08_FAILURE " + traceback.format_exc())
