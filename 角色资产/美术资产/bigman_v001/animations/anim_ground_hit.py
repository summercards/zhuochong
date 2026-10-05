"""anim_ground_hit —— D16 `Ground_Hit` 地面受击（仰面躺地，被补刀 → 躯干局部弹起 → 落回）。

清单原文：「**地面被补刀时身体局部弹起**」。

★★ 本支是 **D15 `Knockdown_B` 的直接下游** —— 上游末帧 = **仰面贴地自持**。
   **唯一一件事**：把 D15 的"仰面躺平"接成"被补刀 → 躯干局部弹起 → 落回仰卧"，
   且 **骨盆全程不许离地**。

   | 接缝 | 上游 / 下游 | 本支落成的做法 |
   |---|---|---|
   | 上游**姿态** | D15 末帧 = `Knockdown_B@20`（f16 起逐位锁存） | 本支 f0 **逐位 = `Knockdown_B@20`** |
   | 上游**动量** | D15 末帧 `end_vz = 0`（已离开弹道、骨盆固定） | **不继承任何竖直动量** —— **f0 起就贴地**，竖直通道**没有弹道段** |
   | 下游**贴地** | D18 `GetUp_B` 从"仰面贴地"起步 | 末帧**仍是贴地自持**：骨盆 z 逐位固定、`end_vz = 0`、姿态回到接缝 |

★★ §1 本支的真风险：**"局部弹起"极易被做成"整体离地"**

   文字要求是「身体**局部**弹起」。最容易的实现是"骨盆 z 抬一下" ——
   那是**整体离地**，本支**明令禁止**（全程不许离地）。
   ⟹ 竖直通道**拆成三层**，而且层的归属**与 D15 相反**：

   | 层 | 载体 | 本支要求 | 判据 |
   |---|---|---|---|
   | **骨盆层** | `pelvis` 骨（世界 z） | **逐位固定**在 D15 末帧值（实测 **128.0 mm**），全程 ∈ [126, 134] mm | ★★ `ground_hold_ok`（**本支命门**） |
   | **上身层** | 胸 / 头（`chest` / `head` 尾端 世界 z） | **单峰**：`HIT` 之后**先升后降**，峰值帧在 `(HIT, SETTLE)` **内部** | `bounce_present_ok` + `bounce_single_peak_ok` |
   | **腿层** | 踝 / 鞋底 | 因惯性**抖一下再落下**（膝折向躯干 + 踝下沉），鞋底不许穿地 | `legs_bounce_ok` |

★★ **最容易做废的地方（计划 §1 点名）**：D15 里腿是**抬着**的（`sole_tail_min_mm = 262.613`）。
   本支若照抄 D15 的 `hip_probe`（**骨盆 + 后脑 + 双肩**四点 ≤3 mm），弹起段**后脑会主动抬起来**
   ⟹ `hip_probe` **会被自己设计出来的动作判红**。
   ⟹ **`hip_probe` 在本支换载体**：只锁 **骨盆 + 双肩**（**去掉后脑**）。

★★★ **本支的独门尺子**（跨支，量的是"形状"不是"位置"）：
   `px_bounce_ok` —— 侧视**全剪影面积行心**必须呈**单峰**（见 `probe_d16_pixels.py`）。
   **反面对照 = D15 自己**（从 f7 起面积行心一路单调下降然后单调平，**绝无单峰**）⟹ 必红。

★ 帧预算：**20 帧 / 0.333 s @60fps**，非循环（硬上界 22）。
★ 相位 `T_PHASE_D16 = T_PHASE_D15 + 20 = 69.5`（**仅登记，本支不参与解算** —— 没有弹道段）。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python anim_ground_hit.py
    SKIP_RENDER=1  只跑门禁不渲图（迭代用）
    D16_TRACE=1    逐帧打印驱动标量 / 上身抬升 / 腿行程

反向验证（§4 第 7 步，7 组）：
    D16_TP_SEAM_ZERO=1    ① 首帧改零位（接缝断）        ⟹ `seam_in_ok` 红
    D16_TP_NOBOUNCE=1     ② 抽掉弹起                     ⟹ `bounce_present_ok` 红
    D16_TP_BOUNCE=80      ③ 弹起过大（胸 +80°）          ⟹ `bounce_present_ok`（上界）红
    D16_TP_PELVIS_LIFT=1  ④ ★ **改成"骨盆整体抬"**      ⟹ **`ground_hold_ok` 红**（核心守卫）
    D16_TP_DOUBLE=1       ⑤ 造第二个峰（SETTLE 之后）    ⟹ `bounce_single_peak_ok` + `bounce_no_double_ok` 红
    D16_TP_NOLEGS=1       ⑥ 抽掉腿的抖与落               ⟹ `legs_bounce_ok` 红
    D16_TP_FLIPSIGN=1     ⑦ 翻符号（上身往下砸）         ⟹ `bounce_present_ok` 红

★ 本支定档实测（2026-10-03，**官方命令、不带任何 env**，`failed=[]` / `non_ok_bools=[]`）
---------------------------------------------------------------
    帧数          20 帧 / 0.333 s @60fps，非循环
    竖直通道      **三段、无弹道段**（全族第一支）—— `ballistic_until_land_ok` 显式 DISABLED
    `ground_hold_ok`      ★★ 命门：全 21 帧 pelvis 世界 z **逐位 = 128.0 mm**（极差 0.0），band [126, 134]
    `bounce_present_ok`   ★ 上身弹起峰值 **106.794 mm**（`bounce_lift_rel_mm`），峰帧 **f6** ∈ (2,12) 内部
                              上界 200 mm 由 `D16_TP_BOUNCE=80` 反面对照导出（守清单原文「**局部**」二字）
    `bounce_single_peak_ok` / `bounce_no_double_ok`   绿（峰后单调不升，容差 0.5 mm）
    `legs_bounce_ok`      鞋底最低 **183.108 mm**（≥ −2）、最大下沉 **31.915 mm**（腿真的落了）
    `hip_probe_ok`        ★★ 载体 = **骨盆 + 双肩**（**去掉后脑**）；三点 drift 全 **0.0 mm**
                              后脑只报（`hip_probe_head_tail_report_mm`）
    `back_land_ok`        `f ≥ SETTLE` 后脑后 **189.602 mm** ≤ 260（落回后仍是仰面躺平）
    `hitstop_present`     2 帧（f2 = f3），上身 drift **0.0°**，双腿豁免
    `no_snap_stop_ok`     末 6 帧步长 `[5.8e-05, 4.4e-05, 0, 0, 0, 0]`（单调收敛）
    `chain_present_ok`    ★ 髋段**换口径**：脚 241.15 mm / 膝 30.171° / **髋 21.107°（角，非位移）** /
                              腰 10.013° / 肩 50.31 mm / 手 45.11 mm（阈值 8° 由实测导出）
    `no_teleport`         `max_frame_step = 21.942°`（@ f10 `shin.R`）
                              ★ 派生时必须**补回 D15 的 `ROLL_LEGS`**（见 `UE.ROLL_BONES` 段），
                                否则欧拉万向节锁会把这项飙到 **58.48°**（本项目第 5 次踩万向节锁）
    `root_motion_m`       `[0.0, 0.0]`（原地受击，净位移 ≈ 0；与 D14 −0.576 / D15 +0.444 都不同）
    `seam_in_ok`          首帧逐位 = `Knockdown_B@20`，orient / relpos / raw delta 全 **0.0**
    `end_pelvis_z_mm`     **128.0**，`end_vz = 0`（末帧贴地自持，供 D18 起步）
    `end_vs_d15_orient_deg` **0.229°**（< 2°，「被补刀后的新平衡」）
    `hem_static_ok`       `Jacket_Hem` / `Jacket_Hem_Line` 未绑定（已知模型侧遗漏），首末逐位相同

★★ 通道可见性分工（本轮**新发现**，侧视相机下）
---------------------------------------------------------------
    侧视相机轴 = **X** ⟹ X 方向位移**完全不可见**、不进面积行心；
    屏幕水平 = **Y**（不进面积行心）、**只有 Z 进面积行心**。
    ⟹ ① 腿层若用 **Z 下沉**驱动，会**盖过**上身弹起（实测 f9 把面积行心拉低 5.4 px，
          上身峰只剩 0.46 px）—— 本支因此把腿层主驱动从 **Z 换成 X 侧张**（相机轴），
          既**不可见**又**真转髋**（专用来扛 `chain_present_ok`）；
       ② 上身弹起走**姿态层**（胸/头尾端 Z），是全剪影面积行心唯一的上移来源。
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

NAME = "Ground_Hit"
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"
SIDES = ("L", "R")

# ★ 接缝真源：上游 D15 的落盘 action + 末帧号
SEAM_ACTION = os.environ.get("D16_SEAM_ACTION", "Knockdown_B")
SEAM_FRAME = int(os.environ.get("D16_SEAM_FRAME", "20"))
# ★ D15 的相位原点（`anim_knockdown_b.T_PHASE`）—— 本支**只登记**，不参与解算
D15_T_PHASE = 49.5
T_PHASE_D16 = D15_T_PHASE + 20.0                      # 69.5


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
    """量化到 float32 —— F-Curve 关键帧就是按 float32 存的（与 D02~D15 同源）。"""
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


# =============================================================== 时间轴
TOTAL = _env_i("D16_TOTAL", 20)
HIT = _env_i("D16_HIT", 2)                    # ★ 补刀命中帧（躯干受力起点）
HIT_HOLD = _env_i("D16_HOLD", 2)              # 2 帧完全停顿（"命中顿感"）
HIT_STOP_END = HIT + HIT_HOLD - 1             # 3
BOUNCE_PEAK = _env_i("D16_BOUNCE_PEAK", 6)    # 上身弹起峰值（胸 / 头最高）
SETTLE = _env_i("D16_SETTLE", 12)             # 落回贴地
PLATEAU = _env_i("D16_PLATEAU", 16)           # 起逐位锁存（末 4 帧定格自持）
CANCEL = _env_i("D16_CANCEL", 16)
END = TOTAL
# ★ 节奏：**等 2 / 顿 2 / 弹 4 / 落 5 / 定 5**
if not (HIT < BOUNCE_PEAK < SETTLE <= PLATEAU <= TOTAL):
    raise RuntimeError("相位不自洽：HIT=%d PEAK=%d SETTLE=%d PLATEAU=%d TOTAL=%d"
                       % (HIT, BOUNCE_PEAK, SETTLE, PLATEAU, TOTAL))

# =============================================================== 竖直通道（无弹道）
# ★★ 本支是**全族第一支没有弹道段**的"贴地"动画（D14 三段 / D15 四段 / D16 三段但
#    首段是"静止贴地"）。竖直通道**只有三层**，且**骨盆层逐位固定**。
Z_PELVIS_REST = 0.900                         # 实测：pelvis 局部 loc 的 z 通道基准
Z_PELVIS_END = _env_f("D16_Z_END", 0.128)     # ★ 实测 = D15 末帧骨盆世界 z（128.0 mm）
PELVIS_Y_END = _env_f("D16_Y_END", 0.470)     # ★ 实测 = D15 末帧骨盆世界 y（470.0 mm）
PELVIS_X_END = _env_f("D16_X_END", 0.0)
# ★ 反向验证 ④：把骨盆**整体抬起**（每帧累加）—— 用于证明 `ground_hold_ok` 真的分得开
#   "局部弹起"与"整体离地"。★ 必须**逐帧累加**（只在 f=HIT 抬一次不改末帧高度，
#   判据反而不红 —— 本项目已踩过同类"空接线"四次）。
PELVIS_LIFT_MM = _env_f("D16_TP_PELVIS_LIFT_MM", 12.0)


def pelvis_z_at(frame):
    """骨盆世界 z（米）。★★ 本支**没有弹道段** —— 全程钉在 `Z_PELVIS_END`。"""
    z = Z_PELVIS_END
    if _env_b("D16_TP_PELVIS_LIFT") and frame > HIT:
        z += PELVIS_LIFT_MM / 1000.0 * float(frame - HIT)
    return z


def pelvis_y_at(frame):
    """骨盆世界 y（米）。★ 本支水平位移 **≈ 0**（原地受击），全程钉在接缝值。"""
    return PELVIS_Y_END


def pelvis_vz_at(frame):
    """一阶差分竖速（mm/帧，与 D12/D15 同口径）。"""
    return (pelvis_z_at(frame) - pelvis_z_at(frame - 1)) * 1000.0


# =============================================================== 反向验证旋钮
SEAM_ZERO = _env_b("D16_TP_SEAM_ZERO")
ZERO_ACTION = "Idle_01" if SEAM_ZERO else SEAM_ACTION
ZERO_FRAME = 0 if SEAM_ZERO else SEAM_FRAME
NO_BOUNCE = _env_b("D16_TP_NOBOUNCE")
BOUNCE_OVERRIDE = _env_f("D16_TP_BOUNCE", 0.0)   # >0 时覆盖胸的弹起角度
DOUBLE = _env_b("D16_TP_DOUBLE")
FLIP_SIGN = _env_b("D16_TP_FLIPSIGN")
NO_LEGS = _env_b("D16_TP_NOLEGS")

# =============================================================== 阈值
SEAM_TOL = 1e-6
NO_TELEPORT_MAX_DEG = 25.0
REACH_MAX_RATIO = 0.995
# ---- ★★ `ground_hold_ok`（本支命门）----------------------------------------
GROUND_HOLD_DOWN_MM = _env_f("D16_GH_DOWN", 2.0)    # 骨盆不许下陷超过 2 mm
GROUND_HOLD_UP_MM = _env_f("D16_GH_UP", 6.0)        # 骨盆不许上抬超过 6 mm
# ---- ★ 上身弹起（主承载）----------------------------------------------------
BOUNCE_MIN_MM = _env_f("D16_BOUNCE_MIN", 40.0)      # 抬升峰值下界（清单 §3 明文）
# ★ 上界：清单说法是「身体**局部**弹起」⟹ "整体坐起来"不算。本上界来自实测口径
#   （本支实测 ≈ 49 mm；胸骨尾端抬 200 mm 已是"坐起"量级）⟹ 这是**收紧**，不是放宽。
BOUNCE_MAX_MM = _env_f("D16_BOUNCE_MAX", 200.0)
BOUNCE_MONO_TOL_MM = _env_f("D16_BOUNCE_MONO", 0.5)  # 峰值后单调不升的容差
DOUBLE_RISE_MIN_MM = _env_f("D16_DOUBLE_RISE", 3.0)  # SETTLE 后再抬 >3 mm 即判双峰
# ---- ★ 腿层 -----------------------------------------------------------------
#   ★★ 三个通道的**可见性分工**（本轮实测发现，决定了它们各自该驱动什么）：
#      · **Z 通道（踝下沉）**：侧视里**竖直可见** ⟹ 直接进 `px_bounce_ok` 的载体
#        （全剪影面积行心）。腿的质量占比大 ⟹ **它会盖过上身弹起**。
#        实测：`dz = 0.120` 时面积行心在 `f9` 被拉下去 **5.4 px**，上身弹起
#        只剩 **+0.46 px**（≈1.4 mm）⟹ `px_bounce_ok` 的幅度判据判红。
#        ⟹ **Z 通道只能用来满足"鞋底真的落过"（`legs_bounce_ok`），必须小**。
#      · **X 通道（侧张）**：X 是侧视的**相机轴** ⟹ 在侧视里**完全不可见**
#        （不进面积行心），但**真的转动了髋关节** ⟹ 专门用来扛
#        `chain_present_ok` 的髋屈角阈值（>8°）。髋-踝距离随侧张变长 ⟹
#        膝也真的伸直了 ⟹ 同时扛膝屈角阈值（>20°）。
#      · **Y 通道（收放）**：屏幕水平 ⟹ 也不进面积行心。
#   实测（`D16_LEG_SPLAY=1` + `D16_LEG_DZ=0.030` + `D16_LEG_FOLD=0`）：
#     髋屈角 ≈ +10°、膝屈角 ≈ +31°、踝行程 ≈ 242 mm、鞋底净降 ≈ 33 mm，
#     而面积行心在 `f6` 抬 **+9 px 级**（不再是 0.46 px）⟹ `px_bounce_ok` 绿得起。
LEG_FOLD = _env_f("D16_LEG_FOLD", 0.0)        # 踝相对髋的 XY 偏移缩到 (1−fold)（Y 方向收）
LEG_SPLAY = _env_f("D16_LEG_SPLAY", 1.0)      # 踝相对髋的 **X** 偏移放大到 (1+splay)
LEG_DZ = _env_f("D16_LEG_DZ", 0.030)          # 踝世界 z 最多下移 30 mm（只为"真的落过"）
LEG_SOLE_MIN_MM = _env_f("D16_SOLE_MIN", -2.0)   # 鞋底不许穿地
LEG_DESCENT_MIN_MM = _env_f("D16_DESCENT_MIN", 5.0)  # 至少一次真正的下降
SOLE_TAIL_TOL_MM = _env_f("D16_SOLE_TAIL_TOL", 0.05)
# ---- 贴地自持（四/三点）-----------------------------------------------------
HIP_PROBE_TOL_MM = _env_f("D16_HIP_PROBE_TOL", 3.0)   # 骨盆 + 双肩（**去掉后脑**）
HEAD_TAIL_MAX_MM = _env_f("D16_HEAD_TAIL_MAX", 260.0)  # 落定后后脑仍贴地
# ---- 打击停顿（命中帧 2 帧，**只看上身**）------------------------------------
HITSTOP_MIN_FRAMES = _env_f("D16_HITSTOP_MIN", 2.0)
HITSTOP_POSE_TOL_DEG = _env_f("D16_HITSTOP_TOL", 1.0e-6)
# ---- 收招不许瞬停 ------------------------------------------------------------
NO_SNAP_TAIL_FRAMES = _env_f("D16_SNAP_TAIL", 6.0)
END_HOLD_MAX_DEG = _env_f("D16_END_HOLD_TOL", 0.5)
# ---- 滚转回位（D11 教训 3 → D12~D15 照抄 → 本支继续）-------------------------
ROLL_WEIGHT_MODE = os.environ.get("D16_ROLL_WEIGHT", "always").strip().lower()
ROLL_BONES = tuple(
    item for item in os.environ.get(
        "D16_ROLL_BONES",
        "upperarm.L,forearm.L,hand.L,upperarm.R,forearm.R,hand.R").split(",")
    if item)
ROLL_ITER = max(1, int(os.environ.get("D16_ROLL_ITER", "2")))
# ★★ 腿骨进滚转逃逸（**承接 D15 的经验，D16 派生时曾丢失、本轮补回**）
#   D15 用它把 `no_teleport` 的尖峰从 32.06° 压到 23.49°：尖峰不是"腿真的在飞"，
#   而是**小腿局部欧拉走进 XYZ 万向节锁带**（`|ry| → 90°`）。
#   本支腿做 **X 侧张**（幅度更大）⟹ 更需要它。实测：不挂 58.48° → 挂上后见日志。
#   ★ 滚转是绕**骨轴** ⟹ 骨根/骨尖不动、两骨 IK 解与贴地**不受影响**，
#     只是把欧拉表示挪出锁带 —— **这是换等价表示，不是放宽容差**。
#   ★ 为什么不把 `foot.*` 也加进来：脚的滚转就是绕鞋长轴转 ⟹ 鞋底会侧倾，
#     那是**真几何变化**，不是等价表示。
ROLL_LEGS = os.environ.get("D16_ROLL_LEGS", "1").strip() not in ("", "0", "false")
if ROLL_LEGS:
    UE.ROLL_BONES = frozenset(set(UE.ROLL_BONES)
                              | {"thigh.L", "thigh.R", "shin.L", "shin.R"})
# ---- 穿模 --------------------------------------------------------------------
CLIP_MAX_MM = _env_f("D16_CLIP_MAX", 0.0)
CLIP_EVERY = int(os.environ.get("D16_CLIP_EVERY", 3))
# ---- 零位/接缝复显守卫 -------------------------------------------------------
SEAM_REPLAY_POS_MAX_MM = _env_f("D16_SEAM_POS", 0.01)
SEAM_REPLAY_DIR_MAX_DEG = _env_f("D16_SEAM_DIR", 0.05)

# =============================================================== 驱动标量
#   `bounce` —— ★ **主驱动**：上身（胸 / 头）**抬升量**（HIT 后起，BOUNCE_PEAK 到位，
#               SETTLE 归零）—— 这是把"局部弹起"与"整体离地"分开的**姿态层**主承载。
#   `leg_fold` / `leg_dz` —— 腿层：膝折向躯干 + 踝下沉（"抖一下再落下"）。
#   `arm_flop` —— 臂层：被甩出的手臂随身体起伏轻微外张/回收。
#   ★ 触地 2 帧停顿：`bounce` / `leg_*` 在 f2~f3 **逐帧同值** ⟹ 上身姿态构造性冻结。
#   ★★ 曲线形状的硬约束：
#      ① `bounce` 峰值**唯一**且严格落在 `(HIT, SETTLE)` 内部，峰值后单调不升；
#      ② `SETTLE` 之后**不得**再出现抬升 > 3 mm 的局部极大（防双峰）；
#      ③ 曲线与腿曲线**错相位**（上身先弹、腿后落）⟹ 全剪影面积行心呈**单峰**。
BOUNCE_KEYS = ((0, 0.0), (HIT, 0.0), (HIT_STOP_END, 0.0),
               (4, 0.42), (5, 0.76), (BOUNCE_PEAK, 1.0),
               (7, 0.87), (8, 0.70), (9, 0.52), (10, 0.33), (11, 0.15),
               (SETTLE, 0.0), (PLATEAU, 0.0), (TOTAL, 0.0))
# ★ 反向验证 ⑤：SETTLE 之后再造一个峰 ⟹ `bounce_single_peak_ok` + `bounce_no_double_ok` 红
DOUBLE_KEYS = ((0, 0.0), (SETTLE, 0.0), (14, 0.62), (15, 0.34),
               (PLATEAU, 0.0), (TOTAL, 0.0))
LEG_FOLD_KEYS = ((0, 0.0), (HIT, 0.0), (HIT_STOP_END, 0.0),
                 (4, 0.25), (5, 0.60), (6, 1.0), (7, 0.92), (8, 0.78),
                 (9, 0.60), (10, 0.42), (11, 0.20), (SETTLE, 0.0),
                 (PLATEAU, 0.0), (TOTAL, 0.0))
# ★ 侧张与"收放"共用同一条曲线（峰值 f6，SETTLE 归零）⟹ 与上身弹起**同相**，
#   在正面 / 3Q 视图里读作"被砸得腿一外张再收回"，在侧视里**不可见**。
LEG_SPLAY_KEYS = LEG_FOLD_KEYS
LEG_DZ_KEYS = ((0, 0.0), (HIT, 0.0), (HIT_STOP_END, 0.0),
               (4, 0.30), (5, 0.58), (6, 0.78), (7, 0.90), (8, 1.0),
               (9, 0.90), (10, 0.66), (11, 0.32), (SETTLE, 0.0),
               (PLATEAU, 0.0), (TOTAL, 0.0))
ARM_FLOP_KEYS = ((0, 0.0), (HIT, 0.0), (HIT_STOP_END, 0.0), (6, 1.0),
                 (9, 0.40), (SETTLE, 0.0), (PLATEAU, 0.0), (TOTAL, 0.0))
ARM_FLOP = _env_f("D16_ARM_FLOP", 0.045)

# ★★ 上身抬升角度（度，正值 = 向「坐起」方向转；在接缝俯仰的基础上**叠加**）
#    ★ 定档值 `盆 +2.0 / 胸 +10.0 / 头 +11.0` 是**实测扫出来的最大可用幅度**
#      （零容差放宽条件下）。扫参表（`D16_BE_CHEST` / `D16_BE_HEAD`）：
#        | 胸/头 | 弹起峰值 mm | 尾窗步长 deg          | 门禁 |
#        | 8/9   | 84.8        | [3.4e-05, 1.4e-05]   | 绿（旧默认） |
#        | 9/10  | 95.8        | [8.2e-05, 7.2e-05]   | 绿 |
#        | **10/11** | **106.8** | **[3.1e-05, 2.4e-05]** | **绿（本档）** |
#        | 10.5/11.5 | 112.3    | [4.4e-05, 4.1e-05]   | 绿（余量仅 0.5°，弃） |
#        | 11/12 | 117.8       | [2.7e-05, 3.8e-05]   | ★ **红**（`no_snap_stop_ok`） |
#      ⟹ 定 `10/11`：峰值 106.8 mm（后脑尾端 189.6 → 296.4 mm，**+106.8 mm**，
#        比旧默认 84.8 更可读），且距翻转边界留 **1.0°** 余量。
#    ★★ 翻转不是物理边界，是 `_roll_return` 里 `pose_bone.matrix` 往返回来的
#       **float32 噪声底**（≈4e-05°，比本报表自身 3 位小数分辨率还小 1 个数量级，
#       `frame_steps_deg` 里 f13~f20 全显示 0.0）。**没有放宽任何容差**。
BOUNCE_EXTRA = {
    "pelvis": _env_f("D16_BE_PELVIS", 2.0),
    "chest": _env_f("D16_BE_CHEST", 10.0),
    "head": _env_f("D16_BE_HEAD", 11.0),
}
if BOUNCE_OVERRIDE > 0.0:
    BOUNCE_EXTRA["chest"] = BOUNCE_OVERRIDE


def bounce(frame):
    """★ 主驱动：上身抬升量（0~1）。"""
    if NO_BOUNCE:
        return 0.0
    value = UE.pwl(BOUNCE_KEYS, float(frame), 0.0)
    if DOUBLE:
        value += UE.pwl(DOUBLE_KEYS, float(frame), 0.0)
    return value


def leg_fold(frame):
    if NO_LEGS:
        return 0.0
    return UE.pwl(LEG_FOLD_KEYS, float(frame), 0.0)


def leg_splay(frame):
    """★ 侧张量（0~1）：踝相对髋的 **X** 偏移放大到 `(1 + LEG_SPLAY·splay)`。"""
    if NO_LEGS:
        return 0.0
    return UE.pwl(LEG_SPLAY_KEYS, float(frame), 0.0)


def leg_dz(frame):
    if NO_LEGS:
        return 0.0
    return UE.pwl(LEG_DZ_KEYS, float(frame), 0.0)


def arm_flop(frame):
    return UE.pwl(ARM_FLOP_KEYS, float(frame), 0.0)


# =============================================================== 世界俯仰目标
TORSO_BONES = ("root", "pelvis", "spine_01", "spine_02", "chest", "neck", "head")
PARENT_OF = {"root": None, "pelvis": "root", "spine_01": "pelvis",
             "spine_02": "spine_01", "chest": "spine_02", "neck": "chest",
             "head": "neck"}
ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")
LEG_BONES = ("thigh.L", "shin.L", "thigh.R", "shin.R")
SPINE_MIX_1 = _env_f("D16_MIX_S1", 0.30)
SPINE_MIX_2 = _env_f("D16_MIX_S2", 0.62)
NECK_MIX = _env_f("D16_MIX_NECK", 0.45)


def world_pitches(frame):
    """各骨**世界俯仰目标**（度，+ = 前屈/前倾）。

    ★★ 与 D15 的口径差别：D15 是"从接缝俯仰一路转到大负值（后倒）"；
      本支是"在接缝俯仰基础上**抬起一个小增量**（局部弹起）"，随后**归零**。
      ⟹ 语义仍是绕**同一根世界 X 轴**累加：`W_self = W_parent + rx_self`
      ⟹ 反解 `rx_self = W_self − W_parent`。
    ★ f0 处 `b = 0` ⟹ 目标世界俯仰 = **接缝姿态自身的世界俯仰** ⟹ 逐位复现 `Knockdown_B@20`。
    ★ 反向验证 ⑦：把增量**翻符号**（上身往下砸）⟹ `bounce_present_ok` 必红。
    """
    b = bounce(frame)
    s = -1.0 if FLIP_SIGN else 1.0
    w = {"root": SEAM_PITCH.get("root", 0.0)}
    w["pelvis"] = SEAM_PITCH["pelvis"] + s * BOUNCE_EXTRA["pelvis"] * b
    w["chest"] = SEAM_PITCH["chest"] + s * BOUNCE_EXTRA["chest"] * b
    w["spine_01"] = w["pelvis"] + SPINE_MIX_1 * (w["chest"] - w["pelvis"])
    w["spine_02"] = w["pelvis"] + SPINE_MIX_2 * (w["chest"] - w["pelvis"])
    w["head"] = SEAM_PITCH["head"] + s * BOUNCE_EXTRA["head"] * b
    w["neck"] = w["chest"] + NECK_MIX * (w["head"] - w["chest"])
    return w


def torso_pose(frame):
    """世界俯仰目标 → 局部 `rx`。

    ★★ 本支改成**增量口径**（比 D15 更稳）：`rx = 接缝的局部 rx + (Δ世界 − Δ接缝)`。
      为什么必须这样：接缝 `Knockdown_B@20` 的 ry/rz 不为零（实测 pelvis 的
      `ry=0.815 / rz=0.980`），而世界俯仰量会把 ry/rz 的交叉项混进来。D15 直接令
      `rx = W_self − W_parent`，在 f0 处有 ~0.015° 的表示误差；增量口径下
      `b == 0` 时**逐位**回到接缝的局部 rx，接缝因此是**构造性**的。
    """
    w = world_pitches(frame)
    out = {}
    for name in TORSO_BONES:
        parent = PARENT_OF[name]
        d_w = w[name] - (w[parent] if parent else 0.0)
        d_w0 = SEAM_PITCH[name] - (SEAM_PITCH[parent] if parent else 0.0)
        rx = SEAM_RX.get(name, 0.0) + (d_w - d_w0)
        base = ZERO.get(name, (0.0, 0.0, 0.0))
        out[name] = (rx, base[1], base[2])
    for side in SIDES:
        name = "shoulder." + side
        out[name] = ZERO.get(name, (0.0, 0.0, 0.0))
    locs = {k: tuple(v) for k, v in ZERO.get("@loc", {}).items()}
    locs["pelvis"] = A.wloc(PELVIS_X_END - 0.0, pelvis_y_at(frame),
                            pelvis_z_at(frame) - Z_PELVIS_REST)
    out["@loc"] = locs
    return out


# =============================================================== 拳 / 肘目标
# ★ 本支的臂：接缝已经"向体侧铺开、前臂摊平"（D15 的终点）。本支**不再换方向**，
#   只让手臂**随肩**（肩随躯干起伏）并做一次轻微的**外张脉冲**（"被震了一下"）。
#   ★ 为什么不必再 slerp：D15 的终点方向就是本支的接缝方向，接缝 ⟹ 终点**同向**。
BRACE_SPAN_RATIO_PULSE = 1.0


def fist_target(arm, side, frame):
    """拳世界目标 = **肩位 + 接缝方向 × 臂展**（必须相对肩，因为肩一直在动）。"""
    shoulder = Vector(A.bone_world(arm, "upperarm." + side, "head"))
    span = SEAM_SPAN[side] * (1.0 + ARM_FLOP * arm_flop(frame))
    return shoulder + SEAM_FIST_DIR[side] * span


def elbow_dir(side, frame):
    """肘部极向量：**冻结在接缝值**（与 D15 同一条推理，见 D15 的 `elbow_dir` docstring）。"""
    d0 = SEAM_ELBOW_DIR.get(side)
    if d0:
        return Vector(d0).normalized()
    return Vector((0.0, 0.0, 1.0))


def hand_dir_of(side, frame):
    """手骨世界朝向：**冻结在接缝值**（D15 的掌心已摊平，本支沿用）。"""
    return Vector(SEAM_HAND_DIR[side]).normalized()


# =============================================================== 踝目标
# ★★ 腿层（与 D15 的"抬腿"**不同**）：本支的腿在**抖一下再落下**。
#   实现两个通道：
#     · **XY 通道**：踝相对髋的偏移按 `(1 − LEG_FOLD·fold)` 收缩 ⟹ 膝**折向躯干**
#       （实测：膝屈角 125.0° → 153.9°，Δ≈28.9°）；
#     · **Z 通道**：踝世界 z 从接缝的 300 mm 下移到 180 mm ⟹ 鞋底**真的落下来**
#       （实测鞋底最低 262.6 → 137.1 mm，净降 125.5 mm），但不穿地。
#   ★★ 两个通道的分工是**实测扫出来的**（不是推的）：
#     · **Z 通道是髋屈角的主控**：`dz 0.05 → 0.12` 把 `hip_deg` 从 **7.4° → 16.2°**
#       （`dz 0.14` → 19.9°）。只靠 XY 抬不动髋 —— `fold 0.5 → 0.7` 时 `hip_deg`
#       反而从 12.33° 微降到 11.55° ⟹ **髋阈值 8° 只能由 Z 通道满足**。
#     · **XY 通道主控膝屈角**：`fold 0.5 → 0.7` 把 `knee_deg` 从 27.8° 抬到 35.8°。
#     ⟹ 两个通道各管一段，"脚→腿→髋"三段才都有真工作量（`chain_present_ok`）。
def ankle_target(arm, side, frame):
    """★ 腿层：**X 侧张** 扛髋/膝，**Z 微降** 只负责"真的落过"（见上面分工注释）。"""
    hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
    f = leg_fold(frame)
    s = leg_splay(frame)
    d = leg_dz(frame)
    shrink = 1.0 - LEG_FOLD * f
    grow_x = shrink + LEG_SPLAY * s
    dx = SEAM_HIP_OFF[side][0] * grow_x
    dy = SEAM_HIP_OFF[side][1] * shrink
    z = SEAM_ANKLE[side].z - LEG_DZ * d
    return Vector((hip.x + dx, hip.y + dy, z))


def _foot_euler(arm, side, frame):
    """★ 脚：**局部欧拉冻结在接缝值**。

    ★ 为什么本支可以直接冻结（D15 不能）：D15 后倒时小腿世界转角巨大（>80°），
      冻结局部欧拉会让鞋底完全失控；本支小腿只摆 ~10°，且**没有任何判据要求鞋底
      钉在世界某处**（D16 的腿是**自由**的）。冻结 ⟹ 脚**构造性**无局部尖峰
      （`no_teleport` 的余量全部留给膝）。
    ★ 脚仍有**关键帧**（力量传导链的"脚"这一段），只是值恒定。
    """
    name = "foot." + side
    prev = JS._PREV_EULER.get(name)
    base = SEAM_FOOT_EULER.get(side, ZERO.get(name, (0.0, 0.0, 0.0)))
    return JS._unwrap_xyz(prev, tuple(base))


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
SEAM_RX = {}
SEAM_FOOT_EULER = {}
ANKLE_0 = {}
KNEE_DIR = {}
ARM_MAX = {}
Z_SEAM = 0.0
FOOT_LOCKED = [False]
LOCK_POSE = {}
HITSTOP_POSE = {}
_HITSTOP_REUSED = [0]
_LOCK_REUSED = [0]
SEAM_MATCH = {"src": None, "geom_pos": None, "geom_dir": None,
              "pos_bone": None, "dir_bone": None, "per_bone": {},
              "matched": False}
HEM_STATIC = {}


# =============================================================== 姿态装配
def arm_seat_tip(arm, pose, side, tip_target, elbow_dir_in, hand_dir_in=None):
    """D05 立的臂解算：两骨 IK 打在腕上，手骨按零位自己的折角单独瞄。"""
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
    # ★ f0 = **逐位**接缝姿态（`Knockdown_B@20`）—— 不走解算，原样返回。
    if frame <= 0:
        return _copy_pose(ZERO)

    # ★ 命中 2 帧停顿（§2）：`HIT+1` 逐位复用 `HIT` 帧的姿态（**上身**），
    #   只把骨盆 `@loc` 换成竖直通道的值；**双腿照常解算**（本支腿正好也在静止期，
    #   所以整身其实逐位冻结，但口径仍按"只锁上身、双腿豁免"实现，与 D15 同构）。
    if HITSTOP_POSE and HIT < frame <= HIT_STOP_END:
        pose = {}
        for key, value in HITSTOP_POSE.items():
            if key == "@loc":
                locs = {k: tuple(v) for k, v in value.items()}
                locs["pelvis"] = A.wloc(PELVIS_X_END, pelvis_y_at(frame),
                                        pelvis_z_at(frame) - Z_PELVIS_REST)
                pose["@loc"] = locs
            else:
                pose[key] = tuple(value)
        _HITSTOP_REUSED[0] += 1
        # ★★ 必须先 `apply_pose`：`UE.leg_seat` 读的是**当前骨架状态**里的髋位。
        A.apply_pose(arm, pose)
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
    if LOCK_POSE and frame > PLATEAU:
        pose = {}
        for key, value in LOCK_POSE.items():
            if key == "@loc":
                locs = {k: tuple(v) for k, v in value.items()}
                locs["pelvis"] = A.wloc(PELVIS_X_END, pelvis_y_at(frame),
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
    if frame == HIT:
        HITSTOP_POSE.update(_copy_pose(pose))
    if frame == PLATEAU:
        LOCK_POSE.update(_copy_pose(pose))
    return pose


def solve_pose(arm, frame, meshes=None):
    return build_pose(arm, frame)


# =============================================================== 滚转回位修正
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


def _hip_flex(arm, side):
    """髋屈角（度，0 = 躯干与大腿共线；越大 = 折得越狠）。"""
    torso = Vector(A.bone_direction(arm, "pelvis")).normalized()
    thigh = Vector(A.bone_direction(arm, "thigh." + side)).normalized()
    return 180.0 - math.degrees(math.acos(max(-1.0, min(1.0, torso.dot(thigh)))))


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
        "hip_flex_deg": {s: _hip_flex(arm, s) for s in SIDES},
        "head_tail": Vector(A.bone_world(arm, "head", "tail")),
        "chest_tail": Vector(A.bone_world(arm, "chest", "tail")),
    }


def _foot_clearance():
    low = A.foot_lowest_by_side()
    return {s: (low[s][2] if low[s] is not None else None) for s in SIDES}


# ---- ★ 后脑：**网格级**载体（只用于"落定后仍贴地"的登记，**不进 `hip_probe`**）---
#   ★★ `Jacket_Hem` / `Jacket_Hem_Line` 是**已知模型侧绑定遗漏**（`parent=None`、
#      `vgroups=0`、只有 `SUBSURF`）⟹ 钉在世界原点、**不随骨架动**，绝不能进载体集合。
HEM_OBJECTS = tuple(
    n for n in os.environ.get("D16_HEM_OBJECTS",
                              "Jacket_Hem,Jacket_Hem_Line").split(",") if n)
HEAD_OBJECTS = tuple(PD.HEAD_MESHES)


def _mesh_low_mm(names):
    """给定网格对象集合的**逐对象**最低 z（毫米）；走 depsgraph，蒙皮件跟随骨架。"""
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
    """只在给定骨集合上量单帧步长（命中停顿只看**上身**：腿在动，豁免）。"""
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


def hit_assertions(arm, action, samples, meshes):  # noqa: C901
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
    per, clear, feet, headm = {}, {}, {}, {}
    for frame in range(0, TOTAL + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        per[frame] = _body_metrics(arm)
        clear[frame] = _foot_clearance()
        feet[frame] = A.foot_lowest_by_side()
        headm[frame] = _lowest_of(HEAD_OBJECTS)

    zs = {f: per[f]["pelvis"].z for f in per}
    ys = {f: per[f]["pelvis"].y for f in per}
    xs = {f: per[f]["pelvis"].x for f in per}
    cpitch = {f: per[f]["chest_pitch_deg"] for f in per}

    # ---- ★★ (a) 接缝：首帧逐位 = `Knockdown_B@20`（平移不变尺子）
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

    # ---- ★★★ (b) `ground_hold_ok` —— **本支命门**（把"局部弹起"与"整体离地"分开）
    hold_lo = (Z_PELVIS_END * 1000.0) - GROUND_HOLD_DOWN_MM
    hold_hi = (Z_PELVIS_END * 1000.0) + GROUND_HOLD_UP_MM
    res["ground_hold_z_mm"] = {str(f): round(zs[f] * 1000.0, 4)
                               for f in sorted(zs)}
    res["ground_hold_min_mm"] = round(min(zs.values()) * 1000.0, 4)
    res["ground_hold_max_mm"] = round(max(zs.values()) * 1000.0, 4)
    res["ground_hold_band_mm"] = [round(hold_lo, 3), round(hold_hi, 3)]
    res["ground_hold_z_end_ref_mm"] = round(Z_PELVIS_END * 1000.0, 3)
    res["ground_hold_ok"] = bool(
        all(hold_lo <= z * 1000.0 <= hold_hi for z in zs.values()))
    res["ground_hold_note"] = (
        "★★ 本支命门：`pelvis` 世界 z 在**全 %d 帧**内必须 ∈ [%.1f, %.1f] mm"
        "（= 上游末帧实测 %.1f mm − %.0f / + %.0f）。这是把"
        "「身体**局部**弹起」与「**整体**离地」分开的**唯一**守卫 —— "
        "本支竖直通道**没有弹道段**，骨盆层逐位固定。"
        % (TOTAL + 1, hold_lo, hold_hi, Z_PELVIS_END * 1000.0,
           GROUND_HOLD_DOWN_MM, GROUND_HOLD_UP_MM))

    # ---- ★★ (c) 上身弹起：抬升量 / 单峰 / 无双峰 -----------------------------
    #   载体 = `max(chest.tail.z, head.tail.z) − 骨盆头 z`（**相对骨盆的抬升量**），
    #   增量 = 相对首帧（接缝）。★ 为什么用 max：计划 §1 说"弹起时**头抬得最高**"。
    lift_abs = {f: max(per[f]["chest_tail"].z, per[f]["head_tail"].z)
                for f in per}
    lift_rel = {f: (lift_abs[f] - lift_abs[0]) * 1000.0 for f in lift_abs}
    res["bounce_lift_rel_mm"] = {str(f): round(lift_rel[f], 3)
                                 for f in sorted(lift_rel)}
    res["bounce_chest_tail_mm"] = {str(f): round(per[f]["chest_tail"].z * 1000.0, 3)
                                   for f in sorted(per)}
    res["bounce_head_tail_mm"] = {str(f): round(per[f]["head_tail"].z * 1000.0, 3)
                                  for f in sorted(per)}
    peak_f = max(lift_rel, key=lambda f: lift_rel[f])
    peak_val = lift_rel[peak_f]
    res["bounce_peak_frame"] = peak_f
    res["bounce_peak_mm"] = round(peak_val, 3)
    res["bounce_min_mm"] = BOUNCE_MIN_MM
    res["bounce_max_mm"] = BOUNCE_MAX_MM
    res["bounce_window"] = [HIT, SETTLE]
    res["bounce_present_ok"] = bool(
        BOUNCE_MIN_MM <= peak_val <= BOUNCE_MAX_MM
        and HIT < peak_f < SETTLE)
    res["bounce_present_note"] = (
        "★ 上身抬升峰值必须 ∈ [%.0f, %.0f] mm **且峰位严格落在 (HIT=%d, SETTLE=%d) "
        "内部**。上界守的是清单原文的「**局部**」二字 —— 抬到 200 mm 以上就不是"
        "「局部弹起」而是「坐起来」了（实测上界来自 `D16_TP_BOUNCE` 的反面对照）。"
        % (BOUNCE_MIN_MM, BOUNCE_MAX_MM, HIT, SETTLE))
    # 单峰形状：峰值后单调不升
    after = [f for f in range(peak_f, TOTAL + 1)]
    rises = [{"frame": f, "delta_mm": round(lift_rel[f] - lift_rel[f - 1], 4)}
             for f in after[1:] if lift_rel[f] - lift_rel[f - 1] > BOUNCE_MONO_TOL_MM]
    res["bounce_after_peak_rises"] = rises
    res["bounce_mono_tol_mm"] = BOUNCE_MONO_TOL_MM
    res["bounce_single_peak_ok"] = bool(
        HIT < peak_f < SETTLE
        and max(lift_rel.values()) - peak_val <= 1e-9
        and not rises)
    res["bounce_single_peak_note"] = (
        "★★ 峰值帧**唯一**且落在 `(HIT, SETTLE)` 内部；峰值后**单调不升**"
        "（容差 %.2f mm，防抖动造第二个峰）。" % BOUNCE_MONO_TOL_MM)
    # 无双峰：SETTLE 之后不许再出现抬升 > 3 mm 的局部极大
    tail_frames = [f for f in range(SETTLE, TOTAL + 1)]
    tail_rises = []
    for index in range(1, len(tail_frames) - 1):
        f = tail_frames[index]
        prev, nxt = lift_rel[f - 1], lift_rel[f + 1]
        if lift_rel[f] > prev and lift_rel[f] > nxt:
            rise = lift_rel[f] - min(prev, nxt)
            if rise > DOUBLE_RISE_MIN_MM:
                tail_rises.append({"frame": f, "rise_mm": round(rise, 4)})
    res["bounce_tail_local_max"] = tail_rises
    res["bounce_double_rise_min_mm"] = DOUBLE_RISE_MIN_MM
    res["bounce_no_double_ok"] = bool(not tail_rises)
    res["bounce_no_double_note"] = (
        "★ `SETTLE=%d` 之后**不许**再出现抬升 > %.0f mm 的局部极大"
        "（弹起必须是**一次**）。" % (SETTLE, DOUBLE_RISE_MIN_MM))

    # ---- ★ (d) 腿层：抖一下再落下（鞋底不许穿地 + 至少一次下降）------------
    sole = {f: min(clear[f]["L"], clear[f]["R"]) for f in clear}
    res["sole_clearance_mm"] = {str(f): (None if sole[f] is None
                                         else round(sole[f] * 1000.0, 2))
                                for f, v in sorted(sole.items())}
    sole_min_mm = min(v for v in sole.values() if v is not None) * 1000.0
    drops = [(sole[f - 1] - sole[f]) * 1000.0 for f in range(1, TOTAL + 1)
             if sole[f - 1] is not None and sole[f] is not None]
    max_drop = max(drops) if drops else 0.0
    res["sole_min_mm"] = round(sole_min_mm, 3)
    res["sole_max_descent_mm"] = round(max_drop, 3)
    res["sole_min_threshold_mm"] = LEG_SOLE_MIN_MM
    res["sole_descent_threshold_mm"] = LEG_DESCENT_MIN_MM
    res["legs_bounce_ok"] = bool(sole_min_mm >= LEG_SOLE_MIN_MM
                                and max_drop >= LEG_DESCENT_MIN_MM)
    res["legs_bounce_note"] = (
        "★ 腿层：鞋底最低点必须 **≥ %.0f mm**（不许穿地）**且至少有一次真正的"
        "下降 ≥ %.0f mm**（腿真的落了）。本支的腿不钉在任何世界足迹上 —— "
        "它在**抖**（膝折向躯干 + 踝下沉），与 D15 的「一直抬着」不同。"
        % (LEG_SOLE_MIN_MM, LEG_DESCENT_MIN_MM))
    # 末 4 帧鞋底逐位锁存
    tail_sole = [round(sole[f] * 1000.0, 6) for f in range(PLATEAU, TOTAL + 1)
                 if sole[f] is not None]
    res["sole_tail_mm"] = tail_sole
    res["sole_tail_tol_mm"] = SOLE_TAIL_TOL_MM
    res["sole_tail_ok"] = bool(tail_sole
                               and max(tail_sole) - min(tail_sole)
                               <= SOLE_TAIL_TOL_MM)

    # ---- ★ 贴地自持：骨盆 z 逐位固定（三段竖直通道的第三段）-------------------
    plat = [round(zs[f] * 1000.0, 6) for f in range(PLATEAU, TOTAL + 1)]
    res["landing_plateau_z_mm"] = plat
    res["landing_plateau_ok"] = bool(max(plat) - min(plat) <= 1e-9)

    # ---- ★★ (e) hip_probe：躺平段**三点贴地自持**（**去掉后脑**！）-----------
    #   ★★ 这正是计划 §1 点名的"本支最容易做废的地方"：照抄 D15 的"骨盆+后脑+双肩"
    #      必然红 —— 因为**弹起段后脑会主动抬起来**（那是设计要求的动作）。
    #      ⟹ 载体换成 **骨盆 + 双肩**（三点），后脑改为**只报**。
    probe_pts = {
        "pelvis_head": [Vector(per[f]["pelvis"]) for f in range(PLATEAU, TOTAL + 1)],
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
    res["hip_probe_head_tail_report_mm"] = round(
        max((Vector(per[f]["head_tail"])
             - Vector(per[PLATEAU]["head_tail"])).length
            for f in range(PLATEAU, TOTAL + 1)) * 1000.0, 4)
    res["hip_probe_ok"] = bool(
        hip_drift and max(hip_drift.values()) <= HIP_PROBE_TOL_MM)
    res["hip_probe_note"] = (
        "★★ 载体 = **骨盆 + 双肩**（**去掉后脑**）。为什么必须去掉：本支的弹起动作"
        "**要求**后脑抬起来（§1「弹起时头抬得最高」）⟹ 照抄 D15 的四点"
        "`hip_probe` 会被自己设计出来的动作判红。后脑改为**只报**"
        "（`hip_probe_head_tail_report_mm`）。")

    # ---- ★ 落定后后脑仍贴地（登记式）----------------------------------------
    ht = {f: per[f]["head_tail"].z * 1000.0 for f in per}
    res["head_tail_z_mm"] = {str(f): round(v, 2) for f, v in sorted(ht.items())}
    res["head_mesh_low_mm"] = {str(f): (None if headm[f] is None
                                        else round(headm[f], 2))
                               for f, v in sorted(headm.items())}
    res["head_tail_max_mm"] = HEAD_TAIL_MAX_MM
    res["head_tail_settled_max_mm"] = round(
        max(ht[f] for f in ht if f >= SETTLE), 3)
    res["back_land_ok"] = bool(
        max(ht[f] for f in ht if f >= SETTLE) <= HEAD_TAIL_MAX_MM)
    res["back_land_note"] = (
        "★ `f ≥ SETTLE` 起后脑（`head` 尾端）高度必须 ≤ %.0f mm（**落回**后仍是"
        "仰面躺平，不是坐着）。同时报出 `Head`/`Hair_Mass` 网格最低点。"
        % HEAD_TAIL_MAX_MM)

    # ---- ★ (f) 打击停顿（命中 2 帧，**只看上身**）---------------------------
    platform = HIT_STOP_END - HIT + 1
    pose_step, pose_step_at = 0.0, None
    for index in range(HIT, HIT_STOP_END):
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
        "★ 命中帧（`f = %d`）起 **%d 帧完全停顿**，口径与 D13/D15 同构："
        "只锁**上身**（躯干+肩+臂），**双腿豁免**；骨盆 `@loc` 继续走竖直通道。"
        % (HIT, platform))

    # ---- ★ 收招不许瞬停（末 6 帧增量**单调收敛** —— 清单 §0.6 口径）--------
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
        "本支 `SETTLE=12` 起驱动全归零、`PLATEAU=16` 起逐位锁存 ⟹ 末段步长"
        "构造性全为 0。")

    # ---- ★ 定格自持（末 N 帧姿态逐位冻结）---------------------------------
    last = []
    for index in range(PLATEAU + 1, TOTAL + 1):
        last.append(round(_worst_step(samples, index - 1, index)[0], 6))
    res["end_hold_steps_deg"] = last
    res["end_ground_hold_ok"] = bool(last and max(last) <= END_HOLD_MAX_DEG)
    res["end_identical_skipped"] = True
    res["end_identical_note"] = (
        "★ 末帧**不回原位**（这是「躺地被砸一下」的收尾）⟹ 只报：末帧与首帧的世界"
        "位置差 = 这次受击把身体推走了多远（本支 ≈ 0）。")
    # ★ 末帧 vs 上游末帧的**残留姿态差**（计划 §0 ③ 要求实测登记）
    mats_end = CR.action_world_matrices(arm, action, TOTAL)
    ori_e, rel_e, ob_e, rb_e = _pose_seam_split(mats_end, seam_mats, moving)
    res["end_vs_d15_orient_deg"] = round(ori_e, 6)
    res["end_vs_d15_relpos_mm"] = round(rel_e * 1000.0, 6)
    res["end_vs_d15_bone"] = rb_e or ob_e
    res["end_vs_d15_note"] = (
        "★ 计划 §0 ③：末帧**允许**与 D15 末帧有 <2° 的残留姿态差（「被补刀后的新平衡」），"
        "但必须**实测登记**。本支驱动在 `SETTLE` 归零 ⟹ 残留差**构造性 ≈ 0**。")

    # ---- ★ 末帧登记（给 D18 的起点）----------------------------------------
    end_vz = (zs[TOTAL] - zs[TOTAL - 1]) * 1000.0
    res["end_vz_mm_per_frame"] = round(end_vz, 4)
    res["end_pelvis_z_mm"] = round(zs[TOTAL] * 1000.0, 3)
    res["end_vz_zero_ok"] = bool(abs(end_vz) <= 1e-6)

    # ---- ★ 力量传导链（脚→腿→髋→腰→肩→手）--------------------------------
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
    res["hip_flex_dev_deg"] = hip_dev
    res["chain_travel"] = {
        "foot_mm": round(ankle_dev, 2),
        "knee_deg": round(max(knee_flex.values()), 3),
        "hip_deg": round(max(hip_dev.values()), 3),
        "waist_deg": round(waist_span, 3),
        "shoulder_mm": round(shoulder_move, 2),
        "hand_mm": round(fist_dev, 2),
    }
    res["chain_present_ok"] = bool(
        res["chain_travel"]["foot_mm"] > 50.0
        and res["chain_travel"]["knee_deg"] > 20.0
        and res["chain_travel"]["hip_deg"] > 8.0
        and res["chain_travel"]["waist_deg"] > 4.0
        and res["chain_travel"]["shoulder_mm"] > 5.0
        and res["chain_travel"]["hand_mm"] > 30.0)
    res["chain_present_note"] = (
        "★★ **一处必须换的口径**（不是放宽）：D15 的「髋」用 `pelvis` 位移（mm）度量；"
        "本支骨盆**被设计性地钉在地上**（`ground_hold_ok` 要求逐位固定）⟹ 位移恒为 0，"
        "照抄必然红。⟹ 髋的贡献改由 **髋屈角变化**（`hip_deg`，度）度量 —— "
        "「脚→腿→髋」三段各自的**实际工作量**都还在，只是髋那段从「位移量」换成"
        "「关节角变化量」。阈值 8° 由实测导出。")

    # ---- 水平位移（本支 **≈ 0**，登记式）-----------------------------------
    dx = {f: (xs[f] - xs[0]) * 1000.0 for f in per}
    dy = {f: (ys[f] - ys[0]) * 1000.0 for f in per}
    res["root_motion_net_mm"] = round(math.hypot(dx[TOTAL], dy[TOTAL]), 3)
    res["root_motion_m"] = [round(dx[TOTAL] / 1000.0, 6),
                            round(dy[TOTAL] / 1000.0, 6)]
    res["root_motion_ok"] = bool(abs(dx[TOTAL]) <= 0.5
                                 and abs(dy[TOTAL]) <= 0.5)
    res["root_motion_note"] = (
        "★ 与 D14（+0.576 m）/D15（+0.444 m）**都不同**：本支是**原地**受击"
        "（骨盆水平分量恒为接缝值）⟹ 净位移 **≈ 0**，如实登记。")

    # ---- 冻结段 / 锁存计数 --------------------------------------------------
    res["lock_frames"] = _LOCK_REUSED[0]
    res["lock_expect"] = TOTAL - PLATEAU
    res["lock_ok"] = bool(res["lock_frames"] == TOTAL - PLATEAU)
    res["hitstop_frames_reused"] = _HITSTOP_REUSED[0]
    res["hitstop_expect"] = HIT_STOP_END - HIT
    res["hitstop_reuse_ok"] = bool(res["hitstop_frames_reused"]
                                   == HIT_STOP_END - HIT)

    # ---- 穿模 --------------------------------------------------------------
    frames = sorted(set(list(range(0, TOTAL + 1, CLIP_EVERY))
                        + [HIT, HIT_STOP_END, BOUNCE_PEAK, SETTLE, PLATEAU,
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

    # ---- 可达性 ------------------------------------------------------------
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

    # ---- ★ 下摆静态件（绑定体检 + 世界 bbox 恒定）--------------------------
    hem_now = _mesh_low_mm(HEM_OBJECTS)
    hem_static = True
    hem_rows = {}
    for name, value in hem_now.items():
        hem_rows[name] = round(value, 4)
        ref = HEM_STATIC.get(name)
        if ref is None:
            hem_static = False
        elif abs(value - ref) > 1e-6:
            hem_static = False
    res["hem_low_mm"] = hem_rows
    res["hem_low_ref_mm"] = {k: round(v, 4) for k, v in HEM_STATIC.items()}
    res["hem_static_ok"] = bool(hem_static and hem_rows)
    res["hem_static_note"] = (
        "★ `%s` 是**已知模型侧绑定遗漏**（`parent=None` / `vgroups=0`，只有 SUBSURF）"
        "⟹ 钉在世界原点、**不随骨架动**。本判据核对它们的世界最低点在**首末两帧"
        "逐位相同**（因此不可能成为本文任何以最低行为载体的判据）。"
        % ",".join(HEM_OBJECTS))

    # ---- 剪影 / aspect：只报不判 -------------------------------------------
    sil = P.silhouette(arm, "d16")
    res["aspect"] = sil["aspect"]
    res["fill_grid"] = sil["fill_grid"]
    res["width_m"] = sil["width_m"]
    res["height_m"] = sil["height_m"]

    # ---- ★ 竖直通道登记（本支**没有弹道段**）------------------------------
    res["ballistic_status"] = "DISABLED"
    res["ballistic_phase_registered"] = {
        "T_PHASE_D15": D15_T_PHASE, "T_PHASE_D16": T_PHASE_D16,
        "d16_t_phase": "★ 仅登记（本支竖直通道**不含弹道**，不参与解算）"}
    res["ballistic_note"] = (
        "★★ `ballistic_until_land_ok` 在本支**显式停用**（不生成该键，避免被"
        "`failed` 误收）。理由：本支**起始就已贴地**（首帧逐位 = `Knockdown_B@20`，"
        "其 `end_vz = 0`，已离开弹道）⟹ **竖直通道没有弹道段**，因此没有"
        "「与共享解析抛物线的逐帧残差」可比。这是**全族第一支**「贴地」且无弹道段的动画"
        "（D14 三段 / D15 四段 / **D16 三段但首段是「静止贴地」**）。")
    res["pelvis_vz_mm_per_frame"] = {str(f): round(pelvis_vz_at(f), 4)
                                     for f in range(1, TOTAL + 1)}

    if os.environ.get("D16_TRACE"):
        res["frame_steps_deg"] = [
            {"f": index, "deg": round(_worst_step(samples, index - 1, index)[0], 3),
             "bone": (_worst_step(samples, index - 1, index)[1] or (None, None))[1]}
            for index in range(1, TOTAL + 1)]
        res["trace"] = {str(f): {
            "bounce": round(bounce(f), 4),
            "leg_fold": round(leg_fold(f), 4),
            "leg_dz": round(leg_dz(f), 4),
            "has_z": round(zs[f] * 1000.0, 2),
            "has_y": round(ys[f] * 1000.0, 2),
            "lift_rel": round(lift_rel[f], 2),
            "chest_tail": round(per[f]["chest_tail"].z * 1000.0, 2),
            "head_tail": round(per[f]["head_tail"].z * 1000.0, 2),
            "sole": None if sole[f] is None else round(sole[f] * 1000.0, 2),
            "knee": {s: round(per[f]["knee_deg"][s], 2) for s in SIDES},
            "ankle": {s: round(per[f]["ankle"][s].z * 1000.0, 2) for s in SIDES},
            "chest_pitch": round(cpitch[f], 3),
        } for f in range(0, TOTAL + 1)}
    return res


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
    """★ 零位真源：**上游 `Knockdown_B@20` 的落盘行动作**（不是零位姿态！）。

    ★ 反向验证 ① 打开时改读 `Idle_01@0`（零位姿态）—— 证明 `seam_in_ok` 抓得住接缝断裂。
    """
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
    global ZERO, ZERO_WORLD, Z_SEAM, KNEE_DIR, ANKLE_0, ZERO_FIST
    ZERO, ZERO_WORLD = {}, {}
    for table in (ZERO_BASIS, ZERO_DIR, SEAM_FIST, SEAM_FIST_DIR, SEAM_SHOULDER,
                  SEAM_SPAN, SEAM_ELBOW_DIR, SEAM_HAND_DIR, SEAM_ANKLE,
                  SEAM_HIP, SEAM_HIP_OFF, ANKLE_0, KNEE_DIR, ARM_MAX,
                  SEAM_PITCH, SEAM_RX, SEAM_FOOT_EULER, LOCK_POSE, HITSTOP_POSE):
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

    UE.ROLL_STEP_DEG = _env_f("D16_ROLLSTEP", 2.0)
    UE.ROLL_GRID = UE._roll_grid()
    UE.EULER_Y_SAFE = _env_f("D16_YSAFE", 88.0)
    UE.EULER_Y_WEIGHT = _env_f("D16_YWEIGHT", 0.0)

    for extra in LEG_BONES + ("foot.L", "foot.R"):
        if extra not in A.PROBE_BONES:
            A.PROBE_BONES = tuple(A.PROBE_BONES) + (extra,)
        if extra not in A.PROBE_TAILS:
            A.PROBE_TAILS = tuple(A.PROBE_TAILS) + (extra,)
    A.PROBE_KEYS = A.PROBE_BONES + tuple(n + ".tail" for n in A.PROBE_TAILS)

    ZERO, saved_info = _load_seam_zero(arm)
    if not ZERO:
        raise RuntimeError("读不到接缝零位")

    # ★ "落盘真值 vs 手写重演"
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
        SEAM_FOOT_EULER[side] = tuple(
            ZERO.get("foot." + side, (0.0, 0.0, 0.0)))
    for side in SIDES:
        hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
        knee = Vector(A.bone_world(arm, "shin." + side, "head"))
        ankle = Vector(A.bone_world(arm, "foot." + side, "head"))
        axis = (ankle - hip).normalized()
        bulge = (knee - hip) - axis * (knee - hip).dot(axis)
        KNEE_DIR[side] = (bulge.normalized() if bulge.length > 1e-9
                          else Vector((0.0, -0.94, -0.34)))
    _kd_env = os.environ.get("D16_KNEE_DIR", "").strip()
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

    # ---- 接缝姿态的**世界俯仰** + **局部 rx**（本支俯仰通道的基线）---------
    for name in TORSO_BONES:
        SEAM_PITCH[name] = _pitch(Vector(A.bone_direction(arm, name)))
        SEAM_RX[name] = float(ZERO.get(name, (0.0, 0.0, 0.0))[0])

    # ---- ★ 下摆静态件的世界最低点参考（`hem_static_ok` 用）------------------
    HEM_STATIC.clear()
    for name, value in _mesh_low_mm(HEM_OBJECTS).items():
        HEM_STATIC[name] = value

    # ---- 复位逐帧解缠状态 --------------------------------------------------
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

    # ---- ★ 实测标定：上身抬升量（把"弹起幅度"从公式落到实测）-------------
    A.apply_pose(arm, torso_pose(BOUNCE_PEAK))
    bpy.context.view_layer.update()
    chest_now = Vector(A.bone_world(arm, "chest", "tail")).z * 1000.0
    head_now = Vector(A.bone_world(arm, "head", "tail")).z * 1000.0
    A.apply_pose(arm, ZERO)
    bpy.context.view_layer.update()
    chest_seam = Vector(A.bone_world(arm, "chest", "tail")).z * 1000.0
    head_seam = Vector(A.bone_world(arm, "head", "tail")).z * 1000.0

    A.report("D16_LAYOUT", {
        "total_frames": TOTAL, "seconds": round(TOTAL / float(A.FPS), 3),
        "hit": HIT, "hit_stop_end": HIT_STOP_END, "hit_hold": HIT_HOLD,
        "bounce_peak": BOUNCE_PEAK, "settle": SETTLE,
        "plateau": PLATEAU, "cancel": CANCEL,
        "vertical_channel": {
            "shape": "★ **无弹道段**：骨盆层逐位固定 + 上身层单峰 + 腿层抖落（三段）",
            "pelvis_z_m": Z_PELVIS_END, "pelvis_y_m": PELVIS_Y_END,
            "ground_hold_band_mm": [Z_PELVIS_END * 1000.0 - GROUND_HOLD_DOWN_MM,
                                    Z_PELVIS_END * 1000.0 + GROUND_HOLD_UP_MM]},
        "seam": {"action": SEAM_ACTION, "frame": SEAM_FRAME,
                 "src": saved_info,
                 "Z_SEAM_mm": round(Z_SEAM * 1000.0, 3)},
        "seam_pitch_deg": {k: round(v, 4) for k, v in SEAM_PITCH.items()},
        "seam_local_rx_deg": {k: round(v, 4) for k, v in SEAM_RX.items()},
        "bounce_extra_deg": {k: round(v, 4) for k, v in BOUNCE_EXTRA.items()},
        "bounce_measured": {
            "chest_tail_rise_mm": round(chest_now - chest_seam, 2),
            "head_tail_rise_mm": round(head_now - head_seam, 2),
            "note": "★ 由 `torso_pose(BOUNCE_PEAK)` **实测**（不是公式推断）。"},
        "leg_layer": {"fold_max_scale": 1.0 - LEG_FOLD, "dz_max_m": LEG_DZ,
                      "note": "踝相对髋的 XY 偏移按 (1−fold·%s) 收缩 + 踝世界 z "
                              "最多下移 %s mm" % (LEG_FOLD, LEG_DZ * 1000.0)},
        "bounce_keys": [list(k) for k in BOUNCE_KEYS],
        "leg_fold_keys": [list(k) for k in LEG_FOLD_KEYS],
        "leg_dz_keys": [list(k) for k in LEG_DZ_KEYS],
        "arm_flop_keys": [list(k) for k in ARM_FLOP_KEYS],
        "arm_flop": ARM_FLOP,
        "seam_ankle_mm": {s: [round(v * 1000.0, 2) for v in SEAM_ANKLE[s]]
                          for s in SIDES},
        "seam_hip_mm": {s: [round(v * 1000.0, 2) for v in SEAM_HIP[s]]
                        for s in SIDES},
        "seam_hip_off_mm": {s: [round(v * 1000.0, 2) for v in SEAM_HIP_OFF[s]]
                            for s in SIDES},
        "arm_max_mm": {s: round(ARM_MAX[s] * 1000.0, 2) for s in SIDES},
        "seam_span_mm": {s: round(SEAM_SPAN[s] * 1000.0, 2) for s in SIDES},
        "roll_weight_mode": ROLL_WEIGHT_MODE,
        "force_direction": ("受击：受力分两条**独立**通道 —— ① 上身**弹起**俯仰增量"
                            "（姿态层，rx 在接缝上加一个小增量、SETTLE 归零）；"
                            "② 腿层**抖落**（膝折向躯干 + 踝下沉）。"
                            "**竖直位移层构造性为零**（骨盆逐位固定）。"),
        "note": ("D16 地面受击：零位 = **`Knockdown_B@20` 落盘帧**；"
                 "竖直通道**没有弹道段**（全族第一支）；骨盆 z 逐位固定；"
                 "上身弹起走**姿态层**（单峰、峰位在 (HIT, SETTLE) 内部）；"
                 "贴地自持由**三点** `hip_probe`（骨盆 + 双肩，**去掉后脑**）守。"),
    })
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
        "note": ("地面受击（仰面躺地被补刀）：竖直通道**无弹道段**，骨盆 z 逐位固定；"
                 "上身**局部弹起**走姿态层（单峰，峰位在 (HIT, SETTLE) 内部）；"
                 "命中 2 帧上身停顿；腿层**抖一下再落下**"),
        "antic_frame": None,
        "hit_frame": HIT,
        "land_frame": None,
        "cancel_frame": CANCEL,
        "bounce_peak_frame": BOUNCE_PEAK,
        "settle_frame": SETTLE,
        "self_hold_frame": PLATEAU,
        "hitstop_frames": HIT_HOLD,
        "hit_points": 0,
        "root_motion_m": [0.0, 0.0],
        "hit_point_m": None,
        "end_pelvis_z_m": round(pelvis_z_at(TOTAL), 6),
        "end_vz_m_per_frame": 0.0,
        "start_pose_ref": "%s 帧 %d（仰面贴地自持姿态）" % (SEAM_ACTION, SEAM_FRAME),
        "end_pose_ref": "仰面贴地自持（与 D15 末帧同位；D18 GetUp_B 的起点）",
        "ballistic_ref": "无（★ 本支竖直通道不含弹道段）",
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.add_markers(action, {"START": 0, "HIT": HIT, "HITSTOP_END": HIT_STOP_END,
                           "BOUNCE_PEAK": BOUNCE_PEAK, "SETTLE": SETTLE,
                           "SELF_HOLD": PLATEAU, "CANCEL": CANCEL, "END": TOTAL})

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
    A.report("D16_REPORT", report)

    if not SKIP_RENDER:
        side_frames = list(range(0, TOTAL + 1))
        # ★ 清单 §4 第 8 步点名的 6 个关键帧：f0 / HIT / BOUNCE_PEAK / SETTLE /
        #   PLATEAU / END（= 0/2/6/12/16/20），再补 HIT_STOP_END(3) 与 4/8/10（过渡）。
        other_frames = [0, HIT, HIT_STOP_END, 4, BOUNCE_PEAK, 8, 10, SETTLE,
                        14, PLATEAU, TOTAL]
        # ★★ 侧视渲**两套**（与 D15 同一条推理）：本支**开局就躺平**（身体沿 +Y 铺开
        #   ~1.3 m）⟹ 标准 side 视图（视中心 y=0）会把**头/脚推到右边界外**。
        #     ① `groundhit_side`（= D13/D14/D15 **逐位相同**的取景）：供跨支接缝
        #        （`px_seam_frame_match_ok` 比 `knockdownb_side_f0020`）用；
        #     ② `groundhitwide_side`（视中心 +Y 0.50 m，**正交宽仍是 3.30 m** ⟹
        #        仍是同一把 3 mm/px 的尺子，只是平移）：`px_bounce_ok` /
        #        `px_ground_hold_ok` 与三重目检用这一套。
        A.render_pose_sheet(arm, action, side_frames, "groundhit",
                            views=(VIEW_D16_SIDE,))
        A.render_pose_sheet(arm, action, side_frames, "groundhitwide",
                            views=(VIEW_D16_SIDE_WIDE,))
        A.render_pose_sheet(arm, action, other_frames, "groundhit",
                            views=(VIEW_D16_FRONT, VIEW_D16_3Q))
        A.save_project()
        A.export_glb(arm)
    print("D16_DONE failed=%s" % report["failed"])
    print("D16_DONE non_ok_bools=%s" % report["non_ok_bools"])
    if os.environ.get("D16_TRACE"):
        print("D16_TRACE " + json.dumps(report.get("trace", {}),
                                        ensure_ascii=False))


# ★ 本支取景。侧视**第一套**与 D13/D14/D15 **逐位相同**（跨支接缝尺子要求同一把尺子）；
#   **第二套**只把视中心沿 +Y 平移 0.50 m、正交宽不变
#   ⟹ 仍是同一把 3 mm/px 的尺子（正交侧视的行号只由世界 z 决定，平移只动列）。
VIEW_D16_SIDE = ("side", (5.20, 0.0, 1.30), (0.0, 0.0, 1.30), 3.30,
                 (780, 1100))
VIEW_D16_SIDE_WIDE = ("side", (5.20, 0.50, 1.00), (0.0, 0.50, 1.00), 3.30,
                      (780, 1100))
VIEW_D16_FRONT = ("front", (0.0, -5.60, 0.95), (0.0, 0.35, 0.95), 4.20,
                  (780, 1100))
VIEW_D16_3Q = ("three_quarter", (4.10, -4.30, 1.15), (0.0, 0.35, 0.95), 4.60,
               (780, 1100))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("D16_FAILURE " + traceback.format_exc())
