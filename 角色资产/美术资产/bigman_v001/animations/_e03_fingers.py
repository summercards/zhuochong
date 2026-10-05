"""手指骨驱动排查：`A.FIST` 的键到底对不对得上骨架里的骨骼名。

打印：
  · 骨架里名字含 index/middle/ring/pinky/thumb 的**全部骨骼**
  · `A.FIST` 的**全部键**
  · 两者的交集 / 差集（差集 = 写了但没生效的键）
  · f=28 时这些骨骼的 rotation_euler 实际值（= 0 就说明没驱动）

用法：
  blender -b --factory-startup -P _e03_fingers.py
"""
import os
import sys
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import anim_rage as R  # noqa: E402
import anim_lib as A  # noqa: E402

arm, meshes = R.boot()

keys = sorted(k for k in arm.pose.bones.keys())
fingers = [k for k in keys
           if any(t in k.lower() for t in ("index", "middle", "ring",
                                           "pinky", "thumb", "fing"))]
print("=" * 78)
print("骨架含手指语义的骨骼（%d 个）：" % len(fingers))
for k in fingers:
    print("   %s" % k)
print("-" * 78)
print("A.FIST 的键（%d 个）：" % len(A.FIST))
for k in sorted(A.FIST):
    print("   %s -> %s" % (k, A.FIST[k]))
print("-" * 78)
fk = set(A.FIST)
sk = set(fingers)
print("交集（真的会生效）：%s" % sorted(fk & sk))
print("★ 写了但骨架里没有（静默失效）：%s" % sorted(fk - sk))
print("★ 骨架里有但没写：%s" % sorted(sk - fk))
print("-" * 78)
print("全骨架骨骼名（供比对）：")
print("   " + ", ".join(keys))

print("=" * 78)
pose = R.rage_pose(arm, 28)
A.apply_pose(arm, pose)
bpy.context.view_layer.update()
print("f=28 手指骨实际 rotation_euler（度）：")
for k in fingers:
    e = [math.degrees(v) for v in arm.pose.bones[k].rotation_euler]
    print("   %-24s (%+8.2f %+8.2f %+8.2f)" % (k, e[0], e[1], e[2]))
print("-" * 78)
print("f=28 手网格对象名：")
for obj in bpy.data.objects:
    if obj.type == "MESH" and any(obj.name.startswith(p)
                                  for p in R.HAND_PREFIX):
        print("   %s" % obj.name)
print("E03_FINGERS_DONE")
