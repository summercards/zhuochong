"""决策用探针（只读）：
(Q1) `y_dir` 混合的**起点**该取什么：`core−shoulder`（现用）还是 `core−elbow`
     （旧口径＝真正的前臂方向）？逐帧量两者与 `−nrm` 的夹角 ⟹ 夹角越小，
     混合跨过的弧越短、越不容易在腕上产生大步长。
(Q2) 收招段（f=84..96）臂包络混合的**两端差多少**：把 IK 臂姿态与站架臂姿态
     逐骨比（世界矩阵夹角）⟹ 确认 f=91 的 15.8°/帧是不是「IK 解与站架臂的
     **滚转**差太大 × 包络斜率」。

用法：
  blender -b --factory-startup -P _e03_q.py
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
ARMB = ("upperarm.L", "upperarm.R", "forearm.L", "forearm.R",
        "hand.L", "hand.R")


def ang(a, b):
    a = Vector(a).normalized()
    b = Vector(b).normalized()
    return math.degrees(math.acos(max(-1.0, min(1.0, a.dot(b)))))


print("=" * 100)
print("(Q1) y_dir 起点候选与 -nrm 的夹角（°）")
print("   f  侧  ∠(core-sh,-nrm)  ∠(core-elbow,-nrm)  ∠(forearm,-nrm)"
      "   肘世界坐标")
for f in list(range(2, 31, 2)) + list(range(66, 97, 3)):
    A.apply_pose(arm, R.rage_pose(arm, f))
    bpy.context.view_layer.update()
    tg = R.fist_targets(arm, f)
    for side in ("R", "L"):
        _surf, nrm = R.chest_surface(arm, side)
        sh = Vector(A.bone_world(arm, "upperarm." + side, "head"))
        el = Vector(A.bone_world(arm, "forearm." + side, "head"))
        fo_t = Vector(A.bone_world(arm, "forearm." + side, "tail"))
        core = Vector(tg[side])
        print("  %3d  %s       %6.1f              %6.1f            %6.1f"
              "     (%+.3f %+.3f %+.3f)"
              % (f, side, ang(core - sh, -nrm), ang(core - el, -nrm),
                 ang(fo_t - el, -nrm), el.x, el.y, el.z))

print("=" * 100)
print("(Q2) 收招段 IK 臂姿态 vs 站架臂姿态（世界矩阵夹角，度）")
print("   f   env  " + " ".join("%11s" % b for b in ARMB))
A.apply_pose(arm, R.BASE)
bpy.context.view_layer.update()
station = {b: arm.pose.bones[b].matrix.to_3x3().normalized().copy()
           for b in ARMB}
for f in range(84, 97):
    pose = R.rage_pose(arm, f)
    A.apply_pose(arm, pose)
    ik = dict(pose)
    R.seat_arm(arm, ik, R.fist_targets(arm, f), R.arm_normals(arm, f),
               R.face_blend(f))
    A.apply_pose(arm, ik)
    bpy.context.view_layer.update()
    cells = []
    for b in ARMB:
        m = arm.pose.bones[b].matrix.to_3x3().normalized()
        q = (station[b].transposed() @ m).to_quaternion()
        cells.append("%11.2f" % math.degrees(abs(q.angle)))
    print("  %3d  %.3f  %s" % (f, R.arm_env(f), " ".join(cells)))
print("E03_Q_DONE")
