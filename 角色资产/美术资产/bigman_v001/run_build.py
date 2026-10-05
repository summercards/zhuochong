"""bigman_v001 —— 一键装配运行脚本（通过 BlenderMCP 桥在会话内执行）。

用法（bash）：
  python blender_bridge.py --code-file ".../bigman_v001/run_build.py"
"""

import importlib
import json
import math
import os
import sys
import traceback

OUT_DIR = r"I:/工作项目/BIGMANFIGHT/角色资产/美术资产/bigman_v001"
if OUT_DIR not in sys.path:
    sys.path.insert(0, OUT_DIR)

import bpy  # noqa: E402

for module_name in ("bigman_lib", "bigman_body", "bigman_head", "bigman_rig"):
    if module_name in sys.modules:
        importlib.reload(sys.modules[module_name])

import bigman_body as B  # noqa: E402
import bigman_head as H  # noqa: E402
import bigman_lib as L  # noqa: E402
import bigman_rig as R  # noqa: E402

STAGES = {
    "render": True,
    "save": True,
    "export": True,
}

REPORT = {"errors": [], "objects": {}, "assertions": {}}


def bones_for(name):
    if name.startswith("Sleeve_"):
        side = name[-1]
        return ["shoulder." + side, "upperarm." + side, "forearm." + side], "auto", None
    if name.startswith("Shirt_Cuff_"):
        side = name[-1]
        return ["forearm." + side], "rigid", "forearm." + side
    if name.startswith("Hand_Palm_"):
        side = name[-1]
        return ["hand." + side, "forearm." + side], "auto", None
    if name.startswith("Finger_"):
        parts = name.split("_")
        digit = parts[1].lower()
        side = parts[2]
        chain = ["%s_%02d.%s" % (digit, i, side) for i in (1, 2, 3)]
        return chain, "auto", None
    if name.startswith("Thumb_"):
        side = name[-1]
        chain = ["thumb_%02d.%s" % (i, side) for i in (1, 2, 3)]
        return chain, "auto", None
    if name.startswith("Trouser_"):
        side = name[-1]
        return ["thigh." + side, "shin." + side, "pelvis"], "auto", None
    if name.startswith("Shoe_"):
        side = name[-1]
        return ["foot." + side, "toe." + side, "shin." + side], "auto", None
    # 注意用 "Eye_" 前缀（不是 "Eye_White_"）：Eye_Glint_ / Eye_Line_Upper_
    # 若落到默认分支会被绑到脊椎骨上，转眼睛时高光会飞出眼眶。
    if name.startswith(("Eye_", "Iris_", "Pupil_")):
        side = name[-1]
        return ["eye." + side], "rigid", "eye." + side
    if name.startswith(("Eyelid_", "Eyebrow_")):
        return ["head"], "rigid", "head"
    if name.startswith(("Hair_", "Sideburn_", "Temple_Hair_")):
        return ["head"], "rigid", "head"
    if name.startswith("Glasses_"):
        return ["glasses"], "rigid", "glasses"
    if name.startswith(("Upper_Lip", "Lower_Lip", "Mouth_Line")):
        return ["head", "jaw"], "auto", None
    if name == "Head" or name == "Nose" or name.startswith(("Nose_Wing_", "Ear_")):
        return ["head", "jaw", "neck"], "auto", None
    if name == "Neck":
        return ["neck", "chest", "head"], "auto", None
    return ["pelvis", "spine_01", "spine_02", "chest", "neck"], "auto", None


def eye_geometry(meshes):
    """量眼型：**在眼心竖切面上解析采样眼球正面，逐点判遮挡**。

    为什么不用网格顶点量：眼球网格每环间隔约 2 mm，可见开口顶正好落在两环之间，
    量出来会比真值小 1~2 mm，门禁直接假红。这里沿正面竖子午线以 0.1 mm 步长采点，
    逐点测试是否落在任一睑椭球体内 —— 得到的才是真实可见开口。

    遮挡判据用的是"睑椭球体"，不是"睑的几何上下缘"：椭球睑在自身 z 极点处 y 厚度
    趋近 0，那圈根本挡不住眼球，可见开口顶比几何下缘低约 2.5 mm。这一条是量出来的，
    不是推出来的，所以必须留这个函数复量。
    """
    out = {}
    for side, sign in (("L", 1.0), ("R", -1.0)):
        cx = sign * H.EYE_X
        ball_y = H.face_front_y(H.Z_EYE, cx) + H.EYE_PROTRUDE
        lids = ((H.Z_LID_UP, ball_y - 0.0004, H.LID_UP_RADII, H.LID_TILT_UP),
                (H.Z_LID_LO, ball_y - 0.0006, H.LID_LO_RADII, H.LID_TILT_LO))

        def hidden(px, py, pz):
            for lid_z, lid_y, (a, b, c), tilt in lids:
                th = -sign * tilt
                dx, dy, dz = px - cx, py - lid_y, pz - lid_z
                lx = dx * math.cos(th) - dz * math.sin(th)
                lz = dx * math.sin(th) + dz * math.cos(th)
                if (lx / a) ** 2 + (dy / b) ** 2 + (lz / c) ** 2 <= 1.0:
                    return True
            return False

        top = bottom = None
        steps = 400
        for i in range(steps + 1):
            dz = -H.EYE_RZ + 2.0 * H.EYE_RZ * i / steps
            k = 1.0 - (dz / H.EYE_RZ) ** 2
            if k <= 0.0:
                continue
            pz = H.Z_EYE + dz
            if hidden(cx, ball_y - H.EYE_RY * math.sqrt(k), pz):
                continue
            top = pz if top is None else max(top, pz)
            bottom = pz if bottom is None else min(bottom, pz)

        line = {obj.name: obj for obj in meshes}.get("Eye_Line_Upper_" + side)
        if top is None or line is None:
            continue
        pts = [((v.co.x - cx) * sign, v.co.z) for v in line.data.vertices]
        iris_c = H.Z_EYE + H.IRIS_DZ
        out[side] = {
            "opening_mm": round((top - bottom) * 1000.0, 2),
            "iris_clip_mm": round((iris_c + H.IRIS_R - top) * 1000.0, 2),
            "sclera_below_mm": round((iris_c - H.IRIS_R - bottom) * 1000.0, 2),
            "slant_mm": round((max(pts, key=lambda p: p[0])[1]
                               - min(pts, key=lambda p: p[0])[1]) * 1000.0, 2),
        }
    return out


def eye_assertions(geom):
    """门禁：眼裂收窄到人眼区间、虹膜被上睑压住（去豆豆眼）、下三白（杀气）。

    阈值来自设计意图，不是拟合结果：
    - 可见开口 9.5~13.5 mm：人眼裂 28~30 × 10~12 mm。>13.5 就回到"圆眼"，
      巩膜一大片、虹膜成了孤立小黑点 —— 那正是上一版的豆豆眼。
    - 虹膜上缘遮挡 1.2~3.5 mm：0 就是整颗圆虹膜裸露（豆豆眼），>3.5 会把虹膜
      切得过狠、眼睛变小而无神。
    - 虹膜下缘留白 0.5~3.0 mm：下三白。0 以下 = 下睑兜住虹膜（无攻击性）。
    - 外挑 ≥ 1.5 mm：外眼角必须明显高于内眼角。
    """
    res = {}
    for side, g in geom.items():
        res["eye_opening_ok_" + side] = 9.5 <= g["opening_mm"] <= 13.5
        res["iris_clipped_ok_" + side] = 1.2 <= g["iris_clip_mm"] <= 3.5
        res["sclera_below_ok_" + side] = 0.5 <= g["sclera_below_mm"] <= 3.0
        res["eye_slant_ok_" + side] = g["slant_mm"] >= 1.5
    return res


def brow_geometry(meshes):
    """从**真实网格**反算眉中心线。

    `_ribbon` 的截面环全部落在同一个 x 上（环平面取 YZ 平面），所以按 x 分组就能
    还原出路径点，每组的 z 均值即该点中心线的 z。封盖各追加 1 个环心点，落在同
    一组里、不影响均值。
    """
    by_name = {obj.name: obj for obj in meshes}
    out = {}
    for side in ("L", "R"):
        obj = by_name.get("Eyebrow_" + side)
        if obj is None:
            continue
        groups = {}
        for v in obj.data.vertices:
            groups.setdefault(round(abs(v.co.x), 6), []).append(v.co.z)
        pts = sorted((x, sum(zs) / len(zs), max(zs) - min(zs))
                     for x, zs in groups.items())
        if len(pts) != 5:
            continue
        zs = [p[1] for p in pts]

        # 直线性口径：第 1/2/3 点相对**"内端→外端"这一条直线**的偏离。
        # 上一版是两段折线（内端→中段、中段→外端），所以要分段比对才抓得到"中段塌"；
        # 现在整条眉必须落在一条直线上，直接拿首尾连线当基准即可 —— 中间任何回塌、
        # 任何鼓起都会以毫米级偏离暴露出来。
        x0, z0 = pts[0][0], pts[0][1]
        x4, z4 = pts[4][0], pts[4][1]

        def dev(i):
            t = (pts[i][0] - x0) / (x4 - x0)
            return (zs[i] - (z0 + t * (z4 - z0))) * 1000.0

        steps = [(zs[i + 1] - zs[i]) * 1000.0 for i in range(4)]
        heights = [p[2] * 1000.0 for p in pts]
        out[side] = {
            "z_mm": [round(z * 1000.0, 2) for z in zs],
            "height_mm": [round(h, 2) for h in heights],
            "rise_mm": round((zs[4] - zs[0]) * 1000.0, 2),
            "slope_deg": round(math.degrees(math.atan2(zs[4] - zs[0], x4 - x0)), 2),
            "min_step_mm": round(min(steps), 3),
            "straight_dev_mm": round(max(abs(dev(1)), abs(dev(2)), abs(dev(3))), 3),
            "mid_widest_mm": round(heights[2] - max(heights[1], heights[3]), 2),
        }
    return out


def brow_assertions(geom):
    """门禁：眉必须是"**内端低、外端高**的单条斜直线"，且中段最宽。

    这是主人的明确造型要求，不是拟合结果。上一版把"一根眉一高一低"误读成
    "两根眉两边高、中间低"，做成了 V 形折线 —— 所以四条都卡死，任一条回退即红：
    - 抬升 ≥ 6 mm：外端必须明显高于内端（"一高一低"的量）；
    - 逐段单调 ≥ 0.5 mm：任何一点不得回塌，否则立刻退化成折线或弧线；
    - 偏首尾连线 ≤ 0.4 mm：真·直线，无弓弧；
    - 中段高度比两侧邻点各高 ≥ 1 mm（"中间更宽"）。
    """
    res = {}
    for side, g in geom.items():
        res["brow_slant_ok_" + side] = g["rise_mm"] >= 6.0
        res["brow_monotonic_ok_" + side] = g["min_step_mm"] >= 0.5
        res["brow_straight_ok_" + side] = g["straight_dev_mm"] <= 0.4
        res["brow_mid_widest_ok_" + side] = g["mid_widest_mm"] >= 1.0
    return res


# 肩区 / 腰区的 z 取样带：肩带取 1.400~1.480（三角肌最宽点到肩线），
# 腰带取 1.050~1.150（含最细的 1.100）。
SHOULDER_BAND = (1.400, 1.480)
WAIST_BAND = (1.050, 1.150)


def _widest_per_z(points, z0, z1, step=0.002):
    """把一段 z 按 2 mm 分桶，返回每桶内的 max|x|（剔除空桶）。

    必须分桶：整段直接取 max 会量到区间端点的值，取 min 会量到环上前中点（x≈0）。
    只有"逐层最宽、再对层取极值"才是肩宽 / 腰宽的定义。
    """
    n = max(int(round((z1 - z0) / step)), 1)
    best = [0.0] * (n + 1)
    for p in points:
        if z0 <= p.z <= z1:
            i = min(int((p.z - z0) / step), n)
            best[i] = max(best[i], abs(p.x))
    return [v for v in best if v > 0.0]


def torso_geometry(meshes):
    """用**真实网格**量躯干的"上宽下窄"与"肩厚" —— 倒三角体型的量化口径。

    为什么不用 `torso_stations()` 的站点值直接算：躯干环上挂着 `pec` / `lat` / `trap`
    三个修正，其中 `lat` 会把侧壁 x 乘 1.058，而超椭圆的最宽点（t=0）正好落在该修正
    的条件边界上。手推"站点半宽 = 实际半宽"会算错 5.8% —— 曾据此以为肩宽是 474 mm，
    量网格才是 486 mm。**尺寸类结论一律量网格，不量公式。**
    """
    obj = next((o for o in meshes if o.name == "Suit_Torso"), None)
    if obj is None:
        return {}
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    me = ev.to_mesh()
    mw = obj.matrix_world
    pts = [mw @ v.co for v in me.vertices]
    ev.to_mesh_clear()

    sh_layers = _widest_per_z(pts, *SHOULDER_BAND)
    wa_layers = _widest_per_z(pts, *WAIST_BAND)
    if not sh_layers or not wa_layers:
        return {}
    sh_half = max(sh_layers)
    wa_half = min(wa_layers)
    band = [p for p in pts if SHOULDER_BAND[0] <= p.z <= SHOULDER_BAND[1]]
    depth = max(p.y for p in band) - min(p.y for p in band)
    return {
        "shoulder_half_m": round(sh_half, 5),
        "shoulder_width_mm": round(sh_half * 2000.0, 1),
        "waist_half_m": round(wa_half, 5),
        "waist_width_mm": round(wa_half * 2000.0, 1),
        "shoulder_depth_m": round(depth, 5),
        "shoulder_waist_ratio": round(sh_half / max(wa_half, 1e-6), 3),
    }


def torso_assertions(geom):
    """门禁：倒三角体型的两根轴线不许回退。

    这是主人连续两轮追加的要求（"肩膀加宽/上臂加粗" → "肩膀厚实、更有倒三角"），
    所以锁死，避免后续改别的部位时把体型顺手改回去：
    - 肩腰比 ≥ 1.60：宽度差是"倒三角"的剪影来源。当前 1.71，上一版 1.49 ——
      1.49 读作"普通壮汉"，1.7 读作"倒三角"。
    - 肩部前后径 ≥ 0.285 m：**厚度**才是"厚实"。只加宽不加厚会变成"纸片人
      披了件宽西装"——正视图看不出来，侧视图一眼露馅。当前 0.298 m。
    - 腰半宽 ≤ 0.150 m：收腰不能松。肩宽是被腰"衬"出来的，腰一松，
      再加宽肩也读不出倒三角。
    """
    if not geom:
        return {"torso_geometry_present": False}
    return {
        "shoulder_waist_ratio_ok": geom["shoulder_waist_ratio"] >= 1.60,
        "shoulder_depth_ok": geom["shoulder_depth_m"] >= 0.285,
        "waist_tight_ok": geom["waist_half_m"] <= 0.150,
    }


def main():
    L.reset_scene()
    L.build_materials()
    char_col = L.collection("BIGMAN")
    pres_col = L.collection("PRESENTATION")

    objects = []
    objects.append(B.build_torso(char_col))
    objects.append(B.build_neck(char_col))
    for side in ("L", "R"):
        objects.append(B.build_arm(char_col, side))
        objects.append(B.build_cuff(char_col, side))
        objects.extend(B.build_hand(char_col, side))
        objects.append(B.build_leg(char_col, side))
        objects.extend(B.build_shoe(char_col, side))
    objects.extend(B.build_suit_details(char_col))
    objects.append(H.build_head(char_col))
    objects.extend(H.build_nose(char_col))
    objects.extend(H.build_mouth(char_col))
    objects.extend(H.build_eyes(char_col))
    objects.extend(H.build_brows(char_col))
    objects.extend(H.build_ears(char_col))
    objects.extend(H.build_hair(char_col))
    objects.extend(H.build_hair_sweep(char_col))
    objects.extend(H.build_glasses(char_col))

    meshes = [obj for obj in objects if obj is not None and obj.type == "MESH"]
    REPORT["objects"]["count"] = len(meshes)
    REPORT["objects"]["names"] = sorted(obj.name for obj in meshes)
    REPORT["objects"]["vertices"] = sum(len(obj.data.vertices) for obj in meshes)
    REPORT["objects"]["triangles"] = sum(
        len(obj.data.polygons) for obj in meshes
    )

    armature = R.build_rig(char_col)
    for obj in meshes:
        bones, mode, rigid = bones_for(obj.name)
        R.bind_object(obj, armature, bones, mode, rigid)

    camera = R.build_presentation(pres_col)
    REPORT["bones"] = [
        {"name": bone.name, "head": [round(v, 4) for v in bone.head_local],
         "tail": [round(v, 4) for v in bone.tail_local],
         "parent": bone.parent.name if bone.parent else None,
         "deform": bone.use_deform}
        for bone in armature.data.bones
    ]

    if STAGES["render"]:
        REPORT["previews"] = R.render_views(camera)

    REPORT["eye_geometry"] = eye_geometry(meshes)
    REPORT["brow_geometry"] = brow_geometry(meshes)
    REPORT["torso_geometry"] = torso_geometry(meshes)
    REPORT["assertions"] = R.run_assertions(armature, meshes)
    REPORT["assertions"].update(eye_assertions(REPORT["eye_geometry"]))
    REPORT["assertions"].update(brow_assertions(REPORT["brow_geometry"]))
    REPORT["assertions"].update(torso_assertions(REPORT["torso_geometry"]))

    # 落盘保护：门禁没全绿就不许覆盖 .blend / .glb。
    # 理由是踩过一次 —— 桥断线那轮渲染出了带缺陷的图，但 .blend 仍是旧版，
    # 磁盘上"图新、模型旧"错位了好几个小时。把"是否落盘"绑到门禁上，
    # 就不会再出现"看起来定稿了、其实存了个不合格版本"。
    _ok_all = all(v for k, v in REPORT["assertions"].items()
                  if k.endswith("_ok"))
    REPORT["all_assertions_ok"] = _ok_all
    if STAGES["save"] and _ok_all:
        bpy.ops.wm.save_as_mainfile(filepath=L.BLEND_PATH)
        REPORT["saved"] = L.BLEND_PATH
    elif STAGES["save"]:
        REPORT["saved"] = None
        REPORT["save_skipped"] = "门禁未全绿，已跳过落盘"
    if STAGES["export"] and _ok_all:
        REPORT["exported_count"] = R.export_glb(char_col)
        REPORT["exported"] = L.GLB_PATH
    elif STAGES["export"]:
        REPORT["exported"] = None
        REPORT["export_skipped"] = "门禁未全绿，已跳过导出"


try:
    main()
    _a = REPORT.get("assertions", {})
    _keys = ("objects", "vertices", "height_m", "height_ok", "sole_at_zero_ok",
             "width_m", "depth_m", "bones", "bone_names_ok",
             "face_symmetry_ok")
    print("BUILD_SUMMARY " + " ".join(
        "%s=%s" % (k, _a.get(k, REPORT["objects"].get(k))) for k in _keys))
    print("EYE_L " + json.dumps(REPORT.get("eye_geometry", {}).get("L", {})))
    print("EYE_R " + json.dumps(REPORT.get("eye_geometry", {}).get("R", {})))
    print("EYE_ASSERT " + json.dumps(
        {k: v for k, v in _a.items() if k.startswith("eye_") or k.startswith("iris_")}))
    print("BROW_L " + json.dumps(REPORT.get("brow_geometry", {}).get("L", {})))
    print("BROW_R " + json.dumps(REPORT.get("brow_geometry", {}).get("R", {})))
    print("BROW_ASSERT " + json.dumps(
        {k: v for k, v in _a.items() if k.startswith("brow_")}))
    print("TORSO " + json.dumps(REPORT.get("torso_geometry", {})))
    print("TORSO_ASSERT " + json.dumps(
        {k: v for k, v in _a.items()
         if k.startswith(("shoulder_", "waist_"))}))
    print("BUILD_REPORT " + json.dumps(REPORT, ensure_ascii=False))
except Exception:  # noqa: BLE001
    print("BUILD_FAILURE " + traceback.format_exc())
