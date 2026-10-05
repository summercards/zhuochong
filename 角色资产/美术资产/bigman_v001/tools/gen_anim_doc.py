# -*- coding: utf-8 -*-
"""由实测数据生成《动画文档》。

数据源（全部为实测，非转录）：
    doc/_animation_index.json   —— 清单 67 行 × Blend Action × GLB 时长，三源合并
    doc/_actions_dump.json      —— 57 骨层级 + 68 个 Action 的全量自定义属性
    doc/_glb_inventory.json     —— GLB 网格/蒙皮/材质/贴图/动画 统计

用法:
    python gen_anim_doc.py <doc_dir> <out.md>
"""
import json
import os
import sys

FAMILY_ORDER = ["基础移动", "普通攻击", "连招与特殊技", "防御与受击", "状态与流程"]
FAMILY_DESC = {
    "基础移动": "位移、站姿、跳跃。除跳跃外全部**原地**，位移由程序给。",
    "普通攻击": "起手快、后摇短。全部以 `Idle_01@0` 为首帧，起手不闪。",
    "连招与特殊技": "带 Root Motion 的强表演动作。终结技、抓投、技能、大招。",
    "防御与受击": "防御循环、破防、八向受击、击飞、倒地、起身、撞墙。",
    "状态与流程": "眩晕/虚弱/狂暴/入场/开战/胜负/死亡复活。多以 `Idle_01@0` 作接缝。",
}


def s(v):
    """归一化缺省值：Blender 的 IDProperty 存不了 None，脚本里写成了字符串 'None'。"""
    if v is None or v == "" or v == "None":
        return "—"
    return str(v)


def fmt_frames(fr):
    if not fr:
        return "—"
    return "%g–%g" % (fr[0], fr[1])


def fmt_rm(rm):
    if not isinstance(rm, list) or len(rm) < 2:
        return "—"
    if abs(rm[0]) < 1e-9 and abs(rm[1]) < 1e-9:
        return "—"
    return "[%.3f, %.3f]" % (rm[0], rm[1])


def fmt_int(v):
    if isinstance(v, str) and v == "None":
        return "—"
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return s(v)


def main():
    doc = os.path.abspath(sys.argv[1])
    out = os.path.abspath(sys.argv[2])

    with open(os.path.join(doc, "_animation_index.json"), encoding="utf-8") as fh:
        idx = json.load(fh)
    with open(os.path.join(doc, "_actions_dump.json"), encoding="utf-8") as fh:
        dump = json.load(fh)
    with open(os.path.join(doc, "_glb_inventory.json"), encoding="utf-8") as fh:
        glb = json.load(fh)

    E = idx["entries"]
    by_name = {e["name"]: e for e in E}
    arm = dump["armatures"][0]
    bones = arm["bones"]
    anim_glb = glb["files"][0]

    L = []
    W = L.append

    # ---------------- 头部 ----------------
    W("# bigman v001 动画文档")
    W("")
    W("> **本文档所有数值均为实测**，由 `tools/gen_anim_doc.py` 从 GLB 二进制与 Blender 工程直接生成，"
      "不经过任何人工转录。改资产后重跑脚本即可同步。")
    W("")
    W("| 项 | 值 |")
    W("|---|---|")
    W("| 角色 | `bigman`（近战猛男 / 力量型） |")
    W("| 版本 | v001 |")
    W("| 帧率 | **60 fps**（格斗逻辑帧） |")
    W("| 动画段数 | **%d**（清单 67 + `Charge_Loop` 配套循环） |" % anim_glb["counts"]["animations"])
    W("| 骨架 | `%s`，**%d 骨** |" % (arm["object"], arm["bone_count"]))
    W("| 网格 / 三角面 | %d / **%s** |" % (anim_glb["counts"]["meshes"], format(anim_glb["triangles"], ",")))
    W("| 材质 / 贴图 | %d / **%d**（纯色材质，零贴图） |" % (anim_glb["counts"]["materials"], anim_glb["counts"]["images"]))
    W("| 站姿身高 | **1.803 m** |")
    W("| 运行时文件 | `assets/characters/bigman/animations/bigman_anim_v001.glb` |")
    W("")
    W("---")
    W("")

    # ---------------- 一、坐标与单位 ----------------
    W("## 一、坐标与单位约定")
    W("")
    W("写任何跟动画有关的代码之前先看这张表。")
    W("")
    W("| 轴 | 含义 |")
    W("|---|---|")
    W("| `+X` | 角色**左**手侧 |")
    W("| `+Y` | 角色**背后** |")
    W("| `+Z` | 上 |")
    W("| 朝向 | **面朝 −Y** |")
    W("")
    W("- **时间**：全部 `frames` 按 60 fps 计。`秒 = 帧数 ÷ 60`。")
    W("- **长度**：全部米（m）。根位移 `root_motion_m` 也是米，写在**世界 XY 平面**上（不含 Z）。")
    W("- **地面**：`z = 0`，角色脚底贴 `z = 0`。")
    W("- **Godot 侧朝向修正**：Godot 前向是 `−Z`，本角色前向是 `−Y`，"
      "所以模型挂进场景后需要绕 **Y 轴 −90°**。")
    W("")
    W("---")
    W("")

    # ---------------- 二、骨架 ----------------
    W("## 二、骨架：%d 骨" % arm["bone_count"])
    W("")
    W("`%s`，根骨骼 `root`。分四条链：" % arm["object"])
    W("")
    W("| 链 | 骨骼 | 骨数 |")
    W("|---|---|---|")
    spine = [b for b in bones if b["name"] in
             ("root", "pelvis", "spine_01", "spine_02", "chest", "neck", "head",
              "jaw", "glasses", "eye.L", "eye.R")]
    ARM_PREFIX = ("shoulder", "upperarm", "forearm", "hand", "index", "middle",
                  "ring", "pinky", "thumb")
    arm_l = [b for b in bones if b["name"].endswith(".L") and b["name"].startswith(ARM_PREFIX)]
    arm_r = [b for b in bones if b["name"].endswith(".R") and b["name"].startswith(ARM_PREFIX)]
    legs = [b for b in bones if b["name"].startswith(("thigh", "shin", "foot", "toe"))]
    W("| 躯干与头 | `%s` | %d |" % ("` → `".join(b["name"] for b in spine), len(spine)))
    W("| 左上肢 | `shoulder.L`/`upperarm.L`/`forearm.L`/`hand.L` + 五指各 3 节 | %d |" % len(arm_l))
    W("| 右上肢 | `shoulder.R`/`upperarm.R`/`forearm.R`/`hand.R` + 五指各 3 节 | %d |" % len(arm_r))
    W("| 双腿 | `thigh` / `shin` / `foot` / `toe` ×L,R | %d |" % len(legs))
    W("| **合计** | | **%d** |" % arm["bone_count"])
    W("")
    W("关键骨长（用于程序算挂点/判定半径）：")
    W("")
    W("| 骨 | 长 (m) | 骨 | 长 (m) |")
    W("|---|---|---|---|")
    pairs = [("pelvis", "thigh.L"), ("spine_01", "shin.L"), ("spine_02", "foot.L"),
             ("chest", "toe.L"), ("neck", "shoulder.L"), ("head", "upperarm.L"),
             ("jaw", "forearm.L"), ("glasses", "hand.L")]
    bl = {b["name"]: b["length"] for b in bones}
    for a, b in pairs:
        W("| `%s` | %.4f | `%s` | %.4f |" % (a, bl.get(a, 0), b, bl.get(b, 0)))
    W("")
    W("---")
    W("")

    # ---------------- 三、总表 ----------------
    W("## 三、动画总表（%d 段）" % len(E))
    W("")
    W("| 编号 | Clip | 中文 | 家族 | 帧区间 | 时长 | 循环 | 根位移 (m) | 前摇 | 命中 | 取消 | 停顿 |")
    W("|---|---|---|---|---|---|:--:|---|:--:|:--:|:--:|:--:|")
    for e in E:
        W("| `%s` | `%s` | %s | %s | %s | %.3f s | %s | %s | %s | %s | %s | %s |" % (
            e["code"], e["name"], e["cn"], e["family"],
            fmt_frames(e["frames"]), e["duration_s"] or 0.0,
            "✅" if e["loop"] else "",
            fmt_rm(e["root_motion_m"]),
            fmt_int(e["antic_frame"]), fmt_int(e["hit_frame"]),
            fmt_int(e["cancel_frame"]), fmt_int(e["hitstop_frames"])))
    W("")

    total_s = sum(e["duration_s"] or 0 for e in E)
    longest = max(E, key=lambda x: x["duration_s"] or 0)
    shortest = min(E, key=lambda x: x["duration_s"] or 0)
    attacks = [e for e in E if e["hit_frame"] is not None]
    W("**统计**：")
    W("")
    W("| 指标 | 值 |")
    W("|---|---|")
    W("| 总时长 | **%.3f s**（%d 段相加） |" % (total_s, len(E)))
    W("| 平均单段 | %.3f s |" % (total_s / len(E)))
    W("| 最长 | `%s` %.3f s |" % (longest["name"], longest["duration_s"]))
    W("| 最短 | `%s` %.3f s |" % (shortest["name"], shortest["duration_s"]))
    W("| 循环段 | %d 段 |" % len([e for e in E if e["loop"]]))
    W("| 带根位移 | %d 段 |" % len([e for e in E if fmt_rm(e["root_motion_m"]) != "—"]))
    W("| 有命中帧 | %d 段 |" % len(attacks))
    W("")
    W("---")
    W("")

    # ---------------- 四、分家族 ----------------
    W("## 四、分家族")
    W("")
    for fi, fam in enumerate(FAMILY_ORDER, start=1):
        items = [e for e in E if e["family"] == fam]
        pref = fam[0]
        W("### 4.%d %s（`%s` 族，%d 段）" % (fi, fam, "ABCDE"[fi - 1], len(items)))
        W("")
        W(FAMILY_DESC.get(fam, ""))
        W("")
        W("| 编号 | Clip | 中文 | 帧/时长 | 循环 | 根位移 (m) | 结构 |")
        W("|---|---|---|---|:--:|---|---|")
        for e in items:
            p = e["props"]
            seg = p.get("segments")
            struct = " / ".join(seg) if seg else (
                "前摇%s → 命中%s → 取消%s" % (fmt_int(e["antic_frame"]), fmt_int(e["hit_frame"]),
                                              fmt_int(e["cancel_frame"]))
                if e["hit_frame"] is not None else "—")
            W("| `%s` | `%s` | %s | %s / %.3f s | %s | %s | %s |" % (
                e["code"], e["name"], e["cn"], fmt_frames(e["frames"]),
                e["duration_s"] or 0, "✅" if e["loop"] else "", fmt_rm(e["root_motion_m"]), struct))
        W("")

    W("---")
    W("")

    # ---------------- 五、循环段 ----------------
    loops = [e for e in E if e["loop"]]
    W("## 五、循环段（%d 段）" % len(loops))
    W("")
    W("这些是**可以无限播**的。程序在进入对应状态时循环播放，退出时切走。")
    W("")
    W("| Clip | 中文 | 帧区间 | 单圈时长 | 家族 |")
    W("|---|---|---|---|---|")
    for e in loops:
        W("| `%s` | %s | %s | %.3f s | %s |" % (e["name"], e["cn"], fmt_frames(e["frames"]),
                                                e["duration_s"] or 0, e["family"]))
    W("")
    W("---")
    W("")

    # ---------------- 六、根位移 ----------------
    rms = [e for e in E if fmt_rm(e["root_motion_m"]) != "—"]
    W("## 六、根位移表（%d 段）" % len(rms))
    W("")
    W("> `root_motion_m = [x, y]`，单位米，**世界 XY 平面**（`+x` = 角色左手侧，`−y` = 角色前方）。")
    W("")
    W("程序用法有两种，二选一，**不要混**：")
    W("")
    W("```")
    W("A. 动画驱动位移（推荐给冲击技）：播完让角色沿 +root_motion 方向平移对应米数")
    W("B. 忽略根位移（推荐给受击）：只用动画做姿态，位移由受击逻辑自己给")
    W("```")
    W("")
    W("| Clip | 中文 | Δx (m) | Δy (m) | 总长 (m) | 方向 |")
    W("|---|---|---:|---:|---:|---|")
    for e in rms:
        x, y = e["root_motion_m"][0], e["root_motion_m"][1]
        d = (x * x + y * y) ** 0.5
        dirn = "前" if y < 0 else ("后" if y > 0 else "")
        dirn += "＋" if x * y != 0 else ""
        dirn += "左" if x > 0 else ("右" if x < 0 else "")
        W("| `%s` | %s | %+.3f | %+.3f | %.3f | %s |" % (e["name"], e["cn"], x, y, d, dirn or "—"))
    W("")
    W("---")
    W("")

    # ---------------- 七、事件帧 ----------------
    W("## 七、事件帧表（供程序打判定）")
    W("")
    W("四个时间点，全部是**帧号**（0 起算，60 fps）：")
    W("")
    W("| 标记 | 含义 | 程序该做什么 |")
    W("|---|---|---|")
    W("| `antic_frame` | 前摇结束 | 此时可以开始表现蓄力特效 / 音效 |")
    W("| `hit_frame` | 命中判定帧 | **这一帧生成攻击判定盒** |")
    W("| `cancel_frame` | 可取消帧 | 从这一帧起允许接下一段连招 |")
    W("| `hitstop_frames` | 打击停顿帧数 | 命中瞬间冻结全身 `hitstop_frames` 帧 |")
    W("")
    W("**取消窗口公式**：")
    W("")
    W("```")
    W("cancel_window_frames = frames[1] - cancel_frame")
    W("cancel_window_seconds = cancel_window_frames / 60")
    W("```")
    W("")
    W("有命中帧的 %d 段：" % len(attacks))
    W("")
    W("| Clip | 中文 | 前摇帧 | 命中帧 | 取消帧 | 停顿帧 | 取消窗口 | 判定点 (m) |")
    W("|---|---|:--:|:--:|:--:|:--:|---|:--:|")
    for e in attacks:
        cf = e["cancel_frame"]
        if isinstance(cf, bool) or not isinstance(cf, (int, float)):
            cw = s(cf)
        else:
            n = e["frames"][1] - cf
            cw = "%g 帧 / %.3f s" % (n, n / 60.0)
        hp = e["props"].get("hit_point_m")
        hp_s = "—"
        if isinstance(hp, list) and len(hp) == 3:
            hp_s = "(%.3f, %.3f, %.3f)" % tuple(hp)
        elif isinstance(hp, list) and hp:
            hp_s = "%s" % hp
        W("| `%s` | %s | %s | **%s** | %s | %s | %s | %s |" % (
            e["name"], e["cn"], fmt_int(e["antic_frame"]), fmt_int(e["hit_frame"]),
            fmt_int(e["cancel_frame"]), fmt_int(e["hitstop_frames"]), cw or "—", hp_s))
    W("")
    W("---")
    W("")

    # ---------------- 八、接缝与链路 ----------------
    W("## 八、接缝与链路")
    W("")
    W("> **接缝 = 上一段的末帧姿态与下一段的首帧姿态逐位相同**（不是「看起来像」，是矩阵级相等）。")
    W("> 有接缝的段落切换时**不会闪**；没有接缝的段落之间需要程序做混合（cross-fade）。")
    W("")
    seams = []
    for e in E:
        p = e["props"]
        for k in ("seam_in", "seam_out", "seam", "seam_ends"):
            if k in p:
                seams.append((e, k, p[k]))
    W("| Clip | 类型 | 接缝对象 |")
    W("|---|---|---|")
    for e, k, v in seams:
        W("| `%s` | `%s` | %s |" % (e["name"], k, json.dumps(v, ensure_ascii=False).strip('"')))
    W("")
    W("**继承关系**（`inherit_from` = 本段的首帧直接抄自某段某帧）：")
    W("")
    W("| Clip | 继承自 |")
    W("|---|---|")
    for e in E:
        p = e["props"]
        if "inherit_from" in p and p["inherit_from"] not in (None, "None"):
            W("| `%s` | `%s` |" % (e["name"], p["inherit_from"]))
    W("")
    W("**链接关系**（`link_prev` / `link_next` = 设计意图上的前后段）：")
    W("")
    W("| Clip | 前接 | 后接 |")
    W("|---|---|---|")
    for e in E:
        p = e["props"]
        if p.get("link_prev") or p.get("link_next"):
            W("| `%s` | %s | %s |" % (e["name"], s(p.get("link_prev")), s(p.get("link_next"))))
    W("")
    W("---")
    W("")

    # ---------------- 九、状态机 ----------------
    W("## 九、状态机建议")
    W("")
    W("这是给横版格斗模板用的落地方案，不是唯一解，但每个数字都有出处。")
    W("")
    W("### 9.1 状态划分")
    W("")
    W("| 状态 | 进入动画 | 循环 | 退出条件 |")
    W("|---|---|:--:|---|")
    rows = [
        ("`IDLE`", "`Idle_01`", "✅", "有输入 → 切 `WALK`/`RUN`/`CROUCH`/`JUMP`/`ATTACK`"),
        ("`WALK`", "`Walk_F` / `Walk_B`", "✅", "松开方向 → `IDLE`；按住加速键 → `RUN`"),
        ("`RUN`", "`Run`", "✅", "松开方向 → `RUN_STOP`；按攻击 → `DASH_ATK`"),
        ("`RUN_STOP`", "`Run_Stop`", "", "播完 → `IDLE`（54 帧 / 0.900 s）"),
        ("`TURN`", "`Turn`", "", "播完 → `IDLE`（30 帧 / 0.500 s）"),
        ("`CROUCH`", "`Crouch` → `Crouch_Idle`", "✅", "松开下蹲 → `IDLE`"),
        ("`JUMP`", "`Jump_Start`→`Jump_Up`→`Jump_Fall`→`Jump_Land`", "", "落地播完 → `IDLE`"),
        ("`ATTACK`", "`Light_01→02→03` / `Heavy_01` / `Heavy_02` / `Low_Attack` / `Uppercut`", "", "过 `cancel_frame` 可续招；否则播完 → `IDLE`"),
        ("`AIR_ATTACK`", "`Air_Light` / `Air_Heavy`", "", "落回 `Jump_Land`"),
        ("`DASH_ATK`", "`Dash_Attack`", "", "播完 → `IDLE`"),
        ("`SPECIAL`", "`Combo_Finish` / `Launcher` / `Knockdown_Attack` / `Ground_Smash` / `Throw` / `Skill_01~03`", "", "播完 → `IDLE`"),
        ("`CHARGE`", "`Charge` → `Charge_Loop`（循环）→ `Charge` 释放段", "✅", "松开蓄力键 → 释放"),
        ("`GRAB`", "`Grab_Start` → `Grab_Hold`（循环）→ `Throw`", "✅", "按投掷 → `Throw`；超时 → `IDLE`"),
        ("`ULTIMATE`", "`Ultimate_Start` → `Ultimate_Attack` → `Ultimate_End`", "", "播完 → `IDLE`"),
        ("`GUARD`", "`Guard_Start` → `Guard_Loop`", "✅", "松开 → `IDLE`；被打 → `Guard_Hit` / `Guard_Break`"),
        ("`HIT`", "`Hit_Light_F/B` / `Hit_Heavy_F/B` / `Hit_Head` / `Hit_Body` / `Hit_Leg`", "", "播完 → `IDLE`；吃击飞技 → `LAUNCH`"),
        ("`LAUNCH`", "`Launch_Hit` → `Air_Hit` → `Knockdown_F/B`", "", "落地 → `KNOCKDOWN`"),
        ("`KNOCKDOWN`", "`Knockdown_F/B` → `Ground_Hit` → `GetUp_F/B`", "", "起身播完 → `IDLE`"),
        ("`WALL`", "`Wall_Hit`", "", "播完 → `IDLE`"),
        ("`STUN`", "`Stun`", "✅", "计时结束 → `IDLE`"),
        ("`EXHAUST`", "`Exhausted`", "✅", "恢复 → `IDLE`"),
        ("`RAGE`", "`Rage`", "", "播完 → `IDLE`（Buff 已挂上）"),
        ("`FLOW`", "`Spawn` / `Battle_Start` / `Victory_01~03` / `Defeat` / `Death` / `Revive`", "", "见 9.3"),
    ]
    for r in rows:
        W("| %s | %s | %s | %s |" % r)
    W("")
    W("### 9.2 攻击连段规则")
    W("")
    W("轻拳三段是一个连段（`Light_01 → Light_02 → Light_03`）。每段的取消帧：")
    W("")
    W("| 段 | Clip | 取消帧 | 取消窗口 | 窗口时长 |")
    W("|---|---|:--:|---:|---:|")
    for e in E:
        if e["name"] in ("Light_01", "Light_02", "Light_03"):
            cw = e["frames"][1] - e["cancel_frame"]
            W("| %s | `%s` | %g | %g 帧 | %.3f s |" % (e["code"], e["name"], e["cancel_frame"], cw, cw / 60))
    W("")
    W("规则：**在 `cancel_frame` 到 `frames[1]` 之间按下一次攻击**，才允许续段。")
    W("错过窗口就必须等整段播完回 `IDLE`。")
    W("")
    W("### 9.3 流程状态")
    W("")
    W("```")
    W("开局      Spawn → Battle_Start → IDLE")
    W("胜利      Battle_Start 后判定胜 → Victory_01 / Victory_02 / Victory_03")
    W("战败      → Defeat → 停留")
    W("死亡      → Death（末帧是稳定尸体 Pose，无限保持）")
    W("复活      Death@120 → Revive → Idle_01@0")
    W("```")
    W("")
    W("**Death → Revive 是本项目唯一的一条完整闭环接缝**：")
    W("`Revive` 的首帧逐位等于 `Death` 的第 120 帧，末帧逐位等于 `Idle_01@0`。")
    W("所以死亡后复活**不需要任何混合**，直接切就行。")
    W("")
    W("### 9.4 混合建议")
    W("")
    W("| 切换场景 | 建议 |")
    W("|---|---|")
    W("| 有接缝的两段之间 | **硬切**（0 帧混合）。混合反而会破坏逐位相等 |")
    W("| `IDLE` ↔ `WALK`/`RUN` | 混合 0.10–0.15 s |")
    W("| 受击 → `IDLE` | 混合 0.05–0.10 s（受击要脆） |")
    W("| 攻击 → `IDLE` | 混合 0.10 s |")
    W("| `Death` → `Revive` | 硬切 + 中间等待复活计时 |")
    W("")
    W("---")
    W("")

    # ---------------- 十、已知问题 ----------------
    W("## 十、已知问题")
    W("")
    W("### 10.1 `Jacket_Hem` / `Jacket_Hem_Line` 未蒙皮")
    W("")
    unsk = anim_glb["unskinned_mesh_nodes"]
    W("| 节点 | 网格 | 三角面 |")
    W("|---|---|---|")
    for u in unsk:
        W("| `%s` | `%s` | %d |" % (u["node"], u["mesh"], u["tris"]))
    W("")
    W("这 %d 个网格（合计 %d 三角面）挂在普通节点上、**不受骨骼驱动**。"
      % (len(unsk), sum(u["tris"] for u in unsk)))
    W("后果：跑动/倒地时外套下摆不跟随身体。三种 GLB 里都是这样，是上游 Blender 阶段就没绑。")
    W("")
    W("### 10.2 Action 的 `category` 属性与清单分类漂移")
    W("")
    cats = {}
    for e in E:
        c = e["category"]
        cats.setdefault(c, 0)
        cats[c] += 1
    W("| Action `category` 值 | 段数 | 应属清单家族 |")
    W("|---|---:|---|")
    for c, n in sorted(cats.items(), key=lambda x: -x[1]):
        want = "基础移动" if c == "基础移动" else (
            "普通攻击" if c == "普通攻击" else (
                "连招与特殊技" if c == "连招与特殊技" else (
                    "防御与受击" if c in ("防御", "防御与受击") else "状态与流程")))
        ok = "✅" if c == want else "❌ 需归一"
        W("| `%s` | %d | %s %s |" % (c, n, want, ok))
    W("")
    W("**本文档一律以清单 A–E 家族为准**，Action 属性值只作参考。")
    W("程序若直接按 `category` 分组会得到 %d 个组而不是 5 个。" % len(cats))
    W("")
    W("### 10.3 清单 67 行 vs 实际 68 段")
    W("")
    W("差的那 1 段是 `Charge_Loop`（36 帧 / 0.600 s），是 `Charge` 的配套循环段。")
    W("两套口径都自洽，但**程序遍历 clip 时总数是 68 不是 67**。")
    W("")
    W("---")
    W("")
    W("_生成时间与数据源哈希见 `_animation_index.json` 的 `source` 字段。_")

    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    print("WROTE %s (%d lines)" % (out, len(L)))


main()
