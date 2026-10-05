import os

import bpy
from mathutils import Vector


ROOT = os.path.abspath(os.path.dirname(__file__))
V4_BLEND = os.path.join(ROOT, "business_man_tpose_v4.blend")
V5_BLEND = os.path.join(ROOT, "business_man_tpose_v5.blend")
V5_GLB = os.path.join(ROOT, "business_man_tpose_v5.glb")
FRONT_PATH = os.path.join(ROOT, "business_man_tpose_v5_front.png")
SIDE_PATH = os.path.join(ROOT, "business_man_tpose_v5_side.png")
BACK_PATH = os.path.join(ROOT, "business_man_tpose_v5_back.png")


BONES = (
    "pelvis",
    "spine",
    "chest",
    "neck",
    "head",
    "clavicle.L",
    "upper_arm.L",
    "forearm.L",
    "hand.L",
    "clavicle.R",
    "upper_arm.R",
    "forearm.R",
    "hand.R",
    "thigh.L",
    "shin.L",
    "foot.L",
    "thigh.R",
    "shin.R",
    "foot.R",
)

HEAD_NAMES = {
    "Head",
    "Jaw",
    "Chin",
    "Nose",
    "Upper_Lip",
    "Lower_Lip",
    "Mouth_Line",
}
HEAD_PREFIXES = (
    "Ear_",
    "Eye_White_",
    "Eyebrow_",
    "Iris_",
    "Pupil_",
    "Face_Line_",
    "Glasses_",
    "Hair_",
    "Sideburn_",
)
HAND_PREFIXES = (
    "Shirt_Cuff_",
    "Palm_",
    "Finger_",
    "Thumb_",
    "Thumb_Tip_",
    "Knuckle_",
)
SHOE_PREFIXES = ("Shoe_",)
FOOT_ONLY_PREFIXES = ("Shoe_",)


def clamp(value, minimum=0.0, maximum=1.0):
    return max(minimum, min(maximum, value))


def mix(first, second, factor):
    factor = clamp(factor)
    if factor <= 0.000001:
        return [(first, 1.0)]
    if factor >= 0.999999:
        return [(second, 1.0)]
    return [(first, 1.0 - factor), (second, factor)]


def side_suffix(name):
    if name.endswith("_L") or "_L_" in name:
        return "L"
    if name.endswith("_R") or "_R_" in name:
        return "R"
    raise ValueError("Cannot determine side for " + name)


def trunk_weights(z):
    if z >= 1.34:
        return [("chest", 1.0)]
    if z >= 1.18:
        return mix("chest", "spine", (1.34 - z) / 0.16)
    if z >= 0.98:
        return mix("spine", "pelvis", (1.18 - z) / 0.20)
    return [("pelvis", 1.0)]


def sleeve_weights(axial_position):
    position = abs(axial_position)
    if position <= 0.42:
        return [("upper_arm", 1.0)]
    if position <= 0.58:
        return mix("upper_arm", "forearm", (position - 0.42) / 0.16)
    return [("forearm", 1.0)]


def trouser_weights(z):
    if z >= 0.84:
        return [("pelvis", 1.0)]
    if z >= 0.64:
        return [("thigh", 1.0)]
    if z <= 0.40:
        return [("shin", 1.0)]
    return mix("shin", "thigh", (z - 0.40) / 0.24)


def weights_for_vertex(name, point):
    if name == "Neck":
        return mix("neck", "head", (point.z - 1.45) / 0.14)
    if name in HEAD_NAMES or name.startswith(HEAD_PREFIXES):
        return [("head", 1.0)]
    if name.startswith("Sleeve_"):
        side = side_suffix(name)
        return [(bone + "." + side, weight) for bone, weight in sleeve_weights(point.x)]
    if name.startswith("Shoulder_"):
        side = side_suffix(name)
        return [("upper_arm." + side, 1.0)]
    if name.startswith(HAND_PREFIXES):
        side = side_suffix(name)
        return [("hand." + side, 1.0)]
    if name.startswith("Cuff_Button_"):
        side = side_suffix(name)
        return [("forearm." + side, 1.0)]
    if name.startswith("Trouser_Leg_") or name.startswith("Trouser_Crease_"):
        side = side_suffix(name)
        return [
            (bone if bone == "pelvis" else bone + "." + side, weight)
            for bone, weight in trouser_weights(point.z)
        ]
    if name == "Trouser_Waist" or name == "Trouser_Fly":
        return [("pelvis", 1.0)]
    if name.startswith(SHOE_PREFIXES):
        side = side_suffix(name)
        return [("foot." + side, 1.0)]
    return trunk_weights(point.z)


def rebuild_weights(character, armature):
    group_names = [
        bone.name
        for bone in armature.data.bones
        if bone.name != "root"
    ]
    objects = [obj for obj in character.objects if obj.type == "MESH"]
    for obj in objects:
        for group in list(obj.vertex_groups):
            obj.vertex_groups.remove(group)
        groups = {name: obj.vertex_groups.new(name=name) for name in group_names}
        matrix = obj.matrix_world
        for vertex in obj.data.vertices:
            point = matrix @ vertex.co
            weights = weights_for_vertex(obj.name, point)
            total = sum(weight for _, weight in weights)
            if total <= 0.0:
                raise RuntimeError("No weights for " + obj.name)
            for bone, weight in weights:
                groups[bone].add([vertex.index], weight / total, "REPLACE")

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

    armature["weight_profile"] = "v5 layered garment blend"


def add_shoulder_caps(character):
    material = bpy.data.materials.get("Suit Cobalt Wool")
    if material is None:
        raise RuntimeError("Suit material is missing")
    for side, sign in (("L", 1), ("R", -1)):
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=32,
            ring_count=20,
            location=(sign * 0.258, -0.001, 1.451),
        )
        obj = bpy.context.object
        obj.name = "Shoulder_" + side
        obj.scale = (0.058, 0.086, 0.080)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        obj.data.materials.append(material)
        for polygon in obj.data.polygons:
            polygon.use_smooth = True
        for owner in list(obj.users_collection):
            owner.objects.unlink(obj)
        character.objects.link(obj)


def render_view(camera, output_path, location, target, ortho_scale):
    camera.location = location
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = ortho_scale
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)


def export_character(character, armature):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in character.objects:
        if obj.type in {"MESH", "ARMATURE"}:
            obj.select_set(True)
    bpy.context.view_layer.objects.active = armature
    bpy.ops.export_scene.gltf(
        filepath=V5_GLB,
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
    if not os.path.exists(V4_BLEND):
        raise FileNotFoundError(V4_BLEND)
    bpy.ops.wm.open_mainfile(filepath=V4_BLEND)

    character = bpy.data.collections.get("CHARACTER")
    if character is None:
        raise RuntimeError("CHARACTER collection is missing")
    armature = bpy.data.objects.get("Character_Rig")
    if armature is None or armature.type != "ARMATURE":
        raise RuntimeError("Character_Rig armature is missing")

    add_shoulder_caps(character)
    rebuild_weights(character, armature)
    camera = bpy.data.objects["Presentation_Camera"]
    render_view(camera, FRONT_PATH, (0.0, -5.0, 0.97), (0.0, 0.0, 0.97), 2.24)
    render_view(camera, SIDE_PATH, (5.0, 0.0, 0.97), (0.0, 0.0, 0.97), 2.12)
    render_view(camera, BACK_PATH, (0.0, 5.0, 0.97), (0.0, 0.0, 0.97), 2.24)

    bpy.ops.wm.save_as_mainfile(filepath=V5_BLEND)
    export_character(character, armature)
    print("CHARACTER_V5_COMPLETE", V5_BLEND, V5_GLB)


if __name__ == "__main__":
    main()
