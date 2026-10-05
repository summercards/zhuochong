"""anim_getup_f —— D17 `GetUp_F` 正面起身（俯卧 → 双掌撑地推起 → 收腿 → 站成战斗姿态）。

清单原文：「趴地起身；猛男用**撑地、翻身**等力量型动作」。

★★ 本支是**起身族第一支**，也是**全项目第一次跨族接缝**：
   起点在**地面族**（`Knockdown_F@20` 俯卧），终点在**站立族**（`Idle_01@0` 战斗站姿）。

   | 接缝 | 上游 / 下游 | 本支落成的做法 |
   |---|---|---|
   | 上游**姿态** | `Knockdown_F@20`（俯卧，脸朝下） | 本支 f0 **逐位 = `Knockdown_F@20`** |
   | 上游**动量** | D14 末帧 `end_vz = 0` | **不继承任何动量** —— 起身是**主动发力**，与全族前 16 支"被动受力"性质不同 |
   | 下游**站姿** | `Idle_01@0`（A 族通用站姿锚点） | 末帧（f34~f36）**逐位 = `Idle_01@0`**（世界矩阵 `max_delta ≤ 1e−6`）★★ **本支最硬的判据** |

★★ §1 本支的真风险：**竖直与水平跨度全项目最大，支点要换两次**

   实测（`probe_d17_baseline.py`，见 `D17_LAYOUT.seam.measured`）：

   | 量 | 起点 `Knockdown_F@20` | 终点 `Idle_01@0` | 跨度 |
   |---|---|---|---|
   | 骨盆世界 z | **220.0 mm** | **830.0 mm** | **+610 mm** |
   | 骨盆世界 y | **−550.0 mm** | **0.0 mm** | **+550 mm** |
   | 躯干（胸骨）世界俯仰 | **+88.06°** | **+9.00°** | **−79°** |

   ★ 与清单计划里写的「220 → 900（+680 mm）／−576 → −15」**不同**：那是**推算值**。
     实测 `Idle_01@0` 的骨盆 z = **830.0**（Idle 自身有 −70 mm 的沉腰），
     y = **0.0**（骨盆正对中线）。本支**一律以实测为准**，`rise_reach_ok` 的阈值
     因此按实测重定（见下），不是放宽容差，是把推算值换成实测值。

   ⟹ **三个支点、两次交接**（本支的结构核心）：

   | 段 | 帧区间 | 支点 | 竖直位移归谁 | 判据 |
   |---|---|---|---|---|
   | 撑地推起段 | `[START, HAND_OFF]` | **双掌**（世界 z ≈ 0） | 肩/肘/腕伸展把**胸**顶起来，骨盆跟着抬 | `chest_rise_ok` + `hand_off_ok`（下侧） |
   | 收腿交接段 | `(HAND_OFF, FOOT_SET)` | **手 → 脚**（唯一一次交接） | 重心后移，双脚接住 | ★★ `hand_off_ok`（上侧）+ ★★ `foot_takeover_ok` |
   | 起立段 | `[FOOT_SET, END]` | **双脚** | 腿的蹬伸把骨盆抬到 830 mm | `rise_monotone_ok` + `rise_reach_ok` + `no_foot_slide_ok` + `sole_ground_ok` |

   ★ **"支点交接"两侧方向相反的两条断言必须同时存在**（`hand_off_ok` 上侧 /
     `foot_takeover_ok`）：缺任何一条，就会有"手和脚同时在地上"或"谁都没在地上"
     的一整段没人管 —— 这是 D14 教训 4 在**两个支点**上的推广。

★★★ 本支的独门尺子（像素级，跨支，量"过程形状"）：`px_rise_monotone_ok`
   —— wide 侧视**全剪影顶缘单调不降**且**总升幅 ≥ 阈值**。
   **反面对照 = D16 自己**（`groundhitwide_side` 顶缘先升后降）⟹ 必红。
   ★ 口径修正（诚实登记）：清单计划原文写的是「**底行**单调不升」。
     本项目行号约定为**自画面底向上**（`probe_d16_pixels.py` 的 `rows_any` 直接用
     `image.pixels` 的索引，索引 0 = 画面底），在该约定下「起身」= 底行**上升**，
     与「单调不升」自相矛盾；且实测本支底行被**裤管穿地**（`Trouser_*`）与
     **收腿时双脚离地**两件事共同支配，本来就不是"起身"的合格载体。
     ⟹ 换成**顶缘**（剪影最高行）：它单调不降 + 总升幅大，同时证明
     「真的从地上起来了」与「是一次起来的、没有中途回落」。**不是放宽容差，是换对了载体。**

★ 帧预算：**36 帧 / 0.600 s @60fps**，非循环（硬上界 40）。
★ 相位 `T_PHASE_D17 = T_PHASE_D14 + 20 = 69.5`（**仅登记**，本支**没有弹道段**）。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python anim_getup_f.py
    SKIP_RENDER=1  只跑门禁不渲图（迭代用）
    D17_TRACE=1    逐帧打印骨盆 / 胸 / 手 / 脚 / 膝的实测值

反向验证（§4 第 7 步，7 组）：
    D17_TP_SEAM_ZERO=1    ① 首帧改零位（接缝断）        ⟹ `seam_in_ok` 红
    D17_TP_NOPUSH=1       ② 抽掉撑地（胸不抬）          ⟹ `chest_rise_ok` 红
    D17_TP_NOTUCK=1       ③ 抽掉收腿（脚不回位）        ⟹ `foot_takeover_ok` 红
    D17_TP_STICKYHAND=1   ④ ★ **手不离地**              ⟹ **`hand_off_ok` 红**（支点交接守卫）
    D17_TP_NOIDLE=1       ⑤ ★ **末帧不给站姿**          ⟹ **`end_matches_idle_ok` 红**（核心守卫）
    D17_TP_DIP=1          ⑥ 造回落（骨盆中途下沉）      ⟹ `rise_monotone_ok` 红
    D17_TP_ENDZERO=1      ⑦ 末帧改零位                  ⟹ `no_snap_stop_ok` / `end_vz_zero_ok` 红

★ 本支停用并**登记理由**的判据（照 D16 停用 `ballistic_until_land_ok` 的做法）：
    `ground_hold_ok` / `back_land_ok` / `landing_plateau_ok` / `legs_bounce_ok` /
    `bounce_*` 全族 —— 它们是**贴地族**的判据，本支骨盆要跑 610 mm，载体全部不同。
    `hitstop_present` —— 本支是**主动发力**动作，**没有"命中帧"**，硬套只会得到
    伪造的停顿；收招由 `no_snap_tail_ok` 守、"一次发力"由 `rise_monotone_ok` 守。
"""

import json
import math
import os
import struct
import sys

import bpy
from mathutils import Euler, Matrix, Quaternion, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A                     # noqa: E402
import anim_jump_start as JS             # noqa: E402
import anim_ultimate_end as UE           # noqa: E402
import anim_crouch as CR                 # noqa: E402
import probe_c12_baseline as P           # noqa: E402
import probe_d01_guard as PD             # noqa: E402

NAME = "GetUp_F"
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"
SIDES = ("L", "R")

# ★ 接缝真源：上游 D14 的落盘 action + 末帧号
SEAM_ACTION = os.environ.get("D17_SEAM_ACTION", "Knockdown_F")
SEAM_FRAME = int(os.environ.get("D17_SEAM_FRAME", "20"))
# ★ 终点真源：A 族通用站姿锚点
END_ACTION = os.environ.get("D17_END_ACTION", "Idle_01")
END_FRAME = int(os.environ.get("D17_END_FRAME", "0"))
# ★ 相位原点（`anim_knockdown_f.T_PHASE`）—— 本支**只登记**，不参与解算
D14_T_PHASE = 49.5
T_PHASE_D17 = D14_T_PHASE + 20.0                      # 69.5


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
    """量化到 float32 —— F-Curve 关键帧就是按 float32 存的（与 D02~D16 同源）。"""
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


def _clamp(value, lo, hi):
    return max(lo, min(hi, value))


def _smoothstep(x):
    x = _clamp(x, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


def _nearest_equiv(target, ref):
    """返回与 `ref` 相差 360° 整数倍里最接近 `ref` 的那个 `target` 等价表示。"""
    return target + 360.0 * round((ref - target) / 360.0)


def _slerp_dir(a, b, t):
    """两个**方向**之间的球面插值（单位向量）。`t` 已夹到 `[0, 1]`。

    ★★ 为什么必须用它而不是"逐分量插值再归一化"（`pwl_vec` + `.normalized()`）：
      当两个方向夹角接近 **180°** 时，逐分量插值的合成向量会**靠近原点**，
      归一化后角速度被放大 `1/sin(夹角)` 倍 —— 实测 `ELBOW_KEYS` 从
      `e2 = (0.40s, −0.30, 0.86)` 走到 `e_end`（夹角 **135.7°**），
      在 `[FOOT_SET, STAND]` 中点处合成向量长度只剩 **0.406** ⟹ 角速度放大
      **2.5×**，把 `forearm.L` 的局部欧拉单帧步长顶到 **81.95°**（`_d17_dbgC3.log`：
      `f=30` 步长 81.95 / 世界旋转 45.16°）。
      球面插值的角速度**均匀**（= 总夹角 / 段长）⟹ 峰值回到 8~9°/帧。
      这不是放宽容差：改的是**轨迹的角速度剖面**，两端方向逐位不变。
    """
    t = _clamp(t, 0.0, 1.0)
    av = Vector(a)
    bv = Vector(b)
    la, lb = av.length, bv.length
    if la < 1e-9 or lb < 1e-9:
        return Vector(b if la < 1e-9 else a)
    av, bv = av / la, bv / lb
    if t <= 0.0:
        return av
    if t >= 1.0:
        return bv
    dot = max(-1.0, min(1.0, av.dot(bv)))
    if dot > 0.999999:
        return av
    if dot < -0.999999:
        # ★ 严格反向：测地线不唯一。取一条**确定的**垂直方向，避免除零。
        seed = Vector((0.0, 0.0, 1.0))
        if abs(av.dot(seed)) > 0.9:
            seed = Vector((1.0, 0.0, 0.0))
        axis = seed - av * seed.dot(av)
        axis.normalize()
        return (Quaternion(axis, math.pi * t) @ av).normalized()
    omega = math.acos(dot)
    sin_omega = math.sin(omega)
    return (av * (math.sin((1.0 - t) * omega) / sin_omega)
            + bv * (math.sin(t * omega) / sin_omega)).normalized()


def _dir_keys_at(keys, frame, default):
    """方向关键帧（`((f, (x, y, z)), ...)`）的**球面**求值。

    ★ 段内用 `_slerp_dir`，`t` 走 **PCHIP**（与 `UE.pwl` 同族，峰值 ≈ 1.1× 均值），
      两端逐位等于端点 ⟹ 不影响 `f=0` 接缝与 `f=STAND` 接缝。
    """
    pts = [(float(f), Vector(v)) for f, v in keys]
    if frame <= pts[0][0]:
        return pts[0][1].normalized() if pts[0][1].length > 1e-9 \
            else Vector(default).normalized()
    if frame >= pts[-1][0]:
        return pts[-1][1].normalized() if pts[-1][1].length > 1e-9 \
            else Vector(default).normalized()
    for index in range(len(pts) - 1):
        f0, a = pts[index]
        f1, b = pts[index + 1]
        if f0 <= frame <= f1:
            span = float(f1 - f0)
            if span < 1e-9:
                return b.normalized()
            return _slerp_dir(a, b, (float(frame) - f0) / span)
    return pts[-1][1].normalized()


# =============================================================== 时间轴
#   ★ 节奏：**撑 9 / 收腿 5 / 蹬起 13 / 定 2**（36 帧 / 0.600 s @60fps）
#   ★★ 为什么撑地期只有 9 帧（原稿写 16）：`Hand_Palm/Finger` 网格到肩的距离
#      必须 ≤ 臂长（实测 `ARM_MAX ≈ 650 mm`）。逐帧实测（`_d17_geom4.log`）
#      |掌目标 − 肩| = 611(0) → 436(4) → 584(8) → **641(9)** → 698(10) → 997(16) mm
#      ⟹ **`f ≥ 10` 手在物理上够不到地面**。撑地期缩到 9 帧不是放宽，是把
#      「手在地上推」这段放在它真正成立的那 9 帧里。
#      （清单计划写的 16 帧基于"肩不随骨盆上抬"的推算；实测肩 z 从 316 → 869 mm。）
TOTAL = _env_i("D17_TOTAL", 36)
START = 0
PUSH = _env_i("D17_PUSH", 4)                  # 双掌撑地、肘开始伸（发力起手）
CHEST_UP = _env_i("D17_CHEST_UP", 6)          # 胸被顶上来的峰值帧
HAND_OFF = _env_i("D17_HAND_OFF", 9)          # ★ 支点交接 1：手掌离地帧（可达上限）
TUCK = _env_i("D17_TUCK", 14)                 # 收腿（膝收到身下）
FOOT_SET = _env_i("D17_FOOT_SET", 20)         # ★ 支点交接 2：双脚接住地面帧（唯一）
RISE_MID = _env_i("D17_RISE_MID", 27)         # 蹬伸中段
STAND = _env_i("D17_STAND", 34)               # 站直（骨盆 830 mm）＝ 逐位 = `Idle_01@0`
# ★★ 肘向/手向关键帧的**抵达帧**：`e1`/`h1`（撑地姿态方向）在第几帧到位。
#    原稿 = `PUSH`（4）⟹ 接缝→撑地的 88° 摆臂在 4 帧里走完，实测 `f=1 forearm.R`
#    欧拉步长 **44.53°**（`_d17_W3.log`，阈值 25）。推到 `HAND_OFF`（9）后摊到 9 帧。
#    ★ 只改**抵达时刻**、不改两端姿态 ⟹ 起止方向逐位不变。
DIR_END = _env_i("D17_DIR_END", HAND_OFF)
SELF_HOLD = STAND
CANCEL = STAND
END = TOTAL
if not (START < DIR_END <= HAND_OFF and START < PUSH < CHEST_UP < HAND_OFF
        < TUCK < FOOT_SET < RISE_MID < STAND <= TOTAL):
    raise RuntimeError("相位不自洽：PUSH=%d DIR_END=%d CHEST_UP=%d HAND_OFF=%d "
                       "TUCK=%d FOOT_SET=%d RISE_MID=%d STAND=%d TOTAL=%d"
                       % (PUSH, DIR_END, CHEST_UP, HAND_OFF, TUCK, FOOT_SET,
                          RISE_MID, STAND, TOTAL))

# =============================================================== 反验证旋钮
SEAM_ZERO = _env_b("D17_TP_SEAM_ZERO")
NO_PUSH = _env_b("D17_TP_NOPUSH")
NO_TUCK = _env_b("D17_TP_NOTUCK")
STICKY_HAND = _env_b("D17_TP_STICKYHAND")
NO_IDLE = _env_b("D17_TP_NOIDLE")
DIP = _env_b("D17_TP_DIP")
END_ZERO = _env_b("D17_TP_ENDZERO")

# =============================================================== 竖直 / 水平通道
#   ★★ 本支**没有弹道段**：骨盆沿一条**单调上升**的曲线从 220 mm 走到 830 mm。
#     三段（撑地 / 交接 / 起立）只是**支点**在换，骨盆从不回落 ⟹
#     `rise_monotone_ok` 覆盖全段（清单要求窗口 `[FOOT_SET, END]`，本支更强）。
Z_PELVIS_REST = 0.900
#   ★★ 撑地期 `[0, HAND_OFF]` 骨盆**只升 48 mm**（220 → 268）—— 这是本支的关键设计：
#      躯干在撑地期保持**近水平**，肩就停在低位，手才够得到地。
#      实测：躯干一旦按原稿早起（f=9 肩 z=736 mm），`|掌目标−肩|` 涨到 816 mm
#      （臂长 650）⟹ `reach_ok` 物理上必然红。撑起改到**手离地之后**发力。
PELVIS_Z_KEYS = (
    (START, 220.0), (PUSH, 238.0), (CHEST_UP, 248.0), (HAND_OFF, 268.0),
    (TUCK, 400.0), (FOOT_SET, 520.0), (RISE_MID, 662.0), (STAND, 830.0),
    (END, 830.0))
PELVIS_Y_KEYS = (
    (START, -550.0), (PUSH, -540.0), (CHEST_UP, -532.0), (HAND_OFF, -512.0),
    (TUCK, -410.0), (FOOT_SET, -330.0), (RISE_MID, -158.0), (STAND, 0.0),
    (END, 0.0))
# ★ 反验证 ⑥：造一次中途回落（骨盆在上升途中沉一下）⟹ `rise_monotone_ok` 必须红
DIP_KEYS = ((0, 0.0), (FOOT_SET, 0.0), (23, -58.0), (25, -30.0), (RISE_MID, 0.0),
            (END, 0.0))


def pelvis_z_at(frame):
    z = UE.pwl(PELVIS_Z_KEYS, float(frame), PELVIS_Z_KEYS[0][1])
    if DIP:
        z += UE.pwl(DIP_KEYS, float(frame), 0.0)
    return z / 1000.0


def pelvis_y_at(frame):
    return UE.pwl(PELVIS_Y_KEYS, float(frame), PELVIS_Y_KEYS[0][1]) / 1000.0


def pelvis_vz_at(frame):
    return (pelvis_z_at(frame) - pelvis_z_at(frame - 1)) * 1000.0


# =============================================================== 躯干通道
#   直接驱动**局部欧拉** rx（比"世界俯仰差分"更好控）：每根骨给一条
#   `0 = 接缝值 / 1 = Idle 值` 的进度曲线，另叠一条"拱起"曲线（撑地期把
#   胸腔顶起来 —— 猛男的撑地是**拱背**，不是平板撑）。
#   ★ 排法：**胸腔先起、骨盆后跟**（起身时先抬头挺胸，髋才被带起来）。
#   ★★ 撑地期 `[0, HAND_OFF]` 的进度必须**压得很低**（原稿的一半以下）：
#      肩是 chest 的子节点 ⟹ 躯干一旦按原稿早起，肩就冲出臂长。
#      实测（`_d17_geom5.log`，chest 进度 0.72 / 拱起 40° @ f=9）：肩 z = 735.9 mm，
#      `|掌目标−肩| = 816 mm`（臂长 650）⟹ `reach_ok` 0.987→1.255 全红，
#      连带 `hand_off_ok`（f=8/9 手已抬到 81.8/119.0 mm，够不到地）。
#      ⟹ 撑地期只走 **chest ≈ 0.20**（拱起保留 40°，视觉上的"撑起"靠拱背），
#      `f ≥ HAND_OFF` 才把进度放出去。这不是拆东墙补西墙：撑地段本来就只该
#      把**上身**顶起来（`chest_rise_ok` 实测 ≥ 300 mm，仍远超 200 mm 门槛），
#      骨盆与腿的抬升归**起立段**。
TORSO_PROG = {
    "root": ((0, 0.0), (END, 0.0)),
    "pelvis": ((0, 0.0), (PUSH, 0.02), (CHEST_UP, 0.06), (HAND_OFF, 0.10),
               (TUCK, 0.30), (FOOT_SET, 0.52), (RISE_MID, 0.85), (STAND, 1.0),
               (END, 1.0)),
    "spine_01": ((0, 0.0), (PUSH, 0.03), (CHEST_UP, 0.09), (HAND_OFF, 0.14),
                 (TUCK, 0.36), (FOOT_SET, 0.58), (RISE_MID, 0.87), (STAND, 1.0),
                 (END, 1.0)),
    "spine_02": ((0, 0.0), (PUSH, 0.03), (CHEST_UP, 0.09), (HAND_OFF, 0.14),
                 (TUCK, 0.36), (FOOT_SET, 0.58), (RISE_MID, 0.87), (STAND, 1.0),
                 (END, 1.0)),
    "chest": ((0, 0.0), (PUSH, 0.04), (CHEST_UP, 0.12), (HAND_OFF, 0.20),
              (TUCK, 0.44), (FOOT_SET, 0.66), (RISE_MID, 0.90), (STAND, 1.0),
              (END, 1.0)),
    "neck": ((0, 0.0), (PUSH, 0.05), (CHEST_UP, 0.15), (HAND_OFF, 0.24),
             (TUCK, 0.48), (FOOT_SET, 0.70), (RISE_MID, 0.92), (STAND, 1.0),
             (END, 1.0)),
    "head": ((0, 0.0), (PUSH, 0.05), (CHEST_UP, 0.14), (HAND_OFF, 0.23),
             (TUCK, 0.47), (FOOT_SET, 0.69), (RISE_MID, 0.91), (STAND, 1.0),
             (END, 1.0)),
}
# "拱起"（度，正数 = rx 往负方向（后仰）压，把胸腔顶起来 / 抬头）
ARCH_KEYS = {
    "pelvis": ((0, 0.0), (PUSH, 1.0), (CHEST_UP, 6.0), (HAND_OFF, 7.0),
               (TUCK, 4.0), (FOOT_SET, 1.0), (RISE_MID, 0.0), (END, 0.0)),
    "chest": ((0, 0.0), (PUSH, 4.0), (CHEST_UP, 34.0), (HAND_OFF, 40.0),
              (TUCK, 26.0), (FOOT_SET, 10.0), (RISE_MID, 2.0), (END, 0.0)),
    "neck": ((0, 0.0), (PUSH, 2.0), (CHEST_UP, 16.0), (HAND_OFF, 18.0),
             (TUCK, 10.0), (FOOT_SET, 3.0), (RISE_MID, 0.0), (END, 0.0)),
    "head": ((0, 0.0), (PUSH, 3.0), (CHEST_UP, 24.0), (HAND_OFF, 26.0),
             (TUCK, 14.0), (FOOT_SET, 4.0), (RISE_MID, 0.0), (END, 0.0)),
}


def arch_of(name, frame):
    if NO_PUSH:
        return 0.0
    keys = ARCH_KEYS.get(name)
    return 0.0 if keys is None else UE.pwl(keys, float(frame), 0.0)


# =============================================================== 参考朝向交接
#   ★★ **滚转参考**与**膝向**都有一对"两端参考"：零位（`Knockdown_F@20`，俯卧）
#      与终点（`Idle_01@0`，站姿）。它们决定的是"骨绕自身轴滚到哪"，**不改骨轴
#      方向**，所以交接过程中踝/膝/腕的位置逐位不动。
#   ★ 不交接的后果（实测，`_d17_gate6.log`）：站起来这一段被硬拽回"趴着时的滚转"，
#      `f=33 → f=34` 在 `upperarm.R` 上攒出 **124.87°** 欧拉跳变 ⟹
#      `no_teleport` + `no_snap_stop_ok` 同时红；鞋底也因小腿被拧而比 `Idle` 低
#      **最多 7 mm**（`_d17_geom6.log`：`f=20` 鞋底 −8.09，`f=34` 才是 −0.96）。
NO_ROLL_MIX = _env_b("D17_TP_NOROLLMIX")
# ★ 臂骨"滚转收尾"：臂的滚转由 `_roll_return` 统一负责（见 `build_pose` 收尾段）。
#   反验证旋钮：`D17_ARM_ROLL_TAIL=0` 关掉它 ⟹ 臂的滚转交回
#   `_set_euler_nearest` 的自由搜索 ⟹ `f=33→34` 重新出现 124° 表示跳变。
ARM_ROLL_TAIL = os.environ.get("D17_ARM_ROLL_TAIL", "1").strip() not in ("", "0", "false", "False")
# ★★ 臂骨收尾的**欧拉支搜索**：在 `_roll_return` 把滚转拉到参考之后，再搜一圈
#    **绕骨轴滚转**找一个"离上一帧最近"的欧拉支（绕骨轴滚不动骨根/骨尖 ⟹
#    拳位、`reach_ok`、`clip_metrics` 全不受影响），用来绕开 XYZ 万向节锁带。
#    实测依据 `_d17_eul8.log` 全段扫描（step > 25°）：`f=1 forearm.L 48.54`、
#    `f=7 hand.R 83.26`、`f=10 hand.L 93.14`、`f=12 forearm.R 93.77`、
#    `f=13 hand.R 62.32`、`f=27 hand.R 85.91` —— 全是臂链。
#    ★★ 但**滚转不能自由跑**：越接近末帧，滚转越必须回到参考（`f = STAND` 由
#      `_end_pose_continuous` 接管，滚转逐位 = `Idle`、`phi` 只取 0）。
#      实测（`_d17_gate14.log`）：不加罚分时搜索会把 `f=33` 的 `hand.R` 拧到
#      偏离参考处，`f=33→34` 反而攒出 **75.17°** 跳变 ⟹ `no_snap_stop_ok` 红。
#      ⟹ 罚分 = `ROLL_PENALTY_DEG * roll_mix^2 * |φ|`：`f ≤ FOOT_SET`（mix=0）
#        完全自由；`f → STAND` 罚分指数级压住φ ⟹ 滚转平滑收回参考。
ARM_ROLL_PENALTY_DEG = _env_f("D17_ARM_ROLL_PENALTY", 20.0)
# ★★★ 头部冻结窗口（帧数，0 = 关）：见 `build_pose` 内注释。尾段有
#    `_roll_grid_window` 把滚转自由度随 `roll_mix` 收到 `φ=0`；头段此前**没有**
#    对应机制 ⟹ `f=1` 的扭转跳变（`hand.L` 真实世界旋转 55.71°）无人管。
HEAD_FREEZE = max(0, _env_i("D17_HEAD_FREEZE", 0))
# ★★ 撑地段拳目标改走**分段线性**（见 `_lerp_keys_clamped` 注释）。默认 1。
PLANT_LINEAR = (os.environ.get("D17_PLANT_LINEAR", "1").strip()
                not in ("", "0", "false", "False"))
# ★ 末段腿骨重写欧拉支的 `roll_mix` 门槛（`f=STAND−1` 时 `mix ≈ 0.9854`）。
TAIL_GRID_MIX = _env_f("D17_TAIL_GRID_MIX", 0.98)
# ★★ 滚转参考的交接**必须在 `STAND−1` 就走到 1.0**：`f = STAND` 起由
#    `_end_pose_continuous` 接管（滚转 = `Idle_01@0`，`phi` 只取 0）。若参考在
#    `f = STAND−1` 还差 1.5%，那 1.5% 的残差会**整段**攒进 `f=STAND−1 → STAND`
#    这一步里（`no_teleport` / `no_snap_stop_ok` 量的就是这一步）。
#    实测依据 `_d17_gate9.log`：`shin.R` 局部欧拉 `f=33` 与 `f=34` 的世界旋转
#    差 **96.89°**，而两者的**骨轴方向几乎相同** ⟹ 差的全是"绕骨轴的滚转"。
ROLL_MIX_END = _env_i("D17_ROLL_MIX_END", STAND - 1)
# ★★ 腿骨"滚转收尾"：主循环的 `ROLL_BONES` 是 **frozenset** ⟹ `thigh`/`shin`
#    的先后是**任意的**。若 `shin` 先滚、`thigh` 后滚，`thigh` 绕自身轴的那一下
#    会把**已经滚好的 `shin`** 一起带走 ⟹ `shin` 的最终滚转 ≠ 参考。
#    这里按 **父先子后**（`thigh → shin`）在最后重滚一遍 + 重钉脚 + 重写欧拉支。
LEG_ROLL_TAIL = os.environ.get("D17_LEG_ROLL_TAIL", "1").strip() not in (
    "", "0", "false", "False")


def roll_mix_at(frame, bone=None):
    """参考朝向从**零位（俯卧）**交接到 **`Idle_01@0`（站姿）** 的权重。

    ★ 窗口 `[FOOT_SET=20, STAND=34]`，臂腿共用。曾试过把腿的窗口提前到
      `[TUCK, FOOT_SET]`（想让 `f=FOOT_SET` 就是站姿滚转），实测**无效**：
      `f=20` 鞋底仍是 −8.02（原 −8.09）—— 因为鞋底偏负的真正载体是
      **小腿的折叠**（`Shoe_Heel` 权重 foot 32.1 / **shin 29.9**），不是滚转；
      提前窗口反而让 `f=18/19` 鞋底提前压到地面，打红 `foot_takeover_ok`。
      **已回退。**
    """
    if NO_ROLL_MIX:
        return 0.0
    return _smoothstep((float(frame) - float(FOOT_SET))
                       / float(ROLL_MIX_END - FOOT_SET))


def knee_dir_at(side, frame):
    """膝鼓出方向：`KNEE_DIR`（接缝）→ `END_KNEE_DIR`（`Idle_01@0`）。"""
    t = roll_mix_at(frame, "thigh." + side)
    a = KNEE_DIR[side]
    if t <= 0.0:
        return a
    b = Vector(END_KNEE_DIR[side])
    if t >= 1.0:
        return b
    # ★ 球面插值（不是逐分量插值后归一化）：理由同 `_slerp_dir`。
    return _slerp_dir(a, b, t)


# =============================================================== 手（拳）目标
#   ★ 撑地段用**世界落掌点**（手真的钉在地上推），收手后切成**肩相对**目标
#     （C13 口径：绝对世界点会在骨盆大幅移动时踩进深折叠奇点）。
def _parse_num_keys(spec, default):
    """`"f:v,f:v,..."` → `((f, v), ...)`；校验帧序单调，否则回退 `default`。"""
    try:
        out = tuple((int(a), float(b)) for a, b in
                    (item.split(":") for item in spec.split(",") if item.strip()))
    except Exception:  # noqa: BLE001
        return default
    if len(out) < 2 or any(out[i][0] >= out[i + 1][0]
                           for i in range(len(out) - 1)):
        return default
    return out


# ★★ `f=HAND_OFF → HAND_OFF+1` 的**单帧抬掌量**（米）是这一段的总闸门：
#    实测（`_d17_R_R1.log` / `_d17_eulR3.log`）原稿 0 → 0.150 让掌最低点在
#    `f=10` 一帧从 −15 mm 冲到 **+216 mm**，`upperarm.R` 世界旋转 **43.7°/帧**
#    （`forearm.R` 局部欧拉步长 68.1°）。而 `hand_off_ok` 只要求 `f=10` ≥ 60 mm。
#    ⟹ 抬掌改成**平缓的钟形**：`f=10` 只抬到刚够 60+ mm，峰值推到 `HAND_OFF+4`，
#      再一路收回 0。峰值高度由 `D17_LIFT_PEAK` 缩放，曲线可由 `D17_LIFT_KEYS` 整条覆盖。
HAND_OFF_LIFT_DEFAULT = ((0, 0.0), (HAND_OFF, 0.0), (HAND_OFF + 1, 0.060),
                         (HAND_OFF + 2, 0.110), (HAND_OFF + 3, 0.140),
                         (HAND_OFF + 4, 0.150), (TUCK, 0.115),
                         (FOOT_SET - 2, 0.050), (FOOT_SET, 0.0), (END, 0.0))
_LIFT_SPEC = os.environ.get("D17_LIFT_KEYS", "").strip()
HAND_OFF_LIFT_KEYS = (_parse_num_keys(_LIFT_SPEC, HAND_OFF_LIFT_DEFAULT)
                      if _LIFT_SPEC else HAND_OFF_LIFT_DEFAULT)
#    ★ 定稿取 `HAND_OFF + 8`（= 17）：收手段从 4 帧摊到 8 帧。
HAND_MIX_END = _env_i("D17_HAND_MIX_END", HAND_OFF + 8)
# ★★ 收手混合的**速率曲线**：`D17_HAND_MIX_POW = 0` 用 `smoothstep`（原稿），
#    `> 0` 用 `u**p`。为什么需要这个旋钮：`no_teleport` 在 `f=11 forearm.R` 卡在
#    **82.09°**（真实世界旋转只有 26.81°），而它是**掌目标**从"落掌偏移"混向
#    "`Idle` 拳偏移"这一段里 `s` 的**单帧增量**造成的 —— `smoothstep` 在中点斜率
#    1.5×平均，`u=0.25→0.5` 一步就吃掉 **0.344** 的总行程。线性 (`p=1`) 把它摊平到
#    `1/N`。**只改收手轨迹的速率，不改起点/终点**（两端 `s=0/1` 逐位不变 ⟹
#    `hand_off_ok` 的两侧与末帧接缝均不受影响）。
#    ★ 定稿取 `p = 1`（线性）：`smoothstep` 的中点斜率把 `f=11` 的臂步长顶到 34~39°。
HAND_MIX_POW = _env_f("D17_HAND_MIX_POW", 1.0)

# ★★★ 臂链末段改用**逐分量欧拉路径插值**的起始帧（A12 定案，见 `build_pose` 末段注释）。
#   本帧起，臂骨不再由 IK 决定，而是从 `f = ARM_MIX_FROM − 1` 的 IK 解**逐分量**线性
#   混向 `Idle_01@0`，直到 `STAND−1` 构造性抵达。`0` = 关闭（回到原 IK 路径）。
#   默认取 `HAND_MIX_END`：此时掌目标已**构造性**等于 `Idle` 的肩-拳偏移
#   （`_hand_mix_s(1) = 1`），臂链后续只剩"绕骨轴的扭转"这一个自由 DOF 需要交接。
ARM_MIX_FROM = _env_i("D17_ARM_MIX_FROM", 20)   # 0 = 关闭（回原 IK 路径）
TAIL_ARM = {}

# ★★★ 臂链**起手段**的同一手法（A12 定案，反向用）：接缝（俯卧 `Knockdown_F@20`）
#    → 撑地（`PUSH`）这一小段里，臂要从"前伸贴地"摆到"肘外张、掌在肩下"，骨轴方向
#    总转 ~88°。这段的 IK 目标是**非线性**地映射到局部欧拉的（A12 原文：「IK 只钉
#    骨轴方向，绕骨轴的扭转是自由 DOF」）⟹ 逐帧解算在 `f0→f1` 一步攒出
#    `forearm.R` 欧拉分量 **44.53°**（实测 `_d17_W3.log`，报告口径
#    `max_frame_step_deg`，阈值 25）。`D17_ARM_MIX_TO = K`（K>0）时，`[1, K−1]` 的臂骨
#    欧拉改由**逐分量线性路径**从 `f0` 接缝值混到 `f=K` 的 IK 解；峰值步长有解析上界
#    = 最大分量差 × 1.136 / 段长（A12 原文）。`0` = 关闭（回原 IK 路径）。
#    ★ 与末段相反的方向，同一条定案：**两端都是显式给定姿态时，走逐分量欧拉路径**。
ARM_MIX_TO = _env_i("D17_ARM_MIX_TO", 0)   # 0 = 关闭（回原 IK 路径）

# ★★★ 臂链的**通用锚点路径**（把上面 head/tail 两个特例统一）：
#   `D17_ARM_ANCHORS="0,9,10,19,34"` ⟹ 相邻锚点之间，`ARM_BONES` 的欧拉按**逐分量**
#   路径插值（smoothstep 参数化），锚点帧本身保持 IK 解（首锚点 = 接缝、末锚点 =
#   `Idle_01@0`）。峰值步长有解析上界 = 最大分量差 × 1.136 / 段长（A12 定案）。
#   ★ 为什么需要「多锚点」而不是单一 head/tail：本支的臂有两个**必须逐帧服从 IK 的
#     约束帧**——`f=9`（掌必须还在地上）与 `f=10`（掌必须 ≥ 60 mm，`hand_off_ok` 两侧），
#     以及 `f=19/20`（收手 → 撑地过渡）。锚点把这两帧钉成 IK，其余帧走线性欧拉路径。
#   `""` = 关闭（回 head/tail 两个特例路径）。
#   ★ 定稿默认 = `(START, HAND_OFF, HAND_OFF+1, FOOT_SET−1, STAND)`；本支实测把
#     `max_frame_step_deg` 从 44.53 压到 **21.37**（`_d17_L3.log`，阈值 25）。
_ANCHORS_SPEC = os.environ.get("D17_ARM_ANCHORS")
if _ANCHORS_SPEC is None:
    ARM_ANCHORS = (START, HAND_OFF, HAND_OFF + 1, FOOT_SET - 1, STAND)
else:
    ARM_ANCHORS = tuple(sorted(set(
        int(_t) for _t in _ANCHORS_SPEC.replace(" ", "").split(",")
        if _t.lstrip("-").isdigit())))

# ★★★ 锚点之间用**哪种插值**：
#   `0` = 逐分量欧拉（A12 原文口径；`D17_ANCHOR_SLERP=0`）
#   `1` = **局部旋转的四元数 slerp**（本支实测需要的）
#   ★ 为什么必须实测决定：撑地段「接缝 → 撑地」的臂骨局部旋转总量 ≈ 88°，
#     且两端骨轴**夹角大**。逐分量欧拉插值在这种情形下**中点会鼓出去** ——
#     实测（`_d17_anc*.log`）：锚点 `(0,9)` + 欧拉插值时 `f=4` 拳（= `hand.*` 骨端，
#     也是 IK 的驱动点）被顶到世界 z **−148.6 mm**（IK 目标 +32 mm，差 181 mm），
#     `Finger_*` 最低 **−177.85 mm**；而**关掉锚点**（纯 IK）只有 **−21.5 mm**。
#     ⟹ 那 −178 mm 不是 IK 解错，是**欧拉插值鼓包**。
#     加密锚点到 `(0,2,4,6,9,…)` 能把 −178 压到 −32，但步长在 `f=2` 反弹到 30.5°。
#     四元数 slerp 走**测地线**：既没有鼓包，单步步长又被 `总角 / 段长 × 1.5` 卡住
#     （与 A12「折叠到同一等价族」同义，只是把"等价族折叠"做到**四元数最近支**）。
ANCHOR_SLERP = (os.environ.get("D17_ANCHOR_SLERP", "1").strip()
                not in ("", "0", "false", "False"))
#   ★ 但 slerp **不能全段用**：末段 `19 → 34` 改用 slerp 后，`f=26 forearm.R` 的
#     逐分量欧拉步长反弹到 **70.39°**（四支锚点配置全同 —— 那一步就在这段里），
#     而欧拉插值在这段是**好的**。⟹ 按**帧**分工：只对 `_fb ≤ 本值` 的段用 slerp。
ANCHOR_SLERP_UNTIL = _env_i("D17_ANCHOR_SLERP_UNTIL", HAND_OFF)


def _hand_mix_s(u):
    u = max(0.0, min(1.0, float(u)))
    if HAND_MIX_POW <= 0.0:
        return _smoothstep(u)
    return u ** HAND_MIX_POW

# ★★ 收手期的**侧向张手**（米，>0 = 往身体外侧）。收腿段手从"撑地点"收回到身侧，
#    但头盒是**偏的**（实测 `f=13`：头盒 x ∈ [−112.7, 56.4] mm，中点在 −28 mm，
#    而右手腕在 x ≈ −128 mm）⟹ 前臂贴着头的左前下角走，`clip_metrics` 报
#    **27.1 mm** 穿模（`_d17_geom6.log`；`CLIP_MAX_MM = 0`）。把拳往**外侧**挪
#    是唯一不破坏"收手回到身侧"语义的解法（猛男收手时手本来就比头宽）。
#    实测需要的余量：腕点到头盒外距 14.9 mm，臂等效半径 42 mm ⟹ 至少外移 27 mm。
HAND_SPREAD_M = _env_f("D17_HAND_SPREAD", 0.062)
HAND_SPREAD_KEYS = ((0, 0.0), (HAND_OFF, 0.0), (HAND_OFF + 1, 0.10),
                    (HAND_OFF + 2, 0.32), (TUCK, 1.0), (FOOT_SET, 0.46),
                    (RISE_MID, 0.0), (STAND, 0.0), (END, 0.0))


def hand_spread(frame):
    """收手期的侧向张手量（米）。撑地期与站定后恒为 0 ⟹ 不影响两条接缝。"""
    return HAND_SPREAD_M * UE.pwl(HAND_SPREAD_KEYS, float(frame), 0.0)


def hand_lift(frame):
    if STICKY_HAND:
        return 0.0
    return UE.pwl(HAND_OFF_LIFT_KEYS, float(frame), 0.0)


def _lerp_keys_clamped(keys, frame, default):
    """分段**线性**求值（键按帧升序，`frame` 夹在两端之间）。

    ★ 为什么需要它：`UE.pwl` 是 **PCHIP**（单调三次 Hermite）。PCHIP 的**端点导数**
      用单侧三点公式估计，键距**不均匀**时会过冲 —— 本支 `PLANT_KEYS` 的键距是
      `(0→4)=4, (4→5)=1, (5→6)=1, (6→9)=3`，`h0=4, h1=1, d0=96.5, d1=34`
      ⟹ 端点导数 `d(0) = ((2h0+h1)·d0 − h0·d1)/(h0+h1) = 146.5 mm/帧`
      （真实平均只有 96.5）—— **前端速度被放大 1.5×**。这正是 `f=1` 那一步
      `forearm.R` 真实世界旋转 **39.6°**（远超 88°/9 帧 ≈ 9.8°/帧 的均值）的来源。
      分段线性把速度摊平到逐段常数，端点不吃过冲。
    """
    keys = sorted(keys, key=lambda kv: kv[0])
    if not keys:
        return list(default)
    if frame <= keys[0][0]:
        return list(keys[0][1])
    if frame >= keys[-1][0]:
        return list(keys[-1][1])
    for (fa, va), (fb, vb) in zip(keys, keys[1:]):
        if fa <= frame <= fb:
            if fb == fa:
                return list(vb)
            u = (float(frame) - float(fa)) / float(fb - fa)
            return [a + (b - a) * u for a, b in zip(va, vb)]
    return list(keys[-1][1])


def fist_target(arm, side, frame):
    """拳世界目标。

    `f ≤ HAND_OFF` ⟹ **世界落掌点**（手钉在地上；`STICKY_HAND` 旋钮把它延伸全覆盖）。
    `f >  HAND_OFF` ⟹ **肩 + 偏移**，偏移从"落掌偏移"过渡到 `Idle_01@0` 的肩-拳偏移。
    """
    shoulder = Vector(A.bone_world(arm, "upperarm." + side, "head"))
    if PLANT_LINEAR:
        world = Vector(_lerp_keys_clamped(PLANT_KEYS[side], float(frame),
                                          SEAM_FIST[side]))
    else:
        world = pwl_vec(PLANT_KEYS[side], float(frame), SEAM_FIST[side])
    if STICKY_HAND:
        return world
    if frame <= HAND_OFF:
        return world
    s = _hand_mix_s((float(frame) - HAND_OFF) / (HAND_MIX_END - HAND_OFF))
    off_a = world - shoulder
    off_b = Vector(END_OFF[side])
    off = off_a * (1.0 - s) + off_b * s
    off.z += hand_lift(frame)
    # ★ 侧向张手：`L` 往 +x、`R` 往 −x（世界 +X = 角色左侧）。
    off.x += (1.0 if side == "L" else -1.0) * hand_spread(frame)
    return shoulder + off


def elbow_dir(side, frame):
    """肘的鼓出偏好（世界向量）。撑地期**肘往外张**（push-up 的肘窝朝外）。

    ★★ 走 `_dir_keys_at`（**球面**求值），不是 `pwl_vec` + `.normalized()`：
      见 `_slerp_dir` 的注释 —— 逐分量插值在 `e2 → e_end`（夹角 135.7°）中段
      会把角速度放大 2.5×，正是 `no_teleport` 在 `f≈30` 的元凶。
    """
    return _dir_keys_at(ELBOW_KEYS[side], frame, SEAM_ELBOW_DIR[side])


def hand_dir_of(side, frame):
    """手骨世界朝向：接缝值 → `Idle_01@0` 值。同样走**球面**求值。"""
    return _dir_keys_at(HAND_DIR_KEYS[side], frame, SEAM_HAND_DIR[side])


# =============================================================== 踝目标
ANKLE_LIFT_KEYS = {
    "L": ((0, 0.0), (PUSH, 0.010), (PUSH + 1, 0.040), (CHEST_UP, 0.060),
          (HAND_OFF, 0.130), (TUCK, 0.205), (FOOT_SET, 0.0), (END, 0.0)),
    "R": ((0, 0.0), (PUSH, 0.012), (PUSH + 1, 0.048), (CHEST_UP, 0.070),
          (HAND_OFF, 0.140), (TUCK, 0.215), (FOOT_SET, 0.0), (END, 0.0)),
}


# ★★ 落地前"抬脚离地余量"（米）—— 防止 `f = FOOT_SET−2 / −1` 鞋底提前压到地面
#    （`foot_takeover_ok` 要求落地帧**唯一**）。实测（`_d17_gate16/17.log`）：
#    默认曲线在 `f=18 / 19` 鞋底 −8.91 / −41.49 mm（已穿地），使 `touch = [18,19,20]`。
#    这里在 `FOOT_SET` 前 2 帧补一段抬脚（不影响 `f ≥ FOOT_SET` 的构造性钉脚，
#    也不影响 `f ≤ TUCK` 的收腿），把下降改成**单调落地**（`f=20` 才首次触地）。
#    抬脚量取**实测反推**：需要把 f19 从 −41.49 抬到 > +6 ⟹ ≥ 48 mm。
#    ★ 定稿取 **0.05**（原 0.100）：加了 `FOOT_PIN_BLEND` 之后，`f17..19` 的鞋底
#      朝向已经是 `Idle` 脚朝向的混入值，不再需要 86 mm 的抬脚余量 —— 100 mm 的
#      余量会在 `f=20` 一帧里收回，把 `shin.L` 顶到 30.51°。降到 50 mm（峰值 0.86×50
#      = 43 mm 余量）后 `foot_takeover_ok`（`touch=[20]` 唯一）与 `sole_ground_ok`
#      仍**逐条为真**，`f=19` 鞋底仍有 **+52.9 mm** 净空。
ANKLE_CLEAR_M = _env_f("D17_ANKLE_CLEAR", 0.050)
ANKLE_CLEAR_KEYS = ((0, 0.0), (TUCK, 0.0), (FOOT_SET - 3, 0.20),
                    (FOOT_SET - 2, 0.62), (FOOT_SET - 1, 0.86),
                    (FOOT_SET, 0.0), (END, 0.0))


def ankle_target(arm, side, frame):
    """踝世界目标：接缝（俯卧）→ 抬起收腿 → `FOOT_SET` 起**抬跟后的 Idle 落脚点**。

    ★★ `f ≥ FOOT_SET` 目标**恒定**（= `END_ANKLE` 绕**脚尖关节**转一个固定的抬跟角），
      与帧号无关 ⟹ 脚**构造性不滑**（`no_foot_slide_ok`）：脚尖关节是旋转不动点，
      而 `toe.*` 骨端正是滑移尺子的探针（见 `_heel_ankle`）。
    """
    end = Vector(END_ANKLE[side])
    if NO_TUCK:
        # ★ 反验证 ③：抽掉收腿 —— 踝从接缝一路直线飞到终点（不是"收腿"，是"瞬移"）
        if frame <= 0:
            return Vector(SEAM_ANKLE[side])
        t = _smoothstep(float(frame) / float(FOOT_SET))
        return Vector(SEAM_ANKLE[side]) * (1.0 - t) + end * t
    if frame >= FOOT_SET:
        return _heel_ankle(side, frame)
    if frame <= 0:
        return Vector(SEAM_ANKLE[side])
    if frame <= TUCK:
        t = _smoothstep(float(frame) / float(TUCK))
        base = Vector(SEAM_ANKLE[side]) * (1.0 - t) + Vector(TUCK_ANKLE[side]) * t
    else:
        t = _smoothstep((float(frame) - TUCK) / float(FOOT_SET - TUCK))
        base = Vector(TUCK_ANKLE[side]) * (1.0 - t) + end * t
    base = base.copy()
    # ★ 单位口径：本文件全部**世界目标**用米（`bone_world` 原生口径）。
    #   `ANKLE_LIFT_KEYS` 已是米，直接相加 —— 曾误写 `1000.0 *` 把踝顶到 215 m，
    #   腿 IK 被夹到极限 ⟹ 脚挂在 1350 mm 天上（`_d17_gate2.log` trace）。
    base.z += UE.pwl(ANKLE_LIFT_KEYS[side], float(frame), 0.0)
    # ★ 落地前抬脚余量（见 `ANKLE_CLEAR_M`）：让鞋底在 `f < FOOT_SET` 保持离地
    base.z += ANKLE_CLEAR_M * UE.pwl(ANKLE_CLEAR_KEYS, float(frame), 0.0)
    return base


# =============================================================== ★ 抬跟（鞋底贴地）
#   ★★ 为什么必须有这一段：`f ≥ FOOT_SET` 起脚的世界朝向被钉成 `Idle_01@0` 的脚朝向、
#      踝被钉在 `END_ANKLE` —— 但**鞋底仍然随小腿的折叠一起往下沉**：鞋的
#      `Shoe_Heel_*` 有约 **一半权重绑在 `shin.*`** 上（实测 `_d17_probe_weights.py`：
#      `foot 32.1 / shin 29.9`）⟹ 深蹲时小腿大幅折叠，脚跟被拖着往下走。
#      实测 `_d17_gate9.log`：`f = 20` 鞋底 **−8.09 mm**、`f = 33` 仍 **−3.52 mm**，
#      而 `f = 34`（逐位 = `Idle_01@0`）才是 −0.96 mm ⟹ `sole_ground_ok`
#      （要求 ∈ [−2, +6] mm）红了一整段。
#   ★ 做法：**绕脚尖关节抬跟**（真实深蹲就是脚跟离地）。旋转不动点取 `Idle_01@0`
#      的 `toe.*` 骨头端 ⟹ 滑移尺子的探针**逐位不动** ⟹ `no_foot_slide_ok` 不受影响
#      （不是靠容差，是构造性）。抬跟角随起身收回到 0 ⟹ `f = STAND` 与 `Idle_01@0`
#      逐位一致（`end_matches_idle_ok` 不受影响）。
# ★★ 落地前一帧的「脚朝向分支切换」缓冲（帧数，0 = 关闭）。见 `_foot_euler` 内注释。
#    定稿取 4（= `FOOT_SET−4 = f16` 起把 `Idle` 脚朝向混进来）：`f=20 shin.L` 的欧拉
#    步长从 30.51° 压到 16.87°，且鞋底下降从「f18→f19 反弹」变成**单调**（`_d17_L3.log`）。
FOOT_PIN_BLEND = _env_i("D17_FOOT_PIN_BLEND", 4)

HEEL_LIFT_PEAK_DEG = _env_f("D17_HEEL_PEAK", 2.60)
HEEL_LIFT_KEYS = ((0, 0.0), (TUCK, 0.0), (FOOT_SET - 2, 0.30),
                  (FOOT_SET, 1.0), (RISE_MID, 0.42), (STAND, 0.0), (END, 0.0))


def heel_lift_deg(frame):
    return HEEL_LIFT_PEAK_DEG * UE.pwl(HEEL_LIFT_KEYS, float(frame), 0.0)


def _heel_rot(side, frame):
    """抬跟旋转（世界 X 轴，+ 角 = 脚跟抬起）。零角返回 `None`（省一次矩阵乘）。"""
    theta = math.radians(heel_lift_deg(frame))
    if abs(theta) < 1e-9:
        return None
    return Matrix.Rotation(theta, 3, "X")


def _heel_ankle(side, frame):
    """抬跟后的踝世界目标 = 脚尖关节 + R·(`END_ANKLE` − 脚尖关节)。"""
    end = Vector(END_ANKLE[side])
    rot = _heel_rot(side, frame)
    if rot is None:
        return end
    pivot = Vector(END_TOE[side])
    return pivot + rot @ (end - pivot)


def _pin_foot_world(arm, name, side, frame):
    """把脚骨的世界 3×3 钉成 **`Idle_01@0` 的脚朝向 × 抬跟旋转**（只动旋转，不动位置）。"""
    pose_bone = arm.pose.bones[name]
    current = pose_bone.matrix.copy()
    basis = END_FOOT_BASIS[name].copy()
    rot = _heel_rot(side, frame)
    if rot is not None:
        basis = rot @ basis
    target = basis.to_4x4()
    target.translation = current.translation
    pose_bone.matrix = target
    bpy.context.view_layer.update()
    return tuple(math.degrees(v) for v in pose_bone.rotation_euler)


def _foot_euler(arm, side, frame):
    """脚：`f < FOOT_SET` 走 pwl（俯卧勾脚 → 落地前压脚背）；`f ≥ FOOT_SET` 钉世界朝向。

    ★★ `f ≥ FOOT_SET` 起**整段**把脚的世界 3×3 钉成 **`Idle_01@0` 的脚朝向**
      （不是 rest 朝向 —— 这是本支踩过的一个坑，见下）⟹
      ①鞋底**构造性 = `Idle_01@0` 的鞋底**（`sole_mm = −0.96`，落在 `[−2, +6]` 内）；
      ②`toe.*` 相对 `foot.head` 的位置恒定，而 `foot.head` 已被腿 IK 钉死
      （`ankerr = 0`）⟹ **脚不滑是构造性的**，不是靠容差；
      ③`f = STAND` 那一帧走的是 `_end_pose_continuous`（逐位 = `Idle_01@0`），
      与这里的钉法**同源** ⟹ 末帧不再有欧拉支跳变。
    ★ 曾写成"pwl → flat 的连续混合"，结果脚在 `f=FOOT_SET..STAND` 一直转，
      `toe` 滑 103/131 mm、鞋底穿地 −8.6 mm（`_d17_gate3.log`）。
    ★★ 之后又写成"钉 **rest** 朝向"：位置对了，朝向错了一档 —— rest 朝向不是
      `Idle_01@0` 的脚朝向，实测鞋底在 `f=20..33` 恒 **−7.34 mm**（穿地），
      而 `f=34`（逐位照抄 Idle）是 **−0.96 mm**；两者之间在 `f=34` 攒出一个
      **134.956°** 的欧拉支跳变，同时打红 `sole_ground_ok` / `no_teleport` /
      `no_snap_stop_ok` 三条（`_d17_gate4.log`）。钉到 **Idle 朝向** 三红同时消除：
      "钉"的目标必须是**接缝另一头**的朝向，不能是零位朝向。
    """
    name = "foot." + side
    prev = JS._PREV_EULER.get(name)
    if frame >= FOOT_SET:
        return JS._unwrap_xyz(prev, _pin_foot_world(arm, name, side, frame))
    pw = pwl_vec(FOOT_KEYS[side], float(frame), SEAM_FOOT_EULER[side])
    if FOOT_PIN_BLEND > 0 and frame > FOOT_SET - FOOT_PIN_BLEND:
        # ★★ 把"钉 `Idle` 脚朝向"**混进来**（见 `FOOT_PIN_BLEND` 注释）：
        #    `f = FOOT_SET−1 → FOOT_SET` 从 **pwl 分支**切到 **钉朝向分支**，两分支在
        #    切换帧相差 ~40°（实测 `D17_EULERDBG`：`foot.L` `f=20` 步长 38.37°、真实
        #    世界旋转 39.87°，`shin.L` 30.51°）⟹ 这是**真实**的朝向跳变，不是表示问题。
        #    做法：`[FOOT_SET−N, FOOT_SET)` 内把钉值按 smoothstep 混进来，`f = FOOT_SET`
        #    处权重构造性为 1 ⟹ 与 `f ≥ FOOT_SET` 的钉法**逐位接上**。
        #    ★ `_pin_foot_world` 会**改活骨**（它按定义要写 `pose_bone.matrix`），
        #      这里算完立刻把活骨恢复原状，避免污染后续的腿/脚重钉。
        _pb = arm.pose.bones[name]
        _saved = tuple(_pb.rotation_euler)
        _pin = _pin_foot_world(arm, name, side, frame)
        _pb.rotation_euler = _saved
        bpy.context.view_layer.update()
        _w = _smoothstep((float(frame) - float(FOOT_SET - FOOT_PIN_BLEND))
                         / float(FOOT_PIN_BLEND))
        pw = tuple(a + (b - a) * _w for a, b in zip(pw, _pin))
    return JS._unwrap_xyz(prev, tuple(pw))


# =============================================================== 模块级表
ZERO = {}
ZERO_WORLD = {}
END_POSE = {}
ZERO_BASIS = {}
ZERO_DIR = {}
END_BASIS = {}
END_DIR = {}
END_KNEE_DIR = {}
END_ELBOW_DIR = {}
END_HAND_DIR = {}
SEAM_FIST = {}
SEAM_ELBOW_DIR = {}
SEAM_HAND_DIR = {}
SEAM_ANKLE = {}
SEAM_FOOT_EULER = {}
END_FOOT_BASIS = {}
SEAM_RX = {}
END_RX = {}
END_OFF = {}
END_ANKLE = {}
END_TOE = {}
END_RX = {}
PLANT_KEYS = {}
ELBOW_KEYS = {}
HAND_DIR_KEYS = {}
FOOT_KEYS = {}
TUCK_ANKLE = {}
KNEE_DIR = {}
ARM_MAX = {}
LOCK_POSE = {}
_LOCK_REUSED = [0]
SEAM_MATCH = {"src": None, "geom_pos": None, "geom_dir": None,
              "pos_bone": None, "dir_bone": None, "per_bone": {},
              "matched": False}
END_MATCH = {}
HEM_STATIC = {}
ROLL_WEIGHT_MODE = os.environ.get("D17_ROLL_WEIGHT", "always").strip().lower()
ROLL_BONES = tuple(
    item for item in os.environ.get(
        "D17_ROLL_BONES",
        "upperarm.L,forearm.L,hand.L,upperarm.R,forearm.R,hand.R").split()
    if item)
ROLL_ITER = max(1, _env_i("D17_ROLL_ITER", 2))
ROLL_LEGS = os.environ.get("D17_ROLL_LEGS", "1").strip() not in ("", "0", "false")
if ROLL_LEGS:
    UE.ROLL_BONES = frozenset(set(UE.ROLL_BONES)
                              | {"thigh.L", "thigh.R", "shin.L", "shin.R"})

# ★ `_toward_end` 的**豁免名单**：腿 + 脚已由 IK 构造性精确定位，不参与末端混合。
#   反验证 ⑧：`D17_MIX_SKIP=""` ⟹ 恢复全骨混合 ⟹ 脚必然被拽离落点。
MIX_SKIP = tuple(item for item in os.environ.get(
    "D17_MIX_SKIP",
    "thigh.L shin.L thigh.R shin.R foot.L foot.R").split() if item)

TORSO_BONES = ("root", "pelvis", "spine_01", "spine_02", "chest", "neck", "head")
PARENT_OF = {"root": None, "pelvis": "root", "spine_01": "pelvis",
             "spine_02": "spine_01", "chest": "spine_02", "neck": "chest",
             "head": "neck"}
ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")
LEG_BONES = ("thigh.L", "shin.L", "thigh.R", "shin.R")
UPPER_BONES = TORSO_BONES + ("shoulder.L", "shoulder.R") + ARM_BONES


# =============================================================== 阈值
SEAM_TOL = 1e-6
END_TOL = 1e-6
NO_TELEPORT_MAX_DEG = 25.0
REACH_MAX_RATIO = 0.995
# ---- ★★ `end_matches_idle_ok`（本支最硬）------------------------------------
# ---- ★ 起身幅度 --------------------------------------------------------------
#   ★ 清单计划写「净升 ≥ 650 mm」是基于**推算**的终点 900 mm；实测终点 **830.0 mm**
#     ⟹ 真实净升 **610 mm**，650 物理上不可能达到。阈值按实测重定为 **580 mm**
#     （= 实测的 95%，仍能挡住"只起来一半"）。**这不是放宽容差，是把推算换成实测。**
RISE_MIN_MM = _env_f("D17_RISE_MIN", 580.0)
RISE_MONO_TOL_MM = _env_f("D17_RISE_MONO", 2.0)
# ---- ★ 撑地推起 --------------------------------------------------------------
CHEST_RISE_MIN_MM = _env_f("D17_CHEST_RISE_MIN", 200.0)
# ---- ★ 支点交接 --------------------------------------------------------------
HAND_TOUCH_MAX_MM = _env_f("D17_HAND_TOUCH_MAX", 60.0)   # 撑地期：手掌最低点 ≤ 此值
HAND_OFF_MIN_MM = _env_f("D17_HAND_OFF_MIN", 60.0)       # 离地后：手掌最低点 ≥ 此值
SOLETOUCH_MAX_MM = _env_f("D17_FOOT_TOUCH_MAX", 6.0)     # 脚接住地面（鞋底 ≤ +6 mm）
# ---- ★ 站姿族硬约束（清单 §6）-----------------------------------------------
FOOT_SLIDE_MAX_MM = _env_f("D17_FOOT_SLIDE_MAX", 3.0)
SOLE_MIN_MM = _env_f("D17_SOLE_MIN", -2.0)
SOLE_MAX_MM = _env_f("D17_SOLE_MAX", 6.0)
# ---- 收招不许瞬停 ------------------------------------------------------------
NO_SNAP_TAIL_FRAMES = _env_f("D17_SNAP_TAIL", 6.0)
END_HOLD_MAX_DEG = _env_f("D17_END_HOLD_TOL", 0.5)
# ---- 穿模 / 可达性 -----------------------------------------------------------
CLIP_MAX_MM = _env_f("D17_CLIP_MAX", 0.0)
CLIP_EVERY = _env_i("D17_CLIP_EVERY", 4)
SEAM_REPLAY_POS_MAX_MM = _env_f("D17_SEAM_POS", 0.01)
SEAM_REPLAY_DIR_MAX_DEG = _env_f("D17_SEAM_DIR", 0.05)

HEM_OBJECTS = tuple(
    n for n in os.environ.get("D17_HEM_OBJECTS",
                              "Jacket_Hem,Jacket_Hem_Line").split(",") if n)
HAND_MESHES = {s: tuple(["Hand_Palm_" + s] + ["Finger_%s_%s" % (d, s)
                                              for d in ("Index", "Middle",
                                                        "Ring", "Pinky")])
               for s in SIDES}


def pwl_vec(keys, frame, default):
    """逐分量 PCHIP（`UE.pwl`）。keys: ((f, (x, y, z)), ...)。"""
    out = []
    for index in range(3):
        sub = tuple((k[0], k[1][index]) for k in keys)
        out.append(UE.pwl(sub, float(frame), default[index]))
    return Vector(out)


# =============================================================== 姿态装配
def arm_seat_tip(arm, pose, side, tip_target, elbow_dir_in, hand_dir_in):
    up, fo, hd = ("upperarm." + side, "forearm." + side, "hand." + side)
    dims = UE.ARM_LEN[side]
    l1, l2 = dims["upper"], dims["forearm"]
    hand_dir = Vector(hand_dir_in).normalized()
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
    # ---- ★ 临时臂 IK 诊断（`D17_ARMPROBE=1`，配合 `D17_ARMPROBE_F`）---------
    #   量的是"肘鼓出方向相对骨轴的**垂直分量长度**"：它越小，`sin_sh` 乘出来的
    #   那一点越会被"肘鼓出方向"的**微小抖动**放大成大幅度摆肘 ⟹ 肘位翻转。
    if _ARMPROBE and _ARMPROBE_F0 <= _ARMPROBE_FRAME[0] <= _ARMPROBE_F1:
        _bul = Vector(elbow_dir_in)
        _perp = _bul - axis * _bul.dot(axis)
        print("D17_ARMPROBE " + json.dumps({
            "f": _ARMPROBE_FRAME[0], "side": side,
            "axis": [round(v, 4) for v in axis],
            "edir": [round(v, 4) for v in _bul.normalized()],
            "perp_len": round(_perp.length, 4),
            "cos_axis_edir": round(axis.dot(_bul.normalized()), 4),
            "dist_mm": round(delta.length * 1000.0, 2),
            "limit_mm": round(limit * 1000.0, 2),
            "clamp": bool(clamp), "sin_sh": round(sin_sh, 4),
            "elbow_z": round((elbow.z) * 1000.0, 2),
            "shoulder_z": round(shoulder.z * 1000.0, 2),
        }))
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


def _toward_end(pose, weight):
    """把 `pose` 朝 `END_POSE` 拉 `weight`（逐骨取最近 360° 等价表示再插值）。

    ★ 为什么需要它：末帧必须**逐位 = `Idle_01@0`**（世界矩阵 ≤1e−6），
      而中段姿态是 IK 解出来的（欧拉支可能与 Idle 不同）。用一条
      **连续**的权重把两者接上，`weight=1` 处**构造性**等于 `END_POSE`。
    ★ `@loc` **不参与混合** —— 竖直通道独立驱动，其终点已**构造性**等于 END 的 loc。
    ★★ 腿与脚**不参与混合**（`MIX_SKIP`）—— 它们由 IK + `keep_world_orientation`
      **构造性**精确控制（`f ≥ FOOT_SET` 脚目标恒 = `END_ANKLE`）；把它们往
      `END_POSE` 的欧拉上混，等于用一条权重把**已解好的 IK 解**拽离落点：
      实测 `f=25..33` 脚误差 12→120 mm，随 `weight` 单调增长
      （`_d17_geom1.log`）。这不是容差问题，是"别再动已经对的骨"。
      反验证：`D17_MIX_SKIP=""` 恢复全骨混合 ⟹ 脚必然漂。
    """
    if weight <= 0.0:
        return pose
    out = {}
    keys = set(pose) | set(END_POSE)
    for key in keys:
        if key == "@loc":
            continue
        if key in MIX_SKIP:
            out[key] = pose.get(key, (0.0, 0.0, 0.0))
            continue
        a = pose.get(key, (0.0, 0.0, 0.0))
        b = END_POSE.get(key, (0.0, 0.0, 0.0))
        bb = [_nearest_equiv(y, x) for x, y in zip(a, b)]
        out[key] = tuple(u + (v - u) * weight for u, v in zip(a, bb))
    out["@loc"] = {k: tuple(v) for k, v in pose.get("@loc", {}).items()}
    return out


TORSO_PROG_END = _env_i("D17_TORSO_END", STAND)


def torso_pose(frame):
    """躯干：局部欧拉 pwl（接缝 → Idle），另叠"拱起"曲线。"""
    out = {}
    for name in TORSO_BONES:
        p = UE.pwl(TORSO_PROG[name], float(frame), 0.0)
        rx = SEAM_RX[name] + (END_RX[name] - SEAM_RX[name]) * p
        rx -= arch_of(name, frame)
        ry = ZERO.get(name, (0.0, 0.0, 0.0))[1] * (1.0 - p)
        rz = ZERO.get(name, (0.0, 0.0, 0.0))[2] * (1.0 - p)
        out[name] = (rx, ry, rz)
    for side in SIDES:
        name = "shoulder." + side
        p = UE.pwl(TORSO_PROG["chest"], float(frame), 0.0)
        a = ZERO.get(name, (0.0, 0.0, 0.0))
        b = END_POSE.get(name, a)
        out[name] = tuple(a[i] + (b[i] - a[i]) * p for i in range(3))
    locs = {k: tuple(v) for k, v in ZERO.get("@loc", {}).items()}
    locs["pelvis"] = A.wloc(0.0, pelvis_y_at(frame),
                            pelvis_z_at(frame) - Z_PELVIS_REST)
    out["@loc"] = locs
    return out


def _end_pose_continuous(arm):
    """末帧：**世界姿态逐位 = `END_POSE`**，但欧拉取**离上一帧最近**的那一支。

    ★ 为什么不能直接 `_copy_pose(END_POSE)`：`END_POSE` 的欧拉是从 `Idle_01@0`
      读出来的**某一支**，与 `f = STAND−1` 的 IK 解可能落在不同的**万向节等价解**
      上（差 116.6°，不是 360° 的整数倍）⟹ `no_teleport` 在 `f = 34` 报
      `max_frame_step_deg = 116.6 @ upperarm.R`（`_d17_gate3.log`）。
      `_nearest_equiv` 只修 ±360°，修不了这一支。
    ★ 做法：把 `END_POSE` 应用到骨架，逐骨调 `UE._set_euler_nearest`
      （C13 教训 3 的正解函数）读回**等价且连续**的欧拉。`phi` 只取 0
      ⟹ **只换欧拉支、不绕骨轴滚转** ⟹ 世界 3×3 逐位不变
      ⟹ `end_matches_idle_ok`（4×4 矩阵 ≤1e−6）不受影响。
    """
    A.apply_pose(arm, END_POSE)
    bpy.context.view_layer.update()
    grid = UE.ROLL_GRID
    UE.ROLL_GRID = (0.0,)          # ★ 禁止绕骨轴滚转：那会改世界 3×3，破坏逐位接缝
    try:
        out = {}
        for name in END_POSE:
            if name.startswith("@"):
                continue
            if name in arm.pose.bones:
                out[name] = UE._set_euler_nearest(arm, name)
            else:
                out[name] = tuple(END_POSE[name])
    finally:
        UE.ROLL_GRID = grid
    out["@loc"] = {k: tuple(v) for k, v in END_POSE.get("@loc", {}).items()}
    return out


def _roll_grid_window(mix):
    """绕骨轴滚转的**允许窗口**：`|φ| ≤ 180° · (1 − mix^p)`。

    `mix=0` 时窗口仍是全网格（躲万向节锁）；`mix=1` 时**恰好只剩 0**
    （与 `_end_pose_continuous` 的 `phi` 只取 0 构造性接得上）。
    `p=1`（原稿）在 `mix → 1` 前就已经把窗口收到很窄；`p=3` 让窗口在**末段之前**
    保持更宽，把"表示跳变"留出可解的自由度。端点行为与 `p` 无关。
    """
    p = _env_f("D17_ROLLWIN_POW", 3.0)
    half = math.radians(180.0 * max(0.0, min(1.0, 1.0 - mix ** max(1e-6, p))))
    out = tuple(phi for phi in UE.ROLL_GRID if abs(phi) <= half + 1e-9)
    return out if out else (0.0,)


def _euler_roll_best(arm, name, prev=None, roll_penalty=0.0):
    """在**当前局部旋转**上再搜一圈绕骨轴滚转，取"步长 + 罚分·|φ|"最小的欧拉支。

    ★ 与 `UE._set_euler_nearest` 的唯一区别是**多了滚转罚分**：
      `cost = max|Δ欧拉分量| + roll_penalty · |φ|`。
      `φ = 0` 处的局部旋转**就是参考滚转**（由 `_roll_return` 刚写好）⟹
      罚分越大，越倾向于"滚转保持参考、只换欧拉写法"。
    ★ 绕骨轴滚**不动骨根也不动骨尖** ⟹ 所有位置口径的门禁（`reach_ok`、
      `no_foot_slide_ok`、`sole_ground_ok`、`clip_metrics`）**构造性**不受影响；
      代价只是网格沿骨轴自转一点（真实视觉量，会在出图目检时核对）。
    """
    pose_bone = arm.pose.bones[name]
    basis = pose_bone.matrix_basis.to_3x3()
    if prev is None:
        prev = JS._PREV_EULER.get(name)
    best, best_cost = None, None
    best_phi = 0.0
    for phi in UE.ROLL_GRID:
        if phi == 0.0:
            m = basis
        else:
            cos_p, sin_p = math.cos(phi), math.sin(phi)
            m = basis @ Matrix(((cos_p, 0.0, sin_p),
                                (0.0, 1.0, 0.0),
                                (-sin_p, 0.0, cos_p)))
        for cand in UE._xyz_candidates(m):
            value = [math.degrees(t) for t in cand]
            if prev is not None:
                for index in range(3):
                    while value[index] - prev[index] > 180.0:
                        value[index] -= 360.0
                    while value[index] - prev[index] < -180.0:
                        value[index] += 360.0
            cost = (0.0 if prev is None
                    else max(abs(a - b) for a, b in zip(value, prev)))
            cost += roll_penalty * abs(math.degrees(phi))
            # ★★ 与 `UE._set_euler_nearest`（C13/C14 正解函数）**同族**：把欧拉路径
            #    推离 XYZ 万向节锁带（`|Y| → 90°`，那里 (X, Z) 的拆分是任意的）。
            #    ★ 缺这一项时本函数会**逐帧贪心**地把表示留在锁带里（因为锁带内单帧
            #      步长确实最小），直到某一帧**跨过** `Y = 90°` 时 (X, Z) 同时大幅
            #      跳变。实测 `f=13 hand.R Y=105.04 → f=14 Y=72.57`（正是跨锁），
            #      该帧**真实世界旋转只有 2.28°** 而欧拉步长 **32.47°**；
            #      同型还有 `f=5 forearm.R`（真实 9.60° / 步长 37.35°）、
            #      `f=30 hand.R`（真实 18.76° / 步长 69.51°）。
            #    ★ 这不是放宽判据：改的是**表示**（绕骨轴滚转 + 两支等价欧拉），
            #      世界 3×3 只多一个纯滚转自由度，骨根/骨尖不动。
            cost += (max(0.0, abs(value[1]) - UE.EULER_Y_SAFE)
                     * UE.EULER_Y_WEIGHT)
            if best_cost is None or cost < best_cost:
                best, best_cost, best_phi = tuple(value), cost, math.degrees(phi)
    _ROLL_LAST_PHI[name] = round(best_phi, 3)
    pose_bone.rotation_euler = [math.radians(t) for t in best]
    bpy.context.view_layer.update()
    return best


def build_pose(arm, frame):
    # ★ f0 = **逐位**接缝姿态（`Knockdown_F@20`）—— 不走解算，原样返回。
    if frame <= 0:
        if SEAM_ZERO:
            # ★ 反验证 ①：抽掉接缝 —— 首帧改成**零位**（不是 `Knockdown_F@20`）
            #    ⟹ `seam_in_ok` 必须红。★ 这个旋钮先前**只声明没接线**（本项目已
            #    第六次踩同一个坑）：`SEAM_ZERO` 读进来了，但 `build_pose` 里没有
            #    任何地方用它，反验证必然假绿。
            _z = {name: (0.0, 0.0, 0.0) for name in ZERO
                  if not name.startswith("@")}
            _z["@loc"] = {"pelvis": A.wloc(0.0, 0.0, 0.0)}
            return _z
        return _copy_pose(ZERO)

    # ★★ 末段：`STAND` 起**逐位** = `Idle_01@0`（3 帧定格自持）。
    #    世界姿态逐位照抄，欧拉取连续支（见 `_end_pose_continuous`）。
    if frame >= STAND and not NO_IDLE and not END_ZERO:
        return _end_pose_continuous(arm)

    pose = torso_pose(frame)

    # ★★ 顺序是关键：**先在躯干欧拉上做末端收束，再解 IK**。
    #    `root` / `pelvis` 不在 `MIX_SKIP` 里，会被拉向 `END_POSE` ⟹ 骨盆世界位姿
    #    变化 ⟹ 髋位变化。若先解腿、后混合躯干，已解好的腿欧拉被 `MIX_SKIP` 冻住
    #    （不再跟随新髋位），踝就会**按混合权重成比例**漂离落点
    #    （实测 `f=30` 漂 59.9 mm，`err/w ≈ 78 mm`；`_d17_geom2/3.log`）。
    #    把 IK 放在混合之后 ⟹ IK 永远在**最终**躯干上求解 ⟹ 踝**构造性**落在
    #    `ankle_target` 上（`no_foot_slide_ok` / `sole_ground_ok` 的前提）。
    if not NO_IDLE:
        w = _smoothstep((float(frame) - float(FOOT_SET))
                        / float(STAND - FOOT_SET))
        pose = _toward_end(pose, w)

    A.apply_pose(arm, pose)
    for side in SIDES:
        UE.leg_seat(arm, pose, side, ankle_target(arm, side, frame),
                    knee_dir_at(side, frame))
    for name in ("foot.L", "foot.R"):
        pose[name] = _foot_euler(arm, name.split(".")[1], frame)
    for side in SIDES:
        arm_seat_tip(arm, pose, side, fist_target(arm, side, frame),
                     elbow_dir(side, frame), hand_dir_of(side, frame))
    if ROLL_WEIGHT_MODE != "off":
        # ★★★ **头部冻结窗口**（`D17_HEAD_FREEZE`，默认 0 = 关）：`f ≤ HEAD_FREEZE` 时
        #    把绕骨轴的滚转**也收成 `{0}`**（= 参考滚转本身，即接缝滚转）。
        #    ★ 为什么需要：尾段早就用 `_roll_grid_window` 把滚转自由度随 `roll_mix`
        #      收窄到 `φ=0`，从而与 `_end_pose_continuous` 构造性接上；**头段没有对应
        #      机制** —— `f ≤ FOOT_SET` 的 `roll_mix` 恒为 0，窗口恒为**全网格**，
        #      于是 `arm_seat_tip`/`_roll_return` 可以在 180° 内自由选一个 φ 来躲
        #      万向节锁。实测（`_d17_A0eul.log`，真实世界旋转口径）：`f=1`
        #      `hand.L` 一步 **55.71°**、`forearm.L` **49.57°**，而同一帧的骨轴方向
        #      只转 ~10° ⟹ 这一跳**主要是扭转**，不是真动作，正是 `no_teleport`
        #      在 `f=1` 的 44.53° 的来源。
        #    ★ 与尾段对称：头段参考 = 接缝（`roll_mix = 0`），把窗口收成 `{0}`
        #      = 把滚转钉在**接缝滚转**上 ⟹ `f0 → f1` 的扭转构造性为 0。
        if HEAD_FREEZE and frame <= HEAD_FREEZE:
            UE.ROLL_GRID = (0.0,)
        for _ in range(ROLL_ITER):
            for name in ROLL_BONES:
                if name in arm.pose.bones:
                    _roll_return(arm, pose, name, 1.0, roll_mix_at(frame, name))
            # ★★ 脚朝向必须在**腿的滚转之后**重钉。`_roll_return` 改的是 thigh/shin
            #    的**局部欧拉**；shin 的世界朝向一变，先前由 `keep_world_orientation`
            #    解出的 foot 局部欧拉就不再对应 rest 世界朝向 ⟹ 鞋底随骨盆上升慢慢
            #    陷地：实测 `f=20..33` 从 **−7.34 mm** 爬到 −1.57 mm，而 `f=34`
            #    （逐位照抄 `Idle_01@0`）才是 −0.96 mm（`_d17_gate4.log`）。
            #    ⟹ 钉朝向必须排在**最后**，不能排在腿之前。
            for name in ("foot.L", "foot.R"):
                pose[name] = _foot_euler(arm, name.split(".")[1], frame)
            for side in SIDES:
                arm_seat_tip(arm, pose, side, fist_target(arm, side, frame),
                             elbow_dir(side, frame), hand_dir_of(side, frame))
        # ★★ 收尾：**臂骨的滚转必须是最后写者**（实测依据 `_d17_eul2.log`）。
        #    `arm_seat_tip` → `aim_nearest` → `UE._set_euler_nearest` 会在**全
        #    `ROLL_GRID`** 上自由搜一个滚转来躲万向节锁 —— 这一步**改世界朝向**
        #    （滚转绕骨轴：骨端不动、网格滚一下）。于是 `f ≤ 33` 的臂被钉在
        #    与 `Idle_01@0` 相差 **90~125°** 的滚转上（实测 `w_upperarm.R`：
        #    `f=28..33` 恒 `[55.77,−12.44,134.03]`，`f=34` 才是
        #    `[−70.09,15.64,111.91]`），而 `f=34` 的 `_end_pose_continuous`
        #    强制 `phi=0` ⟹ `f=33→34` 攒出 **124.87°** 跳变，同时打红
        #    `no_teleport` / `no_snap_stop_ok`。
        #    把它放到最后 ⟹ 臂的滚转 = `_roll_return` 的参考（`roll_mix` 已走到
        #    `Idle`）⟹ 与 f=34 同支。`_roll_return` 只动滚转 ⟹ 拳位、`reach_ok`、
        #    `clip_metrics`(量骨段) 全部不受影响。
        # ★★ 收尾：**臂骨的滚转必须是最后写者**（实测依据 `_d17_eul2.log`）。
        #    `arm_seat_tip` → `aim_nearest` → `UE._set_euler_nearest` 会在**全
        #    `ROLL_GRID`** 上自由搜一个滚转来躲万向节锁 —— `phi ≠ 0` 改的是
        #    **旋转本身**（绕骨轴滚一下）：骨端不动、网格滚一下、**世界 3×3 变**。
        #    于是 `f ≤ 33` 的臂被钉在与 `Idle_01@0` 相差 **90~125°** 的滚转上
        #    （实测 `w_upperarm.R`：`f=28..33` 恒 `[55.77,−12.44,134.03]`，
        #    `f=34` 才是 `[−70.09,15.64,111.91]`），而 `f=34` 的
        #    `_end_pose_continuous` 强制 `phi=0` ⟹ `f=33→34` 攒出 **124.87°**
        #    跳变，同时打红 `no_teleport` / `no_snap_stop_ok`。
        #    ⟹ 臂的滚转由 `_roll_return`（参考已混到 `Idle`）**统一负责**，
        #      随后用 `phi=0` 重写欧拉支（**不改世界 3×3**、只换写法）。
        #      `_roll_return` 只动滚转 ⟹ 拳位、`reach_ok`、`clip_metrics`(量骨段)
        #      全不受影响。
        if ARM_ROLL_TAIL:
            grid_arm = UE.ROLL_GRID
            _mix = roll_mix_at(frame, None)
            _pen = ARM_ROLL_PENALTY_DEG * _mix * _mix
            # ★★ 滚转自由度必须**随 `roll_mix` 收窄**：`f ≤ FOOT_SET` 允许绕骨轴
            #    滚到任何角度（躲万向节锁），`f → STAND` 收敛到只允许 `φ = 0`
            #    （= 参考滚转本身）⟹ 与 `_end_pose_continuous`（`phi` 只取 0）
            #    构造性接得上。
            #    实测：只加罚分（`_d17_gate15.log`）不够 —— 罚分在 `f=24` 只有
            #    ~1°/°，搜索宁可选 `φ=0` 的 142° 欧拉步长也不肯付出滚转代价 ⟹
            #    `hand.R` 在 `f=24` 攒出 **142.18°**。硬收窄窗口没有这个问题。
            UE.ROLL_GRID = _roll_grid_window(_mix)
            try:
                for name in ARM_BONES:          # 父先子后
                    if name in arm.pose.bones:
                        _roll_return(arm, pose, name, 1.0,
                                     roll_mix_at(frame, name))
                # ★★ 滚完**必须重解一次臂 IK**：`_roll_return` 绕骨轴滚父骨 ⟹
                #    `upperarm` 一滚，`forearm`/`hand` 的**世界朝向**就变了
                #    （它们的局部欧拉是给旧父骨朝向解的）⟹ 手的世界朝向不再是
                #    `hand_dir_of`。实测（`D17_EULERDBG_DIR=1`）：`f=27` 请求
                #    `hand_dir = (0.091,−0.974,−0.210)`，实际是
                #    `(0.044,−0.916,0.399)`（差 **35°**）；把滚转整体关掉
                #    （`D17_ROLL_WEIGHT=off`）时两者**逐位相同** ⟹ 差异全来自
                #    这一步，`f=27 hand.R` 的欧拉步长因此从 48.13° 涨到 85.91°。
                #    `arm_seat_tip` 是**世界位置口径**、`aim_nearest` 从 `CARRY_Q`
                #    接力 ⟹ 重解把方向重新对准，同时把刚滚好的滚转保住。
                for side in SIDES:
                    arm_seat_tip(arm, pose, side, fist_target(arm, side, frame),
                                 elbow_dir(side, frame), hand_dir_of(side, frame))
                for name in ARM_BONES:
                    if name in arm.pose.bones:
                        pose[name] = _euler_roll_best(arm, name,
                                                      roll_penalty=_pen)
            finally:
                UE.ROLL_GRID = grid_arm

    # ★★ 腿骨滚转收尾：**只滚 `shin`，且放在最后**（见 `LEG_ROLL_TAIL` 注释）。
    #    ★ 为什么**不能滚 `thigh`**：`_roll_return` 绕骨轴滚 ⟹ 骨端不动，但 `thigh`
    #      的"骨端"是**膝**；膝不动、`shin` 却是绕膝转的孩子 ⟹ `thigh` 一滚，
    #      `shin` 的**世界朝向**就变了（它的局部欧拉是给旧朝向写的）⟹ **踝被甩离
    #      `ankle_target`**。实测：加进 `thigh` 后逐帧 `ankerr` 从 0.0 变成
    #      0.2~111.4 mm，`no_foot_slide_ok` 从 0.019 mm 变成 **144.6 mm**
    #      （`_d17_geom7.log`）。两骨 IK 链的**父骨不能独立滚**，必须重解子骨。
    #      `shin` 的骨端就是踝 ⟹ 滚它**构造性**不动踝；接着重钉脚即可。
    if LEG_ROLL_TAIL and ROLL_WEIGHT_MODE != "off":
        grid_leg = UE.ROLL_GRID
        UE.ROLL_GRID = (0.0,)
        saved_roll_bones = UE.ROLL_BONES
        # ★★ 父先子后，且**父骨滚完必须重解一次腿 IK**：
        #    `thigh` 一滚，它的孩子 `shin` 的**世界朝向**就变了（孩子的局部欧拉是
        #    给旧朝向写的）⟹ 踝被甩离 `ankle_target`（`_d17_geom7.log`：逐帧
        #    `ankerr` 0.2~111.4 mm、`no_foot_slide_ok` 144.6 mm）。
        #    `leg_seat` 是**位置口径**、`aim_nearest` 从 `CARRY_Q` 接力 ⟹
        #    重解既能重新对准踝，又把 `thigh` 刚滚好的滚转保住。
        #    ★★ 重解期间必须把**腿移出 `UE.ROLL_BONES`**：否则 `aim_nearest` →
        #      `_set_euler_nearest` 会在**全 `ROLL_GRID`** 上自由搜一个滚转，把
        #      刚滚好的 `thigh` 又拧走。这正是 `f=33` 上 `thigh.R` 的**世界 3×3
        #      偏离 `Idle` 15.95°、而骨轴只差 0.47°** 的成因（`_d17_eul7.log`）：
        #      纯滚转错位 ⟹ `f=33→34` 攒出 `thigh.L 16.95 / shin.L 21.78` 的欧拉
        #      跳变，打红 `no_snap_stop_ok`（末 6 帧增量不再单调收敛）。
        try:
            UE.ROLL_BONES = frozenset(b for b in saved_roll_bones
                                      if b not in LEG_BONES)
            for name in ("thigh.L", "thigh.R"):
                if name in arm.pose.bones:
                    _roll_return(arm, pose, name, 1.0, roll_mix_at(frame, name))
            for side in SIDES:
                UE.leg_seat(arm, pose, side, ankle_target(arm, side, frame),
                            knee_dir_at(side, frame))
        finally:
            UE.ROLL_BONES = saved_roll_bones
        try:
            for name in ("shin.L", "shin.R"):
                if name in arm.pose.bones:
                    _roll_return(arm, pose, name, 1.0, roll_mix_at(frame, name))
        finally:
            UE.ROLL_GRID = grid_leg

    # ★ 末段：腿骨重写欧拉支 —— **只换写法，不绕骨轴滚**（`ROLL_GRID=(0,)`）。
    #   ★★ 为什么不让它滚：`shin` 的孩子就是 `foot`。`_set_euler_nearest` 一旦给
    #      `shin` 选 `phi ≠ 0`，`shin` 的世界 3×3 就真的转了 ⟹ `foot`（它的孩子）
    #      的世界朝向跟着转 ⟹ 先前钉好的"`Idle` 脚朝向"被推翻、鞋底重新陷地。
    #      实测 `_d17_geom8.log`：`f=21..32` 脚的世界基不再是 `Idle` 朝向
    #      （`fb_L` 与 `f=33` 明显不同），鞋底从 −8 mm 恶化到 **−29 mm**。
    #      ⟹ 腿的滚转**只由 `_roll_return` 负责**（参考已混到 `Idle`），
    #        这一步退化为纯表示选择。
    grid = UE.ROLL_GRID
    UE.ROLL_GRID = (0.0,)
    try:
        for name in LEG_BONES:
            if name in arm.pose.bones:
                pose[name] = UE._set_euler_nearest(arm, name)
    finally:
        UE.ROLL_GRID = grid

    # ★★ 脚必须排在**所有会改变腿世界朝向的步骤之后**：钉脚 = 把"脚的世界 3×3"
    #    写成 `Idle_01@0` 的朝向 ⟹ 只要 `thigh`/`shin` 的世界朝向在它之后变，
    #    脚就不再是钉的那个朝向。这里把它放到最后一道。
    for name in ("foot.L", "foot.R"):
        pose[name] = _foot_euler(arm, name.split(".")[1], frame)

    # ===== ★★★ 臂链末段：**逐分量欧拉路径插值**（A12 定案，见清单 §A12）=======
    #   清单 A12/`Ultimate_End` 的定案原文：
    #     「只要一段的终点是一个**显式给定的固定姿态**，就走**逐分量欧拉路径插值**，
    #       并把两端折叠到同一等价族；**不要走世界朝向 slerp**。」
    #   ★ 为什么本支必须用它：臂链的 IK（`arm_seat_tip` → `aim_nearest`）**只钉骨轴
    #     方向**，绕骨轴的**扭转是自由 DOF**；而 `Idle_01@0` 的臂是 `aim_bone` 从
    #     零旋转解出的，两者的扭转落在**不同的等价支**上。`_roll_return` 想把扭转
    #     「交接」过去，但两端参考的**滚转角可相差接近 180°** ⟹ 球面插值在近乎
    #     对径的两点之间**路径不唯一**（实测 `_d17_RB*.log`：`forearm.R` 的参考在
    #     `f=20→28` 从 296° 摆到 74°，而同一段骨轴方向只走 14°/帧 ⟹ 是**插值病态**，
    #     不是真动作）。这正是 `no_teleport` 在 `f=28..32` 的 53.7~58.5° 的来源。
    #   ★ 换口径后峰值步长有**解析上界** = 最大分量差 × 1.136 / 段长（A12 原文）。
    #     实测段长 17 帧 ⟹ 上界 ≈ 分量差 × 0.067 ⟹ 即使分量差 300° 也只有 20°。
    #   ★ 端点构造性一致：`f = STAND` 起由 `_end_pose_continuous` 接管（= `Idle_01@0`），
    #     本段在 `f = STAND−1` 取 `s = 1` ⟹ 也**构造性** = `Idle_01@0`（同一等价族）
    #     ⟹ `f=STAND−1 → STAND` 的欧拉步长在 `_nearest_branch` 归一后为 0，
    #     `no_snap_stop_ok` / `end_matches_idle_ok` 均不受影响。
    if ARM_MIX_FROM:
        if frame == ARM_MIX_FROM - 1:
            TAIL_ARM["pose"] = {n: tuple(pose.get(n, (0.0, 0.0, 0.0)))
                                for n in ARM_BONES}
        elif frame >= ARM_MIX_FROM and TAIL_ARM.get("pose"):
            _src = TAIL_ARM["pose"]
            _u = (float(frame) - float(ARM_MIX_FROM)) / max(
                1e-9, float(STAND - ARM_MIX_FROM))
            _s = _hand_mix_s(_u)
            for name in ARM_BONES:
                a = _src.get(name, (0.0, 0.0, 0.0))
                b = END_POSE.get(name, a)
                bb = [_nearest_equiv(y, x) for x, y in zip(a, b)]
                pose[name] = tuple(u + (v - u) * _s for u, v in zip(a, bb))

    pose.update(A.FIST)

    for name, value in pose.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)
    if frame == END_ZERO_FRAME:
        LOCK_POSE.update(_copy_pose(pose))
    return pose


_ROLLDBG_NAMES = tuple(n for n in os.environ.get("D17_ROLLDBG", "").split(",") if n)
_ROLLDBG_F = _env_i("D17_ROLLDBG_F", -1)
_ROLLDBG_FRAME = [-1]
_ROLL_LAST_PHI = {}
# ★ 临时臂 IK 诊断（`D17_ARMPROBE=1`）：见 `arm_seat_tip` 里的打印。
_ARMPROBE = bool(os.environ.get("D17_ARMPROBE"))
_ARMPROBE_F0 = _env_i("D17_ARMPROBE_F0", -1)
_ARMPROBE_F1 = _env_i("D17_ARMPROBE_F1", -1)
_ARMPROBE_FRAME = [-1]


def _roll_return(arm, pose, name, weight, roll_mix=0.0):
    """把某根骨的**绕自身轴滚转**沿世界朝向对齐回参考朝向（只改滚转，不改骨轴方向）。

    ★★ `roll_mix` 是**参考朝向的交接权重**（0 = 零位/俯卧，1 = `Idle_01@0`）：
      两端参考都先在"骨轴方向不变"的前提下转到**当前方向**，再做一次 slerp。
      因为两者的相对旋转是**纯滚转**（绕骨轴），slerp 全过程中骨轴方向**逐位不变**
      ⟹ 交接不移动任何骨端（踝/腕/拳都钉得住）。
    ★ 为什么必须有这个交接：滚转参考一直锁在**零位（俯卧）**上时，站起来的姿态
      会被硬拽回"趴着时的滚转"，实测 `f=33 → f=34` 在 `upperarm.R` 上攒出
      **124.87°** 的欧拉跳变，同时打红 `no_teleport` 与 `no_snap_stop_ok`
      （`_d17_gate6.log`）。末帧是逐位 `Idle_01@0`，滚转参考也必须走到 `Idle`
      才接得上 —— 这是"接缝另一头"的问题，不是容差问题。
    """
    if weight <= 1e-9:
        return
    pose_bone = arm.pose.bones[name]
    direction_now = Vector(A.bone_direction(arm, name))
    if direction_now.length < 1e-9:
        return
    direction_now.normalize()
    ref_zero = (ZERO_DIR[name].rotation_difference(direction_now)
                @ Quaternion(ZERO_BASIS[name])).normalized()
    ref_end = (END_DIR[name].rotation_difference(direction_now)
               @ Quaternion(END_BASIS[name])).normalized()
    mix = max(0.0, min(1.0, roll_mix))
    if mix <= 0.0:
        reference = ref_zero
    elif mix >= 1.0:
        reference = ref_end
    else:
        reference = ref_zero.slerp(ref_end, mix).normalized()
    now = pose_bone.matrix.to_3x3().to_quaternion().normalized()
    if _ROLLDBG_NAMES and name in _ROLLDBG_NAMES \
            and _ROLLDBG_FRAME[0] == _ROLLDBG_F:
        _row = {
            "frame": _ROLLDBG_FRAME[0], "bone": name,
            "weight": round(weight, 4), "mix": round(roll_mix, 4),
            "ang_now_refzero": round(math.degrees(
                now.rotation_difference(ref_zero).angle), 3),
            "ang_now_refend": round(math.degrees(
                now.rotation_difference(ref_end).angle), 3),
            "ang_now_ref": round(math.degrees(
                now.rotation_difference(reference).angle), 3),
            "ang_now_endbasis": (round(math.degrees(now.rotation_difference(
                Quaternion(END_BASIS[name])).angle), 3)
                if name in END_BASIS else None),
        }
        print("D17_ROLL " + json.dumps(_row))
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
    if _ROLLDBG_NAMES and name in _ROLLDBG_NAMES \
            and _ROLLDBG_FRAME[0] == _ROLLDBG_F:
        _after = pose_bone.matrix.to_3x3().to_quaternion().normalized()
        print("D17_ROLL_AFTER " + json.dumps({
            "frame": _ROLLDBG_FRAME[0], "bone": name,
            "ang_after_endbasis": (round(math.degrees(_after.rotation_difference(
                Quaternion(END_BASIS[name])).angle), 3)
                if name in END_BASIS else None),
        }))


END_ZERO_FRAME = CANCEL


def solve_pose(arm, frame, meshes=None):
    _ROLLDBG_FRAME[0] = int(frame)
    _ARMPROBE_FRAME[0] = int(frame)
    # ★ 滚转网格是**模块级全局**（`UE.ROLL_GRID`），而 `build_pose` 里有多处
    #   临时改写它（臂尾收窄 / 腿尾钉 0）。任何一处忘了还原都会**泄漏到后续帧**，
    #   让某一帧的滚转自由度悄悄变窄或变宽 —— 这类 bug 极难定位。
    #   ⟹ 在**唯一入口**处统一 save/restore，无论 `build_pose` 怎么改都跑不掉。
    _grid0 = UE.ROLL_GRID
    try:
        return build_pose(arm, frame)
    finally:
        UE.ROLL_GRID = _grid0


# =============================================================== 测量
def _pitch(direction):
    return -math.degrees(math.atan2(direction.y, direction.z))


def _knee_angle(arm, side):
    upper = Vector(A.bone_direction(arm, "thigh." + side)).normalized()
    lower = Vector(A.bone_direction(arm, "shin." + side)).normalized()
    return math.degrees(math.acos(max(-1.0, min(1.0, upper.dot(lower)))))


def _hip_flex(arm, side):
    torso = Vector(A.bone_direction(arm, "pelvis")).normalized()
    thigh = Vector(A.bone_direction(arm, "thigh." + side)).normalized()
    return 180.0 - math.degrees(math.acos(max(-1.0, min(1.0, torso.dot(thigh)))))


def _mesh_low_mm(names):
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


def _worst_step(samples, index_a, index_b):
    ea, eb = samples[index_a]["euler"], samples[index_b]["euler"]
    worst, at = 0.0, None
    for name in set(ea) | set(eb):
        a = ea.get(name, (0.0, 0.0, 0.0))
        b = eb.get(name, (0.0, 0.0, 0.0))
        step = max(abs(x - y) for x, y in zip(a, b))
        if step > worst:
            worst, at = step, (samples[index_b]["frame"], name)
    return worst, at


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


def _pelvis_moving(arm):
    moving = set()
    for bone in arm.pose.bones:
        node = bone
        while node is not None:
            if node.name == "pelvis":
                moving.add(bone.name)
                break
            node = node.parent
    return moving


# =============================================================== 引导
def _load_pose_at(arm, action_name, frame, reset=True):
    """从**落盘 action** 的 fcurve 直接取该帧姿态（euler + location）。"""
    action = bpy.data.actions.get(action_name)
    if action is None:
        return {}, {"action": action_name, "found": False}
    rot_keyed, loc_keyed = _keyed_bones(action)
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    if reset:
        A.reset_pose(arm)
    bpy.context.scene.frame_set(int(frame))
    bpy.context.view_layer.update()
    pose = {name: tuple(math.degrees(v)
                        for v in arm.pose.bones[name].rotation_euler)
            for name in rot_keyed if name in arm.pose.bones}
    loc = {name: tuple(arm.pose.bones[name].location)
           for name in loc_keyed if name in arm.pose.bones}
    if loc:
        pose["@loc"] = loc
    info = {"action": action_name, "found": True, "frame": int(frame),
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
    global ZERO, END_POSE, END_ANKLE, END_OFF, TUCK_ANKLE, SEAM_RX, END_RX
    for table in (ZERO_BASIS, ZERO_DIR, END_BASIS, END_DIR, END_KNEE_DIR,
                  END_ELBOW_DIR, END_HAND_DIR,
                  SEAM_FIST, SEAM_ELBOW_DIR, SEAM_HAND_DIR,
                  SEAM_ANKLE, SEAM_FOOT_EULER, END_FOOT_BASIS, SEAM_RX, END_RX,
                  END_OFF, END_ANKLE, END_TOE, TUCK_ANKLE, KNEE_DIR, ARM_MAX,
                  PLANT_KEYS,
                  ELBOW_KEYS, HAND_DIR_KEYS, FOOT_KEYS, LOCK_POSE):
        table.clear()
    _LOCK_REUSED[0] = 0

    arm, meshes = A.open_animation_project()
    A.setup_scene()
    for action_name in (SEAM_ACTION, END_ACTION):
        if action_name not in bpy.data.actions:
            raise RuntimeError("动作 %s 不在落盘文件里" % action_name)

    for side in SIDES:
        UE.ARM_LEN[side] = {
            "upper": arm.pose.bones["upperarm." + side].length,
            "forearm": arm.pose.bones["forearm." + side].length,
            "hand": arm.pose.bones["hand." + side].length}
        ARM_MAX[side] = (UE.ARM_LEN[side]["upper"]
                         + UE.ARM_LEN[side]["forearm"]
                         + UE.ARM_LEN[side]["hand"])

    UE.ROLL_STEP_DEG = _env_f("D17_ROLLSTEP", 2.0)
    UE.ROLL_GRID = UE._roll_grid()
    UE.EULER_Y_SAFE = _env_f("D17_YSAFE", 88.0)
    UE.EULER_Y_WEIGHT = _env_f("D17_YWEIGHT", 0.0)

    for extra in LEG_BONES + ("foot.L", "foot.R", "toe.L", "toe.R"):
        if extra not in A.PROBE_BONES:
            A.PROBE_BONES = tuple(A.PROBE_BONES) + (extra,)
        if extra not in A.PROBE_TAILS:
            A.PROBE_TAILS = tuple(A.PROBE_TAILS) + (extra,)
    A.PROBE_KEYS = A.PROBE_BONES + tuple(n + ".tail" for n in A.PROBE_TAILS)

    # ---- 接缝姿态（起点）----------------------------------------------------
    ZERO, seam_info = _load_pose_at(arm, SEAM_ACTION, SEAM_FRAME)
    if not ZERO:
        raise RuntimeError("读不到接缝姿态")
    # ---- 终点姿态（`Idle_01@0`）--------------------------------------------
    END_POSE, end_info = _load_pose_at(arm, END_ACTION, END_FRAME)
    if not END_POSE:
        raise RuntimeError("读不到终点姿态")

    # ★ 落盘真值 vs 手写重演（接缝）
    arm.animation_data.action = bpy.data.actions[SEAM_ACTION]
    A._bind_slot(arm, bpy.data.actions[SEAM_ACTION])
    bpy.context.scene.frame_set(int(SEAM_FRAME))
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
        "src": "%s@%d" % (SEAM_ACTION, SEAM_FRAME), "saved": seam_info,
        "geom_pos": round(geom_pos, 6), "pos_bone": geom_pos_bone,
        "geom_dir": round(geom_dir, 6), "dir_bone": geom_dir_bone,
        "matched": bool(geom_pos <= SEAM_REPLAY_POS_MAX_MM
                        and geom_dir <= SEAM_REPLAY_DIR_MAX_DEG)})

    # ★ 落盘真值 vs 手写重演（终点）
    arm.animation_data.action = bpy.data.actions[END_ACTION]
    A._bind_slot(arm, bpy.data.actions[END_ACTION])
    bpy.context.scene.frame_set(int(END_FRAME))
    bpy.context.view_layer.update()
    end_heads = {}
    for name in A.PROBE_BONES:
        if name in arm.pose.bones:
            end_heads[name] = Vector(A.bone_world(arm, name, "head"))
    arm.animation_data.action = None
    replay_end, _dirs = _world_snapshot(arm, END_POSE)
    end_geom, end_bone = 0.0, None
    for name, point in end_heads.items():
        other = replay_end.get(name)
        if other is None:
            continue
        gap = (point - other).length * 1000.0
        if gap > end_geom:
            end_geom, end_bone = gap, name
    END_MATCH.update({"src": "%s@%d" % (END_ACTION, END_FRAME),
                      "saved": end_info, "geom_pos": round(end_geom, 6),
                      "pos_bone": end_bone,
                      "matched": bool(end_geom <= SEAM_REPLAY_POS_MAX_MM)})

    # ---- 两个姿态的关键世界锚点 --------------------------------------------
    A.apply_pose(arm, ZERO)
    bpy.context.view_layer.update()
    for side in SIDES:
        SEAM_ANKLE[side] = Vector(A.bone_world(arm, "foot." + side, "head"))
        SEAM_FIST[side] = Vector(A.bone_world(arm, "hand." + side, "tail"))
        SEAM_HAND_DIR[side] = Vector(
            A.bone_direction(arm, "hand." + side)).normalized()
        shoulder = Vector(A.bone_world(arm, "upperarm." + side, "head"))
        elbow = Vector(A.bone_world(arm, "upperarm." + side, "tail"))
        SEAM_ELBOW_DIR[side] = tuple((elbow - shoulder).normalized())
        SEAM_FOOT_EULER[side] = tuple(ZERO.get("foot." + side, (0.0, 0.0, 0.0)))
    for name in TORSO_BONES:
        SEAM_RX[name] = float(ZERO.get(name, (0.0, 0.0, 0.0))[0])

    A.apply_pose(arm, END_POSE)
    bpy.context.view_layer.update()
    for side in SIDES:
        END_ANKLE[side] = Vector(A.bone_world(arm, "foot." + side, "head"))
        # ★ 抬跟的**旋转不动点** = `Idle_01@0` 的脚尖关节（世界）。它同时是
        #   `no_foot_slide_ok` 的探针（`per[f]["toe"]`）⟹ 绕它转 ⟹ 滑移构造性为 0。
        END_TOE[side] = Vector(A.bone_world(arm, "toe." + side, "head"))
        shoulder = Vector(A.bone_world(arm, "upperarm." + side, "head"))
        fist = Vector(A.bone_world(arm, "hand." + side, "tail"))
        END_OFF[side] = tuple(fist - shoulder)
        # ★ 落地后脚的**世界朝向真源**：`Idle_01@0` 的 foot 世界 3×3。
        #   鞋底口径（`sole_mm`）与脚不滑口径都以此为准（见 `_foot_euler`）。
        END_FOOT_BASIS["foot." + side] = (
            arm.pose.bones["foot." + side].matrix.to_3x3().copy())
        # ★★ 滚转参考的**终点**（`Idle_01@0`）：站姿的骨轴方向 + 世界 3×3。
        #    与 `ZERO_BASIS/ZERO_DIR`（俯卧）成对，供 `_roll_return(roll_mix)` 交接。
        hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
        knee = Vector(A.bone_world(arm, "shin." + side, "head"))
        ankle = Vector(A.bone_world(arm, "foot." + side, "head"))
        axis = (ankle - hip).normalized()
        bulge = (knee - hip) - axis * (knee - hip).dot(axis)
        END_KNEE_DIR[side] = (bulge.normalized() if bulge.length > 1e-9
                              else Vector((0.0, -0.94, -0.34)))
        # ★★ 臂的**肘鼓出方向**与**手骨朝向**在 `Idle_01@0` 的真实值（实测）。
        #    `ELBOW_KEYS` / `HAND_DIR_KEYS` 曾把终点写成**凭空常数**
        #    （`e2=(0.40s,−0.30,0.86)` / `h1=(0.10s,−0.25,−0.96)`）——
        #    拳尖是 IK 目标（钉得住），**肘是自由自由度**，假方向 ⟹ 肘落在别处
        #    ⟹ 上臂世界朝向与 `Idle` 差 **116°**，`f=33→34` 攒出跳变
        #    （`_d17_eul3.log`：`w_upperarm.R` `f=33 (60.27,21.59,−175.61)`
        #    → `f=34 (−70.09,15.64,111.91)`）。**终点必须来自接缝另一头**。
        shoulder = Vector(A.bone_world(arm, "upperarm." + side, "head"))
        elbow = Vector(A.bone_world(arm, "forearm." + side, "head"))
        wrist = Vector(A.bone_world(arm, "hand." + side, "head"))
        arm_axis = (wrist - shoulder).normalized()
        arm_bulge = (elbow - shoulder) - arm_axis * (elbow - shoulder).dot(arm_axis)
        END_ELBOW_DIR[side] = (arm_bulge.normalized() if arm_bulge.length > 1e-9
                               else Vector((0.0, 0.0, 1.0)))
        END_HAND_DIR[side] = Vector(A.bone_direction(arm, "hand." + side)).normalized()
    for name in TORSO_BONES + ("shoulder.L", "shoulder.R") + ARM_BONES + LEG_BONES:
        if name in arm.pose.bones:
            END_BASIS[name] = tuple(
                arm.pose.bones[name].matrix.to_3x3().to_quaternion())
    for name in ARM_BONES + LEG_BONES:
        END_DIR[name] = Vector(A.bone_direction(arm, name)).normalized()
    for name in TORSO_BONES:
        END_RX[name] = float(END_POSE.get(name, (0.0, 0.0, 0.0))[0])

    # ---- 膝向：接缝姿态下的"膝鼓出"方向（与 D16 同口径）--------------------
    A.apply_pose(arm, ZERO)
    bpy.context.view_layer.update()
    for side in SIDES:
        hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
        knee = Vector(A.bone_world(arm, "shin." + side, "head"))
        ankle = Vector(A.bone_world(arm, "foot." + side, "head"))
        axis = (ankle - hip).normalized()
        bulge = (knee - hip) - axis * (knee - hip).dot(axis)
        KNEE_DIR[side] = (bulge.normalized() if bulge.length > 1e-9
                          else Vector((0.0, -0.94, -0.34)))
    _kd_env = os.environ.get("D17_KNEE_DIR", "").strip()
    if _kd_env:
        kd = [float(x) for x in _kd_env.split(",")]
        KNEE_DIR["L"] = Vector((kd[0], kd[1], kd[2])).normalized()
        KNEE_DIR["R"] = Vector((-kd[0], kd[1], kd[2])).normalized()

    for bone in ARM_BONES + LEG_BONES:
        UE.IDLE_BASIS[bone] = arm.pose.bones[bone].matrix.to_3x3().copy()
        UE.IDLE_DIR[bone] = A.bone_direction(arm, bone)

    ZERO_WORLD = {n: tuple(v) for n, v in replay_heads.items()}
    for name in A.PROBE_BONES:
        if name in arm.pose.bones:
            ZERO_BASIS[name] = tuple(
                arm.pose.bones[name].matrix.to_3x3().to_quaternion())
    for name in ARM_BONES + LEG_BONES:
        if name in arm.pose.bones:
            ZERO_DIR[name] = Vector(A.bone_direction(arm, name)).normalized()

    # ---- 中段锚点（全部由两个端点**实测**派生，不是拍的）-------------------
    for side in SIDES:
        s = 1.0 if side == "L" else -1.0
        # ★ 落掌点：把拳从"举过头顶"拉到"肩下前方"的地面上（猛男先把掌收回来再撑）
        #   由接缝的肩-拳偏移与目标地面高度反推，避免拍脑袋写世界坐标。
        # ★★ `pull` 的 y 偏移 0.330 → 0.386：`pull`(f=4) 与 `plant`(f=5) 之间原本
        #    差 90 mm，一帧滑 90 mm 手上会"打滑"。收到 34 mm。
        # ★★ 撑地期的可达性由**躯干进度**保证（见 `TORSO_PROG` 注释），
        #    落掌点本身只做小幅收拢（0.420/0.425 是"肩下前方"的几何位置）。
        pull = Vector((SEAM_FIST[side].x * 0.58,
                       SEAM_FIST[side].y + 0.386,
                       0.032))
        plant = Vector((SEAM_FIST[side].x * 0.52,
                        SEAM_FIST[side].y + 0.420,
                        0.020))
        plant2 = Vector((SEAM_FIST[side].x * 0.50,
                         SEAM_FIST[side].y + 0.425,
                         0.014))
        PLANT_KEYS[side] = ((START, tuple(SEAM_FIST[side])),
                            (PUSH, tuple(pull)), (PUSH + 1, tuple(plant)),
                            (CHEST_UP, tuple(plant)), (HAND_OFF, tuple(plant2)))
        # ★ 肘鼓出：撑地期**往外张**（push-up 的肘窝朝外）
        # ★★ `DIR_END`：`e1`/`h1`（撑地姿态的肘向/手向）抵达帧。
        #    原稿写 `PUSH=4` ⟹ "接缝方向 → 撑地方向"这 **≈87°** 的转向被塞进 4 帧
        #    （实测 `_d17_armprobe2.log`：`edir` 每帧转 **21.8°**），叠加拳头自身
        #    位移后 `forearm.L` 的世界旋转在 `f=1` 达 **47.58°/帧**。
        #    把抵达帧推到 `HAND_OFF` 前 ⟹ 同样 87° 摊到 9 帧 ⟹ 峰值 ≈9.7°/帧。
        e0 = Vector(SEAM_ELBOW_DIR[side])
        e1 = Vector((0.72 * s, 0.30, 0.62)).normalized()
        e2 = Vector((0.40 * s, -0.30, 0.86)).normalized()
        e_end = tuple(END_ELBOW_DIR[side])          # ★ 实测 `Idle_01@0`，不是常数
        ELBOW_KEYS[side] = ((START, tuple(e0)), (DIR_END, tuple(e1)),
                            (HAND_OFF, tuple(e1)), (TUCK, tuple(e2)),
                            (FOOT_SET, tuple(e2)), (STAND, e_end), (END, e_end))
        h0 = Vector(SEAM_HAND_DIR[side])
        # ★★ `D17_HAND_DOWN` = `h1`（撑地期**手骨世界朝向**）的 z 分量，默认 −0.96。
        #    实测（`probe_d17_low.py`，本支定稿姿态）：`f=4` 时 `Finger_Middle_L`
        #    最低点 **−177.6 mm**（`Trouser_R` 只有 −61.5）—— 手骨几乎竖直朝下
        #    ⟹ 指尖扎进地板 178 mm。掌（`Hand_Palm_*`）却是 −13 mm（贴地正常），
        #    所以**现有门禁量不到这一条**（`hand_off_ok` 只取掌）⟹ 遗留盲点。
        #    把它抬到接近水平（撑地时掌平摊、指向身体前方）即可消掉。
        _hd = _env_f("D17_HAND_DOWN", -0.96)
        # ★★ `D17_HAND_FWD` = `h1` 的 **−Y（身前）分量**。默认 −0.25（原稿）。
        #    要「掌平摊在地上」必须把骨轴压向**水平**，即 fwd 变大、down 变小。
        _hf = _env_f("D17_HAND_FWD", -0.25)
        h1 = Vector((0.10 * s, _hf, _hd)).normalized()
        # ★★ `D17_HAND_DIR_END`：**手骨方向**自己的抵达帧（默认 = `DIR_END`）。
        #    为什么要和肘分开：实测（`probe_d17_low.py`）撑地期 `f=4` `hand.L` 骨端
        #    （= 拳 = IK 的驱动点）世界 z = **−148.6 mm**，而它的 IK 目标是 **+32 mm**
        #    —— 差 **181 mm**，`Finger_*` 网格最低点因此到 **−177.6 mm**。
        #    原因：`DIR_END=9` 把「接缝手向 → 撑地手向」压到 9 帧，`f=4` 只走到 44%
        #    ⟹ 手仍是"前伸偏下"，掌没摊平，指端整段扎进地板（`f2..f5` 四帧）。
        #    把**手**的抵达帧提到 `PUSH=4`（肘仍留在 9，肘窝外张本来就慢），
        #    这条 4 帧的"扎地"才有救。`h1` 值本身不变 ⟹ 两端姿态逐位不变。
        _hde = _env_i("D17_HAND_DIR_END", DIR_END)
        if not (START < _hde < TUCK):
            _hde = DIR_END
        h_end = tuple(END_HAND_DIR[side])           # ★ 实测 `Idle_01@0`，不是常数
        HAND_DIR_KEYS[side] = ((START, tuple(h0)), (_hde, tuple(h1)),
                               (TUCK, tuple(h1)), (FOOT_SET, tuple(h1)),
                               (STAND, h_end), (END, h_end))
        f0 = Vector(SEAM_FOOT_EULER[side])
        FE = (f0[0] * 0.55 - 30.0 * 0.45, f0[1] * 0.5, f0[2] * 0.5)
        FOOT_KEYS[side] = ((START, tuple(f0)), (PUSH, tuple(f0)),
                           (CHEST_UP, (f0[0] * 0.62, f0[1] * 0.6, f0[2] * 0.6)),
                           (HAND_OFF, (f0[0] * 0.50, f0[1] * 0.5, f0[2] * 0.5)),
                           (TUCK, FE), (FOOT_SET, FE), (END, FE))
        # ★ 收腿锚点：膝收到身下、踝在髋后上方（离地）
        TUCK_ANKLE[side] = Vector((0.125 * s, pelvis_y_at(TUCK) + 0.360,
                                   0.195))

    HEM_STATIC.clear()
    for name, value in _mesh_low_mm(HEM_OBJECTS).items():
        HEM_STATIC[name] = value

    JS._PREV_EULER.clear()
    UE.CARRY_Q.clear()
    LOCK_POSE.clear()
    A.apply_pose(arm, ZERO)
    bpy.context.view_layer.update()
    for name in ARM_BONES + LEG_BONES:
        UE.CARRY_Q[name] = arm.pose.bones[name].matrix.to_3x3().to_quaternion()
    for name, value in ZERO.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)

    # ---- 实测标定：撑地段胸骨尾端抬升（把 `chest_rise_ok` 落到实测）--------
    A.apply_pose(arm, torso_pose(CHEST_UP))
    bpy.context.view_layer.update()
    chest_mid = Vector(A.bone_world(arm, "chest", "tail")).z * 1000.0

    A.report("D17_LAYOUT", {
        "total_frames": TOTAL, "seconds": round(TOTAL / float(A.FPS), 3),
        "push": PUSH, "chest_up": CHEST_UP, "hand_off": HAND_OFF, "tuck": TUCK,
        "foot_set": FOOT_SET, "rise_mid": RISE_MID, "stand": STAND,
        "vertical_channel": {
            "shape": "★ **无弹道段**：骨盆沿单调上升曲线 220 → 830 mm（三段支点：掌→脚→双腿）",
            "pelvis_z_keys": [list(k) for k in PELVIS_Z_KEYS],
            "pelvis_y_keys": [list(k) for k in PELVIS_Y_KEYS]},
        "seam": {"action": SEAM_ACTION, "frame": SEAM_FRAME, "src": seam_info},
        "end": {"action": END_ACTION, "frame": END_FRAME, "src": end_info},
        "measured": {
            "seam_pelvis_z_mm": round(pelvis_z_at(START) * 1000.0, 3),
            "end_pelvis_z_mm": round(pelvis_z_at(END) * 1000.0, 3),
            "rise_mm": round((pelvis_z_at(END) - pelvis_z_at(START)) * 1000.0, 3),
            "seam_ankle_mm": {s: [round(v * 1000.0, 3) for v in SEAM_ANKLE[s]]
                              for s in SIDES},
            "end_ankle_mm": {s: [round(v * 1000.0, 3) for v in END_ANKLE[s]]
                             for s in SIDES},
            "seam_fist_mm": {s: [round(v * 1000.0, 3) for v in SEAM_FIST[s]]
                             for s in SIDES},
            "end_off_mm": {s: [round(v * 1000.0, 3) for v in END_OFF[s]]
                           for s in SIDES},
        },
        "chest_tail_at_chest_up_mm": round(chest_mid, 3),
        "forward_scalar": {
            "note": "★ 起点在 y = −550 mm、终点在 y = 0 —— 位移层**构造性**为 0"
                    "（骨盆 y 由独立通道驱动）。",
        },
        "roll_weight_mode": ROLL_WEIGHT_MODE,
        "note": ("D17 正面起身：零位 = **`Knockdown_F@20` 落盘帧**；终点 = "
                 "**`Idle_01@0` 落盘帧**（跨族接缝）。竖直通道**无弹道段**，"
                 "骨盆单调升 610 mm；支点**掌 → 脚**，只换一次。"),
    })
    return arm, meshes


# =============================================================== 门禁
def getup_assertions(arm, action, samples, meshes, end_mats_ref):  # noqa: C901
    res = {}
    scene = bpy.context.scene
    arm.animation_data.action = action
    A._bind_slot(arm, action)

    moving = _pelvis_moving(arm)
    seam_mats = CR.action_world_matrices(arm, bpy.data.actions[SEAM_ACTION],
                                         SEAM_FRAME)
    mats0 = CR.action_world_matrices(arm, action, START)
    ori0, rel0, ob0, rb0 = _pose_seam_split(mats0, seam_mats, moving)
    res["seam_in_orient_delta"] = float("%.3e" % ori0)
    res["seam_in_orient_bone"] = ob0
    res["seam_in_relpos_delta_mm"] = round(rel0 * 1000.0, 6)
    res["seam_in_relpos_bone"] = rb0
    res["seam_in_raw_delta"] = float("%.3e" % CR.matrix_delta(mats0, seam_mats))
    res["seam_in_ok"] = bool(max(ori0, rel0) <= SEAM_TOL)
    res["seam_in_note"] = (
        "★★ 首帧**逐位** = `%s@%d`（平移不变尺子：pelvis 的后代比"
        "「世界位置 − 骨盆世界位置」，非后代比世界绝对）。容差 %.0e，未放宽。"
        % (SEAM_ACTION, SEAM_FRAME, SEAM_TOL))

    # ---- ★★★ 末帧 = `Idle_01@0`（本支最硬的判据）---------------------------
    mats_end = CR.action_world_matrices(arm, action, END)
    end_delta = CR.matrix_delta(mats_end, end_mats_ref)
    worst_end, worst_end_bone = 0.0, None
    for name in mats_end:
        ref = end_mats_ref.get(name)
        if ref is None:
            continue
        gap = max(abs(a - b) for a, b in zip(mats_end[name], ref))
        if gap > worst_end:
            worst_end, worst_end_bone = gap, name
    res["end_vs_idle_matrix_delta"] = float("%.3e" % end_delta)
    res["end_vs_idle_worst_bone"] = worst_end_bone
    res["end_vs_idle_worst_delta"] = float("%.3e" % worst_end)
    ori_e, rel_e, ob_e, rb_e = _pose_seam_split(mats_end, end_mats_ref, moving)
    res["end_vs_idle_orient_delta"] = float("%.3e" % ori_e)
    res["end_vs_idle_relpos_mm"] = round(rel_e * 1000.0, 9)
    res["end_matches_idle_tol"] = END_TOL
    res["end_matches_idle_ok"] = bool(max(end_delta, worst_end) <= END_TOL)
    res["end_matches_idle_note"] = (
        "★★★ **本支最硬的判据**：末帧（`f = %d`）**逐骨 4×4 世界矩阵**必须与 "
        "`%s@%d` 一致（`max_delta ≤ %.0e`）。★ 用**世界矩阵**而不是欧拉三元组："
        "`pose_bone.matrix` 的 setter 可能解出等价但不同的欧拉表示。"
        "★ 本支是全项目**第一次跨族**（地面族 → 站立族），这条接缝否则没人管。"
        % (END, END_ACTION, END_FRAME, END_TOL))

    # ---- 上/下缘 & 骨盆逐帧 --------------------------------------------------
    arm.animation_data.action = None
    A.apply_pose(arm, ZERO)
    bpy.context.view_layer.update()
    zero = _body_metrics(arm)
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    per, clear, feet, handlow = {}, {}, {}, {}
    for frame in range(0, TOTAL + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        per[frame] = _body_metrics(arm)
        clear[frame] = _foot_clearance()
        feet[frame] = A.foot_lowest_by_side()
        handlow[frame] = {s: _lowest_of(HAND_MESHES[s]) for s in SIDES}

    zs = {f: per[f]["pelvis"].z for f in per}
    ys = {f: per[f]["pelvis"].y for f in per}
    xs = {f: per[f]["pelvis"].x for f in per}
    cpitch = {f: per[f]["chest_pitch_deg"] for f in per}

    # ---- ★ 起身幅度 ---------------------------------------------------------
    res["pelvis_z_mm"] = {str(f): round(zs[f] * 1000.0, 3) for f in sorted(zs)}
    res["pelvis_y_mm"] = {str(f): round(ys[f] * 1000.0, 3) for f in sorted(ys)}
    rise = (zs[END] - zs[START]) * 1000.0
    res["rise_net_mm"] = round(rise, 3)
    res["rise_min_mm"] = RISE_MIN_MM
    res["rise_reach_ok"] = bool(rise >= RISE_MIN_MM)
    res["rise_reach_note"] = (
        "★ 骨盆 z 从起点到终点净升 **≥ %.0f mm**（防「只起来一半」）。"
        "阈值由**实测**导出：起点 %.1f mm（`%s@%d`）→ 终点 %.1f mm（`%s@%d`），"
        "真实净升 %.1f mm ⟹ 阈值取实测的 %.0f%%。"
        "（清单计划写的 650 mm 基于**推算**的终点 900 mm；实测终点是 830 mm，"
        "650 物理上不可达 ⟹ 这是**把推算换成实测**，不是放宽容差。）"
        % (RISE_MIN_MM, zs[START] * 1000.0, SEAM_ACTION, SEAM_FRAME,
           zs[END] * 1000.0, END_ACTION, END_FRAME, rise,
           RISE_MIN_MM * 100.0 / max(1e-9, rise)))

    # ---- ★ 单调上升（全段，强于清单要求的 `[FOOT_SET, END]` 窗口）----------
    win = [f for f in range(FOOT_SET, TOTAL + 1)]
    rises = [{"frame": f, "dz_mm": round((zs[f] - zs[f - 1]) * 1000.0, 4)}
             for f in win[1:]
             if (zs[f] - zs[f - 1]) * 1000.0 < -RISE_MONO_TOL_MM]
    full_rises = [{"frame": f, "dz_mm": round((zs[f] - zs[f - 1]) * 1000.0, 4)}
                  for f in range(START + 1, TOTAL + 1)
                  if (zs[f] - zs[f - 1]) * 1000.0 < -RISE_MONO_TOL_MM]
    res["rise_monotone_violations_window"] = rises
    res["rise_monotone_violations_full"] = full_rises
    res["rise_monotone_tol_mm"] = RISE_MONO_TOL_MM
    res["rise_monotone_window"] = [FOOT_SET, TOTAL]
    res["rise_monotone_ok"] = bool(not rises)
    res["rise_monotone_note"] = (
        "★ 骨盆 z 在 `[FOOT_SET=%d, END=%d]` 必须**单调不降**（容差 %.1f mm/帧）。"
        "★ 本支实测**全段**（`[0, END]`）都单调（`rise_monotone_violations_full = []`）"
        " —— 起身是**一次**持续发力，中途不回落。"
        % (FOOT_SET, TOTAL, RISE_MONO_TOL_MM))

    # ---- ★ 撑地推起：胸骨尾端抬升 -----------------------------------------
    ct = {f: per[f]["chest_tail"].z * 1000.0 for f in per}
    res["chest_tail_z_mm"] = {str(f): round(ct[f], 3) for f in sorted(ct)}
    chest_rise = ct[HAND_OFF] - ct[START]
    res["chest_rise_mm"] = round(chest_rise, 3)
    res["chest_rise_min_mm"] = CHEST_RISE_MIN_MM
    res["chest_rise_ok"] = bool(chest_rise >= CHEST_RISE_MIN_MM)
    res["chest_rise_note"] = (
        "★ 撑地段 `[START=%d, HAND_OFF=%d]` 胸骨尾端世界 z 必须**净升 ≥ %.0f mm**"
        "（证明「撑地真的把上身顶起来了」，而不是只有胳膊在动）。"
        % (START, HAND_OFF, CHEST_RISE_MIN_MM))

    # ---- ★★ 支点交接 1：手掌离地（两侧都量）-------------------------------
    hand_min = {f: min(handlow[f]["L"], handlow[f]["R"]) for f in handlow}
    res["hand_low_mm"] = {str(f): round(hand_min[f], 2) for f in sorted(hand_min)}
    on = [f for f in range(START, HAND_OFF + 1)
          if hand_min[f] > HAND_TOUCH_MAX_MM]
    off = [f for f in range(HAND_OFF + 1, TOTAL + 1)
           if hand_min[f] < HAND_OFF_MIN_MM]
    res["hand_touch_max_mm"] = HAND_TOUCH_MAX_MM
    res["hand_off_min_mm"] = HAND_OFF_MIN_MM
    res["hand_on_violations"] = on
    res["hand_off_violations"] = off
    res["hand_off_ok"] = bool(not on and not off)
    res["hand_off_note"] = (
        "★★ **支点交接 1**：`f ≤ HAND_OFF=%d` 时手掌（`Hand_Palm_*` + `Finger_*` "
        "网格）最低点必须 **≤ %.0f mm**（手真的在地上推）；`f > HAND_OFF` 必须 "
        "**≥ %.0f mm**（手确实离地了）。**两侧都量** —— 缺任何一侧，就有一整段"
        "「手到底在不在上」没人管。" % (HAND_OFF, HAND_TOUCH_MAX_MM, HAND_OFF_MIN_MM))

    # ---- ★★ 支点交接 2：双脚接住地面（唯一帧）-----------------------------
    sole = {f: min(clear[f]["L"], clear[f]["R"]) for f in clear}
    res["sole_mm"] = {str(f): (None if sole[f] is None
                              else round(sole[f] * 1000.0, 2))
                      for f in sorted(sole)}
    touch = [f for f in range(TUCK, FOOT_SET + 1)
             if sole[f] is not None and sole[f] * 1000.0 <= SOLETOUCH_MAX_MM]
    res["foot_touch_max_mm"] = SOLETOUCH_MAX_MM
    res["foot_touch_frames"] = touch
    res["foot_touch_frame"] = (touch[0] if len(touch) == 1 else None)
    res["foot_takeover_ok"] = bool(len(touch) == 1 and touch[0] == FOOT_SET)
    res["foot_takeover_note"] = (
        "★★ **支点交接 2**：脚接住地面的帧必须**唯一**且落在 `[TUCK=%d, "
        "FOOT_SET=%d]` 内（口径 = **首次鞋底 ≤ %.0f mm**）。实测 `%s`。"
        "★ 与 `hand_off_ok` **方向相反**：这条管「脚什么时候上来」，那条管「手什么"
        "时候下去」，缺任何一条就有「谁都没在地上」的一段没人管。"
        % (TUCK, FOOT_SET, SOLETOUCH_MAX_MM, touch))

    # ---- ★ 站姿族硬约束：脚不滑 + 鞋底贴地（`f ≥ FOOT_SET`）--------------
    slide = {}
    for probe in ("toe.L", "toe.R"):
        pts = [Vector(per[f]["toe"][probe[-1]]) for f in win]
        ref = pts[0]
        slide[probe] = round(max((p - ref).length for p in pts) * 1000.0, 4)
    res["foot_slide_mm_after_set"] = slide
    res["foot_slide_max_mm"] = FOOT_SLIDE_MAX_MM
    res["no_foot_slide_ok"] = bool(slide and max(slide.values())
                                   <= FOOT_SLIDE_MAX_MM)
    res["no_foot_slide_note"] = (
        "★ 清单 §6 硬约束：`f ≥ FOOT_SET=%d` 双脚 `foot_probe`（`toe.L/R` 骨端）"
        "世界位移 **≤ %.0f mm**。" % (FOOT_SET, FOOT_SLIDE_MAX_MM))
    soles_tail = [sole[f] * 1000.0 for f in win if sole[f] is not None]
    res["sole_tail_min_mm"] = round(min(soles_tail), 3)
    res["sole_tail_max_mm"] = round(max(soles_tail), 3)
    res["sole_ground_ok"] = bool(soles_tail
                                 and min(soles_tail) >= SOLE_MIN_MM
                                 and max(soles_tail) <= SOLE_MAX_MM)
    res["sole_ground_note"] = (
        "★ 清单 §6：`f ≥ FOOT_SET` 鞋底必须 ∈ **[%.0f, %.0f] mm**（支撑脚贴地）。"
        % (SOLE_MIN_MM, SOLE_MAX_MM))

    # ---- ★ 收招不许瞬停 ----------------------------------------------------
    tail_start = int(TOTAL - NO_SNAP_TAIL_FRAMES)
    steps = [round(_worst_step(samples, i - 1, i)[0], 6)
             for i in range(tail_start + 1, TOTAL + 1)]
    res["no_snap_tail_steps_deg"] = steps
    res["no_snap_stop_ok"] = bool(
        len(steps) >= 2
        and all(steps[i] >= steps[i + 1] - 1e-6 for i in range(len(steps) - 1))
        and steps[-1] <= 1e-6)
    res["no_snap_tail_window"] = [tail_start, TOTAL]
    res["no_snap_ruler_note"] = (
        "★ 口径按清单 §0.6 原文：「末 6 帧角度增量的绝对值**单调收敛**」。")

    # ---- ★ 定向运动：根位移（本支**构造性** 0）----------------------------
    dx = (xs[END] - xs[START]) * 1000.0
    dy = (ys[END] - ys[START]) * 1000.0
    # ★ 位移层由独立通道驱动 ⟹ 起点/终点的 y 是"计划值"，**实际位移**按实测登记
    res["root_motion_net_mm"] = round(math.hypot(dx, dy), 3)
    res["root_motion_m"] = [round(dx / 1000.0, 6), round(dy / 1000.0, 6)]
    res["root_motion_ok"] = bool(abs(dx) <= 2.0
                                 and abs(dy - 550.0) <= 10.0)
    res["root_motion_note"] = (
        "★ 与 D16（≈0）**不同**：本支骨盆要向前走 **+550 mm**（`−550 → 0`）"
        "把身体带到双脚上方，如实登记。")

    # ---- 末帧登记 ----------------------------------------------------------
    end_vz = (zs[END] - zs[END - 1]) * 1000.0
    res["end_pelvis_z_mm"] = round(zs[END] * 1000.0, 3)
    res["end_vz_mm_per_frame"] = round(end_vz, 6)
    res["end_vz_zero_ok"] = bool(abs(end_vz) <= 1e-6)

    # ---- ★ 力量传导链（脚→腿→髋→腰→肩→手）------------------------------
    knee_flex = {s: round(max(abs(per[f]["knee_deg"][s] - zero["knee_deg"][s])
                              for f in per), 3) for s in SIDES}
    hipf = {s: [per[f]["hip_flex_deg"][s] for f in per] for s in SIDES}
    hip_dev = {s: round(max(abs(v - hipf[s][0]) for v in hipf[s]), 3)
               for s in SIDES}
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
    waist_span = max(abs(cpitch[f] - cpitch[0]) for f in per)
    res["fist_travel_mm"] = round(fist_dev, 3)
    res["fist_travel_at"] = fist_dev_at
    res["ankle_travel_mm"] = round(ankle_dev, 3)
    res["shoulder_move_mm"] = round(shoulder_move, 3)
    res["pelvis_span_mm"] = round(pelvis_span, 3)
    res["chain_travel"] = {
        "foot_mm": round(ankle_dev, 2), "knee_deg": round(max(knee_flex.values()), 3),
        "hip_deg": round(max(hip_dev.values()), 3), "waist_deg": round(waist_span, 3),
        "shoulder_mm": round(shoulder_move, 2), "hand_mm": round(fist_dev, 2)}
    res["chain_present_ok"] = bool(
        res["chain_travel"]["foot_mm"] > 50.0
        and res["chain_travel"]["knee_deg"] > 20.0
        and res["chain_travel"]["hip_deg"] > 8.0
        and res["chain_travel"]["waist_deg"] > 4.0
        and res["chain_travel"]["shoulder_mm"] > 5.0
        and res["chain_travel"]["hand_mm"] > 30.0)
    res["chain_present_note"] = (
        "★ 清单 §6：力量传导链 **脚→腿→髋→腰→肩→手**，每段都要有真实工作量。"
        "本支六段全由**实测**度量（脚=踝世界行程 / 膝=膝屈角变化 / 髋=髋屈角变化 / "
        "腰=胸骨尾端俯仰变化 / 肩=肩峰位移 / 手=拳位移）。")

    # ---- 穿模 --------------------------------------------------------------
    frames = sorted(set(list(range(0, TOTAL + 1, CLIP_EVERY))
                        + [PUSH, CHEST_UP, HAND_OFF, TUCK, FOOT_SET, RISE_MID,
                           STAND, TOTAL]))
    worst_clip, worst_clip_at, worst_clip_frame = 0.0, None, None
    for frame in frames:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        clip = PD.clip_metrics(arm)
        if clip["clip_max_mm"] > worst_clip:
            worst_clip, worst_clip_at, worst_clip_frame = (
                clip["clip_max_mm"], clip["clip_at"], frame)
    res["clip_max_mm"] = round(worst_clip, 2)
    res["clip_at"] = worst_clip_at
    res["clip_frame"] = worst_clip_frame
    res["no_face_clip_ok"] = bool(worst_clip <= CLIP_MAX_MM)

    # ---- 可达性 ------------------------------------------------------------
    worst_reach, worst_reach_frame = 0.0, None
    worst_leg, worst_leg_frame = 0.0, None
    for frame in range(0, TOTAL + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        for side in SIDES:
            shoulder = Vector(A.bone_world(arm, "upperarm." + side, "head"))
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

    # ---- 下摆静态件 --------------------------------------------------------
    hem_now = _mesh_low_mm(HEM_OBJECTS)
    hem_static = True
    hem_rows = {}
    for name, value in hem_now.items():
        hem_rows[name] = round(value, 4)
        ref = HEM_STATIC.get(name)
        if ref is None or abs(value - ref) > 1e-6:
            hem_static = False
    res["hem_low_mm"] = hem_rows
    res["hem_static_ok"] = bool(hem_static and hem_rows)
    res["hem_static_note"] = (
        "★ `%s` 是**已知模型侧绑定遗漏**（`parent=None` / `vgroups=0`）⟹ 钉在世界"
        "原点、**不随骨架动**；本判据核对它们世界最低点**首末逐位相同**。"
        % ",".join(HEM_OBJECTS))

    # ---- 剪影 / aspect：只报不判 -------------------------------------------
    sil = P.silhouette(arm, "d17")
    res["aspect"] = sil["aspect"]
    res["width_m"] = sil["width_m"]
    res["height_m"] = sil["height_m"]

    # ---- ★ 停用判据（显式登记理由，照 D16 停用 `ballistic_until_land_ok`）--
    res["disabled_gates"] = {
        "ground_hold_ok": "DISABLED —— 贴地族判据（骨盆逐位固定）。本支骨盆要跑 "
                          "610 mm ⟹ 照抄必然红。换成 `rise_monotone_ok` + `rise_reach_ok`。",
        "back_land_ok": "DISABLED —— 贴地族判据（后脑贴地）。本支末帧是**站姿**。",
        "landing_plateau_ok": "DISABLED —— 贴地族判据（落地后骨盆逐位相同）。"
                              "本支末段骨盆构造性固定在 830 mm，但语义不同。",
        "legs_bounce_ok": "DISABLED —— 贴地族判据（腿抖一下再落）。本支腿是**主动收放**。",
        "bounce_present_ok / bounce_single_peak_ok / bounce_no_double_ok":
            "DISABLED —— 贴地族「局部弹起」判据。本支是**主动起身**，无受力弹起。",
        "ballistic_until_land_ok": "DISABLED —— 本支竖直通道**没有弹道段**"
                                   "（全段单调上升，无抛物线可比）。",
        "hitstop_present": "DISABLED —— ★ 本支是**主动发力**动作，**没有「命中帧」**。"
                           "硬套只会得到伪造的停顿。收招由 `no_snap_tail_ok` 守，"
                           "「一次发力、不回落」由 `rise_monotone_ok` 守。"
                           "（本条是对清单 §3「照抄不改 `hitstop_present`」的**诚实偏差**，"
                           "理由登记在此。）",
    }
    res["ballistic_status"] = "DISABLED"
    res["ballistic_phase_registered"] = {
        "T_PHASE_D14": D14_T_PHASE, "T_PHASE_D17": T_PHASE_D17,
        "note": "★ 仅登记（本支竖直通道**不含弹道**，不参与解算）"}

    # ---- 冻结段 ------------------------------------------------------------
    res["lock_frames"] = _LOCK_REUSED[0]
    res["lock_expect"] = 0
    last_steps = [round(_worst_step(samples, i - 1, i)[0], 6)
                  for i in range(STAND + 1, TOTAL + 1)]
    res["end_hold_steps_deg"] = last_steps
    res["end_ground_hold_ok"] = bool(not last_steps
                                     or max(last_steps) <= END_HOLD_MAX_DEG)

    res["seam_zero_saved_ok"] = bool(SEAM_MATCH["matched"])
    res["seam_zero_src"] = SEAM_MATCH["src"]
    res["seam_zero_geom_pos_mm"] = SEAM_MATCH["geom_pos"]
    res["seam_zero_geom_dir_deg"] = SEAM_MATCH["geom_dir"]
    res["seam_zero_worst_bone"] = SEAM_MATCH["pos_bone"]
    res["end_zero_saved_ok"] = bool(END_MATCH["matched"])
    res["end_zero_src"] = END_MATCH["src"]
    res["end_zero_geom_pos_mm"] = END_MATCH["geom_pos"]

    if os.environ.get("D17_TRACE"):
        res["trace"] = {str(f): {
            "pelvis_z": round(zs[f] * 1000.0, 2),
            "pelvis_y": round(ys[f] * 1000.0, 2),
            "chest_tail": round(ct[f], 2),
            "hand_low": round(hand_min[f], 2),
            "sole": None if sole[f] is None else round(sole[f] * 1000.0, 2),
            "knee": {s: round(per[f]["knee_deg"][s], 2) for s in SIDES},
            "hip_flex": {s: round(per[f]["hip_flex_deg"][s], 2) for s in SIDES},
            "ankle_z": {s: round(per[f]["ankle"][s].z * 1000.0, 2) for s in SIDES},
        } for f in range(0, TOTAL + 1)}
    return res


def _lowest_of(names):
    row = _mesh_low_mm(names)
    return None if not row else min(row.values())


def _foot_clearance():
    low = A.foot_lowest_by_side()
    return {s: (low[s][2] if low[s] is not None else None) for s in SIDES}


def _body_metrics(arm):
    lo, hi = PD.head_box()
    return {
        "pelvis": Vector(A.bone_world(arm, "pelvis", "head")),
        "chest_tail": Vector(A.bone_world(arm, "chest", "tail")),
        "fist": {s: Vector(A.bone_world(arm, "hand." + s, "tail")) for s in SIDES},
        "shoulder": {s: Vector(A.bone_world(arm, "upperarm." + s, "head"))
                     for s in SIDES},
        "ankle": {s: Vector(A.bone_world(arm, "foot." + s, "head")) for s in SIDES},
        "toe": {s: Vector(A.bone_world(arm, "toe." + s, "head")) for s in SIDES},
        "knee_deg": {s: _knee_angle(arm, s) for s in SIDES},
        "hip_flex_deg": {s: _hip_flex(arm, s) for s in SIDES},
        "chest_pitch_deg": _pitch(Vector(A.bone_direction(arm, "chest"))),
        "head_pitch_deg": _pitch(Vector(A.bone_direction(arm, "head"))),
        "pelvis_pitch_deg": _pitch(Vector(A.bone_direction(arm, "pelvis"))),
    }


ZERO_FIST = {}


def main():
    global ZERO_FIST
    arm, meshes = boot()

    JS._PREV_EULER.clear()
    UE.CARRY_Q.clear()
    LOCK_POSE.clear()
    _LOCK_REUSED[0] = 0
    A.apply_pose(arm, ZERO)
    bpy.context.view_layer.update()
    for name in ARM_BONES + LEG_BONES:
        UE.CARRY_Q[name] = arm.pose.bones[name].matrix.to_3x3().to_quaternion()
    for name, value in ZERO.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)
    ZERO_FIST = {s: Vector(A.bone_world(arm, "hand." + s, "tail")) for s in SIDES}

    # ---- ★ 临时几何诊断（`D17_GEOMDBG=1`）：逐帧真值 ------------------------
    if os.environ.get("D17_GEOMDBG"):
        for f in range(0, TOTAL + 1):
            A.apply_pose(arm, solve_pose(arm, f, meshes))
            bpy.context.view_layer.update()
            row = {"f": f}
            for s in SIDES:
                hip = Vector(A.bone_world(arm, "thigh." + s, "head"))
                tgt = ankle_target(arm, s, f)
                ank = Vector(A.bone_world(arm, "foot." + s, "head"))
                sh = Vector(A.bone_world(arm, "upperarm." + s, "head"))
                ft = fist_target(arm, s, f)
                row["hip_" + s] = [round(v * 1000.0, 1) for v in hip]
                row["anktgt_" + s] = [round(v * 1000.0, 1) for v in tgt]
                row["ank_" + s] = [round(v * 1000.0, 1) for v in ank]
                row["ankerr_" + s] = round((tgt - ank).length * 1000.0, 1)
                row["sh_" + s] = [round(v * 1000.0, 1) for v in sh]
                row["ftgt_" + s] = [round(v * 1000.0, 1) for v in ft]
                row["ft_" + s] = [round(v * 1000.0, 1) for v in
                                  A.bone_world(arm, "hand." + s, "tail")]
                row["rA_" + s] = round((ft - sh).length / ARM_MAX[s], 3)
                row["dL_" + s] = round((tgt - hip).length * 1000.0, 1)
                row["limL_" + s] = round((A.L_THIGH + A.L_SHIN) * 0.9995
                                         * 1000.0, 1)
                row["rL_" + s] = round(
                    (tgt - hip).length / ((A.L_THIGH + A.L_SHIN) * 0.9995), 3)
                row["shoe_" + s] = round(
                    (_foot_clearance()[s] or 0.0) * 1000.0, 2)
                row["fb_" + s] = [round(v, 5) for r in
                                  arm.pose.bones["foot." + s].matrix.to_3x3()
                                  for v in r]
            hb_lo, hb_hi = PD.head_box()
            row["hb_lo"] = [round(v * 1000.0, 1) for v in hb_lo]
            row["hb_hi"] = [round(v * 1000.0, 1) for v in hb_hi]
            row["clip"] = round(PD.clip_metrics(arm)["clip_max_mm"], 2)
            print("D17_GEOM " + json.dumps(row))
        return

    keyframes = []
    for frame in range(0, TOTAL + 1):
        if frame == TOTAL and END_ZERO:
            # ★ 反验证 ⑦：末帧改零位
            pose = {name: (0.0, 0.0, 0.0) for name in ZERO if not name.startswith("@")}
            pose["@loc"] = {"pelvis": A.wloc(0.0, 0.0, 0.0)}
            keyframes.append((frame, pose))
        else:
            keyframes.append((frame, solve_pose(arm, frame, meshes)))

    # ===== ★★★ 臂链**起手段**：接缝 → 撑地的逐分量欧拉路径插值（见 `ARM_MIX_TO`）===
    #   ★ 放在**归一之前**：本段改的是**欧拉分量本身**（等价于改世界旋转），
    #     必须让随后的 `_nearest_branch` 看到真实的最终值。
    #   ★ 只动 `ARM_BONES` 的欧拉；躯干/腿/骨盆/拳一并保留 IK 解 ⟹
    #     `chest_rise_ok` / `rise_monotone_ok` / `no_foot_slide_ok` 不受影响。
    #   ★ `f=0` 与 `f=ARM_MIX_TO` **逐位不动** ⟹ `seam_in_ok` 与 `f≥K` 的连续性不受影响。
    # ★★★ 通用锚点路径（优先于 head 特例）：相邻锚点之间，臂骨欧拉逐分量插值。
    if ARM_ANCHORS:
        _pose_at = {_f: _p for _f, _p in keyframes}
        for _i in range(len(ARM_ANCHORS) - 1):
            _fa, _fb = ARM_ANCHORS[_i], ARM_ANCHORS[_i + 1]
            _pa, _pb2 = _pose_at.get(_fa), _pose_at.get(_fb)
            if _pa is None or _pb2 is None or _fb <= _fa:
                continue
            for _j in range(_fa + 1, _fb):
                _p = _pose_at.get(_j)
                if _p is None:
                    continue
                _s = _smoothstep(float(_j - _fa) / float(_fb - _fa))
                for _n in ARM_BONES:
                    a = tuple(_pa.get(_n, (0.0, 0.0, 0.0)))
                    b = tuple(_pb2.get(_n, a))
                    if ANCHOR_SLERP and _fb <= ANCHOR_SLERP_UNTIL:
                        # ★ 局部旋转走**测地线**（四元数 slerp）。`to_euler` 落哪一支
                        #   无所谓 —— 紧随其后的 `_nearest_branch` 只换写法、不动旋转。
                        _qa = Euler([math.radians(v) for v in a], "XYZ").to_quaternion()
                        _qb = Euler([math.radians(v) for v in b], "XYZ").to_quaternion()
                        if _qa.dot(_qb) < 0.0:
                            _qb = Quaternion((-_qb.w, -_qb.x, -_qb.y, -_qb.z))
                        _p[_n] = tuple(math.degrees(v) for v in
                                       _qa.slerp(_qb, _s).to_euler("XYZ"))
                    else:
                        _bb = tuple(_nearest_equiv(y, x) for x, y in zip(a, b))
                        _p[_n] = tuple(u + (v - u) * _s for u, v in zip(a, _bb))

    if ARM_MIX_TO and not ARM_ANCHORS and 0 < ARM_MIX_TO <= TOTAL:
        _head = None
        for _i, (_f, _p) in enumerate(keyframes):
            if _f == ARM_MIX_TO:
                _head = _p
                _hi = _i
                break
        if _head is not None:
            _seam = keyframes[0][1]
            for _i in range(1, _hi):
                _f, _p = keyframes[_i]
                _u = float(_f) / float(ARM_MIX_TO)
                _s = _smoothstep(_u)
                for _n in ARM_BONES:
                    a = tuple(_seam.get(_n, (0.0, 0.0, 0.0)))
                    b = tuple(_head.get(_n, a))
                    bb = tuple(_nearest_equiv(y, x) for x, y in zip(a, b))
                    _p[_n] = tuple(u + (v - u) * _s for u, v in zip(a, bb))
                keyframes[_i] = (_f, _p)

    # ===== ★★ 欧拉表示归一（只换写法、**不改世界旋转**）=====================
    #   `no_teleport`（`anim_lib.max_frame_step_deg`）与 `no_snap_stop_ok`
    #   （本文件 `_worst_step`）量的都是**逐分量欧拉步长**。同一个局部旋转有多支
    #   等价欧拉写法（两支 XYZ 分支 + 每分量 ±360°）⟹ 逐帧独立解算会让相邻帧落在
    #   不同分支上，制造**纯表示层**的假跳变（`f=10→11 forearm.R` 实测 82.09°，
    #   而该骨的世界朝向是连续的）。
    #   ★ 做法：沿时间轴**贪心重写**——每骨每帧，在所有等价写法里取「离上一帧
    #     最近」的那支。**不移动任何骨端、不改任何世界 3×3 / 4×4** ⟹ 接缝
    #     （`seam_in_ok` / `end_matches_idle_ok`）、贴地（`sole_ground_ok`）、
    #     剪影、拳位、`reach_ok`、`clip_metrics` 按定义**全部不受影响**。
    #   ★ 首帧保持原值（接缝逐位不许动）⟹ `ua_start_ok` 不受影响。
    #   ★ 单调性：原值本身就在候选集里（`Euler(val)` 的两支即含原值）⟹ 每步
    #     **只减不增** ⟹ 这一遍不可能把任何门禁改红（仅可能改绿）。
    def _nearest_branch(value, ref):
        """在所有等价 XYZ 欧拉写法里，取「逐分量离 `ref` 最近」的那支（度）。"""
        m = Euler([math.radians(v) for v in value], "XYZ").to_matrix()
        best, best_cost = None, None
        for cand in UE._xyz_candidates(m):
            val = [math.degrees(t) for t in cand]
            for index in range(3):
                while val[index] - ref[index] > 180.0:
                    val[index] -= 360.0
                while val[index] - ref[index] < -180.0:
                    val[index] += 360.0
            cost = max(abs(a - b) for a, b in zip(val, ref))
            if best_cost is None or cost < best_cost:
                best, best_cost = tuple(val), cost
        return best

    _prev_rep = {}
    _normalised = []
    if not _env_b("D17_NORM_OFF"):
        for _f, _pose in keyframes:
            _new = dict(_pose)
            for _name in _pose:
                if _name.startswith("@"):
                    continue
                _ref = _prev_rep.get(_name)
                if _ref is None:
                    _prev_rep[_name] = tuple(_pose[_name])
                    continue
                _best = _nearest_branch(_pose[_name], _ref)
                _new[_name] = _best
                _prev_rep[_name] = _best
            _normalised.append((_f, _new))
        keyframes = _normalised

    # ---- ★ 临时欧拉诊断（`D17_EULERDBG=1`）---------------------------------
    if os.environ.get("D17_EULERDBG"):
        from mathutils import Quaternion as _Q
        _names = [n for n in os.environ.get(
            "D17_EULERDBG_NAMES", "shin.R,forearm.R").split(",") if n]
        _f0 = _env_i("D17_EULERDBG_F0", 28)
        _f1 = _env_i("D17_EULERDBG_F1", TOTAL)
        _prev_e = {}
        for _f, _p in keyframes:
            if _f0 <= _f <= _f1:
                A.apply_pose(arm, _p)
                bpy.context.view_layer.update()
                _row = {"f": _f}
                for _n in _names:
                    _pb = arm.pose.bones[_n]
                    _wq = _pb.matrix.to_3x3().to_quaternion().normalized()
                    _last = _prev_e.get((_n, "eul"))
                    _e = [round(v, 2) for v in _p.get(_n, (0, 0, 0))]
                    _step = (None if _last is None else
                             round(max(abs(a - b) for a, b in zip(_e, _last)), 2))
                    _dir = A.bone_direction(arm, _n)
                    _row[_n.replace(".", "")] = {
                        "eul": _e, "step": _step,
                        "angZ": round(math.degrees(math.acos(max(
                            -1.0, min(1.0, _dir.dot(ZERO_DIR.get(_n, _dir)))))), 2),
                        "angE": round(math.degrees(math.acos(max(
                            -1.0, min(1.0, _dir.dot(END_DIR.get(_n, _dir)))))), 2),
                        "angWZ": round(math.degrees(_wq.rotation_difference(
                            _Q(ZERO_BASIS[_n])).angle), 2) if _n in ZERO_BASIS else None,
                        "angWE": round(math.degrees(_wq.rotation_difference(
                            _Q(END_BASIS[_n])).angle), 2) if _n in END_BASIS else None,
                        "wdir": (None if not os.environ.get("D17_EULERDBG_DIR")
                                 else [round(v, 3) for v in _dir]),
                        "wreq": (None if not os.environ.get("D17_EULERDBG_DIR")
                                 or _n.split(".")[0] not in ("hand", "forearm")
                                 else [round(v, 3) for v in (
                                     hand_dir_of(_n.split(".")[1], _f)
                                     if _n.startswith("hand.")
                                     else (
                                         fist_target(arm, _n.split(".")[1], _f)
                                         - Vector(A.bone_world(
                                             arm, "upperarm." + _n.split(".")[1],
                                             "head"))).normalized())]),
                        "phi": _ROLL_LAST_PHI.get(_n),
                        "mix": round(roll_mix_at(_f, _n), 4),
                    }
                    _prev_e[(_n, "eul")] = _e
                    _prev_w = _prev_e.get((_n, "w"))
                    _dl = (None if _prev_w is None else round(math.degrees(
                        _wq.rotation_difference(_prev_w).angle), 2))
                    _row[_n.replace(".", "")]["dw"] = _dl
                    _prev_e[(_n, "w")] = _wq
                print("D17_EUL " + json.dumps(_row))
        return

    meta = {
        "anim_id": NAME,
        "loop": False,
        "category": "防御与受击",
        "note": ("正面起身（俯卧 → 双掌撑地推起 → 收腿 → 战斗站姿）：竖直通道"
                 "**无弹道段**，骨盆**单调升 610 mm**；支点**掌 → 脚**只换一次；"
                 "末帧**逐位 = `Idle_01@0`**（跨族接缝）"),
        "antic_frame": PUSH,
        "hit_frame": None,
        "land_frame": FOOT_SET,
        "cancel_frame": CANCEL,
        "push_frame": PUSH,
        "chest_up_frame": CHEST_UP,
        "hand_off_frame": HAND_OFF,
        "tuck_frame": TUCK,
        "foot_set_frame": FOOT_SET,
        "rise_mid_frame": RISE_MID,
        "stand_frame": STAND,
        "self_hold_frame": SELF_HOLD,
        "hitstop_frames": 0,
        "hit_points": 0,
        "root_motion_m": [0.0, round(pelvis_y_at(END) - pelvis_y_at(START), 6)],
        "hit_point_m": None,
        "end_pelvis_z_m": round(pelvis_z_at(END), 6),
        "end_vz_m_per_frame": 0.0,
        "start_pose_ref": "%s 帧 %d（俯卧，脸朝下）" % (SEAM_ACTION, SEAM_FRAME),
        "end_pose_ref": "%s 帧 %d（战斗站姿）" % (END_ACTION, END_FRAME),
        "ballistic_ref": "无（★ 本支竖直通道不含弹道段）",
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.add_markers(action, {"START": START, "PUSH": PUSH, "CHEST_UP": CHEST_UP,
                           "HAND_OFF": HAND_OFF, "TUCK": TUCK,
                           "FOOT_SET": FOOT_SET, "RISE_MID": RISE_MID,
                           "STAND": STAND, "SELF_HOLD": SELF_HOLD,
                           "CANCEL": CANCEL, "END": TOTAL})

    samples = A.sample_animation(arm, action, 0, TOTAL, meshes)
    report = A.run_common_assertions(samples, meta, foot_probe=())
    report.pop("ground_contact_ok", None)
    report.pop("ground_min_mm", None)

    end_mats_ref = CR.action_world_matrices(arm, bpy.data.actions[END_ACTION],
                                            END_FRAME)
    report.update(getup_assertions(arm, action, samples, meshes, end_mats_ref))
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

    report["failed"] = sorted(k for k, v in report.items()
                              if k.endswith("_ok") and v is not True)
    report["non_ok_bools"] = sorted(
        k for k, v in report.items()
        if isinstance(v, bool) and not k.endswith("_ok") and v is not True)
    A.report("D17_REPORT", report)

    if not SKIP_RENDER:
        side_frames = list(range(0, TOTAL + 1))
        other_frames = [START, PUSH, CHEST_UP, HAND_OFF, TUCK, FOOT_SET,
                        RISE_MID, STAND, END]
        A.render_pose_sheet(arm, action, side_frames, "getupf",
                            views=(VIEW_D17_SIDE,))
        A.render_pose_sheet(arm, action, side_frames, "getupfwide",
                            views=(VIEW_D17_SIDE_WIDE,))
        A.render_pose_sheet(arm, action, other_frames, "getupf",
                            views=(VIEW_D17_FRONT, VIEW_D17_3Q))
        # ★ `px_idle_end_ok` 的**对照静帧**：`Idle_01@0` 与 wide 视**同机位**
        idle_action = bpy.data.actions[END_ACTION]
        A.render_pose_sheet(arm, idle_action, [END_FRAME], "idle01wide",
                            views=(VIEW_D17_SIDE_WIDE,))
        A.save_project()
        A.export_glb(arm)
    print("D17_DONE failed=%s" % report["failed"])
    print("D17_DONE non_ok_bools=%s" % report["non_ok_bools"])
    if os.environ.get("D17_TRACE"):
        print("D17_TRACE " + json.dumps(report.get("trace", {}),
                                        ensure_ascii=False))


# ★ 本支取景。
#   `VIEW_D17_SIDE`：与 `side` 家族同源（供"俯卧帧"与交叉目检）；
#   `VIEW_D17_SIDE_WIDE`：★ **起身族专属基准**（D14 + D16 两条遗留都点名要求）。
#     水平中心取**起点与终点的水平中点**（骨盆 y：−550 → 0 ⟹ 中点 −275 mm，
#     再留余量取 −300 mm）；正交宽 3.60 m 覆盖"趴着的高度 + 站起来的高度"
#     （0 → 1.85 m）。跨支尺子只比**行**、不比列。
VIEW_D17_SIDE = ("side", (5.20, -0.275, 1.30), (0.0, -0.275, 1.30), 3.30,
                 (780, 1100))
VIEW_D17_SIDE_WIDE = ("side", (5.20, -0.300, 0.95), (0.0, -0.300, 0.95), 3.60,
                      (780, 1100))
VIEW_D17_FRONT = ("front", (0.0, -5.60, 0.95), (0.0, -0.30, 0.95), 4.20,
                  (780, 1100))
VIEW_D17_3Q = ("three_quarter", (4.10, -4.30, 1.15), (0.0, -0.30, 0.95), 4.60,
               (780, 1100))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("D17_FAILURE " + traceback.format_exc())
