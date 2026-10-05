"""probe_js_arm —— 诊断 Jump_Start 手臂的"单帧大幅欧拉步进"到底是真的在转，
还是欧拉表示在跳（±180 分支 / 万向节奇异）。

输出：逐帧打印上臂/前臂/手的 euler 三分量 + 各骨的**世界朝向角**（相邻帧变化量）。
判据：若 euler 步进 ≫ 世界朝向步进 ⟹ 表示问题（要改构造方式）；
      若两者同量级 ⟹ 是真的在快速转动（要改节奏）。
"""

import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A  # noqa: E402

WATCH = ("upperarm.R", "forearm.R", "hand.R", "upperarm.L", "forearm.L", "hand.L")


def world_dir(arm, name):
    basis = arm.pose.bones[name].matrix.to_3x3()
    return (basis @ Vector((0.0, 1.0, 0.0))).normalized()


def main():
    arm, _ = A.open_animation_project()
    A.setup_scene()
    action = bpy.data.actions["Jump_Start"]
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    scene = bpy.context.scene

    prev_e, prev_d = {}, {}
    for frame in range(0, 10):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        line = {"f": frame}
        for name in WATCH:
            e = [math.degrees(v) for v in arm.pose.bones[name].rotation_euler]
            d = world_dir(arm, name)
            step_e = (max(abs(a - b) for a, b in zip(e, prev_e[name]))
                      if name in prev_e else 0.0)
            step_d = (math.degrees(math.acos(max(-1.0, min(1.0,
                                                           d.dot(prev_d[name])))))
                      if name in prev_d else 0.0)
            line[name] = {"euler": [round(v, 2) for v in e],
                          "euler_step": round(step_e, 2),
                          "dir_step": round(step_d, 2)}
            prev_e[name], prev_d[name] = e, d
        A.report("JSARM", line)


main()
