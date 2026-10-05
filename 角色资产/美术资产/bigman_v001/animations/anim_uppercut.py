"""anim_uppercut —— B07 `Uppercut` 上勾拳（**深蹲蓄力、后腿髋驱动、拳往上打**）。

设计（对着清单「下一支详细制作计划 —— B07」逐条落）：
    定位      上勾拳，适合**击飞**；单发普通攻击（B 族）。清单原文：
              「深蹲蓄力后腿髋驱动拳头向上，适合击飞。**角色自身重心也应明显上升**」。
    时长      50 帧 / 0.833 s @60fps，**非循环**。
    首帧      **逐位 = `Idle_01@0`**（起手不许闪）。
    末帧      **停在自持的「上勾完」姿态**（拳在头侧上方、重心已落回，不回 idle）。
    结构      GUARD 0 ／ LOAD 0~6（微沉 + 后手拳下沉预备）／
              CROUCH 6~14（**深蹲蓄力**：骨盆压到最低、双膝深屈、后手拳压到腰侧）／
              BURST 14~24（`hit_frame = 24`，蹬伸 + 上勾，拳峰冲到过顶）／
              HITSTOP f24~f27（**4 帧完全冻结**，击飞技给足）／
              FOLLOW 24~30（髋继续上送、躯干继续**伸展**"打透"）／
              RECOVER 30~44（缓出滑停）／clock ≥44 姿态**逐位恒定**／CANCEL 34。

---------------------------------------------------------------------------
★★ 第 0 件：**本支的核心矛盾 ——「重心明显上升」与「不许 Root Motion」**

  普通攻击不许位移 root ⟹ 上升只能靠**腿的蹬伸**做出来。三条腿（计划原文）：
  ① 膝伸直；② 踝跖屈（踮脚）；③ 髋后伸/前送。

  ⚠️ 但计划原文对②的估计（"攻击侧脚跟离地 +30~60 mm"）**不足以**撑起
  `rise_ok ≥ +120` —— 这是本支实测出来的硬结论，必须写清楚：

      leg = 410 + 412 = **822 mm**；guard 的髋→踝只有 **771 mm**（余量 51）。
      **支撑脚平踩时骨盆上限 = 897.9 ⟹ 上升天花板只有 +67.9 mm。**
      想要 +120，**支撑脚必须提踵**，而且提踵的"滚动支点"取在哪，
      直接决定踝能升多高（下面第 1 件）。

  另一条同时被实测钉死的结论：**攻击腿（后腿 R）在命中帧必须离地**。
  骨盆前送后髋距后踝 ≥ 820 mm，后脚**无论怎么踮都够不到地面**
  （把后踝按"鞋底最前缘钉地"算到 20° 时，髋→踝要 918 mm > 822）⟹
  后腿在命中帧是**蹬完延伸出去的悬空后腿**，不是支撑腿。

---------------------------------------------------------------------------
★ 第 1 件：**支撑脚的"提踵"用「鞋底最前缘滚动支点」模型**（探针实测选的）。

  三种候选模型都算过，只有一种同时满足「鞋底不戳穿 / 接触点不滑动 / 踝够高」：

    · **踝不动直接转**（`U07_TIP_SCAN` 原始量）：鞋尖捅穿地面 96.6 mm @35°。
    · **钉住"当前最低点"**：模型在 θ∈(0,10°) 处**不连续** —— 平底鞋的"最低点"
      在鞋底一整段上取值本来就是任意的（实测 0° 报 −28.1 mm、10° 突然跳到
      −184.2 mm），钉它会得到一条**带拐点**的踝轨迹（0→156 mm 一帧内跳）。
    · **钉住鞋底最前缘**（本支采用）：鞋底从 −28 到 −201 是一整段平面，
      最前缘就是这条平面的**天然前棱**；绕它滚动，踝的轨迹**连续、单调、无拐点**，
      鞋底其余部分全部旋转**抬起**（不会戳穿），接触点世界坐标**逐帧不变**。

  代价与收益（探针 `U07_TIP_SCAN` + 手算校验）：

      θ=30°  踝 = (143.2, −235.8, 169.8)   髋→踝 802.7 ⟹ 余量 19.3，rise **+135** ✓
      θ=32°  踝 = (143.2, −241.9, 174.3)   髋→踝 799.7 ⟹ 余量 22.3，rise **+135** ✓

  ⚠️ 踝会**向前**移动（−169.6 → −241.9），这是对的：绕鞋尖滚动时踝就是往前上方走
  （和真人踮脚一致）。代价是骨盆必须跟着前送 ≥135 mm 才够得到 —— 正好也把
  `hip_drive_ok ≥ 60` 一起满足了（实测前送 **135 mm**）。

---------------------------------------------------------------------------
★ 第 2 件：**`ground_contact_ok` 必须拆两侧写**（计划原文指定的口径改）。
  B04~B06 的通用门禁取 `min(L, R)`，本支攻击腿**必须离地** ⟹ 一刀切必假红。
  本支：**支撑脚（前脚 L）鞋底 −2~+6**、**攻击脚（后脚 R）允许离地**。
  另一条本支核心门禁 **`support_foot_pinned_ok`** 也跟着换尺子：
  不是"踝不动"（提踵时踝要走 100+ mm），而是**鞋底最前缘接触点的水平位移 ≤3 mm**。

---------------------------------------------------------------------------
★ 第 3 件：**`power_chain` 的基准段照 B06 第 2 件的推理显式选**。
  **同物理量的才严格比较**：`leg` 必须 > **84.788**（深蹲→蹬直 = 上勾的发动机）、
  `hip` 必须 > **12.0**（髋驱动是核心）；`foot` **不与 B06 比** —— 踢击甩脚背
  （76.293）与踮脚跖屈不是同一物理量 ⟹ 只要求非退化（≥3°）+ 踮脚 ≥12°。
  `waist`/`shoulder`/`hand` 非退化 + 时序 + **攻击臂占优**（> 护手臂 ×1.5）。

---------------------------------------------------------------------------
★ 第 4 件：**沿用 B04/B06 的既有结论，一字不改**：
  · 不覆写 `JS.Y_SAFE` / `JS.ROLL_COMFORT`（用库默认 62 / 16）。
  · 冻结窗口的**派生量必须跟着该姿态自己的 clock**（`key`），不许就近取常量。
  · 脚部"钉平/踮脚"一律走 `WF.add_world_rx`（绕**世界 X**），不写 `foot.rx`
    （父链外展把局部轴带偏 4.3°）。
  · 时序峰值只在 `[0, HIT+HOLD]` 发力窗口内取（全程峰落在收招段，是"回收"不是"发力"）。

---------------------------------------------------------------------------
★★ 第 5 件（本支核心修补）：**`aim_carry` 的 roll 搜索必须加"连续性"代价**。

  `aim_carry` 第二段是"步长 > `ROLL_COMFORT` 或 |Y| 越界时扫 `roll` 取
  `欧拉步长 + |Y| 惩罚` 最小的一支"。它的代价函数**只看当前这根骨**、
  不看上一帧选了什么 roll ⟹ 上勾这种连续 10 帧都超 `ROLL_COMFORT` 的快动作里，
  它**逐帧改主意**：实测 `upperarm.R` 的 roll 在 f19→f20 由 **+13° 跳到 −40°**。

  roll 就是绕骨轴的扭转 ⟹ `upperarm.R` 世界旋转单帧 **58.23°**，
  而拳峰只走了 132 mm —— 那是**扭转变**，不是挥臂。
  连锁：前臂扭 58°、手的**世界朝向**只动 21° ⟹ 手的**局部**欧拉必须自己吃掉
  66.7° ⟹ `hand.R` 局部欧拉单帧 **52.094°** ⟹ `no_teleport` 红。

  修法 = `aim_carry_stable`：代价里加 `ROLL_W·|roll − roll_prev|`
  （**只惩罚"改主意"，不改判据** —— 搜索范围 / `Y_SAFE` / `ROLL_COMFORT` /
  欧拉步长口径一字不改）。

---------------------------------------------------------------------------
★★ 第 6 件（本支核心修补）：**拳的轨迹不许从肩口穿过** —— 探针 `probe_up07_arm` 实测。

  第 3 件的"臂可达环带夹取"是**安全网**，但它救不了**轨迹本身有病**：
  双骨臂 `|328−224| = 104 mm`，而 `FOLD_MIN_RATIO` 把夹带下界顶到 **176.6 mm**。
  夹取只是把"请求距离 < 176.6"的腕目标**沿同方向推到 176.6** ——
  **方向本身由 `肩→请求腕` 决定**。请求距离一旦趋近 0，这个方向的**转动速度**
  就发散（|v|→0 时方向可任意快转）⟹ 夹后的腕位**逐帧乱摆**。

  实测（`UP07_ARM_GEOM`，单位 mm，`rel` = 拳峰 − 肩）：

      c=14（蹲底）  rel=(9.2,  −24.7, −127.1)  请求 188.6   ← 拳离肩只有 24.7 mm 前
      c=17          rel=(12.9, −63.7,  −43.8)  请求 118.9
      c=18          rel=(14.7, −84.3,    2.4)  请求  84.6   ← 拳与肩同高
      c=19          rel=(16.6,−107.5,   56.5)  请求  67.7   ← **最紧**
      c=20          rel=(18.6,−132.6,  118.5)  请求  97.1

  根因两条，都是**轨迹设计缺陷**，不是求解器问题：

    ① **蓄力时拳压得不够低**。原 `chamber z` 偏移 −0.3682 ⟹ 蹲底拳 z = **930 mm**，
       而同时骨盆已压到 **615 mm** ⟹ 拳在**骨盆上方 315 mm**（胸腹之间），
       根本不在"腰侧"；且躯干前屈 15° 把**肩前送 122 mm**（`probe_up07_arm`：
       肩 y 由 −51.2 走到 −173.3），**肩追上来把拳吞了**。
    ② **拳峰轨迹是一条直线**（世界偏移空间里 chamber → strike 的弦），
       而 strike 的 y 偏移只用 −0.0015 ⟹ 拳几乎**不往前**，却要**从肩口竖直穿过**。

  修法（三条一起，全部有实测支撑）：

    a. `FIST_TRACK["R"]` 的 `chamber.z`：−0.3682 → **−0.6032**
       ⟹ 蹲底拳 z = **695 mm**（骨盆 615 之上 **80 mm**）——
       ★ 这才真正落实计划原文「后手拳压到腰侧（拳在髋高度）」，原值其实没做到。
    b. `FIST_TRACK["R"]` 的 `strike.y`：−0.0015 → **−0.0915**
       ⟹ 命中帧拳峰前送 90 mm（`rel` 前向由 241.8 → 331.8），
       ★ 拳走**外弧**：从下方绕到肩**外侧**再上顶，不再穿肩。
    c. `BURST_POW` 1.45 → **2.00**
       ⟹ 蹬伸更"**起缓收快**"：发力中段拳仍**留在肩下**（拉开与肩的竖直距离），
       ★ 顺带把拳峰世界速度峰**压到命中帧**（这正是 `power_chain_timing_ok` 要的
       "拳峰 ∈ [HIT−3, HIT+1]"），也正对 §6「启动略慢、命中极重」。

  修后实测（同表）：窗口内最紧 **195.2 mm @ c=21**，**全程不再触发夹取**
  （夹带下界 176.6）⟹ 腕目标由"自己的轨迹"驱动，臂的世界旋转回到 **≤16°/帧**。

  ★ 操守：**夹取是安全网，不是设计**。门禁判红时先问"轨迹本身合不合理"，
  再来才是加夹取；否则只是把病从"求解器"搬到"几何"。

★★ 第 7 件（本支核心修补）：**攻击臂的拳走「肩相对弧」，不走世界直线**。

  第 6 件修完，`forearm.R` 单帧 45.131°（`no_teleport` 红，预算 25°）仍在。
  离线几何扫描（`probe_up07_arc.py`，把 `arm_to` 的两骨几何在探针里复刻）给出
  判决性的对比 —— 同一套端点、只换中间的**形状**：

    形状                    R 最小请求距离  爆发段是否夹取   世界转角峰值
    ─────────────────────   ──────────────  ──────────────   ────────────
    世界直线（原方案）            162.2 mm      夹 1 帧            42.1°
    **肩相对弧（本方案）**        421.0 mm      **不夹**           19.3°

  为什么世界直线必输：拳的可达区是**以肩为心的环带**，而世界直线是**以世界为参照
  的直线**。躯干在 14→24 把肩前送 173 mm、抬高 354 mm ⟹ 同一条世界直线在**肩的
  坐标系里**会明显弯向肩心，中途必然切进内环带。实测 c=21 时拳离肩只有 181 mm。

  所以 R 侧 14→24 改成：**方向 `slerp(rel₁₄ → rel₂₄)`、半径线性插值、圆心 = 该帧的肩**。
  端点由构造**逐位等于**世界轨（`u=0/1` 取端点值）⟹ 六个关键姿态一帧不动。
  实测 `rel` 半径 363 → 559 mm，全程远离折叠下界 176.6 ⟹ 弧内夹取彻底消失。

★★ 第 8 件（本支核心修补）：**护手臂的拳峰轨必须跟着躯干平移，不能钉在世界系**。

  修完第 7 件，最红的一帧从 `forearm.R` 换成了 **f34 `forearm.L` 42.058°/帧**。
  把 `UP07_ARM_REQ` 的窗口从"发力段"放大到**整支**之后，真相是一句话：

    L 的「拳−肩」请求距离 111.8 mm（f15）→ **553.8 mm（f33）**，而可达带是
    **[176.6, 551.7]** —— 护手肘在**折叠芯**和**极限球面**两头各撞了一次。

  根因不是"夹取参数"，是**参照系选错了**：L 的拳峰轨是**世界偏移**（guard 位 + 常量），
  而躯干竖直方向要走 **−215 mm（深蹲）→ +136 mm（命中）**。
  拳钉在世界系不动、肩走了 350 mm，距离必然先塌到 111、再拉爆到 554 mm。
  ★ 这与上勾的"重心明显上升"是同一个物理量 —— 越是强调抬重心，这个坑越深。

  修法：护手臂的拳峰目标 = `世界轨 + 骨盆的世界平移量`
  （`PELVIS_DX/DY/DZ` 的三个 `chain6`，就是躯干自己的位移，不新造数据）。
  ⟹ 拳跟着躯干走，肘角天然有界。实测距离回到 **260~400 mm**（ext 0.47~0.72），
  上下夹取归零，f33→f34 的 42° 跳变随之消失。

  诊断教训（已固化）：`UP07_ARM_CLAMP_SUMMARY` 原来**只报下夹取**
  （`used > req`），而上界夹取是 `used < req` ⟹ 这条红点被埋了好几轮。
  现在上下分开报，并且 `upper_over_by_mm` 直接给出"超了多少"。

★ 第 9 件：**`BURST_POW` 必须同时喂"时机"和"单帧角速度"，两边一起看**。

  第 7/8 件修完，最红的一帧落到 **f24 `shin.R` 27.02°/帧**（预算 25）——
  是**真旋转**（世界 31.66° > 欧拉 27.02°，不是万向节虚高），
  来自"蹬伸越后置 ⟹ 最后一帧越快"这条设计。`BURST_POW` 扫描实测：

    BURST_POW    f24 shin.R    判定
    ──────────   ───────────   ──────────────────────────
      2.00        27.02°/帧    红（timing 峰值仍全在 24）
      1.85        25.82°/帧    红
    **1.55**      23.20°/帧    **绿**（余量 1.80°）
      1.40        21.55°/帧    绿（余量 3.45°，但"收快"变弱）

  ★ 判据：**降 `BURST_POW` 是改运动曲线，不是放宽容差**（阈值 25 一字未动）。
  取值同时满足：① `p > 1`（速度单调升 ⟹ 峰值帧 ≡ HIT）② 单帧 ≤ 25 且留余量。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python anim_uppercut.py
    SKIP_RENDER=1 只跑门禁（迭代用）。
"""

import math
import os
import sys

import bpy
from mathutils import Matrix, Quaternion, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A          # noqa: E402
import anim_idle_01 as I1     # noqa: E402
import anim_jump_start as JS  # noqa: E402
import anim_jump_fall as JF   # noqa: E402
import anim_crouch as CR      # noqa: E402
import anim_light_01 as L1    # noqa: E402
import anim_walk_f as WF      # noqa: E402

NAME = "Uppercut"
TOTAL = 50                    # 0.833 s @60fps
HIT = 24                      # 命中帧
HOLD = 3                      # 冻结 f24..f27 = **4 帧**
CLOCK_END = TOTAL - HOLD      # 47：动作时钟跨度

LOAD_END = 6                  # 反向预备（微沉 + 后手拳下沉）
CHARGE_END = 14               # **深蹲蓄力**到位（= CROUCH_END）
ANTIC_END = CHARGE_END        # 前摇结束（1~14 = 14 帧，落在「重攻击前摇 12~20 帧」）
BURST_START = CHARGE_END      # 爆发起点 = 深蹲谷底（14）⟹ 爆发段 14→24 = 10 帧
FOLLOW_END = 30               # 打透峰值
RECOVER_END = TOTAL - 2 * HOLD  # 44 ⟹ clock ≥44 姿态逐位恒定（末 4 帧零变化）
CANCEL = 34                   # 可取消帧（清单）

LOAD_POW = 1.00
CHAMBER_POW = 1.15            # 深蹲**起缓收快**（`u^p, p>1` ⟹ 首帧无尖峰，B06 第 5 件）
BURST_POW = 1.55              # 蹬伸**起缓收快**（上勾是"弹"出去的）；`p > 1` ⟹
                              #   速度单调升到命中帧 ⟹ 世界速度峰**恰好落在 HIT**
                              #   （`power_chain_timing_ok` 要的就是这个）。
                              # ★ 1.45 → 2.00 → **1.55** 的来回（实测记录，别再来回改）：
                              #   · 2.00：把 `shin.R` 送进 f24 = **27.02°/帧**（预算 25）
                              #     —— 蹬伸越"后置"，最后一帧的蹬伸角速度越大。
                              #   · 1.55：f24 = **23.20°/帧**，留 1.80° 余量；
                              #     四个峰值帧仍是 `{pelvis:24, knee:24, ankle:24, fist:24}`，
                              #     `rise_mm 135.0` / `hit_fist_z 1860` 一字未动。
                              #   · 拳的"起缓收快"现在由**独立的 `ARC_POW`** 管
                              #     （第 7 件），所以这里不必再为拳的形状买单。
FOLLOW_POW = 1.25
SETTLE_POW = 2.00             # 收招缓出（步长单调收敛到 0）
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"

SIDES = ("L", "R")
SUPPORT = "L"                 # 支撑腿 = **前脚** L（提踵滚动、接触点钉死的那条）
ATTACK = "R"                  # 攻击腿/攻击臂 = **后腿后手** R（"后腿髋驱动"，清单原文）
GUARD_SIDE = "L" if ATTACK == "R" else "R"   # 护手臂的**侧别**（见文件头第 8 件）
                              # ⚠️ 别叫 `GUARD_ARM` —— 本文件后面已有
                              #    `GUARD_ARM = ARM_BONES[SUPPORT]`（骨名**元组**），
                              #    同名会把它覆盖成元组，`side == GUARD_SIDE` 恒 False。

ARM_BONES = {"L": ("upperarm.L", "forearm.L", "hand.L"),
             "R": ("upperarm.R", "forearm.R", "hand.R")}
ARM6 = ARM_BONES["L"] + ARM_BONES["R"]
LEG6 = ("thigh.L", "shin.L", "foot.L", "thigh.R", "shin.R", "foot.R")
DROP = I1.DROP                # −0.070：战斗站姿的骨盆下沉量 ⟹ guard 骨盆 z = 830

# B06 的比较基准（写死在文件里，不靠记忆）—— 见文件头第 3 件
B06_SEGMENT_RANGES = {"foot": 76.293, "leg": 84.788, "hip": 12.0,
                      "waist": 22.0, "shoulder": 15.0, "hand": 67.816}
B06_STRICT = ("leg", "hip")             # 与 B06 **同一物理量**、必须严格超过的两段
B06_ATTACK_KNEE_SPAN = 92.83            # B06 的攻击膝伸展幅度（对照量）
B05_HIT_FIST_Z_MM = 1735.4              # B05 命中拳峰 z（"上勾要更高"的对照）

IDLE_PELVIS_Z_MM = 830.0
RISE_MIN_MM = 120.0                     # `rise_ok`：命中帧 − guard ≥ +120
CROUCH_MIN_MM = 150.0                   # `crouch_ok`：蓄力必须真沉下去
UPPERCUT_HEIGHT_MIN_MM = 1800.0         # `uppercut_height_ok`：命中拳峰 z
HIP_DRIVE_MIN_MM = 60.0                 # `hip_drive_ok`：命中帧骨盆前送
KNEE_EXTEND_MIN_DEG = 55.0              # `knee_extend_ok`：单侧膝从深蹲底伸展
TRUNK_EXTEND_MIN_DEG = 25.0             # `trunk_extend_ok`：躯干由前屈转伸展
FIST_TRAVEL_MIN_MM = 900.0              # 拳峰世界行程（弧长）
TIP_MIN_DEG = 12.0                      # 支撑脚踮脚幅度下限
FOLD_MIN_RATIO = 0.32                   # 臂可达环带下界 / (L上+L前) —— 见 `arm_to` 第 3 件
                                        #   0.32×552 = 176.6 mm（折叠极限 104 的 1.70 倍）
                                        #   取它而不是贴极限：留 70% 余量给 `sin_hip`，
                                        #   弯肘 ≈ 82°（`cos_hip 0.74 / sin_hip 0.67`）

# ── 攻击臂的**肩相对弧**（见文件头第 7 件）────────────────────────────────
#   爆发的 14→24 段，拳不再走"世界直线"，而走**以肩为心的球面弧**：
#   方向 `slerp(rel₁₄ → rel₂₄)`、半径线性 `|rel₁₄| → |rel₂₄|`，圆心 = 该帧的肩。
#   两端点由构造**逐位等于**世界轨（`u=0/1` 时方向与半径都取端点值），
#   所以六个关键姿态一个都不动 —— 只改中途 9 帧的形状。
#   ⟹ 拳到肩的距离恒 ≈ 0.75~0.85×臂长，**永不进入不可达环带**，
#     `arm_to` 的夹取在爆发段彻底消失（实测 162.2 → 421.0 mm）。
ARC_SIDE = ATTACK             # 只给攻击臂（护手臂原本就不夹）
ARC_POW = 1.20                # 弧的插值幂：1.00 匀速；>1 略后置 = 出手加速感
ARC_REL = {}                  # side -> (rel_a@CHARGE_END, rel_b@HIT)，单位 m
ARC_SH = {}                   # side -> {clock: 肩世界坐标}（只按躯干相位，与臂无关）
_REACH_MM = 552.0             # 上臂+前臂实测长（mm）——臂可达环带的**上界基数**；
                              #   `main()` 里用真骨长覆写，诊断报告靠它区分上下夹取。


# =============================================================== 相位时钟
def clock(frame):
    """动作时钟：命中停顿期间**时间冻结**（f24~f27 读同一个 clock = 24 ⟹ 姿态逐位相同）。"""
    if frame <= HIT:
        return frame
    if frame <= HIT + HOLD:
        return HIT
    return frame - HOLD


def _ramp(c, start, end, power):
    """`start → end` 的幂律上升；两端**精确**取 0 / 1（"真平台"的来源）。"""
    if c <= start:
        return 0.0
    if c >= end:
        return 1.0
    return ((c - start) / float(end - start)) ** power


def load_s(c):
    return _ramp(c, 0.0, LOAD_END, LOAD_POW)


def chamber_s(c):
    return _ramp(c, LOAD_END, CHARGE_END, CHAMBER_POW)


def burst_s(c):
    """蹬伸/上勾：`BURST_START(14) → HIT(24)` = **10 帧**，`u**1.45`（后段加速）。"""
    return _ramp(c, BURST_START, HIT, BURST_POW)


def follow_s(c):
    return _ramp(c, HIT, FOLLOW_END, FOLLOW_POW)


def settle_s(c):
    """收招：**缓出**（步长随 u→1 单调递减到 0）—— B04 第 5 件的结论，一字不改。"""
    u = (c - FOLLOW_END) / float(RECOVER_END - FOLLOW_END)
    if u <= 0.0:
        return 0.0
    if u >= 1.0:
        return 1.0
    return 1.0 - (1.0 - u) ** SETTLE_POW


def chain6(g, ld, ch, st, fo, en, c):
    """六段姿态路径：guard → load → crouch → strike → follow → end。

    `= g + (ld−g)·load + (ch−ld)·chamber + (st−ch)·burst + (fo−st)·follow
        + (en−fo)·settle`
    每个相位标量都精确饱和 ⟹ `c = 0/6/14/24/30/≥44` 处分别取 `g/ld/ch/st/fo/en`，
    **且 clock ≥44 后逐位恒定**（末 4 帧步长恒为 0）。
    """
    return (g
            + (ld - g) * load_s(c)
            + (ch - ld) * chamber_s(c)
            + (st - ch) * burst_s(c)
            + (fo - st) * follow_s(c)
            + (en - fo) * settle_s(c))


def chain3(row, c):
    return tuple(chain6(row[0][i], row[1][i], row[2][i], row[3][i], row[4][i],
                        row[5][i], c) for i in range(3))


CHANNEL_INDEX = {"rx": 0, "ry": 1, "rz": 2}

ANKLE_REST = {}               # side -> Vector：`Idle_01@0` 的踝位
SOLE_TIP = {}                 # side -> Vector：鞋底滚动支点的世界坐标
SOLE_PIVOT_ID = {}            # side -> (对象名, 顶点序号)：支点那个**材料顶点**
SOLE_PTS = {}                 # side -> [Vector]：鞋底网格全部顶点的世界坐标（guard 姿态）
SOLE_ZMIN = {}                # side -> float：鞋底最低点 z（guard 姿态）
IDLE_POSE = {}                # `Idle_01@0` 的完整姿态字典（首帧整帧取用）
POLE_LEG = {}                 # side -> 实测的膝鼓出方向（idle）
POLE_ARM = {}                 # side -> 实测的肘鼓出方向（idle）
HAND_GUARD = {}               # side -> idle 的手骨世界朝向
O_ARM_GUARD = {}              # side -> idle 的肩→拳峰偏移
A_TRACK = None                # 攻击踝的世界偏移轨（运行时填，含滚动支点算出的角点）
TRACE = []                    # 逐帧手臂/腿欧拉（|Y| 健康度诊断）
TARGETS = []                  # [(frame, side, target)]：腿部 IK 到位核验
REACH = []                    # [(side, ratio)]：腿伸展率体检
REQ = []                      # [(frame, side, req_mm, used_mm)]：臂请求距离 / 夹后距离


# =============================================================== 躯干轨
# 每行 = (bone, channel, guard, load, crouch, strike, follow, end)，单位度。
# ★ guard 那一列必须逐位等于 `Idle_01@0` 的真值：
#   pelvis 4.0 / spine 2.0 / chest 1.0 / neck −6.0 / head 5.0 / shoulder rx −18.0，其余 0。
# ★ 本支的"打透" = 躯干**继续伸展**：蹲底 rx 明显为正（前屈），命中帧转负（伸展），
#   打透相位继续往负走 ⟹ `trunk_extend_ok` 与 `body_follow_through_ok` 都取
#   物理量"骨盆→胸骨顶矢状仰角"（不让 ry/rz 污染，B06 第 3 件）。
TRUNK_CHAIN = (
    ("pelvis", "rx", 4.0, 7.0, 15.0, -7.0, -11.0, 3.0),
    ("spine_01", "rx", 2.0, 3.5, 7.5, -3.0, -4.5, 2.0),
    ("spine_02", "rx", 2.0, 3.5, 7.5, -3.0, -4.5, 2.0),
    ("chest", "rx", 1.0, 2.5, 6.5, -9.0, -14.0, 1.5),
    # 颈/头：蹲着低头蓄力 → 命中帧抬头看**上方目标**。
    ("neck", "rx", -6.0, -6.0, -2.0, -10.0, -11.0, -6.0),
    ("head", "rx", 5.0, 5.0, 3.0, 11.0, 12.0, 5.0),
    # 肩带：攻击侧（R）在命中帧**抬起来**送拳，护手侧（L）往回收。
    ("shoulder.R", "rx", -18.0, -17.0, -15.0, -31.0, -35.0, -20.0),
    ("shoulder.L", "rx", -18.0, -17.5, -16.0, -13.0, -11.0, -17.0),
    ("shoulder.R", "rz", 0.0, -1.0, -2.0, 5.0, 6.0, 1.0),
    ("shoulder.L", "rz", 0.0, 1.0, 2.0, -5.0, -6.0, -1.0),
)

# 骨盆位移（世界，米）：**原地**（清单 §0.4：普通攻击不许 Root Motion）。
# ★ `crouch` 列 = 深蹲谷底：骨盆 z 830 → **645**（沉 **185 mm**）。
# ★ `strike` 列 = 命中帧：骨盆 z 645 → **965**（相对 guard **+135**，`rise_ok` 要 ≥120）
#   且前送 **135 mm**（`hip_drive_ok` 要 ≥60）—— 上升与前送是同一件事的两个分量：
#   髋往前上送，支撑腿才能蹬直（见文件头第 0/1 件）。
PELVIS_DX = (0.000, 0.000, 0.000, 0.000, 0.000, 0.000)
PELVIS_DY = (0.000, 0.012, 0.035, -0.135, -0.150, -0.010)
PELVIS_DZ = (0.000, -0.045, -0.215, 0.135, 0.142, -0.030)

# ★ **蒙皮补偿**（B05 第 2 件）：鞋底随屈膝下沉而线性下陷（线性混合蒙皮固有误差，
#   `ankle_target_error_mm` 只 ~0.02 ⟹ 不是 IK 误差）。按 |下沉量| 的 1.2% 抬高踝目标。
#   ★ 本支**只在下沉时补偿**（`max(0, −dz)`）：命中帧骨盆是**上冲**的，蒙皮是拉伸不是塌陷，
#     还要保证命中帧的接触点严格落在模型算出的位置（多抬 1.7 mm 反而污染 `rise_ok` 的口径）。
ANKLE_SKIN_LIFT_RATIO = 0.012

# 支撑脚**踮脚角度轨**（绕世界 X，正 = 跖屈/脚尖压地）。
# ★ 命中帧 32°：由「鞋底最前缘滚动支点」模型给出踝 z = 174.3 mm ⟹ rise +135。
TIP_SUPPORT = (0.0, 0.0, 0.0, 32.0, 35.0, 0.0)
# 攻击脚**世界朝向轨**（同样绕世界 X 叠角）：地面段是小角度跖屈，
# 离地后把脚背甩下去（收招落回 0）。
TIP_ATTACK = (0.0, 3.0, 12.0, 45.0, 50.0, 0.0)
# 攻击脚"离地权重"：起脚瞬间脚尖**先继续贴地、再跟脚背一起甩出去**（相对角 12°→0）。
TIP_ATTACK_AIRBORNE = (CHARGE_END, HIT - 6)   # 15→18：权重 0→1

# ★ 攻击踝的**世界偏移轨**（相对 `Idle_01@0` 的 R 踝位，米）。
#   `load` / `crouch` 两列 = 滚动支点模型算出的**贴地位置**（运行时算，见 main）；
#   `strike` / `follow` 两列 = 离地后腿甩出去的世界位置（由髋→踝距离反推，ratio 0.99）。
A_TRACK_STRIKE = (0.0, 0.065, 0.150)
A_TRACK_FOLLOW = (0.0, 0.110, 0.185)
TIP_ATTACK_LOAD = TIP_ATTACK[1]
TIP_ATTACK_CROUCH = TIP_ATTACK[2]

# 骨盆位移 / 蹲起的**腿 pole 轨**：idle 实测 → 侧向外（探针 `U07_LEG_POLE_SUMMARY`：
# 侧向 pole 全程 `|pole⊥axis|` ≥ **0.9244**，不退化）。
POLE_LATERAL = {"L": (0.25, -1.0, 0.0), "R": (-0.25, -1.0, 0.0)}
POLE_BLEND_LO = 0.30
POLE_BLEND_HI = 0.90
# 肘 pole：护手/蓄力时肘朝**下外**，送拳时肘留**低位**（上勾的肘永远在拳下方）。
POLE_ELBOW = {"L": (0.30, 0.15, -0.94), "R": (-0.30, 0.15, -0.94)}

# 攻击臂（后手 R）的**拳峰世界目标轨**（米）。
# ★ `crouch` 列 = 拳压到**髋高度**（清单原文：后手拳压到腰侧）。**这一列必须是
#   「相对蹲底骨盆」的髋高，不是"世界 z 930"** —— 蹲底骨盆已压到 615，
#   拳 z 930 就跑到胸腹之间（骨盆上方 315），躯干前屈 15° 又把肩前送 122 mm
#   ⟹ 肩把拳吞掉（见文件头第 6 件）。现值 z = 695 = 骨盆上方 80 mm，才是腰侧。
#   `strike` 列 = 拳峰 z **1.86 m**（`uppercut_height_ok` 要 ≥1800，且比 B05 的 1735.4 高）
#   + **前送 90 mm**（`y = −0.0915`）：拳走**外弧**，从下方绕到肩**外侧**再上顶。
FIST_TRACK = {
    # 攻击臂（后手 R）：guard → 下沉 → **压到腰侧 z≈0.695** → **顶到 1.86 m** →
    #                  继续上送 1.93 → 落回自持位 1.56（拳在头侧上方）。
    "R": ((0.0000, 0.0000, 0.0000),
          (-0.0084, 0.0255, -0.0832),
          (-0.0124, 0.0755, -0.6032),
          (0.0116, -0.0915, 0.5618),
          (0.0176, 0.0285, 0.6318),
          (-0.0054, 0.0335, 0.2618)),
    # 护手臂（前手 L）：蓄力时略降，命中帧**往下后方拉**做反向配重。
    "L": ((0.0000, 0.0000, 0.0000),
          (0.0055, 0.0227, -0.0611),
          (0.0055, 0.0727, -0.2561),
          (0.0505, 0.1777, -0.3011),
          (0.0605, 0.1927, -0.3361),
          (0.0205, 0.0327, -0.0911)),
}
# 拳峰**朝向**轨（相对 idle 的手骨朝向的增量）：命中帧拳往上顶。
HAND_DIR_D = {
    "R": ((0.00, 0.00, 0.00), (0.00, 0.05, -0.15), (0.00, 0.12, -0.45),
          (0.00, 0.05, 1.20), (0.00, 0.08, 1.35), (0.00, 0.20, 0.35)),
    "L": ((0.00, 0.00, 0.00), (0.00, 0.05, -0.05), (0.00, 0.10, -0.15),
          (0.00, 0.15, -0.35), (0.00, 0.18, -0.40), (0.00, 0.05, -0.05)),
}


def trunk_pose(c):
    pose = {}
    for bone, channel, g, ld, ch, st, fo, en in TRUNK_CHAIN:
        row = pose.setdefault(bone, [0.0, 0.0, 0.0])
        row[CHANNEL_INDEX[channel]] = chain6(g, ld, ch, st, fo, en, c)
    return {bone: tuple(row) for bone, row in pose.items()}


def ankle_offset(c):
    return Vector(chain3(A_TRACK, c))


def tip_support(c):
    return chain6(*TIP_SUPPORT, c)


def tip_attack(c):
    return chain6(*TIP_ATTACK, c)


TIP_BAND = 0.006              # 选支点用的"最低层"厚度（米）


def foot_sole_points(side):
    """一侧鞋**全部网格顶点**的世界坐标（`(对象名, 顶点序号, 世界坐标)`）。

    为什么要全量：`tip_ankle` 的"把鞋底最低点拉回地面"必须知道**整只鞋**转过去
    之后谁最低 —— 只拿一个支点是不够的（见 `tip_ankle` 的文件头说明）。
    """
    depsgraph = bpy.context.evaluated_depsgraph_get()
    rows = []
    for name in A.FOOT_MESHES[side]:
        obj = bpy.data.objects.get(name)
        if obj is None:
            continue
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        matrix = evaluated.matrix_world
        for index, vertex in enumerate(mesh.vertices):
            rows.append((name, index, matrix @ vertex.co))
        evaluated.to_mesh_clear()
    return rows


def foot_pivot_vertex(rows, z_band=TIP_BAND):
    """**滚动支点**：最低 `z_band` 那一层里**最靠前**（y 最小）的顶点。

    返回 `(对象名, 顶点序号, 世界坐标)` —— **顶点序号是重点**：
    提踵时"最低的那个点"会在整段弧面上**身份乱跳**，实测假漂移 25~93 mm；
    只有钉住**同一个材料顶点**才能既测出滑移、又不被身份切换骗。

    ★ `z_band` 取 6 mm：鞋底是**弧面**（探针 `UP07_SOLE_GEOM`：0.5 mm 层里
      y 只占 0.08 mm，说明最低点近乎单点），6 mm 层能取到真正的**前缘**。
    """
    if not rows:
        return None
    zmin = min(row[2].z for row in rows)
    band = [row for row in rows if row[2].z <= zmin + z_band]
    name, index, point = min(band, key=lambda row: row[2].y)
    return (name, index, point)


def vertex_world(object_name, index):
    """某个网格顶点当前的世界坐标（逐帧跟踪**固定材料点**用）。"""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = bpy.data.objects[object_name].evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    point = evaluated.matrix_world @ mesh.vertices[index].co
    evaluated.to_mesh_clear()
    return point


def tip_ankle(side, tip_deg):
    """**绕鞋底支点刚性滚动** `tip_deg` 后，踝（`foot.<side>.head`）应落的世界位置。

    几何：踝相对支点 `rel = A_rest − pivot`，脚刚性转 `tip_deg`（绕世界 X，
    正 = 跖屈）后 `rel → R_x(tip)·rel`；支点世界位置不变 ⟹ 踝须移到
    `pivot + R_x(tip)·rel`。

    -----------------------------------------------------------------------
    ★★ 但"支点不动"≠"鞋底贴地" —— 这是本支踩出来的第 2 件事，必须写清楚：

      支点（最低 6 mm 层里最靠前那个顶点）**自己就悬空 5.85 mm**
      （探针 `UP07_SOLE_GEOM`：zmin 1.055、支点 z 6.902）。
      绕它转 ⟹ 整只鞋被抬到 5.4~7.61 mm（`support_sole_max` 7.61，
      `ground_contact_ok` 上限 6.0 ⟹ 判红）。**这是模型缺陷，不是门禁太严。**

      修法：按**整只鞋的真实几何**把"转动后鞋底最低点"拉回地面 ——
      `low(θ) = min_i [R_x(θ)(p_i − A_rest)].z`（对全部鞋底顶点取），
      踝再下移 `(A(θ).z + low(θ)) − zmin`。
      ★ 只做**世界 Z 平移** ⟹ 支点的 x/y 一点不动 ⟹
        `support_foot_pinned_ok`（≤3 mm）的零滑移由构造保证，不受影响。
      ★ `−zmin` 这一项保证 `θ = 0` 时修正量恰为 0（与 `ANKLE_REST` 连续，
        不会在起脚那一帧突然下沉）。
    """
    if abs(tip_deg) < 1e-9:
        return ANKLE_REST[side].copy()
    pivot = SOLE_TIP[side]
    rot = Matrix.Rotation(math.radians(tip_deg), 3, "X")
    ankle = pivot + (rot @ (ANKLE_REST[side] - pivot))
    pts = SOLE_PTS.get(side)
    if pts:
        low = min((rot @ (p - ANKLE_REST[side])).z for p in pts)
        ankle.z -= (ankle.z + low) - SOLE_ZMIN[side]
    return ankle


def fist_target(side, c):
    """拳峰世界目标。

    `side == ARC_SIDE` 且 `CHARGE_END ≤ c ≤ HIT` 时走**肩相对弧**（见文件头第 7 件）：
    拳相对肩的方向与半径各自在两端点插值，圆心取该帧的**肩**（只由躯干相位决定，
    因此可以逐帧预算 —— `apply_pose` 会清空全身，不能在解算循环里现场跑）。
    其余时钟一律走原世界轨，两端点两者逐位相同 ⟹ 关键姿态不动。
    """
    rel = ARC_REL.get(side)
    if rel is not None and CHARGE_END <= c <= HIT:
        u = _ramp(c, CHARGE_END, HIT, ARC_POW)
        ra, rb = rel
        direction = ra.normalized().slerp(rb.normalized(), u)
        length = ra.length + u * (rb.length - ra.length)
        return ARC_SH[side][c] + direction * length
    target = Vector(I1_FIST_GUARD[side]) + Vector(chain3(FIST_TRACK[side], c))
    if side == GUARD_SIDE:
        # ★ 第 8 件：护手臂的拳峰轨**必须跟着躯干平移**（不能钉在世界系）。
        #   躯干竖直要走 −215（深蹲）→ +136 mm（命中）；拳钉死在世界上不动，
        #   「拳−肩」距离就会从 111.8 mm（撞折叠芯）摆到 553.8 mm（撞极限球面）
        #   ⟹ 肘角在奇异点附近被放大 ⟹ f33→f34 `forearm.L` 42.058°/帧。
        #   补上骨盆自己的世界平移（`PELVIS_D*` 三个 chain6）即可 —— 不新造数据，
        #   且 c=0 时三个分量全 0 ⟹ guard 姿态逐位不变。
        target = target + Vector((chain6(*PELVIS_DX, c),
                                  chain6(*PELVIS_DY, c),
                                  chain6(*PELVIS_DZ, c)))
    return target


def _trunk_shoulder(arm, side, c):
    """只按**躯干相位** `c` 取一次「肩（`upperarm.<side>` head）的世界坐标」。

    肩由胸/锁骨链决定，与臂自身姿态无关 ⟹ 只把躯干+骨盆+手骨静止值写进去即可。
    ⚠️ 会调用 `A.apply_pose`（内部 `reset_pose`），**只能在解算循环外**用。
    """
    pose = trunk_pose(c)
    pose["toe.L"] = (0.0, 0.0, 0.0)
    pose["toe.R"] = (0.0, 0.0, 0.0)
    pose["@loc"] = {"pelvis": A.wloc(chain6(*PELVIS_DX, c), chain6(*PELVIS_DY, c),
                                     DROP + chain6(*PELVIS_DZ, c))}
    pose.update(A.FIST)
    A.apply_pose(arm, pose)
    return Vector(A.bone_world(arm, "upperarm." + side, "head"))


def build_arc_table(arm):
    """预算肩相对弧的两端点（`setup` 时跑一次）。"""
    global ARC_REL, ARC_SH
    ARC_REL, ARC_SH = {}, {}
    sh = {c: _trunk_shoulder(arm, ARC_SIDE, c)
          for c in range(CHARGE_END, HIT + 1)}
    ARC_SH[ARC_SIDE] = sh
    # ★ 只登记 `ARC_SIDE` —— 护手臂保持世界轨（实测它不夹，max 世界转角 19.1° < 25）
    ARC_REL[ARC_SIDE] = tuple(
        (Vector(I1_FIST_GUARD[ARC_SIDE])
         + Vector(chain3(FIST_TRACK[ARC_SIDE], c))) - sh[c]
        for c in (CHARGE_END, HIT))
    return ARC_REL


def hand_dir(side, c):
    base = Vector(HAND_GUARD[side])
    return (base + Vector(chain3(HAND_DIR_D[side], c))).normalized()


def bone_len(arm, name):
    return (Vector(A.bone_world(arm, name, "tail"))
            - Vector(A.bone_world(arm, name, "head"))).length


def _leg_pole_from_pose(arm, side):
    """实测「膝的鼓出方向」= (膝−髋) 去掉沿 髋→踝 轴分量后的单位垂足。"""
    hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
    knee = Vector(A.bone_world(arm, "shin." + side, "head"))
    ankle = Vector(A.bone_world(arm, "foot." + side, "head"))
    delta = ankle - hip
    axis = delta.normalized() if delta.length > 1e-9 else Vector((0.0, -1.0, 0.0))
    bulge = (knee - hip) - axis * (knee - hip).dot(axis)
    if bulge.length < 1e-6:
        bulge = Vector((0.0, -1.0, 0.0)) - axis * axis.y
    return tuple(bulge.normalized())


def _elbow_pole_from_pose(arm, side):
    """实测「肘的鼓出方向」（同口径，量臂）。"""
    up = Vector(A.bone_world(arm, "upperarm." + side, "head"))
    elbow = Vector(A.bone_world(arm, "upperarm." + side, "tail"))
    wrist = Vector(A.bone_world(arm, "forearm." + side, "tail"))
    delta = wrist - up
    axis = delta.normalized() if delta.length > 1e-9 else Vector((0.0, -1.0, 0.0))
    bulge = (elbow - up) - axis * (elbow - up).dot(axis)
    if bulge.length < 1e-6:
        bulge = Vector((0.0, 0.0, 1.0)) - axis * axis.z
    return tuple(bulge.normalized())


# =============================================================== 双骨 IK
_BULGE_PREV = {}              # key -> Vector：上一帧的鼓出方向（膝用 side，肘用 "arm.<side>"）
POLE_SIN = []                 # [(frame, tag, |pole⊥axis|)]：pole 退化体检


def _bulge(key, axis, pole):
    """鼓出方向（垂直于 `axis` 的单位向量）+ 退化体检值 `|pole⊥axis|`。

    沿用 B04 第 3 件：`pole` 与"上一帧鼓出方向"按 `|pole⊥axis|` **平滑混合**
    （`POLE_BLEND_LO/HI` 之间 smoothstep），逐帧连续，不被退化投影翻来翻去。
    **不许硬阈值**。
    """
    pole_v = Vector(pole)
    bulge = pole_v - axis * pole_v.dot(axis)
    sin_pole = bulge.length
    prev = _BULGE_PREV.get(key)
    if prev is not None:
        alt = prev - axis * prev.dot(axis)
        if alt.length > 1e-6:
            alt.normalize()
            if bulge.length < 1e-6:
                bulge = alt
            else:
                w = (sin_pole - POLE_BLEND_LO) / (POLE_BLEND_HI - POLE_BLEND_LO)
                w = min(1.0, max(0.0, w))
                w = w * w * (3.0 - 2.0 * w)
                bulge = bulge.normalized() * w + alt * (1.0 - w)
    if bulge.length < 1e-6:
        bulge = Vector((0.0, -1.0, 0.0)) - axis * axis.y
    bulge.normalize()
    _BULGE_PREV[key] = bulge
    return bulge, sin_pole


def leg_aim(arm, pose, side, target, pole):
    """把一侧的 thigh/shin 解到「踝（`foot.head`）落在世界 `target`」。

    与 `TURN.leg_to` 同几何（叉积平面内的两骨解），但膝的鼓出方向用 `_bulge`
    的**接力平滑**，并用 `JS.aim_carry` 反解（从上一帧已达成世界朝向接力 +
    绕骨轴 roll 搜索），表示连续。返回 `|pole⊥axis|`。
    """
    thigh_len, shin_len = A.L_THIGH, A.L_SHIN
    hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
    target = Vector(target)
    delta = target - hip
    raw = delta.length
    limit = (thigh_len + shin_len) * 0.9995
    distance = max(1e-4, min(raw, limit))
    REACH.append((side, raw / (thigh_len + shin_len)))
    axis = (delta.normalized() if delta.length > 1e-9
            else Vector((0.0, 0.0, -1.0)))
    bulge, sin_pole = _bulge(side, axis, pole)
    cos_hip = (thigh_len ** 2 + distance ** 2 - shin_len ** 2) \
        / (2.0 * thigh_len * distance)
    cos_hip = max(-1.0, min(1.0, cos_hip))
    sin_hip = math.sqrt(max(0.0, 1.0 - cos_hip * cos_hip))
    knee = hip + (axis * cos_hip + bulge * sin_hip) * thigh_len
    pose["thigh." + side] = JS.aim_carry(arm, "thigh." + side, knee - hip)
    pose["shin." + side] = JS.aim_carry(arm, "shin." + side, target - knee)
    POLE_SIN.append((side, sin_pole))
    return sin_pole


def arm_to(arm, pose, side, fist_world, direction, pole):
    """把一侧的上臂/前臂/手解到「拳峰落在世界 `fist_world`、手骨指向 `direction`」。

    ★★ 第 3 件（本支的核心修补）：**臂也有"够不到的芯"，必须夹住**。

    双骨链 `|L_上 − L_前| = |328 − 224| = 104 mm` 是**折叠极限**。计划里的拳峰
    轨迹（髋高度 → 过顶）是一条**直线**，中途会**从肩口穿过**：实测 f18~f20 的
    请求距离恒为 **104.0 mm**（正是折叠极限）——`cos_hip` 被夹到 1 ⟹ `sin_hip = 0`
    ⟹ 肘完全塌到 肩→腕 轴上，肘的鼓出方向独占权重且**病态** ⟹ 整条臂的朝向单帧乱转
    （`forearm.R` 世界 54.73°、`hand.R` 局部欧拉 47.55° ⟹ `no_teleport` 红）。

    修法与腿侧同理：把请求距离夹进 **可达环带** `[FOLD_MIN, 0.9995·(Lu+Lf)]`，
    并把 **腕目标一起挪到环带上**（不是只改 `distance` 常量 —— 那样几何会自相矛盾）。

    ⚠️ **但夹取只是安全网，不是设计**（文件头第 6 件）：
    夹取的方向 = `肩 → 请求腕`；请求距离趋近 0 时这个方向的**转动速度发散**
    ⟹ 夹后的腕位逐帧乱摆，臂照样 `no_teleport`。
    所以正解是**把轨迹改成不进入环带**（`FIST_TRACK` 的 chamber 压低 + strike 前送
    + `BURST_POW` 加大），让这里的夹取**全程不触发**。
    """
    upper, fore, handb = ARM_BONES[side]
    length_up = bone_len(arm, upper)
    length_fore = bone_len(arm, fore)
    length_hand = bone_len(arm, handb)
    want = Vector(direction).normalized()
    wrist_target = Vector(fist_world) - want * length_hand

    shoulder = Vector(A.bone_world(arm, upper, "head"))
    delta = wrist_target - shoulder
    raw_distance = delta.length
    reach = length_up + length_fore
    limit = reach * 0.9995
    fold_min = reach * FOLD_MIN_RATIO
    distance = max(1e-4, min(raw_distance, limit))
    axis = (delta.normalized() if delta.length > 1e-9
            else Vector((0.0, -1.0, 0.0)))
    if distance < fold_min:
        # ★ 走进"够不到的芯"：沿同一方向把腕目标推到环带下界，臂不许折叠到底。
        distance = fold_min
        wrist_target = shoulder + axis * distance
    REQ.append((side, raw_distance * 1000.0, distance * 1000.0))
    bulge, sin_pole = _bulge("arm." + side, axis, pole)
    cos_hip = (length_up ** 2 + distance ** 2 - length_fore ** 2) \
        / (2.0 * length_up * distance)
    cos_hip = max(-1.0, min(1.0, cos_hip))
    sin_hip = math.sqrt(max(0.0, 1.0 - cos_hip * cos_hip))
    elbow = shoulder + (axis * cos_hip + bulge * sin_hip) * length_up

    pose[upper] = aim_carry_stable(arm, upper, elbow - shoulder)
    pose[fore] = aim_carry_stable(arm, fore, wrist_target - elbow)
    pose[handb] = aim_carry_stable(arm, handb, want)
    POLE_SIN.append(("arm." + side, sin_pole))


def _record_trace(arm, frame, pose):
    for name, value in pose.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)
    TRACE.append({
        "frame": frame,
        "euler": {b: tuple(round(v, 2) for v in pose[b]) for b in ARM6 + LEG6},
        "roll": {b: round(JS.ARM_ROLL.get(b, 0.0), 1) for b in ARM6 + LEG6},
    })


# =============================================================== 臂：roll-连续性 IK
_ROLL_PREV = {}               # bone -> 上一帧选定的 roll（度）
ROLL_W = 0.60                 # roll 连续性权重（度/度）—— 抑制搜索"逐帧改主意"


def aim_carry_stable(arm, name, direction, base_q=None):
    """`JS.aim_carry` + **roll 连续性惩罚**（本支的核心修补，见文件头第 5 件）。

    为什么非加不可（本支实测）：`aim_carry` 的第二段是"步长 > `ROLL_COMFORT`
    或 |Y| 越界时，扫 `roll` 取 `欧拉步长 + |Y| 惩罚` 最小的一支"。它的代价函数
    **只看当前这根骨**、不看上一帧选了什么 roll ⟹ 上勾这种连续 10 帧都超
    `ROLL_COMFORT` 的快动作里，它会**逐帧改主意**：实测 `upperarm.R` 的 roll
    在 f19→f20 由 **+13° 跳到 −40°**、`hand.R` 由 **−36° 跳到 +21°**。
    roll 就是绕骨轴的扭转 ⟹ 世界旋转单帧 58.23°（`upperarm.R`），
    而拳峰只走了 132 mm —— 是**扭转变**，不是挥臂。
    连锁反应：前臂扭 58°、手的**世界朝向**只动 21° ⟹ 手的**局部**欧拉必须
    自己吃掉 66.7° 的差 ⟹ `hand.R` 局部欧拉单帧 52.094°（`no_teleport` 红）。

    修法：在代价里加 `ROLL_W·|roll − roll_prev|` —— **只惩罚"改主意"，
    不改判据**：搜索范围、`Y_SAFE`、`ROLL_COMFORT`、欧拉步长口径一字不改。
    """
    pose_bone = arm.pose.bones[name]
    prev_q = base_q if base_q is not None else JS.ARM_QUAT.get(name)
    if prev_q is None:
        prev_q = pose_bone.matrix.to_quaternion()
    want = Vector(direction).normalized()
    y_prev = (prev_q @ Vector((0.0, 1.0, 0.0))).normalized()
    q0 = y_prev.rotation_difference(want) @ prev_q

    prev_e = JS._PREV_EULER.get(name)
    roll_prev = _ROLL_PREV.get(name, 0.0)
    best_q = q0
    best_e = JS._unwrap_xyz(prev_e, JS._set_world_quat(arm, name, q0))
    step0 = JS._euler_step(prev_e, best_e)
    best_cost = step0 + JS._y_penalty(best_e) + ROLL_W * abs(roll_prev)
    best_roll = 0.0
    if prev_e is not None and (step0 > JS.ROLL_COMFORT
                               or JS._y_penalty(best_e) > 0.0):
        for roll in JS._frange(-JS.ROLL_RANGE, JS.ROLL_RANGE, JS.ROLL_COARSE):
            if abs(roll) <= 1e-9:
                continue
            q = Quaternion(want, math.radians(roll)) @ q0
            e = JS._unwrap_xyz(prev_e, JS._set_world_quat(arm, name, q))
            cost = (JS._euler_step(prev_e, e) + JS._y_penalty(e)
                    + ROLL_W * abs(roll - roll_prev))
            if cost < best_cost - 1e-9:
                best_cost, best_e, best_q, best_roll = cost, e, q, roll
        if best_roll != 0.0:
            for roll in JS._frange(best_roll - JS.ROLL_COARSE,
                                   best_roll + JS.ROLL_COARSE, JS.ROLL_FINE):
                q = Quaternion(want, math.radians(roll)) @ q0
                e = JS._unwrap_xyz(prev_e, JS._set_world_quat(arm, name, q))
                cost = (JS._euler_step(prev_e, e) + JS._y_penalty(e)
                        + ROLL_W * abs(roll - roll_prev))
                if cost < best_cost - 1e-9:
                    best_cost, best_e, best_q, best_roll = cost, e, q, roll
        JS._set_world_quat(arm, name, best_q)
    _ROLL_PREV[name] = best_roll
    JS.ARM_ROLL[name] = best_roll
    JS.ARM_QUAT[name] = best_q
    JS.ROLL_MAX[name] = max(JS.ROLL_MAX.get(name, 0.0), abs(best_roll))
    return best_e


# =============================================================== 姿态生成
_FROZEN_POSE = {}             # clock -> pose：命停窗口与收招平台**逐位复用同一姿态**
# ★ 命停 4 帧的"冻结"必须靠复用同一个解：f24~f27 是四次独立 IK 求解，
#   历史（`_PREV_EULER` / roll 搜索）各差一帧 ⟹ 会差 0.004° 的浮点噪声，
#   `hitstop_frozen_steps` 直接判成 0（B05 踩过）。
# ★ 收招平台（clock ≥ RECOVER_END）同理：只有**复用**才能保证末 4 帧步长恒为 0。


def _pin_flat(arm, pose, name):
    """把一根骨钉到"rest 朝向 + 绕世界 X 转 deg"（`WF.add_world_rx` 的封装）。

    先 `keep_world_orientation` 钉平（消掉父链外展带来的 4.3° 偏轴），
    再绕**世界 X** 叠角；`deg = 0` 时就是纯钉平。返回若干部问的 euler。
    """
    A.keep_world_orientation(arm, name)
    pose[name] = JS._unwrap_xyz(
        JS._PREV_EULER.get(name),
        tuple(math.degrees(v) for v in arm.pose.bones[name].rotation_euler))


def pin_with_tip(arm, pose, name, deg):
    """钉平后再绕世界 X 转 `deg`（踮脚/勾脚），并把结果写回 pose。"""
    A.keep_world_orientation(arm, name)
    WF.add_world_rx(arm, name, deg)
    pose[name] = JS._unwrap_xyz(
        JS._PREV_EULER.get(name),
        tuple(math.degrees(v) for v in arm.pose.bones[name].rotation_euler))


def build_pose(arm, frame, record=False):
    """按帧构造完整姿态（内部一律用 `clock(frame)` 驱动）。"""
    c = clock(frame)
    key = HIT if c == HIT else (RECOVER_END if c >= RECOVER_END else None)
    frozen = _FROZEN_POSE.get(key) if key is not None else None
    if frozen is not None:
        A.apply_pose(arm, frozen)
        if record:
            # ★ 必须用**该冻结姿态自己的 clock**（`key`），不能用 RECOVER_END 顶替：
            #   命中窗口的姿态是在 c = HIT 解出来的，用别的常量算目标会差几百 mm
            #   ⟹ `ik_reach_ok` 假红（B06 实测 624.942 mm，正是这个坑）。
            lift_z = ANKLE_SKIN_LIFT_RATIO * max(0.0, -chain6(*PELVIS_DZ, key))
            TARGETS.append((frame, SUPPORT,
                            tuple(tip_ankle(SUPPORT, tip_support(key))
                                  + Vector((0.0, 0.0, lift_z)))))
            TARGETS.append((frame, ATTACK,
                            tuple(ANKLE_REST[ATTACK] + ankle_offset(key)
                                  + Vector((0.0, 0.0, lift_z)))))
        _record_trace(arm, frame, frozen)
        return {k: (dict(v) if k == "@loc" else tuple(v))
                for k, v in frozen.items()}

    pose = trunk_pose(c)
    pose["toe.L"] = (0.0, 0.0, 0.0)
    pose["toe.R"] = (0.0, 0.0, 0.0)
    pose["@loc"] = {"pelvis": A.wloc(chain6(*PELVIS_DX, c), chain6(*PELVIS_DY, c),
                                     DROP + chain6(*PELVIS_DZ, c))}
    pose.update(A.FIST)
    A.apply_pose(arm, pose)

    pole_mark = len(POLE_SIN)

    # 蒙皮补偿：**只在下沉段**抬高踝目标（见常量表说明）。
    lift_z = ANKLE_SKIN_LIFT_RATIO * max(0.0, -chain6(*PELVIS_DZ, c))
    lift = Vector((0.0, 0.0, lift_z))

    # 支撑腿：目标 = 「鞋底最前缘滚动支点模型」算出的踝位（+蒙皮补偿）
    # ⟹ 接触点世界坐标逐帧不变（`support_foot_pinned_ok` 的构造保证）。
    target_support = tip_ankle(SUPPORT, tip_support(c)) + lift
    if record:
        TARGETS.append((frame, SUPPORT, tuple(target_support)))
    leg_aim(arm, pose, SUPPORT, target_support, _leg_pole(SUPPORT, c))

    # 攻击腿：地面段同样由滚动支点模型给出（贴地），离地段走世界轨。
    target_attack = ANKLE_REST[ATTACK] + ankle_offset(c) + lift
    if record:
        TARGETS.append((frame, ATTACK, tuple(target_attack)))
    leg_aim(arm, pose, ATTACK, target_attack, _leg_pole(ATTACK, c))

    # 足：
    #   支撑脚：绕**世界 X** 跖屈 `tip_support(c)`（正 = 脚尖压地），
    #           脚尖骨**不参与**（刚体脚，鞋底从最前缘往后整段抬起）。
    #   攻击脚：离地后脚尖跟脚背一起甩出去（相对角 12°→0），地面段脚尖**贴平**。
    pin_with_tip(arm, pose, "foot." + SUPPORT, tip_support(c))
    tip_a = tip_attack(c)
    ar = _ramp(c, TIP_ATTACK_AIRBORNE[0], TIP_ATTACK_AIRBORNE[1], 1.0)
    pin_with_tip(arm, pose, "foot." + ATTACK, tip_a)
    pin_with_tip(arm, pose, "toe." + ATTACK, -tip_a * (1.0 - ar))

    # 双臂：拳峰 = 各自的世界目标（躯干怎么动，拳就跟着这个世界目标走）。
    req_mark = len(REQ)
    for side in SIDES:
        arm_to(arm, pose, side, fist_target(side, c), hand_dir(side, c),
               _arm_pole(side, c))
    for i in range(pole_mark, len(POLE_SIN)):
        POLE_SIN[i] = (frame,) + POLE_SIN[i]
    for i in range(req_mark, len(REQ)):
        REQ[i] = (frame,) + REQ[i]

    _record_trace(arm, frame, pose)
    if c == HIT:
        _FROZEN_POSE[HIT] = {k: (dict(v) if k == "@loc" else tuple(v))
                             for k, v in pose.items()}
    if c == RECOVER_END:
        _FROZEN_POSE[RECOVER_END] = {k: (dict(v) if k == "@loc" else tuple(v))
                                     for k, v in pose.items()}
    return pose


def _leg_pole(side, c):
    """膝鼓出方向的**轨**：idle 实测 → `POLE_LATERAL`；权重 = 深蹲相位的 smoothstep。"""
    base = POLE_LEG.get(side)
    if base is None:
        return POLE_LATERAL[side]
    w = chamber_s(c)
    w = w * w * (3.0 - 2.0 * w)
    return tuple(base[i] + (POLE_LATERAL[side][i] - base[i]) * w
                 for i in range(3))


def _arm_pole(side, c):
    """肘鼓出方向的**轨**：idle 实测 → `POLE_ELBOW`（肘一路留在拳下方）。

    权重用**整条动作链的进度**（`chamber` 到位的瞬间即换向），因为上勾从
    蓄力第 6 帧起肘就已经开始往下压。
    """
    base = POLE_ARM.get(side)
    if base is None:
        return POLE_ELBOW[side]
    w = chamber_s(c)
    w = w * w * (3.0 - 2.0 * w)
    return tuple(base[i] + (POLE_ELBOW[side][i] - base[i]) * w
                 for i in range(3))


# =============================================================== 专属门禁
SEGMENTS = {
    "foot": ("foot.L", "foot.R", "toe.L", "toe.R"),
    "leg": ("thigh.L", "shin.L", "thigh.R", "shin.R"),
    "hip": ("pelvis",),
    "waist": ("spine_01", "spine_02", "chest"),
    "shoulder": ("shoulder.L", "shoulder.R"),
    "hand": ARM6,
}
SEGMENT_POINTS = {
    "foot": ("toe.L.tail", "toe.R.tail"),
    "leg": ("shin.L", "shin.R"),
    "hip": ("pelvis",),
    "waist": ("chest.tail",),
    "shoulder": ("upperarm.L", "upperarm.R"),
    "hand": ("hand.L.tail", "hand.R.tail"),
}
ATTACK_ARM = ARM_BONES[ATTACK]
GUARD_ARM = ARM_BONES[SUPPORT]


def _point_peak_frame(samples, keys):
    """该段**世界空间**运动速度的峰值帧（mm/帧）——欧拉步长会被万向节放大，不作时序尺子。"""
    best_frame, best = None, -1.0
    for index in range(1, len(samples)):
        before, after = samples[index - 1], samples[index]
        worst = 0.0
        for key in keys:
            if key in before and key in after:
                worst = max(worst, (Vector(after[key]) - Vector(before[key])).length)
        if worst > best:
            best, best_frame = worst, after["frame"]
    return best_frame, round(best * 1000.0, 3)


def _step_deg(samples, index):
    before, after = samples[index]["euler"], samples[index + 1]["euler"]
    worst = 0.0
    for name in set(before) | set(after):
        ea = before.get(name, (0.0, 0.0, 0.0))
        eb = after.get(name, (0.0, 0.0, 0.0))
        worst = max(worst, max(abs(a - b) for a, b in zip(ea, eb)))
    return worst


def uppercut_assertions(arm, action, samples, idle_mats, sole, ankles, reach,
                        target_err, contact):
    res = {}
    pelvis = [Vector(s["pelvis"]) for s in samples]
    fist = [Vector(s["hand." + ATTACK + ".tail"]) for s in samples]
    foot_s = [Vector(s["foot." + SUPPORT]) for s in samples]
    foot_a = [Vector(s["foot." + ATTACK]) for s in samples]
    chest_tail = [Vector(s["chest.tail"]) for s in samples]

    # 0) **首帧逐位 = `Idle_01@0`**（世界矩阵）；末帧**必须不回 idle**。
    m0 = CR.action_world_matrices(arm, action, 0)
    mN = CR.action_world_matrices(arm, action, TOTAL)
    d0, dN = CR.matrix_delta(m0, idle_mats), CR.matrix_delta(mN, idle_mats)
    res["first_frame_delta"] = float("%.3e" % d0)
    res["last_frame_delta"] = float("%.3e" % dN)
    res["guard_start_ok"] = bool(d0 <= 1e-6)
    res["end_pose_switched_ok"] = bool(dN > 1e-3)
    res["end_pose_note"] = ("B07 是单发普通攻击：首帧仍须逐位 = Idle_01@0（起手不闪），"
                            "末帧**停在自持的「上勾完」姿态**（拳在头侧上方、重心已落回）")

    # 1) **末帧保持**：末 4 帧姿态变化 ≤2°。
    hold = [round(_step_deg(samples, i), 4)
            for i in range(len(samples) - 5, len(samples) - 1)]
    res["end_hold_steps_deg"] = hold
    res["end_pose_hold_ok"] = bool(max(hold) <= 2.0 and dN > 1e-3)

    # 2) **`crouch_ok`**（本支的"前摇"是**深蹲蓄力**）：窗口 [1, CROUCH_END] 内
    #    骨盆最低点必须比 guard 低 ≥150 mm，且最低点确实落在窗口内。
    #    ★ 窗口从 f1 起（不含 f0）：B03 已记「窗口含 f0 且 f0 按定义 = 0 ⟹ 任何
    #      前摇都被判"没蓄力"」的陷阱。
    win = range(1, ANTIC_END + 1)
    z0 = pelvis[0].z * 1000.0
    low_i = min(win, key=lambda i: pelvis[i].z)
    res["antic_window_frames"] = ANTIC_END
    res["crouch_pelvis_z_mm"] = round(pelvis[low_i].z * 1000.0, 1)
    res["crouch_drop_mm"] = round(z0 - pelvis[low_i].z * 1000.0, 1)
    res["crouch_min_frame"] = samples[low_i]["frame"]
    res["crouch_ok"] = bool(ANTIC_END >= 8
                            and z0 - pelvis[low_i].z * 1000.0 >= CROUCH_MIN_MM)

    # 3) **`rise_ok`**（本支核心，新写）：命中帧骨盆 z − guard ≥ +120 mm，
    #    且全程 `min(pelvis z)` **出现在 [1, CROUCH_END]**（先沉后升的顺序必须对，
    #    防"只升不沉"的假满足）。
    hit_z = pelvis[HIT].z * 1000.0
    all_min_i = min(range(len(pelvis)), key=lambda i: pelvis[i].z)
    res["hit_pelvis_z_mm"] = round(hit_z, 1)
    res["rise_mm"] = round(hit_z - z0, 1)
    res["rise_min_mm"] = RISE_MIN_MM
    res["pelvis_min_z_mm"] = round(pelvis[all_min_i].z * 1000.0, 1)
    res["pelvis_min_frame"] = samples[all_min_i]["frame"]
    res["pelvis_z_series_mm"] = [round(p.z * 1000.0, 1) for p in pelvis]
    res["rise_order_ok"] = bool(1 <= samples[all_min_i]["frame"] <= ANTIC_END)
    res["rise_ok"] = bool(hit_z - z0 >= RISE_MIN_MM and res["rise_order_ok"])
    res["rise_note"] = ("上升靠腿的蹬伸做出来（普通攻击不许 Root Motion）："
                        "膝伸直 + 踝跖屈（支撑脚绕鞋底最前缘滚到 32°）+ 髋前送 135 mm")

    # 4) **`uppercut_height_ok`**：命中帧拳峰 z ≥ 1800（比 B05 的 1735.4 更高 ——
    #    上勾是"往上打"）+ 命中帧拳峰**在骨盆前方**（`fist.y < pelvis.y`，防"打成举手"）。
    res["hit_fist_z_mm"] = round(fist[HIT].z * 1000.0, 1)
    res["hit_fist_y_mm"] = round(fist[HIT].y * 1000.0, 1)
    res["hit_pelvis_y_mm"] = round(pelvis[HIT].y * 1000.0, 1)
    res["fist_guard_z_mm"] = round(fist[0].z * 1000.0, 1)
    res["fist_peak_z_mm"] = round(max(p.z for p in fist) * 1000.0, 1)
    res["above_b05_mm"] = round(fist[HIT].z * 1000.0 - B05_HIT_FIST_Z_MM, 1)
    res["fist_in_front_ok"] = bool(fist[HIT].y < pelvis[HIT].y)
    res["uppercut_height_ok"] = bool(fist[HIT].z * 1000.0 >= UPPERCUT_HEIGHT_MIN_MM
                                      and res["fist_in_front_ok"])

    # 5) **`hip_drive_ok`**：命中帧骨盆前送 `−y` ≥ 60 mm（髋把重心往前上送）。
    res["hit_pelvis_forward_mm"] = round(-pelvis[HIT].y * 1000.0, 1)
    res["hip_drive_min_mm"] = HIP_DRIVE_MIN_MM
    res["hip_drive_ok"] = bool(-pelvis[HIT].y * 1000.0 >= HIP_DRIVE_MIN_MM
                               and pelvis[HIT].y < pelvis[0].y)

    # 6) **`knee_extend_ok`**：单侧（攻击腿）膝角从**深蹲底**到**命中帧**伸展 ≥55°。
    #    ★ 口径：`CR.knee_series` 返 `180 − 内角`（大 = 弯、小 = 直），
    #      所以"伸展量" = 深蹲底的值 − 命中帧的值。
    bend = CR.knee_series(arm, action, [s["frame"] for s in samples])
    span_a = bend[low_i][ATTACK] - bend[HIT][ATTACK]
    span_s = bend[low_i][SUPPORT] - bend[HIT][SUPPORT]
    res["attack_knee_bend_series_deg"] = [round(b[ATTACK], 2) for b in bend]
    res["attack_knee_crouch_deg"] = round(bend[low_i][ATTACK], 2)
    res["attack_knee_hit_deg"] = round(bend[HIT][ATTACK], 2)
    res["attack_knee_extend_deg"] = round(span_a, 2)
    res["support_knee_extend_deg"] = round(span_s, 2)
    res["knee_extend_min_deg"] = KNEE_EXTEND_MIN_DEG
    res["knee_extend_b06_reference_deg"] = B06_ATTACK_KNEE_SPAN
    res["knee_extend_ok"] = bool(span_a >= KNEE_EXTEND_MIN_DEG)

    # 7) **`ground_contact_ok`（拆两侧写）**：支撑脚必须 −2~+6；攻击脚允许离地。
    sole_s = [sole[i][SUPPORT] * 1000.0 for i in range(len(sole))]
    sole_a = [sole[i][ATTACK] * 1000.0 for i in range(len(sole))]
    res["support_sole_min_mm"] = round(min(sole_s), 2)
    res["support_sole_max_mm"] = round(max(sole_s), 2)
    res["support_sole_series_mm"] = [round(v, 2) for v in sole_s]
    res["attack_sole_min_mm"] = round(min(sole_a), 2)
    res["attack_sole_max_mm"] = round(max(sole_a), 2)
    res["attack_sole_series_mm"] = [round(v, 2) for v in sole_a]
    res["ground_min_mm_all_sides"] = round(min(min(sole_s), min(sole_a)), 2)
    res["ground_contact_ok"] = bool(-2.0 <= min(sole_s) and max(sole_s) <= 6.0)
    res["ground_contact_note"] = ("口径改（计划原文指定）：**拆两侧写** —— "
                                  "支撑脚 L 必须 −2~+6 mm，**攻击脚 R 允许离地蹬伸**；"
                                  "B04~B06 的 `min(L, R)` 一刀切在本支必假红")

    # 8) **`support_foot_pinned_ok`**（本支核心，口径改）：支撑脚**接触点**
    #    （= 鞋**最低顶点**，滚动时唯一的着地点）的水平位移 ≤3 mm。
    #    ★ 不是"踝不动"：提踵时踝本就要走 100+ mm（见文件头第 1 件）。
    #    ★ 也不是"最低层里最前的顶点"：鞋头上翘，那个点不是接触点（实测假红 6.13）。
    drift_xy = [math.hypot(contact[i][0] - contact[0][0],
                           contact[i][1] - contact[0][1]) * 1000.0
                for i in range(len(contact))]
    res["support_contact_drift_mm"] = round(max(drift_xy), 4)
    res["support_contact_drift_series_mm"] = [round(v, 3) for v in drift_xy]
    res["support_contact_point_f0_mm"] = [round(v * 1000.0, 2) for v in contact[0]]
    res["support_ankle_travel_mm"] = round(
        max((foot_s[i] - foot_s[0]).length for i in range(len(foot_s))) * 1000.0, 2)
    res["support_foot_pinned_ok"] = bool(max(drift_xy) <= 3.0)
    res["support_foot_note"] = ("口径改：本支支撑脚**必须提踵**（重心上升的唯一来源），"
                                "所以钉的不是踝，而是**接触点 = 鞋最低顶点**"
                                "（纯滚动的着地点；绕世界 X 转不动 x，故只看 y 漂移）")

    # 9) **`trunk_extend_ok`**（本支独有）：躯干由**前屈**（深蹲）转到**伸展**（命中）。
    #    ★ 判据站**物理方向**：骨盆→胸骨顶的矢状仰角 `atan2(Δy, Δz)`，
    #      + = 后仰/伸展，− = 前屈。欧拉 rx 受 ry/rz 污染（B06 第 3 件），只作诊断。
    def _lean(index):
        base, top = pelvis[index], chest_tail[index]
        return math.degrees(math.atan2(top.y - base.y, top.z - base.z))

    lean_c, lean_h = _lean(low_i), _lean(HIT)
    res["trunk_lean_crouch_deg"] = round(lean_c, 2)
    res["trunk_lean_hit_deg"] = round(lean_h, 2)
    res["trunk_extend_deg"] = round(lean_h - lean_c, 2)
    res["trunk_extend_min_deg"] = TRUNK_EXTEND_MIN_DEG
    res["trunk_lean_series_deg"] = [round(_lean(i), 2) for i in range(len(samples))]
    res["trunk_extend_measure"] = ("物理量：骨盆→胸骨顶矢状仰角（+ = 伸展/后仰）。"
                                   "窗口 = [深蹲底, HIT]")
    res["trunk_extend_ok"] = bool(lean_h - lean_c >= TRUNK_EXTEND_MIN_DEG)

    # 10) **`fist_travel_ok`**：攻击拳的世界行程（弧长）≥900 mm（上勾的大弧）。
    path = sum((fist[i] - fist[i - 1]).length
               for i in range(1, len(fist))) * 1000.0
    chord = max((p - fist[0]).length for p in fist) * 1000.0
    res["fist_path_len_mm"] = round(path, 1)
    res["fist_travel_chord_mm"] = round(chord, 1)
    res["fist_travel_min_mm"] = FIST_TRAVEL_MIN_MM
    res["fist_travel_ok"] = bool(path >= FIST_TRAVEL_MIN_MM)

    # 11) **`body_follow_through_ok`**：打透 = 命停之后**继续上送 + 继续伸展**。
    #     窗口与 `follow_s` 相位对齐（`follow_s` 在 clock 24→30 由 0 升到 1，
    #     clock = frame − HOLD ⟹ 峰值落在 f33）。
    ft_lo, ft_hi = HIT + HOLD + 1, FOLLOW_END + HOLD          # [28, 33]
    ft = {}
    ft["fist_z_mm"] = [round(fist[HIT].z * 1000.0, 1),
                       round(max(fist[i].z for i in range(ft_lo, ft_hi + 1)) * 1000.0, 1)]
    ft["fist_z_mm"].append(round(ft["fist_z_mm"][1] - ft["fist_z_mm"][0], 1))
    ft["pelvis_z_mm"] = [round(pelvis[HIT].z * 1000.0, 1),
                         round(max(pelvis[i].z
                                   for i in range(ft_lo, ft_hi + 1)) * 1000.0, 1)]
    ft["pelvis_z_mm"].append(round(ft["pelvis_z_mm"][1] - ft["pelvis_z_mm"][0], 1))
    ft["trunk_lean_deg"] = [round(_lean(HIT), 2),
                            round(max(_lean(i) for i in range(ft_lo, ft_hi + 1)), 2)]
    ft["trunk_lean_deg"].append(
        round(ft["trunk_lean_deg"][1] - ft["trunk_lean_deg"][0], 2))
    res["follow_through"] = ft
    res["follow_through_window"] = [ft_lo, ft_hi]
    res["follow_through_measure"] = "拳峰 z / 骨盆 z / 躯干仰角，三者都取「命停后的窗口内峰值」"
    res["body_follow_through_ok"] = bool(ft["fist_z_mm"][2] >= 30.0
                                         and ft["pelvis_z_mm"][2] >= 2.0
                                         and ft["trunk_lean_deg"][2] >= 2.0)

    # 12) **打击停顿 4 帧**（冻结判据的数值地板 1e-3，B04 第 6 件）。
    FROZEN_EPS_DEG = 1e-3
    steps, cursor = 0, HIT
    while cursor + 1 <= HIT + HOLD:
        if _step_deg(samples, cursor) > FROZEN_EPS_DEG:
            break
        steps += 1
        cursor += 1
    res["hitstop_frozen_steps"] = steps
    res["hitstop_frames"] = steps + 1
    res["hitstop_window"] = [HIT, HIT + HOLD]
    res["hitstop_present"] = bool(steps + 1 == HOLD + 1)

    # 13) **可取消帧**：f34 有 marker，且该帧身体确在**回收路径**上
    #     （骨盆已从命中峰值往下走，但仍在 guard 之上）。
    markers = {m.name: int(m.frame) for m in action.pose_markers}
    res["markers"] = markers
    res["cancel_pelvis_z_mm"] = [round(pelvis[0].z * 1000.0, 1),
                                 round(pelvis[CANCEL].z * 1000.0, 1),
                                 round(pelvis[HIT].z * 1000.0, 1)]
    res["cancel_marker_ok"] = bool(markers.get("CANCEL") == CANCEL
                                   and pelvis[0].z < pelvis[CANCEL].z < pelvis[HIT].z)

    # 14) 肢体 |Y| 健康度（体检项，**不当门禁**）。
    max_y = max(max(abs(samples[i]["euler"].get(b, (0., 0., 0.))[1])
                    for b in ARM6 + LEG6) for i in range(len(samples)))
    res["max_abs_euler_y_deg"] = round(max_y, 2)
    res["euler_y_is_health_check_only"] = True

    # 15) **六段力量传导**（口径见文件头第 3 件）。
    ranges = {}
    for segment, bones in SEGMENTS.items():
        ranges[segment] = round(L1._euler_range(samples, bones), 3)
    attack_arm_range = round(L1._euler_range(samples, ATTACK_ARM), 3)
    guard_arm_range = round(L1._euler_range(samples, GUARD_ARM), 3)
    res["power_chain_ranges_deg"] = ranges
    res["power_chain_b06_ranges_deg"] = B06_SEGMENT_RANGES
    res["power_chain_same_quantity_as_b06"] = list(B06_STRICT)
    res["power_chain_vs_b06"] = {
        k: round(ranges[k] - B06_SEGMENT_RANGES[k], 2) for k in ranges}
    res["power_chain_over_b06"] = {k: bool(ranges[k] > B06_SEGMENT_RANGES[k])
                                   for k in B06_STRICT}
    # ★ 攻击臂"占优"的尺子换成**世界行程（弧长）**，不用欧拉幅度：
    #   本支两条臂的前臂 z 都在 ±180 附近、|Y| 越过 `Y_SAFE`，欧拉幅度被万向节
    #   放大成 175.47° vs 171.34°（几乎相等）—— 那是**表示**问题，不是动作问题。
    #   物理量：攻击拳峰世界弧长 / 护手拳峰世界弧长（B05 第 1 件、B06 第 3 件同款结论）。
    guard_hand = [Vector(s["hand." + SUPPORT + ".tail"]) for s in samples]
    guard_path = sum((guard_hand[i] - guard_hand[i - 1]).length
                     for i in range(1, len(guard_hand))) * 1000.0
    res["attack_arm_euler_range_diagnostic"] = attack_arm_range
    res["guard_arm_euler_range_diagnostic"] = guard_arm_range
    res["attack_arm_path_mm"] = round(path, 1)
    res["guard_arm_path_mm"] = round(guard_path, 1)
    res["attack_arm_dominates"] = bool(path > guard_path * 1.5)
    res["attack_arm_dominates_measure"] = ("世界弧长（mm）：攻击拳峰 > 护手拳峰 ×1.5。"
                                           "欧拉幅度在此支不可用（±180 / |Y|>62 会被放大）")
    res["power_chain_all_segments_alive"] = {k: bool(ranges[k] >= 3.0)
                                            for k in ranges}
    res["support_tip_span_deg"] = round(max(TIP_SUPPORT) - min(TIP_SUPPORT), 2)
    res["tip_min_deg"] = TIP_MIN_DEG
    res["power_chain_note"] = (
        "B07 是**上勾拳**（腿蹬伸驱动 + 手臂上勾）：`leg` / `hip` 两段与 B06 "
        "**同一物理量**（腿部通道幅度 / 髋通道幅度）⟹ **严格要求 > 84.788 / 12.0**；"
        "`foot` **不与 B06 比** —— 踢击甩脚背（76.293）与本支的填脚跖屈不是同一物理量，"
        "只要求非退化 + 踮脚 ≥12°；`waist`/`shoulder`/`hand` 非退化 + 时序 + "
        "攻击臂占优（> 护手臂 ×1.5）。**换尺子，不是放宽**：六段数值全部照实列出。")
    # ★ 这是**全程**峰值帧（含收招段），**诊断用、不是判据**。
    res["power_chain_peak_frames_all_range_diagnostic"] = {
        seg: _point_peak_frame(samples, SEGMENT_POINTS[seg])[0] for seg in SEGMENTS}

    # 15b) **时序**：发力窗口 [0, HIT+HOLD] 内，按**近端→远端**依次达峰
    #      （骨盆 → 膝 → 踝 → 拳），且拳峰必须落在命中帧附近。
    def _peak_in(keys, lo, hi):
        best_frame, best = None, -1.0
        for index in range(1, len(samples)):
            frame = samples[index]["frame"]
            if not (lo <= frame <= hi):
                continue
            worst = 0.0
            for key in keys:
                if key in samples[index - 1] and key in samples[index]:
                    worst = max(worst, (Vector(samples[index][key])
                                        - Vector(samples[index - 1][key])).length)
            if worst > best:
                best, best_frame = worst, frame
        return best_frame, round(best * 1000.0, 2)

    win_lo, win_hi = 0, HIT + HOLD
    p_pelvis = _peak_in(("pelvis",), win_lo, win_hi)
    p_knee = _peak_in(("shin." + ATTACK,), win_lo, win_hi)
    p_ankle = _peak_in(("foot." + ATTACK,), win_lo, win_hi)
    p_fist = _peak_in(("hand." + ATTACK + ".tail",), win_lo, win_hi)
    res["timing_window"] = [win_lo, win_hi]
    res["timing_peak_frames"] = {"pelvis": p_pelvis[0], "knee": p_knee[0],
                                 "ankle": p_ankle[0], "fist": p_fist[0]}
    res["timing_peak_speed_mm_per_frame"] = {"pelvis": p_pelvis[1],
                                             "knee": p_knee[1],
                                             "ankle": p_ankle[1],
                                             "fist": p_fist[1]}
    timing = (p_pelvis[0] <= p_knee[0] + 1
              and p_knee[0] <= p_ankle[0] + 1
              and p_ankle[0] <= p_fist[0] + 1
              and HIT - 3 <= p_fist[0] <= HIT + 1)
    res["power_chain_timing_measure"] = (
        "世界空间速度峰值帧（欧拉步长会被万向节放大，不作时序尺子）；"
        "窗口 = [0, HIT+HOLD]（只取发力段，排除收招段的速度峰）；"
        "顺序 = 骨盆 ≤ 膝 ≤ 踝 ≤ 拳，且拳峰落在 [HIT−3, HIT+1]")
    res["power_chain_timing_ok"] = bool(timing)
    res["power_chain_ok"] = bool(
        timing
        and res["attack_arm_dominates"]
        and all(ranges[k] > B06_SEGMENT_RANGES[k] for k in B06_STRICT)
        and all(ranges[k] >= 3.0 for k in ranges)
        and res["support_tip_span_deg"] >= TIP_MIN_DEG)

    # 15c) 诊断：逐骨逐通道 euler 幅度。
    limb_ranges = {}
    for name in ARM6 + LEG6:
        vals = [[s["euler"].get(name, (0.0, 0.0, 0.0))[ch] for s in samples]
                for ch in range(3)]
        limb_ranges[name] = [round(max(v) - min(v), 2) for v in vals]
    res["limb_euler_ranges_deg"] = limb_ranges
    res["limb_euler_range_max"] = round(max(max(v) for v in limb_ranges.values()), 3)
    res["limb_euler_range_max_at"] = max(
        ((max(v), n, "xyz"[v.index(max(v))]) for n, v in limb_ranges.items()))

    # 15d) 诊断：逐帧最大欧拉步长**排行**（`no_teleport` 红时直接在这里定位）。
    #      口径与 `anim_lib` 的 `max_frame_step_deg` 一字不差（同一套 `samples["euler"]`）。
    scan = []
    for index in range(1, len(samples)):
        before, after = samples[index - 1]["euler"], samples[index]["euler"]
        worst_step, worst_bone = 0.0, None
        for name in set(before) | set(after):
            ea = before.get(name, (0.0, 0.0, 0.0))
            eb = after.get(name, (0.0, 0.0, 0.0))
            step = max(abs(a - b) for a, b in zip(ea, eb))
            if step > worst_step:
                worst_step, worst_bone = step, name
        scan.append([samples[index]["frame"], worst_bone, round(worst_step, 2)])
    res["step_scan_top"] = sorted(scan, key=lambda r: -r[2])[:10]
    res["forearm_L_euler_series"] = [
        [s["frame"]] + [round(v, 2) for v in s["euler"].get("forearm.L", (0, 0, 0))]
        for s in samples]

    # 16) **收招不许瞬停**：末 6 帧最大欧拉增量单调收敛 + 末步 ≤5°。
    deltas, tail_bones = [], []
    for index in range(len(samples) - 6, len(samples)):
        before, after = samples[index - 1]["euler"], samples[index]["euler"]
        worst_step, worst_bone = 0.0, None
        for name in set(before) | set(after):
            ea = before.get(name, (0.0, 0.0, 0.0))
            eb = after.get(name, (0.0, 0.0, 0.0))
            step = max(abs(a - b) for a, b in zip(ea, eb))
            if step > worst_step:
                worst_step, worst_bone = step, name
        deltas.append(round(worst_step, 5))
        tail_bones.append(worst_bone)
    res["tail_deg_per_frame"] = deltas
    res["tail_worst_bone"] = tail_bones
    res["decel_smooth_ok"] = bool(all(deltas[i + 1] <= deltas[i] + 1e-9
                                      for i in range(len(deltas) - 1)))
    res["no_snap_stop_ok"] = bool(deltas[-1] <= 5.0 and deltas[-1] <= deltas[0])

    peak_frame, peak_val = L1._peak_frame(samples, ARM6 + LEG6)
    res["limb_peak_step_frame"] = peak_frame
    res["limb_peak_step_deg"] = peak_val
    res["recover_first_step_deg"] = round(_step_deg(samples, HIT + HOLD), 3)
    res["burst_last_step_deg"] = round(_step_deg(samples, HIT - 1), 3)
    res["no_teleport_budget_left_deg"] = round(25.0 - peak_val, 3)

    # 17) IK 到位 / 腿可达余量（体检）。
    res["ankle_target_error_mm"] = round(target_err * 1000.0, 3)
    res["ik_reach_ok"] = bool(target_err * 1000.0 <= 5.0)
    limit = A.L_THIGH + A.L_SHIN
    res["leg_reach_max_mm"] = {s: round(max(r[s] for r in reach) * 1000.0, 1)
                               for s in SIDES}
    res["leg_reach_headroom_mm"] = {
        s: round((limit - max(r[s] for r in reach)) * 1000.0, 1) for s in SIDES}
    res["leg_reach_ok"] = bool(all(limit - max(r[s] for r in reach) >= 0.0
                                   for s in SIDES))
    res["leg_extension_max"] = {
        s: round(max(r for side, r in REACH if side == s), 4) for s in SIDES}

    # 18) 攻击元数据登记。
    res["antic_frame"] = ANTIC_END
    res["hit_frame"] = HIT
    res["cancel_frame"] = CANCEL
    res["hitstop_frame_span"] = [HIT, HIT + HOLD]
    return res


# =============================================================== 主流程
I1_FIST_GUARD = {}


def contact_series(arm, action, frames, side):
    """逐帧跟踪支撑脚**支点那个材料顶点**的世界位置 —— 滑移判据的尺子。

    ★ 为什么钉**固定材料顶点**：绕支点刚性滚动 = 纯转动，该点世界坐标逐位不变；
      只要脚发生平移（滑移），它立刻漂。提踵时踝必走 160 mm，所以不能钉踝
      （B06 口径）；也不能钉"最低点"（平底上会身份乱跳：实测假漂移 25~93 mm）。
    """
    scene = bpy.context.scene
    previous = arm.animation_data.action if arm.animation_data else None
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    object_name, index = SOLE_PIVOT_ID[side]
    out = []
    for frame in frames:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        point = vertex_world(object_name, index)
        out.append(tuple(point) if point is not None else (0.0, 0.0, 0.0))
    if previous is not None:
        arm.animation_data.action = previous
    return out


def main():
    global ANKLE_REST, SOLE_TIP, IDLE_POSE, POLE_LEG, POLE_ARM
    global HAND_GUARD, O_ARM_GUARD, A_TRACK, I1_FIST_GUARD
    global SOLE_PTS, SOLE_ZMIN

    arm, meshes = A.open_animation_project()
    A.setup_scene()

    if "Idle_01" not in bpy.data.actions:
        print("UP07_BOOTSTRAP 动画工程缺 Idle_01，先补跑 A01")
        I1.main()
        arm, meshes = A.open_animation_project()
        A.setup_scene()

    # ---- 定盘数：一律从 `Idle_01@0` 成品姿态读，不手抄。
    IDLE_POSE = I1.idle_pose(arm, 0.0)
    ANKLE_REST = {side: Vector(A.bone_world(arm, "foot." + side, "head"))
                  for side in SIDES}
    POLE_LEG = {side: _leg_pole_from_pose(arm, side) for side in SIDES}
    POLE_ARM = {side: _elbow_pole_from_pose(arm, side) for side in SIDES}
    HAND_GUARD = {side: tuple(A.bone_direction(arm, "hand." + side))
                  for side in SIDES}
    fist_guard = {s: Vector(A.bone_world(arm, "hand." + s, "tail")) for s in SIDES}
    shoulder_guard = {s: Vector(A.bone_world(arm, "upperarm." + s, "head"))
                      for s in SIDES}
    O_ARM_GUARD = {s: fist_guard[s] - shoulder_guard[s] for s in SIDES}
    knee_guard = {s: Vector(A.bone_world(arm, "shin." + s, "head")) for s in SIDES}
    # ★ 滚动支点：支撑脚鞋底**最低 6 mm 层里最靠前**的顶点（实测，不猜），
    #   连**顶点序号**一起记住 —— 提踵时"最低点"会身份乱跳，滑移判据必须钉材料点。
    #   ★ 同时留下**整只鞋**的顶点云（`SOLE_PTS`）与最低点（`SOLE_ZMIN`）：
    #     `tip_ankle` 要靠它把"转动后鞋底最低点"拉回地面（见 `tip_ankle` 说明）。
    SOLE_PIVOT = {}
    for side in SIDES:
        rows = foot_sole_points(side)
        SOLE_PTS[side] = [row[2] for row in rows]
        SOLE_ZMIN[side] = (min(p.z for p in SOLE_PTS[side]) if SOLE_PTS[side]
                           else ANKLE_REST[side].z - 0.0787)
        SOLE_PIVOT[side] = foot_pivot_vertex(rows)
        if SOLE_PIVOT[side] is None:
            SOLE_PIVOT[side] = ("", 0,
                                ANKLE_REST[side] + Vector((0.0, -0.201, -0.0787)))
        SOLE_TIP[side] = SOLE_PIVOT[side][2]
        SOLE_PIVOT_ID[side] = (SOLE_PIVOT[side][0], SOLE_PIVOT[side][1])

    # 拳峰世界目标 = `I1_FIST_GUARD`（实测的 guard 拳位）+ `FIST_TRACK` 的**偏移**。
    # ★★ 所以 `FIST_TRACK` 的 guard 列必须是 **(0,0,0)** —— 首版把它覆写成
    #    实测的**绝对**拳位，等于把 guard 算了两遍：f1 的拳峰目标被顶到 z = 2.32 m
    #    （头顶以上），手臂整条向上翻 133°（`no_teleport` 红 + 拳峰峰值落在 f1
    #    ⟹ `power_chain_timing_ok` 红）。**轨迹表的第 0 列是偏移，不是位置。**
    I1_FIST_GUARD = {s: tuple(fist_guard[s]) for s in SIDES}

    # ★ 攻击臂的肩相对弧端点（必须在 `I1_FIST_GUARD` / 躯干常数就位之后）。
    global _REACH_MM
    _REACH_MM = (bone_len(arm, "upperarm." + ATTACK)
                 + bone_len(arm, "forearm." + ATTACK)) * 1000.0
    arc = build_arc_table(arm)
    A.report("UP07_ARC", {
        "side": ARC_SIDE, "pow": ARC_POW,
        "rel_a_mm": [round(v * 1000.0, 1) for v in arc[ARC_SIDE][0]],
        "rel_b_mm": [round(v * 1000.0, 1) for v in arc[ARC_SIDE][1]],
        "rel_a_len_mm": round(arc[ARC_SIDE][0].length * 1000.0, 1),
        "rel_b_len_mm": round(arc[ARC_SIDE][1].length * 1000.0, 1),
        "arm_len_mm": round((bone_len(arm, "upperarm." + ARC_SIDE)
                             + bone_len(arm, "forearm." + ARC_SIDE)) * 1000.0, 1),
        "note": "弧的两端「拳−肩」向量：半径远大于折叠下界(FOLD_MIN_RATIO×臂长)，"
                "所以 14→24 段拳到肩的距离恒在环带内，`arm_to` 不夹。",
    })

    # ★ 攻击踝的世界偏移轨：贴地两列由滚动支点模型算出（见文件头第 1 件）。
    A_TRACK = (
        (0.0, 0.0, 0.0),
        tuple(tip_ankle(ATTACK, TIP_ATTACK_LOAD) - ANKLE_REST[ATTACK]),
        tuple(tip_ankle(ATTACK, TIP_ATTACK_CROUCH) - ANKLE_REST[ATTACK]),
        A_TRACK_STRIKE,
        A_TRACK_FOLLOW,
        (0.0, 0.0, 0.0),
    )

    A.report("UP07_IDLE_TRUTH", {
        "support": SUPPORT, "attack": ATTACK,
        "front_foot": "L" if ANKLE_REST["L"].y < ANKLE_REST["R"].y else "R",
        "pelvis_z_mm": round(Vector(A.bone_world(arm, "pelvis", "head")).z * 1000.0, 1),
        "ankle_mm": {s: [round(v * 1000.0, 2) for v in ANKLE_REST[s]] for s in SIDES},
        "sole_tip_mm": {s: [round(v * 1000.0, 2) for v in SOLE_TIP[s]] for s in SIDES},
        "sole_tip_offset_mm": {s: [round(v * 1000.0, 2)
                                   for v in (SOLE_TIP[s] - ANKLE_REST[s])]
                               for s in SIDES},
        "knee_mm": {s: [round(v * 1000.0, 1) for v in knee_guard[s]] for s in SIDES},
        "leg_pole_mm": {s: [round(v * 1000.0, 1) for v in POLE_LEG[s]] for s in SIDES},
        "hand_dir": {s: [round(v, 4) for v in HAND_GUARD[s]] for s in SIDES},
        "arm_guard_offset_mm": {s: [round(v * 1000.0, 1) for v in O_ARM_GUARD[s]]
                                for s in SIDES},
        "leg_units_mm": round((A.L_THIGH + A.L_SHIN) * 1000.0, 1),
        "idle_hip_ankle_mm": {s: round((ANKLE_REST[s]
                                        - Vector(A.bone_world(arm, "thigh." + s, "head"))
                                        ).length * 1000.0, 1) for s in SIDES},
        "attack_track_ground_mm": {
            "load": [round(v * 1000.0, 2) for v in A_TRACK[1]],
            "crouch": [round(v * 1000.0, 2) for v in A_TRACK[2]]},
        "note": ("上勾拳：**后腿 R 驱动**（清单原文）。攻击侧 = R（后腿 R + 后手 R）；"
                 "支撑脚 = 前脚 L（绕**鞋底最前缘**滚动提踵，接触点钉死）。"
                 "命中帧攻击腿必须**离地**（骨盆前送后髋→后踝 ≥820 mm，够不到地面）。"),
    })

    # ★ 支撑脚踮脚的**几何预演**：把滚动支点模型给出的踝高直接报出来，
    #   和 `rise_ok` 的天花板一起核对（先量再做，不许拍脑袋）。
    preview = []
    for tip in (0.0, 10.0, 20.0, 30.0, 32.0, 35.0):
        ank = tip_ankle(SUPPORT, tip)
        preview.append({"tip_deg": tip,
                        "ankle_z_mm": round(ank.z * 1000.0, 1),
                        "ankle_y_mm": round(ank.y * 1000.0, 1)})
    A.report("UP07_TIP_MODEL", {
        "pivot_mm": [round(v * 1000.0, 2) for v in SOLE_TIP[SUPPORT]],
        "pivot_vertex_id": [SOLE_PIVOT_ID[SUPPORT][0], SOLE_PIVOT_ID[SUPPORT][1]],
        "support_ankle_by_tip": preview,
        "hit_tip_deg": TIP_SUPPORT[3],
        "note": ("模型 = **绕「鞋底最低 6 mm 层里最靠前」的材料顶点刚性转动**"
                 "（不用「整块最低点」：平底上滚动时最低点会身份乱跳，产生 25~93 mm 假漂移；"
                 "也不用鞋头上翘处的前缘：绕它会悬空 9.12 mm）。"
                 "命中帧 32° 时踝 z 约 178 mm ⟹ 髋→踝 ~800 mm ⟹ rise +135"),
    })

    # ---- 正式生成：首帧整帧取 `Idle_01@0`，其后逐帧 IK 构造。
    #      ★★ 沿用 B04 第 1 件：**不覆写 `JS.Y_SAFE` / `JS.ROLL_COMFORT`**，用库默认。
    JS._PREV_EULER.clear()
    for name, value in IDLE_POSE.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)
    JS.ARM_QUAT.clear()
    JS.ARM_ROLL.clear()
    JS.ROLL_MAX.clear()
    for name in ARM6 + LEG6:
        JS.ARM_QUAT[name] = arm.pose.bones[name].matrix.to_quaternion()
    del TARGETS[:]
    del TRACE[:]
    del REACH[:]
    del POLE_SIN[:]
    del REQ[:]
    _BULGE_PREV.clear()
    _FROZEN_POSE.clear()
    _ROLL_PREV.clear()

    keyframes = [(0, IDLE_POSE)]
    # 记下种子（诊断用：若某根臂骨不在种子里，第 1 帧就会"从零开始"）。
    seeded = {b: (b in JS._PREV_EULER) for b in ARM6}
    seeded_quat = {b: (b in JS.ARM_QUAT) for b in ARM6}
    HEAD_DIR = {"f0": {b: tuple(A.bone_direction(arm, b)) for b in ARM6}}
    for frame in range(1, TOTAL + 1):
        keyframes.append((frame, build_pose(arm, frame, record=True)))
        if frame <= 2:
            HEAD_DIR["f%d" % frame] = {b: tuple(A.bone_direction(arm, b))
                                       for b in ARM6}

    euler_y = {b: max(abs(row["euler"][b][1]) for row in TRACE) for b in ARM6 + LEG6}
    # ★ 首几帧的手臂欧拉（**诊断 `no_teleport` 的 f1 跳变**）：首帧 = `Idle_01@0`，
    #   第 2 帧必须只动一点点；若这里看到 ±180 级别的差，就是**表示分支**跳了。
    A.report("UP07_HEAD_EULER", {
        "f0_idle": {b: [round(v, 3) for v in IDLE_POSE.get(b, (0.0, 0.0, 0.0))]
                    for b in ARM6},
        "f1": {b: [round(v, 3) for v in TRACE[0]["euler"].get(b, (0.0, 0.0, 0.0))]
               for b in ARM6},
        "f2": {b: [round(v, 3) for v in TRACE[1]["euler"].get(b, (0.0, 0.0, 0.0))]
               for b in ARM6},
        "f1_roll": TRACE[0]["roll"],
        "seeded_prev_euler": seeded,
        "seeded_arm_quat": seeded_quat,
    })

    # ★ 首三帧手臂的**世界骨向**：若 f1 的世界朝向几乎没动、而欧拉跳了 141°，
    #   就是**表示分支**跳（欧拉通道逐分量插值 ⟹ 仍然是真的闪帧，必须修）。
    A.report("UP07_HEAD_DIR", {
        "f0": {b: [round(v, 5) for v in HEAD_DIR["f0"][b]] for b in ARM6},
        "f1": {b: [round(v, 5) for v in HEAD_DIR["f1"][b]] for b in ARM6},
        "f2": {b: [round(v, 5) for v in HEAD_DIR["f2"][b]] for b in ARM6},
        "f0_f1_dir_step_max_deg": round(max(
            math.degrees(Vector(HEAD_DIR["f0"][b]).angle(Vector(HEAD_DIR["f1"][b])))
            for b in ARM6), 4),
        "f1_f2_dir_step_max_deg": round(max(
            math.degrees(Vector(HEAD_DIR["f1"][b]).angle(Vector(HEAD_DIR["f2"][b])))
            for b in ARM6), 4),
    })
    A.report("UP07_LIMB_EULER", {
        "max_abs_euler_y_deg": round(max(euler_y.values()), 2),
        "per_bone_y_deg": {k: round(v, 1) for k, v in euler_y.items()},
        "max_roll_deg": {k: round(JS.ROLL_MAX.get(k, 0.0), 1) for k in ARM6 + LEG6},
        "max_extension_ratio": {
            s: round(max(r for side, r in REACH if side == s), 4) for s in SIDES},
        "note": ("腿 = `leg_aim`（3D 瞄准式双骨 IK + `_bulge` 接力 + `aim_carry`）；"
                 "搜索旋钮用库默认，`no_teleport` 说话"),
    })

    meta = {
        "anim_id": NAME,
        "loop": False,
        "category": "普通攻击",
        "note": ("上勾拳：深蹲蓄力（骨盆沉 185 mm）→ 后腿蹬伸 + 髋前送 135 mm + "
                 "支撑脚绕鞋底最前缘滚到 32° 提踵 ⟹ **重心上升 135 mm**、"
                 "拳峰冲到 1.86 m（比 B05 高 100+ mm）→ 躯干由前屈转伸展打透 → "
                 "f24~f27 冻结 4 帧 → 缓出收招，停在自持「上勾完」（末帧不回 idle）"),
        "antic_frame": ANTIC_END,
        "hit_frame": HIT,
        "cancel_frame": CANCEL,
        "follow_frame": FOLLOW_END,
        "burst_span_clock": [BURST_START, HIT],
        "hitstop_frames": HOLD + 1,
        "hitstop_span": [HIT, HIT + HOLD],
        "motion_clock_hold_frames": HOLD,
        "strike_style": "rear_leg_driven_uppercut",
        "support_leg": SUPPORT,
        "attack_leg": ATTACK,
        "attack_arm": ATTACK,
        "root_motion_m": [0.0, 0.0],
        "root_motion_note": ("**原地**（清单 §0.4：普通攻击不许 Root Motion，C 族起才允许）。"
                             "本支的「重心上升」是**腿的蹬伸**做出来的："
                             "骨盆 z 830 → 965（+135）全部来自膝伸直 + 踝跖屈 + 髋前送，"
                             "root 位移为 0；引擎位移由程序控制"),
        "rise": {
            "rule": "命中帧骨盆 z − guard 骨盆 z ≥ +120 mm，且全程 min(pelvis z) 落在 [1, CROUCH_END]",
            "guard_pelvis_z_mm": 830.0,
            "crouch_pelvis_z_mm": 645.0,
            "hit_pelvis_z_mm": 965.0,
            "how": ("支撑脚**平踩**时骨盆上限只有 897.9 mm（+67.9）⟹ 上升必须"
                    "「膝伸直 + 踝跖屈」一起给；踝跖屈的滚动支点取**鞋底最前缘**"
                    "（钉「当前最低点」会得到带拐点的踝轨迹）"),
        },
        "uppercut_height": {
            "rule": "命中帧拳峰 z ≥ 1800 mm（比 B05 的 1735.4 更高）+ 拳峰在骨盆前方",
            "why": "上勾是往上打；拳必须在骨盆**前上方**，否则是「举手」不是「上勾」",
        },
        "knee_extend": {
            "rule": "攻击腿膝角从深蹲底到命中帧伸展 ≥55°",
            "b06_reference_deg": B06_ATTACK_KNEE_SPAN,
            "why": "「髋驱动」的直接证据：上勾的发动机是后腿的蹬直",
        },
        "hip_drive": {
            "rule": "命中帧骨盆前送 −y ≥ 60 mm",
            "why": "髋把重心往前上送，不是原地举手；同时前送能缩短髋→踝，是 rise 的前提",
        },
        "ground_contact": {
            "rule": "**拆两侧写**：支撑脚 L 鞋底 −2~+6 mm；攻击脚 R **允许离地蹬伸**",
            "why": ("B04~B06 的 `min(L, R)` 一刀切在本支必假红 —— "
                    "本支攻击腿在命中帧必须离地（骨盆前送后髋→后踝 ≥820 mm）"),
        },
        "support_foot": {
            "ankle_travel": "允许（提踵时踝必走 100+ mm）",
            "contact_pin": "鞋底最前缘接触点水平位移 ≤3 mm",
            "why": "钉的不是踝，是**接触点** —— 绕前缘滚动 = 纯滚动，接触点世界坐标不动",
        },
        "trunk_extend": {
            "window": [ANTIC_END, HIT],
            "rule": "骨盆→胸骨顶矢状仰角由前屈转到伸展 ≥25°",
            "why": "深蹲蓄力是前屈，命中帧要**伸展**（上勾是「把身体拉直」）",
        },
        "phase_path": {
            "guard": 0, "load": LOAD_END, "crouch": CHARGE_END,
            "strike": HIT, "follow": FOLLOW_END, "end": RECOVER_END,
            "powers": {"load": LOAD_POW, "chamber": CHAMBER_POW,
                       "burst": BURST_POW, "follow": FOLLOW_POW,
                       "settle": SETTLE_POW},
            "why": ("每条通道 = `g + (ld−g)·load + (ch−ld)·chamber + (st−ch)·burst"
                    " + (fo−st)·follow + (en−fo)·settle`；相位标量精确饱和 ⟹ "
                    "clock 44~47 姿态逐位恒定（末 4 帧零变化）。"
                    "★ 只有 settle 是缓出 `1−(1−u)^p`，其余四个 `u^p` 加速"),
        },
        "power_chain_scale_note": (
            "B07 口径：leg / hip 两段（与 B06 同一物理量）**严格要求 > 84.788 / 12.0**；"
            "foot 不与 B06 比（踢击甩脚背 vs 踮脚跖屈不是同一物理量）⟹ 非退化 + 踮脚 ≥12°；"
            "waist/shoulder/hand 非退化 + 时序 + 攻击臂占优（> 护手臂 ×1.5）。"
            "**换尺子，不是放宽**：六段数值全部照实列出（power_chain_vs_b06）"),
        "link_prev": "Idle_01@0（**首帧**逐位相等；起手不闪）",
        "link_next": ("末帧 = 自持「上勾完」姿态（拳在头侧上方、重心已落回 800 mm，不回 idle）"
                      "⟹ 可直接接后摇/硬直"),
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.set_hitstop(action, HIT, HIT + HOLD)
    A.add_markers(action, {
        "GUARD": 0, "ANTIC": 1, "LOAD_END": LOAD_END, "CROUCH_END": CHARGE_END,
        "ANTIC_END": ANTIC_END, "HIT": HIT, "HITSTOP_END": HIT + HOLD,
        "RECOV": HIT + HOLD, "FOLLOW_END": FOLLOW_END, "CANCEL": CANCEL, "END": TOTAL,
    })

    # ★ 本支判据要读 **thigh / shin 的世界头点**（膝角、腿伸展、髋轴），
    #   而库默认 `PROBE_BONES` 只含上肢与足 ⟹ 采样前把腿骨并进探针表。
    #   （只动**本进程**的库全局，不改 `anim_lib.py` 文件；B06 同款。）
    A.PROBE_BONES = tuple(A.PROBE_BONES) + tuple(
        b for b in ("thigh.L", "thigh.R", "shin.L", "shin.R")
        if b not in A.PROBE_BONES)
    samples = A.sample_animation(arm, action, 0, TOTAL, meshes)
    # 本支是**单腿支撑 + 攻击腿离地**：通用脚滑门禁只对**支撑脚**生效。
    report = A.run_common_assertions(samples, meta, foot_probe=("toe." + SUPPORT,))
    idle_mats = CR.action_world_matrices(arm, bpy.data.actions["Idle_01"], 0)
    frames = list(range(0, TOTAL + 1))
    sole = JS.sole_series(arm, action, frames)
    ankles = JS.ankle_series(arm, action, frames)
    reach = JF.reach_series(arm, action, frames)
    contact = contact_series(arm, action, frames, SUPPORT)
    target_err = 0.0
    pair = {(f, s): Vector(t) for f, s, t in TARGETS}
    for index, frame in enumerate(frames):
        for side in SIDES:
            if (frame, side) in pair:
                target_err = max(target_err, (Vector(ankles[index][side])
                                              - pair[(frame, side)]).length)
    report.update(uppercut_assertions(arm, action, samples, idle_mats, sole,
                                      ankles, reach, target_err, contact))
    report["meta"] = meta

    # ---- 诊断：支撑脚的实际世界转角 vs 目标角 vs 鞋底实测最低点（查"悬空 6 mm"根因）
    def _mat3(flat):
        return Matrix((flat[0:3], flat[4:7], flat[8:11]))

    _m0 = CR.action_world_matrices(arm, action, 0)
    _mats = {f: CR.action_world_matrices(arm, action, f)
             for f in range(12, TOTAL + 1)}
    _q0 = _mat3(_m0["foot." + SUPPORT]).to_quaternion()
    report["UP07_SOLE_DIAG"] = []
    for f in range(12, 31):
        qf = _mat3(_mats[f]["foot." + SUPPORT]).to_quaternion()
        report["UP07_SOLE_DIAG"].append({
            "f": f,
            "tip_target_deg": round(tip_support(clock(f)), 2),
            "foot_world_rot_deg": round(math.degrees((_q0.inverted() @ qf).angle), 2),
            "sole_low_mm": round(sole[f][SUPPORT] * 1000.0, 2),
        })

    # ---- 诊断：逐帧**世界旋转**增量（判 `no_teleport` 是"真闪帧"还是"欧拉表示跳"）
    #      ★ `Quaternion.angle` 会返回 [0, 2π]；>180° 的那支是"绕远路"表示 ⟹ 折算 `2π − θ`。
    def _short_deg(qa, qb):
        ang = math.degrees((qa.inverted() @ qb).angle) % 360.0
        return ang if ang <= 180.0 else 360.0 - ang

    def _head(flat):
        return Vector((flat[3], flat[7], flat[11]))

    _arm_len = {s: bone_len(arm, "upperarm." + s) + bone_len(arm, "forearm." + s)
                for s in SIDES}
    report["UP07_ROT_DIAG"] = []
    for f in range(13, TOTAL + 1):
        row = {"f": f}
        worst_name, worst = None, -1.0
        for name in ARM6 + LEG6:
            ang = _short_deg(_mat3(_mats[f - 1][name]).to_quaternion(),
                             _mat3(_mats[f][name]).to_quaternion())
            row[name] = round(ang, 2)
            if ang > worst:
                worst, worst_name = ang, name
        row["world_rot_max_deg"] = round(worst, 2)
        row["world_rot_max_bone"] = worst_name
        row["arm_ext"] = {
            s: round((_head(_mats[f]["hand." + s])
                      - _head(_mats[f]["upperarm." + s])).length
                     / _arm_len[s], 4) for s in SIDES}
        report["UP07_ROT_DIAG"].append(row)

    def _diff(before, after, top=6):
        rows = []
        for name in set(before) | set(after):
            ea = before.get(name, (0.0, 0.0, 0.0))
            eb = after.get(name, (0.0, 0.0, 0.0))
            for channel in range(3):
                rows.append((round(abs(ea[channel] - eb[channel]), 5),
                             name, "xyz"[channel],
                             round(ea[channel], 4), round(eb[channel], 4)))
        rows.sort(reverse=True)
        return [{"d": r[0], "bone": r[1], "axis": r[2],
                 "before": r[3], "after": r[4]} for r in rows[:top]]

    report["hitstop_probe"] = {
        "f%d_vs_f%d" % (HIT, HIT + 1): _diff(samples[HIT]["euler"],
                                             samples[HIT + 1]["euler"]),
    }
    report["tail_probe"] = [
        {"f": samples[i]["frame"], "top": _diff(samples[i - 1]["euler"],
                                                samples[i]["euler"], 3)}
        for i in range(len(samples) - 8, len(samples))]
    report["burst_probe"] = [
        {"f": row["frame"],
         "euler": {b: list(row["euler"][b]) for b in ARM6},
         "roll": row["roll"]}
        for row in TRACE if 12 <= row["frame"] <= 28]
    report["pole_probe"] = [
        {"f": f, "tag": tag, "sin": round(s, 4)}
        for f, tag, s in POLE_SIN if f <= 28]
    report["UP07_ARM_REQ"] = [
        {"f": f, "side": s, "req_mm": round(req, 1), "used_mm": round(used, 1),
         "lower_clamped": bool(used > req + 1e-6),
         "upper_clamped": bool(req > _REACH_MM * 0.9995 + 0.05)}
        for f, s, req, used in REQ if f <= TOTAL]
    # ★ 汇总：夹取是**安全网**，正解是"轨迹不进入环带"（文件头第 6 件）。
    #   ⚠️ 夹取有**两个方向**，必须分开报：
    #     lower = 拳离肩太近（`raw < fold_min`）⟹ 肘塌进芯，鼓出方向病态；
    #     upper = 拳够不到（`raw > 0.9995·reach`）⟹ 腕被钉在极限球面上，
    #             而"肩→请求腕"的方向在边界上转得很快 ⟹ 解一松手就**跳变**。
    #   f33→f34 的 `forearm.L` 42.06°/帧 就是 **upper** 造成的（旧版只报 lower，
    #   所以这条红点被埋了很久）。
    report["UP07_ARM_CLAMP_SUMMARY"] = {
        "reach_mm": _REACH_MM,
        "limit_mm": round(_REACH_MM * 0.9995, 1),
        "fold_min_mm": round(_REACH_MM * FOLD_MIN_RATIO, 1),
        "lower_clamped_frames": sorted({f for f, s, req, used in REQ
                                        if used > req + 1e-6}),
        "upper_clamped_frames": sorted({f for f, s, req, used in REQ
                                        if req > _REACH_MM * 0.9995 + 0.05}),
        "upper_clamped_frames_in_burst": sorted(
            {f for f, s, req, used in REQ
             if req > _REACH_MM * 0.9995 + 0.05 and CHARGE_END < f <= HIT + HOLD}),
        "upper_over_by_mm": round(max([req - _REACH_MM * 0.9995 for f, s, req, used in REQ
                                       if req > _REACH_MM * 0.9995], default=0.0), 1),
        "min_req_mm_burst": round(min([req for f, s, req, used in REQ
                                       if CHARGE_END < f <= HIT], default=0.0), 1),
        "note": "`clamped_frames_in_burst` 必须为空 —— 否则说明拳的轨迹又穿肩了。",
    }
    report["seg_probe"] = [
        {"f": samples[i]["frame"],
         **{seg: round(max(
             max(abs(samples[i - 1]["euler"].get(n, (0., 0., 0.))[c]
                     - samples[i]["euler"].get(n, (0., 0., 0.))[c])
                 for c in range(3))
             for n in bones), 2)
            for seg, bones in SEGMENTS.items()}}
        for i in range(1, len(samples))]
    report["skipped_gates"] = sorted(
        k for k, v in report.items() if v is None and k.endswith("_ok"))
    failed = sorted(k for k, v in report.items()
                    if (k.endswith("_ok")
                        or k in ("no_teleport", "hitstop_present"))
                    and v is not True and v is not None)
    report["failed"] = failed
    A.report("UP07_REPORT", report)

    if not SKIP_RENDER:
        SIDE = ("side", (4.8, 0.0, 1.00), (0.0, 0.0, 1.00), 2.95, (800, 1220))
        FRONT = ("front", (0.0, -5.4, 1.00), (0.0, 0.0, 1.00), 2.95, (800, 1220))
        TOPQ = ("three_quarter", (3.6, -4.0, 1.15), (0.0, 0.0, 1.00), 2.95,
                (800, 1220))
        A.render_pose_sheet(arm, action,
                            [0, LOAD_END, 10, CHARGE_END, 16, 19, 21, HIT,
                             HIT + HOLD, HIT + HOLD + 4, CANCEL, 40, TOTAL],
                            "up07", views=(SIDE,))
        A.render_pose_sheet(arm, action, [0, CHARGE_END, HIT, TOTAL], "up07",
                            views=(FRONT,))
        A.render_pose_sheet(arm, action, [CHARGE_END, 20, HIT], "up07", views=(TOPQ,))
        A.save_project()
        A.export_glb(arm)
    print("UP07_DONE failed=%s" % failed)


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("UP07_FAILURE " + traceback.format_exc())
