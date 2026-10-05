"""probe_e05_baseline —— E05 `Battle_Start` 开战 的**开工第一件测量**（只读，不改工程）。

清单 §「E05 详细计划」§4 第 3 步要求实测（**不许照抄 E01~E04 的结论**）：

  (a) 上游姿态：`Idle_01@0` vs `Spawn@末帧`（E04 END 已 = `Idle_01@0`）的逐骨世界
      矩阵差 ⟹ 定接缝并写理由。
  (b) ★★★ **碰拳几何**（`bstart_fist_contact_ok` / `bstart_fist_no_pierce_ok` 的
      阈值来源）：站架拳心（`hand.tail`）、拳套沿碰拳轴的**最内侧拳面** `crop`、
      以及**扫描 `x_clash`** 时两拳的 `gap` 曲线 ⟹ 「相触」的 x 到底是多少。
  (c) ★★ **活动肩膀的可达幅度**：肩骨各轴旋转 → 肩峰（`upperarm.head`）世界行程，
      在 OPEN / SHOULDER / WIND 三个实测姿态上给出读数（`bstart_shoulder_ok` 用）。
  (d) ★ 碰拳前的角速度峰值余量 —— 定包络与 `no_teleport`（≤25°/帧）。
  (e) 全网格包络（站架 / 耸肩 / 碰拳 / 摆架）⟹ 取景参数来源。

用法：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python probe_e05_baseline.py
    E05_RENDER=1  额外渲 耸肩 / 碰拳 / 摆架 三个姿态的正面 + 侧视对照图
"""

import json
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A            # noqa: E402
import anim_idle_01 as IDLE     # noqa: E402
import anim_battle_start as B   # noqa: E402

SIDES = ("L", "R")


def mesh_box():
    dg = bpy.context.evaluated_depsgraph_get()
    lo = [1e9] * 3
    hi = [-1e9] * 3
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        ev = obj.evaluated_get(dg)
        me = ev.to_mesh()
        mw = ev.matrix_world
        for v in me.vertices:
            p = mw @ v.co
            for i in range(3):
                lo[i] = min(lo[i], p[i])
                hi[i] = max(hi[i], p[i])
        ev.to_mesh_clear()
    return lo, hi


def main():  # noqa: C901
    arm, meshes = B.boot()
    scene = bpy.context.scene
    out = {}

    # ---------------- (a) 上游候选 ----------------------------------------
    def snapshot(action_name, frame):
        action = bpy.data.actions[action_name]
        if frame is None:
            frame = int(round(action.frame_range[1]))
        arm.animation_data.action = action
        A._bind_slot(arm, action)
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        mats = {n: (arm.matrix_world @ arm.pose.bones[n].matrix).copy()
                for n in arm.pose.bones.keys()}
        return frame, mats

    def diff(m_a, m_b):
        wp, we, at = 0.0, 0.0, None
        for name in m_a:
            if name not in m_b:
                continue
            pos = (m_a[name].translation
                   - m_b[name].translation).length * 1000.0
            if pos > wp:
                wp, at = pos, name
            for r in range(4):
                for c in range(4):
                    we = max(we, abs(m_a[name][r][c] - m_b[name][r][c]))
        return round(wp, 9), we, at

    f_idle, m_idle = snapshot("Idle_01", 0)
    f_spawn, m_spawn = snapshot("Spawn", None)
    f_rage, m_rage = snapshot("Rage", None)
    out["upstream"] = {
        "Spawn@end_frame": f_spawn,
        "Rage@end_frame": f_rage,
        "Idle_01@0_vs_Spawn@end": diff(m_idle, m_spawn),
        "Idle_01@0_vs_Rage@end": diff(m_idle, m_rage),
        "note": ("★ 「开战」是战斗流程的**第一个动作** ⟹ START 必须是**战斗待机**；"
                 "两项若都在 float32 噪声量级，按语义选 `Idle_01@0`。"),
    }

    # ---------------- (b) ★★★ 碰拳几何 ------------------------------------
    A.apply_pose(arm, B.BASE)
    station = B.fist_clash_metrics(step=2)
    out["station_fist_geometry"] = station
    out["station_fist_note"] = (
        "★ 站架（`Idle_01@0`）两拳读数。`crop_*` = 该手全部网格顶点沿**碰拳轴**"
        "（L 拳心 → R 拳心）投影的极大值 = **最内侧拳面**到拳心的距离。")

    scan = []
    for x_mm in (20.0, 30.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 80.0,
                 90.0, 100.0):
        B.FIST_TABLE["CLASH"] = {
            "L": Vector((x_mm / 1000.0, B.CLASH_Y_M, B.CLASH_Z_M)),
            "R": Vector((-x_mm / 1000.0, B.CLASH_Y_M, B.CLASH_Z_M))}
        B.FREEZE["pose"] = None
        pose = B.battle_pose(arm, B.CLASH)
        A.apply_pose(arm, pose)
        m = B.fist_clash_metrics(step=2)
        lo, _hi = mesh_box()
        scan.append({"x_clash_mm": x_mm,
                     "gap_mm": m["gap_mm"],
                     "crop_L_mm": m["crop_L_mm"],
                     "crop_R_mm": m["crop_R_mm"],
                     "center_dist_mm": m["center_dist_mm"],
                     "perp_mm": m["perp_mm"],
                     "sym_x_mm": m["sym_x_mm"],
                     "sym_y_mm": m["sym_y_mm"],
                     "sym_z_mm": m["sym_z_mm"],
                     "sole_min_mm": round(lo[2] * 1000.0, 2),
                     "pelvis_z_mm": round(Vector(A.bone_world(
                         arm, "pelvis", "head")).z * 1000.0, 2)})
    out["clash_x_scan"] = scan
    out["clash_x_note"] = (
        "★★★ **本表给出「相触」的 x**：`gap_mm` 由正转负的那一段就是两拳从「有缝」"
        "到「插上」的分界。⟹ `CLASH_X_MM` 取 gap ≈ 0（或略正、留 ≤ 阈值 的空隙）的 x。")

    # ---------------- (c) ★★ 活动肩膀 -------------------------------------
    shoulder = {}
    for tag, frame in (("STATION", B.START), ("OPEN", B.OPEN_AT),
                       ("SHOULDER", B.SHRUG), ("WIND", B.WIND),
                       ("CLASH", B.CLASH), ("STANCE", B.STANCE)):
        B.FREEZE["pose"] = None
        pose = B.battle_pose(arm, frame)
        A.apply_pose(arm, pose)
        row = {}
        for side in SIDES:
            e = arm.pose.bones["shoulder." + side].rotation_euler
            peak = Vector(A.bone_world(arm, "upperarm." + side, "head"))
            row["shoulder_" + side + "_deg"] = [round(math.degrees(v), 3)
                                                for v in e]
            row["peak_" + side + "_mm"] = [round(v * 1000.0, 2) for v in peak]
        shoulder[tag] = row
    out["shoulder_scan"] = shoulder
    peaks = {}
    for side in SIDES:
        pts = [Vector(shoulder[t]["peak_" + side + "_mm"]) for t in shoulder]
        peaks["peak_" + side + "_travel_mm"] = round(
            max((p - pts[0]).length for p in pts), 2)
    out["shoulder_travel"] = peaks
    out["shoulder_note"] = (
        "★★ 「活动肩膀」的可见量是**肩峰抬起**（`upperarm.head`），不是肩骨旋转本身"
        "（会被大臂遮挡）。本表给出各相位姿态下肩骨的**绝对** euler 与肩峰世界坐标"
        "⟹ `bstart_shoulder_ok` 的行程/位移阈值来源。")

    # ---------------- (d) 角速度峰值余量 ----------------------------------
    out["rate_budget"] = [
        {"swing_deg": s, "frames": f, "deg_per_frame": round(s / f, 3),
         "ok_under_25": bool(s / f <= 25.0)}
        for s, f in ((20, 6), (30, 8), (40, 10), (50, 12), (60, 14), (70, 16))
    ]

    # ---------------- (e) 包络 → 取景 -------------------------------------
    envelope = {}
    for tag, frame in (("STATION", B.START), ("SHOULDER", B.SHRUG),
                       ("CLASH", B.CLASH), ("STANCE", B.STANCE)):
        B.FREEZE["pose"] = None
        pose = B.battle_pose(arm, frame)
        A.apply_pose(arm, pose)
        lo, hi = mesh_box()
        envelope[tag] = {"bbox_mm": [[round(v * 1000.0, 1) for v in lo],
                                     [round(v * 1000.0, 1) for v in hi]]}
    out["envelope"] = envelope
    out["view_note"] = ("★ 取景必须同时装下：站架鞋底 0 → 头顶 ~1803；耸肩时肘尖"
                        "（正是最外沿）。**不许照抄 E01~E04**。")

    # ---------------- (f) 出图对照 ----------------------------------------
    if os.environ.get("E05_RENDER") == "1":
        cam = bpy.data.objects.get("Presentation_Camera")
        if arm.animation_data is not None:
            arm.animation_data.action = None
        for tag, frame in (("shrug", B.SHRUG), ("clash", B.CLASH),
                           ("stance", B.STANCE)):
            B.FREEZE["pose"] = None
            pose = B.battle_pose(arm, frame)
            A.apply_pose(arm, pose)
            A.render_still(cam, os.path.join(
                A.PREVIEW_DIR, "_e05_probe_%s_front.png" % tag),
                (0.0, -4.8, 0.90), (0.0, 0.0, 0.90), 2.20, (780, 1100))
            A.render_still(cam, os.path.join(
                A.PREVIEW_DIR, "_e05_probe_%s_side.png" % tag),
                (4.4, -0.02, 0.90), (0.0, -0.02, 0.90), 2.20, (780, 1100))

    A.report("E05_BASE", out)


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("E05_BASE_FAILURE " + traceback.format_exc())
