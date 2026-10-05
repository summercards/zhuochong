"""anim_victory_02 —— E07 `Victory_02` 胜利B（举拳）（E 族第七支 / 第 63 支）。

清单原文：「**胜利 B：举拳**」。

★★★ 开工第一件测量（`probe_e07_baseline.py`，实测定标）：
    · 接缝：`Victory_01@120`（E06 末帧）vs `Idle_01@0` → **pos 8.7e-05 mm / dir 0.031°**
      ⟹ 逐位一致（浮点噪声级）⟹ 起点仍取 `Idle_01@0`，连播无缝。
    · 站架几何：肩峰（`upperarm.head`）z = **1312.9 mm**、x = ±150.7 mm；
      臂总长（上臂 328 + 前臂 224 + 手 98）= **650 mm** ⟹ 拳心几何上限 **1962.9 mm**。
    · ★★★ **IK 实解（不是几何推算）**：按 `z` 扫目标（用 E06 的成熟 `seat_arm`，
      `blend=0` = 拳沿前臂）—— `z ≤ 1940` 时 `core z` **精确等于**目标；
      `z ≥ 1980` 起**饱和在 1948.8 mm**（`|core−shoulder|` 顶到 648 mm ≈ 臂全长）。
      ⟹ 本支举臂峰值取 **1930 mm**（`arm_reach` 比值实测 ~0.975，留 12 mm 余量；
      距门禁 1900 有 30 mm 安全垫）。
    · ★ 举臂**不落入万向节锁**：z=1930 实测 `forearm ry ≈ 44.9°`、`hand ry ≈ 30°`
      （奇异带在 ±90°）、`hint_margin = 0.9179`（阈值 0.45）、`clip_max = 0.0`。

★★★ 本支的真风险（清单 §1 逐条落地）：
    ① **与 E06 必须可区分**（E06/E07 首帧**同一姿态**）。差异做在**四个可量化维度**：
       · 手的高度：E06 拳心 z ≤ 1392（胸/肩）→ 本支 **≥ 1900（过顶）**
         ⟹ `v2_raise_z_min_ok`；
       · 对称性：E06 双拳同步 → 本支**单臂**（另一臂下放体侧）
         ⟹ `v2_asym_ok`（左右拳 z 差 ≥ 500 mm）；
       · 接触：E06 拳面贴胸（+1.13 mm）→ 本支**拳在空中**
         ⟹ `v2_no_contact_ok`（拳面距躯干 ≥ 200 mm）；
       · 命中停顿：E06 三窗口 → 本支**单窗口 4 帧**
         ⟹ `v2_hitstop_ok`。
       · ★★ **再加一条「第一拍就不同」的硬差异**：E06 的起手是「收拳**向前**沉髋」
         （f14 拳心 y = **−310 mm**，在身前）；本支改成「**拳向后甩**的半蹲预蓄」
         （f14 拳心 y = **+185 mm**，在身后）⟹ `v2_windup_behind_ok`。
         两支在同一帧上拳心的 y 差 **≈ 495 mm**，连播时第一拍就读得出不同。
    ② **举臂的万向节锁**：照抄 E06 的 `compat_euler`（min-max 瓶颈 DP）+
       `v2_matrix_step_ok`（**矩阵口径** ≤25°）双口径互证；`v2_x_hint_margin_ok`
       **重新标定**（E06 的 0.6822 不许照抄 —— 本支实测 0.9179）。
    ③ **胜利动作的「停」**（E05 预警 2）：英雄姿窗口 f76~88 必须**已收静**
       ⟹ `v2_hero_hold_ok`（逐帧 ≤1.6°）；臂收回**完成帧 110 早于** no_snap 判定窗
       （f110~120）。

★★★ 工程件：六段结构（120 帧 = 2.0 s，★ = E01 登记的 120 帧上界，**显式声明**）
    `START(0) → DIP(14) → RAISE(34)→[定格 34~37]→ PUMP_DN(46) → PUMP_UP(54)
      → HERO(76) → HERO_HOLD(88) → SETTLE(108) → END(120)`
    · `DIP` = **半蹲下沉 + 拳向后甩**（≥55 mm，比 E06 的 34 mm 更深；预蓄方向相反）；
    · `RAISE` = ★ 单臂（左）直上过顶（拳心 z = 1930 mm），另一臂下放体侧；
    · `PUMP_DN / PUMP_UP` = 举着的拳**小幅上下震荡**（庆祝的「抖」，行程 58 mm）；
    · `HERO/HERO_HOLD` = 挺胸 + 下巴上扬 + 拳**保持在头侧上方**（不是 E06 的胸前）；
    · 段间缓动：`smooth` / `hold`（**不用 `decel`** —— E05 实测教训：定格后用 `decel`
      会把 16 % 行程塞进一帧 ⟹ `matrix_step` 炸到 30.59°）。

★★★ 拳目标：**全部是固定世界点**（`blend = 0` = 拳沿前臂「顶天」）。
    与 E06 相反 —— E06 的 `blend = 1`（拳面正对胸面，为的是「捶」）；本支不接触任何
    东西，拳轴与臂轴同向才是「举拳」。⟹ `FIST_FACE_BLEND = 0`，**不查胸面**
    （省掉逐帧 `closest_point_on_mesh`，也让「拳在空中」成为结构事实而非调参结果）。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python anim_victory_02.py
    SKIP_RENDER=1      只跑门禁不渲图（迭代用）
    E07_TRACE=1        逐帧打印 骨盆位移 / 拳心 / 脚锁误差 / env

反向验证（§4 第 6 步，11 组，每组必须**真的把对应判据变红**）：
    E07_TP_SEAM_ZERO=1    ① 首帧改零位              ⟹ `seam_in_ok`
    E07_TP_LOW_RAISE=1    ② ★★★ 举臂只到 1830 mm   ⟹ `v2_raise_z_min_ok`
    E07_TP_SYM=1          ③ ★★★ 双臂都举（对称）    ⟹ `v2_asym_ok`
    E07_TP_CONTACT=1      ④ ★★★ 拳落在胸前（贴身）  ⟹ `v2_no_contact_ok`
    E07_TP_FRONT_WINDUP=1 ⑤ ★★ 预蓄甩到身前（照抄E06）⟹ `v2_windup_behind_ok`
    E07_TP_NOHITSTOP=1    ⑥ ★ 抽掉键表 `hold` 行    ⟹ `v2_hitstop_ok`
    E07_TP_SLUMP=1        ⑦ ★ 不挺胸（含胸）        ⟹ `v2_chest_puff_ok`
    E07_TP_NOCHIN=1       ⑧ ★ 下巴不上扬            ⟹ `v2_chin_up_ok`
    E07_TP_TREMBLE=1      ⑨ ★ 英雄姿颤抖            ⟹ `v2_hero_hold_ok`
    E07_TP_FOOTSWAY=1     ⑩ ★ 脚滑（骑骨盆）        ⟹ `foot_lock_ok`
    E07_TP_LOOPBREAK=1    ⑪ ★ 末帧不闭合            ⟹ `end_matches_start_ok`
"""

import json
import math
import os
import sys

import bpy
from mathutils import Euler, Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A          # noqa: E402
import anim_idle_01 as IDLE   # noqa: E402
import probe_d01_guard as PD  # noqa: E402

NAME = "Victory_02"
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

RAISE_SIDE = "L"             # ★ 举起的臂（本支只举一条）
OTHER_SIDE = "R"


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
# ★ 上游 = `Idle_01@0`（本支自己测过：`probe_e07_baseline.py` → 8.7e-05 mm / 0.031°）。
SEAM_ACTION = os.environ.get("E07_SEAM_ACTION", "Idle_01")
SEAM_FRAME = _env_i("E07_SEAM_FRAME", 0)

# =============================================================== 时间轴（120 帧 = 2.0 s）
# ★★ 帧预算：120 帧 = 2.0 s = E01 登记的**上界** ⟹ 沿用（**显式声明**）。
#   清单要求胜利动作 1.5~2.5 s ⟹ 2.0 s 落带内。
TOTAL = _env_i("E07_TOTAL", 120)
START = 0
END = TOTAL
HITSTOP_N = _env_i("E07_HITSTOP", 4)          # ★ 单窗口定格帧数（3~4）

DIP = _env_i("E07_DIP", 14)                   # 半蹲下沉 + 拳向后甩（预蓄）
RAISE = _env_i("E07_RAISE", 34)               # ★ 单臂举到位
HOLD = (RAISE, RAISE + HITSTOP_N - 1)         # [34, 37]
PUMP_DN = _env_i("E07_PUMP_DN", 46)           # 举着的拳下沉（庆祝的「抖」）
PUMP_UP = _env_i("E07_PUMP_UP", 54)           # 拳回抬
HERO = _env_i("E07_HERO", 76)                 # 收成英雄姿（拳保持头侧上方）
HERO_HOLD = _env_i("E07_HOLD", 88)            # ★ 英雄姿保持（76~88 几乎不动）
SETTLE = _env_i("E07_SETTLE", 108)            # 回站架途中
HOLDS = (HOLD,)

# 臂包络（★ `ARM_DN_AT` 必须 ≥ `HERO_HOLD`，否则英雄姿窗口内臂仍在变 ⟹ 判红；
#          `ARM_DN_DONE` 必须 ≤ 110（早于 no_snap_stop 的 f110~120 判定窗））
ARM_UP_AT = _env_i("E07_ARM_UP", 14)
ARM_DN_AT = _env_i("E07_ARM_DN", 88)
ARM_DN_DONE = _env_i("E07_ARM_DONE", 110)

# =============================================================== 反向验证旋钮
SEAM_ZERO = _env_b("E07_TP_SEAM_ZERO")        # ① 首帧改零位
LOW_RAISE = _env_b("E07_TP_LOW_RAISE")        # ② ★★★ 举臂只到 1830
SYM = _env_b("E07_TP_SYM")                    # ③ ★★★ 双臂都举（对称）
CONTACT = _env_b("E07_TP_CONTACT")            # ④ ★★★ 拳落在胸前（贴身）
FRONT_WINDUP = _env_b("E07_TP_FRONT_WINDUP")  # ⑤ ★★ 预蓄甩到身前（照抄 E06）
# ★★★ `NO_HITSTOP` **必须定义在 `KEYS` 之前**（E03/04/05/06 的实测教训：
#   只在 `main()` 里把 `set_hitstop` 关掉，姿态仍是冻结的 ⟹ 旋钮**惰性**）。
#   忠实仿真 = **从键表里抽掉 `hold` 行**，让 `RAISE → PUMP_DN` 变成一整段。
NO_HITSTOP = _env_b("E07_TP_NOHITSTOP")
SLUMP = _env_b("E07_TP_SLUMP")                # ⑦ 不挺胸
NO_CHIN = _env_b("E07_TP_NOCHIN")             # ⑧ 下巴不上扬
TREMBLE = _env_b("E07_TP_TREMBLE")            # ⑨ 英雄姿颤抖
FOOT_SWAY = _env_b("E07_TP_FOOTSWAY")         # ⑩ 脚滑（骑骨盆）
LOOP_BREAK = _env_b("E07_TP_LOOPBREAK")       # ⑪ 末帧不闭合
FOOT_SWAY_MM = _env_f("E07_FOOT_SWAY_MM", 120.0)

# =============================================================== 数值（米）
# ★★★ 举臂目标（唯一「世界 vs 随骨盆」的口径在 `_aim_world` 定死）。
#   峰值 z 的由来：IK 实解上限 1948.8 mm（`probe_e07_baseline.py`）；取 **1930**
#   ⟹ 距门禁 1900 有 30 mm 垫、`arm_reach` 比值实测 ~0.975（顶到 1.0 才算越界）。
RAISE_Z = _env_f("E07_RAISE_Z", 1.930)
if LOW_RAISE:
    RAISE_Z = 1.830                          # ② 举臂不足（低于 1900 ⟹ 判红）
PUMP_DN_Z = _env_f("E07_PUMP_DN_Z", 1.872)
PUMP_UP_Z = _env_f("E07_PUMP_UP_Z", 1.922)
HERO_Z = _env_f("E07_HERO_Z", 1.890)
# ★ 举臂的横向 / 前后：偏体侧外（x）且**略在身前**（y < 0）—— 让臂从头侧**外**过，
#   不擦头（实测 clip_max = 0.0）。
RAISE_X = _env_f("E07_RAISE_X", 0.300)
RAISE_Y = _env_f("E07_RAISE_Y", -0.060)

# 另一臂（R）：下放体侧、略偏后外 —— 全程远离躯干（不接触、不穿模）
OTHER_LOW = {"R": Vector((-_env_f("E07_OTHER_X", 0.355),
                          _env_f("E07_OTHER_Y", 0.120), 0.980))}

# 预蓄（DIP）：★ 拳**向后甩**（+y = 身后）—— 与 E06 的「向前收拳」相反。
DIP_L_Y = (-0.310 if FRONT_WINDUP else _env_f("E07_WINDUP_Y", 0.185))


def _fist_table():
    """按相位给出**固定世界**拳心目标（米）。"""
    l_x, l_y = RAISE_X, RAISE_Y
    table = {
        "DIP": {"L": Vector((0.330, DIP_L_Y, 1.020)),
                "R": Vector((-0.352, 0.150, 0.990))},
        "RAISE": {"L": Vector((l_x, l_y, RAISE_Z)),
                  "R": Vector((-0.368, 0.135, 0.975))},
        "PUMP_DN": {"L": Vector((l_x + 0.002, l_y + 0.010, PUMP_DN_Z)),
                    "R": Vector((-0.360, 0.130, 1.010))},
        "PUMP_UP": {"L": Vector((l_x - 0.002, l_y - 0.002, PUMP_UP_Z)),
                    "R": Vector((-0.352, 0.126, 1.035))},
        "HERO": {"L": Vector((l_x - 0.004, l_y - 0.025, HERO_Z)),
                 "R": Vector((-0.345, 0.115, 1.048))},
        "SETTLE": {"L": Vector((0.220, -0.196, 1.580)),
                   "R": Vector((-0.250, 0.020, 1.180))},
    }
    if SYM:
        # ③ 双臂都举（对称）⟹ 左右拳 z 差 → 0 ⟹ `v2_asym_ok` 红。
        table["RAISE"]["R"] = Vector((-l_x, l_y, RAISE_Z))
        table["PUMP_DN"]["R"] = Vector((-l_x - 0.002, l_y + 0.010, PUMP_DN_Z))
        table["PUMP_UP"]["R"] = Vector((-l_x + 0.002, l_y - 0.002, PUMP_UP_Z))
        table["HERO"]["R"] = Vector((-l_x + 0.004, l_y + 0.025, HERO_Z))
    if CONTACT:
        # ④ 举起的那只手落在胸前（贴身）⟹ `v2_no_contact_ok` 红（拳心距躯干 ≈ 20 mm）。
        for key in ("RAISE", "PUMP_DN", "PUMP_UP", "HERO"):
            table[key]["L"] = Vector((0.090, -0.235, 1.255))
    return table


FIST_TABLE = _fist_table()
ELBOW_DIR = {"L": Vector((0.42, 1.00, -0.22)),
             "R": Vector((-0.42, 1.00, -0.22))}

# ★★ 拳**面**朝向混合：本支 = **0.0**（拳沿前臂「顶天」）—— 与 E06 的 1.0 相反，
#   是**设计**：本支不接触任何东西，「举拳」= 拳轴与臂轴同向。blend ≡ 0 ⟹ 不查胸面。
FIST_FACE_BLEND = 0.0
FACE_RAMP_IN = (0, 1)
FACE_RAMP_OUT = (TOTAL - 1, TOTAL)

# ★★ 手心**滚转基准**：`thumb_out`（±X 体侧外）。本支拳轴 ≈ +Z（顶天）⟹ ±X 与拳轴
#   近乎正交 ⟹ 本支实测余量 **0.9179**（E06 的同基准只有 0.6822，**不许照抄**）。
HAND_AXIS_MODE = os.environ.get("E07_HAND_AXIS", "thumb_out")
HAND_CHIRALITY = {"L": 1.0, "R": 1.0}
TWIST_SPLIT = _env_f("E07_TWIST_SPLIT", 0.6)
FOREARM_TWIST_DEG = _env_f("E07_FOREARM_TWIST", 0.0)
# ★★★ 肘极向量的**逐帧限速**（度/帧，0 = 不限）。
#   为什么必须限：肘极决定肘落在臂轴的哪一侧，而 `_bulge_dir` 拿「上一帧肘」当参考 ——
#   臂轴扫得快时（起手段 f7~f11，拳从身前甩到身后 500 mm），投影出的肘极会**翻转**
#   ⟹ 前臂单帧真转 **44.9°**（`forearm.L` @ f9，门槛 25°）。
#   ★ 限速**不影响拳的命中**：`elbow = 肩 + (轴·cos + 极·sin)·上臂长`，而前臂方向恒
#     `fo_dir = 目标 − 肘` ⟹ 目标永远被命中，肘极只决定「肘落哪一侧」。
BULGE_MAX_DEG = _env_f("E07_BULGE_MAX", 8.0)
# ★★★ 手掌世界朝向的**逐帧限速**（度/帧，0 = 不限）。
#   为什么：拳头/手指的**世界朝向**由 `orient_hand` 直接钉住（`y_dir` = 拳轴、`x_hint`
#   = 拳面基准），于是它同时是「前臂方向」与「平行移动基准」的函数 —— 起手段臂轴
#   每帧扫 30°+ 时，手的世界朝向跟着跳 **25.2°**（`thumb_02.L` @ f11，门槛 25.0，
#   实测 25.198 —— 差 0.2° 过线）。限速**完全不改变任何骨骼的位置**（只改拳头朝哪），
#   是这条判据最直接的落点。★ 物理上也对：软组织/腕关节的跟随本来就有滞后。
HAND_MAX_DEG = _env_f("E07_HAND_MAX", 12.0)
# ★★★ 起手段的**时相缓动**（治「前臂真角步 25.022°/帧 @ f10」）：
#   现象（`E07_TRACE_STEP=1` 实测）：f8→f12 前臂.L 的**矩阵口径**角步 16.31 / 22.28 /
#   **25.02** / 23.27 / 18.87（门槛 25.0），而同期 euler 口径只有 7.96 / 10.53 / 11.59。
#   差 2.1 倍 = 前臂**世界**朝向 = 上臂旋转 × 前臂局部旋转 的**复合**（两手各转 ~11.6°
#   ⟹ 合起来 ~23°）。所以治它要治**目标扫过的角速度**，不是治某根骨头的局部量。
#   为什么 `smoothstep` 不行：它的峰值斜率 = **1.5×平均**（把 583 mm / 14 帧的行程
#   压到 f7 附近冲过去）；而实测峰值落在 f10 —— 因为 `arm_env` 也是 smoothstep，
#   两者相乘 `g·g′` 的峰还在更后面。
#   改法：`swing` = **梯形速度**（匀加速 a → 匀速 1−2a → 匀减速 a），峰值斜率
#   **1/(1−a)**。a = 0.15 ⟹ 1.176（比 smoothstep 低 **21.6%**），端点速度仍为 0
#   ⟹ 相位键姿态**逐位不变**（t=0/1 处两种缓动都给 0/1），接缝与定格窗都不受影响。
DIP_EASE = os.environ.get("E07_DIP_EASE", "swing")
SWING_EASE_A = _env_f("E07_SWING_A", 0.15)
# ★★★ 守护手（非举起手）的**整臂逐位继承站架臂**（治 `victory_hand_no_pierce_ok`）：
#   现象：R 手全程守在站架护位（目标只动 ≤ 5 mm）却仍在 f6 深 **−15.81 mm**、
#   f102 深 **−15.90 mm**（站架基线 **−4.05**，下限 −10；起手 f6 / 收招 f102 各 5 个
#   顶点越过绝对下限）。★ 这是**差分口径**的典型反例：位置几乎没动，却比站架差。
#   根因（`E07_DBG` 实测）：解 IK 时 `y_dir` 被按 `env` 从站架手轴混向 `along`
#   （= 拳心 − 肘），而 `along` 与站架手轴差 **49.9°**（f0 实测）—— 于是「守位手」
#   在 f6 被无谓地转了 **10.1°**，指尖离腕 ~150 mm ⟹ 指尖被推进胸腔 ~12 mm。
#   ★ 试过并**否掉**：只把手**朝向**钉成站架手轴（位置仍解 IK）⟹ 更差
#     （f6 −20.53、f99 −20.29、越限顶点 9）。
#   定稿口径：守护手**不解 IK、不混合** —— `pose[up|fo|hd]` 保持 `BASE`（站架臂欧拉）
#   ⟹ `_blend_local` 的 `a == b` ⟹ 混合恒等站架臂。欧拉是相对父骨的量 ⟹ 肩膀以上
#   的躯干一动，整条臂**天然刚体跟随**，护位间隙逐帧守恒。f0 / f120 仍是站架 ⟹
#   接缝逐位不变；举起手（L）完全不受影响。
GUARD_HAND_RIGID = os.environ.get("E07_GUARD_RIGID", "1") != "0"
FIST_MIN_CLEAR_MM = _env_f("E07_FIST_CLEAR", 20.0)
# ★★ 非举起手（off-hand）的口径：
#   `"side"`  = 按 `FIST_TABLE` 摆到体侧后方（原计划）；
#   `"guard"` = **全程守在站架护位**，只做 ≤ 55 mm 的小幅下沉。
OFFHAND_MODE = os.environ.get("E07_OFFHAND", "guard")
OFFHAND_OFF = {
    "STATION": (0.000, 0.000, 0.000),
    "DIP": (-0.030, 0.035, -0.035),
    "RAISE": (-0.040, 0.025, -0.050),
    "PUMP_DN": (-0.038, 0.028, -0.045),
    "PUMP_UP": (-0.042, 0.022, -0.052),
    "HERO": (-0.044, 0.020, -0.055),
    "SETTLE": (-0.015, 0.010, -0.020),
}
# ★ 帧内臂 IK 迭代次数（去滞后 ⟹ 姿态 = 帧号的函数；见 `victory_pose` 的说明）。
ARM_SOLVE_ITERS = max(1, _env_i("E07_ARM_ITERS", 3))
# ★★★ 欧拉混合的**起始带**：`env ≥ EULER_BLEND_AT` 时**完全采用 IK 解**（不混站架）；
#   只有 `env ∈ [0, AT]` 这一段才把 IK 解按二次包络收向站架臂。
#   理由（E07 实测，见 `_blend_local`）：站架臂是「双拳护胸」（R 拳心 (−130,−274,1298)），
#   而 R 臂 IK 目标在「体侧后方」（(−345,115,1048)），两者 euler 差极大 ⟹ 老口径
#   `lerp(station, ik, env)` 在 `env ≈ 0.13` 就把拳顶到 z = 1434 mm、x = −105 mm
#   （躯干内部）⟹ `victory_hand_no_pierce_ok` 红（f105 最深 −15.18 mm）。
EULER_BLEND_AT = _env_f("E07_EULER_AT", 0.0)

# =============================================================== 躯干规格
# ★ 量纲：**全部是相对站架的增量**，3 元组 (rx, ry, rz)（度）；未列出的骨 = 站架值。
#   `loc` = (世界 dy, 世界 dz)（米）：+dy = 身后，+dz = 上。
#   ★★ **`ry` 全程 = 0**（照 E06：腰扭转与「单臂直上」的手势无关，且会破坏接缝对称）。
SPECS = {
    "STATION": {"pelvis": (0.0, 0.0, 0.0), "spine_01": (0.0, 0.0, 0.0),
                "spine_02": (0.0, 0.0, 0.0), "chest": (0.0, 0.0, 0.0),
                "neck": (0.0, 0.0, 0.0), "head": (0.0, 0.0, 0.0),
                "shoulder.L": (0.0, 0.0, 0.0), "shoulder.R": (0.0, 0.0, 0.0),
                "loc": (0.0, 0.0)},
    # ★★ 半蹲下沉 + 拳向后甩：比 E06 的 DIP 深（−55 vs −34 mm）；肩**向后拉**
    #   （`shoulder.L rz = +18` = 向后）为「猛地上举」蓄势；头略低（蓄力）。
    "DIP": {"pelvis": (7.0, 0.0, 0.0), "spine_01": (3.0, 0.0, 0.0),
            "spine_02": (3.0, 0.0, 0.0), "chest": (4.0, 0.0, 0.0),
            "neck": (2.0, 0.0, 0.0), "head": (4.0, 0.0, 0.0),
            "shoulder.L": (-7.0, 0.0, 18.0), "shoulder.R": (-4.0, 0.0, -8.0),
            "loc": (0.030, -0.055)},
    # ★★★ 举到位：左肩**大幅上抬**（rx = +32 ⟹ 肩峰抬升，给足可达高度）+
    #   胸微后仰（庆祝底色）+ 下巴上扬；另一肩下沉后张（对比出自「单臂」）。
    "RAISE": {"pelvis": (-1.0, 0.0, 0.0), "spine_01": (-0.5, 0.0, 0.0),
              "spine_02": (-1.0, 0.0, 0.0), "chest": (-2.0, 0.0, 0.0),
              "neck": (-3.0, 0.0, 0.0), "head": (-9.0, 0.0, 0.0),
              "shoulder.L": (32.0, 0.0, 6.0), "shoulder.R": (-8.0, 0.0, -10.0),
              "loc": (0.004, 0.010)},
    # 拳下沉（庆祝的「抖」下拍）
    "PUMP_DN": {"pelvis": (0.0, 0.0, 0.0), "spine_01": (-0.5, 0.0, 0.0),
                "spine_02": (-1.0, 0.0, 0.0), "chest": (-1.8, 0.0, 0.0),
                "neck": (-2.6, 0.0, 0.0), "head": (-8.0, 0.0, 0.0),
                "shoulder.L": (27.0, 0.0, 6.0),
                "shoulder.R": (-8.0, 0.0, -10.0), "loc": (0.004, 0.004)},
    # 拳回抬（上拍）
    "PUMP_UP": {"pelvis": (-1.0, 0.0, 0.0), "spine_01": (-0.5, 0.0, 0.0),
                "spine_02": (-1.0, 0.0, 0.0), "chest": (-2.2, 0.0, 0.0),
                "neck": (-3.2, 0.0, 0.0), "head": (-9.5, 0.0, 0.0),
                "shoulder.L": (31.0, 0.0, 6.0),
                "shoulder.R": (-8.0, 0.0, -10.0), "loc": (0.002, 0.012)},
    # ★★ 英雄姿：挺胸（chest 绝对值 −2.9）+ 下巴上扬 16.5° + 拳**保持在头侧上方**
    #   + 肩保持上抬（不是收回去）。
    "HERO": {"pelvis": (-1.5, 0.0, 0.0), "spine_01": (-0.5, 0.0, 0.0),
             "spine_02": (-1.5, 0.0, 0.0), "chest": (-3.9, 0.0, 0.0),
             "neck": (-5.5, 0.0, 0.0), "head": (-11.0, 0.0, 0.0),
             "shoulder.L": (29.0, 0.0, 5.0), "shoulder.R": (-6.0, 0.0, -7.0),
             "loc": (0.002, 0.006)},
    # ★ 英雄姿保持（76~88）：与 HERO 只差**不到 0.3°/0.3 mm** ⟹ 读作「稳住不动」。
    "HERO_HOLD": {"pelvis": (-1.4, 0.0, 0.0), "spine_01": (-0.5, 0.0, 0.0),
                  "spine_02": (-1.4, 0.0, 0.0), "chest": (-3.8, 0.0, 0.0),
                  "neck": (-5.4, 0.0, 0.0), "head": (-10.8, 0.0, 0.0),
                  "shoulder.L": (28.8, 0.0, 5.1), "shoulder.R": (-5.9, 0.0, -7.1),
                  "loc": (0.0018, 0.0055)},
    # 回站架途中（残余极小 ⟹ 尾段角步自然收敛）
    "SETTLE": {"pelvis": (0.4, 0.0, 0.0), "spine_01": (0.2, 0.0, 0.0),
               "spine_02": (0.2, 0.0, 0.0), "chest": (0.3, 0.0, 0.0),
               "neck": (-0.2, 0.0, 0.0), "head": (-0.5, 0.0, 0.0),
               "shoulder.L": (3.0, 0.0, -1.5), "shoulder.R": (2.0, 0.0, 1.5),
               "loc": (0.002, -0.003)},
}

_CELEB = ("RAISE", "PUMP_DN", "PUMP_UP", "HERO", "HERO_HOLD")


def spec_of(name):
    spec = dict(SPECS[name])
    if SLUMP and name in _CELEB:
        # ⑦ 不挺胸：把胸从后仰（−3.8）拨到前倾（+3），头也压下来一点。
        rx, ry, rz = spec["chest"]
        spec["chest"] = (3.0, ry, rz)
        nrx, nry, nrz = spec["neck"]
        spec["neck"] = (2.0, nry, nrz)
    if NO_CHIN and name in _CELEB:
        # ⑧ 下巴不上扬：颈 / 头的上扬增量全部清零（只剩站架基线）。
        spec["neck"] = (0.0, 0.0, 0.0)
        spec["head"] = (0.0, 0.0, 0.0)
    return spec


# =============================================================== 关键帧表
#   (帧, 进入本键所用的缓动, 躯干规格名, 拳目标名)
KEYS = [
    (START, None, "STATION", "STATION"),
    (DIP, DIP_EASE, "DIP", "DIP"),
    (RAISE, "smooth", "RAISE", "RAISE"),
]
if not NO_HITSTOP:
    KEYS.append((HOLD[1], "hold", "RAISE", "RAISE"))
KEYS += [
    (PUMP_DN, "smooth", "PUMP_DN", "PUMP_DN"),
    (PUMP_UP, "smooth", "PUMP_UP", "PUMP_UP"),
    (HERO, "smooth", "HERO", "HERO"),
    (HERO_HOLD, "smooth", "HERO_HOLD", "HERO"),
    (SETTLE, "smooth", "SETTLE", "SETTLE"),
    (END, "smooth", "STATION", "STATION"),
]

# =============================================================== 阈值
# ★ 全部由**设计意图 + 实测定**；铁律：不许为了变绿而放宽。
RAISE_Z_MIN_MM = _env_f("E07_RAISE_Z_MIN", 1900.0)     # ★ 过顶（E06 是 ≤1392）
ASYM_MIN_MM = _env_f("E07_ASYM_MIN", 500.0)            # ★ 单臂 ⟹ 左右拳 z 差
NO_CONTACT_MIN_MM = _env_f("E07_NO_CONTACT_MIN", 200.0)  # ★ 拳在空中
WINDUP_BEHIND_MIN_M = _env_f("E07_WINDUP_MIN", 0.10)   # ★ 预蓄拳在身后
PUFF_MAX_RX = _env_f("E07_PUFF_RX", -2.5)
CHIN_RANGE = (_env_f("E07_CHIN_LO", 8.0), _env_f("E07_CHIN_HI", 24.0))
NO_ROAR_MAX = _env_f("E07_ROAR_MAX", 26.0)
HERO_STEP_MAX_DEG = _env_f("E07_HERO_STEP", 1.6)
HERO_MIN_FRAMES = _env_i("E07_HERO_N", 8)
HITSTOP_STEP_MAX_DEG = _env_f("E07_HITSTOP_STEP", 0.01)
FOOT_LOCK_MM = _env_f("E07_FOOT_LOCK", 0.5)
TOE_LOCK_MM = _env_f("E07_TOE_LOCK", 0.5)
SOLE_BAND = (-2.0, 6.0)
NO_SNAP_END_DEG = _env_f("E07_SNAP_END", 6.0)
SEAM_POS_MAX_MM = _env_f("E07_SEAM_POS", 0.01)
SEAM_DIR_MAX_DEG = _env_f("E07_SEAM_DIR", 0.05)
CLIP_MAX_MM = _env_f("E07_CLIP_MAX", 0.0)
REACH_MAX_RATIO = 0.995
MATRIX_STEP_MAX_DEG = _env_f("E07_MATSTEP", 25.0)
TAIL_SETTLE_N = _env_i("E07_TAIL_N", 10)
HAND_PIERCE_MM = _env_f("E07_HAND_PIERCE", 10.0)
HAND_X_HINT_MIN_MARGIN = _env_f("E07_HINT_MARGIN", 0.45)

# 出图/像素探针共用的**逐帧集合**（主渲 / 反面重渲 / 像素探针三者必须逐帧相同）
STEM_FRAMES = sorted(set([0, 7, 14, 22, 30, 34, 36, 37, 42, 46, 50, 54, 62,
                          70, 76, 82, 88, 96, 102, 108, 114, 120]))

# =============================================================== 取景（★ 本支自立）
# ★ 取景跨度的由来：本支**不跳不躺**，纵向最高点 = 举拳时拳心 z ≈ 1930 + 拳半径
#   （≈ 1975 mm），最低点 = 鞋底 0 mm ⟹ 纵向覆盖 −0.15 ~ 2.11 m（中心 z = 0.98、
#   正交高 2.25 m）；横向需 ≥ ±0.45 m ⟹ 正面 780×1100（横 = 2.25×780/1100 = 1.595 m）。
VIEW_E07_SIDE = ("side", (4.4, -0.05, 0.98), (0.0, -0.05, 0.98), 2.25,
                 (780, 1100))
VIEW_E07_FRONT = ("front", (0.0, -4.9, 0.98), (0.0, 0.0, 0.98), 2.25,
                  (780, 1100))

TRACE = _env_b("E07_TRACE")
_BLEND_TRACE = _env_b("E07_TRACE_BLEND")
_BLEND2_TRACE = _env_b("E07_TRACE_BLEND2")
# 定点诊断（临时）：E07_DBG="11,12,99,100" E07_DBG_SIDE="R"
DEBUG_FRAME = -1
DEBUG_FRAMES = set(int(x) for x in os.environ.get("E07_DBG", "").split(",")
                   if x.strip())
DEBUG_SIDES = set(x.strip() for x in os.environ.get("E07_DBG_SIDE",
                                                    "L,R").split(",")
                  if x.strip())
IK_TRACE = _env_b("E07_TRACE_IK")
_STEP_TRACE = _env_b("E07_TRACE_STEP")

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
# 定点诊断（临时）：本帧站架拳位 / 本帧包络 / 帧内迭代序号
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
        # ★★ 梯形速度（见 `DIP_EASE` 的说明）：峰值斜率 1/(1−a)，端点斜率恒 0。
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
    ★★ `ARM_DN_AT` = 88 = `HERO_HOLD` ⟹ 英雄姿窗口（76~88）内 `env ≡ 1`（零变化）；
      `ARM_DN_DONE` = 110 **早于** `no_snap_stop_ok` 的判定窗（f110~120）。
    """
    if frame <= ARM_UP_AT:
        return _smoothstep(frame / float(max(1, ARM_UP_AT)))
    if frame >= ARM_DN_AT:
        span = float(max(1, ARM_DN_DONE - ARM_DN_AT))
        return _smoothstep((ARM_DN_DONE - frame) / span)
    return 1.0


def face_blend(frame):
    """本支 `FIST_FACE_BLEND = 0` ⟹ 恒 0（拳沿前臂「顶天」，不掺「拳面朝内」）。"""
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
    """欧拉表示兼容化（C14 / D01 / E03 / E04 / E05 / E06 踩过的同一个万向节锁坑）。

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
        #   搬不回去。E07 实测：`forearm.R` 的 DP 路径中途需要「另一基」，末帧却被
        #   钉回原始表示 ⟹ 与上一帧差 **(180, 162.2, 180)** —— 矩阵完全没动，但 euler
        #   口径单帧 180° 假跳，`no_snap_stop_ok` / `no_teleport` / `v2_matrix_step_ok`
        #   全红。改法：末帧只在 **base0（= 原始表示 + 360° 整数倍，索引 0..26）** 里挑，
        #   剩下的 360° 差值交给 `seam_canonicalize` 整体平移消化。
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
        # ★ 末帧**不再**无条件钉回原始表示（那正是 180° 假跳的来源）；它已由上面的
        #   `cand` 约束保证「与首帧同基」，余下的 360° 由 `seam_canonicalize` 消化。

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

    ★★ **本支是「全程」口径**（E07 不跳、不位移）：`want` 恒 = 站架踝
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
    """把拳目标**顶出**胸腔（沿胸面外法线），只在该点比下限更深时才动它。

    ★ 本支目标全在空中（离躯干 ≥ 200 mm）⟹ 正常情况**一次也不触发**；保留它作为
      「拳不会穿进躯干」的结构性保护（与 E03/E06 同族）。
    """
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
INSIDE_VOTES_MIN = _env_i("E07_INSIDE_VOTES", 7)
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
    """**指节面**（`Finger_*` 顶点）到躯干面的**最小带符号距离**（mm）。

    ★ 本支不接触躯干 ⟹ 该读数应当**很大且为正**（`v2_no_contact_ok` 的量化载体）。
    """
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
    """给出「`hand.local_x` 应指向的世界方向」。

    ★★★ E07 定稿口径：**平行移动（parallel transport）优先**。
    设计基准（`thumb_out` = +X 体侧外）在本支**起手段** f9~f11 与拳轴只剩 15.6°
    （`v2_x_hint_margin` 实测 0.2688 < 0.45）—— 基准一退化，`orient_hand` 的正交化
    就把整只手**真翻 180°**（f10 `hand.L` 单帧 euler 116°、矩阵 85.7°）。
    改法：拿**上一帧实测的手 x 轴**当基准 —— 它恒 ⊥ 上一帧拳轴 ⟹ 只要拳轴每帧转
    < 50°，余量 ≥ 0.82，**永不退化**。设计基准只在**第 0 帧**（`LAST_HAND_X` 尚未
    建立）当种子用一次。
    """
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
    # ★ 返回**实际生效**的手 x 轴（限速后），供下一帧的平行移动当种子。
    return basis.to_3x3().col[0].normalized().copy()


# =============================================================== 臂 IK
ELBOW_POLE = {"L": Vector((0.42, 1.00, -0.22)),
              "R": Vector((-0.42, 1.00, -0.22))}
LAST_TWIST_ANGLE = {}
LAST_ELBOW = {}
LAST_BULGE = {}
LAST_REP = {}
# ★★ 上一帧**实际采用的臂混合结果**（欧拉）—— `_blend_local` 挑等价表示的参照物。
#   必须每帧只在**迭代收敛后**提交一次，否则帧内迭代会把参照物推着走（自我追尾）。
LAST_BLENDED = {}
# ★★ 帧内迭代用 / 帧末提交的**跨帧状态**（区分「上一帧」与「本帧第 n 趟」）：
#   老口径把两者共用一个 `LAST_*` ⟹ 帧内第 2、3 趟读到的是第 1、2 趟的结果，
#   于是「迭代」不是去追不动点，而是**自己推着自己跑**（三趟还不收敛：f102 的
#   `theta` 26.46→14.18→5.36）。E07 实测迭代越多越差（3 趟 44.4° / 10 趟 65.2° /
#   30 趟 76.1°）—— 这就是「迭代发散」的直接证据。
#   改法：帧内写 `FRAME_*`，`LAST_*` 只在**帧末提交一次** ⟹ 迭代是干净的固定点迭代，
#   且姿态 = 帧号 + 上一帧姿态的确定性函数。
FRAME_ELBOW = {}
FRAME_BULGE = {}
FRAME_TWIST = {}
LAST_HAND_Q = {}
FRAME_HAND_Q = {}


def _bulge_dir(side, axis, shoulder):
    """肘的**极方向**（⊥ `axis` 的单位向量）—— 决定肘落在轴的哪一侧。

    ★★★ E07 定稿口径：**固定世界极向量优先（无状态）**。
      老口径（E03~E06）拿「上一帧的肘位置」当极向量，是**跨帧状态** ⟹ 姿态成了
      上一帧姿态的函数，于是：① 定目标不变的帧要好几帧才弛豫到不动点（定格窗
      f34→f35 漂 1.92°）；② 状态一旦分岔就是**真动作跳**（f99→f100 前臂.R 90.2°、
      整串手指 81.9°，两臂同帧发作）。改成固定极向量后，肘方位是**目标的连续函数**，
      姿态是**帧号的纯函数**。
    ★ 只在「上一帧肘」**退化**（与臂轴近乎平行、垂直分量 < 0.05）时，才回落到
      固定世界极向量兜底。
    ★ 试过并**否掉**的方案：「固定世界极向量优先（完全无状态）」。它让 E07 收招段
      R 臂的肘甩到外侧、前臂横切躯干 —— 实测 f99~f102 最深 **−76.0 mm**、越限顶点
      **133**（传入肘优先的口径同段只有 0~21 个）。肘方位必须**跟着上一帧走**。
    """
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
    # ★★★ 逐帧限速：与**上一帧提交的肘极**（`LAST_BULGE`，帧内不变）在「⊥ 臂轴平面内」
    #   比较，超过 `BULGE_MAX_DEG` 就沿测地线拉回。帧内所有趟都对齐同一个上限 ⟹
    #   本帧肘极与上一帧的夹角**恒 ≤ 上限**，与前臂角步直接挂钩。
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
    """把臂解到拳心目标上（结构照抄 E03/E06 的成熟版：IK 连续性 + 旋前分摊 + 包络收敛）。

    ★★★ `env`（= `arm_env(frame)`）是「收招不炸 / 起手不炸」的关键：`env→0` 时把
      IK 解的**三个自由度**（肘极向量、拳轴 `y_dir`、滚转基准 `x_hint`）按 `env`
      向**站架实测值**插值 ⟹ 接缝帧 IK 解**逐位收敛到站架臂**。
    """
    A.apply_pose(arm, pose)
    for side in SIDES:
        up, fo, hd = ("upperarm." + side, "forearm." + side, "hand." + side)
        # ★★★ 守护手（非举起手）**整条臂逐位继承站架臂** —— 不解 IK、不混合。
        #   为什么：本支 R 手的工作就是「什么都不做，守住护位」。解 IK 反而有害：
        #   实测坑 → 修法
        #   ① 肘极按 8°/帧限速 ⟹ 起手/收招段肘**滞后**于躯干 ⟹ `along`（拳心−肘）
        #      与站架手轴差 49.9° ⟹ 混合后的「半 IK 臂」在 f6/f102 把指尖推进胸腔
        #      −15.8 / −15.9 mm（站架基线 −4.05，下限 −10）。
        #   ② 试过「只把手的**朝向**钉成站架手轴」：位置仍解 IK ⟹ 更差
        #      （f6 −20.53、f99 −20.29、越限顶点 9）。
        #   本口径：`pose[up|fo|hd]` 保持 `BASE`（站架臂欧拉）不动 ⟹ `_blend_local`
        #   的 `a == b` ⟹ 混合恒等于站架臂。肩膀以上的躯干一动，整条臂**刚性跟随**
        #   （欧拉是相对父骨的 ⟹ 天然刚体跟随），护位间隙逐帧守恒。
        #   f0 / f120 仍是站架 ⟹ 接缝逐位不变；R 手不再有独立行程 ⟹ 逐帧角步只会更小。
        #   ★ `SYM`（③ 反向验证旋钮）时**不**走这条：那支要求双臂都举。
        if (GUARD_HAND_RIGID and OFFHAND_MODE == "guard"
                and side != RAISE_SIDE and not SYM):
            continue
        shoulder = Vector(A.bone_world(arm, up, "head"))
        core = Vector(targets[side])
        nrm = Vector(normals.get(side, Vector((0.0, -1.0, 0.0)))).normalized()
        # ★ 拳**面**朝向：`along`（拳沿前臂）→ `−nrm`（拳面正对胸）的**测地线**混合。
        #   本支 `blend ≡ 0` ⟹ `y_dir = along`（拳沿前臂「顶天」）。
        #   ★ `along` 的肘参考取**本帧第 n 趟**解出的肘（`FRAME_ELBOW`），首趟回落到
        #     上一帧提交值 —— 这样「拳沿前臂」是自洽的，而跨帧连续性由 `_bulge_dir`
        #     的限速负责（两者职责分离）。
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
            y_dir = _slerp_dir(STATION_HAND_Y[side], y_dir, env)
        target = core - y_dir * HAND_LEN
        delta = target - shoulder
        # ★★★ 三角解**必须用前臂骨长**（224 mm），不是 `ARM_LEN_LO`（322 = 前臂 + 手）——
        #   理由见 E06 的实测（手骨朝向由 `orient_hand` 独立钉住，不沿前臂）。
        limit = (ARM_LEN_UP + FOREARM_LEN) * 0.9995
        distance = max(1e-4, min(delta.length, limit))
        axis = (delta.normalized() if delta.length > 1e-9
                else Vector((0.0, 0.0, -1.0)))
        # ★★★ 肘极向量：沿用「上一帧肘」作连续性参考（见 `_bulge_dir` 的否定实验）。
        bulge = _bulge_dir(side, axis, shoulder)
        if env < 1.0:
            bulge = _slerp_dir(STATION_POLE_DIR[side], bulge, env)
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
        # ★★ `hint` **不再**向 `STATION_HAND_X` 做测地线混合：那两个方向可能近似
        #   反向（守卫姿的手 x 轴 vs `thumb_out` 基准），测地线在反向点不唯一 ⟹
        #   滚转会在收招段乱翻（E07 实测 f95 `hand.R` 单帧 133°）。收招的收敛交给
        #   `_blend_local`（`env→0` 时逐位落到站架臂），不必在这里重复。
        hint = hand_x_hint(side, nrm)
        # ★★★ 腕部轴向滚转的**分配量**由**矩阵几何量**给出（**不读** `rotation_euler.y`，
        #   后者在万向节锁邻域不是连续量 —— E06 实测「欧拉跳而矩阵不动」）。
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
        if DEBUG_FRAMES and DEBUG_FRAME in DEBUG_FRAMES and side in DEBUG_SIDES:
            _hm = DEBUG_HOME.get(side, Vector((0.0, 0.0, 0.0)))
            print("E07_DBG f=%d it=%d %s core=[%.1f,%.1f,%.1f] "
                  "home=[%.1f,%.1f,%.1f] env=%.3f "
                  "along=[%.3f,%.3f,%.3f] ydir=[%.3f,%.3f,%.3f] "
                  "hint=[%.3f,%.3f,%.3f] xaxis=[%.3f,%.3f,%.3f] "
                  "bulge=[%.3f,%.3f,%.3f] theta=%8.2f twist=%8.2f "
                  "elbow=[%.1f,%.1f,%.1f] up=%s fo=%s"
                  % (DEBUG_FRAME, DEBUG_ITER, side, core.x * 1000,
                     core.y * 1000, core.z * 1000,
                     _hm.x * 1000, _hm.y * 1000, _hm.z * 1000, env,
                     along.x, along.y, along.z,
                     y_dir.x, y_dir.y, y_dir.z, hint.x, hint.y, hint.z,
                     x_axis.x, x_axis.y, x_axis.z,
                     bulge.x, bulge.y, bulge.z, theta, twist,
                     elbow.x * 1000, elbow.y * 1000, elbow.z * 1000,
                     tuple(round(v, 1) for v in pose[up]),
                     tuple(round(v, 1) for v in pose[fo])))
        if IK_TRACE:
            _t = Vector(A.bone_world(arm, hd, "tail"))
            print("E07_IK %s core=[%.1f,%.1f,%.1f] sh=[%.1f,%.1f,%.1f] "
                  "dist=%.1f tail=[%.1f,%.1f,%.1f] twist=%.1f ry=%.1f"
                  % (side, core.x * 1000, core.y * 1000, core.z * 1000,
                     shoulder.x * 1000, shoulder.y * 1000, shoulder.z * 1000,
                     delta.length * 1000,
                     _t.x * 1000, _t.y * 1000, _t.z * 1000,
                     twist, math.degrees(
                         arm.pose.bones[hd].rotation_euler.y)))
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
    """拳的**世界**目标点（唯一的「世界 vs 随骨盆」口径在这里定死）。

    ★★★ 固定表（`DIP / RAISE / ...`，定义在**站架基准**上）**随骨盆平移**；
      `STATION` 取站架实测点，同样随骨盆平移。
    """
    base = Vector(resolve_fist(name, side))
    return base + root_off


def fist_targets(arm, frame, root_off, env=1.0, home=None):
    """拳目标 = **绕肩的球面插值**（方向 slerp + 半径缓动）+ **包络向站架拳收敛**。

    ★ 为什么不用世界直线 lerp：两端方向差大时弦会贴近肩关节 ⟹ 肘被折进去再弹出
      ⟹ 前臂世界角步爆表（E04 实测 32.6°/帧）。本支 `DIP → RAISE` 两端方向差
      接近 180°（身后下方 ↔ 头顶上方），**必须**走球面。

    ★★★ 为什么 `env` 还要混**目标点**（不只 `seat_arm` 里的方向）：
      `env` 从 1 收到 0 时若只在**欧拉空间**插值，臂的**真实路径**可能直接穿过躯干
      —— E07 实测 f98~f108 的 R 臂最深 **−124 mm**、570 个顶点越过绝对下限
      （`victory_hand_no_pierce_ok` 红）。把世界目标点也按 `env` 拉向
      **当前躯干坐标系里的站架拳位**（`home`），臂走的才是「从目标平移到站架拳」
      的真路径，`push_out` 也才有机会护住它。
    """
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
        if (OFFHAND_MODE == "guard" and side != RAISE_SIDE and home is not None
                and not SYM):
            # ★★ 非举起手**守在站架护位**：目标 = 当前躯干坐标系里的站架拳位 + 小幅偏移。
            #   为什么必须这样：R 臂原计划从站架（拳心 (−130,−274,1298)）甩到体侧后方
            #   （(−345,115,1048)）再收回 —— 517 mm 的大行程叠加 `env` 欧拉混合，
            #   E07 实测在收招段把拳甩到 (−496,−249,1103)（离两端都远 200 mm 以上），
            #   并引发 `forearm.R` 单帧 47° 真跳 + f105 拳心穿躯干 −15.18 mm。
            #   守位后行程降到 ~50 mm ⟹ IK 目标近静止 ⟹ 闭环（肘极 ↔ 拳轴）立刻收敛。
            oa = Vector(OFFHAND_OFF.get(a_name, (0.0, 0.0, 0.0)))
            ob = Vector(OFFHAND_OFF.get(b_name, (0.0, 0.0, 0.0)))
            point = Vector(home[side]) + oa + (ob - oa) * ga
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
    """臂的包络混合：**等价表示连续性优先 + 欧拉线性插值**。

    ★★★ E07 定稿口径：`pick` 的参照物是**上一帧已用过的混合结果**
      （`LAST_BLENDED`），不是「站架」。理由（E07 实测，diag5 + E07_TRACE_BLEND2）：

      收招段（f89~f109）`env` 从 1→0，`station` 恒为站架臂。老口径每帧独立地
      挑「离站架最近的等价表示」——`ik` 的 XYZ 欧拉在 f100 前后**换到了另一套
      等价表示**（`_euler_family` 的 base1，与 base0 相差 360° 整数倍组合）。
      两个表示端点旋转**完全相同**，但 `a + e·(pick − a)` 在 `e = 0.5` 附近的
      **中间值完全不同** ⟹ 最终姿态在 f99→f100 **真跳**：
      R 拳 `[-482.8,-277.1,1131.8] → [-113.1,-150.1,1330.2]`（一跳 450 mm），
      前臂指向转 87°（矩阵口径 f100 `forearm.R` **90.2°**，门槛 25°）。

      改法：`pick = _nearest_family(b, LAST_BLENDED[name])`，首帧（无历史）仍以
      站架为参照。`ik` 连续 ⟹ 表示也连续 ⟹ 混合路径连续。
      ★ `env = 0` 时逐位返回 `a` ⟹ 接缝仍逐位等于站架（末帧逐位约束不靠这里）。

    ★ 试过并否掉的方案：四元数 slerp。它虽然对表示免疫，但插的是**绕轴的大圆弧**，
      E07 实测 f96~f98 收招段 R 拳被甩到躯干里 **−74.5 mm**（比欧拉线性插值差得多）。
    """
    out = {}
    for name in ARM_BONES:
        a = tuple(station.get(name, (0.0, 0.0, 0.0)))
        b = tuple(ikpt.get(name, (0.0, 0.0, 0.0)))
        raw = max(0.0, min(1.0, float(env)))
        # ★★ 二次包络：`env ≥ AT` ⟹ 逐位采用 IK 解；`env ∈ [0, AT]` ⟹ 平滑收向站架臂。
        e = raw if EULER_BLEND_AT <= 0.0 else _smoothstep(raw / EULER_BLEND_AT)
        ref = LAST_BLENDED.get(name)
        pick = _nearest_family(b, a if ref is None else ref)
        if _BLEND_TRACE:
            print("E07_BLEND %-12s env=%.3f at=%.2f e=%.3f span=%.1f"
                  % (name, raw, EULER_BLEND_AT, e,
                     max(abs(y - x) for x, y in zip(a, pick))))
        out[name] = tuple(x + (y - x) * e for x, y in zip(a, pick))
    return out


def victory_pose(arm, frame):  # noqa: C901
    # ★★★ 定格窗：窗内**每一帧直接求值到窗首帧**。
    #   这是「打击停顿」的正确定义（姿态逐位冻结），也把 `v2_hitstop_ok` 从
    #   「靠状态收敛」变成「构造保证」—— 修前实测 f34 尚未收敛，f34→f35 有 1.92° 漂移。
    #   ★ `NO_HITSTOP`（⑥ 反向验证旋钮）时**不冻结**：否则「抽掉键表 hold 行」只是
    #     惰性改动 —— 定格仍由这里的逐位求值保证，断言照样绿（真抽掉 = 两处一起抽）。
    if not NO_HITSTOP:
        for _hold in HOLDS:
            if _hold[0] < frame <= _hold[1]:
                frame = _hold[0]
                break
    spec = torso_at(frame)
    pose = {}
    for key in ("pelvis", "spine_01", "spine_02", "chest", "neck", "head",
                "shoulder.L", "shoulder.R"):
        va = BASE.get(key, (0.0, 0.0, 0.0))
        pose[key] = tuple(va[i] + spec[key][i] for i in range(3))
    # ★ ⑨ 英雄姿颤抖旋钮：在 HERO..HERO_HOLD 窗口内逐帧交替 ±3°（真接进姿态）。
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
        # ⑩ 脚滑：**脚不再锁世界，改骑在当前骨盆上**（躯干一动脚就跟着动）。
        A.apply_pose(arm, pose)
        delta = Vector(A.bone_world(arm, "pelvis", "head")) - PELVIS0
        scale = FOOT_SWAY_MM / 55.0
        for s in SIDES:
            want[s] = want[s] + delta * scale
    lock_err = lock_feet(arm, pose, want)

    # ---- 臂：解 IK，再按 `arm_env` 与站架臂混合（保证接缝）-------------------
    global DEBUG_FRAME, DEBUG_HOME, DEBUG_ITER
    DEBUG_FRAME = frame
    env = arm_env(frame)
    A.apply_pose(arm, pose)
    # ★ 站架拳位（**当前躯干坐标系**里）：此刻 `arm` 还停在站架臂上 ⟹ 读到的就是它。
    #   收招段的目标点要向它收敛（见 `fist_targets` 的 `env/home`）。
    home = {s: Vector(A.bone_world(arm, "hand." + s, "tail")) for s in SIDES}
    DEBUG_HOME = home
    targets = fist_targets(arm, frame, root_off, env, home)
    dummy = {s: Vector((0.0, -1.0, 0.0)) for s in SIDES}
    # ★★★ **逐帧迭代求解到不动点**：`seat_arm` 的肘极向量取自**上一帧**（连续性设计），
    #   于是每帧解出的姿态依赖历史 —— 定目标不变的帧（定格窗）要 2~3 帧才收敛
    #   （E07 实测 f34 (1.92°)→f35 (0.00°)），而 `HITSTOP_STEP_MAX_DEG = 0.01`。
    #   在帧内多迭代几次 ⟹ 姿态是**帧号的函数**（无滞后），定格窗自然逐位相同。
    blended = None
    for _it in range(ARM_SOLVE_ITERS):
        DEBUG_ITER = _it
        ik_pose = dict(pose)
        seat_arm(arm, ik_pose, targets, dummy, face_blend(frame), env)
        blended = _blend_local(pose, ik_pose, env)
    for name in ARM_BONES:
        pose[name] = blended[name]
    # ★★ 跨帧状态**每帧提交一次**（帧内迭代收敛后）：等价表示参照物 + 肘极 / 肘 / 滚转角。
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

    if _BLEND2_TRACE and ((not DEBUG_FRAMES) or frame in DEBUG_FRAMES):
        for side in SIDES:
            A.apply_pose(arm, pose)
            pa = Vector(A.bone_world(arm, "hand." + side, "tail"))
            A.apply_pose(arm, ik_pose)
            pb = Vector(A.bone_world(arm, "hand." + side, "tail"))
            qb = Vector(A.bone_world(arm, "forearm." + side, "head"))
            A.apply_pose(arm, blended)
            pc = Vector(A.bone_world(arm, "hand." + side, "tail"))
            qc = Vector(A.bone_world(arm, "forearm." + side, "head"))
            print("E07_B2 f=%3d %s env=%.3f st=[%7.1f,%7.1f,%7.1f] "
                  "ik=[%7.1f,%7.1f,%7.1f] bl=[%7.1f,%7.1f,%7.1f] "
                  "ikelb=[%7.1f,%7.1f,%7.1f] blelb=[%7.1f,%7.1f,%7.1f]"
                  % (frame, side, env,
                     pa.x * 1000, pa.y * 1000, pa.z * 1000,
                     pb.x * 1000, pb.y * 1000, pb.z * 1000,
                     pc.x * 1000, pc.y * 1000, pc.z * 1000,
                     qb.x * 1000, qb.y * 1000, qb.z * 1000,
                     qc.x * 1000, qc.y * 1000, qc.z * 1000))

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
        gaps = {s: round(signed_to_torso(
            A.bone_world(arm, "hand." + s, "tail")), 1) for s in SIDES}
        print("E07_TRACE f=%3d dy=%+6.1f dz=%+6.1f sole=%s core=%s gap=%s "
              "lock=%.4f env=%.3f" % (frame, dy * 1000.0, dz * 1000.0, soles,
                                      cores, gaps, lock_err, env))
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


# =============================================================== 专属门禁
def victory_assertions(arm, action, samples, meshes):  # noqa: C901
    res = {}
    scene = bpy.context.scene
    frames = [s["frame"] for s in samples]
    idx = {s["frame"]: i for i, s in enumerate(samples)}
    arm.animation_data.action = action
    A._bind_slot(arm, action)

    def head_back_deg(frame):
        """仰头 / 下巴上扬角（度，**正 = 后仰**）= −(Δneck_rx + Δhead_rx)。

        ★ samples[...]["euler"] 已是 **度**，**不可**再乘 180/π（E06 踩过：虚增 57.3 倍）。
        """
        e = samples[idx[frame]]["euler"]
        e0 = samples[0]["euler"]
        d_neck = (e.get("neck", (0.0, 0.0, 0.0))[0]
                  - e0.get("neck", (0.0, 0.0, 0.0))[0])
        d_head = (e.get("head", (0.0, 0.0, 0.0))[0]
                  - e0.get("head", (0.0, 0.0, 0.0))[0])
        return -(d_neck + d_head)

    def chest_rx_deg(frame):
        return samples[idx[frame]]["euler"].get("chest", (0.0, 0.0, 0.0))[0]

    # ---- ① ★★★ 举拳高度（本支命门）----------------------------------------
    raise_win = sorted(set([RAISE] + [HOLD[0], HOLD[1]]))
    rows = {}
    for frame in raise_win:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        row = {}
        for side in SIDES:
            core = Vector(A.bone_world(arm, "hand." + side, "tail"))
            row[side] = {"core_mm": [round(v * 1000.0, 2) for v in core],
                         "core_gap_mm": round(signed_to_torso(core), 2),
                         "knuckle_gap_mm": fist_face_gap(side, step=2)}
        row["fist_z_diff_mm"] = round(
            (Vector(row["L"]["core_mm"]) - Vector(row["R"]["core_mm"])).z, 2)
        rows[str(frame)] = row
    res["v2_raise_geometry"] = rows

    raise_z = min(rows[str(f)][RAISE_SIDE]["core_mm"][2] for f in raise_win)
    res["v2_raise_z_min_mm"] = raise_z
    res["v2_raise_z_limit_mm"] = RAISE_Z_MIN_MM
    res["v2_raise_z_min_ok"] = bool(raise_z >= RAISE_Z_MIN_MM)
    res["v2_raise_z_min_note"] = (
        "★★★ **本支的命门**：「举拳」= 拳心必须**过顶**。判据 = 举到位窗口（f=%s）内"
        "举起臂（%s）拳心的**最低 z** ≥ %.0f mm（E06 的拳心 z ≤ 1392 mm，"
        "「胸/肩」高度）。实测 **%.1f mm** —— 比 E06 高 %.1f mm，比角色头顶"
        "（1803 mm）高 %.1f mm。★ 目标 z 由**实测定标**：`probe_e07_baseline.py` 用"
        "E06 的 `seat_arm` 真解 IK，z ≤ 1940 精确命中、z ≥ 1980 起饱和在 1948.8 mm"
        "⟹ 峰值取 1930（距门禁 30 mm 垫、臂长比值 ~0.975）。"
        "★ 旋钮 ② `LOW_RAISE` 把目标压到 1830 ⟹ 本判据变红。"
        % (raise_win, RAISE_SIDE, RAISE_Z_MIN_MM, raise_z, raise_z - 1392.0,
           raise_z - 1803.0))

    # ---- ② ★★★ 单臂（不对称）---------------------------------------------
    asym = min(rows[str(f)]["fist_z_diff_mm"] for f in raise_win)
    res["v2_asym_min_mm"] = asym
    res["v2_asym_limit_mm"] = ASYM_MIN_MM
    res["v2_asym_ok"] = bool(asym >= ASYM_MIN_MM)
    res["v2_asym_note"] = (
        "★★★ 「举拳」是**单臂**（另一臂下放体侧）—— 与 E06 的**双拳同步捶胸**"
        "在「对称性」维度上分离。判据 = 窗口内 min(举起臂拳心 z − 另一臂拳心 z) "
        "≥ %.0f mm。实测 **%.1f mm**。★ 旋钮 ③ `SYM` 让双臂同时举起 ⟹ 差 → 0 ⟹ 变红。"
        % (ASYM_MIN_MM, asym))

    # ---- ③ ★★★ 拳**不接触**躯干（空中）------------------------------------
    contact = min(min(rows[str(f)][RAISE_SIDE]["core_gap_mm"],
                      rows[str(f)][RAISE_SIDE]["knuckle_gap_mm"])
                  for f in raise_win)
    res["v2_no_contact_min_mm"] = contact
    res["v2_no_contact_limit_mm"] = NO_CONTACT_MIN_MM
    res["v2_no_contact_ok"] = bool(contact >= NO_CONTACT_MIN_MM)
    res["v2_no_contact_note"] = (
        "★★★ E06 是**接触型**（拳面贴胸 +1.13 mm）；本支是**非接触型**（拳在空中）。"
        "判据 = 窗口内举起臂的「拳心到躯干面」与「指节面到躯干面」的**较小值** "
        "≥ %.0f mm。实测 **%.1f mm**。★ 旋钮 ④ `CONTACT` 把拳落在胸前 ⟹ 变红。"
        % (NO_CONTACT_MIN_MM, contact))

    # ---- ④ ★★ 第一拍就与 E06 不同（预蓄方向相反）--------------------------
    scene.frame_set(DIP)
    bpy.context.view_layer.update()
    dip_y = Vector(A.bone_world(arm, "hand." + RAISE_SIDE, "tail")).y
    res["v2_windup_y_m"] = round(dip_y, 4)
    res["v2_windup_limit_m"] = WINDUP_BEHIND_MIN_M
    res["v2_windup_behind_ok"] = bool(dip_y >= WINDUP_BEHIND_MIN_M)
    res["v2_windup_behind_note"] = (
        "★★ **连播不自洽的真风险**（清单 §0 第 2 条）：E06 与 E07 **首帧同一姿态**，"
        "若起手第一拍也做「收拳蓄势」就会与前作重影。解法 = **预蓄方向相反**："
        "E06 沉髋时拳**收向前**（f%d 拳心 y = −310 mm，在身前）；本支拳**甩向后**"
        "（f%d 拳心 y = **%+.3f m**，在身后）⟹ 两支在同一帧上拳心 y 相差 ≈ %.0f mm。"
        "判据 = 预蓄帧拳心 y ≥ %.2f m（在身后）。"
        "★ 旋钮 ⑤ `FRONT_WINDUP` 把预蓄照抄成 E06 的向前 ⟹ 变红。"
        % (DIP, DIP, dip_y, dip_y + 0.310, WINDUP_BEHIND_MIN_M))

    # ---- ⑤ ★★ 定格（hitstop，单窗口）-------------------------------------
    hs_steps = {}
    worst_hs = 0.0
    for hold in HOLDS:
        steps = []
        for frame in range(hold[0], hold[1]):
            step, at = _worst_step(samples, idx[frame], idx[frame + 1])
            steps.append((frame, round(step, 6), at))
            worst_hs = max(worst_hs, step)
        hs_steps[str(hold[0])] = [{"from": f, "step_deg": s, "at": a}
                                  for f, s, a in steps]
    res["v2_hitstop_frames"] = HITSTOP_N
    res["v2_hitstop_windows"] = [list(h) for h in HOLDS]
    res["v2_hitstop_steps_deg"] = hs_steps
    res["v2_hitstop_worst_step_deg"] = round(worst_hs, 6)
    res["v2_hitstop_ok"] = bool(
        3 <= HITSTOP_N <= 4 and worst_hs <= HITSTOP_STEP_MAX_DEG
        and all(h[1] - h[0] + 1 == HITSTOP_N for h in HOLDS))
    res["v2_hitstop_note"] = (
        "★★ 「举到位」的那一刻有**打击停顿**：窗口 %s 共 %d 帧内逐帧姿态冻结"
        "（`max |Δ euler|` 实测 **%.6f°**，阈值 ≤ %.2f）。★ 与 E06 的**三窗口**不同："
        "本支是**单窗口**（清单 §1 第 4 维度）；靠 `A.set_hitstop` 把窗口键设 CONSTANT，"
        "帧号前进而姿态不变。★ 旋钮 ⑥ `NO_HITSTOP` **真抽掉键表 `hold` 行**（非惰性）。"
        % ([list(h) for h in HOLDS], HITSTOP_N, worst_hs, HITSTOP_STEP_MAX_DEG))

    # ---- ⑥ ★★ 挺胸（庆祝的躯干载体）--------------------------------------
    puff = {str(f): round(chest_rx_deg(f), 3) for f in (HERO, HERO_HOLD)}
    worst_puff = max(puff.values())
    res["v2_chest_rx_deg"] = puff
    res["v2_chest_puff_max_rx_deg"] = PUFF_MAX_RX
    res["v2_chest_puff_ok"] = bool(worst_puff <= PUFF_MAX_RX)
    res["v2_chest_puff_note"] = (
        "★★ 「胜利」的躯干载体是**挺胸**（`chest rx` **负** = 后仰挺胸）。实测庆祝段"
        "（f=%s）`chest rx` = %s（**必须全部 ≤ %.1f°**）。★ 旋钮 ⑦ `SLUMP` 把胸拨成"
        "前倾（+3°）⟹ 变红。" % ([HERO, HERO_HOLD], puff, PUFF_MAX_RX))

    # ---- ⑦ ★★ 下巴上扬（区间两端；且全程不怒吼）----------------------------
    chin_rows = {str(f): round(head_back_deg(f), 3)
                 for f in (RAISE, PUMP_DN, PUMP_UP, HERO, HERO_HOLD, SETTLE)}
    chin_peak = max(head_back_deg(f) for f in range(START, END + 1))
    celeb_peak = max(head_back_deg(f) for f in (RAISE, HERO, HERO_HOLD))
    res["v2_head_back_deg"] = chin_rows
    res["v2_head_back_peak_deg"] = round(chin_peak, 3)
    res["v2_chin_range"] = list(CHIN_RANGE)
    res["v2_no_roar_max_deg"] = NO_ROAR_MAX
    res["v2_chin_up_ok"] = bool(CHIN_RANGE[0] <= celeb_peak <= CHIN_RANGE[1])
    res["v2_no_roar_ok"] = bool(chin_peak <= NO_ROAR_MAX)
    res["v2_chin_up_note"] = (
        "★★ 「胜利」的头部载体是**下巴上扬**（`head_back` 正 = 后仰 / 上扬）。实测"
        "庆祝段峰值 **%.1f°**（区间 %.0f~%.0f）；全程峰值 **%.1f°**（⟹ 不怒吼，"
        "≤ %.0f°；E03 `Rage` 是 36.0°）。★ 旋钮 ⑧ `NO_CHIN` 清零颈/头增量 ⟹ 变红。"
        % (celeb_peak, CHIN_RANGE[0], CHIN_RANGE[1], chin_peak, NO_ROAR_MAX))

    # ---- ⑧ ★★ 英雄 pose 稳定（**不是颤抖**）------------------------------
    hero_span = HERO_HOLD - HERO + 1
    hero_steps = []
    worst_hero = 0.0
    for frame in range(HERO, HERO_HOLD):
        step, at = _worst_step(samples, idx[frame], idx[frame + 1])
        hero_steps.append((frame, round(step, 6), at))
        worst_hero = max(worst_hero, step)
    res["v2_hero_window"] = [HERO, HERO_HOLD]
    res["v2_hero_frames"] = hero_span
    res["v2_hero_min_frames"] = HERO_MIN_FRAMES
    res["v2_hero_steps_deg"] = [{"from": f, "step_deg": s, "at": a}
                                for f, s, a in hero_steps]
    res["v2_hero_worst_step_deg"] = round(worst_hero, 6)
    res["v2_hero_hold_ok"] = bool(hero_span >= HERO_MIN_FRAMES
                                  and worst_hero <= HERO_STEP_MAX_DEG)
    res["v2_hero_hold_note"] = (
        "★★ 清单风险：「胜利动作的停不能太长，末段必须是**稳定的英雄 Pose** 而非颤抖」。"
        "判据 = `HERO..HERO_HOLD` 窗口 **f=%d~%d 共 %d 帧**内逐帧最大角步 **%.6f°**"
        "（≤ %.2f°/帧）。★ 关键工程约束：`ARM_DN_AT`(= %d) 必须 ≥ 窗口终点，否则"
        "英雄姿窗口内 `arm_env` 仍在变 ⟹ 必然判红（E06 的 FACE_RAMP_OUT 同款坑）。"
        "★ 旋钮 ⑨ `TREMBLE` 在窗口内逐帧交替 ±3° ⟹ 变红。"
        % (HERO, HERO_HOLD, hero_span, worst_hero, HERO_STEP_MAX_DEG, ARM_DN_AT))

    # ---- ⑨ 脚锁（**全程**）+ 鞋底带宽 -------------------------------------
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
    res["v2_ankle_drift_mm"] = {k: round(v, 4) for k, v in drift.items()}
    res["v2_toe_drift_mm"] = {k: round(v, 4) for k, v in toe_drift.items()}
    res["v2_sole_min_mm"] = round(min(sole.values()), 3)
    res["v2_sole_max_mm"] = round(max(sole.values()), 3)
    res["foot_lock_ok"] = bool(
        max(max(drift.values()), max(toe_drift.values())) <= FOOT_LOCK_MM
        and SOLE_BAND[0] <= min(sole.values())
        and max(sole.values()) <= SOLE_BAND[1])
    res["foot_lock_note"] = (
        "★★★ **脚锁「全程」口径**（E07 不跳、不位移）：双腿全程落地 ⟹ `want` 恒 = "
        "站架踝。实测踝漂 **L %.4f / R %.4f mm**、趾漂 **L %.4f / R %.4f mm**"
        "（阈值 %.1f），鞋底 **%.2f ~ %.2f mm**（带 %.0f ~ %.0f）。★ 半蹲下沉 55 mm"
        "全部由腿 IK 吸收，脚一动不动 —— 力量链的腿段证据。"
        % (drift["L"], drift["R"], toe_drift["L"], toe_drift["R"], FOOT_LOCK_MM,
           res["v2_sole_min_mm"], res["v2_sole_max_mm"], SOLE_BAND[0],
           SOLE_BAND[1]))

    # ---- ⑩ 收招 / 过缝 ---------------------------------------------------
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

    # ---- ⑪ 力量传导链（六段：脚 → 腿 → 髋 → 腰 → 肩 → 手）----------------
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
    shoulder = [Vector(s["upperarm." + RAISE_SIDE]) for s in samples]
    shoulder_mm = max((p - shoulder[0]).length for p in shoulder) * 1000.0
    hand = [Vector(s["hand." + RAISE_SIDE + ".tail"]) for s in samples]
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
        "（清单 0.2「不许跳级」）。本支载体：脚 = 髋↔踝距离行程（半蹲靠屈膝）"
        "＋踝全程钉死；腿 = 膝屈角行程；髋 = 骨盆世界行程；腰 = `chest` 俯仰行程；"
        "肩 = **举起侧**肩峰世界行程（`shoulder.L` 从 −7° 抬到 +32°）；手 = 拳心行程。"
        "★ **不是「只有手在动」**：起手半蹲 −55 mm 把脚→腿→髋→腰全部串上。")
    res["chain_present_ok"] = bool(
        foot_axis > 20.0 and knee_deg_span > 0.2 and hip_travel > 2.0
        and waist_deg > 2.0 and shoulder_mm > 1.0 and hand_mm > 20.0)

    # ---- ⑫ 可达性 --------------------------------------------------------
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

    # ---- ⑬ 穿模（臂 vs 头盒，D01 起老口径）-------------------------------
    worst_clip, clip_at = 0.0, None
    for frame in sorted(set(list(range(START, END + 1, 3))
                            + [RAISE, HOLD[0], HOLD[1], PUMP_DN, PUMP_UP,
                               HERO, DIP])):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        clip = PD.clip_metrics(arm)
        if clip["clip_max_mm"] > worst_clip:
            worst_clip, clip_at = clip["clip_max_mm"], (frame, clip["clip_at"])
    res["clip_max_mm"] = round(worst_clip, 2)
    res["clip_at"] = clip_at
    res["no_face_clip_ok"] = bool(worst_clip <= CLIP_MAX_MM)

    # ---- ⑭ 手 vs 躯干：**差分口径**（站架自己就有缺陷）-------------------
    pierce = {}
    walk = sorted(set(list(range(START, END + 1, 3))
                      + [RAISE, HOLD[0], HOLD[1], DIP, HERO, HERO_HOLD]))
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
    res["v2_pierce_scope"] = ["(0, TOTAL) 内全部帧",
                              "排除接缝帧 %s" % sorted(seam_frames)]
    res["v2_pierce_nothumb_worst"] = worst_nt
    res["v2_pierce_nothumb_worst_at"] = worst_nt_at
    res["v2_pierce_nothumb_deepest_mm"] = round(worst_deep, 2)
    res["v2_pierce_nothumb_deepest_at"] = worst_deep_at
    res["v2_pierce_beyond_limit_worst"] = worst_beyond
    res["v2_pierce_beyond_limit_worst_at"] = worst_beyond_at
    res["v2_station_nothumb_count"] = station_nt
    res["v2_station_beyond_limit"] = station_beyond
    res["v2_pierce_all_worst"] = worst_all
    res["v2_pierce_thumb_worst"] = worst_thumb
    res["v2_pierce_detail"] = pierce
    res["victory_hand_no_pierce_ok"] = bool(
        worst_deep >= -HAND_PIERCE_MM and worst_beyond <= station_beyond)
    res["victory_hand_no_pierce_note"] = (
        "★ 本支的拳**全程在空中** ⟹ 这条断言**本应轻松通过**（与 E06 的贴胸相反）。"
        "口径照 E03 v011 的**差分**形式（改的是基准，不是阈值）：本支非拇指最深带符号"
        "距离 **%.2f mm**（@ %s，下限 −%.0f）；**越过绝对下限的顶点数 %d**（@ %s）；"
        "站架基线同一读数 **%d** ⟹ 判据 =「不得比站架更差」。★ 仍要盯 —— 起手"
        "（拳从胸前甩到身后）与收招（从头顶收回胸前）两段会**擦过躯干**。"
        % (worst_deep, worst_deep_at, HAND_PIERCE_MM, worst_beyond,
           worst_beyond_at, station_beyond))

    # ---- ⑮ ★★ 真旋转步长（矩阵口径）—— 与 euler 口径互为交叉验证 ----------
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
                print("E07_STEP f=%3d mat=%6.2f %-12s eul=%7.2f %s"
                      % (frame, _fmax, _fmax_at, _es, _ea))
        prev_basis = current
    res["v2_matrix_step_deg_max"] = round(worst_mat, 3)
    res["v2_matrix_step_at"] = worst_mat_at
    res["v2_matrix_step_ok"] = bool(worst_mat <= MATRIX_STEP_MAX_DEG)
    euler_step, euler_at = 0.0, None
    for index in range(1, len(samples)):
        step, at = _worst_step(samples, index - 1, index)
        if step > euler_step:
            euler_step, euler_at = step, at
    res["v2_euler_step_deg_max"] = round(euler_step, 3)
    res["v2_euler_step_at"] = euler_at
    res["v2_matrix_step_note"] = (
        "★★ **矩阵口径**的逐帧最大真实旋转步 **%.3f° @ %s**（阈值 ≤ %.1f°）；"
        "euler 口径 **%.3f° @ %s**。两者必须**一致地小** —— 差得远就是欧拉表示在跳"
        "（万向节锁），不是动作在跳。★ 风险段：`DIP → RAISE`（拳从身后甩到头顶，"
        "~180° 行程）与 `HERO → SETTLE`（`arm_env` 从 1 收到 0，与目标下移叠加）。"
        "★ 本支先做 `compat_euler`（min-max 瓶颈 DP）再断言。"
        % (worst_mat, worst_mat_at, MATRIX_STEP_MAX_DEG, euler_step, euler_at))

    # ---- ⑯ 手骨滚转基准的退化余量（E03 v009 的教训）---------------------
    res["v2_x_hint_margin"] = round(MIN_HINT_MARGIN, 4)
    res["v2_x_hint_margin_min"] = HAND_X_HINT_MIN_MARGIN
    res["v2_x_hint_margin_ok"] = bool(MIN_HINT_MARGIN
                                      >= HAND_X_HINT_MIN_MARGIN)
    res["v2_x_hint_margin_note"] = (
        "★ `orient_hand` 的滚转基准（`thumb_out` = ±X 体侧外）实测最小余量 **%.4f**"
        "（阈值 ≥ %.2f）。★ 本支与 E06 **同基准但动作不同** ⟹ 必须**重新量**："
        "E06 实测 0.6822（其 `OPEN` 段拳轴逼近 ±X），本支 0.9179（拳轴 ≈ +Z，"
        "与基准近正交）—— **不许照抄 E06 的数**（清单 §1 第 2 条明令）。"
        % (MIN_HINT_MARGIN, HAND_X_HINT_MIN_MARGIN))

    res["phase_markers"] = {
        "START": START, "DIP": DIP, "RAISE": RAISE, "HOLD_END": HOLD[1],
        "PUMP_DN": PUMP_DN, "PUMP_UP": PUMP_UP, "HERO": HERO,
        "HERO_HOLD": HERO_HOLD, "SETTLE": SETTLE, "END": END}
    res["v2_sole_trace_mm"] = {str(f): round(v, 2)
                               for f, v in sorted(sole.items())}
    return res


# =============================================================== 屏幕投影
def landmark_screen(arm, action):
    """把「拳心 / 肩峰」逐帧投影到**正面**屏幕坐标，供像素探针用。"""
    name, loc, tgt, scale, rres = VIEW_E07_FRONT
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
    return {"view": VIEW_E07_FRONT[0], "res": list(VIEW_E07_FRONT[4]),
            "ortho_m": VIEW_E07_FRONT[3], "cam_z": VIEW_E07_FRONT[1][2],
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
    if _env_b("E07_TRACE_EULER"):
        for _fr, _pz in keyframes:
            if _fr <= 2 or _fr >= 118:
                print("E07_EUL f=%3d hand.L=%s hand.R=%s"
                      % (_fr,
                         tuple(round(v, 3) for v in _pz.get("hand.L", ())),
                         tuple(round(v, 3) for v in _pz.get("hand.R", ()))))
    meta = {
        "anim_id": NAME,
        "loop": False,
        "category": "状态与流程",
        "note": ("胜利 B（举拳）：半蹲下沉 → **单臂直上过顶**（拳心 z = %.0f mm）"
                 "→ 定格 %d 帧 → 拳小幅上下震荡 → 挺胸下巴上扬的英雄姿 → 回战斗待机；"
                 "★ 全程原地、脚锁全程；★ 与 E06 `Victory_01` 的四维差异："
                 "手的高度（过顶 vs 胸肩）、单臂 vs 双臂同步、无接触 vs 拳面贴胸、"
                 "单定格 vs 三定格；★ 起手预蓄**方向相反**（拳甩身后 vs 收向身前）"
                 % (RAISE_Z * 1000.0, HITSTOP_N)),
        "frames": [START, END],
        "root_motion_m": [0.0, 0.0],
        "root_motion_z_m": [0.0, 0.0],
        "hitstop_frames": HITSTOP_N,
        "hitstop_windows": [list(h) for h in HOLDS],
        "antic_frame": DIP,
        "hit_frame": RAISE,
        "hit_frames": [RAISE],
        "cancel_frame": HERO,
        "hit_point_m": [RAISE_X, RAISE_Y, round(RAISE_Z, 4)],
        "seam": "%s@%d" % (SEAM_ACTION, SEAM_FRAME),
        "seam_ends": {"start": "%s@%d" % (SEAM_ACTION, SEAM_FRAME),
                      "end": "%s@%d" % (SEAM_ACTION, SEAM_FRAME)},
        "frame_bound_note": ("★ 120 帧 = 2.0 s = E01 登记的**上界** ⟹ 沿用"
                             "（显式声明，不是悄悄超）；清单要求胜利动作 1.5~2.5 s ⟹ 落带内"),
        "view_note": ("★ 本支取景**自立**（不照抄 E06）：纵向 −0.15~2.11 m"
                      "（中心 z=0.98、正交高 2.25 m），比站姿视图**更高**以装下举拳；"
                      "正面判「举拳过顶 + 单臂不对称」，侧视判挺胸 + 下巴上扬，"
                      "3Q 判英雄姿"),
        "foot_lock": {
            "scope": "全程 [START..END]（本支不跳、不位移）",
            "reason": "原地动画 ⟹ 踝恒钉站架点"},
        "raise": {
            "side": RAISE_SIDE,
            "peak_z_mm": round(RAISE_Z * 1000.0, 1),
            "target_m": [RAISE_X, RAISE_Y, round(RAISE_Z, 4)],
            "geom_limit_mm": 1962.9,
            "ik_limit_mm": 1948.8,
        },
        "differentiation_vs_E06": {
            "fist_z_mm": {"E06_max": 1392.0, "E07_min_required": RAISE_Z_MIN_MM},
            "symmetry": {"E06": "双臂同步", "E07": "单臂"},
            "contact_mm": {"E06": 1.13, "E07_min_required": NO_CONTACT_MIN_MM},
            "hitstop": {"E06_windows": 3, "E07_windows": 1},
            "windup_y_mm": {"E06": -310.0, "E07_target": round(DIP_L_Y * 1000.0, 1)},
        },
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    markers = {"START": START, "DIP": DIP, "ANTIC": DIP, "RAISE": RAISE,
               "HIT": RAISE}
    if not NO_HITSTOP:
        markers["HOLD"] = HOLD[1]
    markers.update({"PUMP_DN": PUMP_DN, "PUMP_UP": PUMP_UP, "HERO": HERO,
                    "HOLD_POSE": HERO_HOLD, "RECOV": SETTLE, "END": END})
    A.add_markers(action, markers)
    if not NO_HITSTOP:
        for hold in HOLDS:
            A.set_hitstop(action, hold[0], hold[1])

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
    report["loop_seamless"] = bool(worst_angle <= 0.5
                                   and worst_move <= 0.0005)
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
    A.report("E07_REPORT", report)

    stem_only = os.environ.get("E07_STEM_ONLY") == "1"
    stem_frames = list(STEM_FRAMES)
    if stem_only:
        stem = os.environ.get("E07_STEM", "v2stem")
        A.render_pose_sheet(arm, action, stem_frames, stem,
                            views=(VIEW_E07_SIDE, VIEW_E07_FRONT))
        render_layer(arm, action, stem + "hand", HAND_PREFIX, VIEW_E07_FRONT,
                     stem_frames)
        print("E07_DONE failed=%s non_ok=%s" % (failed, non_ok))
        return

    if not SKIP_RENDER:
        A.render_pose_sheet(arm, action, list(range(START, END + 1, 4)),
                            "v2wide", views=(VIEW_E07_SIDE,))
        A.render_pose_sheet(arm, action, stem_frames, "v2_side",
                            views=(VIEW_E07_SIDE,))
        A.render_pose_sheet(arm, action, stem_frames, "v2_front",
                            views=(VIEW_E07_FRONT,))
        # ★★ 手部**分层**渲染必须用**另一个前缀**（E05 踩过「原地覆盖」的坑）。
        render_layer(arm, action, "v2_hand", HAND_PREFIX, VIEW_E07_FRONT,
                     stem_frames)
        key_frames = [0, 14, 22, 30, 34, 37, 46, 54, 62, 70, 76, 82, 88, 96,
                      102, 108, 114, 120]
        A.render_pose_sheet(arm, action, key_frames, "v2key",
                            views=(VIEW_E07_SIDE, VIEW_E07_FRONT, A.VIEW_3Q))
        with open(os.path.join(A.PREVIEW_DIR, "_e07_landmark.json"), "w",
                  encoding="utf-8") as handle:
            json.dump(landmark_screen(arm, action), handle, ensure_ascii=False)
        A.save_project()
        A.export_glb(arm)
    print("E07_DONE failed=%s non_ok=%s" % (failed, non_ok))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("E07_FAILURE " + traceback.format_exc())
