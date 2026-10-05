"""从一次运行的日志里抽出 `C12_REPORT`（或任意 *_REPORT）并挑关键项打印。

用法：  python _show_report.py _c12_run.log [PREFIX]
"""
import json
import sys

path = sys.argv[1]
prefix = sys.argv[2] if len(sys.argv) > 2 else "C12_REPORT"

line = None
with open(path, "r", encoding="utf-8", errors="replace") as handle:
    for raw in handle:
        if raw.startswith(prefix + " "):
            line = raw
if line is None:
    print("NO %s in %s" % (prefix, path))
    sys.exit(1)

data = json.loads(line[len(prefix) + 1:])
print("---- 所有 *_ok 与裸布尔 ----")
for key in sorted(data):
    value = data[key]
    if key.endswith("_ok") or isinstance(value, bool):
        print("  %-34s %s" % (key, value))
print("---- failed / non_ok_bools ----")
print("  failed       =", data.get("failed"))
print("  non_ok_bools =", data.get("non_ok_bools"))
print("---- 关键数值 ----")
keep = ("max_frame_step_deg", "max_frame_step_at", "world_step_max_deg",
        "world_step_max_at", "no_teleport_max_deg", "ground_min_mm",
        "sil_aspect_ratio", "sil_fill_ratio", "sil_shoulder_ratio",
        "antic_sink_mm", "antic_rise_mm", "antic_chest_swing_deg",
        "antic_shoulder_swing_deg", "pose_hold_worst_mm", "pose_hold_worst_at",
        "camera_torso_yaw_deg", "camera_head_yaw_deg", "nofreeze_peak_step_mm",
        "nofreeze_path_outside_mm", "flare_peak_mmps", "plant_L_mm",
        "plant_R_mm", "plant_3d_L_mm", "plant_3d_R_mm", "pz_span_mm",
        "root_span_h_mm", "settle_tail_mm", "settle_last2_mm",
        "end_pose_delta_mm", "leg_reach_worst_ratio", "leg_reach_worst_at",
        "arm_clamp", "us_start_delta_deg", "low_bad_frames")
for key in keep:
    if key in data:
        print("  %-26s %s" % (key, data[key]))
