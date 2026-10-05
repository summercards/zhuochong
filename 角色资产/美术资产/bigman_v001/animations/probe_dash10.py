"""probe_dash10 —— B10 `Dash_Attack` 开工前的**先量再做**探针。

要回答四个问题（B10 计划里的四项）：
  1. 上游接缝取 `Run` 的哪一帧？—— 逐帧实测 Run 的骨盆/脚/躯干，找"前冲已起、
     一脚踩实、可以爆发"的那一帧，而不是随手取 f0。
  2. 「前冲惯性」量化成什么？—— 量 Run 的**世界速率**（骨盆在引擎位移下 = 0，
     所以用支撑脚相对身体的后滑速率 = 角色速率）与步态速率。
  3. 肩撞 / 飞膝 / 冲拳 的可达性 —— 量支撑脚的可保窗口与腿长几何上限。
  4. Root Motion 的水平位移上限 —— 单支撑能买多少前进量（= 腿长几何）。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python probe_dash10.py
"""

import json
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A  # noqa: E402
import anim_idle_01 as I1  # noqa: E402
import anim_run as R  # noqa: E402
import anim_walk_f as WF  # noqa: E402


def report(name, payload):
    print("%s %s" % (name, json.dumps(payload, ensure_ascii=False, default=str)))


def run_scan(arm, meshes):
    """逐帧实测 Run：骨盆 / 双脚 / 躯干 / 单帧欧拉步长。"""
    rows = []
    prev_euler = None
    for f in range(0, R.TOTAL + 1):
        pose = WF.gait_pose(arm, R.RUN, f, meshes)
        A.apply_pose(arm, pose)
        pelvis = A.bone_world(arm, "pelvis", "head")
        neck = A.bone_world(arm, "neck", "head")
        fl = A.bone_world(arm, "foot.L", "head")
        fr = A.bone_world(arm, "foot.R", "head")
        hl = A.bone_world(arm, "hand.L", "tail")
        hr = A.bone_world(arm, "hand.R", "tail")
        low = A.foot_lowest_by_side()
        step = 0.0
        step_bone = None
        cur = {b.name: tuple(math.degrees(v)
                             for v in b.rotation_euler)
               for b in arm.pose.bones}
        if prev_euler is not None:
            for name in cur:
                da = max(abs(a - b) for a, b in
                         zip(cur[name], prev_euler.get(name, (0, 0, 0))))
                if da > step:
                    step, step_bone = da, name
        prev_euler = cur
        rows.append({
            "f": f,
            "stance_L": WF.in_stance(R.RUN, f, 0.0),
            "stance_R": WF.in_stance(R.RUN, f, R.RUN.right_offset),
            "pelvis": [round(v * 1000.0, 2) for v in pelvis],
            "lean_mm": round((pelvis.y - neck.y) * 1000.0, 2),
            "ankle_L_yz": [round(fl.y * 1000.0, 2), round(fl.z * 1000.0, 2)],
            "ankle_R_yz": [round(fr.y * 1000.0, 2), round(fr.z * 1000.0, 2)],
            "sole_L_mm": round(low["L"][2] * 1000.0, 2),
            "sole_R_mm": round(low["R"][2] * 1000.0, 2),
            "pelvis_to_ankleL": round(
                (Vector(fl) - Vector(pelvis)).length * 1000.0, 2),
            "pelvis_to_ankleR": round(
                (Vector(fr) - Vector(pelvis)).length * 1000.0, 2),
            "handL": [round(v * 1000.0, 1) for v in hl],
            "handR": [round(v * 1000.0, 1) for v in hr],
            "step_deg": round(step, 2),
            "step_bone": step_bone,
        })
    return rows


def main():
    arm, meshes = A.open_animation_project()
    A.setup_scene()
    if "Idle_01" not in bpy.data.actions:
        I1.main()
        arm, meshes = A.open_animation_project()
        A.setup_scene()

    # ---------- 1) Run 逐帧 ----------
    rows = run_scan(arm, meshes)
    report("DASH10_RUN_SCAN", {"rows": rows})

    # 关键帧摘要（给人看）
    summary = [{
        "f": r["f"],
        "stance": ("L" if r["stance_L"] else "") + ("R" if r["stance_R"] else ""),
        "pelvis_z": r["pelvis"][2],
        "lean": r["lean_mm"],
        "aL_y": r["ankle_L_yz"][0], "aR_y": r["ankle_R_yz"][0],
        "sole_L": r["sole_L_mm"], "sole_R": r["sole_R_mm"],
        "reachL": r["pelvis_to_ankleL"], "reachR": r["pelvis_to_ankleR"],
        "step": r["step_deg"], "bone": r["step_bone"],
    } for r in rows if r["f"] % 4 == 0]
    report("DASH10_RUN_SUMMARY", {"every4": summary})

    # ---------- 2) 支撑期的脚相对身体后滑速率 = 角色速率 ----------
    spans = {}
    for side, offset in (("L", 0.0), ("R", R.RUN.right_offset)):
        pairs = [("foot." + side, r["ankle_%s_yz" % side][0]) for r in rows]
        pts = [(r["f"], r["ankle_%s_yz" % side][0]) for r in rows
               if WF.in_stance(R.RUN, r["f"], offset)]
        rate = 0.0
        if len(pts) >= 2:
            rate = (pts[-1][1] - pts[0][1]) / float(pts[-1][0] - pts[0][0])
        spans[side] = {
            "frames": [pts[0][0], pts[-1][0]] if pts else None,
            "ankle_y_first": pts[0][1] if pts else None,
            "ankle_y_last": pts[-1][1] if pts else None,
            "slide_mm_per_frame": round(rate, 3),
            "slide_mps": round(rate * A.FPS / 1000.0, 4),
        }
    report("DASH10_STANCE_RATE", {
        "declared_locomotion_mps": round(R.RUN.locomotion_mps, 4),
        "spans": spans,
    })

    # ---------- 3) `Idle_01@0` 的踝/骨盆真值（出口接缝目标） ----------
    A.apply_pose(arm, I1.idle_pose(arm, 0.0))
    idle = {
        "pelvis": [round(v * 1000.0, 2)
                   for v in A.bone_world(arm, "pelvis", "head")],
        "ankle_L": [round(v * 1000.0, 2)
                    for v in A.bone_world(arm, "foot.L", "head")],
        "ankle_R": [round(v * 1000.0, 2)
                    for v in A.bone_world(arm, "foot.R", "head")],
        "sole": {k: round(v[2] * 1000.0, 2)
                 for k, v in A.foot_lowest_by_side().items()},
    }
    report("DASH10_IDLE0", idle)

    # ---------- 4) 腿长几何上限：单支撑能买多少前进量 ----------
    leg_len = A.L_THIGH + A.L_SHIN
    geom = {"leg_len_mm": round(leg_len * 1000.0, 2),
            "hip_x_mm": A.HIP_X * 1000.0,
            "ankle_rest_z_mm": A.Z_ANKLE_REST * 1000.0}
    # 给定髋高 h（相对踝），最大的髋-踝水平距离 = sqrt(L^2 - h^2)
    for hip_z_mm in (900.0, 860.0, 830.0, 800.0, 760.0, 720.0):
        h = (hip_z_mm - A.Z_ANKLE_REST * 1000.0) / 1000.0
        if h >= leg_len:
            geom["hip_%d" % int(hip_z_mm)] = 0.0
            continue
        geom["hip_%d" % int(hip_z_mm)] = round(
            math.sqrt(leg_len * leg_len - h * h) * 1000.0, 1)
    report("DASH10_LEG_GEOMETRY", geom)

    # ---------- 5) 前冲惯性的"死量" ----------
    # 若末帧必须回到 Idle_01@0（平移不变），总前进量 = 首末骨盆 y 差。
    a0 = A.bone_world(arm, "pelvis", "head")
    A.apply_pose(arm, WF.gait_pose(arm, R.RUN, 0, meshes))
    p0 = A.bone_world(arm, "pelvis", "head")
    report("DASH10_DEAD_QUANTITY", {
        "run_f0_pelvis_y_mm": round(p0.y * 1000.0, 2),
        "run_f0_pelvis_z_mm": round(p0.z * 1000.0, 2),
        "run_two_step_m": round(R.STEP_M * 2.0, 4),
        "run_rate_mps": round(R.RUN.locomotion_mps, 4),
        "run_rate_mm_per_frame": round(R.RUN.locomotion_mps * 1000.0 / A.FPS, 3),
        "note": ("Run 是**原地**支：骨盆 y 净位移 0，所以「接 Run 的末速」在本支里"
                 "只能体现在「骨盆前进速度曲线的起点」——若本支走 Root Motion，"
                 "f0→f1 的前进量必须等于 Run 的每帧速率。"),
    })
    print("DASH10_PROBE_DONE")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("DASH10_PROBE_FAILURE " + traceback.format_exc())
