import os
import sys

import bpy


ROOT = os.path.abspath(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import build_character_animations_v9 as build


def run_pose(base, swing, shoulder_lift, elbow_amount):
    pose = build.locomotion_arms(
        base,
        swing,
        swing,
        elbow_amount,
        shoulder_lift=shoulder_lift,
    )
    return build.with_pose(
        pose,
        rotations={
            "pelvis": (-3.0, swing * 0.08, -swing * 0.05),
            "spine": (10.0, swing * 0.12, swing * 0.06),
            "chest": (7.0, swing * 0.18, swing * 0.10),
            "neck": (-5.0, -swing * 0.05, -swing * 0.05),
            "head": (-5.0, -swing * 0.07, -swing * 0.08),
            "thigh.L": (-43.0, 0.0, 0.0),
            "shin.L": (15.0, 0.0, 0.0),
            "foot.L": (14.0, 0.0, 0.0),
            "thigh.R": (30.0, 0.0, 0.0),
            "shin.R": (34.0, 0.0, 0.0),
            "foot.R": (-18.0, 0.0, 0.0),
        },
        locations={"pelvis": (0.0, -0.082, -0.012)},
    )


def hand_y_delta(armature, base, swing, shoulder_lift, elbow_amount):
    build.apply_pose(armature, run_pose(base, swing, shoulder_lift, elbow_amount))
    bpy.context.view_layer.update()
    start_left = float(armature.pose.bones["hand.L"].matrix.translation.y)
    start_right = float(armature.pose.bones["hand.R"].matrix.translation.y)
    build.apply_pose(armature, run_pose(base, -swing, shoulder_lift, elbow_amount))
    bpy.context.view_layer.update()
    half_left = float(armature.pose.bones["hand.L"].matrix.translation.y)
    half_right = float(armature.pose.bones["hand.R"].matrix.translation.y)
    return abs(half_left - start_left), abs(half_right - start_right)


def main():
    blend_path = os.path.join(ROOT, "business_man_tpose_v9.blend")
    bpy.ops.wm.open_mainfile(filepath=blend_path)
    armature = bpy.data.objects[build.ARMATURE_NAME]
    armature.animation_data_clear()
    build.reset_pose(armature)
    base = build.neutral_pose()
    candidates = []
    for shoulder_lift in range(-70, -9, 5):
        for swing in range(60, 121, 10):
            for elbow_amount in (-76.0, -62.0, -48.0):
                left, right = hand_y_delta(
                    armature,
                    base,
                    float(swing),
                    float(shoulder_lift),
                    elbow_amount,
                )
                candidates.append(
                    (
                        min(left, right),
                        left,
                        right,
                        shoulder_lift,
                        swing,
                        elbow_amount,
                    )
                )
    print("RUN_SWING_RANKED")
    lowered_arm_candidates = [
        candidate for candidate in candidates if candidate[3] <= -35
    ]
    for candidate in sorted(lowered_arm_candidates, reverse=True)[:30]:
        print(
            "min=%.6f left=%.6f right=%.6f shoulder=%d swing=%d elbow=%.1f"
            % candidate
        )
    current_left, current_right = hand_y_delta(
        armature,
        base,
        90.0,
        -48.0,
        -62.0,
    )
    print(
        "RUN_SWING_CURRENT min=%.6f left=%.6f right=%.6f"
        % (min(current_left, current_right), current_left, current_right)
    )


if __name__ == "__main__":
    main()
