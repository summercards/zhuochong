"""probe_combo01b —— C01 开工第二探针（只读）：

① 补量 `fist_rel_path_mm`（打击手**相对骨盆的路径长度**）—— 见下方"为什么换维度"。
② 量上游接缝 `Heavy_01@36` 的真实世界量（踝位、骨盆、髋踝距），
   因为"跨步"是 Heavy_01 烘进姿态的，不实测算不出来。

★ 为什么要把"躯干前倾极差"这一维换掉（本探针的结论会写进 C01 正文）：
  脊柱（pelvis.head → neck.head）长 ≈ 0.52 m。一条圆弧把两端拉开的最大**矢高**
  = L·(1−cos(θ/2))·(θ/2)/sin(θ/2) 的上界是 L·2/π ≈ 0.331 m（θ=180°）。
  极差 ≤ 2 × 0.331 = **0.662 m**，而 1.5 × Heavy_02(0.501) = **0.7515 m**
  ⟹ **1.5 倍在本维度物理不可达**。如实登记，改用"打击手相对骨盆的**弧长**"
  —— 同一量纲（长度）、无几何天花板、且更贴近"幅度"的观感定义。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python probe_combo01b.py
"""

import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402
import anim_lib as A  # noqa: E402

B_FAMILY = ("Light_01", "Light_02", "Light_03", "Heavy_01", "Heavy_02",
            "Low_Attack", "Uppercut", "Air_Light", "Air_Heavy", "Dash_Attack")


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
            "neck": Vector(A.bone_world(arm, "neck", "head")),
            "fistR": Vector(A.bone_world(arm, "hand.R", "tail")),
            "fistL": Vector(A.bone_world(arm, "hand.L", "tail")),
            "ankL": Vector(A.bone_world(arm, "foot.L", "head")),
            "ankR": Vector(A.bone_world(arm, "foot.R", "head")),
            "hipL": Vector(A.bone_world(arm, "thigh.L", "head")),
            "hipR": Vector(A.bone_world(arm, "thigh.R", "head")),
        })
    return rows


def path_mm(points):
    return sum((points[i + 1] - points[i]).length
               for i in range(len(points) - 1)) * 1000.0


def span_mm(points):
    best = 0.0
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            best = max(best, (points[i] - points[j]).length)
    return best * 1000.0


def metrics(rows):
    pel = [r["pelvis"] for r in rows]
    relR = [r["fistR"] - p for r, p in zip(rows, pel)]
    relL = [r["fistL"] - p for r, p in zip(rows, pel)]
    pitch = [(p.y - n.y) * 1000.0 for p, n in zip(pel, [r["neck"] for r in rows])]

    def step(series):
        return max((series[i + 1] - series[i]).length * 1000.0
                   for i in range(len(series) - 1))

    ankRelL = [r["ankL"] - p for r, p in zip(rows, pel)]
    ankRelR = [r["ankR"] - p for r, p in zip(rows, pel)]
    return {
        "fist_rel_range_mm": round(max(span_mm(relR), span_mm(relL)), 2),
        "fist_rel_path_mm": round(max(path_mm(relR), path_mm(relL)), 2),
        "fist_world_path_mm": round(max(path_mm([r["fistR"] for r in rows]),
                                        path_mm([r["fistL"] for r in rows])), 2),
        "torso_pitch_range_mm": round(max(pitch) - min(pitch), 2),
        "swing_step_rel_mm": round(max(step(ankRelL), step(ankRelR)), 2),
    }


def main():
    arm, _meshes = A.open_animation_project()
    A.setup_scene()
    table = {}
    for name in B_FAMILY:
        action = bpy.data.actions.get(name)
        if action is None:
            continue
        table[name] = metrics(rows_of(arm, action))
        A.report("COMBO01B_PROBE", {"name": name, **table[name]})
    axes = ("fist_rel_range_mm", "fist_rel_path_mm", "torso_pitch_range_mm",
            "swing_step_rel_mm")
    worst = {}
    for axis in axes:
        name, value = max(((n, t[axis]) for n, t in table.items()),
                          key=lambda item: item[1])
        worst[axis] = {"anim": name, "value": value,
                       "x1.5": round(value * 1.5, 2)}
    A.report("COMBO01B_BASELINE", worst)

    # ---- 上游接缝：`Heavy_01@36`（B04 的可取消帧 CANCEL=36）
    heavy = bpy.data.actions.get("Heavy_01")
    scene = bpy.context.scene
    arm.animation_data.action = heavy
    A._bind_slot(arm, heavy)
    scene.frame_set(36)
    bpy.context.view_layer.update()
    pel = Vector(A.bone_world(arm, "pelvis", "head"))
    seam = {"pelvis": [round(v * 1000.0, 2) for v in pel]}
    for side in ("L", "R"):
        ank = Vector(A.bone_world(arm, "foot." + side, "head"))
        hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
        seam["ankle_" + side + "_mm"] = [round(v * 1000.0, 2) for v in ank]
        seam["relative_" + side + "_mm"] = round((pel.y - ank.y) * 1000.0, 2)
        seam["reach_" + side + "_mm"] = round((ank - hip).length * 1000.0, 2)
    seam["leg_length_mm"] = round((A.L_THIGH + A.L_SHIN) * 1000.0, 2)
    seam["hip_z_mm"] = round(A.bone_world(arm, "thigh.L", "head").z * 1000.0, 2)
    # 出口接缝 Idle_01@0 的两脚相对骨盆
    idle = bpy.data.actions.get("Idle_01")
    arm.animation_data.action = idle
    A._bind_slot(arm, idle)
    scene.frame_set(0)
    bpy.context.view_layer.update()
    pel0 = Vector(A.bone_world(arm, "pelvis", "head"))
    seam["idle_pelvis_mm"] = [round(v * 1000.0, 2) for v in pel0]
    for side in ("L", "R"):
        ank = Vector(A.bone_world(arm, "foot." + side, "head"))
        seam["idle_relative_" + side + "_mm"] = round((pel0.y - ank.y) * 1000.0, 2)
    A.report("COMBO01B_SEAM", seam)


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("COMBO01B_FAILURE " + traceback.format_exc())
