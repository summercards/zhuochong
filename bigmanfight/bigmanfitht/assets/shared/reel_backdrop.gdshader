shader_type spatial;
render_mode unshaded, cull_disabled;

// =====================================================================
// 巡礼专用远景幕墙
// =====================================================================
//
// 同 `matrix_backdrop.gdshader` 的视觉语言（地平线辉光 + 数据廊道 +
// 线框网格 + 随机数据块），但**长度参数全部改成 uniform 并且按米标定**。
//
// 为什么要另写一份而不是复用：
//   原来那份是给正交相机调的，可见高度只有 **1.375 m**（它的头注释里推导过），
//   所以把 `0.006 / 0.024`（网格线宽）、`0.045`（柱顶收刀软边）这类
//   尺寸**硬编码**进了着色器 —— 在 1.375 m 的窗口里它们是对的。
//
//   巡礼用透视机位，板子摆在 8~16 m 外，一帧里装下约 **11 m** 的内容
//   （8 倍）。那些硬编码的宽度会细到看不见、柱顶会切出硬边。
//   所以这里把每一个尺寸都提为 uniform，由 `reel_env.gd` 按实际构图给值。
//
// 图案全部按 **wpos**（世界坐标）算，不按 UV —— 板子很高而可见的只是一段，
// 按 UV 算会把图案拉成面条。

uniform vec3 deep_color : source_color = vec3(0.0008, 0.0028, 0.0018);
uniform vec3 haze_color : source_color = vec3(0.0016, 0.0060, 0.0038);
uniform vec3 glow_color : source_color = vec3(0.20, 1.0, 0.46);

// 地平线的世界高度（= 地面 y=0）
uniform float horizon_y = 0.0;

// --- 地平线辉光带 ---
// 峰值由辉光后处理的上限决定，不由审美决定（原实现实测压到 0.55 才不糊背景）
uniform float glow_gain = 0.50;
uniform float glow_width = 0.45;

// 贴地雾色衰减到 deep_color 所需高度（米）
uniform float haze_height = 6.8;

// --- 竖直数据廊道 ---
uniform float conduit_pitch = 3.4;
uniform float conduit_width = 0.10;
uniform float conduit_gain = 0.28;
uniform float conduit_top_min = 2.2;
uniform float conduit_top_max = 9.5;
// 柱顶收刀的软边（米）
uniform float conduit_edge = 0.36;

// --- 线框网格 ---
uniform float grid_cell = 3.2;
// 线半宽（米）
uniform float grid_width = 0.055;
uniform float grid_gain = 0.030;
uniform float grid_falloff = 0.18;

// --- 随机数据块 ---
uniform float block_cell = 1.10;
uniform float block_gain = 0.050;
uniform float block_falloff = 0.14;

// 整块板的总增益（背景亮度的唯一闸门）
uniform float gain = 0.085;

varying vec3 wpos;


void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}


float hash11(float n) {
	return fract(sin(n * 127.1) * 43758.5453);
}

float hash21(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}


void fragment() {
	float wy = wpos.y - horizon_y;
	float above = max(wy, 0.0);

	// --- 1. 纵向渐变：贴地雾色 → 顶部黑 ---
	vec3 col = mix(haze_color, deep_color, sqrt(clamp(above / max(haze_height, 0.01), 0.0, 1.0)));

	// --- 2. 地平线辉光带 ---
	float glow = exp(-pow(above / max(glow_width, 0.001), 2.0));
	col += glow_color * glow * glow_gain;
	col += glow_color * glow_gain * 0.22 * exp(-pow(max(-wy, 0.0) / 0.16, 2.0));

	// --- 3. 竖直数据廊道 ---
	float cx = wpos.x / conduit_pitch;
	float cf = fract(cx);
	float cbin = floor(cx);
	float cdist = min(cf, 1.0 - cf) * conduit_pitch;
	float conduit = 1.0 - smoothstep(conduit_width * 0.4, conduit_width, cdist);
	float con_lit = step(0.42, hash11(cbin));
	float con_top = mix(conduit_top_min, conduit_top_max, hash11(cbin * 3.7 + 11.0));
	col += glow_color * conduit * con_lit * conduit_gain
		* exp(-above / max(con_top, 0.05));
	// 柱顶收一刀，读出"这根柱子有头"（软边宽度改成按米给）
	col += glow_color * conduit * con_lit * conduit_gain * 0.75
		* exp(-pow((above - con_top) / max(conduit_edge, 0.001), 2.0));

	// --- 4a. 线框网格 ---
	vec2 gcoord = vec2(wpos.x, above);
	vec2 gdist = abs(fract(gcoord / grid_cell) - 0.5) * grid_cell;
	float gl = 1.0 - smoothstep(grid_width * 0.25, grid_width, min(gdist.x, gdist.y));
	col += glow_color * gl * grid_gain * exp(-above * grid_falloff);

	// --- 4b. 数据块 ---
	vec2 bcell = floor(gcoord / block_cell);
	float bl = step(0.90, hash21(bcell));
	vec2 bf = abs(fract(gcoord / block_cell) - 0.5) * 2.0;
	float bmask = 1.0 - smoothstep(0.55, 0.92, max(bf.x, bf.y));
	col += glow_color * bl * bmask * block_gain * exp(-above * block_falloff);

	// 地平线以下压暗，让"地面接缝"干净
	col *= mix(1.0, 0.30, clamp(-wy / 0.80, 0.0, 1.0));

	col *= gain;

	ALBEDO = col;
	// 走 EMISSION 才能被 glow 采样到
	EMISSION = col * 0.22;
}
