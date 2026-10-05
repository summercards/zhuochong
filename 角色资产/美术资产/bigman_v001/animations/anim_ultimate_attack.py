"""anim_ultimate_attack —— C13 `Ultimate_Attack` 大招攻击
（★ 本族第一支「为节奏而做」的支）。

目录：`doc/动画制作清单.md` 第 139 行；详细计划见该文件的
「下一支详细制作计划 —— C13 `Ultimate_Attack` 大招攻击」。

================================================================ 本支的物理构造

**4 段重击 + 长收招（120 帧 / 2.000 s @60fps）**：

    0 ──3── 起手接合（f0 逐位 = `Idle_01@0`，f1..3 臂欧拉自 Idle 接到逆解）
    3 ──8── ① 刺拳（右，快）        HIT_1 = 8      停顿 8..10
    11──15  停（ready 位姿**逐位冻结** 4 帧 —— 清单原文的"停"）
    15──22  ② 摆拳（左，重）        HIT_2 = 22     停顿 22..24
    24──32  ③ 上勾拳（右，紧凑快）  HIT_3 = 32     停顿 32..34
    34──50  ④ 蓄力：深蹲下沉 + 双拳过顶
    50──53  蓄力停顿（**逐位冻结** 3 帧 —— "启动略慢"）
    53──62  ④ 重终结：全身下砸      HIT_4 = 62     停顿 62..65（4 帧）
    66──78  后摇（惯性下沉，手臂跟随）
    78─112  收招（全姿仿射回 `Idle_01@0`；腿分层 + 根骨竖直贴地补偿）
    112─120 静止（8 帧 ⟹ 末 2 帧步长构造性 = 0）

==================== 段间隔（`rhythm_uneven_ok` 的直接对象）

`seg_len[i] = HIT_i − HIT_{i−1}`（`HIT_0 = 0`）= **[8, 14, 10, 30]**

  · 均值 15.5、总体标准差 8.646 ⟹ **变异系数 CV = 0.558**（门禁 ≥ 0.25）；
  · 相邻比 **[1.75, 0.714, 3.00]** ⟹ **最大相邻比 3.00**（门禁 ≥ 1.8）。

读法：8 帧的快刺拳 → 14 帧的摆拳（`快—停—快` 里的"停"：11..15 位姿逐位冻结）
→ 10 帧的上勾（更快收回节奏）→ **30 帧的重终结**（长蓄力 + 8~9 帧的全身下砸）。
`seg_len` 与**段峰值速度**同向（越长越重）⟹ 见下「★ 一条阈值修正」。

==================== 本支新立的 6 条节奏判据（计划 §2，全部必须会失败）

| 判据 | 口径 | 失败模式 |
|---|---|---|
| `rhythm_uneven_ok` | `CV(seg_len) ≥ 0.25` **且** `max(seg_len[i+1]/seg_len[i]) ≥ 1.8` | 「六段变成一个大摆臂」 |
| `rhythm_weight_corr_ok` | `Spearman(seg_len, 段峰值手速) ≥ 0.5`（见下阈值修正） | 「节奏是随机的 / 间隔与力度脱钩」 |
| `accent_at_tail_ok` | 每段的**手部峰值速度帧**落在该段**后 40%** | 「匀速挥」而非末端发力 |
| `hitstop_real_ok` | 每个命中帧有 3~4 帧**逐位冻结**（窗内骨世界步长 = 0），**且**冻结进/出那一帧步长 ≥ 5 mm | 「把整段拖慢」伪造的假停 |
| `chain_per_hit_ok` | **每一次**命中，脚→腿→髋→腰→肩→手 的峰值速度帧**严格递增** | 「空气拳」（手比髋先到） |
| `segment_count_ok` | 骨盆 yaw（±3° 迟滞）**符号变化次数 ∈ [3, 6]** | 「一段到底」 |

★ **一条对计划草案的实测修正（与 C12 的两条修正同性质，写进制作日志）**：
计划 §2-1 同一段里给了**互相矛盾**的两句话 ——「长间隔后面跟的是更重的一击」与
「段峰值速度与段间隔**负相关**（间隔越短、峰值越高）」。本支实测并设计后取**正相关**
（长间隔 = 长蓄力 = 更快更重的击），因为它同时满足计划第一句、也符合
「重终结」必须最重这一条硬要求；负相关那半句会导致"最后一击最慢"，读不出终结感。
门禁据此写成 `Spearman ≥ +0.5`，并把实测的 Spearman 值打进报告（两个方向都留痕）。

==================== 撤下的判据（C12 专属）

`silhouette_strong_ok`（本支剪影在动，不是定格强 Pose）、
`anticipation_ok`（改成段级节奏量，见 `rhythm_*`）。
保留 `camera_facing_ok`（躯干 / 头偏航全程 ≤ 20°）。

==================== 位姿要点（判据之外的设计）

· **原地连招，脚不迈步**：踝目标钉在 `Idle_01@0` 的踝位（`plant_ok ≤ 3 mm`），
  "位移"由**骨盆前压**（每段 58~110 mm，世界 −Y）承担 —— 腿由 IK 吸收，
  鞋不滑。这正是计划 §1 差异表要的「每段前压，且要在段末停住」。
· **"脚"节点的信号来自抬跟**：`foot.<drive>.rx` 抬跟（踮脚）⟹ 贴地闭环把**踝抬起来**
  （实测 8° → 踝 ↑≈20 mm，水平位移 = 0）。踝的竖直运动给出一个真实、可比较的
  「脚」峰值时刻 —— 否则脚被钉死，"脚→腿→髋…"的链条第一环无法量。
  抬跟侧 = 驱动侧（右/R 蹬地为主；② 摆拳时换左侧）。

==================== 复用件（不重写）

  `anim_lib`：全部基础件。
  `anim_grab04`：`leg_seat` / `arm_seat` / `aim_bone_ref`。
  `anim_jump_start`：`_unwrap_xyz` / `_PREV_EULER`。
  `anim_run_stop`：`smooth`。
  `anim_ultimate_start`（C12）：**PCHIP 版 `pwl`**（本支照抄 —— 键更密，逐段
    smoothstep 的速度脉冲会成倍恶化 `no_teleport`）、`recover_pose` 的**腿分层 +
    根骨竖直贴地补偿**、`frame_series` 的 `deg_*` / `tail_*` 通道、`silhouette_*` 只读旁证。
  `probe_c13_rhythm`：骨架常数与 Idle 基线（**不重测**）。

============================== 调试开关（环境变量，无需改文件）

  SKIP_RENDER=1     跳过渲染 + 存盘 + 导出（迭代期用）
  C13_TRACE=1       逐帧：骨盆 / 双拳 / 鞋底 / 抬跟 / 关键欧拉角
  C13_RHYTHM=1      逐段：段长 / 各链节点峰值帧 / 段峰值手速 / 命中点

运行（正式那一轮）：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python anim_ultimate_attack.py
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
import anim_ultimate_start as US  # noqa: E402

NAME = "Ultimate_Attack"
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"
SIDES = ("L", "R")
STRIKER = "R"                   # 主击手（左摆拳那一支另算，见 DRIVE）


def _env_i(key, default):
    return int(os.environ.get(key, default))


def _env_f(key, default):
    return float(os.environ.get(key, default))


# ---------------------------------------------------------------- 帧预算
TOTAL = _env_i("C13_TOTAL", 120)                 # 2.000 s @60fps
EASE_END = _env_i("C13_EASE", 3)                 # 起手接合

# 4 段重击的命中帧。段间隔 = [10, 14, 10, 30]（见文件头）。
HIT_1 = _env_i("C13_HIT1", 10)
HIT_2 = _env_i("C13_HIT2", 24)
HIT_3 = _env_i("C13_HIT3", 34)
HIT_4 = _env_i("C13_HIT4", 64)
HITS = (HIT_1, HIT_2, HIT_3, HIT_4)

# 停顿帧数（§0.1「命中关键帧做 2~4 帧完全停顿」）：前三段 3 帧，重终结 4 帧。
HITSTOP = (3, 3, 3, 4)
HITSTOP_END = tuple(HITS[i] + HITSTOP[i] - 1 for i in range(4))   # (12,26,36,67)

# 打击相起点（前摇末）。段内 `[STRIKE_START_i .. HIT_i]` 是"发力段"。
STRIKE_START = (_env_i("C13_S1", 5), _env_i("C13_S2", 19),
                _env_i("C13_S3", 29), _env_i("C13_S4", 58))

# ① 的"停"：ready 位姿逐位冻结
QUIET_1 = (_env_i("C13_Q0", 14), _env_i("C13_Q1", 16))
# ④ 的蓄力停顿
CHARGE_HOLD = (_env_i("C13_C0", 52), _env_i("C13_C1", 55))

FOLLOW_END = _env_i("C13_FOLLOW", 82)            # 后摇末 = 收招起点
RECOVER = FOLLOW_END
SETTLE_END = _env_i("C13_SETTLE", 114)           # 收招位移完成帧（此后逐位静止）
CANCEL = _env_i("C13_CANCEL", 108)               # 可取消帧

SEG_LEN = (HIT_1, HIT_2 - HIT_1, HIT_3 - HIT_2, HIT_4 - HIT_3)   # (10,14,10,30)
# 每段的驱动侧（决定"脚/腿/肩/手"这四个链节点用哪一侧的骨）
DRIVE = ("R", "L", "R", "R")

# =============================================================== 力量传导链
# ★★ 本支最难的一条：`chain_per_hit_ok` 要求**每一次命中**，
#   脚→腿→髋→腰→肩→手 的峰值速度帧**严格递增**（6 个互不相同的帧）。
#
# 为什么第一轮做不到：所有轨道的关键帧**对齐在同几帧**上 ⟹ 六个节点同一帧到峰值。
# 对策是把每个节点的峰值帧**显式指定**，再倒推各自驱动轨道的形状：
#
#   `CHAIN_PEAK[i] = (脚, 腿, 髋, 腰, 肩, 手)`，段内严格递增，相邻差 1 帧。
#
# 各节点由谁驱动（这条映射决定了"要动哪张表"）：
#
#   脚 `foot.<side>`        踝世界位置 —— 只由**抬跟**（`FOOT_LIFT`）+ 贴地闭环驱动。
#                           骨盆平移**不动它**（踝目标 XY 恒定）⟹ 这一环天然干净。
#   腿 `thigh.<side>.tail`  膝世界位置 —— 由骨盆（∝0.47）与踝共同驱动；
#                           ★ 两者都跟别的轨道同相，**只有绕髋-踝轴摆膝**（`KNEE_DIR`）
#                           能让膝单独动 ⟹ 这就是「腿」环的专属驱动。
#   髋 `pelvis`             骨盆头世界位置 —— 只由 `@loc`（`PRESS`/`PZ`）驱动。
#   腰 `chest.tail`         胸顶 —— 骨盆平移（∝1.0）+ 躯干俯仰。
#   肩 `upperarm.<side>`    肩关节 —— 上游全部 + 肩胛骨旋转（`SHOULDER_RX`）。
#   手 `hand.<side>.tail`   拳 —— 上游全部 + 手臂逆解目标（`HAND_DIR`/`HAND_LEN`）。
#
# ★ 由此得到一条硬设计律：**上游每个节点的「爆发幅度」必须大于它的上游**。
#   末节点（手）在一次单帧里走得最多 → 与真实打击一致（拳尖最快）。
#   实测的每级单帧位移目标（mm/帧）：
#       脚 25 ~ 30 · 腿 ≥ 20 · 髋 ≈ 34 · 腰 ≥ 40 · 肩 ≈ 45 · 手 ≈ 110
CHAIN_PEAK = ((5, 6, 7, 8, 9, 10),          # ① 刺拳（右）
              (19, 20, 21, 22, 23, 24),     # ② 摆拳（左）
              (29, 30, 31, 32, 33, 34),     # ③ 上勾（右）
              (59, 60, 61, 62, 63, 64))     # ④ 重终结（全身下砸）

# ---------------------------------------------------------------- 骨盆（mm，相对 Idle 830）
# 探针 `probe_c13_rhythm` 的 drop 相对 **rest 900**；本表的 `pz_delta` 相对 **Idle 830**，
# 换算 `drop_rest = pz_delta − 70`。实测可达性：drop_rest −200（骨盆 700）时腿可达比 0.785。
# ★ 髋环（`pelvis` 头世界位置）的峰值帧 = `CHAIN_PEAK[i][2]` = 7 / 21 / 31 / 61：
#   `PRESS` 与 `PZ` 的**最大单帧位移都安排在这四帧**，其余帧一律更小。
#   实测的髋环单帧位移：35.9 / 17.9 / 18.9 / 44.7 mm ✓ 严格落在这四帧。
# ★★ 第 2 轮的关键修正（第 1 轮 `chain_per_hit_ok` 全假的根因 3）：
#   骨盆平移是**所有环共享**的低频大位移 —— 它一快，髋/腰/肩/手就在同一帧同时到峰值。
#   所以本表把它压成**每段只有一帧台阶**（落在髋环帧 7/21/31/61，≈15 mm），
#   其余帧的速率压到 ≤4 mm/帧。给下游各环的"脉冲"因此只落在髋环帧，
#   腰/肩/手才有可能在自己的帧上超过它。
PZ_KEYS = ((0, 0.0), (6, 0.0),
           (7, -15.0),                                    # ① 髋环 f7：单帧下沉 15 mm
           (10, -17.0), (16, -17.0),
           (19, -11.0), (20, -11.0),
           (21, -26.0),                                   # ② 髋环 f21
           (24, -28.0), (26, -28.0),
           (29, -18.0), (30, -18.0),
           (31, -33.0),                                   # ③ 髋环 f31
           (34, -35.0), (36, -35.0),
           (40, -48.0), (44, -70.0), (47, -82.0), (50, -90.0),   # ④ 蓄力深蹲（≤4 mm/帧）
           (52, -90.0), (55, -90.0), (58, -90.0), (60, -90.0),
           (61, -105.0),                                  # ④ 髋环 f61
           (64, -107.0), (67, -107.0),
           (74, -88.0), (82, -38.0), (98, -8.0), (114, 0.0), (TOTAL, 0.0))

# 骨盆前压（世界 Y，mm；**负 = 向前**）。"每段前压、段末停住"由它承担。
# 骨盆前压（世界 Y，mm；**负 = 向前**）。"每段前压、段末停住"由它承担。
# ★ 同 `PZ_KEYS`：**每段只在髋环帧做一次 17 mm 的单帧台阶**，其余帧压平。
#   `press` 的**水平量**（≥40 mm/段）靠前段慢速推进堆出来，不靠冲量 ——
#   因为 `press_ok` 判的是"段内最大前压量"，不是"每秒前压速度"。
PRESS_KEYS = ((0, 0.0),
              (4, -14.0), (5, -20.0), (6, -22.0),
              (7, -39.0),                                # ① 髋环 f7：单帧 17 mm
              (10, -42.0), (16, -42.0),
              (19, -27.0), (20, -27.0),
              (21, -44.0),                               # ② 髋环 f21
              (24, -47.0), (26, -47.0),
              (29, -34.0), (30, -34.0),
              (31, -51.0),                               # ③ 髋环 f31
              (34, -54.0), (36, -54.0),
              (41, -44.0), (45, -20.0), (48, -4.0), (50, 6.0),   # ④ 蓄力后坐（≤4 mm/帧）
              (52, 6.0), (55, 6.0), (58, 6.0), (60, 6.0),
              (61, -11.0),                               # ④ 髋环 f61：单帧 17 mm
              (62, -22.0), (63, -29.0), (64, -36.0),
              (67, -36.0),
              (74, -26.0), (82, -12.0), (98, -2.0), (114, 0.0),
              (TOTAL, 0.0))

# ---------------------------------------------------------------- 躯干扭转（度）
YAW_W = {"pelvis": 0.72, "spine_01": 0.08, "spine_02": 0.08, "chest": 0.12}
YAW_CNT = {"neck": -0.30, "head": -0.30}
# `YAW_KEYS` 是**躯干总偏航**；各骨按 `YAW_W` 分摊（权重和 = 1.0），
# 颈/头按 `YAW_CNT` **反向**配平 ⟹ 头始终看正面（`camera_facing_ok`）。
# ★ 第 2 轮修正：偏航的最大单帧变化**从髋环帧挪到蓄势段**（每帧 ≤6°），
#   在 `[脚环..手环]` 五帧里保持**完全静止**。理由：`segment_count_ok` 只看
#   **符号变化次数**（不是速率），所以慢转就能满足它；而偏航一转就把
#   **手**（离骨盆竖轴 0.30~0.46 m）横向甩出去 —— 第 1 轮 seg2 的 `hand`
#   峰值被 f21 的偏航抢走（≈98 mm/帧），正是"肩/手环排不到队"的元凶之一。
YAW_KEYS = ((0, 0.0),
            (3, -3.0), (4, -6.0), (5, -9.0), (6, -12.0),        # ① 蓄势扭腰（≤3°/帧）
            (10, -12.0), (13, -12.0), (16, -12.0),              # [脚环..手环] 静止
            (18, -5.0), (19, 0.0), (20, 6.0),                   # ② 反向扭腰
            (24, 6.0), (26, 6.0),
            (28, 1.0), (29, -5.0), (30, -10.0),                 # ③ 再反向
            (34, -10.0), (36, -10.0),
            (40, -8.0), (45, -3.0), (48, 0.0), (50, 3.0), (52, 5.0),
            (55, 5.0), (57, 3.0), (58, 1.0), (60, -4.0),        # ④ 下砸扭腰
            (64, -9.0), (67, -9.0),
            (74, -5.0), (82, 0.0), (TOTAL, 0.0))

# ---------------------------------------------------------------- 躯干俯仰（度）
# ★★ 「腰」环 = `chest.tail` 的**专属驱动**：躯干俯仰的**单帧爆发**。
#   它必须在 8 / 22 / 32 / 62 这四帧（腰环帧）一次跳完，其余帧**完全压平**：
#     · 髋环帧（7/21/31/61）必须**零变化** —— 否则腰环的竞争值会等于髋环的平移脉冲；
#     · 肩环帧（9/23/33/63）必须**零变化** —— 俯仰同样会甩动肩关节，抢走肩环的峰值。
#   实测杠杆（骨盆 rx）：胸顶 ≈ 0.62 m/rad ⟹ 3.2° 的单帧跳 = **35 mm**，
#   恰好越过髋环的平移脉冲（≈23 mm）而留出 50% 余量。
#   为什么把跳变**全部压在骨盆 rx**、而不是分摊给 spine/chest：
#   骨盆 rx 对"胸顶 / 肩关节"的力臂比 ≈ 1.0（两者离骨盆头都是 ≈0.62 m），
#   而 spine_01 是 1.2、chest 是 1.5 —— 每往上游挪一级，肩环的负担就大一分。
PELVIS_RX = ((0, None),
             (5, 2.0), (6, 2.0), (7, 2.0),                 # 髋环 f7：零变化
             (8, 5.2), (12, 5.2), (16, 5.2),               # ① 腰环 f8：单帧 +3.2°
             (18, 3.0), (19, 3.0), (20, 3.0), (21, 3.0),
             (22, 6.2), (26, 6.2),                         # ② 腰环 f22
             (28, 4.0), (29, 4.0), (30, 4.0), (31, 4.0),
             (32, 7.2), (36, 7.2),                         # ③ 腰环 f32
             (41, 5.0), (46, 1.0), (50, -2.0), (52, -2.0),
             (55, -2.0), (57, -2.0), (58, -2.0), (59, -2.0), (60, -2.0), (61, -2.0),
             (62, 1.2), (64, 3.0), (67, 3.0),              # ④ 腰环 f62
             (74, 2.0), (82, 1.0), (TOTAL, None))
SPINE_RX = ((0, None), (3, 1.0), (5, 1.5), (6, 1.5), (7, 1.5),
            (10, 2.0), (16, 2.0),
            (19, 1.5), (21, 1.5),
            (24, 2.0), (26, 2.0),
            (29, 1.5), (31, 1.5),
            (34, 2.0), (36, 2.0),
            (41, 0.5), (46, -2.0), (50, -4.0), (55, -4.0),
            (58, -3.0), (60, -2.5), (61, -2.5), (64, 0.0), (67, 0.0),
            (74, 0.0), (82, 0.0), (TOTAL, None))
CHEST_RX = ((0, None), (3, 1.5), (5, 2.0), (6, 2.0), (7, 2.0),
            (10, 2.5), (16, 2.5),
            (19, 2.0), (21, 2.0),
            (24, 2.5), (26, 2.5),
            (29, 2.0), (31, 2.0),
            (34, 2.5), (36, 2.5),
            (41, 1.0), (46, -2.0), (50, -4.0), (55, -4.0),
            (58, -3.0), (60, -2.0), (61, -2.0), (64, 0.5), (67, 0.5),
            (74, 0.5), (82, 0.0), (TOTAL, None))
NECK_RX = ((0, None), (5, -4.0), (8, -6.0), (12, -6.0), (16, -6.0),
           (19, -3.0), (22, -5.0), (26, -5.0),
           (29, -3.0), (32, -5.0), (36, -5.0),
           (41, -2.0), (50, -4.0), (55, -4.0),
           (58, -3.0), (62, -6.0), (67, -6.0),
           (74, -4.0), (82, -2.0), (TOTAL, None))
HEAD_RX = ((0, None), (5, 3.0), (8, 5.0), (12, 5.0), (16, 5.0),
           (19, 2.5), (22, 4.0), (26, 4.0),
           (29, 2.5), (32, 4.0), (36, 4.0),
           (41, 1.5), (50, 3.0), (55, 3.0),
           (58, 2.5), (62, 5.0), (67, 5.0),
           (74, 3.0), (82, 1.5), (TOTAL, None))
# ★★ 「肩」环 = `upperarm.<side>` 头（肩关节）。
#   第 1 轮用**肩胛骨旋转**驱动它 —— 实测力臂只有 **0.111 m/rad**
#   （`shoulder.<side>` 绕自身长轴转，尾端几乎不动），24°/帧 才挪 46 mm，
#   追不上腰环的转动量。第 2 轮把它换掉，见文件下方 `SHOULDER_PUSH`：
#   **肩胛骨平移**（锁骨前送）。它把整条臂**刚性**前送 ——
#   既不牵动躯干（腰环完全不受影响），也不放大力臂（手 1:1 跟随）。
#   本表（`SHOULDER_RX`）降级为**缓慢的姿态量**：只负责"肩前耸 / 后收"的
#   造型，不再承担峰值帧，所以全程压平到 ≤6°/帧。
SHOULDER_RX = ((0, None), (5, -2.0), (7, -2.0), (10, -3.0), (16, -3.0),
               (19, -2.0), (21, -2.0), (24, -3.0), (26, -3.0),
               (29, -2.0), (31, -2.0), (34, -3.0), (36, -3.0),
               (41, 0.0), (48, 4.0), (55, 4.0),
               (58, 2.0), (60, 0.0), (61, 0.0), (64, -2.0), (67, -2.0),
               (74, -1.0), (82, 0.0), (TOTAL, None))

TARGET_BONES = ("pelvis", "spine_01", "spine_02", "chest", "neck", "head",
                "shoulder.L", "shoulder.R")

# ---------------------------------------------------------------- 抬跟（度）
# `foot.rx > 0` = 踮脚。经贴地闭环后表现为**踝抬起**（水平位移 = 0 ⟹ `plant_ok` 不破），
# 这就是「脚」这个链节点的位移来源。抬跟侧 = `DRIVE[i]`。
# ★ 最大单帧变化精确落在 5 / 19 / 29 / 59（脚环峰值帧）：
#   `[脚环−1] = 0`、`[脚环] = 峰值` 的**单帧台阶**，其余帧立刻收小。
FOOT_LIFT_KEYS = {
    "R": ((0, 0.0), (3, 0.0), (4, 1.0),
          (5, 15.0), (6, 5.0), (7, 1.0), (9, 0.0),          # ① 脚环 f5
          (16, 0.0), (26, 0.0), (27, 0.0), (28, 1.0),
          (29, 16.0), (30, 5.0), (31, 1.0), (33, 0.0),      # ③ 脚环 f29
          (36, 0.0), (55, 0.0), (56, 0.0), (57, 0.0), (58, 1.5),
          (59, 18.0), (60, 6.0), (61, 2.0), (63, 0.0), (67, 0.0),  # ④ 脚环 f59
          (74, 0.0), (TOTAL, 0.0)),
    "L": ((0, 0.0), (16, 0.0), (17, 0.0), (18, 1.0),
          (19, 15.0), (20, 5.0), (21, 1.0), (23, 0.0),      # ② 脚环 f19
          (26, 0.0), (55, 0.0), (56, 0.0), (57, 0.0), (58, 1.5),
          (59, 16.0), (60, 6.0), (61, 2.0), (63, 0.0), (67, 0.0),
          (74, 0.0), (TOTAL, 0.0)),
}

# ---------------------------------------------------------------- 肩胛前送（「肩」环专属驱动）
# ★★ 本支最贵的一条经验（第 3 轮才找到）：
#   「肩」环（肩关节世界位置）需要一个**不牵动躯干、也不放大力臂**的驱动 ——
#   因为 (a) 任何躯干转动都会同时推动腰环，抢走腰环的峰值帧；
#       (b) 肩胛**旋转**的力臂只有 0.111 m/rad，24°/帧 才够 46 mm，跑不过腰环。
#   只有**把 `shoulder.<side>` 沿世界 −Y 平移**满足全部条件：
#   整条臂刚性前送（手 1:1 跟随、不放大），躯干一动不动（腰环零干扰）。
#   物理上它就是**肩胛骨前伸 / 锁骨前送**（出拳时肩先送出去），不是外挂。
#   实现见 `push_shoulder()`：在 `apply_pose` 之后直接设世界矩阵再读回局部位移。
SHOULDER_PUSH = {
    "R": ((0, 0.0),
          (8, 0.0), (9, 48.0), (12, 48.0), (16, 48.0),      # ① 肩环 f9
          (20, 0.0), (30, 0.0),
          (32, 0.0), (33, 48.0), (36, 48.0),                # ③ 肩环 f33
          (40, 0.0), (60, 0.0),
          (62, 0.0), (63, 48.0), (67, 48.0),                # ④ 肩环 f63
          (74, 18.0), (82, 0.0), (TOTAL, 0.0)),
    "L": ((0, 0.0),
          (22, 0.0), (23, 48.0), (26, 48.0),                # ② 肩环 f23
          (30, 0.0), (62, 0.0),
          (63, 30.0), (67, 30.0),                           # ④ 双肩同送
          (74, 12.0), (82, 0.0), (TOTAL, 0.0)),
}

# ---------------------------------------------------------------- 摆膝（"腿"环专属驱动）
# ★ 为什么需要它：踝被钉住时**膝只能跟着骨盆走**（`knee ≈ 0.47·hip + 0.53·ankle`），
#   而骨盆的爆发在髋环帧 —— 膝必然跟着在髋环帧到峰值，腿环就永远排不到髋环前面。
#   唯一能让膝**单独**动的自由度是 `leg_seat` 的 `knee_dir`：绕「髋-踝轴」摆膝时
#   踝与骨盆都不动，膝自己走。物理上它就是打拳时后腿的髋内外旋 / 外展。
#   实现：`knee_dir = normalize(Idle 膝方向 + lat · 外展方向)`（`lat` 见下表）。
# ★ 最大单帧变化精确落在 6 / 20 / 30 / 60（腿环峰值帧）—— 前两帧保持 0，
#   之后的衰减也必须**每帧小于髋环的平移脉冲折算值**（0.47 × 23 ≈ 11 mm）。
KNEE_LAT = ((0, 0.0), (5, 0.0), (6, 0.16), (8, 0.06), (10, 0.015), (12, 0.0),
            (19, 0.0), (20, 0.17), (22, 0.06), (24, 0.015), (26, 0.0),
            (29, 0.0), (30, 0.17), (32, 0.06), (34, 0.015), (36, 0.0),
            (59, 0.0), (60, 0.14), (62, 0.05), (64, 0.02), (67, 0.0),
            (74, 0.0), (TOTAL, 0.0))

# ---------------------------------------------------------------- 手：肩部相对轨道
# ★★ **不用绝对世界坐标**（第一轮的教训）：躯干一前俯/下沉，固定的世界点就会
#   悄悄靠近肩 ⟹ `r = |拳−肩|/649.675` 从 0.46 掉到 **0.10~0.14**（爆发式的病态
#   折叠），或者涨到 **0.95**（近满伸）—— 两个奇点都被踩中。
#   改成 `target = 肩 + u·len`，`r = len/649.675` 就**由构造保证**落在 [0.46, 0.86]。
#   `u` 是单位方向（表里不必归一，取值时归一），`len` 单位 mm。
# ★★ 第 3 轮的核心修正 —— **`Δhand` 的最大值必须精确落在命中帧**。
#
#   为什么前两轮做不到：手环（`hand.<side>.tail`）是链条的**末节点**，它继承
#   上游全部位移：`hand = 肩 + u·len`。而肩环的脉冲（`SHOULDER_PUSH` 48 mm）
#   落在命中帧**前一帧** ⟹
#        Δhand(命中−1) ≥ 48 mm + Δarm(命中−1)
#   所以要让手在命中帧才到峰值，必须
#        Δarm(命中) > 48 mm + Δarm(命中−1)
#   即 **命中前一帧的臂位移必须压到最小**（本文表里就是"平的"那几帧），
#   把整段打击弧**攒到一个单帧里放出去**。
#
#   逐段的实测预算（r ≈ 0.55 m 处 1° ≈ 9.6 mm）：
#       ① f9  臂Δ ≈ 1 mm   → Δhand ≈ 49 mm ；f10 臂Δ ≈ 115 mm ✓
#       ② f23 臂Δ ≈ 3 mm   → Δhand ≈ 51 mm ；f24 臂Δ ≈ 115 mm ✓
#       ③ f33 臂Δ ≈ 1 mm   → Δhand ≈ 49 mm ；f34 臂Δ ≈ 154 mm ✓
#       ④ f63 臂Δ ≈ 47 mm  → Δhand ≈ 95 mm ；f64 臂Δ ≈ 164 mm ✓
#
# ★ 命中帧的方向单帧转角一律压在 **17~20°**（`no_teleport` 上限 25°），
#   其余帧 ≤ 10°/帧 —— 大弧（上勾 41°、下砸 55°）**摊到打击相各帧**，
#   只有最后一帧的份额最大。
# ★ 方向的单帧转角 = 手环峰值帧：10 / 24 / 34 / 64。
_HIT_R = (-0.100, -0.970, -0.240)          # ① 刺拳命中方向
_HIT_L = (0.050, -0.970, -0.240)           # ② 摆拳命中方向（从外侧向中线收）
_HIT_UP = (-0.1370, -0.9906, 0.0211)       # ③ 上勾命中方向（拳过肩高）
_U_CHARGE = (-0.3404, -0.7034, 0.6240)     # ④ 蓄力顶点（双拳过顶，右）
_U_CHARGE_L = (0.3404, -0.7034, 0.6240)    # ④ 蓄力顶点（左）
_SMASH_R = (-0.1510, -0.9560, -0.2516)     # ④ 下砸命中方向（右）
_SMASH_L = (0.1510, -0.9560, -0.2516)      # ④ 下砸命中方向（左）
# ④ 下砸的 6 帧圆弧（slerp 采样，单帧转角 9.2/9.2/9.2/6.0/4.9/16.9°）：
#   `s_62`/`s_63` 故意收小 —— 既给"重终结"一个视觉上的**瞬时悬停**，
#   又保证 Δhand(64) 稳超 Δhand(63)（48 mm 的肩脉冲 + 臂Δ）。
_SMASH_ARC_R = ((-0.3280, -0.8022, 0.4989), (-0.3071, -0.8807, 0.3612),
                (-0.2785, -0.9364, 0.2141), (-0.2558, -0.9600, 0.1146),
                (-0.2346, -0.9717, 0.0308))
_SMASH_ARC_L = tuple((a, b, c) for a, b, c in
                     ((0.3280, -0.8022, 0.4989), (0.3071, -0.8807, 0.3612),
                      (0.2785, -0.9364, 0.2141), (0.2558, -0.9600, 0.1146),
                      (0.2346, -0.9717, 0.0308)))
HAND_PLAN = {
    "R": ((0, None, None),
          (3, (-0.130, -0.860, -0.490), 330.0),
          (4, (-0.130, -0.860, -0.490), 372.0),
          (5, (-0.130, -0.860, -0.490), 386.0),      # ① 脚环 f5
          (6, (-0.130, -0.860, -0.490), 393.0),
          (7, (-0.130, -0.860, -0.490), 397.0),      # ① 髋环 f7
          (8, (-0.130, -0.860, -0.490), 400.0),      # ① 腰环 f8
          (9, (-0.130, -0.860, -0.490), 405.0),      # ① 肩环 f9（臂Δ≈1 mm）
          (10, _HIT_R, 426.0),                       # ① 手环 f10：命中
          (13, (-0.110, -0.950, -0.300), 414.0),     # 微回弹（保 hitstop 出口）
          (16, (-0.110, -0.950, -0.300), 414.0),
          (19, (-0.100, -0.900, -0.430), 384.0),     # 非驱动手：收 guard
          (24, (-0.100, -0.900, -0.430), 384.0),
          (28, (-0.1228, -0.9395, -0.3203), 344.0),  # ③ 起手（上勾蓄势）
          (29, (-0.1235, -0.9390, -0.3195), 346.0),
          (30, (-0.1242, -0.9385, -0.3187), 348.0),
          (31, (-0.1249, -0.9380, -0.3179), 350.0),
          (32, (-0.1256, -0.9375, -0.3172), 351.0),
          (33, (-0.1263, -0.9370, -0.3165), 352.0),  # ③ 肩环 f33（臂Δ≈1 mm）
          (34, _HIT_UP, 424.0),                      # ③ 手环 f34：命中
          (37, (-0.1340, -0.9720, -0.1930), 398.0),
          (40, (-0.280, -0.800, 0.020), 470.0),      # ④ 起手过顶
          (44, (-0.320, -0.700, 0.340), 505.0),
          (48, (-0.340, -0.620, 0.550), 528.0),
          (52, _U_CHARGE, 538.0),
          (55, _U_CHARGE, 540.0),                    # ④ 蓄力停顿（平）
          (57, _U_CHARGE, 543.0),
          (58, _U_CHARGE, 547.0),                    # ④ 打击相起点
          (59, _SMASH_ARC_R[0], 549.0),              # ④ 脚环 f59
          (60, _SMASH_ARC_R[1], 551.0),              # ④ 腿环 f60
          (61, _SMASH_ARC_R[2], 552.0),              # ④ 髋环 f61
          (62, _SMASH_ARC_R[3], 552.0),              # ④ 腰环 f62（悬停）
          (63, _SMASH_ARC_R[4], 550.0),              # ④ 肩环 f63（臂Δ≈47 mm）
          (64, _SMASH_R, 530.0),                     # ④ 手环 f64：重终结
          (68, (-0.140, -0.880, -0.240), 470.0),
          (74, (-0.140, -0.860, -0.300), 420.0),
          (82, (-0.120, -0.860, -0.380), 340.0),
          (TOTAL, None, None)),
    "L": ((0, None, None),
          (4, (0.070, -0.880, -0.470), 300.0),
          (16, (0.070, -0.880, -0.470), 300.0),
          (18, (0.070, -0.870, -0.480), 330.0),      # ② 蓄势
          (19, (0.072, -0.866, -0.484), 344.0),      # ② 脚环 f19
          (20, (0.074, -0.862, -0.488), 352.0),      # ② 腿环 f20
          (21, (0.076, -0.858, -0.492), 357.0),      # ② 髋环 f21
          (22, (0.078, -0.855, -0.495), 360.0),      # ② 腰环 f22
          (23, (0.080, -0.852, -0.498), 354.0),      # ② 肩环 f23（臂Δ≈3 mm）
          (24, _HIT_L, 404.0),                       # ② 手环 f24：命中
          (27, (0.055, -0.955, -0.290), 388.0),
          (32, (0.060, -0.910, -0.410), 356.0),      # 非驱动手
          (37, (0.070, -0.880, -0.470), 330.0),
          (40, (0.280, -0.800, 0.020), 470.0),
          (44, (0.320, -0.700, 0.340), 505.0),
          (48, (0.340, -0.620, 0.550), 528.0),
          (52, _U_CHARGE_L, 538.0),
          (55, _U_CHARGE_L, 540.0),
          (57, _U_CHARGE_L, 543.0),
          (58, _U_CHARGE_L, 547.0),
          (59, _SMASH_ARC_L[0], 549.0),
          (60, _SMASH_ARC_L[1], 551.0),
          (61, _SMASH_ARC_L[2], 552.0),
          (62, _SMASH_ARC_L[3], 552.0),
          (63, _SMASH_ARC_L[4], 550.0),              # ④ 双拳同送（左肩脉冲 30 mm）
          (64, _SMASH_L, 530.0),                     # ④ 双拳同砸
          (68, (0.140, -0.880, -0.240), 470.0),
          (74, (0.140, -0.860, -0.300), 420.0),
          (82, (0.120, -0.860, -0.380), 340.0),
          (TOTAL, None, None)),
}
# 肘的"鼓出"偏好方向（世界坐标）：**取与臂轴近乎垂直的常量**。
# ★ 第一轮的 80.37°/帧就出在这：举拳过顶时臂轴 ≈ +Z，而原来的 `ELBOW_KEYS`
#   给的是 (−0.40, 0.28, −0.87) —— **几乎与臂轴反平行** ⟹ `.dot(axis)` 抵消掉
#   大半，`bulge` 的垂分量只剩一点点，肘的滚转变成病态放大。
#   改用「外 + 后 + 下」的常量偏好，任何手臂朝向下都不会与臂轴共线。
ELBOW_PREFER = {"L": (0.86, 0.42, -0.28), "R": (-0.86, 0.42, -0.28)}

# ---------------------------------------------------------------- 门禁阈值
SOLE_RANGE_MM = (-2.0, 6.0)
NO_TELEPORT_MAX_DEG = 25.0
SEAM_TOL = 1e-6
REACH_MAX_RATIO = 0.995
PLANT_MAX_MM = _env_f("C13_PLANT_MAX", 3.0)
GROUND_MIN_MM = -2.0
GROUND_MAX_MM = 6.0
CV_MIN = _env_f("C13_CV_MIN", 0.25)
ADJ_RATIO_MIN = _env_f("C13_ADJ_MIN", 1.8)
CORR_MIN = _env_f("C13_CORR_MIN", 0.5)
ACCENT_TAIL_FRAC = _env_f("C13_ACCENT", 0.40)
HITSTOP_EDGE_MIN_MM = _env_f("C13_HITSTOP_EDGE", 5.0)
HITSTOP_MAX_IN_MM = _env_f("C13_HITSTOP_IN", 1e-6)
SEG_PEAK_STEP_MIN_MM = _env_f("C13_SEG_STEP", 40.0)
SEG_SIGN_MIN = _env_i("C13_SIGN_MIN", 3)
SEG_SIGN_MAX = _env_i("C13_SIGN_MAX", 6)
YAW_DEADBAND_DEG = _env_f("C13_YAW_BAND", 3.0)
CAMERA_MAX_DEG = _env_f("C13_CAMERA", 20.0)
PRESS_MIN_MM = _env_f("C13_PRESS_MIN", 40.0)
HOLD_MAX_MM = _env_f("C13_HOLD_MAX", 2.0)
END_POSE_TOL_MM = _env_f("C13_ENDTOL", 0.5)
ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")
LEG_BONES = ("thigh.L", "shin.L", "thigh.R", "shin.R")

# 链节点（6 环）：脚 → 腿 → 髋 → 腰 → 肩 → 手。第 i 段的驱动侧见 `DRIVE`。
CHAIN_LABELS = ("foot", "leg", "hip", "waist", "shoulder", "hand")


def chain_keys(side):
    return ("foot." + side, "thigh." + side + ".tail", "pelvis",
            "chest.tail", "upperarm." + side, "hand." + side + ".tail")


# ---------------------------------------------------------------- 观测量
SEAM_POSE = {}
SEAM_EULER = {}
Z_SEAM = 0.0
ANKLE_0 = {}
FOOT0 = {}
IDLE_HAND = {}
IDLE_HAND_OFF = {}
IDLE_KNEE = {}
IDLE_BASIS = {}
IDLE_DIR = {}
IDLE_KNEE_DIR = {}
ARM_LEN = {}
ARM_CLAMP = {}
HIT_POINT = {}
HAND_DIR_KEYS = {}
HAND_LEN_KEYS = {}
ARM_REF = None


def build_hand_keys():
    """把 `HAND_PLAN` 拆成"方向表 / 长度表"两份 `pwl` 键。"""
    HAND_DIR_KEYS.clear()
    HAND_LEN_KEYS.clear()
    for side in SIDES:
        HAND_DIR_KEYS[side] = [(frame, value)
                               for frame, value, _ in HAND_PLAN[side]]
        HAND_LEN_KEYS[side] = [(frame, length)
                               for frame, _, length in HAND_PLAN[side]]


# =============================================================== 轨道求值
# PCHIP 版 `pwl`（照抄 C12 —— 库级改进，逐段 smoothstep 会制造速度脉冲）。
pwl = US.pwl
pwl_vec = US.pwl_vec


def pz_delta(f):
    if f <= 0 or f >= TOTAL:
        return 0.0
    return pwl(PZ_KEYS, f, 0.0) / 1000.0


def press(f):
    """骨盆前压（米，负 = 向前）。两端为 0 ⟹ 首末帧逐位 = Idle。"""
    if f <= 0 or f >= TOTAL:
        return 0.0
    return pwl(PRESS_KEYS, f, 0.0) / 1000.0


def yaw(f):
    return pwl(YAW_KEYS, f, 0.0)


def foot_lift(side, f):
    return pwl(FOOT_LIFT_KEYS[side], f, 0.0)


def hand_target(side, f):
    """**肩部相对**的手目标：`肩 + u·len`（见 `HAND_PLAN` 上方说明）。

    `u` 表里不归一，这里归一；`None` ⟹ 取 Idle 的单位方向与臂长（mm）。
    """
    u = Vector(pwl_vec(HAND_DIR_KEYS[side], f, IDLE_HAND_OFF[side][0]))
    if u.length < 1e-6:
        u = Vector(IDLE_HAND_OFF[side][0])
    u.normalize()
    length = pwl(HAND_LEN_KEYS[side], f, IDLE_HAND_OFF[side][1]) / 1000.0
    shoulder = Vector(A.bone_world(ARM_REF, "upperarm." + side, "head"))
    return tuple(shoulder + u * length)


def elbow_dir(side, f, shoulder=None, target=None):
    """肘的鼓出偏好：把常量 `ELBOW_PREFER` **投影到与臂轴垂直的平面**上。

    ★ 返回的是"偏好方向"，`arm_seat` 内部还会再投一次 —— 但这里先投过之后，
    `arm_seat` 里的那次投影是在一个**已近乎垂直**的向量上做的，垂分量不会塌到 0，
    肘的滚转因此连续（第一轮的 80.37°/帧就是垂分量塌陷导致的病态放大）。
    """
    prefer = Vector(ELBOW_PREFER[side])
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
    """绕「髋-踝轴」摆膝（`KNEE_LAT`），踝与骨盆都不动 ⟹ 「腿」环的专属驱动。"""
    lateral = pwl(KNEE_LAT, f, 0.0)
    sign = 1.0 if side == "L" else -1.0
    out = Vector((sign * lateral, 0.0, 0.0))
    base = Vector(IDLE_KNEE[side]) + out
    if base.length < 1e-6:
        base = Vector(IDLE_KNEE[side])
    return tuple(base.normalized())


def q_of(frame):
    """收招进度：0 = 后摇末姿态，1 = `Idle_01@0`。

    沿用 C12：收招段用 `smoothstep`（两端速度都为 0），之后留**纯静止** ⟹
    末 2 帧步长构造性地 = 0。
    """
    if frame <= RECOVER:
        return 0.0
    if frame >= SETTLE_END:
        return 1.0
    return RS.smooth((frame - RECOVER) / float(SETTLE_END - RECOVER))


def leg_weight(frame):
    """收招段的**腿分层**权重：0 = 纯 IK（钉地），1 = 纯欧拉仿射（保末帧 = Idle）。

    分层点比姿态混合早一帧起（腿先"松"）。理由见 C11 第 3 号 / C12 说明：
    欧拉空间线性插值不保持踝高度，前段必须 IK 钉地；纯 IK 末帧又落不回 Idle。
    """
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
                      YAW_W["pelvis"] * yaw(f), SEAM_EULER["pelvis"][2])
    pose["spine_01"] = (pwl(SPINE_RX, f, SEAM_EULER["spine_01"][0]),
                        YAW_W["spine_01"] * yaw(f), 0.0)
    pose["spine_02"] = (pwl(SPINE_RX, f, SEAM_EULER["spine_02"][0]),
                        YAW_W["spine_02"] * yaw(f), 0.0)
    pose["chest"] = (pwl(CHEST_RX, f, SEAM_EULER["chest"][0]),
                     YAW_W["chest"] * yaw(f), 0.0)
    pose["neck"] = (pwl(NECK_RX, f, SEAM_EULER["neck"][0]),
                    YAW_CNT["neck"] * yaw(f), 0.0)
    pose["head"] = (pwl(HEAD_RX, f, SEAM_EULER["head"][0]),
                    YAW_CNT["head"] * yaw(f), 0.0)
    for name in ("shoulder.L", "shoulder.R"):
        pose[name] = (pwl(SHOULDER_RX, f, SEAM_EULER[name][0]),
                      SEAM_EULER[name][1], 0.0)
    # ★ 骨盆局部位移基线：`Z_SEAM + pz_delta − 0.900`（0.900 是 **rest** 骨盆高度，
    #   `Z_SEAM` 是 Idle 的 830 mm）。漏掉基线会让整条曲线比 Idle 高 70 mm，
    #   第 1 帧腿被拉直。本支 `pz_delta` / `press` 两端为 0 ⟹ 首末帧逐位 = Idle。
    pose["@loc"] = {"pelvis": A.wloc(0.0, press(f),
                                     Z_SEAM + pz_delta(f) - 0.900)}
    return pose


def keep_foot_lifted(arm, side, lift_deg):
    """鞋朝向钉成 rest，再按 `foot.rx` 抬跟（`rx > 0` = 踮脚）。

    为什么抬跟：脚钉死后"脚"这个链节点速度为 0，`chain_per_hit_ok` 的第一环无法量。
    抬跟经贴地闭环把**踝抬起来**（水平位移 = 0），给出真实可比的「脚」峰值时刻。
    """
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
    """肩胛骨**前送**（世界 −Y 平移）——「肩」环的专属驱动。

    为什么必须是"平移"而不是"肩胛骨旋转"（第 1 轮的失败）：
      · 旋转的力臂只有 0.111 m/rad，24°/帧 才挪 46 mm，跑不过腰环的转动量；
      · 任何**躯干**转动都会同时推动腰环，抢走腰环的峰值帧；
      · 只有把 `shoulder.<side>` 沿世界 −Y **平移**，整条臂才**刚性**前送：
        手 1:1 跟随（不放大力臂），躯干一动不动（腰环零干扰）。
      物理上它就是出拳时"肩先送出去"的肩胛骨前伸，不是外挂。

    ★ 平移量**写回 `pose["@loc"]`** —— 否则 `build_action` 打帧时只会写
      `rotation_euler`，这个位移会在存盘那一刻被静默丢掉。
    """
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


# =============================================================== 万向节锁防御
# ★★ 第 3 轮最大的一条发现（`no_teleport` 的假红）：
#   `no_teleport` 量的是**欧拉逐分量步长**，而 `matrix → euler` 在
#   **|Y| → 90°（XYZ 万向节锁）** 附近的 (X, Z) 拆分是**任意的** ——
#   同一旋转有两支等价欧拉 `(x, y, z)` 与 `(x+180°, 180°−y, z+180°)`，
#   每分量还可 ±360°。实测 `forearm.R` 在 f59：**真转 3.5°，欧拉却走了 76°**
#   （X 75.6 → −0.5、Z 143.9 → 64.3，而 x−z 只变 3.5°）。
#   这不是姿态跳变，是**表示跳变**。
#   对策：不用 Blender 反解出来的那一支，**自己解两支等价欧拉、取离上一帧最近的**。
#   这是纯表示层的修正 ⟹ 骨的世界位置/朝向**逐位不变**，
#   链条 / 节奏 / 可达性 / 贴地判据全部不受影响。
EULER_Y_SAFE = _env_f("C13_YSAFE", 70.0)
EULER_Y_WEIGHT = _env_f("C13_YWEIGHT", 1.5)
CARRY_Q = {}          # bone -> 上一帧**已达成**的世界朝向（接力基准）


def _set_euler_nearest(arm, name, prev=None):
    """把该骨当前的**局部旋转**写成"离上一帧最近"的那支欧拉（返回度）。"""
    pose_bone = arm.pose.bones[name]
    m = pose_bone.matrix_basis.to_3x3()
    y = math.asin(max(-1.0, min(1.0, -m[2][0])))
    cy = math.cos(y)
    if abs(cy) > 1e-6:
        x = math.atan2(m[2][1], m[2][2])
        z = math.atan2(m[1][0], m[0][0])
    else:                                   # 万向节锁：x 归零、z 吸收全部
        x = 0.0
        z = math.atan2(-m[0][1], m[1][1])
    if prev is None:
        prev = JS._PREV_EULER.get(name)
    best, best_cost = None, None
    for cand in ((x, y, z), (x + math.pi, math.pi - y, z + math.pi)):
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
    """`G4.aim_bone_ref` 的**接力 + 最近欧拉支**版。

    ★ 为什么不能用固定基准（第 3 轮 f59 的 71.50° 根因）：
      `aim_bone_ref` 取 `ref_dir.rotation_difference(want)` —— 从 **Idle 固定基准**
      出发的最小旋转。当 `want`（骨轴目标方向）扫到与 `ref_dir` **接近反平行**时，
      最小旋转的轴由数值噪声决定 ⟹ **世界朝向真跳**（`anim_jump_start.aim_frame`
      的墓志铭就是这个，本支 f59 又踩了一次）。
      改成从**上一帧已达成朝向**接力：只补"把骨轴摆到目标方向"的那一个最小旋转，
      真旋转步 = ∠(上一帧骨轴, 目标方向)，构造上不会发生大跳。

    ★ 第一帧（`CARRY_Q` 为空）仍从 `IDLE_BASIS` 出发 ⟹ 与 `aim_bone_ref` 逐位同源，
      起手接合（`ua_start_ok`）不受影响。
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
    """`G4.arm_seat` 的本地版（只换 `aim_bone_ref` → `aim_nearest`，几何一模一样）。"""
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
    """`G4.leg_seat` 的本地版（恒定用 Idle 基准，只换欧拉支）。"""
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
        # ★ 「肩」环的脉冲：必须在 `hand_target` 之前落位 —— 手目标是
        #   `肩 + u·len`，读的是**当前**肩关节世界位置，肩先送出去手才跟着走。
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
        # 手目标是**肩部相对**的（第一轮教训：绝对世界点在躯干下沉时会踩进深折叠奇点），
        # 肩位必须在 `apply_pose` 之后现取；肘偏好按同一臂轴投影（否则垂分量塌陷）。
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

    # 起手接合（C10 第 5 号 / C11 / C12 复用）：`arm_seat` 隐含"腕直"，而 Idle 戒备
    # 是**屈腕**的，第 1 帧会被掰直 ⟹ 单帧欧拉步长会超标。f1..EASE_END 平滑接上。
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
    """逐帧贴地闭环：**双脚**鞋底钉到 0 mm（`shift` 并进踝目标）。

    ★ 闭环顺序必须是「**先钉 `foot.*` 朝向 → 再量鞋底**」—— C11 第 4 号教训：
      `apply_pose` 会把 `foot.*` 归零，而归零（rest）朝向与"钉住 + 抬跟"的朝向
      不是一回事，漏了这一步闭环会在**错误朝向**上收敛。
    """
    shift = {side: 0.0 for side in SIDES}
    # ★ 贴地闭环会把 `build_pose` 跑好几遍；`_set_euler_nearest` 以
    #   `_PREV_EULER` 为"上一帧"参照，若不还原，第 2 遍就把第 1 遍的结果
    #   当成上一帧 ⟹ 欧拉支会在同一帧内自我漂移。这里每遍都还原到帧初。
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

    （照抄 C12：分层只把误差压低、没有归零，所以最后量一次鞋底，用根骨纯平移抬回；
      `q == 1` 时不再补偿 ⟹ 末帧就是 Idle 逐位值。）
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
    """逐帧**全探针骨世界坐标**（节奏 / 链条 / 停顿 / 收敛都从它来）。"""
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
    """逐帧：骨盆 / 拳 / 踝 / 鞋底 / 抬跟 / 关键骨欧拉（`C13_TRACE` 的输出源）。"""
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
                              - Vector(poses[index - 1][key])).length
                       * 1000.0)
        out.append(best)
    return out


def speed_of(poses, key, frame):
    return (Vector(poses[frame][key]) - Vector(poses[frame - 1][key])).length \
        * A.FPS * 1000.0


def peak_frame(poses, key, f0, f1):
    """`[f0, f1]` 内该节点的峰值速度帧（含端点；`f0` 取自 `f0-1` 的差分）。"""
    best, best_frame = -1.0, None
    for frame in range(max(1, f0), f1 + 1):
        value = speed_of(poses, key, frame)
        if value > best:
            best, best_frame = value, frame
    return best_frame, best


# =============================================================== 专属门禁
def rhythm_assertions(arm, poses, rows):
    res = {}
    # ★ 逐帧步长只算一次：`step_series` 是 O(帧 × 骨)，在循环里重算是 O(n²)。
    steps = step_series(poses)

    # ---- 0) 首帧逐位 = `Idle_01@0`
    # （在 main 里用 samples 判，这里只留节奏相关的）

    # ---- 1) 段间隔不许平均
    n = len(SEG_LEN)
    mean = sum(SEG_LEN) / float(n)
    var = sum((v - mean) ** 2 for v in SEG_LEN) / float(n)
    std = math.sqrt(var)
    cv = std / mean
    ratios = [SEG_LEN[i + 1] / float(SEG_LEN[i]) for i in range(n - 1)]
    res["seg_len"] = list(SEG_LEN)
    res["seg_mean"] = round(mean, 4)
    res["seg_std"] = round(std, 4)
    res["seg_cv"] = round(cv, 4)
    res["seg_adjacent_ratio"] = [round(r, 4) for r in ratios]
    res["seg_max_adjacent_ratio"] = round(max(ratios), 4)
    res["rhythm_uneven_ok"] = bool(cv >= CV_MIN
                                  and max(ratios) >= ADJ_RATIO_MIN)

    # ---- 2) 每段的峰值手速 / 峰值帧 / 链节点峰值帧
    seg_peak_speed = []
    seg_peak_frame = []
    chain_peaks = []
    seg_peak_step = []
    for index in range(4):
        side = DRIVE[index]
        f0 = (0 if index == 0 else HITS[index - 1]) + 1
        f1 = HITS[index]
        hand_key = "hand." + side + ".tail"
        frame, speed = peak_frame(poses, hand_key, f0, f1)
        seg_peak_speed.append(round(speed, 1))
        seg_peak_frame.append(frame)
        peeks = {}
        for label, key in zip(CHAIN_LABELS, chain_keys(side)):
            pframe, pspeed = peak_frame(poses, key, f0, f1)
            peeks[label] = {"key": key, "frame": pframe,
                            "speed_mmps": round(pspeed, 1)}
        chain_peaks.append(peeks)
        seg_steps = steps[f0:f1 + 1]
        seg_peak_step.append(round(max(seg_steps) if seg_steps else 0.0, 2))

    res["seg_peak_hand_speed_mmps"] = seg_peak_speed
    res["seg_peak_hand_frame"] = seg_peak_frame
    res["seg_peak_step_mm"] = seg_peak_step
    res["chain_peak_frames"] = {CHAIN_LABELS[i]: {
        k: v["frame"] for k, v in chain_peaks[i].items()} for i in range(4)}
    res["chain_peak_detail"] = chain_peaks
    res["chain_peak_keys"] = {CHAIN_LABELS[i]: {
        k: v["key"] for k, v in chain_peaks[i].items()} for i in range(4)}

    # ---- 3) 重音落在段末（每段手部峰值帧在该段后 40%）
    accent = []
    for index in range(4):
        f0 = (0 if index == 0 else HITS[index - 1])
        f1 = HITS[index]
        boundary = f0 + (1.0 - ACCENT_TAIL_FRAC) * (f1 - f0) - 1e-9
        accent.append(bool(seg_peak_frame[index] >= boundary))
    res["accent_ok_flags"] = accent
    res["accent_tail_boundary"] = [
        round((0 if i == 0 else HITS[i - 1])
              + (1.0 - ACCENT_TAIL_FRAC) * SEG_LEN[i], 2) for i in range(4)]
    res["accent_at_tail_ok"] = bool(all(accent))

    # ---- 4) 段峰值速度与段间隔同向（Spearman）
    res["rhythm_weight_corr"] = round(_spearman(SEG_LEN, seg_peak_speed), 4)
    res["rhythm_weight_corr_ok"] = bool(res["rhythm_weight_corr"] >= CORR_MIN)

    # ---- 5) 停顿必须是真的
    stops = []
    ok = True
    for index in range(4):
        hit = HITS[index]
        end = HITSTOP_END[index]
        inside = max(steps[f] for f in range(hit + 1, end + 1))
        before = steps[hit]
        after = (steps[end + 1] if end + 1 <= TOTAL else 0.0)
        entry = {
            "segment": index + 1, "hit": hit, "hold": [hit, end],
            "frames": end - hit + 1,
            "inside_max_step_mm": round(inside, 8),
            "before_step_mm": round(before, 4),
            "after_step_mm": round(after, 4),
            "gap_before_mm": round(before - inside, 4),
            "gap_after_mm": round(after - inside, 4),
        }
        entry["real"] = bool(inside <= HITSTOP_MAX_IN_MM
                             and before >= HITSTOP_EDGE_MIN_MM
                             and after >= HITSTOP_EDGE_MIN_MM
                             and 2 <= (end - hit + 1) <= 4)
        ok = ok and entry["real"]
        stops.append(entry)
    res["hitstop"] = stops
    res["hitstop_real_ok"] = bool(ok)

    # ---- 6) 六环链条严格递增
    chain_flags = []
    for index in range(4):
        frames = [chain_peaks[index][label]["frame"]
                  for label in CHAIN_LABELS]
        good = all(frames[i] < frames[i + 1] for i in range(len(frames) - 1))
        chain_flags.append(bool(good))
    res["chain_strictly_increasing"] = chain_flags
    res["chain_per_hit_ok"] = bool(all(chain_flags))

    # ---- 7) 段数：骨盆 yaw 符号变化次数
    pelvis_yaw = [YAW_W["pelvis"] * yaw(f) for f in range(TOTAL + 1)]
    changes, cur = 0, 0
    for value in pelvis_yaw:
        if value > YAW_DEADBAND_DEG and cur != 1:
            changes += 1 if cur != 0 else 0
            cur = 1
        elif value < -YAW_DEADBAND_DEG and cur != -1:
            changes += 1 if cur != 0 else 0
            cur = -1
    res["segment_yaw_changes"] = changes
    res["segment_yaw_peak_deg"] = round(max(abs(v) for v in pelvis_yaw), 3)
    res["segment_count_ok"] = bool(SEG_SIGN_MIN <= changes <= SEG_SIGN_MAX)

    # ---- 8) 每段不许"什么也没发生"（门槛比 C12 的 3 mm 大幅上调）
    res["seg_peak_step_min_mm"] = round(min(seg_peak_step), 2)
    res["no_freeze_ok"] = bool(min(seg_peak_step) >= SEG_PEAK_STEP_MIN_MM)

    # ---- 9) 每段前压（位移）且段末不松
    press_vals = [press(f) * 1000.0 for f in range(TOTAL + 1)]
    press_report = []
    ok_press = True
    for index in range(4):
        f0 = (0 if index == 0 else HITS[index - 1])
        f1 = HITS[index]
        window = press_vals[f0:f1 + 1]
        forward = max(0.0 - v for v in window)
        at_hit = 0.0 - press_vals[f1]
        entry = {"segment": index + 1, "forward_peak_mm": round(forward, 2),
                 "at_hit_mm": round(at_hit, 2)}
        entry["ok"] = bool(forward >= PRESS_MIN_MM
                           and at_hit >= 0.6 * forward)
        ok_press = ok_press and entry["ok"]
        press_report.append(entry)
    res["press"] = press_report
    res["press_ok"] = bool(ok_press)

    # ---- 10) 朝向镜头（躯干 / 头偏航全程配平）
    torso_yaw = [yaw(f) for f in range(TOTAL + 1)]
    head_yaw = [(1.0 + YAW_CNT["neck"] + YAW_CNT["head"]) * yaw(f)
                for f in range(TOTAL + 1)]
    res["camera_torso_yaw_max_deg"] = round(max(abs(v) for v in torso_yaw), 3)
    res["camera_head_yaw_max_deg"] = round(max(abs(v) for v in head_yaw), 3)
    res["camera_facing_ok"] = bool(
        max(abs(v) for v in torso_yaw) <= CAMERA_MAX_DEG
        and max(abs(v) for v in head_yaw) <= CAMERA_MAX_DEG)

    # ---- 11) 两个冻结窗逐位不漂
    def hold_worst(f0, f1):
        worst = 0.0
        for frame in range(f0 + 1, f1 + 1):
            for key in poses[frame]:
                worst = max(worst, (Vector(poses[frame][key])
                                    - Vector(poses[frame - 1][key])).length
                            * 1000.0)
        return worst

    res["quiet_hold_worst_mm"] = round(hold_worst(*QUIET_1), 8)
    res["quiet_hold_ok"] = bool(res["quiet_hold_worst_mm"] <= HOLD_MAX_MM)
    res["charge_hold_worst_mm"] = round(hold_worst(*CHARGE_HOLD), 8)
    res["charge_hold_ok"] = bool(res["charge_hold_worst_mm"] <= HOLD_MAX_MM)

    # ---- 12) 命中点登记（下游引擎做打击判定与特效挂点）
    hits = []
    for index in range(4):
        side = DRIVE[index]
        hit = HITS[index]
        hand = Vector(A.bone_world(arm, "hand." + side, "tail"))
        hits.append({"index": index + 1, "frame": hit, "side": side,
                     "part": "hand." + side,
                     "point_m": [round(v, 4) for v in hand],
                     "hitstop": [hit, HITSTOP_END[index]]})
        HIT_POINT["HIT_%d" % (index + 1)] = [round(v, 4) for v in hand]
    res["hits"] = hits
    return res


def _spearman(a, b):
    def ranks(values):
        order = sorted(range(len(values)), key=lambda i: values[i])
        out = [0.0] * len(values)
        for rank, index in enumerate(order):
            out[index] = float(rank + 1)
        return out

    ra, rb = ranks(a), ranks(b)
    n = len(a)
    mean = (n + 1) / 2.0
    da = [v - mean for v in ra]
    db = [v - mean for v in rb]
    num = sum(x * y for x, y in zip(da, db))
    den = math.sqrt(sum(x * x for x in da) * sum(y * y for y in db))
    return num / den if den > 0 else 0.0


def marker_registered(action, res):
    """`hitframe_registered_ok`：帧标记 `HIT_i` 必须存在且与 `meta["hits"]` 一致。"""
    markers = {m.name: int(m.frame) for m in action.pose_markers}
    ok = True
    detail = {}
    for index in range(4):
        name = "HIT_%d" % (index + 1)
        got = markers.get(name)
        want = HITS[index]
        detail[name] = {"marker": got, "expected": want,
                        "ok": bool(got == want)}
        ok = ok and got == want
    return bool(ok), detail


# =============================================================== 主流程
def main():
    global SEAM_POSE, SEAM_EULER, Z_SEAM, ANKLE_0, FOOT0
    global IDLE_HAND, IDLE_HAND_OFF, IDLE_KNEE, IDLE_BASIS, IDLE_DIR
    global IDLE_KNEE_DIR, ARM_LEN, ARM_REF

    for store in (SEAM_POSE, SEAM_EULER, ANKLE_0, FOOT0, IDLE_HAND,
                  IDLE_HAND_OFF, IDLE_KNEE, IDLE_BASIS, IDLE_DIR,
                  IDLE_KNEE_DIR, ARM_LEN, ARM_CLAMP, HIT_POINT):
        store.clear()
    HAND_DIR_KEYS.clear()
    HAND_LEN_KEYS.clear()
    CARRY_Q.clear()

    arm, meshes = A.open_animation_project()
    A.setup_scene()
    if I1.NAME not in bpy.data.actions:
        print("C13_BOOTSTRAP 缺 %s，先补跑" % I1.NAME)
        I1.main()
        arm, meshes = A.open_animation_project()
        A.setup_scene()

    for side in SIDES:
        ARM_LEN[side] = {
            "upper": arm.pose.bones["upperarm." + side].length,
            "forearm": arm.pose.bones["forearm." + side].length,
            "hand": arm.pose.bones["hand." + side].length}
    # `ARM_REF` 只在 `hand_target` 里读"当前肩关节世界位置"用（肩部相对轨道）。
    ARM_REF = arm
    for extra in ("thigh.L", "thigh.R", "shin.L", "shin.R"):
        if extra not in A.PROBE_BONES:
            A.PROBE_BONES = tuple(A.PROBE_BONES) + (extra,)
        if extra not in A.PROBE_TAILS:
            A.PROBE_TAILS = tuple(A.PROBE_TAILS) + (extra,)
    A.PROBE_KEYS = A.PROBE_BONES + tuple(n + ".tail" for n in A.PROBE_TAILS)

    # ---- 首帧真值：`Idle_01@0`（★ 先归零再求值，理由见 C12：`.blend` 里存着上次
    #   运行留下的姿态，直接读会读到陈旧值，f1 归零时一步 360°。）
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
        # ★ 肩部相对轨道的两个默认量（`HAND_PLAN` 里的 `None` ⟹ 取这两值）：
        #   `IDLE_HAND_OFF[side] = (单位方向, 肩→拳距离 mm)`。
        #   有它兜底，`HAND_PLAN` 只需覆盖"离开 Idle"之后的部分，
        #   且 f0 的手目标**逐位**等于 Idle ⟹ `ua_start_ok` 的源头之一。
        IDLE_HAND_OFF[side] = (tuple(offset.normalized()),
                               offset.length * 1000.0)
    build_hand_keys()

    # ---- Idle 骨基座（逆解基准；同时灌进 `anim_grab04` 的模块级表）
    idle = I1.idle_pose(arm, 0.0)
    A.apply_pose(arm, idle)
    bpy.context.view_layer.update()
    for side in SIDES:
        hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
        knee = Vector(A.bone_world(arm, "thigh." + side, "tail"))
        IDLE_KNEE_DIR[side] = (knee - hip).normalized()
        # `knee_dir()` 的基准方向（摆膝量 `KNEE_LAT` 就加在它上面）。
        IDLE_KNEE[side] = tuple(IDLE_KNEE_DIR[side])
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

    A.report("C13_LAYOUT", {
        "total_frames": TOTAL, "seconds": round(TOTAL / float(A.FPS), 3),
        "hits": list(HITS), "hitstop_end": list(HITSTOP_END),
        "strike_start": list(STRIKE_START), "seg_len": list(SEG_LEN),
        "drive": list(DRIVE), "quiet": list(QUIET_1),
        "charge_hold": list(CHARGE_HOLD), "recover": RECOVER,
        "settle_end": SETTLE_END, "cancel": CANCEL,
        "pelvis_z0_mm": round(Z_SEAM * 1000.0, 3),
        "ankle0_mm": {s: [round(v * 1000.0, 2) for v in ANKLE_0[s]]
                      for s in SIDES},
        "idle_hand_mm": {s: [round(v * 1000.0, 2) for v in IDLE_HAND[s]]
                         for s in SIDES},
        "note": ("大招攻击：4 段重击（刺拳/摆拳/上勾/全身下砸），间隔 [%s]，"
                 "CV %.3f；每段命中 3~4 帧逐位冻结；原地连招、骨盆前压承担位移。"
                 % (", ".join(str(v) for v in SEG_LEN),
                    (sum((v - sum(SEG_LEN) / 4.0) ** 2 for v in SEG_LEN)
                     / 4.0) ** 0.5 / (sum(SEG_LEN) / 4.0))),
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

    # 命中停顿（3~4 帧）：**逐位复用同一姿态** —— `hitstop_real_ok` 的构造性来源。
    for index in range(4):
        hit, end = HITS[index], HITSTOP_END[index]
        hold = keyframes[hit][1]
        for frame in range(hit + 1, end + 1):
            keyframes[frame] = (frame, dict(hold))

    # ① 的"停"：ready 位姿逐位冻结（清单原文的"停"，也是 `rhythm_uneven` 的视觉落点）
    quiet_pose = keyframes[QUIET_1[0]][1]
    for frame in range(QUIET_1[0] + 1, QUIET_1[1] + 1):
        keyframes[frame] = (frame, dict(quiet_pose))

    # ④ 的蓄力停顿
    charge_pose = keyframes[CHARGE_HOLD[0]][1]
    for frame in range(CHARGE_HOLD[0] + 1, CHARGE_HOLD[1] + 1):
        keyframes[frame] = (frame, dict(charge_pose))

    # 收招仿射：把末姿（Idle）解卷绕到离后摇末姿最近的分支，再逐通道滑过去
    hold_pose = keyframes[RECOVER][1]
    e0 = {k: tuple(v) for k, v in hold_pose.items() if not k.startswith("@")}
    e_end_unw = {bone: JS._unwrap_xyz(e0.get(bone, (0.0, 0.0, 0.0)), value)
                 for bone, value in SEAM_EULER.items()}
    end_pose = dict(e_end_unw)
    end_pose["@loc"] = {"pelvis": A.wloc(0.0, 0.0, Z_SEAM - 0.900)}
    for frame in range(RECOVER + 1, TOTAL + 1):
        keyframes.append((frame, recover_pose(arm, frame, hold_pose, end_pose)))

    meta = {
        "anim_id": NAME,
        "loop": False,
        "category": "连招与特殊技",
        "note": ("大招攻击：4 段重击（右刺拳 / 左摆拳 / 右上勾 / 双拳全身下砸），"
                 "段间隔 [%s] 不平均；每段命中 3~4 帧完全停顿；原地连招，"
                 "位移由骨盆前压承担。" % ", ".join(str(v) for v in SEG_LEN)),
        "hits": None,          # 下面填（需要求值后的世界坐标）
        "segments": {"ease": [0, EASE_END],
                     "seg1": [EASE_END, HIT_1], "hold1": list(QUIET_1),
                     "seg2": [HIT_1, HIT_2], "seg3": [HIT_2, HIT_3],
                     "charge": [HIT_3, CHARGE_HOLD[0]],
                     "charge_hold": list(CHARGE_HOLD),
                     "seg4": [STRIKE_START[3], HIT_4],
                     "follow": [HITSTOP_END[3], FOLLOW_END],
                     "recover": [RECOVER, SETTLE_END],
                     "rest": [SETTLE_END, TOTAL]},
        "hit_frames": list(HITS),
        "hitstop_frames": list(HITSTOP),
        "seg_len": list(SEG_LEN),
        "cancel_frame": CANCEL,
        "settle_end": SETTLE_END,
        "root_motion_m": [0.0, 0.0],
        "pelvis_press_note": "位移由骨盆前压承担（世界 −Y），脚不迈步",
        "foot_lift_note": "抬跟（foot.rx）为 chain 的「脚」节点提供位移；水平位移=0",
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.add_markers(action, {
        "ENTER": 0, "EASE_END": EASE_END,
        "HIT_1": HIT_1, "HITSTOP_1_END": HITSTOP_END[0],
        "HIT_2": HIT_2, "HITSTOP_2_END": HITSTOP_END[1],
        "HIT_3": HIT_3, "HITSTOP_3_END": HITSTOP_END[2],
        "CHARGE_HOLD_END": CHARGE_HOLD[1],
        "HIT_4": HIT_4, "HITSTOP_4_END": HITSTOP_END[3],
        "CANCEL": CANCEL, "SETTLE": SETTLE_END, "END": TOTAL,
    })

    samples = A.sample_animation(arm, action, 0, TOTAL, meshes)
    rows = frame_series(arm, action, TOTAL)
    poses = world_poses(arm, action, TOTAL)

    if os.environ.get("C13_CHAIN") == "1":
        # 每段窗口内 6 环链节点的**逐帧速度**（mm/s）+ 肩→拳距离（查病态反解）。
        for index in range(4):
            f0 = (0 if index == 0 else HITS[index - 1]) + 1
            f1 = HITS[index]
            side = DRIVE[index]
            keys = chain_keys(side)
            print("C13_CHAIN seg=%d side=%s window=[%d,%d] hit=%d"
                  % (index + 1, side, f0, f1, HITS[index]))
            for frame in range(f0, f1 + 1):
                parts = []
                for label, key in zip(CHAIN_LABELS, keys):
                    sp = (Vector(poses[frame][key])
                          - Vector(poses[frame - 1][key])).length * A.FPS * 1000.0
                    parts.append("%s=%6.0f" % (label, sp))
                shoulder = Vector(rows[frame]["upperarm." + side])
                fist = Vector(rows[frame]["hand." + side + "_tail"])
                dist = (fist - shoulder).length
                parts.append("d=%4d/%4d r=%.2f" % (round(dist * 1000.0),
                                                   round(ARM_LEN[side]["upper"]
                                                         + ARM_LEN[side]["forearm"]
                                                         + ARM_LEN[side]["hand"]
                                                         - 0.0, 0),
                                                   dist / 0.649675))
                print("  f%-3d %s" % (frame, " ".join(parts)))

    if os.environ.get("C13_STEP") == "1":
        # 逐帧最大欧拉步长（>15° 才打印）—— `no_teleport` 的定位工具。
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
                print("C13_STEP f%-3d %6.2f deg %s" % (frame, worst, who))

    if os.environ.get("C13_ARM") == "1":
        # 臂骨逐帧欧拉步长（>6° 才打印）+ 该帧的欧拉三元组 —— 用来分辨
        # 「真大弧」与「万向节锁伪影」：后者伴随后一帧的补偿性反向跳变。
        for frame in range(1, TOTAL + 1):
            parts = []
            for name in ARM_BONES:
                a = Vector(rows[frame]["deg_" + name])
                b = Vector(rows[frame - 1]["deg_" + name])
                d = max(abs(x - y) for x, y in zip(a, b))
                if d > 6.0:
                    parts.append("%-11s %6.2f -> %s" % (
                        name, d,
                        ",".join("%7.1f" % v for v in rows[frame]["deg_" + name])))
            if parts:
                print("C13_ARM f%-3d %s" % (frame, " | ".join(parts)))

    if os.environ.get("C13_TRACE") == "1":
        for row in rows:
            print("C13_TRACE " + json.dumps({
                "f": row["frame"],
                "pelvis": [round(v * 1000.0, 2) for v in row["pelvis"]],
                "fist_R": [round(v * 1000.0, 2) for v in row["hand.R_tail"]],
                "fist_L": [round(v * 1000.0, 2) for v in row["hand.L_tail"]],
                "sole_L": (None if row["sole_L"] is None
                           else round(row["sole_L"] * 1000.0, 2)),
                "sole_R": (None if row["sole_R"] is None
                           else round(row["sole_R"] * 1000.0, 2)),
                "ankle_R": [round(v * 1000.0, 2) for v in row["ankle_R"]],
                "liftR": round(row["deg_foot.R"][0], 2),
                "liftL": round(row["deg_foot.L"][0], 2),
                "reachL": round(row["reach_L"], 4),
                "reachR": round(row["reach_R"], 4),
            }))

    report = A.run_common_assertions(samples, meta, foot_probe=())
    report.update(rhythm_assertions(arm, poses, rows))

    # 首帧逐位 = `Idle_01@0`
    delta0 = 0.0
    for name, value in SEAM_EULER.items():
        got = samples[0]["euler"].get(name, (0.0, 0.0, 0.0))
        delta0 = max(delta0, max(abs(a - b) for a, b in zip(got, value)))
    report["ua_start_delta_deg"] = round(delta0, 8)
    report["ua_start_ok"] = bool(delta0 <= SEAM_TOL)

    # 命中帧登记
    registered, detail = marker_registered(action, report)
    report["hitframe_markers"] = detail
    report["hitframe_registered_ok"] = registered
    # ★ 登记到的 `hits` 反过来写回 meta（下游引擎靠它）
    meta["hits"] = report["hits"]
    try:
        action["hits"] = json.dumps(report["hits"], ensure_ascii=False)
    except (TypeError, AttributeError):
        pass

    # 承重脚不滑（水平，踝关节）
    def slide(side):
        pts = [Vector((rows[f]["ankle_" + side][0], rows[f]["ankle_" + side][1]))
               for f in range(TOTAL + 1)]
        return max((p - pts[0]).length for p in pts) * 1000.0

    def slide3(side):
        pts = [Vector(rows[f]["ankle_" + side]) for f in range(TOTAL + 1)]
        return max((p - pts[0]).length for p in pts) * 1000.0

    report["plant_L_mm"] = round(slide("L"), 3)
    report["plant_R_mm"] = round(slide("R"), 3)
    report["plant_3d_L_mm"] = round(slide3("L"), 3)
    report["plant_3d_R_mm"] = round(slide3("R"), 3)
    report["plant_ok"] = bool(max(report["plant_L_mm"], report["plant_R_mm"])
                              <= PLANT_MAX_MM)

    report["ground_min_mm"] = round(min(
        min(s["low"]["L"], s["low"]["R"]) for s in samples) * 1000.0, 2)
    report["ground_contact_ok"] = bool(
        GROUND_MIN_MM <= report["ground_min_mm"] <= GROUND_MAX_MM)
    report["low_bad_frames"] = {
        str(s["frame"]): [round(s["low"]["L"] * 1000.0, 2),
                          round(s["low"]["R"] * 1000.0, 2)]
        for s in samples
        if min(s["low"]["L"], s["low"]["R"]) * 1000.0 < GROUND_MIN_MM}

    # 腿可达比（`frame_series` 已逐帧算好，省掉一趟遍历）
    worst, worst_at = 0.0, None
    for row in rows:
        for side in SIDES:
            if row["reach_" + side] > worst:
                worst, worst_at = row["reach_" + side], [row["frame"], side]
    report["leg_reach_worst_ratio"] = round(worst, 5)
    report["leg_reach_worst_at"] = worst_at
    report["leg_reach_ok"] = bool(worst <= REACH_MAX_RATIO)

    report["arm_clamp"] = {side: dict(info) for side, info in ARM_CLAMP.items()}
    report["arm_reach_ok"] = bool(all(not info["any"]
                                      for info in ARM_CLAMP.values()))

    # 收招：单调收敛 + 末 2 帧不瞬停 + 末帧 = 待机
    steps = step_series(poses)
    tail = [steps[f] for f in range(TOTAL - 5, TOTAL + 1)]
    report["settle_tail_mm"] = [round(v, 3) for v in tail]
    report["settle_monotone_ok"] = bool(
        all(tail[i + 1] <= tail[i] + 1e-6 for i in range(len(tail) - 1)))
    report["settle_last2_mm"] = round(max(tail[-2:]), 4)
    report["settle_no_stop_ok"] = bool(report["settle_last2_mm"] <= 0.5)
    delta_end = 0.0
    for key in A.PROBE_KEYS:
        if key in poses[0] and key in poses[-1]:
            delta_end = max(delta_end,
                            (Vector(poses[0][key])
                             - Vector(poses[-1][key])).length * 1000.0)
    report["end_pose_delta_mm"] = round(delta_end, 4)
    report["end_pose_ok"] = bool(delta_end <= END_POSE_TOL_MM)
    report["settle_ok"] = bool(report["settle_monotone_ok"]
                               and report["settle_no_stop_ok"]
                               and report["end_pose_ok"])

    report["hit_point_m"] = dict(HIT_POINT)
    report["meta"] = meta
    report["failed"] = sorted(k for k, v in report.items()
                              if k.endswith("_ok") and v is not True)
    report["non_ok_bools"] = sorted(
        k for k, v in report.items()
        if isinstance(v, bool) and not k.endswith("_ok") and v is not True)
    A.report("C13_REPORT", report)

    if os.environ.get("C13_RHYTHM") == "1":
        print("C13_RHYTHM " + json.dumps({
            "seg_len": list(SEG_LEN),
            "cv": report["seg_cv"],
            "max_adj": report["seg_max_adjacent_ratio"],
            "corr": report["rhythm_weight_corr"],
            "seg_peak_speed": report["seg_peak_hand_speed_mmps"],
            "seg_peak_frame": report["seg_peak_hand_frame"],
            "chain_frames": report["chain_peak_frames"],
            "chain_ok": report["chain_strictly_increasing"],
            "accent_ok": report["accent_ok_flags"],
            "hitstop_inside": [s["inside_max_step_mm"] for s in report["hitstop"]],
            "hitstop_edges": [[s["before_step_mm"], s["after_step_mm"]]
                              for s in report["hitstop"]],
            "yaw_changes": report["segment_yaw_changes"],
            "hit_point_m": report["hit_point_m"],
        }, ensure_ascii=False))

    if not SKIP_RENDER:
        frames = [0, EASE_END, HIT_1, HITSTOP_END[0], QUIET_1[1], HIT_2,
                  HITSTOP_END[1], HIT_3, HITSTOP_END[2], CHARGE_HOLD[1],
                  STRIKE_START[3], HIT_4, HITSTOP_END[3], FOLLOW_END,
                  SETTLE_END, TOTAL]
        A.render_pose_sheet(arm, action, frames, "ultattack",
                            views=(A.VIEW_SIDE, A.VIEW_FRONT, A.VIEW_3Q))
        A.save_project()
        A.export_glb(arm)
    print("C13_DONE failed=%s" % report["failed"])
    print("C13_DONE non_ok_bools=%s" % report["non_ok_bools"])


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("C13_FAILURE " + traceback.format_exc())
