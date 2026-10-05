"""probe_light01_endpoint —— 只读探针：找出 f0 与 f18 之间**到底有什么几何在动**。

起因：侧视图 `light01_side_f0000.png` 与 `light01_side_f0018.png` 有 351 个像素不同
（y=572..582 / x=357..439，RGBA ≈ (0,1,2,2) 即近乎全透明 —— 亚像素抗锯齿边缘），
而**前视图**同一对帧逐像素相同，骨骼世界矩阵差又是 0.0。

前视图沿 Y 投影 ⟹ 沿 Y 的差异在正视里看不见、侧视里看得见。
所以在这个小区域里有个物体沿 **Y** 动了亚像素量。骨骼排除了，只能是网格侧的东西：
物体级动画、形态键、或未被 `action_world_matrices` 覆盖的骨骼。

本探针逐物体求值（含所有修改器 + 形态键），比对 f0/f18 的**顶点世界坐标哈希**，
把"哪个物体、动多少、是否在动画里"一次问清楚。

只读：不写 .blend、不导 GLB、不建 Action。
"""

import hashlib
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A          # noqa: E402
import anim_crouch as CR      # noqa: E402

ACTION_NAME = os.environ.get("PROBE_ACTION", "Light_01")
F0, FN = 0, 18


def object_signature(depsgraph, obj):
    """物体在世界空间的求值几何指纹：顶点数 + 前 N 个顶点的坐标和 + 整包 sha1。"""
    evaluated = obj.evaluated_get(depsgraph)
    try:
        mesh = evaluated.to_mesh()
    except Exception:  # noqa: BLE001
        return None, None
    if mesh is None:
        return None, None
    matrix = evaluated.matrix_world
    coords = [matrix @ vertex.co for vertex in mesh.vertices]
    digest = hashlib.sha1()
    for co in coords:
        digest.update(("%.7f %.7f %.7f|" % (co.x, co.y, co.z)).encode("ascii"))
    signature = (len(coords), digest.hexdigest())
    evaluated.to_mesh_clear()
    return signature, coords


def main():
    arm, meshes = A.open_animation_project()
    A.setup_scene()
    action = bpy.data.actions.get(ACTION_NAME)
    if action is None:
        raise RuntimeError("找不到 Action %s" % ACTION_NAME)
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)

    scene = bpy.context.scene
    depsgraph = bpy.context.evaluated_depsgraph_get()

    # ---- 1) 场景里到底有哪些物体带自己的动画？
    animated_objects = []
    shapekey_objects = []
    for obj in bpy.data.objects:
        if obj.animation_data and obj.animation_data.action:
            animated_objects.append(
                (obj.name, obj.type, obj.animation_data.action.name))
        if obj.type == "MESH" and obj.data.shape_keys:
            tracks = []
            if obj.data.shape_keys.animation_data \
                    and obj.data.shape_keys.animation_data.action:
                tracks.append(obj.data.shape_keys.animation_data.action.name)
            for key in obj.data.shape_keys.key_blocks:
                if key.animation_data and key.animation_data.action:
                    tracks.append(key.name + ":" + key.animation_data.action.name)
            if tracks:
                shapekey_objects.append((obj.name, tracks))
    A.report("LIGHT01EP_ANIMATED_OBJECTS", {
        "object_level_actions": animated_objects,
        "shapekey_actions": shapekey_objects,
        "note": "非空即说明有骨骼以外的动画源盯着帧号",
    })

    # ---- 2) 逐物体求值几何，比对 f0 / f18
    scene.frame_set(F0)
    bpy.context.view_layer.update()
    first = {}
    for obj in bpy.data.objects:
        signature, _ = object_signature(depsgraph, obj)
        if signature is not None:
            first[obj.name] = signature

    scene.frame_set(FN)
    bpy.context.view_layer.update()
    moved = []
    for obj in bpy.data.objects:
        signature, _ = object_signature(depsgraph, obj)
        if signature is None or obj.name not in first:
            continue
        if signature != first[obj.name]:
            moved.append({
                "object": obj.name,
                "type": obj.type,
                "verts": signature[0],
                "parent": obj.parent.name if obj.parent else None,
                "parent_type": obj.parent_type if obj.parent else None,
                "has_armature_mod": any(
                    m.type == "ARMATURE" for m in obj.modifiers),
            })

    print("LIGHT01EP_MOVED_COUNT %d" % len(moved))
    A.report("LIGHT01EP_MOVED", {
        "count": len(moved),
        "objects": moved,
        "note": ("f%d 与 f%d 的求值几何不一致的物体。空 = 网格侧完全静止，"
                 "渲染像素差另有来源" % (F0, FN)),
    })

    # ---- 3) 骨骼侧复量：全部 pose bone 的世界矩阵（含未被 action_world_matrices 覆盖的）
    def all_bone_matrices(frame):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        return {pb.name: pb.matrix.copy() for pb in arm.pose.bones}

    m0 = all_bone_matrices(F0)
    mN = all_bone_matrices(FN)
    bone_delta = {}
    for name in m0:
        worst = max(abs(a - b) for row_a, row_b in zip(m0[name], mN[name])
                    for a, b in zip(row_a, row_b))
        if worst > 0.0:
            bone_delta[name] = worst
    A.report("LIGHT01EP_BONES", {
        "bone_count": len(m0),
        "differing_bones": {k: "%.3e" % v for k, v in
                            sorted(bone_delta.items(),
                                   key=lambda kv: -kv[1])[:10]},
        "max_delta": "%.3e" % (max(bone_delta.values()) if bone_delta else 0.0),
        "covered_by_gate": len(CR.action_world_matrices(arm, action, F0)),
    })


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("LIGHT01EP_FAILURE " + traceback.format_exc())
