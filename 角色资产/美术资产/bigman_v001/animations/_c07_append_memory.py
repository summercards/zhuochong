# -*- coding: utf-8 -*-
"""把 C07 完成记录追加进 .workbuddy/memory/2026-10-02.md。"""
import io
import os

PATH = os.path.join("..", "..", "..", "..", ".workbuddy", "memory",
                    "2026-10-02.md")

BODY = u"""

---

# C07 `Ground_Smash` 地面砸击 ✅ 已完成（2026-10-02 下午）

清单第 133 行。**原地、一次性、无上游接缝**（起于 `Idle_01@0`，逐位过）。
脚本 `animations/anim_smash07.py`（约 960 行）。**60 帧 / 1.000 s**。

## 门禁

`failed=[]`，`non_ok_bools=['no_teleport']`（通道安全上报，非门禁）。

| 判据 | 实测 |
|---|---|
| `smash_height_ok` | 高举顶拳中点 z **2019.5 mm**（≥1850） |
| `smash_depth_ok` | 砸击帧拳中点 z **292.3 mm**（≤320，余量 27.75） |
| `smash_swing_ok` | 躯干链 sum rx −15.0 → +55.0 ⟹ **70.0°**（≥60） |
| `smash_arc_ok` | 拳 z 逐帧单调下降，上升帧 **0** |
| `squat_depth_ok` | 砸击帧骨盆 z **545.0 mm**（≤640） |
| `spread_ok` | 拳心 x 偏差 **0.0 mm**（≤60） |
| `hitstop_present_ok` | 14 骨冻结步长 `[0.0,0.0,0.0]` |
| `hitstop_keeps_momentum_ok` | **14.0 mm**（>10） |
| `ik_reach_ok` | L 0.98680 / R 0.96315（≤0.995） |
| `world_step_ok` | **23.358°**（≤25） |
| `local_step_max_deg` | **4.902°** |
| `decel_smooth_ok` | 收招尾 4.902 → 0.0 单调不增 |

## 登记值（下游引用）

砸击帧 **f36**（冻结窗 f37~f39）。砸击点 = **身前地面**
`[0.0, −0.4609, 0.2923]` m（两拳并列，拳心 x 偏差 0；拳间距 396.69 mm）；
砸击时骨盆 `[0.0, −0.040, 0.545]` m（下沉 285 mm）。

## 出图 / 出包

- 静帧 24 张 `previews/anim/smash07_{side,front,three_quarter}_f{0000,0009,0020,0028,0036,0039,0054,0060}.png`
- mp4 `previews/anim/Ground_Smash_side.mp4`
- `verify_glb.py`：animations **29 → 30**，`Ground_Smash` 通道 171 / 骨 57 / **1.000 s**
- `probe_belt.py`：`BELT_PROBE_STILL` 仍只有 `Jacket_Hem` / `Jacket_Hem_Line`，**无回归**

## ★ 本支硬知识（已写进清单「本支 5 条教训」）

1. ★★ **门禁全红一片时先找一根根因**。第 1 轮 7 项红（拳心 x 偏 1500~2548 mm、
   腿可达比 1.0943、脚底漂 3.2 m、骨盆行程 3932 mm）—— 根因**只有一个**：
   `PELVIS_X` 是**位移**轨道（米），却被送进 `patch()`，而 `patch()` 取的是
   `SEAM_EULER[bone][0]`（**旋转**角，度）。Idle 骨盆 rx `3.93°` 被当成 **3.93 m**
   横向位移灌进 f0 ⟹ 全身横飞。**一行修正，7 项红一次转绿。**
   **通则：`patch()` 只服务欧拉通道。新增位移轨道时先问"米还是度"。**
2. ★ **走到"与站架反向"的朝向时，不许逐帧做最小旋转反解**（`aim_bone_ref`）。
   本支要求"双拳过顶"，手臂方向接近 Idle 方向的**反向**，而最小旋转的**滚转**分支
   在反向点不连续。实测 ANTIC+2 单帧世界转动 **34.3°**（上限 25），而同帧**方向**
   只变 **8.0°** —— 多出的 26° 是滚转在"补课"。
   把前摇 18→20 帧只压到 25.6°、**峰位不动** ⟹ 证明是滚转不是速度。
   **正解**：对相位两端**朝向**（3×3）做**四元数 slerp**。⟹ **23.358°**，
   且六项专属门禁值**逐位不变**。
   **通则：举过头顶 / 大回环 / 后仰 这类动作，用朝向 slerp 或关键帧直接给滚转。**
3. ★ **`stance_pivot_ok` 量的是"定点"**。第 1 轮 L 侧 57.5 mm 红，而同轮
   `plant_drift` 只有 0.015 mm（踝是钉死的）⟹ 是**量法伪影**。
   原做法取"每帧最低顶点"，脚底前后两顶点 z 只差零点几毫米，"最低"在两者间跳，
   跳量 = 两顶点 xy 距离。**正解**：仿 C06 在 f0 钉死一个顶点（最低 2 mm 带内最前），
   全程量同一个。⟹ 0.0153 mm。
4. ★ **取景的坑这次在竖直**。`ortho_scale` 量的是**长边**：780×1100 视图下
   `2.10` 是**竖直**跨度，中心 z=0.92 ⟹ 上边界只到 **1.97 m**，而高举顶双拳到
   **2.02~2.11 m** ⟹ 第 1 轮出图**把双拳整段切掉**（门禁却全绿）。
   按实测包围盒重定 ⟹ `ortho_scale 2.3084`、上边界 **2.178 m**。
   **通则：肢体高过 1.97 m 的动作必须重定取景，且要同时管竖直与水平。**
5. **命停窗"力量还在往地里压"靠骨盆爬行**。本支无 Root Motion，14 骨冻结 + `PELVIS_Y`
   在命停窗继续前移 **14 mm** ⟹ `hitstop_momentum_mm = 14.0`。
   **为什么 C07 能冻 14 骨而 C06 只能冻 8 骨**：C06 手臂是**位置逆解**（冻欧拉 = 焊住手）；
   C07 手臂是**朝向链**（命停窗朝向本就给死）⟹ 冻欧拉 = 冻视觉。**这正是 C04 的适用条件。**

## 遗留问题

1. `no_teleport = false`（通道口径；两把更严的尺子全绿：`local_step_max_deg 4.902` /
   `world_step_max_deg 23.358`）。**两值之差（45.049 vs 23.358）**来自最小旋转反解
   在臂上产生的**通道级滚转**，`world_step` 才是视觉口径（见教训 2）。
2. 末帧非 Idle（半蹲起势）—— 有意设计，登记在 `end_pose_deg` / `end_arm_dirs`。
3. 净位移 **10 mm**（非 0）—— 末帧半蹲起势略前倾；`root_motion_ok` 门槛 30 mm 内。
   要严格 0 就把 `C07_END_PY` 置 0 重跑（判定 1 cm 不值得再走一轮渲染）。
4. `Jacket_Hem` / `Jacket_Hem_Line` 未蒙皮 —— 本支**无回归**，但本支是**大幅弯腰**动作，
   这条没绑骨的横杆在侧视图里很显眼（`smash07_side_f0036.png` 躯干后方水平蓝杆）。

## 下一支

**C08 `Charge` 蓄力**（清单第 134 行）。★ 清单里**第一支明确要"可分段"**的动作：
**起手 / 循环 / 释放** 三段；循环段要求**首末帧逐位相同**（`loop_seamless`）。
新增 6 条判据：`charge_sink_mm`(≥80) / `charge_sink_pose_ok`(循环段骨盆 z 波动 ≤2) /
`charge_stance_ok`(扎稳) / `charge_leg_reach_ok`(≤0.95，比通用更严) /
`charge_loop_ok`(逐位闭合) / `charge_arm_hold_ok`(拳漂 ≤8)。
**要留意的坑**：`build_action` 取通道并集 ⟹ 三段是同 Action 还是三个 Action
**必须先量清楚**，别假设 `loop_seamless` 能在三段 Action 上成立。
详细计划已写进清单「下一支详细制作计划 —— C08」。
预期：完成 **31/67**，剩余 **36** 支。
"""


def main():
    text = io.open(PATH, encoding="utf-8").read()
    assert u"C07 `Ground_Smash` 地面砸击 ✅ 已完成" not in text, u"记录已存在"
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(
        text.rstrip() + u"\n" + BODY)
    print(u"MEMORY_APPEND_OK")


if __name__ == "__main__":
    main()
