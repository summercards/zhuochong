# -*- coding: utf-8 -*-
"""实测角色在**指定姿态**下的真实体型包围盒（受击盒尺寸的来源）。

为什么需要这个：
    GLB 的整体 AABB（±0.866 × 1.803 × 0.354）是 **T-pose** 的测量结果 ——
    横向 1.732 m 全是两条伸平的手臂。受击盒按这个做会变成"隔着一米也能打到"。
    所以这里把骨架摆到实际待机 / 下蹲 / 防御姿态，取**变形后网格顶点**的包围盒。

输出（Blender 世界坐标，与人形属性一致）：
    x = 角色左手侧, y = 角色背后（**前向 = -y**）, z = 上

用法:
    blender --background --factory-startup <anim.blend> --python measure_body_box.py -- <out.json>
"""
import bpy
import json
import os
import sys
from mathutils import Vector

# 要测的姿态：clip 名 -> 采样帧
POSES = {
    "Idle_01": 0,
    "Crouch_Idle": 0,
    "Guard_Loop": 0,
    "Walk_F": 0,
    "Run": 0,
}


def main():
    argv = sys.argv
    out_path = argv[argv.index("--") + 1] if "--" in argv else None

    arm = None
    for o in bpy.data.objects:
        if o.type == "ARMATURE":
            arm = o
            break
    if arm is None:
        print("BODYBOX_FAIL 场景里没有骨架")
        return

    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    scene = bpy.context.scene
    if arm.animation_data is None:
        arm.animation_data_create()

    report = {
        "armature": arm.name,
        "mesh_objects": len(meshes),
        "fps": scene.render.fps / (scene.render.fps_base or 1.0),
        "note": "Blender 世界坐标: +x=左手侧, +y=背后(前向=-y), +z=上; "
                "half_width_x = 躯干左半宽, half_depth_y = 躯干后半深",
        "poses": {},
    }

    for clip, frame in POSES.items():
        act = bpy.data.actions.get(clip)
        if act is None:
            print("BODYBOX_SKIP 没有 Action: %s" % clip)
            continue
        arm.animation_data.action = act
        scene.frame_set(frame)
        bpy.context.view_layer.update()

        depsgraph = bpy.context.evaluated_depsgraph_get()
        pts = []
        for o in meshes:
            ev = o.evaluated_get(depsgraph)
            try:
                me = ev.to_mesh()
            except Exception:
                continue
            if me is None:
                continue
            mw = o.matrix_world
            for v in me.vertices:
                pts.append(mw @ v.co)
            ev.to_mesh_clear()

        def box(sel, tag):
            if not sel:
                return None
            a = Vector((min(p.x for p in sel), min(p.y for p in sel), min(p.z for p in sel)))
            b = Vector((max(p.x for p in sel), max(p.y for p in sel), max(p.z for p in sel)))
            return {
                "scope": tag,
                "vertices": len(sel),
                "min": [round(v, 4) for v in a],
                "max": [round(v, 4) for v in b],
                "size": [round(v, 4) for v in (b - a)],
                "half_width_x": round(max(abs(a.x), abs(b.x)), 4),
                "half_depth_y": round(max(abs(a.y), abs(b.y)), 4),
                "height_z": round((b - a).z, 4),
            }

        full = box(pts, "全网格")
        if full is None:
            continue
        # 躯干带：取全高 55%~95% 的高度区间（胸→头），排除脚/腿/下垂的手
        h0 = full["min"][2]
        h1 = full["max"][2]
        lo = h0 + (h1 - h0) * 0.55
        hi = h0 + (h1 - h0) * 0.95
        torso = box([p for p in pts if lo <= p.z <= hi], "躯干带(55%~95%高)")

        report["poses"][clip] = {
            "frame": frame,
            "full": full,
            "torso": torso,
            "half_width_x": full["half_width_x"],
            "half_depth_y": full["half_depth_y"],
            "height_z": full["height_z"],
        }

    text = json.dumps(report, ensure_ascii=False, indent=1)
    if out_path:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(text)
        print("WROTE %s (%d bytes)" % (out_path, len(text.encode("utf-8"))))

    for clip, r in report["poses"].items():
        f = r["full"]
        t = r["torso"]
        print("POSE %-14s 全网格 顶点%-7d 尺寸 x=%.3f y=%.3f z=%.3f" % (
            clip, f["vertices"], f["size"][0], f["size"][1], f["size"][2]))
        if t:
            print("     躯干带 顶点%-7d 半宽X=%.3f 半深Y=%.3f  (y %.3f..%.3f)" % (
                t["vertices"], t["half_width_x"], t["half_depth_y"], t["min"][1], t["max"][1]))


main()
