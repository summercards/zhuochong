import os, sys
import bpy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A
arm, meshes = A.open_animation_project()
A.setup_scene()
sc = bpy.context.scene
for name, fr in (("Idle_01",0),("Idle_01",90),("Hit_Head",0),("Hit_Head",10),("Hit_Head",17),("Hit_Head",34),("Idle_01",0),("Idle_01",180)):
    act = bpy.data.actions[name]
    arm.animation_data.action = act
    A._bind_slot(arm, act)
    sc.frame_set(fr)
    bpy.context.view_layer.update()
    p = arm.matrix_world @ arm.pose.bones["pelvis"].matrix.translation
    hd = arm.matrix_world @ arm.pose.bones["head"].tail
    hh = arm.matrix_world @ arm.pose.bones["head"].head
    print("CASE %-10s f=%3d pelvis=(%8.2f,%8.2f,%8.2f) head.tail=(%8.2f,%8.2f,%8.2f) head.head=(%8.2f,%8.2f,%8.2f)"
          % (name, fr, p.x*1000,p.y*1000,p.z*1000, hd.x*1000,hd.y*1000,hd.z*1000, hh.x*1000,hh.y*1000,hh.z*1000))
