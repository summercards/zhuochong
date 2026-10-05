"""probe_c11_axis —— 只回答一个问题：`root.rotation_euler.y` 是不是世界 yaw？

上一版 `probe_c11_baseline.py` 的 axis_proof **测点选在轴上**（rest 位姿的
`head.tail = (0,0,1790)` 恰好落在 root 头顶的竖直轴上）⟹ θ=0/30/90/180 得到
完全相同的 `got`，**无法判定**。这是退化测点，不是结论。

本探针换成**真正离轴的点**（rest 位姿下手臂/脚的末端，xy 明显不为 0），
对 θ 扫描，看它的 xy 是否绕 `root.head`（=(0,0,0)）转过 θ、且 z 不变。

两种情形：
  A. `root.rotation_euler.y` = **世界 yaw** ⟹ 每个离轴点的 xy 绕原点转 θ、z 恒定。
  B. 不是 ⟹ 点会走别的路径（z 变、或不转、或转错轴）。

同时顺带量 `root.location` 的**世界语义**：`matrix_basis = T(loc) @ R` ⟹
位移应发生在**旋转之后、且在未旋转的 rest 系里**。用同一点在
`(yaw=θ, loc=wloc(dx,dy,dz))` 下的位移向量验证。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python probe_c11_axis.py
"""

import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A            # noqa: E402
import anim_idle_01 as I1       # noqa: E402

PROBES = ("foot.L", "foot.R", "hand.L", "hand.R", "head", "pelvis")
OFF_DEG = (0.0, 45.0, 90.0, 180.0, 270.0)


def yaw_of(point, origin=(0.0, 0.0)):
    """点在 xy 平面上相对原点的极角（度）。"""
    return math.degrees(math.atan2(point[1] - origin[1], point[0] - origin[0]))


def body(arm, theta, loc=None):
    pose = {"root": (0.0, theta, 0.0)}
    if loc is not None:
        pose["@loc"] = {"root": loc}
    A.apply_pose(arm, pose)
    bpy.context.view_layer.update()
    return {name: tuple(A.bone_world(arm, name, "tail")) for name in PROBES}


def main():
    arm, _meshes = A.open_animation_project()
    A.setup_scene()
    if I1.NAME not in bpy.data.actions:
        I1.main()
        arm, _meshes = A.open_animation_project()
        A.setup_scene()

    if arm.animation_data is not None:
        arm.animation_data.action = None

    # ---- 0) rest 位姿下各骨末端（找离轴点）
    rest = body(arm, 0.0)
    A.report("C11_AXIS_REST", {
        name: [round(v * 1000.0, 3) for v in pos] for name, pos in rest.items()})

    # ---- 1) yaw 扫描：离轴点的 xy 是否绕原点转过 θ、z 是否恒定
    rows = {}
    for theta in OFF_DEG:
        got = body(arm, theta)
        row = {}
        for name in PROBES:
            p0, p1 = rest[name], got[name]
            r0 = math.hypot(p0[0], p0[1])
            r1 = math.hypot(p1[0], p1[1])
            row[name] = {
                "yaw_in_deg": round(math.degrees(yaw_of(p0)), 4),
                "yaw_out_deg": round(math.degrees(yaw_of(p1)), 4),
                "yaw_step_deg": round(math.degrees(
                    (yaw_of(p1) - yaw_of(p0) + math.pi) % (2 * math.pi) - math.pi), 4),
                "radius_in_mm": round(r0 * 1000.0, 3),
                "radius_out_mm": round(r1 * 1000.0, 3),
                "z_in_mm": round(p0[2] * 1000.0, 3),
                "z_out_mm": round(p1[2] * 1000.0, 3),
            }
        rows["yaw_%03d" % int(theta)] = row

    # ---- 2) root 骨自身的 3×3（最直接：是不是 = Rz(θ)）
    basis_rows = {}
    for theta in OFF_DEG:
        A.apply_pose(arm, {"root": (0.0, theta, 0.0)})
        bpy.context.view_layer.update()
        m = arm.pose.bones["root"].matrix.to_3x3()
        rz = Matrix.Rotation(math.radians(theta), 3, "Z")
        basis_rows["yaw_%03d" % int(theta)] = {
            "pose_basis_3x3": [[round(v, 6) for v in row] for row in m],
            "Rz_3x3": [[round(v, 6) for v in row] for row in rz],
            "max_abs_diff": round(max(abs(m[i][j] - rz[i][j])
                                      for i in range(3) for j in range(3)), 6),
            "euler_deg": [round(math.degrees(v), 4)
                          for v in arm.pose.bones["root"].rotation_euler],
        }

    # ---- 3) root.location 的世界语义（wloc）：位移是否在"未旋转的 rest 系"里
    loc_rows = {}
    dx, dy, dz = 0.20, -0.10, 0.05
    for theta in (0.0, 90.0):
        p_base = body(arm, theta)[PROBES[0]]
        loc = A.wloc(dx, dy, dz)
        p_shift = body(arm, theta, loc=loc)[PROBES[0]]
        delta = Vector(p_shift) - Vector(p_base)
        want = Vector((dx, dy, dz))
        rot = Matrix.Rotation(math.radians(theta), 3, "Z") @ want
        loc_rows["yaw_%03d" % int(theta)] = {
            "loc": [round(v, 6) for v in loc],
            "moved_world_mm": [round(v * 1000.0, 3) for v in delta],
            "want_unrotated_mm": [round(v * 1000.0, 3) for v in want],
            "want_with_yaw_mm": [round(v * 1000.0, 3) for v in rot],
            "err_unrotated_mm": round((delta - want).length * 1000.0, 4),
            "err_with_yaw_mm": round((delta - rot).length * 1000.0, 4),
        }

    A.report("C11_AXIS", {
        "yaw_scan": rows,
        "root_basis": basis_rows,
        "root_loc_semantics": loc_rows,
    })
    print("C11_AXIS_DONE")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("C11_AXIS_FAILURE " + traceback.format_exc())
