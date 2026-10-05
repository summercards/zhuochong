"""probe_up07_sole —— B07 专用：量**支撑脚鞋底**的几何（选滚动支点用）。

问：`foot_pivot_vertex(z_band=6mm)` 挑到的那个点 z = 6.9 mm，
    而 `JS.sole_series` 实测 f0 鞋底最低 = 1.06 mm —— 差 5.8 mm。
    绕一个悬空 6 mm 的点滚动 ⟹ 整个鞋底被抬到 5~7.6 mm（`support_sole_max` 7.61）。
所以本探针要回答：
  ① 鞋底最低平面到底在 z 多少（**真值**）；
  ② 最低层里最靠前的顶点在哪、z 多少（当前模型选的点）；
  ③ 若把 band 收到 0.5 / 1 / 2 mm，选出来的点分别在哪、z 多少；
  ④ 鞋底**最靠前**的顶点（含上翘鞋头）在哪 —— 绕它会戳穿吗。
"""

import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A          # noqa: E402
import anim_idle_01 as I1     # noqa: E402


def sole_rows(side):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    rows = []
    for name in A.FOOT_MESHES[side]:
        obj = bpy.data.objects.get(name)
        if obj is None:
            continue
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        matrix = evaluated.matrix_world
        for index, vertex in enumerate(mesh.vertices):
            rows.append((name, index, matrix @ vertex.co))
        evaluated.to_mesh_clear()
    return rows


def main():
    arm, meshes = A.open_animation_project()
    A.setup_scene()
    pose = I1.idle_pose(arm, 0.0)
    A.apply_pose(arm, pose)
    bpy.context.view_layer.update()

    out = {}
    for side in ("L", "R"):
        rows = sole_rows(side)
        zmin = min(r[2].z for r in rows)
        front_all = min(rows, key=lambda r: r[2].y)
        picked = {}
        for band in (0.0005, 0.001, 0.002, 0.003, 0.006, 0.030):
            cand = [r for r in rows if r[2].z <= zmin + band]
            name, index, point = min(cand, key=lambda r: r[2].y)
            picked["%.1fmm" % (band * 1000.0)] = {
                "obj": name, "idx": index,
                "y_mm": round(point.y * 1000.0, 2),
                "z_mm": round(point.z * 1000.0, 3),
                "dz_above_min_mm": round((point.z - zmin) * 1000.0, 3),
            }
        out[side] = {
            "zmin_mm": round(zmin * 1000.0, 3),
            "n_vertices": len(rows),
            "front_all": {"obj": front_all[0], "idx": front_all[1],
                          "y_mm": round(front_all[2].y * 1000.0, 2),
                          "z_mm": round(front_all[2].z * 1000.0, 3)},
            "picked_by_band": picked,
            # 最低层（0.5mm）里最前 / 最后，看平面有多长
            "low_plane_y_span_mm": [
                round(min(r[2].y for r in rows if r[2].z <= zmin + 0.0005) * 1000.0, 2),
                round(max(r[2].y for r in rows if r[2].z <= zmin + 0.0005) * 1000.0, 2)],
        }
    A.report("UP07_SOLE_GEOM", out)


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("UP07_SOLE_FAILURE " + traceback.format_exc())
