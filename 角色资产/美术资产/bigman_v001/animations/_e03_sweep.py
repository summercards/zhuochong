"""_e03_sweep —— **全时间轴**实测：扫 `TOUCH_OFF`，找「贴住但不穿」的交集。

与 `_e03_depth.py` 的三个关键差别（也是本脚本存在的理由）：
  ① `_e03_depth.py` 只量 5 个孤立帧、且每帧 `LAST_ELBOW.clear()` ⟹ 它测的是
     「**单帧冷启动解**」，而**真实动画**是 f=0→96 **逐帧带着肘连续性走下来**的
     ⟹ 两者姿态不同，穿透深度当然也不同。本脚本**按真实顺序逐帧建姿**。
  ② 取样帧 (28,34,44,52,66) 与真正的命中窗口 (28~36, 52~60) 不一致 ⟹ 会漏帧。
     本脚本按相位**逐帧全覆盖**。
  ③ 体内判定用**13 方向多数表决**（`_e03_yard.py` 实测：单方向奇偶在水密网格上
     会因擦边产生 1~60 个假阳性，得票只有 1；真内部恒 13/13）。

同时量三件东西（拳心 / 掌指簇 / 拇指 各自到胸面的带符号距离），
因为 v004 改了拳面朝向后「谁先碰到胸」会变 —— 这决定 `TOUCH_OFF` 的值。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python _e03_sweep.py
"""

import json
import os
import sys

import bpy
import mathutils.bvhtree as bvhtree
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A          # noqa: E402
import anim_rage as R         # noqa: E402

SIDES = ("L", "R")
# 每项 = "TOUCH_OFF:拳心保护下限"（mm）。留空则下限 = TOUCH_OFF。
PAIRS = os.environ.get("E03_SWEEP_PAIRS", "29:31,30:32,31:33,31:32").split(",")
VSTEP = int(os.environ.get("E03_SWEEP_STEP", "3"))
_FROM = int(os.environ.get("E03_SWEEP_FROM", "0"))
_TO = int(os.environ.get("E03_SWEEP_TO", "96"))
MEASURE = list(range(_FROM, _TO + 1))


def unbound(arm):
    """★ 手工摆姿前必须解绑 Action —— 否则 `view_layer.update()` 会用
    Action 重算姿态，把手工 pose 覆盖掉（`probe_e03_baseline.py` 踩过）。"""
    if arm.animation_data:
        arm.animation_data.action = None


def tree():
    deps = bpy.context.evaluated_depsgraph_get()
    return bvhtree.BVHTree.FromObject(R.TORSO, deps)


def sample(arm, side, t, core_world):
    inside, total, by_part, _single = R.hand_inside_count(
        side, tree=t, step=VSTEP)
    pts = R.hand_mesh_points(side, step=VSTEP)
    groups = {"palm": [], "fingers": [], "thumb": []}
    for p, name in pts:
        if name.startswith("Thumb_"):
            groups["thumb"].append(R.signed_to_torso(p))
        elif name.startswith("Hand_Palm_"):
            groups["palm"].append(R.signed_to_torso(p))
        else:
            groups["fingers"].append(R.signed_to_torso(p))
    mesh = [R.signed_to_torso(p) for p, _n in pts]
    return {"in": inside, "tot": total,
            "core": round(R.signed_to_torso(core_world), 2),
            "palm": round(min(groups["palm"]), 2) if groups["palm"] else None,
            "fingers": round(min(groups["fingers"]), 2) if groups["fingers"] else None,
            "thumb": round(min(groups["thumb"]), 2) if groups["thumb"] else None,
            "mesh": round(min(mesh), 2),
            "part_in": {k: v[0] for k, v in by_part.items()}}


def main():
    arm, _meshes = R.boot()
    unbound(arm)
    R.HAND_AXIS_MODE = "thumb_dn"
    for pair in PAIRS:
        parts = pair.split(":")
        offset = float(parts[0])
        clear = float(parts[1]) if len(parts) > 1 else offset
        R.TOUCH_OFF = offset / 1000.0
        R.FIST_MIN_CLEAR_MM = clear
        R.LAST_ELBOW.clear()
        poses = [(f, R.rage_pose(arm, f)) for f in range(0, R.TOTAL + 1)]
        rows = {}
        for frame in MEASURE:
            A.apply_pose(arm, dict(poses[frame][1]))
            bpy.context.view_layer.update()
            t = tree()
            row = {}
            for side in SIDES:
                core = Vector(A.bone_world(arm, "hand." + side, "tail"))
                row[side] = sample(arm, side, t, core)
            rows[frame] = row
        worst = {k: max(rows[f][s][k] for f in rows for s in SIDES
                        if rows[f][s][k] is not None)
                 for k in ("in", "palm", "fingers", "thumb", "core", "mesh")}
        bad = sorted(set(f for f in rows for s in SIDES if rows[f][s]["in"] > 0))
        print("E03_SWEEP " + json.dumps(
            {"touch_off_mm": offset, "clear_mm": clear, "worst": worst,
             "frames_with_inside": bad,
             "rows": {str(f): rows[f] for f in rows}}, ensure_ascii=False))
    print("E03_SWEEP_DONE")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("E03_SWEEP_FAILURE " + traceback.format_exc())
