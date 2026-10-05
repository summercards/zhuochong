shader_type canvas_item;

// 屏幕后处理：扫描线 + 暗角 + 细微噪点。
//
// 挂在全屏 ColorRect 上，输出**黑色半透明**叠加在原画面上（默认 MIX 混合）。
// 只做"压暗"这一件事 —— 闪白是另一个纯色 ColorRect，不需要着色器。
//
// 为什么这三样都要有：矩阵虚拟空间的关键不是"绿"，而是"看起来像一块显示器"。
// 扫描线给电子感、暗角把注意力收到中间、噪点让纯色区不至于死平。

// 扫描线强度。0.06 是"看得见但不影响读血条"的位置。
uniform float scanline_strength : hint_range(0.0, 0.5) = 0.070;
// 扫描线密度（条数）。按 1080p 调，屏幕越高越密。
uniform float scanline_count = 540.0;
// 暗角强度。
uniform float vignette_strength : hint_range(0.0, 1.0) = 0.50;
// 暗角起始半径（屏幕半对角的比例）。
uniform float vignette_start : hint_range(0.0, 1.0) = 0.34;
// 噪点强度。
uniform float noise_strength : hint_range(0.0, 0.3) = 0.022;
// 整体绿色染色（很轻，只为了让画面统一到矩阵色调上）。
uniform vec3 tint : source_color = vec3(0.10, 0.45, 0.22);
uniform float tint_strength : hint_range(0.0, 0.5) = 0.055;

float hash21(vec2 p) {
	p = fract(p * vec2(123.34, 456.21));
	p += dot(p, p + 45.32);
	return fract(p.x * p.y);
}

void fragment() {
	vec2 uv = UV;

	// --- 扫描线：细密的水平暗线 ---
	float sl = sin(uv.y * scanline_count * 3.14159);
	float scan = (sl * 0.5 + 0.5) * scanline_strength;

	// --- 暗角：越靠边越暗 ---
	float d = length(uv - vec2(0.5)) * 1.414;
	float vig = smoothstep(vignette_start, 0.92, d) * vignette_strength;

	// --- 噪点：逐帧变化的细微颗粒 ---
	float n = (hash21(uv * vec2(1920.0, 1080.0) + fract(TIME) * 137.0) - 0.5)
		* noise_strength;

	// 压暗量 + 噪点（噪点可正可负，所以单独算颜色，不并进 alpha）
	float darken = clamp(scan + vig, 0.0, 1.0);

	// 绿色染色：单独叠一层很淡的绿，让整个画面统一到矩阵色调
	vec3 rgb = tint;
	float a = darken + tint_strength * (1.0 - darken);

	// 噪点直接扰动 alpha，制造颗粒
	a = clamp(a + n, 0.0, 1.0);

	COLOR = vec4(rgb, a);
}
