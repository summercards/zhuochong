shader_type spatial;
render_mode unshaded, blend_add, cull_back, depth_draw_never;

// 受击闪白：叠在角色身上的一层纯白加色。
//
// 为什么用 **material_overlay** 而不是"临时改每个材质的 emission"：
//   这个角色有 17 个材质、91 个 primitive。逐个改 emission 要：
//   备份 17 个材质的状态 → 改 → 事后还原，中间任何一步失败都会把角色永久点亮。
//   `material_overlay` 是 GPU 层面的第二次绘制，只加一层颜色，
//   **一个共享材质就能闪全身**，而且摘下 overlay 就是干净的还原。
//
// 边缘更亮一点（菲涅尔）：纯色平铺会让角色变成一块白纸，
// 边缘加强之后能保住"这是一个立体的人"的轮廓感。

uniform vec3 flash_color : source_color = vec3(1.0, 1.0, 1.0);
// 闪白强度。0 = 完全不闪（此时这块 overlay 等于不存在）。
uniform float flash : hint_range(0.0, 1.0) = 0.0;
// 边缘增强强度
uniform float rim : hint_range(0.0, 2.0) = 0.55;

void fragment() {
	// 法线与视线夹角越大 = 越靠近轮廓剪影
	float facing = abs(dot(normalize(NORMAL), normalize(VIEW)));
	float r = pow(1.0 - facing, 2.0);
	float k = flash * (1.0 + r * rim);
	ALBEDO = flash_color * k;
	EMISSION = vec3(0.0);
}
