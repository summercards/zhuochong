"""D18 只读探针：对照「欧拉逐分量步长」与「世界朝向真实转动角」。

目的：判定 `no_teleport` 的剩余超限点到底是**真几何**（骨头真的转得快）
还是**表示跳变**（世界朝向没动多少，只是欧拉写法换了参考支/缠角）。

做法：挂钩 `A.sample_animation`，先跑原函数（顺带触发本模块的落键），
再自己逐帧 `frame_set` 读 `pose_bone.matrix.to_quaternion()`（armature 空间，
≈世界），算相邻帧四元数夹角；并把门禁口径的欧拉步长一起打印，做并排对照。
只读：所有会写盘的函数改空操作。
"""
import json
import math
import os
import sys

os.environ.setdefault("SKIP_RENDER", "1")
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import anim_lib as A            # noqa: E402
import bpy                      # noqa: E402

_MOD = os.environ.get("D18_MODULE", "anim_getup_b")
M = __import__(_MOD)
print("D18_WORLDROT 被测模块 = %s" % _MOD)

_DEF = ("hand.R,forearm.R,upperarm.R,hand.L,forearm.L,upperarm.L,"
        "shin.R,shin.L,foot.R,foot.L,thigh.R,thigh.L")
WATCH = tuple(n for n in os.environ.get("D18_WATCH", _DEF).split(",") if n)
F_W0 = int(os.environ.get("D18_WR_F0", "0"))
F_W1 = int(os.environ.get("D18_WR_F1", "10**9".replace("10**9", "999")))

_orig = A.sample_animation


def hooked(arm, action, frame_start, frame_end, meshes=None):
    samples = _orig(arm, action, frame_start, frame_end, meshes)
    scene = bpy.context.scene
    prev = arm.animation_data.action if arm.animation_data else None
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    try:
        A._bind_slot(arm, action)
    except Exception:
        pass
    rot = {}
    loc = {}
    eul = {}
    for frame in range(int(frame_start), int(frame_end) + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        rot[frame] = {n: arm.pose.bones[n].matrix.to_quaternion().normalized()
                      for n in WATCH if n in arm.pose.bones}
        loc[frame] = {n: arm.pose.bones[n].matrix_basis.to_quaternion().normalized()
                      for n in WATCH if n in arm.pose.bones}
        eul[frame] = {n: tuple(math.degrees(v) for v in
                               arm.pose.bones[n].rotation_euler)
                      for n in WATCH if n in arm.pose.bones}
    if prev is not None:
        arm.animation_data.action = prev

    rows = []
    for f in sorted(rot):
        if (f - 1) not in rot:
            continue
        for n in WATCH:
            if n not in rot[f] or n not in rot[f - 1]:
                continue
            ang = math.degrees(rot[f - 1][n].rotation_difference(rot[f][n]).angle)
            lang = math.degrees(loc[f - 1][n].rotation_difference(loc[f][n]).angle)
            ea = eul[f - 1][n]
            eb = eul[f][n]
            estep = max(abs(a - b) for a, b in zip(ea, eb))
            rows.append((round(estep, 3), round(lang, 3), round(ang, 3), f, n,
                         [round(v, 1) for v in ea], [round(v, 1) for v in eb]))
    sel = [r for r in rows if F_W0 <= r[3] <= F_W1]
    sel.sort(reverse=True)
    print("D18_WORLDROT[estep,loc,basis,f,bone,e_prev,e_new] "
          + json.dumps(sel[:30], ensure_ascii=False))
    return samples


A.sample_animation = hooked
for _n in ("save_project", "export_glb", "render_pose_sheet",
           "render_animation_mp4", "render_still"):
    if hasattr(A, _n):
        setattr(A, _n, lambda *a, **k: None)

M.main()
