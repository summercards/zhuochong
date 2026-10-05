"""anim_getup_b —— D18 `GetUp_B` 背面起身（仰卧 → 双掌在身侧/身后撑地推起 → 收腿 → 站成战斗姿态）。

清单原文：「仰面起身；猛男用**撑地、翻身**等力量型动作」。

★★ 本支是**起身族第二支（收尾支）**，也是全项目**第二次跨族接缝**：
   起点在**地面族**（`Knockdown_B@20` 仰卧），终点在**站立族**（`Idle_01@0` 战斗站姿）。

   | 接缝 | 上游 / 下游 | 本支落成的做法 |
   |---|---|---|
   | 上游**姿态** | `Knockdown_B@20`（仰卧，脸朝上，腿抬在半空） | 本支 f0 **逐位 = `Knockdown_B@20`** |
   | 上游**动量** | D15 末帧 `end_vz = 0` | **不继承任何动量** —— 起身是**主动发力** |
   | 下游**站姿** | `Idle_01@0`（A 族通用站姿锚点） | 末帧（f34~f36）**逐位 = `Idle_01@0`**（世界矩阵 `max_delta ≤ 1e−6`）★★ **本支最硬的判据** |

★★ 与 D17 的关系：**镜像分支，但支点链多一次交接**

   | 量 | 起点 `Knockdown_B@20` | 终点 `Idle_01@0` | 跨度 | 与 D17 |
   |---|---|---|---|---|
   | 骨盆世界 z | **128.0 mm** | **830.0 mm** | **+702 mm** | 比 D17 的 610 还大 92 |
   | 骨盆世界 y | **+470.0 mm** | **0.0 mm** | **−470 mm** | ★ 符号与 D17（−550→0）相反 |
   | 头世界 z | **205.507 mm** | **1485.502 mm** | **+1280 mm** | — |
   | 膝屈角 L | **124.96°** | **40.59°** | **−84.37°** | — |
   | 剪影最高点 | **脚尖（z 391 / 323 mm）** ★ 不是头 | 头（1485） | — | ★★ 见下 |

   ⟹ **三个支点、三次交接**：

   | 段 | 帧区间 | 支点 | 判据 |
   |---|---|---|---|
   | 落腿段 | `[START, LEGS_DOWN]` | **背/臀**（还躺着） | `knee_unfold_start_ok`（腿自己放开） |
   | 撑地推起段 | `[LEGS_DOWN, HAND_OFF]` | **背/臀 → 双掌** | ★ `hand_plant_ok` + `chest_rise_ok` + `hand_off_ok`（下侧） |
   | 收腿交接段 | `(HAND_OFF, FOOT_SET)` | **手 → 脚** | ★ `hand_off_ok`（上侧）+ ★ `foot_takeover_ok` |
   | 起立段 | `[FOOT_SET, END]` | **双脚** | `rise_monotone_ok` + `rise_reach_ok` + `no_foot_slide_ok` + `sole_ground_ok` |

   ★ **"支点交接"两侧方向相反的三条断言必须同时存在**（`hand_plant_ok` / `hand_off_ok` /
     `foot_takeover_ok`）：缺任何一条，就会有"谁都没在地上"或"手一直在天上"的一整段
     没人管 —— 这是 D14 教训 4 在**三个支点**上的推广。

★★★ 本支的独门尺子（像素级，跨支，量"过程形状"）：`px_rise_monotone_ok`
   —— wide 视**全剪影顶缘单调不降**且**总升幅 ≥ 阈值**，**窗口 `[LEGS_DOWN, END]`**。
   ★★ 为什么窗口不从 `START` 起（诚实登记，不是放宽容差）：仰卧时剪影最高点是**脚尖**
     （z **391 mm**），**不是头**（205 mm）。起身第一段是"**腿先落下**"（脚尖 391 → 地面），
     顶缘必然**先下降**。实测（本支 D18_PX 报告）核对：`[0, LEGS_DOWN]` 顶缘确实降
     **N px** ⟹ **D17 的"从 f0 起的顶缘单调"在 D18 上必红，而且是正确的**。
   ⟹ 载体仍然是**顶缘**（与 D17 同一把尺子、同一口径），**只把起点从 `START` 挪到
     `LEGS_DOWN`**：从"腿已落地"那一刻起，人体最高点就必须**一次不停地**升到站姿。
   ★ **反面对照 = 同一把尺子量 `[START, END]`**（含落腿段）**必须红** ——
     它同时把"为什么不能用从 f0 起的顶缘"实测钉死。

★ 帧预算：**36 帧 / 0.600 s @60fps**，非循环（硬上界 40）。
★ 相位 `T_PHASE_D18 = T_PHASE_D17 + 20 = 89.5`（**仅登记**，本支**没有弹道段**）。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python anim_getup_b.py
    SKIP_RENDER=1  只跑门禁不渲图（迭代用）
    D18_TRACE=1    逐帧打印骨盆 / 胸 / 手 / 脚 / 膝的实测值

反向验证（§4 第 7 步，8 组）：
    D18_TP_SEAM_ZERO=1    ① 首帧改零位（接缝断）        ⟹ `seam_in_ok` 红
    D18_TP_NOPUSH=1       ② 抽掉撑地（胸不抬）          ⟹ `chest_rise_ok` 红
    D18_TP_NOTUCK=1       ③ 抽掉收腿（脚不回位）        ⟹ `foot_takeover_ok` 红
    D18_TP_STICKYHAND=1   ④ ★ **手不离地**              ⟹ **`hand_off_ok` 红**（支点交接守卫）
    D18_TP_NOIDLE=1       ⑤ ★ **末帧不给站姿**          ⟹ **`end_matches_idle_ok` 红**（核心守卫）
    D18_TP_DIP=1          ⑥ 造回落（骨盆中途下沉）      ⟹ `rise_monotone_ok` 红
    D18_TP_ENDZERO=1      ⑦ 末帧改零位                  ⟹ `no_snap_stop_ok` / `end_vz_zero_ok` 红
    D18_TP_NOLEGDROP=1    ⑧ ★ **新增** 抽掉"腿落下"     ⟹ **`knee_unfold_start_ok` 红**

★ 本支停用并**登记理由**的判据（照 D17 停用 `ballistic_until_land_ok` 的做法）：
    `ground_hold_ok` / `back_land_ok` / `landing_plateau_ok` / `legs_bounce_ok` /
    `bounce_*` 全族 —— 它们是**贴地族**的判据，本支骨盆要跑 702 mm，载体全部不同。
    `hitstop_present` —— 本支是**主动发力**动作，**没有"命中帧"**。
"""

import json
import math
import os
import struct
import sys

import bpy
from mathutils import Euler, Matrix, Quaternion, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A                     # noqa: E402
import anim_jump_start as JS             # noqa: E402
import anim_ultimate_end as UE           # noqa: E402
import anim_crouch as CR                 # noqa: E402
import probe_c12_baseline as P           # noqa: E402
import probe_d01_guard as PD             # noqa: E402

NAME = "GetUp_B"
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"
SIDES = ("L", "R")

# ★ 接缝真源：上游 D15 的落盘 action + 末帧号（★ 不是 D14 / D16 / D17）
SEAM_ACTION = os.environ.get("D18_SEAM_ACTION", "Knockdown_B")
SEAM_FRAME = int(os.environ.get("D18_SEAM_FRAME", "20"))
# ★ 终点真源：A 族通用站姿锚点
END_ACTION = os.environ.get("D18_END_ACTION", "Idle_01")
END_FRAME = int(os.environ.get("D18_END_FRAME", "0"))
# ★ 相位原点（`anim_knockdown_b.T_PHASE`）—— 本支**只登记**，不参与解算
D17_T_PHASE = 69.5
T_PHASE_D18 = D17_T_PHASE + 20.0                      # 89.5


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
    """量化到 float32 —— F-Curve 关键帧就是按 float32 存的（与 D02~D17 同源）。"""
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


def _clamp(value, lo, hi):
    return max(lo, min(hi, value))


def _smoothstep(x):
    x = _clamp(x, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


# ★★ 腿踝**段内插值口径**（`D18_ANKLE_LINEAR`）：
#     0 = `_smoothstep`（原口径）；1 = 仅 `[TUCK, FOOT_SET]` 段线性；2 = 三段腿踝段全线性。
#   为什么：`_smoothstep` 在**只有 4 个间隔**的短段上，观测增量剖面是
#     `0.156 / 0.344 / 0.344 / 0.156`（= 线性的 **1.375×** 峰值）⟹ 收腿→落脚那两帧
#     的真旋转被顶到 25.5° / 26.6°，而门禁 `no_teleport` 阈值是 **25°/帧**。
#     分段线性是**同类单调插值里峰值速度最低的**（端点逐位不变）
#     ⟹ 直接摊平角速度剖面。与手臂 `PLANT_LINEAR` 同一操守：**摊平剖面，不动端点**。
_ANKLE_LIN_LVL = _env_i("D18_ANKLE_LINEAR", 0)


def _seg(t, linear):
    """段内插值：线性（峰速最低）或 `_smoothstep`；两端逐位相同。"""
    return _clamp(t, 0.0, 1.0) if linear else _smoothstep(t)


def _nearest_equiv(target, ref):
    """返回与 `ref` 相差 360° 整数倍里最接近 `ref` 的那个 `target` 等价表示。"""
    return target + 360.0 * round((ref - target) / 360.0)


def _slerp_dir(a, b, t):
    """两个**方向**之间的球面插值（单位向量）。`t` 已夹到 `[0, 1]`。

    ★★ 为什么必须用它而不是"逐分量插值再归一化"：两方向夹角接近 **180°** 时，
      逐分量插值的合成向量会**靠近原点**，归一化后角速度被放大 `1/sin(夹角)` 倍
      —— D17 实测把 `forearm.L` 的局部欧拉单帧步长顶到 **81.95°**。
      球面插值的角速度**均匀** ⟹ 峰值回到 8~9°/帧。
      这不是放宽容差：改的是**轨迹的角速度剖面**，两端方向逐位不变。
    """
    t = _clamp(t, 0.0, 1.0)
    av = Vector(a)
    bv = Vector(b)
    la, lb = av.length, bv.length
    if la < 1e-9 or lb < 1e-9:
        return Vector(b if la < 1e-9 else a)
    av, bv = av / la, bv / lb
    if t <= 0.0:
        return av
    if t >= 1.0:
        return bv
    dot = max(-1.0, min(1.0, av.dot(bv)))
    if dot > 0.999999:
        return av
    if dot < -0.999999:
        # ★ 严格反向：测地线不唯一。取一条**确定的**垂直方向，避免除零。
        seed = Vector((0.0, 0.0, 1.0))
        if abs(av.dot(seed)) > 0.9:
            seed = Vector((1.0, 0.0, 0.0))
        axis = seed - av * seed.dot(av)
        axis.normalize()
        return (Quaternion(axis, math.pi * t) @ av).normalized()
    omega = math.acos(dot)
    sin_omega = math.sin(omega)
    return (av * (math.sin((1.0 - t) * omega) / sin_omega)
            + bv * (math.sin(t * omega) / sin_omega)).normalized()


def _dir_keys_at(keys, frame, default):
    """方向关键帧（`((f, (x, y, z)), ...)`）的**球面**求值。两端逐位等于端点。"""
    pts = [(float(f), Vector(v)) for f, v in keys]
    if frame <= pts[0][0]:
        return pts[0][1].normalized() if pts[0][1].length > 1e-9 \
            else Vector(default).normalized()
    if frame >= pts[-1][0]:
        return pts[-1][1].normalized() if pts[-1][1].length > 1e-9 \
            else Vector(default).normalized()
    for index in range(len(pts) - 1):
        f0, a = pts[index]
        f1, b = pts[index + 1]
        if f0 <= frame <= f1:
            span = float(f1 - f0)
            if span < 1e-9:
                return b.normalized()
            return _slerp_dir(a, b, (float(frame) - f0) / span)
    return pts[-1][1].normalized()


# =============================================================== 时间轴
#   ★ 节奏：**落腿 4 / 撑 9 / 交接 4 / 收腿 4 / 蹬起 9 / 定 2**（= 36，见清单 §2）
TOTAL = _env_i("D18_TOTAL", 40)
START = 0
LEGS_DOWN = _env_i("D18_LEGS_DOWN", 4)        # ★ D18 独有：双腿从半空落到地面
PLANT = _env_i("D18_PLANT", 7)                # 双掌在身后/身侧撑地（力量型起手）
CHEST_UP = _env_i("D18_CHEST_UP", 11)         # 胸被顶起来的峰值帧
HAND_OFF = _env_i("D18_HAND_OFF", 20)         # ★ 支点交接 1：手掌离地帧
TUCK = _env_i("D18_TUCK", 22)                 # 收腿（膝收到身下）
#   ★★ 踝的**收腿段起点**独立于 `TUCK`。理由：`HAND_OFF_LIFT_KEYS` / `HAND_SPREAD_KEYS` /
#    `HEEL_LIFT_KEYS` 都以 `TUCK` 为键帧，动 `TUCK` 会把这三张表拧乱（实测 `TUCK=19`
#    时 `HAND_OFF_LIFT_DEFAULT` 的键变成 …(21,0.150),(19,0.115),(23,0.050)… **帧号非单调**）。
#    本支只需要**把踝的 `[TUCK, FOOT_SET]` 段拉长**（`TUCK=21` 时该段只有 4 帧，
#    实测 `thigh.L` 真旋转被顶到 25.5 / 26.6°/帧，而 `no_teleport` 阈值是 25°/帧）。
#    ⟹ 另立 `TUCK_LEG`（默认 = `TUCK`，显式置 19 时该段 6 帧、峰值降到 ~0.70×）。
#    ★ 判据窗口 / 元数据 / 清单口径**继续用 `TUCK=21`** —— 这里改的是**轨迹**，不是判据。
TUCK_LEG = _env_i("D18_TUCK_LEG", TUCK - 2)
FOOT_SET = _env_i("D18_FOOT_SET", 30)         # ★ 支点交接 2：双脚接住地面帧（唯一）
RISE_MID = _env_i("D18_RISE_MID", 34)         # 蹬伸中段
STAND = _env_i("D18_STAND", 38)               # 站直（骨盆 830 mm）＝ 逐位 = `Idle_01@0`
DIR_END = _env_i("D18_DIR_END", HAND_OFF)
SELF_HOLD = STAND
CANCEL = STAND
END = TOTAL
if not (START < DIR_END <= HAND_OFF
        and START < LEGS_DOWN < PLANT < CHEST_UP < HAND_OFF
        < TUCK < FOOT_SET < RISE_MID < STAND <= TOTAL):
    raise RuntimeError("相位不自洽：LEGS_DOWN=%d DIR_END=%d PLANT=%d CHEST_UP=%d "
                       "HAND_OFF=%d TUCK=%d FOOT_SET=%d RISE_MID=%d STAND=%d TOTAL=%d"
                       % (LEGS_DOWN, DIR_END, PLANT, CHEST_UP, HAND_OFF, TUCK,
                          FOOT_SET, RISE_MID, STAND, TOTAL))

# =============================================================== 反验证旋钮
SEAM_ZERO = _env_b("D18_TP_SEAM_ZERO")
NO_PUSH = _env_b("D18_TP_NOPUSH")
NO_TUCK = _env_b("D18_TP_NOTUCK")
STICKY_HAND = _env_b("D18_TP_STICKYHAND")
#   ★ 反验证 ④ 的**延长量**（帧）。原来是「全程钉地」`return world`，**做不到让
#     `hand_off_ok` 见红**（实测）：臂长在骨盆升到 830 mm 后够不着地 ⟹ 手掌被迫停在
#     **高处** ⟹ `hand_off_violations=[]`，红的是 `reach_ok`，目标守卫毫无反应。
#     ⟹ 只把钉地窗口延长 2 帧（够得着），`f > HAND_OFF` 时手**仍在地上** ⟹ 必红。
STICKY_OFF_EXT = _env_i("D18_TP_STICKY_EXT", 1)
NO_IDLE = _env_b("D18_TP_NOIDLE")
DIP = _env_b("D18_TP_DIP")
END_ZERO = _env_b("D18_TP_ENDZERO")
NO_LEGDROP = _env_b("D18_TP_NOLEGDROP")

# =============================================================== 竖直 / 水平通道
#   ★★ 本支**没有弹道段**：骨盆沿一条**单调上升**的曲线从 128 mm 走到 830 mm。
#     四段（落腿 / 撑地 / 交接 / 起立）只是**支点**在换，骨盆从不回落。
#   ★★ 撑地期 `[START, HAND_OFF]` 骨盆只升 **104 mm**（128 → 232）—— 与 D17 同一条设计：
#      躯干在撑地期保持**近水平**，肩就停在低位，手才够得到地。
#      实测 D17：躯干一旦按原稿早起，肩 z 冲到 736 mm，`|掌目标−肩|` 涨到 816 mm
#      （臂长 650）⟹ `reach_ok` 物理上必然红。撑起改到**手离地之后**发力。
#   ★ 骨盆"静息"高度：`@loc` 里要的是**世界位移**，故 = 目标 z − 静息 900 mm。
#     （与 D17 同一约定；末帧骨 830 mm 即 `Idle_01@0` ⟹ 位移 −70 mm。）
Z_PELVIS_REST = 0.900


def _parse_fv(spec):
    """`"f:v,f:v,..."` → `((f, v), ...)`（整数帧、浮点值）。"""
    try:
        return tuple((int(a), float(b)) for a, b in
                     (item.split(":") for item in spec.split(",") if item.strip()))
    except Exception:  # noqa: BLE001
        return ()


# =============================================================== 时间重参数化
#   ★★★ 「路径保持重采样」（path-preserving resample）—— 清单 §10.6 的处方。
#
#   问题（已实测，见 `doc/D18_速度门禁诊断.md` §10.4/§10.6）：本支竖直跨度 702 mm
#   是全项目最大（比 D17 的 610 还大 92 mm），相位键在**源帧空间**只有 36~37 帧
#   ⟹ 撑地段 / 收腿段 / 上摆段的**真实局部角速度**超 25°/帧（`no_teleport` 红，
#   放大系数 0.76~0.99 ⟹ **不是表示问题**）。而**挪相位键**会同时挪动锚点位姿
#   （`PELVIS_Z_KEYS` / `*_LIFT_KEYS` / 锚点全部由相位常量构造）⟹ 路径变了 ⟹
#   本支累计 130+ 组相位键实验、0 绿。`anim_lib.py` 的 `sample_animation` 逐帧取
#   `pose_bone.rotation_euler`，所以「帧距」是唯一没被动过的自由度。
#
#   处方：**不动任何键表、不动任何世界目标**，只在「输出帧 → 源帧」之间插一层
#   单调映射 `g`。`solve_pose(arm, g(n))` 在**同一条路径**上取更密的采样点 ⟹
#   每帧角量按 1/g' 等比缩小，而全部**世界空间**判据（`rise_reach` / `rise_monotone`
#   / `foot_slide` / `sole_ground` / `hand_off` / `foot_takeover` / `chest_rise` /
#   `end_matches_idle` / `seam_in`）**一条都不动** —— 它们量的是路径，不是帧号。
#
#   用法：`D18_OUT_TOTAL=46`（输出 46 帧），或 `D18_WARP="n:src,n:src,..."` 自定义节点。
#   ★★ 默认值 = **40**：与源相位表 `TOTAL=40` **相等** ⟹ `g = 恒等`、逐位无重采样。
#      （清单 §2 的硬上界是 40 帧；本支实测 40 帧即可让 `no_teleport` 落到
#      **24.755°/帧**（阈值 25），故**不需要**任何加密采样。若将来相位表加长，
#      这里必须同步，否则会静默引入重采样。）
OUT_TOTAL = _env_i("D18_OUT_TOTAL", 40)

#   ★★★ 相位对齐（**必须**）：源帧的每个相位边界都要**精确落在整数输出帧**上。
#   理由（本支实测）：第一次只按 `round(WARP_OUT(p))` 取窗口边界，边界帧的源帧是
#   26.98 而不是 27.0 ⟹ 落脚/贴地/不滑动四条窗口判据在**边界外 0.02 帧**处取样
#   ⟹ `sole_ground_ok` / `no_foot_slide_ok` / `hand_off_ok` 全部转红，而世界姿态
#   其实**没变**（纯粹是窗口错位）。↦ 把每条源相位边界钉成输出帧节点。
_SRC_PHASES = (START, LEGS_DOWN, PLANT, CHEST_UP, HAND_OFF, TUCK, FOOT_SET,
               RISE_MID, STAND, TOTAL)

_WARP_SPEC = os.environ.get("D18_WARP", "").strip()
if _WARP_SPEC:
    _WARP_NODES = tuple(sorted(_parse_fv(_WARP_SPEC)))
else:
    _pts, _last = [], -1
    for _p in _SRC_PHASES:
        _o = int(round(_p * OUT_TOTAL / float(TOTAL)))
        if _o <= _last:
            _o = _last + 1
        _pts.append((_o, float(_p)))
        _last = _o
    _pts[0] = (0, float(START))
    _pts[-1] = (OUT_TOTAL, float(TOTAL))
    _WARP_NODES = tuple(_pts)

if _WARP_NODES[0][0] != 0 or _WARP_NODES[-1][0] != OUT_TOTAL:
    raise RuntimeError("D18_WARP 节点必须首尾覆盖 [0, %d]，实得 %s"
                       % (OUT_TOTAL, _WARP_NODES))
if any(b[1] < a[1] for a, b in zip(_WARP_NODES, _WARP_NODES[1:])):
    raise RuntimeError("D18_WARP 必须单调不降：%s" % (_WARP_NODES,))


def WARP_SRC(frame):
    """输出帧 → **源帧**（float；单调不减；首尾逐位 `START` / `TOTAL`）。"""
    value = float(frame)
    for (na, va), (nb, vb) in zip(_WARP_NODES, _WARP_NODES[1:]):
        if value <= nb:
            if nb == na:
                return float(vb)
            u = (value - na) / float(nb - na)
            return float(va) + u * float(vb - va)
    return float(_WARP_NODES[-1][1])


def WARP_OUT(src):
    """源帧 → 输出帧（相位边界**精确命中**节点；其余四舍五入）。"""
    value = float(src)
    for (na, va), (nb, vb) in zip(_WARP_NODES, _WARP_NODES[1:]):
        if abs(value - vb) < 1e-9:
            return int(nb)
        if value < vb:
            if vb == va:
                return int(na)
            u = (value - va) / float(vb - va)
            return int(round(na + u * (nb - na)))
    return int(_WARP_NODES[-1][0])


def resample_keyframes(keyframes):
    """路径保持重采样：**源帧序** `[(f, pose)]` → **输出帧序** `[(n, pose)]`。

    - 对每根骨的**局部旋转**做四元数 slerp（取短路径），`@loc` 逐分量线性；
      **不解 IK、不动任何世界目标**。
    - `WARP_SRC(n)` 在所有相位节点上是**整数源帧** ⟹ 节点帧的姿态**逐位原样**返回
      （绝不插值）⟹ `seam_in_ok` / `end_matches_idle_ok` / `foot_takeover_ok` /
      `hand_off_ok` / `sole_ground_ok` 在这些帧上与源时间轴**逐位一致**。
    - 调用顺序必须是**源帧递增**（`keyframes` 已经是）。
    """
    src = {int(f): p for f, p in keyframes}
    last = max(src)
    out = []
    for n in range(0, OUT_TOTAL + 1):
        s = WARP_SRC(n)
        i0 = int(math.floor(s + 1e-9))
        i1 = min(i0 + 1, last)
        t = s - i0
        if i1 <= i0 or t <= 1e-9:
            out.append((n, _copy_pose(src[min(i0, last)])))
            continue
        if t >= 1.0 - 1e-9:
            out.append((n, _copy_pose(src[i1])))
            continue
        pa, pb = src[i0], src[i1]
        blended = {}
        for name in set(pa) | set(pb):
            if name == "@loc":
                la, lb = pa.get("@loc", {}), pb.get("@loc", {})
                loc = {}
                for key in set(la) | set(lb):
                    u = tuple(la.get(key, (0.0, 0.0, 0.0)))
                    v = tuple(lb.get(key, u))
                    loc[key] = tuple(x + (y - x) * t for x, y in zip(u, v))
                blended["@loc"] = loc
                continue
            a = tuple(pa.get(name, (0.0, 0.0, 0.0)))
            b = tuple(pb.get(name, a))
            qa = Euler([math.radians(v) for v in a], "XYZ").to_quaternion()
            qb = Euler([math.radians(v) for v in b], "XYZ").to_quaternion()
            if qa.dot(qb) < 0.0:
                qb = Quaternion((-qb.w, -qb.x, -qb.y, -qb.z))
            blended[name] = tuple(
                math.degrees(v) for v in qa.slerp(qb, t).to_euler("XYZ"))
        out.append((n, blended))
    return out


def hold_keyframes(keyframes, at, count):
    """★ 反验证 ④ 专用：把**输出帧** `at` 的姿态**多按住** `count` 帧。

    物理含义 = 「**手不离地**」：撑地期结束时手本该按期抬起，这里让它**继续按在地上**
    若干帧。纯**输出帧空间**操作 ——
      · 相位边界 `_OUT_PHASES` **不动**（`HAND_OFF` 仍在 `at`），
        因此门禁窗口 `(HAND_OFF, TOTAL]` 不变，而落在窗口里的那些帧手仍在地面
        ⟹ `hand_off_ok` 的 `off` 侧**必有违反** ⟹ **必须红**。
      · 只改姿态序列、不改任何键表 / 世界目标 ⟹ 不影响其它判据的**定义**。
    """
    count = int(count)
    if count <= 0:
        return keyframes
    table = {int(n): p for n, p in keyframes}
    held = table.get(int(at))
    if held is None:
        return keyframes
    out = []
    for n, pose in keyframes:
        if int(at) < int(n) <= int(at) + count:
            out.append((n, _copy_pose(held)))
        else:
            out.append((n, pose))
    return out


#   ★ 相位常量**两套**（★★ 这是本支最容易出错的地方）：
#     · 键表（`PELVIS_*_KEYS` / `*_LIFT_KEYS` / `ARM_ANCHORS` / 踝目标 …）一律用
#       **源帧空间**的原名 —— 它们必须在同一条路径上被求值，否则路径就变了。
#     · 门禁窗口 / 帧标记 / 元数据用 **输出帧空间**（`_OUT_PHASES`），因为
#       `samples` / Action 的帧号是输出帧。
#     ★ 门禁函数 `getup_assertions` 里用 `_OUT_PHASES` **就地重绑**这 10 个名字。
_OUT_PHASES = tuple(WARP_OUT(v) for v in
                    (LEGS_DOWN, PLANT, CHEST_UP, HAND_OFF, TUCK, FOOT_SET,
                     RISE_MID, STAND, TOTAL, END))


_Z_KEYS_SPEC = os.environ.get("D18_PELVIS_Z_KEYS", "").strip()
_Y_KEYS_SPEC = os.environ.get("D18_PELVIS_Y_KEYS", "").strip()
PELVIS_Z_KEYS = _parse_fv(_Z_KEYS_SPEC) or (
    (START, 128.0), (LEGS_DOWN, 152.0), (PLANT, 172.0), (CHEST_UP, 250.0),
    (HAND_OFF, 420.0), (TUCK, 520.0), (FOOT_SET, 620.0), (RISE_MID, 730.0),
    (STAND, 830.0), (END, 830.0))
#   ★ 水平 **+470 → 0**（符号与 D17 的 −550 → 0 **相反**）
PELVIS_Y_KEYS = _parse_fv(_Y_KEYS_SPEC) or (
    (START, 470.0), (LEGS_DOWN, 452.0), (PLANT, 430.0), (CHEST_UP, 398.0),
    (HAND_OFF, 350.0), (TUCK, 290.0), (FOOT_SET, 220.0), (RISE_MID, 110.0),
    (STAND, 0.0), (END, 0.0))
# ★ 反验证 ⑥：造一次中途回落（骨盆在上升途中沉一下）⟹ `rise_monotone_ok` 必须红
#
#   ★★★ 这里踩过一次**本项目点名过 5 次的坑**（「旋钮没真的接进代码」）：
#     原写法把键帧**写死成 `(28, −58)` / `(30, −30)`**，那是**旧相位**（`FOOT_SET=27`/
#      `RISE_MID=31`）时代的帧号。本支相位改为 `FOOT_SET=30` / `RISE_MID=34` 之后，
#      `(FOOT_SET, 0) → (28, −58) → (30, −30) → (RISE_MID, 0)` 的帧号**不再单调**
#     （30 后面跟 28）⟹ `UE.pwl` 求值退化为恒 0 ⟹ **旋钮静默失效**。
#     实测（`_d18_rv_rv6.log`）：`D18_TP_DIP=1` 时 `failed=[]`、`non_ok_bools=[]`，
#     即**负对照完全没红** —— 正是清单 §4 步 7 警告的那种假绿。
#   ⟹ 改成**相位相对**：回落窗口锚在 `[FOOT_SET, RISE_MID]` 内，随重定时自动跟随。
_DIP_MID = max(FOOT_SET + 1, min(FOOT_SET + 2, RISE_MID - 1))
DIP_KEYS = ((0, 0.0), (FOOT_SET, 0.0), (_DIP_MID, -58.0), (RISE_MID, 0.0),
            (END, 0.0))


def pelvis_z_at(frame):
    z = UE.pwl(PELVIS_Z_KEYS, float(frame), PELVIS_Z_KEYS[0][1])
    if DIP:
        z += UE.pwl(DIP_KEYS, float(frame), 0.0)
    if NO_PUSH and PLANT <= frame <= HAND_OFF:
        #   ★ 反验证 ②：抽掉撑地推起。原来只把 `arch_of` 归零（拱背只占胸净升的
        #   6.8%），`chest_rise_ok` **不红** ⟹ 负对照失效。改成**把推起窗口内的骨盆
        #   竖直通道钉在 `PLANT` 高度** ⟹ 胸骨尾端不再抬升 ⟹ `chest_rise_ok` 必红。
        z = UE.pwl(PELVIS_Z_KEYS, float(PLANT), PELVIS_Z_KEYS[0][1])
    return z / 1000.0


def pelvis_y_at(frame):
    return UE.pwl(PELVIS_Y_KEYS, float(frame), PELVIS_Y_KEYS[0][1]) / 1000.0


def pelvis_vz_at(frame):
    return (pelvis_z_at(frame) - pelvis_z_at(frame - 1)) * 1000.0


# =============================================================== 躯干通道
TORSO_PROG = {
    "root": ((0, 0.0), (END, 0.0)),
    "pelvis": ((0, 0.0), (LEGS_DOWN, 0.02), (PLANT, 0.05), (CHEST_UP, 0.09),
               (HAND_OFF, 0.14), (TUCK, 0.32), (FOOT_SET, 0.54), (RISE_MID, 0.86),
               (STAND, 1.0), (END, 1.0)),
    "spine_01": ((0, 0.0), (LEGS_DOWN, 0.03), (PLANT, 0.07), (CHEST_UP, 0.12),
                 (HAND_OFF, 0.18), (TUCK, 0.38), (FOOT_SET, 0.60), (RISE_MID, 0.88),
                 (STAND, 1.0), (END, 1.0)),
    "spine_02": ((0, 0.0), (LEGS_DOWN, 0.03), (PLANT, 0.07), (CHEST_UP, 0.12),
                 (HAND_OFF, 0.18), (TUCK, 0.38), (FOOT_SET, 0.60), (RISE_MID, 0.88),
                 (STAND, 1.0), (END, 1.0)),
    "chest": ((0, 0.0), (LEGS_DOWN, 0.04), (PLANT, 0.10), (CHEST_UP, 0.16),
              (HAND_OFF, 0.24), (TUCK, 0.46), (FOOT_SET, 0.68), (RISE_MID, 0.91),
              (STAND, 1.0), (END, 1.0)),
    "neck": ((0, 0.0), (LEGS_DOWN, 0.05), (PLANT, 0.12), (CHEST_UP, 0.19),
             (HAND_OFF, 0.27), (TUCK, 0.50), (FOOT_SET, 0.72), (RISE_MID, 0.93),
             (STAND, 1.0), (END, 1.0)),
    "head": ((0, 0.0), (LEGS_DOWN, 0.05), (PLANT, 0.11), (CHEST_UP, 0.18),
             (HAND_OFF, 0.26), (TUCK, 0.49), (FOOT_SET, 0.71), (RISE_MID, 0.92),
             (STAND, 1.0), (END, 1.0)),
}
# "拱起"（度，正数 = rx 往负方向压，把胸腔顶起来 / 抬头）—— 脊柱**伸展**，
#   俯卧与仰卧是同一个局部动作（撑地拱背 / 桥式拱背），符号相同。
ARCH_KEYS = {
    "pelvis": ((0, 0.0), (LEGS_DOWN, 1.0), (PLANT, 3.0), (CHEST_UP, 8.0),
               (HAND_OFF, 9.0), (TUCK, 5.0), (FOOT_SET, 1.0), (RISE_MID, 0.0),
               (END, 0.0)),
    "chest": ((0, 0.0), (LEGS_DOWN, 5.0), (PLANT, 18.0), (CHEST_UP, 36.0),
              (HAND_OFF, 42.0), (TUCK, 26.0), (FOOT_SET, 10.0), (RISE_MID, 2.0),
              (END, 0.0)),
    "neck": ((0, 0.0), (LEGS_DOWN, 3.0), (PLANT, 10.0), (CHEST_UP, 18.0),
             (HAND_OFF, 20.0), (TUCK, 10.0), (FOOT_SET, 3.0), (RISE_MID, 0.0),
             (END, 0.0)),
    "head": ((0, 0.0), (LEGS_DOWN, 3.0), (PLANT, 13.0), (CHEST_UP, 26.0),
             (HAND_OFF, 28.0), (TUCK, 14.0), (FOOT_SET, 4.0), (RISE_MID, 0.0),
             (END, 0.0)),
}

#   ★★ 拱起整体缩放（标定用旋钮）：`chest_rise_ok` 要"撑地把胸顶起来"，
#      而"拱起"正是唯一能把**胸骨尾端**抬离地板的通道（骨盆只升 78 mm）。
#   ★★★ **符号是 D18 的镜像修正，不是调参**：`ARCH_KEYS` 沿用 D17 的数值，
#      但 D17 是**俯卧**（头在 −y 端）、D18 是**仰卧**（头在 +y 端）——
#      `rx -= arch` 在俯卧族把胸**抬离**地面，在仰卧族把胸**压向**地面。
#      实测铁证（`D18_ARCH_SCALE=+1.0`，即照抄 D17 符号）：`f=12` 胸骨尾端
#      z = **158.9 mm < 骨盆 184.0 mm** —— 上胸**翻到骨盆下面去了**，
#      `chest_rise_ok` 只 +29.4 mm。取负号后同帧 = **459.1 mm**，谱系正常。
#   ★ 幅度 **−0.20** 由**手臂可达性**标定（不是拍的）：撑地期掌钉在地上不动，
#     肩随躯干上抬 ⟹ `|掌−肩|` 单调变长；实测 `palm_reach` 比值
#     `arch=−0.10/0.20/0.30/0.40` ⟹ **0.983 / 0.984 / 0.986 / 1.004**，
#     只有 `≥ −0.30` 能守住 `reach_ok`（阈值 0.995）。取 **−0.20** 留双倍余量。
ARCH_SCALE = _env_f("D18_ARCH_SCALE", -0.20)


def arch_of(name, frame):
    if NO_PUSH:
        return 0.0
    keys = ARCH_KEYS.get(name)
    if keys is None:
        return 0.0
    return ARCH_SCALE * UE.pwl(keys, float(frame), 0.0)


# =============================================================== 参考朝向交接
NO_ROLL_MIX = _env_b("D18_TP_NOROLLMIX")
ARM_ROLL_TAIL = os.environ.get("D18_ARM_ROLL_TAIL", "1").strip() not in (
    "", "0", "false", "False")
ARM_ROLL_PENALTY_DEG = _env_f("D18_ARM_ROLL_PENALTY", 20.0)
# ★ 臂骨专用"逃离 |ry|≈90° 万向节锁"的代价项（默认 0/0 = 与旧行为逐位一致）。
#   两条通道：
#     · `ARM_Y_SAFE/ARM_Y_WEIGHT`：硬阈值罚分（超过 safe 的部分线性罚）。
#     · `ARM_Y_SOFT/ARM_Y_MID/ARM_Y_SIGMA`：以 90° 为中心的高斯"软墙"，
#       即使 `|ry| < safe` 也会被推离锁心（锁心附近 1° 的欧拉表示最病态）。
ARM_Y_SAFE = _env_f("D18_ARMYSAFE", 88.0)
ARM_Y_WEIGHT = _env_f("D18_ARMYWEIGHT", 0.0)
ARM_Y_SOFT = _env_f("D18_ARMYSOFT", 0.0)
ARM_Y_MID = _env_f("D18_ARMYMID", 90.0)
ARM_Y_SIGMA = _env_f("D18_ARMYSPREAD", 12.0)
HEAD_FREEZE = max(0, _env_i("D18_HEAD_FREEZE", 0))
PLANT_LINEAR = (os.environ.get("D18_PLANT_LINEAR", "1").strip()
                not in ("", "0", "false", "False"))
TAIL_GRID_MIX = _env_f("D18_TAIL_GRID_MIX", 0.98)
ROLL_MIX_END = _env_i("D18_ROLL_MIX_END", STAND - 1)
LEG_ROLL_TAIL = os.environ.get("D18_LEG_ROLL_TAIL", "1").strip() not in (
    "", "0", "false", "False")


# ★★★ 滚转修正的**作用窗口**（`D18_ROLLWIN_OFF="fa:fb"`，闭区间）。
#
#   为什么必须有这个窗口 —— 本支**最后一次实测到的真根因**：
#
#   `_roll_return` 的参考朝向是这样**搬运**到当前姿态的：
#       `ref_zero = rotation_difference(ZERO_DIR[name], direction_now) @ ZERO_BASIS[name]`
#   即"把接缝朝向按**最小旋转**转到当前骨轴方向"。这个搬运在 `direction_now`
#   与 `ZERO_DIR` **接近反平行**时会**整个翻掉**（`rotation_difference` 的测地线
#   不唯一，轴的选择在此处跳变）。
#
#   `D18_ROLLDBG` 实测（`forearm.R`，`ang_now_refzero` = 当前朝向离零位参考的夹角）：
#       f15 8.68° → f16 18.79° → f17 17.66° → **f18 83.76°** → f19 119.16° → f20 135.81°
#   而**同一段**骨的骨轴方向是连续摆过去的。⟹ 那一跳**不是动作**，是参考搬运的翻转；
#   滚转修正权重是 **1.0**（`always`）⟹ 求解器为了"追上"这个翻转的参考，
#   在 2~3 帧里硬转过 **66°/35°** ⟹ `no_teleport` 红（真旋转 `dw` = 35.95/43.69°，
#   `D18_EULERDBG` 已证实**不是欧拉表示跳**）。
#   `hand.R` 同源（`ang_now_refzero` f22 = 275.95°）。
#
#   ⟹ 正解不是调参，而是**限定滚转修正的作用域**：它的职责是"让**接缝附近**与
#   **终点附近**的臂扭转与参考一致"。手臂交接段（手掌离地、双臂摆动换相）里，
#   臂的朝向完全由 IK + `hand_dir_of` 决定，**不需要**滚转修正，反而是它在那一段
#   制造了假动作。窗口外权重乘 0 ⟹ 逐位退回纯 IK。
#   ★ 窗口默认 = **关闭**（`D18_ROLLWIN_OFF=` 空 ⟹ `_ROLLWIN_OFF = None`）。
#     这个窗口曾是**早期一版布局**（`HAND_OFF=18/TUCK=20/FOOT_SET=27`）的最优解；
#     在**定稿布局**（`HAND_OFF=20/TUCK=22/FOOT_SET=30`）下实测它**反而变差**：
#     开窗 32.779°/帧（`[35, shin.R]`）vs 关窗 **24.755°/帧**。原因是定稿布局把臂链
#     交接改成 `ARM_ANCHORS=(HAND_OFF-1, HAND_OFF+1, …)` 之后，"参考翻转"与"锚点
#     交接"**不再重叠** ⟹ 滚转修正不再制造假动作 ⟹ 此时关掉它等于丢掉真实扭转。
#     ⟹ 保留旋钮（是一条**可复现的负结果**，便于将来重定时对照），但**默认关闭**。
_ROLLWIN_OFF_SPEC = os.environ.get(
    "D18_ROLLWIN_OFF", "").strip()
_ROLLWIN_OFF = None
if _ROLLWIN_OFF_SPEC:
    try:
        _a, _b = (int(v) for v in _ROLLWIN_OFF_SPEC.split(":"))
        _ROLLWIN_OFF = (min(_a, _b), max(_a, _b))
    except Exception:  # noqa: BLE001
        _ROLLWIN_OFF = None
# ★ 边界斜坡帧数（`D18_ROLLWIN_RAMP`）：0 = 保持原硬开关；>0 = 帐篷式平滑。
_ROLLWIN_RAMP = max(0, _env_i("D18_ROLLWIN_RAMP", 0))
# ★★ 窗口内的**残留权重**（`D18_ROLLWIN_W`）：0 = 完全交给 IK（原行为）；
#    >0 = 仍施加 `W` 比例的滚转修正。用来把「参考翻转」造成的硬补偿**按比例摊薄**
#    到多帧上（0 与 1 之间是连续谱），而不是只有"全钉/全放"两档。
_ROLLWIN_W = max(0.0, min(1.0, _env_f("D18_ROLLWIN_W", 0.0)))


def roll_scope(frame):
    """滚转修正的作用域权重：窗口内 0（完全交给 IK）。

    ★★ 硬开关（`ramp = 0`）会在窗口边界制造**扭转不连续**：窗口外滚转修正把臂的
      绕轴扭转钉到"接缝参考"，窗口内不钉 ⟹ 边界那一帧的**真实世界朝向**凭空跳
      20~36°（实测 `forearm.R` f15 `dw=10.46°` → f16 `dw=36.10°`，而同一帧骨轴
      方向只转了 12.3° ⟹ 24° 全是**扭转跳**）⟹ `no_teleport` 红。
      ⟹ `ramp > 0` 时把开关变成**帐篷**：窗口边界外 `r` 帧内平滑过渡
      `1 → 0`（与 `0 → 1`），把扭转跳摊到 `r` 帧上。
    """
    if _ROLLWIN_OFF is None:
        return 1.0
    a, b = _ROLLWIN_OFF
    if _ROLLWIN_RAMP <= 0:
        return _ROLLWIN_W if a <= frame <= b else 1.0
    r = float(_ROLLWIN_RAMP)
    if frame < a - r or frame > b + r:
        return 1.0
    if a <= frame <= b:
        return _ROLLWIN_W
    if frame < a:
        return _ROLLWIN_W + (1.0 - _ROLLWIN_W) * _smoothstep(
            (float(a) - float(frame)) / r)
    return _ROLLWIN_W + (1.0 - _ROLLWIN_W) * _smoothstep(
        (float(frame) - float(b)) / r)


def roll_mix_at(frame, bone=None):
    """参考朝向从**零位（仰卧）**交接到 **`Idle_01@0`（站姿）** 的权重。"""
    if NO_ROLL_MIX:
        return 0.0
    return _smoothstep((float(frame) - float(FOOT_SET))
                       / float(ROLL_MIX_END - FOOT_SET))


def knee_dir_at(side, frame):
    """膝鼓出方向：`KNEE_DIR`（接缝）→ `END_KNEE_DIR`（`Idle_01@0`）。"""
    t = roll_mix_at(frame, "thigh." + side)
    a = KNEE_DIR[side]
    if t <= 0.0:
        return a
    b = Vector(END_KNEE_DIR[side])
    if t >= 1.0:
        return b
    return _slerp_dir(a, b, t)


# =============================================================== 手（拳）目标
def _parse_num_keys(spec, default):
    """`"f:v,f:v,..."` → `((f, v), ...)`；校验帧序单调，否则回退 `default`。"""
    try:
        out = tuple((int(a), float(b)) for a, b in
                    (item.split(":") for item in spec.split(",") if item.strip()))
    except Exception:  # noqa: BLE001
        return default
    if len(out) < 2 or any(out[i][0] >= out[i + 1][0]
                           for i in range(len(out) - 1)):
        return default
    return out


HAND_OFF_LIFT_DEFAULT = ((0, 0.0), (HAND_OFF, 0.0), (HAND_OFF + 1, 0.060),
                         (HAND_OFF + 2, 0.110), (HAND_OFF + 3, 0.140),
                         (HAND_OFF + 4, 0.150), (TUCK, 0.115),
                         (FOOT_SET - 2, 0.050), (FOOT_SET, 0.0), (END, 0.0))
_LIFT_SPEC = os.environ.get("D18_LIFT_KEYS", "").strip()
HAND_OFF_LIFT_KEYS = (_parse_num_keys(_LIFT_SPEC, HAND_OFF_LIFT_DEFAULT)
                      if _LIFT_SPEC else HAND_OFF_LIFT_DEFAULT)
HAND_MIX_END = _env_i("D18_HAND_MIX_END", HAND_OFF + 8)      # 28
HAND_MIX_POW = _env_f("D18_HAND_MIX_POW", 1.0)
#   ★★★ 臂链末段逐分量插值的**起点**（`ARM_MIX_FROM`）是本支一处"假动作"的来源：
#     取 `HAND_MIX_END = HAND_OFF + 8` 时，等于把**肘的 172° 展开压进 9 帧**（实测峰值
#     `forearm.R` **28.9°/帧**）。改到 `HAND_OFF + 2`（提前 6 帧开始交接）后臂链峰值
#     被压掉，且 `hand_off_ok` / `reach_ok` / `hand_plant_ok` 全部不受影响。
ARM_MIX_FROM = _env_i("D18_ARM_MIX_FROM", HAND_OFF + 2)
TAIL_ARM = {}
ARM_MIX_TO = _env_i("D18_ARM_MIX_TO", 0)
_ANCHORS_SPEC = os.environ.get("D18_ARM_ANCHORS")
if _ANCHORS_SPEC is None:
    # ★★ D18 与 D17 的**关键差异**：D17 起点手就在地上 ⟹ 撑地段 `[START, HAND_OFF]`
    #    两端都是"掌贴地"，欧拉 slerp 全程贴地，没毛病。
    #    D18 起点手掌在**地面之下 82 mm**（压在身上），终点在身侧撑地 ——
    #    这两支欧拉的 slerp **不保证**中间帧的掌仍钉在地上：实测 `f = 8` 时
    #    掌网格最低点被拉到 **−121 mm**（真实 IK 解是 −29 mm）⟹ `hand_plant_ok` 必红。
    #    ⟹ **去掉 `START` 这个锚点**，让撑地段走真实 IK（`fist_target` 是
    #    **绝对世界目标**，掌天然钉地）。`HAND_OFF` 之后的锚点照留（D17 原设计）。
    #
    #   ★★★ **本支最后一处假动作的正解**（实测得出，不是猜的）：
    #    锚点原来是 `(HAND_OFF, HAND_OFF+1, FOOT_SET-1, STAND)`。`HAND_OFF` 那一帧
    #    正是"掌离地"的**支点交接帧**：它的姿态由 IK 给出（手还压在地上），
    #    而 `HAND_OFF+1` 起改由锚点插值接管 ⟹ 交接处臂骨欧拉在**相邻两帧**之间
    #    被改了参考支 ⟹ 实测 f17→f18 `hand.R` **26.5°/帧**、`forearm.R` 24.6°/帧
    #    （而同一帧手骨的世界朝向只转了 **8.05°** ⟹ 是**表示跳**，不是动作）。
    #    ⟹ 把锚点**整段前移一帧**到 `HAND_OFF-1` 起（`(HAND_OFF-1, HAND_OFF+1, ...)`）
    #      之后，交接提前一帧、错开 IK 的支点帧，**臂链全部超限点消失**
    #      （实测：臂骨最大步长从 26.5° 降到 < 21°）。
    ARM_ANCHORS = (HAND_OFF - 1, HAND_OFF + 1, FOOT_SET - 1, STAND)
else:
    ARM_ANCHORS = tuple(sorted(set(
        int(_t) for _t in _ANCHORS_SPEC.replace(" ", "").split(",")
        if _t.lstrip("-").isdigit())))
ANCHOR_SLERP = (os.environ.get("D18_ANCHOR_SLERP", "1").strip()
                not in ("", "0", "false", "False"))
ANCHOR_SLERP_UNTIL = _env_i("D18_ANCHOR_SLERP_UNTIL", HAND_OFF)


def _hand_mix_s(u):
    u = max(0.0, min(1.0, float(u)))
    if HAND_MIX_POW <= 0.0:
        return _smoothstep(u)
    return u ** HAND_MIX_POW


HAND_SPREAD_M = _env_f("D18_HAND_SPREAD", 0.062)
HAND_SPREAD_KEYS = ((0, 0.0), (HAND_OFF, 0.0), (HAND_OFF + 1, 0.10),
                    (HAND_OFF + 2, 0.32), (TUCK, 1.0), (FOOT_SET, 0.46),
                    (RISE_MID, 0.0), (STAND, 0.0), (END, 0.0))


def hand_spread(frame):
    """收手期的侧向张手量（米）。撑地期与站定后恒为 0 ⟹ 不影响两条接缝。"""
    return HAND_SPREAD_M * UE.pwl(HAND_SPREAD_KEYS, float(frame), 0.0)


def hand_lift(frame):
    return UE.pwl(HAND_OFF_LIFT_KEYS, float(frame), 0.0)


def _lerp_keys_clamped(keys, frame, default):
    """分段**线性**求值（键按帧升序，`frame` 夹在两端之间）。

    ★ 为什么需要它：`UE.pwl` 是 PCHIP，键距**不均匀**时端点导数会过冲 ——
      D17 的 `PLANT_KEYS` 键距 `(0→4)=4,(4→5)=1,(5→6)=1,(6→9)=3` 使
      前端速度被放大 **1.5×**，正是 `f=1` 那一步 `forearm.R` 真实世界旋转 39.6° 的来源。
      分段线性把速度摊平到逐段常数，端点不吃过冲。
    """
    keys = sorted(keys, key=lambda kv: kv[0])
    if not keys:
        return list(default)
    if frame <= keys[0][0]:
        return list(keys[0][1])
    if frame >= keys[-1][0]:
        return list(keys[-1][1])
    for (fa, va), (fb, vb) in zip(keys, keys[1:]):
        if fa <= frame <= fb:
            if fb == fa:
                return list(vb)
            u = (float(frame) - float(fa)) / float(fb - fa)
            return [a + (b - a) * u for a, b in zip(va, vb)]
    return list(keys[-1][1])


def fist_target(arm, side, frame):
    """拳世界目标。

    `f ≤ HAND_OFF` ⟹ **世界落掌点**（手钉在地上）。
    `f >  HAND_OFF` ⟹ **肩 + 偏移**，偏移从"落掌偏移"过渡到 `Idle_01@0` 的肩-拳偏移。
    """
    shoulder = Vector(A.bone_world(arm, "upperarm." + side, "head"))
    if PLANT_LINEAR:
        world = Vector(_lerp_keys_clamped(PLANT_KEYS[side], float(frame),
                                          SEAM_FIST[side]))
    else:
        world = pwl_vec(PLANT_KEYS[side], float(frame), SEAM_FIST[side])
    if frame <= HAND_OFF:
        return world
    s = _hand_mix_s((float(frame) - HAND_OFF) / (HAND_MIX_END - HAND_OFF))
    off_a = world - shoulder
    off_b = Vector(END_OFF[side])
    off = off_a * (1.0 - s) + off_b * s
    off.z += hand_lift(frame)
    # ★ 侧向张手：`L` 往 +x、`R` 往 −x（世界 +X = 角色左侧）。
    off.x += (1.0 if side == "L" else -1.0) * hand_spread(frame)
    return shoulder + off


def elbow_dir(side, frame):
    """肘的鼓出偏好（世界向量）。撑地期**肘往外上方张**（仰卧撑的肘窝朝外）。"""
    return _dir_keys_at(ELBOW_KEYS[side], frame, SEAM_ELBOW_DIR[side])


def hand_dir_of(side, frame):
    """手骨世界朝向：接缝值 → `Idle_01@0` 值。同样走**球面**求值。"""
    return _dir_keys_at(HAND_DIR_KEYS[side], frame, SEAM_HAND_DIR[side])


# =============================================================== 踝目标
ANKLE_LIFT_MIX = _env_f("D18_ANKLE_LIFT", 1.0)
ANKLE_CLEAR_MIX = _env_f("D18_ANKLE_CLEAR_MIX", 1.0)
TUCK_ANKLE_DY = _env_f("D18_TUCK_ANKLE_DY", 0.150)
TUCK_ANKLE_Z = _env_f("D18_TUCK_ANKLE_Z", 0.210)
ANKLE_LIFT_KEYS = {
    "L": ((0, 0.0), (LEGS_DOWN, 0.0), (PLANT, 0.015), (CHEST_UP, 0.045),
          (HAND_OFF, 0.105), (TUCK, 0.185), (FOOT_SET, 0.0), (END, 0.0)),
    "R": ((0, 0.0), (LEGS_DOWN, 0.0), (PLANT, 0.016), (CHEST_UP, 0.048),
          (HAND_OFF, 0.110), (TUCK, 0.190), (FOOT_SET, 0.0), (END, 0.0)),
}

ANKLE_CLEAR_M = _env_f("D18_ANKLE_CLEAR", 0.050)
ANKLE_CLEAR_KEYS = _parse_fv(os.environ.get("D18_ANKLE_CLEAR_KEYS", "").strip()) or (
    (0, 0.0), (TUCK, 0.0), (FOOT_SET - 3, 0.20),
    (FOOT_SET - 2, 0.62), (FOOT_SET - 1, 0.86),
    (FOOT_SET, 0.0), (END, 0.0))

# =============================================================== ★ 落腿段（D18 独有）
#   ★★ `[START=0, LEGS_DOWN=4]`：**腿从半空落到地面**。仰卧接缝里双腿是**折着的**
#      （膝屈角 124.96°：髋 → 膝几乎贴地、踝被抬到 z 300 mm），必须**真的把膝放开**，
#      否则 `knee_unfold_start_ok` 必红（实测原稿只动 −2.2°，即根本没落腿）。
#   ★★ 落点由**膝几何**反解，不是拍的：绕"膝的屈伸轴"（= 大腿 × 小腿 的叉积，
#      实测 ≈ (−0.556, 0.036, 0.830)）把踝绕膝转 **−65°** ⟹ 膝屈角
#      124.96° → **≈60°**（放开 ≈65°）。三点实测锚：`(330, 231, 300)`（起点）
#      → `(247, −211, 273)`（落腿）。
#      ① 只放开 ~65° 而不是全直：全直会让踝飞到 `y = −333`（跑到身体前面），
#         视觉上像"踢腿"而不像"落腿"；
#      ② z 仍留 **273 mm** ⟹ 鞋底远离地面（实测 ≈ 205 mm），
#         **不会**提前触发 `foot_takeover_ok`（该判据只看 `[TUCK, FOOT_SET]`）。
LEGDOWN_X_F = _env_f("D18_LEGDOWN_XF", 0.749)
LEGDOWN_DY = _env_f("D18_LEGDOWN_DY", -0.442)
LEGDOWN_Z = _env_f("D18_LEGDOWN_Z", 0.273)


def legdown_ankle(side):
    """落腿段的踝世界目标（★ 反验证 ⑧ `NO_LEGDROP` 时退回接缝值 ⟹ 膝不放开）。"""
    if NO_LEGDROP:
        return Vector(SEAM_ANKLE[side])
    a = SEAM_ANKLE[side]
    return Vector((a.x * LEGDOWN_X_F, a.y + LEGDOWN_DY, LEGDOWN_Z))


def ankle_target(arm, side, frame):
    """踝世界目标：接缝（仰卧）→ 腿落平 → 抬起收腿 → `FOOT_SET` 起**抬跟后的 Idle 落脚点**。

    ★★ `f ≥ FOOT_SET` 目标**恒定**（= `END_ANKLE` 绕**脚尖关节**转一个固定的抬跟角），
      与帧号无关 ⟹ 脚**构造性不滑**（`no_foot_slide_ok`）：脚尖关节是旋转不动点，
      而 `toe.*` 骨端正是滑移尺子的探针（见 `_heel_ankle`）。
    ★★ 仰卧族的**独有分段**：`[START, LEGS_DOWN]` 是"**腿从半空落到地面**" ——
      踝的世界 z 必须**真的下降**（接缝 z ≈ 300 mm → 落地 z ≈ 一个贴地值），
      这正是 `knee_unfold_start_ok` 要量的事。
    """
    end = Vector(END_ANKLE[side])
    if NO_TUCK:
        # ★ 反验证 ③：抽掉收腿 —— 踝从接缝一路直线飞到终点（不是"收腿"，是"瞬移"）
        if frame <= 0:
            return Vector(SEAM_ANKLE[side])
        t = _smoothstep(float(frame) / float(FOOT_SET))
        return Vector(SEAM_ANKLE[side]) * (1.0 - t) + end * t
    if frame >= FOOT_SET:
        return _heel_ankle(side, frame)
    if frame <= 0:
        return Vector(SEAM_ANKLE[side])
    if frame <= LEGS_DOWN:
        # ★★ D18 独有：落腿段（膝放开）—— 不是"原地不动"，是踝**真的走出去**。
        t = _seg(float(frame) / float(max(1, LEGS_DOWN)), _ANKLE_LIN_LVL >= 2)
        base = Vector(SEAM_ANKLE[side]) * (1.0 - t) + legdown_ankle(side) * t
    elif frame <= TUCK_LEG:
        t = _seg((float(frame) - float(LEGS_DOWN))
                 / float(max(1, TUCK_LEG - LEGS_DOWN)), _ANKLE_LIN_LVL >= 2)
        base = legdown_ankle(side) * (1.0 - t) + Vector(TUCK_ANKLE[side]) * t
    else:
        t = _seg((float(frame) - TUCK_LEG) / float(FOOT_SET - TUCK_LEG),
                 _ANKLE_LIN_LVL >= 1)
        base = Vector(TUCK_ANKLE[side]) * (1.0 - t) + end * t
    base = base.copy()
    # ★ 单位口径：本文件全部**世界目标**用米（`bone_world` 原生口径）。
    base.z += ANKLE_LIFT_MIX * UE.pwl(ANKLE_LIFT_KEYS[side], float(frame), 0.0)
    base.z += ANKLE_CLEAR_MIX * ANKLE_CLEAR_M * UE.pwl(ANKLE_CLEAR_KEYS,
                                                       float(frame), 0.0)
    return base


# =============================================================== ★ 抬跟（鞋底贴地）
FOOT_PIN_BLEND = _env_i("D18_FOOT_PIN_BLEND", 8)
#   ★★ 实测修正（D18 首次门禁）：取 D17 的 **2.60°** 时，`f = FOOT_SET = 25` 的鞋底
#      被压到 **−3.26 mm**（`sole_ground_ok` 要求 `[−2, +6]`）⟹ 红。
#      逐帧实测灵敏度 **≈ +3.4 mm/°**（2.60° → −3.26；3.40° → **−0.54**）
#      ⟹ 峰值取 **3.40°**：`f=25` 实测 **−0.54 / +0.14 mm**、`f=34..36` = −0.96 / +1.06
#      （= `Idle_01@0` 原值），全段落在 `[−2, +6]` 带内、两侧都有余量。
#      ★ 为什么本支比 D17 需要更大抬跟：脚骨在 `f ≥ FOOT_SET` 已被 `_pin_foot_world`
#        钉成 `Idle_01@0` 鞋底（−0.96 mm，贴地），抬跟专门用来抵消"落地那一下"
#        的相对下沉；D17 是俯卧族、脚背朝下，需要的量不同。
HEEL_LIFT_PEAK_DEG = _env_f("D18_HEEL_PEAK", 3.40)
HEEL_LIFT_KEYS = ((0, 0.0), (TUCK, 0.0), (FOOT_SET - 2, 0.30),
                  (FOOT_SET, 1.0), (RISE_MID, 0.42), (STAND, 0.0), (END, 0.0))


def heel_lift_deg(frame):
    return HEEL_LIFT_PEAK_DEG * UE.pwl(HEEL_LIFT_KEYS, float(frame), 0.0)


def _heel_rot(side, frame):
    """抬跟旋转（世界 X 轴，+ 角 = 脚跟抬起）。零角返回 `None`（省一次矩阵乘）。"""
    theta = math.radians(heel_lift_deg(frame))
    if abs(theta) < 1e-9:
        return None
    return Matrix.Rotation(theta, 3, "X")


def _heel_ankle(side, frame):
    """抬跟后的踝世界目标 = 脚尖关节 + R·(`END_ANKLE` − 脚尖关节)。"""
    end = Vector(END_ANKLE[side])
    rot = _heel_rot(side, frame)
    if rot is None:
        return end
    pivot = Vector(END_TOE[side])
    return pivot + rot @ (end - pivot)


def _pin_foot_world(arm, name, side, frame):
    """把脚骨的世界 3×3 钉成 **`Idle_01@0` 的脚朝向 × 抬跟旋转**（只动旋转，不动位置）。"""
    pose_bone = arm.pose.bones[name]
    current = pose_bone.matrix.copy()
    basis = END_FOOT_BASIS[name].copy()
    rot = _heel_rot(side, frame)
    if rot is not None:
        basis = rot @ basis
    target = basis.to_4x4()
    target.translation = current.translation
    pose_bone.matrix = target
    bpy.context.view_layer.update()
    return tuple(math.degrees(v) for v in pose_bone.rotation_euler)


def _foot_euler(arm, side, frame):
    """脚：`f < FOOT_SET` 走 pwl（仰卧勾脚 → 落地前压脚背）；`f ≥ FOOT_SET` 钉世界朝向。

    ★★ `f ≥ FOOT_SET` 起**整段**把脚的世界 3×3 钉成 **`Idle_01@0` 的脚朝向**
      ⟹ ①鞋底构造性 = `Idle_01@0` 的鞋底；②`toe.*` 相对 `foot.head` 位置恒定 ⟹
      脚不滑是构造性的，不是靠容差；③`f = STAND` 走 `_end_pose_continuous`（逐位 = Idle），
      与这里的钉法同源 ⟹ 末帧不再有欧拉支跳变。
    """
    name = "foot." + side
    prev = JS._PREV_EULER.get(name)
    if frame >= FOOT_SET:
        return JS._unwrap_xyz(prev, _pin_foot_world(arm, name, side, frame))
    pw = pwl_vec(FOOT_KEYS[side], float(frame), SEAM_FOOT_EULER[side])
    if FOOT_PIN_BLEND > 0 and frame > FOOT_SET - FOOT_PIN_BLEND:
        _pb = arm.pose.bones[name]
        _saved = tuple(_pb.rotation_euler)
        _pin = _pin_foot_world(arm, name, side, frame)
        _pb.rotation_euler = _saved
        bpy.context.view_layer.update()
        _w = _smoothstep((float(frame) - float(FOOT_SET - FOOT_PIN_BLEND))
                         / float(FOOT_PIN_BLEND))
        pw = tuple(a + (b - a) * _w for a, b in zip(pw, _pin))
    return JS._unwrap_xyz(prev, tuple(pw))


# =============================================================== 模块级表
ZERO = {}
ZERO_WORLD = {}
END_POSE = {}
ZERO_BASIS = {}
ZERO_DIR = {}
END_BASIS = {}
END_DIR = {}
END_KNEE_DIR = {}
END_ELBOW_DIR = {}
END_HAND_DIR = {}
SEAM_FIST = {}
SEAM_ELBOW_DIR = {}
SEAM_HAND_DIR = {}
SEAM_ANKLE = {}
SEAM_FOOT_EULER = {}
END_FOOT_BASIS = {}
SEAM_RX = {}
END_RX = {}
END_OFF = {}
END_ANKLE = {}
END_TOE = {}
PLANT_KEYS = {}
ELBOW_KEYS = {}
HAND_DIR_KEYS = {}
FOOT_KEYS = {}
TUCK_ANKLE = {}
KNEE_DIR = {}
ARM_MAX = {}
LOCK_POSE = {}
_LOCK_REUSED = [0]
SEAM_MATCH = {"src": None, "geom_pos": None, "geom_dir": None,
              "pos_bone": None, "dir_bone": None, "per_bone": {},
              "matched": False}
END_MATCH = {}
HEM_STATIC = {}
ROLL_WEIGHT_MODE = os.environ.get("D18_ROLL_WEIGHT", "always").strip().lower()
ROLL_BONES = tuple(
    item for item in os.environ.get(
        "D18_ROLL_BONES",
        "upperarm.L,forearm.L,hand.L,upperarm.R,forearm.R,hand.R").split()
    if item)
ROLL_ITER = max(1, _env_i("D18_ROLL_ITER", 2))
ROLL_LEGS = os.environ.get("D18_ROLL_LEGS", "1").strip() not in ("", "0", "false")
if ROLL_LEGS:
    UE.ROLL_BONES = frozenset(set(UE.ROLL_BONES)
                              | {"thigh.L", "thigh.R", "shin.L", "shin.R"})

MIX_SKIP = tuple(item for item in os.environ.get(
    "D18_MIX_SKIP",
    "thigh.L shin.L thigh.R shin.R foot.L foot.R").split() if item)

TORSO_BONES = ("root", "pelvis", "spine_01", "spine_02", "chest", "neck", "head")
PARENT_OF = {"root": None, "pelvis": "root", "spine_01": "pelvis",
             "spine_02": "spine_01", "chest": "spine_02", "neck": "chest",
             "head": "neck"}
ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")
LEG_BONES = ("thigh.L", "shin.L", "thigh.R", "shin.R")
UPPER_BONES = TORSO_BONES + ("shoulder.L", "shoulder.R") + ARM_BONES


# =============================================================== 阈值
SEAM_TOL = 1e-6
END_TOL = 1e-6
NO_TELEPORT_MAX_DEG = 25.0
REACH_MAX_RATIO = 0.995
# ---- ★ 起身幅度 --------------------------------------------------------------
#   ★ 清单计划写「净升 ≥ 650 mm」基于**推算**；实测起点 128.0 / 终点 830.0
#     ⟹ 真实净升 **702.0 mm**，阈值按**实测的 95%** 重定为 **667 mm**。
#     **这不是放宽容差，是把推算换成实测。**
RISE_MIN_MM = _env_f("D18_RISE_MIN", 667.0)
RISE_MONO_TOL_MM = _env_f("D18_RISE_MONO", 2.0)
# ---- ★ 撑地推起 --------------------------------------------------------------
CHEST_RISE_MIN_MM = _env_f("D18_CHEST_RISE_MIN", 200.0)
# ---- ★ 支点交接 --------------------------------------------------------------
HAND_TOUCH_MAX_MM = _env_f("D18_HAND_TOUCH_MAX", 60.0)
HAND_OFF_MIN_MM = _env_f("D18_HAND_OFF_MIN", 60.0)
#   ★ 手最初在地下（实测 `Hand_Palm_L` = −72.06 mm）：`[START, LEGS_DOWN]` 必须
#     实测到 **< HAND_PLANT_BELOW_MM**（"手先出来"的起点事实）。
HAND_PLANT_BELOW_MM = _env_f("D18_HAND_PLANT_BELOW", -2.0)
SOLETOUCH_MAX_MM = _env_f("D18_FOOT_TOUCH_MAX", 6.0)
# ---- ★ 落腿段膝必须真的放开 --------------------------------------------------
KNEE_UNFOLD_MIN_DEG = _env_f("D18_KNEE_UNFOLD_MIN", 30.0)
# ---- ★ 站姿族硬约束（清单 §6）-----------------------------------------------
FOOT_SLIDE_MAX_MM = _env_f("D18_FOOT_SLIDE_MAX", 3.0)
SOLE_MIN_MM = _env_f("D18_SOLE_MIN", -2.0)
SOLE_MAX_MM = _env_f("D18_SOLE_MAX", 6.0)
# ---- 收招不许瞬停 ------------------------------------------------------------
NO_SNAP_TAIL_FRAMES = _env_f("D18_SNAP_TAIL", 6.0)
END_HOLD_MAX_DEG = _env_f("D18_END_HOLD_TOL", 0.5)
# ---- 穿模 / 可达性 -----------------------------------------------------------
CLIP_MAX_MM = _env_f("D18_CLIP_MAX", 0.0)
CLIP_EVERY = _env_i("D18_CLIP_EVERY", 4)
SEAM_REPLAY_POS_MAX_MM = _env_f("D18_SEAM_POS", 0.01)
SEAM_REPLAY_DIR_MAX_DEG = _env_f("D18_SEAM_DIR", 0.05)

HEM_OBJECTS = tuple(
    n for n in os.environ.get("D18_HEM_OBJECTS",
                              "Jacket_Hem,Jacket_Hem_Line").split(",") if n)
HAND_MESHES = {s: tuple(["Hand_Palm_" + s] + ["Finger_%s_%s" % (d, s)
                                              for d in ("Index", "Middle",
                                                        "Ring", "Pinky")])
               for s in SIDES}


def pwl_vec(keys, frame, default):
    """逐分量 PCHIP（`UE.pwl`）。keys: ((f, (x, y, z)), ...)。"""
    out = []
    for index in range(3):
        sub = tuple((k[0], k[1][index]) for k in keys)
        out.append(UE.pwl(sub, float(frame), default[index]))
    return Vector(out)


# =============================================================== 姿态装配
def arm_seat_tip(arm, pose, side, tip_target, elbow_dir_in, hand_dir_in):
    up, fo, hd = ("upperarm." + side, "forearm." + side, "hand." + side)
    dims = UE.ARM_LEN[side]
    l1, l2 = dims["upper"], dims["forearm"]
    hand_dir = Vector(hand_dir_in).normalized()
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
    if _ARMPROBE and _ARMPROBE_F0 <= _ARMPROBE_FRAME[0] <= _ARMPROBE_F1:
        _bul = Vector(elbow_dir_in)
        _perp = _bul - axis * _bul.dot(axis)
        print("D18_ARMPROBE " + json.dumps({
            "f": _ARMPROBE_FRAME[0], "side": side,
            "axis": [round(v, 4) for v in axis],
            "edir": [round(v, 4) for v in _bul.normalized()],
            "perp_len": round(_perp.length, 4),
            "cos_axis_edir": round(axis.dot(_bul.normalized()), 4),
            "dist_mm": round(delta.length * 1000.0, 2),
            "limit_mm": round(limit * 1000.0, 2),
            "clamp": bool(clamp), "sin_sh": round(sin_sh, 4),
            "elbow_z": round((elbow.z) * 1000.0, 2),
            "shoulder_z": round(shoulder.z * 1000.0, 2),
        }))
    for name, direction in ((up, elbow - shoulder),
                            (fo, wrist_target - elbow),
                            (hd, hand_dir)):
        pose[name] = UE.aim_nearest(arm, name, direction,
                                    UE.IDLE_BASIS[name], UE.IDLE_DIR[name])
    return clamp, delta.length * 1000.0, limit * 1000.0


def _copy_pose(source):
    return {k: (tuple(v) if not k.startswith("@")
                else {kk: tuple(vv) for kk, vv in v.items()})
            for k, v in source.items()}


def _toward_end(pose, weight):
    """把 `pose` 朝 `END_POSE` 拉 `weight`（逐骨取最近 360° 等价表示再插值）。"""
    if weight <= 0.0:
        return pose
    out = {}
    #   ★★ `sorted`：`set` 迭代顺序随 `PYTHONHASHSEED` 变 ⟹ `out` 的插入顺序变。
    #     见 `_load_pose_at` 的注释（确定性是门禁可复现的前提）。
    keys = sorted(set(pose) | set(END_POSE))
    for key in keys:
        if key == "@loc":
            continue
        if key in MIX_SKIP:
            out[key] = pose.get(key, (0.0, 0.0, 0.0))
            continue
        a = pose.get(key, (0.0, 0.0, 0.0))
        b = END_POSE.get(key, (0.0, 0.0, 0.0))
        bb = [_nearest_equiv(y, x) for x, y in zip(a, b)]
        out[key] = tuple(u + (v - u) * weight for u, v in zip(a, bb))
    out["@loc"] = {k: tuple(v) for k, v in pose.get("@loc", {}).items()}
    return out


TORSO_PROG_END = _env_i("D18_TORSO_END", STAND)


def torso_pose(frame):
    """躯干：局部欧拉 pwl（接缝 → Idle），另叠"拱起"曲线。"""
    out = {}
    for name in TORSO_BONES:
        p = UE.pwl(TORSO_PROG[name], float(frame), 0.0)
        rx = SEAM_RX[name] + (END_RX[name] - SEAM_RX[name]) * p
        rx -= arch_of(name, frame)
        ry = ZERO.get(name, (0.0, 0.0, 0.0))[1] * (1.0 - p)
        rz = ZERO.get(name, (0.0, 0.0, 0.0))[2] * (1.0 - p)
        out[name] = (rx, ry, rz)
    for side in SIDES:
        name = "shoulder." + side
        p = UE.pwl(TORSO_PROG["chest"], float(frame), 0.0)
        a = ZERO.get(name, (0.0, 0.0, 0.0))
        b = END_POSE.get(name, a)
        out[name] = tuple(a[i] + (b[i] - a[i]) * p for i in range(3))
    locs = {k: tuple(v) for k, v in ZERO.get("@loc", {}).items()}
    locs["pelvis"] = A.wloc(0.0, pelvis_y_at(frame),
                            pelvis_z_at(frame) - Z_PELVIS_REST)
    out["@loc"] = locs
    return out


def _end_pose_continuous(arm):
    """末帧：**世界姿态逐位 = `END_POSE`**，但欧拉取**离上一帧最近**的那一支。

    ★ `END_POSE` 的欧拉与 `f = STAND−1` 的 IK 解可能落在不同的**万向节等价解**上
      （差 116.6°，不是 360° 的整数倍）⟹ `no_teleport` 会红。`_nearest_equiv` 只修 ±360°。
      ★ 做法：把 `END_POSE` 应用到骨架，逐骨调 `UE._set_euler_nearest`（C13 正解函数）
      读回**等价且连续**的欧拉。`phi` 只取 0 ⟹ **只换欧拉支、不绕骨轴滚转** ⟹ 世界 3×3
      逐位不变 ⟹ `end_matches_idle_ok`（4×4 矩阵 ≤1e−6）不受影响。
    """
    A.apply_pose(arm, END_POSE)
    bpy.context.view_layer.update()
    grid = UE.ROLL_GRID
    UE.ROLL_GRID = (0.0,)
    try:
        out = {}
        for name in END_POSE:
            if name.startswith("@"):
                continue
            if name in arm.pose.bones:
                out[name] = UE._set_euler_nearest(arm, name)
            else:
                out[name] = tuple(END_POSE[name])
    finally:
        UE.ROLL_GRID = grid
    out["@loc"] = {k: tuple(v) for k, v in END_POSE.get("@loc", {}).items()}
    return out


def _roll_grid_window(mix):
    """绕骨轴滚转的**允许窗口**：`|φ| ≤ 180° · (1 − mix^p)`（按**绕圈等价角**判距）。

    ★★★ 修的是一个**实测踩到**的坑，而且是**同一根因的第二处**（第一处见 `_legroll_window`）：

      `UE.ROLL_GRID` 只有 **`[0°, 360°)` 的正角** ⟹ "滚 −65°" 在表里存成 **295°**。
      原来写 `abs(phi) <= half`，`mix = 0` 时 `half = 180°` ⟹ 只留下 `[0°, 180°]`，
      **整半圈（−180° ~ 0°）被静默剔掉**。

      实测后果（`D18_EULERDBG` + 离线 DP 复核）：`forearm.L` 的逃锁滚转需要
      **−65° ~ −85°**（= 295° ~ 275°），全部落在被剔掉的半圈里 ⟹ `_euler_roll_best`
      只剩 `φ = 0` 可选（实测 `_ROLL_LAST_PHI` 全段恒为 `0.0`）⟹ 欧拉路径被迫穿过
      `|ry| ≈ 90°` 的 **XYZ 万向节锁**（f2 `ry = −81.99°` → f3 `ry = −19.52°`）
      ⟹ `no_teleport` 红 **64.27°/帧 @ [3, 'forearm.L']**，而同一帧的真实世界旋转只
      由"方向 15.1° + 绕轴滚转"构成 —— 也就是说**红的是表示，不是几何**。

      离线 DP（同一代价 `纯最小步长`，只把窗口从 `[0,180]` 换成整圈）复核：
      `forearm.L` 的最优滚转轨迹为 `φ = 0, 0, 355, 290, 275, 275, ...`，
      全段最大欧拉步长 **64.27° → 22.64°**（< 25 阈值）。
      ⟹ **只改这一个判距口径，不放宽任何容差。**
    """
    p = _env_f("D18_ROLLWIN_POW", 3.0)
    half = math.radians(180.0 * max(0.0, min(1.0, 1.0 - mix ** max(1e-6, p))))
    out = tuple(phi for phi in UE.ROLL_GRID
                if abs((phi + math.pi) % (2.0 * math.pi) - math.pi) <= half + 1e-9)
    return out if out else (0.0,)


def _euler_roll_best(arm, name, prev=None, roll_penalty=0.0):
    """在**当前局部旋转**上再搜一圈绕骨轴滚转，取"步长 + 罚分·|φ|"最小的欧拉支。

    ★★ `D18_ARMYWEIGHT`（臂骨专用"逃离万向节锁"罚分，**默认 0 = 与旧行为逐位一致**）：
      罚分口径 `max(0, |ry| − D18_ARMYSAFE) · D18_ARMYWEIGHT`。
      为什么需要它：`_set_euler_nearest` 的锁罚分走 `UE.EULER_Y_WEIGHT`，而 `boot()`
      把它设成 **0**（腿骨需要它关着）⟹ `_euler_roll_best` 的锁罚分**恒定失效**
      （实测：`forearm.R` f10~f28 的 `φ` **全为 0**）⟹ 滚转自由度**从未被用来逃锁**，
      臂骨只能硬穿 `|ry|≈90°`。这里给臂骨一条**独立**的锁罚分通道：
      它在 φ 的搜索里把"欧拉 y 近 90°"的支排开 ⟹ 用**纯表示自由度**（绕骨轴滚转，
      骨根/骨尖逐位不动）把欧拉路径挪出锁带。
    """
    pose_bone = arm.pose.bones[name]
    basis = pose_bone.matrix_basis.to_3x3()
    if prev is None:
        prev = JS._PREV_EULER.get(name)
    best, best_cost = None, None
    best_phi = 0.0
    for phi in UE.ROLL_GRID:
        if phi == 0.0:
            m = basis
        else:
            cos_p, sin_p = math.cos(phi), math.sin(phi)
            m = basis @ Matrix(((cos_p, 0.0, sin_p),
                                (0.0, 1.0, 0.0),
                                (-sin_p, 0.0, cos_p)))
        for cand in UE._xyz_candidates(m):
            value = [math.degrees(t) for t in cand]
            if prev is not None:
                for index in range(3):
                    while value[index] - prev[index] > 180.0:
                        value[index] -= 360.0
                    while value[index] - prev[index] < -180.0:
                        value[index] += 360.0
            cost = (0.0 if prev is None
                    else max(abs(a - b) for a, b in zip(value, prev)))
            cost += roll_penalty * abs(math.degrees(phi))
            cost += (max(0.0, abs(value[1]) - ARM_Y_SAFE) * ARM_Y_WEIGHT)
            cost += ARM_Y_SOFT * math.exp(
                -((abs(value[1]) - ARM_Y_MID) / max(1e-6, ARM_Y_SIGMA)) ** 2)
            if best_cost is None or cost < best_cost:
                best, best_cost, best_phi = tuple(value), cost, math.degrees(phi)
    _ROLL_LAST_PHI[name] = round(best_phi, 3)
    pose_bone.rotation_euler = [math.radians(t) for t in best]
    bpy.context.view_layer.update()
    return best


# ★★ 小腿绕轴滚转的**幅度窗口**（`shin.*` 专用）。
#    为什么必须有窗口而不能全开：`_set_euler_nearest` 的代价里带"远离锁"罚分
#    `(|ry|−70)·1.5`，全开时会为了压 `|ry|` 把小腿滚到 −45°~−83°（实测），
#    **小腿网格被扭了 60°+**（视觉错），并且 f33（滚了）→ f34（`_end_pose_continuous`
#    用 `ROLL_GRID=(0,)`）之间断 **118.5°** ⟹ `no_snap_stop_ok` + `sole_ground_ok` 双红。
#    ⟹ 改成**帐篷窗口**：两端收到 0°（与首帧接缝、尾帧 `Idle_01@0` 逐位一致），
#    中间只允许 `≤ D18_LEGROLL_MAX` 度，够把欧拉路径挪出锁带、又不扭网格。
LEGROLL_MAX_DEG = _env_f("D18_LEGROLL_MAX", 40.0)
#   ★★ 起坡长度（帧）：窗口从 `f = 0` 的 0° 快速升到 `f >= LEGROLL_RAMP` 的满额。
#   为什么不能再从 `LEGS_DOWN` 才开始（原 `LEGROLL_LO = LEGS_DOWN`）：那只在
#   `f >= 4` 开门，而**腿落下段 `f ∈ [1, 4]` 恰恰是小腿最需要逃锁的地方** ——
#   接缝 `Knockdown_B@20` 里 `shin.R` 的局部欧拉 y = **−94.43°**（已越过 90° 锁带），
#   `f = 1` 就落在 `y = −95.26°`。窗口关着 ⟹ `_set_euler_nearest` 只能在小腿**两支
#   都在锁内**的欧拉里选 ⟹ 实测 `f = 1` 步长 **31.61°**（真实局部旋转只 **10.65°**，
#   放大 **2.97×**）、`f = 2` **38.44°**（真实 **18.11°**，放大 **2.12×**）⟹ 假红。
#   窗口在 `f = 0` 仍为 0（接缝**逐位**不受影响 —— `build_pose` 对 `f <= 0` 直接
#   返回接缝姿态，根本不走这条路），之后快速起坡即可把这段挪出锁带。
LEGROLL_RAMP = _env_i("D18_LEGROLL_RAMP", 3)
LEGROLL_LO = _env_i("D18_LEGROLL_LO", LEGS_DOWN)      # 仅保留兼容：不再作排他用
LEGROLL_MID = _env_i("D18_LEGROLL_MID", HAND_OFF)
LEGROLL_HI = _env_i("D18_LEGROLL_HI", FOOT_SET)


def _legroll_window(frame, source=None):
    """`shin.*` 允许的绕轴滚转集合（弧度）；窗口外退化为 `(0.0,)`。

    ★ `source` 必须是**入口保存的完整栅格**（`build_pose` 里的 `grid`），不能读
      `UE.ROLL_GRID` —— 调用点前面刚把它设成 `(0.0,)`（给 `thigh` 用），
      读它等于筛空集（实测：窗口内 `len(grid)==1`，白忙一场）。

    ★ 另一个坑：`UE.ROLL_GRID` 只有 **`[0°, 360°)` 的正角**，所以"滚 −30°"必须以
      **330°** 入表 ⟹ 必须按**绕圈等价角**判距离 `|wrap(phi)| <= cap`，
      直接筛 `abs(phi) <= cap` 会把 330° 全剔掉。

    ★ 形状：`f = 0` 为 0 → `[1, LEGROLL_RAMP]` 快速起坡到满额 → 保持到
      `LEGROLL_MID` → 帐篷收敛到 `LEGROLL_HI` 的 0（`FOOT_SET` 换支点时必须回零）。
    """
    if frame <= 0 or frame >= LEGROLL_HI:
        return (0.0,)
    if frame <= LEGROLL_MID:
        w = _smoothstep(min(1.0, float(frame) / float(max(1, LEGROLL_RAMP))))
    else:
        w = _smoothstep(float(LEGROLL_HI - frame)
                        / float(max(1, LEGROLL_HI - LEGROLL_MID)))
    cap = math.radians(LEGROLL_MAX_DEG) * w
    src = UE.ROLL_GRID if source is None else source
    out = tuple(p for p in src if abs(_wrap_pi(p)) <= cap + 1e-9)
    return out if out else (0.0,)


def _wrap_pi(angle):
    """把弧度角折到 `(−π, π]`。"""
    return (angle + math.pi) % (2.0 * math.pi) - math.pi


def build_pose(arm, frame):
    # ★ f0 = **逐位**接缝姿态（`Knockdown_B@20`）—— 不走解算，原样返回。
    if frame <= 0:
        if SEAM_ZERO:
            # ★ 反验证 ①：抽掉接缝 —— 首帧改成**零位** ⟹ `seam_in_ok` 必须红。
            _z = {name: (0.0, 0.0, 0.0) for name in ZERO
                  if not name.startswith("@")}
            _z["@loc"] = {"pelvis": A.wloc(0.0, 0.0, 0.0)}
            return _z
        return _copy_pose(ZERO)

    # ★★ 末段：`STAND` 起**逐位** = `Idle_01@0`（3 帧定格自持）。
    if frame >= STAND and not NO_IDLE and not END_ZERO:
        return _end_pose_continuous(arm)

    pose = torso_pose(frame)

    # ★★ 顺序是关键：**先在躯干欧拉上做末端收束，再解 IK**（D17 教训：反之踝会漂）。
    if not NO_IDLE:
        w = _smoothstep((float(frame) - float(FOOT_SET))
                        / float(STAND - FOOT_SET))
        pose = _toward_end(pose, w)

    A.apply_pose(arm, pose)
    for side in SIDES:
        UE.leg_seat(arm, pose, side, ankle_target(arm, side, frame),
                    knee_dir_at(side, frame))
    for name in ("foot.L", "foot.R"):
        pose[name] = _foot_euler(arm, name.split(".")[1], frame)
    for side in SIDES:
        arm_seat_tip(arm, pose, side, fist_target(arm, side, frame),
                     elbow_dir(side, frame), hand_dir_of(side, frame))
    if ROLL_WEIGHT_MODE != "off":
        if HEAD_FREEZE and frame <= HEAD_FREEZE:
            UE.ROLL_GRID = (0.0,)
        _scope = roll_scope(frame)
        for _ in range(ROLL_ITER):
            for name in ROLL_BONES:
                if name in arm.pose.bones:
                    _roll_return(arm, pose, name, _scope,
                                 roll_mix_at(frame, name))
            # ★★ 脚朝向必须在**腿的滚转之后**重钉（见 D17 `_foot_euler` 注释）。
            for name in ("foot.L", "foot.R"):
                pose[name] = _foot_euler(arm, name.split(".")[1], frame)
            for side in SIDES:
                arm_seat_tip(arm, pose, side, fist_target(arm, side, frame),
                             elbow_dir(side, frame), hand_dir_of(side, frame))
        if ARM_ROLL_TAIL:
            grid_arm = UE.ROLL_GRID
            _mix = roll_mix_at(frame, None)
            _pen = ARM_ROLL_PENALTY_DEG * _mix * _mix
            UE.ROLL_GRID = _roll_grid_window(_mix)
            try:
                for name in ARM_BONES:          # 父先子后
                    if name in arm.pose.bones:
                        _roll_return(arm, pose, name, _scope,
                                     roll_mix_at(frame, name))
                for side in SIDES:
                    arm_seat_tip(arm, pose, side, fist_target(arm, side, frame),
                                 elbow_dir(side, frame), hand_dir_of(side, frame))
                for name in ARM_BONES:
                    if name in arm.pose.bones:
                        pose[name] = _euler_roll_best(arm, name,
                                                      roll_penalty=_pen)
            finally:
                UE.ROLL_GRID = grid_arm

    # ★★ 腿骨滚转收尾：只滚 `shin` 之外的父骨要重解子骨（见 D17 注释）。
    if LEG_ROLL_TAIL and ROLL_WEIGHT_MODE != "off":
        grid_leg = UE.ROLL_GRID
        UE.ROLL_GRID = (0.0,)
        saved_roll_bones = UE.ROLL_BONES
        try:
            UE.ROLL_BONES = frozenset(b for b in saved_roll_bones
                                      if b not in LEG_BONES)
            for name in ("thigh.L", "thigh.R"):
                if name in arm.pose.bones:
                    _roll_return(arm, pose, name, 1.0, roll_mix_at(frame, name))
            for side in SIDES:
                UE.leg_seat(arm, pose, side, ankle_target(arm, side, frame),
                            knee_dir_at(side, frame))
        finally:
            UE.ROLL_BONES = saved_roll_bones
        try:
            for name in ("shin.L", "shin.R"):
                if name in arm.pose.bones:
                    _roll_return(arm, pose, name, 1.0, roll_mix_at(frame, name))
        finally:
            UE.ROLL_GRID = grid_leg

    # ★★ 末段：腿骨重写欧拉支。**`thigh` 与 `shin` 必须分开处理**：
    #    · `thigh`：只换写法（`ROLL_GRID=(0,)`）。滚 `thigh` 会连**子骨 `shin`**
    #      一起绕大腿轴转 ⟹ **踝会真的漂** ⟹ IK、脚滑、鞋底全部失守。
    #    · `shin`：**允许绕自身轴滚**（`ROLL_GRID` 全开）。滚 `shin` 是绕它自己的
    #      骨轴，**骨根（膝）/骨尖（踝）逐位不动**，只有子骨 `foot` 的世界朝向被带转
    #      —— 而 `foot` 紧接着就被下面那句 `_foot_euler` **按世界朝向重钉** ⟹
    #      鞋底几何、`toe.*` 滑移尺子、脚朝向全部不受影响。
    #    ★ 为什么必须给 `shin` 开滚转（本支最后一次门禁的唯一剩红）：
    #      实测 `shin.R` 在 f13~f17 走进 `|ry| ≈ −90°` 的 **XYZ 万向节锁**
    #      （f13 欧拉 `(147.01, −95.39, −5.06)` → f14 `(217.08, −94.32, −65.57)`，
    #      逐分量跳 **70.06°/帧**），但同一帧的**世界朝向只转了 7.69°**
    #      ⟹ `no_teleport` 是**假红**（几何平滑、表示在跳）。
    #      不开滚转时 `_set_euler_nearest` 只剩"两支等价欧拉 + ±360"可选，
    #      两支都在锁里 ⟹ 70.06° 就是它能给出的小值。滚转是**唯一**能在
    #      "不改几何"的前提下换表示的余量。
    grid = UE.ROLL_GRID
    _spin_final = (os.environ.get("D18_LEGROLL_FINAL", "1").strip()
                   not in ("", "0", "false", "False"))
    _thigh_roll = (os.environ.get("D18_THIGH_ROLL", "1").strip()
                   not in ("", "0", "false", "False"))
    try:
        if _thigh_roll:
            # ★★★ 大腿也开滚转（**修正原注释的过度保守结论**）：
            #   滚转是绕 `thigh` **自身轴**做的 ⟹ `thigh` 的**骨根（髋）与骨尖（膝）
            #   逐位不动**，唯一被带走的是**子骨 `shin` 的世界朝向** ⟹ 踝会漂。
            #   但 `aim_nearest` 是**绝对世界口径**：它从 `CARRY_Q`（本帧 `leg_seat`
            #   刚写入的值）出发，只补"把骨轴摆到目标方向"的那一个最小旋转 ——
            #   `CARRY_Q` 里的 `shin` 朝向在本帧已经**指着踝目标**了 ⟹ 再调用一次
            #   得到的 `quaternion` 与原值**逐位相同**（`rotation_difference` = 单位）
            #   ⟹ **踝/鞋底/`toe.*` 全部逐位复原**，只有大腿与小/腿的**欧拉写法**变了。
            #   ⟹ 这是**纯表示自由度**（和 `shin` 的滚转同性质），不动任何几何。
            #   ★★ 注意 `_set_euler_nearest` 只对 `name in UE.ROLL_BONES` 才看栅格，
            #      而 `ROLL_BONES` 默认只有臂骨 ⟹ 必须**临时**把大腿并进去，
            #      否则栅格被静默忽略、退化成 `(0.0,)`（本条就是第一次实测踩到的坑）。
            UE.ROLL_GRID = _legroll_window(frame, grid)
            _saved_rb = UE.ROLL_BONES
            UE.ROLL_BONES = frozenset(_saved_rb | {"thigh.L", "thigh.R"})
            try:
                for name in ("thigh.L", "thigh.R"):
                    if name in arm.pose.bones:
                        pose[name] = UE._set_euler_nearest(arm, name)
            finally:
                UE.ROLL_BONES = _saved_rb
            for side in SIDES:
                _shin = "shin." + side
                if _shin in arm.pose.bones:
                    _knee = Vector(A.bone_world(arm, _shin, "head"))
                    _d = Vector(ankle_target(arm, side, frame)) - _knee
                    if _d.length > 1e-9:
                        pose[_shin] = UE.aim_nearest(
                            arm, _shin, _d, UE.IDLE_BASIS[_shin],
                            UE.IDLE_DIR[_shin])
        else:
            UE.ROLL_GRID = (0.0,)
            for name in ("thigh.L", "thigh.R"):
                if name in arm.pose.bones:
                    pose[name] = UE._set_euler_nearest(arm, name)
        if _spin_final:
            UE.ROLL_GRID = _legroll_window(frame, grid)
        else:
            UE.ROLL_GRID = (0.0,)
        for name in ("shin.L", "shin.R"):
            if name in arm.pose.bones:
                _before = tuple(math.degrees(v) for v in
                                arm.pose.bones[name].rotation_euler)
                _got = UE._set_euler_nearest(arm, name)
                if os.environ.get("D18_LEGROLLDBG"):
                    print("D18_LEGROLL " + json.dumps({
                        "f": frame, "bone": name, "grid": len(UE.ROLL_GRID),
                        "prev": [round(v, 2) for v in
                                 (JS._PREV_EULER.get(name) or ())],
                        "before": [round(v, 2) for v in _before],
                        "got": [round(v, 2) for v in _got]}))
                pose[name] = _got
    finally:
        UE.ROLL_GRID = grid

    # ★★ 脚必须排在**所有会改变腿世界朝向的步骤之后**。
    for name in ("foot.L", "foot.R"):
        pose[name] = _foot_euler(arm, name.split(".")[1], frame)

    # ===== ★★★ 臂链末段：**逐分量欧拉路径插值**（A12 定案）=======================
    #   ★★★ 时间重参数化必备（本支实测踩到）：原来写 `frame == ARM_MIX_FROM - 1`，
    #   是**整数帧相等**触发。路径保持重采样后 `frame` 是**浮点源帧**（如 20.62），
    #   `== 20` 永不成立 ⟹ 快照不落 ⟹ 臂链末段混合整段失效 ⟹ 实测欧拉步长从
    #   27.1° 暴涨到 **77.5°（44 帧）/ 129.6°（48 帧）**、`hand_off_ok` 转红。
    #   改成**单调阈值** `frame < ARM_MIX_FROM`：取"边界之前最后一个采样帧"的姿态。
    #   ★ 整数帧下逐位等价（0..20 每帧覆盖一次，最后一次恰是 f=20）。
    if ARM_MIX_FROM:
        if frame < ARM_MIX_FROM:
            TAIL_ARM["pose"] = {n: tuple(pose.get(n, (0.0, 0.0, 0.0)))
                                for n in ARM_BONES}
        elif frame >= ARM_MIX_FROM and TAIL_ARM.get("pose"):
            _src = TAIL_ARM["pose"]
            _u = (float(frame) - float(ARM_MIX_FROM)) / max(
                1e-9, float(STAND - ARM_MIX_FROM))
            _s = _hand_mix_s(_u)
            for name in ARM_BONES:
                a = _src.get(name, (0.0, 0.0, 0.0))
                b = END_POSE.get(name, a)
                bb = [_nearest_equiv(y, x) for x, y in zip(a, b)]
                pose[name] = tuple(u + (v - u) * _s for u, v in zip(a, bb))

    pose.update(A.FIST)

    for name, value in pose.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)
    if frame == END_ZERO_FRAME:
        LOCK_POSE.update(_copy_pose(pose))
    return pose


# ★★★ 滚转参考朝向的**连续搬运**开关（见 `_roll_return` 的长注释）。
#   默认开：`ref_zero` 从上一帧增量搬运，消除"骨轴近反平行时参考翻转"造成的假动作。
_ROLL_TRANSPORT = os.environ.get("D18_ROLL_TRANSPORT", "0").strip() not in (
    "", "0", "false", "False")
_ROLL_REF_CACHE = {}          # name -> (frame, dir_now, ref_zero)

_ROLLDBG_NAMES = tuple(n for n in os.environ.get("D18_ROLLDBG", "").split(",") if n)
_ROLLDBG_F = _env_i("D18_ROLLDBG_F", -1)
_ROLLDBG_F1 = _env_i("D18_ROLLDBG_F1", _env_i("D18_ROLLDBG_F", -1))
_ROLLDBG_FRAME = [-1]
_ROLL_LAST_PHI = {}
_ARMPROBE = bool(os.environ.get("D18_ARMPROBE"))
_ARMPROBE_F0 = _env_i("D18_ARMPROBE_F0", -1)
_ARMPROBE_F1 = _env_i("D18_ARMPROBE_F1", -1)
_ARMPROBE_FRAME = [-1]


def _roll_return(arm, pose, name, weight, roll_mix=0.0):
    """把某根骨的**绕自身轴滚转**沿世界朝向对齐回参考朝向（只改滚转，不改骨轴方向）。

    ★★ `roll_mix` 是**参考朝向的交接权重**（0 = 零位/仰卧，1 = `Idle_01@0`）：
      两端参考都先在"骨轴方向不变"的前提下转到**当前方向**，再做一次 slerp。
      因为两者的相对旋转是**纯滚转**（绕骨轴），slerp 全过程中骨轴方向**逐位不变**
      ⟹ 交接不移动任何骨端（踝/腕/拳都钉得住）。
    """
    pose_bone = arm.pose.bones[name]
    direction_now = Vector(A.bone_direction(arm, name))
    if direction_now.length < 1e-9:
        return
    direction_now.normalize()
    # ★★★ 参考朝向的**连续搬运**（`D18_ROLL_TRANSPORT=1`）。
    #
    #   原写法每帧从零构造 `ref_zero = rotation_difference(ZERO_DIR, dir) @ ZERO_BASIS`。
    #   `rotation_difference` 给的是**最短旋转**；当 `dir` 与 `ZERO_DIR` 接近**反平行**
    #   时，最短旋转的**轴不唯一**（测地线退化）⟹ 参考朝向在相邻帧**整个翻掉**
    #   （实测 `D18_ROLLDBG`：`forearm.R` 的 `ang_now_refzero` = f15 8.68° → f16 18.79°
    #   → f17 17.66° → **f18 83.76°** → f19 119.16°）。滚转修正随后在 2~3 帧里"追上"
    #   这个翻转 ⟹ 制造**假动作**（`hand.R` f17→f18 局部真旋转 33.97°，世界只转 8.05°
    #   —— 那 26° 全是补偿翻转参考的滚转，不是动作）。
    #
    #   ⟹ 正解不是调参，而是**把参考朝向也做成连续量**：从**上一帧**的参考出发，
    #      用"骨轴从上一帧方向转到本帧方向"的**增量旋转**搬运过来
    #      `ref_zero = incr(dir_prev → dir_now) @ ref_zero_prev`。
    #      增量是**小角度**（相邻帧），轴良态 ⟹ 参考朝向**逐帧连续**、不翻。
    #      语义不变：参考仍刚性附着在骨轴上（只搬运、不新造）。
    #   ★ 缓存按**帧号**去重：`_roll_return` 一帧内会被调用多次（`ROLL_ITER` 循环 +
    #     尾段块），必须保证一帧只推进一次搬运，否则会把增量重复累乘。
    if _ROLL_TRANSPORT:
        _c = _ROLL_REF_CACHE.get(name)
        _fnow = int(_ROLLDBG_FRAME[0])
        if _c is not None and _c[0] == _fnow:
            ref_zero = _c[2]
        elif _c is not None:
            _incr = _c[1].rotation_difference(direction_now)
            ref_zero = (_incr @ _c[2]).normalized()
            _ROLL_REF_CACHE[name] = (_fnow, direction_now.copy(), ref_zero)
        else:
            ref_zero = (ZERO_DIR[name].rotation_difference(direction_now)
                        @ Quaternion(ZERO_BASIS[name])).normalized()
            _ROLL_REF_CACHE[name] = (_fnow, direction_now.copy(), ref_zero)
    else:
        ref_zero = (ZERO_DIR[name].rotation_difference(direction_now)
                    @ Quaternion(ZERO_BASIS[name])).normalized()
    if weight <= 1e-9:
        return
    ref_end = (END_DIR[name].rotation_difference(direction_now)
               @ Quaternion(END_BASIS[name])).normalized()
    mix = max(0.0, min(1.0, roll_mix))
    if mix <= 0.0:
        reference = ref_zero
    elif mix >= 1.0:
        reference = ref_end
    else:
        reference = ref_zero.slerp(ref_end, mix).normalized()
    now = pose_bone.matrix.to_3x3().to_quaternion().normalized()
    if _ROLLDBG_NAMES and name in _ROLLDBG_NAMES \
            and _ROLLDBG_F <= _ROLLDBG_FRAME[0] <= _ROLLDBG_F1:
        print("D18_ROLL " + json.dumps({
            "frame": _ROLLDBG_FRAME[0], "bone": name,
            "weight": round(weight, 4), "mix": round(roll_mix, 4),
            "ang_now_refzero": round(math.degrees(
                now.rotation_difference(ref_zero).angle), 3),
            "ang_now_refend": round(math.degrees(
                now.rotation_difference(ref_end).angle), 3),
            "ang_now_ref": round(math.degrees(
                now.rotation_difference(reference).angle), 3)}))
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


END_ZERO_FRAME = CANCEL


_PHIDBG = bool(os.environ.get("D18_PHIDBG"))
_PHIDBG_F0 = _env_i("D18_PHIDBG_F0", 0)
_PHIDBG_F1 = _env_i("D18_PHIDBG_F1", 10 ** 6)


def solve_pose(arm, frame, meshes=None):
    _ROLLDBG_FRAME[0] = int(frame)
    _ARMPROBE_FRAME[0] = int(frame)
    _grid0 = UE.ROLL_GRID
    _phi0 = dict(_ROLL_LAST_PHI)
    try:
        _pose = build_pose(arm, frame)
        if _PHIDBG and _PHIDBG_F0 <= int(frame) <= _PHIDBG_F1:
            print("D18_PHI " + json.dumps({
                "f": int(frame),
                "phi": {n: _ROLL_LAST_PHI.get(n) for n in _phi0
                        if abs((_ROLL_LAST_PHI.get(n) or 0.0)
                               - (_phi0.get(n) or 0.0)) > 1e-6
                        or n in ARM_BONES},
                "scope": round(roll_scope(int(frame)), 3),
                "mix": round(roll_mix_at(int(frame), None), 4),
            }, ensure_ascii=False))
        return _pose
    finally:
        UE.ROLL_GRID = _grid0


# =============================================================== 测量
def _pitch(direction):
    return -math.degrees(math.atan2(direction.y, direction.z))


def _knee_angle(arm, side):
    upper = Vector(A.bone_direction(arm, "thigh." + side)).normalized()
    lower = Vector(A.bone_direction(arm, "shin." + side)).normalized()
    return math.degrees(math.acos(max(-1.0, min(1.0, upper.dot(lower)))))


def _hip_flex(arm, side):
    torso = Vector(A.bone_direction(arm, "pelvis")).normalized()
    thigh = Vector(A.bone_direction(arm, "thigh." + side)).normalized()
    return 180.0 - math.degrees(math.acos(max(-1.0, min(1.0, torso.dot(thigh)))))


def _mesh_low_mm(names):
    dg = bpy.context.evaluated_depsgraph_get()
    out = {}
    for name in names:
        obj = bpy.data.objects.get(name)
        if obj is None or obj.type != "MESH":
            continue
        ev = obj.evaluated_get(dg)
        me = ev.to_mesh()
        if len(me.vertices) == 0:
            ev.to_mesh_clear()
            continue
        mw = ev.matrix_world
        out[name] = min((mw @ v.co).z for v in me.vertices) * 1000.0
        ev.to_mesh_clear()
    return out


def _worst_step(samples, index_a, index_b):
    ea, eb = samples[index_a]["euler"], samples[index_b]["euler"]
    worst, at = 0.0, None
    #   ★★ `sorted`：`set` 迭代顺序随哈希种子变 ⟹ `at` 的并列取舍会飘（数值不变）。
    for name in sorted(set(ea) | set(eb)):
        a = ea.get(name, (0.0, 0.0, 0.0))
        b = eb.get(name, (0.0, 0.0, 0.0))
        step = max(abs(x - y) for x, y in zip(a, b))
        if step > worst:
            worst, at = step, (samples[index_b]["frame"], name)
    return worst, at


def _bone_point(mat):
    return mat[3], mat[7], mat[11]


def _pose_seam_split(mats_a, mats_b, moving):
    """两套世界矩阵的「平移不变」逐位差（B08 第 2 件那把尺子，原样照抄）。"""
    ori, rel = 0.0, 0.0
    ori_bone, rel_bone = None, None
    pa, pb = _bone_point(mats_a["pelvis"]), _bone_point(mats_b["pelvis"])
    for name in sorted(mats_a):
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


# =============================================================== 引导
def _load_pose_at(arm, action_name, frame, reset=True):
    """从**落盘 action** 的 fcurve 直接取该帧姿态（euler + location）。"""
    action = bpy.data.actions.get(action_name)
    if action is None:
        return {}, {"action": action_name, "found": False}
    rot_keyed, loc_keyed = _keyed_bones(action)
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    if reset:
        A.reset_pose(arm)
    bpy.context.scene.frame_set(int(frame))
    bpy.context.view_layer.update()
    #   ★★ 必须 `sorted`：`rot_keyed` / `loc_keyed` 是 **set**，其迭代顺序随
    #     `PYTHONHASHSEED` 变 ⟹ 姿态字典的**插入顺序**随之变 ⟹ 下游任何"按顺序
    #     处理"的环节（`_end_pose_continuous` 的逐骨 `_set_euler_nearest`、
    #     关键帧字典顺序）都会得到**不同的欧拉支**。实测：同一脚本两次运行，
    #     `shin.R` 在 `f=1` 就差 4°、到 `f=33` 差 **112°** ⟹ `no_teleport`
    #     时而红时而绿。**确定性是门禁可复现的前提**，不是"洁癖"。
    pose = {name: tuple(math.degrees(v)
                        for v in arm.pose.bones[name].rotation_euler)
            for name in sorted(rot_keyed) if name in arm.pose.bones}
    loc = {name: tuple(arm.pose.bones[name].location)
           for name in sorted(loc_keyed) if name in arm.pose.bones}
    if loc:
        pose["@loc"] = loc
    info = {"action": action_name, "found": True, "frame": int(frame),
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
    global ZERO, END_POSE, END_ANKLE, END_OFF, TUCK_ANKLE, SEAM_RX, END_RX
    for table in (ZERO_BASIS, ZERO_DIR, END_BASIS, END_DIR, END_KNEE_DIR,
                  END_ELBOW_DIR, END_HAND_DIR,
                  SEAM_FIST, SEAM_ELBOW_DIR, SEAM_HAND_DIR,
                  SEAM_ANKLE, SEAM_FOOT_EULER, END_FOOT_BASIS, SEAM_RX, END_RX,
                  END_OFF, END_ANKLE, END_TOE, TUCK_ANKLE, KNEE_DIR, ARM_MAX,
                  PLANT_KEYS,
                  ELBOW_KEYS, HAND_DIR_KEYS, FOOT_KEYS, LOCK_POSE):
        table.clear()
    _LOCK_REUSED[0] = 0

    arm, meshes = A.open_animation_project()
    A.setup_scene()
    for action_name in (SEAM_ACTION, END_ACTION):
        if action_name not in bpy.data.actions:
            raise RuntimeError("动作 %s 不在落盘文件里" % action_name)

    for side in SIDES:
        UE.ARM_LEN[side] = {
            "upper": arm.pose.bones["upperarm." + side].length,
            "forearm": arm.pose.bones["forearm." + side].length,
            "hand": arm.pose.bones["hand." + side].length}
        ARM_MAX[side] = (UE.ARM_LEN[side]["upper"]
                         + UE.ARM_LEN[side]["forearm"]
                         + UE.ARM_LEN[side]["hand"])

    UE.ROLL_STEP_DEG = _env_f("D18_ROLLSTEP", 2.0)
    UE.ROLL_GRID = UE._roll_grid()
    UE.EULER_Y_SAFE = _env_f("D18_YSAFE", 88.0)
    UE.EULER_Y_WEIGHT = _env_f("D18_YWEIGHT", 0.0)

    for extra in LEG_BONES + ("foot.L", "foot.R", "toe.L", "toe.R"):
        if extra not in A.PROBE_BONES:
            A.PROBE_BONES = tuple(A.PROBE_BONES) + (extra,)
        if extra not in A.PROBE_TAILS:
            A.PROBE_TAILS = tuple(A.PROBE_TAILS) + (extra,)
    A.PROBE_KEYS = A.PROBE_BONES + tuple(n + ".tail" for n in A.PROBE_TAILS)

    # ---- 接缝姿态（起点）----------------------------------------------------
    ZERO, seam_info = _load_pose_at(arm, SEAM_ACTION, SEAM_FRAME)
    if not ZERO:
        raise RuntimeError("读不到接缝姿态")
    # ---- 终点姿态（`Idle_01@0`）--------------------------------------------
    END_POSE, end_info = _load_pose_at(arm, END_ACTION, END_FRAME)
    if not END_POSE:
        raise RuntimeError("读不到终点姿态")

    # ★ 落盘真值 vs 手写重演（接缝）
    arm.animation_data.action = bpy.data.actions[SEAM_ACTION]
    A._bind_slot(arm, bpy.data.actions[SEAM_ACTION])
    bpy.context.scene.frame_set(int(SEAM_FRAME))
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
    SEAM_MATCH.update({
        "src": "%s@%d" % (SEAM_ACTION, SEAM_FRAME), "saved": seam_info,
        "geom_pos": round(geom_pos, 6), "pos_bone": geom_pos_bone,
        "geom_dir": round(geom_dir, 6), "dir_bone": geom_dir_bone,
        "matched": bool(geom_pos <= SEAM_REPLAY_POS_MAX_MM
                        and geom_dir <= SEAM_REPLAY_DIR_MAX_DEG)})

    # ★ 落盘真值 vs 手写重演（终点）
    arm.animation_data.action = bpy.data.actions[END_ACTION]
    A._bind_slot(arm, bpy.data.actions[END_ACTION])
    bpy.context.scene.frame_set(int(END_FRAME))
    bpy.context.view_layer.update()
    end_heads = {}
    for name in A.PROBE_BONES:
        if name in arm.pose.bones:
            end_heads[name] = Vector(A.bone_world(arm, name, "head"))
    arm.animation_data.action = None
    replay_end, _dirs = _world_snapshot(arm, END_POSE)
    end_geom, end_bone = 0.0, None
    for name, point in end_heads.items():
        other = replay_end.get(name)
        if other is None:
            continue
        gap = (point - other).length * 1000.0
        if gap > end_geom:
            end_geom, end_bone = gap, name
    END_MATCH.update({"src": "%s@%d" % (END_ACTION, END_FRAME),
                      "saved": end_info, "geom_pos": round(end_geom, 6),
                      "pos_bone": end_bone,
                      "matched": bool(end_geom <= SEAM_REPLAY_POS_MAX_MM)})

    # ---- 两个姿态的关键世界锚点 --------------------------------------------
    A.apply_pose(arm, ZERO)
    bpy.context.view_layer.update()
    for side in SIDES:
        SEAM_ANKLE[side] = Vector(A.bone_world(arm, "foot." + side, "head"))
        SEAM_FIST[side] = Vector(A.bone_world(arm, "hand." + side, "tail"))
        SEAM_HAND_DIR[side] = Vector(
            A.bone_direction(arm, "hand." + side)).normalized()
        shoulder = Vector(A.bone_world(arm, "upperarm." + side, "head"))
        elbow = Vector(A.bone_world(arm, "upperarm." + side, "tail"))
        SEAM_ELBOW_DIR[side] = tuple((elbow - shoulder).normalized())
        SEAM_FOOT_EULER[side] = tuple(ZERO.get("foot." + side, (0.0, 0.0, 0.0)))
    for name in TORSO_BONES:
        SEAM_RX[name] = float(ZERO.get(name, (0.0, 0.0, 0.0))[0])

    A.apply_pose(arm, END_POSE)
    bpy.context.view_layer.update()
    for side in SIDES:
        END_ANKLE[side] = Vector(A.bone_world(arm, "foot." + side, "head"))
        END_TOE[side] = Vector(A.bone_world(arm, "toe." + side, "head"))
        shoulder = Vector(A.bone_world(arm, "upperarm." + side, "head"))
        fist = Vector(A.bone_world(arm, "hand." + side, "tail"))
        END_OFF[side] = tuple(fist - shoulder)
        END_FOOT_BASIS["foot." + side] = (
            arm.pose.bones["foot." + side].matrix.to_3x3().copy())
        hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
        knee = Vector(A.bone_world(arm, "shin." + side, "head"))
        ankle = Vector(A.bone_world(arm, "foot." + side, "head"))
        axis = (ankle - hip).normalized()
        bulge = (knee - hip) - axis * (knee - hip).dot(axis)
        END_KNEE_DIR[side] = (bulge.normalized() if bulge.length > 1e-9
                              else Vector((0.0, -0.94, -0.34)))
        shoulder = Vector(A.bone_world(arm, "upperarm." + side, "head"))
        elbow = Vector(A.bone_world(arm, "forearm." + side, "head"))
        wrist = Vector(A.bone_world(arm, "hand." + side, "head"))
        arm_axis = (wrist - shoulder).normalized()
        arm_bulge = (elbow - shoulder) - arm_axis * (elbow - shoulder).dot(arm_axis)
        END_ELBOW_DIR[side] = (arm_bulge.normalized() if arm_bulge.length > 1e-9
                               else Vector((0.0, 0.0, 1.0)))
        END_HAND_DIR[side] = Vector(A.bone_direction(arm, "hand." + side)).normalized()
    for name in TORSO_BONES + ("shoulder.L", "shoulder.R") + ARM_BONES + LEG_BONES:
        if name in arm.pose.bones:
            END_BASIS[name] = tuple(
                arm.pose.bones[name].matrix.to_3x3().to_quaternion())
    for name in ARM_BONES + LEG_BONES:
        END_DIR[name] = Vector(A.bone_direction(arm, name)).normalized()
    for name in TORSO_BONES:
        END_RX[name] = float(END_POSE.get(name, (0.0, 0.0, 0.0))[0])

    # ---- 膝向：接缝姿态下的"膝鼓出"方向（与 D16 同口径）--------------------
    A.apply_pose(arm, ZERO)
    bpy.context.view_layer.update()
    for side in SIDES:
        hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
        knee = Vector(A.bone_world(arm, "shin." + side, "head"))
        ankle = Vector(A.bone_world(arm, "foot." + side, "head"))
        axis = (ankle - hip).normalized()
        bulge = (knee - hip) - axis * (knee - hip).dot(axis)
        KNEE_DIR[side] = (bulge.normalized() if bulge.length > 1e-9
                          else Vector((0.0, -0.94, -0.34)))
    _kd_env = os.environ.get("D18_KNEE_DIR", "").strip()
    if _kd_env:
        kd = [float(x) for x in _kd_env.split(",")]
        KNEE_DIR["L"] = Vector((kd[0], kd[1], kd[2])).normalized()
        KNEE_DIR["R"] = Vector((-kd[0], kd[1], kd[2])).normalized()

    for bone in ARM_BONES + LEG_BONES:
        UE.IDLE_BASIS[bone] = arm.pose.bones[bone].matrix.to_3x3().copy()
        UE.IDLE_DIR[bone] = A.bone_direction(arm, bone)

    ZERO_WORLD = {n: tuple(v) for n, v in replay_heads.items()}
    for name in A.PROBE_BONES:
        if name in arm.pose.bones:
            ZERO_BASIS[name] = tuple(
                arm.pose.bones[name].matrix.to_3x3().to_quaternion())
    for name in ARM_BONES + LEG_BONES:
        if name in arm.pose.bones:
            ZERO_DIR[name] = Vector(A.bone_direction(arm, name)).normalized()

    # ---- 中段锚点（全部由两个端点**实测**派生，不是拍的）-------------------
    for side in SIDES:
        s = 1.0 if side == "L" else -1.0
        # ★★ D18：仰卧时双拳在**头顶之外的延伸线上**（实测 `hand.L` 骨端
        #    y = +1275 mm，比头还靠后 155 mm）。撑地时必须把拳**往肩下方收**
        #    （y 减小）并**向内收**（|x| 减小），掌才落在肩侧的支撑点上。
        #    ★ 起点 `SEAM_FIST.y` 是**正**的（D17 是负）⟹ 偏移量符号相反。
        #    ★★ 落掌 **z 抬高量**（实测标定）：拳骨端 ≠ 掌网格最低点 —— 掌骨/指骨
        #       网格比 `hand` 骨端**再低 ≈ 45 mm**（实测 `f=8`：拳端 z 16 mm、
        #       逐对象最低点 −29 mm）。D18 首次门禁用 D17 的 z（16/12 mm）⟹ 掌网格
        #       扎进地板 121 mm。现按实测把落掌 z 抬到 **≈65 mm** ⟹ 掌网格最低点
        #       `f=8` 落到 **+20 mm 上下**（`hand_plant_ok` 要求 `[−2, +60]`）。
        _zadd = _env_f("D18_PLANT_ZADD", 0.049)
        # ★★ 落掌**水平**位置（实测标定）：D17 的 `y − 0.120/0.175/0.195` 把掌放在
        #    肩**后方 190~275 mm**。俯卧族没关系（躯干是往**远离**掌的方向翻的）；
        #    仰卧族相反 —— 躯干坐起时肩往**前**走（实测 `f=8` 肩 y=909 → `f=17` y=805），
        #    掌不动 ⟹ `|掌−肩|` 随帧**单调变长**，`f=17` 实测 **652 mm > 臂长 649**
        #    ⟹ `arm_seat_tip` 夹住 ⟹ 掌**离地悬空**（实测 y 差 275 mm 贡献了 42 mm 超长）。
        #    ⟹ 把落掌**往前收**到肩正下方偏后 ≈ 30~135 mm（仍是"身侧/身后"），
        #      既满足清单「身后/身侧」，又给手臂留出 `rA ≤ 0.96` 的余量。
        _dy = _env_f("D18_PLANT_DY_PULL", -0.200)
        _dy1 = _env_f("D18_PLANT_DY", -0.290)
        _dy2 = _env_f("D18_PLANT_DY2", -0.335)
        pull = Vector((SEAM_FIST[side].x * 0.70,
                       SEAM_FIST[side].y + _dy,
                       0.030 + _zadd))
        plant = Vector((SEAM_FIST[side].x * 0.62,
                        SEAM_FIST[side].y + _dy1,
                       0.016 + _zadd))
        plant2 = Vector((SEAM_FIST[side].x * 0.60,
                         SEAM_FIST[side].y + _dy2,
                         0.012 + _zadd))
        # ★★ 键位**不要出现 1 帧的硬台阶**：D17 原键序是
        #    `(LEGS_DOWN, SEAM) → (LEGS_DOWN+1, pull)` —— 把 200 mm 的掌位移
        #    全塞进**一帧**里。仰卧族掌要从"身下 −43 mm"抬到"身侧 +79 mm"，
        #    一帧硬切会让腕链跨过**万向节锁**（实测 `f=5` 手骨世界旋转 **181.1°**、
        #    欧拉 y 分量冲到 **−0.31°** ≈ 锁点）⟹ `no_teleport` 红。
        #    ⟹ 改成 `(START, SEAM) → (LEGS_DOWN, pull) → (PLANT, plant)`：
        #      位移摊到 `0→4→8` 两段线性，每帧 ≤ 50 mm，锁点自然避开。
        #      同时 `f ∈ [0,4]` 仍有帧落在 `z < −2 mm`（`hand_plant_below_frames`
        #      = `[0,1,2]`）⟹ `hand_plant_ok` 的"手先在地下"事实核对不受影响。
        PLANT_KEYS[side] = ((START, tuple(SEAM_FIST[side])),
                            (LEGS_DOWN, tuple(pull)),
                            (PLANT, tuple(plant)),
                            (CHEST_UP, tuple(plant)),
                            (HAND_OFF, tuple(plant2)))
        # ★ 肘鼓出：撑地期**往外上方张**（仰卧撑的肘窝朝外）。
        e0 = Vector(SEAM_ELBOW_DIR[side])
        e1 = Vector((0.74 * s, -0.06, 0.66)).normalized()
        e2 = Vector((0.40 * s, -0.30, 0.86)).normalized()
        e_end = tuple(END_ELBOW_DIR[side])          # ★ 实测 `Idle_01@0`，不是常数
        ELBOW_KEYS[side] = ((START, tuple(e0)), (DIR_END, tuple(e1)),
                            (HAND_OFF, tuple(e1)), (TUCK, tuple(e2)),
                            (FOOT_SET, tuple(e2)), (STAND, e_end), (END, e_end))
        h0 = Vector(SEAM_HAND_DIR[side])
        # ★★ 撑地期手骨**压向水平**（掌平摊在地面上）。D17 实测 `h1` 的 z 取
        #    −0.96 时指尖扎进地板 **178 mm** ⟹ 本支取 |z| 小的值。
        _hd = _env_f("D18_HAND_DOWN", -0.30)
        _hf = _env_f("D18_HAND_FWD", 0.82)
        h1 = Vector((0.42 * s, _hf, _hd)).normalized()
        _hde = _env_i("D18_HAND_DIR_END", DIR_END)
        if not (START < _hde < TUCK):
            _hde = DIR_END
        h_end = tuple(END_HAND_DIR[side])           # ★ 实测 `Idle_01@0`，不是常数
        HAND_DIR_KEYS[side] = ((START, tuple(h0)), (_hde, tuple(h1)),
                               (TUCK, tuple(h1)), (FOOT_SET, tuple(h1)),
                               (STAND, h_end), (END, h_end))
        f0 = Vector(SEAM_FOOT_EULER[side])
        FE = (f0[0] * 0.55 - 30.0 * 0.45, f0[1] * 0.5, f0[2] * 0.5)
        FOOT_KEYS[side] = ((START, tuple(f0)), (LEGS_DOWN, tuple(f0)),
                           (PLANT, (f0[0] * 0.72, f0[1] * 0.7, f0[2] * 0.7)),
                           (CHEST_UP, (f0[0] * 0.62, f0[1] * 0.6, f0[2] * 0.6)),
                           (HAND_OFF, (f0[0] * 0.50, f0[1] * 0.5, f0[2] * 0.5)),
                           (TUCK, FE), (FOOT_SET, FE), (END, FE))
        # ★ 收腿锚点：膝收到身下、踝在髋前下方（离地），为蹬地做准备。
        #   ★★ `D18_TUCK_ANKLE_DY` / `D18_TUCK_ANKLE_Z` 是**速度标定旋钮**：
        #      实测 `no_teleport` 的真几何硬点就是 `thigh.L` 在 f20→21 的
        #      **34.4°/帧**（探针 `probe_d18_phi.py` 证明：即便放开两帧的绕轴滚转，
        #      该步长仍 ≥32.4° ⟹ **不是表示问题，是踝目标真的跑太快**）。
        #      踝从 `TUCK_ANKLE`（默认 y = 骨盆 +150 mm、z = 210 mm）走到
        #      `FOOT_SET` 的落脚点只用了 6 帧，左腿横move 610 mm。
        #      把收腿锚点往落脚点方向挪（`DY` 变小 / `Z` 变小）即可**按比例**降低
        #      每帧角速度 —— 这是改动作节奏，不是放宽容差。
        TUCK_ANKLE[side] = Vector((0.140 * s,
                                   pelvis_y_at(TUCK) + TUCK_ANKLE_DY,
                                   TUCK_ANKLE_Z))

    HEM_STATIC.clear()
    for name, value in _mesh_low_mm(HEM_OBJECTS).items():
        HEM_STATIC[name] = value

    JS._PREV_EULER.clear()
    UE.CARRY_Q.clear()
    LOCK_POSE.clear()
    A.apply_pose(arm, ZERO)
    bpy.context.view_layer.update()
    for name in ARM_BONES + LEG_BONES:
        UE.CARRY_Q[name] = arm.pose.bones[name].matrix.to_3x3().to_quaternion()
    for name, value in ZERO.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)

    # ---- 实测标定：撑地段胸骨尾端抬升 --------------------------------------
    A.apply_pose(arm, torso_pose(CHEST_UP))
    bpy.context.view_layer.update()
    chest_mid = Vector(A.bone_world(arm, "chest", "tail")).z * 1000.0

    A.report("D18_LAYOUT", {
        "total_frames": TOTAL, "seconds": round(TOTAL / float(A.FPS), 3),
        "legs_down": LEGS_DOWN, "plant": PLANT, "chest_up": CHEST_UP,
        "hand_off": HAND_OFF, "tuck": TUCK,
        "foot_set": FOOT_SET, "rise_mid": RISE_MID, "stand": STAND,
        "vertical_channel": {
            "shape": "★ **无弹道段**：骨盆沿单调上升曲线 128 → 830 mm（四段支点：背/臀→掌→脚→双腿）",
            "pelvis_z_keys": [list(k) for k in PELVIS_Z_KEYS],
            "pelvis_y_keys": [list(k) for k in PELVIS_Y_KEYS]},
        "seam": {"action": SEAM_ACTION, "frame": SEAM_FRAME, "src": seam_info},
        "end": {"action": END_ACTION, "frame": END_FRAME, "src": end_info},
        "measured": {
            "seam_pelvis_z_mm": round(pelvis_z_at(START) * 1000.0, 3),
            "end_pelvis_z_mm": round(pelvis_z_at(END) * 1000.0, 3),
            "rise_mm": round((pelvis_z_at(END) - pelvis_z_at(START)) * 1000.0, 3),
            "seam_ankle_mm": {s: [round(v * 1000.0, 3) for v in SEAM_ANKLE[s]]
                              for s in SIDES},
            "end_ankle_mm": {s: [round(v * 1000.0, 3) for v in END_ANKLE[s]]
                             for s in SIDES},
            "seam_fist_mm": {s: [round(v * 1000.0, 3) for v in SEAM_FIST[s]]
                             for s in SIDES},
            "seam_shoulder_mm": {
                s: [round(v * 1000.0, 3) for v in
                    Vector(A.bone_world(arm, "upperarm." + s, "head"))]
                for s in SIDES} if False else None,
            "end_off_mm": {s: [round(v * 1000.0, 3) for v in END_OFF[s]]
                           for s in SIDES},
        },
        "chest_tail_at_chest_up_mm": round(chest_mid, 3),
        "roll_weight_mode": ROLL_WEIGHT_MODE,
        "note": ("D18 背面起身：零位 = **`Knockdown_B@20` 落盘帧**；终点 = "
                 "**`Idle_01@0` 落盘帧**（跨族接缝）。竖直通道**无弹道段**，"
                 "骨盆单调升 **702 mm**；支点**背/臀 → 掌 → 脚**，换**两次**。"),
    })
    return arm, meshes


# =============================================================== 门禁
def getup_assertions(arm, action, samples, meshes, end_mats_ref):  # noqa: C901
    #   ★★★ 时间重参数化：本函数里的相位常量一律是**输出帧空间**（Action / samples
    #   的帧号空间）。下面这行把它们**就地重绑**为局部名；`OUT_TOTAL == TOTAL` 时
    #   `_OUT_PHASES` 与源帧常量逐位相同 ⟹ 与旧行为逐位一致。
    (LEGS_DOWN, PLANT, CHEST_UP, HAND_OFF, TUCK, FOOT_SET,
     RISE_MID, STAND, TOTAL, END) = _OUT_PHASES
    res = {}
    scene = bpy.context.scene
    arm.animation_data.action = action
    A._bind_slot(arm, action)

    moving = _pelvis_moving(arm)
    seam_mats = CR.action_world_matrices(arm, bpy.data.actions[SEAM_ACTION],
                                         SEAM_FRAME)
    mats0 = CR.action_world_matrices(arm, action, START)
    ori0, rel0, ob0, rb0 = _pose_seam_split(mats0, seam_mats, moving)
    res["seam_in_orient_delta"] = float("%.3e" % ori0)
    res["seam_in_orient_bone"] = ob0
    res["seam_in_relpos_delta_mm"] = round(rel0 * 1000.0, 6)
    res["seam_in_relpos_bone"] = rb0
    res["seam_in_raw_delta"] = float("%.3e" % CR.matrix_delta(mats0, seam_mats))
    res["seam_in_ok"] = bool(max(ori0, rel0) <= SEAM_TOL)
    res["seam_in_note"] = (
        "★★ 首帧**逐位** = `%s@%d`（平移不变尺子）。容差 %.0e，未放宽。"
        % (SEAM_ACTION, SEAM_FRAME, SEAM_TOL))

    # ---- ★★★ 末帧 = `Idle_01@0`（本支最硬的判据）---------------------------
    mats_end = CR.action_world_matrices(arm, action, END)
    end_delta = CR.matrix_delta(mats_end, end_mats_ref)
    worst_end, worst_end_bone = 0.0, None
    for name in mats_end:
        ref = end_mats_ref.get(name)
        if ref is None:
            continue
        gap = max(abs(a - b) for a, b in zip(mats_end[name], ref))
        if gap > worst_end:
            worst_end, worst_end_bone = gap, name
    res["end_vs_idle_matrix_delta"] = float("%.3e" % end_delta)
    res["end_vs_idle_worst_bone"] = worst_end_bone
    res["end_vs_idle_worst_delta"] = float("%.3e" % worst_end)
    ori_e, rel_e, ob_e, rb_e = _pose_seam_split(mats_end, end_mats_ref, moving)
    res["end_vs_idle_orient_delta"] = float("%.3e" % ori_e)
    res["end_vs_idle_relpos_mm"] = round(rel_e * 1000.0, 9)
    res["end_matches_idle_tol"] = END_TOL
    res["end_matches_idle_ok"] = bool(max(end_delta, worst_end) <= END_TOL)
    res["end_matches_idle_note"] = (
        "★★★ **本支最硬的判据**：末帧（`f = %d`）**逐骨 4×4 世界矩阵**必须与 "
        "`%s@%d` 一致（`max_delta ≤ %.0e`）。★ 用**世界矩阵**而不是欧拉三元组。"
        % (END, END_ACTION, END_FRAME, END_TOL))

    # ---- 上/下缘 & 骨盆逐帧 --------------------------------------------------
    arm.animation_data.action = None
    A.apply_pose(arm, ZERO)
    bpy.context.view_layer.update()
    zero = _body_metrics(arm)
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    per, clear, feet, handlow = {}, {}, {}, {}
    for frame in range(0, TOTAL + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        per[frame] = _body_metrics(arm)
        clear[frame] = _foot_clearance()
        feet[frame] = A.foot_lowest_by_side()
        handlow[frame] = {s: _lowest_of(HAND_MESHES[s]) for s in SIDES}

    zs = {f: per[f]["pelvis"].z for f in per}
    ys = {f: per[f]["pelvis"].y for f in per}
    xs = {f: per[f]["pelvis"].x for f in per}
    cpitch = {f: per[f]["chest_pitch_deg"] for f in per}

    # ---- ★ 起身幅度 ---------------------------------------------------------
    res["pelvis_z_mm"] = {str(f): round(zs[f] * 1000.0, 3) for f in sorted(zs)}
    res["pelvis_y_mm"] = {str(f): round(ys[f] * 1000.0, 3) for f in sorted(ys)}
    rise = (zs[END] - zs[START]) * 1000.0
    res["rise_net_mm"] = round(rise, 3)
    res["rise_min_mm"] = RISE_MIN_MM
    res["rise_reach_ok"] = bool(rise >= RISE_MIN_MM)
    res["rise_reach_note"] = (
        "★ 骨盆 z 从起点到终点净升 **≥ %.0f mm**（防「只起来一半」）。"
        "阈值由**实测**导出：起点 %.1f mm（`%s@%d`）→ 终点 %.1f mm（`%s@%d`），"
        "真实净升 %.1f mm ⟹ 阈值取实测的 %.0f%%。"
        "（清单计划写的 650 mm 基于**推算**；实测终点是 830 mm ⟹ 这是**把推算换成实测**。）"
        % (RISE_MIN_MM, zs[START] * 1000.0, SEAM_ACTION, SEAM_FRAME,
           zs[END] * 1000.0, END_ACTION, END_FRAME, rise,
           RISE_MIN_MM * 100.0 / max(1e-9, rise)))

    # ---- ★ 单调上升（窗口 `[FOOT_SET, END]`，与清单 §3 一致）---------------
    win = [f for f in range(FOOT_SET, TOTAL + 1)]
    rises = [{"frame": f, "dz_mm": round((zs[f] - zs[f - 1]) * 1000.0, 4)}
             for f in win[1:]
             if (zs[f] - zs[f - 1]) * 1000.0 < -RISE_MONO_TOL_MM]
    full_rises = [{"frame": f, "dz_mm": round((zs[f] - zs[f - 1]) * 1000.0, 4)}
                  for f in range(START + 1, TOTAL + 1)
                  if (zs[f] - zs[f - 1]) * 1000.0 < -RISE_MONO_TOL_MM]
    res["rise_monotone_violations_window"] = rises
    res["rise_monotone_violations_full"] = full_rises
    res["rise_monotone_tol_mm"] = RISE_MONO_TOL_MM
    res["rise_monotone_window"] = [FOOT_SET, TOTAL]
    res["rise_monotone_ok"] = bool(not rises)
    res["rise_monotone_note"] = (
        "★ 骨盆 z 在 `[FOOT_SET=%d, END=%d]` 必须**单调不降**（容差 %.1f mm/帧）。"
        "★ 本支实测**全段**（`[0, END]`）也单调（`rise_monotone_violations_full = []`）"
        " —— 起身是**一次**持续发力，中途不回落。"
        % (FOOT_SET, TOTAL, RISE_MONO_TOL_MM))

    # ---- ★ 撑地推起：胸骨尾端抬升（窗口 `[PLANT, HAND_OFF]`）--------------
    ct = {f: per[f]["chest_tail"].z * 1000.0 for f in per}
    res["chest_tail_z_mm"] = {str(f): round(ct[f], 3) for f in sorted(ct)}
    chest_rise = ct[HAND_OFF] - ct[PLANT]
    res["chest_rise_mm"] = round(chest_rise, 3)
    res["chest_rise_min_mm"] = CHEST_RISE_MIN_MM
    res["chest_rise_ok"] = bool(chest_rise >= CHEST_RISE_MIN_MM)
    res["chest_rise_note"] = (
        "★ 撑地段 `[PLANT=%d, HAND_OFF=%d]` 胸骨尾端世界 z 必须**净升 ≥ %.0f mm**"
        "（证明「撑地真的把上身顶起来了」，而不是只有胳膊在动）。"
        % (PLANT, HAND_OFF, CHEST_RISE_MIN_MM))

    # ---- ★ 落腿段：膝**真的放开**（D18 独有）------------------------------
    knee_start = {s: per[START]["knee_deg"][s] for s in SIDES}
    knee_land = {s: per[LEGS_DOWN]["knee_deg"][s] for s in SIDES}
    unfold = {s: round(knee_start[s] - knee_land[s], 3) for s in SIDES}
    res["knee_unfold_start_deg"] = unfold
    res["knee_unfold_start_min_deg"] = KNEE_UNFOLD_MIN_DEG
    res["knee_unfold_start_ok"] = bool(
        min(unfold.values()) >= KNEE_UNFOLD_MIN_DEG)
    res["knee_unfold_start_note"] = (
        "★★ **D18 独有**：`f ∈ [START=%d, LEGS_DOWN=%d]` 膝屈角必须**真的放开**"
        "（每条腿都减 ≥ %.0f°；实测起点 %.2f° → %.2f°）。"
        "证明「腿是自己落下来的」，而不是被骨盆拖下来的。"
        % (START, LEGS_DOWN, KNEE_UNFOLD_MIN_DEG,
           min(knee_start.values()), min(knee_land.values())))

    # ---- ★★ 支点交接 0：手掌**先从地下出来、再落到地面**（D18 独有）-------
    hand_min = {f: min(handlow[f]["L"], handlow[f]["R"]) for f in handlow}
    res["hand_low_mm"] = {str(f): round(hand_min[f], 2) for f in sorted(hand_min)}
    below = [f for f in range(START, LEGS_DOWN + 1)
             if hand_min[f] < HAND_PLANT_BELOW_MM]
    plant_ok = bool(-2.0 <= hand_min[PLANT] <= HAND_TOUCH_MAX_MM)
    res["hand_plant_below_mm"] = HAND_PLANT_BELOW_MM
    res["hand_plant_below_frames"] = below
    res["hand_plant_at_plant_mm"] = round(hand_min[PLANT], 2)
    res["hand_plant_ok"] = bool(below and plant_ok)
    res["hand_plant_note"] = (
        "★★ **支点交接 0（D18 独有）**：仰卧起点手掌**在地面之下**"
        "（实测 −72 ~ −82 mm），必须实测到 `f ∈ [START=%d, LEGS_DOWN=%d]` 有 **z < "
        "%.0f mm** 的帧（事实核对：手确实还在身下），**并在 `f = PLANT=%d` 落到地面**"
        "（z ∈ [−2, +%.0f] mm）。缺这条，就有一整段「手到底在不在上」没人管。"
        % (START, LEGS_DOWN, HAND_PLANT_BELOW_MM, PLANT, HAND_TOUCH_MAX_MM))

    # ---- ★★ 支点交接 1：手掌离地（两侧都量）-------------------------------
    on = [f for f in range(START, HAND_OFF + 1)
          if hand_min[f] > HAND_TOUCH_MAX_MM]
    off = [f for f in range(HAND_OFF + 1, TOTAL + 1)
           if hand_min[f] < HAND_OFF_MIN_MM]
    res["hand_touch_max_mm"] = HAND_TOUCH_MAX_MM
    res["hand_off_min_mm"] = HAND_OFF_MIN_MM
    res["hand_on_violations"] = on
    res["hand_off_violations"] = off
    res["hand_off_ok"] = bool(not on and not off)
    res["hand_off_note"] = (
        "★★ **支点交接 1**：`f ≤ HAND_OFF=%d` 时手掌（`Hand_Palm_*` + `Finger_*` "
        "网格）最低点必须 **≤ %.0f mm**（手真的在地上推）；`f > HAND_OFF` 必须 "
        "**≥ %.0f mm**（手确实离地了）。**两侧都量**。"
        % (HAND_OFF, HAND_TOUCH_MAX_MM, HAND_OFF_MIN_MM))

    # ---- ★★ 支点交接 2：双脚接住地面（唯一帧）-----------------------------
    sole = {f: min(clear[f]["L"], clear[f]["R"]) for f in clear}
    res["sole_mm"] = {str(f): (None if sole[f] is None
                              else round(sole[f] * 1000.0, 2))
                      for f in sorted(sole)}
    touch = [f for f in range(TUCK, FOOT_SET + 1)
             if sole[f] is not None and sole[f] * 1000.0 <= SOLETOUCH_MAX_MM]
    res["foot_touch_max_mm"] = SOLETOUCH_MAX_MM
    res["foot_touch_frames"] = touch
    res["foot_touch_frame"] = (touch[0] if len(touch) == 1 else None)
    res["foot_takeover_ok"] = bool(len(touch) == 1 and touch[0] == FOOT_SET)
    res["foot_takeover_note"] = (
        "★★ **支点交接 2**：脚接住地面的帧必须**唯一**且落在 `[TUCK=%d, "
        "FOOT_SET=%d]` 内（口径 = **首次鞋底 ≤ %.0f mm**）。实测 `%s`。"
        % (TUCK, FOOT_SET, SOLETOUCH_MAX_MM, touch))

    # ---- ★ 站姿族硬约束：脚不滑 + 鞋底贴地（`f ≥ FOOT_SET`）--------------
    slide = {}
    for probe in ("toe.L", "toe.R"):
        pts = [Vector(per[f]["toe"][probe[-1]]) for f in win]
        ref = pts[0]
        slide[probe] = round(max((p - ref).length for p in pts) * 1000.0, 4)
    res["foot_slide_mm_after_set"] = slide
    res["foot_slide_max_mm"] = FOOT_SLIDE_MAX_MM
    res["no_foot_slide_ok"] = bool(slide and max(slide.values())
                                   <= FOOT_SLIDE_MAX_MM)
    res["no_foot_slide_note"] = (
        "★ 清单 §6 硬约束：`f ≥ FOOT_SET=%d` 双脚 `foot_probe`（`toe.L/R` 骨端）"
        "世界位移 **≤ %.0f mm**。" % (FOOT_SET, FOOT_SLIDE_MAX_MM))
    soles_tail = [sole[f] * 1000.0 for f in win if sole[f] is not None]
    res["sole_tail_min_mm"] = round(min(soles_tail), 3)
    res["sole_tail_max_mm"] = round(max(soles_tail), 3)
    res["sole_ground_ok"] = bool(soles_tail
                                 and min(soles_tail) >= SOLE_MIN_MM
                                 and max(soles_tail) <= SOLE_MAX_MM)
    res["sole_ground_note"] = (
        "★ 清单 §6：`f ≥ FOOT_SET` 鞋底必须 ∈ **[%.0f, %.0f] mm**（支撑脚贴地）。"
        % (SOLE_MIN_MM, SOLE_MAX_MM))

    # ---- ★ 收招不许瞬停 ----------------------------------------------------
    tail_start = int(TOTAL - NO_SNAP_TAIL_FRAMES)
    steps = [round(_worst_step(samples, i - 1, i)[0], 6)
             for i in range(tail_start + 1, TOTAL + 1)]
    res["no_snap_tail_steps_deg"] = steps
    res["no_snap_stop_ok"] = bool(
        len(steps) >= 2
        and all(steps[i] >= steps[i + 1] - 1e-6 for i in range(len(steps) - 1))
        and steps[-1] <= 1e-6)
    res["no_snap_tail_window"] = [tail_start, TOTAL]
    res["no_snap_ruler_note"] = (
        "★ 口径按清单 §0.6 原文：「末 6 帧角度增量的绝对值**单调收敛**」。")

    # ---- ★ 定向运动：根位移（本支构造性 = −470 mm，符号与 D17 相反）-------
    dx = (xs[END] - xs[START]) * 1000.0
    dy = (ys[END] - ys[START]) * 1000.0
    res["root_motion_net_mm"] = round(math.hypot(dx, dy), 3)
    res["root_motion_m"] = [round(dx / 1000.0, 6), round(dy / 1000.0, 6)]
    res["root_motion_ok"] = bool(abs(dx) <= 2.0
                                 and abs(dy + 470.0) <= 10.0)
    res["root_motion_note"] = (
        "★ 本支骨盆要向**脚的方向**走 **−470 mm**（`+470 → 0`），"
        "把身体带到双脚上方，如实登记（★ 符号与 D17 的 +550 相反）。")

    # ---- 末帧登记 ----------------------------------------------------------
    end_vz = (zs[END] - zs[END - 1]) * 1000.0
    res["end_pelvis_z_mm"] = round(zs[END] * 1000.0, 3)
    res["end_vz_mm_per_frame"] = round(end_vz, 6)
    res["end_vz_zero_ok"] = bool(abs(end_vz) <= 1e-6)

    # ---- ★ 力量传导链（脚→腿→髋→腰→肩→手）------------------------------
    knee_flex = {s: round(max(abs(per[f]["knee_deg"][s] - zero["knee_deg"][s])
                              for f in per), 3) for s in SIDES}
    hipf = {s: [per[f]["hip_flex_deg"][s] for f in per] for s in SIDES}
    hip_dev = {s: round(max(abs(v - hipf[s][0]) for v in hipf[s]), 3)
               for s in SIDES}
    shoulder_move, shoulder_at = 0.0, None
    for frame in per:
        for s in SIDES:
            gap = (per[frame]["shoulder"][s] - zero["shoulder"][s]).length * 1000.0
            if gap > shoulder_move:
                shoulder_move, shoulder_at = gap, (s, frame)
    fist_dev, fist_dev_at = 0.0, None
    for frame in per:
        for s in SIDES:
            gap = (per[frame]["fist"][s] - ZERO_FIST[s]).length * 1000.0
            if gap > fist_dev:
                fist_dev, fist_dev_at = gap, (s, frame)
    ankle_dev = max((per[f]["ankle"][s] - zero["ankle"][s]).length
                    for f in per for s in SIDES) * 1000.0
    pelvis_span = max((per[f]["pelvis"] - per[0]["pelvis"]).length
                      for f in per) * 1000.0
    waist_span = max(abs(cpitch[f] - cpitch[0]) for f in per)
    res["fist_travel_mm"] = round(fist_dev, 3)
    res["fist_travel_at"] = fist_dev_at
    res["ankle_travel_mm"] = round(ankle_dev, 3)
    res["shoulder_move_mm"] = round(shoulder_move, 3)
    res["pelvis_span_mm"] = round(pelvis_span, 3)
    res["chain_travel"] = {
        "foot_mm": round(ankle_dev, 2), "knee_deg": round(max(knee_flex.values()), 3),
        "hip_deg": round(max(hip_dev.values()), 3), "waist_deg": round(waist_span, 3),
        "shoulder_mm": round(shoulder_move, 2), "hand_mm": round(fist_dev, 2)}
    res["chain_present_ok"] = bool(
        res["chain_travel"]["foot_mm"] > 50.0
        and res["chain_travel"]["knee_deg"] > 20.0
        and res["chain_travel"]["hip_deg"] > 8.0
        and res["chain_travel"]["waist_deg"] > 4.0
        and res["chain_travel"]["shoulder_mm"] > 5.0
        and res["chain_travel"]["hand_mm"] > 30.0)
    res["chain_present_note"] = (
        "★ 清单 §6：力量传导链 **脚→腿→髋→腰→肩→手**，每段都要有真实工作量。"
        "本支六段全由**实测**度量。")

    # ---- 穿模 --------------------------------------------------------------
    frames = sorted(set(list(range(0, TOTAL + 1, CLIP_EVERY))
                        + [LEGS_DOWN, PLANT, CHEST_UP, HAND_OFF, TUCK, FOOT_SET,
                           RISE_MID, STAND, TOTAL]))
    worst_clip, worst_clip_at, worst_clip_frame = 0.0, None, None
    for frame in frames:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        clip = PD.clip_metrics(arm)
        if clip["clip_max_mm"] > worst_clip:
            worst_clip, worst_clip_at, worst_clip_frame = (
                clip["clip_max_mm"], clip["clip_at"], frame)
    res["clip_max_mm"] = round(worst_clip, 2)
    res["clip_at"] = worst_clip_at
    res["clip_frame"] = worst_clip_frame
    res["no_face_clip_ok"] = bool(worst_clip <= CLIP_MAX_MM)

    # ---- 可达性 ------------------------------------------------------------
    worst_reach, worst_reach_frame = 0.0, None
    worst_leg, worst_leg_frame = 0.0, None
    for frame in range(0, TOTAL + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        for side in SIDES:
            shoulder = Vector(A.bone_world(arm, "upperarm." + side, "head"))
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

    # ---- 下摆静态件 --------------------------------------------------------
    hem_now = _mesh_low_mm(HEM_OBJECTS)
    hem_static = True
    hem_rows = {}
    for name, value in hem_now.items():
        hem_rows[name] = round(value, 4)
        ref = HEM_STATIC.get(name)
        if ref is None or abs(value - ref) > 1e-6:
            hem_static = False
    res["hem_low_mm"] = hem_rows
    res["hem_static_ok"] = bool(hem_static and hem_rows)
    res["hem_static_note"] = (
        "★ `%s` 是**已知模型侧绑定遗漏**（`parent=None` / `vgroups=0`）⟹ 钉在世界"
        "原点、**不随骨架动**；本判据核对它们世界最低点**首末逐位相同**。"
        % ",".join(HEM_OBJECTS))

    # ---- 剪影 / aspect：只报不判 -------------------------------------------
    sil = P.silhouette(arm, "d18")
    res["aspect"] = sil["aspect"]
    res["width_m"] = sil["width_m"]
    res["height_m"] = sil["height_m"]

    # ---- ★ 停用判据（显式登记理由）----------------------------------------
    res["disabled_gates"] = {
        "ground_hold_ok": "DISABLED —— 贴地族判据（骨盆逐位固定）。本支骨盆要跑 "
                          "702 mm ⟹ 照抄必然红。换成 `rise_monotone_ok` + `rise_reach_ok`。",
        "back_land_ok": "DISABLED —— 贴地族判据（后脑贴地）。本支末帧是**站姿**。",
        "landing_plateau_ok": "DISABLED —— 贴地族判据（落地后骨盆逐位相同）。"
                              "本支末段骨盆构造性固定在 830 mm，但语义不同。",
        "legs_bounce_ok": "DISABLED —— 贴地族判据（腿抖一下再落）。本支腿是**主动收放**。",
        "bounce_present_ok / bounce_single_peak_ok / bounce_no_double_ok":
            "DISABLED —— 贴地族「局部弹起」判据。本支是**主动起身**，无受力弹起。",
        "ballistic_until_land_ok": "DISABLED —— 本支竖直通道**没有弹道段**"
                                   "（全段单调上升，无抛物线可比）。",
        "hitstop_present": "DISABLED —— ★ 本支是**主动发力**动作，**没有「命中帧」**。"
                           "硬套只会得到伪造的停顿。收招由 `no_snap_tail_ok` 守，"
                           "「一次发力、不回落」由 `rise_monotone_ok` 守。",
    }
    res["ballistic_status"] = "DISABLED"
    res["ballistic_phase_registered"] = {
        "T_PHASE_D17": D17_T_PHASE, "T_PHASE_D18": T_PHASE_D18,
        "note": "★ 仅登记（本支竖直通道**不含弹道**，不参与解算）"}

    # ---- 冻结段 ------------------------------------------------------------
    res["lock_frames"] = _LOCK_REUSED[0]
    res["lock_expect"] = 0
    last_steps = [round(_worst_step(samples, i - 1, i)[0], 6)
                  for i in range(STAND + 1, TOTAL + 1)]
    res["end_hold_steps_deg"] = last_steps
    res["end_ground_hold_ok"] = bool(not last_steps
                                     or max(last_steps) <= END_HOLD_MAX_DEG)

    res["seam_zero_saved_ok"] = bool(SEAM_MATCH["matched"])
    res["seam_zero_src"] = SEAM_MATCH["src"]
    res["seam_zero_geom_pos_mm"] = SEAM_MATCH["geom_pos"]
    res["seam_zero_geom_dir_deg"] = SEAM_MATCH["geom_dir"]
    res["seam_zero_worst_bone"] = SEAM_MATCH["pos_bone"]
    res["end_zero_saved_ok"] = bool(END_MATCH["matched"])
    res["end_zero_src"] = END_MATCH["src"]
    res["end_zero_geom_pos_mm"] = END_MATCH["geom_pos"]

    if os.environ.get("D18_TRACE"):
        res["trace"] = {str(f): {
            "pelvis_z": round(zs[f] * 1000.0, 2),
            "pelvis_y": round(ys[f] * 1000.0, 2),
            "chest_tail": round(ct[f], 2),
            "hand_low": round(hand_min[f], 2),
            "sole": None if sole[f] is None else round(sole[f] * 1000.0, 2),
            "knee": {s: round(per[f]["knee_deg"][s], 2) for s in SIDES},
            "hip_flex": {s: round(per[f]["hip_flex_deg"][s], 2) for s in SIDES},
            "ankle_z": {s: round(per[f]["ankle"][s].z * 1000.0, 2) for s in SIDES},
        } for f in range(0, TOTAL + 1)}
    return res


def _lowest_of(names):
    row = _mesh_low_mm(names)
    return None if not row else min(row.values())


def _foot_clearance():
    low = A.foot_lowest_by_side()
    return {s: (low[s][2] if low[s] is not None else None) for s in SIDES}


def _body_metrics(arm):
    lo, hi = PD.head_box()
    return {
        "pelvis": Vector(A.bone_world(arm, "pelvis", "head")),
        "chest_tail": Vector(A.bone_world(arm, "chest", "tail")),
        "fist": {s: Vector(A.bone_world(arm, "hand." + s, "tail")) for s in SIDES},
        "shoulder": {s: Vector(A.bone_world(arm, "upperarm." + s, "head"))
                     for s in SIDES},
        "ankle": {s: Vector(A.bone_world(arm, "foot." + s, "head")) for s in SIDES},
        "toe": {s: Vector(A.bone_world(arm, "toe." + s, "head")) for s in SIDES},
        "knee_deg": {s: _knee_angle(arm, s) for s in SIDES},
        "hip_flex_deg": {s: _hip_flex(arm, s) for s in SIDES},
        "chest_pitch_deg": _pitch(Vector(A.bone_direction(arm, "chest"))),
        "head_pitch_deg": _pitch(Vector(A.bone_direction(arm, "head"))),
        "pelvis_pitch_deg": _pitch(Vector(A.bone_direction(arm, "pelvis"))),
    }


ZERO_FIST = {}


def main():
    global ZERO_FIST
    arm, meshes = boot()

    JS._PREV_EULER.clear()
    UE.CARRY_Q.clear()
    LOCK_POSE.clear()
    _LOCK_REUSED[0] = 0
    A.apply_pose(arm, ZERO)
    bpy.context.view_layer.update()
    for name in ARM_BONES + LEG_BONES:
        UE.CARRY_Q[name] = arm.pose.bones[name].matrix.to_3x3().to_quaternion()
    for name, value in ZERO.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)
    ZERO_FIST = {s: Vector(A.bone_world(arm, "hand." + s, "tail")) for s in SIDES}

    # ---- ★ 临时几何诊断（`D18_GEOMDBG=1`）：逐帧真值 ------------------------
    if os.environ.get("D18_GEOMDBG"):
        for f in range(0, OUT_TOTAL + 1):
            A.apply_pose(arm, solve_pose(arm, WARP_SRC(f), meshes))
            bpy.context.view_layer.update()
            row = {"f": f}
            for s in SIDES:
                hip = Vector(A.bone_world(arm, "thigh." + s, "head"))
                tgt = ankle_target(arm, s, WARP_SRC(f))
                ank = Vector(A.bone_world(arm, "foot." + s, "head"))
                sh = Vector(A.bone_world(arm, "upperarm." + s, "head"))
                ft = fist_target(arm, s, WARP_SRC(f))
                row["hip_" + s] = [round(v * 1000.0, 1) for v in hip]
                row["anktgt_" + s] = [round(v * 1000.0, 1) for v in tgt]
                row["ank_" + s] = [round(v * 1000.0, 1) for v in ank]
                row["ankerr_" + s] = round((tgt - ank).length * 1000.0, 1)
                row["sh_" + s] = [round(v * 1000.0, 1) for v in sh]
                row["ftgt_" + s] = [round(v * 1000.0, 1) for v in ft]
                row["ft_" + s] = [round(v * 1000.0, 1) for v in
                                  A.bone_world(arm, "hand." + s, "tail")]
                row["rA_" + s] = round((ft - sh).length / ARM_MAX[s], 3)
                row["dL_" + s] = round((tgt - hip).length * 1000.0, 1)
                row["limL_" + s] = round((A.L_THIGH + A.L_SHIN) * 0.9995
                                         * 1000.0, 1)
                row["rL_" + s] = round(
                    (tgt - hip).length / ((A.L_THIGH + A.L_SHIN) * 0.9995), 3)
                row["shoe_" + s] = round(
                    (_foot_clearance()[s] or 0.0) * 1000.0, 2)
                row["handlow_" + s] = round(_lowest_of(HAND_MESHES[s]) or 0.0, 2)
                row["knee_" + s] = round(_knee_angle(arm, s), 2)
            row["pelvis_z"] = round(
                Vector(A.bone_world(arm, "pelvis", "head")).z * 1000.0, 1)
            row["chest_tail_z"] = round(
                Vector(A.bone_world(arm, "chest", "tail")).z * 1000.0, 1)
            row["clip"] = round(PD.clip_metrics(arm)["clip_max_mm"], 2)
            print("D18_GEOM " + json.dumps(row))
        return

    keyframes = []
    for frame in range(0, TOTAL + 1):
        if frame == TOTAL and END_ZERO:
            pose = {name: (0.0, 0.0, 0.0) for name in ZERO if not name.startswith("@")}
            pose["@loc"] = {"pelvis": A.wloc(0.0, 0.0, 0.0)}
            keyframes.append((frame, pose))
        else:
            keyframes.append((frame, solve_pose(arm, frame, meshes)))

    # ===== ★★★ 时间重参数化（路径保持重采样）=================================
    #   ★★★ 必须**在解算之后**做，不能把浮点源帧喂给 `solve_pose`。原因（本支实测）：
    #   `build_pose` 是**路径相关**的（`UE.CARRY_Q` / `_ROLL_LAST_PHI` / `A.FIST` /
    #   `JS._PREV_EULER` 全是逐帧递推状态）。喂浮点源帧 ⟹ 递推历史变了 ⟹
    #   **同一个源帧解出不同姿态**（实测 src=7 的 `hand_plant_at_plant_mm`
    #   23.03 → 25.74 mm），且 `forearm.L` 在 src≈2.4 处直接跳到 **46.3°/帧**。
    #   ⟹ 正确做法：**先按源帧逐帧解算（与旧行为逐位一致），再对已解姿态做
    #   局部旋转插值**（清单 §10.6 步骤 3 的原话：「不重新解 IK、不动任何世界目标」）。
    #   ★ 位置很关键：必须排在 `ARM_ANCHORS` / `ARM_MIX_TO` **之后** ——
    #     那两个后处理用的是**源帧号**（`HAND_OFF`/`FOOT_SET`/`STAND`），
    #     不能拿输出帧号去索引。

    # ===== ★★★ 臂链通用锚点路径：相邻锚点之间，臂骨欧拉逐分量 / 四元数 slerp 插值 ===
    if ARM_ANCHORS:
        _pose_at = {_f: _p for _f, _p in keyframes}
        for _i in range(len(ARM_ANCHORS) - 1):
            _fa, _fb = ARM_ANCHORS[_i], ARM_ANCHORS[_i + 1]
            _pa, _pb2 = _pose_at.get(_fa), _pose_at.get(_fb)
            if _pa is None or _pb2 is None or _fb <= _fa:
                continue
            for _j in range(_fa + 1, _fb):
                _p = _pose_at.get(_j)
                if _p is None:
                    continue
                _s = _smoothstep(float(_j - _fa) / float(_fb - _fa))
                for _n in ARM_BONES:
                    a = tuple(_pa.get(_n, (0.0, 0.0, 0.0)))
                    b = tuple(_pb2.get(_n, a))
                    if ANCHOR_SLERP and _fb <= ANCHOR_SLERP_UNTIL:
                        _qa = Euler([math.radians(v) for v in a], "XYZ").to_quaternion()
                        _qb = Euler([math.radians(v) for v in b], "XYZ").to_quaternion()
                        if _qa.dot(_qb) < 0.0:
                            _qb = Quaternion((-_qb.w, -_qb.x, -_qb.y, -_qb.z))
                        _p[_n] = tuple(math.degrees(v) for v in
                                       _qa.slerp(_qb, _s).to_euler("XYZ"))
                    else:
                        _bb = tuple(_nearest_equiv(y, x) for x, y in zip(a, b))
                        _p[_n] = tuple(u + (v - u) * _s for u, v in zip(a, _bb))

    if ARM_MIX_TO and not ARM_ANCHORS and 0 < ARM_MIX_TO <= TOTAL:
        _head = None
        for _i, (_f, _p) in enumerate(keyframes):
            if _f == ARM_MIX_TO:
                _head = _p
                _hi = _i
                break
        if _head is not None:
            _seam = keyframes[0][1]
            for _i in range(1, _hi):
                _f, _p = keyframes[_i]
                _u = float(_f) / float(ARM_MIX_TO)
                _s = _smoothstep(_u)
                for _n in ARM_BONES:
                    a = tuple(_seam.get(_n, (0.0, 0.0, 0.0)))
                    b = tuple(_head.get(_n, a))
                    bb = tuple(_nearest_equiv(y, x) for x, y in zip(a, b))
                    _p[_n] = tuple(u + (v - u) * _s for u, v in zip(a, bb))
                keyframes[_i] = (_f, _p)

    # ===== ★★★ 时间重参数化（路径保持重采样）—— 见上方长注释 ==================
    if OUT_TOTAL != TOTAL:
        keyframes = resample_keyframes(keyframes)

    # ===== ★ 反验证 ④（`D18_TP_STICKYHAND`）：手不离地 ======================
    #   在 `HAND_OFF` 处把姿态**多按住** `STICKY_OFF_EXT` 帧 ⟹ 那些帧手仍在地面 ⟹
    #   `hand_off_ok` 的 `off` 侧必有违反。纯输出帧空间，**不动相位边界**。
    if STICKY_HAND:
        keyframes = hold_keyframes(keyframes, _OUT_PHASES[3], STICKY_OFF_EXT)

    # ===== ★★ 欧拉表示归一（只换写法、**不改世界旋转**）=====================
    def _nearest_branch(value, ref):
        """在所有等价 XYZ 欧拉写法里，取「逐分量离 `ref` 最近」的那支（度）。"""
        m = Euler([math.radians(v) for v in value], "XYZ").to_matrix()
        best, best_cost = None, None
        for cand in UE._xyz_candidates(m):
            val = [math.degrees(t) for t in cand]
            for index in range(3):
                while val[index] - ref[index] > 180.0:
                    val[index] -= 360.0
                while val[index] - ref[index] < -180.0:
                    val[index] += 360.0
            cost = max(abs(a - b) for a, b in zip(val, ref))
            if best_cost is None or cost < best_cost:
                best, best_cost = tuple(val), cost
        return best

    _prev_rep = {}
    _normalised = []
    if not _env_b("D18_NORM_OFF"):
        for _f, _pose in keyframes:
            _new = dict(_pose)
            for _name in _pose:
                if _name.startswith("@"):
                    continue
                _ref = _prev_rep.get(_name)
                if _ref is None:
                    _prev_rep[_name] = tuple(_pose[_name])
                    continue
                _best = _nearest_branch(_pose[_name], _ref)
                _new[_name] = _best
                _prev_rep[_name] = _best
            _normalised.append((_f, _new))
        keyframes = _normalised

    # ---- ★ 临时"最大步长"诊断（`D18_STEPDBG=1`）-----------------------------
    #   归一化**之后**逐帧算裸欧拉最大分量步长，按降序打印；用来定位
    #   `no_teleport` 的**全部**超限点，而不是只看全局最大值那一个。
    if os.environ.get("D18_STEPDBG"):
        _thr = _env_f("D18_STEPDBG_THR", 20.0)
        _rows = []
        for _i in range(1, len(keyframes)):
            _f0, _pa = keyframes[_i - 1]
            _f1_, _pb = keyframes[_i]
            for _n in sorted(set(_pa) | set(_pb)):
                if _n.startswith("@"):
                    continue
                _a = tuple(_pa.get(_n, (0.0, 0.0, 0.0)))
                _b = tuple(_pb.get(_n, (0.0, 0.0, 0.0)))
                _st = max(abs(x - y) for x, y in zip(_a, _b))
                if _st > _thr:
                    _rows.append((round(_st, 3), _f0, _f1_, _n,
                                  [round(v, 1) for v in _a],
                                  [round(v, 1) for v in _b]))
        _rows.sort(reverse=True)
        print("D18_STEP_ALL " + json.dumps(_rows[:40], ensure_ascii=False))

    # ---- ★ 临时欧拉诊断（`D18_EULERDBG=1`）---------------------------------
    if os.environ.get("D18_EULERDBG"):
        from mathutils import Quaternion as _Q
        _names = [n for n in os.environ.get(
            "D18_EULERDBG_NAMES", "shin.R,forearm.R").split(",") if n]
        _f0 = _env_i("D18_EULERDBG_F0", 28)
        _f1 = _env_i("D18_EULERDBG_F1", OUT_TOTAL)
        _prev_e = {}
        for _f, _p in keyframes:
            if _f0 <= _f <= _f1:
                A.apply_pose(arm, _p)
                bpy.context.view_layer.update()
                _row = {"f": _f}
                for _n in _names:
                    _pb = arm.pose.bones[_n]
                    _wq = _pb.matrix.to_3x3().to_quaternion().normalized()
                    _last = _prev_e.get((_n, "eul"))
                    _e = [round(v, 2) for v in _p.get(_n, (0, 0, 0))]
                    _step = (None if _last is None else
                             round(max(abs(a - b) for a, b in zip(_e, _last)), 2))
                    _dir = A.bone_direction(arm, _n)
                    _row[_n.replace(".", "")] = {
                        "eul": _e, "step": _step,
                        "angZ": round(math.degrees(math.acos(max(
                            -1.0, min(1.0, _dir.dot(ZERO_DIR.get(_n, _dir)))))), 2),
                        "angE": round(math.degrees(math.acos(max(
                            -1.0, min(1.0, _dir.dot(END_DIR.get(_n, _dir)))))), 2),
                        "wdir": (None if not os.environ.get("D18_EULERDBG_DIR")
                                 else [round(v, 3) for v in _dir]),
                        "phi": _ROLL_LAST_PHI.get(_n),
                        "mix": round(roll_mix_at(_f, _n), 4),
                    }
                    _prev_e[(_n, "eul")] = _e
                    _prev_w = _prev_e.get((_n, "w"))
                    _dl = (None if _prev_w is None else round(math.degrees(
                        _wq.rotation_difference(_prev_w).angle), 2))
                    _row[_n.replace(".", "")]["dw"] = _dl
                    _prev_e[(_n, "w")] = _wq
                print("D18_EUL " + json.dumps(_row))
        return

    # ---- ★ 输出帧空间的相位（元数据 / 帧标记 / 出图帧号一律用它）------------
    (O_LEGS_DOWN, O_PLANT, O_CHEST_UP, O_HAND_OFF, O_TUCK, O_FOOT_SET,
     O_RISE_MID, O_STAND, O_TOTAL, O_END) = _OUT_PHASES

    meta = {
        "anim_id": NAME,
        "loop": False,
        "category": "防御与受击",
        "note": ("背面起身（仰卧 → 双掌在身侧/身后撑地推起 → 收腿 → 战斗站姿）："
                 "竖直通道**无弹道段**，骨盆**单调升 702 mm**；支点**背/臀 → 掌 → 脚**"
                 "换两次；末帧**逐位 = `Idle_01@0`**（跨族接缝）；"
                 "★ 时间轴经**路径保持重采样**（源 %d 帧 → 输出 %d 帧）"
                 % (TOTAL, OUT_TOTAL)),
        "antic_frame": O_LEGS_DOWN,
        "hit_frame": None,
        "land_frame": O_FOOT_SET,
        "cancel_frame": O_STAND,
        "legs_down_frame": O_LEGS_DOWN,
        "plant_frame": O_PLANT,
        "chest_up_frame": O_CHEST_UP,
        "hand_off_frame": O_HAND_OFF,
        "tuck_frame": O_TUCK,
        "foot_set_frame": O_FOOT_SET,
        "rise_mid_frame": O_RISE_MID,
        "stand_frame": O_STAND,
        "self_hold_frame": O_STAND,
        "warp_src_total": TOTAL,
        "warp_out_total": OUT_TOTAL,
        "hitstop_frames": 0,
        "hit_points": 0,
        "root_motion_m": [0.0, round(pelvis_y_at(END) - pelvis_y_at(START), 6)],
        "hit_point_m": None,
        "end_pelvis_z_m": round(pelvis_z_at(END), 6),
        "end_vz_m_per_frame": 0.0,
        "start_pose_ref": "%s 帧 %d（仰卧，脸朝上）" % (SEAM_ACTION, SEAM_FRAME),
        "end_pose_ref": "%s 帧 %d（战斗站姿）" % (END_ACTION, END_FRAME),
        "ballistic_ref": "无（★ 本支竖直通道不含弹道段）",
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.add_markers(action, {"START": START, "LEGS_DOWN": O_LEGS_DOWN, "PLANT": O_PLANT,
                           "CHEST_UP": O_CHEST_UP, "HAND_OFF": O_HAND_OFF,
                           "TUCK": O_TUCK,
                           "FOOT_SET": O_FOOT_SET, "RISE_MID": O_RISE_MID,
                           "STAND": O_STAND, "SELF_HOLD": O_STAND,
                           "CANCEL": O_STAND, "END": OUT_TOTAL})

    samples = A.sample_animation(arm, action, 0, OUT_TOTAL, meshes)
    report = A.run_common_assertions(samples, meta, foot_probe=())
    report.pop("ground_contact_ok", None)
    report.pop("ground_min_mm", None)

    end_mats_ref = CR.action_world_matrices(arm, bpy.data.actions[END_ACTION],
                                            END_FRAME)
    report.update(getup_assertions(arm, action, samples, meshes, end_mats_ref))
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

    report["failed"] = sorted(k for k, v in report.items()
                              if k.endswith("_ok") and v is not True)
    report["non_ok_bools"] = sorted(
        k for k, v in report.items()
        if isinstance(v, bool) and not k.endswith("_ok") and v is not True)
    A.report("D18_REPORT", report)

    if not SKIP_RENDER:
        side_frames = list(range(0, OUT_TOTAL + 1))
        other_frames = [START, O_LEGS_DOWN, O_PLANT, O_CHEST_UP, O_HAND_OFF, O_TUCK,
                        O_FOOT_SET, O_RISE_MID, O_STAND, O_END]
        A.render_pose_sheet(arm, action, side_frames, "getupb",
                            views=(VIEW_D18_SIDE,))
        A.render_pose_sheet(arm, action, side_frames, "getupbwide",
                            views=(VIEW_D18_SIDE_WIDE,))
        A.render_pose_sheet(arm, action, other_frames, "getupb",
                            views=(VIEW_D18_FRONT, VIEW_D18_3Q))
        # ★ `px_idle_end_ok` 的**对照静帧**：与 D18 wide 视**同机位**重渲一份
        idle_action = bpy.data.actions[END_ACTION]
        A.render_pose_sheet(arm, idle_action, [END_FRAME], "idle01wideb",
                            views=(VIEW_D18_SIDE_WIDE,))
        A.save_project()
        A.export_glb(arm)
    print("D18_DONE failed=%s" % report["failed"])
    print("D18_DONE non_ok_bools=%s" % report["non_ok_bools"])
    if os.environ.get("D18_TRACE"):
        print("D18_TRACE " + json.dumps(report.get("trace", {}),
                                        ensure_ascii=False))


# ★ 本支取景。
#   ★★ `VIEW_D18_SIDE_WIDE` 是**起身族第二套基准**：D18 从 y = **+470** 走到 0，
#      水平中点 = **+235 mm** ⟹ 机位中心取 **+250 mm**（**不许照抄 D17 的 −300**，
#      否则起点 y = +470 会被切出画面）。正交宽 3.60 m 覆盖"仰卧的纵向跨度
#      （含抬起的脚 z 391 mm）+ 站起来的高度（1.85 m）"。跨支尺子只比**行**、不比列。
VIEW_D18_SIDE = ("side", (5.20, 0.235, 1.30), (0.0, 0.235, 1.30), 3.30,
                 (780, 1100))
VIEW_D18_SIDE_WIDE = ("side", (5.20, 0.250, 0.95), (0.0, 0.250, 0.95), 3.60,
                      (780, 1100))
VIEW_D18_FRONT = ("front", (0.0, -5.60, 0.95), (0.0, 0.250, 0.95), 4.20,
                  (780, 1100))
VIEW_D18_3Q = ("three_quarter", (4.10, -4.30, 1.15), (0.0, 0.250, 0.95), 4.60,
               (780, 1100))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("D18_FAILURE " + traceback.format_exc())
