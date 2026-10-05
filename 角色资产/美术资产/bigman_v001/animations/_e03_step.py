"""E03 过渡段逐帧步长定性：euler 口径 vs matrix 口径并排，逐骨打印。

判据为什么需要它：`no_snap_stop_ok` / `no_teleport` 量的是 **euler 逐帧差**，
而 `rage_matrix_step_ok` 量的是 **真实旋转**。两者在某一帧打架时，只有把
「哪根骨 / 哪个口径 / 差多少」并排摆出来，才能判断是**表示在跳**还是**动作在跳**。

★ 同时打印 `hand.<side>` 的 `local_y`（世界）与 `hand_x_hint` 的夹角 ——
  滚转退化（x_hint 与 y_dir 接近平行 ⟹ 投影趋零 ⟹ 滚转翻 180°）会在这里现形。
"""
import os
import sys
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
from mathutils import Vector, Euler  # noqa: E402

import anim_rage as R  # noqa: E402
import anim_lib as A  # noqa: E402

RANGES = os.environ.get("E03_STEP_RANGE", "16,30;70,86")
SCOPES = []
for part in RANGES.split(";"):
    lo, hi = (int(x) for x in part.split(","))
    SCOPES.extend(range(lo, hi + 1))

BONES = ["hand.L", "hand.R", "upperarm.L", "upperarm.R",
         "forearm.L", "forearm.R", "thumb_01.L", "thumb_01.R",
         "thumb_03.L", "thumb_03.R", "pinky_01.L", "pinky_01.R"]

arm, meshes = R.boot()
keyframes = [(f, R.rage_pose(arm, f)) for f in range(R.START, R.END + 1)]
keyframes = R.compat_euler(keyframes)
meta = {"anim_id": R.NAME, "loop": False, "category": "t", "frames": [0, R.TOTAL]}
action, meta = A.build_action(arm, R.NAME, keyframes, meta)
A.sample_animation(arm, action, R.START, R.END)


def euler_deg(bone):
    return [math.degrees(v) for v in arm.pose.bones[bone].rotation_euler]


def wrap360(x):
    x = abs(x) % 360.0
    return min(x, 360.0 - x)


print("=== 逐帧步长（deg）：m = 矩阵/真旋转，e = 欧拉数值 ===")
prev_m, prev_e = {}, {}
for f in SCOPES:
    bpy.context.scene.frame_set(f)
    bpy.context.view_layer.update()
    rows = []
    for b in BONES:
        m = arm.pose.bones[b].matrix.to_3x3().normalized()
        e = euler_deg(b)
        if b in prev_m:
            q = (prev_m[b].transposed() @ m).to_quaternion()
            dm = math.degrees(abs(q.angle))
            de = max(wrap360(x - y) for x, y in zip(e, prev_e[b]))
        else:
            dm = de = 0.0
        prev_m[b], prev_e[b] = m, e
        rows.append((b, dm, de))
    rows.sort(key=lambda r: max(r[1], r[2]), reverse=True)
    tag = "  ".join("%s m=%.1f e=%.1f" % r for r in rows[:3])
    print("f=%3d  %s" % (f, tag))

print()
print("=== hand 滚转退化检查：y(world) 与 x_hint 夹角（越接近 0 越危险）===")
for f in SCOPES:
    bpy.context.scene.frame_set(f)
    bpy.context.view_layer.update()
    cells = []
    for side in ("L", "R"):
        y = arm.pose.bones["hand." + side].matrix.to_3x3().col[1].normalized()
        hint = R.hand_x_hint(side, Vector((0.0, 0.0, 0.0))).normalized()
        ang = math.degrees(math.acos(max(-1.0, min(1.0, abs(y.dot(hint))))))
        cells.append("%s=%.1f" % (side, ang))
    print("f=%3d  %s" % (f, "  ".join(cells)))

print()
print("=== 帧末 euler 现场（hand.L / hand.R）===")
for f in (0, 22, 23, 24, 96):
    bpy.context.scene.frame_set(f)
    bpy.context.view_layer.update()
    print("f=%3d  hand.L=%s  hand.R=%s" % (
        f,
        ["%.1f" % v for v in euler_deg("hand.L")],
        ["%.1f" % v for v in euler_deg("hand.R")]))
