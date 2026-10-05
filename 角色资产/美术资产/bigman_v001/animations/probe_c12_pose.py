"""probe_c12_pose —— C12 强 Pose 参数扫描（先量再定阈值，第 2 轮）。

`probe_c12_baseline.py` 已给出三条结论：
  · 纵横比：Idle 0.3351 / 举拳 0.3502(+4.5%) / 拉弓 0.3743(+11.7%) / **沉腰 0.4543(+35.6%)**
  · 填充率：Idle 0.5931，三个候选**全部更低**（0.479 / 0.451 / 0.486）
    ⟹ 计划里"填充率 ≥1.3× Idle"这条**不成立**（强 Pose 把包围盒撑大，
       填充率必然下降）。要守住的是"**变宽的同时不许变稀**"。
  · 肩宽/站高：Idle 0.1740 / 沉腰 0.1798 —— 计划里写的 0.34 对本骨架（肩宽实测
    0.301 m、身高 1.73 m）**不可能达到**，是拍脑袋的数，按实测重定。

本探针在**沉腰握拳**族里扫参数，目标是把两项同时推高：
    aspect 高（≥ 1.30 × Idle）**且** fill_grid 不掉太多（≥ 0.80 × Idle）。

扫描维度（保持双脚钉在 Idle 原位，零水平位移 ⟹ 所有 plant 门禁构造性绿）：
    drop   骨盆下沉  −0.085 / −0.115 / −0.145
    span   肘外张量（upperarm 方向 x 分量）
    az     上臂竖直分量（拳头高度）
    tilt   骨盆前倾
    lean   含胸 / 挺胸

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python probe_c12_pose.py
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


def arms_of(span, az, by, bz_edge):
    """双拳收腰、肘向后外张的臂方向（体坐标 → 世界，朝向恒定 ⟹ 可直接写世界）。"""
    out = {}
    for side, sign in (("L", 1.0), ("R", -1.0)):
        out["upperarm." + side] = (span * sign, by, az)
        out["forearm." + side] = (0.18 * sign, by - 0.86, -0.48)
        out["hand." + side] = (0.10 * sign, by - 1.10, bz_edge)
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
    base_aspect = base["aspect"]
    base_fill = base["fill_grid"]

    rows = {}
    for drop in (-0.085, -0.115, -0.145):
        for span in (0.30, 0.40, 0.50):
            for az in (-0.80, -0.92):
                for (tilt, lean) in ((4.0, 4.0), (8.0, 10.0)):
                    key = "d%03d_s%02d_z%02d_t%02d_%02d" % (
                        -drop * 1000, span * 100, -az * 100, tilt, lean)
                    spec = {
                        "drop": drop, "tilt": tilt,
                        "torso": {
                            "spine_01": (lean * 0.5, 0.0, 0.0),
                            "spine_02": (lean * 0.5, 0.0, 0.0),
                            "chest": (lean, 0.0, 0.0),
                            "neck": (-lean - 6.0, 0.0, 0.0),
                            "head": (lean * 0.6 + 4.0, 0.0, 0.0),
                            "shoulder.L": (-16.0, 0.0, 0.0),
                            "shoulder.R": (-16.0, 0.0, 0.0)},
                        "arms": arms_of(span, az, 0.42, -0.55),
                    }
                    P.apply(spec)
                    bpy.context.view_layer.update()
                    sil = P.silhouette(arm, key)
                    sil["aspect_ratio"] = round(sil["aspect"] / base_aspect, 4)
                    sil["fill_ratio"] = round(sil["fill_grid"] / base_fill, 4)
                    rows[key] = sil
                    print("C12_POSE " + json.dumps({
                        "key": key,
                        "aspect": sil["aspect"],
                        "aspect_ratio": sil["aspect_ratio"],
                        "fill": sil["fill_grid"],
                        "fill_ratio": sil["fill_ratio"],
                        "sh_over_h": sil["shoulder_over_height"],
                        "headoff_mm": sil["head_top_offset_mm"],
                        "sole_mm": sil["sole_min_mm"],
                        "com_in": sil["com_inside_support"],
                    }, ensure_ascii=False))

    ranked = sorted(rows.items(),
                    key=lambda kv: -(kv[1]["aspect_ratio"]
                                     + kv[1]["fill_ratio"]))
    print("C12_POSE_TOP " + json.dumps(
        [(k, v["aspect_ratio"], v["fill_ratio"]) for k, v in ranked[:8]]))
    print("C12_POSE_BASELINE " + json.dumps(
        {"aspect": base_aspect, "fill": base_fill}))
    print("C12_POSE_DONE")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("C12_POSE_FAILURE " + traceback.format_exc())
