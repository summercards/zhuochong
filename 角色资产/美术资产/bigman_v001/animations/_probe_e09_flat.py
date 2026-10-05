"""E09 伏地段参数网格探针（诊断用，不是生产件）。

为什么需要它：`dft_knee_path_ok` 盯「前扑段膝关节世界 z」，`dft_body_ground_ok`
盯「伏地全身最低件」。两者都随 (髋 z, 踝目标 y, 踝目标 z) 联动，靠猜参数撞不出来。

做法：**直接复用生产版 `D.dft_pose`**（保证几何与生产逐位一致），只把
`lock_feet` 的外环膝伺服换成 no-op —— 伺服本身会改踝目标 y，先量**纯几何**映射，
再由伺服做残余修正。

用法：
    PROF_FRAMES=70 HIPZ=0.100,0.112 ANKY=0.700,0.720 ANKZ=0.100,0.140 \
      "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python _probe_e09_flat.py
"""
import json
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anim_lib as A          # noqa: E402
import anim_defeat as D       # noqa: E402

FRAMES = [int(x) for x in os.environ.get("PROF_FRAMES", "70").split(",")]
HIPS_Z = [float(x) for x in os.environ.get(
    "HIPZ", "0.100,0.106,0.112,0.118").split(",")]
ANK_Y = [float(x) for x in os.environ.get("ANKY", "0.700,0.715,0.730").split(",")]
ANK_Z = [float(x) for x in os.environ.get("ANKZ", "0.100,0.120,0.140").split(",")]
USE_SERVO = os.environ.get("PROBE_SERVO", "0") == "1"

_ORIG_LOCK = D.lock_feet


def _lock_no_servo(arm, pose, want, fp_deg, iters=8, damp=0.85, knee_z=None):
    return _ORIG_LOCK(arm, pose, want, fp_deg, iters=iters, damp=damp,
                      knee_z=None)


if not USE_SERVO:
    D.lock_feet = _lock_no_servo

arm, meshes = D.boot()
_TERM_LOC = D.TERM["@loc"]["pelvis"]

for hz in HIPS_Z:
    D.TERM["@loc"] = {"pelvis": A.wloc(0.0, D.TERM_PELVIS_Y, hz - 0.900)}
    for ay in ANK_Y:
        for az in ANK_Z:
            D.PRONE_ANKLE_Y = ay
            D.PRONE_ANKLE_Z = az
            for fr in FRAMES:
                A.apply_pose(arm, D.dft_pose(arm, fr))
                prof = D.body_low_profile()
                knee = {s: A.bone_world(arm, "shin." + s, "head")
                        for s in D.SIDES}
                ank = {s: A.bone_world(arm, "foot." + s, "head")
                       for s in D.SIDES}
                hip = {s: A.bone_world(arm, "thigh." + s, "head")
                       for s in D.SIDES}
                low3 = sorted(prof.items(), key=lambda kv: kv[1])[:4]
                print("E09_FLAT " + json.dumps({
                    "frame": fr,
                    "breath_br": round(D.breath_env(fr), 4),
                    "hip_z": round(hz * 1000.0, 1),
                    "ank_y": round(ay * 1000.0, 1),
                    "ank_z": round(az * 1000.0, 1),
                    "knee_z": round(min(knee[s].z for s in D.SIDES) * 1000.0, 2),
                    "sternum_z": round(A.bone_world(arm, "neck", "head").z
                                       * 1000.0, 2),
                    "ank_z_real": round(min(ank[s].z for s in D.SIDES) * 1000.0, 1),
                    "ank_y_real": round(min(ank[s].y for s in D.SIDES) * 1000.0, 1),
                    "low4": [(k, round(v, 1)) for k, v in low3],
                    "body_low": round(min(prof.values()), 2),
                    "body_low_at": min(prof.items(), key=lambda kv: kv[1])[0],
                    "reach": round(max((Vector(ank[s]) - Vector(hip[s])).length
                                       for s in D.SIDES)
                                   / (A.L_THIGH + A.L_SHIN), 5),
                }, ensure_ascii=False))
print("E09_FLAT_DONE")
