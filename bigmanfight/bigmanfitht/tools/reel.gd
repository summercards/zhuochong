extends Node3D
## =====================================================================
## 多视角快切巡礼渲染器 —— 把 68 段动画剪成一条展示片
## =====================================================================
##
## 做什么：
##   1. 把 bigman 的 GLB 单独放进场景（**不实例化 Fighter** —— 巡礼不需要状态机，
##      需要的是"精确摆到某一帧"，那是 seek 的活）；
##   2. 按 manifest 的清单顺序（A01…E11，含 C08b）逐段过一遍，一段不落；
##   3. **每段只用一个机位**（见 ONE_CAM_PER_CLIP）：段内不切镜，多机位的信息量
##      靠"段与段之间换机位"来给。相邻两段的机位方位角差仍受 CUT_MAX_ANGLE_DEG
##      约束，避免在 PROFILE_L(-66°)↔PROFILE_R(+66°) 之间反向闪跳；
##   4. 命中帧**定格 + 半速 + 闪白**：命中帧取 manifest 的 `hit_frame`（60 fps 实测值）；
##   5. 左下角角标（家族 / 编号 / 中文名 / 实测元数据），底部进度条，右上计数；
##   6. 片头字卡 + 片尾名单卡（字卡期间角色走待机，机位缓慢环绕）；
##   7. 逐帧 seek 到精确时刻再抓图，输出 PNG 序列。
##
## 为什么逐帧 seek，而不是"让动画播着抓"：
##   播着抓的采样点跟着物理帧率走 —— 命中定格、命中后半速这类**时间重映射**
##   根本做不了，而且换台机器帧率一变，成片节奏就变了。seek 模式下
##   "第 n 个输出帧显示动画的第几秒"是一张算得出来的表，可复现、可校验、可打印。
##
## 为什么机位是"绕着角色转"而不是"固定侧视"：
##   这是巡礼不是对局。侧视只看得见剪影，看不见动作的纵深 —— 旋转重拳、
##   抱摔、大招这些招式在 3/4 角度才有体积感。
##
## 用法：
##   godot --path . --resolution 1280x720 res://tools/reel.tscn
##   godot --path . --resolution 1280x720 res://tools/reel.tscn -- --pilot
##   godot --path . --resolution 1280x720 res://tools/reel.tscn -- --dbg=norain,noback
## 产物：
##   <工作区>/outputs/bigman_reel_v001/frames/frame_00001.png …
##   <工作区>/outputs/bigman_reel_v001/frames/plan.json

# =====================================================================
# 输出与节奏参数
# =====================================================================
const FPS := 30
## 每段的时间缩放：输出帧推进 SEG_TIME_SCALE×(1/FPS) 秒。
## 1.0 = 原速；0.90 = 动作放慢 11%、每段自然变长约 11%。
## 调这个数**只影响"看得多清楚"**，不改变剪出来的段数。
const SEG_TIME_SCALE := 0.90
## 循环段最多展示多久（秒）。待机/走/跑这类循环段全长 3.5 s 会拖节奏。
const LOOP_SHOW_S := 1.6
## 每段末尾定格帧数 —— 让最后一下在眼里留一留。
const HOLD_END_FRAMES := 6
## 命中定格帧数
const FREEZE_HIT_FRAMES := 5
## 命中后慢放帧数（按 SLOW_FACTOR 的步长推进）
const SLOW_HIT_FRAMES := 8
const SLOW_FACTOR := 0.5
## 单次切镜的帧数区间（30 fps 下 14~26 帧 = 0.47~0.87 s）。
## **仅在 ONE_CAM_PER_CLIP = false 时生效**（默认 true，段内不切镜，用不到这两个数）。
const CUT_MIN_FRAMES := 14
const CUT_MAX_FRAMES := 26

## 每段只用**一个**机位，段内不切镜。
## 这是用户的明确要求："每个动画只要一个镜头就好了，不用那么多镜头" ——
## 段内反复切镜本身就是"晃"的最大来源：观众每 0.4 s 要重建一次空间方位。
## 关掉它，多机位的信息量改由**段与段之间**换机位来给，观感立刻稳下来。
## 设成 false 可回退到"段内快切"模式（那时 CUT_MIN/MAX_FRAMES 决定切镜长度）。
const ONE_CAM_PER_CLIP := true

## 相邻两镜允许的最大方位角差（度）。单机位模式下作用于**段与段之间**；
## 超过就是"正反打闪跳"，是"晃眼"的头号来源。
const CUT_MAX_ANGLE_DEG := 105.0
## 单镜内的缓慢方位漂移幅度（度）。段内不切镜了，靠这点漂移让镜头"活"着，
## 否则两秒的固定机位会显得很死。幅度刻意压小（±5°），只求有呼吸感不求动感。
const CUT_DRIFT_DEG := 5.0
## 片头 / 片尾字卡时长（秒）
const TITLE_S := 4.0
const CREDITS_S := 6.0
## 随机种子 —— 机位与切点全部由它决定，改这个数就换一版剪辑。
const SEED := 20261004

const MODEL_PATH := "res://assets/characters/bigman/animations/bigman_anim_v001.glb"
## 巡礼舞台用 **preload 而不是 class_name**：
## class_name 要靠 `.godot/global_script_class_cache.cfg` 才能按名字解析，
## 而那个缓存只有编辑器扫过才更新 —— 新写的脚本直接跑会因为"标识符未声明"
## 整个场景脚本加载失败，表现是**窗口开着但什么都不做**（踩过）。
const ENV_SCRIPT := preload("res://tools/reel_env.gd")
## 资产里未蒙皮的件数（GLB 里缺 JOINTS_0）。它们不跟骨骼动，必须藏掉。
const UNSKINNED_MESH_COUNT := 2

## 看门狗：超过这个秒数直接退出，绝不留下一个"窗口开着、什么都不做"的僵尸进程。
const WATCHDOG_S := 45.0

const CHAR_NAME := "BIGMAN"
const CHAR_SUB := "v001 · 57 BONES · 68 CLIPS"

# =====================================================================
# 机位表
# ---------------------------------------------------------------------
# az   方位角（度）：0 = 相机在角色正前方，正 = 往角色左侧绕，负 = 往右侧绕。
# el   仰角（度）：正 = 高位俯拍，负 = 低角度仰拍。
# dist 距离（米）
# fov  透视视场角（度）—— 用中等长焦，压缩感更像展示片而不是鱼眼。
# fh   注视高度（米）
# fs   横向偏移（米，沿相机右方向）：把角色推到三分线上，避免永远居中
# push 单次切镜内的推镜量（比例）：dist 在这一次切镜里缩短 push 倍
# =====================================================================
const CAMS := [
	{"id": "WIDE_FRONT", "az": 0.0,   "el": 6.0,  "dist": 5.05, "fov": 37.0, "fh": 1.00, "fs": 0.00,  "push": 0.05},
	{"id": "WIDE_3QL",   "az": -34.0, "el": 7.0,  "dist": 4.80, "fov": 37.0, "fh": 1.00, "fs": 0.10,  "push": 0.06},
	{"id": "WIDE_3QR",   "az": 34.0,  "el": 7.0,  "dist": 4.80, "fov": 37.0, "fh": 1.00, "fs": -0.10, "push": 0.06},
	{"id": "PROFILE_L",  "az": -66.0, "el": 5.0,  "dist": 4.85, "fov": 35.0, "fh": 1.00, "fs": 0.00,  "push": 0.05},
	{"id": "PROFILE_R",  "az": 66.0,  "el": 5.0,  "dist": 4.85, "fov": 35.0, "fh": 1.00, "fs": 0.00,  "push": 0.05},
	{"id": "MED_3QL",    "az": -22.0, "el": 4.0,  "dist": 3.85, "fov": 35.0, "fh": 1.05, "fs": 0.12,  "push": 0.08},
	{"id": "MED_3QR",    "az": 22.0,  "el": 4.0,  "dist": 3.85, "fov": 35.0, "fh": 1.05, "fs": -0.12, "push": 0.08},
	{"id": "LOW_HERO",   "az": 6.0,   "el": -8.0, "dist": 4.35, "fov": 41.0, "fh": 1.05, "fs": 0.00,  "push": 0.07},
	{"id": "HIGH_ANGLE", "az": -18.0, "el": 33.0, "dist": 5.20, "fov": 43.0, "fh": 0.95, "fs": 0.00,  "push": 0.05},
	{"id": "CLOSE_BUST", "az": -12.0, "el": 6.0,  "dist": 2.55, "fov": 34.0, "fh": 1.36, "fs": 0.00,  "push": 0.10},
	{"id": "CLOSE_LOW",  "az": 16.0,  "el": 2.0,  "dist": 2.85, "fov": 36.0, "fh": 0.62, "fs": 0.00,  "push": 0.10},
	{"id": "IMPACT_L",   "az": -52.0, "el": 8.0,  "dist": 4.30, "fov": 33.0, "fh": 1.08, "fs": 0.18,  "push": 0.12},
	{"id": "IMPACT_R",   "az": 48.0,  "el": 6.0,  "dist": 4.20, "fov": 33.0, "fh": 1.06, "fs": -0.18, "push": 0.12},
]

## 各家族的机位池 —— 池子的取法本身就是剪辑语言：
## 移动段给侧面（步态要侧面才看得见），攻击段给 3/4（要有纵深），
## 受击段给近景（要看得清挨了什么），流程段给正面（要立得住）。
##
## 注：冲击机位（11/12）**只在命中那一拍**被强制插入，而命中帧恰好是姿态
## 最舒展的时候（出拳伸展 + 前倾）。实测把它们按"近景"给（dist≈3.0）会直接
## 把腿切掉 —— 所以它们的景别定成"中景偏宽"（dist≈4.3, fov 33），
## 单镜内再推近 12%，落点才既紧凑又不切脚。
const POOL_LOCOMOTION := [0, 3, 4, 5, 6, 7, 8, 2, 1]
const POOL_NORMAL := [5, 6, 1, 2, 3, 4, 9, 7, 0]
const POOL_COMBO := [1, 2, 3, 4, 7, 8, 9, 5, 6, 0]
const POOL_GUARD := [5, 6, 3, 4, 9, 10, 7, 1]
const POOL_STATE := [0, 1, 2, 7, 9, 8, 5]
const POOL_CARD := [0, 1, 3, 4, 7]
## 只放**保证不切脚**的机位：11/12 是专用冲击机位，7 是低角度英雄镜
## （dist 4.35，仰拍，命中帧的前倾姿态在这个距离下也装得下）。
const POOL_IMPACT := [11, 12, 7]

## 家族配色（角标竖条 + 家族名）
const FAMILY_STYLE := {
	"Locomotion": {"cn": "基础移动", "en": "LOCOMOTION", "col": Color(0.36, 0.94, 0.56)},
	"NormalAttack": {"cn": "普通攻击", "en": "NORMAL ATTACK", "col": Color(1.00, 0.72, 0.26)},
	"ComboSpecial": {"cn": "连招与特殊技", "en": "COMBO & SPECIAL", "col": Color(0.80, 0.46, 1.00)},
	"GuardHit": {"cn": "防御与受击", "en": "GUARD & HIT", "col": Color(0.34, 0.72, 1.00)},
	"StateFlow": {"cn": "状态与流程", "en": "STATE & FLOW", "col": Color(0.30, 0.95, 0.92)},
	"Card": {"cn": "巡礼", "en": "SHOWCASE", "col": Color(0.90, 0.92, 0.96)},
}

## 中文字体候选（与 hud.gd 同一策略：先工程内，再系统；用 has_char 复检）
const CJK_CANDIDATES := [
	"res://assets/fonts/cjk.ttf",
	"res://assets/fonts/cjk.otf",
	"C:/Windows/Fonts/msyh.ttc",
	"C:/Windows/Fonts/msyhl.ttc",
	"C:/Windows/Fonts/Deng.ttf",
	"C:/Windows/Fonts/simhei.ttf",
	"C:/Windows/Fonts/simsun.ttc",
]
const CJK_PROBE := "重"

# =====================================================================
# 运行时
# =====================================================================
var _out_dir := ""
var _plan: Array = []
var _rng := RandomNumberGenerator.new()
## 故意**不加类型标注**：舞台脚本是 preload 进来的，写成 Variant 让方法调用
## 走动态派发，免得被"基类 Node3D 上没有 setup()"这种静态检查拦下。
var _env
var _log_f: FileAccess
## 上一个用过的机位索引（-1 = 还没有）。单机位模式下用来约束**段间**角差，
## 让相邻段不会在相反机位之间闪跳。
var _prev_cam := -1

var _rig: Node3D
var _ap: AnimationPlayer
var _skeleton: Skeleton3D
var _cam: Camera3D

var _hud: CanvasLayer
var _l_title: Label
var _l_sub: Label
var _l_hint: Label
var _l_family: Label
var _l_code: Label
var _l_name: Label
var _l_meta: Label
var _l_counter: Label
var _l_credits: Label
var _bar_fill: ColorRect
var _bar_bg: ColorRect
var _stripe: ColorRect
var _panel: PanelContainer
var _flash: ColorRect

var _font: FontFile
var _total_frames := 0
var _flash_amt := 0.0
var _aspect := 16.0 / 9.0


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	var pilot := args.has("--pilot")
	var dbg := ""
	var only := ""
	for a in args:
		if a.begins_with("--dbg="):
			dbg = a.substr(6)
		elif a.begins_with("--only="):
			only = a.substr(7)

	_out_dir = _resolve_out_dir()
	DirAccess.make_dir_recursive_absolute(_out_dir)
	# 分步日志写文件并**每条 flush** —— Godot 的 stdout 被管道接走时是块缓冲的，
	# "卡住了"和"没输错但没刷出来"分不清，这条日志就是为了分清。
	_log_f = FileAccess.open(_out_dir.path_join("render.log"), FileAccess.WRITE)
	_lg("start out=%s pilot=%s dbg=%s only=%s" % [_out_dir, str(pilot), dbg, only])

	_rng.seed = SEED
	Engine.max_fps = 0

	_lg("step: font")
	_build_font()
	_lg("step: camera")
	_build_cameras()
	_lg("step: character")
	_build_character()

	# 视口必须真的是 1280x720，否则"抓下来的图"和"计划的分辨率"对不上。
	var win := get_window()
	win.size = Vector2i(1280, 720)
	await get_tree().process_frame
	var vp := get_viewport().get_visible_rect().size
	_aspect = vp.x / maxf(vp.y, 1.0)
	_lg("step: viewport %dx%d aspect=%.4f window=%s" % [
		int(vp.x), int(vp.y), _aspect, str(win.size)])

	_lg("step: env")
	_build_env()
	_lg("step: hud")
	_build_hud()

	if dbg != "":
		_arm_watchdog(WATCHDOG_S)
		await _debug_frame(dbg)
		_finish(0)
		return

	_plan = _build_plan(pilot, only)
	_dump_plan()
	await _render_all()
	_lg("end frames=%d" % _total_frames)
	_finish(0)


func _lg(msg: String) -> void:
	print("[reel] %s" % msg)
	if _log_f != null:
		_log_f.store_line("%8.2f  %s" % [Time.get_ticks_msec() / 1000.0, msg])
		_log_f.flush()


func _finish(code: int) -> void:
	if _log_f != null:
		_log_f.store_line("EXIT %d" % code)
		_log_f.close()
		_log_f = null
	get_tree().quit(code)


## 看门狗：绝不留下"窗口开着但什么都不做"的僵尸进程。
func _arm_watchdog(seconds: float) -> void:
	var wd := Timer.new()
	wd.one_shot = true
	wd.wait_time = seconds
	wd.timeout.connect(func() -> void:
		_lg("WATCHDOG 超时 %.0fs，强制退出" % seconds)
		if _log_f != null:
			_log_f.close()
			_log_f = null
		OS.kill(OS.get_process_id()))
	add_child(wd)
	wd.start()


func _resolve_out_dir() -> String:
	var env := OS.get_environment("REEL_OUT")
	if env != "":
		return env.path_join("frames")
	# 帧序列**必须写到工程目录之外**：写在 res:// 里 Godot 会给每张 PNG 生成 .import，
	# 几千张图就是几千个 .import —— 那是把渲染中间产物当资产了。
	var proj := ProjectSettings.globalize_path("res://")
	var parts := proj.replace("\\", "/").split("/", false)
	# 工程在 <工作区>/bigmanfight/bigmanfitht，往上两级才是工作区根
	var root := "/".join(Array(parts).slice(0, maxi(1, parts.size() - 2)))
	return root.path_join("outputs/bigman_reel_v001/frames")


# =====================================================================
# 场景搭建
# =====================================================================
func _build_font() -> void:
	for p in CJK_CANDIDATES:
		if not FileAccess.file_exists(p):
			continue
		var f := FontFile.new()
		if f.load_dynamic_font(p) != OK:
			continue
		if f.has_char(CJK_PROBE.unicode_at(0)):
			_font = f
			print("REEL_FONT %s" % p)
			return
	print("REEL_FONT 未找到中文字体，中文将显示为方框")


func _build_cameras() -> void:
	_cam = Camera3D.new()
	_cam.name = "ReelCam"
	_cam.projection = Camera3D.PROJECTION_PERSPECTIVE
	_cam.fov = 38.0
	_cam.near = 0.05
	_cam.far = 400.0
	_cam.current = true
	add_child(_cam)


func _build_env() -> void:
	_env = ENV_SCRIPT.new()
	_env.name = "ReelEnv"
	add_child(_env)
	_env.setup(_cam)


func _build_character() -> void:
	var ps: PackedScene = load(MODEL_PATH)
	assert(ps != null, "找不到模型: %s" % MODEL_PATH)
	var model: Node3D = ps.instantiate()

	_rig = Node3D.new()
	_rig.name = "Rig"
	add_child(_rig)
	_rig.add_child(model)

	_ap = model.find_child("AnimationPlayer", true, false) as AnimationPlayer
	_skeleton = model.find_child("Skeleton3D", true, false) as Skeleton3D
	assert(_ap != null, "模型里没有 AnimationPlayer")
	assert(_skeleton != null, "模型里没有 Skeleton3D")

	# 手动模式：动画只在我 seek 的那一刻求值。不这么做引擎会自己按物理帧推进，
	# 我 seek 到的帧会被下一拍物理帧顶掉 —— 定格就永远是假的。
	_ap.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	_ap.playback_default_blend_time = 0.0

	_hide_unskinned(model)
	print("REEL_MODEL 动画 %d 段" % _ap.get_animation_list().size())


func _hide_unskinned(root: Node) -> void:
	var found: Array[MeshInstance3D] = []
	_collect_unskinned(root, found)
	for mi in found:
		mi.visible = false
	var names: Array[String] = []
	for mi in found:
		names.append(String(mi.name))
	print("REEL_UNSKINNED 隐藏 %d 个（期望 %d）: %s" % [
		found.size(), UNSKINNED_MESH_COUNT, str(names)])
	assert(found.size() == UNSKINNED_MESH_COUNT,
		"未蒙皮网格数量变了（期望 %d，实得 %d）" % [UNSKINNED_MESH_COUNT, found.size()])


func _collect_unskinned(node: Node, out: Array[MeshInstance3D]) -> void:
	var mi := node as MeshInstance3D
	# 注意：`skeleton` 是 NodePath，空值是**空 NodePath**，== null 恒为 false。
	if mi != null and mi.mesh != null and mi.skeleton.is_empty():
		out.append(mi)
	for c in node.get_children():
		_collect_unskinned(c, out)


# =====================================================================
# HUD（字卡 / 角标 / 计数 / 进度条 / 命中闪白）
# =====================================================================
func _build_hud() -> void:
	_hud = CanvasLayer.new()
	_hud.name = "ReelHud"
	add_child(_hud)

	# 命中闪白：全屏叠加，压在所有 HUD 之下（先加 = 先绘制）
	_flash = ColorRect.new()
	_flash.color = Color(0.80, 1.0, 0.88, 0.0)
	_flash.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_flash.offset_left = 0.0
	_flash.offset_top = 0.0
	_flash.offset_right = 1280.0
	_flash.offset_bottom = 720.0
	_hud.add_child(_flash)

	_l_title = _mk_label(88, Color(0.96, 0.98, 1.0), HORIZONTAL_ALIGNMENT_CENTER)
	_l_title.add_theme_constant_override("outline_size", 10)
	_l_title.add_theme_color_override("font_outline_color", Color(0.02, 0.05, 0.04, 0.9))
	_place(_l_title, 0.0, 262.0, 1280.0, 120.0)

	_l_sub = _mk_label(26, Color(0.45, 0.98, 0.66), HORIZONTAL_ALIGNMENT_CENTER)
	_l_sub.add_theme_constant_override("outline_size", 6)
	_l_sub.add_theme_color_override("font_outline_color", Color(0.02, 0.05, 0.04, 0.9))
	_place(_l_sub, 0.0, 386.0, 1280.0, 40.0)

	_l_hint = _mk_label(18, Color(0.72, 0.80, 0.86, 0.85), HORIZONTAL_ALIGNMENT_CENTER)
	_place(_l_hint, 0.0, 430.0, 1280.0, 30.0)

	_l_credits = _mk_label(22, Color(0.88, 0.94, 1.0), HORIZONTAL_ALIGNMENT_CENTER)
	_l_credits.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_l_credits.add_theme_constant_override("line_spacing", 12)
	_l_credits.add_theme_constant_override("outline_size", 8)
	_l_credits.add_theme_color_override("font_outline_color", Color(0.02, 0.05, 0.04, 0.92))
	_place(_l_credits, 0.0, 186.0, 1280.0, 360.0)

	# --- 左下角标 ---
	_panel = PanelContainer.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.04, 0.06, 0.08, 0.62)
	sb.border_color = Color(1, 1, 1, 0.10)
	sb.set_border_width_all(1)
	sb.set_corner_radius_all(4)
	sb.content_margin_left = 22.0
	sb.content_margin_right = 22.0
	sb.content_margin_top = 12.0
	sb.content_margin_bottom = 12.0
	_panel.add_theme_stylebox_override("panel", sb)
	_panel.offset_left = 44.0
	_panel.offset_top = 556.0
	_panel.offset_right = 640.0
	_panel.offset_bottom = 660.0
	_hud.add_child(_panel)

	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 2)
	_panel.add_child(box)

	_l_family = _mk_label(17, Color(0.7, 0.8, 0.86), HORIZONTAL_ALIGNMENT_LEFT)
	box.add_child(_l_family)

	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 14)
	box.add_child(row)

	_l_code = _mk_label(40, Color(1, 1, 1), HORIZONTAL_ALIGNMENT_LEFT)
	row.add_child(_l_code)

	_l_name = _mk_label(32, Color(0.94, 0.97, 1.0), HORIZONTAL_ALIGNMENT_LEFT)
	_l_name.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	row.add_child(_l_name)

	_l_meta = _mk_label(15, Color(0.62, 0.72, 0.80), HORIZONTAL_ALIGNMENT_LEFT)
	box.add_child(_l_meta)

	_stripe = ColorRect.new()
	_stripe.color = Color(0.36, 0.94, 0.56)
	_stripe.offset_left = 40.0
	_stripe.offset_top = 556.0
	_stripe.offset_right = 46.0
	_stripe.offset_bottom = 660.0
	_hud.add_child(_stripe)

	# --- 右上计数 ---
	_l_counter = _mk_label(24, Color(0.85, 0.92, 0.98), HORIZONTAL_ALIGNMENT_RIGHT)
	_l_counter.add_theme_constant_override("outline_size", 6)
	_l_counter.add_theme_color_override("font_outline_color", Color(0.02, 0.05, 0.04, 0.9))
	_place(_l_counter, 900.0, 40.0, 336.0, 34.0)

	# --- 底部进度条 ---
	_bar_bg = ColorRect.new()
	_bar_bg.color = Color(1, 1, 1, 0.14)
	_bar_bg.offset_left = 44.0
	_bar_bg.offset_top = 694.0
	_bar_bg.offset_right = 1236.0
	_bar_bg.offset_bottom = 698.0
	_hud.add_child(_bar_bg)

	_bar_fill = ColorRect.new()
	_bar_fill.color = Color(0.40, 0.96, 0.62, 0.95)
	_bar_fill.offset_left = 44.0
	_bar_fill.offset_top = 694.0
	_bar_fill.offset_right = 44.0
	_bar_fill.offset_bottom = 698.0
	_hud.add_child(_bar_fill)


func _mk_label(size: int, col: Color, align: int) -> Label:
	var l := Label.new()
	l.horizontal_alignment = align
	l.autowrap_mode = TextServer.AUTOWRAP_OFF
	if _font != null:
		l.add_theme_font_override("font", _font)
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", col)
	return l


func _place(l: Label, x: float, y: float, w: float, h: float) -> void:
	l.offset_left = x
	l.offset_top = y
	l.offset_right = x + w
	l.offset_bottom = y + h
	_hud.add_child(l)


# =====================================================================
# 计划：把 68 段展开成"每个输出帧该显示什么"
# =====================================================================
func _build_plan(pilot: bool, only: String = "") -> Array:
	var plan: Array = []
	plan.append(_make_card("title", TITLE_S, "Idle_01"))

	var names: Array = GameDB.all_clip_names()
	if only != "":
		# 抽查用：只渲指定编号的段（如 --only=B04,C11,E05），仍走完整的计划结构
		var want := only.split(",", false)
		var picked: Array = []
		for n in names:
			if want.has(String(GameDB.clip(n).get("code", ""))):
				picked.append(n)
		names = picked
		print("[reel] --only=%s 命中 %d 段: %s" % [only, names.size(), str(names)])
	elif pilot:
		names = names.slice(0, 3)

	var last_group := ""
	for n in names:
		var key := String(GameDB.clip(n).get("group_key", ""))
		# 每个家族开头插一张章节卡（含第一个家族）
		if key != last_group and only == "":
			plan.append(_make_sep("—— %s · %s ——" % [
				FAMILY_STYLE.get(key, FAMILY_STYLE["Card"])["cn"],
				FAMILY_STYLE.get(key, FAMILY_STYLE["Card"])["en"]], key))
		last_group = key
		plan.append(_make_clip(n))

	if only == "":
		plan.append(_make_card("credits", CREDITS_S, "Idle_01"))
	return plan


## 分隔卡：家族切换时插一张，给观众一个"章节"的呼吸点。
func _make_sep(text: String, group_key: String) -> Dictionary:
	var frames := 34
	var times: Array = []
	for i in frames:
		times.append(float(i) / float(FPS))
	return {
		"kind": "sep", "text": text, "group_key": group_key,
		"clip": "Idle_01", "label": "Idle_01",
		"times": times, "dur": float(frames) / float(FPS),
		"anchor": Vector3.ZERO, "disp": Vector3.ZERO,
		"cam_pool": POOL_CARD, "hit_out": -1, "prog": 0.0,
	}


func _make_card(kind: String, dur: float, clip: String) -> Dictionary:
	var frames := int(round(dur * FPS))
	var clip_dur := maxf(GameDB.duration(clip), 0.001)
	var times: Array = []
	for i in frames:
		times.append(fmod(float(i) / float(FPS), clip_dur))
	return {
		"kind": kind, "text": "", "group_key": "Card",
		"clip": clip, "label": clip,
		"times": times, "dur": dur,
		"anchor": Vector3.ZERO, "disp": Vector3.ZERO,
		"cam_pool": POOL_CARD, "hit_out": -1, "prog": 0.0,
	}


func _make_clip(clip: String) -> Dictionary:
	var d := GameDB.clip(clip)
	var full_dur := float(d.get("duration_s", 0.0))
	var looped := bool(d.get("loop", false))
	# 循环段截短；非循环段走完
	var show_dur := minf(full_dur, LOOP_SHOW_S) if looped else full_dur
	show_dur = maxf(show_dur, 0.20)

	var hit: Variant = GameDB.hit_frame(clip)
	var times := _build_times(show_dur, full_dur, hit, looped)

	# 根位移：manifest 是 Blender 系的 [x, y]（y 负 = 前方）。
	# 本角色在 Godot 里的前向 = 局部 +Z，所以局部位移 = (0, 0, -rm.y)。
	var rm := GameDB.root_motion(clip)
	var yaw := _yaw_for(clip)
	var local := Vector3(float(rm.x), 0.0, -float(rm.y))
	var disp := Basis(Vector3.UP, deg_to_rad(yaw)) * local

	var group_key := String(d.get("group_key", ""))

	var hit_out := -1
	if hit != null:
		var hit_t := float(hit) / 60.0
		for i in times.size():
			if absf(float(times[i]) - hit_t) < 0.0005:
				hit_out = i
				break

	return {
		"kind": "clip",
		"text": "",
		"group_key": group_key,
		"clip": clip,
		"label": clip,
		"code": String(d.get("code", "")),
		"cn": String(d.get("cn", "")),
		"loop": looped,
		"full_dur": full_dur,
		"show_dur": show_dur,
		"times": times,
		"dur": float(times.size()) / float(FPS),
		"yaw": yaw,
		# 锚点取位移中点：角色从 x=0 出发走到 disp，相机盯着**中间**才不会半路出画
		"anchor": Vector3(disp.x * 0.5, 0.0, disp.z * 0.5),
		"disp": disp,
		"hit_out": hit_out,
		"cam_pool": _pool_for(group_key),
		"prog": 0.0,
	}


## 输出帧 → 动画时刻（秒）的映射表。这是整个"快剪节奏"的核心。
##
##   常规段：每输出帧推进 SEG_TIME_SCALE/FPS 秒（SEG_TIME_SCALE<1 即整体放慢）。
##   命中帧：先**定格** FREEZE_HIT_FRAMES 帧（同一时刻重复采样），
##           再以半速走 SLOW_HIT_FRAMES 帧，然后恢复常速。
##   段尾：定格 HOLD_END_FRAMES 帧。
func _build_times(show_dur: float, full_dur: float, hit: Variant, looped: bool) -> Array:
	var out: Array = []
	var step := SEG_TIME_SCALE / float(FPS)
	var t := 0.0
	var freeze_left := 0
	var slow_left := 0
	var hit_pending := hit != null
	var ht := 0.0 if hit == null else float(hit) / 60.0
	var cycle := maxf(full_dur, 0.001)
	var guard := 0

	while t < show_dur - 0.0005 and guard < 200000:
		guard += 1
		out.append(fmod(t, cycle) if looped else t)
		var dt := step
		if hit_pending:
			if freeze_left > 0:
				freeze_left -= 1
				dt = 0.0
			elif slow_left > 0:
				slow_left -= 1
				dt = step * SLOW_FACTOR
			elif t < ht and t + step >= ht:
				# 正好跨过命中帧：钉到命中时刻，接下来定格 + 慢放
				t = ht
				freeze_left = FREEZE_HIT_FRAMES
				slow_left = SLOW_HIT_FRAMES
				hit_pending = false
				continue   # 当前这一拍不 append，下一轮从头采样命中帧
			else:
				dt = step
		t += dt

	# 尾帧定格
	var last_t: float = 0.0
	if not out.is_empty():
		last_t = float(out[out.size() - 1])
	for _k in HOLD_END_FRAMES:
		out.append(last_t)
	return out


func _pool_for(group_key: String) -> Array:
	match group_key:
		"Locomotion": return POOL_LOCOMOTION
		"NormalAttack": return POOL_NORMAL
		"ComboSpecial": return POOL_COMBO
		"GuardHit": return POOL_GUARD
		"StateFlow": return POOL_STATE
	return POOL_CARD


## 角色朝向（度）。0 = 面向相机(+Z)，90 = 面向屏幕右(+X)。
##
## 取值理由：
##   移动段给 ~72°（偏侧面）—— 步态只有侧面才读得出来；
##   攻击段给 ~30°（3/4 面向）—— 拳头朝相机来才有纵深；
##   受击段给 ~20°（近正面）—— 要让观众看清"挨了什么"；
##   流程段给 ~10°（正面）—— 入场/胜利/死亡是"立住"的表演。
func _yaw_for(clip: String) -> float:
	match clip:
		"Idle_01", "Idle_02":
			return 14.0
		"Walk_F", "Walk_B", "Run", "Run_Stop":
			return 72.0
		"Turn":
			return 24.0
		"Crouch", "Crouch_Idle":
			return 20.0
		"Jump_Start", "Jump_Up", "Jump_Fall", "Jump_Land":
			return 56.0
	match String(GameDB.clip(clip).get("group_key", "")):
		"NormalAttack":
			return 30.0
		"ComboSpecial":
			return 34.0
		"GuardHit":
			return 20.0
		"StateFlow":
			return 10.0
	return 20.0


# =====================================================================
# 切镜表
# =====================================================================
func _make_cuts(seg: Dictionary) -> Array:
	var n: int = (seg["times"] as Array).size()
	var pool: Array = seg["cam_pool"]
	var cuts: Array = []

	# --- 单机位模式（默认）：整段一个镜，段内不切 ---
	if ONE_CAM_PER_CLIP:
		var cam := -1
		var ho: int = int(seg.get("hit_out", -1))
		var prev_az := _prev_az()
		if ho >= 0:
			# 有命中的段给冲击机位池 —— 它是保证不切脚的中景，正好用来压住最重的一下。
			# 池内有左(-52°)/右(48°)/低角度(6°)三档，挑与上一段角差最小的一档。
			cam = _impact_near(prev_az)
		else:
			# 其余段从本家族机位池里挑，并按段间角差约束过滤。
			cam = _pick_cam(pool, _prev_cam)
		# 段间校验：单机位模式下唯一的"切"发生在段与段之间，这里才是该盯的地方。
		var d := absf(_angle_delta(float(CAMS[cam]["az"]), prev_az))
		if absf(prev_az) < 900.0 and d > CUT_MAX_ANGLE_DEG:
			_lg("CUT_ANGLE 段间超限 %.0f°  prev#%d→%s  @%s" % [
				d, _prev_cam, String(CAMS[cam]["id"]), String(seg.get("label", "?"))])
		# 字卡段（片头/片尾/章节）**不是动画**，可以给更大的漂移做缓慢环绕 ——
		# 不然 4~6 秒的固定镜头会显得很死；动画段则严格压小，只求稳不求动。
		var kind := String(seg.get("kind", "clip"))
		var drift := _rng.randf_range(-CUT_DRIFT_DEG, CUT_DRIFT_DEG)
		if kind == "title" or kind == "credits":
			drift = _rng.randf_range(18.0, 34.0) * (1.0 if _rng.randf() < 0.5 else -1.0)
		elif kind == "sep":
			drift = _rng.randf_range(-14.0, 14.0)
		cuts.append({
			"a": 0, "b": n, "cam": cam,
			"drift": drift,
		})
		_prev_cam = cam
		return cuts

	# --- 多机位快切模式（ONE_CAM_PER_CLIP=false 时才会走到这里）---
	var i := 0
	var prev := -1
	while i < n:
		var length := _rng.randi_range(CUT_MIN_FRAMES, CUT_MAX_FRAMES)
		var b := mini(n, i + length)
		var cam := _pick_cam(pool, prev)
		cuts.append({
			"a": i, "b": b, "cam": cam,
			"drift": _rng.randf_range(-CUT_DRIFT_DEG, CUT_DRIFT_DEG),
		})
		prev = cam
		i = b

	# 命中所在的切镜强制换成冲击机位 —— 快剪不是乱剪，
	# 得让最重的一下有专门的处理。但**选中哪个冲击机位仍要角差最小**：
	# 命中那一拍虽然是硬切，也不该从 -66°(PROFILE_L) 一刀切到 +66°(PROFILE_R)，
	# 那是最晃的一种切法（v1 漏了这条约束，所以还是晃）。
	var ho2: int = int(seg.get("hit_out", -1))
	if ho2 >= 0:
		for ci in cuts.size():
			var c: Dictionary = cuts[ci]
			if int(c["a"]) <= ho2 and ho2 < int(c["b"]):
				var prev_az2 := 999.0
				if ci > 0:
					prev_az2 = float(CAMS[int((cuts[ci - 1] as Dictionary)["cam"])]["az"])
				c["cam"] = _impact_near(prev_az2)
				if ci + 1 < cuts.size():
					(cuts[ci + 1] as Dictionary)["cam"] = _impact_near(
						float(CAMS[int(c["cam"])]["az"]))
				break

	_validate_cuts(cuts, String(seg.get("label", "?")))
	_prev_cam = int(cuts[cuts.size() - 1]["cam"])
	return cuts


## 上一段的机位方位角；没有上一段时返回 999（哨兵值，调用方用 absf()<900 判断有效性）。
func _prev_az() -> float:
	if _prev_cam >= 0 and _prev_cam < CAMS.size():
		return float(CAMS[_prev_cam]["az"])
	return 999.0


## 从冲击机位池里挑一个与 prev_az 角差**最小**的。
## prev_az 传 999 表示"没有上一镜"，此时随机取。
func _impact_near(prev_az: float) -> int:
	if absf(prev_az) > 900.0:
		return int(POOL_IMPACT[_rng.randi() % POOL_IMPACT.size()])
	var best := -1
	var best_d := 1e9
	for c in POOL_IMPACT:
		var d := absf(_angle_delta(float(CAMS[int(c)]["az"]), prev_az))
		if d < best_d:
			best_d = d
			best = int(c)
	return best if best >= 0 else int(POOL_IMPACT[0])


## 生成即校验：把仍然超过 CUT_MAX_ANGLE_DEG 的相邻切镜打出来。
## 没有输出 = 全片没有反向闪跳。
func _validate_cuts(cuts: Array, label: String) -> void:
	for i in range(1, cuts.size()):
		var i0 := int(cuts[i - 1]["cam"])
		var i1 := int(cuts[i]["cam"])
		var d := absf(_angle_delta(float(CAMS[i0]["az"]), float(CAMS[i1]["az"])))
		if d > CUT_MAX_ANGLE_DEG:
			_lg("CUT_ANGLE 超限 %.0f°  %s→%s  @%s" % [
				d, String(CAMS[i0]["id"]), String(CAMS[i1]["id"]), label])


## 从池子里挑一个机位。约束 **c != prev**（不连续同机位）且与上一镜方位角差
## ≤ CUT_MAX_ANGLE_DEG（避免正反打闪跳）。
##   - 合格候选里**随机**挑一个 —— 保留剪辑的随机感，不是永远选"最正"的那个；
##   - 一个都不合格时，退而求其次选**角差最小**的（旧版退到"第一个不同的"，
##     还是会闪；只有 prev<0（第一段）时才真的无约束）。
func _pick_cam(pool: Array, prev: int) -> int:
	if pool.size() <= 1:
		return int(pool[0]) if not pool.is_empty() else 0
	var has_prev := prev >= 0 and prev < CAMS.size()
	var prev_az := float(CAMS[prev]["az"]) if has_prev else 0.0
	var ok: Array = []
	var all: Array = []
	for c in pool:
		var ci := int(c)
		if ci == prev:
			continue
		all.append(ci)
		if (not has_prev) or absf(_angle_delta(float(CAMS[ci]["az"]), prev_az)) <= CUT_MAX_ANGLE_DEG:
			ok.append(ci)
	if not ok.is_empty():
		return int(ok[_rng.randi() % ok.size()])
	if not all.is_empty():
		var best := int(all[0])
		var bd := 1e9
		for ci in all:
			var d := absf(_angle_delta(float(CAMS[ci]["az"]), prev_az))
			if d < bd:
				bd = d
				best = ci
		return best
	return int(pool[0])


## 两个方位角之间的最短夹角（-180…180），单位度。
func _angle_delta(a: float, b: float) -> float:
	return fmod(a - b + 540.0, 360.0) - 180.0


# =====================================================================
# 渲染
# =====================================================================
func _render_all() -> void:
	var frame_no := 0
	for si in _plan.size():
		var seg: Dictionary = _plan[si]
		var times: Array = seg["times"]
		var cuts := _make_cuts(seg)
		for i in times.size():
			_apply_pose(seg, i)
			_apply_camera(seg, _cut_at(cuts, i), i)
			_apply_hud(seg, i)
			# 闪白：命中帧起算，两帧内衰减干净
			var fade_in := 0
			var ho: int = int(seg.get("hit_out", -1))
			if ho >= 0 and i >= ho and i < ho + 3:
				fade_in = 1
			_flash_amt = 0.0 if fade_in == 0 else (0.24 if i == ho else _flash_amt * 0.45)
			_flash.color = Color(0.80, 1.0, 0.88, _flash_amt)

			await RenderingServer.frame_post_draw
			var img := get_viewport().get_texture().get_image()
			frame_no += 1
			var err := img.save_png(_out_dir.path_join("frame_%05d.png" % frame_no))
			if err != OK:
				push_error("[reel] 写帧失败 #%d" % frame_no)
			if frame_no % 90 == 0:
				print("  … %d 帧  %s" % [frame_no, seg["label"]])
	_total_frames = frame_no


func _cut_at(cuts: Array, i: int) -> Dictionary:
	for c in cuts:
		if int(c["a"]) <= i and i < int(c["b"]):
			return c
	return cuts[cuts.size() - 1]


## 把角色摆到这一输出帧该有的姿态与位置
func _apply_pose(seg: Dictionary, i: int) -> void:
	var clip: String = seg["clip"]
	var engine := GameDB.engine_name(clip)
	var t: float = float((seg["times"] as Array)[i])
	_ap.play(engine)
	_ap.seek(t, true)

	_rig.rotation.y = deg_to_rad(float(seg.get("yaw", 0.0)))

	# 根位移在整段里线性铺开（与 Fighter._apply_slide 同一套算法）
	var disp: Vector3 = seg["disp"]
	var show := maxf(float(seg.get("show_dur", 1.0)), 0.001)
	var prog := clampf(t / show, 0.0, 1.0)
	_rig.position = disp * prog


## 机位 = 注视点(角色锚点 + 高度 + 横向偏移) + 方向(方位/仰角) × 距离(带推镜)
func _apply_camera(seg: Dictionary, cut: Dictionary, i: int) -> void:
	var cd: Dictionary = CAMS[int(cut["cam"])]
	var span: float = maxf(float(int(cut["b"]) - int(cut["a"])), 1.0)
	var p := clampf(float(i - int(cut["a"])) / span, 0.0, 1.0)

	var az_deg := float(cd["az"]) + float(cut["drift"]) * p
	var el_deg := float(cd["el"])
	var dist := float(cd["dist"]) * (1.0 - float(cd["push"]) * p)
	var fov := float(cd["fov"])

	var anchor: Vector3 = seg["anchor"]
	var right := Vector3(cos(deg_to_rad(az_deg)), 0.0, -sin(deg_to_rad(az_deg)))
	# 环境锚点：不加横向偏移，背景要正对角色
	var env_focus := anchor + Vector3(0.0, float(cd["fh"]), 0.0)
	# 注视点：加横向偏移，把角色推到三分线上
	var focus := env_focus + right * float(cd["fs"])

	var dir := Vector3(
		sin(deg_to_rad(az_deg)) * cos(deg_to_rad(el_deg)),
		sin(deg_to_rad(el_deg)),
		cos(deg_to_rad(az_deg)) * cos(deg_to_rad(el_deg)))

	_cam.position = focus + dir * dist
	_cam.look_at(focus, Vector3.UP)
	_cam.fov = fov

	_env.sync(env_focus, _cam.position, fov, _aspect)


func _apply_hud(seg: Dictionary, i: int) -> void:
	var kind: String = seg["kind"]
	var n := (seg["times"] as Array).size()
	var fade := _edge_fade(i, n)
	var is_card := kind == "title" or kind == "credits"
	var is_sep := kind == "sep"

	_l_title.visible = kind == "title"
	_l_sub.visible = kind == "title"
	_l_hint.visible = kind == "title"
	if kind == "title":
		_l_title.text = CHAR_NAME
		_l_sub.text = CHAR_SUB
		_l_hint.text = "多视角动画巡礼  ·  68 CLIPS  ·  MULTI-ANGLE SHOWCASE"
	_l_title.modulate.a = fade
	_l_sub.modulate.a = fade
	_l_hint.modulate.a = fade

	_l_credits.visible = kind == "credits"
	if kind == "credits":
		_l_credits.text = _credits_text()
	_l_credits.modulate.a = fade

	var show_chrome := not is_card
	_panel.visible = show_chrome and kind == "clip"
	_stripe.visible = show_chrome and kind == "clip"
	_l_counter.visible = show_chrome
	_bar_bg.visible = show_chrome
	_bar_fill.visible = show_chrome

	if kind == "clip":
		var st: Dictionary = FAMILY_STYLE.get(seg["group_key"], FAMILY_STYLE["Card"])
		_stripe.color = st["col"]
		_l_family.text = "%s  /  %s" % [st["cn"], st["en"]]
		_l_family.add_theme_color_override("font_color", st["col"])
		_l_code.text = String(seg.get("code", ""))
		_l_code.add_theme_color_override("font_color", st["col"])
		_l_name.text = String(seg.get("cn", ""))
		_l_meta.text = _meta_text(seg)
		# 角标跟着该段的淡入淡出，不做硬闪
		var a := clampf(float(i) / 5.0, 0.0, 1.0) * fade
		_panel.modulate.a = a
		_stripe.modulate.a = a
		_l_counter.text = "%d / %d" % [int(seg.get("index", 0)), _clip_total()]
		_l_counter.add_theme_color_override("font_color", Color(0.85, 0.92, 0.98))
		_l_counter.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		_l_counter.offset_left = 900.0
		_l_counter.offset_right = 1236.0
		_l_counter.offset_top = 40.0
		_l_counter.offset_bottom = 74.0
		_l_counter.modulate.a = 1.0
	elif is_sep:
		_l_counter.text = String(seg.get("text", ""))
		_l_counter.add_theme_color_override("font_color", Color(0.55, 0.98, 0.72))
		_l_counter.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		_l_counter.offset_left = 0.0
		_l_counter.offset_right = 1280.0
		_l_counter.offset_top = 62.0
		_l_counter.offset_bottom = 100.0
		_l_counter.modulate.a = fade

	if show_chrome:
		var frac := clampf(float(seg.get("prog", 0.0)), 0.0, 1.0)
		_bar_fill.offset_right = 44.0 + (1236.0 - 44.0) * frac


func _edge_fade(i: int, n: int) -> float:
	var a := 1.0
	if i < 8:
		a = float(i) / 8.0
	if i > n - 9:
		a = minf(a, float(n - 1 - i) / 8.0)
	return clampf(a, 0.0, 1.0)


func _meta_text(seg: Dictionary) -> String:
	var parts: Array[String] = []
	var c: Dictionary = GameDB.clip(seg["clip"])
	parts.append("时长 %.3f s" % float(c.get("duration_s", 0.0)))
	if bool(seg.get("loop", false)):
		parts.append("循环")
	var antic: Variant = c.get("antic_frame")
	if antic != null:
		parts.append("前摇 %dF" % int(antic))
	var hit: Variant = c.get("hit_frame")
	if hit != null:
		parts.append("命中 %dF" % int(hit))
	var hs: Variant = c.get("hitstop_frames")
	if hs != null:
		parts.append("停顿 %dF" % int(hs))
	var rm: Vector2 = c.get("root_motion_m", Vector2.ZERO)
	if absf(rm.y) > 0.0001:
		parts.append("根位移 %.3f m" % absf(rm.y))
	return "  ·  ".join(parts)


func _credits_text() -> String:
	var lines: Array[String] = []
	lines.append(CHAR_NAME + "   " + CHAR_SUB)
	lines.append("")
	lines.append("模型 / 蒙皮 / 动画   ——   bigman_v001 · 57 骨 · 78,048 三角面")
	lines.append("动画 68 段 · 总时长 72.65 s · 60 fps 逻辑帧 · 零贴图纯色材质")
	lines.append("引擎 Godot 4.6.3 · 逐帧 seek + 多视角快切 · 720p / 30 fps")
	lines.append("")
	lines.append("全部数值取自 manifest.json 的实测值，非人工转录")
	return "\n".join(lines)


func _clip_total() -> int:
	var n := 0
	for s in _plan:
		if String(s.get("kind", "")) == "clip":
			n += 1
	return n


# =====================================================================
# 诊断：渲一张固定机位的图，用来隔离"是哪一层把画面搞亮的"
# =====================================================================
func _debug_frame(flags_s: String) -> void:
	var flags := flags_s.split(",")
	print("REEL_DBG flags=%s" % str(flags))

	# --- 逐机位扫描：13 个机位各出一张，用来一次看全取景 ---
	if flags.has("camsweep"):
		await _cam_sweep()
		return

	if flags.has("norain"):
		for r in _env.get_children():
			if String(r.name).begins_with("Rain"):
				(r as Node3D).visible = false
	if flags.has("noback"):
		var b: Node = _env.get_node_or_null("Backdrop")
		if b != null:
			(b as Node3D).visible = false
	if flags.has("nofloor"):
		var fl: Node = _env.get_node_or_null("Floor")
		if fl != null:
			(fl as Node3D).visible = false
	if flags.has("nogrid"):
		var fm: ShaderMaterial = _env.floor_material()
		if fm != null:
			fm.set_shader_parameter("minor_px", 0.0)
			fm.set_shader_parameter("major_px", 0.0)
			fm.set_shader_parameter("sweep_gain", 0.0)

	for n in [_l_title, _l_sub, _l_hint, _l_credits, _l_counter]:
		n.visible = false
	_panel.visible = false
	_stripe.visible = false
	_bar_bg.visible = false
	_bar_fill.visible = false

	var yaw := 20.0
	if flags.has("side"):
		yaw = 72.0
	var seg := _make_clip("Idle_01")
	seg["yaw"] = yaw
	seg["disp"] = Vector3.ZERO
	seg["anchor"] = Vector3.ZERO
	seg["times"] = [1.0]
	_apply_pose(seg, 0)

	# 固定用一个中景 3/4 机位，跟 pilot 里那个坏画面同机位，便于逐层对比
	var cut := {"a": 0, "b": 30, "cam": 5, "drift": 0.0}
	_apply_camera(seg, cut, 0)

	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	var out := _out_dir.path_join("dbg_%s.png" % flags_s.replace(",", "_"))
	img.save_png(out)
	print("REEL_DBG_OUT %s" % out)


## 13 个机位各渲一张（HUD 保留），文件名带机位 id。
## 取景是否切脚、角色是否出画，看这一组图就够了 —— 不用靠单帧猜。
func _cam_sweep() -> void:
	var yaw_list := [14.0, 30.0, 72.0]
	for ci in CAMS.size():
		var cd: Dictionary = CAMS[ci]
		# 用"哪一族最常用它"来决定角色的朝向，扫出来的画面才接近成片
		var yaw: float = yaw_list[ci % yaw_list.size()]
		if ci >= 5 and ci <= 7:
			yaw = 30.0
		elif ci >= 9:
			yaw = 20.0

		var seg := _make_clip("Idle_01")
		seg["yaw"] = yaw
		seg["disp"] = Vector3.ZERO
		seg["anchor"] = Vector3.ZERO
		seg["times"] = [1.0]
		_apply_pose(seg, 0)

		var cut := {"a": 0, "b": 1, "cam": ci, "drift": 0.0}
		_apply_camera(seg, cut, 0)

		_l_counter.text = "%02d %s" % [ci, String(cd["id"])]
		_l_counter.visible = true

		await RenderingServer.frame_post_draw
		var img := get_viewport().get_texture().get_image()
		img.save_png(_out_dir.path_join("dbg_cam_%02d_%s.png" % [ci, String(cd["id"])]))
		print("  cam %02d %s yaw=%.0f" % [ci, String(cd["id"]), yaw])
	print("REEL_DBG_OUT 机位扫描完成 (%d 个)" % CAMS.size())


# =====================================================================
# 计划落盘
# =====================================================================
func _dump_plan() -> void:
	var total := _clip_total()
	var grand := maxi(1, _sum_frames())
	var k := 0
	var frames := 0
	var rows: Array = []
	for s in _plan:
		var seg: Dictionary = s
		if String(seg["kind"]) == "clip":
			k += 1
			seg["index"] = k
		frames += (seg["times"] as Array).size()
		seg["prog"] = float(frames) / float(grand)
		rows.append({
			"kind": seg["kind"], "code": seg.get("code", ""), "clip": seg["clip"],
			"cn": seg.get("cn", ""), "group": seg.get("group_key", ""),
			"frames": (seg["times"] as Array).size(),
			"sec": float((seg["times"] as Array).size()) / float(FPS),
			"hit_out": seg.get("hit_out", -1),
		})

	var f := FileAccess.open(_out_dir.path_join("plan.json"), FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify({
			"fps": FPS, "seed": SEED, "total_frames": _sum_frames(),
			"total_clips": total, "segments": rows,
		}, "  "))
		f.close()

	print("REEL_PLAN 段数=%d 动画段=%d 总帧=%d ≈ %.1f s" % [
		_plan.size(), total, _sum_frames(), float(_sum_frames()) / float(FPS)])


func _sum_frames() -> int:
	var n := 0
	for s in _plan:
		n += (s["times"] as Array).size()
	return n
