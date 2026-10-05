"""_e03_twist_shot —— 捶胸「拳面」特写对照（只读，不写工程）。

问题不是「拳打多深」，而是「**用拳的哪一面**打」：`A.aim_bone` 只做最小旋转，
拇指朝哪边是顺带的。`_e03_twist.py` 已量出各 twist 下拇指/掌面的穿透量，
但那些数字说不出「看起来是拿指节砸胸，还是拿拇指戳胸」——必须看图。

本脚本固定贴胸帧，扫一组 twist，用**贴近胸口的小取景**（正交 0.85 m）
渲 3/4 前视特写，专门看拳头的朝向与拳面。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python _e03_twist_shot.py
"""

import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A          # noqa: E402
import anim_rage as R         # noqa: E402

FRAME = 28
TWISTS = (-180, -90, 0, 90, 105, 180)
# 胸口特写：从**左前上方**看右脚侧那只拳（左拳 x>0 ⟹ 相机放 +X 侧）
CHEST_CAM = ("chest_close", (2.6, -3.0, 1.45), (0.0, -0.16, 1.16), 0.85,
             (900, 900))


def main():
    arm, _meshes = R.boot()
    out = os.path.join(A.PREVIEW_DIR, "_e03_twist")
    os.makedirs(out, exist_ok=True)
    camera = bpy.data.objects["Presentation_Camera"]
    for twist in TWISTS:
        R.HAND_TWIST = twist
        pose = R.rage_pose(arm, FRAME)
        if arm.animation_data is not None:
            arm.animation_data.action = None      # 见 E03 首版的渲染覆盖坑
        A.apply_pose(arm, pose)
        bpy.context.view_layer.update()
        name, loc, tgt, scale, res = CHEST_CAM
        path = os.path.join(out, "close_twist%+04d.png" % twist)
        A.render_still(camera, path, loc, tgt, scale, res)
        print("E03_SHOT " + path)
    print("E03_SHOT_DONE")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("E03_SHOT_FAILURE " + traceback.format_exc())
