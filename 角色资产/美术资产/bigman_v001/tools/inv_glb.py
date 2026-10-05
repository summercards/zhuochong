# -*- coding: utf-8 -*-
"""解析 GLB：网格 / 蒙皮 / 材质 / 贴图 / 动画 的实测统计。

用法:
    python inv_glb.py <out.json> <file1.glb> [file2.glb ...]
"""
import json
import os
import struct
import sys

GLB_MAGIC = 0x46546C67
CHUNK_JSON = 0x4E4F534A
CHUNK_BIN = 0x004E4942

PRIM_MODES = {0: "POINTS", 1: "LINES", 2: "LINE_LOOP", 3: "LINE_STRIP",
              4: "TRIANGLES", 5: "TRIANGLE_STRIP", 6: "TRIANGLE_FAN"}


def read_glb(path):
    with open(path, "rb") as fh:
        data = fh.read()
    if len(data) < 12:
        raise ValueError("too short")
    magic, version, length = struct.unpack_from("<III", data, 0)
    if magic != GLB_MAGIC:
        raise ValueError("not a GLB (magic=%08x)" % magic)
    off = 12
    js = None
    binlen = 0
    while off + 8 <= length:
        clen, ctype = struct.unpack_from("<II", data, off)
        off += 8
        chunk = data[off:off + clen]
        off += clen
        if ctype == CHUNK_JSON:
            js = json.loads(chunk.decode("utf-8"))
        elif ctype == CHUNK_BIN:
            binlen = clen
    return js, binlen, version, length


def acc_count(g, idx):
    return g["accessors"][idx].get("count", 0)


def prim_tris(g, prim):
    mode = prim.get("mode", 4)
    if "indices" in prim:
        n = acc_count(g, prim["indices"])
    else:
        n = acc_count(g, prim["attributes"]["POSITION"])
    if mode == 4:
        return n // 3
    if mode in (5, 6):
        return max(0, n - 2)
    return 0


def summarise(path):
    g, binlen, version, total = read_glb(path)
    out = {
        "path": path,
        "file_bytes": os.path.getsize(path),
        "glb_version": version,
        "bin_chunk_bytes": binlen,
        "generator": g.get("asset", {}).get("generator"),
        "copyright": g.get("asset", {}).get("copyright"),
        "counts": {},
    }

    nodes = g.get("nodes", [])
    meshes = g.get("meshes", [])
    materials = g.get("materials", [])
    images = g.get("images", [])
    textures = g.get("textures", [])
    skins = g.get("skins", [])
    anims = g.get("animations", [])

    out["counts"] = {
        "nodes": len(nodes),
        "meshes": len(meshes),
        "primitives": sum(len(m.get("primitives", [])) for m in meshes),
        "materials": len(materials),
        "images": len(images),
        "textures": len(textures),
        "skins": len(skins),
        "animations": len(anims),
    }

    # 三角面
    tris = 0
    prim_modes = {}
    for m in meshes:
        for p in m.get("primitives", []):
            tris += prim_tris(g, p)
            mode = p.get("mode", 4)
            prim_modes[PRIM_MODES.get(mode, str(mode))] = prim_modes.get(PRIM_MODES.get(mode, str(mode)), 0) + 1
    out["triangles"] = tris
    out["primitive_modes"] = prim_modes

    # 蒙皮
    out["skins"] = []
    for s in skins:
        out["skins"].append({
            "name": s.get("name"),
            "joints": len(s.get("joints", [])),
            "skeleton": nodes[s["skeleton"]].get("name") if "skeleton" in s else None,
            "inverseBindMatrices": "inverseBindMatrices" in s,
        })

    # 骨骼层级（取第一个 skin 的 joints）
    if skins:
        joint_set = set(skins[0].get("joints", []))
        tree = []
        for ji in skins[0].get("joints", []):
            n = nodes[ji]
            parent_name = None
            for pi, pn in enumerate(nodes):
                if ji in pn.get("children", []):
                    parent_name = pn.get("name")
                    break
            tree.append({"name": n.get("name"), "parent": parent_name,
                         "children": [nodes[c].get("name") for c in n.get("children", [])
                                      if c in joint_set]})
        out["joint_tree"] = tree

    # 未蒙皮网格节点（有 mesh 但不在任何 skin 里）
    skinned_nodes = set()
    for n in nodes:
        if "skin" in n:
            skinned_nodes.add(n.get("name"))
    unskinned = []
    for i, n in enumerate(nodes):
        if "mesh" in n and "skin" not in n:
            mi = n["mesh"]
            tp = sum(prim_tris(g, p) for p in meshes[mi].get("primitives", []))
            unskinned.append({"node": n.get("name"), "mesh": meshes[mi].get("name"), "tris": tp})
    out["unskinned_mesh_nodes"] = unskinned
    out["skinned_node_count"] = len(skinned_nodes)

    # 材质清单
    out["material_names"] = [m.get("name") for m in materials]

    # 贴图
    out["image_names"] = [i.get("name") or i.get("uri") or i.get("mimeType") for i in images]

    # 动画：名称 / 通道数 / 时长
    alist = []
    for a in anims:
        dur = 0.0
        frame_lo = None
        frame_hi = None
        for s in a.get("samplers", []):
            acc = g["accessors"][s["input"]]
            if "max" in acc:
                dur = max(dur, float(acc["max"][0]))
            if "min" in acc:
                v = float(acc["min"][0])
                frame_lo = v if frame_lo is None else min(frame_lo, v)
            if "max" in acc:
                v = float(acc["max"][0])
                frame_hi = v if frame_hi is None else max(frame_hi, v)
        tags = set()
        targets = set()
        for ch in a.get("channels", []):
            targets.add(ch["target"]["path"])
        for m in meshes:
            pass
        alist.append({
            "name": a.get("name"),
            "channels": len(a.get("channels", [])),
            "samplers": len(a.get("samplers", [])),
            "duration_s": round(dur, 6),
            "frames_60fps": round(dur * 60.0, 3),
            "t_lo": frame_lo,
            "t_hi": frame_hi,
            "paths": sorted(targets),
        })
    out["animations"] = alist
    return out


def main():
    out_path = sys.argv[1]
    files = sys.argv[2:]
    report = {"files": []}
    for f in files:
        report["files"].append(summarise(os.path.abspath(f)))

    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)
    print("WROTE %s" % out_path)
    for r in report["files"]:
        c = r["counts"]
        print("== %s" % os.path.basename(r["path"]))
        print("   bytes=%d tris=%d nodes=%d meshes=%d prims=%d mats=%d imgs=%d anims=%d skins=%d"
              % (r["file_bytes"], r["triangles"], c["nodes"], c["meshes"], c["primitives"],
                 c["materials"], c["images"], c["animations"], c["skins"]))
        if r["skins"]:
            print("   skin joints=%s unskinned_nodes=%d" % (r["skins"][0]["joints"], len(r["unskinned_mesh_nodes"])))
        for u in r["unskinned_mesh_nodes"]:
            print("   UNSKINNED %s (%d tris)" % (u["node"], u["tris"]))


main()
