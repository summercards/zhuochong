class_name InputFrame
extends RefCounted
## 一帧的输入快照。
##
## 玩家与 AI 都产出这个结构，战斗逻辑只认它 —— 所以换 AI / 录像回放 / 网络输入
## 都不用动状态机一行代码。

var left := false
var right := false
var jump := false
var crouch := false
var guard := false

## 攻击键是**边沿触发**：只在"本帧刚按下"时为 true。
var light := false
var heavy := false
var dash := false
var upper := false
var low := false
var special := false
## 抓技键。也是**边沿触发** —— 它的语义有两个：手上没人时"伸手去抓"，
## 手上有人时"把抓住的人投出去"。两种语义都要求"这一次按下"，
## 所以它必须和攻击键一样只在按下帧为真（按住不放不能连续投）。
var grab := false

## 技能键（C 族特殊技）。同样是边沿触发。
##
## **刻意不并进 `any_attack()`**：那套连段逻辑（`_resolve_chain` / 取消窗口）
## 是按"轻→轻→轻→重"设计的，把技能塞进去会让"取消"变成"强制接轻拳"
## （`_resolve_chain` 对认不出的键会兜底返回 Light_01）。
## 技能走独立的 `any_special_key()`，有自己的派发路径。
var skill1 := false      ## 肩撞
var skill2 := false      ## 抱摔（抓技型）
var smash := false       ## 地面砸击
var ultimate := false    ## 大招（三段连续）
var charge := false      ## 蓄力

## 拾取 / 投掷键。同样是**边沿触发** —— 它和抓技键是同一个语义家族：
## 手上空着时"把地上的东西捡起来"，手上已经拿着东西时"把它扔出去"。
## 两种语义都要求"这一次按下"，所以按住不放不会连续捡/连续扔。
##
## **刻意不并进 `any_attack()`**：它不是"出招"，把它算进攻击会让
## "捡东西"顺手把连段也点出去（`_resolve_chain` 会把认不出的键兜底成 Light_01）。
## 也不并进 `any_special_key()`（那不是 C 族技能）。
var pick := false


## 水平轴：-1 左 / +1 右 / 0 静止。
func axis() -> float:
	return (1.0 if right else 0.0) - (1.0 if left else 0.0)


## 拳脚攻击（**不含抓技、不含技能**）。
##
## 分开的理由：这两个的语义不同 —— 拳脚是"打出去"，抓技是"贴上去"。
## 混在一起会让"取消窗口内按下抓技"变成"接一段普通攻击"，
## 也会让被捕者的挣脱计数把普通攻击和抓技混为一谈。
func any_attack() -> bool:
	return light or heavy or dash or upper or low or special


## 技能键（C 族）有没有被按。
func any_special_key() -> bool:
	return skill1 or skill2 or smash or ultimate or charge


## 一切"主动出招"的按键（拳脚 + 技能 + 抓技）。
## 只在需要"玩家想干点什么"的场合用（例如挣脱计数）。
func any_action() -> bool:
	return any_attack() or any_special_key() or grab


func clear_edges() -> void:
	light = false
	heavy = false
	dash = false
	upper = false
	low = false
	special = false
	grab = false
	skill1 = false
	skill2 = false
	smash = false
	ultimate = false
	charge = false
	pick = false


func _to_string() -> String:
	var bits: Array[String] = []
	if left: bits.append("L")
	if right: bits.append("R")
	if jump: bits.append("J")
	if crouch: bits.append("C")
	if guard: bits.append("G")
	if light: bits.append("j")
	if heavy: bits.append("k")
	if dash: bits.append("l")
	if upper: bits.append("u")
	if low: bits.append("o")
	if special: bits.append("p")
	if grab: bits.append("T")
	if skill1: bits.append("1")
	if skill2: bits.append("2")
	if smash: bits.append("B")
	if ultimate: bits.append("Y")
	if charge: bits.append("C")
	if pick: bits.append("E")
	return "[%s]" % "".join(bits)
