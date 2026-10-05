import math
import os
import sys

import bpy
from mathutils import Vector


def parse_paths():
    values = sys.argv[sys.argv.index("--") + 1 :]
    if len(values) != 4:
        raise ValueError("Expected GLB, action, frame, and side after --")
    return os.path.abspath(values[0]), values[1], int(values[2]), values[3]


def evaluated_stats(meshes, side):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    all_points = []
    lowest = []
    shoe_minimum = None
    leg_minimum = None
    for obj in meshes:
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        try:
            points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
            minimum_z = min(point.z for point in points)
            maximum_z = max(point.z for point in points)
            all_points.extend(points)
            lowest.append((minimum_z, maximum_z, obj.name))
            if "Shoe_" + side in obj.name or obj.name == "Shoe_" + side:
                shoe_minimum = (
                    minimum_z
                    if shoe_minimum is None
                    else min(shoe_minimum, minimum_z)
                )
            if (
                "Trouser_Leg_" + side in obj.name
                or "Shoe_" + side in obj.name
                or obj.name == "Shoe_" + side
            ):
                leg_minimum = (
                    minimum_z
                    if leg_minimum is None
                    else min(leg_minimum, minimum_z)
                )
        finally:
            evaluated.to_mesh_clear()
    return {
        "minimum": Vector(
            (
                min(point.x for point in all_points),
                min(point.y for point in all_points),
                min(point.z for point in all_points),
            )
        ),
        "maximum": Vector(
            (
                max(point.x for point in all_points),
                max(point.y for point in all_points),
                max(point.z for point in all_points),
            )
        ),
        "lowest": sorted(lowest)[:6],
        "shoe_minimum": shoe_minimum,
        "leg_minimum": leg_minimum,
    }


def pose_summary(armature, meshes, side):
    bpy.context.view_layer.update()
    stats = evaluated_stats(meshes, side)
    summary = {
        "min_z": round(float(stats["minimum"].z), 6),
        "shoe_min_z": round(float(stats["shoe_minimum"]), 6),
        "leg_min_z": round(float(stats["leg_minimum"]), 6),
        "lowest": [
            (round(minimum_z, 5), name)
            for minimum_z, _maximum_z, name in stats["lowest"]
        ],
    }
    for bone_name in (
        "thigh." + side,
        "shin." + side,
        "foot." + side,
    ):
        pose_bone = armature.pose.bones[bone_name]
        summary[bone_name] = {
            "rotation": tuple(round(math.degrees(value), 3) for value in pose_bone.rotation_euler),
            "head": tuple(round(float(value), 4) for value in pose_bone.matrix.translation),
            "tail": tuple(
                round(float(value), 4)
                for value in pose_bone.matrix
                @ Vector((0.0, pose_bone.length, 0.0))
            ),
        }
    return summary


def main():
    glb_path, action_name, frame, side = parse_paths()
    overrides = {}
    if ";" in side or ":" in side:
        for entry in side.split(";"):
            entry_side, values = entry.split(":", 1)
            if entry_side not in {"L", "R"}:
                raise ValueError("Override side must be L or R")
            try:
                angles = tuple(float(value) for value in values.split(","))
            except ValueError as exc:
                raise ValueError(
                    "Override must be side:thigh,shin,foot"
                ) from exc
            if len(angles) != 3:
                raise ValueError(
                    "Override must have thigh, shin, and foot angles"
                )
            overrides[entry_side] = angles
        side = "B" if len(overrides) == 2 else next(iter(overrides))
    if side not in {"L", "R", "B", "W"}:
        raise ValueError(
            "Side must be L, R, B, W, or side:thigh,shin,foot[;side:...]"
        )
    if side == "B":
        print("READY")
    elif side == "W":
        return

    if overrides:
        single_override = (
            next(iter(overrides.values())) if len(overrides) == 1 else None
        )
    else:
        single_override = None
    if glb_path.lower().endswith(".blend"):
        bpy.ops.wm.open_mainfile(filepath=glb_path)
    else:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=glb_path)
    importer_helpers = {
        obj
        for obj in bpy.context.scene.objects
        if any(
            collection.name == "glTF_not_exported"
            for collection in obj.users_collection
        )
    }
    meshes = [
        obj
        for obj in bpy.context.scene.objects
        if obj.type == "MESH" and obj not in importer_helpers
    ]
    armature = next(
        obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE"
    )
    for obj in meshes:
        if obj.name in {
            "Shoe_Heel_L",
            "Shoe_Sole_L",
            "Shoe_L",
            "Trouser_Leg_L",
        }:
            group_counts = {}
            for vertex in obj.data.vertices:
                for assignment in vertex.groups:
                    group_name = obj.vertex_groups[assignment.group].name
                    group_counts[group_name] = group_counts.get(group_name, 0) + 1
            print(
                "WEIGHTS",
                obj.name,
                sorted(
                    group_counts.items(),
                    key=lambda item: item[1],
                    reverse=True,
                )[:12],
            )
    if side == "W":
        return
    action = bpy.data.actions[action_name]
    armature.animation_data.action = action
    if armature.animation_data.action_slot is None and action.slots:
        armature.animation_data.action_slot = action.slots[0]
    rotation_curves = {
        (fcurve.data_path, fcurve.array_index): fcurve
        for fcurve in action.fcurves
        if fcurve.data_path.endswith(".rotation_euler")
    }

    def curve_at_frame(bone_name, axis):
        data_path = 'pose.bones["%s"].rotation_euler' % bone_name
        fcurve = rotation_curves[(data_path, axis)]
        for point in fcurve.keyframe_points:
            if abs(float(point.co.x) - frame) <= 0.001:
                return fcurve, point
        raise RuntimeError("No rotation key at frame %s for %s" % (frame, bone_name))

    if single_override is not None:
        for bone_name, degrees_xyz in (
            ("thigh." + side, (single_override[0], 0.0, -10.0 if side == "L" else 12.0)),
            ("shin." + side, (single_override[1], 0.0, 0.0)),
            ("foot." + side, (single_override[2], 0.0, 0.0)),
        ):
            for axis, degrees in enumerate(degrees_xyz):
                fcurve, point = curve_at_frame(bone_name, axis)
                point.co.y = math.radians(degrees)
                fcurve.update()
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()
        print("SINGLE", side, single_override, pose_summary(armature, meshes, side))
        return

    if overrides:
        for override_side, angles in overrides.items():
            for bone_name, degrees_xyz in (
                (
                    "thigh." + override_side,
                    (
                        angles[0],
                        0.0,
                        -10.0 if override_side == "L" else 12.0,
                    ),
                ),
                ("shin." + override_side, (angles[1], 0.0, 0.0)),
                ("foot." + override_side, (angles[2], 0.0, 0.0)),
            ):
                for axis, degrees in enumerate(degrees_xyz):
                    fcurve, point = curve_at_frame(bone_name, axis)
                    point.co.y = math.radians(degrees)
                    fcurve.update()
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()
        print(
            "COMBINED",
            overrides,
            pose_summary(armature, meshes, "L"),
            pose_summary(armature, meshes, "R"),
        )
        return

    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()

    def evaluate(label, overrides, verbose=False):
        for bone_name, degrees_xyz in overrides.items():
            for axis, degrees in enumerate(degrees_xyz):
                fcurve, point = curve_at_frame(bone_name, axis)
                point.co.y = math.radians(degrees)
                fcurve.update()
        bpy.context.scene.frame_set(max(0, frame - 1))
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()
        summary = pose_summary(armature, meshes, side)
        if verbose:
            print("VARIANT", label, summary)
        return summary

    evaluate("current", {}, verbose=True)
    thigh_z = -10.0 if side == "L" else 12.0
    candidates = []
    candidate_index = 0
    for thigh_x in range(-40, 11, 5):
        for shin_x in range(-20, 121, 10):
            for foot_x in (-60, 0, 60):
                label = "thigh.x.%s.shin.x.%s.foot.x.%s" % (
                    thigh_x,
                    shin_x,
                    foot_x,
                )
                summary = evaluate(
                    label,
                    {
                        "thigh." + side: (float(thigh_x), 0.0, thigh_z),
                        "shin." + side: (float(shin_x), 0.0, 0.0),
                        "foot." + side: (float(foot_x), 0.0, 0.0),
                    },
                    verbose=candidate_index < 3,
                )
                candidate_index += 1
                candidates.append(
                    (
                        summary["min_z"],
                        summary["shoe_min_z"],
                        summary["leg_min_z"],
                        label,
                    )
                )
    print("RANKED CANDIDATES")
    ranked = sorted(
        candidates,
        key=lambda item: (
            abs(item[1] - 0.01),
            abs(item[0]),
        ),
    )
    for candidate in ranked[:30]:
        print("CANDIDATE", candidate)


if __name__ == "__main__":
    main()
