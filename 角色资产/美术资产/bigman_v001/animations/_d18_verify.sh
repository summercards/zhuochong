#!/usr/bin/env bash
cd "I:/工作项目/BIGMANFIGHT/角色资产/美术资产/bigman_v001/animations" || exit 1
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
BASE="D18_OUT_TOTAL=40 D18_TOTAL=40 D18_LEGS_DOWN=4 D18_PLANT=7 D18_CHEST_UP=11 \
D18_HAND_OFF=20 D18_TUCK=22 D18_FOOT_SET=30 D18_RISE_MID=34 D18_STAND=38 \
D18_ARM_MIX_FROM=22 D18_ARM_ANCHORS=19,21,29,38 D18_ANCHOR_SLERP_UNTIL=20 \
D18_ROLL_TRANSPORT=0 D18_ROLLWIN_OFF= D18_LEGROLL_MAX=40 D18_FOOT_PIN_BLEND=8"
run () {
  local tag="$1"; shift
  env PYTHONHASHSEED=0 SKIP_RENDER=1 $BASE "$@" \
      "$BL" --background --factory-startup --python probe_d18_gate_samples.py \
      > "_d18_rv_$tag.log" 2>&1
  printf "== %-14s " "$tag"
  grep -o '"failed": \[[^]]*\]\|"non_ok_bools": \[[^]]*\]\|"max_frame_step_deg": [0-9.]*' "_d18_rv_$tag.log" | tr '\n' ' '
  echo
  python - "$tag" <<'PY'
import json,sys
tag=sys.argv[1]
for line in open("_d18_rv_%s.log"%tag,encoding="utf-8",errors="replace"):
    if line.startswith("D18_REPORT "):
        d=json.loads(line[11:])
        keys=["seam_in_ok","chest_rise_ok","foot_takeover_ok","hand_off_ok",
              "end_matches_idle_ok","rise_monotone_ok","no_snap_stop_ok","end_vz_zero_ok",
              "knee_unfold_start_ok","no_foot_slide_ok","sole_ground_ok","rise_reach_ok"]
        print("      " + "  ".join("%s=%s"%(k,d.get(k)) for k in keys if d.get(k) is False))
        break
PY
}
run repro1
run repro2
run repro3
run rv1  D18_TP_SEAM_ZERO=1
run rv2  D18_TP_NOPUSH=1
run rv3  D18_TP_NOTUCK=1
run rv4  D18_TP_STICKYHAND=1
run rv5  D18_TP_NOIDLE=1
run rv6  D18_TP_DIP=1
run rv7  D18_TP_ENDZERO=1
run rv8  D18_TP_NOLEGDROP=1
