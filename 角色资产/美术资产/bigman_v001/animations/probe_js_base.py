"""probe_js_base —— 逐帧量"刚性跟随基准"的几何：

  · 该侧 `qd`（上臂 guard→now 的世界旋转）的转角
  · `y_prev`（= base 作用到骨轴上的实际朝向）与目标方向 `want` 的夹角
    —— 若这一项逼近 180°，`rotation_difference` 的旋转轴不可定 ⟹
       twist 每帧乱跳（方向对、滚转错），`no_teleport` 抓的就是这个。
  · 真世界旋转步（测地角，折回 min(ang, 360-ang)）
  · 原始欧拉步 / 解缠后欧拉步

只跑 0~T_TUCK（手臂有轨的区间）。
"""
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A       # noqa: E402
import anim_idle_01 as I1  # noqa: E402
import anim_jump_start as JS  # noqa: E402


def geo(a, b):
    q = a.to_quaternion().rotation_difference(b.to_quaternion())
    ang = math.degrees(q.angle)
    return min(ang, 360.0 - ang)


arm, _ = A.open_animation_project()
A.setup_scene()
JS.build_arm_targets()
I1.idle_pose(arm, 0.0)
JS.ANKLE_REST = {s: Vector(A.bone_world(arm, "foot." + s, "head"))
                 for s in ("L", "R")}
JS.ARM_REF = JS.arm_refs(arm)
JS.ARM_GUARD_Q.clear()
for n in JS.ARM_BONES:
    JS.ARM_GUARD_Q[n] = arm.pose.bones[n].matrix.to_quaternion()
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
JS.ARM_GUARD_Q.clear()
for n in JS.ARM_BONES:
    JS.ARM_QUAT[n] = arm.pose.bones[n].matrix.to_quaternion()
    JS.ARM_GUARD_Q[n] = arm.pose.bones[n].matrix.to_quaternion()

prev_r = {n: arm.pose.bones[n].matrix.to_3x3().copy() for n in JS.ARM_BONES}
prev_raw = {n: tuple(math.degrees(v)
                     for v in arm.pose.bones[n].rotation_euler)
            for n in JS.ARM_BONES}
rows = []
for f in range(1, JS.T_TUCK + 1):
    dirs = JS.arm_dirs(f)
    pose = JS.build_pose(arm, f)
    for side in ("L", "R"):
        up = "upperarm." + side
        qd = Vector(I1.ARM_DIRS[up]).normalized().rotation_difference(
            Vector(dirs[up]).normalized())
        for n in (up, "forearm." + side, "hand." + side):
            base = qd @ JS.ARM_GUARD_Q[n]
            y_prev = (base @ Vector((0.0, 1.0, 0.0))).normalized()
            want = Vector(dirs[n]).normalized()
            sep = math.degrees(y_prev.angle(want))
            r = arm.pose.bones[n].matrix.to_3x3()
            raw = tuple(math.degrees(v)
                        for v in arm.pose.bones[n].rotation_euler)
            rows.append({
                "f": f, "bone": n,
                "qd": round(math.degrees(qd.angle), 2),
                "sep": round(sep, 2),
                "rot": round(geo(prev_r[n], r), 2),
                "raw_step": round(max(abs(x - y) for x, y
                                      in zip(raw, prev_raw[n])), 2),
                "euler_step": round(max(abs(x - y) for x, y
                                        in zip(pose[n], JS._PREV_EULER[n])), 2),
            })
            prev_r[n] = r.copy()
            prev_raw[n] = raw
rows.sort(key=lambda d: -d["euler_step"])
A.report("JSBASE_TOP", rows[:10])
print("JSBASE_SEP_MAX %s" % max(rows, key=lambda d: d["sep"]))
