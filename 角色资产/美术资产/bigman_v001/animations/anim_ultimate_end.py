"""anim_ultimate_end —— C14 `Ultimate_End` 大招收尾
（本族最后一支「为**定格英雄 Pose**而做」的支）。

目录：`doc/动画制作清单.md` 第 140 行；详细计划见该文件的
「下一支详细制作计划 —— C14 `Ultimate_End` 大招收尾」。

清单原文：「最后一击后保持英雄 Pose 约 0.3~0.6 秒，再恢复战斗姿态。」

================================================================ 本支的物理构造

**1 段（无节奏维度）+ 长定格 + 收招（72 帧 / 1.200 s @60fps）**：

    0 ──3── 起手接合（f0 **逐位** = `Idle_01@0`，f1..2 臂欧拉自 Idle 接到逆解）
    3 ─10── 沉收（骨盆 −48 mm、含胸 +7°、肩沉 −22°）—— "启动略慢"的蓄势
    10─12── 沉收停顿（**逐位冻结** 2 帧 —— 静→动的重音）
    12─22── 爆发起身 → 挺胸 + 右拳扬起斜上 + 左拳垂体侧（**英雄 Pose 到位**）
    22─50── ★★ **定格窗 29 帧**（0.483 s，逐位冻结同一 `dict`）
    50─66── 收招（全姿仿射回 `Idle_01@0`；腿分层 + 根骨竖直贴地补偿）
    66─72── 静止（6 帧 ⟹ 末 2 帧步长构造性 = 0）

==================== 位姿来源（**先量再定**，第 1~17 轮探针）

`probe_c14_pose.py` 扫了 17 轮共 60+ 个候选（收拳于腰侧 / 单臂上举 / 双臂下压 /
侧身亮相 / 冲天拳 / 宽站架 …），用**正视剪影指标 × 目检侧视图**双重筛。

★ 三条实测结论（都写进了探针头注，也决定了本支的最终位姿）：

1. **「纵横比」与「填充率」在英雄 Pose 上是拮抗的**（把宽度从 0.58 m 推到 0.88 m
   必然在包围盒里加进空白）⟹ C12 的 `ar≥1.30 且 fr≥0.80` 三线合取式在本支**不可达**，
   阈值必须按本支重定。
2. **竖直臂不买宽度** ⟹ `aspect` 单用会把"竖直英雄 Pose"判死（冲天拳族 ar 仅
   1.04~1.20）。必须**配 fr 一起用**。
3. ★★ **`plant_ok` 要求踝水平位移 ≤ 3 mm** ⟹ 站姿**不许挪脚**，踝目标钉在
   `ANKLE_0`（Idle 的 −0.170 / +0.140）。探针里所有"宽站架"候选**在主脚本里拿不到**
   （第 16 轮发现，前 15 轮的站架增益作废）—— 最终位姿一律用 **Idle 原站架**。

★ 同时目检否掉了：`lat_spread`（读成"准备开打"不像胜利）、`T-pose` 陷阱
（`F_spread` ar 2.09 但臂轴近水平 ≡ rest T-pose）、`raise_both`（双拳夹头，头被埋）。

最终定稿 **`y38_fin`**（探针 `C14_PROBE_FINAL`，真值照抄进 `HAND_HERO`/`TORSO_*`）：
右拳扬到 `(−0.380, −0.080, 1.860)`（**肩部相对** `u=(−0.437, −0.181, 0.881)`、
`len = 561.967 mm`）、左拳垂到 `(0.300, 0.020, 0.740)`、躯干右拧 15°、
骨盆 815 mm（比 Idle 低 15 mm）。
★ **前臂近乎竖直 ⟹ 主视角（2.5D 横版 = **侧视**）里拳在头**上方外侧**，不横越头部**
（前 15 轮的 `sky_hip` 族侧视里臂横过脸，正是被目检否掉的）。

==================== 本支新立的 4 条判据（计划 §2，全部必须会失败）

| 判据 | 口径 | 失败模式 |
|---|---|---|
| `hero_pose_hold_ok` | 定格窗 18~36 帧内**逐位冻结**（`pose_hold_worst_mm = 0.0`，靠构造） | 「定格还在飘」/「窗太短或太长」 |
| `hero_silhouette_ok` | 定格帧的**正视剪影**：ar ≥ 1.12、fr ≥ 0.65、肩宽比 ≥ 0.88、头顶之上 ≤ 300 mm、重心在支撑面内 | 「判据全绿但 Pose 不帅」 |
| `exit_pose_ok` | `end_pose_delta_mm = 0.0`、末 2 帧步长 = 0、`settle` 单调递减 | 「收招没停住就断片」 |
| `resolve_ok` | 定格 → 收招的转折**不许硬切**：后 2 帧最大骨世界步长 ≤ 3× 起身段的最大步长 | 「定格完突然弹回」 |

★ `hero_silhouette_ok` 的阈值**重新校准过**（不做 C12 的 ×1.30/×0.80/×0.90 照抄）：
基准是**本支 `Idle_01@0` 的正视剪影**（ar ≡ 1.00 / fr ≡ 1.00 / 肩宽比 ≡ 1.00）。
定稿 `y38_fin` 实测 ar **1.1874** / fr **0.7583** / 肩宽比 **0.9373** ⟹ 阈值取
1.12 / 0.65 / 0.88（各留 ~7~15% 余量，口径差 70 mm 也不会误红，见 C12 第 1 号教训）。
★ 其中"头顶之上 ≤ 300 mm"这一条是**修正探针第 1 版口径**得来的：最初量"最高点的 x
贴近头骨 x"，但**单臂过顶**天然会高出头顶 500+ mm（合法胜利 Pose 被误杀）；
改量**头顶之上还压着多少东西** —— `raise_both`（双拳夹头）会远超 300 mm ⟹ 判负。

==================== 撤下的判据（C13 专属）

`rhythm_*` / `hitstop_*` / `chain_per_hit_ok` / `segment_count_ok` /
`hitframe_registered_ok` / `press_ok` —— 本支 **0 命中点、0.0 mm 位移**、只有 1 段。
保留 `camera_facing_ok`（躯干 15°、头 3°，≤ 20° ✓）。

==================== 复用件（不重写）

  `anim_lib`：全部基础件。
  `anim_grab04`：`leg_seat` / `arm_seat` / `aim_bone_ref`。
  `anim_jump_start`：`_unwrap_xyz` / `_PREV_EULER`。
  `anim_run_stop`：`smooth`。
  `anim_ultimate_start`（C12）：**PCHIP 版 `pwl`**、`recover_pose` 的**腿分层 +
    根骨竖直贴地补偿**、`frame_series` / `silhouette_now` / `silhouette_at`。
  `anim_ultimate_attack`（C13）：★ **位置口径臂 IK**（`arm_seat`）、
    `_set_euler_nearest`（万向节锁防御）、`aim_nearest`（**接力版**，避开固定基准
    反平行奇点）、`solve_pose` 的 `rebuild()` 重启、`push_shoulder`、`chain_keys` 的
    `deg_*` / `tail_*` 通道。
  `probe_c14_pose`：★ **英雄 Pose 真值**（不重测）。

============================== 调试开关（环境变量，无需改文件）

  SKIP_RENDER=1     跳过渲染 + 存盘 + 导出（迭代期用）
  C14_TRACE=1       逐帧：骨盆 / 双拳 / 鞋底 / 关键欧拉角
  C14_STEP=1        逐帧最大欧拉步长（>15° 才打印）—— `no_teleport` 的定位工具
  C14_SIL=1         逐帧正视剪影（ar / fr / 宽高）

运行（正式那一轮）：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python anim_ultimate_end.py
"""

import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A              # noqa: E402
import anim_idle_01 as I1         # noqa: E402
import anim_grab04 as G4          # noqa: E402
import anim_run_stop as RS        # noqa: E402
import anim_jump_start as JS      # noqa: E402
import anim_ultimate_start as US  # noqa: E402
import probe_c12_baseline as P    # noqa: E402

NAME = "Ultimate_End"
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"
SIDES = ("L", "R")


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


# =============================================================== 时间轴
TOTAL = _env_i("C14_TOTAL", 72)              # 1.200 s @60fps（计划要 0.8~1.4 s）
EASE_END = _env_i("C14_EASE", 3)             # 起手接合
SINK_END = _env_i("C14_SINK", 10)            # 沉收到底
SINK_HOLD = _env_i("C14_SINKHOLD", 2)        # 沉收停顿帧数（逐位冻结）
SINK_HOLD_END = SINK_END + SINK_HOLD         # 12
POSE = _env_i("C14_POSE", 22)                # ★ 定格窗首帧（英雄 Pose 到位）
HOLD_END = _env_i("C14_HOLDEND", 50)         # ★ 定格窗末帧（22..50 = 29 帧）
RECOVER = HOLD_END                           # 收招起点
SETTLE_END = _env_i("C14_SETTLE", 66)        # 收招位移完成帧（此后逐位静止）
CANCEL = _env_i("C14_CANCEL", 60)            # 可取消帧

# =============================================================== 阈值（全部会失败）
SOLE_RANGE_MM = (-2.0, 6.0)
NO_TELEPORT_MAX_DEG = 25.0
SEAM_TOL = 1e-6
REACH_MAX_RATIO = 0.995
PLANT_MAX_MM = _env_f("C14_PLANT_MAX", 3.0)
GROUND_MIN_MM = -2.0
GROUND_MAX_MM = 6.0
HOLD_MAX_MM = _env_f("C14_HOLD_MAX", 2.0)
HOLD_FRAME_MIN = _env_i("C14_HOLD_FMIN", 18)     # 0.300 s @60fps
HOLD_FRAME_MAX = _env_i("C14_HOLD_FMAX", 36)     # 0.600 s @60fps
SIL_ASPECT_MIN = _env_f("C14_SIL_ASPECT", 1.12)  # 定稿实测 1.1874
SIL_FILL_MIN = _env_f("C14_SIL_FILL", 0.65)      # 定稿实测 0.7583
SIL_SHOULDER_MIN = _env_f("C14_SIL_SHOULDER", 0.88)   # 定稿实测 0.9373
ABOVE_HEAD_MAX_MM = _env_f("C14_ABOVE_HEAD", 300.0)   # 定稿实测 188.7
CAMERA_MAX_DEG = _env_f("C14_CAMERA", 20.0)
END_POSE_TOL_MM = _env_f("C14_ENDTOL", 0.5)
SETTLE_LAST2_MAX_MM = _env_f("C14_LAST2", 0.5)
RESOLVE_RATIO_MAX = _env_f("C14_RESOLVE", 3.0)

ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")
LEG_BONES = ("thigh.L", "shin.L", "thigh.R", "shin.R")
TARGET_BONES = ("pelvis", "spine_01", "spine_02", "chest", "neck", "head",
                "shoulder.L", "shoulder.R")
HEM_EXCLUDE = P.HEM_EXCLUDE
SIL_TORSO_RY = ("pelvis", "spine_01", "spine_02", "chest")

# =============================================================== 探针真值（照抄）
# ★ 来源：`probe_c14_pose.py` 第 16 轮 `C14_PROBE_FINAL {"key": "y38_fin", ...}`
#   `rel[side] = (肩→拳 单位方向, 肩→拳 长度 mm)`；`torso` = 定格帧的躯干欧拉。
HAND_HERO = {
    "R": ((-0.437134, -0.180534, 0.881091), 561.967),
    "L": ((0.249596, 0.113436, -0.961683), 608.557),
}
ELBOW_HERO = {
    "R": (-0.457604, 0.849837, -0.261488),
    "L": (0.319680, 0.399601, -0.859141),
}
TORSO_HERO = {
    "pelvis": (3.0, -5.0, 0.0),
    "spine_01": (0.0, -3.0, 0.0),
    "spine_02": (0.0, -3.0, 0.0),
    "chest": (-6.0, -4.0, 0.0),
    "neck": (-6.0, 6.0, 0.0),
    "head": (6.0, 6.0, 0.0),
    "shoulder.L": (-4.0, 0.0, 0.0),
    "shoulder.R": (16.0, 0.0, 0.0),
}
HERO_PZ_MM = -15.0          # 探针 drop −0.085 − Idle −0.070 = −0.015 m
SINK_PZ_MM = _env_f("C14_SINKPZ", -48.0)
YAW_W = {"pelvis": 1.0, "spine_01": 1.0, "spine_02": 1.0, "chest": 1.0}
YAW_CNT = {"neck": 1.0, "head": 1.0}

# =============================================================== 信封（曲线）
# ★ 一切在 f0 取 `SEAM_EULER`（= `Idle_01@0` 真值）、在 `POSE..RECOVER` 取
#   **定格真值**（逐位平直）⟹ 首帧逐位 = Idle、定格窗逐位冻结，都是构造性的。
PZ_KEYS = ((0, None), (SINK_END, SINK_PZ_MM), (SINK_HOLD_END, SINK_PZ_MM),
           (POSE, HERO_PZ_MM), (RECOVER, HERO_PZ_MM))
PELVIS_RX = ((0, None), (SINK_END, 8.0), (SINK_HOLD_END, 8.0),
             (POSE, 3.0), (RECOVER, 3.0))
SPINE_RX = ((0, None), (SINK_END, 5.0), (SINK_HOLD_END, 5.0),
            (POSE, 0.0), (RECOVER, 0.0))
CHEST_RX = ((0, None), (SINK_END, 7.0), (SINK_HOLD_END, 7.0),
            (POSE, -6.0), (RECOVER, -6.0))
NECK_RX = ((0, None), (SINK_END, -10.0), (SINK_HOLD_END, -10.0),
           (POSE, -6.0), (RECOVER, -6.0))
HEAD_RX = ((0, None), (SINK_END, 8.0), (SINK_HOLD_END, 8.0),
           (POSE, 6.0), (RECOVER, 6.0))
PELVIS_RY = ((0, None), (SINK_END, -2.0), (SINK_HOLD_END, -2.0),
             (POSE, -5.0), (RECOVER, -5.0))
SPINE_RY = ((0, None), (SINK_END, -1.0), (SINK_HOLD_END, -1.0),
            (POSE, -3.0), (RECOVER, -3.0))
CHEST_RY = ((0, None), (SINK_END, -1.0), (SINK_HOLD_END, -1.0),
            (POSE, -4.0), (RECOVER, -4.0))
NECK_RY = ((0, None), (SINK_END, 2.0), (SINK_HOLD_END, 2.0),
           (POSE, 6.0), (RECOVER, 6.0))
HEAD_RY = ((0, None), (SINK_END, 2.0), (SINK_HOLD_END, 2.0),
           (POSE, 6.0), (RECOVER, 6.0))
SHOULDER_RX = {
    "L": ((0, None), (SINK_END, -22.0), (SINK_HOLD_END, -22.0),
          (POSE, -4.0), (RECOVER, -4.0)),
    "R": ((0, None), (SINK_END, -22.0), (SINK_HOLD_END, -22.0),
          (POSE, 16.0), (RECOVER, 16.0)),
}
# 肩胛前送（世界 −Y 平移）—— 本支原地起 Pose，不用脉冲，恒 0（保留接口）。
SHOULDER_PUSH = {"L": ((0, 0.0),), "R": ((0, 0.0),)}
FOOT_LIFT_KEYS = {"L": ((0, 0.0),), "R": ((0, 0.0),)}
# 摆膝量：本支腿只靠 IK 随骨盆升降弯曲，不加侧向摆（0 全程）。
KNEE_LAT = ((0, 0.0),)

# =============================================================== 模块级表
SEAM_POSE = {}
SEAM_EULER = {}
Z_SEAM = 0.0
ANKLE_0 = {}
FOOT0 = {}
IDLE_HAND = {}
IDLE_HAND_OFF = {}
IDLE_ELBOW = {}
IDLE_KNEE = {}
IDLE_BASIS = {}
IDLE_DIR = {}
IDLE_KNEE_DIR = {}
ARM_LEN = {}
ARM_CLAMP = {}
HAND_DIR_KEYS = {}
HAND_LEN_KEYS = {}
ELBOW_KEYS = {}
ARM_REF = None
SIL_BASE = {}

pwl = US.pwl
pwl_vec = US.pwl_vec


def _lerp_dir(a, b, t):
    out = Vector(((1.0 - t) * a[0] + t * b[0],
                  (1.0 - t) * a[1] + t * b[1],
                  (1.0 - t) * a[2] + t * b[2]))
    if out.length < 1e-9:
        return tuple(b)
    return tuple(out.normalized())


def build_hand_keys():
    """按 `HAND_HERO` 与 `Idle_01@0` 现算手目标键（`None` ⟹ 取 Idle 真值）。

    ★ 中段键（`SINK_HOLD_END` = 22%，**在 `Idle → 英雄` 之间**）是为了给出
      "**启动略慢**"的速度剖面：PCHIP 在单调段切线非零，三点（Idle/22%/英雄）
      自然形成"慢起 → 加速 → 到位"的加速段，且不会在键处脉冲（C12 第 3 号教训）。
    """
    HAND_DIR_KEYS.clear()
    HAND_LEN_KEYS.clear()
    ELBOW_KEYS.clear()
    for side in SIDES:
        idle_u, idle_len = IDLE_HAND_OFF[side]
        hero_u, hero_len = HAND_HERO[side]
        mid_u = _lerp_dir(idle_u, hero_u, 0.22)
        mid_len = idle_len + (hero_len - idle_len) * 0.22
        HAND_DIR_KEYS[side] = ((0, None), (SINK_HOLD_END, mid_u),
                               (POSE, hero_u), (RECOVER, hero_u))
        HAND_LEN_KEYS[side] = ((0, None), (SINK_HOLD_END, mid_len),
                               (POSE, hero_len), (RECOVER, hero_len))
        ELBOW_KEYS[side] = ((0, None), (SINK_HOLD_END,
                                        _lerp_dir(IDLE_ELBOW[side],
                                                  ELBOW_HERO[side], 0.22)),
                            (POSE, ELBOW_HERO[side]),
                            (RECOVER, ELBOW_HERO[side]))


# =============================================================== 曲线取值
def pz_delta(f):
    """骨盆相对 Idle 的**竖直**增量（米）。两端为 0 ⟹ 首末帧逐位 = Idle。"""
    if f <= 0 or f >= TOTAL:
        return 0.0
    return pwl(PZ_KEYS, f, 0.0) / 1000.0


def press(f):
    """骨盆前后位移：本支**原地起 Pose**，恒 0（计划 §1：位移 0.0 mm）。"""
    return 0.0


def foot_lift(side, f):
    return pwl(FOOT_LIFT_KEYS[side], f, 0.0)


def hand_target(side, f):
    """**肩部相对**的手目标：`肩 + u·len`（C13 口径；绝对世界点会在躯干下沉时
    踩进深折叠奇点）。`None` ⟹ 取 Idle 的单位方向与臂长（mm）。"""
    u = Vector(pwl_vec(HAND_DIR_KEYS[side], f, IDLE_HAND_OFF[side][0]))
    if u.length < 1e-6:
        u = Vector(IDLE_HAND_OFF[side][0])
    u.normalize()
    length = pwl(HAND_LEN_KEYS[side], f, IDLE_HAND_OFF[side][1]) / 1000.0
    shoulder = Vector(A.bone_world(ARM_REF, "upperarm." + side, "head"))
    return tuple(shoulder + u * length)


def elbow_dir(side, f, shoulder=None, target=None):
    """肘的鼓出偏好：把 `ELBOW_KEYS` **投影到与臂轴垂直的平面**上（C13 口径）。"""
    prefer = Vector(pwl_vec(ELBOW_KEYS[side], f, IDLE_ELBOW[side]))
    if shoulder is None or target is None:
        return tuple(prefer.normalized())
    axis = (Vector(target) - Vector(shoulder))
    if axis.length < 1e-9:
        return tuple(prefer.normalized())
    axis.normalize()
    flat = prefer - axis * prefer.dot(axis)
    if flat.length < 1e-6:
        flat = Vector((0.0, 1.0, 0.0)) - axis * axis.y
        if flat.length < 1e-6:
            flat = Vector((0.0, 0.0, 1.0)) - axis * axis.z
    return tuple(flat.normalized())


def knee_dir(side, f):
    """绕「髋-踝轴」摆膝（`KNEE_LAT` 恒 0 ⟹ 纯 Idle 膝向）。"""
    lateral = pwl(KNEE_LAT, f, 0.0)
    sign = 1.0 if side == "L" else -1.0
    out = Vector((sign * lateral, 0.0, 0.0))
    base = Vector(IDLE_KNEE[side]) + out
    if base.length < 1e-6:
        base = Vector(IDLE_KNEE[side])
    return tuple(base.normalized())


def q_of(frame):
    """收招进度：0 = 定格末帧姿态，1 = `Idle_01@0`。

    沿用 C12：收招段用 `smoothstep`（两端速度都为 0），之后留**纯静止** ⟹
    末 2 帧步长构造性地 = 0（`settle_no_stop_ok` 的构造性来源）。
    """
    if frame <= RECOVER:
        return 0.0
    if frame >= SETTLE_END:
        return 1.0
    return RS.smooth((frame - RECOVER) / float(SETTLE_END - RECOVER))


def leg_weight(frame):
    """收招段的**腿分层**权重：0 = 纯 IK（钉地），1 = 纯欧拉仿射（保末帧 = Idle）。"""
    if frame <= RECOVER + 1:
        return 0.0
    if frame >= SETTLE_END:
        return 1.0
    return RS.smooth((frame - RECOVER - 1) / float(SETTLE_END - RECOVER - 1))


# =============================================================== 姿态装配
def torso_pose(f):
    pose = {}
    for name in TARGET_BONES:
        pose[name] = tuple(SEAM_EULER[name])
    pose["pelvis"] = (pwl(PELVIS_RX, f, SEAM_EULER["pelvis"][0]),
                      YAW_W["pelvis"] * pwl(PELVIS_RY, f, 0.0),
                      SEAM_EULER["pelvis"][2])
    pose["spine_01"] = (pwl(SPINE_RX, f, SEAM_EULER["spine_01"][0]),
                        YAW_W["spine_01"] * pwl(SPINE_RY, f, 0.0), 0.0)
    pose["spine_02"] = (pwl(SPINE_RX, f, SEAM_EULER["spine_02"][0]),
                        YAW_W["spine_02"] * pwl(SPINE_RY, f, 0.0), 0.0)
    pose["chest"] = (pwl(CHEST_RX, f, SEAM_EULER["chest"][0]),
                     YAW_W["chest"] * pwl(CHEST_RY, f, 0.0), 0.0)
    pose["neck"] = (pwl(NECK_RX, f, SEAM_EULER["neck"][0]),
                    YAW_CNT["neck"] * pwl(NECK_RY, f, 0.0), 0.0)
    pose["head"] = (pwl(HEAD_RX, f, SEAM_EULER["head"][0]),
                    YAW_CNT["head"] * pwl(HEAD_RY, f, 0.0), 0.0)
    for side in SIDES:
        name = "shoulder." + side
        pose[name] = (pwl(SHOULDER_RX[side], f, SEAM_EULER[name][0]),
                      SEAM_EULER[name][1], 0.0)
    # ★ 骨盆局部位移基线：`Z_SEAM + pz_delta − 0.900`（0.900 = **rest** 骨盆高度）。
    #   漏掉基线会让整条曲线比 Idle 高 70 mm、第 1 帧腿被拉直（C13 教训）。
    pose["@loc"] = {"pelvis": A.wloc(0.0, press(f),
                                     Z_SEAM + pz_delta(f) - 0.900)}
    return pose


def keep_foot_lifted(arm, side, lift_deg):
    """鞋朝向钉成 rest，再按 `foot.rx` 抬跟（`rx > 0` = 踮脚）。本支恒 0。"""
    name = "foot." + side
    pose_bone = arm.pose.bones[name]
    rest_basis = pose_bone.bone.matrix_local.to_3x3()
    current = pose_bone.matrix.copy()
    target = rest_basis.to_4x4()
    target.translation = current.translation
    pose_bone.matrix = target
    bpy.context.view_layer.update()
    if abs(lift_deg) > 1e-9:
        pose_bone.rotation_euler.rotate_axis("X", math.radians(lift_deg))
        bpy.context.view_layer.update()
    return tuple(math.degrees(v) for v in pose_bone.rotation_euler)


def push_shoulder(arm, side, push_mm, pose):
    """肩胛骨**前送**（世界 −Y 平移）。★ 位移必须写回 `pose["@loc"]`，否则打帧时丢掉。"""
    name = "shoulder." + side
    locations = pose.setdefault("@loc", {})
    if abs(push_mm) < 1e-9:
        locations[name] = (0.0, 0.0, 0.0)
        return
    pose_bone = arm.pose.bones[name]
    target = pose_bone.matrix.copy()
    target.translation = (target.translation
                          + Vector((0.0, -push_mm / 1000.0, 0.0)))
    pose_bone.matrix = target
    bpy.context.view_layer.update()
    locations[name] = tuple(pose_bone.location)


# =============================================================== 万向节锁防御（C13 照抄）
EULER_Y_SAFE = _env_f("C14_YSAFE", 70.0)
EULER_Y_WEIGHT = _env_f("C14_YWEIGHT", 1.5)
# ★ C14 追加：**臂骨滚转搜索**。`aim_nearest` 只约束骨轴方向，绕自身轴的滚转由接力
#   （`rotation_difference` 复合）决定 —— 这会在"抬臂越顶"这类大摆幅里**漂进
#   |Y|≈90° 万向节锁**：实测 `forearm.R` 的**真实局部旋转**逐帧只变 ≤27°，但同一
#   旋转写成 XYZ 欧拉后逐分量跳 90.53°/帧 ⟹ `no_teleport` 假红（C13 教训的升级版：
#   C13 只换"两支等价欧拉"，而这里两支**都**在锁里，必须换**旋转本身**）。
#   滚转绕骨轴、过骨根 ⟹ **骨根/骨尖都不动、IK 与贴地全不受影响**，只是网格滚一下。
#   于是把滚转当自由度，逐帧在 `ROLL_GRID` 上搜"离上一帧欧拉最近 + 远离锁"的那支。
ROLL_STEP_DEG = _env_f("C14_ROLLSTEP", 5.0)
ROLL_BONES = frozenset(ARM_BONES)
CARRY_Q = {}          # bone -> 上一帧**已达成**的世界朝向（接力基准）


def _roll_grid():
    """臂骨绕自身轴的可选滚转（弧度）。0 必在内。"""
    step = math.radians(max(0.5, ROLL_STEP_DEG))
    return tuple(index * step for index in range(int(round(2.0 * math.pi / step))))


ROLL_GRID = _roll_grid()


def _xyz_candidates(m):
    """3×3 基 → 两支等价 XYZ 欧拉（弧度）。|Y|→90° 时分拆任意，故必须给两支。"""
    y = math.asin(max(-1.0, min(1.0, -m[2][0])))
    cy = math.cos(y)
    if abs(cy) > 1e-6:
        x = math.atan2(m[2][1], m[2][2])
        z = math.atan2(m[1][0], m[0][0])
    else:                                   # 万向节锁：x 归零、z 吸收全部
        x = 0.0
        z = math.atan2(-m[0][1], m[1][1])
    return ((x, y, z), (x + math.pi, math.pi - y, z + math.pi))


def _set_euler_nearest(arm, name, prev=None):
    """把该骨当前的**局部旋转**写成"离上一帧最近"的那支欧拉（返回度）。

    ★ C13 第 3 号教训：`matrix → euler` 在 |Y| → 90°（XYZ 万向节锁）附近的 (X, Z)
      拆分是任意的 ⟹ 同一旋转的欧拉表示会跳；`no_teleport` 量的是欧拉逐分量步长，
      于是报假红。这里自己解两支等价欧拉、取离上一帧最近的。

    ★ C14 追加：当**两支都在锁里**（真实局部旋转是平滑的，但绕骨轴的滚转把它拖进了
      |Y|≈90° 带），再搜一圈绕骨轴的滚转 `ROLL_GRID`（只对臂骨）。滚转过骨根 ⟹
      骨根/骨尖不动 ⟹ IK、贴地、剪影全部不受影响，只是把欧拉路径挪出锁带。
    """
    pose_bone = arm.pose.bones[name]
    basis = pose_bone.matrix_basis.to_3x3()
    if prev is None:
        prev = JS._PREV_EULER.get(name)
    best, best_cost = None, None
    for phi in (ROLL_GRID if name in ROLL_BONES else (0.0,)):
        if phi == 0.0:
            m = basis
        else:
            cos_p, sin_p = math.cos(phi), math.sin(phi)
            m = basis @ Matrix(((cos_p, 0.0, sin_p),
                                (0.0, 1.0, 0.0),
                                (-sin_p, 0.0, cos_p)))
        for cand in _xyz_candidates(m):
            value = [math.degrees(t) for t in cand]
            if prev is not None:
                for index in range(3):
                    while value[index] - prev[index] > 180.0:
                        value[index] -= 360.0
                    while value[index] - prev[index] < -180.0:
                        value[index] += 360.0
            cost = 0.0
            if prev is not None:
                cost = max(abs(a - b) for a, b in zip(value, prev))
            cost += max(0.0, abs(value[1]) - EULER_Y_SAFE) * EULER_Y_WEIGHT
            if best_cost is None or cost < best_cost:
                best, best_cost = tuple(value), cost
    pose_bone.rotation_euler = [math.radians(t) for t in best]
    bpy.context.view_layer.update()
    return best


def aim_nearest(arm, name, direction, basis, rdir):
    """`aim_bone_ref` 的**接力 + 最近欧拉支**版（C13 第 3 号教训）。

    从**上一帧已达成朝向**接力，只补"把骨轴摆到目标方向"的那一个最小旋转 ⟹
    构造上不会与固定基准反平行、不会发生大跳。第一帧仍从 `IDLE_BASIS` 出发
    ⟹ 与 `aim_bone_ref` 逐位同源，起手接合不受影响。
    """
    pose_bone = arm.pose.bones[name]
    want = Vector(direction)
    if want.length < 1e-9:
        return _set_euler_nearest(arm, name)
    want.normalize()
    prev_q = CARRY_Q.get(name)
    if prev_q is None:
        prev_q = (Vector(rdir).normalized().rotation_difference(want)
                  @ basis.to_3x3().to_quaternion())
    y_prev = (prev_q @ Vector((0.0, 1.0, 0.0))).normalized()
    quaternion = y_prev.rotation_difference(want) @ prev_q
    target = quaternion.to_matrix().to_4x4()
    target.translation = pose_bone.matrix.translation
    pose_bone.matrix = target
    bpy.context.view_layer.update()
    CARRY_Q[name] = quaternion
    return _set_euler_nearest(arm, name)


def arm_seat(arm, pose, side, target, elbow_dir):
    """位置口径两骨臂 IK（C13 口径）+ 最近欧拉支。"""
    up, fo, hd = ("upperarm." + side, "forearm." + side, "hand." + side)
    dims = ARM_LEN[side]
    l1 = dims["upper"]
    l23 = dims["forearm"] + dims["hand"]
    shoulder = Vector(A.bone_world(arm, up, "head"))
    target = Vector(target)
    delta = target - shoulder
    limit = (l1 + l23) * 0.9995
    clamp = delta.length > limit
    distance = max(1e-4, min(delta.length, limit))
    axis = (delta.normalized() if delta.length > 1e-9
            else Vector((0.0, 0.0, -1.0)))
    bulge = Vector(elbow_dir) - axis * Vector(elbow_dir).dot(axis)
    if bulge.length < 1e-6:
        bulge = Vector((0.0, 0.0, 1.0)) - axis * axis.z
    bulge.normalize()
    cos_sh = (l1 * l1 + distance * distance - l23 * l23) / (2.0 * l1 * distance)
    cos_sh = max(-1.0, min(1.0, cos_sh))
    sin_sh = math.sqrt(max(0.0, 1.0 - cos_sh * cos_sh))
    elbow = shoulder + (axis * cos_sh + bulge * sin_sh) * l1
    for name, direction in ((up, elbow - shoulder),
                            (fo, target - elbow),
                            (hd, target - elbow)):
        pose[name] = aim_nearest(arm, name, direction,
                                 IDLE_BASIS[name], IDLE_DIR[name])
    return clamp, delta.length * 1000.0, limit * 1000.0


def leg_seat(arm, pose, side, target, knee_dir):
    """位置口径两骨腿 IK（恒定用 Idle 基准，只换欧拉支）。"""
    thigh_len, shin_len = A.L_THIGH, A.L_SHIN
    hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
    target = Vector(target)
    delta = target - hip
    distance = max(1e-4, min(delta.length, (thigh_len + shin_len) * 0.9995))
    axis = delta.normalized() if delta.length > 1e-9 else Vector((0.0, 0.0, -1.0))
    bulge = Vector(knee_dir) - axis * Vector(knee_dir).dot(axis)
    if bulge.length < 1e-6:
        fallback = Vector((0.0, -1.0, 0.0))
        bulge = fallback - axis * fallback.dot(axis)
        if bulge.length < 1e-6:
            bulge = Vector((0.0, 0.0, 1.0)) - axis * axis.z
    bulge.normalize()
    cos_hip = (thigh_len ** 2 + distance ** 2 - shin_len ** 2) \
        / (2.0 * thigh_len * distance)
    cos_hip = max(-1.0, min(1.0, cos_hip))
    sin_hip = math.sqrt(max(0.0, 1.0 - cos_hip * cos_hip))
    knee = hip + (axis * cos_hip + bulge * sin_hip) * thigh_len
    for name, direction in (("thigh." + side, knee - hip),
                            ("shin." + side, target - knee)):
        pose[name] = aim_nearest(arm, name, direction,
                                 IDLE_BASIS[name], IDLE_DIR[name])


def build_pose(arm, frame, shift):
    pose = torso_pose(frame)
    A.apply_pose(arm, pose)
    for side in SIDES:
        push_shoulder(arm, side, pwl(SHOULDER_PUSH[side], frame, 0.0), pose)
    for side in SIDES:
        target = ANKLE_0[side]
        leg_seat(arm, pose, side,
                 (target[0], target[1], target[2] + shift[side]),
                 knee_dir(side, frame))
    for side in SIDES:
        name = "foot." + side
        pose[name] = JS._unwrap_xyz(
            JS._PREV_EULER.get(name),
            keep_foot_lifted(arm, side, foot_lift(side, frame)))
    for side in SIDES:
        # ★ 手目标必须在 `apply_pose` 之后现取（肩位随躯干变动），肘偏好按同一臂轴投影。
        target = hand_target(side, frame)
        shoulder = A.bone_world(ARM_REF, "upperarm." + side, "head")
        clamp, dist_mm, limit_mm = arm_seat(
            arm, pose, side, target,
            elbow_dir(side, frame, shoulder, target))
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

    # 起手接合（C10 第 5 号 / C11 / C12 / C13 复用）：`arm_seat` 隐含"腕直"，而 Idle
    # 戒备是**屈腕**的，第 1 帧会被掰直 ⟹ 单帧欧拉步长会超标。f1..EASE_END 平滑接上。
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
    """逐帧贴地闭环：**双脚**鞋底钉到 0 mm（`shift` 并进踝目标）。"""
    shift = {side: 0.0 for side in SIDES}
    # ★ 闭环会把 `build_pose` 跑好几遍；`_set_euler_nearest` 以 `_PREV_EULER` 为
    #   "上一帧"参照，若不还原，第 2 遍就把第 1 遍的结果当成上一帧（C13 教训）。
    base_prev = dict(JS._PREV_EULER)
    base_carry = dict(CARRY_Q)

    def rebuild():
        JS._PREV_EULER.clear()
        JS._PREV_EULER.update(base_prev)
        CARRY_Q.clear()
        CARRY_Q.update(base_carry)
        return build_pose(arm, frame, shift)

    pose = rebuild()
    if meshes is None:
        return pose
    for _step in range(10):
        low = A.foot_lowest_by_side()
        error = {side: 0.0 - low[side][2] for side in SIDES
                 if low[side] is not None}
        if not error or max(abs(v) for v in error.values()) < 1e-6:
            break
        for side, value in error.items():
            shift[side] += value
        pose = rebuild()
    return pose


def recover_pose(arm, frame, pose_a, pose_b):
    """收招段：躯干/臂走**欧拉仿射**，腿**分层**，最后补**根骨竖直贴地补偿**。

    （照抄 C12 / C13：分层只把误差压低、没有归零，所以最后量一次鞋底，用根骨纯平移
      抬回；`q == 1` 时不再补偿 ⟹ 末帧就是 Idle 逐位值。）
    """
    q = q_of(frame)
    pose = A.blend(pose_a, pose_b, q)
    A.apply_pose(arm, pose)
    weight = leg_weight(frame)
    if weight < 0.999:
        shift = {side: 0.0 for side in SIDES}
        solved = None
        for _step in range(10):
            trial = dict(pose)
            A.apply_pose(arm, trial)
            for side in SIDES:
                target = ANKLE_0[side]
                leg_seat(arm, trial, side,
                         (target[0], target[1], target[2] + shift[side]),
                         knee_dir(side, frame))
            for side in SIDES:
                name = "foot." + side
                trial[name] = JS._unwrap_xyz(
                    JS._PREV_EULER.get(name),
                    keep_foot_lifted(arm, side, foot_lift(side, frame)))
            solved = trial
            low = A.foot_lowest_by_side()
            error = {s: 0.0 - low[s][2] for s in SIDES if low[s] is not None}
            if not error or max(abs(v) for v in error.values()) < 1e-6:
                break
            for side, value in error.items():
                shift[side] += value
        mixed = {}
        for side in SIDES:
            for bone in ("thigh." + side, "shin." + side):
                affine = pose[bone]
                ik = JS._unwrap_xyz(affine, solved[bone])
                mixed[bone] = tuple(i + (a - i) * weight
                                    for i, a in zip(ik, affine))
        pose.update(mixed)
    A.apply_pose(arm, pose)
    for side in SIDES:
        name = "foot." + side
        pose[name] = JS._unwrap_xyz(
            JS._PREV_EULER.get(name),
            keep_foot_lifted(arm, side, foot_lift(side, frame)))
    A.apply_pose(arm, pose)

    if q < 1.0:
        low = A.foot_lowest_by_side()
        penetration = max(0.0, -min(low[s][2] for s in SIDES
                                    if low[s] is not None))
        if penetration > 1e-6:
            locations = dict(pose.get("@loc", {}))
            locations["root"] = A.wloc(0.0, 0.0, penetration)
            pose["@loc"] = locations
            A.apply_pose(arm, pose)

    pose.update(A.FIST)
    for name, value in pose.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)
    return pose


# =============================================================== 逐帧实测
def world_poses(arm, action, total):
    """逐帧**全探针骨世界坐标**（停顿 / 收敛 / 转折都从它来）。"""
    scene = bpy.context.scene
    previous = arm.animation_data.action if arm.animation_data else None
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    frames = []
    for frame in range(0, total + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        point = {}
        for key in A.PROBE_KEYS:
            if key.endswith(".tail"):
                name = key[:-5]
                point[key] = tuple(A.bone_world(arm, name, "tail"))
            else:
                point[key] = tuple(A.bone_world(arm, key, "head"))
        frames.append(point)
    if previous is not None:
        arm.animation_data.action = previous
    return frames


def frame_series(arm, action, total):
    """逐帧：骨盆 / 拳 / 踝 / 鞋底 / 关键骨欧拉 / 腿可达比。"""
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
        for name in ("pelvis", "chest", "head", "upperarm.L", "upperarm.R",
                     "foot.L", "foot.R", "thigh.L", "thigh.R"):
            row[name] = tuple(A.bone_world(arm, name, "head"))
        for name in ("hand.L", "hand.R", "thigh.L", "thigh.R"):
            row[name + "_tail"] = tuple(A.bone_world(arm, name, "tail"))
        for name in ARM_BONES + LEG_BONES + ("foot.L", "foot.R"):
            row["deg_" + name] = tuple(
                math.degrees(v) for v in arm.pose.bones[name].rotation_euler)
        low = A.foot_lowest_by_side()
        for side in SIDES:
            row["sole_" + side] = None if low[side] is None else low[side][2]
            row["ankle_" + side] = tuple(A.bone_world(arm, "foot." + side, "head"))
        hip_limit = A.L_THIGH + A.L_SHIN
        for side in SIDES:
            hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
            ankle = Vector(A.bone_world(arm, "foot." + side, "head"))
            row["reach_" + side] = (ankle - hip).length / hip_limit
        rows.append(row)
    if previous is not None:
        arm.animation_data.action = previous
    return rows


def step_series(poses):
    """逐帧步长（mm）：该帧相对前一帧的**最大单骨世界位移**。index 0 = 0。"""
    out = [0.0]
    for index in range(1, len(poses)):
        best = 0.0
        for key in poses[index]:
            best = max(best, (Vector(poses[index][key])
                              - Vector(poses[index - 1][key])).length * 1000.0)
        out.append(best)
    return out


# =============================================================== 剪影（在 Action 上量）
def silhouette_now(arm):
    """当前的（已在目标帧上求值的）**正视**剪影指标（相机 −Y：横轴世界 X）。"""
    all_pts, keep_pts = P._mesh_verts()
    verts, tris = P._mesh_tris()
    lo, hi = P._bbox(keep_pts)
    width = hi[0] - lo[0]
    height = hi[2] - lo[2]
    fill_grid, filled, nx, nz = P._fill_grid(verts, tris, lo, hi)
    com = P._centroid_area_weighted(verts, tris)
    (slo, shi), zmin = P._support_box()
    shoulder = [A.bone_world(arm, "upperarm." + s, "head").x for s in SIDES]
    # ★ 可失败版「头顶没被别的东西埋住」：`bbox 顶 − 头骨顶 ≤ 300 mm`。
    #   （探针第 1 版量"最高点的 x 贴近头骨 x"，但单臂过顶天然高出 500+ mm，
    #   把合法的胜利 Pose 误杀；改量"头顶之上还压着多少东西"。）
    head_top_z = A.bone_world(arm, "head", "tail").z
    return {
        "bbox_m": [[round(v, 4) for v in lo], [round(v, 4) for v in hi]],
        "width_m": round(width, 4), "height_m": round(height, 4),
        "aspect": round(width / height, 4) if height > 0 else 0.0,
        "proj_area_m2": round(P._proj_area_xz(verts, tris), 4),
        "fill_grid": round(fill_grid, 4),
        "grid": [nx, nz, filled],
        "com_xy_m": [round(com[0], 4), round(com[1], 4)],
        "com_inside_support": None if slo is None else bool(
            slo[0] - 0.02 <= com[0] <= shi[0] + 0.02
            and slo[1] - 0.02 <= com[1] <= shi[1] + 0.02),
        "shoulder_width_m": round(abs(shoulder[0] - shoulder[1]), 4),
        "above_head_mm": round((hi[2] - head_top_z) * 1000.0, 2),
        "sole_min_mm": round(zmin * 1000.0, 2),
    }


def silhouette_at(arm, action, frame):
    scene = bpy.context.scene
    previous = arm.animation_data.action if arm.animation_data else None
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    out = silhouette_now(arm)
    if previous is not None:
        arm.animation_data.action = previous
    return out


# =============================================================== 专属门禁
def end_assertions(arm, action, samples, rows, poses, sil_pose, sil_idle):
    res = {}
    steps = step_series(poses)

    # ---- 1) ★ `hero_pose_hold_ok`：定格窗 18~36 帧内**逐位冻结**
    worst = 0.0
    worst_at = None
    for frame in range(POSE + 1, HOLD_END + 1):
        for key in poses[frame]:
            step = (Vector(poses[frame][key])
                    - Vector(poses[frame - 1][key])).length * 1000.0
            if step > worst:
                worst, worst_at = step, [frame, key]
    hold_frames = HOLD_END - POSE + 1
    res["hero_pose_hold_frames"] = hold_frames
    res["hero_pose_hold_window_ok"] = bool(
        HOLD_FRAME_MIN <= hold_frames <= HOLD_FRAME_MAX)
    res["hero_pose_hold_worst_mm"] = round(worst, 6)
    res["hero_pose_hold_worst_at"] = worst_at
    res["hero_pose_hold_freeze_ok"] = bool(worst <= HOLD_MAX_MM)
    res["hero_pose_hold_ok"] = bool(res["hero_pose_hold_window_ok"]
                                    and res["hero_pose_hold_freeze_ok"])
    res["hero_pose_hold_frame_min"] = HOLD_FRAME_MIN
    res["hero_pose_hold_frame_max"] = HOLD_FRAME_MAX

    # ---- 2) ★ `hero_silhouette_ok`：定格帧的正视剪影（阈值本支重定）
    aspect_ratio = sil_pose["aspect"] / sil_idle["aspect"]
    fill_ratio = sil_pose["fill_grid"] / sil_idle["fill_grid"]
    shoulder_ratio = (sil_pose["shoulder_width_m"]
                      / sil_idle["shoulder_width_m"])
    res["sil_idle"] = sil_idle
    res["sil_hero"] = sil_pose
    res["sil_aspect_ratio"] = round(aspect_ratio, 4)
    res["sil_fill_ratio"] = round(fill_ratio, 4)
    res["sil_shoulder_ratio"] = round(shoulder_ratio, 4)
    res["sil_above_head_mm"] = sil_pose["above_head_mm"]
    res["sil_aspect_ok"] = bool(aspect_ratio >= SIL_ASPECT_MIN)
    res["sil_fill_ok"] = bool(fill_ratio >= SIL_FILL_MIN)
    res["sil_shoulder_ok"] = bool(shoulder_ratio >= SIL_SHOULDER_MIN)
    res["sil_head_top_ok"] = bool(
        sil_pose["above_head_mm"] <= ABOVE_HEAD_MAX_MM)
    res["sil_com_ok"] = sil_pose["com_inside_support"] is True
    res["hero_silhouette_ok"] = bool(
        res["sil_aspect_ok"] and res["sil_fill_ok"] and res["sil_shoulder_ok"]
        and res["sil_head_top_ok"] and res["sil_com_ok"])
    res["sil_aspect_min"] = SIL_ASPECT_MIN
    res["sil_fill_min"] = SIL_FILL_MIN
    res["sil_shoulder_min"] = SIL_SHOULDER_MIN
    res["sil_above_head_max_mm"] = ABOVE_HEAD_MAX_MM
    res["sil_axis"] = "正视图（相机 −Y）：横轴 = 世界 X，纵轴 = 世界 Z"

    # ---- 3) ★ `exit_pose_ok`：平滑回到 `Idle_01@0`
    tail = [steps[f] for f in range(TOTAL - 5, TOTAL + 1)]
    res["settle_tail_mm"] = [round(v, 3) for v in tail]
    res["settle_monotone_ok"] = bool(
        all(tail[i + 1] <= tail[i] + 1e-6 for i in range(len(tail) - 1)))
    res["settle_last2_mm"] = round(max(tail[-2:]), 4)
    res["settle_no_stop_ok"] = bool(res["settle_last2_mm"]
                                    <= SETTLE_LAST2_MAX_MM)
    delta_end = 0.0
    for key in A.PROBE_KEYS:
        if key in poses[0] and key in poses[-1]:
            delta_end = max(delta_end,
                            (Vector(poses[0][key])
                             - Vector(poses[-1][key])).length * 1000.0)
    res["end_pose_delta_mm"] = round(delta_end, 4)
    res["end_pose_ok"] = bool(delta_end <= END_POSE_TOL_MM)
    res["exit_pose_ok"] = bool(res["end_pose_ok"]
                               and res["settle_no_stop_ok"]
                               and res["settle_monotone_ok"])

    # ---- 4) ★ `resolve_ok`：定格 → 收招的转折不许硬切
    before = max(steps[SINK_END + 1:POSE + 1]) if POSE > SINK_END else 0.0
    span = min(RECOVER + 2, TOTAL)
    after = max(steps[RECOVER + 1:span + 1]) if span > RECOVER else 0.0
    res["resolve_before_max_mm"] = round(before, 3)
    res["resolve_after_max_mm"] = round(after, 3)
    res["resolve_ratio"] = round(after / max(before, 1e-6), 4)
    res["resolve_ratio_max"] = RESOLVE_RATIO_MAX
    res["resolve_ok"] = bool(res["resolve_ratio"] <= RESOLVE_RATIO_MAX)

    # ---- 5) 朝向镜头（躯干 / 头偏航）
    torso_yaw = sum(pwl(k, POSE, 0.0) for k in
                    (PELVIS_RY, SPINE_RY, SPINE_RY, CHEST_RY))
    head_yaw = torso_yaw + pwl(NECK_RY, POSE, 0.0) + pwl(HEAD_RY, POSE, 0.0)
    res["camera_torso_yaw_deg"] = round(torso_yaw, 3)
    res["camera_head_yaw_deg"] = round(head_yaw, 3)
    res["camera_facing_ok"] = bool(abs(torso_yaw) <= CAMERA_MAX_DEG
                                   and abs(head_yaw) <= CAMERA_MAX_DEG)
    res["camera_max_deg"] = CAMERA_MAX_DEG

    # ---- 6) 反作弊：不能"整支等于静止"
    peak_step = max(steps) if steps else 0.0
    path = sum(steps[i] for i in range(len(steps))
               if not (POSE <= i <= HOLD_END))
    res["nofreeze_peak_step_mm"] = round(peak_step, 3)
    res["nofreeze_path_outside_mm"] = round(path, 1)
    res["no_freeze_ok"] = bool(peak_step >= 3.0 and path >= 300.0)

    # ---- 7) 沉收（"启动略慢"的蓄势）实测
    pz = [row["pelvis"][2] * 1000.0 for row in rows]
    sink = pz[0] - min(pz[:POSE])
    rise = pz[POSE] - min(pz[:POSE])
    res["antic_sink_mm"] = round(sink, 2)
    res["antic_rise_mm"] = round(rise, 2)
    res["anticipation_ok"] = bool(sink >= 20.0 and rise >= 8.0)

    # ---- 8) 承重脚不滑（水平，踝关节）+ 位移
    def slide(side):
        pts = [Vector((rows[f]["ankle_" + side][0], rows[f]["ankle_" + side][1]))
               for f in range(TOTAL + 1)]
        return max((p - pts[0]).length for p in pts) * 1000.0

    def slide3(side):
        pts = [Vector(rows[f]["ankle_" + side]) for f in range(TOTAL + 1)]
        return max((p - pts[0]).length for p in pts) * 1000.0

    res["plant_L_mm"] = round(slide("L"), 3)
    res["plant_R_mm"] = round(slide("R"), 3)
    res["plant_3d_L_mm"] = round(slide3("L"), 3)
    res["plant_3d_R_mm"] = round(slide3("R"), 3)
    res["plant_ok"] = bool(max(res["plant_L_mm"], res["plant_R_mm"])
                           <= PLANT_MAX_MM)
    pelvis = [Vector(row["pelvis"]) for row in rows]
    span_h = math.hypot(max(p.x for p in pelvis) - min(p.x for p in pelvis),
                        max(p.y for p in pelvis) - min(p.y for p in pelvis))
    res["root_span_h_mm"] = round(span_h * 1000.0, 2)
    res["root_motion_ok"] = bool(span_h * 1000.0 <= 3.0)

    # ---- 9) 腿可达比 / 臂逆解不截断
    worst_ratio, worst_r_at = 0.0, None
    for row in rows:
        for side in SIDES:
            if row["reach_" + side] > worst_ratio:
                worst_ratio, worst_r_at = row["reach_" + side], [row["frame"], side]
    res["leg_reach_worst_ratio"] = round(worst_ratio, 5)
    res["leg_reach_worst_at"] = worst_r_at
    res["leg_reach_ok"] = bool(worst_ratio <= REACH_MAX_RATIO)
    res["arm_clamp"] = {side: dict(info) for side, info in ARM_CLAMP.items()}
    res["arm_reach_ok"] = bool(all(not info["any"]
                                   for info in ARM_CLAMP.values()))

    # ---- 10) 冻结窗的两端：进窗 / 出窗那一帧必须有可见位移（不是"整段拖慢"）
    res["hold_edge_in_mm"] = round(steps[POSE], 3)
    res["hold_edge_out_mm"] = round(steps[RECOVER + 1], 3)
    return res


# =============================================================== 主流程
def main():
    global SEAM_POSE, SEAM_EULER, Z_SEAM, ANKLE_0, FOOT0
    global IDLE_HAND, IDLE_HAND_OFF, IDLE_ELBOW, IDLE_KNEE, IDLE_BASIS
    global IDLE_DIR, IDLE_KNEE_DIR, ARM_LEN, ARM_REF, SIL_BASE

    for store in (SEAM_POSE, SEAM_EULER, ANKLE_0, FOOT0, IDLE_HAND,
                  IDLE_HAND_OFF, IDLE_ELBOW, IDLE_KNEE, IDLE_BASIS, IDLE_DIR,
                  IDLE_KNEE_DIR, ARM_LEN, ARM_CLAMP, SIL_BASE):
        store.clear()
    HAND_DIR_KEYS.clear()
    HAND_LEN_KEYS.clear()
    ELBOW_KEYS.clear()
    CARRY_Q.clear()

    arm, meshes = A.open_animation_project()
    A.setup_scene()
    if I1.NAME not in bpy.data.actions:
        print("C14_BOOTSTRAP 缺 %s，先补跑" % I1.NAME)
        I1.main()
        arm, meshes = A.open_animation_project()
        A.setup_scene()

    for side in SIDES:
        ARM_LEN[side] = {
            "upper": arm.pose.bones["upperarm." + side].length,
            "forearm": arm.pose.bones["forearm." + side].length,
            "hand": arm.pose.bones["hand." + side].length}
    ARM_REF = arm
    for extra in ("thigh.L", "thigh.R", "shin.L", "shin.R"):
        if extra not in A.PROBE_BONES:
            A.PROBE_BONES = tuple(A.PROBE_BONES) + (extra,)
        if extra not in A.PROBE_TAILS:
            A.PROBE_TAILS = tuple(A.PROBE_TAILS) + (extra,)
    A.PROBE_KEYS = A.PROBE_BONES + tuple(n + ".tail" for n in A.PROBE_TAILS)

    # ---- 首帧真值：`Idle_01@0`（★ 先归零再求值：`.blend` 里存着上次运行留下的
    #   姿态，直接读会读到陈旧值，f1 归零时一步 360° —— C12/C13 教训。）
    scene = bpy.context.scene
    src = bpy.data.actions[I1.NAME]
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = src
    A._bind_slot(arm, src)
    A.reset_pose(arm)
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
        fist = Vector(A.bone_world(arm, "hand." + side, "tail"))
        shoulder = Vector(A.bone_world(arm, "upperarm." + side, "head"))
        offset = fist - shoulder
        IDLE_HAND[side] = tuple(fist)
        IDLE_HAND_OFF[side] = (tuple(offset.normalized()),
                               offset.length * 1000.0)

    # ---- Idle 骨基座（逆解基准；同时灌进 `anim_grab04` 的模块级表）
    idle = I1.idle_pose(arm, 0.0)
    A.apply_pose(arm, idle)
    bpy.context.view_layer.update()
    for side in SIDES:
        hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
        knee = Vector(A.bone_world(arm, "thigh." + side, "tail"))
        IDLE_KNEE_DIR[side] = (knee - hip).normalized()
        IDLE_KNEE[side] = tuple(IDLE_KNEE_DIR[side])
        for bone in ("thigh." + side, "shin." + side):
            IDLE_BASIS[bone] = arm.pose.bones[bone].matrix.to_3x3().copy()
            IDLE_DIR[bone] = A.bone_direction(arm, bone)
    for bone in ARM_BONES:
        IDLE_BASIS[bone] = arm.pose.bones[bone].matrix.to_3x3().copy()
        IDLE_DIR[bone] = A.bone_direction(arm, bone)
    for side in SIDES:
        shoulder = Vector(A.bone_world(arm, "upperarm." + side, "head"))
        elbow = Vector(A.bone_world(arm, "upperarm." + side, "tail"))
        IDLE_ELBOW[side] = tuple((elbow - shoulder).normalized())

    # ★ `build_hand_keys` 依赖 `IDLE_HAND_OFF`（上）与 `IDLE_ELBOW`（刚测），
    #   必须在两者都就位后调用（C14 专属：键由 `Idle_01@0` 真值现算）。
    build_hand_keys()

    for table, source in ((G4.IDLE_BASIS, IDLE_BASIS), (G4.IDLE_DIR, IDLE_DIR),
                          (G4.IDLE_KNEE_DIR, IDLE_KNEE_DIR)):
        table.clear()
        table.update(source)
    G4.ARM_LEN.clear()
    for side in SIDES:
        G4.ARM_LEN[side] = dict(ARM_LEN[side])

    A.report("C14_LAYOUT", {
        "total_frames": TOTAL, "seconds": round(TOTAL / float(A.FPS), 3),
        "ease_end": EASE_END, "sink_end": SINK_END,
        "sink_hold_end": SINK_HOLD_END, "pose": POSE, "hold_end": HOLD_END,
        "hold_frames": HOLD_END - POSE + 1, "recover": RECOVER,
        "settle_end": SETTLE_END, "cancel": CANCEL,
        "pelvis_z0_mm": round(Z_SEAM * 1000.0, 3),
        "ankle0_mm": {s: [round(v * 1000.0, 2) for v in ANKLE_0[s]]
                      for s in SIDES},
        "idle_hand_mm": {s: [round(v * 1000.0, 2) for v in IDLE_HAND[s]]
                         for s in SIDES},
        "hand_hero": {s: [list(HAND_HERO[s][0]), HAND_HERO[s][1]]
                      for s in SIDES},
        "torso_hero": {k: list(v) for k, v in TORSO_HERO.items()},
        "start_basis": ("`Idle_01@0`（默认：C14 独立触发；若引擎按大招三段"
                        "连续播放，则 C13 的 `FOLLOW_END` 才是起手基准）"),
        "note": ("大招收尾：沉收 %d 帧 → 停顿 %d 帧 → 爆发起身 %d 帧到英雄 Pose"
                 "→ 定格 %d 帧（逐位冻结）→ 收招 %d 帧回待机。"
                 "0 命中点、0.0 mm 位移、1 段。"
                 % (SINK_END - EASE_END, SINK_HOLD, POSE - SINK_HOLD_END,
                    HOLD_END - POSE + 1, TOTAL - RECOVER)),
    })

    # ---- 建片段
    JS._PREV_EULER.clear()
    A.apply_pose(arm, SEAM_POSE)
    bpy.context.view_layer.update()
    for name, value in SEAM_POSE.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)

    keyframes = [(0, SEAM_POSE)]
    for frame in range(1, RECOVER + 1):
        keyframes.append((frame, solve_pose(arm, frame, meshes)))

    # ★ 定格窗：`POSE` 姿态**逐位复用**到 `HOLD_END`（`hero_pose_hold_ok` 的
    #   构造性来源 —— 共用同一 `dict`，漂移恒为 0.0 mm）
    hold_pose = keyframes[POSE][1]
    for frame in range(POSE + 1, HOLD_END + 1):
        keyframes[frame] = (frame, dict(hold_pose))

    # 收招仿射：把末姿（Idle）解卷绕到离定格姿态最近的分支，再逐通道滑过去
    e0 = {k: tuple(v) for k, v in hold_pose.items() if not k.startswith("@")}
    e_end_unw = {bone: JS._unwrap_xyz(e0.get(bone, (0.0, 0.0, 0.0)), value)
                 for bone, value in SEAM_EULER.items()}
    end_pose = dict(e_end_unw)
    end_pose["@loc"] = {"pelvis": A.wloc(0.0, 0.0, Z_SEAM - 0.900)}
    A.report("C14_BLEND", {
        "delta_deg": {bone: round(max(abs(a - b) for a, b in
                                      zip(e0[bone], e_end_unw[bone])), 3)
                      for bone in sorted(e0) if bone in e0}})
    for frame in range(RECOVER + 1, TOTAL + 1):
        keyframes.append((frame, recover_pose(arm, frame, hold_pose, end_pose)))

    meta = {
        "anim_id": NAME,
        "loop": False,
        "category": "连招与特殊技",
        "note": ("大招收尾：沉收 → 爆发起身成英雄 Pose → 定格 %d 帧（逐位冻结）"
                 "→ 收招回待机。0 命中点、0.0 mm 位移、1 段。" % (HOLD_END - POSE + 1)),
        "antic_frame": SINK_END,
        "pose_frame": POSE,
        "hold_frames": HOLD_END - POSE + 1,
        "cancel_frame": CANCEL,
        "root_motion_m": [0.0, 0.0],
        "inherit_from": None,
        "start_basis": "Idle_01@0",
        "hit_count": 0,
        "segments": {"ease": [0, EASE_END], "sink": [EASE_END, SINK_END],
                     "sink_hold": [SINK_END, SINK_HOLD_END],
                     "rise": [SINK_HOLD_END, POSE], "hold": [POSE, HOLD_END],
                     "recover": [RECOVER, SETTLE_END],
                     "rest": [SETTLE_END, TOTAL]},
        "settle_end": SETTLE_END,
        "silhouette_axis": "正视图（相机 −Y）：横轴 = 世界 X，纵轴 = 世界 Z",
        "hem_excluded": list(HEM_EXCLUDE),
        "hero_pose_source": ("probe_c14_pose.py 第 16 轮 C14_PROBE_FINAL "
                             "y38_fin（先量再定）"),
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.add_markers(action, {
        "ENTER": 0, "EASE_END": EASE_END, "ANTIC": SINK_END,
        "ANTIC_HOLD_END": SINK_HOLD_END, "POSE": POSE, "HOLD_END": HOLD_END,
        "CANCEL": CANCEL, "SETTLE": SETTLE_END, "END": TOTAL,
    })

    samples = A.sample_animation(arm, action, 0, TOTAL, meshes)
    rows = frame_series(arm, action, TOTAL)
    poses = world_poses(arm, action, TOTAL)
    sil_idle = silhouette_at(arm, action, 0)
    sil_pose = silhouette_at(arm, action, POSE)
    SIL_BASE = sil_idle

    if os.environ.get("C14_TRACE") == "1":
        for row in rows:
            print("C14_TRACE " + json.dumps({
                "f": row["frame"],
                "pelvis": [round(v * 1000.0, 2) for v in row["pelvis"]],
                "fist_R": [round(v * 1000.0, 2) for v in row["hand.R_tail"]],
                "fist_L": [round(v * 1000.0, 2) for v in row["hand.L_tail"]],
                "sole_L": (None if row["sole_L"] is None
                           else round(row["sole_L"] * 1000.0, 2)),
                "sole_R": (None if row["sole_R"] is None
                           else round(row["sole_R"] * 1000.0, 2)),
                "reachR": round(row["reach_R"], 4),
                "reachL": round(row["reach_L"], 4),
            }))
    if os.environ.get("C14_ARM") == "1":
        prevq = {}
        prevl = {}
        for frame in range(0, POSE + 3):
            scene.frame_set(frame)
            bpy.context.view_layer.update()
            wq = arm.pose.bones["forearm.R"].matrix.to_3x3().to_quaternion()
            lq = arm.pose.bones["forearm.R"].matrix_basis.to_3x3().to_quaternion()
            dw = dl = None
            if "q" in prevq:
                dw = round(math.degrees(prevq["q"].rotation_difference(wq).angle), 2)
                dl = round(math.degrees(prevl["q"].rotation_difference(lq).angle), 2)
            prevq["q"] = wq.copy()
            prevl["q"] = lq.copy()
            print("C14_ARM f%-3d uR=%s fR=%s dworld=%s dlocal=%s lAng=%.2f" % (
                frame,
                [round(v, 2) for v in rows[frame]["deg_upperarm.R"]],
                [round(v, 2) for v in rows[frame]["deg_forearm.R"]],
                dw, dl, math.degrees(lq.angle)))
    if os.environ.get("C14_STEP") == "1":
        bones = ARM_BONES + LEG_BONES + ("foot.L", "foot.R")
        for frame in range(1, TOTAL + 1):
            worst, who = 0.0, None
            for name in bones:
                a = Vector(rows[frame]["deg_" + name])
                b = Vector(rows[frame - 1]["deg_" + name])
                d = max(abs(x - y) for x, y in zip(a, b))
                if d > worst:
                    worst, who = d, name
            if worst > 15.0:
                print("C14_STEP f%-3d %6.2f deg %s" % (frame, worst, who))
    if os.environ.get("C14_SIL") == "1":
        for frame in range(0, TOTAL + 1, 2):
            s = silhouette_at(arm, action, frame)
            print("C14_SIL " + json.dumps({
                "f": frame, "aspect": s["aspect"], "fill": s["fill_grid"],
                "ar": round(s["aspect"] / sil_idle["aspect"], 4),
                "fr": round(s["fill_grid"] / sil_idle["fill_grid"], 4),
                "w": s["width_m"], "h": s["height_m"],
                "above_head": s["above_head_mm"]}))

    report = A.run_common_assertions(samples, meta,
                                     foot_probe=("toe.L", "toe.R"),
                                     slide_tolerance_mm=PLANT_MAX_MM)
    report.update(end_assertions(arm, action, samples, rows, poses,
                                 sil_pose, sil_idle))

    # 首帧逐位 = `Idle_01@0`
    delta0 = 0.0
    for name, value in SEAM_EULER.items():
        got = samples[0]["euler"].get(name, (0.0, 0.0, 0.0))
        delta0 = max(delta0, max(abs(a - b) for a, b in zip(got, value)))
    report["ua_start_delta_deg"] = round(delta0, 8)
    report["ua_start_ok"] = bool(delta0 <= SEAM_TOL)

    report["low_bad_frames"] = {
        str(s["frame"]): [round(s["low"]["L"] * 1000.0, 2),
                          round(s["low"]["R"] * 1000.0, 2)]
        for s in samples
        if min(s["low"]["L"], s["low"]["R"]) * 1000.0 < GROUND_MIN_MM}
    report["meta"] = meta
    report["failed"] = sorted(k for k, v in report.items()
                              if k.endswith("_ok") and v is not True)
    report["non_ok_bools"] = sorted(
        k for k, v in report.items()
        if isinstance(v, bool) and not k.endswith("_ok") and v is not True)
    A.report("C14_REPORT", report)

    if not SKIP_RENDER:
        frames = [0, EASE_END, SINK_END, SINK_HOLD_END, POSE, POSE + 10,
                  HOLD_END, CANCEL, SETTLE_END, TOTAL]
        A.render_pose_sheet(arm, action, frames, "ultend",
                            views=(A.VIEW_SIDE, A.VIEW_FRONT, A.VIEW_3Q))
        A.save_project()
        A.export_glb(arm)
    print("C14_DONE failed=%s" % report["failed"])
    print("C14_DONE non_ok_bools=%s" % report["non_ok_bools"])


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("C14_FAILURE " + traceback.format_exc())
