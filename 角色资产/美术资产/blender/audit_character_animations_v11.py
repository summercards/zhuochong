import hashlib
import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector


ROOT = os.path.abspath(os.path.dirname(__file__))
DEFAULT_GLB = os.path.join(ROOT, "business_man_tpose_v11.glb")
DEFAULT_REPORT = os.path.join(ROOT, "CHARACTER_ANIMATION_AUDIT_V11.json")
DEFAULT_PREVIEW_DIR = ROOT
GROUND_Z = -0.012

EXPECTED_ACTIONS = {
    "idle": {"duration": 2.0, "loop": True, "preview_fraction": 0.25},
    "walk": {"duration": 32.0 / 30.0, "loop": True, "preview_fraction": 0.25},
    "run": {"duration": 24.0 / 30.0, "loop": True, "preview_fraction": 0.0},
    "talk": {"duration": 2.0, "loop": True, "preview_fraction": 0.40},
    "attack": {"duration": 24.0 / 30.0, "loop": False, "preview_fraction": 11.0 / 24.0},
    "jump": {"duration": 36.0 / 30.0, "loop": False, "preview_fraction": 0.50},
    "hit": {"duration": 20.0 / 30.0, "loop": False, "preview_fraction": 0.15},
    "crouch": {"duration": 1.0, "loop": True, "preview_fraction": 0.50},
    "jump_up": {"duration": 18.0 / 30.0, "loop": False, "preview_fraction": 10.0 / 18.0},
    "defeat": {"duration": 2.0, "loop": False, "preview_fraction": 52.0 / 60.0},
    "dance": {"duration": 2.0, "loop": True, "preview_fraction": 0.50},
}


def parse_paths():
    if "--" not in sys.argv:
        return DEFAULT_GLB, DEFAULT_REPORT, DEFAULT_PREVIEW_DIR
    values = sys.argv[sys.argv.index("--") + 1 :]
    if len(values) != 3:
        raise ValueError("Expected GLB, report, and preview directory paths after --")
    return tuple(os.path.abspath(value) for value in values)


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def serializable_vector(vector):
    return [round(float(value), 6) for value in vector]


def finite_vector(vector):
    return all(math.isfinite(float(value)) for value in vector)


def matrix_delta(a, b):
    return max(
        abs(float(a[row][column]) - float(b[row][column]))
        for row in range(4)
        for column in range(4)
    )


def pose_snapshot(armature):
    return {
        pose_bone.name: pose_bone.matrix_basis.copy()
        for pose_bone in armature.pose.bones
    }


def max_pose_delta(first, second):
    if set(first) != set(second):
        raise RuntimeError("Pose snapshots contain different bones")
    return max(matrix_delta(first[name], second[name]) for name in first)


def evaluated_points(meshes):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    points = []
    finite = True
    for obj in meshes:
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        try:
            for vertex in mesh.vertices:
                point = evaluated.matrix_world @ vertex.co
                finite = finite and finite_vector(point)
                points.append(point)
        finally:
            evaluated.to_mesh_clear()
    return points, finite


def evaluated_stats(meshes):
    points, finite = evaluated_points(meshes)
    if not points:
        raise RuntimeError("No mesh vertices were evaluated")
    minimum = Vector(
        (
            min(point.x for point in points),
            min(point.y for point in points),
            min(point.z for point in points),
        )
    )
    maximum = Vector(
        (
            max(point.x for point in points),
            max(point.y for point in points),
            max(point.z for point in points),
        )
    )
    return {
        "minimum": serializable_vector(minimum),
        "maximum": serializable_vector(maximum),
        "dimensions": serializable_vector(maximum - minimum),
        "finite": finite,
    }


def reset_pose(armature):
    for pose_bone in armature.pose.bones:
        pose_bone.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()


def assign_action(armature, action):
    if armature.animation_data is None:
        armature.animation_data_create()
    armature.animation_data.action = action
    if armature.animation_data.action_slot is None and action.slots:
        preferred = next(
            (
                slot
                for slot in action.slots
                if slot.identifier == "OB" + armature.name
            ),
            action.slots[0],
        )
        armature.animation_data.action_slot = preferred
    bpy.context.view_layer.update()


def action_time_frame(action, seconds):
    start, end = action.frame_range
    return int(round(start + seconds * bpy.context.scene.render.fps))


def sample_fraction(armature, action, fraction):
    start, end = action.frame_range
    frame = int(round(start + (end - start) * float(fraction)))
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()
    return frame


def action_finite(action):
    value_finite = True
    time_finite = True
    point_count = 0
    for fcurve in action.fcurves:
        for point in fcurve.keyframe_points:
            point_count += 1
            time_finite = time_finite and math.isfinite(float(point.co[0]))
            value_finite = value_finite and math.isfinite(float(point.co[1]))
    return {
        "curve_count": len(action.fcurves),
        "keyframe_point_count": point_count,
        "time_finite": time_finite,
        "value_finite": value_finite,
        "pass": bool(action.fcurves) and time_finite and value_finite,
    }


def root_motion_check(armature, action):
    start, end = action.frame_range
    max_location = 0.0
    max_rotation = 0.0
    max_scale_error = 0.0
    finite = True
    for frame in range(int(math.floor(start)), int(math.ceil(end)) + 1):
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()
        root = armature.pose.bones["root"]
        location = root.matrix_basis.to_translation()
        rotation = root.matrix_basis.to_quaternion().angle
        scale = root.matrix_basis.to_scale()
        finite = finite and finite_vector(location)
        finite = finite and math.isfinite(float(rotation))
        finite = finite and finite_vector(scale)
        max_location = max(max_location, float(location.length))
        max_rotation = max(max_rotation, abs(float(rotation)))
        max_scale_error = max(
            max_scale_error,
            max(abs(float(value) - 1.0) for value in scale),
        )
    return {
        "max_location_m": round(max_location, 8),
        "max_rotation_radians": round(max_rotation, 8),
        "max_scale_error": round(max_scale_error, 8),
        "finite": finite,
        "pass": (
            finite
            and max_location <= 0.0001
            and max_rotation <= 0.0001
            and max_scale_error <= 0.0001
        ),
    }


def loop_check(armature, action):
    start, end = action.frame_range
    delta = 0.0
    for fcurve in action.fcurves:
        delta = max(
            delta,
            abs(float(fcurve.evaluate(start)) - float(fcurve.evaluate(end))),
        )
    return {
        "max_curve_endpoint_delta": round(float(delta), 8),
        "pass": delta <= 0.0001,
    }


def pose_angle_degrees(pose_bone):
    return math.degrees(float(pose_bone.matrix_basis.to_quaternion().angle))


def action_pose_checks(armature, actions, meshes):
    checks = {}
    talk = actions["talk"]
    assign_action(armature, talk)
    sample_fraction(armature, talk, 24.0 / 60.0)
    jaw_angle = pose_angle_degrees(armature.pose.bones["jaw"])
    upper_lip_offset = abs(float(armature.pose.bones["upper_lip"].location.y))
    lower_lip_offset = abs(float(armature.pose.bones["lower_lip"].location.y))
    checks["talk"] = {
        "sample": "source frame 24",
        "jaw_angle_degrees": round(jaw_angle, 6),
        "upper_lip_local_y_m": round(upper_lip_offset, 6),
        "lower_lip_local_y_m": round(lower_lip_offset, 6),
        "pass": (
            jaw_angle >= 10.0
            and upper_lip_offset >= 0.003
            and lower_lip_offset >= 0.006
        ),
    }

    attack = actions["attack"]
    assign_action(armature, attack)
    sample_fraction(armature, attack, 11.0 / 24.0)
    fist_angles = [
        pose_angle_degrees(armature.pose.bones["finger_%s_01.R" % digit])
        for digit in ("index", "middle", "ring", "pinky")
    ]
    checks["attack"] = {
        "sample": "source frame 11",
        "right_index_to_pinky_first_joint_degrees": [
            round(value, 6) for value in fist_angles
        ],
        "pass": min(fist_angles) >= 45.0,
    }

    crouch = actions["crouch"]
    assign_action(armature, crouch)
    sample_fraction(armature, crouch, 0.0)
    crouch_pelvis_offset = float(armature.pose.bones["pelvis"].location.length)
    checks["crouch"] = {
        "pelvis_offset_m": round(crouch_pelvis_offset, 6),
        "pass": crouch_pelvis_offset >= 0.14,
    }

    jump = actions["jump"]
    assign_action(armature, jump)
    sample_fraction(armature, jump, 0.50)
    jump_pelvis_offset = float(armature.pose.bones["pelvis"].location.length)
    checks["jump"] = {
        "pelvis_offset_m": round(jump_pelvis_offset, 6),
        "pass": jump_pelvis_offset >= 0.25,
    }

    jump_up = actions["jump_up"]
    assign_action(armature, jump_up)
    sample_fraction(armature, jump_up, 1.0)
    jump_up_pelvis_offset = float(armature.pose.bones["pelvis"].location.length)
    checks["jump_up"] = {
        "pelvis_offset_m": round(jump_up_pelvis_offset, 6),
        "pass": jump_up_pelvis_offset >= 0.20,
    }

    hit = actions["hit"]
    assign_action(armature, hit)
    sample_fraction(armature, hit, 3.0 / 20.0)
    hit_chest_angle = pose_angle_degrees(armature.pose.bones["chest"])
    hit_head_angle = pose_angle_degrees(armature.pose.bones["head"])
    checks["hit"] = {
        "chest_angle_degrees": round(hit_chest_angle, 6),
        "head_angle_degrees": round(hit_head_angle, 6),
        "pass": hit_chest_angle >= 8.0 and hit_head_angle >= 10.0,
    }

    locomotion = {}
    for action_name in ("walk", "run"):
        action = actions[action_name]
        assign_action(armature, action)
        sample_fraction(armature, action, 0.0)
        left_a = armature.pose.bones["thigh.L"].matrix_basis.copy()
        right_a = armature.pose.bones["thigh.R"].matrix_basis.copy()
        sample_fraction(armature, action, 0.5)
        left_b = armature.pose.bones["thigh.L"].matrix_basis.copy()
        right_b = armature.pose.bones["thigh.R"].matrix_basis.copy()
        stride_delta = max(
            matrix_delta(left_a, left_b),
            matrix_delta(right_a, right_b),
        )
        minimum = 0.20 if action_name == "run" else 0.10
        locomotion[action_name] = {
            "half_cycle_thigh_matrix_delta": round(float(stride_delta), 6),
            "pass": stride_delta >= minimum,
        }
        if action_name == "run":
            sample_fraction(armature, action, 0.0)
            left_y_start = float(
                armature.pose.bones["hand.L"].matrix.translation.y
            )
            right_y_start = float(
                armature.pose.bones["hand.R"].matrix.translation.y
            )
            sample_fraction(armature, action, 0.5)
            left_y_half = float(
                armature.pose.bones["hand.L"].matrix.translation.y
            )
            right_y_half = float(
                armature.pose.bones["hand.R"].matrix.translation.y
            )
            left_delta = left_y_half - left_y_start
            right_delta = right_y_half - right_y_start
            opposite_phase = left_delta * right_delta < 0.0
            locomotion[action_name].update(
                {
                    "left_hand_y_delta_m": round(abs(left_delta), 6),
                    "right_hand_y_delta_m": round(abs(right_delta), 6),
                    "opposite_phase": opposite_phase,
                }
            )
            locomotion[action_name]["pass"] = (
                locomotion[action_name]["pass"]
                and abs(left_delta) >= 0.45
                and abs(right_delta) >= 0.45
                and opposite_phase
            )
    checks["locomotion"] = locomotion

    dance = actions["dance"]
    assign_action(armature, dance)
    dance_frames = (0, 8, 15, 23, 30, 38, 45, 53, 60)
    dance_snapshots = {}
    for frame in dance_frames:
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()
        dance_snapshots[frame] = {
            bone_name: armature.pose.bones[bone_name].matrix_basis.copy()
            for bone_name in (
                "pelvis",
                "chest",
                "head",
                "upper_arm.L",
                "upper_arm.R",
                "forearm.L",
                "forearm.R",
                "hand.L",
                "hand.R",
                "thigh.L",
                "thigh.R",
                "shin.L",
                "shin.R",
                "finger_index_01.L",
                "finger_index_01.R",
            )
        }
        dance_snapshots[frame]["pelvis_world_z"] = (
            armature.pose.bones["pelvis"].matrix.translation.z
        )
        dance_snapshots[frame]["left_hand_world"] = (
            armature.pose.bones["hand.L"].matrix.translation.copy()
        )
        dance_snapshots[frame]["right_hand_world"] = (
            armature.pose.bones["hand.R"].matrix.translation.copy()
        )

    pelvis_world_z = [
        float(dance_snapshots[frame]["pelvis_world_z"])
        for frame in dance_frames
    ]
    left_hand_positions = [
        dance_snapshots[frame]["left_hand_world"]
        for frame in dance_frames
    ]
    right_hand_positions = [
        dance_snapshots[frame]["right_hand_world"]
        for frame in dance_frames
    ]

    def position_range(positions):
        return max(
            max(position[axis] for position in positions)
            - min(position[axis] for position in positions)
            for axis in range(3)
        )

    pelvis_bounce = max(pelvis_world_z) - min(pelvis_world_z)
    left_hand_travel = position_range(left_hand_positions)
    right_hand_travel = position_range(right_hand_positions)
    arm_swing_delta = max(
        matrix_delta(
            dance_snapshots[0]["upper_arm.L"],
            dance_snapshots[30]["upper_arm.L"],
        ),
        matrix_delta(
            dance_snapshots[0]["upper_arm.R"],
            dance_snapshots[30]["upper_arm.R"],
        ),
    )
    knee_bounce_delta = max(
        matrix_delta(
            dance_snapshots[0]["shin.L"],
            dance_snapshots[8]["shin.L"],
        ),
        matrix_delta(
            dance_snapshots[0]["shin.R"],
            dance_snapshots[8]["shin.R"],
        ),
    )
    torso_twist_delta = max(
        matrix_delta(
            dance_snapshots[0]["chest"],
            dance_snapshots[15]["chest"],
        ),
        matrix_delta(
            dance_snapshots[15]["chest"],
            dance_snapshots[30]["chest"],
        ),
    )
    head_motion_delta = max(
        matrix_delta(
            dance_snapshots[0]["head"],
            dance_snapshots[15]["head"],
        ),
        matrix_delta(
            dance_snapshots[15]["head"],
            dance_snapshots[30]["head"],
        ),
    )
    finger_gesture_delta = max(
        matrix_delta(
            dance_snapshots[0]["finger_index_01.L"],
            dance_snapshots[15]["finger_index_01.L"],
        ),
        matrix_delta(
            dance_snapshots[0]["finger_index_01.R"],
            dance_snapshots[30]["finger_index_01.R"],
        ),
    )
    bpy.context.scene.frame_set(30)
    bpy.context.view_layer.update()
    dance_jaw_angle = pose_angle_degrees(armature.pose.bones["jaw"])
    checks["dance"] = {
        "pelvis_vertical_range_m": round(float(pelvis_bounce), 6),
        "left_hand_travel_m": round(float(left_hand_travel), 6),
        "right_hand_travel_m": round(float(right_hand_travel), 6),
        "arm_swing_matrix_delta": round(float(arm_swing_delta), 6),
        "knee_bounce_matrix_delta": round(float(knee_bounce_delta), 6),
        "torso_twist_matrix_delta": round(float(torso_twist_delta), 6),
        "head_motion_matrix_delta": round(float(head_motion_delta), 6),
        "finger_gesture_matrix_delta": round(float(finger_gesture_delta), 6),
        "jaw_angle_degrees_at_beat": round(float(dance_jaw_angle), 6),
        "pass": (
            pelvis_bounce >= 0.025
            and left_hand_travel >= 0.35
            and right_hand_travel >= 0.35
            and arm_swing_delta >= 0.35
            and knee_bounce_delta >= 0.15
            and torso_twist_delta >= 0.20
            and head_motion_delta >= 0.15
            and finger_gesture_delta >= 0.30
            and dance_jaw_angle >= 8.0
        ),
    }

    defeat = actions["defeat"]
    assign_action(armature, defeat)
    sample_fraction(armature, defeat, 1.0)
    defeat_pelvis_angle = pose_angle_degrees(armature.pose.bones["pelvis"])
    defeat_pelvis_drop = abs(
        float(armature.pose.bones["pelvis"].location.y)
    )
    defeat_stats = evaluated_stats(meshes)
    checks["defeat"] = {
        "sample": "source frame 60",
        "pelvis_fall_angle_degrees": round(defeat_pelvis_angle, 6),
        "pelvis_drop_m": round(defeat_pelvis_drop, 6),
        "final_maximum_z_m": defeat_stats["maximum"][2],
        "final_y_dimension_m": defeat_stats["dimensions"][1],
        "final_minimum_z_m": defeat_stats["minimum"][2],
        "pass": (
            defeat_pelvis_angle >= 70.0
            and defeat_pelvis_drop >= 0.60
            and defeat_stats["maximum"][2] <= 1.0
            and defeat_stats["dimensions"][1] >= 1.3
            and defeat_stats["minimum"][2] >= -0.040
        ),
    }
    return checks


def add_presentation():
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 720
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    if scene.world is None:
        scene.world = bpy.data.worlds.new("Animation Audit World")
    scene.world.color = (0.018, 0.024, 0.035)

    bpy.ops.object.camera_add(location=(3.5, -5.0, 2.4))
    camera = bpy.context.object
    camera.name = "Animation_Audit_Camera"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 2.55
    target = Vector((0.0, 0.0, 0.94))
    camera.rotation_euler = (
        target - camera.location
    ).to_track_quat("-Z", "Y").to_euler()
    scene.camera = camera

    for name, location, energy, size in (
        ("Animation_Audit_Key", (-4.0, -4.5, 5.5), 1350.0, 4.0),
        ("Animation_Audit_Fill", (4.2, -2.0, 3.2), 720.0, 3.2),
        ("Animation_Audit_Rim", (1.2, 4.5, 4.6), 980.0, 3.0),
    ):
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.name = name
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        light.rotation_euler = (
            target - light.location
        ).to_track_quat("-Z", "Y").to_euler()

    bpy.ops.mesh.primitive_plane_add(size=8.0, location=(0.0, 0.0, -0.012))
    ground = bpy.context.object
    ground.name = "Animation_Audit_Ground"
    material = bpy.data.materials.new("Animation Audit Ground")
    material.diffuse_color = (0.045, 0.055, 0.075, 1.0)
    ground.data.materials.append(material)
    return camera


def camera_view_for_action(action_name):
    if action_name == "attack":
        return (
            Vector((-3.7, -4.6, 2.15)),
            Vector((0.0, 0.0, 0.94)),
            2.55,
        )
    if action_name == "run":
        return (
            Vector((4.8, -0.7, 2.1)),
            Vector((0.0, 0.0, 0.95)),
            2.55,
        )
    if action_name == "defeat":
        return (
            Vector((4.1, -5.4, 3.1)),
            Vector((0.0, 0.08, 0.34)),
            2.80,
        )
    if action_name == "dance":
        return (
            Vector((3.8, -5.2, 2.35)),
            Vector((0.0, 0.0, 0.98)),
            2.65,
        )
    return (
        Vector((3.5, -5.0, 2.4)),
        Vector((0.0, 0.0, 0.94)),
        2.55,
    )


def render_previews(armature, actions, preview_dir):
    os.makedirs(preview_dir, exist_ok=True)
    camera = add_presentation()
    previews = {}
    for action_name in EXPECTED_ACTIONS:
        camera.location, target, camera.data.ortho_scale = camera_view_for_action(
            action_name
        )
        camera.rotation_euler = (
            target - camera.location
        ).to_track_quat("-Z", "Y").to_euler()
        action = actions[action_name]
        assign_action(armature, action)
        fraction = EXPECTED_ACTIONS[action_name]["preview_fraction"]
        sample_fraction(armature, action, fraction)
        path = os.path.join(
            preview_dir,
            "business_man_tpose_v11_%s_preview.png" % action_name,
        )
        bpy.context.scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        previews[action_name] = {
            "path": path,
            "source_frame": int(round(EXPECTED_ACTIONS[action_name]["duration"] * 30.0 * fraction)),
        }
    return previews


def ground_contact_checks(armature, actions, meshes):
    expected_frames = {
        "idle": (0, 30, 60),
        "walk": (0, 8, 16, 24, 32),
        "run": (0, 6, 12, 18, 24),
        "talk": (0, 30, 60),
        "attack": (0, 24),
        "jump": (0, 36),
        "hit": (0, 20),
        "crouch": (0, 15, 30),
        "jump_up": (0,),
        "defeat": (0, 22, 44, 60),
        "dance": (0, 8, 15, 23, 30, 38, 45, 53, 60),
    }
    checks = {}
    for action_name, frames in expected_frames.items():
        action = actions[action_name]
        assign_action(armature, action)
        samples = []
        for frame in frames:
            bpy.context.scene.frame_set(frame)
            bpy.context.view_layer.update()
            stats = evaluated_stats(meshes)
            clearance = float(stats["minimum"][2]) - GROUND_Z
            samples.append({
                "frame": frame,
                "minimum_z_m": stats["minimum"][2],
                "ground_clearance_m": round(clearance, 6),
            })
        clearances = [sample["ground_clearance_m"] for sample in samples]
        maximum_clearance = (
            0.06 if action_name == "run"
            else 0.055 if action_name == "dance"
            else 0.045
        )
        checks[action_name] = {
            "samples": samples,
            "minimum_clearance_m": round(min(clearances), 6),
            "maximum_clearance_m": round(max(clearances), 6),
            "pass": (
                min(clearances) >= -0.035
                and max(clearances) <= maximum_clearance
            ),
        }
    return checks


def main():
    glb_path, report_path, preview_dir = parse_paths()
    if not os.path.exists(glb_path):
        raise FileNotFoundError(glb_path)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps = 30
    bpy.context.scene.render.fps_base = 1.0
    bpy.ops.import_scene.gltf(filepath=glb_path)
    importer_helpers = {
        obj
        for obj in bpy.context.scene.objects
        if any(collection.name == "glTF_not_exported" for collection in obj.users_collection)
    }
    meshes = [
        obj
        for obj in bpy.context.scene.objects
        if obj.type == "MESH" and obj not in importer_helpers
    ]
    armatures = [obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE"]
    cameras = [obj for obj in bpy.context.scene.objects if obj.type == "CAMERA"]
    lights = [obj for obj in bpy.context.scene.objects if obj.type == "LIGHT"]
    if len(armatures) != 1:
        raise RuntimeError("Expected exactly one imported armature")
    armature = armatures[0]
    actions = {action.name: action for action in bpy.data.actions}

    action_names_pass = set(actions) == set(EXPECTED_ACTIONS)
    durations = {}
    action_validation = {}
    root_checks = {}
    loop_checks = {}
    bounds_checks = {}
    for action_name, expected in EXPECTED_ACTIONS.items():
        action = actions.get(action_name)
        if action is None:
            continue
        start, end = action.frame_range
        duration = float(end - start) / float(bpy.context.scene.render.fps)
        durations[action_name] = {
            "start_time_seconds": round(float(start) / float(bpy.context.scene.render.fps), 6),
            "end_time_seconds": round(float(end) / float(bpy.context.scene.render.fps), 6),
            "duration_seconds": round(duration, 6),
            "expected_seconds": round(float(expected["duration"]), 6),
        }
        durations[action_name]["pass"] = abs(duration - expected["duration"]) <= 1.0 / 30.0
        action_validation[action_name] = action_finite(action)
        root_checks[action_name] = root_motion_check(armature, action)
        loop_checks[action_name] = (
            loop_check(armature, action)
            if expected["loop"]
            else {"pass": True, "skipped": "one-shot"}
        )

        assign_action(armature, action)
        sampled_bounds = []
        for fraction in (0.0, 0.5, 1.0):
            sample_fraction(armature, action, fraction)
            stats = evaluated_stats(meshes)
            sampled_bounds.append(stats)
        bounds_checks[action_name] = {
            "samples": sampled_bounds,
            "all_finite": all(item["finite"] for item in sampled_bounds),
        }
        bounds_checks[action_name]["pass"] = bounds_checks[action_name]["all_finite"]

    pose_checks = (
        action_pose_checks(armature, actions, meshes)
        if action_names_pass
        else {}
    )
    ground_checks = (
        ground_contact_checks(armature, actions, meshes)
        if action_names_pass
        else {}
    )
    reset_pose(armature)
    previews = render_previews(armature, actions, preview_dir) if action_names_pass else {}

    scene_scope = {
        "mesh_count": len(meshes),
        "armature_count": len(armatures),
        "bone_count": len(armature.data.bones),
        "camera_count": len(cameras),
        "light_count": len(lights),
        "importer_helper_count": len(importer_helpers),
    }
    scene_scope["pass"] = (
        len(meshes) == 121
        and len(armatures) == 1
        and len(armature.data.bones) == 56
        and not cameras
        and not lights
    )

    pose_checks_pass = bool(pose_checks) and all(
        (
            all(item["pass"] for item in value.values())
            if isinstance(value, dict) and all(isinstance(child, dict) for child in value.values())
            else value["pass"]
        )
        for value in pose_checks.values()
    )
    report = {
        "glb_path": glb_path,
        "glb_sha256": sha256_file(glb_path),
        "glb_size_bytes": os.path.getsize(glb_path),
        "blender_version": bpy.app.version_string,
        "scene_scope": scene_scope,
        "action_names": sorted(actions),
        "action_names_pass": action_names_pass,
        "durations": durations,
        "actions": action_validation,
        "root_motion": root_checks,
        "loop_checks": loop_checks,
        "bounds": bounds_checks,
        "pose_checks": pose_checks,
        "ground_contact": ground_checks,
        "previews": previews,
    }
    report["pass"] = (
        action_names_pass
        and scene_scope["pass"]
        and all(item["pass"] for item in durations.values())
        and all(item["pass"] for item in action_validation.values())
        and all(item["pass"] for item in root_checks.values())
        and all(item["pass"] for item in loop_checks.values())
        and all(item["pass"] for item in bounds_checks.values())
        and pose_checks_pass
        and all(item["pass"] for item in ground_checks.values())
        and len(previews) == len(EXPECTED_ACTIONS)
    )

    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    print("CHARACTER_ANIMATION_AUDIT_COMPLETE", report_path)
    print(json.dumps(
        {
            "pass": report["pass"],
            "action_names": sorted(actions),
            "scene_scope": scene_scope,
            "durations": durations,
            "loop_checks": loop_checks,
            "pose_checks": pose_checks,
            "ground_contact": ground_checks,
            "previews": previews,
        },
        ensure_ascii=False,
        indent=2,
    ))


if __name__ == "__main__":
    main()
