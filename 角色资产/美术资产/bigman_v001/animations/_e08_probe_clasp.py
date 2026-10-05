"""_e08_probe_clasp —— E08 `Victory_03` 擦拳套 **两拳贴合安全区**猎人（本支最关键的诊断工具）。

清单 §「下一支详细制作计划 —— E08」第 3 步：
    `_e08_probe_clasp.py` 扫「两手间距 × 高度 × 前后」找**贴合不穿透**的安全区。

★ 上一步 `probe_e08_baseline.py` 的粗扫暴露了一个**状态泄漏**：`seat_arm` 会写
  `FRAME_ELBOW` / `FRAME_BULGE` / `FRAME_TWIST` / `FRAME_HAND_Q`，而逐次 `solve()`
  不清理它们 ⟹ 同一组目标在不同调用顺序下给出**不同的拳姿态**（实测 x60/z1.30
  两次读数 12.34 与 26.68）。本探针**每次求解前清空全部帧内状态 + 迭代到不动点**
  （与 `anim_victory_03.py` 的 `victory_pose` 同口径）⟹ 读数可复现。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python _e08_probe_clasp.py
"""

import json
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A          # noqa: E402
import anim_victory_02 as V2  # noqa: E402
import probe_e08_baseline as P  # noqa: E402

SIDES = ("L", "R")


def clear_frame_state():
    V2.FRAME_ELBOW.clear()
    V2.FRAME_BULGE.clear()
    V2.FRAME_TWIST.clear()
    V2.FRAME_HAND_Q.clear()


def solve(arm, base, targets, iters=3):
    """干净地解一遍双臂 IK（帧内迭代到不动点，逐帧状态不跨调用残留）。"""
    V2.LAST_ELBOW = {}
    V2.LAST_BULGE = {}
    V2.LAST_TWIST_ANGLE = {}
    V2.LAST_BLENDED = {}
    V2.LAST_HAND_Q = {}
    V2.LAST_HAND_X = dict(V2.STATION_HAND_X)
    V2.MIN_HINT_MARGIN = 1.0
    clear_frame_state()
    normals = {s: Vector((0.0, -1.0, 0.0)) for s in SIDES}
    pose = dict(base)
    for _ in range(iters):
        ik = dict(pose)
        V2.seat_arm(arm, ik, targets, normals, blend=0.0, env=1.0)
        pose = ik
    A.apply_pose(arm, pose)
    return pose


def measure(arm, pose, station, shoulder, arm_total):
    cores = {s: Vector(A.bone_world(arm, "hand." + s, "tail")) for s in SIDES}
    gap, who = P.hand_vs_hand_gap(step=1)
    reach = max((cores[s] - shoulder[s]).length
                / (arm_total[s] * 0.995) for s in SIDES)
    return {
        "gap_mm": gap, "who": who,
        "core_L_mm": [round(v * 1000.0, 1) for v in cores["L"]],
        "core_R_mm": [round(v * 1000.0, 1) for v in cores["R"]],
        "dL_mm": round((cores["L"] - station["L"]).length * 1000.0, 1),
        "dR_mm": round((cores["R"] - station["R"]).length * 1000.0, 1),
        "reach": round(reach, 4), "hint": round(V2.MIN_HINT_MARGIN, 4),
    }


def main():  # noqa: C901
    arm, _meshes = V2.boot()
    A.setup_scene()
    V2.GUARD_HAND_RIGID = False
    V2.OFFHAND_MODE = "side"

    station = {s: Vector(A.bone_world(arm, "hand." + s, "tail")) for s in SIDES}
    shoulder = {s: Vector(A.bone_world(arm, "upperarm." + s, "head"))
                for s in SIDES}
    arm_total = {s: (arm.pose.bones["upperarm." + s].length
                     + arm.pose.bones["forearm." + s].length
                     + arm.pose.bones["hand." + s].length) for s in SIDES}
    base = V2.victory_pose(arm, 0)

    # ---------------------------------------------------------- ① 对齐贴合细扫
    grid = {}
    best = None
    for x_half in (0.048, 0.054, 0.060, 0.066, 0.072):
        for z in (1.220, 1.260, 1.300):
            for y in (-0.290, -0.270, -0.250, -0.230):
                targets = {"L": Vector((+x_half, y, z)),
                           "R": Vector((-x_half, y, z))}
                pose = solve(arm, base, targets)
                row = measure(arm, pose, station, shoulder, arm_total)
                key = "x%.0f_z%.3f_y%.3f" % (x_half * 1000, z, y)
                grid[key] = row
                if 0.0 <= row["gap_mm"] <= 15.0 and max(row["dL_mm"],
                                                        row["dR_mm"]) <= 118.0:
                    score = abs(row["gap_mm"] - 6.0) + max(0.0,
                                                           row["dL_mm"] - 110)
                    if best is None or score < best[0]:
                        best = (score, key, row)
    print("E08_CLASP_GRID " + json.dumps(grid, ensure_ascii=False))
    print("E08_CLASP_BEST " + json.dumps(best, ensure_ascii=False))

    # ---------------------------------------------------------- ② 往复方向选型
    # ★ 实测（见 `E08_CLASP_SLIDE`）：两拳是**圆角**的 ⟹ 纯 `z_opp`（上下反向擦）
    #   一滑就分离（dz 16/32/48 → gap 13.3/27.1/48.8 mm）；`y_opp`（前后反向擦）
    #   分离得慢（32 → 13.9）；`y_same`（一起前后）几乎不分离。本段扫「斜向反向」
    #   组合，找「gap 全程 ≤ ~14 mm 且单程位移 ≥ 25 mm」的往复方向。
    if best is not None:
        _, key, row = best
        parts = key.split("_")
        x_half = float(parts[0][1:]) / 1000.0
        z = float(parts[1][1:])
        y = float(parts[2][1:])
        print("E08_CLASP_PICK x=%.3f z=%.3f y=%.3f" % (x_half, z, y))
        stroke = {}
        for dy, dz in ((0.030, 0.000), (0.032, 0.000), (0.028, 0.006),
                       (0.024, 0.010), (0.020, 0.014), (0.016, 0.016),
                       (0.000, 0.016), (0.034, 0.000)):
            tl = Vector((+x_half, y - dy, z - dz))
            tr = Vector((-x_half, y + dy, z + dz))
            pose = solve(arm, base, {"L": tl, "R": tr})
            m = measure(arm, pose, station, shoulder, arm_total)
            # 单程位移（拳心从 CLASP 到本键）
            disp = (Vector(m["core_L_mm"]) - Vector(row["core_L_mm"])).length
            stroke["dy%.0f_dz%.0f" % (dy * 1000, dz * 1000)] = {
                "gap_mm": m["gap_mm"],
                "stroke_len_mm": round(disp, 1),
                "dL_mm": m["dL_mm"], "dR_mm": m["dR_mm"],
                "L": m["core_L_mm"], "R": m["core_R_mm"],
                "hint": m["hint"], "reach": m["reach"]}
        print("E08_CLASP_STROKE " + json.dumps(stroke, ensure_ascii=False))

    print("E08_CLASP_DONE")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("E08_CLASP_FAILURE " + traceback.format_exc())
