"""probe_light01 —— B01 `Light_01` 轻拳1 的开工探针（只读，不改工程）。

为什么非要先跑它：
  ① 清单要求「开工第一步：量 `Idle_01@0` 双脚世界 Y 定"前手"」—— 从成品读，不手抄。
  ② A13 定案要求「先量 strike 姿态的 `max_abs_euler_y_deg`，>45° 先换等价族再插值」。
     本探针把候选出拳姿态逐个 aim 出来，直接报 |Y|、报「guard→strike 的逐分量欧拉差」
     —— 因为 `no_teleport ≤25°/帧` 的预算就是从这个差里分的（本支的真约束）。
  ③ 顺手量「拳峰相对胸骨顶的前伸量」，确认 `strike_reach_ok`（≥320 mm 增量）能不能达到。

用法：
    blender --background --factory-startup --python probe_light01.py
"""

import json
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A          # noqa: E402
import anim_idle_01 as I1     # noqa: E402
import anim_jump_start as JS  # noqa: E402

ARM6 = ("upperarm.L", "forearm.L", "hand.L",
        "upperarm.R", "forearm.R", "hand.R")
FINGERS = tuple(A.FIST.keys())

# 躯干八骨（与 A13 的 TRUNK_KEYS 同一套）
TRUNK8 = ("pelvis", "spine_01", "spine_02", "chest", "neck", "head",
          "shoulder.L", "shoulder.R")

# ---------------------------------------------------------------- 候选姿态
# 出拳躯干：髋微转（ry<0 = 左肩前送）、前肩推前（shoulder.L rz<0）、后肩后拉。
TRUNK_STRIKE = {
    "pelvis": (6.0, -3.0, 0.0),
    "spine_01": (3.0, -2.0, 0.0),
    "spine_02": (3.0, -2.0, 0.0),
    "chest": (3.0, -4.0, 0.0),
    "neck": (-5.0, 0.0, 0.0),
    "head": (5.0, 0.0, 0.0),
    "shoulder.L": (-6.0, 0.0, -9.0),
    "shoulder.R": (-16.0, 0.0, -4.0),
}

# 前摇躯干：与出拳反向 —— 髋反向微转、前肩略收、重心略后。
TRUNK_COIL = {
    "pelvis": (5.0, 2.0, 0.0),
    "spine_01": (2.4, 1.4, 0.0),
    "spine_02": (2.4, 1.4, 0.0),
    "chest": (2.0, 2.6, 0.0),
    "neck": (-6.0, -1.0, 0.0),
    "head": (5.0, -1.0, 0.0),
    "shoulder.L": (-17.0, 0.0, 4.0),
    "shoulder.R": (-18.0, 0.0, 1.0),
}

# 候选出拳手臂方向（世界单位向量，front hand = L 待实测确认）
CANDIDATES = {
    "S1": {
        "upperarm.L": (0.16, -0.96, -0.22),
        "forearm.L": (0.05, -0.999, -0.02),
        "hand.L": (0.02, -1.0, -0.01),
        "upperarm.R": (-0.30, -0.18, -0.94),
        "forearm.R": (0.34, -0.26, 0.90),
        "hand.R": (0.18, -0.68, 0.71),
    },
    "S2": {   # 更平更高（肩高平举）
        "upperarm.L": (0.20, -0.97, -0.10),
        "forearm.L": (0.06, -0.998, -0.01),
        "hand.L": (0.02, -1.0, 0.0),
        "upperarm.R": (-0.32, -0.22, -0.92),
        "forearm.R": (0.36, -0.28, 0.89),
        "hand.R": (0.20, -0.70, 0.68),
    },
    "S3": {   # 略低、略内（打在胸口高度）
        "upperarm.L": (0.12, -0.95, -0.28),
        "forearm.L": (0.04, -0.998, -0.05),
        "hand.L": (0.02, -1.0, -0.03),
        "upperarm.R": (-0.30, -0.18, -0.94),
        "forearm.R": (0.34, -0.26, 0.90),
        "hand.R": (0.18, -0.68, 0.71),
    },
    "C1": {   # 前摇：拳略后收 20 mm、肘收、肩后
        "upperarm.L": (0.30, -0.16, -0.94),
        "forearm.L": (-0.28, -0.22, 0.93),
        "hand.L": (-0.16, -0.52, 0.84),
        "upperarm.R": (-0.24, -0.14, -0.96),
        "forearm.R": (0.36, -0.16, 0.92),
        "hand.R": (0.20, -0.52, 0.83),
    },
}


def mm(v):
    return [round(x * 1000.0, 1) for x in v]


def trunk_pose(trunk):
    return {name: tuple(trunk[name]) for name in TRUNK8}


def aim_arms(arm, pose, dirs):
    A.apply_pose(arm, pose)
    out = {}
    for bone in ARM6:
        out[bone] = A.aim_bone(arm, bone, dirs[bone])
    return out


def euler_of(arm, names):
    return {n: tuple(math.degrees(v) for v in arm.pose.bones[n].rotation_euler)
            for n in names}


def main():
    arm, _meshes = A.open_animation_project()
    A.setup_scene()

    if "Idle_01" not in bpy.data.actions:
        print("PROBE_BOOTSTRAP 缺 Idle_01，先补跑 A01")
        I1.main()
        arm, _meshes = A.open_animation_project()
        A.setup_scene()

    # ---------- ① `Idle_01@0` 站架真值（前手 = 哪只脚在前） ----------
    I1.idle_pose(arm, 0.0)
    ankle = {s: Vector(A.bone_world(arm, "foot." + s, "head")) for s in ("L", "R")}
    toetip = {s: Vector(A.bone_world(arm, "foot." + s, "tail")) for s in ("L", "R")}
    sternum = Vector(A.bone_world(arm, "neck", "head"))
    fist = {s: Vector(A.bone_world(arm, "hand." + s, "tail")) for s in ("L", "R")}
    shoulder = {s: Vector(A.bone_world(arm, "upperarm." + s, "head"))
                for s in ("L", "R")}
    pelvis = Vector(A.bone_world(arm, "pelvis", "head"))
    E_GUARD = euler_of(arm, ARM6)
    A.report("LIGHT01_IDLE_TRUTH", {
        "ankle_mm": {s: mm(ankle[s]) for s in ankle},
        "toe_tip_mm": {s: mm(toetip[s]) for s in toetip},
        "sternum_mm": mm(sternum),
        "fist_mm": {s: mm(fist[s]) for s in fist},
        "shoulder_mm": {s: mm(shoulder[s]) for s in shoulder},
        "pelvis_mm": mm(pelvis),
        "front_foot": "L" if ankle["L"].y < ankle["R"].y else "R",
        "front_hand_predicted": "L",
        "guard_arm_euler_deg": {k: [round(x, 3) for x in v]
                                for k, v in E_GUARD.items()},
        "guard_reach_mm": {s: round((sternum.y - fist[s].y) * 1000.0, 1)
                           for s in ("L", "R")},
    })

    # ---------- ② 候选姿态体检 ----------
    rows = {}
    for tag, dirs in CANDIDATES.items():
        strike = tag.startswith("S")
        trunk = trunk_pose(TRUNK_STRIKE if strike else TRUNK_COIL)
        pose = dict(trunk)
        pose.update(A.FIST)
        e = aim_arms(arm, pose, dirs)
        world_fist = {s: Vector(A.bone_world(arm, "hand." + s, "tail"))
                      for s in ("L", "R")}
        world_sh = {s: Vector(A.bone_world(arm, "upperarm." + s, "head"))
                    for s in ("L", "R")}
        world_elbow = {s: Vector(A.bone_world(arm, "forearm." + s, "head"))
                       for s in ("L", "R")}
        world_wrist = {s: Vector(A.bone_world(arm, "hand." + s, "head"))
                       for s in ("L", "R")}
        line = {}
        for s in ("L", "R"):
            upper = (world_elbow[s] - world_sh[s]).length
            fore = (world_wrist[s] - world_elbow[s]).length
            span = (world_wrist[s] - world_sh[s]).length
            line[s] = round(span / max(1e-9, upper + fore), 4)
        delta = {b: [round(e[b][i] - E_GUARD[b][i], 2) for i in range(3)]
                 for b in ARM6}
        rows[tag] = {
            "euler_deg": {b: [round(x, 2) for x in e[b]] for b in ARM6},
            "max_abs_euler_y_deg": round(max(abs(e[b][1]) for b in ARM6), 2),
            "max_abs_euler_x_deg": round(max(abs(e[b][0]) for b in ARM6), 2),
            "max_abs_euler_z_deg": round(max(abs(e[b][2]) for b in ARM6), 2),
            "delta_from_guard_deg": delta,
            "max_comp_delta_deg": round(max(max(abs(x) for x in delta[b])
                                            for b in ARM6), 2),
            "fist_mm": {s: mm(world_fist[s]) for s in ("L", "R")},
            "reach_from_sternum_mm": {
                s: round((sternum.y - world_fist[s].y) * 1000.0, 1)
                for s in ("L", "R")},
            "reach_gain_mm": {
                s: round((fist[s].y - world_fist[s].y) * 1000.0, 1)
                for s in ("L", "R")},
            "strike_line_ratio": line,
        }
    A.report("LIGHT01_CANDIDATES", rows)

    # ---------- ③ 出拳姿态的骨盆前送预算 ----------
    print("LIGHT01_NOTE 前手=%s（ankle.L.y=%.1f mm vs ankle.R.y=%.1f mm）"
          % ("L" if ankle["L"].y < ankle["R"].y else "R",
             ankle["L"].y * 1000.0, ankle["R"].y * 1000.0))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("PROBE_LIGHT01_FAILURE " + traceback.format_exc())
