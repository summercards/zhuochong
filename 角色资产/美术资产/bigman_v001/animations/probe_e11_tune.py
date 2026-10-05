"""probe_e11_tune.py —— E11 第三版参数标定器（真机、纯只读、不渲染）。

★★★ 为什么要有它（v3 门禁四红的根因，实测钉死）：
    v3 报告：
      `rvw_body_low_min_mm = -65.02`（凶手全程 `Shoe_Sole_R`）
      `rvw_knee_min_mm     =  95.50 @f68`（判据 ≥ 104.7 − 4 = 100.7 ⟹ 红）
      `rvw_limb_step_max   = 221.42 @[64,'knee.R']`
      `no_teleport`         `max_frame_step = 101.7° @[64,'foot.R']`
    两条根因：
      ① **右踝 z 目标太低**。右鞋鞋底到踝的深度由**脚的世界俯仰**决定，实测
         fp=44° 时深 **194 mm**，而 v3 把踝放在 **132 mm** ⟹ 鞋底压穿地 60+ mm。
      ② **右膝目标在「固定踝」上不可达**。`_pole_for_knee_z` 只在**给定踝**上
         比两支：实测 f44 两支 = **+471 / −149**、f58 = **+455 / −34**，
         而目标是 160 / 120 —— 于是规则 ② 强制取自然支，膝被顶到 455 mm；
         随后 f60→f61 目标忽然落进可达区 ⟹ **单帧翻支 286 mm**（= 那条 teleport）。

★★★ 本脚本做的事（把「不可达」变成「设计出来的可达」）：
    不再把踝 y 当自由手调参数，而是**反过来解**：
      · 踝 z ← **实测鞋底深度** + 目标离地量（鞋底不再穿地）
      · 踝 y ← **膝高目标的一维搜索**（让 `_pole_for_knee_z` 的两支真的夹住目标）
    输出可直接粘进 `anim_revive.py` 的 `ANKLE_KEYS["R"]` / `KNEE_Z_R`，
    并附「每帧可达膝高区间」，用来判断某个目标是否**天生不可能**。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python probe_e11_tune.py
"""

import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A          # noqa: E402
import anim_death as D        # noqa: E402
import anim_revive as RV      # noqa: E402

SIDES = ("L", "R")

# 右膝**期望高度**（mm）—— 本表就是「设计意图」，其余全部由它反解出来。
#   f0~f16  仰卧：膝贴地（膝网格半径 104.7 ⟹ 140.5 与 `Death@120` 一致）
#   f16~f52 收腿：膝抬起来（腿折进来，膝朝胸前）
#   f52~f80 半跪：膝落回地面（108 = 膝半径 + 3.3 mm，留 7 mm 门禁余量）
#   f80~f104 站起：膝随身体升起，f104 收敛到 `Idle_01` 实测站姿膝高
KNEE_WANT = (
    (0, 140.5), (16, 140.5), (24, 152.0), (30, 168.0), (38, 142.0),
    (44, 126.0), (52, 112.0), (60, 108.0), (68, 108.0), (72, 108.0),
    (76, 108.0), (84, 132.0), (92, 232.0), (100, 342.0), (104, 428.4),
    (120, 428.4),
)
# 右鞋鞋底**离地目标**（mm）—— 半跪段鞋底贴地；收腿段抬起来（腿在空中）
SOLE_WANT = (
    (0, 0.0), (16, 0.0), (30, 20.0), (44, 10.0), (52, 4.0), (60, 2.0),
    (76, 2.0), (92, 2.0), (104, 0.0), (120, 0.0),
)
# 已经定死的踝 y（不参与搜索的帧：起点贴 `Death@120`、终点贴 `Idle_01@0`）
KEY_FRAMES = (16, 24, 30, 38, 44, 52, 60, 68, 76, 84, 92, 100)

arm, meshes = RV.boot()


def _pwl_simple(keys, frame):
    if frame <= keys[0][0]:
        return keys[0][1]
    if frame >= keys[-1][0]:
        return keys[-1][1]
    for i in range(len(keys) - 1):
        f0, v0 = keys[i]
        f1, v1 = keys[i + 1]
        if f0 <= frame <= f1:
            if f1 == f0:
                return v1
            t = (frame - f0) / float(f1 - f0)
            return v0 + (v1 - v0) * t
    return keys[-1][1]


def body_pose(frame):
    """只装骨盆 + 躯干（腿不参与），取出髋/骨盆世界坐标。

    ★ 腿的姿态**不影响**髋（thigh 的 head 只由 pelvis 链决定）⟹ 可以单独取。
    """
    f = frame
    if not RV.NO_PLATEAU and RV.TUCK_END <= f <= RV.HK_END:
        f = RV.TUCK_END
    py, pz, prx = RV._pwl(RV.PELVIS_KEYS, f)
    pose = {"pelvis": (prx, 0.0, 0.0)}
    for bone in ("spine_01", "spine_02", "chest", "neck"):
        pose[bone] = (RV._pwl(RV.TORSO_KEYS[bone], f), 0.0, 0.0)
    pose["head"] = (RV._pwl(RV.TORSO_KEYS["head_rx"], f),
                    RV._pwl(RV.TORSO_KEYS["head_ry"], f), 0.0)
    sh = RV._pwl(RV.TORSO_KEYS["shoulder"], f)
    pose["shoulder.L"] = (sh, 0.0, 0.0)
    pose["shoulder.R"] = (sh, 0.0, 0.0)
    pose["@loc"] = {"pelvis": A.wloc(0.0, py, pz - 0.900)}
    pose["root"] = (0.0, 0.0, 0.0)
    A.apply_pose(arm, pose)
    return {"pelvis": Vector(A.bone_world(arm, "pelvis")),
            "L": Vector(A.bone_world(arm, "thigh.L", "head")),
            "R": Vector(A.bone_world(arm, "thigh.R", "head"))}


def sole_depth(side, fp_deg, roll_deg):
    """鞋底最低点到踝的世界距离（mm，正 = 鞋底在踝**下方**）。

    ★ 由 `keep_foot_orient` 把脚的世界朝向钉死 ⟹ 这个量**与腿的姿态无关**，
      只随 (fp, roll) 变（见 `probe_e11_foot.py` 的网格实测）。
    """
    pose = dict(RV.TERM)
    pose["foot." + side] = D.keep_foot_orient(arm, "foot." + side,
                                              fp_deg, roll_deg)
    A.apply_pose(arm, pose)
    ank = Vector(A.bone_world(arm, "foot." + side))
    objs = [bpy.data.objects[n] for n in A.FOOT_MESHES[side]
            if n in bpy.data.objects]
    low = A.lowest_point_of(objs)
    return (ank.z - low[2]) * 1000.0


def fp_roll_at(frame, side):
    roll = RV._pwl(RV.ROLL_KEYS, frame)
    if side == "L":
        return RV._pwl(RV.FP_KEYS, frame), roll
    return RV._pwl(RV.R_FP_KEYS, frame), -roll


def both_branches(hip, tgt):
    """在**给定踝**上，两个膝分支的世界 z（mm）。返回 (z_plus, z_minus)。"""
    hip = Vector(hip)
    d = Vector(tgt) - hip
    dist = d.length
    limit = (L1 + L2) * D.REACH_MAX_RATIO
    dist = max(min(dist, limit), abs(L1 - L2) + 1e-4)
    if d.length < 1e-9:
        return None
    u = d.normalized()
    a = (L1 * L1 - L2 * L2 + dist * dist) / (2.0 * dist)
    h = math.sqrt(max(0.0, L1 * L1 - a * a))
    s = math.hypot(u.y, u.z)
    if s < 1e-6:
        return None
    base = Vector((0.0, u.z, -u.y)) / s
    kz = (hip + u * a).z
    return ((kz + base.z * h) * 1000.0, (kz - base.z * h) * 1000.0)


def solve_ankle(hip, ax, fp, roll, want_mm, sole_mm, y_lo=-0.45, y_hi=0.85):
    """给定踝 x / 脚朝向 / 膝高目标 / 鞋底离地目标 ⟹ 解出 (ay, az)。

    · `az` 由鞋底目标唯一确定（鞋底深度是实测的，不是估的）
    · `ay` 一维扫描，取「两支膝高**夹住**目标」且误差最小的那个
    返回 dict：az / ay / knee / err / 该 az 上可达的膝高区间。
    """
    depth = sole_depth("R", fp, roll)
    az = (sole_mm + depth) / 1000.0
    best = None
    lo, hi = 1e9, -1e9
    for step in range(int((y_hi - y_lo) * 500) + 1):
        ay = y_lo + step / 500.0
        zs = both_branches(hip, Vector((ax, ay, az)))
        if zs is None:
            continue
        lo = min(lo, zs[0], zs[1])
        hi = max(hi, zs[0], zs[1])
        for branch, kz in ((1.0, zs[0]), (-1.0, zs[1])):
            err = abs(kz - want_mm)
            if best is None or err < best[0]:
                best = (err, ay, kz, branch)
    if best is None:
        return None
    return {"az": az, "ay": best[1], "knee": best[2], "err": best[0],
            "branch": best[3], "depth": depth, "lo": lo, "hi": hi}


L1, L2 = D.L1, D.L2

print("# ================= E11T_BODY 髋/骨盆世界坐标 =================")
for f in range(0, RV.END + 1, 2):
    bp = body_pose(f)
    print("E11T_BODY f=%3d pelvis=(%+.3f,%+.3f,%+.3f) hipL=(%+.3f,%+.3f,"
          "%+.3f) hipR=(%+.3f,%+.3f,%+.3f)"
          % (f, bp["pelvis"].x, bp["pelvis"].y, bp["pelvis"].z,
             bp["L"].x, bp["L"].y, bp["L"].z,
             bp["R"].x, bp["R"].y, bp["R"].z))

print("# ================= E11T_NOW 现状逐帧 =================")
for f in range(0, RV.END + 1, 2):
    bp = body_pose(f)
    line = "E11T_NOW f=%3d" % f
    for side in SIDES:
        fp, roll = fp_roll_at(f, side)
        depth = sole_depth(side, fp, roll)
        tgt = RV._ankle_target(f, side)
        zs = both_branches(bp[side], tgt)
        line += (" | %s fp=%+6.1f roll=%+6.1f depth=%6.1f ank=(%+.3f,%+.3f,"
                 "%+.3f) sole=%+7.2f knee+=" % (side, fp, roll, depth,
                                                tgt.x, tgt.y, tgt.z,
                                                (tgt.z - depth / 1000.0) * 1000.0))
        line += ("%7.1f" % zs[0]) if zs else "  n/a "
    print(line)

print("# ================= E11T_SOLVE 反解（踝 y 扫出膝目标）=========")
SOLVED = {}
for f in KEY_FRAMES:
    bp = body_pose(f)
    fp, roll = fp_roll_at(f, "R")
    want = _pwl_simple(KNEE_WANT, f)
    sole = _pwl_simple(SOLE_WANT, f)
    ax = RV._pwl(RV.ANKLE_KEYS["R"], f)[0] if False else None
    # 踝 x 沿用旧表（站位宽度），只解 y / z
    old = RV._ankle_target(f, "R")
    res = solve_ankle(bp["R"], old.x, fp, roll, want, sole)
    if res is None:
        print("E11T_SOLVE f=%3d 解不出来" % f)
        continue
    SOLVED[f] = res
    print("E11T_SOLVE f=%3d want=%6.1f sole=%5.1f depth=%6.1f az=%+.4f "
          "ay=%+.4f -> knee=%7.1f err=%5.1f br=%+.0f 可达区间=[%7.1f, %7.1f]"
          % (f, want, sole, res["depth"], res["az"], res["ay"], res["knee"],
             res["err"], res["branch"], res["lo"], res["hi"]))

print("# ================= E11T_KEY 可直接粘的键 =================")
items = sorted(SOLVED.items())
print("ANKLE_KEYS_R = (")
print('    (0, "TERM"), (16, "TERM"),')
for f, res in items:
    if f in (104, 120):
        continue
    print("    (%d, (%.3f, %+.4f, %.4f))," % (f, RV._ankle_target(f, "R").x,
                                              res["ay"], res["az"]))
print('    (104, "REST"), (120, "REST"),')
print(")")
print("KNEE_Z_R = (")
print("    (0, 0.1405), (16, 0.1405),")
for f in sorted(set([k[0] for k in KNEE_WANT])):
    print("    (%d, %.4f)," % (f, _pwl_simple(KNEE_WANT, f) / 1000.0))
print(")")

print("# ================= E11T_CHK 连续性（膝/踝单帧步长）=========")
prev = None
worst = (0.0, None)
for f in range(0, RV.END + 1):
    bp = body_pose(f)
    fp, roll = fp_roll_at(f, "R")
    depth = sole_depth("R", fp, roll)
    want = _pwl_simple(KNEE_WANT, f)
    sole = _pwl_simple(SOLE_WANT, f)
    old = RV._ankle_target(f, "R")
    res = solve_ankle(bp["R"], old.x, fp, roll, want, sole)
    if res is None:
        continue
    cur = (Vector((old.x, res["ay"], res["az"])), res["knee"])
    if prev is not None:
        da = (cur[0] - prev[0]).length * 1000.0
        dk = abs(cur[1] - prev[1])
        if da > worst[0]:
            worst = (da, ("ankle", f, da, dk))
    prev = cur
print("E11T_CHK worst_ankle_step_mm=%s" % (worst,))
