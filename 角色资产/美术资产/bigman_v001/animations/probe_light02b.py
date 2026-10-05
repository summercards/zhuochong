"""probe_light02b —— 给 B02 的 `strike_arc_ok` 取基线：量 B01 `Light_01` 的"肩轴扫掠角"。

为什么必须量：`strike_arc_ok` 的门禁口径从计划原文的「腕到肩半径变化 ≤25%」
换成了「**以肩为轴的累计扫掠角 ≥25°**」（原文口径几何不可达，证明见
`anim_light_02.py` 文件头 + 报告里的 `strike_arc_plan_metric_unreachable`）。
换过口径的判据**必须证明它真的能区分直拳与横拳** —— 否则就是一条凑绿的假判据。
本探针把 B01（直拳）在同一口径下的数值量出来，作为基线写进 B02 的报告。

用法：
    blender --background --factory-startup --python probe_light02b.py
"""

import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A  # noqa: E402


def sweep(points, pivots, i0, i1):
    total, prev = 0.0, None
    for i in range(i0, i1 + 1):
        d = points[i] - pivots[i]
        if d.length < 1e-9:
            continue
        d = d.normalized()
        if prev is not None:
            total += math.degrees(prev.angle(d))
        prev = d
    return total


def report_for(arm, action, hand, hit):
    frames = list(range(0, int(action.frame_range[1]) + 1))
    samples = A.sample_animation(arm, action, frames[0], frames[-1])
    fist = [Vector(s["hand.%s.tail" % hand]) for s in samples]
    sh = [Vector(s["upperarm.%s" % hand]) for s in samples]
    wrist = [Vector(s["hand.%s" % hand]) for s in samples]
    rad = [(wrist[i] - sh[i]).length * 1000.0 for i in range(len(samples))]
    A.report("ARC_BASELINE_%s" % action.name, {
        "hand": hand,
        "hit": hit,
        "frames": [frames[0], frames[-1]],
        "shoulder_sweep_0_to_hit_deg": round(sweep(fist, sh, 0, hit), 2),
        "shoulder_sweep_0_to_end_deg": round(sweep(fist, sh, 0, len(samples) - 1), 2),
        "radius_guard_mm": round(rad[0], 1),
        "radius_hit_mm": round(rad[hit], 1),
        "radius_span_ratio": round((max(rad) - min(rad)) / max(rad), 4),
        "note": "同口径下直拳 vs 横拳的对照：扫掠角越大 = 越是绕肩横摆",
    })
    return sweep(fist, sh, 0, hit)


def main():
    arm, _meshes = A.open_animation_project()
    A.setup_scene()
    out = {}
    for name, hand, hit in (("Light_01", "L", 6), ("Light_02", "R", 8)):
        action = bpy.data.actions.get(name)
        if action is None:
            print("ARC_BASELINE_SKIP %s 不在工程里" % name)
            continue
        out[name] = report_for(arm, action, hand, hit)
    if len(out) == 2:
        A.report("ARC_BASELINE_COMPARE", {
            "b01_light01_sweep_deg": out["Light_01"],
            "b02_light02_sweep_deg": out["Light_02"],
            "gap_deg": round(out["Light_02"] - out["Light_01"], 2),
            "verdict": ("横拳的扫掠角必须显著大于直拳，否则该判据不具区分度"
                        if out["Light_02"] > out["Light_01"] + 15.0
                        else "★ 区分度不足，判据要重设计"),
        })
    print("PROBE_LIGHT02B_DONE")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("PROBE_LIGHT02B_FAILURE " + traceback.format_exc())
