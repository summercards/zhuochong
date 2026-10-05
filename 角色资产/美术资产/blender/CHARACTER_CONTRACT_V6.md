# Business Man Character Contract V6

## 资产身份

- 资产类型：独立风格化商务男角色视觉模型
- 版本：v6
- 原始参考：
  `C:\Users\ZHUANG~1\AppData\Local\Temp\codex-clipboard-6aee020d-3540-4c09-96e2-db9b3da614c1.png`
- Blender 源文件：
  `I:\工作项目\blender\business_man_tpose_v6.blend`
- GLB 导出：
  `I:\工作项目\blender\business_man_tpose_v6.glb`
- 构建脚本：
  `I:\工作项目\blender\build_character_v6.py`
- GLB 审计脚本：
  `I:\工作项目\blender\audit_character_glb.py`
- GLB 审计报告：
  `I:\工作项目\blender\CHARACTER_AUDIT_V6.json`
- 身体姿态测试：
  `I:\工作项目\blender\pose_test_character_v4.py`
- 身体姿态报告：
  `I:\工作项目\blender\CHARACTER_POSE_AUDIT_V6.json`
- 新增功能区测试：
  `I:\工作项目\blender\test_character_detail_v6.py`
- 新增功能区报告：
  `I:\工作项目\blender\CHARACTER_DETAIL_AUDIT_V6.json`

v6 从已审计的 v5 增量生成。原始身体网格、材质、T-pose、根变换和
v1-v5 文件均保持不变。

## 运行时契约

- 导入根：`Character_Rig`
- 前向轴：`-Y`
- 上轴：`+Z`
- 角色展示尺寸：高度 `1.857 m`
- 包围盒：`1.926 x 0.428331 x 1.857 m`
- 最低点：`Z = 0.001 m`
- 根变换：位置 `(0, 0, 0)`、旋转 `0`、缩放 `1`
- 静止姿势：严格水平手臂 T-pose
- 运行时消费者：未提供，因此未新增控制器、碰撞、装备槽或状态机
- GLB 内容：`121` 个角色网格、一个骨架、`17` 个材质
- GLB 不包含：相机、灯光、地面、动画剪辑和展示辅助物

## 骨架契约

- 骨架：`Character_Rig`
- 总骨数：`53`
- 原有基础骨：`20`
- 新增面部骨：
  - `jaw`
  - `eye.L`
  - `eye.R`
- 每只手新增 `15` 根手指骨，双手共 `30` 根：
  - `finger_index_01.L` 至 `finger_index_03.L`
  - `finger_middle_01.L` 至 `finger_middle_03.L`
  - `finger_ring_01.L` 至 `finger_ring_03.L`
  - `finger_pinky_01.L` 至 `finger_pinky_03.L`
  - `thumb_01.L` 至 `thumb_03.L`
  - 右侧使用相同名称并将 `.L` 替换为 `.R`
- `jaw`、`eye.L`、`eye.R` 的父骨为 `head`
- 四指三段骨链的父骨为对应 `hand.L` 或 `hand.R`
- 拇指三段骨链的父骨为对应 `hand.L` 或 `hand.R`
- 手指骨为直接 FK 链，没有新增 IK 控制器、约束或驱动器

## 蒙皮契约

- `Jaw`、`Chin`、`Lower_Lip`、`Mouth_Line` 刚性绑定到 `jaw`
- `Upper_Lip` 继续绑定到 `head`
- `Eye_White_L`、`Iris_L`、`Pupil_L` 刚性绑定到 `eye.L`
- `Eye_White_R`、`Iris_R`、`Pupil_R` 刚性绑定到 `eye.R`
- `Finger_*` 按三段指骨执行局部双骨平滑权重
- `Knuckle_*` 刚性绑定到对应近端指骨
- `Thumb_*` 和 `Thumb_Tip_*` 绑定到对应三段拇指骨链
- 新增功能区最大权重和误差：`0.00000003`
- 新增功能区异常骨骼组和负权重：`0`
- 原有身体权重未重算，继续使用 `Preserve Volume`

## 动画测试

测试均为 GLB 干净回导后的实际求值几何，不是只在源文件中检查骨名。

- 下颌绕局部 X 轴旋转 `30°`：
  - `Jaw` 最大顶点位移 `0.067589 m`
  - `Chin` 最大顶点位移 `0.069358 m`
  - `Lower_Lip` 最大顶点位移 `0.071523 m`
  - `Mouth_Line` 最大顶点位移 `0.073145 m`
- 双眼绕局部 Z 轴旋转 `20°`：
  - 眼球、虹膜、瞳孔整体位移约 `0.008-0.010 m`
  - 眼球、虹膜、瞳孔保持组合运动，没有脱出眼窝
- 每根四指的前两节旋转 `38°`：
  - 最大顶点位移范围 `0.069818-0.094218 m`
  - 每根手指的三段骨链均产生连续、有限形变
- 每根拇指的前两节旋转 `28°`：
  - 最大顶点位移范围 `0.034809-0.041004 m`
- 左右手指测试结果对称
- 所有测试姿势几何均有限

## 验证状态

- Blender 4.5 GLB 干净回导：通过
- 骨骼数量与命名：通过，实测 `53`
- T-pose 手臂水平误差：`0.003 m`，通过 `0.01 m` 上限
- 导出范围：通过，无相机、灯光、地面或 Tripo 对象
- 身体姿态压力测试：通过
- 下颌、眼睛、手指细节测试：通过
- 新增区域权重覆盖率：通过
- 表情与手指动画形态近景人工检查：通过

这是可直接用于动画和运行时展示的风格化 production blockout。当前面部
控制是刚性部件骨动画，不是混合形状、肌肉模拟或精修口型系统；手指为
直接 FK，不包含手势 IK、抓握求解或道具约束。

## 预览文件

- 正面 T-pose：
  `I:\工作项目\blender\business_man_tpose_v6_front.png`
- 侧面 T-pose：
  `I:\工作项目\blender\business_man_tpose_v6_side.png`
- 背面 T-pose：
  `I:\工作项目\blender\business_man_tpose_v6_back.png`
- 身体姿态测试：
  `I:\工作项目\blender\business_man_tpose_v6_pose_test.png`
- 张嘴与眼球测试：
  `I:\工作项目\blender\business_man_tpose_v6_face_test.png`
- 左手弯曲测试：
  `I:\工作项目\blender\business_man_tpose_v6_hand_L_test.png`
- 右手弯曲测试：
  `I:\工作项目\blender\business_man_tpose_v6_hand_R_test.png`

## 文件哈希

- GLB SHA256：
  `a94daf94b2bbf238ff0522c4b25b1d0c7ec94d893005cbd9ca0f2c1097135ad3`
- Blend SHA256：
  `4ecddd9a3db22711da07293aa5d6bf538277c5376248046c00e17de389af9c67`

## 版本与回滚

- 当前源文件：
  `I:\工作项目\blender\business_man_tpose_v6.blend`
- 当前导出：
  `I:\工作项目\blender\business_man_tpose_v6.glb`
- 上一版契约：
  `I:\工作项目\blender\CHARACTER_CONTRACT_V5.md`
- 回滚源文件：
  `I:\工作项目\blender\business_man_tpose_v5.blend`
- 回滚导出：
  `I:\工作项目\blender\business_man_tpose_v5.glb`

不得覆盖 v1-v6。后续修改必须创建 v7 或更高版本，并保留本契约、
Blend、GLB、预览和审计报告。
