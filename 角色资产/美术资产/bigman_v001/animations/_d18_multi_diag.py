"""D18 多骨逐帧诊断（只读，不落盘）。

对 `D18_DIAG_BONES`（逗号分隔）里的每根骨，逐帧解 D18 姿态并打印：
  - `eul`     落到 pose 里的欧拉（度）
  - `step`    相对上一帧**已选表示**的逐分量最大步长（= 门禁 `no_teleport` 的口径）
  - `dw`      相对上一帧的**世界 3×3 测地角**（真旋转）
  - `ddir`    骨轴方向的转角（真方向）
  - `y`       XYZ 欧拉的中间角（|y|→90 即万向节锁带）

用途：把每个超限点判成「真闪帧（dw 大）」还是「欧拉表示跳（dw 小）」。

运行：
    D18_DIAG_BONES=thigh.L,forearm.L,shin.R PYTHONHASHSEED=0 \
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python _d18_multi_diag.py
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import anim_getup_b as B  # noqa: E402

BONES = [b for b in os.environ.get(
    "D18_DIAG_BONES", "thigh.L,forearm.L,shin.R").split(",") if b]
MIN_STEP = float(os.environ.get("D18_DIAG_MINSTEP", "18"))


def main():
    arm, meshes = B.boot()
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

    prev = {b: {"eul": None, "wq": None, "dir": None} for b in BONES}
    for f in range(0, B.TOTAL + 1):
        pose = B.solve_pose(arm, f, meshes)
        B.A.apply_pose(arm, pose)
        bpy.context.view_layer.update()
        for b in BONES:
            pb = arm.pose.bones.get(b)
            if pb is None:
                continue
            eul = [round(v, 2) for v in pose.get(b, (0, 0, 0))]
            wq = pb.matrix.to_3x3().to_quaternion().normalized()
            dnow = Vector(B.A.bone_direction(arm, b)).normalized()
            p = prev[b]
            step = (None if p["eul"] is None else
                    round(max(abs(x - y) for x, y in zip(eul, p["eul"])), 2))
            dw = (None if p["wq"] is None else round(math.degrees(
                wq.rotation_difference(p["wq"]).angle), 2))
            ddir = (None if p["dir"] is None else round(
                math.degrees(dnow.angle(p["dir"])), 2))
            if step is not None and step >= MIN_STEP:
                print("D18_MULTI " + json.dumps({
                    "f": f, "bone": b, "eul": eul, "prev_eul": p["eul"],
                    "step": step, "dw": dw, "ddir": ddir, "y": round(eul[1], 2)}))
            p["eul"], p["wq"], p["dir"] = eul, wq, dnow


if __name__ == "__main__":
    main()
