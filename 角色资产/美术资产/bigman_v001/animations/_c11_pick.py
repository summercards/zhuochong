"""_c11_pick —— 从 Blender 日志里安全提取某个 tag 后面的 JSON。

Blender 退出时会把 "Blender quit" 之类的行**紧贴**在报告后面（同一行），
所以不能按 `\\n` 切 —— 用 `raw_decode` 让解码器自己决定 JSON 的终点（C10 教训）。
"""

import json
import sys


def pick(path, tag):
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        text = handle.read()
    out = []
    index = 0
    decoder = json.JSONDecoder()
    while True:
        index = text.find(tag, index)
        if index < 0:
            break
        start = index + len(tag)
        while start < len(text) and text[start] in " \t":
            start += 1
        try:
            payload, end = decoder.raw_decode(text, start)
        except ValueError:
            index = start
            continue
        out.append(payload)
        index = end
    return out


if __name__ == "__main__":
    path = sys.argv[1]
    tag = sys.argv[2]
    mode = sys.argv[3] if len(sys.argv) > 3 else "dump"
    for payload in pick(path, tag):
        if mode == "dump":
            print(json.dumps(payload, ensure_ascii=False, indent=1,
                             default=str))
        else:
            print(json.dumps(payload.get(mode), ensure_ascii=False, indent=1,
                             default=str))
