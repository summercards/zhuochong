"""probe_up07 —— B07 `Uppercut` 上勾拳 **只读** 探针（定盘数）。

清单「下一支详细制作计划 —— B07」的 ★ 四件事在这里落地（**先量再做**）：

  1. **深蹲下界**：骨盆能压到多低 —— 膝深屈时 `leg_reach_headroom_mm` 还剩多少。
     余量 < 20 mm 就缩下沉量。
  2. **命中帧拳峰可达高度**：上勾时肩→腕轴接近竖直，`aim_carry` 的伸展极限在哪。
     量"拳尖 z 的上界"，再决定 `uppercut_height_ok` 的 1800 mm 要不要调。
  3. **踮脚能贡献多少骨盆 z**：foot 跖屈 25°/35°/45° 三档（本探针加密到
     15~55°），各量**骨盆 z 上限**与**鞋底最低点**（鞋尖会不会戳穿）。
     ★ 本支最贵的一课就在这：`rise_ok` 要 +120 mm，而**脚平放在地上时腿够不到** ——
       骨盆上升只能靠"腿伸直 + 踮脚"，必须量清可用的踝高。
  4. **上勾的肘 pole**：拳向上打时肩→腕轴近竖直、pole 接近水平 ⟹ `|pole⊥axis|`
     必然退化。低于 0.30 就走 `_elbow_bulge` 接力做法，**不许硬阈值**。

另量清楚：idle 踝/膝/髋/肩实测位、腿长、鞋底接触点的几何（贴地枢轴在踝前多远）、
两脚在"踮脚"时的踝位移（抬升 + 前移补偿，用于不滑步）。

本探针**只读**：只摆姿态、只测量，不建 Action、不存盘、不导 GLB。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python probe_up07.py
"""

import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A          # noqa: E402
import anim_idle_01 as I1     # noqa: E402
import anim_walk_f as WF      # noqa: E402

SIDES = ("L", "R")
# 后腿 R 驱动（清单原文「深蹲蓄力**后腿**髋驱动拳头向上」）⟹ 攻击侧 = 后侧 R；
# 前脚 L 是撑地的那只（−2~+6 mm 贴地）。
SUPPORT = "L"
ATTACK = "R"

LEG_LIMIT = A.L_THIGH + A.L_SHIN          # 0.822 m


def mm(v):
    return [round(float(x) * 1000.0, 1) for x in v]


def _leg_geom(hip, target, pole):
    """纯几何预报：伸展率 / 膝内角 / `|pole⊥axis|` / 是否可达。"""
    hip = Vector(hip)
    delta = Vector(target) - hip
    raw = delta.length
    limit = LEG_LIMIT * 0.9995
    axis = delta.normalized() if raw > 1e-9 else Vector((0.0, -1.0, 0.0))
    distance = max(1e-4, min(raw, limit))
    cos_hip = ((A.L_THIGH ** 2 + distance ** 2 - A.L_SHIN ** 2)
               / (2.0 * A.L_THIGH * distance))
    cos_hip = max(-1.0, min(1.0, cos_hip))
    inner = math.degrees(math.acos(cos_hip))
    knee_bend = 180.0 - inner
    pole_v = Vector(pole).normalized()
    bulge = pole_v - axis * pole_v.dot(axis)
    return {"reach_mm": round(raw * 1000.0, 1),
            "extension": round(raw / LEG_LIMIT, 4),
            "headroom_mm": round((LEG_LIMIT - raw) * 1000.0, 1),
            "knee_bend_deg": round(knee_bend, 2),
            "pole_sin": round(bulge.length, 4),
            "reachable": bool(raw <= limit)}


def _arm_geom(shoulder, wrist, upper, fore, pole):
    delta = Vector(wrist) - Vector(shoulder)
    raw = delta.length
    limit = (upper + fore) * 0.9995
    axis = delta.normalized() if raw > 1e-9 else Vector((0.0, 0.0, 1.0))
    pole_v = Vector(pole).normalized()
    bulge = pole_v - axis * pole_v.dot(axis)
    return {"reach_mm": round(raw * 1000.0, 1),
            "extension": round(raw / (upper + fore), 4),
            "headroom_mm": round(((upper + fore) - raw) * 1000.0, 1),
            "pole_sin": round(bulge.length, 4),
            "reachable": bool(raw <= limit)}


def _bone_len(arm, name):
    return (Vector(A.bone_world(arm, name, "tail"))
            - Vector(A.bone_world(arm, name, "head"))).length


def _leg_pole_from_pose(arm, side):
    """实测「膝的鼓出方向」= (膝−髋) 去掉沿 髋→踝 轴分量后的单位垂足。"""
    hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
    knee = Vector(A.bone_world(arm, "shin." + side, "head"))
    ankle = Vector(A.bone_world(arm, "foot." + side, "head"))
    delta = ankle - hip
    axis = delta.normalized() if delta.length > 1e-9 else Vector((0.0, -1.0, 0.0))
    bulge = (knee - hip) - axis * (knee - hip).dot(axis)
    if bulge.length < 1e-6:
        bulge = Vector((0.0, -1.0, 0.0)) - axis * axis.y
    return tuple(bulge.normalized())


def set_tip(arm, pose, side, tip_deg):
    """摆好 `pose` 后，把该侧脚**钉平到 rest 朝向**再绕世界 X 叠 `tip_deg`。

    与 A10 `Jump_Start` 的 `build_pose` 同一条路（`foot.rx` 会被父链外展带偏，
    所以不用欧拉通道，直接在世界空间叠）。
    """
    name = "foot." + side
    A.apply_pose(arm, pose)
    A.keep_world_orientation(arm, name)
    WF.add_world_rx(arm, name, tip_deg)
    bpy.context.view_layer.update()
    return name


def sole_low(arm):
    """左右鞋底最低顶点（世界坐标），按**具名鞋对象**分侧。"""
    low = A.foot_lowest_by_side()
    return {s: (None if low[s] is None else Vector(low[s])) for s in SIDES}


def main():
    arm, _meshes = A.open_animation_project()
    A.setup_scene()

    idle = I1.idle_pose(arm, 0.0)
    A.apply_pose(arm, idle)

    ANK = {s: Vector(A.bone_world(arm, "foot." + s, "head")) for s in SIDES}
    KNEE = {s: Vector(A.bone_world(arm, "shin." + s, "head")) for s in SIDES}
    HIP = {s: Vector(A.bone_world(arm, "thigh." + s, "head")) for s in SIDES}
    TOE = {s: Vector(A.bone_world(arm, "toe." + s, "head")) for s in SIDES}
    PELVIS = Vector(A.bone_world(arm, "pelvis", "head"))
    SHOULDER = {s: Vector(A.bone_world(arm, "upperarm." + s, "head"))
                for s in SIDES}
    FIST = {s: Vector(A.bone_world(arm, "hand." + s, "tail")) for s in SIDES}
    FOOT_DIR = {s: tuple(A.bone_direction(arm, "foot." + s)) for s in SIDES}
    sole0 = sole_low(arm)

    A.report("U07_IDENTITY", {
        "support": SUPPORT, "attack": ATTACK,
        "front_foot": "L" if ANK["L"].y < ANK["R"].y else "R",
        "pelvis_mm": mm(PELVIS),
        "pelvis_z_mm": round(PELVIS.z * 1000.0, 1),
        "shoulder_mm": {s: mm(SHOULDER[s]) for s in SIDES},
        "fist_mm": {s: mm(FIST[s]) for s in SIDES},
        "ankle_mm": {s: mm(ANK[s]) for s in SIDES},
        "knee_mm": {s: mm(KNEE[s]) for s in SIDES},
        "hip_mm": {s: mm(HIP[s]) for s in SIDES},
        "toe_mm": {s: mm(TOE[s]) for s in SIDES},
        "foot_rest_dir": {s: [round(v, 4) for v in FOOT_DIR[s]] for s in SIDES},
        "sole_lowest_mm": {s: mm(sole0[s]) for s in SIDES},
        "leg_bone_len_mm": {"thigh": round(A.L_THIGH * 1000.0, 1),
                            "shin": round(A.L_SHIN * 1000.0, 1),
                            "limit": round(LEG_LIMIT * 1000.0, 1)},
        "arm_bone_len_mm": {
            "upperarm": round(_bone_len(arm, "upperarm.R") * 1000.0, 1),
            "forearm": round(_bone_len(arm, "forearm.R") * 1000.0, 1),
            "hand": round(_bone_len(arm, "hand.R") * 1000.0, 1),
            "arm_total": round((_bone_len(arm, "upperarm.R")
                                + _bone_len(arm, "forearm.R")
                                + _bone_len(arm, "hand.R")) * 1000.0, 1)},
        "idle_hip_ankle_mm": {s: round((ANK[s] - HIP[s]).length * 1000.0, 1)
                              for s in SIDES},
        "idle_headroom_mm": {s: round((LEG_LIMIT - (ANK[s] - HIP[s]).length)
                                      * 1000.0, 1) for s in SIDES},
        "note": ("上勾拳：**后腿 R 驱动**（清单原文）。攻击侧 = R（脚跟离地蹬伸），"
                 "支撑脚 = 前脚 L（鞋底 −2~+6 mm）。"),
    })

    # ================================================================ 1 深蹲下界
    # 蓄力：骨盆下沉、双膝深屈。踝**不动**（平脚踩地）⟹ 髋→踝被压短，越深越安全。
    # 真正要量的是"腿还够不够"，以及"膝弯有多少"（knee_extend_ok 的伸展量上限）。
    crouch_rows = []
    for dz_mm in (-60, -90, -120, -150, -180, -210):
        row = {"pelvis_dz_mm": dz_mm,
               "pelvis_z_mm": round((PELVIS.z + dz_mm / 1000.0) * 1000.0, 1)}
        for side in SIDES:
            hip = HIP[side] + Vector((0.0, 0.0, dz_mm / 1000.0))
            row[side] = _leg_geom(hip, ANK[side], _leg_pole_from_pose(arm, side))
        crouch_rows.append(row)
    A.report("U07_CROUCH_SCAN", crouch_rows)
    A.report("U07_CROUCH_SUMMARY", {
        "rule": "余量 < 20 mm 就缩下沉量；本支双膝深屈，踝不动 ⟹ 下沉**增加**余量。",
        "deepest_safe_dz_mm": max(
            (r["pelvis_dz_mm"] for r in crouch_rows
             if min(r["L"]["headroom_mm"], r["R"]["headroom_mm"]) >= 20.0),
            default=None),
        "knee_bend_at_150": {s: next(r[s]["knee_bend_deg"] for r in crouch_rows
                                     if r["pelvis_dz_mm"] == -150)
                             for s in SIDES},
    })

    # ================================================================ 2 踮脚
    # ★ 本支最核心的一组数：`rise_ok` 要 +120 mm，而**脚平放时腿够不到**
    #   （骨盆 z 0.950 + 支撑脚踝 0.078 ⟹ 髋→踝 0.886 > 腿长 0.822）。
    #   ⟹ 上升只能靠"腿伸直 + 踮脚"，所以要把"跖屈 θ 能换多少踝高"量准。
    #   做法：把脚钉平后绕世界 X 叠 θ，量鞋底最低点（踝此时仍在 rest 位）
    #        ⟹ **需要的踝抬升 = −鞋底最低 z**；再量接触点的 y 漂移 ⟹ **前移补偿**。
    tip_rows = []
    base = {k: (dict(v) if k == "@loc" else tuple(v)) for k, v in idle.items()}
    base["toe.L"] = (0.0, 0.0, 0.0)
    base["toe.R"] = (0.0, 0.0, 0.0)
    for tip in (0, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55):
        row = {"tip_deg": tip}
        for side in SIDES:
            # ★ 必须在 **idle 姿态之上**做：`apply_pose` 会把未列出的骨归零，
            #   零姿态的踝在髋正下方（0.084, 0, 0.078），**不是** idle 的
            #   (0.1432, −0.1696, 0.0798) —— 首版就是这么量歪的。
            A.apply_pose(arm, base)
            A.keep_world_orientation(arm, "foot.L")
            A.keep_world_orientation(arm, "foot.R")
            WF.add_world_rx(arm, "foot." + side, tip)
            bpy.context.view_layer.update()
            low = sole_low(arm)[side]
            ank_now = Vector(A.bone_world(arm, "foot." + side, "head"))
            lift = -low.z
            row[side] = {
                "sole_low_z_mm": round(low.z * 1000.0, 2),
                "ankle_lift_mm": round(lift * 1000.0, 2),
                "contact_y_rel_ankle_mm": round(
                    (low.y - ank_now.y) * 1000.0, 1),
                "contact_drift_y_mm": round(
                    (low.y - sole0[side].y) * 1000.0, 1),
                # 不滑步所需的踝 y 平移（= 把接触点送回原处，负 = 向前）
                "ankle_fwd_mm": round((sole0[side].y - low.y) * 1000.0, 1),
                "ankle_z_after_mm": round(
                    (ANK[side].z + lift) * 1000.0, 1),
                "ankle_y_after_mm": round(
                    (ANK[side].y + sole0[side].y - low.y) * 1000.0, 1),
                "ankle_moved_mm": round((ank_now - ANK[side]).length * 1000.0, 3),
            }
        tip_rows.append(row)
    A.report("U07_TIP_SCAN", tip_rows)

    # 给定 θ，算出"贴地支撑"的踝目标，再看骨盆能升到多高。
    def tip_ankle(row, side):
        return Vector((ANK[side].x,
                       ANK[side].y + row[side]["ankle_fwd_mm"] / 1000.0,
                       ANK[side].z + row[side]["ankle_lift_mm"] / 1000.0))

    rise_rows = []
    for tip in (30, 35, 40, 45, 50):
        row = next(r for r in tip_rows if r["tip_deg"] == tip)
        for dz_mm in (100, 120, 140, 160):
            for dy_mm in (0, -60, -100):
                pelvis_z = PELVIS.z + dz_mm / 1000.0
                pelvis_y = dy_mm / 1000.0
                entry = {"tip_deg": tip, "pelvis_dz_mm": dz_mm,
                         "pelvis_dy_mm": dy_mm,
                         "pelvis_z_mm": round(pelvis_z * 1000.0, 1)}
                for side in SIDES:
                    hip = HIP[side] + Vector((0.0, pelvis_y, dz_mm / 1000.0))
                    entry[side] = _leg_geom(hip, tip_ankle(row, side),
                                            (0.35 if side == "L" else -0.35,
                                             -1.0, 0.0))
                rise_rows.append(entry)
    A.report("U07_RISE_SCAN", rise_rows)
    A.report("U07_RISE_SUMMARY", {
        "rule": ("`rise_ok`：命中帧骨盆 z − guard(830) ≥ **+120**，"
                 "且全程 min(pelvis z) 落在 [1, CROUCH_END]（先沉后升）。"
                 "支撑脚还要满足鞋底 −2~+6 ⟹ 踝高由踮脚严格决定。"),
        "note": ("dy 负 = 骨盆**前送**（`hip_drive_ok` 要 ≥60）。"
                 "按 side 看两条腿的余量：支撑腿余量 < 20 就降 dz 或加 θ。"),
        "min_pole_sin_fwd_out": round(min(
            min(r["L"]["pole_sin"], r["R"]["pole_sin"]) for r in rise_rows), 4),
        "support_headroom_by_pose": {
            "%d/%d/%d" % (r["tip_deg"], r["pelvis_dz_mm"], r["pelvis_dy_mm"]):
                r[SUPPORT]["headroom_mm"] for r in rise_rows},
    })

    # ================================================================ 3 盆高 + 拳高
    # 命中帧的躯干：上勾是**伸展**（后仰），骨盆高位、胸腔展开。
    HIT_TRUNK = {"pelvis": (-8.0, 0.0, 0.0), "spine_01": (-3.0, 0.0, 0.0),
                 "spine_02": (-3.0, 0.0, 0.0), "chest": (-14.0, 0.0, 0.0),
                 "neck": (6.0, 0.0, 0.0), "head": (8.0, 0.0, 0.0),
                 "shoulder.L": (-24.0, 0.0, 0.0), "shoulder.R": (-24.0, 0.0, 0.0),
                 "toe.L": (0.0, 0.0, 0.0), "toe.R": (0.0, 0.0, 0.0)}
    up_rows = []
    for dz_mm in (100, 120, 140, 150, 160):
        for dy_mm in (0, -60, -100):
            pose = dict(HIT_TRUNK)
            pose["@loc"] = {"pelvis": A.wloc(0.0, dy_mm / 1000.0,
                                             I1.DROP + dz_mm / 1000.0)}
            A.apply_pose(arm, pose)
            sh = Vector(A.bone_world(arm, "upperarm." + ATTACK, "head"))
            up = _bone_len(arm, "upperarm." + ATTACK)
            fore = _bone_len(arm, "forearm." + ATTACK)
            hand = _bone_len(arm, "hand." + ATTACK)
            entry = {"pelvis_dz_mm": dz_mm, "pelvis_dy_mm": dy_mm,
                     "pelvis_z_mm": round(
                         Vector(A.bone_world(arm, "pelvis", "head")).z * 1000.0, 1),
                     "shoulder_mm": mm(sh),
                     "arm_total_mm": round((up + fore + hand) * 1000.0, 1),
                     "fist_z_max_straight_up_mm": round(
                         (sh.z + up + fore + hand) * 1000.0, 1),
                     "fist_z_reach_90pct_mm": round(
                         (sh.z + (up + fore + hand) * 0.90) * 1000.0, 1)}
            up_rows.append(entry)
    A.report("U07_ARM_HEIGHT_SCAN", up_rows)

    # 真实 IK 复核：把拳峰目标放在 (x=−0.26, y=−0.16, z) 逐档试，报残差与肘 pole。
    A.apply_pose(arm, {"toe.L": (0.0, 0.0, 0.0), "toe.R": (0.0, 0.0, 0.0)})
    sh0 = Vector(A.bone_world(arm, "upperarm.R", "head"))
    up = _bone_len(arm, "upperarm.R")
    fore = _bone_len(arm, "forearm.R")
    hand = _bone_len(arm, "hand.R")
    ik_rows = []
    for z_mm in (1750, 1800, 1850, 1900, 1950, 2000):
        for pole_name, pole in (("out_dn", (-0.30, -1.0, -0.20)),
                                ("out", (-1.0, -0.20, 0.0)),
                                ("fwd", (0.0, -1.0, 0.0))):
            target = Vector((-0.26, -0.16, z_mm / 1000.0))
            entry = _arm_geom(sh0, target - Vector((0, 0, hand)), up, fore, pole)
            entry.update({"z_mm": z_mm, "pole": pole_name,
                          "fist_target_mm": mm(target)})
            ik_rows.append(entry)
    A.report("U07_ARM_IK_SCAN", ik_rows)

    # ================================================================ 4 腿的 pole
    # 上勾是"腿伸直 + 踮脚"，支撑腿髋→踝轴**接近竖直**；膝鼓出方向若取"正前方"，
    # 在轴近竖直时并不会退化（轴竖直 ⟹ 任意水平 pole 都有 |⊥|=1）。
    # 真正会退化的地方是**深蹲**那几帧（轴被压得很短、几乎水平）。
    pole_rows = []
    for dz_mm, dy_mm, tip in ((-150, 0, 0), (-120, 0, 0), (0, 0, 20),
                              (120, -60, 40), (140, -100, 45)):
        tip_row = min(tip_rows, key=lambda r: abs(r["tip_deg"] - tip))
        for side in SIDES:
            pose = {"pelvis": (14.0, 0.0, 0.0), "spine_01": (4.0, 0.0, 0.0),
                    "spine_02": (4.0, 0.0, 0.0), "chest": (3.0, 0.0, 0.0),
                    "toe.L": (0.0, 0.0, 0.0), "toe.R": (0.0, 0.0, 0.0),
                    "@loc": {"pelvis": A.wloc(0.0, dy_mm / 1000.0,
                                              I1.DROP + dz_mm / 1000.0)}}
            A.apply_pose(arm, pose)
            hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
            rest = tip_ankle(tip_row, side)
            for pole_name, pole in (("fwd", (0.0, -1.0, 0.0)),
                                    ("fwd_out", (0.35 if side == "L" else -0.35,
                                                 -1.0, 0.0)),
                                    ("down", (0.0, 0.0, -1.0))):
                geom = _leg_geom(hip, rest, pole)
                pole_rows.append({"dz_mm": dz_mm, "dy_mm": dy_mm, "tip": tip,
                                  "side": side, "pole": pole_name,
                                  "reach_mm": geom["reach_mm"],
                                  "headroom_mm": geom["headroom_mm"],
                                  "pole_sin": geom["pole_sin"]})
    A.report("U07_LEG_POLE_SCAN", pole_rows)
    A.report("U07_LEG_POLE_SUMMARY", {
        "rule": "`|pole⊥axis| ≥ 0.30` 否则走 `_knee_bulge` 接力（B04 第 3 件）。",
        "min_pole_sin": min(r["pole_sin"] for r in pole_rows),
        "worst": min(pole_rows, key=lambda r: r["pole_sin"]),
    })

    A.report("U07_DECISION", {
        "support_leg": SUPPORT, "attack_leg": ATTACK,
        "attack_fist": ATTACK,
        "plan_rule": ("`rise_ok` ≥ +120；`uppercut_height_ok` 拳峰 z ≥ 1800 且 "
                      "拳在骨盆前方；`knee_extend_ok` 单侧膝伸 ≥ 55°；"
                      "`hip_drive_ok` 骨盆前送 ≥ 60 mm。"),
        "note": ("本支的物理核心：**脚平放时腿够不到 +120 mm**，"
                 "上升必须「腿伸直 + 踮脚」一起给 —— 见 U07_TIP_SCAN / "
                 "U07_RISE_SCAN。"),
    })
    print("PROBE_UP07_DONE")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("PROBE_UP07_FAILURE " + traceback.format_exc())
