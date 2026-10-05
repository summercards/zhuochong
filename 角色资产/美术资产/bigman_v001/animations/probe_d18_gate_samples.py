"""D18 只读探针：导出**门禁真正看到的那份欧拉数据**。

为什么要这个
------------
`probe_d18_euler_all.py` 导的是 `solve_pose()` 的**原始**输出（54.597 峰值），
而门禁量的是 `A.sample_animation()` 读到的 `pose_bone.rotation_euler`——
两者**不是同一份数据**：滚转求解 / 尾段网格混合等后处理发生在
`A.build_action()`（`anim_getup_b.py:2568`）落键阶段，会把欧拉写法整体改写。

做法：挂钩 `A.sample_animation` 把 samples 里的 `euler` 落成 JSON，
并把所有**会写盘**的函数（保存工程 / 导出 GLB / 各种渲染）改成空操作。
只读：不写 blend、不写 previews、不导出 GLB。
"""
import json
import os
import sys

os.environ.setdefault("SKIP_RENDER", "1")
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import anim_lib as A            # noqa: E402

# ★ 允许指定被测模块：`D18_MODULE=_bak_getup_b_071112` 可复现快照上的历史最优
_MOD = os.environ.get("D18_MODULE", "anim_getup_b")
M = __import__(_MOD)
print("D18_GATE_SAMPLES 被测模块 = %s" % _MOD)

OUT = os.path.join(_HERE, "_d18_gate_samples.json")

_orig_sample = A.sample_animation


def hooked(arm, action, frame_start, frame_end, meshes=None):
    samples = _orig_sample(arm, action, frame_start, frame_end, meshes)
    payload = [{"f": r["frame"],
                "euler": {k: [round(x, 9) for x in v]
                          for k, v in r["euler"].items()}}
               for r in samples]
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False)
    print("D18_GATE_SAMPLES frames=%d -> %s" % (len(payload), OUT))
    return samples


def _noop(*_a, **_k):
    return None


A.sample_animation = hooked
# ★ 不要动 `open_animation_project` —— `boot()`（`anim_getup_b.py:1589`）靠它载入落盘工程
for _name in ("save_project", "export_glb",
              "render_pose_sheet", "render_animation_mp4", "render_still"):
    if hasattr(A, _name):
        setattr(A, _name, _noop)

M.main()
