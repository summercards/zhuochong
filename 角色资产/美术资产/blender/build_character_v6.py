import math
import os

import bpy
from mathutils import Vector


ROOT = os.path.abspath(os.path.dirname(__file__))
V5_BLEND = os.path.join(ROOT, "business_man_tpose_v5.blend")
V6_BLEND = os.path.join(ROOT, "business_man_tpose_v6.blend")
V6_GLB = os.path.join(ROOT, "business_man_tpose_v6.glb")
FRONT_PATH = os.path.join(ROOT, "business_man_tpose_v6_front.png")
SIDE_PATH = os.path.join(ROOT, "business_man_tpose_v6_side.png")
BACK_PATH = os.path.join(ROOT, "business_man_tpose_v6_back.png")

FINGER_DIGITS = (
    ("index", 1),
    ("middle", 2),
    ("ring", 3),
    ("pinky", 4),
)
DIGIT_NAMES = {name: number for name, number in FINGER_DIGITS}


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


def point_segment_distance(point, start, end):
    segment = end - start
    length_squared = segment.length_squared
    if length_squared <= 0.00000001:
        return (point - start).length
    factor = max(0.0, min(1.0, (point - start).dot(segment) / length_squared))
    return (point - (start + segment * factor)).length


def set_chain_weights(character, armature, object_name, bone_names):
    obj = character.objects[object_name]
    clear_vertex_groups(obj)
    groups = {
        name: obj.vertex_groups.new(name=name)
        for name in bone_names
    }
    segments = []
    for name in bone_names:
        bone = armature.data.bones[name]
        segments.append(
            (
                name,
                armature.matrix_world @ bone.head_local,
                armature.matrix_world @ bone.tail_local,
            )
        )

    for vertex in obj.data.vertices:
        point = obj.matrix_world @ vertex.co
        distances = sorted(
            (
                point_segment_distance(point, start, end),
                name,
            )
            for name, start, end in segments
        )
        closest = distances[:2]
        if closest[0][0] < 0.00001 or closest[1][0] > closest[0][0] * 1.9:
            weights = [(closest[0][1], 1.0)]
        else:
            raw = [
                (1.0 / max(distance, 0.0002) ** 4.0, name)
                for distance, name in closest
            ]
            total = sum(weight for weight, _ in raw)
            weights = [(name, weight / total) for weight, name in raw]
        for bone_name, weight in weights:
            groups[bone_name].add([vertex.index], weight, "REPLACE")

    ensure_skin_modifier(obj, armature)


def bounds_center_at_extreme(obj, use_max_x):
    points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    values = [point.x for point in points]
    target = max(values) if use_max_x else min(values)
    selected = [point for point in points if abs(point.x - target) <= 0.004]
    return sum(selected, Vector((0.0, 0.0, 0.0))) / len(selected)


def finger_chain_points(character, side, digit_name, digit_number):
    sign = 1.0 if side == "L" else -1.0
    obj = character.objects["Finger_%s_%d" % (side, digit_number)]
    start = bounds_center_at_extreme(obj, use_max_x=False if side == "L" else True)
    end = bounds_center_at_extreme(obj, use_max_x=True if side == "L" else False)
    return [
        start,
        start.lerp(end, 1.0 / 3.0),
        start.lerp(end, 2.0 / 3.0),
        end,
    ]


def thumb_chain_points(side):
    sign = 1.0 if side == "L" else -1.0
    return [
        Vector((sign * 0.794, -0.061, 1.438)),
        Vector((sign * 0.823, -0.087, 1.421)),
        Vector((sign * 0.849, -0.086, 1.428)),
        Vector((sign * 0.858, -0.080, 1.437)),
    ]


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


def add_face_bones(armature):
    edit_bones = armature.data.edit_bones
    add_bone(
        edit_bones,
        "jaw",
        (0.0, 0.042, 1.699),
        (0.0, -0.055, 1.626),
        parent="head",
    )
    for side, sign in (("L", 1.0), ("R", -1.0)):
        add_bone(
            edit_bones,
            "eye." + side,
            (sign * 0.029, -0.050, 1.741),
            (sign * 0.029, -0.096, 1.741),
            parent="head",
        )


def add_finger_bones(character, armature):
    edit_bones = armature.data.edit_bones
    for side in ("L", "R"):
        for digit_name, digit_number in FINGER_DIGITS:
            points = finger_chain_points(
                character,
                side,
                digit_name,
                digit_number,
            )
            bone_names = []
            previous = "hand." + side
            for segment_index in range(3):
                name = "finger_%s_%02d.%s" % (
                    digit_name,
                    segment_index + 1,
                    side,
                )
                add_bone(
                    edit_bones,
                    name,
                    points[segment_index],
                    points[segment_index + 1],
                    parent=previous,
                    connected=segment_index > 0,
                )
                bone_names.append(name)
                previous = name

        points = thumb_chain_points(side)
        previous = "hand." + side
        for segment_index in range(3):
            name = "thumb_%02d.%s" % (segment_index + 1, side)
            add_bone(
                edit_bones,
                name,
                points[segment_index],
                points[segment_index + 1],
                parent=previous,
                connected=segment_index > 0,
            )
            previous = name


def bind_face(character, armature):
    for side in ("L", "R"):
        for prefix in ("Eye_White_", "Iris_", "Pupil_"):
            set_rigid_weights(
                character,
                armature,
                prefix + side,
                "eye." + side,
            )
    for object_name in ("Jaw", "Chin", "Lower_Lip", "Mouth_Line"):
        set_rigid_weights(
            character,
            armature,
            object_name,
            "jaw",
        )
    set_rigid_weights(character, armature, "Upper_Lip", "head")


def bind_fingers(character, armature):
    for side in ("L", "R"):
        for digit_name, digit_number in FINGER_DIGITS:
            chain = [
                "finger_%s_%02d.%s" % (digit_name, index, side)
                for index in range(1, 4)
            ]
            set_chain_weights(
                character,
                armature,
                "Finger_%s_%d" % (side, digit_number),
                chain,
            )
            set_rigid_weights(
                character,
                armature,
                "Knuckle_%s_%d" % (side, digit_number),
                chain[0],
            )

        thumb_chain = ["thumb_%02d.%s" % (index, side) for index in range(1, 4)]
        for object_name in ("Thumb_" + side, "Thumb_Tip_" + side):
            set_chain_weights(
                character,
                armature,
                object_name,
                thumb_chain,
            )


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
        filepath=V6_GLB,
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
    if not os.path.exists(V5_BLEND):
        raise FileNotFoundError(V5_BLEND)
    bpy.ops.wm.open_mainfile(filepath=V5_BLEND)

    character = bpy.data.collections.get("CHARACTER")
    if character is None:
        raise RuntimeError("CHARACTER collection is missing")
    armature = bpy.data.objects.get("Character_Rig")
    if armature is None or armature.type != "ARMATURE":
        raise RuntimeError("Character_Rig armature is missing")

    bpy.ops.object.select_all(action="DESELECT")
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode="EDIT")
    add_face_bones(armature)
    add_finger_bones(character, armature)
    bpy.ops.object.mode_set(mode="OBJECT")

    bind_face(character, armature)
    bind_fingers(character, armature)

    for bone_name in ("jaw", "eye.L", "eye.R"):
        armature.pose.bones[bone_name].rotation_mode = "XYZ"
    for side in ("L", "R"):
        for digit_name, _ in FINGER_DIGITS:
            for segment_index in range(1, 4):
                armature.pose.bones[
                    "finger_%s_%02d.%s"
                    % (digit_name, segment_index, side)
                ].rotation_mode = "XYZ"
        for segment_index in range(1, 4):
            armature.pose.bones[
                "thumb_%02d.%s" % (segment_index, side)
            ].rotation_mode = "XYZ"

    armature["rig_profile"] = "v6 face and finger rig"
    armature["jaw_bone"] = "jaw"
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

    bpy.ops.wm.save_as_mainfile(filepath=V6_BLEND)
    export_character(character, armature)
    print(
        "CHARACTER_V6_COMPLETE",
        V6_BLEND,
        V6_GLB,
        "bones=%d" % len(armature.data.bones),
    )


if __name__ == "__main__":
    main()
