"""anim_idle_01 —— A01 `Idle_01` 战斗待机。

设计（对着清单 §一 A01 的原文逐条落）：
    双脚宽站    踝左右各 0.150 m（两脚间距 0.30 m，比静止站姿宽 78%）
                前脚 y = −0.170、后脚 y = +0.140（跨度 0.31 m）
    重心降低    骨盆 z 从 0.900 降到 0.830（−70 mm，−7.8%），屈膝 40~43°
    拳护胸前    双拳 x ≈ ±0.15、y ≈ −0.26、z ≈ 1.33（胸口高度，肘外张）
    胸腹呼吸    胸腔 rx 摆 4°、肩 rx 摆 4°、头 rx 摆 2° —— 吸 1.2 s / 停 0.4 s / 呼 1.4 s
    避免晃动    骨盆水平位移 0（**故意不做重心左右转移**：骨盆一动脚就跟着动，
                既是脚滑，也违背"沉稳"）。仅骨盆做 ±2 mm 的呼吸升降，
                且由腿部 IK 吸收，脚纹丝不动。
    循环        3.0 s = 180 帧 @60 fps，首尾姿态由同一组参数生成，逐位相同。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python anim_idle_01.py
"""

import json
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A  # noqa: E402

NAME = "Idle_01"
TOTAL = 180                      # 3.0 s @ 60 fps
PELVIS_TILT = 4.0
DROP = -0.070
HIP_Y = 0.0
FRONT_ANKLE_Y = -0.170
BACK_ANKLE_Y = 0.140
STANCE_HALF_X = 0.150
ABDUCT_DEG = 4.3

# 手臂方向：前手（左）略低护胸、后手（右）略高护下巴 —— 拳架要有层次，
# 两手齐平会读成"抱拳"而不是"准备打人"。
ARM_DIRS = {
    "upperarm.L": (0.26, -0.30, -0.92),
    "forearm.L": (-0.32, -0.40, 0.86),
    "hand.L": (-0.20, -0.70, 0.68),
    "upperarm.R": (-0.22, -0.36, -0.90),
    "forearm.R": (0.34, -0.20, 0.92),
    "hand.R": (0.18, -0.60, 0.78),
}

# 呼吸关键帧：吸气快(0→72)、顶峰保持(72→96)、呼气慢(96→180)
BREATH_KEYS = ((0, 0.00), (36, 0.42), (72, 1.00), (96, 1.00),
               (132, 0.40), (180, 0.00))


def idle_pose(arm, breath):
    """按呼吸量生成完整姿态（腿由 IK 跟随骨盆，脚不动）。

    `breath`：0 = 呼气末，1 = 吸气峰。
    """
    drop = DROP + 0.0030 * breath
    hip_z = 0.900 + drop
    # 骨盆倾角**必须恒定**。曾经让它随呼吸摆 +0.6°，结果整条脊椎被整体前推 3.8 mm，
    # 恰好抵消掉胸腔后仰的 11 mm，胸骨顶净位移只剩 6.5 mm（"看不见的呼吸"）。
    # 呼吸是胸腔的事，骨盆不参与。
    tilt = PELVIS_TILT

    thigh_l, bend_l = A.leg_ik(HIP_Y, hip_z, FRONT_ANKLE_Y, A.Z_ANKLE_REST,
                               tilt_deg=tilt)
    thigh_r, bend_r = A.leg_ik(HIP_Y, hip_z, BACK_ANKLE_Y, A.Z_ANKLE_REST,
                               tilt_deg=tilt)

    pose = {
        "pelvis": (tilt, 0.0, 0.0),
        "spine_01": (2.0, 0.0, 0.0),
        # 呼吸配平（三个量一起定，单独调任何一个都会把另一个顶红）：
        #   胸腔可见度  ← chest 摆 3.5°，胸骨顶走 ~11 mm，叠加骨盆升降 3 mm ≈ 14 mm
        #   肩部起伏    ← shoulder 摆 5°，肩峰走 ~13 mm（"肩膀轻微起伏"）
        #   头部稳定    ← 头朝向变化 = chest(−3.5°) + neck(−0.5°) + head(+1.5°) = −2.5°，
        #                 这个量级读作"随呼吸微动"；超过 5° 就变成点头了。
        "spine_02": (2.0, 0.0, 0.0),
        "chest": (1.0 - 3.5 * breath, 0.0, 0.0),
        "neck": (-6.0 - 0.5 * breath, 0.0, 0.0),
        "head": (5.0 + 1.5 * breath, 0.0, 0.0),
        # 肩：呼气时沉（−18）、吸气时抬 5° —— "肩膀轻微起伏"
        "shoulder.L": (-18.0 + 5.0 * breath, 0.0, 0.0),
        "shoulder.R": (-18.0 + 5.0 * breath, 0.0, 0.0),
        "thigh.L": (thigh_l, 0.0, -ABDUCT_DEG),
        "shin.L": (bend_l, 0.0, 0.0),
        "foot.L": (0.0, 0.0, 0.0),
        "toe.L": (0.0, 0.0, 0.0),
        "thigh.R": (thigh_r, 0.0, ABDUCT_DEG),
        "shin.R": (bend_r, 0.0, 0.0),
        "foot.R": (0.0, 0.0, 0.0),
        "toe.R": (0.0, 0.0, 0.0),
        "@loc": {"pelvis": A.wloc(0.0, 0.0, drop)},
    }
    pose.update(A.FIST)
    A.apply_pose(arm, pose)

    for side in ("L", "R"):
        pose["foot." + side] = A.keep_world_orientation(arm, "foot." + side)
    for bone in ("upperarm.L", "forearm.L", "hand.L",
                 "upperarm.R", "forearm.R", "hand.R"):
        pose[bone] = A.aim_bone(arm, bone, ARM_DIRS[bone])
    return pose


def idle_assertions(samples):
    """Idle 专属门禁：呼吸必须看得见，晃动必须看不见。

    量点选择（踩过坑）：
      胸腔起伏 → `neck` 的 head（= chest.tail，胸骨顶）。量 chest.head 是胸骨**底**，
                 它绕自己转多久都不动，只会给出 1.7 mm 的假值。
      肩部起伏 → `upperarm.L` 的 head（= shoulder.tail，肩峰）。
      拳架位置 → `hand.L/R` 的 tail（拳头），不是 head（腕关节）。
    """
    res = {}
    sternum = [s["neck"] for s in samples]
    shoulder_peak = [s["upperarm.L"] for s in samples]
    head = [s["head"] for s in samples]
    pelvis = [s["pelvis"] for s in samples]
    fist_l = [s["hand.L.tail"] for s in samples]
    fist_r = [s["hand.R.tail"] for s in samples]

    breath = max(math.dist(c, sternum[0]) for c in sternum) * 1000.0
    res["chest_breath_mm"] = round(breath, 2)
    res["breath_visible_ok"] = 7.0 <= breath <= 30.0

    rise = (max(s[2] for s in shoulder_peak)
            - min(s[2] for s in shoulder_peak)) * 1000.0
    res["shoulder_rise_mm"] = round(rise, 2)
    res["shoulder_rise_ok"] = 3.0 <= rise <= 20.0

    # "头稳不稳"的量法（第三次才对）：
    #   量绝对位移 → 胸腔一起伏头就动 37 mm，"红"，但那是设计意图；
    #   量相对胸骨顶的位移 → 胸腔转 5° 时头离支点更远、杠杆更长，必然比胸骨走得远，
    #                          16.7 mm 又"红"，可这也不是头自己乱动。
    # 真正要守的是**头在空间里的朝向**：脖子转 −1.6°、头转 +1.6°，世界朝向净变化 0，
    # 看起来就是"头钉在那儿、只有胸在呼吸"。位置跟随胸腔是正常的（真人也是）。
    def unit(vector):
        length = math.sqrt(sum(v * v for v in vector)) or 1.0
        return tuple(v / length for v in vector)

    def angle(a, b):
        cos = max(-1.0, min(1.0, sum(x * y for x, y in zip(a, b))))
        return math.degrees(math.acos(cos))

    axes = [unit(tuple(t[i] - h[i] for i in range(3)))
            for t, h in zip([s["head.tail"] for s in samples], head)]
    tilt = max(angle(a, axes[0]) for a in axes)
    head_abs = max(math.dist(h, head[0]) for h in head) * 1000.0
    res["head_travel_abs_mm"] = round(head_abs, 2)
    res["head_orientation_deg"] = round(tilt, 3)
    res["head_settled_ok"] = tilt <= 3.0 and head_abs <= 60.0

    # 「避免身体一直晃」的量化：骨盆只允许呼吸升降，水平位移必须几乎为零。
    sway = max(math.hypot(p[0] - pelvis[0][0], p[1] - pelvis[0][1])
               for p in pelvis) * 1000.0
    res["pelvis_sway_mm"] = round(sway, 3)
    res["pelvis_steady_ok"] = sway <= 2.0

    shift = max(max(math.dist(f, fist_l[0]) for f in fist_l),
                max(math.dist(f, fist_r[0]) for f in fist_r)) * 1000.0
    res["guard_shift_mm"] = round(shift, 2)
    res["guard_steady_ok"] = shift <= 25.0

    # 拳架：双拳护在胸口，前后有纵深，左右有层次（后手比前手高）
    mid = samples[len(samples) // 2]
    fl, fr = mid["hand.L.tail"], mid["hand.R.tail"]
    res["fist_L_mm"] = [round(v * 1000.0, 1) for v in fl]
    res["fist_R_mm"] = [round(v * 1000.0, 1) for v in fr]
    res["guard_height_ok"] = 1.28 <= fl[2] <= 1.50 and 1.28 <= fr[2] <= 1.52
    res["guard_in_front_ok"] = 0.14 <= -fl[1] <= 0.36 and 0.12 <= -fr[1] <= 0.34
    res["guard_stagger_ok"] = 0.005 <= (fr[2] - fl[2]) <= 0.09
    return res


def main():
    arm, meshes = A.open_animation_project()
    scene = A.setup_scene()

    keyframes = [(frame, idle_pose(arm, breath)) for frame, breath in BREATH_KEYS]
    meta = {
        "anim_id": NAME,
        "loop": True,
        "category": "基础移动",
        "note": "战斗待机：宽站低重心，拳护胸前，胸腹呼吸，脚不动",
        "root_motion_m": [0.0, 0.0],
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.add_markers(action, {"LOOP_START": 0, "INHALE_PEAK": 72,
                           "HOLD_END": 96, "LOOP_END": TOTAL})

    samples = A.sample_animation(arm, action, 0, TOTAL, meshes)
    report = A.run_common_assertions(samples, meta)
    report.update(idle_assertions(samples))
    report["meta"] = meta
    failed = sorted(k for k, v in report.items()
                    if k.endswith("_ok") and v is not True)
    report["failed"] = failed
    A.report("IDLE01_REPORT", report)

    frames = [0, 72, 132]
    A.render_pose_sheet(arm, action, frames, "idle01",
                        views=(A.VIEW_SIDE, A.VIEW_FRONT))
    A.save_project()
    A.export_glb(arm)
    print("IDLE01_DONE failed=%s" % failed)


if __name__ == "__main__":
    # 必须加这道守卫：Idle_02 起后续动画都要 `import anim_idle_01` 复用
    # `idle_pose` / `ARM_DIRS` / `FIST`。没有守卫时 import 会**顺带把 A01 整支
    # 重跑一遍**（重渲 6 张静帧 + 存盘 + 导 GLB），既白花时间，又让"我这一轮
    # 到底改了哪支"变得不可读。`blender --python anim_idle_01.py` 时
    # `__name__ == "__main__"`，命令行行为完全不变。
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("IDLE01_FAILURE " + traceback.format_exc())
