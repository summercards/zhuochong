#!/usr/bin/env bash
cd "I:/工作项目/BIGMANFIGHT/角色资产/美术资产/bigman_v001/animations" || exit 1
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
PY="C:/Users/zhuangmenghong/.workbuddy/binaries/python/versions/3.13.12/python.exe"
run () {
  local tag="$1"; shift
  env PYTHONHASHSEED=0 SKIP_RENDER=1 D18_ROLL_TRANSPORT=0 D18_ROLLWIN_OFF= \
      D18_LEGROLL_MAX=40 D18_FOOT_PIN_BLEND=8 D18_ARM_MIX_FROM=21 \
      "$@" \
      "$BL" --background --factory-startup --python probe_d18_gate_samples.py \
      > "_d18_st_$tag.log" 2>&1
  printf "== %-12s " "$tag"
  grep -o '"max_frame_step_deg": [0-9.]*, "max_frame_step_at": \[[0-9]*, "[A-Za-z._0-9]*"\]' "_d18_st_$tag.log" | tail -1
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
B="D18_PLANT=7 D18_CHEST_UP=10 D18_HAND_OFF=18 D18_ARM_ANCHORS=17,19,26,35 D18_ANCHOR_SLERP_UNTIL=19"
run T37base $B D18_TOTAL=37 D18_TUCK=20 D18_FOOT_SET=27 D18_RISE_MID=31 D18_STAND=35
B38="D18_PLANT=7 D18_CHEST_UP=10 D18_HAND_OFF=18 D18_ARM_ANCHORS=17,19,27,36 D18_ANCHOR_SLERP_UNTIL=19"
run T38 $B38 D18_TOTAL=38 D18_TUCK=21 D18_FOOT_SET=28 D18_RISE_MID=32 D18_STAND=36
run T38b $B38 D18_TOTAL=38 D18_TUCK=20 D18_FOOT_SET=28 D18_RISE_MID=32 D18_STAND=36
B39="D18_PLANT=7 D18_CHEST_UP=10 D18_HAND_OFF=18 D18_ARM_ANCHORS=17,19,28,37 D18_ANCHOR_SLERP_UNTIL=19"
run T39 $B39 D18_TOTAL=39 D18_TUCK=21 D18_FOOT_SET=29 D18_RISE_MID=33 D18_STAND=37
B40="D18_PLANT=7 D18_CHEST_UP=10 D18_HAND_OFF=18 D18_ARM_ANCHORS=17,19,29,38 D18_ANCHOR_SLERP_UNTIL=19"
run T40 $B40 D18_TOTAL=40 D18_TUCK=22 D18_FOOT_SET=30 D18_RISE_MID=34 D18_STAND=38
run T40b $B40 D18_TOTAL=40 D18_TUCK=21 D18_FOOT_SET=30 D18_RISE_MID=34 D18_STAND=38
run T38hf19 $B38 D18_TOTAL=38 D18_HAND_OFF=19 D18_ARM_ANCHORS=18,20,27,36 D18_TUCK=21 D18_FOOT_SET=28 D18_RISE_MID=32 D18_STAND=36
