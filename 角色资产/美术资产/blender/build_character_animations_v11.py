import math
import os
import sys

import bpy
from mathutils import Matrix


ROOT = os.path.abspath(os.path.dirname(__file__))
DEFAULT_BLEND = os.path.join(ROOT, "business_man_tpose_v11.blend")
DEFAULT_GLB = os.path.join(ROOT, "business_man_tpose_v11.glb")
ARMATURE_NAME = "Character_Rig"
FPS = 30

FOUR_FINGERS = ("index", "middle", "ring", "pinky")
LOCATION_BONES = {
    "root",
    "pelvis",
    "upper_lip",
    "lower_lip",
}


def parse_paths():
    if "--" not in sys.argv:
        return DEFAULT_BLEND, DEFAULT_GLB
    values = sys.argv[sys.argv.index("--") + 1 :]
    if len(values) != 2:
        raise ValueError("Expected output Blend and GLB paths after --")
    return tuple(os.path.abspath(value) for value in values)


def d(value):
    return math.radians(float(value))


def merge_pose(rotations, locations):
    return {
        "rotations": {
            bone_name: tuple(float(value) for value in values)
            for bone_name, values in rotations.items()
        },
        "locations": {
            bone_name: tuple(float(value) for value in values)
            for bone_name, values in locations.items()
        },
    }


def neutral_pose():
    rotations = {
        "upper_arm.L": (-70.0, 0.0, -5.0),
        "upper_arm.R": (-70.0, 0.0, 5.0),
        "forearm.L": (-12.0, 0.0, 0.0),
        "forearm.R": (-12.0, 0.0, 0.0),
        "hand.L": (0.0, 0.0, 0.0),
        "hand.R": (0.0, 0.0, 0.0),
        "shin.L": (3.0, 0.0, 0.0),
        "shin.R": (3.0, 0.0, 0.0),
        "foot.L": (-1.0, 0.0, 0.0),
        "foot.R": (-1.0, 0.0, 0.0),
    }
    for side in ("L", "R"):
        for digit_name in FOUR_FINGERS:
            rotations["finger_%s_01.%s" % (digit_name, side)] = (-18.0, 0.0, 0.0)
            rotations["finger_%s_02.%s" % (digit_name, side)] = (-24.0, 0.0, 0.0)
            rotations["finger_%s_03.%s" % (digit_name, side)] = (-12.0, 0.0, 0.0)
        thumb_sign = 1.0 if side == "L" else -1.0
        rotations["thumb_01." + side] = (0.0, 0.0, 10.0 * thumb_sign)
        rotations["thumb_02." + side] = (0.0, 0.0, 14.0 * thumb_sign)
        rotations["thumb_03." + side] = (0.0, 0.0, 8.0 * thumb_sign)
    locations = {
        "root": (0.0, 0.0, 0.0),
        "pelvis": (0.0, 0.0, 0.0),
        "upper_lip": (0.0, 0.0, 0.0),
        "lower_lip": (0.0, 0.0, 0.0),
    }
    return merge_pose(rotations, locations)


def with_rotations(base, rotations):
    result = {
        "rotations": dict(base["rotations"]),
        "locations": dict(base["locations"]),
    }
    result["rotations"].update(rotations)
    return result


def with_locations(base, locations):
    result = {
        "rotations": dict(base["rotations"]),
        "locations": dict(base["locations"]),
    }
    result["locations"].update(locations)
    return result


def with_pose(base, rotations=None, locations=None):
    result = with_rotations(base, rotations or {})
    if locations:
        result = with_locations(result, locations)
    return result


def fist_pose(base, side, amount=1.0):
    rotations = {}
    for digit_name in FOUR_FINGERS:
        rotations["finger_%s_01.%s" % (digit_name, side)] = (
            -82.0 * amount,
            0.0,
            0.0,
        )
        rotations["finger_%s_02.%s" % (digit_name, side)] = (
            -88.0 * amount,
            0.0,
            0.0,
        )
        rotations["finger_%s_03.%s" % (digit_name, side)] = (
            -58.0 * amount,
            0.0,
            0.0,
        )
    thumb_sign = 1.0 if side == "L" else -1.0
    rotations["thumb_01." + side] = (0.0, 0.0, 48.0 * thumb_sign * amount)
    rotations["thumb_02." + side] = (0.0, 0.0, 52.0 * thumb_sign * amount)
    rotations["thumb_03." + side] = (0.0, 0.0, 34.0 * thumb_sign * amount)
    return with_rotations(base, rotations)


def relaxed_hand_pose(base, side, curl=1.0):
    rotations = {}
    for digit_name in FOUR_FINGERS:
        rotations["finger_%s_01.%s" % (digit_name, side)] = (-26.0 * curl, 0.0, 0.0)
        rotations["finger_%s_02.%s" % (digit_name, side)] = (-36.0 * curl, 0.0, 0.0)
        rotations["finger_%s_03.%s" % (digit_name, side)] = (-20.0 * curl, 0.0, 0.0)
    thumb_sign = 1.0 if side == "L" else -1.0
    rotations["thumb_01." + side] = (0.0, 0.0, 16.0 * thumb_sign * curl)
    rotations["thumb_02." + side] = (0.0, 0.0, 22.0 * thumb_sign * curl)
    rotations["thumb_03." + side] = (0.0, 0.0, 14.0 * thumb_sign * curl)
    return with_rotations(base, rotations)


def open_hand_pose(base, side, spread=1.0):
    rotations = {}
    spread_sign = 1.0 if side == "L" else -1.0
    for index, digit_name in enumerate(FOUR_FINGERS):
        rotations["finger_%s_01.%s" % (digit_name, side)] = (-2.0, 0.0, 0.0)
        rotations["finger_%s_02.%s" % (digit_name, side)] = (-3.0, 0.0, 0.0)
        rotations["finger_%s_03.%s" % (digit_name, side)] = (-2.0, 0.0, 0.0)
        rotations["finger_%s_01.%s" % (digit_name, side)] = (
            -2.0,
            0.0,
            spread_sign * spread * (index - 1.5) * 2.4,
        )
    rotations["thumb_01." + side] = (0.0, 0.0, 4.0 * spread_sign * spread)
    rotations["thumb_02." + side] = (0.0, 0.0, 5.0 * spread_sign * spread)
    rotations["thumb_03." + side] = (0.0, 0.0, 3.0 * spread_sign * spread)
    return with_rotations(base, rotations)


def point_hand_pose(base, side):
    pose = fist_pose(base, side, 0.92)
    rotations = {
        "finger_index_01." + side: (-4.0, 0.0, 0.0),
        "finger_index_02." + side: (-3.0, 0.0, 0.0),
        "finger_index_03." + side: (-2.0, 0.0, 0.0),
    }
    return with_rotations(pose, rotations)


def locomotion_arms(base, left_swing, right_swing, elbow_amount, shoulder_lift=-58.0):
    return with_rotations(
        base,
        {
            "upper_arm.L": (shoulder_lift, 0.0, left_swing),
            "upper_arm.R": (shoulder_lift, 0.0, right_swing),
            "forearm.L": (elbow_amount, 0.0, 0.0),
            "forearm.R": (elbow_amount, 0.0, 0.0),
        },
    )


def crouch_pose(base, depth=1.0, body_bob=0.0):
    return with_pose(
        base,
        rotations={
            "pelvis": (-4.0 * depth, 0.0, 0.0),
            "spine": (8.0 * depth, 0.0, 0.0),
            "chest": (5.0 * depth, 0.0, 0.0),
            "neck": (-4.0 * depth, 0.0, 0.0),
            "head": (-5.0 * depth, 0.0, 0.0),
            "thigh.L": (-38.0 * depth, 0.0, 0.0),
            "thigh.R": (-38.0 * depth, 0.0, 0.0),
            "shin.L": (70.0 * depth, 0.0, 0.0),
            "shin.R": (70.0 * depth, 0.0, 0.0),
            "foot.L": (-24.0 * depth, 0.0, 0.0),
            "foot.R": (-24.0 * depth, 0.0, 0.0),
            "upper_arm.L": (-58.0, 0.0, -22.0),
            "upper_arm.R": (-58.0, 0.0, 22.0),
            "forearm.L": (-42.0, 0.0, 0.0),
            "forearm.R": (-42.0, 0.0, 0.0),
        },
        locations={"pelvis": (0.0, -0.150 * depth + body_bob, 0.015 * depth)},
    )


def idle_frames():
    base = neutral_pose()
    frames = []
    values = (
        (0, 0.000, 0.0, 0.0, 0.0, 0.0),
        (15, 0.006, -1.2, 0.6, -0.5, 1.5),
        (30, 0.002, 0.3, -0.4, 0.5, -1.0),
        (45, 0.008, -1.0, 0.4, -0.4, 1.0),
        (60, 0.000, 0.0, 0.0, 0.0, 0.0),
    )
    for frame, lift, chest_x, neck_x, head_x, sway in values:
        pose = with_pose(
            base,
            rotations={
                "pelvis": (0.0, 0.0, sway * 0.25),
                "spine": (chest_x * 0.35, 0.0, sway * 0.20),
                "chest": (chest_x, 0.0, sway * 0.25),
                "neck": (neck_x, 0.0, -sway * 0.15),
                "head": (head_x, 0.0, -sway * 0.25),
                "upper_arm.L": (-70.0 + chest_x * 0.3, 0.0, -5.0 + sway),
                "upper_arm.R": (-70.0 + chest_x * 0.3, 0.0, 5.0 + sway),
                "forearm.L": (-12.0 - sway * 0.5, 0.0, 0.0),
                "forearm.R": (-12.0 + sway * 0.5, 0.0, 0.0),
            },
            locations={"pelvis": (0.0, lift, 0.0)},
        )
        frames.append((frame, pose))
    return frames


def walk_frames():
    base = neutral_pose()
    specs = (
        (0, -27.0, 6.0, 4.0, 21.0, 14.0, -7.0, 15.0, 26.0, 0.008, 2.5, -4.0, 1.5),
        (8, -5.0, 28.0, 4.0, -2.0, 41.0, -10.0, 1.0, 1.0, 0.071, 0.0, 0.0, -0.5),
        (16, 21.0, 14.0, -7.0, -27.0, 6.0, 4.0, -1.0, 26.0, 0.008, -2.5, 4.0, -1.5),
        (24, -2.0, 41.0, -10.0, -5.0, 28.0, 4.0, 26.0, 1.0, 0.031, 0.0, 0.0, 0.5),
    )
    frames = []
    for (
        frame,
        thigh_l,
        shin_l,
        foot_l,
        thigh_r,
        shin_r,
        foot_r,
        left_swing,
        right_swing,
        pelvis_lift,
        pelvis_yaw,
        chest_yaw,
        chest_roll,
    ) in specs:
        pose = locomotion_arms(base, left_swing, right_swing, -22.0)
        pose = with_pose(
            pose,
            rotations={
                "pelvis": (-1.0, pelvis_yaw, chest_roll),
                "spine": (2.0, chest_yaw * 0.25, -chest_roll * 0.4),
                "chest": (1.0, chest_yaw, -chest_roll),
                "neck": (-0.5, -chest_yaw * 0.25, chest_roll * 0.4),
                "head": (-0.5, -chest_yaw * 0.35, chest_roll * 0.5),
                "thigh.L": (thigh_l, 0.0, 0.0),
                "shin.L": (shin_l, 0.0, 0.0),
                "foot.L": (foot_l, 0.0, 0.0),
                "thigh.R": (thigh_r, 0.0, 0.0),
                "shin.R": (shin_r, 0.0, 0.0),
                "foot.R": (foot_r, 0.0, 0.0),
            },
            locations={"pelvis": (0.0, pelvis_lift, 0.0)},
        )
        frames.append((frame, pose))
    frames.append((32, frames[0][1]))
    return frames


def run_frames():
    base = neutral_pose()
    specs = (
        (0, -43.0, 15.0, 14.0, 30.0, 34.0, -18.0, 90.0, 90.0, -0.082),
        (6, -13.0, 62.0, 8.0, -11.0, 54.0, -8.0, 20.0, 20.0, 0.055),
        (12, 30.0, 34.0, -18.0, -43.0, 15.0, 14.0, -90.0, -90.0, -0.082),
        (18, -11.0, 54.0, -8.0, -13.0, 62.0, 8.0, -20.0, -20.0, 0.055),
    )
    frames = []
    for (
        frame,
        thigh_l,
        shin_l,
        foot_l,
        thigh_r,
        shin_r,
        foot_r,
        left_swing,
        right_swing,
        pelvis_lift,
    ) in specs:
        pose = locomotion_arms(
            base,
            left_swing,
            right_swing,
            -62.0,
            shoulder_lift=-42.0,
        )
        pose = with_pose(
            pose,
            rotations={
                "pelvis": (-3.0, left_swing * 0.08, -right_swing * 0.05),
                "spine": (10.0, left_swing * 0.12, right_swing * 0.06),
                "chest": (7.0, left_swing * 0.18, right_swing * 0.10),
                "neck": (-5.0, -left_swing * 0.05, -right_swing * 0.05),
                "head": (-5.0, -left_swing * 0.07, -right_swing * 0.08),
                "thigh.L": (thigh_l, 0.0, 0.0),
                "shin.L": (shin_l, 0.0, 0.0),
                "foot.L": (foot_l, 0.0, 0.0),
                "thigh.R": (thigh_r, 0.0, 0.0),
                "shin.R": (shin_r, 0.0, 0.0),
                "foot.R": (foot_r, 0.0, 0.0),
            },
            locations={"pelvis": (0.0, pelvis_lift, -0.012)},
        )
        frames.append((frame, pose))
    frames.append((24, frames[0][1]))
    return frames


def talk_frames():
    base = neutral_pose()
    values = (
        (0, 0.0, 0.000, 0.000, 0.0, 0.0, -2.0),
        (8, 10.0, 0.003, 0.007, 4.0, 2.0, 6.0),
        (16, 3.0, 0.001, 0.002, -3.0, -1.0, -3.0),
        (24, 15.0, 0.005, 0.010, 5.0, 3.0, 8.0),
        (32, 2.0, 0.000, 0.001, -2.0, -2.0, -5.0),
        (40, 11.0, 0.004, 0.008, 3.0, 1.0, 5.0),
        (48, 5.0, 0.002, 0.003, -4.0, -1.0, -2.0),
        (60, 0.0, 0.000, 0.000, 0.0, 0.0, -2.0),
    )
    frames = []
    for frame, jaw, upper_lip, lower_lip, eye_x, head_x, gesture in values:
        pose = with_pose(
            base,
            rotations={
                "jaw": (jaw, 0.0, 0.0),
                "upper_lip": (jaw * 0.08, 0.0, 0.0),
                "lower_lip": (-jaw * 0.05, 0.0, 0.0),
                "glasses": (jaw * 0.06, 0.0, gesture * 0.10),
                "eye.L": (0.0, 0.0, eye_x),
                "eye.R": (0.0, 0.0, eye_x),
                "spine": (1.0, gesture * 0.08, gesture * 0.08),
                "chest": (-1.0, gesture * 0.16, gesture * 0.12),
                "neck": (head_x * 0.25, -gesture * 0.12, -gesture * 0.12),
                "head": (head_x, -gesture * 0.18, -gesture * 0.18),
                "upper_arm.R": (-63.0, 0.0, 5.0 + max(0.0, gesture)),
                "forearm.R": (-20.0 - max(0.0, gesture) * 1.8, 0.0, 0.0),
                "hand.R": (0.0, gesture * 0.8, 0.0),
            },
            locations={
                "upper_lip": (0.0, upper_lip, 0.0),
                "lower_lip": (0.0, lower_lip, 0.0),
                "pelvis": (0.0, 0.004 * math.sin(math.radians(frame * 12.0)), 0.0),
            },
        )
        frames.append((frame, pose))
    return frames


def attack_frames():
    base = neutral_pose()
    guard = with_rotations(
        base,
        {
            "upper_arm.L": (-50.0, 0.0, -34.0),
            "forearm.L": (-64.0, 0.0, 0.0),
            "hand.L": (-10.0, 0.0, 0.0),
        },
    )
    guard = fist_pose(guard, "L", 0.9)
    guard = fist_pose(guard, "R", 0.95)
    frames = []
    frames.append((0, guard))

    windup = with_pose(
        guard,
        rotations={
            "pelvis": (0.0, -8.0, 0.0),
            "spine": (-3.0, -10.0, 0.0),
            "chest": (-4.0, -17.0, 0.0),
            "neck": (2.0, 8.0, 0.0),
            "head": (3.0, 12.0, 0.0),
            "upper_arm.R": (-42.0, 0.0, -24.0),
            "forearm.R": (-74.0, 0.0, 0.0),
            "upper_arm.L": (-48.0, 0.0, -26.0),
            "forearm.L": (-50.0, 0.0, 0.0),
        },
        locations={"pelvis": (0.0, -0.018, -0.012)},
    )
    frames.append((6, windup))

    strike = with_pose(
        guard,
        rotations={
            "pelvis": (2.0, 9.0, 0.0),
            "spine": (5.0, 13.0, 0.0),
            "chest": (6.0, 21.0, 0.0),
            "neck": (-3.0, -10.0, 0.0),
            "head": (-4.0, -14.0, 0.0),
            "upper_arm.R": (-18.0, 0.0, 76.0),
            "forearm.R": (-6.0, 0.0, 4.0),
            "hand.R": (0.0, 0.0, 0.0),
            "upper_arm.L": (-53.0, 0.0, -38.0),
            "forearm.L": (-70.0, 0.0, 0.0),
        },
        locations={"pelvis": (0.0, 0.012, 0.035)},
    )
    frames.append((11, strike))
    frames.append((15, strike))
    frames.append((24, guard))
    return frames


def jump_frames():
    base = neutral_pose()
    frames = []
    frames.append((0, crouch_pose(base, 0.75)))

    launch = with_pose(
        base,
        rotations={
            "pelvis": (-2.0, 0.0, 0.0),
            "spine": (8.0, 0.0, 0.0),
            "chest": (5.0, 0.0, 0.0),
            "head": (-4.0, 0.0, 0.0),
            "thigh.L": (-7.0, 0.0, 0.0),
            "thigh.R": (-7.0, 0.0, 0.0),
            "shin.L": (10.0, 0.0, 0.0),
            "shin.R": (10.0, 0.0, 0.0),
            "foot.L": (18.0, 0.0, 0.0),
            "foot.R": (18.0, 0.0, 0.0),
            "upper_arm.L": (-28.0, 0.0, -24.0),
            "upper_arm.R": (-28.0, 0.0, 24.0),
            "forearm.L": (-30.0, 0.0, 0.0),
            "forearm.R": (-30.0, 0.0, 0.0),
        },
        locations={"pelvis": (0.0, 0.055, 0.0)},
    )
    frames.append((5, launch))

    ascending = with_pose(
        launch,
        rotations={
            "thigh.L": (-22.0, 0.0, 0.0),
            "thigh.R": (-18.0, 0.0, 0.0),
            "shin.L": (42.0, 0.0, 0.0),
            "shin.R": (35.0, 0.0, 0.0),
            "foot.L": (-8.0, 0.0, 0.0),
            "foot.R": (-8.0, 0.0, 0.0),
            "upper_arm.L": (2.0, 0.0, -14.0),
            "upper_arm.R": (2.0, 0.0, 14.0),
            "forearm.L": (-48.0, 0.0, 0.0),
            "forearm.R": (-48.0, 0.0, 0.0),
        },
        locations={"pelvis": (0.0, 0.255, 0.0)},
    )
    frames.append((12, ascending))

    apex = with_pose(
        ascending,
        rotations={
            "thigh.L": (-27.0, 0.0, 0.0),
            "thigh.R": (-23.0, 0.0, 0.0),
            "shin.L": (52.0, 0.0, 0.0),
            "shin.R": (45.0, 0.0, 0.0),
            "upper_arm.L": (-6.0, 0.0, -10.0),
            "upper_arm.R": (-6.0, 0.0, 10.0),
            "forearm.L": (-62.0, 0.0, 0.0),
            "forearm.R": (-62.0, 0.0, 0.0),
        },
        locations={"pelvis": (0.0, 0.335, 0.0)},
    )
    frames.append((18, apex))

    descent = with_pose(
        apex,
        rotations={
            "thigh.L": (-14.0, 0.0, 0.0),
            "thigh.R": (-12.0, 0.0, 0.0),
            "shin.L": (30.0, 0.0, 0.0),
            "shin.R": (26.0, 0.0, 0.0),
            "upper_arm.L": (-10.0, 0.0, -25.0),
            "upper_arm.R": (-10.0, 0.0, 25.0),
            "forearm.L": (-30.0, 0.0, 0.0),
            "forearm.R": (-30.0, 0.0, 0.0),
        },
        locations={"pelvis": (0.0, 0.155, 0.0)},
    )
    frames.append((24, descent))

    landing = crouch_pose(base, 1.0)
    landing = with_rotations(
        landing,
        {
            "upper_arm.L": (-44.0, 0.0, -32.0),
            "upper_arm.R": (-44.0, 0.0, 32.0),
            "forearm.L": (-50.0, 0.0, 0.0),
            "forearm.R": (-50.0, 0.0, 0.0),
        },
    )
    frames.append((29, landing))
    frames.append((36, neutral_pose()))
    return frames


def hit_frames():
    base = neutral_pose()
    frames = [(0, base)]
    impact = with_pose(
        base,
        rotations={
            "pelvis": (-4.0, -5.0, 3.0),
            "spine": (-10.0, -8.0, -5.0),
            "chest": (-16.0, -14.0, -8.0),
            "neck": (-10.0, 8.0, 5.0),
            "head": (-20.0, 14.0, 7.0),
            "upper_arm.L": (-44.0, 0.0, -25.0),
            "upper_arm.R": (-50.0, 0.0, -5.0),
            "forearm.L": (-35.0, 0.0, 0.0),
            "forearm.R": (-28.0, 0.0, 0.0),
        },
        locations={"pelvis": (0.0, -0.025, 0.045)},
    )
    frames.append((3, impact))
    recoil = with_pose(
        base,
        rotations={
            "pelvis": (-2.0, 2.0, -1.0),
            "spine": (-4.0, 4.0, 2.0),
            "chest": (-6.0, 6.0, 3.0),
            "head": (8.0, -7.0, -3.0),
            "upper_arm.L": (-58.0, 0.0, -12.0),
            "upper_arm.R": (-59.0, 0.0, 12.0),
        },
        locations={"pelvis": (0.0, -0.012, 0.018)},
    )
    frames.append((8, recoil))
    recover = with_pose(
        base,
        rotations={
            "spine": (1.0, 1.0, 0.0),
            "chest": (2.0, 2.0, 0.0),
            "head": (-2.0, -2.0, 0.0),
        },
        locations={"pelvis": (0.0, 0.003, 0.0)},
    )
    frames.append((14, recover))
    frames.append((20, neutral_pose()))
    return frames


def crouch_frames():
    base = neutral_pose()
    frames = []
    for frame, bob in ((0, 0.0), (15, 0.006), (30, 0.0)):
        pose = crouch_pose(base, 1.0, bob)
        pose = with_rotations(
            pose,
            {
                "neck": (-3.0 + bob * 20.0, 0.0, 0.0),
                "head": (-5.0 - bob * 18.0, 0.0, 0.0),
            },
        )
        frames.append((frame, pose))
    return frames


def jump_up_frames():
    base = neutral_pose()
    frames = []
    frames.append((0, crouch_pose(base, 0.82)))

    push = with_pose(
        base,
        rotations={
            "spine": (9.0, 0.0, 0.0),
            "chest": (6.0, 0.0, 0.0),
            "head": (-5.0, 0.0, 0.0),
            "thigh.L": (-8.0, 0.0, 0.0),
            "thigh.R": (-8.0, 0.0, 0.0),
            "shin.L": (12.0, 0.0, 0.0),
            "shin.R": (12.0, 0.0, 0.0),
            "foot.L": (19.0, 0.0, 0.0),
            "foot.R": (19.0, 0.0, 0.0),
            "upper_arm.L": (-30.0, 0.0, -25.0),
            "upper_arm.R": (-30.0, 0.0, 25.0),
            "forearm.L": (-30.0, 0.0, 0.0),
            "forearm.R": (-30.0, 0.0, 0.0),
        },
        locations={"pelvis": (0.0, 0.065, 0.0)},
    )
    frames.append((4, push))

    rising = with_pose(
        push,
        rotations={
            "thigh.L": (-18.0, 0.0, 0.0),
            "thigh.R": (-15.0, 0.0, 0.0),
            "shin.L": (34.0, 0.0, 0.0),
            "shin.R": (28.0, 0.0, 0.0),
            "foot.L": (-5.0, 0.0, 0.0),
            "foot.R": (-5.0, 0.0, 0.0),
            "upper_arm.L": (0.0, 0.0, -13.0),
            "upper_arm.R": (0.0, 0.0, 13.0),
            "forearm.L": (-48.0, 0.0, 0.0),
            "forearm.R": (-48.0, 0.0, 0.0),
        },
        locations={"pelvis": (0.0, 0.205, 0.0)},
    )
    frames.append((10, rising))

    peak = with_pose(
        rising,
        rotations={
            "thigh.L": (-22.0, 0.0, 0.0),
            "thigh.R": (-19.0, 0.0, 0.0),
            "shin.L": (41.0, 0.0, 0.0),
            "shin.R": (36.0, 0.0, 0.0),
            "upper_arm.L": (-8.0, 0.0, -9.0),
            "upper_arm.R": (-8.0, 0.0, 9.0),
            "forearm.L": (-60.0, 0.0, 0.0),
            "forearm.R": (-60.0, 0.0, 0.0),
        },
        locations={"pelvis": (0.0, 0.265, 0.0)},
    )
    frames.append((18, peak))
    return frames


def defeat_frames():
    base = neutral_pose()
    frames = [(0, base)]

    impact = with_pose(
        base,
        rotations={
            "pelvis": (-5.0, -5.0, 0.0),
            "spine": (-12.0, -4.0, 3.0),
            "chest": (-18.0, -7.0, 6.0),
            "neck": (-8.0, 5.0, 4.0),
            "head": (-22.0, 8.0, 7.0),
            "upper_arm.L": (-42.0, 0.0, -32.0),
            "upper_arm.R": (-44.0, 0.0, 28.0),
            "forearm.L": (-24.0, 0.0, 0.0),
            "forearm.R": (-20.0, 0.0, 0.0),
            "thigh.L": (-5.0, 0.0, 0.0),
            "thigh.R": (5.0, 0.0, 0.0),
            "shin.L": (10.0, 0.0, 0.0),
            "shin.R": (14.0, 0.0, 0.0),
        },
        locations={"pelvis": (0.0, -0.020, -0.035)},
    )
    frames.append((6, impact))

    off_balance = with_pose(
        base,
        rotations={
            "pelvis": (-20.0, -8.0, 4.0),
            "spine": (-25.0, -6.0, 5.0),
            "chest": (-18.0, -8.0, 8.0),
            "neck": (-10.0, 7.0, 4.0),
            "head": (-16.0, 11.0, 8.0),
            "upper_arm.L": (-25.0, 0.0, -50.0),
            "upper_arm.R": (-28.0, 0.0, 45.0),
            "forearm.L": (-20.0, 0.0, 0.0),
            "forearm.R": (-18.0, 0.0, 0.0),
            "thigh.L": (15.0, 0.0, -3.0),
            "thigh.R": (-8.0, 0.0, 4.0),
            "shin.L": (32.0, 0.0, 0.0),
            "shin.R": (26.0, 0.0, 0.0),
            "foot.L": (-8.0, 0.0, 0.0),
            "foot.R": (-5.0, 0.0, 0.0),
        },
        locations={"pelvis": (0.0, -0.100, -0.080)},
    )
    frames.append((12, off_balance))

    knee_collapse = with_pose(
        base,
        rotations={
            "pelvis": (-45.0, -5.0, 2.0),
            "spine": (-12.0, -4.0, 2.0),
            "chest": (-8.0, -5.0, 4.0),
            "neck": (-8.0, 5.0, 2.0),
            "head": (-8.0, 8.0, 4.0),
            "upper_arm.L": (-30.0, 0.0, -58.0),
            "upper_arm.R": (-32.0, 0.0, 52.0),
            "forearm.L": (-35.0, 0.0, 0.0),
            "forearm.R": (-32.0, 0.0, 0.0),
            "thigh.L": (-50.0, 0.0, -10.0),
            "thigh.R": (-50.0, 0.0, 12.0),
            "shin.L": (120.0, 0.0, 0.0),
            "shin.R": (120.0, 0.0, 0.0),
            "foot.L": (80.0, 0.0, 0.0),
            "foot.R": (80.0, 0.0, 0.0),
        },
        locations={"pelvis": (0.0, -0.320, -0.120)},
    )
    frames.append((22, knee_collapse))

    falling = with_pose(
        base,
        rotations={
            "pelvis": (-68.0, -3.0, -2.0),
            "spine": (-8.0, -3.0, -2.0),
            "chest": (-5.0, -4.0, -3.0),
            "neck": (-5.0, 3.0, -2.0),
            "head": (-12.0, 5.0, -4.0),
            "upper_arm.L": (-15.0, 0.0, -65.0),
            "upper_arm.R": (-18.0, 0.0, 60.0),
            "forearm.L": (-28.0, 0.0, 0.0),
            "forearm.R": (-25.0, 0.0, 0.0),
            "thigh.L": (-45.0, 0.0, -10.0),
            "thigh.R": (-35.0, 0.0, 12.0),
            "shin.L": (80.0, 0.0, 0.0),
            "shin.R": (60.0, 0.0, 0.0),
            "foot.L": (30.0, 0.0, 0.0),
            "foot.R": (45.0, 0.0, 0.0),
        },
        locations={"pelvis": (0.0, -0.520, -0.100)},
    )
    frames.append((34, falling))

    ground_impact = with_pose(
        base,
        rotations={
            "pelvis": (-84.0, -1.0, -3.0),
            "spine": (4.0, -1.0, -2.0),
            "chest": (6.0, -2.0, -3.0),
            "neck": (4.0, 2.0, -2.0),
            "head": (-8.0, 4.0, 5.0),
            "upper_arm.L": (-12.0, 0.0, -75.0),
            "upper_arm.R": (-14.0, 0.0, 70.0),
            "forearm.L": (-18.0, 0.0, 0.0),
            "forearm.R": (-16.0, 0.0, 0.0),
            "thigh.L": (-45.0, 0.0, -10.0),
            "thigh.R": (-35.0, 0.0, 12.0),
            "shin.L": (80.0, 0.0, 0.0),
            "shin.R": (60.0, 0.0, 0.0),
            "foot.L": (30.0, 0.0, 0.0),
            "foot.R": (45.0, 0.0, 0.0),
        },
        locations={"pelvis": (0.0, -0.660, -0.070)},
    )
    frames.append((44, ground_impact))

    settle = with_pose(
        ground_impact,
        rotations={
            "pelvis": (-87.0, 1.0, -2.0),
            "spine": (2.0, -1.0, -1.0),
            "chest": (3.0, -1.0, -2.0),
            "neck": (2.0, 2.0, -1.0),
            "head": (-5.0, 3.0, 5.0),
            "upper_arm.L": (-10.0, 0.0, -78.0),
            "upper_arm.R": (-12.0, 0.0, 73.0),
            "forearm.L": (-15.0, 0.0, 0.0),
            "forearm.R": (-14.0, 0.0, 0.0),
            "thigh.L": (-45.0, 0.0, -10.0),
            "thigh.R": (-35.0, 0.0, 12.0),
            "shin.L": (80.0, 0.0, 0.0),
            "shin.R": (60.0, 0.0, 0.0),
            "foot.L": (30.0, 0.0, 0.0),
            "foot.R": (45.0, 0.0, 0.0),
        },
        locations={"pelvis": (0.0, -0.680, -0.060)},
    )
    frames.append((52, settle))

    final = with_rotations(
        settle,
        {
            "pelvis": (-88.0, 1.0, -2.0),
            "spine": (2.0, -1.0, -1.0),
            "chest": (3.0, -1.0, -1.0),
            "neck": (2.0, 2.0, -1.0),
            "head": (-5.0, 3.0, 5.0),
        },
    )
    frames.append((60, final))
    return frames


def dance_pose(
    base,
    pelvis,
    pelvis_location,
    spine,
    chest,
    neck,
    head,
    left_arm,
    right_arm,
    left_leg,
    right_leg,
    jaw=0.0,
    lips=0.0,
    eye=0.0,
):
    rotations = {
        "pelvis": pelvis,
        "spine": spine,
        "chest": chest,
        "neck": neck,
        "head": head,
        "upper_arm.L": left_arm[0],
        "forearm.L": left_arm[1],
        "hand.L": left_arm[2],
        "upper_arm.R": right_arm[0],
        "forearm.R": right_arm[1],
        "hand.R": right_arm[2],
        "thigh.L": left_leg[0],
        "shin.L": left_leg[1],
        "foot.L": left_leg[2],
        "thigh.R": right_leg[0],
        "shin.R": right_leg[1],
        "foot.R": right_leg[2],
        "jaw": (jaw, 0.0, 0.0),
        "upper_lip": (jaw * 0.08, 0.0, 0.0),
        "lower_lip": (-jaw * 0.05, 0.0, 0.0),
        "glasses": (jaw * 0.05, 0.0, eye * 0.08),
        "eye.L": (0.0, 0.0, eye),
        "eye.R": (0.0, 0.0, eye),
    }
    return with_pose(
        base,
        rotations=rotations,
        locations={
            "pelvis": pelvis_location,
            "upper_lip": (0.0, lips, 0.0),
            "lower_lip": (0.0, lips * 1.5, 0.0),
        },
    )


def dance_frames():
    base = neutral_pose()

    def build_pose(style):
        pose = dance_pose(
            base,
            style["pelvis"],
            style["pelvis_location"],
            style["spine"],
            style["chest"],
            style["neck"],
            style["head"],
            style["left_arm"],
            style["right_arm"],
            style["left_leg"],
            style["right_leg"],
            style.get("jaw", 0.0),
            style.get("lips", 0.0),
            style.get("eye", 0.0),
        )
        left_hand = style.get("left_hand", "relaxed")
        right_hand = style.get("right_hand", "relaxed")
        if left_hand == "open":
            pose = open_hand_pose(pose, "L")
        elif left_hand == "point":
            pose = point_hand_pose(pose, "L")
        elif left_hand == "fist":
            pose = fist_pose(pose, "L", 0.88)
        if right_hand == "open":
            pose = open_hand_pose(pose, "R")
        elif right_hand == "point":
            pose = point_hand_pose(pose, "R")
        elif right_hand == "fist":
            pose = fist_pose(pose, "R", 0.88)
        return pose

    low_a = build_pose(
        {
            "pelvis": (4.0, 10.0, -5.0),
            "pelvis_location": (-0.026, 0.002, 0.012),
            "spine": (8.0, 17.0, 8.0),
            "chest": (5.0, 25.0, 11.0),
            "neck": (-4.0, -11.0, -6.0),
            "head": (-7.0, -18.0, -9.0),
            "left_arm": (
                (-17.0, 0.0, -68.0),
                (-88.0, 0.0, -10.0),
                (0.0, -8.0, -8.0),
            ),
            "right_arm": (
                (-59.0, 0.0, 48.0),
                (-48.0, 0.0, 12.0),
                (0.0, 8.0, 8.0),
            ),
            "left_leg": ((-16.0, 0.0, -4.0), (38.0, 0.0, 0.0), (-15.0, 0.0, 0.0)),
            "right_leg": ((8.0, 0.0, 4.0), (18.0, 0.0, 0.0), (-4.0, 0.0, 0.0)),
            "left_hand": "open",
            "right_hand": "fist",
            "jaw": 5.0,
            "lips": 0.002,
            "eye": 4.0,
        }
    )
    pop_a = build_pose(
        {
            "pelvis": (0.0, -5.0, 3.0),
            "pelvis_location": (0.010, 0.058, 0.004),
            "spine": (3.0, -10.0, -4.0),
            "chest": (1.0, -16.0, -7.0),
            "neck": (-1.0, 7.0, 4.0),
            "head": (-3.0, 12.0, 6.0),
            "left_arm": (
                (-36.0, 0.0, -20.0),
                (-72.0, 0.0, -4.0),
                (0.0, -4.0, -4.0),
            ),
            "right_arm": (
                (-28.0, 0.0, 22.0),
                (-70.0, 0.0, 4.0),
                (0.0, 4.0, 4.0),
            ),
            "left_leg": ((-6.0, 0.0, -2.0), (18.0, 0.0, 0.0), (-5.0, 0.0, 0.0)),
            "right_leg": ((-7.0, 0.0, 2.0), (20.0, 0.0, 0.0), (-6.0, 0.0, 0.0)),
            "left_hand": "open",
            "right_hand": "open",
            "jaw": 1.0,
            "eye": -3.0,
        }
    )
    low_b = build_pose(
        {
            "pelvis": (5.0, -11.0, 5.0),
            "pelvis_location": (0.027, 0.008, 0.010),
            "spine": (9.0, -18.0, -8.0),
            "chest": (6.0, -27.0, -12.0),
            "neck": (-4.0, 12.0, 7.0),
            "head": (-8.0, 20.0, 10.0),
            "left_arm": (
                (-58.0, 0.0, -46.0),
                (-46.0, 0.0, -12.0),
                (0.0, -8.0, -8.0),
            ),
            "right_arm": (
                (-16.0, 0.0, 69.0),
                (-90.0, 0.0, 10.0),
                (0.0, 9.0, 8.0),
            ),
            "left_leg": ((8.0, 0.0, -4.0), (18.0, 0.0, 0.0), (-4.0, 0.0, 0.0)),
            "right_leg": ((-16.0, 0.0, 4.0), (38.0, 0.0, 0.0), (-15.0, 0.0, 0.0)),
            "left_hand": "fist",
            "right_hand": "open",
            "jaw": 8.0,
            "lips": 0.004,
            "eye": -5.0,
        }
    )
    pop_b = build_pose(
        {
            "pelvis": (0.0, 4.0, -3.0),
            "pelvis_location": (-0.010, 0.060, 0.002),
            "spine": (3.0, 9.0, 4.0),
            "chest": (1.0, 15.0, 7.0),
            "neck": (-1.0, -7.0, -4.0),
            "head": (-3.0, -11.0, -6.0),
            "left_arm": (
                (-29.0, 0.0, -24.0),
                (-68.0, 0.0, -4.0),
                (0.0, -4.0, -4.0),
            ),
            "right_arm": (
                (-36.0, 0.0, 19.0),
                (-74.0, 0.0, 4.0),
                (0.0, 4.0, 4.0),
            ),
            "left_leg": ((-7.0, 0.0, -2.0), (20.0, 0.0, 0.0), (-6.0, 0.0, 0.0)),
            "right_leg": ((-6.0, 0.0, 2.0), (18.0, 0.0, 0.0), (-5.0, 0.0, 0.0)),
            "left_hand": "open",
            "right_hand": "open",
            "jaw": 2.0,
            "eye": 3.0,
        }
    )
    low_c = build_pose(
        {
            "pelvis": (7.0, 0.0, -8.0),
            "pelvis_location": (0.000, -0.004, 0.018),
            "spine": (10.0, 0.0, 12.0),
            "chest": (7.0, 0.0, 17.0),
            "neck": (-5.0, 0.0, -9.0),
            "head": (-9.0, 0.0, -14.0),
            "left_arm": (
                (-8.0, 0.0, -84.0),
                (-58.0, 0.0, -8.0),
                (0.0, 0.0, -10.0),
            ),
            "right_arm": (
                (-8.0, 0.0, 84.0),
                (-58.0, 0.0, 8.0),
                (0.0, 0.0, 10.0),
            ),
            "left_leg": ((-20.0, 0.0, -5.0), (44.0, 0.0, 0.0), (-19.0, 0.0, 0.0)),
            "right_leg": ((-20.0, 0.0, 5.0), (44.0, 0.0, 0.0), (-19.0, 0.0, 0.0)),
            "left_hand": "open",
            "right_hand": "open",
            "jaw": 12.0,
            "lips": 0.006,
            "eye": 0.0,
        }
    )
    pop_c = build_pose(
        {
            "pelvis": (0.0, 7.0, 4.0),
            "pelvis_location": (-0.014, 0.059, -0.002),
            "spine": (2.0, 14.0, -6.0),
            "chest": (0.0, 22.0, -9.0),
            "neck": (-1.0, -10.0, 5.0),
            "head": (-2.0, -16.0, 8.0),
            "left_arm": (
                (-30.0, 0.0, -40.0),
                (-76.0, 0.0, -6.0),
                (0.0, -6.0, -5.0),
            ),
            "right_arm": (
                (-27.0, 0.0, 35.0),
                (-82.0, 0.0, 6.0),
                (0.0, 6.0, 5.0),
            ),
            "left_leg": ((-7.0, 0.0, -2.0), (20.0, 0.0, 0.0), (-6.0, 0.0, 0.0)),
            "right_leg": ((-8.0, 0.0, 2.0), (22.0, 0.0, 0.0), (-7.0, 0.0, 0.0)),
            "left_hand": "point",
            "right_hand": "open",
            "jaw": 3.0,
            "eye": -4.0,
        }
    )
    low_d = build_pose(
        {
            "pelvis": (3.0, 13.0, -4.0),
            "pelvis_location": (-0.032, 0.016, 0.008),
            "spine": (7.0, 20.0, 7.0),
            "chest": (4.0, 29.0, 10.0),
            "neck": (-3.0, -13.0, -6.0),
            "head": (-6.0, -21.0, -8.0),
            "left_arm": (
                (-20.0, 0.0, -48.0),
                (-112.0, 0.0, -11.0),
                (0.0, -10.0, -8.0),
            ),
            "right_arm": (
                (-39.0, 0.0, 43.0),
                (-106.0, 0.0, 10.0),
                (0.0, 10.0, 8.0),
            ),
            "left_leg": ((-11.0, 0.0, -4.0), (30.0, 0.0, 0.0), (-11.0, 0.0, 0.0)),
            "right_leg": ((4.0, 0.0, 4.0), (22.0, 0.0, 0.0), (-7.0, 0.0, 0.0)),
            "left_hand": "fist",
            "right_hand": "point",
            "jaw": 6.0,
            "lips": 0.003,
            "eye": 5.0,
        }
    )
    pop_d = build_pose(
        {
            "pelvis": (0.0, -6.0, 3.0),
            "pelvis_location": (0.012, 0.062, 0.000),
            "spine": (3.0, -11.0, -5.0),
            "chest": (1.0, -18.0, -8.0),
            "neck": (-1.0, 8.0, 4.0),
            "head": (-3.0, 13.0, 6.0),
            "left_arm": (
                (-34.0, 0.0, -28.0),
                (-78.0, 0.0, -5.0),
                (0.0, -5.0, -4.0),
            ),
            "right_arm": (
                (-27.0, 0.0, 26.0),
                (-72.0, 0.0, 5.0),
                (0.0, 5.0, 4.0),
            ),
            "left_leg": ((-6.0, 0.0, -2.0), (18.0, 0.0, 0.0), (-5.0, 0.0, 0.0)),
            "right_leg": ((-7.0, 0.0, 2.0), (20.0, 0.0, 0.0), (-6.0, 0.0, 0.0)),
            "left_hand": "fist",
            "right_hand": "fist",
            "jaw": 1.0,
            "eye": -2.0,
        }
    )

    return [
        (0, low_a),
        (8, pop_a),
        (15, low_b),
        (23, pop_b),
        (30, low_c),
        (38, pop_c),
        (45, low_d),
        (53, pop_d),
        (60, low_a),
    ]


ACTION_SPECS = {
    "idle": {"frames": idle_frames, "loop": True, "frame_end": 60},
    "walk": {"frames": walk_frames, "loop": True, "frame_end": 32},
    "run": {"frames": run_frames, "loop": True, "frame_end": 24},
    "talk": {"frames": talk_frames, "loop": True, "frame_end": 60},
    "attack": {"frames": attack_frames, "loop": False, "frame_end": 24},
    "jump": {"frames": jump_frames, "loop": False, "frame_end": 36},
    "hit": {"frames": hit_frames, "loop": False, "frame_end": 20},
    "crouch": {"frames": crouch_frames, "loop": True, "frame_end": 30},
    "jump_up": {"frames": jump_up_frames, "loop": False, "frame_end": 18},
    "defeat": {"frames": defeat_frames, "loop": False, "frame_end": 60},
    "dance": {"frames": dance_frames, "loop": True, "frame_end": 60},
}


def reset_pose(armature):
    for pose_bone in armature.pose.bones:
        pose_bone.matrix_basis = Matrix.Identity(4)
        pose_bone.rotation_mode = "XYZ"
    bpy.context.view_layer.update()


def set_bone_rotation(armature, bone_name, degrees_xyz):
    pose_bone = armature.pose.bones[bone_name]
    pose_bone.rotation_mode = "XYZ"
    pose_bone.rotation_euler = tuple(d(value) for value in degrees_xyz)


def set_bone_location(armature, bone_name, location_xyz):
    pose_bone = armature.pose.bones[bone_name]
    pose_bone.location = location_xyz


def apply_pose(armature, pose):
    reset_pose(armature)
    for bone_name, rotation in pose["rotations"].items():
        set_bone_rotation(armature, bone_name, rotation)
    for bone_name, location in pose["locations"].items():
        set_bone_location(armature, bone_name, location)
    bpy.context.view_layer.update()


def key_pose(armature, frame, bone_names):
    for bone_name in bone_names:
        pose_bone = armature.pose.bones[bone_name]
        pose_bone.keyframe_insert(data_path="rotation_euler", frame=frame)
        if bone_name in LOCATION_BONES:
            pose_bone.keyframe_insert(data_path="location", frame=frame)


def configure_action_curves(action, loop):
    fcurves = list(action.fcurves)
    for fcurve in fcurves:
        for point in fcurve.keyframe_points:
            point.interpolation = "BEZIER"
            point.handle_left_type = "AUTO_CLAMPED"
            point.handle_right_type = "AUTO_CLAMPED"
        if loop and len(fcurve.keyframe_points) >= 2:
            first = fcurve.keyframe_points[0]
            last = fcurve.keyframe_points[-1]
            first.handle_left_type = "AUTO"
            first.handle_right_type = "AUTO"
            last.handle_left_type = "AUTO"
            last.handle_right_type = "AUTO"


def clear_previous_animation(armature):
    if armature.animation_data:
        armature.animation_data_clear()
    for action in list(bpy.data.actions):
        bpy.data.actions.remove(action)
    for pose_bone in armature.pose.bones:
        pose_bone.rotation_mode = "XYZ"
        pose_bone.matrix_basis = Matrix.Identity(4)


def build_actions(armature):
    bone_names = [bone.name for bone in armature.data.bones]
    armature.animation_data_create()
    created = {}
    for action_name, spec in ACTION_SPECS.items():
        action = bpy.data.actions.new(action_name)
        action.use_fake_user = True
        action["clip_name"] = action_name
        action["loop"] = bool(spec["loop"])
        action["duration_frames"] = int(spec["frame_end"])
        armature.animation_data.action = action
        for frame, pose in spec["frames"]():
            bpy.context.scene.frame_set(frame)
            apply_pose(armature, pose)
            key_pose(armature, frame, bone_names)
        if hasattr(action, "use_frame_range"):
            action.use_frame_range = True
            action.frame_start = 0.0
            action.frame_end = float(spec["frame_end"])
        configure_action_curves(action, spec["loop"])
        created[action_name] = action
    return created


def export_glb(glb_path):
    character_collection = bpy.data.collections.get("CHARACTER")
    if character_collection is None:
        raise RuntimeError("CHARACTER collection is missing")
    bpy.ops.object.select_all(action="DESELECT")
    for obj in character_collection.objects:
        if obj.type in {"MESH", "ARMATURE"}:
            obj.select_set(True)
    armature = bpy.data.objects.get(ARMATURE_NAME)
    if armature is None:
        raise RuntimeError("Character armature is missing")
    bpy.context.view_layer.objects.active = armature
    bpy.ops.export_scene.gltf(
        filepath=glb_path,
        export_format="GLB",
        use_selection=True,
        export_yup=True,
        export_apply=True,
        export_skins=True,
        export_animations=True,
        export_animation_mode="ACTIONS",
        export_merge_animation="ACTION",
        export_frame_range=False,
        export_bake_animation=True,
        export_optimize_animation_size=False,
        export_optimize_animation_keep_anim_armature=True,
        export_anim_scene_split_object=False,
        export_morph_animation=False,
        export_cameras=False,
        export_lights=False,
    )


def main():
    blend_path, glb_path = parse_paths()
    armatures = [obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE"]
    if len(armatures) != 1:
        raise RuntimeError("Expected exactly one armature")
    armature = armatures[0]
    if armature.name != ARMATURE_NAME:
        raise RuntimeError("Expected armature %s" % ARMATURE_NAME)
    if len(armature.data.bones) != 56:
        raise RuntimeError("Expected 56 bones, found %d" % len(armature.data.bones))

    clear_previous_animation(armature)
    bpy.context.scene.render.fps = FPS
    bpy.context.scene.render.fps_base = 1.0
    actions = build_actions(armature)
    armature.animation_data.action = actions["idle"]
    bpy.context.scene.frame_start = 0
    bpy.context.scene.frame_end = 60
    bpy.context.scene.frame_set(0)
    reset_pose(armature)

    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    export_glb(glb_path)
    print("CHARACTER_ANIMATIONS_V11_BUILD_COMPLETE")
    print("BLEND", blend_path)
    print("GLB", glb_path)
    print("ACTIONS", ",".join(sorted(actions)))


if __name__ == "__main__":
    main()
