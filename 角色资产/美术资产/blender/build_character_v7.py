import math
import os

import bpy
from mathutils import Vector


ROOT = os.path.abspath(os.path.dirname(__file__))
V6_BLEND = os.path.join(ROOT, "business_man_tpose_v6.blend")
V7_BLEND = os.path.join(ROOT, "business_man_tpose_v7.blend")
V7_GLB = os.path.join(ROOT, "business_man_tpose_v7.glb")
FRONT_PATH = os.path.join(ROOT, "business_man_tpose_v7_front.png")
SIDE_PATH = os.path.join(ROOT, "business_man_tpose_v7_side.png")
BACK_PATH = os.path.join(ROOT, "business_man_tpose_v7_back.png")

GLASSES_OBJECTS = (
    "Glasses_Bridge",
    "Glasses_Frame_L",
    "Glasses_Frame_R",
    "Glasses_Lens_L",
    "Glasses_Lens_R",
    "Glasses_Temple_L",
    "Glasses_Temple_R",
)


def clear_vertex_groups(obj):
    for group in list(obj.vertex_groups):
        obj.vertex_groups.remove(group)


def ensure_skin_modifier(obj, armature):
    modifier = next(
        (
            candidate
            for candidate in obj.modifiers
            if candidate.type == "ARMATURE"
        ),
        None,
    )
    if modifier is None:
        modifier = obj.modifiers.new("Character skin", "ARMATURE")
    modifier.object = armature
    modifier.use_deform_preserve_volume = True
    if obj.parent != armature:
        obj.parent = armature
        obj.matrix_parent_inverse = armature.matrix_world.inverted()


def set_rigid_weights(character, armature, object_name, bone_name):
    obj = character.objects[object_name]
    clear_vertex_groups(obj)
    group = obj.vertex_groups.new(name=bone_name)
    group.add([vertex.index for vertex in obj.data.vertices], 1.0, "REPLACE")
    ensure_skin_modifier(obj, armature)


def set_mouth_line_weights(character, armature):
    obj = character.objects["Mouth_Line"]
    clear_vertex_groups(obj)
    upper_group = obj.vertex_groups.new(name="upper_lip")
    lower_group = obj.vertex_groups.new(name="lower_lip")
    points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    minimum_z = min(point.z for point in points)
    maximum_z = max(point.z for point in points)
    span = max(maximum_z - minimum_z, 0.000001)

    for vertex, point in zip(obj.data.vertices, points):
        factor = max(0.0, min(1.0, (point.z - minimum_z) / span))
        smooth = factor * factor * (3.0 - 2.0 * factor)
        upper_weight = smooth
        lower_weight = 1.0 - smooth
        if upper_weight > 0.000001:
            upper_group.add([vertex.index], upper_weight, "REPLACE")
        if lower_weight > 0.000001:
            lower_group.add([vertex.index], lower_weight, "REPLACE")

    ensure_skin_modifier(obj, armature)


def add_bone(edit_bones, name, head, tail, parent=None, connected=False):
    if name in edit_bones:
        raise RuntimeError("Bone already exists: " + name)
    bone = edit_bones.new(name)
    bone.head = head
    bone.tail = tail
    bone.use_deform = True
    bone.roll = 0.0
    if parent is not None:
        bone.parent = edit_bones[parent]
        bone.use_connect = connected
    return bone


def add_mouth_and_glasses_bones(armature):
    edit_bones = armature.data.edit_bones
    add_bone(
        edit_bones,
        "upper_lip",
        (0.0, -0.088, 1.669),
        (0.0, -0.088, 1.689),
        parent="head",
    )
    add_bone(
        edit_bones,
        "lower_lip",
        (0.0, -0.088, 1.663),
        (0.0, -0.088, 1.643),
        parent="jaw",
    )
    add_bone(
        edit_bones,
        "glasses",
        (0.0, -0.086, 1.742),
        (0.0, -0.086, 1.762),
        parent="head",
    )


def bind_mouth_and_glasses(character, armature):
    set_rigid_weights(character, armature, "Upper_Lip", "upper_lip")
    set_rigid_weights(character, armature, "Lower_Lip", "lower_lip")
    set_mouth_line_weights(character, armature)
    for object_name in GLASSES_OBJECTS:
        set_rigid_weights(character, armature, object_name, "glasses")


def render_view(camera, output_path, location, target, ortho_scale):
    camera.location = location
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = ortho_scale
    camera.rotation_euler = (
        Vector(target) - camera.location
    ).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)


def export_character(character, armature):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in character.objects:
        if obj.type in {"MESH", "ARMATURE"}:
            obj.select_set(True)
    bpy.context.view_layer.objects.active = armature
    bpy.ops.export_scene.gltf(
        filepath=V7_GLB,
        export_format="GLB",
        use_selection=True,
        export_yup=True,
        export_apply=True,
        export_skins=True,
        export_animations=False,
        export_cameras=False,
        export_lights=False,
    )


def main():
    if not os.path.exists(V6_BLEND):
        raise FileNotFoundError(V6_BLEND)
    bpy.ops.wm.open_mainfile(filepath=V6_BLEND)

    character = bpy.data.collections.get("CHARACTER")
    if character is None:
        raise RuntimeError("CHARACTER collection is missing")
    armature = bpy.data.objects.get("Character_Rig")
    if armature is None or armature.type != "ARMATURE":
        raise RuntimeError("Character_Rig armature is missing")
    if len(armature.data.bones) != 53:
        raise RuntimeError(
            "Expected v6 armature with 53 bones, found %d"
            % len(armature.data.bones)
        )

    bpy.ops.object.select_all(action="DESELECT")
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode="EDIT")
    add_mouth_and_glasses_bones(armature)
    bpy.ops.object.mode_set(mode="OBJECT")

    bind_mouth_and_glasses(character, armature)
    for bone_name in ("upper_lip", "lower_lip", "glasses"):
        armature.pose.bones[bone_name].rotation_mode = "XYZ"

    armature["rig_profile"] = "v7 independent lips and glasses rig"
    armature["jaw_bone"] = "jaw"
    armature["upper_lip_bone"] = "upper_lip"
    armature["lower_lip_bone"] = "lower_lip"
    armature["glasses_bone"] = "glasses"
    armature["eye_bones"] = "eye.L,eye.R"
    armature["finger_bones_per_hand"] = 15

    camera = bpy.data.objects["Presentation_Camera"]
    render_view(
        camera,
        FRONT_PATH,
        (0.0, -5.0, 0.97),
        (0.0, 0.0, 0.97),
        2.24,
    )
    render_view(
        camera,
        SIDE_PATH,
        (5.0, 0.0, 0.97),
        (0.0, 0.0, 0.97),
        2.12,
    )
    render_view(
        camera,
        BACK_PATH,
        (0.0, 5.0, 0.97),
        (0.0, 0.0, 0.97),
        2.24,
    )

    bpy.ops.wm.save_as_mainfile(filepath=V7_BLEND)
    export_character(character, armature)
    print(
        "CHARACTER_V7_COMPLETE",
        V7_BLEND,
        V7_GLB,
        "bones=%d" % len(armature.data.bones),
    )


if __name__ == "__main__":
    main()
