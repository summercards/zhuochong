"""anim_wall_hit —— D19 `Wall_Hit` 撞墙。

清单原文：「**后背** / 正面撞墙后**短暂停留**再下落」。

★★★ 本支是全项目**第一支引入「世界实体」**的动画：前 55 支的世界里**只有地面（z = 0）**。
    本支第一次要在世界里立一堵**墙**（法线 = −Y 的竖直平面，立在角色**身后** +Y）。
    ⟹ 必须新建一整套「**会失败**的」墙判据（§1 风险 1）。本项目铁律：
    **没有任何判据盯着的约束等于不存在** —— 若 `wall_no_penetration_ok` 在反向验证里
    不红，这堵墙就是**装饰**，本支不算完成。

★★ 三条接缝（计划 §0）：
   ① 上游**姿态**：首帧**逐位** = `Launch_Hit@34`（D12 末帧，SELF_HOLD 锁存姿态）。
      ★ 上游**动量**：D12 携带 `vy = 0`（击飞距离是**招式数值**，D12 已登记不烘进动画）。
      ⟹ 本支的 +Y 位移是**本支自己烘的**，理由：**墙是「世界」的一部分**，
         「撞墙」是**位移事件**（必须走到墙上才叫撞墙），与 D12/D13「位移交给引擎」的
         立场**不同**。已登记 `root_motion_m = [0, +Y]` + `wall_y_m` 到 `meta`。
   ② 上游**弹道**：D12/D13 都落在**同一条共享解析抛物线**上 ⟹ 本支 f0 逐位续上，
      `T_PHASE = 31.5`（与 D13 **完全相同**），撞墙帧之前残差 ≤ 2.0 mm。
   ③ 下游**落点**：末帧**离开墙面、正在下落**（`end_vz < 0`），交给 D14/D15/D16。
      ★ **不**在本支硬接一个"落地"。

★★ §1 本支唯一的真风险：**「墙」是硬的吗？** —— 三条守卫：
   · `wall_no_penetration_ok`：**全帧**任一顶点 `y ≤ wall_eff + 5 mm`（墙硬的**唯一**守卫）；
   · `wall_back_first_ok`：**撞墙帧接触墙面的对象必须是"后背族"**（清单原文要「后背撞墙」）
     —— 首 55 支里脚/手总是最靠后的，本支必须**用姿态把它们收到前面去**；
   · `wall_stay_ok`：停留段骨盆 **y 钉住**、**z 在下落** ⟹ 证明是"**贴着墙往下滑**"
     而不是"原路弹回"。

★★ 本支技术件 ①：**竖直通道由"单条弹道"改成"四段分段"**
   `弹道(0..WALL_HIT) → 硬直冻结(WALL_HIT..HITSTOP_END) → 贴墙下滑(..DETACH) → 新抛物线(..END)`

★★ 本支技术件 ②：**命中停顿 = 姿态 + 位置**全冻（与 D13「只冻姿态」**相反**）
   墙是**支撑物** ⟹ 撞墙帧全冻 3 帧是物理正确的（§6 硬约束："命中关键帧做 2~4 帧完全停顿"）。
   构造式实现：姿态**逐位复用** + `pelvis_z_at/y_at` 在该段返回**常量**。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python anim_wall_hit.py
    SKIP_RENDER=1    只跑门禁不渲图（迭代用）
    D19_TRACE=1      逐帧打印驱动标量 / z / y / 后缘（调参用）

反向验证（§4 第 7 步，九组）：
    D19_TP_SEAM_ZERO=1        ① 首帧改零位        ⟹ `seam_in_ok`
    D19_TP_WALLFAR=1          ② 墙挪远 150 mm     ⟹ `wall_contact_ok`
    D19_TP_WALLNEAR=1         ③ 墙挪近 60 mm      ⟹ `wall_no_penetration_ok`（★ 最关键）
    D19_TP_NOHITSTOP=1        ④ 抽掉停顿          ⟹ `wall_hitstop_ok`
    D19_TP_BOUNCEBACK=1       ⑤ 撞墙后原路弹回    ⟹ `wall_stay_ok`
    D19_TP_NOFALL=1           ⑥ 撞墙后不下落      ⟹ `wall_fall_ok`
    D19_TP_ENDZERO=1          ⑦ 末帧给静止        ⟹ `end_vz_sign_ok`
    D19_TP_SIDEDRIFT=1        ⑧ 侧向漂移          ⟹ `wall_x_ok`（像素探针看不见 X，唯一守卫）
    D19_TP_BALLISTIC_BREAK=1  ⑨ 打断弹道          ⟹ `ballistic_ok`
"""

import json
import math
import os
import struct
import sys

import bpy
from mathutils import Quaternion, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A                     # noqa: E402
import anim_jump_start as JS             # noqa: E402
import anim_jump_fall as JFE             # noqa: E402
import anim_ultimate_end as UE           # noqa: E402
import anim_crouch as CR                 # noqa: E402
import probe_c12_baseline as P           # noqa: E402
import probe_d01_guard as PD             # noqa: E402

NAME = "Wall_Hit"
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"
SIDES = ("L", "R")

# ★ 接缝真源：上游 D12 `Launch_Hit` 的落盘 action + 末帧号
SEAM_ACTION = os.environ.get("D19_SEAM_ACTION", "Launch_Hit")
SEAM_FRAME = int(os.environ.get("D19_SEAM_FRAME", "34"))
D12_T_ORIGIN = 2.50


def _env_i(key, default):
    try:
        return int(os.environ.get(key, default))
    except (TypeError, ValueError):
        return default


def _env_f(key, default):
    try:
        return float(os.environ.get(key, default))
    except (TypeError, ValueError):
        return default


def _env_b(key):
    return os.environ.get(key, "0").strip() not in ("", "0", "false", "False")


def _f32(value):
    """量化到 float32 —— F-Curve 关键帧就是按 float32 存的（与 D02~D12 同源）。"""
    return struct.unpack("<f", struct.pack("<f", float(value)))[0]


def _keyed_bones(action):
    rot, loc = set(), set()
    for curve in action.fcurves:
        path = curve.data_path
        if not path.startswith('pose.bones["'):
            continue
        name = path.split('"')[1]
        if path.endswith("rotation_euler"):
            rot.add(name)
        elif path.endswith("location"):
            loc.add(name)
    return rot, loc


def _lin(keys, frame):
    """分段**线性**取值。★ 值为 `None` 的锚点**直接丢掉**（表示"由驱动标量接管，
    本通道不定义"）—— 否则 `None * t` 会炸。"""
    keys = tuple(item for item in keys if item[1] is not None)
    if not keys:
        return 0.0
    if frame <= keys[0][0]:
        return keys[0][1]
    if frame >= keys[-1][0]:
        return keys[-1][1]
    for index in range(len(keys) - 1):
        xa, ya = keys[index]
        xb, yb = keys[index + 1]
        if xa <= frame <= xb:
            if xb == xa:
                return yb
            return ya + (yb - ya) * (frame - xa) / float(xb - xa)
    return keys[-1][1]


# =============================================================== 时间轴
#   ★ 帧预算（计划 §2「待实测」，硬上界 40；本支取 34 = 0.567 s @60fps）：
#     来程 14 帧（弹道 · 抛物线上 z 1931.9 → 1514.6 mm，够高、够看）+
#     硬直 3 帧（§6 要求 2~4）+ 贴墙下滑 9 帧（"短暂停留"）+
#     自由下落 8 帧（末帧仍在空中，交给 D14/D15/D16）。
TOTAL = _env_i("D19_TOTAL", 34)
START = 0
ENTER = _env_i("D19_ENTER", 2)               # 进入判据窗口
WALL_HIT = _env_i("D19_WALL_HIT", 14)        # ★ 撞墙帧（后背首次触墙）
HITSTOP_END = _env_i("D19_HITSTOP_END", 16)  # 硬直末帧（含）
SLIDE_START = HITSTOP_END + 1
SLIDE_END = _env_i("D19_SLIDE_END", 25)      # 贴墙下滑末帧
DETACH = SLIDE_END + 1                       # ★ 离开墙面（airborne 段下界）
FALL_MID = _env_i("D19_FALL_MID", 30)
CANCEL = SLIDE_END
END = TOTAL

# =============================================================== 共享弹道
# ★ 相位**与 D13 完全相同**（`T_PHASE = SEAM_FRAME − T_ORIGIN = 31.5`）：
#   本支 frame f ⟺ 解析时刻 t = (f + 34) − T_ORIGIN ⟹ f0 与 D12 f34 同一个解析点。
T_PHASE = float(SEAM_FRAME) - D12_T_ORIGIN   # 31.5
BALLISTIC_TOL_MM = _env_f("D19_BALLISTIC_TOL", 2.0)
Z_PELVIS_REST = 0.900


def ball_z(frame):
    """★ 与 A10/A11/A12/B08/D12/D13 **同一个**解析弹道。"""
    t = T_PHASE + float(frame)
    return JS.TAKEOFF_PELVIS_Z + JS.TAKEOFF_SPEED * t - 0.5 * JS.G_PER_FRAME * t * t


def ball_vz(frame):
    return JS.TAKEOFF_SPEED - JS.G_PER_FRAME * (T_PHASE + float(frame))


D12_END_VZ_MM = (ball_z(0) - ball_z(-1)) * 1000.0     # = −9.388889 mm/帧
G_MM = JS.G_PER_FRAME * 1000.0                        # = 2.722222 mm/帧²
G_M = JS.G_PER_FRAME
Z_APEX = JS.TAKEOFF_PELVIS_Z + JS.APEX_RISE
F_APEX_D12 = D12_T_ORIGIN + JS.TAKEOFF_SPEED / JS.G_PER_FRAME
F_APEX_LOCAL = F_APEX_D12 - float(SEAM_FRAME)

Z_WALL_BALL = ball_z(WALL_HIT)                        # 撞墙帧的弹道 z（= 冻结值）

# =============================================================== ★★ 墙常量
# ★ `WALL_Y_M` 是**实测派生**（两遍法）：先跑一遍读出 `wall_hit_rear_all_mm`
#   （= 撞墙帧全网格 +Y 极值），再把墙立在**那一点**上并冻成常量。**不许拍脑袋**。
#   ① 第一遍（墙先随便立在 0.665）：实测 f14 全网格 +Y 极值 = **705.561 mm**
#      （对象 `Hair_Mass`，即后脑/头发 —— 后仰拱姿态下它是身体最后侧的面）。
#      同时实测：0~34 帧全网格 +Y 极值 **就出现在 f14**（705.561）。
#   ② 第二遍：把墙冻在 **0.705561 m** ⟹ f14 后缘恰好贴墙（穿透 0.000 mm、贴合间隙 0.000 mm），
#      且 f13 后缘 684.1 mm < 705.06 mm（触墙带宽 0.5 mm）⟹ **首次触墙帧唯一 = 14**。
WALL_Y_M = _env_f("D19_WALL_Y", 0.705561)     # ★ 第一遍实测 705.561 mm 派生，勿手改
PELVIS_Y_START = _env_f("D19_Y0", 0.026)      # = D12 末帧骨盆 y（接缝逐位对齐）
PELVIS_Y_WALL = _env_f("D19_Y_WALL", 0.320)   # 撞墙帧骨盆 y
# ★ 离墙段的骨盆 y：**必须缓退**。第一版把 y 从 320 一帧内拉到 268（−52 mm/帧），
#   实测后果：① f26 `shin.L` 单帧转 17.257°（`no_snap_stop_ok` 红，上界 6°）；
#   ② `no_teleport` 红。物理上人被墙"放开"后主要是**竖直**下落（重力竖直），
#   水平后退是身体前倾带出来的**缓慢**量，不该是瞬移。
PELVIS_Y_DETACH = _env_f("D19_Y_DETACH", 0.318)   # 离墙瞬间几乎还贴在墙线上
PELVIS_Y_END = _env_f("D19_Y_END", 0.252)     # 末帧骨盆 y（缓退到此处）

Y_KEYS = ((START, PELVIS_Y_START), (WALL_HIT, PELVIS_Y_WALL),
          (HITSTOP_END, PELVIS_Y_WALL), (SLIDE_END, PELVIS_Y_WALL),
          (DETACH, PELVIS_Y_DETACH), (FALL_MID, 0.288), (END, PELVIS_Y_END))

# ★ 贴墙下滑的降幅（米）：**摩擦** ⟹ 明显慢于自由落体（自由落体 9 帧要掉 ~500 mm）。
SLIDE_DROP_M = _env_f("D19_SLIDE_DROP", 0.220)
SLIDE_POW = _env_f("D19_SLIDE_POW", 1.35)     # >1 ⟹ 越滑越快（先涩后顺）


def _slide_drop(frame):
    u = (float(frame) - HITSTOP_END) / float(DETACH - HITSTOP_END)
    u = max(0.0, min(1.0, u))
    return SLIDE_DROP_M * (u ** SLIDE_POW)


# ★ 离墙瞬间的竖速 = 下滑段最后一步的差分（新抛物线接着它走，**位置与速度都连续**）。
_SLIDE_EXIT_VZ = -(SLIDE_DROP_M - _slide_drop(SLIDE_END))


# =============================================================== 反向验证旋钮
SEAM_ZERO = _env_b("D19_TP_SEAM_ZERO")
ZERO_ACTION = "Idle_01" if SEAM_ZERO else SEAM_ACTION
ZERO_FRAME = 0 if SEAM_ZERO else SEAM_FRAME

WALLFAR = _env_b("D19_TP_WALLFAR")            # ② 墙挪远（判据尺子动，动画不动）
WALLFAR_MM = _env_f("D19_TP_WALLFAR_MM", 150.0)
WALLNEAR = _env_b("D19_TP_WALLNEAR")          # ③ 墙挪近（判据尺子动）
WALLNEAR_MM = _env_f("D19_TP_WALLNEAR_MM", 60.0)
NO_HITSTOP = _env_b("D19_TP_NOHITSTOP")       # ④ 抽掉停顿
BOUNCEBACK = _env_b("D19_TP_BOUNCEBACK")      # ⑤ 撞墙后原路弹回
NO_FALL = _env_b("D19_TP_NOFALL")             # ⑥ 撞墙后不下落
END_ZERO = _env_b("D19_TP_ENDZERO")           # ⑦ 末帧给静止
SIDEDRIFT = _env_b("D19_TP_SIDEDRIFT")        # ⑧ 侧向漂移
SIDEDRIFT_MM = _env_f("D19_TP_SIDEDRIFT_MM", 90.0)
BALLISTIC_BREAK = _env_b("D19_TP_BALLISTIC_BREAK")   # ⑨ 打断弹道
BALLISTIC_BREAK_MM = _env_f("D19_TP_BREAK_MM", 40.0)
TRACE = _env_b("D19_TRACE")


def wall_eff():
    """★ 判据用的**有效墙面** —— 反向验证 ②③ 只动这把**尺子**，不动动画。"""
    y = WALL_Y_M
    if WALLFAR:
        y += WALLFAR_MM / 1000.0
    if WALLNEAR:
        y -= WALLNEAR_MM / 1000.0
    return y


def side_drift(frame):
    """⑧ 侧向漂移（默认 0）。"""
    if not SIDEDRIFT:
        return 0.0
    return SIDEDRIFT_MM / 1000.0 * math.sin(
        math.pi * min(1.0, max(0.0, float(frame) / float(TOTAL))))


def pelvis_x_at(frame):
    return side_drift(frame)


def pelvis_y_at(frame):
    """骨盆世界 y（米）。★ 接近 → 钉墙 → 离墙（前倾）三段式。"""
    if BOUNCEBACK and frame > HITSTOP_END:
        # ⑤ 「原路弹回」：撞墙后 y 反向退回（物理上错，用来证明 `wall_stay_ok` 抓得住）
        return PELVIS_Y_WALL - (PELVIS_Y_WALL - PELVIS_Y_START) * (
            (float(frame) - HITSTOP_END) / float(TOTAL - HITSTOP_END))
    return _lin(Y_KEYS, frame)


def pelvis_z_at(frame):
    """骨盆世界 z（米）。★ 四段：弹道 → 硬直冻结 → 贴墙下滑 → 新抛物线自由落体。"""
    if frame <= WALL_HIT:
        z = ball_z(frame)
        if BALLISTIC_BREAK and frame > ENTER:
            # ⑨ 打断弹道：把来程抬离共享抛物线
            z += BALLISTIC_BREAK_MM / 1000.0
        return z
    if NO_HITSTOP:
        # ④ 抽掉停顿：撞墙帧之后**不冻**，直接接下滑（帧号从 `WALL_HIT` 起算，
        #    保证 `u ≥ 0` —— 负数底数的分数次幂在 Python 里会变成复数）。
        if frame <= DETACH:
            u = (float(frame) - WALL_HIT) / float(DETACH - WALL_HIT)
            u = max(0.0, min(1.0, u))
            return Z_WALL_BALL - SLIDE_DROP_M * (u ** SLIDE_POW)
        n = frame - DETACH
        return (Z_WALL_BALL - SLIDE_DROP_M) + _SLIDE_EXIT_VZ * n \
            - 0.5 * G_M * n * n
    if frame <= HITSTOP_END:
        return Z_WALL_BALL                       # ★ 硬直：位置**全冻**
    if NO_FALL:
        return Z_WALL_BALL - SLIDE_DROP_M        # ⑥ 撞墙后不下落
    if frame <= DETACH:
        return Z_WALL_BALL - _slide_drop(frame)
    n = frame - DETACH
    base = Z_WALL_BALL - SLIDE_DROP_M
    if END_ZERO:
        # ⑦ 末帧给静止：把尾巴压平成**匀速上升**（末帧 vz 为正 ⟹ 两条判据都红）
        u = float(frame - DETACH) / float(END - DETACH)
        return base + 0.030 * u
    # ★ 离散自由落体：`z(n) = base + V·n − ½G·n²`
    #   ⟹ 一阶差分 `Δz(n) = V − ½G(2n−1)`，**从 n=1 起就严格更负**；
    #   ⟹ 二阶差分 ≡ −G（严格）。
    #   ★ 为什么不用 `−½G·n(n−1)`（第一版）：那种写法让 Δz(1) = V，于是
    #     `vz(DETACH)` 与 `vz(DETACH+1)` **完全相等**，`wall_fall_vz_monotone_ok` 必红；
    #     且它的物理含义是"第一步的平均速度 = V"（等价于 n=0 处瞬时速度 = V + ½G，
    #     即接缝处有**半个步长的速度断点**）。`−½G·n²` 则让 n=0 处瞬时速度恰为 V，
    #     与下滑段末步差分 V 连续 —— 物理上更对，判据上也更强。
    return base + _SLIDE_EXIT_VZ * n - 0.5 * G_M * n * n


def pelvis_vz_at(frame):
    """判据用的"竖速" = **一阶差分**（与 D12 `end_vz_mm_per_frame` 同口径）。"""
    return (pelvis_z_at(frame) - pelvis_z_at(frame - 1)) * 1000.0


# =============================================================== 阈值
SEAM_TOL = 1e-6
NO_TELEPORT_MAX_DEG = 25.0
REACH_MAX_RATIO = 0.995

BALLISTIC_TOL = BALLISTIC_TOL_MM

# ---- ★★★ 墙族 ---------------------------------------------------------------
WALL_PEN_TOL_MM = _env_f("D19_WALL_PEN_TOL", 5.0)      # "墙是硬的"容差（≤5 mm）
WALL_CONTACT_EPS_MM = _env_f("D19_WALL_CONTACT_EPS", 0.5)   # 触墙判定带宽
WALL_STAY_Y_TOL_MM = _env_f("D19_WALL_STAY_Y", 12.0)   # 停留段骨盆 y 抖动上界
WALL_STAY_GAP_MM = _env_f("D19_WALL_STAY_GAP", 18.0)   # 停留段后缘离墙不得超此值
WALL_X_TOL_MM = _env_f("D19_WALL_X_TOL", 20.0)         # 侧向漂移上界
HITSTOP_MIN_FRAMES = _env_f("D19_HITSTOP_MIN", 2.0)
HITSTOP_MAX_FRAMES = _env_f("D19_HITSTOP_MAX", 4.0)
STOP_TOL = _env_f("D19_STOP_TOL", 1.0e-6)

# ---- 离地（撞墙后的"无支撑段"）-----------------------------------------------
AIRBORNE_MIN_MM = _env_f("D19_AIRBORNE_MIN", 100.0)
AIRBORNE_WALL_GAP_MM = _env_f("D19_AIRBORNE_GAP", 20.0)

# ---- 撞墙后的新抛物线（自由下落）--------------------------------------------
FALL_VZ_TOL_MM = _env_f("D19_FALL_VZ_TOL", 1.0e-4)     # 二阶差分 ≡ −G
END_VZ_REG_MAX_MM = _env_f("D19_END_VZ_MAX", -1.0e-3)   # 登记竖速必须**严格为负**

# ---- 躯干后仰拱（本支主驱动：让**后背**成为最靠后的面）------------------------
ARCH_PELVIS_DEG = _env_f("D19_ARCH_PELVIS", -4.0)
ARCH_SPINE1_DEG = _env_f("D19_ARCH_SPINE1", -9.0)
ARCH_SPINE2_DEG = _env_f("D19_ARCH_SPINE2", -9.0)
ARCH_CHEST_DEG = _env_f("D19_ARCH_CHEST", -9.0)
ARCH_NECK_DEG = _env_f("D19_ARCH_NECK", -4.0)
ARCH_HEAD_DEG = _env_f("D19_ARCH_HEAD", -3.0)
ARCH_PEAK = _env_i("D19_ARCH_PEAK", WALL_HIT)          # 后仰到位帧

# ---- 四肢（惯性向前甩 —— 被击退时四肢相对躯干**向前**甩，物理正确）------------
LIMB_PEAK = _env_i("D19_LIMB_PEAK", WALL_HIT)          # 四肢甩到位帧
LIMB_FIST_RATIO = _env_f("D19_FIST_RATIO", 0.74)
FIST_TRAVEL_MIN_MM = _env_f("D19_FIST_MIN", 200.0)
ANKLE_TRAVEL_MIN_MM = _env_f("D19_ANKLE_MIN", 200.0)
NO_SNAP_END_DEG = _env_f("D19_SNAP_END", 6.0)
SNAP_WINDOW = _env_i("D19_SNAP_WIN", 8)

# ---- 滚转回位（D11 教训 3 → D12/D13 照抄）------------------------------------
ROLL_WEIGHT_MODE = os.environ.get("D19_ROLL_WEIGHT", "always").strip().lower()
ROLL_BONES = tuple(
    item for item in os.environ.get(
        "D19_ROLL_BONES",
        "upperarm.L,forearm.L,hand.L,upperarm.R,forearm.R,hand.R").split()
    if item)
ROLL_ITER = max(1, int(os.environ.get("D19_ROLL_ITER", "2")))

CLIP_MAX_MM = _env_f("D19_CLIP_MAX", 0.0)
CLIP_EVERY = int(os.environ.get("D19_CLIP_EVERY", 3))
SEAM_REPLAY_POS_MAX_MM = _env_f("D19_SEAM_POS", 0.01)
SEAM_REPLAY_DIR_MAX_DEG = _env_f("D19_SEAM_DIR", 0.05)

# ---- 水平位移归属（★ 与 D12/D13 **不同**：本支**烘** +Y 位移，理由见文件头）-----
ROOT_MOTION_Y_REG_M = PELVIS_Y_END - PELVIS_Y_START
ROOT_MOTION_TOL_MM = _env_f("D19_ROOT_TOL", 8.0)

# =============================================================== 驱动标量
ARCH_KEYS = ((0, 0.0), (1, 0.12), (3, 0.42), (6, 0.72), (9, 0.90),
             (ARCH_PEAK, 1.00), (HITSTOP_END, 1.00), (20, 0.97),
             (SLIDE_END, 0.92), (FALL_MID, 0.82), (END, 0.66))
LIMB_KEYS = ((0, 0.0), (1, 0.16), (3, 0.46), (6, 0.75), (9, 0.93),
             (LIMB_PEAK, 1.00), (HITSTOP_END, 1.00), (20, 0.99),
             (SLIDE_END, 0.96), (FALL_MID, 0.90), (END, 0.80))
TWIST_KEYS = ((0, 0.0), (2, 0.20), (WALL_HIT, 0.62), (HITSTOP_END, 0.62),
              (20, 0.66), (SLIDE_END, 0.64), (FALL_MID, 0.54), (END, 0.40))
# ★ 三张权重表在 `SLIDE_END` 处**都不许放"拐点键"** —— 第一版把 `ARCH_RELAX(=26)`
#   直接塞在这里（0.92→0.82、0.96→0.88、0.64→0.52 全在**一帧内**），
#   叠加 `Y_KEYS` 的 −52 mm 跳变 ⟹ f26 单帧 17.257°。改为经 `FALL_MID` 两段缓释。


def arch(frame):
    """★ 主驱动 ①：躯干**后仰拱**（0~1）—— 让后背成为最靠后的面。"""
    return UE.pwl(ARCH_KEYS, float(frame), 0.0)


def limb(frame):
    """★ 主驱动 ②：四肢**惯性向前甩**（0~1）。"""
    return UE.pwl(LIMB_KEYS, float(frame), 0.0)


def twist(frame):
    """绕体轴轻微拧转（避免读成纯平面动作）。"""
    return UE.pwl(TWIST_KEYS, float(frame), 0.0)


# =============================================================== 世界角目标
TORSO_BONES = ("pelvis", "spine_01", "spine_02", "chest", "neck", "head")
PARENT_OF = {"pelvis": "root", "spine_01": "pelvis", "spine_02": "spine_01",
             "chest": "spine_02", "neck": "chest", "head": "neck"}
ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")
LEG_BONES = ("thigh.L", "shin.L", "thigh.R", "shin.R")

# ★ 矢状面（前后）世界角目标：`rig_axis_map` 记 `rx > 0 = 前屈` ⟹ 后仰取负。
#   自骨 = 父骨 + `rx_self` ⟹ `rx_self = W_self − W_parent`（D12 的"世界俯仰 → 局部 rx"）。
ARCH_W = (("pelvis", ARCH_PELVIS_DEG), ("spine_01", ARCH_SPINE1_DEG),
          ("spine_02", ARCH_SPINE2_DEG), ("chest", ARCH_CHEST_DEG),
          ("neck", ARCH_NECK_DEG), ("head", ARCH_HEAD_DEG))

SPINE_RY_DEG = _env_f("D19_SPINE_RY", 7.0)
PELVIS_RY_DEG = _env_f("D19_PELVIS_RY", 4.0)


def world_arch(frame):
    """各骨**世界后仰目标**（度，负 = 后仰）。"""
    a = arch(frame)
    w = {"root": 0.0}
    for name, deg in ARCH_W:
        w[name] = deg * a
    return w


def torso_pose(frame):
    """后仰拱（局部 rx）+ 轻微拧转（ry）叠加在**接缝姿态**之上。"""
    w = world_arch(frame)
    t = twist(frame)
    out = {}
    for name in TORSO_BONES:
        rx = w[name] - w[PARENT_OF[name]]        # ★ 自骨 = 父骨 + rx_self
        base = ZERO.get(name, (0.0, 0.0, 0.0))
        if name == "pelvis":
            ry = PELVIS_RY_DEG * t
        elif name in ("spine_01", "spine_02", "chest"):
            ry = SPINE_RY_DEG * t * (0.6 if name == "spine_01" else
                                     1.0 if name == "spine_02" else 0.8)
        else:
            ry = 0.0
        out[name] = (base[0] + rx, base[1] + ry, base[2])
    for side in SIDES:
        name = "shoulder." + side
        out[name] = tuple(ZERO.get(name, (0.0, 0.0, 0.0)))
    out["@loc"] = {"pelvis": A.wloc(pelvis_x_at(frame), pelvis_y_at(frame),
                                    pelvis_z_at(frame) - Z_PELVIS_REST)}
    return out


# =============================================================== 拳 / 肘目标
# ★ 目标方向 = 相对肩的**世界方向**：外张 + 前甩 + 下垂。
FIST_DIR = {
    "L": tuple(float(x) for x in
               os.environ.get("D19_FIST_L", "0.760,-0.470,-0.450").split(",")),
    "R": tuple(float(x) for x in
               os.environ.get("D19_FIST_R", "-0.760,-0.470,-0.450").split(",")),
}
ELBOW_DIR = {
    "L": tuple(float(x) for x in
               os.environ.get("D19_ELBOW_L", "0.620,-0.520,-0.586").split(",")),
    "R": tuple(float(x) for x in
               os.environ.get("D19_ELBOW_R", "-0.620,-0.520,-0.586").split(",")),
}


def fist_target(arm, side, frame):
    """拳世界目标 = 肩位 + 方向 × 臂展（锚在肩上：骨盆一直在动）。"""
    shoulder = Vector(A.bone_world(arm, "upperarm." + side, "head"))
    d0 = (SEAM_FIST[side] - SEAM_SHOULDER[side])
    d0 = d0.normalized() if d0.length > 1e-9 else Vector((0.0, -1.0, 0.0))
    d1 = Vector(FIST_DIR[side]).normalized()
    t = limb(frame)
    direction = d0 * (1.0 - t) + d1 * t
    direction = direction.normalized() if direction.length > 1e-9 else d1
    span = SEAM_SPAN[side] + (LIMB_FIST_RATIO * ARM_MAX[side]
                              - SEAM_SPAN[side]) * t
    return shoulder + direction * span


def elbow_dir(side, frame):
    t = limb(frame)
    d0 = Vector(SEAM_ELBOW_DIR[side])
    d1 = Vector(ELBOW_DIR[side]).normalized()
    out = d0 * (1.0 - t) + d1 * t
    return out.normalized() if out.length > 1e-9 else d1


# =============================================================== 踝目标
# ★ 关键设计：**脚必须从"拖在身后"收到"身下偏前"**，否则最早接触墙的是鞋（不是后背）。
ANKLE_OFF_KEYS = {
    "dx": ((0, 0.0), (WALL_HIT, 0.105), (SLIDE_END, 0.095), (END, 0.085)),
    "dy": ((0, 0.0), (WALL_HIT, -0.185), (SLIDE_END, -0.130), (END, -0.075)),
    "dz": ((0, 0.600), (WALL_HIT, 0.700), (SLIDE_END, 0.740), (END, 0.680)),
}
# ★ 三个通道的含义（**都是接缝基准上的增量**，见 `ankle_target` 的 ★★ 注释）：
#   dx = 向外张开（按侧取符号）／dy = 向前收（−Y = 身前）／
#   dz = **髋下深度绝对值**（不是增量！t=0 时由 `SEAM_VERT` 接管，故此处 f0 值不被使用）。
#   `dy < 0` 是本支相对 D13 的**方向反转**：D13 让腿**向后拖尾**，本支必须把腿
#   收到**身下偏前**，否则最早接触墙的是鞋、不是后背（`wall_back_first_ok`）。


def ankle_target(arm, side, frame):
    """踝目标 = **髋位 + 接缝髋-踝偏移** +（向外 / 向前 / 向下）**叠在接缝值上**。

    ★★ 这条是 D19 最容易踩的坑，写清楚：
      第一版写成 `hip + off*(1−t) + new*t`，且 `z = hip.z + dz*t`
      —— 于是 **t→0 时踝目标 z 收敛到髋高**（脚瞬移 0.5 m 到髋上）。
      实测后果：f1 `foot.R` 单帧 **100.15°**、`shin.R` **96.83°**、`thigh.L` **−76.97°**
      ⟹ `no_teleport` 红。对照 D13（同一套机械、`max_frame_step_deg = 23.653`）：
      它的写法是 `hip + off`（接缝偏移**始终全额生效**）+ 增量*t，且
      `z = hip.z − vert`，`vert` 是**髋下深度绝对值**（0.685~0.718 m，从不取 0）。
      ⟹ 教训（本项目通用）：**任何锚在关节上的目标量，都必须"以接缝值为基准 + 增量"，
      绝不允许"从 0 混合"** —— 从 0 混合等于在 f0 断言了一个物理上不存在的姿态。
    """
    hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
    off = SEAM_HIP_OFF[side]        # (dx, dy) —— 接缝处踝相对髋，**始终全额生效**
    vert0 = SEAM_VERT[side]         # 接缝处踝在髋下的深度（米，正数）
    t = limb(frame)
    sgn = 1.0 if side == "L" else -1.0
    dx = _lin(ANKLE_OFF_KEYS["dx"], frame) * sgn
    dy = _lin(ANKLE_OFF_KEYS["dy"], frame)
    dz = _lin(ANKLE_OFF_KEYS["dz"], frame)
    return Vector((hip.x + off[0] + dx * t,
                   hip.y + off[1] + dy * t,
                   hip.z - (vert0 * (1.0 - t) + dz * t)))


TIP_KEYS = ((0, 6.0), (WALL_HIT, 6.0), (SLIDE_END, 0.0), (END, 0.0))


# =============================================================== 模块级表
ZERO = {}
ZERO_WORLD = {}
ZERO_BASIS = {}
ZERO_DIR = {}
SEAM_FIST = {}
SEAM_SHOULDER = {}
SEAM_SPAN = {}
SEAM_ELBOW_DIR = {}
SEAM_HAND_DIR = {}
SEAM_ANKLE = {}
SEAM_HIP = {}
SEAM_HIP_OFF = {}
SEAM_VERT = {}
ANKLE_0 = {}
KNEE_DIR = {}
ARM_MAX = {}
Z_SEAM = 0.0
HITSTOP_POSE = {}
_HITSTOP_REUSED = [0]
SEAM_MATCH = {"src": None, "geom_pos": None, "geom_dir": None,
              "pos_bone": None, "dir_bone": None, "per_bone": {}}
UNKEYED_START = [0]


# =============================================================== 姿态装配
def arm_seat_tip(arm, pose, side, tip_target, elbow_dir_in):
    """D05 立的臂解算：两骨 IK 打在腕上，手骨按零位自己的折角单独瞄。"""
    up, fo, hd = ("upperarm." + side, "forearm." + side, "hand." + side)
    dims = UE.ARM_LEN[side]
    l1, l2 = dims["upper"], dims["forearm"]
    hand_dir = SEAM_HAND_DIR[side]
    wrist_target = Vector(tip_target) - hand_dir * dims["hand"]
    shoulder = Vector(A.bone_world(arm, up, "head"))
    delta = wrist_target - shoulder
    limit = (l1 + l2) * 0.9995
    clamp = delta.length > limit
    distance = max(1e-4, min(delta.length, limit))
    axis = (delta.normalized() if delta.length > 1e-9
            else Vector((0.0, 0.0, -1.0)))
    bulge = Vector(elbow_dir_in) - axis * Vector(elbow_dir_in).dot(axis)
    if bulge.length < 1e-6:
        bulge = Vector((0.0, 0.0, 1.0)) - axis * axis.z
    bulge.normalize()
    cos_sh = (l1 * l1 + distance * distance - l2 * l2) / (2.0 * l1 * distance)
    cos_sh = max(-1.0, min(1.0, cos_sh))
    sin_sh = math.sqrt(max(0.0, 1.0 - cos_sh * cos_sh))
    elbow = shoulder + (axis * cos_sh + bulge * sin_sh) * l1
    for name, direction in ((up, elbow - shoulder),
                            (fo, wrist_target - elbow),
                            (hd, hand_dir)):
        pose[name] = UE.aim_nearest(arm, name, direction,
                                    UE.IDLE_BASIS[name], UE.IDLE_DIR[name])
    return clamp, delta.length * 1000.0, limit * 1000.0


def build_pose(arm, frame):
    # ★ f0 = **逐位**接缝姿态（`Launch_Hit@34`）—— 不走解算，原样返回。
    if frame <= 0:
        pose = {}
        for key, value in ZERO.items():
            pose[key] = (tuple(value) if not key.startswith("@")
                         else {kk: tuple(vv) for kk, vv in value.items()})
        UNKEYED_START[0] += 1
        return pose

    # ★★ 硬直（§6）：`WALL_HIT+1..HITSTOP_END` **逐位复用** f=WALL_HIT 的姿态；
    #   且 `pelvis_z_at/y_at` 在该段返回**常量** ⟹ 「姿态 + 位置全冻」构造性成立。
    if HITSTOP_POSE and WALL_HIT < frame <= HITSTOP_END:
        pose = {}
        for key, value in HITSTOP_POSE.items():
            if key == "@loc":
                locs = {k: tuple(v) for k, v in value.items()}
                locs["pelvis"] = A.wloc(pelvis_x_at(frame), pelvis_y_at(frame),
                                        pelvis_z_at(frame) - Z_PELVIS_REST)
                pose["@loc"] = locs
            else:
                pose[key] = tuple(value)
        _HITSTOP_REUSED[0] += 1
        return pose

    pose = torso_pose(frame)
    A.apply_pose(arm, pose)
    for side in SIDES:
        UE.leg_seat(arm, pose, side, ankle_target(arm, side, frame),
                    KNEE_DIR[side])
    for name in ("foot.L", "foot.R"):
        tip = _lin(TIP_KEYS, frame)
        if tip is None:
            continue
        pose[name] = JS._unwrap_xyz(
            JS._PREV_EULER.get(name),
            UE.keep_foot_lifted(arm, name.split(".")[1], tip))
    for side in SIDES:
        arm_seat_tip(arm, pose, side, fist_target(arm, side, frame),
                     elbow_dir(side, frame))
    if ROLL_WEIGHT_MODE != "off":
        weight = 1.0
        for _ in range(ROLL_ITER):
            for name in ROLL_BONES:
                if name in arm.pose.bones:
                    _roll_return(arm, pose, name, weight)
            for side in SIDES:
                arm_seat_tip(arm, pose, side, fist_target(arm, side, frame),
                             elbow_dir(side, frame))
    pose.update(A.FIST)
    for name, value in pose.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)
    if frame == WALL_HIT:
        HITSTOP_POSE.update({k: (tuple(v) if not k.startswith("@")
                                 else {kk: tuple(vv) for kk, vv in v.items()})
                             for k, v in pose.items()})
    return pose


def solve_pose(arm, frame, meshes=None):
    return build_pose(arm, frame)


# =============================================================== 滚转回位修正
def _roll_return(arm, pose, name, weight):
    if weight <= 1e-9:
        return
    pose_bone = arm.pose.bones[name]
    reference = Quaternion(ZERO_BASIS[name])
    direction_now = Vector(A.bone_direction(arm, name))
    if direction_now.length < 1e-9:
        return
    direction_now.normalize()
    turn = ZERO_DIR[name].rotation_difference(direction_now)
    reference = (turn @ reference).normalized()
    now = pose_bone.matrix.to_3x3().to_quaternion().normalized()
    if now.dot(reference) < 0.0:
        reference.negate()
    blended = now.slerp(reference, max(0.0, min(1.0, weight)))
    matrix = blended.to_matrix().to_4x4()
    matrix.translation = pose_bone.matrix.translation
    pose_bone.matrix = matrix
    bpy.context.view_layer.update()
    UE.CARRY_Q[name] = blended
    pose[name] = JS._unwrap_xyz(
        JS._PREV_EULER.get(name),
        tuple(math.degrees(v) for v in pose_bone.rotation_euler))


# =============================================================== 墙测量
# ★ "后背族"：名字里带躯干 / 头颈 / 外套的网格。撞墙帧**接触墙面的必须是它们**。
BACK_KEYWORDS = ("Torso", "Shirt", "Jacket", "Coat", "Suit", "Head", "Hair",
                 "Neck", "Collar", "Tie", "Lapel", "Chest", "Back", "Body")
LIMB_KEYWORDS = ("Shoe", "Trouser", "Sleeve", "Hand", "Glove", "Arm", "Leg",
                 "Foot", "Toe", "Heel", "Sole", "Cuff", "Button")


def _is_back(name):
    if any(k in name for k in LIMB_KEYWORDS):
        return False
    return any(k in name for k in BACK_KEYWORDS)


def _mesh_extremes(meshes):
    """逐对象求 (最靠后 +Y, 最低 z, 最左 X, 最右 X)，单位 mm（世界）。"""
    dg = bpy.context.evaluated_depsgraph_get()
    rows = {}
    for obj in meshes:
        ev = obj.evaluated_get(dg)
        me = ev.to_mesh()
        if len(me.vertices) == 0:
            ev.to_mesh_clear()
            continue
        mw = ev.matrix_world
        rear, low, xmin, xmax = -1e9, 1e9, 1e9, -1e9
        for vert in me.vertices:
            wco = mw @ vert.co
            if wco.y > rear:
                rear = wco.y
            if wco.z < low:
                low = wco.z
            if wco.x < xmin:
                xmin = wco.x
            if wco.x > xmax:
                xmax = wco.x
        rows[obj.name] = (rear * 1000.0, low * 1000.0, xmin * 1000.0, xmax * 1000.0)
        ev.to_mesh_clear()
    return rows


def _scan_frames(arm, action, scene, meshes):
    """逐帧扫描：骨盆 / 后缘 / 最低点 / 侧向。"""
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    per = {}
    for frame in range(0, TOTAL + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        rows = _mesh_extremes(meshes)
        rear_all, rear_obj = -1e9, None
        rear_back, rear_back_obj = -1e9, None
        low_all, low_obj = 1e9, None
        xmin, xmax = 1e9, -1e9
        for name, (rear, low, xa, xb) in rows.items():
            if rear > rear_all:
                rear_all, rear_obj = rear, name
            if _is_back(name) and rear > rear_back:
                rear_back, rear_back_obj = rear, name
            if low < low_all:
                low_all, low_obj = low, name
            xmin = min(xmin, xa)
            xmax = max(xmax, xb)
        per[frame] = {
            "pelvis": Vector(A.bone_world(arm, "pelvis", "head")),
            "rear_all": rear_all, "rear_all_obj": rear_obj,
            "rear_back": rear_back, "rear_back_obj": rear_back_obj,
            "low_all": low_all, "low_all_obj": low_obj,
            "x_min": xmin, "x_max": xmax,
        }
    return per


# =============================================================== 测量
def _pitch(direction):
    """世界**俯仰**（矢状面 YZ，度）：+ = 前屈，− = 后仰。"""
    return -math.degrees(math.atan2(direction.y, direction.z))


def _lat(direction):
    return math.degrees(math.atan2(direction.x, direction.z))


def _knee_angle(arm, side):
    upper = Vector(A.bone_direction(arm, "thigh." + side)).normalized()
    lower = Vector(A.bone_direction(arm, "shin." + side)).normalized()
    return math.degrees(math.acos(max(-1.0, min(1.0, upper.dot(lower)))))


def _body_metrics(arm):
    lo, hi = PD.head_box()
    fists = {s: Vector(A.bone_world(arm, "hand." + s, "tail")) for s in SIDES}
    return {
        "box_lo": Vector(lo), "box_hi": Vector(hi),
        "fist": fists,
        "chest_pitch_deg": _pitch(Vector(A.bone_direction(arm, "chest"))),
        "pelvis_pitch_deg": _pitch(Vector(A.bone_direction(arm, "pelvis"))),
        "head_pitch_deg": _pitch(Vector(A.bone_direction(arm, "head"))),
        "pelvis": Vector(A.bone_world(arm, "pelvis", "head")),
        "ankle": {s: Vector(A.bone_world(arm, "foot." + s, "head"))
                  for s in SIDES},
        "shoulder": {s: Vector(A.bone_world(arm, "upperarm." + s, "head"))
                     for s in SIDES},
        "knee_deg": {s: _knee_angle(arm, s) for s in SIDES},
    }


def _worst_step(samples, index_a, index_b):
    ea, eb = samples[index_a]["euler"], samples[index_b]["euler"]
    worst, at = 0.0, None
    for name in set(ea) | set(eb):
        a = ea.get(name, (0.0, 0.0, 0.0))
        b = eb.get(name, (0.0, 0.0, 0.0))
        step = max(abs(x - y) for x, y in zip(a, b))
        if step > worst:
            worst, at = step, (samples[index_b]["frame"], name)
    return worst, at


# =============================================================== 门禁
def wall_assertions(arm, action, samples, meshes):  # noqa: C901
    res = {}
    scene = bpy.context.scene
    arm.animation_data.action = action
    A._bind_slot(arm, action)

    arm.animation_data.action = None
    A.apply_pose(arm, ZERO)
    bpy.context.view_layer.update()
    zero = _body_metrics(arm)
    ZERO_FIST = {s: Vector(A.bone_world(arm, "hand." + s, "tail")) for s in SIDES}

    per = _scan_frames(arm, action, scene, meshes)
    WEFF = wall_eff() * 1000.0          # mm

    # ---- ★★★ ① `wall_no_penetration_ok`：全帧任一顶点 y ≤ 墙面 + tol ----
    worst_pen, worst_pen_at, worst_pen_obj = -1e9, None, None
    for frame, row in per.items():
        pen = row["rear_all"] - WEFF
        if pen > worst_pen:
            worst_pen, worst_pen_at, worst_pen_obj = pen, frame, row["rear_all_obj"]
    res["wall_eff_mm"] = round(WEFF, 3)
    res["wall_y_registered_mm"] = round(WALL_Y_M * 1000.0, 3)
    res["wall_penetration_max_mm"] = round(worst_pen, 3)
    res["wall_penetration_at"] = worst_pen_at
    res["wall_penetration_obj"] = worst_pen_obj
    res["wall_pen_tol_mm"] = WALL_PEN_TOL_MM
    res["wall_no_penetration_ok"] = bool(worst_pen <= WALL_PEN_TOL_MM)
    res["wall_no_penetration_note"] = (
        "★★★ 本支头号守卫（「墙是硬的」**唯一**形式化）：全 0~%d 帧、全部网格顶点，"
        "世界 y 必须 ≤ 墙面 + %.1f mm。★ 它红了就是**穿墙**；它若在反向验证 ③ 里"
        "**不红**，说明这堵墙是装饰、本支不算完成。" % (TOTAL, WALL_PEN_TOL_MM))

    # ---- ★★ ② `wall_contact_ok`：首次触墙帧**唯一**且 = `WALL_HIT` ----
    touch = [f for f in sorted(per) if per[f]["rear_all"] >= WEFF - WALL_CONTACT_EPS_MM]
    res["wall_contact_first_frame"] = touch[0] if touch else None
    res["wall_contact_frames"] = touch[:8]
    res["wall_contact_expected"] = WALL_HIT
    res["wall_contact_ok"] = bool(touch and touch[0] == WALL_HIT)
    res["wall_contact_note"] = (
        "★ 口径同 `foot_takeover_ok`：**首次** ≤ 阈值的帧必须唯一且 = `WALL_HIT`。"
        "反向验证 ② 把墙挪远 150 mm ⟹ 永远够不到 ⟹ 本判据红。")

    # ---- ★★ ③ `wall_back_first_ok`：撞墙帧接触墙面的必须是**后背族** ----
    hit_row = per[WALL_HIT]
    res["wall_hit_rear_all_mm"] = round(hit_row["rear_all"], 3)
    res["wall_hit_rear_obj"] = hit_row["rear_all_obj"]
    res["wall_hit_rear_back_mm"] = round(hit_row["rear_back"], 3)
    res["wall_hit_rear_back_obj"] = hit_row["rear_back_obj"]
    res["wall_back_first_ok"] = bool(_is_back(hit_row["rear_all_obj"] or ""))
    res["wall_back_first_note"] = (
        "★ 清单原文要「**后背**撞墙」⟹ 撞墙帧 +Y 极值对象必须属于后背族"
        "（躯干/头颈/外套）。本支为此把**脚与手从身后收到身下偏前** —— "
        "首 55 支里脚/手总是最靠后的，这是本支的姿态设计约束。")

    # ---- ★★ ④ `wall_stay_ok`：停留段 y 钉住、z 下落、"仍在贴墙" ----
    stay = list(range(HITSTOP_END, SLIDE_END + 1))
    y0 = per[HITSTOP_END]["pelvis"].y
    y_dev = max(abs(per[f]["pelvis"].y - y0) * 1000.0 for f in stay)
    gaps = [WEFF - per[f]["rear_all"] for f in stay]
    zs_stay = [per[f]["pelvis"].z for f in stay]
    z_fall = all(zs_stay[i + 1] < zs_stay[i] for i in range(len(zs_stay) - 1))
    res["wall_stay_y_dev_mm"] = round(y_dev, 3)
    res["wall_stay_y_tol_mm"] = WALL_STAY_Y_TOL_MM
    res["wall_stay_gap_max_mm"] = round(max(gaps), 3)
    res["wall_stay_gap_tol_mm"] = WALL_STAY_GAP_MM
    res["wall_stay_z_drop_mm"] = round((zs_stay[0] - zs_stay[-1]) * 1000.0, 3)
    res["wall_stay_z_strictly_falling"] = bool(z_fall)
    res["wall_stay_ok"] = bool(abs(y_dev) <= WALL_STAY_Y_TOL_MM and
                               max(gaps) <= WALL_STAY_GAP_MM and z_fall)
    res["wall_stay_note"] = (
        "★ 「短暂停留」= **贴着墙往下滑**：骨盆 y 钉住（≤%.0f mm）、后缘始终离墙 ≤%.0f mm、"
        "z 严格下降。反向验证 ⑤「原路弹回」必须让本判据红。"
        % (WALL_STAY_Y_TOL_MM, WALL_STAY_GAP_MM))

    # ---- ★★ ⑤ `wall_fall_ok`：离墙后**新的**抛物线（单调更负 + 二阶差分 ≡ −G）----
    fall = list(range(DETACH, TOTAL + 1))
    vz = {f: pelvis_vz_at(f) for f in range(1, TOTAL + 1)}
    fv = [vz[f] for f in fall]
    monotone = all(fv[i + 1] < fv[i] for i in range(len(fv) - 1))
    # ★ 二阶差分窗口 = `DETACH+2 … END`（纯落体**内部**，必须严格 ≡ −G）。
    #   开区间起点为什么不是 `DETACH+1`：`−½G·n²` 是"**速度连续**"的离散化，
    #   它的一阶差分从 n=1 起就严格更负（⟹ 单调成立），但 `f=DETACH` 的一阶差分
    #   继承**下滑段（摩擦）**的动力学，接缝处那一格不是重力该负责的量。
    #   ★ 这里不放空：接缝改用**精确期望值**单独钉死（下面 `wall_fall_seam_ok`）。
    gerr, gerr_at = 0.0, None
    for f in range(DETACH + 2, TOTAL + 1):
        d = (vz[f] - vz[f - 1]) - (-G_MM)
        if abs(d) > abs(gerr):
            gerr, gerr_at = d, f
    # ★★ 接缝速度连续：`z(n)=V·n−½G·n²` ⟹ Δz(1)=V−½G。故
    #    `vz(DETACH+1) − vz(DETACH)` 的**解析期望值恰为 −G/2**（不是 −G）。
    #    这正是"速度 Verlet 在换力点走半步"的标准表现 —— 是**速度连续**的证据，
    #    不是误差。用精确值钉住它（容差 = 二阶差分同一把尺子），比"不检查"强。
    seam_dv = vz[DETACH + 1] - vz[DETACH]
    seam_dv_expect = -0.5 * G_MM
    res["wall_fall_seam_dv_mm"] = round(seam_dv, 9)
    res["wall_fall_seam_dv_expected_mm"] = round(seam_dv_expect, 9)
    res["wall_fall_seam_ok"] = bool(
        abs(seam_dv - seam_dv_expect) <= FALL_VZ_TOL_MM)
    res["wall_fall_vz_mm"] = {str(f): round(vz[f], 4) for f in fall}
    res["wall_fall_vz_monotone_ok"] = bool(monotone)
    res["wall_fall_g_err_mm"] = round(abs(gerr), 9)
    res["wall_fall_g_err_at"] = gerr_at
    res["wall_fall_g_tol_mm"] = FALL_VZ_TOL_MM
    res["wall_fall_ok"] = bool(monotone and abs(gerr) <= FALL_VZ_TOL_MM
                               and max(fv) < 0.0
                               and res["wall_fall_seam_ok"])
    res["wall_fall_note"] = (
        "★ 停留段结束（f%d）后进入**新的**解析自由落体（`z = base + V·n − ½G·n²`）："
        "竖速**从 f%d 起严格更负**、f%d..%d 二阶差分 ≡ −G、"
        "且接缝 `vz(%d)−vz(%d)` 精确 = −G/2（速度连续，见上方注释）。"
        "反向验证 ⑥「不下落」必须让本判据红。"
        % (DETACH, DETACH, DETACH + 2, TOTAL, DETACH + 1, DETACH))

    # ---- ★★ ⑥ `wall_hitstop_ok`：2~4 帧**姿态 + 位置**全冻 ----
    if NO_HITSTOP:
        res["wall_hitstop_frames"] = 0
        res["wall_hitstop_pose_drift_deg"] = -1.0
        res["wall_hitstop_pos_drift_mm"] = -1.0
        res["wall_hitstop_ok"] = False
    else:
        nframes = HITSTOP_END - WALL_HIT + 1
        pose_drift, pose_at = 0.0, None
        for index in range(WALL_HIT, HITSTOP_END):
            step, at = _worst_step(samples, index, index + 1)
            if step > pose_drift:
                pose_drift, pose_at = step, at
        pose_drift = max(pose_drift, _worst_step(samples, WALL_HIT, HITSTOP_END)[0])
        pos_dev = 0.0
        for f in range(WALL_HIT, HITSTOP_END + 1):
            pos_dev = max(pos_dev,
                          (per[f]["pelvis"] - per[WALL_HIT]["pelvis"]).length * 1000.0)
        res["wall_hitstop_frames"] = nframes
        res["wall_hitstop_pose_drift_deg"] = round(pose_drift, 9)
        res["wall_hitstop_pose_drift_at"] = pose_at
        res["wall_hitstop_pos_drift_mm"] = round(pos_dev, 6)
        res["wall_hitstop_ok"] = bool(
            HITSTOP_MIN_FRAMES <= nframes <= HITSTOP_MAX_FRAMES
            and pose_drift <= STOP_TOL and pos_dev <= STOP_TOL * 1000.0)
    res["hitstop_present"] = res["wall_hitstop_ok"]
    res["wall_hitstop_note"] = (
        "★★ 与 D13「只冻姿态」**相反**：墙是**支撑物** ⟹ 撞墙帧**姿态 + 位置全冻**"
        "（§6：命中关键帧做 2~4 帧完全停顿）。构造式实现：姿态逐位复用 + z/y 通道取常量。")

    # ---- ★ `wall_x_ok`：X 方向不许漂出去（像素探针看不见 X，这是唯一守卫）----
    # ★ 第一版量的是**全网格 |x| 极值**（得到 632.692 mm = 双手张开的绝对跨度），
    #   那不是"漂移"—— 判据要钉的是「**人没有从墙的侧面滑出去**」，是**根位移**性质。
    #   后果：反向验证 ⑧（`SIDEDRIFT` 把骨盆 x 推 90 mm）**完全测不出来**（惰性旋钮），
    #   而项目已被"名义接线实则惰性"的旋钮坑过 6 次。改为量**骨盆 x 相对首帧的漂移**。
    x_abs = [max(abs(per[f]["x_min"]), abs(per[f]["x_max"])) for f in per]
    x0 = per[0]["pelvis"].x
    x_all = [abs(per[f]["pelvis"].x - x0) * 1000.0 for f in per]
    res["wall_x_max_mm"] = round(max(x_all), 3)          # 侧向漂移（受判据）
    res["wall_x_extent_max_mm"] = round(max(x_abs), 3)   # 身体绝对跨度（只报不判）
    res["wall_x_drift_frame"] = max(
        per, key=lambda f: abs(per[f]["pelvis"].x - x0))
    res["wall_x_tol_mm"] = WALL_X_TOL_MM
    res["wall_x_ok"] = bool(max(x_all) <= WALL_X_TOL_MM)
    res["wall_x_note"] = (
        "★ 墙是相机轴方向的平面（法线 = −Y）⟹ **X 方向的位移像素探针完全看不见**"
        "（D16 的技术发现）⟹ 必须有这条**骨架级**断言钉住「人没有从墙的侧面滑出去」。"
        "口径 = `|骨盆.x(f) − 骨盆.x(0)|`（**根位移**），上界 %.0f mm。"
        "反向验证 ⑧（`SIDEDRIFT` +%.0f mm）必须让本判据红。" % (WALL_X_TOL_MM, SIDEDRIFT_MM))

    # ---- ★★ `ballistic_ok`：撞墙帧之前**逐帧**在共享抛物线上 ----
    ball_err, ball_err_at = 0.0, None
    for f in range(0, WALL_HIT + 1):
        err = abs(per[f]["pelvis"].z - ball_z(f)) * 1000.0
        if err > ball_err:
            ball_err, ball_err_at = err, f
    res["ballistic_max_err_mm"] = round(ball_err, 4)
    res["ballistic_err_at"] = ball_err_at
    res["ballistic_tol_mm"] = BALLISTIC_TOL
    res["ballistic_ok"] = bool(ball_err <= BALLISTIC_TOL)
    res["ballistic_until_wall_ok"] = res["ballistic_ok"]
    res["ballistic_phase"] = {
        "T_PHASE": T_PHASE, "z_f0_mm": round(ball_z(0) * 1000.0, 3),
        "vz_f0_mm": round(ball_vz(0) * 1000.0, 4),
        "apex_frame_local": round(F_APEX_LOCAL, 3),
        "apex_frame_d12": round(F_APEX_D12, 3),
        "apex_z_mm": round(Z_APEX * 1000.0, 3),
        "z_wall_frame_mm": round(Z_WALL_BALL * 1000.0, 3),
        "d12_end_vz_mm": round(D12_END_VZ_MM, 4)}
    res["ballistic_note"] = (
        "★★ 与 D18 **相反**：D18 登记 N/A（无弹道段）；本支**必须启用**——承接同一条共享"
        "抛物线（`T_PHASE = 31.5`，与 D13 逐位相同），撞墙帧之前残差 ≤ %.1f mm。"
        "反向验证 ⑨ 必须让本判据红。" % BALLISTIC_TOL)

    # ---- ★ `end_vz_sign_ok`：末帧**必须正在下落** ----
    end_vz = vz[TOTAL]
    res["end_vz_mm_per_frame"] = round(end_vz, 4)
    res["end_pelvis_z_mm"] = round(per[TOTAL]["pelvis"].z * 1000.0, 3)
    res["end_pelvis_y_mm"] = round(per[TOTAL]["pelvis"].y * 1000.0, 3)
    res["end_vz_sign_ok"] = bool(end_vz <= END_VZ_REG_MAX_MM)
    res["end_vz_zero_skipped"] = True
    res["end_vz_zero_note"] = (
        "★ D17/D18 的 `end_vz_zero_ok`（末帧静止）在本支**必须停用**并登记理由："
        "本支末帧**正在下落**，交给 D14/D15/D16，**不接站姿**。")

    # ---- ★ `airborne_after_wall_ok`：离墙后有"谁都不在支撑"的帧 ----
    # ★ 第一版把"离墙间隙"写成 `rear_all − WEFF`（正值 = 越过墙面）。**符号错了**：
    #   墙就立在**后缘极值**上 ⟹ 这个量恒 ≤ 0，判据**永不可能为真**（不可满足的判据 = 缺陷）。
    #   正确的"离墙多远"= `WEFF − rear_all`（正值 = 已经离开墙面）。
    air_low, air_low_at = 1e9, None
    clear, clear_at = -1e9, None
    for f in fall:
        if per[f]["low_all"] < air_low:
            air_low, air_low_at = per[f]["low_all"], f
        gap = WEFF - per[f]["rear_all"]
        if gap > clear:
            clear, clear_at = gap, f
    res["airborne_after_wall_min_low_mm"] = round(air_low, 3)
    res["airborne_after_wall_min_low_at"] = air_low_at
    res["airborne_after_wall_max_clear_mm"] = round(clear, 3)
    res["airborne_after_wall_max_clear_at"] = clear_at
    res["airborne_min_threshold_mm"] = AIRBORNE_MIN_MM
    res["airborne_air_gap_threshold_mm"] = AIRBORNE_WALL_GAP_MM
    res["airborne_after_wall_ok"] = bool(air_low >= AIRBORNE_MIN_MM
                                         and clear >= AIRBORNE_WALL_GAP_MM)
    res["airborne_after_wall_note"] = (
        "★ 两条同时要满足：① 最低点离地 ≥ %.0f mm（重力在管它）；"
        "② 后缘离墙 ≥ %.0f mm（**墙面**也在管它 —— 人真的离开了墙，不是黏在上面）。"
        % (AIRBORNE_MIN_MM, AIRBORNE_WALL_GAP_MM))

    # ---- 力量传导链（脚→腿→髋→腰→肩→手）------------------------------------
    fist_dev, fist_dev_at = 0.0, None
    knee_flex = {}
    ankle_dev = 0.0
    shoulder_move = 0.0
    for frame in range(0, TOTAL + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        for s in SIDES:
            gap = (Vector(A.bone_world(arm, "hand." + s, "tail"))
                   - ZERO_FIST[s]).length * 1000.0
            if gap > fist_dev:
                fist_dev, fist_dev_at = gap, (s, frame)
            ankle_dev = max(ankle_dev,
                            (Vector(A.bone_world(arm, "foot." + s, "head"))
                             - zero["ankle"][s]).length * 1000.0)
            shoulder_move = max(shoulder_move,
                                (Vector(A.bone_world(arm, "upperarm." + s, "head"))
                                 - zero["shoulder"][s]).length * 1000.0)
    for s in SIDES:
        worst = 0.0
        for frame in range(0, TOTAL + 1):
            scene.frame_set(frame)
            bpy.context.view_layer.update()
            worst = max(worst, abs(_knee_angle(arm, s) - zero["knee_deg"][s]))
        knee_flex[s] = round(worst, 3)
    pelvis_span = max((per[f]["pelvis"] - per[0]["pelvis"]).length
                      for f in per) * 1000.0
    scene.frame_set(WALL_HIT)
    bpy.context.view_layer.update()
    waist_deg = abs(_pitch(Vector(A.bone_direction(arm, "chest")))
                    - zero["chest_pitch_deg"])
    res["chain_travel"] = {
        "foot_mm": round(ankle_dev, 2),
        "knee_deg": round(max(knee_flex.values()), 3),
        "hip_mm": round(pelvis_span, 2),
        "waist_deg": round(waist_deg, 3),
        "shoulder_mm": round(shoulder_move, 2),
        "hand_mm": round(fist_dev, 2),
    }
    res["fist_travel_mm"] = round(fist_dev, 3)
    res["fist_travel_at"] = fist_dev_at
    res["ankle_travel_mm"] = round(ankle_dev, 3)
    res["limb_flung_ok"] = bool(fist_dev >= FIST_TRAVEL_MIN_MM
                                and ankle_dev >= ANKLE_TRAVEL_MIN_MM)
    res["chain_present_ok"] = bool(
        res["chain_travel"]["foot_mm"] > 50.0
        and res["chain_travel"]["knee_deg"] > 0.2
        and res["chain_travel"]["hip_mm"] > 20.0
        and res["chain_travel"]["waist_deg"] > 2.0
        and res["chain_travel"]["shoulder_mm"] > 5.0
        and res["chain_travel"]["hand_mm"] > 30.0)
    res["chain_note"] = (
        "★ 力量传导链 脚→腿→髋→腰→肩→手，六段全部要有量（§6 硬约束）。"
        "「髋」段由 **+Y 位移通道**承担（本支烘了击退位移，与 D12/D13 不同）。")

    # ---- 水平位移归属（★ 本支**烘** +Y）--------------------------------------
    dx_net = (per[TOTAL]["pelvis"].x - per[0]["pelvis"].x) * 1000.0
    dy_net = (per[TOTAL]["pelvis"].y - per[0]["pelvis"].y) * 1000.0
    res["root_motion_net_y_mm"] = round(dy_net, 3)
    res["root_motion_net_x_mm"] = round(dx_net, 3)
    res["root_motion_registered_m"] = round(ROOT_MOTION_Y_REG_M, 6)
    res["root_motion_tol_mm"] = ROOT_MOTION_TOL_MM
    res["root_motion_ok"] = bool(abs(dy_net - ROOT_MOTION_Y_REG_M * 1000.0)
                                 <= ROOT_MOTION_TOL_MM
                                 and abs(dx_net) <= ROOT_MOTION_TOL_MM)
    res["root_motion_note"] = (
        "★★ 与 D12/D13 **立场不同**（已登记）：D12/D13 的 `root_motion_m = [0, 0]`"
        "（击飞距离是招式数值、位移交给引擎）；本支**必须烘 +Y 位移** —— "
        "「墙」是**世界实体**，不走到墙上就没有「撞墙」。登记值 %.4f m。"
        % ROOT_MOTION_Y_REG_M)

    # ---- 收招不许瞬停 --------------------------------------------------------
    snap, snap_at = 0.0, None
    lo = max(1, CANCEL - SNAP_WINDOW)
    for index in range(lo, TOTAL + 1):
        step, at = _worst_step(samples, index - 1, index)
        if step > snap:
            snap, snap_at = step, at
    res["no_snap_stop_step_deg"] = round(snap, 4)
    res["no_snap_stop_at"] = snap_at
    res["no_snap_stop_ok"] = bool(snap <= NO_SNAP_END_DEG)
    res["no_snap_window"] = [lo, TOTAL]

    # ---- 硬直复用帧数 --------------------------------------------------------
    res["lock_reused_frames"] = _HITSTOP_REUSED[0]
    res["lock_expect"] = max(0, HITSTOP_END - WALL_HIT) if not NO_HITSTOP else 0
    res["lock_ok"] = bool(res["lock_reused_frames"] == res["lock_expect"])

    # ---- 穿模 ----------------------------------------------------------------
    frames = sorted(set(list(range(0, TOTAL + 1, CLIP_EVERY))
                        + [ENTER, WALL_HIT, HITSTOP_END, SLIDE_END, DETACH, TOTAL]))
    worst_clip, worst_clip_at, worst_clip_frame = 0.0, None, None
    for frame in frames:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        clip = PD.clip_metrics(arm)
        if clip["clip_max_mm"] > worst_clip:
            worst_clip = clip["clip_max_mm"]
            worst_clip_at = clip["clip_at"]
            worst_clip_frame = frame
    res["clip_max_mm"] = round(worst_clip, 2)
    res["clip_at"] = worst_clip_at
    res["clip_frame"] = worst_clip_frame
    res["no_face_clip_ok"] = bool(worst_clip <= CLIP_MAX_MM)

    # ---- 可达性 --------------------------------------------------------------
    worst_reach, worst_reach_frame = 0.0, None
    worst_leg, worst_leg_frame = 0.0, None
    for frame in range(0, TOTAL + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        for side in SIDES:
            up = "upperarm." + side
            shoulder = Vector(A.bone_world(arm, up, "head"))
            limit = ARM_MAX[side] * 0.9995
            ratio = (fist_target(arm, side, frame) - shoulder).length / limit
            if ratio > worst_reach:
                worst_reach, worst_reach_frame = ratio, (frame, side)
            hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
            leg_limit = (A.L_THIGH + A.L_SHIN) * 0.9995
            ratio = (ankle_target(arm, side, frame) - hip).length / leg_limit
            if ratio > worst_leg:
                worst_leg, worst_leg_frame = ratio, (frame, side)
    res["reach_ratio_max"] = round(worst_reach, 5)
    res["reach_ratio_at"] = worst_reach_frame
    res["reach_ok"] = bool(worst_reach <= REACH_MAX_RATIO)
    res["leg_reach_ratio_max"] = round(worst_leg, 5)
    res["leg_reach_ratio_at"] = worst_leg_frame
    res["leg_reach_ok"] = bool(worst_leg <= REACH_MAX_RATIO)

    # ---- ★ 诊断：全帧最大步长榜（定位"一帧内的大跳"，供 `no_teleport` 归因）----
    steps = []
    for index in range(1, len(samples)):
        prev_eu = samples[index - 1]["euler"]
        cur_eu = samples[index]["euler"]
        for name in set(cur_eu) | set(prev_eu):
            ea = prev_eu.get(name, (0.0, 0.0, 0.0))
            eb = cur_eu.get(name, (0.0, 0.0, 0.0))
            step = max(abs(a - b) for a, b in zip(ea, eb))
            steps.append((step, samples[index]["frame"], name,
                          [round(v, 3) for v in ea],
                          [round(v, 3) for v in eb]))
    steps.sort(key=lambda row: -row[0])
    res["step_scan_top"] = [[round(r[0], 3), r[1], r[2], r[3], r[4]]
                            for r in steps[:12]]

    # ---- 剪影：只报不判 ------------------------------------------------------
    sil = P.silhouette(arm, "d19")
    res["aspect"] = sil["aspect"]
    res["fill_grid"] = sil["fill_grid"]
    res["width_m"] = sil["width_m"]
    res["height_m"] = sil["height_m"]

    # ---- 姿态口径**显式停用 + 登记理由**（§3）--------------------------------
    skipped = {
        "ground_hold_ok": "全段离地（撞墙支没有触地段）",
        "back_land_ok": "本支末帧**不回地面**，落地是 D14/D15/D16 的活",
        "landing_plateau_ok": "无落地平台段",
        "legs_bounce_ok": "无落地缓冲",
        "rise_monotone_ok": "★ 竖直通道**先升后降**（撞墙后下落），单调升必然红",
        "rise_reach_ok": "同上 —— 换成 `wall_fall_ok`",
        "end_matches_idle_ok": "末帧**不接站姿**（在下落中），交给下游",
        "end_vz_zero_ok": "★ 换成 `end_vz_sign_ok`（末帧必须**正在下落**）",
        "hand_plant_ok": "撞墙支**没有撑地**（是后背撞墙，不是手撑地）",
        "hand_off_ok": "无手撑→离地交接",
        "foot_takeover_ok": "双脚全程**不接地面**",
        "sole_ground_ok": "全程离地",
        "no_foot_slide_ok": "全程离地（`foot_probe=()` 显式关掉，同 D12/D13 先例）",
        "knee_unfold_start_ok": "无蹲→站蹬伸段",
        "bounce_absent_ok": "无落地回弹族",
    }
    for key, why in skipped.items():
        res[key + "_disabled"] = True
        res[key + "_disabled_reason"] = why
    res["foot_slide_skipped"] = True
    res["foot_slide_note"] = ("★ 全段离地 ⟹ `foot_probe=()` 显式关掉、`ground_contact_ok` "
                              "pop 掉（同 A12/D12/D13 的先例）。")

    if TRACE:
        res["trace"] = {str(f): {
            "arch": round(arch(f), 4),
            "limb": round(limb(f), 4),
            "z_mm": round(per[f]["pelvis"].z * 1000.0, 2),
            "y_mm": round(per[f]["pelvis"].y * 1000.0, 2),
            "vz": round(vz[f], 2) if f in vz else None,
            "rear_all": round(per[f]["rear_all"], 1),
            "rear_obj": per[f]["rear_all_obj"],
            "rear_back": round(per[f]["rear_back"], 1),
            "low_all": round(per[f]["low_all"], 1),
            "gap": round(WEFF - per[f]["rear_all"], 1),
        } for f in range(0, TOTAL + 1)}
    return res


def _pelvis_moving(arm):
    moving = set()
    for bone in arm.pose.bones:
        node = bone
        while node is not None:
            if node.name == "pelvis":
                moving.add(bone.name)
                break
            node = node.parent
    return moving


def _bone_point(mat):
    return mat[3], mat[7], mat[11]


def _pose_seam_split(mats_a, mats_b, moving):
    """两套世界矩阵的「平移不变」逐位差（B08 第 2 件那把尺子，原样照抄）。"""
    ori, rel = 0.0, 0.0
    ori_bone, rel_bone = None, None
    pa, pb = _bone_point(mats_a["pelvis"]), _bone_point(mats_b["pelvis"])
    for name in mats_a:
        ma, mb = mats_a[name], mats_b[name]
        for index in (0, 1, 2, 4, 5, 6, 8, 9, 10):
            if abs(ma[index] - mb[index]) > ori:
                ori, ori_bone = abs(ma[index] - mb[index]), name
        xa, ya, za = _bone_point(ma)
        xb, yb, zb = _bone_point(mb)
        if name in moving:
            da = (xa - pa[0], ya - pa[1], za - pa[2])
            db = (xb - pb[0], yb - pb[1], zb - pb[2])
        else:
            da, db = (xa, ya, za), (xb, yb, zb)
        worst = max(abs(u - v) for u, v in zip(da, db))
        if worst > rel:
            rel, rel_bone = worst, name
    return ori, rel, ori_bone, rel_bone


def _seam_action():
    return bpy.data.actions.get(SEAM_ACTION)


# =============================================================== 引导
def _load_seam_zero(arm):
    """★ 零位真源：**上游 `Launch_Hit@34` 的落盘行动作**（不是零位姿态）。

    ★ 反向验证 ① 打开时改读 `Idle_01@0` —— 用来证明 `seam_in_ok` 抓得住接缝断裂。
    """
    action = bpy.data.actions.get(ZERO_ACTION)
    if action is None:
        return {}, {"action": ZERO_ACTION, "found": False}
    rot_keyed, loc_keyed = _keyed_bones(action)
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    A.reset_pose(arm)
    bpy.context.scene.frame_set(int(ZERO_FRAME))
    bpy.context.view_layer.update()
    pose = {name: tuple(math.degrees(v)
                        for v in arm.pose.bones[name].rotation_euler)
            for name in rot_keyed if name in arm.pose.bones}
    loc = {name: tuple(arm.pose.bones[name].location)
           for name in loc_keyed if name in arm.pose.bones}
    if loc:
        pose["@loc"] = loc
    info = {"action": ZERO_ACTION, "found": True, "frame": int(ZERO_FRAME),
            "rot_bones": len(rot_keyed), "loc_bones": sorted(loc_keyed),
            "frame_range": [int(v) for v in action.frame_range]}
    return pose, info


def _world_snapshot(arm, pose):
    A.apply_pose(arm, pose)
    bpy.context.view_layer.update()
    heads, dirs = {}, {}
    for name in A.PROBE_BONES:
        if name not in arm.pose.bones:
            continue
        heads[name] = Vector(A.bone_world(arm, name, "head"))
        dirs[name] = Vector(A.bone_direction(arm, name)).normalized()
    return heads, dirs


def boot():
    global ZERO, ZERO_WORLD, Z_SEAM, KNEE_DIR, ANKLE_0, ZERO_FIST
    ZERO, ZERO_WORLD = {}, {}
    ZERO_BASIS.clear()
    ZERO_DIR.clear()
    SEAM_FIST.clear()
    SEAM_SHOULDER.clear()
    SEAM_SPAN.clear()
    SEAM_ELBOW_DIR.clear()
    SEAM_HAND_DIR.clear()
    SEAM_ANKLE.clear()
    SEAM_HIP.clear()
    SEAM_HIP_OFF.clear()
    ANKLE_0.clear()
    KNEE_DIR.clear()
    ARM_MAX.clear()
    HITSTOP_POSE.clear()
    _HITSTOP_REUSED[0] = 0
    UNKEYED_START[0] = 0

    arm, meshes = A.open_animation_project()
    A.setup_scene()
    if SEAM_ACTION not in bpy.data.actions:
        raise RuntimeError("接缝动作 %s 不在落盘文件里" % SEAM_ACTION)
    if ZERO_ACTION not in bpy.data.actions:
        raise RuntimeError("零位真源 %s 不在落盘文件里" % ZERO_ACTION)

    for side in SIDES:
        UE.ARM_LEN[side] = {
            "upper": arm.pose.bones["upperarm." + side].length,
            "forearm": arm.pose.bones["forearm." + side].length,
            "hand": arm.pose.bones["hand." + side].length}
        ARM_MAX[side] = (UE.ARM_LEN[side]["upper"]
                         + UE.ARM_LEN[side]["forearm"]
                         + UE.ARM_LEN[side]["hand"])

    UE.ROLL_STEP_DEG = _env_f("D19_ROLLSTEP", 2.0)
    UE.ROLL_GRID = UE._roll_grid()
    UE.EULER_Y_SAFE = _env_f("D19_YSAFE", 88.0)
    UE.EULER_Y_WEIGHT = _env_f("D19_YWEIGHT", 0.0)

    for extra in LEG_BONES + ("foot.L", "foot.R"):
        if extra not in A.PROBE_BONES:
            A.PROBE_BONES = tuple(A.PROBE_BONES) + (extra,)
        if extra not in A.PROBE_TAILS:
            A.PROBE_TAILS = tuple(A.PROBE_TAILS) + (extra,)
    A.PROBE_KEYS = A.PROBE_BONES + tuple(n + ".tail" for n in A.PROBE_TAILS)

    ZERO, saved_info = _load_seam_zero(arm)
    if not ZERO:
        raise RuntimeError("读不到接缝零位")

    # ★ "落盘真值 vs 手写重演"（同 D12/D13 的 `_load_idle_zero` 检查口径）
    arm.animation_data.action = bpy.data.actions[ZERO_ACTION]
    A._bind_slot(arm, bpy.data.actions[ZERO_ACTION])
    bpy.context.scene.frame_set(int(ZERO_FRAME))
    bpy.context.view_layer.update()
    action_heads, action_dirs = {}, {}
    for name in A.PROBE_BONES:
        if name in arm.pose.bones:
            action_heads[name] = Vector(A.bone_world(arm, name, "head"))
            action_dirs[name] = Vector(A.bone_direction(arm, name)).normalized()
    arm.animation_data.action = None
    replay_heads, replay_dirs = _world_snapshot(arm, ZERO)
    geom_pos, geom_pos_bone = 0.0, None
    for name, point in action_heads.items():
        other = replay_heads.get(name)
        if other is None:
            continue
        gap = (point - other).length * 1000.0
        if gap > geom_pos:
            geom_pos, geom_pos_bone = gap, name
    geom_dir, geom_dir_bone = 0.0, None
    for name, direction in action_dirs.items():
        other = replay_dirs.get(name)
        if other is None:
            continue
        dot = max(-1.0, min(1.0, direction.dot(other)))
        gap = math.degrees(math.acos(dot))
        if gap > geom_dir:
            geom_dir, geom_dir_bone = gap, name
    euler_diff, euler_bone, per_bone = 0.0, None, {}
    for name, value in ZERO.items():
        if name.startswith("@"):
            continue
        got = ZERO.get(name)
        row = [_f32(a) - _f32(b) for a, b in zip(got, value)]
        worst = max(abs(v) for v in row)
        if worst > euler_diff:
            euler_diff, euler_bone = worst, name
        if worst > 0.5:
            per_bone[name] = [round(v, 4) for v in row]
    SEAM_MATCH.update({
        "src": "%s@%d" % (ZERO_ACTION, ZERO_FRAME),
        "saved": saved_info,
        "geom_pos": round(geom_pos, 6), "pos_bone": geom_pos_bone,
        "geom_dir": round(geom_dir, 6), "dir_bone": geom_dir_bone,
        "per_bone": per_bone,
        "matched": bool(geom_pos <= SEAM_REPLAY_POS_MAX_MM
                        and geom_dir <= SEAM_REPLAY_DIR_MAX_DEG),
    })

    A.apply_pose(arm, ZERO)
    bpy.context.view_layer.update()
    Z_SEAM = A.bone_world(arm, "pelvis", "head").z
    ANKLE_0 = {s: Vector(A.bone_world(arm, "foot." + s, "head")) for s in SIDES}
    for side in SIDES:
        SEAM_FIST[side] = Vector(A.bone_world(arm, "hand." + side, "tail"))
        SEAM_ANKLE[side] = Vector(A.bone_world(arm, "foot." + side, "head"))
        SEAM_HIP[side] = Vector(A.bone_world(arm, "thigh." + side, "head"))
        SEAM_HIP_OFF[side] = (SEAM_ANKLE[side].x - SEAM_HIP[side].x,
                              SEAM_ANKLE[side].y - SEAM_HIP[side].y)
        # ★ 接缝处踝在髋下的**深度**（米，正数）—— `ankle_target` 的 t=0 基准。
        SEAM_VERT[side] = SEAM_HIP[side].z - SEAM_ANKLE[side].z
        SEAM_HAND_DIR[side] = Vector(
            A.bone_direction(arm, "hand." + side)).normalized()
        shoulder = Vector(A.bone_world(arm, "upperarm." + side, "head"))
        SEAM_SHOULDER[side] = shoulder
        SEAM_SPAN[side] = (SEAM_FIST[side] - shoulder).length
        elbow = Vector(A.bone_world(arm, "upperarm." + side, "tail"))
        SEAM_ELBOW_DIR[side] = tuple((elbow - shoulder).normalized())
    for side in SIDES:
        hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
        knee = Vector(A.bone_world(arm, "shin." + side, "head"))
        ankle = Vector(A.bone_world(arm, "foot." + side, "head"))
        axis = (ankle - hip).normalized()
        bulge = (knee - hip) - axis * (knee - hip).dot(axis)
        KNEE_DIR[side] = (bulge.normalized() if bulge.length > 1e-9
                          else Vector((0.0, -0.94, -0.34)))
    for bone in ARM_BONES + LEG_BONES:
        UE.IDLE_BASIS[bone] = arm.pose.bones[bone].matrix.to_3x3().copy()
        UE.IDLE_DIR[bone] = A.bone_direction(arm, bone)

    ZERO_WORLD = {n: tuple(v) for n, v in replay_heads.items()}
    for name in A.PROBE_TAILS:
        if name in arm.pose.bones:
            ZERO_WORLD[name + ".tail"] = tuple(A.bone_world(arm, name, "tail"))
    for name in A.PROBE_BONES:
        if name in arm.pose.bones:
            ZERO_BASIS[name] = tuple(
                arm.pose.bones[name].matrix.to_3x3().to_quaternion())
    for name in ARM_BONES:
        ZERO_DIR[name] = Vector(A.bone_direction(arm, name)).normalized()

    ZERO_FIST = {s: Vector(A.bone_world(arm, "hand." + s, "tail")) for s in SIDES}
    A.report("D19_LAYOUT", {
        "total_frames": TOTAL, "seconds": round(TOTAL / float(A.FPS), 3),
        "wall_hit": WALL_HIT, "hitstop_end": HITSTOP_END,
        "slide_end": SLIDE_END, "detach": DETACH, "end": END,
        "wall_y_registered_mm": round(WALL_Y_M * 1000.0, 3),
        "pelvis_y": {"start_mm": round(PELVIS_Y_START * 1000.0, 2),
                     "wall_mm": round(PELVIS_Y_WALL * 1000.0, 2),
                     "detach_mm": round(PELVIS_Y_DETACH * 1000.0, 2),
                     "end_mm": round(PELVIS_Y_END * 1000.0, 2)},
        "pelvis_z_mm": {"wall_mm": round(Z_WALL_BALL * 1000.0, 3),
                        "detach_mm": round((Z_WALL_BALL - SLIDE_DROP_M) * 1000.0, 3),
                        "end_mm": round(pelvis_z_at(TOTAL) * 1000.0, 3)},
        "slide_exit_vz_mm": round(_SLIDE_EXIT_VZ * 1000.0, 4),
        "root_motion_m": [0.0, round(ROOT_MOTION_Y_REG_M, 6)],
        "seam": {"action": SEAM_ACTION, "frame": SEAM_FRAME,
                 "src": saved_info,
                 "d12_end_vz_mm": round(D12_END_VZ_MM, 4),
                 "z_f0_mm": round(ball_z(0) * 1000.0, 3),
                 "apex_frame_d12": round(F_APEX_D12, 3),
                 "apex_frame_local": round(F_APEX_LOCAL, 3),
                 "Z_SEAM_mm": round(Z_SEAM * 1000.0, 3)},
        "zero_pelvis_loc": {k: [round(v, 6) for v in val]
                            for k, val in (ZERO.get("@loc") or {}).items()},
        "zero_pelvis_loc_expected": list(
            A.wloc(0.0, PELVIS_Y_START, ball_z(0) - Z_PELVIS_REST)),
        "ballistic": {"T_PHASE": T_PHASE, "T_ORIGIN_D12": D12_T_ORIGIN,
                      "takeoff_pelvis_z_m": JS.TAKEOFF_PELVIS_Z,
                      "takeoff_speed_mps": round(JS.TAKEOFF_SPEED * A.FPS, 3),
                      "g_per_frame": JS.G_PER_FRAME,
                      "f0_z_mm": round(ball_z(0) * 1000.0, 3),
                      "f0_vz_mm": round(ball_vz(0) * 1000.0, 4),
                      "tol_mm": BALLISTIC_TOL},
        "zero_pelvis_z_mm": round(Z_SEAM * 1000.0, 3),
        "zero_fist_mm": {s: [round(v * 1000.0, 2) for v in SEAM_FIST[s]]
                         for s in SIDES},
        "zero_ankle_mm": {s: [round(v * 1000.0, 2) for v in SEAM_ANKLE[s]]
                          for s in SIDES},
        "zero_hip_mm": {s: [round(v * 1000.0, 2) for v in SEAM_HIP[s]]
                        for s in SIDES},
        "seam_vert_mm": {s: round(SEAM_VERT[s] * 1000.0, 2) for s in SIDES},
        "arm_max_mm": {s: round(ARM_MAX[s] * 1000.0, 2) for s in SIDES},
        "arch_keys": [list(k) for k in ARCH_KEYS],
        "limb_keys": [list(k) for k in LIMB_KEYS],
        "wall_eff_mm": round(wall_eff() * 1000.0, 3),
        "knobs": {"WALLFAR": WALLFAR, "WALLNEAR": WALLNEAR,
                  "NOHITSTOP": NO_HITSTOP, "BOUNCEBACK": BOUNCEBACK,
                  "NOFALL": NO_FALL, "ENDZERO": END_ZERO,
                  "SIDEDRIFT": SIDEDRIFT, "BALLISTIC_BREAK": BALLISTIC_BREAK,
                  "SEAM_ZERO": SEAM_ZERO},
        "note": ("D19 撞墙：★ 全项目**第一支引入世界实体「墙」**；首帧 = `Launch_Hit@34` "
                 "落盘帧；撞墙帧之前 = 共享解析抛物线（同 D13）；撞墙帧全冻 3 帧"
                 "（姿态 + 位置）；贴墙下滑后被松开、落在**新的**抛物线上；末帧**正在下落**。"),
    })
    return arm, meshes


def main():
    arm, meshes = boot()

    JS._PREV_EULER.clear()
    A.apply_pose(arm, ZERO)
    bpy.context.view_layer.update()
    for name in ARM_BONES + LEG_BONES:
        UE.CARRY_Q[name] = arm.pose.bones[name].matrix.to_3x3().to_quaternion()
    for name, value in ZERO.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)

    keyframes = [(0, ZERO)]
    for frame in range(1, TOTAL + 1):
        keyframes.append((frame, solve_pose(arm, frame, meshes)))

    meta = {
        "anim_id": NAME,
        "loop": False,
        "category": "防御与受击",
        "note": ("撞墙：★ 全项目第一支**世界实体（墙）**动画；首帧逐位 = `Launch_Hit@34`；"
                 "撞墙前承接共享抛物线；撞墙帧姿态+位置全冻 3 帧（§6 命中停顿）；"
                 "贴墙下滑后松开、落新抛物线；末帧**正在下落**（交 D14/D15/D16）"),
        "antic_frame": 0,
        "hit_frame": WALL_HIT,
        "cancel_frame": CANCEL,
        "self_hold_frame": SLIDE_END,
        "hitstop_frames": (HITSTOP_END - WALL_HIT + 1) if not NO_HITSTOP else 0,
        "hit_points": 0,
        "root_motion_m": [0.0, round(ROOT_MOTION_Y_REG_M, 6)],
        "hit_point_m": None,
        "wall_y_m": round(WALL_Y_M, 6),
        "wall_normal": [0.0, -1.0, 0.0],
        "wall_contact_frame": WALL_HIT,
        "wall_slide_end_frame": SLIDE_END,
        "wall_detach_frame": DETACH,
        "end_pelvis_z_m": round(pelvis_z_at(TOTAL), 6),
        "end_pelvis_y_m": round(PELVIS_Y_END, 6),
        "end_vz_m_per_frame": round(
            (pelvis_z_at(TOTAL) - pelvis_z_at(TOTAL - 1)), 6),
        "ballistic_ref": "anim_jump_start.TAKEOFF_PELVIS_Z/TAKEOFF_SPEED + "
                         "anim_jump_fall.G_PER_FRAME（相位续 D12 f%d，与 D13 逐位相同）"
                         % SEAM_FRAME,
        "start_pose_ref": "%s 帧 %d（SELF_HOLD 锁存姿态）" % (SEAM_ACTION, SEAM_FRAME),
        "end_pose_ref": "**离墙下落中**（不回原位、不接站姿）",
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.add_markers(action, {"START": 0, "ENTER": ENTER, "WALL_HIT": WALL_HIT,
                           "HITSTOP_END": HITSTOP_END, "SLIDE_END": SLIDE_END,
                           "DETACH": DETACH, "FALL_MID": FALL_MID,
                           "CANCEL": CANCEL, "END": TOTAL})

    samples = A.sample_animation(arm, action, 0, TOTAL, meshes)
    report = A.run_common_assertions(samples, meta, foot_probe=())
    report.pop("ground_contact_ok", None)
    report.pop("ground_min_mm", None)
    report.update(wall_assertions(arm, action, samples, meshes))
    report["meta"] = meta

    delta0 = 0.0
    for name, ref in ZERO.items():
        if name.startswith("@"):
            continue
        got = samples[0]["euler"].get(name)
        if got is None:
            continue
        delta0 = max(delta0, max(abs(_f32(a) - _f32(b))
                                 for a, b in zip(got, ref)))
    report["ua_start_delta_deg"] = round(delta0, 8)
    report["ua_start_ok"] = bool(delta0 <= SEAM_TOL)

    report["seam_zero_saved_ok"] = bool(SEAM_MATCH["matched"])
    report["seam_zero_src"] = SEAM_MATCH["src"]
    report["seam_zero_geom_pos_mm"] = SEAM_MATCH["geom_pos"]
    report["seam_zero_geom_dir_deg"] = SEAM_MATCH["geom_dir"]
    report["seam_zero_worst_bone"] = SEAM_MATCH["pos_bone"]

    # ---- ★ 接缝：首帧逐位 = `Launch_Hit@34`（平移不变尺子）-------------------
    moving = _pelvis_moving(arm)
    seam_mats = CR.action_world_matrices(arm, _seam_action(), SEAM_FRAME)
    mats0 = CR.action_world_matrices(arm, action, 0)
    ori0, rel0, ori_bone0, rel_bone0 = _pose_seam_split(mats0, seam_mats, moving)
    report["seam_in_orient_delta"] = float("%.3e" % ori0)
    report["seam_in_relpos_delta_mm"] = round(rel0 * 1000.0, 6)
    report["seam_in_relpos_bone"] = rel_bone0
    report["seam_in_raw_delta"] = float("%.3e" % CR.matrix_delta(mats0, seam_mats))
    report["seam_in_ok"] = bool(ori0 <= SEAM_TOL and rel0 <= SEAM_TOL)
    report["seam_ruler_note"] = (
        "首帧比 `%s@%d`：**平移不变**尺子（pelvis 后代比「骨位置−骨盆位置」，"
        "非后代比世界绝对）。容差 1e-6，未放宽。" % (SEAM_ACTION, SEAM_FRAME))

    report["failed"] = sorted(k for k, v in report.items()
                              if k.endswith("_ok") and v is not True)
    report["non_ok_bools"] = sorted(
        k for k, v in report.items()
        if isinstance(v, bool) and not k.endswith("_ok") and v is not True)
    A.report("D19_REPORT", report)

    if not SKIP_RENDER:
        # ★ `D19_STEM_ONLY=1`：**只为像素探针的 ④ 反面对照**服务 —— 在
        #   `D19_TP_NOHITSTOP=1` 下只重渲侧视的 3 张关键帧，**不存盘、不导出**。
        #   （探针要证明"抽掉停顿 ⟹ `px_hitstop_ok` 红"，就得有那 3 张图。）
        if os.environ.get("D19_STEM_ONLY") == "1":
            # ★ 渲的是 **`[WALL_HIT, WALL_HIT+1, HITSTOP_END]` = [14, 15, 16]** ——
            #   **与本支 `px_hitstop_ok` 的判据三点逐帧相同**。第一版渲的是
            #   `[WALL_HIT, HITSTOP_END, FALL_MID]`（14/16/30），缺 f15 ⟹
            #   反面对照只能用"14 比 16"两点，**与基线的三点尺子不是同一把**
            #   —— 那正是本项目最忌讳的"反对照换了尺子"。改掉。
            A.render_pose_sheet(arm, action, [WALL_HIT, WALL_HIT + 1, HITSTOP_END],
                                os.environ.get("D19_STEM", "wallhitstem"),
                                views=(VIEW_D19_SIDE_WIDE,))
            print("D19_DONE failed=%s" % report["failed"])
            print("D19_DONE non_ok_bools=%s" % report["non_ok_bools"])
            return

        side_frames = list(range(0, TOTAL + 1))
        other_frames = [0, ENTER, WALL_HIT, HITSTOP_END, SLIDE_END, DETACH,
                        FALL_MID, TOTAL]
        key_frames = [ENTER, WALL_HIT, HITSTOP_END, SLIDE_END, DETACH, FALL_MID]

        # ★★★ 两套图，**必须分开渲**（这是本支踩到的坑，写清楚）：
        #   第一版把墙代理一直挂在场里，于是 35 张 `wallhit_side_*` 的
        #   **右缘 / 顶缘 / 面积行心全部被墙面本身接管**（实测：top 恒 104、
        #   bottom 恒 1099、col_hi 恒 543 = 墙面投影），像素探针**量的是墙不是人**。
        #   ⟹ ① `wallhit*`（**探针用**）：**不挂墙** —— 这样 `col_hi` 才量得到
        #        角色的后缘，而"墙在哪一列"由 `WALL_Y_M` **解析算得**（540.3 px），
        #        反而变成一条更硬的尺子（角色不得越过墙面那一列）。
        #      ② `wallhitwall*`（**目检用**）：**挂墙** —— 给肉眼读"撞墙"。
        A.render_pose_sheet(arm, action, side_frames, "wallhit",
                            views=(VIEW_D19_SIDE_WIDE,))
        A.render_pose_sheet(arm, action, other_frames, "wallhit",
                            views=(VIEW_D19_FRONT, VIEW_D19_3Q))
        A.render_pose_sheet(arm, action, key_frames, "wallhitwide",
                            views=(VIEW_D19_SIDE_WIDE, VIEW_D19_FRONT,
                                   VIEW_D19_3Q))
        _ensure_wall_proxy()
        A.render_pose_sheet(arm, action, key_frames, "wallhitwall",
                            views=(VIEW_D19_SIDE_WIDE, VIEW_D19_FRONT,
                                   VIEW_D19_3Q))
        _remove_wall_proxy()          # ★★ 必须在存盘/导出**之前**删掉
        A.save_project()
        A.export_glb(arm)
    print("D19_DONE failed=%s" % report["failed"])
    print("D19_DONE non_ok_bools=%s" % report["non_ok_bools"])
    if TRACE:
        print("D19_TRACE " + json.dumps(report.get("trace", {}),
                                        ensure_ascii=False))


# ★ 本支取景：**必须自己立第三套基准**（不许照抄 D17 的 −300 / D18 的 +250）。
#   本支骨盆 y：26 → 320 → 252 mm；后缘极值到 705.6 mm（= 墙面）；
#   ⟹ y 有效区间 ≈ [−0.55, +0.71] ⟹ 机位中心取 **+0.20**（墙面留一点点余量）。
#   高度：骨盆 z 1931.9 → 974.2 mm，撞墙前躯干一度甩到 2.6 m 以上 ⟹ 中心 1.45、ortho 3.70。
VIEW_D19_SIDE_WIDE = ("side", (5.40, 0.20, 1.45), (0.0, 0.20, 1.45), 3.70,
                      (780, 1100))
VIEW_D19_FRONT = ("front", (0.0, -5.80, 1.45), (0.0, 0.20, 1.45), 3.70,
                  (780, 1100))
VIEW_D19_3Q = ("three_quarter", (4.10, -4.30, 1.55), (0.0, 0.20, 1.45), 3.70,
               (780, 1100))


# =============================================================== 渲染用墙面代理
WALL_PROXY_NAME = "D19_Wall_Proxy"


def _ensure_wall_proxy():
    """★ 出图专用：在 `y = WALL_Y_M` 立一块**薄板**（法线 −Y）。

    ★★ 纪律：它**只**服务于"出图肉眼验收"，**绝不允许**进入
      `bpy.ops.wm.save_as_mainfile`（.blend）或 `export_glb`（GLB）——
      所以 `main()` 里**渲完立刻删掉**再存盘。
    ★ 侧视图里它被"看边"（正对相机轴）⟹ 图上是一条**竖线**，
      正好当那把"墙在哪儿"的尺子：贴墙/下滑/离墙一眼可判。
    """
    obj = bpy.data.objects.get(WALL_PROXY_NAME)
    if obj is not None:
        return obj
    y = WALL_Y_M
    x0, x1 = -1.55, 1.55
    z0, z1 = -0.05, 3.30
    t = 0.010
    verts = [(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1),
             (x0, y + t, z0), (x1, y + t, z0), (x1, y + t, z1), (x0, y + t, z1)]
    faces = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1),
             (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    mesh = bpy.data.meshes.new(WALL_PROXY_NAME)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(WALL_PROXY_NAME, mesh)
    bpy.context.scene.collection.objects.link(obj)
    mat = bpy.data.materials.get("D19_Wall_Mat")
    if mat is None:
        mat = bpy.data.materials.new("D19_Wall_Mat")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf is not None:
            bsdf.inputs["Base Color"].default_value = (0.16, 0.18, 0.22, 1.0)
            if "Roughness" in bsdf.inputs:
                bsdf.inputs["Roughness"].default_value = 0.85
        mat.diffuse_color = (0.16, 0.18, 0.22, 1.0)
    obj.data.materials.append(mat)
    obj.color = (0.16, 0.18, 0.22, 1.0)
    print("D19_WALL_PROXY y_m=%r verts=%d" % (round(y, 6), len(verts)))
    return obj


def _remove_wall_proxy():
    obj = bpy.data.objects.get(WALL_PROXY_NAME)
    if obj is not None:
        bpy.data.objects.remove(obj, do_unlink=True)
        print("D19_WALL_PROXY removed (出图结束，不进 .blend / GLB)")



if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("D19_FAILURE " + traceback.format_exc())
