"""从门禁日志里挑出 C10_REPORT 并打印指定键（C10 支专用小工具）。"""
import json
import sys

log = sys.argv[1]
keys = sys.argv[2:]
text = open(log, encoding="utf-8", errors="replace").read()
tag = "C10_REPORT "
i = text.find(tag)
if i < 0:
    print("NO C10_REPORT in " + log)
    raise SystemExit(1)
j = text.find("\n", i)
if j < 0:
    j = len(text)
# Blender 退出时会把版本行紧贴在报告后面（同一行）⟹ 用 raw_decode 只取第一个值。
report, _end = json.JSONDecoder().raw_decode(text, i + len(tag))
json.dump(report, open(log.replace(".log", "_rep.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
if not keys:
    keys = list(report)
for key in keys:
    print("%s = %s" % (key, json.dumps(report.get(key), ensure_ascii=False)))
