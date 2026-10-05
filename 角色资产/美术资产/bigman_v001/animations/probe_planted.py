"""A06 支撑段诊断（只读）：L 脚第二支撑窗口 [20,54] 逐帧数据。

问题：`foot.L` 骨行程 1.798 mm，但 `sole_low`（鞋底最低顶点）行程 5.424 mm。
要分辨是"脚真在滑"还是"最低顶点在并列候选间跳变"。

做法：
  1) 用 depsgraph **求值后**的网格（不是 data.vertices，那是未变形的静置坐标）；
  2) 记下 f=20 的最低顶点索引，之后**追同一个索引**的世界坐标行程
     —— 鞋是刚体，这才是"滑不滑"的正解；
  3) 同时记每帧最低顶点集合的规模与 xy 展布，看 argmin 是否在跳。
"""
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import anim_lib as A

FRAMES = list(range(20, 55))
NAMES = ("Shoe_Heel_L", "Shoe_Sole_L", "Shoe_Toe_Cap_L", "Shoe_Upper_L")


def evaluated_vertices():
    """[(对象名, 顶点索引, 世界坐标)]，来自求值后的网格。"""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    out = []
    for name in NAMES:
        obj = bpy.data.objects.get(name)
        if obj is None:
            continue
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        matrix = evaluated.matrix_world
        for index, vertex in enumerate(mesh.vertices):
            out.append((name, index, matrix @ vertex.co))
        evaluated.to_mesh_clear()
    return out


def main():
    arm, meshes = A.open_animation_project()
    A.setup_scene()
    action = bpy.data.actions["Run_Stop"]
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    scene = bpy.context.scene

    trackers = None
    origin = None
    rows = []
    for frame in FRAMES:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        verts = evaluated_vertices()
        low = min(v[2].z for v in verts)
        tied = [v for v in verts if v[2].z <= low + 1e-7]
        spread = max((Vector((a[2].x - b[2].x, a[2].y - b[2].y, 0.0)).length
                      for a in tied for b in tied), default=0.0)
        if trackers is None:
            trackers = [(v[0], v[1]) for v in tied]
            origin = {(v[0], v[1]): v[2] for v in tied}
        current = {(v[0], v[1]): v[2] for v in verts}
        travel = max((current[key] - origin[key]).length
                     for key in trackers) * 1000.0
        foot = A.bone_world(arm, "foot.L", "head")
        rows.append((frame, foot, low, len(tied), spread, travel))

    print("PLANTED_TRACK header frame foot_mm low_z_mm tied spread_mm "
          "tracked_travel_mm| toe_mm foot_dir rot_deg")
    basis_ref = None
    for row in rows:
        frame, foot, low, tied, spread, travel = row
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        toe = A.bone_world(arm, "toe.L", "head")
        basis = arm.pose.bones["foot.L"].matrix.to_3x3().copy()
        if basis_ref is None:
            basis_ref = basis
        rot = math.degrees((basis_ref.transposed() @ basis).to_quaternion().angle)
        direction = A.bone_direction(arm, "foot.L")
        print("PLANTED_TRACK %d foot=%.4f,%.4f,%.4f low_z=%.4f tied=%d "
              "spread=%.3f travel=%.4f toe=%.4f,%.4f,%.4f dir=%.5f,%.5f,%.5f "
              "rot=%.5f" %
              (frame, foot.x * 1000, foot.y * 1000, foot.z * 1000,
               low * 1000, tied, spread * 1000, travel,
               toe.x * 1000, toe.y * 1000, toe.z * 1000,
               direction[0], direction[1], direction[2], rot))

    zs = [row[1].z * 1000 for row in rows]
    xs = [row[1].x * 1000 for row in rows]
    ys = [row[1].y * 1000 for row in rows]
    lows = [row[2] * 1000 for row in rows]
    print("PLANTED_SUM ankle_z_span=%.4f ankle_xy_span=%.4f sole_low_z_span=%.4f "
          "tracked_travel_max=%.4f tied=%s"
          % (max(zs) - min(zs),
             max(max(xs) - min(xs), max(ys) - min(ys)),
             max(lows) - min(lows),
             max(row[5] for row in rows),
             sorted({row[3] for row in rows})))


main()
