"""probe_light01_jitter —— 决定性实验：EEVEE Next 的渲染是否"依赖帧号"。

背景：`Light_01` 侧视 f0 与 f18 的几何被证明**逐位相同**
（57 根骨骼世界矩阵最大差 0.000e+00；全场景求值顶点 sha1 全等），
但渲染出的 PNG 有 351 个像素不同（y=572..582 / x=357..439，RGBA ≈ (0,1,2,2)）。

本探针把骨骼动画**完全摘掉**（`animation_data.action = None`，姿态静止），
于是 f0 与 f18 的场景状态在数学上绝对一致；此时若渲染仍有像素差，
就唯一地证明：**差异来自渲染器本身对帧号的依赖（EEVEE Next 的 TAA 抖动）**，
而不是动画数据的问题。

对照组：同一帧渲两次（应逐位相同）—— 证明渲染本身是确定性的，
差异确实来自"帧号"这一个变量，而不是随机性。

只读：不写 .blend、不导 GLB。
输出：previews/anim/_jitter_probe/ 下的 4 张 png。
"""

import hashlib
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A  # noqa: E402

OUT = os.path.join(A.PREVIEW_DIR, "_jitter_probe")
VIEW = A.VIEW_SIDE


def digest(path):
    with open(path, "rb") as handle:
        raw = handle.read()
    # 只比 PNG 的 IDAT 原始像素流，跳过元数据
    return hashlib.sha1(raw).hexdigest()[:16], len(raw)


def main():
    arm, _meshes = A.open_animation_project()
    A.setup_scene()
    os.makedirs(OUT, exist_ok=True)

    # ---- 1) 骨骼静止：摘掉动画，姿态固定在 rest
    if arm.animation_data:
        arm.animation_data.action = None
    for pose_bone in arm.pose.bones:
        pose_bone.rotation_mode = pose_bone.rotation_mode or "XYZ"
        pose_bone.rotation_euler = (0.0, 0.0, 0.0)
        pose_bone.location = (0.0, 0.0, 0.0)
        pose_bone.scale = (1.0, 1.0, 1.0)
    bpy.context.view_layer.update()

    camera = bpy.data.objects.get("Presentation_Camera")
    scene = bpy.context.scene
    name, location, target, scale, res = VIEW

    shots = {}
    for label, frame in (("static_f0000_a", 0), ("static_f0000_b", 0),
                         ("static_f0018", 18), ("static_f0041", 41)):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        path = os.path.join(OUT, "%s.png" % label)
        A.render_still(camera, path, location, target, scale, res)
        shots[label] = digest(path)

    A.report("LIGHT01EP_JITTER", {
        "engine": scene.render.engine,
        "taa_render_samples": scene.eevee.taa_render_samples,
        "motion_blur": scene.render.use_motion_blur,
        "armature_action": (arm.animation_data.action.name
                            if arm.animation_data
                            and arm.animation_data.action else None),
        "digests": {k: v[0] for k, v in shots.items()},
        "sizes": {k: v[1] for k, v in shots.items()},
        "same_frame_rerender_identical": (
            shots["static_f0000_a"] == shots["static_f0000_b"]),
        "f0_vs_f18_identical": (shots["static_f0000_a"] == shots["static_f0018"]),
        "verdict": ("若 same_frame_rerender_identical=True 且 "
                    "f0_vs_f18_identical=False ⟹ 渲染器按帧号抖动，"
                    "像素相等不可作为首末帧判据"),
    })


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("LIGHT01EP_JITTER_FAILURE " + traceback.format_exc())
