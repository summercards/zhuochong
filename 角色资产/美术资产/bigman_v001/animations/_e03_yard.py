"""_e03_yard —— 给「体内/穿透判定」定案：**哪个口径是权威**。

起因：`_e03_valid.py` 在 `f=60` 上三个口径打架 ——
    单方向射线奇偶 = 22 个顶点在体内
    13 方向多数表决 = 0
    正面射线遮挡   = 0
若 `Suit_Torso` 是**闭合流形**（水密），三条必然一致 ⟹ 不一致就说明**网格有开孔**，
射线会从孔里漏出去（穿过次数变偶）⟹ **单方向奇偶会假阳性**。
本脚本做两件决定性测量：
  ① **流形检查**：数 `Suit_Torso` 的边界边（只属于 1 个面的边）与非流形边。
     有边界边 = 有开孔 = 奇偶法在孔附近不可靠。
  ② **一致性扫描**：对每个顶点跑 13 个方向，统计「票数分布」。真·内部的顶点
     应当 **13/13 一致为内**；受开孔影响的顶点票数会散在中间。
     票数分布本身就是「这个尺子有多可信」的定量证据。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python _e03_yard.py
"""

import json
import math
import os
import sys
from collections import Counter

import bpy
import bmesh
import mathutils.bvhtree as bvhtree
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A          # noqa: E402
import anim_rage as R         # noqa: E402

SIDES = ("L", "R")
DIRS = []
for _j in range(13):
    _a = 2.0 * math.pi * _j / 13.0
    _z = 1.0 - 2.0 * (_j + 0.5) / 13.0
    _r = math.sqrt(max(0.0, 1.0 - _z * _z))
    DIRS.append(Vector((math.cos(_a) * _r, math.sin(_a) * _r, _z)).normalized())


def manifold_report():
    deps = bpy.context.evaluated_depsgraph_get()
    ev = R.TORSO.evaluated_get(deps)
    me = ev.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(me)
    boundary = sum(1 for e in bm.edges if len(e.link_faces) == 1)
    nonmani = sum(1 for e in bm.edges if len(e.link_faces) > 2)
    loose = sum(1 for e in bm.edges if len(e.link_faces) == 0)
    stats = {"verts": len(bm.verts), "edges": len(bm.edges),
             "faces": len(bm.faces), "boundary_edges": boundary,
             "nonmanifold_edges": nonmani, "loose_edges": loose,
             "watertight": boundary == 0 and nonmani == 0}
    bm.free()
    ev.to_mesh_clear()
    return stats


def votes_for(tree, point):
    origin = Vector(point)
    votes = 0
    for d in DIRS:
        o = origin.copy()
        hits = 0
        for _ in range(64):
            loc, _n, index, distance = tree.ray_cast(o, d)
            if loc is None or index is None:
                break
            hits += 1
            o = loc + d * max(1e-7, distance * 1e-6 + 1e-7)
        if hits % 2 == 1:
            votes += 1
    return votes


def parity(tree, point, direction):
    o = Vector(point)
    d = Vector(direction).normalized()
    hits = 0
    for _ in range(64):
        loc, _n, index, distance = tree.ray_cast(o, d)
        if loc is None or index is None:
            break
        hits += 1
        o = loc + d * max(1e-7, distance * 1e-6 + 1e-7)
    return hits % 2 == 1


def main():
    arm, _meshes = R.boot()
    if arm.animation_data:
        arm.animation_data.action = None

    print("E03_YARD_MANIFOLD " + json.dumps(manifold_report()))

    deps = bpy.context.evaluated_depsgraph_get()
    tree = bvhtree.BVHTree.FromObject(R.TORSO, deps)
    single_dir = Vector((0.3178, 0.7512, 0.5773)).normalized()

    R.HAND_AXIS_MODE = "thumb_dn"
    R.LAST_ELBOW.clear()
    poses = [(f, R.rage_pose(arm, f)) for f in range(0, R.TOTAL + 1)]
    for frame in (0, 26, 28, 44, 52, 57, 60, 66, 96):
        A.apply_pose(arm, dict(poses[frame][1]))
        bpy.context.view_layer.update()
        deps = bpy.context.evaluated_depsgraph_get()
        tree = bvhtree.BVHTree.FromObject(R.TORSO, deps)
        out = {}
        for side in SIDES:
            pts = R.hand_mesh_points(side, step=2)
            hist = Counter()
            single = 0
            for p, _name in pts:
                v = votes_for(tree, p)
                hist[v] += 1
                if parity(tree, p, single_dir):
                    single += 1
            out[side] = {"n": len(pts), "single_dir": single,
                         "votes>6": sum(c for v, c in hist.items() if v > 6),
                         "votes==13": hist.get(13, 0),
                         "votes_hist": {str(k): hist[k]
                                        for k in sorted(hist) if k}, }
        print("E03_YARD " + json.dumps({"f": frame, "sides": out},
                                       ensure_ascii=False))
    print("E03_YARD_DONE")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("E03_YARD_FAILURE " + traceback.format_exc())
