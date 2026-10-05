"""_e03_depth —— 标定 `TOUCH_OFF`：拳压到胸面多深时「贴住但不进去」。

`thumb_dn` 已定（手性修正后左右对称，体内顶点数从 466~498 降到 0~36）。
最后一件事：`f=44`（怒吼顶，胸口前挺）还残留 28~36 个顶点在体内。
本脚本扫 `TOUCH_OFF ∈ {20,24,28,32,36,38}`，量：
    · 体内顶点数（要 = 0）
    · 掌/指簇到胸面的最小带符号距离（要 ≤ +2 mm ⟹ 拳真的压住了）
    · 拳心到胸面的距离（诊断）
「贴近」与「不穿」是两个方向，本脚本找它们的交集。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python _e03_depth.py
"""

import json
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A          # noqa: E402
import anim_rage as R         # noqa: E402

SIDES = ("L", "R")
FRAMES = (28, 34, 44, 52, 66)
OFFSETS = (20.0, 24.0, 28.0, 32.0, 36.0, 38.0)


def main():
    arm, _meshes = R.boot()
    R.HAND_AXIS_MODE = "thumb_dn"
    for offset in OFFSETS:
        R.TOUCH_OFF = offset / 1000.0
        R.FIST_MIN_CLEAR_MM = offset
        rows = {}
        for frame in FRAMES:
            R.LAST_ELBOW.clear()
            pose = R.rage_pose(arm, frame)
            A.apply_pose(arm, pose)
            bpy.context.view_layer.update()
            R.torso_bvh_reset()
            row = {}
            for side in SIDES:
                inside, total, by_part = R.hand_inside_count(side)
                palm = [R.signed_to_torso(p) for p, n
                        in R.hand_mesh_points(side, step=2)
                        if not n.startswith("Thumb_")]
                row[side] = {
                    "inside": inside, "total": total,
                    "palm_min_mm": round(min(palm), 2),
                    "core_mm": round(R.signed_to_torso(
                        Vector(A.bone_world(arm, "hand." + side, "tail"))), 2),
                    "by_part": by_part,
                }
            rows[str(frame)] = row
        worst_inside = max(row[s]["inside"] for row in rows.values()
                           for s in SIDES)
        worst_palm = max(row[s]["palm_min_mm"] for row in rows.values()
                         for s in SIDES)
        print("E03_DEPTH " + json.dumps(
            {"touch_off_mm": offset, "worst_inside": worst_inside,
             "worst_palm_min_mm": round(worst_palm, 2), "frames": rows},
            ensure_ascii=False))
    print("E03_DEPTH_DONE")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("E03_DEPTH_FAILURE " + traceback.format_exc())
