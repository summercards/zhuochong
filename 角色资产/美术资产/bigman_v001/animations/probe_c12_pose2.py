"""probe_c12_pose2 —— C12 强 Pose 参数扫描（第 3 轮）：**挺胸 + 宽肘**的展开姿。

第 1 轮（`probe_c12_baseline`）比了三个候选族，第 2 轮（`probe_c12_pose`）
在"沉腰握拳"族里扫出：**下沉越深、肘越外张 ⟹ aspect 越高、fill 越低**。

但第 2 轮全是**含胸前压**（`lean > 0`），而 `anticipation_ok` 要求"先收再开" ——
若沉收与强 Pose 都含胸，则"收紧"这条**同向**，判据不成立。
于是本轮把强 Pose 改成 **挺胸后仰 + 头抬起 + 双拳拉到腰侧后方 + 肘大幅外张**：

    沉收：下沉 −122 mm、chest rx **+16°**（含胸）、肩 −26°、双拳内收抱紧、头低
    展开：下沉仅 −45~−95 mm、chest rx **−8°**（挺胸）、肩 +6°、肘外张、头抬起
    ⟹ 胸/肩**反向张开 24° / 32°**，同时骨盆**回升 27~77 mm** ⟹ 两条
       `anticipation_ok` 子句**同时**成立。

本轮量的问题是：**在"挺胸"的构型下，aspect ≥1.30 与 fill ≥0.80 还能同时守住吗？**

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python probe_c12_pose2.py
"""

import json
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A              # noqa: E402
import anim_idle_01 as I1         # noqa: E402
import probe_c12_baseline as P    # noqa: E402

SIDES = ("L", "R")


def arms_of(span, az, by, hand_z, hand_y):
    out = {}
    for side, sign in (("L", 1.0), ("R", -1.0)):
        out["upperarm." + side] = (span * sign, by, az)
        out["forearm." + side] = (span * 0.55 * sign, by - 0.62, -0.62)
        out["hand." + side] = (span * 0.30 * sign, hand_y, hand_z)
    return out


def main():
    arm, _meshes = A.open_animation_project()
    A.setup_scene()
    if I1.NAME not in bpy.data.actions:
        I1.main()
        arm, _meshes = A.open_animation_project()
        A.setup_scene()
    P.A_RIG = arm

    src = bpy.data.actions[I1.NAME]
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = src
    A._bind_slot(arm, src)
    bpy.context.scene.frame_set(0)
    bpy.context.view_layer.update()
    base = P.silhouette(arm, "Idle_01@0")

    rows = {}
    for drop in (-0.045, -0.070, -0.095):
        for span in (0.44, 0.52, 0.60):
            for az in (-0.86, -0.96):
                key = "d%03d_s%02d_z%02d" % (-drop * 1000, span * 100, -az * 100)
                spec = {
                    "drop": drop, "tilt": 2.0,
                    "torso": {
                        "spine_01": (-3.0, 0.0, 0.0),
                        "spine_02": (-3.0, 0.0, 0.0),
                        "chest": (-8.0, 0.0, 0.0),
                        "neck": (-6.0, 0.0, 0.0),
                        "head": (10.0, 0.0, 0.0),
                        "shoulder.L": (6.0, 0.0, 0.0),
                        "shoulder.R": (6.0, 0.0, 0.0)},
                    "arms": arms_of(span, az, 0.34, -0.30, -0.86),
                }
                P.apply(spec)
                bpy.context.view_layer.update()
                sil = P.silhouette(arm, key)
                sil["aspect_ratio"] = round(sil["aspect"] / base["aspect"], 4)
                sil["fill_ratio"] = round(sil["fill_grid"] / base["fill_grid"], 4)
                rows[key] = sil
                print("C12_POSE2 " + json.dumps({
                    "key": key,
                    "aspect": sil["aspect"],
                    "ar": sil["aspect_ratio"],
                    "fill": sil["fill_grid"],
                    "fr": sil["fill_ratio"],
                    "sh_over_h": sil["shoulder_over_height"],
                    "headoff_mm": sil["head_top_offset_mm"],
                    "sole_mm": sil["sole_min_mm"],
                    "com_in": sil["com_inside_support"],
                    "pz_mm": sil["pelvis_z_mm"],
                }, ensure_ascii=False))

    ok = [(k, v) for k, v in rows.items()
          if v["aspect_ratio"] >= 1.30 and v["fill_ratio"] >= 0.80
          and v["shoulder_over_height"] >= 0.175]
    msg = [(k, round(v["aspect_ratio"], 3), round(v["fill_ratio"], 3),
            round(v["shoulder_over_height"], 4)) for k, v in ok]
    print("C12_POSE2_PASS " + json.dumps(msg, ensure_ascii=False))
    print("C12_POSE2_BASELINE " + json.dumps(
        {"aspect": base["aspect"], "fill": base["fill_grid"],
         "sh_over_h": base["shoulder_over_height"]}))
    print("C12_POSE2_DONE")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("C12_POSE2_FAILURE " + traceback.format_exc())
