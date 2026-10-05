"""probe_launch02 —— C02 `Launcher` 开工第一探针（只读）。

任务（来自 `doc/动画制作清单.md` §下一支详细制作计划 第 0 件）：
① 量上游接缝候选的真值（Heavy_01@36 / Combo_Finish@40 / Light_03@17 /
   Uppercut@34）与出口 `Idle_01@0`；
② 为「攻击轨迹明确向上」找到**可判定量**，并量出 B 族（含 C01）同量的全族最大值；
③ 量「鞋底贴地时踝高 vs 足尖角」的曲线（踮脚抬髋要用）；
④ 量「原地站架下髋能抬多高」的可达上限（腿长 822 是死约束）。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python probe_launch02.py
"""

import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402
import anim_lib as A  # noqa: E402
import anim_run_stop as RS  # noqa: E402

# 打击类：B 族（普通攻击）+ C01（已有的唯一 C 族）+ A 族两个参考（下蹲深度）
B_FAMILY = ("Light_01", "Light_02", "Light_03", "Heavy_01", "Heavy_02",
            "Low_Attack", "Uppercut", "Air_Light", "Air_Heavy", "Dash_Attack")
C_FAMILY = ("Combo_Finish",)
REF = ("Crouch", "Jump_Start", "Idle_01")

# 上游接缝候选
SEAM_CANDIDATES = (("Heavy_01", 36), ("Combo_Finish", 40),
                   ("Light_03", 17), ("Uppercut", 34))


def rows_of(arm, action):
    scene = bpy.context.scene
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    start, end = action.frame_range
    rows = []
    for frame in range(int(round(start)), int(round(end)) + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        rows.append({
            "f": frame,
            "pelvis": Vector(A.bone_world(arm, "pelvis", "head")),
            "fistR": Vector(A.bone_world(arm, "hand.R", "tail")),
            "fistL": Vector(A.bone_world(arm, "hand.L", "tail")),
            "ankL": Vector(A.bone_world(arm, "foot.L", "head")),
            "ankR": Vector(A.bone_world(arm, "foot.R", "head")),
            "hipL": Vector(A.bone_world(arm, "thigh.L", "head")),
            "hipR": Vector(A.bone_world(arm, "thigh.R", "head")),
        })
    return rows


def vertical_metrics(rows):
    """「向上」这件事只认**世界 z**（骨盆系里"向上"会被身体自转吃掉）。

    本探针量四个量：
      pelvis_z_rise_mm  髋世界 z 的**全程极差**（max − min）
      fist_z_rise_mm    打击拳（取两手较大者）世界 z 的**全程极差**
      fist_z_up_path    拳向上走的路径长（只累计 dz>0 的步长）
      fist_z_peak_mm    拳峰世界 z
    """
    def z(series):
        return [p.z * 1000.0 for p in series]

    pz = z([r["pelvis"] for r in rows])
    zR = z([r["fistR"] for r in rows])
    zL = z([r["fistL"] for r in rows])
    up = 0.0
    for seq in (zR, zL):
        up = max(up, sum(max(0.0, seq[i + 1] - seq[i])
                         for i in range(len(seq) - 1)))
    best = zR if (max(zR) - min(zR)) >= (max(zL) - min(zL)) else zL
    which = "R" if best is zR else "L"
    return {
        "pelvis_z_min_mm": round(min(pz), 2),
        "pelvis_z_max_mm": round(max(pz), 2),
        "pelvis_z_rise_mm": round(max(pz) - min(pz), 2),
        "pelvis_z_at_0": round(pz[0], 2),
        "pelvis_z_at_end": round(pz[-1], 2),
        "fist_z_rise_mm": round(max(best) - min(best), 2),
        "fist_z_up_path_mm": round(up, 2),
        "fist_z_peak_mm": round(max(best), 2),
        "fist_z_low_mm": round(min(best), 2),
        "up_hand": which,
    }


def main():
    arm, _meshes = A.open_animation_project()
    A.setup_scene()
    scene = bpy.context.scene

    # ---------------------------------------------------------- ① 基线
    table = {}
    for name in B_FAMILY + C_FAMILY + REF:
        action = bpy.data.actions.get(name)
        if action is None:
            continue
        table[name] = vertical_metrics(rows_of(arm, action))
        A.report("LAUNCH02_BASE", {"name": name, **table[name]})

    axes = ("pelvis_z_rise_mm", "fist_z_rise_mm", "fist_z_up_path_mm",
            "fist_z_peak_mm")
    ground_only = [n for n in B_FAMILY if n not in ("Air_Light", "Air_Heavy")]
    worst = {}
    for axis in axes:
        for tag, pool in (("all", B_FAMILY), ("ground", ground_only)):
            name, value = max(((n, table[n][axis]) for n in pool
                               if n in table), key=lambda it: it[1])
            worst["%s__%s" % (axis, tag)] = {
                "anim": name, "value": value,
                "x1.05": round(value * 1.05, 2),
                "x1.15": round(value * 1.15, 2),
                "x1.50": round(value * 1.50, 2)}
    A.report("LAUNCH02_BASELINE", worst)

    # ---------------------------------------------------------- ② 接缝真值
    for name, frame in SEAM_CANDIDATES:
        action = bpy.data.actions.get(name)
        if action is None:
            continue
        arm.animation_data.action = action
        A._bind_slot(arm, action)
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        pel = Vector(A.bone_world(arm, "pelvis", "head"))
        row = {"action": name, "frame": frame,
               "pelvis_mm": [round(v * 1000.0, 2) for v in pel]}
        for side in ("L", "R"):
            ank = Vector(A.bone_world(arm, "foot." + side, "head"))
            hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
            row["ank_%s_mm" % side] = [round(v * 1000.0, 2) for v in ank]
            row["rel_%s_mm" % side] = round((pel.y - ank.y) * 1000.0, 2)
            row["reach_%s_mm" % side] = round((ank - hip).length * 1000.0, 2)
            row["ratio_%s" % side] = round((ank - hip).length
                                           / (A.L_THIGH + A.L_SHIN), 5)
        row["hip_z_mm"] = round(A.bone_world(arm, "thigh.L", "head").z * 1000.0, 2)
        row["hip_minus_pelvis_z_mm"] = round(row["hip_z_mm"]
                                             - row["pelvis_mm"][2], 2)
        A.report("LAUNCH02_SEAM", row)

    idle = bpy.data.actions.get("Idle_01")
    arm.animation_data.action = idle
    A._bind_slot(arm, idle)
    scene.frame_set(0)
    bpy.context.view_layer.update()
    pel0 = Vector(A.bone_world(arm, "pelvis", "head"))
    out = {"pelvis_mm": [round(v * 1000.0, 2) for v in pel0],
           "hip_z_mm": round(A.bone_world(arm, "thigh.L", "head").z * 1000.0, 2)}
    for side in ("L", "R"):
        ank = Vector(A.bone_world(arm, "foot." + side, "head"))
        hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
        out["ank_%s_mm" % side] = [round(v * 1000.0, 2) for v in ank]
        out["rel_%s_mm" % side] = round((pel0.y - ank.y) * 1000.0, 2)
        out["reach_%s_mm" % side] = round((ank - hip).length * 1000.0, 2)
    out["leg_length_mm"] = round((A.L_THIGH + A.L_SHIN) * 1000.0, 2)
    A.report("LAUNCH02_IDLE0", out)

    # ---------------------------------------------------------- ③ 踝高 vs 足尖角
    # 口径：让鞋底最低点刚好贴地（z=0），量此时踝（foot.head）的世界高度 z。
    # 姿态取「两脚都踩在接缝位置」的站架 —— 标定姿态必须与动画里的姿态量级接近
    # （RS.measure_plant_z 的文件头记过这个坑）。
    heavy = bpy.data.actions.get("Heavy_01")
    arm.animation_data.action = heavy
    A._bind_slot(arm, heavy)
    scene.frame_set(36)
    bpy.context.view_layer.update()
    seam_pelvis = Vector(A.bone_world(arm, "pelvis", "head"))
    seam_ank = {s: Vector(A.bone_world(arm, "foot." + s, "head"))
                for s in ("L", "R")}
    torso = {"pelvis": (4.0, 0.0, 0.0),
             "@loc": {"pelvis": A.wloc(0.0, 0.0, -0.070)}}
    curve = {}
    for tip in (0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0):
        z, err = RS.measure_plant_z(arm, tip, torso,
                                    (seam_ank["L"].x, seam_ank["L"].y),
                                    seam_ank["L"].z)
        curve["%g" % tip] = [round(z * 1000.0, 3), round(err, 3)]
    A.report("LAUNCH02_TIP_CURVE", {
        "tip_deg_to_ankle_z_mm": curve,
        "note": ("第二个数是 leg_to 的落点误差 mm（必须 ≈0，否则标定姿态不可达）。"
                 "踝高 − 78 mm（静止踝高）≈ 踮脚能白送多少抬髋量。")})

    # ---------------------------------------------------------- ④ 原地最大抬髋
    # 在「踝固定在接缝位置」的前提下，逐 tip 求髋能抬到多高：
    #   竖直余量 dz_max = sqrt((0.995·822)² − dy²)，dy = |踝 y − 髋 y|
    limit = 0.995 * (A.L_THIGH + A.L_SHIN) * 1000.0
    reach_table = {}
    for side in ("L", "R"):
        dy = abs(seam_pelvis.y - seam_ank[side].y) * 1000.0
        dz = math.sqrt(max(0.0, limit * limit - dy * dy))
        z70 = curve["0"][0]   # 平放时踝高（mm）
        reach_table[side] = {
            "dy_mm": round(dy, 2),
            "dz_max_mm": round(dz, 2),
            "ankle_z_flat_mm": z70,
            "hip_z_max_flat_mm": round(z70 + dz, 2),
            "pelvis_z_max_flat_mm": round(z70 + dz - 13.06, 2),
        }
    A.report("LAUNCH02_REACH", {
        "limit_mm": round(limit, 2),
        "per_side": reach_table,
        "note": "pelvis_z_max = 踝高 + sqrt(0.995L² − dy²) − (髋比骨盆高多少)。",
    })


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("LAUNCH02_FAILURE " + traceback.format_exc())
