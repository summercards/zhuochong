"""probe_light01b —— B01 第二支探针：腿的解算器一致性 + 出拳通道预算。

要回答两个问题（都直接决定写法）：

  ① **`TURN.leg_to`（3D 瞄准式 IK）能不能在"站姿参数"下复现 `Idle_01@0` 的腿？**
     B01 的首末帧必须**逐位** = `Idle_01@0`。若两者世界矩阵差 >1e-6，就不能让
     `build_pose` 去生成首末帧，只能把那两帧替换成成品姿态 —— 而替换点会不会
     制造 `decel_smooth_ok` 的台阶，取决于这个差有多大。**先量，再决定。**

  ② **`forearm.L` 的 rz 通道要扫多少度？**（= `no_teleport ≤25°/帧` 的预算来源）
     已知 guard rz = −137.845、S1 strike rz = −6.25 ⟹ 差 131.6°。这里核对
     候选 strike 的逐分量差，并算「6 帧 / 11 帧摊完」各自需要的单帧峰值。

用法：
    blender --background --factory-startup --python probe_light01b.py
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
import anim_turn as TURN      # noqa: E402
import anim_crouch as CR      # noqa: E402

LEG6 = ("thigh.L", "shin.L", "foot.L", "thigh.R", "shin.R", "foot.R")
ARM6 = ("upperarm.L", "forearm.L", "hand.L",
        "upperarm.R", "forearm.R", "hand.R")


def euler_of(arm, names):
    return {n: tuple(math.degrees(v) for v in arm.pose.bones[n].rotation_euler)
            for n in names}


def main():
    arm, _meshes = A.open_animation_project()
    A.setup_scene()
    if "Idle_01" not in bpy.data.actions:
        I1.main()
        arm, _meshes = A.open_animation_project()
        A.setup_scene()

    # ---------- ① `Idle_01@0` 的腿 ─----------
    A.PREV = None
    JS._PREV_EULER.clear()
    for name in list(arm.pose.bones.keys()):
        JS._PREV_EULER[name] = (0.0, 0.0, 0.0)
    idle_pose = I1.idle_pose(arm, 0.0)
    idle_leg = euler_of(arm, LEG6)
    ankle = {s: Vector(A.bone_world(arm, "foot." + s, "head")) for s in ("L", "R")}
    idle_mats = {b.name: [v for row in b.matrix for v in row]
                 for b in arm.pose.bones}

    # ---------- ② 用 leg_to 复现同一目标 ----------
    variants = {}
    for tag, fw in (("forward_-Y", (0.0, -1.0)),
                    ("abduct_matched",
                     (0.075 if True else 0.0, -0.997))):
        # abduct 匹配版：左右各按自身外展方向给膝鼓出方向
        variants[tag] = fw

    rows = {}
    for tag, fw in variants.items():
        # 重置到 idle 的躯干 + 骨盆（腿由 IK 解）
        base = {k: v for k, v in idle_pose.items()
                if k in ("pelvis", "spine_01", "spine_02", "chest", "neck",
                         "head", "shoulder.L", "shoulder.R")}
        base["@loc"] = idle_pose.get("@loc", {})
        base.update(A.FIST)
        A.apply_pose(arm, base)
        pose = dict(base)
        for side in ("L", "R"):
            f = (fw[0] * (1.0 if side == "L" else -1.0), fw[1])
            TURN.leg_to(arm, pose, side, ankle[side], f)
        for name in LEG6:
            raw = tuple(math.degrees(v)
                        for v in arm.pose.bones[name].rotation_euler)
            pose[name] = JS._unwrap_xyz(idle_leg[name], raw)
            arm.pose.bones[name].rotation_euler = [math.radians(v)
                                                   for v in pose[name]]
        bpy.context.view_layer.update()
        for side in ("L", "R"):
            A.keep_world_orientation(arm, "foot." + side)
        bpy.context.view_layer.update()
        got = euler_of(arm, LEG6)
        ew = {}
        for n in LEG6:
            ew[n] = max(abs(got[n][i] - idle_leg[n][i]) for i in range(3))
        mats = {b.name: [v for row in b.matrix for v in row]
                for b in arm.pose.bones}
        md = max(max(abs(x - y) for x, y in zip(mats[n], idle_mats[n]))
                 for n in mats)
        ank = {s: Vector(A.bone_world(arm, "foot." + s, "head"))
               for s in ("L", "R")}
        rows[tag] = {
            "euler_delta_deg": {k: round(v, 4) for k, v in ew.items()},
            "max_euler_delta_deg": round(max(ew.values()), 4),
            "matrix_max_delta": float("%.3e" % md),
            "ankle_err_mm": {s: round((ank[s] - ankle[s]).length * 1000.0, 3)
                             for s in ank},
        }
    A.report("LIGHT01B_LEG_SOLVER", {
        "idle_leg_euler_deg": {k: [round(x, 3) for x in v]
                               for k, v in idle_leg.items()},
        "idle_ankle_mm": {s: [round(v * 1000.0, 1) for v in ankle[s]]
                          for s in ankle},
        "variants": rows,
        "verdict_hint": ("max_euler_delta 若 >2~3°，首末帧就必须替换成成品姿态，"
                         "并检查替换点是否制造 decel 台阶"),
    })

    # ---------- ③ 通道预算 ----------
    I1.idle_pose(arm, 0.0)
    E_GUARD = euler_of(arm, ARM6)
    strike_e = {
        "upperarm.L": (6.46, 3.91, -62.28),
        "forearm.L": (11.7, 0.64, -6.25),
        "hand.L": (0.6, 0.01, -1.71),
        "upperarm.R": (-54.25, 15.53, 29.82),
        "forearm.R": (-1.37, 5.98, 154.26),
        "hand.R": (9.34, 2.2, -26.48),
    }
    delta = {b: [round(strike_e[b][i] - E_GUARD[b][i], 2) for i in range(3)]
             for b in ARM6}
    worst = max(max(abs(x) for x in delta[b]) for b in ARM6)
    # 峰值行为：s = u^p 的最后一格增量 = 1 − (1−1/N)^p
    rows2 = {}
    for span in (6, 11):
        for p in (1.0, 1.01, 1.02, 1.05, 1.1):
            last = (1.0 - (1.0 - 1.0 / span) ** p) * 100.0
            rows2["span%d_p%.2f" % (span, p)] = round(worst * last / 100.0, 2)
    # 收招：s = 2u − u²（速度线性衰减到 0）的首格增量
    rec = {}
    for span in (11,):
        first = (2.0 / span - 1.0 / (span * span)) * 100.0
        rec["span%d_first_step_deg" % span] = round(worst * first / 100.0, 2)
    A.report("LIGHT01B_CHANNEL_BUDGET", {
        "guard_arm_euler_deg": {k: [round(x, 3) for x in v]
                                for k, v in E_GUARD.items()},
        "strike_arm_euler_deg": {k: [round(x, 2) for x in v]
                                 for k, v in strike_e.items()},
        "delta_deg": delta,
        "worst_component_delta_deg": round(worst, 2),
        "outbound_peak_step_deg_by_profile": rows2,
        "recover_profile_2u_minus_u2": rec,
        "limit_deg": 25.0,
    })


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("PROBE_LIGHT01B_FAILURE " + traceback.format_exc())
