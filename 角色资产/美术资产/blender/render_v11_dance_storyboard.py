import os
import sys

import bpy
from mathutils import Vector


ROOT = os.path.abspath(os.path.dirname(__file__))
DEFAULT_GLB = os.path.join(ROOT, "business_man_tpose_v11.glb")
DEFAULT_OUTPUT = os.path.join(ROOT, "v11_dance_storyboard")
ACTION_NAME = "dance"
FRAMES = (0, 8, 15, 23, 30, 38, 45, 53)


def parse_paths():
    if "--" not in sys.argv:
        return DEFAULT_GLB, DEFAULT_OUTPUT
    values = sys.argv[sys.argv.index("--") + 1 :]
    if len(values) != 2:
        raise ValueError("Expected GLB and output directory paths after --")
    return tuple(os.path.abspath(value) for value in values)


def add_presentation():
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 640
    scene.render.resolution_y = 640
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    if scene.world is None:
        scene.world = bpy.data.worlds.new("Dance Storyboard World")
    scene.world.color = (0.018, 0.024, 0.035)

    bpy.ops.object.camera_add()
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 2.75
    target = Vector((0.0, 0.0, 0.98))
    camera.location = Vector((3.8, -5.2, 2.35))
    camera.rotation_euler = (
        target - camera.location
    ).to_track_quat("-Z", "Y").to_euler()
    scene.camera = camera

    for location, energy, size in (
        ((-4.0, -4.5, 5.5), 1350.0, 4.0),
        ((4.2, -2.0, 3.2), 720.0, 3.2),
        ((1.2, 4.5, 4.6), 980.0, 3.0),
    ):
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        light.rotation_euler = (
            target - light.location
        ).to_track_quat("-Z", "Y").to_euler()

    bpy.ops.mesh.primitive_plane_add(size=8.0, location=(0.0, 0.0, -0.012))
    ground = bpy.context.object
    material = bpy.data.materials.new("Dance Storyboard Ground")
    material.diffuse_color = (0.045, 0.055, 0.075, 1.0)
    ground.data.materials.append(material)


def assign_action(armature, action):
    if armature.animation_data is None:
        armature.animation_data_create()
    armature.animation_data.action = action
    if armature.animation_data.action_slot is None and action.slots:
        armature.animation_data.action_slot = action.slots[0]
    bpy.context.view_layer.update()


def main():
    glb_path, output_dir = parse_paths()
    os.makedirs(output_dir, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps = 30
    bpy.context.scene.render.fps_base = 1.0
    bpy.ops.import_scene.gltf(filepath=glb_path)
    armatures = [obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE"]
    if len(armatures) != 1:
        raise RuntimeError("Expected one armature")
    armature = armatures[0]
    action = bpy.data.actions.get(ACTION_NAME)
    if action is None:
        raise RuntimeError("Dance action is missing")
    add_presentation()
    assign_action(armature, action)
    scene = bpy.context.scene
    for frame in FRAMES:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        scene.render.filepath = os.path.join(
            output_dir,
            "dance_%02d.png" % frame,
        )
        bpy.ops.render.render(write_still=True)
    print("DANCE_STORYBOARD_COMPLETE", output_dir)


if __name__ == "__main__":
    main()
