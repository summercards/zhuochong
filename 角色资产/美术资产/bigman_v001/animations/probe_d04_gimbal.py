"""D04 破防 —— 只读数值探针：**绕骨轴滚转**在零位欧拉上到底是"表示跳变"还是"真跳"。

背景（本支第 2 次收尾实测）：
    `end_roll_deg` 修正打开后，`upperarm.L` 的单帧欧拉步长冲到 **76.85°**，
    而同帧**世界朝向只走 12.84°**（`arm_world_step_trace` 实测）⟹ 纯表示跳变。
    假设：零位欧拉 `upperarm.L ry = −94.4543°`（D01 定格真值）越过了 XYZ 万向节锁
    |ry| = 90°，所以在该骨上"绕自身轴拧 δ"会让 (rx, rz) 拆分剧烈摆动。

本探针**不用 Blender**，纯解析验证这个假设：
    ① 用零位欧拉建 M = Rz(rz)·Ry(ry)·Rx(rx)（Blender XYZ 约定）；
    ② 绕**骨自身轴**滚转 = 右乘 Ry(δ)（见 `_roll_return()` 的推导）⟹ M' = M·Ry(δ)；
    ③ 解 M' 的两支等价欧拉，取离零位最近的一支，量 max|Δ分量|；
    ④ 同时量**世界朝向**的真实变化（= δ，绕骨轴滚转不改骨轴方向）；
    ⑤ 对照 `forearm.L`（和乐主承载骨）与一个"安全"骨（`hand.L`，ry 远离锁）。

判据：
    若 `euler_step_max` ≫ `world_step`（世界步长恒 = δ），则该骨的欧拉表示在锁带内
    **病态**，对它做滚转修正 = 改一个不需要改的量、换来一个假闪帧 ⟹ 应当排除。

用法： python probe_d04_gimbal.py
"""

import math

# ---- 零位真值：D01_REPORT.end_euler_ref（D01 定格，勿重跑 D01）--------------------
ZERO_EULER = {
    "upperarm.L": (-11.0915, -94.4543, -98.4231),
    "upperarm.R": (-23.6061, 92.1385, 85.8904),
    "forearm.L": (8.4272, 13.3886, -140.1672),
    "forearm.R": (9.7189, 5.5987, 143.389),
    "hand.L": (-0.0, -1.7942, 0.0),
    "hand.R": (0.0, 7.7368, 0.0),
}
# 本支第 2 次收尾实测：末帧滚转漂移（修正关闭时）落在 forearm 上，打开修正后
# 残到 upperarm（因为远端被拉正后，和乐**搬**到了近端）。
DEG = math.pi / 180.0


def rx(a):
    c, s = math.cos(a), math.sin(a)
    return ((1.0, 0.0, 0.0), (0.0, c, -s), (0.0, s, c))


def ry(a):
    c, s = math.cos(a), math.sin(a)
    return ((c, 0.0, s), (0.0, 1.0, 0.0), (-s, 0.0, c))


def rz(a):
    c, s = math.cos(a), math.sin(a)
    return ((c, -s, 0.0), (s, c, 0.0), (0.0, 0.0, 1.0))


def mul(a, b):
    return tuple(tuple(sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3))
                 for i in range(3))


def euler_to_m(deg):
    return mul(rz(deg[2] * DEG), mul(ry(deg[1] * DEG), rx(deg[0] * DEG)))


def m_to_candidates(m):
    """`UE._xyz_candidates` 的逐行复刻（弧度）。|Y|→90° 时分拆任意，故必须两支。"""
    y = math.asin(max(-1.0, min(1.0, -m[2][0])))
    cy = math.cos(y)
    if abs(cy) > 1e-6:
        x = math.atan2(m[2][1], m[2][2])
        z = math.atan2(m[1][0], m[0][0])
    else:                                        # 万向节锁：x 归零、z 吸收全部
        x = 0.0
        z = math.atan2(-m[0][1], m[1][1])
    return ((x, y, z), (x + math.pi, math.pi - y, z + math.pi))


def nearest_euler_deg(m, prev_deg):
    """解两支 + ±360k，取 max|Δ分量| 最小的那支（= `JS._unwrap_xyz` 的语义）。"""
    best, best_cost = None, None
    for cand in m_to_candidates(m):
        base = [math.degrees(t) for t in cand]
        for kx in (-1, 0, 1):
            for ky in (-1, 0, 1):
                for kz in (-1, 0, 1):
                    v = (base[0] + 360.0 * kx,
                         base[1] + 360.0 * ky,
                         base[2] + 360.0 * kz)
                    cost = max(abs(v[i] - prev_deg[i]) for i in range(3))
                    if best_cost is None or cost < best_cost:
                        best, best_cost = v, cost
    return best, best_cost


def main():
    print("=" * 78)
    print("D04 万向节锁探针 —— 绕骨轴滚转 δ 的**欧拉**步长 vs **世界朝向**步长")
    print("=" * 78)
    print("%-12s %6s %10s %12s %14s" % ("bone", "ry(°)", "δ(°)", "euler_step", "world_step"))
    print("-" * 78)
    verdicts = {}
    for name, e0 in ZERO_EULER.items():
        m0 = euler_to_m(e0)
        worst = 0.0
        for delta in (1.0, 2.0, 5.0, 10.0, 18.0, 25.0, 30.0):
            m1 = mul(m0, ry(delta * DEG))         # ★ 绕骨自身轴 = 右乘 Ry
            _, cost = nearest_euler_deg(m1, e0)
            worst = max(worst, cost)
            print("%-12s %8.4f %10.1f %12.2f %14.2f"
                  % (name, e0[1], delta, cost, delta))
        verdicts[name] = worst
        print("-" * 78)

    print("\n汇总（δ=30° 时的欧拉步长 / 世界步长 = 放大倍数）：")
    for name, worst in sorted(verdicts.items(), key=lambda kv: -kv[1]):
        ratio = worst / 30.0
        flag = "★ 锁带病态" if ratio > 1.5 else ""
        print("    %-12s ry=%9.4f°  欧拉 %8.2f°  → 放大 %5.2fx  %s"
              % (name, ZERO_EULER[name][1], worst, ratio, flag))
    print("\n结论口径：`no_teleport` 量的是**欧拉分量步长**。若放大倍数 ≫ 1，"
          "则该骨的滚转修正是'假闪帧'的来源，应排除（`ROLL_BONES` 白名单）。")


if __name__ == "__main__":
    main()
