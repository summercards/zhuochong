# -*- coding: utf-8 -*-
"""修正镜像后的复算（只读）：_scan_h02.build() 的 mirror() 是**点反射**
（negate 全三轴），但真实身体是**矢状面镜像**（只 negate x）。

本脚本用真实约定复算定稿解：
  - 偏移路径 L = base，R = (-x, y, z)（矢状面镜像）
  - pole 目标 L = (+lat0, lat1, lat2)，R = (-lat0, lat1, lat2)
  - 手骨方向用真实 HAMMER_HAND（L/R 各自给，本身已是矢状对）
  - 腿/躯干不参与（纯手臂几何）
"""
import importlib.util
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("sc", os.path.join(HERE, "_scan_h02.py"))
sc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sc)
spec2 = importlib.util.spec_from_file_location("s5", os.path.join(HERE, "_scan5.py"))  # noqa
# 不 exec _scan5（它会跑 20000 步），只借常量

L_UP, L_FO, L_HA = sc.L_UP, sc.L_FO, sc.L_HA
HIT, HOLD = sc.HIT, sc.HOLD
FOLLOW_END = 31

GUARD = {"L": (-0.0062, -0.2566, -0.0418), "R": (0.0211, -0.2223, -0.0147)}
POLE_GUARD = {"L": (0.3149, 0.4925, -0.8113), "R": (-0.3575, 0.4487, -0.8191)}
HAND = {"L": ((-0.20, -0.70, 0.68), (-0.10, -0.55, 0.83), (-0.08, -0.80, -0.60),
              (-0.08, -0.82, -0.58), (-0.16, -0.76, -0.63)),
        "R": ((0.18, -0.60, 0.78), (0.10, -0.55, 0.83), (0.08, -0.80, -0.60),
              (0.08, -0.82, -0.58), (0.16, -0.76, -0.63))}

BASE = {
    "apex": [0.020683, -0.110971, 0.440395],
    "rise": [0.350730, -0.008161, 0.296086],
    "bctrl": [0.150058, -0.358609, 0.076495],
    "strike": [0.032695, -0.264642, -0.426071],
    "fo": [0.031217, -0.263055, -0.458063],
    "end": [0.039758, -0.207299, -0.295671],
    "rec": [0.020042, -0.261207, -0.368822],
    "lat": [0.998973, 0.411109, 0.023887],
    "ce": 14,
    "cp": 1.24,
    "shape": "power",
}


def sag(v):
    return (-v[0], v[1], v[2])


def cfg_from(p, sag_mirror=True):
    out = {}
    for k in ("apex", "rise", "bctrl", "strike", "fo", "end", "rec"):
        out[k] = {"L": tuple(p[k]), "R": sag(tuple(p[k])) if sag_mirror else tuple(p[k])}
    return out


def pole_of(p, side):
    sg = 1.0 if side == "L" else -1.0
    return (sg * p["lat"][0], p["lat"][1], p["lat"][2])


def eval_real(p, frames=range(0, 32), verbose=False, ce=None, cp=None, shape=None):
    ce = p["ce"] if ce is None else ce
    cp = p["cp"] if cp is None else cp
    shape = p["shape"] if shape is None else shape
    old = (sc.CHARGE_END, sc.CHARGE_POW, sc.PHASE["burst_start"], sc.PHASE["charge_shape"])
    sc.CHARGE_END, sc.CHARGE_POW = ce, cp
    sc.PHASE["burst_start"] = ce
    sc.PHASE["charge_shape"] = shape
    try:
        cfg = cfg_from(p)
        worst = {s: {"up": (0.0, None), "fo": (0.0, None), "want": (0.0, None)}
                 for s in ("L", "R")}
        min_d, min_sin, min_sin_at = 9.9, 9.9, None
        dsin = 0.0
        prev = {}
        rows = []
        for f in frames:
            c = f if f <= HIT else (HIT if f <= HIT + HOLD else f - HOLD)
            row = {}
            for s in ("L", "R"):
                g = GUARD[s]
                ap = cfg["apex"][s]
                st = cfg["strike"][s]
                fo = cfg["fo"][s]
                en = cfg["end"][s]
                if c <= sc.PHASE["burst_start"]:
                    off = sc.qbez3(g, cfg["rise"][s], ap, sc.charge_s(c))
                elif c <= HIT:
                    off = sc.qbez3(ap, cfg["bctrl"][s], st, sc.burst_s(c))
                elif c <= FOLLOW_END:
                    off = sc.lerp3(st, fo, sc.follow_s(c))
                else:
                    off = sc.qbez3(fo, cfg["rec"][s], en, sc.settle_s(c))
                want = sc.vnorm(sc.chain5(*HAND[s], c))
                wrist = sc.vsub(off, sc.vmul(want, L_HA))
                d = sc.vlen(wrist)
                axis = sc.vnorm(wrist)
                w = sc.charge_s(c)
                w = w * w * (3.0 - 2.0 * w)
                pole = sc.vnorm(sc.lerp3(POLE_GUARD[s], pole_of(p, s), w))
                perp = sc.vsub(pole, sc.vmul(axis, sc.vdot(pole, axis)))
                sinv = sc.vlen(perp)
                if sinv < 1e-6:
                    perp = sc.vnorm(sc.vsub((0.0, 0.0, 1.0), sc.vmul(axis, axis[2])))
                    sinv = 0.0
                else:
                    perp = sc.vnorm(perp)
                limit = (L_UP + L_FO) * 0.9995
                dd = max(1e-4, min(d, limit))
                ch = max(-1.0, min(1.0, (L_UP ** 2 + dd ** 2 - L_FO ** 2) / (2 * L_UP * dd)))
                sh = (1.0 - ch * ch) ** 0.5
                elbow = sc.vadd(sc.vmul(axis, ch * L_UP), sc.vmul(perp, sh * L_UP))
                up = sc.vnorm(elbow)
                fo_v = sc.vnorm(sc.vsub(wrist, elbow))
                row[s] = {"d": d, "sin": sinv, "up": up, "fo": fo_v, "want": want}
                min_d = min(min_d, d)
                if sinv < min_sin:
                    min_sin, min_sin_at = sinv, (f, s)
                if s in prev:
                    for key, cur in (("up", up), ("fo", fo_v), ("want", want)):
                        a = sc.ang(prev[s][key], cur)
                        if a > worst[s][key][0]:
                            worst[s][key] = (a, f)
                    dsin = max(dsin, abs(sinv - prev[s + "_sin"]))
                prev[s] = row[s]
                prev[s + "_sin"] = sinv
            rows.append((f, row))
        per = {}
        for s in ("L", "R"):
            per[s] = {"up": round(worst[s]["up"][0], 1), "up_at": worst[s]["up"][1],
                      "fo": round(worst[s]["fo"][0], 1), "fo_at": worst[s]["fo"][1],
                      "want": round(worst[s]["want"][0], 1), "want_at": worst[s]["want"][1]}
        geom = max(max(per[s]["up"], per[s]["fo"]) for s in ("L", "R"))
        out = {"geom_step": round(geom, 1), "per_side": per,
               "min_sh_mm": round(min_d * 1000.0, 1), "min_sin": round(min_sin, 3),
               "sin_at": min_sin_at, "dsin": round(dsin, 3)}
        if verbose:
            out["rows"] = rows
        return out
    finally:
        (sc.CHARGE_END, sc.CHARGE_POW, sc.PHASE["burst_start"],
         sc.PHASE["charge_shape"]) = old


def detail(p, lo=0, hi=30):
    """逐帧打印（L/R 各自的 |wrist-sh|、sin、相邻帧 up/fo 转角）。"""
    r = eval_real(p, frames=range(lo, hi + 1), verbose=True)
    print("f   L.d     L.sin  L.up   L.fo  | R.d     R.sin  R.up   R.fo")
    prev = None
    for f, row in r["rows"]:
        if prev is None:
            print("%2d %6.1f  %.3f    -      -    | %6.1f  %.3f    -      -"
                  % (f, row["L"]["d"] * 1000, row["L"]["sin"],
                     row["R"]["d"] * 1000, row["R"]["sin"]))
        else:
            print("%2d %6.1f  %.3f %6.1f %6.1f | %6.1f  %.3f %6.1f %6.1f"
                  % (f, row["L"]["d"] * 1000, row["L"]["sin"],
                     sc.ang(prev["L"]["up"], row["L"]["up"]),
                     sc.ang(prev["L"]["fo"], row["L"]["fo"]),
                     row["R"]["d"] * 1000, row["R"]["sin"],
                     sc.ang(prev["R"]["up"], row["R"]["up"]),
                     sc.ang(prev["R"]["fo"], row["R"]["fo"])))
        prev = row
    return r


if __name__ == "__main__":
    import sys
    if "--detail" in sys.argv:
        rr = detail(BASE)
    else:
        rr = eval_real(BASE)
    print()
    print("平移解（矢状镜像）geom_step =", rr["geom_step"])
    print("  per_side:", rr["per_side"])
    print("  min_sh_mm=%.1f min_sin=%.3f %s dsin=%.3f"
          % (rr["min_sh_mm"], rr["min_sin"], rr["sin_at"], rr["dsin"]))
