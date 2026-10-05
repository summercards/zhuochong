"""verify_glb —— 直接解析 GLB 二进制，核对导出的动画是否真的落进去了。

为什么要单独验：Blender 的导出算子在不认识的参数上不一定报错，
"文件生成了"和"文件里有动画"是两件事。引擎侧拿到没有 animation 的 GLB，
要到集成阶段才发现 —— 那时候已经晚了好几支动画。

用法（纯 Python，不需要 Blender）：
    python verify_glb.py <path.glb>
"""

import json
import struct
import sys


def read_glb(path):
    with open(path, "rb") as handle:
        data = handle.read()
    magic, version, total = struct.unpack("<III", data[:12])
    if magic != 0x46546C67:
        raise ValueError("不是 GLB 文件（magic=%08x）" % magic)
    chunks = {}
    offset = 12
    while offset < total:
        length, kind = struct.unpack("<II", data[offset:offset + 8])
        chunks[kind] = data[offset + 8:offset + 8 + length]
        offset += 8 + length
    return version, json.loads(chunks[0x4E4F534A].decode("utf-8"))


def main(path):
    version, doc = read_glb(path)
    animations = doc.get("animations", [])
    nodes = doc.get("nodes", [])
    accessors = doc.get("accessors", [])

    print("GLB %s" % path)
    print("  version=%d  nodes=%d  meshes=%d  skins=%d  materials=%d"
          % (version, len(nodes), len(doc.get("meshes", [])),
             len(doc.get("skins", [])), len(doc.get("materials", []))))
    print("  animations=%d" % len(animations))
    for animation in animations:
        span = 0.0
        bones = set()
        for channel in animation.get("channels", []):
            sampler = animation["samplers"][channel["sampler"]]
            accessor = accessors[sampler["input"]]
            if accessor.get("max"):
                span = max(span, accessor["max"][0])
            target = channel["target"]
            bones.add(nodes[target["node"]].get("name", "?"))
        print("    - %-24s 通道=%3d 骨骼=%3d 时长=%.3fs"
              % (animation.get("name", "?"), len(animation["channels"]),
                 len(bones), span))
    return animations


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else (
        r"I:/工作项目/BIGMANFIGHT/角色资产/美术资产/bigman_v001/"
        r"bigman_anim_v001.glb")
    if not main(target):
        print("!! 没有任何动画，导出配置有问题")
        sys.exit(1)
