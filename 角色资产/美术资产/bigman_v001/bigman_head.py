"""bigman_v001 —— 头部、五官、头发与眼镜（v2 整体重制）。

标尺（米）：下巴底 1.552 / 口线 1.596 / 鼻底 1.625 / 眼线 1.680 / 眉线 1.698 /
皮肤发际线 1.744 / 颅顶 1.786 / 含发顶 1.800。
脸宽 0.156，头深 0.181，头高（下巴→颅顶）0.234 ≈ 身高的 1/7.7。

硬汉五官四根柱子（改动前先读，这四项是互相咬合的）：
- **眉弓**：骨面净外凸 8.0 mm（`brow` 修正 0.0112）、眼窝净内凹 7.8 mm
  （`socket` 0.0102），峰值同在 z=1.7014 —— 眉下必须有一片投影才读得出"深眉弓"。
- **眉毛**：**内端低、外端高的斜直线眉**（剑眉，斜率 0.208 ≈ 11.8°），中段最宽。
  不是弧眉、也不是"两端高中段低"的折线 —— 注意"一高一低"说的是**一根眉自己**，
  不是左右两条眉。整条眉必须高于镜框上横梁（z=1.7043）才在前视图可见。
- **眼睛**：眼球 ⌀28 mm × 可见眼裂 11.9 mm 的**斜杏仁眼**。上睑倾 10°、下睑倾 7°
  → 外眼角比内眼角高 5.2 mm（上挑 = 杀气）。虹膜直径 12.8 mm 且**上缘被上睑
  压住 2.3 mm** —— 整颗圆虹膜裸露就是"豆豆眼"，这条不能回退。
- **鼻子**：鼻宽 41 mm、前伸 23.4 mm、鼻底下移到 1.625 —— 硬汉鼻要有体量。

设计约束（血泪教训，勿回退）：
1. 面部所有贴面构件（眼、眉、唇、鼻）的 y **必须**由 `face_front_y()` 反算，
   不得写死 —— 写死的 y 会把五官埋进皮肤里，渲染出来"脸是空的"。
2. 眼镜框平面必须整体位于眉面**之前**（眉面 y ≈ -0.0905），否则镜框穿进眉毛。
3. 头发是**单一闭合薄壳**（外穹面 + 内穹面 + 发际边），不是"帽子 + 独立球簇"。
   碎发质感来自沿法线的正弦位移，幅度 ±3.6 mm，共振频率取奇数谐波避免网格折痕。
4. 所有对称函数必须写成 `a = |t - 1.5π|` 的函数（`a` 天然镜像对称），
   再叠加 `sin(k·a)` 一类偶对称项；直接用 `sin(k·t)` 会破坏左右对称断言。
"""

import math

from mathutils import Vector

from bigman_lib import (MAT, TAU, lerp, loft, mesh_object, ring_plane, ring_xy,
                        smoothstep, sphere, superellipse)

Z_CHIN = 1.552
Z_MOUTH = 1.596
Z_NOSE = 1.626
Z_EYE = 1.680
Z_BROW = 1.698
Z_HAIRLINE = 1.744
Z_CROWN = 1.786
Z_TOP = 1.800

HEAD_SEGMENTS = 56


def bell(value, center, width):
    return math.exp(-((value - center) / width) ** 2)


# ---------------------------------------------------------------- 头骨
def head_stations():
    """硬汉向头骨：方下颌 + 外扩下颌角 + 厚眉骨 + 深眼窝 + 高颧骨。"""

    def chin_pad(x, y, cv):
        if cv < 0:
            y -= 0.0064 * bell(abs(x), 0.0, 0.030)
        return x, y

    def jaw_angle(x, y, cv):
        if abs(x) > 0.036:
            x *= 1.034
        return x, y

    def hollow(x, y, cv):
        if cv < 0 and abs(x) > 0.044:
            x *= 0.962
            y += 0.0056
        return x, y

    def cheek(x, y, cv):
        if cv < 0 and 0.042 < abs(x) < 0.078:
            y -= 0.0060 * bell(abs(x), 0.063, 0.020)
        return x, y

    def socket(x, y, cv):
        if cv < 0 and 0.005 < abs(x) < 0.064:
            y += 0.0102 * bell(abs(x), 0.034, 0.023)
        return x, y

    def brow(x, y, cv):
        if cv < 0 and abs(x) < 0.070:
            y -= 0.0112 * bell(abs(x), 0.031, 0.029)
        return x, y

    return [
        (Z_CHIN, 0.036, 0.078, 0.008, 4.2, chin_pad),
        (1.5620, 0.047, 0.086, 0.028, 4.1, chin_pad),
        (1.5760, 0.057, 0.090, 0.048, 3.9, jaw_angle),
        (1.5900, 0.064, 0.091, 0.062, 3.7, jaw_angle),
        (1.6060, 0.069, 0.093, 0.074, 3.3, hollow),
        (Z_NOSE, 0.072, 0.093, 0.083, 3.0, hollow),
        (1.6480, 0.075, 0.093, 0.088, 2.7, hollow),
        (1.6680, 0.077, 0.092, 0.091, 2.5, cheek),
        (Z_EYE, 0.078, 0.090, 0.093, 2.4, socket),
        (Z_BROW, 0.078, 0.090, 0.094, 2.4, brow),
        (1.7140, 0.076, 0.087, 0.094, 2.4, None),
        (1.7300, 0.073, 0.081, 0.092, 2.4, None),
        (Z_HAIRLINE, 0.069, 0.073, 0.089, 2.4, None),
        (1.7580, 0.063, 0.064, 0.083, 2.4, None),
        (1.7690, 0.054, 0.054, 0.077, 2.4, None),
        (1.7780, 0.041, 0.041, 0.066, 2.4, None),
        (Z_CROWN, 0.024, 0.024, 0.048, 2.4, None),
    ]


def head_params(z):
    st = head_stations()
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


def head_extent(z, t):
    hx, front, back, e = head_params(z)
    cu, cv = superellipse(t, e)
    x = hx * cu
    y = back * cv if cv >= 0 else -front * (-cv)
    return Vector((x, y, z))


def face_front_y(z, x):
    """面部皮肤正面的世界 y —— 五官定位的唯一依据（含下颌/眼窝/眉骨/下巴修正）。"""
    hx, front, _back, e = head_params(z)
    cu = min(abs(x) / max(hx, 1e-9), 1.0)
    cv = (1.0 - cu ** e) ** (1.0 / e) if cu < 1.0 else 0.0
    y = -front * cv
    if abs(x) > 0.044:
        y += 0.0056 * bell(z, Z_NOSE, 0.040) * smoothstep((abs(x) - 0.044) / 0.030)
    y -= 0.0060 * bell(z, 1.6680, 0.014) * bell(abs(x), 0.063, 0.020)
    y += 0.0102 * bell(z, Z_EYE, 0.021) * bell(abs(x), 0.034, 0.023)
    # 眉骨隆起（峰值 z=1.7014）：这是**颅骨**的横向棱脊，不是眉毛的形状 ——
    # 眉毛改型（现在是两端高中段低的折线）时这里不动，只保证棱脊仍在眉下。
    # 当前眉中心线均值 1.7048，离峰值 3.4 mm，仍在棱脊的支撑范围内。
    # 前突 0.0084→0.0116：眉弓净外凸 5.9 → 8.0 mm，眉下投影加深，
    # 眼窝后退 0.0078→0.0102：净内凹 6.4 → 7.8 mm。
    # 二者叠加才读得出"硬汉深眉弓"；只加其中一项会变成"肿眼皮"。
    y -= 0.0116 * bell(z, 1.7014, 0.017) * bell(abs(x), 0.031, 0.029)
    y -= 0.0064 * bell(z, 1.5580, 0.020) * bell(abs(x), 0.0, 0.030)
    return y


def build_head(col):
    rings = []
    for z, hx, front, back, e, mod in head_stations():
        rings.append(ring_xy(z, hx, front, back, e, HEAD_SEGMENTS, mod))
    return loft("Head", rings, MAT["Skin"], col, subsurf=1)


def build_neck_unused(col):
    """颈部几何由 bigman_body.build_neck 提供（保持单一来源）。"""
    return None


# ---------------------------------------------------------------- 鼻
# (z, 半宽, 相对脸面的前伸)
# 放大后的鼻：半宽 ×1.14、前伸 ×1.14、鼻底下移 1.4 mm —— 鼻宽 36 → 41 mm、
# 鼻前伸 20.4 → 23.2 mm。硬汉鼻必须是"有体量的方鼻头"，不是小巧的锥形鼻。
NOSE_STATIONS = (
    (1.6920, 0.0074, 0.0012),
    (1.6820, 0.0083, 0.0056),
    (1.6720, 0.0093, 0.0104),
    (1.6610, 0.0104, 0.0152),
    (1.6505, 0.0118, 0.0202),
    (1.6420, 0.0136, 0.0228),
    (1.6350, 0.0150, 0.0234),   # 鼻翼从这里开始外扩
    (1.6300, 0.0158, 0.0206),   # 最宽处：鼻翼（半宽 15.8 → 鼻底宽 31.6 mm）
    (1.6272, 0.0148, 0.0128),
    (1.6252, 0.0112, 0.0046),
)


def build_nose(col):
    objects = []
    rings = [_nose_ring(z, hw, p) for z, hw, p in NOSE_STATIONS]
    objects.append(loft("Nose", rings, MAT["Skin"], col, subsurf=1))
    for side, sign in (("L", 1.0), ("R", -1.0)):
        # 鼻翼**由鼻体自身外扩**（基部半宽 0.0137→0.0158）来做，这颗球只补一点点鼓起：
        # 半径 0.0042、球心 x=±0.0134（落在鼻体内侧 2.4 mm），外缘 0.0176 只比鼻体
        # 宽 1.8 mm。上一版球心压在鼻体边缘、半径 0.0066、外伸 7 mm，渲染出来是
        # "鼻头两侧各挂一颗独立小球"。
        wy = face_front_y(1.6295, 0.0134) - 0.0068
        objects.append(
            sphere("Nose_Wing_" + side, (sign * 0.0134, wy, 1.6295),
                   (0.0042, 0.0072, 0.0044), MAT["Skin"], col, 18, 12)
        )
    return objects


def _nose_ring(z, hw, protrude, segments=22):
    y_front = face_front_y(z, 0.0) - protrude
    y_back = face_front_y(z, 0.0) + 0.012
    cy = (y_front + y_back) * 0.5
    ry = (y_back - y_front) * 0.5
    pts = []
    for i in range(segments):
        t = TAU * i / segments
        cu, cv = superellipse(t, 2.2)
        pts.append(Vector((hw * cu, cy + ry * cv, z)))
    return pts


# ---------------------------------------------------------------- 口
def build_mouth(col):
    objects = []
    fy_up = face_front_y(1.6045, 0.0)
    fy_lo = face_front_y(1.5915, 0.0)
    objects.append(
        sphere("Upper_Lip", (0.0, fy_up + 0.0044, 1.6048),
               (0.0226, 0.0058, 0.0034), MAT["Lips"], col, 22, 14)
    )
    objects.append(
        sphere("Lower_Lip", (0.0, fy_lo + 0.0048, 1.5918),
               (0.0200, 0.0060, 0.0034), MAT["Lips"], col, 22, 14)
    )
    path = []
    sizes = []
    for x in (-0.0258, -0.0140, 0.0, 0.0140, 0.0258):
        z = 1.5986 + (0.0016 * (abs(x) / 0.0258) ** 2)
        path.append((x, face_front_y(z, x) - 0.0017, z))
        sizes.append((0.0021, 0.0015))
    objects.append(_ribbon("Mouth_Line", path, sizes, MAT["Skin_Dark"], col))
    return objects


def _ribbon(name, path, sizes, material, col, u_axis=(0, 1, 0),
            v_axis=(0, 0, 1), segments=12, smooth=True, subsurf=0):
    rings = []
    for p, size in zip(path, sizes):
        hw, hh = size
        rings.append(ring_plane(p, u_axis, v_axis, hw, hw, hh, hh, 2.6, segments))
    return loft(name, rings, material, col, True, True, smooth, subsurf)


# ---------------------------------------------------------------- 眼与眉
EYE_X = 0.0324
EYE_RX, EYE_RY, EYE_RZ = 0.0140, 0.0092, 0.0140

# 眼睑椭球半轴 (a, b, c)：a 沿 x（横）、b 沿 y（深）、c 沿 z（竖）。
# b 必须够大 —— 椭球睑在自身 z 极点处 y 厚度趋近 0，那一圈根本挡不住眼球，
# **真正决定眼裂的是"睑前表面与眼球前表面相交"的位置，而非睑的几何下缘**。
# 实测：几何下缘 1.6831 时，可见开口顶在 1.6856 —— 差 2.5 mm。改任一参数都要
# 用 run_build 的 eye_geometry() 复量，不能靠推。
LID_UP_RADII = (0.0180, 0.0096, 0.0056)
LID_LO_RADII = (0.0166, 0.0096, 0.0056)
Z_LID_UP = 1.6886      # 上睑球心（几何下缘 1.68309）
Z_LID_LO = 1.6702      # 下睑球心（几何上缘 1.67576）

# 眼睑倾角：外眼角上挑 10°、下睑 7°。**这是"杀气"的第一来源**——
# 水平眼裂读作"温和/困倦"，外高内低的斜眼裂才读作"锐利/攻击性"。
# 符号：绕 +Y 轴旋转 θ 时椭球最低点落在内侧（θ<0，左眼），镜像后右眼取 +θ。
LID_TILT_UP = math.radians(10.0)
LID_TILT_LO = math.radians(7.0)

# 虹膜 ⌀12.8 mm / 瞳孔 ⌀6.4 mm，虹膜中心比眼球中心高 1.4 mm。
# 上一版的问题是**眼裂太空**：一整片惨白巩膜里浮着一颗孤立的小黑点 —— 那才是
# "豆豆眼"的真正成因（不是虹膜小，是上睑一点没压住它）。现在：
#   可见开口 11.9 mm（上一版按同法折算约 15 mm）
#   虹膜上缘被上睑压掉 2.3 mm（原来 0）
#   虹膜下缘下方留 1.4 mm 巩膜 —— "下三白"，怒视的读图信号
IRIS_R = 0.0064
PUPIL_R = 0.0032
IRIS_DZ = 0.0014       # 虹膜中心相对眼球中心的 z 偏移

# 眼球前凸量 —— **决定眼睛大小**：可见部分就是眼球露在脸外面的那块球冠，
# 球冠直径 = 2√(2·R·p − p²)，R = EYE_RY = 14 mm：
#   p = 2.0 mm → 球冠 14.4 mm（上一版：小于虹膜 ⌀13.6 加上角膜缘环 → 可见区
#                            被虹膜填满，只剩一颗深色珠 = "豆豆眼"）
#   p = 5.2 mm → 球冠 21.8 mm（现用：虹膜两侧各留约 4 mm 巩膜，才是眼睛）
# 这个量是 run_build.eye_geometry 的输入，改这里必须同步那里的 `H.EYE_PROTRUDE`
# （已改为直接引用，不再是写死的数字）。
EYE_PROTRUDE = 0.0040  # 前凸 = EYE_RY − EYE_PROTRUDE = 5.2 mm


def build_eyes(col):
    """眼型总纲：**横宽纵窄的斜杏仁眼**，不是圆眼。

    1. 眼球 ⌀28 mm，**前凸 5.2 mm**（`EYE_PROTRUDE`）—— 这一项决定眼睛的大小：
       眼球是从脸面里鼓出来的球，可见部分就是它的球冠。前凸 2 mm 时球冠只有
       14.4 mm 宽，而虹膜就 ⌀13.6 mm，于是可见区被虹膜填满、只剩一颗深色珠
       （这就是"豆豆眼"的几何根因，实测出来的，不是感觉）。前凸 5.2 mm 时
       球冠 21.8 mm，虹膜两侧才留得出巩膜；
    2. 外眼角上挑 10°（下睑 7°）→ 外眼角比内眼角高 5.2 mm；
    3. 上睑压住虹膜上缘 2.3 mm —— 去豆豆眼、出杀气的头号手段；
    4. 虹膜下缘留 1.4 mm 巩膜（下三白）—— 怒视读图信号；
    5. 虹膜分两层（`Iris` 中棕 + `Iris_Ring` 近黑外圈）—— 深色角膜缘环把虹膜
       从巩膜上"切"出来，单色虹膜无论多深都读作玻璃珠；
    6. 角膜高光点落在瞳孔边缘的外上方（不是正上方）；
    7. 上眼睑线内粗（2.6 mm）外细（1.5 mm）、随睑裂一起上挑。

    全部走镜像对称（左眼 +x 侧与右眼 -x 侧角向相反），对称门禁覆盖。
    """
    objects = []
    for side, sign in (("L", 1.0), ("R", -1.0)):
        x = sign * EYE_X
        surf = face_front_y(Z_EYE, x)
        ball_y = surf + EYE_PROTRUDE
        iris_z = Z_EYE + IRIS_DZ
        objects.append(
            sphere("Eye_White_" + side, (x, ball_y, Z_EYE),
                   (EYE_RX, EYE_RY, EYE_RZ), MAT["Eye_White"], col, 28, 22)
        )
        objects.append(
            sphere("Iris_Ring_" + side, (x, ball_y - 0.0084, iris_z),
                   (IRIS_R + 0.0004, 0.0024, IRIS_R + 0.0004),
                   MAT["Iris_Ring"], col, 22, 16)
        )
        objects.append(
            sphere("Iris_" + side, (x, ball_y - 0.0086, iris_z),
                   (IRIS_R, 0.0026, IRIS_R), MAT["Iris"], col, 22, 16)
        )
        objects.append(
            sphere("Pupil_" + side, (x, ball_y - 0.0104, iris_z),
                   (PUPIL_R, 0.0018, PUPIL_R), MAT["Pupil"], col, 16, 12)
        )
        objects.append(
            sphere("Eye_Glint_" + side,
                   (x + sign * 0.0032, ball_y - 0.0110, iris_z + 0.0030),
                   (0.0018, 0.0012, 0.0018), MAT["Eye_Glint"], col, 14, 10)
        )
        objects.append(
            sphere("Eyelid_Upper_" + side, (x, ball_y - 0.0004, Z_LID_UP),
                   LID_UP_RADII, MAT["Skin"], col, 24, 18,
                   rot=(0.0, -sign * LID_TILT_UP, 0.0))
        )
        objects.append(
            sphere("Eyelid_Lower_" + side, (x, ball_y - 0.0006, Z_LID_LO),
                   LID_LO_RADII, MAT["Skin"], col, 24, 18,
                   rot=(0.0, -sign * LID_TILT_LO, 0.0))
        )
        objects.append(_eye_line(x, ball_y, sign, side, col))
    return objects


def _eye_line(cx, ball_y, sign, side, col):
    """上眼睑线：沿眼球面走的一条深色弧，随睑裂一起外高内低。

    起点高度取**可见开口顶（1.6856）而不是睑的几何下缘（1.6831）**——
    否则这条线会沉到巩膜里面去，读作"眼睛上缘有一道黑线浮着"。
    y 由**眼球面反算**（不是脸面）—— 线要浮在眼白之前，否则被眼白球挡住。
    """
    path = []
    sizes = []
    steps = 9
    for i in range(steps):
        u = -1.0 + 2.0 * i / (steps - 1)
        dx = u * 0.0100
        # 外侧（u·sign = +1）抬高 2.6 mm，内侧同样下沉；中间再拱起 1.2 mm
        z = 1.68550 + 0.0026 * (u * sign) + 0.0012 * (1.0 - u * u)
        dz = z - Z_EYE
        inner = 1.0 - (dx / EYE_RX) ** 2 - (dz / EYE_RZ) ** 2
        y = ball_y - EYE_RY * math.sqrt(max(inner, 0.0)) - 0.0012
        path.append((cx + dx, y, z))
        sizes.append((0.0013, 0.00105 * (1.0 - 0.30 * (u * sign))))
    return _ribbon("Eye_Line_Upper_" + side, path, sizes, MAT["Brow"], col)


# 眉型：**一条斜的直线眉 —— 内端低、外端高**（剑眉），中段最宽。
# 五个控制点严格落在**同一条直线**上（斜率 0.208，≈11.8°），不是折线、不是弧线。
#
# 上一版读错了主人的意思：做成了"两端高、中段低"的折线（V 形），那是把
# **一根眉**当成了**两条眉**来理解。主人要的是**一根眉自己一高一低**。
#
# 数值边界（咬在一起，改一个先读另三个）：
#   1. **镜框上横梁占 z ∈ [1.7001, 1.7043]、x ∈ [0.0058, 0.0590]**，而眉的 x 范围
#      0.0078~0.0578 完全落在其中 —— 眉在**前视图**里只有高于 1.7043 的那部分看得见，
#      低于它的部分被横梁挡掉（眉在镜框之后，y 更靠后）。所以：
#        · 中段下缘 1.7044 —— 刚好齐平横梁上沿，中段整条可见（这是全眉的最低容许点）；
#        · 内端下缘 1.7018 主动让横梁吃掉 2.5 mm —— 内端本来就该细，被吃一点反而
#          读作"眉从镜框后面长出来"，比硬抬一条完整的细眉更自然。
#      曾实测过：中段下缘一旦压到 1.7001 以下，那一截会掉进镜片开口里，
#      渲染成"镜片内浮着一块黑眉"。
#   2. 外端 1.7162（上缘 1.7190）距**太阳穴发际线 1.7239** 只剩 4.9 mm —— 上限。
#   3. 全眉抬升 10.4 mm（内→外），这是"一高一低"的量。
#   4. 中段 13.2 mm 高（最宽），向两端收到 8.0 / 5.6 mm 收尖。
BROW_PATH = ((0.0078, 1.7058), (0.0200, 1.7083), (0.0330, 1.7110),
             (0.0460, 1.7137), (0.0578, 1.7162))
BROW_SIZES = ((0.0018, 0.0040), (0.0021, 0.0054), (0.0022, 0.0066),
              (0.0019, 0.0048), (0.0013, 0.0028))


def build_brows(col):
    objects = []
    for side, sign in (("L", 1.0), ("R", -1.0)):
        path = [(sign * x, face_front_y(z, sign * x) - 0.0022, z)
                for x, z in BROW_PATH]
        objects.append(_ribbon("Eyebrow_" + side, path, BROW_SIZES,
                               MAT["Brow"], col))
    return objects


def build_ears(col):
    """耳：整只向后倾 11°，形成耳轮前倾 / 耳尖后收的自然姿态。"""
    tilt = (math.radians(-11.0), 0.0, 0.0)
    objects = []
    for side, sign in (("L", 1.0), ("R", -1.0)):
        objects.append(
            sphere("Ear_" + side, (sign * 0.0756, 0.0080, 1.6600),
                   (0.0062, 0.0148, 0.0278), MAT["Skin"], col, 20, 16,
                   rot=tilt)
        )
        objects.append(
            sphere("Ear_Inner_" + side, (sign * 0.0790, 0.0026, 1.6612),
                   (0.0030, 0.0082, 0.0150), MAT["Skin_Dark"], col, 16, 12,
                   rot=tilt)
        )
        objects.append(
            sphere("Ear_Lobe_" + side, (sign * 0.0750, 0.0050, 1.6348),
                   (0.0056, 0.0084, 0.0078), MAT["Skin"], col, 16, 12,
                   rot=tilt)
        )
    return objects


# ---------------------------------------------------------------- 头发
HAIR_ROWS = 12

# 侧分（三七分）分缝所在的带符号前额偏角：+0.62 rad ≈ 分缝落在 x≈+0.043（角色左侧）。
# 因而 +x 侧是"少的一侧"（向后梳、露额角），-x 侧是"多的一侧"（斜刘海压住额角）。
A_PART = 0.62

# 发际线控制点：(a, z)，a = 距前额中央的角距（弧度，0 前 / π 后）。
# 前额整体较上一版下移 7 mm —— 大背头是"发际线高到看不见头发"，分头要有刘海层。
HAIR_KNOTS = (
    (0.0000, 1.7490),
    (0.2200, 1.7505),
    (0.4800, 1.7490),
    (0.7800, 1.7360),
    (1.0500, 1.6990),   # 太阳穴
    (1.3200, 1.6630),   # 鬓角：向前下方探出，落到耳前
    (1.5700, 1.6880),   # 耳上：必须贴住耳上缘（1.6878）。
                        # 原值 1.6980 高出耳顶 10 mm，侧视图露出一块头皮，
                        # 读作"发际线后移"。
    (1.9000, 1.6870),
    (2.3000, 1.6790),
    (2.7200, 1.6700),
    (3.1416, 1.6640),
)


def _catmull(p0, p1, p2, p3, u):
    return 0.5 * ((2.0 * p1)
                  + (-p0 + p2) * u
                  + (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * u * u
                  + (-p0 + 3.0 * p1 - 3.0 * p2 + p3) * u * u * u)


def _knot_value(knots, a):
    n = len(knots)
    if a <= knots[0][0]:
        return knots[0][1]
    if a >= knots[-1][0]:
        return knots[-1][1]
    for i in range(n - 1):
        a0, v0 = knots[i]
        a1, v1 = knots[i + 1]
        if a0 <= a <= a1:
            u = (a - a0) / (a1 - a0)
            pm1 = knots[max(i - 1, 0)][1]
            pp1 = knots[min(i + 2, n - 1)][1]
            return _catmull(pm1, v0, v1, pp1, u)
    return knots[-1][1]


def _hair_angle(t):
    """无符号角距（0 = 前额正中）。所有**对称**的修正项都必须用它。"""
    return abs(((t - 1.5 * math.pi + math.pi) % TAU) - math.pi)


def _front_offset(t):
    """带符号前额偏角：0 = 正中，正 = 角色左侧（+x），负 = 角色右侧（-x）。

    侧分是**有意的不对称造型**，所有破坏左右对称的项都只允许用这个量。
    头发不在 `run_assertions` 的 `_L/_R` 成对检查里，所以不会拖红门禁。
    """
    ang = (t - 1.5 * math.pi) % TAU
    if ang > math.pi:
        ang -= TAU
    return ang


def hair_boundary_z(t):
    a = _hair_angle(t)
    ang = _front_offset(t)
    z = _knot_value(HAIR_KNOTS, a)
    # 前额碎发下探（对称）
    fringe = 0.0042 * math.exp(-(a / 0.45) ** 2) * (0.55
                                                    + 0.45 * math.cos(5.2 * a))
    # 侧分·多的一侧（-x）：发际线下压 8 mm，形成斜刘海压住额角
    sweep = -0.0080 * math.exp(-((ang + 0.30) / 0.62) ** 2)
    # 侧分·分缝处的尖凹：缝的起点必须落在发际线上，否则"分头"读不出来
    cut = -0.0058 * math.exp(-((ang - A_PART) / 0.16) ** 2)
    # 发际线锯齿 —— 避免"锅盖边"的干净弧线（对称项）
    chop = (0.0026 * math.sin(11.0 * a + 0.60)
            + 0.0016 * math.sin(19.0 * a + 2.10))
    return z - fringe + sweep + cut + chop


def _skull_normal(z, t, dz=0.0045, dt=0.030):
    p = head_extent(z, t)
    du = head_extent(z, t + dt) - head_extent(z, t - dt)
    dv = (head_extent(min(z + dz, Z_CROWN), t)
          - head_extent(max(z - dz, 1.580), t))
    n = du.cross(dv)
    if n.length < 1e-9:
        return Vector((0.0, 0.0, 1.0))
    n.normalize()
    if n.dot(Vector((0.0, 0.0, 1.700)) - p) > 0.0:
        n = -n
    return n


def _hair_noise(a, s, ang):
    """沿法线的位移。波纹相位取**距分缝的角距**，于是发丝读作"从分缝向两侧梳开"。

    `|d|` 在 d=0 处不可导 —— 那正是一条天然折痕，分缝就长在上面。
    """
    d = ang - A_PART
    ad = abs(d)
    wave = (0.0034 * math.sin(ad * 17.0 + s * 4.2)
            + 0.0022 * math.sin(ad * 27.0 - s * 6.2 + 1.7)
            + 0.0015 * math.sin(ad * 9.0 + s * 7.6 + 0.4))
    # 分缝凹槽：宽约 0.155 rad、最深 7.2 mm。
    # 前额段（s≈0）必须已有 55% 深度 —— 若让凹槽从 s=0.4 才渐入，
    # 分缝在额头上根本看不见，侧分就只剩"后脑一道沟"。
    part = (0.0072 * math.exp(-(d / 0.155) ** 2)
            * (0.55 + 0.45 * smoothstep(s / 0.45)))
    return wave - part


def _hair_thickness(s, a, ang):
    base = lerp(0.0028, 0.0136, smoothstep(min(1.0, s * 1.45)))
    base += 0.0018 * smoothstep((a - 1.30) / 1.30)
    # 侧分·多的一侧（-x）加厚 4.4 mm 做出斜刘海体量；分缝侧贴颅
    base += 0.0044 * math.exp(-((ang + 0.42) / 0.70) ** 2) * min(1.0, s * 1.25)
    return base


def build_hair(col):
    """头发 = 单一闭合薄壳（外穹面 + 内穹面 + 发际边），不再用独立球簇。"""
    n = HEAD_SEGMENTS
    rows = HAIR_ROWS

    def sample(t, s):
        a = _hair_angle(t)
        ang = _front_offset(t)
        zb = hair_boundary_z(t)
        z = min(max(lerp(zb, Z_CROWN, s ** 0.90), zb), Z_CROWN)
        p = head_extent(z, t)
        nrm = _skull_normal(z, t)
        th = _hair_thickness(s, a, ang)
        # 最低也要保留 35% 波纹：原先用 smoothstep(s*2.4)，s<0.42 几乎无起伏，
        # 额顶和鬓角就成了一块光滑塑料壳 —— 那正是"头盔感"的来源。
        wobble = _hair_noise(a, s, ang) * (0.35 + 0.65 * smoothstep(s * 1.8))
        return p + nrm * (th + wobble), p + nrm * 0.0012

    outer_rings = []
    inner_rings = []
    for r in range(rows + 1):
        s = r / rows
        oring, iring = [], []
        for i in range(n):
            t = TAU * i / n
            o, ii = sample(t, s)
            oring.append(o)
            iring.append(ii)
        outer_rings.append(oring)
        inner_rings.append(iring)

    o_apex = sum(outer_rings[-1], Vector()) / n
    i_apex = sum(inner_rings[-1], Vector()) / n
    o_apex = Vector((o_apex.x, o_apex.y, o_apex.z + 0.0022))
    i_apex = Vector((i_apex.x, i_apex.y, i_apex.z + 0.0018))

    verts = []
    for ring in outer_rings:
        verts.extend(ring)
    n_outer = len(verts)
    for ring in inner_rings:
        verts.extend(ring)
    o_apex_i = len(verts)
    verts.append(o_apex)
    i_apex_i = len(verts)
    verts.append(i_apex)

    faces = []
    nrows = len(outer_rings)
    for r in range(nrows - 1):
        a0 = r * n
        b0 = (r + 1) * n
        for i in range(n):
            k = (i + 1) % n
            faces.append((a0 + i, a0 + k, b0 + k, b0 + i))
            faces.append((n_outer + a0 + i, n_outer + b0 + i,
                          n_outer + b0 + k, n_outer + a0 + k))
    top = (nrows - 1) * n
    for i in range(n):
        k = (i + 1) % n
        faces.append((top + i, top + k, o_apex_i))
        faces.append((n_outer + top + i, i_apex_i, n_outer + top + k))
    for i in range(n):
        k = (i + 1) % n
        faces.append((i, n_outer + i, n_outer + k, k))

    return [mesh_object("Hair_Mass", verts, faces, MAT["Hair_Black"], col,
                        smooth=True, subsurf=1)]


# 斜刘海路径：(x, z, 半厚, 半宽, 浮出额面量)。
# y 由 face_front_y 反算；浮出量逐点给出 —— 根部几乎贴着发壳（否则会与发壳
# 之间出现一条可见断层，读作"额头贴了条黑胶带"），梢部才略微抬起。
HAIR_SWEEP_KNOTS = (
    (0.0370, 1.7464, 0.0042, 0.0092, 0.0010),   # 根：紧贴分缝的 -x 侧（别压进缝心）
    (0.0160, 1.7402, 0.0058, 0.0144, 0.0024),   # 最宽处 —— 这束的体量感来源
    (-0.0090, 1.7348, 0.0056, 0.0140, 0.0028),
    (-0.0330, 1.7302, 0.0048, 0.0114, 0.0028),
    (-0.0530, 1.7266, 0.0034, 0.0070, 0.0028),  # 梢：收尖搭在额角
)


def build_hair_sweep(col):
    """侧分·斜刘海：一束从分缝起点向 -x 侧斜扫过额头的独立发束。

    单靠发壳上的一道凹槽，"分头"很容易被读成"头顶有条缝"；
    真正让人一眼认出侧分的是**多的一侧压下来的那层刘海**。
    故发壳负责体量与分缝，本束负责"斜"这个读图信号。
    """
    path = []
    sizes = []
    for x, z, thick, width, lift in HAIR_SWEEP_KNOTS:
        path.append((x, face_front_y(z, x) - lift, z))
        sizes.append((thick, width))
    return [_ribbon("Hair_Sweep", path, sizes, MAT["Hair_Black"], col,
                    segments=14, subsurf=1)]


# ---------------------------------------------------------------- 眼镜
# FRAME_X 必须与 EYE_X 相等 —— 差 1 mm 框就会偏心，读作"眼镜戴歪"。
FRAME_X = EYE_X
FRAME_Y = -0.0986          # 必须整体位于眉面（前表面 y≈-0.0946）之前，再往前就"浮空"
FRAME_Z = Z_EYE + 0.0034   # 框内缘上 1.6997 / 下 1.6671 —— 恰好包住上下睑球（勿下移）


def build_glasses(col):
    """细黑方框眼镜。**不建镜片几何** —— 薄片镜片在 EEVEE 里无论怎么调材质
    都会被高光打成白板，把眼睛整个盖掉（实测两轮）。留空反而读作"透明镜片"，
    而且眼睛可见。镜片材质 Lens_Glass 保留备用，勿恢复调用。"""
    objects = []
    for side, sign in (("L", 1.0), ("R", -1.0)):
        objects.append(
            _rect_ring("Glasses_Frame_" + side,
                       (sign * FRAME_X, FRAME_Y, FRAME_Z),
                       0.0266, 0.0188, 0.0021, MAT["Glasses_Black"], col)
        )
    # 鼻梁架：搭在两只镜框上边之间（框上边管心 z=1.7022），故 z 取 1.702 一带；
    # 这一高度正好从眉毛（x=0.008~0.015 处 z=1.696~1.700）上方掠过，不会压眉。
    objects.append(
        _ribbon("Glasses_Bridge",
                [(-0.0130, -0.1002, 1.7018), (-0.0065, -0.0972, 1.7012),
                 (0.0, -0.0962, 1.7008), (0.0065, -0.0972, 1.7012),
                 (0.0130, -0.1002, 1.7018)],
                [(0.0018, 0.0018)] * 5, MAT["Glasses_Black"], col,
                u_axis=(0, 0, 1), v_axis=(0, 1, 0), segments=10)
    )
    for side, sign in (("L", 1.0), ("R", -1.0)):
        path = [(sign * 0.0604, -0.0958, 1.6912),
                (sign * 0.0766, -0.0570, 1.6930),
                (sign * 0.0818, -0.0160, 1.6895),
                (sign * 0.0804, 0.0060, 1.6820)]
        # 镜腿高度压到 6.8 mm（原 10 mm）—— 3/4 视角下 10 mm 的腿会被透视放大成
        # 一块盖住镜片左上的黑三角，读作"头发插进镜片里"。
        sizes = [(0.0016, 0.0034), (0.0016, 0.0035), (0.0016, 0.0035),
                 (0.0014, 0.0030)]
        objects.append(
            _ribbon("Glasses_Temple_" + side, path, sizes, MAT["Glasses_Black"],
                    col, u_axis=(0, 1, 0), v_axis=(0, 0, 1), segments=10)
        )
    return objects


def _rect_ring(name, center, half_w, half_h, tube_r, material, col):
    cx, cy, cz = center
    steps = 32
    points = []
    for i in range(steps):
        t = TAU * i / steps
        cu, cv = superellipse(t, 3.4)
        points.append(Vector((cx + half_w * cu, cy, cz + half_h * cv)))
    points.append(points[0])
    rings = []
    for i, p in enumerate(points):
        if i == 0:
            tangent = points[1] - points[0]
        elif i == len(points) - 1:
            tangent = points[-1] - points[-2]
        else:
            tangent = points[i + 1] - points[i - 1]
        tangent.normalize()
        u_axis = tangent.cross(Vector((0, 1, 0)))
        if u_axis.length < 1e-6:
            u_axis = Vector((0, 0, 1))
        u_axis.normalize()
        v_axis = u_axis.cross(tangent).normalized()
        rings.append(ring_plane(p, u_axis, v_axis, tube_r, tube_r, tube_r,
                                tube_r, 2.0, 10))
    return loft(name, rings, material, col, False, False)


def _lens(name, center, half_w, half_h, col):
    from bigman_lib import box

    return box(name, center, (half_w * 2.0, 0.0014, half_h * 2.0),
               MAT["Lens_Glass"], col, bevel=0.0038, bevel_segments=3,
               smooth=True)
