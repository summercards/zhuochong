"""bigman_v001 —— 躯体与西装几何（壮硕倒三角体型 + 宝蓝单排两粒扣西装）。

关键标尺（米）：肩线 1.446 / 胸最宽 1.372 / 腰最细 1.100 / 下摆 0.905 /
手臂轴线 1.420 / 胯 0.94 / 膝 0.49 / 踝 0.078。

体型实测（渲染尺寸，含 subsurf，取自 run_build 的 TORSO 输出 —— **不要拿站点表算**）：
肩半宽 0.2395 / 腰半宽 0.1459 / 肩厚 0.3003 / 肩腰比 1.642。
"""

import math

from mathutils import Vector

from bigman_lib import (MAT, TAU, Z_ARM, Z_HEM, bell, lerp, loft, mesh_object,
                        ring_plane, ring_xy, smoothstep, sphere)


def box(name, center, size, material, collection, rot=None, bevel=0.0,
        bevel_segments=2, smooth=False, subsurf=0):
    from bigman_lib import box as lib_box

    return lib_box(name, center, size, material, collection, rot, bevel,
                   bevel_segments, smooth, subsurf)


# ---------------------------------------------------------------- 躯干剖面
def torso_stations():
    """(z, 半宽, 前伸, 后伸, 指数, 修正)"""

    def pec(x, y, cv):
        """胸大肌：前胸外推。0.021 → 0.026（厚实化的主力项，前视图里胸廓的体量靠它）。"""
        if cv < 0 and abs(x) < 0.17:
            y -= 0.026 * bell(abs(x), 0.078, 0.058)
        return x, y

    def lat(x, y, cv):
        """背阔肌：背部上段外扩。范围 0.105 → 0.098、增益 1.045 → 1.058 —— 让背从
        腋下就张开，肩胛一带的宽度靠它撑起来，倒三角的\"上宽\"有一半来自这里。"""
        if cv > 0 and abs(x) > 0.098:
            x *= 1.058
        return x, y

    def glute(x, y, cv):
        if cv > 0 and abs(x) < 0.15:
            y += 0.012 * bell(abs(x), 0.075, 0.070)
        return x, y

    def trap(x, y, cv):
        """斜方肌：颈根到肩峰的隆起。0.008 → 0.017、峰位外移 0.055 → 0.070。
        这一项直接决定\"肩膀厚不厚\"——侧视图里肩上那道从脖子斜落到肩头的
        斜坡就是它，薄了整块肩读作衣架，厚了才读作肌肉。"""
        if cv > 0 and abs(x) < 0.16:
            y += 0.017 * bell(abs(x), 0.070, 0.062)
        return x, y

    # 倒三角的三根轴线（改任一项先读另两项，它们共同决定轮廓）：
    #   1. 肩（1.412 三角肌最宽 / 1.446 肩线）—— "上宽"；
    #   2. 腰（1.100 收到 0.139）—— "下窄"；
    #   3. 肩部前后径（1.372 站 0.155+0.144 = 0.299 m）—— "厚"。宽度给了剪影，
    #      厚度才给体量；只加宽不加厚会变成"纸片人披了件宽西装"。
    #
    # ⚠ 站点值是**控制点**，不是渲染尺寸。躯干挂了 subsurf=1，Catmull-Clark 会把
    #   凸处收进去、凹处抬出来：肩（凸）控制点 0.243 → 实际 0.234（−3.9%），
    #   腰（局部极小）控制点 0.142 → 实际 0.149（+4.8%）。所以按站点值推算的
    #   肩腰比 1.71，渲染出来只有 1.57。**判断体型一律看 run_build 的 TORSO 输出，
    #   不要拿这张表算。**下面的站点值是按实测反推出来的。
    #
    # 肩区相邻站实测半宽落差控制在 16 mm 以内，读作**方肩**。曾有一版 1.412 相对
    # 1.372 突 25 mm，渲染出来是"腋下各挂一颗球"——最宽点单独耸起就是圆肩。
    return [
        (Z_HEM,  0.186, 0.120, 0.126, 2.9, glute),
        (0.958,  0.190, 0.123, 0.132, 2.8, glute),
        (1.030,  0.184, 0.121, 0.126, 2.7, glute),
        (1.100,  0.139, 0.110, 0.114, 2.7, None),
        (1.170,  0.151, 0.117, 0.120, 2.6, None),
        (1.240,  0.182, 0.134, 0.132, 2.5, None),
        (1.300,  0.208, 0.146, 0.138, 2.4, pec),
        (1.372,  0.228, 0.155, 0.144, 2.4, pec),
        (1.412,  0.237, 0.152, 0.145, 2.35, lat),
        (1.446,  0.241, 0.144, 0.140, 2.3, trap),
        (1.470,  0.228, 0.132, 0.134, 2.3, trap),
        (1.492,  0.172, 0.114, 0.122, 2.3, trap),
        (1.514,  0.106, 0.087, 0.097, 2.3, None),
        (1.532,  0.086, 0.076, 0.084, 2.3, None),
    ]


class TorsoProfile:
    def __init__(self):
        self.stations = torso_stations()

    def params(self, z):
        st = self.stations
        if z <= st[0][0]:
            return st[0][1:5]
        if z >= st[-1][0]:
            return st[-1][1:5]
        for i in range(len(st) - 1):
            z0, z1 = st[i][0], st[i + 1][0]
            if z0 <= z <= z1:
                t = (z - z0) / (z1 - z0)
                return tuple(lerp(st[i][k], st[i + 1][k], t) for k in (1, 2, 3, 4))
        return st[-1][1:5]

    def front_y(self, z, x):
        hx, front, _back, e = self.params(z)
        cu = min(abs(x) / max(hx, 1e-6), 1.0)
        cv = (1.0 - cu ** e) ** (1.0 / e) if cu < 1.0 else 0.0
        return -front * cv

    def back_y(self, z, x):
        hx, _front, back, e = self.params(z)
        cu = min(abs(x) / max(hx, 1e-6), 1.0)
        cv = (1.0 - cu ** e) ** (1.0 / e) if cu < 1.0 else 0.0
        return back * cv


PROFILE = TorsoProfile()


def build_torso(col):
    rings = []
    for z, hx, front, back, e, mod in torso_stations():
        rings.append(ring_xy(z, hx, front, back, e, 32, mod))
    torso = loft("Suit_Torso", rings, MAT["Suit_Blue"], col, subsurf=1)

    # 下摆：极窄深色切线 + 同色外扩，读作清晰下摆边缘
    hem_dark = []
    for z in (0.8975, 0.9015):
        hx, front, back, _e = PROFILE.params(z)
        hem_dark.append(ring_xy(z, hx * 0.999, front * 0.999, back * 0.999,
                                2.9, 32))
    loft("Jacket_Hem_Line", hem_dark, MAT["Suit_Blue_Deep"], col, False, False,
         subsurf=1)
    hem_rings = []
    for z, scale in ((0.9030, 1.0035), (0.9080, 1.0075), (0.9200, 1.0075),
                     (0.9260, 1.0020)):
        hx, front, back, e = PROFILE.params(z)
        hem_rings.append(ring_xy(z, hx * scale, front * scale, back * scale,
                                 2.9, 32))
    loft("Jacket_Hem", hem_rings, MAT["Suit_Blue"], col, True, False, subsurf=1)
    return torso


def build_neck(col):
    """颈部：基部粗、向上渐细，顶端收窄让下颌包住（避免粗脖子顶穿下颌）。"""
    rings = [
        ring_xy(1.410, 0.070, 0.064, 0.068, 2.3, 28),
        ring_xy(1.458, 0.064, 0.058, 0.062, 2.3, 28),
        ring_xy(1.505, 0.059, 0.053, 0.058, 2.3, 28),
        ring_xy(1.550, 0.055, 0.050, 0.055, 2.3, 28),
        ring_xy(1.590, 0.052, 0.048, 0.053, 2.3, 28),
    ]
    return loft("Neck", rings, MAT["Skin"], col, subsurf=1)


# ---------------------------------------------------------------- 手臂与手
def arm_stations():
    """(x, 前后半径, 上伸, 下伸, 指数)

    三角肌段（0.136 ~ 0.230）是"肩厚实"的落点：
    - **前后径** 0.104 → 0.118（±14 mm）—— 侧视图里肩的厚度，正视图看不到，
      但它是"宽西装"与"宽肩膀"的区别所在；
    - **下伸** 0.116 → 0.134（肱三头肌侧）—— 臂根向下加厚，肩到臂的过渡变浑圆，
      不再是一根管子从躯干上"插"出来；
    - **上伸** 0.090 → 0.096 —— 只加 6 mm 就收手。肩头上缘 1.516 已经比躯干
      在该处的轮廓高 24 mm，再加就把肩推得比躯干顶（1.532）还高，读作
      "耸肩 / 垫肩肿起"而不是肌肉。
    峰位仍在 x=0.184，向手腕单调收细，中途不回塌。
    """
    return [
        (0.136, 0.108, 0.088, 0.126, 2.8),
        (0.184, 0.118, 0.096, 0.134, 2.6),
        (0.230, 0.110, 0.088, 0.116, 2.5),
        (0.276, 0.101, 0.077, 0.099, 2.45),
        (0.318, 0.094, 0.064, 0.085, 2.4),
        (0.358, 0.089, 0.057, 0.076, 2.4),
        (0.398, 0.085, 0.053, 0.070, 2.4),
        (0.438, 0.081, 0.050, 0.065, 2.4),
        (0.476, 0.077, 0.047, 0.061, 2.4),
        (0.506, 0.076, 0.046, 0.060, 2.4),
        (0.536, 0.072, 0.044, 0.058, 2.4),
        (0.578, 0.069, 0.042, 0.056, 2.4),
        # 0.618 往下必须与 `build_cuff` 的衬衫袖口保持 3 mm 以上的半径差，
        # 否则白袖口会与西装袖口共面（Z-fighting 花斑）。袖口段的数值不动。
        (0.618, 0.062, 0.036, 0.048, 2.4),
        (0.648, 0.056, 0.032, 0.043, 2.4),
        (0.662, 0.054, 0.031, 0.042, 2.4),
    ]


def build_arm(col, side):
    sign = 1.0 if side == "L" else -1.0
    rings = []
    for x, r, up, down, e in arm_stations():
        rings.append(ring_plane((sign * x, 0.0, Z_ARM), (0, 1, 0), (0, 0, 1),
                                r, r, down, up, e, 28))
    return loft("Sleeve_" + side, rings, MAT["Suit_Blue"], col, subsurf=1)


def build_cuff(col, side):
    """衬衫袖口：从西装袖口里露出的白边（半径略小于袖口）。"""
    sign = 1.0 if side == "L" else -1.0
    rings = [
        ring_plane((sign * 0.634, 0.0, Z_ARM), (0, 1, 0), (0, 0, 1),
                   0.056, 0.056, 0.031, 0.042, 2.3, 22),
        ring_plane((sign * 0.662, 0.0, Z_ARM), (0, 1, 0), (0, 0, 1),
                   0.055, 0.055, 0.030, 0.041, 2.3, 22),
        ring_plane((sign * 0.684, 0.0, Z_ARM), (0, 1, 0), (0, 0, 1),
                   0.054, 0.054, 0.029, 0.040, 2.3, 22),
    ]
    return loft("Shirt_Cuff_" + side, rings, MAT["Shirt_White"], col)

FINGERS = (
    ("index", -0.030, 0.074),
    ("middle", -0.010, 0.080),
    ("ring", 0.011, 0.073),
    ("pinky", 0.031, 0.058),
)


def build_hand(col, side):
    sign = 1.0 if side == "L" else -1.0
    objects = []
    palm = [
        ring_plane((sign * 0.668, 0.0, Z_ARM), (0, 1, 0), (0, 0, 1),
                   0.035, 0.035, 0.017, 0.017, 2.6, 24),
        ring_plane((sign * 0.712, 0.0, Z_ARM), (0, 1, 0), (0, 0, 1),
                   0.043, 0.043, 0.019, 0.018, 3.0, 24),
        ring_plane((sign * 0.752, 0.0, Z_ARM), (0, 1, 0), (0, 0, 1),
                   0.046, 0.046, 0.019, 0.018, 3.0, 24),
        ring_plane((sign * 0.786, 0.0, Z_ARM), (0, 1, 0), (0, 0, 1),
                   0.045, 0.045, 0.017, 0.016, 3.0, 24),
    ]
    objects.append(loft("Hand_Palm_" + side, palm, MAT["Skin"], col, subsurf=1))

    for name, y, length in FINGERS:
        segments = 6
        rings = []
        for i in range(segments + 1):
            s = i / segments
            x = sign * (0.786 + length * s)
            taper = 1.0 - 0.20 * smoothstep(s)
            r = 0.0114 * taper
            rz = 0.0120 * taper
            rings.append(
                ring_plane((x, y - 0.004 * s, Z_ARM), (0, 1, 0), (0, 0, 1),
                           r, r, rz, rz, 2.4, 16)
            )
        objects.append(
            loft("Finger_%s_%s" % (name.capitalize(), side), rings, MAT["Skin"],
                 col, subsurf=1)
        )

    thumb_path = (
        (0.706, -0.044, Z_ARM - 0.011),
        (0.726, -0.064, Z_ARM - 0.006),
        (0.744, -0.082, Z_ARM - 0.003),
        (0.754, -0.095, Z_ARM - 0.002),
    )
    rings = []
    for i, p in enumerate(thumb_path):
        s = i / (len(thumb_path) - 1)
        r = lerp(0.0148, 0.0096, smoothstep(s))
        rings.append(
            ring_plane((sign * p[0], p[1], p[2]), (0, 1, 0), (0, 0, 1),
                       r, r, r, r, 2.3, 16)
        )
    objects.append(loft("Thumb_" + side, rings, MAT["Skin"], col, subsurf=1))
    return objects


# ---------------------------------------------------------------- 腿与鞋
LEG_CENTER = 0.093


def build_leg(col, side):
    sign = 1.0 if side == "L" else -1.0

    def crease(x, y, cv):
        if cv < 0 and abs(x) < 0.022:
            y -= 0.0050 * bell(x, 0.0, 0.013)
        return x, y

    stations = [
        (1.030, 0.090, 0.096, 0.100, 2.7, None),
        (0.940, 0.093, 0.101, 0.108, 2.6, None),
        (0.860, 0.092, 0.100, 0.104, 2.6, crease),
        (0.760, 0.090, 0.098, 0.099, 2.6, crease),
        (0.660, 0.088, 0.096, 0.095, 2.6, crease),
        (0.560, 0.085, 0.092, 0.089, 2.6, crease),
        (0.500, 0.082, 0.090, 0.083, 2.6, crease),
        (0.450, 0.080, 0.086, 0.086, 2.6, crease),
        (0.390, 0.079, 0.080, 0.090, 2.6, crease),
        (0.320, 0.076, 0.075, 0.085, 2.6, crease),
        (0.250, 0.072, 0.071, 0.076, 2.6, crease),
        (0.180, 0.069, 0.068, 0.069, 2.6, crease),
        (0.125, 0.069, 0.073, 0.069, 2.6, crease),
        (0.108, 0.070, 0.076, 0.070, 2.6, crease),
    ]
    rings = []
    for z, hx, front, back, e, mod in stations:
        center = sign * (LEG_CENTER - 0.005 * (1.030 - z) / 0.9)
        rings.append(ring_xy(z, hx, front, back, e, 26, mod,
                             center_xy=(center, 0.0)))
    return loft("Trouser_" + side, rings, MAT["Suit_Blue"], col, subsurf=1)


def build_shoe(col, side):
    sign = 1.0 if side == "L" else -1.0
    x = 0.090 * sign
    objects = []

    upper = [
        (0.080, 0.036, 0.018, 0.076, 3.0),
        (0.052, 0.044, 0.016, 0.088, 3.0),
        (0.010, 0.050, 0.016, 0.096, 2.9),
        (-0.040, 0.051, 0.016, 0.094, 2.9),
        (-0.092, 0.050, 0.016, 0.082, 2.9),
        (-0.140, 0.046, 0.017, 0.064, 2.9),
        (-0.176, 0.039, 0.018, 0.046, 2.9),
        (-0.200, 0.028, 0.020, 0.030, 2.8),
    ]
    rings = []
    for y, hx, z0, z1, e in upper:
        rings.append(
            ring_plane((x, y, (z0 + z1) * 0.5), (1, 0, 0), (0, 0, 1),
                       hx, hx, (z1 - z0) * 0.5, (z1 - z0) * 0.5, e, 24)
        )
    objects.append(loft("Shoe_Upper_" + side, rings, MAT["Shoe_Black"], col,
                        subsurf=1))

    sole = [
        (0.084, 0.042, 0.002),
        (0.052, 0.052, 0.000),
        (0.000, 0.057, 0.000),
        (-0.060, 0.057, 0.000),
        (-0.120, 0.053, 0.000),
        (-0.170, 0.045, 0.001),
        (-0.206, 0.031, 0.004),
    ]
    rings = []
    for y, hx, z0 in sole:
        rings.append(
            ring_plane((x, y, (z0 + 0.017) * 0.5), (1, 0, 0), (0, 0, 1),
                       hx, hx, (0.017 - z0) * 0.5, (0.017 - z0) * 0.5, 3.2, 20)
        )
    objects.append(loft("Shoe_Sole_" + side, rings, MAT["Shoe_Sole"], col,
                        subsurf=1))

    heel = [(0.082, 0.042), (0.040, 0.048), (0.006, 0.049)]
    rings = []
    for y, hx in heel:
        rings.append(
            ring_plane((x, y, 0.017), (1, 0, 0), (0, 0, 1),
                       hx, hx, 0.016, 0.016, 3.0, 20)
        )
    objects.append(loft("Shoe_Heel_" + side, rings, MAT["Shoe_Sole"], col,
                        subsurf=1))

    # 鞋头压线（牛津鞋头帽分界）
    objects.append(
        box("Shoe_Toe_Cap_" + side, (x, -0.150, 0.050),
            (0.098, 0.006, 0.004), MAT["Shoe_Sole"], col,
            rot=(math.radians(-8.0), 0.0, 0.0))
    )
    return objects


# ---------------------------------------------------------------- 西装细节
V_TOP = 1.480
V_BOTTOM = 1.276
V_HALF_TOP = 0.043
V_HALF_BOTTOM = 0.008


def _v_t(z):
    return max(0.0, min(1.0, (V_TOP - z) / (V_TOP - V_BOTTOM)))


def _v_edge(z):
    return lerp(V_HALF_TOP, V_HALF_BOTTOM, _v_t(z))


def _fold_x(z):
    return lerp(0.092, 0.030, _v_t(z) ** 0.85)


def plate_grid(name, columns, material, col, thickness=0.007):
    """columns 每列为 [(x, z, out), ...]；out 为沿躯干前表面外推的距离。"""
    front = []
    back = []
    for column in columns:
        col_front = []
        col_back = []
        for x, z, out in column:
            y = PROFILE.front_y(z, x)
            col_front.append(Vector((x, y - out, z)))
            col_back.append(Vector((x, y - out + thickness, z)))
        front.append(col_front)
        back.append(col_back)

    verts = []
    idx = {}
    for i, column in enumerate(front):
        for j, point in enumerate(column):
            idx[("f", i, j)] = len(verts)
            verts.append(point)
    for i, column in enumerate(back):
        for j, point in enumerate(column):
            idx[("b", i, j)] = len(verts)
            verts.append(point)

    faces = []
    nx = len(columns)
    rows = len(columns[0])
    for i in range(nx - 1):
        for j in range(rows - 1):
            faces.append((idx[("f", i, j)], idx[("f", i + 1, j)],
                          idx[("f", i + 1, j + 1)], idx[("f", i, j + 1)]))
            faces.append((idx[("b", i, j)], idx[("b", i, j + 1)],
                          idx[("b", i + 1, j + 1)], idx[("b", i + 1, j)]))
    for i in range(nx - 1):
        faces.append((idx[("f", i, 0)], idx[("b", i, 0)],
                      idx[("b", i + 1, 0)], idx[("f", i + 1, 0)]))
        faces.append((idx[("f", i, rows - 1)], idx[("f", i + 1, rows - 1)],
                      idx[("b", i + 1, rows - 1)], idx[("b", i, rows - 1)]))
    for j in range(rows - 1):
        faces.append((idx[("f", 0, j)], idx[("b", 0, j)],
                      idx[("b", 0, j + 1)], idx[("f", 0, j + 1)]))
        faces.append((idx[("f", nx - 1, j)], idx[("f", nx - 1, j + 1)],
                      idx[("b", nx - 1, j + 1)], idx[("b", nx - 1, j)]))
    return mesh_object(name, verts, faces, material, col, smooth=True)


def surface_plate(name, columns, rows, material, col, out=0.006,
                  thickness=0.007, back=False):
    """按 (x, z_bottom, z_top) 列构造贴合躯干表面的薄板。"""
    nodes = []
    for x, zb, zt in columns:
        column = []
        for j in range(rows + 1):
            column.append((x, lerp(zb, zt, j / rows), out))
        nodes.append(column)
    obj = plate_grid(name, nodes, material, col, thickness)
    if back:
        pass
    return obj


def build_suit_details(col):
    objects = []

    # 白衬衫 V 区（严格贴 V 边收窄，不得从驳头外侧露出）
    shirt_columns = []
    steps = 10
    for i in range(steps + 1):
        z = lerp(V_TOP, V_BOTTOM, i / steps)
        w = max(_v_edge(z) * 0.975, 0.005)
        nodes = []
        for j in range(4):
            nodes.append((lerp(-w, w, j / 3), z, 0.0045))
        shirt_columns.append(nodes)
    objects.append(plate_grid("Shirt_Front", shirt_columns, MAT["Shirt_White"],
                              col, thickness=0.005))

    # 驳头：从 V 边向外翻到折线，内侧更外凸（翻领卷边）
    for side, sign in (("L", 1.0), ("R", -1.0)):
        columns = []
        count = 9
        for i in range(count + 1):
            t = i / count
            z = lerp(V_TOP, V_BOTTOM, t)
            inner = _v_edge(z) + 0.0012
            outer = _fold_x(z)
            mid = inner + (outer - inner) * 0.55
            column = [(sign * inner, z, 0.0135), (sign * mid, z, 0.0105),
                      (sign * outer, z, 0.0060)]
            columns.append(column)
        if sign < 0:
            columns = list(reversed(columns))
        objects.append(plate_grid("Jacket_Lapel_" + side, columns,
                                  MAT["Suit_Blue"], col, thickness=0.009))

    # 驳头折线（深色细线，强调翻领折边）
    for side, sign in (("L", 1.0), ("R", -1.0)):
        columns = []
        count = 6
        for i in range(count + 1):
            t = i / count
            z = lerp(V_TOP, V_BOTTOM, t)
            x = sign * _fold_x(z)
            columns.append([(x - sign * 0.0022, z, 0.0062),
                            (x + sign * 0.0022, z, 0.0062)])
        objects.append(plate_grid("Lapel_Fold_" + side, columns,
                                  MAT["Suit_Blue_Deep"], col, thickness=0.004))

    # 领口缺角
    for side, sign in (("L", 1.0), ("R", -1.0)):
        nodes = [[(sign * 0.048, 1.482, 0.013), (sign * 0.048, 1.468, 0.013)],
                 [(sign * 0.074, 1.476, 0.010), (sign * 0.074, 1.462, 0.010)]]
        if sign < 0:
            nodes = list(reversed(nodes))
        objects.append(plate_grid("Lapel_Notch_" + side, nodes,
                                  MAT["Suit_Blue_Deep"], col, thickness=0.004))

    # 领圈（西服领 + 衬衫领，前方开口）
    # 注：衬衫领整体矮于西服领，否则会在后颈露一圈白边（肩宽加大后尤其明显）。
    for name, r_out, r_in, z0, z1_back, z1_front, mat, gap_deg in (
        ("Shirt_Collar", 0.072, 0.062, 1.492, 1.528, 1.512,
         MAT["Shirt_White"], 64.0),
        ("Jacket_Collar", 0.092, 0.080, 1.472, 1.534, 1.482,
         MAT["Suit_Blue"], 104.0),
    ):
        gap = math.radians(gap_deg)
        start = 1.5 * math.pi + gap * 0.5
        end = 1.5 * math.pi + TAU - gap * 0.5
        seg = 26
        rings = []
        for i in range(seg + 1):
            t = start + (end - start) * i / seg
            frac = abs(((t - 1.5 * math.pi + math.pi) % TAU) - math.pi) / math.pi
            top = lerp(z1_front, z1_back, smoothstep(frac))
            cu, cv = math.cos(t), math.sin(t)
            outer = Vector((r_out * cu, r_out * cv, 0.0))
            inner = Vector((r_in * cu, r_in * cv, 0.0))
            rings.append([outer + Vector((0, 0, z0)),
                          outer + Vector((0, 0, top)),
                          inner + Vector((0, 0, top)),
                          inner + Vector((0, 0, z0))])
        mesh_verts = []
        mesh_faces = []
        for r in rings:
            mesh_verts.extend(r)
        for i in range(len(rings) - 1):
            a, b = i * 4, (i + 1) * 4
            for j in range(4):
                k = (j + 1) % 4
                mesh_faces.append((a + j, a + k, b + k, b + j))
        mesh_faces.append((0, 1, 2, 3))
        base = (len(rings) - 1) * 4
        mesh_faces.append((base + 3, base + 2, base + 1, base + 0))
        objects.append(mesh_object(name, mesh_verts, mesh_faces, mat, col))

    # 衬衫领尖（压在驳头上，向下收）
    for side, sign in (("L", 1.0), ("R", -1.0)):
        nodes = [[(sign * 0.012, 1.500, 0.0110), (sign * 0.012, 1.462, 0.0110)],
                 [(sign * 0.030, 1.496, 0.0095), (sign * 0.030, 1.450, 0.0095)],
                 [(sign * 0.046, 1.490, 0.0085), (sign * 0.040, 1.442, 0.0085)]]
        if sign < 0:
            nodes = list(reversed(nodes))
        objects.append(plate_grid("Collar_Point_" + side, nodes,
                                  MAT["Shirt_White"], col, thickness=0.005))

    # 两粒扣
    for index, z in enumerate((1.246, 1.192)):
        y = PROFILE.front_y(z, 0.0) - 0.005
        objects.append(sphere("Jacket_Button_%d" % (index + 1),
                              (0.0, y, z), (0.0105, 0.0038, 0.0105),
                              MAT["Button_Dark"], col, 16, 10))

    # 袋盖
    for side, sign in (("L", 1.0), ("R", -1.0)):
        cols = []
        count = 6
        for i in range(count + 1):
            x = sign * lerp(0.072, 0.166, i / count)
            cols.append((x, 0.992, 1.038))
        if sign < 0:
            cols = list(reversed(cols))
        objects.append(surface_plate("Pocket_Flap_" + side, cols, 2,
                                     MAT["Suit_Blue"], col, out=0.010,
                                     thickness=0.006))

    # 袖口三粒装饰扣（贴在袖筒前上 45° 母线）
    for side, sign in (("L", 1.0), ("R", -1.0)):
        for i, x in enumerate((0.560, 0.580, 0.600)):
            objects.append(
                sphere("Sleeve_Button_%d_%s" % (i + 1, side),
                       (sign * x, -0.0560, Z_ARM + 0.0380),
                       (0.0048, 0.0048, 0.0048), MAT["Button_Dark"], col, 12, 8)
            )

    # 后背开叉与背中缝
    objects.append(
        box("Jacket_Vent", (0.0, PROFILE.back_y(0.960, 0.0) + 0.002, 0.962),
            (0.004, 0.008, 0.104), MAT["Suit_Blue_Deep"], col)
    )
    objects.append(
        box("Jacket_Back_Seam", (0.0, PROFILE.back_y(1.250, 0.0) + 0.002, 1.250),
            (0.003, 0.008, 0.300), MAT["Suit_Blue_Deep"], col)
    )
    return objects
