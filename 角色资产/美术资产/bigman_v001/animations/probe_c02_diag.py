# -*- coding: utf-8 -*-
"""C02 `Launcher` 门禁诊断探针 —— 不改任何东西，只读已存盘的 `Launcher` Action。

用途：把 `stance_pivot_ok` / `stance_sole_ok` / `ik_reach_ok` / `decel_smooth_ok`
四条红项的**逐帧真值**打出来，替代心算与公式推断（§0.6 硬约束）。

跑法：在 `animations` 目录下
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
        --background --factory-startup --python probe_c02_diag.py
"""
import json
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import anim_lib as A  # noqa: E402
import anim_launcher02 as L2  # noqa: E402


def _front_vertex_track(arm, action, side):
    """诊断用：盯死"首帧鞋底最前缘最低顶点"，逐帧报它的世界坐标。

    与 `anim_launcher02.pivot_series` 同口径（用固定顶点，不用逐帧找最低顶点 ——
    平放时整块鞋底 z 相同，逐帧找最低点会沿 250 mm 鞋底乱跳）。
    """
    scene = bpy.context.scene
    previous = arm.animation_data.action if arm.animation_data else None
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    deps = bpy.context.evaluated_depsgraph_get()

    def snapshot(frame):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        out = {}
        for name in A.FOOT_MESHES[side]:
            obj = bpy.data.objects.get(name)
            if obj is None:
                continue
            evaluated = obj.evaluated_get(deps)
            mesh = evaluated.to_mesh()
            matrix = evaluated.matrix_world
            out[name] = [(matrix @ v.co) for v in mesh.vertices]
            evaluated.to_mesh_clear()
        return out

    first = snapshot(0)
    best = None
    for name, points in first.items():
        for index, point in enumerate(points):
            if best is None or point.z < best[0].z - 1e-9:
                best = (point, name, index)
            elif abs(point.z - best[0].z) <= 1e-9 and point.y < best[0].y:
                best = (point, name, index)
    name, index = best[1], best[2]

    out = {}
    for frame in range(0, L2.TOTAL + 1):
        points = snapshot(frame)[name]
        point = points[index]
        out[frame] = (point.x, point.y, point.z)
    if previous is not None:
        arm.animation_data.action = previous
    return out


def main():
    arm, meshes = A.open_animation_project()
    action = bpy.data.actions.get(L2.NAME)
    if action is None:
        print("C02DIAG_NO_ACTION")
        return

    foots = L2.foot_series(arm, action, meshes)
    contacts = {s: _front_vertex_track(arm, action, s) for s in L2.SIDES}

    limit = (A.L_THIGH + A.L_SHIN) * 1000.0
    print("C02DIAG_LIMIT_MM %.3f" % limit)

    scene = bpy.context.scene
    prev = arm.animation_data.action if arm.animation_data else None
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)

    for f in foots:
        n = f["frame"]
        scene.frame_set(n)
        bpy.context.view_layer.update()
        qL = arm.pose.bones["foot.L"].matrix.to_quaternion()
        qR = arm.pose.bones["foot.R"].matrix.to_quaternion()
        row = {
            "f": n,
            "w": L2.window_of("L", n), "wR": L2.window_of("R", n),
            "tipL": round(L2.tip_of("L", n), 2),
            "tipR": round(L2.tip_of("R", n), 2),
            "pel": [round(v * 1000.0, 1) for v in f["pelvis"]],
            "ancL": [round(v * 1000.0, 1) for v in f["ankle_L"]],
            "ancR": [round(v * 1000.0, 1) for v in f["ankle_R"]],
            "sL": (None if f["sole_L"] is None
                   else round(f["sole_L"] * 1000.0, 3)),
            "sR": (None if f["sole_R"] is None
                   else round(f["sole_R"] * 1000.0, 3)),
            "rL": round(f["reach_L"] * 1000.0, 2),
            "rR": round(f["reach_R"] * 1000.0, 2),
            "overL": round(f["reach_L"] * 1000.0 - limit, 2),
            "overR": round(f["reach_R"] * 1000.0 - limit, 2),
            "cL": [round(c * 1000.0, 2) for c in contacts["L"][n]],
            "cR": [round(c * 1000.0, 2) for c in contacts["R"][n]],
            "fqL": [round(v, 5) for v in qL],
            "fqR": [round(v, 5) for v in qR],
        }
        print("C02DIAG " + json.dumps(row))

    if prev is not None:
        arm.animation_data.action = prev


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("C02DIAG_FAILURE " + traceback.format_exc())
