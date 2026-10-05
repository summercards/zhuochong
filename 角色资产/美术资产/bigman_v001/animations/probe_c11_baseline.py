"""probe_c11_baseline —— 只量不做：为 C11 `Skill_03` 旋转重拳 回答四个问题。

清单 C11 计划 §4「开工顺序」第 2 条要求的四量：

  ① **单脚支撑 + 转体**下的腿可达比许可域 —— 旋转会把髋-踝距离拉长吗？
     （`ik_reach_ok` 是最可能先红的一项；本支的构造是「绕枢轴刚性旋转」，
      理论上髋-踝距离**逐位不变** —— 这条探针就是去证实/证伪它）
  ② **转体时骨盆 z / 水平位移**的许可域（对 `root_motion_ok` 定标）
  ③ 拳能到的**世界域**（定标 `hand_target` 的贴身点与伸展点）
  ④ 支撑脚鞋底顶点的**枢轴漂移**基线（定 `foot_pivot_ok` 的 30 mm 是否现实
     —— **先量再定阈值**）

另外顺手把本支要用的**基础设施**量清楚（不量清楚就会像 C10 那样返工）：

  ★ `root.rotation_euler.y` 到底是不是世界 yaw？
     `rig_axis_map.md` 只说了 `root` 的 Y 轴**末端位移 = 0**（转轴重合）——
     这正是"绕纵轴自转"的特征，但**没有直接证明**它等于绕世界 Z。
     本探针取一个不在轴上的世界点，绕 yaw 转 θ，看它是不是落到
     「绕世界 Z 转 θ」的解析位置上 —— **直接证实/证伪**。
  ★ `root.location` 在**自身旋转之后**是否仍按 `wloc` 的世界语义生效？
     （Blender 的 `matrix_basis = T(loc) @ R` ⟹ loc 应在**未旋转**的 rest 系里。
      若成立，绕枢轴补偿就是一个干净的闭式解，不需要数值迭代。）
  ★ 网格对象名（拳套 / 头组 / 躯干组）—— `silhouette_*` 要用**网格面**量。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python probe_c11_baseline.py
"""

import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A            # noqa: E402
import anim_idle_01 as I1       # noqa: E402
import anim_grab04 as G4        # noqa: E402

SIDES = ("L", "R")
XOFF = {"L": 1.0, "R": -1.0}     # +X = 角色左
PIVOT_SIDE = "R"                 # 支撑脚（后脚）
SWING_SIDE = "L"                 # 摆动脚（前脚）

SEAM_EULER = {}
Z_SEAM = 0.0
ANKLE_0 = {}
ROOT_HEAD = None
PIVOT0 = None                    # 枢轴顶点在 Idle@0 的世界 (x, y, z)
PIVOT_KEY = None                 # (对象名, 顶点号)
EYE = None                       # 明显不在轴上的验证点（world）
IDLE_KNEE_DIR = {}
ARM_LEN = {}


# ---------------------------------------------------------------- 工具
def rot2(x, y, theta_deg):
    c = math.cos(math.radians(theta_deg))
    s = math.sin(math.radians(theta_deg))
    return (x * c - y * s, x * s + y * c)


def rigid(xy, theta_deg):
    """把世界 xy 绕枢轴 `PIVOT0` 刚性转 `theta_deg`（绕竖直轴）。"""
    dx, dy = xy[0] - PIVOT0[0], xy[1] - PIVOT0[1]
    rx, ry = rot2(dx, dy, theta_deg)
    return (PIVOT0[0] + rx, PIVOT0[1] + ry)


def rot_dir(d, theta_deg):
    x, y = rot2(d[0], d[1], theta_deg)
    return (x, y, d[2])


def root_loc(theta_deg, extra=(0.0, 0.0, 0.0)):
    """**绕枢轴补偿**的 root 局部位移。

    推导：`pose.matrix(root) = M0 @ T(loc) @ R(θ)` ⟹ 世界等效 = 先绕
    `ROOT_HEAD` 转 R(θ)、再把原点整体平移 `B0 @ loc`（B0 = root 的 rest 3×3）。
    要让**枢轴顶点** `P0` 不动：

        B0 @ loc = (I − R(θ)) · (P0 − ROOT_HEAD)        （只取 xy）

    `B0^{-1}` 就是 `wloc`（局部 X→世界 X、局部 Y→世界 Z、局部 Z→世界 −Y）。
    """
    dx = PIVOT0[0] - ROOT_HEAD[0]
    dy = PIVOT0[1] - ROOT_HEAD[1]
    rx, ry = rot2(dx, dy, theta_deg)
    wx = dx - rx + extra[0]
    wy = dy - ry + extra[1]
    wz = extra[2]
    return (wx, wz, -wy)


def keep_yaw(arm, name, theta_deg):
    """把骨的**世界朝向**钉成「rest 绕世界 Z 转 θ」—— 支撑脚贴地 + 随体转。

    `A.keep_world_orientation` 是把世界朝向钉回 rest（θ=0）：转体时脚就"不跟体转"
    了（鞋尖永远指同一世界方向）。转体动作必须换成这个版本，否则鞋是"悬浮陀螺"。
    """
    pose_bone = arm.pose.bones[name]
    rest = pose_bone.bone.matrix_local.to_3x3()
    target = (Matrix.Rotation(math.radians(theta_deg), 3, "Z") @ rest).to_4x4()
    target.translation = pose_bone.matrix.translation
    pose_bone.matrix = target
    bpy.context.view_layer.update()
    return tuple(math.degrees(v) for v in pose_bone.rotation_euler)


def foot_vertices(side):
    deps = bpy.context.evaluated_depsgraph_get()
    points = []
    for name in A.FOOT_MESHES[side]:
        obj = bpy.data.objects.get(name)
        if obj is None:
            continue
        evaluated = obj.evaluated_get(deps)
        mesh = evaluated.to_mesh()
        matrix = evaluated.matrix_world
        for vertex in mesh.vertices:
            point = matrix @ vertex.co
            points.append((point.x, point.y, point.z, name, vertex.index))
        evaluated.to_mesh_clear()
    return points


def pivot_vertex(side):
    """鞋底「最前的最低点」顶点（C07 教训 3：别用 AABB 中心，那是 57 mm 伪影）。"""
    points = foot_vertices(side)
    if not points:
        return None
    zmin = min(p[2] for p in points)
    band = [p for p in points if p[2] <= zmin + 2.0]
    front = min(band, key=lambda p: p[1])
    return (front[3], front[4], (front[0], front[1], front[2]))


def vertex_world(key):
    deps = bpy.context.evaluated_depsgraph_get()
    obj = bpy.data.objects.get(key[0])
    if obj is None:
        return None
    evaluated = obj.evaluated_get(deps)
    mesh = evaluated.to_mesh()
    point = evaluated.matrix_world @ mesh.vertices[key[1]].co
    evaluated.to_mesh_clear()
    return (point.x, point.y, point.z)


# ---------------------------------------------------------------- 装配
def setup(arm):
    global SEAM_EULER, Z_SEAM, ANKLE_0, ROOT_HEAD, PIVOT0, PIVOT_KEY, EYE
    global IDLE_KNEE_DIR, ARM_LEN

    src = bpy.data.actions[I1.NAME]
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = src
    A._bind_slot(arm, src)
    bpy.context.scene.frame_set(0)
    bpy.context.view_layer.update()

    SEAM_EULER = {b.name: tuple(math.degrees(v) for v in b.rotation_euler)
                  for b in arm.pose.bones}
    Z_SEAM = A.bone_world(arm, "pelvis", "head").z
    ANKLE_0 = {s: Vector(A.bone_world(arm, "foot." + s, "head")) for s in SIDES}
    ROOT_HEAD = Vector(A.bone_world(arm, "root", "head"))
    name, index, world = pivot_vertex(PIVOT_SIDE)
    PIVOT_KEY = (name, index)
    PIVOT0 = world
    EYE = Vector(A.bone_world(arm, "head", "tail"))

    idle = I1.idle_pose(arm, 0.0)
    A.apply_pose(arm, idle)
    bpy.context.view_layer.update()
    basis, dirs, knee = {}, {}, {}
    for bone in ("thigh.L", "shin.L", "thigh.R", "shin.R",
                 "upperarm.L", "forearm.L", "hand.L",
                 "upperarm.R", "forearm.R", "hand.R"):
        basis[bone] = arm.pose.bones[bone].matrix.to_3x3().copy()
        dirs[bone] = tuple(A.bone_direction(arm, bone))
    for s in SIDES:
        hip = Vector(A.bone_world(arm, "thigh." + s, "head"))
        kn = Vector(A.bone_world(arm, "thigh." + s, "tail"))
        knee[s] = (kn - hip).normalized()
    G4.IDLE_BASIS.clear()
    G4.IDLE_BASIS.update(basis)
    G4.IDLE_DIR.clear()
    G4.IDLE_DIR.update(dirs)
    G4.IDLE_KNEE_DIR.clear()
    G4.IDLE_KNEE_DIR.update(knee)
    IDLE_KNEE_DIR = knee
    G4.ARM_LEN.clear()
    ARM_LEN.clear()
    for s in SIDES:
        ARM_LEN[s] = {
            "upper": arm.pose.bones["upperarm." + s].length,
            "forearm": arm.pose.bones["forearm." + s].length,
            "hand": arm.pose.bones["hand." + s].length}
        G4.ARM_LEN[s] = dict(ARM_LEN[s])

    A.report("C11_PROBE_ANCHOR", {
        "arm_matrix_identity": bool(arm.matrix_world == Matrix.Identity(4)),
        "root_head_mm": [round(v * 1000.0, 3) for v in ROOT_HEAD],
        "pivot_side": PIVOT_SIDE, "swing_side": SWING_SIDE,
        "pivot_key": [PIVOT_KEY[0], PIVOT_KEY[1]],
        "pivot_world_mm": [round(v * 1000.0, 3) for v in PIVOT0],
        "pelvis_z0_mm": round(Z_SEAM * 1000.0, 3),
        "pelvis_xy0_mm": [round(A.bone_world(arm, "pelvis", "head").x * 1000.0, 3),
                          round(A.bone_world(arm, "pelvis", "head").y * 1000.0, 3)],
        "ankle0_mm": {s: [round(v * 1000.0, 2) for v in ANKLE_0[s]]
                      for s in SIDES},
        "eye0_mm": [round(v * 1000.0, 2) for v in EYE],
        "arm_len_mm": {s: {k: round(v * 1000.0, 2) for k, v in d.items()}
                       for s, d in ARM_LEN.items()},
        "shoulder_R_head_mm": [round(v * 1000.0, 2) for v in
                               A.bone_world(arm, "upperarm.R", "head")],
        "hand_R_tail_mm": [round(v * 1000.0, 2) for v in
                           A.bone_world(arm, "hand.R", "tail")],
        "leg_len_mm": round((A.L_THIGH + A.L_SHIN) * 1000.0, 3),
    })


# ---------------------------------------------------------------- ① 轴向证明
def _arc_pose(arm, theta, drop=0.0, extra=(0.0, 0.0, 0.0)):
    """绕枢轴刚性旋转的一整帧姿态（骨盆 + 双腿 IK + 双鞋跟转）。"""
    pose = {"root": (0.0, theta, 0.0),
            "@loc": {"root": root_loc(theta, extra=(extra[0], extra[1],
                                                    extra[2] + drop))}}
    A.apply_pose(arm, pose)
    for s in SIDES:
        xy = rigid((ANKLE_0[s].x, ANKLE_0[s].y), theta)
        G4.leg_seat(arm, pose, s, (xy[0], xy[1], ANKLE_0[s].z),
                    IDLE_KNEE_DIR[s])
    for s in SIDES:
        keep_yaw(arm, "foot." + s, theta)
    return pose


def axis_proof(arm):
    out = {}
    for theta in (0.0, 30.0, 90.0, 180.0):
        A.apply_pose(arm, {"root": (0.0, theta, 0.0),
                           "@loc": {"root": (0.0, 0.0, 0.0)}})
        bpy.context.view_layer.update()
        got = Vector(A.bone_world(arm, "head", "tail"))
        dx, dy = EYE.x - ROOT_HEAD.x, EYE.y - ROOT_HEAD.y
        rx, ry = rot2(dx, dy, theta)
        want = Vector((ROOT_HEAD.x + rx, ROOT_HEAD.y + ry, EYE.z))
        out["yaw_%03d" % int(theta)] = {
            "got_mm": [round(v * 1000.0, 3) for v in got],
            "want_mm": [round(v * 1000.0, 3) for v in want],
            "err_mm": round((got - want).length * 1000.0, 3)}

    for theta in (0.0, 90.0):
        loc = root_loc(theta, extra=(0.0, 0.0, 0.05))
        A.apply_pose(arm, {"root": (0.0, theta, 0.0), "@loc": {"root": loc}})
        bpy.context.view_layer.update()
        got = Vector(A.bone_world(arm, "head", "tail"))
        dx, dy = EYE.x - ROOT_HEAD.x, EYE.y - ROOT_HEAD.y
        rx, ry = rot2(dx, dy, theta)
        want = Vector((ROOT_HEAD.x + rx, ROOT_HEAD.y + ry, EYE.z + 0.05))
        out["loc_yaw_%03d" % int(theta)] = {
            "loc": [round(v, 6) for v in loc],
            "err_mm": round((got - want).length * 1000.0, 3)}

    for theta in (0.0, 90.0, 180.0, 270.0, 360.0):
        _arc_pose(arm, theta)
        bpy.context.view_layer.update()
        got = vertex_world(PIVOT_KEY)
        out["pivot_%03d" % int(theta)] = {
            "got_mm": [round(v * 1000.0, 3) for v in got],
            "drift_mm": round(math.dist(got, PIVOT0) * 1000.0, 4)}
    return out


# ---------------------------------------------------------------- ② 转体可达域
def spin_reach(arm):
    out = {}
    limit = A.L_THIGH + A.L_SHIN
    for theta in (0, 45, 90, 135, 180, 225, 270, 315, 360):
        for drop in (0.0, -0.04, -0.08):
            pose = _arc_pose(arm, float(theta), drop=drop)
            row = {}
            for s in SIDES:
                xy = rigid((ANKLE_0[s].x, ANKLE_0[s].y), float(theta))
                hip = Vector(A.bone_world(arm, "thigh." + s, "head"))
                row["leg_ratio_" + s] = round(
                    (Vector((xy[0], xy[1], ANKLE_0[s].z)) - hip).length / limit, 5)
            low = A.foot_lowest_by_side()
            row["pelvis_mm"] = [round(v * 1000.0, 2)
                                for v in A.bone_world(arm, "pelvis", "head")]
            row["sole_mm"] = {s: (None if low[s] is None
                                  else round(low[s][2] * 1000.0, 2))
                              for s in SIDES}
            out["t%03d_drop%+05.0f" % (theta, drop * 1000.0)] = row

    tuck = {}
    for tz in (0.30, 0.38, 0.46):
        for ty in (-0.20, -0.10, 0.00, 0.10):
            for tx in (0.06, 0.13, 0.20, 0.28):
                pose = _arc_pose(arm, 90.0)
                wx, wy = rigid((tx, ty), 90.0)
                tgt = (wx, wy, tz)
                G4.leg_seat(arm, pose, SWING_SIDE, tgt, IDLE_KNEE_DIR[SWING_SIDE])
                keep_yaw(arm, "foot." + SWING_SIDE, 90.0)
                hip = Vector(A.bone_world(arm, "thigh." + SWING_SIDE, "head"))
                tuck["z%05.2f_y%+05.2f_x%05.2f" % (tz, ty, tx)] = round(
                    (Vector(tgt) - hip).length / limit, 5)
    out["swing_tuck_ratio"] = tuck
    return out


# ---------------------------------------------------------------- ③ 拳的世界域
def hand_reach(arm):
    out = {}
    for theta in (0.0, 90.0, 270.0):
        torso = {"root": (0.0, theta, 0.0), "@loc": {"root": root_loc(theta)},
                 "pelvis": (6.0, 0.0, 0.0), "spine_01": (5.0, 0.0, 0.0),
                 "spine_02": (5.0, 0.0, 0.0), "chest": (8.0, 0.0, 0.0)}
        cand = {}
        for by in (-0.65, -0.55, -0.48, -0.40, -0.30, -0.22, -0.14):
            for bx in (-0.44, -0.36, -0.28, -0.20, -0.12):
                for bz in (1.38, 1.32):
                    wx, wy = rigid((bx, by), theta)
                    A.apply_pose(arm, torso)
                    clamp, dist, lim = G4.arm_seat(
                        arm, torso, "R", (wx, wy, bz),
                        rot_dir((-0.30, 0.0, -0.95), theta), ref=None)
                    cand["x%+05.2f_y%+05.2f_z%05.2f" % (bx, by, bz)] = {
                        "ratio": round(dist / lim, 4), "clamp": bool(clamp)}
        out["theta_%03d" % int(theta)] = cand
    # 左臂（防守手）贴身域
    for bz in (1.24, 1.32, 1.40):
        for by in (-0.30, -0.22, -0.14):
            for bx in (0.06, 0.14, 0.22):
                torso = {"root": (0.0, 0.0, 0.0), "@loc": {"root": root_loc(0.0)},
                         "pelvis": (6.0, 0.0, 0.0), "spine_01": (5.0, 0.0, 0.0),
                         "spine_02": (5.0, 0.0, 0.0), "chest": (8.0, 0.0, 0.0)}
                A.apply_pose(arm, torso)
                clamp, dist, lim = G4.arm_seat(
                    arm, torso, "L", (bx, by, bz), (0.85, 0.1, -0.5), ref=None)
                out.setdefault("guard_L", {})[
                    "x%+05.2f_y%+05.2f_z%05.2f" % (bx, by, bz)] = {
                        "ratio": round(dist / lim, 4), "clamp": bool(clamp)}
    return out


# ---------------------------------------------------------------- ④ 网格对象名
def mesh_names():
    groups = {"glove": [], "sleeve": [], "head": [], "torso": [], "shoe": []}
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        low = obj.name.lower()
        if any(k in low for k in ("glove", "fist", "hand")):
            groups["glove"].append(obj.name)
        if "sleeve" in low:
            groups["sleeve"].append(obj.name)
        if any(k in low for k in ("head", "nose", "hair", "glasses",
                                  "ear", "jaw", "mouth", "eye")):
            groups["head"].append(obj.name)
        if any(k in low for k in ("suit", "shirt", "jacket", "collar",
                                  "lapel", "pocket", "button")):
            groups["torso"].append(obj.name)
        if "shoe" in low:
            groups["shoe"].append(obj.name)
    return {k: sorted(v) for k, v in groups.items()}


def main():
    arm, _meshes = A.open_animation_project()
    A.setup_scene()
    if I1.NAME not in bpy.data.actions:
        I1.main()
        arm, _meshes = A.open_animation_project()
        A.setup_scene()
    setup(arm)

    A.report("C11_BASELINE", {
        "mesh_names": mesh_names(),
        "axis_proof": axis_proof(arm),
        "spin_reach": spin_reach(arm),
        "hand_reach": hand_reach(arm),
    })
    print("C11_PROBE_DONE")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("C11_PROBE_FAILURE " + traceback.format_exc())
