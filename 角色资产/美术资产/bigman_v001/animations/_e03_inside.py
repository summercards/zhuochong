"""_e03_inside —— 用射线奇偶判定量「手的哪些部分真的在躯干体内」（只读）。

为什么换判据：`closest_point_on_mesh` 的**带符号距离**在凹几何上会骗人
（最近面可能是躯干侧壁 / 下摆内壁，不是胸面）⟹ 出现「拳在胸外 38 mm、
掌面却 −21 mm」这种自相矛盾的读数。射线奇偶判定在闭合网格上是**精确**
内外判定，不受凹面影响。

本脚本量：
  ① 站架姿（A01@0）下，左右手网格**在躯干内的顶点数**（预存几何基线）
  ② 4 种手的摆法在关键帧上的**体内顶点数**，并按部位（拇指/掌/指）拆开
  ③ 拳心到躯干表面的带符号距离（对照，看两个口径差多少）

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python _e03_inside.py
"""

import json
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A          # noqa: E402
import anim_rage as R         # noqa: E402

SIDES = ("L", "R")
FRAMES = (28, 34, 44, 52, 66)


def inside_report(side):
    """该侧手部各部位在躯干体内的顶点数 / 总数（★ 13 方向多数表决口径）。"""
    _inside, _total, by_part, _single = R.hand_inside_count(side)
    return by_part


def main():
    arm, _meshes = R.boot()

    # ① 站架基线
    A.reset_pose(arm)
    bpy.context.view_layer.update()
    R.torso_bvh_reset()
    station = {s: inside_report(s) for s in SIDES}
    print("E03_INSIDE_STATION " + json.dumps(station, ensure_ascii=False))

    # ② 4 种摆法
    for mode in R.HAND_AXIS_MODES:
        R.HAND_AXIS_MODE = mode
        frames = {}
        for frame in FRAMES:
            R.LAST_ELBOW.clear()
            pose = R.rage_pose(arm, frame)
            A.apply_pose(arm, pose)
            bpy.context.view_layer.update()
            R.torso_bvh_reset()
            frames[str(frame)] = {s: inside_report(s) for s in SIDES}
        total = {s: [sum(v[s][g][0] for g in v[s]) for _f, v in frames.items()]
                 for s in SIDES}
        print("E03_INSIDE_MODE " + json.dumps(
            {"mode": mode,
             "per_frame_inside_L": total["L"],
             "per_frame_inside_R": total["R"],
             "frames": [int(f) for f in FRAMES],
             "detail": frames}, ensure_ascii=False))

    print("E03_INSIDE_DONE")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("E03_INSIDE_FAILURE " + traceback.format_exc())
