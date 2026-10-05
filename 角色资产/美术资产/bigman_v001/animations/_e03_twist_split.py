"""标定前臂旋前量：给定 `E03_FOREARM_TWIST`，量手部 euler 逐帧步长与真旋转步长。

目的：找出让 `no_teleport`（euler 步 ≤ 25°/帧）成立、且**真实旋转步不增大**的
扭转载荷分配。判据是「手的世界朝向不变、真旋转步不变、只有 euler 分解变」，
所以这里必须**同时**打印两个口径 —— 只看 euler 会被「把真跳藏进表示」骗过。

用法：
  E03_FOREARM_TWIST=45 blender -b --factory-startup -P _e03_twist_split.py
"""
import os
import sys
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
from mathutils import Matrix  # noqa: E402

import anim_rage as R  # noqa: E402
import anim_lib as A  # noqa: E402

BONES = ["hand.L", "hand.R", "forearm.L", "forearm.R"]

arm, meshes = R.boot()
keyframes = [(f, R.rage_pose(arm, f)) for f in range(R.START, R.END + 1)]
keyframes = R.compat_euler(keyframes)
keyframes = R.seam_canonicalize(keyframes)
action, _meta = A.build_action(arm, R.NAME, keyframes,
                              {"anim_id": R.NAME, "loop": False,
                               "category": "t", "frames": [0, R.TOTAL]})
A.sample_animation(arm, action, R.START, R.END)


def wrap360(x):
    x = abs(x) % 360.0
    return min(x, 360.0 - x)


prev_m, prev_e = {}, {}
step_m = {b: (0.0, -1) for b in BONES}
step_e = {b: (0.0, -1) for b in BONES}
ry_lo = {b: 1e9 for b in BONES}
ry_hi = {b: -1e9 for b in BONES}
for f in range(R.START, R.END + 1):
    bpy.context.scene.frame_set(f)
    bpy.context.view_layer.update()
    for b in BONES:
        m = arm.pose.bones[b].matrix.to_3x3().normalized()
        e = [math.degrees(v) for v in arm.pose.bones[b].rotation_euler]
        ry_lo[b] = min(ry_lo[b], e[1])
        ry_hi[b] = max(ry_hi[b], e[1])
        if b in prev_m:
            q = (prev_m[b].transposed() @ m).to_quaternion()
            dm = math.degrees(abs(q.angle))
            de = max(wrap360(x - y) for x, y in zip(e, prev_e[b]))
            if dm > step_m[b][0]:
                step_m[b] = (dm, f)
            if de > step_e[b][0]:
                step_e[b] = (de, f)
        prev_m[b], prev_e[b] = m, e

tw = R.FOREARM_TWIST_DEG
print("E03_TWIST_PROBE twist=%g" % tw)
for b in BONES:
    print("  %-10s euler_step=%7.2f @f%-3d  matrix_step=%7.2f @f%-3d  "
          "ry=[%.1f, %.1f]" % (b, step_e[b][0], step_e[b][1],
                               step_m[b][0], step_m[b][1],
                               ry_lo[b], ry_hi[b]))

print()
print("=== f=14..30 的 hand 局部 euler（度）===")
for f in range(14, 31):
    bpy.context.scene.frame_set(f)
    bpy.context.view_layer.update()
    cells = []
    for b in ("hand.L", "hand.R"):
        e = [math.degrees(v) for v in arm.pose.bones[b].rotation_euler]
        cells.append("%s=[%7.1f %7.1f %7.1f]" % (b[-1], e[0], e[1], e[2]))
    print("f=%3d  %s" % (f, "  ".join(cells)))
