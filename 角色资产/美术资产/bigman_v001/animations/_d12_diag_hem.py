import os, sys
import bpy
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anim_lib as A
arm, meshes = A.open_animation_project()
for name in ("Jacket_Hem", "Jacket_Hem_Line", "Suit_Torso", "Jacket_Vent"):
    o = bpy.data.objects.get(name)
    if o is None:
        print("MISSING", name); continue
    mods = [(m.name, m.type, getattr(m, "object", None).name if getattr(m, "object", None) else None) for m in o.modifiers]
    groups = [g.name for g in o.vertex_groups]
    print("%-18s parent=%-14s parent_type=%-8s mods=%s" % (name, o.parent.name if o.parent else "-", o.parent_type, mods))
    print("   groups(%d)=%s" % (len(groups), groups[:8]))
    if o.type == "MESH" and o.data.vertices:
        v = o.data.vertices[0]
        print("   v0 groups=", [(o.vertex_groups[g.group].name, round(g.weight, 3)) for g in v.groups])
        nz = sum(1 for vv in o.data.vertices if len(vv.groups) > 0)
        print("   verts=%d  with_groups=%d" % (len(o.data.vertices), nz))
