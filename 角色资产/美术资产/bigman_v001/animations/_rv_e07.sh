#!/usr/bin/env bash
# E07 反向验证驱动：对每一组旋钮跑一遍专属门禁，要求 failed ∪ non_ok 非空。
# 用法：bash _rv_e07.sh <并发数>
set -u
cd "I:/工作项目/BIGMANFIGHT/角色资产/美术资产/bigman_v001/animations"
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
PAR="${1:-4}"

cat > _rv_e07_pairs.txt <<'EOF'
SEAM_ZERO|E07_TP_SEAM_ZERO=1
LOW_RAISE|E07_TP_LOW_RAISE=1
SYM|E07_TP_SYM=1
CONTACT|E07_TP_CONTACT=1
FRONT_WINDUP|E07_TP_FRONT_WINDUP=1
NO_HITSTOP|E07_TP_NOHITSTOP=1
SLUMP|E07_TP_SLUMP=1
NO_CHIN|E07_TP_NOCHIN=1
TREMBLE|E07_TP_TREMBLE=1
FOOT_SWAY|E07_TP_FOOTSWAY=1
LOOP_BREAK|E07_TP_LOOPBREAK=1
SWING_OFF|E07_DIP_EASE=smooth
GUARD_UNLOCK|E07_GUARD_RIGID=0
EOF

run_one() {
    local line="$1"
    local name="${line%%|*}"
    local envs="${line#*|}"
    env $envs SKIP_RENDER=1 "$BL" --background --factory-startup \
        --python anim_victory_02.py > "_e07_rv_${name}.log" 2>&1
    echo "DONE ${name}"
}
export -f run_one
export BL

grep -v '^[[:space:]]*$' _rv_e07_pairs.txt | xargs -P "$PAR" -I{} bash -c 'run_one "$@"' _ {}
echo "ALL DONE"
