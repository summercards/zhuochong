"""_d11_owner_probe —— 逐对象藏起来，找出侧视腰部那根"横板"的归属。"""
import os, sys, json
import bpy, numpy as np
from mathutils import Vector
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
import anim_lib as A
FRAME=int(os.environ.get("OWNER_FRAME","3"))
VIEW=A.VIEW_SIDE

def mask_count(p):
    im=bpy.data.images.load(p,check_existing=False); w,h=im.size
    px=np.array(im.pixels[:],dtype=np.float32).reshape(h,w,4); bpy.data.images.remove(im)
    a=px[:,:,3]
    m=a>0.5 if float(a.min())<0.5 else px[:,:,:3].min(axis=2)<0.92
    return int(m.sum())

def bb(obj):
    pts=[obj.matrix_world@Vector(c) for c in obj.bound_box]
    return ([min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)])

arm,_=A.open_animation_project(); A.setup_scene()
sc=bpy.context.scene; cam=bpy.data.objects.get("Presentation_Camera")
act=bpy.data.actions.get(os.environ.get("OWNER_ACTION","Hit_Leg"))
if arm.animation_data is None: arm.animation_data_create()
arm.animation_data.action=act; A._bind_slot(arm,act)
sc.frame_set(FRAME); bpy.context.view_layer.update()
name,loc,tgt,scale,res=VIEW
base=os.path.join(A.PREVIEW_DIR,"_owner_base_f%04d.png"%FRAME)
A.render_still(cam,base,loc,tgt,scale,res); n0=mask_count(base)
cands=[]
for o in bpy.data.objects:
    if o.type!="MESH" or o.hide_render: continue
    lo,hi=bb(o)
    if hi[2]*1000.0<820 or lo[2]*1000.0>1060: continue
    cands.append(o)
rows=[]
for o in cands:
    o.hide_render=True
    p=os.path.join(A.PREVIEW_DIR,"_owner_%s_f%04d.png"%(o.name.replace(" ","_"),FRAME))
    A.render_still(cam,p,loc,tgt,scale,res)
    d=n0-mask_count(p); o.hide_render=False
    lo,hi=bb(o)
    rows.append({"name":o.name,"px_removed":d,"vgroups":len(o.vertex_groups),
                 "z_mm":[round(lo[2]*1000),round(hi[2]*1000)],
                 "y_mm":[round(lo[1]*1000),round(hi[1]*1000)]})
rows.sort(key=lambda r:-r["px_removed"])
print("OWNER_BASE_PX %d"%n0)
print("OWNER "+json.dumps(rows,ensure_ascii=False,indent=1))
print("OWNER_DONE")
