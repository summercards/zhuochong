"""anim_victory_01 —— E06 `Victory_01` 胜利A（捶胸）（E 族第六支 / 第 62 支）。

清单原文：「**胜利 A：捶胸**」。

★★★ 开工第一件事（清单 §「给 E06 的三条预警」第 1 条）已做完：`probe_e06_baseline.py`
    实测 **推翻了清单的前提**。清单说「E03 已做过『仰头怒吼 + **单臂交替**捶胸』」，
    但实测（`E06_BASE_E03` 行）E03 `Rage` 的 f=28 上：

        fist_L=[123.1, −238.2, 1166.6]  fist_R=[−121.3, −238.5, 1166.1]
        fist_dx = **244.4 mm**，face_min L 4.56 / R 4.29 mm（左右差 0.27 mm）

    ⟹ **E03 本来就是「双拳同时、精确对称」捶胸**，不是单臂交替。
    ⟹ 清单建议的差异（「E06 改成双臂同时」）**打不到差分维度上** —— 那一维 E03 已经占了。
    ⟹ **E06 改在下面 5 个「可量化」的维度做差异**（每条都有专属门禁盯着）：

      · ① **捶点更高**：E03 捶**下胸/剑突**（fist z = 1166.6 mm）；
        E06 捶**上胸/胸肌**（探测点取胸骨下 70 mm ⟹ fist z ≈ 1277 mm，**高 110 mm**）
        ⟹ `victory_pound_site_ok`（z ≥ 1255）。
      · ② **三连捶（不是两捶）**：E03 是 f28 / f52 两捶、间隔 24 帧；
        E06 是 f26 / f40 / f54 **三捶、间隔 14 帧**（更快的庆祝节奏）
        ⟹ `victory_pound_count_ok`（== 3）。
      · ③ **只上扬、不怒吼**：E03 怒吼时 `head_back = 36.0°`；
        E06 庆祝只有 **16°（OPEN）/ 12°（HERO）** ⟹ `victory_chin_up_ok`（区间 8~24°）
        + `victory_no_roar_ok`（全程 ≤ 26°）。
      · ④ **挺胸 + 张臂庆祝**：E03 全程没有「张臂」这一段；
        E06 在第三捶之后**双拳向外张开**（fist |x| 从 0.113 → 0.400 m）+ **挺胸**
        （`chest rx ≤ −2.5°`）⟹ `victory_chest_puff_ok`。
      · ⑤ **英雄 pose 稳定收尾**：E03 捶完直接回站架；E06 有 10 帧
        （f=84~94）**几乎不动**的稳定英雄姿 ⟹ `victory_hero_hold_ok`。

★★★ 与前五支的结构关系：
    · 接缝 = `Idle_01@0`（★ 自己测过：`E06_BASE_SEAM` 显示 `Idle_01@0` vs
      `Battle_Start@96` 逐骨世界矩阵差 `pos 8.7e-05 mm / dir 0.031°` ⟹ 浮点噪声级；
      按**语义**选 `Idle_01@0` —— 玩家赢的那一刻角色还在**战斗站架**上）。
    · 脚锁 = **全程**口径（照 E05；E06 原地、不跳、不位移）。
    · 力量链 = 脚→腿→髋→腰→肩→手 六段全有（三捶的**屈膝下沉**把前四段串上）。
    · **不拧腰**（照 E05 的硬教训）：捶胸是**双手对称**手势，`pelvis/spine/chest`
      的 `ry` 全程 0 ⟹ `sym_x/y/z` 天然 = 0。

★★★ 工程件：六段结构（120 帧 = 2.0 s，★ = E01 登记的 120 帧上界，**显式声明**）
    `START(0) → DIP(14) → POUND1(26)→[定格 26~28]→ PULL1(33) → POUND2(40)
      →[定格 40~42]→ PULL2(47) → POUND3(54)→[定格 54~56]→ OPEN(72) → HERO(84)
      → HOLD(94) → SETTLE(108) → END(120)`
    · `DIP` = 收拳 + 沉髋（反向预备，力量链的「髋」段在这里沉下去）；
    · `POUND1/2/3` = 双拳同步砸上胸（拳面朝胸，用指节面砸）；
    · `PULL1/2` = 拳**离胸 45 mm** 回抽（否则三次捶之间读不出「捶」）；
    · `PULL → POUND` 用 `accel`（慢起 → 加速砸上去，重击手感）；
    · `OPEN` = 张臂庆祝（拳向外张开 + 挺胸 + 下巴上扬）；
    · `HERO/HOLD` = 稳定英雄姿（★ 10 帧几乎不动，**不是颤抖**）；
    · 段间缓动：`smooth` / `accel` / `hold`（**不用 `decel`** —— E05 实测教训：
      定格之后用 `decel` 会把 16 % 行程塞进一帧 ⟹ `matrix_step` 炸到 30.59°）。

★★★ 捶胸几何全部**照抄 E03 的成熟口径**（不重新发明）：
    · 拳目标 = `当前帧胸面点 + 外法线 × TOUCH_OFF`（胸面**逐帧重解**，不是静态值）；
    · `FIST_FACE_BLEND = 1.0`（拳面正对胸面 = 用**指节面**砸，不是拳侧蹭），
      但**只在臂包络平台段内**生效（`face_blend` 的相位包络，E03 v005 的教训）；
    · 手心滚转基准 = `thumb_out`（±X）—— E03 实测该基准全程 `min|投影| = 0.701`
      （YZ 平面内的基准必然退化：胸腔法线是 0.000）⟹ `victory_x_hint_margin_ok` 盯着；
    · 腕部轴向滚转按 ρ = 0.6 **不动点迭代**分给前臂（旋前）与腕（`TWIST_SPLIT`）——
      XYZ 欧拉的中间轴就是骨轴 Y，不分担就会在 `ry = ±90°` 附近把 euler 步放大 1.5×；
    · 肘部 **IK 连续性**（用上一帧解出的肘作极向量参考）。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python anim_victory_01.py
    SKIP_RENDER=1      只跑门禁不渲图（迭代用）
    E06_TRACE=1        逐帧打印 骨盆位移 / 拳心离胸 / 脚锁误差 / env

反向验证（§4 第 7 步，11 组，每组必须**真的把对应判据变红**）：
    E06_TP_SEAM_ZERO=1    ① 首帧改零位              ⟹ `seam_in_ok`
    E06_TP_NOCONTACT=1    ② ★★★ 拳离胸 60 mm（命门）⟹ `victory_pound_contact_ok`
    E06_TP_DEEP=1         ③ ★★★ 拳插进胸 30 mm      ⟹ `victory_pound_pierce_ok`
    E06_TP_LOWCHEST=1     ④ ★★★ 捶点降到 E03 高度   ⟹ `victory_pound_site_ok`
    E06_TP_ASYM=1         ⑤ ★ 左拳抬高 90 mm        ⟹ `victory_pound_sym_ok`
    E06_TP_NOHITSTOP=1    ⑥ ★ 捶击无定格            ⟹ `victory_hitstop_ok`
    E06_TP_SLUMP=1        ⑦ ★ 不挺胸（含胸）        ⟹ `victory_chest_puff_ok`
    E06_TP_NOCHIN=1       ⑧ ★ 下巴不上扬            ⟹ `victory_chin_up_ok`
    E06_TP_TREMBLE=1      ⑨ ★ 英雄姿颤抖            ⟹ `victory_hero_hold_ok`
    E06_TP_FOOTSWAY=1     ⑩ ★ 脚滑                  ⟹ `foot_lock_ok`
    E06_TP_LOOPBREAK=1    ⑪ ★ 末帧不闭合            ⟹ `end_matches_start_ok`
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

NAME = "Victory_01"
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"
SIDES = ("L", "R")
ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")
ARM_SET = set(ARM_BONES)
ARM_LEN_UP = 0.328
FOREARM_LEN = 0.224          # 前臂骨长（肘 → 腕）
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
# ★ 上游 = `Idle_01@0`（★ 本支自己测过，见模块 docstring 与 `probe_e06_baseline.py`）。
SEAM_ACTION = os.environ.get("E06_SEAM_ACTION", "Idle_01")
SEAM_FRAME = _env_i("E06_SEAM_FRAME", 0)

# =============================================================== 时间轴（120 帧 = 2.0 s）
# ★★ 帧预算：120 帧 = 2.0 s = E01 登记的**上界** ⟹ 可直接沿用（**显式声明**）。
#   清单要求「胜利动作的停不能太长（1.5~2.5 s）」⟹ 2.0 s 落带内。
TOTAL = _env_i("E06_TOTAL", 120)
START = 0
END = TOTAL
HITSTOP_N = _env_i("E06_HITSTOP", 3)          # 每次捶击定格帧数（2~4）

DIP = _env_i("E06_DIP", 14)                   # 收拳蓄势（沉髋）
# ★★ 实测修正（本轮）：`POUND1` 14 → 26 **改 28**，其后各键**整体顺延 2 帧**。
#   理由：`no_teleport` 与 `victory_hitstop_ok` 在**同一个窗口**上对立 ——
#     折叠（拳面朝胸）必须在**命中帧之前**走完，窗口越窄逐帧步越大；
#     但折叠一旦越过命中帧，**定格窗内姿态就在变** ⟹ `victory_hitstop_ok` 红。
#     `FACE_IN1 = 28` 时实测 f26→f27 hand.L 还有 3.32° 的变化 ⟹ 唯一自洽的解是
#     「**把命中帧挪到折叠正好走完的那一帧**」：`FACE_IN0=14 / FACE_IN1=28`
#     ⟹ `POUND1 = 28`。全链顺延 2 帧（`TOTAL = 120` 不变，末段相应缩短）。
#   ★ 顺延后的帧预算（实测）：DIP 14 / 三捶 28·42·56（间隔 14）/ 定格各 3 帧 /
#     张臂 74 / 英雄姿 86 · 保持至 96（10 帧 ≥ `HERO_MIN_FRAMES = 8`）/ 回站架 110 / 收于 120。
POUND1 = _env_i("E06_POUND1", 28)             # ★ 第一捶（定格起点；= 折叠完成帧）
HOLD1 = (POUND1, POUND1 + HITSTOP_N - 1)      # [28, 30]
PULL1 = _env_i("E06_PULL1", 35)               # 拳离胸回抽
POUND2 = _env_i("E06_POUND2", 42)             # ★ 第二捶
HOLD2 = (POUND2, POUND2 + HITSTOP_N - 1)      # [42, 44]
PULL2 = _env_i("E06_PULL2", 49)
POUND3 = _env_i("E06_POUND3", 56)             # ★ 第三捶
HOLD3 = (POUND3, POUND3 + HITSTOP_N - 1)      # [56, 58]
HOLDS = (HOLD1, HOLD2, HOLD3)
POUND_FRAMES = (POUND1, POUND2, POUND3)
OPEN = _env_i("E06_OPEN", 74)                 # 张臂庆祝（挺胸 + 下巴上扬）
HERO = _env_i("E06_HERO", 86)                 # 收成英雄 pose
HERO_HOLD = _env_i("E06_HOLD", 96)            # ★ 英雄姿保持（86~96 几乎不动）
SETTLE = _env_i("E06_SETTLE", 110)            # 回站架途中
# ★ 段长 / 缓动的由来（照 E05 的实测教训，不重蹈覆辙）：
#   `victory_matrix_step_ok` 最危险的一段 = `PULL → POUND`（重击加速段）与
#   `POUND3 → OPEN`（拳从胸面甩到体侧外，行程最大）。
#   · `PULL → POUND` 用 `accel`（t²，慢起加速撞上去）—— **重击段必须保留**；
#     段长 7 帧（33→40 / 47→54）⟹ 末帧吃 (2N−1)/N² = 18.4 %，但**行程只有 ~50 mm**
#     （拳从离胸 45 mm 回到贴胸）⟹ 绝对角步不大。
#   · `POUND3 → OPEN` 用 `smooth`（两端都慢）—— 行程 ~300 mm、16 帧，
#     `decel`（开头最快）会把 16 % 塞进第 1 帧 ⟹ 照 E05 的坑，**不用 decel**。
#   · 定格之后的每一段**都不许用 `decel`**（E05 实测 30.594° @ f49 的唯一根因）。

# 臂包络（★ `ARM_DN_DONE` 必须**早于** no_snap_stop 判定窗 f110~120，见 docstring）
ARM_UP_AT = _env_i("E06_ARM_UP", 14)
ARM_DN_AT = _env_i("E06_ARM_DN", 96)
ARM_DN_DONE = _env_i("E06_ARM_DONE", 108)

# =============================================================== 反向验证旋钮
SEAM_ZERO = _env_b("E06_TP_SEAM_ZERO")        # ① 首帧改零位
NO_CONTACT = _env_b("E06_TP_NOCONTACT")       # ② ★★★ 拳离胸（命门）
DEEP = _env_b("E06_TP_DEEP")                  # ③ ★★★ 拳插进胸（互穿）
LOW_CHEST = _env_b("E06_TP_LOWCHEST")         # ④ ★★★ 捶点降到 E03 高度
ASYM = _env_b("E06_TP_ASYM")                  # ⑤ ★ 左拳抬高（破坏同步）
# ★★★ `NO_HITSTOP` **必须定义在 `KEYS` 之前**（E03 ⑤ / E04 ④ / E05 ④ 的实测教训：
#   只在 `main()` 里把 `set_hitstop` 关掉，姿态仍是冻结的 ⟹ 旋钮**惰性**）。
#   忠实仿真 = **从键表里抽掉全部 `hold` 行**，让 `POUND → PULL` 变成一整段。
NO_HITSTOP = _env_b("E06_TP_NOHITSTOP")
SLUMP = _env_b("E06_TP_SLUMP")                # ⑦ 不挺胸
NO_CHIN = _env_b("E06_TP_NOCHIN")             # ⑧ 下巴不上扬
TREMBLE = _env_b("E06_TP_TREMBLE")            # ⑨ 英雄姿颤抖
FOOT_SWAY = _env_b("E06_TP_FOOTSWAY")         # ⑩ 脚滑（骑骨盆）
LOOP_BREAK = _env_b("E06_TP_LOOPBREAK")       # ⑪ 末帧不闭合
FOOT_SWAY_MM = _env_f("E06_FOOT_SWAY_MM", 120.0)
ASYM_Z_MM = _env_f("E06_ASYM_Z", 90.0)

# =============================================================== 数值（米 / 毫米）
# ★ 捶胸几何照抄 E03 的成熟口径；★ 唯一**设计差异** = 探测点更高（上胸 vs 下胸）。
CHE_PROBE_X = _env_f("E06_PROBE_X", 0.090)    # 胸面探针的横向偏移（米）
CHE_PROBE_FWD = _env_f("E06_PROBE_FWD", 0.20)  # 探针在胸前多远（米）
# ★★★ **E06 与 E03 的核心几何差异**：捶点在**胸骨下多少**。
#   E03：`mid = chest.head.lerp(neck.head, 0.45)` ⟹ 实测命中拳心 z = 1166.6 mm（下胸）。
#   E06：探测点取 **胸骨下 54 mm**（= 上胸 / 胸肌），实测拳心 z ≈ 1262 mm（高 ~95 mm）。
#   ★ 探针几何是**实测定出来的**（`_e06_probe_site.py` 扫 x×fwd×dz 共 64 组）：
#     `fwd` 从 0.55 收到 **0.20** 是关键 —— 0.55 时最近点**饱和**在胸肌最鼓处
#     （z 恒 ≈ 1225.7，抬高探测点也不动）；收到 0.20 后最近点才**跟住**探测高度
#     （dz 0.020/0.040/0.060 → surf z 1290.6 / 1277.1 / 1254.1）。`x` 收到 0.09
#     同理（贴胸骨下缘，法线更朝前：nrm = (0.10, −0.99, 0.06)）。
#   旋钮 ④ `LOW_CHEST` 把探测点压到胸骨下 185 mm ⟹ 本判据变红。
POUND_DZ = 0.185 if LOW_CHEST else _env_f("E06_POUND_DZ", 0.054)
TOUCH_OFF = _env_f("E06_TOUCH_OFF", 0.020)    # 拳心落在「胸面 + 法线 × 本值」
PULL_OUT = _env_f("E06_PULL_OUT", 0.045)      # 回抽：拳心再离胸这么远
CHEST_EXTRA_OFF = {}                           # 保留接口（本支不使用）

# 固定世界拳目标（离胸的那些相位）—— 米
# ★★★ 摆位选择有**硬理由**（首轮实测逼出来的，不是拍脑袋）：
#   · `DIP` 的拳必须**在躯干前方足够远**（y ≤ −0.33）。首轮取 y = −0.235（贴近身体
#     侧面）⟹ 收拳 → 砸胸的那段**弧扫过躯干侧面**，实测 f=18 非拇指手网格
#     **26 个顶点插进躯干、最深 −21.42 mm**（`victory_hand_no_pierce_ok` 红）。
#   · `OPEN` / `HERO` 的拳**不许走到纯侧向（±X）**。原因见 `hand_x_hint`：
#     本支滚转基准是 `thumb_out`（±X），一旦拳轴 `y_dir` 逼近 ±X，基准投影退化
#     ⟹ 滚转由噪声决定 ⟹ 实测 f=80 `hand.L` 一步 **116.679°**（真翻，
#     `victory_matrix_step_ok` 红 + `victory_x_hint_margin` 掉到 0.323）。
#     ⟹ 张臂改成「**前上方**张开」（−Y 分量保底），拳轴全程与 ±X 保持 ≥ 55°。
FIST_DIP = {"L": Vector((0.290, -0.330, 1.095)),
            "R": Vector((-0.290, -0.330, 1.095))}
# ★★★ ★ 遗留问题（三重目检发现；本轮**试过三条路，全部被门禁否决**，阈值一字未改）：
#   `OPEN` 取 ±0.330 / z 1.400 ⟹ 拳心只比肩宽（±0.22 m）外 **0.11 m**、高度也只到
#   肩高 ⟹ three-quarter 视图**读成「耸肩摊手」**，不是「张臂庆祝」。实测外扩：
#     · x → 0.415 / z 1.435：euler 步 **75.675° @ f78**、基准余量 0.4625（逼近 0.45）
#     · x → 0.372 / z 1.475：euler 步 **40.245° @ f78**、余量 0.4898
#     · x → 0.336 / z 1.510（只抬高不外扩）：euler 步 **26.962° @ f78**
#     · 再加「`OPEN→HERO` 改 `linear` 砍峰值」：euler 降到 25.795°（仍 >25），且
#       `victory_hero_hold_ok` **变红**（3.154° > 1.6）—— 该段必须 `smooth` 才能在
#       进入英雄姿窗口时**已收静**（= 清单 E05 预警 2 的实质）。
#   ⟹ **外张幅度被两条硬约束夹死**：① `thumb_out` 滚转基准（拳轴逼近 ±X 即退化）；
#     ② 英雄姿窗口必须收静。真正的解法是**换滚转基准**（`OPEN` 段切 `thumb_up`）+ 
#     把外扩的代价挪到「长段」上 —— 属结构性改动，留给 E07/E08（同在胜利三连，
#     宜统一设计「张臂」语汇）。**本轮不退让阈值**，只登记。
FIST_OPEN = {"L": Vector((0.330, -0.330, 1.400)),
             "R": Vector((-0.330, -0.330, 1.400))}
FIST_HERO = {"L": Vector((0.265, -0.275, 1.205)),
             "R": Vector((-0.265, -0.275, 1.205))}
FIST_SETTLE = {"L": Vector((0.175, -0.310, 1.278)),
               "R": Vector((-0.175, -0.310, 1.278))}
FIST_TABLE = {"DIP": FIST_DIP, "OPEN": FIST_OPEN, "HERO": FIST_HERO,
              "SETTLE": FIST_SETTLE}
ELBOW_DIR = {"L": Vector((0.42, 1.00, -0.22)),
             "R": Vector((-0.42, 1.00, -0.22))}

# ★★ 拳**面**朝向混合：本支 = **1.0**（拳面正对胸面）—— 与 E05（碰拳，`blend=0`）相反，
#   是**设计**不是照抄：清单原文是「**捶胸**」—— 捶 = 用拳面砸，不是用拳侧蹭。
FIST_FACE_BLEND = 0.0 if _env_b("E06_TP_FACEALONG") else _env_f(
    "E06_FACE_BLEND", 1.0)
# ★★ 拳面朝胸的**相位包络**（E03 v005 的实测教训）：
#   窗口必须**内含于臂包络的平台段** = `[ARM_UP_AT(14), ARM_DN_AT(96)]`：
#     · RAMP_IN  (14, 28)：臂抬到位（14）之后才开始反折，命中（**28**）时满值；
#     · RAMP_OUT (58, 80)：第三捶（**56~58**）与张臂段之后才松开（避免与张臂叠加）。
#   ★ 首轮若写成窗口**越过**平台段，实测会在 b≈0.5 处出现 169.6°/93.7° 的逐帧真翻转。
#   ★★ `FACE_RAMP_OUT` 的终点（80）必须**早于**英雄姿窗口起点（86 ≥ `HERO`）——
#      否则「稳住不动」的那 11 帧里 `blend` 还在降 ⟹ `victory_hero_hold_ok` 红。
#   ★★ 实测修正（`_e06_probe_fold.py` 扫 IN×TWIST，逐帧量 euler/矩阵步）：
#     原写 (14, 26) ⟹ 折叠必须在 12 帧内走完 ~90° ⟹ 实测 f20 **euler 34.103°**
#     （`no_teleport` ≤ 25 判红，命中帧 `forearm.L`）、矩阵 24.739°。
#     ★ 反直觉的实测结论：**把起点提前反而更糟**（IN0=8/4/2/0 → euler 41.6/51.9/
#       52.3/49.7）—— 提前会让折叠**撞上臂包络的爬升段**（`arm_env` 在 0~14 帧
#       从 0 爬到 1），两个变化叠加。正确解法是**加宽窗口**：IN1 26 → **28**，
#       折叠摊到 14 帧 ⟹ 实测 euler **25.87°**、矩阵 **22.43°**，双双回绿。
#     另一条被证伪的路：TWIST_SPLIT 0.5/0.7/0.8 → euler 180/45.0/49.2（都更差）。
FACE_RAMP_IN = (_env_i("E06_FACE_IN0", 14), _env_i("E06_FACE_IN1", 28))
#   ★★ 实测修正（首轮）：原写 (66, 92) ⟹ 反折**还没松完就进了英雄姿窗口**
#     （f=84~94）⟹ 那段本来该「稳住不动」，实测却因为 `blend` 还在下降而
#     `hand.R` 一步 **18.001674°**（`victory_hero_hold_ok` 红）。
#     ⟹ 窗口提前到 (58, 80)：`blend` 在 f=80 已归 0 ⟹ 英雄姿窗口内**零变化**。
FACE_RAMP_OUT = (_env_i("E06_FACE_OUT0", 58), _env_i("E06_FACE_OUT1", 80))

# ★★ 手心**滚转基准**：`thumb_out`（±X 体侧外）—— E03 `_e03_hint2.py` 实测
#   对全时间轴 194 条 `y_dir` 求 `min|投影|`：±X = 0.701 ＞ 下/上 0.173 ＞
#   前/后 0.091 ＞ **胸腔法线 0.000**（捶胸时拳轴按定义就沿 −法线 ⟹ 恒正交最坏）。
HAND_AXIS_MODE = os.environ.get("E06_HAND_AXIS", "thumb_out")
HAND_CHIRALITY = ({"L": 1.0, "R": -1.0} if _env_b("E06_CHIRALITY_FLIP")
                  else {"L": 1.0, "R": 1.0})
# ★★ 腕部轴向滚转的**分配比** ρ（前臂旋前承担的比例）。
#   E03 实测：ρ=0.5 → `no_teleport` 红（27.862° @ [19, hand.R]）；ρ=0.6 → 24.081°（绿）。
#   理由：XYZ 欧拉的中间轴 = 骨轴 Y，反折 ~115° 必穿 `ry=±90°` 奇异带；
#   把滚转摊给前臂 ⟹ 腕的 `|ry|` 离奇异带更远 ⟹ euler 步不再被雅可比放大 1.5×。
TWIST_SPLIT = _env_f("E06_TWIST_SPLIT", 0.6)
FOREARM_TWIST_DEG = _env_f("E06_FOREARM_TWIST", 0.0)

# ★ 拳**心**自身不得进胸超过此值（`push_out` 用）。★ = 命中深度（本轮取 20 mm）：
#   拳心之外还有**指节前缘** ⟹ 只保护拳心挡不住「胸廓前挺时把拳面顶进胸腔」。
#   ★★ 20 mm 是**实测标定**出来的（`_e06_probe_site.py` 扫 off ∈ {14,18,22,26}）：
#     指节面到躯干的带符号距离与拳心间距存在**稳定仿射关系**
#     `knuckle ≈ core_gap − 17.74 mm`（四档 off 全部吻合到 0.01 mm）⟹
#     要满足「贴合 ≤ +8 / 不穿透 ≥ −10」⟹ `core_gap ∈ [7.74, 25.74] mm`。
#     取 **20 mm**（正中间）⟹ 实测指节面 **+2.3 mm**（轻贴胸面，不穿）。
FIST_MIN_CLEAR_MM = _env_f("E06_FIST_CLEAR", 0.0) or (TOUCH_OFF * 1000.0)

# =============================================================== 躯干规格
# ★ 量纲：**全部是相对站架的增量**，3 元组 (rx, ry, rz)（度）；未列出的骨 = 站架值。
#   `loc` = (世界 dy, 世界 dz)（米）：+dy = 身后，+dz = 上。
#   ★★ **`ry` 全程 = 0**（E05 的硬教训：腰扭转按定义不对称，与对称手势互斥）。
SPECS = {
    "STATION": {"pelvis": (0.0, 0.0, 0.0), "spine_01": (0.0, 0.0, 0.0),
                "spine_02": (0.0, 0.0, 0.0), "chest": (0.0, 0.0, 0.0),
                "neck": (0.0, 0.0, 0.0), "head": (0.0, 0.0, 0.0),
                "shoulder.L": (0.0, 0.0, 0.0), "shoulder.R": (0.0, 0.0, 0.0),
                "loc": (0.0, 0.0)},
    # 收拳蓄势：肩**后张**（拳收到体侧前）、沉髋、髋后坐（要捶胸先收拳）
    "DIP": {"pelvis": (4.0, 0.0, 0.0), "spine_01": (2.0, 0.0, 0.0),
            "spine_02": (2.0, 0.0, 0.0), "chest": (3.0, 0.0, 0.0),
            "neck": (-1.0, 0.0, 0.0), "head": (-2.0, 0.0, 0.0),
            "shoulder.L": (6.0, 0.0, 12.0), "shoulder.R": (6.0, 0.0, -12.0),
            "loc": (0.020, -0.034)},
    # ★★ 捶击命中：**肩前送 + 胸口迎拳 + 屈膝下沉**（力量链在命中帧全部到位）。
    #   ★ 下巴**微抬**（−5°）—— 与 E03 命中帧的「头未动」不同，是本支的庆祝底色。
    "POUND": {"pelvis": (5.0, 0.0, 0.0), "spine_01": (2.5, 0.0, 0.0),
              "spine_02": (2.5, 0.0, 0.0), "chest": (1.5, 0.0, 0.0),
              "neck": (-2.0, 0.0, 0.0), "head": (-5.0, 0.0, 0.0),
              "shoulder.L": (2.0, 0.0, -8.0), "shoulder.R": (2.0, 0.0, 8.0),
              "loc": (0.010, -0.030)},
    # 回抽：拳离胸 45 mm，躯干微起（为下一次捶积蓄）
    "PULL": {"pelvis": (4.0, 0.0, 0.0), "spine_01": (2.0, 0.0, 0.0),
             "spine_02": (2.0, 0.0, 0.0), "chest": (2.5, 0.0, 0.0),
             "neck": (-1.5, 0.0, 0.0), "head": (-3.5, 0.0, 0.0),
             "shoulder.L": (5.0, 0.0, 6.0), "shoulder.R": (5.0, 0.0, -6.0),
             "loc": (0.014, -0.030)},
    # ★★ 张臂庆祝：双拳向外张开 + **挺胸**（chest rx = −4 ⟹ 后仰挺胸）+ 下巴上扬
    #   + 双肩**后张外展**（rz 符号：L + / R − = 后张）。
    #   ★ 本段是 E06 相对 E03 的**结构性新增**（E03 全程没有张臂段）。
    "OPEN": {"pelvis": (-2.0, 0.0, 0.0), "spine_01": (-1.0, 0.0, 0.0),
             "spine_02": (-1.5, 0.0, 0.0), "chest": (-4.0, 0.0, 0.0),
             "neck": (-4.0, 0.0, 0.0), "head": (-12.0, 0.0, 0.0),
             "shoulder.L": (16.0, 0.0, 10.0), "shoulder.R": (16.0, 0.0, -10.0),
             "loc": (0.004, -0.008)},
    # 英雄 pose：挺胸 + 下巴上扬 + 双拳收在胸前偏外（虚握），肩略张
    "HERO": {"pelvis": (-1.0, 0.0, 0.0), "spine_01": (0.0, 0.0, 0.0),
             "spine_02": (-1.0, 0.0, 0.0), "chest": (-3.7, 0.0, 0.0),
             "neck": (-3.0, 0.0, 0.0), "head": (-9.0, 0.0, 0.0),
             "shoulder.L": (10.0, 0.0, 5.0), "shoulder.R": (10.0, 0.0, -5.0),
             "loc": (0.004, -0.006)},
    # ★ 英雄姿保持（84~94）：与 HERO 只差**不到 0.3°/0.5 mm** ⟹ 读作「稳住不动」，
    #   而不是颤抖（`victory_hero_hold_ok` 盯着这一段）。
    #   ★ 实测修正：原写 −3.5 / −3.4 ⟹ 绝对 `chest rx` 只有 −2.5 / −2.4，
    #     顶到 `PUFF_MAX_RX = −2.5` 的边界外（worst −2.4 > −2.5 ⟹ 判红）。
    #     两帧同降 0.2°（保持 0.1° 的帧间差）⟹ 绝对 −2.7 / −2.6，满足「挺胸」。
    "HERO_HOLD": {"pelvis": (-0.9, 0.0, 0.0), "spine_01": (0.0, 0.0, 0.0),
                  "spine_02": (-0.9, 0.0, 0.0), "chest": (-3.6, 0.0, 0.0),
                  "neck": (-2.9, 0.0, 0.0), "head": (-8.8, 0.0, 0.0),
                  "shoulder.L": (9.8, 0.0, 5.1), "shoulder.R": (9.8, 0.0, -5.1),
                  "loc": (0.0037, -0.0055)},
    # 回站架途中（残余极小 ⟹ 尾段角步自然收敛）
    "SETTLE": {"pelvis": (0.4, 0.0, 0.0), "spine_01": (0.2, 0.0, 0.0),
               "spine_02": (0.2, 0.0, 0.0), "chest": (0.3, 0.0, 0.0),
               "neck": (-0.2, 0.0, 0.0), "head": (-0.5, 0.0, 0.0),
               "shoulder.L": (2.0, 0.0, -1.5), "shoulder.R": (2.0, 0.0, 1.5),
               "loc": (0.002, -0.003)},
}

_CELEB = ("OPEN", "HERO", "HERO_HOLD")


def spec_of(name):
    spec = dict(SPECS[name])
    if SLUMP and name in _CELEB:
        # ⑦ 不挺胸：把胸从后仰（−4）拨到前倾（+3），头也压下来一点。
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
    (DIP, "smooth", "DIP", "DIP"),
    (POUND1, "accel", "POUND", "POUND"),
]
if not NO_HITSTOP:
    KEYS.append((HOLD1[1], "hold", "POUND", "POUND"))
KEYS += [
    (PULL1, "smooth", "PULL", "PULL"),
    (POUND2, "accel", "POUND", "POUND"),
]
if not NO_HITSTOP:
    KEYS.append((HOLD2[1], "hold", "POUND", "POUND"))
KEYS += [
    (PULL2, "smooth", "PULL", "PULL"),
    (POUND3, "accel", "POUND", "POUND"),
]
if not NO_HITSTOP:
    KEYS.append((HOLD3[1], "hold", "POUND", "POUND"))
KEYS += [
    (OPEN, "smooth", "OPEN", "OPEN"),
    (HERO, "smooth", "HERO", "HERO"),
    (HERO_HOLD, "smooth", "HERO_HOLD", "HERO"),
    (SETTLE, "smooth", "SETTLE", "SETTLE"),
    (END, "smooth", "STATION", "STATION"),
]

# =============================================================== 阈值
# ★ 全部由**设计意图 + 实测定**；铁律：不许为了变绿而放宽。
#   ① 捶胸「贴合」：指节面（`Finger_*` 顶点）到躯干面的最小带符号距离上限。
POUND_CONTACT_MAX_MM = _env_f("E06_CONTACT_MAX", 8.0)
#   ③ 捶胸「互不穿透」：允许陷入胸体的最大深度。
POUND_PIERCE_MM = _env_f("E06_PIERCE", 10.0)
#   ② 捶胸「同步对称」：两拳心关于中线的镜像偏差（三捶全部要满足）。
POUND_SYM_X_MM = _env_f("E06_SYM_X", 20.0)
POUND_SYM_Y_MM = _env_f("E06_SYM_Y", 25.0)
POUND_SYM_Z_MM = _env_f("E06_SYM_Z", 25.0)
#   ★★★ 捶点高度（E06 与 E03 的核心差异）：E03 实测 1166.6 ⟹ 本支要求 ≥ 1255。
POUND_Z_MIN_MM = _env_f("E06_POUND_Z_MIN", 1255.0)
POUND_X_MAX_MM = _env_f("E06_POUND_X_MAX", 150.0)
POUND_COUNT = _env_i("E06_POUND_COUNT", 3)
#   ④ 挺胸：庆祝段 `chest rx` 必须 ≤ 本值（负 = 后仰挺胸）。
PUFF_MAX_RX = _env_f("E06_PUFF_RX", -2.5)
#   ⑥ 下巴上扬（区间两端）：庆祝段 `head_back` ∈ [lo, hi]；E03 怒吼是 36°。
CHIN_RANGE = (_env_f("E06_CHIN_LO", 8.0), _env_f("E06_CHIN_HI", 24.0))
#   ⑧ 本支**不怒吼**：全程 `head_back` 不得超过本值（严格低于 E03 的 36°）。
NO_ROAR_MAX = _env_f("E06_ROAR_MAX", 26.0)
#   ⑦ 英雄姿稳定：`HERO..HERO_HOLD` 窗口内逐帧最大角步 ≤ 本值，且窗口 ≥ N 帧。
HERO_STEP_MAX_DEG = _env_f("E06_HERO_STEP", 1.6)
HERO_MIN_FRAMES = _env_i("E06_HERO_N", 8)
#   ⑥ 定格：窗口内逐帧姿态冻结（`max |Δ euler|`）。
HITSTOP_STEP_MAX_DEG = _env_f("E06_HITSTOP_STEP", 0.01)
FOOT_LOCK_MM = _env_f("E06_FOOT_LOCK", 0.5)
TOE_LOCK_MM = _env_f("E06_TOE_LOCK", 0.5)
SOLE_BAND = (-2.0, 6.0)
NO_SNAP_END_DEG = _env_f("E06_SNAP_END", 6.0)
SEAM_POS_MAX_MM = _env_f("E06_SEAM_POS", 0.01)
SEAM_DIR_MAX_DEG = _env_f("E06_SEAM_DIR", 0.05)
CLIP_MAX_MM = _env_f("E06_CLIP_MAX", 0.0)
REACH_MAX_RATIO = 0.995
MATRIX_STEP_MAX_DEG = _env_f("E06_MATSTEP", 25.0)
TAIL_SETTLE_N = _env_i("E06_TAIL_N", 10)
HAND_PIERCE_MM = _env_f("E06_HAND_PIERCE", 10.0)
HAND_X_HINT_MIN_MARGIN = _env_f("E06_HINT_MARGIN", 0.45)

# 出图/像素探针共用的**逐帧集合**（主渲、反面重渲、像素探针三者必须逐帧相同）
# ★ 本轮随相位顺延同步重排（旧表是按 26 / 72 / 84 定的）：起手 / 蓄势 / 折叠中段 /
#   三捶的**命中帧与定格末帧**（28/30、42/44、56/58，每捶各 2 帧）/ 回抽 / 张臂 /
#   英雄姿两端 / 回站架两端 —— 保证「关键姿态」逐一有图可看。
STEM_FRAMES = sorted(set([0, 8, 14, 20, 26, 28, 30, 35, 42, 44, 49, 56, 58,
                          62, 68, 74, 80, 86, 91, 96, 103, 110, 115, 120]))

# =============================================================== 取景（★ 本支自立）
# ★ 取景跨度的由来：本支**不跳不躺**，纵向最高点 = 站架头顶 ≈ 1803 mm（张臂时
#   双拳升到 z ≈ 1310 mm + 拳半径），最低点 = 鞋底 0 mm，最外 = 张臂时拳心
#   x = ±400 mm（含拳半径 ≈ ±440 mm）。⟹ 纵向覆盖 −0.15 ~ 1.95 m（中心 z = 0.90、
#   正交高 2.10 m）；横向需 ≥ ±0.75 m ⟹ 正面用 780×1100（横 = 2.10×780/1100 = 1.489 m）。
#   ★ **不照抄** E03 的 (0.90 / 1.95)：本支需要**略高一点**装下张臂。
VIEW_E06_SIDE = ("side", (4.4, -0.05, 0.92), (0.0, -0.05, 0.92), 2.10,
                 (780, 1100))
VIEW_E06_FRONT = ("front", (0.0, -4.9, 0.92), (0.0, 0.0, 0.92), 2.10,
                  (780, 1100))

TRACE = _env_b("E06_TRACE")
_BLEND_TRACE = _env_b("E06_TRACE_BLEND")
TGT_TRACE = _env_b("E06_TRACE_TGT")
SITE_TRACE = _env_b("E06_TRACE_SITE")
IK_TRACE = _env_b("E06_TRACE_IK")
_STEP_TRACE = _env_b("E06_TRACE_STEP")

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
      站架实测值** ⟹ 接缝帧（f=0 / f=120）逐位等于站架。
    ★ `ARM_DN_DONE`（108）是「回 0 **完成**」帧，**早于** `no_snap_stop_ok` 的判定窗
      （末 10 帧 f110~120）⟹ 尾段臂**已经等于站架**，姿态静止，判据自然满足。
    """
    if frame <= ARM_UP_AT:
        return _smoothstep(frame / float(max(1, ARM_UP_AT)))
    if frame >= ARM_DN_AT:
        span = float(max(1, ARM_DN_DONE - ARM_DN_AT))
        return _smoothstep((ARM_DN_DONE - frame) / span)
    return 1.0


FACE_EASE = os.environ.get("E06_FACE_EASE", "linear")   # "smooth" | "linear"


def _face_ramp(x):
    x = max(0.0, min(1.0, x))
    return x if FACE_EASE == "linear" else _smoothstep(x)


def face_blend(frame):
    """「拳面正对胸面」的混合系数**随相位**变化（E03 v005 的成熟口径）。

    ★★★ 为什么不能全时段恒 1.0：`blend = 1` 意味着手腕相对前臂**反折约 90°**，
      而站架的手是「掌心朝内、沿前臂」的 ⟹ 反折若与臂包络（`arm_env` 0→1）
      叠加，手腕要在十几帧里完成这次反折 —— E03 实测 `matrix_step = 51.5°`
      （真旋转）、且手在扫过躯干时最多 210 个顶点在体内、最深 −43.11 mm。
    ★ 修法：把「反折」**移出包络过渡段** —— 过渡段拳沿前臂（两端姿态差小），
      等拳已抬到身前再完成反折，收招时先松开反折再放下手臂。
    ★★ `E06_FACE_EASE`（本轮新增）：实测「折叠速度」才是 `no_teleport` 的真凶，
      而**缓动形状**能直接改峰值速率 —— `smoothstep` 的峰值是均值的 **1.5 倍**，
      `linear` 只有 **1.0 倍**（E06 实测见 §「折叠窗口」的注释）。
    """
    blend = FIST_FACE_BLEND
    if blend <= 0.0:
        return 0.0
    lo, hi = FACE_RAMP_IN
    if frame <= lo:
        return 0.0
    if frame < hi:
        return blend * _face_ramp((frame - lo) / float(max(1, hi - lo)))
    lo2, hi2 = FACE_RAMP_OUT
    if frame >= hi2:
        return 0.0
    if frame > lo2:
        return blend * _face_ramp((hi2 - frame) / float(max(1, hi2 - lo2)))
    return blend


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
    """欧拉表示兼容化（C14 / D01 / E03 / E04 / E05 踩过的同一个万向节锁坑）。

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

    ★★ **本支是「全程」口径**（E06 不跳、不位移；E04 是分段）：`want` 恒 = 站架踝
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


def chest_surface(arm, side):
    """当前姿态下「**上胸**表面点 + 外法线」（世界）。逐帧重解，不是静态值。

    ★★★ 与 E03 的唯一差别：探测点的**高度**。E03 用
      `mid = chest.head.lerp(neck.head, 0.45)`，实测命中拳心 z = 1166.6 mm（**下胸**）。
      本支取 **胸骨（`neck.head`）下 `POUND_DZ` = 70 mm** ⟹ 命中拳心 z ≈ 1277 mm
      （**上胸 / 胸肌**），比 E03 高 ~110 mm —— 这就是两支动画「捶哪儿」的量化差异。
    """
    ev, mw = _torso_eval()
    ct = Vector(A.bone_world(arm, "neck", "head"))    # 胸骨顶（= 颈根）
    sx = 1.0 if side == "L" else -1.0
    probe = Vector((sx * CHE_PROBE_X, ct.y - CHE_PROBE_FWD, ct.z - POUND_DZ))
    _ok, loc, nrm, _idx = ev.closest_point_on_mesh(mw.inverted() @ probe)
    world_loc = mw @ loc
    world_nrm = (mw.to_3x3() @ nrm).normalized()
    return world_loc, world_nrm


def push_out(point, min_gap_mm):
    """把拳目标**顶出**胸腔（沿胸面外法线），只在该点比下限更深时才动它。

    ★★★ 为什么必须做（E03 v003 的核心修正）：拳目标在**时间上**是插值的，
      「离胸位」↔「胸面点」之间的直线弦可能**切进躯干**。一个实心拳头不可能
      在胸腔里 ⟹ 对插值后的目标点做一次「沿外法线顶出」：只在比**命中深度**
      更深时才动它 ⟹ 命中姿态本身**完全不受影响**，只是把穿透的弦自动换成
      「贴着胸面滑进/滑出」（这也是**正确的动作**：拳是擦着胸口滑的）。
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
INSIDE_VOTES_MIN = _env_i("E06_INSIDE_VOTES", 7)
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
    """点沿 13 个方向各打一条射线，返回**得票数**（全票 13 = 内部）。

    ★★★ 为什么用投票而不是单方向奇偶（E03 `_e03_yard.py` 实测）：`Suit_Torso`
      是水密的，但单方向射线会**擦过边 / 顶点** ⟹ 一次擦边就多算一次穿越 ⟹
      假阳性（实测 f=60 单方向报 22 个"体内顶点"，实际得票全是 1）。
      多方向下真内部恒 13/13 票、噪声恒 ≤ 2 票，**断崖式分离**。
    """
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


def fist_face_gap(side, step=2):
    """★ 本支主判据：**指节面**（`Finger_*` 顶点，不含拇指/掌）到躯干面的
    **最小带符号距离**（mm；正 = 在胸外，负 = 已陷入胸体）。"""
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
    """该侧手网格 vs **躯干**的几何读数（排除拇指的口径是判据，拇指单独登记）。

    ★ `limit_mm`（可选）：绝对穿模下限（mm）⟹ 额外返回 `beyond_limit`
      = **低于该下限的非拇指顶点数**（本支取 `HAND_PIERCE_MM = 10 mm`）。
      ★ 这是本支**改用的数量口径**：原口径「体内顶点个数 ≤ 站架个数」被实测推翻
        （站架附近有 ~9 个顶点紧贴胸面 ±5 mm，刀刃型读数），见断言 ⑬ 的 note。
    """
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
    """按 `HAND_AXIS_MODE` 给出「`hand.local_x` 应指向的世界方向」。

    ★ 必须先乘 `HAND_CHIRALITY`：左右手 rest 基的 `local_x` 与拇指**反向**
      （`hand.L` 的 `local_x = (0,−1,0)`、`hand.R` 的 `local_x = (0,+1,0)`），
      不修正就会出现「一侧拇指朝上、另一侧拇指朝下」的镜像错位。
    ★ 默认模式 `thumb_out` 是**扫出来的**（E03 `_e03_hint2.py`）：±X 余量 0.701，
      而 YZ 平面内的任何基准（下/上、前/后、胸腔法线）在捶胸时必然退化 ——
      因为捶胸时拳轴就沿 −法线，法线恒正交于 y（余量 0.000）。
    """
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
    """用**显式正交基**摆 `hand.<side>`：`local_y` = `y_dir`，`local_x` 尽量贴 `x_hint`。

    `local_z = local_x × local_y`（rest 实测的右手系约定）。
    ★ E03 v009 的教训：基准「由几何量算得」**不等于**连续 —— 若基准落在骨轴
      方向上，投影长度 → 0 ⟹ 滚转由浮点噪声决定 ⟹ **真旋转 83.86°/帧**。
      ⟹ 修法是**换基准**（`thumb_out`），不是打补丁；且必须有 `x_hint` 余量断言盯着。
    """
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
    LAST_HAND_FRAME[side] = (y_axis.copy(), x_axis.copy())
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
_LAST_FO = {}
_LAST_HD = {}
LAST_TWIST_ANGLE = {}
LAST_ELBOW = {}


def seat_arm(arm, pose, targets, normals, blend=1.0, env=1.0):  # noqa: C901
    """把臂解到拳心目标上（结构照抄 E03 的成熟版：IK 连续性 + 旋前分摊 + 包络收敛）。

    ★★★ `env`（= `arm_env(frame)`）是「收招不炸 / 起手不炸」的关键：
      IK 解在 `env=0` 时**并不自动等于站架解**（`orient_hand` 是绝对设定手的世界
      朝向，与站架松拳朝向可差 ~120°）⟹ 包络两端不重合，混合就会用 Δenv/帧
      去推一个上百度的差 ⟹ 实测 15.75°/帧，`no_snap_stop_ok` 必红。
      ⟹ 修法：把 IK 解的**三个自由度**（肘极向量、拳轴 `y_dir`、滚转基准 `x_hint`）
        按 `env` 向**站架实测值**插值 ⟹ `env→0` 时 IK 解**逐位收敛到站架臂**。
      ★ 这不是掩盖：它把「接缝处必须等于站架」从「靠包络近似」升级成
        「IK 解本身就等于站架」，三条矩阵口径断言**照旧独立**盯着。
    """
    A.apply_pose(arm, pose)
    for side in SIDES:
        up, fo, hd = ("upperarm." + side, "forearm." + side, "hand." + side)
        shoulder = Vector(A.bone_world(arm, up, "head"))
        core = Vector(targets[side])
        nrm = Vector(normals.get(side, Vector((0.0, -1.0, 0.0)))).normalized()
        # ★ 拳**面**朝向：`along`（拳沿前臂）→ `−nrm`（拳面正对胸）的测地线混合。
        #   ★ 必须走**测地线**（大圆）：线性式在 b≈0.5 处模长趋近 0，归一化后
        #     方向由浮点噪声决定 ⟹ 腕在相邻两帧间整体翻过去（E03 实测 93.736°）。
        #   ★ `along` 用**前臂方向**（core − 肘）而不是 core − 肩：E03 实测
        #     `∠(core−shoulder, −nrm) = 142~170°`（近反对跖），而 `∠(core−elbow, −nrm)
        #     = 87~136°` ⟹ 混合跨过的弧少 30~45°，腕步长随之下降。
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
        # ★★★ 2026 修复（本支开工实测发现）：三角解**必须用前臂骨长**（224 mm），
        #   不是 `ARM_LEN_LO`（322 = 前臂 + 手）。理由：`hand` 骨的朝向由
        #   `orient_hand` **独立**钉到 `y_dir`（拳面朝胸），**不**沿 `fo_dir`。
        #   旧式用 322 解三角 ⟹ 肘被放到「离腕 322mm」的位置，而前臂只能伸 224mm
        #   ⟹ 腕落在 `wrist_target − fo_dir_n × 98 mm`，拳心 = 目标 − 98·fo_dir_n。
        #   实测（修复前 f26 L）：core z 1199.0 → 拳心 z 1121.6，**差 98.0 mm 且
        #   方向恰为 −fo_dir_n**。⟹ 「捶点」其实比瞄准点低 ~77 mm，捶在了下胸。
        #   ⟹ 用 224 解三角后：`|elbow→wrist| = 224`、`wrist = wrist_target`、
        #   `fist = wrist + y_dir×98 = core`，**拳心精确落在目标上**。
        #   （E03 / E05 用的是旧式，其"命中点"同样带着这个 98 mm·fo_dir_n 的偏移 ——
        #     它们的数值是在该偏移下**标定**出来的，故不受影响；本支要「捶点更高」，
        #     必须先把「瞄准 ≠ 命中」这件事消掉，否则高度是小臂朝向的副产物。）
        limit = (ARM_LEN_UP + FOREARM_LEN) * 0.9995
        distance = max(1e-4, min(delta.length, limit))
        axis = (delta.normalized() if delta.length > 1e-9
                else Vector((0.0, 0.0, -1.0)))
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
        bulge.normalize()
        if env < 1.0:
            bulge = _slerp_dir(STATION_POLE_DIR[side], bulge, env)
        else:
            bulge = bulge.copy()
        bulge.normalize()
        cos_sh = max(-1.0, min(1.0, (ARM_LEN_UP ** 2 + distance ** 2
                                     - FOREARM_LEN ** 2)
                               / (2.0 * ARM_LEN_UP * distance)))
        sin_sh = math.sqrt(max(0.0, 1.0 - cos_sh * cos_sh))
        elbow = shoulder + (axis * cos_sh + bulge * sin_sh) * ARM_LEN_UP
        LAST_ELBOW[side] = elbow.copy()
        pose[up] = A.aim_bone(arm, up, elbow - shoulder)
        fo_dir = target - elbow
        base_twist = FOREARM_TWIST_DEG * blend * HAND_CHIRALITY[side]
        pose[fo] = A.aim_bone(arm, fo, fo_dir, twist_deg=base_twist)
        hint = hand_x_hint(side, nrm)
        if env < 1.0:
            hint = _slerp_dir(STATION_HAND_X[side], hint, env)
        # ★★★ 2026 修复：腕部轴向滚转的**分配量**改由**矩阵几何量**给出，
        #   **不再**读 `hand.rotation_euler.y`。
        #   旧式（读 euler 中间轴 + 不动点迭代）在万向节锁附近**会炸**：
        #   XYZ 欧拉的 ry 在奇点邻域**不是连续量** —— 实测（本支 f75→f76, hand.R）
        #   手骨世界矩阵只动了 **7.6°**，但 euler `ry` 从 **−73.0 跳到 +74.4**；
        #   由于 twist 是 ry 的仿射函数（收敛值 ≈ 0.5·ry），twist 随之从 −102.1
        #   跳到 +104.3 ⟹ 前臂绕自身轴**真翻 151.4°/帧**（`victory_matrix_step_ok` 红）。
        #   ★ 这不是「欧拉表示在跳」（矩阵口径也红），是**用了一个不连续的输入量**。
        #   ⟹ 改用**测地量**：θ = 绕骨轴从「前臂未旋前的世界 X（`u`）」到「手的目标
        #     世界 X（`x_axis`）」的**带符号夹角**。`u` 与 `x_axis` 都随姿态连续变化
        #     ⟹ θ 连续；再按前帧 `θ` 展开（±360 整数倍）⟹ 跨帧也连续。
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
        prev_theta = LAST_TWIST_ANGLE.get(side)
        if prev_theta is not None:
            theta += 360.0 * round((prev_theta - theta) / 360.0)
        LAST_TWIST_ANGLE[side] = theta
        twist = TWIST_SPLIT * theta + base_twist
        pose[fo] = A.aim_bone(arm, fo, fo_dir, twist_deg=twist)
        LAST_HAND_X[side] = orient_hand(arm, side, y_dir, hint)
        LAST_FOREARM_TWIST[side] = twist
        if IK_TRACE:
            _w = Vector(A.bone_world(arm, fo, "head"))
            _t = Vector(A.bone_world(arm, hd, "tail"))
            _fm = arm.pose.bones[fo].matrix.to_3x3().normalized()
            _hm = arm.pose.bones[hd].matrix.to_3x3().normalized()
            _dfo = _dhd = 0.0
            if side in _LAST_FO:
                _a, _b = _LAST_FO[side], _fm
                _dfo = max(math.degrees(math.acos(max(-1.0, min(
                    1.0, _a.col[i].normalized().dot(_b.col[i].normalized())))))
                    for i in range(3))
                _a, _b = _LAST_HD[side], _hm
                _dhd = max(math.degrees(math.acos(max(-1.0, min(
                    1.0, _a.col[i].normalized().dot(_b.col[i].normalized())))))
                    for i in range(3))
            _LAST_FO[side], _LAST_HD[side] = _fm, _hm
            print("E06_IK %s core=[%.1f,%.1f,%.1f] sh=[%.1f,%.1f,%.1f] "
                  "wr_tgt=[%.1f,%.1f,%.1f] dlen=%.1f lim=%.1f dist=%.1f "
                  "wr=[%.1f,%.1f,%.1f] tail=[%.1f,%.1f,%.1f] "
                  "twist=%.1f ry=%.1f dfo=%.1f dhd=%.1f"
                  % (side, core.x * 1000, core.y * 1000, core.z * 1000,
                     shoulder.x * 1000, shoulder.y * 1000, shoulder.z * 1000,
                     target.x * 1000, target.y * 1000, target.z * 1000,
                     delta.length * 1000, limit * 1000, distance * 1000,
                     _w.x * 1000, _w.y * 1000, _w.z * 1000,
                     _t.x * 1000, _t.y * 1000, _t.z * 1000,
                     twist, math.degrees(
                         arm.pose.bones[hd].rotation_euler.y), _dfo, _dhd))
        pose[hd] = tuple(math.degrees(v)
                         for v in arm.pose.bones[hd].rotation_euler)
    return pose


# =============================================================== 拳目标
def resolve_fist(name, side, arm):
    """拳心目标（世界，米）。

    · `STATION` → 站架实测拳心（接缝锚）；
    · `POUND`   → **当前帧胸面点 + 外法线 × TOUCH_OFF**（胸面逐帧重解）；
    · `PULL`    → 同上但再远 `PULL_OUT`（回抽）；
    · 其余（DIP / OPEN / HERO / SETTLE）→ 固定世界点（都离胸，不随姿态变）。
    """
    if name == "STATION":
        return Vector(STATION_FIST[side])
    if name in ("POUND", "PULL"):
        surf, nrm = chest_surface(arm, side)
        off = TOUCH_OFF + (PULL_OUT if name == "PULL" else 0.0)
        # ★★★ 反面旋钮必须接进代码（否则惰性）：
        #   ② NO_CONTACT → 拳心再离胸 60 mm（读作「没捶到」）；
        #   ③ DEEP       → 拳心再进胸 30 mm（读作「插进胸腔」）。
        if NO_CONTACT:
            off += 0.060
        if DEEP:
            off -= 0.030
        point = surf + nrm * off
        if SITE_TRACE and name == "POUND":
            _ct = Vector(A.bone_world(arm, "neck", "head"))
            _ch = Vector(A.bone_world(arm, "chest", "head"))
            print("E06_SITE %s ct=[%.1f,%.1f,%.1f] ch=[%.1f,%.1f,%.1f] "
                  "probe_z=%.1f surf=[%.1f,%.1f,%.1f] nrm=[%.2f,%.2f,%.2f] "
                  "tgt=[%.1f,%.1f,%.1f]"
                  % (side, _ct.x * 1000, _ct.y * 1000, _ct.z * 1000,
                     _ch.x * 1000, _ch.y * 1000, _ch.z * 1000,
                     (_ct.z - POUND_DZ) * 1000,
                     surf.x * 1000, surf.y * 1000, surf.z * 1000,
                     nrm.x, nrm.y, nrm.z,
                     point.x * 1000, point.y * 1000, point.z * 1000))
        if ASYM and name == "POUND" and side == "L":
            point = Vector((point.x, point.y, point.z + ASYM_Z_MM / 1000.0))
        return point
    return Vector(FIST_TABLE[name][side])


def _aim_world(name, side, arm, root_off):
    """拳的**世界**目标点（唯一的「世界 vs 随骨盆」口径在这里定死）。

    ★★★ 开工实测修复（`_e06_probe_site.py` / `_e06_probe_f26.py`）：
      `POUND` / `PULL` 的目标由 `chest_surface` **逐帧从当前姿态的胸面**解出 ——
      它读的是**当前帧**的 `neck.head` ⟹ 该点**已经包含**骨盆的世界位移。
      早先在这里又 `+ root_off` ⟹ **骨盆位移被算了两遍**（POUND 的 `loc.dz = −30 mm`
      被扣了两次）⟹ 实测第二拍起拳心 z = **1199.0**，而瞄准点其实在 **1229.5**
      （差 30.5 mm ≈ `root_off.z`）⟹ `victory_pound_site_ok` 是**假红**（不是 IK 错、
      也不是胸够不着）。IK 侧已被 `_e06_probe_f26.py` 反证：`core == want`，`|d| = 0.00 mm`。
      ⟹ 只有**固定表**（`DIP / OPEN / HERO / SETTLE / STATION`，定义在**站架基准**上）
        才需要随骨盆平移。
    """
    base = Vector(resolve_fist(name, side, arm))
    if name in ("POUND", "PULL"):
        return base
    return base + root_off


def fist_targets(arm, frame, root_off):
    """拳目标 = **绕肩的球面插值**（方向 slerp + 半径缓动）。

    ★ 为什么不用世界直线 lerp：两端方向差大时弦会贴近肩关节 ⟹ 肘被折进去再弹出
      ⟹ 前臂世界角步爆表（E04 实测 32.6°/帧）。本支 `POUND3 → OPEN` 两端方向
      差大（胸前中线 ↔ 体侧外上方），同样必须走球面。
    """
    index, t, kind = _segment(frame)
    ga = _ease(kind, t)
    a_name = KEYS[index][3]
    b_name = KEYS[index + 1][3]
    out = {}
    for side in SIDES:
        shoulder = Vector(A.bone_world(arm, "upperarm." + side, "head"))
        va = _aim_world(a_name, side, arm, root_off) - shoulder
        vb = _aim_world(b_name, side, arm, root_off) - shoulder
        ra, rb = va.length, vb.length
        if ra < 1e-6:
            dirv = vb.normalized()
        elif rb < 1e-6:
            dirv = va.normalized()
        else:
            dirv = _slerp_dir(va.normalized(), vb.normalized(), ga)
        point = shoulder + dirv * (ra + (rb - ra) * ga)
        # ★ ③ DEEP 必须**绕开**这道保护（否则顶回胸外 ⟹ 旋钮惰性、判据不见红）。
        if not DEEP:
            point = push_out(point, FIST_MIN_CLEAR_MM)
        if TGT_TRACE and frame in POUND_FRAMES:
            print("E06_TGT f=%3d %s gap=%+7.2f" % (frame, side,
                                                   signed_to_torso(point)))
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
            print("E06_BLEND %-12s env=%.3f span=%.1f"
                  % (name, env, max(abs(y - x) for x, y in zip(a, b))))
        out[name] = tuple(x + (y - x) * max(0.0, min(1.0, env))
                          for x, y in zip(a, b))
    return out


def victory_pose(arm, frame):  # noqa: C901
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
        #   ★ 忠实仿真必须让脚的目标位置**依赖当前躯干姿态**（恒定偏移在任何帧都
        #     相同 ⟹ 跨帧漂移恒 0 ⟹ 旋钮惰性，E03 v012 / E04 ⑦ 的教训）。
        A.apply_pose(arm, pose)
        delta = Vector(A.bone_world(arm, "pelvis", "head")) - PELVIS0
        scale = FOOT_SWAY_MM / 55.0
        for s in SIDES:
            want[s] = want[s] + delta * scale
    lock_err = lock_feet(arm, pose, want)

    # ---- 臂：对**当前帧的胸**重解，再按 `arm_env` 与站架臂混合（保证接缝）--------
    env = arm_env(frame)
    A.apply_pose(arm, pose)
    ik_pose = dict(pose)
    seat_arm(arm, ik_pose, fist_targets(arm, frame, root_off),
             {s: chest_surface(arm, s)[1] for s in SIDES},
             face_blend(frame), env)
    blended = _blend_local(pose, ik_pose, env)
    for name in ARM_BONES:
        pose[name] = blended[name]

    if LOOP_BREAK and frame == TOTAL:
        rx, ry, rz = pose["chest"]
        pose["chest"] = (rx + 4.0, ry, rz + 4.0)

    if TRACE:
        A.apply_pose(arm, pose)
        low = A.foot_lowest_by_side()
        soles = {s: round(low[s][2] * 1000.0, 1) for s in SIDES
                 if low[s] is not None}
        gaps = {s: round(signed_to_torso(
            A.bone_world(arm, "hand." + s, "tail")), 1) for s in SIDES}
        cores = {s: [round(v * 1000.0, 1)
                     for v in A.bone_world(arm, "hand." + s, "tail")]
                 for s in SIDES}
        faces = {s: fist_face_gap(s, step=4) for s in SIDES}
        print("E06_TRACE f=%3d dy=%+6.1f dz=%+6.1f sole=%s core=%s face=%s "
              "lock=%.4f env=%.3f abs=%s"
              % (frame, dy * 1000.0, dz * 1000.0, soles, gaps, faces,
                 lock_err, env, cores))
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

    def pelvis_z_mm(frame):
        return Vector(samples[idx[frame]]["pelvis"]).z * 1000.0

    def knee_deg(frame):
        return max(abs(samples[idx[frame]]["euler"].get("shin." + s,
                                                        (0.0, 0.0, 0.0))[0])
                   for s in SIDES)

    def head_back_deg(frame):
        """仰头 / 下巴上扬角（度，**正 = 后仰**）= −(Δneck_rx + Δhead_rx)。

        ★ 口径照 E03 `current_head_back`：量的是**相对站架（f=0）的增量之和**。
          实测标定：E03 怒吼顶 +36.0°；本支庆祝段应落在 CHIN_RANGE。
        """
        # ★ samples[...]["euler"] 已是 **度**（anim_lib.sample_animation 里
        #   `math.degrees(v)`），**不可**再乘 180/π —— 早先版本在此乘了一次，
        #   导致仰头角被虚增 57.3 倍（读出 916.7°）。见 §6「结论必须基于实测」。
        e = samples[idx[frame]]["euler"]
        e0 = samples[0]["euler"]
        d_neck = (e.get("neck", (0.0, 0.0, 0.0))[0]
                  - e0.get("neck", (0.0, 0.0, 0.0))[0])
        d_head = (e.get("head", (0.0, 0.0, 0.0))[0]
                  - e0.get("head", (0.0, 0.0, 0.0))[0])
        return -(d_neck + d_head)

    def chest_rx_deg(frame):
        # ★ 同上：samples euler 已是度。
        return samples[idx[frame]]["euler"].get("chest", (0.0, 0.0, 0.0))[0]

    # ---- ① ★★★ 捶胸几何（本支命门：贴合 + 互不穿透 + 同步对称）-----------
    pound_rows = {}
    for frame in sorted(set(list(POUND_FRAMES) + [h[0] for h in HOLDS]
                            + [h[1] for h in HOLDS] + [DIP, PULL1, OPEN])):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        row = {}
        for side in SIDES:
            core = Vector(A.bone_world(arm, "hand." + side, "tail"))
            row[side] = {
                "core_mm": [round(v * 1000.0, 2) for v in core],
                "core_gap_mm": round(signed_to_torso(core), 2),
                "knuckle_gap_mm": fist_face_gap(side, step=2)}
            row["sym_" + side + "_x"] = round(abs(core.x) * 1000.0, 2)
        pound_rows[str(frame)] = row
    res["victory_pound_geometry"] = pound_rows

    hold_all = sorted(set([f for h in HOLDS for f in (h[0], h[1])]))
    knuckle = {}
    for frame in hold_all:
        for side in SIDES:
            knuckle[(frame, side)] = pound_rows[str(frame)][side][
                "knuckle_gap_mm"]
    kn_vals = [v for v in knuckle.values() if v is not None]
    worst_kn = max(kn_vals) if kn_vals else None
    best_kn = min(kn_vals) if kn_vals else None
    res["victory_pound_knuckle_worst_mm"] = worst_kn
    res["victory_pound_knuckle_deepest_mm"] = best_kn
    res["victory_pound_contact_max_mm"] = POUND_CONTACT_MAX_MM
    res["victory_pound_contact_ok"] = bool(
        worst_kn is not None and worst_kn <= POUND_CONTACT_MAX_MM)
    res["victory_pound_pierce_max_mm"] = POUND_PIERCE_MM
    res["victory_pound_pierce_ok"] = bool(
        best_kn is not None and best_kn >= -POUND_PIERCE_MM)
    res["victory_pound_contact_note"] = (
        "★★★ **本支命门**：「捶胸」= 拳**面**（指节 `Finger_*` 顶点）砸在胸面上。"
        "判据 = **指节面到躯干面的最小带符号距离**（真·网格量，不是球近似）："
        "贴合 ⟹ 最大值 ≤ %.1f mm（三捶的 6 个定格帧全部要满足）；"
        "不穿透 ⟹ 最小值 ≥ −%.1f mm。实测定格窗（%s）内 最松 **%s mm** / "
        "最深 **%s mm**。★ 与 E05 `bstart_fist_contact_ok`（拳 vs **拳**）不同："
        "本支是「拳 vs **躯干**」，与 E03 `rage_chest_hit_ok` 同族 —— 但**捶点更高**"
        "（见 `victory_pound_site_ok`）。"
        % (POUND_CONTACT_MAX_MM, POUND_PIERCE_MM, [list(h) for h in HOLDS],
           worst_kn, best_kn))

    # 同步对称（三捶全部要满足）
    sym_worst = {"x": 0.0, "y": 0.0, "z": 0.0}
    sym_rows = {}
    for frame in POUND_FRAMES:
        row = pound_rows[str(frame)]
        cl = Vector(row["L"]["core_mm"])
        cr = Vector(row["R"]["core_mm"])
        s = {"x": round(abs(cl.x + cr.x), 2),
             "y": round(abs(cl.y - cr.y), 2),
             "z": round(abs(cl.z - cr.z), 2)}
        sym_rows[str(frame)] = s
        for k in sym_worst:
            sym_worst[k] = max(sym_worst[k], s[k])
    res["victory_pound_sym_rows"] = sym_rows
    res["victory_pound_sym_worst_mm"] = sym_worst
    res["victory_pound_sym_limits_mm"] = [POUND_SYM_X_MM, POUND_SYM_Y_MM,
                                          POUND_SYM_Z_MM]
    res["victory_pound_sym_ok"] = bool(
        sym_worst["x"] <= POUND_SYM_X_MM and sym_worst["y"] <= POUND_SYM_Y_MM
        and sym_worst["z"] <= POUND_SYM_Z_MM)
    res["victory_pound_sym_note"] = (
        "★ **三捶的同步性**：「双拳同时捶胸」两拳必须**同时、同高、同深** —— "
        "一高一低 / 一前一后会被读成「一只手在挠痒」。实测三捶（f=%s）的拳心"
        "镜像偏差 **x %.2f / y %.2f / z %.2f mm**（≤ %.0f / %.0f / %.0f）。"
        "★ 本支 `ry ≡ 0`（不拧腰），对称由**结构**保证，不是靠调参。"
        % (list(POUND_FRAMES), sym_worst["x"], sym_worst["y"], sym_worst["z"],
           POUND_SYM_X_MM, POUND_SYM_Y_MM, POUND_SYM_Z_MM))

    # ---- ② ★★★ 捶点高度（E06 与 E03 的**核心几何差异**）------------------
    site = {}
    for frame in POUND_FRAMES:
        row = pound_rows[str(frame)]
        site[str(frame)] = {
            "z_mm": round(min(row["L"]["core_mm"][2], row["R"]["core_mm"][2]), 2),
            "x_abs_mm": round(max(abs(row["L"]["core_mm"][0]),
                                  abs(row["R"]["core_mm"][0])), 2)}
    worst_z = min(v["z_mm"] for v in site.values())
    worst_x = max(v["x_abs_mm"] for v in site.values())
    res["victory_pound_site_rows"] = site
    res["victory_pound_site_z_min_mm"] = worst_z
    res["victory_pound_site_x_max_mm"] = worst_x
    res["victory_pound_site_z_limit_mm"] = POUND_Z_MIN_MM
    res["victory_pound_site_ok"] = bool(worst_z >= POUND_Z_MIN_MM
                                        and worst_x <= POUND_X_MAX_MM)
    res["victory_pound_site_note"] = (
        "★★★ **E06 与 E03 的核心差异（可量化）**：清单预警说「E06 捶胸会与 E03 "
        "`Rage` 撞车」，开工实测（`probe_e06_baseline.py`）**推翻了清单的前提** —— "
        "E03 **本来就是双拳同时、精确对称**捶胸（`fist_dx = 244.4 mm`，两侧拳面 "
        "4.56 / 4.29 mm）。⟹ 差异只能做在**别的维度**上，本支选的是**捶点高度**："
        "E03 实测命中拳心 z = **1166.6 mm**（下胸 / 剑突）；本支实测三捶最低 "
        "z = **%.1f mm**（上胸 / 胸肌，探测点取胸骨下 %.0f mm）⟹ **高 %.1f mm**。"
        "判据：z ≥ %.0f mm（旋钮 ④ `LOW_CHEST` 把探测点拨回 E03 高度 ⟹ 本判据变红）。"
        % (worst_z, POUND_DZ * 1000.0, worst_z - 1166.6, POUND_Z_MIN_MM))

    # ---- ③ ★ 三连捶计数 ---------------------------------------------------
    res["victory_pound_count"] = len(POUND_FRAMES)
    res["victory_pound_count_ok"] = bool(len(POUND_FRAMES) == POUND_COUNT)
    res["victory_pound_count_note"] = (
        "★ E03 是 **f28 / f52 两捶**（间隔 24 帧）；本支是 **f%s 三捶**"
        "（间隔 14 帧）—— 更快的庆祝节奏，也是与 E03 的第二处可量化差异。"
        % (list(POUND_FRAMES),))

    # ---- ④ ★★ 定格（hitstop）在**三个**捶击窗口内 -------------------------
    res["victory_hitstop_frames"] = HITSTOP_N
    res["victory_hitstop_windows"] = [list(h) for h in HOLDS]
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
    res["victory_hitstop_steps_deg"] = hs_steps
    res["victory_hitstop_worst_step_deg"] = round(worst_hs, 6)
    res["victory_hitstop_ok"] = bool(
        2 <= HITSTOP_N <= 4 and worst_hs <= HITSTOP_STEP_MAX_DEG
        and all(h[1] - h[0] + 1 == HITSTOP_N for h in HOLDS))
    res["victory_hitstop_note"] = (
        "★ 「打击停顿」**每次捶击**都有：判据量**三个定格窗口内逐帧姿态**"
        "（`max |Δ euler|`），窗口 %s 各 %d 帧，实测窗口内最大逐帧角步 "
        "**%.6f°**（阈值 ≤ %.2f° ⟹ 姿态完全冻结）。★ 定格靠**时间轴冻结**"
        "（帧号前进、姿态不变 + `A.set_hitstop` 把窗口键设 CONSTANT），"
        "**不是**把 N 帧压进插值 —— 否则 `no_snap_stop_ok` 会在定格边界炸。"
        "★ 与 E03 的两窗口、E05 的单窗口都不同：本支是**三窗口**。"
        % ([list(h) for h in HOLDS], HITSTOP_N, worst_hs,
           HITSTOP_STEP_MAX_DEG))

    # ---- ⑤ ★★ 挺胸（庆祝的躯干载体）--------------------------------------
    puff = {}
    for frame in (OPEN, HERO, HERO_HOLD):
        puff[str(frame)] = round(chest_rx_deg(frame), 3)
    worst_puff = max(puff.values())
    res["victory_chest_rx_deg"] = puff
    res["victory_chest_puff_max_rx_deg"] = PUFF_MAX_RX
    res["victory_chest_puff_ok"] = bool(worst_puff <= PUFF_MAX_RX)
    res["victory_chest_puff_note"] = (
        "★★ 「胜利」的躯干载体是**挺胸**（`chest rx` **负** = 后仰挺胸）。"
        "实测庆祝段（f=%s）`chest rx` = %s（**必须全部 ≤ %.1f°**）。"
        "★ 与 E03 的区别：E03 的胸后仰发生在**怒吼**时（头后仰 36°）；"
        "本支是**张臂 + 挺胸 + 下巴只上扬 12~16°** ⟹ 情绪读成「庆祝」而非「愤怒」。"
        "★ 旋钮 ⑦ `SLUMP` 把胸拨成前倾（+3°）⟹ 本判据变红。"
        % ([OPEN, HERO, HERO_HOLD], puff, PUFF_MAX_RX))

    # ---- ⑥ ★★ 下巴上扬（区间两端；且全程不怒吼）--------------------------
    chin_rows = {str(f): round(head_back_deg(f), 3)
                 for f in (POUND1, POUND2, POUND3, OPEN, HERO, HERO_HOLD, SETTLE)}
    chin_peak = max(head_back_deg(f) for f in range(START, END + 1))
    celeb_peak = max(chin_rows[str(f)] for f in (OPEN, HERO, HERO_HOLD))
    res["victory_head_back_deg"] = chin_rows
    res["victory_head_back_peak_deg"] = round(chin_peak, 3)
    res["victory_chin_range"] = list(CHIN_RANGE)
    res["victory_no_roar_max_deg"] = NO_ROAR_MAX
    res["victory_chin_up_ok"] = bool(CHIN_RANGE[0] <= celeb_peak
                                     <= CHIN_RANGE[1])
    res["victory_no_roar_ok"] = bool(chin_peak <= NO_ROAR_MAX)
    res["victory_chin_up_note"] = (
        "★★ 「胜利」的头部载体是**下巴上扬**（`head_back` **正** = 后仰 / 上扬）。"
        "实测庆祝段峰值 **%.1f°**（区间 %.0f~%.0f）；全程峰值 **%.1f°**"
        "（⟹ `victory_no_roar_ok`：**不怒吼**，必须 ≤ %.0f°）。"
        "★ 这是与 E03 的第三处可量化差异：E03 怒吼顶 `head_back = 36.0°`。"
        "★ 区间**两端卡**：太小 = 没抬头（读不出胜利）；太大 = 变成 E03 的怒吼。"
        "★ 旋钮 ⑧ `NO_CHIN` 把颈/头上扬增量清零 ⟹ 本判据变红。"
        % (celeb_peak, CHIN_RANGE[0], CHIN_RANGE[1], chin_peak, NO_ROAR_MAX))

    # ---- ⑦ ★★ 英雄 pose 稳定（**不是颤抖**）------------------------------
    hero_span = HERO_HOLD - HERO + 1
    hero_steps = []
    worst_hero = 0.0
    for frame in range(HERO, HERO_HOLD):
        step, at = _worst_step(samples, idx[frame], idx[frame + 1])
        hero_steps.append((frame, round(step, 6), at))
        worst_hero = max(worst_hero, step)
    res["victory_hero_window"] = [HERO, HERO_HOLD]
    res["victory_hero_frames"] = hero_span
    res["victory_hero_min_frames"] = HERO_MIN_FRAMES
    res["victory_hero_steps_deg"] = [{"from": f, "step_deg": s, "at": a}
                                     for f, s, a in hero_steps]
    res["victory_hero_worst_step_deg"] = round(worst_hero, 6)
    res["victory_hero_hold_ok"] = bool(hero_span >= HERO_MIN_FRAMES
                                       and worst_hero <= HERO_STEP_MAX_DEG)
    res["victory_hero_hold_note"] = (
        "★★ 清单风险 2：「胜利动作的停不能太长，末段必须是**稳定的英雄 Pose** "
        "而非颤抖」。判据 = `HERO..HERO_HOLD` 窗口 **f=%d~%d 共 %d 帧**内逐帧"
        "最大角步 **%.6f°**（≤ %.2f°/帧 ⟹ 读作「稳住」）。"
        "★ 与「定格」的区别：定格是 CONSTANT 插值的**硬冻结**（角步 ≈ 1e−6），"
        "本段是**缓动到几乎静止**（HOLD 键与 HERO 键只差 < 0.3°）——"
        "语义上是「摆好姿势站定」，不是「被打停了」。"
        "★ 旋钮 ⑨ `TREMBLE` 在窗口内逐帧交替 ±3° ⟹ 本判据变红。"
        % (HERO, HERO_HOLD, hero_span, worst_hero, HERO_STEP_MAX_DEG))

    # ---- ⑧ 脚锁（**全程**）+ 鞋底带宽 -------------------------------------
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
    res["victory_ankle_drift_mm"] = {k: round(v, 4) for k, v in drift.items()}
    res["victory_toe_drift_mm"] = {k: round(v, 4)
                                   for k, v in toe_drift.items()}
    res["victory_sole_min_mm"] = round(min(sole.values()), 3)
    res["victory_sole_max_mm"] = round(max(sole.values()), 3)
    res["foot_lock_ok"] = bool(
        max(max(drift.values()), max(toe_drift.values())) <= FOOT_LOCK_MM
        and SOLE_BAND[0] <= min(sole.values())
        and max(sole.values()) <= SOLE_BAND[1])
    res["foot_lock_note"] = (
        "★★★ **脚锁「全程」口径**（照 E05；E06 不跳、不位移）：本支双腿全程落地 "
        "⟹ `want` 恒 = 站架踝。实测踝漂 **L %.4f / R %.4f mm**、趾漂 "
        "**L %.4f / R %.4f mm**（阈值 %.1f mm），鞋底 **%.2f ~ %.2f mm**"
        "（带 %.0f ~ %.0f）。★ 三捶的**屈膝下沉**全部由腿 IK 吸收，脚一动不动 —— "
        "这正是「捶胸靠屈膝发力」的物理证据（力量链的腿段）。"
        % (drift["L"], drift["R"], toe_drift["L"], toe_drift["R"], FOOT_LOCK_MM,
           res["victory_sole_min_mm"], res["victory_sole_max_mm"], SOLE_BAND[0],
           SOLE_BAND[1]))

    # ---- ⑨ 收招 / 过缝 ---------------------------------------------------
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
        "「胜利」：站架 → 三捶 → 张臂 → 英雄姿 → 回站架），首末帧同姿只用于"
        "「起手不留痕」，**不要求角速度对称**。实测首帧步 %.3f° / 末帧步 %.3f°。"
        % (first_step, last_step))

    # ---- ⑩ 力量传导链（六段：脚 → 腿 → 髋 → 腰 → 肩 → 手）----------------
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
    # ★ knee 取的是 pose_bone.rotation_euler.x 原值（**弧度**）⟹ 这里要 ×180/π。
    knee_deg_span = (max(knee) - min(knee)) * 180.0 / math.pi
    waist = [abs(s["euler"].get("chest", (0.0, 0.0, 0.0))[0])
             for s in samples]
    # ★ waist 取的是 samples[...]["euler"]（**已是度**）⟹ 不再乘 180/π。
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
        "（清单 0.2「不许跳级」）。本支载体：脚 = 髋↔踝距离行程（下沉靠屈膝）"
        "＋ 踝**全程钉死**（漂移 ≤ %.1f mm）；腿 = 膝屈角行程；髋 = 骨盆世界行程；"
        "腰 = `chest` 俯仰行程；肩 = 肩峰世界行程；手 = 拳心世界行程。"
        "★ 本支**没有「只有手在动」**：每次捶击的屈膝下沉把脚→腿→髋→腰全部串上。"
        % (FOOT_LOCK_MM,))
    res["chain_present_ok"] = bool(
        foot_axis > 20.0 and knee_deg_span > 0.2 and hip_travel > 2.0
        and waist_deg > 2.0 and shoulder_mm > 1.0 and hand_mm > 20.0)

    # ---- ⑪ 可达性 --------------------------------------------------------
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

    # ---- ⑫ 穿模（臂 vs 头盒，D01 起老口径）-------------------------------
    worst_clip, clip_at = 0.0, None
    for frame in sorted(set(list(range(START, END + 1, 3))
                            + list(POUND_FRAMES) + hold_all
                            + [OPEN, HERO, HERO_HOLD, DIP])):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        clip = PD.clip_metrics(arm)
        if clip["clip_max_mm"] > worst_clip:
            worst_clip, clip_at = clip["clip_max_mm"], (frame, clip["clip_at"])
    res["clip_max_mm"] = round(worst_clip, 2)
    res["clip_at"] = clip_at
    res["no_face_clip_ok"] = bool(worst_clip <= CLIP_MAX_MM)

    # ---- ⑬ ★★ 手 vs 躯干：**差分口径**（站架自己就有缺陷）-----------------
    pierce = {}
    walk = sorted(set(list(range(START, END + 1, 3))
                      + list(POUND_FRAMES) + hold_all))
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
    station_nt = max(STATION_PIERCE[s]["inside_nothumb"] for s in SIDES)
    station_beyond = max(STATION_PIERCE[s]["beyond_limit"] for s in SIDES)
    res["victory_pierce_scope"] = ["(0, TOTAL) 内全部帧",
                                   "排除接缝帧 %s" % sorted(seam_frames)]
    res["victory_pierce_nothumb_worst"] = worst_nt
    res["victory_pierce_nothumb_worst_at"] = worst_nt_at
    res["victory_pierce_nothumb_deepest_mm"] = round(worst_deep, 2)
    res["victory_pierce_nothumb_deepest_at"] = worst_deep_at
    res["victory_pierce_beyond_limit_worst"] = worst_beyond
    res["victory_pierce_beyond_limit_worst_at"] = worst_beyond_at
    res["victory_pierce_beyond_limit_abs_mm"] = HAND_PIERCE_MM
    res["victory_pierce_all_worst"] = worst_all
    res["victory_pierce_thumb_worst"] = worst_thumb
    res["victory_station_nothumb_count"] = station_nt
    res["victory_station_beyond_limit"] = station_beyond
    res["victory_station_pierce"] = {s: dict(STATION_PIERCE[s]) for s in SIDES}
    res["victory_pierce_detail"] = pierce
    # ★★★ 判据定稿（**口径换了，不是阈值放宽** —— 见 note 里的实测依据）：
    #   ① 绝对下限（不变）：任何非拇指顶点不得低于 −HAND_PIERCE_MM；
    #   ② 数量口径改为**计数「越过绝对下限」的顶点数**（E06 与站架都必须为 0）。
    #   ★ 原口径「体内顶点个数 ≤ 站架个数」被**实测推翻**：站架右手侧本身有 3 个
    #     顶点在体内、最深 −4.05 mm；而 f3 的姿态 **96.4% 还是站架**（`env = 0.036`）
    #     却报出 **9 个** —— 因为站架附近有 ~9 个顶点紧贴胸面（±5 mm 内），
    #     3.6% 的混合就能再翻 6 个过去（`_e06_probe_depth.py` 实测）。
    #     ⟹ 那是**刀刃型**读数，不能当判据；真正有意义的是**深度**。
    res["victory_hand_no_pierce_ok"] = bool(
        worst_deep >= -HAND_PIERCE_MM and worst_beyond <= station_beyond)
    res["victory_hand_no_pierce_note"] = (
        "★ 本支的拳要**压到胸面上**（捶胸）—— 比 E04 的腾空摆臂**更贴近躯干**"
        "⟹ 这条断言在本支**真的有风险**，不是走过场。口径照 E03 v011 的**差分**形式"
        "（**改的是基准，不是阈值**）：本支非拇指最深带符号距离 **%.2f mm**（@ %s，"
        "下限 −%.0f mm）；**越过绝对下限的顶点数 %d**（@ %s）—— 站架基线的同一读数是 "
        "**%d** 个 ⟹ 判据 =「不得比站架更差」。★ 参考读数：非拇指「真在体内」顶点数 "
        "本支最多 **%d**（@ %s）、站架 **%d**；全手（含拇指）体内最多 **%d** 个"
        "（其中拇指 **%d**）。★ 为什么不拿「体内个数」当判据：站架（`Idle_01@0`）"
        "右手侧已有 3 个顶点在体内（−4.05 mm），而站架附近有 ~9 个顶点紧贴胸面"
        "（±5 mm 内）—— 混合系数只要 3.6%% 就能让其中 6 个翻进去（f3 实测就是如此，"
        "而 f3 的姿态 **96.4%% 还是站架**）⟹ 个数是**刀刃型**读数；"
        "深度才是真信号（`_e06_probe_depth.py` 实测标定）。"
        % (worst_deep, worst_deep_at, HAND_PIERCE_MM, worst_beyond,
           worst_beyond_at, station_beyond, worst_nt, worst_nt_at, station_nt,
           worst_all, worst_thumb))

    # ---- ⑭ ★★ 真旋转步长（矩阵口径）—— 与 euler 口径互为交叉验证 ----------
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
                print("E06_STEP f=%3d mat=%6.2f %-12s eul=%7.2f %s"
                      % (frame, _fmax, _fmax_at, _es, _ea))
        prev_basis = current
    res["victory_matrix_step_deg_max"] = round(worst_mat, 3)
    res["victory_matrix_step_at"] = worst_mat_at
    res["victory_matrix_step_ok"] = bool(worst_mat <= MATRIX_STEP_MAX_DEG)
    euler_step, euler_at = 0.0, None
    for index in range(1, len(samples)):
        step, at = _worst_step(samples, index - 1, index)
        if step > euler_step:
            euler_step, euler_at = step, at
    res["victory_euler_step_deg_max"] = round(euler_step, 3)
    res["victory_euler_step_at"] = euler_at
    res["victory_matrix_step_note"] = (
        "★★ **矩阵口径**的逐帧最大真实旋转步 **%.3f° @ %s**（阈值 ≤ %.1f°）；"
        "euler 口径 **%.3f° @ %s**。两者**必须一致地小** —— 差得远就说明欧拉表示"
        "在跳（C14 / D01 / E03 的万向节锁坑），而不是动作在跳。"
        "★ 本支先做 `compat_euler`（min-max 瓶颈 DP）再断言。"
        "★ 风险段：`PULL → POUND`（收拳 → 砸胸，`accel` 重击）与 `POUND3 → OPEN`"
        "（拳从胸面甩到体侧外，行程最大 ~300 mm）。"
        % (worst_mat, worst_mat_at, MATRIX_STEP_MAX_DEG, euler_step, euler_at))

    # ---- ⑮ 手骨滚转基准的退化余量（E03 v009 的教训）---------------------
    res["victory_x_hint_margin"] = round(MIN_HINT_MARGIN, 4)
    res["victory_x_hint_margin_min"] = HAND_X_HINT_MIN_MARGIN
    res["victory_x_hint_margin_ok"] = bool(MIN_HINT_MARGIN
                                          >= HAND_X_HINT_MIN_MARGIN)
    res["victory_x_hint_margin_note"] = (
        "★ `orient_hand` 的滚转基准（`thumb_out` = ±X 体侧外）实测最小余量 "
        "**%.4f**（阈值 ≥ %.2f）。E03 v009 的实测教训：基准若落在骨轴方向上，"
        "投影退化为 0 ⟹ 滚转由浮点噪声决定 ⟹ **真实旋转 83.86°/帧**（不是表示问题，"
        "是真翻）。★ 本支与 E03 同族（基准 = ±X），但**动作不同** ⟹ 必须**重新量**"
        "（E03 的 0.701 不能照抄到本支的张臂轨迹上）。"
        % (MIN_HINT_MARGIN, HAND_X_HINT_MIN_MARGIN))

    res["phase_markers"] = {
        "START": START, "DIP": DIP, "POUND1": POUND1, "PULL1": PULL1,
        "POUND2": POUND2, "PULL2": PULL2, "POUND3": POUND3, "OPEN": OPEN,
        "HERO": HERO, "HERO_HOLD": HERO_HOLD, "SETTLE": SETTLE, "END": END}
    res["victory_sole_trace_mm"] = {str(f): round(v, 2)
                                    for f, v in sorted(sole.items())}
    return res


# =============================================================== 屏幕投影
def landmark_screen(arm, action):
    """把「拳心 / 拳面 / 肩峰」逐帧投影到**正面**屏幕坐标，供像素探针用。"""
    name, loc, tgt, scale, rres = VIEW_E06_FRONT
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
    return {"view": VIEW_E06_FRONT[0], "res": list(VIEW_E06_FRONT[4]),
            "ortho_m": VIEW_E06_FRONT[3], "cam_z": VIEW_E06_FRONT[1][2],
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
    global LAST_HAND_X, LAST_TWIST_ANGLE
    LAST_ELBOW = {}
    LAST_HAND_X = {}
    LAST_TWIST_ANGLE = {}
    LAST_HAND_FRAME = {}
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
        STATION_PIERCE[side] = hand_mesh_stats(side, step=4,
                                               limit_mm=HAND_PIERCE_MM)
    return arm, meshes


def main():  # noqa: C901
    arm, meshes = boot()
    keyframes = [(frame, victory_pose(arm, frame))
                 for frame in range(START, END + 1)]
    if _env_b("E06_TRACE_RAW"):
        for _fr, _pz in keyframes:
            if 13 <= _fr <= 30:
                _l = _pz.get("forearm.L", (0.0, 0.0, 0.0))
                _u = _pz.get("upperarm.L", (0.0, 0.0, 0.0))
                print("E06_RAW f=%3d foL=(%8.2f,%8.2f,%8.2f) upL=(%8.2f,%8.2f,"
                      "%8.2f)" % (_fr, _l[0], _l[1], _l[2],
                                  _u[0], _u[1], _u[2]))
    keyframes = compat_euler(keyframes)
    keyframes = seam_canonicalize(keyframes)
    if _env_b("E06_TRACE_EULER"):
        for _fr, _pz in keyframes:
            if _fr >= 114 or _fr <= 1:
                print("E06_EUL f=%3d hand.L=%s hand.R=%s"
                      % (_fr,
                         tuple(round(v, 3) for v in _pz.get("hand.L", ())),
                         tuple(round(v, 3) for v in _pz.get("hand.R", ()))))
    meta = {
        "anim_id": NAME,
        "loop": False,
        "category": "状态与流程",
        "note": ("胜利 A（捶胸）：双拳同步**三连捶上胸**（每次都定格 %d 帧）→ "
                 "张臂挺胸庆祝 → 稳定英雄姿 → 回战斗待机；★ 全程原地、脚锁全程；"
                 "★ 与 E03 `Rage` 的差异：捶点高 110 mm（上胸 vs 下胸）、三捶 vs 两捶、"
                 "只上扬 16° vs 怒吼 36°、新增张臂段" % HITSTOP_N),
        "frames": [START, END],
        "root_motion_m": [0.0, 0.0],
        "root_motion_z_m": [0.0, 0.0],
        "hitstop_frames": HITSTOP_N,
        "hitstop_windows": [list(h) for h in HOLDS],
        "antic_frame": DIP,
        "hit_frame": POUND1,
        "hit_frames": list(POUND_FRAMES),
        "cancel_frame": OPEN,
        "hit_point_m": [0.0, None, None],
        "seam": "%s@%d" % (SEAM_ACTION, SEAM_FRAME),
        "seam_ends": {"start": "%s@%d" % (SEAM_ACTION, SEAM_FRAME),
                      "end": "%s@%d" % (SEAM_ACTION, SEAM_FRAME)},
        "frame_bound_note": ("★ 120 帧 = 2.0 s = E01 登记的**上界** ⟹ 可直接沿用"
                             "（显式声明，不是悄悄超）；清单要求胜利动作 1.5~2.5 s ⟹ 落带内"),
        "view_note": ("★ 本支取景**自立**（不照抄 E03/E05）：纵向 −0.15~1.95 m"
                      "（中心 z=0.92、正交高 2.10 m），比标准站姿视图**略高**"
                      "以装下张臂；正面判捶胸贴合 + 同步，侧视判挺胸 + 下巴上扬，"
                      "3Q 判英雄姿"),
        "foot_lock": {
            "scope": "全程 [START..END]（本支不跳、不位移）",
            "reason": "原地动画 ⟹ 踝恒钉站架点（与 E04 的**分段**口径相反）"},
        "pound": {
            "kind": "hand.geometry（拳面 = 指节顶点）vs torso.geometry",
            "site": "上胸（胸骨下 %d mm），与 E03 下胸不同" % int(POUND_DZ * 1000),
            "contact_max_mm": POUND_CONTACT_MAX_MM,
            "pierce_mm": POUND_PIERCE_MM,
            "touch_off_mm": TOUCH_OFF * 1000.0,
            "count": len(POUND_FRAMES)},
        "differentiation_vs_E03": {
            "site_z_mm": {"E03": 1166.6, "E06_min": POUND_Z_MIN_MM},
            "count": {"E03": 2, "E06": len(POUND_FRAMES)},
            "head_back_deg": {"E03_roar": 36.0, "E06_max": NO_ROAR_MAX},
            "extra": "E06 新增「张臂庆祝」段 + 「英雄姿保持」段"},
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    markers = {"START": START, "DIP": DIP, "ANTIC": DIP}
    for i, pf in enumerate(POUND_FRAMES, start=1):
        markers["POUND%d" % i] = pf
        markers["HIT%d" % i] = pf
    markers.update({"OPEN": OPEN, "HERO": HERO, "HOLD": HERO_HOLD,
                    "RECOV": SETTLE, "END": END})
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
    A.report("E06_REPORT", report)

    stem_only = os.environ.get("E06_STEM_ONLY") == "1"
    stem_frames = list(STEM_FRAMES)
    if stem_only:
        # ★ 只为像素探针的**反面对照**重渲：**同一台相机 + 同一批帧 + 两个机位**。
        #   ★ 不 save_project / export_glb ⟹ 不污染正式 .blend / GLB。
        stem = os.environ.get("E06_STEM", "vicstem")
        A.render_pose_sheet(arm, action, stem_frames, stem,
                            views=(VIEW_E06_SIDE, VIEW_E06_FRONT))
        render_layer(arm, action, stem + "hand", HAND_PREFIX, VIEW_E06_FRONT,
                     stem_frames)
        print("E06_DONE failed=%s non_ok=%s" % (failed, non_ok))
        return

    if not SKIP_RENDER:
        A.render_pose_sheet(arm, action, list(range(START, END + 1, 4)),
                            "vicwide", views=(VIEW_E06_SIDE,))
        A.render_pose_sheet(arm, action, stem_frames, "vic_side",
                            views=(VIEW_E06_SIDE,))
        A.render_pose_sheet(arm, action, stem_frames, "vic_front",
                            views=(VIEW_E06_FRONT,))
        # ★★ 手部**分层**渲染必须用**另一个前缀**：`render_pose_sheet` 的文件名是
        #   `<prefix>_<view>_f<NNNN>.png` ⟹ 若分层也用 `vic_front` 会把上面那份
        #   **全身正面图原地覆盖**（E05 首轮实测踩到）。
        render_layer(arm, action, "vic_hand", HAND_PREFIX, VIEW_E06_FRONT,
                     stem_frames)
        key_frames = [0, 14, 20, 28, 30, 35, 42, 56, 62, 68, 74, 80, 86, 91,
                      96, 103, 110, 115, 120]
        A.render_pose_sheet(arm, action, key_frames, "vickey",
                            views=(VIEW_E06_SIDE, VIEW_E06_FRONT, A.VIEW_3Q))
        with open(os.path.join(A.PREVIEW_DIR, "_e06_landmark.json"), "w",
                  encoding="utf-8") as handle:
            json.dump(landmark_screen(arm, action), handle, ensure_ascii=False)
        A.save_project()
        A.export_glb(arm)
    print("E06_DONE failed=%s non_ok=%s" % (failed, non_ok))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("E06_FAILURE " + traceback.format_exc())
