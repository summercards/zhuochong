"""把两侧手网格顶点投到**各自 hand 骨的局部坐标系**里比对。

要回答：L/R 两只手的**网格**在骨骼局部空间里是
  (a) 逐位镜像（x 取反）—— 那么世界里的差异只可能来自骨架构型/胸几何；
  (b) 逐位相同 —— 那么「手性是靠摆放补的」，两侧的世界几何必然不同。

做法：`p_local = pose_bone.matrix.inverted() @ p_world`（armature 空间）再乘
`bone.matrix_local` 的逆 —— 直接用它给出的矩阵即可；这里用
`arm.pose.bones[b].matrix.inverted()`（armature 空间 → 骨空间），
armature 空间与世界只差一个对象矩阵（这里对象矩阵接近单位）。

打印：
  · 每个网格对象（Hand_Palm_? / Finger_*_? / Thumb_*）在局部空间的质心
  · 两侧**全套**顶点的局部包围盒
  · 两侧局部质心数组逐项对比（L 原样 vs R **x 取反**后的差）

用法：
  blender -b --factory-startup -P _e03_local.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import anim_rage as R  # noqa: E402
import anim_lib as A  # noqa: E402

arm, meshes = R.boot()
pose = R.rage_pose(arm, 28)
A.apply_pose(arm, pose)
bpy.context.view_layer.update()

deps = bpy.context.evaluated_depsgraph_get()


def local_points(side):
    bone = arm.pose.bones["hand." + side]
    # pose_bone.matrix: 骨空间 → armature 空间。取逆得 armature → 骨空间。
    inv = bone.matrix.inverted()
    out = []
    for obj in bpy.data.objects:
        if obj.type != "MESH" or not obj.name.endswith("_" + side):
            continue
        if not any(obj.name.startswith(p) for p in R.HAND_PREFIX):
            continue
        ev = obj.evaluated_get(deps)
        me = ev.to_mesh()
        mw = ev.matrix_world
        # 先回 armature 空间（对象矩阵的逆），再进骨空间
        obj_inv = arm.matrix_world.inverted()
        pts = [inv @ (obj_inv @ (mw @ v.co)) for v in me.vertices]
        ev.to_mesh_clear()
        out.append((obj.name, pts))
    return out


data = {s: local_points(s) for s in R.SIDES}
print("=" * 78)
for side in R.SIDES:
    allpts = [p for _n, pts in data[side] for p in pts]
    mn = Vector((min(p.x for p in allpts), min(p.y for p in allpts),
                 min(p.z for p in allpts)))
    mx = Vector((max(p.x for p in allpts), max(p.y for p in allpts),
                 max(p.z for p in allpts)))
    cen = sum(allpts, Vector((0, 0, 0))) / float(len(allpts))
    print("[%s] 局部包围盒 min=(%+.4f %+.4f %+.4f) max=(%+.4f %+.4f %+.4f)"
          % (side, mn.x, mn.y, mn.z, mx.x, mx.y, mx.z))
    print("     局部质心=(%+.4f %+.4f %+.4f)  顶点数=%d"
          % (cen.x, cen.y, cen.z, len(allpts)))

print("-" * 78)
print("逐对象局部质心（左 vs 右，右按 x 取反后比）")
dl = {n: sum(p, Vector((0, 0, 0))) / float(len(p)) for n, p in data["L"]}
dr = {n: sum(p, Vector((0, 0, 0))) / float(len(p)) for n, p in data["R"]}


def key_of(name):
    base = name.rsplit("_", 1)[0]
    return base


rl = {}
rr = {}
for name, c in dl.items():
    rl[key_of(name)] = c
for name, c in dr.items():
    rr[key_of(name)] = c
for base in sorted(set(rl) | set(rr)):
    a = rl.get(base)
    b = rr.get(base)
    if a is None or b is None:
        print("  %-24s %s" % (base, "缺一侧"))
        continue
    bm = Vector((-b.x, b.y, b.z))
    print("  %-24s L=(%+.4f %+.4f %+.4f)  R*=(%+.4f %+.4f %+.4f)  "
          "|Δ|=%7.3f mm"
          % (base, a.x, a.y, a.z, bm.x, bm.y, bm.z, (a - bm).length * 1000.0))

print("-" * 78)
# 局部空间里「指节面」沿 -y 的极值（拳在骨空间里朝哪）
for side in R.SIDES:
    pts = [p for _n, ps in data[side] for p in ps
           if not _n.startswith("Thumb_")]
    lo = min(pts, key=lambda p: p.y)
    hi = max(pts, key=lambda p: p.y)
    print("[%s] 指节簇局部 y 极值: min=%+.4f  max=%+.4f  跨度=%.1f mm"
          % (side, lo.y, hi.y, (hi.y - lo.y) * 1000.0))
print("E03_LOCAL_DONE")
