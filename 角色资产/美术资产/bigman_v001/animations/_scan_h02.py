# -*- coding: utf-8 -*-
"""纯几何扫描（只读）：候选拳路 + pole 轨，量"上臂/前臂世界方向逐帧转角"。

网格搜索目标：min_sin 尽量大、上臂/前臂逐帧真转角尽量小、腕-肩距离不塌陷。
"""
import math
import itertools

L_UP, L_FO, L_HA = 0.328, 0.224, 0.098
HIT, HOLD = 26, 3
PHASE = {"burst_start": 12, "charge_end": 12, "charge_pow": 1.30,
         "charge_shape": "power"}
CHARGE_END, FOLLOW_END, RECOVER_END = 12, 31, 46
CHARGE_POW, BURST_POW, FOLLOW_POW, SETTLE_POW = 1.30, 1.20, 1.25, 2.00


def vadd(a, b):
    return tuple(a[i] + b[i] for i in range(3))


def vsub(a, b):
    return tuple(a[i] - b[i] for i in range(3))


def vmul(a, s):
    return tuple(a[i] * s for i in range(3))


def vlen(a):
    return math.sqrt(sum(x * x for x in a))


def vnorm(a):
    l = vlen(a)
    return tuple(x / l for x in a) if l > 1e-12 else (0.0, 0.0, 0.0)


def vdot(a, b):
    return sum(a[i] * b[i] for i in range(3))


def lerp3(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def qbez3(p0, p1, p2, t):
    u = 1.0 - t
    return tuple(u * u * p0[i] + 2.0 * u * t * p1[i] + t * t * p2[i] for i in range(3))


def ramp(c, start, end, p):
    if c <= start:
        return 0.0
    if c >= end:
        return 1.0
    return ((c - start) / float(end - start)) ** p


def charge_s(c):
    if PHASE.get("charge_shape") == "smoothstep":
        if c <= 0.0:
            return 0.0
        if c >= CHARGE_END:
            return 1.0
        u = c / float(CHARGE_END)
        return u * u * (3.0 - 2.0 * u)
    return ramp(c, 0.0, CHARGE_END, CHARGE_POW)


def burst_s(c):
    return ramp(c, PHASE["burst_start"], HIT, BURST_POW)


def follow_s(c):
    return ramp(c, HIT, FOLLOW_END, FOLLOW_POW)


def settle_s(c):
    u = (c - FOLLOW_END) / float(RECOVER_END - FOLLOW_END)
    if u <= 0.0:
        return 0.0
    if u >= 1.0:
        return 1.0
    return 1.0 - (1.0 - u) ** SETTLE_POW


def chain5(g, ch, st, fo, en, c):
    return tuple(
        g[i] + (ch[i] - g[i]) * charge_s(c) + (st[i] - ch[i]) * burst_s(c)
        + (fo[i] - st[i]) * follow_s(c) + (en[i] - fo[i]) * settle_s(c)
        for i in range(3))


GUARD = {"L": (-0.0062, -0.2566, -0.0418), "R": (0.0211, -0.2223, -0.0147)}
HAND = {"L": ((-0.20, -0.70, 0.68), (-0.10, -0.55, 0.83), (-0.08, -0.80, -0.60),
              (-0.08, -0.82, -0.58), (-0.16, -0.76, -0.63)),
        "R": ((0.18, -0.60, 0.78), (0.10, -0.55, 0.83), (0.08, -0.80, -0.60),
              (0.08, -0.82, -0.58), (0.16, -0.76, -0.63))}
POLE_GUARD = {"L": (0.3149, 0.4925, -0.8113), "R": (-0.3575, 0.4487, -0.8191)}


def mirror(v):
    return tuple(-x for x in v)


def build(apex, rise_ctrl, burst_ctrl, strike, follow, end, rec):
    d = {"guard": dict(GUARD), "hand": dict(HAND)}
    for key, base_v in (("apex", apex), ("rise_ctrl", rise_ctrl),
                        ("ctrl", burst_ctrl), ("strike", strike),
                        ("follow", follow), ("end", end), ("rec", rec)):
        d[key] = {"L": tuple(base_v), "R": mirror(base_v)}
    return d


def pole_track_factory(g_apex, g_strike, g_follow=None, g_end=None):
    def f(s, c, cfg):
        ap = tuple(g_apex) if s == "L" else mirror(g_apex)
        st = tuple(g_strike) if s == "L" else mirror(g_strike)
        fo = tuple(g_follow or g_strike)
        en = tuple(g_end or g_follow or g_strike)
        if s == "R":
            fo, en = mirror(fo), mirror(en)
        return chain5(POLE_GUARD[s], ap, st, fo, en, c)
    return f


def pole_fixed(s, c, cfg):
    return POLE_GUARD[s]


def pose_path(side, c, cfg, pole_raw):
    g = cfg["guard"][side]
    ap = cfg["apex"][side]
    st = cfg["strike"][side]
    fo = cfg["follow"][side]
    if c <= PHASE["burst_start"]:
        off = qbez3(g, cfg["rise_ctrl"][side], ap, charge_s(c))
    elif c <= HIT:
        off = qbez3(ap, cfg["ctrl"][side], st, burst_s(c))
    elif c <= FOLLOW_END:
        off = lerp3(st, fo, follow_s(c))
    else:
        off = qbez3(fo, cfg["rec"][side], cfg["end"][side], settle_s(c))
    hd = cfg["hand"][side]
    want = vnorm(chain5(hd[0], hd[1], hd[2], hd[3], hd[4], c))
    wrist = vsub(off, vmul(want, L_HA))
    d = vlen(wrist)
    axis = vnorm(wrist)
    pole = vnorm(pole_raw)
    perp = vsub(pole, vmul(axis, vdot(pole, axis)))
    sin_pole = vlen(perp)
    if sin_pole < 1e-6:
        perp = vnorm(vsub((0.0, 0.0, 1.0), vmul(axis, axis[2])))
        sin_pole = 0.0
    else:
        perp = vnorm(perp)
    limit = (L_UP + L_FO) * 0.9995
    dd = max(1e-4, min(d, limit))
    cos_hip = (L_UP ** 2 + dd ** 2 - L_FO ** 2) / (2.0 * L_UP * dd)
    cos_hip = max(-1.0, min(1.0, cos_hip))
    sin_hip = math.sqrt(max(0.0, 1.0 - cos_hip * cos_hip))
    elbow = vadd(vmul(axis, cos_hip * L_UP), vmul(perp, sin_hip * L_UP))
    return {"off": off, "want": want, "wrist": wrist, "d": d, "sin": sin_pole,
            "up": vnorm(elbow), "fo": vnorm(vsub(wrist, elbow))}


def ang(a, b):
    c = max(-1.0, min(1.0, vdot(vnorm(a), vnorm(b))))
    return math.degrees(math.acos(c))


def evaluate(cfg, pole_track, frames=range(0, 32), verbose=False):
    worst = {"up": (0.0, None), "fo": (0.0, None), "want": (0.0, None)}
    min_d, min_sin, min_sin_at = 9.9, 9.9, None
    max_sin_step = 0.0
    prev = {}
    rows = []
    for f in frames:
        c = f if f <= HIT else (HIT if f <= HIT + HOLD else f - HOLD)
        row = {}
        for s in ("L", "R"):
            r = pose_path(s, c, cfg, pole_track(s, c, cfg))
            row[s] = r
            min_d = min(min_d, r["d"])
            if r["sin"] < min_sin:
                min_sin, min_sin_at = r["sin"], (f, s)
            if s in prev:
                for key, cur in (("up", r["up"]), ("fo", r["fo"]), ("want", r["want"])):
                    a = ang(prev[s][key], cur)
                    if a > worst[key][0]:
                        worst[key] = (a, (f, s))
                max_sin_step = max(max_sin_step, abs(r["sin"] - prev[s + "_sin"]))
            prev[s] = r
            prev[s + "_sin"] = r["sin"]
        rows.append((f, row))
    geom_step = max(worst["up"][0], worst["fo"][0])
    out = {"min_sh_mm": round(min_d * 1000.0, 1),
           "min_sin": round(min_sin, 3), "sin_at": min_sin_at,
           "dsin": round(max_sin_step, 3),
           "up": round(worst["up"][0], 1), "up_at": worst["up"][1],
           "fo": round(worst["fo"][0], 1), "fo_at": worst["fo"][1],
           "geom_step": round(geom_step, 1),
           "hnd": round(worst["want"][0], 1), "hnd_at": worst["want"][1]}
    if verbose:
        out["rows"] = [(f, round(row["L"]["d"] * 1000, 1), round(row["L"]["sin"], 3),
                        round(row["R"]["d"] * 1000, 1), round(row["R"]["sin"], 3))
                       for f, row in rows]
    return out


def evaluate_timed(cfg, pole_track, charge_end, charge_pow, shape="power"):
    """在指定的举升参数下评估（用局部 ram 覆盖全局常量）。"""
    global CHARGE_END, CHARGE_POW
    old = (CHARGE_END, CHARGE_POW, PHASE["burst_start"], PHASE["charge_shape"])
    CHARGE_END, CHARGE_POW = charge_end, charge_pow
    PHASE["burst_start"] = charge_end
    PHASE["charge_shape"] = shape
    try:
        return evaluate(cfg, pole_track, frames=range(0, HIT + 1))
    finally:
        (CHARGE_END, CHARGE_POW, PHASE["burst_start"],
         PHASE["charge_shape"]) = old


def _grid():
    PT = pole_track_factory((0.60, 0.72, 0.10), (0.62, 0.66, -0.42))
    rise_set = [(0.34, -0.20, 0.16), (0.30, -0.30, 0.10), (0.26, -0.16, 0.22),
                (0.40, -0.26, 0.10), (0.22, -0.34, 0.12)]
    bctrl_set = [(0.060, -0.430, 0.150), (0.020, -0.400, 0.220),
                 (0.100, -0.360, 0.200), (0.060, -0.500, 0.100)]
    apex_set = [(0.020, -0.030, 0.470), (0.060, -0.040, 0.470)]
    strike_set = [(0.030, -0.250, -0.470), (0.070, -0.230, -0.470)]
    FO = (-0.052, -0.262, -0.492)
    EN = (-0.075, -0.215, -0.325)
    REC = (-0.070, -0.240, -0.410)
    rows = []
    for ce, cp in ((14, 1.10), (16, 1.10), (16, 1.30), (18, 1.10), (18, 1.30)):
        for apex, rise, bctrl, strike in itertools.product(
                apex_set, rise_set, bctrl_set, strike_set):
            cfg = build(apex, rise, bctrl, strike,
                        (strike[0] - 0.002, FO[1], FO[2]), EN, REC)
            r = evaluate_timed(cfg, PT, ce, cp)
            score = (r["geom_step"] + max(0.0, 0.70 - r["min_sin"]) * 60.0
                     + max(0.0, 0.18 - r["min_sh_mm"] / 1000.0) * 400.0)
            rows.append((score, r["geom_step"], r["min_sin"], r["min_sh_mm"],
                         ce, cp, apex, rise, bctrl, strike, r))
    rows.sort(key=lambda t: t[0])
    print("=== TOP 10 ===")
    for row in rows[:10]:
        print("score=%5.1f geom=%5.1f min_sin=%.3f min_sh=%5.1f ce=%d cp=%.2f"
              % (row[0], row[1], row[2], row[3], row[4], row[5]))
        print("   apex=%s rise=%s bctrl=%s strike=%s" % (row[6], row[7], row[8], row[9]))
        print("  ", {k: v for k, v in row[10].items() if k != "rows"})


def trace(side, cfg, pole_track, charge_end, charge_pow, lo=0, hi=28,
          shape="power"):
    """逐帧打印：|wrist-sh|、|pole⊥axis|、pole 投影方向、上臂方向，及相邻帧转角。"""
    global CHARGE_END, CHARGE_POW
    old = (CHARGE_END, CHARGE_POW, PHASE["burst_start"], PHASE["charge_shape"])
    CHARGE_END, CHARGE_POW = charge_end, charge_pow
    PHASE["burst_start"] = charge_end
    PHASE["charge_shape"] = shape
    try:
        prev = None
        print("f  |wrist-sh|mm  sin   perp_step  up_step  fore_step   axis")
        for f in range(lo, hi + 1):
            c = f if f <= HIT else (HIT if f <= HIT + HOLD else f - HOLD)
            pole_raw = pole_track(side, c, cfg)
            g = cfg["guard"][side]
            ap = cfg["apex"][side]
            st = cfg["strike"][side]
            if c <= PHASE["burst_start"]:
                off = qbez3(g, cfg["rise_ctrl"][side], ap, charge_s(c))
            elif c <= HIT:
                off = qbez3(ap, cfg["ctrl"][side], st, burst_s(c))
            elif c <= FOLLOW_END:
                off = lerp3(st, cfg["follow"][side], follow_s(c))
            else:
                off = qbez3(cfg["follow"][side], cfg["rec"][side],
                            cfg["end"][side], settle_s(c))
            want = vnorm(chain5(*cfg["hand"][side], c))
            wrist = vsub(off, vmul(want, L_HA))
            axis = vnorm(wrist)
            pole = vnorm(pole_raw)
            perp = vsub(pole, vmul(axis, vdot(pole, axis)))
            sinv = vlen(perp)
            perp = vnorm(perp) if sinv > 1e-6 else vnorm(
                vsub((0.0, 0.0, 1.0), vmul(axis, axis[2])))
            limit = (L_UP + L_FO) * 0.9995
            dd = max(1e-4, min(vlen(wrist), limit))
            ch = max(-1.0, min(1.0, (L_UP ** 2 + dd ** 2 - L_FO ** 2) / (2 * L_UP * dd)))
            sh = math.sqrt(max(0.0, 1 - ch * ch))
            elbow = vadd(vmul(axis, ch * L_UP), vmul(perp, sh * L_UP))
            up = vnorm(elbow)
            fo = vnorm(vsub(wrist, elbow))
            if prev is None:
                print("%2d %7.1f  %.3f      -        -        -        %s"
                      % (f, vlen(wrist) * 1000, sinv, [round(x, 3) for x in axis]))
            else:
                print("%2d %7.1f  %.3f  %7.2f  %7.2f  %7.2f  %s"
                      % (f, vlen(wrist) * 1000, sinv, ang(prev["perp"], perp),
                         ang(prev["up"], up), ang(prev["fo"], fo),
                         [round(x, 3) for x in axis]))
            prev = {"perp": perp, "up": up, "fo": fo}
    finally:
        (CHARGE_END, CHARGE_POW, PHASE["burst_start"],
         PHASE["charge_shape"]) = old


def _demo():
    PT = pole_track_factory((0.60, 0.72, 0.10), (0.62, 0.66, -0.42))
    FO = (-0.052, -0.262, -0.492)
    EN = (-0.075, -0.215, -0.325)
    REC = (-0.070, -0.240, -0.410)
    best = build((0.060, -0.040, 0.470), (0.400, -0.260, 0.100),
                 (0.060, -0.430, 0.150), (0.030, -0.250, -0.470),
                 (0.028, -0.262, -0.492), EN, REC)
    print("### R 侧 trace（ce=18, cp=1.10）")
    trace("R", best, PT, 18, 1.10)
    print()
    print("### 原配置 R 侧 trace（ce=12, cp=1.30）")
    old = build((-0.068, -0.020, 0.457), (-0.0062, -0.2566, -0.0418),
                (-0.100, -0.230, 0.060), (-0.050, -0.255, -0.470),
                FO, EN, REC)
    trace("R", old, pole_fixed, 12, 1.30)


if __name__ == "__main__":
    import sys
    if "--demo" in sys.argv:
        _demo()
    else:
        _grid()
