import bpy, sys, math
sys.path.insert(0, ".")
import anim_lib as A, anim_idle_01 as I1
from mathutils import Vector, Matrix
arm, meshes = A.open_animation_project()
A.setup_scene()
print("ACTIONS", "Idle_01" in bpy.data.actions)
act = bpy.data.actions.get(I1.NAME)
arm.animation_data.action = act
A._bind_slot(arm, act)
A.reset_pose(arm); bpy.context.scene.frame_set(0); bpy.context.view_layer.update()
for n in ("upperarm.L", "forearm.L", "hand.L", "pelvis", "chest"):
    pb = arm.pose.bones[n]
    m3 = pb.matrix.to_3x3()
    y = m3 @ Vector((0.0, 1.0, 0.0))
    q = m3.to_quaternion()
    print("%-12s len=%.5f |Y|=%.5f  scale=(%.4f,%.4f,%.4f)  dir_dot=%.8f" % (
        n, pb.bone.length, y.length,
        m3.col[0].length, m3.col[1].length, m3.col[2].length,
        y.normalized().dot((pb.tail - pb.head).normalized())))
    # 用"去尺度"后的矩阵抽四元数，看与直接 to_quaternion 差多少
    clean = Matrix((
        (m3.col[0].normalized().x, m3.col[1].normalized().x, m3.col[2].normalized().x),
        (m3.col[0].normalized().y, m3.col[1].normalized().y, m3.col[2].normalized().y),
        (m3.col[0].normalized().z, m3.col[1].normalized().z, m3.col[2].normalized().z)))
    q2 = clean.to_quaternion()
    gap = math.degrees(2.0*math.acos(min(1.0, abs(q.dot(q2)))))
    print("             raw->quat vs cleaned->quat = %.5f deg" % gap)
