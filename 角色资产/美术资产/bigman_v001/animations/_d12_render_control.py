"""_d12_render_control —— 为 D12 像素探针补渲**对照动画**的静帧。

★ 为什么需要：D12 的像素探针要证明"这把尺子量的确实是**共享解析弹道**"，
  必须拿一支**别的**动画（A12 `Jump_Fall`，同一解析弹道、**不同的正交宽与
  像素比例**）在同一把尺子下量一遍。previews/anim/ 里没有 jumpfall 的静帧
  （A12 当年只输出了 mp4 与 7 帧 side，未落盘…… 实际是未渲染），所以这里补渲。

用法：
  "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" --background \
      --factory-startup --python _d12_render_control.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A  # noqa: E402
import anim_jump_fall as JF  # noqa: E402

FRAMES = [0, 4, 8, 12, 16, 20, JF.TOTAL]
FALL_SIDE = ("side", (4.8, 0.0, 1.30), (0.0, 0.0, 1.30), 3.80, (780, 1100))


def main():
    arm, _meshes = A.open_animation_project()
    action = None
    for candidate in A.bpy.data.actions:
        if candidate.name == JF.NAME:
            action = candidate
            break
    if action is None:
        raise RuntimeError("找不到 Action：%s" % JF.NAME)
    outs = A.render_pose_sheet(arm, action, FRAMES, "jumpfall",
                               views=(FALL_SIDE,))
    print("D12_CONTROL_DONE %d %s" % (len(outs), FRAMES))


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("D12_CONTROL_FAILURE " + traceback.format_exc())
