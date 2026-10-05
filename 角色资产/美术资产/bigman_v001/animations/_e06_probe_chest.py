"""E06 专用探针：**胸面剖面实测**。

回答：「捶点（拳心 z）最高能到多少？」—— 用真网格量，不用公式推断。

做法：在**捶击命中姿态**（f=POUND1 的躯干）下，从前方向躯干投一组探针点
（x 横向若干档 × z 纵向若干档），逐点取 `closest_point_on_mesh` 的
**表面点 + 外法线**，打印表。据此选 `CHE_PROBE_X / POUND_DZ`。

跑法：
  "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" --background \
    --factory-startup --python _e06_probe_chest.py
"""
import importlib.util
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
_spec = importlib.util.spec_from_file_location(
    "_vic_chest", os.path.join(HERE, "anim_victory_01.py"))
V = importlib.util.module_from_spec(_spec)
sys.modules["_vic_chest"] = V
_spec.loader.exec_module(V)
A = V.A

FRAME = int(os.environ.get("E06_PC_F", "26"))
XS = [float(v) for v in os.environ.get(
    "E06_PC_X", "0.05,0.08,0.11,0.135,0.16").split(",")]
ZS = [int(v) for v in os.environ.get(
    "E06_PC_Z", "1180,1200,1220,1240,1260,1280,1300,1320").split(",")]


def main():
    arm, _meshes = V.boot()
    V.TRACE = False
    pose = V.victory_pose(arm, FRAME)
    A.apply_pose(arm, pose)
    ev, mw = V._torso_eval()
    inv = mw.inverted()
    ct = Vector(A.bone_world(arm, "neck", "head"))
    ch = Vector(A.bone_world(arm, "chest", "head"))
    print("E06PC neck_head=[%.1f,%.1f,%.1f] chest_head=[%.1f,%.1f,%.1f]"
          % (ct.x * 1000, ct.y * 1000, ct.z * 1000,
             ch.x * 1000, ch.y * 1000, ch.z * 1000))
    print("E06PC # x_mm  y_probe_mm  z_mm | surf_x surf_y surf_z | nrm |"
          " gap_to_probe_mm")
    y_probe = ct.y - 0.55
    for z in ZS:
        for x in XS:
            probe = Vector((x, y_probe, z / 1000.0))
            _ok, loc, nrm, _idx = ev.closest_point_on_mesh(inv @ probe)
            wloc = mw @ loc
            wnrm = (mw.to_3x3() @ nrm).normalized()
            gap = (probe - wloc).length * 1000.0
            print("E06PC %5.1f %8.1f %6d | %7.1f %7.1f %7.1f | "
                  "%6.3f %6.3f %6.3f | %7.1f"
                  % (x * 1000, y_probe * 1000, z,
                     wloc.x * 1000, wloc.y * 1000, wloc.z * 1000,
                     wnrm.x, wnrm.y, wnrm.z, gap))
    # 再报一次：躯干盒（确认表面范围）
    print("E06PC done")


if __name__ == "__main__":
    main()
