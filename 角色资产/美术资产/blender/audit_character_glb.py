import hashlib
import json
import os
import sys
from datetime import datetime, timezone

import bpy
from mathutils import Vector


ROOT = os.path.abspath(os.path.dirname(__file__))
DEFAULT_GLB = os.path.join(ROOT, "business_man_tpose_v3.glb")
DEFAULT_REPORT = os.path.join(ROOT, "CHARACTER_AUDIT_V3.json")


def parse_paths():
    args = sys.argv
    if "--" not in args:
        return DEFAULT_GLB, DEFAULT_REPORT
    values = args[args.index("--") + 1 :]
    glb_path = os.path.abspath(values[0]) if values else DEFAULT_GLB
    report_path = os.path.abspath(values[1]) if len(values) > 1 else DEFAULT_REPORT
    return glb_path, report_path


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def world_bounds(objects):
    minimum = Vector((float("inf"), float("inf"), float("inf")))
    maximum = Vector((float("-inf"), float("-inf"), float("-inf")))
    for obj in objects:
        if obj.type != "MESH":
            continue
        for corner in obj.bound_box:
            point = obj.matrix_world @ Vector(corner)
            minimum.x = min(minimum.x, point.x)
            minimum.y = min(minimum.y, point.y)
            minimum.z = min(minimum.z, point.z)
            maximum.x = max(maximum.x, point.x)
            maximum.y = max(maximum.y, point.y)
            maximum.z = max(maximum.z, point.z)
    return minimum, maximum


def serializable_vector(vector):
    return [round(float(value), 6) for value in vector]


def main():
    glb_path, report_path = parse_paths()
    if not os.path.exists(glb_path):
        raise FileNotFoundError(glb_path)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=glb_path)

    objects = list(bpy.context.scene.objects)
    importer_helpers = [
        obj
        for obj in objects
        if any(collection.name == "glTF_not_exported" for collection in obj.users_collection)
    ]
    meshes = [
        obj
        for obj in objects
        if obj.type == "MESH" and obj not in importer_helpers
    ]
    armatures = [obj for obj in objects if obj.type == "ARMATURE"]
    cameras = [obj for obj in objects if obj.type == "CAMERA"]
    lights = [obj for obj in objects if obj.type == "LIGHT"]
    minimum, maximum = world_bounds(meshes)
    dimensions = maximum - minimum

    triangle_count = 0
    vertex_count = 0
    mesh_details = []
    forbidden_name_parts = (
        "presentation",
        "ground",
        "camera",
        "light",
        "tripo",
        "wheel",
    )
    forbidden_objects = []

    for obj in meshes:
        mesh = obj.data
        vertex_count += len(mesh.vertices)
        triangle_count += sum(max(1, len(poly.vertices) - 2) for poly in mesh.polygons)
        mesh_min, mesh_max = world_bounds([obj])
        mesh_details.append(
            {
                "name": obj.name,
                "vertices": len(mesh.vertices),
                "triangles": sum(max(1, len(poly.vertices) - 2) for poly in mesh.polygons),
                "min": serializable_vector(mesh_min),
                "max": serializable_vector(mesh_max),
                "modifiers": [modifier.type for modifier in obj.modifiers],
                "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
            }
        )
        if any(part in obj.name.lower() for part in forbidden_name_parts):
            forbidden_objects.append(obj.name)

    rigs = []
    t_pose_checks = []
    for armature in armatures:
        bones = []
        for bone in armature.data.bones:
            head_world = armature.matrix_world @ bone.head_local
            tail_world = armature.matrix_world @ bone.tail_local
            bones.append(
                {
                    "name": bone.name,
                    "parent": bone.parent.name if bone.parent else None,
                    "head": serializable_vector(head_world),
                    "tail": serializable_vector(tail_world),
                }
            )
            if bone.name.startswith(("upper_arm.", "forearm.", "hand.")):
                t_pose_checks.append(
                    {
                        "bone": bone.name,
                        "head_tail_z_delta": round(float(tail_world.z - head_world.z), 6),
                    }
                )
        rigs.append(
            {
                "object": armature.name,
                "data": armature.data.name,
                "location": serializable_vector(armature.location),
                "rotation_euler": serializable_vector(armature.rotation_euler),
                "scale": serializable_vector(armature.scale),
                "bone_count": len(bones),
                "bones": bones,
            }
        )

    material_names = sorted(
        {
            slot.material.name
            for obj in meshes
            for slot in obj.material_slots
            if slot.material is not None
        }
    )
    max_arm_z_delta = max(
        (abs(item["head_tail_z_delta"]) for item in t_pose_checks),
        default=None,
    )
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "glb_path": glb_path,
        "glb_sha256": sha256_file(glb_path),
        "blender_version": bpy.app.version_string,
        "scene": {
            "object_count": len(objects),
            "mesh_count": len(meshes),
            "armature_count": len(armatures),
            "camera_count": len(cameras),
            "light_count": len(lights),
            "importer_helper_count": len(importer_helpers),
            "importer_helpers": sorted(obj.name for obj in importer_helpers),
            "character_object_names": sorted(obj.name for obj in objects if obj not in importer_helpers),
        },
        "bounds": {
            "min": serializable_vector(minimum),
            "max": serializable_vector(maximum),
            "dimensions": serializable_vector(dimensions),
            "height_m": round(float(dimensions.z), 6),
        },
        "geometry": {
            "vertex_count": vertex_count,
            "triangle_count": triangle_count,
            "meshes": sorted(mesh_details, key=lambda item: item["name"]),
        },
        "materials": material_names,
        "rigs": rigs,
        "t_pose": {
            "checked_bones": t_pose_checks,
            "max_abs_head_tail_z_delta": max_arm_z_delta,
            "pass": max_arm_z_delta is not None and max_arm_z_delta <= 0.01,
        },
        "export_scope": {
            "forbidden_objects": forbidden_objects,
            "pass": (
                not cameras
                and not lights
                and not forbidden_objects
                and len(meshes) > 0
                and len(armatures) == 1
            ),
        },
    }

    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    print("CHARACTER_AUDIT_COMPLETE", report_path)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
