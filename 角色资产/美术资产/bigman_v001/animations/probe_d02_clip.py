"""probe_d02_clip —— D02 承压循环的轻量诊断（不跑全门禁、不测鞋底）。

量三件事：
  1. 帧 0 的 `solve_pose` 欧拉与 D01 零位 `ZERO` 的差（判"能不能用 solve 结果当首键"）
  2. 全程前臂/腕到头盒的最大插入深度（穿模）
  3. 全程 胸腔顶 / 拳 / 骨盆 的竖直行程与骨盆水平位移（承压可见度）
"""

import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A                     # noqa: E402
import anim_jump_start as JS             # noqa: E402
import probe_d01_guard as PD             # noqa: E402
import anim_guard_loop as GL             # noqa: E402

arm, meshes = GL.boot()

JS._PREV_EULER.clear()
A.apply_pose(arm, GL.ZERO)
bpy.context.view_layer.update()
for name, value in GL.ZERO.items():
    if not name.startswith("@"):
        JS._PREV_EULER[name] = tuple(value)

WATCH = set(os.environ.get("D02_WATCH", "0,18,36,54,72").split(","))
WATCH = {int(v) for v in WATCH if v.strip()}

sternum, fist_z, pelvis = [], [], []
worst_clip, worst_clip_at, worst_clip_frame = -9.99, None, None
frame0_euler_delta = None
frame0_world_delta = None
rows_cache = []

for frame in range(0, GL.TOTAL + 1):
    pose = GL.solve_pose(arm, frame, meshes)

    if frame == 0:
        d = 0.0
        for name, ref in GL.ZERO.items():
            if name.startswith("@"):
                continue
            got = JS._unwrap_xyz(ref, pose.get(name, ref))
            d = max(d, max(abs(a - b) for a, b in zip(got, ref)))
        frame0_euler_delta = d
        w = 0.0
        for name, ref in GL.ZERO_WORLD.items():
            if name.endswith(".tail"):
                base = name[:-5]
                if base in arm.pose.bones:
                    got = A.bone_world(arm, base, "tail")
                    w = max(w, (Vector(got) - Vector(ref)).length)
            elif name in arm.pose.bones:
                got = A.bone_world(arm, name, "head")
                w = max(w, (Vector(got) - Vector(ref)).length)
        frame0_world_delta = w * 1000.0

    sternum.append(A.bone_world(arm, "neck", "head").z)
    fist_z.append((A.bone_world(arm, "hand.L", "tail").z
                   + A.bone_world(arm, "hand.R", "tail").z) / 2.0)
    pelvis.append(Vector(A.bone_world(arm, "pelvis", "head")))

    lo, hi = PD.head_box()
    for name in GL.ARM_BONES:
        head = Vector(A.bone_world(arm, name, "head"))
        tail = Vector(A.bone_world(arm, name, "tail"))
        for index in range(9):
            point = head.lerp(tail, index / 8.0)
            pen = PD.ARM_R - PD._outside_distance(point, lo, hi)
            if pen > worst_clip:
                worst_clip, worst_clip_at, worst_clip_frame = \
                    pen, [name, index], frame
    if frame in WATCH:
        rows_cache.append((frame, worst_clip * 1000.0, worst_clip_at,
                           [round(v * 1000.0, 1) for v in lo],
                           [round(v * 1000.0, 1) for v in hi]))

for row in rows_cache:
    print("D02C frame=%d cum_worst_mm=%.2f at=%s box_lo=%s box_hi=%s" % row)

ster = (max(sternum) - min(sternum)) * 1000.0
fz = (max(fist_z) - min(fist_z)) * 1000.0
pv = (max(p[2] for p in pelvis) - min(p[2] for p in pelvis)) * 1000.0
ph = max((p - pelvis[0]).length for p in pelvis) * 1000.0
print("D02C_SUMMARY frame0_euler_delta=%.8f frame0_world_delta_mm=%.4f"
      % (frame0_euler_delta, frame0_world_delta))
print("D02C_SUMMARY clip_max_mm=%.2f at=%s frame=%s"
      % (worst_clip * 1000.0, worst_clip_at, worst_clip_frame))
print("D02C_SUMMARY sternum_mm=%.2f fist_mm=%.2f pelvis_mm=%.2f "
      "pelvis_horiz_mm=%.3f" % (ster, fz, pv, ph))
print("D02C_DONE")
