"""D18 `shin.R` 万向节锁诊断（只读，不改任何落盘文件）。

目的：`no_teleport` 假红（f13→f14 裸欧拉步 70.07°，真实世界旋转只走 7.69°）。
本脚本逐帧解 D18 姿态，打印 `shin.R` 的**局部旋转**信息：
  - `eul` = 落到 pose 里的欧拉（度）
  - `m20` / `m22` = `matrix_basis` 的 [2][0] / [2][2]（万向节锁灵敏度指标）
  - `y` = `asin(-m20)`（XYZ 欧拉的中间角）
  - 对 `ROLL_GRID` 上每个 φ（绕骨轴滚转）算出的 `y` 与「相对上一帧已选表示的逐分量最大步长」

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python _d18_shin_diag.py
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bpy  # noqa: E402
from mathutils import Euler, Matrix, Vector  # noqa: E402

import anim_getup_b as B  # noqa: E402

TARGET = os.environ.get("D18_DIAG_BONE", "shin.R")
GRID = [0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 15.0, 20.0, 30.0,
        -2.0, -4.0, -6.0, -8.0, -10.0, -15.0, -20.0, -30.0,
        45.0, -45.0, 90.0, -90.0, 135.0, 180.0, -135.0]


def cands(m):
    return B.UE._xyz_candidates(m)


def unwrap_to(value, ref):
    out = list(value)
    for i in range(3):
        while out[i] - ref[i] > 180.0:
            out[i] -= 360.0
        while out[i] - ref[i] < -180.0:
            out[i] += 360.0
    return out


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

    prev_chosen = None
    prev_wq = None
    prev_dir = None
    for f in range(0, B.TOTAL + 1):
        pose = B.solve_pose(arm, f, meshes)
        B.A.apply_pose(arm, pose)
        bpy.context.view_layer.update()
        pb = arm.pose.bones[TARGET]
        wq = pb.matrix.to_3x3().to_quaternion().normalized()
        basis = pb.matrix_basis.to_3x3()
        m20, m22 = basis[2][0], basis[2][2]
        row = {"f": f}
        row["eul"] = [round(v, 2) for v in pose.get(TARGET, (0, 0, 0))]
        row["dw_world"] = (None if prev_wq is None else round(math.degrees(
            wq.rotation_difference(prev_wq).angle), 2))
        _dir_now = Vector(B.A.bone_direction(arm, TARGET)).normalized()
        row["ddir"] = (None if prev_dir is None else round(math.degrees(
            _dir_now.angle(prev_dir)), 2))
        prev_dir = _dir_now
        prev_wq = wq
        row["m20"] = round(m20, 6)
        row["m22"] = round(m22, 6)
        row["y_deg"] = round(math.degrees(math.asin(max(-1.0, min(1.0, -m20)))), 2)
        # 逐 φ（绕骨轴滚转）后的欧拉 & 相对上一帧的步长
        opts = []
        for phi_deg in GRID:
            phi = math.radians(phi_deg)
            cp, sp = math.cos(phi), math.sin(phi)
            m = basis @ Matrix(((cp, 0.0, sp), (0.0, 1.0, 0.0), (-sp, 0.0, cp)))
            best = None
            for cand in cands(m):
                val = [math.degrees(t) for t in cand]
                if prev_chosen is not None:
                    val = unwrap_to(val, prev_chosen)
                step = (None if prev_chosen is None else
                        round(max(abs(a - b) for a, b in zip(val, prev_chosen)), 2))
                yabs = abs(val[1])
                key = (999.0 if step is None else step)
                if best is None or key < best[0]:
                    best = (key, round(yabs, 2), [round(v, 2) for v in val])
            opts.append({"phi": phi_deg, "step": best[0] if best[0] < 999 else None,
                         "yabs": best[1], "eul": best[2]})
        # 只印 ±30° 内的 φ 简表 + φ=0
        small = [o for o in opts if abs(o["phi"]) <= 30.0]
        row["opts"] = small
        row["eul_step"] = (None if prev_chosen is None else round(
            max(abs(a - b) for a, b in zip(row["eul"], prev_chosen)), 2))
        print("D18_SHIN " + json.dumps(row, ensure_ascii=False))
        prev_chosen = tuple(pose.get(TARGET, (0, 0, 0)))


if __name__ == "__main__":
    main()
