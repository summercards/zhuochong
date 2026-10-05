# -*- coding: utf-8 -*-
"""资产一致性校验器 —— 三桶必须同版本、同几何。

这不是「检查一下」，是**会失败的断言**。三角面数/网格数/材质数被改动、
或者某桶被单独换了版本，这里会红。

用法:
    python verify_assets.py                # 校验 assets/characters 下全部角色
    python verify_assets.py --json out.json

退出码: 0 = 全部通过; 1 = 有断言失败
"""
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.abspath(os.path.join(HERE, "..", "assets", "characters"))

GLB_MAGIC = 0x46546C67
CHUNK_JSON = 0x4E4F534A

NAME_RE = re.compile(r"^(?P<cid>[a-z0-9_]+)_(?P<role>model|skin|anim)_v(?P<ver>\d{3})\.glb$")

# 各角色期望值（改资产就必须同步改这里，否则门禁会挡住你）
EXPECT = {
    "bigman": {
        "triangles": 78048,
        "meshes": 91,
        "materials": 17,
        "images": 0,
        "joints": 57,
        "anims": 68,
        # GLB 里**没有** JOINTS_0 的 primitive 数（不会跟骨骼动）。
        # 当前 = 2（Jacket_Hem / Jacket_Hem_Line 下摆件，登记在案）。
        # 运行时 Fighter 会按同一判据把它们隐藏，并且也用这个数字做断言 ——
        # 所以这里和那边必须同时改，任何一侧漂了都会被门禁或断言拦下。
        "unskinned": 2,
    }
}


def read_glb_json(path):
    with open(path, "rb") as fh:
        data = fh.read()
    magic, _ver, length = struct.unpack_from("<III", data, 0)
    if magic != GLB_MAGIC:
        raise ValueError("not a GLB: %s" % path)
    off = 12
    while off + 8 <= length:
        clen, ctype = struct.unpack_from("<II", data, off)
        off += 8
        chunk = data[off:off + clen]
        off += clen
        if ctype == CHUNK_JSON:
            return json.loads(chunk.decode("utf-8"))
    raise ValueError("no JSON chunk: %s" % path)


def prim_tris(g, prim):
    n = g["accessors"][prim["indices"]]["count"] if "indices" in prim \
        else g["accessors"][prim["attributes"]["POSITION"]]["count"]
    mode = prim.get("mode", 4)
    if mode == 4:
        return n // 3
    if mode in (5, 6):
        return max(0, n - 2)
    return 0


def measure(path):
    g = read_glb_json(path)
    tris = sum(prim_tris(g, p) for m in g.get("meshes", []) for p in m.get("primitives", []))
    skins = g.get("skins", [])
    # 未蒙皮 primitive：只要有一个顶点属性里没有 JOINTS_0，这一块就不会跟骨骼动。
    # 它们在画面里表现为"悬在静止位姿上的一块" —— 静态看不出来，动起来才露馅。
    unskinned = 0
    for m in g.get("meshes", []):
        for p in m.get("primitives", []):
            if "JOINTS_0" not in p.get("attributes", {}):
                unskinned += 1
    return {
        "bytes": os.path.getsize(path),
        "triangles": tris,
        "meshes": len(g.get("meshes", [])),
        "materials": len(g.get("materials", [])),
        "images": len(g.get("images", [])),
        "textures": len(g.get("textures", [])),
        "skins": len(skins),
        "joints": len(skins[0]["joints"]) if skins else 0,
        "anims": len(g.get("animations", [])),
        "anim_names": [a.get("name") for a in g.get("animations", [])],
        "unskinned": unskinned,
    }


def engine_name(name, all_names):
    """复现 Godot glTF 导入器的动画名规则（实测归纳）。

    Godot 会把动画名结尾的 `_Loop` 去掉 —— 它把 `_Loop` 当循环标记 ——
    但**仅当去掉后缀后不与文件里其它动画名冲突时**才改。

    实测证据（tools/probe_anim_names.gd）：
      Guard_Loop  -> Guard         （去掉后无人撞名，所以改了）
      Charge_Loop -> Charge_Loop   （去掉会撞上已有的 Charge，所以保住）
    对照实验：把 GLB 里 Guard_Loop 等长改成 GuardXLoop 后 Godot 原样保留。
    """
    suffix = "_Loop"
    if name.endswith(suffix):
        stripped = name[:-len(suffix)]
        if stripped not in (set(all_names) - {name}):
            return stripped
    return name


def scan_characters():
    found = {}
    if not os.path.isdir(ASSETS):
        return found
    for cid in sorted(os.listdir(ASSETS)):
        cdir = os.path.join(ASSETS, cid)
        if not os.path.isdir(cdir):
            continue
        buckets = {}
        for role in ("model", "skin", "animations"):
            rdir = os.path.join(cdir, "model" if role == "model" else role)
            if not os.path.isdir(rdir):
                continue
            for fn in sorted(os.listdir(rdir)):
                m = NAME_RE.match(fn)
                if m:
                    buckets.setdefault(m.group("role"), []).append(
                        (os.path.join(rdir, fn), m.group("ver")))
        found[cid] = buckets
    return found


def lint_scripts(failures):
    """静态门禁：把两条**踩过的坑**变成会失败的断言。

    这两条不是风格偏好，是真实故障的单行复现条件：

    (a) `current_animation` 恒等比较 —— 非循环动画播完后 AnimationPlayer 会
        停止播放并把 `current_animation` 清成空串，于是
        `_ap.current_animation == "Guard_Start"` 永远为假，状态机卡死。
        实测现场：tools/probe_guard.gd。所以**禁止**拿它做"当前是哪段"的判断；
        要用 Fighter._clip（清单名）。

    (b) 写死的 clip 名必须在 manifest 里存在 —— 改资产后代码里的裸字符串
        不会被任何东西发现，只有运行到那一步才炸。
    """
    sdir = os.path.abspath(os.path.join(HERE, "..", "scripts"))
    if not os.path.isdir(sdir):
        return
    man = os.path.join(ASSETS, "bigman", "animations", "manifest.json")
    clip_names = set()
    if os.path.isfile(man):
        with open(man, encoding="utf-8") as fh:
            clip_names = set(json.load(fh).get("clips", {}))

    identity_re = re.compile(r"current_animation\s*(==|!=)")
    shaped_re = re.compile(r"\"([A-Z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)+)\"")
    arg_re = re.compile(r"_(?:play|start_attack)\(\s*\"([^\"]+)\"")

    for root, _dirs, files in os.walk(sdir):
        for fn in sorted(files):
            if not fn.endswith(".gd"):
                continue
            path = os.path.join(root, fn)
            rel = os.path.relpath(path, os.path.dirname(sdir)).replace("\\", "/")
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
            for i, line in enumerate(text.splitlines(), 1):
                m = identity_re.search(line)
                if m:
                    failures.append(
                        "ENGINE_NAME_IDENTITY: %s:%d 拿 current_animation 做恒等判断 —— "
                        "非循环动画播完后它会被清成空串，判断必然失效。改用 Fighter._clip。"
                        % (rel, i))
            if not clip_names:
                continue
            cands = set(shaped_re.findall(text))
            cands |= set(arg_re.findall(text))
            for name in sorted(cands):
                if name not in clip_names:
                    failures.append(
                        "CLIP_NAME_UNKNOWN: %s 引用了 manifest 里不存在的 clip %r" % (rel, name))


def main():
    out_json = None
    if "--json" in sys.argv:
        out_json = sys.argv[sys.argv.index("--json") + 1]

    failures = []
    report = {"characters": {}}

    # 0) 脚本静态门禁（与资产无关的部分）
    lint_scripts(failures)

    for cid, buckets in scan_characters().items():
        exp = EXPECT.get(cid)
        if exp is None:
            failures.append("EXPECT_MISSING: 角色 %s 没有在 EXPECT 里登记期望值" % cid)
            continue

        # 1) 三桶齐备
        for role in ("model", "skin", "anim"):
            if not buckets.get(role):
                failures.append("BUCKET_MISSING: %s/%s 桶为空" % (cid, role))

        # 2) 版本号一致
        vers = {r: sorted({v for _, v in vs}) for r, vs in buckets.items() if vs}
        allver = {v for vs in vers.values() for v in vs}
        if len(allver) != 1:
            failures.append("VERSION_SPLIT: %s 三桶版本不一致 %s" % (cid, vers))
        if any(len(vs) > 1 for vs in vers.values()):
            failures.append("VERSION_DUP: %s 同一桶存在多版本并存 %s" % (cid, vers))

        # 3) 逐桶实测
        meas = {}
        for role, lst in buckets.items():
            path, ver = lst[0]
            meas[role] = measure(path)
            meas[role]["file"] = os.path.basename(path)

        report["characters"][cid] = {"versions": vers, "measured": meas}

        # 4) 几何必须完全一致
        base = meas.get("model")
        if base:
            for role, m in meas.items():
                if role == "model":
                    continue
                if m["triangles"] != base["triangles"]:
                    failures.append("GEOM_DRIFT: %s %s 三角面 %d != model %d"
                                    % (cid, role, m["triangles"], base["triangles"]))
                if m["meshes"] != base["meshes"]:
                    failures.append("MESH_DRIFT: %s %s 网格数 %d != model %d"
                                    % (cid, role, m["meshes"], base["meshes"]))
                if m["materials"] != base["materials"]:
                    failures.append("MAT_DRIFT: %s %s 材质数 %d != model %d"
                                    % (cid, role, m["materials"], base["materials"]))

        # 5) 各桶内容物必须符合定义
        mm = meas.get("model", {})
        sk = meas.get("skin", {})
        an = meas.get("anim", {})
        if mm.get("skins") or mm.get("anims"):
            failures.append("BUCKET_DEF: %s/model 含骨架或动画 (skins=%s anims=%s)"
                            % (cid, mm.get("skins"), mm.get("anims")))
        if sk.get("anims"):
            failures.append("BUCKET_DEF: %s/skin 含动画 (%d 段)" % (cid, sk["anims"]))
        if sk.get("skins") != 1:
            failures.append("BUCKET_DEF: %s/skin 骨架数应为 1，实为 %s" % (cid, sk.get("skins")))
        if an.get("skins") != 1:
            failures.append("BUCKET_DEF: %s/anim 骨架数应为 1，实为 %s" % (cid, an.get("skins")))

        # 6) 对期望值
        for key in ("triangles", "meshes", "materials", "images", "joints"):
            for role, m in meas.items():
                got = m.get(key)
                if role == "model" and key == "joints":
                    continue
                if got != exp[key]:
                    failures.append("EXPECT: %s %s.%s 期望 %s 实测 %s"
                                    % (cid, role, key, exp[key], got))
        if an and an["anims"] != exp["anims"]:
            failures.append("EXPECT: %s anim.anims 期望 %d 实测 %d"
                            % (cid, exp["anims"], an["anims"]))
        # 未蒙皮件数：只在 anim 桶（真正被游戏加载的那份）上校验。
        # 数量变了说明重导时又漏绑了（或多绑了）—— 运行时那边会一起炸。
        if an and "unskinned" in exp and an.get("unskinned") != exp["unskinned"]:
            failures.append(
                "UNSKINNED_DRIFT: %s anim 桶未蒙皮 primitive 期望 %d 实测 %d —— "
                "有网格没绑到骨架，它不会跟骨骼动（运行时也会被隐藏）"
                % (cid, exp["unskinned"], an.get("unskinned")))

        # 7) manifest 与 GLB 的 clip 名必须一一对应
        man_path = os.path.join(ASSETS, cid, "animations", "manifest.json")
        if os.path.isfile(man_path) and an:
            with open(man_path, encoding="utf-8") as fh:
                man = json.load(fh)
            man_names = set(man.get("clips", {}))
            glb_names = set(an["anim_names"])
            if man_names != glb_names:
                failures.append("MANIFEST_MISMATCH: %s manifest-only=%s glb-only=%s"
                                % (cid, sorted(man_names - glb_names), sorted(glb_names - man_names)))
            report["characters"][cid]["manifest_clips"] = len(man_names)
        elif an:
            failures.append("MANIFEST_MISSING: %s/animations/manifest.json 不存在" % cid)

        # 8) 引擎名差异表必须与"Godot 导入器规则"逐条一致
        #    这是跨语言契约：运行时（GDScript）按这张表把清单名翻译成引擎名，
        #    这里用同一条规则从 GLB 重算。对不上就说明资产变了而表没跟上。
        if an and man_names:
            expected = {n: engine_name(n, an["anim_names"]) for n in an["anim_names"]}
            expected = {k: v for k, v in expected.items() if k != v}
            en_path = os.path.join(ASSETS, cid, "animations", "engine_names.json")
            if not os.path.isfile(en_path):
                failures.append("ENGINE_NAMES_MISSING: %s/animations/engine_names.json 不存在" % cid)
            else:
                with open(en_path, encoding="utf-8") as fh:
                    got = json.load(fh).get("fixups", {})
                if got != expected:
                    failures.append(
                        "ENGINE_NAMES_DRIFT: %s 差异表 %s 与实测规则 %s 不一致"
                        % (cid, got, expected))
                report["characters"][cid]["engine_fixups"] = got
                # 修正后的目标名按定义**不该**出现在 GLB 里 ——
                # 一旦出现，说明它和另一段动画撞名了，翻译会指错段。
                for k, v in got.items():
                    if v in an["anim_names"]:
                        failures.append("ENGINE_NAMES_COLLIDE: %s 修正项 %s->%s 与 GLB 里已有动画名撞名"
                                        % (cid, k, v))

    if out_json:
        with open(out_json, "w", encoding="utf-8") as fh:
            json.dump({"failures": failures, **report}, fh, ensure_ascii=False, indent=1)

    for cid, info in report["characters"].items():
        print("=== %s" % cid)
        for role, m in info["measured"].items():
            print("   %-4s %-28s %9dB tris=%-6d meshes=%-3d mats=%-2d joints=%-2d anims=%-3d unskinned=%d"
                  % (role, m["file"], m["bytes"], m["triangles"], m["meshes"],
                     m["materials"], m["joints"], m["anims"], m.get("unskinned", -1)))

    if failures:
        print("\nFAILED %d" % len(failures))
        for f in failures:
            print("  ✗ %s" % f)
        sys.exit(1)

    print("\nASSET_ASSERT_OK")


main()
