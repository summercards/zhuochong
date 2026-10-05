# -*- coding: utf-8 -*-
"""把 E01 完成记录追加到 .workbuddy/memory/2026-10-03.md（一次性脚本）。"""
import io
import os

DOC = r"I:\工作项目\BIGMANFIGHT\.workbuddy\memory\2026-10-03.md"

TEXT = u"""

---

# 2026-10-03（第三轮）—— E01 `Stun` 眩晕 ✅ 已完成（57/67，五 1）

> 格斗动画生产链第 57 支。**E 族（状态与流程）第一支**。
> 清单原文：「身体摇晃但**脚尽量保持原位**，方便判定」。
> 链路的接棒方式：`animations/anim_stun.py` + `probe_e01_baseline.py` + `probe_e01_pixels.py`。

## 做了什么

1. **开工第一件测量** `probe_e01_baseline.py`（新建，照 `probe_d19_baseline.py` 结构）。
2. **制作** `anim_stun.py`：120 帧 / 2.0 s / 2 个摇晃周期 / 循环。
3. **门禁** `failed=[]`、`non_ok_bools=[]`（`_e01_final.log`）。
4. **反向验证 7 组**，每组都真的见红。
5. **出图**：`stunwide_front_*` 121 张（探针用）/ `stun_*` 61 张 / `stunkey_*` 21 张 /
   反面对照 `stunfootsway_front_*` + `stunnosway_front_*` 各 121 张。
6. **mp4** 三视角：`Stun_side.mp4` / `Stun_front.mp4` / `Stun_three_quarter.mp4`。
7. **GLB** `animations=58`，`Stun`（通道 171 / 骨骼 57 / 2.000 s）。
8. **像素探针** `probe_e01_pixels.py`（新建）：7 项全绿、3 对真实正/反对照。
9. **三重目检** 逐帧看过，反例全部排除。

## ★★★ 本支的两件工程（全项目首次）

**(1)「消失于接缝」的周期函数**。首帧必须**完全等于** `Idle_01@0`（不许有一丝摇晃），
末帧又必须**逐位复现**首帧 —— 两个约束天然打架。解法是每个通道都用

```
v(φ) = A · w · [ sin(φ + ψ − δ) − sin(ψ − δ) ]
```

`f=0` 与 `f=N` 上 **v ≡ 0**（不是「看起来一样」，是恒等于 0）。
实测 `seam_in_pos_max = 0.000258 mm`、`end_matches_start_elem_max = 9.7e-17`。

**(2) 脚锁 = 闭环数值修正，不是解析 IK**。实测躯干每倾 1° 踝漂 **2.13 mm**，
大头来自骨盆 rz（`0.75 m × sinθ ≈ 13.09 mm/°`），而 `A.leg_ik` 是**平面 YZ 解**、
**没有通道管 rz** ⟹ x 通道必须另配一条：误差反馈成 `thigh.rz` 反向配平
（灵敏度 `1/0.01309` °/m）。迭代 6 轮，实测踝漂 **0.0036 mm**。

## 关键数字（全部来自门禁实测）

- 踝漂 **L 0.0036 / R 0.0024 mm**（阈值 0.5）⟹ `stun_foot_lock_ok`
- 头横行程 **237.953 mm** / 前后 **130.869 mm**；过零 **4** / 周期 **60.667 帧**
- 骨盆 z 波动 **7.0 mm**；鞋底 z ∈ [−1.082, +1.062] mm；鞋底起伏 L 0.143 / R 0.138 mm
- `loop_seamless=true`（角 0.0° / 位移 0.0 mm）
- `chain_travel`：脚 **0.0036 mm** / 膝 5.03° / 髋 8.08 mm / 腰 3.60° / 肩 60.08 mm / 手 69.45 mm
- `max_frame_step_deg = 0.314` / `no_snap_stop = 0.3033` / `clip_max = 0.0` / `leg_reach = 0.94289`

## ★★★ 四处实测修正（没有一处是靠放宽判据）

| # | 现象 | 根因 | 修法 |
|---|---|---|---|
| ① | `stun_toe_drift = 128.86 mm` | 把 `toe.*` 拿去和**踝锚点**比 —— 那 128 mm 是**脚掌本身的长度** | 每类量取**自己的首帧值**作基准 |
| ② | `end_matches_start_dir_deg = 0.0312°` | float32 精度被 `acos` 放大成 `sqrt(2ε)` | 改**逐元素 4×4 矩阵比对**（阈值 1e-6） |
| ③ | `E01_TP_SEAM_ZERO` 抛 `KeyError: 'thigh.L'` | `BASE={}` 时 `pose` 里没有 `thigh.*` | 改 `.get(..., (0,0,0))` |
| ④ | ★★ **`save_project` / `export_glb` 写在 `SKIP_RENDER` 守卫之外** | 跑任何一组 TP 都会把**畸形动画写进正式 `.blend` / `.glb`** | 挪进守卫；并让 `E01_STEM_ONLY=1` 也一并拦住基线图 |

★ ④ 是 D19 记过的同一类坑，**本支又踩了一次** —— 已写进代码注释。

## 反向验证 7 组（全部见红）

① `SEAM_ZERO` → `seam_in_ok` / `leg_reach_ok`
② ★★★ `FOOTSWAY` → **`stun_foot_lock_ok`** / `sole_ground_ok` / `ground_contact_ok` /
`ground_hold_ok` / `chain_present_ok` / `no_foot_slide_toe.L/.R`
③ `NOSWAY` → `stun_sway_amp_ok` / `stun_sway_period_ok` / `stun_sway_side_amp_ok`
④ `ONESHOT` → `stun_sway_period_ok`
⑤ `LOOPBREAK` → `end_matches_start_ok` / `loop_velocity_ok` / `loop_seamless`
⑥ `SINK` → `stun_height_hold_ok`
⑦ `LIFT` → `sole_ground_ok` / `ground_contact_ok` / `seam_in_ok`

## 像素探针 7 项全绿（`E01PX_DONE failed=[]`）

| 判据 | 实测 |
|---|---|
| `px_stun_foot_lock_ok` | 脚带左右缘漂 **1.0 / 0.0 px**、底缘行漂 **0.0 px** |
| `px_stun_foot_lock_can_fail_ok` | 反面（FOOTSWAY 重渲 121 张）：**76 / 79 / 6 px** ⟹ 红 |
| `px_stun_sway_ok` | 上段列心峰峰值 **36.289 px**、过零 4、周期 60.0 帧 |
| `px_stun_sway_can_fail_ok` | 同尺子换载体（脚带列心）⟹ **0.394 px** ⟹ 红 |
| `px_stun_sway_nosway_can_fail_ok` | 反面（NOSWAY 重渲 121 张）⟹ **0.416 px** ⟹ 红 |
| `px_hem_excluded_ok` | 衣摆 rows 547..565 与脚带 78..129、上段 680..1099 **均不相交**（算得） |
| `px_hem_stripped_ok` | 全剪影列心 raw vs 剔除后偏移 **0.2027 px**（不是空操作） |

## ★★★ 帧预算：登记新上界 = 120 帧 / 2.0 s

- 理由：**循环状态的时长由「看起来像不像眩晕」决定**，不由单次受击的 40 帧上界决定
  （A01 `Idle_01` 已登记 180 帧 / 3.0 s 是同一逻辑先例）。
- `TOTAL = 120` 是**常量、不是 env 覆写** ⟹ 可复现（对照 D18 因「悄悄超到 46 帧且依赖 env」被改判）。
- 实测周期 60.667 帧 ⟹ 120 帧 = 约 1.98 个周期；`CYCLES = 2.0`（整数 ⟹ 闭合）。

## ★★★ 机位从「侧视」换成「正面」（几何必然，不是偏好）

D13~D19 全用**侧视**，因为那些支的位移在 **Y/Z**。本支主运动是 **X**（横 237.953 vs 前后 130.869）。
**侧视沿 −X 看 ⟹ X 向摇摆落在视轴上，完全不可见**。
★ **实测印证**：`stunkey_side_f0015` 与 `f0030` 肉眼几乎无差别，同一对帧在正面是「右倾 / 左倾 13°」。
⟹ 第一次建立 **`VIEW_E01_FRONT_WIDE`**（正面宽视，机位中心 x 0.0 / z 0.90 / ortho 2.10 / 780×1100）。
行列换算：`mm_per_px = 1.9090909`、`floor_row = 78.5714`、`col = 390 + x_mm/1.9090909`。
★ 列的语义变了：**正面 image-right = +X = 角色左手侧**（D19 是「image-right = +Y = 身后」）。

## 三重目检（逐帧看过）

正面（主检）f0 站架 → f15 右倾（鞋逐位不动）→ f30 回中 → f45 左倾 → f60 回中 → f120 逐位回 f0 ✅
侧视 f15/f30 差异极小（**预期**：X 向在侧视不可见）✅
3/4 肩与拳架晃动清晰、腿部稳定 ✅
反例排除：**「整个人左右平移」** ⟹ 见 `stunfootsway_front_f0015`（同机位整体右移，差别一眼可判）；
**「歪向一侧不动」** ⟹ f15 右 / f45 左来回；**「循环处跳变」** ⟹ f120 = f0（`elem_max = 9.7e-17`）。

## 新增 / 修改的文件（E01）

- `animations/anim_stun.py`（新建，主交付物）
- `animations/probe_e01_baseline.py`（新建，开工第一件测量）
- `animations/probe_e01_pixels.py`（新建，像素级，7 项全绿）
- `animations/_run_e01_tp.sh`（**临时**，7 组反向验证跑批）
- `animations/_e01_append_log.py`（**临时**，清单日志追加）
- `doc/动画制作清单.md`（E01 → ✅ 已完成；进度 → 57/67；追加 E01 日志 + **E02 详细计划**）
- `previews/anim/`：`stunwide_front_*`(121) / `stun_*`(61) / `stunkey_*`(21) /
  `stunfootsway_front_*`(121) / `stunnosway_front_*`(121) / `Stun_*.mp4`(3)
- `bigman_anim_v001.blend` / `bigman_anim_v001.glb`（现 58 支动画）

## 遗留问题（留给 E02 或主人决定）

1. **`seam_in_dir_max_deg = 0.031181` 不是姿态差**，是 float32 `acos` 噪声底
   （`acos(1−1.5e-7) ≈ 0.0312°`）。本支已把 `end_matches_start_ok` 改口径为逐元素；
   **前 56 支历史日志的 `dir_deg` 数字未回改**。
2. **`E01_TP_SEAM_ZERO` 下 `leg_reach_ok` 亦红**是副产物（零位下腿是 T-pose 长度），非独立缺陷。
3. ★★ **`Idle_01@0` / `Idle_01@180` / `Hit_Head@0` / `Hit_Head@34` 四者逐位同一姿态**
   （`head.tail` 皆 `(0, −104.06, 1713.26)`、`shape_cost` 全 0.0）⟹ E 族后续各支在
   「从站架起 / 从上一支起」之间**代价完全相等**，**选择依据只能是语义**。E02 直接受益。
4. `_run_e01_tp.sh` / `_e01_append_log.py` 是本轮临时脚本，**未登记为正式工具**。

## 下一支

**E02 `Exhausted` 虚弱** —— 清单原文「**弯腰喘气、双手扶膝**」。
详细计划已写在 `doc/动画制作清单.md` 文末（§0 三条接缝 / §1 四个风险 / §2 两段相位 /
§3 判据换口径表 / §4 十一步执行顺序 + 收尾自查）。
★ 三处与 E01 根本不同：① 横向摇晃 → **纵向呼吸**；② 骨盆高度恒定 → **弯腰必然下降**；
③ ★★★ 手从自由 → **钉在膝盖上**（**动目标追踪 + 自碰撞**，比 E01 的静止踝锚点更难）。
★ 命门判据：`exh_hand_on_knee_ok` + `px_exh_hand_on_knee_ok`，
反面 ② （`E02_TP_HANDFAR=1`）**必须见红**，否则本支不算完成。
★ 帧预算：E01 已登记 **120 帧 / 2.0 s**，E02 若 ≤120 帧可直接沿用（须在日志明说）。

## 进度

**57/67**（一 13 / 二 10 / 三 14 / 四 19 / **五 1**），剩余 ⬜ 待做 **10** 支（**E 10**）。
与 E01 详细计划 §4 末尾「E01 之后预期 57/67」**逐项吻合**。
"""


def main():
    with io.open(DOC, "a", encoding="utf-8", newline="") as handle:
        handle.write(TEXT)
    print("APPENDED chars=%d" % len(TEXT))


main()
