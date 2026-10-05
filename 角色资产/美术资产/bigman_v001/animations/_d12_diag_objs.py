import os, sys
import bpy
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anim_lib as A
arm, meshes = A.open_animation_project()
print("OBJ_COUNT", len(bpy.data.objects))
for o in sorted(bpy.data.objects, key=lambda x: x.name):
    zs = []
    try:
        for c in o.bound_box:
            zs.append((o.matrix_world @ __import__("mathutils").Vector(c)).z)
    except Exception:
        pass
    print("  %-28s type=%-9s parent=%-14s z=[%s]" % (
        o.name, o.type,
        (o.parent.name if o.parent else "-"),
        ("%.3f..%.3f" % (min(zs), max(zs))) if zs else "-"))
print("MESHES", [m.name if hasattr(m, "name") else str(m) for m in (meshes or [])])
