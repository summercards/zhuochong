#!/usr/bin/env bash
# E08 反向验证驱动：对每一组旋钮跑一遍专属门禁，要求 failed ∪ non_ok 非空。
# 用法：bash _rv_e08.sh <并发数>
set -u
cd "I:/工作项目/BIGMANFIGHT/角色资产/美术资产/bigman_v001/animations"
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
PAR="${1:-4}"

cat > _rv_e08_pairs.txt <<'EOF'
SEAM_ZERO|E08_TP_SEAM_ZERO=1
AMP_X2|E08_TP_AMP_X2=1
AMP_ZERO|E08_TP_AMP_ZERO=1
NO_CLASP|E08_TP_NO_CLASP=1
OVERLAP|E08_TP_OVERLAP=1
HIGH|E08_TP_HIGH=1
LOW|E08_TP_LOW=1
STROKE1|E08_TP_STROKE1=1
ASYMM|E08_TP_ASYMM=1
ADDHITSTOP|E08_TP_ADDHITSTOP=1
BIGFIRST|E08_TP_BIGFIRST=1
SLUMP|E08_TP_SLUMP=1
NO_CHIN|E08_TP_NOCHIN=1
TREMBLE|E08_TP_TREMBLE=1
FOOT_SWAY|E08_TP_FOOTSWAY=1
LOOP_BREAK|E08_TP_LOOPBREAK=1
ENVLINEAR|E08_ENV_POW=1.0
EOF

run_one() {
    local line="$1"
    local name="${line%%|*}"
    local envs="${line#*|}"
    env $envs SKIP_RENDER=1 "$BL" --background --factory-startup \
        --python anim_victory_03.py > "_e08_rv_${name}.log" 2>&1
    echo "DONE ${name}"
}
export -f run_one
export BL

grep -v '^[[:space:]]*$' _rv_e08_pairs.txt | xargs -P "$PAR" -I{} bash -c 'run_one "$@"' _ {}
echo "ALL DONE"
