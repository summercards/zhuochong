"""anim_idle_02 —— A02 `Idle_02` 待机变化。

设计（对着清单「下一支计划 —— A02」的原文逐条落）：
    定位        长时间不操作时随机切入的"小动作"，播完必须能无缝回到 A01 的呼吸循环。
    时长        210 帧 = 3.500 s @60 fps，**非循环**。
    首末帧      与 `anim_idle_01.idle_pose(arm, 0.0)` 逐位一致 —— 首帧接在 A01
                呼气末，末帧回到同一姿态，于是"接得回去"不靠调参靠构造。
    动作序列    1) 脖子：head.ry ±14° / neck.ry ±6°，左 18 帧 → 停 → 右 → 停 → 回中
                2) 捏拳：手指从 FIST 张开到 −18°（行程 60°）→ 停 → 攥紧（微过 FIST）
                        配合前臂内旋 forearm.ry ±9°，拳头在胸前不动
                3) 甩肩：两拍，肩 rx −18 → −22（沉）→ −14（弹）→ −22 → −14
                4) 收势：f166 弹起后一路沉回战斗架势；末 12 帧落在 Bezier 的
                        ease-out 尾巴上，角度增量自然单调收敛（不许瞬停）
    位置不变    骨盆、腿、足全部原样继承 A01（breath=0）→ 脚纹丝不动，
                重心不晃（"活动筋骨"，不是"换姿势"）。

参数化做法：三条参数轨（neck_t / fist_t / shrug_t）叠加在 A01 基础姿态上。
    neck_t  +1 = 头左转到底， −1 = 右转到底， 0 = 正
    fist_t  +1 = 手指张开，   −1 = 攥紧，     0 = FIST
    shrug_t +1 = 耸肩沉，     −1 = 耸肩弹，   0 = 静息（−18°）
这样每个关键帧都是"基础姿态 + 三点偏移"，不会出现"某段忘了写、Blender 静默沿用上一帧"。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python anim_idle_02.py
    SKIP_RENDER=1 可跳过所有渲染，只跑门禁（迭代用）。
"""

import json
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A  # noqa: E402
import anim_idle_01 as I1  # noqa: E402

NAME = "Idle_02"
TOTAL = 210                     # 3.5 s @ 60 fps
HEAD_TURN = 14.0                # head.ry 峰值
NECK_TURN = 6.0                 # neck.ry 峰值
SHRUG_AMP = 4.0                 # 肩 rx 相对静息 −18° 的摆幅（沉 −22 / 弹 −14）
FOREARM_TWIST = 9.0             # 攥拳时前臂内旋（forearm.ry）
TAIL_FRAMES = 12                # 末段减速窗口（门禁口径）
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"

# 关键帧时间轴：(帧, neck_t, fist_t, shrug_t)
KEYS = (
    (0, 0.0, 0.0, 0.0),        # = Idle_01 breath 0
    (18, +1.0, 0.0, 0.0),      # 脖子向左到位
    (21, +1.0, 0.0, 0.0),      # 停 3 帧
    (44, -1.0, 0.0, 0.0),      # 脖子向右到位
    (47, -1.0, 0.0, 0.0),      # 停 3 帧
    (64, 0.0, 0.0, 0.0),       # 回中
    (72, 0.0, +1.0, 0.0),      # 手指张开
    (78, 0.0, +1.0, 0.0),      # 停 6 帧
    (90, 0.0, -1.0, 0.0),      # 攥紧
    (95, 0.0, -1.0, 0.0),      # 停 5 帧
    (108, 0.0, 0.0, 0.0),      # 松开回到 FIST
    (122, 0.0, 0.0, +1.0),     # 双肩下沉（第一拍）
    (136, 0.0, 0.0, -1.0),     # 双肩弹起
    (150, 0.0, 0.0, +1.0),     # 双肩再沉（第二拍）
    (164, 0.0, 0.0, -1.0),     # 双肩再弹
    (210, 0.0, 0.0, 0.0),      # 收势：沉回战斗架势（46 帧，自然减速）
)

MARKERS = {
    "START": 0,
    "NECK_LEFT": 18,
    "NECK_RIGHT": 44,
    "NECK_CENTER": 64,
    "FIST_OPEN": 72,
    "FIST_CLENCH": 90,
    "SHRUG_1_SINK": 122,
    "SHRUG_1_POP": 136,
    "SHRUG_2_SINK": 150,
    "SHRUG_2_POP": 164,
    "SETTLE": 164,
    "END": 210,
}


# --------------------------------------------------------------- 手指张/攥
def _digit_map(table):
    out = {}
    for digit in ("index", "middle", "ring", "pinky"):
        for seg, angle in table["finger"]:
            out["%s_%02d.L" % (digit, seg)] = angle
            out["%s_%02d.R" % (digit, seg)] = angle
    for seg, angle in table["thumb"]:
        out["thumb_%02d.L" % seg] = angle
        out["thumb_%02d.R" % seg] = angle
    return out


# 张开：不是"摊平手掌"，是松开拳（猛男待机里的"活动手指"，幅度克制但不含糊）。
# 门禁要求 1 号节行程 ≥ 40°：FIST(−78) → −18 即 60°。
OPEN_HAND = _digit_map({"finger": ((1, -18), (2, -22), (3, -16)),
                        "thumb": ((1, -10), (2, -8), (3, -6))})
# 攥紧：比 FIST 再紧一点（+5° 左右），给"捏"一个收势落点。
# 不敢过 95°：指节只有 ~30 mm，过度屈曲会穿掌。
CLENCH = _digit_map({"finger": ((1, -83), (2, -92), (3, -65)),
                     "thumb": ((1, -38), (2, -29), (3, -24))})


def finger_angles(t):
    """t ∈ [−1, +1] → 每根手指的三节 rx（0 为 FIST）。"""
    out = {}
    for key, value in A.FIST.items():
        base = value[0]
        target_table = OPEN_HAND if t >= 0.0 else CLENCH
        weight = t if t >= 0.0 else -t
        out[key] = (base + (target_table[key] - base) * weight, 0.0, 0.0)
    return out


# --------------------------------------------------------------- 姿态
def variation_pose(arm, neck_t, fist_t, shrug_t):
    """A01 基础姿态 + 三条参数轨。返回完整姿态字典（并已写进 arm）。"""
    pose = I1.idle_pose(arm, 0.0)          # 基础 = Idle_01 呼气末

    head_x, _head_y, head_z = pose["head"]
    pose["head"] = (head_x, HEAD_TURN * neck_t, head_z)
    neck_x, _neck_y, neck_z = pose["neck"]
    pose["neck"] = (neck_x, NECK_TURN * neck_t, neck_z)

    # 肩：静息是 A01 的沉肩 −18°，这里只在它上面加减，别写死绝对值
    for side in ("L", "R"):
        name = "shoulder." + side
        base_x, base_y, base_z = pose[name]
        pose[name] = (base_x - SHRUG_AMP * shrug_t, base_y, base_z)

    for key, angles in finger_angles(fist_t).items():
        pose[key] = angles

    # 前臂内旋：aim_bone 解出来的 euler 上叠一个 ry 偏量（local Y = 骨轴 = 扭转）
    twist = -FOREARM_TWIST * fist_t
    for side, mirror in (("L", 1.0), ("R", -1.0)):
        name = "forearm." + side
        fore_x, fore_y, fore_z = pose[name]
        pose[name] = (fore_x, fore_y + twist * mirror, fore_z)

    A.apply_pose(arm, pose)
    return pose


def euler_map(arm):
    return {pose_bone.name:
            tuple(math.degrees(v) for v in pose_bone.rotation_euler)
            for pose_bone in arm.pose.bones}


def pose_gap(sample_euler, reference):
    """逐骨最大角度差（只比参考里出现过的骨，采样里缺的按 0 算）。"""
    worst = 0.0
    for name, angles in reference.items():
        got = sample_euler.get(name, (0.0, 0.0, 0.0))
        worst = max(worst, max(abs(a - b) for a, b in zip(angles, got)))
    return worst


# --------------------------------------------------------------- 头部朝向测量
def head_yaw_series(arm, action, frame_start, frame_end):
    """逐帧头部**世界朝向的偏航角**。

    为什么要另测：`sample_animation` 记的是骨head/tail世界坐标，而 head 骨是竖直的，
    转头时"骨轴方向"几乎不变 —— 拿 tail−head 向量算角度会得到 ~0° 的假值。
    真正反映转头的是骨头的**横向参考轴**（local X）在世界 XY 平面里的方位角。
    """
    scene = bpy.context.scene
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    series = []
    for frame in range(int(frame_start), int(frame_end) + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        axis = arm.pose.bones["head"].matrix.to_3x3() @ Vector((1.0, 0.0, 0.0))
        series.append((frame, math.degrees(math.atan2(axis.y, axis.x))))
    return series


# --------------------------------------------------------------- 专属门禁
def idle02_assertions(arm, action, samples, reference):
    res = {}

    res["start_gap_deg"] = round(pose_gap(samples[0]["euler"], reference), 4)
    res["starts_from_idle_ok"] = res["start_gap_deg"] <= 0.3
    res["end_gap_deg"] = round(pose_gap(samples[-1]["euler"], reference), 4)
    res["ends_at_idle_ok"] = res["end_gap_deg"] <= 0.3

    yaw = head_yaw_series(arm, action, samples[0]["frame"], samples[-1]["frame"])
    base_yaw = yaw[0][1]
    peak = max(abs(v - base_yaw) for _f, v in yaw)
    peak_to_peak = max(v for _f, v in yaw) - min(v for _f, v in yaw)
    # 门禁口径是"单侧峰值"（头转到一边的幅度），不是峰峰值 —— 峰峰值天然是它的两倍，
    # 拿它去对"head.ry ≥ 10°"会比设计值宽松一倍，是假绿。
    res["head_yaw_peak_deg"] = round(peak, 2)
    res["head_yaw_p2p_deg"] = round(peak_to_peak, 2)
    res["head_turn_visible_ok"] = peak >= 10.0

    for digit in ("index_01", "middle_01"):
        for side in ("L", "R"):
            name = "%s.%s" % (digit, side)
            values = [s["euler"].get(name, (0.0, 0.0, 0.0))[0] for s in samples]
            span = max(values) - min(values)
            res["fist_travel_deg_%s" % name] = round(span, 2)
            res["fist_squeeze_visible_ok_%s" % name] = span >= 40.0

    # 「拳头在胸前不动」：捏拳窗口内 hand.tail（拳 = 掌指关节）不许漂
    window = [s for s in samples if 66 <= s["frame"] <= 104]
    drift = 0.0
    for name in ("hand.L.tail", "hand.R.tail"):
        anchor = Vector(window[0][name])
        drift = max(drift, max((Vector(s[name]) - anchor).length
                               for s in window))
    res["fist_drift_mm"] = round(drift * 1000.0, 2)
    res["fist_steady_ok"] = drift * 1000.0 <= 15.0

    # 「甩肩看得见」：肩峰（= upperarm.head）的升降幅度。肩骨只有 ~112 mm，
    # shoulder.rx 对"肩峰高度"的杠杆是 1.95 mm/°，8° 摆幅 ≈ 16 mm —— 必须量出来，
    # 不能假设"给了角度就一定看得见"。
    shrug = [s for s in samples if 108 <= s["frame"] <= 210]
    shoulder_z = [s["upperarm.L"][2] for s in shrug]
    fist_z = [s["hand.L.tail"][2] for s in shrug]
    res["shrug_shoulder_rise_mm"] = round((max(shoulder_z) - min(shoulder_z))
                                          * 1000.0, 2)
    res["shrug_fist_rise_mm"] = round((max(fist_z) - min(fist_z)) * 1000.0, 2)
    res["shrug_visible_ok"] = res["shrug_shoulder_rise_mm"] >= 8.0

    # 末 12 帧减速尾巴：任意通道的逐帧角度增量绝对值必须单调不增
    tail = samples[-(TAIL_FRAMES + 1):]
    steps = []
    for index in range(1, len(tail)):
        previous, current = tail[index - 1]["euler"], tail[index]["euler"]
        worst = 0.0
        for name in set(previous) | set(current):
            a = previous.get(name, (0.0, 0.0, 0.0))
            b = current.get(name, (0.0, 0.0, 0.0))
            worst = max(worst, max(abs(x - y) for x, y in zip(a, b)))
        steps.append(round(worst, 4))
    converged = all(steps[i] <= steps[i - 1] + 1e-6 for i in range(1, len(steps)))
    res["tail_steps_deg"] = steps
    res["no_snap_stop_ok"] = converged and steps[0] > 0.0
    return res


# --------------------------------------------------------------- 主流程
def main():
    arm, meshes = A.open_animation_project()
    A.setup_scene()

    # 动画工程里必须已经有 A01：Idle_02 的首末帧就是"接回 Idle_01 呼气末"，
    # 缺了它 GLB 里会少一支、引擎侧找不到回退动作。`import anim_idle_01`
    # 现在带 `__main__` 守卫不会再自动跑，所以这里显式补。
    if "Idle_01" not in bpy.data.actions:
        print("IDLE02_BOOTSTRAP 动画工程缺 Idle_01，先补跑 A01")
        I1.main()
        arm, meshes = A.open_animation_project()
        A.setup_scene()

    keyframes = []
    for frame, neck_t, fist_t, shrug_t in KEYS:
        keyframes.append((frame, variation_pose(arm, neck_t, fist_t, shrug_t)))
    reference = euler_map(arm)          # 首帧即为基础姿态，留作门禁基准

    meta = {
        "anim_id": NAME,
        "loop": False,
        "category": "基础移动",
        "note": "待机变化：转头 → 捏拳 → 甩肩 → 收势，首末帧回到 Idle_01 呼气末",
        "root_motion_m": [0.0, 0.0],
        "returns_to": "Idle_01",
        "returns_at_breath": 0.0,
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.add_markers(action, MARKERS)

    samples = A.sample_animation(arm, action, 0, TOTAL, meshes)
    report = A.run_common_assertions(samples, meta)
    report.update(idle02_assertions(arm, action, samples, reference))
    report["meta"] = meta
    failed = sorted(k for k, v in report.items()
                    if k.endswith("_ok") and v is not True)
    report["failed"] = failed
    A.report("IDLE02_REPORT", report)

    if not SKIP_RENDER:
        # 转头 / 捏拳 / 甩肩 都是"左右对称"的变化 → 正面看最清楚；
        # 侧视只留三帧用于核对"起手帧 = A01 呼气末"。
        A.render_pose_sheet(arm, action, [18, 44, 72, 90, 122, 164], "idle02",
                            views=(A.VIEW_FRONT,))
        A.render_pose_sheet(arm, action, [0, 90, 164], "idle02",
                            views=(A.VIEW_SIDE,))
    A.save_project()
    A.export_glb(arm)
    print("IDLE02_DONE failed=%s" % failed)


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("IDLE02_FAILURE " + traceback.format_exc())
