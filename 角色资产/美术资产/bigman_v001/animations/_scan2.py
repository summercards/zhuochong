# -*- coding: utf-8 -*-
"""验证：把 pole 从 idle 实测值过渡到"侧向外"（肘朝外），看 sin 与逐帧转角。"""
import math, importlib.util, os
spec = importlib.util.spec_from_file_location(
    "sc", os.path.join(os.path.dirname(os.path.abspath(__file__)), "_scan_h02.py"))
sc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sc)

LAT_SET = {
    "纯侧向(1,0,0)": (1.0, 0.0, 0.0),
    "侧后(0.9,0.35,0)": (0.90, 0.35, 0.0),
    "侧后下(0.85,0.30,-0.25)": (0.85, 0.30, -0.25),
    "侧前下(0.9,-0.2,-0.2)": (0.90, -0.20, -0.20),
}
FO = (-0.052, -0.262, -0.492)
EN = (-0.075, -0.215, -0.325)
REC = (-0.070, -0.240, -0.410)


def pole_lat(lat, use_smoothstep=True):
    def f(s, c, cfg):
        sg = 1.0 if s == "L" else -1.0
        tgt = (sg * lat[0], lat[1], lat[2])
        w = sc.charge_s(c)
        if use_smoothstep:
            w = w * w * (3.0 - 2.0 * w)
        return sc.lerp3(sc.POLE_GUARD[s], tgt, w)
    return f


configs = {
    "C(肩上/前外弧)": sc.build((0.020, -0.030, 0.470), (0.250, -0.300, 0.130),
                              (0.030, -0.360, 0.230), (0.030, -0.250, -0.470),
                              (0.032, -0.258, -0.492), (0.040, -0.215, -0.325),
                              (0.036, -0.240, -0.410)),
    "F(宽外摆)": sc.build((0.020, -0.030, 0.470), (0.340, -0.230, 0.150),
                         (0.060, -0.430, 0.150), (0.030, -0.250, -0.470),
                         (0.032, -0.258, -0.492), (0.040, -0.215, -0.325),
                         (0.036, -0.240, -0.410)),
}
for cname, cfg in configs.items():
    for lname, lat in LAT_SET.items():
        for ce in (12, 16):
            pt = pole_lat(lat)
            r = sc.evaluate_timed(cfg, pt, ce, 1.20)
            print("%-14s %-22s ce=%d -> geom=%5.1f min_sin=%.3f@%s min_sh=%5.1f up=%4.1f@%s fo=%4.1f@%s"
                  % (cname, lname, ce, r["geom_step"], r["min_sin"], r["sin_at"],
                     r["min_sh_mm"], r["up"], r["up_at"], r["fo"], r["fo_at"]))
