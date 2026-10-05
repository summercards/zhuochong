"""probe_turn —— A07 `Turn` 专用标定：转身主轴（yaw）与"朝向"的量法。

清单「下一支计划 —— A07」的注意第一条写明：
    yaw 是本支唯一的主轴，但 rig_axis_map.md 只标到 28 根主控骨的 x/y/z ——
    先用 probe_axes.py 补测骨盆 yaw（局部哪根轴 = 世界 Z 旋转）再动手，别再靠猜。
    转身是"绕世界 Z 转"，而骨骼局部轴在骨盆已有前倾/侧倾时会偏，
    所以朝向要用 A.bone_world 的**投影**算，不能用 euler 的某个分量直接读。

本探针回答四个问题（全部实测，不推断）：
  Q1 骨盆/胸/头 的 rest 朝向角（投影法）各是多少？
  Q2 `rotation_euler.ry` 是不是世界 Z yaw？加了前倾 rx 之后还准不准？
  Q3 直接给 `pose_bone.matrix`（Rz(yaw)·Rx(pitch)·rest）能不能精确命中 yaw？
  Q4 脊椎链累加：pelvis.ry + spine_01.ry + spine_02.ry + chest.ry 是否 ≈ 胸的世界 yaw？

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python probe_turn.py
"""

import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A  # noqa: E402

# 竖直骨（root/pelvis/spine/chest/neck/head）的静止局部系实测为
#   局部 X = 世界 +X，局部 Y（骨长）= 世界 +Z，局部 Z = 世界 −Y
# （由 rig_axis_map 的 pelvis/chest/head 三行反推，见文件末的推导）。
# 因此"角色朝向"用局部 X 轴在世界 XY 平面里的方位角来量：
#   rest 时 X_local = +X  ⟹ 方位角 0°；绕世界 Z 转 +90° 后 X_local = +Y ⟹ 90°。


def heading_deg(arm, name):
    """骨的世界朝向（偏航角，度）。用**横向参考轴**（局部 X）的投影算。

    为什么不能用"某个 euler 分量直接读"：局部轴在父链有前倾/侧倾时会偏，
    `pelvis.ry` 只是在**局部**绕骨长轴转，它不是严格的"绕世界 Z 转多少度"。
    """
    basis = arm.pose.bones[name].matrix.to_3x3()
    vector = basis @ Vector((1.0, 0.0, 0.0))
    return math.degrees(math.atan2(vector.y, vector.x))


def set_free(arm):
    if arm.animation_data:
        arm.animation_data.action = None
    A.reset_pose(arm)
    bpy.context.view_layer.update()


def set_euler(arm, name, rx=0.0, ry=0.0, rz=0.0):
    set_free(arm)
    arm.pose.bones[name].rotation_euler = (math.radians(rx), math.radians(ry),
                                           math.radians(rz))
    bpy.context.view_layer.update()


def set_matrix_yaw(arm, name, yaw, pitch=0.0, roll=0.0):
    """把骨的世界朝向设成 Rz(yaw)·Rx(pitch)·Ry(roll)·rest（只改朝向，不动位置）。"""
    set_free(arm)
    pose_bone = arm.pose.bones[name]
    rest = pose_bone.bone.matrix_local.to_3x3()
    target = (Matrix.Rotation(math.radians(yaw), 3, "Z")
              @ Matrix.Rotation(math.radians(pitch), 3, "X")
              @ Matrix.Rotation(math.radians(roll), 3, "Y")
              @ rest).to_4x4()
    target.translation = pose_bone.matrix.translation
    pose_bone.matrix = target
    bpy.context.view_layer.update()
    return tuple(round(math.degrees(v), 4) for v in pose_bone.rotation_euler)


def main():
    arm, _meshes = A.open_animation_project()
    set_free(arm)

    near_rest = {name: round(heading_deg(arm, name), 4)
                 for name in ("pelvis", "spine_01", "spine_02", "chest",
                              "neck", "head")}
    A.report("TURN_PROBE_REST_HEADING", near_rest)

    # Q2：euler ry 与"世界 yaw"的关系，以及前倾 rx 的耦合量
    rows = []
    for rx in (0.0, 4.0, 8.0):
        for ry in (15.0, 45.0, 90.0):
            set_euler(arm, "pelvis", rx=rx, ry=ry)
            rows.append({"rx": rx, "ry": ry,
                         "heading": round(heading_deg(arm, "pelvis"), 4),
                         "err": round(heading_deg(arm, "pelvis") - ry, 4)})
    A.report("TURN_PROBE_EULER_RY", rows)

    # Q3：直接给矩阵能不能精确命中 yaw
    rows = []
    for pitch in (0.0, 4.0, 8.0):
        for yaw in (15.0, 45.0, 90.0):
            euler = set_matrix_yaw(arm, "pelvis", yaw, pitch=pitch)
            rows.append({"yaw": yaw, "pitch": pitch,
                         "heading": round(heading_deg(arm, "pelvis"), 4),
                         "err": round(heading_deg(arm, "pelvis") - yaw, 4),
                         "euler_deg": euler})
    A.report("TURN_PROBE_MATRIX", rows)

    # Q4：脊椎链累加是否等于胸的世界 yaw（本项目惯用的近似）
    rows = []
    for twist in (6.0, 12.0):
        set_free(arm)
        arm.pose.bones["pelvis"].rotation_euler = (math.radians(4.0), 0.0, 0.0)
        for name, share in (("spine_01", 0.30), ("spine_02", 0.30),
                            ("chest", 0.40)):
            arm.pose.bones[name].rotation_euler = (
                math.radians(2.0), math.radians(twist * share), 0.0)
        bpy.context.view_layer.update()
        rows.append({"spine_total_deg": twist,
                     "chest_heading": round(heading_deg(arm, "chest"), 4)})
    A.report("TURN_PROBE_CHAIN", rows)

    # 竖直骨的 rest 局部系（证明"局部 X = 世界 +X"）
    rows = {}
    for name in ("pelvis", "chest", "head"):
        basis = arm.pose.bones[name].bone.matrix_local.to_3x3()
        rows[name] = {"local_X_world": [round(v, 4) for v in basis.col[0]],
                      "local_Y_world": [round(v, 4) for v in basis.col[1]],
                      "local_Z_world": [round(v, 4) for v in basis.col[2]]}
    A.report("TURN_PROBE_LOCAL_FRAME", rows)


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("TURN_PROBE_FAILURE " + traceback.format_exc())
