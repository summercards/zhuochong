"""probe_c07_baseline —— C07 `Ground_Smash` 开工前的「只量不做」探针。

清单 C07 计划 §4 第 2 步：
    「量 Idle 站架下的**双臂高举可达上限**（肩到过顶高度够不够）、
      **躯干 rx 开到 55° 时骨盆的位移**、以及**蹲到 640 mm 时的腿可达比**
      （`leg_seat` 的 `ratio`，须 <0.95）。」

本探针只读不写：不改 Action、不存盘、不导 GLB。回答三个数字问题：

  ① 高举顶：躯干后仰 sum −15°、骨盆抬到候选高度、双臂指向过顶（世界 z ≈ +0.97）
     ⟹ 双拳中点世界 z 是多少？比门禁 1850 mm 有多少余量？
  ② 砸下：躯干前折 sum +55°、骨盆沉到候选高度、双臂指向身前下
     ⟹ 双拳中点世界 z 是多少？低于门禁 320 mm 吗？拳有没有穿地（< −20 mm）？
  ③ 腿：上述两个姿态下（踝钉在 Idle 站架原处）`leg_seat` 的可达比是多少？
     （>0.995 会被截断 ⟹ 支撑脚会滑）

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python probe_c07_baseline.py
"""

import json
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A        # noqa: E402
import anim_idle_01 as I1   # noqa: E402
import anim_grab04 as G4    # noqa: E402
import anim_jump_start as JS  # noqa: E402

SIDES = ("L", "R")
ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")

IDLE_BASIS = {}
IDLE_DIR = {}
IDLE_KNEE_DIR = {}
ARM_LEN = {}
ANKLE = {}


def setup_idle(arm):
    """Idle_01@0 站架 + 骨基座（`leg_seat` / `aim_bone_ref` 的缺省基准）。"""
    if "Idle_01" not in bpy.data.actions:
        print("C07PROBE_BOOTSTRAP 缺 Idle_01，先补跑 A01")
        I1.main()
    arm, _meshes = A.open_animation_project()
    A.setup_scene()
    I1.idle_pose(arm, 0.0)
    IDLE_BASIS.clear()
    IDLE_DIR.clear()
    IDLE_KNEE_DIR.clear()
    ARM_LEN.clear()
    ANKLE.clear()
    for side in SIDES:
        hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
        knee = Vector(A.bone_world(arm, "thigh." + side, "tail"))
        IDLE_KNEE_DIR[side] = (knee - hip).normalized()
        for name in ("thigh." + side, "shin." + side):
            IDLE_BASIS[name] = arm.pose.bones[name].matrix.to_3x3().copy()
            IDLE_DIR[name] = A.bone_direction(arm, name)
        ANKLE[side] = Vector(A.bone_world(arm, "foot." + side, "head"))
        ARM_LEN[side] = {
            "upper": arm.pose.bones["upperarm." + side].length,
            "forearm": arm.pose.bones["forearm." + side].length,
            "hand": arm.pose.bones["hand." + side].length}
    for name in ARM_BONES:
        IDLE_BASIS[name] = arm.pose.bones[name].matrix.to_3x3().copy()
        IDLE_DIR[name] = A.bone_direction(arm, name)
    G4.IDLE_BASIS.clear()
    G4.IDLE_BASIS.update(IDLE_BASIS)
    G4.IDLE_DIR.clear()
    G4.IDLE_DIR.update(IDLE_DIR)
    G4.IDLE_KNEE_DIR.clear()
    G4.IDLE_KNEE_DIR.update(IDLE_KNEE_DIR)
    G4.ARM_LEN.clear()
    for side in SIDES:
        G4.ARM_LEN[side] = dict(ARM_LEN[side])
    return arm


def solve(arm, rot, pelvis_z, arm_dirs, pelvis_y=0.0, pelvis_x=0.0):
    """把给定躯干 + 骨盆高度 + 手臂方向摆出来，返回实测。"""
    pose = dict(rot)
    pose["@loc"] = {"pelvis": A.wloc(pelvis_x, pelvis_y, pelvis_z - 0.900)}
    A.apply_pose(arm, pose)
    for side in SIDES:
        G4.leg_seat(arm, pose, side, tuple(ANKLE[side]), IDLE_KNEE_DIR[side])
    for side in SIDES:
        A.keep_world_orientation(arm, "foot." + side)
    for bone in ARM_BONES:
        pose[bone] = JS._unwrap_xyz(
            None, G4.aim_bone_ref(arm, bone, arm_dirs[bone],
                                  IDLE_BASIS[bone], IDLE_DIR[bone]))
    bpy.context.view_layer.update()

    out = {}
    pelvis = Vector(A.bone_world(arm, "pelvis", "head"))
    chest = Vector(A.bone_world(arm, "chest", "tail"))
    out["pelvis_z_mm"] = round(pelvis.z * 1000.0, 2)
    out["shoulder_z_mm"] = {s: round(A.bone_world(
        arm, "upperarm." + s, "head").z * 1000.0, 1) for s in SIDES}
    fists = {s: Vector(A.bone_world(arm, "hand." + s, "tail")) for s in SIDES}
    out["fist_mm"] = {s: [round(v * 1000.0, 1) for v in fists[s]]
                      for s in SIDES}
    mid = (fists["L"] + fists["R"]) * 0.5
    out["fist_mid_mm"] = [round(v * 1000.0, 1) for v in mid]
    out["fist_gap_mm"] = round((fists["L"] - fists["R"]).length * 1000.0, 1)
    limit = A.L_THIGH + A.L_SHIN
    out["leg_ratio"] = {}
    for side in SIDES:
        hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
        ach = Vector(A.bone_world(arm, "foot." + side, "head"))
        out["leg_ratio"][side] = round((ach - hip).length / limit, 5)
    out["torso_sum_rx_deg"] = round(sum(rot[b][0] for b in
                                        ("pelvis", "spine_01", "spine_02",
                                         "chest")), 2)
    out["chest_z_mm"] = round(chest.z * 1000.0, 1)
    low = A.foot_lowest_by_side()
    out["sole_mm"] = {s: (None if low[s] is None
                          else round(low[s][2] * 1000.0, 2)) for s in SIDES}
    return out


def main():
    arm = setup_idle(arm=None)
    A.report("C07PROBE_IDLE", {
        "ankle_mm": {s: [round(v * 1000.0, 2) for v in ANKLE[s]]
                     for s in SIDES},
        "arm_len_mm": {s: {k: round(v * 1000.0, 2) for k, v in d.items()}
                       for s, d in ARM_LEN.items()},
        "idle_shoulder_z_mm": {
            s: round(A.bone_world(arm, "upperarm." + s, "head").z * 1000.0, 1)
            for s in SIDES},
        "idle_fist_mid_mm": [round(v * 1000.0, 1) for v in (
            (Vector(A.bone_world(arm, "hand.L", "tail"))
             + Vector(A.bone_world(arm, "hand.R", "tail"))) * 0.5)],
    })

    # ---------------------------------------------------------------- ① 高举顶
    raise_rot = {
        "pelvis": (-8.0, 0.0, 0.0), "spine_01": (-3.0, 0.0, 0.0),
        "spine_02": (-2.0, 0.0, 0.0), "chest": (-2.0, 0.0, 0.0),
        "neck": (14.0, 0.0, 0.0), "head": (6.0, 0.0, 0.0),
        "shoulder.L": (14.0, 0.0, 0.0), "shoulder.R": (14.0, 0.0, 0.0),
    }
    up_dir = {"upperarm.L": (0.16, 0.06, 0.985),
              "forearm.L": (0.14, 0.05, 0.988),
              "hand.L": (0.12, 0.04, 0.992),
              "upperarm.R": (-0.16, 0.06, 0.985),
              "forearm.R": (-0.14, 0.05, 0.988),
              "hand.R": (-0.12, 0.04, 0.992)}
    rows = []
    for pz in (0.830, 0.850, 0.870, 0.890):
        for sh in (10.0, 14.0, 18.0, 22.0):
            rot = dict(raise_rot)
            rot["shoulder.L"] = (sh, 0.0, 0.0)
            rot["shoulder.R"] = (sh, 0.0, 0.0)
            res = solve(arm, rot, pz, up_dir)
            res["pelvis_z_arg"] = pz
            res["shoulder_rx"] = sh
            rows.append(res)
    A.report("C07PROBE_RAISE", {
        "rows": rows,
        "note": "门禁 smash_height_ok：fist_mid_mm[2] >= 1850；leg_ratio 须 <0.995",
        "best_over_1850_mm": round(max(r["fist_mid_mm"][2] for r in rows), 1),
    })

    # ---------------------------------------------------------------- ② 砸下
    smash_rot = {
        "pelvis": (22.0, 0.0, 0.0), "spine_01": (11.0, 0.0, 0.0),
        "spine_02": (11.0, 0.0, 0.0), "chest": (11.0, 0.0, 0.0),
        "neck": (-14.0, 0.0, 0.0), "head": (-4.0, 0.0, 0.0),
        "shoulder.L": (-6.0, 0.0, 0.0), "shoulder.R": (-6.0, 0.0, 0.0),
    }
    down_dir = {"upperarm.L": (0.24, -0.44, -0.866),
                "forearm.L": (0.20, -0.50, -0.843),
                "hand.L": (0.18, -0.52, -0.835),
                "upperarm.R": (-0.24, -0.44, -0.866),
                "forearm.R": (-0.20, -0.50, -0.843),
                "hand.R": (-0.18, -0.52, -0.835)}
    rows = []
    for pz in (0.560, 0.590, 0.620, 0.650):
        rot = dict(smash_rot)
        res = solve(arm, rot, pz, down_dir)
        res["pelvis_z_arg"] = pz
        rows.append(res)
    A.report("C07PROBE_SMASH", {
        "rows": rows,
        "note": "门禁 smash_depth_ok：fist_mid_mm[2] <= 320；"
                "squat_depth_ok：pelvis_z <= 640；拳不许低于 −20 mm",
    })


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("C07PROBE_FAILURE " + traceback.format_exc())
