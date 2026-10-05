shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never;

// 蓄力/爆气光环：一张竖立的四边形，画向上流动的能量条纹。
//
// 用途：蓄力（Charge）、大招起手（Ultimate_Start）、以及被打倒起身时的"暴气"。
// 它和命中火花的关键区别是**持续**：命中火花是一瞬间（progress 0→1 走完就没了），
// 光环要能在几秒里一直存在并且"在动"，所以它不靠 progress，靠 TIME。
//
// 视觉三层：
//   1. 向上的流动条纹 —— 能量在往上升（"蓄"的读法）
//   2. 底部聚集光斑   —— 能量从脚下起来
//   3. 垂直渐隐       —— 上下两头都要收掉，不然会看到四边形的直边

uniform vec3 color : source_color = vec3(0.45, 1.0, 0.66);
uniform vec3 hot_color : source_color = vec3(0.90, 1.0, 0.95);
// 条纹数量（按 UV 宽度均分）
uniform float columns = 22.0;
// 上升速度（每秒走过的 UV 比例）
uniform float speed = 0.55;
// 条纹占格子宽度的比例。**它决定条纹之间的空档有多宽** ——
// 空档必须是 0（全黑），否则整块会糊成一片白板（踩过：第一版用
// `mix(1.0, wx, 1.0 - w)` 收窄条纹，结果 wx=0 时还剩 0.34 的底噪，
// 屏幕上就是一整块白）。
uniform float streak_w : hint_range(0.05, 1.0) = 0.62;
// 有几成条纹是亮的（其余留空，让光环透气）
uniform float density = 0.55;
// 底部的聚集光斑半径（UV 比例）
uniform float base_glow = 0.55;
// 条纹与底光的合成增益。**别调太高** —— 加色混合下很容易一路顶到纯白。
uniform float streak_gain = 0.85;
uniform float base_gain = 0.55;
// 整体强度 —— 由脚本按"蓄力进度"驱动，做出"越蓄越亮"
uniform float gain : hint_range(0.0, 2.0) = 1.0;
// 整体生命周期（0=刚出现，1=该消失了）。和 gain 分开：
// gain 管强度，life 管"还没到该收的时候"。
uniform float life : hint_range(0.0, 1.0) = 1.0;

float hash21(vec2 p) {
	p = fract(p * vec2(123.34, 456.21));
	p += dot(p, p + 45.32);
	return fract(p.x * p.y);
}

void fragment() {
	vec2 uv = UV;

	// --- 1. 向上的流动条纹 ---
	float col = floor(uv.x * columns);
	float fx = fract(uv.x * columns);
	float lit = step(1.0 - density, hash21(vec2(col, 5.0)));
	// 每列不同相位 + 不同速度
	float ph = hash21(vec2(col, 11.0));
	float sp = speed * (0.6 + 0.9 * hash21(vec2(col, 17.0)));
	// 条纹往上走。QuadMesh 的 UV 原点在**左上**，所以 uv.y 增大 = 往下，
	// 让相位随 TIME 增大 → 条纹向上移动。
	float t = fract(uv.y * 1.6 - TIME * sp + ph);

	// 条纹本体：一段亮起的余迹，头端更亮
	float head = smoothstep(0.86, 1.0, t);
	float tail = (1.0 - smoothstep(0.0, 0.65, t)) * 0.45;
	float streak = (head + tail) * lit;

	// 横向收窄：格心最亮、到格边收到**真正 0**
	float dx = abs(fx - 0.5) * 2.0;
	float wx = 1.0 - smoothstep(1.0 - streak_w, 1.0, dx);
	float s = streak * wx;

	// --- 2. 底部聚集光斑 ---
	// 底 = uv.y 接近 1
	float base = exp(-pow((1.0 - uv.y) / max(base_glow, 0.001), 2.0));

	// --- 3. 垂直渐隐（上下都要收掉，不然会看到四边形的直边）---
	//
	// **注意不能写 smoothstep(1.0, 0.86, uv.y)** —— Godot 文档明确说
	// `edge0 >= edge1` 时结果未定义。第一版这么写，顶部渐隐完全没生效，
	// 出图里光环顶上是一条刀切的直边。降序必须写成 `1.0 - smoothstep(lo, hi, x)`。
	float vfade = smoothstep(0.0, 0.14, uv.y) * (1.0 - smoothstep(0.80, 1.0, uv.y));

	float i = (s * streak_gain + base * base_gain) * vfade * gain * life;
	vec3 c = mix(color, hot_color, clamp(base * 1.1 + head * 0.4, 0.0, 1.0));
	ALBEDO = c * i;
	EMISSION = vec3(0.0);
}
