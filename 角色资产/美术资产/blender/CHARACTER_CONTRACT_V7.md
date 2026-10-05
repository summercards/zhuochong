# Business Man Character Contract V7

## 资产身份

- 资产类型：独立风格化商务男角色视觉模型
- 版本：v7
- 原始参考：
  `C:\Users\ZHUANG~1\AppData\Local\Temp\codex-clipboard-6aee020d-3540-4c09-96e2-db9b3da614c1.png`
- Blender 源文件：
  `I:\工作项目\blender\business_man_tpose_v7.blend`
- GLB 导出：
  `I:\工作项目\blender\business_man_tpose_v7.glb`
- 构建脚本：
  `I:\工作项目\blender\build_character_v7.py`
- GLB 审计脚本：
  `I:\工作项目\blender\audit_character_glb.py`
- GLB 审计报告：
  `I:\工作项目\blender\CHARACTER_AUDIT_V7.json`
- 身体姿态测试：
  `I:\工作项目\blender\pose_test_character_v4.py`
- 身体姿态报告：
  `I:\工作项目\blender\CHARACTER_POSE_AUDIT_V7.json`
- 新增功能区测试：
  `I:\工作项目\blender\test_character_detail_v7.py`
- 新增功能区报告：
  `I:\工作项目\blender\CHARACTER_DETAIL_AUDIT_V7.json`

v7 从已审计的 v6 增量生成。原始身体网格、材质、T-pose、根变换和
v1-v6 文件均保持不变。

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
- 总骨数：`56`
- 原有基础骨：`20`
- v6 原有面部骨：
  - `jaw`
  - `eye.L`
  - `eye.R`
- v7 新增嘴唇和眼镜骨：
  - `upper_lip`，父骨为 `head`
  - `lower_lip`，父骨为 `jaw`
  - `glasses`，父骨为 `head`
- 双手各有 `15` 根手指骨，双手共 `30` 根：
  - `finger_index_01.L` 至 `finger_index_03.L`
  - `finger_middle_01.L` 至 `finger_middle_03.L`
  - `finger_ring_01.L` 至 `finger_ring_03.L`
  - `finger_pinky_01.L` 至 `finger_pinky_03.L`
  - `thumb_01.L` 至 `thumb_03.L`
  - 右侧使用相同名称并将 `.L` 替换为 `.R`
- 手指骨为直接 FK 链，没有新增 IK 控制器、约束或驱动器

## 蒙皮契约

- `Jaw`、`Chin` 刚性绑定到 `jaw`
- `Upper_Lip` 刚性绑定到 `upper_lip`
- `Lower_Lip` 刚性绑定到 `lower_lip`
- `Mouth_Line` 按静止世界 `Z` 高度使用平滑权重分配给
  `upper_lip` 和 `lower_lip`
- `lower_lip` 的父骨为 `jaw`，因此下颌开合时下唇会继承下颌运动，
  同时仍可独立微调
- `Glasses_Bridge`、`Glasses_Frame_L`、`Glasses_Frame_R`、
  `Glasses_Lens_L`、`Glasses_Lens_R`、`Glasses_Temple_L`、
  `Glasses_Temple_R` 全部刚性绑定到 `glasses`
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

- 上唇单独沿骨局部 Y 平移 `0.006 m`：
  - 质心 `+Z` 位移 `0.006002 m`
  - 最大顶点位移 `0.006 m`
- 下唇单独沿骨局部 Y 平移 `0.010 m`：
  - 质心 `-Z` 位移 `-0.009999 m`
  - 最大顶点位移 `0.010 m`
- 上唇、下唇分别绕局部 X 旋转 `12°`：
  - 最大顶点位移分别为 `0.001150 m`、`0.001114 m`
- 组合说话压力姿势：
  - `jaw` 绕局部 X 旋转 `30°`
  - 上唇局部 Y 平移 `0.006 m`
  - 下唇局部 Y 平移 `0.010 m`
  - 上下唇质心间距增加 `0.074339 m`
  - `Mouth_Line` 上、下四分之一顶点带的间距增加 `0.063291 m`
- 展示近景使用较温和的 `jaw` 旋转 `6°`、上唇平移 `0.004 m`、
  下唇平移 `0.007 m`，可清楚看到上下唇分别开合
- `glasses` 绕局部 X 旋转 `8°`、局部 Z 旋转 `10°`：
  - 最大顶点位移 `0.028533 m`
  - 七个眼镜部件最大两两距离误差 `0.00000072 m`
  - 镜框、镜片和镜腿保持整组刚性跟随
- 下颌压力姿势下：
  - `Jaw` 最大顶点位移 `0.067588 m`
  - `Chin` 最大顶点位移 `0.069358 m`
  - `Lower_Lip` 最大顶点位移 `0.081523 m`
  - `Mouth_Line` 最大顶点位移 `0.082941 m`
- 双眼绕局部 Z 轴旋转 `20°`：
  - 眼球、虹膜、瞳孔整体位移约 `0.008-0.010 m`
- 每根四指的前两节旋转 `38°`：
  - 最大顶点位移范围 `0.069818-0.094218 m`
- 每根拇指的前两节旋转 `28°`：
  - 最大顶点位移范围 `0.034809-0.041004 m`
- 左右手指测试结果对称
- 所有测试姿势几何均有限

## 验证状态

- Blender 4.5 GLB 干净回导：通过
- 骨骼数量与命名：通过，实测 `56`
- T-pose 手臂水平误差：`0.003 m`，通过 `0.01 m` 上限
- 导出范围：通过，无相机、灯光、地面或 Tripo 对象
- 身体姿态压力测试：通过
- 上下唇独立运动：通过
- 说话张嘴和嘴线形变：通过
- 眼镜整组刚性控制：通过
- 眼睛、手指和新增区域细节测试：通过
- 新增区域权重覆盖率：通过
- 张嘴、嘴唇、眼镜和手指近景人工检查：通过

这是可直接用于动画和运行时展示的风格化 production blockout。当前嘴唇
和眼镜控制是刚性部件骨动画，不是混合形状、肌肉模拟或精修口型系统；
`Mouth_Line` 使用平滑双骨权重。手指为直接 FK，不包含手势 IK、抓握
求解或道具约束。GLB 当前不导出动画剪辑。

## 预览文件

- 正面 T-pose：
  `I:\工作项目\blender\business_man_tpose_v7_front.png`
- 侧面 T-pose：
  `I:\工作项目\blender\business_man_tpose_v7_side.png`
- 背面 T-pose：
  `I:\工作项目\blender\business_man_tpose_v7_back.png`
- 身体姿态测试：
  `I:\工作项目\blender\business_man_tpose_v7_pose_test.png`
- 嘴唇和眼镜近景测试：
  `I:\工作项目\blender\business_man_tpose_v7_face_test.png`
- 左手弯曲测试：
  `I:\工作项目\blender\business_man_tpose_v7_hand_L_test.png`
- 右手弯曲测试：
  `I:\工作项目\blender\business_man_tpose_v7_hand_R_test.png`

## 文件哈希

- GLB SHA256：
  `0c1697d9569e027a247256b0f9e6eca055c912ceafab3150325eaf0e679f405f`
- Blend SHA256：
  `33affc63cfc0551c85efdd1ab050fe0a35e7327eb744bc86c0ccf85eb9fd6460`

## 版本与回滚

- 当前源文件：
  `I:\工作项目\blender\business_man_tpose_v7.blend`
- 当前导出：
  `I:\工作项目\blender\business_man_tpose_v7.glb`
- 上一版契约：
  `I:\工作项目\blender\CHARACTER_CONTRACT_V6.md`
- 回滚源文件：
  `I:\工作项目\blender\business_man_tpose_v6.blend`
- 回滚导出：
  `I:\工作项目\blender\business_man_tpose_v6.glb`

不得覆盖 v1-v7。后续修改必须创建 v8 或更高版本，并保留本契约、
Blend、GLB、预览和审计报告。
