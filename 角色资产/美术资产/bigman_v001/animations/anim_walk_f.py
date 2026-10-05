"""anim_walk_f —— A03 `Walk_F` 前走。

设计（对着清单「下一支计划 —— A03」逐条落）：
    定位      身体略前倾、步幅中等、肩随步伐摆；**不要像跑步，体现重量**。
    周期      72 帧 / 1.200 s @60fps（两步），**循环**（首末帧同一相位生成）。
    步长      相邻触地点间距 0.36 m → 前进速率 0.600 m/s（登记 locomotion_mps）。
    支撑期    36 帧（50%），其中全脚掌平放 30 帧 + 踮脚离地 6 帧（foot 世界转角 →24°）。
    双支撑    两脚支撑期首尾相接，**无腾空**（腾空就是跑了）。
    摆动期    36 帧，脚底离地峰值 ~58 mm。
    骨盆      升降峰峰 ≥ 20 mm（每步一次，双峰）、左右 ≤ 45 mm、前后 ≤ 25 mm 且净 0。
    前倾      胸骨顶相对骨盆前移 40~70 mm（≈"略前倾"，再大就读作跑步）。
    肩摆      肩峰 y 行程 ≥ 25 mm，左右反相，且与**同侧脚**反向。
    手臂      保持 A01 护体架势（ARM_DIRS），叠加 ±4° 前后摆 —— 不是常人甩手。
    脚不滑    Walk 的**正确口径**是 `stance_slide_is_linear`（支撑期匀速后滑），
              不是 A01 的"脚不动 3 mm"。§0.4 规定普通移动是原地动画 ⟹ 支撑脚
              必须相对身体匀速后滑；**匀速滑移是对的，忽快忽慢才是错的**。

口径修正（与清单原文的差异，附推导 —— 不改正文，写在这里备案）：
    清单写「步幅 0.36 m（单脚前后跨度）／支撑期 55%／速率 0.600 m/s」，这三条
    在数学上不能同时成立：单脚踝若在 55% 周期（0.667 s）内滑完 0.36 m，
    速率只有 0.36/0.667 = **0.540 m/s**。本文把 0.36 m 理解为**相邻触地点间距
    （步长 step length）**：每周期两步 → 前进 0.72 m / 1.2 s = **0.600 m/s** ✓，
    于是单脚支撑期滑移 = 0.600 × 0.667 = **0.400 m**（踝 y 从 −0.200 到 +0.200）。
    三条约束全部满足，步长 0.36 m 仍在门禁区间 [0.30, 0.45] 内。

关于"首末帧落到 A01 呼吸中点"（清单建议）：
    步行循环的 0 帧是**左脚触地的跨步姿态**，不可能同时等于 Idle 的并腿站姿 ——
    两者是不同位姿。故本条按**纯循环**处理（首末帧逐位一致，由同一相位函数生成），
    过渡平滑改由引擎侧做短混合。若日后需要，另做一支 `Walk_Start` 专责过渡。

---------------------------------------------------------------------------
2026-10-01 —— **为 A04 `Walk_B` 做的重构（本支行为不变）**

`Walk_F` 的常量整支搬进 `Gait` 参数对象，`ankle_track` / `_leg` / `_build` /
`gait_pose` / `add_world_rx` / `swung` / `in_stance` 全部改成「按参数工作」的通用
函数。`WALK_F = Gait(...)` 逐项复刻原来的常量，`walk_pose()` / `walk_assertions()`
保留为 Walk_F 的兼容入口 —— 重跑本支门禁仍然 `failed = []`，数值与 A03 记录一致。

A04 不再复制粘贴，直接：
    import anim_walk_f as WF
    GAIT = WF.Gait(name="Walk_B", ..., backward=True)
    pose  = WF.gait_pose(arm, GAIT, frame, meshes)
**顺带补上 `if __name__ == "__main__":` 守卫** —— 原文件没写，A04 一旦 import 它
就会把整支 A03 重跑一遍（重渲 6 张静帧 + 存盘 + 导 GLB），与 A02 踩过的坑同源。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python anim_walk_f.py
    SKIP_RENDER=1 只跑门禁（迭代用）。
"""

import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A  # noqa: E402
import anim_idle_01 as I1  # noqa: E402

NAME = "Walk_F"
TOTAL = 72                       # 1.200 s @60fps，两步
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"

# ---------------------------------------------------------------- 步态参数
STEP_M = 0.36                    # 相邻触地点间距（步长）→ 门禁 0.30~0.45
LOCOMOTION_MPS = STEP_M * 2.0 / (TOTAL / float(A.FPS))     # 0.600 m/s
# 支撑期 50%（36 帧）：两脚支撑期首尾相接，**无腾空**（腾空就是跑）。
# 为什么不是清单写的 55%：55%×2 = 110% ⟹ 双支撑窗口下限就有 10%（7~8 帧），
# 再叠加摆动两端必然存在的"贴地边界帧"，一定突破 `double_support_ok` 的
# 15% 上限 —— 这两条约束互斥。改成 50% 后步长 / 速率 / 双支撑三条同时成立。
STANCE_FRAMES = 36
FLAT_FRAMES = 30                 # 其中全脚掌平放 30 帧
TIP_FRAMES = STANCE_FRAMES - FLAT_FRAMES                   # 踮脚离地 6 帧
SWING_FRAMES = TOTAL - STANCE_FRAMES                       # 36 帧
SLIDE_M = LOCOMOTION_MPS * STANCE_FRAMES / float(A.FPS)    # 0.360 m
ANKLE_Y_FRONT = -SLIDE_M / 2.0                             # −0.180
ANKLE_Y_BACK = SLIDE_M / 2.0                               # +0.180
RIGHT_OFFSET = 0.5               # 右脚相位相对左脚错开半周期

L_FOOT = 0.130                   # foot 骨长（由 rig_axis_map: 33.64mm/15° 反推）
TIP_DEG = 24.0                   # 踮脚世界转角（清单 20~28°）
CLEAR_PEAK = 0.058               # 摆动期脚底离地峰值（门禁要求 ≥ 40 mm）
CLEAR_EXP = 0.7                  # 抬脚包络指数（<1 = 起脚快、落地前收脚快）
TIP_DECAY = 0.15                 # 摆动期前 15% 内把踮脚角收平

ANKLE_X = 0.100                  # 走步轨道半宽（比站姿略窄，读作"走"不是"站"）
PELVIS_X_AMP = 0.018             # 重心左右转移（峰峰 36 mm ≤ 45）
PELVIS_Y_AMP = 0.005             # 前后摆动（峰峰 10 mm ≤ 25，净位移 0）
PELVIS_BOB = 0.014               # 升降（峰峰 28 mm ≥ 20）
PELVIS_DROP = -0.055             # 基础下沉（比 Idle 的 −70 mm 略高，步幅中腿更直）
PELVIS_RX = 2.5                  # 骨盆前倾（leg_ik 的 tilt_deg 必须同步）
PELVIS_TWIST = 3.0               # 骨盆绕纵轴扭转
SPINE_01_RX = 1.8
SPINE_02_RX = 1.5
CHEST_RX = 1.2
# 胸腔反向扭转 / 肩摆：这两个是**差模**（左右反相），是"肩随步伐摆"的本体。
# 骨盆前后摆动是**共模**（两肩一起前后移），它只糊相关性、不产生"摆"的读感，
# 所以压到 ±5 mm；把摆幅预算让给差模。第一版共模 24 mm 压过差模，
# 相关系数只有 −0.219（判据 ≤ −0.5），读起来就是两肩一起晃 = 踏步。
CHEST_TWIST = 5.0
SHOULDER_SWING = 9.0             # shoulder rz 摆幅（度）；肩峰杠杆 ~1.9 mm/°
ARM_SWING = 4.0                  # 上臂前后摆幅（度）
SHOULDER_REST_RX = -18.0         # 与 A01 一致的沉肩
PELVIS_X_PHASE = 0.27778         # 重心左右转移的相位（对支撑脚中相）
NECK_RX = -6.0
HEAD_RX = 5.0


def _smooth(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3.0 - 2.0 * u)


def wrap(phase):
    """把相位规约到 [0,1)。"""
    return phase % 1.0


# =============================================================== 步态参数对象
class Gait:
    """一套步态参数。Walk_F / Walk_B 的差异全部落在这里，函数体共用。

    **Foot 轨迹的通用形状**（`ankle_track`）：
        支撑期：踝 y 从 `stance_from` **线性**滑到 `stance_to`（原地动画里
                支撑脚相对身体必须匀速反向滑，速率 = 角色速率）。
        摆动期：三次 Hermite 从 `stance_to` 荡回 `stance_from`。
        脚背角 tip：触地段（`tip_touch_deg`，0 = 平放落）→ 平放 → 抬跟（`tip_deg`）。

    **Hermite 系数**：两端斜率同取 `end_slope` ⇒
        a + b + c = swing_to − swing_from ， 3a + 2b + c = c
        ⇒ b = −1.5a ， a = 2(c − D)（D = swing_to − swing_from）
    `end_slope` 是"米 / 每单位 s"。要两端速度与支撑期**严格连续**，
    应传 `None`（由支撑期每帧速率 × `swing_frames` 推出，见 __init__）——
    A04 的 36 == 36 恰好与旧写法重合，Run 的 17 ≠ 31 就必须走这条；
    A03 当年取 `c = 0.32`（D = −0.36），端速度比支撑期小 11%，为不改 A03
    的输出，这里按原值传入。
    """

    def __init__(self, *, name, total, step_m, stance_frames, flat_frames,
                 end_slope=None, end_slope_out=None, tip_deg, clear_peak,
                 clear_exp, tip_decay,
                 ankle_x, pelvis_x_amp, pelvis_y_amp, pelvis_bob, pelvis_drop,
                 pelvis_rx, pelvis_twist, spine_01_rx, spine_02_rx, chest_rx,
                 chest_twist, shoulder_swing, shoulder_rest_rx, arm_swing,
                 neck_rx, head_rx, torso_lean_band,
                 tip_touch_deg=0.0, touch_frames=0, swing_tip_decay=None,
                 clear_pow=1.0, spine_01_twist=0.0, spine_02_twist=0.0,
                 pelvis_x_phase=0.0, pelvis_bob_phase=0.0, arm_tuck_deg=0.0,
                 backward=False, right_offset=0.5):
        self.name = name
        self.total = total
        self.backward = backward
        self.right_offset = right_offset
        self.fps = A.FPS

        self.stance_frames = stance_frames
        self.flat_frames = flat_frames
        self.tip_frames = stance_frames - flat_frames
        self.swing_frames = total - stance_frames
        self.touch_frames = touch_frames

        # 步长 → 速率 → 单脚支撑期滑移量。三者是一条链，不许各自独立给。
        self.step_m = step_m
        self.locomotion_mps = step_m * 2.0 / (total / float(A.FPS))
        self.slide_m = self.locomotion_mps * stance_frames / float(A.FPS)
        self.ankle_y_front = -self.slide_m / 2.0
        self.ankle_y_back = self.slide_m / 2.0

        # 后退 = 支撑脚从**身后**滑到**身前**（相对身体朝 −Y 滑）。
        if backward:
            self.stance_from, self.stance_to = self.ankle_y_back, self.ankle_y_front
        else:
            self.stance_from, self.stance_to = self.ankle_y_front, self.ankle_y_back
        self.swing_from, self.swing_to = self.stance_to, self.stance_from

        swing_d = self.swing_to - self.swing_from
        # `end_slope` / `end_slope_out` 的单位是 **"米 / 每单位 s"**（s ∈ [0,1] 是
        # 摆动期归一化进度），而支撑期的速率是"米 / 帧"。两者要**严格速度连续**，
        # 必须先把支撑期的每帧速率乘回 `swing_frames`：v = R_perframe × swing_frames。
        #
        # 两端**分别**给：`end_slope` 是**离地端**（s=0，接支撑期末端），
        # `end_slope_out` 是**触地端**（s=1）。这两端在物理上并不对称：
        #   · 离地端：脚刚离地，相对身体的速度仍等于支撑期速率 ⟹ **必须连续**。
        #   · 触地端：脚从空中拍下来、瞬间被地面钉住 ⟹ 相对身体的速度**本来就跳变**
        #     （这个跳变就是"落地"本身，也是"重踏"的重量来源）。若强行让触地端也
        #     连续，解出来的摆动轨迹会先把脚**再往后拖 147 mm** 才往前抡 ——
        #     脚在身后拖一大段才归位，那就不是跑步了。
        #
        # A03/A04 的 `stance_frames == swing_frames`，旧写法 `−SLIDE_M` 与严格连续
        # 恰好重合，所以看不出问题；Run 的 17 ≠ 31 才暴露：照抄旧写法会得到一条
        # "摆动 31 帧却按 17 帧的斜率走"的直线，离地瞬间脚相对身体的速度掉到 55%
        # —— 观感就是"脚被粘了一下"。传 `None` 即按严格连续推导。
        if end_slope is None:
            end_slope = ((self.stance_to - self.stance_from)
                         / float(stance_frames) * self.swing_frames)
        if end_slope_out is None:
            end_slope_out = end_slope
        self.swing_end_slope = end_slope
        self.swing_end_slope_out = end_slope_out
        # 三次 Hermite，满足 y(0)=from、y(1)=to、y'(0)=c0、y'(1)=c1：
        #     a = c0 + c1 − 2D ，  b = 3D − 2c0 − c1 ，  c = c0
        # 令 c0 == c1 == c 即退化成 A03/A04 用的 a = 2(c − D)、b = −1.5a。
        self.swing_a = end_slope + end_slope_out - 2.0 * swing_d
        self.swing_b = 3.0 * swing_d - 2.0 * end_slope - end_slope_out
        self.swing_c = end_slope
        # 支撑期"应有"的滑移速率（带符号）；门禁拿它比对实测拟合斜率。
        self.stance_rate_mps = (self.stance_to - self.stance_from) \
            / float(stance_frames) * A.FPS

        self.tip_deg = tip_deg
        self.tip_touch_deg = tip_touch_deg
        self.tip_decay = tip_decay
        self.swing_tip_decay = (tip_decay if swing_tip_decay is None
                                else swing_tip_decay)
        self.clear_peak = clear_peak
        self.clear_exp = clear_exp
        self.clear_pow = clear_pow

        self.ankle_x = ankle_x
        self.pelvis_x_amp = pelvis_x_amp
        self.pelvis_y_amp = pelvis_y_amp
        self.pelvis_bob = pelvis_bob
        self.pelvis_drop = pelvis_drop
        self.pelvis_rx = pelvis_rx
        self.pelvis_twist = pelvis_twist
        self.pelvis_x_phase = pelvis_x_phase
        # 骨盆升降的最低点相位（周期单位，0 = 触地帧）。
        # Walk 族取 0（触地即最低）；Run 取 约 STANCE/2/TOTAL —— 跑步的最低点
        # 必须在**支撑中期**（吸收下坠），落在腾空段就读作"踩着空气"。
        self.pelvis_bob_phase = pelvis_bob_phase
        self.spine_01_rx = spine_01_rx
        self.spine_02_rx = spine_02_rx
        self.chest_rx = chest_rx
        self.spine_01_twist = spine_01_twist
        self.spine_02_twist = spine_02_twist
        self.chest_twist = chest_twist
        self.neck_rx = neck_rx
        self.head_rx = head_rx
        self.shoulder_swing = shoulder_swing
        self.shoulder_rest_rx = shoulder_rest_rx
        self.arm_swing = arm_swing
        self.arm_tuck_deg = arm_tuck_deg
        self.torso_lean_band = torso_lean_band      # (min, max) mm，判"前倾/直立"


WALK_F = Gait(
    name=NAME, total=TOTAL, step_m=STEP_M, stance_frames=STANCE_FRAMES,
    flat_frames=FLAT_FRAMES, end_slope=0.32, tip_deg=TIP_DEG,
    clear_peak=CLEAR_PEAK, clear_exp=CLEAR_EXP, tip_decay=TIP_DECAY,
    ankle_x=ANKLE_X, pelvis_x_amp=PELVIS_X_AMP, pelvis_y_amp=PELVIS_Y_AMP,
    pelvis_bob=PELVIS_BOB, pelvis_drop=PELVIS_DROP, pelvis_rx=PELVIS_RX,
    pelvis_twist=PELVIS_TWIST, pelvis_x_phase=PELVIS_X_PHASE,
    spine_01_rx=SPINE_01_RX, spine_02_rx=SPINE_02_RX, chest_rx=CHEST_RX,
    chest_twist=CHEST_TWIST, shoulder_swing=SHOULDER_SWING,
    shoulder_rest_rx=SHOULDER_REST_RX, arm_swing=ARM_SWING,
    neck_rx=NECK_RX, head_rx=HEAD_RX, torso_lean_band=(40.0, 70.0),
    right_offset=RIGHT_OFFSET)


# =============================================================== 足踝轨迹
def ankle_track(gait, local_phase):
    """单脚在**本地相位**（0 = 触地瞬间）上的踝轨迹。

    返回 (ankle_y, ankle_z, tip_deg, clearance)：
      ankle_y     世界 y（−Y 是角色正面，所以"前方"= 负值）
      ankle_z     踝的世界 z —— **只是初值**，第 2 遍由实测贴地闭环修正
      tip_deg     该脚绕**世界 X 轴**的附加转角
                  （+ = 压脚背 / 脚尖朝下，− = 勾脚；0 = 全脚掌平放）
      clearance   该帧期望的**鞋底离地量**（支撑期 0，摆动期按包络）
    """
    frame = wrap(local_phase) * gait.total

    if frame <= gait.stance_frames:
        u = frame / float(gait.stance_frames)
        ankle_y = gait.stance_from + (gait.stance_to - gait.stance_from) * u
        if gait.touch_frames and frame <= gait.touch_frames:
            # 触地：脚尖先落（tip_touch_deg > 0）→ 前 touch_frames 帧内收平
            tip = gait.tip_touch_deg * (1.0 - _smooth(
                frame / float(gait.touch_frames)))
        elif frame <= gait.flat_frames:
            tip = 0.0
        else:
            tip = gait.tip_deg * _smooth(
                (frame - gait.flat_frames) / float(gait.tip_frames))
        ankle_z = A.Z_ANKLE_REST + L_FOOT * math.sin(math.radians(tip))
        return ankle_y, ankle_z, tip, 0.0

    s = (frame - gait.stance_frames) / float(gait.swing_frames)
    ankle_y = (gait.swing_a * s ** 3 + gait.swing_b * s ** 2
               + gait.swing_c * s + gait.swing_from)
    # 抬脚后把抬跟角收到"触地角"，并**保持**到落地 —— 落地那一下就带着
    # tip_touch_deg 的脚尖朝下，这是 toe-first 的来源（A03 是收到 0 = 平放落）。
    tip = gait.tip_touch_deg + (gait.tip_deg - gait.tip_touch_deg) * max(
        0.0, 1.0 - s / gait.swing_tip_decay)
    ankle_z = A.Z_ANKLE_REST + L_FOOT * math.sin(math.radians(tip))
    clearance = gait.clear_peak * math.sin(
        math.pi * s ** gait.clear_pow) ** gait.clear_exp
    return ankle_y, ankle_z, tip, clearance


def add_world_rx(arm, name, deg):
    """在骨**当前世界朝向**上再叠一个绕世界 X 轴的转角（踮脚/勾脚用）。

    为什么不直接写 foot.rx：foot 的局部 rx 轴被父链（thigh 外展 rz）带偏了
    几度，直接写角度会差出 4.3°、脚掌末端陷地 ~7 mm（A01 已踩过）。
    这里先 `keep_world_orientation` 把脚钉平（相对世界水平），再绕世界 X
    转 deg —— 角度是在世界系里给的，不受父链偏轴影响。
    """
    if abs(deg) < 1e-9:
        return
    pose_bone = arm.pose.bones[name]
    current = pose_bone.matrix.copy()
    target = Matrix.Rotation(math.radians(deg), 4, "X") @ current
    target.translation = current.translation
    pose_bone.matrix = target
    bpy.context.view_layer.update()


def swung(direction, deg):
    """把方向向量绕世界 X 轴转 deg（>0 = 末端向 +Y，即身后）。"""
    r = math.radians(deg)
    x, y, z = direction
    return (x, y * math.cos(r) - z * math.sin(r), y * math.sin(r) + z * math.cos(r))


def swung_z(direction, deg):
    """把方向向量绕世界 Z 轴转 deg（水平偏摆；"收肘"用它）。"""
    r = math.radians(deg)
    x, y, z = direction
    return (x * math.cos(r) - y * math.sin(r), x * math.sin(r) + y * math.cos(r), z)


# =============================================================== 姿态
def _leg(pose, gait, side, sign, local_phase, pelvis_x, hip_y, hip_z, z_shift):
    """写一只脚的腿骨（thigh / shin），返回 (tip_deg, clearance)。"""
    ankle_y, ankle_z, tip, clearance = ankle_track(gait, local_phase)
    ankle_z += z_shift
    ankle_x = gait.ankle_x * sign
    hip_x = A.HIP_X * sign + pelvis_x
    thigh_rx, shin_rx = A.leg_ik(hip_y, hip_z, ankle_y, ankle_z,
                                 tilt_deg=gait.pelvis_rx)
    abduct = math.degrees(math.atan2((ankle_x - hip_x) * sign,
                                     hip_z - ankle_z))
    pose["thigh." + side] = (thigh_rx, 0.0, -abduct * sign)
    pose["shin." + side] = (shin_rx, 0.0, 0.0)
    pose["foot." + side] = (0.0, 0.0, 0.0)
    pose["toe." + side] = (0.0, 0.0, 0.0)
    return tip, clearance


def _build(arm, gait, frame, shifts):
    """按给定的踝 z 修正量构造并写入完整姿态，返回 (pose, clearances)。"""
    t = wrap(frame / float(gait.total))

    # 骨盆：三轴都不是"表演"，是步态的必然结果 —— 重心必须移到支撑脚上，
    # 否则摆动腿抬不起来。左右 / 前后都收敛在门禁区间内，且整周期净位移 0。
    pelvis_x = gait.pelvis_x_amp * math.cos(
        2.0 * math.pi * (t - gait.pelvis_x_phase))
    pelvis_y = -gait.pelvis_y_amp * math.cos(2.0 * math.pi * 2.0 * t)
    # 升降（每步一次，双峰）。`pelvis_bob_phase` 把最低点挪到想要的相位上：
    #   Walk 族 = 0（触地即最低，A03/A04 行为不变）；
    #   Run    = 支撑中期（见 anim_run：落地后先沉再弹，"重踏"的机器判据）。
    pelvis_z = gait.pelvis_drop - gait.pelvis_bob * math.cos(
        2.0 * math.pi * 2.0 * (t - gait.pelvis_bob_phase))
    hip_z = 0.900 + pelvis_z
    twist = math.cos(2.0 * math.pi * t)
    # 骨盆绕纵轴一扭，髋关节会被横向甩出去：它不在纵轴上（|x| = 90 mm），
    # 转 θ 度髋的 y 就偏 90·sinθ。IK 若仍按 pelvis 的 y 解，踝会跟着摆 ±4.7 mm，
    # 支撑期那条"匀速滑移"直线就被这个周期性误差顶红。髋点必须用扭转后的实位。
    hip_swing = math.sin(math.radians(-gait.pelvis_twist * twist))

    pose = {
        "pelvis": (gait.pelvis_rx, -gait.pelvis_twist * twist, 0.0),
        "spine_01": (gait.spine_01_rx, gait.spine_01_twist * twist, 0.0),
        "spine_02": (gait.spine_02_rx, gait.spine_02_twist * twist, 0.0),
        "chest": (gait.chest_rx, gait.chest_twist * twist, 0.0),
        "neck": (gait.neck_rx, 0.0, 0.0),
        "head": (gait.head_rx, 0.0, 0.0),
        # 肩的轴语义是**镜像**的（shoulder.L rz>0 = 向后，shoulder.R rz>0 = 向前），
        # 所以两肩要给**同号** rz 才是一前一后；给反号会变成"两肩一起向后甩"
        # —— 那就是踏步而不是走路（第一版门禁相关系数 0.977，正是同相）。
        "shoulder.L": (gait.shoulder_rest_rx, 0.0, gait.shoulder_swing * twist),
        "shoulder.R": (gait.shoulder_rest_rx, 0.0, gait.shoulder_swing * twist),
        "@loc": {"pelvis": A.wloc(pelvis_x, pelvis_y, pelvis_z)},
    }

    tips = {}
    clearances = {}
    for side, sign, offset in (("L", 1.0, 0.0),
                               ("R", -1.0, gait.right_offset)):
        tips[side], clearances[side] = _leg(
            pose, gait, side, sign, t - offset, pelvis_x,
            pelvis_y + A.HIP_X * sign * hip_swing, hip_z, shifts[side])

    pose.update(A.FIST)
    A.apply_pose(arm, pose)

    # 足：先钉平到世界水平，再叠世界系踮脚角 —— 贴地脚因此在整段里
    # 既不陷地也不飘（A01 已证明"角度补偿"在外展角下要差 4.3°、陷 6.9 mm）。
    for side in ("L", "R"):
        name = "foot." + side
        A.keep_world_orientation(arm, name)
        add_world_rx(arm, name, tips[side])
        pose[name] = tuple(math.degrees(v)
                           for v in arm.pose.bones[name].rotation_euler)

    # 臂：保持 A01 的护体架势，只叠一个小的前后摆。世界转角给**反号**
    # 才是"一前一后"的摆臂（轴语义同样是镜像的）。
    for bone in ("upperarm.L", "forearm.L", "hand.L",
                 "upperarm.R", "forearm.R", "hand.R"):
        deg = gait.arm_swing * twist * (1.0 if bone.endswith(".L") else -1.0)
        direction = swung(I1.ARM_DIRS[bone], deg)
        if gait.arm_tuck_deg and bone.startswith("upperarm"):
            direction = swung_z(direction, -gait.arm_tuck_deg
                                if bone.endswith(".L") else gait.arm_tuck_deg)
        pose[bone] = A.aim_bone(arm, bone, direction)
    return pose, clearances


def gait_pose(arm, gait, frame, meshes=None):
    """生成姿态。给了 meshes 就做第 2 遍**实测贴地闭环**。

    为什么必须闭环：踮脚时踝该抬多高，取决于"鞋底前端到踝的水平距离"，
    而这个距离由蒙皮后的鞋网格决定，不是 foot 骨长 0.130 m —— 第一版按骨长
    硬算，鞋底前端一踮脚就扎进地面 18.07 mm。
    做法：第 1 遍按解析初值摆好 → 实测该侧鞋底最低点 → 令踝 z 平移
    (目标 − 实测) 再摆一次。踝的平移与鞋底最低点是 1:1 的，一次即到位。
    """
    pose, clearances = _build(arm, gait, frame, {"L": 0.0, "R": 0.0})
    if meshes is None:
        return pose
    low = A.lowest_z_by_side(meshes)
    shifts = {side: clearances[side] - low[side] for side in ("L", "R")}
    if max(abs(v) for v in shifts.values()) < 5e-5:
        return pose
    pose, _ = _build(arm, gait, frame, shifts)
    return pose


def walk_pose(arm, frame, meshes=None):
    """Walk_F 的兼容入口（等价 `gait_pose(arm, WALK_F, frame, meshes)`）。"""
    return gait_pose(arm, WALK_F, frame, meshes)


# =============================================================== 专属门禁
def in_stance(gait, frame, offset):
    return wrap(frame / float(gait.total) - offset) * gait.total \
        <= gait.stance_frames + 1e-6


def in_swing(gait, frame, offset):
    return not in_stance(gait, frame, offset)


def local_series(samples, total, offset, key, axis=1):
    """把一整个周期的采样重排成**按本地相位**递增的顺序（本地 0 = 触地瞬间）。

    为什么需要重排：`samples` 是按**绝对帧号**排的，而右脚触地在第 24 帧，
    它的本地相位在数据里是断裂的（…23, 24→0, 1, …）。任何"在支撑期/摆动期
    交界处取前后帧算速度"的判据都必须在本地相位轴上做，否则取到的前后帧
    根本不是交界的两侧。

    `axis` 取某个分量（默认 1 = 世界 y，即前进轴）；采样值是 (x, y, z) 三元组。
    """
    total = int(total)
    start = int(round(offset * total))
    ordered = list(samples[start:total]) + list(samples[0:start + 1])
    return [sample[key][axis] for sample in ordered]


def velocity_continuity(gait, samples):
    """离地端的**速度连续性** + 触地端的**速度跳变量**。

    这是 `end_slope` 口径的会失败的断言。步态机旧写法 `end_slope = −SLIDE_M`
    只在 `stance_frames == swing_frames` 时与支撑期速率相等（A03/A04 都是 36==36，
    所以看不出问题）。Run 的 17 ≠ 31：照抄旧写法会得到"摆动 31 帧却按 17 帧的
    斜率走"的直线，离地瞬间脚相对身体的速度掉到支撑期的 55% —— 观感就是
    "脚被粘了一下"，而**其它门禁全是绿的**（端点对、匀速性对、腾空对）。
    所以必须单独盯。

    两端口径**不同**（见 `Gait.__init__` 的推导）：
      · 离地端 s=0：脚刚离地，速度必须与支撑期连续 ⟹ 判据 ≤15%。
      · 触地端 s=1：脚拍下来被地面钉住，速度**本来就跳变** ⟹ 不判连续，
        改判"跳变必须够大"（≥1.0 m/s）—— 这是"重踏"的量化，跳变太小 = 软着陆。
    """
    total = int(gait.total)
    stance = int(gait.stance_frames)
    out = {}
    worst = 0.0
    smallest_step = 1e9
    for side, offset in (("L", 0.0), ("R", gait.right_offset)):
        ys = local_series(samples, total, offset, "foot." + side)
        # 支撑期是本地 [0, stance] 的一段直线，每帧速率取端点差。
        v_stance = (ys[stance] - ys[0]) / float(stance)
        v_off = ys[stance + 1] - ys[stance]          # 跨"离地"那一帧
        v_touch = ys[total] - ys[total - 1]          # 跨"触地"那一帧
        rel_off = abs(v_off - v_stance) / abs(v_stance)
        # 触地跳变 = 落地前速度 → 支撑期速度 的变化量（矢量差，取模）。
        step = abs(v_stance - v_touch) * A.FPS
        out["v_stance_mps_%s" % side] = round(v_stance * A.FPS, 4)
        out["v_off_mps_%s" % side] = round(v_off * A.FPS, 4)
        out["v_touch_mps_%s" % side] = round(v_touch * A.FPS, 4)
        out["takeoff_velocity_jump_%s" % side] = round(rel_off, 4)
        out["landing_velocity_step_mps_%s" % side] = round(step, 4)
        worst = max(worst, rel_off)
        smallest_step = min(smallest_step, step)
    out["takeoff_velocity_jump"] = round(worst, 4)
    out["takeoff_velocity_continuous_ok"] = worst <= 0.15
    out["landing_velocity_step_mps"] = round(smallest_step, 4)
    # 落地冲击：脚在"即将触地"时相对身体的速度应与支撑期**反向等大**
    # （脚在地面系里刚好静止下来再被钉住），跳变因此约等于 2×速率。
    # 这里只判"必须有明显冲击"，不判具体倍率（倍率由 end_slope_out 设计决定）。
    out["landing_impact_ok"] = smallest_step >= 1.0
    return out


def _fit_line(xs, ys):
    """最小二乘直线，返回 (slope, intercept, max_abs_residual)。"""
    n = float(len(xs))
    sum_x, sum_y = sum(xs), sum(ys)
    sum_xx = sum(x * x for x in xs)
    sum_xy = sum(x * y for x, y in zip(xs, ys))
    denominator = n * sum_xx - sum_x * sum_x
    slope = (n * sum_xy - sum_x * sum_y) / denominator
    intercept = (sum_y - slope * sum_x) / n
    residual = max(abs(y - (slope * x + intercept)) for x, y in zip(xs, ys))
    return slope, intercept, residual


def _correlation(a, b):
    n = float(len(a))
    mean_a, mean_b = sum(a) / n, sum(b) / n
    da = [x - mean_a for x in a]
    db = [x - mean_b for x in b]
    cov = sum(x * y for x, y in zip(da, db))
    va = math.sqrt(sum(x * x for x in da))
    vb = math.sqrt(sum(y * y for y in db))
    return cov / (va * vb) if va > 1e-12 and vb > 1e-12 else 0.0


def walk_assertions(samples):
    res = {}
    gait = WALK_F
    frames = [s["frame"] for s in samples]

    # 1) 支撑期滑移必须**匀速**：贴地窗口内踝 y 对时间近似直线，速率 = 0.6 m/s。
    #    这是 Walk 版的"脚不滑"——不是"脚不动"，是"不许忽快忽慢"。
    worst_dev = 0.0
    for side, offset in (("L", 0.0), ("R", gait.right_offset)):
        index = [i for i, f in enumerate(frames) if in_stance(gait, f, offset)]
        # 横坐标用**相位轴**而不是帧号：f0 与 f72 是同一姿态（循环），若拿帧号
        # 当横坐标，x=72 的点会跟 x=0 的点落在同一 y 上，最小二乘被拉出一根
        # 斜率为零的怪线（第一版残差 494 mm，就是这么来的）。
        xs = [wrap(frames[i] / float(gait.total) - offset) * gait.total
              for i in index]
        ys = [samples[i]["foot.%s" % side][1] for i in index]
        slope, _intercept, residual = _fit_line(xs, ys)
        rate = slope * A.FPS
        res["stance_rate_mps_%s" % side] = round(rate, 4)
        res["stance_dev_mm_%s" % side] = round(residual * 1000.0, 3)
        worst_dev = max(worst_dev, residual)
    res["stance_slide_dev_mm"] = round(worst_dev * 1000.0, 3)
    res["stance_slide_is_linear"] = worst_dev * 1000.0 <= 5.0
    res["stance_rate_ok"] = all(
        abs(res["stance_rate_mps_%s" % side] - gait.locomotion_mps) <= 0.03
        for side in ("L", "R"))

    # 2) 步长：单脚在一整个周期里相对身体的前后跨度。
    stride = 0.0
    for side in ("L", "R"):
        ys = [s["foot.%s" % side][1] for s in samples]
        stride = max(stride, max(ys) - min(ys))
    res["stride_m"] = round(stride, 4)
    res["stride_length_ok"] = 0.30 <= stride <= 0.45

    # 3) 摆动脚离地高度：脚底网格最低点（按世界 x 分左右）的峰值。
    clearances = {}
    for side, offset in (("L", 0.0), ("R", gait.right_offset)):
        vals = [s["low"][side] for s in samples if in_swing(gait, s["frame"], offset)]
        clearances[side] = round(max(vals) * 1000.0, 2)
    res["swing_clearance_mm"] = clearances
    res["swing_clearance_ok"] = min(clearances.values()) >= 40.0

    # 4) 双支撑窗口：两脚同时贴地的帧数占比（走路必须**没有腾空**）。
    contact = 5.0 / 1000.0
    together = sum(1 for s in samples
                   if s["low"]["L"] <= contact and s["low"]["R"] <= contact)
    ratio = together / float(len(samples))
    res["double_support_ratio"] = round(ratio, 4)
    res["double_support_ok"] = ratio <= 0.15
    airborne = sum(1 for s in samples
                   if s["low"]["L"] > contact and s["low"]["R"] > contact)
    res["airborne_frames"] = airborne
    res["no_airborne_ok"] = airborne == 0

    # 5) 骨盆：升降要有重量感（双峰 ≥ 20 mm），水平不许自带位移。
    pelvis = [s["pelvis"] for s in samples]
    bob = (max(p[2] for p in pelvis) - min(p[2] for p in pelvis)) * 1000.0
    span_x = (max(p[0] for p in pelvis) - min(p[0] for p in pelvis)) * 1000.0
    span_y = (max(p[1] for p in pelvis) - min(p[1] for p in pelvis)) * 1000.0
    net_y = abs(pelvis[-1][1] - pelvis[0][1]) * 1000.0
    res["pelvis_bob_mm"] = round(bob, 2)
    res["pelvis_bob_ok"] = bob >= 20.0
    res["pelvis_span_x_mm"] = round(span_x, 2)
    res["pelvis_span_y_mm"] = round(span_y, 2)
    res["pelvis_net_y_mm"] = round(net_y, 3)
    res["pelvis_no_self_displacement_ok"] = (
        span_x <= 45.0 and span_y <= 25.0 and net_y <= 0.5)

    # 6) 前倾：胸骨顶（= neck.head = chest.tail）相对骨盆**前移** 40~70 mm。
    lean = [(p[1] - s["neck"][1]) * 1000.0
            for p, s in zip(pelvis, samples)][len(samples) // 2]
    res["lean_forward_mm"] = round(lean, 2)
    res["lean_forward_ok"] = 40.0 <= lean <= 70.0

    # 7) 肩随步伐摆：肩峰（= upperarm.head）y 行程 ≥ 25 mm，且左右**反相**
    #    （反相 = 相关系数为负；同相就成了"踏步"）。
    sh_l = [s["upperarm.L"][1] for s in samples]
    sh_r = [s["upperarm.R"][1] for s in samples]
    travel_l = (max(sh_l) - min(sh_l)) * 1000.0
    travel_r = (max(sh_r) - min(sh_r)) * 1000.0
    corr = _correlation(sh_l, sh_r)
    res["shoulder_travel_mm"] = {"L": round(travel_l, 2), "R": round(travel_r, 2)}
    res["shoulder_swing_corr"] = round(corr, 3)
    res["shoulder_swing_ok"] = (min(travel_l, travel_r) >= 25.0
                                and corr <= -0.5)

    # 8) 力量传导链：脚→腿→髋→腰→肩→手，不许"只有手在动"。
    #    位置类看世界行程；角度类看逐帧姿态角跨度。
    #    注意 spine_01 / spine_02 在走路里是**稳定支撑段**（上身不该乱扭），
    #    清单 §0.6 原文只要求这两个通道"有关键帧且非零"，故按原文判存在性。
    res.update(power_chain(samples))
    return res


def power_chain(samples):
    """脚→腿→髋→腰→肩→手，每一段都必须动（清单 §0.6 `power_chain`）。"""
    res = {}
    travel_chain = {
        "foot": ("foot.L", "foot.R"),
        "pelvis": ("pelvis",),
        "chest": ("chest",),
        "shoulder": ("shoulder.L", "shoulder.R"),
        "hand": ("hand.L.tail", "hand.R.tail"),
    }
    moved = {}
    for segment, names in travel_chain.items():
        span = 0.0
        for name in names:
            points = [Vector(s[name]) for s in samples]
            span = max(span, max((p - points[0]).length for p in points) * 1000.0)
        moved[segment] = round(span, 2)
    swing_deg = {}
    for segment, names in (("thigh", ("thigh.L", "thigh.R")),
                           ("shin", ("shin.L", "shin.R"))):
        span = 0.0
        for name in names:
            values = [s["euler"].get(name, (0.0, 0.0, 0.0))[0] for s in samples]
            span = max(span, max(values) - min(values))
        swing_deg[segment] = round(span, 2)
    nonzero = {}
    for name in ("spine_01", "spine_02", "chest", "shoulder.L", "shoulder.R"):
        values = [abs(v) for s in samples
                  for v in s["euler"].get(name, (0.0, 0.0, 0.0))]
        nonzero[name] = round(max(values), 2)
    res["power_chain_travel_mm"] = moved
    res["power_chain_swing_deg"] = swing_deg
    res["power_chain_nonzero_deg"] = nonzero
    res["power_chain_ok"] = (all(v >= 5.0 for v in moved.values())
                             and all(v >= 15.0 for v in swing_deg.values())
                             and all(v >= 1.0 for v in nonzero.values()))
    return res


# ---------------------------------------------------------------- 主流程
def main():
    arm, meshes = A.open_animation_project()
    A.setup_scene()

    if "Idle_01" not in bpy.data.actions:
        print("WALKF_BOOTSTRAP 动画工程缺 Idle_01，先补跑 A01")
        I1.main()
        arm, meshes = A.open_animation_project()
        A.setup_scene()

    # 逐帧打帧：走路是强几何约束动画（支撑脚要钉在世界坐标上匀速后滑），
    # 每帧姿态都由 IK 反解得到，中间帧没有"插值出来"的自由度。
    keyframes = [(frame, gait_pose(arm, WALK_F, frame, meshes))
                 for frame in range(0, TOTAL + 1)]

    meta = {
        "anim_id": NAME,
        "loop": True,
        "category": "基础移动",
        "note": "前走：略前倾、步长 0.36m、肩随步伐摆；原地动画，位移由程序给",
        "locomotion_mps": round(LOCOMOTION_MPS, 4),
        "stride_m": STEP_M,
        "stance_ratio": round(STANCE_FRAMES / float(TOTAL), 4),
        "root_motion_m": [0.0, 0.0],
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.add_markers(action, {
        "L_TOUCH": 0, "L_TIP": FLAT_FRAMES, "L_OFF": STANCE_FRAMES,
        "R_TOUCH": int(RIGHT_OFFSET * TOTAL),
        "R_TIP": int(RIGHT_OFFSET * TOTAL) + FLAT_FRAMES,
        "CYCLE_END": TOTAL,
    })

    samples = A.sample_animation(arm, action, 0, TOTAL, meshes)
    # foot_probe 置空：通用门禁的 `no_foot_slide`（脚位移 ≤3 mm）在 Walk 上
    # 是**错的口径**（原地走路要求支撑脚匀速后滑 400 mm），这里换成
    # `stance_slide_is_linear` 判"匀速"，见 walk_assertions。
    report = A.run_common_assertions(samples, meta, foot_probe=())
    report.update(walk_assertions(samples))
    report["meta"] = meta
    failed = sorted(k for k, v in report.items()
                    if k.endswith("_ok") and v is not True)
    report["failed"] = failed
    A.report("WALKF_REPORT", report)

    if not SKIP_RENDER:
        # 侧视看步态（前倾 / 步幅 / 抬脚高度），正面看肩摆与重心转移。
        A.render_pose_sheet(arm, action, [0, 20, 36, 40, 54], "walkf",
                            views=(A.VIEW_SIDE,))
        A.render_pose_sheet(arm, action, [0, 20, 40], "walkf",
                            views=(A.VIEW_FRONT,))
    A.save_project()
    A.export_glb(arm)
    print("WALKF_DONE failed=%s" % failed)


if __name__ == "__main__":
    # 必须加这道守卫：A04 起要 `import anim_walk_f` 复用它这套步态机器。
    # 没有守卫时 import 会**顺带把 A03 整支重跑一遍**（重渲 6 张静帧 + 存盘 +
    # 导 GLB）—— 与 A02 踩过的 `import anim_idle_01` 同源。
    # `blender --python anim_walk_f.py` 时 __name__ == "__main__"，行为不变。
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("WALKF_FAILURE " + traceback.format_exc())
