"""E02 诊断：查清两处红门禁的真实成因（不猜）。

红 ①：`hand_leg_no_clip_ok=False`，`hand_leg_clearance_mm=-56.3` @ f21
红 ②：`no_snap_stop_ok=False`，`no_snap_stop_step_deg=12.9392` @ [114, forearm.R]

本脚本输出：
  (A) 臂三骨（upperarm/forearm/hand .R）在 0~25 与 96~120 帧的 euler 值 + B(f)
      —— 判断 12.94°/帧 是「真的摆得快」还是「euler 表示跳变」。
  (B) 全帧 euler 逐帧最大步（与 `_worst_step` 同口径）+ 该处 BASE→IK 的表示差。
  (C) f=21/22/60/98/114 的臂链与腿链世界坐标 + 最小穿模点的归属。
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("SKIP_RENDER", "1")

from mathutils import Vector  # noqa: E402

import anim_lib as A            # noqa: E402
import anim_exhausted as EX     # noqa: E402


def clearance_detail(arm):
    pts = []
    for side in ("L", "R"):
        for name in EX.ARM_BONES:
            h = Vector(A.bone_world(arm, name, "head"))
            t = Vector(A.bone_world(arm, name, "tail"))
            for i in range(9):
                pts.append((name, side, i / 8.0, h.lerp(t, i / 8.0)))
    best = (1e9, None, None)
    for side in ("L", "R"):
        for bone_name, radius in (("thigh." + side, EX.LEG_THIGH_R),
                                  ("shin." + side, EX.LEG_SHIN_R)):
            a = Vector(A.bone_world(arm, bone_name, "head"))
            b = Vector(A.bone_world(arm, bone_name, "tail"))
            ab = b - a
            for name, sd, tt, p in pts:
                u = 0.0 if ab.length_squared < 1e-12 else max(
                    0.0, min(1.0, (p - a).dot(ab) / ab.length_squared))
                d = (p - (a + ab * u)).length - radius
                if d < best[0]:
                    best = (round(d * 1000.0, 2),
                            "%s[%s] t=%.2f vs %s u=%.2f" % (name, sd, tt,
                                                            bone_name, u), None)
    return best


def main():  # noqa: C901
    arm, _meshes = EX.boot()

    print("DIAG_A euler_continuity")
    for frame in list(range(0, 26)) + list(range(96, 121)):
        pose = EX.exh_pose(arm, frame)
        b = EX.bend_env(frame)
        seg = []
        for name in ("upperarm.R", "forearm.R", "hand.R"):
            e = pose.get(name, (0.0, 0.0, 0.0))
            seg.append("%s=(%7.2f,%7.2f,%7.2f)"
                       % (name.split(".")[0],
                          math.degrees(e[0]), math.degrees(e[1]),
                          math.degrees(e[2])))
        print("f=%3d B=%.4f %s" % (frame, b, " ".join(seg)))

    print("DIAG_B worst_step")
    poses = {f: EX.exh_pose(arm, f) for f in range(EX.START, EX.END + 1)}
    worst = (0.0, None)
    for f in range(EX.START + 1, EX.END + 1):
        ea, eb = poses[f - 1], poses[f]
        for name in (set(ea) | set(eb)) - {"@loc"}:
            va = ea.get(name, (0.0, 0.0, 0.0))
            vb = eb.get(name, (0.0, 0.0, 0.0))
            step = max(abs(x - y) for x, y in zip(va, vb))
            if step > worst[0]:
                worst = (round(math.degrees(step), 4), (f, name,
                            round(math.degrees(va[0]), 2),
                            "->", round(math.degrees(vb[0]), 2)))
    print("worst_step_deg=%s" % (worst,))
    # 只看臂：哪些骨、哪些帧步最大（按帧列出）
    print("  arm steps by frame (deg/frame, worst component):")
    for f in range(EX.START + 1, EX.END + 1):
        if f not in list(range(1, 26)) + list(range(96, 121)):
            continue
        ea, eb = poses[f - 1], poses[f]
        row = []
        for name in EX.ARM_BONES:
            va = ea.get(name, (0.0, 0.0, 0.0))
            vb = eb.get(name, (0.0, 0.0, 0.0))
            st = max(abs(x - y) for x, y in zip(va, vb))
            row.append("%s=%6.2f" % (name.split(".")[0][:5] + name[-2:],
                                     math.degrees(st)))
        print("   f=%3d %s" % (f, " ".join(row)))
    # BASE 臂 vs 全弯 IK 臂的表示差（判断是不是 euler 绕了一整圈）
    A.apply_pose(arm, poses[EX.END])
    ik = dict(poses[EX.END])
    EX.seat_arm(arm, ik, {s: EX.fist_target(arm, s) for s in ("L", "R")})
    for name in ("upperarm.R", "forearm.R", "hand.R"):
        base = poses[EX.END].get(name, (0.0, 0.0, 0.0))
        full = ik.get(name, (0.0, 0.0, 0.0))
        print("  %-12s base=(%8.2f,%8.2f,%8.2f) ik=(%8.2f,%8.2f,%8.2f)"
              % (name, math.degrees(base[0]), math.degrees(base[1]),
                 math.degrees(base[2]), math.degrees(full[0]),
                 math.degrees(full[1]), math.degrees(full[2])))

    print("DIAG_C geometry")
    for frame in (21, 22, 60, 98, 114):
        pose = EX.exh_pose(arm, frame)
        A.apply_pose(arm, pose)
        print("--- frame %d  limb_clearance=%.2f mm  min@%s"
              % (frame, EX.limb_clearance(arm), clearance_detail(arm)[1]))
        for side in ("L", "R"):
            sh = Vector(A.bone_world(arm, "upperarm." + side, "head"))
            el = Vector(A.bone_world(arm, "forearm." + side, "head"))
            hd = Vector(A.bone_world(arm, "hand." + side, "tail"))
            wp = Vector(A.bone_world(arm, "hand." + side, "head"))
            hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
            kn = Vector(A.bone_world(arm, "shin." + side, "head"))
            print("   %s sh=%s el=%s wrist=%s fist=%s"
                  % (side, [round(v * 1000, 1) for v in sh],
                     [round(v * 1000, 1) for v in el],
                     [round(v * 1000, 1) for v in wp],
                     [round(v * 1000, 1) for v in hd]))
            print("      hip=%s knee=%s  fist-knee=%.1f"
                  % ([round(v * 1000, 1) for v in hip],
                     [round(v * 1000, 1) for v in kn],
                     (hd - kn).length * 1000.0))


if __name__ == "__main__":
    main()
