import bpy, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A
arm, meshes = A.open_animation_project()
A.setup_scene()
out = {}
for side in ("L", "R"):
    for nm in A.FOOT_MESHES[side]:
        obj = bpy.data.objects.get(nm)
        if obj is None:
            continue
        vg = {g.index: g.name for g in obj.vertex_groups}
        agg = {}
        mods = [(m.type, getattr(m, "object", None).name if getattr(m, "object", None) else None)
                for m in obj.modifiers]
        for v in obj.data.vertices:
            for g in v.groups:
                nmg = vg.get(g.group)
                if nmg is None:
                    continue
                agg[nmg] = max(agg.get(nmg, 0.0), g.weight)
        out[nm] = {
            "parent": obj.parent.name if obj.parent else None,
            "parent_type": obj.parent_type,
            "parent_bone": obj.parent_bone,
            "modifiers": mods,
            "weights": {k: round(v, 4) for k, v in sorted(agg.items(), key=lambda kv: -kv[1])},
        }
print("D08_SKIN " + json.dumps(out, ensure_ascii=False))
