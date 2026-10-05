"""probe_js_true —— 逐帧对比：真世界旋转步 / 原始欧拉步 / 解缠后欧拉步。"""
import math, os, sys
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A
import anim_idle_01 as I1
import anim_jump_start as JS


def geo(a, b):
    q = a.to_quaternion().rotation_difference(b.to_quaternion())
    ang = math.degrees(q.angle)
    return min(ang, 360.0 - ang)


arm, _ = A.open_animation_project()
A.setup_scene()
I1.idle_pose(arm, 0.0)
JS.ANKLE_REST = {s: Vector(A.bone_world(arm, "foot." + s, "head"))
                 for s in ("L", "R")}
JS.ARM_REF = JS.arm_refs(arm)
JS.PIVOT_FWD = JS.measure_pivot(arm)
JS.Z_OFF, _ = JS.calibrate(arm)
for s in ("L", "R"):
    piv, rest = JS.PIVOT_FWD[s], JS.ANKLE_REST[s]
    z0 = rest.z + JS.Z_OFF[s]
    t = math.radians(JS.TIP_TAKEOFF)
    JS.TAKEOFF_ANKLE_Z[s] = piv * math.sin(t) + z0 * math.cos(t)
    JS.TAKEOFF_VERT[s] = JS.TAKEOFF_PELVIS_Z - JS.TAKEOFF_ANKLE_Z[s]
I1.idle_pose(arm, 0.0)

prev_r = {n: arm.pose.bones[n].matrix.to_3x3().copy() for n in JS.ARM_BONES}
prev_e = {}
for n in JS.ARM_BONES:
    prev_e[n] = tuple(math.degrees(v)
                      for v in arm.pose.bones[n].rotation_euler)
rows = []
for f in range(1, JS.TOTAL + 1):
    pose = JS.build_pose(arm, f)
    for n in JS.ARM_BONES:
        r = arm.pose.bones[n].matrix.to_3x3()
        raw = tuple(math.degrees(v)
                    for v in arm.pose.bones[n].rotation_euler)
        rows.append({"rot": round(geo(prev_r[n], r), 2), "f": f, "bone": n,
                     "raw_step": round(max(abs(x - y) for x, y
                                           in zip(raw, prev_e[n])), 2),
                     "euler_step": round(max(abs(x - y) for x, y
                                             in zip(pose[n], prev_e[n])), 2),
                     "unwrapped": [round(v, 1) for v in pose[n]],
                     "prev": [round(v, 1) for v in prev_e[n]]})
        prev_r[n] = r.copy()
        prev_e[n] = tuple(pose[n])
rows.sort(key=lambda d: -d["euler_step"])
A.report("JSTRUETOP", rows[:6])
