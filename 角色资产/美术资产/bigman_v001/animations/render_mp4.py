"""render_mp4 —— 把指定 Action 渲染成 mp4（给人过目用）。

用法（环境变量）：
    ANIM=Idle_01 VIEW=side  blender --background --factory-startup --python render_mp4.py
    VIEW 取 side / front / three_quarter，默认 side。
    OFFSET_Z=1.30 SCALE=4.20 可覆盖取景中心高度与正交宽度 —— **Jump 族需要**：
    标准视图是给站姿（中心 0.92 m、宽 2.10 m）定的，A12 从 2.85 m 高落到 1.3 m，
    用标准视图会把头和脚一起切掉。

输出：previews/anim/<ANIM>_<VIEW>.mp4
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A  # noqa: E402

NAME = os.environ.get("ANIM", "Idle_01")
VIEW_NAME = os.environ.get("VIEW", "side")
VIEWS = {"side": A.VIEW_SIDE, "front": A.VIEW_FRONT,
         "three_quarter": A.VIEW_3Q,
         # ★ D16 新增：`side_wide` = 与 `side` **同机位**、只是取景更宽。
         #   由来：躺地族（D14/D15/D16 及后续 D17/D18/D19/E11）身体水平横跨
         #   1.3 m+，标准侧视（宽 2.10 m、中心高 0.92 m）装不下，人的头会被
         #   右边缘切掉。`side` 保持原样以维持 **D13/D14/D15 的跨支逐位可比性**；
         #   要"给人过目"就用 `side_wide` + `OFFSET_Y/OFFSET_Z/SCALE`。
         "side_wide": A.VIEW_SIDE,
         "front_wide": A.VIEW_FRONT,
         "three_quarter_wide": A.VIEW_3Q}
OFFSET_Z = os.environ.get("OFFSET_Z")
OFFSET_Y = os.environ.get("OFFSET_Y")
SCALE = os.environ.get("SCALE")


def make_wall_proxy(y_m, name="D19_Wall_Proxy"):
    """可选：在 `y = y_m` 立一块薄板（法线 −Y），**只在出图时存在**。

    ★ D19 `Wall_Hit` 是全项目第一支引入**世界实体**的动画：mp4 里没有墙，
      目检根本读不出"撞墙"。由 `WALL_Y=<米>` 环境变量显式开启（**默认不开**，
      其余 56 支的行为逐位不变）。★ 它**绝不**进入 .blend / GLB —— 本脚本
      只渲染、不存盘。
    """
    x0, x1 = -1.55, 1.55
    z0, z1 = -0.05, 3.30
    t = 0.010
    verts = [(x0, y_m, z0), (x1, y_m, z0), (x1, y_m, z1), (x0, y_m, z1),
             (x0, y_m + t, z0), (x1, y_m + t, z0),
             (x1, y_m + t, z1), (x0, y_m + t, z1)]
    faces = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1),
             (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    mesh = A.bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = A.bpy.data.objects.new(name, mesh)
    A.bpy.context.scene.collection.objects.link(obj)
    mat = A.bpy.data.materials.new("D19_Wall_Mat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is not None:
        bsdf.inputs["Base Color"].default_value = (0.16, 0.18, 0.22, 1.0)
    mat.diffuse_color = (0.16, 0.18, 0.22, 1.0)
    obj.data.materials.append(mat)
    obj.color = (0.16, 0.18, 0.22, 1.0)
    print("WALL_PROXY_BUILT y_m=%r" % y_m)
    return obj


def main():
    arm, _meshes = A.open_animation_project()
    A.setup_scene()
    wall_y = os.environ.get("WALL_Y")
    if wall_y:
        make_wall_proxy(float(wall_y))
    action = None
    for candidate in A.bpy.data.actions:
        if candidate.name == NAME:
            action = candidate
            break
    if action is None:
        raise RuntimeError("找不到 Action：%s（现有 %s）"
                           % (NAME, [a.name for a in A.bpy.data.actions]))
    view = VIEWS[VIEW_NAME]
    if OFFSET_Z or OFFSET_Y or SCALE:
        name, location, target, scale, res = view
        z = float(OFFSET_Z) if OFFSET_Z else target[2]
        y = float(OFFSET_Y) if OFFSET_Y else target[1]
        view = (name, (location[0], location[1] + (y - target[1]), z),
                (target[0], y, z),
                float(SCALE) if SCALE else scale, res)
    os.makedirs(A.PREVIEW_DIR, exist_ok=True)
    path = os.path.join(A.PREVIEW_DIR, "%s_%s.mp4" % (NAME, VIEW_NAME))
    A.render_animation_mp4(arm, action, path, view=view)
    print("MP4_DONE %s" % path)


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("MP4_FAILURE " + traceback.format_exc())
