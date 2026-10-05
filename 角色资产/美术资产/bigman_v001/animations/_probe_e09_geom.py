"""E09 腿几何实测探针（诊断用，不是生产件）。

量什么：跪姿 / 伏地两个关键帧上，hip(thigh.head) / knee(shin.head) /
ankle(foot.head) / toe 的**世界坐标**，以及各段骨长、YZ 投影长。
用来把「解析反解」里那几个假设（l1/l2 的 YZ 投影、外展角）换成实测值。

用法：
    PROF_FRAMES=28,46,66,70 \\
      "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python _probe_e09_geom.py
"""
import json
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anim_lib as A          # noqa: E402
import anim_defeat as D       # noqa: E402

FRAMES = [int(x) for x in os.environ.get("PROF_FRAMES", "28,46,66,70").split(",")]

arm, meshes = D.boot()
print("E09_GEOM_LEN L_THIGH=%.6f L_SHIN=%.6f SUM=%.6f"
      % (A.L_THIGH, A.L_SHIN, A.L_THIGH + A.L_SHIN))

for fr in FRAMES:
    pose = D.dft_pose(arm, fr)
    A.apply_pose(arm, pose)
    bpy.context.view_layer.update()
    row = {"frame": fr,
           "k": round(D.kneel_env(fr), 5),
           "p": round(D.fall_env(fr), 5),
           "rest_z": round(D.ANKLE_REST["L"].z * 1000.0, 3),
           "rest_y": round(D.ANKLE_REST["L"].y * 1000.0, 3),
           "rest_x": round(D.ANKLE_REST["L"].x * 1000.0, 3)}
    for bone in ("pelvis", "thigh.L", "shin.L", "foot.L", "toe.L",
                 "thigh.R", "shin.R", "foot.R"):
        h = Vector(A.bone_world(arm, bone, "head"))
        t = Vector(A.bone_world(arm, bone, "tail"))
        row[bone] = {"head": [round(v * 1000.0, 2) for v in h],
                     "tail": [round(v * 1000.0, 2) for v in t],
                     "len": round((t - h).length * 1000.0, 3)}
    # 段长（世界欧氏）与 YZ 投影
    hip = Vector(A.bone_world(arm, "thigh.L", "head"))
    knee = Vector(A.bone_world(arm, "shin.L", "head"))
    ank = Vector(A.bone_world(arm, "foot.L", "head"))
    row["thigh_world"] = round((knee - hip).length * 1000.0, 3)
    row["shin_world"] = round((ank - knee).length * 1000.0, 3)
    row["thigh_yz"] = round(math.hypot(knee.y - hip.y, knee.z - hip.z) * 1000.0, 3)
    row["shin_yz"] = round(math.hypot(ank.y - knee.y, ank.z - knee.z) * 1000.0, 3)
    row["thigh_dx"] = round((knee.x - hip.x) * 1000.0, 3)
    row["shin_dx"] = round((ank.x - knee.x) * 1000.0, 3)
    row["hip_ank_dist"] = round((ank - hip).length * 1000.0, 3)
    row["root_euler_deg"] = [round(math.degrees(v), 3)
                             for v in arm.pose.bones["root"].rotation_euler]
    row["root_loc_mm"] = [round(v * 1000.0, 3)
                          for v in arm.pose.bones["root"].location]
    row["pelvis_euler_deg"] = [round(math.degrees(v), 3)
                               for v in arm.pose.bones["pelvis"].rotation_euler]
    print("E09_GEOM " + json.dumps(row))

print("E09_GEOM_DONE")
