"""_rv_e11_check.py —— 核对 E11 反向验证：每组旋钮必须让**指定判据**见红。

比 E10 的宽松判据（"failed ∪ non_ok 非空"）更严，因为本支的
`rvw_common_ground_contact_raw` 是**显式置空**的继承口径、恒为 False 且不以
`_ok` 结尾 ⟹ 宽松判据会永远通过、掩盖假绿。

用法（先跑 bash _rv_e11.sh）：
    python _rv_e11_check.py
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PAIRS = os.path.join(HERE, "_rv_e11_pairs.txt")

rows = []
with open(PAIRS, encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if line:
            rows.append(line.split("|"))

print("%-12s %-26s %-9s %s" % ("旋钮", "应以见红", "实测", "全部红项"))
print("-" * 96)
bad = []
for name, envs, gate in rows:
    path = os.path.join(HERE, "_e11_rv_%s.log" % name)
    if not os.path.exists(path):
        print("%-12s %-26s %-9s %s" % (name, gate, "缺日志", "-"))
        bad.append(name)
        continue
    txt = open(path, encoding="utf-8", errors="replace").read()
    if "E11_FAILURE" in txt:
        print("%-12s %-26s %-9s %s" % (name, gate, "崩溃",
                                       txt.split("E11_FAILURE")[1][:60]))
        bad.append(name)
        continue
    match = re.search(r"E11_REPORT (\{.*\})", txt, re.S)
    if not match:
        print("%-12s %-26s %-9s %s" % (name, gate, "无报告", "-"))
        bad.append(name)
        continue
    rep = json.loads(match.group(1))
    oks_red = sorted(k for k, v in rep.items()
                     if k.endswith("_ok") and v is False)
    hit = rep.get(gate) is False
    print("%-12s %-26s %-9s %s" % (name, gate, "✔ 红" if hit else "✘ 未红",
                                   ", ".join(oks_red) or "（无）"))
    if not hit:
        bad.append(name)

print("-" * 96)
if bad:
    print("E11_RV_FAIL 未生效旋钮 = %s" % bad)
    sys.exit(1)
print("E11_RV_ALL_OK 10/10 旋钮均让指定判据见红")
