"""D04 破防 —— 只读探针：末帧 vs 零位帧的**像素差量化**，与 D 族对照组。

背景：
    `probe_d04_pixels.py` 的 `end_identical_ok`（f60 vs f0 **逐位相同**）红了，
    但同一对帧的**几何指标全部是 0**：
        front_arm_delta_px = 0 ｜ side_torso_delta_px = 0.0 ｜ side_head_delta_px = -0.0
    ⟹ 红的不是"姿态回不去"，而是"通道值差了几个 LSB"。

本探针做两件事：
    ① 量化 f60↔f0 到底差多少（差异像素数 / 占比 / 通道差最大值与均值）；
    ② **对照组**：把 D02(Guard_Loop) / D03(Guard_Hit) 的同类帧对也量一遍 ——
       如果 D02/D03 同样不是逐位相同，那"逐位相同"就不是 D 族可达的判据，
       应当换成有量纲的判据（**不是**为了绿灯而放宽，是判据本身选错了）。

用法： python probe_d04_endpix.py
"""

import glob
import os

import numpy as np

PREVIEW = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "..", "previews", "anim")

# (标签, 前帧文件名, 后帧文件名) —— 后帧必须是"回零位"的那一帧
# 三视图都量：正面对"宽度差"最敏感，侧面对"前后/俯仰差"最敏感。
PAIRS = []
for _v, _suf in (("正面", "front"), ("侧面", "side")):
    PAIRS += [
        ("D04 回零位 f0↔f60 " + _v,
         "guardbreak_%s_f0000.png" % _suf, "guardbreak_%s_f0060.png" % _suf),
        ("D04 硬直平台 f4↔f14 " + _v,
         "guardbreak_%s_f0004.png" % _suf, "guardbreak_%s_f0014.png" % _suf),
        ("D03 对照 回零位 f0↔f36 " + _v,
         "guardhit_%s_f0000.png" % _suf, "guardhit_%s_f0036.png" % _suf),
    ]


def load(path):
    import bpy  # noqa: PLC0415  —— Blender 自带图像解码
    image = bpy.data.images.load(path)
    w, h = image.size
    px = np.array(image.pixels[:], dtype=np.float32).reshape(h, w, 4)
    bpy.data.images.remove(image)
    return px


def stats(a, b):
    d = np.abs(a - b)
    both = np.maximum(np.abs(a[..., :3]).max(axis=-1),
                      np.abs(b[..., :3]).max(axis=-1))
    mask = both > 0.02                      # 只看有内容的像素（去掉纯白背景抖动）
    out = {"n_px": int(mask.sum())}
    if not out["n_px"]:
        return out
    dd = d[..., :3][mask]
    out["diff_px"] = int((dd.max(axis=-1) > 1.0 / 255.0 + 1e-6).sum())
    out["pct"] = round(100.0 * out["diff_px"] / out["n_px"], 4)
    out["max_lsb"] = round(float(dd.max()) * 255.0, 3)
    out["mean_lsb"] = round(float(dd.mean()) * 255.0, 3)
    out["p999_lsb"] = round(float(np.percentile(dd, 99.9)) * 255.0, 3)
    return out


def main():
    print("=" * 84)
    print("D04 末帧像素差量化 ｜ 问题：\"逐位相同\"是 D 族可达的判据吗？")
    print("=" * 84)
    for label, name_a, name_b in PAIRS:
        a_path = os.path.join(PREVIEW, name_a)
        b_path = os.path.join(PREVIEW, name_b)
        if not os.path.exists(a_path) or not os.path.exists(b_path):
            print("  %-30s 缺图（%s / %s）" % (label, name_a, name_b))
            print("-" * 84)
            continue
        s = stats(load(a_path), load(b_path))
        identical = (s.get("diff_px", 0) == 0)
        print("  %-30s %s  vs  %s" % (label, name_a, name_b))
        print("      内容像素 %d ｜ 差异像素 %d (%.4f%%) ｜ max %.2f lsb ｜ "
              "p99.9 %.2f lsb ｜ mean %.3f lsb ｜ 逐位相同=%s"
              % (s.get("n_px", 0), s.get("diff_px", -1), s.get("pct", -1.0),
                 s.get("max_lsb", -1.0), s.get("p999_lsb", -1.0),
                 s.get("mean_lsb", -1.0), identical))
        print("-" * 84)


if __name__ == "__main__":
    main()
