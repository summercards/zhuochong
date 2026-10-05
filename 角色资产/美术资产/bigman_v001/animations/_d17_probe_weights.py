"""D17 一次性探针：鞋网格到底绑在哪些骨上（决定 `sole_mm` 的口径边界）。"""
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import anim_lib as A  # noqa: E402

arm, meshes = A.open_animation_project()
for side, names in A.FOOT_MESHES.items():
    for name in names:
        obj = __import__("bpy").data.objects.get(name)
        if obj is None:
            print("MISSING", name)
            continue
        weights = {}
        for vg in obj.vertex_groups:
            weights[vg.name] = 0
        for v in obj.data.vertices:
            for g in v.groups:
                gname = obj.vertex_groups[g.group].name
                if g.weight > 1e-4:
                    weights[gname] = weights.get(gname, 0) + 1
        used = {k: v for k, v in weights.items() if v > 0}
        print("SHOE %-24s verts=%d groups=%s" % (name, len(obj.data.vertices),
                                                 used))
        # 逐骨权重和
        tot = {}
        for v in obj.data.vertices:
            for g in v.groups:
                gname = obj.vertex_groups[g.group].name
                tot[gname] = tot.get(gname, 0.0) + g.weight
        print("     mass=%s" % {k: round(v, 1) for k, v in sorted(tot.items())})
