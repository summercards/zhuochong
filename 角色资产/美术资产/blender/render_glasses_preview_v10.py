import os
import sys

import bpy
from mathutils import Vector


ROOT = os.path.abspath(os.path.dirname(__file__))
DEFAULT_OUTPUT = os.path.join(ROOT, "business_man_tpose_v10_glasses_preview.png")


def parse_output_path():
    if "--" not in sys.argv:
        return DEFAULT_OUTPUT
    values = sys.argv[sys.argv.index("--") + 1 :]
    if len(values) != 1:
        raise ValueError("Expected preview output path after --")
    return os.path.abspath(values[0])


def add_presentation():
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 900
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.view_transform = "AgX"

    if scene.world is None:
        scene.world = bpy.data.worlds.new("Glasses Preview World")
    scene.world.color = (0.018, 0.026, 0.040)

    target = Vector((0.0, -0.015, 1.625))
    bpy.ops.object.camera_add(location=(0.72, -1.42, 1.72))
    camera = bpy.context.object
    camera.name = "Glasses_Preview_Camera"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 0.62
    camera.rotation_euler = (
        target - camera.location
    ).to_track_quat("-Z", "Y").to_euler()
    scene.camera = camera

    for name, location, energy, size in (
        ("Glasses_Preview_Key", (-1.4, -1.8, 2.5), 620.0, 1.8),
        ("Glasses_Preview_Fill", (1.6, -1.1, 1.75), 430.0, 1.5),
        ("Glasses_Preview_Rim", (0.8, 1.5, 2.2), 520.0, 1.5),
    ):
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.name = name
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        light.rotation_euler = (
            target - light.location
        ).to_track_quat("-Z", "Y").to_euler()


def main():
    output_path = parse_output_path()
    armature = next(
        (obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE"),
        None,
    )
    if armature is None:
        raise RuntimeError("Imported character armature is missing")

    idle = bpy.data.actions.get("idle")
    if idle is None:
        raise RuntimeError("Imported idle action is missing")
    armature.animation_data_create()
    armature.animation_data.action = idle
    bpy.context.scene.frame_set(15)

    add_presentation()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print("GLASSES_PREVIEW", output_path)


if __name__ == "__main__":
    main()
