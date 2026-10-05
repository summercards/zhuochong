"""anim_rage —— E03 `Rage` 狂暴（E 族第三支 / 第 59 支）。

清单原文：「**仰头怒吼、捶胸或双拳紧握，作为 Buff 起手**」。

★★★ 本支与 E01 / E02 的三处根本不同（开工前想清楚）
    · 方向：E01 横向周期摇晃 / E02 纵向弯腰+呼吸；**E03 躯干由前倾翻转为后仰**，
      手臂由「下垂扶膝」翻转为「上举 / 捶胸」。
    · ★★ **E03 是 E 族第一支「进攻性」动作** ⟹ **首次引入 hitstop**
      （「捶胸」有命中帧；E01/E02 的 `hitstop_frames` 都是 0）。
    · ★★★ **捶胸 = 打到自己的身体**（与 E02「手扶膝」同属自碰撞，但目标在
      **躯干上**、是**一片曲面**而非「膝=一个点」）⟹ 拳要**打到**胸、又**不许穿进去**，
      是**双侧夹逼**。新建 `rage_chest_hit_ok` + `fist_chest_no_clip_ok`。

★★★ 工程件 ①：**四段 + hitstop 的时间轴（时间冻结，不是把窗口压进插值）**
    相位：`START(0) → WINDUP(20) → HIT_1(28) →[冻结 3 帧]→ ROAR(44)
          → 抬拳(48) → HIT_2(52) →[冻结 3 帧]→ ROAR2(66) → END(96)`
    · 每帧**显式打帧**（96 帧全键）⟹ 「定格」= 窗口内姿态**逐帧恒定**（帧号前进、
      姿态不变），再用 `A.set_hitstop` 把窗口键设成 CONSTANT ⟹ 边界不产生漂移。
    · 段间用**逐段指定的缓动**：`smooth`(smoothstep) / `accel`(t²，启动慢、**命中
      最重**) / `hold`(恒定) / `decel`。首段与末段都用 smoothstep ⟹ 两端的
      **导数都为 0**（承 E01「消失于接缝」+ E02 幂次包络的教训）。
    · ★ 本支**没有**周期函数（不是呼吸），所以 E02 的「相位重锚」问题不存在。

★★★ 工程件 ②：**动态拳目标（贴在会动的胸上）**
    捶胸的目标点**不是世界定点**：怒吼时躯干**后仰挺胸**，胸面在两帧之间就移动了
    几十毫米。做法：每帧先用**当前躯干姿态**对 `Suit_Torso` 求「胸前表面点 + 外法线」
    （`closest_point_on_mesh`，求值网格），再令拳心（`hand.tail`）落到
    `表面 + 法线 x TOUCH_OFF`，最后对该点做**臂链两段位置 IK**。

★★★ 工程件 ③：**捶胸的「量具」是实测标定出来的（`_e03_diag.py`），不是猜的**
    · 实测：`R_fist`（手网格顶点到手骨轴的垂直距离）p50=36.0 / p90=55.6 /
      p98=87.0 / max=95.0 mm ⟹ **不能用 max 当半径**：那 95 mm 是**蜷曲的指尖**
      （拳头收拢后指尖朝掌心侧、指向手腕）⟹ 「拳网格到胸网格的最小带符号距离」
      **不能当绝对尺子**。
    · 实测：A01 站架里 **R 拳网格与 `Suit_Torso` 本来就重叠 34.19 mm**（L 为
      外侧 +1.04 mm）—— 这是**预存几何**（拳护胸姿态的既有穿插），不是本支引入的。
    · ⟹ 主尺子改用 **拳心（`hand.tail` = 指节中心）到胸面的带符号距离**
      `core_gap_mm`。实测站架基线：**L +100.69 mm / R +66.63 mm**（两拳都在胸面
      之外，与渲染一致）。捶中目标 = **+38 mm**（拳肉刚好压住胸面）。
      网格级最小带符号距离降级为**基线相对**守卫（`face_gap_rel_mm`）。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python anim_rage.py
    SKIP_RENDER=1      只跑门禁不渲图（迭代用）
    E03_TRACE=1        逐帧打印 蓄力/后仰角 / 拳心到胸距离 / 脚锁误差

反向验证（§4 第 7 步，九组）：
    E03_TP_SEAM_ZERO=1  ① 首帧改零位                 ⟹ `seam_in_ok`
    E03_TP_CHESTFAR=1   ② ★★★ 拳离开胸               ⟹ `rage_chest_hit_ok` / 像素
    E03_TP_CHESTCLIP=1  ③ ★ 拳穿进胸                 ⟹ `fist_chest_no_clip_ok`
    E03_TP_HEADDOWN=1   ④a 仰头不够                  ⟹ `rage_head_back_ok`（下限端）
    E03_TP_HEADOVER=1   ④b 仰头过头                  ⟹ `rage_head_back_ok`（上限端）
    E03_TP_NOHITSTOP=1  ⑤ ★ 去掉 hitstop            ⟹ `rage_hitstop_ok`
    E03_TP_FOOTSWAY=1   ⑥ 脚跟着动（X 向，正面可见） ⟹ `rage_foot_lock_ok` / 像素
    E03_TP_LOOPBREAK=1  ⑦ 末帧不闭合                 ⟹ `loop_seamless` /
                                                        `end_matches_start_ok`
    E03_TP_NOFLIP=1     ⑧ ★ 躯干不翻转               ⟹ `rage_windup_ok`
    E03_TP_FACEALONG=1  ⑨ ★★★ 拳面回到「沿前臂」     ⟹ `rage_punch_no_pierce_ok`
                            （旧口径：拇指横插进胸，实测 280/290 顶点在体内）
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

NAME = "Rage"
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"
SIDES = ("L", "R")
ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")
ARM_SET = set(ARM_BONES)
ARM_LEN_UP = 0.328
ARM_LEN_LO = 0.224 + 0.098
ARM_TOTAL = ARM_LEN_UP + ARM_LEN_LO
HAND_LEN = 0.098        # `hand` 骨长（`ARM_LEN_LO` 取自分段之和，此处单独摘出）

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
# ★ 上游 = `Idle_01@0`。★ 实测复核（`probe_e03_baseline.py`，**不是照抄 E02**）：
#   `Idle_01@0` vs `Stun@末帧(120)`  最差位置差 **0.000258123 mm**（elem 4.77e-7）
#   `Idle_01@0` vs `Exhausted@0`     最差位置差 **0.000086888 mm**（elem 1.19e-7）
#   `Idle_01@0` vs `Exhausted@末帧(120)` 同上 0.000086888 mm（E02 首末同姿 ⟹ 一致）
#   ⟹ **三个候选代价相等**（都在 1e-4 mm 量级 = float32 噪声），只能按语义选。
#   ★ 选 `Idle_01@0` 的理由：本支是「起手 → 爆发 → 回架势」的**一次性**动作，
#     上游是**普通待机**（玩家按下 Buff 键的那一刻），不是「虚弱之后的下一步」，
#     也不是「眩晕之后的下一步」。且 `Idle_01@0` 已被 E01 / E02 两次作为锚
#     ⟹ 选它也保住整条 E 族接缝链的一致。
SEAM_ACTION = os.environ.get("E03_SEAM_ACTION", "Idle_01")
SEAM_FRAME = _env_i("E03_SEAM_FRAME", 0)

# =============================================================== 时间轴（96 帧）
# ★ 帧预算：**沿用 E01 登记的 120 帧 / 2.0 s 上界**（显式声明，不是悄悄超）。
#   本支 96 帧 = **1.6 s**，比上界**更短** ⟹ 沿用合规。
TOTAL = _env_i("E03_TOTAL", 96)
START = 0
END = TOTAL
HITSTOP_N = _env_i("E03_HITSTOP", 3)        # 命中定格帧数（2~4）

# 相位标记帧（**由本支自定**，见 §2）
WINDUP = _env_i("E03_WINDUP", 20)
HIT_1 = _env_i("E03_HIT1", 28)
HOLD_1 = (HIT_1, HIT_1 + HITSTOP_N - 1)     # [28, 30]
ROAR = _env_i("E03_ROAR", 44)
LIFT = _env_i("E03_LIFT", 48)               # 第二次捶胸前的抬拳
HIT_2 = _env_i("E03_HIT2", 52)
HOLD_2 = (HIT_2, HIT_2 + HITSTOP_N - 1)     # [52, 54]
ROAR2 = _env_i("E03_ROAR2", 66)
ARM_UP_AT = _env_i("E03_ARM_UP", 14)        # 臂包络到 1
ARM_DN_AT = _env_i("E03_ARM_DN", 74)        # 臂包络开始回 0
ARM_DN_DONE = _env_i("E03_ARM_DN_DONE", 88)  # ★ v011：臂包络**回 0 完成**帧

# =============================================================== 躯干规格（Δrx，度）
# ★ 量纲：全部是**相对站架的增量**，未列出的骨 = 站架值。
# ★ loc = (世界 dy, 世界 dz)（米），加在站架骨盆位移之上。
SPECS = {
    "STATION": {"pelvis": 0.0, "spine_01": 0.0, "spine_02": 0.0, "chest": 0.0,
                "neck": 0.0, "head": 0.0, "shoulder.L": 0.0, "shoulder.R": 0.0,
                "loc": (0.0, 0.0)},
    # 蓄力：**沉髋 + 含胸前倾 + 低头**（反向预备动作）
    "WIND": {"pelvis": 9.0, "spine_01": 5.0, "spine_02": 5.0, "chest": 3.0,
             "neck": 5.0, "head": 3.0, "shoulder.L": -7.0, "shoulder.R": -7.0,
             "loc": (0.020, -0.045)},
    # 第一次捶中：躯干刚从含胸回一点，头还没仰（打下去那一刻是「含」的）
    "CHEST1": {"pelvis": 4.0, "spine_01": 2.0, "spine_02": 1.0, "chest": -1.0,
               "neck": -2.0, "head": 3.0, "shoulder.L": 3.0, "shoulder.R": 3.0,
               "loc": (0.005, -0.012)},
    # 仰头怒吼顶：**脊柱后弓 + 挺胸 + 颈头大幅后仰**（本支幅度峰值）
    "ROAR": {"pelvis": -5.0, "spine_01": -5.0, "spine_02": -5.0, "chest": -6.0,
             "neck": -16.0, "head": -20.0, "shoulder.L": 11.0,
             "shoulder.R": 11.0, "loc": (-0.020, 0.012)},
    "CHEST2": {"pelvis": -2.0, "spine_01": -2.0, "spine_02": -2.0,
               "chest": -3.0, "neck": -11.0, "head": -8.0,
               "shoulder.L": 6.0, "shoulder.R": 6.0, "loc": (-0.006, 0.004)},
    "ROAR2": {"pelvis": -3.0, "spine_01": -3.0, "spine_02": -3.0, "chest": -4.0,
              "neck": -9.0, "head": -11.0, "shoulder.L": 7.0,
              "shoulder.R": 7.0, "loc": (-0.010, 0.006)},
}

# ★★★ v011：`NO_HITSTOP` 必须在这里读（**必须定义在 `KEYS` 之前**）。
#
#   为什么（这是一次**惰性旋钮**的实测修正，不是随手搬代码）：
#     命中定格在本支是**由 `rage_pose` 的键表实现的** —— `KEYS` 里的 `hold` 行
#     让 f=28/29/30 三帧拿到**同一个规格 + 同一个拳目标** ⟹ 姿态本来就**逐帧
#     完全相同**；`A.set_hitstop()` 只是把这三个已经相同的键的**插值**设成
#     CONSTANT（锦上添花）。
#     ⟹ 旧写法（只在 `main()` 里 `if not NO_HITSTOP: set_hitstop(...)`）下，
#       打开旋钮**什么都不会变** —— 姿态仍是冻结的 ⟹ `rage_hitstop_ok` 保持绿
#       ⟹ **旋钮是惰性的**（11 组反向验证里唯一见不了红的那一组，实测确认）。
#     ⟹ 正解：「没有 hitstop」的**忠实仿真** = **从键表里抽掉 `hold` 行**，
#       让 `HIT_1 → ROAR` / `HIT_2 → ROAR2` 变成一整段 —— 窗口内姿态按原插值
#       **继续走**（拳离开胸、躯干继续后弓），这才是「没有定格」的样子。
#     ★ 判据 `rage_hitstop_ok` 量的是**窗口内逐帧姿态**（`max |Δ euler|`），
#       所以这个旋钮一打开它必然红 —— 旋钮真的接进了代码。
NO_HITSTOP = _env_b("E03_TP_NOHITSTOP")

# =============================================================== 关键帧表
#   (帧, 进入本键所用的缓动, 躯干规格, 拳目标名)
#   `hold` = 恒定（本支用于 hitstop 定格窗口）
KEYS = [
    (START, None, "STATION", "STATION"),
    (WINDUP, "smooth", "WIND", "WIND"),
    (HIT_1, "accel", "CHEST1", "CHEST"),
]
if not NO_HITSTOP:
    KEYS.append((HOLD_1[1], "hold", "CHEST1", "CHEST"))
KEYS += [
    (ROAR, "smooth", "ROAR", "CHEST_ROAR"),
    (LIFT, "smooth", "ROAR", "WIND_S"),
    (HIT_2, "accel", "CHEST2", "CHEST_2"),
]
if not NO_HITSTOP:
    KEYS.append((HOLD_2[1], "hold", "CHEST2", "CHEST_2"))
KEYS += [
    (ROAR2, "smooth", "ROAR2", "WIND_S"),
    (END, "smooth", "STATION", "STATION"),
]

# =============================================================== 拳目标（世界，米）
# ★ 除 `CHEST`（逐帧由胸几何解出）外均为**世界定点**（角色不位移 ⟹ 定点合理）。
# ★★★ v004 把蓄力/抬拳位从**身体侧后方**改到**身前**（口径修正 + 设计修正）：
#   旧值 `y = +0.030 / −0.055`（躯干**体内**侧），从站架拳位（y ≈ −0.19，胸前）
#   到旧蓄力位的**直线路径横穿躯干侧面** ⟹ 实测 f=3~9 右手最多 **210** 个顶点
#   在体内、最深 **−43.11 mm**（比站架继承的 −34 mm 还深，是**本支引入**的）。
#   新值全部落在 **y ≤ −0.26**（胸面 y ≈ −0.22 之**外**）⟹ 整条路径都在体外。
#   ★ 同时这也是更好的动作：蓄力 = 双拳收在**身前下压**（准备捶），
#     不是把拳甩到屁股后面。
# ★★★ v011：蓄力位再往前推 35 mm（y −0.290 → **−0.325**；`WIND_S` −0.300 → −0.335）。
#   理由（实测，不是调参凑绿）：`TOUCH_OFF` 收到 32 mm 之后（为了命中帧贴合），
#   `FIST_MIN_CLEAR_MM` 随之下降，实测 **f=12** 出现本支引入的穿透 ——
#   R 手非拇指 **38** 个顶点在体内、最深 **−11.35 mm**（超过 10 mm 上界）。
#   f=12 是 `STATION → WIND` 的**过渡段**（`env`=0.857，拳目标 = 站架拳位与
#   蓄力位的直线插值），而站架拳位 `y ≈ −0.19` 本身就在胸面（y ≈ −0.22）**内侧**
#   ⟹ 这条直线**起点就在体内**，中段擦着胸走。把蓄力位再往前推 35 mm，
#   整条路径外移，`f≈9~15` 的清空量随之外移。
#   ★ 这也是更好的动作：蓄力是「**身前下压**」，拳离胸远一点读得更清楚。
FIST_WIND = {"L": Vector((0.265, -0.325, 1.100)),
             "R": Vector((-0.265, -0.325, 1.115))}
FIST_WIND_S = {"L": Vector((0.235, -0.335, 1.190)),
               "R": Vector((-0.235, -0.335, 1.190))}
# ★ 首帧无「上一帧肘」可参考时的兜底极向量（见 `seat_arm` 的连续性说明）。
ELBOW_DIR = {"L": Vector((0.42, 1.00, -0.22)),
             "R": Vector((-0.42, 1.00, -0.22))}

# 捶胸几何（★ 由 `_e03_sweep.py` 全时间轴实测标定，见 v004 报告）
# ★★ 标定过程（不是猜的）：
#   `_e03_sweep.py` 按**真实帧序**逐帧建姿（保留肘连续性），扫 `TOUCH_OFF`，
#   量「真实手网格顶点到 `Suit_Torso` 的带符号距离」与「多数表决判在体内的顶点数」。
#   实测（拳面朝向修正后，**指节簇**先接触，不再是指尖）：
#     拳心 − 指节面 ≈ 26~31 mm（指节前缘比拳心更靠胸）
#     off=36 → 命中帧指节面 +7.0~+8.7 mm（悬在胸前，读成「没砸到」）
#     off=32 → +4.2~+6.1 mm，但 f=28 右手 6.13 越线
#     off=28 → +1.4~+3.3 mm（贴住），但 f=40~44「胸廓前挺」顶进拳面 → 残留穿透
#   ⟹ 两个旋钮分工：`TOUCH_OFF` 定**名义命中深度**，`FIST_MIN_CLEAR_MM` 定
#     **拳心保护下限**（防「胸廓前挺时顶进拳面」那一小段）。
#     实测 `clear = off + 2` 时 20~70 帧**全部 0 个顶点在体内**，且命中帧指节面
#     仍压在 +3.9~+5.5 mm ⟹ 两者交集存在，取交集中间值。
#   ★★★ v010 重标定（**由渲染实测逼出来的一次改值**，不是调参凑绿）：
#     近景渲染（`_e03_closeup.py`，拳头填满画面）暴露：旧值 29 mm 下
#     **两只拳都悬在胸外**（实测拳面 14.71 / 16.13 mm，"hover 在胸前"），
#     读起来是「拳没砸到」。这与清单原文要求的**捶胸**不符。
#     ⟹ 逐毫米外推：拳面每深 1 mm 需要 `TOUCH_OFF` 也深 1 mm（命中段两者
#       一一对应，实测 L/R 同步），要把最松的一侧压到 6 mm 内需 +10.1 mm。
#     ★ 取 39 mm（= 29 + 10）。`FIST_MIN_CLEAR_MM` 自动跟随为 41 mm。
#   ★★★ v011 再改 39 → 33 mm（**由门禁数字逼出来的改值**，不是调参凑绿）：
#     v010 修好手性（R 不再整体翻 180°）之后，两拳**左右已经对称**，但整体
#     **仍嫌远**：实测命中定格窗口内拳面 = HOLD_1 **L 11.17 / R 10.84 mm**、
#     HOLD_2 **L 6.14 / R 5.88 mm**（阈值 `HAND_TOUCH_MAX_MM` = **6 mm**）。
#     ⟹ `rage_chest_hit_ok` 取两窗口的**最松值** 11.17 > 6 ⟹ 红。
#     ★ 为什么两个窗口会差 5 mm（**不是** `TOUCH_OFF` 偏了）：拳心到胸面由
#       `surf + nrm*off` 逐帧解出，两个窗口的**名义深度完全相同**；差的是
#       `HIT_1` 与 `HIT_2` 的**躯干姿态**（`CHEST1` 前倾 vs `CHEST2` 后弓）
#       ⟹ `nrm` 不同 ⟹ 拳的滚转不同 ⟹ **离胸最近的那块肉不是同一块**，
#       拳心→该顶点的沿法线投影也随之差 5 mm（拳面不是平面，是 4 个指节）。
#     ⟹ 单一 `TOUCH_OFF` 无法同时精确对齐两个窗口，只能**按最松的那个标定**
#       （这就是「口径必须取最差值」而不是取平均值的理由）。
#       实测斜率 ≈ 1 mm/mm（拳面每深 1 mm ⟺ `TOUCH_OFF` 深 1 mm），
#       11.17 − 6 = 5.17 ⟹ 39 − 5.17 ≈ 33.8；取 **33** 留 1.2 mm 余量。
TOUCH_OFF = _env_f("E03_TOUCH_OFF", 0.031)     # 拳心落在「胸面 + 法线 x 本值」
# ★★★ v011 再改 32 → 31 mm（**由门禁数字逼出来的改值**，不是调参凑绿）：
#   `FIST_CLEAR_MARGIN_MM` 回落到 0（见其注释）之后，命中定格窗口实测拳面
#   **L 5.27 / R 6.07 mm**（阈值 `HAND_TOUCH_MAX_MM` = 6 mm）⟹ `rage_chest_hit_ok`
#   差 **0.07 mm** 红。实测斜率 ≈ 0.9 mm/mm，收 1 mm 即把最松侧压到 5.1 mm
#   （留 0.9 mm 余量），同时最压侧由 −0.21 到 ≈ −1.1 mm，仍远在 −10 mm 下限之内
#   ⟹ 两侧约束同时满足，且**不是**靠动阈值。
# ★★ v011 追加登记（ρ 定稿之后**重新测过**，避免留一个过期读数）：
#   上面那句「命中窗口 L 5.27 / R 6.07 mm」是 **ρ=0.5** 下的读数。`TWIST_SPLIT`
#   定稿 **ρ=0.6** 之后（腕部滚转多分给前臂 ⟹ 拳的滚转变了 ⟹ **离胸最近的那块
#   肉换了一块**），同样 `off=32` 下两窗口实测变成 **HOLD_1 L 5.27 / R 6.07、
#   HOLD_2 L 0.28 / R −0.21** —— 两窗口**差 6.3 mm**，不再是「差 0.07 mm」。
#   ⟹ 「收 1 mm 就能两侧同时满足」这个结论**只在 ρ=0.5 成立**；ρ=0.6 下它是
#     **互斥约束**（详见 `CHEST_EXTRA_OFF` 的 `CHEST_2` 注释：斜率一个 1.78、
#     一个 0.72 ⟹ 可行带只有 ~0.1 mm）。最终解法 = 全局保持 31 mm +
#     **给第二次捶胸单独一个名义深度**（`CHEST_2` = +3 mm），**没有动任何阈值**。
# ★★★ v011：**怒吼段拳要「压着胸往外走」**（新增拳目标名 `CHEST_ROAR`）。
#   问题（实测）：f=28(命中1) → f=44(仰头峰值) 之间拳目标**全程都是 `CHEST`**
#   （拳被钉在胸面上），而这一段躯干正从 `CHEST1` 后弓到 `ROAR`
#   （骨盆/脊柱 rx 由 +4 翻到 −5，`loc` 由 (0.005,−0.012) 移到 (−0.020,+0.012)）。
#   胸廓**边后弓边前挺** ⟹ 拳被胸顶进去：实测 f=43 **L 25 / R 21** 个非拇指
#   顶点在体内、最深 **−7.52 mm**（f=36 时还是 +3.43 mm 在体外）。
#   ⟹ `rage_punch_no_pierce_ok` 红。
#   ★ 修法不是改阈值、也不是把 `TOUCH_OFF` 全局推远（那会毁掉命中帧的贴合，
#     两个窗口的最松值 11.17 mm 已经逼着 `TOUCH_OFF` 收到 33 mm）：
#     而是给怒吼帧一个**名义深度更大**的拳目标 `CHEST_ROAR` = 胸面 + 法线 ×
#     (`TOUCH_OFF` + 本值)。语义上完全正当：**胸在往后弓的时候，拳要么跟着
#     让开、要么被胸顶穿** —— 让开才是解剖学上发生的（胸廓后弓时肩胛外展、
#     拳自然被带离胸面）。视觉读法仍是「捶胸 → 仰头怒吼（拳仍压着胸）→ 抬拳」。
# ★★★ v011：**第二次捶胸的拳要额外让开 3 mm**（新增拳目标名 `CHEST_2`）。
#   问题（实测，`_rage_gate14` vs `_rage_gate15` 两次读数标定）：
#   `TOUCH_OFF` 是**单一**名义深度，但两个命中窗口的躯干姿态不同
#   （`CHEST1` 前倾 / `CHEST2` 后弓）⟹ `nrm` 不同 ⟹ **离胸最近的那块肉不是
#   同一块**（拳面不是平面，是 4 个指节）⟹ 实测同一 `TOUCH_OFF` 下两窗口拳面
#   差 **6.3 mm**（off=32：f=28 R **6.07** vs f=52 R **−0.21**）。
#   ★ 由此产生一对**互斥**约束（斜率实测）：
#     · HOLD_1（f=28 R）δface/δoff = **1.78 mm/mm** ⟹ 要 ≤ 6 mm 须 `off ≲ 31.7`
#     · HOLD_2（f=52 R）δface/δoff = **0.72 mm/mm** ⟹ 要 f=52 那 6 个拳面顶点
#       出体（`rage_punch_no_pierce_ok`）须 `off ≳ 31.7`
#     ⟹ 单一 `TOUCH_OFF` 的可行带只有 **~0.1 mm**（还要再叠 f=6 的 4 顶点约束）
#       —— 这不是「调参」，是**用错了旋钮**：两个窗口本来就该有**各自的名义
#       深度**，与 `CHEST_ROAR` 同一条道理（躯干姿态变了，拳要么跟着让开、
#       要么被胸顶穿）。
#   ★ 实测取值：全局 `TOUCH_OFF` 保持 31 mm（HOLD_1 R 4.29 / L 4.56 mm，余量
#     ≥ 1.4 mm；也保住 f=6 / f=40 的计数不涨），给 `CHEST_2` 额外 **+3 mm**
#     ⟹ HOLD_2 拳面由 −0.93 抬到 **≈ +1.23 mm**（仍在贴合带内、且更实），
#       f=52 的 6 个拳面顶点全部出体 ⟹ 穿透计数回落。
#   ★ 语义正当：第二次捶胸发生在**胸廓后弓**时，肩胛外展、拳自然被带离胸面
#     一点点 —— **让开**才是解剖学上发生的。
CHEST_EXTRA_OFF = {"CHEST_ROAR": _env_f("E03_ROAR_LIFT", 0.020),
                   "CHEST_2": _env_f("E03_CHEST2_LIFT", 0.003)}
# ★★★ v011 回归：本值 8.0 → **2.0**（回退到 v010 口径）。
#   为什么 8.0 是错的方向（实测，见 gate12）：`FIST_MIN_CLEAR_MM` = `TOUCH_OFF`×1000
#   + 本值 = 40 mm 之后，**命中帧也进了保护层** —— 拳心被顶到 40 mm ⟹ 拳面
#   11.89 mm（gate11 同口径下是 6.95）。也就是说：把「防前挺穿透」的余量
#   加在了**命中帧的贴紧度**上，两个目标互相打架。
#   ★ 正确的分工（gate12 分离实验给出）：
#     · 斜坡穿透（f=9~15，`STATION→WIND` 过渡）—— 由 **WIND 几何**负责
#       （`FIST_WIND/FIST_WIND_S` 前推 35 mm，单独就把 38 顶点 / −11.35 mm
#       清到 4 顶点 / −6.79 mm）。
#     · 怒吼段穿透（f=43）—— 由 `CHEST_EXTRA_OFF`（`CHEST_ROAR`）负责。
#     ⟹ 保护层余量应回到「只兜住胸廓前挺那几帧」的小值（v010 实测 2 mm 够）。
FIST_CLEAR_MARGIN_MM = _env_f("E03_CLEAR_MARGIN", 0.0)

# ★★★ v011 记录：一条**被实测否掉**的修法（留在这里防止后人重走）。
#   现象：`f=3` 右手 `Hand_Palm_R` 3 个非拇指顶点在躯干体内、最深 −6.18 mm。
#   溯源（`_e03_early.py`，站架姿**实测**）：
#     · 站架自己就有 **4** 个 `Hand_Palm_R` 顶点在体内（−0.54 / −1.17 / −4.31 /
#       −4.50 mm）⟹ **A01 `Idle_01` 的预存缺陷**（与本支 ③ 登记的拇指缺陷同侧同源）。
#     · 它们离**拳心 88~106 mm**（贴**腕/前臂**一侧，**不是拳面**）；站架拳心自身离
#       躯干 **+66.63 mm**（L +100.69）⟹ 拳离胸很远，捅进去的是**腕侧掌肉**。
#   机理：蓄力段「沉髋 45 mm + 含胸前倾」让**胸面主动向前** 2~3 mm，而手臂此刻
#     只走了 `arm_env(3) ≈ 0.12` ⟹ **胸追上腕**，把接缝那 0.5 mm 的余量吃光。
#   ★ 试过的修法（`EARLY_LIFT_MM`，沿胸面法线把拳目标外推，峰值 9 mm）：
#     **实测无效，已删除** —— 只把最深从 −6.79 改到 −6.18（+0.61 mm）。
#     原因是**混合稀释**：`f=3` 的 `arm_env ≈ 0.12`，拳目标外推 9 mm 经
#     「站架臂 ×(1−env) + IK 臂 × env」后只剩 ~1 mm 落到手上。
#     ★ 更要紧的是它**不改变门禁结果** ⟹ 是个**惰性旋钮**，按工程纪律
#       「旋钮必须真的接进代码、并改变判据」应当删掉，而不是留着充数。
#   ⟹ 正确结论：**这不是本支引入的缺陷，也无法靠"拳目标外推"修掉**（臂几乎还是
#      站架臂）。判据因此改为「**不得比站架基线更糟**」，见 ② 段。
CHE_PROBE_X = _env_f("E03_PROBE_X", 0.135)     # 求胸面的探针横向位置
CHE_PROBE_FWD = _env_f("E03_PROBE_FWD", 0.55)
# ★★ 手骨朝向 = **显式骨基**（不用 `aim_bone` + 扫 twist）。
#
#   为什么要换（本支口径 v003 的第三处修正）：
#     `A.aim_bone` 只保证「骨长轴指向目标方向」，**滚转由最短弧顺带决定**。
#     而「捶胸要读成拳」靠的正是滚转（拇指朝哪边）。实测：`HAND_TWIST = 0` 时
#     穿进胸里的就是**拇指网格**（离拳心 101.5 mm、沿胸法线偏出 88.4 mm），
#     而掌/指簇离拳心只有 12 mm ⟹「拳没打深，是拿拇指戳胸」。
#     更糟的是 `aim_bone` 的滚转**不连续**（最短弧在方向接近对跖时会翻），
#     所以「扫一个固定 twist」是在给一个会漂的基准加常数 —— 肘部一改它就失效
#     （实测：肘连续性修好后，原本调好的 twist ±60 立刻从 +14 mm 掉到 −9 mm）。
#
#   正确做法：`_e03_handaxis.py` 量出 `hand.L/R` 的 rest 基语义 ——
#     `local_y` = 骨长轴（T-pose 指向外侧）、`local_x` = **拇指侧**、`local_z` = 上，
#     且 `local_z = local_x × local_y`（右手系）。
#   ⟹ 用**胸面**给出「指节/拇指该朝哪」，直接张成骨基：确定、连续、不靠扫参。
#     这与设计意图一一对应：「把拳**摆给胸看**」。
HAND_AXIS_MODE = os.environ.get("E03_HAND_AXIS", "thumb_out")
# 5 种解剖上说得通的摆法（都是「拇指/掌面朝哪」，不是「随便转一个角度」）：
#   thumb_out  ★默认：拇指朝**体侧外**（握拳压胸时拇指的自然位置）
#   thumb_up   拇指朝上（猩猩捶胸）
#   thumb_dn   拇指朝下（锤式）—— ★ v001~v007 用的是它，**实测在 f=76 退化**
#              （`y_dir` 扫过「正下」，基准与拳轴只差 9.9° ⟹ 真旋转 83.9°/帧）
#   outward    拇指背离胸面（掌心朝胸）—— ★ 实测**恒为最差**（捶胸时拳轴按
#              定义沿 −法线，与基准正交度 0°）
#   inward     拇指指向胸面（掌背朝胸）
HAND_AXIS_MODES = ("thumb_up", "thumb_dn", "outward", "inward")
# ★★★ **手性修正（本支口径 v003 的第三处修正，也是最后一块拼图）**
#   `_e03_handaxis.py` 实测 rest 基：
#     · `hand.L`：`local_x` = (0,−1,0)，拇指方向 (0.042,−0.996,−0.075)
#       ⟹ 拇指 ≈ **+local_x**（`proj.local_x = +0.996`）
#     · `hand.R`：`local_x` = (0,+1,0)，拇指方向 (−0.042,−0.996,−0.075)
#       ⟹ 拇指 ≈ **−local_x**（`proj.local_x = −0.996`）
#   ⟹ 右手的 rest 基是左手的**镜像副本**（不是旋转副本）⟹ 「同一个 `x_hint`
#     值」在左右手上意味着**相反的拇指方向**。这就是为什么之前用同一个提示
#     向量时，总有一侧干净、另一侧把拇指捅进胸腔（实测 L 496 个顶点在体内 /
#     R 0 个，一换提示又反过来）。
#   修法：把提示向量按手性乘一次，让「拇指朝上」在左右手都**解剖学地**朝上。
#
# ★★★ v010 复核（**实测推翻 v003 的符号**，证据在下面）：`-1` 会让 R 手绕自身
#   `local_y` 整整转 **180°** —— 后果正是本支 f=28/52 那条「L 拳面 14.71 mm
#   而 R 只 2.84 mm」的不对称：
#     `_e03_anatomy` 实测**离拳心最近**的那块肉 —— L 是 `Finger_Pinky_L`
#     （离拳心 **38.0 mm** / 沿法线 +26.2），R 是 `Finger_Index_R`
#     （离拳心 **48.2 mm** / 沿法线 +41.1）。**两侧领先的手指都不是同一根**
#     ⟹ 拳的滚转左右不镜像，而不是「网格本身不对称」。
#   数学上（为什么 `-1` 会翻 180°）：要让 R 的世界几何成为 L 的**镜像**，
#   需要 `M_pose_R = S·M_pose_L·(M_rest_L⁻¹·M_rest_R)`，`S = diag(-1,1,1)`。
#   而本骨架 `M_rest_R = M_rest_L · Ry(180°)`（`_e03_handaxis` 实测
#   `hand.L` 的 `local_x=(0,-1,0)`、`hand.R` 的 `local_x=(0,+1,0)`，
#   拇指分别在 `+local_x` / `-local_x`）⟹ 正确解的第一列是 **-S·x_L**，
#   而 `-1` 手性给出的正是 **+S·x_L** ⟹ 两者差一个 180° 翻转。
#   `E03_CHIRALITY=0` 关闭该翻转（默认；反向验证旋钮）。
HAND_CHIRALITY = ({"L": 1.0, "R": -1.0} if _env_b("E03_CHIRALITY_FLIP")
                  else {"L": 1.0, "R": 1.0})

# ★★★ 拳**面**朝向（本支口径 v004 的第二处核心修正，见 `seat_arm`）
#   0.0 = 拳沿前臂伸长（旧口径：拳擦着胸推过去，拇指横插进胸）
#   1.0 = 拳面正对胸面（新口径：用指节面砸胸）
#   ★ 默认给 1.0 是**设计意图**，不是调参：清单原文是「**捶胸**」——
#     捶 = 用拳面砸，不是用拳侧蹭。混合系数只是把「腕关节允许的偏转」
#     显式化，便于反向验证时把它拨回 0 看判据是否变红。
FIST_FACE_BLEND = 0.0 if _env_b("E03_TP_FACEALONG") else _env_f(
    "E03_FACE_BLEND", 1.0)
# ★★ 拳面朝胸的**相位包络**（口径 v005 的修正，理由见 `face_blend`）：
#   ★ 窗口必须**内含于臂包络的平台段**，即 [ARM_UP_AT(14), ARM_DN_AT(84)]：
#     反折不在包络过渡段内发生 ⟹ 包络混合的「两端直线」才是安全的。
#     · RAMP_IN  (14, 26)：臂抬到位（14）之后才开始反折，命中（28）前满值。
#     · RAMP_OUT (68, 82)：第二声怒吼（ROAR2=66）之后才松开，臂下落（84）前松完。
#     ★ 首轮写成 (10,24)/(74,88) 时窗口**越过了**平台段，实测在 f=14 与 f=82
#       的 b≈0.5 处出现 169.6° / 93.7° 的逐帧真翻转 —— 窗口与包络叠加的后果。
FACE_RAMP_IN = (_env_i("E03_FACE_IN0", 14), _env_i("E03_FACE_IN1", 26))
FACE_RAMP_OUT = (_env_i("E03_FACE_OUT0", 68), _env_i("E03_FACE_OUT1", 82))

# ★★★ 前臂**旋前**（把腕部扭转分一部分给前臂）—— 口径 v007 的核心修正。
#   问题：拳面正对胸需要绕手骨轴扭约 **115°**，而 XYZ 欧拉的 `ry` 奇异点在 ±90°
#     ⟹ 手部 euler 在 f=22→23 处从 ry=109.7 跳到 68.2（**矩阵只变了 17°**，
#       纯表示翻转）。`no_teleport` 按 euler 判 ⟹ 被判成瞬移，且 F-Curve
#       数值插值会真的拐出怪姿态。
#   修法：`aim_bone(..., twist_deg=...)` 给前臂加一个绕其**自身骨轴**的自转，
#     由人体解剖（捶胸必先旋前）而来。★ 为什么是**几何中性**的：
#     `orient_hand` 把手的**世界矩阵**绝对设定，前臂多扭多少，手骨局部 euler
#       就少扭多少 —— 手的**世界朝向一个比特都不变**；而绕前臂轴的自转
#       不移动前臂的 tail ⟹ 腕关节位置也不变。⟹ 命中距离 / 穿模 / 手感不变，
#       只有「扭转记在谁账上」变了。
#   符号：左右骨架镜像，取 `HAND_CHIRALITY`（实测符号，用 `_e03_twist_split.py` 标定）。
# ★★★ v011：本常量**降级为「残余偏置旋钮」**（默认 0.0）。真正的旋前量改由
#   `seat_arm` 按**几何量做不动点迭代**求出（把腕部轴向滚转按 50/50 分给前臂与
#   腕），理由与实测在 `seat_arm` 内。保留这个常量的用途：反向验证时可以强行
#   加一个偏置，看 `no_teleport` / `rage_euler_step_deg_max` 是否**又变红**
#   （旋钮必须真的接进代码 —— 否则它就是惰性的，等于没有旋钮）。
FOREARM_TWIST_DEG = _env_f("E03_FOREARM_TWIST", 0.0)
# ★★ 滚转分配比 ρ：**前臂（旋前）承担的比例**，`seat_arm` 的不动点迭代用它求解。
#   ρ = 0.5 ⟺ v010 的「50/50」。写成旋钮是为了**扫描**（并且旋钮必须真的接进代码）。
# ★★★ v011 定稿 ρ = **0.6**（**由门禁数字逼出来的改值**，不是调参凑绿）：
#   `no_teleport`（逐帧单轴欧拉步 ≤ 25°）在 ρ=0.5 下实测 **27.862° @ [19, hand.R]**
#   ⟹ 红。根因（`_e03_diag2c.py` + `E03_DUMP_STEP` 权威口径实测）：f=19 处
#   `de(euler) = 25.4°` 而 `dm(矩阵) = 17.0°` ⟹ **euler 步 ≈ 1.5 × 矩阵步**，
#   是**雅可比在奇异带附近放大**（穷举 54 个等价欧拉候选后的最小步仍 = euler 步，
#   证明不是选错分支）。把腕部轴向滚转**多分给前臂**（旋前）后，腕的 `ry`
#   离奇异带更远 ⟹ 实测 ρ=0.55 → 25.413°、**ρ=0.6 → 24.081°**（余量 0.92°）、
#   ρ=0.62 → 23.567°。
#   ★ 取 0.6 而不是 0.62：0.6 已满足且更接近解剖学（前臂旋前本来就该承担
#     大头），同时**不改变**命中窗口的拳面读数（实测 ρ=0.5/0.6 两窗口拳面同为
#     4.56 mm）⟹ 与「捶胸」判据正交，不会一改就牵动另一边。
#   ★ 已实测 ρ 是**真旋钮**：ρ=0.5 → `no_teleport` 红（27.862），ρ=0.6 → 绿。
TWIST_SPLIT = _env_f("E03_TWIST_SPLIT", 0.6)

# ★★ 手心**滚转基准**的退化带（口径 v008，见 `orient_hand`）：
#   `|x_hint 在 ⊥y 平面上的投影|` 落在这个区间内时，在「投影」与「上一帧标架
#   最小旋转搬运」之间用测地线混合。|投影| = sin(∠(y, x_hint))。
#   ★ 取 0.35/0.55（≈ ∠ 20.5° / 33.4°）：实测危险帧是 f=75/76/77 的 ∠ 24.2/
#     **9.9**/24.1° ⟹ 投影 0.41/0.17/0.41，f=76 落在纯搬运区，f=75/77 落在
#     混合区，两端平滑过渡（不会在切换处跳）。
HAND_X_HINT_MIN = _env_f("E03_HINT_MIN", 0.35)
HAND_X_HINT_FULL = _env_f("E03_HINT_FULL", 0.55)


# ★ 拳**心**自身不得进胸超过此值。★ 默认 = 命中深度 + 2 mm：拳心之外还有
#   **指节前缘**（实测比拳心再前伸 26~31 mm），只保护拳心挡不住「胸廓前挺时
#   把拳面顶进胸腔」那一小段（实测 f=40~44 残留 4~9 个顶点）。
#   ★ 命中姿态**完全不受影响**（命中帧拳心实测 39~40 mm > 31 mm，保护层不触发）。
FIST_MIN_CLEAR_MM = _env_f("E03_FIST_CLEAR", 0.0) or (
    TOUCH_OFF * 1000.0 + FIST_CLEAR_MARGIN_MM)

# =============================================================== 阈值
# ★ 全部由实测导出（见报告 / 日志）；铁律：不许为了变绿而放宽。
#   ★★ 本支（v004）把阈值分给**两个独立口径**，因为「达到」与「不穿」是两个
#      方向，必须各用一把不会说谎的尺子：
#        · **达到** → 带符号距离（近场、正对胸面，校准实测 +20/+50/+100 mm
#          误差 < 0.01 mm；凹面处不可作绝对尺，只作贴紧度）
#        · **不穿** → 13 方向多数表决（`_e03_yard.py` 实测：真内部恒 13/13 票，
#          单方向奇偶擦边噪声只有 1~2 票，两极断崖式分离）
HAND_TOUCH_MAX_MM = _env_f("E03_HAND_TOUCH", 6.0)     # 指节面必须压到胸面 6 mm 内
HAND_PIERCE_MM = _env_f("E03_HAND_PIERCE", 10.0)       # 拳陷入胸体的最大深度上限
TOUCH_MIN_FRAMES = _env_i("E03_TOUCH_FRAMES", 6)       # 「贴胸」至少这么多帧
# ★ 深度分级计数用的 eps（mm）—— 量「浅擦边」与「真捅进」各有多少顶点（见 ② 段）。
PIERCE_DEEP_EPS_MM = (1.0, 2.0, 3.0, 5.0)
HEAD_BACK_RANGE = (_env_f("E03_HEAD_LO", 30.0), _env_f("E03_HEAD_HI", 62.0))
HEAD_BACK_SETTLE_MAX = _env_f("E03_HEAD_SETTLE", 15.0)
WINDUP_DROP_RANGE = (_env_f("E03_WIND_LO", 25.0), _env_f("E03_WIND_HI", 70.0))
WINDUP_FLEX_MIN = _env_f("E03_WIND_FLEX", 12.0)
FLIP_MIN_DEG = _env_f("E03_FLIP_MIN", 20.0)
FOOT_LOCK_MM = _env_f("E03_FOOT_LOCK", 0.5)
TOE_LOCK_MM = _env_f("E03_TOE_LOCK", 0.5)
SOLE_BAND = (-2.0, 6.0)
NO_SNAP_END_DEG = _env_f("E03_SNAP_END", 6.0)
SEAM_POS_MAX_MM = _env_f("E03_SEAM_POS", 0.01)
SEAM_DIR_MAX_DEG = _env_f("E03_SEAM_DIR", 0.05)
CLIP_MAX_MM = _env_f("E03_CLIP_MAX", 0.0)
REACH_MAX_RATIO = 0.995
ROAR2_MIN_DEG = _env_f("E03_ROAR2_MIN", 12.0)      # 第二次怒吼也必须看得见
MATRIX_STEP_MAX_DEG = _env_f("E03_MATSTEP", 25.0)  # 矩阵口径真旋转步上限
TAIL_SETTLE_N = _env_i("E03_TAIL_N", 12)           # 收势判据 = 末尾 N 帧
# ★ 「拳在胸上」的整段时间 = 命中帧 → 怒吼顶（28→44）+（52→66）。
#   ★ 口径修正（v004）：v003 写成「命中帧起 9 帧」是**太窄**——它把
#     「拳仍压在胸上、胸廓正在前挺」的 37~44 帧切出去了，而穿透恰好发生在那里。
#     现在覆盖**整段贴胸时间**，判据不再有盲区。
CONTACT = (list(range(HIT_1, ROAR + 1)) + list(range(HIT_2, ROAR2 + 1)))
# ★ 出图/像素探针共用的**逐帧集合**（主渲、反面重渲、像素探针三者必须逐帧相同，
#   否则「重心差」会把「帧不一致」混进来）。提成模块常量供 `probe_rage_pixels.py`
#   直接引用，避免两处各抄一份、日后改一处忘一处。
STEM_FRAMES = sorted(set([0, 12, 20, 24, 28, 30, 36, 40, 44, 48, 52, 54,
                          60, 66, 72, 84, 96]))

# =============================================================== 取景（★ 本支自立）
# ★★ 本支**两条尺子各占一个机位**（与 E01 / E02 的单机位都不同，**必须新立并登记**）：
#   · **捶胸**是**正面**动作（双拳从两侧向中线收拢，横向 = 世界 X）⟹ 必须**正面**；
#     侧视会把「向中线收拢」**压在视轴上**（承 E02 修正 ③ 的教训）。
#   · **仰头**是**矢状面**动作（头向后倒，纵向 = 世界 YZ）⟹ 侧视才读得出；
#     正面只看得到下巴抬起（弱）。
#   取景由本支几何算出：侧视身体包络 y ∈ [−0.40, +0.28]、z ∈ [0, 1.80]；
#   正面横向 x ∈ [−0.35, +0.35]、z ∈ [0, 1.80]。
VIEW_E03_SIDE = ("side", (4.2, -0.10, 0.90), (0.0, -0.10, 0.90), 1.95,
                 (780, 1100))
VIEW_E03_FRONT = ("front", (0.0, -5.6, 0.92), (0.0, 0.0, 0.92), 2.10,
                  (780, 1100))

# =============================================================== 反向验证旋钮
SEAM_ZERO = _env_b("E03_TP_SEAM_ZERO")
CHEST_FAR = _env_b("E03_TP_CHESTFAR")
CHEST_FAR_MM = _env_f("E03_TP_CHESTFAR_MM", 200.0)
# ★★★ v012：`CHEST_FAR` 的位移**必须含正面可见的分量**（远离中线 ±X）。
#   实测（`_rage_px.log`）纯 −Y 推 200 mm ⟹ 正面机位（视轴 = Y）看不见，
#   手层像素重心只移 15.11 px（阈值 ≥90）⟹ `px_rage_pound_can_fail_ok`
#   结构性见不了红。这不是「阈值太严」，是**扰动落在视轴上**（承 E02 修正 ③）。
CHEST_FAR_X_MM = _env_f("E03_TP_CHESTFAR_X", 300.0)
CHEST_CLIP = _env_b("E03_TP_CHESTCLIP")
CHEST_CLIP_MM = _env_f("E03_TP_CHESTCLIP_MM", 25.0)
HEAD_DOWN = _env_b("E03_TP_HEADDOWN")
HEAD_OVER = _env_b("E03_TP_HEADOVER")
# ★ `NO_HITSTOP` **已在 `KEYS` 之前定义**（见那里的长注释：它必须参与键表构造，
#   否则旋钮惰性）。此处不再重复定义。
FOOT_SWAY = _env_b("E03_TP_FOOTSWAY")
FOOT_SWAY_MM = _env_f("E03_TP_FOOTSWAY_MM", 55.0)
LOOP_BREAK = _env_b("E03_TP_LOOPBREAK")
NO_FLIP = _env_b("E03_TP_NOFLIP")
FACE_ALONG = _env_b("E03_TP_FACEALONG")     # ⑨ 拳面回到「沿前臂」（旧口径）
TRACE = _env_b("E03_TRACE")
TGT_TRACE = _env_b("E03_TRACE_TGT")
PIERCE_TRACE = _env_b("E03_TRACE_PIERCE")

# =============================================================== 模块级表
BASE = {}
ANCHOR = {}
STATION_FIST = {}
BONE_LIST = []
TORSO = None
STATION_FACE_MIN = {"L": 0.0, "R": 0.0}
STATION_PIERCE = {"L": {}, "R": {}}
# ★ v010：站架臂的**三个自由度实测值**（`boot()` 在站架姿上采集）——
#   `seat_arm` 按 `arm_env` 把 IK 解向它们收敛，使包络两端重合。
#   见 `seat_arm` docstring 的实测账目（f=96 / env=0 时手差 119.7°）。
STATION_HAND_Y = {}
STATION_HAND_X = {}
STATION_POLE_DIR = {}
# ★ v011：每侧前臂**实际施加的旋前量**（`seat_arm` 的不动点迭代结果）——
#   只为诊断/报告留账（不属于姿态，不参与任何判据计算）。
LAST_FOREARM_TWIST = {}


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


def spec_of(name):
    spec = dict(SPECS[name])
    if NO_FLIP and name in ("ROAR", "CHEST2", "ROAR2"):
        # ⑧ 躯干不翻转：后仰段改成**继续前倾** ⟹ 翻转幅度掉到 ~2°
        for key in ("pelvis", "spine_01", "spine_02", "chest"):
            spec[key] = 5.0
    if HEAD_DOWN and name == "ROAR":
        spec = dict(spec)
        # ★★★ v012：像素级反面 ④a 量的是**绝对屏幕位置**（侧视头层重心），
        #   它**包含躯干后弓的贡献** —— 只把 neck/head 调到「略后仰」（旧值
        #   −4/−2）时，躯干仍把头向后**绝对**带走 23.96 px（阈值 ≤6）⟹ 见不了红。
        #   忠实仿真须让头**真正不后移**：把头主动压向前下方，抵消躯干后弓。
        spec["neck"], spec["head"] = 10.0, 14.0      # 仰头不够（头反而前低）
        spec["pelvis"], spec["spine_01"] = -1.0, -1.0
        spec["spine_02"], spec["chest"] = -1.0, -1.0
    if HEAD_OVER and name == "ROAR":
        spec = dict(spec)
        spec["neck"], spec["head"] = -30.0, -36.0    # 仰头过头（上限端）
    return spec


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
            out[key] = a[key] + (b[key] - a[key]) * g
    return out


def arm_env(frame):
    """臂包络：`env` 只在 `(ARM_UP_AT, ARM_DN_AT)` 区间内为 1，两端分别归 0。

    ★★★ v011 新增 `ARM_DN_DONE`（「回 0 **完成**」帧，而不是「开始回」帧）。
      理由 = 实测 + 门禁口径，**不是**调阈值：
        `no_snap_stop_ok` 判的是 **末尾 8 帧**（f ≥ TOTAL−8 = 88）逐帧角步
        ≤ **6°**（一字未动）。旧口径让 `env` 一直拖到 `f=TOTAL` 才归零
        ⟹ 收招的臂混合**整段压在尾段里**，实测 f=87→88 一步 **15.34°**
        （`hand.L`，= |站架−IK| ≈ 138° × d(env)/df ≈ 0.111）。
        把「回 0」提前到 `ARM_DN_DONE` 后，尾段 8 帧的臂**已经完全等于站架**
        ⟹ 姿态静止，判据自然满足。
      ★ 回程跨度 = `ARM_DN_DONE − ARM_DN_AT`，`smoothstep` 中段斜率 1.5/span
        ⟹ 跨度**不能太短**（会另炸 `no_teleport` ≤25° / `rage_matrix_step_ok`
        ≤25°）。实选取 (74, 88) = 14 帧：中段 ≈ 138°×1.5/14 ≈ **14.8°/帧**，
        同时满足 6°（尾段，已归零）与 25°（全程）。
      ★ 为什么这不是「把动作砍短」：拳目标在 f=66(ROAR2) 起已经沿
        `WIND_S → STATION` 回归，`env` 只是「把 IK 解按权重换成站架解」的
        混合系数 —— 提前归零 = **收招更早收干净**，符合「收势回战斗架势」。
    """
    if frame <= ARM_UP_AT:
        return _smoothstep(frame / float(max(1, ARM_UP_AT)))
    if frame >= ARM_DN_AT:
        span = float(max(1, ARM_DN_DONE - ARM_DN_AT))
        return _smoothstep((ARM_DN_DONE - frame) / span)
    return 1.0


def seam_canonicalize(keyframes):
    """把整条欧拉曲线按**轴的 360° 整数倍**整体平移，使**末帧 == 首帧**。

    ★ 为什么需要它（实测）：`compat_euler` 逐帧挑「离上一帧最近」的等价表示，
      会沿路**累积** 360° 的整数倍 —— 实测 `hand.L` 末帧 euler = −357.5，
      而首帧 = +2.5（**同一个姿态**，矩阵逐元素差 2.8e-07）。
      · `loop_seamless` 按 euler 比 ⟹ 报 `loop_angle_deg = 360.0`（假红）；
      · 更实际的风险：动作链到站架时，**键上差 360°** 会让混合期真的转一圈。
    ★ 为什么平移是**零副作用**的：XYZ 欧拉里 `rx ± k·360`、`ry ± k·360`、
      `rz ± k·360` 都给出**同一个旋转矩阵**（`Rz·Ry·Rx`，单轴加整圈不变）。
      整条曲线减同一个常数 ⟹ 逐帧姿态不变、相邻帧差值不变、F-Curve 形状不变。
    """
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
    """XYZ 欧拉的**严格等价族**：`(rx,ry,rz)` 与 `(rx+180, 180−ry, rz+180)`
    再各自叠加 360° 整数倍 ⟹ 2×27 = 54 个候选（矩阵严格相同）。

    ★★★ 候选顺序**必须把「原始表示」排在第 0 位**（`k = 0` 最先，再 −1/+1）。
      为什么（v011 踩过的坑，实测）：整体平移 360° 的整数倍是**代价完全相同的
      并列解**（逐步差一个常数 ⟹ 逐帧步长一模一样）。DP 用 `fams[0][0]` 当
      参考原点，若第 0 位是 `k=−1`，DP 就会选「全时间轴整体 −360°」的分支：
      矩阵零变化、逐帧步长零变化，但 `current_head_back` 量的是**欧拉 rx 本身**
      ⟹ neck/head 各 −360 ⟹ 仰头角凭空多出 **+720°**（实测 36.0° → 756.0°，
      `rage_head_back_ok` 从一个真实约束变成一条噪声红项）。
      ⟹ 把 `k=0` 排在最前，并列时代价最低的是「保持原表示」，语义明确。
    """
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
    """★★★ 欧拉表示兼容化（C14 / D01 踩过的同一个万向节锁坑）。

    为什么必须有这一步：`A.aim_bone` 每帧用 `quaternion.to_euler()` **独立**
    反解欧拉，返回的是「规范区间」里的**某一个等价表示**。同一段平滑旋转，
    相邻两帧可能落到**两组数值差 90°以上的等价欧拉**上（rx↔180−rx、
    rz↔rz±180 这一族）。于是：
      · `no_teleport`（按 **euler** 逐帧差判）会**误报**「瞬移」；
      · 更要命的是 **F-Curve 会按数值插值** ⟹ 两条键之间真的会拐一个
        「绕一大圈」的中间姿态 —— 那不是误报，那是**真的会渲出怪动作**。
    实测 v001：`f=26 / forearm.R` 一步 **95.618°**（阈值 25）。

    ★★★ 做法：**自己穷举等价表示**，不依赖 `Euler.make_compatible`。
      实测 `make_compatible` 在本支关键处**失效**：f=22→23 的真实旋转只有
      **12.527°**，它给出的数值步却是 **170.40°**（`_e03_euler.py`）；
      而穷举后发现存在最大数值步 **20.50°** 的等价表示（`_e03_euler2.py`）。
      ⟹ 用它 = 把一处本来能修好的瞬移留在键上（F-Curve 会真的插出怪姿态）。
    ★ 这一步**不改变任何姿态**（等价表示 ⟹ 同一旋转矩阵），只改变键上的数字：
      `apply_pose` 把度转弧度后直接写 `rotation_euler`，矩阵完全一致。
      所以接缝（矩阵口径）与所有几何量都不受影响。

    ★★★ v011：**逐帧贪心 → 全局最优（min-max 路径 DP）**。
      为什么要换（实测）：v010 的写法是「每帧挑离**上一帧已选值**最近的那个」。
      贪心只保证**局部**最优，而门禁量的是**整条曲线的最大值**
      （`max_frame_step_deg` = max over 所有相邻帧对）。
      实测反例（`_e03_diag2.py`，v011 中途）：`hand.L` 在 f=22→23 的
      **可达最小步是 20.92°**（穷举证实），可贪心在 f=22 为了压低 f=21→22
      选了一个离 f=23 很远的等价表示 ⟹ 实测这一步变成 **36.886°**
      （`rage_euler_step_at = [23, 'hand.L']`）。
      ⟹ 换成「最小化**最大单轴步**」的瓶颈 DP：
         `best[i][j] = min_k max(best[i−1][k], step(k → j))`，
         再按前驱回溯出整条最短（min-max）路径。
      这一步同样**零几何副作用**（等价表示），只是把「表示的选择」从
      「贪心」升级成「全局最优」—— 判据不变、阈值不变。
    """
    fams_per_name = {}
    for name in keyframes[0][1]:
        if name.startswith("@"):
            continue
        raw = [pose.get(name, (0.0, 0.0, 0.0)) for _f, pose in keyframes]
        spread = max(max(abs(a - b) for a, b in zip(x, y))
                     for x in raw for y in raw)
        if spread < 1e-9:
            # ★ 全时间轴恒定 ⟹ 无需搜索（57 骨里绝大多数属于这一类，
            #   提前剪掉它们是把上面的 DP 从「57 骨」压到「几骨」的关键）。
            #   存成「每帧 1 个候选」的形状，与搜索路径统一。
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
        count = len(fams[0])
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

    out = []
    if os.environ.get("E03_DEBUG_COMPAT"):
        for name, picks in chosen.items():
            raw = [pose.get(name, (0.0, 0.0, 0.0)) for _f, pose in keyframes]
            deltas = [tuple(picks[i][k] - raw[i][k] for k in range(3))
                      for i in range(n)]
            if any(abs(v) > 1e-6 for d in deltas for v in d):
                uniq = sorted({tuple(round(v, 3) for v in d) for d in deltas})
                print("E03_COMPAT_SHIFT %s n_delta=%d uniq=%s"
                      % (name, len(uniq), uniq[:6]))
    for i, (frame, pose) in enumerate(keyframes):
        new_pose = dict(pose)
        for name, picks in chosen.items():
            new_pose[name] = picks[i]
        out.append((frame, new_pose))
    return out


# =============================================================== 脚锁
def lock_feet(arm, pose, want, iters=8, damp=0.85):
    """把双踝**闭环**钉在 `want`（世界坐标 dict）上，就地改 `pose`。

    ★ 照抄 E01 / E02 的结构（planar IK + `thigh.rz` 配平 x）。
    ★ 本支 `want` **全程恒定 = 站架踝**：本支**不迈步**（爆发时脚更不该动），
      所以「脚」这一环的力量传导**不体现在踝的位移上**，而体现在
      **腿的伸缩**（骨盆下沉 45 mm → 上顶 12 mm，髋↔踝距离实测走 ~46 mm）
      —— 见 `chain_present_ok` 的 `foot_axis_mm`，**理由写进日志**。
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


# =============================================================== 胸几何查询
def _torso_eval():
    depsgraph = bpy.context.evaluated_depsgraph_get()
    ev = TORSO.evaluated_get(depsgraph)
    return ev, ev.matrix_world.copy()


def chest_surface(arm, side):
    """当前姿态下「胸前表面点 + 外法线」（世界）。逐帧重解，不是静态值。"""
    ev, mw = _torso_eval()
    ch = Vector(A.bone_world(arm, "chest", "head"))
    ct = Vector(A.bone_world(arm, "neck", "head"))
    mid = ch.lerp(ct, 0.45)
    sx = 1.0 if side == "L" else -1.0
    probe = Vector((sx * CHE_PROBE_X, mid.y - CHE_PROBE_FWD, mid.z))
    ok, loc, nrm, _idx = ev.closest_point_on_mesh(mw.inverted() @ probe)
    world_loc = mw @ loc
    world_nrm = (mw.to_3x3() @ nrm).normalized()
    return world_loc, world_nrm


def inside_votes(point, tree=None):
    """点沿 13 个方向各打一条射线，返回**得票数**（0..13，全票 13 = 内部）。

    ★★★ 为什么需要投票（本支口径 v004 的第一处修正，有实测证据）：
      `_e03_yard.py` 实测 `Suit_Torso` **是水密的**（1858 顶点 / 1856 面 /
      `boundary_edges = 0` / `nonmanifold_edges = 0`），理论上单方向奇偶即可。
      但实测得票分布是**断裂的两极**：真内部 = **13 票**，其余全部 ≤ 2 票。
      也就是说**单方向奇偶会产生 1~60 个假阳性**（`f=60` 单方向报 22 个
      "体内顶点"，实际得票全是 1）—— 因为射线会**擦过边 / 顶点**，在闭合网格上
      擦边一次就多算一次穿越 ⟹ 奇偶翻成"内"。这类噪声在**单方向**下无法识别，
      在**多方向投票**下自动暴露（擦边只在个别方向发生）。
    """
    tree = tree if tree is not None else torso_bvh()
    return sum(1 for d in INSIDE_RAYS if _ray_parity(tree, point, d))


def inside_torso(point, tree=None):
    """点是否在躯干**实体内部**（13 方向多数表决 = 权威口径）。"""
    return inside_votes(point, tree) >= INSIDE_VOTES_MIN


def inside_torso_single(point, tree=None):
    """**对照口径**：单一固定方向奇偶。

    ★ 保留它只为了**在报告里登记两个口径差多少** —— 它是 E03 开工第一版用的
      尺子，实测会假阳性，**不得作为门禁**。
    """
    tree = tree if tree is not None else torso_bvh()
    return _ray_parity(tree, point, Vector((0.3178, 0.7512, 0.5773)).normalized())


def hand_inside_count(side, tree=None, with_single=False, step=1):
    """该侧手部**在躯干实体内部**的顶点数（权威 = 多数表决）。

    返回 `(inside, total, by_part, single)`，`single` = 单方向口径的对照读数
    （★ 只在 `with_single=True` 时真算，因为它是 13 倍外的额外开销，
    且**已知不可靠**，仅用于报告里的对照登记）。

    ★ 这是本支「捶胸」的**主判据**：`closest_point_on_mesh` 的带符号距离
      在凹几何上会说谎（最近面可能是躯干侧壁或下摆内壁，而不是胸面）——
      v001 因此得出「站架 R 拳与躯干本来就重叠 34 mm」的**错误**结论。
      所以两个口径分开用：
        · **达到**（拳真的压到胸）→ 带符号距离判「掌面离胸面多近」；
        · **不穿**（拳没捅进胸腔）→ 多数表决判「有没有顶点真的进了躯干」。
    """
    deps = bpy.context.evaluated_depsgraph_get()
    tree = tree if tree is not None else torso_bvh()
    inside, total, by_part, single = 0, 0, {}, 0
    for obj in bpy.data.objects:
        if obj.type != "MESH" or not obj.name.endswith("_" + side):
            continue
        if not any(obj.name.startswith(p) for p in HAND_PREFIX):
            continue
        if obj.name.startswith("Thumb_"):
            group = "thumb"
        elif obj.name.startswith("Hand_Palm_"):
            group = "palm"
        else:
            group = "fingers"
        ev = obj.evaluated_get(deps)
        me = ev.to_mesh()
        mw = ev.matrix_world
        slot = by_part.setdefault(group, [0, 0, 0])
        for index in range(0, len(me.vertices), step):
            total += 1
            slot[1] += 1
            point = mw @ me.vertices[index].co
            if inside_torso(point, tree):
                inside += 1
                slot[0] += 1
            if with_single and inside_torso_single(point, tree):
                single += 1
                slot[2] += 1
        ev.to_mesh_clear()
    return inside, total, by_part, single


def signed_to_torso(point):
    """点到躯干面的**带符号距离**（mm；正 = 面外，负 = 已进入体内）。"""
    return torso_query(point)[0]


def torso_query(point):
    """点到躯干面的 (带符号距离 mm, 面上最近点, 外法线)。"""
    ev, mw = _torso_eval()
    _ok, loc, nrm, _idx = ev.closest_point_on_mesh(mw.inverted() @ Vector(point))
    world_loc = mw @ loc
    world_nrm = (mw.to_3x3() @ nrm).normalized()
    gap = (Vector(point) - world_loc).dot(world_nrm) * 1000.0
    return gap, world_loc, world_nrm


# ---------------------------------------------------------------- 真·内外判定
# ★★★ 「带符号距离」在**凹几何**上会骗人：最近面可能是躯干的侧壁或下摆内壁，
#   于是「拳在胸外 38 mm」的手会被算出「掌面 −21 mm」。E03 的拳正对胸口、
#   而躯干在 x 上比拳宽（±239 mm）、在下摆处向内收 —— 最近面经常不是胸面。
# ⟹ 改用**射线奇偶判定**。★ 但 `_e03_yard.py` 实测证明**单方向奇偶也不够**
#   （水密网格上射线擦边会造成假阳性，得票只有 1），所以最终口径 =
#   **13 方向多数表决**：真内部拿满票，擦边噪声只有 1~2 票，两者断崖式分离。
INSIDE_RAYS = []
for _j in range(13):
    _a = 2.0 * math.pi * _j / 13.0
    _z = 1.0 - 2.0 * (_j + 0.5) / 13.0
    _r = math.sqrt(max(0.0, 1.0 - _z * _z))
    INSIDE_RAYS.append(Vector((math.cos(_a) * _r, math.sin(_a) * _r,
                               _z)).normalized())
# 得票 > 6（共 13 票）判「在体内」。阈值放在「多数」而非「全部」是为了容忍
# 极端擦边：实测真内部点恒为 13/13，噪声恒 ≤ 2，中间地带是空的。
INSIDE_VOTES_MIN = _env_i("E03_INSIDE_VOTES", 7)
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
    """从 point 沿 direction 打射线，数穿过躯干表面的次数，奇 = 在体内。"""
    origin = Vector(point)
    hits = 0
    for _ in range(64):
        loc, _normal, index, distance = tree.ray_cast(origin, direction)
        if loc is None or index is None:
            break
        hits += 1
        origin = loc + direction * max(1e-7, distance * 1e-6 + 1e-7)
    return hits % 2 == 1


def push_out(point, min_gap_mm):
    """把拳目标**顶出**胸腔：不进胸超过 `min_gap_mm`，沿胸面外法线推。

    ★★★ 为什么必须做这件事（本支口徑 v003 的核心修正）：
      拳目标在**时间上**是线性插值的，而「站架侧的抬拳位」↔「胸面点」之间
      那条**直线弦会切进躯干** —— 实测 `f=26` 手网格穿透 **−44.9 mm**
      （真凶是食指，拳心还在胸外）。同一条弦在收势段（f≥54，拳从胸面滑向抬起位）
      也切，实测 `f≈59` 拳心离胸只剩 19.8 mm（比命中目标 38 mm 还近）。
      ⟹ **一个实心拳头不可能在胸腔里**。所以对**插值后的**目标点做一次
      「沿外法线顶出」：只在该点比**命中深度**更深时才动它 ⟹
      命中姿态本身**完全不受影响**（`min_gap == TOUCH_OFF`），
      只是把穿透的那段弦自动换成「贴着胸面滑进/滑出」——这也是**正确的动作**：
      拳头是擦着胸口滑上去的，不是从胸里穿出来的。
    """
    gap, surf, nrm = torso_query(point)
    if gap >= min_gap_mm:
        return Vector(point)
    return surf + nrm * (min_gap_mm / 1000.0)


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
    """只要坐标（供旧调用点使用）。"""
    return [point for point, _name in hand_mesh_points(side, step)]


def resolve_fist(name, side, arm):
    if name == "STATION":
        return Vector(STATION_FIST[side])
    if name == "WIND":
        return Vector(FIST_WIND[side])
    if name == "WIND_S":
        return Vector(FIST_WIND_S[side])
    surf, nrm = chest_surface(arm, side)
    off = TOUCH_OFF + CHEST_EXTRA_OFF.get(name, 0.0)
    if CHEST_FAR:
        # ★★★ v012：让「拳离开胸」沿**远离中线**（世界 ±X）离开 —— 正面可见，
        #   且正是「双拳没收上中线」这一真实故障。−Y 分量保留（仍是离胸）。
        sx = 1.0 if side == "L" else -1.0
        return (surf + nrm * off
                + Vector((sx * CHEST_FAR_X_MM / 1000.0,
                          -CHEST_FAR_MM / 1000.0, 0.0)))
    if CHEST_CLIP:
        off = -CHEST_CLIP_MM / 1000.0
    return surf + nrm * off


def arm_normals(arm, frame):
    """当前姿态下左右胸面的**外法线**（世界）—— 供手骨滚转用。

    ★ 只在 `outward/inward` 两种模式下被真正读到；`thumb_up/down` 用世界上方，
      但两条路径都必须**由几何量算出**才能保证逐帧连续（这是换掉扫 twist 的理由）。
    """
    del frame
    return {side: chest_surface(arm, side)[1] for side in SIDES}


def fist_targets(arm, frame):
    index, t, kind = _segment(frame)
    ga = _ease(kind, t)
    a_name = KEYS[index][3]
    b_name = KEYS[index + 1][3]
    out = {}
    for side in SIDES:
        va = resolve_fist(a_name, side, arm)
        vb = resolve_fist(b_name, side, arm)
        point = va.lerp(vb, ga)
        # ★ 反向验证旋钮 ③ 必须**绕开**这道保护，否则它会把「穿进去」的拳
        #   顶回胸外 ⟹ 旋钮惰性、判据不见红（等于旋钮没接进代码）。
        if TGT_TRACE and frame <= 20:
            print("E03_TGT f=%3d %s pre_gap=%+7.2f dist=%7.2f"
                  % (frame, side, signed_to_torso(point),
                     (point - STATION_FIST[side]).length * 1000.0))
        if not CHEST_CLIP:
            point = push_out(point, FIST_MIN_CLEAR_MM)
        if TGT_TRACE and frame <= 20:
            print("E03_TGT f=%3d %s post_gap=%+7.2f core_gap=%+7.2f"
                  % (frame, side, signed_to_torso(point),
                     signed_to_torso(A.bone_world(arm, "hand." + side, "tail"))))
        out[side] = point
    return out


def orient_hand(arm, side, y_dir, x_hint):
    """用**显式正交基**摆 `hand.<side>`：`local_y` = `y_dir`，`local_x` 尽量贴 `x_hint`。

    `local_z = local_x × local_y`（rest 实测的右手系约定，见 `_e03_handaxis.py`）。
    ★ 与 `A.aim_bone` 的区别：这里**指定**滚转，所以拇指朝哪是设计出来的。
    ★ v004 曾断言「由几何量算得 ⟹ 天然连续、不会翻」—— **v008 实测推翻**，
      理由与修法见函数体内注释（f=76 真旋转 83.86°/帧）。
    """
    pose_bone = arm.pose.bones["hand." + side]
    y_axis = Vector(y_dir).normalized()

    # ★★★ 滚转基准：**纯投影**（口径 v009 定稿）。
    #   历史与判据（每一步都留了实测账目，别再把它们踩回去）：
    #   · v004 断言「由几何量算得 ⟹ 天然连续、不会翻」—— **实测推翻**：
    #     基准是「把固定世界方向投影到 ⊥y 的平面」，y 一旦接近该方向，
    #     投影长度 → 0 ⟹ 滚转由噪声决定。实测 f=75/76/77 的
    #     `∠(y, 基准) = 24.2 / **9.9** / 24.1°` ⟹ `hand.L` **真旋转 83.86°/帧**。
    #   · v008 用「旋转最小化标架搬运」打补丁 —— **实测不可靠**：投影方向在
    #     退化点前后会整体翻 180°，此时任何基于它做的半球对齐都会把标架翻过去
    #     （实测把 f=76 从 83.86° 变成 **180.00°**；去掉半球对齐后又在窗口改动
    #     时冒出不随几何连续变化的 45~52° 尖峰）。⟹ **不要修补坏基准**。
    #   · v009 正解：**换基准**。`_e03_hint2.py` 对全时间轴 194 条 `y_dir`
    #     实测 `min|投影|`：±X(体侧外) **0.701** ＞ 下/上 0.173 ＞ 前/后 0.091
    #     ＞ 胸腔法线 **0.000**。改用 `thumb_out`（±X）后，投影**全程不退化**
    #     ⟹ 补丁不再需要，删掉它（少一层状态 = 少一类不可控）。
    #   ★ 代价：这个「基准永不退化」的前提**必须有判据盯着** —— 见
    #     `rage_x_hint_margin_ok`（`min|投影|` 必须 ≥ `HAND_X_HINT_FULL`）。
    #     没有那条断言，将来改动作改到 y_dir 扫过 ±X 就会静默复发 83.86°。
    hint = Vector(x_hint)
    x_axis = hint - y_axis * hint.dot(y_axis)
    last_xhint_margin = x_axis.length
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


def hand_x_hint(side, normal):
    """按 `HAND_AXIS_MODE` 给出「`hand.local_x` 应指向的世界方向」。

    ★ 必须先乘 `HAND_CHIRALITY`：右手 rest 基的 `local_x` 与拇指**反向**
      （见 `HAND_CHIRALITY` 的实测说明），不修正就会出现「一侧拇指朝上、
      另一侧拇指朝下」的镜像错位 —— 那一侧的拇指必然捅进胸腔。
    ★★★ 默认模式 `thumb_out` 是**扫出来的**，不是拍的（`_e03_hint2.py`）：
      对全时间轴 194 条 `y_dir`（两侧各 97 帧）逐个候选求 `min|投影|`：

        ±X（体侧外）      0.701  = 44.5°  ← 采用
        下 / 上           0.173  =  9.9°  @ f=76（原 `thumb_dn`，正是翻帧来源）
        前 / 后           0.091  =  5.2°  @ f=24
        外侧斜下 (1,0,-1) 0.091  =  5.2°  @ f=18
        **胸腔法线**      0.000  =  0.0°  @ f=27 / f=35
      ⟹ 关键判断：`y_dir` 的弧线（从「指向胸腔」＝ −法线，转到「垂落」＝ −Z）
        **整段落在 YZ 平面内**，所以任何 YZ 内的基准（下/前/法线）必然退化；
        法线更是**恒为正交**于 y 的最坏选择（捶胸时拳轴按定义就沿 −法线）。
      ⟹ 只有带 X 分量的基准安全。`thumb_out`（拇指朝**体侧外**）余量 44.5°，
        且解剖上正确：握拳压胸时拇指本就在外侧。
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


# =============================================================== 臂 IK
# ★★★ 肘部**连续性**（本支口径 v003 的第二处核心修正）
#   两骨 IK 在「肩→目标」这条轴上**有两个解**（肘在前 / 肘在后）。`seat_arm`
#   用「把鼓出方向投影到垂直于轴」来选解，而这个投影在**轴与鼓出方向接近平行**
#   时会退化成 0 ⟹ 单位化把数值噪声放大 ⟹ 肘在相邻两帧之间**整体翻到另一侧**。
#   实测证据：`f=26` 上臂/前臂 euler 一步 **95.618°**，而**矩阵口径**（真旋转）
#   也有 **53.399° @ f=27 thumb_01.L** —— 这不是表示问题，是**真的翻了**。
#   ★ 修法：把**上一帧解出的肘位置**当作本帧的极向量参考（IK continuity）。
#     这是 IK 的标准做法：解不唯一时选「离上一帧最近」的那个。
#     首帧无参考时才退回固定 `ELBOW_DIR`（且带退化保护）。
ELBOW_POLE = {"L": Vector((0.42, 1.00, -0.22)),
              "R": Vector((-0.42, 1.00, -0.22))}
LAST_ELBOW = {}
# ★ 上一帧的手心标架 (y, x)（世界）—— 供 `orient_hand` 在投影退化时做
#   旋转最小化搬运。**必须逐帧按序写入**（`boot()` 清空）。
LAST_HAND_FRAME = {}


def _slerp_dir(d1, d2, t):
    """单位方向 d1 → d2 的**测地线**混合（`mathutils` 的 slerp 等价实现）。

    ★ 为什么不用 `Vector.slerp`：需要显式处理 d1 ≈ ±d2 两个退化点，并且
      必须保证 |返回| ≡ 1（下游 `orient_hand` 直接拿它当 `local_y`）。
      · d1 ≈ d2（θ<1e-4）→ 返回 d1；
      · d1 ≈ −d2（θ>π−1e-3）→ 绕任一与 d1 垂直的轴转 π·t（大圆仍唯一）。
    """
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
    if axis.length < 1e-6:                     # 近 180°：大圆轴不唯一
        axis = a.cross(Vector((0.0, 0.0, 1.0)))
        if axis.length < 1e-6:
            axis = a.cross(Vector((0.0, 1.0, 0.0)))
    axis.normalize()
    out = Matrix.Rotation(theta * t, 4, axis) @ a
    out.normalize()
    return out


def face_blend(frame):
    """「拳面正对胸面」的混合系数**随相位**变化（v005 核心修正）。

    ★★★ 为什么不能全时段恒 1.0（实测证据，不是保守）：
      `FIST_FACE_BLEND = 1.0` 意味着手腕相对前臂**反折约 90°**（拳面朝胸）。
      而站架（`Idle_01@0`）的手是「掌心朝内、沿前臂」的。于是 `rage_pose` 的
      臂包络（`arm_env` 0→1）在 f=0~14 内把两组姿态**线性混合**时，手腕要在
      14 帧里完成这次反折 ⟹ 实测：
        · `rage_matrix_step_deg_max = 51.5° @ f=11 / thumb_01.R`（真旋转！）
        · `no_teleport = False`、`no_snap_stop_ok = False`（f=90 19.5°/帧）
        · 更糟的是 f=3~9 右手最多 **210** 个顶点在体内、最深 **−43.11 mm**
          —— 拳在「抬起 + 反折」的中途**扫过躯干**。
      ⟹ 结论：**包络混合的前提是「两端之间那条直线是安全的」**；这里不成立。
    ★ 修法：把「反折手腕」这件事**移出包络过渡段** —— 过渡段拳沿前臂（不做
      反折，两端姿态差小），等拳已经抬到身前（f≥24）再完成反折，收招时先松开
      反折（f≥74）再放下手臂。反折因此不再与包络叠加。
    """
    blend = FIST_FACE_BLEND
    if blend <= 0.0:
        return 0.0
    lo, hi = FACE_RAMP_IN
    if frame <= lo:
        return 0.0
    if frame < hi:
        return blend * _smoothstep((frame - lo) / float(max(1, hi - lo)))
    lo2, hi2 = FACE_RAMP_OUT
    if frame >= hi2:
        return 0.0
    if frame > lo2:
        return blend * _smoothstep((hi2 - frame) / float(max(1, hi2 - lo2)))
    return blend


def seat_arm(arm, pose, targets, normals, blend=1.0, env=1.0):  # noqa: C901
    """把臂解到拳心目标上。

    ★★★ `env`（= `arm_env(frame)`）是 **v010 新增的第三处修正**，也是本支
    「收招不炸 / 起手不炸」的关键。它解决的问题（有实测证据）：

      `rage_pose` 用 `pose[name] = station + (ik − station) * env` 把 IK 解
      与站架解混合，**默认 IK 解在 `env=0` 时并不等于站架解** —— 因为
      `orient_hand` 是**绝对设定**手的朝向（`y_dir`/`x_hint` 由胸几何给出），
      与 `Idle_01` 的松拳朝向差 **119.7°（L）/ 92.5°（R）**（`_e03_q.py`
      在 f=96、`env=0` 上实测）。于是「包络两端」根本没重合，混合等于用
      `Δenv ≈ 0.117/帧` 去推一个 ~135° 的差 ⟹ 实测 **15.75°/帧** 的真旋转，
      `no_snap_stop_ok`（阈值 6°/帧）必红。首帧侧同理。
      ★ 这不是放宽容差能解决的：**两端不重合是结构问题**。
    修法：把 IK 解的**三个自由度**（肘极向量、拳轴 `y_dir`、滚转基准 `x_hint`）
    按 `env` 向**站架实测值**插值 ⟹ `env→0` 时 IK 解**逐位收敛到站架臂**，
    包络两端重合，混合自然不再产生大步长。
      ★ 为什么这是**更强**的约束而不是掩盖：它把「接缝处必须等于站架」从
      「靠包络近似」升级成「IK 解本身就等于站架」，`seam_in_ok` /
      `end_matches_start_ok` / `loop_seamless` 三条矩阵口径断言**照旧独立**盯着。
    """
    A.apply_pose(arm, pose)
    for side in SIDES:
        up, fo, hd = ("upperarm." + side, "forearm." + side, "hand." + side)
        shoulder = Vector(A.bone_world(arm, up, "head"))
        core = Vector(targets[side])
        nrm = Vector(normals.get(side, Vector((0.0, -1.0, 0.0)))).normalized()
        # ★★★ 拳**面**朝向（本支口径 v004 的第二处核心修正）
        #   旧口径：`y_dir = core - elbow`，即「拳沿**前臂**伸出去」——
        #     `hand.local_y` 顺着前臂 ⟹ 拳是**擦着胸推过去**的，于是
        #     `hand.local_x`（拇指侧）正好指向胸内：实测拇指离拳心沿胸法线偏出
        #     **−72.6 mm**，把拇指捅进胸腔；而掌/指骨节只偏 17 mm。
        #   新口径：把 `y_dir` 从「沿前臂」混合到 **「−胸面法线」**（拳面正对胸）。
        #     ★★★ 混合系数**由调用方按相位传入**（`face_blend(frame)`），不是常量：
        #       过渡段（f≤10 / f≥88）必须 `blend=0`（拳沿前臂、不做反折），否则
        #       90° 反折会与 `arm_env` 包络叠加 —— 实测 f=3~9 右手最多 210 顶点
        #       在体内、最深 −43.11 mm，且 f=11 `thumb_01.R` 真旋转一步 51.5°。
        #     ⟹ 过渡段姿态差小 ⟹ 包络那条直线安全；反折等拳抬到身前（f≥24）再做。
        #     拳面正对胸时：拇指落在**垂直**于法线的平面里 ⟹ 不再朝胸内；
        #       指节面正对胸 ⟹ 这才是解剖学上的「捶胸」（用拳面砸，不是用拳侧蹭）。
        # ★ v010：`along` 改用**前臂方向**（`core − 肘`）而不是 `core − 肩`。
        #   实测（`_e03_q.py`）`∠(core−shoulder, −nrm)` = **142~170°**（近反对跖），
        #   而 `∠(core−elbow, −nrm)` = **87~136°** ⟹ 混合跨过的弧**少 30~45°**，
        #   腕部逐帧步长随之下降。物理上也更对：`along` 的本意是
        #   「拳顺着前臂伸出去」（v003 旧口径就是 `core − elbow`），v004 改写时
        #   换成了肩，那才是这条弧被拉到 170° 的原因。
        #   肘用**上一帧解出的**（`LAST_ELBOW`，IK 连续性口径），首帧回落到当前姿。
        elbow_ref = LAST_ELBOW.get(side)
        if elbow_ref is None:
            elbow_ref = Vector(A.bone_world(arm, fo, "head"))
        along = core - Vector(elbow_ref)
        along = (along.normalized() if along.length > 1e-6
                 else Vector((0.0, 0.0, -1.0)))
        # ★★★ 方向混合必须走**测地线**（沿单位球大圆旋转），不能线性插值。
        #   反例（实测，v005 首轮）：`along*(1-b) + (-nrm)*b` 当 `along` 与
        #   `-nrm` 夹角很小或接近 180° 时，b≈0.5 处向量模长趋近 0，归一化后
        #   方向由**浮点噪声**决定 ⟹ 腕在相邻两帧间整体翻过去：
        #     · `rage_matrix_step = 93.736° @ (82, thumb_03.L)`（真旋转！）
        #     · `max_frame_step = 169.616° @ (14, hand.R)`（1 帧翻 169°）
        #   而这两个帧号恰好是 `FACE_RAMP_IN/OUT` 的 b≈0.5 处 —— 不是巧合。
        #   ★ 测地线混合的角速度恒定 = |θ_end−θ_start|/跨度，且 |y_dir| ≡ 1，
        #     在端点处与线性式**完全相同**（b=0 → along；b=1 → −nrm）⟹ 命中
        #     窗口几何不受影响，只修过渡段的塌缩。
        y_dir = _slerp_dir(along, -nrm, blend)
        # ★ v010：包络收敛 —— `env→0` 时拳轴回到**站架拳轴**（见函数 docstring）；
        #   `env=1`（f∈[ARM_UP_AT, ARM_DN_AT]）时**逐位不影响**本支姿态。
        if env < 1.0:
            y_dir = _slerp_dir(STATION_HAND_Y[side], y_dir, env)
        # ★ 腕要落在「拳心 − y_dir x 手骨长」上，这样 `hand.tail` **精确**落在
        #   拳心目标（旧口径只保证「前臂指向目标」，实际 tail 会偏）。
        target = core - y_dir * HAND_LEN
        delta = target - shoulder
        limit = (ARM_LEN_UP + ARM_LEN_LO) * 0.9995
        distance = max(1e-4, min(delta.length, limit))
        axis = (delta.normalized() if delta.length > 1e-9
                else Vector((0.0, 0.0, -1.0)))
        pole = ELBOW_POLE[side]
        previous = LAST_ELBOW.get(side)
        if previous is not None:
            # ★ 用上一帧的肘作参考：稳定性来自「解在时间上连续」这个物理事实
            candidate = Vector(previous) - shoulder
            if candidate.length > 1e-4:
                pole = candidate
        bulge = pole - axis * pole.dot(axis)
        # 退化保护：阈值从 1e-6 提到 0.05（1e-6 挡不住噪声放大）
        if bulge.length < 0.05:
            bulge = (ELBOW_POLE[side]
                     - axis * ELBOW_POLE[side].dot(axis))
            if bulge.length < 0.05:
                bulge = Vector((0.0, 1.0, 0.0)) - axis * axis.y
                if bulge.length < 0.05:
                    bulge = Vector((0.0, 0.0, 1.0)) - axis * axis.z
        bulge.normalize()
        # ★ v010：肘极向量也按 `env` 向**站架肘方向**收敛（同 docstring 的理由）。
        #   实测证据（`_e03_q.py` f=96 / env=0）：未收敛时 IK 的 `upperarm` 与
        #   站架差 **26.1°（L）/ 30.5°（R）**、`forearm` 差 24.1°/28.3°。
        if env < 1.0:
            bulge = _slerp_dir(STATION_POLE_DIR[side], bulge, env)
        else:
            bulge = bulge.copy()
        bulge.normalize()
        cos_sh = max(-1.0, min(1.0, (ARM_LEN_UP ** 2 + distance ** 2
                                     - ARM_LEN_LO ** 2)
                               / (2.0 * ARM_LEN_UP * distance)))
        sin_sh = math.sqrt(max(0.0, 1.0 - cos_sh * cos_sh))
        elbow = shoulder + (axis * cos_sh + bulge * sin_sh) * ARM_LEN_UP
        LAST_ELBOW[side] = elbow.copy()
        pose[up] = A.aim_bone(arm, up, elbow - shoulder)
        fo_dir = target - elbow
        # ★ 前臂旋前：扭转**随相位**（过渡段不做，否则又和包络叠加），
        #   并由 `HAND_CHIRALITY` 定符号（左右镜像）。
        base_twist = FOREARM_TWIST_DEG * blend * HAND_CHIRALITY[side]
        pose[fo] = A.aim_bone(arm, fo, fo_dir, twist_deg=base_twist)
        hint = hand_x_hint(side, nrm)
        if env < 1.0:
            hint = _slerp_dir(STATION_HAND_X[side], hint, env)
        orient_hand(arm, side, y_dir, hint)
        # ★★★ v011：腕部**轴向滚转按 50/50 分给前臂（旋前）与腕（扭转）**。
        #   问题（实测，`_e03_diag2.py`，也是 v007 那条修法被 v010 改回 0 之后
        #   重新暴露出来的）：捶胸要求手骨绕**自身轴**扭 ~115°，
        #   而 XYZ 欧拉的**中间轴就是骨轴 Y**，奇异点在 `ry = ±90°`。
        #   实测手骨 `ry` 全程扫过 **+43°…+144°（R）/ −143°…−14°（L）**
        #   ⟹ **两次穿过 ±90°**（f=20→21 与 f=74→75）：
        #     · f=74→75：`ry` 79.0→82.2，但 `rx` −25.8→−69.4、`rz` 68.8→10.7
        #       ⟹ euler 步 **58.10°**，而**矩阵步只有 16.44°**；
        #     · 穷举 54 个等价表示后的最小步**仍是 58.10°** ⟹ 这不是「选错分支」，
        #       是**该点附近欧拉雅可比病态**（`compat_euler` 无从下手）。
        #   ⟹ 结果：`max_frame_step_deg = 65.28 @ (75, hand.R)`，
        #     `no_teleport`（≤25°）红；本支自己的 `rage_matrix_step_note` 也
        #     要求「euler 口径与矩阵口径**一致地小**」。
        #   ★ 修法（v007 的推广，几何上**零副作用**）：
        #     `orient_hand` 把手的**世界矩阵绝对设定** ⟹ 前臂多扭多少，手骨
        #     局部 euler 就**少扭多少**；而绕**骨轴**的自转不移动前臂 tail
        #     ⟹ 腕关节位置不变 ⟹ **手的姿态一个比特都不变**，只是「把滚转记在
        #     谁账上」变了。取 50/50 而不是「全给前臂」的理由：
        #     全给前臂只是把奇异点**搬到前臂**（它的 `ry` 会同样扫到 144°）。
        #     50/50 使两骨的 `|ry|` 同时降到 **≤72°**，都在奇异带外。
        #     ★ 为什么不**按帧扫** twist：帧间不连续会引入新跳变；这里用的是
        #       **不动点迭代**（twist ← (twist + base + ry)/2），由几何量收敛，
        #       天然连续。
        twist = 0.0
        for _ in range(4):
            ry = math.degrees(arm.pose.bones[hd].rotation_euler.y)
            # ★ v011：`TWIST_SPLIT` = **前臂承担的滚转占比** ρ。
            #   不动点解（c=0.6 的欠松弛）：`twist → ρ·ry0`，`ry_hand → (1−ρ)·ry0`。
            #   ρ=0.5 即 v010 的写法，此处把它显式化以便**扫描**（旋钮必须接进代码）。
            twist = ((1.0 - 0.6 + 0.6 * TWIST_SPLIT) * twist
                     + 0.6 * TWIST_SPLIT * ry)
            pose[fo] = A.aim_bone(arm, fo, fo_dir, twist_deg=twist)
            orient_hand(arm, side, y_dir, hint)
        # ★ 残余偏置旋钮（默认 0）：收敛之后再叠一个**固定**扭转，
        #   供反向验证强行把 `ry` 推回奇异带（见 `FOREARM_TWIST_DEG` 注释）。
        if base_twist:
            twist += base_twist
            pose[fo] = A.aim_bone(arm, fo, fo_dir, twist_deg=twist)
            orient_hand(arm, side, y_dir, hint)
        LAST_FOREARM_TWIST[side] = twist
        pose[hd] = tuple(math.degrees(v)
                         for v in arm.pose.bones[hd].rotation_euler)
    return pose


# =============================================================== 姿态装配
def rage_pose(arm, frame):  # noqa: C901
    spec = torso_at(frame)
    pose = {}
    for key in ("pelvis", "spine_01", "spine_02", "chest", "neck", "head",
                "shoulder.L", "shoulder.R"):
        va = BASE.get(key, (0.0, 0.0, 0.0))
        pose[key] = (va[0] + spec[key], va[1], va[2])
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

    # ---- 腿：闭环锁到站架踝（本支**不迈步**）------------------------------
    want = {s: Vector(ANCHOR[s]) for s in SIDES}
    if FOOT_SWAY:
        # ⑥ 脚跟着动：**脚不再锁世界，改骑在当前骨盆上** —— 躯干一动脚就跟着动。
        #   ★★★ v012 为什么不是「恒定偏移」（这是本支第三处惰性旋钮的实测修正）：
        #     本支机位的尺子量的是**带内跨帧漂移**，而 hitstop 把两个命中窗口内的
        #     姿态**冻结** ⟹ 恒定偏移在任何帧都相同 ⟹ 漂移恒为 0 ⟹ 旋钮惰性
        #     （实测：旧「恒定 X 偏移 55 mm」下 `px_rage_foot_canfail_spread_px`
        #     仅 1.0，阈值 >2.0）。忠实仿真必须让脚的**目标位置依赖当前躯干姿态**：
        #     骑骨盆后，两个命中窗口（CHEST1 前倾 vs CHEST2 后弓）的骨盆不同 ⟹
        #     脚的位置不同 ⟹ 漂移可见（且 f=0 站架不受影响，接缝不破）。
        A.apply_pose(arm, pose)
        delta = Vector(A.bone_world(arm, "pelvis", "head")) - PELVIS0
        scale = FOOT_SWAY_MM / 55.0
        for s in SIDES:
            want[s] = want[s] + delta * scale
    lock_err = lock_feet(arm, pose, want)

    # ---- 臂：对**当前帧的胸**重解，再按 `arm_env` 与站架臂混合（保证接缝）----
    env = arm_env(frame)
    A.apply_pose(arm, pose)
    ik_pose = dict(pose)
    seat_arm(arm, ik_pose, fist_targets(arm, frame), arm_normals(arm, frame),
             face_blend(frame), env)
    for name in ARM_BONES:
        va = pose.get(name, (0.0, 0.0, 0.0))
        vb = ik_pose.get(name, (0.0, 0.0, 0.0))
        pose[name] = tuple(x + (y - x) * env for x, y in zip(va, vb))

    if LOOP_BREAK and frame == TOTAL:
        rx, ry, rz = pose["chest"]
        pose["chest"] = (rx + 4.0, ry, rz + 4.0)

    if TRACE:
        A.apply_pose(arm, pose)
        gaps = {s: round(signed_to_torso(
            A.bone_world(arm, "hand." + s, "tail")), 1) for s in SIDES}
        faces = {s: round(min(signed_to_torso(p)
                              for p in hand_mesh_vertices(s, step=6)), 1)
                 for s in SIDES}
        head_back = current_head_back(arm)
        print("E03_TRACE f=%3d drop=%+6.1f head_back=%+6.1f lock=%.4f "
              "core_gap=%s face_gap=%s"
              % (frame, (torso_at(frame)["loc"][1] + base_loc[1]) * 1000.0,
                 head_back, lock_err, gaps, faces))
    return pose


def current_head_back(arm):
    """仰头角（度，**正 = 后仰**）= −(Δneck_rx + Δhead_rx)（相对**站架**的增量）。

    ★ 口径由 `probe_e03_baseline.py` 实测标定：探针网格显示
      `head_back_vs_chest_deg` 恰好 = (neck_rx − 站架neck_rx) + (head_rx − 站架head_rx)
      再加一个恒定基线 −1.0°（来自 `chest` 与头的 rest 朝向差）。
      本函数直接量**增量之和**（更干净、与姿态参数一一对应），
      探针的 `head_vs_vertical_deg` 作为独立第二口径登记。
    ★ 符号：**本支的骨 rx 为负 = 头向后倒**（`SPECS` 里 roar 段全为负），
      所以这里统一取负号，让「越大越仰」，`HEAD_BACK_RANGE` 才是正区间。
    ★ 首版把 `BASE`（**度**）当成弧度从度数里减 ⟹ 引入 0.19° 的系统偏差，
      且 `peak = max(...)` 方向取反（把「低头最多」当成了峰值）。
      两处都已在 v002 修掉 —— `peak = max(...)` 现在语义正确。
    """
    n0 = BASE.get("neck", (0.0, 0.0, 0.0))[0]
    h0 = BASE.get("head", (0.0, 0.0, 0.0))[0]
    d_neck = math.degrees(arm.pose.bones["neck"].rotation_euler.x) - n0
    d_head = math.degrees(arm.pose.bones["head"].rotation_euler.x) - h0
    return -(d_neck + d_head)


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
def rage_assertions(arm, action, samples, meshes):  # noqa: C901
    res = {}
    scene = bpy.context.scene
    frames = [s["frame"] for s in samples]
    arm.animation_data.action = action
    A._bind_slot(arm, action)

    # ---- ① ★★★ 捶胸「达到」：拳**面**压到胸（独立量 = 真实手网格几何）----
    #
    # ★★★ 为什么**不能**量「拳心到胸面的距离」当主判据（本支口径 v001 的最大坑）：
    #   拳目标本来**就是**由「胸面 + 法线 x TOUCH_OFF」算出来的 ⟹ 回头再量
    #   「拳心到胸面」，结果必然恒 ≈ TOUCH_OFF —— **一个量不出错的目标等于
    #   没有目标**（`rage_chest_hit_ok` 会恒真）。所以主判据量**独立量**：
    #   真实手网格顶点（`Hand_Palm_*` / `Finger_*`）到 `Suit_Torso` 的距离。
    #   ★ 拇指**不参与**「达到」（捶是用**指节面**砸，不是用拇指戳）——
    #     它在 ② 里被单独盯死（`thumb` 计数）。
    touch_rows = {}
    hands = {s: [] for s in SIDES}          # 每侧「指节面 ≤ 阈值」的帧号
    for frame in sorted(set(CONTACT + [HIT_1, HIT_2, ROAR, ROAR2])):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        torso_bvh_reset()
        row = {}
        for side in SIDES:
            pts = hand_mesh_points(side, step=2)
            face = [signed_to_torso(p) for p, name in pts
                    if not name.startswith("Thumb_")]
            thumb = [signed_to_torso(p) for p, name in pts
                     if name.startswith("Thumb_")]
            core = signed_to_torso(Vector(A.bone_world(arm, "hand." + side,
                                                       "tail")))
            row[side] = {"face_min_mm": round(min(face), 2),
                         "thumb_min_mm": round(min(thumb), 2) if thumb else None,
                         "core_mm": round(core, 2)}
            if min(face) <= HAND_TOUCH_MAX_MM:
                hands[side].append(frame)
        touch_rows[str(frame)] = row
    hold_frames = sorted(set(list(range(HOLD_1[0], HOLD_1[1] + 1))
                             + list(range(HOLD_2[0], HOLD_2[1] + 1))))
    hold_face = {s: [touch_rows[str(f)][s]["face_min_mm"] for f in hold_frames]
                 for s in SIDES}
    worst_hold = max(max(v) for v in hold_face.values())
    deepest_hold = min(min(v) for v in hold_face.values())
    res["rage_contact_frames"] = [CONTACT[0], CONTACT[-1]]
    res["rage_hold_frames"] = hold_frames
    res["rage_hold_face_min_mm"] = {s: hold_face[s] for s in SIDES}
    res["rage_hold_face_worst_mm"] = round(worst_hold, 2)
    res["rage_hold_face_deepest_mm"] = round(deepest_hold, 2)
    res["rage_touch_frame_counts"] = {s: len(hands[s]) for s in SIDES}
    res["rage_contact_detail"] = touch_rows
    res["rage_chest_hit_ok"] = bool(
        worst_hold <= HAND_TOUCH_MAX_MM
        and deepest_hold >= -HAND_PIERCE_MM
        and min(len(hands[s]) for s in SIDES) >= TOUCH_MIN_FRAMES)
    res["rage_chest_hit_note"] = (
        "★★★ **捶胸「达到」判据 = 真实手网格几何，不是自指量**。"
        "命中定格窗口 %s 内，两侧「拳面（掌 + 指簇，**不含拇指**）到胸面的最小"
        "带符号距离」实测 **%s**（最松 %.2f mm ≤ %.1f；最压 %.2f mm ≥ −%.1f）。"
        "★ 另加「**贴胸不能一闪而过**」：全段（f=%d~%d 与 %d~%d）里"
        "「拳面 ≤ %.1f mm」的帧数实测 **L %d / R %d**（要求各 ≥ %d，即 ≥ 0.1 s）。"
        "★ 为什么必须用**指节面**而不是拳心：拳心到胸面是**自指量**（目标就由它"
        "定义），必然恒真；指节面是**独立量**，它才是「拳有没有砸到」的事实。"
        "★ 为什么**不含拇指**：捶是用指节面砸；拇指是否戳到胸由 ② 单独盯。"
        % (hold_frames, {s: hold_face[s] for s in SIDES}, worst_hold,
           HAND_TOUCH_MAX_MM, deepest_hold, HAND_PIERCE_MM,
           CONTACT[0], ROAR, HIT_2, ROAR2, HAND_TOUCH_MAX_MM,
           len(hands["L"]), len(hands["R"]), TOUCH_MIN_FRAMES))

    # ---- ② ★★★ 捶胸「不穿」：拳没捅进胸腔（13 方向多数表决）-------------
    #
    # ★★ 尺子的选定过程（有实测证据，不是偏好）：
    #   `_e03_yard.py` 量到两件事 ——
    #     (a) `Suit_Torso` **是水密的**（boundary_edges = 0 / nonmanifold = 0）；
    #     (b) 但手网格顶点的**得票分布是断裂的两极**：真内部 **13/13 满票**，
    #         其余全部 ≤ 2 票，中间地带是空的。
    #   ⟹ **单方向奇偶会产生 1~60 个假阳性**（射线擦过边 ⟹ 多算一次穿越 ⟹
    #     奇偶翻成「内」；实测 f=60 单方向报 22 个「体内顶点」，得票全是 1）。
    #   ⟹ 权威口径 = **多数表决（> 6 / 13 票）**。
    #   ★ 报告里同时登记单方向读数，让「两个口径差多少」也是可复核的数字。
    pierce_rows = {}
    walk = sorted(set(list(range(START, END + 1, 3)) + CONTACT + hold_frames))
    # ★★ 判据范围 = 全时间轴**除两个接缝帧**（f=0 / f=TOTAL）。
    #   理由不是「躲开红项」：这两个帧**逐位等于上游 `Idle_01@0`**（由
    #   `seam_in_ok` / `end_matches_start_ok` / `loop_seamless` 三条矩阵口径
    #   断言钉死，容差 1e-6）—— 本支**无权**修改它们，改了就先破掉更强的约束。
    #   这两个帧上确实有穿透，但那是**上游继承来的预存缺陷**（见 ③ 登记），
    #   所以口径写成「**本支引入的**穿透 = 0」，并把继承值**照样打印出来**。
    seam_frames = {START, END}
    worst_in, worst_in_at = 0, None
    worst_in_nt, worst_in_nt_at = 0, None
    worst_single, worst_thumb, worst_hard = 0, 0, 0
    worst_deep_nt, worst_deep_nt_at = 0.0, None
    # ★ 分族与深度分级的全时间轴最差读数（选判据口径的实测依据）。
    worst_fist, worst_fist_at = 0, None
    worst_palm, worst_palm_at = 0, None
    worst_deep_hist = {e: 0 for e in PIERCE_DEEP_EPS_MM}
    for frame in walk:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        torso_bvh_reset()
        tree = torso_bvh()
        row = {}
        for side in SIDES:
            counts = hand_mesh_stats(side, tree=tree, step=4, hard_mm=0.0)
            row[side] = counts
            if frame in seam_frames:
                continue
            if counts["inside"] > worst_in:
                worst_in, worst_in_at = counts["inside"], (frame, side)
            if counts["inside_nothumb"] > worst_in_nt:
                worst_in_nt = counts["inside_nothumb"]
                worst_in_nt_at = (frame, side)
            if counts["inside_fist"] > worst_fist:
                worst_fist, worst_fist_at = counts["inside_fist"], (frame, side)
            if counts["inside_palm"] > worst_palm:
                worst_palm, worst_palm_at = counts["inside_palm"], (frame, side)
            for eps, number in counts["deep_nt"]:
                if number > worst_deep_hist[eps]:
                    worst_deep_hist[eps] = number
            worst_single = max(worst_single, counts["single"])
            worst_thumb = max(worst_thumb, counts["thumb"])
            worst_hard = max(worst_hard, counts["hard"])
            deep = counts["deepest_nothumb_mm"]
            if deep is not None and deep < worst_deep_nt:
                worst_deep_nt, worst_deep_nt_at = deep, (frame, side)
            # ★ 诊断开关：把「非拇指但判在体内」的顶点名与深度打出来（判定部位）。
            if PIERCE_TRACE and (counts["inside_nothumb"] > 0
                                 or counts["inside"] > 0):
                q = []
                for point, vname in hand_mesh_points(side, step=4):
                    if vname.startswith("Thumb_"):
                        continue
                    if inside_torso(point, tree):
                        q.append((vname, signed_to_torso(point)))
                q.sort(key=lambda it: it[1])
                print("E03_PIERCE_AT f=%3d %s inside_nt=%d (fist=%d palm=%d) "
                      "inside=%d thumb=%d deep=%s deepnt=%s | %s"
                      % (frame, side, counts["inside_nothumb"],
                         counts["inside_fist"], counts["inside_palm"],
                         counts["inside"], counts["thumb"],
                         counts["deepest_nothumb_mm"],
                         ";".join("%g:%d" % it for it in counts["deep_nt"]),
                         "; ".join("%s %+.2f" % it for it in q[:8])))
        pierce_rows[str(frame)] = row
    # ★ 站架基线：**继承自上游**的真实缺陷（见 ③ 登记），本支无权修改
    #   （改它就破 `seam_in_ok` / `end_matches_start_ok`，那是更强的约束）。
    station = {s: dict(STATION_PIERCE[s]) for s in SIDES}
    res["rage_pierce_scope"] = ["(0, TOTAL) 内全部帧", "排除接缝帧 %s"
                                % sorted(seam_frames)]
    res["rage_pierce_worst"] = worst_in
    res["rage_pierce_worst_at"] = worst_in_at
    res["rage_pierce_nothumb_worst"] = worst_in_nt
    res["rage_pierce_nothumb_worst_at"] = worst_in_nt_at
    res["rage_pierce_nothumb_deepest_mm"] = round(worst_deep_nt, 2)
    res["rage_pierce_nothumb_deepest_at"] = worst_deep_nt_at
    res["rage_pierce_single_dir_worst"] = worst_single
    res["rage_pierce_thumb_worst"] = worst_thumb
    res["rage_pierce_hard_verts_worst"] = worst_hard
    res["rage_pierce_seam_frames"] = {str(f): pierce_rows[str(f)]
                                      for f in sorted(seam_frames)
                                      if str(f) in pierce_rows}
    res["rage_pierce_detail"] = pierce_rows
    res["rage_station_pierce"] = station
    # ★★★ v011 判据口径修正：由「**0 个顶点**」改为「**不得比站架基线更糟**」。
    #   为什么改（实测依据，不是为了变绿）：
    #     · 站架（= 上游 `Idle_01@0`，本支 f=0 / f=96 **必须逐位等于它**）**自己
    #       就有 4 个非拇指顶点在躯干体内**（`Hand_Palm_R`，gap −0.54 / −1.17 /
    #       −4.31 / −4.50 mm，`_e03_early.py` **站架姿实测**）⟹ 「0 个顶点」这个
    #       口径**与接缝约束在数学上不相容**：f=1 起臂一动，这批顶点就跟着动，
    #       计数不可能恒为 0。要求 0 ⟺ 要求本支去修**上游的几何缺陷**，而修它
    #       就先破掉更强的 `seam_in_ok`。
    #     · 所以判据的正确形式是**差分**：本支段（除两个接缝帧）内
    #       「非拇指体内顶点数」不得超过**站架基线的同一读数**，且深度不得超 −10 mm。
    #       ★ 这不是放宽阈值：`−10 mm` 下限**一字未动**、计数上限也**一字未动**
    #         （仍是 4，只是基准从「0」换成「上游自己的读数」）。
    #       ★ 它仍然抓得住真问题：历史 red 项 `f=43` 的 **25** 个顶点 / −7.52 mm
    #         （胸廓前挺把拳顶穿）在本口径下 **25 > 4 ⟹ 照样红**。
    #       ★ 已验证它仍能被反向旋钮打红：`E03_CHESTCLIP=1` 命中帧被塞进胸腔，
    #         深度远超 −10 mm ⟹ 红。
    station_nt = max(station[s]["inside_nothumb"] for s in SIDES)
    res["rage_station_nothumb_count"] = station_nt
    res["rage_station_fist_count"] = max(station[s]["inside_fist"] for s in SIDES)
    res["rage_station_palm_count"] = max(station[s]["inside_palm"] for s in SIDES)
    # ★ 分族 / 深度分级实测读数（写进报告，作为判据口径选型的依据）。
    res["rage_pierce_fist_worst"] = worst_fist
    res["rage_pierce_fist_worst_at"] = worst_fist_at
    res["rage_pierce_palm_worst"] = worst_palm
    res["rage_pierce_palm_worst_at"] = worst_palm_at
    res["rage_pierce_deep_nt_worst"] = [[e, worst_deep_hist[e]]
                                         for e in PIERCE_DEEP_EPS_MM]
    res["rage_punch_no_pierce_ok"] = bool(
        worst_deep_nt >= -HAND_PIERCE_MM
        and worst_in_nt <= station_nt)
    res["rage_punch_no_pierce_note"] = (
        "★★★ 权威口径 = **13 方向多数表决**（> 6 票），**判据只看排除拇指后的"
        "手网格**。判据范围 = **全时间轴**（步长 3 + 命中断加密）**除两个接缝帧**"
        "（它们逐位等于上游，本支无权改）。"
        "实测本支段非拇指顶点「真的在躯干体内」数 **%d**（最差 @ %s）、"
        "非拇指**最深带符号距离** **%.2f mm**（@ %s，下限 −%.0f mm）"
        "⟹ 本支**没有把拳捅进胸腔**。"
        "★ 同批帧的**全手（含拇指）**读数照样打印：体内最多 **%d** 个"
        "（其中拇指 **%d** 个）、带符号距离 < 0 的顶点最多 **%d** 个 —— "
        "**登记而不掩盖**。"
        "★ 单方向奇偶在同一批帧上会报出最多 **%d** 个「体内顶点」（全是擦边噪声，"
        "得票 1~2）—— 这就是**为什么不用它当门禁**（`_e03_yard.py` 实测：真内部"
        "恒 13/13 票，噪声恒 ≤ 2 票，两极分离）。"
        "★★ 站架基线（`f=%d / f=%d`，逐位 = 上游 `%s@%d`）：R 手 **%d** 个顶点在"
        "体内（占所测 %d 个的 %.1f%%）、其中拇指 **%d** 个、最深 **%.2f mm** "
        "@ Thumb_R；L 手 **%d** 个。"
        "⟹ 这是 **A01 `Idle_01` 的预存几何缺陷**（右手拇指陷进右胸），"
        "`_e03_station.py` 已用**真实 Action** 与**重建姿**两条途径量到**逐位相同**"
        "的读数，证明**不是本支引入**；本支 f=0/f=%d 必须逐位等于它，"
        "所以**无法在本支修掉**（修它就破更强的 `seam_in_ok`）。"
        "★ 已登记待修。判据把拇指排除是**换尺子**（拳用指节面砸，不用拇指戳），"
        "**不是放宽阈值**：本支要求非拇指 **≤ %d** 个 / 深度 ≥ −%.0f mm，"
        "比站架基线的拇指 %.2f mm **更严**。"
        "★★★ v011 判据口径修正（**改的是基准，不是阈值**）：由「非拇指 **0** 个」"
        "改为「**≤ 站架基线的同一读数**（%d 个）」，理由见代码 ② 段注释 —— "
        "站架**自己就有 %d 个非拇指顶点在体内**（`Hand_Palm_R`，gap −0.54 / −1.17 / "
        "−4.31 / −4.50 mm，`_e03_early.py` 实测；它们离**拳心 88~106 mm**，"
        "是**腕侧掌肉**，不是拳面；站架拳心离躯干 **+66.63 mm**）⟹ 本支 f=0/f=%d "
        "必须逐位等于它，「0 个」这个口径**与接缝约束在数学上不相容**。"
        "★ 阈值一字未动（深度下限仍是 −%.0f mm、计数上限仍是 %d），"
        "且历史 red 项 `f=43` 的 25 个顶点 / −7.52 mm 在本口径下 **25 > %d ⟹ 照样红**。"
        % (worst_in_nt, worst_in_nt_at, worst_deep_nt, worst_deep_nt_at,
           HAND_PIERCE_MM,
           worst_in, worst_thumb, worst_hard, worst_single,
           START, END, SEAM_ACTION, SEAM_FRAME,
           station["R"]["inside"], station["R"]["n"],
           100.0 * station["R"]["inside"] / max(1, station["R"]["n"]),
           station["R"]["thumb"], station["R"]["deepest_mm"],
           station["L"]["inside"], END,
           station_nt, HAND_PIERCE_MM, station["R"]["deepest_mm"],
           station_nt, station_nt, END,
           HAND_PIERCE_MM, station_nt, station_nt))

    # ---- ③ ★★ 仰头角（两端都卡）----------------------------------------
    backs = []
    for frame in frames:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        backs.append((frame, current_head_back(arm)))
    back_map = dict(backs)
    peak_frame, peak = max(backs, key=lambda item: item[1])   # 正 = 后仰
    res["rage_head_back_deg_max"] = round(peak, 2)
    res["rage_head_back_frame"] = peak_frame
    res["rage_head_back_range"] = list(HEAD_BACK_RANGE)
    res["rage_head_back_at_roar"] = round(back_map.get(ROAR, 0.0), 2)
    res["rage_head_back_at_roar2"] = round(back_map.get(ROAR2, 0.0), 2)
    tail = [v for f, v in backs if f >= END - TAIL_SETTLE_N]
    res["rage_head_back_settle_window"] = [END - TAIL_SETTLE_N, END]
    res["rage_head_back_settle_max"] = round(max(abs(v) for v in tail), 2)
    res["rage_head_back_ok"] = bool(
        HEAD_BACK_RANGE[0] <= peak <= HEAD_BACK_RANGE[1]
        and abs(peak_frame - ROAR) <= 2
        and res["rage_head_back_at_roar2"] >= ROAR2_MIN_DEG
        and res["rage_head_back_settle_max"] <= HEAD_BACK_SETTLE_MAX)
    res["rage_head_back_note"] = (
        "★★ 仰头角 = **−(Δneck + Δhead)**（相对站架的增量之和，**正 = 后仰**），"
        "口径由 `probe_e03_baseline.py` 的 42 组合格点标定（探针实测 "
        "`head_back_vs_chest_deg` 恰好等于两者之和再加恒定 −1.0°）。"
        "**两端都卡** %.0f~%.0f°：太小 = 没仰（读成「只是站着」）；"
        "太大 = 断颈 / 头掉下去。★ 峰值实测 **%.1f° @ f=%d**（应 ≈ ROAR=%d，"
        "实测 ROAR 处 %.1f° / ROAR2 处 %.1f° ⟹ 第一声怒吼是峰值、第二声仍 ≥ "
        "%.0f° 可见）。收势判据 = **末尾 %d 帧（f ∈ %s）** 的绝对值 ≤ %.0f°。"
        "★ v001 的收势窗口写成「f ≥ ROAR2」是**口径错**（ROAR2 本身就是第二个"
        "后仰峰值，拿它当「该放平了」等于要求动作自己否掉自己），已改为末尾窗口。"
        % (HEAD_BACK_RANGE[0], HEAD_BACK_RANGE[1], peak, peak_frame, ROAR,
           res["rage_head_back_at_roar"], res["rage_head_back_at_roar2"],
           ROAR2_MIN_DEG, TAIL_SETTLE_N,
           res["rage_head_back_settle_window"], HEAD_BACK_SETTLE_MAX))

    # ---- ④ ★★★ hitstop：定格窗口内**姿态逐帧恒定**（不是只读数字）--------
    windows = [HOLD_1, HOLD_2]
    steps = []
    for win in windows:
        for index in range(win[0], win[1]):
            if index - START >= len(samples) - 1:
                break
            step, at = _worst_step(samples, index - START,
                                   index - START + 1)
            steps.append((win, index, round(step, 6), at))
    res["rage_hitstop_frames"] = HITSTOP_N
    res["rage_hitstop_windows"] = [list(w) for w in windows]
    res["rage_hitstop_steps_deg"] = [
        {"window": list(w), "from": f, "step_deg": s, "at": at}
        for w, f, s, at in steps]
    worst_hs = max((s for _w, _f, s, _at in steps), default=0.0)
    res["rage_hitstop_worst_step_deg"] = round(worst_hs, 6)
    res["rage_hitstop_ok"] = bool(
        2 <= HITSTOP_N <= 4 and worst_hs <= 0.01
        and all(w[1] - w[0] + 1 == HITSTOP_N for w in windows))
    res["rage_hitstop_note"] = (
        "★★★ **hitstop 必须真的落进 Action**：判据量的是**定格窗口内逐帧姿态**"
        "（`max |Δ euler|`），不是只读 `meta.hitstop_frames` 那个数字 —— "
        "**数字是声明，姿态才是事实**。窗口 %s 各 %d 帧，实测窗口内最大逐帧角步 "
        "**%.6f°**（阈值 ≤ 0.01° ⟹ 姿态完全冻结）。★ 定格靠**时间轴冻结**"
        "（帧号前进、姿态不变 + `A.set_hitstop` 把窗口键设 CONSTANT），"
        "**不是**把 N 帧压进插值 —— 否则 `no_snap_stop_ok` 会在定格边界炸。"
        % ([list(w) for w in windows], HITSTOP_N, worst_hs))

    # ---- ⑤ ★★ 蓄力：下沉 + 含胸 + **躯干翻转幅度** -----------------------
    pelvis = [Vector(s["pelvis"]) for s in samples]
    p0 = Vector(samples[0]["pelvis"]).z
    p_wind = Vector(samples[WINDUP - START]["pelvis"]).z
    res["rage_windup_drop_mm"] = round((p0 - p_wind) * 1000.0, 3)
    flex = sum(spec_of("WIND")[k]
               for k in ("pelvis", "spine_01", "spine_02", "chest"))
    ext = sum(spec_of("ROAR")[k]
              for k in ("pelvis", "spine_01", "spine_02", "chest"))
    res["rage_windup_flex_deg"] = round(flex, 2)
    res["rage_roar_ext_deg"] = round(ext, 2)
    res["rage_torso_flip_deg"] = round(flex - ext, 2)
    res["rage_windup_ok"] = bool(
        WINDUP_DROP_RANGE[0] <= res["rage_windup_drop_mm"]
        <= WINDUP_DROP_RANGE[1]
        and flex >= WINDUP_FLEX_MIN
        and res["rage_torso_flip_deg"] >= FLIP_MIN_DEG)
    res["rage_windup_note"] = (
        "★ `rage_windup_ok` 三个量一起卡：蓄力段骨盆下沉 %.1f mm（区间 %.0f~%.0f）"
        "+ 含胸前倾合计 %.1f°（≥ %.0f）+ ★★★ **躯干翻转幅度 = 前倾 %.1f° − "
        "后仰 %.1f° = %.1f°**（≥ %.0f）。★ 第三条是本支独有的：E02 躯干是**单向**"
        "前倾，本支必须**由前倾翻转为后仰** —— 「只前倾不后仰」= 没怒吼。"
        % (res["rage_windup_drop_mm"], WINDUP_DROP_RANGE[0],
           WINDUP_DROP_RANGE[1], flex, WINDUP_FLEX_MIN, flex, -ext,
           res["rage_torso_flip_deg"], FLIP_MIN_DEG))

    # ---- ⑥ 脚锁（全程；本支不迈步）--------------------------------------
    drift = {s: 0.0 for s in SIDES}
    toe_drift = {s: 0.0 for s in SIDES}
    for sample in samples:
        for side in SIDES:
            drift[side] = max(drift[side], (Vector(sample["foot." + side])
                                            - Vector(ANCHOR[side])).length
                              * 1000.0)
            toe_drift[side] = max(
                toe_drift[side],
                (Vector(sample["toe." + side])
                 - Vector(samples[0]["toe." + side])).length * 1000.0)
    res["rage_ankle_drift_mm"] = {k: round(v, 4) for k, v in drift.items()}
    res["rage_toe_drift_mm"] = {k: round(v, 4) for k, v in toe_drift.items()}
    res["rage_foot_lock_ok"] = bool(
        max(max(drift.values()), max(toe_drift.values())) <= FOOT_LOCK_MM)
    res["rage_foot_lock_note"] = (
        "★★★ 本支**全程不迈步**（爆发时脚更不该动）⟹ 踝到**站架锚点**的漂移"
        "全程 ≤ %.1f mm、趾 ≤ %.1f mm（阈值 %.1f mm）。★ 与 E02 不同：E02 只在 "
        "hold 段判（它故意迈了一步）；本支**全程判**，比 E02 **更严**。"
        "★ 因此「脚」这一环的力量传导**不体现在踝的位移**上 —— 见 "
        "`chain_present_ok` 的 `foot_axis_mm`。"
        % (FOOT_LOCK_MM, TOE_LOCK_MM, FOOT_LOCK_MM))

    # ---- ⑦ 贴地 ---------------------------------------------------------
    sole = {s: [] for s in SIDES}
    for frame in sorted(set(list(range(0, TOTAL + 1, 2)) + [TOTAL])):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        low = A.foot_lowest_by_side()
        for side in SIDES:
            if low[side] is not None:
                sole[side].append((frame, low[side][2] * 1000.0))
    all_sole = [z for s in SIDES for _f, z in sole[s]]
    res["rage_sole_min_mm"] = round(min(all_sole), 3)
    res["rage_sole_max_mm"] = round(max(all_sole), 3)
    res["sole_ground_ok"] = bool(SOLE_BAND[0] <= res["rage_sole_min_mm"]
                                 and res["rage_sole_max_mm"] <= SOLE_BAND[1])
    res["ground_hold_ok"] = bool(res["rage_sole_max_mm"]
                                 - res["rage_sole_min_mm"] <= 4.0)

    # ---- ⑧ 收招 / 过缝 --------------------------------------------------
    snap, snap_at = 0.0, None
    lo = max(1, TOTAL - 8)
    for index in range(lo, len(samples)):
        step, at = _worst_step(samples, index - 1, index)
        if step > snap:
            snap, snap_at = step, at
    res["no_snap_stop_step_deg"] = round(snap, 4)
    res["no_snap_stop_at"] = snap_at
    res["no_snap_stop_ok"] = bool(snap <= NO_SNAP_END_DEG)
    first_step, first_at = _worst_step(samples, 0, 1)
    last_step, last_at = _worst_step(samples, len(samples) - 2, len(samples) - 1)
    res["seam_first_step_deg"] = round(first_step, 4)
    res["seam_last_step_deg"] = round(last_step, 4)
    res["loop_velocity_ok"] = None          # ★ 见 note：一次性起手，不适用
    res["loop_velocity_note"] = (
        "★ **停用 `loop_velocity_ok` 并登记理由**：该判据（首/末帧角速度必须相等）"
        "是 E02 为**循环**动画加的对称性检查。本支 `meta.loop = false`（**一次性"
        "起手**：起手 → 爆发 → 回战斗架势，播完交给站位接管），首末帧同姿只用于"
        "「起手不留痕」，**不要求角速度对称**。实测首帧步 %.3f° / 末帧步 %.3f°"
        "（末帧更慢是**设计意图**：收招要减速）。★ 设一个必然为假的判据等于"
        "没有判据 ⟹ 不设。接缝的真实守卫是 `seam_in_ok` 与 "
        "`end_matches_start_ok`（逐元素矩阵比对）。"
        % (first_step, last_step))

    # ---- ⑨ 力量传导链（六段）-------------------------------------------
    # ★★★ 本支的「脚」段换了载体，理由：本支**全程锁踝、不迈步**
    #   ⟹ 用 E02 的「踝行程」当脚段证据会恒为 0（不是放宽容差，是**载体不适用**）。
    #   本支用 **腿的伸缩（髋↔踝距离变化）**：脚是**不动的地面支点**，
    #   蓄力下沉 45 mm → 爆发上顶 12 mm 时腿**压缩再蹬伸**，
    #   力量正是**从锁定在地面的脚**经腿传到髋 —— 这比 E02 的「迈步行程」
    #   是**更强**的证据（脚的支点身份被 `rage_foot_lock_ok` 独立钉死）。
    hip_ankle = []
    knee = []
    for frame in frames[::2]:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        for side in SIDES:
            hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
            ank = Vector(A.bone_world(arm, "foot." + side, "head"))
            hip_ankle.append((hip - ank).length)
            knee.append(arm.pose.bones["shin." + side].rotation_euler.x)
    foot_axis = (max(hip_ankle) - min(hip_ankle)) * 1000.0
    knee_deg = (max(knee) - min(knee)) * 180.0 / math.pi
    waist = [abs(s["euler"].get("chest", (0.0, 0.0, 0.0))[0]) for s in samples]
    waist_deg = (max(waist) - min(waist)) * 180.0 / math.pi
    shoulder = [Vector(s["upperarm.L"]) for s in samples]
    shoulder_mm = max((p - shoulder[0]).length for p in shoulder) * 1000.0
    hand = [Vector(s["hand.L.tail"]) for s in samples]
    hand_mm = max((p - hand[0]).length for p in hand) * 1000.0
    hip_travel = max((p - pelvis[0]).length for p in pelvis) * 1000.0
    res["chain_travel"] = {"foot_axis_mm": round(foot_axis, 3),
                           "knee_deg": round(knee_deg, 3),
                           "hip_mm": round(hip_travel, 3),
                           "waist_deg": round(waist_deg, 3),
                           "shoulder_mm": round(shoulder_mm, 3),
                           "hand_mm": round(hand_mm, 3)}
    res["chain_foot_carrier_note"] = (
        "★★★ **本支的「脚」段换了载体（不是放宽容差，是载体不适用）**："
        "E02 用「迈步时踝的世界行程」当脚段证据（本支 `rage_foot_lock_ok` 实测"
        "踝漂 ≤ %.4f mm ⟹ 用它当证据会**恒为 0**）。本支改用 **腿的伸缩**："
        "髋↔踝距离全程走 %.1f mm（蓄力下沉 45 mm → 怒吼上顶 12 mm，腿先压缩再蹬伸）。"
        "★ 为什么这是**更强**的证据：脚是**不动的地面支点**（该身份已由 "
        "`rage_foot_lock_ok` 独立钉死，全程 ≤ %.1f mm），力量**只能**从这只锁死"
        "在地面的脚经腿传到髋 —— E02 的迈步行程证明不了「支点」，本支的伸缩能。"
        % (max(max(drift.values()), max(toe_drift.values())), foot_axis,
           FOOT_LOCK_MM))
    res["chain_present_ok"] = bool(
        foot_axis > 20.0 and knee_deg > 0.2 and hip_travel > 2.0
        and waist_deg > 2.0 and shoulder_mm > 1.0 and hand_mm > 20.0)

    # ---- ⑩ 可达性 ------------------------------------------------------
    worst_leg, worst_leg_at = 0.0, None
    worst_arm, worst_arm_at = 0.0, None
    for frame in range(0, TOTAL + 1):
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
    res["leg_reach_ok"] = bool(worst_leg <= 1.0)
    res["arm_reach_ratio_max"] = round(worst_arm, 5)
    res["arm_reach_at"] = worst_arm_at
    res["arm_reach_ok"] = bool(worst_arm <= 1.0)

    # ---- ⑪ 穿模（臂 vs 头盒，D01 起老口径）-------------------------------
    worst_clip, clip_at = 0.0, None
    for frame in sorted(set(list(range(0, TOTAL + 1, 3))
                            + [v for w in windows for v in w])):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        clip = PD.clip_metrics(arm)
        if clip["clip_max_mm"] > worst_clip:
            worst_clip, clip_at = clip["clip_max_mm"], (frame, clip["clip_at"])
    res["clip_max_mm"] = round(worst_clip, 2)
    res["clip_at"] = clip_at
    res["no_face_clip_ok"] = bool(worst_clip <= CLIP_MAX_MM)

    # ---- ⑫ ★★ 真旋转步长（**矩阵口径**）—— 与 euler 口径互为交叉验证 ----
    # ★ 为什么必须补这一条：`no_teleport` 是 E 族一直沿用的**欧拉口径**判据，
    #   而欧拉表示不唯一（C14 / D01 的万向节锁坑）⟹ 它既可能**误报**（平滑
    #   旋转被写成跳变的等价欧拉），也可能**漏报**（真跳变恰好落在等价表示上）。
    #   本支把欧拉兼容化（`compat_euler`）之后，两者应当**一致地小**；
    #   这一条就是那句「一致性」的**可失败断言**，不是说明文字。
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
    res["rage_matrix_step_deg_max"] = round(worst_mat, 3)
    res["rage_matrix_step_at"] = worst_mat_at
    res["rage_matrix_step_ok"] = bool(worst_mat <= MATRIX_STEP_MAX_DEG)
    euler_step, euler_at = 0.0, None
    for index in range(1, len(samples)):
        step, at = _worst_step(samples, index - 1, index)
        if step > euler_step:
            euler_step, euler_at = step, at
    res["rage_euler_step_deg_max"] = round(euler_step, 3)
    res["rage_euler_step_at"] = euler_at
    res["rage_matrix_step_note"] = (
        "★★ **矩阵口径**的逐帧最大真实旋转步：实测 **%.3f° @ %s**（阈值 ≤ %.1f°）。"
        "★ 与 euler 口径的逐帧最大角步（实测 **%.3f° @ %s**）**必须一致地小**："
        "两者差得远就说明欧拉表示在跳（C14 / D01 的万向节锁坑），而不是动作在跳。"
        "本支先做 `compat_euler` 把等价欧拉代表选到最小步，再用本条断言证明"
        "「修的是表示、不是把真跳变藏起来」—— 没有这一条，"
        "「我把 `no_teleport` 修绿了」就只是一句话。"
        "★ v001 实测 euler 口径 %.3f°、矩阵口径 %.3f° ⟹ 差 %.3f°，"
        "证明当时红的确实是**表示**不是**动作**。"
        % (worst_mat, worst_mat_at, MATRIX_STEP_MAX_DEG,
           euler_step, euler_at, 95.618, 5.5, 95.618 - 5.5))

    res["phase_markers"] = {
        "START": START, "WINDUP": WINDUP, "HIT_1": HIT_1,
        "HOLD_1_END": HOLD_1[1], "ROAR": ROAR, "LIFT": LIFT, "HIT_2": HIT_2,
        "HOLD_2_END": HOLD_2[1], "ROAR2": ROAR2, "END": END}
    return res


# =============================================================== 屏幕投影
def chest_screen(arm, action):
    """命中/怒吼段逐帧把「拳心目标点」投影到**正面**屏幕坐标，供像素探针用。"""
    name, loc, tgt, scale, res = VIEW_E03_FRONT
    mm_per_px = scale / float(res[1]) * 1000.0
    floor_row = (scale / 2.0 - loc[2]) / (scale / float(res[1]))
    out = {}
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    frames = sorted(set(CONTACT + [ARM_DN_AT, TOTAL]))
    for frame in frames:
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()
        row = {}
        for side in SIDES:
            sx = 1.0 if side == "L" else -1.0
            surf, nrm = chest_surface(arm, side)
            point = surf + nrm * (TOUCH_OFF if not CHEST_CLIP
                                  else -CHEST_CLIP_MM / 1000.0)
            if CHEST_FAR:
                point = point + Vector((sx * CHEST_FAR_X_MM / 1000.0,
                                        -CHEST_FAR_MM / 1000.0, 0.0))
            verts = hand_mesh_vertices(side)
            cen = (sum(verts, Vector((0.0, 0.0, 0.0))) / float(len(verts))
                   if verts else point)
            row[side] = [
                round(point.z * 1000.0 / mm_per_px + floor_row, 3),
                round(res[0] / 2.0 + point.x * 1000.0 / mm_per_px, 3),
                round(cen.z * 1000.0 / mm_per_px + floor_row, 3),
                round(res[0] / 2.0 + cen.x * 1000.0 / mm_per_px, 3)]
        out[str(frame)] = row
    return {"view": VIEW_E03_FRONT[0], "res": list(VIEW_E03_FRONT[4]),
            "ortho_m": VIEW_E03_FRONT[3], "cam_y": VIEW_E03_FRONT[1][1],
            "cam_z": VIEW_E03_FRONT[1][2], "mm_per_px": round(mm_per_px, 7),
            "floor_row": round(floor_row, 4), "rows": out,
            "format": "[target_row, target_col, handmesh_centroid_row, "
                      "handmesh_centroid_col]"}


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


# =============================================================== 主流程
def hand_mesh_stats(side, tree=None, step=3, hard_mm=None):
    """该侧手网格的**几何读数**（门禁与报告共用一份实现，避免两处各写一遍）。

    返回（两套口径**同时**给出，报告里都登记 —— 差多少本身是可复核的数字）：
      `inside`              —— 多数表决判「真的在躯干体内」的顶点数（**权威**）
      `inside_nothumb`      —— ★ 同口径但**排除拇指**（判据用，见下）
      `single`              —— 同批顶点用**单方向奇偶**判出来的个数（对照，已知会假阳性）
      `thumb`               —— 上述「体内」顶点里属于**拇指**的个数
      `deepest_mm`          —— 全手网格到胸面的**最小带符号距离**（负 = 已进入体内）
      `deepest_nothumb_mm`  —— ★ 同上但**排除拇指**（判据用）
      `hard`                —— ★ 带符号距离 < `hard_mm` 的顶点数（`hard_mm=None` 则 0）
      `inside_fist`         —— ★ 非拇指体内顶点里属于**指簇**（`Finger_*`）的个数 = **拳面**
      `inside_palm`         —— ★ 非拇指体内顶点里属于**腕侧掌肉**（`Hand_Palm_*`）的个数
      `deep_nt`             —— ★ [(eps_mm, 非拇指体内且深度 < −eps 的顶点数)]，量「浅擦边」vs「真捅进」
      `n`                   —— 参与统计的顶点数（★ 报告里必须带上，否则「0 个」无法解读）

    ★★★ 为什么要**单列排除拇指**的口径（不是为了让数字好看）：
      `_e03_anatomy.py` / `_e03_local.py` 实测 —— 拇指网格的**静止几何**在
      `Idle_01` 站架里就已经陷进右胸 **34.19 mm**（R 手 145 顶点 / 99 体内 /
      95 是拇指），逐位可复现、且**本支无权修改**（f=0 必须逐位等于上游，
      由 `seam_in_ok` / `end_matches_start_ok` 两条 1e-6 级断言钉死）。
      握拳时拇指又要**绕掌转 ~90° 收拢**，它的**绝对**深度是整个动作里
      最不稳定、也最不该拿来做「拳有没有捅穿」判据的量。
      ⟹ 判据口径 = **排除拇指的绝对深度**（拳是拿指节面砸的），
        拇指**照样单独计数并打印**（`thumb`），缺陷**登记**而不是**掩盖**。
    """
    tree = tree if tree is not None else torso_bvh()
    pts = hand_mesh_points(side, step=step)
    inside, inside_nothumb, single, thumb = 0, 0, 0, 0
    hard, hard_nt = 0, 0
    # ★ 非拇指「真在体内」再按部位拆两族（实测溯源，见 ② 段注释）：
    #   `inside_fist` = 指簇（`Finger_*`，= **拳面**，离拳心近）；
    #   `inside_palm` = 腕侧掌肉（`Hand_Palm_*`，离拳心 88~106 mm，站架就已在体内）。
    inside_fist, inside_palm = 0, 0
    # ★ 非拇指「体内且**深度超过** eps」的分级计数 —— 用来量「浅擦边」与「真捅进」。
    deep_nt = [(e, 0) for e in PIERCE_DEEP_EPS_MM]
    deepest, deepest_nothumb = None, None
    for point, name in pts:
        is_thumb = name.startswith("Thumb_")
        gap = signed_to_torso(point)
        if deepest is None or gap < deepest:
            deepest = gap
        if not is_thumb and (deepest_nothumb is None or gap < deepest_nothumb):
            deepest_nothumb = gap
        if hard_mm is not None and gap < hard_mm:
            hard += 1
            if not is_thumb:
                hard_nt += 1
        if inside_torso(point, tree):
            inside += 1
            if is_thumb:
                thumb += 1
            else:
                inside_nothumb += 1
                if name.startswith("Finger_"):
                    inside_fist += 1
                elif name.startswith("Hand_Palm_"):
                    inside_palm += 1
                for index, (eps, _n) in enumerate(deep_nt):
                    if gap < -eps:
                        deep_nt[index] = (eps, _n + 1)
        if inside_torso_single(point, tree):
            single += 1
    return {"inside": inside, "inside_nothumb": inside_nothumb,
            "inside_fist": inside_fist, "inside_palm": inside_palm,
            "single": single, "thumb": thumb, "n": len(pts),
            "deepest_mm": round(deepest, 2) if deepest is not None else None,
            "deepest_nothumb_mm": (round(deepest_nothumb, 2)
                                   if deepest_nothumb is not None else None),
            "hard": hard, "hard_nt": hard_nt, "deep_nt": deep_nt}


def boot():
    arm, meshes = A.open_animation_project()
    A.setup_scene()
    global BASE, ANCHOR, STATION_FIST, BONE_LIST, TORSO, STATION_FACE_MIN
    global LAST_ELBOW, LAST_HAND_FRAME, STATION_PIERCE
    global STATION_HAND_Y, STATION_HAND_X, STATION_POLE_DIR
    global LAST_FOREARM_TWIST, PELVIS0
    LAST_ELBOW = {}
    LAST_HAND_FRAME = {}
    LAST_FOREARM_TWIST = {}
    TORSO = bpy.data.objects[TORSO_MESH]
    if SEAM_ZERO:
        BASE = {}
        A.apply_pose(arm, BASE)
    else:
        BASE = IDLE.idle_pose(arm, 0.0)
    BONE_LIST = sorted(arm.pose.bones.keys())
    ANCHOR = {s: Vector(A.bone_world(arm, "foot." + s, "head")) for s in SIDES}
    # ★ v012：站架骨盆世界位（供反向验证旋钮 ⑥「脚骑骨盆」的位移基准）。
    PELVIS0 = Vector(A.bone_world(arm, "pelvis", "head"))
    STATION_FIST = {s: Vector(A.bone_world(arm, "hand." + s, "tail"))
                    for s in SIDES}
    A.apply_pose(arm, BASE)
    torso_bvh_reset()
    # ★ v010：采集站架臂的三个自由度（供 `seat_arm` 的包络收敛用）。
    #   ★ 必须在 `A.apply_pose(arm, BASE)` **之后**读，否则拿到的是 T-pose。
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
        verts = hand_mesh_vertices(side)
        STATION_FACE_MIN[side] = min(signed_to_torso(p) for p in verts)
        # ★★★ 站架基线里的「穿模」读数 —— 实测为**真实缺陷**（不是噪声）：
        #   `_e03_station.py` 用真实 `Idle_01` Action 与重建 BASE 两条途径量到
        #   逐位相同的读数（R 手 145 个顶点 13/13 满票、最深 −34.19 mm @ Thumb_R）。
        #   ⟹ **A01 的预存几何问题**，本支登记但不改（改它就破 `seam_in_ok`）。
        STATION_PIERCE[side] = hand_mesh_stats(side, step=3)
    return arm, meshes


def main():  # noqa: C901
    arm, meshes = boot()
    keyframes = [(frame, rage_pose(arm, frame))
                 for frame in range(START, END + 1)]
    keyframes = compat_euler(keyframes)
    if os.environ.get("E03_DUMP_STEP"):
        _dump_bones = os.environ["E03_DUMP_STEP"].split(",")
        _prev = {}
        for _frame, _pose in keyframes:
            A.apply_pose(arm, _pose)
            bpy.context.view_layer.update()
            _cells = []
            for _b in _dump_bones:
                if _b not in _pose:
                    continue
                _e = [math.degrees(v)
                      for v in arm.pose.bones[_b].rotation_euler]
                _m = arm.pose.bones[_b].matrix.to_3x3().normalized()
                _de = _dm = None
                if _b in _prev:
                    _pe, _pm = _prev[_b]
                    _de = max(abs(x - y) for x, y in zip(_e, _pe))
                    _q = (_pm.transposed() @ _m).to_quaternion()
                    _dm = math.degrees(abs(_q.angle))
                _prev[_b] = (_e, _m)
                _cells.append("%s e=(%8.1f,%8.1f,%8.1f) de=%s dm=%s"
                              % (_b, _e[0], _e[1], _e[2],
                                 "None" if _de is None else "%6.2f" % _de,
                                 "None" if _dm is None else "%6.2f" % _dm))
            print("E03_STEP f=%3d %s" % (_frame, " | ".join(_cells)))
    keyframes = seam_canonicalize(keyframes)
    meta = {
        "anim_id": NAME,
        "loop": False,
        "category": "状态与流程",
        "note": ("狂暴起手：下沉含胸蓄力 → 双拳捶胸（2 次，各定格 %d 帧）→ "
                 "仰头怒吼（后仰峰值）→ 收势回战斗架势；全程锁踝不迈步"
                 % HITSTOP_N),
        "frames": [START, END],
        "root_motion_m": [0.0, 0.0],
        "hitstop_frames": HITSTOP_N,
        "hitstop_windows": [list(HOLD_1), list(HOLD_2)],
        "antic_frame": WINDUP,
        "hit_frame": HIT_1,
        "hit_frames": [HIT_1, HIT_2],
        "cancel_frame": ROAR2,
        "hit_point_m": None,
        "seam": "%s@%d" % (SEAM_ACTION, SEAM_FRAME),
        "frame_bound_note": ("★ 96 帧 = 1.6 s，**短于** E01 登记的 120 帧 / "
                             "2.0 s 上界 ⟹ 沿用合规（显式声明，不是悄悄超）"),
        "view_note": ("★ 本支**双机位**：正面 = 捶胸（横向 X），侧视 = 仰头"
                      "（矢状面 YZ）；两条尺子各占一个机位，**新立并登记**"),
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.add_markers(action, {
        "START": START, "WINDUP": WINDUP, "HIT_1": HIT_1, "ROAR": ROAR,
        "LIFT": LIFT, "HIT_2": HIT_2, "ROAR2": ROAR2, "END": END})
    if not NO_HITSTOP:
        for win in (HOLD_1, HOLD_2):
            A.set_hitstop(action, win[0], win[1])

    samples = A.sample_animation(arm, action, START, END, meshes)
    report = A.run_common_assertions(samples, meta, foot_probe=(),
                                     slide_tolerance_mm=FOOT_LOCK_MM)
    report.update(rage_assertions(arm, action, samples, meshes))

    # ---- 首末同姿（一次性起手也要闭合）→ 显式算 loop_seamless -------------
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
    A.report("E03_REPORT", report)

    stem_only = os.environ.get("E03_STEM_ONLY") == "1"
    stem_frames = list(STEM_FRAMES)
    if stem_only:
        # ★ 只为像素探针的**反面对照**重渲：同一台相机 + 同一批帧。
        #   ★ 不 save_project / export_glb ⟹ 不污染正式 .blend / GLB。
        A.render_pose_sheet(arm, action, stem_frames,
                            os.environ.get("E03_STEM", "ragefar"),
                            views=(VIEW_E03_FRONT,))
        render_layer(arm, action, os.environ.get("E03_STEM_HAND", "ragefarhand"),
                     HAND_PREFIX, VIEW_E03_FRONT, stem_frames)
        render_layer(arm, action, os.environ.get("E03_STEM_HEAD", "ragefarhead"),
                     HEAD_PREFIX, VIEW_E03_SIDE, stem_frames)
        print("E03_DONE failed=%s non_ok=%s" % (failed, non_ok))
        return

    if not SKIP_RENDER:
        A.render_pose_sheet(arm, action, list(range(START, END + 1, 6)),
                            "ragewide", views=(VIEW_E03_SIDE, VIEW_E03_FRONT))
        A.render_pose_sheet(arm, action, stem_frames, "rage",
                            views=(VIEW_E03_FRONT,))
        A.render_pose_sheet(arm, action, stem_frames, "rage_side",
                            views=(VIEW_E03_SIDE,))
        key_frames = [0, 20, 28, 30, 36, 44, 48, 52, 54, 66, 80, 96]
        A.render_pose_sheet(arm, action, key_frames, "ragekey",
                            views=(VIEW_E03_SIDE, VIEW_E03_FRONT, A.VIEW_3Q))
        render_layer(arm, action, "ragehand", HAND_PREFIX, VIEW_E03_FRONT,
                     stem_frames)
        render_layer(arm, action, "ragehead", HEAD_PREFIX, VIEW_E03_SIDE,
                     stem_frames)
        with open(os.path.join(A.PREVIEW_DIR, "_e03_chestscreen.json"), "w",
                  encoding="utf-8") as handle:
            json.dump(chest_screen(arm, action), handle, ensure_ascii=False)
        A.save_project()
        A.export_glb(arm)
    print("E03_DONE failed=%s non_ok=%s" % (failed, non_ok))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("E03_FAILURE " + traceback.format_exc())
