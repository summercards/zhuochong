"""probe_light03 —— B03 `Light_03`（重摆拳 / 勾拳·连击终结）**只读**探针。

清单「下一支计划 —— B03」的 ★ 三件事全部在这里落地，**不许照抄 B02 的符号**：

  1. **出拳手身份重测**：读 `Idle_01@0` 的踝世界坐标，判前后脚 ⟹ 前手/后手。
     L / R 两侧的候选命中姿态**都**算一遍（不预设结论）。
  2. **`|Y|` 提前体检**：大摆拳把上臂大幅过中线，欧拉 `|Y|` 显著大于 B02 的 17.1°；
     这里**两支等价族都算**（`(x,y,z)` 与 `(x+180,180−y,z+180)`），取离 guard 近的那支，
     并把两支的代价都报出来 —— 「换族」到底救不救得回来，用数字说话。
  3. **预算先算死**：`峰值 = span×(1−(1−1/n)^p) ≤ 25`，span 大就**加帧**。
     本支 26 帧、HIT=10、HOLD=3（冻结 4 帧）⟹ 伸出段 n = 10 帧。

★ 修正记录（第一版探针的错）：第一版把躯干轨写死成「左肩前送」，
  对 R 拳候选是错的 —— 守手侧的 euler 被反向拧到 `|Y| = 55°`，
  读数全是污染。现改为**按出拳侧镜像**（`sgn = +1/-1`）的躯干轨。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python probe_light03.py
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

HIT = 10
HOLD = 3
TOTAL = 26
CLOCK_END = TOTAL - HOLD          # 23
ARM_POW = 1.25
REC_POW = 1.45

B02_REACH_MM = 595.8
B02_LATERAL_MM = 361.2
B02_TRAVEL_MM = 588.3
B02_SWEEP_DEG = 108.08
B02_MAX_Y_DEG = 17.1

ARM6 = ("upperarm.L", "forearm.L", "hand.L",
        "upperarm.R", "forearm.R", "hand.R")
TRUNK6 = ("pelvis", "spine_01", "spine_02", "chest", "neck", "head")

PELVIS_Y = ((0, 0.000), (3.0, 0.008), (HIT, -0.036), (CLOCK_END, 0.0))
PELVIS_X = ((0, 0.000), (4.0, 0.010), (HIT, -0.016), (CLOCK_END, 0.0))
PELVIS_DZ = ((0, 0.0), (3.0, 0.004), (HIT, -0.008), (CLOCK_END, 0.0))
DROP = I1.DROP


def trunk_tracks(punch):
    """按出拳侧镜像的躯干轨（关键帧横坐标 0/4/HIT/CLOCK_END 对齐 ⟹ 髋肩峰值同帧）。

    `sgn = +1`（R 拳）／`−1`（L 拳）。
    右臂 `rz>0` = 向前，左臂 `rz>0` = 向后 —— 两支的 rz 符号**必须反**。
    `ry>0` 把 +X（左）侧转向身后 ⟹ **右肩向前**；L 拳要左肩向前，故 ry 也要反号。
    """
    sgn = 1.0 if punch == "R" else -1.0
    guard = "L" if punch == "R" else "R"
    out = {
        "pelvis": {"rx": ((0, 4.0), (4, 5.4), (HIT, 6.5), (CLOCK_END, 4.0)),
                   "ry": ((0, 0.0), (4.0, -9.0 * sgn), (HIT, 14.0 * sgn),
                          (CLOCK_END, 0.0))},
        "spine_01": {"rx": ((0, 2.0), (4, 2.7), (HIT, 3.2), (CLOCK_END, 2.0)),
                     "ry": ((0, 0.0), (4.0, -4.0 * sgn), (HIT, 7.0 * sgn),
                            (CLOCK_END, 0.0))},
        "spine_02": {"rx": ((0, 2.0), (4, 2.7), (HIT, 3.2), (CLOCK_END, 2.0)),
                     "ry": ((0, 0.0), (4.0, -4.0 * sgn), (HIT, 7.0 * sgn),
                            (CLOCK_END, 0.0))},
        "chest": {"rx": ((0, 1.0), (4, 1.8), (HIT, 3.2), (CLOCK_END, 1.0)),
                  "ry": ((0, 0.0), (4.0, -9.0 * sgn), (HIT, 14.0 * sgn),
                         (CLOCK_END, 0.0))},
        "neck": {"rx": ((0, -6.0), (4, -7.0), (HIT, -10.0), (CLOCK_END, -6.0)),
                 "ry": ((0, 0.0), (4.0, 4.5 * sgn), (HIT, -12.0 * sgn),
                        (CLOCK_END, 0.0))},
        "head": {"rx": ((0, 5.0), (4, 5.3), (HIT, 4.0), (CLOCK_END, 5.0)),
                 "ry": ((0, 0.0), (4.0, 3.0 * sgn), (HIT, -9.0 * sgn),
                        (CLOCK_END, 0.0))},
    }
    out["shoulder." + punch] = {
        "rx": ((0, -18.0), (4, -14.0), (HIT, -5.0), (CLOCK_END, -18.0)),
        "rz": ((0, 0.0), (4.0, -12.0 * sgn), (HIT, 19.0 * sgn), (CLOCK_END, 0.0))}
    out["shoulder." + guard] = {
        "rx": ((0, -18.0), (4, -19.0), (HIT, -20.0), (CLOCK_END, -18.0)),
        "rz": ((0, 0.0), (4.0, -5.0 * sgn), (HIT, 7.0 * sgn), (CLOCK_END, 0.0))}
    return out


COIL = {
    "L": {"upperarm.L": {"rz": ((0, 0.0), (1.5, 11.0), (3.0, 13.0),
                                (5.5, 4.5), (HIT, 0.0), (CLOCK_END, 0.0))}},
    "R": {"upperarm.R": {"rz": ((0, 0.0), (1.5, -11.0), (3.0, -13.0),
                                (5.5, -4.5), (HIT, 0.0), (CLOCK_END, 0.0))}},
}

GUARD_SIDE_DIRS = {
    "upperarm.L": (0.26, -0.30, -0.92),
    "forearm.L": (-0.32, -0.40, 0.86),
    "hand.L": (-0.20, -0.70, 0.68),
    "upperarm.R": (-0.22, -0.36, -0.90),
    "forearm.R": (0.34, -0.20, 0.92),
    "hand.R": (0.18, -0.60, 0.78),
}

CANDIDATES = {}


def _mirror(dirs, side):
    """把一组「出拳侧」方向按镜像规则补全成 6 骨方向。

    镜像：`x → −x`（左右互换即 +X ↔ −X）；出拳侧与守手侧各取一支。
    """
    out = {}
    for bone, d in dirs.items():
        out[bone] = d
    return out


# ---- 左拳（前手，1-2-3 的第三拳）------------------------------
CANDIDATES["L_mirror_b02"] = {
    "upperarm.L": (-0.35, -0.90, -0.25),
    "forearm.L": (-0.70, -0.70, 0.10),
    "hand.L": (-0.80, -0.58, 0.10),
}
CANDIDATES["L_wide_long"] = {
    "upperarm.L": (-0.28, -0.93, -0.22),
    "forearm.L": (-0.52, -0.84, -0.05),
    "hand.L": (-0.62, -0.78, -0.02),
}
CANDIDATES["L_high_overhand"] = {
    "upperarm.L": (-0.30, -0.90, 0.05),
    "forearm.L": (-0.45, -0.88, -0.02),
    "hand.L": (-0.58, -0.80, -0.05),
}
CANDIDATES["L_hook_deep"] = {
    "upperarm.L": (-0.55, -0.75, -0.35),
    "forearm.L": (-0.85, -0.50, 0.05),
    "hand.L": (-0.90, -0.40, 0.02),
}
CANDIDATES["L_hook_high_wrap"] = {
    "upperarm.L": (-0.62, -0.62, 0.48),
    "forearm.L": (-0.88, -0.42, -0.20),
    "hand.L": (-0.92, -0.36, -0.12),
}
# ---- 精调：在「reach > 595.8（轻击退门禁）」的前提下把**横向**顶到最大 ----------
CANDIDATES["L_hook_v2"] = {
    "upperarm.L": (-0.44, -0.84, -0.30),
    "forearm.L": (-0.82, -0.55, 0.06),
    "hand.L": (-0.88, -0.45, 0.05),
}
CANDIDATES["L_hook_v3"] = {
    "upperarm.L": (-0.35, -0.88, -0.32),
    "forearm.L": (-0.72, -0.68, 0.02),
    "hand.L": (-0.82, -0.56, 0.02),
}
CANDIDATES["L_hook_v4"] = {
    "upperarm.L": (-0.30, -0.92, -0.24),
    "forearm.L": (-0.68, -0.72, 0.06),
    "hand.L": (-0.78, -0.60, 0.06),
}
# ---- 右拳（后手）------------------------------------------------
CANDIDATES["R_like_b02"] = {
    "upperarm.R": (0.35, -0.90, -0.25),
    "forearm.R": (0.70, -0.70, 0.10),
    "hand.R": (0.80, -0.58, 0.10),
}
CANDIDATES["R_wide_long"] = {
    "upperarm.R": (0.28, -0.93, -0.22),
    "forearm.R": (0.52, -0.84, -0.05),
    "hand.R": (0.62, -0.78, -0.02),
}

CHANNEL_INDEX = {"rx": 0, "ry": 1, "rz": 2}


def tval(track, c):
    return TURN.track(track, c) if track else 0.0


def trunk_pose(tracks, c):
    return {bone: (tval(t.get("rx"), c), tval(t.get("ry"), c), tval(t.get("rz"), c))
            for bone, t in tracks.items()}


def arm_s(c):
    if c <= 0.0:
        return 0.0
    if c < HIT:
        return (c / float(HIT)) ** ARM_POW
    if c >= CLOCK_END:
        return 0.0
    u = (c - HIT) / float(CLOCK_END - HIT)
    return (1.0 - u) ** REC_POW


def main():
    arm, _meshes = A.open_animation_project()
    A.setup_scene()

    idle_pose = I1.idle_pose(arm, 0.0)
    A.apply_pose(arm, idle_pose)
    ankle = {s: Vector(A.bone_world(arm, "foot." + s, "head")) for s in ("L", "R")}
    guard_e = {b: tuple(math.degrees(v)
                        for v in arm.pose.bones[b].rotation_euler) for b in ARM6}
    sternum0 = Vector(A.bone_world(arm, "neck", "head"))
    fist0 = {s: Vector(A.bone_world(arm, "hand." + s, "tail")) for s in ("L", "R")}

    front = "L" if ankle["L"].y < ankle["R"].y else "R"
    A.report("LIGHT03_IDENTITY", {
        "ankle_world_mm": {s: [round(v * 1000.0, 1) for v in ankle[s]]
                           for s in ("L", "R")},
        "front_foot": front,
        "back_foot": "R" if front == "L" else "L",
        "guard_fist_mm": {s: [round(v * 1000.0, 1) for v in fist0[s]]
                          for s in ("L", "R")},
        "sternum_mm": [round(v * 1000.0, 1) for v in sternum0],
        "guard_reach_mm": {s: round((sternum0.y - fist0[s].y) * 1000.0, 1)
                           for s in ("L", "R")},
        "guard_lateral_mm": {s: round((fist0[s].x - sternum0.x) * 1000.0, 1)
                             for s in ("L", "R")},
        "guard_arm_euler_deg": {k: [round(x, 3) for x in v]
                                for k, v in guard_e.items()},
    })

    rows = []
    for name, dirs in CANDIDATES.items():
        side = name[0]
        tracks = trunk_tracks(side)
        full = {}
        for bone in ARM6:
            full[bone] = dirs[bone] if bone.endswith("." + side) \
                else GUARD_SIDE_DIRS[bone]

        strike_trunk = trunk_pose(tracks, HIT)
        strike_trunk.update(A.FIST)
        A.apply_pose(arm, strike_trunk)
        raw = {b: A.aim_bone(arm, b, full[b]) for b in ARM6}
        estrike = {b: JS._unwrap_xyz(guard_e[b], raw[b]) for b in ARM6}
        # 两支等价族都报（"换族救不救得回来"）
        fam = {}
        for b in ARM6:
            base = tuple(raw[b])
            flip = (base[0] + 180.0, 180.0 - base[1], base[2] + 180.0)
            cost0 = max(abs(base[i] - guard_e[b][i]) for i in range(3))
            cost1 = max(abs(flip[i] - guard_e[b][i]) for i in range(3))
            fam[b] = {"y_base": round(base[1], 2), "y_flip": round(flip[1], 2),
                      "cost_base": round(cost0, 2), "cost_flip": round(cost1, 2),
                      "cost_min": round(min(cost0, cost1), 2)}
        max_y = max(abs(estrike[b][1]) for b in ARM6)
        worst = max(max(abs(estrike[b][i] - guard_e[b][i]) for i in range(3))
                    for b in ARM6)
        worstbone = max(ARM6, key=lambda b: max(abs(estrike[b][i] - guard_e[b][i])
                                               for i in range(3)))
        pred_out = worst * (1.0 - (1.0 - 1.0 / HIT) ** ARM_POW)
        pred_rec = worst * (1.0 - (1.0 - 1.0 / (CLOCK_END - HIT)) ** REC_POW)

        # ---- 迷你仿真（clock 0..HIT）
        coil = COIL[side]
        fist_path, sh_path, eu_path = [], [], []
        for c in range(0, HIT + 1):
            s = arm_s(float(c))
            pose = trunk_pose(tracks, c)
            pose["@loc"] = {"pelvis": A.wloc(tval(PELVIS_X, c), tval(PELVIS_Y, c),
                                             DROP + tval(PELVIS_DZ, c))}
            eul = {}
            for b in ARM6:
                vals = [guard_e[b][i] + (estrike[b][i] - guard_e[b][i]) * s
                        for i in range(3)]
                for ch, tr in coil.get(b, {}).items():
                    vals[CHANNEL_INDEX[ch]] += tval(tr, c)
                eul[b] = tuple(vals)
                pose[b] = eul[b]
            pose.update(A.FIST)
            A.apply_pose(arm, pose)
            fist_path.append(Vector(A.bone_world(arm, "hand." + side, "tail")))
            sh_path.append(Vector(A.bone_world(arm, "upperarm." + side, "head")))
            eu_path.append((c, eul, {b: pose[b] for b in TRUNK6
                                     if b in pose}))
        # 实际逐帧最大欧拉步（no_teleport 代理，含躯干）
        max_step, step_at = 0.0, None
        for i in range(1, len(eu_path)):
            for b in ARM6:
                a = eu_path[i - 1][1][b]
                d = eu_path[i][1][b]
                st = max(abs(a[k] - d[k]) for k in range(3))
                if st > max_step:
                    max_step, step_at = st, (eu_path[i][0], b)
        fist_hit = fist_path[HIT]
        s = arm_s(float(HIT))
        pose = trunk_pose(tracks, HIT)
        pose["@loc"] = {"pelvis": A.wloc(tval(PELVIS_X, HIT), tval(PELVIS_Y, HIT),
                                         DROP + tval(PELVIS_DZ, HIT))}
        for b in ARM6:
            pose[b] = tuple(guard_e[b][i] + (estrike[b][i] - guard_e[b][i]) * s
                            for i in range(3))
        pose.update(A.FIST)
        A.apply_pose(arm, pose)
        sternum_hit = Vector(A.bone_world(arm, "neck", "head"))
        fist_guard_world = Vector(A.bone_world(arm, "hand." + side, "tail"))

        reach = (sternum_hit.y - fist_hit.y) * 1000.0
        lat0 = (fist_path[0].x - sternum0.x) * 1000.0
        lat_hit = (fist_hit.x - sternum_hit.x) * 1000.0
        lateral = abs(lat_hit - lat0)
        travel = max((f - fist_path[0]).length for f in fist_path) * 1000.0
        total, prev = 0.0, None
        for i in range(len(fist_path)):
            d = fist_path[i] - sh_path[i]
            if d.length < 1e-9:
                continue
            d = d.normalized()
            if prev is not None:
                total += math.degrees(prev.angle(d))
            prev = d

        rows.append({
            "cand": name, "hand": side,
            "reach_mm": round(reach, 1), "lateral_mm": round(lateral, 1),
            "travel_mm": round(travel, 1), "sweep_deg": round(total, 2),
            "max_abs_y_deg": round(max_y, 2),
            "worst_delta_deg": round(worst, 2), "worst_bone": worstbone,
            "actual_max_step_deg": round(max_step, 2), "step_at": step_at,
            "pred_peak_step": round(pred_out, 2),
            "pred_rec_first": round(pred_rec, 2),
            "pred_peak_wins": bool(pred_out > pred_rec),
            "beat_reach": bool(reach > B02_REACH_MM),
            "beat_lateral": bool(lateral > B02_LATERAL_MM),
            "beat_travel": bool(travel > B02_TRAVEL_MM),
            "beat_sweep": bool(total > B02_SWEEP_DEG),
            "y_ok_lt45": bool(max_y < 45.0),
            "fist_hit_mm": [round(v * 1000.0, 1) for v in fist_hit],
            "family_cost": fam,
            "euler": {b: [round(x, 2) for x in estrike[b]] for b in ARM6},
        })

    rows.sort(key=lambda r: -(r["beat_travel"] + r["beat_sweep"]))
    A.report("LIGHT03_CANDIDATES", rows)
    A.report("LIGHT03_BASELINE", {
        "b02": {"reach": B02_REACH_MM, "lateral": B02_LATERAL_MM,
                "travel": B02_TRAVEL_MM, "sweep": B02_SWEEP_DEG,
                "max_y": B02_MAX_Y_DEG},
        "span_limit_for_25deg": round(25.0 / (1.0 - (1.0 - 1.0 / HIT)
                                              ** ARM_POW), 1),
    })
    print("PROBE_LIGHT03_DONE candidates=%d" % len(rows))


if __name__ == "__main__":
    main()
