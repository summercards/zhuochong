# Skill Effect V1

完整技能特效工程，按参考图拆成蓄能、旋涡、成形、爆发和回落五个阶段。

## 文件

- `skill_effect_v1/skill_effect_v1.blend`：Blender 4.5 主工程。
- `skill_effect_v1/skill_effect_v1_preview.mp4`：160 帧、30 fps 的预览视频。
- `skill_effect_v1/previews/`：阶段关键帧与拼图。
- `skill_effect_v1/SKILL_EFFECT_V1_MANIFEST.json`：场景和阶段结构。

## 动画阶段

- `1-30`：星尘苏醒，黑核与内环出现。
- `25-70`：紫、蓝、青、粉旋臂展开。
- `62-104`：熊猫能量面、螺旋眼和口部符文成形。
- `92-138`：冲击环、碎片和面部能量脉冲爆发。
- `138-160`：能量回落并进入可循环的稳定状态。

## 主要控制组

- `CTRL_CoreAssembly`
- `CTRL_MainVortex`
- `CTRL_FaceAssembly`
- `CTRL_BurstAssembly`
- `CTRL_Shards`

`Skill_Camera` 与 `CAM_Target` 控制三段镜头运动；`SKILL_EFFECT` 合集内全部对象可整体复制到其他场景。
