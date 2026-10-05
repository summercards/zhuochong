#!/usr/bin/env bash
# E10 反向验证驱动：对每一组旋钮跑一遍专属门禁，要求 failed ∪ non_ok 非空
# （`dth_common_ground_contact_raw` 是本支**显式置空**的继承口径，不算响应）。
# 用法：bash _rv_e10.sh <并发数>
set -u
cd "I:/工作项目/BIGMANFIGHT/角色资产/美术资产/bigman_v001/animations"
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
PAR="${1:-5}"

cat > _rv_e10_pairs.txt <<'EOF'
SEAM_ZERO|E10_TP_SEAM_ZERO=1
NOFALL|E10_TP_NOFALL=1
MICROMOTION|E10_TP_MICROMOTION=1
NOHITSTOP|E10_TP_NOHITSTOP=1
SINK|E10_TP_SINK=1
KNEEPLUNGE|E10_TP_KNEEPLUNGE=1
LIMBJUMP|E10_TP_LIMBJUMP=1
KNEEL|E10_TP_KNEEL=1
SNAP|E10_TP_SNAP=1
PRONE|E10_TP_PRONE=1
EOF

run_one() {
    local line="$1"
    local name="${line%%|*}"
    local envs="${line#*|}"
    env $envs SKIP_RENDER=1 "$BL" --background --factory-startup \
        --python anim_death.py > "_e10_rv_${name}.log" 2>&1
    echo "DONE ${name}"
}
export -f run_one
export BL

grep -v '^[[:space:]]*$' _rv_e10_pairs.txt | xargs -P "$PAR" -I{} bash -c 'run_one "$@"' _ {}
echo "ALL DONE"
