"""probe_e04_baseline —— E04 `Spawn` 入场 的**开工第一件测量**（只读，不改工程）。

清单 §「E04 详细计划」§4 第 3 步要求实测（**不许照抄 E01 / E02 / E03 的结论**）：

  (a) 上游姿态：`Idle_01@0` vs `Stun@末帧` vs `Exhausted@0` vs `Rage@末帧`
      —— 逐骨世界矩阵差。E01/E02/E03 三次实测都在 1e-4 mm 量级（float32 噪声）
      ⟹ 代价相等，只能按语义选。本探针**第四次复核**，并确认 `Rage` 末帧是否
      也逐位等于 `Idle_01@0`（若是，则整条 E 族接缝链只有一个锚，更干净）。
  (b) ★★★ **落地几何**（`spawn_land_sink_ok` 的可达阈值来源）：
      站架骨盆 z、髋↔踝距离、腿长上限、**膝屈到极限时骨盆能下沉多少**。
  (c) ★★ **起跳上界**（`spawn_root_motion_ok` 的可达阈值来源）：
      脚钉在地面时**腿完全伸展**能把骨盆顶到多高 = 原地起跳的物理上限。
  (d) ★★ **脚离地判据**：给定踝抬升量 δ 时 `sole_min_z` 实测值
      ⟹ 定 `spawn_airborne_ok` 的阈值与 `TAKEOFF` / `LAND` 的自动帧号规则。
  (e) ★ 起跳 / 落地的**峰值角速度余量** —— 定包络与 `no_teleport`（≤25°/帧）。
  (f) ★ 落地机位下「冲击感」怎么读（全网格包络 → 取景参数）。

用法：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python probe_e04_baseline.py
    E04_RENDER=1  额外渲 深蹲 / 腾空顶 / 落地冲击 三个姿态的侧视对照图
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
LEG_ITER = 8
LEG_DAMP = 0.85
THIGH_RZ_GAIN = 1.0 / 0.01309


# =============================================================== 脚锁（照抄主脚本口径）
def lock_feet(arm, pose, want):
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


def build(arm, base, anchor, dz=0.0, dy=0.0, tilts=None,
          foot_lift=0.0, foot_dy=0.0):
    """在站架上叠躯干规格 + 骨盆位移 + 踝目标抬升，返回 (pose, lock_err)。"""
    pose = {}
    for key, value in base.items():
        pose[key] = ({k: tuple(v) for k, v in value.items()}
                     if key.startswith("@") else tuple(value))
    for name, delta in (tilts or {}).items():
        cur = pose.get(name, (0.0, 0.0, 0.0))
        pose[name] = (cur[0] + delta, cur[1], cur[2])
    base_loc = pose.get("@loc", {}).get("pelvis", (0.0, 0.0, 0.0))
    off = A.wloc(0.0, dy, dz)
    pose["@loc"] = {"pelvis": tuple(a + b for a, b in zip(base_loc, off))}
    want = {s: Vector(anchor[s]) + Vector((0.0, foot_dy, foot_lift))
            for s in SIDES}
    err = lock_feet(arm, pose, want)
    return pose, err


def mesh_box():
    """全网格世界包围盒（解算后）。"""
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


def knee_deg(arm):
    return {s: math.degrees(arm.pose.bones["shin." + s].rotation_euler.x)
            for s in SIDES}


def main():  # noqa: C901
    arm, meshes = A.open_animation_project()
    A.setup_scene()
    scene = bpy.context.scene
    out = {}

    base = IDLE.idle_pose(arm, 0.0)
    A.apply_pose(arm, base)
    anchor = {s: Vector(A.bone_world(arm, "foot." + s, "head")) for s in SIDES}
    out["rig_consts"] = {
        "L_THIGH": A.L_THIGH, "L_SHIN": A.L_SHIN,
        "LEG_SUM": A.L_THIGH + A.L_SHIN,
        "Z_ANKLE_REST": A.Z_ANKLE_REST, "HIP_X": A.HIP_X,
        "ANKLE_X_REST": A.ANKLE_X_REST,
        "anchor_ankle_mm": {s: [round(v * 1000.0, 3) for v in anchor[s]]
                            for s in SIDES},
        "base_pelvis_z_mm": round(
            Vector(A.bone_world(arm, "pelvis", "head")).z * 1000.0, 3),
    }
    hip0 = {s: Vector(A.bone_world(arm, "thigh." + s, "head")) for s in SIDES}
    out["station_hip_ankle_mm"] = {
        s: round((hip0[s] - anchor[s]).length * 1000.0, 3) for s in SIDES}
    out["station_knee_deg"] = {s: round(v, 2)
                               for s, v in knee_deg(arm).items()}
    out["leg_slack_mm"] = round(
        ((A.L_THIGH + A.L_SHIN) - (hip0["L"] - anchor["L"]).length) * 1000.0, 3)

    # ---------------- (a) 上游四个候选 -----------------------------------
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
    f_stun, m_stun = snapshot("Stun", None)
    f_exh0, m_exh0 = snapshot("Exhausted", 0)
    f_exhN, m_exhN = snapshot("Exhausted", None)
    f_rage, m_rage = snapshot("Rage", None)
    up = {
        "Stun@end_frame": f_stun,
        "Exhausted@0_frame": f_exh0,
        "Exhausted@end_frame": f_exhN,
        "Rage@end_frame": f_rage,
        "Idle_01@0_vs_Stun@end": diff(m_idle, m_stun),
        "Idle_01@0_vs_Exhausted@0": diff(m_idle, m_exh0),
        "Idle_01@0_vs_Exhausted@end": diff(m_idle, m_exhN),
        "Idle_01@0_vs_Rage@end": diff(m_idle, m_rage),
    }
    up["note"] = ("★ 四项若全 ~0 ⟹ 所有候选代价相等（float32 噪声），只能按语义选"
                  " `Idle_01@0`。★ 若 `Rage@end` 也 ~0，说明整条 E 族只有一个锚。")
    out["upstream"] = up

    # ---------------- (b) 下沉可达性 --------------------------------------
    A.apply_pose(arm, base)
    sink = []
    dz = 0.0
    while dz >= -0.42:
        pose, err = build(arm, base, anchor, dz=dz)
        lo, _hi = mesh_box()
        sink.append({"dz_mm": round(dz * 1000.0, 1),
                     "lock_err_mm": round(err, 4),
                     "knee_deg": round(max(knee_deg(arm).values()), 2),
                     "sole_min_mm": round(lo[2] * 1000.0, 2),
                     "pelvis_z_mm": round(Vector(A.bone_world(
                         arm, "pelvis", "head")).z * 1000.0, 2)})
        dz -= 0.01
    out["sink_scan"] = sink
    ok_sink = [r for r in sink if r["lock_err_mm"] <= 0.5 and r["sole_min_mm"] >= -2.0]
    out["sink_max_mm"] = (min(r["dz_mm"] for r in ok_sink)
                          if ok_sink else None)

    # ---------------- (c) 起跳上界（脚钉地、腿伸展）------------------------
    rise = []
    dz = 0.0
    while dz <= 0.20:
        pose, err = build(arm, base, anchor, dz=dz,
                          tilts={"pelvis": -1.0, "spine_01": -1.0,
                                 "spine_02": -1.0, "chest": -1.0})
        lo, _hi = mesh_box()
        rise.append({"dz_mm": round(dz * 1000.0, 1),
                     "lock_err_mm": round(err, 4),
                     "knee_deg": round(max(knee_deg(arm).values()), 2),
                     "sole_min_mm": round(lo[2] * 1000.0, 2),
                     "hip_ankle_mm": round((Vector(A.bone_world(
                         arm, "thigh.L", "head"))
                         - Vector(A.bone_world(arm, "foot.L", "head"))).length
                         * 1000.0, 2)})
        dz += 0.01
    out["rise_scan"] = rise
    ok_rise = [r for r in rise if r["lock_err_mm"] <= 0.5]
    out["rise_max_mm"] = (max(r["dz_mm"] for r in ok_rise)
                          if ok_rise else None)
    out["rise_note"] = ("★ 脚**钉在地面**时腿完全伸展能把骨盆顶到的最高点 = "
                        "**原地起跳的物理上限**。腾空段可以超过它（脚已离地）。")

    # ---------------- (d) 踝抬升量 → sole_min_z ---------------------------
    lift_rows = []
    for lift in (0.0, 0.02, 0.05, 0.10, 0.20, 0.30, 0.42, 0.50, 0.60):
        pose, err = build(arm, base, anchor, dz=lift, foot_lift=lift)
        lo, _hi = mesh_box()
        lift_rows.append({"lift_mm": round(lift * 1000.0, 1),
                          "dz_mm": round(lift * 1000.0, 1),
                          "lock_err_mm": round(err, 4),
                          "sole_min_mm": round(lo[2] * 1000.0, 2),
                          "hip_ankle_mm": round((Vector(A.bone_world(
                              arm, "thigh.L", "head"))
                              - Vector(A.bone_world(
                                  arm, "foot.L", "head"))).length
                              * 1000.0, 2)})
    out["lift_scan"] = lift_rows
    out["lift_note"] = ("★ 本表 = 「踝目标随体抬升 δ、骨盆同步抬 δ」时的 `sole_min_z`"
                        "（全网格最低点）⟹ 直接给出 `spawn_airborne_ok` 的阈值："
                        "δ 多大时脚真的离地、离多少。")

    # ---------------- (e) 角速度余量 --------------------------------------
    out["rate_budget"] = [
        {"swing_deg": s, "frames": f, "deg_per_frame": round(s / f, 3),
         "ok_under_25": bool(s / f <= 25.0)}
        for s, f in ((30, 6), (40, 6), (50, 8), (60, 10), (70, 12), (80, 14))
    ]

    # ---------------- (f) 三个代表姿态的包络 + 取景 ------------------------
    envelope = {}
    for tag, kwargs in (
            ("station", {}),
            ("crouch", {"dz": -0.16, "tilts": {"pelvis": 14.0, "spine_01": 7.0,
                                               "spine_02": 7.0, "chest": 5.0,
                                               "neck": 6.0, "head": 5.0}}),
            ("apex", {"dz": 0.42, "foot_lift": 0.42, "foot_dy": 0.05,
                      "tilts": {"pelvis": -4.0, "spine_01": -3.0,
                                "spine_02": -3.0, "chest": -4.0}}),
            ("land", {"dz": -0.20, "tilts": {"pelvis": 12.0, "spine_01": 6.0,
                                             "spine_02": 6.0, "chest": 4.0,
                                             "neck": 4.0, "head": 3.0}})):
        pose, err = build(arm, base, anchor, **kwargs)
        lo, hi = mesh_box()
        envelope[tag] = {
            "bbox_mm": [[round(v * 1000.0, 1) for v in lo],
                        [round(v * 1000.0, 1) for v in hi]],
            "lock_err_mm": round(err, 4),
            "knee_deg": round(max(knee_deg(arm).values()), 2),
        }
    out["envelope"] = envelope
    out["view_note"] = ("★ 侧视取景必须同时装下 深蹲(低) 与 腾空(高)："
                        "z 跨度 = 0 ~ (apex 头顶)。**不许照抄 E01~E03**。")

    # ---------------- (g) 出图对照 ----------------------------------------
    if os.environ.get("E04_RENDER") == "1":
        cam = bpy.data.objects.get("Presentation_Camera")
        if arm.animation_data is not None:
            arm.animation_data.action = None
        for tag, kwargs in (
                ("crouch", {"dz": -0.16,
                            "tilts": {"pelvis": 14.0, "spine_01": 7.0,
                                      "spine_02": 7.0, "chest": 5.0}}),
                ("apex", {"dz": 0.42, "foot_lift": 0.42, "foot_dy": 0.05,
                          "tilts": {"pelvis": -4.0, "spine_01": -3.0,
                                    "spine_02": -3.0, "chest": -4.0}}),
                ("land", {"dz": -0.20,
                          "tilts": {"pelvis": 12.0, "spine_01": 6.0,
                                    "spine_02": 6.0, "chest": 4.0}})):
            pose, _err = build(arm, base, anchor, **kwargs)
            A.apply_pose(arm, pose)
            A.render_still(cam, os.path.join(
                A.PREVIEW_DIR, "_e04_probe_%s_side.png" % tag),
                (4.6, -0.10, 1.10), (0.0, -0.10, 1.10), 2.60, (780, 1100))

    A.report("E04_BASE", out)


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("E04_BASE_FAILURE " + traceback.format_exc())
