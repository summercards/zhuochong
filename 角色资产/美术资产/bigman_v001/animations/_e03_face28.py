"""定点探针：把命中帧两侧拳头的**几何**摊开（L 拳面 14.71 mm 而 R 只有 2.84 mm）。

要回答的问题：`resolve_fist` 对两侧都返回「胸面 + 法线×TOUCH_OFF」，为何
**实现出来的**指节面距离差 12 mm？

打印（f = 命中帧与邻近帧）：
  · 胸面点 / 外法线（世界）
  · 拳心目标 core、`hand.tail` 实达位置、两者差
  · y_dir / x_axis / z_axis（世界）
  · 指节簇（掌 + 指，不含拇指）**最近顶点**：对象名 / 到胸带符号距离 / 该顶点沿法线的分量
  · 拇指最近顶点：对象名 / 距离
  · 拳心到**各方向**的极值顶点：沿 +y(拳轴) / −y / +x / −x / +z / −z 的投影极值
    ⟹ 直接看出「拳面朝哪、指节面有没有正对胸」

用法：
  blender -b --factory-startup -P _e03_face28.py
"""
import os
import sys
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import anim_rage as R  # noqa: E402
import anim_lib as A  # noqa: E402

arm, meshes = R.boot()

FRAMES = [26, 27, 28, 29, 30, 36, 44, 52]


def ext(points, axis, want_max):
    best = None
    for p, name in points:
        d = p.dot(axis)
        if best is None or (d > best[0] if want_max else d < best[0]):
            best = (d, name, p.copy())
    return best


for frame in FRAMES:
    pose = R.rage_pose(arm, frame)
    A.apply_pose(arm, pose)
    targets = R.fist_targets(arm, frame)
    normals = R.arm_normals(arm, frame)
    blend = R.face_blend(frame)
    print("=" * 78)
    print("f=%d  face_blend=%.3f  arm_env=%.3f" % (frame, blend,
                                                   R.arm_env(frame)))
    for side in R.SIDES:
        surf, nrm = R.chest_surface(arm, side)
        core = Vector(targets[side])
        tail = Vector(A.bone_world(arm, "hand." + side, "tail"))
        head = Vector(A.bone_world(arm, "hand." + side, "head"))
        pts = R.hand_mesh_points(side, step=1)
        knuckle = [(p, n) for p, n in pts if not n.startswith("Thumb_")]
        thumb = [(p, n) for p, n in pts if n.startswith("Thumb_")]
        fmin = min((R.signed_to_torso(p), n, p) for p, n in knuckle)
        tmin = min((R.signed_to_torso(p), n, p) for p, n in thumb)
        hb = R.current_head_back(arm) if hasattr(R, "current_head_back") else 0.0
        y_dir = (tail - head).normalized()
        # 手骨三轴（用 pose bone 矩阵的列）
        m = arm.pose.bones["hand." + side].matrix.to_3x3()
        ax, ay, az = (m.col[0].normalized(), m.col[1].normalized(),
                      m.col[2].normalized())
        print("  [%s] nrm=(%+.3f %+.3f %+.3f)  y_dir=(%+.3f %+.3f %+.3f)"
              % (side, nrm.x, nrm.y, nrm.z, y_dir.x, y_dir.y, y_dir.z))
        print("       y_dir·nrm=%+.3f  ∠(y_dir,−nrm)=%5.1f°"
              % (y_dir.dot(nrm), math.degrees(math.acos(
                  max(-1.0, min(1.0, -y_dir.dot(nrm)))))))
        print("       bone x=(%+.3f %+.3f %+.3f) y=(%+.3f %+.3f %+.3f) "
              "z=(%+.3f %+.3f %+.3f)"
              % (ax.x, ax.y, ax.z, ay.x, ay.y, ay.z, az.x, az.y, az.z))
        print("       core_gap=%+7.2f  tail_gap=%+7.2f  |tail−core|=%.3f mm"
              % (R.signed_to_torso(core), R.signed_to_torso(tail),
                 (tail - core).length * 1000.0))
        print("       拳面最近 %-22s gap=%+7.2f  (沿nrm分量 %+7.2f)"
              % (fmin[1], fmin[0],
                 (fmin[2] - surf).dot(nrm) * 1000.0))
        print("       拇指最近 %-22s gap=%+7.2f" % (tmin[1], tmin[0]))
        nz = nrm
        print("       拳簇沿法线极值: min=%+7.2f (%s)  max=%+7.2f (%s)"
              % (ext(knuckle, nz, False)[0] * 1000.0,
                 ext(knuckle, nz, False)[1],
                 ext(knuckle, nz, True)[0] * 1000.0,
                 ext(knuckle, nz, True)[1]))
        print("       拳簇沿±X极值: L侧=%+7.2f (%s)  R侧=%+7.2f (%s)"
              % (ext(knuckle, Vector((1, 0, 0)), True)[0] * 1000.0,
                 ext(knuckle, Vector((1, 0, 0)), True)[1],
                 ext(knuckle, Vector((-1, 0, 0)), True)[0] * 1000.0,
                 ext(knuckle, Vector((-1, 0, 0)), True)[1]))
print("E03_FACE28_DONE")
