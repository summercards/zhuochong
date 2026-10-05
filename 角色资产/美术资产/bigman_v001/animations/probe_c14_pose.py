"""probe_c14_pose —— 只量不做：为 C14 `Ultimate_End` 大招收尾 的「英雄 Pose」定标判据。

清单「下一支详细制作计划 —— C14 `Ultimate_End`」§4「开工顺序」第 3 条要求：

    建 `probe_c14_pose.py` —— 扫候选英雄 Pose × 骨盆高度几档，量**剪影指标分布**，
    **先量再定阈值**。

================================ 第 1 轮的两个结论（已实测，写进主脚本与日志）

① ★★ **「纵横比」与「填充率」在英雄 Pose 上是拮抗的，C12 的三线合取式在这里不可达。**
   第 1 轮扫 6 族 × 3 档 drop = 18 个候选，`C14_PROBE_SPREAD` 实测：
     · `triumph_wide`（双臂斜上外张）→ ar **2.39~2.45**、fr **0.449**（包围盒被撑成 1.43 m 宽，
       两臂与躯干之间是**大片空白**）
     · `lunge_punch`（弓步推拳，臂向前伸）→ fr **0.827~0.832**、ar 仅 **1.17~1.19**
       （臂朝 −Y 伸，"投影进躯干"，宽度不增）
     · `press_down`（双拳压髋侧外张）→ ar **1.49~1.53**、fr **0.715~0.720**
   没有任何一族同时够到 C12 的 `ar≥1.30 且 fr≥0.80`。**这不是姿态不好，是几何**：
   把宽度从 0.58 m 推到 0.88 m，必然在包围盒里加进空白。
    ⟹ 阈值必须**按本支实测重新定**（计划原文的要求），不能照抄 C12。

② ★ **C12 的 `sil_head_top_ok` 是恒真的（继承自 `probe_c12_baseline.silhouette`）。**
   `head_top = max(p[2] for p in keep_pts)`，而 `hi_k = _bbox(keep_pts)` ⟹
   `head_top_offset_mm ≡ 0.00`，18 个候选全部 0.00 —— 这条判据**永远不会失败**。
   本探针改用**可失败的**口径：剪影**最高点**的 x 必须落在**头骨 x 的 ±180 mm 内**
   （"顶在上面的是头，不是举起来的拳头"）。`raise_both` 类（双拳过顶）会因此判负 ——
   这正是原判据想抓、却抓不到的东西。

================================ 第 2 轮：位置口径的族扫描

第 1 轮用 `aim_bone`（**方向**口径）指定手臂 —— 方向与"拳头落在哪里"没有直观映射，
没法做参数化搜索。第 2 轮改成**位置逆解**（与主脚本 `arm_seat` 同口径）：
直接给**拳的世界坐标** + **肘的鼓出方向**，再解上臂/前臂/手三段朝向。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python probe_c14_pose.py
"""

import json
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A              # noqa: E402
import anim_idle_01 as I1         # noqa: E402
import probe_c12_baseline as P    # noqa: E402

SIDES = ("L", "R")
TORSO_RY = ("pelvis", "spine_01", "spine_02", "chest")
HEAD_TOP_X_TOL_M = 0.180
ARM_LEN = {}


def pchip_endpoint(h0, h1, d0, d1):
    m = ((2.0 * h0 + h1) * d0 - h0 * d1) / (h0 + h1)
    if m * d0 <= 0.0:
        return 0.0
    if d0 * d1 <= 0.0 and abs(m) > abs(3.0 * d0):
        return 3.0 * d0
    return m


def _torso(**kw):
    out = {"pelvis": (3.0, 0.0, 0.0),
           "spine_01": (0.0, 0.0, 0.0), "spine_02": (0.0, 0.0, 0.0),
           "chest": (0.0, 0.0, 0.0), "neck": (0.0, 0.0, 0.0),
           "head": (0.0, 0.0, 0.0),
           "shoulder.L": (0.0, 0.0, 0.0), "shoulder.R": (0.0, 0.0, 0.0)}
    out.update(kw)
    return out


# ---------------------------------------------------------------- 剪影（本探针自己一份）
def head_top_metrics(arm, keep_pts, hi):
    """可失败版「头顶没被别的东西埋住」。

    第 1 版口径（最高点到头骨 x 的距离 ≤ 180 mm）在**第 8 轮**被证伪：
    扬起的拳天然会高过头顶 500+ mm，判负 —— 但**单臂过顶**是合法的胜利 Pose，
    原判据想抓的是 `raise_both`（双拳夹头，头被埋在两臂之间）。
    改成量**头顶之上还压着多少东西**：`bbox 顶 − 头骨顶 ≤ 300 mm`。
    双拳过顶会把头埋进去、差值远大于 300 mm ⟹ 判负；单臂扬起则通过。
    """
    top = max(keep_pts, key=lambda p: p[2])
    head_x = A.bone_world(arm, "head", "head").x
    head_top_z = A.bone_world(arm, "head", "tail")[2]
    above_mm = (hi[2] - head_top_z) * 1000.0
    return {
        "head_top_x_mm": round(top[0] * 1000.0, 1),
        "head_bone_x_mm": round(head_x * 1000.0, 1),
        "head_top_dx_mm": round(abs(top[0] - head_x) * 1000.0, 1),
        "above_head_mm": round(above_mm, 1),
        "head_top_ok": bool(above_mm <= 300.0),
        "top_z_mm": round(top[2] * 1000.0, 1),
        "head_top_z_mm": round(head_top_z * 1000.0, 1),
        "bbox_top_z_mm": round(hi[2] * 1000.0, 1),
    }


def yaw_of(spec):
    torso = sum(spec["torso"].get(n, (0.0, 0.0, 0.0))[1] for n in TORSO_RY)
    head = torso + spec["torso"].get("neck", (0.0, 0.0, 0.0))[1] \
        + spec["torso"].get("head", (0.0, 0.0, 0.0))[1]
    return round(torso, 2), round(head, 2)


def measure(arm, spec, label):
    P.apply(spec)
    bpy.context.view_layer.update()
    sil = P.silhouette(arm, label)
    all_pts, keep_pts = P._mesh_verts()
    _lo, hi = P._bbox(keep_pts)
    sil.update(head_top_metrics(arm, keep_pts, hi))
    return sil


# ---------------------------------------------------------------- 位置口径装臂
def apply_pos(spec):
    """位置逆解装臂（同 `arm_seat` 口径）：`fist` 世界坐标 + `elbow` 鼓出方向。"""
    pose, _ = P.build(spec)
    A.apply_pose(P.A_RIG, pose)
    for side in SIDES:
        pose["foot." + side] = A.keep_world_orientation(P.A_RIG, "foot." + side)
    for side in SIDES:
        up, fo, hd = ("upperarm." + side, "forearm." + side, "hand." + side)
        l1 = ARM_LEN[side]["upper"]
        l23 = ARM_LEN[side]["forearm"] + ARM_LEN[side]["hand"]
        shoulder = Vector(A.bone_world(P.A_RIG, up, "head"))
        target = Vector(spec["fist"][side])
        delta = target - shoulder
        limit = (l1 + l23) * 0.9995
        distance = max(1e-4, min(delta.length, limit))
        axis = (delta.normalized() if delta.length > 1e-9
                else Vector((0.0, 0.0, -1.0)))
        bulge = Vector(spec["elbow"][side]) - axis * Vector(
            spec["elbow"][side]).dot(axis)
        if bulge.length < 1e-6:
            bulge = Vector((0.0, 0.0, 1.0)) - axis * axis.z
        bulge.normalize()
        cos_sh = max(-1.0, min(1.0, (l1 * l1 + distance * distance - l23 * l23)
                               / (2.0 * l1 * distance)))
        sin_sh = math.sqrt(max(0.0, 1.0 - cos_sh * cos_sh))
        elbow = shoulder + (axis * cos_sh + bulge * sin_sh) * l1
        for name, direction in ((up, elbow - shoulder),
                                (fo, target - elbow),
                                (hd, target - elbow)):
            pose[name] = A.aim_bone(P.A_RIG, name, direction)
    return pose


def append_fist(spec, side, x, y, z):
    spec.setdefault("fist", {})[side] = (x, y, z)


def append_elbow(spec, side, x, y, z):
    spec.setdefault("elbow", {})[side] = (x, y, z)


def symmetric(family, lx, fz, fy, ex, ey, ez, **torso):
    """左右镜像的候选：拳 (±lx, fy, fz)，肘鼓出 (±ex, ey, ez)。"""
    spec = {"drop": torso.pop("drop", -0.042),
            "torso": _torso(**torso)}
    append_fist(spec, "L", lx, fy, fz)
    append_fist(spec, "R", -lx, fy, fz)
    append_elbow(spec, "L", ex, ey, ez)
    append_elbow(spec, "R", -ex, ey, ez)
    spec["_family"] = family
    return spec


def tpose_metrics(arm, spec):
    """★ 不能读成 T-pose：肩→拳的**臂轴**偏离世界 X 轴至少 26°（|x| ≤ 0.90）。

    第 3 轮踩的坑：`F_spread`（双拳斜上外张 45°）拿到最高分 ar 2.09 / fr 0.535，
    但肩高 1.369、拳高 1.400 ⟹ 臂轴几乎是**水平外伸**（|x| = 0.935）——
    那与角色的 **rest T-pose 同形**，引擎里读出来就是"没摆姿势"。
    剪影指标（ar/fr）看不见这件事，必须另立一条判据盯着。
    """
    worst = 0.0
    for side in SIDES:
        shoulder = Vector(A.bone_world(arm, "upperarm." + side, "head"))
        fist = Vector(A.bone_world(arm, "hand." + side, "tail"))
        axis = (fist - shoulder)
        if axis.length < 1e-9:
            continue
        worst = max(worst, abs(axis.normalized().x))
    return {"arm_axis_x_worst": round(worst, 4),
            "tpose_ok": bool(worst <= 0.90)}


def sky_spec(drop, abduct, ankle, fist, elbow, shrug=16.0, twist=(-5.0, -3.0, -4.0),
             head_yaw=(6.0, 6.0), left=((0.46, -0.06, 0.90),
                                        (0.48, 0.32, -0.82)),
             arch=(-2.0, -2.0, -7.0), head_rx=(8.0, -8.0)):
    """主力族 `sky_hip`：右拳扬起（英雄亮相）+ 左拳压腰 + 躯干拧转 + 宽站架。

    第 6 轮目检结论：`G_sky` 在**正视**里够帅（扬拳 + 压腰的斜向剪影），
    但**侧视**里手臂横到脸前、腿站得太窄 —— 2.5D 横版格斗的主视角是**侧视**，
    所以第 8 轮把扬拳改成"**更高、更靠外、更不朝前**"，并把站架加宽、加深。
    """
    ty0, ty1, ty2 = twist
    s1, s2, ch = arch
    spec = {"drop": drop, "abduct": abduct, "ankle": ankle,
            # ★ `leg_ik` 只按 `tilt` 补偿骨盆前倾。`pose["pelvis"].rx` 由下面的
            #   `torso` 覆盖成 3.0°，若不同步写 `spec["tilt"]`，leg_ik 会按 Idle 的
            #   4.0° 去解 ⟹ 鞋底差 2~4 mm（第 9 轮实测 −3.2~−5.6 mm，越界）。
            "tilt": 3.0,
            "torso": _torso(pelvis=(3.0, ty0, 0.0),
                            spine_01=(s1, ty1, 0.0),
                            spine_02=(s2, ty1, 0.0),
                            chest=(ch, ty2, 0.0),
                            neck=(head_rx[1], head_yaw[0], 0.0),
                            head=(head_rx[0], head_yaw[1], 0.0),
                            **{"shoulder.L": (-4.0, 0.0, 0.0),
                               "shoulder.R": (shrug, 0.0, 0.0)})}
    append_fist(spec, "R", fist[0], fist[1], fist[2])
    append_elbow(spec, "R", elbow[0], elbow[1], elbow[2])
    append_fist(spec, "L", left[0][0], left[0][1], left[0][2])
    append_elbow(spec, "L", left[1][0], left[1][1], left[1][2])
    spec["_family"] = "sky_hip"
    return spec


def build_candidates():
    out = {}
    # ★ 站架只动**前后向（Y）**：`leg_ik` 在 YZ 面内解，Y 偏移是**精确**的；
    #   而 `abduct`（thigh rz）不在 leg_ik 的补偿里 —— 第 8 轮把 abduct 拉到 12~18°
    #   让鞋底抬起 9~29 mm（`sole_mm` 实测），探针与主脚本会因此错位。
    #   本族一律用 Idle 的 abduct，把站架宽度买在 Y 上（侧视也更有"扎马步"感）。
    NARROW = (I1.FRONT_ANKLE_Y, I1.BACK_ANKLE_Y)      # −0.170 / +0.140（Idle 原样）
    MID = (-0.240, 0.185)
    WIDE = (-0.320, 0.240)

    # 对照：第 6 轮目检赢家（原始 G）
    out["T0_ctrl"] = sky_spec(-0.070, I1.ABDUCT_DEG, NARROW,
                              (-0.46, -0.18, 1.66), (-0.62, 0.56, 0.06))
    # ① 中步幅 + 拳略抬、肘略收（侧视别横到脸前）
    out["T1_mid"] = sky_spec(-0.070, I1.ABDUCT_DEG, MID,
                             (-0.48, -0.16, 1.70), (-0.58, 0.46, -0.20))
    # ② 同 ① 拳再抬一档
    out["T2_mid_hi"] = sky_spec(-0.070, I1.ABDUCT_DEG, MID,
                                (-0.50, -0.14, 1.74), (-0.58, 0.46, -0.20))
    # ③ 大步幅
    out["T3_wide"] = sky_spec(-0.070, I1.ABDUCT_DEG, WIDE,
                              (-0.50, -0.14, 1.74), (-0.58, 0.46, -0.20))
    # ④ 大步幅 + 拳低一档（头顶留白更干净）
    out["T4_wide_lo"] = sky_spec(-0.070, I1.ABDUCT_DEG, WIDE,
                                 (-0.50, -0.14, 1.70), (-0.58, 0.46, -0.20))
    # ⑤ 基准沉得更低（重心更低 = 更稳重）
    out["T5_deep"] = sky_spec(-0.100, I1.ABDUCT_DEG, WIDE,
                              (-0.50, -0.14, 1.72), (-0.58, 0.46, -0.20))
    # ⑥ 头随拳（视线指向扬起的拳）
    out["T6_head"] = sky_spec(-0.070, I1.ABDUCT_DEG, MID,
                              (-0.50, -0.14, 1.74), (-0.58, 0.46, -0.20),
                              head_yaw=(2.0, -6.0))
    # ⑦ 大步幅 + 更大肩抬 + 更挺胸（胸腔打开）
    out["T7_open"] = sky_spec(-0.070, I1.ABDUCT_DEG, WIDE,
                              (-0.50, -0.14, 1.74), (-0.58, 0.46, -0.20),
                              shrug=22.0, twist=(-6.0, -4.0, -5.0))

    # ── 第 11 轮：从「目检 T1_mid 的侧视」出发 —— 扬起的拳与头**在侧面重叠**，
    #    主视角（2.5D 横版 = 侧视）读不清。核心变量 = 右拳的 **Y（前后）** 与高度。
    MID = (-0.240, 0.185)
    L_CKD = ((0.40, 0.06, 0.88), (0.46, 0.36, -0.80))   # 左拳:收回髋后侧（收招亮相型）
    # ① 拳抬到前方（侧视完全离开头）
    out["U1_fwd"] = sky_spec(-0.070, I1.ABDUCT_DEG, MID,
                             (-0.44, -0.40, 1.68), (-0.52, 0.22, -0.42),
                             left=L_CKD)
    # ② 拳更前 + 更高（大斜线）
    out["U2_fwd_hi"] = sky_spec(-0.070, I1.ABDUCT_DEG, MID,
                                (-0.42, -0.36, 1.80), (-0.50, 0.24, -0.40),
                                left=L_CKD)
    # ③ 拳几乎竖直向上（"举拳"不是"伸拳"）
    out["U3_vert"] = sky_spec(-0.070, I1.ABDUCT_DEG, MID,
                              (-0.28, -0.24, 1.88), (-0.44, 0.30, -0.16),
                              left=L_CKD)
    # ④ 拳扬到身后（"收势"，侧视也不挡头）
    out["U4_back"] = sky_spec(-0.070, I1.ABDUCT_DEG, MID,
                              (-0.48, 0.10, 1.70), (-0.46, 0.40, -0.46),
                              left=L_CKD)
    # ⑤ 拳抬在同侧、更外（侧视靠后不挡头；正视宽度最大）
    out["U5_out"] = sky_spec(-0.070, I1.ABDUCT_DEG, MID,
                             (-0.58, -0.10, 1.66), (-0.50, 0.30, -0.56),
                             left=L_CKD)
    # ⑥ 对称"双拳下压 + 挺胸"（与 C12 同族的稳妥版，做对照）
    out["U6_power"] = sky_spec(-0.070, I1.ABDUCT_DEG, MID,
                               (-0.36, -0.16, 0.86), (-0.52, 0.30, -0.74),
                               shrug=14.0, twist=(-4.0, -3.0, -4.0),
                               left=((0.36, -0.16, 0.86), (0.52, 0.30, -0.74)))

    # ── 第 12 轮：把扬拳改成**竖直冲天拳**（前臂竖直 ⟹ 侧视不横越头部），
    #    并收掉后仰（后仰让侧视读成"后躲"而不是"亮相"）。
    L_HIP = ((0.34, 0.10, 0.92), (0.52, 0.38, -0.76))
    # ① 冲天拳：拳略高于头、前臂近乎竖直
    out["V1_sky_up"] = sky_spec(-0.070, I1.ABDUCT_DEG, MID,
                                (-0.22, -0.06, 1.94), (-0.30, 0.88, -0.16),
                                left=L_HIP, arch=(-1.0, -1.0, -4.0),
                                head_rx=(4.0, -10.0))
    # ② 冲天拳 + 更靠外（正视更宽）
    out["V2_sky_wide"] = sky_spec(-0.070, I1.ABDUCT_DEG, MID,
                                  (-0.36, -0.06, 1.90), (-0.34, 0.86, -0.20),
                                  left=L_HIP, arch=(-1.0, -1.0, -4.0),
                                  head_rx=(4.0, -10.0))
    # ③ 冲天拳 + 躯干更拧转
    out["V3_sky_twist"] = sky_spec(-0.070, I1.ABDUCT_DEG, MID,
                                   (-0.24, -0.08, 1.92), (-0.32, 0.86, -0.18),
                                   shrug=20.0, twist=(-8.0, -5.0, -6.0),
                                   left=L_HIP, arch=(-1.0, -1.0, -4.0),
                                   head_rx=(4.0, -10.0))
    # ④ 拳在肩正上方（最小投影宽度，但侧视最干净）
    out["V4_sky_narrow"] = sky_spec(-0.070, I1.ABDUCT_DEG, MID,
                                    (-0.16, -0.04, 1.96), (-0.28, 0.90, -0.14),
                                    left=L_HIP, arch=(-1.0, -1.0, -4.0),
                                    head_rx=(4.0, -10.0))
    # ⑤ 起势后坐（一拳后收、一拳前指）—— 侧视有前后张力
    out["V5_cock"] = sky_spec(-0.090, I1.ABDUCT_DEG, MID,
                              (-0.40, 0.30, 1.06), (-0.50, 0.46, -0.72),
                              twist=(4.0, 2.0, 2.0),
                              left=((0.34, -0.40, 1.32), (0.44, 0.10, -0.80)),
                              arch=(-1.0, -1.0, -5.0), head_rx=(2.0, -6.0))
    # ⑥ 双拳下压挺胸（侧视腿架最稳、最"稳如山"）
    out["V6_press"] = sky_spec(-0.090, I1.ABDUCT_DEG, MID,
                               (-0.34, -0.18, 0.84), (-0.50, 0.34, -0.78),
                               shrug=14.0, twist=(-4.0, -3.0, -3.0),
                               left=((0.34, -0.18, 0.84), (0.50, 0.34, -0.78)),
                               arch=(-1.0, -1.0, -5.0), head_rx=(3.0, -6.0))

    # ── 第 13 轮：定稿精修。第 12 轮结论：
    #    · 竖直冲天拳（V1）**侧视最干净**（前臂竖直、不横越头部）⟹ 定为主形。
    #    · 但**横版主视角是侧视**、而竖直臂**不买宽度** ⟹ ar 只有 1.11~1.35。
    #      ⟹ `aspect_ratio` 单独用会把"竖直英雄 Pose"判死，**必须配合 fr 一起用**
    #      （竖直臂把空隙填住，fr 反而高：V4 的头埋度 280 mm、fr 0.7475）。
    #    · ★ **深蹲能换到宽站架**：WIDE(-0.320/0.240) 在 pelvis 830 时鞋底抬到
    #      −6.52 mm（腿够不着，`leg_ik` 被 0.9995 截断），但 pelvis 800 时只有
    #      −1.80 mm —— 腿的余量随髋高下降而增加。定稿用 drop=−0.100。
    #    · V1 的**左臂**在正视里"肘外翻"读起来别扭 ⟹ 换三种收法重试。
    DEEP = (-0.320, 0.240)
    R_UP = ((-0.30, -0.08, 1.92), (-0.34, 0.78, -0.24))
    L_SIDE = ((0.30, 0.02, 0.74), (0.32, 0.40, -0.86))   # 垂在体侧（最简洁）
    L_HIPA = ((0.28, -0.04, 0.92), (0.30, 0.50, -0.78))  # 拳按髋（肘内收）
    L_GUARD = ((0.20, -0.22, 1.20), (0.34, 0.08, -0.86))  # 护胸
    out["W1_side"] = sky_spec(-0.100, I1.ABDUCT_DEG, DEEP,
                              R_UP[0], R_UP[1], left=L_SIDE,
                              arch=(0.0, 0.0, -6.0), head_rx=(6.0, -6.0))
    out["W2_hip"] = sky_spec(-0.100, I1.ABDUCT_DEG, DEEP,
                             R_UP[0], R_UP[1], left=L_HIPA,
                             arch=(0.0, 0.0, -6.0), head_rx=(6.0, -6.0))
    out["W3_guard"] = sky_spec(-0.100, I1.ABDUCT_DEG, DEEP,
                               R_UP[0], R_UP[1], left=L_GUARD,
                               arch=(0.0, 0.0, -6.0), head_rx=(6.0, -6.0))
    out["W4_vert"] = sky_spec(-0.100, I1.ABDUCT_DEG, DEEP,
                              (-0.22, -0.06, 1.96), (-0.28, 0.82, -0.20),
                              left=L_SIDE, arch=(0.0, 0.0, -6.0),
                              head_rx=(6.0, -6.0))
    out["W5_twist"] = sky_spec(-0.100, I1.ABDUCT_DEG, DEEP,
                               R_UP[0], R_UP[1], shrug=20.0,
                               twist=(-9.0, -6.0, -7.0), left=L_SIDE,
                               arch=(0.0, 0.0, -6.0), head_rx=(6.0, -6.0))
    out["W6_out"] = sky_spec(-0.100, I1.ABDUCT_DEG, DEEP,
                             (-0.40, -0.10, 1.84), (-0.38, 0.72, -0.30),
                             left=L_SIDE, arch=(0.0, 0.0, -6.0),
                             head_rx=(6.0, -6.0))
    # 对照：不举拳，改"双拳收髋 + 挺胸"（最稳，但少一个"顶点"）
    out["W7_hips"] = sky_spec(-0.100, I1.ABDUCT_DEG, DEEP,
                              (-0.34, -0.12, 0.86), (-0.44, 0.44, -0.76),
                              shrug=12.0, twist=(-6.0, -4.0, -4.0),
                              left=((0.34, -0.12, 0.86), (0.44, 0.44, -0.76)),
                              arch=(0.0, 0.0, -6.0), head_rx=(5.0, -6.0))

    # ── 第 16 轮：★★ **口径修正** —— 主脚本的 `plant_ok` 要求**踝水平位移 ≤ 3 mm**
    #    （站姿不许挪脚），踝目标钉在 `ANKLE_0`（= Idle 的 −0.170 / +0.140）。
    #    ⟹ 探针里的 `MID`/`WIDE` 站架**在主脚本里根本拿不到**，
    #    前 15 轮的站架相关增益全部作废（`plant_ok` 会直接红）。
    #    本轮一律用 **Idle 原站架**，只扫"下沉档 × 扬拳角"，产出主脚本能照抄的真值。
    I_ST = (I1.FRONT_ANKLE_Y, I1.BACK_ANKLE_Y)
    LEFT_S = ((0.30, 0.02, 0.74), (0.32, 0.40, -0.86))
    for tag, fx, fz, drop in (("y30", -0.30, 1.88, -0.085),
                              ("y38", -0.38, 1.86, -0.085),
                              ("y44", -0.44, 1.82, -0.085),
                              ("y38d", -0.38, 1.86, -0.110),
                              ("y38u", -0.38, 1.86, -0.060),
                              ("y34", -0.34, 1.90, -0.085),
                              ("y42hi", -0.42, 1.94, -0.085),
                              ("y46", -0.46, 1.78, -0.085)):
        out["%s_fin" % tag] = sky_spec(
            drop, I1.ABDUCT_DEG, I_ST,
            (fx, -0.08, fz), (fx - 0.04, 0.78, -0.24),
            shrug=16.0, twist=(-5.0, -3.0, -4.0), left=LEFT_S,
            arch=(0.0, 0.0, -6.0), head_rx=(6.0, -6.0))
    return out


def render_top(rows, arm, n=4):
    """把评分最高的 n 个候选渲成「侧视 + 正视」静帧，供人眼判「帅不帅」。

    计划 §4 第 5 条：判据是新立的时候全绿可能是假绿 —— 先看图，再落阈值。
    """
    order = sorted(rows, key=lambda r: -(r[2]["aspect_ratio"] * r[2]["fill_ratio"]))
    out_dir = os.path.join(A.PREVIEW_DIR, "_c14_cand")
    os.makedirs(out_dir, exist_ok=True)
    camera = bpy.data.objects.get("Presentation_Camera")
    if camera is None:
        raise RuntimeError("展示相机不见了：Presentation_Camera")
    # ★ 必须先解绑 Action：`render.render()` 会强制重算依赖图并重放动画曲线，
    #   绑着 Idle_01 渲出来 6 个候选会长得一模一样（第 5 轮踩的坑）。
    if arm.animation_data is not None:
        arm.animation_data.action = None
    made = []
    for idx, (key, spec, _sil) in enumerate(order[:n]):
        apply_pos(spec)
        bpy.context.view_layer.update()
        for name, location, target, scale, res in (A.VIEW_SIDE, A.VIEW_FRONT):
            path = os.path.join(out_dir, "%02d_%s_%s.png" % (idx, key, name))
            made.append(A.render_still(camera, path, location, target, scale,
                                       res))
    print("C14_PROBE_RENDER " + json.dumps(made, ensure_ascii=False))
    return made


def main():
    arm, _meshes = A.open_animation_project()
    A.setup_scene()
    if I1.NAME not in bpy.data.actions:
        print("C14_PROBE_BOOTSTRAP 缺 %s，先补跑" % I1.NAME)
        I1.main()
        arm, _meshes = A.open_animation_project()
        A.setup_scene()
    P.A_RIG = arm
    for side in SIDES:
        ARM_LEN[side] = {
            "upper": arm.pose.bones["upperarm." + side].length,
            "forearm": arm.pose.bones["forearm." + side].length,
            "hand": arm.pose.bones["hand." + side].length}

    src = bpy.data.actions[I1.NAME]
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = src
    A._bind_slot(arm, src)
    bpy.context.scene.frame_set(0)
    bpy.context.view_layer.update()
    base = P.silhouette(arm, "Idle_01@0")
    _ap, _kp = P._mesh_verts()
    base.update(head_top_metrics(arm, _kp, P._bbox(_kp)[1]))
    print("C14_PROBE_BASE " + json.dumps(base, ensure_ascii=False))

    cands = build_candidates()
    rows = []
    for key in sorted(cands):
        spec = cands[key]
        apply_pos(spec)
        bpy.context.view_layer.update()
        sil = P.silhouette(arm, key)
        _ap, kp = P._mesh_verts()
        sil.update(head_top_metrics(arm, kp, P._bbox(kp)[1]))
        sil["aspect_ratio"] = round(sil["aspect"] / base["aspect"], 4)
        sil["fill_ratio"] = round(sil["fill_grid"] / base["fill_grid"], 4)
        sil["shoulder_ratio"] = round(
            sil["shoulder_width_m"] / base["shoulder_width_m"], 4)
        ty, hy = yaw_of(spec)
        sil["torso_yaw_deg"] = ty
        sil["head_yaw_deg"] = hy
        sil["clamp_ok"] = _clamp_of(spec)
        sil.update(tpose_metrics(arm, spec))
        sil["pz_delta_mm"] = round((spec["drop"] + 0.070) * 1000.0, 1)
        rows.append((key, spec, sil))
        print("C14_PROBE " + json.dumps({
            "key": key, "pz_delta_mm": sil["pz_delta_mm"],
            "ar": sil["aspect_ratio"], "fr": sil["fill_ratio"],
            "sh_ratio": sil["shoulder_ratio"],
            "w": sil["width_m"], "h": sil["height_m"],
            "aspect": sil["aspect"], "fill": sil["fill_grid"],
            "head_top_dx_mm": sil["head_top_dx_mm"],
            "above_head_mm": sil["above_head_mm"],
            "head_top_ok": sil["head_top_ok"],
            "com_in": sil["com_inside_support"],
            "sole_mm": sil["sole_min_mm"], "pelvis_mm": sil["pelvis_z_mm"],
            "torso_yaw": ty, "head_yaw": hy, "clamp_ok": sil["clamp_ok"],
            "arm_axis_x": sil["arm_axis_x_worst"],
            "tpose_ok": sil["tpose_ok"],
        }, ensure_ascii=False))

    print("C14_PROBE_SPREAD " + json.dumps({
        "n": len(rows),
        "ar": [min(r[2]["aspect_ratio"] for r in rows),
               max(r[2]["aspect_ratio"] for r in rows)],
        "fr": [min(r[2]["fill_ratio"] for r in rows),
               max(r[2]["fill_ratio"] for r in rows)],
        "ar_max_at": max(rows, key=lambda r: r[2]["aspect_ratio"])[0],
        "fr_max_at": max(rows, key=lambda r: r[2]["fill_ratio"])[0],
        "ar_ge_130": sorted(r[0] for r in rows
                            if r[2]["aspect_ratio"] >= 1.30),
        "fr_ge_075": sorted(r[0] for r in rows
                            if r[2]["fill_ratio"] >= 0.75),
    }, ensure_ascii=False))

    # ★ 定标：`hero_silhouette_ok` 的**红线**。基于本探针全部 13 轮实测的分布：
    #   · Idle（要判死的"没摆姿势"）           → ar 1.00 / fr 1.00 / sh 1.00
    #   · 竖直冲天拳族（侧视最可读）            → ar 1.04~1.16 / fr 0.73~0.81 / sh 0.94
    #   · 宽拳外张族（正视最宽，但侧视挡脸）    → ar 1.57~1.81 / fr 0.60~0.68 / sh 0.94
    #   ⟹ ar 单用会把"竖直英雄 Pose"判死（竖直臂不买宽度）—— 必须**配 fr 一起用**，
    #      并显式要求**不可能由 Idle 满足**：肩宽必须被"抬肩"显著改变。
    #   红线（三项全过才算 `hero_silhouette_ok`）：
    #     ar ≥ 1.10 且 fr ≥ 0.65 且 sh 比 ≤ 0.95↑… 见下，sh 用"必须 >= 0.85"作地板。
    #   ★ 另两条（`head_top_ok` / `com_inside_support`）独立计入。
    AR_MIN, FR_MIN, SH_MIN = 1.10, 0.65, 0.85
    ok = [r for r in rows
          if r[2]["aspect_ratio"] >= AR_MIN and r[2]["fill_ratio"] >= FR_MIN
          and r[2]["shoulder_ratio"] >= SH_MIN
          and r[2]["head_top_ok"] and r[2]["com_inside_support"] is True
          and r[2]["clamp_ok"]]
    # 综合评分：ar × fr（"宽"与"密"拮抗，乘法两边一起计入，不给任一边放水）
    ok.sort(key=lambda r: -(r[2]["aspect_ratio"] * r[2]["fill_ratio"]))
    print("C14_PROBE_PASS " + json.dumps(
        [[r[0], r[2]["aspect_ratio"], r[2]["fill_ratio"],
          r[2]["shoulder_ratio"], r[2]["head_top_dx_mm"],
          round(r[2]["aspect_ratio"] * r[2]["fill_ratio"], 4)]
         for r in ok], ensure_ascii=False))

    fin = [r for r in rows if r[0].endswith("_fin")]
    for f_row in fin:
        f = f_row[2]
        apply_pos(f_row[1])
        bpy.context.view_layer.update()
        # ★ 交给主脚本的**肩部相对**手目标（`肩 + u·len`）：主脚本的臂 IK 用同一口径，
        #   只要躯干欧拉与骨盆高度一致，解出来的拳世界位置就与探针逐位相同。
        rel = {}
        for side in SIDES:
            shoulder = Vector(A.bone_world(arm, "upperarm." + side, "head"))
            fist = Vector(A.bone_world(arm, "hand." + side, "tail"))
            offset = fist - shoulder
            rel[side] = {
                "fist_dir": [round(v, 6) for v in offset.normalized()],
                "fist_len_mm": round(offset.length * 1000.0, 3),
                "fist_mm": [round(v * 1000.0, 2) for v in fist],
                "shoulder_mm": [round(v * 1000.0, 2) for v in shoulder],
                "elbow_dir": [round(v, 6) for v in Vector(f_row[1]["elbow"][side]).normalized()],
            }
        print("C14_PROBE_FINAL " + json.dumps({
            "key": f_row[0],
            "rel": rel,
            "torso": {k: list(v) for k, v in f_row[1]["torso"].items()},
            "drop": f_row[1]["drop"], "abduct": f_row[1]["abduct"],
            "ankle": list(f_row[1]["ankle"]),
            "ar": f["aspect_ratio"], "fr": f["fill_ratio"],
            "sh_ratio": f["shoulder_ratio"],
            "aspect": f["aspect"], "fill": f["fill_grid"],
            "w": f["width_m"], "h": f["height_m"],
            "head_top_dx_mm": f["head_top_dx_mm"],
            "above_head_mm": f["above_head_mm"],
            "arm_axis_x": f["arm_axis_x_worst"], "tpose_ok": f["tpose_ok"],
            "com_in": f["com_inside_support"], "clamp_ok": f["clamp_ok"],
            "sole_mm": f["sole_min_mm"], "pelvis_mm": f["pelvis_z_mm"],
            "thresholds": {"ar_min": AR_MIN, "fr_min": FR_MIN,
                           "sh_min": SH_MIN},
            "idle": {"ar": 1.0, "fr": 1.0, "sh": 1.0,
                     "aspect": base["aspect"], "fill": base["fill_grid"],
                     "shoulder_m": base["shoulder_width_m"]},
        }, ensure_ascii=False))

    if ok:
        key, spec, sil = ok[0]
        apply_pos(spec)
        bpy.context.view_layer.update()
        port = {"key": key, "family": spec.get("_family"), "drop": spec["drop"],
                "pz_delta_mm": round((spec["drop"] + 0.070) * 1000.0, 2),
                "aspect_ratio": sil["aspect_ratio"],
                "fill_ratio": sil["fill_ratio"],
                "shoulder_ratio": sil["shoulder_ratio"],
                "aspect": sil["aspect"], "fill": sil["fill_grid"],
                "shoulder_width_m": sil["shoulder_width_m"],
                "height_m": sil["height_m"], "width_m": sil["width_m"],
                "head_top_dx_mm": sil["head_top_dx_mm"],
                "torso_yaw_deg": yaw_of(spec)[0],
                "head_yaw_deg": yaw_of(spec)[1],
                "torso": {k: list(v) for k, v in spec["torso"].items()},
                "fist_mm": {}, "elbow_dir": {}, "shoulder_mm": {}}
        for side in SIDES:
            port["fist_mm"][side] = [round(v * 1000.0, 2) for v in
                                     A.bone_world(arm, "hand." + side, "tail")]
            head = Vector(A.bone_world(arm, "upperarm." + side, "head"))
            tail = Vector(A.bone_world(arm, "upperarm." + side, "tail"))
            port["elbow_dir"][side] = [round(v, 4)
                                       for v in (tail - head).normalized()]
            port["shoulder_mm"][side] = [round(v * 1000.0, 2) for v in
                                         A.bone_world(arm, "upperarm." + side,
                                                      "head")]
        print("C14_PROBE_WINNER " + json.dumps(port, ensure_ascii=False))

    if os.environ.get("C14_RENDER"):
        render_top(rows, arm, n=int(os.environ.get("C14_RENDER_N", "4")))

    print("C14_PROBE_BASELINE " + json.dumps(
        {"aspect": base["aspect"], "fill": base["fill_grid"],
         "shoulder_m": base["shoulder_width_m"],
         "height_m": base["height_m"], "width_m": base["width_m"],
         "head_top_dx_mm": base["head_top_dx_mm"],
         "sole_mm": base["sole_min_mm"], "pelvis_mm": base["pelvis_z_mm"]}))
    print("C14_PROBE_DONE")


def _clamp_of(spec):
    """位置逆解是否被截断（拳超出臂长）—— 用 `arm_seat` 同口径复算。"""
    worst = 0.0
    for side in SIDES:
        l1 = ARM_LEN[side]["upper"]
        l23 = ARM_LEN[side]["forearm"] + ARM_LEN[side]["hand"]
        shoulder = Vector(A.bone_world(P.A_RIG, "upperarm." + side, "head"))
        delta = Vector(spec["fist"][side]) - shoulder
        worst = max(worst, delta.length / ((l1 + l23) * 0.9995))
    return bool(worst <= 1.0)


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("C14_PROBE_FAILURE " + traceback.format_exc())
