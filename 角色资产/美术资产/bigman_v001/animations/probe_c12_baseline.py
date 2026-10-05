"""probe_c12_baseline —— 只量不做：为 C12 `Ultimate_Start` 大招起手 定标判据。

清单「下一支详细制作计划 —— C12 `Ultimate_Start`」§4「开工顺序」第 2 条要求：

  ① `Idle_01@0` 的**剪影基线**（纵横比 / 填充率 / 包围盒 / 肩宽比 / 头沿 / 重心投影）
     —— 作为 `silhouette_strong_ok` 的**对照组**；
  ② 在"零位移"约束下**骨盆 z 的许可域**（沉多低还能保住 `ground_contact_ok` /
     `leg_reach_ok`）；
  ③ 三种强 Pose 候选（**举拳 / 拉弓 / 沉腰握拳**）各自能达到的剪影指标
     —— **先量再定阈值，不许拍脑袋**。

★ 为什么本支必须新立判据：C11 的门禁（`spin_*` / `foot_pivot_*` / `punch_chain_*`）
  全部撤下，通用项（贴地 / 不滑 / 不跳变）在本支**会全部轻松绿** —— 因为本支
  几乎零位移。门槛失去意义 ⟹ 判据必须重新设计（C12 计划 §1 的"失败模式：
  运动学全绿但什么也没发生"）。

==================== 剪影量怎么算（本探针的口径，后续门禁照抄）

**正视投影**（相机在 −Y，画面横轴 = 世界 X、纵轴 = 世界 Z）：

  · 顶点集 = 全部 MESH 对象的**求值后网格**顶点（含 subsurf），世界化后取 (x, z)；
  · 包围盒 = (max_x−min_x) × (max_z−min_z)；
  · `aspect` = 宽 / 高；
  · `fill` = 投影面积 / 包围盒面积。投影面积用**三角形在 XZ 平面的面积和**
    （`Σ |A_xz|`）—— 这是清单原文「用网格面算…面积／包围盒面积」的字面口径。
    它是**无遮挡**口径（前后重叠会重复计），但对照组与实验组同源 ⟹ 比值仍然可比。
  · 同时报一个**独立口径** `fill_grid`（10 mm 网格占用率，三角形光栅化，
    有遮挡去重）—— 两个口径若给出**同向**结论，说明 `fill` 不是口径伪影。

★ **排除未蒙皮件**：`Jacket_Hem` / `Jacket_Hem_Line`（`parent: null`、钉在世界原点，
  C11 遗留问题）不属于角色剪影。本探针两个口径都排除它们，并在报告里给出
  "含/不含"的差值，证明排除是必要的而不是掩盖。

**重心投影**：取所有网格顶点的**面积加权**质心 (x, y)（不是顶点算术平均 ——
  关节处顶点密、质心会被拽偏）。支撑面 = 双脚"最低 20 mm 带"内顶点的 x/y 包围盒。

**躯干朝向**：`torso_yaw` = `pelvis.ry + spine_01.ry + spine_02.ry + chest.ry`
  （躯干骨 rest 轴都是竖直 +Z ⟹ 各自 `ry` 就是绕世界 Z 的偏航，沿链可加）。
  `head_yaw` = `torso_yaw + neck.ry + head.ry`。
  ★ 不用骨端点算 yaw：`head.tail` 在转轴上会给出"根本没转"的假值（C11 教训）。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python probe_c12_baseline.py
"""

import json
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A            # noqa: E402
import anim_idle_01 as I1       # noqa: E402

SIDES = ("L", "R")
HEM_EXCLUDE = ("Jacket_Hem", "Jacket_Hem_Line")
GRID_MM = 10.0

ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")
TORSO_RY = ("pelvis", "spine_01", "spine_02", "chest")

IDLE_HAND = {}
ANKLE_0 = {}
A_RIG = None


# ---------------------------------------------------------------- 剪影
def _mesh_verts():
    """全部 MESH 的求值顶点（世界 (x, y, z)）。返回 (含 hem, 不含 hem) 两份。"""
    deps = bpy.context.evaluated_depsgraph_get()
    all_pts = []
    keep_pts = []
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        evaluated = obj.evaluated_get(deps)
        mesh = evaluated.to_mesh()
        matrix = evaluated.matrix_world
        for vertex in mesh.vertices:
            point = matrix @ vertex.co
            all_pts.append((point.x, point.y, point.z))
            if obj.name not in HEM_EXCLUDE:
                keep_pts.append((point.x, point.y, point.z))
        evaluated.to_mesh_clear()
    return all_pts, keep_pts


def _mesh_tris():
    """全部 MESH 的求值三角面（世界坐标），排除未蒙皮件。返回 (verts, tris)。"""
    deps = bpy.context.evaluated_depsgraph_get()
    verts = []
    tris = []
    for obj in bpy.data.objects:
        if obj.type != "MESH" or obj.name in HEM_EXCLUDE:
            continue
        evaluated = obj.evaluated_get(deps)
        mesh = evaluated.to_mesh()
        matrix = evaluated.matrix_world
        base = len(verts)
        for vertex in mesh.vertices:
            point = matrix @ vertex.co
            verts.append((point.x, point.y, point.z))
        for poly in mesh.polygons:
            idx = [base + i for i in poly.vertices]
            for k in range(1, len(idx) - 1):
                tris.append((idx[0], idx[k], idx[k + 1]))
        evaluated.to_mesh_clear()
    return verts, tris


def _bbox(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    zs = [p[2] for p in points]
    return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


def _centroid_area_weighted(verts, tris):
    """面积加权质心（世界 xy 用三角形面积加权；z 同）。"""
    total = 0.0
    sx = sy = sz = 0.0
    for i0, i1, i2 in tris:
        a, b, c = verts[i0], verts[i1], verts[i2]
        area = 0.5 * ((b[0] - a[0]) * (c[1] - a[1])
                      - (c[0] - a[0]) * (b[1] - a[1]))
        # 用三维三角形面积（更稳，接近"表面积加权"）
        ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
        vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
        nx = uy * vz - uz * vy
        ny = uz * vx - ux * vz
        nz = ux * vy - uy * vx
        w = 0.5 * math.sqrt(nx * nx + ny * ny + nz * nz)
        total += w
        sx += w * (a[0] + b[0] + c[0]) / 3.0
        sy += w * (a[1] + b[1] + c[1]) / 3.0
        sz += w * (a[2] + b[2] + c[2]) / 3.0
        del area
    if total <= 0.0:
        return (0.0, 0.0, 0.0)
    return (sx / total, sy / total, sz / total)


def _fill_grid(verts, tris, lo, hi, cell=GRID_MM / 1000.0):
    """三角形光栅化占用率（有遮挡去重）：覆盖格数 × cell² / 包围盒面积。"""
    width = hi[0] - lo[0]
    depth = hi[2] - lo[2]
    if width <= 0 or depth <= 0:
        return 0.0, 0, 0, 0
    nx = max(1, int(math.ceil(width / cell)))
    nz = max(1, int(math.ceil(depth / cell)))
    grid = bytearray(nx * nz)

    def cell_of(x, z):
        return (min(nx - 1, max(0, int((x - lo[0]) / cell))),
                min(nz - 1, max(0, int((z - lo[2]) / cell))))

    for i0, i1, i2 in tris:
        p = [verts[i0], verts[i1], verts[i2]]
        umin = min(q[0] for q in p)
        umax = max(q[0] for q in p)
        vmin = min(q[2] for q in p)
        vmax = max(q[2] for q in p)
        i_u0, i_v0 = cell_of(umin, vmin)
        i_u1, i_v1 = cell_of(umax, vmax)
        ax, az = p[0][0], p[0][2]
        bx, bz = p[1][0], p[1][2]
        cx, cz = p[2][0], p[2][2]
        den = (bz - cz) * (ax - cx) + (cx - bx) * (az - cz)
        for iu in range(i_u0, i_u1 + 1):
            u = lo[0] + (iu + 0.5) * cell
            for iv in range(i_v0, i_v1 + 1):
                v = lo[2] + (iv + 0.5) * cell
                if abs(den) < 1e-12:
                    grid[iu * nz + iv] = 1
                    continue
                l1 = ((bz - cz) * (u - cx) + (cx - bx) * (v - cz)) / den
                l2 = ((cz - az) * (u - cx) + (ax - cx) * (v - cz)) / den
                l3 = 1.0 - l1 - l2
                if l1 >= -1e-9 and l2 >= -1e-9 and l3 >= -1e-9:
                    grid[iu * nz + iv] = 1
    filled = sum(grid)
    return (filled * cell * cell / (width * depth), filled, nx, nz)


def _proj_area_xz(verts, tris):
    total = 0.0
    for i0, i1, i2 in tris:
        a, b, c = verts[i0], verts[i1], verts[i2]
        total += abs((b[0] - a[0]) * (c[2] - a[2])
                     - (c[0] - a[0]) * (b[2] - a[2])) * 0.5
    return total


def _support_box():
    """支撑面 = 双脚"最低 20 mm 带"内顶点的 xy 包围盒。"""
    deps = bpy.context.evaluated_depsgraph_get()
    pts = []
    for side in SIDES:
        for name in A.FOOT_MESHES[side]:
            obj = bpy.data.objects.get(name)
            if obj is None:
                continue
            evaluated = obj.evaluated_get(deps)
            mesh = evaluated.to_mesh()
            matrix = evaluated.matrix_world
            for vertex in mesh.vertices:
                point = matrix @ vertex.co
                pts.append((point.x, point.y, point.z))
            evaluated.to_mesh_clear()
    if not pts:
        return None, 0.0
    zmin = min(p[2] for p in pts)
    band = [p for p in pts if p[2] <= zmin + 0.020]
    lo, hi = _bbox(band)
    return (lo, hi), zmin


def silhouette(arm, label):
    all_pts, keep_pts = _mesh_verts()
    verts, tris = _mesh_tris()
    lo_k, hi_k = _bbox(keep_pts)
    lo_a, hi_a = _bbox(all_pts)
    width = hi_k[0] - lo_k[0]
    height = hi_k[2] - lo_k[2]
    area = _proj_area_xz(verts, tris)
    bbox_area = width * height
    fill = area / bbox_area if bbox_area > 0 else 0.0
    fill_grid, filled, nx, nz = _fill_grid(verts, tris, (lo_k[0], lo_k[1], lo_k[2]),
                                           hi_k)
    com = _centroid_area_weighted(verts, tris)
    (slo, shi), zmin = _support_box()

    def ry_sum(names):
        return sum(arm.pose.bones[n].rotation_euler[1] * 180.0 / math.pi
                   for n in names)

    shoulder_x = [A.bone_world(arm, "upperarm." + s, "head").x for s in SIDES]
    shoulder_w = abs(shoulder_x[0] - shoulder_x[1])
    head_top = max(p[2] for p in keep_pts)
    out = {
        "label": label,
        "bbox_m": [[round(v, 4) for v in lo_k], [round(v, 4) for v in hi_k]],
        "bbox_all_m": [[round(v, 4) for v in lo_a], [round(v, 4) for v in hi_a]],
        "width_m": round(width, 4), "height_m": round(height, 4),
        "aspect": round(width / height, 4) if height > 0 else 0.0,
        "proj_area_m2": round(area, 4),
        "fill": round(fill, 4),
        "fill_grid": round(fill_grid, 4),
        "grid": [nx, nz, filled],
        "com_xy_m": [round(com[0], 4), round(com[1], 4)],
        "com_z_m": round(com[2], 4),
        "support_box_m": None if slo is None else
        [[round(v, 4) for v in slo], [round(v, 4) for v in shi]],
        "com_inside_support": None if slo is None else bool(
            slo[0] - 0.02 <= com[0] <= shi[0] + 0.02
            and slo[1] - 0.02 <= com[1] <= shi[1] + 0.02),
        "sole_min_mm": round(zmin * 1000.0, 2),
        "shoulder_width_m": round(shoulder_w, 4),
        "shoulder_over_height": round(shoulder_w / height, 4) if height else 0.0,
        "head_top_offset_mm": round((hi_k[2] - head_top) * 1000.0, 2),
        "torso_yaw_deg": round(math.degrees(ry_sum(TORSO_RY)), 2),
        "head_yaw_deg": round(math.degrees(ry_sum(TORSO_RY + ("neck", "head"))), 2),
        "pelvis_z_mm": round(A.bone_world(arm, "pelvis", "head").z * 1000.0, 2),
    }
    return out


# ---------------------------------------------------------------- 姿态构造
def build(spec):
    """由 spec 构造一整帧姿态（腿 IK 钉原位 + 鞋钉 Idle 朝向 + 臂按方向逆解）。"""
    drop = spec.get("drop", 0.0)
    tilt = spec.get("tilt", I1.PELVIS_TILT)
    abduct = spec.get("abduct", I1.ABDUCT_DEG)
    ankle = spec.get("ankle", (I1.FRONT_ANKLE_Y, I1.BACK_ANKLE_Y))
    hip_z = 0.900 + drop
    thigh_f, bend_f = A.leg_ik(0.0, hip_z, ankle[0], A.Z_ANKLE_REST, tilt_deg=tilt)
    thigh_b, bend_b = A.leg_ik(0.0, hip_z, ankle[1], A.Z_ANKLE_REST, tilt_deg=tilt)
    pose = {
        "pelvis": (tilt, 0.0, 0.0),
        "spine_01": (0.0, 0.0, 0.0),
        "spine_02": (0.0, 0.0, 0.0),
        "chest": (0.0, 0.0, 0.0),
        "neck": (0.0, 0.0, 0.0),
        "head": (0.0, 0.0, 0.0),
        "shoulder.L": (0.0, 0.0, 0.0),
        "shoulder.R": (0.0, 0.0, 0.0),
        "thigh.L": (thigh_f, 0.0, -abduct),
        "shin.L": (bend_f, 0.0, 0.0),
        "foot.L": (0.0, 0.0, 0.0),
        "toe.L": (0.0, 0.0, 0.0),
        "thigh.R": (thigh_b, 0.0, abduct),
        "shin.R": (bend_b, 0.0, 0.0),
        "foot.R": (0.0, 0.0, 0.0),
        "toe.R": (0.0, 0.0, 0.0),
        "@loc": {"pelvis": A.wloc(0.0, 0.0, drop)},
    }
    pose.update(spec.get("torso", {}))
    pose.update(A.FIST)
    return pose, spec.get("arms", {})


def apply(spec):
    pose, arms = build(spec)
    A.apply_pose(A_RIG, pose)
    for side in SIDES:
        pose["foot." + side] = A.keep_world_orientation(A_RIG, "foot." + side)
    for bone, direction in arms.items():
        pose[bone] = A.aim_bone(A_RIG, bone, direction)
    return pose


# ---------------------------------------------------------------- 候选强 Pose
# 方向向量 = 骨长轴的世界朝向（`aim_bone` 口径）。+X = 角色左，+Y = 身后，+Z = 上。
CANDIDATES = {
    # ① 举拳：双拳过顶、胸腔打开、头微微上扬（"力量灌顶"）
    "raise_both": {
        "drop": -0.045,
        "torso": {"spine_01": (-2.0, 0.0, 0.0), "spine_02": (-2.0, 0.0, 0.0),
                  "chest": (-9.0, 0.0, 0.0), "neck": (-8.0, 0.0, 0.0),
                  "head": (6.0, 0.0, 0.0),
                  "shoulder.L": (10.0, 0.0, 0.0), "shoulder.R": (10.0, 0.0, 0.0)},
        "arms": {"upperarm.L": (0.34, -0.28, 0.90),
                 "forearm.L": (0.18, -0.24, 0.95),
                 "hand.L": (0.10, -0.20, 0.97),
                 "upperarm.R": (-0.34, -0.28, 0.90),
                 "forearm.R": (-0.18, -0.24, 0.95),
                 "hand.R": (-0.10, -0.20, 0.97)},
    },
    # ② 拉弓：前手（左）指向目标、后手（右）拉到耳后，躯干后拧、头留在正面
    "bow_draw": {
        "drop": -0.040,
        "torso": {"pelvis": (5.0, -14.0, 0.0),
                  "spine_01": (3.0, -10.0, 0.0), "spine_02": (3.0, -10.0, 0.0),
                  "chest": (2.0, -12.0, 0.0), "neck": (-6.0, 18.0, 0.0),
                  "head": (2.0, 18.0, 0.0),
                  "shoulder.L": (-6.0, 0.0, 0.0), "shoulder.R": (-12.0, 0.0, 0.0)},
        "arms": {"upperarm.L": (0.46, -0.80, -0.38),
                 "forearm.L": (0.28, -0.93, -0.24),
                 "hand.L": (0.20, -0.96, -0.20),
                 "upperarm.R": (-0.30, 0.50, 0.81),
                 "forearm.R": (-0.20, 0.34, 0.92),
                 "hand.R": (-0.14, 0.26, 0.96)},
    },
    # ③ 沉腰握拳：重心压到最低、双拳收在腰侧、肘向后张、身体前压
    "sunk_charge": {
        "drop": -0.095,
        "tilt": 7.0,
        "torso": {"spine_01": (5.0, 0.0, 0.0), "spine_02": (5.0, 0.0, 0.0),
                  "chest": (7.0, 0.0, 0.0), "neck": (-12.0, 0.0, 0.0),
                  "head": (6.0, 0.0, 0.0),
                  "shoulder.L": (-14.0, 0.0, 0.0), "shoulder.R": (-14.0, 0.0, 0.0)},
        "arms": {"upperarm.L": (0.44, 0.30, -0.85),
                 "forearm.L": (0.22, -0.42, -0.88),
                 "hand.L": (0.12, -0.62, -0.78),
                 "upperarm.R": (-0.44, 0.30, -0.85),
                 "forearm.R": (-0.22, -0.42, -0.88),
                 "hand.R": (-0.12, -0.62, -0.78)},
    },
}

# 沉收（anticipation）姿态：用于量 `anticipation_ok` 的可达下限
SINK = {
    "drop": -0.075,
    "tilt": 6.0,
    "torso": {"spine_01": (6.0, 0.0, 0.0), "spine_02": (6.0, 0.0, 0.0),
              "chest": (9.0, 0.0, 0.0), "neck": (-10.0, 0.0, 0.0),
              "head": (4.0, 0.0, 0.0),
              "shoulder.L": (-16.0, 0.0, 0.0), "shoulder.R": (-16.0, 0.0, 0.0)},
    "arms": {"upperarm.L": (0.30, -0.34, -0.89),
             "forearm.L": (-0.30, -0.46, 0.83),
             "hand.L": (-0.18, -0.72, 0.67),
             "upperarm.R": (-0.26, -0.40, -0.88),
             "forearm.R": (0.32, -0.26, 0.91),
             "hand.R": (0.16, -0.62, 0.77)},
}


def main():
    global A_RIG
    arm, _meshes = A.open_animation_project()
    A.setup_scene()
    if I1.NAME not in bpy.data.actions:
        I1.main()
        arm, _meshes = A.open_animation_project()
        A.setup_scene()
    A_RIG = arm

    src = bpy.data.actions[I1.NAME]
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = src
    A._bind_slot(arm, src)
    bpy.context.scene.frame_set(0)
    bpy.context.view_layer.update()
    for side in SIDES:
        IDLE_HAND[side] = tuple(A.bone_world(arm, "hand." + side, "tail"))
        ANKLE_0[side] = tuple(A.bone_world(arm, "foot." + side, "head"))

    out = {"idle_baseline": silhouette(arm, "Idle_01@0"),
           "candidates": {}, "sink": None, "drop_domain": {}}

    for key, spec in CANDIDATES.items():
        apply(spec)
        bpy.context.view_layer.update()
        out["candidates"][key] = silhouette(arm, key)

    apply(SINK)
    bpy.context.view_layer.update()
    out["sink"] = silhouette(arm, "sink")

    # ② 骨盆 z 许可域（零水平位移）：drop 扫描，看鞋底 / 腿可达比
    limit = A.L_THIGH + A.L_SHIN
    for drop in (0.0, -0.02, -0.04, -0.055, -0.070, -0.085, -0.100, -0.115):
        apply({"drop": drop, "tilt": 6.0,
               "torso": {"spine_01": (4.0, 0.0, 0.0),
                         "spine_02": (4.0, 0.0, 0.0),
                         "chest": (6.0, 0.0, 0.0)}, "arms": {}})
        bpy.context.view_layer.update()
        low = A.foot_lowest_by_side()
        row = {"sole_mm": {s: (None if low[s] is None
                               else round(low[s][2] * 1000.0, 2)) for s in SIDES},
               "pelvis_mm": round(A.bone_world(arm, "pelvis", "head").z * 1000.0, 2)}
        for side in SIDES:
            hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
            ankle = Vector(A.bone_world(arm, "foot." + side, "head"))
            row["reach_" + side] = round((ankle - hip).length / limit, 5)
        out["drop_domain"]["%+05.0f" % (drop * 1000.0)] = row

    # 网格规模（决定剪影口径的可行性）
    verts, tris = _mesh_tris()
    out["mesh_scale"] = {"verts": len(verts), "tris": len(tris),
                         "grid_cell_mm": GRID_MM}
    out["hem_delta"] = {
        "bbox_all": out["candidates"]["bow_draw"]["bbox_all_m"],
        "bbox_keep": out["candidates"]["bow_draw"]["bbox_m"]}
    A.report("C12_BASELINE", out)
    print("C12_PROBE_DONE")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("C12_PROBE_FAILURE " + traceback.format_exc())
