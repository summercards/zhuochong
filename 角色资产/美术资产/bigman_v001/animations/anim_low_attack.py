"""anim_low_attack —— B06 `Low_Attack` 下段攻击（**前腿低踢**，命中高度明确低于腰部）。

设计（对着清单「下一支详细制作计划 —— B06」逐条落）：
    定位      踢腿 / 扫腿，攻击高度**明确低于腰部**；单发普通攻击（B 族）。
    时长      46 帧 / 0.767 s @60fps，**非循环**。
    首帧      **逐位 = `Idle_01@0`**（起手不许闪）。
    末帧      **停在自持的「收势」姿态**（收腿落地，不回 idle）。
    结构      GUARD 0 ／ LOAD 0~5（攻击腿**向后压**做反向预备）／
              CHAMBER 5~10（抬腿前引：膝抬到 z≈0.69、小腿回折，`ANTIC_END = 10`）／
              BURST 10~20（`hit_frame = 20`，小腿甩出、踢到 z≈0.42 的低位）／
              HITSTOP f20~f23（**4 帧完全冻结**）／
              FOLLOW 20~25（髋继续送、上身继续后仰"打透"）／
              RECOVER 25~40（缓出滑停，收腿落地）／clock ≥40 姿态**逐位恒定**／CANCEL 30。

---------------------------------------------------------------------------
★ 第 0 件：探针（`probe_low06.py`）四个定盘数

  1. **支撑腿 = 后脚 R / 攻击腿 = 前脚 L**。理由两条：
     · 前脚踢出时腿向前甩、骨盆不挡道；且**前脚是近侧腿**（side 相机在 +X，
       角色左半身朝镜头）⟹ 踢击全程**看得见**，不会被躯干挡住。
     · 支撑腿 R 在髋**后面 140 mm**：骨盆后移会**缩短**髋→踝，比反过来安全。
       探针实测支撑腿全程余量 **≥48.7 mm**（计划下限 20 mm），最险的一档是
       "骨盆前移 40 mm"才能压到 48.7 —— 本支的位移是**下沉 + 后移**，方向安全。
  2. **踝骨全静止位**：L (143.2, −169.6, 79.8) / R (−141.6, 140.4, 79.8)；
     髋 (±90.0, 0, 830.0)；腿长 410 + 412 = 822 mm；idle 髋→踝 **771.0 / 764.9**
     （余量 51.0 / 57.1，与 B05 记的逐位一致）。大腿中点（髋膝中点）**658.6** mm。
  3. **腿的 pole 不退化**：抬腿到侧前方时，纯"向前"的膝鼓出方向在**伸直的瞬间**
     会退化（探针实测 (y −700, z 550) 时 `|pole⊥axis|` 只剩 **0.377**）；
     把 pole 加一点**侧向外**（0.25, −1, 0）后，全程 **≥0.60**（chamber 段 ≥0.96）。
     ⟹ 用**侧向偏置的 pole 轨**（idle 实测 → (0.25,−1,0)，smoothstep 过渡），
       并用 `_knee_bulge` 的**接力式平滑混**（同 B04 第 3 件的做法，**不是硬阈值**）。
  4. **命中高度可行**：骨盆沉 115 mm（z 0.715）时，"骨盆 z − 250 = 465 mm"的
     天花板下，攻击踝放在 **425 mm** 仍可解（伸展率 **0.937**、屈膝 40.7°、
     `|pole⊥|` 0.66）⟹ 命中点**低于腰线 290 mm**，视觉余量 40 mm。

---------------------------------------------------------------------------
★ 第 1 件：**本支是清单第一支「单腿支撑」动画，脚滑判据必须拆两侧写。**
  B04/B05 的 `no_foot_slide` 是"双脚都不动"（`toe.L` 与 `toe.R` 都量）。
  本支支撑脚必须**全程钉死 ≤3 mm**、鞋底 −2~+6 mm，而**攻击腿要大幅离地**。
  ⟹ 通用门禁只对**支撑脚**生效（`foot_probe=("toe.R",)`），
     攻击腿**不进**这条判据；同时新写 `support_foot_pinned_ok`（踝位移 + 鞋底）。

---------------------------------------------------------------------------
★ 第 2 件：**`power_chain` 的六段基准不能照搬 B05 —— 换尺子，不是放宽。**
  B05 的六段是这么挣来的：`hand` 段 **137.43°** 来自锤击**手腕的大翻转**，
  `hip`/`waist` 来自双手锤击的**躯干折叠**。本支是**踢腿**：手臂只做配重，
  腕子不可能翻 137°，躯干也不该折 —— 六段全 > B05 在物理上不成立。
  处置（照 B04→B05 的先例「口径跟着动作类型走」）：
    · **同物理量的两段仍然严格要求 > B05**：
      `foot` > 23.53（脚部通道幅度）、`leg` > 44.91（腿部通道幅度）——
      下段攻击的驱动肢体正落在这两段上（实测预期 ≈60 / ≈90）。
    · 其余四段改为 **非退化（≥3°）+ 时序（髋先于脚）+ 攻击肢体占优
      （攻击腿幅度 > 支撑腿 ×1.5）** 三条结构判据。
    · `power_chain_vs_b05` 把**六段全部数值**照实列出，不做隐藏。

---------------------------------------------------------------------------
★ 第 3 件：**"上身反向配重"量的是物理方向，不是欧拉符号。**
  `upper_body_balance_ok`：腿**向前**摆（`thigh.rx` 变小）时，上身必须**向后仰**
  （`spine_01+spine_02+chest` 的 rx 变小）。两者在**世界 rx 上同号**（都是绕 +X
  负向），但**物理方向相反** —— 报告里把两个量都明确写出来（`leg_swings_forward`
  / `trunk_leans_back`），幅度取 `trunk_rel` 的变化量，门槛 **≥8°**。

---------------------------------------------------------------------------
★ 第 4 件：**沿用 B04 第 1 件：不要覆写 `aim_carry` 的搜索旋钮。**
  `JS.Y_SAFE` / `JS.ROLL_COMFORT` 一律用库默认（62 / 16）。
  本文件**不出现**任何 `JS.Y_SAFE = …` 的赋值。
  ★ 本支把 `aim_carry` 第一次用在**腿**上（B04/B05 用的是 `TURN.leg_to` + 解缠）：
    必须把 `JS.ARM_QUAT` / `JS._PREV_EULER` 对 thigh/shin/foot **一并播种**
    （否则 f0→f1 腿从 rest 起步，第一帧就闪）。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python anim_low_attack.py
    SKIP_RENDER=1 只跑门禁（迭代用）。
"""

import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A          # noqa: E402
import anim_idle_01 as I1     # noqa: E402
import anim_jump_start as JS  # noqa: E402
import anim_jump_up as JU     # noqa: E402
import anim_jump_fall as JF   # noqa: E402
import anim_crouch as CR      # noqa: E402
import anim_light_01 as L1    # noqa: E402

NAME = "Low_Attack"
TOTAL = 46                    # 0.767 s @60fps
HIT = 20                      # 命中帧
HOLD = 3                      # 冻结 f20..f23 = **4 帧**
CLOCK_END = TOTAL - HOLD      # 43：动作时钟跨度

LOAD_END = 5                  # 反向预备（攻击腿向后压）到位
CHARGE_END = 10               # 抬腿前引（chamber）到位
ANTIC_END = CHARGE_END        # 前摇结束（清单「重攻击前摇 12~20 帧」的短支）
BURST_START = CHARGE_END      # 爆发起点 = chamber 到位点（10）⟹ 爆发段 10→20 = 10 帧
FOLLOW_END = 25               # 打透峰值
RECOVER_END = TOTAL - 2 * HOLD  # 40 ⟹ clock 40~43 姿态逐位恒定（末 4 帧零变化）
CANCEL = 30                   # 可取消帧（清单）

LOAD_POW = 1.00
CHAMBER_POW = 1.10            # 抬腿前引**起步缓、收尾快**（`u^p, p>1` ⟹ 首帧无尖峰）
BURST_POW = 1.65              # 后段加速 = 踢击的"甩出去"（踢击必须是全程最快的一段）
FOLLOW_POW = 1.25
SETTLE_POW = 2.00             # 收招缓出（步长单调收敛到 0）
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"

SIDES = ("L", "R")
SUPPORT = "R"                 # 支撑腿 = 后脚 R（钉死的那条）
ATTACK = "L"                  # 攻击腿 = 前脚 L（离地自由的那条）

ARM_BONES = {"L": ("upperarm.L", "forearm.L", "hand.L"),
             "R": ("upperarm.R", "forearm.R", "hand.R")}
ARM6 = ARM_BONES["L"] + ARM_BONES["R"]
LEG6 = ("thigh.L", "shin.L", "foot.L", "thigh.R", "shin.R", "foot.R")
DROP = I1.DROP                # −0.070：战斗站姿的骨盆下沉量

# B05 的比较基准（写死在文件里，不靠记忆）—— 见文件头第 2 件
B05_SEGMENT_RANGES = {"foot": 23.53, "leg": 44.91, "hip": 28.0,
                      "waist": 33.0, "shoulder": 39.0, "hand": 137.43}
B05_SAME_QUANTITY = ("foot", "leg")     # 与 B05 **同一物理量**的两段，必须严格超过
B05_HIT_Z_MM = 638.9                    # B05 命中拳峰 z（"下段攻击要比它更低"的对照）

IDLE_PELVIS_Z_MM = 830.0                # 探针实测：idle 骨盆 z
LOW_HEIGHT_MARGIN_MM = 250.0            # 计划原文：命中脚 z < 骨盆 z − 250
CHAMBER_RISE_MIN_MM = 120.0             # 膝必须真抬起来
TRAVEL_MIN_MM = 600.0                   # 攻击脚世界行程（弧长）
HIP_SWEEP_MIN_DEG = 70.0                # 以髋为轴的累计转角
BALANCE_MIN_DEG = 8.0                   # 上身反向配重幅度


# =============================================================== 相位时钟
def clock(frame):
    """动作时钟：命中停顿期间**时间冻结**（f20~f23 读同一个 clock = 20 ⟹ 姿态逐位相同）。"""
    if frame <= HIT:
        return frame
    if frame <= HIT + HOLD:
        return HIT
    return frame - HOLD


def _ramp(c, start, end, power):
    """`start → end` 的幂律上升；两端**精确**取 0 / 1（"真平台"的来源）。"""
    if c <= start:
        return 0.0
    if c >= end:
        return 1.0
    return ((c - start) / float(end - start)) ** power


def load_s(c):
    return _ramp(c, 0.0, LOAD_END, LOAD_POW)


def chamber_s(c):
    return _ramp(c, LOAD_END, CHARGE_END, CHAMBER_POW)


def burst_s(c):
    """踢击：`BURST_START(10) → HIT(20)` = **10 帧**，`u**1.25`（后段加速）。"""
    return _ramp(c, BURST_START, HIT, BURST_POW)


def follow_s(c):
    return _ramp(c, HIT, FOLLOW_END, FOLLOW_POW)


def settle_s(c):
    """收招：**缓出**（步长随 u→1 单调递减到 0）—— B04 第 5 件的结论，一字不改。"""
    u = (c - FOLLOW_END) / float(RECOVER_END - FOLLOW_END)
    if u <= 0.0:
        return 0.0
    if u >= 1.0:
        return 1.0
    return 1.0 - (1.0 - u) ** SETTLE_POW


def chain6(g, ld, ch, st, fo, en, c):
    """六段姿态路径：guard → load → chamber → strike → follow → end。

    `= g + (ld−g)·load + (ch−ld)·chamber + (st−ch)·burst + (fo−st)·follow
        + (en−fo)·settle`
    每个相位标量都精确饱和 ⟹ `c = 0/5/10/20/25/≥40` 处分别取 `g/ld/ch/st/fo/en`，
    **且 clock ≥40 后逐位恒定**（末 4 帧步长恒为 0）。
    """
    return (g
            + (ld - g) * load_s(c)
            + (ch - ld) * chamber_s(c)
            + (st - ch) * burst_s(c)
            + (fo - st) * follow_s(c)
            + (en - fo) * settle_s(c))


def chain3(row, c):
    return tuple(chain6(row[0][i], row[1][i], row[2][i], row[3][i], row[4][i],
                        row[5][i], c) for i in range(3))


CHANNEL_INDEX = {"rx": 0, "ry": 1, "rz": 2}

ANKLE_REST = {}               # side -> Vector：`Idle_01@0` 的踝位
IDLE_POSE = {}                # `Idle_01@0` 的完整姿态字典（首帧整帧取用）
POLE_LEG = {}                 # side -> 实测的膝鼓出方向（idle）
TRACE = []                    # 逐帧手臂/腿欧拉（|Y| 健康度诊断）
TARGETS = []                  # [(frame, side, target)]：腿部 IK 到位核验
REACH = []                    # [(side, ratio)]：腿伸展率体检


# =============================================================== 躯干轨
# 每行 = (bone, channel, guard, load, chamber, strike, follow, end)，单位度。
# ★ guard 那一列必须逐位等于 `Idle_01@0` 的真值：
#   pelvis 4.0 / spine 2.0 / chest 1.0 / neck −6.0 / head 5.0 / shoulder rx −18.0，其余 0。
# ★ 本支的"打透"落在 **−rx（后仰量）** 上：踢腿时上身后仰，命中后**继续后仰**
#   ⟹ `body_follow_through_ok` 的通道取 `−rx`（见门禁与报告口径）。
TRUNK_CHAIN = (
    ("pelvis", "rx", 4.0, 3.0, 3.0, -4.0, -8.0, 3.0),
    ("spine_01", "rx", 2.0, 2.0, 2.0, -3.0, -5.0, 2.0),
    ("spine_02", "rx", 2.0, 2.0, 2.0, -3.0, -5.0, 2.0),
    ("chest", "rx", 1.0, 0.0, -4.0, -14.0, -20.0, 2.0),
    # 颈/头：低头看**低位目标**（净俯角 = chest + neck + head）。
    ("neck", "rx", -6.0, -5.0, -2.0, 6.0, 8.0, -5.0),
    ("head", "rx", 5.0, 4.0, 3.0, 16.0, 20.0, 6.0),
    # 肩带：抬腿时略收（rx 抬 4°）、踢出去时**沉 + 前后摆**做配重。
    ("shoulder.L", "rx", -18.0, -16.0, -14.0, -24.0, -29.0, -15.0),
    ("shoulder.R", "rx", -18.0, -16.0, -14.0, -24.0, -29.0, -15.0),
    ("shoulder.L", "rz", 0.0, 1.0, 2.0, -6.0, -8.0, -2.0),
    ("shoulder.R", "rz", 0.0, -1.0, -2.0, 6.0, 8.0, 2.0),
)

# 骨盆位移：**原地**（清单 §0.4：普通攻击不许 Root Motion）—— 只有"下沉 + 微后移"。
# ★ `knee_drop_ok`（本支改口径）：支撑腿**屈膝下沉 ≥40 mm**；实测下沉 115 mm。
# ★ **为什么给到 115 mm**：① 命中高度靠它把天花板压到 465 mm；② 支撑腿屈膝变深
#   让 `leg` 段幅度真的大起来（不是把尺子换软）。
# ★ 后移（+Y）对支撑腿 R 是**安全方向**（R 在髋后面 140 mm，后移会缩短髋→踝）。
PELVIS_DX = (0.000, 0.000, 0.000, 0.000, 0.000, 0.000)
PELVIS_DY = (0.000, 0.000, 0.010, 0.020, 0.024, 0.006)
PELVIS_DZ = (0.000, -0.030, -0.055, -0.115, -0.135, -0.040)

# ★ **蒙皮补偿**（B05 第 2 件的结论）：鞋底最高点随屈膝下沉**线性下陷**
#   （线性混合蒙皮在踝部的固有下沉，`ankle_target_error_mm` 只有 ~0.02 mm ⟹ 不是 IK 误差）。
#   按 |下沉量| 的 1.2% 把踝 IK 目标抬高补偿，**只在 c > 0 生效**
#   ⟹ f0 的踝位仍逐位 = idle，`guard_start_ok` 不受影响。
ANKLE_SKIN_LIFT_RATIO = 0.012

# 攻击腿踝目标的**世界偏移轨**（相对 `Idle_01@0` 的踝位，米）。
# ★ 六段端点值即探针定盘的目标；中间段用 `lerp3`（直线），因为三段直线都不触地。
A_TRACK = (
    (0.000, 0.000, 0.000),        # guard   = idle 踝位
    (0.012, 0.220, 0.075),        # load    : 向后压 220 mm（反向预备），踝同时抬 75
    (0.057, 0.050, 0.360),        # chamber : 膝抬起（膝 z≈0.66）、小腿回折，踝在膝下偏后
    (0.022, -0.520, 0.345),       # strike  : 甩出到前方（y≈−0.690、z≈0.425）
    (0.024, -0.530, 0.310),       # follow  : 髋继续送、脚再落下一点
    (0.000, 0.000, 0.000),        # end     : 收腿落地，回到原位
)
# 攻击脚**世界朝向轨**（foot 骨的骨长方向）：从踩平 → 压脚背 → 甩成脚背朝前的踢击面。
# ★ `load` 行取**接近 rest**（而不是"脚尖压地"的陡俯角）：首版 load 行 (0.10,−0.55,−0.83)
#   在踝只抬 35 mm 时把**鞋尖捅进地面 48.24 mm**（`ground_contact_ok` 假红）。
#   本支的 load 不做"脚尖压地"，改做"平脚后撤、踝略抬"，鞋底全程离地。
FOOT_DIR_TRACK = (
    (0.031, -0.8924, -0.4501),    # guard   = 实测 rest 朝向
    (0.060, -0.8200, -0.5700),    # load    : 平脚后撤（略压脚背，踝已抬 75）
    (0.150, 0.1000, -0.9800),     # chamber : 脚尖垂下（小腿回折）
    (0.100, -0.9300, -0.3500),    # strike  : 脚背顺着小腿甩出
    (0.100, -0.9600, -0.2600),    # follow  : 再压一点
    (0.031, -0.8924, -0.4501),    # end     : 踩回平地
)

# 骨盆后移 / 下沉的**腿 pole 轨**：idle 实测 → 侧向外（见文件头第 3 件）。
POLE_LATERAL = {"L": (0.25, -1.0, 0.0), "R": (-0.25, -1.0, 0.0)}
# pole 退化保护（同 B04 第 3 件）：低于 LO 完全接力、高于 HI 完全用 pole，中间 smoothstep。
POLE_BLEND_LO = 0.30
POLE_BLEND_HI = 0.90

# 双臂配重（肩相对偏移轨，米）：踢腿时双拳**向后、向外**拉，做反向配重。
# guard 列 = idle 实测；x 分量为正表示**向身体外侧**（左侧 +x、右侧 −x）。
ARM_TRACK_D = (
    (0.000, 0.000, 0.000),
    (-0.008, 0.020, 0.010),
    (-0.016, 0.045, 0.005),
    (0.045, 0.115, -0.020),
    (0.055, 0.130, -0.030),
    (0.015, 0.030, -0.045),
)
HAND_DIR_D = (
    (0.000, 0.000, 0.000),
    (0.000, 0.060, 0.020),
    (0.000, 0.100, 0.050),
    (0.000, 0.220, 0.100),
    (0.000, 0.260, 0.120),
    (0.000, 0.050, -0.050),
)


def trunk_pose(c):
    pose = {}
    for bone, channel, g, ld, ch, st, fo, en in TRUNK_CHAIN:
        row = pose.setdefault(bone, [0.0, 0.0, 0.0])
        row[CHANNEL_INDEX[channel]] = chain6(g, ld, ch, st, fo, en, c)
    return {bone: tuple(row) for bone, row in pose.items()}


def ankle_offset(c):
    return Vector(chain3(A_TRACK, c))


def foot_dir(c):
    return Vector(chain3(FOOT_DIR_TRACK, c)).normalized()


def arm_offset(side, c):
    """肩相对偏移：guard 实测 + 一条**只 negate x** 的镜像轨（矢状面镜像）。"""
    out = Vector(O_ARM_GUARD[side])
    delta = Vector(chain3(ARM_TRACK_D, c))
    sign = 1.0 if side == "L" else -1.0
    return out + Vector((delta.x * sign, delta.y, delta.z))


def hand_dir(side, c):
    base = Vector(I1.ARM_DIRS["hand." + side])
    return (base + Vector(chain3(HAND_DIR_D, c))).normalized()


def bone_len(arm, name):
    return (Vector(A.bone_world(arm, name, "tail"))
            - Vector(A.bone_world(arm, name, "head"))).length


def _leg_pole_from_pose(arm, side):
    """实测「膝的鼓出方向」= (膝−髋) 去掉沿 髋→踝 轴分量后的单位垂足。

    与 `anim_heavy_02._pole_from_pose`（肘）同一口径。**必须实测**：
    IK 只定髋→踝的轴与两段骨长，**膝落在轴的哪一侧由 pole 决定**；
    pole 与 idle 的实际膝向差 90°，f0（= idle）到 f1（IK 解）就会**拧膝**。
    """
    hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
    knee = Vector(A.bone_world(arm, "shin." + side, "head"))
    ankle = Vector(A.bone_world(arm, "foot." + side, "head"))
    delta = ankle - hip
    axis = delta.normalized() if delta.length > 1e-9 else Vector((0.0, -1.0, 0.0))
    bulge = (knee - hip) - axis * (knee - hip).dot(axis)
    if bulge.length < 1e-6:
        bulge = Vector((0.0, -1.0, 0.0)) - axis * axis.y
    return tuple(bulge.normalized())


# =============================================================== 腿双骨 IK
_BULGE_PREV = {}              # side -> Vector：上一帧的膝鼓出方向（世界单位向量）
POLE_SIN = []                 # [(frame, side, |pole⊥axis|)]：pole 退化体检


def _knee_bulge(side, axis, pole):
    """膝的鼓出方向（垂直于 `axis` 的单位向量）+ 退化体检值 `|pole⊥axis|`。

    沿用 B04 第 3 件：`pole` 与"上一帧鼓出方向"按 `|pole⊥axis|` **平滑混合**
    （`POLE_BLEND_LO/HI` 之间的 smoothstep 过渡带），鼓出方向逐帧连续，
    不被退化投影翻来翻去。输出仍是严格垂直于轴的单位向量 —— 是"接力"不是放宽。
    **不许硬阈值**：本支伸直的瞬间 `|pole⊥axis|` 会掉到 0.66 附近，正好落在过渡带上方。
    """
    pole_v = Vector(pole)
    bulge = pole_v - axis * pole_v.dot(axis)
    sin_pole = bulge.length
    prev = _BULGE_PREV.get(side)
    if prev is not None:
        alt = prev - axis * prev.dot(axis)
        if alt.length > 1e-6:
            alt.normalize()
            if bulge.length < 1e-6:
                bulge = alt
            else:
                w = (sin_pole - POLE_BLEND_LO) / (POLE_BLEND_HI - POLE_BLEND_LO)
                w = min(1.0, max(0.0, w))
                w = w * w * (3.0 - 2.0 * w)
                bulge = bulge.normalized() * w + alt * (1.0 - w)
    if bulge.length < 1e-6:
        bulge = Vector((0.0, -1.0, 0.0)) - axis * axis.y
    bulge.normalize()
    _BULGE_PREV[side] = bulge
    return bulge, sin_pole


def leg_aim(arm, pose, side, target, pole):
    """把一侧的 thigh/shin 解到「踝（`foot.head`）落在世界 `target`」。

    与 `TURN.leg_to` 同几何（叉积平面内的两骨解），但两处不同：
      · 膝的鼓出方向用 `_knee_bulge` 的**接力平滑**（B04 第 3 件），
        不是 `leg_to` 里那个"投影为零就退化成 Z 轴"的硬分支；
      · 用 `JS.aim_carry` 反解（**从上一帧已达成世界朝向接力** + 绕骨轴 roll 搜索），
        表示连续 —— B04/B05 用 `TURN.leg_to` + `_unwrap_legs` 补的那一步，
        在这里由 carry 从源头保证。
    返回 `|pole⊥axis|`（体检值）。
    """
    thigh_len, shin_len = A.L_THIGH, A.L_SHIN
    hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
    target = Vector(target)
    delta = target - hip
    raw = delta.length
    limit = (thigh_len + shin_len) * 0.9995
    distance = max(1e-4, min(raw, limit))
    REACH.append((side, raw / (thigh_len + shin_len)))
    axis = (delta.normalized() if delta.length > 1e-9
            else Vector((0.0, 0.0, -1.0)))
    bulge, sin_pole = _knee_bulge(side, axis, pole)
    cos_hip = (thigh_len ** 2 + distance ** 2 - shin_len ** 2) \
        / (2.0 * thigh_len * distance)
    cos_hip = max(-1.0, min(1.0, cos_hip))
    sin_hip = math.sqrt(max(0.0, 1.0 - cos_hip * cos_hip))
    knee = hip + (axis * cos_hip + bulge * sin_hip) * thigh_len
    pose["thigh." + side] = JS.aim_carry(arm, "thigh." + side, knee - hip)
    pose["shin." + side] = JS.aim_carry(arm, "shin." + side, target - knee)
    POLE_SIN.append((side, sin_pole))
    return sin_pole


def arm_to(arm, pose, side, fist_target, direction, pole):
    """把一侧的上臂/前臂/手解到「拳峰落在世界 `fist_target`、手骨指向 `direction`」。

    与 `anim_heavy_02.arm_to` 同几何（本支的拳只是配重，不需要新工具）。
    """
    upper, fore, handb = ARM_BONES[side]
    length_up = bone_len(arm, upper)
    length_fore = bone_len(arm, fore)
    length_hand = bone_len(arm, handb)
    want = Vector(direction).normalized()
    wrist_target = Vector(fist_target) - want * length_hand

    shoulder = Vector(A.bone_world(arm, upper, "head"))
    delta = wrist_target - shoulder
    raw_distance = delta.length
    limit = (length_up + length_fore) * 0.9995
    distance = max(1e-4, min(raw_distance, limit))
    axis = (delta.normalized() if delta.length > 1e-9
            else Vector((0.0, -1.0, 0.0)))
    pole_v = Vector(pole)
    bulge = pole_v - axis * pole_v.dot(axis)
    if bulge.length < 1e-6:
        bulge = Vector((0.0, 0.0, 1.0)) - axis * axis.z
    bulge.normalize()
    cos_hip = (length_up ** 2 + distance ** 2 - length_fore ** 2) \
        / (2.0 * length_up * distance)
    cos_hip = max(-1.0, min(1.0, cos_hip))
    sin_hip = math.sqrt(max(0.0, 1.0 - cos_hip * cos_hip))
    elbow = shoulder + (axis * cos_hip + bulge * sin_hip) * length_up

    pose[upper] = JS.aim_carry(arm, upper, elbow - shoulder)
    pose[fore] = JS.aim_carry(arm, fore, wrist_target - elbow)
    pose[handb] = JS.aim_carry(arm, handb, want)


def _record_trace(arm, frame, pose):
    for name, value in pose.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)
    TRACE.append({
        "frame": frame,
        "euler": {b: tuple(round(v, 2) for v in pose[b]) for b in ARM6 + LEG6},
        "roll": {b: round(JS.ARM_ROLL.get(b, 0.0), 1) for b in ARM6 + LEG6},
    })


# =============================================================== 姿态生成
_FROZEN_POSE = {}             # clock -> pose：命停窗口与收招平台**逐位复用同一姿态**
# ★ 命停 4 帧的"冻结"必须靠复用同一个解：f20~f23 是四次独立 IK 求解，
#   历史（`_PREV_EULER` / roll 搜索）各差一帧 ⟹ 会差 0.004° 的浮点噪声，
#   `hitstop_frozen_steps` 直接判成 0（B05 踩过）。
# ★ 收招平台（clock ≥ RECOVER_END）同理：只有**复用**才能保证末 4 帧步长恒为 0，
#   `decel_smooth_ok` 的"单调收敛到 0"才不是碰运气。


def build_pose(arm, frame, record=False):
    """按帧构造完整姿态（内部一律用 `clock(frame)` 驱动）。"""
    c = clock(frame)
    key = HIT if c == HIT else (RECOVER_END if c >= RECOVER_END else None)
    frozen = _FROZEN_POSE.get(key) if key is not None else None
    if frozen is not None:
        A.apply_pose(arm, frozen)
        if record:
            # ★ 必须用**该冻结姿态自己的 clock**（`key`），不能用 RECOVER_END 顶替：
            #   命中窗口的冻结姿态是在 c = HIT 解出来的，若这里用 c = RECOVER_END 的
            #   `ankle_offset`，记录的目标会与姿态差 (0.022,−0.520,0.345) ≈ **623 mm**
            #   ⟹ `ik_reach_ok` 假红（首版实测 624.942 mm，正是这个数）。
            lift = Vector((0.0, 0.0, ANKLE_SKIN_LIFT_RATIO
                           * abs(chain6(*PELVIS_DZ, key))))
            TARGETS.append((frame, SUPPORT, tuple(ANKLE_REST[SUPPORT] + lift)))
            TARGETS.append((frame, ATTACK,
                            tuple(ANKLE_REST[ATTACK] + lift
                                  + ankle_offset(key))))
        _record_trace(arm, frame, frozen)
        return {k: (dict(v) if k == "@loc" else tuple(v))
                for k, v in frozen.items()}

    pose = trunk_pose(c)
    pose["toe.L"] = (0.0, 0.0, 0.0)
    pose["toe.R"] = (0.0, 0.0, 0.0)
    pose["@loc"] = {"pelvis": A.wloc(chain6(*PELVIS_DX, c), chain6(*PELVIS_DY, c),
                                     DROP + chain6(*PELVIS_DZ, c))}
    pose.update(A.FIST)
    A.apply_pose(arm, pose)

    # `POLE_SIN` 里 `leg_aim` 追加的是 `(side, sin)` 二元 ⟹ 这里统一补帧号。
    # ★ 标记必须在**第一次 `leg_aim` 之前**取（B06 只有腿走这条轨）。
    pole_mark = len(POLE_SIN)

    # 踝目标抬 `ANKLE_SKIN_LIFT_RATIO × 下沉量`：补偿蒙皮在踝部的固有下陷（见常量表）。
    lift_z = ANKLE_SKIN_LIFT_RATIO * abs(chain6(*PELVIS_DZ, c))
    # ★ 支撑腿：目标 = idle 踝位钉死（+蒙皮补偿）⟹ `support_foot_pinned_ok` 的构造保证。
    target_support = ANKLE_REST[SUPPORT] + Vector((0.0, 0.0, lift_z))
    if record:
        TARGETS.append((frame, SUPPORT, tuple(target_support)))
    leg_aim(arm, pose, SUPPORT, target_support,
            _leg_pole(SUPPORT, c))
    # ★ 攻击腿：目标 = idle 踝位 + 偏移轨（+蒙皮补偿）⟹ 全程离地自由。
    target_attack = (ANKLE_REST[ATTACK] + ankle_offset(c)
                     + Vector((0.0, 0.0, lift_z)))
    if record:
        TARGETS.append((frame, ATTACK, tuple(target_attack)))
    leg_aim(arm, pose, ATTACK, target_attack, _leg_pole(ATTACK, c))

    # 足：支撑脚**钉平到世界水平**（rest 朝向），鞋底全程贴地；
    #     攻击脚：**离地踢击窗口内**按 `FOOT_DIR_TRACK` 的朝向轨（踢击面 = 脚背），
    #     **落地段**（收招）改用与支撑脚同一条 `keep_world_orientation` ——
    #     ★ 理由（实测得出，不是猜）：`aim_carry` 的 roll 是**历史相关**的，
    #       踢完一圈回到 rest 朝向时 roll 已经漂了，鞋底被拧出一个倾角 ⟹
    #       末 4 帧（收招平台）鞋底陷地 **−5.78 mm**（同姿态下支撑脚只有 −0.94，
    #       差 4.84 mm 全在 roll 上，不在踝高上）。钉 rest 基座没有这个累积误差。
    name = "foot." + SUPPORT
    A.keep_world_orientation(arm, name)
    pose[name] = JS._unwrap_xyz(
        JS._PREV_EULER.get(name),
        tuple(math.degrees(v) for v in arm.pose.bones[name].rotation_euler))
    an = "foot." + ATTACK
    if LOAD_END <= c <= FOLLOW_END:                 # c∈[5,25]：踢击面
        pose[an] = JS.aim_carry(arm, an, foot_dir(c))
    else:                                           # 其余：钉平（= idle rest 朝向）
        A.keep_world_orientation(arm, an)
        pose[an] = JS._unwrap_xyz(
            JS._PREV_EULER.get(an),
            tuple(math.degrees(v) for v in arm.pose.bones[an].rotation_euler))

    # 双臂：拳峰 = 各自的肩 + 世界偏移（躯干怎么动，拳就跟着肩走）。
    for side in SIDES:
        shoulder = Vector(A.bone_world(arm, "upperarm." + side, "head"))
        arm_to(arm, pose, side, shoulder + arm_offset(side, c),
               hand_dir(side, c), POLE_ARM[side])
    for i in range(pole_mark, len(POLE_SIN)):
        POLE_SIN[i] = (frame,) + POLE_SIN[i]

    _record_trace(arm, frame, pose)
    if c == HIT:
        _FROZEN_POSE[HIT] = {k: (dict(v) if k == "@loc" else tuple(v))
                             for k, v in pose.items()}
    if c == RECOVER_END:
        _FROZEN_POSE[RECOVER_END] = {k: (dict(v) if k == "@loc" else tuple(v))
                                     for k, v in pose.items()}
    return pose


def _leg_pole(side, c):
    """膝鼓出方向的**轨**：idle 实测 → `POLE_LATERAL`；权重 = 前摇相位的 smoothstep。

    ★ 目的：让 `|pole⊥axis|` 在"腿伸直"的那几帧也不退化（探针实测最低 0.60），
      从而 `_knee_bulge` 的接力不会被迫接管太多。
    """
    base = POLE_LEG.get(side)
    if base is None:
        return POLE_LATERAL[side]
    w = chamber_s(c)
    w = w * w * (3.0 - 2.0 * w)
    return tuple(base[i] + (POLE_LATERAL[side][i] - base[i]) * w
                 for i in range(3))


# =============================================================== 专属门禁
SEGMENTS = {
    "foot": ("foot.L", "foot.R", "toe.L", "toe.R"),
    "leg": ("thigh.L", "shin.L", "thigh.R", "shin.R"),
    "hip": ("pelvis",),
    "waist": ("spine_01", "spine_02", "chest"),
    "shoulder": ("shoulder.L", "shoulder.R"),
    "hand": ARM6,
}
SEGMENT_POINTS = {
    "foot": ("foot.L.tail",),
    "leg": ("foot.L",),
    "hip": ("pelvis",),
    "waist": ("chest.tail",),
    "shoulder": ("upperarm.L", "upperarm.R"),
    "hand": ("hand.L.tail", "hand.R.tail"),
}
STRIKE_LIMB = ("thigh.L", "shin.L", "foot.L")
SUPPORT_LIMB = ("thigh.R", "shin.R", "foot.R")


def _point_peak_frame(samples, keys):
    """该段**世界空间**运动速度的峰值帧（mm/帧）。

    ★ 时序判据一律站世界空间：欧拉步长会被万向节放大（B05 实测 2.34×），
      峰值帧会被钉在表示法的伪影上，不是力量传导。
    """
    best_frame, best = None, -1.0
    for index in range(1, len(samples)):
        before, after = samples[index - 1], samples[index]
        worst = 0.0
        for key in keys:
            if key in before and key in after:
                worst = max(worst, (Vector(after[key]) - Vector(before[key])).length)
        if worst > best:
            best, best_frame = worst, after["frame"]
    return best_frame, round(best * 1000.0, 3)


def _step_deg(samples, index):
    before, after = samples[index]["euler"], samples[index + 1]["euler"]
    worst = 0.0
    for name in set(before) | set(after):
        ea = before.get(name, (0.0, 0.0, 0.0))
        eb = after.get(name, (0.0, 0.0, 0.0))
        worst = max(worst, max(abs(a - b) for a, b in zip(ea, eb)))
    return worst


def low_assertions(arm, action, samples, idle_mats, sole, ankles, reach,
                   target_err):
    res = {}
    pelvis = [Vector(s["pelvis"]) for s in samples]
    attack = [Vector(s["foot." + ATTACK]) for s in samples]      # 攻击踝（世界）
    support = [Vector(s["foot." + SUPPORT]) for s in samples]    # 支撑踝（世界）
    hip_a = [Vector(s["thigh." + ATTACK]) for s in samples]
    chest_tail = [Vector(s["chest.tail"]) for s in samples]

    # 0b) 地面接触**定位诊断**：通用门禁只给一个数，这里给出"哪一帧、多低、整条曲线"。
    lows = [(min(s["low"]["L"], s["low"]["R"]) * 1000.0, s["frame"]) for s in samples]
    res["ground_min_mm_detail"] = round(min(v for v, _ in lows), 3)
    res["ground_min_frame"] = min(lows)[1]
    res["ground_series_mm"] = [round(v, 2) for v, _ in lows]

    # 0) **首帧逐位 = `Idle_01@0`**（世界矩阵）；末帧**允许不回 idle**。
    m0 = CR.action_world_matrices(arm, action, 0)
    mN = CR.action_world_matrices(arm, action, TOTAL)
    d0, dN = CR.matrix_delta(m0, idle_mats), CR.matrix_delta(mN, idle_mats)
    res["first_frame_delta"] = float("%.3e" % d0)
    res["last_frame_delta"] = float("%.3e" % dN)
    res["guard_start_ok"] = bool(d0 <= 1e-6)
    res["end_pose_switched_ok"] = bool(dN > 1e-3)
    res["end_pose_note"] = ("B06 是单发普通攻击：首帧仍须逐位 = Idle_01@0（起手不闪），"
                            "末帧**停在自持的「收势」姿态**（收腿落地站稳，骨盆仍沉 40 mm）")

    # 1) **末帧保持**：末 4 帧姿态变化 ≤2°。
    hold = [round(_step_deg(samples, i), 4)
            for i in range(len(samples) - 5, len(samples) - 1)]
    res["end_hold_steps_deg"] = hold
    res["end_pose_hold_ok"] = bool(max(hold) <= 2.0 and dN > 1e-3)

    # 2) **`chamber_ok`**（取代 B05 的 `raise_window_ok`）：
    #    踢腿的前摇是"**抬腿前引**"，不是"举拳" ⟹ 窗口 **[1, ANTIC_END]**、
    #    量**攻击膝**的 z 抬升（膝 = `shin.<攻击侧>.head`）。
    #    ★ 窗口从 f1 起（不含 f0）：B03 已记「窗口含 f0 且 f0 按定义 = 0 ⟹
    #      任何前摇都被判"没蓄力"」的陷阱。
    knee_a = [Vector(s["shin." + ATTACK]) for s in samples]
    window = range(1, ANTIC_END + 1)
    knee_z0 = knee_a[0].z * 1000.0
    knee_peak = max(knee_a[i].z for i in window) * 1000.0
    res["chamber_window_frames"] = ANTIC_END
    res["chamber_knee_z_guard_mm"] = round(knee_z0, 1)
    res["chamber_knee_z_peak_mm"] = round(knee_peak, 1)
    res["chamber_knee_rise_mm"] = round(knee_peak - knee_z0, 1)
    res["chamber_ankle_z_peak_mm"] = round(
        max(attack[i].z for i in window) * 1000.0, 1)
    res["chamber_ok"] = bool(ANTIC_END >= 8
                             and knee_peak - knee_z0 >= CHAMBER_RISE_MIN_MM)

    # 3) **`support_foot_pinned_ok`**（本支核心）：**支撑脚**踝位移 ≤3 mm +
    #    支撑脚鞋底 −2~+6 mm。**攻击腿不参与这条判据**（离地自由）。
    sup_travel = max((support[i] - support[0]).length
                     for i in range(len(support))) * 1000.0
    sup_sole = [sole[i][SUPPORT] * 1000.0 for i in range(len(sole))]
    res["support_ankle_travel_mm"] = round(sup_travel, 4)
    res["support_sole_series_mm"] = [round(v, 2) for v in sup_sole]
    res["support_sole_min_mm"] = round(min(sup_sole), 2)
    res["support_sole_max_mm"] = round(max(sup_sole), 2)
    res["support_foot_pinned_ok"] = bool(sup_travel <= 3.0
                                         and -2.0 <= min(sup_sole)
                                         and max(sup_sole) <= 6.0)
    res["support_foot_note"] = ("这是本清单**第一支单腿支撑动画**：B04/B05 的"
                                "`no_foot_slide` 是「双脚都不动」，本支拆两侧写 ——"
                                " 支撑脚 ≤3 mm + 鞋底 −2~+6，攻击腿**不进**判据。")

    # 4) **`low_height_ok`**（"攻击高度明确低于腰部"）：
    #    ① 命中帧攻击踝世界 z ≤ 骨盆 z − 250；② 全程攻击踝最高点 < 大腿中部
    #    （大腿中部 = 命中帧**支撑腿**髋膝中点的高度；「腰部」以骨盆世界 z 为基准）。
    hit_pelvis_z = pelvis[HIT].z * 1000.0
    hit_foot_z = attack[HIT].z * 1000.0
    ceiling = hit_pelvis_z - LOW_HEIGHT_MARGIN_MM
    thigh_mid = (Vector(samples[HIT]["thigh." + SUPPORT]).z
                 + Vector(samples[HIT]["shin." + SUPPORT]).z) * 500.0
    res["hit_pelvis_z_mm"] = round(hit_pelvis_z, 1)
    res["hit_foot_z_mm"] = round(hit_foot_z, 1)
    res["hit_z_ceiling_mm"] = round(ceiling, 1)
    res["hit_z_margin_mm"] = round(ceiling - hit_foot_z, 1)
    res["attack_foot_max_z_mm"] = round(max(p.z for p in attack) * 1000.0, 1)
    res["thigh_mid_z_mm"] = round(thigh_mid, 1)
    res["hit_z_below_b05_mm"] = round(hit_foot_z - B05_HIT_Z_MM, 1)
    res["hit_point_m"] = [round(v, 4) for v in samples[HIT]["foot." + ATTACK]]
    res["low_height_ok"] = bool(hit_foot_z <= ceiling
                                and max(p.z for p in attack) * 1000.0 <= thigh_mid)

    # 5) **`leg_amplitude_ok`**：攻击脚世界行程（**弧长**，计划原文"踢击弧长"）
    #    ≥600 mm **且** 以髋为轴的累计转角 ≥70°。
    #    ★ 两条都报：弧长（逐帧位移之和）与**弦长**（相对首帧的最大位移）。
    path = sum((attack[i] - attack[i - 1]).length
               for i in range(1, len(attack))) * 1000.0
    chord = max((p - attack[0]).length for p in attack) * 1000.0
    sweep, prev = 0.0, None
    for i in range(0, HIT + 1):
        d = attack[i] - hip_a[i]
        if d.length < 1e-9:
            continue
        d = d.normalized()
        if prev is not None:
            sweep += math.degrees(prev.angle(d))
        prev = d
    res["leg_path_len_mm"] = round(path, 1)
    res["leg_travel_chord_mm"] = round(chord, 1)
    res["leg_travel_min_mm"] = TRAVEL_MIN_MM
    res["hip_sweep_deg"] = round(sweep, 2)
    res["hip_sweep_min_deg"] = HIP_SWEEP_MIN_DEG
    res["leg_amplitude_ok"] = bool(path >= TRAVEL_MIN_MM
                                   and sweep >= HIP_SWEEP_MIN_DEG)

    # 6) **`upper_body_balance_ok`**（本支独有）：踢腿时上身**必须反向配重**。
    #    ★★ 判据站**世界空间/物理方向**，不站欧拉符号 —— 这是 B05 第 1 件的直接复用：
    #       `thigh.L` 在抬腿段带着 ry/rz，欧拉 rx 不再是"腿摆到哪"的干净尺子；
    #       首版用欧拉 rx 得出 `d_leg = +10.06`（判"腿在向后摆"），但**同一份报告**里
    #       攻击踝的 y 从 −119.6 走到 −689.6（**向前 570 mm**）—— 自相矛盾 ⟹ 尺子坏了。
    #    腿的物理摆向 = 髋→踝 的**矢状分量** `(踝.y − 髋.y)`；上身仰角 = 骨盆→胸骨顶
    #       的矢状仰角 `atan2(Δy, Δz)`。两者都照实报出，欧拉值只作诊断。
    def _rx(sample, name):
        return sample["euler"].get(name, (0.0, 0.0, 0.0))[0]

    trunk_rel = [_rx(s, "spine_01") + _rx(s, "spine_02") + _rx(s, "chest")
                 for s in samples]

    def _leg_sag(index):                       # 髋→踝 的 y 分量（米）
        return attack[index].y - hip_a[index].y

    def _trunk_lean(index):                    # 骨盆→胸骨顶 的矢状仰角（度），+ = 后仰
        base = pelvis[index]
        top = chest_tail[index]
        return math.degrees(math.atan2(top.y - base.y, top.z - base.z))

    sag0, sag1 = _leg_sag(CHARGE_END), _leg_sag(HIT)
    lean0, lean1 = _trunk_lean(CHARGE_END), _trunk_lean(HIT)
    d_leg_phys = (sag1 - sag0) * 1000.0        # < 0 = 腿向前摆
    d_trunk_phys = lean1 - lean0               # > 0 = 上身向后仰
    res["balance_window_clock"] = [CHARGE_END, HIT]
    res["balance_leg_sag_mm"] = [round(sag0 * 1000.0, 1), round(sag1 * 1000.0, 1)]
    res["balance_leg_forward_mm"] = round(-d_leg_phys, 1)
    res["balance_trunk_lean_deg"] = [round(lean0, 2), round(lean1, 2)]
    res["balance_trunk_leans_back_deg"] = round(d_trunk_phys, 2)
    res["balance_leg_rx_delta_deg"] = round(
        _rx(samples[HIT], "thigh." + ATTACK)
        - _rx(samples[CHARGE_END], "thigh." + ATTACK), 2)
    res["balance_trunk_rx_delta_deg"] = round(trunk_rel[HIT] - trunk_rel[CHARGE_END], 2)
    res["balance_leg_swings_forward"] = bool(d_leg_phys < 0.0)
    res["balance_trunk_leans_back"] = bool(d_trunk_phys > 0.0)
    res["balance_trunk_rel_series_deg"] = [round(v, 2) for v in trunk_rel]
    res["balance_measure"] = ("物理量：腿 = 髋→踝矢状分量（前移 mm）；"
                              "上身 = 骨盆→胸骨顶矢状仰角（后仰 deg）。"
                              "欧拉 rx 只作诊断（受 ry/rz 污染）")
    res["upper_body_balance_ok"] = bool(d_leg_phys < 0.0 and d_trunk_phys > 0.0
                                        and abs(d_trunk_phys) >= BALANCE_MIN_DEG)

    # 7) **`body_follow_through_ok`**：通道换成 **−rx（后仰量）**（本支是"上身继续后仰
    #    打透"，与 B05 的"前折"方向相反）；时窗与 `follow_s` 的相位对齐
    #    （`follow_s` 在 clock 20→25 由 0 升到 1，clock = frame − HOLD ⟹ 峰值落在 f28）。
    ft_lo, ft_hi = HIT + HOLD + 1, FOLLOW_END + HOLD          # [24, 28]
    ft = {}
    for bone in ("chest", "pelvis"):
        series = [-_rx(s, bone) for s in samples]
        peak = max(series[ft_lo:ft_hi + 1])
        ft[bone] = [round(series[HIT], 2), round(peak, 2),
                    round(peak - series[HIT], 2)]
    res["follow_through_deg"] = ft
    res["follow_through_window"] = [ft_lo, ft_hi]
    res["follow_through_channel"] = "−rx（后仰量；踢腿的打透 = 上身继续后仰）"
    res["body_follow_through_ok"] = bool(ft["chest"][2] >= 3.0
                                         and ft["pelvis"][2] >= 3.0)

    # 8) **`knee_drop_ok`**（改口径）：支撑腿**屈膝下沉 ≥40 mm** + 骨盆 XY ≤120 mm
    #    + **支撑脚**全程 ≤3 mm（攻击腿不参与）。
    z0 = pelvis[0].z
    drop = (z0 - min(p.z for p in pelvis)) * 1000.0
    span_xy = max(math.hypot(p.x - pelvis[0].x, p.y - pelvis[0].y)
                  for p in pelvis) * 1000.0
    bend = CR.knee_series(arm, action, [s["frame"] for s in samples])
    res["pelvis_drop_mm"] = round(drop, 2)
    res["pelvis_xy_span_mm"] = round(span_xy, 3)
    res["support_knee_bend_span_deg"] = round(
        max(b[SUPPORT] for b in bend) - min(b[SUPPORT] for b in bend), 2)
    res["attack_knee_bend_span_deg"] = round(
        max(b[ATTACK] for b in bend) - min(b[ATTACK] for b in bend), 2)
    res["knee_drop_ok"] = bool(drop >= 40.0 and span_xy <= 120.0
                               and sup_travel <= 3.0)
    res["knee_drop_note"] = ("口径改：门槛由 B05 的 60 mm 降到 **40 mm**"
                             "（单腿支撑的下沉空间小，计划原文指定）；"
                             "但**多了一条**——只许支撑脚下沉、攻击脚自由，"
                             "骨盆 XY ≤120 mm 与 B05 同。")

    # 9) **打击停顿 4 帧**（冻结判据的数值地板 1e-3，B04 第 6 件）。
    FROZEN_EPS_DEG = 1e-3
    steps, cursor = 0, HIT
    while cursor + 1 <= HIT + HOLD:
        if _step_deg(samples, cursor) > FROZEN_EPS_DEG:
            break
        steps += 1
        cursor += 1
    res["hitstop_frozen_steps"] = steps
    res["hitstop_frames"] = steps + 1
    res["hitstop_window"] = [HIT, HIT + HOLD]
    res["hitstop_present"] = bool(steps + 1 == HOLD + 1)

    # 10) **可取消帧**：f30 有 marker，且该帧攻击脚确在**回收路径**上。
    #     ★ 口径改：B05 量的是"拳峰相对肩的伸展量"，而踢腿在 guard 时髋→踝**本来
    #       就接近腿长**（0.771 / 0.822），那个量在收招时反而变小 ⟹ 换成本支真正
    #       单调的量：**攻击脚的前伸量** `−(踝 y)`（guard < cancel < hit）。
    markers = {m.name: int(m.frame) for m in action.pose_markers}
    res["markers"] = markers
    fwd = [-p.y for p in attack]
    res["cancel_reach_mm"] = [round(fwd[0] * 1000.0, 1),
                              round(fwd[HIT] * 1000.0, 1),
                              round(fwd[CANCEL] * 1000.0, 1)]
    res["cancel_marker_ok"] = bool(markers.get("CANCEL") == CANCEL
                                   and fwd[0] < fwd[CANCEL] < fwd[HIT])

    # 11) 腿部 |Y| / 伸展率健康度（体检项，**不当门禁** —— B03/B04 的结论）。
    max_y = max(max(abs(samples[i]["euler"].get(b, (0., 0., 0.))[1])
                    for b in ARM6 + LEG6) for i in range(len(samples)))
    res["max_abs_euler_y_deg"] = round(max_y, 2)
    res["euler_y_is_health_check_only"] = True

    # 12) **六段力量传导**（口径见文件头第 2 件）。
    #     同物理量的两段（foot / leg）严格 > B05；其余四段只要求非退化。
    ranges, peaks_seg = {}, {}
    for segment, bones in SEGMENTS.items():
        ranges[segment] = round(L1._euler_range(samples, bones), 3)
        peaks_seg[segment] = _point_peak_frame(samples, SEGMENT_POINTS[segment])[0]
    strike_range = round(L1._euler_range(samples, STRIKE_LIMB), 3)
    support_range = round(L1._euler_range(samples, SUPPORT_LIMB), 3)
    res["power_chain_ranges_deg"] = ranges
    res["power_chain_b05_ranges_deg"] = B05_SEGMENT_RANGES
    res["power_chain_same_quantity_as_b05"] = list(B05_SAME_QUANTITY)
    res["power_chain_vs_b05"] = {
        k: round(ranges[k] - B05_SEGMENT_RANGES[k], 2) for k in ranges}
    res["power_chain_over_b05"] = {k: bool(ranges[k] > B05_SEGMENT_RANGES[k])
                                   for k in B05_SAME_QUANTITY}
    res["strike_limb_range_deg"] = strike_range
    res["support_limb_range_deg"] = support_range
    res["strike_dominates_support"] = bool(strike_range > support_range * 1.5)
    res["power_chain_all_segments_alive"] = {
        k: bool(ranges[k] >= 3.0) for k in ranges}
    # ★ 注意：这是**全程**峰值帧（含收招段），**诊断用、不是判据**。
    #   骨盆的全程速度峰在 f29（收招初期把 95 mm 下沉拉回来，那是"回收"不是"发力"）
    #   ⟹ 判据必须用下面的 `timing_peak_frames`（窗口 [0, HIT+HOLD] 内）。
    res["power_chain_peak_frames_all_range_diagnostic"] = peaks_seg
    res["power_chain_note"] = ("B06 是**踢腿**：驱动肢体是腿，`hand` 段不可能翻到 "
                               "B05 的 137.43°（那是锤击手腕的行程）。照 B04→B05 的"
                               "先例「口径跟着动作类型走」：**foot / leg 两段（与 B05 "
                               "同一物理量）仍严格要求 > B05**，其余四段改为"
                               "非退化 + 时序 + 攻击肢体占优。六段数值全部照实列出。")

    # 12b) **时序**（站世界空间，B05 第 1 件的口径）：发力窗口 [0, HIT+HOLD] 内，
    #   攻击肢体按**近端→远端**依次达峰（骨盆 → 膝 → 踝 → 脚尖），且**攻击踝**的
    #   速度峰值必须落在命中帧附近（踢击本身就得是全程最快的一段）。
    #   ★ 首版直接拿 6 段 `SEGMENT_POINTS` 的峰值帧排序，报 `leg`=f9 / `hip`=f29
    #     而判红。根因不是动作错，是**窗口错**：骨盆速度峰值出现在 **收招段**
    #     （settle 的缓出把下沉 95 mm 拉回来，最快在恢复初期），那是"回收"不是
    #     "发力"。口径收紧为"只在本动作的**发力窗口**内取峰值 + 按肢体链排序"，
    #     **不是放宽容差**（窗口与顺序都是照 §6 力量传导链写的）。
    def _peak_in(keys, lo, hi):
        best_frame, best = None, -1.0
        for index in range(1, len(samples)):
            frame = samples[index]["frame"]
            if not (lo <= frame <= hi):
                continue
            worst = 0.0
            for key in keys:
                if key in samples[index - 1] and key in samples[index]:
                    worst = max(worst, (Vector(samples[index][key])
                                        - Vector(samples[index - 1][key])).length)
            if worst > best:
                best, best_frame = worst, frame
        return best_frame, round(best * 1000.0, 2)

    win_lo, win_hi = 0, HIT + HOLD
    p_pelvis = _peak_in(("pelvis",), win_lo, win_hi)
    p_knee = _peak_in(("shin." + ATTACK,), win_lo, win_hi)
    p_ankle = _peak_in(("foot." + ATTACK,), win_lo, win_hi)
    p_toe = _peak_in(("foot." + ATTACK + ".tail",), win_lo, win_hi)
    res["timing_window"] = [win_lo, win_hi]
    res["timing_peak_frames"] = {"pelvis": p_pelvis[0], "knee": p_knee[0],
                                 "ankle": p_ankle[0], "toe": p_toe[0]}
    res["timing_peak_speed_mm_per_frame"] = {"pelvis": p_pelvis[1],
                                             "knee": p_knee[1],
                                             "ankle": p_ankle[1],
                                             "toe": p_toe[1]}
    timing = (p_pelvis[0] <= p_ankle[0]
              and p_knee[0] <= p_ankle[0]
              and p_ankle[0] <= p_toe[0] + 1
              and HIT - 3 <= p_ankle[0] <= HIT + 1)
    res["power_chain_timing_measure"] = (
        "世界空间速度峰值帧（欧拉步长会被万向节放大，不作时序尺子）；"
        "窗口 = [0, HIT+HOLD]（只取发力段，排除收招段的速度峰）；"
        "顺序 = 骨盆 ≤ 膝 ≤ 踝 ≤ 脚尖，且踝峰落在 [HIT−3, HIT+1]")
    res["power_chain_timing_ok"] = bool(timing)
    res["power_chain_ok"] = bool(timing
                                 and res["strike_dominates_support"]
                                 and all(ranges[k] > B05_SEGMENT_RANGES[k]
                                         for k in B05_SAME_QUANTITY)
                                 and all(ranges[k] >= 3.0 for k in ranges))

    # 12b) **诊断**：逐骨逐通道 euler 幅度。
    limb_ranges = {}
    for name in ARM6 + LEG6:
        vals = [[s["euler"].get(name, (0.0, 0.0, 0.0))[ch] for s in samples]
                for ch in range(3)]
        limb_ranges[name] = [round(max(v) - min(v), 2) for v in vals]
    res["limb_euler_ranges_deg"] = limb_ranges
    res["limb_euler_range_max"] = round(max(max(v) for v in limb_ranges.values()), 3)
    res["limb_euler_range_max_at"] = max(
        ((max(v), n, "xyz"[v.index(max(v))]) for n, v in limb_ranges.items()))

    # 13) **收招不许瞬停**：末 6 帧最大欧拉增量单调收敛 + 峰值锁在命中帧。
    deltas, tail_bones = [], []
    for index in range(len(samples) - 6, len(samples)):
        before, after = samples[index - 1]["euler"], samples[index]["euler"]
        worst_step, worst_bone = 0.0, None
        for name in set(before) | set(after):
            ea = before.get(name, (0.0, 0.0, 0.0))
            eb = after.get(name, (0.0, 0.0, 0.0))
            step = max(abs(a - b) for a, b in zip(ea, eb))
            if step > worst_step:
                worst_step, worst_bone = step, name
        deltas.append(round(worst_step, 5))
        tail_bones.append(worst_bone)
    res["tail_deg_per_frame"] = deltas
    res["tail_worst_bone"] = tail_bones
    res["decel_smooth_ok"] = bool(all(deltas[i + 1] <= deltas[i] + 1e-9
                                      for i in range(len(deltas) - 1)))
    res["no_snap_stop_ok"] = bool(deltas[-1] <= 5.0 and deltas[-1] <= deltas[0])

    peak_frame, peak_val = L1._peak_frame(samples, ARM6 + LEG6)
    res["limb_peak_step_frame"] = peak_frame
    res["limb_peak_step_deg"] = peak_val
    res["recover_first_step_deg"] = round(_step_deg(samples, HIT + HOLD), 3)
    res["burst_last_step_deg"] = round(_step_deg(samples, HIT - 1), 3)
    res["no_teleport_budget_left_deg"] = round(25.0 - peak_val, 3)

    # 14) IK 到位 / 腿可达余量 / 膝（体检）。
    res["ankle_target_error_mm"] = round(target_err * 1000.0, 3)
    res["ik_reach_ok"] = bool(target_err * 1000.0 <= 5.0)
    limit = A.L_THIGH + A.L_SHIN
    res["leg_reach_max_mm"] = {s: round(max(r[s] for r in reach) * 1000.0, 1)
                               for s in SIDES}
    res["leg_reach_headroom_mm"] = {
        s: round((limit - max(r[s] for r in reach)) * 1000.0, 1) for s in SIDES}
    res["leg_reach_ok"] = bool(all(limit - max(r[s] for r in reach) >= 0.0
                                   for s in SIDES))
    res["leg_extension_max"] = {
        s: round(max(r for side, r in REACH if side == s), 4) for s in SIDES}

    # 15) 攻击元数据登记。
    res["antic_frame"] = ANTIC_END
    res["hit_frame"] = HIT
    res["cancel_frame"] = CANCEL
    res["hitstop_frame_span"] = [HIT, HIT + HOLD]
    return res


# =============================================================== 主流程
O_ARM_GUARD = {}
POLE_ARM = {}


def main():
    global ANKLE_REST, IDLE_POSE, POLE_LEG, O_ARM_GUARD, POLE_ARM

    arm, meshes = A.open_animation_project()
    A.setup_scene()

    if "Idle_01" not in bpy.data.actions:
        print("LOW06_BOOTSTRAP 动画工程缺 Idle_01，先补跑 A01")
        I1.main()
        arm, meshes = A.open_animation_project()
        A.setup_scene()

    # ---- 定盘数：一律从 `Idle_01@0` 成品姿态读，不手抄。
    IDLE_POSE = I1.idle_pose(arm, 0.0)
    ANKLE_REST = {side: Vector(A.bone_world(arm, "foot." + side, "head"))
                  for side in SIDES}
    POLE_LEG = {side: _leg_pole_from_pose(arm, side) for side in SIDES}
    POLE_ARM = {side: (None, ) for side in SIDES}
    POLE_ARM = {}
    fist_guard = {s: Vector(A.bone_world(arm, "hand." + s, "tail")) for s in SIDES}
    shoulder_guard = {s: Vector(A.bone_world(arm, "upperarm." + s, "head"))
                      for s in SIDES}
    O_ARM_GUARD = {s: fist_guard[s] - shoulder_guard[s] for s in SIDES}

    def _pole_arm(side):
        up = Vector(A.bone_world(arm, "upperarm." + side, "head"))
        elbow = Vector(A.bone_world(arm, "upperarm." + side, "tail"))
        wrist = Vector(A.bone_world(arm, "forearm." + side, "tail"))
        delta = wrist - up
        axis = delta.normalized() if delta.length > 1e-9 else Vector((0.0, -1.0, 0.0))
        bulge = (elbow - up) - axis * (elbow - up).dot(axis)
        return tuple(bulge.normalized())

    POLE_ARM = {side: _pole_arm(side) for side in SIDES}
    knee_guard = {s: Vector(A.bone_world(arm, "shin." + s, "head")) for s in SIDES}

    A.report("LOW06_IDLE_TRUTH", {
        "support": SUPPORT, "attack": ATTACK,
        "front_foot": "L" if ANKLE_REST["L"].y < ANKLE_REST["R"].y else "R",
        "ankle_mm": {s: [round(v * 1000.0, 2) for v in ANKLE_REST[s]] for s in SIDES},
        "knee_mm": {s: [round(v * 1000.0, 1) for v in knee_guard[s]] for s in SIDES},
        "pelvis_z_mm": round(Vector(A.bone_world(arm, "pelvis", "head")).z * 1000.0, 1),
        "thigh_mid_z_mm": {s: round((Vector(A.bone_world(arm, "thigh." + s, "head")).z
                                     + knee_guard[s].z) * 500.0, 1) for s in SIDES},
        "leg_pole_mm": {s: [round(v * 1000.0, 1) for v in POLE_LEG[s]] for s in SIDES},
        "arm_guard_offset_mm": {s: [round(v * 1000.0, 1) for v in O_ARM_GUARD[s]]
                                for s in SIDES},
        "leg_units_mm": round((A.L_THIGH + A.L_SHIN) * 1000.0, 1),
        "idle_hip_ankle_mm": {s: round((ANKLE_REST[s]
                                        - Vector(A.bone_world(arm, "thigh." + s, "head"))
                                        ).length * 1000.0, 1) for s in SIDES},
        "note": ("下段攻击：**前腿（L）低踢**、后腿（R）单腿支撑。"
                 "支撑腿在髋后面 140 mm ⟹ 骨盆下沉 + 后移对它都是安全方向。"),
    })

    # ---- 正式生成：首帧整帧取 `Idle_01@0`，其后逐帧 IK 构造。
    #      ★★ 沿用 B04 第 1 件：**不覆写 `JS.Y_SAFE` / `JS.ROLL_COMFORT`**，用库默认。
    #      ★★ 本支第一次把 `aim_carry` 用在**腿**上：thigh/shin/foot 必须一并播种。
    JS._PREV_EULER.clear()
    for name, value in IDLE_POSE.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)
    JS.ARM_QUAT.clear()
    JS.ARM_ROLL.clear()
    JS.ROLL_MAX.clear()
    for name in ARM6 + LEG6:
        JS.ARM_QUAT[name] = arm.pose.bones[name].matrix.to_quaternion()
    del TARGETS[:]
    del TRACE[:]
    del REACH[:]
    del POLE_SIN[:]
    _BULGE_PREV.clear()
    _FROZEN_POSE.clear()

    keyframes = [(0, IDLE_POSE)]
    for frame in range(1, TOTAL + 1):
        keyframes.append((frame, build_pose(arm, frame, record=True)))

    euler_y = {b: max(abs(row["euler"][b][1]) for row in TRACE)
               for b in ARM6 + LEG6}
    A.report("LOW06_LIMB_EULER", {
        "max_abs_euler_y_deg": round(max(euler_y.values()), 2),
        "per_bone_y_deg": {k: round(v, 1) for k, v in euler_y.items()},
        "max_roll_deg": {k: round(JS.ROLL_MAX.get(k, 0.0), 1) for k in ARM6 + LEG6},
        "max_extension_ratio": {
            s: round(max(r for side, r in REACH if side == s), 4) for s in SIDES},
        "note": ("腿 = `leg_aim`（3D 瞄准式双骨 IK + `_knee_bulge` 接力 + `aim_carry`）。"
                 "搜索旋钮用库默认，`no_teleport` 说话"),
    })

    meta = {
        "anim_id": NAME,
        "loop": False,
        "category": "普通攻击",
        "note": ("下段攻击（前腿低踢）：攻击腿后压 220 mm 做反向预备 → 抬腿前引"
                 "（膝抬到 z≈690 mm）→ 小腿甩出（hit_frame 20，命中踝 z ≈425 mm，"
                 "**低于腰线 290 mm**）→ 上身反向配重并继续后仰打透 → "
                 "f20~f23 冻结 4 帧 → 收腿落地停在自持「收势」（末帧不回 idle）"),
        "antic_frame": ANTIC_END,
        "hit_frame": HIT,
        "cancel_frame": CANCEL,
        "follow_frame": FOLLOW_END,
        "burst_span_clock": [BURST_START, HIT],
        "hitstop_frames": HOLD + 1,
        "hitstop_span": [HIT, HIT + HOLD],
        "motion_clock_hold_frames": HOLD,
        "strike_style": "front_leg_low_kick",
        "support_leg": SUPPORT,
        "attack_leg": ATTACK,
        "root_motion_m": [0.0, 0.0],
        "root_motion_note": ("**原地**（清单 §0.4：普通攻击不许 Root Motion，C 族起才允许）。"
                             "本支没有跨步，只有骨盆下沉 + 20 mm 后移；引擎位移由程序控制"),
        "support_foot_pinned": {
            "ankle_travel_mm": "≤3（支撑脚 R 全程钉死）",
            "sole_mm": "−2~+6（鞋底贴地）",
            "attack_leg_excluded": "攻击腿 L **不进**这条判据（离地自由）",
            "why": "本清单第一支单腿支撑动画：B04/B05 的 no_foot_slide 是「双脚都不动」",
        },
        "low_height": {
            "rule": "命中帧攻击踝 z ≤ 骨盆 z − 250 mm，且全程攻击踝最高点 < 大腿中部",
            "pelvis_z_mm": 830.0,
            "pelvis_drop_mm": "115（命中帧骨盆 z 715 ⟹ 天花板 465）",
        },
        "leg_amplitude": {
            "path_len_mm": "≥600（踢击弧长，逐帧位移之和）",
            "chord_mm": "同时报出（相对首帧的最大位移）",
            "hip_sweep_deg": "≥70（以髋为轴的累计转角，到命中帧）",
        },
        "upper_body_balance": {
            "rule": ("腿向前摆（thigh.rx 变小）时上身必须向后仰"
                     "（spine_01+spine_02+chest 的 rx 变小），幅度 ≥8°"),
            "why": ("防「只有腿在动」的僵直感；对应 §6 力量传导链的「腰」段。"
                    "「反号」按**物理方向**取 —— 两者在世界 rx 上同号（都绕 +X 负向）"),
        },
        "knee_drop": {
            "pelvis_drop_mm": "≥40（单腿支撑下沉空间小，计划原文指定，比 B05 的 60 宽松）",
            "pelvis_xy_mm": "≤120",
            "support_foot_mm": "≤3",
        },
        "follow_through": {
            "window": [HIT + HOLD + 1, FOLLOW_END + HOLD],
            "peak_clock": FOLLOW_END,
            "channel": "−rx（后仰量；B05 用 +rx 是因为锤击是前折）",
            "why": ("f20~f23 是 4 帧完全冻结（clock 被夹在 20），"
                    "「命中后继续送」只能取冻结之后的窗口；"
                    "踢腿的打透 = 上身**继续后仰**（重心留在支撑腿上才能把腿送出去）"),
        },
        "phase_path": {
            "guard": 0, "load": LOAD_END, "chamber": CHARGE_END,
            "strike": HIT, "follow": FOLLOW_END, "end": RECOVER_END,
            "powers": {"load": LOAD_POW, "chamber": CHAMBER_POW,
                       "burst": BURST_POW, "follow": FOLLOW_POW,
                       "settle": SETTLE_POW},
            "why": ("每条通道 = `g + (ld−g)·load + (ch−ld)·chamber + (st−ch)·burst"
                    " + (fo−st)·follow + (en−fo)·settle`；相位标量精确饱和 ⟹ "
                    "clock 40~43 姿态逐位恒定（末 4 帧零变化）。"
                    "★ 只有 settle 是缓出 `1−(1−u)^p`，其余四个 `u^p` 加速"),
        },
        "power_chain_scale_note": (
            "B06 口径：foot / leg 两段（与 B05 同一物理量）**严格要求 > B05**"
            "（23.53 / 44.91）；其余四段（hip/waist/shoulder/hand）在 B05 里是"
            "锤击的躯干折叠与手腕翻转挣来的，与踢腿不是同一物理量 ⟹ 改为"
            "非退化（≥3°）+ 时序 + 攻击肢体占优（> 支撑腿 ×1.5）。"
            "**换尺子，不是放宽**：六段数值全部照实列出（power_chain_vs_b05）"),
        "link_prev": "Idle_01@0（**首帧**逐位相等；起手不闪）",
        "link_next": ("末帧 = 自持「收势」姿态（收腿落地站稳、骨盆仍沉 40 mm，不回 idle）"
                      "⟹ 可直接接后摇/硬直"),
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.set_hitstop(action, HIT, HIT + HOLD)
    A.add_markers(action, {
        "GUARD": 0, "ANTIC": 1, "LOAD_END": LOAD_END, "ANTIC_END": ANTIC_END,
        "HIT": HIT, "HITSTOP_END": HIT + HOLD, "RECOV": HIT + HOLD,
        "FOLLOW_END": FOLLOW_END, "CANCEL": CANCEL, "END": TOTAL,
    })

    # ★ 本支判据要读 **thigh / shin 的世界头点**（膝抬升、髋轴扫掠、大腿中部高度），
    #   而库默认 `PROBE_BONES` 只含上肢与足 ⟹ 采样前把腿骨并进探针表。
    #   （只动**本进程**的库全局，不改 `anim_lib.py` 文件；不影响其它支。）
    A.PROBE_BONES = tuple(A.PROBE_BONES) + tuple(
        b for b in ("thigh.L", "thigh.R", "shin.L", "shin.R")
        if b not in A.PROBE_BONES)
    samples = A.sample_animation(arm, action, 0, TOTAL, meshes)
    # 本支是**单腿支撑**：通用脚滑门禁只对**支撑脚**生效（攻击腿离地自由）。
    report = A.run_common_assertions(samples, meta, foot_probe=("toe." + SUPPORT,))
    idle_mats = CR.action_world_matrices(arm, bpy.data.actions["Idle_01"], 0)
    frames = list(range(0, TOTAL + 1))
    sole = JS.sole_series(arm, action, frames)
    ankles = JS.ankle_series(arm, action, frames)
    reach = JF.reach_series(arm, action, frames)
    target_err = 0.0
    pair = {(f, s): Vector(t) for f, s, t in TARGETS}
    for index, frame in enumerate(frames):
        for side in SIDES:
            if (frame, side) in pair:
                target_err = max(target_err, (Vector(ankles[index][side])
                                              - pair[(frame, side)]).length)
    report.update(low_assertions(arm, action, samples, idle_mats, sole,
                                 ankles, reach, target_err))
    report["meta"] = meta

    def _diff(before, after, top=6):
        rows = []
        for name in set(before) | set(after):
            ea = before.get(name, (0.0, 0.0, 0.0))
            eb = after.get(name, (0.0, 0.0, 0.0))
            for channel in range(3):
                rows.append((round(abs(ea[channel] - eb[channel]), 5),
                             name, "xyz"[channel],
                             round(ea[channel], 4), round(eb[channel], 4)))
        rows.sort(reverse=True)
        return [{"d": r[0], "bone": r[1], "axis": r[2],
                 "before": r[3], "after": r[4]} for r in rows[:top]]

    report["hitstop_probe"] = {
        "f%d_vs_f%d" % (HIT, HIT + 1): _diff(samples[HIT]["euler"],
                                             samples[HIT + 1]["euler"]),
    }
    report["tail_probe"] = [
        {"f": samples[i]["frame"], "top": _diff(samples[i - 1]["euler"],
                                                samples[i]["euler"], 3)}
        for i in range(len(samples) - 8, len(samples))]
    report["burst_probe"] = [
        {"f": row["frame"],
         "euler": {b: list(row["euler"][b]) for b in ARM6 + (LEG6 if False else ())},
         "roll": row["roll"]}
        for row in TRACE if 8 <= row["frame"] <= 26]
    report["pole_probe"] = [
        {"f": f, "side": side, "sin": round(s, 4)}
        for f, side, s in POLE_SIN if f <= 26]
    report["seg_probe"] = [
        {"f": samples[i]["frame"],
         **{seg: round(max(
             max(abs(samples[i - 1]["euler"].get(n, (0., 0., 0.))[c]
                     - samples[i]["euler"].get(n, (0., 0., 0.))[c])
                 for c in range(3))
             for n in bones), 2)
            for seg, bones in SEGMENTS.items()}}
        for i in range(1, len(samples))]
    report["skipped_gates"] = sorted(
        k for k, v in report.items() if v is None and k.endswith("_ok"))
    failed = sorted(k for k, v in report.items()
                    if (k.endswith("_ok")
                        or k in ("no_teleport", "hitstop_present"))
                    and v is not True and v is not None)
    report["failed"] = failed
    A.report("LOW06_REPORT", report)

    if not SKIP_RENDER:
        SIDE = ("side", (4.8, 0.0, 0.95), (0.0, 0.0, 0.95), 2.60, (780, 1160))
        FRONT = ("front", (0.0, -5.2, 0.95), (0.0, 0.0, 0.95), 2.60, (760, 1220))
        TOPQ = ("three_quarter", (3.4, -3.8, 1.05), (0.0, 0.0, 0.95), 2.60,
                (780, 1160))
        A.render_pose_sheet(arm, action,
                            [0, LOAD_END, 8, CHARGE_END, 14, 17, HIT, HIT + HOLD,
                             HIT + HOLD + 3, CANCEL, 34, TOTAL],
                            "low06", views=(SIDE,))
        A.render_pose_sheet(arm, action, [0, CHARGE_END, HIT, TOTAL], "low06",
                            views=(FRONT,))
        A.render_pose_sheet(arm, action, [CHARGE_END, HIT], "low06", views=(TOPQ,))
        A.save_project()
        A.export_glb(arm)
    print("LOW06_DONE failed=%s" % failed)


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("LOW06_FAILURE " + traceback.format_exc())
