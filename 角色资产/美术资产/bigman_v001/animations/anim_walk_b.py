"""anim_walk_b —— A04 `Walk_B` 后退。

设计（对着清单「下一支计划 —— A04」逐条落）：
    定位      面朝敌人倒退，脚步谨慎，身体保持防御姿态。**禁止直接播放前走倒放**。
    周期      72 帧 / 1.200 s @60fps（两步），**循环**（首末帧同一相位生成）。
    步长      0.27 m（比前走小 25%）→ 后退速率 **0.450 m/s**（登记 locomotion_mps）。
    支撑期    36 帧（50%，两脚首尾相接，**无腾空**）。
              支撑脚相对身体从 **+0.135（身后）滑到 −0.135（身前）**，
              即"相对身体朝 −Y 匀速滑" —— 速率 −0.450 m/s。
    摆动期    36 帧，脚底离地峰值 ~35 mm（判据 **25~45 mm**：上限也要卡，
              太高就是"迈步"而不是"试探"）。抬脚包络峰值前移（pow 0.85）→
              下落段占 58%，读起来是"先抬起来、再探着放下"。
    躯干      **直立**（胸骨顶相对骨盆 −10 ~ +20 mm）。前走是"压"着走（+48），
              后退是"扛"着走 —— 重心留在前脚，上身不朝行进方向倒。
    触地      **脚尖先落**（见下），落地后 10 帧内把脚背收平。
    脚背滚动  tip 是 **V 形**：+11（脚尖先落）→ 0（全掌）→ +24（抬跟推离）。
              前走是**单调** 0 → +24（平放落 → 抬跟）。这一条是"不是倒放"的
              第二组机器可验证证据。
    手臂      保持 A01 护体架势并**收紧**（肘内收 5°），前后摆幅 2°（前走 4°）——
              防守时手不该甩开。
    脚不滑    沿用 Walk_F 口径 `stance_slide_is_linear`（支撑期匀速滑移），
              速率 = −0.450 m/s（不是 A01 的"脚不动 3 mm"）。

---------------------------------------------------------------------------
两处**口径修正**（附推导 —— 不改清单正文，写在这里备案）

1) 「禁止倒放」的判据，清单把符号记反了。
   清单原文：「摆动期末、触地那一帧，脚底最低点必须位于踝的**后方**（low_z 对应的
   顶点 y > 踝 y），且 foot 世界转角为**负**（勾脚尖，−12°）」，并称「倒放 Walk_F 的
   触地帧必然是**脚跟先落（转角 +）**」。
   实测语义（`doc/rig_axis_map.md` + `anim_lib.add_world_rx` 的推导）：
   **正**世界转角 = 绕 +X 正转 = 脚尖朝下（压脚背 / 踮脚）；**负**转角 = 脚跟朝下。
   于是清单里那两条判据（最低点在踝**后方** + 转角为**负**）互相自洽，
   但它们描述的是 **脚跟先落**，与同一段文字的目标「脚尖先落」正好相反；
   而它给倒放贴的标签"转角 +"恰恰是脚尖先落。
   → 本支按**物理正确**的方式实现：**脚尖先落** ⟹ 触地帧鞋底最低点在踝的**前方**
   （鞋尖长在踝的前面）且世界转角为**正**（+11°）。真实倒退步态的着地方式也是
   前掌/脚尖先接触、随后脚跟落下，与倒放无关。

2) 「倒放」在 **foot 轨迹方向**上无法用参数镜像绕开 —— 那是运动学必然。
   原地动画里支撑脚永远相对身体朝**行进方向的反向**滑：后退必然"从身后滑到身前"，
   与前走"从身前滑到身后"方向相反。所以 foot 的 y 轨迹形状天然就是前走的镜像。
   真正把两支区分开的是**躯干朝向**（前倾 48 mm vs 直立 ≈0）与**足部滚动**
   （tip 单调 0→24 vs V 形 11→0→24），加上机器判据
   `not_reversed_walk_f_ok`（逐帧对 Walk_F 的**时间反演**比角，最大差 ≥ 15°；
   真倒放会得到 ≈0°）。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python anim_walk_b.py
    SKIP_RENDER=1 只跑门禁（迭代用）。
"""

import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A  # noqa: E402
import anim_walk_f as WF  # noqa: E402  复用整套步态机器，不复制粘贴

NAME = "Walk_B"
TOTAL = 72                       # 1.200 s @60fps，两步
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"

# ---------------------------------------------------------------- 步态参数
STEP_M = 0.27                    # 步长（比前走小 25% → "谨慎"）
LOCOMOTION_MPS = STEP_M * 2.0 / (TOTAL / float(A.FPS))     # 0.450 m/s
STANCE_FRAMES = 36               # 50%，与摆动期首尾相接 → 双支撑 ~0、无腾空
FLAT_FRAMES = 28                 # 全掌平放窗口：第 28~36 帧抬跟
SWING_FRAMES = TOTAL - STANCE_FRAMES
SLIDE_M = LOCOMOTION_MPS * STANCE_FRAMES / float(A.FPS)    # 0.270 m
TOUCH_FRAMES = 10                # 触地后 10 帧把"脚尖先落"的压脚背角收平
TIP_TOUCH_DEG = 11.0             # 触地脚背角（+ = 脚尖朝下）
TIP_DEG = 24.0                   # 抬跟推离角（与前走同量级）
SWING_TIP_DECAY = 0.25           # 摆动期前 25% 内把抬跟角收到触地角
CLEAR_PEAK = 0.035               # 抬脚峰值 35 mm
CLEAR_EXP = 0.7
CLEAR_POW = 0.85                 # <1 → 峰值前移 = 下落段更长（"探"）

ANKLE_X = 0.100                  # 轨道半宽：步幅小，重心不过度外移
PELVIS_X_AMP = 0.016             # 左右 ±16 mm（峰峰 32 ≤ 40）
PELVIS_Y_AMP = 0.005             # 前后 ±5 mm（峰峰 10 ≤ 25，净 0）
PELVIS_BOB = 0.009               # 升降 ±9 mm（峰峰 18 ≥ 15，比前走 28 小）
PELVIS_DROP = -0.058             # 基础下沉比前走多 3 mm（防御姿态重心更低）
PELVIS_RX = 0.0                  # **骨盆不前倾**（前走 2.5°）
PELVIS_TWIST = 1.8               # 扭髋幅度收敛（前走 3.0°）
SPINE_01_RX = 0.0
SPINE_02_RX = 0.0
CHEST_RX = 0.0                   # 脊椎四段 rx 全 0 ⟹ 直立
# 绕纵轴的扭转**逐段累加**：肩峰的世界扭转角 ≈ pelvis + spine_01 + spine_02 +
# chest。第一版照抄前走的"同号叠加"写法，得到世界扭转 4.0°（前走只有 2.0°），
# 于是肩峰行程 42.76 mm —— 比前走的 42.05 还大，与"防御姿态摆幅更小"正好相反。
# 本版把三段都压到"合计世界扭转 2.4°"：−1.8 + 1.1 + 1.1 + 2.0。
# 这三段仍非零且**单段 ≥1.0°**（清单 §0.6 的 power_chain 要求通道存在且非零 ——
# 第一版给到 0.6/0.8 被这条卡红，是"幅度收敛"踩到"通道存在性"的下限）。
SPINE_01_TWIST = 1.1
SPINE_02_TWIST = 1.1
CHEST_TWIST = 2.0
SHOULDER_SWING = 5.0             # 肩摆幅度（前走 9.0°）→ 肩峰行程 ~30 mm（前走 42）
SHOULDER_REST_RX = -18.0
ARM_SWING = 2.0                  # 摆臂幅度（前走 4.0°）—— 防守时不甩手
ARM_TUCK_DEG = 5.0               # 双肘内收 5°（"护体收紧"）

WALK_B = WF.Gait(
    name=NAME, total=TOTAL, step_m=STEP_M, stance_frames=STANCE_FRAMES,
    flat_frames=FLAT_FRAMES,
    # 两端斜率取 −SLIDE_M ⟹ **严格**速度连续（离地/触地瞬间脚相对身体的速度
    # 与支撑期完全一致）。前走当年取 0.32（比 0.36 小 11%）是它的一处遗留，
    # 本支不再沿用，见清单 A04 计划里的通用式 a = 2(c − D)、b = −1.5a。
    end_slope=-SLIDE_M,
    tip_deg=TIP_DEG, tip_touch_deg=TIP_TOUCH_DEG, touch_frames=TOUCH_FRAMES,
    swing_tip_decay=SWING_TIP_DECAY,
    clear_peak=CLEAR_PEAK, clear_exp=CLEAR_EXP, clear_pow=CLEAR_POW,
    tip_decay=SWING_TIP_DECAY,
    ankle_x=ANKLE_X, pelvis_x_amp=PELVIS_X_AMP, pelvis_y_amp=PELVIS_Y_AMP,
    pelvis_bob=PELVIS_BOB, pelvis_drop=PELVIS_DROP, pelvis_rx=PELVIS_RX,
    pelvis_twist=PELVIS_TWIST, pelvis_x_phase=WF.PELVIS_X_PHASE,
    spine_01_rx=SPINE_01_RX, spine_02_rx=SPINE_02_RX, chest_rx=CHEST_RX,
    spine_01_twist=SPINE_01_TWIST, spine_02_twist=SPINE_02_TWIST,
    chest_twist=CHEST_TWIST, neck_rx=WF.NECK_RX, head_rx=WF.HEAD_RX,
    shoulder_swing=SHOULDER_SWING, shoulder_rest_rx=SHOULDER_REST_RX,
    arm_swing=ARM_SWING, arm_tuck_deg=ARM_TUCK_DEG,
    torso_lean_band=(-10.0, 20.0), backward=True)


# ---------------------------------------------------------------- 触地证据
def contact_evidence(arm, meshes, action, gait):
    """逐脚取**触地那一帧**的实测证据，供 `toe_first_contact_ok` 判读。

    三项：踝的世界 y、鞋底**最低顶点**的世界 y/z、foot 相对 rest 的世界 X 转角。
    → "脚尖先落" ⟺ 最低顶点在踝的**前方**（y 更小）且转角为**正**。
    """
    scene = bpy.context.scene
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)

    out = {}
    for side, offset in (("L", 0.0), ("R", gait.right_offset)):
        frame = int(round(gait.total * offset))
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        name = "foot." + side
        point = A.lowest_point_by_side(meshes)[side]
        ankle = A.bone_world(arm, name, "head")
        out[side] = {
            "frame": frame,
            "ankle_y_mm": round(ankle.y * 1000.0, 2),
            "low_y_mm": round(point[1] * 1000.0, 2),
            "low_z_mm": round(point[2] * 1000.0, 2),
            "tip_deg": round(A.world_tip_deg(arm, name), 3),
            "toe_ahead_mm": round((ankle.y - point[1]) * 1000.0, 2),
        }
    return out


# ---------------------------------------------------------------- 专属门禁
def walk_b_assertions(gait, samples, evidence, reversal):
    res = {}
    frames = [s["frame"] for s in samples]

    # 1) 支撑期匀速滑移（Walk 版"脚不滑"）。速率必须是 **−0.450 m/s**：
    #    身体向 +Y 后退，支撑脚相对身体就向 −Y 前滑。横坐标用相位轴（不能用帧号，
    #    f0 与 f72 同姿态会把最小二乘拉成斜率为零的怪线 —— A03 踩过）。
    worst_dev = 0.0
    for side, offset in (("L", 0.0), ("R", gait.right_offset)):
        index = [i for i, f in enumerate(frames)
                 if WF.in_stance(gait, f, offset)]
        xs = [WF.wrap(frames[i] / float(gait.total) - offset) * gait.total
              for i in index]
        ys = [samples[i]["foot.%s" % side][1] for i in index]
        slope, _intercept, residual = WF._fit_line(xs, ys)
        res["stance_rate_mps_%s" % side] = round(slope * A.FPS, 4)
        res["stance_dev_mm_%s" % side] = round(residual * 1000.0, 3)
        worst_dev = max(worst_dev, residual)
    res["stance_slide_dev_mm"] = round(worst_dev * 1000.0, 3)
    res["stance_slide_is_linear"] = worst_dev * 1000.0 <= 5.0
    res["stance_rate_ok"] = all(
        abs(res["stance_rate_mps_%s" % side] - gait.stance_rate_mps) <= 0.03
        for side in ("L", "R"))

    # 2) 步长 0.22~0.32 m（比前走 0.30~0.45 小一档）。
    stride = 0.0
    for side in ("L", "R"):
        ys = [s["foot.%s" % side][1] for s in samples]
        stride = max(stride, max(ys) - min(ys))
    res["stride_m"] = round(stride, 4)
    res["stride_length_ok"] = 0.22 <= stride <= 0.32

    # 3) 抬脚高度 **25~45 mm**：上限也要卡 —— 抬太高就是"迈步"，不是"试探"。
    clearances = {}
    for side, offset in (("L", 0.0), ("R", gait.right_offset)):
        vals = [s["low"][side] for s in samples
                if WF.in_swing(gait, s["frame"], offset)]
        clearances[side] = round(max(vals) * 1000.0, 2)
    res["swing_clearance_mm"] = clearances
    res["swing_clearance_ok"] = all(25.0 <= v <= 45.0
                                    for v in clearances.values())

    # 4) 双支撑 ≤15%，且全程**无腾空**（走路）。
    contact = 5.0 / 1000.0
    together = sum(1 for s in samples
                   if s["low"]["L"] <= contact and s["low"]["R"] <= contact)
    ratio = together / float(len(samples))
    res["double_support_ratio"] = round(ratio, 4)
    res["double_support_ok"] = ratio <= 0.15
    airborne = sum(1 for s in samples
                   if s["low"]["L"] > contact and s["low"]["R"] > contact)
    res["airborne_frames"] = airborne
    res["no_airborne_ok"] = airborne == 0

    # 5) 骨盆：升降峰峰 ≥15 mm（比前走小）、水平不许自带位移。
    pelvis = [s["pelvis"] for s in samples]
    bob = (max(p[2] for p in pelvis) - min(p[2] for p in pelvis)) * 1000.0
    span_x = (max(p[0] for p in pelvis) - min(p[0] for p in pelvis)) * 1000.0
    span_y = (max(p[1] for p in pelvis) - min(p[1] for p in pelvis)) * 1000.0
    net_y = abs(pelvis[-1][1] - pelvis[0][1]) * 1000.0
    res["pelvis_bob_mm"] = round(bob, 2)
    res["pelvis_bob_ok"] = bob >= 15.0
    res["pelvis_span_x_mm"] = round(span_x, 2)
    res["pelvis_span_y_mm"] = round(span_y, 2)
    res["pelvis_net_y_mm"] = round(net_y, 3)
    res["pelvis_no_self_displacement_ok"] = (
        span_x <= 40.0 and span_y <= 25.0 and net_y <= 0.5)

    # 6) 躯干**直立**：胸骨顶相对骨盆前移 −10~+20 mm。
    #    （前走这里是 40~70 的 `lean_forward_ok`；本支**取消**该门禁换成这条。）
    leans = [(p[1] - s["neck"][1]) * 1000.0 for p, s in zip(pelvis, samples)]
    lean = leans[len(leans) // 2]
    res["torso_lean_mm"] = round(lean, 2)
    res["torso_lean_range_mm"] = [round(min(leans), 2), round(max(leans), 2)]
    res["torso_upright_ok"] = (gait.torso_lean_band[0] <= lean
                               <= gait.torso_lean_band[1])

    # 7) 肩随步伐摆：肩峰行程 ≥18 mm（比前走 42 小）且左右**反相**。
    sh_l = [s["upperarm.L"][1] for s in samples]
    sh_r = [s["upperarm.R"][1] for s in samples]
    travel_l = (max(sh_l) - min(sh_l)) * 1000.0
    travel_r = (max(sh_r) - min(sh_r)) * 1000.0
    corr = WF._correlation(sh_l, sh_r)
    res["shoulder_travel_mm"] = {"L": round(travel_l, 2),
                                 "R": round(travel_r, 2)}
    res["shoulder_swing_corr"] = round(corr, 3)
    res["shoulder_swing_ok"] = (min(travel_l, travel_r) >= 18.0
                               and corr <= -0.5)

    # 8) 力量传导链（脚→腿→髋→腰→肩→手，不许"只有手在动"）。
    res.update(WF.power_chain(samples))

    # 9) **脚尖先落** —— 本支的专属核心判据，也是"这是倒着走"的直接证据。
    toe_ok = True
    detail = {}
    for side, ev in evidence.items():
        # 鞋底最低顶点必须在踝的**前方**（y 更小），且至少前出 20 mm：
        # 脚跟先落时这个量必然是**负**的（最低点在踝后面），一眼可分。
        ahead_ok = ev["toe_ahead_mm"] >= 20.0
        tip_ok = ev["tip_deg"] >= 5.0          # 正 = 脚尖朝下（压脚背）
        detail[side] = {"ahead_ok": ahead_ok, "tip_ok": tip_ok, **ev}
        toe_ok = toe_ok and ahead_ok and tip_ok
    res["toe_first_contact_detail"] = detail
    res["toe_first_contact_ok"] = toe_ok

    # 10) **不是倒放**：把本支每一帧与 Walk_F 的**时间反演**逐骨比角，
    #     最大差必须 ≥15°。真做成倒放会得到 ≈0°。
    res["reversal_max_diff_deg"] = round(reversal["max_diff_deg"], 3)
    res["reversal_max_diff_at"] = reversal["at"]
    res["reversal_mean_diff_deg"] = round(reversal["mean_diff_deg"], 3)
    res["not_reversed_walk_f_ok"] = reversal["max_diff_deg"] >= 15.0
    return res


def reversal_report(gait, samples, ref_samples):
    """本支 vs Walk_F 时间反演（`Walk_F@(TOTAL−f)`）的逐骨角度最大差。"""
    total = int(gait.total)
    worst = 0.0
    worst_at = None
    total_diff = 0.0
    count = 0
    for sample in samples:
        frame = int(sample["frame"])
        reference = ref_samples[min(max(total - frame, 0), len(ref_samples) - 1)]
        for name in set(sample["euler"]) | set(reference["euler"]):
            a = sample["euler"].get(name, (0.0, 0.0, 0.0))
            b = reference["euler"].get(name, (0.0, 0.0, 0.0))
            diff = max(abs(x - y) for x, y in zip(a, b))
            total_diff += diff
            count += 1
            if diff > worst:
                worst, worst_at = diff, (frame, name)
    return {"max_diff_deg": worst, "at": worst_at,
            "mean_diff_deg": total_diff / max(count, 1)}


# ---------------------------------------------------------------- 主流程
def main():
    arm, meshes = A.open_animation_project()
    A.setup_scene()

    if "Idle_01" not in bpy.data.actions:
        print("WALKB_BOOTSTRAP 动画工程缺 Idle_01，先补跑 A01")
        import anim_idle_01 as I1
        I1.main()
        arm, meshes = A.open_animation_project()
        A.setup_scene()
    if NAME not in bpy.data.actions and "Walk_F" not in bpy.data.actions:
        print("WALKB_BOOTSTRAP 动画工程缺 Walk_F，先补跑 A03（时间反演判据的基准）")
        WF.main()
        arm, meshes = A.open_animation_project()
        A.setup_scene()

    # 逐帧打帧：支撑脚要钉在世界坐标上匀速前滑，每帧姿态都由 IK 反解得到。
    keyframes = [(frame, WF.gait_pose(arm, WALK_B, frame, meshes))
                 for frame in range(0, TOTAL + 1)]

    meta = {
        "anim_id": NAME,
        "loop": True,
        "category": "基础移动",
        "note": "后退：直立躯干、脚尖先落、步长 0.27m、0.450 m/s；原地动画，位移由程序给",
        "locomotion_mps": round(WALK_B.locomotion_mps, 4),
        "stride_m": STEP_M,
        "stance_ratio": round(STANCE_FRAMES / float(TOTAL), 4),
        "root_motion_m": [0.0, 0.0],
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.add_markers(action, {
        "L_TOUCH": 0, "L_FLAT": TOUCH_FRAMES, "L_TIP": FLAT_FRAMES,
        "L_OFF": STANCE_FRAMES,
        "R_TOUCH": int(WALK_B.right_offset * TOTAL),
        "R_TIP": int(WALK_B.right_offset * TOTAL) + FLAT_FRAMES,
        "CYCLE_END": TOTAL,
    })

    samples = A.sample_animation(arm, action, 0, TOTAL, meshes)
    # Walk 的正确"脚不滑"口径是"匀速"而不是"不动"，通用门禁的 3 mm 判据在这里
    # 必然假红（支撑脚要滑 0.27 m），故 foot_probe 置空。
    report = A.run_common_assertions(samples, meta, foot_probe=())

    ref_action = bpy.data.actions.get("Walk_F")
    ref_samples = A.sample_animation(arm, ref_action, 0, TOTAL, meshes)
    reversal = reversal_report(WALK_B, samples, ref_samples)

    evidence = contact_evidence(arm, meshes, action, WALK_B)
    # 把触地证据也写进 Action 自定义属性（引擎侧对位/调试可读）。
    action["toe_first_contact"] = str(evidence)

    report.update(walk_b_assertions(WALK_B, samples, evidence, reversal))
    report["meta"] = meta
    failed = sorted(k for k, v in report.items()
                    if k.endswith("_ok") and v is not True)
    report["failed"] = failed
    A.report("WALKB_REPORT", report)

    if not SKIP_RENDER:
        # 侧视：0 = 左脚触地（看脚尖先落）、36 = 右脚触地 / 左脚抬跟推离。
        A.render_pose_sheet(arm, action, [0, 10, 22, 36, 50, 64], "walkb",
                            views=(A.VIEW_SIDE,))
        A.render_pose_sheet(arm, action, [0, 18, 36], "walkb",
                            views=(A.VIEW_FRONT,))
    A.save_project()
    A.export_glb(arm)
    print("WALKB_DONE failed=%s" % failed)


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("WALKB_FAILURE " + traceback.format_exc())
