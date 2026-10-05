# -*- coding: utf-8 -*-
"""扫描 anim_ground_hit.py：找出「单行字符串被内层直引号提前闭合」的行。"""
import io
import re
import sys

PATH = sys.argv[1] if len(sys.argv) > 1 else "anim_ground_hit.py"
CJK = re.compile(r"[\u3000-\u303f\u4e00-\u9fff\u3400-\u4dbf\uff00-\uffef]")

src = io.open(PATH, encoding="utf-8").read().split("\n")
state = None  # 当前所处的三引号定界符
bad = []

for idx, line in enumerate(src, 1):
    i = 0
    n = len(line)
    while i < n:
        if state:
            j = line.find(state, i)
            if j < 0:
                break
            i = j + len(state)
            state = None
            continue
        c = line[i]
        if c == "#":
            break
        if line.startswith('"""', i):
            state = '"""'
            i += 3
            continue
        if line.startswith("'''", i):
            state = "'''"
            i += 3
            continue
        if c in ('"', "'"):
            q = c
            j = i + 1
            closed = False
            while j < n:
                if line[j] == "\\":
                    j += 2
                    continue
                if line[j] == q:
                    closed = True
                    break
                j += 1
            if not closed:
                break
            k = j + 1
            if k < n and CJK.match(line[k]):
                bad.append((idx, line))
                break
            i = k
            continue
        i += 1

print("BROKEN:", len(bad))
for idx, l in bad:
    print(idx, repr(l))
