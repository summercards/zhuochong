"""try_stance —— 战斗站架的姿态试算台（快速迭代用，不产出正式动画）。

腿：两骨 IK 解析，脚贴地；
臂：**按方向摆**（`A.aim_bone`）—— 先定"上臂朝哪、前臂朝哪"，再让 Blender
    反解 euler，比试角度可靠。渲染三视图出来看，看图调方向。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python try_stance.py
"""

import json
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A  # noqa: E402

TAG = os.environ.get("STANCE_TAG", "stance")

# ---------------------------------------------------------------- 站架参数
PELVIS_TILT = 4.0          # 骨盆前倾（度）—— 必须传给 leg_ik
DROP = -0.070              # 骨盆下降（m）
FRONT_ANKLE_Y = -0.170     # 前脚（左脚）踝 y
BACK_ANKLE_Y = 0.140       # 后脚（右脚）踝 y
STANCE_HALF_X = 0.150      # 踝到中线的水平距离
ABDUCT_DEG = 4.3           # 外展角

# 手臂目标方向（世界空间单位向量；+X 左，+Y 后，−Y 前，+Z 上）
ARM_DIRS = {
    "upperarm.L": (0.22, -0.18, -0.96),
    "forearm.L": (-0.30, -0.55, 0.78),
    "hand.L": (-0.16, -0.78, 0.60),
    "upperarm.R": (-0.20, -0.20, -0.96),
    "forearm.R": (0.28, -0.42, 0.86),
    "hand.R": (0.14, -0.68, 0.72),
}

TORSO = {
    "pelvis": (PELVIS_TILT, 0.0, 0.0),
    "spine_01": (2.0, 0.0, 0.0),
    "spine_02": (2.0, 0.0, 0.0),
    "chest": (1.0, 0.0, 0.0),
    "neck": (-6.0, 0.0, 0.0),
    "head": (4.0, 0.0, 0.0),
    # 肩骨分担一部分"垂臂"旋转：上臂从 T-pose 落下 80° 若全压在肩关节上，
    # Sleeve 臂根（权重在 shoulder/upperarm 之间各约 50%）会被拧成两个鼓包。
    # 沉肩还顺带符合"沉肩坠肘"的力量型架势。
    "shoulder.L": (-20.0, 0.0, 0.0),
    "shoulder.R": (-20.0, 0.0, 0.0),
}


def build_stance(arm):
    hip_z = 0.900 + DROP
    thigh_l, bend_l = A.leg_ik(0.0, hip_z, FRONT_ANKLE_Y, A.Z_ANKLE_REST,
                               tilt_deg=PELVIS_TILT)
    thigh_r, bend_r = A.leg_ik(0.0, hip_z, BACK_ANKLE_Y, A.Z_ANKLE_REST,
                               tilt_deg=PELVIS_TILT)

    pose = dict(TORSO)
    pose.update({
        "thigh.L": (thigh_l, 0.0, -ABDUCT_DEG),
        "shin.L": (bend_l, 0.0, 0.0),
        "foot.L": (-(thigh_l + bend_l), 0.0, 0.0),
        "thigh.R": (thigh_r, 0.0, ABDUCT_DEG),
        "shin.R": (bend_r, 0.0, 0.0),
        "foot.R": (-(thigh_r + bend_r), 0.0, 0.0),
        "toe.L": (0.0, 0.0, 0.0),
        "toe.R": (0.0, 0.0, 0.0),
        "@loc": {"pelvis": A.wloc(0.0, 0.0, DROP)},
    })
    pose.update(A.FIST)
    A.apply_pose(arm, pose)

    # 支撑脚：钉死世界朝向 → 鞋底永远平贴地面
    for side in ("L", "R"):
        pose["foot." + side] = A.keep_world_orientation(arm, "foot." + side)

    # 手臂按方向摆（父级要先摆好：shoulder → upperarm → forearm → hand）
    for name in ("upperarm.L", "forearm.L", "hand.L",
                 "upperarm.R", "forearm.R", "hand.R"):
        pose[name] = A.aim_bone(arm, name, ARM_DIRS[name])

    return pose


def main():
    arm, meshes = A.open_animation_project()
    A.setup_scene()
    pose = build_stance(arm)

    low = A.lowest_z_by_side(meshes)
    report = {
        "low_L_mm": round(low["L"] * 1000.0, 2),
        "low_R_mm": round(low["R"] * 1000.0, 2),
        "bones": {},
    }
    for name in ("pelvis", "chest", "head", "shoulder.L", "upperarm.L",
                 "forearm.L", "hand.L", "hand.R", "foot.L", "foot.R"):
        head = A.bone_world(arm, name, "head")
        tail = A.bone_world(arm, name, "tail")
        report["bones"][name] = {
            "head": [round(v, 4) for v in head],
            "tail": [round(v, 4) for v in tail],
        }
    report["arms"] = {name: [round(v, 1) for v in pose[name]]
                      for name in ARM_DIRS}
    print("STANCE_METRICS " + json.dumps(report, ensure_ascii=False))

    for view in (A.VIEW_SIDE, A.VIEW_FRONT, A.VIEW_3Q):
        name, location, target, scale, res = view
        A.render_still(bpy.data.objects["Presentation_Camera"],
                       os.path.join(A.PREVIEW_DIR,
                                    "try_%s_%s.png" % (TAG, name)),
                       location, target, scale, res)
    print("STANCE_SHOT_OK " + A.PREVIEW_DIR)


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("STANCE_FAILURE " + traceback.format_exc())
