import bpy
import os


OUTPUT_DIR = os.environ.get(
    "GREEN_EFFECT_OUTPUT_DIR",
    r"I:\工作项目\blender\green_shooting_effect_v1",
)
PREVIEW_DIR = os.path.join(OUTPUT_DIR, "previews")
os.makedirs(PREVIEW_DIR, exist_ok=True)

scene = bpy.context.scene
scene.render.resolution_x = 640
scene.render.resolution_y = 640
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"

try:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
except Exception:
    scene.render.engine = "BLENDER_EEVEE"

if hasattr(scene, "eevee"):
    for attr in ("taa_render_samples", "taa_samples"):
        if hasattr(scene.eevee, attr):
            setattr(scene.eevee, attr, 24)

frames = [1, 8, 18, 32, 52, 76, 100, 124, 144, 160]
for frame in frames:
    scene.frame_set(frame)
    scene.render.filepath = os.path.join(PREVIEW_DIR, f"frame_{frame:03d}.png")
    bpy.ops.render.render(write_still=True)
    print(f"RENDERED_{frame:03d}")

print("RENDER_GREEN_PREVIEWS_OK")
