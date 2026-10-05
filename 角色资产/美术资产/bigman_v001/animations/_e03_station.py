"""_e03_station —— 定性「A01 站架姿里右手拇指陷进躯干 36 mm」是谁的问题。

背景：`_e03_valid.py` 用**三个互相独立**的口径（单方向射线奇偶 / 13 方向多数
表决 / 正面射线遮挡）在 `f=0`（= A01 站架）上一致读出
    R: 145 / 1326 个手部顶点在躯干实体内，最深 36.15 mm，位置 (-0.095,-0.179,1.293)
    L: 0
三种口径一致 ⟹ 不是口径噪声。本脚本回答两个问题：

  ① 这是**真实 A01 Action** 的问题，还是本支**重建 `BASE`** 的问题？
     → 直接把**真实 `Idle_01` Action** 绑上去、`frame_set(0)`，跑同一套扫描，
       与 `rage_pose(arm, 0)` 的重建姿态并排比。
  ② 它**看得见吗**？→ 渲胸/手特写（正面 / 3Q / 侧）+ **手部层单独渲**
     （把手以外的网格全隐藏）——「剔掉躯干后手到底在哪」是唯一不会骗人的看法。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python _e03_station.py
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

# 胸前特写（正交 0.55 m）——捶胸的「案发现场」就在这个框里
CHEST_FRONT = ("chestfront", (0.0, -2.0, 1.30), (0.0, 0.0, 1.30), 0.55,
               (760, 760))
CHEST_3Q = ("chest3q", (1.15, -1.55, 1.55), (0.0, -0.05, 1.30), 0.60,
            (760, 760))
CHEST_SIDE = ("chestside", (2.0, -0.05, 1.30), (0.0, -0.05, 1.30), 0.62,
              (760, 760))


def scan(tag):
    R.torso_bvh_reset()
    out = {}
    for side in SIDES:
        inside, total, by_part, single = R.hand_inside_count(side,
                                                             with_single=True)
        pts = R.hand_mesh_points(side, step=2)
        palm = [R.signed_to_torso(p) for p, n in pts
                if not n.startswith("Thumb_")]
        thumb = [R.signed_to_torso(p) for p, n in pts
                 if n.startswith("Thumb_")]
        deepest = min(pts, key=lambda item: R.signed_to_torso(item[0]))
        out[side] = {"inside_votes": inside, "inside_single_dir": single,
                     "n": total,
                     "palm_min_mm": round(min(palm), 2),
                     "thumb_min_mm": round(min(thumb), 2) if thumb else None,
                     "all_min_mm": round(R.signed_to_torso(deepest[0]), 2),
                     "all_min_at": deepest[1],
                     "all_min_xyz": [round(c, 4) for c in deepest[0]],
                     "by_part": by_part}
    print("E03_STATION " + json.dumps({"tag": tag, "sides": out},
                                      ensure_ascii=False))


def main():
    arm, meshes = R.boot()
    R.HAND_AXIS_MODE = "thumb_dn"

    # ---- ① 真实 Idle_01 Action @ frame 0 --------------------------------
    action = bpy.data.actions["Idle_01"]
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    bpy.context.scene.frame_set(0)
    bpy.context.view_layer.update()
    scan("real Idle_01 @0")

    # ---- ② 本支重建的 BASE（= rage_pose(arm, 0)）------------------------
    if arm.animation_data:
        arm.animation_data.action = None
    R.LAST_ELBOW.clear()
    pose0 = R.rage_pose(arm, 0)
    A.apply_pose(arm, dict(pose0))
    bpy.context.view_layer.update()
    scan("rage_pose(0) rebuild")

    # ---- ③ 渲特写：整身 + 手部层 ----------------------------------------
    prefix = "e03station"
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    bpy.context.scene.frame_set(0)
    bpy.context.view_layer.update()
    A.render_pose_sheet(arm, action, [0], prefix,
                        views=(CHEST_FRONT, CHEST_3Q, CHEST_SIDE))
    R.render_layer(arm, action, prefix + "_hand", R.HAND_PREFIX,
                   CHEST_FRONT, [0])
    R.render_layer(arm, action, prefix + "_hand3q", R.HAND_PREFIX,
                   CHEST_3Q, [0])
    print("E03_STATION_DONE")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("E03_STATION_FAILURE " + traceback.format_exc())
