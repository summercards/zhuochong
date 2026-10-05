# -*- coding: utf-8 -*-
"""C02 `Launcher` `no_teleport` 诊断探针 —— 只读已存盘的 Action，不改任何东西。

回答一个问题：`max_frame_step_deg = 39.83° @ (f24, upperarm.R)` 到底是
  (a) 真·单帧瞬移（世界旋转也跳），还是
  (b) 欧拉分量的非线性（世界旋转平滑，只是 euler 在 gimbal 附近跑得快）。

对 6 根手臂骨逐帧给：
  - 存盘的 rotation_euler（度）
  - 相邻帧**逐分量**最大增量（= 门禁 `no_teleport` 用的量）
  - 相邻帧**世界 3×3 的测地角**（= 观众真正看到的角度变化）
  - 该帧的 roll 用量

跑法：在 `animations` 目录下
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
        --background --factory-startup --python probe_c02_teleport.py
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import anim_lib as A  # noqa: E402
import anim_launcher02 as L2  # noqa: E402

BONES = ("shoulder.R", "upperarm.R", "forearm.R", "hand.R",
         "shoulder.L", "upperarm.L", "forearm.L", "hand.L")
F0, F1 = 14, 34


def main():
    arm, meshes = A.open_animation_project()
    action = bpy.data.actions.get(L2.NAME)
    if action is None:
        print("C02TP_NO_ACTION")
        return

    scene = bpy.context.scene
    prev = arm.animation_data.action if arm.animation_data else None
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)

    eul = {}
    mats = {}
    dirs = {}
    for frame in range(F0, F1 + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        eul[frame] = {}
        mats[frame] = {}
        dirs[frame] = {}
        for name in BONES:
            bone = arm.pose.bones[name]
            eul[frame][name] = tuple(math.degrees(v)
                                     for v in bone.rotation_euler)
            mats[frame][name] = bone.matrix.to_3x3().copy()
            # 骨轴方向 = 骨矩阵的 Y 列
            dirs[frame][name] = (bone.matrix.to_3x3()
                                 @ Vector((0.0, 1.0, 0.0))).normalized()

    worst = (0.0, None, None, None)
    for frame in range(F0 + 1, F1 + 1):
        for name in BONES:
            ea, eb = eul[frame - 1][name], eul[frame][name]
            step = max(abs(a - b) for a, b in zip(ea, eb))
            ma, mb = mats[frame - 1][name], mats[frame][name]
            world = math.degrees((ma.transposed() @ mb).to_quaternion().angle)
            d_axis = math.degrees(dirs[frame - 1][name].angle(dirs[frame][name]))
            if step > worst[0]:
                worst = (step, frame, name, world)
            print("C02TP " + json.dumps({
                "f": frame, "bone": name,
                "euler": [round(v, 2) for v in eb],
                "d_euler": round(step, 3),
                "d_world_deg": round(world, 3),
                "axis": [round(v, 4) for v in dirs[frame][name]],
                "d_axis_deg": round(d_axis, 3)}))

    print("C02TP_WORST " + json.dumps({
        "step_deg": round(worst[0], 3), "frame": worst[1], "bone": worst[2],
        "world_deg": (None if worst[3] is None else round(worst[3], 3)),
        "limit_deg": L2.NO_TELEPORT_MAX_DEG}))

    if prev is not None:
        arm.animation_data.action = prev


def JS_ROLL():
    try:
        import anim_jump_start as JS
        return dict(JS.ROLL_MAX)
    except Exception:  # noqa: BLE001
        return {}


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("C02TP_FAILURE " + traceback.format_exc())
