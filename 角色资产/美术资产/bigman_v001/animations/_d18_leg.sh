#!/usr/bin/env bash
cd "I:/工作项目/BIGMANFIGHT/角色资产/美术资产/bigman_v001/animations" || exit 1
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
PY="C:/Users/zhuangmenghong/.workbuddy/binaries/python/versions/3.13.12/python.exe"
run () {
  local tag="$1"; shift
  env PYTHONHASHSEED=0 SKIP_RENDER=1 D18_ROLL_TRANSPORT=0 D18_ROLLWIN_OFF= \
      D18_LEGROLL_MAX=40 D18_FOOT_PIN_BLEND=8 \
      D18_TOTAL=37 D18_PLANT=7 D18_CHEST_UP=10 D18_HAND_OFF=18 D18_TUCK=20 \
      D18_FOOT_SET=27 D18_RISE_MID=31 D18_STAND=35 D18_ARM_MIX_FROM=21 \
      D18_ARM_ANCHORS="17,19,26,35" D18_ANCHOR_SLERP_UNTIL=19 \
      "$@" \
      "$BL" --background --factory-startup --python probe_d18_gate_samples.py \
      > "_d18_leg_$tag.log" 2>&1
  printf "== %-10s " "$tag"
  grep -o '"max_frame_step_deg": [0-9.]*, "max_frame_step_at": \[[0-9]*, "[A-Za-z._0-9]*"\]' "_d18_leg_$tag.log" | tail -1
  "$PY" - "_d18_gate_samples.json" <<'PY'
import json,sys
d=json.load(open(sys.argv[1],encoding="utf-8"))
rows=[]
for i in range(1,len(d)):
    a=d[i-1]["euler"]; b=d[i]["euler"]
    for n in sorted(set(a)|set(b)):
        s=max(abs(x-y) for x,y in zip(a.get(n,[0,0,0]),b.get(n,[0,0,0])))
        if s>23.0: rows.append((s,d[i]["f"],n))
rows.sort(reverse=True)
print("      " + "  ".join("%s@%d=%.1f"%(n,f,s) for s,f,n in rows[:5]))
PY
}
run base       D18_ANKLE_LIFT=1.0
run lift07     D18_ANKLE_LIFT=0.7
run lift05     D18_ANKLE_LIFT=0.5
run lift03     D18_ANKLE_LIFT=0.3
run clr02      D18_ANKLE_CLEAR=0.02
run clr05mix04 D18_ANKLE_CLEAR_MIX=0.4
run lift07clr04 D18_ANKLE_LIFT=0.7 D18_ANKLE_CLEAR_MIX=0.4
run tz16       D18_TUCK_ANKLE_Z=0.16
run tz26       D18_TUCK_ANKLE_Z=0.26
run tuck21     D18_TUCK=21
run tuck19     D18_TUCK=19
run tdy20      D18_TUCK_ANKLE_DY=0.20
run ckeys      D18_ANKLE_CLEAR_KEYS="0:0.0,20:0.0,22:0.15,25:0.62,26:0.86,27:0.0,37:0.0"
run fp6        D18_FOOT_PIN_BLEND=6
run fp10       D18_FOOT_PIN_BLEND=10
run heel26     D18_HEEL_PEAK=2.60
