"""probe_e11_leg —— E11 腿部几何标定探针（**开工必做**，清单 §1 风险 4）。

首跑 `anim_revive.py` 把两个结构性错误暴露了出来：

  · `rvw_knee_path_ok` 红：R 膝在 **f56 掉到 −112.7 mm**（膝穿地 0.21 m）。
  · `rvw_body_band_ok` 红：最低件 −208.35 mm（f56 `Trouser_R`），
    且 f28~f48 期间 **左鞋** 常驻 −19 ~ −22 mm。

本探针把「**R 踝目标 (y,z) ↔ 膝 z ↔ 髋**」的映射表打出来，
并量「**左鞋 sole 深度 ↔ 脚 roll**」——这两个映射决定了参数该怎么改。

    SKIP_RENDER 无关；输出 `_e11_leg_probe.log`
"""

import json
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A              # noqa: E402
import anim_death as D            # noqa: E402
import anim_revive as RV          # noqa: E402

SIDES = ("L", "R")
FRAMES = (0, 30, 44, 48, 52, 56, 60, 64, 68, 72, 76, 84, 92, 100, 104)


def torso_pose(arm, frame):
    """只装配**躯干部分**（骨盆 + 脊椎 + 头 + 肩）—— 腿留给扫描用。"""
    py, pz, prx = RV._pwl(RV.PELVIS_KEYS, frame)
    pose = {"pelvis": (prx, 0.0, 0.0)}
    for bone in ("spine_01", "spine_02", "chest", "neck"):
        pose[bone] = (RV._pwl(RV.TORSO_KEYS[bone], frame), 0.0, 0.0)
    pose["head"] = (RV._pwl(RV.TORSO_KEYS["head_rx"], frame),
                    RV._pwl(RV.TORSO_KEYS["head_ry"], frame), 0.0)
    sh = RV._pwl(RV.TORSO_KEYS["shoulder"], frame)
    pose["shoulder.L"] = (sh, 0.0, 0.0)
    pose["shoulder.R"] = (sh, 0.0, 0.0)
    pose["@loc"] = {"pelvis": A.wloc(0.0, py, pz - 0.900)}
    pose["root"] = (0.0, 0.0, 0.0)
    pose.update(A.FIST)
    return pose


def main():
    arm, meshes = RV.boot()
    A.setup_scene()

    # ---------------- ① 髋的世界位置（躯干单独驱动）------------------------
    hip_tab = {}
    for frame in FRAMES:
        A.apply_pose(arm, torso_pose(arm, frame))
        hip_tab[frame] = {s: A.bone_world(arm, "thigh." + s, "head")
                          for s in SIDES}
        print("E11L_HIP f=%3d L=[%s] R=[%s]"
              % (frame,
                 ", ".join("%+.4f" % v for v in hip_tab[frame]["L"]),
                 ", ".join("%+.4f" % v for v in hip_tab[frame]["R"])))

    # ---------------- ② R 踝目标 (y,z) → 膝 z（三种极点）------------------
    POLES = {
        "fwd": (0.0, -1.0, 0.0),
        "dn": (0.0, 0.0, -1.0),
        "up": (0.0, 0.0, 1.0),
        "fwd_dn": (0.0, -0.7071, -0.7071),
        "fwd_up": (0.0, -0.7071, 0.7071),
        "bk_dn": (0.0, 0.7071, -0.7071),
    }
    for frame in (44, 52, 60, 68, 72, 76, 84, 92, 100, 104):
        A.apply_pose(arm, torso_pose(arm, frame))
        hip = Vector(hip_tab[frame]["R"])
        rows = []
        for ay in (-0.20, 0.00, 0.20, 0.36, 0.52, 0.68, 0.84, 1.00):
            for az in (0.08, 0.12, 0.18):
                tgt = Vector((-0.145, ay, az))
                line = []
                for tag, pole in POLES.items():
                    _du, _df, knee, clip = RV._safe_leg_solve(hip, tgt, pole)
                    line.append("%s=%+.0f%s" % (tag, knee.z * 1000.0,
                                                "C" if clip else ""))
                rows.append("   y=%+.2f z=%.2f | %s" % (ay, az, " ".join(line)))
        print("E11L_KNEEMAP f=%d hipR=[%.3f,%.3f,%.3f]\n%s"
              % (frame, hip[0], hip[1], hip[2], "\n".join(rows)))

    # ---------------- ③ 左鞋 sole 深度 ↔ 脚 roll --------------------------
    #   口径：把左踝放在 z=0.20（悬空），量 sole 最低点到踝的距离；
    #   ⟹ 想要 sole 落在 [0, +6] mm，踝 z 就取该深度。
    A.apply_pose(arm, torso_pose(arm, 72))
    for roll in (0.0, 6.0, 15.0, 30.0, 45.0):
        for fp in (0.0, -8.0, -15.0):
            A.apply_pose(arm, torso_pose(arm, 72))
            _du, _df, knee, _c = RV._safe_leg_solve(
                Vector(hip_tab[72]["L"]), Vector((0.145, -0.170, 0.200)),
                Vector((0.0, -1.0, 0.0)))
            pose = {"thigh.L": A.aim_bone(arm, "thigh.L", _du)}
            A.apply_pose(arm, torso_pose(arm, 72))
            pose["thigh.L"] = A.aim_bone(arm, "thigh.L", _du)
            A.apply_pose(arm, {**torso_pose(arm, 72), **pose})
            pose["shin.L"] = A.aim_bone(arm, "shin.L", _df)
            A.apply_pose(arm, {**torso_pose(arm, 72), **pose})
            pose["foot.L"] = D.keep_foot_orient(arm, "foot.L", fp, roll)
            A.apply_pose(arm, {**torso_pose(arm, 72), **pose})
            ankle = A.bone_world(arm, "foot.L", "head").z * 1000.0
            sole = RV._sole_low_mm()["L"]
            print("E11L_SOLE roll=%5.1f fp=%6.1f -> ankle=%.2f sole=%.2f "
                  "depth=%.2f mm" % (roll, fp, ankle, sole, ankle - sole))

    print("E11L_DONE")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("E11L_FAILURE " + traceback.format_exc())
