shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never;

// 黑客帝国式数字雨。
//
// 为什么用着色器而不是粒子：数字雨是**背景**，要铺满 56×16 m 的板子并且永远不重复。
// 用粒子要做几千个发射器才铺得满，而这里只要一个 fragment 就能算出整面"字符流"。
//
// 视觉构造（四层叠加，缺一层就"不像"）：
//   1. 分列        —— 每列独立的相位与速度，列间不同步才有"乱中有序"
//   2. 亮头 + 拖尾 —— 一个亮块 + 它上方一段渐暗的余迹（雨滴下落的读法）
//   3. 逐格亮度    —— 按格随机点亮，让拖尾断续成"字符"而不是一条实线
//   4. 格间留缝    —— 横竖都留缝，否则会糊成一片绿背景

// 雨的颜色。矩阵绿偏青，纯 (0,1,0) 会刺眼。
uniform vec3 rain_color : source_color = vec3(0.18, 1.0, 0.42);
// 整块板的列数（按 UV 均分）。板很宽，所以这个数要比"可见列数"大得多。
uniform float columns = 400.0;
// 下落速度（每秒走过 UV 的比例）。一块 7 m 高的板，0.4 ≈ 2.8 m/s。
uniform float speed = 0.40;
// 有多少比例的列是激活的（其余是空的，让画面透气）。
//
// **这个值是整块板亮度的第一闸门。** 第一版给了 0.5~0.68，四层叠起来
// 上半屏被糊成一片均匀的绿（实测线性绿 0.13）。它不是一个"风格"参数，
// 而是"背景亮度"参数 —— 要暗背景就必须给小数。
uniform float density = 0.14;
// 拖尾长度（占一个循环周期的比例）。太大每列就成了一条长亮条。
uniform float tail_len = 0.10;
// 拖尾相对亮头的亮度比。
//
// **对比度全靠它。** 第一版是 0.55，等于"亮头 + 一条半亮的尾巴"，
// 平均下来是一层均匀的绿雾。压到 0.22 之后，亮头依然是 1.0，
// 但尾巴几乎不可见 —— 画面才有"黑底上跑着亮字符"的矩阵感。
uniform float tail_gain = 0.22;
// 整体亮度。作用在颜色与 alpha 上，所以它是"雨滴本身多亮"，不是"背景多亮"。
uniform float brightness = 0.75;
// 纵向分格数 —— 决定"字符"的大小。太大就成细线了。
uniform float rows = 54.0;
// 底部与顶部的渐隐，避免雨"撞到"板边缘露馅。
uniform float edge_fade = 0.10;

float hash21(vec2 p) {
	p = fract(p * vec2(123.34, 456.21));
	p += dot(p, p + 45.32);
	return fract(p.x * p.y);
}

void fragment() {
	vec2 uv = UV;

	float col = floor(uv.x * columns);
	float frac_x = fract(uv.x * columns);

	// 每列一个固定的随机相位和速度倍率 —— 列与列不同步
	float ph = hash21(vec2(col, 1.0));
	float sp = speed * (0.55 + 0.95 * hash21(vec2(col, 7.0)));

	// t 是"这一列当前的下落进度"，随 TIME 增大而整体平移
	float t = fract(uv.y + TIME * sp + ph);

	// 该列是否激活
	float active = step(1.0 - density, hash21(vec2(col, 3.0)));

	// --- 亮头 ---
	float head = smoothstep(0.975, 1.0, t);

	// --- 拖尾：亮头经过之后留下的那段（t 刚回绕到 0 的位置 = 亮头上方）---
	float tail = 1.0 - smoothstep(0.0, tail_len, t);

	// --- 逐格随机点亮：拖尾因此断续成"字符"而不是实线 ---
	float ch = floor(t * rows);
	float lit = step(0.40, hash21(vec2(col, ch)));

	// --- 格间留缝 ---
	float gap_x = smoothstep(0.03, 0.20, frac_x) * smoothstep(1.0, 0.80, frac_x);
	float frac_y = fract(t * rows);
	float gap_y = smoothstep(0.04, 0.30, frac_y) * smoothstep(1.0, 0.72, frac_y);

	float a = active * gap_x * (
		head * gap_y * 1.0
		+ tail * lit * gap_y * tail_gain
	);

	// 上下渐隐，避免在板边缘硬切
	a *= smoothstep(0.0, edge_fade, uv.y) * smoothstep(1.0, 1.0 - edge_fade, uv.y);

	// 亮头再补一层白芯，让它更"跳"
	vec3 c = rain_color * a * 2.2;
	c += vec3(0.85, 1.0, 0.90) * head * active * gap_x * 0.55 * brightness;

	ALBEDO = c * brightness;
	EMISSION = c * brightness * 1.2;
	ALPHA = clamp(a * brightness * 1.6, 0.0, 1.0);
}
