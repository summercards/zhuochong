"""probe_air08 —— B08 `Air_Light` 开工前的四项实测（先量再做，不许拍脑袋）。

清单下一支计划要求量的四项：

1. **carry 起点**：把 `Jump_Fall@0` 的完整姿态 + 六根臂骨世界四元数读回来当 B08 的
   carry 起点（**不重算** —— `aim_carry` 是有状态接力）。读完必须
   `arm.animation_data.action = None`（A11 实测：留着上游 action 会污染尺子）。
2. **膝撞可达性**：把 R 踝目标沿"髋相对"扫一遍，看膝（`shin.R` head）
   相对骨盆能抬多高、`|髋−踝|` 还剩多少余量（B07 攻击腿只剩 7.7 mm）。
   ⟹ 先量再定提膝高度，别等门禁红了才发现够不到。
3. **拳的目标几何**：量 `REL0 = 拳峰 − 肩`（guard），以及臂长上界
   （`上臂+前臂+手骨`），才能知道"向前 300 mm 以上"这个要求能不能在不夹取的情况下做到。
4. **反向冲量的量级**：整段骨盆水平漂移可动多少（`AIR_DRIFT_MAX_MM` 阈值定案）。

本探针**不改任何文件**、只读 + 纯几何计算。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python probe_air08.py
"""

import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A          # noqa: E402
import anim_idle_01 as I1     # noqa: E402
import anim_jump_start as JS  # noqa: E402
import anim_jump_up as JU     # noqa: E402
import anim_jump_fall as JFE  # noqa: E402

SIDES = ("L", "R")
FRONT = "L"      # Idle_01：前脚 L（y = −0.170）
REAR = "R"       # 后脚 R（y = +0.140）—— 膝撞用后腿


def mm(v):
    return [round(x * 1000.0, 1) for x in v]


def knee_of(hip, ankle, thigh, shin, bulge):
    """两骨 IK 的膝位置（与 `anim_uppercut.leg_aim` 同一公式，纯几何）。"""
    delta = Vector(ankle) - Vector(hip)
    raw = delta.length
    distance = max(1e-4, min(raw, (thigh + shin) * 0.9995))
    axis = delta.normalized() if delta.length > 1e-9 else Vector((0.0, 0.0, -1.0))
    b = Vector(bulge)
    b = b - axis * b.dot(axis)
    b = b.normalized() if b.length > 1e-9 else Vector((0.0, -1.0, 0.0))
    cos_hip = (thigh ** 2 + distance ** 2 - shin ** 2) / (2.0 * thigh * distance)
    cos_hip = max(-1.0, min(1.0, cos_hip))
    sin_hip = math.sqrt(max(0.0, 1.0 - cos_hip * cos_hip))
    return Vector(hip) + (axis * cos_hip + b * sin_hip) * thigh, raw, distance


def main():
    arm, meshes = A.open_animation_project()
    A.setup_scene()

    if JFE.NAME not in bpy.data.actions:
        print("AIR08_PROBE 动画工程缺 %s —— 无法读接缝" % JFE.NAME)
        return

    # ---------------------------------------------------------- 1) carry 起点
    start_pose, start_quats = JU.capture_start(
        arm, bpy.data.actions[JFE.NAME], 0)
    start_mats = JFE.CR.action_world_matrices(arm, bpy.data.actions[JFE.NAME], 0)
    # ★ 读完立刻卸 action：否则后续 view_layer.update() 会把上游 f-curve 压回 pose bone
    arm.animation_data.action = None
    bpy.context.view_layer.update()

    rest_ankle = {}
    I1.idle_pose(arm, 0.0)
    rest_ankle = {s: Vector(A.bone_world(arm, "foot." + s, "head")) for s in SIDES}

    # 把 capture 到的姿态重新 apply 一次，逐骨量世界坐标（尺子干净：action 已卸）
    A.apply_pose(arm, start_pose)
    bpy.context.view_layer.update()
    world = {}
    for name in ("pelvis", "chest", "neck", "head", "upperarm.L", "upperarm.R",
                 "hand.L", "hand.R", "forearm.L", "forearm.R",
                 "thigh.L", "thigh.R", "shin.L", "shin.R", "foot.L", "foot.R",
                 "shoulder.L", "shoulder.R"):
        world[name] = Vector(A.bone_world(arm, name, "head"))
    world["hand.L.tail"] = Vector(A.bone_world(arm, "hand.L", "tail"))
    world["hand.R.tail"] = Vector(A.bone_world(arm, "hand.R", "tail"))
    hand_dir = {s: tuple(A.bone_direction(arm, "hand." + s)) for s in SIDES}
    hand_len = {s: (world["hand.%s.tail" % s] - world["hand.%s" % s]).length
                for s in SIDES}
    arm_len = {s: (world["upperarm.%s" % s] - world["forearm.%s" % s]).length
               + (world["forearm.%s" % s] - world["hand.%s" % s]).length
               for s in SIDES}
    leg_len = (A.L_THIGH, A.L_SHIN)

    A.report("AIR08_SEAM", {
        "source": "%s@0" % JFE.NAME,
        "pose_channels": sorted(k for k in start_pose if not k.startswith("@")),
        "pose_loc": {k: mm(v) for k, v in start_pose.get("@loc", {}).items()},
        "arm_quat_present": sorted(start_quats.keys()),
        "pelvis_z_mm": round(world["pelvis"].z * 1000.0, 2),
        "pelvis_xy_mm": mm(world["pelvis"])[:2],
        "hip_z_mm": {s: round(world["thigh." + s].z * 1000.0, 1) for s in SIDES},
        "knee_mm": {s: mm(world["shin." + s]) for s in SIDES},
        "ankle_mm": {s: mm(world["foot." + s]) for s in SIDES},
        "hip_ankle_mm": {s: round((world["foot." + s]
                                   - world["thigh." + s]).length * 1000.0, 1)
                         for s in SIDES},
        "hip_ankle_vert_mm": {s: round((world["thigh." + s].z
                                        - world["foot." + s].z) * 1000.0, 1)
                              for s in SIDES},
        "knee_below_hip_mm": {s: round((world["thigh." + s].z
                                        - world["shin." + s].z) * 1000.0, 1)
                              for s in SIDES},
        "shoulder_mm": {s: mm(world["upperarm." + s]) for s in SIDES},
        "fist_mm": {s: mm(world["hand.%s.tail" % s]) for s in SIDES},
        "fist_rel_shoulder_mm": {
            s: mm(world["hand.%s.tail" % s] - world["upperarm." + s])
            for s in SIDES},
        "fist_rel_len_mm": {
            s: round((world["hand.%s.tail" % s]
                      - world["upperarm." + s]).length * 1000.0, 1)
            for s in SIDES},
        "hand_dir": hand_dir,
        "hand_len_mm": {s: round(hand_len[s] * 1000.0, 2) for s in SIDES},
        "arm_len_mm": {s: round(arm_len[s] * 1000.0, 2) for s in SIDES},
        "fist_reach_max_mm": {s: round((arm_len[s] + hand_len[s]) * 1000.0, 1)
                              for s in SIDES},
        "fold_min_mm": {s: round(arm_len[s] * 0.32 * 1000.0, 1) for s in SIDES},
        "leg_len_mm": round((leg_len[0] + leg_len[1]) * 1000.0, 1),
        "note": ("`fist_reach_max_mm` = 上臂+前臂+手骨，是**拳峰离肩的几何上界**"
                 "（拳沿手骨方向伸直时取到）。向前 300 mm 的要求必须在这个上界内。"),
    })

    # ---------------------------------------------------------- 2) 膝撞可达性
    hip = world["thigh." + REAR]
    base_ankle = world["foot." + REAR]
    base_knee = world["shin." + REAR]
    pelvis = world["pelvis"]
    rows = []
    # 踝目标按"髋相对"扫：dz 从 −0.62（f0 附近）到 −0.30，
    # dy 从 rest(0.140) 到 −0.41（大腿抬到水平）。
    dy_list = (0.140, 0.060, -0.060, -0.180, -0.300, -0.410)
    dz_list = (-0.618, -0.560, -0.500, -0.450, -0.412, -0.360, -0.300)
    for dy in dy_list:
        for dz in dz_list:
            target = Vector((hip.x, hip.y + dy, hip.z + dz))
            knee, raw, _ = knee_of(hip, target, A.L_THIGH, A.L_SHIN,
                                   (0.0, -1.0, 0.0))
            rows.append({
                "ankle_rel_mm": [round(dy * 1000.0, 1), round(dz * 1000.0, 1)],
                "req_mm": round(raw * 1000.0, 1),
                "headroom_mm": round((A.L_THIGH + A.L_SHIN - raw) * 1000.0, 1),
                "knee_fwd_mm": round((hip.y - knee.y) * 1000.0, 1),
                "knee_below_hip_mm": round((hip.z - knee.z) * 1000.0, 1),
                "knee_rise_vs_base_mm": round(
                    (knee.z - base_knee.z) * 1000.0, 1),
                "knee_rise_vs_pelvis_mm": round(
                    ((pelvis.z - knee.z) - (pelvis.z - base_knee.z)) * 1000.0, 1),
            })
    best = max(rows, key=lambda r: r["knee_fwd_mm"])
    A.report("AIR08_KNEE_SWEEP", {
        "hip_mm": mm(hip), "base_knee_mm": mm(base_knee),
        "base_ankle_mm": mm(base_ankle),
        "base_knee_below_hip_mm": round((hip.z - base_knee.z) * 1000.0, 1),
        "base_knee_fwd_mm": round((hip.y - base_knee.y) * 1000.0, 1),
        "rows": rows,
        "best_knee_fwd": best,
        "note": ("`knee_rise_vs_pelvis_mm` 就是 `knee_strike_ok` 要量的量"
                 "（`shin.R` head 相对骨盆高度的上升，阈值草案 150 mm）。"
                 "老规矩：提膝越高，|髋−踝| 越大、余量越小。"),
    })

    # ---------------------------------------------------------- 3) 拳的目标几何
    punch = "L"     # 前手直拳
    rel0 = world["hand.L.tail"] - world["upperarm.L"]
    reach_max = (arm_len[punch] + hand_len[punch])
    fold_min = arm_len[punch] * 0.32
    cand = []
    for dz in (0.0, 0.04, -0.04):
        for dy in (-0.30, -0.34, -0.38, -0.42, -0.46, -0.50, -0.55):
            want = Vector((0.06, dy, dz)).normalized()
            length = min(rel0.length + 0.20, reach_max * 0.9995)
            rel = want * length
            cand.append({
                "target_rel_mm": mm(rel),
                "rel_len_mm": round(length * 1000.0, 1),
                "y_advance_vs_guard_mm": round(
                    (rel.y - rel0.y) * 1000.0, 1),
                "wrist_req_mm": round(
                    (length + (hand_len[punch] if False else 0.0)) * 1000.0, 1),
                "in_band": bool(fold_min <= length - hand_len[punch] <= reach_max),
            })
    A.report("AIR08_PUNCH_GEOM", {
        "punch_side": punch, "guard_side": REAR,
        "rel0_mm": mm(rel0), "rel0_len_mm": round(rel0.length * 1000.0, 1),
        "arm_len_mm": round(arm_len[punch] * 1000.0, 1),
        "hand_len_mm": round(hand_len[punch] * 1000.0, 1),
        "reach_max_mm": round(reach_max * 1000.0, 1),
        "fold_min_mm": round(fold_min * 1000.0, 1),
        "candidates": cand,
        "note": ("★ 想让拳峰**世界 −y 前移 ≥300 mm**，其实不必让 |拳−肩| 变长"
                 "—— 因为「拳峰世界前移」= 肩前移 + 相对前移。但肩在空中的前移"
                 "受 `air_drift_ok`(≤60 mm) 限制 ⟹ 主要还得靠相对前移，"
                 "即 `y_advance_vs_guard_mm` 这一列必须 ≥ ~260。"),
    })

    # ---------------------------------------------------------- 4) 反向冲量预算
    A.report("AIR08_DRIFT_BUDGET", {
        "air_drift_max_mm_draft": 60.0,
        "b07_ground_drift_mm": 0.0,
        "reason": ("蹬地类（B04~B07）有地面反力，骨盆漂移必须 0；空中没有反作用力，"
                   "出拳必然给骨盆一个反向冲量。60 mm ≈ 0.8 倍肩宽的 8%，"
                   "读作'有反冲但不成漂移'。"),
        "mitigation": ("制动力只能由对侧肢体提供：后手 R 向后摆 + 后腿 R 提膝前送，"
                       "两者对骨盆的角动量反向 ⟹ 由**躯干扭转（ry）**吃掉，"
                       "骨盆自己的 x/y 轨另给一条小轨（≤40 mm 前送）。"),
    })

    # ---------------------------------------------------------- 5) 末帧回收可行性
    A.report("AIR08_RETURN_PLAN", {
        "seam_end_target": "%s@0（与首帧逐位相同）" % JFE.NAME,
        "frames_available": [16, 20],
        "method": ("末帧直接写回 `Jump_Fall@0` 的姿态字典（`_unwrap_xyz` 折算到"
                   "离 f19 最近的等价表示 ⟹ 世界矩阵逐位不变、欧拉不跳）。"
                   "前 4 帧（f16~f19）用 `_ease_ramp` 把目标从命中值收回 guard 值，"
                   "两端速度为 0 ⟹ f19 ≈ f20，末帧步长天然小。"),
        "risk": "若 f19→f20 仍 >25°，把 RETURN 加长（TOTAL 20→22）而不是放宽阈值。",
    })
    print("AIR08_PROBE_DONE")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("AIR08_PROBE_FAILURE " + traceback.format_exc())
