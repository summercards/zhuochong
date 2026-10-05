"""probe_combo01 —— C01 `Combo_Finish` 开工前的**只读**基线扫描。

清单要求「动作幅度 ≥ 普通攻击的 **1.5 倍**」。1.5 倍必须落在**可判定量**上，
而"可判定量"的口径必须能跨支比较。本探针把 B 族（普通攻击 B01~B10）逐帧实测，
给出候选口径的**全族分布**，再在 C01 里按"全族最大 × 1.5"设阈值。

三个候选维度（都在**世界坐标**上先量，再各给一份**骨盆系**版本）：

  A. 拳世界行程    `fist_range_mm`      = max_{i,j} |hand.R.tail(i) − hand.R.tail(j)|
     定义成"全片最大两点距离"而不是"从某帧到某帧" —— 不需要知道每支的相位表，
     跨支口径完全一致（不会因为"我把 ANTIC 标在别处"而变）。
  B. 躯干前倾摆动  `torso_pitch_range_mm` = max_f(pelvis.y − neck.y) − min_f(...)
     平移不变（骨盆与颈一起动），量的是躯干**从上到下的总摆幅**。
  C. 摆动脚单帧步长 `swing_step_mm`      = max 相邻帧的踝世界位移（左右取大）

★ 为什么同时给**骨盆系**版本：B10 的教训 11 —— 有 Root Motion 的支，
  凡"世界位移"型判据都要先问一句"这量是相对谁的"。骨盆系版本把整具身体的
  平移减掉，量的是"角色自己动了多少"，是跨支可比的那一个。

只读：不建 Action、不打帧、不存盘。
运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python probe_combo01.py
"""

import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402
import anim_lib as A  # noqa: E402

ART = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   ".."))
B_FAMILY = ("Light_01", "Light_02", "Light_03", "Heavy_01", "Heavy_02",
            "Low_Attack", "Uppercut", "Air_Light", "Air_Heavy", "Dash_Attack")


def sample(arm, action):
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
            "pelvis": tuple(A.bone_world(arm, "pelvis", "head")),
            "neck": tuple(A.bone_world(arm, "neck", "head")),
            "fistR": tuple(A.bone_world(arm, "hand.R", "tail")),
            "fistL": tuple(A.bone_world(arm, "hand.L", "tail")),
            "ankL": tuple(A.bone_world(arm, "foot.L", "head")),
            "ankR": tuple(A.bone_world(arm, "foot.R", "head")),
        })
    return rows


def range_mm(points):
    """全片最大两点距离（mm）。点 = [(x,y,z), ...]"""
    best = 0.0
    for i in range(len(points)):
        a = Vector(points[i])
        for j in range(i + 1, len(points)):
            best = max(best, (a - Vector(points[j])).length)
    return best * 1000.0


def metrics(rows):
    pel = [Vector(r["pelvis"]) for r in rows]
    neck = [Vector(r["neck"]) for r in rows]

    def rel(key):
        return [(Vector(r[key]) - p) for r, p in zip(rows, pel)]

    fist_w = [r["fistR"] for r in rows]
    fist_r = [tuple(v) for v in rel("fistR")]
    fistL_w = [r["fistL"] for r in rows]
    fistL_r = [tuple(v) for v in rel("fistL")]
    ank_w = {"L": [r["ankL"] for r in rows], "R": [r["ankR"] for r in rows]}
    ank_r = {"L": [tuple(v) for v in rel("ankL")],
             "R": [tuple(v) for v in rel("ankR")]}

    pitch = [(p.y - n.y) * 1000.0 for p, n in zip(pel, neck)]

    def step(series):
        return max(((Vector(series[i + 1]) - Vector(series[i])).length * 1000.0)
                   for i in range(len(series) - 1))

    out = {
        "frames": len(rows),
        "fist_world_range_mm": round(range_mm(fist_w), 2),
        "fist_rel_range_mm": round(range_mm(fist_r), 2),
        "guard_world_range_mm": round(range_mm(fistL_w), 2),
        "guard_rel_range_mm": round(range_mm(fistL_r), 2),
        "torso_pitch_range_mm": round(max(pitch) - min(pitch), 2),
        "torso_pitch_peak_mm": round(max(pitch), 2),
        "torso_pitch_min_mm": round(min(pitch), 2),
        "swing_step_world_mm": round(max(step(ank_w["L"]), step(ank_w["R"])), 2),
        "swing_step_rel_mm": round(max(step(ank_r["L"]), step(ank_r["R"])), 2),
        "pelvis_span_mm": round(range_mm([r["pelvis"] for r in rows]), 2),
    }
    return out


def main():
    arm, _meshes = A.open_animation_project()
    A.setup_scene()
    table = {}
    for name in B_FAMILY:
        action = bpy.data.actions.get(name)
        if action is None:
            A.report("COMBO01_PROBE_MISSING", {"name": name})
            continue
        table[name] = metrics(sample(arm, action))
        A.report("COMBO01_PROBE", {"name": name, **table[name]})
    axes = ("fist_world_range_mm", "fist_rel_range_mm", "guard_rel_range_mm",
            "torso_pitch_range_mm", "torso_pitch_peak_mm",
            "swing_step_world_mm", "swing_step_rel_mm", "pelvis_span_mm")
    worst = {}
    for axis in axes:
        name, value = max(((n, t[axis]) for n, t in table.items()),
                          key=lambda item: item[1])
        worst[axis] = {"anim": name, "value": value,
                       "x1.5": round(value * 1.5, 2)}
    A.report("COMBO01_BASELINE", worst)


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("COMBO01_PROBE_FAILURE " + traceback.format_exc())
