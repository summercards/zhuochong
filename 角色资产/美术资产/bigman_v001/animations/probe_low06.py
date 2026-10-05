"""probe_low06 —— B06 `Low_Attack` 下段攻击 **只读** 探针（定盘数）。

清单「下一支详细制作计划 —— B06」的 ★ 三件事在这里落地（**先量再做**）：
  1. **命中点高度**：以「骨盆世界 z」为腰线基准，量 `hit_foot_z_mm ≤ pelvis_z_mm − 250`
     在多大范围里可解（髋→踝距离 ≤ 腿长 0.822 m）。
  2. **支撑腿 IK 余量**：单腿支撑 + 骨盆前移/侧移时 `leg_reach_headroom_mm` 还剩多少
     （B04/B05 在 42~57 mm）。**余量 < 20 mm 就要缩骨盆位移**。
  3. **攻击腿的 pole**：抬腿到侧前方时髋→膝轴接近水平，pole 可能退化。
     量 `|pole⊥axis|`，低于 0.30 就走 `_elbow_bulge` 的**同款接力**（`leg_to` 版），
     **不许硬阈值**。

另外量清楚：idle 的踝/膝/髋/肩实测位、腿长、攻击脚骨的世界 rest 朝向、大腿中点高度
（`low_height_ok` 的"大腿中部"基准）。

本探针**只读**：只摆姿态、只测量，不建 Action、不存盘、不导 GLB。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python probe_low06.py
"""

import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A          # noqa: E402
import anim_idle_01 as I1     # noqa: E402

SIDES = ("L", "R")
SUPPORT = "R"                 # 支撑腿 = 后脚 R（y = +0.140，站得更稳、离髋更近）
ATTACK = "L"                  # 攻击腿 = 前脚 L

LEG_LIMIT = A.L_THIGH + A.L_SHIN          # 0.822 m


def mm(v):
    return [round(float(x) * 1000.0, 1) for x in v]


def _bone_len(arm, name):
    return (Vector(A.bone_world(arm, name, "tail"))
            - Vector(A.bone_world(arm, name, "head"))).length


def _leg_geom(hip, target, pole):
    """纯几何预报：|髋→踝| 的伸展率 / 膝内角 / `|pole⊥axis|` / 是否可达。

    `pole` = 膝的鼓出方向（世界向量）。`|pole⊥axis|` 是**决策量**：
    轴与 pole 近乎共线时鼓出方向由噪声决定 ⟹ 膝会单帧甩几十度。
    """
    hip = Vector(hip)
    delta = Vector(target) - hip
    raw = delta.length
    limit = LEG_LIMIT * 0.9995
    axis = delta.normalized() if raw > 1e-9 else Vector((0.0, -1.0, 0.0))
    distance = max(1e-4, min(raw, limit))
    cos_hip = ((A.L_THIGH ** 2 + distance ** 2 - A.L_SHIN ** 2)
               / (2.0 * A.L_THIGH * distance))
    cos_hip = max(-1.0, min(1.0, cos_hip))
    inner = math.degrees(math.acos(cos_hip))          # 髋内角（0 = 完全回折）
    knee_bend = 180.0 - inner                          # 屈膝量（0 = 完全伸直）
    pole_v = Vector(pole).normalized()
    bulge = pole_v - axis * pole_v.dot(axis)
    return {"reach_mm": round(raw * 1000.0, 1),
            "extension": round(raw / LEG_LIMIT, 4),
            "headroom_mm": round((LEG_LIMIT - raw) * 1000.0, 1),
            "knee_bend_deg": round(knee_bend, 2),
            "pole_sin": round(bulge.length, 4),
            "reachable": bool(raw <= limit)}


def main():
    arm, _meshes = A.open_animation_project()
    A.setup_scene()

    idle = I1.idle_pose(arm, 0.0)
    A.apply_pose(arm, idle)

    ANK = {s: Vector(A.bone_world(arm, "foot." + s, "head")) for s in SIDES}
    KNEE = {s: Vector(A.bone_world(arm, "shin." + s, "head")) for s in SIDES}
    HIP = {s: Vector(A.bone_world(arm, "thigh." + s, "head")) for s in SIDES}
    TOE = {s: Vector(A.bone_world(arm, "toe." + s, "head")) for s in SIDES}
    PELVIS = Vector(A.bone_world(arm, "pelvis", "head"))
    STERNUM = Vector(A.bone_world(arm, "neck", "head"))
    FOOT_DIR = {s: tuple(A.bone_direction(arm, "foot." + s)) for s in SIDES}

    front = "L" if ANK["L"].y < ANK["R"].y else "R"

    A.report("L06_IDENTITY", {
        "front_foot": front,
        "support": SUPPORT, "attack": ATTACK,
        "pelvis_mm": mm(PELVIS),
        "pelvis_z_mm": round(PELVIS.z * 1000.0, 1),
        "sternum_mm": mm(STERNUM),
        "ankle_mm": {s: mm(ANK[s]) for s in SIDES},
        "knee_mm": {s: mm(KNEE[s]) for s in SIDES},
        "hip_mm": {s: mm(HIP[s]) for s in SIDES},
        "toe_mm": {s: mm(TOE[s]) for s in SIDES},
        "thigh_mid_z_mm": {s: round((HIP[s].z + KNEE[s].z) * 500.0, 1)
                           for s in SIDES},
        "foot_rest_dir": {s: [round(v, 4) for v in FOOT_DIR[s]] for s in SIDES},
        "leg_bone_len_mm": {"thigh": round(A.L_THIGH * 1000.0, 1),
                            "shin": round(A.L_SHIN * 1000.0, 1),
                            "limit": round(LEG_LIMIT * 1000.0, 1)},
        "idle_hip_ankle_mm": {s: round((ANK[s] - HIP[s]).length * 1000.0, 1)
                              for s in SIDES},
        "idle_headroom_mm": {s: round((LEG_LIMIT - (ANK[s] - HIP[s]).length) * 1000.0, 1)
                             for s in SIDES},
        "hip_bone_len_mm": round((Vector(A.bone_world(arm, "thigh.L", "tail"))
                                  - HIP["L"]).length * 1000.0, 1),
        "note": ("支撑腿 = 后脚 R；攻击腿 = 前脚 L。前脚踢出时腿向前、骨盆不挡道，"
                 "且支撑腿 R 在髋**后面 140 mm** ⟹ 骨盆后移（+Y）会**缩短**支撑腿，"
                 "比反过来更安全。"),
    })

    # ---------------------------------------------------------------- 支撑腿余量
    # 单腿支撑：骨盆在 XY 上怎么挪，支撑腿 R 还够不够得到（踝钉死不动）。
    support_rows = []
    for dy_mm in (-40, -20, 0, 20, 40):
        for dz_mm in (0, -40, -60, -80, -100):
            hip = HIP[SUPPORT] + Vector((0.0, dy_mm / 1000.0, dz_mm / 1000.0))
            row = {"pelvis_dy_mm": dy_mm, "pelvis_dz_mm": dz_mm}
            for pole_name, pole in (("fwd", (0.0, -1.0, 0.0)),
                                    ("fwd_out", (0.35 if SUPPORT == "L" else -0.35,
                                                 -1.0, 0.0))):
                row["pole_" + pole_name] = _leg_geom(hip, ANK[SUPPORT], pole)
            support_rows.append(row)
    A.report("L06_SUPPORT_HEADROOM", support_rows)
    A.report("L06_SUPPORT_SUMMARY", {
        "limit_mm": round(LEG_LIMIT * 1000.0, 1),
        "idle_headroom_mm": round((LEG_LIMIT - (ANK[SUPPORT] - HIP[SUPPORT]).length)
                                  * 1000.0, 1),
        "rule": ("余量 < 20 mm 就缩骨盆位移。dz 每 −100 mm 会把 |髋→踝| **缩短**"
                 "（膝弯更深），dy 正（骨盆后移）也缩短 ⟹ 本支的下沉 + 后移"
                 "对支撑腿是**安全方向**；真正危险的是 dy 负（骨盆前移）。"),
        "worst_case": min(
            (r["pole_fwd"]["headroom_mm"], r["pelvis_dy_mm"], r["pelvis_dz_mm"])
            for r in support_rows),
    })

    # ---------------------------------------------------------------- 攻击腿 pole
    # 抬腿到「侧前方」时髋→膝轴接近水平，pole 会退化。逐候选量 |pole⊥axis|。
    attack_rows = []
    for y_mm in (-700, -600, -500, -400, -300, -200, -100, 0):
        for z_mm in (80, 150, 250, 350, 450, 550):
            target = Vector((ANK[ATTACK].x, y_mm / 1000.0, z_mm / 1000.0))
            row = {"y_mm": y_mm, "z_mm": z_mm}
            for pole_name, pole in (
                    ("fwd", (0.0, -1.0, 0.0)),
                    ("out", (-1.0, 0.0, 0.0)),
                    ("fwd_out", (-0.5, -1.0, 0.0)),
                    ("down", (0.0, 0.0, -1.0))):
                row["pole_" + pole_name] = _leg_geom(HIP[ATTACK], target, pole)
            attack_rows.append(row)
    A.report("L06_ATTACK_POLE_SCAN", attack_rows)

    # ---------------------------------------------------------------- 命中点高度
    # 骨盆沉到不同深度时，"命中脚 z < 骨盆 z − 250 mm" 还能不能解出来。
    hit_rows = []
    for dz_mm in (-40, -60, -80, -100):
        pelvis_z = PELVIS.z + dz_mm / 1000.0
        ceiling = pelvis_z - 0.250
        row = {"pelvis_dz_mm": dz_mm,
               "pelvis_z_mm": round(pelvis_z * 1000.0, 1),
               "hit_z_ceiling_mm": round(ceiling * 1000.0, 1)}
        for y_mm in (-500, -600, -650, -700, -750):
            hip = HIP[ATTACK] + Vector((0.0, 0.0, dz_mm / 1000.0))
            # 在 ceiling 之下、以及 ceiling 之上各试着解一档
            trial = {}
            for tag, z in (("below", ceiling - 0.02), ("at", ceiling)):
                trial[tag] = _leg_geom(hip, Vector((ANK[ATTACK].x, y_mm / 1000.0, z)),
                                       (-0.5, -1.0, 0.0))
                trial[tag]["z_mm"] = round(z * 1000.0, 1)
            row["y_%d" % y_mm] = trial
        hit_rows.append(row)
    A.report("L06_HIT_HEIGHT_SCAN", hit_rows)

    # ---------------------------------------------------------------- 行程 / 转角
    # `leg_amplitude_ok` 的两条腿：世界行程 ≥600 mm、以髋为轴的累计转角 ≥70°。
    for tag, y_mm, z_mm in (("chamber", -240, 300), ("strike", -670, 455),
                            ("follow", -720, 440), ("low_trial", -650, 400)):
        target = Vector((ANK[ATTACK].x, y_mm / 1000.0, z_mm / 1000.0))
        geom = _leg_geom(HIP[ATTACK], target, (-0.5, -1.0, 0.0))
        geom["travel_from_guard_mm"] = round(
            (target - ANK[ATTACK]).length * 1000.0, 1)
        v0 = (ANK[ATTACK] - HIP[ATTACK]).normalized()
        v1 = (target - Vector(HIP[ATTACK])).normalized()
        geom["hip_axis_net_deg"] = round(math.degrees(v0.angle(v1)), 2)
        geom["target_mm"] = [round(y_mm, 1), round(z_mm, 1)]
        A.report("L06_TARGET_" + tag.upper(), geom)

    A.report("L06_DECISION", {
        "support_leg": SUPPORT, "attack_leg": ATTACK,
        "plan_rule": ("命中：`hit_foot_z_mm ≤ pelvis_z_mm − 250`；"
                      "支撑：`leg_reach_headroom_mm ≥ 20`；"
                      "攻击腿 pole：`|pole⊥axis| ≥ 0.30` 否则走接力。"),
        "thigh_mid_z_mm": round((HIP[ATTACK].z + KNEE[ATTACK].z) * 500.0, 1),
        "note": ("`low_height_ok` 里「大腿中部」基准 = 髋与膝中点的高度（实测见上）；"
                 "命中脚 z 必须同时低于 `pelvis_z − 250` **和** 大腿中点。"),
    })
    print("PROBE_LOW06_DONE")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("PROBE_LOW06_FAILURE " + traceback.format_exc())
