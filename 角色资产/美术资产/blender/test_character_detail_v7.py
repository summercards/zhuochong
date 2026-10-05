import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector


ROOT = os.path.abspath(os.path.dirname(__file__))
DEFAULT_GLB = os.path.join(ROOT, "business_man_tpose_v7.glb")
DEFAULT_REPORT = os.path.join(ROOT, "CHARACTER_DETAIL_AUDIT_V7.json")
DEFAULT_FACE = os.path.join(ROOT, "business_man_tpose_v7_face_test.png")
DEFAULT_HAND_L = os.path.join(ROOT, "business_man_tpose_v7_hand_L_test.png")
DEFAULT_HAND_R = os.path.join(ROOT, "business_man_tpose_v7_hand_R_test.png")

FINGER_DIGITS = (
    ("index", 1),
    ("middle", 2),
    ("ring", 3),
    ("pinky", 4),
)
GLASSES_OBJECTS = (
    "Glasses_Bridge",
    "Glasses_Frame_L",
    "Glasses_Frame_R",
    "Glasses_Lens_L",
    "Glasses_Lens_R",
    "Glasses_Temple_L",
    "Glasses_Temple_R",
)
FACE_BONES = {
    "jaw": ("Jaw", "Chin", "Lower_Lip", "Mouth_Line"),
    "upper_lip": ("Upper_Lip", "Mouth_Line"),
    "lower_lip": ("Lower_Lip", "Mouth_Line"),
    "glasses": GLASSES_OBJECTS,
    "eye.L": ("Eye_White_L", "Iris_L", "Pupil_L"),
    "eye.R": ("Eye_White_R", "Iris_R", "Pupil_R"),
}


def parse_paths():
    if "--" not in sys.argv:
        return DEFAULT_GLB, DEFAULT_REPORT, DEFAULT_FACE, DEFAULT_HAND_L, DEFAULT_HAND_R
    values = sys.argv[sys.argv.index("--") + 1 :]
    if len(values) != 5:
        raise ValueError(
            "Expected GLB, report, face preview, left hand preview, "
            "and right hand preview paths after --"
        )
    return tuple(os.path.abspath(value) for value in values)


def finite_vector(vector):
    return all(math.isfinite(float(value)) for value in vector)


def serializable_vector(vector):
    return [round(float(value), 6) for value in vector]


def evaluated_mesh_stats(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        if not mesh.vertices:
            raise RuntimeError("Mesh has no vertices: " + obj.name)
        points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
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
        center = sum(points, Vector((0.0, 0.0, 0.0))) / len(points)
        finite = all(finite_vector(point) for point in points)
        return {
            "center": center,
            "minimum": minimum,
            "maximum": maximum,
            "finite": finite,
        }
    finally:
        evaluated.to_mesh_clear()


def evaluated_max_displacement(obj, baseline_points):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
        if len(points) != len(baseline_points):
            raise RuntimeError("Evaluated vertex count changed: " + obj.name)
        distances = [
            (point - baseline).length
            for point, baseline in zip(points, baseline_points)
        ]
        return max(distances), all(finite_vector(point) for point in points)
    finally:
        evaluated.to_mesh_clear()


def evaluated_points(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        return [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    finally:
        evaluated.to_mesh_clear()


def reset_pose(armature):
    for pose_bone in armature.pose.bones:
        pose_bone.matrix_basis = Matrix.Identity(4)
        pose_bone.rotation_mode = "XYZ"
    bpy.context.view_layer.update()


def set_rotation(armature, bone_name, axis, angle):
    pose_bone = armature.pose.bones[bone_name]
    pose_bone.rotation_mode = "XYZ"
    rotation = [0.0, 0.0, 0.0]
    rotation[axis] = angle
    pose_bone.rotation_euler = rotation


def set_location(armature, bone_name, axis, value):
    pose_bone = armature.pose.bones[bone_name]
    pose_bone.rotation_mode = "XYZ"
    location = [0.0, 0.0, 0.0]
    location[axis] = value
    pose_bone.location = location


def set_rotation_xyz(armature, bone_name, x=0.0, y=0.0, z=0.0):
    pose_bone = armature.pose.bones[bone_name]
    pose_bone.rotation_mode = "XYZ"
    pose_bone.rotation_euler = (x, y, z)


def choose_chain_curl(armature, chain, object_name, rest_center, target, angle):
    candidates = []
    for axis in (0, 1, 2):
        for sign in (-1.0, 1.0):
            reset_pose(armature)
            for bone_name in chain[:2]:
                set_rotation(armature, bone_name, axis, sign * angle)
            bpy.context.view_layer.update()
            posed_center = evaluated_mesh_stats(bpy.data.objects[object_name])["center"]
            score = (posed_center - target).length
            candidates.append(
                {
                    "axis": axis,
                    "sign": sign,
                    "score": score,
                    "center": posed_center,
                }
            )
    reset_pose(armature)
    chosen = min(candidates, key=lambda item: (item["score"], item["axis"], item["sign"]))
    return {
        "axis": chosen["axis"],
        "sign": chosen["sign"],
        "angle": angle,
        "target_distance": chosen["score"],
        "rest_target_distance": (rest_center - target).length,
        "candidate_count": len(candidates),
    }


def apply_incremental_pose(armature, selected_curls):
    reset_pose(armature)
    set_rotation(armature, "jaw", 0, math.radians(30.0))
    set_location(armature, "upper_lip", 1, 0.006)
    set_location(armature, "lower_lip", 1, 0.010)
    set_rotation_xyz(armature, "glasses", x=math.radians(4.0), z=math.radians(-5.0))
    set_rotation(armature, "eye.L", 2, math.radians(20.0))
    set_rotation(armature, "eye.R", 2, math.radians(20.0))
    for chain, curl in selected_curls:
        for bone_name in chain[:2]:
            set_rotation(
                armature,
                bone_name,
                curl["axis"],
                curl["sign"] * curl["angle"],
            )
    bpy.context.view_layer.update()


def apply_speech_preview_pose(armature, selected_curls):
    reset_pose(armature)
    set_rotation(armature, "jaw", 0, math.radians(6.0))
    set_location(armature, "upper_lip", 1, 0.004)
    set_location(armature, "lower_lip", 1, 0.007)
    set_rotation_xyz(armature, "glasses", x=math.radians(2.0), z=math.radians(-3.0))
    set_rotation(armature, "eye.L", 2, math.radians(8.0))
    set_rotation(armature, "eye.R", 2, math.radians(8.0))
    for chain, curl in selected_curls:
        for bone_name in chain[:2]:
            set_rotation(
                armature,
                bone_name,
                curl["axis"],
                curl["sign"] * curl["angle"],
            )
    bpy.context.view_layer.update()


def check_weight_coverage(obj, allowed_bones):
    index_to_name = {
        group.index: group.name
        for group in obj.vertex_groups
    }
    max_error = 0.0
    unexpected = set()
    negative = 0
    for vertex in obj.data.vertices:
        total = 0.0
        for assignment in vertex.groups:
            name = index_to_name[assignment.group]
            if name not in allowed_bones:
                unexpected.add(name)
            if assignment.weight < 0.0:
                negative += 1
            total += assignment.weight
        max_error = max(max_error, abs(total - 1.0))
    return {
        "max_abs_weight_sum_error": round(max_error, 8),
        "unexpected_groups": sorted(unexpected),
        "negative_assignments": negative,
        "pass": max_error <= 0.0001 and not unexpected and negative == 0,
    }


def add_presentation():
    bpy.ops.object.camera_add(location=(0.0, -1.0, 1.7))
    camera = bpy.context.object
    camera.name = "Detail_Test_Camera"
    camera.data.type = "ORTHO"
    bpy.context.scene.camera = camera

    for name, location, energy, size in (
        ("Detail_Test_Key", (-1.2, -2.0, 2.7), 850.0, 1.7),
        ("Detail_Test_Fill", (1.6, -1.0, 1.9), 500.0, 1.3),
        ("Detail_Test_Rim", (0.4, 1.8, 2.5), 700.0, 1.2),
    ):
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.name = name
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        light.rotation_euler = (
            Vector((0.0, -0.03, 1.53)) - light.location
        ).to_track_quat("-Z", "Y").to_euler()

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 1100
    scene.render.resolution_y = 1100
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    if scene.world is None:
        scene.world = bpy.data.worlds.new("Detail Test World")
    scene.world.color = (0.018, 0.024, 0.035)
    return camera


def render_view(camera, output_path, location, target, ortho_scale):
    camera.location = location
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = ortho_scale
    camera.rotation_euler = (
        Vector(target) - camera.location
    ).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)


def main():
    (
        glb_path,
        report_path,
        face_preview,
        hand_l_preview,
        hand_r_preview,
    ) = parse_paths()
    if not os.path.exists(glb_path):
        raise FileNotFoundError(glb_path)

    bpy.ops.wm.read_factory_settings(use_empty=True)
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
    if len(armatures) != 1:
        raise RuntimeError("Expected exactly one armature")
    armature = armatures[0]
    if len(armature.data.bones) != 56:
        raise RuntimeError("Expected 56 bones, found %d" % len(armature.data.bones))

    reset_pose(armature)
    target_objects = set()
    for names in FACE_BONES.values():
        target_objects.update(names)
    for side in ("L", "R"):
        for _, digit_number in FINGER_DIGITS:
            target_objects.add("Finger_%s_%d" % (side, digit_number))
            target_objects.add("Knuckle_%s_%d" % (side, digit_number))
        target_objects.add("Thumb_" + side)
        target_objects.add("Thumb_Tip_" + side)

    rest_points = {
        object_name: evaluated_points(bpy.data.objects[object_name])
        for object_name in target_objects
    }
    rest_centers = {
        object_name: sum(points, Vector((0.0, 0.0, 0.0))) / len(points)
        for object_name, points in rest_points.items()
    }

    selected_curls = []
    for side in ("L", "R"):
        sign = 1.0 if side == "L" else -1.0
        for digit_name, digit_number in FINGER_DIGITS:
            chain = [
                "finger_%s_%02d.%s" % (digit_name, index, side)
                for index in range(1, 4)
            ]
            object_name = "Finger_%s_%d" % (side, digit_number)
            target = Vector((sign * 0.835, rest_centers[object_name].y, 1.397))
            selected_curls.append(
                (
                    chain,
                    choose_chain_curl(
                        armature,
                        chain,
                        object_name,
                        rest_centers[object_name],
                        target,
                        math.radians(38.0),
                    ),
                )
            )

        thumb_chain = ["thumb_%02d.%s" % (index, side) for index in range(1, 4)]
        thumb_object = "Thumb_" + side
        thumb_target = Vector((sign * 0.816, -0.052, 1.438))
        selected_curls.append(
            (
                thumb_chain,
                choose_chain_curl(
                    armature,
                    thumb_chain,
                    thumb_object,
                    rest_centers[thumb_object],
                    thumb_target,
                    math.radians(28.0),
                ),
            )
        )

    reset_pose(armature)
    set_location(armature, "upper_lip", 1, 0.006)
    bpy.context.view_layer.update()
    upper_lip_rotation_points = rest_points["Upper_Lip"]
    upper_lip_control = {
        "local_y_translation_m": 0.006,
        "center_delta_z_m": round(
            float(
                evaluated_mesh_stats(bpy.data.objects["Upper_Lip"])["center"].z
                - rest_centers["Upper_Lip"].z
            ),
            6,
        ),
        "max_vertex_displacement_m": round(
            float(
                evaluated_max_displacement(
                    bpy.data.objects["Upper_Lip"],
                    upper_lip_rotation_points,
                )[0]
            ),
            6,
        ),
    }
    upper_lip_control["pass"] = (
        upper_lip_control["center_delta_z_m"] >= 0.004
        and upper_lip_control["max_vertex_displacement_m"] >= 0.004
    )

    reset_pose(armature)
    set_location(armature, "lower_lip", 1, 0.010)
    bpy.context.view_layer.update()
    lower_lip_control = {
        "local_y_translation_m": 0.010,
        "center_delta_z_m": round(
            float(
                evaluated_mesh_stats(bpy.data.objects["Lower_Lip"])["center"].z
                - rest_centers["Lower_Lip"].z
            ),
            6,
        ),
        "max_vertex_displacement_m": round(
            float(
                evaluated_max_displacement(
                    bpy.data.objects["Lower_Lip"],
                    rest_points["Lower_Lip"],
                )[0]
            ),
            6,
        ),
    }
    lower_lip_control["pass"] = (
        lower_lip_control["center_delta_z_m"] <= -0.007
        and lower_lip_control["max_vertex_displacement_m"] >= 0.008
    )

    reset_pose(armature)
    set_rotation(armature, "upper_lip", 0, math.radians(12.0))
    bpy.context.view_layer.update()
    upper_lip_rotation = {
        "local_x_rotation_degrees": 12.0,
        "max_vertex_displacement_m": round(
            float(
                evaluated_max_displacement(
                    bpy.data.objects["Upper_Lip"],
                    rest_points["Upper_Lip"],
                )[0]
            ),
            6,
        ),
    }
    upper_lip_rotation["pass"] = upper_lip_rotation["max_vertex_displacement_m"] >= 0.0005

    reset_pose(armature)
    set_rotation(armature, "lower_lip", 0, math.radians(12.0))
    bpy.context.view_layer.update()
    lower_lip_rotation = {
        "local_x_rotation_degrees": 12.0,
        "max_vertex_displacement_m": round(
            float(
                evaluated_max_displacement(
                    bpy.data.objects["Lower_Lip"],
                    rest_points["Lower_Lip"],
                )[0]
            ),
            6,
        ),
    }
    lower_lip_rotation["pass"] = lower_lip_rotation["max_vertex_displacement_m"] >= 0.0005

    reset_pose(armature)
    set_rotation_xyz(
        armature,
        "glasses",
        x=math.radians(8.0),
        z=math.radians(10.0),
    )
    bpy.context.view_layer.update()
    glasses_posed_centers = {
        object_name: evaluated_mesh_stats(bpy.data.objects[object_name])["center"]
        for object_name in GLASSES_OBJECTS
    }
    rest_pair_distances = {}
    posed_pair_distances = {}
    for index, left_name in enumerate(GLASSES_OBJECTS):
        for right_name in GLASSES_OBJECTS[index + 1 :]:
            pair = (left_name, right_name)
            rest_pair_distances[pair] = (
                rest_centers[left_name] - rest_centers[right_name]
            ).length
            posed_pair_distances[pair] = (
                glasses_posed_centers[left_name] - glasses_posed_centers[right_name]
            ).length
    glasses_rigid_error = max(
        abs(posed_pair_distances[pair] - rest_pair_distances[pair])
        for pair in rest_pair_distances
    )
    glasses_max_displacement = max(
        evaluated_max_displacement(
            bpy.data.objects[object_name],
            rest_points[object_name],
        )[0]
        for object_name in GLASSES_OBJECTS
    )
    glasses_control = {
        "rotation_degrees": {"x": 8.0, "z": 10.0},
        "max_vertex_displacement_m": round(float(glasses_max_displacement), 6),
        "max_pairwise_distance_error_m": round(float(glasses_rigid_error), 8),
        "all_finite": all(
            evaluated_mesh_stats(bpy.data.objects[object_name])["finite"]
            for object_name in GLASSES_OBJECTS
        ),
    }
    glasses_control["pass"] = (
        glasses_control["max_vertex_displacement_m"] >= 0.003
        and glasses_control["max_pairwise_distance_error_m"] <= 0.00001
        and glasses_control["all_finite"]
    )

    apply_incremental_pose(armature, selected_curls)

    object_checks = {}
    for object_name in sorted(target_objects):
        obj = bpy.data.objects[object_name]
        displacement, finite = evaluated_max_displacement(obj, rest_points[object_name])
        center = evaluated_mesh_stats(obj)["center"]
        object_checks[object_name] = {
            "center_displacement_m": round(
                float((center - rest_centers[object_name]).length),
                6,
            ),
            "max_vertex_displacement_m": round(float(displacement), 6),
            "finite": finite,
        }

    posed_centers = {
        object_name: evaluated_mesh_stats(bpy.data.objects[object_name])["center"]
        for object_name in ("Upper_Lip", "Lower_Lip", "Mouth_Line")
    }
    rest_lip_gap = rest_centers["Upper_Lip"].z - rest_centers["Lower_Lip"].z
    posed_lip_gap = posed_centers["Upper_Lip"].z - posed_centers["Lower_Lip"].z
    mouth_line_rest_points = rest_points["Mouth_Line"]
    ordered_indices = sorted(
        range(len(mouth_line_rest_points)),
        key=lambda index: mouth_line_rest_points[index].z,
    )
    band_size = max(1, len(ordered_indices) // 4)
    lower_band = ordered_indices[:band_size]
    upper_band = ordered_indices[-band_size:]
    mouth_line_posed_points = evaluated_points(bpy.data.objects["Mouth_Line"])
    rest_line_gap = (
        sum(mouth_line_rest_points[index].z for index in upper_band) / len(upper_band)
        - sum(mouth_line_rest_points[index].z for index in lower_band) / len(lower_band)
    )
    posed_line_gap = (
        sum(mouth_line_posed_points[index].z for index in upper_band) / len(upper_band)
        - sum(mouth_line_posed_points[index].z for index in lower_band) / len(lower_band)
    )
    mouth_speech_control = {
        "pose": {
            "jaw_rotation_degrees": 30.0,
            "upper_lip_local_y_translation_m": 0.006,
            "lower_lip_local_y_translation_m": 0.010,
        },
        "rest_lip_center_gap_m": round(float(rest_lip_gap), 6),
        "posed_lip_center_gap_m": round(float(posed_lip_gap), 6),
        "lip_center_gap_increase_m": round(float(posed_lip_gap - rest_lip_gap), 6),
        "rest_mouth_line_band_gap_m": round(float(rest_line_gap), 6),
        "posed_mouth_line_band_gap_m": round(float(posed_line_gap), 6),
        "mouth_line_band_gap_increase_m": round(float(posed_line_gap - rest_line_gap), 6),
    }
    mouth_speech_control["pass"] = (
        mouth_speech_control["lip_center_gap_increase_m"] >= 0.006
        and mouth_speech_control["mouth_line_band_gap_increase_m"] >= 0.003
        and all(item["finite"] for item in object_checks.values())
    )

    face_checks = {}
    for bone_name, object_names in FACE_BONES.items():
        face_checks[bone_name] = {
            "objects": object_names,
            "max_center_displacement_m": max(
                object_checks[object_name]["center_displacement_m"]
                for object_name in object_names
            ),
            "all_finite": all(
                object_checks[object_name]["finite"]
                for object_name in object_names
            ),
        }

    weight_checks = {}
    fixed_weight_groups = {
        "Jaw": {"jaw"},
        "Chin": {"jaw"},
        "Upper_Lip": {"upper_lip"},
        "Lower_Lip": {"lower_lip"},
        "Mouth_Line": {"upper_lip", "lower_lip"},
        "Eye_White_L": {"eye.L"},
        "Iris_L": {"eye.L"},
        "Pupil_L": {"eye.L"},
        "Eye_White_R": {"eye.R"},
        "Iris_R": {"eye.R"},
        "Pupil_R": {"eye.R"},
    }
    for object_name in GLASSES_OBJECTS:
        fixed_weight_groups[object_name] = {"glasses"}
    for object_name, allowed_bones in fixed_weight_groups.items():
        detail = check_weight_coverage(
            bpy.data.objects[object_name],
            allowed_bones,
        )
        weight_checks[object_name] = {
            "allowed_bones": sorted(allowed_bones),
            "pass": detail["pass"],
            "detail": detail,
        }
    for side in ("L", "R"):
        for digit_name, digit_number in FINGER_DIGITS:
            chain = [
                "finger_%s_%02d.%s" % (digit_name, index, side)
                for index in range(1, 4)
            ]
            weight_checks["Finger_%s_%d" % (side, digit_number)] = {
                "pass": check_weight_coverage(
                    bpy.data.objects["Finger_%s_%d" % (side, digit_number)],
                    set(chain),
                )["pass"],
                "detail": check_weight_coverage(
                    bpy.data.objects["Finger_%s_%d" % (side, digit_number)],
                    set(chain),
                ),
            }
            weight_checks["Knuckle_%s_%d" % (side, digit_number)] = {
                "pass": check_weight_coverage(
                    bpy.data.objects["Knuckle_%s_%d" % (side, digit_number)],
                    {chain[0]},
                )["pass"],
                "detail": check_weight_coverage(
                    bpy.data.objects["Knuckle_%s_%d" % (side, digit_number)],
                    {chain[0]},
                ),
            }
        thumb_chain = ["thumb_%02d.%s" % (index, side) for index in range(1, 4)]
        for object_name in ("Thumb_" + side, "Thumb_Tip_" + side):
            weight_checks[object_name] = {
                "pass": check_weight_coverage(
                    bpy.data.objects[object_name],
                    set(thumb_chain),
                )["pass"],
                "detail": check_weight_coverage(
                    bpy.data.objects[object_name],
                    set(thumb_chain),
                ),
            }

    jaw_pass = all(
        item["max_vertex_displacement_m"] >= 0.002 and item["finite"]
        for name, item in object_checks.items()
        if name in FACE_BONES["jaw"]
    )
    eye_pass = True
    for object_name in (
        "Eye_White_L",
        "Iris_L",
        "Pupil_L",
        "Eye_White_R",
        "Iris_R",
        "Pupil_R",
    ):
        displacement = object_checks[object_name]["center_displacement_m"]
        eye_pass = eye_pass and 0.003 <= displacement <= 0.04
        eye_pass = eye_pass and object_checks[object_name]["finite"]

    finger_checks = {}
    finger_pass = True
    for side in ("L", "R"):
        for digit_name, digit_number in FINGER_DIGITS:
            object_name = "Finger_%s_%d" % (side, digit_number)
            max_displacement = object_checks[object_name]["max_vertex_displacement_m"]
            passed = 0.003 <= max_displacement <= 0.2 and object_checks[object_name]["finite"]
            finger_checks[object_name] = {
                "max_vertex_displacement_m": max_displacement,
                "finite": object_checks[object_name]["finite"],
                "pass": passed,
            }
            finger_pass = finger_pass and passed
        for object_name in ("Thumb_" + side, "Thumb_Tip_" + side):
            max_displacement = object_checks[object_name]["max_vertex_displacement_m"]
            passed = 0.002 <= max_displacement <= 0.2 and object_checks[object_name]["finite"]
            finger_checks[object_name] = {
                "max_vertex_displacement_m": max_displacement,
                "finite": object_checks[object_name]["finite"],
                "pass": passed,
            }
            finger_pass = finger_pass and passed

    weight_pass = all(item["pass"] for item in weight_checks.values())
    lip_pass = (
        upper_lip_control["pass"]
        and lower_lip_control["pass"]
        and upper_lip_rotation["pass"]
        and lower_lip_rotation["pass"]
    )
    camera = add_presentation()
    apply_speech_preview_pose(armature, selected_curls)
    render_view(
        camera,
        face_preview,
        (0.24, -0.58, 1.79),
        (0.0, -0.065, 1.715),
        0.30,
    )
    render_view(
        camera,
        hand_l_preview,
        (0.94, -0.42, 1.62),
        (0.895, -0.015, 1.435),
        0.29,
    )
    render_view(
        camera,
        hand_r_preview,
        (-0.94, -0.42, 1.62),
        (-0.895, -0.015, 1.435),
        0.29,
    )

    report = {
        "glb_path": glb_path,
        "bone_count": len(armature.data.bones),
        "previews": {
            "face": face_preview,
            "left_hand": hand_l_preview,
            "right_hand": hand_r_preview,
        },
        "pose": {
            "stress_pose": {
                "jaw_rotation_degrees": 30.0,
                "upper_lip_local_y_translation_m": 0.006,
                "lower_lip_local_y_translation_m": 0.010,
            },
            "preview_pose": {
                "jaw_rotation_degrees": 6.0,
                "upper_lip_local_y_translation_m": 0.004,
                "lower_lip_local_y_translation_m": 0.007,
            },
            "eye_rotation_degrees": 20.0,
            "selected_curls": [
                {
                    "bones": chain,
                    "axis_index": curl["axis"],
                    "sign": curl["sign"],
                    "angle_degrees": round(math.degrees(curl["angle"]), 6),
                    "target_distance_m": round(curl["target_distance"], 6),
                    "rest_target_distance_m": round(curl["rest_target_distance"], 6),
                }
                for chain, curl in selected_curls
            ],
        },
        "face_checks": face_checks,
        "lip_controls": {
            "upper_lip_translation": upper_lip_control,
            "lower_lip_translation": lower_lip_control,
            "upper_lip_rotation": upper_lip_rotation,
            "lower_lip_rotation": lower_lip_rotation,
            "combined_speech_pose": mouth_speech_control,
        },
        "glasses_control": glasses_control,
        "finger_checks": finger_checks,
        "weight_checks": weight_checks,
        "object_checks": object_checks,
        "pass": (
            jaw_pass
            and eye_pass
            and finger_pass
            and weight_pass
            and lip_pass
            and mouth_speech_control["pass"]
            and glasses_control["pass"]
        ),
    }
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    print("CHARACTER_DETAIL_AUDIT_COMPLETE", report_path)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
