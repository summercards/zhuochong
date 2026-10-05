"""一次性探针：量 D03 `Guard_Hit` 的**膝关节角度**与**小腿/踝**可见变化。

背景：门禁只钉了踝（`plant_mm` 0.001 mm）与脚底贴地（`ground_min` −1.33 mm），
但清单 §4.4 的目检项写的是「拳要往脸靠近、上身后仰、**膝盖角度不变**」。
骨盆下沉 14 mm 由腿 IK 吸收 ⟹ 膝**必然**微弯，需要知道弯了多少度、
以及它在画面里表现为「裤腿遮挡鞋面」还是「脚真动了」。

用法：
  "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" --background \
      --factory-startup --python probe_d03_knee.py
"""
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anim_lib as A  # noqa: E402

NAME = "Guard_Hit"
FRAMES = [0, 2, 4, 6, 14, 32, 36]


def bone_pair_deg(arm, parent, child):
    """膝角 = 大腿骨轴 与 小腿骨轴 的夹角（度）。0 = 完全伸直。"""
    d1 = Vector(A.bone_direction(arm, parent)).normalized()
    d2 = Vector(A.bone_direction(arm, child)).normalized()
    return math.degrees(math.acos(max(-1.0, min(1.0, d1.dot(d2)))))


def main():
    bpy.ops.wm.open_mainfile(filepath=A.ANIM_BLEND)
    arm = bpy.data.objects["Armature"] if "Armature" in bpy.data.objects else None
    if arm is None:
        for ob in bpy.data.objects:
            if ob.type == "ARMATURE":
                arm = ob
                break
    scene = bpy.context.scene
    action = bpy.data.actions.get(NAME)
    if action is None:
        print("PROBE_D03_KNEE NO_ACTION %s" % NAME)
        return
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action

    rows = []
    for frame in FRAMES:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        row = {"frame": frame}
        for side in ("L", "R"):
            row["knee." + side] = round(
                bone_pair_deg(arm, "thigh." + side, "shin." + side), 3)
            row["ankle." + side] = round(
                bone_pair_deg(arm, "shin." + side, "foot." + side), 3)
            row["foot_z." + side] = round(
                Vector(A.bone_world(arm, "foot." + side, "head")).z * 1000.0, 3)
            row["foot_y." + side] = round(
                Vector(A.bone_world(arm, "foot." + side, "head")).y * 1000.0, 3)
            row["knee_y." + side] = round(
                Vector(A.bone_world(arm, "shin." + side, "head")).y * 1000.0, 3)
            row["knee_z." + side] = round(
                Vector(A.bone_world(arm, "shin." + side, "head")).z * 1000.0, 3)
        rows.append(row)

    zero = rows[0]
    print("PROBE_D03_KNEE_BEGIN")
    for row in rows:
        print("frame=%2d  knee L/R = %7.3f / %7.3f  (Δ %+6.3f / %+6.3f)   "
              "foot_z L/R = %8.3f / %8.3f   foot_y Δ = %+6.3f / %+6.3f"
              % (row["frame"], row["knee.L"], row["knee.R"],
                 row["knee.L"] - zero["knee.L"], row["knee.R"] - zero["knee.R"],
                 row["foot_z.L"], row["foot_z.R"],
                 row["foot_y.L"] - zero["foot_y.L"],
                 row["foot_y.R"] - zero["foot_y.R"]))
    worst = 0.0
    worst_f = None
    for row in rows:
        for side in ("L", "R"):
            d = abs(row["knee." + side] - zero["knee." + side])
            if d > worst:
                worst, worst_f = d, (row["frame"], side)
    print("PROBE_D03_KNEE_WORST_DEG %.4f at frame=%s" % (worst, worst_f))
    print("PROBE_D03_KNEE_END")


if __name__ == "__main__":
    main()
