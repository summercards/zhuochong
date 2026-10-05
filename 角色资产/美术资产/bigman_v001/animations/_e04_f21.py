"""E04 f=21 手骨步长归因：把 hand 的矩阵步长拆成
  · 前臂自身世界旋转步长
  · hand 相对前臂的**局部**步长（= 滚转贡献）
  · y_dir 变化率 / hint 变化率
"""
import os
import sys
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy                                     # noqa: E402
from mathutils import Vector, Matrix           # noqa: E402
import anim_lib as A                           # noqa: E402
import anim_spawn as S                         # noqa: E402

F0 = int(os.environ.get("F0", "16"))
F1 = int(os.environ.get("F1", "27"))


def colstep(a, b):
    worst = 0.0
    for c in range(3):
        va, vb = a.col[c].normalized(), b.col[c].normalized()
        d = math.degrees(math.acos(max(-1.0, min(1.0, va.dot(vb)))))
        worst = max(worst, d)
    return worst


def main():
    arm, meshes = S.boot()
    kfs = [(f, S.spawn_pose(arm, f)) for f in range(S.START, S.END + 1)]
    kfs = S.compat_euler(kfs)
    kfs = S.seam_canonicalize(kfs)
    action, meta = A.build_action(arm, S.NAME + "_F21", kfs, meta={"anim_id": S.NAME, "loop": False})

    prev = {}
    print("frame  handM  foreM  upM  | hLoc  fLoc  | dUp dFo dSW  reach")
    for f in range(F0, F1 + 1):
        bpy.context.scene.frame_set(f)
        bpy.context.view_layer.update()
        cur = {n: arm.pose.bones[n].matrix.copy() for n in
               ("hand.L", "forearm.L", "upperarm.L")}
        loc = {}
        for n in ("hand.L", "forearm.L"):
            parent = {"hand.L": "forearm.L", "forearm.L": "upperarm.L"}[n]
            pb = arm.pose.bones[n]
            loc[n] = pb.matrix.to_3x3() @ arm.pose.bones[parent].matrix.to_3x3().inverted()
        row = {}
        for n in ("hand.L", "forearm.L", "upperarm.L"):
            row[n + "_w"] = cur[n].to_3x3()
        for n in ("hand.L", "forearm.L"):
            row[n + "_l"] = loc[n]
        # 骨段世界方向（head→tail）与肘角
        sh = Vector(arm.pose.bones["upperarm.L"].head)
        el = Vector(arm.pose.bones["forearm.L"].head)
        wr = Vector(arm.pose.bones["hand.L"].head)
        row["d_up"] = (el - sh).normalized()
        row["d_fo"] = (wr - el).normalized()
        row["d_sh_wr"] = (wr - sh).normalized()
        row["reach"] = (wr - sh).length
        row["sh"] = sh.copy()
        if prev:
            hm = colstep(prev["hand.L_w"], row["hand.L_w"])
            fm = colstep(prev["forearm.L_w"], row["forearm.L_w"])
            um = colstep(prev["upperarm.L_w"], row["upperarm.L_w"])
            hl = colstep(prev["hand.L_l"], row["hand.L_l"])
            fl = colstep(prev["forearm.L_l"], row["forearm.L_l"])
            du = math.degrees(math.acos(max(-1.0, min(1.0, prev["d_up"].dot(row["d_up"])))))
            df = math.degrees(math.acos(max(-1.0, min(1.0, prev["d_fo"].dot(row["d_fo"])))))
            ds = math.degrees(math.acos(max(-1.0, min(1.0, prev["d_sh_wr"].dot(row["d_sh_wr"])))))
            print("%5d  %6.2f %6.2f %6.2f | %6.2f %6.2f | dUp%6.2f dFo%6.2f dSW%6.2f reach%6.3f  sh(%.3f,%.3f,%.3f)" %
                  (f, hm, fm, um, hl, fl, du, df, ds, row["reach"], row["sh"].x, row["sh"].y, row["sh"].z))
        prev = row


if __name__ == "__main__":
    main()
