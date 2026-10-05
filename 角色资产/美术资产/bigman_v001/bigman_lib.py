"""bigman_v001 —— 几何 / 材质 / 场景基础库（从零构建，不引用任何既有资产）。

坐标约定：+Z 向上，角色正面朝 -Y，角色左侧为 +X。
尺寸约定：鞋底 z = 0，发顶 z = 1.800（身高 1.80 m），T-pose 手臂水平于 z = 1.420。

所有几何用纯数据构建（from_pydata / bmesh），不依赖 bpy.ops 的上下文。
"""

import math
import os

import bmesh
import bpy
from mathutils import Matrix, Vector

OUT_DIR = os.path.abspath(r"I:/工作项目/BIGMANFIGHT/角色资产/美术资产/bigman_v001")
BLEND_PATH = os.path.join(OUT_DIR, "bigman_tpose_v001.blend")
GLB_PATH = os.path.join(OUT_DIR, "bigman_tpose_v001.glb")
PREVIEW_DIR = os.path.join(OUT_DIR, "previews")

TAU = math.pi * 2.0

# ---------------------------------------------------------------- 纵向标尺 (m)
Z_SOLE = 0.000
Z_ANKLE = 0.078
Z_KNEE = 0.490
Z_HIP = 0.900
Z_HEM = 0.900
Z_WAIST = 1.100
Z_ARMPIT = 1.270
Z_CHEST = 1.330
Z_ARM = 1.420
Z_NECK_BASE = 1.500
Z_CHIN = 1.552
Z_MOUTH = 1.596
Z_NOSE = 1.626
Z_EYE = 1.680
Z_BROW = 1.698
Z_HAIRLINE = 1.744
Z_CROWN = 1.786
Z_TOP = 1.800


# ---------------------------------------------------------------- 数学工具
def superellipse(t, e):
    c = math.cos(t)
    s = math.sin(t)
    u = math.copysign(abs(c) ** (2.0 / e), c) if abs(c) > 1e-12 else 0.0
    v = math.copysign(abs(s) ** (2.0 / e), s) if abs(s) > 1e-12 else 0.0
    return u, v


def bell(value, center, width):
    return math.exp(-((value - center) / width) ** 2)


def lerp(a, b, t):
    return a + (b - a) * t


def smoothstep(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3.0 - 2.0 * x)


def axis_matrix(axis, angle):
    return Matrix.Rotation(angle, 3, axis)


def apply_rot(point, rot):
    p = Vector(point)
    if not rot:
        return p
    for axis, angle in zip("XYZ", rot):
        p.rotate(axis_matrix(axis, angle))
    return p


# ---------------------------------------------------------------- 截面与放样
def ring_xy(z, hx, front, back, e=2.0, segments=32, mod=None, center_xy=(0.0, 0.0)):
    """XY 平面截面环，front/back 为正向长度（front 朝 -Y）。"""
    pts = []
    for i in range(segments):
        t = TAU * i / segments
        cu, cv = superellipse(t, e)
        x = hx * cu
        y = back * cv if cv >= 0 else -front * (-cv)
        if mod:
            x, y = mod(x, y, cv)
        pts.append(Vector((center_xy[0] + x, center_xy[1] + y, z)))
    return pts


def ring_plane(center, u_axis, v_axis, ru_neg, ru_pos, rv_neg, rv_pos, e=2.0,
               segments=32, mod=None):
    """任意平面截面环；u/v 为平面内两轴，neg/pos 为负向/正向半轴长度。"""
    c = Vector(center)
    ua = Vector(u_axis)
    va = Vector(v_axis)
    pts = []
    for i in range(segments):
        t = TAU * i / segments
        cu, cv = superellipse(t, e)
        ru = ru_pos if cu >= 0 else ru_neg
        rv = rv_pos if cv >= 0 else rv_neg
        x, y = ru * cu, rv * cv
        if mod:
            x, y = mod(x, y, cu, cv)
        pts.append(c + ua * x + va * y)
    return pts


def mesh_object(name, verts, faces, material, collection=None, smooth=True,
                subsurf=0):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    mesh.validate(verbose=False)
    mesh.update()

    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    (collection or bpy.context.scene.collection).objects.link(obj)
    if material is not None:
        obj.data.materials.append(material)
    if smooth:
        for poly in mesh.polygons:
            poly.use_smooth = True
    if subsurf:
        mod = obj.modifiers.new("Subdivision", "SUBSURF")
        mod.levels = subsurf
        mod.render_levels = subsurf
    return obj


def loft(name, rings, material, collection=None, cap_start=True, cap_end=True,
         smooth=True, subsurf=0):
    count = len(rings[0])
    verts = []
    for r in rings:
        verts.extend(r)
    faces = []
    for i in range(len(rings) - 1):
        a = i * count
        b = (i + 1) * count
        for j in range(count):
            k = (j + 1) % count
            faces.append((a + j, a + k, b + k, b + j))
    if cap_start:
        center = sum((Vector(v) for v in rings[0]), Vector()) / count
        ci = len(verts)
        verts.append(center)
        for j in range(count):
            faces.append((ci, (j + 1) % count, j))
    if cap_end:
        base = (len(rings) - 1) * count
        center = sum((Vector(v) for v in rings[-1]), Vector()) / count
        ci = len(verts)
        verts.append(center)
        for j in range(count):
            faces.append((ci, base + j, base + (j + 1) % count))
    return mesh_object(name, verts, faces, material, collection, smooth, subsurf)


def sphere(name, center, radii, material, collection=None, segments=24,
           rings=14, rot=None, smooth=True, subsurf=0):
    rx, ry, rz = radii
    verts = []
    for i in range(1, rings):
        phi = math.pi * i / rings
        z = math.cos(phi)
        r = math.sin(phi)
        for j in range(segments):
            th = TAU * j / segments
            verts.append(Vector((r * math.cos(th) * rx,
                                 r * math.sin(th) * ry,
                                 z * rz)))
    verts.append(Vector((0.0, 0.0, rz)))
    verts.append(Vector((0.0, 0.0, -rz)))
    top = len(verts) - 2
    bottom = len(verts) - 1

    faces = []
    for i in range(rings - 2):
        for j in range(segments):
            k = (j + 1) % segments
            a, b = i * segments, (i + 1) * segments
            faces.append((a + j, a + k, b + k, b + j))
    for j in range(segments):
        k = (j + 1) % segments
        faces.append((top, k, j))
        base = (rings - 2) * segments
        faces.append((bottom, base + j, base + k))

    out = [apply_rot(v, rot) + Vector(center) for v in verts]
    return mesh_object(name, out, faces, material, collection, smooth, subsurf)


def box(name, center, size, material, collection=None, rot=None, bevel=0.0,
        bevel_segments=2, smooth=False, subsurf=0):
    sx, sy, sz = (s * 0.5 for s in size)
    if bevel <= 0.0:
        corners = [
            (-sx, -sy, -sz), (sx, -sy, -sz), (sx, sy, -sz), (-sx, sy, -sz),
            (-sx, -sy, sz), (sx, -sy, sz), (sx, sy, sz), (-sx, sy, sz),
        ]
        faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
                 (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        verts = [apply_rot(c, rot) + Vector(center) for c in corners]
        return mesh_object(name, verts, faces, material, collection, smooth,
                           subsurf)

    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector((size[0], size[1], size[2])), verts=bm.verts)
    bmesh.ops.bevel(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces),
                    offset=bevel, segments=bevel_segments, profile=0.5,
                    affect="EDGES")
    matrix = Matrix.Identity(3)
    if rot:
        for axis, angle in zip("XYZ", rot):
            matrix = Matrix.Rotation(angle, 3, axis) @ matrix
    bmesh.ops.transform(bm, matrix=matrix.to_4x4(), verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(center), verts=bm.verts)
    bm.verts.index_update()
    verts = [v.co.copy() for v in bm.verts]
    faces = [[v.index for v in f.verts] for f in bm.faces]
    bm.free()
    return mesh_object(name, verts, faces, material, collection, smooth,
                       subsurf)


def tube(name, path, radii, material, collection=None, segments=14,
         section="round", rect=None, e=2.0, up_hint=(0, 0, 1), smooth=True,
         subsurf=0, caps=True):
    """沿折线扫管。section='round' 用 radii；section='rect' 用 rect=(hw,hh)。"""
    pts = [Vector(p) for p in path]
    rings = []
    for i, p in enumerate(pts):
        if i == 0:
            tangent = pts[1] - pts[0]
        elif i == len(pts) - 1:
            tangent = pts[-1] - pts[-2]
        else:
            tangent = pts[i + 1] - pts[i - 1]
        if tangent.length < 1e-9:
            tangent = Vector((0, 0, 1))
        tangent.normalize()
        up = Vector(up_hint)
        if abs(tangent.dot(up)) > 0.95:
            up = Vector((0, 1, 0))
        u_axis = tangent.cross(up).normalized()
        v_axis = u_axis.cross(tangent).normalized()
        if section == "round":
            r = radii[i]
            rings.append(ring_plane(p, u_axis, v_axis, r, r, r, r, 2.0, segments))
        else:
            hw, hh = rect
            rings.append(ring_plane(p, u_axis, v_axis, hw, hw, hh, hh, e,
                                    segments))
    return loft(name, rings, material, collection, caps, caps, smooth, subsurf)


def rect_frame(name, center, half_w, half_h, tube_r, material, collection=None,
               e=3.2, segments=12):
    """绕矩形路径扫一圈，做眼镜框。"""
    cx, cy, cz = center
    steps = 28
    pts = []
    for i in range(steps):
        t = TAU * i / steps
        cu, cv = superellipse(t, e)
        pts.append(Vector((cx + half_w * cu, cy, cz + half_h * cv)))
    pts.append(pts[0])
    return tube(name, pts, [tube_r] * len(pts), material, collection, segments)


# ---------------------------------------------------------------- 材质
MAT = {}


def make_material(name, color, roughness=0.5, metallic=0.0, alpha=1.0,
                  specular=0.5):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = next(
        (node for node in mat.node_tree.nodes if node.type == "BSDF_PRINCIPLED"),
        None,
    )
    if bsdf is None:
        bsdf = mat.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    for socket in ("Specular IOR Level", "Specular"):
        try:
            bsdf.inputs[socket].default_value = specular
            break
        except (KeyError, IndexError):
            continue
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
        for attr, value in (("blend_method", "BLEND"),
                            ("surface_render_method", "BLENDED"),
                            ("use_backface_culling", False)):
            try:
                setattr(mat, attr, value)
            except (AttributeError, TypeError):
                pass
    mat.diffuse_color = (color[0], color[1], color[2], alpha)
    mat.roughness = roughness
    mat.metallic = metallic
    MAT[name] = mat
    return mat


def build_materials():
    make_material("Skin", (0.552, 0.300, 0.212), 0.52)
    make_material("Skin_Dark", (0.430, 0.215, 0.150), 0.50)
    make_material("Suit_Blue", (0.019, 0.086, 0.545), 0.74)
    make_material("Suit_Blue_Deep", (0.010, 0.045, 0.320), 0.72)
    make_material("Shirt_White", (0.800, 0.810, 0.830), 0.62)
    # 黑发在柔光棚里是哑光的：高 specular 会把它渲染成抛光塑料头盔
    make_material("Hair_Black", (0.013, 0.012, 0.014), 0.66, specular=0.14)
    make_material("Shoe_Black", (0.022, 0.023, 0.027), 0.62, specular=0.30)
    make_material("Shoe_Sole", (0.010, 0.010, 0.011), 0.68, specular=0.22)
    make_material("Glasses_Black", (0.020, 0.020, 0.024), 0.44, specular=0.32)
    make_material("Lens_Glass", (0.620, 0.660, 0.700), 0.30, 0.0, 0.34)
    # 巩膜不能是纯白 —— 纯白 + 大面积 = "惨白瞪眼"，读作卡通豆豆眼。
    # 压到 0.72 并略偏暖，接近真实结膜色，深色虹膜才咬得住它。
    make_material("Eye_White", (0.720, 0.706, 0.690), 0.26)
    make_material("Iris", (0.128, 0.062, 0.028), 0.20)
    # 角膜缘环（limbal ring）：虹膜外一圈近黑的深色。单色虹膜无论多深都读作
    # "玻璃珠/豆豆眼"，只有这圈深色轮廓能把虹膜从巩膜上"切"出来，眼睛才显利。
    make_material("Iris_Ring", (0.028, 0.014, 0.008), 0.18)
    make_material("Pupil", (0.004, 0.004, 0.004), 0.14)
    # 角膜高光点：眼睛"有神"的唯一来源 —— 一颗高亮低粗糙度的小球
    make_material("Eye_Glint", (0.965, 0.960, 0.955), 0.06, specular=0.75)
    make_material("Brow", (0.012, 0.011, 0.012), 0.56, specular=0.30)
    make_material("Lips", (0.520, 0.300, 0.268), 0.50)
    make_material("Button_Dark", (0.022, 0.026, 0.036), 0.34, 0.35)
    make_material("Backdrop", (0.820, 0.820, 0.820), 0.90)


# ---------------------------------------------------------------- 场景管理
COLLECTIONS = {}


def reset_scene():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for col in list(bpy.data.collections):
        bpy.data.collections.remove(col)
    for attr in ("meshes", "materials", "armatures", "cameras", "lights",
                 "actions", "images", "node_groups"):
        data = getattr(bpy.data, attr, None)
        if data is None:
            continue
        for block in list(data):
            if block.users == 0:
                try:
                    data.remove(block)
                except (RuntimeError, ReferenceError):
                    pass
    MAT.clear()
    COLLECTIONS.clear()


def collection(name, parent=None):
    col = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(col)
    COLLECTIONS[name] = col
    return col
