import bpy
import os


ROOT_DIR = r"I:\工作项目\blender"
OUTPUT_DIR = os.environ.get(
    "GREEN_EFFECT_OUTPUT_DIR",
    os.path.join(ROOT_DIR, "green_shooting_effect_v1"),
)
VIDEO_PATH = os.environ.get(
    "GREEN_EFFECT_VIDEO_PATH",
    os.path.join(ROOT_DIR, "green_shooting_effect_v1_preview.mp4"),
)
BLEND_PATH = os.environ.get(
    "GREEN_EFFECT_BLEND_PATH",
    os.path.join(ROOT_DIR, "green_shooting_effect_v1.blend"),
)

scene = bpy.context.scene
scene.render.resolution_x = 720
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "FFMPEG"
scene.render.ffmpeg.format = "MPEG4"
scene.render.ffmpeg.codec = "H264"
scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
scene.render.ffmpeg.ffmpeg_preset = "GOOD"
scene.render.ffmpeg.gopsize = 15
scene.render.ffmpeg.audio_codec = "NONE"
scene.render.filepath = VIDEO_PATH
scene.frame_start = 1
scene.frame_end = 160
scene.frame_set(1)

if hasattr(scene, "eevee"):
    for attr in ("taa_render_samples", "taa_samples"):
        if hasattr(scene.eevee, attr):
            setattr(scene.eevee, attr, 24)

bpy.ops.render.render(animation=True)

scene.render.resolution_x = 720
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.render.filepath = os.path.join(OUTPUT_DIR, "previews", "green_shooting_")
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)

print("VIDEO_GREEN_OK")
print(VIDEO_PATH)
