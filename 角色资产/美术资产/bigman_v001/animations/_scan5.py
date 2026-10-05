# -*- coding: utf-8 -*-
"""在最优解附近联合搜索：charge 缓动形状 + 举升帧数 + 弧线微调。"""
import importlib.util, os, random
spec = importlib.util.spec_from_file_location(
    "sc", os.path.join(os.path.dirname(os.path.abspath(__file__)), "_scan_h02.py"))
sc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sc)
APEX_Z_MIN = 0.425


def make_pole(lat):
    def f(s, c, cfg):
        sg = 1.0 if s == "L" else -1.0
        w = sc.charge_s(c)
        w = w * w * (3.0 - 2.0 * w)
        return sc.lerp3(sc.POLE_GUARD[s], (sg * lat[0], lat[1], lat[2]), w)
    return f


cur = {
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


def score(p):
    if p["apex"][2] < APEX_Z_MIN:
        return None, {}
    cfg = sc.build(tuple(p["apex"]), tuple(p["rise"]), tuple(p["bctrl"]),
                   tuple(p["strike"]), tuple(p["fo"]), tuple(p["end"]), tuple(p["rec"]))
    r = sc.evaluate_timed(cfg, make_pole(tuple(p["lat"])), p["ce"], p["cp"],
                          shape=p["shape"])
    if r["min_sin"] < 0.50 or r["min_sh_mm"] < 158.0:
        return None, r
    return max(r["geom_step"], r["up"], r["fo"]), r


rnd = random.Random(11)
best_s, best_r = score(cur)
print("start", best_s, {k: v for k, v in best_r.items() if k != 'rows'})
for step in range(20000):
    cand = {k: (list(v) if isinstance(v, list) else v) for k, v in cur.items()}
    k = rnd.choice(list(cur))
    if k == "ce":
        cand[k] = rnd.choice([12, 13, 14, 15, 16, 17, 18])
    elif k == "cp":
        cand[k] = cur[k] + rnd.gauss(0, 0.05)
    elif k == "shape":
        cand[k] = rnd.choice(["power", "smoothstep"])
    else:
        scale = 0.05 if k == "lat" else 0.02
        cand[k] = [v + rnd.gauss(0, scale) for v in cur[k]]
        if k == "apex":
            cand[k][2] = max(APEX_Z_MIN, cand[k][2])
    s, r = score(cand)
    if s is not None and (best_s is None or s < best_s):
        best_s, best_r, cur = s, r, cand
        print("step %5d -> %5.2f min_sin=%.3f sh=%5.1f ce=%d cp=%.2f %s"
              % (step, s, r["min_sin"], r["min_sh_mm"], cur["ce"], cur["cp"],
                 cur["shape"]))
print()
print("BEST =", best_s)
for k, v in cur.items():
    print("    %s=%s" % (k, v))
print("  detail:", {k: v for k, v in best_r.items() if k != "rows"})
