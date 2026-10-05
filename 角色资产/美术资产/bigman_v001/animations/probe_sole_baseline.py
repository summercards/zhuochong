"""鞋底漂移基线（只读）：同一把尺子量各动作的"支撑脚"。

要回答的问题：`planted_feet_frozen_ok` 里那条 **按网格顶点** 量的
`sole_low`，到底测的是"脚在滑"还是"蒙皮变形"？

判据：鞋顶点是**蒙皮**的（`foot.L` 与 `shin.L` 混权），
      而 `foot.L` 骨本身是刚体。所以同时量三样：
        1) 脚骨世界行程（`foot.<side>` head）—— 动画的输出；
        2) 同上脚尖（`toe.<side>` head）；
        3) 最低鞋顶点世界行程 —— 动画 + 蒙皮；
        4) 最低鞋顶点在**脚骨局部系**里的行程 —— 纯蒙皮残差
           （若刚性绑到脚骨则恒为 0）。
若 A01 `Idle_01`（门禁全绿）的 (3) 也是毫米级、而 (1) 是微米级，
则说明 (3) 是这套骨架的固有属性，不该当"脚滑"判据。
"""
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import anim_lib as A

CASES = [
    ("Idle_01", 0, 180),
    ("Run", 0, 48),
    ("Run_Stop", 0, 54),
]
NAMES = ("Shoe_Heel_%s", "Shoe_Sole_%s", "Shoe_Toe_Cap_%s", "Shoe_Upper_%s")


def side_vertices(side):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    out = []
    for pattern in NAMES:
        obj = bpy.data.objects.get(pattern % side)
        if obj is None:
            continue
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        matrix = evaluated.matrix_world
        for index, vertex in enumerate(mesh.vertices):
            out.append((pattern % side, index, matrix @ vertex.co))
        evaluated.to_mesh_clear()
    return out


def probe(action_name, start, end):
    arm, meshes = A.open_animation_project()
    action = bpy.data.actions[action_name]
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    scene = bpy.context.scene

    trackers = {}
    origin = {}
    bone_points = {"L": [], "R": []}
    toe_points = {"L": [], "R": []}
    low_points = {"L": [], "R": []}
    local_res = {"L": [], "R": []}

    for frame in range(start, end + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        for side in ("L", "R"):
            bone_points[side].append(Vector(A.bone_world(arm, "foot." + side,
                                                         "head")))
            toe_points[side].append(Vector(A.bone_world(arm, "toe." + side,
                                                        "head")))
            verts = side_vertices(side)
            low = min(v[2].z for v in verts)
            lows = [v for v in verts if v[2].z <= low + 1e-7]
            if side not in trackers:
                trackers[side] = [(v[0], v[1]) for v in lows]
                origin[side] = {(v[0], v[1]): v[2] for v in lows}
            low_points[side].append(min(v[2].z for v in verts))

            # 脚骨局部系：把同一批顶点变换到 foot 骨的世界基里
            basis = arm.pose.bones["foot." + side].matrix.copy()
            inverse = basis.inverted()
            current = {(v[0], v[1]): v[2] for v in verts}
            if side not in local_res:
                local_res[side] = {}
            residual = max((inverse @ current[key]
                            - inverse @ origin[side][key]).length
                           for key in trackers[side]) * 1000.0
            local_res[side].append(residual)

    for side in ("L", "R"):
        travel_bone = max((p - bone_points[side][0]).length
                          for p in bone_points[side]) * 1000.0
        travel_toe = max((p - toe_points[side][0]).length
                         for p in toe_points[side]) * 1000.0
        basis = arm.pose.bones["foot." + side].matrix.copy()
        print("SOLE_BASE %s %s bone=%.4f toe=%.4f local_res_max=%.4f "
              "sole_z_span=%.4f"
              % (action_name, side, travel_bone, travel_toe,
                 max(local_res[side]),
                 (max(low_points[side]) - min(low_points[side])) * 1000.0))


def main():
    for action_name, start, end in CASES:
        probe(action_name, start, end)


main()
