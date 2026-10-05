#!/usr/bin/env bash
# E11 反向验证驱动：对每一组旋钮跑一遍专属门禁。
# ★ 判据（比 E10 更严）：每一组必须让**指定的那一条** `*_ok` 判据见红
#   （E10 只要求 "failed ∪ non_ok 非空"，而本支 `rvw_common_ground_contact_raw`
#    恒为 False 且**不以 `_ok` 结尾**，所以宽松判据会永远通过 ⟹ 必须指名道姓）。
#   核对由 `_rv_e11_check.py` 完成。
# 用法：bash _rv_e11.sh <并发数>
set -u
cd "I:/工作项目/BIGMANFIGHT/角色资产/美术资产/bigman_v001/animations"
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
PAR="${1:-4}"

cat > _rv_e11_pairs.txt <<'EOF'
SEAM_ZERO|E11_TP_SEAM_ZERO=1|rvw_seam_in_ok
ENDZERO|E11_TP_ENDZERO=1|rvw_seam_out_ok
NORIGOR|E11_TP_NORIGOR=1|rvw_rigor_break_ok
NOKNEEL|E11_TP_NOKNEEL=1|rvw_halfkneel_ok
NOLIFT|E11_TP_NOLIFT=1|rvw_phase_c_rise_ok
NOPLATEAU|E11_TP_NOPLATEAU=1|rvw_plateau_ok
LIMBJUMP|E11_TP_LIMBJUMP=1|rvw_limb_step_ok
KNEEPLUNGE|E11_TP_KNEEPLUNGE=1|rvw_knee_path_ok
SINK|E11_TP_SINK=1|rvw_no_penetration_ok
SLIDE|E11_TP_SLIDE=1|rvw_foot_slide_ok
EOF

run_one() {
    local line="$1"
    local name="${line%%|*}"
    local rest="${line#*|}"
    local envs="${rest%%|*}"
    env $envs SKIP_RENDER=1 "$BL" --background --factory-startup \
        --python anim_revive.py > "_e11_rv_${name}.log" 2>&1
    echo "DONE ${name}"
}
export -f run_one
export BL

grep -v '^[[:space:]]*$' _rv_e11_pairs.txt | xargs -P "$PAR" -I{} bash -c 'run_one "$@"' _ {}
echo "ALL DONE"
