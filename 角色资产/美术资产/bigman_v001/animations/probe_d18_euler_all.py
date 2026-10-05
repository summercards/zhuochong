"""D18 只读探针：把 `solve_pose` 解出的**全部帧 × 全部骨骼**的局部 `rotation_euler`
（度，`XYZ` 序）整份落盘，供离线做「等价表示」求解。

为什么需要它
------------
`anim_lib.sample_animation()` 的行 517 记录的是 **`pose_bone.rotation_euler`** ——
也就是**局部欧拉三元组本体**，不是世界姿态。而门禁 `no_teleport` 的尺子
（`anim_lib.py:569-581`）量的是**相邻两帧该三元组的逐分量最大差**。

同一个 3×3 旋转矩阵有无穷多种等价欧拉写法：
  · 换支（branch）：`XYZ` 序下每个矩阵有 2 组解；
  · ±360 缠绕：`(x+360k, y+360m, z+360n)`。
两者写出来的**矩阵逐位相同** ⟹ 世界姿态不变、其他所有判据不变 ⟹
**这是完全免费、可直接落盘的表示自由度**。

`probe_d18_phi.py`（另一实例）允许对每根骨**绕自身轴滚转 φ**——那会改变
后代骨的世界朝向，**不是**纯表示自由度；它的 `best` 不能直接当成「可免改落地」。

本探针**不做任何求解/优化**，只负责把原始数据完整导出。
只读：不写 blend、不导出、不改门禁。
"""
import os
import sys
import json

os.environ.setdefault("SKIP_RENDER", "1")
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import anim_getup_b as M        # noqa: E402
import anim_lib as A            # noqa: E402
import anim_jump_start as JS    # noqa: E402
import anim_ultimate_end as UE  # noqa: E402


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

    rows = []
    for f in range(0, M.TOTAL + 1):
        pose = M.solve_pose(arm, f, meshes)
        rows.append({k: [round(v, 9) for v in val]
                     for k, val in pose.items() if not k.startswith("@")})

    print("D18_TOTAL %d" % M.TOTAL)
    print("D18_EULER_ALL " + json.dumps(rows, ensure_ascii=False))


main()
