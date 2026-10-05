"""probe_up07_arc —— B07 专用：**离线重放 `arm_to` 的几何**，用来扫「拳峰轨迹的形状」。

## 为什么需要它

`up07_gate.log` 的红项只剩一条：

    no_teleport  max_frame_step_deg 45.131 @ f24 'forearm.R'（预算 25）

但 `UP07_ROT_DIAG` 把真相掀开了 —— **真正超标的是世界转角，不是欧拉表示**：

    f20→21  upperarm.R 32.55  forearm.R 40.24      ← 超
    f21→22  upperarm.R 39.62  forearm.R 33.44      ← 超
    f22→23  upperarm.R 26.13                       ← 超
    f23→24  upperarm.R 27.45                       ← 超

而同期的 `arm_ext["R"]` 是 `0.3695 → 0.32(夹) → 0.3556 → 0.5606 → 0.8491`：
**臂在发力窗口里先被夹到折叠下界、再被拽开** —— 文件头第 6 件
「夹取是安全网，不是设计」在**峰值速率**上的表现。

## 根因（本探针量出来的）

拳峰轨迹在**世界偏移空间**是 chamber→strike 的**直线**，而肩同时在动。
逐帧算「拳峰 − 肩」这个相对向量：

    c14  |rel| = 363 mm   （拳在腰侧，肩在 1057 高）        ← 健康
    c21  |rel| = 181 mm   （拳 1266 高，**肩也升到 1259.5**）← 塌了
    c24  |rel| = 560 mm   （拳 1860 高，肩 1411）            ← 健康

**肩的上升速度追上了拳**：c14→c24 肩升 354 mm、拳升 1165 mm，但拳的上升被
`BURST_POW` 后置，于是 c21 那一刻**肩正好升到与拳同高**，拳从肩口穿过。

两段相对向量的夹角 = **139.3°**，直线插值的最近点落在 `t*=0.161` 处、
长度 ≈ 107 mm —— 与门禁实测的 162.2 mm（腕口径）同量级，**模型自洽**。

## 本探针做什么

Blender 里**逐帧重放 `build_pose` 的躯干/骨盆 → 肩**，然后：
  1. 用可替换的 `fist_target` 候选算出「请求距离 req」；
  2. **按 `arm_to` 同一套几何**（`axis` / `_bulge` / `cos_hip` / `sin_hip`）解出
     `elbow`、`wrist_target`，于是拿到上臂/前臂的**世界方向**；
  3. 逐帧求**世界方向转角**（上臂、前臂）—— 这就是 `no_teleport` 的物理量代理。

跑一轮 = 几秒（不渲染、不出图、不写 blend），所以可以**先扫参数再改文件**。

## 候选空间

  * `line`：现状（世界偏移空间直线，`BURST_POW` 幂律）—— **基线**，用来验模型。
  * `bez` ：世界空间二次贝塞尔，控制点 = 中点 + `k·out`。
  * `slerp`：**肩相对插值** —— `rel = 拳 − 肩` 的**方向 slerp** + **长度线性**。
    两端点与 `line` 逐位相同 ⟹ 6 个关键姿态不变，只有中间形状变。

判据（都在爆发窗口 `[CHARGE_END, HIT]` 内，且**不看全程峰**——B06 第 4 件事）：
  * `min_req` ≥ 折叠下界（**不许夹**）；
  * `max_axis` / `max_upper` / `max_fore` ≤ 25（`no_teleport` 预算）。
"""

import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A          # noqa: E402
import anim_idle_01 as I1     # noqa: E402
import anim_uppercut as U     # noqa: E402


def setup(arm):
    U.IDLE_POSE = I1.idle_pose(arm, 0.0)
    U.ANKLE_REST = {s: Vector(A.bone_world(arm, "foot." + s, "head"))
                    for s in U.SIDES}
    U.POLE_LEG = {s: U._leg_pole_from_pose(arm, s) for s in U.SIDES}
    U.POLE_ARM = {s: U._elbow_pole_from_pose(arm, s) for s in U.SIDES}
    U.HAND_GUARD = {s: tuple(A.bone_direction(arm, "hand." + s))
                    for s in U.SIDES}
    U.I1_FIST_GUARD = {s: tuple(Vector(A.bone_world(arm, "hand." + s, "tail")))
                       for s in U.SIDES}


def apply_trunk(arm, c):
    """逐位复刻 `build_pose` 里**肩之前**的部分（躯干 + 骨盆），不多不少。"""
    pose = U.trunk_pose(c)
    pose["toe.L"] = (0.0, 0.0, 0.0)
    pose["toe.R"] = (0.0, 0.0, 0.0)
    pose["@loc"] = {"pelvis": A.wloc(U.chain6(*U.PELVIS_DX, c),
                                     U.chain6(*U.PELVIS_DY, c),
                                     U.DROP + U.chain6(*U.PELVIS_DZ, c))}
    pose.update(A.FIST)
    A.apply_pose(arm, pose)
    bpy.context.view_layer.update()


def world_fist(side, c):
    """现状的世界拳峰轨（`line` 基线；也是 slerp 两端点的锚）。"""
    return Vector(U.I1_FIST_GUARD[side]) + Vector(U.chain3(U.FIST_TRACK[side], c))


# ----------------------------------------------------------------- 候选轨迹
def make_line(pow_burst):
    def target(side, c):
        if U.CHARGE_END < c < U.HIT:
            u = ((c - U.CHARGE_END) / float(U.HIT - U.CHARGE_END)) ** pow_burst
            return (world_fist(side, U.CHARGE_END) * (1.0 - u)
                    + world_fist(side, U.HIT) * u)
        return world_fist(side, c)
    return target


def make_bez(pow_burst, k_m, out):
    control = {s: 0.5 * (world_fist(s, U.CHARGE_END)
                         + world_fist(s, U.HIT)) + Vector(out) * k_m
               for s in U.SIDES}
    a = {s: world_fist(s, U.CHARGE_END) for s in U.SIDES}
    b = {s: world_fist(s, U.HIT) for s in U.SIDES}

    def target(side, c):
        if U.CHARGE_END < c < U.HIT:
            u = ((c - U.CHARGE_END) / float(U.HIT - U.CHARGE_END)) ** pow_burst
            return ((1.0 - u) ** 2 * a[side] + 2.0 * (1.0 - u) * u
                    * control[side] + u * u * b[side])
        return world_fist(side, c)
    return target


def make_slerp(arm, pow_burst, bow_m=0.0, side=None):
    """肩相对插值：`fist = 肩(c) + |rel|·slerp(rel 方向)`。

    ★ 端点由构造逐位等于 `line`（`u=0` → `肩(14)+rel_a` = 现状 c14 拳位；
      `u=1` → `肩(24)+rel_b` = 现状 c24 拳位）⟹ **六个关键姿态一个不动**。
    `bow_m` = 长度的正弦鼓包（正 = 中途离肩更远）。
    ★ `pow_burst` 只作用于**臂自己的**摆动斜坡，**不动 `U.BURST_POW`**
      （后者经 `chain6` 驱动躯干/骨盆/腿/脚，动它等于把整支重做）。
    """
    apply_trunk(arm, U.CHARGE_END)
    rel_a = {s: world_fist(s, U.CHARGE_END)
             - Vector(A.bone_world(arm, "upperarm." + s, "head")) for s in U.SIDES}
    apply_trunk(arm, U.HIT)
    rel_b = {s: world_fist(s, U.HIT)
             - Vector(A.bone_world(arm, "upperarm." + s, "head")) for s in U.SIDES}

    def target(s, c):
        if U.CHARGE_END <= c <= U.HIT and (side is None or s == side):
            shoulder = Vector(A.bone_world(arm, "upperarm." + s, "head"))
            u = ((c - U.CHARGE_END) / float(U.HIT - U.CHARGE_END)) ** pow_burst
            ra, rb = rel_a[s], rel_b[s]
            direction = ra.normalized().slerp(rb.normalized(), u)
            length = (ra.length + u * (rb.length - ra.length)
                      + bow_m * math.sin(math.pi * u))
            return shoulder + direction * length
        return world_fist(s, c)
    return target


def make_shifted(arm, l_shift, pow_r, bow_r=0.0, l_slerp_pow=None, l_bow=0.0,
                 r_dip=0.0, l_dip=0.0, l_pow=None):
    """双臂都走肩相对弧：**方向 slerp + 半径带"中途收拢"鼓包**。

    半径 `L(u) = 线性 + dip·sin(πu)`（`dip < 0` = 中途把拳收向身体）：
      * `dip = 0`   → 半径单调 363→560，拳会画一条**前凸 299 mm** 的大弧（"抡"感）；
      * `dip < 0`   → 中途收拢，拳贴身穿过去，但**必须 ≥ 夹取下界**（否则又回到夹取）。

    L 侧 `l_shift` 仍可把世界轨的 y 前移（在 `l_slerp_pow is None` 时生效）。
    """
    track = {s: [tuple(col) for col in U.FIST_TRACK[s]] for s in U.SIDES}
    if l_shift:
        for col in (1, 2, 3, 4):
            row = list(track["L"][col])
            row[1] += l_shift
            track["L"][col] = tuple(row)
    guard = {s: Vector(U.I1_FIST_GUARD[s]) for s in U.SIDES}
    apply_trunk(arm, U.CHARGE_END)
    rel_a = {s: world_fist(s, U.CHARGE_END)
             - Vector(A.bone_world(arm, "upperarm." + s, "head")) for s in U.SIDES}
    apply_trunk(arm, U.HIT)
    rel_b = {s: world_fist(s, U.HIT)
             - Vector(A.bone_world(arm, "upperarm." + s, "head")) for s in U.SIDES}

    def shifted(s, c):
        return guard[s] + Vector(U.chain3(track[s], c))

    def arc(s, c, pow_side, dip):
        shoulder = Vector(A.bone_world(arm, "upperarm." + s, "head"))
        u = ((c - U.CHARGE_END) / float(U.HIT - U.CHARGE_END)) ** pow_side
        ra, rb = rel_a[s], rel_b[s]
        direction = ra.normalized().slerp(rb.normalized(), u)
        length = (ra.length + u * (rb.length - ra.length)
                  + dip * math.sin(math.pi * u))
        return shoulder + direction * length

    def target(s, c):
        if U.CHARGE_END <= c <= U.HIT:
            if s == "R":
                return arc(s, c, pow_r, r_dip + bow_r)
            if l_slerp_pow is not None:
                return arc(s, c, l_slerp_pow, l_dip + l_bow)
            if l_pow is not None:
                return arc(s, c, l_pow, l_dip)
        return shifted(s, c)
    return target


def replay(arm, target):
    """按 `arm_to` 同一套几何重放两臂，返回逐帧几何行。"""
    U._BULGE_PREV.clear()
    rows, prev = [], {}
    for c in range(0, U.HIT + U.HOLD + 1):
        apply_trunk(arm, c)
        row = {"c": c}
        for side in U.SIDES:
            upper, fore, handb = U.ARM_BONES[side]
            length_up = U.bone_len(arm, upper)
            length_fore = U.bone_len(arm, fore)
            want = U.hand_dir(side, c)
            fist = target(side, c)
            wrist = fist - want * U.bone_len(arm, handb)
            shoulder = Vector(A.bone_world(arm, upper, "head"))
            delta = wrist - shoulder
            raw = delta.length
            reach = length_up + length_fore
            fold_min = reach * U.FOLD_MIN_RATIO
            axis = (delta.normalized() if raw > 1e-9
                    else Vector((0.0, -1.0, 0.0)))
            dist = max(1e-4, min(raw, reach * 0.9995))
            if dist < fold_min:
                dist = fold_min
                wrist = shoulder + axis * dist
            bulge, _ = U._bulge("arm." + side, axis, U._arm_pole(side, c))
            cos_hip = (length_up ** 2 + dist ** 2 - length_fore ** 2) \
                / (2.0 * length_up * dist)
            cos_hip = max(-1.0, min(1.0, cos_hip))
            sin_hip = (1.0 - cos_hip * cos_hip) ** 0.5
            elbow = shoulder + (axis * cos_hip + bulge * sin_hip) * length_up
            row[side] = {
                "req": raw * 1000.0, "clamped": raw < fold_min - 1e-9,
                "ext": raw / reach, "sin_hip": sin_hip,
                "fist": fist, "shoulder": shoulder,
                "rel": (fist - shoulder).length * 1000.0,
                "axis": axis, "upper": (elbow - shoulder).normalized(),
                "fore": (wrist - elbow).normalized(),
            }
            for tag, vec in (("axis", axis), ("upper", row[side]["upper"]),
                             ("fore", row[side]["fore"])):
                q = prev.get((side, tag))
                if q is not None:
                    ang = math.degrees(q.angle(vec)) % 360.0
                    row.setdefault("d", {})[(side, tag)] = \
                        ang if ang <= 180.0 else 360.0 - ang
                prev[(side, tag)] = vec.copy()
        rows.append(row)
    return rows


def summarise(rows, tag):
    use = [r for r in rows if U.CHARGE_END < r["c"] <= U.HIT]
    out = {"tag": tag, "frames": [r["c"] for r in use]}
    for side in U.SIDES:
        reqs = [r[side]["req"] for r in use]
        out[side] = {
            "min_req": round(min(reqs), 1),
            "min_req_c": use[reqs.index(min(reqs))]["c"],
            "req_at_hit": round(use[-1][side]["req"], 1),
            "min_rel": round(min(r[side]["rel"] for r in use), 1),
            "ext_span": [round(use[0][side]["ext"], 3),
                         round(use[-1][side]["ext"], 3)],
            "ext_series": [round(r[side]["ext"], 3) for r in use],
            "clamped": [r["c"] for r in use if r[side]["clamped"]],
            "axis_series": [round(r["d"][(side, "axis")], 1) for r in use],
            "upper_series": [round(r["d"][(side, "upper")], 1) for r in use],
            "fore_series": [round(r["d"][(side, "fore")], 1) for r in use],
            "max_axis": round(max(r["d"][(side, "axis")] for r in use), 2),
            "max_upper": round(max(r["d"][(side, "upper")] for r in use), 2),
            "max_fore": round(max(r["d"][(side, "fore")] for r in use), 2),
            "min_sin_hip": round(min(r[side]["sin_hip"] for r in use), 3),
        }
    out["worst"] = round(max(max(r["d"][(s, "axis")] for s in U.SIDES)
                             for r in use), 2)
    for side in U.SIDES:
        full = [r for r in rows if 1 <= r["c"] <= U.HIT + U.HOLD]
        out[side]["clamped_all"] = [r["c"] for r in full
                                    if r[side]["clamped"]]
        out[side]["min_req_all"] = round(min(r[side]["req"] for r in full), 1)
    burst = [r for r in rows if U.CHARGE_END <= r["c"] <= U.HIT]
    for side in U.SIDES:
        path, speed = [], []
        for i, r in enumerate(burst):
            path.append([round(v * 1000.0, 1) for v in r[side]["fist"]])
            speed.append(round((r[side]["fist"]
                                - burst[i - 1][side]["fist"]).length * 1000.0, 1)
                         if i else 0.0)
        # 弧的"前凸"：拳路径到弦的最大垂距（mm）—— 弦 = chamber→strike
        p0, p1 = burst[0][side]["fist"], burst[-1][side]["fist"]
        chord = p1 - p0
        bulge = 0.0
        if chord.length > 1e-9:
            for r in burst[1:-1]:
                v = r[side]["fist"] - p0
                bulge = max(bulge, (v - chord * (v.dot(chord)
                                                 / chord.length_squared)).length)
        out[side]["path"] = path
        out[side]["speed"] = speed
        out[side]["bulge_mm"] = round(bulge * 1000.0, 1)
    out["hit_fist"] = {s: [round(v * 1000.0, 1) for v in
                           rows[U.HIT][s]["fist"]] for s in U.SIDES}
    out["crouch_fist"] = {s: [round(v * 1000.0, 1) for v in
                              rows[U.CHARGE_END][s]["fist"]] for s in U.SIDES}
    return out


CONFIGS = [
    ("R-arc1.20  L=世界线(现状)",
     dict(l_shift=0.0, pow_r=1.20)),
    ("R-arc1.20  L-arc p=1.20 dip+0.06",
     dict(l_shift=0.0, pow_r=1.20, l_pow=1.20, l_dip=0.06)),
    ("R-arc1.20  L-arc p=1.10 dip+0.06",
     dict(l_shift=0.0, pow_r=1.20, l_pow=1.10, l_dip=0.06)),
    ("R-arc1.20  L-arc p=1.00 dip+0.06",
     dict(l_shift=0.0, pow_r=1.20, l_pow=1.00, l_dip=0.06)),
    ("R-arc1.20  L-arc p=1.10 dip+0.00",
     dict(l_shift=0.0, pow_r=1.20, l_pow=1.10)),
]


def sweep(arm, fold):
    """用给定 `FOLD_MIN_RATIO` 跑一遍候选。"""
    keep = U.FOLD_MIN_RATIO
    U.FOLD_MIN_RATIO = fold
    out = [summarise(replay(arm, make_line(U.BURST_POW)),
                     "line p=%.2f  [基线]" % U.BURST_POW)]
    for tag, kw in CONFIGS:
        out.append(summarise(replay(arm, make_shifted(arm, **kw)), tag))
    U.FOLD_MIN_RATIO = keep
    return out


def main():
    arm, _ = A.open_animation_project()
    A.setup_scene()
    setup(arm)

    geom = []
    for c in range(0, U.HIT + U.HOLD + 1):
        apply_trunk(arm, c)
        geom.append({"c": c, "pelvis_z": round(
            Vector(A.bone_world(arm, "pelvis", "head")).z * 1000.0, 1),
            "sh_R": [round(v * 1000.0, 1)
                     for v in A.bone_world(arm, "upperarm.R", "head")],
            "sh_L": [round(v * 1000.0, 1)
                     for v in A.bone_world(arm, "upperarm.L", "head")]})
    reach = U.bone_len(arm, "upperarm.R") + U.bone_len(arm, "forearm.R")
    A.report("UP07_ARC_GEOM", {
        "arm_len_mm": round(reach * 1000.0, 1),
        "physical_fold_mm": round(
            abs(U.bone_len(arm, "upperarm.R") - U.bone_len(arm, "forearm.R"))
            * 1000.0, 1),
        "fold_min_mm_at_0.32": round(reach * 0.32 * 1000.0, 1),
        "rows": geom,
        "note": "肩的世界 z 逐帧真值 —— c14 深蹲底 vs c24 命中帧，看肩抬高了多少。",
    })

    A.report("UP07_ARC_SWEEP", {
        "budget_deg_per_frame": 25.0,
        "fold_min_ratio": 0.32,
        "note": "`max_*` = 世界方向逐帧转角（`axis` = 肩→腕单位向量）。"
                "判据：min_req ≥ fold_min（不夹）+ 三种转角 ≤ 25。"
                "`frames` 是爆发窗口的时钟序列，series 与它对齐。",
        "results": sweep(arm, 0.32),
    })
    A.report("UP07_ARC_SWEEP_FOLD022", {
        "budget_deg_per_frame": 25.0,
        "fold_min_ratio": 0.22,
        "note": "同候选、只把折叠下界换成**由 `sin_hip ≥ 0.30` 反解**出来的 0.22"
                "（= 121.4 mm；物理折叠极限 104 mm）。看残余夹取是否消失。",
        "results": sweep(arm, 0.22),
    })


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("UP07_ARC_PROBE_FAILURE " + traceback.format_exc())
