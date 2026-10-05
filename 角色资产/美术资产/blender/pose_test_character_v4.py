import json
import math
import os
import sys

import bpy
from mathutils import Vector


ROOT = os.path.abspath(os.path.dirname(__file__))
GLB_PATH = os.path.join(ROOT, "business_man_tpose_v4.glb")
REPORT_PATH = os.path.join(ROOT, "CHARACTER_POSE_AUDIT_V4.json")
PREVIEW_PATH = os.path.join(ROOT, "business_man_tpose_v4_pose_test.png")


def parse_paths():
    if "--" not in sys.argv:
        return GLB_PATH, REPORT_PATH, PREVIEW_PATH
    values = sys.argv[sys.argv.index("--") + 1 :]
    if len(values) != 3:
        raise ValueError("Expected GLB, report, and preview paths after --")
    return tuple(os.path.abspath(value) for value in values)


def evaluated_bounds(meshes):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    minimum = Vector((float("inf"), float("inf"), float("inf")))
    maximum = Vector((float("-inf"), float("-inf"), float("-inf")))
    finite = True
    for obj in meshes:
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        try:
            for vertex in mesh.vertices:
                point = evaluated.matrix_world @ vertex.co
                finite = finite and all(math.isfinite(value) for value in point)
                minimum.x = min(minimum.x, point.x)
                minimum.y = min(minimum.y, point.y)
                minimum.z = min(minimum.z, point.z)
                maximum.x = max(maximum.x, point.x)
                maximum.y = max(maximum.y, point.y)
                maximum.z = max(maximum.z, point.z)
        finally:
            evaluated.to_mesh_clear()
    return minimum, maximum, finite


def add_presentation():
    bpy.ops.object.camera_add(location=(3.7, -5.2, 2.35))
    camera = bpy.context.object
    camera.name = "Pose_Test_Camera"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 2.42
    target = Vector((0.0, 0.0, 0.93))
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = camera

    for name, location, energy, size in (
        ("Pose_Test_Key", (-4.0, -4.0, 5.0), 1250.0, 4.0),
        ("Pose_Test_Fill", (4.0, -2.0, 3.0), 700.0, 3.5),
        ("Pose_Test_Rim", (1.5, 4.0, 4.0), 950.0, 3.0),
    ):
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.name = name
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        light.rotation_euler = (target - light.location).to_track_quat("-Z", "Y").to_euler()

    bpy.ops.mesh.primitive_plane_add(size=8.0, location=(0.0, 0.0, -0.002))
    ground = bpy.context.object
    ground.name = "Pose_Test_Ground"
    material = bpy.data.materials.new("Pose Test Ground")
    material.diffuse_color = (0.055, 0.065, 0.08, 1.0)
    ground.data.materials.append(material)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 1100
    scene.render.resolution_y = 1100
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = PREVIEW_PATH
    scene.render.film_transparent = False


def set_pose(armature):
    rotations = {
        "upper_arm.L": (math.radians(-18.0), math.radians(-22.0), math.radians(8.0)),
        "forearm.L": (math.radians(0.0), math.radians(-62.0), math.radians(12.0)),
        "hand.L": (math.radians(0.0), math.radians(-10.0), math.radians(0.0)),
        "upper_arm.R": (math.radians(16.0), math.radians(20.0), math.radians(-8.0)),
        "forearm.R": (math.radians(0.0), math.radians(58.0), math.radians(-10.0)),
        "thigh.L": (math.radians(-22.0), math.radians(4.0), math.radians(0.0)),
        "shin.L": (math.radians(35.0), math.radians(0.0), math.radians(0.0)),
        "thigh.R": (math.radians(14.0), math.radians(-3.0), math.radians(0.0)),
        "head": (math.radians(-8.0), math.radians(0.0), math.radians(12.0)),
        "spine": (math.radians(-7.0), math.radians(0.0), math.radians(0.0)),
        "chest": (math.radians(-8.0), math.radians(0.0), math.radians(0.0)),
    }
    for name, rotation in rotations.items():
        pose_bone = armature.pose.bones[name]
        pose_bone.rotation_mode = "XYZ"
        pose_bone.rotation_euler = rotation
    bpy.context.view_layer.update()


def main():
    global GLB_PATH, REPORT_PATH, PREVIEW_PATH
    GLB_PATH, REPORT_PATH, PREVIEW_PATH = parse_paths()
    if not os.path.exists(GLB_PATH):
        raise FileNotFoundError(GLB_PATH)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=GLB_PATH)
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

    rest_min, rest_max, rest_finite = evaluated_bounds(meshes)
    set_pose(armatures[0])
    posed_min, posed_max, posed_finite = evaluated_bounds(meshes)
    add_presentation()
    bpy.ops.render.render(write_still=True)

    report = {
        "glb_path": GLB_PATH,
        "preview_path": PREVIEW_PATH,
        "pose_checks": {
            "bones_rotated": [
                "upper_arm.L",
                "forearm.L",
                "hand.L",
                "upper_arm.R",
                "forearm.R",
                "thigh.L",
                "shin.L",
                "thigh.R",
                "head",
                "spine",
                "chest",
            ],
            "finite_geometry_rest": rest_finite,
            "finite_geometry_posed": posed_finite,
            "rest_bounds": {
                "min": [round(float(value), 6) for value in rest_min],
                "max": [round(float(value), 6) for value in rest_max],
            },
            "posed_bounds": {
                "min": [round(float(value), 6) for value in posed_min],
                "max": [round(float(value), 6) for value in posed_max],
            },
            "pass": rest_finite and posed_finite,
        },
    }
    with open(REPORT_PATH, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    print("CHARACTER_POSE_AUDIT_COMPLETE", REPORT_PATH)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
