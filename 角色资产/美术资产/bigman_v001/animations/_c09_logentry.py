# -*- coding: utf-8 -*-
"""把 C09 制作日志（CRLF）追加到 doc/动画制作清单.md。"""
import io
import os

DOC = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "..", "doc", "动画制作清单.md")

ENTRY = u"""
### 2026-10-02 —— C09 `Skill_01` 肩撞 ✅ 已完成

**清单原文**：「起步短、前冲强，**肩膀作为明确命中点**。」

**产物**

| 产物 | 路径 |
|---|---|
| 脚本 | `animations/anim_skill01.py` |
| 标定探针 | `animations/probe_c09_baseline.py` |
| 关键帧三视图 | `previews/anim/skill01_{side,front,three_quarter}_f{0000,0008,0012,0020,0028,0036,0039,0090,0096}.png` |
| 动态预览 | `previews/anim/Skill_01_side.mp4` / `Skill_01_three_quarter.mp4` |
| 入库 | `bigman_anim_v001.glb` → `Skill_01` 通道 **171** / 骨 **57** / **1.600 s** |

**分段与时间轴**（`TOTAL=96` @60fps）

| 段 | 帧 | 时长 | 内容 |
|---|---|---|---|
| 起步 | 0→8 | 0.133 s | 微后坐 30 mm + 下沉 30 mm、含胸夹肩、屈膝蓄力 |
| 冲刺 | 8→36 | 0.467 s | 骨盆加速前冲 **590 mm**（速度 11.3→30.9 mm/f 线性上升）、双脚贴地拖行 |
| 命停 | 36→39 | 0.067 s | **14 骨旋转逐位冻结**，骨盆继续前压 **25 mm** |
| 收招 | 39→90 | 0.850 s | 单向减速 `q = 1−(1−u)^1.25` 回「战斗待机」 |
| 静止窗 | 90→96 | 0.100 s | 逐位静止，留给引擎混合 |

标记：`ENTER 0 / START_END 8 / DASH 8 / HIT 36 / HOLD_END 39 / RECOV 40 / SETTLE 90 / CANCEL 92 / END 96`

**门禁（全绿 `failed = []` / `non_ok_bools = []`，未放宽容差）**

| 门禁 | 实测 |
|---|---|
| `skill_start_ok` | 接缝差 **0.0**（`Skill_01@0` 逐位 = `Idle_01@0`，`SEAM_TOL=1e-6`） |
| `root_motion_ok` | 前冲 **560.0 mm**、净 **545.0 mm**（域 400~900） |
| `dash_speed_ok` | 28 帧速度 11.288→30.855 mm/f **严格递增** |
| `start_short_ok` | 前摇 **8 帧** |
| `shoulder_hit_ok` | 肩领先最前拳 **+550.02 mm**（≥150） |
| `hit_point_frontmost_ok` | 最差竞争者 = 胸 **+50.78 mm**（≥40） |
| `silhouette_torso_leads_head_ok` | 网格面：躯干最前点领先鼻尖 **83.64 mm**（≥60）、领先鞋尖 **84.47 mm**（≥30） |
| `hit_arm_leads_off_arm_ok` | 撞出侧袖面领先非撞出侧 **19.68 mm** |
| `lean_ok` | 撞击帧躯干前倾和 **45.0°**（≥35） |
| `drag_speed_ok` | 冲刺段两脚拖行速度单调非减（L 11.74→32.09 / R 10.61→29.00 mm/f） |
| `ground_contact_ok` | 全网格最低 **−0.96 mm**（域 −2~+6） |
| `stance_sole_ok` | L [−0.00, 1.055] / R [−0.962, −0.00] mm |
| `ik_reach_ok` | 腿可达比 L 0.9518 / R 0.9671（≤0.995） |
| `world_step_ok` / `no_teleport` | 世界最大单帧转角 **5.571°** / 欧拉最大 **6.285°**（≤25） |
| `hitstop_frames_ok` / `hitstop_present_ok` | **4 帧**、14 骨步长 [0, 0, 0] |
| `hitstop_keeps_momentum_ok` | 命停期前压 **25.0 mm** |
| `decel_smooth_ok` / `no_snap_stop_ok` | 收招步长 3.864→1.160→0 **单调不增**、末帧 0 |
| `tail_settle_ok` | 末帧 8 骨与登记值差 **全部 0.0000°**（战斗待机） |
| `power_chain_ok` | 16 通道全非零 |

**登记元数据（供下游）**

- `root_motion_m = [0.0, −0.545]`
- `hit_side = "L"`；`hit_frame = 36`
- `hit_point_m.shoulder_m = [0.0597, −0.8837, 1.1126]`（肩骨 tail，绑定位）
- `hit_point_m.contact_m = [0.0198, −0.9910, 1.1421]`（★ **躯干最前顶点 = 真正的接触面**；
  骨端点埋在肉里 **107 mm**，下游 VFX / 命中判定请用 `contact_m`）
- `end_pose_deg` = Idle@0 躯干真值（`pelvis 4 / spine 2,2 / chest 1 / neck −6 / head 5 / shoulder ∓18`）

**★★ 第 1 件 —— 「肩膀是命中点」这条门禁第一版是「假绿」的。**

第一版 `shoulder_hit_ok` 只比「肩 vs 双拳」，实测 **+550 mm，轻松通过**。但把撞击帧
渲染出来一看：**头比肩还靠前 132 mm**（`head_m` y=−0.992 vs `shoulder` y=−0.860），
剪影读成**「用脸撞」** —— 门禁绿的，清单要求却是假的。现场指纹：侧视 f36 人脸在最前、肩在后。

**根因**：躯干前压 45° 时，颈/头只写了 `neck −14 / head −5` —— 这个量只够**抵不掉**前压，
头仍被顶到肩前。**解法**：`neck −46 / head −26`，并**新增两条会失败的门禁**：

1. **`hit_point_frontmost_ok`** —— 命中点必须**严格领先头 / 胸 / 双膝 / 双脚 / 双拳**
   全部 ≥ **40 mm**。这条当场又抓出**第二个**违规者：前脚脚尖（`LAG_L=1.04` 让前脚抢到
   肩前 38 mm，读成「脚先撞上」）⟹ 拖行系数改 **0.90 / 0.80**（身体从脚上**压过去**，
   不是脚抢在前面）。
2. **`silhouette_torso_leads_head_ok`** —— `bone_world()` 取的是**骨端点**（`head` 的 tail
   是**颅顶**），而观众看到的是**网格面**，两者差 100 mm 量级。改用
   `Head/Nose/Hair_Mass/Glasses_*` 与 `Suit_Torso/Shirt_Front/Jacket_*` 的**最前顶点**
   复测：躯干面领先鼻尖 **83.6 mm**、领先鞋尖 **84.5 mm**。

> 这是 C08 第 5 号教训（「登记了元数据就该有一条会失败的断言盯着它」）的**再次适用**，
> 但换了病灶：这次**门禁量的是代理量（骨端点），被代理量与观测量（网格面）的差骗过去了**。
> 凡「用骨端点下结论」的地方，都要问一句：**观众看到的是这个点吗？**

**★ 第 2 件 —— 肩的「前送」必须给它自己开一根通道，扭转带不动。**

第一版把「送肩出去」全押在躯干扭转（`ry`）上：实测扭转 **−22° 只换来肩前移 23 mm**
（≈**1.06 mm/度**）。补上 `shoulder.L` 的 **rz** 通道（`rig_axis_map.md`：`shoulder.L`
rz<0 = 前，15° ⟹ tail 前移 29.19 mm ≈ **1.95 mm/度**）后，`rz = −18°` 再叠加扭转加深到
−7.9°，胸部端点从「只落后肩 23 mm」拉到**阈值内 50.78 mm**。
**结论**：想要某根骨真的领跑，就要给它**自己的通道**，别指望父链的旋转把它带出去。

**★ 第 3 件 —— `u^p` 加速剖面的首帧是「卡住」，不是「起步」。**

第一版冲刺用 `y = Δ·u^2`：速度单调 ✓，但 `n = 28` 时首帧只走 `Δ/n² = 0.75 mm`
（≈0.04% 身高），前 5 帧合计 **19 mm** —— 与清单「起步短、前冲强」直接打架
（短是短了，但**没有冲**）。
**解法**：速度剖面改成 `v(u) = v1·(r + (1−r)·u)`，`r = DASH_R0 = 0.35`
⟹ 位移 `y(u) = Δ·(r·u + (1−r)·u²/2) / ((1+r)/2)`。速度仍是 **u 的线性函数（单调非减）**，
但首帧 **11.288 mm（×15）**、末帧 30.855 mm。`dash_speed_ok` 依旧绿。

**★ 第 4 件 —— 手臂中段必须在**基准**上插测地线，不是在**方向**上插。**

首版 `world_step_ok` **31.6° @f4**、`no_teleport` **86.0° @f16**，指纹指向 `hand.R`。
根因：Idle 拳架的前臂指向前上方（−y,+z），命中姿指向上后方（+y,−z），两者夹角 **141°**；
首版按帧号在**方向**上等分后各自 `key_basis()` 重新解滚转 ⟹ 三段各走各的测地线，
接缝处出现折角。
**解法**：`MID1/MID2` 由 `SEAM → HIT` 两个**端点基准矩阵**做 `slerp` 取得
（`_basis_slerp`），"分段 slerp" 与 "整段 slerp" 逐位等价。修完**世界最大单帧转角
5.571°**（↓5.7×）、欧拉最大 6.285°。

**★ 第 5 件 —— 拖行单调判据的窗口只到 HIT，不含命停段。**

首版 `drag_speed_ok` 取 `(DASH_IN, HOLD_END]`，把命停段算进去 ⟹ 末 3 个值塌到常数
**8.667 mm/f**（命停期骨盆只再压 25 mm/4f = 6.25 mm/f），**必然破单调**。
命停之后的「脚还在滑」不属于「越冲越快」的范畴，那是 `hitstop_*` 的辖区。
窗口收到 `(DASH_IN, HIT]` 后 `drag_speed_ok` 自然绿。

**★ 第 6 件 —— 贴地闭环的 `shift` 必须并进踝**目标**，不是加在**姿态**上。**

首版 `build_pose` 把闭环解出的 `shift` 忘了并进 `leg_seat` 的踝目标 z ⟹ 闭环变成
**空转**（收敛判据永远不满足，白跑 4 轮），右脚鞋底全程骑在 **−2.06 mm**（刚越过
−2 下限），`ground_contact_ok` / `stance_sole_ok` 双红。修完闭环 2 轮收敛：残差
**0.015 mm**。另把收敛阈值从 `5e-5` 收到 `1e-6`。

**遗留问题**

- **`Jacket_Hem` / `Jacket_Hem_Line` 仍未绑骨**（`parent=null`、`vgroups=0`、
  只有 `SUBSURF` 无 `ARMATURE`、`dy_mm=0.0` 在 f0 与 f48 逐位相同）。与 C07 的
  `probe_belt.py` 结果**逐字一致** ⟹ **不是 C09 引入的**，是 C01 起就登记在案的
  模型蒙皮缺陷。**本支渲染图上肉眼可见**：末帧右后方浮着一条蓝色细条（就是它）。
  属模型侧，不在动画侧修。
- 本支未做「撞空」变体（清单未要求）；`hit_point_m` 保留了 `contact_m` 与
  `shoulder_m` 两个点，若要接「撞墙 / 撞空」分支可直接用。
- `no_foot_slide_*` 在本支**按计划撤下**（清单 §0.4 允许 Root Motion，支撑脚在地上
  拖行是「前冲强」的视觉本体），代价已用 `drag_speed_ok` 的可失败判据补上。

#### 下一支（C10 `Skill_02` 抱摔）的详细计划

清单要求：**抓取后抱起敌人砸地，重点制作两角色同步动画。**

**1. 与 C09 的差异表**

| 维度 | C09 `Skill_01` 肩撞 | C10 `Skill_02` 抱摔 |
|---|---|---|
| 段数 | 两段（起步/冲刺）+ 收招 | **四段**（抓取 → 抱起 → 砸地 → 收招） |
| 位移 | 前冲 545 mm | ★ **前冲 + 抬升**（抱起时 Root Motion 带 **+z**） |
| 命中点 | 肩（自身） | ★ **对手的落点**（第二角色，不是自身骨） |
| 同步对象 | 无 | ★★ **双角色同步**（本工程唯一没有先例的维度） |
| 核心难点 | 前冲惯性 vs 脚不滑 | ★ **抱住期间双手不漂**（≤3 mm）+ **砸地帧对手不穿地** |
| 顿感 | 命中帧 4 帧、14 骨冻 | 砸地帧 3~4 帧；**抱起抬高点的「顶」也要一停**（0.3~0.5 s 举起定住） |
| 前摇 | ≤ 8f | 抓取 ≤ **6f**（贴身技，比肩撞更快） |

**2. 门禁草案**

- **保留（通用）**：`ground_contact_ok` / `power_chain_ok` / `ik_reach_ok` /
  `world_step_ok` / `no_teleport` / `bone_travel_mm` / `low_bad_frames` /
  `hitstop_*` / `decel_smooth_ok` / `no_snap_stop_ok`。
- **保留（C09 新立，本支继续用）**：`skill_start_ok`（若上游是 Idle）、
  `tail_settle_ok`（末帧回战斗待机）、`silhouette_*` 两条（若剪影有明确最前点）。
- **撤下（C09 专属）**：`shoulder_hit_ok` / `hit_point_frontmost_ok`（本支命中点是
  **对手**，不是自身肩）/ `dash_speed_ok` / `drag_speed_ok`（抓取段是「贴近」不是
  「冲」，速度不必单调）/ `lean_ok` / `start_short_ok`（改判 `grab_time_ok ≤6f`）/
  `root_motion_ok`（域值不同，见下）。
- **C10 新增（必须会失败）**：
  1. **`carry_steady_ok`** —— 抱起窗口内**双手世界位置漂移 ≤ 3 mm**（C04
     `grab_hold_steady_ok` 的延续，对象换成「抱起」相位）。**这条是本支核心**：
     受招方是挂在手上摆的，手一漂，第二角色就在手里抖。
  2. **`victim_anchor_ok`** —— 逐相位登记受招方锚点世界坐标
     （`grab_point_m` / `carry_point_m` / `slam_point_m`），**三个都非空**且
     `slam_point_m.z ≥ −0.02 m`（**砸地帧对手不许穿地**；这条要会失败）。
  3. **`lift_height_ok`** —— 抱起相位 `carry_point_m.z` 相对抓取帧抬升 ≥ **600 mm**
     （「抱起」的字面量化：敌人要被离地带起来）。
  4. **`slam_speed_ok`** —— 砸地段 `slam_point_m` 的 z 速度单调**递减到 0**
     （下砸加速下落、触地瞬间停），且触地帧步长 ≤ 25°。
  5. **`root_motion_ok`（本支版）** —— 水平 ≤ 900 mm、**竖直** ∈ [0, +500] mm
     （抱起时可以把对手带离地，但本体不许飞起来）。
  6. **`grab_time_ok`** —— 抓取相位 ≤ **6 帧**（贴身技要快）。
  7. **`tail_settle_ok`** —— 收招回「战斗待机」（照抄 C09 写法 + `end_pose_deg`）。

**3. 复用清单**

- 抄 `anim_skill01.py` 的骨架：`_seg()` 两段取值、`q_of()`、`dash_ramp()`、
  `solve_pose()` 贴地闭环（**记得 `shift` 要并进踝目标**，C09 第 6 号教训）、
  `_sole_anchor()`、`arm_world_steps()`、`silhouette_front()`、`_frontmost_of()`。
- ★ **`_basis_slerp()` 的「在基准上插、不在方向上插」**（C09 第 4 号教训）——
  本支手臂轨迹更复杂（抓→抱→砸），更要用。
- ★ **`start_short_ok` 这类「字面量化」门禁的写法照搬**，只改阈值与名字。
- ★ **「登记了元数据就要有会失败的断言」**（C08 第 5 号 / C09 第 1 号）——
  本支要登记的锚点最多（3 个），每个都要有对应门禁。
- ★ **帧数反推 + 位移轨道不许进 `patch()` + `TOTAL ≥ SETTLE/CANCEL`**（C08 第 4 号）。
- ★ **看渲染图，别只看数字**（C09 第 1 号：假绿就是这么来的）。

**4. 开工顺序**

1. 读 `Idle_01@0` 真值 → 确认 `SEAM_TOL=1e-6`（C09 的上游是 Idle，C10 大概率也是）。
2. **只量不做**（`probe_c10_baseline.py`）：
   ① 抓取姿下双手能到的世界域（对 `grab_point_m` 定标，复用 C04 的结论）；
   ② 抱起姿下**双手能抬到多高**（`lift_height_ok` 的 600 mm 能不能达标，
      受臂长 + 肩高限制，**先量再定阈值**）；
   ③ 髋部发力下骨盆 z 的许可域（结合腿可达比 ≤0.995）；
   ④ 砸地段手从高处到地面的世界速度曲线（对 `slam_speed_ok` 定标）。
3. 写脚本 → `SKIP_RENDER=1` 迭代到 `failed=[]` **且** `non_ok_bools=[]`。
4. 完整渲染 → 目检 **抓取帧 / 抱起顶点 / 砸地帧 / 命停帧 / 末帧**，三视角。
5. 出 mp4 → `verify_glb.py`（确认 `Skill_02` 进 GLB）→ `probe_belt.py`。
6. 更新清单（登记三个锚点坐标 + 抬升高度 + 抓取帧数）→ 追加日志 → 接棒。

> **C10 之后预期**：完成 33/67，剩余 ⬜ 待做 **34** 支（C 4 / D 19 / E 11）。

---

### 本支沉淀的可复用件（给下一支的自己）

`anim_skill01.py` 里已经立了 6 个**可复用的量测 / 门禁件**：

| 件 | 作用 |
|---|---|
| `dash_ramp(u)` | 速度随 u 线性上升的**单调加速剖面**（`r=DASH_R0` 决定首帧速度） |
| `_basis_slerp(a, b, t)` | 两个世界 3×3 之间的**测地线插值**（处理 q/−q 双覆盖） |
| `silhouette_front()` + `_frontmost_of()` | **网格面**剪影前沿实测（头组 / 躯干组 / 鞋组 / 撞出侧袖） |
| `foot_series()` / `arm_world_steps()` | 逐帧世界实测（踝 / 鞋底 / 枢轴顶点 / 骨端转角） |
| `solve_pose()` | 贴地闭环（`SOLE_DIAG` 可打迭代过程） |
| `skill_assertions()` 的 14 段结构 | 门禁编号 + `failed` / `non_ok_bools` 分离 |

**调试开关**（全部走环境变量，便于**扫描而不改文件**）：

- `SKIP_RENDER=1` 只跑门禁；`C09_TRACE=1` 打逐帧轨迹；
  `C09_SOLE_DIAG=1` + `C09_SOLE_DIAG_FRAMES=8,36,...` 打贴地闭环迭代过程。
- 所有阈值 / 常量都能用 `C09_*` 环境变量覆盖。
- 扫描脚本样例：`animations/_c09_sweep.sh`（把参数组合喂给环境变量跑一轮门禁对比）。
  本支就是用它一眼看出「头角 −46/−26 是唯一可行点」（−38/−18 掉到 46 mm、不符）。
"""

with io.open(DOC, "rb") as fh:
    raw = fh.read()
text = raw.decode("utf-8")
assert "\r\n" in text, "目标文件不是 CRLF，先确认行尾"
entry = ENTRY.replace("\r\n", "\n").replace("\n", "\r\n")
if not text.endswith("\r\n"):
    entry = "\r\n" + entry
with io.open(DOC, "wb") as fh:
    fh.write(text.encode("utf-8") + entry.encode("utf-8"))
print("C09_LOG_APPENDED bytes=%d" % len(entry.encode("utf-8")))
