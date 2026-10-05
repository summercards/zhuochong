"""probe_translate —— 标定 pose bone 的 **location 通道**语义。

pose bone 的 `location` 是**骨骼局部空间**的平移，而骨骼局部 Y 轴沿骨长方向
（root/pelvis/脊椎都朝上），所以 `location = (0, 0.1, 0)` 推到世界里很可能是
**竖直向上 0.1 m** 而不是沿 Y 走。重心升降全靠这个通道，不能猜。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python probe_translate.py
"""

import os

import bpy

OUT_DIR = os.path.abspath(
    r"I:/工作项目/BIGMANFIGHT/角色资产/美术资产/bigman_v001")
BLEND_PATH = os.path.join(OUT_DIR, "bigman_tpose_v001.blend")

STEP = 0.10


def clear_pose(arm):
    for pose_bone in arm.pose.bones:
        pose_bone.rotation_euler = (0.0, 0.0, 0.0)
        pose_bone.location = (0.0, 0.0, 0.0)
        pose_bone.scale = (1.0, 1.0, 1.0)
    bpy.context.view_layer.update()


def main():
    bpy.ops.wm.open_mainfile(filepath=BLEND_PATH)
    arm = bpy.data.objects["Character_Rig"]

    for name in ("root", "pelvis", "chest"):
        clear_pose(arm)
        base = arm.matrix_world @ arm.pose.bones[name].head
        for index, axis in enumerate("XYZ"):
            clear_pose(arm)
            vector = [0.0, 0.0, 0.0]
            vector[index] = STEP
            arm.pose.bones[name].location = vector
            bpy.context.view_layer.update()
            moved = (arm.matrix_world @ arm.pose.bones[name].head) - base
            print("LOC %-9s local_%s -> world dx=%+7.1f dy=%+7.1f dz=%+7.1f mm"
                  % (name, axis, moved.x * 1000.0, moved.y * 1000.0,
                     moved.z * 1000.0))
    clear_pose(arm)
    print("PROBE_TRANSLATE_DONE")


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("PROBE_TRANSLATE_FAILURE " + traceback.format_exc())
