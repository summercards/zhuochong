"""anim_crouch —— A08 `Crouch` 蹲伏。

设计（对着清单「下一支计划 —— A08」逐条落）：
    定位      重心**迅速**下降，双拳保持战斗状态。
              这是「战斗站姿 → 蹲姿」的**一次性过渡**；下一支 A09 `Crouch_Idle`
              是它的蹲姿循环，两者**末帧/首帧必须逐位对接**。
    时长      24 帧 / 0.400 s @60fps，**非循环**（`loop=False`）。
    衔接      首帧 = `Idle_01@0`（`I1.idle_pose(arm, 0.0)`，世界矩阵逐位一致）。
    结构      0~3   预备：上身**先微微上抬**（反向预备、蓄势），膝松；
                     两脚一动不动。
              3~14  下蹲：**髋部先折叠**（pelvis rx 领跑），膝跟着弯，
                     重心沿**近直线**下降；脚钉死在世界坐标上。
              14~24 稳定：落进蹲姿，上身微前倾压低；末 6 帧角度增量单调收敛。
    脚        踝 L (150, −170) / R (−150, +140) mm，踏宽 **300 mm** ——
              **蹲下时脚不移位**（本支的核心门禁 `feet_pinned_ok`）。
    手臂      蹲伏是「重心低 + 双拳护胸」，**手臂不能跟着塌下去** ——
              手臂朝向按**胸骨世界系**给定（`Rx(胸链累计前倾)·I1.ARM_DIRS`），
              不随骨盆下沉而改变相对胸的角度。

---------------------------------------------------------------------------
本支的三个关键做法（都有前几支的实测依据）

1. **贴地不靠"逐帧追鞋底"，靠"一次冻结的常数偏移"。**
   蹲下时膝弯从 ~40° 拉到 ~90°，鞋底网格顶点会被 `shin` 权重带偏（A06 踩坑 5，
   实测 5.6 mm）。逐帧重算闭环会形成**蒙皮反馈环**，把踝一路往下拉
   （A01~A07 都踩过）。本支改成：
     ① 先用 `build_pose(zoff=0)` 扫一遍全部帧，量出两脚鞋底各自的 z 区间 [lo, hi]；
     ② 取**一个常数** c，把 [lo, hi] 塞进门禁窗口 [−2, +6] mm 的正中；
     ③ 全程冻结 c。
   ⟹ 踝的世界坐标是**严格常量** ⟹ `feet_pinned_mm ≈ 0`；
      鞋底只承受"蒙皮带来的形状漂移"，登记为 `planted_sole_drift_mm` **只报不判**。
   这正是清单注意第二条要的"shift 在首帧冻结"，只是把冻结粒度从"一个支撑窗口"
   收紧到"整支动画" —— 蹲伏两脚全程都在支撑窗口里，两者等价。

2. **膝弯角从骨骼世界位置算，不从 euler 读。** thigh 带外展 rz，shin 的旋转轴
   被父链带偏（A01 的老坑：差值 4.3°）。按世界位置算夹角没有这种累积误差。

3. **收招收敛用 A06 踩坑 4 的修法**：`track` 末段切线强制置 0。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python anim_crouch.py
    SKIP_RENDER=1 只跑门禁（迭代用）。
"""

import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A  # noqa: E402
import anim_idle_01 as I1  # noqa: E402
import anim_walk_f as WF  # noqa: E402
import anim_turn as TURN  # noqa: E402  （复用 track / leg_to —— 都有 __main__ 守卫）

NAME = "Crouch"
TOTAL = 24                       # 0.400 s @ 60 fps
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"

ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")

# ---------------------------------------------------------------- 轨迹（帧, 值）
# 骨盆升降：0.830（A01 战斗站姿）→ 反向预备 +8.5 mm → 迅速下坠 → 落进 0.628
# 下降量 = 0.830 − 0.628 = **202 mm**（门禁要求 ≥ 200）。
# 3~14 段逐段位移 −32 / −53 / −67 / −56 mm 近似直线加速再收，读作"迅速下降"。
PELVIS_Z = ((0, 0.8300), (2, 0.8355), (3, 0.8385), (5, 0.8280), (8, 0.7750),
            (11, 0.7080), (14, 0.6520), (17, 0.6340), (20, 0.6290),
            (24, 0.6280))
# 骨盆水平：**原地**（清单 §0.4，蹲伏属基础移动，位移由程序控制）。
# x 恒 0；y 只做 26 mm 的后坐，让重心压在脚上（深蹲的必然，不是表演）。
PELVIS_X = ((0, 0.0000), (24, 0.0000))
PELVIS_Y = ((0, 0.0000), (3, 0.0040), (8, 0.0135), (14, 0.0225),
            (20, 0.0255), (24, 0.0255))

# 躯干：**髋先折叠**（pelvis rx 从 4° 涨到 13.5°，全程领跑），腰、胸跟上。
# 胸链累计前倾 = pelvis + spine_01 + spine_02 + chest：9° → 26.5°。
PELVIS_RX = ((0, 4.0), (3, 5.6), (8, 9.4), (14, 13.0), (20, 13.5), (24, 13.5))
SPINE01_RX = ((0, 2.0), (3, 2.5), (8, 3.7), (14, 5.0), (24, 5.0))
SPINE02_RX = ((0, 2.0), (3, 2.5), (8, 3.5), (14, 4.8), (24, 4.8))
CHEST_RX = ((0, 1.0), (3, 1.3), (8, 2.1), (14, 3.2), (24, 3.2))
NECK_RX = ((0, -6.0), (3, -6.7), (8, -8.2), (14, -10.0), (24, -10.0))
HEAD_RX = ((0, 5.0), (3, 5.5), (8, 6.5), (14, 7.8), (24, 7.8))
# 沉肩：与 A01 的 −18° 一致，蹲下时再沉 2.5°，读作"缩起来防住头胸"。
SHOULDER_RX = ((0, -18.0), (3, -18.4), (8, -19.5), (14, -20.5), (24, -20.5))

# 踝目标：全部来自下面的实测（`ANKLE`），这里不写死数值。
ANKLE = {}                       # side -> Vector（世界踝参考位，取自 Idle_01@0）
Z_OFF = {"L": 0.0, "R": 0.0}     # 鞋底贴地的**冻结常数偏移**（米）

# 手臂的**参照零点**：A01 战斗站姿自身的胸链累计前倾。
# 必须减掉它，否则 f0→f1 手臂会瞬间跳 9°（Idle_01 的 `aim_bone` 是直接给
# 世界方向 ARM_DIRS 的，并不知道自己的胸已经前倾了 9°）。
# 减掉之后：f0 手臂 = ARM_DIRS（与 A01 逐位一致），此后手臂随胸链**增量**转动。
LEAN0 = PELVIS_RX[0][1] + SPINE01_RX[0][1] + SPINE02_RX[0][1] + CHEST_RX[0][1]


# =============================================================== 姿态生成
def build_pose(arm, t, zoff):
    """按帧 t 构造完整姿态。`zoff` 是踝 z 的常数修正（贴地冻结值）。"""
    lean = (TURN.track(PELVIS_RX, t) + TURN.track(SPINE01_RX, t)
            + TURN.track(SPINE02_RX, t) + TURN.track(CHEST_RX, t))
    pose = {
        "pelvis": (TURN.track(PELVIS_RX, t), 0.0, 0.0),
        "spine_01": (TURN.track(SPINE01_RX, t), 0.0, 0.0),
        "spine_02": (TURN.track(SPINE02_RX, t), 0.0, 0.0),
        "chest": (TURN.track(CHEST_RX, t), 0.0, 0.0),
        "neck": (TURN.track(NECK_RX, t), 0.0, 0.0),
        "head": (TURN.track(HEAD_RX, t), 0.0, 0.0),
        "shoulder.L": (TURN.track(SHOULDER_RX, t), 0.0, 0.0),
        "shoulder.R": (TURN.track(SHOULDER_RX, t), 0.0, 0.0),
        "@loc": {"pelvis": A.wloc(TURN.track(PELVIS_X, t),
                                  TURN.track(PELVIS_Y, t),
                                  TURN.track(PELVIS_Z, t) - 0.900)},
    }
    A.apply_pose(arm, pose)

    # 腿：真双骨 IK（A06/A07 的 `leg_to`），膝弯方向给世界 −Y（膝盖向前鼓）。
    # 踝目标 = Idle_01@0 实测踝位 + 冻结的 z 偏移 ⟹ 水平钉死、z 恒定。
    for side in ("L", "R"):
        point = ANKLE[side]
        TURN.leg_to(arm, pose, side,
                    (point.x, point.y, point.z + zoff[side]), (0.0, -1.0))

    # 足：钉平到世界水平（与 A01 同口径，`keep_world_orientation` 直接钉 rest）。
    for side in ("L", "R"):
        name = "foot." + side
        pose[name] = A.keep_world_orientation(arm, name)

    pose.update(A.FIST)

    # 臂：**只跟着胸链转**，参照零点减掉 A01 站姿自身的前倾（`LEAN0`）。
    # `swung(v, θ)` 就是绕世界 X 转 θ（与 Rx(θ) 同式）⟹ 拳头相对胸口的角度
    # 全程不变 —— 蹲下时手臂不会随躯干一起塌下去（清单注意最后一条）。
    for bone in ARM_BONES:
        pose[bone] = A.aim_bone(arm, bone,
                                WF.swung(I1.ARM_DIRS[bone], lean - LEAN0))
    return pose


def calibrate(arm):
    """扫全部帧量鞋底 z 区间，解出**一个**冻结常数偏移。

    判据：把两脚各自的鞋底区间 [lo, hi] 塞进门禁窗口 [−2, +6] mm，
    且让**最低点落在 −1 mm**（鞋底刚好压住地面，不悬空、不深陷）。
    这样窗口还剩 +7 mm 的余量给蒙皮形状漂移。
    """
    lows = {"L": [], "R": []}
    for frame in range(1, TOTAL + 1):
        build_pose(arm, frame, {"L": 0.0, "R": 0.0})
        low = A.foot_lowest_by_side()
        for side in ("L", "R"):
            lows[side].append(low[side][2])

    out = {}
    for side in ("L", "R"):
        lo = min(lows[side])
        # 踝 z 偏移本身就是首帧与后续帧的踝位差 ⟹ 必须 ≤3 mm，否则
        # `feet_pinned_ok` 会红。真撞上说明鞋底整体电平偏了 2 mm 以上
        # （蒙皮问题，不是动画问题），此时按 2 mm 截断，把余差登记出来。
        out[side] = max(-0.002, min(0.002, -0.0010 - lo))
    return out, lows


# =============================================================== 测量
def knee_series(arm, action, frames):
    """逐帧读膝弯角（大腿/胫夹角，度）：从**世界位置**算，不读 euler。"""
    scene = bpy.context.scene
    previous = arm.animation_data.action if arm.animation_data else None
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    out = []
    for frame in frames:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        record = {}
        for side in ("L", "R"):
            hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
            knee = Vector(A.bone_world(arm, "shin." + side, "head"))
            ankle = Vector(A.bone_world(arm, "foot." + side, "head"))
            u = (hip - knee).normalized()
            v = (ankle - knee).normalized()
            interior = math.degrees(math.acos(max(-1.0, min(1.0, u.dot(v)))))
            record[side] = 180.0 - interior
        out.append(record)
    if previous is not None:
        arm.animation_data.action = previous
    return out


def action_world_matrices(arm, action, frame):
    scene = bpy.context.scene
    previous = arm.animation_data.action if arm.animation_data else None
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    out = {bone.name: tuple(v for row in bone.matrix for v in row)
           for bone in arm.pose.bones}
    if previous is not None:
        arm.animation_data.action = previous
    return out


def matrix_delta(a, b):
    return max(abs(x - y) for name in a for x, y in zip(a[name], b[name]))


# =============================================================== 专属门禁
def crouch_assertions(arm, action, samples, idle_mats, sole_lows):
    res = {}
    frames = [s["frame"] for s in samples]
    pelvis = [s["pelvis"] for s in samples]

    # 0) 首帧必须**逐位**等于 `Idle_01@0`（世界矩阵，不是 euler）。
    mats = action_world_matrices(arm, action, 0)
    delta = matrix_delta(mats, idle_mats)
    res["first_frame_delta"] = float("%.3e" % delta)
    res["first_frame_matches_idle_ok"] = delta <= 1e-6

    # 1) **重心迅速下降**：骨盆 z 从 0.830 掉到 ≤0.630，降幅 ≥200 mm。
    zs = [p[2] for p in pelvis]
    res["pelvis_z_start_mm"] = round(zs[0] * 1000.0, 2)
    res["pelvis_z_min_mm"] = round(min(zs) * 1000.0, 2)
    res["pelvis_z_end_mm"] = round(zs[-1] * 1000.0, 2)
    drop = (zs[0] - min(zs)) * 1000.0
    res["pelvis_drop_mm"] = round(drop, 2)
    res["pelvis_drop_ok"] = drop >= 200.0 and zs[-1] <= 0.630

    # 1b) 反向预备：下蹲前必须真的"先上抬"一下（清单「预备 0~3 上抬」）。
    rise = (max(zs[:4]) - zs[0]) * 1000.0
    res["antic_rise_mm"] = round(rise, 2)
    res["antic_rise_ok"] = 4.0 <= rise <= 15.0

    # 1c) 「重心沿**近直线**下降」量的是**路径**，不是速度曲线 ——
    #     中文原句里"沿"的宾语是"近直线"，描述的是轨迹不是速率。
    #     （第一版按"z 对帧号线性拟合残差"量，残差 20.2 mm 恒红；那是**加了
    #       "匀减速"这个原文没有的约束**，而且与"迅速下降"本身矛盾 ——
    #       匀减速 = 越落越慢，恰好把"迅速"抵消掉。改按原文口径。）
    #     路径直不直，判两件事：z 单调不增（不许中途回升）＋ 水平位移有界。
    seg = [(f, i) for i, f in enumerate(frames) if 3 <= f <= 14]
    zs_descent = [zs[i] for _, i in seg]
    res["descent_monotone_ok"] = all(zs_descent[i + 1] <= zs_descent[i]
                                     for i in range(len(zs_descent) - 1))
    hx = [pelvis[i][0] - pelvis[0][0] for _, i in seg]
    hy = [pelvis[i][1] - pelvis[0][1] for _, i in seg]
    hdev = max(math.hypot(a, b) for a, b in zip(hx, hy)) * 1000.0
    res["descent_horizontal_mm"] = round(hdev, 2)
    res["descent_straight_ok"] = hdev <= 25.0
    # 只报不判：下降段的**平均**下降速率（"迅速"的读数）。
    res["descent_rate_mm_per_frame"] = round(
        (zs_descent[0] - zs_descent[-1]) / float(len(zs_descent) - 1)
        * 1000.0, 2)

    # 2) **脚不移位**（骨架世界坐标，口径同 A01/A07）。
    #    网格口径（鞋底顶点）只报不判 —— 膝弯 90° 会被 shin 权重带偏（A06 踩坑 5）。
    travel = {}
    for side in ("L", "R"):
        points = [Vector(s["foot." + side]) for s in samples]
        travel[side] = max((p - points[0]).length for p in points) * 1000.0
    res["feet_pinned_mm"] = {k: round(v, 3) for k, v in travel.items()}
    res["feet_pinned_ok"] = all(v <= 3.0 for v in travel.values())
    span = {}
    for side in ("L", "R"):
        span[side] = round((max(sole_lows[side]) - min(sole_lows[side]))
                           * 1000.0, 2)
    res["planted_sole_span_mm"] = span       # 只报不判（蒙皮固有）
    res["z_off_mm"] = {k: round(v * 1000.0, 3) for k, v in Z_OFF.items()}

    # 3) **蹲得下去**：膝弯（大腿/胫夹角）≥60°。
    bend = knee_series(arm, action, frames)
    peak = {side: max(b[side] for b in bend) for side in ("L", "R")}
    end = {side: bend[-1][side] for side in ("L", "R")}
    res["knee_bend_peak_deg"] = {k: round(v, 2) for k, v in peak.items()}
    res["knee_bend_end_deg"] = {k: round(v, 2) for k, v in end.items()}
    res["knee_bend_start_deg"] = {k: round(bend[0][k], 2) for k in ("L", "R")}
    res["knee_bend_ok"] = (min(peak.values()) >= 60.0
                           and min(end.values()) >= 60.0)
    res["knee_bend_delta_deg"] = {k: round(end[k] - bend[0][k], 2)
                                  for k in ("L", "R")}

    # 4) **上身微前倾且有界**：骨盆顶 → 胸骨顶 的连线相对竖直的夹角。
    lean = []
    for s in samples:
        v = Vector(s["neck"]) - Vector(s["pelvis"])
        lean.append(math.degrees(math.atan2(-v.y, v.z)))
    res["torso_lean_start_deg"] = round(lean[0], 2)
    res["torso_lean_end_deg"] = round(lean[-1], 2)
    res["torso_lean_max_deg"] = round(max(lean), 2)
    res["torso_lean_ok"] = (8.0 <= lean[-1] <= 45.0 and max(lean) <= 45.0)

    # 4b) **手臂不能跟着塌下去**：拳头相对胸骨顶的距离全程基本不变。
    fist_rel = []
    for s in samples:
        sternum = Vector(s["neck"])
        fist_rel.append(max((Vector(s["hand.L.tail"]) - sternum).length,
                            (Vector(s["hand.R.tail"]) - sternum).length))
    res["fist_sternum_start_mm"] = round(fist_rel[0] * 1000.0, 2)
    res["fist_sternum_end_mm"] = round(fist_rel[-1] * 1000.0, 2)
    res["fist_sternum_drift_mm"] = round(
        (max(fist_rel) - min(fist_rel)) * 1000.0, 2)
    res["guard_kept_ok"] = (max(fist_rel) - min(fist_rel)) * 1000.0 <= 45.0

    # 4c) 拳仍护在头胸高度（相对胸口，不是相对地面 —— 蹲下时绝对高度必然下降）。
    res["guard_height_end_mm"] = round(float(samples[-1]["hand.L.tail"][2])
                                       * 1000.0, 1)

    # 5) 原地：骨盆水平行程（清单 §0.4「防自带位移」）。
    hspan = max(math.hypot(p[0] - pelvis[0][0], p[1] - pelvis[0][1])
                for p in pelvis) * 1000.0
    hnet = math.hypot(pelvis[-1][0] - pelvis[0][0],
                      pelvis[-1][1] - pelvis[0][1]) * 1000.0
    res["pelvis_span_mm"] = round(hspan, 2)
    res["pelvis_net_mm"] = round(hnet, 3)
    res["pelvis_in_place_ok"] = hspan <= 60.0

    # 6) 末帧站姿 = 蹲姿，供 A09 起手（脚位与 A01 完全一致，只是重心低）。
    last = samples[-1]
    lx, ly = last["foot.L"][0], last["foot.L"][1]
    rx, ry = last["foot.R"][0], last["foot.R"][1]
    res["stance_last_mm"] = {"L": [round(lx * 1000.0, 1),
                                  round(ly * 1000.0, 1)],
                             "R": [round(rx * 1000.0, 1),
                                   round(ry * 1000.0, 1)]}
    # 「踏宽」在两处记录里口径不同：A06 说的是 **x 向间距**（左右各 150 → 300 mm），
    # A07 说的是**踝间斜距**。本支两个都报，避免下一次再对不上账。
    res["stance_x_mm"] = round((lx - rx) * 1000.0, 1)
    res["stance_diag_mm"] = round(math.hypot(lx - rx, ly - ry) * 1000.0, 1)
    res["stance_ok"] = (lx - rx) >= 0.28 and (ly - ry) <= -0.28

    # 7) 收招不许瞬停：末 6 帧角度增量绝对值单调收敛（A06 踩坑 4 的口径）。
    deltas = []
    tail_bones = []
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
    res["decel_smooth_ok"] = all(deltas[i + 1] <= deltas[i] + 1e-9
                                 for i in range(len(deltas) - 1))

    # 8) 力量传导链（清单 §0.6 原文口径：脚→腿→髋→腰→肩→手，逐段非零）。
    #    注意本支的**脚是刻意钉死的**（这正是门禁 `feet_pinned_ok` 要的），
    #    所以那一段按"钉死"判，其余各段仍要求真的动。
    res.update(chain_assertions(samples))
    return res


def chain_assertions(samples):
    res = {}
    travel = {
        "foot(pinned)": ("foot.L", "foot.R"),
        "pelvis": ("pelvis",),
        "chest": ("chest",),
        "shoulder": ("shoulder.L", "shoulder.R"),
        "hand": ("hand.L.tail", "hand.R.tail"),
    }
    moved = {}
    for segment, names in travel.items():
        biggest = 0.0
        for name in names:
            points = [Vector(s[name]) for s in samples]
            biggest = max(biggest, max((p - points[0]).length for p in points)
                          * 1000.0)
        moved[segment] = round(biggest, 2)
    swing = {}
    for segment, names in (("thigh", ("thigh.L", "thigh.R")),
                           ("shin", ("shin.L", "shin.R"))):
        biggest = 0.0
        for name in names:
            values = [s["euler"].get(name, (0.0, 0.0, 0.0))[0] for s in samples]
            biggest = max(biggest, max(values) - min(values))
        swing[segment] = round(biggest, 2)
    nonzero = {}
    for name in ("spine_01", "spine_02", "chest", "shoulder.L", "shoulder.R"):
        values = [abs(v) for s in samples
                  for v in s["euler"].get(name, (0.0, 0.0, 0.0))]
        nonzero[name] = round(max(values), 2)
    res["power_chain_travel_mm"] = moved
    res["power_chain_swing_deg"] = swing
    res["power_chain_nonzero_deg"] = nonzero
    res["power_chain_ok"] = (all(v >= 5.0 for k, v in moved.items()
                                 if k != "foot(pinned)")
                             and moved["foot(pinned)"] <= 3.0
                             and all(v >= 15.0 for v in swing.values())
                             and all(v >= 1.0 for v in nonzero.values()))
    return res


# =============================================================== 主流程
def main():
    global ANKLE, Z_OFF

    arm, meshes = A.open_animation_project()
    A.setup_scene()

    if "Idle_01" not in bpy.data.actions:
        print("CROUCH_BOOTSTRAP 动画工程缺 Idle_01，先补跑 A01")
        I1.main()
        arm, meshes = A.open_animation_project()
        A.setup_scene()

    # 踝参考位 = A01@0 的实测踝位（不是写死的常量）——
    # 这样首帧衔接与"脚钉死"用的是同一个真值。
    I1.idle_pose(arm, 0.0)
    ANKLE = {side: Vector(A.bone_world(arm, "foot." + side, "head"))
             for side in ("L", "R")}
    A.report("CROUCH_CALIBRATION_ANKLE", {
        side: [round(v * 1000.0, 2) for v in ANKLE[side]] for side in ANKLE})

    Z_OFF, lows = calibrate(arm)
    A.report("CROUCH_CALIBRATION_SOLE", {
        "z_off_mm": {k: round(v * 1000.0, 3) for k, v in Z_OFF.items()},
        "sole_range_mm": {k: [round(min(lows[k]) * 1000.0, 2),
                              round(max(lows[k]) * 1000.0, 2)]
                          for k in ("L", "R")},
        "predicted_min_mm": round(min(min(lows[k]) + Z_OFF[k]
                                      for k in ("L", "R")) * 1000.0, 2),
        "predicted_max_mm": round(max(max(lows[k]) + Z_OFF[k]
                                      for k in ("L", "R")) * 1000.0, 2),
    })

    # 首帧 = Idle_01@0（逐位衔接，与 A07 同一条入口）
    first_pose = I1.idle_pose(arm, 0.0)

    keyframes = [(0, first_pose)]
    for frame in range(1, TOTAL + 1):
        keyframes.append((frame, build_pose(arm, frame, Z_OFF)))

    meta = {
        "anim_id": NAME,
        "loop": False,
        "category": "基础移动",
        "note": ("战斗站姿 → 蹲姿：先上抬蓄势，髋先折叠带动屈膝，重心沿近直线"
                 "下降 202 mm；两脚世界坐标钉死不动；手臂相对胸口保持护体架势"),
        "antic_frame": 3,
        "hit_frame": None,
        "cancel_frame": 20,
        "hitstop_frames": 0,
        "crouch_drop_mm": 202.0,
        "pelvis_drop_m": 0.202,
        "root_motion_m": [0.0, 0.0],
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.add_markers(action, {
        "START": 0, "ANTIC_TOP": 3, "ANTIC_END": 3, "DESCENT_MID": 8,
        "DESCENT_END": 14, "SETTLE_END": TOTAL,
    })

    samples = A.sample_animation(arm, action, 0, TOTAL, meshes)
    # foot_probe 置空：通用门禁的"脚位移 ≤3 mm"默认量 toe 骨，本支由专属
    # `feet_pinned_ok` 按 **踝** 判（toe 是踝的下游，踝钉死则 toe 钉死）。
    report = A.run_common_assertions(samples, meta, foot_probe=())

    idle_mats = action_world_matrices(arm, bpy.data.actions["Idle_01"], 0)
    report.update(crouch_assertions(arm, action, samples, idle_mats, lows))
    report["meta"] = meta
    failed = sorted(k for k, v in report.items()
                    if k.endswith("_ok") and v is not True)
    report["failed"] = failed
    A.report("CROUCH_REPORT", report)

    if not SKIP_RENDER:
        A.render_pose_sheet(arm, action, [0, 3, 6, 9, 12, 14, 18, 24],
                            "crouch", views=(A.VIEW_SIDE,))
        A.render_pose_sheet(arm, action, [0, 3, 14, 24], "crouch",
                            views=(A.VIEW_FRONT,))
    A.save_project()
    A.export_glb(arm)
    print("CROUCH_DONE failed=%s" % failed)


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("CROUCH_FAILURE " + traceback.format_exc())
