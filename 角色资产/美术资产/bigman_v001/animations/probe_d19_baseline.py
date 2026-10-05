"""probe_d19_baseline —— D19 `Wall_Hit` 的**开工第一件测量**（只读，不改工程）。

与 `probe_d18_baseline.py` 同构，换 CASES / 量。
计划 §0 / §4 第 3 步要求实测：
  (a) 上游末帧（`Launch_Hit@34` / `Air_Hit@18`）的骨盆 z / y / vz / 后仰角；
  (b) 逐对象求**身体最后侧**（+Y 极值）—— 撞墙时**它**先接触；
  (c) 逐对象最低点（确认剪影最低行由谁接管）；
  (d) 确认弹道常量与 `Launch_Hit` **完全一致**。

用法：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python probe_d19_baseline.py
"""

import json
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A  # noqa: E402

# 上游候选：D12 Launch_Hit 末帧 / D13 Air_Hit 末帧 / 站姿参考
CASES = (
    ("D12_END", "Launch_Hit", 34),
    ("D13_END", "Air_Hit", 18),
    ("IDLE0", "Idle_01", 0),
)

WATCH = ("pelvis", "chest", "head", "neck", "hand.L", "hand.R",
         "thigh.L", "shin.L", "foot.L", "toe.L",
         "thigh.R", "shin.R", "foot.R", "toe.R",
         "upperarm.L", "upperarm.R", "forearm.L", "forearm.R")


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


def _rear_by_object(meshes):
    """每个对象的 **+Y 极值**（世界），单位 mm —— 撞墙时最先接触的是最大者。"""
    dg = bpy.context.evaluated_depsgraph_get()
    rows = {}
    for obj in meshes:
        ev = obj.evaluated_get(dg)
        me = ev.to_mesh()
        if len(me.vertices) == 0:
            ev.to_mesh_clear()
            continue
        mw = ev.matrix_world
        rows[obj.name] = max((mw @ v.co).y for v in me.vertices) * 1000.0
        ev.to_mesh_clear()
    return rows


def _pitch(arm, bone, action, frame):
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()
    mat = arm.matrix_world @ arm.pose.bones[bone].matrix
    d = (mat.to_3x3() @ Vector((0.0, 1.0, 0.0))).normalized()
    return math.degrees(math.asin(max(-1.0, min(1.0, d.z))))


def _pelvis_series(arm, action, f0, f1):
    """骨盆世界 (y, z)，用于估 vz / vy。"""
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    out = []
    for f in range(f0, f1 + 1):
        bpy.context.scene.frame_set(f)
        bpy.context.view_layer.update()
        p = arm.matrix_world @ arm.pose.bones["pelvis"].matrix.translation
        out.append((f, p.x * 1000.0, p.y * 1000.0, p.z * 1000.0))
    return out


def main():
    arm, meshes = A.open_animation_project()
    A.setup_scene()
    scene = bpy.context.scene
    out = {"cases": {}, "low": {}, "rear": {}}

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
                               "frame_range": [round(v, 3) for v in action.frame_range]}
        out["low"][label] = sorted(
            ({"z_mm": round(z, 2), "obj": n}
             for n, z in _low_by_object(meshes).items()),
            key=lambda r: r["z_mm"])[:8]
        out["rear"][label] = sorted(
            ({"y_mm": round(y, 2), "obj": n}
             for n, y in _rear_by_object(meshes).items()),
            key=lambda r: -r["y_mm"])[:8]
        out["cases"][label]["pitch_deg"] = {
            b: round(_pitch(arm, b, action, frame), 4)
            for b in ("pelvis", "chest", "head")}

    # 末帧竖速 / 水平后向速度（用最后两帧骨盆）
    for label, action_name, frame in CASES:
        if frame < 2:
            continue
        action = bpy.data.actions[action_name]
        ser = _pelvis_series(arm, action, frame - 2, frame)
        out["cases"][label]["pelvis_series"] = [
            {"frame": f, "x_mm": round(x, 3), "y_mm": round(y, 3), "z_mm": round(z, 3)}
            for (f, x, y, z) in ser]
        out["cases"][label]["vz_last_mm"] = round(ser[-1][3] - ser[-2][3], 4)
        out["cases"][label]["vy_last_mm"] = round(ser[-1][2] - ser[-2][2], 4)

    # 共享抛物线常量（与 Launch_Hit 对照）
    import anim_jump_start as JS
    T_ORIGIN = 2.5
    G = JS.G_PER_FRAME * 1000.0
    V0 = JS.TAKEOFF_SPEED * 1000.0
    Z0 = JS.TAKEOFF_PELVIS_Z * 1000.0

    def ball_z(frame):
        t = frame - T_ORIGIN
        return Z0 + V0 * t - 0.5 * G * t * t

    out["ballistic"] = {
        "T_ORIGIN": T_ORIGIN, "Z0_mm": Z0, "V0_mm_per_frame": V0,
        "G_mm_per_frame2": round(G, 5),
        "apex_frame": round(T_ORIGIN + V0 / G, 3),
        "apex_z_mm": round(Z0 + V0 ** 2 / (2 * G), 3),
        "z_at_34_mm": round(ball_z(34), 3),
        "z_at_52_mm": round(ball_z(52), 3),
        "vz_at_34_mm": round(V0 - G * (34 - T_ORIGIN), 4),
    }
    A.report("D19_BASE", out)


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("D19_BASE_FAILURE " + traceback.format_exc())
