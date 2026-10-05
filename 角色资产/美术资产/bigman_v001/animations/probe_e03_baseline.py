"""probe_e03_baseline —— E03 `Rage` 狂暴 的**开工第一件测量**（只读，不改工程）。

计划 §4 第 3 步要求实测（**不许照抄 E01 / E02 的结论**）：

  (a) 上游姿态：`Idle_01@0` vs `Stun@末帧` vs `Exhausted@0` —— 逐骨世界矩阵差。
      ★ E02 已实测前两者差 0.000258 mm ⟹ 代价相等，只能按语义选。本探针**复核**。
  (b) ★★★ 「胸」在世界坐标里是一片多大的曲面（`Suit_Torso` 全网格实测）
      —— 本支「捶胸」的**目标几何**，决定 `rage_chest_hit_ok` 的可达阈值。
  (c) ★★ 臂链能不能打到自己的胸（`upperarm+forearm+hand` = 0.650 vs 肩→胸距离）。
  (d) ★★ `neck` / `head` 后仰的**分配表** —— 哪个角度下巴不顶锁骨、脖不折断；
      并给出「仰头角」的两种量法（相对 chest 法 / 相对世界竖直法）。
  (e) ★ 躯干**翻转**（前倾→后仰）时的峰值角速度余量 —— 定包络与 `no_teleport`。
  (f) ★ 正面机位下「捶胸」与「仰头」怎么读（渲对照图）。

用法：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python probe_e03_baseline.py
    E03_RENDER=1  额外渲正面 / 侧视对照图（仰头 + 捶胸 两个姿态）
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
ARM_LEN_UP = 0.328
ARM_LEN_LO = 0.224 + 0.098
ARM_TOTAL = ARM_LEN_UP + ARM_LEN_LO

TORSO_MESH = "Suit_Torso"
CHIN_MESHES = ("Head", "Lower_Lip", "Mouth_Line", "Nose")
CHEST_NEIGHBOR = ("Suit_Torso", "Neck", "Jacket_Collar", "Shirt_Collar",
                  "Jacket_Lapel_L", "Jacket_Lapel_R")

LEG_ITER = 8
LEG_DAMP = 0.85
THIGH_RZ_GAIN = 1.0 / 0.01309


def lock_feet(arm, pose, want):
    """照抄 `anim_exhausted.lock_feet`（闭环数值修正；planar IK + thigh.rz 配平 x）。"""
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
            err = Vector(A.bone_world(arm, "foot." + side, "head")) - want[side]
            tgt[side] = tgt[side] - err * LEG_DAMP
            rz[side] = rz[side] + THIGH_RZ_GAIN * err.x * LEG_DAMP
            worst = max(worst, err.length * 1000.0)
    return worst


def mesh_points(name, step=1):
    dg = bpy.context.evaluated_depsgraph_get()
    obj = bpy.data.objects.get(name)
    if obj is None:
        return []
    ev = obj.evaluated_get(dg)
    me = ev.to_mesh()
    mw = ev.matrix_world
    pts = [mw @ me.vertices[i].co for i in range(0, len(me.vertices), step)]
    ev.to_mesh_clear()
    return pts


def dist_to_segment(p, a, b):
    ab = b - a
    t = 0.0 if ab.length_squared < 1e-12 else max(
        0.0, min(1.0, (p - a).dot(ab) / ab.length_squared))
    return (p - (a + ab * t)).length


def main():  # noqa: C901
    arm, meshes = A.open_animation_project()
    A.setup_scene()
    scene = bpy.context.scene
    out = {}

    base = IDLE.idle_pose(arm, 0.0)
    A.apply_pose(arm, base)
    anchor = {s: Vector(A.bone_world(arm, "foot." + s, "head")) for s in SIDES}
    out["anchor_ankle_mm"] = {s: [round(v * 1000.0, 3) for v in anchor[s]]
                              for s in SIDES}
    out["base_pelvis_z_mm"] = round(
        Vector(A.bone_world(arm, "pelvis", "head")).z * 1000.0, 3)

    # ---------------- (a) 上游三个候选 -----------------------------------
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
            pos = (m_a[name].translation - m_b[name].translation).length * 1000.0
            if pos > wp:
                wp, at = pos, name
            for r in range(4):
                for c in range(4):
                    we = max(we, abs(m_a[name][r][c] - m_b[name][r][c]))
        return round(wp, 9), we, at

    f_idle, m_idle = snapshot("Idle_01", 0)
    f_stun, m_stun = snapshot("Stun", None)
    f_exh0, m_exh0 = snapshot("Exhausted", 0)
    f_exhN, m_exhN = snapshot("Exhausted", None)
    out["upstream"] = {
        "Stun@end_frame": f_stun,
        "Exhausted@0_frame": f_exh0,
        "Exhausted@end_frame": f_exhN,
        "Idle_01@0_vs_Stun@end": diff(m_idle, m_stun),
        "Idle_01@0_vs_Exhausted@0": diff(m_idle, m_exh0),
        "Idle_01@0_vs_Exhausted@end": diff(m_idle, m_exhN),
        "note": "★ 三项若全 ~0 ⟹ 所有候选代价相等，只能按语义选 `Idle_01@0`。",
    }

    # ---------------- (b) 胸几何（Suit_Torso 全网格实测，idle 站架下）------
    A.apply_pose(arm, base)
    chest_head = Vector(A.bone_world(arm, "chest", "head"))
    chest_tail = Vector(A.bone_world(arm, "chest", "tail"))
    neck_head = Vector(A.bone_world(arm, "neck", "head"))
    torso = mesh_points(TORSO_MESH, 1)
    zlo, zhi = 1.02, 1.30
    band = [p for p in torso if zlo <= p.z <= zhi]
    front = min(band, key=lambda p: p.y) if band else None
    center = [p for p in band if abs(p.x) < 0.06]
    front_c = min(center, key=lambda p: p.y) if center else front
    radius = max(dist_to_segment(p, chest_head, neck_head) for p in band)
    out["chest_geom_mm"] = {
        "chest_head": [round(v * 1000.0, 2) for v in chest_head],
        "chest_tail": [round(v * 1000.0, 2) for v in chest_tail],
        "neck_head": [round(v * 1000.0, 2) for v in neck_head],
        "band_z": [zlo, zhi],
        "band_vert_n": len(band),
        "front_all": [round(v * 1000.0, 2) for v in front] if front else None,
        "front_center": ([round(v * 1000.0, 2) for v in front_c]
                         if front_c else None),
        "chest_axis_radius_mm": round(radius * 1000.0, 2),
        "note": ("★ front_center = 胸带内 |x|<60 mm 的最前（−Y）顶点 = **胸口表面**；"
                 "chest_axis_radius = 该带内所有躯干顶点到胸轴（chest.head→neck.head）"
                 "的最大距离 = **躯干等效半径**（捶胸目标与不穿模判据都用它）。"),
    }
    # 前法线（胸带内最前点的外法，用 axis→point 方向近似）
    if front_c is not None:
        axis_pt = chest_head.lerp(neck_head, 0.5)
        nrm = (front_c - axis_pt)
        nrm.z = 0.0
        nrm = nrm.normalized() if nrm.length > 1e-6 else Vector((0, -1, 0))
        out["chest_front_normal"] = [round(v, 4) for v in nrm]
        # 拳心应落在 表面 + 法线*(拳半径+余隙) —— 拳半径按掌网格半宽估
        palm = mesh_points("Hand_Palm_L", 1)
        fist_r = 0.5 * max(
            (Vector((p.x, p.y, 0.0)) - Vector((0.15, -0.35, 0.0))).length
            for p in palm) if palm else 0.05
        out["fist_radius_mm_est"] = round(fist_r * 1000.0, 2)

    # ---------------- (c) 臂链可达性 --------------------------------------
    # 目标点：双侧胸口表面（x = ±0.13 处的表面点，用带内最前点代替）
    tgt_c = front_c if front_c is not None else Vector((0.0, -0.25, 1.15))
    row = {}
    for side in SIDES:
        sh = Vector(A.bone_world(arm, "upperarm." + side, "head"))
        d = (tgt_c - sh).length
        row["shoulder_" + side] = [round(v * 1000.0, 2) for v in sh]
        row["shoulder_to_chest_mm_" + side] = round(d * 1000.0, 2)
        row["reach_ratio_" + side] = round(d / (ARM_TOTAL * 0.9995), 4)
    out["arm_reach"] = row
    out["arm_reach_note"] = (
        "★ ratio ≤ 1 = 手能够到自己的胸口（肘微屈即可，越远越绷）。"
        "捶胸是**短距离自接触**，必然可达 —— 关键不是够不够，是**别顶穿**。")

    # ---------------- (d) neck / head 后仰分配表 --------------------------
    # ★ 与 E02 的穿模同一族：这里量「下巴是否顶到锁骨」。
    grid = []
    for nrx in (0.0, -6.0, -12.0, -18.0, -24.0, -30.0):
        for hrx in (0.0, -6.0, -12.0, -18.0, -24.0, -30.0, -36.0):
            pose = {}
            for key, value in base.items():
                pose[key] = (tuple(value) if not key.startswith("@")
                             else {k: tuple(v) for k, v in value.items()})
            n0 = pose.get("neck", (0.0, 0.0, 0.0))[0]
            h0 = pose.get("head", (0.0, 0.0, 0.0))[0]
            pose["neck"] = (n0 + nrx, 0.0, 0.0)
            pose["head"] = (h0 + hrx, 0.0, 0.0)
            A.apply_pose(arm, pose)
            head_dir = A.bone_direction(arm, "head")
            chest_dir = A.bone_direction(arm, "chest")
            # 仰头角 = 头轴相对胸轴在 YZ 平面内的夹角（正 = 后仰 / 朝上）
            def yz(v):
                return math.atan2(-v.y, v.z)          # 前(−Y)为 0，上为 +90°
            back = math.degrees(yz(head_dir) - yz(chest_dir))
            vert = math.degrees(yz(head_dir) - yz(Vector((0.0, 0.0, 1.0))))
            chin = mesh_points("Lower_Lip", 1) + mesh_points("Mouth_Line", 1)
            near = []
            for nm in CHEST_NEIGHBOR:
                near += mesh_points(nm, 3)
            dmin = min((c - n).length for c in chin for n in near) \
                if chin and near else None
            grid.append({
                "neck_rx": round(n0 + nrx, 2), "head_rx": round(h0 + hrx, 2),
                "add_n": nrx, "add_h": hrx,
                "head_back_vs_chest_deg": round(back, 2),
                "head_vs_vertical_deg": round(vert, 2),
                "head_tail_z_mm": round(Vector(A.bone_world(arm, "head",
                                                            "tail")).z * 1000, 1),
                "chin_clearance_mm": (round(dmin * 1000.0, 2)
                                      if dmin is not None else None),
            })
    out["neck_head_grid"] = grid
    out["neck_head_note"] = (
        "★ `head_back_vs_chest_deg` = 仰头角（本支 `rage_head_back_ok` 的载体）；"
        "`chin_clearance_mm` = 下巴/嘴到胸颈衣物最近面距（≈0 = 下巴顶锁骨）。"
        "**两端都卡**：太小=没仰；太大=断颈 / 下巴顶锁骨。")

    # ---------------- (e) 躯干翻转角速度余量 ------------------------------
    out["flip_budget"] = [
        {"swing_deg": s, "frames": f, "deg_per_frame": round(s / f, 3),
         "ok_under_25": bool(s / f <= 25.0)}
        for s, f in ((40, 8), (50, 8), (60, 8), (60, 10), (70, 12))
    ]

    # ---------------- (f) 出图对照 ----------------------------------------
    if os.environ.get("E03_RENDER") == "1":
        cam = bpy.data.objects.get("Presentation_Camera")
        # ★★ 必须先解绑 Action：上面 (a) 的快照把 `Exhausted` 绑了回去，
        #    否则渲染出来的是**那条 action 在当前帧的姿态**，我摆的姿势被静默覆盖
        #    —— 首次跑出来的四张图 roar/chest 逐像素相同就是这个原因。
        if arm.animation_data is not None:
            arm.animation_data.action = None
        pose = {}
        for key, value in base.items():
            pose[key] = (tuple(value) if not key.startswith("@")
                         else {k: tuple(v) for k, v in value.items()})
        pose["neck"] = (base.get("neck", (0, 0, 0))[0] - 18.0, 0.0, 0.0)
        pose["head"] = (base.get("head", (0, 0, 0))[0] - 24.0, 0.0, 0.0)
        A.apply_pose(arm, pose)
        for tag, view in (("front", A.VIEW_FRONT), ("side", A.VIEW_SIDE)):
            name, loc, tgt, scale, res = view
            A.render_still(cam, os.path.join(A.PREVIEW_DIR,
                                             "_e03_probe_roar_%s.png" % tag),
                           loc, tgt, scale, res)
        # 捶胸姿态：双拳外张 → 用站架臂方向硬摆两拳到胸口
        pose2 = {}
        for key, value in base.items():
            pose2[key] = (tuple(value) if not key.startswith("@")
                          else {k: tuple(v) for k, v in value.items()})
        A.apply_pose(arm, pose2)
        for side in SIDES:
            up, fo, hd = ("upperarm." + side, "forearm." + side, "hand." + side)
            tgt2 = Vector((0.13 if side == "L" else -0.13,
                           tgt_c.y - 0.05, tgt_c.z))
            sh = Vector(A.bone_world(arm, up, "head"))
            delta = tgt2 - sh
            pose2[up] = A.aim_bone(arm, up, delta.normalized())
            A.apply_pose(arm, pose2)
            elbow = Vector(A.bone_world(arm, up, "tail"))
            pose2[fo] = A.aim_bone(arm, fo, (tgt2 - elbow))
            A.apply_pose(arm, pose2)
            pose2[hd] = A.aim_bone(arm, hd, (tgt2 - elbow))
            A.apply_pose(arm, pose2)
        for tag, view in (("front", A.VIEW_FRONT), ("side", A.VIEW_SIDE)):
            name, loc, tgt, scale, res = view
            A.render_still(cam, os.path.join(A.PREVIEW_DIR,
                                             "_e03_probe_chest_%s.png" % tag),
                           loc, tgt, scale, res)

    A.report("E03_BASE", out)


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("E03_BASE_FAILURE " + traceback.format_exc())
