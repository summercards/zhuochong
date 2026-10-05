shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never;

// 命中爆点：贴着一个 XY 平面的四边形画出来的"打击火花"。
//
// 为什么用四边形 + 着色器，而不是粒子：
//   1. 横版格斗的相机几乎正交地盯着 +Z 方向，命中火花本来就该是**朝向相机的一张图**。
//      粒子要摆几千个才铺得出这个形状，而这里一个 fragment 就够。
//   2. **时序可控**：所有形状都由 progress 一个 0→1 的数驱动，
//      于是"哪一帧长什么样"是确定的 —— 可以截图验收，粒子做不到。
//
// 视觉三层（缺一层就不像打击感）：
//   1. 核心闪光 —— 一开始又大又白，迅速缩小。这是"打中了"的第一读法。
//   2. 扩散环   —— 半径 0→1 推开、同时变薄。这是"力量传出去"的读法。
//   3. 放射尖刺 —— N 根按角度分布的短线，把"冲击"读成有方向的。

// 主色（暖橙 = 普通命中）与高光色（白）
uniform vec3 color : source_color = vec3(1.0, 0.78, 0.28);
uniform vec3 hot_color : source_color = vec3(1.0, 1.0, 0.94);
// 0 = 刚出现，1 = 完全消失。整个生命周期由这一个数驱动。
uniform float progress : hint_range(0.0, 1.0) = 0.0;
// 放射尖刺的根数
uniform int spokes = 8;
// 尖刺长度（UV 半径比例，1.0 = 铺满整张四边形）
uniform float spoke_len = 0.95;
// 尖刺宽度（角向占比，越小越细）
uniform float spoke_w = 0.16;
// 环的厚度（初始值，会随 progress 变薄）
uniform float ring_thickness = 0.40;
// 环的最大半径
uniform float ring_radius = 0.95;
// 核心半径（初始值）
uniform float core_size = 0.62;
// 整体增益 —— 强度分级靠它（轻/重/大招走不同增益）
uniform float gain = 1.0;

// 注意：**不要自己定义 TAU** —— Godot 的着色器语言已内置 `TAU`，
// 再写一遍是 "Redefinition of 'TAU'"，整个着色器编译失败（踩过一次）。
// 圆周率同理（`PI` 也是内置的）。

void fragment() {
	// UV 中心化到 [-1,1]
	vec2 p = UV * 2.0 - 1.0;
	float r = length(p);
	float ang = atan(p.y, p.x);

	// 生命周期：尾部收得比头部快，读起来像"啪"一下而不是慢慢淡
	float life = 1.0 - progress;
	float fade = pow(life, 1.5);

	// --- 1. 核心闪光：随 progress 缩小 ---
	float core_r = max(core_size * (1.0 - progress * 0.75), 0.001);
	float core = 1.0 - smoothstep(core_r * 0.35, core_r, r);

	// --- 2. 扩散环 ---
	float rr = ring_radius * progress;
	float th = max(ring_thickness * (1.0 - progress * 0.65), 0.001);
	float ring = 1.0 - smoothstep(th * 0.30, th, abs(r - rr));

	// --- 3. 放射尖刺 ---
	float a01 = ang / TAU + 0.5;
	float cell = fract(a01 * float(spokes));
	// 到最近尖刺中心的角向距离
	float ang_d = min(cell, 1.0 - cell);
	float spike = 1.0 - smoothstep(spoke_w * 0.25, spoke_w, ang_d);
	// 尖刺只延长到 spoke_len，并且头端要软
	float reach = 1.0 - smoothstep(spoke_len * 0.30, spoke_len, r);
	// 尖刺比环消失得更快（前 60% 就没了）
	float spike_fade = 1.0 - smoothstep(0.0, 0.6, progress);
	float sp = spike * reach * spike_fade * fade;

	// 合成。核心给最强的高光，环给主色，尖刺居中。
	float i = core * 1.8 * fade + ring * 1.35 + sp * 1.25;
	i *= gain;

	// 核心偏白、外圈偏主色 —— 这一步是"温度感"的来源
	vec3 c = mix(color, hot_color, clamp(core * 1.2, 0.0, 1.0));
	ALBEDO = c * i;
	// blend_add 下 EMISSION 会再叠一层，所以留 0，全部走 ALBEDO
	EMISSION = vec3(0.0);
}
