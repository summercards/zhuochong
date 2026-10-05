"""E06 专用探针：**臂折叠窗口的逐帧步长**（`no_teleport` / `matrix_step` 的快速猎手）。

只跑「建帧 + compat + 打 Action + 逐帧量步长」，**不跑**捶胸几何 / 穿模 / 脚锁
⟹ 比整条门禁快数倍，专供扫 `FACE_IN0 / FACE_IN1 / DIP / TWIST_SPLIT`。

读数口径与门禁**逐位一致**：
  · euler 步 = `_worst_step`（键上姿态，等价于 Action 上逐帧读数）；
  · 矩阵步 = `pose_bone.matrix.to_3x3()` 三个列的**最大夹角**（门禁 ⑭ 同款）。

跑法（可带 env 覆盖）：
  E06_FACE_IN0=2 ... "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
    --background --factory-startup --python _e06_probe_fold.py
"""
import importlib.util
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
_spec = importlib.util.spec_from_file_location(
    "_vic_fold", os.path.join(HERE, "anim_victory_01.py"))
V = importlib.util.module_from_spec(_spec)
sys.modules["_vic_fold"] = V
_spec.loader.exec_module(V)
A = V.A

WATCH = int(os.environ.get("E06_FOLD_LO", "6"))
WATCH_HI = int(os.environ.get("E06_FOLD_HI", "36"))


def _euler_step(pa, pb):
    worst, at = 0.0, None
    for name in set(pa) | set(pb):
        if name.startswith("@"):
            continue
        va = pa.get(name, (0.0, 0.0, 0.0))
        vb = pb.get(name, (0.0, 0.0, 0.0))
        if not isinstance(va, tuple) or not isinstance(vb, tuple):
            continue
        for x, y in zip(va, vb):
            d = abs(x - y)
            if d > worst:
                worst, at = d, name
    return worst, at


def main():
    arm, _meshes = V.boot()
    V.TRACE = False
    kfs = [(f, V.victory_pose(arm, f)) for f in range(V.START, V.END + 1)]
    kfs = V.compat_euler(kfs)
    kfs = V.seam_canonicalize(kfs)
    action, _meta = A.build_action(arm, V.NAME, kfs, {})

    worst_e, worst_e_at = 0.0, None
    for i in range(1, len(kfs)):
        s, at = _euler_step(kfs[i - 1][1], kfs[i][1])
        if s > worst_e:
            worst_e, worst_e_at = s, (kfs[i][0], at)
        if WATCH <= kfs[i][0] <= WATCH_HI:
            print("E06F_E f=%3d eul=%7.2f %s" % (kfs[i][0], s, at))

    arm.animation_data.action = action
    A._bind_slot(arm, action)
    scene = bpy.context.scene
    prev = None
    worst_m, worst_m_at = 0.0, None
    for frame in range(V.START, V.END + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        cur = {n: arm.pose.bones[n].matrix.to_3x3().copy()
               for n in arm.pose.bones.keys()}
        if prev is not None:
            fm, fm_at = 0.0, None
            for name in set(cur) & set(prev):
                a, b = prev[name], cur[name]
                for c in range(3):
                    va = a.col[c].normalized()
                    vb = b.col[c].normalized()
                    deg = math.degrees(math.acos(max(-1.0, min(
                        1.0, va.dot(vb)))))
                    if deg > fm:
                        fm, fm_at = deg, name
                    if deg > worst_m:
                        worst_m, worst_m_at = deg, (frame, name)
            if WATCH <= frame <= WATCH_HI:
                print("E06F_M f=%3d mat=%7.2f %s" % (frame, fm, fm_at))
        prev = cur

    print("E06FOLD face_in=%s dip=%d twist=%.2f | eul=%.3f @ %s | "
          "mat=%.3f @ %s"
          % (V.FACE_RAMP_IN, V.DIP, V.TWIST_SPLIT, worst_e, worst_e_at,
             worst_m, worst_m_at))


if __name__ == "__main__":
    main()
