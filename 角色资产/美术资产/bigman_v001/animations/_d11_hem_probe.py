"""_d11_hem_probe —— 判明侧视图腰部那根"横插薄片"的来路（只读 + 出图）。

背景：D11 首次目检时，侧视 / 3Q 的命中帧（f3/f8）腰部前侧露出一根**水平薄片**。
  `probe_c11_belt.py` 已确认模型里有 2 个**未蒙皮**对象
  （`Jacket_Hem` 377.6×251×23 mm、`Jacket_Hem_Line` 371.8×246×4 mm，
   均 `vgroups=0`、无 armature 父级），世界位姿在整段动画里**逐位恒定**
  ⟹ 身体动、薄片不动 ⟹ 露出。

本探针把三件事一次说清（纯事实核对，不设门槛）：
  ① 薄片在这几帧里**贡献了多少像素**（`Jacket_Hem*` 单独渲染计数）；
  ② 把它们**藏起来**再渲同样几帧 —— 若薄片消失，来路即坐实；
  ③ 对照 D10 `Hit_Body` 同帧，量 D11 是否**放大**了它（纯骨盆平移的副作用）。

产物：`previews/anim/_hemcheck_hitleg_{view}_f{frame}_nohem.png`（**下划线开头 = 诊断图**）
"""
import json
import os
import sys

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anim_lib as A  # noqa: E402

TARGETS = ("Jacket_Hem", "Jacket_Hem_Line")
FRAMES = {"Hit_Leg": (0, 3, 8), "Hit_Body": (0, 3, 8)}
VIEWS = (A.VIEW_SIDE, A.VIEW_3Q)


def mask_count(path):
    image = bpy.data.images.load(path, check_existing=False)
    width, height = image.size
    pix = np.array(image.pixels[:], dtype=np.float32).reshape(height, width, 4)
    bpy.data.images.remove(image)
    alpha = pix[:, :, 3]
    if float(alpha.min()) < 0.5:
        m = alpha > 0.5
    else:
        m = pix[:, :, :3].min(axis=2) < 0.92
    return int(m.sum())


def main():
    arm, _meshes = A.open_animation_project()
    A.setup_scene()
    scene = bpy.context.scene
    camera = bpy.data.objects.get("Presentation_Camera")

    out = {}
    for action_name, frames in FRAMES.items():
        action = bpy.data.actions.get(action_name)
        if action is None:
            out[action_name] = "NO_ACTION"
            continue
        if arm.animation_data is None:
            arm.animation_data_create()
        arm.animation_data.action = action
        A._bind_slot(arm, action)
        out[action_name] = {}
        for frame in frames:
            scene.frame_set(frame)
            bpy.context.view_layer.update()
            rec = {}
            for name, location, target, scale, res in VIEWS:
                # ① 有薄片
                path_on = os.path.join(A.PREVIEW_DIR, "_hemcheck_%s_%s_f%04d_on.png"
                                       % (action_name.lower(), name, frame))
                A.render_still(camera, path_on, location, target, scale, res)
                # ② 藏起薄片
                for t in TARGETS:
                    obj = bpy.data.objects.get(t)
                    if obj is not None:
                        obj.hide_render = True
                path_off = os.path.join(A.PREVIEW_DIR,
                                        "_hemcheck_%s_%s_f%04d_nohem.png"
                                        % (action_name.lower(), name, frame))
                A.render_still(camera, path_off, location, target, scale, res)
                for t in TARGETS:
                    obj = bpy.data.objects.get(t)
                    if obj is not None:
                        obj.hide_render = False
                n_on, n_off = mask_count(path_on), mask_count(path_off)
                rec[name] = {"px_with_hem": n_on, "px_without_hem": n_off,
                             "px_hem_visible": n_on - n_off,
                             "nohem_png": os.path.basename(path_off)}
            out[action_name][str(frame)] = rec
    print("HEM_PROBE " + json.dumps(out, ensure_ascii=False, indent=1))
    print("HEM_PROBE_DONE")


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("HEM_PROBE_FAILURE " + traceback.format_exc())
