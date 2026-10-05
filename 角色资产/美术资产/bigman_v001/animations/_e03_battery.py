"""E03 反向验证批量驱动：逐个打开旋钮，要求**每一个都让门禁见红**。

用法（在 animations 目录下）：
    "C:/Users/zhuangmenghong/.workbuddy/binaries/python/versions/3.13.12/python.exe" _e03_battery.py

判据：每条旋钮跑完，`failed ∪ non_ok_bools` 必须**非空**。
若某条为空 ⟹ 该旋钮是**惰性**的（没真的接进代码 / 扰动不在判据可见的那一维），
必须回去改，不能登记为「已验证」。
"""
import io
import json
import os
import re
import subprocess

BLENDER = "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = ["--background", "--factory-startup", "--python", "anim_rage.py"]

KNOBS = [
    ("E03_TP_SEAM_ZERO", "① 首帧改零位"),
    ("E03_TP_CHESTFAR", "② ★★★ 拳离开胸"),
    ("E03_TP_CHESTCLIP", "③ 拳穿进胸"),
    ("E03_TP_HEADDOWN", "④a 仰头不够"),
    ("E03_TP_HEADOVER", "④b 仰头过头"),
    ("E03_TP_NOHITSTOP", "⑤ 去掉 hitstop"),
    ("E03_TP_FOOTSWAY", "⑥ 脚跟着动"),
    ("E03_TP_LOOPBREAK", "⑦ 末帧不闭合"),
    ("E03_TP_NOFLIP", "⑧ 躯干不翻转"),
    ("E03_TP_FACEALONG", "⑨ 拳面沿前臂"),
    ("E03_CHIRALITY_FLIP", "⑩ 手性翻转"),
]


def run(extra, tag):
    env = dict(os.environ)
    env["SKIP_RENDER"] = "1"
    env.update(extra)
    log = os.path.join(HERE, "_bat_%s.log" % tag)
    with io.open(log, "wb") as handle:
        subprocess.run([BLENDER] + BASE, cwd=HERE, env=env, stdout=handle,
                       stderr=subprocess.STDOUT)
    text = io.open(log, encoding="utf-8", errors="replace").read()
    match = re.search(r"E03_REPORT (\{.*\})", text)
    if not match:
        return None
    return json.loads(match.group(1))


def main():
    base = run({}, "base")
    if base is None:
        print("BASE NO REPORT —— 先修基线")
        return 1
    print("BASE  failed=%s  non_ok=%s" % (base.get("failed"),
                                          base.get("non_ok_bools")))
    print("-" * 78)
    lazy = []
    for key, desc in KNOBS:
        rep = run({key: "1"}, key)
        if rep is None:
            print("%-24s %-16s ** NO REPORT **" % (key, desc))
            lazy.append(key)
            continue
        red = sorted(set(rep.get("failed") or [])
                     | set(rep.get("non_ok_bools") or []))
        if red:
            print("%-24s %-16s red=%s" % (key, desc, red))
        else:
            print("%-24s %-16s *** 惰性：没有任何判据见红 ***" % (key, desc))
            lazy.append(key)
    print("-" * 78)
    print("LAZY_KNOBS = %s" % lazy)
    return 1 if lazy else 0


if __name__ == "__main__":
    raise SystemExit(main())
