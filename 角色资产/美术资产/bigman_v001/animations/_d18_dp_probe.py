"""只读：量「逐骨 DP（纯表示自由度：换支 + ±360 缠绕）」能把 max_frame_step 压到多少。"""
import json, math, os, sys
import bpy  # noqa
from mathutils import Euler
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import anim_ultimate_end as UE

P = os.path.join(_HERE, "_d18_gate_samples.json")
d = json.load(open(P, encoding="utf-8"))

def cands(v):
    m = Euler([math.radians(x) for x in v], "XYZ").to_matrix()
    out = []
    for c in UE._xyz_candidates(m):
        b = [math.degrees(t) for t in c]
        for k0 in (-1, 0, 1):
            for k1 in (-1, 0, 1):
                for k2 in (-1, 0, 1):
                    out.append([b[0] + 360.0 * k0, b[1] + 360.0 * k1, b[2] + 360.0 * k2])
    return out

bones = sorted({n for r in d for n in r["euler"]})
frames = [r["f"] for r in d]
best_all = {}
for bone in bones:
    seq = [r["euler"].get(bone) for r in d]
    if any(s is None for s in seq):
        continue
    O = [cands(v) for v in seq]
    # minimax DP: dp[s] = 最小可达「已发生最大步长」
    dp = [0.0] * len(O[0])
    for i in range(1, len(O)):
        nd = [None] * len(O[i])
        for j, y in enumerate(O[i]):
            bv = None
            for k, x in enumerate(O[i - 1]):
                if dp[k] is None:
                    continue
                st = max(abs(a - b) for a, b in zip(x, y))
                c = max(dp[k], st)
                if bv is None or c < bv:
                    bv = c
            nd[j] = bv
        dp = nd
    best_all[bone] = min(v for v in dp if v is not None)

cur = {}
for i in range(1, len(d)):
    a = d[i - 1]["euler"]; b = d[i]["euler"]
    for n in set(a) | set(b):
        s = max(abs(x - y) for x, y in zip(a.get(n, [0, 0, 0]), b.get(n, [0, 0, 0])))
        if s > cur.get(n, 0.0):
            cur[n] = s
print("D18_DPVERDICT")
for n in sorted(bones, key=lambda k: -cur.get(k, 0.0)):
    c = cur.get(n, 0.0); b2 = best_all.get(n)
    if c > 18.0:
        print("  %-14s now=%7.2f  dp_free=%7.2f  %s"
              % (n, c, b2, "★可免费消除" if (b2 is not None and b2 <= 25.0) else "仍需改轨迹"))
print("  GLOBAL now=%7.2f  dp_free=%7.2f"
      % (max(cur.values()), max(v for v in best_all.values() if v is not None)))
