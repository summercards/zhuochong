import os
import sys

import bpy
from mathutils import Vector


def parse_paths():
    values = sys.argv[sys.argv.index("--") + 1 :]
    if len(values) != 3:
        raise ValueError("Expected GLB, action, and frame after --")
    return os.path.abspath(values[0]), values[1], int(values[2])


def evaluated_bounds(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
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
        return minimum, maximum
    finally:
        evaluated.to_mesh_clear()


def main():
    glb_path, action_name, frame = parse_paths()
    if glb_path.lower().endswith(".blend"):
        bpy.ops.wm.open_mainfile(filepath=glb_path)
    else:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.context.scene.render.fps = 30
        bpy.context.scene.render.fps_base = 1.0
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
    action = bpy.data.actions[action_name]
    armature.animation_data.action = action
    if armature.animation_data.action_slot is None and action.slots:
        armature.animation_data.action_slot = action.slots[0]
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()

    bounds = []
    for obj in meshes:
        minimum, maximum = evaluated_bounds(obj)
        bounds.append((minimum.z, maximum.z, obj.name))

    print("FRAME", frame, "ACTION", action_name)
    print("LOWEST MESHES")
    for minimum_z, maximum_z, name in sorted(bounds)[:15]:
        print(
            name,
            "min_z=%.6f" % minimum_z,
            "max_z=%.6f" % maximum_z,
        )
    print("HIGHEST MESHES")
    for minimum_z, maximum_z, name in sorted(
        bounds,
        key=lambda item: item[1],
        reverse=True,
    )[:15]:
        print(
            name,
            "min_z=%.6f" % minimum_z,
            "max_z=%.6f" % maximum_z,
        )

    print("KEY BONE WORLD POSITIONS")
    print(
        "hand_y",
        "L=%.6f" % float(armature.pose.bones["hand.L"].matrix.translation.y),
        "R=%.6f" % float(armature.pose.bones["hand.R"].matrix.translation.y),
    )
    for bone_name in (
        "root",
        "pelvis",
        "spine",
        "chest",
        "head",
        "upper_arm.L",
        "forearm.L",
        "hand.L",
        "upper_arm.R",
        "forearm.R",
        "hand.R",
        "thigh.L",
        "shin.L",
        "foot.L",
        "thigh.R",
        "shin.R",
        "foot.R",
    ):
        pose_bone = armature.pose.bones[bone_name]
        print(
            bone_name,
            "head=",
            tuple(round(float(value), 6) for value in pose_bone.matrix.translation),
            "tail=",
            tuple(
                round(float(value), 6)
                for value in pose_bone.matrix @ Vector(
                    (0.0, pose_bone.length, 0.0)
                )
            ),
        )


if __name__ == "__main__":
    main()
