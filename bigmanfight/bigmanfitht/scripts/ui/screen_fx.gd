class_name ScreenFx
extends CanvasLayer
## 屏幕后处理层：扫描线 + 暗角 + 噪点，以及"受击闪白 / 命中闪色"。
##
## 放在 3D 之上、HUD 之下（layer 顺序由 main.tscn 保证），所以：
##   - 扫描线会盖住战场，让整块画面像一块显示器；
##   - **不会**盖住血条和操作提示（那些要一直看得清）。
##
## 闪色为什么不用着色器：它就是一个纯色矩形改 alpha，着色器只会让事情更复杂。
## 着色器负责"一直存在的静态质感"，纯色矩形负责"短促的一次性反馈"。

const SHADER_PATH := "res://assets/shared/screen_fx.gdshader"

## 闪色衰减的指数。>1 表示前段压住、后段飞快收掉，
## 比线性更像真实的"曝光一下"；线性尾段会拖出一层擦不掉的薄色。
const FLASH_FALLOFF := 1.6

var _mat: ShaderMaterial
var _overlay: ColorRect
var _flash: ColorRect

var _peak := 0.0
var _left := 0.0
var _total := 0.0


func _ready() -> void:
	# 9 = 在 3D 之上、HUD 之下。HUD 自己用的是 10（见 hud.gd），
	# 所以扫描线和闪色都**不会**糊住血条与操作提示 —— 那些必须一直看得清。
	layer = 9

	var sh: Shader = load(SHADER_PATH)
	assert(sh != null, "找不到屏幕后处理着色器: %s" % SHADER_PATH)

	_mat = ShaderMaterial.new()
	_mat.shader = sh

	_overlay = ColorRect.new()
	_overlay.name = "Overlay"
	_overlay.material = _mat
	_overlay.color = Color(1.0, 1.0, 1.0, 1.0)
	_overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	_overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_overlay)

	_flash = ColorRect.new()
	_flash.name = "Flash"
	_flash.color = Color(1.0, 1.0, 1.0, 0.0)
	_flash.set_anchors_preset(Control.PRESET_FULL_RECT)
	_flash.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_flash)


## 闪一下屏幕。strength 0~1 是初始不透明度，duration 是完整衰减时间（秒）。
func flash(color: Color, strength: float = 0.5, duration: float = 0.18) -> void:
	_peak = clampf(strength, 0.0, 1.0)
	_total = maxf(duration, 0.001)
	_left = _total
	_flash.color = Color(color.r, color.g, color.b, _peak)


## 给测试/调试用：当前闪色不透明度。0 表示没有闪色在跑。
func flash_alpha() -> float:
	return _flash.color.a


func _process(delta: float) -> void:
	if _left <= 0.0:
		return
	_left = maxf(0.0, _left - delta)
	var t: float = _left / _total
	var a: float = 0.0 if _left <= 0.0 else _peak * pow(t, FLASH_FALLOFF)
	var c := _flash.color
	_flash.color = Color(c.r, c.g, c.b, a)


## 运行时调扫描线/暗角强度（自动化测试里用来把后处理关掉，拍干净的原图）。
func set_overlay_enabled(on: bool) -> void:
	if _overlay != null:
		_overlay.visible = on
