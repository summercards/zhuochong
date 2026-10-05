"""probe_js_amp —— 逐帧放大率 = 欧拉步 / 方向步（手臂六骨）。

放大率大 = 该构型下"世界朝向的小变化"需要"欧拉分量的大变化"（近万向节锁）。
输出每帧的最大放大率与所属骨，以及该骨的局部欧拉，供判断退化构型。
"""
import math, os, sys
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A
import anim_idle_01 as I1
import anim_jump_start as JS


arm, _ = A.open_animation_project()
A.setup_scene()
JS.build_arm_targets()
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

first = I1.idle_pose(arm, 0.0)
JS._PREV_EULER.clear()
for n, v in first.items():
    if not n.startswith("@"):
        JS._PREV_EULER[n] = tuple(v)
JS.ARM_QUAT.clear()
for n in JS.ARM_BONES:
    JS.ARM_QUAT[n] = arm.pose.bones[n].matrix.to_quaternion()

prev_d = {n: (JS.ARM_QUAT[n] @ Vector((0.0, 1.0, 0.0))).normalized()
          for n in JS.ARM_BONES}
prev_e = {n: tuple(JS._PREV_EULER[n]) for n in JS.ARM_BONES}
out = []
for f in range(1, JS.TOTAL + 1):
    pose = JS.build_pose(arm, f)
    row = {"f": f}
    worst, at = 0.0, None
    for n in JS.ARM_BONES:
        want = Vector(JS.arm_dirs(f)[n]).normalized()
        dstep = math.degrees(prev_d[n].angle(want))
        estep = max(abs(x - y) for x, y in zip(pose[n], prev_e[n]))
        amp = estep / dstep if dstep > 0.05 else 0.0
        if amp > worst:
            worst, at = amp, n
        prev_d[n] = want
        prev_e[n] = tuple(pose[n])
    row["amp"] = round(worst, 2)
    row["bone"] = at
    row["local_euler"] = [round(v, 1)
                          for v in JS._PREV_EULER.get(at, (0, 0, 0))]
    out.append(row)
for r in out:
    print("JSAMPROW %d %.2f %s %s" % (r["f"], r["amp"], r["bone"],
                                      r["local_euler"]))
