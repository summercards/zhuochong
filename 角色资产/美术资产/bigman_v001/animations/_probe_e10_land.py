"""_probe_e10_land —— 命中帧附近「鞋为什么陷 9 mm」的定位探针。

现象：`dth_no_penetration_ok`（容差 −8 mm）在 f24 实测 **−9.18 mm**（`Shoe_Sole_L`）。
待查：鞋子到底是**刚体挂在 `foot`**（那就只该随踝平移），还是**部分蒙皮在 `shin`**
（那它就会跟着折叠的小腿扭下去）。
"""
import json
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A       # noqa: E402
import anim_death as D     # noqa: E402

FOOT_NAMES = ("Shoe_Heel_L", "Shoe_Sole_L", "Shoe_Toe_Cap_L", "Shoe_Upper_L",
              "Shoe_Heel_R", "Shoe_Sole_R", "Shoe_Toe_Cap_R", "Shoe_Upper_R")


def group_low(prof, keys):
    vals = [prof[k] for k in keys if k in prof]
    return min(vals) if vals else None


def main():
    arm, _meshes = D.boot()

    # ---- 蒙皮归属：鞋到底挂在哪些骨上 -------------------------------------
    dep = {}
    for name in FOOT_NAMES:
        obj = bpy.data.objects.get(name)
        if obj is None:
            continue
        groups = [g.name for g in obj.vertex_groups]
        dep[name] = {"parents": groups[:8], "nvg": len(groups)}
    print("E10LAND_SKIN %s" % json.dumps(dep, ensure_ascii=False))

    rest_basis = {}
    for n in ("foot.L", "toe.L"):
        rest_basis[n] = [list(row) for row in
                         arm.data.bones[n].matrix_local.to_3x3()]

    for frame in (10, 20, 22, 23, 24, 29, 30, 34, 38, 42, 46, 52, 60):
        D.death_pose(arm, frame)
        prof = D.body_low_profile()
        low8 = sorted(prof.items(), key=lambda kv: kv[1])[:8]
        print("E10LAND f=%3d low8=%s" % (frame,
                                         [(k, round(v, 2)) for k, v in low8]))
        print("    shoeL=%s shoeR=%s trouser=%s"
              % (round(group_low(prof, FOOT_NAMES[:4]), 2),
                 round(group_low(prof, FOOT_NAMES[4:]), 2),
                 round(group_low(prof, [k for k in prof
                                        if "Trouser" in k]), 2)))
        for n in ("shin.L", "foot.L", "toe.L"):
            h = Vector(A.bone_world(arm, n, "head"))
            t = Vector(A.bone_world(arm, n, "tail"))
            cur = arm.pose.bones[n].matrix.to_3x3()
            rb = arm.data.bones[n].matrix_local.to_3x3()
            diff = 0.0
            for i in range(3):
                va, vb = cur.col[i].normalized(), rb.col[i].normalized()
                cos = max(-1.0, min(1.0, va.dot(vb)))
                import math
                diff = max(diff, math.degrees(math.acos(cos)))
            print("    %-8s head=%s tail=%s 朝向差(rest)=%.3f°"
                  % (n, [round(v * 1000.0, 1) for v in h],
                     [round(v * 1000.0, 1) for v in t], diff))
    print("E10LAND_DONE")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("E10LAND_FAILURE " + traceback.format_exc())
