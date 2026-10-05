shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never;

// 地面冲击波：贴着地面（XZ 平面）扩散的一圈光环。
//
// 和 vfx_hit 分开写而不是共用一个 shader，理由是**朝向不同**：
// 命中火花是朝向相机的 XY 面；冲击波必须躺在 XZ 地面上 ——
// 如果它立起来对着相机，就完全没有"砸在地上"的感觉了。
//
// ---------------------------------------------------------------------------
// **这个方向的代价要说清楚**：相机俯角只有 8°，地面上的圆投影到屏幕上
// 会被压成很扁的椭圆 —— 半径 0.78 m 时屏幕上宽约 184 px、**高只有 26 px**。
// 所以这个特效天生"不好看见"，必须靠**更大的半径 + 更厚的环 + 更高的增益**
// 才读得出来（第一版按"正常尺寸"给的 2.4 m / 0.30 m / 增益 1.6，
// 出图里几乎看不出有东西）。想更醒目就要往大里做，这是这个机位的物理限制。
//
// 视觉：外扩的亮环 + 内部若隐若现的横向波纹 + 中心残留的光斑。

uniform vec3 color : source_color = vec3(0.60, 1.0, 0.78);
uniform vec3 hot_color : source_color = vec3(1.0, 1.0, 1.0);
uniform float progress : hint_range(0.0, 1.0) = 0.0;
// 环的半径（米，最终值）
uniform float max_radius = 2.4;
// 环的厚度（米）
uniform float thickness = 0.30;
// 相机俯角的正弦。补偿 z 方向的透视压缩，让圆在屏幕上还是圆。
uniform float view_sin : hint_range(0.02, 1.0) = 0.139;
// 波纹圈数（内部的同心余波）
uniform float ripples = 2.0;
uniform float gain = 1.0;

/** 世界坐标（米）。**不能用 UV 算半径** —— UV 是归一化的，
 *  按 UV 算的话"半径 2.4 m"在长条形的四边形上会变成椭圆。 */
varying vec3 wpos;
/** 四边形在 XZ 上的半尺寸（米），由脚本按 mesh.size 传进来 */
uniform vec2 half_size = vec2(2.4, 2.4);
/** 四边形的中心世界坐标（x,z）—— 用于算"离爆点多远" */
uniform vec2 center_xz = vec2(0.0, 0.0);

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	// 离爆心的平面距离（米）
	vec2 d = wpos.xz - center_xz;
	// 把 z 方向除回 sin(俯角)，否则屏幕上是个扁的
	d.y /= max(view_sin, 0.02);
	float r = length(d);

	float life = 1.0 - progress;
	float fade = pow(life, 1.35);

	// 主环：半径随时间线性外扩
	float rr = max_radius * progress;
	// 环的厚度**下限**要有保证：8° 俯角下 z 方向压扁 sin8°≈0.14，
	// 环越细越看不见。给一个绝对下限 0.16 m，别让它随 progress 收到 0。
	float th = max(max(thickness * (1.0 - progress * 0.55), 0.16), 0.01);
	float ring = 1.0 - smoothstep(th * 0.25, th, abs(r - rr));

	// 内部余波：跟在主环后面的几圈更淡的同心环
	float rp = rr * 0.55;
	float rw = max(th * 2.2, 0.01);
	float ripple = 0.0;
	if (rp > 0.02) {
		float rl = abs(mod(r - rp, max(rw, 0.03)) - rw * 0.5);
		ripple = (1.0 - smoothstep(0.0, rw * 0.5, rl)) * 0.35;
	}

	// 中心残留光斑：一开始很亮，很快消失
	float core = (1.0 - smoothstep(0.0, max_radius * 0.30, r))
		* (1.0 - smoothstep(0.0, 0.25, progress));

	// 超出四边形范围就裁掉（避免看到四边形的边）
	float edge = 1.0 - smoothstep(0.86, 1.0, max(abs(UV.x), abs(UV.y)));

	// 增益：环给最高（它才是"冲击波"本体）。第一版给 1.6，
	// 出图里环几乎看不见 —— 因为加色混合下它要和**已经很亮的绿色地面**竞争，
	// 亮度不够就被地面吃掉了。这里按"要比地面亮一个档"来定。
	float i = (ring * 3.4 + ripple * 1.4 + core * 2.6) * fade * edge * gain;
	vec3 c = mix(color, hot_color, clamp(core * 1.3, 0.0, 1.0));
	ALBEDO = c * i;
	EMISSION = vec3(0.0);
}
