"""_d14wide_render —— 给 `probe_d15_pixels.py` 造**反面对照**用的 D14 取景帧。

★★ 为什么必须另渲一套（方法论，不是补丁）：
   `probe_d15_pixels.py` 的独门尺子是「**头在图像哪一侧**」—— 它比的是
   **同一段动画内**，头部的肤色列心 从触地帧到末帧 往哪边移动。
   但 D14 自己的 `knockdownf_side` 取景在末段**左侧被裁**（实测 f15/f20 的
   `col_all = [0, 501]` 且 `clip_L = True` ⟹ 头部整个出画）⟹ 拿它当对照
   量不出列心，对照就是**无效的**（不是"尺子坏了"，是"对照坏了"）。
   ⟹ 用**同一把像素尺子**（正交侧视、3.30 m 正交宽、780×1100 ⟹ 3 mm/px）
     给 D14 重渲一套，只把视中心沿 Y 平移到 D14 身体所在的一侧（−0.35 m），
     使全身在画面内。**图像右仍恒为 +Y** ⟹ 与 D15 的读法逐位一致。

输出：`previews/anim/_probe/knockdownfW_side_f####.png`
     ★ 刻意写进 `_probe/` 子目录，**不污染**正式交付的 `previews/anim/`。

用法：
  "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" --background \
      --factory-startup --python _d14wide_render.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A  # noqa: E402

# ★ 与 `probe_d15_pixels.py` 的 D15 侧视同一把尺子（正交宽/分辨率逐位相同），
#   只把视中心沿 Y 移到 D14 身体那一侧。
VIEW = ("side", (5.20, -0.35, 1.00), (0.0, -0.35, 1.00), 3.30, (780, 1100))
OUT = os.path.join(A.OUT_DIR, "previews", "anim", "_probe")


def main():
    arm, _meshes = A.open_animation_project()
    A.setup_scene()
    action = None
    for candidate in A.bpy.data.actions:
        if candidate.name == "Knockdown_F":
            action = candidate
            break
    if action is None:
        raise RuntimeError("找不到 Action：Knockdown_F")
    os.makedirs(OUT, exist_ok=True)
    A.render_pose_sheet(arm, action, list(range(0, 21)), "knockdownfW",
                        views=(VIEW,), out_dir=OUT)
    print("D14WIDE_DONE %s" % OUT)


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("D14WIDE_FAILURE " + traceback.format_exc())
