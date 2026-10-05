"""E04 反向验证批量驱动：逐个打开旋钮，要求**每一个都让门禁见红**。

用法（在 animations 目录下）：
    "C:/Users/zhuangmenghong/.workbuddy/binaries/python/versions/3.13.12/python.exe" _e04_battery.py

判据：每条旋钮跑完，`failed ∪ non_ok_bools` 必须**非空**。
若某条为空 ⟹ 该旋钮是**惰性**的（没真的接进代码 / 扰动不在判据可见的那一维），
必须回去改，不能登记为「已验证」。

★ 顺序照清单 §4 step 7：
  ① SEAM_ZERO ② NOSINK ③ NOLIFT ④ NOHITSTOP ⑤ GLUED ⑥ FOOTSWAY ⑦ LOOPBREAK ⑧ OVERSINK
"""
import io
import json
import os
import re
import subprocess

BLENDER = "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = ["--background", "--factory-startup", "--python", "anim_spawn.py"]

KNOBS = [
    ("E04_TP_SEAM_ZERO", "① 首帧改零位"),
    ("E04_TP_NOSINK", "② ★★★ 落地不下沉"),
    ("E04_TP_NOLIFT", "③ ★ 起跳不起"),
    ("E04_TP_NOHITSTOP", "④ ★ 落地无定格"),
    ("E04_TP_GLUED", "⑤ ★ 空中段脚没离地"),
    ("E04_TP_FOOTSWAY", "⑥ ★ 地面段脚滑"),
    ("E04_TP_LOOPBREAK", "⑦ 末帧不闭合"),
    ("E04_TP_OVERSINK", "⑧ 落地过头"),
    ("E04_TP_FOOTASYM", "⑨ ★ L 脚 +X（像素对称）"),
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
    match = re.search(r"E04_REPORT (\{.*\})", text)
    if not match:
        return None
    return json.loads(match.group(1))


def main():
    base = run({}, "E04_base")
    if base is None:
        print("BASE NO REPORT —— 先修基线")
        return 1
    print("BASE  failed=%s  non_ok=%s" % (base.get("failed"),
                                          base.get("non_ok_bools")))
    print("-" * 78)
    lazy = []
    for key, desc in KNOBS:
        rep = run({key: "1"}, "E04_" + key)
        if rep is None:
            print("%-24s %-18s ** NO REPORT **" % (key, desc))
            lazy.append(key)
            continue
        red = sorted(set(rep.get("failed") or [])
                     | set(rep.get("non_ok_bools") or []))
        if red:
            print("%-24s %-18s red=%s" % (key, desc, red))
        else:
            print("%-24s %-18s *** 惰性：没有任何判据见红 ***" % (key, desc))
            lazy.append(key)
    print("-" * 78)
    print("LAZY_KNOBS = %s" % lazy)
    return 1 if lazy else 0


if __name__ == "__main__":
    raise SystemExit(main())
