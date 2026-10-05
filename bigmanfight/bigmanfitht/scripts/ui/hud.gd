class_name Hud
extends CanvasLayer
## 战局 HUD：血条 / 状态 / 横幅 / 调试读数 / 操作图例。
##
## 两个刻意的决定：
##  1. **整块用代码搭，不放 .tscn。** 血条宽度、边距这些数字只能有一个出处；
##     写在场景文件里的像素值迟早和 game_db 的常量对不上。
##  2. **字体要实测过才敢用中文。** Godot 默认字体是 Open Sans SemiBold，
##     实测 `has_char("待") == false` —— 直接写中文会全是方框。所以这里先
##     去系统字体目录找一个中文黑体，找到就用中文，找不到整块退回英文。
##     （判定用 has_char 复检，不是"文件存在就当能用"。）

const BAR_W := 440.0
const BAR_H := 24.0
const MARGIN := 30.0
const TOP := 30.0
## 白色残影条的下落速度（1/秒）。残影 = 刚掉的血，给一眼能看出"刚挨了多少"。
const GHOST_FALL_RATE := 0.65
## 伤害数字停留时长（秒）
const DMG_HOLD := 0.7

## 中文字体候选：先看工程内，再看系统。找到能渲染中文的第一个就用。
const CJK_CANDIDATES := [
	"res://assets/fonts/cjk.ttf",
	"res://assets/fonts/cjk.otf",
	"C:/Windows/Fonts/msyh.ttc",
	"C:/Windows/Fonts/msyhl.ttc",
	"C:/Windows/Fonts/Deng.ttf",
	"C:/Windows/Fonts/simhei.ttf",
	"C:/Windows/Fonts/simsun.ttc",
]
const CJK_PROBE := "待"

const COL_BG := Color(0.07, 0.08, 0.11, 0.88)
const COL_EDGE := Color(1.0, 1.0, 1.0, 0.16)
const COL_P1 := Color(0.96, 0.71, 0.24)
const COL_P2 := Color(0.28, 0.71, 0.96)
const COL_LOW := Color(0.94, 0.31, 0.24)
const COL_GHOST := Color(0.95, 0.95, 0.95, 0.40)
const COL_TEXT := Color(0.90, 0.92, 0.96)
const COL_DIM := Color(0.62, 0.66, 0.74)

var _player: Fighter = null
var _dummy: Fighter = null

var _p_fill: ColorRect
var _p_ghost: ColorRect
var _d_fill: ColorRect
var _d_ghost: ColorRect
var _p_name: Label
var _d_name: Label
var _p_state: Label
var _d_state: Label
var _p_dmg: Label
var _d_dmg: Label
var _banner: Label
var _debug: Label
var _legend: Label

var _use_cjk := false
var _cjk_theme: Theme = null
var _p_ghost_v := 1.0
var _d_ghost_v := 1.0
var _p_dmg_t := 0.0
var _d_dmg_t := 0.0
var _banner_t := 0.0
var _debug_on := false


func _ready() -> void:
	_cjk_theme = _try_load_cjk_font()
	layer = 10
	_build()


# ---------------------------------------------------------------------
# 字体
# ---------------------------------------------------------------------
## 返回可用的中文字体 Theme；没有就返回 null。
## 注意：CanvasLayer **没有** theme 属性（只有 Control/Window 有），
## 所以字体挂在下面那个全屏 Control 上，靠继承生效。
func _try_load_cjk_font() -> Theme:
	for path in CJK_CANDIDATES:
		var ff: FontFile = null
		if path.begins_with("res://"):
			if not ResourceLoader.exists(path):
				continue
			ff = load(path) as FontFile
			if ff == null:
				continue
		else:
			ff = FontFile.new()
			if ff.load_dynamic_font(path) != OK:
				continue
		# 关键：不能"文件能读"就当真，必须实测能不能出中文字形
		if ff.has_char(CJK_PROBE.unicode_at(0)):
			var th := Theme.new()
			th.default_font = ff
			th.default_font_size = 16
			print("[Hud] 中文字体已装载: %s" % path)
			return th
	print("[Hud] 没找到可用中文字体 → HUD 退回英文（Godot 默认字体不含 CJK 字形）")
	return null


## 双语取词：有中文字体给中文，否则给英文。
func _t(zh: String, en: String) -> String:
	return zh if _use_cjk else en


# ---------------------------------------------------------------------
# 搭建
# ---------------------------------------------------------------------
func _build() -> void:
	var root := Control.new()
	root.name = "Root"
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	if _cjk_theme != null:
		root.theme = _cjk_theme
		_use_cjk = true
	add_child(root)

	# --- 1P（左，血条从右往左掉）---
	_p_name = _mk_label(root, Control.PRESET_TOP_LEFT, MARGIN, TOP, 0, 0)
	_p_name.text = _t("1P  玩家", "1P  PLAYER")
	_p_name.add_theme_color_override("font_color", COL_P1)

	_p_ghost = _mk_rect(root, Control.PRESET_TOP_LEFT, MARGIN, TOP + 26, BAR_W, BAR_H, COL_GHOST)
	_p_fill = _mk_rect(root, Control.PRESET_TOP_LEFT, MARGIN, TOP + 26, BAR_W, BAR_H, COL_P1)

	_p_state = _mk_label(root, Control.PRESET_TOP_LEFT, MARGIN, TOP + 26 + BAR_H + 5, 0, 0)
	_p_dmg = _mk_label(root, Control.PRESET_TOP_LEFT, MARGIN, TOP + 26 + BAR_H + 5, BAR_W, 0)
	_p_dmg.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	_p_dmg.add_theme_font_size_override("font_size", 22)
	_p_dmg.add_theme_color_override("font_color", COL_LOW)

	# --- 2P（右，血条从左往右掉）---
	_d_name = _mk_label(root, Control.PRESET_TOP_RIGHT, 0, TOP, 0, 0)
	_d_name.text = _t("2P  假人", "2P  DUMMY")
	_d_name.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	_d_name.add_theme_color_override("font_color", COL_P2)

	_d_ghost = _mk_rect(root, Control.PRESET_TOP_RIGHT, -MARGIN - BAR_W, TOP + 26, BAR_W, BAR_H, COL_GHOST)
	_d_fill = _mk_rect(root, Control.PRESET_TOP_RIGHT, -MARGIN - BAR_W, TOP + 26, BAR_W, BAR_H, COL_P2)

	_d_state = _mk_label(root, Control.PRESET_TOP_RIGHT, -MARGIN, TOP + 26 + BAR_H + 5, 0, 0)
	_d_state.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	_d_dmg = _mk_label(root, Control.PRESET_TOP_RIGHT, -MARGIN - BAR_W, TOP + 26 + BAR_H + 5, BAR_W, 0)
	_d_dmg.add_theme_font_size_override("font_size", 22)
	_d_dmg.add_theme_color_override("font_color", COL_LOW)

	# --- 条槽底与描边（放在填充之前画 → 这里用 z_index 压到下面）---
	for pair in [[_p_ghost, _p_fill], [_d_ghost, _d_fill]]:
		for r in pair:
			r.z_index = -1

	# --- 横幅 ---
	_banner = Label.new()
	_banner.name = "Banner"
	_banner.set_anchors_preset(Control.PRESET_TOP_WIDE)
	_banner.anchor_top = 0.28
	_banner.anchor_bottom = 0.28
	_banner.offset_bottom = 96.0
	_banner.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_banner.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_banner.add_theme_font_size_override("font_size", 62)
	_banner.add_theme_color_override("font_color", Color(1, 1, 1))
	_banner.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.85))
	_banner.add_theme_constant_override("outline_size", 10)
	_banner.visible = false
	root.add_child(_banner)

	# --- 图例（右下）---
	_legend = Label.new()
	_legend.name = "Legend"
	_legend.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)
	_legend.offset_left = -430.0
	_legend.offset_top = -160.0
	_legend.offset_right = -MARGIN
	_legend.offset_bottom = -MARGIN
	_legend.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	_legend.vertical_alignment = VERTICAL_ALIGNMENT_BOTTOM
	_legend.add_theme_font_size_override("font_size", 15)
	_legend.add_theme_color_override("font_color", COL_DIM)
	_legend.text = _legend_text()
	root.add_child(_legend)

	# --- 调试读数（左下）---
	_debug = Label.new()
	_debug.name = "Debug"
	_debug.set_anchors_preset(Control.PRESET_BOTTOM_LEFT)
	_debug.offset_left = MARGIN
	_debug.offset_top = -220.0
	_debug.offset_right = MARGIN + 560.0
	_debug.offset_bottom = -MARGIN
	_debug.vertical_alignment = VERTICAL_ALIGNMENT_BOTTOM
	_debug.add_theme_font_size_override("font_size", 15)
	_debug.add_theme_color_override("font_color", COL_TEXT)
	_debug.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.8))
	_debug.add_theme_constant_override("outline_size", 4)
	_debug.visible = false
	root.add_child(_debug)


func _mk_label(parent: Control, preset: int, x: float, y: float, w: float, h: float) -> Label:
	var l := Label.new()
	l.set_anchors_preset(preset)
	l.offset_left = x
	l.offset_top = y
	l.offset_right = x + maxf(w, 380.0)
	l.offset_bottom = y + maxf(h, 24.0)
	if preset == Control.PRESET_TOP_RIGHT:
		l.offset_left = x - maxf(w, 380.0)
		l.offset_right = x
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	parent.add_child(l)
	return l


func _mk_rect(parent: Control, preset: int, x: float, y: float, w: float, h: float, col: Color) -> ColorRect:
	var r := ColorRect.new()
	r.set_anchors_preset(preset)
	r.offset_left = x
	r.offset_top = y
	r.offset_right = x + w
	r.offset_bottom = y + h
	r.color = col
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	parent.add_child(r)
	return r


func _legend_text() -> String:
	if _use_cjk:
		return "\n".join([
			"A/← 后退    D/→ 前进    W/↑/空格 跳跃    S/↓ 下蹲",
			"J 轻拳(三连)   K 重拳   L 冲刺攻击",
			"U 上勾拳   O 下段攻击   P 技能(旋转重拳)",
			"G 抓取 / 再按一次投出去（被抓时连按可挣脱）",
			"E 捡起地上的东西 / 手上有东西时再按一次扔出去",
			"手上有东西时出拳=抡它砸（伤害更高，砸中会掉耐久，砸几下就碎）",
			"连按两次方向 = 起跑；跑动中按拳脚 = 跳起飞踢",
			"I / Shift 举防     R 重开     F1 调试读数     Esc 退出",
		])
	return "\n".join([
		"A/<-  BACK    D/->  FORWARD    W/UP/SPACE  JUMP    S/DOWN  CROUCH",
		"J  LIGHT (3-chain)   K  HEAVY   L  DASH ATTACK",
		"U  UPPERCUT   O  LOW ATTACK   P  SPECIAL (SPIN)",
		"G  GRAB / press again to THROW  (mash to break free when held)",
		"E  PICK UP what's on the ground / press again to THROW it",
		"With something in hand, punch = SWING it (more damage, it wears out)",
		"Double-tap a direction = RUN; press attack while running = JUMP KICK",
		"I / SHIFT  GUARD     R  RESTART     F1  DEBUG     ESC  QUIT",
	])


# ---------------------------------------------------------------------
# 对外
# ---------------------------------------------------------------------
func bind(player: Fighter, dummy: Fighter) -> void:
	_player = player
	_dummy = dummy
	_p_ghost_v = 1.0
	_d_ghost_v = 1.0


func say(zh: String, en: String, seconds := 1.4) -> void:
	_banner.text = _t(zh, en)
	_banner.visible = true
	_banner_t = seconds


func clear_banner() -> void:
	_banner_t = 0.0
	_banner.visible = false


func toggle_debug() -> void:
	_debug_on = not _debug_on
	_debug.visible = _debug_on


# ---------------------------------------------------------------------
# 每帧刷新
# ---------------------------------------------------------------------
func _process(delta: float) -> void:
	if _player == null or _dummy == null:
		return
	_refresh_bar(_p_fill, _p_ghost, _player, false, delta)
	_refresh_bar(_d_fill, _d_ghost, _dummy, true, delta)
	_refresh_labels(delta)
	if _debug_on:
		_debug.text = _debug_text()


func _refresh_bar(fill: ColorRect, ghost: ColorRect, f: Fighter, right_align: bool,
		delta: float) -> void:
	var ratio: float = f.hp_ratio()
	var is_p1: bool = not right_align
	# 残影：掉血时慢慢追下来；回血时立刻跳上去
	var gv: float = _p_ghost_v if is_p1 else _d_ghost_v
	if ratio > gv:
		gv = ratio
	else:
		gv = move_toward(gv, ratio, GHOST_FALL_RATE * delta)
	if is_p1:
		_p_ghost_v = gv
	else:
		_d_ghost_v = gv

	var col: Color = COL_P1 if is_p1 else COL_P2
	if ratio < 0.30:
		col = COL_LOW
	fill.color = col

	fill.offset_right = fill.offset_left + BAR_W * ratio
	ghost.offset_right = ghost.offset_left + BAR_W * gv
	if right_align:
		# 右对齐的条：右边缘钉死，往左缩
		fill.offset_left = -MARGIN - BAR_W * ratio
		fill.offset_right = -MARGIN
		ghost.offset_left = -MARGIN - BAR_W * gv
		ghost.offset_right = -MARGIN


func _refresh_labels(delta: float) -> void:
	_p_state.text = "%s   %s  %d/%d" % [
		_player.label() if _use_cjk else _player.label_en(),
		_player.clip_name(), _player.hp, _player.max_hp]
	_d_state.text = "%s   %s  %d/%d" % [
		_dummy.label() if _use_cjk else _dummy.label_en(),
		_dummy.clip_name(), _dummy.hp, _dummy.max_hp]

	_p_dmg_t = maxf(0.0, _p_dmg_t - delta)
	_d_dmg_t = maxf(0.0, _d_dmg_t - delta)
	_p_dmg.visible = _p_dmg_t > 0.0
	_d_dmg.visible = _d_dmg_t > 0.0
	if _p_dmg_t > 0.0:
		_p_dmg.modulate.a = clampf(_p_dmg_t / DMG_HOLD, 0.0, 1.0)
	if _d_dmg_t > 0.0:
		_d_dmg.modulate.a = clampf(_d_dmg_t / DMG_HOLD, 0.0, 1.0)

	if _banner_t > 0.0:
		_banner_t -= delta
		if _banner_t <= 0.0:
			_banner.visible = false


## 伤害数字：由 Game 在命中时调用（victim 决定显示在哪一侧）。
func show_damage(victim: Fighter, amount: int) -> void:
	var txt := "-%d" % amount
	if victim == _player:
		_p_dmg.text = txt
		_p_dmg_t = DMG_HOLD
	elif victim == _dummy:
		_d_dmg.text = txt
		_d_dmg_t = DMG_HOLD


func _debug_text() -> String:
	var dist: float = absf(_player.global_position.x - _dummy.global_position.x)
	var pframe: float = _player.current_frame()
	var dframe: float = _dummy.current_frame()
	var pn: String = _player.clip_name()
	var dn: String = _dummy.clip_name()
	var cam: Camera3D = get_viewport().get_camera_3d()
	var cam_size: float = 0.0
	if cam != null:
		cam_size = cam.size
	return "\n".join([
		"1P  %-12s clip=%-16s frame=%6.1f / %-6.1f  hp=%d  face=%+d  x=%+.3f" % [
			_t(_player.label(), _player.label_en()), pn, pframe, GameDB.frame_count(pn),
			_player.hp, _player.facing, _player.global_position.x],
		"2P  %-12s clip=%-16s frame=%6.1f / %-6.1f  hp=%d  face=%+d  x=%+.3f" % [
			_t(_dummy.label(), _dummy.label_en()), dn, dframe, GameDB.frame_count(dn),
			_dummy.hp, _dummy.facing, _dummy.global_position.x],
		"dist=%.3f m   engage=%.3f m   push=%.3f m   cam.size=%.2f" % [
			dist, GameDB.engage_distance, GameDB.PUSH_SEPARATION, cam_size],
		"walk=%.3f  run=%.3f m/s   dmg(light/heavy/dash)=%d/%d/%d   stage=±%.1f" % [
			GameDB.walk_speed, GameDB.run_speed,
			GameDB.damage("Light_01"), GameDB.damage("Heavy_01"), GameDB.damage("Dash_Attack"),
			GameDB.STAGE_HALF_WIDTH],
		"hurtbox r=%.2f h=%.3f/%.3f   clips=%d" % [
			GameDB.HURTBOX_RADIUS, GameDB.HURTBOX_HEIGHT, GameDB.HURTBOX_HEIGHT_CROUCH,
			GameDB.clips.size()],
	])
