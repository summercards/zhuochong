"""E07 定点诊断 5：R 臂收招段的**真路径** + 矩阵口径角步（★ 过 compat_euler 后）。

目的：把「f100 forearm.R 90° 真跳」与「f105 R 拳穿躯干」两件事，落到
「拳在哪 / 肘在哪 / 前臂指向哪 / 站架在哪」四个实数上。
★ 与初版的区别：角步在 **`compat_euler` + `seam_canonicalize` 之后**量 ——
  初版直接量原始 pose，会把「欧拉表示跳」误判成「动作跳」。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import math  # noqa: E402

from mathutils import Vector  # noqa: E402

import anim_lib as A  # noqa: E402
import anim_victory_02 as V2  # noqa: E402

arm, meshes = V2.boot()
S = V2.SIDES
mm = lambda v: [round(x * 1000.0, 1) for x in v]  # noqa: E731
print("STATION_FIST", {s: mm(V2.STATION_FIST[s]) for s in S})
print("STATION_POLE", {s: [round(x, 3) for x in V2.STATION_POLE_DIR[s]]
                       for s in S})
print("AT", V2.EULER_BLEND_AT, "ITERS", V2.ARM_SOLVE_ITERS,
      "OFFHAND", V2.OFFHAND_MODE)

raw = {}
for f in range(0, V2.TOTAL + 1):
    raw[f] = V2.victory_pose(arm, f)
kf = V2.seam_canonicalize(V2.compat_euler([(f, raw[f]) for f in sorted(raw)]))
poses = dict(kf)

# ---- A 段：双臂逐帧真路径（起手段 + 收招段） -----------------------------
print("---- arm path ----")
for f in list(range(0, 20)) + list(range(88, V2.TOTAL + 1, 2)):
    A.apply_pose(arm, poses[f])
    hdl = Vector(A.bone_world(arm, "hand.L", "tail"))
    hdr = Vector(A.bone_world(arm, "hand.R", "tail"))
    print("f=%3d env=%.3f L=[%7.1f,%7.1f,%7.1f] gL=%7.2f "
          "R=[%7.1f,%7.1f,%7.1f] gR=%7.2f"
          % (f, V2.arm_env(f), hdl.x * 1000, hdl.y * 1000, hdl.z * 1000,
             V2.signed_to_torso(hdl), hdr.x * 1000, hdr.y * 1000,
             hdr.z * 1000, V2.signed_to_torso(hdr)))

# ---- B 段：矩阵口径逐帧角步（compat_euler 之后） --------------------------
print("---- matrix step (deg) top ----")
def _ang(a, b):
    """两组旋转的**测地角**（度）：`acos((tr(aᵀb) − 1)/2)` —— 与四元数双覆盖无关。"""
    m = a.transposed() @ b
    tr = sum(m[i][i] for i in range(3))
    return math.degrees(math.acos(max(-1.0, min(1.0, (tr - 1.0) / 2.0))))


names = sorted(V2.BONE_LIST)
steps = []
prev = None
for f in range(0, V2.TOTAL + 1):
    A.apply_pose(arm, poses[f])
    cur = {n: arm.pose.bones[n].matrix.to_3x3().normalized().copy()
           for n in names}
    if prev is not None:
        for n in names:
            d = _ang(prev[n], cur[n])
            if d > 5.0:
                steps.append((d, f, n))
    prev = cur
steps.sort(reverse=True)
for d, f, n in steps[:25]:
    print("STEP %8.2f  f=%3d->%3d  %s" % (d, f - 1, f, n))
print("DIAG5_END")
