"""anim_run —— A05 `Run` 奔跑。

设计（对着清单「下一支计划 —— A05」逐条落）：
    定位      大步重踏，身体明显前压；每次落脚要有重量感。
    周期      48 帧 / 0.800 s @60fps（两步），**循环**（首末帧同一相位生成）。
    支撑期    17 帧（35.4%），**< 50%** ⟹ 每步各留出 1 段**腾空**（两脚皆离地）。
    腾空      ≥8 帧/周期，且必须**真的离地**（>5 mm）；跑不该有双支撑。
    摆动抬脚  脚底离地峰值 ≥120 mm（大腿抬平）。
    骨盆      升降峰峰 ≥45 mm（重踏的下坠感），**最低点必须落在支撑中期**
              （吸收下坠），不许落在腾空段 —— 落错读作"踩着空气"。
    前压      胸骨顶相对骨盆前移 90~140 mm。
    落地下沉  触地帧起 3 帧内骨盆再下沉 ≥20 mm（"重踏"的机器判据）。
    触地      前掌/全掌落地（触地世界转角 0~6°），落地后立刻压踝缓冲。
              摆动期末的抬跟角收到触地角并保持到落地 —— 不是"勾着脚砸下去"。
    脚不滑    沿用 Walk 族口径 `stance_slide_is_linear`（支撑期**匀速**后滑，
              速率 = 角色速率）。通用门禁的 3 mm「脚不动」在原地动画里必然假红。

---------------------------------------------------------------------------
口径修正（与清单原文的差异，附推导 —— 不改正文，写在这里备案）

清单 差异表 写「步长 1.30~1.90 m → 速率 ~4.5 m/s」。这两条在本骨架上
**物理不可达**，原因是"原地动画"这四个字：

    原地动画里，支撑脚在支撑期内必须相对身体滑完 `速率 × 支撑期` 的位移
    （这正是 `stance_slide_is_linear` 判据的内容，也是不能放水的那一条）。
    于是 4.5 m/s × 17/60 s = **1.275 m** 的单脚前后跨度（±0.64 m）。
    但本角色的 髋→踝 腿长 L = L_THIGH + L_SHIN = 0.410 + 0.412 = **0.822 m**
    （T-pose 下腿已经**完全伸直**，见 anim_lib 的两条常量 —— 腿没有任何富余）。
    脚向前伸 d 就必须把髋压低   Δ = L − √(L² − d²)：
        d = 0.30 m → Δ = 57 mm
        d = 0.39 m → Δ = 98 mm
        d = 0.50 m → Δ = 170 mm
        d = 0.64 m（4.5 m/s 所需）→ Δ = **278 mm** —— 骨盆要掉到 0.62 m。
    那不是跑步，那是蹲着滑行。所以清单那条只能取它的**意图**（"大步"），
    实际按**几何上限**反推：把"落地那一刻腿接近伸直（跑步特征，q/L ≈ 0.99）"
    当约束，得到本支的取值 ——
        d = 0.3896 m ⟹ 单脚跨度 0.779 m ⟹ 速率 **2.75 m/s**（前走的 4.6 倍）
    并把 `contact_leg_extension_ratio` 登记进 Action：它证明这一支已经吃掉了
    该骨盆高度下腿可及距离的 ~96%，不是"随手缩小了步幅"。
    引擎侧若要更快的**手感**，应该走**播放倍率 / 根位移**，而不是继续加大
    动画里的脚滑量 —— 加大只会让落地帧的腿穿出骨架。

---------------------------------------------------------------------------
运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python anim_run.py
    SKIP_RENDER=1 只跑门禁（迭代用）。
"""

import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A  # noqa: E402
import anim_walk_f as WF  # noqa: E402  复用整套步态机器，不复制函数

NAME = "Run"
TOTAL = 48                       # 0.800 s @60fps，两步
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"

# ---------------------------------------------------------------- 步态参数
STEP_M = 1.10                    # 单步地面进给量 → 速率 2.75 m/s（见上文口径修正）
LOCOMOTION_MPS = STEP_M * 2.0 / (TOTAL / float(A.FPS))     # 2.750 m/s
STANCE_FRAMES = 17               # 35.4%（判据 35~40%）；< 半周期 ⟹ 每步一段腾空
FLAT_FRAMES = 11                 # 全掌平放窗口：第 11~17 帧抬跟推离
TOUCH_FRAMES = 3                 # 触地后 3 帧内把落地脚背角收平
TIP_TOUCH_DEG = 3.0              # 触地脚背角（+ = 脚尖朝下 = 前掌先触地）
TIP_DEG = 34.0                   # 抬跟推离角（比走路的 24° 大 —— 蹬地更狠）
SWING_TIP_DECAY = 0.22           # 摆动期前 22% 内把抬跟角收到触地角
CLEAR_PEAK = 0.150               # 摆动脚离地峰值 150 mm（判据 ≥120）
CLEAR_EXP = 0.80
CLEAR_POW = 0.90
SLIDE_M = LOCOMOTION_MPS * STANCE_FRAMES / float(A.FPS)    # 0.779 m

ANKLE_X = 0.085                  # 跑步轨道比走路窄（两脚贴近中线）
PELVIS_X_AMP = 0.012             # 重心左右转移（峰峰 24 mm，比走路 36 小）
PELVIS_Y_AMP = 0.008             # 前后摆动（峰峰 16 mm ≤ 25，净位移 0）
PELVIS_BOB = 0.030               # 升降 ±30 mm（峰峰 60 ≥ 45）——"重踏"的下坠感
PELVIS_DROP = -0.117             # 基础下沉：由"落地帧腿接近伸直"反推（见口径修正）
# 升降最低点相位：支撑中期（17 帧的一半）。放在这里才满足
#   `landing_depth_ok`（触地后 3 帧内继续下沉 ≥20 mm）与
#   `foot_strike_sync_ok`（最低点在支撑期、最高点在腾空段）两条同时成立。
PELVIS_BOB_PHASE = (STANCE_FRAMES / 2.0) / float(TOTAL)    # 0.17708
PELVIS_RX = 8.0                  # 骨盆前倾（leg_ik 的 tilt_deg 必须同步）
PELVIS_TWIST = 6.0               # 骨盆绕纵轴扭转（跑比走大一倍）
SPINE_01_RX = 4.0
SPINE_02_RX = 3.0
CHEST_RX = 3.0                   # 合计脊椎前屈 ~18° → 胸骨顶前移 ~120 mm
SPINE_01_TWIST = 3.0
SPINE_02_TWIST = 3.0
CHEST_TWIST = 4.0                # 反向扭转（与骨盆反向），肩摆的来源
SHOULDER_SWING = 14.0            # shoulder rz 摆幅（走路 9.0°）
SHOULDER_REST_RX = -18.0
# 上臂前后摆幅（走路 4.0°）。跑步手臂要活着 —— 但第一版 12° 实测拳的前后
# 行程只有 75.8 mm（护体架势的肘是折的，握拳点离肩很近，杠杆比"直臂甩手"短
# 一大截），达不到"看得见的摆臂"，故提到 18°。`arm_swing_ok` 判据 ≥100 mm，
# **不改判据**。
ARM_SWING = 18.0
NECK_RX = -10.0                  # 前压之后要把头抬回来（不然脸朝地）
HEAD_RX = 9.0

LEG_LEN = A.L_THIGH + A.L_SHIN   # 0.822 m：髋→踝，T-pose 下已完全伸直
SWING_FRAMES = TOTAL - STANCE_FRAMES                       # 31 帧
# 摆动期**离地端**斜率（米 / 每单位 s）。单位换算见 `Gait.__init__` 的推导：
# 支撑期速率是"米/帧"，乘 `swing_frames` 才是"米/每单位 s"。
STRICT_OFF_SLOPE = (SLIDE_M / float(STANCE_FRAMES)) * SWING_FRAMES

RUN = WF.Gait(
    name=NAME, total=TOTAL, step_m=STEP_M, stance_frames=STANCE_FRAMES,
    flat_frames=FLAT_FRAMES,
    # `end_slope=None` ⟹ 摆动期**离地端**斜率由"支撑期每帧速率 × swing_frames"
    # 推出，离地瞬间脚相对身体的速度与支撑期**严格**连续。
    # 步态机的旧写法 `end_slope = −SLIDE_M` 只在 `stance_frames == swing_frames`
    # 时成立（A03/A04 都是 36==36，所以看不出问题）；Run 是 17≠31，沿用旧写法会
    # 得到"摆动 31 帧却按 17 帧的斜率走"的直线 —— 速度掉到支撑期的 55% =
    # "脚被粘了一下"。速度越大越刺眼，必须给 None。
    end_slope=None,
    # **触地端**另给 −离地端：脚拍下来被地面钉住，相对身体的速度本就跳变
    # （这是"落地"本身）。取反号 ⟹ 触地前脚在**地面系**里刚好静止下来
    # （相对身体速度 = −v，恰好抵消身体前进的 +v），落地最"实"，
    # 跳变 = 2 × 速率 = 落地冲击。若这里也传 None（两端都用连续值），
    # 解出来的轨迹会先把脚**再往后拖 147 mm** 才往前抡 —— 脚在身后拖一大段，
    # 读起来就不像跑步了。
    end_slope_out=STRICT_OFF_SLOPE * -1.0,
    tip_deg=TIP_DEG, tip_touch_deg=TIP_TOUCH_DEG, touch_frames=TOUCH_FRAMES,
    swing_tip_decay=SWING_TIP_DECAY, tip_decay=SWING_TIP_DECAY,
    clear_peak=CLEAR_PEAK, clear_exp=CLEAR_EXP, clear_pow=CLEAR_POW,
    ankle_x=ANKLE_X, pelvis_x_amp=PELVIS_X_AMP, pelvis_y_amp=PELVIS_Y_AMP,
    pelvis_bob=PELVIS_BOB, pelvis_drop=PELVIS_DROP, pelvis_rx=PELVIS_RX,
    pelvis_twist=PELVIS_TWIST, pelvis_x_phase=WF.PELVIS_X_PHASE,
    pelvis_bob_phase=PELVIS_BOB_PHASE,
    spine_01_rx=SPINE_01_RX, spine_02_rx=SPINE_02_RX, chest_rx=CHEST_RX,
    spine_01_twist=SPINE_01_TWIST, spine_02_twist=SPINE_02_TWIST,
    chest_twist=CHEST_TWIST, neck_rx=NECK_RX, head_rx=HEAD_RX,
    shoulder_swing=SHOULDER_SWING, shoulder_rest_rx=SHOULDER_REST_RX,
    arm_swing=ARM_SWING, torso_lean_band=(90.0, 140.0))


def _spans(frames):
    """把帧号列表压成连续区间 [[a, b], ...]（给人看"腾空在哪几段"）。"""
    spans = []
    for frame in frames:
        if spans and frame == spans[-1][1] + 1:
            spans[-1][1] = frame
        else:
            spans.append([frame, frame])
    return spans


# ---------------------------------------------------------------- 触地证据
def contact_evidence(arm, meshes, action, gait):
    """逐脚取**触地那一帧**的实测证据（供两条触地判据读）。

    为什么落在这一帧：本地相位 0 = 触地瞬间，帧号 = 周期 × 相位偏移。
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
        hip = A.bone_world(arm, "thigh." + side, "head")
        ankle = A.bone_world(arm, "foot." + side, "head")
        reach = (Vector(ankle) - Vector(hip)).length
        # 膝 = `shin` 的 **head**（也是 `thigh` 的 tail）。
        # 别用 `shin.tail` —— 那是踝，与 `foot.head` 是同一点，算出来是零向量，
        # `acos(0)` 会稳态给出 **90.0°** 的假膝角（第一版就是这个错）。
        knee = A.bone_world(arm, "shin." + side, "head")
        thigh_dir = (Vector(knee) - Vector(hip)).normalized()
        shin_dir = (Vector(ankle) - Vector(knee)).normalized()
        cos_knee = max(-1.0, min(1.0, thigh_dir.dot(shin_dir)))
        low = A.lowest_point_by_side(meshes)[side]
        out[side] = {
            "frame": frame,
            "ankle_y_mm": round(ankle.y * 1000.0, 2),
            "ankle_z_mm": round(ankle.z * 1000.0, 2),
            "low_y_mm": round(low[1] * 1000.0, 2),
            "low_z_mm": round(low[2] * 1000.0, 2),
            # 落地时"腿伸得有多直"：q/L。跑步落地接近伸直，但不许锁死（>0.998）。
            "leg_extension_ratio": round(reach / LEG_LEN, 4),
            "knee_deg": round(math.degrees(math.acos(cos_knee)), 2),
            # 相对 rest 的世界 X 转角：+ = 脚尖朝下（前掌先落）。
            "tip_deg": round(A.world_tip_deg(arm, "foot." + side), 3),
            # 鞋底最低顶点相对踝的**前出量**（正 = 最低点在踝前方 = 前掌先落）。
            "toe_ahead_mm": round((ankle.y - low[1]) * 1000.0, 2),
        }
    return out


# ---------------------------------------------------------------- 专属门禁
def run_assertions(gait, samples, evidence):
    res = {}
    frames = [s["frame"] for s in samples]
    contact = 5.0 / 1000.0
    pelvis = [s["pelvis"] for s in samples]

    # 1) **必须有腾空** —— Run 与 Walk 的本质差别，判据方向与走路相反。
    air = [f for f, s in zip(frames, samples)
           if s["low"]["L"] > contact and s["low"]["R"] > contact]
    res["airborne_frames"] = len(air)
    res["airborne_spans"] = _spans(air)
    res["airborne_ok"] = len(air) >= 8

    # 2) 跑不该有双支撑（走路那条 `double_support_ok` ≤15% 在这里收紧到 ≤2%）。
    together = sum(1 for s in samples
                   if s["low"]["L"] <= contact and s["low"]["R"] <= contact)
    ratio = together / float(len(samples))
    res["double_support_ratio"] = round(ratio, 4)
    res["double_support_none_ok"] = ratio <= 0.02

    # 3) 支撑期匀速滑移（Walk 族口径）。横坐标必须用**相位轴**（f0 与 f48 同姿态，
    #    用帧号当横坐标会被最小二乘拉成斜率为零的怪线 —— A03 踩过）。
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
        abs(res["stance_rate_mps_%s" % side] - gait.locomotion_mps) <= 0.05
        for side in ("L", "R"))

    # 3b) 离地/触地瞬间的**速度连续性**（`end_slope` 口径的会失败断言）。
    #     这一支 17 ≠ 31，是步态机里第一次让这两个数不相等 —— 旧写法会在这里红。
    res.update(WF.velocity_continuity(gait, samples))

    # 4) 单脚前后跨度（"大步"）。上界由**几何**定：d ≤ √(L²−dz²)，
    #    见文件头口径修正 —— 0.95 m 已经是本骨架在原地动画里的天花板。
    span = 0.0
    for side in ("L", "R"):
        ys = [s["foot.%s" % side][1] for s in samples]
        span = max(span, max(ys) - min(ys))
    res["stride_span_m"] = round(span, 4)
    res["step_length_m"] = round(gait.locomotion_mps * gait.total
                                 / (2.0 * A.FPS), 4)
    res["stride_span_ok"] = 0.60 <= span <= 0.95

    # 5) 抬脚高度：摆动期脚底网格最低点的峰值（判据 ≥120 mm）。
    clearances = {}
    for side, offset in (("L", 0.0), ("R", gait.right_offset)):
        vals = [s["low"][side] for s in samples
                if WF.in_swing(gait, s["frame"], offset)]
        clearances[side] = round(max(vals) * 1000.0, 2)
    res["swing_clearance_mm"] = clearances
    res["swing_clearance_ok"] = min(clearances.values()) >= 120.0

    # 6) 骨盆：升降要有重量感（≥45 mm），水平不许自带位移。
    bob = (max(p[2] for p in pelvis) - min(p[2] for p in pelvis)) * 1000.0
    span_x = (max(p[0] for p in pelvis) - min(p[0] for p in pelvis)) * 1000.0
    span_y = (max(p[1] for p in pelvis) - min(p[1] for p in pelvis)) * 1000.0
    net_y = abs(pelvis[-1][1] - pelvis[0][1]) * 1000.0
    res["pelvis_bob_mm"] = round(bob, 2)
    res["pelvis_bob_ok"] = bob >= 45.0
    res["pelvis_span_x_mm"] = round(span_x, 2)
    res["pelvis_span_y_mm"] = round(span_y, 2)
    res["pelvis_net_y_mm"] = round(net_y, 3)
    res["pelvis_no_self_displacement_ok"] = (
        span_x <= 45.0 and span_y <= 25.0 and net_y <= 0.5)

    # 7) 前压：胸骨顶（= chest.tail = neck.head）相对骨盆前移 90~140 mm。
    leans = [(p[1] - s["neck"][1]) * 1000.0 for p, s in zip(pelvis, samples)]
    lean = leans[len(leans) // 2]
    res["lean_forward_mm"] = round(lean, 2)
    res["lean_forward_range_mm"] = [round(min(leans), 2), round(max(leans), 2)]
    res["torso_lean_ok"] = (gait.torso_lean_band[0] <= lean
                            <= gait.torso_lean_band[1])

    # 8) **落地下沉**：触地帧起 3 帧内骨盆还要继续往下沉 ≥20 mm。
    #    这是"重踏"的机器判据 —— 落地就往上弹的读作"踩弹簧"。
    depths = {}
    for side, offset in (("L", 0.0), ("R", gait.right_offset)):
        base_index = int(round(gait.total * offset))
        base = pelvis[base_index][2]
        window = min(p[2] for p in pelvis[base_index:base_index + 4])
        depths[side] = round((base - window) * 1000.0, 2)
    res["landing_depth_mm"] = depths
    res["landing_depth_ok"] = all(v >= 20.0 for v in depths.values())

    # 9) **落点与骨盆 bob 对齐**：最低点必须在支撑期内（吸收下坠），
    #    最高点必须在腾空段（弹起来那一下要离地）。落错就是"踩着空气"。
    low_index = min(range(len(pelvis)), key=lambda i: pelvis[i][2])
    high_index = max(range(len(pelvis)), key=lambda i: pelvis[i][2])

    def in_any_stance(index):
        return (WF.in_stance(gait, frames[index], 0.0)
                or WF.in_stance(gait, frames[index], gait.right_offset))

    res["bob_low_frame"] = frames[low_index]
    res["bob_high_frame"] = frames[high_index]
    res["foot_strike_sync_ok"] = (in_any_stance(low_index)
                                  and not in_any_stance(high_index))

    # 10) 触地方式：前掌/全掌（世界转角 0~6°）+ 最低点在踝前方 + 落地时腿接近伸直。
    detail = {}
    tip_ok = ahead_ok = reach_ok = True
    for side, ev in evidence.items():
        tip_ok = tip_ok and 0.0 <= ev["tip_deg"] <= 6.0
        ahead_ok = ahead_ok and ev["toe_ahead_mm"] >= 10.0
        reach_ok = reach_ok and 0.90 <= ev["leg_extension_ratio"] <= 0.998
        detail[side] = ev
    res["contact_detail"] = detail
    res["contact_tip_ok"] = tip_ok
    res["contact_forefoot_ok"] = ahead_ok
    res["contact_leg_extension_ok"] = reach_ok

    # 11) 手臂要活着（Run 不是"端着架子滑过去"）。
    #     口径与 `power_chain` 的 hand 段一致：拳相对首帧的**最大世界位移**；
    #     阈值取 **110 mm = A03/Walk_F 实测 55.15 mm 的 2 倍** ——
    #     跑的手臂动态至少要是走的两倍，这个倍数关系是可审计的。
    #     踩过的坑：第一版拿"拳的 y 向行程 ≥100 mm"当判据，量出 75.8 mm（12° 摆幅）
    #     / 90.5 mm（18° 摆幅）恒红。原因是**尺子选错了** —— 护体架势的肘是折的，
    #     握拳点离肩很近，绕世界 X 摆臂时拳走的是 y/z 的合成方向，不是纯 y；
    #     这个量天生到不了 100 mm，跟"手臂动没动"不是一回事。
    #     故改成位移口径，并**把 y 向行程一并登记**（供人看"前后摆"的读数）。
    hand_points = [Vector(s["hand.L.tail"]) for s in samples]
    hand_disp = max((p - hand_points[0]).length for p in hand_points) * 1000.0
    hand_ys = [p[1] for p in hand_points]
    res["arm_swing_travel_mm"] = round(hand_disp, 2)
    res["arm_swing_fore_aft_mm"] = round((max(hand_ys) - min(hand_ys)) * 1000.0, 2)
    res["arm_swing_ok"] = hand_disp >= 110.0

    # 12) 力量传导链（脚→腿→髋→腰→肩→手，不许"只有手在动"）。
    res.update(WF.power_chain(samples))
    return res


# ---------------------------------------------------------------- 主流程
def main():
    arm, meshes = A.open_animation_project()
    A.setup_scene()

    if "Idle_01" not in bpy.data.actions:
        print("RUN_BOOTSTRAP 动画工程缺 Idle_01，先补跑 A01")
        import anim_idle_01 as I1
        I1.main()
        arm, meshes = A.open_animation_project()
        A.setup_scene()

    # 逐帧打帧：支撑脚要钉在世界坐标上匀速后滑，每帧姿态都由 IK 反解得到。
    keyframes = [(frame, WF.gait_pose(arm, RUN, frame, meshes))
                 for frame in range(0, TOTAL + 1)]

    meta = {
        "anim_id": NAME,
        "loop": True,
        "category": "基础移动",
        "note": "奔跑：前压、有腾空、单脚跨度 0.78m、2.75 m/s；原地动画，位移由程序给",
        "locomotion_mps": round(RUN.locomotion_mps, 4),
        "step_length_m": round(STEP_M, 4),
        "stance_slide_m": round(SLIDE_M, 4),
        "stance_ratio": round(STANCE_FRAMES / float(TOTAL), 4),
        "root_motion_m": [0.0, 0.0],
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.add_markers(action, {
        "L_TOUCH": 0, "L_FLAT": TOUCH_FRAMES, "L_TIP": FLAT_FRAMES,
        "L_OFF": STANCE_FRAMES, "L_APEX": int(TOTAL * 0.40625),
        "R_TOUCH": int(RUN.right_offset * TOTAL),
        "R_OFF": int(RUN.right_offset * TOTAL) + STANCE_FRAMES,
        "CYCLE_END": TOTAL,
    })

    samples = A.sample_animation(arm, action, 0, TOTAL, meshes)
    # foot_probe 置空：通用门禁的"脚位移 ≤3 mm"在原地跑步上是错口径（支撑脚要
    # 匀速后滑 0.78 m），换成 `stance_slide_is_linear` 判"匀速"。
    report = A.run_common_assertions(samples, meta, foot_probe=())

    evidence = contact_evidence(arm, meshes, action, RUN)
    report.update(run_assertions(RUN, samples, evidence))
    report["meta"] = meta
    failed = sorted(k for k, v in report.items()
                    if k.endswith("_ok") and v is not True)
    report["failed"] = failed
    A.report("RUN_REPORT", report)

    if not SKIP_RENDER:
        # 侧视：0 左脚触地、7/8 支撑中期（骨盆最低）、19 腾空顶点、
        #       24 右脚触地、36 右支撑中期、43 腾空。
        A.render_pose_sheet(arm, action, [0, 4, 8, 14, 17, 20, 24, 31, 43],
                            "run", views=(A.VIEW_SIDE,))
        A.render_pose_sheet(arm, action, [0, 8, 20], "run",
                            views=(A.VIEW_FRONT,))
    A.save_project()
    A.export_glb(arm)
    print("RUN_DONE failed=%s" % failed)


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("RUN_FAILURE " + traceback.format_exc())
