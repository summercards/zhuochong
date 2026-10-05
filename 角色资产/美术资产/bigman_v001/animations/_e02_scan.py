"""_e02_scan —— E02 站架/弯腰网格二次扫描（临时脚本，只为定参数）。

背景：`probe_e02_baseline.py` 实测出 ——— 沿用 `Idle_01@0` 的**弓步站架**时，
后脚（R）膝盖到肩的距离 = **757 mm > 臂链 650 mm**（ratio 1.164）⟹
「双手扶膝」在弓步下**几何不可达**（不是参数没调好，是姿势族不匹配）。
⟹ 本支必须让角色在**过渡段把双脚挪成对称站架**（力竭时站平撑膝是自然动作）。

本脚本给对称站架扫 (drop, bend, 髋后移) 三轴，量：
  · 肩 → 膝 距离 / 臂链 650 mm 的比（**必须 ≤ ~0.95，且要留出肘部弯曲**）
  · 膝盖世界坐标（定 `exh_hand_on_knee_ok` 的目标）
  · 臂骨采样点到腿胶囊的最小外距（穿模余量）
"""

import json
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A          # noqa: E402
import anim_idle_01 as IDLE   # noqa: E402

SIDES = ("L", "R")
ARM_LEN = 0.650
ANKLE_X = 0.150
BEND_TABLE = (("pelvis", 0.22), ("spine_01", 0.24), ("spine_02", 0.24),
              ("chest", 0.22), ("neck", 0.04), ("head", 0.04))


def build(arm, drop, bend_deg, hip_back, ankle_y, knee_out_deg=0.0):
    """造一个「对称站架 + 弯腰 + 髋后移」的姿态（脚锚在指定踝上）。"""
    tilt = 12.0 * (bend_deg / 62.0)
    hip_z = 0.900 + drop
    pose = {
        "pelvis": (tilt, 0.0, 0.0),
        "spine_01": (2.0, 0.0, 0.0),
        "spine_02": (2.0, 0.0, 0.0),
        "chest": (0.0, 0.0, 0.0),
        "neck": (-6.0, 0.0, 0.0),
        "head": (5.0, 0.0, 0.0),
        "shoulder.L": (-14.0, 0.0, 0.0),
        "shoulder.R": (-14.0, 0.0, 0.0),
        "@loc": {"pelvis": A.wloc(0.0, hip_back, drop)},
    }
    for name, w in BEND_TABLE:
        if name == "pelvis":
            continue
        rx, ry, rz = pose[name]
        pose[name] = (rx + bend_deg * w, ry, rz)
    # 腿：以「髋 → 踝」平面 IK 求大腿/小腿角（tilt 用 pelvis 前倾）
    for side, sign in (("L", 1.0), ("R", -1.0)):
        thigh_rx, shin_rx = A.leg_ik(hip_back, hip_z, ankle_y, A.Z_ANKLE_REST,
                                     tilt_deg=tilt)
        pose["thigh." + side] = (thigh_rx, 0.0, -sign * knee_out_deg
                                 - sign * math.degrees(
                                     math.asin(min(1.0, (ANKLE_X - A.HIP_X)
                                                  / (A.L_THIGH + A.L_SHIN)))))
        pose["shin." + side] = (shin_rx, 0.0, 0.0)
        pose["foot." + side] = (0.0, 0.0, 0.0)
        pose["toe." + side] = (0.0, 0.0, 0.0)
    return pose


def measure(arm, pose):
    A.apply_pose(arm, pose)
    for side in SIDES:
        pose["foot." + side] = A.keep_world_orientation(arm, "foot." + side)
    A.apply_pose(arm, pose)
    row = {}
    for side in SIDES:
        knee = Vector(A.bone_world(arm, "shin." + side, "head"))
        sh = Vector(A.bone_world(arm, "upperarm." + side, "head"))
        d = (knee - sh).length
        row["knee_" + side] = [round(v * 1000.0, 1) for v in knee]
        row["shoulder_" + side] = [round(v * 1000.0, 1) for v in sh]
        row["ratio_" + side] = round(d / ARM_LEN, 4)
    row["head"] = [round(v * 1000.0, 1)
                   for v in Vector(A.bone_world(arm, "head", "tail"))]
    pts = []
    for side in SIDES:
        for name in ("upperarm." + side, "forearm." + side, "hand." + side):
            h = Vector(A.bone_world(arm, name, "head"))
            t = Vector(A.bone_world(arm, name, "tail"))
            for i in range(9):
                pts.append(h.lerp(t, i / 8.0))
    worst = 1e9
    for side in SIDES:
        for bn, r in (("thigh." + side, 0.105), ("shin." + side, 0.095)):
            a = Vector(A.bone_world(arm, bn, "head"))
            b = Vector(A.bone_world(arm, bn, "tail"))
            ab = b - a
            for p in pts:
                t = max(0.0, min(1.0, (p - a).dot(ab) / ab.length_squared))
                worst = min(worst, (p - (a + ab * t)).length - r)
    row["clearance_mm"] = round(worst * 1000.0, 1)
    low = A.foot_lowest_by_side()
    row["sole_mm"] = {s: (None if low[s] is None else round(low[s][2] * 1000.0, 2))
                      for s in SIDES}
    return row


def main():
    arm, _m = A.open_animation_project()
    A.setup_scene()
    rows = []
    for drop in (-0.090, -0.120, -0.150, -0.180):
        for bend in (50.0, 62.0, 74.0):
            for back in (0.0, 0.05, 0.10):
                for ay in (-0.10, -0.18):
                    pose = build(arm, drop, bend, back, ay)
                    r = measure(arm, pose)
                    r.update({"drop": drop, "bend": bend, "hip_back": back,
                              "ankle_y": ay})
                    rows.append(r)
    A.report("E02_SCAN", {"rows": rows})


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("E02_SCAN_FAILURE " + traceback.format_exc())
