"""probe_js_roll —— 手臂欧拉通道的逐帧体检 + 全圈 roll 可达性。

输出两段：
  1) f14~36 每帧：forearm.R 的目标方向、选定 roll、解缠欧拉、真世界旋转步、欧拉步。
  2) 在问题帧处扫**全圆** roll（2° 步长），给出该帧可达的最小欧拉步
     —— 判定"是搜索范围不够，还是这一帧的位移本身在欧拉里就是大的"。
"""
import math
import os
import sys

import bpy
from mathutils import Quaternion, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A       # noqa: E402
import anim_idle_01 as I1  # noqa: E402
import anim_jump_start as JS  # noqa: E402

BONE = os.environ.get("PROBE_BONE", "forearm.R")

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
JS.ARM_ROLL.clear()
for n in JS.ARM_BONES:
    JS.ARM_QUAT[n] = arm.pose.bones[n].matrix.to_quaternion()

prev_r = None
rows = []
qs = {}
for f in range(1, JS.TOTAL + 1):
    JS.build_pose(arm, f)
    qs[f] = JS.ARM_QUAT[BONE].copy()
    r = arm.pose.bones[BONE].matrix.to_3x3()
    rot = 0.0
    if prev_r is not None:
        q = prev_r.to_quaternion().rotation_difference(r.to_quaternion())
        rot = min(math.degrees(q.angle), 360.0 - math.degrees(q.angle))
    prev_r = r.copy()
    if f >= 12:
        rows.append({"f": f, "roll": round(JS.ARM_ROLL.get(BONE, 0.0), 1),
                     "euler": [round(v, 1) for v in JS._PREV_EULER[BONE]],
                     "true_rot": round(rot, 2)})
prev = [0.0] * len(rows)
for i in range(1, len(rows)):
    prev[i] = max(abs(a - b) for a, b in zip(rows[i]["euler"], rows[i - 1]["euler"]))
for i, row in enumerate(rows):
    row["euler_step"] = round(prev[i], 2)
    print("JSROLL %(f)d roll=%(roll)s step=%(euler_step)s true=%(true_rot)s "
          "e=%(euler)s" % row)

# ---- 全圆 roll 可达性：在问题帧处，上一帧欧拉已知，扫 0~360 找最小欧拉步
tgt = int(os.environ.get("PROBE_FRAME", "30"))
index = [r["f"] for r in rows].index(tgt)
if index == 0:
    print("JSROLL_SCAN skipped (need f>=13)")
else:
    prev_e = tuple(rows[index - 1]["euler"])
    want = Vector(JS.arm_dirs(tgt)[BONE]).normalized()
    prev_q = qs[tgt - 1]
    y_prev = (prev_q @ Vector((0.0, 1.0, 0.0))).normalized()
    q0 = y_prev.rotation_difference(want) @ prev_q
    best, best_roll = None, None
    for roll in range(0, 360, 2):
        q = Quaternion(want, math.radians(roll)) @ q0
        e = JS._unwrap_xyz(prev_e, JS._set_world_quat(arm, BONE, q))
        cost = max(abs(a - b) for a, b in zip(prev_e, e))
        if roll % 30 == 0:
            print("JSROLL_MAP roll=%3d e=%s step=%.2f"
                  % (roll, [round(v, 1) for v in e], cost))
        if best is None or cost < best:
            best, best_roll = cost, roll
    print("JSROLL_SCAN frame=%d best_step=%.2f at roll=%d (carry step was %s)"
          % (tgt, best, best_roll, rows[index]["euler_step"]))
    print("JSROLL_SCAN carry_q_is_roll0 step=%.2f"
          % max(abs(a - b) for a, b in
                zip(prev_e, JS._unwrap_xyz(
                    prev_e, JS._set_world_quat(arm, BONE, q0)))))
