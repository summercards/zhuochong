"""probe_up07_arm —— B07 专用：量**攻击臂（后手 R）的「肩→腕 相对几何」**。

问：`UP07_ARM_REQ` 显示 f18/f19/f20 的请求距离只有 **84.6 / 67.7 / 97.1 mm**
    （折叠极限 104 mm、`FOLD_MIN_RATIO` 夹到 176.6 mm）。
    `FIST_TRACK` 的 chamber(拳在髋高) → strike(拳过顶) 在**世界偏移空间**里是一条
    **直线**；而同一时间**肩**在跟着骨盆**前送 135 mm + 上升**。
    ⟹ 拳**相对肩**的位移 = 世界位移 − 肩位移，两者一减，拳在 f18~f21 会**贴到肩上**。

本探针只回答一件事：**逐帧把「肩→腕」这个相对向量量出来**，
看清是"拳没走够"还是"肩追上去把拳吞了"。

输出（米/毫米混排，字段带单位后缀）：
  c            动作时钟
  shoulder_mm  `upperarm.R` head 世界坐标
  fist_mm      拳峰世界目标（= `I1_FIST_GUARD.R` + `chain3(FIST_TRACK.R, c)`）
  rel_mm       拳峰 − 肩（**相对几何**，本探针的主角）
  wrist_mm     腕目标 = 拳峰 − 手骨朝向 × 手骨长
  req_mm       |肩→腕目标|
  pelvis_mm    骨盆世界坐标（看肩是不是被前送拽着走）
  shoulder_move_mm  肩相对 f0 的位移
"""

import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A          # noqa: E402
import anim_idle_01 as I1     # noqa: E402
import anim_uppercut as U     # noqa: E402


def setup(arm):
    U.IDLE_POSE = I1.idle_pose(arm, 0.0)
    U.ANKLE_REST = {s: Vector(A.bone_world(arm, "foot." + s, "head"))
                    for s in U.SIDES}
    U.POLE_LEG = {s: U._leg_pole_from_pose(arm, s) for s in U.SIDES}
    U.POLE_ARM = {s: U._elbow_pole_from_pose(arm, s) for s in U.SIDES}
    U.HAND_GUARD = {s: tuple(A.bone_direction(arm, "hand." + s))
                    for s in U.SIDES}
    fist_guard = {s: Vector(A.bone_world(arm, "hand." + s, "tail"))
                  for s in U.SIDES}
    U.I1_FIST_GUARD = {s: tuple(fist_guard[s]) for s in U.SIDES}


def mm(v):
    return [round(x * 1000.0, 1) for x in v]


def main():
    arm, _ = A.open_animation_project()
    A.setup_scene()
    setup(arm)

    hand_len = U.bone_len(arm, "hand.R")
    rel0 = None
    rows = []
    for c in range(0, 34):
        pose = U.trunk_pose(c)
        pose["toe.L"] = (0.0, 0.0, 0.0)
        pose["toe.R"] = (0.0, 0.0, 0.0)
        pose["@loc"] = {"pelvis": A.wloc(U.chain6(*U.PELVIS_DX, c),
                                         U.chain6(*U.PELVIS_DY, c),
                                         U.DROP + U.chain6(*U.PELVIS_DZ, c))}
        pose.update(A.FIST)
        A.apply_pose(arm, pose)
        bpy.context.view_layer.update()

        shoulder = Vector(A.bone_world(arm, "upperarm.R", "head"))
        fist = U.fist_target("R", c)
        want = U.hand_dir("R", c)
        wrist = fist - want * hand_len
        rel = fist - shoulder
        if rel0 is None:
            rel0 = rel.copy()
        rows.append({
            "c": c,
            "shoulder_mm": mm(shoulder),
            "fist_mm": mm(fist),
            "rel_mm": mm(rel),
            "wrist_mm": mm(wrist),
            "req_mm": round((wrist - shoulder).length * 1000.0, 1),
            "pelvis_mm": mm(Vector(A.bone_world(arm, "pelvis", "head"))),
        })

    base = Vector(rows[0]["shoulder_mm"]) / 1000.0
    for row in rows:
        row["shoulder_move_mm"] = mm(Vector(row["shoulder_mm"]) / 1000.0 - base)
        row["rel_delta_from_guard_mm"] = mm(
            Vector(row["rel_mm"]) / 1000.0 - rel0)

    A.report("UP07_ARM_GEOM", {
        "hand_len_mm": round(hand_len * 1000.0, 2),
        "fold_limit_mm": round((U.bone_len(arm, "upperarm.R")
                                + U.bone_len(arm, "forearm.R")) * 1000.0, 2),
        "rows": rows,
        "note": "`rel_mm` = 拳峰 − 肩（相对几何）。它若在 f18~f21 掉到 ~100 mm，"
                "说明拳被**肩追上来吞掉**了，不是拳没走。",
    })


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("UP07_ARM_PROBE_FAILURE " + traceback.format_exc())
