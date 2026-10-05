"""_e03_valid —— 先验证「体内判定」这个**尺子本身**可信，再谈用它量什么。

触发原因：`_e03_sweep.py` 在 `f=96`（收势 = 站架姿）报出 **R 手拇指 280 个顶点
在躯干体内**，且在 TOUCH_OFF = 36/40/44 下**读数完全相同**（那时臂包络已归零，
姿态就是 A01 站架）。两种可能：
  (a) A01 站架本身就穿模（真缺陷，且是**预存**的，与本支无关）；
  (b) `inside_torso` 的**单方向射线奇偶**在**非水密网格**上失效
      （连体衣在脖颈 / 袖口 / 下摆有开孔，射线从孔里穿出 ⟹ 奇偶计数变奇 ⟹ 假阳性）。

本脚本用**已知点**给尺子做校准，并对同一批顶点并排跑三种口径：
  ① `inside_torso`（现状：单一固定方向 (0.3178,0.7512,0.5773)）
  ② **多方向多数表决**（13 个方向，> 半数判"在内"才算在内）
  ③ **正面遮挡**（从顶点沿 −Y 打射线，命中胸壳且距离 ≤ 80 mm ⟹ 该顶点在
     正面机位下**被躯干挡住** = 视觉上的"穿进躯干"）
★ ③ 才是「渲染出来看得见」的那件事；① / ② 只是几何代理。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python _e03_valid.py
"""

import json
import math
import os
import sys

import bpy
import mathutils.bvhtree as bvhtree
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A          # noqa: E402
import anim_rage as R         # noqa: E402

SIDES = ("L", "R")
FRAMES = (0, 20, 26, 28, 44, 52, 60, 66, 96)
DIRS = []
for _i in range(1, 7):
    for _j in range(3):
        _a = 2.0 * math.pi * _j / 3.0
        DIRS.append(Vector((math.cos(_a) * 0.7, math.sin(_a) * 0.7,
                            0.6 if _i % 2 else -0.6)).normalized())
DIRS = DIRS[:13]


def tree():
    deps = bpy.context.evaluated_depsgraph_get()
    return bvhtree.BVHTree.FromObject(R.TORSO, deps)


def parity(t, point, direction):
    origin = Vector(point)
    direction = Vector(direction).normalized()
    hits = 0
    for _ in range(64):
        loc, _n, index, distance = t.ray_cast(origin, direction)
        if loc is None or index is None:
            break
        hits += 1
        origin = loc + direction * max(1e-7, distance * 1e-6 + 1e-7)
    return hits % 2 == 1


def majority(t, point):
    votes = sum(1 for d in DIRS if parity(t, point, d))
    return votes > len(DIRS) / 2.0, votes


def front_hidden(t, point, limit_mm=80.0):
    loc, _n, index, distance = t.ray_cast(Vector(point), Vector((0.0, -1.0, 0.0)))
    if loc is None or index is None:
        return False, None
    mm = distance * 1000.0
    return (mm <= limit_mm), round(mm, 2)


def hand_verts(side, step=2):
    return R.hand_mesh_points(side, step=step)


def scan(arm, tag):
    t = tree()
    out = {}
    for side in SIDES:
        pts = hand_verts(side)
        single = sum(1 for p, _n in pts if R.inside_torso(p))
        maj = 0
        fh = 0
        worst = None
        for p, name in pts:
            ok, _v = majority(t, p)
            maj += 1 if ok else 0
            hid, mm = front_hidden(t, p)
            if hid:
                fh += 1
                if worst is None or mm > worst[0]:
                    worst = (mm, name, [round(c, 4) for c in p])
        palm = [R.signed_to_torso(p) for p, n in pts
                if not n.startswith("Thumb_")]
        core = R.signed_to_torso(Vector(A.bone_world(arm, "hand." + side, "tail")))
        out[side] = {"n": len(pts), "single_dir": single, "majority": maj,
                     "front_hidden": fh, "front_worst": worst,
                     "palm_min_mm": round(min(palm), 2),
                     "core_mm": round(core, 2)}
    print("E03_VALID " + json.dumps({"tag": tag, "sides": out},
                                    ensure_ascii=False))


def main():
    arm, _meshes = R.boot()
    if arm.animation_data:
        arm.animation_data.action = None

    # ---- ① 尺子校准：已知点 -------------------------------------------
    A.apply_pose(arm, dict(R.BASE))
    bpy.context.view_layer.update()
    t = tree()
    nrm = Vector((0.0, -1.0, 0.0))
    _loc, n = R.chest_surface(arm, "L")
    base = Vector(_loc)
    calib = {}
    for label, point, expect in (
            ("chest_bone_head", Vector(A.bone_world(arm, "chest", "head")), "in"),
            ("spine02_head", Vector(A.bone_world(arm, "spine_02", "head")), "in"),
            ("pelvis_head", Vector(A.bone_world(arm, "pelvis", "head")), "in"),
            ("front_surf+0mm", base, "out"),
            ("front_surf+20mm", base + nrm * 0.020, "out"),
            ("front_surf+50mm", base + nrm * 0.050, "out"),
            ("front_surf+100mm", base + nrm * 0.100, "out"),
            ("front_surf+300mm", base + nrm * 0.300, "out"),
            ("far_front_1m", base + nrm * 1.000, "out")):
        ok, votes = majority(t, point)
        calib[label] = {"expect": expect, "single": R.inside_torso(point),
                        "majority": ok, "votes": votes, "n_dirs": len(DIRS),
                        "algo_dir": n.dot(Vector((0.3178, 0.7512, 0.5773)))
                        if label == "chest_bone_head" else None}
    print("E03_VALID_CALIB " + json.dumps(calib, ensure_ascii=False))
    print("E03_VALID_CHEST_SURF " + json.dumps(
        {"loc": [round(c, 4) for c in _loc], "nrm": [round(c, 4) for c in n]},
        ensure_ascii=False))

    # ---- ② 手网格三口径并排 --------------------------------------------
    R.HAND_AXIS_MODE = "thumb_dn"
    R.LAST_ELBOW.clear()
    poses = [(f, R.rage_pose(arm, f)) for f in range(0, R.TOTAL + 1)]
    for frame in FRAMES:
        A.apply_pose(arm, dict(poses[frame][1]))
        bpy.context.view_layer.update()
        R.torso_bvh_reset()
        scan(arm, "f=%d" % frame)
    print("E03_VALID_DONE")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("E03_VALID_FAILURE " + traceback.format_exc())
