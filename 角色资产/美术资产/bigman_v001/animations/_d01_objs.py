import bpy, sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A
arm, meshes = A.open_animation_project()
A.setup_scene()
import anim_idle_01 as I1
src = bpy.data.actions[I1.NAME]
if arm.animation_data is None:
    arm.animation_data_create()
arm.animation_data.action = src
A._bind_slot(arm, src)
A.reset_pose(arm)
bpy.context.scene.frame_set(0)
bpy.context.view_layer.update()
names = sorted(o.name for o in bpy.data.objects if o.type == "MESH")
print("MESH_NAMES " + json.dumps(names, ensure_ascii=False))
for b in ("pelvis","chest","neck","head","hand.L","hand.R","upperarm.L","upperarm.R","forearm.L","forearm.R"):
    h = A.bone_world(arm, b, "head"); t = A.bone_world(arm, b, "tail")
    print("BONE %-12s head=%s tail=%s" % (b, [round(v*1000,1) for v in h], [round(v*1000,1) for v in t]))
# head mesh-ish: report per-object world bbox z range for objects near head height
deps = bpy.context.evaluated_depsgraph_get()
info=[]
for obj in bpy.data.objects:
    if obj.type != "MESH": continue
    ev = obj.evaluated_get(deps); me = ev.to_mesh(); mw = ev.matrix_world
    zs=[(mw @ v.co).z for v in me.vertices]
    xs=[(mw @ v.co).x for v in me.vertices]
    ys=[(mw @ v.co).y for v in me.vertices]
    info.append([obj.name, round(min(xs)*1000,1), round(max(xs)*1000,1), round(min(ys)*1000,1), round(max(ys)*1000,1), round(min(zs)*1000,1), round(max(zs)*1000,1)])
    ev.to_mesh_clear()
print("OBJ_BBOX " + json.dumps(info, ensure_ascii=False))
print("D01_OBJS_DONE")
