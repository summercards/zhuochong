#!/usr/bin/env python
"""对比多份 E07 门禁日志的关键读数（只读，不改任何东西）。"""
import json
import re
import sys

FRAMES = ["0", "3", "6", "9", "12", "93", "96", "99", "102", "105", "108", "120"]


def load(path):
    text = open(path, encoding="utf-8", errors="replace").read()
    idx = text.find("E07_REPORT ")
    if idx < 0:
        return None
    start = idx + len("E07_REPORT ")
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
            print("%s: NO REPORT" % p)
            continue
        rows.append((p, d))
    keys = ["v2_matrix_step_deg_max", "v2_matrix_step_at",
            "v2_euler_step_deg_max", "max_frame_step_deg",
            "v2_pierce_beyond_limit_worst", "v2_pierce_beyond_limit_worst_at",
            "v2_pierce_nothumb_deepest_mm", "v2_pierce_nothumb_deepest_at",
            "v2_raise_z_min_mm", "v2_asym_min_mm", "v2_no_contact_min_mm",
            "v2_windup_y_m", "v2_x_hint_margin", "v2_hero_worst_step_deg",
            "arm_reach_ratio_max", "clip_max_mm"]
    for p, d in rows:
        print("=== %s" % p)
        print("   failed=%s" % d.get("failed"))
        for k in keys:
            print("   %-34s %s" % (k, d.get(k)))
        pd = d.get("v2_pierce_detail", {})
        print("   --- R hand per-frame (inside_nt / beyond / deep_nt)")
        for fr in FRAMES:
            r = pd.get(fr, {}).get("R", {})
            print("     f=%-4s inside_nt=%-4s beyond=%-3s deep_nt=%s"
                  % (fr, r.get("inside_nothumb"), r.get("beyond_limit"),
                     r.get("deepest_nothumb_mm")))
        print("   station_beyond=%s station_nt=%s"
              % (d.get("v2_station_beyond_limit"), d.get("v2_station_nothumb_count")))


if __name__ == "__main__":
    main(sys.argv[1:])
