"""E04 诊断 6：定位臂 IK 在 f≈8 的真实不连续源。

打印 f=0..26：
  · 拳目标（世界）、肩、肘、前臂世界方向
  · `pole·axis`（bulge 退化指标）、|bulge|
  · 手网格在躯干体内的非拇指顶点数（穿模相关）
"""
import os
import sys
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy                                     # noqa: E402
from mathutils import Vector                   # noqa: E402
import anim_lib as A                           # noqa: E402
import anim_spawn as S                         # noqa: E402


def main():
    arm, meshes = S.boot()
    print("%-4s %-24s %-24s %-24s %7s %7s %6s %s"
          % ("f", "target_L", "elbow_L", "foreL_dir", "pole.ax", "|bulge|",
             "env", "inL/inR(nt)"))
    for frame in range(0, 27):
        pose = S.spawn_pose(arm, frame)
        A.apply_pose(arm, pose)                     # 落到该帧的最终姿态
        idx, t, kind = S._segment(frame)
        env = S.arm_env(frame)
        spec = S.torso_at(frame)
        dy, dz = spec["loc"]
        root_off = Vector((0.0, dy, dz))
        # 目标（复算，含 push_out）
        tg = {}
        index, tt, kk = S._segment(frame)
        ga = S._ease(kk, tt)
        an = S.KEYS[index][3]
        bn = S.KEYS[index + 1][3]
        for side in S.SIDES:
            va = S.resolve_fist(an, side) + root_off
            vb = S.resolve_fist(bn, side) + root_off
            pt = va.lerp(vb, ga)
            tg[side] = S.push_out(pt, S.FIST_MIN_CLEAR_MM)
        sho = Vector(A.bone_world(arm, "upperarm.L", "head"))
        elb = Vector(A.bone_world(arm, "forearm.L", "head"))
        fore = Vector(A.bone_direction(arm, "forearm.L"))
        tgt = tg["L"]
        along = (tgt - sho)
        along = along.normalized() if along.length > 1e-6 else Vector((0, 0, -1))
        pole = Vector(S.ELBOW_POLE["L"])
        if env < 1.0:
            pole = S._slerp_dir(S.STATION_POLE_DIR["L"], pole, env)
        bulge = pole - along * pole.dot(along)
        # 手 vs 躯干
        S.torso_bvh_reset()
        tree = S.torso_bvh()
        cL = S.hand_mesh_stats("L", tree=tree, step=4)
        cR = S.hand_mesh_stats("R", tree=tree, step=4)
        print("%-4d (%6.3f,%6.3f,%6.3f) (%6.3f,%6.3f,%6.3f) (%5.2f,%5.2f,%5.2f)"
              " %7.3f %7.3f %6.3f  %d/%d"
              % (frame, tgt.x, tgt.y, tgt.z, elb.x, elb.y, elb.z,
                 fore.x, fore.y, fore.z, pole.dot(along), bulge.length, env,
                 cL["inside_nothumb"], cR["inside_nothumb"]))


if __name__ == "__main__":
    main()
