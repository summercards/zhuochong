"""probe_e11_hip.py —— 量「髋关节（thigh.head） vs 骨盆骨 head」的偏移（只读）。

`A.leg_ik` 的 `hip_z` 参数实际要的是**髋关节**世界 z，而 `Idle_01` 传的是
`0.900 + DROP = 0.830`（= 骨盆骨 head 的 z）。本探针就是为了确认这两个到底差多少，
好判断尾段交接里 `py/pz` 能不能直接喂进 `leg_ik`。
"""

import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A           # noqa: E402
import anim_revive as RV       # noqa: E402

arm, meshes = RV.boot()


def show(tag, pose):
    A.apply_pose(arm, pose)
    pel = Vector(A.bone_world(arm, "pelvis", "head"))
    out = []
    for side in RV.SIDES:
        hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
        ank = Vector(A.bone_world(arm, "foot." + side, "head"))
        knee = Vector(A.bone_world(arm, "shin." + side, "head"))
        out.append("%s hip=(%+7.1f,%+7.1f,%+7.1f) ank=(%+7.1f,%+7.1f,%+7.1f) "
                   "knee=(%+7.1f,%+7.1f,%+7.1f)"
                   % (side, hip.x * 1000, hip.y * 1000, hip.z * 1000,
                      ank.x * 1000, ank.y * 1000, ank.z * 1000,
                      knee.x * 1000, knee.y * 1000, knee.z * 1000))
    print("E11H %-14s pel=(%+7.1f,%+7.1f,%+7.1f) | %s"
          % (tag, pel.x * 1000, pel.y * 1000, pel.z * 1000, " | ".join(out)))


show("Idle@0", RV.IDLE.idle_pose(arm, 0.0))
for f in (88, 92, 96, 100, 104, 110, 120):
    show("E11@%d" % f, RV.revive_pose(arm, f))
