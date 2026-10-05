"""E02 诊断 2：**定量**判明「臂 euler 的大数值（−2867° / 8381°）到底怎么进 Action 的」。

三个假设，一次跑清：
  H1  `aim_bone` 返回的就是原值，`apply_pose` / `rotation_euler` setter 不改；
  H2  setter 会折回 [−180,180)；
  H3  `keyframe_insert` / fcurve 求值会改。

输出：
  (1) aim_bone 返回值 → 读回 rotation_euler → matrix_basis.to_euler() 三者对比
  (2) 直接写 8381.89° 后读回
  (3) 打好 Action 后：forearm.R / upperarm.R 的 fcurve 关键帧实际值（度）
      与 `sample_animation` 读到的 euler（度）逐帧并排
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("SKIP_RENDER", "1")

import bpy  # noqa: E402

import anim_lib as A            # noqa: E402
import anim_exhausted as EX     # noqa: E402


def deg3(e):
    return [round(math.degrees(v), 3) for v in e]


def main():  # noqa: C901
    arm, meshes = EX.boot()
    pb = arm.pose.bones["forearm.R"]

    print("D2_1 aim_bone_roundtrip")
    ret = A.aim_bone(arm, "forearm.R", (-0.32, -0.40, 0.86))
    print("  rotation_mode   =", pb.rotation_mode)
    print("  aim_bone_return =", [round(v, 3) for v in ret])
    print("  read_back_euler =", deg3(pb.rotation_euler))
    print("  matrix_basis_eul=", deg3(pb.matrix_basis.to_euler("XYZ")))

    print("D2_2 set_huge")
    pb.rotation_euler = (math.radians(8381.89), math.radians(-509.94),
                         math.radians(-1407.09))
    print("  read_back       =", deg3(pb.rotation_euler))

    print("D2_3 build_action_fcurve")
    keyframes = [(f, EX.exh_pose(arm, f)) for f in range(EX.START, EX.END + 1)]
    action, _meta = A.build_action(arm, "__D2_PROBE__", keyframes, {})
    paths = {}
    for fc in action.fcurves:
        paths.setdefault(fc.data_path, {})[fc.array_index] = fc
    want = {0: "upperarm.R", 1: "forearm.R", 2: "hand.R"}
    for idx, bone in want.items():
        path = 'pose.bones["%s"].rotation_euler' % bone
        fcs = paths.get(path)
        print("  %s fcurves=%s" % (bone, "MISSING" if not fcs else "ok"))
        if not fcs:
            continue
        for comp in range(3):
            fc = fcs[comp]
            vals = {int(k.co[0]): round(math.degrees(k.co[1]), 2)
                    for k in fc.keyframe_points}
            sample = {f: vals.get(f) for f in
                      list(range(0, 6)) + list(range(20, 26))
                      + list(range(96, 101)) + [112, 113, 114, 118, 119, 120]}
            print("    comp%d %s" % (comp, sample))

    print("D2_4 sample_animation_euler")
    samples = A.sample_animation(arm, action, EX.START, EX.END, meshes)
    for f in list(range(0, 6)) + list(range(20, 26)) + [112, 113, 114, 120]:
        e = samples[f]["euler"].get("forearm.R")
        print("  f=%3d forearm.R=%s" % (f, None if e is None
                                        else [round(v, 2) for v in e]))
    bpy.data.actions.remove(action)


if __name__ == "__main__":
    main()
