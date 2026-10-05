"""anim_crouch_idle —— A09 `Crouch_Idle` 蹲姿待机。

设计（对着清单「下一支计划 —— A09」逐条落）：
    定位      蹲姿呼吸循环，**身体不要上下漂浮过大**（清单原文 A09 条目）。
    时长      120 帧 / 2.000 s @60fps，**循环**（`loop=True`）。
    衔接      首帧**逐位等于 `Crouch@24`**（世界矩阵 delta ≤1e-6）—— 这是清单
              §0.5 对"过渡 → 循环"的硬要求，也是 A08 末帧刻意的设计目的。
    结构      吸 0~48（0.8 s）/ 停 48~66（0.3 s）/ 呼 66~120（0.9 s）
              —— A01 的 吸 1.2 / 停 0.4 / 呼 1.4 按 2 s 等比压缩。
    呼吸      只归**胸腔**（`chest`）+ 肩（`shoulder`）+ 颈/头微量补偿；
              骨盆**倾角恒定 13.5°**、腿与踝由 `leg_to` 钉在世界坐标上。
    手臂      沿用 A08 的口径 `swung(ARM_DIRS, lean − LEAN0)`，**不单独给臂轨** ——
              呼吸带来的 `lean` 变化自动变成手臂相对胸口的微动。

---------------------------------------------------------------------------
本支的三个关键做法（都有前几支的实测依据）

1. **基座不重写，直接取 A08 的 `Crouch@24` 参数值。**
   清单注意第 1 条要求"首帧逐位等于 `Crouch@24`"。做法不是"再算一遍希望能对上"，
   而是把 A08 的 7 条躯干轨 + 3 条骨盆位移轨的**末键值**原样取来当基座常量
   （`CR.PELVIS_RX[-1][1]` 而不是硬编码 13.5）—— 浮点逐位一致，不靠运气。
   腿/足/臂的解算路径与 A08 **完全同一条**（`TURN.leg_to` + `keep_world_orientation`
   + `A.FIST` + `aim_bone(swung(...))`），只是参数换成"基座 + 呼吸偏移"。

2. **贴地常数**重跑** A08 的标定，而不是沿用它的数字。**
   A08 遗留第 3 条明确警告：蹲姿下膝弯 90° 的蒙皮影响 ≠ 蹲下过程中任一帧的影响。
   本支在 `main` 里重跑 `CR.calibrate()`（同一条代码路径 ⟹ 结果必然与 A08 相同，
   因为 A08 的标定区间 1~24 帧本来就覆盖了末帧蹲姿），并**复报**蹲姿区间实测鞋底
   范围，用来证明"沿用这组常数不会把 `ground_contact_ok` 顶红"。

3. **循环的呼吸曲线两端切线必须都为 0。**
   `TURN.track` 只把**末段**切线置 0（那是 A06 给"收招不许瞬停"写的修法），
   首段用的是割线斜率。循环动画的 f0 与 f120 是同一个姿态、同一个呼吸极值点，
   速度必须都是 0 —— 用 `TURN.track` 会在**循环点**制造一次速度跳变
   （f120 平着进来、f0 斜着出去）。本支改用 `breath_at()`：逐段 smoothstep，
   两端与每个键上速度天然为 0，循环点真正闭合。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python anim_crouch_idle.py
    SKIP_RENDER=1 只跑门禁（迭代用）。
"""

import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A       # noqa: E402
import anim_idle_01 as I1  # noqa: E402
import anim_walk_f as WF   # noqa: E402
import anim_turn as TURN   # noqa: E402   （复用 track / leg_to）
import anim_crouch as CR   # noqa: E402   （复用 calibrate / knee_series / matrix_delta）

NAME = "Crouch_Idle"
TOTAL = 120                      # 2.000 s @ 60 fps
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"

ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")

# ---------------------------------------------------------------- 基座 = Crouch@24
# **一律从 A08 的轨迹末键取**，不硬编码数字 —— 这样"首帧逐位等于 Crouch@24"
# 是构造出来的，不是调参调出来的（A02 的 `neck_t`/`fist_t` 用的是同一手法）。
BASE_PELVIS_RX = CR.PELVIS_RX[-1][1]        # 13.5  髋已折叠
BASE_SPINE01_RX = CR.SPINE01_RX[-1][1]      #  5.0
BASE_SPINE02_RX = CR.SPINE02_RX[-1][1]      #  4.8
BASE_CHEST_RX = CR.CHEST_RX[-1][1]          #  3.2
BASE_NECK_RX = CR.NECK_RX[-1][1]            # −10.0
BASE_HEAD_RX = CR.HEAD_RX[-1][1]            #  7.8
BASE_SHOULDER_RX = CR.SHOULDER_RX[-1][1]    # −20.5
BASE_PELVIS_X = CR.PELVIS_X[-1][1]          #  0.0
BASE_PELVIS_Y = CR.PELVIS_Y[-1][1]          #  0.0255（重心压在脚上的后坐）
BASE_PELVIS_Z = CR.PELVIS_Z[-1][1]          #  0.6280

# ---------------------------------------------------------------- 呼吸幅度
# 清单注意最后一条：「幅度整体按 A01 的 ~60% 起步：蹲姿下没有'展开胸腔'的空间，
# 同样的度数读起来更大。」A01 的实测幅度是 chest 3.5° / shoulder 5.0° / 骨盆 3 mm。
CHEST_AMP = 2.1        # 3.5 × 0.60   → 胸骨顶行程预估 180 mm · sin(2.1°) ≈ 6.6 mm
SHOULDER_AMP = 3.0     # 5.0 × 0.60   → 肩峰行程预估 ≈ 7.7 mm
NECK_AMP = 0.3         # 颈/头补偿：让头在空间里的朝向基本不动（A01 踩坑 3 同源）
HEAD_AMP = 1.2         # 净头部朝向变化 = −2.1 − 0.3 + 1.2 = −1.2°
PELVIS_Z_AMP = 0.0030  # 与 A01 同量级（3 mm）；门禁 `bob_amplitude_ok` 上限 12 mm

# 呼吸关键帧：(帧, 幅度)。0 = 呼气末（= Crouch@24），1 = 吸气峰。
# 吸 0→48 / 停 48→66 / 呼 66→120，两端与每个键上速度均为 0（见 `breath_at`）。
BREATH_KEYS = ((0, 0.0), (48, 1.0), (66, 1.0), (120, 0.0))

# 贴地常数（米）：由 `CR.calibrate()` 重跑得出，不是硬编码
Z_OFF = {"L": 0.0, "R": 0.0}


# =============================================================== 呼吸曲线
def _smoothstep(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3.0 - 2.0 * u)


def breath_at(frame):
    """分段 smoothstep 呼吸包络。

    为什么不用 `TURN.track`：它只把**末段**切线置 0，首段用割线斜率。
    循环动画的 f0 与 f120 是同一个姿态（同一个呼吸极值点），两端速度都必须是 0，
    否则循环点会有一次速度跳变（末帧平着滑进来、首帧斜着冲出去）——
    这在连播里读作"呼吸卡了一下"，而 `loop_seamless` 是量不出来的（它只比姿态）。
    smoothstep 在每个键上速度天然为 0，包括 48→66 的"保持"段本身就恒定。
    """
    keys = BREATH_KEYS
    if frame <= keys[0][0]:
        return keys[0][1]
    if frame >= keys[-1][0]:
        return keys[-1][1]
    for index in range(len(keys) - 1):
        frame_a, value_a = keys[index]
        frame_b, value_b = keys[index + 1]
        if frame_a <= frame <= frame_b:
            span = float(frame_b - frame_a)
            if span <= 0.0:
                return value_b
            return value_a + (value_b - value_a) * _smoothstep(
                (frame - frame_a) / span)
    return keys[-1][1]


# =============================================================== 姿态生成
def crouch_idle_pose(arm, breath):
    """蹲姿基座 + 呼吸偏移。`breath=0` 时**逐位**等于 `Crouch@24`。"""
    chest = BASE_CHEST_RX - CHEST_AMP * breath
    pose = {
        "pelvis": (BASE_PELVIS_RX, 0.0, 0.0),
        "spine_01": (BASE_SPINE01_RX, 0.0, 0.0),
        "spine_02": (BASE_SPINE02_RX, 0.0, 0.0),
        "chest": (chest, 0.0, 0.0),
        "neck": (BASE_NECK_RX - NECK_AMP * breath, 0.0, 0.0),
        "head": (BASE_HEAD_RX + HEAD_AMP * breath, 0.0, 0.0),
        "shoulder.L": (BASE_SHOULDER_RX + SHOULDER_AMP * breath, 0.0, 0.0),
        "shoulder.R": (BASE_SHOULDER_RX + SHOULDER_AMP * breath, 0.0, 0.0),
        "toe.L": (0.0, 0.0, 0.0),
        "toe.R": (0.0, 0.0, 0.0),
        "@loc": {"pelvis": A.wloc(BASE_PELVIS_X, BASE_PELVIS_Y,
                                  BASE_PELVIS_Z + PELVIS_Z_AMP * breath - 0.900)},
    }
    A.apply_pose(arm, pose)

    # 腿：真双骨 IK（A06/A07 的 `leg_to`），踝目标 = A01@0 实测踝位 + 冻结贴地常数。
    # 骨盆 z 随呼吸升降 3 mm → 由 IK 吸收 ⟹ 踝的世界坐标纹丝不动
    # （这正是清单注意第二条怕的那件事：不用 IK 的话，骨盆动一点就被
    #  200 mm 长的大腿杠杆放大成脚部位移，直接吃掉 `feet_pinned_ok` 的余量）。
    for side in ("L", "R"):
        point = CR.ANKLE[side]
        TURN.leg_to(arm, pose, side,
                    (point.x, point.y, point.z + Z_OFF[side]), (0.0, -1.0))

    # 足：钉平到世界水平（与 A01/A08 同口径）。
    for side in ("L", "R"):
        pose["foot." + side] = A.keep_world_orientation(arm, "foot." + side)

    pose.update(A.FIST)

    # 臂：只跟着**胸链**转（骨盆与脊椎在本支是常量），参照零点减掉 A01 站姿
    # 自身的前倾 `LEAN0`（A08 踩坑 1：不减就会让 f0→f1 的手臂凭空弹 9°）。
    lean = (BASE_PELVIS_RX + BASE_SPINE01_RX + BASE_SPINE02_RX + chest)
    for bone in ARM_BONES:
        pose[bone] = A.aim_bone(arm, bone,
                                WF.swung(I1.ARM_DIRS[bone], lean - CR.LEAN0))
    return pose


# =============================================================== 专属门禁
def crouch_idle_assertions(arm, action, samples, crouch_mats):
    res = {}
    frames = [s["frame"] for s in samples]
    pelvis = [s["pelvis"] for s in samples]
    sternum = [s["neck"] for s in samples]

    # 0) 首帧必须**逐位**等于 `Crouch@24`（世界矩阵，不是 euler：
    #    `pose_bone.matrix` 的 setter 会解出等价但不同的 euler 三元组，A02 踩过）。
    mats = CR.action_world_matrices(arm, action, 0)
    delta = CR.matrix_delta(mats, crouch_mats)
    res["first_frame_delta"] = float("%.3e" % delta)
    res["first_frame_matches_crouch_ok"] = delta <= 1e-6

    # 1) 「身体不要上下漂浮过大」的可量化读数：骨盆 z 峰峰 ≤ 12 mm。
    #    标尺取在三者之间 —— A01 站姿呼吸只有 ~3 mm、Run 的 bob 是 59.5 mm，
    #    12 mm 卡在"沉稳呼吸"与"上下起伏"之间。
    zs = [p[2] for p in pelvis]
    bob = (max(zs) - min(zs)) * 1000.0
    res["pelvis_z_min_mm"] = round(min(zs) * 1000.0, 2)
    res["pelvis_z_max_mm"] = round(max(zs) * 1000.0, 2)
    res["pelvis_bob_mm"] = round(bob, 3)
    res["bob_amplitude_ok"] = bob <= 12.0

    # 1b) 呼吸看得见：胸骨顶（`neck` 的 head = chest.tail）3D 行程 5~18 mm。
    #     上限比 A01 的 7~30 **收紧**：蹲姿下胸腹被压缩，同样的角度摆幅读起来更大。
    travel = max((Vector(c) - Vector(sternum[0])).length for c in sternum) * 1000.0
    res["chest_breath_mm"] = round(travel, 2)
    res["breath_visible_ok"] = 5.0 <= travel <= 18.0

    # 1c) 肩部起伏（只报；清单 A09 没要求，但"呼吸"读感有一半在肩上）。
    shoulder = [s["upperarm.L"] for s in samples]
    rise = (max(p[2] for p in shoulder) - min(p[2] for p in shoulder)) * 1000.0
    res["shoulder_rise_mm"] = round(rise, 2)

    # 1d) 头部在**空间里的朝向**基本不动（A01 踩坑 2：竖骨要量横向参考轴，
    #     量"骨轴方向"会得到 ~0° 的假值）。
    def _unit(vector):
        length = math.sqrt(sum(v * v for v in vector)) or 1.0
        return tuple(v / length for v in vector)

    def _ang(a, b):
        return math.degrees(math.acos(max(-1.0, min(1.0,
                                                      sum(x * y for x, y in zip(a, b))))))

    axes = [_unit(tuple(t[i] - h[i] for i in range(3)))
            for t, h in zip([s["head.tail"] for s in samples],
                            [s["head"] for s in samples])]
    res["head_orientation_deg"] = round(max(_ang(a, axes[0]) for a in axes), 3)

    # 2) **脚不移位**（骨架世界坐标，口径同 A01/A06/A07/A08）。
    travel_feet = {}
    for side in ("L", "R"):
        points = [Vector(s["foot." + side]) for s in samples]
        travel_feet[side] = max((p - points[0]).length for p in points) * 1000.0
    res["feet_pinned_mm"] = {k: round(v, 3) for k, v in travel_feet.items()}
    res["feet_pinned_ok"] = all(v <= 3.0 for v in travel_feet.values())

    # 2b) 骨盆倾角恒定（清单注意第二条：呼吸只归胸腔）。
    tilts = [s["euler"].get("pelvis", (0.0, 0.0, 0.0))[0] for s in samples]
    res["pelvis_rx_range_deg"] = round(max(tilts) - min(tilts), 4)
    res["pelvis_tilt_steady_ok"] = (max(tilts) - min(tilts)) <= 0.01

    # 2c) 「腿没被呼吸带着动」——**不能要求膝弯角恒定**。
    #
    # 第一版把这条写成"膝弯角逐帧变化 ≤0.15°"，实测 0.56° 直接红。但那不是缺陷：
    # 骨盆随吸气抬 3 mm ⟹ 髋-踝距离 q 也涨 3 mm ⟹ 90° 屈膝的膝角必然变化。
    # 解析预估 dθ ≈ dq · q / (L_thigh·L_shin·sin(interior)) = 3 × 585/(410×412×1)
    #   = 0.0104 rad = **0.60°**，实测 0.56° —— 逐位是同一件事。
    # 拿"恒定"当判据等于要求"骨盆移动时膝不许动"，是一条**不可满足的判据**
    # （同族问题见 A06 踩坑 5：尺子选错会恒红）。
    # → 改判**可解释性**：① 变化幅度落在"骨盆升降能解释的范围"里（≤1.5°，
    #   是解析值的 2.5 倍余量）；② 变化**方向**必须与骨盆升降反向 ——
    #   骨盆最高处膝最直。若哪天有人往腿上偷偷加了关键帧，②必红。
    bend = CR.knee_series(arm, action, frames)
    zs_all = [p[2] for p in pelvis]
    index_high, index_low = zs_all.index(max(zs_all)), zs_all.index(min(zs_all))
    knee_range = {}
    knee_inverse = {}
    for side in ("L", "R"):
        values = [b[side] for b in bend]
        knee_range[side] = round(max(values) - min(values), 3)
        knee_inverse[side] = bool(values[index_high] < values[index_low])
        res["knee_bend_%s_deg" % side] = [round(min(values), 2),
                                          round(max(values), 2)]
    res["knee_bend_range_deg"] = knee_range
    res["knee_bend_at_pelvis_peak_is_straighter"] = knee_inverse
    res["knee_steady_ok"] = (all(v <= 1.5 for v in knee_range.values())
                             and all(knee_inverse.values()))

    # 3) **护体架势不能抖散**：拳 → 胸骨顶距离全程漂移 ≤45 mm（A08 同一把尺子）。
    fist_rel = []
    for s in samples:
        point = Vector(s["neck"])
        fist_rel.append(max((Vector(s["hand.L.tail"]) - point).length,
                            (Vector(s["hand.R.tail"]) - point).length))
    res["fist_sternum_start_mm"] = round(fist_rel[0] * 1000.0, 2)
    res["fist_sternum_drift_mm"] = round(
        (max(fist_rel) - min(fist_rel)) * 1000.0, 2)
    res["guard_kept_ok"] = (max(fist_rel) - min(fist_rel)) * 1000.0 <= 45.0
    res["guard_height_mm"] = round(float(samples[0]["hand.L.tail"][2])
                                   * 1000.0, 1)

    # 4) 原地（清单 §0.4）：骨盆水平行程有界。本支理论上应为 0（腿被钉死）。
    hspan = max(math.hypot(p[0] - pelvis[0][0], p[1] - pelvis[0][1])
                for p in pelvis) * 1000.0
    res["pelvis_horizontal_span_mm"] = round(hspan, 3)
    res["pelvis_in_place_ok"] = hspan <= 5.0

    # 5) 站姿与 A08 末帧一致（供 A10 `Jump_Start` 起手）。
    last = samples[-1]
    lx, ly = last["foot.L"][0], last["foot.L"][1]
    rx, ry = last["foot.R"][0], last["foot.R"][1]
    res["stance_last_mm"] = {"L": [round(lx * 1000.0, 1), round(ly * 1000.0, 1)],
                             "R": [round(rx * 1000.0, 1), round(ry * 1000.0, 1)]}
    res["stance_x_mm"] = round((lx - rx) * 1000.0, 1)
    res["stance_diag_mm"] = round(math.hypot(lx - rx, ly - ry) * 1000.0, 1)

    # 6) 呼吸曲线本身：逐帧增量必须小而单调（"不要漂浮"的另一种读法）。
    breaths = [breath_at(f) for f in frames]
    steps = [abs(breaths[i + 1] - breaths[i]) for i in range(len(breaths) - 1)]
    res["breath_peak_step"] = round(max(steps), 5)
    res["breath_smooth_ok"] = max(steps) <= 0.05
    res["chest_amp_deg"] = CHEST_AMP
    res["z_off_mm"] = {k: round(v * 1000.0, 3) for k, v in Z_OFF.items()}
    return res


# =============================================================== 主流程
def main():
    global Z_OFF

    arm, meshes = A.open_animation_project()
    A.setup_scene()

    if "Idle_01" not in bpy.data.actions:
        print("CI_BOOTSTRAP 动画工程缺 Idle_01，先补跑 A01")
        I1.main()
        arm, meshes = A.open_animation_project()
        A.setup_scene()
    if "Crouch" not in bpy.data.actions:
        print("CI_BOOTSTRAP 动画工程缺 Crouch，先补跑 A08")
        CR.main()
        arm, meshes = A.open_animation_project()
        A.setup_scene()

    # ---- 踝参考位 + 贴地常数：**重跑 A08 的标定**（清单注意第二条的硬要求）
    I1.idle_pose(arm, 0.0)
    CR.ANKLE = {side: Vector(A.bone_world(arm, "foot." + side, "head"))
                for side in ("L", "R")}
    Z_OFF, lows = CR.calibrate(arm)
    A.report("CI_CALIBRATION", {
        "ankle_mm": {side: [round(v * 1000.0, 2) for v in CR.ANKLE[side]]
                     for side in CR.ANKLE},
        "z_off_mm": {k: round(v * 1000.0, 3) for k, v in Z_OFF.items()},
        # A08 的标定区间是 1~24 帧（覆盖末帧蹲姿），这里把 raw 区间复报一遍，
        # 证明"沿用这组常数"在蹲姿区间里的鞋底范围仍在门禁窗口 [−2, +6] 内。
        "a08_raw_sole_range_mm": {
            k: [round(min(lows[k]) * 1000.0, 2), round(max(lows[k]) * 1000.0, 2)]
            for k in ("L", "R")},
    })

    keyframes = [(frame, crouch_idle_pose(arm, breath_at(frame)))
                 for frame in range(0, TOTAL + 1)]

    meta = {
        "anim_id": NAME,
        "loop": True,
        "category": "基础移动",
        "note": ("蹲姿呼吸循环：首帧逐位接 Crouch@24；呼吸只归胸腔与肩，"
                 "骨盆倾角恒定、踝世界坐标钉死；吸 0.8 s / 停 0.3 s / 呼 0.9 s"),
        "antic_frame": None,
        "hit_frame": None,
        "cancel_frame": None,
        "hitstop_frames": 0,
        "root_motion_m": [0.0, 0.0],
        "inherit_from": "Crouch@24",
        "breath_chest_deg": CHEST_AMP,
        "breath_shoulder_deg": SHOULDER_AMP,
        "breath_pelvis_z_mm": round(PELVIS_Z_AMP * 1000.0, 2),
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.add_markers(action, {"LOOP_START": 0, "INHALE_PEAK": 48,
                           "HOLD_END": 66, "LOOP_END": TOTAL})

    samples = A.sample_animation(arm, action, 0, TOTAL, meshes)
    # foot_probe 置空：通用门禁的"脚位移 ≤3 mm"默认量 toe 骨，本支由专属
    # `feet_pinned_ok` 按**踝**判（口径与 A01/A06/A07/A08 一致）。
    report = A.run_common_assertions(samples, meta, foot_probe=())

    crouch_mats = CR.action_world_matrices(arm, bpy.data.actions["Crouch"],
                                           CR.TOTAL)
    report.update(crouch_idle_assertions(arm, action, samples, crouch_mats))
    report["meta"] = meta
    failed = sorted(k for k, v in report.items()
                    if k.endswith("_ok") and v is not True)
    report["failed"] = failed
    A.report("CROUCHIDLE_REPORT", report)

    # 每帧的呼吸值 / 骨盆 z / 胸骨顶 z：贴在日志里做人工复核用。
    A.report("CI_TRACE", {
        "frames": [f for f in range(0, TOTAL + 1, 12)],
        "breath": [round(breath_at(f), 4) for f in range(0, TOTAL + 1, 12)],
    })

    if not SKIP_RENDER:
        A.render_pose_sheet(arm, action, [0, 24, 48, 66, 93], "crouchidle",
                            views=(A.VIEW_SIDE,))
        A.render_pose_sheet(arm, action, [0, 48, 66], "crouchidle",
                            views=(A.VIEW_FRONT,))
        A.render_pose_sheet(arm, action, [0, 48], "crouchidle",
                            views=(A.VIEW_3Q,))
    A.save_project()
    A.export_glb(arm)
    print("CROUCHIDLE_DONE failed=%s" % failed)


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("CROUCHIDLE_FAILURE " + traceback.format_exc())
