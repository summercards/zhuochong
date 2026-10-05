"""probe_d18_baseline —— D18 `GetUp_B` 的**起步实测**（只读，不改任何工程文件）。

与 `probe_d17_baseline.py` 同构，只换 CASES：
  (a) 起点 = **`Knockdown_B@20`**（仰面）—— 实测 pelvis 世界 z / y、后脑 z、
      躯干仰角（俯仰）、膝屈角，作为 D18 竖直通道的**起点锚**（不许照抄 D17 的 220.0 / −550.0）。
  (b) 终点 = **`Idle_01@0`**（战斗站姿）—— 实测骨盆 z 与双脚世界 xy。
  (c) 逐对象最低点 —— 确认**仰卧段**剪影最低行由谁接管（后脑 / 肩背 / 臀 / 鞋跟？）。

用法：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python probe_d18_baseline.py
"""

import json
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A  # noqa: E402

CASES = (("D15_END", "Knockdown_B", 20), ("IDLE0", "Idle_01", 0))

WATCH = ("pelvis", "chest", "head", "neck", "hand.L", "hand.R",
         "thigh.L", "shin.L", "foot.L", "toe.L",
         "thigh.R", "shin.R", "foot.R", "toe.R")


def _low_by_object(meshes):
    dg = bpy.context.evaluated_depsgraph_get()
    rows = {}
    for obj in meshes:
        ev = obj.evaluated_get(dg)
        me = ev.to_mesh()
        if len(me.vertices) == 0:
            ev.to_mesh_clear()
            continue
        mw = ev.matrix_world
        rows[obj.name] = min((mw @ v.co).z for v in me.vertices) * 1000.0
        ev.to_mesh_clear()
    return rows


def _pitch(arm, bone, action, frame):
    """世界俯仰（deg）：骨骼世界 Y 轴（head→tail 方向）与水平面的夹角。

    本项目约定 +X = 角色左、+Y = 身后、+Z = 上、正面朝 −Y。
    仰面躺平 ⟹ 躯干朝上/后 ⟹ 俯仰接近 −88°（承接 D15 的 `supine_pitch_end_deg`）。
    """
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()
    mat = arm.matrix_world @ arm.pose.bones[bone].matrix
    d = (mat.to_3x3() @ Vector((0.0, 1.0, 0.0))).normalized()
    return math.degrees(math.asin(max(-1.0, min(1.0, d.z))))


def main():
    arm, meshes = A.open_animation_project()
    A.setup_scene()
    scene = bpy.context.scene
    out = {"cases": {}, "low": {}}

    for label, action_name, frame in CASES:
        action = bpy.data.actions[action_name]
        arm.animation_data.action = action
        A._bind_slot(arm, action)
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        head, tail = {}, {}
        for name in WATCH:
            pb = arm.pose.bones[name]
            head[name] = [round(v * 1000.0, 3)
                          for v in (arm.matrix_world @ pb.matrix).translation]
            tail[name] = [round(v * 1000.0, 3)
                          for v in (arm.matrix_world @ pb.tail)]
        out["cases"][label] = {"action": action_name, "frame": frame,
                               "head": head, "tail": tail,
                               "frame_range": list(action.frame_range),
                               "bones": len(action.fcurves) and len(
                                   {fc.data_path for fc in action.fcurves})}
        out["low"][label] = sorted(
            ({"z_mm": round(z, 2), "obj": n}
             for n, z in _low_by_object(meshes).items()),
            key=lambda r: r["z_mm"])[:10]
        out["cases"][label]["pitch_deg"] = {
            b: round(_pitch(arm, b, action, frame), 4)
            for b in ("pelvis", "chest", "head")}

    # 让"膝屈角"可读：shin 相对 thigh 的角度（世界方向夹角）
    for label, _a, _f in CASES:
        t = Vector(out["cases"][label]["tail"]["thigh.L"]) - Vector(
            out["cases"][label]["head"]["thigh.L"])
        s = Vector(out["cases"][label]["tail"]["shin.L"]) - Vector(
            out["cases"][label]["head"]["shin.L"])
        if t.length > 0 and s.length > 0:
            out["cases"][label]["knee_deg_L"] = round(
                math.degrees(t.angle(s)), 4)

    d = out["cases"]["D15_END"]
    i = out["cases"]["IDLE0"]
    out["span"] = {
        "pelvis_z_mm": [d["head"]["pelvis"][2], i["head"]["pelvis"][2]],
        "pelvis_y_mm": [d["head"]["pelvis"][1], i["head"]["pelvis"][1]],
        "pelvis_z_rise_mm": round(i["head"]["pelvis"][2] - d["head"]["pelvis"][2], 3),
        "pelvis_y_travel_mm": round(i["head"]["pelvis"][1] - d["head"]["pelvis"][1], 3),
        "head_z_mm": [d["head"]["head"][2], i["head"]["head"][2]],
    }
    A.report("D18_BASE", out)


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("D18_BASE_FAILURE " + traceback.format_exc())
