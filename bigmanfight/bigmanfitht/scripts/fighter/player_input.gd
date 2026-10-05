class_name PlayerInput
extends RefCounted
## 把键盘映射成 InputFrame。边沿检测在这里做。

const ACTIONS := {
	"move_left": "left",
	"move_right": "right",
	"jump": "jump",
	"crouch": "crouch",
	"guard": "guard",
}

## 攻击键：名字 -> InputFrame 字段
const ATTACKS := {
	"atk_light": "light",
	"atk_heavy": "heavy",
	"atk_dash": "dash",
	"atk_upper": "upper",
	"atk_low": "low",
	"atk_special": "special",
	"atk_grab": "grab",
	"atk_skill1": "skill1",
	"atk_skill2": "skill2",
	"atk_smash": "smash",
	"atk_ultimate": "ultimate",
	"atk_charge": "charge",
	"atk_pick": "pick",
}

var _prev: Dictionary = {}


func poll() -> InputFrame:
	var f := InputFrame.new()

	for act in ACTIONS.keys():
		if InputMap.has_action(act):
			f.set(ACTIONS[act], Input.is_action_pressed(act))

	for act in ATTACKS.keys():
		if not InputMap.has_action(act):
			continue
		var now := Input.is_action_pressed(act)
		var was: bool = _prev.get(act, false)
		if now and not was:
			f.set(ATTACKS[act], true)
		_prev[act] = now

	return f
