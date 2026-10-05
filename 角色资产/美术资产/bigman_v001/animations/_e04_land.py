"""_e04_land —— 只读：为 E04 落地找「下沉量上限」。

背景（已实测）：
  · 收敛后踝残差 ~1e-4 mm ⟹ 腿**够得到**任何目标，下沉不是可达性问题。
  · 但鞋底会随**膝屈**往下走：膝 42.96° → sole −0.96；膝 71.49° → −2.02；
    膝 84.43° → −2.44（对象一直是 `Shoe_Sole_R`）。
  · E02（`_e04_e02ref.py` 实测）用**对称宽站**在骨盆降 71 mm 时膝只有 56.38°、
    sole −0.90 ⟹ **膝屈才是自变量，站姿几何是调节旋钮**。

本脚本扫「下沉量 × 髋后移」，量膝屈 / 鞋底 / 髋踝距，用来定：
  · `spawn_land_sink_ok` 的下沉量目标值（要够重）
  · 同时鞋底留在门禁带 (−2, +6) 内（§6 硬约束）
"""
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A          # noqa: E402
import anim_idle_01 as IDLE   # noqa: E402

SIDES = ("L", "R")


def lock_feet_final(arm, pose, want, iters=20, damp=0.85):
    tgt = {s: Vector(want[s]) for s in SIDES}
    rz = {s: pose.get("thigh." + s, (0.0, 0.0, 0.0))[2] for s in SIDES}
    pelvis_rx = pose.get("pelvis", (0.0, 0.0, 0.0))[0]
    last = 0.0
    for _it in range(iters):
        A.apply_pose(arm, pose)
        for side in SIDES:
            hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
            th, sh = A.leg_ik(hip.y, hip.z, tgt[side].y, tgt[side].z,
                              tilt_deg=pelvis_rx)
            pose["thigh." + side] = (th, 0.0, rz[side])
            pose["shin." + side] = (sh, 0.0, 0.0)
        A.apply_pose(arm, pose)
        for side in SIDES:
            pose["foot." + side] = A.keep_world_orientation(arm, "foot." + side)
        A.apply_pose(arm, pose)
        last = 0.0
        for side in SIDES:
            err = Vector(A.bone_world(arm, "foot." + side, "head")) - want[side]
            tgt[side] = tgt[side] - err * damp
            rz[side] = rz[side] + (1.0 / 0.01309) * err.x * damp
            last = max(last, err.length * 1000.0)
    return last


def build(base, anchor, dz, dy, tilts):
    pose = {}
    for key, value in base.items():
        pose[key] = ({k: tuple(v) for k, v in value.items()}
                     if key.startswith("@") else tuple(value))
    for name, delta in tilts.items():
        cur = pose.get(name, (0.0, 0.0, 0.0))
        pose[name] = (cur[0] + delta, cur[1], cur[2])
    base_loc = pose.get("@loc", {}).get("pelvis", (0.0, 0.0, 0.0))
    off = A.wloc(0.0, dy, dz)
    pose["@loc"] = {"pelvis": tuple(a + b for a, b in zip(base_loc, off))}
    want = {s: Vector(anchor[s]) for s in SIDES}
    return pose, want


# 落地姿态的躯干形态：前倾塌腰（重心压低、读成「砸下来」）
LAND_TILT = {"pelvis": 16.0, "spine_01": 8.0, "spine_02": 8.0, "chest": 5.0,
             "neck": -3.0, "head": -6.0}


def main():
    arm, _m = A.open_animation_project()
    A.setup_scene()
    base = IDLE.idle_pose(arm, 0.0)
    A.apply_pose(arm, base)
    anchor = {s: Vector(A.bone_world(arm, "foot." + s, "head")) for s in SIDES}

    rows = []
    for dy in (0.0, 0.06, 0.12, 0.18):
        for dz in (-0.08, -0.12, -0.16, -0.20, -0.24, -0.28, -0.32):
            pose, want = build(base, anchor, dz, dy, LAND_TILT)
            fin = lock_feet_final(arm, pose, want)
            sole = A.foot_lowest_by_side()
            knee = max(math.degrees(arm.pose.bones["shin." + s].rotation_euler.x)
                       for s in SIDES)
            hip = Vector(A.bone_world(arm, "thigh.L", "head"))
            ank = Vector(A.bone_world(arm, "foot.L", "head"))
            rows.append({"dy_mm": round(dy * 1000.0, 0),
                         "dz_mm": round(dz * 1000.0, 0),
                         "err_mm": round(fin, 5),
                         "knee_deg": round(knee, 2),
                         "hip_ankle_mm": round((hip - ank).length * 1000.0, 1),
                         "sole_mm": round(min(sole["L"][2], sole["R"][2])
                                          * 1000.0, 2)})
    print("E04_LAND " + str(rows).replace("'", '"'))


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("E04_LAND_FAILURE " + traceback.format_exc())
