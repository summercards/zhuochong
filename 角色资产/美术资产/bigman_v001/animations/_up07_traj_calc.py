"""临时算稿：用 `probe_up07_arm` 实测的**肩轨迹**预演新拳峰轨迹下的臂伸展（不跑 Blender）。

肩/骨盆只由躯干+骨盆轨决定、与 `FIST_TRACK` 无关 ⟹ 这份实测表可以直接复用。
"""
import math

SH = {0: (-150.7, -51.2, 1312.9), 1: (-150.7, -56.4, 1304.9),
      2: (-150.8, -61.6, 1296.8), 3: (-150.8, -66.8, 1288.6),
      4: (-150.8, -72.0, 1280.3), 5: (-150.8, -77.3, 1271.8),
      6: (-150.9, -82.5, 1263.3), 7: (-150.9, -91.1, 1245.7),
      8: (-150.9, -101.5, 1223.9), 9: (-151.0, -112.8, 1199.9),
      10: (-151.0, -124.5, 1174.2), 11: (-151.1, -136.5, 1146.9),
      12: (-151.1, -148.7, 1118.3), 13: (-151.1, -161.0, 1088.3),
      14: (-151.2, -173.3, 1057.1), 15: (-151.1, -168.2, 1073.7),
      16: (-150.9, -159.3, 1101.9), 17: (-150.7, -147.7, 1136.0),
      18: (-150.3, -134.1, 1173.9), 19: (-149.8, -118.7, 1213.9),
      20: (-149.2, -102.1, 1254.8), 21: (-148.3, -84.6, 1295.7),
      22: (-147.2, -66.9, 1335.8), 23: (-145.9, -49.6, 1374.3),
      24: (-144.3, -33.2, 1411.0), 25: (-144.0, -29.5, 1409.5),
      26: (-143.6, -24.4, 1407.2), 27: (-143.1, -18.8, 1404.4),
      28: (-142.5, -12.9, 1401.3), 29: (-141.9, -6.8, 1397.7),
      30: (-141.2, -0.5, 1393.8), 31: (-142.9, -4.3, 1382.9),
      32: (-144.3, -9.0, 1371.7), 33: (-145.6, -14.2, 1360.3)}
HG = (-129.6, -273.5, 1298.2)
HDG = (0.1799, -0.5998, 0.7797)
LOAD, CH, HIT, FO, CE = 6, 14, 24, 30, 47
HAND_LEN = 0.098
ARM = 0.552
FOLD_MIN = ARM * 0.32 * 1000.0
FT_LOAD = (-0.0084, 0.0255, -0.0832)
FT_FOLLOW = (0.0176, 0.0285, 0.6318)
FT_END = (-0.0054, 0.0335, 0.2618)
HD = ((0.0, 0.0, 0.0), (0.00, 0.05, -0.15), (0.00, 0.12, -0.45),
      (0.00, 0.05, 1.20), (0.00, 0.08, 1.35), (0.00, 0.20, 0.35))


def ramp(c, s, e, p):
    if c <= s:
        return 0.0
    if c >= e:
        return 1.0
    return ((c - s) / float(e - s)) ** p


def c6(g, ld, ch, st, fo, en, c, burst_pow):
    return (g + (ld - g) * ramp(c, 0, LOAD, 1.0)
            + (ch - ld) * ramp(c, LOAD, CH, 1.15)
            + (st - ch) * ramp(c, CH, HIT, burst_pow)
            + (fo - st) * ramp(c, HIT, FO, 1.25)
            + (en - fo) * ramp(c, FO, CE, 2.0))


def norm(v):
    length = math.sqrt(sum(x * x for x in v))
    return tuple(x / length for x in v)


def run(tag, cham, strike, burst_pow):
    ft = ((0.0, 0.0, 0.0), FT_LOAD, cham, strike, FT_FOLLOW, FT_END)
    print("=== " + tag + "   BURST_POW=%.2f" % burst_pow)
    worst = (9e9, None)
    for c in range(14, 25):
        off = tuple(c6(ft[0][i], ft[1][i], ft[2][i], ft[3][i], ft[4][i],
                       ft[5][i], c, burst_pow) for i in range(3))
        fist = tuple(HG[i] + off[i] * 1000.0 for i in range(3))
        d = tuple(c6(HD[0][i], HD[1][i], HD[2][i], HD[3][i], HD[4][i],
                     HD[5][i], c, burst_pow) for i in range(3))
        wdir = norm(tuple(HDG[i] + d[i] for i in range(3)))
        wrist = tuple(fist[i] - wdir[i] * HAND_LEN * 1000.0 for i in range(3))
        s = SH.get(c)
        if s is None:
            continue
        rel = tuple(fist[i] - s[i] for i in range(3))
        wr = tuple(wrist[i] - s[i] for i in range(3))
        req = math.sqrt(sum(x * x for x in wr))
        flag = "" if req >= 185.0 else "   <== 夹到环带"
        print("c=%2d req=%7.1f ext=%.3f fist=(%7.1f,%8.1f,%7.1f)"
              " rel=(%7.1f,%8.1f,%7.1f)%s"
              % (c, req, req / 552.0, fist[0], fist[1], fist[2],
                 rel[0], rel[1], rel[2], flag))
        if req < worst[0]:
            worst = (req, c)
    print("发力窗口内最紧: %.1f mm @ c=%s（夹带下界 %.1f）" % (worst[0], worst[1],
                                                          FOLD_MIN))
    print()


A = (-0.0124, 0.0755, -0.6032)
CAND = [
    ("最终候选: 前送90 + BURST_POW 2.00", (0.0116, -0.0915, 0.5618), 2.00),
    ("最终候选: 前送90 + BURST_POW 2.10", (0.0116, -0.0915, 0.5618), 2.10),
]
for tag, strike, pw in CAND:
    run(tag, A, strike, pw)

