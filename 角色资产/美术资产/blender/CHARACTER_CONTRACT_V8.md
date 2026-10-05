# Business Man Character Contract V8

## 资产身份

- 资产类型：独立风格化商务男角色视觉模型与游戏动画资产
- 版本：v8
- 原始参考：
  `C:\Users\ZHUANG~1\AppData\Local\Temp\codex-clipboard-6aee020d-3540-4c09-96e2-db9b3da614c1.png`
- Blender 源文件：
  `I:\工作项目\blender\business_man_tpose_v8.blend`
- GLB 导出：
  `I:\工作项目\blender\business_man_tpose_v8.glb`
- 动画构建脚本：
  `I:\工作项目\blender\build_character_animations_v8.py`
- GLB 回导审计脚本：
  `I:\工作项目\blender\audit_character_animations_v8.py`
- GLB 回导审计报告：
  `I:\工作项目\blender\CHARACTER_ANIMATION_AUDIT_V8.json`
- 上一版角色与骨骼契约：
  `I:\工作项目\blender\CHARACTER_CONTRACT_V7.md`

v8 从已审计的 v7 增量生成，只增加并验证动画剪辑。v7 的身体、面部、
眼镜、手指、T-pose、材质、骨骼层级、权重、根变换与 v1-v7 文件均保持
不变。v8 是当前动画交付版本，v7 是当前可回滚母版。

## v7 到 v8 的增量

- 新增动作：`idle`、`walk`、`run`、`talk`、`attack`、`jump`、
  `hit`、`crouch`、`jump_up`
- 动画帧率：`30 FPS`
- 角色网格数保持：`121`
- 骨架数保持：`1`
- 骨骼数保持：`56`
- 根骨名称和层级保持：`Character_Rig`
- 蒙皮、材质、模型尺寸和 T-pose 静止姿势保持不变

## 运行时契约

- 导入根：`Character_Rig`
- 前向轴：`-Y`
- 上轴：`+Z`
- 角色展示尺寸：高度约 `1.857 m`
- 根变换：位置 `(0, 0, 0)`、旋转 `0`、缩放 `1`
- 静止姿势：严格水平手臂 T-pose
- 运行时消费者：未提供，因此未新增控制器、碰撞、装备槽、HP、
  攻击判定或状态机脚本
- GLB 内容：`121` 个角色网格、一个骨架、`56` 根骨骼、9 个动画剪辑
- GLB 不包含：相机、灯光、地面、展示辅助物或碰撞体
- 根运动策略：所有动作均为原地动画，根骨位置、旋转和缩放漂移为 `0`
- 位移策略：水平移动、垂直位移、重力、碰撞、击退距离和状态切换均由
  游戏运行时控制

## 骨骼契约

v8 完整保留 v7 的 `56` 根骨骼：

- 原有基础骨：`20`
- 面部骨：`jaw`、`eye.L`、`eye.R`
- 嘴唇骨：`upper_lip`，父骨为 `head`
- 嘴唇骨：`lower_lip`，父骨为 `jaw`
- 眼镜骨：`glasses`，父骨为 `head`
- 双手各有 `15` 根手指骨，双手共 `30` 根：
  `finger_index_01` 至 `finger_index_03`、
  `finger_middle_01` 至 `finger_middle_03`、
  `finger_ring_01` 至 `finger_ring_03`、
  `finger_pinky_01` 至 `finger_pinky_03`、
  `thumb_01` 至 `thumb_03`，左右分别使用 `.L` 和 `.R` 后缀

手指为直接 FK 链。动画资产不包含 IK 控制器、约束或驱动器。

## 动画清单

| 状态 | 帧段 | 时长 | 类型 | 用途 |
| --- | --- | --- | --- | --- |
| `idle` | `0-60` | `2.0 s` | 循环 | 待机呼吸与轻微重心变化 |
| `walk` | `0-32` | `1.066667 s` | 循环 | 步行 |
| `run` | `0-24` | `0.8 s` | 循环 | 跑步 |
| `talk` | `0-60` | `2.0 s` | 循环 | 说话、下颌和上下唇运动 |
| `attack` | `0-24` | `0.8 s` | 一次性 | 徒手右拳攻击 |
| `jump` | `0-36` | `1.2 s` | 一次性 | 完整起跳、腾空和落地表现 |
| `hit` | `0-20` | `0.666667 s` | 一次性 | 受击后仰与恢复 |
| `crouch` | `0-30` | `1.0 s` | 循环 | 蹲伏待机 |
| `jump_up` | `0-18` | `0.6 s` | 一次性 | 起跳阶段 |

`jump` 是完整腾空过程；`jump_up` 只覆盖起跳阶段。运行时可按状态机需要
选择其中一种，也可以先播放 `jump_up`，进入空中状态后切换到 `jump`
或其他空中循环动作。

## 验证状态

验证对象为 GLB 干净回导后的实际动画数据与求值几何，不是只检查源文件。

- GLB 回导总体验证：通过
- 动作名称与数量：通过，实测 9 个
- 所有动作时长：通过
- 所有关键帧时间和值有限性：通过
- 根骨位置、旋转和缩放漂移：全部为 `0`
- 循环端点：
  - `idle`：误差 `0`
  - `walk`：误差 `0`
  - `run`：误差 `0`
  - `talk`：误差 `0`
  - `crouch`：误差 `0`
- `talk` 说话检查：
  - 下颌旋转约 `14.87 deg`
  - 上下唇独立位移有效
  - 嘴线形变有效
- `attack` 攻击检查：
  - 右拳四指约 `77.9 deg` 弯曲
  - 右拳在世界空间明确向前伸出
- `crouch` 蹲伏检查：骨盆下移约 `0.150748 m`
- `jump` 跳跃检查：骨盆峰值约 `0.333472 m`
- `jump_up` 起跳检查：骨盆峰值约 `0.264218 m`
- `hit` 受击检查：胸部约 `20.27 deg`、头部约 `22.58 deg`
- `walk` 鞋底接触误差约 `-0.0093 m` 至 `+0.0097 m`
- `run` 腾空约 `0.9 cm` 至 `3.2 cm`
- `crouch`、`jump` 落地存在约 `1-3 cm` 的轻微鞋底穿透，属于当前
  production blockout 的可接受范围
- 9 张预览图人工检查：通过

动画只负责表现，不包含位移、碰撞、HP、攻击判定、伤害结算或状态切换
逻辑。攻击动作不附带武器、攻击盒或命中帧事件。

## 状态机建议

- 循环状态：`idle`、`walk`、`run`、`talk`、`crouch`
- 一次性状态：`attack`、`jump`、`hit`、`jump_up`
- 一次性动作结束后回落到当前移动状态，例如 `idle`、`walk`、`run`
  或 `crouch`
- `talk` 可作为独立循环状态，也可由上层状态机覆盖到待机或移动表现
- 移动速度、蹲伏高度、跳跃曲线、击退距离和攻击命中窗口应由角色控制器
  与状态机控制，不应从根骨动画中提取

## 预览文件

- 待机：
  `I:\工作项目\blender\business_man_tpose_v8_idle_preview.png`
- 走路：
  `I:\工作项目\blender\business_man_tpose_v8_walk_preview.png`
- 跑步：
  `I:\工作项目\blender\business_man_tpose_v8_run_preview.png`
- 说话：
  `I:\工作项目\blender\business_man_tpose_v8_talk_preview.png`
- 攻击：
  `I:\工作项目\blender\business_man_tpose_v8_attack_preview.png`
- 跳跃：
  `I:\工作项目\blender\business_man_tpose_v8_jump_preview.png`
- 受击：
  `I:\工作项目\blender\business_man_tpose_v8_hit_preview.png`
- 蹲下：
  `I:\工作项目\blender\business_man_tpose_v8_crouch_preview.png`
- 跳起：
  `I:\工作项目\blender\business_man_tpose_v8_jump_up_preview.png`

## 文件哈希

- Blend SHA256：
  `111a0b59ae5c5c7754f2774fcc2068c968b6df7164ba266981ae5bfafdcd3210`
- GLB SHA256：
  `954bda3243aefd3690e25e0901fc370912a9bc715e76524075666aba8be7af45`

审计报告内的 GLB 哈希与上述文件哈希一致。

## 版本与回滚

- 当前动画源文件：
  `I:\工作项目\blender\business_man_tpose_v8.blend`
- 当前动画导出：
  `I:\工作项目\blender\business_man_tpose_v8.glb`
- 当前动画审计：
  `I:\工作项目\blender\CHARACTER_ANIMATION_AUDIT_V8.json`
- 当前契约：
  `I:\工作项目\blender\CHARACTER_CONTRACT_V8.md`
- 回滚源文件：
  `I:\工作项目\blender\business_man_tpose_v7.blend`
- 回滚导出：
  `I:\工作项目\blender\business_man_tpose_v7.glb`
- 回滚契约：
  `I:\工作项目\blender\CHARACTER_CONTRACT_V7.md`

不得覆盖 v1-v8。后续修改必须创建 v9 或更高版本，并保留本契约、
Blend、GLB、预览、构建脚本和审计报告。
