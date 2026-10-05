"""probe_rs —— A06 `Run_Stop` 开工前的实测探针（只读，不改工程）。

回答三个问题：
  1) `Run@48`（= A06 首帧）各关键骨的世界坐标与欧拉，作为 A06 的起点真值；
  2) 网格对象的名字与 bbox —— 找出"鞋"，以便按**对象**而不是按 x 符号测鞋底，
     避免两脚靠得近时 `lowest_z_by_side` 把左右串门；
  3) 每只鞋各自的 lowest z（按对象测），供两遍贴地闭环用。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python probe_rs.py
"""

import json
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A  # noqa: E402
import anim_walk_f as WF  # noqa: E402
import anim_run as R  # noqa: E402


def obj_lowest(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    matrix = evaluated.matrix_world
    best = None
    for vertex in mesh.vertices:
        point = matrix @ vertex.co
        if best is None or point.z < best[2]:
            best = (point.x, point.y, point.z)
    evaluated.to_mesh_clear()
    return best


def main():
    arm, meshes = A.open_animation_project()
    A.setup_scene()

    print("MESH_OBJECTS " + json.dumps(
        sorted(o.name for o in bpy.data.objects), ensure_ascii=False))
    info = {}
    for obj in meshes:
        corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
        info[obj.name] = {
            "z": [round(min(c.z for c in corners) * 1000.0, 1),
                  round(max(c.z for c in corners) * 1000.0, 1)],
            "x": [round(min(c.x for c in corners) * 1000.0, 1),
                  round(max(c.x for c in corners) * 1000.0, 1)],
            "y": [round(min(c.y for c in corners) * 1000.0, 1),
                  round(max(c.y for c in corners) * 1000.0, 1)],
        }
    A.report("OBJECT_BBOX", info)

    # ---- Run@48 姿态（A06 首帧真值）----
    pose = WF.gait_pose(arm, R.RUN, 0, meshes)
    A.apply_pose(arm, pose)
    bpy.context.view_layer.update()

    bones = ("pelvis", "chest", "neck", "head", "foot.L", "foot.R",
             "toe.L", "toe.R", "thigh.L", "thigh.R", "shin.L", "shin.R",
             "hand.L", "hand.R", "upperarm.L", "upperarm.R")
    data = {}
    for name in bones:
        head = A.bone_world(arm, name, "head")
        data[name] = [round(v * 1000.0, 1) for v in head]
    data["chest.tail(neck.head)"] = [round(v * 1000.0, 1)
                                     for v in A.bone_world(arm, "chest", "tail")]
    data["hand.L.tail"] = [round(v * 1000.0, 1)
                           for v in A.bone_world(arm, "hand.L", "tail")]
    data["hand.R.tail"] = [round(v * 1000.0, 1)
                           for v in A.bone_world(arm, "hand.R", "tail")]
    eul = {}
    for name in ("pelvis", "spine_01", "spine_02", "chest", "neck", "head",
                 "thigh.L", "thigh.R", "shin.L", "shin.R", "foot.L", "foot.R",
                 "shoulder.L", "shoulder.R", "upperarm.L", "upperarm.R"):
        eul[name] = [round(math.degrees(v), 3)
                     for v in arm.pose.bones[name].rotation_euler]
    data["euler"] = eul
    data["pelvis_loc_world"] = [
        round(v * 1000.0, 3) for v in (arm.matrix_world @
                                       arm.pose.bones["pelvis"].head)]
    A.report("RUN48_BONES_MM", data)

    lows = {}
    for obj in meshes:
        low = obj_lowest(obj)
        if low is not None and low[2] < 0.30:
            lows[obj.name] = [round(v * 1000.0, 2) for v in low]
    A.report("OBJ_LOWEST_NEAR_GROUND", lows)
    A.report("LOW_BY_SIDE", {k: round(v * 1000.0, 2)
                             for k, v in A.lowest_z_by_side(meshes).items()})

    # tip 角（世界 X 相对 rest）：
    A.report("FOOT_TIP_DEG", {s: round(A.world_tip_deg(arm, "foot." + s), 3)
                              for s in ("L", "R")})


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("PROBE_RS_FAILURE " + traceback.format_exc())
