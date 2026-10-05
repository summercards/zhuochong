"""probe_c07_smash —— 只量不做（第二轮）：把「砸下」这一帧的可达域量清楚。

第一轮 `probe_c07_baseline.py` 结论：
  · 高举顶轻松达标（pz 0.83 时拳中点 z ≈ 1999 mm，门禁 1850，余量 ~150 mm）。
  · 砸下**不达标**：pz 0.56、`down_dir` z = −0.866 时拳中点 z = 390.7 mm，
    门禁 `smash_depth_ok` 要求 ≤ 320 ⟹ 差 70 mm。

本轮要回答：
  ① 把手臂方向**转陡**（绕 YZ 平面用单一角 α 参数化：α = 0 竖直向下，
     α 增大则向前倾），拳中点 z 能压到多少？α 该取几？
  ② 拳间距（`fist_gap_mm`）能不能收到「砸地」该有的窄距（目标 ≤ 300 mm，
     免得读成「拍地」）？
  ③ 骨盆要多低？`squat_depth_ok` 只要求 ≤ 640，但太低会读成「跪」。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python probe_c07_smash.py
"""

import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A            # noqa: E402
import probe_c07_baseline as P  # noqa: E402

SIDES = ("L", "R")
ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")


def arm_dirs(alpha_deg, spread_mm_deg=3.0, elbow_bend_deg=6.0):
    """α 从竖直向下起算、向 **前（−y）** 旋转。返回 6 根臂骨的世界方向。

    `spread`：上臂略微外张（让拳不打架）；`elbow_bend`：前臂/手比上臂多前倾
    一点，避免读成一根直棍。
    """
    def unit(v):
        n = math.sqrt(sum(c * c for c in v)) or 1.0
        return tuple(c / n for c in v)

    a = math.radians(alpha_deg)
    b = math.radians(alpha_deg + elbow_bend_deg)
    out = {}
    for side, sx in (("L", 1.0), ("R", -1.0)):
        s = math.radians(spread_mm_deg)
        out["upperarm." + side] = unit((sx * math.sin(s), -math.sin(a), -math.cos(a)))
        out["forearm." + side] = unit((sx * math.sin(s) * 0.6, -math.sin(b), -math.cos(b)))
        out["hand." + side] = unit((sx * math.sin(s) * 0.4, -math.sin(b), -math.cos(b)))
    return out


def main():
    arm = P.setup_idle(arm=None)

    smash_rot = {
        "pelvis": (22.0, 0.0, 0.0), "spine_01": (11.0, 0.0, 0.0),
        "spine_02": (11.0, 0.0, 0.0), "chest": (11.0, 0.0, 0.0),
        "neck": (-14.0, 0.0, 0.0), "head": (-4.0, 0.0, 0.0),
        "shoulder.L": (-6.0, 0.0, 0.0), "shoulder.R": (-6.0, 0.0, 0.0),
    }
    rows = []
    for pz in (0.520, 0.560, 0.600, 0.640):
        for alpha in (0.0, 8.0, 16.0, 24.0, 32.0):
            res = P.solve(arm, smash_rot, pz, arm_dirs(alpha))
            res["pelvis_z_arg"] = pz
            res["alpha_deg"] = alpha
            rows.append(res)
    A.report("C07PROBE_SMASH2", {
        "rows": rows,
        "note": ("门禁：fist_mid_mm[2] <= 320（越陡 α 越小）；"
                 "pelvis_z <= 640；fist_gap 目标 <= 300；"
                 "leg_ratio 越低越安全（<0.95）"),
    })
    print("C07PROBE_SMASH2_DONE")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("C07PROBE_SMASH2_FAILURE " + traceback.format_exc())
