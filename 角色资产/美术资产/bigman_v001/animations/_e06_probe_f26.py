"""E06 专用探针：**IK 落点自证**。

只回答三个问题，全部用实测数字：
  ① 骨长到底是多少（`forearm` / `hand`）—— 不信常量，量它；
  ② `victory_pose(f)` 解出来的拳心（`hand.tail`）离**瞄点**差多少、差在哪；
  ③ 这个差是不是「被 action 打帧过程弄丢的」（对比 pose 口径与 action 口径）。

跑法：
  "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" --background \
    --factory-startup --python _e06_probe_f26.py
"""
import importlib.util
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
_spec = importlib.util.spec_from_file_location(
    "_vic_probe", os.path.join(HERE, "anim_victory_01.py"))
V = importlib.util.module_from_spec(_spec)
sys.modules["_vic_probe"] = V
_spec.loader.exec_module(V)
A = V.A

FRAMES = [int(x) for x in os.environ.get("E06_PF", "14,20,26,40,54,72").split(",")]


def mm(v):
    return [round(c * 1000.0, 2) for c in v]


def main():
    arm, _meshes = V.boot()
    print("E06P_KN = %.6f  E06P_FO = %.6f  E06P_HD = %.6f"
          % (V.ARM_LEN_UP, V.FOREARM_LEN, V.HAND_LEN))
    for side in ("L", "R"):
        fo_h = Vector(A.bone_world(arm, "forearm." + side, "head"))
        fo_t = Vector(A.bone_world(arm, "forearm." + side, "tail"))
        hd_h = Vector(A.bone_world(arm, "hand." + side, "head"))
        hd_t = Vector(A.bone_world(arm, "hand." + side, "tail"))
        print("E06P_LEN %s upperarm=%.6f forearm=%.6f hand=%.6f "
              "wrist_join_gap=%.6f"
              % (side,
                 (Vector(A.bone_world(arm, "upperarm." + side, "head"))
                  - Vector(A.bone_world(arm, "upperarm." + side, "tail"))
                  ).length,
                 (fo_h - fo_t).length, (hd_h - hd_t).length,
                 (fo_t - hd_h).length))

    V.SITE_TRACE = True
    V.IK_TRACE = True
    for frame in FRAMES:
        V.LAST_ELBOW = {}
        V.LAST_TWIST_ANGLE = {}
        pose = V.victory_pose(arm, frame)
        A.apply_pose(arm, pose)
        # 瞄点（在不改场景的前提下算一次）
        spec = V.torso_at(frame)
        _dy, _dz = spec["loc"]
        root = Vector((0.0, _dy, _dz))
        tgt = V.fist_targets(arm, frame, root)
        for side in ("L", "R"):
            A.apply_pose(arm, pose)
            core = Vector(A.bone_world(arm, "hand." + side, "tail"))
            want = Vector(tgt[side])
            d = core - want
            print("E06P_MISS f=%3d %s core=%s want=%s d=%s |d|=%.2fmm"
                  % (frame, side, mm(core), mm(want), mm(d), d.length * 1000.0))
            print("E06P_EUL f=%3d %s pose_eul=%s"
                  % (frame, side,
                     tuple(round(v, 3) for v in pose["hand." + side])))


if __name__ == "__main__":
    main()
