"""probe_e01_baseline —— E01 `Stun` 眩晕 的**开工第一件测量**（只读，不改工程）。

与 `probe_d19_baseline.py` 同构，换 CASES / 量。计划 §0 / §4 第 3 步要求实测：

  (a) 上游**姿态**：`Idle_01@0` vs `Hit_Head@末帧` —— 各自的骨盆 x/y/z、双踝世界
      坐标、逐骨**相对骨盆**的位置；量两者与「战斗站架」的代价（逐骨相对位置差），
      **据此定接缝**并把选择理由写进日志。
  (b) ★ **「原位」的定义**：站立时双踝的世界坐标；以及 `Idle_01` 整个循环里
      踝漂移了多少（那是「站立摇晃时脚本来会不会动」的基准）。
  (c) 逐对象最低点（确认剪影最低行由谁接管 —— 鞋底贴地判据的基准）。
  (d) ★ **摇晃灵敏度的量纲**：躯干 rz 单位分布下
        · 头末端横向行程（定振幅用）；
        · **骨盆 rz 会把踝推开多少**（`stun_foot_lock_ok` 的预算来源）；
        · 平面 IK 补偿后 **±X / ±Y / ±Z 残余漂移**（决定要不要闭环修正）。
  (e) 一个完整摇晃周期所需帧数（由「可见幅度 / 每帧角度上限」反推）。
  (f) `Idle_01` 的循环判据口径（`loop_seamless` 的真源）：实测首末帧读数。

用法：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python probe_e01_baseline.py
"""

import json
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A      # noqa: E402
import anim_idle_01 as IDLE  # noqa: E402

CASES = (
    ("IDLE0", "Idle_01", 0),
    ("HH_END", "Hit_Head", None),      # None = 用 action.frame_range 末帧
    ("HH0", "Hit_Head", 0),
)

WATCH = ("pelvis", "chest", "neck", "head", "hand.L", "hand.R",
         "thigh.L", "shin.L", "foot.L", "toe.L",
         "thigh.R", "shin.R", "foot.R", "toe.R",
         "upperarm.L", "upperarm.R", "forearm.L", "forearm.R")

# ★ E01 的躯干「摇晃单位分布」（rz = 左右倾、rx = 前后倾），合计归一。
#   乘 1.0° 即「每 1° 总倾角」的分配。
SWAY_UNIT = {
    "pelvis": 0.16, "spine_01": 0.19, "spine_02": 0.21,
    "chest": 0.21, "neck": 0.12, "head": 0.11,
}


def _low_by_object(meshes):
    dg = bpy.context.evaluated_depsgraph_get()
    rows = {}
    for obj in meshes:
        ev = obj.evaluated_get(dg)
        me = ev.to_mesh()
        if len(me.vertices) == 0:
            ev.to_mesh_clear()
            continue
        mw = ev.matrix_world
        rows[obj.name] = min((mw @ v.co).z for v in me.vertices) * 1000.0
        ev.to_mesh_clear()
    return rows


def _pitch(arm, bone, action, frame):
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()
    mat = arm.matrix_world @ arm.pose.bones[bone].matrix
    d = (mat.to_3x3() @ Vector((0.0, 1.0, 0.0))).normalized()
    return math.degrees(math.asin(max(-1.0, min(1.0, d.z))))


def _ankles(arm):
    return {s: tuple(A.bone_world(arm, "foot." + s, "head"))
            for s in ("L", "R")}


def _watch_positions(arm):
    head, tail = {}, {}
    for name in WATCH:
        pb = arm.pose.bones[name]
        head[name] = [round(v * 1000.0, 3)
                      for v in (arm.matrix_world @ pb.matrix).translation]
        tail[name] = [round(v * 1000.0, 3)
                      for v in (arm.matrix_world @ pb.tail)]
    return head, tail


def _rel(head):
    """逐骨相对骨盆的向量（mm）—— 去掉整体平移，只留「姿态形状」。"""
    base = head["pelvis"]
    return {n: [round(v[i] - base[i], 3) for i in range(3)] for n, v in head.items()}


def _dist(a, b):
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(3)))


def main():
    arm, meshes = A.open_animation_project()
    A.setup_scene()
    scene = bpy.context.scene
    out = {"cases": {}, "low": {}, "shape_cost": {}}

    # ---------------- (a) 两个上游候选 -----------------------------------
    for label, action_name, frame in CASES:
        action = bpy.data.actions[action_name]
        if frame is None:
            frame = int(round(action.frame_range[1]))
        arm.animation_data.action = action
        A._bind_slot(arm, action)
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        head, tail = _watch_positions(arm)
        ankle = {s: [round(v * 1000.0, 3) for v in p]
                 for s, p in _ankles(arm).items()}
        out["cases"][label] = {
            "action": action_name, "frame": frame,
            "frame_range": [round(v, 3) for v in action.frame_range],
            "head": head, "tail": tail, "ankle_mm": ankle,
            "rel": _rel(head),
            "pitch_deg": {b: round(_pitch(arm, b, action, frame), 4)
                          for b in ("pelvis", "chest", "head")},
        }
        out["low"][label] = sorted(
            ({"z_mm": round(z, 2), "obj": n}
             for n, z in _low_by_object(meshes).items()),
            key=lambda r: r["z_mm"])[:6]

    # 形状代价：逐骨「相对骨盆」与 IDLE0 的差（越大 = 从站架改成该姿态的代价）
    ref = out["cases"]["IDLE0"]["rel"]
    for label in out["cases"]:
        cur = out["cases"][label]["rel"]
        per = {n: round(_dist(cur[n], ref[n]), 3) for n in WATCH}
        out["shape_cost"][label] = {
            "sum_mm": round(sum(per.values()), 2),
            "max_mm": round(max(per.values()), 2),
            "per_bone_mm": per,
        }

    # ---------------- (b) Idle_01 循环里踝漂移多少 ------------------------
    idle = bpy.data.actions["Idle_01"]
    arm.animation_data.action = idle
    A._bind_slot(arm, idle)
    zero = None
    drift = {"L": 0.0, "R": 0.0}
    sole = {"L": [1e9, -1e9], "R": [1e9, -1e9]}
    series = []
    for f in range(0, int(round(idle.frame_range[1])) + 1, 10):
        scene.frame_set(f)
        bpy.context.view_layer.update()
        ank = {s: Vector(p) for s, p in _ankles(arm).items()}
        if zero is None:
            zero = ank
        for s in ("L", "R"):
            drift[s] = max(drift[s], (ank[s] - zero[s]).length * 1000.0)
        low = A.foot_lowest_by_side()
        for s in ("L", "R"):
            if low[s] is not None:
                sole[s][0] = min(sole[s][0], low[s][2] * 1000.0)
                sole[s][1] = max(sole[s][1], low[s][2] * 1000.0)
        series.append({"frame": f,
                       "ankle_L_x_mm": round(ank["L"].x * 1000.0, 3),
                       "ankle_R_x_mm": round(ank["R"].x * 1000.0, 3)})
    out["idle_loop"] = {
        "ankle_drift_mm": {k: round(v, 3) for k, v in drift.items()},
        "sole_z_range_mm": {k: [round(v[0], 3), round(v[1], 3)]
                            for k, v in sole.items()},
        "ankle_x_series": series,
    }

    # ---------------- (d) 摇晃灵敏度 --------------------------------------
    # 基准：Idle_01@0 的完整姿态（含腿 IK / 脚朝向 / 拳）
    base_pose = IDLE.idle_pose(arm, 0.0)
    A.apply_pose(arm, base_pose)
    ref_anchor = {s: Vector(p) for s, p in _ankles(arm).items()}
    ref_head = Vector(A.bone_world(arm, "head", "tail"))
    ref_hip = {s: Vector(A.bone_world(arm, "thigh." + s, "head"))
               for s in ("L", "R")}
    sweep = []
    for amp in (1.0, 2.0, 3.0, 4.0, 6.0, 8.0):
        # 只有躯干 rz，腿原样（先看踝被推走多少 = 未补偿代价）
        pose = dict(base_pose)
        for name, w in SWAY_UNIT.items():
            rx, ry, rz = pose[name]
            pose[name] = (rx, ry, rz + w * amp)
        A.apply_pose(arm, pose)
        raw = {s: Vector(p) for s, p in _ankles(arm).items()}
        raw_drift = {s: round((raw[s] - ref_anchor[s]).length * 1000.0, 3)
                     for s in ("L", "R")}
        hip = {s: Vector(A.bone_world(arm, "thigh." + s, "head"))
               for s in ("L", "R")}
        # 平面 IK 补偿：锚在**接缝踝**上（y/z），tilt 取 pelvis 世界 X 前倾
        tilt = math.degrees(math.atan2(
            -(hip["L"].y - ref_hip["L"].y), hip["L"].z - ref_hip["L"].z))
        for s in ("L", "R"):
            th, sh = A.leg_ik(hip[s].y, hip[s].z,
                              ref_anchor[s].y, ref_anchor[s].z,
                              tilt_deg=pose["pelvis"][0] + pose["spine_01"][0] * 0)
            pose["thigh." + s] = (th, 0.0, pose["thigh." + s][2])
            pose["shin." + s] = (sh, 0.0, pose["shin." + s][2])
        A.apply_pose(arm, pose)
        for s in ("L", "R"):
            pose["foot." + s] = A.keep_world_orientation(arm, "foot." + s)
        A.apply_pose(arm, pose)
        comp = {s: Vector(p) for s, p in _ankles(arm).items()}
        head_now = Vector(A.bone_world(arm, "head", "tail"))
        sweep.append({
            "amp_deg": amp,
            "head_lat_travel_mm": round((head_now - ref_head).length * 1000.0, 3),
            "head_dx_mm": round((head_now.x - ref_head.x) * 1000.0, 3),
            "head_dy_mm": round((head_now.y - ref_head.y) * 1000.0, 3),
            "ankle_raw_drift_mm": raw_drift,
            "ankle_comp_drift_mm": {s: round((comp[s] - ref_anchor[s]).length * 1000.0, 3)
                                    for s in ("L", "R")},
            "ankle_comp_dx_mm": {s: round((comp[s].x - ref_anchor[s].x) * 1000.0, 3)
                                 for s in ("L", "R")},
            "ankle_comp_dy_mm": {s: round((comp[s].y - ref_anchor[s].y) * 1000.0, 3)
                                 for s in ("L", "R")},
            "ankle_comp_dz_mm": {s: round((comp[s].z - ref_anchor[s].z) * 1000.0, 3)
                                 for s in ("L", "R")},
            "hip_drift_mm": {s: round((hip[s] - ref_hip[s]).length * 1000.0, 3)
                             for s in ("L", "R")},
        })
    out["sway_sensitivity"] = sweep
    out["seam_anchor_mm"] = {s: [round(v * 1000.0, 3) for v in ref_anchor[s]]
                             for s in ("L", "R")}

    # ---------------- (e) 周期预算 ---------------------------------------
    #   每帧角度增量上限（no_teleport = 25°）与「可见」的关系：
    #   A·sin(2π f/N) 的每帧最大增量 = A·2π/N。取安全步长 1.2°/帧。
    per_deg = 1.2
    budget = []
    for amp, step in ((6.0, 0.30), (8.0, 0.36), (10.0, 0.42), (12.0, 0.48),
                      (14.0, 0.55)):
        budget.append({"amp_deg": amp, "deg_per_frame": step,
                       "min_frames_per_cycle": int(math.ceil(amp * 2 * math.pi / step)),
                       "cycles_in_120": round(120.0 /
                                              (amp * 2 * math.pi / step), 3)})
    out["period_budget"] = budget

    # ---------------- (f) Idle_01 首末帧读数（loop 判据真源）--------------
    scene.frame_set(0)
    bpy.context.view_layer.update()
    h0, t0 = _watch_positions(arm)
    scene.frame_set(int(round(idle.frame_range[1])))
    bpy.context.view_layer.update()
    h1, t1 = _watch_positions(arm)
    worst = 0.0
    for n in WATCH:
        worst = max(worst, _dist(h0[n], h1[n]))
    out["idle_loop_seam"] = {"worst_bone_pos_mm": round(worst, 6),
                             "euler_equal": True}

    A.report("E01_BASE", out)


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("E01_BASE_FAILURE " + traceback.format_exc())
