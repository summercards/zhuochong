# -*- coding: utf-8 -*-
"""随机搜索：举拳/爆发弧 + 侧向 pole 轨，目标最小化逐帧真转角。"""
import math, random, importlib.util, os
spec = importlib.util.spec_from_file_location(
    "sc", os.path.join(os.path.dirname(os.path.abspath(__file__)), "_scan_h02.py"))
sc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sc)

EN = (-0.075, -0.215, -0.325)
REC = (-0.070, -0.240, -0.410)
rnd = random.Random(20261001)
N = 26000


def make_pole(lat):
    def f(s, c, cfg):
        sg = 1.0 if s == "L" else -1.0
        tgt = (sg * lat[0], lat[1], lat[2])
        w = sc.charge_s(c)
        w = w * w * (3.0 - 2.0 * w)
        return sc.lerp3(sc.POLE_GUARD[s], tgt, w)
    return f


best = []
for it in range(N):
    apex = (rnd.uniform(0.0, 0.10), rnd.uniform(-0.14, 0.02), rnd.uniform(0.36, 0.52))
    rise = (rnd.uniform(0.08, 0.50), rnd.uniform(-0.40, -0.05), rnd.uniform(0.0, 0.30))
    bctrl = (rnd.uniform(-0.05, 0.16), rnd.uniform(-0.56, -0.20), rnd.uniform(0.0, 0.30))
    strike = (rnd.uniform(0.0, 0.10), rnd.uniform(-0.32, -0.18), rnd.uniform(-0.52, -0.38))
    fo = (strike[0] + rnd.uniform(-0.02, 0.02), strike[1] - rnd.uniform(0.0, 0.02),
          strike[2] - rnd.uniform(0.0, 0.03))
    end = (apex[0] + rnd.uniform(0.0, 0.06), strike[1] + rnd.uniform(0.02, 0.06),
           strike[2] + rnd.uniform(0.08, 0.20))
    rec = (end[0] - rnd.uniform(0.0, 0.02), strike[1] - rnd.uniform(0.0, 0.03),
           strike[2] + rnd.uniform(0.02, 0.09))
    lat = (rnd.uniform(0.70, 1.0), rnd.uniform(0.0, 0.45), rnd.uniform(-0.25, 0.15))
    ce = rnd.choice([12, 13, 14, 15, 16, 17, 18])
    cp = rnd.uniform(0.9, 1.4)
    cfg = sc.build(apex, rise, bctrl, strike, fo, end, rec)
    r = sc.evaluate_timed(cfg, make_pole(lat), ce, cp)
    if r["min_sin"] < 0.50 or r["min_sh_mm"] < 155.0:
        continue
    best.append((r["geom_step"], r["up"], r["fo"], r["min_sin"], r["min_sh_mm"],
                 ce, cp, apex, rise, bctrl, strike, fo, end, rec, lat))
best.sort(key=lambda t: max(t[0], t[1], t[2]))
print("feasible:", len(best))
for row in best[:8]:
    print("geom=%5.1f up=%5.1f fo=%5.1f min_sin=%.3f min_sh=%5.1f ce=%d cp=%.2f"
          % (row[0], row[1], row[2], row[3], row[4], row[5], row[6]))
    print("   apex=%s\n   rise=%s\n   bctrl=%s\n   strike=%s\n   fo=%s\n   end=%s\n   rec=%s\n   lat=%s"
          % (row[7], row[8], row[9], row[10], row[11], row[12], row[13], row[14]))
