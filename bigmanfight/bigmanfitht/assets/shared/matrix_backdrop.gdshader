shader_type spatial;
render_mode unshaded, cull_disabled;

// 远景幕墙：把"地面之上"那半屏填成有纵深的虚拟空间。
//
// ---------------------------------------------------------------------------
// 为什么必须有这块板（这是这个场景最容易做错的地方）：
//
//   正交相机俯视时，**地面平面的投影会铺满整个画面**。推导一下：
//   相机 y=1.884、俯角 8°，地面点 (0,0,z) 的屏幕纵坐标
//       ndc_y = (-0.892 - 0.139·z) / 1.525
//   z → -∞ 时 ndc_y → +∞ —— "无限远的地面"跑到了屏幕**上方之外**。
//   结论：画面里根本不存在"天空"，上半屏看到的其实也是地面（远处那一段），
//   一片死黑的绿，没有任何信息量。
//
//   第一版就是没意识到这点，把远处的地面当成了"背景"，在上面摆了数据柱。
//   一根 1.6 m 宽、最高 9 m 的**不透明**方块（x=0.5, z=-5.5）在竖直视野只有
//   3.05 m 的相机里，屏幕上就是一块占满整个画面高度、宽 29% 的**黑墙**。
//
//   解法：在 z = BACKDROP_Z（-7.6）竖一块**竖直**的板挡住远处那段地面。
//   它会挡住后面的地面，于是屏幕上重新出现一条"地平线"，
//   上半屏才有地方放远景。
//
// ---------------------------------------------------------------------------
// 这块板在屏幕上只露出很窄的一条 —— 参数必须按这个算，不能凭感觉：
//
//   板平面 z = -7.6 上的高度 y 投影到屏幕：
//       ndc_y = [(y - 1.884)·0.990 + 2.029] / 1.525
//   板底 y=0 → ndc = +0.108；屏幕顶 ndc=+1.0 → y = 1.375。
//
//   ⟹ **可见的板只有 y ∈ [0, 1.375] 这 1.375 m**，占屏幕顶部 44.6%。
//      所以 haze_height 必须 < 1.4（第一版设了 3.0，等于整个可见区都泡在雾色里，
//      结果上半屏糊成一整片亮绿），glow_width 必须 ~0.09（0.55 会糊掉半个屏幕）。
//   ⟹ 每一个 uniform 都是按"1.375 m 能装下什么"来定的。
//
// 板上内容自下而上：
//   1. 地平线辉光带 —— 落在 y=0（地面高度）。这一行恰好是"地面被板挡住的接缝"，
//      用它把一条硬接缝变成"城市灯火"。这是整块板存在的主要理由。
//   2. 数据廊道 —— 细亮竖条，高矮不一，给远景骨架。
//   3. 线框网格 + 数据块 —— 给远景纹理，否则只是渐变。
//   4. 上方渐暗 —— 顶部要真正黑下去，不然和雨幕叠在一起会发灰。
//
// 所有图案都按 **wpos**（世界坐标）算，不按 UV：
// 板高 26 m 而可见的只有底部 1.375 m，按 UV 算会把图案拉成面条。

// 顶部的远景色（必须够黑，否则整块板会"发灰"）
uniform vec3 deep_color : source_color = vec3(0.001, 0.005, 0.003);
// 贴地处的雾色。
//
// **这个值是背景亮度的总闸门。** 实测过程：把它从 0.005 扫到 0.0008，
// 上半屏几乎纹丝不动 —— 说明亮度不来自单一项，而是 haze + conduit + grid
// + block **四项累加**（0.018 + 0.012 + 0.009 + 0.0075 ≈ 0.047 线性绿，
// 再乘 1.45 的 ALBEDO+EMISSION ≈ 0.068，与实测的 +0.065 吻合）。
// 所以调暗必须**四项一起降**，只压 haze 是没用的。
uniform vec3 haze_color : source_color = vec3(0.0016, 0.0060, 0.0038);
// 辉光 / 廊道 / 网格的绿
uniform vec3 glow_color : source_color = vec3(0.20, 1.0, 0.46);

// 地平线所在的世界高度（= 地面 y=0）
uniform float horizon_y = 0.0;
// 辉光带强度 / 厚度（米）。
//
// **峰值的上限由辉光后处理决定，不由审美决定。** 这一带是全场景最亮的源，
// 峰值每高一点，bloom 就多糊一层到整屏。
// 峰值 = glow_gain × glow_color.g = 1.0 线性，×1.22 = 1.22，
// 刚好压在 glow_hdr_threshold(1.30) 之下 —— 想让它发光就往上加一点。
uniform float glow_gain = 1.0;
uniform float glow_width = 0.055;
// 雾色衰减到 deep_color 所需的高度（米）。**必须 < 可见上限 1.375**
uniform float haze_height = 0.85;

// 竖直数据廊道。这一项是"结构感"的主要来源，所以保持最高的单项增益，
// 但把 duty（宽度/间距）压到 6%，避免它变成一层均匀的绿。
uniform float conduit_pitch = 0.44;
uniform float conduit_width = 0.013;
uniform float conduit_gain = 0.30;
// 廊道高度范围（米）—— 上限也不能超过可见高度 1.375
uniform float conduit_top_min = 0.30;
uniform float conduit_top_max = 1.24;

// 线框网格
uniform float grid_cell = 0.40;
uniform float grid_gain = 0.026;
uniform float grid_falloff = 1.40;

// 数据块（随机点亮的小方块，给远景"有东西"的感觉）
uniform float block_cell = 0.14;
uniform float block_gain = 0.055;
uniform float block_falloff = 1.10;

// 整块板的**总增益** —— 背景亮度的唯一闸门。
//
// 为什么需要一个"总闸门"，而不是继续微调上面那些分项：
//   分项（haze / conduit / grid / block）负责**形状**：哪里有线、哪里是块、怎么衰减。
//   gain 负责**亮度**：整块板统一乘一个数。
//   两者分开之后，换风格只需要重扫 gain 一个数，不用重推十几个分项。
//
// 取值依据（实测标定）：
//   分项叠加后上半屏约 0.0063 线性绿（≈ sRGB 32）。gain=2.0 时
//   0.0063×2.0×1.22 ≈ 0.0154 → sRGB ≈ 36，是一个"暗但看得见"的远景底。
uniform float gain = 2.0;

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
	// 相对地平线的高度。负值 = 地面以下（被地面挡住，看不见）。
	float wy = wpos.y - horizon_y;
	float above = max(wy, 0.0);

	// --- 1. 基础纵向渐变：贴地雾色 → 顶部黑 ---
	// 用 sqrt 让雾色收得慢一点、亮带上方还留一层薄雾，避免出现"雾带 + 黑"的硬分界。
	vec3 col = mix(haze_color, deep_color, sqrt(clamp(above / haze_height, 0.0, 1.0)));

	// --- 2. 地平线辉光带 ---
	//
	// **这条带子刻意放在 gain 之外。** 它是画面里唯一的"结构性高压线"，
	// 要一直保持亮；如果跟着 gain（0.085）一起缩，就彻底看不见了。
	// 所以这里算的是"高频结构"层，最后不乘 gain。
	vec3 band = vec3(0.0);
	float glow = exp(-pow(above / max(glow_width, 0.001), 2.0));
	band += glow_color * glow * glow_gain;
	// 地平线两侧各留一点光，避免板底与地面交界处出现一条黑缝。
	//
	// **必须用 abs(wy)，不能用 max(-wy, 0.0)。** 这里踩过一个很隐蔽的坑：
	// 写成 max(-wy, 0.0) 时，在地平线**上方**这个值恒等于 0，
	// 于是 exp(-0) = 1 —— 本该只作用于 ±0.16 m 的那一小撮光，
	// 变成了在整个上半屏满强度常亮。验算：glow_color.g(1.0) × 0.55 × 0.22 = 0.121，
	// ×1.22(ALBEDO+EMISSION) = 0.148 线性 → sRGB **107**，而实测是 108。完全吻合。
	// 我一开始把这 13 倍偏差归因成"管线乘数"，其实一行就是全部原因。
	band += glow_color * glow_gain * 0.22 * exp(-pow(abs(wy) / 0.16, 2.0));

	// --- 3. 竖直数据廊道（走 gain，因为它属于"背景底噪"而不是"结构光源"）---
	float cx = wpos.x / conduit_pitch;
	float cf = fract(cx);
	float cbin = floor(cx);
	float cdist = min(cf, 1.0 - cf) * conduit_pitch;
	float conduit = 1.0 - smoothstep(conduit_width * 0.4, conduit_width, cdist);
	// 只有一部分廊道点亮，避免变成一排等距栅栏
	float con_lit = step(0.42, hash11(cbin));
	float con_top = mix(conduit_top_min, conduit_top_max, hash11(cbin * 3.7 + 11.0));
	// 亮度沿高度衰减到各自的"柱顶"
	col += glow_color * conduit * con_lit * conduit_gain
		* exp(-above / max(con_top, 0.05));
	// 柱顶收一刀，读出"这根柱子有头"
	col += glow_color * conduit * con_lit * conduit_gain * 0.75
		* exp(-pow((above - con_top) / 0.045, 2.0));

	// --- 4a. 线框网格 ---
	vec2 gcoord = vec2(wpos.x, above);
	vec2 gdist = abs(fract(gcoord / grid_cell) - 0.5) * grid_cell;
	float gl = 1.0 - smoothstep(0.006, 0.024, min(gdist.x, gdist.y));
	col += glow_color * gl * grid_gain * exp(-above * grid_falloff);

	// --- 4b. 数据块：随机点亮的小方块 ---
	vec2 bcell = floor(gcoord / block_cell);
	float bl = step(0.90, hash21(bcell));
	// 格内留边，让块与块分开
	vec2 bf = abs(fract(gcoord / block_cell) - 0.5) * 2.0;
	float bmask = (1.0 - smoothstep(0.55, 0.92, max(bf.x, bf.y)));
	col += glow_color * bl * bmask * block_gain * exp(-above * block_falloff);

	// 两层合成：低频底色乘 gain，高频结构层不乘
	vec3 out_col = col * gain + band;
	// 地平线以下压暗，让"地面接缝"干净
	out_col *= mix(1.0, 0.30, clamp(-wy / 0.80, 0.0, 1.0));

	ALBEDO = out_col;
	// 走 EMISSION 才能被 glow 采样到 —— 地平线带靠这一步"发亮"。
	// 与 ALBEDO 是**相加**关系，所以系数等于把整板亮度再放大 (1+系数) 倍。
	EMISSION = out_col * 0.22;
}
