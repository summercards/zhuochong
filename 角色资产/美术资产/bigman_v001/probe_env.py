import json
import os

import bpy

OUT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(bpy.data.filepath) if bpy.data.filepath else
                 r"I:/工作项目/BIGMANFIGHT/角色资产/美术资产/bigman_v001")
)

info = {}
info["blender_version"] = list(bpy.app.version)
info["blender_version_string"] = bpy.app.version_string
info["binary_path"] = bpy.app.binary_path
try:
    info["engines"] = [
        item.identifier
        for item in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items
    ]
except Exception as exc:  # noqa: BLE001
    info["engines_error"] = str(exc)
info["scene_name"] = bpy.context.scene.name
info["objects"] = [
    {"name": obj.name, "type": obj.type} for obj in bpy.context.scene.objects
]
info["filepath"] = bpy.data.filepath
info["collections"] = [collection.name for collection in bpy.data.collections]
info["unit_scale"] = bpy.context.scene.unit_settings.scale_length
info["unit_system"] = bpy.context.scene.unit_settings.system
try:
    info["render_engine"] = bpy.context.scene.render.engine
except Exception as exc:  # noqa: BLE001
    info["render_engine_error"] = str(exc)
info["addons"] = [
    name for name in bpy.context.preferences.addons.keys() if "mcp" in name.lower()
]
print("PROBE_JSON " + json.dumps(info, ensure_ascii=False))
