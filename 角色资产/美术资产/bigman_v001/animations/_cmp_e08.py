#!/usr/bin/env python
"""对比多份 E08 门禁日志的关键读数（只读，不改任何东西）。"""
import json
import sys

FRAMES = ["0", "6", "12", "18", "24", "28", "32", "36", "40", "44", "48",
          "60", "80", "92", "110", "120"]

KEYS = ["v3_amp_diameter_mm", "v3_amp_diameter_at", "v3_amp_path_len_mm",
        "v3_stroke_oneway_mm", "v3_stroke_count", "v3_stroke_extrema",
        "v3_stroke_sym_worst_mm", "v3_stroke_sym_at",
        "v3_hand_gap_min_mm", "v3_hand_gap_min_at", "v3_hand_gap_clasp_mm",
        "v3_clasp_z_min_mm", "v3_clasp_z_max_mm",
        "v3_firstbeat_mm", "v3_hitstop_longest_frozen",
        "v3_matrix_step_deg_max", "v3_matrix_step_at",
        "v3_euler_step_deg_max", "max_frame_step_deg",
        "v3_pierce_beyond_limit_worst", "v3_pierce_beyond_limit_worst_at",
        "v3_pierce_nothumb_deepest_mm", "v3_pierce_nothumb_deepest_at",
        "v3_x_hint_margin", "v3_hero_worst_step_deg",
        "arm_reach_ratio_max", "clip_max_mm"]


def load(path):
    text = open(path, encoding="utf-8", errors="replace").read()
    idx = text.find("E08_REPORT ")
    if idx < 0:
        return None
    start = idx + len("E08_REPORT ")
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start:i + 1])
    return None


def main(paths):
    rows = []
    for p in paths:
        d = load(p)
        if d is None:
            print("=== %s\n   NO REPORT" % p)
            continue
        rows.append((p, d))
    for p, d in rows:
        print("=== %s" % p)
        print("   failed=%s" % d.get("failed"))
        print("   non_ok=%s" % d.get("non_ok_bools"))
        for k in KEYS:
            print("   %-36s %s" % (k, d.get(k)))
        pd = d.get("v3_pierce_detail", {})
        print("   --- hand-vs-torso per-frame (L/R: inside_nt / beyond / deep_nt)")
        for fr in FRAMES:
            l = pd.get(fr, {}).get("L", {})
            r = pd.get(fr, {}).get("R", {})
            print("     f=%-4s L %-4s %-3s %-8s | R %-4s %-3s %s"
                  % (fr, l.get("inside_nothumb"), l.get("beyond_limit"),
                     l.get("deepest_nothumb_mm"),
                     r.get("inside_nothumb"), r.get("beyond_limit"),
                     r.get("deepest_nothumb_mm")))
        print("   station_beyond=%s station_nt=%s"
              % (d.get("v3_station_beyond_limit"),
                 d.get("v3_station_nothumb_count")))


if __name__ == "__main__":
    main(sys.argv[1:])
