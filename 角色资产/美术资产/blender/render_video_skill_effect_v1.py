import bpy
import os


OUTPUT_DIR = r"I:\工作项目\blender\skill_effect_v1"
VIDEO_PATH = os.path.join(OUTPUT_DIR, "skill_effect_v1_preview.mp4")

scene = bpy.context.scene
original = {
    "resolution_x": scene.render.resolution_x,
    "resolution_y": scene.render.resolution_y,
    "resolution_percentage": scene.render.resolution_percentage,
    "file_format": scene.render.image_settings.file_format,
    "filepath": scene.render.filepath,
    "engine": scene.render.engine,
}

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

scene.render.resolution_x = original["resolution_x"]
scene.render.resolution_y = original["resolution_y"]
scene.render.resolution_percentage = original["resolution_percentage"]
scene.render.image_settings.file_format = original["file_format"]
scene.render.filepath = original["filepath"]
scene.render.engine = original["engine"]
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUTPUT_DIR, "skill_effect_v1.blend"))

print("VIDEO_OK")
print(VIDEO_PATH)
