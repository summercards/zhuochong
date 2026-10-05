"""E06 专用探针：**捶点可达高度 + 指节贴合**联合扫描。

回答两件事（都用真网格量，不用公式推断）：
1. `chest_surface` 的**探测点参数**（`CHE_PROBE_X / CHE_PROBE_FWD / POUND_DZ`）
   取什么值时，解出的**胸面点 z** 能到多高（= 捶点高度上限）。
2. `TOUCH_OFF` 取什么值时，`Finger_*` 指节面到躯干的**最小带符号距离**
   落进 `[−10, +8] mm`（贴合且不穿透）。

做法：直接小猴补丁改 `anim_victory_01` 的模块级全局，再调**生产同款**函数
（`chest_surface` / `victory_pose` / `fist_face_gap`）⟹ 读数与门禁同源。

跑法：
  "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" --background \
    --factory-startup --python _e06_probe_site.py
"""
import importlib.util
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
_spec = importlib.util.spec_from_file_location(
    "_vic_site", os.path.join(HERE, "anim_victory_01.py"))
V = importlib.util.module_from_spec(_spec)
sys.modules["_vic_site"] = V
_spec.loader.exec_module(V)
A = V.A

FRAME = int(os.environ.get("E06_PS_F", "26"))
XS = [float(v) for v in os.environ.get(
    "E06_PS_X", "0.060,0.090,0.120,0.150").split(",")]
FWDS = [float(v) for v in os.environ.get(
    "E06_PS_FWD", "0.10,0.20,0.35,0.55").split(",")]
DZS = [float(v) for v in os.environ.get(
    "E06_PS_DZ", "0.020,0.040,0.060,0.085").split(",")]
OFFS = [float(v) for v in os.environ.get(
    "E06_PS_OFF", "0.014,0.018,0.022,0.026").split(",")]


def _reset():
    for d in (V.LAST_ELBOW, V.LAST_TWIST_ANGLE, V._LAST_FO, V._LAST_HD,
              V.LAST_HAND_X, V.LAST_HAND_FRAME, V.LAST_FOREARM_TWIST):
        d.clear()
    V.MIN_HINT_MARGIN = 1.0


def main():
    arm, _meshes = V.boot()
    V.TRACE = False

    print("E06PS # === 一、胸面点可达高度（探针几何 sweep）===")
    print("E06PS # x_mm fwd_m dz_mm | neck_z surf_z | nrm | surf_x")
    base_x, base_fwd, base_dz = V.CHE_PROBE_X, V.CHE_PROBE_FWD, V.POUND_DZ
    _reset()
    pose = V.victory_pose(arm, FRAME)
    A.apply_pose(arm, pose)
    ct = Vector(A.bone_world(arm, "neck", "head"))
    for dz in DZS:
        for fwd in FWDS:
            for x in XS:
                V.CHE_PROBE_X, V.CHE_PROBE_FWD, V.POUND_DZ = x, fwd, dz
                surf, nrm = V.chest_surface(arm, "L")
                print("E06PS %5.1f %5.2f %5.3f | %7.1f %7.1f | "
                      "%6.3f %6.3f %6.3f | %7.1f"
                      % (x * 1000, fwd, dz, ct.z * 1000, surf.z * 1000,
                         nrm.x, nrm.y, nrm.z, surf.x * 1000))
    V.CHE_PROBE_X, V.CHE_PROBE_FWD, V.POUND_DZ = base_x, base_fwd, base_dz

    print("E06PS # === 二、贴合 + 高度联合（整姿 · 真拳面）===")
    print("E06PS # x_mm fwd_m dz_mm off_mm | coreL_z coreL_x | knuckleL_mm"
          " | core_gapL_mm")
    for dz in DZS:
        for x in (0.090, 0.120):
            for off in OFFS:
                V.CHE_PROBE_X, V.POUND_DZ = x, dz
                V.CHE_PROBE_FWD = 0.20
                V.TOUCH_OFF = off
                V.FIST_MIN_CLEAR_MM = off * 1000.0
                _reset()
                pose = V.victory_pose(arm, FRAME)
                A.apply_pose(arm, pose)
                core = Vector(A.bone_world(arm, "hand.L", "tail"))
                kn = V.fist_face_gap("L", step=2)
                gap = V.signed_to_torso(core)
                print("E06PS %5.1f %5.2f %5.3f %5.1f | %8.1f %8.1f | "
                      "%+8.2f | %+8.2f"
                      % (x * 1000, 0.20, dz, off * 1000, core.z * 1000,
                         core.x * 1000, kn, gap))
    V.CHE_PROBE_X, V.CHE_PROBE_FWD, V.POUND_DZ = base_x, base_fwd, base_dz
    V.TOUCH_OFF = 0.031
    V.FIST_MIN_CLEAR_MM = 31.0
    print("E06PS done")


if __name__ == "__main__":
    main()
