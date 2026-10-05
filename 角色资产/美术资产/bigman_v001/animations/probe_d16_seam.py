"""probe_d16_seam —— D16 开工标定（只读，不改任何资产）。

量 D15 `Knockdown_B@20`（= D16 的首帧接缝）的：
  (a) 髋 / 踝 / 鞋底 世界坐标 + 髋-踝距离 + 膝角 + 髋屈角（供"腿层"幅度定标）；
  (b) 躯干各骨的 **世界俯仰** 与 **局部欧拉**（供 rx 增量口径）；
  (c) 肩 / 拳 / 肘 / 手骨朝向（供臂层）；
  (d) `@loc` 通道（root / pelvis 是否都有 location 键）。

用法：
    blender.exe --background --factory-startup --python probe_d16_seam.py
"""

import json
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A                    # noqa: E402

SEAM_ACTION = "Knockdown_B"
SEAM_FRAME = 20
SIDES = ("L", "R")
TORSO = ("root", "pelvis", "spine_01", "spine_02", "chest", "neck", "head")


def _pitch(direction):
    return -math.degrees(math.atan2(direction.y, direction.z))


def main():
    arm, _meshes = A.open_animation_project()
    A.setup_scene()
    scene = bpy.context.scene
    action = bpy.data.actions.get(SEAM_ACTION)
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    scene.frame_set(SEAM_FRAME)
    bpy.context.view_layer.update()

    out = {"seam": {"action": SEAM_ACTION, "frame": SEAM_FRAME}}

    # (a) 腿
    legs = {}
    for s in SIDES:
        hip = Vector(A.bone_world(arm, "thigh." + s, "head"))
        knee = Vector(A.bone_world(arm, "shin." + s, "head"))
        ank = Vector(A.bone_world(arm, "foot." + s, "head"))
        upper = Vector(A.bone_direction(arm, "thigh." + s)).normalized()
        lower = Vector(A.bone_direction(arm, "shin." + s)).normalized()
        legs[s] = {
            "hip_mm": [round(v * 1000.0, 2) for v in hip],
            "knee_mm": [round(v * 1000.0, 2) for v in knee],
            "ankle_mm": [round(v * 1000.0, 2) for v in ank],
            "hip_ankle_mm": round((ank - hip).length * 1000.0, 2),
            "hip_off_xy_mm": [round((ank.x - hip.x) * 1000.0, 2),
                              round((ank.y - hip.y) * 1000.0, 2)],
            "knee_deg": round(math.degrees(math.acos(
                max(-1.0, min(1.0, upper.dot(lower))))), 3),
        }
    out["legs"] = legs
    out["leg_limit_mm"] = round((A.L_THIGH + A.L_SHIN) * 1000.0, 3)
    sole = A.foot_lowest_by_side()
    out["sole_mm"] = {s: (None if sole[s] is None
                          else [round(v * 1000.0, 2) for v in sole[s]])
                      for s in SIDES}

    # (b) 躯干：世界俯仰 + 局部欧拉
    torso = {}
    for n in TORSO:
        pb = arm.pose.bones[n]
        torso[n] = {
            "world_pitch_deg": round(_pitch(Vector(A.bone_direction(arm, n))), 4),
            "local_euler_deg": [round(math.degrees(v), 4)
                                for v in pb.rotation_euler],
        }
    out["torso"] = torso

    # (c) 臂
    arms = {}
    for s in SIDES:
        sh = Vector(A.bone_world(arm, "upperarm." + s, "head"))
        el = Vector(A.bone_world(arm, "upperarm." + s, "tail"))
        wr = Vector(A.bone_world(arm, "forearm." + s, "tail"))
        fi = Vector(A.bone_world(arm, "hand." + s, "tail"))
        arms[s] = {
            "shoulder_mm": [round(v * 1000.0, 2) for v in sh],
            "elbow_mm": [round(v * 1000.0, 2) for v in el],
            "wrist_mm": [round(v * 1000.0, 2) for v in wr],
            "fist_mm": [round(v * 1000.0, 2) for v in fi],
            "span_mm": round((fi - sh).length * 1000.0, 2),
            "elbow_dir": [round(v, 5) for v in
                          Vector(A.bone_direction(arm, "upperarm." + s)).normalized()],
            "hand_dir": [round(v, 5) for v in
                         Vector(A.bone_direction(arm, "hand." + s)).normalized()],
            "arm_max_mm": round((arm.pose.bones["upperarm." + s].length
                                 + arm.pose.bones["forearm." + s].length
                                 + arm.pose.bones["hand." + s].length) * 1000.0, 2),
        }
    out["arms"] = arms

    # (d) location 通道
    loc_bones = sorted({c.data_path.split('"')[1] for c in action.fcurves
                        if c.data_path.endswith("location")})
    rot_bones = sorted({c.data_path.split('"')[1] for c in action.fcurves
                        if c.data_path.endswith("rotation_euler")})
    out["keyed"] = {"loc": loc_bones, "rot": len(rot_bones),
                    "frame_range": [int(v) for v in action.frame_range]}
    out["loc_values"] = {n: [round(v, 6) for v in arm.pose.bones[n].location]
                         for n in loc_bones if n in arm.pose.bones}

    # (e) 骨长
    out["bone_len_mm"] = {n: round(arm.pose.bones[n].length * 1000.0, 3)
                          for n in ("pelvis", "spine_01", "spine_02", "chest",
                                    "neck", "head", "thigh.L", "shin.L", "foot.L",
                                    "upperarm.L", "forearm.L", "hand.L")}
    A.report("D16_SEAM", out)


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("D16_SEAM_FAILURE " + traceback.format_exc())
