"""D18 末段 `shin.R` 深诊断（只读）：f33→f34 的 112° 是「方向」还是「绕骨轴滚转」。

对每帧打印：
  - `eul`     落到 pose 的欧拉（度）
  - `dirEnd`  shin.R 骨轴方向 与 END 姿态方向的夹角（度）
  - `wEnd`    shin.R **世界 3×3** 与 END 姿态世界 3×3 的旋转夹角（度）
  - `rollEnd` 在"方向已对齐"前提下，绕骨轴的滚转残差（度）
  - `footW`   foot.R 世界 3×3 与 END 的夹角

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python _d18_shin_diag2.py
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bpy  # noqa: E402
from mathutils import Euler, Quaternion, Vector  # noqa: E402

import anim_getup_b as B  # noqa: E402

F0 = int(os.environ.get("D18_DIAG2_F0", "22"))
F1 = int(os.environ.get("D18_DIAG2_F1", "36"))
BONE = os.environ.get("D18_DIAG2_BONE", "shin.R")


def wq(arm, name):
    return arm.pose.bones[name].matrix.to_3x3().to_quaternion().normalized()


def main():
    arm, meshes = B.boot()

    # ---- 先取 END 姿态的世界参考 ----
    B.A.apply_pose(arm, B.END_POSE)
    bpy.context.view_layer.update()
    end_wq = {n: wq(arm, n) for n in (BONE, "thigh." + BONE[-1],
                                      "foot." + BONE[-1], "toe." + BONE[-1])}
    end_dir = {n: Vector(B.A.bone_direction(arm, n)).normalized()
               for n in (BONE, "thigh." + BONE[-1])}

    B.JS._PREV_EULER.clear()
    B.UE.CARRY_Q.clear()
    B.LOCK_POSE.clear()
    B._LOCK_REUSED[0] = 0
    B.A.apply_pose(arm, B.ZERO)
    bpy.context.view_layer.update()
    for name in B.ARM_BONES + B.LEG_BONES:
        B.UE.CARRY_Q[name] = arm.pose.bones[name].matrix.to_3x3().to_quaternion()
    for name, value in B.ZERO.items():
        if not name.startswith("@"):
            B.JS._PREV_EULER[name] = tuple(value)

    for f in range(0, B.TOTAL + 1):
        pose = B.solve_pose(arm, f, meshes)
        B.A.apply_pose(arm, pose)
        bpy.context.view_layer.update()
        if not (F0 <= f <= F1):
            continue
        row = {"f": f}
        row["eul"] = [round(v, 2) for v in pose.get(BONE, (0, 0, 0))]
        side = BONE[-1]
        for n, tag in ((BONE, "self"), ("thigh." + side, "thigh"),
                       ("foot." + side, "foot"), ("toe." + side, "toe")):
            q = wq(arm, n)
            row["w_" + tag] = round(math.degrees(
                q.rotation_difference(end_wq[n]).angle), 2)
        d = Vector(B.A.bone_direction(arm, BONE)).normalized()
        row["dir"] = round(math.degrees(
            d.angle(end_dir[BONE])), 2) if d.length else None
        # 方向对齐后剩下的滚转
        q = wq(arm, BONE)
        align = end_dir[BONE].rotation_difference(d)
        row["roll"] = round(math.degrees(
            (align @ end_wq[BONE]).rotation_difference(q).angle), 2)
        print("D18_SHIN2 " + json.dumps(row, ensure_ascii=False))


if __name__ == "__main__":
    main()
