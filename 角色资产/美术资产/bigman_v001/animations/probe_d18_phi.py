"""D18 判定性探针：对每个超限点，扫描「两帧各自绕骨轴滚转 φ」的组合，
求**可实现的最小欧拉逐分量步长**。

- 若最小值 ≤ 25° ⟹ 那一步是**表示假红**，可以用纯滚转（骨根/骨尖不动）消掉。
- 若最小值 > 25° ⟹ 那一步是**真几何**，只能靠改时间轴/幅度/目标路径，不能靠换写法。

只读：不写任何 blend、不导出、不改门禁。
"""
import os
import sys
import math
import json

os.environ.setdefault("SKIP_RENDER", "1")
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import bpy  # noqa: E402
from mathutils import Matrix, Vector, Euler  # noqa: E402

import anim_getup_b as M      # noqa: E402
import anim_lib as A          # noqa: E402
import anim_jump_start as JS  # noqa: E402
import anim_ultimate_end as UE  # noqa: E402


GRID_STEP = 5.0
PHIS = [math.radians(GRID_STEP * i) for i in range(int(360.0 / GRID_STEP))]


def _twist(rot3, phi):
    cos_p, sin_p = math.cos(phi), math.sin(phi)
    return rot3 @ Matrix(((cos_p, 0.0, sin_p),
                          (0.0, 1.0, 0.0),
                          (-sin_p, 0.0, cos_p)))


def _branches(m):
    out = []
    for cand in UE._xyz_candidates(m):
        out.append([math.degrees(t) for t in cand])
    return out


def _aligned(value, ref):
    v = list(value)
    for i in range(3):
        while v[i] - ref[i] > 180.0:
            v[i] -= 360.0
        while v[i] - ref[i] < -180.0:
            v[i] += 360.0
    return v


def _best_step(rot_a, rot_b, phis=PHIS):
    """两帧各自可绕骨轴滚转 ⟹ 最小可能的欧拉逐分量步长（度），及其 φ。"""
    best, best_pair = None, None
    a_opts = []
    for pa in phis:
        for br in _branches(_twist(rot_a, pa)):
            a_opts.append((pa, br))
    b_opts = []
    for pb in phis:
        for br in _branches(_twist(rot_b, pb)):
            b_opts.append((pb, br))
    # 用一个"共同参考"消 +-360 歧义：先取 b 相对 a 最近的等价写法
    for pa, bv in a_opts:
        for pb, av in b_opts:
            av2 = _aligned(av, bv)
            step = max(abs(x - y) for x, y in zip(bv, av2))
            if best is None or step < best:
                best = step
                best_pair = (round(math.degrees(pa), 1),
                             round(math.degrees(pb), 1),
                             [round(v, 2) for v in av2],
                             [round(v, 2) for v in bv])
    return best, best_pair


def main():
    arm, meshes = M.boot()
    JS._PREV_EULER.clear()
    UE.CARRY_Q.clear()
    A.apply_pose(arm, M.ZERO)
    bpy.context.view_layer.update()
    for name in M.ARM_BONES + M.LEG_BONES:
        UE.CARRY_Q[name] = arm.pose.bones[name].matrix.to_3x3().to_quaternion()
    for name, value in M.ZERO.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)
    M.ZERO_FIST = {s: Vector(A.bone_world(arm, "hand." + s, "tail"))
                   for s in ("L", "R")}

    poses = {}
    for f in range(0, M.TOTAL + 1):
        poses[f] = M.solve_pose(arm, f, meshes)

    # ---- 收集当前门禁下的全部超限点 ----------------------------------------
    offenders = []
    for f in range(1, M.TOTAL + 1):
        names = set(poses[f]) | set(poses[f - 1])
        for name in sorted(names):
            if name.startswith("@"):
                continue
            ea = tuple(poses[f - 1].get(name, (0.0, 0.0, 0.0)))
            eb = tuple(poses[f].get(name, (0.0, 0.0, 0.0)))
            step = max(abs(a - b) for a, b in zip(ea, eb))
            if step > 25.0:
                offenders.append((step, f, name))
    offenders.sort(reverse=True)

    rows = []
    for step, f, name in offenders:
        qa = Euler([math.radians(v) for v in
                    poses[f - 1].get(name, (0.0, 0.0, 0.0))], "XYZ").to_matrix()
        qb = Euler([math.radians(v) for v in
                    poses[f].get(name, (0.0, 0.0, 0.0))], "XYZ").to_matrix()
        bst, pair = _best_step(qa, qb)
        rows.append({"framestep": f, "bone": name, "now": round(step, 3),
                     "best": round(bst, 3) if bst is not None else None,
                     "kind": ("表示可救" if (bst is not None and bst <= 25.0)
                              else "真几何"),
                     "phi": None if pair is None else [pair[0], pair[1]]})
    print("D18_PHISCAN " + json.dumps(rows, ensure_ascii=False))
    for r in rows:
        print("  f%02d %-12s now=%7.3f  best=%7.3f  %s  phi=%s"
              % (r["framestep"], r["bone"], r["now"], r["best"], r["kind"],
                 r["phi"]))


main()
