"""E06 专用探针：**手 vs 躯干「深度口径」标定**。

背景（门禁实测）：站架（`Idle_01@0`）本身在右手侧就有 **3 个非拇指顶点在躯干内、
最深 −4.05 mm** —— 这是**预存缺陷**。而 E06 的 `env` 在 f3 只有 0.036
（姿态 96.4% 还是站架）却报出 **9 个**、最深 −9.12 mm ⟹ 说明站架附近有 ~9 个顶点
**紧贴在胸面上**（±5 mm 内）⟹ 「数个数」在这条判据上是**刀刃型**的（3.6% 的混合
就能再翻 6 个过去），不稳健。

本探针量三种口径，为「改用哪一种」提供实测依据：
  · `nt`        —— 当前口径：体内非拇指顶点**个数**；
  · `deep`      —— 当前口径：非拇指**最深**带符号距离；
  · `n<sta`     —— **候选口径**：比**站架最深（−4.05）更深**的顶点个数（应当为 0）；
  · `n<-10`     —— 绝对下限 −10 mm 之外的顶点个数。

跑法：
  "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" --background \
    --factory-startup --python _e06_probe_depth.py
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
_spec = importlib.util.spec_from_file_location(
    "_vic_dep", os.path.join(HERE, "anim_victory_01.py"))
V = importlib.util.module_from_spec(_spec)
sys.modules["_vic_dep"] = V
_spec.loader.exec_module(V)
A = V.A

LIMIT = float(os.environ.get("E06_DEP_LIMIT", "10.0"))


def _reset():
    for d in (V.LAST_ELBOW, V.LAST_TWIST_ANGLE, V._LAST_FO, V._LAST_HD,
              V.LAST_HAND_X, V.LAST_HAND_FRAME, V.LAST_FOREARM_TWIST):
        d.clear()
    V.MIN_HINT_MARGIN = 1.0


def survey(arm, step=4):
    """返回 {side: (nt, deep, n_lt_station, n_lt_limit, n_total)}。"""
    V.torso_bvh_reset()
    tree = V.torso_bvh()
    out = {}
    for side in V.SIDES:
        sta = V.STATION_PIERCE[side]["deepest_nothumb_mm"]
        pts = V.hand_mesh_points(side, step=step)
        nt = deep = 0
        lt_sta = lt_lim = 0
        deepest = None
        for point, name in pts:
            if name.startswith("Thumb_"):
                continue
            gap = V.signed_to_torso(point)
            if deepest is None or gap < deepest:
                deepest = gap
            if gap < 0.0:
                nt += 1
            if gap < sta - 1e-9:
                lt_sta += 1
            if gap < -LIMIT + 1e-9:
                lt_lim += 1
        out[side] = (nt, None if deepest is None else round(deepest, 2),
                     lt_sta, lt_lim, len(pts))
    return out


def main():
    arm, _meshes = V.boot()
    V.TRACE = False
    print("E06DEP station: L=%s R=%s"
          % (V.STATION_PIERCE["L"]["deepest_nothumb_mm"],
             V.STATION_PIERCE["R"]["deepest_nothumb_mm"]))
    print("E06DEP # frame | L(nt deep n<sta n<lim) | R(nt deep n<sta n<lim)")
    worst = {"L": (0, 1e9, 0, 0), "R": (0, 1e9, 0, 0)}
    _reset()
    for frame in range(V.START, V.END + 1, 3):
        pose = V.victory_pose(arm, frame)
        A.apply_pose(arm, pose)
        row = survey(arm)
        def fmt(side):
            nt, deep, ls, ll, _n = row[side]
            return "%2d %7s %5d %5d" % (nt, deep, ls, ll)
        print("E06DEP %5d | %s | %s" % (frame, fmt("L"), fmt("R")))
        for side in V.SIDES:
            nt, deep, ls, ll, _n = row[side]
            w = worst[side]
            worst[side] = (max(w[0], nt), min(w[1], deep), max(w[2], ls),
                           max(w[3], ll))
    for side in V.SIDES:
        nt, deep, ls, ll = worst[side]
        print("E06DEPW %s nt=%d deep=%.2f n_lt_station=%d n_lt_limit=%d"
              % (side, nt, deep, ls, ll))
    print("E06DEP done")


if __name__ == "__main__":
    main()
