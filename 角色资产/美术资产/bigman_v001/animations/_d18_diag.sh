#!/usr/bin/env bash
# D18：当前默认配置下的臂链 / 腿链诊断（步长 + 欧拉 + 真实世界旋转）
set -u
cd "$(dirname "$0")"
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"

env PYTHONHASHSEED=0 SKIP_RENDER=1 \
  D18_STEPDBG=1 D18_STEPDBG_THR=19 \
  D18_EULERDBG=1 D18_EULERDBG_DIR=1 \
  D18_EULERDBG_NAMES=forearm.R,hand.R,upperarm.R,forearm.L,hand.L,thigh.L,shin.R \
  D18_EULERDBG_F0=13 D18_EULERDBG_F1=26 \
  "$BL" --background --factory-startup --python anim_getup_b.py \
  > "_d18_diag.log" 2>&1

echo "=== STEP_ALL ==="
grep -o 'D18_STEP_ALL .*' "_d18_diag.log" | head -1 | \
  python -c "import sys,json; d=json.loads(sys.stdin.read().replace('D18_STEP_ALL ','')); [print('%7.3f  f%d->%d  %-12s %s -> %s'%(r[0],r[1],r[2],r[3],r[4],r[5])) for r in d]"
echo "=== EUL ==="
grep -o 'D18_EUL .*' "_d18_diag.log" | \
  python -c "
import sys,json
for line in sys.stdin:
    d=json.loads(line.replace('D18_EUL ',''))
    out='f%02d'%d['f']
    for k,v in d.items():
        if k=='f': continue
        out+='  %s eul%s step=%s dw=%s wdir=%s phi=%s mix=%s'%(k,v['eul'],v['step'],v.get('dw'),v.get('wdir'),v.get('phi'),v.get('mix'))
    print(out)
"
echo "=== DONE ==="
