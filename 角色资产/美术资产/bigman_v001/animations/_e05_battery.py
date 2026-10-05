"""E05 反向验证批量驱动：逐个打开旋钮，要求**每一个都让门禁见红**。

用法（在 animations 目录下）：
    "C:/Users/zhuangmenghong/.workbuddy/binaries/python/versions/3.13.12/python.exe" _e05_battery.py

判据：每条旋钮跑完，`failed ∪ non_ok_bools` 必须**非空**。
若某条为空 ⟹ 该旋钮是**惰性**的（没真的接进代码 / 扰动不在判据可见的那一维），
必须回去改，不能登记为「已验证」。

★ 顺序照清单 §「E05 详细计划」§4 step 7（9 组 + 1 组补充）：
  ① SEAM_ZERO ② FARCLASH ③ DEEPCLASH ④ NOHITSTOP ⑤ NOSHOULDER
  ⑥ FOOTSWAY ⑦ ASYMCLASH ⑧ LOOPBREAK ⑨ OVER ⑩ NOSINK
"""
import io
import json
import os
import re
import subprocess

BLENDER = "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = ["--background", "--factory-startup", "--python", "anim_battle_start.py"]

KNOBS = [
    ("E05_TP_SEAM_ZERO", "① 首帧改零位"),
    ("E05_TP_FARCLASH", "② ★★★ 两拳拉开（命门）"),
    ("E05_TP_DEEPCLASH", "③ ★★★ 两拳推进（互穿）"),
    ("E05_TP_NOHITSTOP", "④ ★ 碰拳无定格"),
    ("E05_TP_NOSHOULDER", "⑤ ★ 肩膀不动"),
    ("E05_TP_FOOTSWAY", "⑥ ★ 脚滑"),
    ("E05_TP_ASYMCLASH", "⑦ ★ 碰拳不对称"),
    ("E05_TP_LOOPBREAK", "⑧ 末帧不闭合"),
    ("E05_TP_OVER", "⑨ ★ 过头（区间上限）"),
    ("E05_TP_NOSINK", "⑩ ★ 不沉不发力（下限）"),
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
    match = re.search(r"E05_REPORT (\{.*\})", text)
    if not match:
        return None
    return json.loads(match.group(1))


def main():
    base = run({}, "E05_base")
    if base is None:
        print("BASE NO REPORT —— 先修基线")
        return 1
    print("BASE  failed=%s  non_ok=%s" % (base.get("failed"),
                                          base.get("non_ok_bools")))
    if base.get("failed") or base.get("non_ok_bools"):
        print("!! 基线不是全绿，先修基线再跑反面验证")
        return 1
    print("-" * 78)
    lazy = []
    for key, desc in KNOBS:
        rep = run({key: "1"}, "E05_" + key)
        if rep is None:
            print("%-22s %-22s ** NO REPORT **" % (key, desc))
            lazy.append(key)
            continue
        red = sorted(set(rep.get("failed") or [])
                     | set(rep.get("non_ok_bools") or []))
        if red:
            print("%-22s %-22s red=%s" % (key, desc, red))
        else:
            print("%-22s %-22s *** 惰性：没有任何判据见红 ***" % (key, desc))
            lazy.append(key)
    print("-" * 78)
    print("LAZY_KNOBS = %s" % lazy)
    return 1 if lazy else 0


if __name__ == "__main__":
    raise SystemExit(main())
