import os
import sys

import bpy


ROOT = os.path.abspath(os.path.dirname(__file__))
DEFAULT_BLEND = os.path.join(ROOT, "business_man_tpose_v10.blend")
DEFAULT_GLB = os.path.join(ROOT, "business_man_tpose_v10.glb")
ARMATURE_NAME = "Character_Rig"
LENS_MATERIAL_NAME = "Glasses Lens"
LENS_OBJECTS = {"Glasses_Lens_L", "Glasses_Lens_R"}


def parse_paths():
    if "--" not in sys.argv:
        return DEFAULT_BLEND, DEFAULT_GLB
    values = sys.argv[sys.argv.index("--") + 1 :]
    if len(values) != 2:
        raise ValueError("Expected output Blend and GLB paths after --")
    return tuple(os.path.abspath(value) for value in values)


def configure_lens_material():
    material = bpy.data.materials.get(LENS_MATERIAL_NAME)
    if material is None:
        raise RuntimeError("Missing material %s" % LENS_MATERIAL_NAME)

    material.use_nodes = True
    material.surface_render_method = "BLENDED"
    material.use_transparency_overlap = False
    material.diffuse_color = (0.22, 0.38, 0.44, 0.32)
    material["runtime_alpha"] = 0.32
    material["material_role"] = "semi_transparent_glasses_lens"

    principled = next(
        (node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"),
        None,
    )
    if principled is None:
        raise RuntimeError("Glasses Lens has no Principled BSDF node")

    principled.inputs["Base Color"].default_value = (0.22, 0.38, 0.44, 0.32)
    principled.inputs["Metallic"].default_value = 0.02
    principled.inputs["Roughness"].default_value = 0.08
    principled.inputs["IOR"].default_value = 1.47
    principled.inputs["Alpha"].default_value = 0.32
    principled.inputs["Transmission Weight"].default_value = 0.35
    principled.inputs["Coat Weight"].default_value = 0.20
    principled.inputs["Coat Roughness"].default_value = 0.04

    lens_meshes = [
        obj
        for obj in bpy.data.objects
        if obj.type == "MESH" and obj.name in LENS_OBJECTS
    ]
    if {obj.name for obj in lens_meshes} != LENS_OBJECTS:
        raise RuntimeError("Expected both glasses lens mesh objects")
    for obj in lens_meshes:
        if material.name not in [slot.name for slot in obj.data.materials if slot]:
            raise RuntimeError("%s does not use %s" % (obj.name, material.name))

    return material, lens_meshes


def export_glb(glb_path, material):
    character_collection = bpy.data.collections.get("CHARACTER")
    if character_collection is None:
        raise RuntimeError("CHARACTER collection is missing")
    armature = bpy.data.objects.get(ARMATURE_NAME)
    if armature is None:
        raise RuntimeError("Character armature is missing")

    bpy.ops.object.select_all(action="DESELECT")
    for obj in character_collection.objects:
        if obj.type in {"MESH", "ARMATURE"}:
            obj.select_set(True)
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
    material, lens_meshes = configure_lens_material()

    armatures = [obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE"]
    if len(armatures) != 1:
        raise RuntimeError("Expected exactly one armature")
    if armatures[0].name != ARMATURE_NAME:
        raise RuntimeError("Expected armature %s" % ARMATURE_NAME)
    if len(armatures[0].data.bones) != 56:
        raise RuntimeError("Expected 56 bones")

    action_names = sorted(action.name for action in bpy.data.actions)
    expected_actions = {
        "attack",
        "crouch",
        "defeat",
        "hit",
        "idle",
        "jump",
        "jump_up",
        "run",
        "talk",
        "walk",
    }
    if set(action_names) != expected_actions:
        raise RuntimeError("Unexpected actions: %s" % ", ".join(action_names))

    bpy.context.scene.render.fps = 30
    bpy.context.scene.render.fps_base = 1.0
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    export_glb(glb_path, material)

    print("GLASSES_MATERIAL_V10_COMPLETE")
    print("V10_BLEND", blend_path)
    print("V10_GLB", glb_path)
    print("LENS_MESHES", ",".join(sorted(obj.name for obj in lens_meshes)))
    print("LENS_ALPHA", float(material["runtime_alpha"]))
    print("SURFACE_RENDER_METHOD", material.surface_render_method)
    print("ACTIONS", ",".join(action_names))


if __name__ == "__main__":
    main()
