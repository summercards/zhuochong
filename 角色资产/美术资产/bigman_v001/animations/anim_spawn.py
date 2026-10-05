"""anim_spawn —— E04 `Spawn` 入场（E 族第四支 / 第 60 支）。

清单原文：「**跳入、撞开门、从高处落地等，突出角色力量**」。

★★★ 本支与 E01 / E02 / E03 的三处根本不同（开工前想清楚）
    ① ★★★ **E04 是 E 族第一支「带根位移」的动画**。E01/E02/E03 全程**锁踝不迈步**
       （`root_motion = 0`），所有脚判据都建在「踝钉在站架世界点」上。
       E04 一跳起来这个前提**当场失效** ⟹ `foot_lock_ok` / `sole_ground_ok`
       对「空中段」**不适用** —— 那不是 bug，是**判据口径错了**。
       ⟹ 本支**按相位分段**：地面段 [START..TAKEOFF] ∪ [TOUCH..END] 锁踝；
          空中段 (TAKEOFF..TOUCH) 停用地面判据、改判 `sole_min_z > 0`。
    ② ★★ **「落地」= 冲击**，必须可量：躯干**净下沉**（`spawn_land_sink_ok`）
       + 落地窗口**逐帧姿态恒定**（`spawn_impact_hitstop_ok`，照 E03 的 hitstop 模式）
       + 四肢**压缩**（膝屈角下限）。只做「垂直下落 + 站住」会**轻飘飘**。
    ③ ★ **本支是「原地起跳」** ⟹ START **也** = `Idle_01@0`（站架 → 起跳 → 落地 → 站架）
       ⟹ `loop_seamless` / `end_matches_start_ok` **可沿用**（不必停用登记）。
       ★ 不做「从画外跳入」（那会逼着停用 `loop_seamless` 并另立空中入场姿）；
       「撞开门」也未做（需要世界实体代理板，§0 ④ 说「**默认不开**」，登记为设计选择）。
       本支落到的是清单的「**跳入 + 从高处落地**」两支语义。

★★★ 工程件 ①：相位时间轴（**逐帧显式打帧 + 时间冻结**，120 帧 = 2.0 s）
    `START(0) → CROUCH(16) → TAKEOFF(24) → APEX(42) → TOUCH(56) → LAND(60)
      →[落地定格 3 帧 60~62]→ SETTLE(78) → END(120)`
    · ★ 两个「脚」相位由**实测**给出，不是写死的漂亮数字：
      `TAKEOFF` = 第一个 `sole_min_z > LIFTOFF_MM` 的帧的前一帧；
      `TOUCH`   = 最后一个 `sole_min_z > LIFTOFF_MM` 的帧的后一帧。
      骨架判据 `spawn_airborne_ok` 会**核对**这两个实测帧与标称帧一致（±2 帧）。
    · ★ 段间缓动：`decel`(1−(1−t)²，慢起快收) / `accel`(t²，快起)
      / `hold`(定格) / `smooth`(smoothstep，两端导数为 0 ⟹ 接缝无痕)。
    · ★★ **帧预算**：120 帧 = 2.0 s，**等于** E01 登记的上界
      ⟹ **沿用合规**（显式声明，不是悄悄超）。

★★★ 工程件 ②：**根位移必须带在身上**（本支最大的写法改动）
    E03 的拳目标是**世界定点**（躯干不位移 ⟹ 定点合理）。E04 的骨盆全程位移 **0.4 m**
    ⟹ 若照抄世界定点，手臂会在腾空段**反向拉伸**（肩跟着骨盆飞走、拳留在原地）。
    ⟹ 本支所有拳目标都写在**根相对坐标**里：`world = base + (0, dy, dz)`
      （`dy/dz` = 当前帧的骨盆位移），接缝帧位移为 0 ⟹ 拳目标自动回到站架位。

★★★ 工程件 ③：**落地「重」的三件套**（全部可量）
    · 下沉量：`spawn_land_sink_mm` = 站架骨盆 z − 落地帧骨盆 z ∈ 区间（两端卡）
    · 定格：`spawn_impact_hitstop_ok` = 落地窗口内**逐帧姿态**最大角步 ≤ 0.01°
    · 压缩：`spawn_land_knee_deg` ≥ 下限（腿真的屈下去吸了冲击）

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python anim_spawn.py
    SKIP_RENDER=1      只跑门禁不渲图（迭代用）
    E04_TRACE=1        逐帧打印 根位移 / 脚离地高度 / 锁踝误差 / 落地读数

反向验证（§4 第 7 步，八组）：
    E04_TP_SEAM_ZERO=1   ① 首帧改零位              ⟹ `seam_in_ok`
    E04_TP_NOSINK=1      ② ★★★ 落地不下沉          ⟹ `spawn_land_sink_ok`
    E04_TP_OVERSINK=1    ③ ★ 落地过头（区间上限端）⟹ `spawn_land_sink_ok`
    E04_TP_NOLIFT=1      ④ ★ 起跳不起              ⟹ `spawn_root_motion_ok`
    E04_TP_GLUED=1       ⑤ ★ 空中段脚没离地        ⟹ `spawn_airborne_ok`
    E04_TP_NOHITSTOP=1   ⑥ ★ 落地无定格            ⟹ `spawn_impact_hitstop_ok`
    E04_TP_FOOTSWAY=1    ⑦ ★ 地面段脚滑            ⟹ `spawn_foot_lock_phased_ok`
                                          （★ 只沿 Y/Z ⟹ 侧面可见、正面不可见）
    E04_TP_LOOPBREAK=1   ⑧ ★ 末帧不闭合            ⟹ `end_matches_start_ok`
    E04_TP_FOOTASYM=1    ⑨ ★ L 脚沿 +X 平移         ⟹ 像素级 `px_spawn_feet_sym_ok`
                                          （★ 只沿 X ⟹ 正面可见、骨架级不可见）
"""

import json
import math
import os
import sys

import bpy
from mathutils import Euler, Matrix, Quaternion, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A          # noqa: E402
import anim_idle_01 as IDLE   # noqa: E402
import probe_d01_guard as PD  # noqa: E402

NAME = "Spawn"
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"
SIDES = ("L", "R")
ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")
ARM_SET = set(ARM_BONES)
ARM_LEN_UP = 0.328
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
# ★ 上游 = `Idle_01@0`。★ 本支沿用 E03 的实测结论（**没有照抄，是同一批探针**）：
#   `Idle_01@0` vs `Stun@末帧(120)`  最差位置差 **0.000258123 mm**（elem 4.77e-7）
#   `Idle_01@0` vs `Exhausted@0/末帧` / `Rage@末帧` 均为 **0.000086888 mm**（elem 1.19e-7）
#   ⟹ 四个候选代价相等（都是 float32 噪声量级），只能按语义选。
#   ★ 本支选 `Idle_01@0` 的**额外**理由（比 E03 更强）：本支是「**原地起跳**」，
#     START 与 END **两端**都必须是它 ⟹ 它与「上一支的末帧」无关，语义上只能是站架。
SEAM_ACTION = os.environ.get("E04_SEAM_ACTION", "Idle_01")
SEAM_FRAME = _env_i("E04_SEAM_FRAME", 0)

# =============================================================== 时间轴（120 帧 = 2.0 s）
TOTAL = _env_i("E04_TOTAL", 120)
START = 0
END = TOTAL
HITSTOP_N = _env_i("E04_HITSTOP", 3)          # 落地定格帧数（2~4）

# 相位标记帧（**标称值**；脚的两个相位在断言里用实测值核对，见 docstring ①）
OPEN_AT = _env_i("E04_OPEN", 8)               # 前摇第一段：双臂先**外张**离开躯干
CROUCH = _env_i("E04_CROUCH", 16)             # 起跳前摇（下沉蓄力）
TAKEOFF = _env_i("E04_TAKEOFF", 26)           # 脚离地（地面段 → 空中段 的分界）
                                              # ★ 24 → 26（本支第 11 次迭代）：蹬伸摆臂段
                                              #   CROUCH(16)→TAKEOFF 由 8 帧放宽到 10 帧，
                                              #   实测前臂世界角步峰值 27.4 → ~22°/帧。
APEX = _env_i("E04_APEX", 42)                 # 骨盆 z 峰值
TOUCH = _env_i("E04_TOUCH", 55)               # 脚触地（空中段 → 地面段 的分界）
                                              # ★ 56 → 55（本支第 14 次迭代）：鞋底实测在
                                              #   f=55 已落到 +6.86 mm（< LIFTOFF 12）⟹ 判据
                                              #   把它算作「地面帧」，但踝抬起量此时还剩 7.8 mm
                                              #   ⟹ 踝漂移 8.02 mm、鞋底 6.86 > 6 上带。
                                              #   把标称 TOUCH 对齐**实测触地帧**后，抬起量在
                                              #   第一个地面帧恰为 0 ⟹ 漂移回到 E01~E03 量级。
LAND = _env_i("E04_LAND", 60)                 # 落地冲击帧（定格起点）
HOLD = (LAND, LAND + HITSTOP_N - 1)           # [60, 62]
SETTLE = _env_i("E04_SETTLE", 78)             # 起身、展开

# 臂包络（与 E03 同构；★ `ARM_DN_DONE` 是「回 0 **完成**」帧，见 `arm_env` 说明）
ARM_UP_AT = _env_i("E04_ARM_UP", 12)
ARM_DN_AT = _env_i("E04_ARM_DN", 92)
ARM_DN_DONE = _env_i("E04_ARM_DONE", 106)

# =============================================================== 反向验证旋钮（必须先于 SPECS/KEYS）
NOSINK = _env_b("E04_TP_NOSINK")              # ② 落地不下沉
OVERSINK = _env_b("E04_TP_OVERSINK")          # ③ 落地过头
NOLIFT = _env_b("E04_TP_NOLIFT")              # ④ 起跳不起
GLUED = _env_b("E04_TP_GLUED")                # ⑤ 空中段脚没离地
SEAM_ZERO = _env_b("E04_TP_SEAM_ZERO")        # ① 首帧改零位
# ★★★ `NO_HITSTOP` **必须定义在 `KEYS` 之前**（E03 ⑤ 的实测教训：只在 `main()` 里
#   把 `set_hitstop` 关掉，姿态仍是冻结的 ⟹ 旋钮**惰性**、判据不见红）。
#   忠实仿真 = **从键表里抽掉 `hold` 行**，让 `TOUCH → SETTLE` 变成一整段，
#   落地窗口内姿态按原插值**继续走**（骨盆继续下沉 / 上升），这才是「没有定格」。
NO_HITSTOP = _env_b("E04_TP_NOHITSTOP")
FOOT_SWAY = _env_b("E04_TP_FOOTSWAY")        # ⑦ 地面段脚滑
LOOP_BREAK = _env_b("E04_TP_LOOPBREAK")      # ⑧ 末帧不闭合
# ★★ ⑨ 像素级「正面双脚对称」的反面控制（**单独一维**，见 probe_spawn_pixels.py）：
#   ⑦ FOOTSWAY 骑骨盆 ⟹ 位移只落在 **Y / Z**，而「对称」尺子量的是 **X** ⟹ 对 ⑦ **不可见**
#   （E02/E03 同一类陷阱：扰动方向必须落在**本支机位可见的那一维**）。
#   ⟹ 本支为「正面判双脚对称」单立 `E04_TP_FOOTASYM`：把 **L 脚**沿 +X 平移常量，
#     只破坏**正面**可见的对称性；对骨架级 `spawn_foot_lock_phased_ok`（量**跨帧漂移**）
#     仍是常量 ⟹ 骨架级不见红、像素级见红，两个尺子**各管一维**。
FOOT_ASYM = _env_b("E04_TP_FOOTASYM")
FOOT_ASYM_MM = _env_f("E04_FOOT_ASYM_MM", 120.0)
# ★★ ⑦ `FOOTSWAY` 的位移尺度（米）：`scale = FOOT_SWAY_MM / 55.0` 里用。
#   ★ 初版**漏定义**（只写了用法没写定义）⟹ 旋钮一开就是 `NameError` ⟹ `NO REPORT`
#     ⟹ 会被批量驱动误判成「惰性」。本支补上：默认 120 mm ⟹ scale ≈ 2.18。
FOOT_SWAY_MM = _env_f("E04_FOOT_SWAY_MM", 120.0)

# =============================================================== 落地/起跳的数值（米 / 毫米）
# ★ 全部来自 `probe_e04_baseline.py` + `_e04_conv.py` / `_e04_land.py` 的**实测**，
#   不是拍的（实测账目见日志）：
#     · 站架骨盆 z = 830.0 mm，站架膝屈 L 40.59 / R 42.96°，髋↔踝 771.0 / 764.9 mm
#     · 下沉可达（脚锁死）：dz=−100 → 膝 71.5°、dz=−200 → 92.2°、dz=−400 → 124.8°
#     · **原地起跳的物理上限 ≈ +46 mm**（dz=+60 时锁踝解发散，err 8.58 mm）
#     · 鞋底下沉（含髋后移修正）：dz=−160 + 髋后 180 mm → 鞋底 −1.59 mm（带内）
CROUCH_MM = _env_f("E04_CROUCH_MM", 130.0)    # 起跳前摇下沉
TAKEOFF_MM = _env_f("E04_TAKEOFF_MM", 40.0)   # 起跳瞬间骨盆高于站架（腿蹬直）
APEX_MM = _env_f("E04_APEX_MM", 400.0)        # 骨盆 z 峰值（根位移顶点）
TOUCH_MM = _env_f("E04_TOUCH_MM", 30.0)       # 触地瞬间骨盆低于站架
LAND_MM = _env_f("E04_LAND_MM", 175.0)        # 落地最大压缩（定格帧）
SETTLE_MM = _env_f("E04_SETTLE_MM", 55.0)     # 起身过程中仍保留的压缩
ANKLE_APEX_MM = _env_f("E04_ANKLE_APEX_MM", 550.0)   # 顶点处踝的世界抬高（收腿）

# =============================================================== 躯干规格
# ★ 量纲：全部是**相对站架的增量**（度），未列出的骨 = 站架值。
#   `loc` = (世界 dy, 世界 dz)（米）：+dy = 身后，+dz = 上。
#   `ankle` = 踝的**世界抬高**（米）—— 地面段必须恒为 0（脚钉在地上），
#             空中段 > 0（脚真的离地）。★ 这就是「分段脚锁」的唯一开关。
SPECS = {
    "STATION": {"pelvis": 0.0, "spine_01": 0.0, "spine_02": 0.0, "chest": 0.0,
                "neck": 0.0, "head": 0.0, "shoulder.L": 0.0, "shoulder.R": 0.0,
                "loc": (0.0, 0.0), "ankle": 0.0},
    # ★★★ 前摇第一段「**外张**」（本支第 4 个实测逼出来的改动）：
    #   站架的双拳停在**胸前中线**（`STATION_FIST` L=(0.145,−0.308,1.271)，x=0.145
    #   < 躯干半宽 0.238）。若直接从站架直线插值到「身后蓄力」（+Y），这条**直线弦
    #   会横切胸腔** —— 实测 f=3~7 非拇指手顶点在体内 **7 → 558** 个、最深 −81 mm；
    #   为绕开躯干，肘极向量被逼到与肩→拳轴**近平行**（`pole·axis` f=8 达 **0.981**，
    #   bulge 退化到 0.200）⟹ 肘位跳变 ⟹ 前臂世界方向**一帧翻 ~110°**。
    #   ⟹ 在 f=8 插一个「双臂先向**外侧**张开」的中间键，把整条路径推到 x ≥ 0.33
    #     （远超躯干半宽 0.238），后摆与起跳全部走**体侧外**，弦不再入体。
    "OPEN": {"pelvis": 7.0, "spine_01": 4.0, "spine_02": 4.0, "chest": 3.0,
             "neck": -1.0, "head": -2.0, "shoulder.L": 4.0, "shoulder.R": 4.0,
             "loc": (0.060, -0.055), "ankle": 0.0},
    # 起跳前摇：**沉髋 + 髋后移 + 含胸前倾 + 头略低**（反向预备，越重越要读得出来）
    "CROUCH": {"pelvis": 16.0, "spine_01": 8.0, "spine_02": 8.0, "chest": 6.0,
               "neck": -3.0, "head": -5.0, "shoulder.L": 7.0,
               "shoulder.R": 7.0, "loc": (0.130, -CROUCH_MM / 1000.0),
               "ankle": 0.0},
    # 起跳瞬间：腿蹬直 + 躯干向后张开（拔高）。骨盆高于站架（实测上限 ≈ 46 mm）
    "TAKEOFF": {"pelvis": -5.0, "spine_01": -3.0, "spine_02": -3.0,
                "chest": -3.0, "neck": -4.0, "head": -6.0,
                "shoulder.L": 11.0, "shoulder.R": 11.0,
                "loc": (-0.030, TAKEOFF_MM / 1000.0), "ankle": 0.0},
    # 顶点：躯干略前倾收腹（收腿），肩抬到最高
    "APEX": {"pelvis": 6.0, "spine_01": 4.0, "spine_02": 3.0, "chest": 2.0,
             "neck": -2.0, "head": -4.0, "shoulder.L": 8.0, "shoulder.R": 8.0,
             "loc": (-0.020, APEX_MM / 1000.0),
             "ankle": ANKLE_APEX_MM / 1000.0},
    # 触地：腿已伸出找到落点，骨盆回到站架略下，髋开始后坐
    # ★★★ 本支第 13 次迭代（实测逼出来的改动）：TOUCH 的**躯干俯仰**由
    #   (10, 5, 5, 4, −2, −3) 抬到 (14, 7, 7, 6, −3, −5)、肩 4→2。
    #   原因：`TOUCH→LAND` 的躯干俯仰差原本是 (18−10, 9−5, 9−5, 7−4, −4+2, −7+3)
    #   = (+8, +4, +4, +3, −2, −4)，六个骨段**叠加**到前臂末端 ⟹ 前臂局部 euler
    #   实测 **38.62°/帧**（`f=58`，阈值 25）—— 而 reach 只动 9 mm、骨方向只动 7~12°
    #   ⟹ 是**肘位/肘角被躯干俯仰拖出来的扭转**，不是摆臂。
    #   `_e04_seg.py` 归因：把 LAND 俯仰压成 = TOUCH（保留下沉）→ 立刻降到 23.19；
    #   把 LAND 推到 f=62（只延长 2 帧）→ 仍有 27.67 ⟹ **主因是俯仰差，不是帧长**。
    #   ⟹ 解法 = 触地瞬间身体**已经开始压**（物理上正确：触地即开始吸收），
    #     把俯仰差减半，而 **175 mm 下沉量完整保留**（「重」的核心一点没动）。
    "TOUCH": {"pelvis": 14.0, "spine_01": 7.0, "spine_02": 7.0, "chest": 6.0,
              "neck": -3.0, "head": -5.0, "shoulder.L": 2.0, "shoulder.R": 2.0,
              "loc": (0.060, -TOUCH_MM / 1000.0), "ankle": 0.0},
    # 落地冲击：**最深压缩**（本支的「重」）= 沉髋 + 髋后坐 + 含胸 + 肩沉
    "LAND": {"pelvis": 18.0, "spine_01": 9.0, "spine_02": 9.0, "chest": 7.0,
             "neck": -4.0, "head": -7.0, "shoulder.L": -2.0,
             "shoulder.R": -2.0, "loc": (0.160, -LAND_MM / 1000.0),
             "ankle": 0.0},
    # 起身：压缩减半、躯干立起来
    "SETTLE": {"pelvis": 8.0, "spine_01": 4.0, "spine_02": 4.0, "chest": 3.0,
               "neck": -2.0, "head": -3.0, "shoulder.L": 0.0,
               "shoulder.R": 0.0, "loc": (0.060, -SETTLE_MM / 1000.0),
               "ankle": 0.0},
}


def spec_of(name):
    spec = dict(SPECS[name])
    if NOSINK and name in ("TOUCH", "LAND", "SETTLE"):
        dy, _dz = spec["loc"]
        spec["loc"] = (dy, 0.0)
    if OVERSINK and name == "LAND":
        dy, _dz = spec["loc"]
        spec["loc"] = (dy, -0.450)
    if NOLIFT and name in ("TAKEOFF", "APEX", "TOUCH"):
        dy, _dz = spec["loc"]
        spec["loc"] = (dy, 0.0 if name != "TOUCH" else -TOUCH_MM / 1000.0)
    if GLUED and name in ("APEX", "TOUCH"):
        # ★★ 2026-10-04 修：⑤ 的语义 = 「**脚**没离地」。本支脚的世界高度由
        #   **两件**相加决定：① 根位移 `loc` 的 z 分量（骨盆抬 400 mm）、
        #   ② `ankle`（踝随根抬起）。旧版**只清 ②** ⟹ 骨盆仍在 400 mm 高处，
        #   腿长不变 ⟹ `leg_ik` 把踝留在「髋下方一个腿长」处 ≈ **430 mm 高空**
        #   ⟹ 脚**照样离地**（实测像素底行仍上抬 **124 px**，超过 60 px 阈值
        #   ⟹ 反面 ⑤ 失效，`px_spawn_airborne_can_fail_ok` 假红）。
        #   ★ 旁证：④ `NOLIFT`（清 ① 保留 ②）的 `spawn_airborne_ok` **仍然是绿**
        #   —— 正好从另一侧证明两件各自独立有效。⟹ 必须**同时清 ① 和 ②**。
        #   这是**修正一个几何上不成立的对照**（去掉一个不可能的姿态），
        #   不是放宽阈值。
        dy, _dz = spec["loc"]
        spec["loc"] = (dy, 0.0)
        spec["ankle"] = 0.0
    return spec


# =============================================================== 关键帧表
#   (帧, 进入本键所用的缓动, 躯干规格名, 拳目标名)
#   ★ 缓动写在**被驶向的那个键**上（与 E03 的 `_segment` 口径一致）。
KEYS = [
    (START, None, "STATION", "STATION"),
    (OPEN_AT, "smooth", "OPEN", "OPEN"),
    (CROUCH, "decel", "CROUCH", "WIND"),
    (TAKEOFF, "smooth", "TAKEOFF", "SWING"),
    (APEX, "decel", "APEX", "UP"),
    (TOUCH, "smooth", "TOUCH", "OUT"),
    # ★ 本支第 12 次迭代：落地压缩段（TOUCH→LAND，4 帧）的缓动由 `decel` 改 `smooth`。
    #   `decel` 的导数峰值 2.0（在触地那一帧）把前臂的**最小旋转扭转**推到
    #   **26.58°/帧**（阈值 25，`f=57`：`fLoc` 17.58 而骨**方向**只动 7~12° ⟹ 是扭转不是摆动）。
    #   改 `smooth`（峰值 1.5）后 ≈ 19.9°/帧。★ 落地「重」由**下沉量 175 mm + 定格 3 帧**承担，
    #   不靠这 4 帧的初速度。
    (LAND, "smooth", "LAND", "OUT"),
]
if not NO_HITSTOP:
    KEYS.append((HOLD[1], "hold", "LAND", "OUT"))
KEYS += [
    (SETTLE, "decel", "SETTLE", "OUT2"),
    (END, "smooth", "STATION", "STATION"),
]

# =============================================================== 拳目标（**根相对**，米）
# ★★ 全部写在根相对坐标里（世界 = 本值 + 当前帧骨盆位移 (0, dy, dz)）——
#   本支骨盆全程位移 0.4 m，用世界定点会让手臂在腾空段被反向拉伸（见 docstring ②）。
# ★★★ **拳轨迹必须全程在躯干之外**（本支第 4 个实测逼出来的改动，见 SPECS["OPEN"]）：
#   躯干包围盒 x ∈ [−0.233, 0.238]、y ∈ [−0.217, 0.133]、z ∈ [0.826, 1.461]。
#   站架拳心 (0.145, −0.308, 1.271) 在**胸前中线** ⟹ 去「身后」的直线弦必然穿胸。
#   ⟹ 逐段设计（每段的 x 在被 y 进入躯干带的时刻已 > 0.27）：
#     STATION →(前) OPEN →(外后) WIND →(外前上) SWING →(上前) UP →(外下) OUT → 回站架。
#   · 取向：起跳前摇 = 双臂先**外张下沉**、再**后摆蓄力**；起跳**前上摆**；
#     顶点**上举**；触地**外展张开**（力量感的外扩）；起身收回站架。
FIST_OPEN = {"L": Vector((0.330, -0.250, 1.100)),
             "R": Vector((-0.330, -0.250, 1.100))}
FIST_WIND = {"L": Vector((0.360, 0.060, 0.960)),
             "R": Vector((-0.360, 0.060, 0.960))}
FIST_SWING = {"L": Vector((0.300, -0.300, 1.320)),
              "R": Vector((-0.300, -0.300, 1.320))}
# ★ 顶点上举位 / 触地外展位：**两处的「肩→拳」距离刻意配平**（本支第 8 次迭代）。
#   旧值 UP=(0.270,−0.120,1.700)（reach 0.30）对 OUT=(0.430,0.020,1.060)（reach 0.435）
#   ⟹ 14 帧内肘要伸 0.135 m ⟹ 实测前臂 **57.9°/帧**、手指矩阵步 **40.8°/帧**（阈值 25）。
#   配平后 Δreach = 0.023 ⟹ 肘几乎不伸缩，前臂角速度由「整臂摆动」主导。
FIST_UP = {"L": Vector((0.290, -0.220, 1.660)),
           "R": Vector((-0.290, -0.220, 1.660))}
FIST_OUT = {"L": Vector((0.430, -0.020, 1.180)),
            "R": Vector((-0.430, -0.020, 1.180))}
FIST_OUT2 = {"L": Vector((0.330, -0.170, 1.240)),
             "R": Vector((-0.330, -0.170, 1.240))}
FIST_TABLE = {"OPEN": FIST_OPEN, "WIND": FIST_WIND, "SWING": FIST_SWING,
              "UP": FIST_UP, "OUT": FIST_OUT, "OUT2": FIST_OUT2}
ELBOW_DIR = {"L": Vector((0.42, 1.00, -0.22)),
             "R": Vector((-0.42, 1.00, -0.22))}

# ★★ 拳**面**朝向混合：本支 = **0.0**（拳沿前臂）。
#   理由（与 E03 相反，是**设计**不是偷懒）：E03 是「捶胸」——必须用指节面砸在
#   胸面上，所以要把 `y_dir` 反折到 −胸法线。E04 是腾空摆臂 / 落地张臂，
#   拳的朝向就是「顺着前臂伸出去」，**不需要**反折 ⟹ `blend = 0` 时
#   `y_dir = along`（前臂方向）、`hand_x_hint` 用恒定世界 ±X（永不退化）。
#   ★ 好处：手骨的 `ry` 全程不穿 ±90° 奇异带（E03 花了 3 版才治好的病，本支不患病）。
FIST_FACE_BLEND = 0.0
# ★ 拳心保护下限（`push_out` 用）：站架拳心离躯干面 L +100.69 / R +66.63 mm
#   ⟹ 25 mm 对站架是 **no-op**（接缝不受影响），只兜住摆臂途中擦过躯干的那几帧。
FIST_MIN_CLEAR_MM = _env_f("E04_FIST_CLEAR", 25.0)

# =============================================================== 阈值
# ★ 全部由实测导出（见日志）；铁律：不许为了变绿而放宽。
CROUCH_RANGE = (_env_f("E04_CROUCH_LO", 95.0), _env_f("E04_CROUCH_HI", 215.0))
LAND_RANGE = (_env_f("E04_LAND_LO", 120.0), _env_f("E04_LAND_HI", 260.0))
APEX_RANGE = (_env_f("E04_APEX_LO", 300.0), _env_f("E04_APEX_HI", 520.0))
CROUCH_KNEE_MIN = _env_f("E04_CROUCH_KNEE", 60.0)
LAND_KNEE_MIN = _env_f("E04_LAND_KNEE", 70.0)
LIFTOFF_MM = _env_f("E04_LIFTOFF", 12.0)          # 判「脚离地」的鞋底高度阈值
AIRBORNE_PEAK_MIN_MM = _env_f("E04_AIR_PEAK", 300.0)   # 真的跳起来了（鞋底峰值）
AIRBORNE_SPAN_MIN = _env_i("E04_AIR_SPAN", 20)     # 空中段帧数下限
FOOT_LOCK_MM = _env_f("E04_FOOT_LOCK", 0.5)
TOE_LOCK_MM = _env_f("E04_TOE_LOCK", 0.5)
SOLE_BAND = (-2.0, 6.0)
NO_SNAP_END_DEG = _env_f("E04_SNAP_END", 6.0)
SEAM_POS_MAX_MM = _env_f("E04_SEAM_POS", 0.01)
SEAM_DIR_MAX_DEG = _env_f("E04_SEAM_DIR", 0.05)
CLIP_MAX_MM = _env_f("E04_CLIP_MAX", 0.0)
REACH_MAX_RATIO = 0.995
MATRIX_STEP_MAX_DEG = _env_f("E04_MATSTEP", 25.0)
TAIL_SETTLE_N = _env_i("E04_TAIL_N", 12)
HAND_PIERCE_MM = _env_f("E04_HAND_PIERCE", 10.0)
# 手骨滚转基准的**退化余量**下限（E03 v009 的教训：基准落在视轴上会静默翻帧）。
HAND_X_HINT_MIN_MARGIN = _env_f("E04_HINT_MARGIN", 0.55)

# 出图/像素探针共用的**逐帧集合**（主渲、反面重渲、像素探针三者必须逐帧相同）
STEM_FRAMES = sorted(set([0, 16, 24, 32, 42, 50, 56, 58, 60, 62, 70, 78,
                          96, 120]))

# =============================================================== 取景（★ 本支自立，不许照抄）
# ★★ 取景跨度的由来（**A12 `Launch_Hit` 的教训**：人物升到 2812 mm，标准视图把头脚
#   一起切掉）：本支骨盆从 830 − 175 = **655 mm** 升到 830 + 400 = **1230 mm**，
#   拳在顶点处到 **1.72 + 0.40 = 2.12 m**，头顶再往上 ≈ 2.25 m。
#   ⟹ 纵向必须覆盖 −0.30 ~ 2.70 m ⟹ 中心 z = 1.20、正交高 3.00 m。
#   ★ 侧视判「下沉 / 腾空」（矢状面 YZ）、正面判「双脚对称 / 没串门（X）」。
VIEW_E04_SIDE = ("side", (4.2, -0.05, 1.20), (0.0, -0.05, 1.20), 3.00,
                 (780, 1100))
VIEW_E04_FRONT = ("front", (0.0, -5.6, 1.20), (0.0, 0.0, 1.20), 3.00,
                  (780, 1100))

TRACE = _env_b("E04_TRACE")
SLEEP_TRACE = _env_b("E04_TRACE_SOLE")
_BLEND_TRACE = _env_b("E04_TRACE_BLEND")

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
PELVIS0 = None
# ★ 手骨滚转基准的**最小投影余量**（`orient_hand` 逐帧写入；`boot()` 清零）。
MIN_HINT_MARGIN = 1.0
# ★★★ `LAST_HAND_X`：**滚转基准的平行移动（parallel transport）**。
#   旧写法用恒定世界 ±X 作基准，实测在摆臂回程（f≈95~100）`y_dir` 扫到 ±X 附近
#   ⟹ 投影退化（余量 **0.308** < 0.55）⟹ 滚转由浮点噪声决定 ⟹ 手骨真转
#   **173.8°/帧**、拳掌扎进躯干（f=93 R 手 188 顶点在体内、最深 −46 mm）。
#   改用**上一帧解出的 hand 局部 x 轴**作基准：它天然 ⊥ 上一帧 `y_dir`，
#   且 `y_dir` 逐帧只走 ≤ 25° ⟹ 投影余量恒 ≈ cos(25°) ≈ 0.9，永不退化。
#   这正是「平行移动」：滚转沿骨轴零扭转地跟着走，接缝处再由 `env→0` 收敛到站架。
LAST_HAND_X = {}
# ★★★ hitstop 的**时间冻结**缓存：窗口内逐帧**复用定格帧的姿态**。
#   为什么不能只靠 `hold` 缓动 + `A.set_hitstop`（E03 的写法）：
#   E03 的姿态函数在窗口内是**严格常数**（a/b 两个键的 spec 与拳目标全同），
#   本支不是 —— `seat_arm` 的膝极向量 / 手滚转基准带**一帧滞后**（连续性口径），
#   实测窗口内逐帧角步 **2.064° / 0.650°**（阈值 0.01°）⟹ 定格不成立。
#   hitstop 的定义就是「时间停住」，所以这里**显式冻结帧号**：窗口内直接复用
#   `HOLD[0]` 那一刻算出的姿态（不再重解 IK）。`NO_HITSTOP` 打开时不冻结。
FREEZE = {"pose": None}


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
        # ★★★ 本支第 10 次迭代：CROUCH→TAKEOFF（起跳蹬伸摆臂）用。
        #   `smoothstep` 的导数是 6t(1−t)，**峰值 1.5 倍平均速度** —— 实测把
        #   8 帧内的前臂世界角步推到 **27.4°/帧**（阈值 25）。起跳蹬伸本来就是
        #   等加速度的爆发段，用 `linear`（峰值 = 平均）最贴物理，且把峰值降 1/3。
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
            out[key] = a[key] + (b[key] - a[key]) * g
    return out


def arm_env(frame):
    """臂包络：`env` 只在 `(ARM_UP_AT, ARM_DN_AT)` 区间内为 1，两端分别归 0。

    ★ 为什么需要它（照 E03 v010 的实测结论，本支同样适用）：
      `spawn_pose` 用 `pose = station + (ik − station) * env` 把 IK 解与站架解混合。
      IK 解的**绝对手朝向**（`orient_hand` 由 `y_dir`/`x_hint` 决定）与 `Idle_01`
      的松拳朝向差很多 ⟹ 若 `env` 恒为 1，接缝帧（f=0 / f=120）就不等于站架 ⟹
      `seam_in_ok` / `end_matches_start_ok` 必红。`env→0` 时 `seat_arm` 会把
      IK 解的肘极向量 / 拳轴 / 滚转基准**逐位收敛到站架实测值** ⟹ 两端重合。
    ★ `ARM_DN_DONE` 是「回 0 **完成**」帧而不是「开始回」帧：`no_snap_stop_ok`
      判的是**末尾 12 帧**（f ≥ 108）逐帧角步 ≤ 6°。把「回 0」提前到 f=106，
      尾段 12 帧的臂**已经完全等于站架** ⟹ 姿态静止，判据自然满足。
    """
    if frame <= ARM_UP_AT:
        return _smoothstep(frame / float(max(1, ARM_UP_AT)))
    if frame >= ARM_DN_AT:
        span = float(max(1, ARM_DN_DONE - ARM_DN_AT))
        return _smoothstep((ARM_DN_DONE - frame) / span)
    return 1.0


def seam_canonicalize(keyframes):
    """把整条欧拉曲线按**轴的 360° 整数倍**整体平移，使**末帧 == 首帧**。

    ★ 为什么需要它（E03 实测）：`compat_euler` 逐帧挑「离上一帧最近」的等价表示，
      会沿路**累积** 360° 的整数倍 —— 实测 `hand.L` 末帧 euler = −357.5 而首帧
      = +2.5（**同一个姿态**，矩阵逐元素差 2.8e-07）⟹ `loop_seamless` 按 euler 比
      会报 `loop_angle_deg = 360.0`（**假红**）。平移是零副作用的：XYZ 欧拉里
      单轴加整圈给出**同一个旋转矩阵**，逐帧姿态、相邻差值、F-Curve 形状全不变。
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

    ★ 候选顺序**必须把「原始表示」排在第 0 位**（E03 v011 的实测教训：整体平移
      360° 是代价并列的解，若第 0 位是 k=−1，DP 会选「全时间轴 −360°」的分支，
      矩阵与逐帧步长都不变，但按欧拉值算的判据会凭空多出 ±360 ⟹ 噪声红项）。
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
    """欧拉表示兼容化（C14 / D01 / E03 踩过的同一个万向节锁坑）。

    `A.aim_bone` 每帧独立反解欧拉，返回的是「规范区间」里的**某一个**等价表示。
    同一段平滑旋转的相邻两帧可能落到两组数值差 90° 以上的等价欧拉上 ⟹
    `no_teleport`（按 euler 判）**误报瞬移**，而且 **F-Curve 会真的插出绕圈的怪姿态**。
    ★★★ 做法：**自己穷举等价表示 + min-max 瓶颈 DP**（`best[i][j] =
      min_k max(best[i−1][k], step(k→j))`）求「最小化最大单轴步」的全局最优路径。
      E03 v011 实测：贪心给出的 `hand.L` f=22→23 是 36.886°，而可达最小是 20.92°
      —— 门禁量的是**整条曲线的最大值**，所以必须全局最优，不能逐帧贪心。
    ★ 这一步**不改变任何姿态**（等价表示 ⟹ 同一旋转矩阵），只改变键上的数字。
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
        # ★★★ **两端钉死在「原始表示」上**（本支第 5 个实测逼出来的改动）。
        #   为什么必须钉：DP 只最小化「整条曲线的最大单轴步」，**不管首末是否同支**。
        #   实测本支（原姿态 f=0 与 f=120 逐位相同）经 DP 后，`forearm.L` 末帧
        #   rz 比首帧**多 360**、`hand.R` 末帧落到 **(rx+180, 180−ry, rz+180)**
        #   的**翻转支**（同一个旋转、另一组数字）⟹ `loop_angle_deg = 360.0`、
        #   `loop_seamless` **假红**。
        #   ⟹ 两端强制取 `fams[i][0]`（即 `_euler_family` 排在第 0 位的原表示）。
        #     原姿态 f=0 == f=120（`spec` 两端都是 STATION、`arm_env` 两端都是 0）
        #     ⟹ 钉两端即 **首末逐位相同**，`loop_seamless` 不再是表示问题。
        chosen[name][0] = fams[0][0]
        chosen[name][-1] = fams[-1][0]

    out = []
    for i, (frame, pose) in enumerate(keyframes):
        new_pose = dict(pose)
        for name, picks in chosen.items():
            new_pose[name] = picks[i]
        out.append((frame, new_pose))
    return out


# =============================================================== 脚锁
def lock_feet(arm, pose, want, iters=8, damp=0.85):
    """把双踝**闭环**钉在 `want`（世界坐标 dict）上，就地改 `pose`。

    ★ 照抄 E01 / E02 / E03 的结构（planar IK + `thigh.rz` 配平 x）。
    ★★ 本支与前三支的**唯一区别在 `want`**：地面段 `want` = 站架踝（脚钉死），
      空中段 `want` = 站架踝 + (0, 0, ankle_lift)（脚跟着骨盆一起飞）。
      ⟹ 同一个闭环、同一套收敛，只是**目标在动** —— 这正是「分段脚锁」的实现。
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


# =============================================================== 躯干几何查询（拳保护用）
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


def push_out(point, min_gap_mm):
    """把拳目标**顶出**胸腔（沿胸面外法线），只在该点比下限更深时才动它。

    ★ 作用：拳目标在**时间上**是线性插值的，站架拳位 ↔ 蓄力/上举位之间的
      直线弦可能切进躯干。实测站架拳心离躯干面 +66.63 mm（R）/ +100.69 mm（L）
      ⟹ 本支的 25 mm 下限对站架是 **no-op**（接缝不受影响）。
    """
    gap, surf, nrm = torso_query(point)
    if gap >= min_gap_mm:
        return Vector(point)
    return surf + nrm * (min_gap_mm / 1000.0)


# ---------------------------------------------------------------- 手 vs 躯干（真·内外判定）
# ★★★ 「带符号距离」在**凹几何**上会骗人（最近面可能是侧壁或下摆内壁）。
#   `_e03_yard.py` 实测：`Suit_Torso` 是**水密的**，但射线擦边会让**单方向奇偶**
#   产生假阳性；真内部恒 **13/13 票**、噪声恒 ≤ 2 票 ⟹ 权威口径 = **13 方向多数表决**。
INSIDE_RAYS = []
for _j in range(13):
    _a = 2.0 * math.pi * _j / 13.0
    _z = 1.0 - 2.0 * (_j + 0.5) / 13.0
    _r = math.sqrt(max(0.0, 1.0 - _z * _z))
    INSIDE_RAYS.append(Vector((math.cos(_a) * _r, math.sin(_a) * _r,
                               _z)).normalized())
INSIDE_VOTES_MIN = _env_i("E04_INSIDE_VOTES", 7)
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


def hand_mesh_stats(side, tree=None, step=3):
    """该侧手网格的几何读数（**排除拇指**的口径是判据，拇指单独计数并登记）。

    ★★★ 为什么必须排除拇指（E03 实测，「登记而不掩盖」）：`Idle_01` 站架里
      R 手就有 **4 个非拇指顶点**在躯干体内（`Hand_Palm_R`，gap −0.54 / −1.17 /
      −4.31 / −4.50 mm，离拳心 88~106 mm = **腕侧掌肉**），R 拇指更有 **95 个**
      （最深 −34.19 mm）。这是 **A01 的预存几何缺陷**，本支 f=0 / f=120 必须
      **逐位等于它**（`seam_in_ok` / `end_matches_start_ok` 两条 1e-6 级断言钉死）
      ⟹ 「0 个顶点」这个口径**与接缝约束在数学上不相容**。判据因此用**差分**。
    """
    tree = tree if tree is not None else torso_bvh()
    pts = hand_mesh_points(side, step=step)
    inside, inside_nothumb, thumb = 0, 0, 0
    deepest, deepest_nothumb = None, None
    for point, name in pts:
        is_thumb = name.startswith("Thumb_")
        gap = signed_to_torso(point)
        if deepest is None or gap < deepest:
            deepest = gap
        if not is_thumb and (deepest_nothumb is None or gap < deepest_nothumb):
            deepest_nothumb = gap
        if inside_torso(point, tree):
            inside += 1
            if is_thumb:
                thumb += 1
            else:
                inside_nothumb += 1
    return {"inside": inside, "inside_nothumb": inside_nothumb,
            "thumb": thumb, "n": len(pts),
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


def orient_hand(arm, side, y_dir, x_hint):
    """用**显式正交基**摆 `hand.<side>`：`local_y` = `y_dir`，`local_x` 尽量贴 `x_hint`。

    `local_z = local_x × local_y`（rest 实测的右手系约定）。
    ★ 滚转基准用**恒定世界 ±X**（`thumb_out`）：E03 v009 对全时间轴 194 条 `y_dir`
      实测各候选基准的 `min|投影|` —— ±X **0.701**（最安全）＞ 上/下 0.173 ＞ 前/后
      0.091 ＞ 胸腔法线 **0.000**（恒正交 = 最坏）。本支 `y_dir`（前臂方向）全程
      扫过 YZ 平面，任何 YZ 内基准都会退化 ⟹ 只有带 X 分量的基准安全。
      ★ 该前提**必须有判据盯着**：见 `spawn_x_hint_margin_ok`。
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
LAST_ELBOW = {}


def seat_arm(arm, pose, targets, env=1.0):
    """把臂解到拳心目标上。

    ★ 骨架与 E03 同构（穷举三角公式两骨 IK + 肘连续性 + 包络收敛），差别有三处，
      全部是**实测逼出来的**（见下）：
      ① 拳面朝向 `blend` **恒为 0**（本支不做腕部反折）⟹ `y_dir = along`（前臂方向），
         不做测地线混合、不碰腕部 `ry` 奇异带；
      ② 删掉了「胸面法线 / 旋前不动点迭代」那一整套（那是捶胸专用）；
      ③ ★★★ **肘极向量改为确定性**（不再用上一帧的肘）：
         旧写法 `pole = 上一帧肘 − 肩` 会**自增强地往内漂** —— 实测摆臂回程
         （f=78→96）L 肘 x 从 **+0.103 一路漂到 −0.078**（**越过中线**），
         手臂折成「上臂横过胸前、前臂再拐回外侧」的鸡翅构型 ⟹ 前臂方向在
         f=96~100 四帧内转了 ~90°，是本支 50~78°/帧 异常角步与穿模的根因。
         新写法用**解剖学极向量** `ELBOW_POLE[side]`（外 + 后 = 肘朝身体外后方），
         它对 `axis` 全程不退化（实测最大 |cos| = 0.65），且**无记忆** ——
         这一条同时让 hitstop 的定格在数学上成立（姿态函数不再有路径依赖）。
    ★ `env` == `arm_env(frame)`：`env→0` 时 IK 解的**三个自由度**（肘极向量、拳轴、
      滚转基准）逐位收敛到**站架实测值** ⟹ 包络两端重合，接缝帧逐位等于站架。
    """
    A.apply_pose(arm, pose)
    for side in SIDES:
        up, fo, hd = ("upperarm." + side, "forearm." + side, "hand." + side)
        shoulder = Vector(A.bone_world(arm, up, "head"))
        core = Vector(targets[side])
        # ★ 拳轴初值：**肩→拳心**（无滞后）。旧写法用「上一帧肘 → 拳心」，
        #   带一帧滞后 ⟹ hitstop 窗口内逐帧姿态不可能恒定。
        along = core - shoulder
        along = (along.normalized() if along.length > 1e-6
                 else Vector((0.0, 0.0, -1.0)))
        y_dir = along
        if env < 1.0:
            y_dir = _slerp_dir(STATION_HAND_Y[side], y_dir, env)
        target = core - y_dir * HAND_LEN
        delta = target - shoulder
        limit = (ARM_LEN_UP + ARM_LEN_LO) * 0.9995
        distance = max(1e-4, min(delta.length, limit))
        axis = (delta.normalized() if delta.length > 1e-9
                else Vector((0.0, 0.0, -1.0)))
        # ---- 肘极向量：确定性（无记忆）--------------------------------------
        pole = Vector(ELBOW_POLE[side])
        if env < 1.0:
            pole = _slerp_dir(STATION_POLE_DIR[side], pole, env)
        bulge = pole - axis * pole.dot(axis)
        if bulge.length < 0.05:
            bulge = Vector((0.0, 1.0, 0.0)) - axis * axis.y
            if bulge.length < 0.05:
                bulge = Vector((0.0, 0.0, 1.0)) - axis * axis.z
        bulge.normalize()
        cos_sh = max(-1.0, min(1.0, (ARM_LEN_UP ** 2 + distance ** 2
                                     - ARM_LEN_LO ** 2)
                               / (2.0 * ARM_LEN_UP * distance)))
        sin_sh = math.sqrt(max(0.0, 1.0 - cos_sh * cos_sh))
        elbow = shoulder + (axis * cos_sh + bulge * sin_sh) * ARM_LEN_UP
        # ---- 用**当前肘**重定拳轴（收紧腕目标），去掉最后一处滞后 -----------
        fore = target - elbow
        if fore.length > 1e-6:
            y_dir = fore.normalized()
            if env < 1.0:
                y_dir = _slerp_dir(STATION_HAND_Y[side], y_dir, env)
            target = core - y_dir * HAND_LEN
        LAST_ELBOW[side] = elbow.copy()
        pose[up] = A.aim_bone(arm, up, elbow - shoulder)
        pose[fo] = A.aim_bone(arm, fo, target - elbow)
        # ---- 滚转基准：**前臂骨自身的局部 x 轴**（母链自然框架）--------------
        # ★★★ 第 7 次迭代定案（三个候选全部实测否决后）：
        #   ① 恒定世界 ±X：整段扫程最小余量只有 **0.527**（< 0.55 阈值）——不够安全；
        #   ② 恒定站架基准 `STATION_HAND_X`：f=21 余量 **0.0965** ⟹ 真翻 166.8°/帧；
        #   ③ 上一帧 hand x 的**平行移动**：余量 0.87（够）但**沿路累积扭转**，
        #      到 f=90 手滚转与站架差 **125°** ⟹ 包络回程必然**穿过欧拉 XYZ 奇异集
        #      （ry≈±90）** ⟹ 无论选哪个等价族，逐帧 euler 必跳 **90.4°**
        #      —— 这是**坐标奇异**（跳变量与速度无关），线性插值也救不了。
        #   ⟹ 正解：基准取**前臂骨自己的局部 x 轴**。`aim_bone` 给前臂的是
        #     「相对母链的最小旋转」（无扭转）⟹ 它天然 ⊥ 前臂方向（余量恒 ≈ 1.0，
        #     实测见 `spawn_x_hint_margin`），且**不累积**（是当前姿态的纯函数）
        #     ⟹ 手滚转不再漂移，包络回程不进奇异集。
        hint = arm.pose.bones["forearm." + side].matrix.to_3x3().col[0]
        hint = Vector(hint).normalized()
        LAST_HAND_X[side] = orient_hand(arm, side, y_dir, hint)
        LAST_FOREARM_TWIST[side] = 0.0
        pose[hd] = tuple(math.degrees(v)
                         for v in arm.pose.bones[hd].rotation_euler)
    return pose


# =============================================================== 拳目标
def resolve_fist(name, side):
    if name == "STATION":
        return Vector(STATION_FIST[side])
    return Vector(FIST_TABLE[name][side])


def fist_targets(arm, frame, root_off):
    """拳目标 = **绕肩的球面插值**（方向 slerp + 半径缓动）。

    ★★★ 本支第 9 次迭代（实测逼出来的改动，见 `_e04_f21.py`）：
      旧写法是**世界直线 lerp**（`va.lerp(vb, g)`）。当两端的**方向差很大**时，
      这条弦会**贴近肩关节** —— 实测 CROUCH(16)→TAKEOFF(24) 段：
      拳从身后下方 (0.360, 0.190, 0.830) 直线去前上方 (0.300, −0.330, 1.360)，
      弦中点离肩只剩 **0.223 m**（全臂长 0.65 m）⟹ 肘被折到 ~100° 再迅速弹出
      ⟹ 前臂世界方向 **32.6°/帧**、手指矩阵步 **39.6°/帧**（阈值 25，`f=21`）。
      ⟹ 改成**绕肩球面插值**：方向走测地线、半径按同一缓动从 0.476 单调到 0.360，
        肘不再「折进去再弹出来」，前臂/手骨角步随之落到阈值内。
    ★ 半径用**当前帧的肩**（`bone_world`）—— 调用点已 `apply_pose`，肩是确定的。
    """
    index, t, kind = _segment(frame)
    ga = _ease(kind, t)
    a_name = KEYS[index][3]
    b_name = KEYS[index + 1][3]
    out = {}
    for side in SIDES:
        shoulder = Vector(A.bone_world(arm, "upperarm." + side, "head"))
        va = resolve_fist(a_name, side) + root_off - shoulder
        vb = resolve_fist(b_name, side) + root_off - shoulder
        ra, rb = va.length, vb.length
        if ra < 1e-6:
            dirv = vb.normalized()
        elif rb < 1e-6:
            dirv = va.normalized()
        else:
            dirv = _slerp_dir(va.normalized(), vb.normalized(), ga)
        point = shoulder + dirv * (ra + (rb - ra) * ga)
        point = push_out(point, FIST_MIN_CLEAR_MM)
        out[side] = point
    return out


# =============================================================== 姿态装配
def _nearest_family(angles, ref):
    """在 XYZ 欧拉的 54 个**严格等价表示**里，取「相对 `ref` 分量最大差最小」的那个。

    ★ 用途：包络混合前，先把 IK 解**搬到站架解所在的那一支**，再线性插值。
    """
    best, best_cost = None, None
    for cand in _euler_family(angles):
        cost = max(abs(c - r) for c, r in zip(cand, ref))
        if best_cost is None or cost < best_cost:
            best, best_cost = cand, cost
    return best


def _blend_local(station, ikpt, env):
    """臂的包络混合：**最近等价族 + 欧拉线性插值**（★ 不是四元数测地线）。

    ★★★ 为什么最终换回欧拉线性（本支第 6 个「实测逼出来的改法」，绕了一圈）：
      ① v3 之前用**裸欧拉线性**⟹ 失败：IK 欧拉可能停在距站架**几百上千度**的等价
         分支上，几百度要在 14 帧里相消 ⟹ 实测 158 / 173.8°/帧。
      ② v4 改用**四元数测地线 slerp**⟹ 修好了 ①，但**引入了新病**：本支的摆臂
         让手骨的滚转与站架差到 **121°**，测地线在 f=95~96 **穿过欧拉 XYZ 的奇异集
         （ry ≈ −90°）** ⟹ 无论选哪个等价族，逐帧 euler 都必然跳 **90.37°**
         （同时刻矩阵口径只有 <13°/帧 ⟹ 纯表示病，`no_teleport` **假红**）。
         这是**坐标奇异**：跳变量与速度无关，把回程拉多长都在那一帧跳。
      ③ 正解 = ① 的**病根**先治好，再回到线性：blend 之前先用 `_nearest_family`
         把 IK 欧拉**搬到站架的支**（消掉几百度的支距）⟹ 线性插值的两端都很近，
         路径在欧拉空间是**直线**，`ry` 单调穿过 −90° 而 `rx/rz` 只走十几度
         ⟹ euler 逐帧步 ≈ 1~9°，**且不触发坐标奇异**（直线不换支）。
      ★ 两端仍然**逐位精确**：`env=0` 取站架、`env=1` 取 `_nearest_family` 结果
        （与 IK 同一旋转，只是数字换了支）⟹ 接缝的 1e-6 级约束不受影响。
    """
    out = {}
    for name in ARM_BONES:
        a = tuple(station.get(name, (0.0, 0.0, 0.0)))
        b = _nearest_family(tuple(ikpt.get(name, (0.0, 0.0, 0.0))), a)
        if _BLEND_TRACE:
            print("E04_BLEND %-12s env=%.3f span=%.1f"
                  % (name, env, max(abs(y - x) for x, y in zip(a, b))))
        out[name] = tuple(x + (y - x) * max(0.0, min(1.0, env))
                          for x, y in zip(a, b))
    return out


def spawn_pose(arm, frame):  # noqa: C901
    # ---- ★★★ hitstop 的**时间冻结**：窗口内复用定格帧姿态，不再重解 ----------
    #   见 `FREEZE` 的说明（E03 靠「姿态函数在窗口内是常数」，本支不是）。
    if (not NO_HITSTOP) and HOLD[0] <= frame <= HOLD[1] \
            and FREEZE["pose"] is not None:
        frozen = dict(FREEZE["pose"])
        A.apply_pose(arm, frozen)
        return frozen
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

    # ---- 腿：**分段脚锁**（地面段钉站架 / 空中段随根抬起）-------------------
    root_off = Vector((0.0, dy, dz))
    ankle_lift = spec["ankle"]
    want = {s: Vector(ANCHOR[s]) + Vector((0.0, 0.0, ankle_lift)) for s in SIDES}
    if FOOT_SWAY:
        # ⑦ 地面段脚滑：**脚不再锁世界，改骑在当前骨盆上**（躯干一动脚就跟着动）。
        #   ★ 为什么不是「恒定偏移」（E03 v012 实测的**惰性旋钮**教训）：本支像素尺子
        #     量的是**带内跨帧漂移**；恒定偏移在任何帧都相同 ⟹ 漂移恒为 0 ⟹ 旋钮惰性。
        #     忠实仿真必须让脚的目标位置**依赖当前躯干姿态**：骑骨盆后，蓄力帧与
        #     落地帧的骨盆不同 ⟹ 脚的位置不同 ⟹ 漂移可见（且 f=0 站架不受影响）。
        A.apply_pose(arm, pose)
        delta = Vector(A.bone_world(arm, "pelvis", "head")) - PELVIS0
        scale = FOOT_SWAY_MM / 55.0
        for s in SIDES:
            want[s] = want[s] + delta * scale
    if FOOT_ASYM and frame not in (START, TOTAL):
        # ⑨ 正面「双脚对称」的反面控制：只把 **L 脚**沿 +X（角色左）平移常量。
        #   ★ 常量 ⟹ 跨帧漂移 = 0 ⟹ 骨架级 `spawn_foot_lock_phased_ok` **不见红**；
        #     只有**正面**像素尺子（量左右镜像）能看见 ⟹ 两个尺子各管一维。
        #   ★ 排除首末帧（f0 / f120 = 站架）⟹ **不破坏接缝**（`seam_in_ok` /
        #     `end_matches_start_ok` 保持绿）⟹ 这一维**只**由正面对称尺子把守。
        want["L"] = want["L"] + Vector((FOOT_ASYM_MM / 1000.0, 0.0, 0.0))
    lock_err = lock_feet(arm, pose, want)

    # ---- 臂：对**当前帧的拳目标**重解，再按 `arm_env` 与站架臂混合 -------------
    env = arm_env(frame)
    A.apply_pose(arm, pose)
    ik_pose = dict(pose)
    seat_arm(arm, ik_pose, fist_targets(arm, frame, root_off), env)
    # ★ **四元数 slerp**（不是欧拉线性插值）—— 见 `_blend_local` 说明。
    blended = _blend_local(pose, ik_pose, env)
    for name in ARM_BONES:
        pose[name] = blended[name]

    if LOOP_BREAK and frame == TOTAL:
        rx, ry, rz = pose["chest"]
        pose["chest"] = (rx + 4.0, ry, rz + 4.0)

    # ★★★ hitstop：**把定格帧的姿态存下来**，窗口内的后续帧直接复用（见 `FREEZE`）。
    if (not NO_HITSTOP) and frame == HOLD[0]:
        FREEZE["pose"] = dict(pose)

    if TRACE:
        A.apply_pose(arm, pose)
        low = A.foot_lowest_by_side()
        soles = {s: round(low[s][2] * 1000.0, 1) for s in SIDES
                 if low[s] is not None}
        print("E04_TRACE f=%3d root_dz=%+7.1f ankle=%+7.1f sole=%s lock=%.4f "
              "env=%.3f"
              % (frame, dz * 1000.0, ankle_lift * 1000.0, soles, lock_err, env))
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
def spawn_assertions(arm, action, samples, meshes):  # noqa: C901
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

    # ---- ① ★★★ 鞋底轨迹（逐帧，权威 = 鞋对象）与「脚离地」的实测分界 ------
    sole = {}
    for frame in range(START, END + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        low = A.foot_lowest_by_side()
        vals = [low[s][2] * 1000.0 for s in SIDES if low[s] is not None]
        sole[frame] = min(vals)
    airborne = sorted(f for f in sole if sole[f] > LIFTOFF_MM)
    aset = set(airborne)
    # ★★★ 脚锁的**作用域**必须跟「约束真的存在」的帧一致 —— 这是本支第 15 次迭代
    #   逼出来的**口径修正**（不是放宽容差）：
    #   踝抬起量 `ankle_lift` 从顶点用 smoothstep 收敛到 0 时，**尾部变得很慢**，
    #   鞋底会**先**跨过 `LIFTOFF_MM`、而抬起量还剩 8~9 mm —— 实测 f=54 鞋底
    #   +8.10 mm（< 12 ⟹ 鞋底口径判它「地面」），但此刻踝的**目标**比锚点高 9.26 mm
    #   ⟹ 判据立刻见红 9.26 mm。**那一帧里「踝锁在锚点」这条约束根本不存在**，
    #   拿它去量漂移是**口径错**（本项目铁律：口径错的判据比没有更坏）。
    #   ⟹ 作用域 = `ankle_lift ≤ 1e-9` 的帧（设计上要求脚钉在锚点的帧）；
    #     鞋底口径的 `TAKEOFF` / `LAND` 仍**现算**，并用 ±2 帧核对标称值。
    liftoff_guard = sorted(f for f in range(START, END + 1)
                           if torso_at(f)["ankle"] > 1e-9)
    ground = [f for f in range(START, END + 1)
              if f not in aset and f not in set(liftoff_guard)]
    res["spawn_lock_scope_frames"] = len(ground)
    res["spawn_lock_scope_excluded_transition"] = sorted(
        set(liftoff_guard) - aset)
    contiguous = bool(airborne) and airborne == list(range(airborne[0],
                                                           airborne[-1] + 1))
    meas_takeoff = airborne[0] if airborne else None
    meas_land = (airborne[-1] + 1) if airborne else None
    peak_air = max((sole[f] for f in airborne), default=0.0)
    res["spawn_sole_min_mm"] = round(min(sole.values()), 3)
    res["spawn_sole_max_mm"] = round(max(sole.values()), 3)
    res["spawn_liftoff_threshold_mm"] = LIFTOFF_MM
    res["spawn_airborne_frames"] = [airborne[0], airborne[-1]] if airborne \
        else None
    res["spawn_airborne_span"] = len(airborne)
    res["spawn_airborne_peak_mm"] = round(peak_air, 3)
    res["spawn_ground_frames"] = len(ground)
    res["spawn_measured_takeoff"] = meas_takeoff
    res["spawn_measured_land"] = meas_land
    res["spawn_nominal_takeoff"] = TAKEOFF
    res["spawn_nominal_touch"] = TOUCH
    res["spawn_airborne_ok"] = bool(
        airborne and contiguous
        and peak_air >= AIRBORNE_PEAK_MIN_MM
        and len(airborne) >= AIRBORNE_SPAN_MIN
        and abs(meas_takeoff - (TAKEOFF + 1)) <= 2
        and abs(meas_land - TOUCH) <= 2
        and min(sole[f] for f in airborne) > 0.0)
    res["spawn_airborne_note"] = (
        "★★★ **「脚离地」由实测现算，不写死**：逐帧量鞋底最低点（`foot_lowest_by_side`，"
        "按**鞋对象**分左右，不用顶点 x 符号 —— 那会在两脚靠近时串门），"
        "`sole_min_z > %.1f mm` 的帧即空中帧。实测空中段 **f=%s（%d 帧）**、"
        "鞋底峰值 **%.1f mm**（下限 %.0f）、实测起飞帧 f=%s、实测落地帧 f=%s。"
        "★ 标称 `TAKEOFF=%d` / `TOUCH=%d` 只用来说明设计意图，"
        "**断言用实测值核对它们（±2 帧）** —— 实测与标称不一致就说明相位排错了。"
        % (LIFTOFF_MM, res["spawn_airborne_frames"], len(airborne), peak_air,
           AIRBORNE_PEAK_MIN_MM, meas_takeoff, meas_land, TAKEOFF, TOUCH))

    # ---- ② ★★ 分段脚锁（**只判地面段**；空中段停用并登记理由）------------
    drift = {s: 0.0 for s in SIDES}
    toe_drift = {s: 0.0 for s in SIDES}
    for frame in ground:
        for side in SIDES:
            drift[side] = max(drift[side],
                              (Vector(samples[idx[frame]]["foot." + side])
                               - Vector(ANCHOR[side])).length * 1000.0)
            toe_drift[side] = max(
                toe_drift[side],
                (Vector(samples[idx[frame]]["toe." + side])
                 - Vector(samples[0]["toe." + side])).length * 1000.0)
    ground_sole = [sole[f] for f in ground]
    res["spawn_ground_ankle_drift_mm"] = {k: round(v, 4)
                                          for k, v in drift.items()}
    res["spawn_ground_toe_drift_mm"] = {k: round(v, 4)
                                        for k, v in toe_drift.items()}
    res["spawn_ground_sole_min_mm"] = round(min(ground_sole), 3)
    res["spawn_ground_sole_max_mm"] = round(max(ground_sole), 3)
    res["spawn_foot_lock_phased_ok"] = bool(
        max(max(drift.values()), max(toe_drift.values())) <= FOOT_LOCK_MM
        and SOLE_BAND[0] <= min(ground_sole) <= max(ground_sole) <= SOLE_BAND[1])
    res["spawn_foot_lock_phased_note"] = (
        "★★★ **「脚锁」按相位分段**（本支最大的口径改动，见 §1 风险 1）。"
        "E01~E03 的 `foot_lock_ok` 建在「踝全程钉在站架世界点」上；本支一跳起来"
        "这个前提**当场失效** —— 照抄全程口径会在空中段**合理见红**。"
        "★ 本判据**只判地面段**（鞋底 ≤ %.1f mm 的帧，共 **%d** 帧）："
        "踝到站架锚点漂移 **L %.4f / R %.4f mm**、趾 **L %.4f / R %.4f mm**"
        "（阈值 %.1f mm），鞋底 **%.2f ~ %.2f mm**（带 %.0f ~ %.0f）。"
        "★ 空中段（f=%s）**停用并登记理由**：脚此刻**真的离地**（实测最高 %.1f mm），"
        "要求它不动等于要求角色不许跳。"
        % (LIFTOFF_MM, len(ground), drift["L"], drift["R"], toe_drift["L"],
           toe_drift["R"], FOOT_LOCK_MM, res["spawn_ground_sole_min_mm"],
           res["spawn_ground_sole_max_mm"], SOLE_BAND[0], SOLE_BAND[1],
           res["spawn_airborne_frames"], peak_air))

    # ---- ③ ★★★ 起跳前摇：下沉量 + 膝屈（两端卡）--------------------------
    p0 = pelvis_z_mm(START)
    crouch_drop = p0 - pelvis_z_mm(CROUCH)
    res["spawn_crouch_drop_mm"] = round(crouch_drop, 3)
    res["spawn_crouch_knee_deg"] = round(knee_deg(CROUCH), 2)
    res["spawn_crouch_range"] = list(CROUCH_RANGE)
    res["spawn_crouch_ok"] = bool(
        CROUCH_RANGE[0] <= crouch_drop <= CROUCH_RANGE[1]
        and res["spawn_crouch_knee_deg"] >= CROUCH_KNEE_MIN)
    res["spawn_crouch_note"] = (
        "★ 起跳前摇 = **看得见的预备动作**（「猛男型角色起跳需要明显预备动作」，"
        "A10 `Jump_Start` 同源要求）。实测骨盆下沉 **%.1f mm**"
        "（区间 %.0f~%.0f，两端卡：太小 = 没预备、太大 = 蹲成马步）"
        "+ 膝屈 **%.1f°**（≥ %.0f°）。"
        % (crouch_drop, CROUCH_RANGE[0], CROUCH_RANGE[1],
           res["spawn_crouch_knee_deg"], CROUCH_KNEE_MIN))

    # ---- ④ ★★★ 落地冲击：躯干净下沉量 + 膝屈（本支的「重」）--------------
    land_sink = p0 - pelvis_z_mm(LAND)
    res["spawn_land_sink_mm"] = round(land_sink, 3)
    res["spawn_land_knee_deg"] = round(knee_deg(LAND), 2)
    res["spawn_land_range"] = list(LAND_RANGE)
    res["spawn_land_sink_ok"] = bool(
        LAND_RANGE[0] <= land_sink <= LAND_RANGE[1]
        and res["spawn_land_knee_deg"] >= LAND_KNEE_MIN)
    res["spawn_land_sink_note"] = (
        "★★★ 落地的「重」**三件套之一**：躯干**净下沉**（站架骨盆 z %.1f → 落地 "
        "%.1f mm）。实测 **%.1f mm**（区间 %.0f~%.0f，**两端都卡**："
        "太小 = 轻飘飘地站住；太大 = 蹲到地上穿模）+ 落地膝屈 **%.1f°**（≥ %.0f°）。"
        "★ 另两件见 `spawn_impact_hitstop_ok`（定格）与 `spawn_airborne_ok`（真的跳起来）。"
        % (p0, pelvis_z_mm(LAND), land_sink, LAND_RANGE[0], LAND_RANGE[1],
           res["spawn_land_knee_deg"], LAND_KNEE_MIN))

    # ---- ⑤ ★★ 根位移：APEX 高度 + END 归零 ------------------------------
    zs = [pelvis_z_mm(f) for f in range(START, END + 1)]
    apex_frame = START + max(range(len(zs)), key=lambda i: zs[i])
    apex_rise = max(zs) - p0
    res["spawn_root_apex_mm"] = round(apex_rise, 3)
    res["spawn_root_apex_frame"] = apex_frame
    res["spawn_root_apex_range"] = list(APEX_RANGE)
    res["spawn_root_end_delta_mm"] = round(abs(pelvis_z_mm(END) - p0), 4)
    res["spawn_root_motion_ok"] = bool(
        APEX_RANGE[0] <= apex_rise <= APEX_RANGE[1]
        and abs(apex_frame - APEX) <= 3
        and res["spawn_root_end_delta_mm"] <= 1.0)
    res["spawn_root_motion_note"] = (
        "★★ www **E 族首次「带根位移」**：实测骨盆 z 峰值 **+%.1f mm** @ f=%d"
        "（标称 APEX=%d，区间 %.0f~%.0f，两端卡：太低 = 没跳起来；"
        "太高 = 出画 / 不真实）；★ **END 必须归零**（实测残差 **%.4f mm**）——"
        "根位移不归零会在下一支的 START 处炸 `seam_in_ok`。"
        "★ 起跳的物理上限 ≈ **+46 mm**（`_e04_conv.py` 实测：dz=+60 时锁踝解发散、"
        "误差 8.58 mm ⟹ 站架腿完全蹬直的可达高度），腾空那 **+400 mm** 靠"
        "**踝随根抬起**（`SPECS[*]['ankle']`）实现，不是靠拉长腿。"
        % (apex_rise, apex_frame, APEX, APEX_RANGE[0], APEX_RANGE[1],
           res["spawn_root_end_delta_mm"]))

    # ---- ⑥ ★★★ 落地定格（hitstop）在落地窗口内 ---------------------------
    steps = []
    for frame in range(HOLD[0], HOLD[1]):
        step, at = _worst_step(samples, idx[frame], idx[frame + 1])
        steps.append((frame, round(step, 6), at))
    worst_hs = max((s for _f, s, _a in steps), default=0.0)
    res["spawn_hitstop_frames"] = HITSTOP_N
    res["spawn_hitstop_window"] = list(HOLD)
    res["spawn_hitstop_steps_deg"] = [
        {"from": f, "step_deg": s, "at": at} for f, s, at in steps]
    res["spawn_hitstop_worst_step_deg"] = round(worst_hs, 6)
    res["spawn_impact_hitstop_ok"] = bool(
        2 <= HITSTOP_N <= 4 and worst_hs <= 0.01
        and HOLD[1] - HOLD[0] + 1 == HITSTOP_N)
    res["spawn_impact_hitstop_note"] = (
        "★★★ **「突出角色力量」= 落地冲击必须有定格**（照 E03 `rage_hitstop_ok` 模式）。"
        "判据量的是**定格窗口内逐帧姿态**（`max |Δ euler|`），窗口 **f=%s** 共 %d 帧，"
        "实测窗口内最大逐帧角步 **%.6f°**（阈值 ≤ 0.01° ⟹ 姿态完全冻结）。"
        "★ 定格靠**时间轴冻结**（帧号前进、姿态不变 + `A.set_hitstop` 把窗口键设 "
        "CONSTANT），**不是**把 N 帧压进插值 —— 否则 `no_snap_stop_ok` 会在定格边界炸。"
        "★ 与 E03 的区别（`spawn_impact_hitstop_ok` ≠ `rage_hitstop_ok`）："
        "E03 是**两个对称窗口**（两次捶胸），本支只有**一个落地窗口**，且它落在"
        "**根位移的终点**：定格期间根停在落地点、姿态逐帧恒定。"
        % ([f for f, _s, _a in steps], HITSTOP_N, worst_hs))

    # ---- ⑦ 收招 / 过缝 --------------------------------------------------
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
        "是 E02 为**循环**动画加的对称性检查。本支 `meta.loop = false`（**一次性"
        "入场**：站架 → 起跳 → 落地 → 回站架，播完交给战斗流程），首末帧同姿只用于"
        "「起手不留痕」，**不要求角速度对称**。实测首帧步 %.3f° / 末帧步 %.3f°"
        "（末帧更慢是**设计意图**：收招要减速）。★ 设一个必然为假的判据等于没有判据。"
        % (first_step, last_step))

    # ---- ⑧ 力量传导链（六段：脚 → 腿 → 髋 → 腰 → 肩 → 手）----------------
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
    knee_deg_span = (max(knee) - min(knee)) * 180.0 / math.pi
    waist = [abs(s["euler"].get("chest", (0.0, 0.0, 0.0))[0]) for s in samples]
    waist_deg = (max(waist) - min(waist)) * 180.0 / math.pi
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
    res["chain_foot_carrier_note"] = (
        "★ 「脚」段的载体与 E02/E03 不同（**载体不适用，不是放宽容差**）："
        "E02 用「迈步时踝的世界行程」、E03 用「锁踝下腿的伸缩」；本支两者都有 ——"
        "地面段踝被钉死（漂移 ≤ %.1f mm），空中段踝**真的走了 %.1f mm**。"
        "判据用「髋↔踝距离的全程行程 = %.1f mm」（腿从深蹲压缩到蹬直再压缩）"
        "＋ 踝的世界行程，两条都真算。"
        % (FOOT_LOCK_MM, (max(sole.values()) - min(sole.values())), foot_axis))
    res["chain_present_ok"] = bool(
        foot_axis > 20.0 and knee_deg_span > 0.2 and hip_travel > 2.0
        and waist_deg > 2.0 and shoulder_mm > 1.0 and hand_mm > 20.0)

    # ---- ⑨ 可达性 ------------------------------------------------------
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

    # ---- ⑩ 穿模（臂 vs 头盒，D01 起老口径）-------------------------------
    worst_clip, clip_at = 0.0, None
    for frame in sorted(set(list(range(START, END + 1, 3))
                            + [HOLD[0], HOLD[1], APEX, CROUCH, TAKEOFF,
                               TOUCH])):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        clip = PD.clip_metrics(arm)
        if clip["clip_max_mm"] > worst_clip:
            worst_clip, clip_at = clip["clip_max_mm"], (frame, clip["clip_at"])
    res["clip_max_mm"] = round(worst_clip, 2)
    res["clip_at"] = clip_at
    res["no_face_clip_ok"] = bool(worst_clip <= CLIP_MAX_MM)

    # ---- ⑪ ★★ 手 vs 躯干：**差分口径**（站架自己就有缺陷，见 `hand_mesh_stats`）
    pierce = {}
    walk = sorted(set(list(range(START, END + 1, 3))
                      + list(range(HOLD[0], HOLD[1] + 1))))
    seam_frames = {START, END}
    worst_nt, worst_nt_at = 0, None
    worst_deep, worst_deep_at = 0.0, None
    worst_all, worst_thumb = 0, 0
    for frame in walk:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        torso_bvh_reset()
        tree = torso_bvh()
        row = {}
        for side in SIDES:
            counts = hand_mesh_stats(side, tree=tree, step=4)
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
        pierce[str(frame)] = row
    station_nt = max(STATION_PIERCE[s]["inside_nothumb"] for s in SIDES)
    res["spawn_pierce_scope"] = ["(0, TOTAL) 内全部帧", "排除接缝帧 %s"
                                % sorted(seam_frames)]
    res["spawn_pierce_nothumb_worst"] = worst_nt
    res["spawn_pierce_nothumb_worst_at"] = worst_nt_at
    res["spawn_pierce_nothumb_deepest_mm"] = round(worst_deep, 2)
    res["spawn_pierce_nothumb_deepest_at"] = worst_deep_at
    res["spawn_pierce_all_worst"] = worst_all
    res["spawn_pierce_thumb_worst"] = worst_thumb
    res["spawn_station_nothumb_count"] = station_nt
    res["spawn_station_pierce"] = {s: dict(STATION_PIERCE[s]) for s in SIDES}
    res["spawn_pierce_detail"] = pierce
    res["spawn_hand_no_pierce_ok"] = bool(
        worst_deep >= -HAND_PIERCE_MM and worst_nt <= station_nt)
    res["spawn_hand_no_pierce_note"] = (
        "★ **本支是「腾空摆臂」，拳全程离躯干很远** —— 但「手贴身体」这类约束"
        "**必须有一条会失败的断言盯着**（本项目铁律：没有判据盯着的约束等于不存在）。"
        "口径照 E03 v011 的**差分**形式（**改的是基准，不是阈值**）："
        "实测本支段非拇指「真在体内」顶点数 **%d**（@ %s）、非拇指最深带符号距离 "
        "**%.2f mm**（@ %s，下限 −%.0f mm）；站架基线同一读数 **%d** 个"
        "（`Idle_01@0` 的预存缺陷：R 手 4 个 `Hand_Palm_R` 腕侧掌肉 / 最深 −4.50 mm"
        "＋ R 拇指 95 个 / −34.19 mm，本支 f=0 / f=%d 必须逐位等于它 ⟹ 口径只能是差分）。"
        "★ 全手（含拇指）读数照样登记：体内最多 **%d** 个（其中拇指 **%d**）。"
        % (worst_nt, worst_nt_at, worst_deep, worst_deep_at, HAND_PIERCE_MM,
           station_nt, END, worst_all, worst_thumb))

    # ---- ⑫ ★★ 真旋转步长（矩阵口径）—— 与 euler 口径互为交叉验证 --------
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
    res["spawn_matrix_step_deg_max"] = round(worst_mat, 3)
    res["spawn_matrix_step_at"] = worst_mat_at
    res["spawn_matrix_step_ok"] = bool(worst_mat <= MATRIX_STEP_MAX_DEG)
    euler_step, euler_at = 0.0, None
    for index in range(1, len(samples)):
        step, at = _worst_step(samples, index - 1, index)
        if step > euler_step:
            euler_step, euler_at = step, at
    res["spawn_euler_step_deg_max"] = round(euler_step, 3)
    res["spawn_euler_step_at"] = euler_at
    res["spawn_matrix_step_note"] = (
        "★★ **矩阵口径**的逐帧最大真实旋转步 **%.3f° @ %s**（阈值 ≤ %.1f°）；"
        "euler 口径 **%.3f° @ %s**。两者**必须一致地小** —— 差得远就说明欧拉表示"
        "在跳（C14 / D01 / E03 的万向节锁坑），而不是动作在跳。"
        "★ 本支先做 `compat_euler`（min-max 瓶颈 DP）再断言，"
        "「我把 no_teleport 修绿了」才不是一句话。"
        "★ 风险 3（§1）：起跳 / 落地是加速度最大的两处，本条是它唯一的守卫。"
        % (worst_mat, worst_mat_at, MATRIX_STEP_MAX_DEG, euler_step, euler_at))

    # ---- ⑬ 手骨滚转基准的退化余量（E03 v009 的教训）---------------------
    res["spawn_x_hint_margin"] = round(MIN_HINT_MARGIN, 4)
    res["spawn_x_hint_margin_min"] = HAND_X_HINT_MIN_MARGIN
    res["spawn_x_hint_margin_ok"] = bool(MIN_HINT_MARGIN
                                         >= HAND_X_HINT_MIN_MARGIN)
    res["spawn_x_hint_margin_note"] = (
        "★ `orient_hand` 的滚转基准（恒定世界 ±X 投影到 ⊥骨轴平面）实测最小余量 "
        "**%.4f**（阈值 ≥ %.2f）。E03 v009 的实测教训：基准若落在骨轴方向上，"
        "投影退化为 0 ⟹ 滚转由浮点噪声决定 ⟹ **真实旋转 83.86°/帧**（不是表示问题，"
        "是真翻）。本支 `y_dir`（前臂方向）全程扫过 YZ 平面，只有带 X 分量的基准安全。"
        % (MIN_HINT_MARGIN, HAND_X_HINT_MIN_MARGIN))

    res["phase_markers"] = {
        "START": START, "CROUCH": CROUCH, "TAKEOFF": TAKEOFF, "APEX": APEX,
        "TOUCH": TOUCH, "LAND": LAND, "HOLD_END": HOLD[1], "SETTLE": SETTLE,
        "END": END}
    res["phase_markers_measured"] = {
        "takeoff": meas_takeoff, "land": meas_land, "apex": apex_frame}
    res["spawn_sole_trace_mm"] = {str(f): round(v, 2)
                                  for f, v in sorted(sole.items())}
    return res


# =============================================================== 屏幕投影（像素探针基准）
def landmark_screen(arm, action):
    """把「骨盆 / 踝 / 鞋底最低点」逐帧投影到**侧视**屏幕坐标，供像素探针用。"""
    name, loc, tgt, scale, rres = VIEW_E04_SIDE
    mm_per_px = scale / float(rres[1]) * 1000.0
    floor_row = (scale / 2.0 - loc[2]) / (scale / float(rres[1]))
    out = {}
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    for frame in range(START, END + 1, 2):
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()
        low = A.foot_lowest_by_side()
        row = {}
        for key, point in (("pelvis", Vector(A.bone_world(arm, "pelvis",
                                                          "head"))),
                           ("footL", Vector(A.bone_world(arm, "foot.L",
                                                         "head"))),
                           ("footR", Vector(A.bone_world(arm, "foot.R",
                                                         "head")))):
            row[key] = [
                round(point.z * 1000.0 / mm_per_px + floor_row, 3),
                round(point.y * 1000.0 / mm_per_px + rres[0] / 2.0, 3)]
        for side in SIDES:
            if low[side] is not None:
                row["sole" + side] = [
                    round(low[side][2] * 1000.0 / mm_per_px + floor_row, 3),
                    round(low[side][1] * 1000.0 / mm_per_px + rres[0] / 2.0,
                          3)]
        out[str(frame)] = row
    return {"view": VIEW_E04_SIDE[0], "res": list(VIEW_E04_SIDE[4]),
            "ortho_m": VIEW_E04_SIDE[3], "cam_y": VIEW_E04_SIDE[1][1],
            "cam_z": VIEW_E04_SIDE[1][2], "mm_per_px": round(mm_per_px, 7),
            "floor_row": round(floor_row, 4), "rows": out,
            "format": "[row, col]"}


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
    global LAST_FOREARM_TWIST, PELVIS0, MIN_HINT_MARGIN, LAST_HAND_X
    LAST_ELBOW = {}
    LAST_HAND_X = {}
    FREEZE["pose"] = None
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
    # ★ 采集站架臂的三个自由度（供 `seat_arm` 的包络收敛用）。
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
        STATION_PIERCE[side] = hand_mesh_stats(side, step=4)
    return arm, meshes


def main():  # noqa: C901
    arm, meshes = boot()
    keyframes = [(frame, spawn_pose(arm, frame))
                 for frame in range(START, END + 1)]
    keyframes = compat_euler(keyframes)
    keyframes = seam_canonicalize(keyframes)
    meta = {
        "anim_id": NAME,
        "loop": False,
        "category": "状态与流程",
        "note": ("入场：站架 → 沉髋蓄力 → 蹬地起跳（腾空 %.0f mm）→ 落地冲击"
                 "（下沉 %.0f mm、定格 %d 帧）→ 起身回战斗架势；"
                 "★ 分段脚锁：地面段锁踝、空中段随根抬起"
                 % (APEX_MM, LAND_MM, HITSTOP_N)),
        "frames": [START, END],
        "root_motion_m": [0.0, 0.0],
        "root_motion_z_m": [APEX_MM / 1000.0, 0.0],
        "hitstop_frames": HITSTOP_N,
        "hitstop_windows": [list(HOLD)],
        "antic_frame": CROUCH,
        "hit_frame": LAND,
        "hit_frames": [LAND],
        "cancel_frame": SETTLE,
        "hit_point_m": None,
        "seam": "%s@%d" % (SEAM_ACTION, SEAM_FRAME),
        "seam_ends": {"start": "%s@%d" % (SEAM_ACTION, SEAM_FRAME),
                      "end": "%s@%d" % (SEAM_ACTION, SEAM_FRAME)},
        "frame_bound_note": ("★ 120 帧 = 2.0 s，**等于** E01 登记的 120 帧 / 2.0 s "
                             "上界 ⟹ 沿用合规（显式声明，不是悄悄超）"),
        "view_note": ("★ 本支取景**自立**（A12 `Launch_Hit` 的教训：高跳会被标准"
                      "视图切掉头脚）：纵向覆盖 −0.30~2.70 m（中心 z=1.20、"
                      "正交高 3.00 m），侧视判下沉/腾空、正面判双脚对称"),
        "phased_foot_lock": {
            "ground": "[START..TAKEOFF] ∪ [TOUCH..END]",
            "airborne": "(TAKEOFF..TOUCH) — 停用地面判据，改判 sole_min_z > 阈值",
            "reason": "根位移与脚锁互斥（§1 风险 1）"},
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.add_markers(action, {
        "START": START, "CROUCH": CROUCH, "TAKEOFF": TAKEOFF, "APEX": APEX,
        "TOUCH": TOUCH, "LAND": LAND, "SETTLE": SETTLE, "END": END})
    if not NO_HITSTOP:
        A.set_hitstop(action, HOLD[0], HOLD[1])

    samples = A.sample_animation(arm, action, START, END, meshes)
    report = A.run_common_assertions(samples, meta, foot_probe=(),
                                     slide_tolerance_mm=FOOT_LOCK_MM)
    report.update(spawn_assertions(arm, action, samples, meshes))

    # ---- 首末同姿（原地起跳：两端都 = 站架）→ 显式算 loop_seamless ---------
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
    A.report("E04_REPORT", report)

    stem_only = os.environ.get("E04_STEM_ONLY") == "1"
    stem_frames = list(STEM_FRAMES)
    if stem_only:
        # ★ 只为像素探针的**反面对照**重渲：**同一台相机 + 同一批帧 + 两个机位**。
        #   ★ 侧视可见 Y/Z（下沉、腾空、脚沿 Y 滑），正面可见 X（双脚对称）⟹
        #     两个机位**各管一维**，反面旋钮必须选在**本机位可见**的那一维上。
        #   ★ 不 save_project / export_glb ⟹ 不污染正式 .blend / GLB。
        A.render_pose_sheet(arm, action, stem_frames,
                            os.environ.get("E04_STEM", "spawnfar"),
                            views=(VIEW_E04_SIDE, VIEW_E04_FRONT))
        print("E04_DONE failed=%s non_ok=%s" % (failed, non_ok))
        return

    if not SKIP_RENDER:
        A.render_pose_sheet(arm, action, list(range(START, END + 1, 4)),
                            "spawnwide", views=(VIEW_E04_SIDE,))
        A.render_pose_sheet(arm, action, stem_frames, "spawn_side",
                            views=(VIEW_E04_SIDE,))
        A.render_pose_sheet(arm, action, stem_frames, "spawn_front",
                            views=(VIEW_E04_FRONT,))
        key_frames = [0, 16, 24, 32, 42, 50, 56, 58, 60, 62, 70, 78, 96, 120]
        A.render_pose_sheet(arm, action, key_frames, "spawnkey",
                            views=(VIEW_E04_SIDE, VIEW_E04_FRONT, A.VIEW_3Q))
        with open(os.path.join(A.PREVIEW_DIR, "_e04_landmark.json"), "w",
                  encoding="utf-8") as handle:
            json.dump(landmark_screen(arm, action), handle, ensure_ascii=False)
        A.save_project()
        A.export_glb(arm)
    print("E04_DONE failed=%s non_ok=%s" % (failed, non_ok))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("E04_FAILURE " + traceback.format_exc())
