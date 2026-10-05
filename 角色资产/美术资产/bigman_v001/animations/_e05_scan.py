"""_e05_scan —— E05 碰拳帧（CLASH）的**摆位搜索**（只读，不改工程）。

背景：首轮门禁（`_e05_gate1.log`）在 CLASH 帧同时炸了四条：
  · `bstart_fist_perp_ok`  —— 两拳面侧向错开 125.9 mm（不是正对）
  · `bstart_fist_no_pierce_ok` —— 拳互插 74.7 mm
  · `bstart_hand_no_pierce_ok` —— 左拳 425 个顶点在**胸腔内**、最深 −81.5 mm
  · `no_face_clip_ok`      —— 右**前臂**穿脸 42 mm
根因是同一件：CLASH 目标放在 (x=±55, y=−0.335, z=1.290) —— **贴胸、齐下巴**，
手臂必须横过胸前并把前臂送到脸前。

本脚本在 (x, y, z) 三维网格上重解 CLASH 姿态，逐格量**四条独立读数**，
找「拳面相触 + 不插胸 + 前臂不穿脸 + 左右对称」的交集。

用法：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python _e05_scan.py
    E05_SCAN_TWIST=1   保留腰扭转（默认 0 = 去掉，因为碰拳是**对称**手势）
"""

import json
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A            # noqa: E402
import anim_battle_start as B   # noqa: E402
import probe_d01_guard as PD    # noqa: E402

SIDES = ("L", "R")


def apply_clash(arm, x_mm, y_m, z_m, twist):
    """把 CLASH 的拳目标与躯干规格改成给定值，解出姿态并铺到骨架。"""
    B.FIST_TABLE["CLASH"] = {
        "L": Vector((x_mm / 1000.0, y_m, z_m)),
        "R": Vector((-x_mm / 1000.0, y_m, z_m))}
    spec = B.SPECS["CLASH"]
    if twist:
        spec["pelvis"] = (9.0, 2.0, 0.0)
        spec["spine_01"] = (5.0, 2.0, 0.0)
        spec["spine_02"] = (5.0, 2.0, 0.0)
        spec["chest"] = (5.0, 3.0, 0.0)
        spec["neck"] = (-2.0, -1.0, 0.0)
        spec["head"] = (-4.0, -2.0, 0.0)
    else:
        spec["pelvis"] = (9.0, 0.0, 0.0)
        spec["spine_01"] = (5.0, 0.0, 0.0)
        spec["spine_02"] = (5.0, 0.0, 0.0)
        spec["chest"] = (5.0, 0.0, 0.0)
        spec["neck"] = (-2.0, 0.0, 0.0)
        spec["head"] = (-4.0, 0.0, 0.0)
    B.FREEZE["pose"] = None
    pose = B.battle_pose(arm, B.CLASH)
    A.apply_pose(arm, pose)
    bpy.context.view_layer.update()


def hand_points(side, step=6):
    return B.hand_mesh_vertices(side, step)


def fist_fist_min_dist(step=6):
    """两拳网格顶点之间的**真实最近距离**（与朝向无关的「缝/触点」读数）。"""
    pts_l = hand_points("L", step)
    pts_r = hand_points("R", step)
    best = None
    for pl in pts_l:
        for pr in pts_r:
            d = (pl - pr).length
            if best is None or d < best:
                best = d
    return best * 1000.0 if best is not None else None


def torso_pierce(step=6):
    """非拇指顶点在躯干内部的最深带符号距离 + 个数。"""
    deep, count = None, 0
    for side in SIDES:
        for point, name in B.hand_mesh_points(side, step):
            if name.startswith("Thumb_"):
                continue
            gap = B.signed_to_torso(point)
            if deep is None or gap < deep:
                deep = gap
            if gap < 0.0:
                count += 1
    return deep, count


def main():  # noqa: C901
    arm, meshes = B.boot()
    twist = os.environ.get("E05_SCAN_TWIST") == "1"
    xs = [int(v) for v in os.environ.get("E05_SCAN_X", "45,55,65,75,85,95")
          .split(",")]
    ys = [float(v) for v in os.environ.get("E05_SCAN_Y",
                                           "-0.34,-0.40,-0.46,-0.52")
          .split(",")]
    zs = [float(v) for v in os.environ.get("E05_SCAN_Z", "1.16,1.24,1.32")
          .split(",")]
    rows = []
    for x_mm in xs:
        for y_m in ys:
            for z_m in zs:
                apply_clash(arm, x_mm, y_m, z_m, twist)
                m = B.fist_clash_metrics(step=4)
                md = fist_fist_min_dist(step=8)
                deep, cnt = torso_pierce(step=6)
                clip = PD.clip_metrics(arm)
                rows.append({
                    "x": x_mm, "y": y_m, "z": z_m,
                    "gap": m["gap_mm"], "mind": None if md is None
                    else round(md, 2),
                    "sym_x": m["sym_x_mm"], "sym_y": m["sym_y_mm"],
                    "sym_z": m["sym_z_mm"], "perp": m["perp_mm"],
                    "torso_deep": None if deep is None else round(deep, 2),
                    "torso_n": cnt,
                    "clip": round(clip["clip_max_mm"], 2),
                    "clip_at": clip["clip_at"]})
    A.report("E05_SCAN", {"twist": twist, "rows": rows})

    print("")
    print("  x    y      z    | gap    mind  | symx symy symz  perp | "
          "torD  torN | clip  clip_at")
    for r in rows:
        print("%4d %6.2f %5.2f  | %6.1f %6.1f | %4.1f %4.1f %4.1f %5.1f | "
              "%6.1f %4d | %5.1f %s"
              % (r["x"], r["y"], r["z"], r["gap"], r["mind"], r["sym_x"],
                 r["sym_y"], r["sym_z"], r["perp"], r["torso_deep"],
                 r["torso_n"], r["clip"], r["clip_at"]))


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("E05_SCAN_FAILURE " + traceback.format_exc())
