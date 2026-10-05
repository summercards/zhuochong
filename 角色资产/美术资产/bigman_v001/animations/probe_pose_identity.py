"""probe_pose_identity —— 核对两支动作在指定帧上是不是**同一个姿态**。

动机：A02 的设计要求"首末帧等于 Idle_01 的 breath=0 姿态"。光比 euler 不够硬
（`pose_bone.matrix` 的 setter 可能解出等价但不同的 euler 三元组），所以这里
直接比对**全部骨的 armature 空间世界矩阵**，逐元素取最大差。

用法：
    blender --background --factory-startup --python probe_pose_identity.py
"""

import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A  # noqa: E402


def matrices(arm, action, frame):
    scene = bpy.context.scene
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    return {pose_bone.name: [v for row in pose_bone.matrix for v in row]
            for pose_bone in arm.pose.bones}


def main():
    arm, _meshes = A.open_animation_project()
    A.setup_scene()
    actions = {action.name: action for action in bpy.data.actions}
    print("ACTIONS %s" % sorted(actions))

    # 循环动画的闭合点：末帧必须与本支首帧**逐位一致**。
    # （euler 相等不够硬 —— pose_bone.matrix 的 setter 可能解出等价但不同的三元组。）
    pairs = (("Idle_01", 0, "Idle_02", 0), ("Idle_01", 0, "Idle_02", 210),
             ("Walk_F", 0, "Walk_F", 72), ("Walk_B", 0, "Walk_B", 72),
             ("Run", 0, "Run", 48),
             # A06 的首帧是一条**跨文件隐形契约**：必须逐位等于 `Run@48`
             # （A06 直接复用 `WF.gait_pose(arm, anim_run.RUN, 0, meshes)`）。
             # 若日后有人改了 Run 的周期/触地相位而没重跑 A06，这一行会红。
             ("Run", 48, "Run_Stop", 0))
    for name_a, frame_a, name_b, frame_b in pairs:
        if name_a not in actions or name_b not in actions:
            print("SKIP %s/%s" % (name_a, name_b))
            continue
        map_a = matrices(arm, actions[name_a], frame_a)
        map_b = matrices(arm, actions[name_b], frame_b)
        worst = 0.0
        worst_bone = None
        for name in map_a:
            delta = max(abs(x - y) for x, y in zip(map_a[name], map_b[name]))
            if delta > worst:
                worst, worst_bone = delta, name
        # 姿态用 4x4 世界矩阵比对；矩阵元素单位是米/无量纲，1e-6 已是亚纳米级
        print("POSE_IDENTITY %s@%d vs %s@%d  max_delta=%.3e (%.6f mm)  bone=%s"
              % (name_a, frame_a, name_b, frame_b, worst, worst * 1000.0,
                 worst_bone))

    # 顺便：A01 在它自己的 0 帧上是不是落到同一个姿态（防"动作被覆盖"）
    if "Idle_01" in actions:
        first = matrices(arm, actions["Idle_01"], 0)
        last = matrices(arm, actions["Idle_01"], 180)
        worst = max(max(abs(x - y) for x, y in zip(first[n], last[n]))
                    for n in first)
        print("IDLE01_LOOP_CLOSURE max_delta=%.3e (%.6f mm)"
              % (worst, worst * 1000.0))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("PROBE_FAILURE " + traceback.format_exc())
