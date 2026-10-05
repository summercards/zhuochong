# -*- coding: utf-8 -*-
"""C02 `Launcher` 支点漂移探针 —— 只读已存盘的 `Launcher` Action。

盯死**标定出的那颗鞋底前缘顶点**（`C02_CALIBRATION.pivot_vertex`），逐帧报：
  - 它的世界 (x, y, z)
  - 相对首帧的 x/y 偏移
  - 脚骨世界 3×3 与 "Rx(θ)·首帧 3×3" 的夹角（踮脚是否真在绕世界 X 转）
  - 踝世界坐标 / 足尖角 / 骨盆

跑法：在 `animations` 目录下
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
        --background --factory-startup --python probe_c02_pivot.py
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import anim_lib as A  # noqa: E402
import anim_launcher02 as L2  # noqa: E402

# 来自 C02_CALIBRATION 报告（`pivot_vertex`）
TRACK = {"L": ("Shoe_Sole_L", 141), "R": ("Shoe_Sole_R", 141)}


def main():
    arm, meshes = A.open_animation_project()
    action = bpy.data.actions.get(L2.NAME)
    if action is None:
        print("C02PIVOT_NO_ACTION")
        return

    scene = bpy.context.scene
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    deps = bpy.context.evaluated_depsgraph_get()

    def sample(frame):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        row = {"f": frame}
        for side in L2.SIDES:
            name, index = TRACK[side]
            obj = bpy.data.objects[name].evaluated_get(deps)
            mesh = obj.to_mesh()
            matrix = obj.matrix_world
            point = matrix @ mesh.vertices[index].co
            obj.to_mesh_clear()
            bone = arm.pose.bones["foot." + side]
            row[side] = {
                "p": [round(point.x * 1000.0, 4), round(point.y * 1000.0, 4),
                      round(point.z * 1000.0, 4)],
                "basis": [[round(v, 6) for v in r] for r in bone.matrix.to_3x3()],
                "ank": [round(v * 1000.0, 3)
                        for v in A.bone_world(arm, "foot." + side, "head")],
                "tip": round(L2.tip_of(side, frame), 3),
                "w": L2.window_of(side, frame),
            }
        row["pel"] = [round(v * 1000.0, 3) for v in
                      A.bone_world(arm, "pelvis", "head")]
        return row

    rows = [sample(f) for f in range(0, L2.TOTAL + 1)]
    base = rows[0]
    for row in rows:
        out = {"f": row["f"], "pel_z": row["pel"][2]}
        for side in L2.SIDES:
            cur, ref = row[side], base[side]
            dx = cur["p"][0] - ref["p"][0]
            dy = cur["p"][1] - ref["p"][1]
            tip = cur["tip"]
            b_ref = Matrix([ref["basis"][i] for i in range(3)])
            b_cur = Matrix([cur["basis"][i] for i in range(3)])
            want = Matrix.Rotation(math.radians(tip), 3, "X") @ b_ref
            dev = math.degrees((want.transposed() @ b_cur).to_quaternion().angle)
            out[side] = {
                "p": [round(cur["p"][0], 3), round(cur["p"][1], 3)],
                "d": [round(dx, 4), round(dy, 4)],
                "tip": tip, "w": cur["w"],
                "basis_dev_deg": round(dev, 4),
            }
        print("C02PIVOT " + json.dumps(out))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("C02PIVOT_FAILURE " + traceback.format_exc())
