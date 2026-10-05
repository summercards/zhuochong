"""probe_e02_baseline —— E02 `Exhausted` 虚弱 的**开工第一件测量**（只读，不改工程）。

计划 §0 / §4 第 3 步要求实测（**不许照抄 E01 的结论**）：

  (a) 上游姿态：`Idle_01@0` vs `Stun@末帧`（120）—— 逐骨世界矩阵差；
      ★ E01 已实测 `Idle_01@0/180`、`Hit_Head@0/34` 四者逐位同一姿态，
        且 `Stun` 末帧逐位 = `Idle_01@0` ⟹ 两个候选**代价应相等**，只能按语义选。
        本探针**复核**这一点（不许凭 E01 的话就当真）。
  (b) ★★★ 膝盖（`shin.*` head = `thigh.*` tail）随骨盆下沉 + 弯腰怎么走
      —— 这是本支的**动目标**，是**新问题**（E01 的锚点是静止的踝）。
  (c) ★★ 臂链长度够不够：`upperarm + forearm + hand` 总长 vs 「肩 → 膝」距离。
      **若够不到 ⟹ 加大弯腰深度或屈膝，不许硬拉肩膀**。
  (d) 站姿下「手 / 前臂」与**大腿 / 小腿**的最小间距 + 腿的等效半径
      —— 穿模余量基准（`no_face_clip_ok` 只量臂 vs 头盒，**盖不到手 vs 腿**）。
  (e) 喘气周期需要多少帧 → 定总预算（★ E01 已登记上界 120 帧 / 2.0 s）。
  (f) 像素上「手扶膝」怎么看出来 —— 正面 / 侧视各渲一张对照，量**手**在屏幕上的位置。

用法：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python probe_e02_baseline.py
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
ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")

# ---------------------------------------------------------------- 候选弯身姿态
# rx > 0 = 前屈。合计 = 躯干总前倾（度）。★ 分配**不是**均匀的：越靠上的段给得越少，
# 否则头会一起扎下去、读成「鞠躬」而不是「力竭弯腰」。
BEND_TABLE = (
    ("pelvis",   0.22),
    ("spine_01", 0.24),
    ("spine_02", 0.24),
    ("chest",    0.22),
    ("neck",     0.04),
    ("head",     0.04),
)
BEND_TOTAL_DEG = 62.0          # 满弯时的躯干总前倾

DROPS = (-0.020, -0.060, -0.090, -0.120, -0.150, -0.180)
BEND_SCALES = (0.0, 0.5, 0.75, 1.0)

LEG_ITER = 8
LEG_DAMP = 0.85
THIGH_RZ_GAIN = 1.0 / 0.01309


def _ankles(arm):
    return {s: Vector(A.bone_world(arm, "foot." + s, "head")) for s in SIDES}


def lock_feet(arm, pose, want):
    """照抄 `anim_stun.lock_feet`（闭环数值修正；planar IK + thigh.rz 配平 x）。"""
    tgt = {s: Vector(want[s]) for s in SIDES}
    rz = {s: pose.get("thigh." + s, (0.0, 0.0, 0.0))[2] for s in SIDES}
    pelvis_rx = pose.get("pelvis", (0.0, 0.0, 0.0))[0]
    worst = 0.0
    for _ in range(LEG_ITER):
        A.apply_pose(arm, pose)
        for side in SIDES:
            hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
            th, sh = A.leg_ik(hip.y, hip.z, tgt[side].y, tgt[side].z,
                              tilt_deg=pelvis_rx)
            pose["thigh." + side] = (th, 0.0, rz[side])
            pose["shin." + side] = (sh, 0.0, 0.0)
        A.apply_pose(arm, pose)
        for side in SIDES:
            pose["foot." + side] = A.keep_world_orientation(arm, "foot." + side)
        A.apply_pose(arm, pose)
        for side in SIDES:
            err = Vector(A.bone_world(arm, "foot." + side, "head")) - Vector(want[side])
            tgt[side] = tgt[side] - err * LEG_DAMP
            rz[side] = rz[side] + THIGH_RZ_GAIN * err.x * LEG_DAMP
            worst = max(worst, err.length * 1000.0)
    return worst


def bent_pose(arm, base, drop, scale):
    """由站架姿态派生一个「弯腰 + 下沉」姿态（脚锚在 base 的踝上）。"""
    pose = {}
    for key, value in base.items():
        pose[key] = (tuple(value) if not key.startswith("@")
                     else {k: tuple(v) for k, v in value.items()})
    pose.setdefault("@loc", {})
    for name, w in BEND_TABLE:
        rx, ry, rz = pose.get(name, (0.0, 0.0, 0.0))
        pose[name] = (rx + BEND_TOTAL_DEG * w * scale, ry, rz)
    loc = pose["@loc"].get("pelvis", (0.0, 0.0, 0.0))
    base_drop = -0.070
    pose["@loc"]["pelvis"] = (loc[0], loc[1] + (drop - base_drop), loc[2])
    return pose


def measure(arm, base, anchor, drop, scale):
    pose = bent_pose(arm, base, drop, scale)
    lock_err = lock_feet(arm, pose, anchor)
    A.apply_pose(arm, pose)
    row = {"drop_mm": round(drop * 1000.0, 1), "bend_scale": scale,
           "lock_err_mm": round(lock_err, 4)}
    pelvis = Vector(A.bone_world(arm, "pelvis", "head"))
    row["pelvis_z_mm"] = round(pelvis.z * 1000.0, 2)
    row["hand_leg_dists"] = {}
    for side in SIDES:
        knee = Vector(A.bone_world(arm, "shin." + side, "head"))
        sh = Vector(A.bone_world(arm, "upperarm." + side, "head"))
        d = (knee - sh).length
        row["knee_mm_" + side] = [round(v * 1000.0, 2) for v in knee]
        row["shoulder_mm_" + side] = [round(v * 1000.0, 2) for v in sh]
        row["shoulder_knee_mm_" + side] = round(d * 1000.0, 2)
        row["reach_ratio_" + side] = round(d / 0.650, 4)
    row["head_mm"] = [round(v * 1000.0, 2)
                      for v in Vector(A.bone_world(arm, "head", "tail"))]
    # 手 / 前臂 到 腿轴 的最小距离（穿模余量基准）
    hand_pts = []
    for name in ARM_BONES:
        h = Vector(A.bone_world(arm, name, "head"))
        t = Vector(A.bone_world(arm, name, "tail"))
        for i in range(9):
            hand_pts.append(h.lerp(t, i / 8.0))
    legs = {}
    for side in SIDES:
        legs[side] = [(Vector(A.bone_world(arm, "thigh." + side, "head")),
                       Vector(A.bone_world(arm, "thigh." + side, "tail")),
                       0.105),
                      (Vector(A.bone_world(arm, "shin." + side, "head")),
                       Vector(A.bone_world(arm, "shin." + side, "tail")),
                       0.095)]
    worst = 1e9
    for p in hand_pts:
        for side in SIDES:
            for a, b, r in legs[side]:
                ab = b - a
                t = 0.0 if ab.length_squared < 1e-12 else max(
                    0.0, min(1.0, (p - a).dot(ab) / ab.length_squared))
                d = (p - (a + ab * t)).length - r
                worst = min(worst, d)
    row["arm_leg_clearance_mm"] = round(worst * 1000.0, 2)
    return row


def leg_radius(meshes):
    """量小腿 / 大腿的等效半径（绕骨轴的最大水平径向距离），给穿模判据定半径。"""
    dg = bpy.context.evaluated_depsgraph_get()
    out = {"thigh_L": 0.0, "shin_L": 0.0}
    for obj in meshes:
        if obj.name not in ("Trouser_L", "Trouser_R"):
            continue
        ev = obj.evaluated_get(dg)
        me = ev.to_mesh()
        mw = ev.matrix_world
        for v in me.vertices:
            p = mw @ v.co
            if p.z > 0.60:
                axis = Vector((p.x, p.y, 0.0))
            else:
                axis = Vector((p.x, p.y, 0.0))
            r = math.hypot(p.x - 0.086, p.y)
            key = "thigh_L" if p.z > 0.60 else "shin_L"
            out[key] = max(out[key], r)
        ev.to_mesh_clear()
    return {k: round(v * 1000.0, 2) for k, v in out.items()}


def main():  # noqa: C901
    arm, meshes = A.open_animation_project()
    A.setup_scene()
    scene = bpy.context.scene
    out = {}

    base = IDLE.idle_pose(arm, 0.0)
    A.apply_pose(arm, base)
    anchor = _ankles(arm)
    out["anchor_ankle_mm"] = {s: [round(v * 1000.0, 3) for v in anchor[s]]
                              for s in SIDES}
    out["base_pelvis_z_mm"] = round(
        Vector(A.bone_world(arm, "pelvis", "head")).z * 1000.0, 3)

    # ---------------- (a) 上游两个候选 -----------------------------------
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

    f_idle, m_idle = snapshot("Idle_01", 0)
    f_stun, m_stun = snapshot("Stun", None)
    worst_pos, worst_elem, at = 0.0, 0.0, None
    for name in m_idle:
        if name not in m_stun:
            continue
        pos = (m_idle[name].translation - m_stun[name].translation).length * 1000.0
        if pos > worst_pos:
            worst_pos, at = pos, name
        for r in range(4):
            for c in range(4):
                worst_elem = max(worst_elem,
                                 abs(m_idle[name][r][c] - m_stun[name][r][c]))
    out["upstream"] = {
        "Idle_01@0_vs_Stun@end": {
            "stun_end_frame": f_stun,
            "worst_bone_pos_mm": round(worst_pos, 9),
            "worst_elem": worst_elem, "at": at},
        "note": ("★ 复核 E01 的结论。若 pos/elem 皆为 0（或 ~1e-16），"
                 "则两个接缝候选**代价完全相等** ⟹ 只能按语义选。"),
    }
    out["head_tail_idle0_mm"] = [round(v * 1000.0, 3) for v in
                                 Vector(A.bone_world(arm, "head", "tail"))]

    # ---------------- (b)(c) 弯腰网格 ------------------------------------
    grid = []
    knees = {}
    for drop in DROPS:
        for scale in BEND_SCALES:
            row = measure(arm, base, anchor, drop, scale)
            grid.append(row)
    out["bend_grid"] = grid
    out["bend_grid_note"] = (
        "★ (c) 臂链（upperarm+forearm+hand = 0.650 m）vs 肩→膝距离 = "
        "`reach_ratio_*`。**ratio > 1 = 够不到** ⟹ 加大 drop 或 bend_scale，"
        "不许硬拉肩膀。(d) `arm_leg_clearance_mm` = 臂骨采样点到腿胶囊面的最小外距"
        "（正 = 有间隙，负 = 已穿模）。")

    # ---------------- (b2) 膝盖随「呼吸高度调制」走多少 -------------------
    # 直接量 ±3 mm 骨盆升降下膝盖的位移
    kset = []
    for drop in (-0.120, -0.117, -0.123):
        pose = bent_pose(arm, base, drop, 1.0)
        lock_feet(arm, pose, anchor)
        A.apply_pose(arm, pose)
        kset.append(Vector(A.bone_world(arm, "shin.L", "head")))
    out["knee_motion_per_3mm_pelvis_mm"] = round(
        max((k - kset[0]).length for k in kset) * 1000.0, 4)
    out["knee_motion_note"] = (
        "★ 呼吸让骨盆升降 ±3 mm 时，**膝盖跟着走多少** —— 这就是「动目标」的幅度，"
        "也是 `exh_hand_on_knee_ok` 的阈值下限来源（手要跟得住它）。")

    # ---------------- (d2) 腿半径 + 衣摆盒 ---------------------------------
    out["leg_radius_mm"] = leg_radius(meshes)
    out["hem_box_mm"] = {"x": [-188.78, 188.78], "z": [897.5, 926.0],
                         "source": "probe_c11_belt（E01 已实测逐帧恒定）"}

    # ---------------- (e) 周期预算 ---------------------------------------
    out["period_budget"] = [
        {"cycles_in_hold": c, "frames_per_cycle": int(round(hold / c))}
        for hold, c in ((70, 2.0), (80, 2.0), (90, 2.0), (80, 3.0))]

    # ---------------- (f) 弯身姿态出图（正面 + 侧视）----------------------
    if os.environ.get("E02_RENDER") == "1":
        from mathutils import Vector as _V  # noqa: F401
        pose = bent_pose(arm, base, -0.120, 1.0)
        lock_feet(arm, pose, anchor)
        A.apply_pose(arm, pose)
        cam = bpy.data.objects.get("Presentation_Camera")
        for tag, view in (("front", A.VIEW_FRONT), ("side", A.VIEW_SIDE)):
            name, loc, tgt, scale, res = view
            A.render_still(cam,
                           os.path.join(A.PREVIEW_DIR, "_e02_probe_%s.png" % tag),
                           loc, tgt, scale, res)

    A.report("E02_BASE", out)


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("E02_BASE_FAILURE " + traceback.format_exc())
