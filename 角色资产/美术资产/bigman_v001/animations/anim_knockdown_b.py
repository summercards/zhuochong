"""anim_knockdown_b —— D15 `Knockdown_B` 后倒（背面倒地）。

清单原文：「**背面倒地**」。

★★ 本支是 **D14 `Knockdown_F` 的镜像分支** —— 两支**共用同一个入口**
   （`Air_Hit@18`）、**共用同一条抛物线**，只在"落地之后往哪边倒"上分岔：
     · D14：向前扑倒 → **俯卧**（脸朝下）⟹ 骨盆向 **−Y** 扑出、躯干俯仰转到 **+88°**；
     · D15：向后坐倒 → **仰卧**（脸朝上）⟹ 骨盆向 **+Y** 退出、躯干俯仰转到 **−88°**。
   ★ 画面上一眼可分辨：D14 头在**图像左**（−Y = 前方），D15 头在**图像右**（+Y = 后方）。

    | 接缝 | 上游 / 下游 | 本支落成的做法 |
    |---|---|---|
    | 上游**姿态** | D13 末帧 = `Air_Hit@18`（f14 起逐位锁存的空中自持姿态） | 本支 f0 **逐位 = `Air_Hit@18`**（与 D14 **同源**） |
    | 上游**动量** | D13 末帧 `end_vz = −58.3889 mm/帧` | **继承**且 f0 起继续加速（与 D14 **完全相同**的那一条抛物线） |
    | 下游**落地** | D16 `Ground_Hit` / D18 `GetUp_B` 从"仰面贴地"起步 | 末帧**离开弹道**：骨盆 z 固定，登记 `end_pelvis_z_m` + `end_vz = 0` |

★★ §1 本支的真风险：**触地是"两次"，而且载体与 D14 完全不同**

   D14 只有**一个**受管载体：**鞋底**（`f ≥ LAND` 双脚钉死在固定世界足迹上）。
   后倒时腿会**因惯性抬起**（膝盖朝上），鞋底**必然离地** ⟹ D14 的 `foot_probe`
   在本支**必须停用**，否则一落地就红。
   本支的受管载体换成 **③ 点 `hip_probe`：骨盆 + 后脑（`head` 尾端）+ 双肩**
   （都固定在落地曲线上），另加 **`butt_contact_ok`** 单管"臀/骨盆区网格首次触地"。

   ★ 竖直通道仍是**四段**（D14 只有三段）：
     | 段 | 帧 | 竖直位移归谁 | 判据 |
     |---|---|---|---|
     | 下落段 | `f0 ~ LAND−1` | 共享解析弹道（与 D13 同一条） | `ballistic_until_land_ok`（≤2 mm） |
     | 触地帧 | `f = LAND` | 弹道**最后一个点**，身体最低点恰好接触 | `landing_event_ok` / `butt_contact_ok` |
     | 坐倒段 | `LAND < f ≤ SUPINE_PEAK` | **落地曲线**（骨盆 z 单调不升、末端固定） | `landing_z_fixed_ok` / `landing_no_bounce_ok` |
     | 躺平段 | `f > SUPINE_PEAK` | 骨盆 z **逐位固定** | `landing_plateau_ok` |

   ★★ **对计划原文的一处诚实修正（附实测）**：计划 §1 说"**臀/骨盆先着地 → 背部再着地**"。
     实测**证伪**：接缝 `Air_Hit@18` 的**最低于全身的是鞋底**（`Shoe_Sole_R` **432.9 mm** /
     `Shoe_Sole_L` **454.7 mm**，逐对象实测），而弹道给出的骨盆高在 `f=7` 是 **812.5 mm** ——
     后倒的臀距骨盆骨 ≈ 200~250 mm，几何上**不可能**在 `f=7` 触地。
     ⟹ 本支的真实次序是 **① 脚先着地（`f = LAND = 7`）→ ② 臀/背再着地**
     （`BUTT_LAND` 由臀区网格实测确定）。这与 D14 的"脚先着地"**同一个事件**，
     差别只在**落地之后往哪边倒**。两条分支因此共用同一把"落地事件"尺子。

★ 帧预算：**20 帧 / 0.333 s @60fps**，非循环（硬上界 22）。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python anim_knockdown_b.py
    SKIP_RENDER=1  只跑门禁不渲图（迭代用）
    D15_TRACE=1    逐帧打印驱动标量 / 竖直曲线 / 落地曲线 / 四肢行程

反向验证（§4 第 7 步）：
    D15_TP_SEAM_ZERO=1   ① 首帧改零位（接缝断）      ⟹ `seam_in_ok` 红
    D15_TP_BUMP=30       ② 触地帧骨盆 +30 mm 上抬    ⟹ `ballistic_until_land_ok` + `landing_no_bounce_ok` 红
    D15_TP_NOVZ=1        ③ 抽掉 vz 继承（f0 竖速 = 0）⟹ `vz_fall_then_stop_ok` 红
    D15_TP_NOSUPINE=1    ④ 抽掉**后倒俯仰**主驱动     ⟹ `supine_rotation_ok` + `compress_present_ok` 红
    D15_TP_FLIPSIGN=1    ⑤ **把后倒俯仰的符号翻正**（变成"前倒"）⟹ `supine_pitch_ok` 红
      ★ ⑤ 是 D14 没有的一组：它证明"**方向**也被守着"，不只是"幅度"。
    D15_TP_NOLEGS=1      ⑥ 抽掉**抬腿**驱动           ⟹ `legs_lift_ok` 红
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
import anim_jump_start as JS             # noqa: E402
import anim_ultimate_end as UE           # noqa: E402
import anim_crouch as CR                 # noqa: E402
import probe_c12_baseline as P           # noqa: E402
import probe_d01_guard as PD             # noqa: E402

NAME = "Knockdown_B"
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"
SIDES = ("L", "R")

# ★ 接缝真源：上游 D13 的落盘 action + 末帧号
SEAM_ACTION = os.environ.get("D15_SEAM_ACTION", "Air_Hit")
SEAM_FRAME = int(os.environ.get("D15_SEAM_FRAME", "18"))
# ★ D13 的相位原点（`anim_air_hit.T_PHASE`）—— 本支**必须**沿用它
D13_T_PHASE = 31.5


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


def _f32(value):
    """量化到 float32 —— F-Curve 关键帧就是按 float32 存的（与 D02~D13 同源）。"""
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
    """分段**线性**取值。"""
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


def _clamp(value, lo, hi):
    return max(lo, min(hi, value))


# =============================================================== 时间轴
TOTAL = _env_i("D15_TOTAL", 20)
# ★ 触地帧 = **脚先着地**（与 D14 同一个事件、同一条弹道）。
#   实测依据（`probe_d15_measure.py`）：接缝全身最低 = `Shoe_Sole_R` 432.9 mm，
#   弹道 f7 骨盆 812.5 mm ⟹ 脚在 f≈7 触地。`D15_LAND` 可覆盖以复测。
LAND = _env_i("D15_LAND", 7)
HIT_HOLD = _env_i("D15_HOLD", 2)              # 触地帧 2 帧姿态停顿（"砸地"顿感）
HOLD_END = LAND + HIT_HOLD - 1                # 8
# ★ 后倒的"压缩"不是膝屈 —— 是**髋屈**（臀坐实、膝被动抬起）+ 膝屈**持续**。
#   峰值窗口仍取 `LAND+1 ~ LAND+4`（= 8~11），与 D14 同一节奏。
COMPRESS_PEAK = _env_i("D15_COMPRESS", 11)
SUPINE_PEAK = _env_i("D15_SUPINE_PEAK", 15)     # ★ 仰面到位（躯干世界俯仰最大负值）
PLATEAU = _env_i("D15_PLATEAU", 16)           # ★ 起逐位锁存（贴地自持）
CANCEL = _env_i("D15_CANCEL", 16)
END = TOTAL

# =============================================================== 共享弹道
# ★ 相位**直接续在 D13 末帧之后**：D15 frame f ⟺ 解析时刻 t = (49.5) + f
#   ⟹ f0 与 D13 f18 是**同一个**解析点（z 逐位相同），全片同一条抛物线。
T_PHASE = D13_T_PHASE + float(SEAM_FRAME)     # 49.5
BALLISTIC_TOL_MM = _env_f("D15_BALLISTIC_TOL", 2.0)
Z_PELVIS_REST = 0.900
Z_ANKLE_REST = A.Z_ANKLE_REST                 # 0.078

PELVIS_Y_START = _env_f("D15_Y_START", 0.026)  # 沿用 D12/D13 的水平后移量
PELVIS_Y_END = _env_f("D15_Y_END", 0.470)      # ★ 后倒：骨盆向 **+Y** 退出（★ 与 D14 符号相反）
# ★★ 末帧骨盆高 —— **本支自己实测**，不照抄 D14 的 220.0 mm（计划收尾自查明文要求）。
#   实测法（本文件 `butt_contact_ok` 的载体）：仰卧到位时，臀/背区网格（`Suit_Torso`）
#   的最低点比 `pelvis` 骨头低 **128.4 mm**（`probe` 实测）。要求"背贴地"（最低 ≈ 0）
#   ⟹ 骨盆骨头必须落在 **≈ 128.4 mm**。取 0.128 ⟹ 背最低 ≈ −0.4 mm（贴地）。
Z_PELVIS_END = _env_f("D15_Z_END", 0.128)

# ★ 落地曲线的进入竖速 = 弹道在 LAND 帧的瞬时竖速（**不许跳变**）
VZ_LAND = None   # boot 后填


def ball_z(frame):
    """★ 与 A10/A11/A12/B08/D12/D13 **同一个**解析弹道，相位续在 D13 之后。"""
    t = T_PHASE + float(frame)
    return JS.TAKEOFF_PELVIS_Z + JS.TAKEOFF_SPEED * t - 0.5 * JS.G_PER_FRAME * t * t


def ball_vz(frame):
    """该帧的弹道**瞬时**竖速（米/帧）。"""
    return JS.TAKEOFF_SPEED - JS.G_PER_FRAME * (T_PHASE + float(frame))


G_MM = JS.G_PER_FRAME * 1000.0                # 2.722222 mm/帧²
D13_END_VZ_MM = -58.3889                      # 上游登记的末帧竖速（一阶差分口径）


def landing_k(frame):
    return float(frame - LAND)


def landing_count():
    return float(PLATEAU - LAND)


def _hermite(k, span, delta, v0):
    """三次 Hermite：起点竖速 = `v0`、终点竖速 = 0、总位移 = `delta`。

    ★ 为什么不用"ease-out"（`1−(1−u)²`）：它起点斜率为 2×平均，会让骨盆在触地
      **之后反而加速下坠**（实测 −131 mm/帧 vs 触地前的 −79），物理上讲不通。
      本式起点斜率**等于弹道末竖速** ⟹ 支点切换处一阶连续。
    """
    t = span
    c2 = 3.0 * delta / (t * t) - 2.0 * v0 / t
    c3 = -2.0 * delta / (t ** 3) + v0 / (t * t)
    return v0 * k + c2 * k * k + c3 * k ** 3


def pelvis_z_at(frame):
    """骨盆世界 z（米）。★ 三段：弹道 / 触地帧（弹道最后一点）/ 落地曲线。

    ★★ `f > PLATEAU` 必须**钳住 k**（`k = min(k, span)`）：三次 Hermite 一旦被
       **外推**（k > span），骨盆 z 会重新抬升 —— 实测 f20 抬到 472.8 mm，
       等于"反弹"漏进了位移层（`end_vz_zero_ok` / `landing_no_bounce_ok` /
       `landing_plateau_ok` / `root_motion_ok` 一起变红）。
       钳住之后 `f ≥ PLATEAU` 骨盆 z **构造性**恒 = `Z_PELVIS_END`。
    """
    if frame <= LAND:
        z = ball_z(frame)
        if NO_VZ:
            # ③ 抽掉 vz 继承：前段**不再下落**（vz ≡ 0）⟹ `vz_fall_then_stop_ok` 必红。
            #    ★ D13 教训 3：旋钮要真的接进代码。旧实现只把 f0 压到 `ball_z(1)`，
            #    结果 f≥2 仍在落、`prefix_min < 0` 照旧成立 ⟹ 判据**压根不红**（空接线）。
            z = ball_z(0)
        return z + pelvis_bump(frame)
    if NODESCENT:
        # ⑤ 抽掉落地下降主驱动：骨盆停在触地高度（腿不再压缩）
        return ball_z(LAND) + pelvis_bump(frame)
    span = landing_count()
    k = min(landing_k(frame), span)          # ★ 钳住：末段逐位固定在 Z_PELVIS_END
    return (ball_z(LAND) + _hermite(k, span, Z_PELVIS_END - ball_z(LAND), VZ_LAND)
            + pelvis_bump(frame))


def pelvis_y_at(frame):
    """骨盆世界 y（米）。★ 后倒的水平分量：绕双脚向 **+Y** 退出（同一条 Hermite）。

    ★ 与 D14 **符号相反**：D14 向 −Y 扑出 0.576 m（前倒）；本支向 +Y 退出
      `PELVIS_Y_END − PELVIS_Y_START`（量由实测确定，**不照抄 0.576**）。
    """
    if frame <= LAND:
        return PELVIS_Y_START
    span = landing_count()
    k = min(landing_k(frame), span)          # ★ 同上：末段逐位固定在 PELVIS_Y_END
    return PELVIS_Y_START + _hermite(k, span, PELVIS_Y_END - PELVIS_Y_START, 0.0)


def pelvis_vz_at(frame):
    """一阶差分竖速（mm/帧，与 D12/D13 的 `end_vz_mm_per_frame` 同口径）。"""
    return (pelvis_z_at(frame) - pelvis_z_at(frame - 1)) * 1000.0


# =============================================================== 反向验证旋钮
BUMP_MM = _env_f("D15_TP_BUMP", 0.0)
SEAM_ZERO = _env_b("D15_TP_SEAM_ZERO")
ZERO_ACTION = "Idle_01" if SEAM_ZERO else SEAM_ACTION
ZERO_FRAME = 0 if SEAM_ZERO else SEAM_FRAME
NO_VZ = _env_b("D15_TP_NOVZ")
NO_SUPINE = _env_b("D15_TP_NOSUPINE")
NODESCENT = _env_b("D15_TP_NODESCENT")
# ★ ⑤ 后倒俯仰**符号翻正**（变成"前倒"）—— D14 没有这一组，它守的是"方向"。
FLIP_SIGN = _env_b("D15_TP_FLIPSIGN")
# ★ ⑥ 抽掉**抬腿**驱动（腿不抬 ⟹ `legs_lift_ok` 必红）。
NO_LEGS = _env_b("D15_TP_NOLEGS")


def pelvis_bump(frame):
    """★ 反向验证 ② 用：把"反弹"灌回**位移层**（正常 = 0）。

    口径 = 触地帧起，骨盆每帧再抬 `BUMP_MM`（mm/帧）⟹ 该帧 `vz` 的增量 = `BUMP_MM`。
    ★★ 为什么必须**逐帧累加**而不是"只在触地帧抬一次"：落地曲线的 `vz` 从 −82.6 mm/帧
      单调升到 0，一次性 +30 mm 只是把触地帧抬高、`vz` 依旧全负 ⟹ `landing_no_bounce_ok`
      **压根不红**（D14 实测：只加在 `frame <= LAND` 时该判据绿）。改成逐帧 +30 mm/帧后
      末段 `vz` 被抬到 **+30 mm/帧** ⟹ 与计划原文「② … ⟹ `ballistic_until_land_ok`
      + `landing_no_bounce_ok`」**逐条对上**（D14 实测 `vz_land_max = 30.0`，容差 2.0）。
    """
    if BUMP_MM <= 0.0:
        return 0.0
    if frame <= LAND:
        return BUMP_MM / 1000.0
    return (BUMP_MM / 1000.0) * float(frame - LAND + 1)


# =============================================================== 阈值
SEAM_TOL = 1e-6
NO_TELEPORT_MAX_DEG = 25.0
REACH_MAX_RATIO = 0.995
BALLISTIC_TOL = BALLISTIC_TOL_MM
# ---- ★ 离地 / 触地（口径与 D14 不同：触地**载体分两次**，脚 → 臀）----------
AIRBORNE_MIN_MM = _env_f("D15_AIRBORNE_MIN", 100.0)   # 触地前全身最低 ≥ 100 mm
LAND_EVENT_MAX_MM = _env_f("D15_LAND_EVENT_MAX", 5.0)  # 触地帧全身最低 ≤ 5 mm
CONTACT_LO_MM = _env_f("D15_CONTACT_LO", 2.0)          # 触地帧鞋底可允许的最低（鞋网格公差）
LAND_PLATEAU_TOL_MM = _env_f("D15_PLATEAU_TOL", 0.05)
NO_BOUNCE_MAX_MM = _env_f("D15_BOUNCE_MAX", 2.0)
# ★ 触地帧目标鞋底高（实测校准用）：取小正数，稳稳落在 [−2, +6] 内
TARGET_LAND_SOLE_MM = _env_f("D15_LAND_SOLE", 1.0)
# ---- ★ 后倒俯仰（主承载，**负值**，与 D14 一正一负互相守着）----------------
SUPINE_END_MIN_DEG = _env_f("D15_SUPINE_MIN", 75.0)     # 末帧躯干世界俯仰 ≤ −75°
SUPINE_RISE_MIN_DEG = _env_f("D15_SUPINE_RISE", 30.0)   # 从触地帧起还要再转 ≥ 30°
PITCH_TARGET_PELVIS = _env_f("D15_PITCH_PELVIS", -74.0)
PITCH_TARGET_CHEST = _env_f("D15_PITCH_CHEST", -88.0)
PITCH_TARGET_HEAD = _env_f("D15_PITCH_HEAD", -94.0)
# ---- ★ 压缩：本支是**髋屈**（臀坐实、膝抬起）+ 膝屈**持续** ------------------
HIP_FLEX_MIN_DEG = _env_f("D15_HIPFLEX_MIN", 45.0)     # 髋屈角（绝对）峰值 ≥ 45°
HIP_FLEX_SIT_MIN_DEG = _env_f("D15_HIPFLEX_SIT", 8.0)  # SIT_PEAK(f10) 髋屈角（相对触地帧）≥ 8°
KNEE_SUSTAIN_MIN_DEG = _env_f("D15_KNEE_MIN", 60.0)    # 躺平段膝屈角**不许伸直**
# ★ 吸震**速率**阈值（膝屈角的一阶差分，度/帧）—— 触地帧骨盆一帧掉 82.8 mm，
#   膝以 ~24°/帧 屈曲吸收；D14 实测该帧 `max_frame_step = 23.365°`（同源同量级）。
COMPRESS_MIN_DEG = _env_f("D15_COMPRESS_RATE", 12.0)
COMPRESS_WINDOW = (LAND + 1, LAND + 4)                 # 峰值必须落在这一段
# ---- ★ 臀触地 / 后脑贴地 / 腿抬起 ------------------------------------------
BUTT_CONTACT_MAX_MM = _env_f("D15_BUTT_MAX", 5.0)       # 臀区网格触地阈值
BUTT_AIRBORNE_MIN_MM = _env_f("D15_BUTT_AIR", 200.0)    # 触地前臀区网格 ≥ 200 mm
HIP_PROBE_TOL_MM = _env_f("D15_HIP_PROBE_TOL", 3.0)     # 骨盆/后脑/双肩四点贴地稳定
LEGS_LIFT_MIN_MM = _env_f("D15_LEGS_LIFT", 50.0)        # 躺平段鞋底离地 ≥ 50 mm
HEAD_TAIL_MAX_MM = _env_f("D15_HEAD_TAIL_MAX", 260.0)   # 仰面时后脑（head 尾端）高
# ---- ★ 打击停顿（触地帧 2 帧）---------------------------------------------
HITSTOP_MIN_FRAMES = _env_f("D15_HITSTOP_MIN", 2.0)
HITSTOP_POSE_TOL_DEG = _env_f("D15_HITSTOP_TOL", 1.0e-6)
# ---- 收招不许瞬停（末 6 帧增量单调收敛 —— 清单 §0.6 口径）-----------------
NO_SNAP_TAIL_FRAMES = _env_f("D15_SNAP_TAIL", 6.0)
# ---- 定格自持 --------------------------------------------------------------
END_HOLD_MAX_DEG = _env_f("D15_END_HOLD_TOL", 0.5)
# ---- 滚转回位（D11 教训 3 → D12/D13/D14 照抄 → 本支继续）-----------------
ROLL_WEIGHT_MODE = os.environ.get("D15_ROLL_WEIGHT", "always").strip().lower()
ROLL_BONES = tuple(
    item for item in os.environ.get(
        "D15_ROLL_BONES",
        "upperarm.L,forearm.L,hand.L,upperarm.R,forearm.R,hand.R").split(",")
    if item)
ROLL_ITER = max(1, int(os.environ.get("D15_ROLL_ITER", "2")))
# ---- 穿模 ------------------------------------------------------------------
CLIP_MAX_MM = _env_f("D15_CLIP_MAX", 0.0)
CLIP_EVERY = int(os.environ.get("D15_CLIP_EVERY", 3))
# ---- 零位/接缝复显守卫 -----------------------------------------------------
SEAM_REPLAY_POS_MAX_MM = _env_f("D15_SEAM_POS", 0.01)
SEAM_REPLAY_DIR_MAX_DEG = _env_f("D15_SEAM_DIR", 0.05)

# =============================================================== 驱动标量
#   `supine` —— ★ **主驱动 1**：躯干**后倒俯仰**（触地后开始，SUPINE_PEAK 到位）
#   `brace`  —— ★ **主驱动 2**：双臂被甩开、向体侧/身后摊平（与俯仰同相）
#   `legs`   —— ★ **主驱动 3**：双腿**因惯性抬起**（触地后开始，膝朝上）
#   `decay`  —— D13 的"横折"残余衰减（本支起来后横折必须退场）
#   `land_curve` 由 pelvis_z_at / pelvis_y_at 的 Hermite 承担（不在标量表里）
#   ★ 触地 2 帧停顿：`supine` / `brace` 在 f7~f8 **逐帧同值** ⟹ 上身姿态构造性冻结，
#     而骨盆继续下坠、**双腿继续抬起**（"砸地"的顿感 = 上身停、下身还在动）。
#   ★★ 曲线形状的硬约束（f8→f9 是"解冻帧"，最容易出尖峰）：
#     解冻帧的增量不得超过前段（f6→f7）与后段（f9→f10）的增量 ⟹ "倒"的陡段
#     必须落在解冻**之后**。
#   ★ 手臂在**落地前**就开始被甩开（f3 起 0.10 ⟹ f6 已到 0.32）—— 物理读相：
#     被击飞的人在空中四肢本就在外张，落地前继续摊开，把行程摊到 15 帧上。
SUPINE_KEYS = ((0, 0.0), (6, 0.0), (LAND, 0.06), (HOLD_END, 0.06),
               (9, 0.13), (10, 0.25), (11, 0.39), (12, 0.54),
               (13, 0.70), (14, 0.86), (SUPINE_PEAK, 1.0), (PLATEAU, 1.0),
               (TOTAL, 1.0))
BRACE_KEYS = ((0, 0.0), (3, 0.10), (6, 0.32), (LAND, 0.42), (HOLD_END, 0.42),
              (9, 0.50), (10, 0.60), (11, 0.70), (12, 0.78),
              (13, 0.86), (14, 0.94), (SUPINE_PEAK, 1.0), (PLATEAU, 1.0),
              (TOTAL, 1.0))
# ★★ 抬腿起跳点**必须晚于触地帧**（f ≥ HOLD_END+1 = 9）——
#   为什么：`no_teleport` 的尖峰就在落地帧 `f8`（骨盆一帧掉 82.8 mm，膝必须快屈）。
#   D14 实测该帧 `max_frame_step = 23.365°`（@f8 `shin.L`，余量只有 1.6°）。
#   本支若在 f8 就让踝跟着抬（+9.6 mm），髋-踝距离多缩 9.6 mm ⟹ 膝屈速率再涨，
#   实测冲到 **26.02°（红）**。把抬腿推迟到 f9，f8 与 D14 逐位同构 ⟹ 尖峰回落到 D14 水平。
LEGS_KEYS = ((0, 0.0), (6, 0.0), (LAND, 0.0), (HOLD_END, 0.0),
             (9, 0.18), (10, 0.34), (11, 0.50), (12, 0.66),
             (13, 0.80), (14, 0.92), (SUPINE_PEAK, 1.0), (PLATEAU, 1.0),
             (TOTAL, 1.0))
DECAY_KEYS = ((0, 1.0), (6, 0.88), (9, 0.55), (11, 0.28), (13, 0.16),
              (PLATEAU, 0.14), (TOTAL, 0.14))


def supine(frame):
    """★ 主驱动 1：躯干**后倒**俯仰量（0~1）。"""
    if NO_SUPINE:
        return 0.0
    return UE.pwl(SUPINE_KEYS, float(frame), 0.0)


def brace(frame):
    """★ 主驱动 2：双臂被甩开、向体侧摊平量（0~1）。"""
    return UE.pwl(BRACE_KEYS, float(frame), 0.0)


def legs(frame):
    """★ 主驱动 3：双腿因惯性抬起量（0~1）。"""
    if NO_LEGS:
        return 0.0
    return UE.pwl(LEGS_KEYS, float(frame), 0.0)


def decay(frame):
    """D13 横折残余的衰减（0~1）。"""
    return UE.pwl(DECAY_KEYS, float(frame), 0.0)


# =============================================================== 世界俯仰目标
TORSO_BONES = ("root", "pelvis", "spine_01", "spine_02", "chest", "neck", "head")
PARENT_OF = {"root": None, "pelvis": "root", "spine_01": "pelvis",
             "spine_02": "spine_01", "chest": "spine_02", "neck": "chest",
             "head": "neck"}
ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")
LEG_BONES = ("thigh.L", "shin.L", "thigh.R", "shin.R")
SPINE_MIX_1 = _env_f("D15_MIX_S1", 0.30)
SPINE_MIX_2 = _env_f("D15_MIX_S2", 0.62)
NECK_MIX = _env_f("D15_MIX_NECK", 0.45)


def world_pitches(frame):
    """★★ 各骨**世界俯仰目标**（度，+ = 前屈/前倾）—— 本支核心解算。

    D13 解的是**侧倾**（横折，绕世界 X 的 rz 通道）；本支解的是**俯仰**。
    语义：躯干 `rx > 0` = 前屈/前倾，且俯仰角是绕**同一根世界 X 轴**累加的
    ⟹ **`W_self = W_parent + rx_self`**，反解 **`rx_self = W_self − W_parent`**
    （即成对轴上"rx_self = W_self − W_parent"，与计划 §3 给的口径逐字一致）。

    ★ f0 处 `p = 0` ⟹ 目标世界俯仰 = **接缝姿态自身的世界俯仰** ⟹ 本式在 f0
      逐位复现 `Air_Hit@18` 的躯干 rx（ry/rz 的交叉项在本支 ≤ 3° 量级）。
    """
    p = supine(frame)
    # ★ 反向验证 ⑤：把后倒俯仰的**符号翻正**（= 变成 D14 的"前倒"）⟹ `supine_pitch_ok` 必红。
    #   这是 D14 没有的一组 —— 它证明判据守的是**方向**，不只是幅度。
    s = -1.0 if FLIP_SIGN else 1.0
    w = {"root": SEAM_PITCH.get("root", 0.0)}
    w["pelvis"] = SEAM_PITCH["pelvis"] + s * SUPINE_EXTRA["pelvis"] * p
    w["chest"] = SEAM_PITCH["chest"] + s * SUPINE_EXTRA["chest"] * p
    w["spine_01"] = w["pelvis"] + SPINE_MIX_1 * (w["chest"] - w["pelvis"])
    w["spine_02"] = w["pelvis"] + SPINE_MIX_2 * (w["chest"] - w["pelvis"])
    w["head"] = SEAM_PITCH["head"] + s * SUPINE_EXTRA["head"] * p
    w["neck"] = w["chest"] + NECK_MIX * (w["head"] - w["chest"])
    return w


def torso_pose(frame):
    """世界俯仰目标 → 局部 `rx`；`ry`/`rz` = 接缝值 × 横折衰减。"""
    w = world_pitches(frame)
    d = decay(frame)
    out = {}
    for name in TORSO_BONES:
        parent = PARENT_OF[name]
        rx = w[name] - (w[parent] if parent else 0.0)
        base = ZERO.get(name, (0.0, 0.0, 0.0))
        out[name] = (rx, base[1] * d, base[2] * d)
    for side in SIDES:
        name = "shoulder." + side
        base = ZERO.get(name, (0.0, 0.0, 0.0))
        out[name] = (base[0], base[1] * d, base[2] * d)
    out["@loc"] = {"pelvis": A.wloc(0.0, pelvis_y_at(frame),
                                    pelvis_z_at(frame) - Z_PELVIS_REST)}
    return out


# =============================================================== 拳 / 肘目标
# ★ 本支的甩出方向 = 从 D13 末帧的"被击飞外甩"**继续摊开**到"仰卧时双臂向体侧铺开"。
#   物理读相：后倒的人两条手臂**不会**去前面撑地（那是 D14 的前扑读相），
#   而是**被惯性甩向体侧/身后、肘尖朝外上、前臂摊平**（仰卧的经典姿势）。
#   ★★ 与 D14 的差别必须在**方向**上读得出来：D14 的终点在 −Y（前方、手心朝下撑地），
#      本支的终点在 +Y 侧后方（体侧铺开）。两组的 `BRACE_DIR` 点积**明显为负**。
BRACE_DIR = {
    "L": tuple(float(x) for x in
               os.environ.get("D15_BRACE_L", "0.760,0.520,-0.386").split(",")),
    "R": tuple(float(x) for x in
               os.environ.get("D15_BRACE_R", "-0.760,0.520,-0.386").split(",")),
}
# ★ 肘极向量（仅当 `D15_POLE_SWING=1` 时是"摆动终点"；默认冻结在接缝值，见 `elbow_dir`）。
#   仰卧时肘尖朝**外上**：极向量 = 外 + 略后 + 上。
ELBOW_BRACE = {
    "L": tuple(float(x) for x in
               os.environ.get("D15_ELBOW_L", "0.620,0.300,0.724").split(",")),
    "R": tuple(float(x) for x in
               os.environ.get("D15_ELBOW_R", "-0.620,0.300,0.724").split(",")),
}
# ★★ 手骨朝向：与 `BRACE_DIR` **同向**（= 压平到臂轴上，掌心随前臂摊平）。
#   为什么非改不可（D14 实测教训，本支沿用同一条推理）：`arm_seat_tip` 把腕目标算成
#   `拳目标 − hand_dir×手长`。若 `hand_dir` 与臂轴夹角很大，则"拳可达 650 mm"这个
#   名义极限**用不上** —— 腕的可达极限只有 `l1+l2 ≈ 551.7 mm`，腕目标被推过极限
#   ⟹ 两骨 IK 打进**伸展奇异** ⟹ 前臂单帧世界旋转超 `no_teleport`(25°/帧)。
#   把 `hand_dir` 对齐到 `BRACE_DIR` ⟹ 腕距回到 ~0.93 ⟹ 奇异消失。
#   ★ f0 处 `brace = 0` ⟹ 手骨朝向 = `SEAM_HAND_DIR` **逐位不变** ⟹ 接缝不受影响。
BRACE_HAND_DIR = {
    "L": tuple(float(x) for x in
               os.environ.get("D15_HAND_L", "0.760,0.520,-0.386").split(",")),
    "R": tuple(float(x) for x in
               os.environ.get("D15_HAND_R", "-0.760,0.520,-0.386").split(",")),
}
BRACE_SPAN_RATIO = _env_f("D15_BRACE_SPAN", 0.94)
POLE_SWING = bool(_env_i("D15_POLE_SWING", 0))


def hand_dir_of(side, frame):
    """手骨世界朝向：由 `brace` 从接缝朝向球面插值到"压平沿臂轴"。"""
    b = brace(frame)
    d0 = Vector(SEAM_HAND_DIR[side]) if SEAM_HAND_DIR.get(side) else \
        Vector(BRACE_HAND_DIR[side])
    d1 = Vector(BRACE_HAND_DIR[side]).normalized()
    return _slerp_dir(d0.normalized(), d1, b)


def _slerp_dir(d0, d1, b):
    """两单位向量间的**球面**插值（角速度 ∝ Δb）。

    ★★ 为什么不能用 `(d0*(1-b) + d1*b).normalized()`：本支 `d0` 是接缝的
       "双臂被甩到头顶"方向、`d1` 是"前扑撑地"方向，**近乎反平行**（夹角 ~180°）。
       线性插值在 `b ≈ 0.5` 处合矢量长度趋近 0 ⟹ 归一化后方向**瞬间翻转**
       （实测 Δb = 0.14 就换出 27.7° 的单帧骨旋转，`no_teleport` 必红）。
       球面插值把角速度摊平到全段，单帧步长直接受 Δb 控制。
    """
    dot = max(-1.0, min(1.0, d0.dot(d1)))
    if dot > 0.9995:
        out = d0 * (1.0 - b) + d1 * b
        return out.normalized() if out.length > 1e-9 else d1
    if dot < -0.9995:
        # 完全反平行：没有唯一大圆 —— 用零位基准叉一个稳定的旋转轴
        axis = d0.cross(Vector((0.0, 0.0, 1.0)))
        if axis.length < 1e-6:
            axis = d0.cross(Vector((0.0, 1.0, 0.0)))
        axis.normalize()
        return (d0 * math.cos(math.pi * b) + axis * math.sin(math.pi * b)).normalized()
    omega = math.acos(dot)
    sin_o = math.sin(omega)
    out = (d0 * (math.sin((1.0 - b) * omega) / sin_o)
           + d1 * (math.sin(b * omega) / sin_o))
    return out.normalized() if out.length > 1e-9 else d1


def fist_target(arm, side, frame):
    """拳世界目标 = **肩位 + 方向 × 臂展**（必须相对肩，因为肩一直在动）。"""
    shoulder = Vector(A.bone_world(arm, "upperarm." + side, "head"))
    d0 = SEAM_FIST_DIR[side]
    d1 = Vector(BRACE_DIR[side]).normalized()
    b = brace(frame)
    direction = _slerp_dir(d0, d1, b)
    span = SEAM_SPAN[side] + \
        (BRACE_SPAN_RATIO * ARM_MAX[side] - SEAM_SPAN[side]) * b
    return shoulder + direction * span


def elbow_dir(side, frame):
    """肘部极向量（决定肘在"肘圆"上的方位角 = 臂平面）。

    ★★ 本支把极向量**冻结成接缝值**（`POLE_SWING = False`），这不是偷懒，是**必须**：
      实测 `axis·elbow`（臂轴与极向量的夹角余弦）在"扑"段前段从 0.892 一路涨到
      **0.9688**（夹角只剩 14.4°）—— 极向量几乎贴到臂轴上。此时极向量在
      「垂直于臂轴平面」上的投影方向对臂轴旋转的敏感度 ≈ `1/sin(14.4°) ≈ 4×`，
      实测放大到 **5.6×**：拳头方向每帧只走 8.6°，前臂世界旋转却 **47.9°/帧**
      （`no_teleport` 25°/帧）。冻结极向量后该尖峰**完全消失**（见门禁 10 对照）。
      ★ 物理读相也对：撑地时肘朝外后方基本不动，动的是前臂与腕。
      ★ 若要恢复摆动，`D15_POLE_SWING=1` 打开（ELBOW_BRACE 仍保留为摆动终点）。
    """
    if not POLE_SWING:
        d0 = SEAM_ELBOW_DIR.get(side)
        if d0:
            return Vector(d0).normalized()
    b = brace(frame)
    d0 = Vector(SEAM_ELBOW_DIR[side])
    d1 = Vector(ELBOW_BRACE[side]).normalized()
    out = d0 * (1.0 - b) + d1 * b
    return out.normalized() if out.length > 1e-9 else d1


# =============================================================== 踝目标
# ★ 空中段（`f < LAND`）：**脚本化的鞋底高度**（保证 `f < LAND` 鞋底 ≥ 100 mm 是构造性的）。
#   ★★ 鞋底目标 ≠ 踝高：脚绕踝转 `foot.rx` 时**鞋尖会下探**（f0 的 26° 实测下探
#      153.6 mm）⟹ 必须扣掉"鞋底−踝"落差 `foot_gap(tip)`（纯 `foot.rx` 的函数，
#      与腿姿无关，boot 里实测成表）。否则 f0 的踝会被压到比接缝低 93 mm
#      ⟹ 腿够不着 ⟹ `leg_reach_ok` 假红。
#   ★★ 鞋底脚本的两条硬约束（f6→f7 是"落地帧"，第二轮 `no_teleport` 就红在这里）：
#     ① 前段（f0~f6）必须与**身体下落同速**（≈53 mm/帧，对齐弹道的 60~78 mm/帧），
#        不能前段 50 mm/帧、末段突然 150 mm/帧（3×）⟹ 落地帧 shin.L 29.4°；
#     ② `f < LAND` 鞋底 ≥ 100 mm 是**判据要求**（`airborne_prefix_ok`）⟹ 末段**至少**
#        要走 100 mm。取 115 mm 留 15 mm 余量，配合"落地前把脚放平"（见 `TIP_KEYS`）
#        把踝高从 253.6 mm 压到 192.9 mm ⟹ 落地帧踝只掉 110.7 mm ⟹ shin ≈ 16°。
SOLE_DROP = ((1, 0.380), (2, 0.325), (3, 0.270), (4, 0.215),
             (5, 0.163), (6, 0.115), (7, 0.0))
SOLE_KEYS_FOR = {"L": (), "R": ()}       # boot 里按"实测接缝鞋底"补上 f0 这一档
# ★ 落地站姿（t=1 时相对**髋**的水平偏移）：收敛到"双脚略在髋后"的对称站姿。
#   为什么必须收敛：D13 的接缝姿态是**被击中的张开姿**（R 踝在髋后 286 mm、L 踝在
#   髋前 29 mm）。若原样落地，后倒时骨盆向 +Y 退出会把 R 腿**拉直超限**
#   （实测 `leg_reach_ratio_max = 1.129` ⟹ 腿够不着 ⟹ 鞋底陷进地里、腿姿崩）。
#   收敛到对称站姿后，后倒全程腿都在可达范围内。
LAND_STANCE_X = _env_f("D15_STANCE_X", 0.115)
LAND_STANCE_Y = _env_f("D15_STANCE_Y", -0.115)
# ★★ 落地**后**（`f ≥ LAND`）的"抬腿"目标 —— 本支与 D14 最大的机械差别。
#   物理：双脚在 `f = LAND` 先触地，随后躯干继续向 **+Y** 坐倒、臀部着地，
#   双腿**因惯性抬起**（膝朝上、鞋底离地）。⟹ D14 的"固定世界足迹 + 逐脚 ≤3 mm"
#   **在本支必然红**（腿抬起 ⟹ 鞋底离开足迹），必须换成"随髋 + 整体抬高"。
#   实现：X/Y **随髋**（相对偏移从"落地站姿"收敛到"抬腿站姿"），
#         Z **绝对**（从落地踝高抬到 `LIFT_Z_END`）⟹ "躺平段鞋底 ≥ 50 mm" 是**构造性**的。
#   ★★ 三个数（`-0.115 / 0.240 / -0.240`）是**扫参实测**出来的：落地站姿与抬腿站姿的
#      **方位角对齐**后，髋→踝轴在"扫过水平"那几帧的角速度最平缓
#      （`no_teleport` 单帧峰值 32.06° → 配上 `local` 钉 + 腿骨滚转搜索后 23.49°）。
LIFT_DX = _env_f("D15_LIFT_X", 0.240)          # 抬腿到位时相对髋的横向偏移（略外）
LIFT_DY = _env_f("D15_LIFT_Y", -0.240)         # 抬腿到位时相对髋的前后偏移（−Y = 身体前方 = 脚的方向）
#   ★ 为什么是 0.300（而不是 D14 口径的 ~0.155）：`local` 钉法下脚随小腿摆、
#     鞋底不再由踝高直接决定 ⟹ 必须把踝抬到 300 mm 才能让躺平段鞋底 ≥ 50 mm
#     （实测 260.7 mm）。这是"用抬高换掉脚的局部欧拉尖峰"的**明码代价**。
LIFT_Z_END = _env_f("D15_LIFT_Z", 0.300)       # 抬腿到位时的**绝对**踝高（米）
# ★★ `f = LAND + 1`（= 落地后第一帧）的踝高补正（米）。
#   为什么需要：`local` 钉法下脚随小腿摆，落地后第一帧膝要猛屈（吸震速率峰值 = f8）
#   ⟹ 鞋底被"滚"到地面**以下**（实测 −12.46 mm，其余帧全为正）。
#   把踝在 f8 抬 `BUMP` 就把鞋底抬回（实测 8 mm ⟹ −4.68 mm）。副作用：f8 的髋-踝
#   距离缩短 ⟹ 膝屈速率上涨（`no_teleport` 23.49° → 24.70°）。实测 13 mm 就翻红
#   （25.70°）⟹ 单独用它**最多只能给到 4 mm**。
LIFT_BUMP = _env_f("D15_LIFT_BUMP", 0.004)
# ★★ `local` 钉法下**脚局部 rx 的补正曲线**（度；负 = 脚尖上抬 ⟹ 鞋底抬高）。
#   为什么它比 `LIFT_BUMP` 干净：`LIFT_BUMP` 抬的是**踝**，缩短了髋-踝距离 ⟹
#   膝必须多屈 ⟹ 直接吃掉 `no_teleport` 余量（实测 8 mm 就花掉 1.2°）。
#   而**绕踝转脚**不改变踝的位置 ⟹ 髋-踝距离不变 ⟹ **膝屈一点不多**
#   （实测 `max_frame_step_deg` 恒 23.489°，与不补正时**逐位相同**）。
#   ★ 只在 `local` 钉法下有意义（`world` 钉会把这个世界朝向反过来吸收成局部尖峰，
#     实测那样做反而更糟：扫参 E 70.5 → F 74.4 → H 86.8 ⟹ 已弃用）。
#   ★ 实测（`local` 钉法，斜率 ≈ **1.3 mm/°**，比 `world` 钉下的 `foot_gap` 斜率
#     −2.94 mm/° 小 —— 因为局部 X 轴在 shin 转过之后**不再等于世界俯仰轴**）：
#     rx = −5° ⟹ 鞋底 −12.46 → −5.95 mm（+6.5 mm）；rx = −7° ⟹ −4.95 mm（+7.5 mm）。
#   ★★ 最终取 `bump = 4 mm` + `rx = −7°`：**落地后第一帧鞋底 = −1.18 mm**，
#     落在 §6「支撑脚脚底 −2 ~ +6 mm」带内；`no_teleport` = **23.811°**（余量 1.19°）。
#     单独 rx = −7° 只到 −4.95 mm；单独 bump = 4 mm 只到 −2.84 mm。
FOOT_RX = _env_f("D15_FOOT_RX", -7.0)
FOOT_RX_KEYS = ((LAND, 0.0), (LAND + 2, FOOT_RX), (TOTAL, FOOT_RX))
LIFT_Z_KEYS = {}                               # side -> 绝对踝高曲线（boot 里按实测落地踝高补 f=LAND）
# ★ 脚俯仰：落地**前**就把脚放平（tip=0）。为什么要提前：`foot_gap(tip)` 是"鞋底−踝"
#   落差，tip 越大鞋尖下探越多（tip=0 → −77.9 mm；tip=9° → −103.6 mm）。若落地瞬间
#   还带着 9° 俯角，踝高被抬到 253.6 mm，落地一帧要掉 171 mm ⟹ shin.L 29.4°/帧。
#   提前放平后踝高 192.9 mm，落地帧只掉 110.7 mm。
#   ★ 落地后（抬腿段）继续 tip=0：`keep_foot_lifted` 把脚的**世界朝向**钉在
#     "零位 + rx"，仰卧抬腿时鞋底仍朝下 ⟹ 画面读相正确（且与 D14 同一把尺子）。
TIP_KEYS = ((0, 26.0), (3, 14.0), (5, 4.0), (6, 0.0), (LAND, 0.0), (TOTAL, 0.0))
# ★★ 落地后的**世界俯仰终值**（本支新增旋钮）：世界钉的"倾角"本身也可以是一条平滑曲线。
#   为什么需要：世界钉把脚的**世界朝向**钉住 ⟹ 小腿世界转角全由脚的**局部**欧拉反向吸收
#   （实测 `foot.R` 单帧 54.2°，限额 25°）。让脚的**世界朝向也跟着转**（脚背绷直/脚尖下垂）
#   ⟹ 局部欧拉的负担按 `(1 − 跟随比)` 下降；代价是鞋底最低点（脚尖）被压低
#   （`foot_gap` 每 +1° ≈ −2.9 mm）⟹ 必须同步抬 `LIFT_Z_END` 把鞋底抬回 ≥50 mm。
FOOT_WTIP = _env_f("D15_FOOT_WTIP", 0.0)
if FOOT_WTIP:
    TIP_KEYS = ((0, 26.0), (3, 14.0), (5, 4.0), (6, 0.0), (LAND, 0.0),
                (HOLD_END, 0.0), (SUPINE_PEAK, FOOT_WTIP), (TOTAL, FOOT_WTIP))
FOOT_GAP_TIPS = (0.0, 4.0, 8.0, 12.0, 16.0, 20.0, 24.0, 28.0)
FOOT_GAP_MM = {}                          # tip -> {"L": mm, "R": mm}
FOOT_GAP_SYMMETRY_MM = {}                 # tip -> |L − R|（守卫：tip=0 必须 ≈ 0）
# ★★ 落地**后**脚的钉法（`D15_FOOT_PIN`，默认 `world`）——
#   `world`：世界朝向恒钉（鞋底高可预测，但脚的局部欧拉要吸收小腿的世界转角）；
#   `local`：局部欧拉冻在落地帧（脚随小腿摆，无局部尖峰，但鞋底要另抬 `LIFT_Z_END`）。
#   两者都已实测，见 `_foot_euler`。
# ★ 默认 `local`：实测两条路的**取舍**（`no_teleport` 峰值）——
#     `world` 钉：23.5° 起跳但**尖峰在 `foot.R`**，实测冲到 **53~54°（红）**；鞋底可预测（63.8 mm）。
#     `local` 钉：脚局部欧拉构造性无尖峰 ⟹ 全场峰值降到小腿的 **23.49°（全绿）**；
#                 代价是鞋底不可预测 ⟹ 已用 `LIFT_Z_END = 0.300` 补回（260.7 mm）。
#   ⟹ **最终默认 `local`**（配合腿骨滚转搜索）。
FOOT_PIN = os.environ.get("D15_FOOT_PIN", "local").strip().lower()
FOOT_LAND_EULER = {}      # side -> f = LAND 时脚的**局部**欧拉（世界钉的结果）

# ★★ `no_teleport` 的真凶诊断（本轮扫参结论）：尖峰不是"腿真的在飞"，而是
#   **小腿的局部欧拉走进了 XYZ 万向节锁带**（`|ry| → 90°`）。证据：
#     · `knee_deg_abs` 在 f12~f15 几乎恒定（88.08 → 88.79 → 85.08 → 80.31），
#       物理上膝盖**没有**在猛转；可是 `shin.R` 的局部欧拉单帧跳 **44~45°**。
#     · `UE._set_euler_nearest` 已经有"绕骨轴滚转搜索"（`ROLL_BONES`）用来把欧拉
#       路径挪出锁带 —— 但 `ROLL_BONES` 目前**只有臂骨**（`C14` 时加的），腿骨不在里面。
#   ★ 默认把腿骨（`thigh.*/shin.*`）也加进 `ROLL_BONES`（实测 32.06° → 23.49°）。
#     滚转是绕**骨轴**的 ⟹ 骨根/骨尖不动，`leg_seat` 的两骨 IK 解、贴地、剪影
#     全部**不受影响**，只是把欧拉表示挪出锁带。**这不是放宽容差**，是换等价表示。
#     ★ 为什么**不**把 `foot.*` 也加进去：脚的滚转就是绕鞋的长轴转 ⟹ 鞋底会侧倾，
#       是**真几何变化**，不再是等价表示。
ROLL_LEGS = os.environ.get("D15_ROLL_LEGS", "1").strip() not in ("", "0", "false")
if ROLL_LEGS:
    UE.ROLL_BONES = frozenset(set(UE.ROLL_BONES)
                              | {"thigh.L", "thigh.R", "shin.L", "shin.R"})


def _sole_target(side, frame):
    return _lin(SOLE_KEYS_FOR[side], frame)


def foot_gap(tip_deg, side):
    """鞋底最低点相对踝的世界高度差（**米**，负值 = 鞋底在踝下）。"""
    tips = sorted(FOOT_GAP_MM)
    if not tips:
        return -Z_ANKLE_REST
    row = FOOT_GAP_MM
    if tip_deg <= tips[0]:
        return row[tips[0]][side] / 1000.0
    if tip_deg >= tips[-1]:
        return row[tips[-1]][side] / 1000.0
    for index in range(len(tips) - 1):
        a, b = tips[index], tips[index + 1]
        if a <= tip_deg <= b:
            va, vb = row[a][side], row[b][side]
            return (va + (vb - va) * (tip_deg - a) / (b - a)) / 1000.0
    return row[tips[-1]][side] / 1000.0


def _measure_foot_gap(arm):
    """★ 实测"鞋底 − 踝"随 `foot.rx` 的变化（纯函数：脚世界朝向恒 = rest + rx）。

    ★★ 必须先 `view_layer.update()` 再设脚：`pose_bone.matrix` 的 setter 是用
       **父骨当前矩阵**反算 `matrix_basis` 的。`reset_pose` 之后不刷一次，
       设脚时读到的还是**上一姿态的陈旧 shin 矩阵** ⟹ 第一档（tip=0）量出
       `L = −93.6 mm / R = −77.9 mm`（同一姿态两侧竟不相等，物理上不可能）。
    """
    FOOT_GAP_MM.clear()
    for tip in FOOT_GAP_TIPS:
        A.reset_pose(arm)
        bpy.context.view_layer.update()          # ★ 先让 reset 生效，再设脚
        for side in SIDES:
            UE.keep_foot_lifted(arm, side, tip)
        bpy.context.view_layer.update()
        low = A.foot_lowest_by_side()
        row = {}
        for side in SIDES:
            ank = Vector(A.bone_world(arm, "foot." + side, "head"))
            row[side] = (low[side][2] - ank.z) * 1000.0
        FOOT_GAP_MM[tip] = row
    # ★ 守卫：tip=0 两侧必须相等（同一朝向 ⟹ 同一落差）。差 > 1 mm = 量法坏了。
    base = FOOT_GAP_MM[FOOT_GAP_TIPS[0]]
    FOOT_GAP_SYMMETRY_MM[0] = round(abs(base["L"] - base["R"]), 4)


def _air_ankle(arm, side, frame):
    """空中段踝目标 = 髋 + **从接缝偏移收敛到落地站姿** + **脚本鞋底高度**。

    ★ 收敛（不是照抄接缝偏移）是本支落地机械自洽的前提，见 `LAND_STANCE_*` 注释。
    ★ 鞋底目标是**脚本化**的（`SOLE_KEYS_FOR`）⟹ `f < LAND` 鞋底 ≥ 100 mm 是**构造性**的；
      踝高 = 鞋底目标 − `foot_gap(foot.rx)`（扣掉鞋尖下探）。
    """
    hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
    sgn = 1.0 if side == "L" else -1.0
    t = _clamp(float(frame) / float(max(1, LAND)), 0.0, 1.0)
    off0 = SEAM_HIP_OFF[side]
    off1 = (LAND_STANCE_X * sgn, LAND_STANCE_Y)
    dx = off0[0] + (off1[0] - off0[0]) * t
    dy = off0[1] + (off1[1] - off0[1]) * t
    tip = _lin(TIP_KEYS, frame)
    z = _sole_target(side, frame) - foot_gap(tip, side)
    return Vector((hip.x + dx, hip.y + dy, z))


def _lift_ankle(arm, side, frame):
    """★ 落地后踝目标：X/Y **随髋**（落地站姿 → 抬腿站姿），Z 走**绝对**抬起曲线。

    ★★ 与 D14 的关键差别：D14 的 `f ≥ LAND` 踝目标 = **固定世界足迹**（双脚一拍不滑）；
      本支后倒时腿要**抬起来**，锚在世界上就会把腿拉直 ⟹ 必须随髋，
      且 Z 抬到 `LIFT_Z_END` ⟹ 躺平段鞋底 ≥ 50 mm 是构造性的。
    """
    hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
    sgn = 1.0 if side == "L" else -1.0
    g = legs(frame)
    dx = LAND_STANCE_X * sgn * (1.0 - g) + LIFT_DX * sgn * g
    dy = LAND_STANCE_Y * (1.0 - g) + LIFT_DY * g
    return Vector((hip.x + dx, hip.y + dy, _lin(LIFT_Z_KEYS[side], frame)))


def ankle_target(arm, side, frame):
    """★ 分段：`f < LAND` 髋相对（空中）；`f ≥ LAND` **随髋抬腿**（本支与 D14 相反）。"""
    if frame >= LAND and LIFT_Z_KEYS.get(side):
        return _lift_ankle(arm, side, frame)
    return _air_ankle(arm, side, frame)


def _foot_euler(arm, side, frame):
    """★ 脚：默认**全程世界钉**（世界朝向 = rest + `foot.rx`，D14 同一把尺子）。

    ★★ 两条路都已实测，各有代价（`D15_FOOT_PIN` 扫参用，默认 `world`）：
      - `world`（世界钉）：鞋底高 = 踝高 − `foot_gap(rx)` **可预测**（躺平段构造性 77 mm），
        但小腿世界转角全由脚的**局部**欧拉反向吸收 ⟹ `foot.R` 单帧尖峰（实测 47~54°）。
      - `local`（局部钉，`f ≥ LAND` 起把脚的局部欧拉冻在落地帧值）：脚随小腿自然摆动
        ⟹ 局部欧拉**构造性**无尖峰；但鞋底**不可预测**（实测躺平段只剩 0.85 mm）
        ⟹ 必须同步把 `LIFT_Z_END` 抬高到让鞋底 ≥ 50 mm（腿抬得更高）。
    """
    name = "foot." + side
    prev = JS._PREV_EULER.get(name)
    if FOOT_PIN == "local" and frame >= LAND and FOOT_LAND_EULER.get(side):
        base = FOOT_LAND_EULER[side]
        rx = base[0] + _lin(FOOT_RX_KEYS, frame)
        return JS._unwrap_xyz(prev, (rx, base[1], base[2]))
    return JS._unwrap_xyz(prev, UE.keep_foot_lifted(
        arm, side, _lin(TIP_KEYS, frame)))


# =============================================================== 模块级表
ZERO = {}
ZERO_WORLD = {}
ZERO_BASIS = {}
ZERO_DIR = {}
SEAM_FIST = {}
SEAM_FIST_DIR = {}
SEAM_SHOULDER = {}
SEAM_SPAN = {}
SEAM_ELBOW_DIR = {}
SEAM_HAND_DIR = {}
SEAM_ANKLE = {}
SEAM_HIP = {}
SEAM_HIP_OFF = {}
SEAM_PITCH = {}
SUPINE_EXTRA = {}
ANKLE_0 = {}
KNEE_DIR = {}
ARM_MAX = {}
Z_SEAM = 0.0
LAND_ANKLE = {}
LAND_SOLE_MM = {}
SEAM_SOLE_MM = {}
FOOT_LOCKED = [False]
LOCK_POSE = {}
HITSTOP_POSE = {}
_HITSTOP_REUSED = [0]
_LOCK_REUSED = [0]
SEAM_MATCH = {"src": None, "geom_pos": None, "geom_dir": None,
              "pos_bone": None, "dir_bone": None, "per_bone": {},
              "matched": False}


# =============================================================== 姿态装配
def arm_seat_tip(arm, pose, side, tip_target, elbow_dir_in, hand_dir_in=None):
    """D05 立的臂解算：两骨 IK 打在腕上，手骨按零位自己的折角单独瞄。

    ★ `hand_dir_in`（新增）：手骨**世界朝向**。默认沿用接缝常量；本支在"扑"段把它
      压平到臂轴上（见 `hand_dir_of`），否则腕目标超出 `l1+l2` 打进伸展奇异。
    """
    up, fo, hd = ("upperarm." + side, "forearm." + side, "hand." + side)
    dims = UE.ARM_LEN[side]
    l1, l2 = dims["upper"], dims["forearm"]
    hand_dir = (Vector(hand_dir_in).normalized() if hand_dir_in is not None
                else SEAM_HAND_DIR[side])
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


def _copy_pose(source):
    return {k: (tuple(v) if not k.startswith("@")
                else {kk: tuple(vv) for kk, vv in v.items()})
            for k, v in source.items()}


def build_pose(arm, frame):
    # ★ f0 = **逐位**接缝姿态（`Air_Hit@18`）—— 不走解算，原样返回。
    if frame <= 0:
        return _copy_pose(ZERO)

    # ★ 触地 2 帧停顿（§2）：`LAND+1` 逐位复用 `LAND` 的姿态（**上身**），
    #   只把骨盆 `@loc` 换成落地曲线的值；**双腿照常解算**（脚钉在足迹上吸收冲击）
    #   —— 地面受击不能像 D13 那样整身锁存，否则脚会跟着骨盆沉进地里。
    if HITSTOP_POSE and LAND < frame <= HOLD_END:
        pose = {}
        for key, value in HITSTOP_POSE.items():
            if key == "@loc":
                locs = {k: tuple(v) for k, v in value.items()}
                locs["pelvis"] = A.wloc(0.0, pelvis_y_at(frame),
                                       pelvis_z_at(frame) - Z_PELVIS_REST)
                pose["@loc"] = locs
            else:
                pose[key] = tuple(value)
        _HITSTOP_REUSED[0] += 1
        # ★★ 必须先 `apply_pose`：`UE.leg_seat` 读的是**当前骨架状态**里的髋位。
        #    漏了这一步，腿就是对着**上一帧的骨盆**解算、却按**本帧骨盆**打帧
        #    ⟹ 实测 f8 鞋底 −85.86 mm（陷进地里 86 mm）。
        A.apply_pose(arm, pose)
        # 双腿重解（脚贴地）
        for side in SIDES:
            UE.leg_seat(arm, pose, side, ankle_target(arm, side, frame),
                        KNEE_DIR[side])
        for name in ("foot.L", "foot.R"):
            pose[name] = _foot_euler(arm, name.split(".")[1], frame)
        for name, value in pose.items():
            if not name.startswith("@"):
                JS._PREV_EULER[name] = tuple(value)
        return pose

    # ★ 贴地自持：f > PLATEAU ⟹ **逐位复用** f16 的解，只换骨盆 `@loc`
    #   ⟹ 整段沿地面曲线平移、姿态构造性冻结。
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
        _LOCK_REUSED[0] += 1
        return pose

    pose = torso_pose(frame)
    A.apply_pose(arm, pose)
    for side in SIDES:
        UE.leg_seat(arm, pose, side, ankle_target(arm, side, frame),
                    KNEE_DIR[side])
    for name in ("foot.L", "foot.R"):
        pose[name] = _foot_euler(arm, name.split(".")[1], frame)
    for side in SIDES:
        arm_seat_tip(arm, pose, side, fist_target(arm, side, frame),
                     elbow_dir(side, frame), hand_dir_of(side, frame))
    if ROLL_WEIGHT_MODE != "off":
        weight = 1.0
        for _ in range(ROLL_ITER):
            for name in ROLL_BONES:
                if name in arm.pose.bones:
                    _roll_return(arm, pose, name, weight)
            for side in SIDES:
                arm_seat_tip(arm, pose, side, fist_target(arm, side, frame),
                             elbow_dir(side, frame), hand_dir_of(side, frame))
    pose.update(A.FIST)
    for name, value in pose.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)
    if frame == LAND:
        HITSTOP_POSE.update(_copy_pose(pose))
    if frame == PLATEAU:
        LOCK_POSE.update(_copy_pose(pose))
    return pose


def solve_pose(arm, frame, meshes=None):
    return build_pose(arm, frame)


# =============================================================== 滚转回位修正
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
    """世界**俯仰**（矢状面 YZ，度）：+ = 前屈，− = 后仰。"""
    return -math.degrees(math.atan2(direction.y, direction.z))


def _lat(direction):
    """世界**侧倾**（正面平面 XZ，度）：+ = 倾向 +X（角色左）。"""
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
        "pelvis_lat_deg": _lat(Vector(A.bone_direction(arm, "pelvis"))),
        "chest_lat_deg": _lat(Vector(A.bone_direction(arm, "chest"))),
        "head_lat_deg": _lat(Vector(A.bone_direction(arm, "head"))),
        "pelvis_pitch_deg": _pitch(Vector(A.bone_direction(arm, "pelvis"))),
        "chest_pitch_deg": _pitch(Vector(A.bone_direction(arm, "chest"))),
        "head_pitch_deg": _pitch(Vector(A.bone_direction(arm, "head"))),
        "pelvis": Vector(A.bone_world(arm, "pelvis", "head")),
        "hip_z": {s: Vector(A.bone_world(arm, "thigh." + s, "head")).z
                  for s in SIDES},
        "ankle": {s: Vector(A.bone_world(arm, "foot." + s, "head"))
                  for s in SIDES},
        "shoulder": {s: Vector(A.bone_world(arm, "upperarm." + s, "head"))
                     for s in SIDES},
        "knee_deg": {s: _knee_angle(arm, s) for s in SIDES},
        # ★ 本支新增：后倒主承载量（髋屈角）+ 后脑点（`head` 尾端）
        "hip_flex_deg": {s: _hip_flex(arm, s) for s in SIDES},
        "head_tail": Vector(A.bone_world(arm, "head", "tail")),
    }


def _foot_clearance():
    low = A.foot_lowest_by_side()
    return {s: (low[s][2] if low[s] is not None else None) for s in SIDES}


# ---- ★ 臀/背区 & 后脑：**网格级**载体（不是骨位）--------------------------
#   ★★ 为什么必须网格级：仰卧时 `pelvis` 骨（髋关节）停在 ~`Z_PELVIS_END`（≈220 mm，
#      髋关节在身体半厚处），**永远到不了 0**。真正"贴地"的是**臀/背区网格**。
#      D14 的 `foot_probe` 本来就是网格级（鞋网格），本支也必须同级别，两支才可比。
#   ★★ `Jacket_Hem` / `Jacket_Hem_Line` 是**已知模型侧绑定遗漏**（`parent=null`、
#      `vgroups=0`，钉在世界原点、**不随骨架动**）⟹ 绝不能进载体集合（否则最低点
#      恒为 ~900 mm，判据变成常量）。D12~D14 的像素探针同样把它们排除。
BUTT_OBJECTS = tuple(
    n for n in os.environ.get("D15_BUTT_OBJECTS", "Suit_Torso,Jacket_Vent").split(",")
    if n)
HEAD_OBJECTS = tuple(PD.HEAD_MESHES)


def _mesh_low_mm(names):
    """给定网格对象集合的**逐对象**最低 z（毫米）；走 depsgraph，蒙皮件会跟随骨架。"""
    dg = bpy.context.evaluated_depsgraph_get()
    out = {}
    for name in names:
        obj = bpy.data.objects.get(name)
        if obj is None or obj.type != "MESH":
            continue
        ev = obj.evaluated_get(dg)
        me = ev.to_mesh()
        if len(me.vertices) == 0:
            ev.to_mesh_clear()
            continue
        mw = ev.matrix_world
        out[name] = min((mw @ v.co).z for v in me.vertices) * 1000.0
        ev.to_mesh_clear()
    return out


def _lowest_of(names):
    row = _mesh_low_mm(names)
    return None if not row else min(row.values())


def _hip_flex(arm, side):
    """髋屈角（度，0 = 躯干与大腿共线；越大 = 折得越狠）。

    ★ 口径：躯干轴（`pelvis` 骨方向）与大腿骨方向的夹角，取 **180° − 夹角**
      （零位站立时两骨近似反向 ⟹ 该式 ≈ 0）。
    """
    torso = Vector(A.bone_direction(arm, "pelvis")).normalized()
    thigh = Vector(A.bone_direction(arm, "thigh." + side)).normalized()
    return 180.0 - math.degrees(math.acos(max(-1.0, min(1.0, torso.dot(thigh)))))


def _worst_step(samples, index_a, index_b, skip_loc=True):
    ea, eb = samples[index_a]["euler"], samples[index_b]["euler"]
    worst, at = 0.0, None
    for name in set(ea) | set(eb):
        a = ea.get(name, (0.0, 0.0, 0.0))
        b = eb.get(name, (0.0, 0.0, 0.0))
        step = max(abs(x - y) for x, y in zip(a, b))
        if step > worst:
            worst, at = step, (samples[index_b]["frame"], name)
    return worst, at


def _worst_step_bones(samples, index_a, index_b, bones):
    """只在给定骨集合上量单帧步长（触地停顿只看**上身**：腿在吸震，豁免）。"""
    ea, eb = samples[index_a]["euler"], samples[index_b]["euler"]
    worst, at = 0.0, None
    for name in bones:
        a = ea.get(name, (0.0, 0.0, 0.0))
        b = eb.get(name, (0.0, 0.0, 0.0))
        step = max(abs(x - y) for x, y in zip(a, b))
        if step > worst:
            worst, at = step, (samples[index_b]["frame"], name)
    return worst, at


UPPER_BONES = (TORSO_BONES + ("shoulder.L", "shoulder.R") + ARM_BONES)


def hit_assertions(arm, action, samples, meshes):
    res = {}
    scene = bpy.context.scene
    arm.animation_data.action = action
    A._bind_slot(arm, action)

    # ---- 接缝真值 + 逐帧扫描
    arm.animation_data.action = None
    A.apply_pose(arm, ZERO)
    bpy.context.view_layer.update()
    zero = _body_metrics(arm)
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    per, clear, feet, butt, headm = {}, {}, {}, {}, {}
    _LEG_AXIS = {}
    for frame in range(0, TOTAL + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        per[frame] = _body_metrics(arm)
        clear[frame] = _foot_clearance()
        feet[frame] = A.foot_lowest_by_side()
        butt[frame] = _lowest_of(BUTT_OBJECTS)
        headm[frame] = _lowest_of(HEAD_OBJECTS)
        if os.environ.get("D15_TRACE"):
            # ★ 诊断 `no_teleport`：髋→踝**目标轴**本身 slewing 有多快（IK 的输入量）。
            row = {}
            for side in SIDES:
                hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
                delta = Vector(ankle_target(arm, side, frame)) - hip
                row[side] = ((delta.normalized() if delta.length > 1e-9
                              else Vector((0.0, 0.0, -1.0))))
            _LEG_AXIS[frame] = row

    zs = {f: per[f]["pelvis"].z for f in per}
    ys = {f: per[f]["pelvis"].y for f in per}
    xs = {f: per[f]["pelvis"].x for f in per}
    cpitch = {f: per[f]["chest_pitch_deg"] for f in per}

    if os.environ.get("D15_TARGETTRACE"):
        # ★ 诊断 `no_teleport`：目标方向本身 slewing 快，还是 IK 抖动？
        tgt = {}
        for frame in range(0, TOTAL + 1):
            scene.frame_set(frame)
            bpy.context.view_layer.update()
            row = {}
            for side in SIDES:
                sh = Vector(A.bone_world(arm, "upperarm." + side, "head"))
                tip = Vector(A.bone_world(arm, "hand." + side, "tail"))
                want = fist_target(arm, side, frame) - sh
                dims = UE.ARM_LEN[side]
                dd = UE.ARM_LEN[side]
                l1 = dd["upper"]
                l2 = dd["forearm"]
                hand_dir = hand_dir_of(side, frame)
                wrist = Vector(fist_target(arm, side, frame)) - hand_dir * dd["hand"]
                delta = wrist - sh
                lim = (l1 + l2) * 0.9995
                ax = (delta.normalized() if delta.length > 1e-9
                      else Vector((0.0, 0.0, -1.0)))
                ed = Vector(elbow_dir(side, frame))
                bulge_v = ed - ax * ed.dot(ax)
                row[side] = {"sh": [round(v * 1000.0, 2) for v in sh],
                             "want_dir": [round(v, 5) for v in want.normalized()],
                             "want_span_mm": round(want.length * 1000.0, 2),
                             "got_dir": [round(v, 5) for v in
                                         (tip - sh).normalized()],
                             "elbow_cmd": [round(v, 5) for v in ed],
                             "wrist_dist_mm": round(delta.length * 1000.0, 2),
                             "wrist_limit_mm": round(lim * 1000.0, 2),
                             "wrist_ratio": round(delta.length / lim, 5),
                             "clamped": bool(delta.length > lim),
                             "bulge_len_mm": round(bulge_v.length * 1000.0, 3),
                             "axis_dot_elbow": round(ax.dot(ed), 5),
                             "l1_mm": round(l1 * 1000.0, 2),
                             "l2_mm": round(l2 * 1000.0, 2),
                             "sh_dir": [round(v, 5) for v in
                                        Vector(A.bone_direction(arm, "upperarm." + side)).normalized()],
                             "fo_dir": [round(v, 5) for v in
                                        Vector(A.bone_direction(arm, "forearm." + side)).normalized()],
                             "hd_dir": [round(v, 5) for v in
                                        Vector(A.bone_direction(arm, "hand." + side)).normalized()],
                             "elbow_pos_mm": [round(v * 1000.0, 2) for v in
                                              Vector(A.bone_world(arm, "upperarm." + side, "tail"))],
                             "wrist_pos_mm": [round(v * 1000.0, 2) for v in
                                              Vector(A.bone_world(arm, "forearm." + side, "tail"))],
                             "hand_tail_mm": [round(v * 1000.0, 2) for v in tip]}
            tgt[str(frame)] = row
        steps = {}
        for side in SIDES:
            seq = []
            for frame in range(1, TOTAL + 1):
                a = Vector(tgt[str(frame - 1)][side]["want_dir"])
                b = Vector(tgt[str(frame)][side]["want_dir"])
                seq.append(round(math.degrees(math.acos(
                    max(-1.0, min(1.0, a.dot(b))))), 3))
            steps[side] = seq
        # ★ 世界旋转的真实逐帧角（物理意义上的"瞬移"）—— 与欧拉分量步长对照
        wq = {}
        WA_BONES = ("upperarm.L", "forearm.L", "hand.L",
                    "upperarm.R", "forearm.R", "hand.R")
        for frame in range(0, TOTAL + 1):
            scene.frame_set(frame)
            bpy.context.view_layer.update()
            wq[str(frame)] = {
                n: [round(v, 6) for v in
                    arm.pose.bones[n].matrix.to_3x3().to_quaternion()]
                for n in WA_BONES if n in arm.pose.bones}
        world_steps = {}
        for n in WA_BONES:
            seq = []
            for frame in range(1, TOTAL + 1):
                qa = Quaternion(wq[str(frame - 1)][n])
                qb = Quaternion(wq[str(frame)][n])
                dot = abs(max(-1.0, min(1.0, qa.dot(qb))))
                seq.append(round(math.degrees(2.0 * math.acos(dot)), 3))
            world_steps[n] = seq
        A.report("D15_TARGETTRACE", {"targets": tgt,
                                     "want_dir_steps_deg": steps,
                                     "world_rot_steps_deg": world_steps})

    # ---- ★★ (a) 接缝：首帧逐位 = `Air_Hit@18`（平移不变尺子）
    moving = _pelvis_moving(arm)
    seam_mats = CR.action_world_matrices(arm, bpy.data.actions[SEAM_ACTION],
                                         SEAM_FRAME)
    mats0 = CR.action_world_matrices(arm, action, 0)
    ori0, rel0, ori_bone0, rel_bone0 = _pose_seam_split(mats0, seam_mats, moving)
    raw0 = CR.matrix_delta(mats0, seam_mats)
    res["seam_in_orient_delta"] = float("%.3e" % ori0)
    res["seam_in_orient_bone"] = ori_bone0
    res["seam_in_relpos_delta_mm"] = round(rel0 * 1000.0, 6)
    res["seam_in_relpos_bone"] = rel_bone0
    res["seam_in_raw_delta"] = float("%.3e" % raw0)
    res["seam_in_ok"] = bool(max(ori0, rel0) <= SEAM_TOL)
    res["seam_ruler_note"] = (
        "首帧比 `%s@%d`：**平移不变**尺子（pelvis 的后代比「骨位置−骨盆位置」，"
        "非后代比世界绝对）。容差 1e-6，未放宽。" % (SEAM_ACTION, SEAM_FRAME))

    # ---- ★★ (b) 弹道：**仅前段** `f ≤ LAND` 逐帧 = 共享解析弹道 -----------
    ball_err, ball_err_at = 0.0, None
    for frame in range(0, LAND + 1):
        err = abs(zs[frame] - ball_z(frame)) * 1000.0
        if err > ball_err:
            ball_err, ball_err_at = err, frame
    res["ballistic_prefix_max_err_mm"] = round(ball_err, 4)
    res["ballistic_prefix_err_at"] = ball_err_at
    res["ballistic_tol_mm"] = BALLISTIC_TOL
    res["ballistic_until_land_ok"] = bool(ball_err <= BALLISTIC_TOL)
    res["ballistic_phase"] = {
        "T_PHASE": T_PHASE, "d13_t_phase": D13_T_PHASE,
        "z_f0_mm": round(ball_z(0) * 1000.0, 3),
        "vz_f0_mm": round(ball_vz(0) * 1000.0, 4),
        "z_land_mm": round(ball_z(LAND) * 1000.0, 3),
        "vz_land_mm": round(ball_vz(LAND) * 1000.0, 4),
        "d13_end_vz_mm": round(D13_END_VZ_MM, 4)}

    # ---- ★★ (c) 落地曲线：单调不升 + 末端固定 ---------------------------
    land_z = {f: (zs[f] - zs[LAND]) * 1000.0 for f in range(LAND, TOTAL + 1)}
    res["landing_z_rel_land_mm"] = {str(f): round(land_z[f], 3)
                                    for f in sorted(land_z)}
    rises = [(f, round(land_z[f] - land_z[f - 1], 4))
             for f in range(LAND + 1, PLATEAU + 1)
             if land_z[f] - land_z[f - 1] > 1e-9]
    res["landing_rises"] = [{"frame": f, "delta_mm": d} for f, d in rises]
    res["landing_z_fixed_ok"] = bool(not rises)
    plat = [round(zs[f] * 1000.0, 6) for f in range(PLATEAU, TOTAL + 1)]
    res["landing_plateau_z_mm"] = plat
    res["landing_plateau_tol_mm"] = LAND_PLATEAU_TOL_MM
    res["landing_plateau_ok"] = bool(max(plat) - min(plat) <= LAND_PLATEAU_TOL_MM)

    # ---- ★★ (d) 竖速：前段全负 / 落地后不许反弹 ---------------------------
    vz = {f: pelvis_vz_at(f) for f in range(1, TOTAL + 1)}
    res["pelvis_vz_mm_per_frame"] = {str(f): round(vz[f], 4) for f in sorted(vz)}
    res["vz_tail_mm"] = {str(f): round(vz[f], 4)
                         for f in sorted(vz) if f >= LAND}
    prefix_min = min(vz[f] for f in vz if f < LAND)
    res["vz_prefix_max_mm"] = round(prefix_min, 4)
    # ★ 口径收紧（不是放宽）：要求前段**逐帧都在下落**（全为负），而不是"至少一帧负"。
    #   旧写法 `prefix_min < 0` 对任何下落都成立 ⟹ 反向验证 ③ 压根撬不动它（假绿）。
    res["vz_prefix_all_negative"] = bool(all(vz[f] < 0.0 for f in vz if f < LAND))
    res["vz_fall_then_stop_ok"] = res["vz_prefix_all_negative"]
    tail_max = max(vz[f] for f in vz if f >= LAND)
    res["vz_land_max_mm"] = round(tail_max, 4)
    res["landing_no_bounce_max_mm"] = NO_BOUNCE_MAX_MM
    res["landing_no_bounce_ok"] = bool(tail_max <= NO_BOUNCE_MAX_MM)
    res["vz_note"] = (
        "★ 三段竖速各管一段：`f < LAND` 必须**全为负**（还在下落）；"
        "`f ≥ LAND` 增量 ≤ +%.1f mm/帧（落地后**不许反弹**，回弹已全部挪进姿态层）。"
        % NO_BOUNCE_MAX_MM)

    # ---- ★★ (e) 触地事件 ①：**脚先着地**（唯一）+ 落地帧贴地 -----------------
    # ★ 与 D14 的差别（§3「必须换口径」表）：D14 要求 `f ≥ LAND` **全程**鞋底贴地
    #   （钉在固定世界足迹上）；本支后倒时腿会**抬起来** ⟹ 只要求：
    #     ① `f < LAND` 鞋底离地 ≥ `AIRBORNE_MIN_MM`；② `f = LAND` 这一帧贴地。
    #   "躺平段贴地"改由 (f) 的 `hip_probe`（骨盆/后脑/双肩）守。
    #   ★ 不许把 `tail_max_sole` 再写进本判据 —— 一落地腿就抬，那必然红。
    sole = {f: min(clear[f]["L"], clear[f]["R"]) * 1000.0 for f in clear}
    res["sole_clearance_mm"] = {str(f): round(v, 2) for f, v in sorted(sole.items())}
    first = next((f for f in range(0, TOTAL + 1) if sole[f] <= LAND_EVENT_MAX_MM),
                 None)
    res["landing_first_contact_frame"] = first
    res["landing_frame"] = LAND
    prefix_min_sole = min(sole[f] for f in sole if f < LAND)
    tail_min_sole = min(sole[f] for f in sole if f >= PLATEAU)
    res["airborne_prefix_min_mm"] = round(prefix_min_sole, 3)
    res["airborne_min_threshold_mm"] = AIRBORNE_MIN_MM
    res["airborne_prefix_ok"] = bool(prefix_min_sole >= AIRBORNE_MIN_MM)
    res["landing_sole_at_land_mm"] = {
        s: (None if clear[LAND][s] is None else round(clear[LAND][s] * 1000.0, 3))
        for s in SIDES}
    res["sole_tail_min_mm"] = round(tail_min_sole, 3)
    res["legs_airborne_tail_ok"] = bool(tail_min_sole >= LEGS_LIFT_MIN_MM)
    res["landing_event_ok"] = bool(
        first == LAND
        and prefix_min_sole > AIRBORNE_MIN_MM
        and -CONTACT_LO_MM <= sole[LAND] <= LAND_EVENT_MAX_MM)
    res["landing_event_note"] = (
        "★ 触地事件 ①（**脚**）：`f < LAND` 鞋底 > %.0f mm、`f = LAND = %d` 鞋底 ∈ "
        "[−%.0f, %.0f] mm，且首次出现就在 `f = LAND`。`f ≥ LAND` 鞋底**不再受管**"
        "（腿抬起，本支与 D14 相反）—— 改由 `legs_airborne_tail_ok` 与 `hip_probe_ok` 守。"
        % (AIRBORNE_MIN_MM, LAND, CONTACT_LO_MM, LAND_EVENT_MAX_MM))

    # ---- ★★ (e2) 触地事件 ②：**臀/背区**（本支新增，D14 没有）----------------
    #   计划 §1 的"两次触地"在本支**实测成立**，但次序是 **脚(①, f=LAND) → 臀(②)**，
    #   而不是计划猜的"臀先"。判据据此写成：② 必须**晚于** ①，且 ① 时臀仍明显离地。
    res["butt_low_mm"] = {str(f): (None if butt[f] is None else round(butt[f], 2))
                          for f, v in sorted(butt.items())}
    butt_first = next((f for f in range(0, TOTAL + 1)
                       if butt[f] is not None and butt[f] <= BUTT_CONTACT_MAX_MM),
                      None)
    res["butt_first_contact_frame"] = butt_first
    res["butt_contact_max_mm"] = BUTT_CONTACT_MAX_MM
    res["butt_airborne_at_land_mm"] = (None if butt[LAND] is None
                                       else round(butt[LAND], 3))
    res["butt_airborne_min_mm"] = BUTT_AIRBORNE_MIN_MM
    res["butt_contact_ok"] = bool(
        butt_first is not None
        and butt_first > LAND
        and butt_first <= PLATEAU
        and butt[LAND] is not None
        and butt[LAND] >= BUTT_AIRBORNE_MIN_MM)
    res["butt_contact_note"] = (
        "★ 触地事件 ②（**臀/背区网格** `%s`）：必须**晚于**脚（`> f = %d`）、且在 "
        "`f ≤ PLATEAU = %d` 之前完成；`f = LAND` 时臀区仍 ≥ %.0f mm（证明两次次序）。"
        "载体是**网格级**最低点，不是 `pelvis` 骨位（髋关节永远在 ~%.0f mm）。"
        % (",".join(BUTT_OBJECTS), LAND, PLATEAU, BUTT_AIRBORNE_MIN_MM,
           Z_PELVIS_END * 1000.0))

    # ---- ★★ (f) hip_probe：躺平段**四点贴地自持**（**替换** D14 的 `foot_probe`）--
    #   ★★ 这正是计划 §1 点名的"本支最容易做废的地方"：照抄 D14 的"`f ≥ LAND`
    #      逐脚 ≤3 mm"必然红（腿抬起）。本支换成 **骨盆 + 后脑 + 双肩** 四点。
    probe_pts = {
        "pelvis_head": [Vector(per[f]["pelvis"]) for f in range(PLATEAU, TOTAL + 1)],
        "head_tail": [Vector(per[f]["head_tail"]) for f in range(PLATEAU, TOTAL + 1)],
        "shoulder.L": [Vector(per[f]["shoulder"]["L"])
                       for f in range(PLATEAU, TOTAL + 1)],
        "shoulder.R": [Vector(per[f]["shoulder"]["R"])
                       for f in range(PLATEAU, TOTAL + 1)],
    }
    hip_drift = {}
    for name, pts in probe_pts.items():
        if not pts:
            continue
        ref = pts[0]
        hip_drift[name] = round(max((p - ref).length for p in pts) * 1000.0, 4)
    res["hip_probe_drift_mm"] = hip_drift
    res["hip_probe_tol_mm"] = HIP_PROBE_TOL_MM
    res["hip_probe_ok"] = bool(
        hip_drift and max(hip_drift.values()) <= HIP_PROBE_TOL_MM)
    res["foot_slide_note"] = (
        "★ 与 D13/D14 **都不同**：本支 `f ≥ LAND` 腿**抬起** ⟹ D14 的 `foot_probe` "
        "**停用**（照抄必红）；贴地自持改由四点 `hip_probe`（骨盆 / 后脑 / 双肩）守。")

    # ---- ★★ (g) 后倒俯仰（主承载 1，**负值**）--------------------------------
    #   ★★ 与 D14 的 `prone_rotation_ok` **符号相反**（一正一负，两队互相守着）：
    #      D14 末帧 `chest` 世界俯仰 → **+88°**（前倒、脸朝下）；
    #      本支末帧 `chest` 世界俯仰 → **≤ −75°**（后倒、脸朝上）。
    pr_land = cpitch[LAND]
    pr_end = cpitch[TOTAL]
    pr_peak = min(cpitch[f] for f in cpitch)          # ★ 最负 = 仰到最狠
    pr_peak_frame = min(cpitch, key=lambda f: cpitch[f])
    res["supine_pitch_zero_deg"] = round(cpitch[0], 4)
    res["supine_pitch_land_deg"] = round(pr_land, 4)
    res["supine_pitch_end_deg"] = round(pr_end, 4)
    res["supine_pitch_peak_deg"] = round(pr_peak, 4)
    res["supine_pitch_peak_frame"] = pr_peak_frame
    res["supine_pitch_min_deg"] = SUPINE_END_MIN_DEG
    res["supine_pitch_rise_min_deg"] = SUPINE_RISE_MIN_DEG
    res["supine_pitch_head_end_deg"] = round(per[TOTAL]["head_pitch_deg"], 4)
    res["supine_pitch_pelvis_end_deg"] = round(per[TOTAL]["pelvis_pitch_deg"], 4)
    # ★ 方向守卫：本支是**俯仰**主导（不是横折）—— 末帧俯仰行程必须大于侧倾行程
    lat_span = max(abs(per[f]["chest_lat_deg"] - per[0]["chest_lat_deg"])
                   for f in per)
    res["supine_lateral_span_deg"] = round(lat_span, 4)
    res["supine_pitch_axis_ok"] = bool(pr_land - pr_end > lat_span)
    res["supine_pitch_sign_ok"] = bool(pr_end < 0.0)
    res["supine_pitch_ok"] = bool(
        pr_end <= -SUPINE_END_MIN_DEG
        and pr_land - pr_end >= SUPINE_RISE_MIN_DEG
        and pr_peak_frame >= LAND)

    # ---- ★★ (h) 压缩（主承载 2）：**膝屈速率**峰值 ∈ [LAND+1, LAND+4] ---------
    #   ★ 为什么 D15 用**速率**而不是 D14 的"数值峰值"：后倒时腿在**抬**，膝屈角与
    #     髋屈角的**数值**都是一路单调涨到 `SUPINE_PEAK`（实测膝屈 f7→f13 单调升），
    #     数值峰值根本不落在窗口里 —— 照抄 D14 的口径必红且**不可修**（除非把腿改成
    #     不抬，那就不是后倒了）。真正的"猛烈吸震"在后倒里是**速率**现象：触地后
    #     骨盆一帧掉 82.8 mm，膝必须以 **~24°/帧** 屈曲吸收，随后速率单调衰减。
    #   ★ 这一改动是**口径**适配，不是放宽容差：阈值仍从实测取，且加了"此后全局最大"
    #     的**峰位**约束（把吸震挪到窗口外照样红）。
    knee_abs = {f: max(per[f]["knee_deg"]["L"], per[f]["knee_deg"]["R"]) for f in per}
    knee_rate = {f: knee_abs[f] - knee_abs[f - 1] for f in range(1, TOTAL + 1)}
    hipf = {f: max(per[f]["hip_flex_deg"]["L"], per[f]["hip_flex_deg"]["R"])
            for f in per}
    hip_rel = {f: hipf[f] - hipf[LAND] for f in hipf}
    hip_rate = {f: hipf[f] - hipf[f - 1] for f in range(1, TOTAL + 1)}
    res["hip_flex_abs_deg"] = {str(f): round(hipf[f], 3) for f in sorted(hipf)}
    res["hip_flex_rel_land_deg"] = {str(f): round(hip_rel[f], 3)
                                    for f in sorted(hip_rel)}
    res["knee_deg_abs"] = {str(f): round(knee_abs[f], 3) for f in sorted(knee_abs)}
    res["knee_rate_deg_per_frame"] = {str(f): round(knee_rate[f], 3)
                                      for f in sorted(knee_rate)}
    res["hip_flex_rate_deg_per_frame"] = {str(f): round(hip_rate[f], 3)
                                          for f in sorted(hip_rate)}
    seg = [f for f in range(COMPRESS_WINDOW[0], COMPRESS_WINDOW[1] + 1)]
    peak_f = max(seg, key=lambda f: knee_rate[f])
    rate_peak_f = max(knee_rate, key=lambda f: knee_rate[f])
    res["compress_peak_frame"] = peak_f
    res["compress_peak_deg"] = round(knee_rate[peak_f], 3)
    res["compress_rate_global_peak_frame"] = rate_peak_f
    res["compress_rate_global_peak_deg"] = round(knee_rate[rate_peak_f], 3)
    res["compress_window"] = list(COMPRESS_WINDOW)
    res["compress_min_deg"] = COMPRESS_MIN_DEG
    res["compress_hip_sit_frame"] = 10
    res["compress_hip_sit_deg"] = round(hip_rel[10], 3)
    res["hip_sit_min_deg"] = HIP_FLEX_SIT_MIN_DEG
    res["compress_present_ok"] = bool(
        knee_rate[peak_f] >= COMPRESS_MIN_DEG
        and knee_rate[peak_f] >= max(knee_rate[f] for f in knee_rate if f > peak_f)
        and hip_rel[10] >= HIP_FLEX_SIT_MIN_DEG)
    res["compress_note"] = (
        "★ 触地后**吸震速率**：膝屈速率（相对上一帧）峰值必须落在 `LAND+1 ~ LAND+4` "
        "**且**是此后全局最大；另要求 `SIT_PEAK`(f10) 的髋屈角已抬到 ≥ %.0f°"
        "（= 臀坐实、膝被动抬起）。" % HIP_FLEX_SIT_MIN_DEG)

    # ---- ★★ (h2) 腿抬起（躺平段：膝不许伸直 + 鞋底离地）---------------------
    knee_plateau = min(min(per[f]["knee_deg"].values())
                       for f in per if f >= PLATEAU)
    res["knee_plateau_min_deg"] = round(knee_plateau, 3)
    res["knee_sustain_min_deg"] = KNEE_SUSTAIN_MIN_DEG
    res["legs_lift_min_mm"] = LEGS_LIFT_MIN_MM
    res["legs_lift_sole_min_mm"] = round(tail_min_sole, 3)
    res["legs_lift_ok"] = bool(
        tail_min_sole >= LEGS_LIFT_MIN_MM
        and knee_plateau >= KNEE_SUSTAIN_MIN_DEG)
    res["legs_lift_note"] = (
        "★ 躺平段（`f ≥ PLATEAU`）**双膝不许伸直**（膝屈角 ≥ %.0f°）**且鞋底离地** "
        "（≥ %.0f mm）—— 后倒时腿因惯性抬起，这是与 D14（脚钉地）最直观的画面差别。"
        % (KNEE_SUSTAIN_MIN_DEG, LEGS_LIFT_MIN_MM))

    # ---- ★★ (h3) 后脑贴地（真的躺下，不是坐着）-----------------------------
    ht = {f: per[f]["head_tail"].z * 1000.0 for f in per}
    res["head_tail_z_mm"] = {str(f): round(v, 2) for f, v in sorted(ht.items())}
    hmesh = {f: (None if headm[f] is None else round(headm[f], 2)) for f in headm}
    res["head_mesh_low_mm"] = {str(f): v for f, v in sorted(hmesh.items())}
    res["head_tail_max_mm"] = HEAD_TAIL_MAX_MM
    res["head_tail_plateau_max_mm"] = round(
        max(ht[f] for f in ht if f >= SUPINE_PEAK), 3)
    res["back_land_ok"] = bool(
        max(ht[f] for f in ht if f >= SUPINE_PEAK) <= HEAD_TAIL_MAX_MM)
    res["back_land_note"] = (
        "★ `f ≥ SUPINE_PEAK` 后，后脑（`head` 尾端）高度必须 ≤ %.0f mm "
        "（真的仰面躺平；坐着够不到这个高度）。同时报出 `Head`/`Hair_Mass` 网格最低点。"
        % HEAD_TAIL_MAX_MM)

    # ---- ★ (i) 打击停顿（触地 2 帧，**只看上身**）------------------------
    platform = HOLD_END - LAND + 1
    pose_step, pose_step_at = 0.0, None
    # ★ 只扫**停顿窗口内部**的相邻帧（f7→f8）；`range(LAND, HOLD_END + 1)` 会把
    #   窗口外的 f8→f9 也算进来 ⟹ 把"恢复运动"误判成"停顿没冻住"。
    for index in range(LAND, HOLD_END):
        step, at = _worst_step_bones(samples, index, index + 1, UPPER_BONES)
        if step > pose_step:
            pose_step, pose_step_at = step, at
    res["hitstop_frames"] = platform
    res["hitstop_upper_drift_deg"] = round(pose_step, 6)
    res["hitstop_upper_drift_at"] = pose_step_at
    res["hitstop_leg_exempt"] = True
    res["hitstop_present"] = bool(
        platform >= HITSTOP_MIN_FRAMES and pose_step <= HITSTOP_POSE_TOL_DEG)
    res["hitstop_note"] = (
        "★ 口径（与 D13 的差别）：D13 是**整身**逐位冻结（全段离地，脚不管）；"
        "本支 `f ≥ LAND` 腿在**抬起** ⟹ 停顿只锁**上身**（躯干+肩+臂），"
        "**双腿豁免**（继续解算以抬腿）；骨盆 `@loc` 继续走落地曲线。")

    # ---- ★ 收招不许瞬停（末 6 帧增量**单调收敛** —— 清单 §0.6 口径）-----
    tail_start = int(TOTAL - NO_SNAP_TAIL_FRAMES)
    steps = []
    for index in range(tail_start + 1, TOTAL + 1):
        steps.append(round(_worst_step(samples, index - 1, index)[0], 6))
    res["no_snap_tail_steps_deg"] = steps
    res["no_snap_stop_ok"] = bool(
        len(steps) >= 2
        and all(steps[i] >= steps[i + 1] - 1e-6 for i in range(len(steps) - 1))
        and steps[-1] <= 1e-6)
    res["no_snap_tail_window"] = [tail_start, TOTAL]
    res["no_snap_ruler_note"] = (
        "★ 口径按**清单 §0.6 原文**：「末 6 帧角度增量的绝对值**单调收敛**」。"
        "D13 用的是更严的代理（窗口内单帧步长 ≤5°），本支的'坐倒/躺平'段正好落在该"
        "窗口里（后倒在地面段本来就是大角度行程），代理口径必然红 ⟹ 按清单原文实现，"
        "并**并列报出**窗口内单帧步长峰值 `no_snap_tail_max_deg` 供人判读。")

    # ---- ★ 定格自持（末 N 帧姿态逐位冻结）-------------------------------
    last = []
    for index in range(PLATEAU + 1, TOTAL + 1):
        last.append(round(_worst_step(samples, index - 1, index)[0], 6))
    res["end_hold_steps_deg"] = last
    res["end_ground_hold_ok"] = bool(last and max(last) <= END_HOLD_MAX_DEG)
    res["end_identical_skipped"] = True
    res["end_identical_note"] = (
        "★ 末帧**不回原位**（首帧在空中、末帧仰面躺地）⟹ 只报：末帧与 f0 的世界位置差"
        "就是「这一摔向后躺出去多远」。")

    # ---- ★ 末帧登记（给 D15/D16/D17 的起点）-----------------------------
    end_vz = (zs[TOTAL] - zs[TOTAL - 1]) * 1000.0
    res["end_vz_mm_per_frame"] = round(end_vz, 4)
    res["end_pelvis_z_mm"] = round(zs[TOTAL] * 1000.0, 3)
    res["end_vz_zero_ok"] = bool(abs(end_vz) <= 1e-6)

    # ---- ★ handoff（**只报**）：末帧 vs 上游 / vs `Crouch@` -------------
    res["handoff"] = _handoff_report(arm, action, seam_mats)

    # ---- ★ 力量传导链（脚→腿→髋→腰→肩→手）-------------------------------
    knee_flex = {s: round(max(abs(per[f]["knee_deg"][s] - zero["knee_deg"][s])
                              for f in per), 3) for s in SIDES}
    shoulder_move, shoulder_at = 0.0, None
    for frame in per:
        for s in SIDES:
            gap = (per[frame]["shoulder"][s] - zero["shoulder"][s]).length * 1000.0
            if gap > shoulder_move:
                shoulder_move, shoulder_at = gap, (s, frame)
    fist_dev, fist_dev_at = 0.0, None
    for frame in per:
        for s in SIDES:
            gap = (per[frame]["fist"][s] - ZERO_FIST[s]).length * 1000.0
            if gap > fist_dev:
                fist_dev, fist_dev_at = gap, (s, frame)
    ankle_dev = max((per[f]["ankle"][s] - zero["ankle"][s]).length
                    for f in per for s in SIDES) * 1000.0
    pelvis_span = max((per[f]["pelvis"] - per[0]["pelvis"]).length
                      for f in per) * 1000.0
    res["fist_travel_mm"] = round(fist_dev, 3)
    res["fist_travel_at"] = fist_dev_at
    res["ankle_travel_mm"] = round(ankle_dev, 3)
    res["shoulder_move_mm"] = round(shoulder_move, 3)
    res["pelvis_span_mm"] = round(pelvis_span, 3)
    res["chain_travel"] = {
        "foot_mm": round(ankle_dev, 2),
        "knee_deg": round(max(knee_flex.values()), 3),
        "hip_mm": round(pelvis_span, 2),
        "waist_deg": round(abs(pr_end - pr_land), 3),
        "shoulder_mm": round(shoulder_move, 2),
        "hand_mm": round(fist_dev, 2),
    }
    res["chain_present_ok"] = bool(
        res["chain_travel"]["foot_mm"] > 50.0
        and res["chain_travel"]["knee_deg"] > 20.0
        and res["chain_travel"]["hip_mm"] > 20.0
        and res["chain_travel"]["waist_deg"] > 2.0
        and res["chain_travel"]["shoulder_mm"] > 5.0
        and res["chain_travel"]["hand_mm"] > 30.0)

    # ---- 水平位移（本支**登记式**，不是"零位移"）------------------------
    dx = {f: (xs[f] - xs[0]) * 1000.0 for f in per}
    dy = {f: (ys[f] - ys[0]) * 1000.0 for f in per}
    res["root_motion_net_mm"] = round(math.hypot(dx[TOTAL], dy[TOTAL]), 3)
    res["root_motion_m"] = [round(dx[TOTAL] / 1000.0, 6),
                            round(dy[TOTAL] / 1000.0, 6)]
    res["root_motion_registered_m"] = [
        round((PELVIS_Y_END - PELVIS_Y_START) * 0.0, 6),
        round(PELVIS_Y_END - PELVIS_Y_START, 6)]
    res["root_motion_ok"] = bool(
        abs(dx[TOTAL]) <= 0.5 and abs(dy[TOTAL] / 1000.0
                                      - (PELVIS_Y_END - PELVIS_Y_START)) <= 0.002)
    res["root_motion_note"] = (
        "★ 与 D12/D13 **不同**（那两支登记 0），也与 D14 **符号相反**：后倒天然带水平"
        "位移 —— 骨盆绕双脚向 **+Y** 退出 %.3f m，本支**如实登记** `root_motion_m`。"
        % (PELVIS_Y_END - PELVIS_Y_START))

    # ---- 冻结段 / 锁存计数 ----------------------------------------------
    res["lock_frames"] = _LOCK_REUSED[0]
    res["lock_expect"] = TOTAL - PLATEAU
    res["lock_ok"] = bool(res["lock_frames"] == TOTAL - PLATEAU)
    res["hitstop_frames_reused"] = _HITSTOP_REUSED[0]
    res["hitstop_expect"] = HOLD_END - LAND
    res["hitstop_reuse_ok"] = bool(res["hitstop_frames_reused"]
                                   == HOLD_END - LAND)

    # ---- 穿模 -----------------------------------------------------------
    frames = sorted(set(list(range(0, TOTAL + 1, CLIP_EVERY))
                        + [LAND, HOLD_END, COMPRESS_PEAK, SUPINE_PEAK, PLATEAU,
                           TOTAL]))
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
            limit = ARM_MAX[side] * 0.9995
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

    # ---- 剪影 / aspect：只报不判 ----------------------------------------
    sil = P.silhouette(arm, "d15")
    res["aspect"] = sil["aspect"]
    res["fill_grid"] = sil["fill_grid"]
    res["width_m"] = sil["width_m"]
    res["height_m"] = sil["height_m"]

    if os.environ.get("D15_TRACE"):
        # ★ 逐帧单帧步长（定位 `no_teleport` 红在哪一帧 / 哪根骨）
        steps = []
        for index in range(1, TOTAL + 1):
            w, at = _worst_step(samples, index - 1, index)
            steps.append({"f": index, "deg": round(w, 3),
                          "bone": (at[1] if at else None)})
        res["frame_steps_deg"] = steps
        res["trace"] = {str(f): {
            "supine": round(supine(f), 4),
            "brace": round(brace(f), 4),
            "decay": round(decay(f), 4),
            "ball_z": round(ball_z(f) * 1000.0, 2),
            "has_z": round(zs[f] * 1000.0, 2),
            "has_y": round(ys[f] * 1000.0, 2),
            "vz": round(vz[f], 2) if f in vz else None,
            "lowL": None if clear[f]["L"] is None else round(clear[f]["L"] * 1000.0, 2),
            "lowR": None if clear[f]["R"] is None else round(clear[f]["R"] * 1000.0, 2),
            "kneeL": round(per[f]["knee_deg"]["L"] - zero["knee_deg"]["L"], 3),
            "kneeR": round(per[f]["knee_deg"]["R"] - zero["knee_deg"]["R"], 3),
            "chest_pitch": round(cpitch[f], 3),
            "foot": {s: None if feet[f][s] is None
                     else round(feet[f][s][2] * 1000.0, 2) for s in SIDES},
            "leg_axis": {s: [round(v, 5) for v in _LEG_AXIS[f][s]]
                         for s in SIDES},
            "hand": {s: [round(v * 1000.0, 1) for v in per[f]["fist"][s]]
                     for s in SIDES},
            "euler": {n: [round(v, 2) for v in samples[f]["euler"].get(
                n, (0.0, 0.0, 0.0))]
                for n in ("hand.R", "hand.L", "forearm.R", "forearm.L",
                          "upperarm.R", "upperarm.L",
                          "shoulder.R", "shoulder.L",
                          "shin.L", "thigh.L", "shin.R", "thigh.R",
                          "foot.L", "foot.R", "pelvis", "chest")},
        } for f in range(0, TOTAL + 1)}
    return res


def _handoff_report(arm, action, seam_mats):
    """末帧 vs 上游末帧 —— **只报**，不判。"""
    out = {}
    mats_end = CR.action_world_matrices(arm, action, TOTAL)
    moving = _pelvis_moving(arm)
    ori, rel, ob, rb = _pose_seam_split(mats_end, seam_mats, moving)
    out["vs_air_hit18_orient"] = float("%.3e" % ori)
    out["vs_air_hit18_relpos_mm"] = round(rel * 1000.0, 3)
    out["vs_air_hit18_bone"] = rb or ob
    crouch = bpy.data.actions.get("Crouch")
    if crouch is not None:
        cm = CR.action_world_matrices(arm, crouch, 0)
        ori2, rel2, ob2, rb2 = _pose_seam_split(mats_end, cm, moving)
        out["vs_crouch0_orient"] = float("%.3e" % ori2)
        out["vs_crouch0_relpos_mm"] = round(rel2 * 1000.0, 3)
        out["vs_crouch0_bone"] = rb2 or ob2
    return out


def _pelvis_moving(arm):
    """pelvis 的**后代**骨集合（接缝尺子用）。"""
    moving = set()
    for bone in arm.pose.bones:
        node = bone
        while node is not None:
            if node.name == "pelvis":
                moving.add(bone.name)
                break
            node = node.parent
    return moving


def _bone_point(mat):
    return mat[3], mat[7], mat[11]


def _pose_seam_split(mats_a, mats_b, moving):
    """两套世界矩阵的「平移不变」逐位差（B08 第 2 件那把尺子，原样照抄）。"""
    ori, rel = 0.0, 0.0
    ori_bone, rel_bone = None, None
    pa, pb = _bone_point(mats_a["pelvis"]), _bone_point(mats_b["pelvis"])
    for name in mats_a:
        ma, mb = mats_a[name], mats_b[name]
        for index in (0, 1, 2, 4, 5, 6, 8, 9, 10):
            if abs(ma[index] - mb[index]) > ori:
                ori, ori_bone = abs(ma[index] - mb[index]), name
        xa, ya, za = _bone_point(ma)
        xb, yb, zb = _bone_point(mb)
        if name in moving:
            da = (xa - pa[0], ya - pa[1], za - pa[2])
            db = (xb - pb[0], yb - pb[1], zb - pb[2])
        else:
            da, db = (xa, ya, za), (xb, yb, zb)
        worst = max(abs(u - v) for u, v in zip(da, db))
        if worst > rel:
            rel, rel_bone = worst, name
    return ori, rel, ori_bone, rel_bone


# =============================================================== 引导
def _load_seam_zero(arm):
    """★ 零位真源：**上游 `Air_Hit@18` 的落盘行动作**（不是零位姿态！）。

    ★ 反向验证 ① 打开时改读 `Idle_01@0`（零位姿态）—— 证明 `seam_in_ok` 抓得住接缝断裂。
    """
    global VZ_LAND
    action = bpy.data.actions.get(ZERO_ACTION)
    if action is None:
        return {}, {"action": ZERO_ACTION, "found": False}
    rot_keyed, loc_keyed = _keyed_bones(action)
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    A.reset_pose(arm)
    bpy.context.scene.frame_set(int(ZERO_FRAME))
    bpy.context.view_layer.update()
    pose = {name: tuple(math.degrees(v)
                        for v in arm.pose.bones[name].rotation_euler)
            for name in rot_keyed if name in arm.pose.bones}
    loc = {name: tuple(arm.pose.bones[name].location)
           for name in loc_keyed if name in arm.pose.bones}
    if loc:
        pose["@loc"] = loc
    info = {"action": ZERO_ACTION, "found": True, "frame": int(ZERO_FRAME),
            "rot_bones": len(rot_keyed), "loc_bones": sorted(loc_keyed),
            "frame_range": [int(v) for v in action.frame_range]}
    return pose, info


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
    global ZERO, ZERO_WORLD, Z_SEAM, KNEE_DIR, ANKLE_0, ZERO_FIST, VZ_LAND
    ZERO, ZERO_WORLD = {}, {}
    for table in (ZERO_BASIS, ZERO_DIR, SEAM_FIST, SEAM_FIST_DIR, SEAM_SHOULDER,
                  SEAM_SPAN, SEAM_ELBOW_DIR, SEAM_HAND_DIR, SEAM_ANKLE,
                  SEAM_HIP, SEAM_HIP_OFF, ANKLE_0, KNEE_DIR, ARM_MAX,
                  LAND_ANKLE, LAND_SOLE_MM, SEAM_SOLE_MM, SEAM_PITCH,
                  SUPINE_EXTRA, LOCK_POSE, HITSTOP_POSE, LIFT_Z_KEYS,
                  FOOT_LAND_EULER):
        table.clear()
    _HITSTOP_REUSED[0] = 0
    _LOCK_REUSED[0] = 0
    FOOT_LOCKED[0] = False

    arm, meshes = A.open_animation_project()
    A.setup_scene()
    if SEAM_ACTION not in bpy.data.actions:
        raise RuntimeError("接缝动作 %s 不在落盘文件里" % SEAM_ACTION)
    if ZERO_ACTION not in bpy.data.actions:
        raise RuntimeError("零位真源 %s 不在落盘文件里" % ZERO_ACTION)

    for side in SIDES:
        UE.ARM_LEN[side] = {
            "upper": arm.pose.bones["upperarm." + side].length,
            "forearm": arm.pose.bones["forearm." + side].length,
            "hand": arm.pose.bones["hand." + side].length}
        ARM_MAX[side] = (UE.ARM_LEN[side]["upper"]
                         + UE.ARM_LEN[side]["forearm"]
                         + UE.ARM_LEN[side]["hand"])

    UE.ROLL_STEP_DEG = _env_f("D15_ROLLSTEP", 2.0)
    UE.ROLL_GRID = UE._roll_grid()
    UE.EULER_Y_SAFE = _env_f("D15_YSAFE", 88.0)
    UE.EULER_Y_WEIGHT = _env_f("D15_YWEIGHT", 0.0)

    for extra in LEG_BONES + ("foot.L", "foot.R"):
        if extra not in A.PROBE_BONES:
            A.PROBE_BONES = tuple(A.PROBE_BONES) + (extra,)
        if extra not in A.PROBE_TAILS:
            A.PROBE_TAILS = tuple(A.PROBE_TAILS) + (extra,)
    A.PROBE_KEYS = A.PROBE_BONES + tuple(n + ".tail" for n in A.PROBE_TAILS)

    ZERO, saved_info = _load_seam_zero(arm)
    if not ZERO:
        raise RuntimeError("读不到接缝零位")

    # ★ "落盘真值 vs 手写重演"（同 D12/D13 的检查口径）
    arm.animation_data.action = bpy.data.actions[ZERO_ACTION]
    A._bind_slot(arm, bpy.data.actions[ZERO_ACTION])
    bpy.context.scene.frame_set(int(ZERO_FRAME))
    bpy.context.view_layer.update()
    action_heads, action_dirs = {}, {}
    for name in A.PROBE_BONES:
        if name in arm.pose.bones:
            action_heads[name] = Vector(A.bone_world(arm, name, "head"))
            action_dirs[name] = Vector(A.bone_direction(arm, name)).normalized()
    arm.animation_data.action = None
    replay_heads, replay_dirs = _world_snapshot(arm, ZERO)
    geom_pos, geom_pos_bone = 0.0, None
    for name, point in action_heads.items():
        other = replay_heads.get(name)
        if other is None:
            continue
        gap = (point - other).length * 1000.0
        if gap > geom_pos:
            geom_pos, geom_pos_bone = gap, name
    geom_dir, geom_dir_bone = 0.0, None
    for name, direction in action_dirs.items():
        other = replay_dirs.get(name)
        if other is None:
            continue
        dot = max(-1.0, min(1.0, direction.dot(other)))
        gap = math.degrees(math.acos(dot))
        if gap > geom_dir:
            geom_dir, geom_dir_bone = gap, name
    SEAM_MATCH.update({
        "src": "%s@%d" % (ZERO_ACTION, ZERO_FRAME),
        "saved": saved_info,
        "geom_pos": round(geom_pos, 6), "pos_bone": geom_pos_bone,
        "geom_dir": round(geom_dir, 6), "dir_bone": geom_dir_bone,
        "matched": bool(geom_pos <= SEAM_REPLAY_POS_MAX_MM
                        and geom_dir <= SEAM_REPLAY_DIR_MAX_DEG),
    })

    A.apply_pose(arm, ZERO)
    bpy.context.view_layer.update()
    Z_SEAM = A.bone_world(arm, "pelvis", "head").z
    ANKLE_0 = {s: Vector(A.bone_world(arm, "foot." + s, "head")) for s in SIDES}
    for side in SIDES:
        SEAM_FIST[side] = Vector(A.bone_world(arm, "hand." + side, "tail"))
        SEAM_ANKLE[side] = Vector(A.bone_world(arm, "foot." + side, "head"))
        SEAM_HIP[side] = Vector(A.bone_world(arm, "thigh." + side, "head"))
        SEAM_HIP_OFF[side] = (SEAM_ANKLE[side].x - SEAM_HIP[side].x,
                              SEAM_ANKLE[side].y - SEAM_HIP[side].y)
        SEAM_HAND_DIR[side] = Vector(
            A.bone_direction(arm, "hand." + side)).normalized()
        shoulder = Vector(A.bone_world(arm, "upperarm." + side, "head"))
        SEAM_SHOULDER[side] = shoulder
        SEAM_SPAN[side] = (SEAM_FIST[side] - shoulder).length
        elbow = Vector(A.bone_world(arm, "upperarm." + side, "tail"))
        SEAM_ELBOW_DIR[side] = tuple((elbow - shoulder).normalized())
        d = SEAM_FIST[side] - shoulder
        SEAM_FIST_DIR[side] = d.normalized() if d.length > 1e-9 \
            else Vector((0.0, -1.0, 0.0))
    for side in SIDES:
        hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
        knee = Vector(A.bone_world(arm, "shin." + side, "head"))
        ankle = Vector(A.bone_world(arm, "foot." + side, "head"))
        axis = (ankle - hip).normalized()
        bulge = (knee - hip) - axis * (knee - hip).dot(axis)
        KNEE_DIR[side] = (bulge.normalized() if bulge.length > 1e-9
                          else Vector((0.0, -0.94, -0.34)))
    # ★★ 膝朝向 **可覆盖**（`D15_KNEE_DIR`，默认空 = 用接缝实测）：
    #   接缝姿态是**被击中的张开姿**（两腿不对称 ⟹ 两腿的膝朝向不是镜像），
    #   深屈膝时两腿落在**不同的欧拉分支**上。扫参用。
    _kd_env = os.environ.get("D15_KNEE_DIR", "").strip()
    if _kd_env:
        kd = [float(x) for x in _kd_env.split(",")]
        KNEE_DIR["L"] = Vector((kd[0], kd[1], kd[2])).normalized()
        KNEE_DIR["R"] = Vector((-kd[0], kd[1], kd[2])).normalized()
    for bone in ARM_BONES + LEG_BONES:
        UE.IDLE_BASIS[bone] = arm.pose.bones[bone].matrix.to_3x3().copy()
        UE.IDLE_DIR[bone] = A.bone_direction(arm, bone)

    ZERO_WORLD = {n: tuple(v) for n, v in replay_heads.items()}
    for name in A.PROBE_TAILS:
        if name in arm.pose.bones:
            ZERO_WORLD[name + ".tail"] = tuple(A.bone_world(arm, name, "tail"))
    for name in A.PROBE_BONES:
        if name in arm.pose.bones:
            ZERO_BASIS[name] = tuple(
                arm.pose.bones[name].matrix.to_3x3().to_quaternion())
    for name in ARM_BONES:
        ZERO_DIR[name] = Vector(A.bone_direction(arm, name)).normalized()

    ZERO_FIST = {s: Vector(A.bone_world(arm, "hand." + s, "tail")) for s in SIDES}

    # ---- 接缝姿态的**世界俯仰**（本支俯仰通道的基线）-------------------
    for name in TORSO_BONES:
        SEAM_PITCH[name] = _pitch(Vector(A.bone_direction(arm, name)))
    SUPINE_EXTRA["pelvis"] = PITCH_TARGET_PELVIS - SEAM_PITCH["pelvis"]
    SUPINE_EXTRA["chest"] = PITCH_TARGET_CHEST - SEAM_PITCH["chest"]
    SUPINE_EXTRA["head"] = PITCH_TARGET_HEAD - SEAM_PITCH["head"]

    # ---- ★ 落地曲线的进入竖速 = 弹道在触地帧的瞬时竖速 -------------------
    VZ_LAND = ball_vz(LAND)

    # ---- ★★ 落地足迹：先用"空中目标"解一次 `f = LAND`，把它读出来后钉死 ----
    #   ★ 前置两件**实测标定**（都必须在"接缝零位"上量）：
    #     ① f0 的鞋底目标 ← 实测接缝鞋底；② "鞋底 − 踝"落差表 ← 扫 `foot.rx`。
    A.apply_pose(arm, ZERO)
    bpy.context.view_layer.update()
    low_seam = A.foot_lowest_by_side()
    for side in SIDES:
        SEAM_SOLE_MM[side] = round(low_seam[side][2] * 1000.0, 3)
        SOLE_KEYS_FOR[side] = ((0, SEAM_SOLE_MM[side] / 1000.0),) + SOLE_DROP
    _measure_foot_gap(arm)
    A.apply_pose(arm, ZERO)
    bpy.context.view_layer.update()

    FOOT_LOCKED[0] = False
    JS._PREV_EULER.clear()
    A.apply_pose(arm, ZERO)
    bpy.context.view_layer.update()
    for name in ARM_BONES + LEG_BONES:
        UE.CARRY_Q[name] = arm.pose.bones[name].matrix.to_3x3().to_quaternion()
    for name, value in ZERO.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)
    for frame in range(1, LAND + 1):
        solve_pose(arm, frame, meshes)
    # ★ 足迹高度**实测校准**：先用 rest 踝高解一遍，量出鞋底，再按差值把足迹抬到
    #   "鞋底 = TARGET_LAND_SOLE_MM"。否则鞋底会停在 −2.6 ~ −3.3 mm
    #   （`ground_contact_ok` 下界 = −2）—— 解析值（踝高 = rest ⟹ 鞋底 = 0）
    #   与鞋网格实测差约 3 mm，是**姿态相关量**，不许用公式代替实测。
    low_land = A.foot_lowest_by_side()
    LAND_SOLE_MM.clear()
    for side in SIDES:
        ank = Vector(A.bone_world(arm, "foot." + side, "head"))
        sole_mm = low_land[side][2] * 1000.0
        LAND_SOLE_MM[side] = round(sole_mm, 3)
        dz = (TARGET_LAND_SOLE_MM - sole_mm) / 1000.0
        LAND_ANKLE[side] = Vector((ank.x, ank.y, Z_ANKLE_REST + dz))
    FOOT_LOCKED[0] = True
    # ★★ 落地后的**抬腿曲线**（本支与 D14 相反）：`f = LAND` 从**实测落地踝高**起步
    #   （一阶连续，不许跳），到 `SUPINE_PEAK` 抬到 `LIFT_Z_END`，其后逐位固定。
    #   Z 是**绝对**高度 ⟹ "躺平段鞋底 ≥ 50 mm" 由 `LIFT_Z_END` 直接构造。
    LIFT_Z_KEYS.clear()
    for side in SIDES:
        z0 = LAND_ANKLE[side].z
        if NO_LEGS:
            # ★★ ⑥ 抽掉抬腿驱动：踝**恒停在落地高度**。
            #    旧实现只把水平分量 `g` 归零（`legs()` 返回 0），Z 仍走
            #    `LIFT_Z_KEYS` 抬到 300 mm ⟹ 鞋底照样 ≥ 50 mm、膝照样屈 ⟹
            #    `legs_lift_ok` **压根不红**（实测：`failed=[]`）—— 这是**空接线**。
            #    清单 §4 第 7 步明令"旋钮必须真的接进代码"⟹ 这里把竖直分量一起抽掉。
            LIFT_Z_KEYS[side] = ((LAND, z0), (TOTAL, z0))
        elif LIFT_BUMP:
            LIFT_Z_KEYS[side] = ((LAND, z0), (LAND + 1, z0 + LIFT_BUMP),
                                 (SUPINE_PEAK, LIFT_Z_END),
                                 (TOTAL, LIFT_Z_END))
        else:
            LIFT_Z_KEYS[side] = ((LAND, z0), (HOLD_END, z0),
                                 (SUPINE_PEAK, LIFT_Z_END),
                                 (TOTAL, LIFT_Z_END))
    # ★ `local` 钉法的起点：`f = LAND` 时脚的**局部**欧拉（此刻世界钉刚解完）。
    FOOT_LAND_EULER.clear()
    for side in SIDES:
        FOOT_LAND_EULER[side] = tuple(
            JS._PREV_EULER.get("foot." + side, (0.0, 0.0, 0.0)))

    # ★ 复位逐帧解缠状态，正式重解
    JS._PREV_EULER.clear()
    UE.CARRY_Q.clear()
    LOCK_POSE.clear()
    HITSTOP_POSE.clear()
    _HITSTOP_REUSED[0] = 0
    _LOCK_REUSED[0] = 0
    Arm0 = (arm, meshes)
    _ = Arm0

    zrow = _body_metrics(arm)
    A.report("D15_LAYOUT", {
        "total_frames": TOTAL, "seconds": round(TOTAL / float(A.FPS), 3),
        "land": LAND, "hold_end": HOLD_END, "hit_hold": HIT_HOLD,
        "compress_peak": COMPRESS_PEAK, "supine_peak": SUPINE_PEAK,
        "plateau": PLATEAU, "cancel": CANCEL,
        "seam": {"action": SEAM_ACTION, "frame": SEAM_FRAME,
                 "src": saved_info,
                 "d13_end_vz_mm": round(D13_END_VZ_MM, 4),
                 "z_f0_mm": round(ball_z(0) * 1000.0, 3),
                 "z_land_mm": round(ball_z(LAND) * 1000.0, 3),
                 "vz_land_mm": round(ball_vz(LAND) * 1000.0, 4),
                 "Z_SEAM_mm": round(Z_SEAM * 1000.0, 3)},
        "seam_pitch_deg": {k: round(v, 4) for k, v in SEAM_PITCH.items()},
        "supine_extra_deg": {k: round(v, 4) for k, v in SUPINE_EXTRA.items()},
        "target_pitch_deg": {"pelvis": PITCH_TARGET_PELVIS,
                             "chest": PITCH_TARGET_CHEST,
                             "head": PITCH_TARGET_HEAD},
        "landing_curve": {
            "z_start_m": round(ball_z(LAND), 6), "z_end_m": Z_PELVIS_END,
            "y_start_m": PELVIS_Y_START, "y_end_m": PELVIS_Y_END,
            "v0_m_per_frame": round(ball_vz(LAND), 6),
            "span_frames": PLATEAU - LAND,
            "shape": "三次 Hermite（起点竖速 = 弹道末竖速，终点竖速 = 0）"},
        "land_ankle_mm": {s: [round(v * 1000.0, 2) for v in LAND_ANKLE[s]]
                          for s in SIDES},
        "land_sole_measured_mm": dict(LAND_SOLE_MM),
        "land_sole_target_mm": TARGET_LAND_SOLE_MM,
        "land_stance_mm": {"x": LAND_STANCE_X * 1000.0,
                           "y": LAND_STANCE_Y * 1000.0},
        "seam_ankle_mm": {s: [round(v * 1000.0, 2) for v in SEAM_ANKLE[s]]
                          for s in SIDES},
        "seam_hip_mm": {s: [round(v * 1000.0, 2) for v in SEAM_HIP[s]]
                        for s in SIDES},
        "seam_hip_off_mm": {s: [round(v * 1000.0, 2) for v in SEAM_HIP_OFF[s]]
                            for s in SIDES},
        "arm_max_mm": {s: round(ARM_MAX[s] * 1000.0, 2) for s in SIDES},
        "seam_span_mm": {s: round(SEAM_SPAN[s] * 1000.0, 2) for s in SIDES},
        "zero_pelvis_loc_expected": list(
            A.wloc(0.0, PELVIS_Y_START, ball_z(0) - Z_PELVIS_REST)),
        "force_direction": "后倒：受力分两条**独立**通道 —— ① 躯干后倒俯仰（姿态层，"
                           "rx_self = W_self − W_parent，**负值**）；② 骨盆 z 落地曲线 + "
                           "双腿抬起（位移层）。回弹全部挪进姿态层，位移层单调不升。",
        "lift_keys_m": {s: [[k, round(v, 6)] for k, v in LIFT_Z_KEYS[s]]
                        for s in SIDES},
        "lift_target_m": {"dx": LIFT_DX, "dy": LIFT_DY, "z_end": LIFT_Z_END},
        "knee_dir": {s: [round(v, 5) for v in KNEE_DIR[s]] for s in SIDES},
        "supine_keys": [list(k) for k in SUPINE_KEYS],
        "brace_keys": [list(k) for k in BRACE_KEYS],
        "legs_keys": [list(k) for k in LEGS_KEYS],
        "decay_keys": [list(k) for k in DECAY_KEYS],
        "sole_drop": [list(k) for k in SOLE_DROP],
        "sole_keys_for_m": {s: [list(k) for k in SOLE_KEYS_FOR[s]] for s in SIDES},
        "seam_sole_mm": dict(SEAM_SOLE_MM),
        "foot_gap_mm": {str(k): dict(v) for k, v in sorted(FOOT_GAP_MM.items())},
        "foot_gap_symmetry_mm": dict(FOOT_GAP_SYMMETRY_MM),
        "tip_keys": [list(k) for k in TIP_KEYS],
        "roll_weight_mode": ROLL_WEIGHT_MODE,
        "zero_chest_pitch_deg": round(zrow["chest_pitch_deg"], 4),
        "note": ("D15 后倒：零位 = **`Air_Hit@18` 落盘帧**（与 D14 同源）；骨盆 z 前段 = "
                 "共享解析弹道，触地帧后 = 三次 Hermite 落地曲线（单调不升、末端固定）；"
                 "后倒俯仰走**姿态层**（rx_self，**负值**）；`f ≥ LAND` 双腿**抬起**"
                 "（随髋 + 绝对抬高），贴地自持由四点 `hip_probe` 守。"),
    })

    if os.environ.get("D15_ARMDUMP"):
        dump = {}
        for side in SIDES:
            d0 = Vector(SEAM_FIST_DIR[side])
            d1 = Vector(BRACE_DIR[side]).normalized()
            e0 = Vector(SEAM_ELBOW_DIR[side]).normalized()
            e1 = Vector(ELBOW_BRACE[side]).normalized()
            h0 = Vector(SEAM_HAND_DIR[side]).normalized()
            dump[side] = {
                "fist_sweep_deg": round(math.degrees(math.acos(
                    max(-1.0, min(1.0, d0.dot(d1))))), 3),
                "elbow_sweep_deg": round(math.degrees(math.acos(
                    max(-1.0, min(1.0, e0.dot(e1))))), 3),
                "seam_fist_dir": [round(v, 4) for v in d0],
                "brace_fist_dir": [round(v, 4) for v in d1],
                "seam_elbow_dir": [round(v, 4) for v in e0],
                "brace_elbow_dir": [round(v, 4) for v in e1],
                "seam_hand_dir": [round(v, 4) for v in h0],
                "arm_max_mm": round(ARM_MAX[side] * 1000.0, 2),
                "seam_span_mm": round(SEAM_SPAN[side] * 1000.0, 2),
                "brace_span_mm": round(BRACE_SPAN_RATIO * ARM_MAX[side] * 1000.0, 2),
            }
        A.report("D15_ARMDUMP", dump)
    return arm, meshes


def main():
    arm, meshes = boot()

    JS._PREV_EULER.clear()
    UE.CARRY_Q.clear()
    LOCK_POSE.clear()
    HITSTOP_POSE.clear()
    _HITSTOP_REUSED[0] = 0
    _LOCK_REUSED[0] = 0
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
        "note": ("后倒（背面倒地）：前段沿用共享解析弹道，触地帧后换落地曲线"
                 "（骨盆 z 单调不升、末端固定）；后倒俯仰走姿态层（**负值**）；"
                 "触地 2 帧上身停顿；`f ≥ LAND` 双腿**抬起**（随髋 + 绝对抬高）"),
        "antic_frame": 0,
        "hit_frame": LAND,
        "land_frame": LAND,
        "cancel_frame": CANCEL,
        "compress_peak_frame": COMPRESS_PEAK,
        "supine_peak_frame": SUPINE_PEAK,
        "self_hold_frame": PLATEAU,
        "hitstop_frames": HIT_HOLD,
        "hit_points": 0,
        "root_motion_m": [0.0, round(PELVIS_Y_END - PELVIS_Y_START, 6)],
        "hit_point_m": None,
        "end_pelvis_z_m": round(pelvis_z_at(TOTAL), 6),
        "end_vz_m_per_frame": 0.0,
        "start_pose_ref": "%s 帧 %d（空中自持姿态）" % (SEAM_ACTION, SEAM_FRAME),
        "end_pose_ref": "后倒仰面躺地（贴地自持；D16 Ground_Hit / D18 GetUp_B 的起点）",
        "ballistic_ref": "anim_jump_start.TAKEOFF_PELVIS_Z/TAKEOFF_SPEED + "
                         "anim_jump_fall.G_PER_FRAME（相位续 D13 f%d）" % SEAM_FRAME,
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.add_markers(action, {"START": 0, "FALL_END": LAND - 1, "LAND": LAND,
                           "HITSTOP_END": HOLD_END, "SIT_PEAK": 10,
                           "COMPRESS_PEAK": COMPRESS_PEAK,
                           "SUPINE_PEAK": SUPINE_PEAK, "SELF_HOLD": PLATEAU,
                           "CANCEL": CANCEL, "END": TOTAL})

    samples = A.sample_animation(arm, action, 0, TOTAL, meshes)
    report = A.run_common_assertions(samples, meta, foot_probe=())
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

    report["seam_zero_saved_ok"] = bool(SEAM_MATCH["matched"])
    report["seam_zero_src"] = SEAM_MATCH["src"]
    report["seam_zero_geom_pos_mm"] = SEAM_MATCH["geom_pos"]
    report["seam_zero_geom_dir_deg"] = SEAM_MATCH["geom_dir"]
    report["seam_zero_worst_bone"] = SEAM_MATCH["pos_bone"]

    report["failed"] = sorted(k for k, v in report.items()
                              if k.endswith("_ok") and v is not True)
    report["non_ok_bools"] = sorted(
        k for k, v in report.items()
        if isinstance(v, bool) and not k.endswith("_ok") and v is not True)
    A.report("D15_REPORT", report)

    if not SKIP_RENDER:
        side_frames = list(range(0, TOTAL + 1))
        # ★ 清单 §4 第 8 步点名的 7 个关键帧：f0 / FALL_END / LAND / SIT_PEAK /
        #   SUPINE_PEAK / PLATEAU / END（= 0/6/7/10/15/16/20），再补上 2/4（空中过渡）与
        #   HOLD_END(8)（停顿末帧）与 COMPRESS_PEAK(11)（吸震峰值帧）。
        other_frames = [0, 2, 4, 6, LAND, HOLD_END, 10, COMPRESS_PEAK, 13,
                        SUPINE_PEAK, PLATEAU, TOTAL]
        # ★★ 侧视渲**两套**（实测理由，不是随手加的）：本支后倒带 **+Y 0.444 m** 的
        #   水平位移 ⟹ 末段整个人被推出 D13 那套取景的右边缘（实测 `f15~f20`
        #   `col_hi = 779` = 顶到边界，头被裁）。两套取景各有**不可替代**的用途：
        #     ① `knockdownb_side`（= D13/D14 **逐位相同**的取景）：供跨支尺子用。
        #        实测 `knockdownb_side_f0000` 与 `airhit_side_f0018` 的剪影范围
        #        逐位一致（cols 298~527 / rows 261~825 / 59570 px）⟹ `px_seam_frame_match_ok`
        #        在**同一把尺子**下成立。
        #     ② `knockdownbwide_side`（视中心 +Y 0.50 m，**正交宽仍是 3.30 m** ⟹
        #        仍是同一把 3 mm/px 的尺子，只是平移）：末段全身在画面内 ⟹
        #        `px_ground_hold_ok` / `px_supine_flip_ok` 与三重目检用这一套。
        #    ★ 为什么"平移"不破坏尺子：正交侧视的**行号只由世界 z 决定**
        #      （相机沿 −X 看、up = +Z）⟹ 平移只动列号，`z_mm = −350 + row×3` 不变。
        A.render_pose_sheet(arm, action, side_frames, "knockdownb",
                            views=(VIEW_D15_SIDE,))
        A.render_pose_sheet(arm, action, side_frames, "knockdownbwide",
                            views=(VIEW_D15_SIDE_WIDE,))
        A.render_pose_sheet(arm, action, other_frames, "knockdownb",
                            views=(VIEW_D15_FRONT, VIEW_D15_3Q))
        A.save_project()
        A.export_glb(arm)
    print("D15_DONE failed=%s" % report["failed"])
    print("D15_DONE non_ok_bools=%s" % report["non_ok_bools"])
    if os.environ.get("D15_TRACE"):
        print("D15_TRACE " + json.dumps(report.get("trace", {}),
                                        ensure_ascii=False))


# ★ 本支取景。侧视**第一套**与 D13/D14 **逐位相同**（跨支合并拟合那把尺子要求两段
#   画面同一把尺子）；**第二套**只把视中心沿 +Y 平移 0.50 m、正交宽不变
#   ⟹ 仍是同一把 3 mm/px 的尺子（正交侧视的行号只由世界 z 决定）。
VIEW_D15_SIDE = ("side", (5.20, 0.0, 1.30), (0.0, 0.0, 1.30), 3.30,
                 (780, 1100))
VIEW_D15_SIDE_WIDE = ("side", (5.20, 0.50, 1.00), (0.0, 0.50, 1.00), 3.30,
                      (780, 1100))
# ★ 前视/3Q 也必须放宽：实测末帧 `col_hi = 779`（顶到边界）。这两套只给人看
#   （像素探针的三重目检），不承担任何毫米级尺子职责 ⟹ 允许改正交宽。
VIEW_D15_FRONT = ("front", (0.0, -5.60, 0.95), (0.0, 0.35, 0.95), 4.20,
                  (780, 1100))
VIEW_D15_3Q = ("three_quarter", (4.10, -4.30, 1.15), (0.0, 0.35, 0.95), 4.60,
               (780, 1100))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("D15_FAILURE " + traceback.format_exc())
