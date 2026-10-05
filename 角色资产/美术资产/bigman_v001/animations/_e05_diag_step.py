"""_e05_diag_step —— 定位 `bstart_matrix_step_ok` 失败的**单帧**（只读诊断）。

读数：`bstart_matrix_step_deg_max = 30.594 @ (49, 'forearm.L')`（阈值 25）。
49 = 定格窗 [46,48] 的**下一帧**。本脚本逐帧打印：
  · 臂三段 euler（解算值，未经 build_action）
  · 该帧世界矩阵相对上一帧的**真实旋转步**（逐骨最大）
  · 拳目标世界坐标
以区分「目标在跳」「IK 分支在跳」「欧拉表示在跳」三种可能。
"""

import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A            # noqa: E402
import anim_battle_start as B   # noqa: E402

SIDES = ("L", "R")
WATCH = ("upperarm.L", "forearm.L", "hand.L", "shoulder.L", "chest")


def main():
    arm, meshes = B.boot()
    scene = bpy.context.scene
    prev = None
    for frame in range(B.WIND - 2, B.STANCE + 3):
        B.FREEZE["pose"] = None if frame <= B.HOLD[0] else B.FREEZE["pose"]
        pose = B.battle_pose(arm, frame)
        A.apply_pose(arm, pose)
        bpy.context.view_layer.update()
        mats = {n: (arm.matrix_world
                    @ arm.pose.bones[n].matrix).to_3x3().copy()
                for n in WATCH}
        step, at = 0.0, None
        if prev is not None:
            for n in WATCH:
                a, b = prev[n], mats[n]
                for c in range(3):
                    va = a.col[c].normalized()
                    vb = b.col[c].normalized()
                    d = math.degrees(math.acos(max(-1.0, min(1.0,
                                                             va.dot(vb)))))
                    if d > step:
                        step, at = d, n
        tgt = B.fist_targets(arm, frame, Vector((0.0, 0.0, 0.0)))
        eul = {n: [round(math.degrees(v), 2)
                   for v in arm.pose.bones[n].rotation_euler] for n in WATCH}
        print("f=%3d  step=%7.3f @%-12s  tgtL=(%7.1f %7.1f %7.1f) tgtR.x=%7.1f"
              % (frame, step, at,
                 tgt["L"].x * 1000, tgt["L"].y * 1000, tgt["L"].z * 1000,
                 tgt["R"].x * 1000))
        print("        sh=%s" % eul["shoulder.L"])
        print("        up=%s  fo=%s" % (eul["upperarm.L"], eul["forearm.L"]))
        print("        hd=%s  ch=%s" % (eul["hand.L"], eul["chest"]))
        prev = mats


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("E05_DIAG_FAILURE " + traceback.format_exc())
