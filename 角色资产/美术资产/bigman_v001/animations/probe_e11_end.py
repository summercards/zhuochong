"""probe_e11_end —— E11 **收势段**「解算腿 vs `Idle_01@0`」逐骨标定。

★ 要回答的问题（首跑读数 `no_snap_stop_step_deg = 26.368 @ (120, 'shin.R')`）：
  E11 在 `[STAND_START, END]` 段**所有参数表都恒定**（骨盆 / 躯干 / 踝目标 /
  膝高 / 脚朝向全取端点值）⟹ 解算姿态逐帧相同；而末帧被 `END_POSE`
  （`Idle_01@0` 逐位）替换。所以这 26.4° **全部**来自「解算腿 ≠ 待机腿」。
  但「差 26°」有两种完全不同的性质，必须分开：
    ① **关节点世界位置**不同 ⟹ 真的摆错了地方（几何问题，改参数）；
    ② 位置相同、只有**骨世界朝向**不同 ⟹ 只是绕骨轴的自转（`aim_bone` 不控
       twist）；③ 位置与朝向都相同、只有**欧拉分量**不同 ⟹ 门禁量错了维度。

  探针把三样一起打出来（位置 mm / 朝向 deg / 欧拉 deg），据此决定改哪一样。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python probe_e11_end.py
"""

import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A            # noqa: E402
import anim_revive as RV        # noqa: E402

LEG = ("thigh.L", "shin.L", "foot.L", "toe.L",
       "thigh.R", "shin.R", "foot.R", "toe.R")


def _snap(arm):
    return {
        "pos": {n: Vector(A.bone_world(arm, n, "head")) for n in LEG},
        "dir": {n: Vector(A.bone_direction(arm, n)) for n in LEG},
        "eul": {n: tuple(math.degrees(v) for v in
                         arm.pose.bones[n].rotation_euler) for n in LEG},
    }


def _cmp(cur, ref, tag):
    worst = (0.0, None)
    for name in LEG:
        dp = (cur["pos"][name] - ref["pos"][name]).length * 1000.0
        dd = math.degrees(math.acos(max(-1.0, min(
            1.0, cur["dir"][name].dot(ref["dir"][name])))))
        de = max(abs(a - b) for a, b in zip(cur["eul"][name], ref["eul"][name]))
        if de > worst[0]:
            worst = (de, name)
        print("E11E_%-8s %-9s dpos=%8.3f mm  ddir=%7.3f deg  deul=%8.3f deg"
              % (tag, name, dp, dd, de))
    print("E11E_%-8s WORST deul=%.3f deg @ %s" % (tag, worst[0], worst[1]))


def _geo(hip, tgt, knee_z, tag):
    """腿的两骨解几何：a / h / 矢状面两支的膝高。"""
    L1, L2 = RV.L1, RV.L2
    d = Vector(tgt) - Vector(hip)
    dist = d.length
    limit = (L1 + L2) * RV.D.REACH_MAX_RATIO
    dist = max(min(dist, limit), abs(L1 - L2) + 1e-4)
    u = d.normalized()
    a = (L1 * L1 - L2 * L2 + dist * dist) / (2.0 * dist)
    h = math.sqrt(max(0.0, L1 * L1 - a * a))
    s = math.hypot(u.y, u.z)
    base = Vector((0.0, u.z, -u.y)) / s if s > 1e-9 else Vector((0.0, -1.0, 0.0))
    k_plus = hip.z + u.z * a + base.z * h
    k_minus = hip.z + u.z * a - base.z * h
    print("E11E_GEO %-6s hip=(%+.4f,%+.4f,%+.4f) tgt=(%+.4f,%+.4f,%+.4f) "
          "dist=%.4f a=%.4f h=%.4f  u=(%+.3f,%+.3f,%+.3f) n=(%+.3f,%+.3f,%+.3f)"
          % (tag, hip.x, hip.y, hip.z, tgt.x, tgt.y, tgt.z, dist, a, h,
             u.x, u.y, u.z, base.x, base.y, base.z))
    print("E11E_GEO %-6s 支+ 膝z=%.4f  支− 膝z=%.4f  目标=%.4f"
          % (tag, k_plus, k_minus, knee_z))


def main():
    arm, _meshes = RV.boot()

    A.apply_pose(arm, RV.END_POSE)
    bpy.context.view_layer.update()
    idle = _snap(arm)
    print("E11E_IDLE pos: " + " ".join(
        "%s=(%+.4f,%+.4f,%+.4f)" % (n, idle["pos"][n].x, idle["pos"][n].y,
                                    idle["pos"][n].z) for n in LEG))
    print("E11E_IDLE eul: " + " ".join(
        "%s=(%+8.3f,%+8.3f,%+8.3f)" % ((n,) + idle["eul"][n]) for n in LEG))

    snaps = {}
    for frame in (88, 96, 104, 110, 119, 120):
        RV.revive_pose(arm, frame)
        bpy.context.view_layer.update()
        snaps[frame] = _snap(arm)
        _cmp(snaps[frame], idle, "f%d" % frame)
        if 104 in snaps:
            d = max(abs(a - b) for n in LEG
                    for a, b in zip(snaps[frame]["eul"][n],
                                    snaps[104]["eul"][n]))
            print("E11E_STEP f104->f%-4d deul_max=%8.3f deg" % (frame, d))
    if 120 in snaps and 119 in snaps:
        d = max(abs(a - b) for n in LEG
                for a, b in zip(snaps[120]["eul"][n], snaps[119]["eul"][n]))
        print("E11E_STEP f119->f120 deul_max=%8.3f deg" % d)

    for frame in (0, 16, 30, 44, 58, 72, 84, 92, 104, 120):
        RV.revive_pose(arm, frame)
        bpy.context.view_layer.update()
        _geo(Vector(A.bone_world(arm, "thigh.R", "head")),
             RV._ankle_target(frame, "R"),
             RV._pwl(RV.KNEE_Z_R, frame), "f%d/R" % frame)
        print("E11E_RKO f=%-4d kneeR=%8.2f mm  ankleR=%8.2f mm"
              % (frame,
                 A.bone_world(arm, "shin.R", "head").z * 1000.0,
                 A.bone_world(arm, "foot.R", "head").z * 1000.0))

    print("E11E_DONE")


if __name__ == "__main__":
    main()
