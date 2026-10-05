"""E06 专用探针：**f3 手穿躯干**的归因（`victory_hand_no_pierce_ok` 的唯一红点）。

门禁实测：`victory_pierce_nothumb_worst = 9 @ (3, 'R')`、最深 −9.12 mm，
而站架基线（f0）= 3 / −4.05 mm ⟹ 全片**只有 f3 这一个帧**越界。

本探针逐帧拆解 f0~f7 的「非拇指体内顶点数」，并做四组**对照**：
  · `as_is`   —— 原样；
  · `env0`    —— 臂包络恒 0（臂**冻结在站架**）⟹ 只剩「躯干下沉」的影响；
  · `slow`    —— `ARM_UP_AT` 14 → 20（臂起步更晚）⟹ 臂的影响有多大；
  · `dipfwd`  —— 把 `FIST_DIP` 往外前方挪（y −0.330 → −0.400、z 1.095 → 1.150）。

跑法：
  "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" --background \
    --factory-startup --python _e06_probe_dip.py
"""
import importlib.util
import os
import sys

from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
_spec = importlib.util.spec_from_file_location(
    "_vic_dip", os.path.join(HERE, "anim_victory_01.py"))
V = importlib.util.module_from_spec(_spec)
sys.modules["_vic_dip"] = V
_spec.loader.exec_module(V)
A = V.A

FRAMES = [int(v) for v in os.environ.get(
    "E06_DIAG_F", "0,1,2,3,4,5,6,7,8,9,10").split(",")]


def _reset():
    for d in (V.LAST_ELBOW, V.LAST_TWIST_ANGLE, V._LAST_FO, V._LAST_HD,
              V.LAST_HAND_X, V.LAST_HAND_FRAME, V.LAST_FOREARM_TWIST):
        d.clear()
    V.MIN_HINT_MARGIN = 1.0


def sweep(label, arm):
    _reset()
    for frame in FRAMES:
        pose = V.victory_pose(arm, frame)
        A.apply_pose(arm, pose)
        V.torso_bvh_reset()
        tree = V.torso_bvh()
        row = {s: V.hand_mesh_stats(s, tree=tree, step=4) for s in V.SIDES}
        print("E06DIAG %-8s f=%2d  L nt=%2d deep=%7s | R nt=%2d deep=%7s"
              % (label, frame, row["L"]["inside_nothumb"],
                 row["L"]["deepest_nothumb_mm"],
                 row["R"]["inside_nothumb"], row["R"]["deepest_nothumb_mm"]))


def main():
    arm, _meshes = V.boot()
    V.TRACE = False
    orig_env = V.arm_env
    orig_up = V.ARM_UP_AT
    orig_dip = {s: V.FIST_DIP[s].copy() for s in V.SIDES}

    sweep("as_is", arm)

    V.arm_env = lambda frame: 0.0
    sweep("env0", arm)
    V.arm_env = orig_env

    V.ARM_UP_AT = 20
    sweep("slow20", arm)
    V.ARM_UP_AT = orig_up

    for s in V.SIDES:
        px = 1.0 if s == "L" else -1.0
        V.FIST_DIP[s] = Vector((px * 0.300, -0.400, 1.150))
    sweep("dipfwd", arm)
    for s in V.SIDES:
        V.FIST_DIP[s] = orig_dip[s]

    print("E06DIAG done")


if __name__ == "__main__":
    main()
