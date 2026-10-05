"""probe_d08_sole —— 诊断 D08 迈步脚 L 末帧鞋底 −4.55 mm 的来源。

问三件事（逐帧）：
  1. `foot.<s>` 的**世界朝向**与 rest 基的夹角（度）—— 若 ≈0 说明"钉回 rest"成立。
  2. `foot.<s>` head 的世界 z（踝高）与目标踝高之差（mm）。
  3. 该侧鞋对象（`A.FOOT_MESHES`）最低顶点的世界 (x,y,z) —— 分清是"脚跟"还是"脚尖"最低。

用法：
  "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" --background \
      --factory-startup --python probe_d08_sole.py
"""
import json
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anim_lib as A  # noqa: E402

ACTION = os.environ.get("D08_SOLE_ACTION", "Hit_Heavy_B")
FRAMES = [0, 4, 8, 17, 29, 34, 42]
SIDES = ("L", "R")


def basis_gap(arm, name):
    pose_bone = arm.pose.bones[name]
    rest = pose_bone.bone.matrix_local.to_3x3().to_quaternion()
    now = pose_bone.matrix.to_3x3().to_quaternion()
    dot = abs(max(-1.0, min(1.0, now.dot(rest))))
    return math.degrees(2.0 * math.acos(dot))


def main():
    arm, _meshes = A.open_animation_project()
    A.setup_scene()
    action = bpy.data.actions.get(ACTION)
    if action is None:
        raise RuntimeError("找不到 Action %s" % ACTION)
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)

    scene = bpy.context.scene
    rows = {}
    for frame in FRAMES:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        row = {}
        for side in SIDES:
            foot = "foot." + side
            objects = [bpy.data.objects[n] for n in A.FOOT_MESHES[side]
                       if n in bpy.data.objects]
            low = A.lowest_point_of(objects)
            row[side] = {
                "foot_head_mm": [round(v * 1000.0, 2)
                                 for v in A.bone_world(arm, foot, "head")],
                "foot_tail_mm": [round(v * 1000.0, 2)
                                 for v in A.bone_world(arm, foot, "tail")],
                "toe_head_mm": [round(v * 1000.0, 2)
                                for v in A.bone_world(arm, "toe." + side, "head")],
                "basis_vs_rest_deg": round(basis_gap(arm, foot), 4),
                "shoe_low_mm": None if low is None else [round(v * 1000.0, 2)
                                                         for v in low],
                "shoe_low_z_mm": None if low is None else round(low[2] * 1000.0, 2),
            }
        # 也报 `lowest_z_by_side` 的分半口径（判据用的就是这个）
        low = A.lowest_z_by_side(None)
        row["lowest_z_by_side_mm"] = {s: round(low[s] * 1000.0, 2) for s in SIDES}
        rows[str(frame)] = row
    print("D08_SOLE " + json.dumps(rows, ensure_ascii=False))


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("D08_SOLE_FAILURE " + traceback.format_exc())
