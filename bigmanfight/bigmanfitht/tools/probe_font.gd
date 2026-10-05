extends SceneTree
## 检查默认主题字体是否有中文字形 —— 决定 HUD 用中文还是英文。

func _initialize() -> void:
	var f: Font = ThemeDB.fallback_font
	print("FALLBACK_FONT name=", f.get_font_name() if f != null else "<null>")
	if f == null:
		quit(1)
		return
	var probes := ["待", "攻", "击", "帧", "血", "A", "1"]
	for p in probes:
		print("  %s -> %s" % [p, str(f.has_char(p.unicode_at(0)))])
	print("FALLBACK_OK ", f.has_char("待".unicode_at(0)))
	quit(0)
