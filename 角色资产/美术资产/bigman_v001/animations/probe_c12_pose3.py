"""probe_c12_pose3 —— C12 强 Pose 参数扫描（第 4 轮）：**对齐口径**后重扫「沉腰后张」族。

============================ 为什么还要第 4 轮（前 3 轮的坑）

第 3 轮（`probe_c12_pose2`）锁定 drop −95 / span 0.44 / az −0.96 之后，主脚本
`anim_ultimate_start.py` 实测**剪影填充率只有 0.691×** Idle，远低于探针标称的 0.80×。

★ 根因是**口径不一致**（不是姿态不好）：

    `probe_*` 的 `build()`：`@loc pelvis = wloc(0, 0, drop)`
        ⟹ 骨盆 z = **rest 0.900** + drop
    主脚本 `torso_pose()`：`@loc pelvis = wloc(0, 0, Z_SEAM + pz_delta - 0.900)`
        ⟹ 骨盆 z = **Idle 0.830** + pz_delta

    同一个数字 `-0.095` 在两边的物理高度差 **70 mm**：
        探针 -0.095 ⟹ 骨盆 **0.805 m**
        主脚本 -0.095 ⟹ 骨盆 **0.735 m**（比探针最深档 -0.145 还低 20 mm）

    实测也印证：主脚本 aspect ×1.655（比探针最深档 ×1.512 还高）、fill ×0.691
    （比探针最深档 ×0.756 还低）—— 完全落在"下沉越深 ⟹ aspect 越高 / fill 越低"
    这条已实测趋势的**延长线之外**。

============================ 本轮要回答的问题

在**探针口径**下（drop 相对 rest 0.900），"沉腰后张"族在哪个 drop 上能同时拿到

    aspect ≥ 1.30 × Idle(0.3351)   ⟹   ≥ 0.4356
    fill   ≥ 0.80 × Idle(0.5931)   ⟹   ≥ 0.4745
    shoulder ≥ 0.90 × Idle(0.3014) ⟹   ≥ 0.2713

并且**打印出赢家的拳世界坐标与上臂朝向**，好把位置逆解（`arm_seat`）的目标点
原样搬进主脚本 —— 方向向量口径（`aim_bone`）搬不过去，位置口径才可以。

换算表（探针 drop → 主脚本 pz_delta）：`pz_delta = drop + 0.070`

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python probe_c12_pose3.py
"""

import json
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A              # noqa: E402
import anim_idle_01 as I1         # noqa: E402
import probe_c12_baseline as P    # noqa: E402

SIDES = ("L", "R")


def sunk_arms(flare):
    """沉腰后张：上臂向外后下、前臂外张（`flare` 越大肘越外）、拳压在腰侧后方。"""
    out = {}
    for side, sign in (("L", 1.0), ("R", -1.0)):
        out["upperarm." + side] = (0.44 * sign, 0.30, -0.85)
        out["forearm." + side] = (flare * sign, -0.42, -0.88)
        out["hand." + side] = (0.12 * sign, -0.62, -0.78)
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

    aspect_min = base["aspect"] * 1.30
    fill_min = base["fill_grid"] * 0.80
    shoulder_min = base["shoulder_width_m"] * 0.90

    rows = []
    for drop in (-0.045, -0.070, -0.095, -0.120):
        for flare in (0.10, 0.22, 0.34):
            key = "d%03d_f%02d" % (-drop * 1000, flare * 100)
            spec = {
                "drop": drop, "tilt": 4.0,
                "torso": {"spine_01": (-2.0, 0.0, 0.0),
                          "spine_02": (-2.0, 0.0, 0.0),
                          "chest": (-2.0, 0.0, 0.0),
                          "neck": (-6.0, 0.0, 0.0),
                          "head": (6.0, 0.0, 0.0),
                          "shoulder.L": (4.0, 0.0, 0.0),
                          "shoulder.R": (4.0, 0.0, 0.0)},
                "arms": sunk_arms(flare),
            }
            P.apply(spec)
            bpy.context.view_layer.update()
            sil = P.silhouette(arm, key)
            sil["aspect_ratio"] = round(sil["aspect"] / base["aspect"], 4)
            sil["fill_ratio"] = round(sil["fill_grid"] / base["fill_grid"], 4)
            sil["shoulder_ratio"] = round(
                sil["shoulder_width_m"] / base["shoulder_width_m"], 4)
            sil["pass"] = bool(sil["aspect"] >= aspect_min
                               and sil["fill_grid"] >= fill_min
                               and sil["shoulder_width_m"] >= shoulder_min)
            rows.append((key, drop, flare, sil))
            print("C12_POSE3 " + json.dumps({
                "key": key, "drop": round(drop, 3), "flare": flare,
                "aspect": sil["aspect"], "ar": sil["aspect_ratio"],
                "fill": sil["fill_grid"], "fr": sil["fill_ratio"],
                "sh_ratio": sil["shoulder_ratio"],
                "w": sil["width_m"], "h": sil["height_m"],
                "sole_mm": sil["sole_min_mm"], "com_in": sil["com_inside_support"],
                "pelvis_mm": sil["pelvis_z_mm"], "pass": sil["pass"],
            }, ensure_ascii=False))

    passed = [r for r in rows if r[3]["pass"]]
    passed.sort(key=lambda r: -r[3]["fill_ratio"])
    print("C12_POSE3_PASS " + json.dumps(
        [(r[0], r[3]["aspect_ratio"], r[3]["fill_ratio"],
          r[3]["shoulder_ratio"]) for r in passed], ensure_ascii=False))

    # 赢家：打印拳世界坐标 / 上臂朝向（供主脚本的位置逆解搬用）
    if passed:
        key, drop, flare, sil = passed[0]
        P.apply({"drop": drop, "tilt": 4.0,
                 "torso": {"spine_01": (-2.0, 0.0, 0.0),
                           "spine_02": (-2.0, 0.0, 0.0),
                           "chest": (-2.0, 0.0, 0.0),
                           "neck": (-6.0, 0.0, 0.0),
                           "head": (6.0, 0.0, 0.0),
                           "shoulder.L": (4.0, 0.0, 0.0),
                           "shoulder.R": (4.0, 0.0, 0.0)},
                 "arms": sunk_arms(flare)})
        bpy.context.view_layer.update()
        port = {"key": key, "drop": drop, "flare": flare,
                "pz_delta_mm": round((drop + 0.070) * 1000.0, 2),
                "aspect_ratio": sil["aspect_ratio"],
                "fill_ratio": sil["fill_ratio"],
                "shoulder_ratio": sil["shoulder_ratio"],
                "fist_mm": {}, "elbow_dir": {}, "shoulder_mm": {}}
        for side in SIDES:
            port["fist_mm"][side] = [round(v * 1000.0, 2) for v in
                                     A.bone_world(arm, "hand." + side, "tail")]
            head = Vector(A.bone_world(arm, "upperarm." + side, "head"))
            tail = Vector(A.bone_world(arm, "upperarm." + side, "tail"))
            port["elbow_dir"][side] = [round(v, 4) for v in (tail - head).normalized()]
            port["shoulder_mm"][side] = [round(v * 1000.0, 2) for v in
                                         A.bone_world(arm, "upperarm." + side, "head")]
        print("C12_POSE3_WINNER " + json.dumps(port, ensure_ascii=False))

    print("C12_POSE3_BASELINE " + json.dumps(
        {"aspect": base["aspect"], "fill": base["fill_grid"],
         "shoulder_m": base["shoulder_width_m"],
         "aspect_min": round(aspect_min, 4), "fill_min": round(fill_min, 4),
         "shoulder_min": round(shoulder_min, 4)}))
    print("C12_POSE3_DONE")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("C12_POSE3_FAILURE " + traceback.format_exc())
