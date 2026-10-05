"""anim_ultimate_start —— C12 `Ultimate_Start` 大招起手（C 族最后一支「无命中强 Pose」支）。

目录：`doc/动画制作清单.md` 第 138 行；详细计划见该文件的
「下一支详细制作计划 —— C12 `Ultimate_Start` 大招起手」。

================================================================ 本支的物理构造

三段 + **静止窗** + 收招（**62 帧 / 1.033 s** @60fps）：

    0 ──4── 起手接合（f0 逐位 = `Idle_01@0`，f1..4 全姿接合）
    4 ──16  ① 沉收（anticipation：骨盆 −130 mm、含胸 +16°、沉肩 −26°、双拳前收）
    16 ─19  沉收停顿（逐位冻结 3 帧 —— "启动略慢"的停顿感）
    19 ─38  ② 爆发展开（**19 帧**、6 个键 —— 骨盆回 −50 mm、挺胸、双拳甩到腰侧外张）
    38 ─52  ③ 静止窗（**逐位冻结 15 帧 / 0.25 s** —— 给镜头推进、慢动作、特写用）
    52 ─60  收招（全姿仿射回 `Idle_01@0`，末帧逐位一致）
    60 ─62  静止（4 帧纯静止 ⟹ 末 2 帧步长构造性 = 0）

==================== 第 2 轮返工：`no_teleport` 53.44° → 19.90°（三条并行改动）

第 1 轮 `failed=[]` 但 `non_ok_bools=['no_teleport']`，
`max_frame_step_deg = 53.442 @ [21, "upperarm.R"]`。逐帧追踪 + 世界朝向追踪
**证实是真跳变**（f21/f22 上臂世界朝向单帧转 48.20/46.57°，肘部单帧位移
275.2/283.0 mm = **17 m/s**），不是欧拉参数化伪影 —— 所以不能用"解卷绕"糊过去。

根因与对策（三条都改，缺一不可）：

  1. ★★ **病态反解**：`arm_seat` 里 `cos_sh = (l1²+d²−l23²)/(2·l1·d)`（实测
     `l1=328 mm`、`l23=649.675−328=321.675 mm`，即两段几乎等长 ⟹
     `|l1−l23| = 6 mm`）。当拳距肩 d 很小时 `sin_sh→1`，肘位置
     `elbow = shoulder + (axis·cos_sh + bulge·sin_sh)·l1` 就**几乎只由 `bulge`
     决定**，对 `axis` 的转动不敏感 —— 反过来说，拳路径上一点点方向变化
     都会被放大成上臂的大幅转动。第 1 轮蓄势拳距肩只有 **≈160 mm**
     （649 mm 臂长的 **25%**）⟹ 放大率爆表。
     **对策**：把蓄势拳从"贴胸"前推下移到距肩 **≈270 mm**（40%）。
     重跑实测 `dist.sfR` 全程落在 **270~590 mm**，`uaR` 逐帧步长 ≤19.9°。
  2. ★ **插值器**：逐段 `smoothstep` 在**每个**关键点导数都为 0 ⟹ 速度在每键处
     脉冲，峰值 = 段均值 **1.5×**。换成 **PCHIP（单调三次 Hermite）** 后只在
     局部极值处置零切线，单调段切线连续 ⟹ 峰值 ≈1.0×。
  3. **分帧**：爆发段 13 帧 → **19 帧**（`FLARE_KEYS=(19,23,27,31,35,38)`）。
     拉长 = 直接降速率。同时把 `HAND_KEYS`/`ELBOW_KEYS` 的中间键**对齐**到
     `FLARE_KEYS`（旧版键在 26/29，和分帧错位），并让 `ELBOW_KEYS` 整段只做
     ±1° 微调（旧版在 26/29 让肘额外外扫 12°，是在病态放大之上再加旋转速度）。

**实测**：`max_frame_step_deg 19.901 @ [21, "upperarm.L"]`（余量 5.1°，
比 A10 的 22.817 更宽）、`flare_peak_mmps 2679.7`（门禁 800）、
`nofreeze_peak_step_mm 149.4`、`leg_reach_worst_ratio 0.938`、
`arm_clamp` 最差比 **0.921**（无截断）。

==================== 本支为什么必须**重新设计判据**（计划 §1 的"失败模式"）

本支**几乎零位移**（水平 ≤ 30 mm、无命中、无转体）⟹ C11 那套门禁
（`spin_*` / `foot_pivot_*` / `punch_chain_*` / `punch_frontmost_*` / `root_motion_ok`）
**全部撤下**，而通用项（贴地 / 不滑 / 不跳变）在本支会**全部轻松绿**。

⟹ 危险不是"红"，是"**运动学全绿但什么也没发生**"。所以本支的门禁里立了六条
**反作弊/构图判据**（全部按 `probe_c12_baseline.py` + `probe_c12_pose*.py`
三轮实测**先量后定**，不是拍脑袋）：

  | 判据 | 口径 | 阈值来源 |
  |---|---|---|
  | `anticipation_ok` | 骨盆先沉 ≥40 mm 再回升 ≥10 mm，**或** 胸/肩先内收 ≥15° 再反向张开 ≥15° | 实测：沉 **130** / 回升 **80**；胸 **18.0°** / 肩 **30.0°** —— 两条子句同时成立 |
  | `pose_hold_ok` | 静止窗内**逐帧**骨世界位移 ≤ **2 mm** | 构造性：窗口 15 帧**逐位复用同一姿态** ⟹ 漂移 = **0.0 mm** |
  | `silhouette_strong_ok` | 正视投影**纵横比** ≥ **1.30×** `Idle_01@0`、**填充率** ≥ **0.80×**、双肩展开 ≥ **0.90×**、头在包围盒上沿、重心投影落在支撑面内 | 实测：纵横比 **×1.3136**、填充 **×0.8346**、肩宽 **×0.9552** |
  | `camera_facing_ok` | 躯干偏航 ≤ **20°** 且头偏航 ≤ **20°**（"看着镜头"） | 实测：躯干 **−14.0°**、头 **0.0°** |
  | `no_freeze_ok` | 全支最大单帧骨世界步长 ≥ **3 mm**；静止窗**之外**的累积路径 ≥ **200 mm** | 实测：**149.4 mm** / **1900.3 mm** |
  | `settle_ok` | 末段单帧世界步长**单调收敛**且末 2 帧 ≤ **0.5 mm**，末帧逐位 = 待机 | 实测：末 6 帧 `[130.6, 98.6, 64.2, 22.5, 0.0, 0.0]`；`end_pose_delta = 0.0` |

★ **对计划里两条草案阈值的实测修正**（写进制作日志，供 C13/C14 复用）：
  1. **「填充率 ≥1.3× Idle」不可能达到** —— 强 Pose 把包围盒撑大，填充率**必然下降**。
     实测三族候选全部低于 Idle（0.479 / 0.451 / 0.486 vs 0.593）。
     真正要守的是「**变宽的同时不许变稀**」⟹ 改成 `fill ≥ 0.80× Idle`。
  2. **「肩宽/站高 ≥ 0.34」对本骨架不可能达到** —— 肩宽实测恒定 ≈ **0.301 m**
     （锁骨长度决定，姿态改不动），而站高 1.68~1.94 m ⟹ 该比值天花板 ≈ 0.18。
     实测：Idle 0.1740 / 沉腰族 0.1733 / 挺胸族 0.1684。⟹ 改成
     `shoulder_width ≥ 0.90 × Idle(0.3014 m)`（只防"抱胸缩成一团"）。

==================== 剪影口径（两个独立口径互相印证）

正视投影（相机在 −Y）：横轴 = 世界 X、纵轴 = 世界 Z。
  · 包围盒 / 纵横比 —— 全部**求值后网格**顶点（含 subsurf）的 (x, z) 极值；
  · `fill_grid` —— 三角形**光栅化占用率**（10 mm 网格，有遮挡去重），本支的主口径；
  · `proj_area_m2` —— `Σ|A_xz|` 的无遮挡口径（清单原文的字面口径），只作旁证。
  · **排除**未蒙皮件 `Jacket_Hem` / `Jacket_Hem_Line`（C11 遗留：`parent: null`、
    钉在世界原点）。实测它们的 xy 落在角色包围盒**内部**（`bbox_all == bbox_keep`）
    ⟹ 排除是"把不属于角色的东西剔掉"，不是掩盖。

==================== 复用件（不重写）

  `anim_lib`：全部基础件。
  `anim_grab04`：`leg_seat` / `arm_seat` / `aim_bone_ref`（位置逆解 + 滚转基准）。
  `anim_jump_start`：`_unwrap_xyz` / `_PREV_EULER`（欧拉翻转分支）。
  `anim_run_stop`：`track` / `smooth` / `slerp_dir`。
  `anim_skill03`：`pwl` / `terro_pose` 的写法、`recover_pose` 的**腿分层**、
    `solve_pose` 的**先钉鞋再量鞋底**闭环、`keep_foot`（本支 θ≡0 退化为 Idle 鞋朝向）。
  `probe_c12_baseline`：`_mesh_tris` / `_fill_grid` / `_proj_area_xz` /
    `_centroid_area_weighted` / `_support_box` —— 剪影量（本支另有一份"在 Action 上
    量"的包装，见 `silhouette_of_action`）。

============================== 调试开关（环境变量，无需改文件）

  SKIP_RENDER=1     跳过渲染 + 存盘 + 导出（单轮 ~30 s，迭代期用）
  C12_TRACE=1       逐帧：骨盆 / 双拳 / 双肩 / 鞋底 / 腿可达比
  C12_SIL_DIAG=1    逐帧剪影指标（纵横比 / 填充率 / 包围盒 / 肩宽比）
  C12_HOLD_DIAG=1   静止窗逐帧最大骨世界步长
  C12_SPEED_DIAG=1  逐段世界速度

运行（正式那一轮）：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python anim_ultimate_start.py
"""

import json
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A            # noqa: E402
import anim_idle_01 as I1       # noqa: E402
import anim_grab04 as G4        # noqa: E402
import anim_run_stop as RS      # noqa: E402
import anim_jump_start as JS    # noqa: E402
import probe_c12_baseline as P  # noqa: E402

NAME = "Ultimate_Start"
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"
SIDES = ("L", "R")

POWER_SIDE = "R"        # 蓄势主手（甩到腰侧外张的那只）
GUARD_SIDE = "L"        # 护身手


def _env_i(key, default):
    return int(os.environ.get(key, default))


def _env_f(key, default):
    return float(os.environ.get(key, default))


# ---------------------------------------------------------------- 帧预算
TOTAL = _env_i("C12_TOTAL", 62)                 # 1.033 s @60fps
EASE_END = _env_i("C12_EASE", 4)                # 起手接合
SINK_END = _env_i("C12_SINK", 16)               # ① 沉收到底
SINK_HOLD = _env_i("C12_SINKHOLD", 3)           # 沉收停顿帧数（逐位冻结）
SINK_HOLD_END = SINK_END + SINK_HOLD            # 19
PSHAPE = _env_i("C12_POSE", 38)                 # ② 展开完毕 = 强 Pose 首帧
HOLD_END = _env_i("C12_HOLDEND", 52)            # ③ 静止窗末帧（38..52 = 15 帧）
RECOVER = HOLD_END                              # 收招起点
SETTLE_END = _env_i("C12_SETTLE", 60)           # 收招位移完成帧（此后逐位静止）
CANCEL = _env_i("C12_CANCEL", 56)               # 可取消帧

# ★ 爆发段为什么要 16 帧而不是 10 帧：见 `pwl` 的 PCHIP 说明与文件头「第 2 轮」，
#   实测 `upperarm.R` 世界朝向单帧转 48°、肘部单帧位移 275 mm（= 17 m/s），
#   `no_teleport`（≤25°）红。拉长 = 直接降速率。
FLARE_START = SINK_HOLD_END                     # 19
FLARE_KEYS = (19, 23, 27, 31, 35, PSHAPE)       # 均匀推进 + f35 一个显式过冲键

# ---------------------------------------------------------------- 骨盆高度（mm，相对 Idle 的 830）
# ★ 第 1 轮把 PSHAPE 定在 −95（骨盆 735 mm）是**口径错误**：探针 `build()` 的 drop
#   相对 **rest 0.900**，主脚本 `pz_delta` 相对 **Idle 0.830** —— 同一个数字差 70 mm，
#   于是实测落到探针测量域之外（fill 只有 0.691×）。第 4 轮 `probe_c12_pose3` 对齐口径
#   重扫后，赢家 `d120_f22` ⟹ **pz_delta = −50 mm（骨盆 780 mm）**，实测
#   aspect ×1.336 / fill ×0.825 / 肩宽 ×0.984 —— 三项同时过，且留 3% 余量。
PZ_KEYS = ((0, None), (SINK_END, -130.0), (SINK_HOLD_END, -130.0),
           (23, -118.0), (27, -92.0), (31, -62.0), (35, -42.0),
           (PSHAPE, -50.0), (HOLD_END, -50.0), (TOTAL, None))

# ---------------------------------------------------------------- 躯干通道（度）
# 沉收：含胸 + 沉肩 + 低头；展开：挺胸 + 耸肩 + 抬头。**成对反向** ⟹ 两条 anticipation 子句都成立。
# 强 Pose 侧的数值取自 `probe_c12_pose3` 赢家 `d120_f22` 的实测 spec：
#   pelvis rx 4 / spine −2 / chest −2 / neck −6 / head +6 / shoulder +4。
# 与沉收侧（chest +16 / shoulder −26）反向 ⟹ 胸摆 18°、肩摆 30°，两条子句都过 15°。
PELVIS_RX = ((0, None), (SINK_END, 10.0), (SINK_HOLD_END, 10.0), (23, 8.0),
             (27, 6.0), (31, 4.5), (35, 4.0), (PSHAPE, 4.0),
             (HOLD_END, 4.0), (TOTAL, None))
SPINE_RX = ((0, None), (SINK_END, 6.0), (SINK_HOLD_END, 6.0), (23, 4.0),
            (27, 2.0), (31, -1.0), (35, -2.0), (PSHAPE, -2.0),
            (HOLD_END, -2.0), (TOTAL, None))
CHEST_RX = ((0, None), (SINK_END, 16.0), (SINK_HOLD_END, 16.0), (23, 12.0),
            (27, 6.0), (31, 0.0), (35, -4.0), (PSHAPE, -2.0),
            (HOLD_END, -2.0), (TOTAL, None))
NECK_RX = ((0, None), (SINK_END, -16.0), (SINK_HOLD_END, -16.0), (23, -14.0),
           (27, -10.0), (31, -7.0), (35, -6.0), (PSHAPE, -6.0),
           (HOLD_END, -6.0), (TOTAL, None))
HEAD_RX = ((0, None), (SINK_END, 14.0), (SINK_HOLD_END, 14.0), (23, 12.0),
           (27, 9.0), (31, 7.0), (35, 6.0), (PSHAPE, 6.0),
           (HOLD_END, 6.0), (TOTAL, None))
SHOULDER_RX = ((0, None), (SINK_END, -26.0), (SINK_HOLD_END, -26.0), (23, -20.0),
               (27, -12.0), (31, -6.0), (35, 2.0), (PSHAPE, 4.0),
               (HOLD_END, 4.0), (TOTAL, None))
# 偏航：蓄势微微拧向蓄势侧、**头留在正面** ⟹ `camera_facing_ok`
# 实测口径：躯干 yaw = pelvis + spine_01 + spine_02 + chest = −4−3−3−4 = **−14°**；
#           头 yaw = 躯干 + neck + head = −14+7+7 = **0°**（都 ≤ 20°）。
PELVIS_RY = ((0, 0.0), (SINK_END, -2.0), (SINK_HOLD_END, -2.0), (23, -2.0),
             (27, -3.0), (31, -4.0), (35, -4.0), (PSHAPE, -4.0),
             (HOLD_END, -4.0), (TOTAL, 0.0))
SPINE_RY = ((0, 0.0), (SINK_END, -1.0), (SINK_HOLD_END, -1.0), (23, -1.0),
            (27, -2.0), (31, -3.0), (35, -3.0), (PSHAPE, -3.0),
            (HOLD_END, -3.0), (TOTAL, 0.0))
CHEST_RY = ((0, 0.0), (SINK_END, -1.0), (SINK_HOLD_END, -1.0), (23, -2.0),
            (27, -3.0), (31, -4.0), (35, -4.0), (PSHAPE, -4.0),
            (HOLD_END, -4.0), (TOTAL, 0.0))
NECK_RY = ((0, 0.0), (SINK_END, 2.0), (SINK_HOLD_END, 2.0), (23, 3.0),
           (27, 5.0), (31, 7.0), (35, 7.0), (PSHAPE, 7.0),
           (HOLD_END, 7.0), (TOTAL, 0.0))
HEAD_RY = ((0, 0.0), (SINK_END, 2.0), (SINK_HOLD_END, 2.0), (23, 3.0),
           (27, 5.0), (31, 7.0), (35, 7.0), (PSHAPE, 7.0),
           (HOLD_END, 7.0), (TOTAL, 0.0))

TARGET_BONES = ("pelvis", "spine_01", "spine_02", "chest", "neck", "head",
                "shoulder.L", "shoulder.R")

# ---------------------------------------------------------------- 手：体坐标目标轨道（米）
# 强 Pose 的拳/肘由 `probe_c12_pose3` 赢家 `d120_f22` **实测**给出（不是估的）：
#     拳世界坐标  (±0.3533, −0.0647, 0.7558) m   ← 与位置逆解 `arm_seat` 的口径相同
#     上臂朝向    (±0.4387,  0.2991, −0.8474)    ← 即肘的鼓出方向
# 该构型实测 aspect ×1.336 / fill ×0.825 / 肩宽 ×0.984 —— **三项同时过门禁**。
#
# ★★ 第 2 轮返工（`no_teleport` 红）的两条改动：
#   ① **键位对齐** `FLARE_KEYS=(19,23,27,31,35,38)`。旧版中间键在 26/29，
#      和爆发段的分帧不匹配 ⟹ 速度剖面被切碎。
#   ② **把蓄势（SINK）的拳从"贴胸"拉开**。旧版 R 蓄势拳 (−0.115, −0.215, 1.215)
#      距肩 **≈160 mm**（臂全长 ≈650 mm 的 **25%**）。`arm_seat` 里
#      `cos_sh = (l1²+d²−l23²)/(2·l1·d)`，d 一深折叠 ⟹ `sin_sh→1` ⟹ 肘位置
#      几乎完全由 `bulge` 决定、对 `axis` 转动极不敏感（= 病态反解）：
#      拳路径上一点点方向变化，上臂朝向就会被放大成 **48°/帧**。
#      本版把蓄势拳前推 + 下移到 **≈270 mm**（40%），放大率降到安全区。
#      **判据不变、姿态改** —— 不是为凑绿放宽容差。
HAND_KEYS = {
    "R": {  # 蓄势主手：胸前收拳 → 甩到腰侧外张
        "x": ((0, None), (SINK_END, -0.130), (SINK_HOLD_END, -0.130),
              (23, -0.205), (27, -0.285), (31, -0.335), (35, -0.360),
              (PSHAPE, -0.3533), (HOLD_END, -0.3533), (TOTAL, None)),
        "y": ((0, None), (SINK_END, -0.300), (SINK_HOLD_END, -0.300),
              (23, -0.270), (27, -0.205), (31, -0.140), (35, -0.095),
              (PSHAPE, -0.0647), (HOLD_END, -0.0647), (TOTAL, None)),
        "z": ((0, None), (SINK_END, 1.150), (SINK_HOLD_END, 1.150),
              (23, 1.040), (27, 0.920), (31, 0.830), (35, 0.775),
              (PSHAPE, 0.7558), (HOLD_END, 0.7558), (TOTAL, None)),
    },
    "L": {  # 护手：略高 25 mm、略内 10 mm（层次感，别两手齐平）
        "x": ((0, None), (SINK_END, 0.115), (SINK_HOLD_END, 0.115),
              (23, 0.190), (27, 0.275), (31, 0.325), (35, 0.350),
              (PSHAPE, 0.3433), (HOLD_END, 0.3433), (TOTAL, None)),
        "y": ((0, None), (SINK_END, -0.320), (SINK_HOLD_END, -0.320),
              (23, -0.290), (27, -0.220), (31, -0.150), (35, -0.100),
              (PSHAPE, -0.0747), (HOLD_END, -0.0747), (TOTAL, None)),
        "z": ((0, None), (SINK_END, 1.170), (SINK_HOLD_END, 1.170),
              (23, 1.060), (27, 0.945), (31, 0.850), (35, 0.795),
              (PSHAPE, 0.7808), (HOLD_END, 0.7808), (TOTAL, None)),
    },
}
# 肘的鼓出方向（世界坐标，`arm_seat` 的 `bulge` 口径）：**整段近乎恒定**。
# ★ 旧版在 26/29 让肘向显著外扫（−0.56→−0.60 的 x、0.42→0.50 的 y），
#   那是在**已经被病态放大**的前提下再给肘本身加旋转速度 ⟹ 双倍恶化。
#   本版让肘向只做 ±1° 的微调：拳路径的变化已经足够撑起剪影，肘不需要再动。
ELBOW_KEYS = {
    "R": ((0, None), (SINK_END, (-0.440, 0.320, -0.840)),
          (SINK_HOLD_END, (-0.440, 0.320, -0.840)),
          (23, (-0.445, 0.312, -0.840)), (27, (-0.450, 0.303, -0.843)),
          (31, (-0.447, 0.300, -0.846)), (35, (-0.442, 0.299, -0.847)),
          (PSHAPE, (-0.4387, 0.2991, -0.8474)),
          (HOLD_END, (-0.4387, 0.2991, -0.8474)), (TOTAL, None)),
    "L": ((0, None), (SINK_END, (0.440, 0.320, -0.840)),
          (SINK_HOLD_END, (0.440, 0.320, -0.840)),
          (23, (0.445, 0.312, -0.840)), (27, (0.450, 0.303, -0.843)),
          (31, (0.447, 0.300, -0.846)), (35, (0.442, 0.299, -0.847)),
          (PSHAPE, (0.4387, 0.2991, -0.8474)),
          (HOLD_END, (0.4387, 0.2991, -0.8474)), (TOTAL, None)),
}

# ---------------------------------------------------------------- 门禁阈值
SOLE_RANGE_MM = (-2.0, 6.0)
NO_TELEPORT_MAX_DEG = 25.0
SEAM_TOL = 1e-6
REACH_MAX_RATIO = 0.995
PLANT_MAX_MM = _env_f("C12_PLANT_MAX", 3.0)
HOLD_MAX_MM = _env_f("C12_HOLD_MAX", 2.0)
SIL_ASPECT_MIN = _env_f("C12_SIL_ASPECT", 1.30)
SIL_FILL_MIN = _env_f("C12_SIL_FILL", 0.80)
SIL_SHOULDER_MIN = _env_f("C12_SIL_SHOULDER", 0.90)
SIL_HEAD_TOP_FRAC = _env_f("C12_SIL_HEADTOP", 0.05)
CAMERA_MAX_DEG = _env_f("C12_CAMERA", 20.0)
ANTIC_SINK_MIN_MM = _env_f("C12_ANTIC_SINK", 40.0)
ANTIC_RISE_MIN_MM = _env_f("C12_ANTIC_RISE", 10.0)
ANTIC_TWIST_MIN_DEG = _env_f("C12_ANTIC_TWIST", 15.0)
NOFREEZE_STEP_MIN_MM = _env_f("C12_NOFREEZE_STEP", 3.0)
NOFREEZE_PATH_MIN_MM = _env_f("C12_NOFREEZE_PATH", 200.0)
FLARE_SPEED_MIN_MMPS = _env_f("C12_FLARE_SPEED", 800.0)
PZ_SPAN_MIN_MM = _env_f("C12_PZSPAN_MIN", 40.0)
PZ_SPAN_MAX_MM = _env_f("C12_PZSPAN_MAX", 220.0)
ROOT_H_MAX_MM = _env_f("C12_ROOTH", 30.0)
END_POSE_TOL_MM = _env_f("C12_ENDTOL", 0.5)
ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")
HEM_EXCLUDE = P.HEM_EXCLUDE

# ---------------------------------------------------------------- 观测量
SEAM_POSE = {}
SEAM_EULER = {}
Z_SEAM = 0.0
ANKLE_0 = {}
FOOT0 = {}
IDLE_HAND = {}
IDLE_ELBOW = {}
IDLE_BASIS = {}
IDLE_DIR = {}
IDLE_KNEE_DIR = {}
ARM_LEN = {}
E0 = {}
E_END_UNW = {}
ARM_CLAMP = {}
SIL_BASE = {}
FOOT_BASE_3D = {}


# =============================================================== 轨道求值
def _pchip_endpoint(h0, h1, d0, d1):
    """PCHIP 端点切线（Fritsch–Carlson 端点公式 + 限幅）。"""
    m = ((2.0 * h0 + h1) * d0 - h0 * d1) / (h0 + h1)
    if m * d0 <= 0.0:
        return 0.0
    if d0 * d1 <= 0.0 and abs(m) > abs(3.0 * d0):
        return 3.0 * d0
    return m


def _pchip_slopes(xs, ys):
    """单调三次 Hermite（PCHIP）节点切线：只在**局部极值**处置零。"""
    n = len(xs)
    if n < 2:
        return [0.0] * n
    h = [xs[i + 1] - xs[i] for i in range(n - 1)]
    d = [(ys[i + 1] - ys[i]) / h[i] if h[i] > 1e-12 else 0.0
         for i in range(n - 1)]
    if n == 2:
        return [d[0], d[0]]
    m = [0.0] * n
    for i in range(1, n - 1):
        if d[i - 1] * d[i] <= 0.0:
            m[i] = 0.0
        else:
            w1 = 2.0 * h[i] + h[i - 1]
            w2 = h[i] + 2.0 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
    m[0] = _pchip_endpoint(h[0], h[1], d[0], d[1])
    m[-1] = _pchip_endpoint(h[-1], h[-2], d[-1], d[-2])
    return m


def pwl(keys, f, base=None):
    """**单调三次 Hermite（PCHIP）**取值：关键点逐位精确、段内无过冲。

    ★ 第 2 轮为什么把逐段 `smoothstep` 换掉（本支第 2 号教训）：
      逐段 smoothstep 在**每一个**关键点导数都为 0 ⟹ 速度在**每**键处脉冲式
      加减速，实测峰值达段均值的 **1.5×**；而本支爆发段只有 3~4 帧/键，
      于是 `no_teleport` 的 `upperarm.R` 单帧 **53.44°** 直接由它顶出来。
      PCHIP 只在**局部极值**处置零切线，单调段上切线连续且非零 ⟹
      速度剖面接近匀速，峰值 ≈ 1.0~1.1× 均值。
    """
    if base is not None:
        keys = [(frame, base if value is None else value) for frame, value in keys]
    if f <= keys[0][0]:
        return keys[0][1]
    if f >= keys[-1][0]:
        return keys[-1][1]
    xs = [float(k[0]) for k in keys]
    ys = [float(k[1]) for k in keys]
    m = _pchip_slopes(xs, ys)
    for index in range(len(xs) - 1):
        xa, xb = xs[index], xs[index + 1]
        if xa <= f <= xb:
            h = xb - xa
            if h < 1e-9:
                return ys[index + 1]
            t = (f - xa) / h
            t2 = t * t
            t3 = t2 * t
            return ((2.0 * t3 - 3.0 * t2 + 1.0) * ys[index]
                    + (t3 - 2.0 * t2 + t) * h * m[index]
                    + (-2.0 * t3 + 3.0 * t2) * ys[index + 1]
                    + (t3 - t2) * h * m[index + 1])
    return keys[-1][1]


def pwl_vec(keys, f, base=None):
    return tuple(pwl([(frame, None if value is None else value[i])
                      for frame, value in keys], f,
                     None if base is None else base[i]) for i in range(3))


def pz_delta(f):
    """骨盆相对 Idle 的高度增量（米）。`base` 在两端取 Idle 真值 ±0。"""
    if f <= 0:
        return 0.0
    if f >= TOTAL:
        return 0.0
    return pwl(PZ_KEYS, f, 0.0) / 1000.0


def elbow_dir(side, f):
    return pwl_vec(ELBOW_KEYS[side], f, IDLE_ELBOW[side])


def q_of(frame):
    """收招进度：0 = 静止窗末帧姿态，1 = `Idle_01@0`。

    ★ 第 1 轮的门禁 `settle_no_stop_ok`（末 2 帧 ≤0.5 mm）红了：收招只有 8 帧、
      曲线 `1−(1−u)^1.25` 到不了位，末帧单帧世界步长还有 **41.6 mm** —— 等于
      "收招没停住就断片"。本版把收招拉成 `RECOVER → SETTLE_END`（8 帧）的
      **`smoothstep`（两端速度都为 0）**，并在 `SETTLE_END → TOTAL` 留 **4 帧纯静止**：
      加速度连续（不会"瞬停"），末 2 帧步长构造性地 = 0。
    """
    if frame <= RECOVER:
        return 0.0
    if frame >= SETTLE_END:
        return 1.0
    return RS.smooth((frame - RECOVER) / float(SETTLE_END - RECOVER))


def leg_weight(frame):
    """收招段的**腿分层**权重：0 = 纯 IK（钉地），1 = 纯欧拉仿射（保末帧=Idle）。

    C11 第 3 号教训：欧拉空间线性插值不保持踝高度（误差二阶，两端 0、中点最大），
    所以前段必须用 IK 钉地；但纯 IK 末帧落不回 Idle 逐位值（`leg_seat` 的膝位构造
    与 Idle 的欧拉不是同一支解，本支实测差 shin 28.5°），所以后段必须淡入仿射。
    分层点在 `RECOVER+1`，比姿态混合早一帧起（腿先"松"，避免脚先离地）。
    """
    if frame <= RECOVER + 1:
        return 0.0
    if frame >= SETTLE_END:
        return 1.0
    return RS.smooth((frame - RECOVER - 1) / float(SETTLE_END - RECOVER - 1))


def hand_target(side, f):
    base = IDLE_HAND[side]
    return tuple(pwl(HAND_KEYS[side][axis], f, base[i])
                 for i, axis in enumerate(("x", "y", "z")))


# =============================================================== 姿态装配
def torso_pose(f):
    pose = {}
    for name in TARGET_BONES:
        pose[name] = tuple(SEAM_EULER[name])
    pose["pelvis"] = (pwl(PELVIS_RX, f, SEAM_EULER["pelvis"][0]),
                      pwl(PELVIS_RY, f, SEAM_EULER["pelvis"][1]),
                      SEAM_EULER["pelvis"][2])
    pose["spine_01"] = (pwl(SPINE_RX, f, SEAM_EULER["spine_01"][0]),
                        pwl(SPINE_RY, f, SEAM_EULER["spine_01"][1]), 0.0)
    pose["spine_02"] = (pwl(SPINE_RX, f, SEAM_EULER["spine_02"][0]),
                        pwl(SPINE_RY, f, SEAM_EULER["spine_02"][1]), 0.0)
    pose["chest"] = (pwl(CHEST_RX, f, SEAM_EULER["chest"][0]),
                     pwl(CHEST_RY, f, SEAM_EULER["chest"][1]), 0.0)
    pose["neck"] = (pwl(NECK_RX, f, SEAM_EULER["neck"][0]),
                    pwl(NECK_RY, f, SEAM_EULER["neck"][1]), 0.0)
    pose["head"] = (pwl(HEAD_RX, f, SEAM_EULER["head"][0]),
                    pwl(HEAD_RY, f, SEAM_EULER["head"][1]), 0.0)
    for name in ("shoulder.L", "shoulder.R"):
        pose[name] = (pwl(SHOULDER_RX, f, SEAM_EULER[name][0]),
                      SEAM_EULER[name][1], 0.0)
    # ★ 骨盆局部位移基线：`Z_SEAM + pz_delta − 0.900`（0.900 是 **rest** 骨盆高度，
    #   `Z_SEAM` 是 Idle 的 830 mm）。漏掉基线会让整条曲线比 Idle 高 70 mm
    #   ⟹ 第 1 帧腿被拉直（C11 第 1 轮病根 A）。本支 pz_delta 两端为 0 ⟹ 首末帧逐位 = Idle。
    pose["@loc"] = {"pelvis": A.wloc(0.0, 0.0, Z_SEAM + pz_delta(f) - 0.900)}
    return pose


LEG_BONES = ("thigh.L", "shin.L", "thigh.R", "shin.R")


def build_pose(arm, frame, shift):
    pose = torso_pose(frame)
    A.apply_pose(arm, pose)
    for side in SIDES:
        target = ANKLE_0[side]
        G4.leg_seat(arm, pose, side,
                    (target[0], target[1], target[2] + shift[side]),
                    IDLE_KNEE_DIR[side], ref=None)
    for side in SIDES:
        name = "foot." + side
        pose[name] = JS._unwrap_xyz(JS._PREV_EULER.get(name),
                                    A.keep_world_orientation(arm, name))
    for side in SIDES:
        clamp, dist_mm, limit_mm = G4.arm_seat(
            arm, pose, side, hand_target(side, frame), elbow_dir(side, frame),
            ref=None)
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

    # 起手接合（C10 第 5 号 / C11 复用）：`arm_seat` 隐含"腕直"，而 Idle 戒备是**屈腕**的，
    # 第 1 帧会被掰直 ⟹ 单帧欧拉步长会超标。f1..EASE_END 把臂欧拉从 Idle 平滑接到逆解。
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
    """逐帧贴地闭环：**双脚**鞋底钉到 0 mm（`shift` 并进踝目标，C09 第 6 号）。

    ★ 闭环顺序必须是「**先算 `foot.*`（钉鞋朝向）→ 再量鞋底**」—— C11 第 4 号教训：
      `apply_pose` 会把 `foot.*` 归零，而归零（rest）朝向与钉住的朝向不是一回事，
      漏了这一步闭环会在**错误朝向**上收敛（实测 +6.66 mm 悬空，且表现为"抬"不是"滑"）。
    """
    shift = {side: 0.0 for side in SIDES}
    pose = build_pose(arm, frame, shift)
    if meshes is None:
        return pose
    for _step in range(8):
        low = A.foot_lowest_by_side()
        error = {side: 0.0 - low[side][2] for side in SIDES
                 if low[side] is not None}
        if not error or max(abs(v) for v in error.values()) < 1e-6:
            break
        for side, value in error.items():
            shift[side] += value
        pose = build_pose(arm, frame, shift)
    return pose


def recover_pose(arm, frame, pose_a, pose_b):
    """收招段：躯干/臂走**欧拉仿射**，腿**分层**（前段纯 IK 钉地、后段淡入仿射），
    最后再补一层**根骨竖直贴地补偿**。

    C11 第 3 号教训：欧拉空间线性插值**不保持踝高度**（误差二阶，两端 0、中点最大），
    纯仿射会把鞋压到地面以下；而纯 IK 末帧又落不回 Idle 逐位值。分层是这两难的解。

    ★ 但分层**只把误差压低、没有归零** —— 第 1 轮实测 f51..53 鞋底 −1.90 / −2.61 /
      −2.95 mm（`ground_contact_ok` 容差 −2.0），越接近纯仿射越深。本版在最后
      量一次鞋底，把**穿透量**用根骨（纯平移，不改任何朝向）抬回去；因为 `q==1`
      时不再补偿（末帧就是 Idle 逐位），补偿量在 `q→1` 时已经自然趋近 Idle 自身
      的 −0.96 mm ⟹ 一跳 ≤1 mm，肉眼不可见。
    """
    q = q_of(frame)
    pose = A.blend(pose_a, pose_b, q)
    A.apply_pose(arm, pose)
    weight = leg_weight(frame)
    if weight < 0.999:
        shift = {side: 0.0 for side in SIDES}
        solved = None
        for _step in range(8):
            trial = dict(pose)
            A.apply_pose(arm, trial)
            for side in SIDES:
                target = ANKLE_0[side]
                G4.leg_seat(arm, trial, side,
                            (target[0], target[1], target[2] + shift[side]),
                            IDLE_KNEE_DIR[side], ref=None)
            for side in SIDES:
                name = "foot." + side
                trial[name] = JS._unwrap_xyz(JS._PREV_EULER.get(name),
                                             A.keep_world_orientation(arm, name))
            solved = trial
            low = A.foot_lowest_by_side()
            error = {s: 0.0 - low[s][2] for s in SIDES if low[s] is not None}
            if max(abs(v) for v in error.values()) < 1e-6:
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
        pose[name] = JS._unwrap_xyz(JS._PREV_EULER.get(name),
                                    A.keep_world_orientation(arm, name))
    A.apply_pose(arm, pose)

    # ---- 根骨竖直贴地补偿（纯平移 ⟹ 不改变任何骨的世界朝向）
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
def frame_series(arm, action, total):
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
                     "foot.L", "foot.R"):
            row[name] = tuple(A.bone_world(arm, name, "head"))
        for name in ("hand.L", "hand.R"):
            row[name + "_tail"] = tuple(A.bone_world(arm, name, "tail"))
        for name in ARM_BONES + LEG_BONES:
            row["deg_" + name] = tuple(
                math.degrees(v) for v in arm.pose.bones[name].rotation_euler)
        for name in ("upperarm.L", "upperarm.R", "forearm.L", "forearm.R"):
            row["tail_" + name] = tuple(A.bone_world(arm, name, "tail"))
        low = A.foot_lowest_by_side()
        for side in SIDES:
            row["sole_" + side] = None if low[side] is None else low[side][2]
            row["ankle_" + side] = tuple(A.bone_world(arm, "foot." + side, "head"))
        rows.append(row)
    if previous is not None:
        arm.animation_data.action = previous
    return rows


def world_poses(arm, action, total):
    """逐帧**全探针骨世界坐标**（用于静止窗漂移 / 无冻结 / 收招收敛）。"""
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
            parts = key.split(".")
            bone = parts[0] if len(parts) == 1 or parts[1] != "tail" \
                else parts[0] + "." + parts[1] if len(parts) == 3 else parts[0]
            if key.endswith(".tail"):
                name = key[:-5]
                point[name + ".tail"] = tuple(A.bone_world(arm, name, "tail"))
            else:
                point[key] = tuple(A.bone_world(arm, key, "head"))
            del bone, parts
        frames.append(point)
    if previous is not None:
        arm.animation_data.action = previous
    return frames


def speeds(rows, key):
    out = []
    for index in range(1, len(rows)):
        d = (Vector(rows[index][key]) - Vector(rows[index - 1][key])).length
        out.append(d * A.FPS * 1000.0)
    return out


# =============================================================== 剪影（在 Action 上量）
def silhouette_now(arm):
    """当前的（已在目标帧上求值的）正视剪影指标。"""
    all_pts, keep_pts = P._mesh_verts()
    verts, tris = P._mesh_tris()
    lo, hi = P._bbox(keep_pts)
    width = hi[0] - lo[0]
    height = hi[2] - lo[2]
    fill_grid, filled, nx, nz = P._fill_grid(verts, tris, lo, hi)
    com = P._centroid_area_weighted(verts, tris)
    (slo, shi), zmin = P._support_box()
    shoulder = [A.bone_world(arm, "upperarm." + s, "head").x for s in SIDES]
    head_top = max(p[2] for p in keep_pts)
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
        "head_top_offset_mm": round((hi[2] - head_top) * 1000.0, 2),
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
def ultimate_assertions(arm, action, samples, rows, poses, sil_pose, sil_idle):
    res = {}
    first, last = samples[0], samples[-1]

    # ---- 0) 首帧：逐位 = `Idle_01@0`
    delta0 = 0.0
    for name, value in SEAM_EULER.items():
        got = first["euler"].get(name, (0.0, 0.0, 0.0))
        delta0 = max(delta0, max(abs(a - b) for a, b in zip(got, value)))
    res["us_start_delta_deg"] = round(delta0, 8)
    res["us_start_ok"] = delta0 <= SEAM_TOL

    # ---- 1) 沉收 / 展开：两条子句都量（计划 §2-4 给了 OR，本支两条同时成立）
    pz = [row["pelvis"][2] * 1000.0 for row in rows]
    sink = pz[0] - min(pz[:PSHAPE])
    pz_pose = pz[PSHAPE]
    rise = pz_pose - min(pz[:PSHAPE])
    res["antic_sink_mm"] = round(sink, 2)
    res["antic_rise_mm"] = round(rise, 2)
    chest = [pwl(CHEST_RX, f, SEAM_EULER["chest"][0]) for f in range(TOTAL + 1)]
    sh = [pwl(SHOULDER_RX, f, SEAM_EULER["shoulder.L"][0])
          for f in range(TOTAL + 1)]
    chest_swing = (max(chest[:PSHAPE + 1]) - chest[PSHAPE])
    sh_swing = (sh[PSHAPE] - min(sh[:PSHAPE + 1]))
    res["antic_chest_swing_deg"] = round(chest_swing, 3)
    res["antic_shoulder_swing_deg"] = round(sh_swing, 3)
    clause_sink = sink >= ANTIC_SINK_MIN_MM and rise >= ANTIC_RISE_MIN_MM
    clause_twist = (chest_swing >= ANTIC_TWIST_MIN_DEG
                    and sh_swing >= ANTIC_TWIST_MIN_DEG)
    res["antic_clause_sink_ok"] = bool(clause_sink)
    res["antic_clause_twist_ok"] = bool(clause_twist)
    res["anticipation_ok"] = bool(clause_sink or clause_twist)

    # ---- 2) 静止窗逐位不漂
    worst = 0.0
    worst_at = None
    for frame in range(PSHAPE + 1, HOLD_END + 1):
        for key in poses[frame]:
            step = (Vector(poses[frame][key])
                    - Vector(poses[frame - 1][key])).length * 1000.0
            if step > worst:
                worst = step
                worst_at = [frame, key]
    res["pose_hold_worst_mm"] = round(worst, 6)
    res["pose_hold_worst_at"] = worst_at
    res["pose_hold_frames"] = HOLD_END - PSHAPE + 1
    res["pose_hold_ok"] = worst <= HOLD_MAX_MM

    # ---- 3) 剪影：强 Pose vs `Idle_01@0`
    aspect_ratio = sil_pose["aspect"] / sil_idle["aspect"]
    fill_ratio = sil_pose["fill_grid"] / sil_idle["fill_grid"]
    shoulder_ratio = (sil_pose["shoulder_width_m"]
                      / sil_idle["shoulder_width_m"])
    head_top_ok = (sil_pose["head_top_offset_mm"]
                   <= SIL_HEAD_TOP_FRAC * sil_pose["height_m"] * 1000.0)
    res["sil_idle"] = sil_idle
    res["sil_pose"] = sil_pose
    res["sil_aspect_ratio"] = round(aspect_ratio, 4)
    res["sil_fill_ratio"] = round(fill_ratio, 4)
    res["sil_shoulder_ratio"] = round(shoulder_ratio, 4)
    res["sil_aspect_ok"] = aspect_ratio >= SIL_ASPECT_MIN
    res["sil_fill_ok"] = fill_ratio >= SIL_FILL_MIN
    res["sil_shoulder_ok"] = shoulder_ratio >= SIL_SHOULDER_MIN
    res["sil_head_top_ok"] = bool(head_top_ok)
    res["sil_com_ok"] = sil_pose["com_inside_support"] is True
    res["silhouette_strong_ok"] = bool(
        res["sil_aspect_ok"] and res["sil_fill_ok"] and res["sil_shoulder_ok"]
        and res["sil_head_top_ok"] and res["sil_com_ok"])
    res["sil_aspect_min"] = SIL_ASPECT_MIN
    res["sil_fill_min"] = SIL_FILL_MIN
    res["sil_shoulder_min"] = SIL_SHOULDER_MIN

    # ---- 4) 朝向镜头（躯干 / 头偏航）
    def ry(keys_lists, f):
        return sum(pwl(keys, f, 0.0) for keys in keys_lists)

    torso_yaw = ry((PELVIS_RY, SPINE_RY, SPINE_RY, CHEST_RY), PSHAPE)
    head_yaw = torso_yaw + ry((NECK_RY, HEAD_RY), PSHAPE)
    res["camera_torso_yaw_deg"] = round(torso_yaw, 3)
    res["camera_head_yaw_deg"] = round(head_yaw, 3)
    res["camera_facing_ok"] = (abs(torso_yaw) <= CAMERA_MAX_DEG
                               and abs(head_yaw) <= CAMERA_MAX_DEG)
    res["camera_max_deg"] = CAMERA_MAX_DEG

    # ---- 5) 反作弊：不能"整支等于静止"
    steps = []
    for index in range(1, len(poses)):
        best = 0.0
        for key in poses[index]:
            best = max(best, (Vector(poses[index][key])
                              - Vector(poses[index - 1][key])).length * 1000.0)
        steps.append(best)
    peak_step = max(steps) if steps else 0.0
    path = sum(steps[i] for i in range(len(steps))
               if not (PSHAPE <= i + 1 <= HOLD_END))
    res["nofreeze_peak_step_mm"] = round(peak_step, 3)
    res["nofreeze_path_outside_mm"] = round(path, 1)
    res["nofreeze_step_ok"] = peak_step >= NOFREEZE_STEP_MIN_MM
    res["nofreeze_path_ok"] = path >= NOFREEZE_PATH_MIN_MM
    res["no_freeze_ok"] = bool(res["nofreeze_step_ok"]
                               and res["nofreeze_path_ok"])

    # ---- 6) 展开段的爆发速度（"什么也没发生"的另一面）
    flare = speeds(rows, "hand." + POWER_SIDE + "_tail")
    window = flare[SINK_HOLD_END:PSHAPE]
    res["flare_peak_mmps"] = round(max(window) if window else 0.0, 1)
    res["flare_speed_ok"] = (max(window) if window else 0.0) \
        >= FLARE_SPEED_MIN_MMPS

    # ---- 7) 承重脚不滑（水平）
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
    res["plant_ok"] = max(res["plant_L_mm"], res["plant_R_mm"]) <= PLANT_MAX_MM

    # ---- 8) 骨盆竖直跨度 / 水平位移
    pelvis = [Vector(row["pelvis"]) for row in rows]
    span_h = math.hypot(max(p.x for p in pelvis) - min(p.x for p in pelvis),
                        max(p.y for p in pelvis) - min(p.y for p in pelvis))
    span_z = (max(p.z for p in pelvis) - min(p.z for p in pelvis)) * 1000.0
    res["pz_span_mm"] = round(span_z, 2)
    res["root_span_h_mm"] = round(span_h * 1000.0, 2)
    res["root_motion_ok"] = span_h * 1000.0 <= ROOT_H_MAX_MM
    res["pz_span_ok"] = PZ_SPAN_MIN_MM <= span_z <= PZ_SPAN_MAX_MM

    # ---- 9) 收招：单调收敛 + 末 2 帧不瞬停 + 末帧 = 待机
    tail = [steps[f - 1] for f in range(TOTAL - 5, TOTAL + 1)]
    res["settle_tail_mm"] = [round(v, 3) for v in tail]
    mono = all(tail[i + 1] <= tail[i] + 1e-6 for i in range(len(tail) - 1))
    res["settle_monotone_ok"] = bool(mono)
    res["settle_last2_mm"] = round(max(tail[-2:]), 4)
    res["settle_no_stop_ok"] = res["settle_last2_mm"] <= 0.5
    res["end_pose_delta_mm"] = 0.0
    for key in A.PROBE_KEYS:
        if key in first and key in last:
            res["end_pose_delta_mm"] = max(
                res["end_pose_delta_mm"],
                (Vector(first[key]) - Vector(last[key])).length * 1000.0)
    res["end_pose_delta_mm"] = round(res["end_pose_delta_mm"], 4)
    res["end_pose_ok"] = res["end_pose_delta_mm"] <= END_POSE_TOL_MM
    res["settle_ok"] = bool(res["settle_monotone_ok"]
                            and res["settle_no_stop_ok"]
                            and res["end_pose_ok"])

    # ---- 10) 腿可达比 / 臂逆解不截断
    worst_ratio = 0.0
    worst_at = None
    limit = A.L_THIGH + A.L_SHIN
    for row in rows:
        for side in SIDES:
            hip = Vector(A.bone_world_dummy) if False else None
            del hip
    for index, row in enumerate(rows):
        for side in SIDES:
            ratio = row["reach_" + side] if "reach_" + side in row else None
            del ratio
    worst_ratio, worst_at = _leg_reach(arm, action, rows)
    res["leg_reach_worst_ratio"] = round(worst_ratio, 5)
    res["leg_reach_worst_at"] = worst_at
    res["leg_reach_ok"] = worst_ratio <= REACH_MAX_RATIO
    res["arm_clamp"] = {side: dict(info) for side, info in ARM_CLAMP.items()}
    res["arm_reach_ok"] = all(not info["any"] for info in ARM_CLAMP.values())
    res["leg_len_mm"] = round(limit * 1000.0, 3)
    return res


def _leg_reach(arm, action, rows):
    """全程腿可达比最差（在 Action 上逐帧量髋-踝距离）。"""
    scene = bpy.context.scene
    previous = arm.animation_data.action if arm.animation_data else None
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    limit = A.L_THIGH + A.L_SHIN
    worst = 0.0
    worst_at = None
    for frame in range(TOTAL + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        for side in SIDES:
            hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
            ankle = Vector(A.bone_world(arm, "foot." + side, "head"))
            ratio = (ankle - hip).length / limit
            if ratio > worst:
                worst = ratio
                worst_at = [frame, side]
    if previous is not None:
        arm.animation_data.action = previous
    return worst, worst_at


# =============================================================== 主流程
def main():
    global SEAM_POSE, SEAM_EULER, Z_SEAM, ANKLE_0, FOOT0, IDLE_HAND
    global IDLE_ELBOW, IDLE_BASIS, IDLE_DIR, IDLE_KNEE_DIR, ARM_LEN
    global E0, E_END_UNW, SIL_BASE

    for store in (SEAM_POSE, SEAM_EULER, ANKLE_0, FOOT0, IDLE_HAND, IDLE_ELBOW,
                  IDLE_BASIS, IDLE_DIR, IDLE_KNEE_DIR, ARM_LEN, E0, E_END_UNW,
                  ARM_CLAMP, SIL_BASE):
        store.clear()

    arm, meshes = A.open_animation_project()
    A.setup_scene()
    if I1.NAME not in bpy.data.actions:
        print("C12_BOOTSTRAP 缺 %s，先补跑" % I1.NAME)
        I1.main()
        arm, meshes = A.open_animation_project()
        A.setup_scene()

    for side in SIDES:
        ARM_LEN[side] = {
            "upper": arm.pose.bones["upperarm." + side].length,
            "forearm": arm.pose.bones["forearm." + side].length,
            "hand": arm.pose.bones["hand." + side].length}
    for extra in ("thigh.L", "thigh.R", "shin.L", "shin.R"):
        if extra not in A.PROBE_BONES:
            A.PROBE_BONES = tuple(A.PROBE_BONES) + (extra,)
    A.PROBE_KEYS = A.PROBE_BONES + tuple(n + ".tail" for n in A.PROBE_TAILS)

    # ---- 首帧真值：`Idle_01@0`
    scene = bpy.context.scene
    src = bpy.data.actions[I1.NAME]
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = src
    A._bind_slot(arm, src)
    # ★ 先归零再求值：`Idle_01` 不给 `root` 打通道，而 `.blend` 文件里**存着上次运行
    #   留下的姿态** ⟹ 直接读会读到陈旧值。第 1 轮 `no_teleport` 红在
    #   `max_frame_step_deg = 360.0 at (1, "root")` —— 就是 f0 的 root 是 6.283 rad
    #   （= 360°），f1 被 `reset_pose` 归零，一步 360°。归零后 f0 的 root 也是 0，
    #   这一条构造性地消失；同时也消除了跨运行的隐性不确定。
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
        IDLE_HAND[side] = tuple(A.bone_world(arm, "hand." + side, "tail"))
        shoulder = Vector(A.bone_world(arm, "upperarm." + side, "head"))
        elbow = Vector(A.bone_world(arm, "upperarm." + side, "tail"))
        IDLE_ELBOW[side] = tuple((elbow - shoulder).normalized())
    SIL_BASE = silhouette_now(arm)

    # ---- Idle 骨基座（逆解基准）
    idle = I1.idle_pose(arm, 0.0)
    A.apply_pose(arm, idle)
    bpy.context.view_layer.update()
    for side in SIDES:
        hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
        knee = Vector(A.bone_world(arm, "thigh." + side, "tail"))
        IDLE_KNEE_DIR[side] = (knee - hip).normalized()
        for bone in ("thigh." + side, "shin." + side):
            IDLE_BASIS[bone] = arm.pose.bones[bone].matrix.to_3x3().copy()
            IDLE_DIR[bone] = A.bone_direction(arm, bone)
    for bone in ARM_BONES:
        IDLE_BASIS[bone] = arm.pose.bones[bone].matrix.to_3x3().copy()
        IDLE_DIR[bone] = A.bone_direction(arm, bone)
    for table, source in ((G4.IDLE_BASIS, IDLE_BASIS), (G4.IDLE_DIR, IDLE_DIR),
                          (G4.IDLE_KNEE_DIR, IDLE_KNEE_DIR)):
        table.clear()
        table.update(source)
    G4.ARM_LEN.clear()
    for side in SIDES:
        G4.ARM_LEN[side] = dict(ARM_LEN[side])

    A.report("C12_LAYOUT", {
        "total_frames": TOTAL, "seconds": round(TOTAL / float(A.FPS), 3),
        "ease_end": EASE_END, "sink_end": SINK_END,
        "sink_hold_end": SINK_HOLD_END, "pose": PSHAPE, "hold_end": HOLD_END,
        "recover": RECOVER, "cancel": CANCEL,
        "pelvis_z0_mm": round(Z_SEAM * 1000.0, 3),
        "ankle0_mm": {s: [round(v * 1000.0, 2) for v in ANKLE_0[s]]
                      for s in SIDES},
        "idle_hand_mm": {s: [round(v * 1000.0, 2) for v in IDLE_HAND[s]]
                         for s in SIDES},
        "idle_sil": SIL_BASE,
        "note": ("大招起手：%d 帧沉收（骨盆 −140 mm、含胸 +16°）→ 停顿 %d 帧"
                 "→ %d 帧爆发展开（挺胸 −8°、双拳甩到腰侧外张）"
                 "→ 静止窗 %d 帧（逐位冻结）→ %d 帧收招回待机。"
                 % (SINK_END - EASE_END, SINK_HOLD, PSHAPE - SINK_HOLD_END,
                    HOLD_END - PSHAPE + 1, TOTAL - RECOVER)),
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

    # 静止窗：`PSHAPE` 姿态**逐位复用**到 `HOLD_END`（§0.1「2~4 帧完全停顿」的延长版；
    # 静止窗越长，`pose_hold_ok` 越硬 —— 任何漂移都会被抓出来）
    hold_pose = keyframes[PSHAPE][1]
    for frame in range(PSHAPE + 1, HOLD_END + 1):
        keyframes[frame] = (frame, dict(hold_pose))

    # 收招仿射：把末姿（Idle）解卷绕到离静止窗姿态最近的分支，再逐通道滑过去
    E0.clear()
    E0.update({k: tuple(v) for k, v in hold_pose.items()
               if not k.startswith("@")})
    E_END_UNW.clear()
    for bone, value in SEAM_EULER.items():
        E_END_UNW[bone] = JS._unwrap_xyz(E0.get(bone, (0.0, 0.0, 0.0)), value)
    end_pose = dict(E_END_UNW)
    end_pose["@loc"] = {"pelvis": A.wloc(0.0, 0.0, Z_SEAM - 0.900)}
    A.report("C12_BLEND", {
        "delta_deg": {bone: round(max(abs(a - b) for a, b in
                                      zip(E0[bone], E_END_UNW[bone])), 3)
                      for bone in sorted(E0)},
    })
    for frame in range(RECOVER + 1, TOTAL + 1):
        keyframes.append((frame, recover_pose(arm, frame, hold_pose, end_pose)))

    meta = {
        "anim_id": NAME,
        "loop": False,
        "category": "连招与特殊技",
        "note": ("大招起手：沉收 → 爆发展开成强 Pose → 静止窗 %d 帧 → 收招。"
                 "无命中、无位移（原地起 Pose）。" % (HOLD_END - PSHAPE + 1)),
        "antic_frame": SINK_END,
        "pose_frame": PSHAPE,
        "cancel_frame": CANCEL,
        "hold_frames": HOLD_END - PSHAPE + 1,
        "root_motion_m": [0.0, 0.0],
        "inherit_from": None,
        "segments": {"ease": [0, EASE_END], "sink": [EASE_END, SINK_END],
                     "sink_hold": [SINK_END, SINK_HOLD_END],
                     "flare": [SINK_HOLD_END, PSHAPE],
                     "hold": [PSHAPE, HOLD_END],
                     "recover": [RECOVER, SETTLE_END],
                     "rest": [SETTLE_END, TOTAL]},
        "settle_end": SETTLE_END,
        "silhouette_axis": "正视图（相机 −Y）：横轴 = 世界 X，纵轴 = 世界 Z",
        "hem_excluded": list(HEM_EXCLUDE),
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.add_markers(action, {
        "ENTER": 0, "EASE_END": EASE_END, "ANTIC": SINK_END,
        "ANTIC_HOLD_END": SINK_HOLD_END, "POSE": PSHAPE, "HOLD_END": HOLD_END,
        "CANCEL": CANCEL, "SETTLE": SETTLE_END, "END": TOTAL,
    })

    samples = A.sample_animation(arm, action, 0, TOTAL, meshes)
    rows = frame_series(arm, action, TOTAL)
    poses = world_poses(arm, action, TOTAL)
    sil_idle = silhouette_at(arm, action, 0)
    sil_pose = silhouette_at(arm, action, PSHAPE)

    if os.environ.get("C12_TRACE") == "1":
        for row in rows:
            sf = {}
            for side in SIDES:
                sh = Vector(row["upperarm." + side])
                fi = Vector(row["hand." + side + "_tail"])
                sf["sf" + side] = round((fi - sh).length * 1000.0, 2)
                sf["ua" + side] = round(
                    (Vector(row["tail_upperarm." + side])
                     - Vector(row["upperarm." + side])).length * 1000.0, 2)
            print("C12_TRACE " + json.dumps({
                "f": row["frame"],
                "pelvis": [round(v * 1000.0, 2) for v in row["pelvis"]],
                "fist_R": [round(v * 1000.0, 2) for v in row["hand.R_tail"]],
                "fist_L": [round(v * 1000.0, 2) for v in row["hand.L_tail"]],
                "sole_L": (None if row["sole_L"] is None
                           else round(row["sole_L"] * 1000.0, 2)),
                "sole_R": (None if row["sole_R"] is None
                           else round(row["sole_R"] * 1000.0, 2)),
                "uaR": [round(v, 2) for v in row["deg_upperarm.R"]],
                "uaL": [round(v, 2) for v in row["deg_upperarm.L"]],
                "faR": [round(v, 2) for v in row["deg_forearm.R"]],
                "thL": [round(v, 2) for v in row["deg_thigh.L"]],
                "shR": [round(v, 4) for v in row["upperarm.R"]],
                "elbR": [round(v, 4) for v in row["tail_upperarm.R"]],
                "wrR": [round(v, 4) for v in row["tail_forearm.R"]],
                "elbL": [round(v, 4) for v in row["tail_upperarm.L"]],
                "wrL": [round(v, 4) for v in row["tail_forearm.L"]],
                "shL": [round(v, 4) for v in row["upperarm.L"]],
                "dist": sf,
            }))
    if os.environ.get("C12_SIL_DIAG") == "1":
        for frame in range(0, TOTAL + 1, 2):
            s = silhouette_at(arm, action, frame)
            print("C12_SIL_DIAG " + json.dumps({
                "f": frame, "aspect": s["aspect"], "fill": s["fill_grid"],
                "ar": round(s["aspect"] / sil_idle["aspect"], 4),
                "fr": round(s["fill_grid"] / sil_idle["fill_grid"], 4),
                "w": s["width_m"], "h": s["height_m"]}))
    if os.environ.get("C12_HOLD_DIAG") == "1":
        for frame in range(PSHAPE, HOLD_END + 1):
            best = 0.0
            at = None
            for key in poses[frame]:
                step = (Vector(poses[frame][key])
                        - Vector(poses[frame - 1][key])).length * 1000.0
                if step > best:
                    best, at = step, key
            print("C12_HOLD_DIAG " + json.dumps({"f": frame,
                                                 "step_mm": round(best, 6),
                                                 "at": at}))

    report = A.run_common_assertions(samples, meta, foot_probe=())
    report.update(ultimate_assertions(arm, action, samples, rows, poses,
                                      sil_pose, sil_idle))
    report["low_bad_frames"] = {
        str(s["frame"]): [round(s["low"]["L"] * 1000.0, 2),
                          round(s["low"]["R"] * 1000.0, 2)]
        for s in samples
        if min(s["low"]["L"], s["low"]["R"]) * 1000.0 < -2.0}
    report["meta"] = meta
    report["failed"] = sorted(k for k, v in report.items()
                              if k.endswith("_ok") and v is not True)
    report["non_ok_bools"] = sorted(
        k for k, v in report.items()
        if isinstance(v, bool) and not k.endswith("_ok") and v is not True)
    A.report("C12_REPORT", report)

    if not SKIP_RENDER:
        frames = [0, EASE_END, SINK_END, SINK_HOLD_END, 27, PSHAPE,
                  PSHAPE + 7, HOLD_END, CANCEL, SETTLE_END, TOTAL]
        ratio = 780.0 / 1100.0
        keys = [k for k in samples[0]
                if k != "frame" and isinstance(samples[0][k], tuple)]
        pts = [Vector(s[k]) for s in samples for k in keys if k in s]
        xs = [p.x for p in pts]
        ys = [p.y for p in pts]
        zs = [p.z for p in pts]
        center = (0.5 * (min(xs) + max(xs)), 0.5 * (min(ys) + max(ys)),
                  0.5 * (min(zs) + max(zs)))
        scale = max(2.10, (max(zs) - min(zs)) * 1.15,
                    (max(xs) - min(xs)) * 1.15 / ratio,
                    (max(ys) - min(ys)) * 1.15 / ratio)
        A.report("C12_CAMERA", {
            "center": [round(v, 4) for v in center],
            "ortho_scale": round(scale, 4)})

        def reframe(view):
            name, location, target, _scale, res = view
            direction = (Vector(location) - Vector(target)).normalized()
            new_target = Vector(center)
            new_location = new_target + direction * 4.6
            return (name, tuple(new_location), tuple(new_target), scale, res)

        for base in (A.VIEW_SIDE, A.VIEW_FRONT, A.VIEW_3Q):
            A.render_pose_sheet(arm, action, frames, "ultstart",
                                views=(reframe(base),))
        A.save_project()
        A.export_glb(arm)
    print("C12_DONE failed=%s" % report["failed"])
    print("C12_DONE non_ok_bools=%s" % report["non_ok_bools"])


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("C12_FAILURE " + traceback.format_exc())
