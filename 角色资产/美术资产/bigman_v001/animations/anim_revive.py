"""anim_revive —— E11 `Revive` 复活（E 族第 11 支 / **全项目第 67 支 / 最后一支**）。

清单原文：「从地面撑起 → 半跪 → 站立 → 战斗姿态」。

★★★ 本支是**全链唯一一次首尾闭合**（清单 E11 详细计划 §0）
    · 起点 = `Death`（E10）末姿 **f120 逐位**（仰卧尸僵、双臂摊在身侧、膝未压死）。
      ★ 直接调 `anim_death.death_pose(arm, 120)` 生成 —— 不抄读数、不手调。
    · 终点 = `Idle_01@0` **逐位**（`anim_idle_01.idle_pose(arm, 0.0)`）。
      ★ 链首（A01 待机）与链尾（E11 复活）在此闭合：任意两支可连播。

★★★ 与 D18 `GetUp_B` 的**可分性**（清单 §0 第 3 条 / §1 风险 2）—— 本支最大撞车风险
    D18 也是「仰面起身」。★ 开工探针 `probe_e11_seam.py` **实测**它的读数：
      · D18 min 膝 z = **−38.53 mm**、单膝低（≤150 mm）连续 **22 帧**、时长 40 帧。
    ⟹ **「有膝地停顿」这条分不开它们**（D18 也有），所以本支的可分性判据换成
      **「E11 经过一个 D18 从不经过的姿态」**：把 E11 的**半跪姿**（f74）与 D18 的
      **每一帧**做 57 骨世界矩阵比对，要求**最近的一帧**也差 **≥ 15°**。
      探针实测最近帧 = D18@34，差 **132.5°**（余量 8.8×）——这是可证的分界。

★★★ 时间轴（120 帧 / 2.0 s，沿用 E01 登记的 E 族上界；非循环）
    f0  ──16──▶ **僵直破除**（手指/肘先动 + 胸廓「一口气」；`rvw_rigor_break_ok`）
    f16 ──44──▶ **撑起**（手撑地、躯干离地、髋开始升；躯干 −86° → −26°）
    f44 ──72──▶ **收腿**（双脚回收、右膝落地、骨盆升到半跪高）
    f72 ══76══▶ **半跪停顿**（4 帧完全冻结 —— 与 D18 的分界，`rvw_plateau_ok`）
    f76 ──104─▶ **站起**（蹬腿，力量传导链 脚→腿→髋→腰→肩→手，骨盆 0.418 → 0.830）
    f104 ──120▶ **收势回待机**（逐位收在 `Idle_01@0`）
    ★ 本支**没有「命中帧」**（不是攻击动作）⟹ 无 hitstop 判据，改为**半跪停顿**。

★★★ 腿的驱动方式（继承 E10 的解算器，但**换掉极点来源**）
    腿**不插欧拉**，一律由「世界空间两骨解 `anim_death.leg_solve` + 世界极点」驱动。
    ★ E10 的 `leg_pole(prx)`（骨盆局部 −Y 的世界方向）**本支不用** ——
      它在「髋→踝」带 x 分量时会把极点也带出 x，实测 f56 把**右膝推到 x = +42 mm**
      （跨过身体中线）。本支改用 `_sagittal_pole(hip, tgt)`：⊥「髋→踝」且 **x ≡ 0**。
    它随「脚在髋前 / 髋后」**连续**把膝抬上 / 放下（不是两支二选一），
    所以 `leg_ik` 的小角度假设（在 rx=−86° 处失效）在这里**不适用** ⟹ 仍须 `leg_solve`。
    ★★ **不设膝高目标**（v3「矢状面反解」/ v4「整圈 ⊥ 搜索」两次弯路的结论）：
      **膝高不是输入、是输出** —— 给定髋与踝，膝高只有两个取值（⊥圆上的 ±base），
      中间值只能靠把膝甩到体外 330 mm 去换。半跪 = **把踝放到髋的后下方**，
      膝自己会落下来。要设计膝的轨迹，就做在**踝的路径**上（见 `ANKLE_KEYS` ①②③）。
    ★★ 尾段 `[92, 104]` 把腿**交接到 `Idle_01` 的求解器** `A.leg_ik`（见 `_tail_mix`）：
      不是插角度（v4/v5 两版都栽在这），而是让**输入参数**在 f104 处逐位等于
      Idle 的字面量 ⟹ 解出的 euler 就是 `Idle_01@0` 的 euler，且两骨约束永不破。

★★★ 反向验证旋钮（10 组，每组都必须**真的见红**；驱动脚本 `_rv_e11.sh`）
    E11_TP_SEAM_ZERO=1   ① 首帧改零位              ⟹ `rvw_seam_in_ok`
    E11_TP_ENDZERO=1     ② 末帧改零位              ⟹ `rvw_seam_out_ok`
    E11_TP_NORIGOR=1     ③ 起步窗抹平              ⟹ `rvw_rigor_break_ok`（本支新判据）
    E11_TP_NOKNEEL=1     ④ 抽掉半跪（膝不落地）    ⟹ `rvw_halfkneel_ok`
    E11_TP_NOLIFT=1      ⑤ 骨盆封在低位            ⟹ `rvw_phase_c_rise_ok`
    E11_TP_NOPLATEAU=1   ⑥ 半跪段不冻结            ⟹ `rvw_plateau_ok`
    E11_TP_LIMBJUMP=1    ⑦ 踝目标注入 50 mm 尖峰    ⟹ `rvw_limb_step_ok`
    E11_TP_KNEEPLUNGE=1  ⑧ 极点取反 ⟹ 膝走另一支    ⟹ `rvw_knee_path_ok`
    E11_TP_SINK=1        ⑨ 整体下沉 60 mm          ⟹ `rvw_no_penetration_ok`
    E11_TP_SLIDE=1       ⑩ 站姿段脚横向滑 40 mm    ⟹ `rvw_foot_slide_ok`

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python anim_revive.py
    SKIP_RENDER=1     只跑门禁不渲图（迭代用）
    E11_TRACE=1       逐帧打印骨盆 / 躯干 / 膝踝 / 最低件
"""

import json
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A              # noqa: E402
import anim_idle_01 as IDLE       # noqa: E402
import anim_death as D            # noqa: E402

NAME = "Revive"
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"
SIDES = ("L", "R")
ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")
# 站立段窗口（脚必须踩平、不许滑）
STAND_START = 104
END = 120
START = 0

# =============================================================== 时间轴
RIGOR_END = 16        # 僵直破除末（一口气）
PROP_END = 44         # 撑起末（躯干离地、脚在回收途中）
TUCK_END = 72         # 收腿末 = 半跪达成
HK_END = 76           # 半跪停顿末（[TUCK_END, HK_END] 逐位冻结）
TOTAL = 120

# =============================================================== 阈值
BODY_BAND = (-8.0, 10.0)          # 全程「全身最低件」带（仰卧背/站姿鞋底都落此带内）
PENETRATION_MIN_MM = -8.0         # 沿用 E09/E10
KNEE_RADIUS_MM = 104.7            # 膝网格半径（沿用 E09/E10）
KNEE_PATH_TOL_MM = 4.0
LIMB_STEP_MAX_MM = 60.0           # 沿用 E09/E10
SEAM_POS_MAX_MM = 0.01
SEAM_DIR_MAX_DEG = 0.05
NO_TELEPORT_DEG = 25.0
NO_SNAP_END_DEG = 6.0
# ① 本支新判据：**打破僵直**（与 E10 `dth_zero_motion_ok` 成对，同一探针、期望相反）
RIGOR_WINDOW = (START, RIGOR_END)
RIGOR_MIN_MM = 3.0
# ② 四段相位**各自的幅度判据对**（承 E08 教训：必须成对写，只写上界会把动作写成「几乎不动」）
PHASE_A = (RIGOR_END, PROP_END)     # 撑起
PHASE_A_HEAD_MIN_MM = 120.0
PHASE_A_HEAD_MAX_MM = 900.0
PHASE_A_HIP_MIN_MM = 10.0
PHASE_B = (PROP_END, TUCK_END)      # 收腿
PHASE_B_HIP_MIN_MM = 80.0
PHASE_B_KNEE_DROP_MIN_MM = 60.0     # 右膝相对髋的下降（膝往地上去）
PHASE_C = (HK_END, STAND_START)     # 站起
PHASE_C_HIP_MIN_MM = 350.0
PHASE_C_HEAD_MIN_MM = 550.0
PHASE_D = (STAND_START, END)        # 收势
PHASE_D_HIP_MAX_MM = 25.0
# 半跪判定
HK_FRAME = 74
HK_DOWN_KNEE_MAX_MM = 160.0         # 跪的那侧膝 ≤ 此值
HK_UP_KNEE_MIN_MM = 280.0           # 踏的那侧膝 ≥ 此值
HK_PLATEAU_MAX_DEG = 0.01
# 站立判定
STAND_PELVIS_Z_MM = (820.0, 840.0)
STAND_HEAD_MIN_MM = 1400.0
SOLE_BAND_MM = (-2.0, 6.0)
FOOT_SLIDE_MAX_MM = 3.0
# 可分性
DISTINCT_MIN_DEG = 15.0
# 腿极点：**不设膝高目标**；极点一律取矢状面那一支 `_sagittal_pole(hip, tgt)`（x ≡ 0）。
#   ★ 这是 v3「矢状面反解」与 v4「整圈 ⊥ 搜索」两次弯路之后的**正解**，
#     推导见 `_sagittal_pole` 的长注：**膝高不是输入，是输出**。
#   ★ 不用 E10 的 `D.leg_pole(prx)`：u_x ≠ 0 时它带 x 分量，实测把右膝推到 x = +42 mm。
# 站姿尾段：把腿**交接到 `Idle_01` 的求解器与参数**（见 `_tail_mix`）。
#   ★ 为什么必须交接：本支终点 = `Idle_01@0` **逐位**，而 Idle 的腿是
#     `A.leg_ik`（YZ 平面解 + `ABDUCT_DEG` 外展）算出来的，`leg_solve` 给的是
#     「世界方向 + aim_bone 反解 euler」。二者落点相近、**euler 表示不同**
#     ⟹ 末帧硬覆盖会在 f119→f120 留下 **26.368°** 的 euler 台阶
#     （v3 实测 `no_snap_stop_at = [120, 'shin.R']`，且 `no_teleport` 也红）。
#   ★ 正确做法不是"插角度"，而是**换求解器 + 让输入参数收敛到 Idle 的字面量**
#     （v4 的 6 骨 euler 线性插值 / v5 的「大腿插值 + 小腿 aim」都不满足两骨约束，
#      实测把左踝拉偏 64 mm、左鞋压穿 −65.6）。详见 `_tail_mix` 的长注。
TAIL_MIX_START = 92

# =============================================================== 取景
VIEW_RVW_SIDE = ("side", (4.6, 0.34, 0.66), (0.0, 0.34, 0.66), 2.70,
                 (1100, 700))
VIEW_RVW_FRONT = ("front", (0.0, -5.2, 0.66), (0.0, 0.34, 0.66), 2.70,
                  (1100, 700))
VIEW_RVW_3Q = ("three_quarter", (3.4, -3.2, 1.45), (0.0, 0.34, 0.50), 2.70,
               (1100, 700))


# =============================================================== 反向验证旋钮
def _b(key):
    return os.environ.get(key, "0").strip() not in ("", "0", "false", "False")


SEAM_ZERO = _b("E11_TP_SEAM_ZERO")
END_ZERO = _b("E11_TP_ENDZERO")
NO_RIGOR = _b("E11_TP_NORIGOR")
NO_KNEEL = _b("E11_TP_NOKNEEL")
NO_LIFT = _b("E11_TP_NOLIFT")
NO_PLATEAU = _b("E11_TP_NOPLATEAU")
LIMB_JUMP = _b("E11_TP_LIMBJUMP")
LIMB_JUMP_MM = 50.0
LIMB_JUMP_FRAME = 52
KNEE_PLUNGE = _b("E11_TP_KNEEPLUNGE")
SINK = _b("E11_TP_SINK")
SINK_MM = 60.0
SLIDE = _b("E11_TP_SLIDE")
SLIDE_MM = 40.0
TRACE = _b("E11_TRACE")

# =============================================================== 里程碑表
# 骨盆 (world_y, world_z, rx_deg)：**分段线性**（E10 教训：线性峰速最低，端点不动）
PELVIS_KEYS = (
    (0,   (0.640, 0.141, -86.0)),
    (16,  (0.640, 0.141, -86.0)),
    (30,  (0.596, 0.170, -57.0)),
    (44,  (0.520, 0.218, -26.0)),
    (58,  (0.430, 0.300,   6.0)),
    (72,  (0.318, 0.418,  28.0)),
    (76,  (0.318, 0.418,  28.0)),
    (92,  (0.150, 0.640,  16.0)),
    (104, (0.000, 0.830,   4.0)),
    (120, (0.000, 0.830,   4.0)),
)

# 躯干欧拉（骨 -> ((frame, deg), ...)）
TORSO_KEYS = {
    "spine_01": ((0, 0.0), (16, 0.0), (30, 3.0), (44, 6.0), (58, 8.0),
                 (72, 8.0), (76, 8.0), (92, 5.0), (104, 2.0), (120, 2.0)),
    "spine_02": ((0, 0.0), (16, 0.0), (30, 3.0), (44, 6.0), (58, 8.0),
                 (72, 8.0), (76, 8.0), (92, 5.0), (104, 2.0), (120, 2.0)),
    "chest": ((0, 0.0), (16, 5.0), (30, 7.0), (44, 9.0), (58, 10.0),
              (72, 6.0), (76, 6.0), (92, 3.0), (104, 1.0), (120, 1.0)),
    "neck": ((0, -14.0), (16, -9.0), (30, -2.0), (44, 2.0), (58, 4.0),
             (72, -4.0), (76, -4.0), (92, -5.0), (104, -6.0), (120, -6.0)),
    "head_rx": ((0, -11.0), (16, -4.0), (30, 2.0), (44, 6.0), (58, 7.0),
                (72, 6.0), (76, 6.0), (92, 5.0), (104, 5.0), (120, 5.0)),
    "head_ry": ((0, 22.0), (16, 15.0), (30, 8.0), (44, 2.0), (58, 0.0),
                (72, 0.0), (76, 0.0), (92, 0.0), (104, 0.0), (120, 0.0)),
    "shoulder": ((0, -6.0), (16, -6.0), (30, -10.0), (44, -14.0), (58, -17.0),
                 (72, -20.0), (76, -20.0), (92, -18.0), (104, -18.0),
                 (120, -18.0)),
}

# 踝**世界目标**（米）。用 `REST`/`TERM` 实测值做端点，⟹ 两端天然接缝。
# ★★★ 第三版 —— 本支踝路径的**定稿**（前两版都错，错因写在这里免得后人重犯）：
#   ① 第一版让左踝先荡到 +0.062 再荡回来：白白多出 230 mm 水平位移，
#      还把脚 roll 卡在大角度、左鞋 sole 掉到 −19 mm。**左踝 y 全程几乎不动**
#      （TERM −0.1722 → REST −0.1696，只差 2.6 mm）—— 它是**全程planted 的那只脚**。
#   ② 第二版把右踝一口气荡到 +1.02：髋→踝 被压到 0.33 m、膝被迫鼓 0.40 m，
#      极点一指向后下小腿就扎进地里（f56 膝 z = −112.7 mm）。**最远 +0.47 就够**。
#   ③ 本版最重要的一条：**右踝 y 在 f16~f44 保持 planted（≈ −0.175）**，
#      到 f48 才起摆。理由不是审美，是**几何**：
#      膝高由 `base_z = −u_y/√(u_y²+u_z²)` 决定 —— 右踝一旦提前越过髋的 y，
#      `u_y` 翻号，膝会先冲到 ~545 mm 再砸下来，读成「腿抽了一下」。
#      让它**先坐着屈膝（膝自然抬到 460 mm）、再整条小腿扫到身后**，
#      膝的轨迹才是单调下降的一段弧（`probe_e11_path.py` 全程逐帧实测）。
#   ④ 右踝 z 由 `probe_e11_path.py` **闭环实测鞋底**反解（鞋是跨踝蒙皮的，
#      「鞋底到踝的深度」依赖小腿姿态，离线表会差 30 mm）。
ANKLE_KEYS = {
    "L": ((0, "TERM"), (16, "TERM"),
          (30, (0.190, -0.1710, 0.118)),
          (44, (0.172, -0.1705, 0.112)),
          (58, (0.160, -0.1700, 0.098)),
          (72, (0.152, -0.1698, 0.092)),
          (92, (0.148, -0.1697, 0.088)),
          (104, "REST"), (120, "REST")),
    "R": ((0, "TERM"), (16, "TERM"),
          (24, (-0.200, -0.1750, 0.117)),
          (32, (-0.198, -0.1760, 0.116)),
          (40, (-0.196, -0.1740, 0.118)),
          (48, (-0.192, 0.0200, 0.150)),
          (56, (-0.188, 0.2400, 0.150)),
          (64, (-0.184, 0.3950, 0.140)),
          (72, (-0.180, 0.4550, 0.130)),
          (76, (-0.180, 0.4550, 0.130)),
          (84, (-0.176, 0.3950, 0.130)),
          (92, (-0.170, 0.2900, 0.128)),
          (100, (-0.158, 0.2050, 0.110)),
          (104, "REST"), (120, "REST")),
}

# ★★★ 本支**没有 `KNEE_Z_R`**（第一版有、第二版有、第三版删掉）：
#   那段历史值得留一句 —— 一开始的设计意图是"把右膝压到 110 mm 就是半跪"，
#   于是写了一张「膝世界高度目标表」再用极点去反解。**这条路是死的**：
#   给定髋与踝，膝高只有两个取值（⊥圆上 ±base），想取中间值只能把膝甩到体外
#   （v4 实测外展 330 mm）。半跪**不是**"把膝压到某个高度"，而是
#   **"把踝放到髋的后下方"** —— 膝的高度自己会落下来（`_sagittal_pole`）。

# 脚的世界朝向：俯仰 / 外翻（度）。roll 直接决定鞋底绕踝转多深。
FP_KEYS = ((0, -15.0), (16, -15.0), (30, -10.0), (44, -6.0), (58, -2.0),
           (72, 0.0), (120, 0.0))
ROLL_KEYS = ((0, 45.0), (16, 45.0), (30, 34.0), (44, 20.0), (58, 6.0),
             (72, 0.0), (120, 0.0))
# ★★★ 跪的那一侧（R）的脚俯仰 —— **第三版（定稿）**。前两版都错，错因写在这里。
#
#   第一版（意图版）：`(44,0) (52,14) (60,30) (68,40) (76,44) (92,30) (104,0)`
#     设计意图是「跪侧脚背朝地、脚跟在半跪段抬起来」⟹ 让俯仰一路升到 **+44°**。
#     ★ 实测**恰好相反**：这条曲线把右鞋底压到 **−62.51 mm**（f77），
#       `rvw_body_band_ok` / `rvw_no_penetration_ok` 两条门禁同时红。
#
#   为什么"抬脚跟"会把鞋压进地里（这是本支最反直觉的一处）：
#     **鞋网格是跨 3 根骨蒙皮的 —— `foot` + `toe` + `shin`**（不是只挂 `foot`）。
#     半跪段小腿被折成近水平（f72 膝 z=114.57、踝 z=130.00，`|Δz|` 只有 15 mm），
#     此时 `shin` 权重那一部分顶点**不随 `keep_foot_orient` 转**。俯仰越大，
#     `foot` 权重那部分越是把鞋**绕踝往下拧**，叠加上 `shin` 那部分的固定贡献，
#     鞋底就整体沉下去。`probe_e11_refit.py` 实测：**soleR 对 fp 单调递减**
#     （fp 越大鞋越深），与第一版的意图完全反向。
#
#   第二版（逐帧反解）：`probe_e11_refit.py` 在 f56~f103 逐帧二分出 `soleR=+3.0`
#     的 fp。结论可用，但**不能直接照抄 121 个值**，有两处坑：
#       ① **f73~f76 是测量假象**：`revive_pose` 把半跪停顿 `[72,76]` 冻结到 f72，
#          那 4 帧的 fp **根本不可观测**（改它不影响画面）⟹ 二分只能撞边界
#          （日志里的 `+79.99 @f73~f76` 就是这个假象，不是真解）。
#       ② **f103 是真非单调**（soleR 对 fp 不再是单调函数，日志里撞到 `−89.99`）；
#          但 f103 原始 fp（≈+2.5）本来就把 soleR 放在 **−0.16** ⟹ 无需干预。
#
#   第三版（本表）：把 f56~f102 的反解值**压缩成 4 帧间隔的关键帧**，只改中段。
#     ★ 端点**必须钉死**（否则破接缝）：f0~f16 = **−15.0**（= E10 `Death@120`
#       的 `foot_pitch`，起点逐位）；f104~f120 = **0.0**（= `Idle_01@0` 的脚，
#       终点逐位）。中间从 +22.5 平滑降到 0，**不再冲到 +44**。
#     ★ `probe_e11_fp.py` 实测（`_e11_fp.log`）：
#         · 跪段右鞋底 f56~f102 ∈ **[+2.86, +5.10]**（原来 −62.51）
#         · `body_low_min = −4.80`（= f0 的 `Hair_Mass`，起点接缝自带，E10 已验收）
#         · `body_low_max = +5.37`（= f44 左鞋，未变）
#         · `halfkneel f74 kneeR = 114.57`、`kneeL = 493.72` —— **与改前逐位相同**
#       ⟹ **fp 只转鞋、不动腿**，所以本改动**不可能**牵动膝高 / 肢体台阶 /
#          相位幅度 / 半跪停顿这些已绿的判据（这也是选"只改 fp"而非
#          "抬踝 z"（`E11S_B dz=80`）的原因：后者会把 `kneeR_max` 从 427 顶到 565）。
R_FP_KEYS = ((0, -15.0), (16, -15.0),
             (30, -8.0), (44, 0.0),
             (52, 14.0), (56, 22.5), (60, 21.0), (64, 19.5), (68, 18.0),
             (72, 16.4), (80, 16.4), (88, 16.0), (92, 15.7),
             (96, 13.2), (100, 9.0),
             (104, 0.0), (120, 0.0))

# 臂**世界方向**（骨 -> ((frame, (x,y,z)), ...)）—— 球面插值，不插欧拉
# ★ 第二版：**f0~f24 一律保持 `TERM_DIRS`（摊在地上）不动**。
#   首跑实测：手臂一开始就往「朝下撑」的方向插值，而肩此时还贴在 0.2 m 高，
#   于是 f2 手指就沉到 −13 mm、f16 到 −153 mm。物理上也不对 ——
#   躺在地上的人不会先把手伸到身下，是**先撑住、后抬起**。
IDLE_DIRS = dict(IDLE.ARM_DIRS)
TERM_DIRS = dict(D.TERM_DIRS)
ARM_DIR_KEYS = {
    "upperarm.L": ((0, TERM_DIRS["upperarm.L"]), (24, TERM_DIRS["upperarm.L"]),
                   (40, (0.86, 0.06, -0.50)), (58, (0.74, 0.06, -0.67)),
                   (72, (0.40, -0.20, -0.89)), (92, (0.28, -0.36, -0.89)),
                   (104, IDLE_DIRS["upperarm.L"]),
                   (120, IDLE_DIRS["upperarm.L"])),
    "forearm.L": ((0, TERM_DIRS["forearm.L"]), (24, TERM_DIRS["forearm.L"]),
                  (40, (0.56, 0.10, -0.82)), (58, (0.42, 0.02, -0.91)),
                  (72, (0.24, -0.36, -0.90)), (92, (0.20, -0.34, -0.92)),
                  (104, IDLE_DIRS["forearm.L"]),
                  (120, IDLE_DIRS["forearm.L"])),
    "hand.L": ((0, TERM_DIRS["hand.L"]), (24, TERM_DIRS["hand.L"]),
               (40, (0.60, 0.06, -0.80)), (58, (0.44, 0.02, -0.90)),
               (72, (0.20, -0.40, -0.89)), (92, (0.16, -0.42, -0.89)),
               (104, IDLE_DIRS["hand.L"]), (120, IDLE_DIRS["hand.L"])),
    "upperarm.R": ((0, TERM_DIRS["upperarm.R"]), (24, TERM_DIRS["upperarm.R"]),
                   (40, (-0.86, 0.06, -0.50)), (58, (-0.74, 0.06, -0.67)),
                   (72, (-0.40, -0.20, -0.89)), (92, (-0.28, -0.36, -0.89)),
                   (104, IDLE_DIRS["upperarm.R"]),
                   (120, IDLE_DIRS["upperarm.R"])),
    "forearm.R": ((0, TERM_DIRS["forearm.R"]), (24, TERM_DIRS["forearm.R"]),
                  (40, (-0.56, 0.10, -0.82)), (58, (-0.42, 0.02, -0.91)),
                  (72, (-0.24, -0.36, -0.90)), (92, (-0.20, -0.34, -0.92)),
                  (104, IDLE_DIRS["forearm.R"]),
                  (120, IDLE_DIRS["forearm.R"])),
    "hand.R": ((0, TERM_DIRS["hand.R"]), (24, TERM_DIRS["hand.R"]),
               (40, (-0.60, 0.06, -0.80)), (58, (-0.44, 0.02, -0.90)),
               (72, (-0.20, -0.40, -0.89)), (92, (-0.16, -0.42, -0.89)),
               (104, IDLE_DIRS["hand.R"]), (120, IDLE_DIRS["hand.R"])),
}

# =============================================================== 模块级状态
BASE = {}          # Idle_01@0
TERM = {}          # Death@120
START_POSE = {}    # Death@120（起点逐位）
END_POSE = {}      # Idle_01@0（终点逐位）
BONE_LIST = []
ANKLE_REST = {}
ANKLE_TERM = {}
L1 = 0.410019
L2 = 0.412005
TGT = {}
_PREV = {}


# =============================================================== 求值工具
def _clamp01(x):
    return 0.0 if x <= 0.0 else (1.0 if x >= 1.0 else x)


def _lerp_value(v0, v1, t):
    """标量 / 元组都要能插（`PELVIS_KEYS` 的值是三元组）。"""
    if isinstance(v0, (int, float)) and isinstance(v1, (int, float)):
        return v0 + (v1 - v0) * t
    return tuple(a + (b - a) * t for a, b in zip(v0, v1))


def _pwl(keys, frame):
    """分段**线性**求值（端点逐位返回；元组值逐分量插）。"""
    if frame <= keys[0][0]:
        return keys[0][1]
    if frame >= keys[-1][0]:
        return keys[-1][1]
    for index in range(len(keys) - 1):
        f0, v0 = keys[index]
        f1, v1 = keys[index + 1]
        if f0 <= frame <= f1:
            if f1 == f0:
                return v1
            t = (frame - f0) / float(f1 - f0)
            return _lerp_value(v0, v1, t)
    return keys[-1][1]


def _vec_keys_at(keys, frame):
    """方向关键帧（(f, (x,y,z))）的**球面**求值。"""
    pts = []
    for f, v in keys:
        vec = Vector(v)
        if vec.length < 1e-9:
            vec = Vector((0.0, 0.0, -1.0))
        pts.append((float(f), vec.normalized()))
    if frame <= pts[0][0]:
        return pts[0][1]
    if frame >= pts[-1][0]:
        return pts[-1][1]
    for index in range(len(pts) - 1):
        f0, a = pts[index]
        f1, b = pts[index + 1]
        if f0 <= frame <= f1:
            span = f1 - f0
            if span < 1e-9:
                return b
            t = _clamp01((frame - f0) / span)
            dot = max(-1.0, min(1.0, a.dot(b)))
            if dot > 0.999999:
                return a
            if t <= 0.0:
                return a
            if t >= 1.0:
                return b
            return a.slerp(b, t)
    return pts[-1][1]


def _ankle_target(frame, side):
    keys = ANKLE_KEYS[side]
    if frame <= keys[0][0]:
        return Vector(_resolve_ankle(keys[0][1], side))
    if frame >= keys[-1][0]:
        return Vector(_resolve_ankle(keys[-1][1], side))
    for index in range(len(keys) - 1):
        f0, v0 = keys[index]
        f1, v1 = keys[index + 1]
        if f0 <= frame <= f1:
            a0 = _resolve_ankle(v0, side)
            a1 = _resolve_ankle(v1, side)
            if f1 == f0:
                return Vector(a1)
            t = _clamp01((frame - f0) / float(f1 - f0))
            out = Vector(a0) + (Vector(a1) - Vector(a0)) * t
            if LIMB_JUMP and frame == LIMB_JUMP_FRAME:
                out.y += LIMB_JUMP_MM / 1000.0
            return out
    return Vector(_resolve_ankle(keys[-1][1], side))


def _resolve_ankle(token, side):
    if token == "REST":
        return tuple(ANKLE_REST[side])
    if token == "TERM":
        return tuple(ANKLE_TERM[side])
    return tuple(token)


def _sagittal_pole(hip, tgt):
    """腿的世界极点 —— ⊥「髋→踝」、且 x ≡ 0 的单位向量（下称 `base`）。退化时回落世界 +Z。

    ★★★ 为什么本支最终**不控制膝高**（v3「矢状面反解」/ v4「整圈搜索」两次弯路的结论）

      给定髋与踝，`leg_solve` 里 膝 = 髋 + u·a + n·h（n 是 ⊥「髋→踝」的单位极点）。
      ⊥ 圆上 n 有无穷多个，但膝高的**两个极值**出现在 n = ±base
      （base = 矢状面内那一支，`base_z = −u_y/√(u_y²+u_z²)`）；其余方向的 n
      只把膝往**体外侧**推。v4 用整圈搜索去够一个"中间值"的膝高时，代价是
      膝横向外展 **330 mm**（当 `lateral_z ≡ 0` 时膝高对 ψ 的**一阶导为 0**，
      想调 10 mm 膝高要转 86°）⟹ **这条自由度根本不是用来调膝高的**。

      ⟹ 正解是承认：**膝高不是输入，是输出**。要设计膝的轨迹，就得做在
      **踝的路径**上。而 base 恰好**自动**给出物理上唯一的自然解：
        · 脚在髋**前**（u_y<0，仰卧 / 收腿中）⟹ base_z>0 ⟹ 膝往**上**（坐着屈膝）
        · 脚在髋**后**（u_y>0，半跪）      ⟹ base_z<0 ⟹ 膝往**下**（跪下去）
      两者在 u_y=0（脚正落髋下）处**连续**交接 —— 不是"两个分支二选一"。

      v3 之所以四红，正是因为它拿一个**不可达的膝高目标**（200/150/112）
      去逼这个连续解跳到另一支（膝顶到 471 mm），随后目标忽然落进可达区
      ⟹ **单帧翻支 286 mm**（`no_teleport` + `rvw_limb_step_ok`）。

    ★ `base` 与 E10 的 `D.leg_pole(prx)` 只差 2° 量级（**当 u_x = 0 时**投影后
      逐位相同），但 `leg_pole(prx)` **在 u_x ≠ 0 时会带出 x 分量**：
      实测 f56（右踝比右髋外开 98 mm）处 `leg_pole(1.4°)` 的 ⊥ 分量把
      **右膝推到 x = +42 mm** —— 跨过身体中线。`base` 的 x 恒为 0
      ⟹ 膝恒落在「髋—踝」的竖直平面里。
    """
    d = Vector(tgt) - Vector(hip)
    if d.length < 1e-9:
        return Vector((0.0, 0.0, 1.0))
    u = d.normalized()
    s = math.hypot(u.y, u.z)
    if s < 1e-6:
        return Vector((0.0, 0.0, 1.0))       # 连线沿世界 X ⟹ 矢状面退化
    return Vector((0.0, u.z, -u.y)) / s


def _safe_leg_solve(hip, tgt, pole):
    """`D.leg_solve` 的直通封装（**不再有退化守卫**）。

    ★ 历史（v3 的 `|perp| < 0.30` 守卫为什么**必须删**）：
      当时的极点是 `D.leg_pole(prx)`，它可能**几乎与「髋→踝」共线**；
      共线时 `leg_solve` 里的 `n` 由浮点残差归一化而来 ⟹ 膝被甩到侧面。
      于是加了这条守卫：`|perp| < 0.30` 时换「把 u 绕世界 X 转 +90°」的方向。
      **但这个守卫本身不连续** —— 阈值两侧是两个不同极点，跨过阈值时膝会跳
      （`probe_e11_path.py` 实测 f56 跳 **87.29 mm**、f81 跳 **85.86 mm**）。
      这正好是 `rvw_limb_step_ok` / `no_teleport` 变红的真凶之一。

    ★ 现在极点由 `_sagittal_pole(hip, tgt)` 给出，而它**构造上就 ⊥「髋→踝」**
      （`base = (0, u.z, −u.y)/s`，与 u 的点积 ≡ 0）⟹ `|perp| ≡ 1` ⟹ 守卫**永不触发**。
      留着它只是给后人埋一个「阈值两侧不相同」的雷，故删除，直通调用。
      （唯一的例外是反向验证 ⑧ 传进来的取反极点 —— 它同样 ⊥ u，|perp| 仍 ≡ 1。）
    """
    return D.leg_solve(Vector(hip), Vector(tgt), L1, L2, Vector(pole))


# =============================================================== 尾段交接
# 只交接**腿**：躯干 / 骨盆 / 手臂在 f104 处本来就与 `Idle_01@0`
# **逐位相同**（两侧用的是同一组参数与同一支 `aim_bone`），不需要也不该动它 ——
# 动了反而把 `rvw_sole_ground_ok` / `rvw_foot_slide_ok` 的余量吃掉。
TAIL_BONES = ("thigh.L", "shin.L", "thigh.R", "shin.R", "foot.L", "foot.R")
TAIL_SIDES = {"L": -1.0, "R": +1.0}          # Idle 的外展符号（L 用 −，R 用 +）
TAIL_ANKLE_Y = {"L": IDLE.FRONT_ANKLE_Y, "R": IDLE.BACK_ANKLE_Y}
# ★ 外展的**起点值**：`A.leg_ik` 是 **YZ 平面解**（不含 x）。从 `leg_solve+aim_bone`
#   切过来的那一帧，踝的 x 由极点/两骨解给出（跪姿里 R 踝在髋外侧 80 mm）；
#   若外展从 0 起，`leg_ik` 会把踝直接拉回髋的矢状面 ⟹ **单帧踝跳 78~83 mm**，
#   `rvw_limb_step_ok`（≤60）当场红（v6 实测 `limb_step_max=83.27 @f93`）。
#   ⟹ 起点外展由 `probe_e11_abduct.py` **实机反解**（让 f93 的踝 x 接上 f92 的踝 x），
#   再线性收敛到 `Idle` 的 `±ABDUCT_DEG`。
TAIL_ABDUCT_START = {"L": -7.041, "R": +9.132}


def _tail_mix(arm, pose, frame):
    """尾段 `[TAIL_MIX_START, STAND_START]`：把腿**交接到 `Idle_01@0` 的求解器**。

    ★★★ 为什么不是"交接角度"（v4 / v5 两版都栽在这里）

      v4 做法：6 根腿骨 euler **线性插值**（IK 解 ↔ Idle 解）。
        ~`probe_e11_sweep.py` 的 `E11S_A`（把混合关掉）证明纯 IK 解的踝**逐帧精确**
         等于设计目标（f94 ankL=86.63 = tgt 86.63），鞋底 ≥ +1.06；
         而开着混合时 f98 的左踝被拉到 **19.62 mm**（目标 83.88），差 **64 mm**
         ⟹ 左鞋压穿 **−65.64**。
         根因：两个解的世界落点不同，euler 线性插值**不落在任何一条可达路径上**，
         中途的膝/踝位置无处可管。

      v5 做法（把大腿插值 + 小腿按踝目标 `aim_bone`）**仍然错**：
         `aim_bone` 只把小腿**指向**踝目标，落点 = 膝 + L2·d̂ —— 而混合后的大腿
         已经不在 IK 解的膝上，`|踝目标 − 膝| ≠ L2` ⟹ 踝偏出目标，
         实测 f97 左鞋 −67.73、右鞋还要靠 fp 硬压。**两骨约束不是"指方向"能替代的。**

    ★★★ 正解：**交接"求解器 + 参数"，不交接角度**

      尾段直接改用 `Idle_01` 用的那支解算器 `A.leg_ik(hip_y, hip_z, ankle_y,
      ankle_z, tilt_deg)`，并让**输入参数**在 `STAND_START` 处逐位等于 Idle 的
      字面量：`py→IDLE.HIP_Y(0.0)`、`pz→0.900+IDLE.DROP(0.830)`、
      `prx→IDLE.PELVIS_TILT(4.0)`、`ankle_y→FRONT/BACK_ANKLE_Y`、
      `ankle_z→A.Z_ANKLE_REST`、外展 `0→IDLE.ABDUCT_DEG`。
      ⟹ f104 解出的 euler **就是** `Idle_01@0` 的 euler（同一个函数、同一组参数），
         f103→f104 台阶 ≈ 0；而两骨约束由 `leg_ik` 自己保证 ⟹ 踝不脱轨、鞋不穿地。

      ★ 为什么 `py/pz/prx` 不用另做斜坡：`PELVIS_KEYS` 的 (104, 120) 键本来就是
        `(0.000, 0.830, 4.0)` —— 与 Idle 的三个字面量逐位相同（这是本支设计的前提）。
      ★ 脚**不参与**：`keep_foot_orient` 直接钉世界朝向，`fp=roll=0` 时与
        `A.keep_world_orientation` 逐位相同（= Idle 的脚）；`FP/ROLL/R_FP` 三张表
        在 f104 处本来就都是 0。
    """
    if frame >= STAND_START:
        for bone in TAIL_BONES:
            b = END_POSE.get(bone)
            if b is not None:
                pose[bone] = tuple(b)           # 逐位，不留浮点残差
        return
    if frame <= TAIL_MIX_START:
        return
    mix = (frame - TAIL_MIX_START) / float(STAND_START - TAIL_MIX_START)
    py, pz, prx = _pwl(PELVIS_KEYS, frame)
    for side in SIDES:
        tgt = _ankle_target(frame, side)
        # 输入端向 Idle 的字面量收敛（f104 逐位相等）
        ank_y = tgt.y + (TAIL_ANKLE_Y[side] - tgt.y) * mix
        ank_z = tgt.z + (A.Z_ANKLE_REST - tgt.z) * mix
        thigh_rx, bend = A.leg_ik(py, pz, ank_y, ank_z, tilt_deg=prx)
        a0 = TAIL_ABDUCT_START[side]
        a1 = TAIL_SIDES[side] * IDLE.ABDUCT_DEG
        pose["thigh." + side] = (thigh_rx, 0.0, a0 + (a1 - a0) * mix)
        pose["shin." + side] = (bend, 0.0, 0.0)
        A.apply_pose(arm, pose)


# =============================================================== 姿态装配
def revive_pose(arm, frame):  # noqa: C901
    """生成第 `frame` 帧的完整姿态（**逐帧**调用，每帧自洽）。"""
    raw = frame
    # ★ 半跪停顿：`[TUCK_END, HK_END]` 逐位冻结（= 清单 §2 的「4 帧停顿」）
    if not NO_PLATEAU and TUCK_END <= frame <= HK_END:
        frame = TUCK_END
    # ★ 反向验证 ③：起步窗抹平（去掉胸廓「一口气」）
    if NO_RIGOR and frame <= RIGOR_END:
        frame = START

    py, pz, prx = _pwl(PELVIS_KEYS, frame)
    if NO_LIFT and pz > 0.30:
        pz = 0.30
    pose = {}
    pose["pelvis"] = (prx, 0.0, 0.0)

    # ---- 躯干欧拉（分段线性；头带 ry）-------------------------------------
    for bone in ("spine_01", "spine_02", "chest", "neck"):
        pose[bone] = (_pwl(TORSO_KEYS[bone], frame), 0.0, 0.0)
    pose["head"] = (_pwl(TORSO_KEYS["head_rx"], frame),
                    _pwl(TORSO_KEYS["head_ry"], frame), 0.0)
    sh = _pwl(TORSO_KEYS["shoulder"], frame)
    pose["shoulder.L"] = (sh, 0.0, 0.0)
    pose["shoulder.R"] = (sh, 0.0, 0.0)

    pose["@loc"] = {"pelvis": A.wloc(0.0, py, pz - 0.900)}
    if SINK:
        loc = pose["@loc"]["pelvis"]
        pose["@loc"] = {"pelvis": (loc[0], loc[1] - SINK_MM / 1000.0, loc[2])}
    pose["root"] = (0.0, 0.0, 0.0)
    pose.update(A.FIST)

    # ---- 腿：世界空间两骨解 + 世界极点（不插欧拉）------------------------
    #   ★ 两条腿**同一个极点规则** `_sagittal_pole(hip, tgt)`：⊥「髋→踝」、x ≡ 0。
    #     它随「脚在髋前 / 髋后」**连续**地把膝抬上 / 放下（不是分支二选一）。
    #   ★ **不写膝高目标**（v3/v4 两次弯路的结论，见 `_sagittal_pole` 长注）。
    #   ★ 不用 E10 的 `D.leg_pole(prx)`：u_x ≠ 0 时它带出 x 分量，
    #     实测把右膝推到 x = +42 mm（跨中线）；`_sagittal_pole` 的 x 恒为 0。
    A.apply_pose(arm, pose)
    for side in SIDES:
        hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
        tgt = _ankle_target(frame, side)
        if SLIDE and frame >= STAND_START:    # 反向验证 ⑩：站姿段脚横向滑 40 mm
            tgt = tgt + Vector((SLIDE_MM * 0.001, 0.0, 0.0))
        if NO_KNEEL and side == "R":          # 反向验证 ④：右脚不许摆到身后
            tgt = Vector((tgt.x, min(tgt.y, -0.150), tgt.z))
        TGT[(raw, side)] = tgt.copy()
        if KNEE_PLUNGE:                       # 反向验证 ⑧：极点取反 ⟹ 膝走另一支（入地）
            pole = -_sagittal_pole(hip, tgt)
        else:
            pole = _sagittal_pole(hip, tgt)
        du, df, _knee, _clip = _safe_leg_solve(hip, tgt, pole)
        pose["thigh." + side] = A.aim_bone(arm, "thigh." + side, du)
        A.apply_pose(arm, pose)
        pose["shin." + side] = A.aim_bone(arm, "shin." + side, df)
        A.apply_pose(arm, pose)
    # ---- 脚：世界朝向 = rest 绕世界 X 俯仰 + 绕世界 Y 外翻 ----------------
    #   ★ 仰卧时脚外翻（roll 45），站起过程回收；站姿段 pitch/roll = 0
    #     （`keep_foot_orient(0,0)` 与 `A.keep_world_orientation` 逐位相同）
    fp = _pwl(FP_KEYS, frame)
    roll = _pwl(ROLL_KEYS, frame)
    for side in SIDES:
        r_sign = 1.0 if side == "L" else -1.0
        # 跪的那一侧（R）脚要立起来（脚背朝地）：pitch 单独放大
        side_fp = fp if side == "L" else _pwl(R_FP_KEYS, frame)
        pose["foot." + side] = D.keep_foot_orient(
            arm, "foot." + side, side_fp, roll * r_sign)
        pose["toe." + side] = (0.0, 0.0, 0.0)
        A.apply_pose(arm, pose)
    # ---- 臂：世界方向球面插值（不插欧拉）--------------------------------
    for bone in ARM_BONES:
        d = _vec_keys_at(ARM_DIR_KEYS[bone], frame)
        pose[bone] = A.aim_bone(arm, bone, tuple(d))
        A.apply_pose(arm, pose)

    # ---- 尾段：把 IK 腿平滑交接到 `Idle_01@0` 的腿（见 `TAIL_MIX_START`）----
    _tail_mix(arm, pose, frame)

    # ---- 反向验证 ⑩：站姿段脚横向滑 -------------------------------------------------
    #   ★★ 必须放在 `_tail_mix` **之后**（旧版把它写在腿解算之前 —— 那是**假绿**）：
    #      站姿窗 `[104, 120)` 的 `foot.L/R` 是 `_tail_mix` 用 `END_POSE` **整段覆盖**
    #      的（腿被钉死在 `Idle_01@0` 的脚上），且 `toe.L/R` **不在** `TAIL_BONES` 里
    #      ⟹ 写在 `_tail_mix` 之前的任何扰动都会被丢掉。旧版那一块更是**把值原样
    #      赋回去的空操作**（`pose["foot.x"] = (v0, v1, v2)` 三项逐一抄回），
    #      所以旋钮 ⑩ 根本推不动 `toe`，`rvw_foot_slide_ok` 一直是假绿。
    #   ★ 位移载体 = 骨盆的**世界 X** 平移（`A.wloc` 的 local[0] ≡ 世界 X）：
    #      本 rig 的骨骼没有独立平移通道，"脚相对地面滑" 只能用链条上的世界位移表达，
    #      而这正是判据要防的失效模式（着地的脚相对**固定地面**发生位移）。
    #      从 f104 的 0 mm 线性拉到 f120 的 40 mm；`raw == END` 会被接缝特判整体覆盖，
    #      所以实际最大位移 ≈ 37.5 mm（f119）—— 仍远超 3 mm 阈值。
    #   ★ 只平移不旋转 ⟹ `no_teleport`（量 euler）不受影响 ⟹ 本旋钮**只**让
    #      `rvw_foot_slide_ok` 见红，是**特异**守卫，不误伤其它判据。
    if SLIDE and STAND_START <= raw < END:
        t = (raw - STAND_START) / float(END - STAND_START)
        loc = dict(pose.get("@loc", {}))
        base = loc.get("pelvis", (0.0, 0.0, 0.0))
        loc["pelvis"] = (base[0] + SLIDE_MM / 1000.0 * t, base[1], base[2])
        pose["@loc"] = loc
        A.apply_pose(arm, pose)

    # ---- 两端逐位特判（接缝）--------------------------------------------
    # ★ 反向验证 ① ② 的口径是「把该端**改成零位**」，**不是「不覆盖」**：
    #   本支经 `_tail_mix` 之后 f120 的**自然输出已经逐位等于** `Idle_01@0`
    #   （腿走 `Idle.leg_ik`、躯干/骨盆/臂本来就是同一组参数）
    #   ⟹ "不覆盖"这个动作**不可观测**，守卫会假绿。必须**主动写坏**。
    if raw == START and SEAM_ZERO:
        pose = {"root": (0.0, 0.0, 0.0)}
    elif raw == START:
        pose = dict(START_POSE)
        pose["@loc"] = dict(START_POSE.get("@loc", {}))
    if raw == END and END_ZERO:
        pose = {"root": (0.0, 0.0, 0.0)}
    elif raw == END:
        pose = dict(END_POSE)
        pose["@loc"] = dict(END_POSE.get("@loc", {}))
    if raw in (START, END):
        A.apply_pose(arm, pose)

    if TRACE:
        A.apply_pose(arm, pose)
        lows = D.body_low_profile()
        ank = {x: A.bone_world(arm, "foot." + x).z * 1000.0 for x in SIDES}
        knee = {x: A.bone_world(arm, "shin." + x).z * 1000.0 for x in SIDES}
        print("E11_TRACE f=%3d py=%+.3f pz=%.3f rx=%+5.1f kneeL=%.1f "
              "kneeR=%.1f ankL=%.1f ankR=%.1f low=%.2f(%s) head=%.1f"
              % (raw, py, pz, prx, knee["L"], knee["R"], ank["L"], ank["R"],
                 min(lows.values()),
                 min(lows.items(), key=lambda kv: kv[1])[0],
                 A.bone_world(arm, "head").z * 1000.0))
    return pose


# =============================================================== 工具
def world_mats(arm, action, frame):
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()
    return {name: (arm.matrix_world @ arm.pose.bones[name].matrix).copy()
            for name in BONE_LIST if name in arm.pose.bones}


def _mat_delta(a, b):
    pos = (a.translation - b.translation).length * 1000.0
    dirs = []
    for index in range(3):
        va = a.to_3x3().col[index]
        vb = b.to_3x3().col[index]
        cos = max(-1.0, min(1.0, va.normalized().dot(vb.normalized())))
        dirs.append(math.degrees(math.acos(cos)))
    return pos, max(dirs)


def _worst_delta(mats_a, mats_b):
    wp, wd, wb = 0.0, 0.0, None
    for name in mats_a:
        if name not in mats_b:
            continue
        pos, deg = _mat_delta(mats_a[name], mats_b[name])
        if deg > wd:
            wd, wb = deg, name
        wp = max(wp, pos)
    return wp, wd, wb


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


def _sole_low_mm():
    """按**鞋对象**分左右测脚底最低点（沿用 anim_lib 的口径）。"""
    out = {}
    for side, names in A.FOOT_MESHES.items():
        objs = [bpy.data.objects[n] for n in names if n in bpy.data.objects]
        low = A.lowest_point_of(objs)
        out[side] = None if low is None else low[2] * 1000.0
    return out


# =============================================================== 专属门禁
def rvw_assertions(arm, action, samples, meshes):  # noqa: C901
    res = {}
    scene = bpy.context.scene
    idx = {s["frame"]: s for s in samples}

    # ★ `PROBE_BONES` 里**没有** thigh/shin ⟹ 膝高必须单独实测量。
    #   一次性建表（逐帧 scene.frame_set），后面所有涉及膝/踝的判据都用它。
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    limb_tab = {}
    for frame in range(START, END + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        entry = {}
        for side in SIDES:
            entry["knee." + side] = Vector(A.bone_world(arm, "shin." + side,
                                                        "head"))
            entry["foot." + side] = Vector(A.bone_world(arm, "foot." + side,
                                                        "head"))
        limb_tab[frame] = entry

    def z_of(bone, frame):
        return Vector(idx[frame][bone]).z * 1000.0

    def knee_z(side, frame):
        return limb_tab[frame]["knee." + side].z * 1000.0

    def pel_z(frame):
        return Vector(idx[frame]["pelvis"]).z * 1000.0

    # ---- ① ★ 打破僵直（本支新判据；与 E10 `dth_zero_motion_ok` 成对）------
    stern = [z_of("neck", f) for f in range(RIGOR_WINDOW[0],
                                           RIGOR_WINDOW[1] + 1)]
    amp = max(stern) - min(stern)
    res["rvw_rigor_sternum_mm"] = round(amp, 4)
    res["rvw_rigor_break_ok"] = bool(amp >= RIGOR_MIN_MM)
    res["rvw_rigor_note"] = (
        "★★★ **本支新判据**（清单 E11 §1 风险 3）：「复活」与「尸体」的差别**就是**"
        "「僵直被打破」。载体 = 与 E10 `dth_zero_motion_ok` **完全同一根探针**"
        "（胸骨顶 `neck` = chest.tail 世界 z），窗口 = 起步窗 `[%d, %d]`。"
        "E10 在尸僵窗实测 **0.0000 mm**；本支同探针实测 **%.4f mm**（判据 ≥ %.1f mm）。"
        "★ 守卫 = `E11_TP_NORIGOR=1`（把起步窗抹平）⟹ 必须见红。"
        % (RIGOR_WINDOW[0], RIGOR_WINDOW[1], amp, RIGOR_MIN_MM))

    # ---- ② 四段相位**各自的幅度判据对** ----------------------------------
    a_head = z_of("head", PHASE_A[1]) - z_of("head", PHASE_A[0])
    a_hip = pel_z(PHASE_A[1]) - pel_z(PHASE_A[0])
    res["rvw_phase_a_head_mm"] = round(a_head, 2)
    res["rvw_phase_a_hip_mm"] = round(a_hip, 2)
    res["rvw_phase_a_ok"] = bool(
        PHASE_A_HEAD_MIN_MM <= a_head <= PHASE_A_HEAD_MAX_MM
        and a_hip >= PHASE_A_HIP_MIN_MM)
    res["rvw_phase_a_note"] = (
        "★ 撑起段 `[%d, %d]`：头世界 z 必须上升 **%.0f ~ %.0f mm**（上界防「一次跳到"
        "站姿」），骨盆 z ≥ %.0f mm（下界防「只抬手不抬身」）。实测头 %.2f / 髋 %.2f。"
        % (PHASE_A[0], PHASE_A[1], PHASE_A_HEAD_MIN_MM, PHASE_A_HEAD_MAX_MM,
           PHASE_A_HIP_MIN_MM, a_head, a_hip))

    b_hip = pel_z(PHASE_B[1]) - pel_z(PHASE_B[0])
    b_drop = (knee_z("R", PHASE_B[0]) - pel_z(PHASE_B[0])) \
        - (knee_z("R", PHASE_B[1]) - pel_z(PHASE_B[1]))
    res["rvw_phase_b_hip_mm"] = round(b_hip, 2)
    res["rvw_phase_b_knee_drop_mm"] = round(b_drop, 2)
    res["rvw_phase_b_ok"] = bool(b_hip >= PHASE_B_HIP_MIN_MM
                                 and b_drop >= PHASE_B_KNEE_DROP_MIN_MM)
    res["rvw_phase_b_note"] = (
        "★ 收腿段 `[%d, %d]`：骨盆 z 上升 ≥ %.0f mm **且** 右膝**相对髋**下降"
        " ≥ %.0f mm（膝往地上去，这才是「跪下去」而不是「躺平被抬起来」）。"
        "实测髋 +%.2f / 膝相对髋降 %.2f。守卫 = `E11_TP_NOKNEEL=1`。"
        % (PHASE_B[0], PHASE_B[1], PHASE_B_HIP_MIN_MM,
           PHASE_B_KNEE_DROP_MIN_MM, b_hip, b_drop))

    c_hip = pel_z(PHASE_C[1]) - pel_z(PHASE_C[0])
    c_head = z_of("head", PHASE_C[1]) - z_of("head", PHASE_C[0])
    res["rvw_phase_c_hip_mm"] = round(c_hip, 2)
    res["rvw_phase_c_head_mm"] = round(c_head, 2)
    res["rvw_phase_c_rise_ok"] = bool(c_hip >= PHASE_C_HIP_MIN_MM
                                      and c_head >= PHASE_C_HEAD_MIN_MM)
    res["rvw_phase_c_note"] = (
        "★ 站起段 `[%d, %d]`：骨盆 z 上升 ≥ %.0f mm、头上升 ≥ %.0f mm。"
        "实测髋 +%.2f / 头 +%.2f。守卫 = `E11_TP_NOLIFT=1`（骨盆封在低位）。"
        % (PHASE_C[0], PHASE_C[1], PHASE_C_HIP_MIN_MM, PHASE_C_HEAD_MIN_MM,
           c_hip, c_head))

    d_hip = abs(pel_z(PHASE_D[1]) - pel_z(PHASE_D[0]))
    res["rvw_phase_d_hip_mm"] = round(d_hip, 2)
    res["rvw_phase_d_settle_ok"] = bool(d_hip <= PHASE_D_HIP_MAX_MM)
    res["rvw_phase_d_note"] = (
        "★ 收势段 `[%d, %d]`：这一段是「站稳后的余势」⟹ 骨盆位移必须**小**"
        "（≤ %.0f mm），否则读成「还在往上跳」。实测 %.2f mm。"
        % (PHASE_D[0], PHASE_D[1], PHASE_D_HIP_MAX_MM, d_hip))

    # ---- ③ 半跪（跪侧膝低 + 踏侧膝高 + 停顿冻结）-------------------------
    kd = min(knee_z("L", HK_FRAME), knee_z("R", HK_FRAME))
    ku = max(knee_z("L", HK_FRAME), knee_z("R", HK_FRAME))
    res["rvw_hk_down_knee_mm"] = round(kd, 2)
    res["rvw_hk_up_knee_mm"] = round(ku, 2)
    res["rvw_hk_gap_mm"] = round(ku - kd, 2)
    res["rvw_halfkneel_ok"] = bool(kd <= HK_DOWN_KNEE_MAX_MM
                                   and ku >= HK_UP_KNEE_MIN_MM)
    res["rvw_halfkneel_note"] = (
        "★★ 清单 §2 的「半跪」：**一膝着地 + 一膝高抬**。载体 = f%d 两侧膝世界 z"
        "（低的那侧 ≤ %.0f mm、高的那侧 ≥ %.0f mm）。实测低 %.2f / 高 %.2f"
        "（差 %.2f）。守卫 = `E11_TP_NOKNEEL=1`（膝不落地）。"
        % (HK_FRAME, HK_DOWN_KNEE_MAX_MM, HK_UP_KNEE_MIN_MM, kd, ku, ku - kd))

    # ---- ④ 半跪停顿（4 帧完全冻结）---------------------------------------
    worst, at = 0.0, None
    for frame in range(TUCK_END + 1, HK_END + 1):
        step, pos = _worst_step(samples, frame - START - 1, frame - START)
        if step > worst:
            worst, at = step, pos
    res["rvw_plateau_worst_deg"] = round(worst, 6)
    res["rvw_plateau_ok"] = bool(worst <= HK_PLATEAU_MAX_DEG)
    res["rvw_plateau_note"] = (
        "★★ 清单 §0 第 3 条要求的**与 D18 的分界**：半跪处给 **4 帧完全停顿**"
        "（窗口 `[%d, %d]` 逐帧姿态漂移 ≤ %.2f°）。实测最差 %.6f°。"
        "守卫 = `E11_TP_NOPLATEAU=1`（不冻结）。"
        % (TUCK_END, HK_END, HK_PLATEAU_MAX_DEG, worst))

    # ---- ⑤ 可分性：E11 的半跪姿 vs D18 **每一帧** ------------------------
    d18 = bpy.data.actions.get("GetUp_B")
    if d18 is None:
        res["rvw_distinct_from_d18_ok"] = None
        res["rvw_distinct_note"] = "★ `GetUp_B` 不在工程里 ⟹ 本判据置空。"
    else:
        hk_mats = world_mats(arm, action, HK_FRAME)
        d_start, d_end = int(d18.frame_range[0]), int(d18.frame_range[1])
        best_frame, best_wd = None, 1e9
        for frame in range(d_start, d_end + 1):
            _p, wd, _b = _worst_delta(hk_mats, world_mats(arm, d18, frame))
            if wd < best_wd:
                best_wd, best_frame = wd, frame
        res["rvw_d18_closest_frame"] = best_frame
        res["rvw_d18_min_max_dir_deg"] = round(best_wd, 3)
        res["rvw_distinct_from_d18_ok"] = bool(best_wd >= DISTINCT_MIN_DEG)
        arm.animation_data.action = action
        A._bind_slot(arm, action)
        res["rvw_distinct_note"] = (
            "★★★ 清单 E11 §0 第 3 条：「与 D18 撞车」是本支**最大风险**。"
            "★ 开工探针实测 D18 也有 **22 帧**低膝段 ⟹「有膝地停顿」这条**分不开**"
            "它们，故改用**姿态分界**：把 E11 的半跪姿（f%d）与 D18 **每一帧**做"
            "57 骨世界矩阵比对，要求**最近那一帧**也差 ≥ %.0f°。实测最近帧 = D18@%s，"
            "差 **%.3f°**（余量 %.1f×）⟹ E11 经过一个 D18 从不经过的姿态。"
            % (HK_FRAME, DISTINCT_MIN_DEG, best_frame, best_wd,
               (best_wd / DISTINCT_MIN_DEG) if DISTINCT_MIN_DEG else 0.0))

    # ---- ⑥ 逐帧「全身最低件」带 + 全程无穿地 -----------------------------
    lows = {s["frame"]: min(s["low"]["L"], s["low"]["R"]) * 1000.0
            for s in samples}
    res["rvw_body_low_min_mm"] = round(min(lows.values()), 2)
    res["rvw_body_low_max_mm"] = round(max(lows.values()), 2)
    res["rvw_body_band_ok"] = bool(
        BODY_BAND[0] <= res["rvw_body_low_min_mm"]
        and res["rvw_body_low_max_mm"] <= BODY_BAND[1])
    res["rvw_no_penetration_ok"] = bool(
        res["rvw_body_low_min_mm"] >= PENETRATION_MIN_MM)
    res["rvw_body_low_note"] = (
        "★ 载体 = **全身最低件**（逐帧、全部网格）。带 [%.0f, %.0f] mm，下限 %.0f。"
        "实测最低 %.2f / 最高 %.2f。★ 为什么不用通用 `ground_contact_ok`（鞋底口径）："
        "本支起点是**仰卧**（支撑面是背/头），鞋底只是其中一件 —— 同 E10 先例"
        "**显式置空 + 换载体**。守卫 = `E11_TP_SINK=1`（整体下沉 %.0f mm）。"
        % (BODY_BAND[0], BODY_BAND[1], PENETRATION_MIN_MM,
           res["rvw_body_low_min_mm"], res["rvw_body_low_max_mm"], SINK_MM))

    # ---- ⑦ 膝不入地 + 无肢体跳变 ----------------------------------------
    knee_min = 1e9
    knee_at = None
    steps, step_at = [], None
    prev = None
    for frame in range(START, END + 1):
        cur = limb_tab[frame]
        kz = min(v.z for k, v in cur.items() if k.startswith("knee")) * 1000.0
        if kz < knee_min:
            knee_min, knee_at = kz, frame
        if prev is not None:
            for key in cur:
                d = (cur[key] - prev[key]).length * 1000.0
                if step_at is None or d > step_at[0]:
                    step_at = (d, frame, key)
                steps.append(d)
        prev = cur
    res["rvw_knee_min_mm"] = round(knee_min, 2)
    res["rvw_knee_min_at"] = knee_at
    res["rvw_knee_path_ok"] = bool(
        knee_min >= KNEE_RADIUS_MM - KNEE_PATH_TOL_MM)
    res["rvw_limb_step_max_mm"] = round(max(steps), 2)
    res["rvw_limb_step_at"] = step_at
    res["rvw_limb_step_ok"] = bool(max(steps) <= LIMB_STEP_MAX_MM)
    res["rvw_limb_note"] = (
        "★ 沿用 E09/E10 容差：膝 z ≥ %.1f − %.1f mm（实测最低 %.2f @f%s）、"
        "膝/踝单帧世界位移 ≤ %.0f mm（实测峰 %.2f @f%s）。"
        "守卫 = `E11_TP_KNEEPLUNGE=1`（极点翻向下）/ `E11_TP_LIMBJUMP=1`（踝尖峰）。"
        % (KNEE_RADIUS_MM, KNEE_PATH_TOL_MM, knee_min, knee_at,
           LIMB_STEP_MAX_MM, max(steps),
           step_at[1] if step_at else "?"))

    # ---- ⑧ 站姿段：脚踩平 + 不许滑 ---------------------------------------
    sole_min, sole_max = 1e9, -1e9
    for frame in range(STAND_START, END + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        sole = _sole_low_mm()
        for value in sole.values():
            if value is None:
                continue
            sole_min = min(sole_min, value)
            sole_max = max(sole_max, value)
    res["rvw_sole_ground_min_mm"] = round(sole_min, 2)
    res["rvw_sole_ground_max_mm"] = round(sole_max, 2)
    res["rvw_sole_ground_ok"] = bool(
        SOLE_BAND_MM[0] <= sole_min and sole_max <= SOLE_BAND_MM[1])

    travel = {}
    for probe in ("toe.L", "toe.R"):
        pts = [Vector(s[probe]) for s in samples
               if STAND_START <= s["frame"] <= END]
        travel[probe] = max((p - pts[0]).length for p in pts) * 1000.0
    res["rvw_foot_slide_mm"] = {k: round(v, 3) for k, v in travel.items()}
    res["rvw_foot_slide_ok"] = bool(max(travel.values()) <= FOOT_SLIDE_MAX_MM)
    res["rvw_sole_note"] = (
        "★★ 清单 §1 风险 5：本支**是站姿类终点** ⟹ 通用的「鞋底 −2 ~ +6 mm」"
        "`ground_contact_ok` **本支真的启用**（不像 E10 置空），但只在**站姿窗**"
        " `[%d, %d]` 上量（起点仰卧时鞋底离地是设计意图）。实测鞋底 z ∈ "
        "[%.2f, %.2f]。★ 脚不许滑：窗口内 `toe.L/R` 世界位移 ≤ %.0f mm，实测 %s。"
        "守卫 = `E11_TP_SLIDE=1`。"
        % (STAND_START, END, sole_min, sole_max, FOOT_SLIDE_MAX_MM,
           res["rvw_foot_slide_mm"]))

    # ---- ⑨ 力量传导链（脚→腿→髋→腰→肩→手，每段都要有量）----------------
    def _span(name, tail=False):
        pts = [Vector(s[name + (".tail" if tail else "")]) for s in samples]
        return max((p - pts[0]).length for p in pts) * 1000.0

    knee_deg = 0.0
    for sample in samples:
        for side in SIDES:
            knee_deg = max(knee_deg,
                           abs(sample["euler"].get("shin." + side,
                                                   (0.0, 0.0, 0.0))[0]))
    chain = {
        "foot_mm": round(_span("toe.L", True), 3),
        "knee_deg": round(knee_deg, 3),
        "hip_mm": round(_span("pelvis"), 3),
        "waist_deg": round(max(abs(s["euler"].get("chest", (0, 0, 0))[0])
                               for s in samples)
                           - min(abs(s["euler"].get("chest", (0, 0, 0))[0])
                                 for s in samples), 3),
        "shoulder_mm": round(_span("upperarm.L"), 3),
        "hand_mm": round(_span("hand.L", True), 3),
    }
    res["rvw_chain"] = chain
    res["rvw_chain_ok"] = bool(
        chain["foot_mm"] > 100.0 and chain["knee_deg"] > 5.0
        and chain["hip_mm"] > 300.0 and chain["waist_deg"] > 2.0
        and chain["shoulder_mm"] > 50.0 and chain["hand_mm"] > 300.0)
    res["rvw_chain_note"] = (
        "★ SOUL 硬约束：**脚→腿→髋→腰→肩→手**逐段都要有关键帧量。实测 %s。"
        % json.dumps(chain, ensure_ascii=False))

    # ---- ⑩ 站姿终点 ------------------------------------------------------
    res["rvw_stand_pelvis_mm"] = round(pel_z(END), 2)
    res["rvw_stand_head_mm"] = round(z_of("head", END), 2)
    res["rvw_stand_ok"] = bool(
        STAND_PELVIS_Z_MM[0] <= res["rvw_stand_pelvis_mm"]
        <= STAND_PELVIS_Z_MM[1] and res["rvw_stand_head_mm"] >= STAND_HEAD_MIN_MM)

    res["phase_markers"] = {"START": START, "RIGOR_END": RIGOR_END,
                            "PROP_END": PROP_END, "TUCK_END": TUCK_END,
                            "HK_END": HK_END, "STAND": STAND_START,
                            "END": END}
    return res


# =============================================================== 主流程
def boot():
    arm, meshes = D.boot()
    A.setup_scene()
    global BASE, TERM, START_POSE, END_POSE, BONE_LIST
    global ANKLE_REST, ANKLE_TERM, L1, L2
    L1, L2 = D.L1, D.L2
    BASE = dict(D.BASE)
    TERM = dict(D.TERM)
    ANKLE_REST = {s: D.ANKLE_REST[s].copy() for s in SIDES}
    ANKLE_TERM = {s: D.ANKLE_TERM[s].copy() for s in SIDES}
    BONE_LIST = sorted(arm.pose.bones.keys())

    A.apply_pose(arm, TERM)
    START_POSE = D.death_pose(arm, 120)          # ★ 起点 = Death@120 逐位
    END_POSE = IDLE.idle_pose(arm, 0.0)          # ★ 终点 = Idle_01@0 逐位
    return arm, meshes


def main():  # noqa: C901
    arm, meshes = boot()

    keyframes = [(frame, revive_pose(arm, frame))
                 for frame in range(START, END + 1)]
    meta = {
        "anim_id": NAME,
        "loop": False,
        "category": "状态与战斗流程",
        "note": ("复活：从 Death 末姿（仰卧尸僵）撑起 → 收腿半跪（4 帧停顿）→ "
                 "站起 → 收回 Idle_01@0。★ 全链唯一一次首尾闭合。"),
        "frame_bound_note": "★ 沿用 E01 登记的 E 族上界 120 帧 / 2.0 s",
        "hitstop_frames": "none（非攻击动作 ⟹ 无命中帧；代之以半跪 4 帧停顿）",
        "seam_in": "Death@120（E10 末姿，逐位）",
        "seam_out": "Idle_01@0（A01 站架，逐位）",
        "half_kneel_frame": HK_FRAME,
        "root_motion_m": [0.0, -0.640],
        "distinct_from": "D18 GetUp_B（姿态分界：半跪姿 vs D18 全帧 ≥15°）",
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.add_markers(action, {"START": START, "RIGOR_END": RIGOR_END,
                           "PROP_END": PROP_END, "TUCK_END": TUCK_END,
                           "HK_END": HK_END, "STAND": STAND_START,
                           "END": END})
    A.set_hitstop(action, TUCK_END, HK_END)

    samples = A.sample_animation(arm, action, START, END, meshes)
    report = A.run_common_assertions(samples, meta, foot_probe=(),
                                     slide_tolerance_mm=3.0)
    # ★ 通用 `ground_contact_ok`（**鞋底** −2 ~ +6）在起点仰卧处不适用
    #   ⟹ 同 E10 先例**显式置空 + 换载体**（替代判据 = `rvw_sole_ground_ok` 站姿窗 +
    #   `rvw_body_band_ok` 全程）。**不是删红灯，是换载体。**
    raw_ground = report.pop("ground_contact_ok")
    report["rvw_common_ground_contact_raw"] = raw_ground
    report["rvw_common_ground_contact_note"] = (
        "★ 原读数（鞋底口径 `ground_contact_ok`）= %r，**本支置空**：起点是仰卧"
        "（支撑面 = 背/头）。替代判据 = `rvw_body_band_ok`（全程全身最低件）"
        "+ `rvw_sole_ground_ok`（**仅站姿窗**启用鞋底带）。" % (raw_ground,))
    report.update(rvw_assertions(arm, action, samples, meshes))

    # ---- 接缝入：f0 vs Death@120 ----------------------------------------
    death = bpy.data.actions.get("Death")
    if death is None:
        report["rvw_seam_in_ok"] = None
        report["rvw_seam_in_note"] = "★ `Death` action 不在工程里 ⟹ 置空。"
    else:
        seam = world_mats(arm, death, 120)
        mine = world_mats(arm, action, START)
        wp, wd, wb = _worst_delta(mine, seam)
        report["rvw_seam_in_pos_mm"] = round(wp, 6)
        report["rvw_seam_in_dir_deg"] = round(wd, 6)
        report["rvw_seam_in_at"] = wb
        report["rvw_seam_in_ok"] = bool(wp <= SEAM_POS_MAX_MM
                                       and wd <= SEAM_DIR_MAX_DEG)
        report["rvw_seam_in_note"] = (
            "★★ 清单 §0 第 1 条：起点 = `Death@120` **逐位**（仰卧尸僵）。"
            "实测 pos %.6f mm / dir %.6f°（容差 %.2f mm / %.2f°）。"
            "守卫 = `E11_TP_SEAM_ZERO=1`。"
            % (wp, wd, SEAM_POS_MAX_MM, SEAM_DIR_MAX_DEG))

    # ---- 接缝出：f120 vs Idle_01@0 --------------------------------------
    idle = bpy.data.actions.get("Idle_01")
    if idle is None:
        report["rvw_seam_out_ok"] = None
        report["rvw_seam_out_note"] = "★ `Idle_01` action 不在工程里 ⟹ 置空。"
    else:
        endref = world_mats(arm, idle, 0)
        mine = world_mats(arm, action, END)
        wp, wd, wb = _worst_delta(mine, endref)
        report["rvw_seam_out_pos_mm"] = round(wp, 6)
        report["rvw_seam_out_dir_deg"] = round(wd, 6)
        report["rvw_seam_out_at"] = wb
        report["rvw_seam_out_ok"] = bool(wp <= SEAM_POS_MAX_MM
                                        and wd <= SEAM_DIR_MAX_DEG)
        report["rvw_seam_out_note"] = (
            "★★★ 清单 §0 第 2 条：终点 = `Idle_01@0` **逐位** —— **全链唯一一次"
            "首尾闭合**（用同一组参数 `IDLE.idle_pose(arm, 0.0)` 生成，不手调末帧）。"
            "实测 pos %.6f mm / dir %.6f°（容差 %.2f mm / %.2f°）。"
            "守卫 = `E11_TP_ENDZERO=1`。"
            % (wp, wd, SEAM_POS_MAX_MM, SEAM_DIR_MAX_DEG))

    # ---- 收招不许瞬停（末 8 帧）-----------------------------------------
    snap, snap_at = 0.0, None
    for index in range(max(1, len(samples) - 8), len(samples)):
        step, at = _worst_step(samples, index - 1, index)
        if step > snap:
            snap, snap_at = step, at
    report["no_snap_stop_step_deg"] = round(snap, 4)
    report["no_snap_stop_at"] = snap_at
    report["no_snap_stop_ok"] = bool(snap <= NO_SNAP_END_DEG)

    # ---- 上游未蒙皮件（模型侧遗留，报告用）------------------------------
    bpy.context.scene.frame_set(END)
    bpy.context.view_layer.update()
    prof_end = D.body_low_profile()
    hem = min(prof_end.get("Jacket_Hem", 1e9),
              prof_end.get("Jacket_Hem_Line", 1e9))
    report["rvw_hem_end_mm"] = round(hem, 2)
    report["rvw_hem_note"] = (
        "★ 清单 §1 风险 6：`Jacket_Hem` / `Jacket_Hem_Line` 未蒙皮（E04 起登记）。"
        "本支**末段回到直立** ⟹ 浮片会自己回到腰上：末帧衣摆世界 z = **%.2f mm**"
        "（E10 尸体末帧它在身体上方 902 mm ⟹ 常驻穿帮）。直立姿下**不穿帮**，"
        "但**属性仍是上游缺陷**（待主人决策，见 E10 日志 §七）。"
        % (hem,))

    report["meta"] = meta
    failed = sorted(k for k, v in report.items()
                    if k.endswith("_ok") and v is not True and v is not None)
    non_ok = sorted(k for k, v in report.items()
                    if isinstance(v, bool) and v is False)
    report["failed"] = failed
    report["non_ok_bools"] = non_ok
    A.report("E11_REPORT", report)

    if not SKIP_RENDER:
        key = [START, 8, RIGOR_END, 30, PROP_END, 58, TUCK_END, HK_FRAME,
               HK_END, 92, STAND_START, 112, END]
        A.render_pose_sheet(arm, action, key, "rvwkey",
                            views=(VIEW_RVW_SIDE, VIEW_RVW_FRONT, VIEW_RVW_3Q))
        side = sorted(set(list(range(START, END + 1, 4)) + [END]))
        A.render_pose_sheet(arm, action, side, "rvw", views=(VIEW_RVW_SIDE,))
        A.save_project()
        A.export_glb(arm)
    print("E11_DONE failed=%s non_ok=%s" % (failed, non_ok))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("E11_FAILURE " + traceback.format_exc())
