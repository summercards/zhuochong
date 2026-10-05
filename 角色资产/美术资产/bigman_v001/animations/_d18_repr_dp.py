"""D18 离线：求「纯表示自由度」下 `no_teleport` 读数的**严格下界**。

自由度（两者都**逐位保持同一个 3x3 矩阵** ⟹ 世界姿态不变、其他判据不变）
------------------------------------------------------------------------
1. **换支**：`XYZ` 序（Blender 的 `Rz·Ry·Rx`）下，每个旋转矩阵有 2 组欧拉解。
2. **±360 缠绕**：`Rz(z-360k)·Ry(y-360m)·Rx(x-360n)` 与 `Rz(z)Ry(y)Rx(x)` 逐位相同
   （每个因子各自是独立旋转矩阵）⟹ x/y/z 三个角可**各自**独立加减 360 的整数倍。

门禁 `no_teleport` 量的是 `pose_bone.rotation_euler` 相邻帧的**逐分量最大差**
（`anim_lib.py:569-581`）⟹ 上面两条恰好是它的**零代价自由度**。

求解（精确，无二分）
--------------------
每根骨**互相独立**（改一根骨的欧拉写法不影响别的骨的读数）⟹
  全局下界 = `max over 骨 (单骨下界)`。
单骨用 bottleneck DP：
  `dp[f][c] = min over p∈C[f-1] of max(dp[f-1][p], step(p, c))`，`dp[0][*] = 0`
  下界 = `min over c∈C[N-1] of dp[N-1][c]`
复杂度 `O(N·|C|²)`，一次算完，精确。

自检
----
先用**原样写法**复算基线最大步长，必须复现门禁日志里的值（本支 28.558）。
复现不出来就说明矩阵约定/骨骼取舍口径错了，结果不可信。

纯离线：不 import bpy、不读 blend、不写任何生产文件（只写一个 `.witness.json`）。
"""
import json
import math
import sys


# ---------------------------------------------------------------- 3x3 线性代数
def _mm(A, B):
    return tuple(tuple(sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3))
                 for i in range(3))


def _rot(rx, ry, rz):
    """Blender `'XYZ'` = `Rz·Ry·Rx`（已用 `Euler((90,90,0),'XYZ').to_matrix()` 实测定标）。"""
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    Rx = ((1, 0, 0), (0, cx, -sx), (0, sx, cx))
    Ry = ((cy, 0, sy), (0, 1, 0), (-sy, 0, cy))
    Rz = ((cz, -sz, 0), (sz, cz, 0), (0, 0, 1))
    return _mm(Rz, _mm(Ry, Rx))


def _mat_of(triple):
    return _rot(*[math.radians(v) for v in triple])


# ---------------------------------------------------- 等价欧拉写法（矩阵 -> 三元组）
def _clamp(v, lo=-1.0, hi=1.0):
    return max(lo, min(hi, v))


def _branches(M):
    """该矩阵在 `Rz·Ry·Rx` 序下的全部欧拉解（弧度）。"""
    out = []
    s = _clamp(-M[2][0])                      # M[2][0] = -sin(y)
    y1 = math.asin(s)
    out.append((math.atan2(M[2][1], M[2][2]), y1, math.atan2(M[1][0], M[0][0])))
    if abs(abs(s) - 1.0) > 1e-12:             # 非万向锁：第二支存在
        y2 = math.copysign(math.pi, y1) - y1
        out.append((math.atan2(-M[2][1], -M[2][2]), y2,
                    math.atan2(-M[1][0], -M[0][0])))
    return out


def candidates(triple, span=1):
    """该三元组对应的全部等价写法（度）。span=1 ⟹ 每角 ±360 各一次。"""
    M = _mat_of(triple)
    cands = set()
    for br in _branches(M):
        base = [math.degrees(v) for v in br]
        for kx in range(-span, span + 1):
            for ky in range(-span, span + 1):
                for kz in range(-span, span + 1):
                    cands.add((round(base[0] + 360.0 * kx, 6),
                               round(base[1] + 360.0 * ky, 6),
                               round(base[2] + 360.0 * kz, 6)))
    cands.add(tuple(round(v, 6) for v in triple))     # 兜底：原写法必在集合内
    return sorted(cands)


def step(a, b):
    return max(abs(x - y) for x, y in zip(a, b))


# ------------------------------------------------------------------ 单骨 DP
def best_for_bone(seq, span=1):
    """bottleneck DP：返回 (下界 T, 取值序列)。"""
    C = [candidates(t, span) for t in seq]
    n = len(C)
    dp = [0.0] * len(C[0])
    prev_choice = []
    for f in range(1, n):
        ndp = [float("inf")] * len(C[f])
        ch = [0] * len(C[f])
        for ci, c in enumerate(C[f]):
            best, arg = float("inf"), 0
            for pi, p in enumerate(C[f - 1]):
                v = dp[pi] if dp[pi] > (s := step(p, c)) else s
                if v < best:
                    best, arg = v, pi
            ndp[ci], ch[ci] = best, arg
        prev_choice.append(ch)
        dp = ndp
    end = min(range(len(dp)), key=lambda i: dp[i])
    T = dp[end]
    path = [None] * n
    path[n - 1] = C[n - 1][end]
    for f in range(n - 1, 0, -1):
        end = prev_choice[f - 1][end]
        path[f - 1] = C[f - 1][end]
    return T, path


def baseline(seqs, nframe):
    best, at = 0.0, None
    for b, s in seqs.items():
        for f in range(1, nframe):
            v = step(s[f - 1], s[f])
            if v > best:
                best, at = v, (f, b)
    return best, at


# ---------------------------------------------------------------------- 主流程
def main():
    path = sys.argv[1]
    span = 1
    for a in sys.argv[2:]:
        if a.startswith("--span="):
            span = int(a.split("=")[1])
    text = open(path, encoding="utf-8", errors="replace").read()
    if text.lstrip()[:1] == "[":                       # 门禁 samples JSON
        rows = json.loads(text)
        raw = [r["euler"] for r in rows]
        print("输入 = 门禁 samples（%d 帧，首帧 f=%s）" % (len(raw), rows[0]["f"]))
    else:                                              # `D18_EULER_ALL` 行
        at = text.index("D18_EULER_ALL ")
        raw = json.loads(text[at + len("D18_EULER_ALL "):].split("\n")[0])
        print("输入 = D18_EULER_ALL（%d 帧）" % len(raw))

    nframe = len(raw)
    bones = sorted({b for row in raw for b in row})
    seqs = {b: [tuple(row.get(b, (0.0, 0.0, 0.0))) for row in raw] for b in bones}

    base_max, base_at = baseline(seqs, nframe)
    print("BASELINE 复算 max_step = %.3f @ %s   (帧 %d, 骨 %d, span %d)"
          % (base_max, base_at, nframe, len(bones), span))

    cache = {b: best_for_bone(seqs[b], span) for b in bones}
    rows = sorted(((T, b) for b, (T, _) in cache.items()), reverse=True)

    print("\n=== 单骨下界 Top 20（纯表示自由度可达的最小峰值步长，度/帧）===")
    for T, b in rows[:20]:
        print("  %-14s T_min = %7.3f" % (b, T))
    print("\n全局下界 T* = %.3f  （位于 %s）" % (rows[0][0], rows[0][1]))
    print("下界仍 > 25 的骨数：%d / %d"
          % (sum(1 for T, _ in rows if T > 25.0 + 1e-6), len(rows)))

    witness = {b: cache[b][1] for b in bones}
    worst, worst_at = 0.0, None
    for b, s in witness.items():
        for f in range(1, nframe):
            v = step(s[f - 1], s[f])
            if v > worst:
                worst, worst_at = v, (f, b)
    print("witness 全体骨实测最大步长 = %.3f @ %s" % (worst, worst_at))

    out = path + ".witness.json"
    json.dump({"baseline": base_max, "T_min_global": rows[0][0],
               "witness_worst": worst,
               "per_bone_Tmin": {b: round(T, 6) for T, b in rows},
               "witness": {b: [[round(v, 6) for v in t] for t in s]
                           for b, s in witness.items()}},
              open(out, "w", encoding="utf-8"), ensure_ascii=False)
    print("witness 已落盘 -> %s" % out)


main()
