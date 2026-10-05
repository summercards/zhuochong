"""E06 / E07 / E08 三方逐帧姿态距离（判「胜利三连是否撞车」）。

只读：打开工程、取三支 action、按帧号逐帧比对 57 骨的矩阵口径最大差
+ 拳心世界位置差 + 拳心高度曲线。

★ 与二方版 `_probe_e07_vs_e06.py` 的区别：三支**两两**都要比（3 对），
  且额外输出**首拍差异**（f14 / f12 —— 清单 §0 第 2 条的量化载体）。
"""
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A  # noqa: E402

ARMS = ("Victory_01", "Victory_02", "Victory_03")
TOTAL = 120
PAIRS = (("Victory_01", "Victory_02"), ("Victory_01", "Victory_03"),
         ("Victory_02", "Victory_03"))
# ★ 三支的「第一拍」关键帧（E06/E07 是 14，E08 是 12）。
FIRSTBEAT = {"Victory_01": 14, "Victory_02": 14, "Victory_03": 12}


def mat_deg(ma, mb):
    worst = 0.0
    for c in range(3):
        va = ma.col[c].normalized()
        vb = mb.col[c].normalized()
        worst = max(worst, math.degrees(math.acos(max(-1.0, min(1.0,
                                                              va.dot(vb))))))
    return worst


def main():
    arm, _meshes = A.open_animation_project()
    A.setup_scene()
    bones = sorted(arm.pose.bones.keys())
    acts = {n: bpy.data.actions[n] for n in ARMS}
    scene = bpy.context.scene

    # 逐帧缓存：矩阵 + 双拳心世界位置
    cache = {n: {} for n in ARMS}
    for name, act in acts.items():
        arm.animation_data.action = act
        A._bind_slot(arm, act)
        for frame in range(TOTAL + 1):
            scene.frame_set(frame)
            bpy.context.view_layer.update()
            cache[name][frame] = {
                "m": {b: arm.pose.bones[b].matrix.to_3x3().copy()
                      for b in bones if b in arm.pose.bones},
                "fistL": Vector(A.bone_world(arm, "hand.L", "tail")),
                "fistR": Vector(A.bone_world(arm, "hand.R", "tail")),
            }

    for a, b in PAIRS:
        rows = []
        for frame in range(TOTAL + 1):
            ma, mb = cache[a][frame]["m"], cache[b][frame]["m"]
            rows.append((frame,
                         max(mat_deg(ma[k], mb[k]) for k in set(ma) & set(mb))))
        mx = max(rows, key=lambda r: r[1])
        same = sum(1 for _f, d in rows if d <= 1.0)
        # 拳心最大差（取两臂的较大）
        fist_max, fist_at = 0.0, None
        for frame in range(TOTAL + 1):
            for key in ("fistL", "fistR"):
                d = (cache[a][frame][key]
                     - cache[b][frame][key]).length * 1000.0
                if d > fist_max:
                    fist_max, fist_at = d, (frame, key)
        print("E08_3WAY %s vs %s: max_mat_deg=%.3f @f=%d | "
              "identical(<=1deg)=%d frames | fist_max=%.1f mm @ f%s"
              % (a, b, mx[1], mx[0], same, fist_max, fist_at))
        for frame in (0, 12, 14, 24, 34, 48, 60, 80, 92, 110, 120):
            print("   f=%3d mat=%7.3f deg  fistL_d=%8.2f mm  fistR_d=%8.2f mm"
                  % (frame, rows[frame][1],
                     (cache[a][frame]["fistL"]
                      - cache[b][frame]["fistL"]).length * 1000.0,
                     (cache[a][frame]["fistR"]
                      - cache[b][frame]["fistR"]).length * 1000.0))

    # ---- 首拍位移（三支各自的 f0→第一拍）--------------------------------
    print("E08_3WAY_FIRSTBEAT (f0 -> 第一拍) 的拳心位移")
    for name in ARMS:
        fb = FIRSTBEAT[name]
        for key in ("fistL", "fistR"):
            d = (cache[name][fb][key] - cache[name][0][key]).length * 1000.0
            print("   %-12s %s  f0->f%-3d = %8.2f mm  (y: %+7.1f -> %+7.1f)"
                  % (name, key, fb, d,
                     cache[name][0][key].y * 1000.0,
                     cache[name][fb][key].y * 1000.0))

    # ---- 拳心高度带（三支的分离维度之一）---------------------------------
    print("E08_3WAY_HEIGHT (拳心 z 范围，mm)")
    for name in ARMS:
        zs = [cache[name][f]["fistL"].z * 1000.0 for f in range(TOTAL + 1)]
        zr = [cache[name][f]["fistR"].z * 1000.0 for f in range(TOTAL + 1)]
        print("   %-12s zL %.1f ~ %.1f | zR %.1f ~ %.1f"
              % (name, min(zs), max(zs), min(zr), max(zr)))


main()
