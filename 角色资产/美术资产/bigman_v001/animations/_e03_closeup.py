"""拳-胸**近景**渲染：把命中帧的拳与胸填满画面，亲眼判定贴合/对称/穿模。

★ 为什么必须做这一步：全身图（scale 2.10）里拳-胸只占几十像素，
  「L 拳面 14.71 mm / R 2.84 mm」在画面上无法分辨是「可见的缝」还是
  「几何尺在肩部说谎」。项目铁律：结论来自渲染实测。

镜头（正交，`Presentation_Camera`）：
  · chest   目标 (0, -0.16, 1.30) scale 0.62  —— 双拳 + 胸一起
  · chestlo 目标 (0, -0.16, 1.22) scale 0.55  —— 略低，看拳有没有压到胸骨
  · left    目标 (+0.16, -0.20, 1.28) scale 0.30 —— 左拳特写
  · right   目标 (-0.16, -0.20, 1.28) scale 0.30 —— 右拳特写
  · side    侧视 目标 (0, -0.16, 1.28) scale 0.62，相机在 +X

帧：28（第一次捶中）/ 36（胸廓前挺，报告里 L 6.18 R −3.59）/ 52（第二次捶中）

用法：
  blender -b --factory-startup -P _e03_closeup.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import anim_rage as R  # noqa: E402
import anim_lib as A  # noqa: E402

OUT = os.path.join(A.PREVIEW_DIR, "closeup")
os.makedirs(OUT, exist_ok=True)

arm, meshes = R.boot()
keyframes = [(f, R.rage_pose(arm, f)) for f in range(R.START, R.END + 1)]
keyframes = R.compat_euler(keyframes)
keyframes = R.seam_canonicalize(keyframes)
action, _meta = A.build_action(arm, R.NAME, keyframes,
                              {"anim_id": R.NAME, "loop": False,
                               "category": "t", "frames": [0, R.TOTAL]})
for win in (R.HOLD_1, R.HOLD_2):
    A.set_hitstop(action, win[0], win[1])

camera = bpy.data.objects.get("Presentation_Camera")
RES = (1024, 1024)

SHOTS = [
    ("chest", (0.0, -5.6, 1.30), (0.0, -0.16, 1.30), 0.62),
    ("chestlo", (0.0, -5.6, 1.22), (0.0, -0.16, 1.22), 0.55),
    ("left", (0.0, -5.6, 1.28), (0.16, -0.20, 1.28), 0.30),
    ("right", (0.0, -5.6, 1.28), (-0.16, -0.20, 1.28), 0.30),
    ("side", (5.6, -0.16, 1.28), (0.0, -0.16, 1.28), 0.62),
    ("sideL", (5.6, -0.16, 1.28), (0.16, -0.16, 1.28), 0.30),
]

arm.animation_data.action = action
A._bind_slot(arm, action)
for frame in (28, 36, 52):
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()
    for name, loc, tgt, scale in SHOTS:
        path = os.path.join(OUT, "f%04d_%s.png" % (frame, name))
        A.render_still(camera, path, loc, tgt, scale, RES)
        print("WROTE %s" % path)
print("E03_CLOSEUP_DONE")
