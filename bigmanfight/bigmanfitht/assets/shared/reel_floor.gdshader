shader_type spatial;

// =====================================================================
// 巡礼专用发光网格地面
// =====================================================================
//
// 为什么不能直接用游戏里的 `grid_floor.gdshader`：
//
//   那个着色器是给**正交相机 + 固定 8° 俯角**调的，它靠
//   `1.0 / sin(俯角)` 这个常数去补偿 z 方向的透视压缩 —— 正交投影下
//   "1 m 永远是 234 px"，这个补偿是对的。
//
//   但巡礼用的是**透视相机 + 环绕机位**：同一个平面上，近处的 1 m 在屏幕上
//   有 400 px，30 m 外的 1 m 只有 8 px。于是那个固定补偿会把近处的横线拉成
//   一根占满屏幕的粗亮带（实测出图：地面像铺了一条条白炽灯管）。
//
// 解法：**把线宽定义在屏幕空间，而不是世界空间。**
//   用 `fwidth()` 求"格坐标"在屏幕上的导数（= 1 格占几个像素），
//   再把"到最近格线的距离"除以它 —— 得到的距离单位是**像素**。
//   于是无论远近、无论什么角度，线永远是 1~2 px 宽。
//
// 这是"无限网格"的标准做法，也是唯一能在环绕机位下站得住的做法。

// 底板颜色（受光照，接角色阴影）
uniform vec3 base_color : source_color = vec3(0.010, 0.022, 0.017);
// 远处底板融入雾色
uniform vec3 far_color : source_color = vec3(0.008, 0.030, 0.020);
// 细网格线
uniform vec3 line_color : source_color = vec3(0.16, 0.88, 0.44);
// 主网格线（每 major_every 格）
uniform vec3 major_color : source_color = vec3(0.55, 1.0, 0.75);

// 格边长（米）
uniform float cell_size = 1.0;
uniform float major_every = 5.0;
// **屏幕空间**半宽（像素）—— 这才是"线多粗"
uniform float minor_px = 1.0;
uniform float major_px = 1.5;

// 距离淡出（米）
uniform float fade_start = 8.0;
uniform float fade_end = 46.0;
// 近处压暗：贴着地面拍时，近处不该是一片白
uniform float near_dim_dist = 6.0;
uniform float near_dim = 0.40;

// 扫描光带
uniform float sweep_gain = 0.18;

varying vec3 wpos;

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

// 屏幕空间恒定线宽的网格覆盖度。
// g: 以"格"为单位的坐标；half_px: 线在屏幕上的半宽（像素）
float grid_cover(vec2 g, float half_px) {
	vec2 dd = max(fwidth(g), vec2(1e-6));
	vec2 d = abs(fract(g - 0.5) - 0.5) / dd;   // 到最近格线的距离，单位 = 屏幕像素
	return 1.0 - clamp(min(d.x, d.y) / half_px, 0.0, 1.0);
}

void fragment() {
	vec2 g_minor = vec2(wpos.x, wpos.z) / cell_size;
	vec2 g_major = g_minor / major_every;

	float minor = grid_cover(g_minor, minor_px);
	float major = grid_cover(g_major, major_px);
	// 取 max 而不是相加：相交处不会叠成一个光斑
	float cover = max(minor * (1.0 - major), major);

	float dist = length(wpos.xz - CAMERA_POSITION_WORLD.xz);
	float fade = 1.0 - smoothstep(fade_start, fade_end, dist);

	// 扫描光带：沿世界 -Z 推进的一条亮带，让静止画面有呼吸
	float phase = fract(TIME * 0.16);
	float band_z = mix(-70.0, 24.0, phase);
	float band = exp(-pow((wpos.z - band_z) * 0.085, 2.0));

	// 近处压暗
	float near_dim_f = mix(near_dim, 1.0, clamp(dist / max(near_dim_dist, 0.001), 0.0, 1.0));

	ALBEDO = mix(base_color, far_color, smoothstep(fade_start, fade_end, dist));
	ALBEDO += (line_color * minor * 0.16 + major_color * major * 0.20) * fade * near_dim_f;
	ALBEDO *= near_dim_f;

	EMISSION = line_color * minor * fade * near_dim_f * 0.60
		+ major_color * major * fade * near_dim_f * 0.95
		+ line_color * band * sweep_gain * fade;
}
