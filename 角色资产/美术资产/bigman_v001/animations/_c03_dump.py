"""从 C03 门禁日志里抽关键指标（不做任何判定，只读）。用法: python _c03_dump.py _c03_gateNN.log"""
import json
import re
import sys

KEYS = [
    "failed", "non_ok_bools",
    "return_tail", "return_tail_bones", "decel_smooth_ok", "no_snap_stop_ok",
    "pivot_drift_mm", "stance_pivot_ok",
    "z_drop_world_mm", "z_drop_min_mm", "z_drop_ratio_vs_combo",
    "fwd_ratio_net", "knockdown_fwd_ratio_ok", "knockdown_z_ok", "knockdown_down_ok",
    "leg_reach_max_ratio", "ik_reach_ok",
    "world_step_max_deg", "world_step_max_at", "world_step_ok",
    "local_step_max_deg", "local_step_max_at",
    "stance_sole_ok", "ground_min_mm", "ground_contact_ok",
    "pelvis_z_min_mm", "pelvis_z_min_frame", "pelvis_z_sink_mm", "pelvis_sink_ok",
    "always_supported_ok", "unsupported_frames",
    "swing_airborne_ok", "air_sole_min_mm",
    "seam_start_ok", "seam_start_delta", "seam_end_ok", "seam_end_pose_delta",
    "hitstop_present_ok", "hitstop_frames", "hitstop_keeps_momentum_ok",
    "power_chain_ok", "no_teleport", "low_bad_frames",
]


def main():
    path = sys.argv[1]
    text = open(path, encoding="utf-8", errors="replace").read()
    found = None
    for line in text.splitlines():
        if line.startswith("C03_REPORT "):
            found = json.loads(line[len("C03_REPORT "):])
    if found is None:
        print("!! 日志里没有 C03_REPORT（脚本中途失败？）")
        for line in text.splitlines():
            if "Error" in line or "Traceback" in line:
                print("   ", line)
        return 1
    for key in KEYS:
        if key in found:
            print("%-28s = %s" % (key, json.dumps(found[key], ensure_ascii=False)))
    print("-" * 60)
    fl = found.get("failed") or []
    print("门禁:", "🟢 ALL GREEN" if not fl else "🔴 " + ", ".join(fl))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
