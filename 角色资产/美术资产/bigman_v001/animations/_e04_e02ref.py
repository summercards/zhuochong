"""_e04_e02ref —— 只读对照：把 **E02 的 hold 姿态** 原样建出来，
量它的「骨盆下沉 / 膝屈 / 鞋底 z」。目的是解释一个矛盾：

  · `probe_e04_baseline` 的下沉扫描（**不加任何躯干倾斜**）里，
    dz=−80 → sole −1.85、dz=−100 → −2.02。
  · 但 E02 实测 `exh_pelvis_drop_mm = 78.986` 而 `exh_sole_min_mm = −0.992`。

同一台骨架、同样的 `lock_feet`，为什么 E02 沉了 79 mm 鞋底还在 −0.99，
而我的扫描沉 80 mm 就到 −1.85？

★ 本脚本直接调用 `anim_exhausted` 的模块函数，把它的 BENT 姿态**逐位复现**，
   并逐项打印 —— 用事实回答，不猜。
"""
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A          # noqa: E402
import anim_exhausted as E    # noqa: E402


def main():
    A.setup_scene()
    arm, _m = E.boot()   # E02 自己的 boot：建 BASE / BENT / ANCHOR / TARGET
    print("E04_E02REF constants PELVIS_DROP=%s HIP_BACK=%s BEND_DEG=%s"
          % (E.PELVIS_DROP, E.HIP_BACK, E.BEND_DEG))
    print("E04_E02REF BENT_loc=%s BASE_loc=%s"
          % (E.BENT.get("@loc"), E.BASE.get("@loc")))
    for key in ("pelvis", "spine_01", "spine_02", "chest", "neck", "head"):
        print("E04_E02REF BENT[%s]=%s BASE[%s]=%s"
              % (key, E.BENT.get(key), key, E.BASE.get(key)))

    hold = E.BEND_END + 10          # hold 段内一帧（弯腰已到位）
    pose = E.exh_pose(arm, hold)
    A.apply_pose(arm, pose)
    sole = A.foot_lowest_by_side()
    pel = Vector(A.bone_world(arm, "pelvis", "head"))
    knee = {s: round(math.degrees(arm.pose.bones["shin." + s].rotation_euler.x), 2)
            for s in ("L", "R")}
    ank = {s: [round(v * 1000.0, 2)
               for v in Vector(A.bone_world(arm, "foot." + s, "head"))]
           for s in ("L", "R")}
    print("E04_E02REF hold=%d pelvis_z=%.2f pelvis_rx=%.2f knee=%s sole=%s "
          "ankle=%s"
          % (hold, pel.z * 1000.0,
             math.degrees(arm.pose.bones["pelvis"].rotation_euler.x), knee,
             {s: round(sole[s][2] * 1000.0, 2) for s in ("L", "R")}, ank))
    print("E04_E02REF thigh=%s foot=%s"
          % ({s: tuple(round(v, 2) for v in pose.get("thigh." + s, (0, 0, 0)))
              for s in ("L", "R")},
             {s: tuple(round(v, 2) for v in pose.get("foot." + s, (0, 0, 0)))
              for s in ("L", "R")}))
    print("E04_E02REF target=%s anchor=%s"
          % ({s: [round(v * 1000.0, 2) for v in E.TARGET[s]] for s in ("L", "R")},
             {s: [round(v * 1000.0, 2) for v in E.ANCHOR[s]] for s in ("L", "R")}))


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("E04_E02REF_FAILURE " + traceback.format_exc())
