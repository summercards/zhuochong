"""_e03_handaxis —— 量手骨的本体轴语义（只读）。

目标：把「手摆成指节朝胸面」这件事从「试 twist 角度」升级为「直接用胸面法线
张成骨基」——后者确定、连续、且不需要扫参数。前提是先知道 `hand.L/R` 的
**rest 基**里哪根轴指向掌心 / 指节 / 拇指侧。

做法：对 rest 姿态（T-pose 定稿）打印
    · `hand.L/R` 的 rest 世界 3×3（三列 = 骨骼局部 x/y/z 在世界里的朝向）
    · 掌 / 指 / 拇指 三簇网格顶点的世界重心 ⟹ 得到
        ① 拇指方向 = thumb_centroid − palm_centroid
        ② 指节外法线 = (palm_centroid − torso_centroid) 的横向分量近似
    再把这两个方向**投影到骨基**上，读出它们各自落在哪根轴上。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python _e03_handaxis.py
"""

import json
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A          # noqa: E402
import anim_rage as R         # noqa: E402

SIDES = ("L", "R")


def centroid(points):
    return sum(points, Vector((0.0, 0.0, 0.0))) / float(max(1, len(points)))


def cluster(side, kind):
    deps = bpy.context.evaluated_depsgraph_get()
    out = []
    for obj in bpy.data.objects:
        if obj.type != "MESH" or not obj.name.endswith("_" + side):
            continue
        if not any(obj.name.startswith(p) for p in R.HAND_PREFIX):
            continue
        is_thumb = obj.name.startswith("Thumb_")
        is_palm = obj.name.startswith("Hand_Palm_")
        if kind == "thumb" and not is_thumb:
            continue
        if kind == "palm" and not is_palm:
            continue
        if kind == "fingers" and (is_thumb or is_palm):
            continue
        ev = obj.evaluated_get(deps)
        me = ev.to_mesh()
        mw = ev.matrix_world
        out += [mw @ v.co for v in me.vertices]
        ev.to_mesh_clear()
    return out


def main():
    arm, _meshes = R.boot()
    A.reset_pose(arm)
    bpy.context.view_layer.update()
    report = {}
    torso_c = centroid([p for s in ("L",) for p in cluster(s, "palm")])
    for side in SIDES:
        pb = arm.pose.bones["hand." + side]
        basis = pb.matrix.to_3x3()
        cols = {
            "local_x": (basis @ Vector((1.0, 0.0, 0.0))).normalized(),
            "local_y": (basis @ Vector((0.0, 1.0, 0.0))).normalized(),
            "local_z": (basis @ Vector((0.0, 0.0, 1.0))).normalized(),
        }
        palm = centroid(cluster(side, "palm"))
        thumb = centroid(cluster(side, "thumb"))
        fingers = centroid(cluster(side, "fingers"))
        thumb_dir = (thumb - palm).normalized()
        knuckle_dir = (palm - fingers).normalized()
        report[side] = {
            "basis": {k: [round(v, 4) for v in val] for k, val in cols.items()},
            "thumb_dir": [round(v, 4) for v in thumb_dir],
            "knuckle_dir": [round(v, 4) for v in knuckle_dir],
            "thumb_proj": {k: round(thumb_dir.dot(val), 3)
                           for k, val in cols.items()},
            "knuckle_proj": {k: round(knuckle_dir.dot(val), 3)
                             for k, val in cols.items()},
            "palm_centroid_mm": [round(v * 1000.0, 1) for v in palm],
            "hand_tail_mm": [round(v * 1000.0, 1)
                             for v in Vector(A.bone_world(arm, "hand." + side,
                                                          "tail"))],
            "hand_head_mm": [round(v * 1000.0, 1)
                             for v in Vector(A.bone_world(arm, "hand." + side,
                                                          "head"))],
        }
    del torso_c
    print("E03_HANDAXIS " + json.dumps(report, ensure_ascii=False))
    print("E03_HANDAXIS_DONE")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("E03_HANDAXIS_FAILURE " + traceback.format_exc())
