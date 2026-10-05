"""anim_battle_start —— E05 `Battle_Start` 开战（E 族第五支 / 第 61 支）。

清单原文：「**活动肩膀、碰拳、摆出战斗架势**」。

★★★ 与 E04 `Spawn` 的三处根本不同（开工前想清楚，清单 §「E05 详细计划」）
    ① ★★★ **E05 回到「原地」** —— E04 是 E 族唯一一支带根位移的；本支双腿**全程
       落地**、`root_motion = 0` ⟹ **脚锁口径回到 E01~E03 的「全程」**（`foot_lock_ok`），
       **不是** E04 的**分段**口径。★ 照抄 `spawn_foot_lock_phased_ok` = 错。
    ② ★★★ **本支命门是「碰拳」= 双拳相击** —— 全项目**第一支「手与手」自接触**的动画。
       E03 `rage_chest_hit_ok` 是「拳 vs **躯干**」；本支是「拳 vs **拳**」⟹
       **必须新建两条**断言：
         · `bstart_fist_contact_ok`（两拳**贴合量**，拳面间距小到读得出「碰上了」）；
         · `bstart_fist_no_pierce_ok`（两拳**互不穿透**，拳套不许互相插进去）。
       ★ 两条各有反面控制（② FARCLASH 拉开 / ③ DEEPCLASH 推近）。
    ③ ★★ **「活动肩膀」极容易读成「什么也没做」**（幅度小、且肩部常被大臂遮挡）
       ⟹ 必须**量化**肩部活动幅度（`bstart_shoulder_ok`：肩骨旋转行程 + **肩峰**世界
       行程，区间**两端卡**）+ 出图确认**看得见**。**这是本支最容易失败的地方。**

★★★ 工程件：五段结构（START / SHOULDER / CLASH / STANCE / END，96 帧 = 1.6 s）
    `START(0) → OPEN(12) → SHRUG(24) → WIND(32) → CLASH(46)
      →[碰拳定格 3 帧 46~48]→ STANCE(62) → SETTLE(80) → END(96)`
    · `SHRUG` 段 = **肩绕环**（肩后张 → 前上耸 → 后下收），由肩骨 rx/rz 驱动；
    · `WIND` = 反向预备（收拳蓄势，力量链的「髋」段在这里沉下去）；
    · `CLASH` = 双拳在**胸下沿中线**相击（自动判定两拳贴合）；
    · `STANCE` = 展开、摆出战斗架势；
    · 段间缓动：`smooth` / `accel` / `hold`（**不再用 `decel`**，理由见时间轴注释）。
    ★★ **帧预算**：96 帧 = 1.6 s ≤ E01 登记的 120 帧 / 2.0 s 上界 ⟹ **可直接沿用**
      （**显式声明**，不是悄悄超）。

★★★ 工程件 ②：**碰拳的「会失败」断言怎么量**（本支唯一的几何创新）
    两条断言都建在**同一条几何轴**上：`axis` = 由 L 拳心指向 R 拳心的单位向量。
    · `cropL` = L 手**全部网格顶点**在 +axis 方向的极大投影（= L 拳最靠内的拳面）；
      `cropR` = R 手在 −axis 方向的极大投影。两者都是**真·网格量**，不是球近似。
    · `gap_mm = |cR − cL| − cropL − cropR`
      ⟹ **正** = 两拳之间还有这么大空隙；**负** = 互相插进去这么深。
    · `perp_mm` = 两拳**拳面中心**在 ⊥axis 平面内的距离（防「一拳前一拳后擦身而过」）。
    ★ 贴合 = `gap_mm ≤ CONTACT_MAX`；互不穿透 = `gap_mm ≥ −PIERCE_TOL`。
    ★ 对称 = 两拳心关于中线镜像（`bstart_fist_sym_ok`，照 E04 `px_spawn_feet_sym_ok`
      模式**改成手**）。

★★★ 工程件 ③：**防接缝 / 防瞬停**
    · `arm_env` 在两端 →0 ⟹ IK 解的肘极向量 / 拳轴 / 滚转基准逐位收敛到站架实测值
      ⟹ START / END 逐位 = `Idle_01@0`。
    · 「回 0 完成」帧 `ARM_DN_DONE = 80` **早于** `no_snap_stop` 的判定窗（末 13 帧
      = f83~96）⟹ 尾段臂**已经完全等于站架**，判据自然满足（E04 同一手法）。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python anim_battle_start.py
    SKIP_RENDER=1      只跑门禁不渲图（迭代用）
    E05_TRACE=1        逐帧打印 骨盆位移 / 拳心间距 / 脚锁误差 / env

反向验证（§4 第 7 步，9 组 + 1 组补充）：
    E05_TP_SEAM_ZERO=1    ① 首帧改零位            ⟹ `seam_in_ok`
    E05_TP_FARCLASH=1     ② ★★★ 两拳拉开（本支命门）⟹ `bstart_fist_contact_ok`
    E05_TP_DEEPCLASH=1    ③ ★★★ 两拳推进          ⟹ `bstart_fist_no_pierce_ok`
    E05_TP_NOHITSTOP=1    ④ ★ 碰拳无定格          ⟹ `bstart_clash_hitstop_ok`
    E05_TP_NOSHOULDER=1   ⑤ ★ 肩膀不动            ⟹ `bstart_shoulder_ok`
    E05_TP_FOOTSWAY=1     ⑥ ★ 脚滑                ⟹ `foot_lock_ok`
    E05_TP_ASYMCLASH=1    ⑦ ★ 碰拳不对称          ⟹ `bstart_fist_sym_ok`
    E05_TP_LOOPBREAK=1    ⑧ ★ 末帧不闭合          ⟹ `end_matches_start_ok`
    E05_TP_OVER=1         ⑨ ★ 过头姿态（区间上限）⟹ `bstart_body_sink_ok`
    E05_TP_NOSINK=1       ⑩ ★（补充）不沉不发力    ⟹ `bstart_body_sink_ok`（下限端）
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

NAME = "Battle_Start"
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"
SIDES = ("L", "R")
ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")
ARM_SET = set(ARM_BONES)
ARM_LEN_UP = 0.328
ARM_LEN_LO = 0.224 + 0.098
ARM_TOTAL = ARM_LEN_UP + ARM_LEN_LO
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
# ★ 上游 = `Idle_01@0`。★ 本支**自己测一遍**（清单 §0 ①）：`Idle_01@0` vs
#   `Spawn@末帧`（E04 END 已 = `Idle_01@0`）的逐骨世界矩阵差；两者都是 float32 噪声
#   量级时按语义选。本支是「战斗流程的第一个动作」，START 必须是**战斗待机** ⟹
#   语义上只能是 `Idle_01@0`（★ 实测读数见 `probe_e05_baseline.py` 的 `E05_BASE`）。
SEAM_ACTION = os.environ.get("E05_SEAM_ACTION", "Idle_01")
SEAM_FRAME = _env_i("E05_SEAM_FRAME", 0)

# =============================================================== 时间轴（96 帧 = 1.6 s）
TOTAL = _env_i("E05_TOTAL", 96)
START = 0
END = TOTAL
HITSTOP_N = _env_i("E05_HITSTOP", 3)          # 碰拳定格帧数（2~4）

OPEN_AT = _env_i("E05_OPEN", 12)              # 双臂外张 + 肩后张（活动肩膀第一拍）
SHRUG = _env_i("E05_SHRUG", 24)               # 肩前上耸（活动肩膀峰值）
WIND = _env_i("E05_WIND", 32)                 # 收拳蓄势（反向预备 + 沉髋）
CLASH = _env_i("E05_CLASH", 46)               # ★ 碰拳命中帧（定格起点）
HOLD = (CLASH, CLASH + HITSTOP_N - 1)         # [46, 48]
STANCE = _env_i("E05_STANCE", 62)             # 展开、摆出战斗架势
SETTLE = _env_i("E05_SETTLE", 80)             # 回站架途中
# ★★ 段长与缓动的由来（`_e05_diag.log` 逐帧实测）：
#   `bstart_matrix_step_ok` 首轮唯一红项 = **30.594° @ (49, 'forearm.L')**（阈值 25）。
#   逐帧定位发现根因**不是**动作在跳，而是两条**缓动选错**：
#     · `CLASH → STANCE` 用了 `decel`（= 1−(1−t)²，**开头最快**）⟹ 定格一结束就把
#       整段行程的 **16 %** 塞进第 1 帧（目标 f46=(36,−430,1160) → f49=(73.5,−437,1198)，
#       一帧跳 54 mm）。**「定格之后必须慢起」** ⟹ 改成 `smooth`（smoothstep，两端都慢）。
#     · `SHRUG → WIND` 原来 12 帧 `decel`（开头就吃 16 %），且 `WIND → CLASH` 只有
#       12 帧 `accel`（t²，末帧吃 (2N−1)/N² = 16 %）。本支是「重击」段，`accel`
#       **必须保留**（慢起 → 加速撞上去）；但要把 N 拉长 ⟹ `WIND` 提前到 32、
#       `CLASH` 保持 46（N=14，末帧占比降到 13.8 %），`SHRUG` 后移到 24。
#   ★ 时长**仍是 96 帧 = 1.6 s**（未动 TOTAL）：只挪段界，不加帧。

# 臂包络（★ `ARM_DN_DONE` 必须**早于** no_snap_stop 判定窗 f83~96，见 docstring）
ARM_UP_AT = _env_i("E05_ARM_UP", 12)
ARM_DN_AT = _env_i("E05_ARM_DN", 68)
ARM_DN_DONE = _env_i("E05_ARM_DONE", 80)

# =============================================================== 反向验证旋钮
SEAM_ZERO = _env_b("E05_TP_SEAM_ZERO")        # ① 首帧改零位
FARCLASH = _env_b("E05_TP_FARCLASH")          # ② 两拳拉开（命门）
DEEPCLASH = _env_b("E05_TP_DEEPCLASH")        # ③ 两拳推进（互穿）
# ★★★ `NO_HITSTOP` **必须定义在 `KEYS` 之前**（E03 ⑤ / E04 ④ 的实测教训：
#   只在 `main()` 里把 `set_hitstop` 关掉，姿态仍是冻结的 ⟹ 旋钮**惰性**）。
#   忠实仿真 = **从键表里抽掉 `hold` 行**，让 `CLASH → STANCE` 变成一整段。
NO_HITSTOP = _env_b("E05_TP_NOHITSTOP")
NOSHOULDER = _env_b("E05_TP_NOSHOULDER")      # ⑤ 肩膀不动
FOOT_SWAY = _env_b("E05_TP_FOOTSWAY")         # ⑥ 脚滑（骑骨盆）
ASYM_CLASH = _env_b("E05_TP_ASYMCLASH")       # ⑦ 碰拳不对称（L 拳抬高）
LOOP_BREAK = _env_b("E05_TP_LOOPBREAK")       # ⑧ 末帧不闭合
OVER = _env_b("E05_TP_OVER")                  # ⑨ 过头（区间上限端）
NOSINK = _env_b("E05_TP_NOSINK")              # ⑩（补充）不沉不发力（下限端）
FOOT_SWAY_MM = _env_f("E05_FOOT_SWAY_MM", 120.0)
ASYM_Z_MM = _env_f("E05_ASYM_Z", 100.0)
# ★ ② / ③ 的位移量：沿碰拳轴（±x）把两拳**同时**拉开 / 推近。忠实仿真的关键：
#   **两拳都动**（各 |Δx|）⟹ 拳心间距改变 2·Δx，gap 曲线整体平移；
#   只动一拳会同时污染「对称」门禁，读不出到底是哪条判据在响应。
FARCLASH_MM = _env_f("E05_FARCLASH_MM", 45.0)
DEEPCLASH_MM = _env_f("E05_DEEPCLASH_MM", 45.0)

# =============================================================== 数值（米 / 毫米）
# ★★★ 碰拳摆位**全部来自 `_e05_scan.py` 的实测网格搜索**（`_e05_scan1/2.log`），
#   不照抄 E01~E04，也不照抄本文件初版的拍脑袋值。初版取 (x=±55, y=−0.335,
#   z=1.290)（贴胸、齐下巴），首轮门禁四条同炸：拳面侧向错开 125.9 mm、互插
#   74.7 mm、左拳 425 顶点插进胸腔（最深 −81.5 mm）、右**前臂穿脸** 42 mm。
#   根因：命门点**贴胸又齐下巴** ⟹ 手臂必须横过胸前、前臂送到脸前。
#   扫描结论（`gap` = 两拳拳面沿碰拳轴的空隙；`torD` = 非拇指顶点对躯干面的
#   最深带符号距离，>0 = 全体在体外；`mind` = 两拳网格顶点的真实最近距离）：
#     x=34 y=−0.40 z=1.16 → gap −7.4 / torD **+0.7** / mind 0.1   （贴着，但离胸太近）
#     x=38 y=−0.40 z=1.16 → gap +1.9 / torD **+1.3** / mind 4.0   （贴着，离胸仍太近）
#     x=34 y=−0.44 z=1.16 → gap −0.2 / torD **+37.8** / mind 5.7  ★ 相触且胸口让开 38 mm
#     x=42 y=−0.40 z=1.22 → gap −2.2 / torD **−12.4**（51 个顶点插胸）⟹ 抬到 z=1.22 就插胸
#   ⟹ 命门区在 **z≈1.16（胸下沿 / 剑突高度）、y≈−0.43（胸面前 215 mm）**，
#      x 由「拳面恰相触」定（本支实测 x≈36 ⟹ 两拳心相距 ~72 mm，每只拳面 ~36 mm）。
#   ★ 全部单元格 `sym_x/y/z = 0.00`、`clip = 0.00`（去腰扭转后**精确对称、不穿脸**）。
CLASH_X_MM = _env_f("E05_CLASH_X", 36.0)      # 碰拳帧拳心 x（±）
CLASH_Y_M = _env_f("E05_CLASH_Y", -0.430)
CLASH_Z_M = _env_f("E05_CLASH_Z", 1.160)
SINK_MM = _env_f("E05_SINK_MM", 55.0)         # 碰拳帧躯干下沉（发力）
WIND_SINK_MM = _env_f("E05_WIND_SINK_MM", 60.0)
STANCE_SINK_MM = _env_f("E05_STANCE_SINK_MM", 30.0)
WIND_BACK_M = _env_f("E05_WIND_BACK", 0.045)
CLASH_BACK_M = _env_f("E05_CLASH_BACK", 0.030)
STANCE_BACK_M = _env_f("E05_STANCE_BACK", 0.015)

# =============================================================== 躯干规格
# ★ 量纲：**全部是相对站架的增量**，3 元组 (rx, ry, rz)（度）；未列出的骨 = 站架值。
#   `loc` = (世界 dy, 世界 dz)（米）：+dy = 身后，+dz = 上。
#   ★ 肩骨用 3 元组（本支与 E04 的第一处结构差异：E04 只动 rx；本支 `rz` 也要动
#     —— 「活动肩膀」的**绕环**靠 rx（抬落）× rz（前后）两轴画出来）。
SPECS = {
    "STATION": {"pelvis": (0.0, 0.0, 0.0), "spine_01": (0.0, 0.0, 0.0),
                "spine_02": (0.0, 0.0, 0.0), "chest": (0.0, 0.0, 0.0),
                "neck": (0.0, 0.0, 0.0), "head": (0.0, 0.0, 0.0),
                "shoulder.L": (0.0, 0.0, 0.0), "shoulder.R": (0.0, 0.0, 0.0),
                "loc": (0.0, 0.0)},
    # 第一拍：双肩**后张下沉**（绕环的后半圈起点）+ 胸腔轻微后仰
    "OPEN": {"pelvis": (2.0, 0.0, 0.0), "spine_01": (1.0, 0.0, 0.0),
             "spine_02": (1.0, 0.0, 0.0), "chest": (1.5, 0.0, 0.0),
             "neck": (-1.0, 0.0, 0.0), "head": (-2.0, 0.0, 0.0),
             "shoulder.L": (5.0, 0.0, 15.0), "shoulder.R": (5.0, 0.0, -15.0),
             "loc": (0.014, -0.018)},
    # 峰值：双肩**前上耸**（肩峰顶到最高 —— 「活动肩膀」最可读的一拍）
    "SHRUG": {"pelvis": (-1.0, 0.0, 0.0), "spine_01": (0.0, 0.0, 0.0),
              "spine_02": (1.0, 0.0, 0.0), "chest": (2.5, 0.0, 0.0),
              "neck": (-2.0, 0.0, 0.0), "head": (-3.0, 0.0, 0.0),
              "shoulder.L": (28.0, 0.0, -8.0), "shoulder.R": (28.0, 0.0, 8.0),
              "loc": (0.004, -0.014)},
    # 收拳蓄势：肩**后下收**、沉髋、髋后坐（反向预备 —— 要出拳先收拳）
    "WIND": {"pelvis": (7.0, 0.0, 0.0), "spine_01": (3.5, 0.0, 0.0),
             "spine_02": (3.5, 0.0, 0.0), "chest": (3.0, 0.0, 0.0),
             "neck": (-1.0, 0.0, 0.0), "head": (-3.0, 0.0, 0.0),
             "shoulder.L": (-9.0, 0.0, 11.0), "shoulder.R": (-9.0, 0.0, -11.0),
             "loc": (WIND_BACK_M, -WIND_SINK_MM / 1000.0)},
    # ★★ 碰拳命中：**送肩前压 + 身体下沉**（力量链在命中帧全部到位）。
    #   ★★★ 实测教训（`_e05_scan1.log` / `_e05_scan2.log`）：初版在这里加了
    #   **微拧腰**（`pelvis/spine/chest` 的 `ry` = +2 / +3°）。结果碰拳帧的
    #   `sym_x/y/z` 变成 **2.19 / 13.83 / 27.33 mm**、`perp` 飙到 **125.88 mm**，
    #   而且 `bstart_matrix_step` 在 `upperarm.R` 上炸出 **161.6°**。
    #   根因：**腰扭转按定义就不是左右对称的**（它把整个上身绕竖轴转了一个角），
    #   而「碰拳」是**双手对称**的手势 —— 两句要求物理上互斥。
    #   ⟹ **设计决定：碰拳帧不拧腰**（拧腰留给 E03 捶胸那类**单臂**发力动作）。
    #   力量感改由**送肩（rz）× 下沉（55 mm 屈膝）× 前压（rx）**三件对称载体承担。
    #   去掉 `ry` 后实测 `sym_x/y/z = 0.00 / 0.00 / 0.00`、`perp = 0.00`（精确对称）。
    "CLASH": {"pelvis": (9.0, 0.0, 0.0), "spine_01": (5.0, 0.0, 0.0),
              "spine_02": (5.0, 0.0, 0.0), "chest": (5.0, 0.0, 0.0),
              "neck": (-2.0, 0.0, 0.0), "head": (-4.0, 0.0, 0.0),
              "shoulder.L": (7.0, 0.0, -17.0),
              "shoulder.R": (7.0, 0.0, 17.0),
              "loc": (CLASH_BACK_M, -SINK_MM / 1000.0)},
    # 展开：双拳拉开到护架（比站架略宽略高，读得出「架势」）
    "STANCE": {"pelvis": (4.0, 0.0, 0.0), "spine_01": (2.0, 0.0, 0.0),
               "spine_02": (2.0, 0.0, 0.0), "chest": (1.5, 0.0, 0.0),
               "neck": (-1.0, 0.0, 0.0), "head": (-2.0, 0.0, 0.0),
               "shoulder.L": (3.0, 0.0, -3.0), "shoulder.R": (3.0, 0.0, 3.0),
               "loc": (STANCE_BACK_M, -STANCE_SINK_MM / 1000.0)},
    # 回站架途中（残余极小 ⟹ 尾段角步自然收敛）
    "SETTLE": {"pelvis": (1.0, 0.0, 0.0), "spine_01": (0.5, 0.0, 0.0),
               "spine_02": (0.5, 0.0, 0.0), "chest": (0.4, 0.0, 0.0),
               "neck": (-0.3, 0.0, 0.0), "head": (-0.6, 0.0, 0.0),
               "shoulder.L": (1.0, 0.0, -1.0), "shoulder.R": (1.0, 0.0, 1.0),
               "loc": (0.004, -0.007)},
}


def spec_of(name):
    spec = dict(SPECS[name])
    if NOSHOULDER and name in ("OPEN", "SHRUG"):
        spec["shoulder.L"] = (0.0, 0.0, 0.0)
        spec["shoulder.R"] = (0.0, 0.0, 0.0)
        spec["loc"] = (0.0, 0.0)
    if NOSINK and name in ("WIND", "CLASH", "STANCE"):
        dy, _dz = spec["loc"]
        spec["loc"] = (dy, 0.0)
    if OVER and name == "CLASH":
        dy, _dz = spec["loc"]
        spec["loc"] = (dy, -0.230)
    return spec


# =============================================================== 关键帧表
#   (帧, 进入本键所用的缓动, 躯干规格名, 拳目标名)
KEYS = [
    (START, None, "STATION", "STATION"),
    (OPEN_AT, "smooth", "OPEN", "OPEN"),
    (SHRUG, "smooth", "SHRUG", "SHRUG"),
    (WIND, "smooth", "WIND", "WIND"),
    (CLASH, "accel", "CLASH", "CLASH"),
]
if not NO_HITSTOP:
    KEYS.append((HOLD[1], "hold", "CLASH", "CLASH"))
KEYS += [
    (STANCE, "smooth", "STANCE", "STANCE"),
    (SETTLE, "smooth", "SETTLE", "SETTLE"),
    (END, "smooth", "STATION", "STATION"),
]

# =============================================================== 拳目标（世界，米）
# ★ 本支无根位移（`root_off ≡ 0`），拳目标就是**世界定点**；躯干位移只有 ±60 mm
#   ⟹ 定点不会让手臂被反向拉伸（E04 的问题本支不存在）。
# ★★★ **拳轨迹必须全程在躯干之外**（躯干包围盒 x ∈ [−0.233, 0.238]、y ∈ [−0.217,
#   0.133]、z ∈ [0.826, 1.461]，E04 实测）：站架拳心在**胸前中线**（x=0.145
#   < 躯干半宽），去「体侧后方」的直线弦必然穿胸 ⟹ 逐段设计：
#     STATION →(外下) OPEN →(外上) SHRUG →(外后) WIND →(内前上) CLASH
#            →(中外) STANCE → 回站架。
FIST_OPEN = {"L": Vector((0.330, -0.235, 1.115)),
             "R": Vector((-0.330, -0.235, 1.115))}
FIST_SHRUG = {"L": Vector((0.300, -0.285, 1.395)),
              "R": Vector((-0.300, -0.285, 1.395))}
FIST_WIND = {"L": Vector((0.400, 0.075, 1.185)),
             "R": Vector((-0.400, 0.075, 1.185))}
FIST_CLASH = {"L": Vector((CLASH_X_MM / 1000.0, CLASH_Y_M, CLASH_Z_M)),
              "R": Vector((-CLASH_X_MM / 1000.0, CLASH_Y_M, CLASH_Z_M))}
FIST_STANCE = {"L": Vector((0.235, -0.330, 1.335)),
               "R": Vector((-0.235, -0.330, 1.335))}
FIST_SETTLE = {"L": Vector((0.175, -0.315, 1.288)),
               "R": Vector((-0.175, -0.315, 1.288))}
FIST_TABLE = {"OPEN": FIST_OPEN, "SHRUG": FIST_SHRUG, "WIND": FIST_WIND,
              "CLASH": FIST_CLASH, "STANCE": FIST_STANCE,
              "SETTLE": FIST_SETTLE}
ELBOW_DIR = {"L": Vector((0.42, 1.00, -0.22)),
             "R": Vector((-0.42, 1.00, -0.22))}

# ★★ 拳**面**朝向混合：本支 = **0.0**（拳沿前臂）—— 与 E03（捶胸，需要指节面砸在
#   胸面上）相反，是**设计**不是偷懒：碰拳是「两拳对撞」，拳的方向就是「顺着前臂
#   伸出去」，不需要把 `y_dir` 反折到某个面法线 ⟹ `blend=0` 时手骨的 `ry` 全程
#   不穿 ±90° 奇异带（E03 花了 3 版才治好的病，本支不患病）。
FIST_FACE_BLEND = 0.0
# 拳心保护下限（`push_out` 用）：站架拳心离躯干面 L +100.69 / R +66.63 mm ⟹
# 25 mm 对站架是 **no-op**（接缝不受影响），只兜住摆臂途中擦过躯干的那几帧。
FIST_MIN_CLEAR_MM = _env_f("E05_FIST_CLEAR", 25.0)

# =============================================================== 阈值
# ★ 全部由实测导出（见日志）；铁律：不许为了变绿而放宽。
#   碰拳「贴合」上限：两拳拳面之间允许的最大空隙。**由实测定**（见日志）。
CLASH_CONTACT_MAX_MM = _env_f("E05_CONTACT_MAX", 14.0)
#   碰拳「互不穿透」容差：允许的最大重叠深度（≤ 这个值读作「贴住了」而不是「插进去」）。
CLASH_PIERCE_TOL_MM = _env_f("E05_PIERCE_TOL", 8.0)
#   碰拳「对称」容差（拳心关于中线的镜像偏差）。
SYM_X_MM = _env_f("E05_SYM_X", 20.0)
SYM_Y_MM = _env_f("E05_SYM_Y", 30.0)
SYM_Z_MM = _env_f("E05_SYM_Z", 30.0)
#   碰拳「擦身而过」容差：两拳**拳面中心**在 ⊥ 轴平面内的距离。
CLASH_PERP_MAX_MM = _env_f("E05_PERP_MAX", 35.0)
#   活动肩膀：肩骨旋转行程（度）+ 肩峰世界行程（mm），**两端卡**。
SHOULDER_TRAVEL_RANGE = (_env_f("E05_SHO_LO", 25.0),
                         _env_f("E05_SHO_HI", 110.0))
SHOULDER_TAIL_RANGE = (_env_f("E05_SHOTAIL_LO", 45.0),
                       _env_f("E05_SHOTAIL_HI", 260.0))
#   碰拳发力：躯干下沉（mm）+ 膝屈下限（度），两端卡。
BODY_SINK_RANGE = (_env_f("E05_SINK_LO", 15.0), _env_f("E05_SINK_HI", 95.0))
BODY_KNEE_MIN = _env_f("E05_KNEE_MIN", 48.0)
FOOT_LOCK_MM = _env_f("E05_FOOT_LOCK", 0.5)
TOE_LOCK_MM = _env_f("E05_TOE_LOCK", 0.5)
SOLE_BAND = (-2.0, 6.0)
NO_SNAP_END_DEG = _env_f("E05_SNAP_END", 6.0)
SEAM_POS_MAX_MM = _env_f("E05_SEAM_POS", 0.01)
SEAM_DIR_MAX_DEG = _env_f("E05_SEAM_DIR", 0.05)
CLIP_MAX_MM = _env_f("E05_CLIP_MAX", 0.0)
REACH_MAX_RATIO = 0.995
MATRIX_STEP_MAX_DEG = _env_f("E05_MATSTEP", 25.0)
TAIL_SETTLE_N = _env_i("E05_TAIL_N", 12)
HAND_PIERCE_MM = _env_f("E05_HAND_PIERCE", 10.0)
HAND_X_HINT_MIN_MARGIN = _env_f("E05_HINT_MARGIN", 0.55)
HITSTOP_STEP_MAX_DEG = _env_f("E05_HITSTOP_STEP", 0.01)

# 出图/像素探针共用的**逐帧集合**（主渲、反面重渲、像素探针三者必须逐帧相同）
STEM_FRAMES = sorted(set([0, 6, 12, 18, 24, 28, 32, 36, 40, 44, 46, 48, 52, 56,
                          62, 68, 74, 80, 88, 96]))

# =============================================================== 取景（★ 本支自立）
# ★ 取景跨度的由来：本支**不跳不躺**，纵向最高点 = 站架头顶 ≈ 1803 mm（耸肩时
#   肩峰升到 ≈ 1470 mm），最低点 = 鞋底 0 mm，最外 = 耸肩时肘尖（正面 x ≈ ±420 mm）。
#   ⟹ 纵向覆盖 −0.20 ~ 2.00 m（中心 z = 0.90、正交高 2.20 m）、横向足够装下 ±420 mm。
#   ★ **不照抄** E01~E04 的 (0.92 / 2.10)：本支需要**略宽一点**装下张开的手臂。
VIEW_E05_SIDE = ("side", (4.4, -0.02, 0.90), (0.0, -0.02, 0.90), 2.20,
                 (780, 1100))
VIEW_E05_FRONT = ("front", (0.0, -4.8, 0.90), (0.0, 0.0, 0.90), 2.20,
                  (780, 1100))

TRACE = _env_b("E05_TRACE")
_BLEND_TRACE = _env_b("E05_TRACE_BLEND")

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
PELVIS0 = None
MIN_HINT_MARGIN = 1.0
LAST_HAND_X = {}
# ★★★ hitstop 的**时间冻结**缓存：窗口内逐帧**复用定格帧的姿态**（同 E03 / E04）。
FREEZE = {"pose": None}


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
      站架实测值** ⟹ 接缝帧（f=0 / f=96）逐位等于站架。
    ★ `ARM_DN_DONE` 是「回 0 **完成**」帧（80），**早于** `no_snap_stop_ok` 的判定窗
      （末 13 帧 f83~96）⟹ 尾段臂**已经等于站架**，姿态静止，判据自然满足。
    """
    if frame <= ARM_UP_AT:
        return _smoothstep(frame / float(max(1, ARM_UP_AT)))
    if frame >= ARM_DN_AT:
        span = float(max(1, ARM_DN_DONE - ARM_DN_AT))
        return _smoothstep((ARM_DN_DONE - frame) / span)
    return 1.0


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
    """欧拉表示兼容化（C14 / D01 / E03 / E04 踩过的同一个万向节锁坑）。

    ★★★ 做法：**穷举等价表示 + min-max 瓶颈 DP** 求「最小化最大单轴步」的全局最优
      路径；两端**钉死在原始表示**上（E04 第 5 个实测逼出来的改动）。
    ★ 这一步**不改变任何姿态**（等价表示 ⟹ 同一旋转矩阵），只改变键上的数字。
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
        j = min(range(count), key=lambda idx: best[idx])
        seq = [j]
        for i in range(n - 1, 0, -1):
            j = back[i][j]
            seq.append(j)
        seq.reverse()
        chosen[name] = [fams[i][seq[i]] for i in range(n)]
        chosen[name][0] = fams[0][0]
        chosen[name][-1] = fams[-1][0]

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

    ★★ **本支是「全程」口径**（E04 是分段）：`want` 恒 = 站架踝 ⟹ 脚从头到尾
      钉死不动（`foot_lock_ok` ≤ 3 mm）。E04 的 `spawn_foot_lock_phased_ok`
      照抄到本支 = **错**（本支不跳）。
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
INSIDE_VOTES_MIN = _env_i("E05_INSIDE_VOTES", 7)
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


def hand_mesh_vertices(side, step=3):
    return [point for point, _name in hand_mesh_points(side, step)]


def hand_mesh_stats(side, tree=None, step=3):
    """该侧手网格 vs **躯干**的几何读数（排除拇指的口径是判据，拇指单独登记）。"""
    tree = tree if tree is not None else torso_bvh()
    pts = hand_mesh_points(side, step=step)
    inside, inside_nothumb, thumb = 0, 0, 0
    deepest, deepest_nothumb = None, None
    for point, name in pts:
        is_thumb = name.startswith("Thumb_")
        gap = signed_to_torso(point)
        if deepest is None or gap < deepest:
            deepest = gap
        if not is_thumb and (deepest_nothumb is None or gap < deepest_nothumb):
            deepest_nothumb = gap
        if inside_torso(point, tree):
            inside += 1
            if is_thumb:
                thumb += 1
            else:
                inside_nothumb += 1
    return {"inside": inside, "inside_nothumb": inside_nothumb,
            "thumb": thumb, "n": len(pts),
            "deepest_mm": round(deepest, 2) if deepest is not None else None,
            "deepest_nothumb_mm": (round(deepest_nothumb, 2)
                                   if deepest_nothumb is not None else None)}


# ---------------------------------------------------------------- ★★★ 两拳互测
def fist_clash_metrics(step=3, face_mm=40.0):
    """★★★ **本支命门**：两拳之间的「贴合 / 穿透 / 擦身 / 对称」四类读数。

    几何（**真·网格量，不是球近似**）：
      · `axis` = 由 L 拳心指向 R 拳心的单位向量（拳心 = `hand.tail` 世界坐标）；
      · `cropL` = L 手**全部网格顶点**在 +axis 方向的极大投影（= L 拳最靠内的拳面）；
        `cropR` = R 手在 −axis 方向的极大投影；
      · `gap_mm = |cR − cL| − cropL − cropR`
        ⟹ **正** = 两拳之间还有这么大空隙；**负** = 互相插进去这么深。
      · `faceL/faceR` = 各自「拳面」（`crop − face_mm` 以内的顶点）的质心；
        `perp_mm` = 两拳面质心在 ⊥axis 平面内的距离（防「一拳前一拳后擦身而过」）。
      · `sym_*_mm` = 两拳心关于中线（x=0）的镜像偏差。
    """
    pts_l = hand_mesh_vertices("L", step)
    pts_r = hand_mesh_vertices("R", step)
    c_l = Vector(A.bone_world(bpy.data.objects[A.ARM_NAME], "hand.L", "tail"))
    c_r = Vector(A.bone_world(bpy.data.objects[A.ARM_NAME], "hand.R", "tail"))
    out = {"fist_L_mm": [round(v * 1000.0, 2) for v in c_l],
           "fist_R_mm": [round(v * 1000.0, 2) for v in c_r],
           "sym_x_mm": round(abs(c_l.x + c_r.x) * 1000.0, 2),
           "sym_y_mm": round(abs(c_l.y - c_r.y) * 1000.0, 2),
           "sym_z_mm": round(abs(c_l.z - c_r.z) * 1000.0, 2),
           "point_counts": [len(pts_l), len(pts_r)]}
    delta = c_r - c_l
    if delta.length < 1e-6:
        delta = Vector((1.0, 0.0, 0.0))
    axis = delta.normalized()
    if not pts_l or not pts_r:
        out.update({"gap_mm": None, "crop_L_mm": None, "crop_R_mm": None,
                    "perp_mm": None})
        return out
    s_l = [(v - c_l).dot(axis) for v in pts_l]
    s_r = [-(v - c_r).dot(axis) for v in pts_r]
    crop_l = max(s_l)
    crop_r = max(s_r)
    center_mm = delta.length * 1000.0
    gap = center_mm - (crop_l + crop_r) * 1000.0
    thr = face_mm / 1000.0
    face_l_pts = [v for v, s in zip(pts_l, s_l) if s >= crop_l - thr]
    face_r_pts = [v for v, s in zip(pts_r, s_r) if s >= crop_r - thr]
    perp = None
    if face_l_pts and face_r_pts:
        fl = sum(face_l_pts, Vector((0.0, 0.0, 0.0))) / float(len(face_l_pts))
        fr = sum(face_r_pts, Vector((0.0, 0.0, 0.0))) / float(len(face_r_pts))
        shift = fr - fl
        perp = (shift - axis * shift.dot(axis)).length * 1000.0
    out.update({"axis": [round(v, 5) for v in axis],
                "crop_L_mm": round(crop_l * 1000.0, 2),
                "crop_R_mm": round(crop_r * 1000.0, 2),
                "center_dist_mm": round(center_mm, 2),
                "gap_mm": round(gap, 2),
                "perp_mm": None if perp is None else round(perp, 2)})
    return out


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
    basis.translation = current.translation
    pose_bone.matrix = basis
    bpy.context.view_layer.update()
    return x_axis.copy()


# =============================================================== 臂 IK
ELBOW_POLE = {"L": Vector((0.42, 1.00, -0.22)),
              "R": Vector((-0.42, 1.00, -0.22))}
LAST_ELBOW = {}


def seat_arm(arm, pose, targets, env=1.0):
    """把臂解到拳心目标上（结构照抄 E04 的**确定性**版本：肘极向量无记忆）。

    ★ 与 E04 的唯一差别：本支的拳目标在**胸前中线**，肘的自然外极向量指向体侧
      ⟹ 「外 + 后 = 肘朝身体外后方」仍然成立（不退化）。`env→0` 时三个自由度
      （肘极向量、拳轴、滚转基准）逐位收敛到站架实测值 ⟹ 接缝帧逐位等于站架。
    """
    A.apply_pose(arm, pose)
    for side in SIDES:
        up, fo, hd = ("upperarm." + side, "forearm." + side, "hand." + side)
        shoulder = Vector(A.bone_world(arm, up, "head"))
        core = Vector(targets[side])
        along = core - shoulder
        along = (along.normalized() if along.length > 1e-6
                 else Vector((0.0, 0.0, -1.0)))
        y_dir = along
        if env < 1.0:
            y_dir = _slerp_dir(STATION_HAND_Y[side], y_dir, env)
        target = core - y_dir * HAND_LEN
        delta = target - shoulder
        limit = (ARM_LEN_UP + ARM_LEN_LO) * 0.9995
        distance = max(1e-4, min(delta.length, limit))
        axis = (delta.normalized() if delta.length > 1e-9
                else Vector((0.0, 0.0, -1.0)))
        pole = Vector(ELBOW_POLE[side])
        if env < 1.0:
            pole = _slerp_dir(STATION_POLE_DIR[side], pole, env)
        bulge = pole - axis * pole.dot(axis)
        if bulge.length < 0.05:
            bulge = Vector((0.0, 1.0, 0.0)) - axis * axis.y
            if bulge.length < 0.05:
                bulge = Vector((0.0, 0.0, 1.0)) - axis * axis.z
        bulge.normalize()
        cos_sh = max(-1.0, min(1.0, (ARM_LEN_UP ** 2 + distance ** 2
                                     - ARM_LEN_LO ** 2)
                               / (2.0 * ARM_LEN_UP * distance)))
        sin_sh = math.sqrt(max(0.0, 1.0 - cos_sh * cos_sh))
        elbow = shoulder + (axis * cos_sh + bulge * sin_sh) * ARM_LEN_UP
        fore = target - elbow
        if fore.length > 1e-6:
            y_dir = fore.normalized()
            if env < 1.0:
                y_dir = _slerp_dir(STATION_HAND_Y[side], y_dir, env)
            target = core - y_dir * HAND_LEN
        LAST_ELBOW[side] = elbow.copy()
        pose[up] = A.aim_bone(arm, up, elbow - shoulder)
        pose[fo] = A.aim_bone(arm, fo, target - elbow)
        # 滚转基准 = **前臂骨自身的局部 x 轴**（母链自然框架，不累积、不退化）
        hint = arm.pose.bones["forearm." + side].matrix.to_3x3().col[0]
        hint = Vector(hint).normalized()
        LAST_HAND_X[side] = orient_hand(arm, side, y_dir, hint)
        LAST_FOREARM_TWIST[side] = 0.0
        pose[hd] = tuple(math.degrees(v)
                         for v in arm.pose.bones[hd].rotation_euler)
    return pose


# =============================================================== 拳目标
def resolve_fist(name, side):
    if NOSHOULDER and name in ("OPEN", "SHRUG"):
        name = "STATION"
    if ASYM_CLASH and name == "CLASH" and side == "L":
        base = Vector(FIST_TABLE[name][side])
        return Vector((base.x, base.y, base.z + ASYM_Z_MM / 1000.0))
    # ★★★ ② / ③ 命门反面控制：沿碰拳轴（±x）把**两拳同时**拉开 / 推近。
    #   关键细节：门禁 `/ gap = |cR − cL| − cropL − cropR` 在**碰拳帧**读；
    #   OPEN/SHRUG/WIND/STANCE 段两端姿态**完全不变**（只换 CLASH 这一个端点的
    #   世界目标）⟹ 只有 CLASH 那一段（以及其后回 STANCE 的一段）的轨迹改变，
    #   其余门禁（接缝 / 定格 / 肩膀 / 脚锁）保持绿 ⟹ 失败集合干净地只指向命门。
    if FARCLASH and name == "CLASH":
        base = Vector(FIST_TABLE[name][side])
        sign = 1.0 if side == "L" else -1.0
        return Vector((base.x + sign * FARCLASH_MM / 1000.0, base.y, base.z))
    if DEEPCLASH and name == "CLASH":
        base = Vector(FIST_TABLE[name][side])
        sign = 1.0 if side == "L" else -1.0
        return Vector((base.x - sign * DEEPCLASH_MM / 1000.0, base.y, base.z))
    if name == "STATION":
        return Vector(STATION_FIST[side])
    return Vector(FIST_TABLE[name][side])


def fist_targets(arm, frame, root_off):
    """拳目标 = **绕肩的球面插值**（方向 slerp + 半径缓动），照 E04 第 9 次迭代口径。

    ★ 为什么不用世界直线 lerp：两端方向差大时弦会贴近肩关节 ⟹ 肘被折进去再弹出
      ⟹ 前臂世界角步爆表（E04 实测 32.6°/帧）。本支 CLASH 段（WIND→CLASH）两端
      方向差大（身后 ↔ 胸前中线），同样必须走球面。
    """
    index, t, kind = _segment(frame)
    ga = _ease(kind, t)
    a_name = KEYS[index][3]
    b_name = KEYS[index + 1][3]
    out = {}
    for side in SIDES:
        shoulder = Vector(A.bone_world(arm, "upperarm." + side, "head"))
        va = resolve_fist(a_name, side) + root_off - shoulder
        vb = resolve_fist(b_name, side) + root_off - shoulder
        ra, rb = va.length, vb.length
        if ra < 1e-6:
            dirv = vb.normalized()
        elif rb < 1e-6:
            dirv = va.normalized()
        else:
            dirv = _slerp_dir(va.normalized(), vb.normalized(), ga)
        point = shoulder + dirv * (ra + (rb - ra) * ga)
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
    """臂的包络混合：**最近等价族 + 欧拉线性插值**（照 E04 第 6 个实测的结论）。"""
    out = {}
    for name in ARM_BONES:
        a = tuple(station.get(name, (0.0, 0.0, 0.0)))
        b = _nearest_family(tuple(ikpt.get(name, (0.0, 0.0, 0.0))), a)
        if _BLEND_TRACE:
            print("E05_BLEND %-12s env=%.3f span=%.1f"
                  % (name, env, max(abs(y - x) for x, y in zip(a, b))))
        out[name] = tuple(x + (y - x) * max(0.0, min(1.0, env))
                          for x, y in zip(a, b))
    return out


def battle_pose(arm, frame):  # noqa: C901
    # ---- ★★★ hitstop 的**时间冻结**：窗口内复用定格帧姿态，不再重解 ----------
    if (not NO_HITSTOP) and HOLD[0] <= frame <= HOLD[1] \
            and FREEZE["pose"] is not None:
        frozen = dict(FREEZE["pose"])
        A.apply_pose(arm, frozen)
        return frozen
    spec = torso_at(frame)
    pose = {}
    for key in ("pelvis", "spine_01", "spine_02", "chest", "neck", "head",
                "shoulder.L", "shoulder.R"):
        va = BASE.get(key, (0.0, 0.0, 0.0))
        pose[key] = tuple(va[i] + spec[key][i] for i in range(3))
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
        # ⑥ 脚滑：**脚不再锁世界，改骑在当前骨盆上**（躯干一动脚就跟着动）。
        #   ★ 忠实仿真必须让脚的目标位置**依赖当前躯干姿态**（恒定偏移在任何帧都
        #     相同 ⟹ 跨帧漂移恒 0 ⟹ 旋钮惰性，E03 v012 / E04 ⑦ 的教训）。
        A.apply_pose(arm, pose)
        delta = Vector(A.bone_world(arm, "pelvis", "head")) - PELVIS0
        scale = FOOT_SWAY_MM / 55.0
        for s in SIDES:
            want[s] = want[s] + delta * scale
    lock_err = lock_feet(arm, pose, want)

    # ---- 臂：对**当前帧的拳目标**重解，再按 `arm_env` 与站架臂混合 -------------
    env = arm_env(frame)
    A.apply_pose(arm, pose)
    ik_pose = dict(pose)
    seat_arm(arm, ik_pose, fist_targets(arm, frame, root_off), env)
    blended = _blend_local(pose, ik_pose, env)
    for name in ARM_BONES:
        pose[name] = blended[name]

    if LOOP_BREAK and frame == TOTAL:
        rx, ry, rz = pose["chest"]
        pose["chest"] = (rx + 4.0, ry, rz + 4.0)

    if (not NO_HITSTOP) and frame == HOLD[0]:
        FREEZE["pose"] = dict(pose)

    if TRACE:
        A.apply_pose(arm, pose)
        low = A.foot_lowest_by_side()
        soles = {s: round(low[s][2] * 1000.0, 1) for s in SIDES
                 if low[s] is not None}
        c_l = Vector(A.bone_world(arm, "hand.L", "tail"))
        c_r = Vector(A.bone_world(arm, "hand.R", "tail"))
        print("E05_TRACE f=%3d root_dy=%+7.1f root_dz=%+7.1f sole=%s "
              "fist_gap=%7.1f lock=%.4f env=%.3f"
              % (frame, dy * 1000.0, dz * 1000.0, soles,
                 (c_r - c_l).length * 1000.0, lock_err, env))
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
def bstart_assertions(arm, action, samples, meshes):  # noqa: C901
    res = {}
    scene = bpy.context.scene
    frames = [s["frame"] for s in samples]
    idx = {s["frame"]: i for i, s in enumerate(samples)}
    arm.animation_data.action = action
    A._bind_slot(arm, action)

    def pelvis_z_mm(frame):
        return Vector(samples[idx[frame]]["pelvis"]).z * 1000.0

    def knee_deg(frame):
        return max(abs(samples[idx[frame]]["euler"].get("shin." + s,
                                                        (0.0, 0.0, 0.0))[0])
                   for s in SIDES)

    # ---- ① ★★★ 碰拳几何（本支命门：贴合 + 互不穿透 + 对称 + 不擦身）---------
    clash_rows = {}
    for frame in sorted(set([WIND, CLASH, HOLD[0], HOLD[1], STANCE])):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        clash_rows[str(frame)] = fist_clash_metrics(step=3)
    res["bstart_clash_geometry"] = clash_rows
    row = clash_rows[str(CLASH)]
    hold_rows = [clash_rows[str(f)] for f in (HOLD[0], HOLD[1])]
    gap = row["gap_mm"]
    gaps = [g for g in ([gap] + [r["gap_mm"] for r in hold_rows])
            if g is not None]
    worst_gap = max(gaps) if gaps else None
    best_gap = min(gaps) if gaps else None
    res["bstart_clash_gap_mm"] = gap
    res["bstart_clash_gap_max_mm"] = worst_gap
    res["bstart_clash_gap_min_mm"] = best_gap
    res["bstart_clash_contact_max_mm"] = CLASH_CONTACT_MAX_MM
    res["bstart_fist_contact_ok"] = bool(
        gap is not None and gap <= CLASH_CONTACT_MAX_MM and gap >= 0.0
        or (best_gap is not None and best_gap <= CLASH_CONTACT_MAX_MM))
    res["bstart_clash_pierce_tol_mm"] = CLASH_PIERCE_TOL_MM
    res["bstart_fist_no_pierce_ok"] = bool(
        best_gap is not None and best_gap >= -CLASH_PIERCE_TOL_MM)
    res["bstart_fist_contact_note"] = (
        "★★★ **本支命门**：「碰拳」= 全项目第一支「手与手」自接触。判据是**真·网格量**："
        "`gap = |cR − cL| − cropL − cropR`（`crop` = 各自网格沿碰拳轴的**最内侧拳面**"
        "投影）。碰拳帧 f=%d 实测 **gap = %.2f mm**（≤ %.1f mm 判「碰上了」；"
        "≥ 0 判「没插进去」），定格窗 f=%s 内 gap ∈ [%.2f, %.2f]。"
        "★ 与 E03 `rage_chest_hit_ok`（拳 vs **躯干**）不同：本支是「拳 vs 拳」，"
        "**不能**用 `no_face_clip_ok` 代替（它盯的是「手不穿脸 / 胸」）。"
        "★ 差分口径不适用（两拳都是同一套手网格，不存在「上游站架自带的缺陷」）。"
        % (CLASH, gap if gap is None else gap, CLASH_CONTACT_MAX_MM,
           list(HOLD), best_gap, worst_gap))
    res["bstart_fist_sym_x_mm"] = row["sym_x_mm"]
    res["bstart_fist_sym_y_mm"] = row["sym_y_mm"]
    res["bstart_fist_sym_z_mm"] = row["sym_z_mm"]
    res["bstart_fist_sym_limits_mm"] = [SYM_X_MM, SYM_Y_MM, SYM_Z_MM]
    res["bstart_fist_sym_ok"] = bool(
        row["sym_x_mm"] <= SYM_X_MM and row["sym_y_mm"] <= SYM_Y_MM
        and row["sym_z_mm"] <= SYM_Z_MM)
    res["bstart_clash_perp_mm"] = row["perp_mm"]
    res["bstart_clash_perp_max_mm"] = CLASH_PERP_MAX_MM
    res["bstart_fist_perp_ok"] = bool(row["perp_mm"] is not None
                                      and row["perp_mm"] <= CLASH_PERP_MAX_MM)
    res["bstart_fist_sym_note"] = (
        "★ **碰拳的对称性**（照 E04 `px_spawn_feet_sym_ok` 模式**改成手**）："
        "「碰拳」两拳应当在**中线相遇** ⟹ 一拳高一拳低 / 一前一后会被读成"
        "「一只手够不着」。碰拳帧实测拳心镜像偏差 x **%.2f** / y **%.2f** / z **%.2f** mm"
        "（≤ %.0f / %.0f / %.0f）；两拳**拳面质心**在 ⊥ 轴平面内的距离 **%s** mm"
        "（≤ %.0f，防「一拳前一拳后擦身而过」）。"
        % (row["sym_x_mm"], row["sym_y_mm"], row["sym_z_mm"], SYM_X_MM, SYM_Y_MM,
           SYM_Z_MM, row["perp_mm"], CLASH_PERP_MAX_MM))

    # ---- ② ★★★ 碰拳定格（hitstop）在碰拳窗口内 ---------------------------
    steps = []
    for frame in range(HOLD[0], HOLD[1]):
        step, at = _worst_step(samples, idx[frame], idx[frame + 1])
        steps.append((frame, round(step, 6), at))
    worst_hs = max((s for _f, s, _a in steps), default=0.0)
    res["bstart_hitstop_frames"] = HITSTOP_N
    res["bstart_hitstop_window"] = list(HOLD)
    res["bstart_hitstop_steps_deg"] = [
        {"from": f, "step_deg": s, "at": at} for f, s, at in steps]
    res["bstart_hitstop_worst_step_deg"] = round(worst_hs, 6)
    res["bstart_clash_hitstop_ok"] = bool(
        2 <= HITSTOP_N <= 4 and worst_hs <= HITSTOP_STEP_MAX_DEG
        and HOLD[1] - HOLD[0] + 1 == HITSTOP_N)
    res["bstart_hitstop_note"] = (
        "★★★ 「打击停顿」在碰拳帧：判据量**定格窗口内逐帧姿态**（`max |Δ euler|`），"
        "窗口 **f=%s** 共 %d 帧，实测窗口内最大逐帧角步 **%.6f°**（阈值 ≤ %.2f° ⟹ "
        "姿态完全冻结）。★ 定格靠**时间轴冻结**（帧号前进、姿态不变 + `A.set_hitstop` "
        "把窗口键设 CONSTANT），**不是**把 N 帧压进插值 —— 否则 `no_snap_stop_ok` "
        "会在定格边界炸（E03 / E04 同一坑）。★ 与 E03 的区别：E03 是**两个对称窗口**"
        "（两次捶胸），本支是**碰拳单窗口**。"
        % ([f for f, _s, _a in steps], HITSTOP_N, worst_hs, HITSTOP_STEP_MAX_DEG))

    # ---- ③ ★★★ 活动肩膀（本支最容易失败处：幅度必须可量、看得见）---------
    sho_travel = {}
    for name in ("shoulder.L", "shoulder.R"):
        axis_travel = [0.0, 0.0, 0.0]
        for s in samples:
            if s["frame"] > WIND:
                continue
            e = s["euler"].get(name, (0.0, 0.0, 0.0))
            for k in range(3):
                axis_travel[k] = max(axis_travel[k], abs(e[k]))
        sho_travel[name] = [round(v, 3) for v in axis_travel]
    #   注意：`euler` 记录的是**局部**角度（含站架基线）⟹ 这里改用**全窗行程**
    #   （max − min）才与「活动幅度」对齐（差一点都会把静止的 −18° 基线读成行程）。
    sho_span = {}
    for name in ("shoulder.L", "shoulder.R"):
        vals = [[], [], []]
        for s in samples:
            if s["frame"] > WIND:
                continue
            e = s["euler"].get(name, (0.0, 0.0, 0.0))
            for k in range(3):
                vals[k].append(e[k])
        sho_span[name] = [round(max(v) - min(v), 3) for v in vals]
    worst_span = max(max(v) for v in sho_span.values())
    res["bstart_shoulder_span_deg"] = sho_span
    res["bstart_shoulder_absmax_deg"] = sho_travel
    res["bstart_shoulder_window"] = [START, WIND]
    res["bstart_shoulder_range"] = list(SHOULDER_TRAVEL_RANGE)
    # 肩峰（upperarm.head）世界行程 —— 肩骨旋转 + 躯干驱动的**可见**位移
    peak_travel = {}
    for side in SIDES:
        pts = [Vector(s["upperarm." + side]) for s in samples
               if s["frame"] <= WIND]
        peak_travel[side] = round(
            max((p - pts[0]).length for p in pts) * 1000.0, 3)
    worst_peak = max(peak_travel.values())
    res["bstart_shoulder_peak_travel_mm"] = peak_travel
    res["bstart_shoulder_peak_range"] = list(SHOULDER_TAIL_RANGE)
    res["bstart_shoulder_ok"] = bool(
        SHOULDER_TRAVEL_RANGE[0] <= worst_span <= SHOULDER_TRAVEL_RANGE[1]
        and SHOULDER_TAIL_RANGE[0] <= worst_peak <= SHOULDER_TAIL_RANGE[1])
    res["bstart_shoulder_note"] = (
        "★★★ **本支最容易失败的地方**（清单 §1 风险 3：「活动肩膀」极容易读成"
        "「什么也没做」）。实测肩骨**全窗行程**（f=%s，取 rx/ry/rz 各轴 max−min）"
        "L=%s / R=%s 度（区间 %.0f~%.0f，**两端卡**：太小 = 站着没动、太大 = 耸肩变形）"
        "＋ **肩峰**（`upperarm.head`）世界行程 L=%.1f / R=%.1f mm（区间 %.0f~%.0f）。"
        "★ 载体说明：肩骨旋转本身**看不见**（被大臂遮挡），可见量是**肩峰抬起**；"
        "两条一起量，缺一不可。"
        % ([START, WIND], sho_span["shoulder.L"], sho_span["shoulder.R"],
           SHOULDER_TRAVEL_RANGE[0], SHOULDER_TRAVEL_RANGE[1],
           peak_travel["L"], peak_travel["R"], SHOULDER_TAIL_RANGE[0],
           SHOULDER_TAIL_RANGE[1]))

    # ---- ④ ★★ 碰拳发力：躯干下沉 + 膝屈（两端卡）-------------------------
    p0 = pelvis_z_mm(START)
    sink = p0 - pelvis_z_mm(CLASH)
    res["bstart_body_sink_mm"] = round(sink, 3)
    res["bstart_body_knee_deg"] = round(knee_deg(CLASH), 2)
    res["bstart_body_sink_range"] = list(BODY_SINK_RANGE)
    res["bstart_body_sink_ok"] = bool(
        BODY_SINK_RANGE[0] <= sink <= BODY_SINK_RANGE[1]
        and res["bstart_body_knee_deg"] >= BODY_KNEE_MIN)
    res["bstart_body_sink_note"] = (
        "★★ 「碰拳」的**力度**必须可量：躯干**净下沉**（站架骨盆 z %.1f → 碰拳 "
        "%.1f mm）。实测 **%.1f mm**（区间 %.0f~%.0f，**两端卡**：太小 = 只动手不动身"
        "（力量链断）；太大 = 蹲成马步不像开战）+ 碰拳膝屈 **%.1f°**（≥ %.0f°）。"
        "★ 无根位移（原地），下沉由**屈膝**吸收（与 E04 落地同一套腿 IK 口径）。"
        % (p0, pelvis_z_mm(CLASH), sink, BODY_SINK_RANGE[0], BODY_SINK_RANGE[1],
           res["bstart_body_knee_deg"], BODY_KNEE_MIN))

    # ---- ⑤ ★★ 脚锁（**全程**）+ 鞋底带宽 ---------------------------------
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
    res["bstart_ankle_drift_mm"] = {k: round(v, 4) for k, v in drift.items()}
    res["bstart_toe_drift_mm"] = {k: round(v, 4)
                                 for k, v in toe_drift.items()}
    res["bstart_sole_min_mm"] = round(min(sole.values()), 3)
    res["bstart_sole_max_mm"] = round(max(sole.values()), 3)
    res["foot_lock_ok"] = bool(
        max(max(drift.values()), max(toe_drift.values())) <= FOOT_LOCK_MM
        and SOLE_BAND[0] <= min(sole.values())
        and max(sole.values()) <= SOLE_BAND[1])
    res["foot_lock_note"] = (
        "★★★ **脚锁回到「全程」口径**（本支最大的口径回归，见 §1 风险 1）：本支"
        "**不跳、不位移**，双腿全程落地 ⟹ `want` 恒 = 站架踝。实测踝漂 "
        "**L %.4f / R %.4f mm**、趾漂 **L %.4f / R %.4f mm**（阈值 %.1f mm），"
        "鞋底 **%.2f ~ %.2f mm**（带 %.0f ~ %.0f）。★ 照抄 E04 的**分段**口径 = 错"
        "（E04 空中段脚**真的离地**；本支若把哪一帧判成「空中」，那是判据错了）。"
        % (drift["L"], drift["R"], toe_drift["L"], toe_drift["R"], FOOT_LOCK_MM,
           res["bstart_sole_min_mm"], res["bstart_sole_max_mm"], SOLE_BAND[0],
           SOLE_BAND[1]))

    # ---- ⑥ 收招 / 过缝 ---------------------------------------------------
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
    res["loop_velocity_ok"] = None
    res["loop_velocity_note"] = (
        "★ **停用 `loop_velocity_ok` 并登记理由**：该判据（首/末帧角速度必须相等）"
        "是 E02 为**循环**动画加的对称性检查。本支 `meta.loop = false`（**一次性**"
        "「开战」：站架 → 活动肩膀 → 碰拳 → 摆架势 → 回站架），首末帧同姿只用于"
        "「起手不留痕」，**不要求角速度对称**。实测首帧步 %.3f° / 末帧步 %.3f°"
        "（末帧更慢是**设计意图**：收招减速）。★ 设一个必然为假的判据等于没有判据。"
        % (first_step, last_step))

    # ---- ⑦ 力量传导链（六段：脚 → 腿 → 髋 → 腰 → 肩 → 手）----------------
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
    waist_deg = (max(waist) - min(waist)) * 180.0 / math.pi
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
        "（清单 0.2「不许跳级」）。本支载体：脚 = 髋↔踝距离行程（下沉靠屈膝）"
        "＋ 踝**全程钉死**（漂移 ≤ %.1f mm）；腿 = 膝屈角行程；髋 = 骨盆世界行程；"
        "腰 = `chest` 俯仰行程；肩 = 肩峰世界行程；手 = 拳心世界行程。"
        "★ 本支**没有「只有手在动」**：碰拳帧的躯干下沉 %.1f mm 把脚→腿→髋→腰"
        "全部串上（见 `bstart_body_sink_ok`）。"
        % (FOOT_LOCK_MM, res["bstart_body_sink_mm"]))
    res["chain_present_ok"] = bool(
        foot_axis > 20.0 and knee_deg_span > 0.2 and hip_travel > 2.0
        and waist_deg > 2.0 and shoulder_mm > 1.0 and hand_mm > 20.0)

    # ---- ⑧ 可达性 --------------------------------------------------------
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

    # ---- ⑨ 穿模（臂 vs 头盒，D01 起老口径）-------------------------------
    worst_clip, clip_at = 0.0, None
    for frame in sorted(set(list(range(START, END + 1, 3))
                            + [CLASH, HOLD[1], SHRUG, WIND, STANCE])):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        clip = PD.clip_metrics(arm)
        if clip["clip_max_mm"] > worst_clip:
            worst_clip, clip_at = clip["clip_max_mm"], (frame, clip["clip_at"])
    res["clip_max_mm"] = round(worst_clip, 2)
    res["clip_at"] = clip_at
    res["no_face_clip_ok"] = bool(worst_clip <= CLIP_MAX_MM)

    # ---- ⑩ ★★ 手 vs 躯干：**差分口径**（站架自己就有缺陷）-----------------
    pierce = {}
    walk = sorted(set(list(range(START, END + 1, 3))
                      + list(range(HOLD[0], HOLD[1] + 1))))
    seam_frames = {START, END}
    worst_nt, worst_nt_at = 0, None
    worst_deep, worst_deep_at = 0.0, None
    worst_all, worst_thumb = 0, 0
    for frame in walk:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        torso_bvh_reset()
        tree = torso_bvh()
        row = {}
        for side in SIDES:
            counts = hand_mesh_stats(side, tree=tree, step=4)
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
        pierce[str(frame)] = row
    station_nt = max(STATION_PIERCE[s]["inside_nothumb"] for s in SIDES)
    res["bstart_pierce_scope"] = ["(0, TOTAL) 内全部帧",
                                  "排除接缝帧 %s" % sorted(seam_frames)]
    res["bstart_pierce_nothumb_worst"] = worst_nt
    res["bstart_pierce_nothumb_worst_at"] = worst_nt_at
    res["bstart_pierce_nothumb_deepest_mm"] = round(worst_deep, 2)
    res["bstart_pierce_nothumb_deepest_at"] = worst_deep_at
    res["bstart_pierce_all_worst"] = worst_all
    res["bstart_pierce_thumb_worst"] = worst_thumb
    res["bstart_station_nothumb_count"] = station_nt
    res["bstart_station_pierce"] = {s: dict(STATION_PIERCE[s]) for s in SIDES}
    res["bstart_pierce_detail"] = pierce
    res["bstart_hand_no_pierce_ok"] = bool(
        worst_deep >= -HAND_PIERCE_MM and worst_nt <= station_nt)
    res["bstart_hand_no_pierce_note"] = (
        "★ 本支的拳要**收到胸前中线**（碰拳）—— 比 E04 的腾空摆臂**更贴近躯干**"
        "⟹ 这条断言在本支**真的有风险**，不是走过场。口径照 E03 v011 的**差分**形式"
        "（**改的是基准，不是阈值**）：实测非拇指「真在体内」顶点数 **%d**（@ %s）、"
        "非拇指最深带符号距离 **%.2f mm**（@ %s，下限 −%.0f mm）；站架基线同一读数 "
        "**%d** 个（`Idle_01@0` 的预存缺陷：R 手 4 个 `Hand_Palm_R` 腕侧掌肉 / 最深 "
        "−4.50 mm ＋ R 拇指 95 个 / −34.19 mm，本支 f=0 / f=%d 必须逐位等于它 "
        "⟹ 口径只能是差分）。★ 全手（含拇指）读数照样登记：体内最多 **%d** 个"
        "（其中拇指 **%d**）。"
        % (worst_nt, worst_nt_at, worst_deep, worst_deep_at, HAND_PIERCE_MM,
           station_nt, END, worst_all, worst_thumb))

    # ---- ⑪ ★★ 真旋转步长（矩阵口径）—— 与 euler 口径互为交叉验证 ----------
    prev_basis = None
    worst_mat, worst_mat_at = 0.0, None
    for frame in range(START, END + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        current = {name: arm.pose.bones[name].matrix.to_3x3().copy()
                   for name in BONE_LIST if name in arm.pose.bones}
        if prev_basis is not None:
            for name in set(current) & set(prev_basis):
                a, b = prev_basis[name], current[name]
                for column in range(3):
                    va = a.col[column].normalized()
                    vb = b.col[column].normalized()
                    deg = math.degrees(math.acos(max(-1.0, min(1.0,
                                                             va.dot(vb)))))
                    if deg > worst_mat:
                        worst_mat, worst_mat_at = deg, (frame, name)
        prev_basis = current
    res["bstart_matrix_step_deg_max"] = round(worst_mat, 3)
    res["bstart_matrix_step_at"] = worst_mat_at
    res["bstart_matrix_step_ok"] = bool(worst_mat <= MATRIX_STEP_MAX_DEG)
    euler_step, euler_at = 0.0, None
    for index in range(1, len(samples)):
        step, at = _worst_step(samples, index - 1, index)
        if step > euler_step:
            euler_step, euler_at = step, at
    res["bstart_euler_step_deg_max"] = round(euler_step, 3)
    res["bstart_euler_step_at"] = euler_at
    res["bstart_matrix_step_note"] = (
        "★★ **矩阵口径**的逐帧最大真实旋转步 **%.3f° @ %s**（阈值 ≤ %.1f°）；"
        "euler 口径 **%.3f° @ %s**。两者**必须一致地小** —— 差得远就说明欧拉表示"
        "在跳（C14 / D01 / E03 的万向节锁坑），而不是动作在跳。"
        "★ 本支先做 `compat_euler`（min-max 瓶颈 DP）再断言。"
        "★ 风险 4（§1）：`WIND→CLASH`（收拳 → 碰拳）是加速度最大的一段，"
        "本条是它唯一的守卫（E03 实测 24.081°、E04 实测 24.656°，都在上限附近）。"
        % (worst_mat, worst_mat_at, MATRIX_STEP_MAX_DEG, euler_step, euler_at))

    # ---- ⑫ 手骨滚转基准的退化余量（E03 v009 的教训）---------------------
    res["bstart_x_hint_margin"] = round(MIN_HINT_MARGIN, 4)
    res["bstart_x_hint_margin_min"] = HAND_X_HINT_MIN_MARGIN
    res["bstart_x_hint_margin_ok"] = bool(MIN_HINT_MARGIN
                                          >= HAND_X_HINT_MIN_MARGIN)
    res["bstart_x_hint_margin_note"] = (
        "★ `orient_hand` 的滚转基准（**前臂骨自身的局部 x 轴**）实测最小余量 "
        "**%.4f**（阈值 ≥ %.2f）。E03 v009 的实测教训：基准若落在骨轴方向上，"
        "投影退化为 0 ⟹ 滚转由浮点噪声决定 ⟹ **真实旋转 83.86°/帧**（不是表示问题，"
        "是真翻）。★ 本支与 E04 同族（基准 = 前臂局部 x），余量恒 ≈ 1，"
        "且**不累积**（当前姿态的纯函数）。"
        % (MIN_HINT_MARGIN, HAND_X_HINT_MIN_MARGIN))

    res["phase_markers"] = {
        "START": START, "OPEN": OPEN_AT, "SHOULDER": SHRUG, "WIND": WIND,
        "CLASH": CLASH, "HOLD_END": HOLD[1], "STANCE": STANCE,
        "SETTLE": SETTLE, "END": END}
    res["bstart_sole_trace_mm"] = {str(f): round(v, 2)
                                   for f, v in sorted(sole.items())}
    return res


# =============================================================== 屏幕投影
def landmark_screen(arm, action):
    """把「拳心 / 拳面 crop / 肩峰」逐帧投影到**正面**屏幕坐标，供像素探针用。"""
    name, loc, tgt, scale, rres = VIEW_E05_FRONT
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
    return {"view": VIEW_E05_FRONT[0], "res": list(VIEW_E05_FRONT[4]),
            "ortho_m": VIEW_E05_FRONT[3], "cam_z": VIEW_E05_FRONT[1][2],
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
    global LAST_FOREARM_TWIST, PELVIS0, MIN_HINT_MARGIN, LAST_HAND_X
    LAST_ELBOW = {}
    LAST_HAND_X = {}
    FREEZE["pose"] = None
    LAST_FOREARM_TWIST = {}
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
    for side in SIDES:
        STATION_PIERCE[side] = hand_mesh_stats(side, step=4)
    return arm, meshes


def main():  # noqa: C901
    arm, meshes = boot()
    keyframes = [(frame, battle_pose(arm, frame))
                 for frame in range(START, END + 1)]
    keyframes = compat_euler(keyframes)
    keyframes = seam_canonicalize(keyframes)
    meta = {
        "anim_id": NAME,
        "loop": False,
        "category": "状态与流程",
        "note": ("开战：活动肩膀（肩绕环）→ 收拳蓄势 → 双拳在胸前中线**相击**"
                 "（定格 %d 帧）→ 展开摆出战斗架势 → 回战斗待机；"
                 "★ 全程原地、脚锁全程" % HITSTOP_N),
        "frames": [START, END],
        "root_motion_m": [0.0, 0.0],
        "root_motion_z_m": [0.0, 0.0],
        "hitstop_frames": HITSTOP_N,
        "hitstop_windows": [list(HOLD)],
        "antic_frame": WIND,
        "hit_frame": CLASH,
        "hit_frames": [CLASH],
        "cancel_frame": STANCE,
        "hit_point_m": [0.0, CLASH_Y_M, CLASH_Z_M],
        "seam": "%s@%d" % (SEAM_ACTION, SEAM_FRAME),
        "seam_ends": {"start": "%s@%d" % (SEAM_ACTION, SEAM_FRAME),
                      "end": "%s@%d" % (SEAM_ACTION, SEAM_FRAME)},
        "frame_bound_note": ("★ 96 帧 = 1.6 s，**小于** E01 登记的 120 帧 / 2.0 s "
                             "上界 ⟹ 可直接沿用（显式声明，不是悄悄超）"),
        "view_note": ("★ 本支取景**自立**（不照抄 E01~E04）：纵向覆盖 −0.20~2.00 m"
                      "（中心 z=0.90、正交高 2.20 m），比标准站姿视图**略宽**"
                      "以装下耸肩时张开的手臂；正面判碰拳贴合 + 对称，"
                      "侧视 / 3Q 判肩部活动"),
        "foot_lock": {
            "scope": "全程 [START..END]（本支不跳、不位移）",
            "reason": "原地动画 ⟹ 踝恒钉站架点（与 E04 的**分段**口径相反）"},
        "clash_pair": {
            "kind": "hand.geometry vs hand.geometry（全项目首支「手与手」自接触）",
            "axis": "L 拳心 → R 拳心",
            "contact_max_mm": CLASH_CONTACT_MAX_MM,
            "pierce_tol_mm": CLASH_PIERCE_TOL_MM,
            "hit_point_m": [0.0, CLASH_Y_M, CLASH_Z_M]},
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.add_markers(action, {
        "START": START, "OPEN": OPEN_AT, "SHOULDER": SHRUG, "ANTIC": WIND,
        "CLASH": CLASH, "HIT": CLASH, "STANCE": STANCE, "RECOV": SETTLE,
        "END": END})
    if not NO_HITSTOP:
        A.set_hitstop(action, HOLD[0], HOLD[1])

    samples = A.sample_animation(arm, action, START, END, meshes)
    report = A.run_common_assertions(samples, meta, foot_probe=(),
                                     slide_tolerance_mm=FOOT_LOCK_MM)
    report.update(bstart_assertions(arm, action, samples, meshes))

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
    A.report("E05_REPORT", report)

    stem_only = os.environ.get("E05_STEM_ONLY") == "1"
    stem_frames = list(STEM_FRAMES)
    if stem_only:
        # ★ 只为像素探针的**反面对照**重渲：**同一台相机 + 同一批帧 + 两个机位**。
        #   ★ 侧视可见 Y/Z（耸肩、下沉、脚沿 Y 滑），正面可见 X（碰拳贴合 / 对称）
        #     ⟹ 两个机位**各管一维**，反面旋钮必须选在**本机位可见**的那一维上。
        #   ★ 不 save_project / export_glb ⟹ 不污染正式 .blend / GLB。
        stem = os.environ.get("E05_STEM", "bstartfar")
        A.render_pose_sheet(arm, action, stem_frames, stem,
                            views=(VIEW_E05_SIDE, VIEW_E05_FRONT))
        render_layer(arm, action, stem + "hand", HAND_PREFIX, VIEW_E05_FRONT,
                     stem_frames)
        print("E05_DONE failed=%s non_ok=%s" % (failed, non_ok))
        return

    if not SKIP_RENDER:
        A.render_pose_sheet(arm, action, list(range(START, END + 1, 4)),
                            "bstartwide", views=(VIEW_E05_SIDE,))
        A.render_pose_sheet(arm, action, stem_frames, "bstart_side",
                            views=(VIEW_E05_SIDE,))
        A.render_pose_sheet(arm, action, stem_frames, "bstart_front",
                            views=(VIEW_E05_FRONT,))
        # ★★ 手部**分层**渲染必须用**另一个前缀**：`render_pose_sheet` 的文件名是
        #   `<prefix>_<view>_f<NNNN>.png` ⟹ 若分层也用 `bstart_front` 会把上面那份
        #   **全身正面图原地覆盖**（E05 首轮实测踩到：全身正面图凭空消失）。
        #   E04 的 main 只调 `render_pose_sheet`、没有分层，所以没暴露这个坑。
        render_layer(arm, action, "bstart_hand", HAND_PREFIX,
                     VIEW_E05_FRONT, stem_frames)
        key_frames = [0, 12, 24, 30, 32, 38, 44, 46, 48, 54, 62, 70, 80, 88,
                      96]
        A.render_pose_sheet(arm, action, key_frames, "bstartkey",
                            views=(VIEW_E05_SIDE, VIEW_E05_FRONT, A.VIEW_3Q))
        with open(os.path.join(A.PREVIEW_DIR, "_e05_landmark.json"), "w",
                  encoding="utf-8") as handle:
            json.dump(landmark_screen(arm, action), handle, ensure_ascii=False)
        A.save_project()
        A.export_glb(arm)
    print("E05_DONE failed=%s non_ok=%s" % (failed, non_ok))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("E05_FAILURE " + traceback.format_exc())
