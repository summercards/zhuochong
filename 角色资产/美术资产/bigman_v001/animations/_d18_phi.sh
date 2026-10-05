#!/usr/bin/env bash
# D18：臂骨滚转 φ 的逐帧真值
set -u
cd "$(dirname "$0")"
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"

env PYTHONHASHSEED=0 SKIP_RENDER=1 \
  D18_PHIDBG=1 D18_PHIDBG_F0=10 D18_PHIDBG_F1=28 \
  D18_EULERDBG=1 \
  D18_EULERDBG_NAMES=forearm.R,upperarm.R,hand.R,forearm.L,upperarm.L,hand.L \
  D18_EULERDBG_F0=10 D18_EULERDBG_F1=28 \
  "$BL" --background --factory-startup --python anim_getup_b.py \
  > "_d18_phi.log" 2>&1

echo "=== PHI ==="
grep -o 'D18_PHI .*' "_d18_phi.log" | \
  python -c "
import sys,json
for line in sys.stdin:
    d=json.loads(line.replace('D18_PHI ',''))
    p=d['phi']
    print('f%02d scope=%.2f mix=%.3f  '%(d['f'],d['scope'],d['mix']) + '  '.join('%s=%+7.2f'%(k,v) for k,v in sorted(p.items())))
"
echo "=== EUL ==="
grep -o 'D18_EUL .*' "_d18_phi.log" | \
  python -c "
import sys,json
for line in sys.stdin:
    d=json.loads(line.replace('D18_EUL ',''))
    out='f%02d'%d['f']
    for k,v in d.items():
        if k=='f': continue
        out+='  %s st=%s dw=%s w=%s'%(k,v['step'],v.get('dw'),v.get('wdir'))
    print(out)
"
echo "=== DONE ==="
