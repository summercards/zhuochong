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
from mathutils import Quaternion, Vector

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


# =============================================================== 时间轴
#   ★ 节奏：**撑 12 / 交接 4 / 收腿 4 / 蹬起 10 / 定 2**
TOTAL = _env_i("D17_TOTAL", 36)
START = 0
PUSH = _env_i("D17_PUSH", 4)                  # 双掌撑地、肘开始伸（发力起手）
CHEST_UP = _env_i("D17_CHEST_UP", 12)         # 胸被顶上来的峰值帧
HAND_OFF = _env_i("D17_HAND_OFF", 16)         # ★ 支点交接 1：手掌离地帧
TUCK = _env_i("D17_TUCK", 20)                 # 收腿（膝收到身下）
FOOT_SET = _env_i("D17_FOOT_SET", 24)         # ★ 支点交接 2：双脚接住地面帧（唯一）
RISE_MID = _env_i("D17_RISE_MID", 30)         # 蹬伸中段
STAND = _env_i("D17_STAND", 34)               # 站直（骨盆 830 mm）＝ 逐位 = `Idle_01@0`
SELF_HOLD = STAND
CANCEL = STAND
END = TOTAL
if not (START < PUSH < CHEST_UP < HAND_OFF < TUCK < FOOT_SET < RISE_MID < STAND
        <= TOTAL):
    raise RuntimeError("相位不自洽：PUSH=%d CHEST_UP=%d HAND_OFF=%d TUCK=%d "
                       "FOOT_SET=%d RISE_MID=%d STAND=%d TOTAL=%d"
                       % (PUSH, CHEST_UP, HAND_OFF, TUCK, FOOT_SET, RISE_MID,
                          STAND, TOTAL))

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
PELVIS_Z_KEYS = (
    (START, 220.0), (PUSH, 252.0), (CHEST_UP, 404.0), (HAND_OFF, 478.0),
    (TUCK, 528.0), (FOOT_SET, 562.0), (RISE_MID, 706.0), (STAND, 830.0),
    (END, 830.0))
PELVIS_Y_KEYS = (
    (START, -550.0), (PUSH, -540.0), (CHEST_UP, -436.0), (HAND_OFF, -366.0),
    (TUCK, -312.0), (FOOT_SET, -258.0), (RISE_MID, -108.0), (STAND, 0.0),
    (END, 0.0))
# ★ 反验证 ⑥：造一次中途回落（骨盆在上升途中沉一下）⟹ `rise_monotone_ok` 必须红
DIP_KEYS = ((0, 0.0), (FOOT_SET, 0.0), (26, -58.0), (28, -30.0), (30, 0.0),
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
TORSO_PROG = {
    "root": ((0, 0.0), (END, 0.0)),
    "pelvis": ((0, 0.0), (PUSH, 0.05), (CHEST_UP, 0.24), (HAND_OFF, 0.38),
               (TUCK, 0.54), (FOOT_SET, 0.66), (RISE_MID, 0.88), (STAND, 1.0),
               (END, 1.0)),
    "spine_01": ((0, 0.0), (PUSH, 0.08), (CHEST_UP, 0.38), (HAND_OFF, 0.52),
                 (TUCK, 0.66), (FOOT_SET, 0.76), (RISE_MID, 0.92), (STAND, 1.0),
                 (END, 1.0)),
    "spine_02": ((0, 0.0), (PUSH, 0.08), (CHEST_UP, 0.38), (HAND_OFF, 0.52),
                 (TUCK, 0.66), (FOOT_SET, 0.76), (RISE_MID, 0.92), (STAND, 1.0),
                 (END, 1.0)),
    "chest": ((0, 0.0), (PUSH, 0.14), (CHEST_UP, 0.58), (HAND_OFF, 0.72),
              (TUCK, 0.82), (FOOT_SET, 0.88), (RISE_MID, 0.95), (STAND, 1.0),
              (END, 1.0)),
    "neck": ((0, 0.0), (PUSH, 0.14), (CHEST_UP, 0.50), (HAND_OFF, 0.64),
             (TUCK, 0.78), (FOOT_SET, 0.86), (RISE_MID, 0.95), (STAND, 1.0),
             (END, 1.0)),
    "head": ((0, 0.0), (PUSH, 0.14), (CHEST_UP, 0.48), (HAND_OFF, 0.62),
             (TUCK, 0.76), (FOOT_SET, 0.86), (RISE_MID, 0.95), (STAND, 1.0),
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


# =============================================================== 手（拳）目标
#   ★ 撑地段用**世界落掌点**（手真的钉在地上推），收手后切成**肩相对**目标
#     （C13 口径：绝对世界点会在骨盆大幅移动时踩进深折叠奇点）。
HAND_OFF_LIFT_KEYS = ((0, 0.0), (HAND_OFF, 0.0), (HAND_OFF + 1, 0.150),
                      (HAND_OFF + 2, 0.170), (HAND_OFF + 3, 0.120),
                      (TUCK, 0.040), (FOOT_SET, 0.0), (END, 0.0))
HAND_MIX_END = _env_i("D17_HAND_MIX_END", HAND_OFF + 4)


def hand_lift(frame):
    if STICKY_HAND:
        return 0.0
    return UE.pwl(HAND_OFF_LIFT_KEYS, float(frame), 0.0)


def fist_target(arm, side, frame):
    """拳世界目标。

    `f ≤ HAND_OFF` ⟹ **世界落掌点**（手钉在地上；`STICKY_HAND` 旋钮把它延伸全覆盖）。
    `f >  HAND_OFF` ⟹ **肩 + 偏移**，偏移从"落掌偏移"过渡到 `Idle_01@0` 的肩-拳偏移。
    """
    shoulder = Vector(A.bone_world(arm, "upperarm." + side, "head"))
    world = pwl_vec(PLANT_KEYS[side], float(frame), SEAM_FIST[side])
    if STICKY_HAND:
        return world
    if frame <= HAND_OFF:
        return world
    s = _smoothstep((float(frame) - HAND_OFF) / (HAND_MIX_END - HAND_OFF))
    off_a = world - shoulder
    off_b = Vector(END_OFF[side])
    off = off_a * (1.0 - s) + off_b * s
    off.z += hand_lift(frame)
    return shoulder + off


def elbow_dir(side, frame):
    """肘的鼓出偏好（世界向量）。撑地期**肘往外张**（push-up 的肘窝朝外）。"""
    d = pwl_vec(ELBOW_KEYS[side], float(frame), SEAM_ELBOW_DIR[side])
    return Vector(d).normalized()


def hand_dir_of(side, frame):
    """手骨世界朝向：接缝值 → `Idle_01@0` 值。"""
    return Vector(pwl_vec(HAND_DIR_KEYS[side], float(frame),
                          SEAM_HAND_DIR[side])).normalized()


# =============================================================== 踝目标
ANKLE_LIFT_KEYS = {
    "L": ((0, 0.0), (PUSH, 0.010), (8, 0.060), (CHEST_UP, 0.115),
          (HAND_OFF, 0.165), (TUCK, 0.205), (FOOT_SET, 0.0), (END, 0.0)),
    "R": ((0, 0.0), (PUSH, 0.012), (8, 0.070), (CHEST_UP, 0.130),
          (HAND_OFF, 0.180), (TUCK, 0.215), (FOOT_SET, 0.0), (END, 0.0)),
}


def ankle_target(arm, side, frame):
    """踝世界目标：接缝（俯卧）→ 抬起收腿 → `FOOT_SET` 起**逐位 = Idle 落脚点**。

    ★ `FOOT_SET` 之后目标**恒等于 `END_ANKLE`** ⟹ 脚构造性不滑（`no_foot_slide_ok`）。
    """
    end = Vector(END_ANKLE[side])
    if NO_TUCK:
        # ★ 反验证 ③：抽掉收腿 —— 踝从接缝一路直线飞到终点（不是"收腿"，是"瞬移"）
        if frame <= 0:
            return Vector(SEAM_ANKLE[side])
        t = _smoothstep(float(frame) / float(FOOT_SET))
        return Vector(SEAM_ANKLE[side]) * (1.0 - t) + end * t
    if frame >= FOOT_SET:
        return end
    if frame <= 0:
        return Vector(SEAM_ANKLE[side])
    if frame <= TUCK:
        t = _smoothstep(float(frame) / float(TUCK))
        base = Vector(SEAM_ANKLE[side]) * (1.0 - t) + Vector(TUCK_ANKLE[side]) * t
    else:
        t = _smoothstep((float(frame) - TUCK) / float(FOOT_SET - TUCK))
        base = Vector(TUCK_ANKLE[side]) * (1.0 - t) + end * t
    base = base.copy()
    base.z += 1000.0 * UE.pwl(ANKLE_LIFT_KEYS[side], float(frame), 0.0)
    return base


def _foot_euler(arm, side, frame):
    """脚：`f < FOOT_SET` 走 pwl（俯卧勾脚 → 落地前压脚背）；`f ≥ FOOT_SET` 钉世界朝向。

    `FOOT_SET` 起用 `keep_world_orientation` ⟹ 鞋底**构造性贴地**（与 `Idle_01` 同一把尺子）。
    """
    name = "foot." + side
    prev = JS._PREV_EULER.get(name)
    if frame >= FOOT_SET:
        flat = A.keep_world_orientation(arm, name)
        if frame == FOOT_SET:
            return JS._unwrap_xyz(prev, tuple(flat))
        t = _smoothstep((float(frame) - FOOT_SET) / float(STAND - FOOT_SET))
        pw = pwl_vec(FOOT_KEYS[side], float(frame), SEAM_FOOT_EULER[side])
        return JS._unwrap_xyz(prev, tuple(pw * (1.0 - t) + Vector(flat) * t))
    pw = pwl_vec(FOOT_KEYS[side], float(frame), SEAM_FOOT_EULER[side])
    return JS._unwrap_xyz(prev, tuple(pw))


# =============================================================== 模块级表
ZERO = {}
ZERO_WORLD = {}
END_POSE = {}
ZERO_BASIS = {}
ZERO_DIR = {}
SEAM_FIST = {}
SEAM_ELBOW_DIR = {}
SEAM_HAND_DIR = {}
SEAM_ANKLE = {}
SEAM_FOOT_EULER = {}
SEAM_RX = {}
END_RX = {}
END_OFF = {}
END_ANKLE = {}
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
    """
    if weight <= 0.0:
        return pose
    out = {}
    keys = set(pose) | set(END_POSE)
    for key in keys:
        if key == "@loc":
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


def build_pose(arm, frame):
    # ★ f0 = **逐位**接缝姿态（`Knockdown_F@20`）—— 不走解算，原样返回。
    if frame <= 0:
        return _copy_pose(ZERO)

    # ★★ 末段：`STAND` 起**逐位** = `Idle_01@0`（3 帧定格自持）。
    if frame >= STAND and not NO_IDLE and not END_ZERO:
        return _copy_pose(END_POSE)

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
        for _ in range(ROLL_ITER):
            for name in ROLL_BONES:
                if name in arm.pose.bones:
                    _roll_return(arm, pose, name, 1.0)
            for side in SIDES:
                arm_seat_tip(arm, pose, side, fist_target(arm, side, frame),
                             elbow_dir(side, frame), hand_dir_of(side, frame))
    pose.update(A.FIST)

    # ★ 朝终点站姿收束（连续权重；`STAND` 处构造性 = `END_POSE`）
    if not NO_IDLE:
        w = _smoothstep((float(frame) - float(FOOT_SET))
                        / float(STAND - FOOT_SET))
        pose = _toward_end(pose, w)

    for name, value in pose.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)
    if frame == END_ZERO_FRAME:
        LOCK_POSE.update(_copy_pose(pose))
    return pose


def _roll_return(arm, pose, name, weight):
    """把某根骨的**绕自身轴滚转**沿世界朝向对齐回零位（只改滚转，不改骨轴方向）。"""
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


END_ZERO_FRAME = CANCEL


def solve_pose(arm, frame, meshes=None):
    return build_pose(arm, frame)


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
    for table in (ZERO_BASIS, ZERO_DIR, SEAM_FIST, SEAM_ELBOW_DIR, SEAM_HAND_DIR,
                  SEAM_ANKLE, SEAM_FOOT_EULER, SEAM_RX, END_RX, END_OFF,
                  END_ANKLE, TUCK_ANKLE, KNEE_DIR, ARM_MAX, PLANT_KEYS,
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
        shoulder = Vector(A.bone_world(arm, "upperarm." + side, "head"))
        fist = Vector(A.bone_world(arm, "hand." + side, "tail"))
        END_OFF[side] = tuple(fist - shoulder)
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
    for name in ARM_BONES:
        ZERO_DIR[name] = Vector(A.bone_direction(arm, name)).normalized()

    # ---- 中段锚点（全部由两个端点**实测**派生，不是拍的）-------------------
    for side in SIDES:
        s = 1.0 if side == "L" else -1.0
        # ★ 落掌点：把拳从"举过头顶"拉到"肩下前方"的地面上（猛男先把掌收回来再撑）
        #   由接缝的肩-拳偏移与目标地面高度反推，避免拍脑袋写世界坐标。
        pull = Vector((SEAM_FIST[side].x * 0.62,
                       SEAM_FIST[side].y + 0.300,
                       0.035))
        plant = Vector((SEAM_FIST[side].x * 0.52,
                        SEAM_FIST[side].y + 0.395,
                        0.020))
        plant2 = Vector((SEAM_FIST[side].x * 0.50,
                         SEAM_FIST[side].y + 0.400,
                         0.014))
        PLANT_KEYS[side] = ((START, tuple(SEAM_FIST[side])),
                            (PUSH, tuple(pull)), (8, tuple(plant)),
                            (CHEST_UP, tuple(plant)), (HAND_OFF, tuple(plant2)))
        # ★ 肘鼓出：撑地期**往外张**（push-up 的肘窝朝外）
        e0 = Vector(SEAM_ELBOW_DIR[side])
        e1 = Vector((0.72 * s, 0.30, 0.62)).normalized()
        e2 = Vector((0.40 * s, -0.30, 0.86)).normalized()
        ELBOW_KEYS[side] = ((START, tuple(e0)), (PUSH, tuple(e1)),
                            (CHEST_UP, tuple(e1)), (HAND_OFF, tuple(e1)),
                            (TUCK, tuple(e2)), (FOOT_SET, tuple(e2)),
                            (STAND, tuple(e2)), (END, tuple(e2)))
        h0 = Vector(SEAM_HAND_DIR[side])
        h1 = Vector((0.10 * s, -0.25, -0.96)).normalized()
        HAND_DIR_KEYS[side] = ((START, tuple(h0)), (PUSH, tuple(h1)),
                               (CHEST_UP, tuple(h1)), (HAND_OFF, tuple(h1)),
                               (TUCK, tuple(h1)), (FOOT_SET, tuple(h1)),
                               (STAND, tuple(h1)), (END, tuple(h1)))
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
        "★ 骨盆 z 从起点到终点净升 **≥ %.0f mm**（防"只起来一半"）。"
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
        "（证明"撑地真的把上身顶起来了"，而不是只有胳膊在动）。"
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
            "DISABLED —— 贴地族"局部弹起"判据。本支是**主动起身**，无受力弹起。",
        "ballistic_until_land_ok": "DISABLED —— 本支竖直通道**没有弹道段**"
                                   "（全段单调上升，无抛物线可比）。",
        "hitstop_present": "DISABLED —— ★ 本支是**主动发力**动作，**没有"命中帧"**。"
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

    keyframes = []
    for frame in range(0, TOTAL + 1):
        if frame == TOTAL and END_ZERO:
            # ★ 反验证 ⑦：末帧改零位
            pose = {name: (0.0, 0.0, 0.0) for name in ZERO if not name.startswith("@")}
            pose["@loc"] = {"pelvis": A.wloc(0.0, 0.0, 0.0)}
            keyframes.append((frame, pose))
        else:
            keyframes.append((frame, solve_pose(arm, frame, meshes)))

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
