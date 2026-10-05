"""_probe_e10_arm —— 定位 `no_teleport` 在 f17 报 25.868°（`forearm.R`）的原因。

`no_teleport` 的载体 = **每骨 euler 通道**单帧最大变化（`sample_animation` 记录
`pose_bone.rotation_euler`）。手臂这段走的是 `aim_bone`（**最小旋转**解），
所以 euler 未必与「方向变化」同量级：父链一滚，子骨的 euler 就要反向补偿。

本探针不动门禁，只逐帧打印 f8~f30 的：
  ① `death_pose` 返回的 euler 三元组（= 会被写进 action 的值）；
  ② 该骨的**世界朝向**（判断到底是方向在跳还是纯 euler 分支在跳）。
"""
import json
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A       # noqa: E402
import anim_death as D     # noqa: E402

BONES = ("upperarm.R", "forearm.R", "hand.R",
         "upperarm.L", "forearm.L", "hand.L")


def main():
    arm, _meshes = D.boot()
    prev = {}
    for frame in range(8, 31):
        pose = D.death_pose(arm, frame)
        row = {"f": frame,
               "ars": round(D.arm_rise_env(frame), 3),
               "afs": round(D.arm_fall_env(frame), 3)}
        for b in BONES:
            e = tuple(round(v, 3) for v in pose.get(b, (0.0, 0.0, 0.0)))
            d = Vector(A.bone_direction(arm, b))
            row[b] = [e, [round(v, 4) for v in d]]
        if prev:
            worst = []
            for b in BONES:
                ea = prev[b][0]
                eb = row[b][0]
                step = max(abs(x - y) for x, y in zip(ea, eb))
                da, db = Vector(prev[b][1]), Vector(row[b][1])
                ang = da.angle(db)
                worst.append([b, round(step, 3),
                              round(ang * 180.0 / 3.141592653589793, 3)])
            row["step"] = worst
        prev = {b: row[b] for b in BONES}
        print("E10ARM " + json.dumps(row, ensure_ascii=False))
    print("E10ARM_DONE")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("E10ARM_FAILURE " + traceback.format_exc())
