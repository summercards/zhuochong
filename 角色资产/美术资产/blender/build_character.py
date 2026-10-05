import bpy, math, os
from mathutils import Vector
OUT=os.path.abspath('business_man_tpose.blend'); RENDER=os.path.abspath('business_man_tpose_preview.png')
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
def mat(n,c,metal=0,rough=.4):
 m=bpy.data.materials.new(n); m.diffuse_color=(*c,1); m.use_nodes=True; b=next(x for x in m.node_tree.nodes if x.type=='BSDF_PRINCIPLED'); b.inputs['Base Color'].default_value=(*c,1); b.inputs['Metallic'].default_value=metal; b.inputs['Roughness'].default_value=rough; return m
M={'blue':mat('Suit Royal Blue',(.02,.08,.34),.05,.3),'dark':mat('Suit Edge',(.008,.02,.1),.05,.35),'white':mat('Shirt White',(.8,.88,.98),0,.3),'skin':mat('Skin',(.52,.22,.12),0,.5),'skin2':mat('Skin Highlight',(.7,.34,.18),0,.5),'hair':mat('Hair',(.006,.008,.015),0,.25),'shoe':mat('Leather',(.005,.007,.01),.3,.16),'glass':mat('Frames',(.01,.008,.006),.7,.16),'lens':mat('Lens',(.08,.16,.24),.3,.08),'button':mat('Buttons',(.01,.015,.025),.7,.2),'ground':mat('Ground',(.03,.04,.06),0,.75)}
for n in ['Character','Clothing','Accessories','Rig','Presentation']: bpy.context.scene.collection.children.link(bpy.data.collections.new(n))
def mv(o,c):
 for x in list(o.users_collection): x.objects.unlink(o)
 bpy.data.collections[c].objects.link(o); return o
def sm(o):
 if o.type=='MESH':
  for p in o.data.polygons:p.use_smooth=True
 return o
def sph(n,l,s,ma):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=16,location=l); o=bpy.context.object; o.name=n; o.scale=s; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); o.data.materials.append(ma); return sm(o)
def cube(n,l,s,ma,bev=.08,rot=(0,0,0)):
 bpy.ops.mesh.primitive_cube_add(location=l,rotation=rot); o=bpy.context.object; o.name=n; o.scale=s; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); o.data.materials.append(ma)
 if bev: q=o.modifiers.new('Tailored bevel','BEVEL'); q.width=bev; q.segments=3
 return o
def cyl(n,a,b,r,ma):
 a,b=Vector(a),Vector(b); d=b-a; bpy.ops.mesh.primitive_cylinder_add(vertices=20,radius=r,depth=d.length,location=(a+b)/2); o=bpy.context.object; o.name=n; o.data.materials.append(ma); o.rotation_mode='QUATERNION'; o.rotation_quaternion=d.to_track_quat('Z','Y'); return sm(o)
def tor(n,l,maj,minr,ma):
 bpy.ops.mesh.primitive_torus_add(major_radius=maj,minor_radius=minr,major_segments=32,minor_segments=10,location=l,rotation=(math.pi/2,0,0)); o=bpy.context.object; o.name=n; o.data.materials.append(ma); return sm(o)
for side,x in [('L',-.48),('R',.48)]:
 cube('Shoe_'+side,(x,-.1,.22),(.42,.78,.2),M['shoe'],.14); cube('Sole_'+side,(x,-.1,.1),(.45,.82,.08),M['shoe'],.04)
 cube('LowerLeg_'+side,(x,0,1.4),(.3,.28,.8),M['blue'],.12); sph('Knee_'+side,(x,0,2.18),(.33,.31,.3),M['blue']); cube('UpperLeg_'+side,(x,0,2.72),(.36,.34,.62),M['blue'],.15)
 cube('Cuff_'+side,(x*5.3,0,4.78),(.16,.27,.2),M['white'],.04); sph('Hand_'+side,(x*5.65,0,4.78),(.34,.2,.25),M['skin2'])
cube('Trouser_Waist',(0,0,3.28),(.82,.4,.28),M['blue'],.12); cube('Jacket_Torso',(0,0,4.25),(.93,.43,.88),M['blue'],.18); cube('Jacket_Lower',(0,0,3.62),(.88,.42,.28),M['blue'],.1)
cube('Shirt_Front',(0,-.445,4.55),(.27,.045,.6),M['white'],.02); cube('Lapel_L',(-.37,-.49,4.65),(.11,.035,.53),M['dark'],.02,rot=(0,math.radians(-23),math.radians(-4))); cube('Lapel_R',(.37,-.49,4.65),(.11,.035,.53),M['dark'],.02,rot=(0,math.radians(23),math.radians(4)))
for x in (-.62,.62): cube('Pocket_Flap',(x,-.48,3.95),(.24,.035,.1),M['dark'],.02)
for z in (4.28,3.95): sph('Jacket_Button',(0,-.505,z),(.065,.04,.065),M['button'])
cyl('Neck',(0,0,5.05),(0,0,5.48),.28,M['skin']); sph('Head',(0,0,5.95),(.48,.4,.57),M['skin']); sph('Jaw',(0,-.02,5.65),(.39,.35,.28),M['skin']); sph('Nose',(0,-.39,5.95),(.08,.11,.12),M['skin2']); cube('Mouth',(0,-.385,5.73),(.12,.018,.018),M['dark'],.01)
sph('Hair_Cap',(0,.01,6.32),(.5,.42,.3),M['hair'])
for i,x in enumerate([-.38,-.25,-.12,0,.12,.25,.38]): sph('Hair_Tuft_'+str(i),(x,-.02,6.48),(.15,.18,.22),M['hair'])
for side,s in [('L',-1),('R',1)]:
 x1,x2,x3=.93*s,1.72*s,2.55*s; sph('Shoulder_'+side,(x1,0,4.82),(.3,.38,.34),M['blue']); cyl('UpperArm_'+side,(x1,0,4.78),(x2,0,4.78),.28,M['blue']); sph('Elbow_'+side,(x2,0,4.78),(.28,.29,.28),M['blue']); cyl('Forearm_'+side,(x2,0,4.78),(x3,0,4.78),.23,M['blue'])
for x in (-.19,.19): tor('Glasses_Frame',(x,-.405,6.04),.16,.025,M['glass']); sph('Glasses_Lens',(x,-.398,6.04),(.145,.018,.115),M['lens'])
cyl('Glasses_Bridge',(-.04,-.41,6.04),(.04,-.41,6.04),.025,M['glass'])
bpy.ops.object.armature_add(enter_editmode=True,location=(0,0,0)); arm=bpy.context.object; arm.name='Character_Rig'; arm.data.name='Character_Rig'; [arm.data.edit_bones.remove(b) for b in list(arm.data.edit_bones)]
def bone(n,h,t,p=None): b=arm.data.edit_bones.new(n); b.head=h; b.tail=t; b.parent=arm.data.edit_bones.get(p) if p else None
bone('root',(0,0,0),(0,0,.4)); bone('spine',(0,0,3.25),(0,0,4.65),'root'); bone('neck',(0,0,4.65),(0,0,5.45),'spine'); bone('head',(0,0,5.45),(0,0,6.25),'neck')
for side,s in [('L',-1),('R',1)]:
 bone('upper_arm.'+side,(.85*s,0,4.78),(1.7*s,0,4.78),'spine'); bone('forearm.'+side,(1.7*s,0,4.78),(2.48*s,0,4.78),'upper_arm.'+side); bone('hand.'+side,(2.48*s,0,4.78),(2.9*s,0,4.78),'forearm.'+side); bone('thigh.'+side,(.45*s,0,3.25),(.48*s,0,2.2),'root'); bone('shin.'+side,(.48*s,0,2.2),(.48*s,0,.55),'thigh.'+side); bone('foot.'+side,(.48*s,0,.55),(.48*s,-.55,.15),'shin.'+side)
bpy.ops.object.mode_set(mode='OBJECT'); arm.show_in_front=True; mv(arm,'Rig'); arm['asset_type']='character'; arm['pose']='T-pose'; arm['description']='Business man in royal blue suit with glasses'
bpy.ops.mesh.primitive_plane_add(size=30,location=(0,0,0)); floor=bpy.context.object; floor.name='Presentation_Ground'; floor.data.materials.append(M['ground']); mv(floor,'Presentation')
def track(o,p): o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(10,-18,7)); cam=bpy.context.object; cam.name='Preview_Camera'; cam.data.lens=58; track(cam,(0,0,3.5)); bpy.context.scene.camera=cam; mv(cam,'Presentation')
for typ,loc,en,size in [('AREA',(4,-8,10),1300,5),('AREA',(-5,-4,6),700,4),('AREA',(0,4,8),1000,3)]: bpy.ops.object.light_add(type=typ,location=loc); l=bpy.context.object; l.data.energy=en; l.data.shape='DISK'; l.data.size=size; track(l,(0,0,3.5)); mv(l,'Presentation')
sc=bpy.context.scene; sc.render.engine='BLENDER_EEVEE_NEXT'; sc.render.resolution_x=700; sc.render.resolution_y=700; sc.render.resolution_percentage=100; sc.render.image_settings.file_format='PNG'; sc.render.filepath=RENDER; sc.world.color=(.008,.012,.025)
bpy.ops.wm.save_as_mainfile(filepath=OUT); bpy.ops.render.render(write_still=True)
for o in bpy.context.selected_objects: o.select_set(False)
for o in bpy.context.scene.objects:
 if o.name!='Presentation_Ground' and o.type not in {'CAMERA','LIGHT'}: o.select_set(True)
bpy.context.view_layer.objects.active=arm
bpy.ops.export_scene.gltf(filepath=os.path.abspath('business_man_tpose.glb'),export_format='GLB',use_selection=True,export_yup=True)
print('SAVED',OUT,RENDER)
