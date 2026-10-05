"""probe_c03_baseline —— C03 `Knockdown_Attack` 开工第一探针（**只读，不写任何资产**）。

清单对 C03 的要求：「攻击力量方向向下或横向，适合把敌人打倒」。
C03 详细计划（`doc/动画制作清单.md` 尾部）要求先量三件事，本探针一次量完：

① **C 族同向先例的真值** —— `Combo_Finish`（C01，双拳过顶**向下**劈砸）的
   「打击点世界 z 净下降」与「前向（世界 −y）行程占比」。C03 的两条专属阈值
   按它的 **1.10~1.20 倍** 定，比率登记进 `amplitude_baseline`。
   同时把 `Launcher`（C02，**向上**）拉来当**反向对照**：它的 z 净变化应为负
   （上升），若量出来也是"下降"就说明口径写错了。

② **两个候选上游接缝的真值** —— `Heavy_01@CANCEL(36)`（C01/C02 都用过）
   与 `Combo_Finish@CANCEL(40)`。两条都量出骨盆/双踝/髋踝距，**按站姿宽度选**：
   "横向下劈"要一记能蹬地下压的**宽站架**，站姿越宽越吃力越好看。

③ **C01 的逐帧 z 曲线** —— 判"净下降"到底发生在哪一段，避免把后摇的回收
   也算进"打击行程"（C01 日志第 2 件的教训：时序峰值必须限定在发力窗口内）。

口径全部**世界系**（root motion 只沿 y，不污染 z；前向另报骨盆系做对照）。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python probe_c03_baseline.py
"""

import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402
import anim_lib as A  # noqa: E402

# (名字, ANTIC, HIT) —— 从各自脚本的帧预算读出
CASES = (("Combo_Finish", 15, 30), ("Launcher", 18, 30))
HANDS = ("hand.R", "hand.L")


def rows_of(arm, action):
    scene = bpy.context.scene
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    start, end = action.frame_range
    rows = []
    for frame in range(int(round(start)), int(round(end)) + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        row = {"f": frame,
               "pelvis": Vector(A.bone_world(arm, "pelvis", "head"))}
        for hand in HANDS:
            row[hand] = Vector(A.bone_world(arm, hand, "tail"))
        rows.append(row)
    return rows


def strike_metrics(rows, antic, hit):
    """打击窗口 [antic, hit] 的三个量：z 净变化 / 前向行程 / 路径长。

    取**两只手里行程更大的那只**当"打击手"（C01 是双拳，C02 是后手）。
    每个量都报**世界系**与**骨盆系**两套：世界系是世界空间里真的走了多远
    （root motion 只沿 y，所以 z 的量不受污染）；骨盆系是"相对身体发力的量"。
    """
    seg = [r for r in rows if antic <= r["f"] <= hit]
    out = {"window": [antic, hit]}
    for hand in HANDS:
        world = [r[hand] for r in seg]
        rel = [r[hand] - r["pelvis"] for r in seg]
        path_w = sum((world[i + 1] - world[i]).length
                     for i in range(len(world) - 1)) * 1000.0
        path_r = sum((rel[i + 1] - rel[i]).length
                     for i in range(len(rel) - 1)) * 1000.0
        dz_w = (world[0].z - world[-1].z) * 1000.0    # >0 = 净下降
        dy_w = (world[0].y - world[-1].y) * 1000.0    # >0 = 净前移（−y）
        dz_r = (rel[0].z - rel[-1].z) * 1000.0
        dy_r = (rel[0].y - rel[-1].y) * 1000.0
        out[hand] = {
            "z_drop_world_mm": round(dz_w, 2),
            "fwd_world_mm": round(dy_w, 2),
            "path_world_mm": round(path_w, 2),
            "down_dom_world": round(dz_w / path_w, 4) if path_w > 1e-6 else 0.0,
            "fwd_dom_world": round(dy_w / path_w, 4) if path_w > 1e-6 else 0.0,
            "z_drop_rel_mm": round(dz_r, 2),
            "fwd_rel_mm": round(dy_r, 2),
            "path_rel_mm": round(path_r, 2),
            "down_dom_rel": round(dz_r / path_r, 4) if path_r > 1e-6 else 0.0,
            "fwd_dom_rel": round(dy_r / path_r, 4) if path_r > 1e-6 else 0.0,
            "z_start_mm": round(world[0].z * 1000.0, 2),
            "z_end_mm": round(world[-1].z * 1000.0, 2),
        }
    return out


def seam_of(arm, action, frame, label):
    scene = bpy.context.scene
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    pel = Vector(A.bone_world(arm, "pelvis", "head"))
    out = {"label": label, "action": action.name, "frame": frame,
           "pelvis_mm": [round(v * 1000.0, 2) for v in pel]}
    for side in ("L", "R"):
        ank = Vector(A.bone_world(arm, "foot." + side, "head"))
        hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
        out["ankle_" + side + "_mm"] = [round(v * 1000.0, 2) for v in ank]
        out["relative_" + side + "_mm"] = round((pel.y - ank.y) * 1000.0, 2)
        out["abs_relative_" + side + "_mm"] = round(abs(ank.y - pel.y) * 1000.0, 2)
        out["reach_" + side + "_mm"] = round((ank - hip).length * 1000.0, 2)
    out["stance_width_mm"] = round(abs(
        Vector(A.bone_world(arm, "foot.L", "head")).y
        - Vector(A.bone_world(arm, "foot.R", "head")).y) * 1000.0, 2)
    return out


def main():
    arm, _meshes = A.open_animation_project()
    A.setup_scene()

    for name, antic, hit in CASES:
        action = bpy.data.actions.get(name)
        if action is None:
            A.report("C03_PROBE", {"name": name, "error": "action 不存在"})
            continue
        rows = rows_of(arm, action)
        metrics = strike_metrics(rows, antic, hit)
        metrics["name"] = name
        metrics["pelvis_advance_mm"] = round(
            (rows[-1]["pelvis"].y - rows[0]["pelvis"].y) * 1000.0, 2)
        A.report("C03_PROBE", metrics)
        if name == "Combo_Finish":
            print("C03_ZCURVE " + json.dumps(
                [{"f": r["f"],
                  "R": round(r["hand.R"].z * 1000.0, 1),
                  "L": round(r["hand.L"].z * 1000.0, 1)}
                 for r in rows], ensure_ascii=False))

    # ---- 两个候选上游接缝
    heavy = bpy.data.actions.get("Heavy_01")
    combo = bpy.data.actions.get("Combo_Finish")
    idle = bpy.data.actions.get("Idle_01")
    seams = []
    if heavy is not None:
        seams.append(seam_of(arm, heavy, 36, "Heavy_01@36"))
    if combo is not None:
        seams.append(seam_of(arm, combo, 40, "Combo_Finish@40"))
    for item in seams:
        A.report("C03_SEAM", item)
    if idle is not None:
        A.report("C03_SEAM", seam_of(arm, idle, 0, "Idle_01@0"))


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("C03_PROBE_FAILURE " + traceback.format_exc())
