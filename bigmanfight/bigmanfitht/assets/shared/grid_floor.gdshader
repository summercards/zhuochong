shader_type spatial;

// 矩阵虚拟空间的发光网格地面。
//
// 为什么用着色器画网格，而不是摆一堆细长方体当线：
//   1. **线宽和密度不用摆几何** —— 1 m 一格、5 m 一条主线，全是公式算的，
//      改一个 uniform 就换密度，不用增删节点。
//   2. **无限延伸** —— 地面只要够大，网格自动铺满，不会出现"走到边上没线了"。
//   3. 网格线走 EMISSION（会进 glow 发光），底板走 ALBEDO（**接收角色阴影**）。
//      刻意不加 `unshaded`：一旦 unshaded 就不再接收阴影，角色会像浮在地上。
//
// ---------------------------------------------------------------------------
// 关于"横线看不见"这个坑（第一版的实测症状）：
//
//   相机俯角 8° 时，地面的 z 方向被压缩了 sin(8°) = 0.139。
//   一条 14 mm 半宽的**横**线（沿 x 走、z 固定）在屏幕上只剩
//   0.014 × 0.139 × 236 px/m ≈ **0.46 px** —— 完全看不见，
//   于是画面里只剩等距的竖线，像一排栅栏而不是网格。
//
//   解法：把 z 方向的判线宽度乘 1/sin(俯角)（= 7.2）补偿回来，
//   两个方向的线在屏幕上就一样粗了。这就是 view_sin 这个 uniform 的全部作用。
// ---------------------------------------------------------------------------

// 底板颜色（受光照，能接阴影）
uniform vec3 base_color : source_color = vec3(0.010, 0.026, 0.019);
// 远处底板融入的颜色（应当和远景幕墙的 haze 接近，让地平线接缝不显眼）。
// 实测：这块板的远端在关闭幕墙后会露出一片 (78,87,74) 的灰绿，偏亮偏灰。
// 压到和幕墙 haze 同一量级，接缝处就不会跳。
uniform vec3 far_color : source_color = vec3(0.0042, 0.0140, 0.0090);
// 细网格线（自发光）
uniform vec3 line_color : source_color = vec3(0.14, 0.90, 0.42);
// 主网格线（每 major_every 格一条，更亮）
uniform vec3 major_color : source_color = vec3(0.52, 1.0, 0.72);
// 格边长（米）—— 1 m 约等于角色半个身位，便于目测距离
uniform float cell_size = 1.0;
// 每几格一条主线
uniform float major_every = 5.0;
// 细线半宽（米）—— 这个宽度是"正面看"的宽度，z 方向会再乘 1/view_sin 补偿
uniform float line_width = 0.014;
// 主线半宽（米）
uniform float major_width = 0.030;
// 线亮度
uniform float line_gain = 1.0;
// **俯角的正弦**。用来补偿 z 方向的透视压缩。俯角 8° → 0.139。
// 这个值必须和 Game.CAM_PITCH_DEG 一致，由 stage.gd 传进来，不要在着色器里写死。
uniform float view_sin : hint_range(0.02, 1.0) = 0.139;
// 距离淡出：从 fade_start 米开始淡，到 fade_end 米完全消失
uniform float fade_start = 4.0;
uniform float fade_end = 15.0;
// 扫描光带
uniform float sweep_speed = 5.5;
uniform float sweep_period = 26.0;
uniform float sweep_gain = 0.22;

// 世界坐标。Godot 4 **没有**内置的 world position（`world_position` 不存在），
// 必须自己在 vertex 里乘 MODEL_MATRIX 再传给 fragment。
// 第一版就是漏了这步，直接写 world_position，编译不过。
varying vec3 wpos;


void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}


// 到最近格线的距离（米）
float line_dist(float coord, float size) {
	float f = fract(coord / size);
	return min(f, 1.0 - f) * size;
}


// 一条轴向的格线覆盖度：0 = 在格心，1 = 正好压在线上
float axis_line(float coord, float size, float half_width) {
	float d = line_dist(coord, size);
	return 1.0 - smoothstep(half_width * 0.35, half_width, d);
}


void fragment() {
	// 地面是 y=0 的水平面，格子在 XZ 上展开
	// 补偿系数：z 方向被俯角压扁了 sin(θ) 倍，判线宽度要除回去
	float stretch = 1.0 / max(view_sin, 0.02);

	// 取两个方向的 max 而不是相加 —— 相加会让交叉点亮成一个个光斑
	float minor = max(
		axis_line(wpos.x, cell_size, line_width),
		axis_line(wpos.z, cell_size, line_width * stretch)
	);
	float major = max(
		axis_line(wpos.x, cell_size * major_every, major_width),
		axis_line(wpos.z, cell_size * major_every, major_width * stretch)
	);

	// --- 距离淡出：远处别糊成一片亮网 ---
	float dist = length(wpos - CAMERA_POSITION_WORLD);
	float fade = 1.0 - smoothstep(fade_start, fade_end, dist);

	// --- 扫描光带：沿 -Z（朝相机方向）推进的一条亮带 ---
	float phase = fract(TIME * sweep_speed / sweep_period);
	float band_z = mix(-sweep_period, 10.0, phase);
	float band = exp(-pow((wpos.z - band_z) * 0.22, 2.0));

	float glow = min(minor * (1.0 - major) + major, 1.0) * line_gain * fade;

	// 底板远处融入雾色，避免和远景幕墙撞出一条硬边
	float dfade = smoothstep(fade_start, fade_end, dist);
	ALBEDO = mix(base_color, far_color, dfade);

	EMISSION = line_color * glow * 1.25
		+ major_color * major * glow * 1.55
		+ line_color * band * sweep_gain * fade;

	// 混一点线的亮度到底板，让线看起来"烧"在地面上而不是浮着
	ALBEDO += line_color * glow * 0.30;
}
