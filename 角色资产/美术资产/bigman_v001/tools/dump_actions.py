# -*- coding: utf-8 -*-
"""从 bigman_anim_v001.blend 里导出全部 Action 的权威元数据。

用法:
    blender --background <blend> --factory-startup --python dump_actions.py -- <out.json>

输出内容:
  - scene fps / frame range
  - armature: 骨骼数量、骨骼名、父子层级
  - actions: 每个 Action 的 frame_range / 手动区间 / 自定义属性(anim_id/loop/antic_frame/...)
"""
import bpy
import json
import sys
import os


def _prop_value(v):
    """把 Blender 自定义属性值转成可 JSON 序列化的形态。"""
    if isinstance(v, (bool, int, float, str)):
        return v
    try:
        return [float(x) for x in v]
    except Exception:
        pass
    try:
        return [str(x) for x in v]
    except Exception:
        pass
    return str(v)


def main():
    argv = sys.argv
    out_path = None
    if "--" in argv:
        rest = argv[argv.index("--") + 1:]
        if rest:
            out_path = rest[0]

    scene = bpy.context.scene
    result = {
        "blend": bpy.data.filepath,
        "fps": scene.render.fps / scene.render.fps_base if scene.render.fps_base else scene.render.fps,
        "scene_frame_range": [scene.frame_start, scene.frame_end],
        "armatures": [],
        "actions": {},
    }

    for arm_obj in [o for o in bpy.data.objects if o.type == "ARMATURE"]:
        bones = []
        for b in arm_obj.data.bones:
            bones.append({
                "name": b.name,
                "parent": b.parent.name if b.parent else None,
                "head": [round(v, 6) for v in b.head_local],
                "tail": [round(v, 6) for v in b.tail_local],
                "length": round(b.length, 6),
            })
        result["armatures"].append({
            "object": arm_obj.name,
            "data": arm_obj.data.name,
            "bone_count": len(arm_obj.data.bones),
            "bones": bones,
            "mesh_children": [c.name for c in arm_obj.children if c.type == "MESH"],
        })

    for act in bpy.data.actions:
        rec = {
            "name": act.name,
            "frame_range": [round(v, 4) for v in act.frame_range],
            "fcurves": len(act.fcurves),
            "use_frame_range": bool(getattr(act, "use_frame_range", False)),
            "use_cyclic": bool(getattr(act, "use_cyclic", False)),
            "prop_keys": sorted([k for k in act.keys() if k != "_RNA_UI"]),
            "props": {},
        }
        if rec["use_frame_range"]:
            rec["manual_range"] = [act.frame_start, act.frame_end]
        for k in act.keys():
            if k == "_RNA_UI":
                continue
            rec["props"][k] = _prop_value(act[k])
        result["actions"][act.name] = rec

    text = json.dumps(result, ensure_ascii=False, indent=1)
    if out_path:
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(text)
        print("WROTE %s (%d bytes)" % (out_path, len(text.encode("utf-8"))))
    else:
        print("===JSON_START===")
        print(text)
        print("===JSON_END===")

    print("ACTIONS_TOTAL %d" % len(bpy.data.actions))
    print("ARMATURES_TOTAL %d" % len(result["armatures"]))
    for a in result["armatures"]:
        print("ARMATURE %s bones=%d meshes=%d" % (a["object"], a["bone_count"], len(a["mesh_children"])))


main()
