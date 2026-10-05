"""bigman_v001 —— 全新骨架、蒙皮、展示环境、三视图渲染、GLB 导出与数值断言。"""

import json
import math
import os

import bpy
from mathutils import Vector

from bigman_body import FINGERS, build_arm, build_cuff, build_hand, build_leg
from bigman_body import build_shoe, build_suit_details, build_torso, build_neck
from bigman_head import build_brows, build_ears, build_eyes, build_glasses
from bigman_head import build_hair, build_head, build_mouth, build_nose
from bigman_lib import (BLEND_PATH, GLB_PATH, MAT, OUT_DIR, PREVIEW_DIR, Z_ARM,
                        build_materials, collection, lerp, reset_scene)
from bigman_lib import axis_matrix

REPORT = {"stages": [], "objects": {}, "assertions": {}}


# ---------------------------------------------------------------- 骨架定义
def finger_bones():
    bones = []
    for side, sign in (("L", 1.0), ("R", -1.0)):
        for name, y, length in FINGERS:
            joints = (0.0, 0.40, 0.72, 1.00)
            points = [(sign * (0.800 + length * j), y, Z_ARM) for j in joints]
            for index in range(3):
                bone_name = "%s_%02d.%s" % (name, index + 1, side)
                parent = ("hand." + side) if index == 0 else \
                    "%s_%02d.%s" % (name, index, side)
                bones.append((bone_name, points[index], points[index + 1],
                              parent, index > 0))
        thumb = "thumb"
        thumb_points = (
            (0.726, -0.042, Z_ARM - 0.010),
            (0.744, -0.062, Z_ARM - 0.005),
            (0.760, -0.080, Z_ARM - 0.003),
            (0.770, -0.093, Z_ARM - 0.002),
        )
        for index in range(3):
            bone_name = "%s_%02d.%s" % (thumb, index + 1, side)
            parent = ("hand." + side) if index == 0 else \
                "%s_%02d.%s" % (thumb, index, side)
            head = (sign * thumb_points[index][0], thumb_points[index][1],
                    thumb_points[index][2])
            tail = (sign * thumb_points[index + 1][0], thumb_points[index + 1][1],
                    thumb_points[index + 1][2])
            bones.append((bone_name, head, tail, parent, index > 0))
    return bones


def rig_definition():
    bones = [
        ("root", (0, 0, 0.0), (0, 0, 0.20), None, False),
        ("pelvis", (0, 0, 0.900), (0, 0, 1.020), "root", False),
        ("spine_01", (0, 0, 1.020), (0, 0, 1.140), "pelvis", True),
        ("spine_02", (0, 0, 1.140), (0, 0, 1.260), "spine_01", True),
        ("chest", (0, 0, 1.260), (0, 0, 1.440), "spine_02", True),
        ("neck", (0, 0, 1.440), (0, 0, 1.560), "chest", True),
        ("head", (0, 0, 1.560), (0, 0, 1.790), "neck", True),
        ("jaw", (0, 0.030, 1.640), (0, -0.070, 1.572), "head", False),
        ("glasses", (0, -0.0885, 1.700), (0, -0.0885, 1.724), "head", False),
    ]
    for side, sign in (("L", 1.0), ("R", -1.0)):
        bones.extend([
            ("eye." + side, (sign * 0.0335, -0.0665, 1.700),
             (sign * 0.0335, -0.1000, 1.700), "head", False),
            ("shoulder." + side, (sign * 0.040, 0, 1.400),
             (sign * 0.150, 0, 1.420), "chest", False),
            ("upperarm." + side, (sign * 0.150, 0, 1.420),
             (sign * 0.478, 0, 1.420), "shoulder." + side, True),
            ("forearm." + side, (sign * 0.478, 0, 1.420),
             (sign * 0.702, 0, 1.420), "upperarm." + side, True),
            ("hand." + side, (sign * 0.702, 0, 1.420),
             (sign * 0.800, 0, 1.420), "forearm." + side, True),
            ("thigh." + side, (sign * 0.090, 0, 0.900),
             (sign * 0.086, 0, 0.490), "pelvis", False),
            ("shin." + side, (sign * 0.086, 0, 0.490),
             (sign * 0.084, 0, 0.078), "thigh." + side, True),
            ("foot." + side, (sign * 0.084, 0, 0.078),
             (sign * 0.088, -0.115, 0.020), "shin." + side, True),
            ("toe." + side, (sign * 0.088, -0.115, 0.020),
             (sign * 0.088, -0.190, 0.020), "foot." + side, True),
        ])
    bones.extend(finger_bones())
    return bones


def build_rig(col):
    data = bpy.data.armatures.new("BigMan_Rig")
    arm = bpy.data.objects.new("Character_Rig", data)
    col.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    edit_bones = data.edit_bones
    created = {}
    for name, head, tail, parent, connect in rig_definition():
        bone = edit_bones.new(name)
        bone.head = Vector(head)
        bone.tail = Vector(tail)
        bone.roll = 0.0
        bone.use_deform = True
        created[name] = bone
    for name, head, tail, parent, connect in rig_definition():
        if parent:
            created[name].parent = created[parent]
            created[name].use_connect = bool(connect)
    bpy.ops.object.mode_set(mode="OBJECT")
    for pose_bone in arm.pose.bones:
        pose_bone.rotation_mode = "XYZ"
    arm.show_in_front = True
    arm["asset_type"] = "character"
    arm["pose"] = "T-pose"
    arm["height_m"] = 1.80
    arm["facing"] = "-Y"
    arm["description"] = "Big man in royal blue suit with black glasses"
    arm["bone_groups"] = "spine/arms/fingers/legs/head/jaw/eyes/glasses"
    return arm


# ---------------------------------------------------------------- 蒙皮
def bind_object(obj, arm, bones, mode="auto", rigid=None):
    groups = {}
    for name in bones:
        if name in obj.vertex_groups:
            obj.vertex_groups.remove(obj.vertex_groups[name])
    for name in bones:
        groups[name] = obj.vertex_groups.new(name=name)

    if mode == "rigid":
        indices = [vertex.index for vertex in obj.data.vertices]
        groups[rigid].add(indices, 1.0, "REPLACE")
    else:
        segments = []
        for name in bones:
            bone = arm.data.bones[name]
            segments.append((name, Vector(bone.head_local), Vector(bone.tail_local)))
        for vertex in obj.data.vertices:
            point = obj.matrix_world @ vertex.co
            distances = []
            for name, head, tail in segments:
                distances.append((point_segment_distance(point, head, tail), name))
            distances.sort(key=lambda item: item[0])
            first, second = distances[0], distances[1] if len(distances) > 1 else distances[0]
            if first[0] < 1e-5 or second[0] > first[0] * 1.9:
                groups[first[1]].add([vertex.index], 1.0, "REPLACE")
            else:
                raw = [(1.0 / max(d, 2e-4) ** 4.0, n) for d, n in (first, second)]
                total = sum(w for w, _ in raw)
                for weight, name in raw:
                    groups[name].add([vertex.index], weight / total, "REPLACE")

    modifier = obj.modifiers.get("Armature") or obj.modifiers.new("Armature",
                                                                 "ARMATURE")
    modifier.object = arm
    modifier.use_deform_preserve_volume = True
    if obj.parent != arm:
        obj.parent = arm
        obj.matrix_parent_inverse = arm.matrix_world.inverted()
    return obj


def point_segment_distance(point, start, end):
    segment = end - start
    length_squared = segment.length_squared
    if length_squared <= 1e-12:
        return (point - start).length
    factor = max(0.0, min(1.0, (point - start).dot(segment) / length_squared))
    return (point - (start + segment * factor)).length


# ---------------------------------------------------------------- 展示环境
def build_presentation(col):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 780
    scene.render.resolution_y = 1200
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.render.film_transparent = True
    try:
        scene.eevee.taa_render_samples = 64
    except AttributeError:
        pass

    # 合成：把透明底压成纯白，避免世界光照把材质冲白
    scene.use_nodes = True
    tree = scene.node_tree
    for node in list(tree.nodes):
        tree.nodes.remove(node)
    render_layers = tree.nodes.new("CompositorNodeRLayers")
    alpha_over = tree.nodes.new("CompositorNodeAlphaOver")
    composite = tree.nodes.new("CompositorNodeComposite")
    alpha_over.inputs[0].default_value = 1.0
    alpha_over.inputs[1].default_value = (1.0, 1.0, 1.0, 1.0)
    tree.links.new(render_layers.outputs["Image"], alpha_over.inputs[2])
    tree.links.new(alpha_over.outputs[0], composite.inputs[0])

    world = bpy.data.worlds.new("BigMan_World") if not bpy.data.worlds else \
        bpy.data.worlds[0]
    scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    if background:
        background.inputs[0].default_value = (0.90, 0.91, 0.93, 1.0)
        background.inputs[1].default_value = 0.30

    lights = (
        ("Key_Light", "AREA", (1.90, -2.70, 2.35), 200.0, 2.2, (0, 0, 1.10)),
        ("Fill_Light", "AREA", (-2.40, -1.90, 1.45), 70.0, 3.0, (0, 0, 1.15)),
        ("Rim_Light", "AREA", (0.40, 2.90, 2.20), 140.0, 2.5, (0, 0, 1.20)),
        ("Front_Light", "AREA", (0.0, -3.20, 1.30), 55.0, 3.6, (0, 0, 1.30)),
    )
    for name, kind, location, energy, size, target in lights:
        data = bpy.data.lights.new(name, kind)
        data.energy = energy
        data.size = size
        data.shape = "DISK"
        obj = bpy.data.objects.new(name, data)
        col.objects.link(obj)
        obj.location = location
        direction = Vector(target) - Vector(location)
        obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

    camera_data = bpy.data.cameras.new("Presentation_Camera")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 2.02
    camera = bpy.data.objects.new("Presentation_Camera", camera_data)
    col.objects.link(camera)
    scene.camera = camera
    return camera


def render_view(camera, path, location, target, ortho_scale):
    camera.location = Vector(location)
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = ortho_scale
    camera.rotation_euler = (
        Vector(target) - Vector(location)
    ).to_track_quat("-Z", "Y").to_euler()
    scene = bpy.context.scene
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def render_views(camera):
    os.makedirs(PREVIEW_DIR, exist_ok=True)
    views = (
        ("front", (0.0, -5.0, 0.90), (0.0, 0.0, 0.90), 2.04, 780, 1200),
        ("side", (5.0, 0.0, 0.90), (0.0, 0.0, 0.90), 2.04, 780, 1200),
        ("back", (0.0, 5.0, 0.90), (0.0, 0.0, 0.90), 2.04, 780, 1200),
        ("three_quarter", (3.4, -3.9, 1.20), (0.0, 0.0, 1.05), 2.10, 780, 1200),
        ("head_front", (0.0, -1.6, 1.686), (0.0, 0.0, 1.686), 0.40, 760, 860),
        ("head_side", (1.6, 0.0, 1.686), (0.0, 0.0, 1.686), 0.40, 760, 860),
        ("head_three_quarter", (0.9, -1.3, 1.72), (0.0, 0.0, 1.686), 0.42, 760,
         860),
    )
    scene = bpy.context.scene
    outputs = []
    for name, location, target, scale, res_x, res_y in views:
        scene.render.resolution_x = res_x
        scene.render.resolution_y = res_y
        path = os.path.join(PREVIEW_DIR, "bigman_v001_%s.png" % name)
        render_view(camera, path, location, target, scale)
        outputs.append(path)
    return outputs


# ---------------------------------------------------------------- 断言
def evaluated_bounds(objects):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    low = Vector((1e9, 1e9, 1e9))
    high = Vector((-1e9, -1e9, -1e9))
    for obj in objects:
        if obj.type != "MESH":
            continue
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        for vertex in mesh.vertices:
            point = evaluated.matrix_world @ vertex.co
            for axis in range(3):
                low[axis] = min(low[axis], point[axis])
                high[axis] = max(high[axis], point[axis])
        evaluated.to_mesh_clear()
    return low, high


def run_assertions(arm, character_objects):
    low, high = evaluated_bounds(character_objects)
    height = high.z - low.z
    results = {
        "bounds_min": [round(v, 5) for v in low],
        "bounds_max": [round(v, 5) for v in high],
        "height_m": round(height, 5),
        "height_ok": abs(height - 1.800) <= 0.004,
        "sole_at_zero_ok": abs(low.z) <= 0.003,
        "width_m": round(high.x - low.x, 5),
        "depth_m": round(high.y - low.y, 5),
    }

    by_name = {obj.name: obj for obj in character_objects}
    from mathutils import kdtree

    symmetry = []
    for name, obj in sorted(by_name.items()):
        if not name.endswith("_L"):
            continue
        other = by_name.get(name[:-2] + "_R")
        if other is None:
            continue
        right_points = [other.matrix_world @ v.co for v in other.data.vertices]
        tree = kdtree.KDTree(len(right_points))
        for index, point in enumerate(right_points):
            tree.insert(Vector((-point.x, point.y, point.z)), index)
        tree.balance()
        worst = 0.0
        for vertex in obj.data.vertices:
            point = obj.matrix_world @ vertex.co
            _co, _index, distance = tree.find(point)
            worst = max(worst, distance)
        symmetry.append({"pair": name, "ok": worst <= 0.002,
                         "worst_m": round(worst, 6)})
    results["symmetry_pairs"] = len(symmetry)
    results["symmetry_failures"] = [item for item in symmetry if not item["ok"]]
    results["bones"] = len(arm.data.bones)
    results["bone_names_ok"] = all(
        arm.data.bones.get(n) is not None
        for n in ("root", "pelvis", "chest", "head", "jaw", "glasses",
                  "eye.L", "eye.R", "hand.L", "hand.R", "thigh.L", "shin.R",
                  "index_01.L", "pinky_03.R", "thumb_01.L", "toe.R")
    )
    results["face_symmetry_ok"] = results["symmetry_failures"] == []
    # T-pose 契约：手臂必须水平。
    #
    # 判据挂在**骨骼**上，不挂网格 —— 曾经用"Sleeve 顶点平均 z"判，那是错的：
    # 手臂截面天然上下不对称（三角肌腋侧 0.134 远长于肩峰侧 0.096），顶点平均 z
    # 必然低于臂轴，且这个差值沿 x 变化（0.184 处 −19 mm、0.662 处 −5.5 mm）。
    # 三角肌一加厚它就越界报红，但模型完全正确。网格层只把漂移量留作**报告**。
    #
    # 这里引 `Z_ARM` 而不是写死 1.420：Z_ARM 定义在 bigman_lib，骨骼 z 定义在本模块，
    # 是一条跨文件的隐形契约 —— 改了前者忘改后者，这条会立刻红。
    ends = []
    for bone_name in ("upperarm.L", "forearm.L", "hand.L"):
        bone = arm.data.bones.get(bone_name)
        if bone is None:
            continue
        ends.append(round((arm.matrix_world @ bone.head_local).z, 6))
        ends.append(round((arm.matrix_world @ bone.tail_local).z, 6))
    results["arm_axis_z"] = ends
    results["arm_horizontal_ok"] = bool(ends) and all(
        abs(z - Z_ARM) <= 1e-6 for z in ends)

    sleeve = by_name.get("Sleeve_L")
    if sleeve is not None:
        points = [sleeve.matrix_world @ v.co for v in sleeve.data.vertices]
        layers = {}
        for p in points:
            layers.setdefault(round(p.x, 3), []).append(p.z)
        mids = sorted((x, (min(zs) + max(zs)) / 2.0)
                      for x, zs in layers.items())
        if mids:
            # 三角肌下垂造成的"中线漂移"：正数=远端更高。只报告不断言。
            results["sleeve_mid_lean_mm"] = round(
                (mids[-1][1] - mids[0][1]) * 1000.0, 1)
    return results


# ---------------------------------------------------------------- 导出
def export_glb(collection_obj):
    bpy.ops.object.select_all(action="DESELECT")
    selected = []
    for obj in collection_obj.objects:
        if obj.type in {"MESH", "ARMATURE"}:
            obj.select_set(True)
            selected.append(obj)
    bpy.context.view_layer.objects.active = next(
        obj for obj in collection_obj.objects if obj.type == "ARMATURE"
    )
    bpy.ops.export_scene.gltf(
        filepath=GLB_PATH,
        export_format="GLB",
        use_selection=True,
        export_yup=True,
        export_apply=True,
        export_skins=True,
        export_animations=False,
        export_cameras=False,
        export_lights=False,
    )
    return len(selected)


if __name__ == "__main__":
    pass
