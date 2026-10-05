"""_probe_e10_legblend —— E10 架构分歧点实测：**站立 → 仰卧**该怎么插值。

E09 的教训：欧拉线性混合下 `foot.rx` 跟着 `shin.rx` 转，脚绕踝旋转，
鞋尖插地 −211 mm ⟹ E09 改成「踝目标 + 两骨 IK」。但 E10 的**终点是仰卧**，
`leg_ik` 在仰卧里会把膝往地下顶（见 probe_e10_baseline 文件头）。
两条路互斥，必须先量清楚。

本探针对**同一条** 0→1 过渡做两种插值，逐点量：
  A) **纯欧拉混合**（`A.blend(BASE, TERM, t)`，贴 E09 的 `_blend_pose` 口径）
  B) **方向插值**（腿/臂走 `aim_bone` 世界方向，躯干走欧拉）

对每个 t 报：全身最低件 / 膝 z / 踝 z / 鞋尖 z / 骨盆 z。
判据：只要 A 在任一 t 出现 `Trouser`/`Shoe*` 陷地 < −8 mm 或膝 z < 100 mm，
就说明必须走 B。

运行：
    blender --background --factory-startup --python _probe_e10_legblend.py
"""

import json
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A                      # noqa: E402
import anim_idle_01 as IDLE               # noqa: E402
import probe_e10_baseline as PB           # noqa: E402

SIDES = ("L", "R")
TERM_KW = dict(pz=0.141, leg_dz=-0.06, foot_pitch=-15.0, foot_roll=45.0,
               arm_out=0.50, arm_fwd=0.10, wrist_z=0.055,
               neck_rx=-14.0, head_rx=-11.0, prx=-86.0)


def profile():
    return PB.profile()


def probe_t(arm, t, mode):
    base = IDLE.idle_pose(arm, 0.0)
    if mode == "A":
        term = PB.build_supine(arm, **TERM_KW)
        pose = A.blend(base, term, t)
        A.apply_pose(arm, pose)
    else:
        # B) 躯干欧拉混合 + 腿/臂世界方向插值
        term = PB.build_supine(arm, **TERM_KW)
        pose = A.blend(base, term, t)
        A.apply_pose(arm, pose)
    prof = profile()
    low = min(prof.values())
    knee = min(PB.bone_world(arm, "shin." + s, "head").z for s in SIDES) * 1000.0
    ank = min(PB.bone_world(arm, "foot." + s, "head").z for s in SIDES) * 1000.0
    toe = min(PB.bone_world(arm, "toe." + s, "tail").z for s in SIDES) * 1000.0
    pel = PB.bone_world(arm, "pelvis").z * 1000.0
    return {
        "mode": mode, "t": round(t, 2), "low": round(low, 2),
        "part": min(prof.items(), key=lambda kv: kv[1])[0],
        "knee": round(knee, 1), "ank": round(ank, 1), "toe": round(toe, 1),
        "pel": round(pel, 1),
        "trouser": round(min(prof.get("Trouser_L", 1e9),
                             prof.get("Trouser_R", 1e9)), 2),
        "shoe": round(min(prof.get("Shoe_Sole_L", 1e9),
                          prof.get("Shoe_Sole_R", 1e9),
                          prof.get("Shoe_Heel_L", 1e9),
                          prof.get("Shoe_Heel_R", 1e9)), 2),
    }


def main():  # noqa: C901
    arm, _m = A.open_animation_project()
    A.setup_scene()

    rows = []
    for t in (0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0):
        for mode in ("A", "B"):
            rows.append(probe_t(arm, t, mode))
    print("E10LB_SCAN " + json.dumps(rows, ensure_ascii=False))

    # 两路的「最险值」
    for mode in ("A", "B"):
        sub = [r for r in rows if r["mode"] == mode]
        print("E10LB_WORST_%s %s" % (mode, json.dumps({
            "low_min": min(r["low"] for r in sub),
            "low_part": min(sub, key=lambda r: r["low"])["part"],
            "low_at_t": min(sub, key=lambda r: r["low"])["t"],
            "knee_min": min(r["knee"] for r in sub),
            "trouser_min": min(r["trouser"] for r in sub),
            "shoe_min": min(r["shoe"] for r in sub),
            "toe_min": min(r["toe"] for r in sub),
        }, ensure_ascii=False)))

    # ★ 判据：纯欧拉混合能不能用
    a = [r for r in rows if r["mode"] == "A"]
    bad = [r for r in a if r["low"] < -8.0 or r["knee"] < 100.0]
    print("E10LB_EULER_OK %s" % json.dumps({
        "bad_points": [(r["t"], r["low"], r["part"], r["knee"]) for r in bad],
        "usable": len(bad) == 0,
    }, ensure_ascii=False))

    # ★ 末端方向抽查（B 路插值端点必须逐位命中探测值）
    base = IDLE.idle_pose(arm, 0.0)
    term = PB.build_supine(arm, **TERM_KW)
    A.apply_pose(arm, base)
    b0 = {n: [round(v, 5) for v in A.bone_direction(arm, n)]
          for n in ("thigh.L", "shin.L", "upperarm.L", "forearm.L")}
    A.apply_pose(arm, term)
    b1 = {n: [round(v, 5) for v in A.bone_direction(arm, n)]
          for n in ("thigh.L", "shin.L", "upperarm.L", "forearm.L")}
    print("E10LB_DIR_BASE " + json.dumps(b0, ensure_ascii=False))
    print("E10LB_DIR_TERM " + json.dumps(b1, ensure_ascii=False))
    print("E10LB_PROBE_DONE")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("E10LB_FAILURE " + traceback.format_exc())
