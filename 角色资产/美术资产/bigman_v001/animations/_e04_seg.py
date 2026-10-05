"""分段归因：把 TOUCH→LAND 的姿态步长拆成「躯干俯仰贡献」与「根位移贡献」。
用 monkeypatch 改 SPECS / 段长，看 raw euler 逐帧最大步怎么变。不用改源文件。
"""
import os, sys, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import anim_spawn as S

CASE = os.environ.get("CASE", "base")

if CASE == "flat":
    # LAND 的躯干俯仰 = TOUCH 的躯干俯仰（只保留下沉）
    for k in ("pelvis", "spine_01", "spine_02", "chest", "neck", "head",
              "shoulder.L", "shoulder.R"):
        S.SPECS["LAND"][k] = S.SPECS["TOUCH"][k]
elif CASE == "torso14":
    for k in ("pelvis", "spine_01", "spine_02", "chest", "neck", "head"):
        S.SPECS["LAND"][k] = min(S.SPECS["LAND"][k], S.SPECS["TOUCH"][k] * 1.3)
elif CASE == "touchup":
    S.SPECS["TOUCH"].update({"pelvis": 14.0, "spine_01": 7.0, "spine_02": 7.0,
                             "chest": 6.0, "neck": -3.0, "head": -5.0,
                             "shoulder.L": 2.0, "shoulder.R": 2.0})
elif CASE == "touchup2":
    S.SPECS["TOUCH"].update({"pelvis": 15.0, "spine_01": 7.5, "spine_02": 7.5,
                             "chest": 6.0, "neck": -3.0, "head": -6.0,
                             "shoulder.L": 1.0, "shoulder.R": 1.0})
elif CASE == "land62":
    S.LAND = 62
    S.HOLD = (62, 62 + S.HITSTOP_N - 1)
    S.KEYS = [(f, e, a, b) for (f, e, a, b) in S.KEYS]
    S.KEYS = [(62 if f == 60 else (62 + S.HITSTOP_N - 1 if f == 60 + S.HITSTOP_N - 1 else f), e, a, b)
              for (f, e, a, b) in S.KEYS]
elif CASE == "land64":
    S.KEYS = [(64 if f == 60 else (64 + S.HITSTOP_N - 1 if f == 60 + S.HITSTOP_N - 1 else f), e, a, b)
              for (f, e, a, b) in S.KEYS]

arm, meshes = S.boot()
kfs = [(f, S.spawn_pose(arm, f)) for f in range(S.START, S.END + 1)]
steps = []
for i in range(1, len(kfs)):
    a, b = kfs[i - 1][1], kfs[i][1]
    w = 0.0; at = None
    for n in set(a) | set(b):
        if n.startswith("@"):
            continue
        va = a.get(n, (0, 0, 0)); vb = b.get(n, (0, 0, 0))
        if not isinstance(va, (tuple, list)) or len(va) != 3:
            continue
        d = max(abs(x - y) for x, y in zip(va, vb))
        if d > w:
            w, at = d, n
    steps.append((w, kfs[i][0], at))
steps.sort(reverse=True)
print("CASE=%s  top:" % CASE)
for w, f, n in steps[:8]:
    print("   euler-raw %6.2f  f=%3d %s" % (w, f, n))
