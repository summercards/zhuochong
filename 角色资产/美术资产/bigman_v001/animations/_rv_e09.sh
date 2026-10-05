#!/usr/bin/env bash
# E09 反向验证驱动：对每一组旋钮跑一遍专属门禁，要求 failed ∪ non_ok 非空。
# 用法：bash _rv_e09.sh <并发数>
set -u
cd "I:/工作项目/BIGMANFIGHT/角色资产/美术资产/bigman_v001/animations"
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
PAR="${1:-4}"

cat > _rv_e09_pairs.txt <<'EOF'
SEAM_ZERO|E09_TP_SEAM_ZERO=1
NO_KNEEL|E09_TP_NOKNEEL=1
NO_FALL|E09_TP_NOFALL=1
NO_BREATH|E09_TP_NOBREATH=1
FOOT_SWAY|E09_TP_FOOTSWAY=1
KNEE_FLOAT|E09_TP_KNEEFLOAT=1
NO_HITSTOP|E09_TP_NOHITSTOP=1
SINK|E09_TP_SINK=1
KNEE_PLUNGE|E09_TP_KNEEPLUNGE=1
LIMB_JUMP|E09_TP_LIMBJUMP=1
EOF

run_one() {
    local line="$1"
    local name="${line%%|*}"
    local envs="${line#*|}"
    env $envs SKIP_RENDER=1 "$BL" --background --factory-startup \
        --python anim_defeat.py > "_e09_rv_${name}.log" 2>&1
    echo "DONE ${name}"
}
export -f run_one
export BL

grep -v '^[[:space:]]*$' _rv_e09_pairs.txt | xargs -P "$PAR" -I{} bash -c 'run_one "$@"' _ {}
echo "ALL DONE"
