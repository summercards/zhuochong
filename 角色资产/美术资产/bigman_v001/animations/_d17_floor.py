import os, sys, json
import bpy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A
arm, meshes = A.open_animation_project()
rows = []
for obj in bpy.data.objects:
    if obj.type != "MESH":
        continue
    bb = [obj.matrix_world @ __import__("mathutils").Vector(c) for c in obj.bound_box]
    zs = [v.z for v in bb]; xs=[v.x for v in bb]; ys=[v.y for v in bb]
    rows.append({"obj": obj.name, "z_min_mm": round(min(zs)*1000,1), "z_max_mm": round(max(zs)*1000,1),
                 "sx_m": round(max(xs)-min(xs),2), "sy_m": round(max(ys)-min(ys),2)})
rows.sort(key=lambda r: (r["z_min_mm"]))
big = [r for r in rows if r["sx_m"] > 2.0 or r["sy_m"] > 2.0]
print("FLOOR_BIG " + json.dumps(big, ensure_ascii=False))
print("FLOOR_LOWEST " + json.dumps(rows[:12], ensure_ascii=False))
