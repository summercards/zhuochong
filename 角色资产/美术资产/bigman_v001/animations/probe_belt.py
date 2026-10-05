"""probe_belt —— 只读：查清 C01 预览里那根"不跟随骨架的蓝色细条"是什么。

对 f0 / f48 各列一次场景里所有 mesh 对象的世界包围盒，找出
**在 f0 贴着身体、在 f48 留在原处**的那些 —— 那些就是没被骨架带走的对象。
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402
import anim_lib as A  # noqa: E402


def world_bounds(obj):
    pts = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    lo = [min(p[i] for p in pts) for i in range(3)]
    hi = [max(p[i] for p in pts) for i in range(3)]
    return lo, hi


def main():
    arm, meshes = A.open_animation_project()
    A.setup_scene()
    scene = bpy.context.scene

    action = bpy.data.actions.get("Combo_Finish")
    if action is None:
        print("BELT_PROBE no Combo_Finish action")
        return
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)

    print("BELT_PROBE arm_children=%s" % [c.name for c in arm.children])

    snapshot = {}
    for frame in (0, 48):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        rows = {}
        for obj in bpy.data.objects:
            if obj.type != "MESH":
                continue
            lo, hi = world_bounds(obj)
            rows[obj.name] = {
                "y": [round(lo[1] * 1000.0, 1), round(hi[1] * 1000.0, 1)],
                "z": [round(lo[2] * 1000.0, 1), round(hi[2] * 1000.0, 1)],
                "parent": obj.parent.name if obj.parent else None,
                "mods": [m.type for m in obj.modifiers],
                "vgroups": len(obj.vertex_groups),
                "size_y_mm": round((hi[1] - lo[1]) * 1000.0, 1),
                "size_z_mm": round((hi[2] - lo[2]) * 1000.0, 1),
            }
        snapshot[frame] = rows

    moved = []
    still = []
    for name, r0 in snapshot[0].items():
        r1 = snapshot.get(48, {}).get(name)
        if r1 is None:
            continue
        dy = abs(r1["y"][0] - r0["y"][0])
        (moved if dy > 10.0 else still).append(
            (name, round(dy, 1), r0, r1))

    print("BELT_PROBE_MOVED " + json.dumps(
        [{"name": n, "dy_mm": d, "f0": a, "f48": b} for n, d, a, b in moved],
        ensure_ascii=False))
    print("BELT_PROBE_STILL " + json.dumps(
        [{"name": n, "dy_mm": d, "f0": a, "f48": b} for n, d, a, b in still],
        ensure_ascii=False))


if __name__ == "__main__":
    main()
