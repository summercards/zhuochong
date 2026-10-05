import bpy
import json
import math
import os
import random
from mathutils import Matrix, Vector


ROOT_DIR = r"I:\工作项目\blender"
OUTPUT_DIR = os.environ.get(
    "GREEN_EFFECT_OUTPUT_DIR",
    os.path.join(ROOT_DIR, "green_shooting_effect_v1"),
)
PREVIEW_DIR = os.path.join(OUTPUT_DIR, "previews")
BLEND_PATH = os.environ.get(
    "GREEN_EFFECT_BLEND_PATH",
    os.path.join(ROOT_DIR, "green_shooting_effect_v1.blend"),
)
random.seed(20260915)


def ensure_dirs():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(PREVIEW_DIR, exist_ok=True)


def clear_scene(scene):
    for collection in list(scene.collection.children):
        for obj in list(collection.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        scene.collection.children.unlink(collection)
        bpy.data.collections.remove(collection)
    for obj in list(scene.collection.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def set_input(node, name, value):
    socket = node.inputs.get(name)
    if socket is not None:
        socket.default_value = value
    return socket


def link_to_collection(obj, collection):
    for old_collection in list(obj.users_collection):
        old_collection.objects.unlink(obj)
    collection.objects.link(obj)
    return obj


def create_empty(name, collection, location=(0.0, 0.0, 0.0)):
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_type = "PLAIN_AXES"
    obj.empty_display_size = 0.35
    obj.location = location
    collection.objects.link(obj)
    return obj


def set_material(obj, material):
    if obj.data and hasattr(obj.data, "materials"):
        obj.data.materials.append(material)


def create_emission_material(
    name,
    color,
    secondary,
    strength,
    noise_scale=4.0,
    noise_detail=3.0,
):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    emission = nodes.new("ShaderNodeEmission")
    texcoord = nodes.new("ShaderNodeTexCoord")
    noise = nodes.new("ShaderNodeTexNoise")
    ramp = nodes.new("ShaderNodeValToRGB")

    set_input(noise, "Scale", noise_scale)
    set_input(noise, "Detail", noise_detail)
    set_input(noise, "Roughness", 0.55)
    ramp.color_ramp.elements[0].position = 0.16
    ramp.color_ramp.elements[0].color = color
    ramp.color_ramp.elements[1].position = 0.84
    ramp.color_ramp.elements[1].color = secondary
    set_input(emission, "Strength", strength)

    links.new(texcoord.outputs["Generated"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], emission.inputs["Color"])
    links.new(emission.outputs["Emission"], output.inputs["Surface"])
    material["base_strength"] = strength
    material["strength_node"] = emission.name
    return material


def create_surface_material(name, base_color, roughness=0.65, metallic=0.0):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    principled = nodes.new("ShaderNodeBsdfPrincipled")
    set_input(principled, "Base Color", base_color)
    set_input(principled, "Roughness", roughness)
    set_input(principled, "Metallic", metallic)
    links.new(principled.outputs["BSDF"], output.inputs["Surface"])
    return material


def create_glow_shell_material(name, color, strength=2.2, edge_power=2.4):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    transparent = nodes.new("ShaderNodeBsdfTransparent")
    emission = nodes.new("ShaderNodeEmission")
    mix = nodes.new("ShaderNodeMixShader")
    fresnel = nodes.new("ShaderNodeFresnel")
    power = nodes.new("ShaderNodeMath")
    noise = nodes.new("ShaderNodeTexNoise")
    texcoord = nodes.new("ShaderNodeTexCoord")

    fresnel.inputs["IOR"].default_value = 1.38
    power.operation = "POWER"
    power.inputs[1].default_value = edge_power
    set_input(noise, "Scale", 8.0)
    set_input(noise, "Detail", 4.0)
    set_input(emission, "Color", color)
    set_input(emission, "Strength", strength)

    links.new(texcoord.outputs["Generated"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], power.inputs[0])
    links.new(fresnel.outputs["Fac"], power.inputs[0])
    links.new(power.outputs["Value"], mix.inputs[0])
    links.new(transparent.outputs["BSDF"], mix.inputs[1])
    links.new(emission.outputs["Emission"], mix.inputs[2])
    links.new(mix.outputs["Shader"], output.inputs["Surface"])
    material["base_strength"] = strength
    material["strength_node"] = emission.name
    try:
        material.surface_render_method = "DITHERED"
    except Exception:
        pass
    try:
        material.blend_method = "BLEND"
    except Exception:
        pass
    return material


def animate_emission_material(material, end_frame=160):
    node_name = material.get("strength_node")
    base_strength = material.get("base_strength", 1.0)
    if not node_name:
        return
    node = material.node_tree.nodes.get(node_name)
    if not node:
        return
    strength = node.inputs.get("Strength")
    profile = [
        (1, 0.16),
        (8, 0.82),
        (18, 1.00),
        (82, 1.12),
        (108, 1.00),
        (130, 0.62),
        (145, 0.22),
        (end_frame, 0.0),
    ]
    for frame, multiplier in profile:
        strength.default_value = base_strength * multiplier
        strength.keyframe_insert("default_value", frame=frame)


def build_materials():
    materials = {}
    materials["core"] = create_emission_material(
        "MAT_BeamCore",
        (0.24, 1.0, 0.34, 1.0),
        (0.62, 1.0, 0.68, 1.0),
        5.7,
        5.0,
    )
    materials["lime"] = create_emission_material(
        "MAT_LimeEnergy",
        (0.02, 0.70, 0.045, 1.0),
        (0.20, 1.0, 0.13, 1.0),
        4.0,
        6.0,
    )
    materials["green"] = create_emission_material(
        "MAT_GreenEnergy",
        (0.005, 0.20, 0.025, 1.0),
        (0.08, 0.80, 0.08, 1.0),
        2.8,
        7.5,
    )
    materials["teal"] = create_emission_material(
        "MAT_TealRim",
        (0.0, 0.18, 0.12, 1.0),
        (0.0, 0.72, 0.34, 1.0),
        2.4,
        4.0,
    )
    materials["mist"] = create_glow_shell_material(
        "MAT_MistGlow", (0.02, 0.46, 0.09, 1.0), 1.15, 2.0
    )
    materials["beam_shell"] = create_glow_shell_material(
        "MAT_BeamShell", (0.025, 0.76, 0.06, 1.0), 1.7, 1.7
    )
    materials["ground"] = create_surface_material(
        "MAT_Ground", (0.0025, 0.012, 0.0035, 1.0), 0.60, 0.05
    )
    background = bpy.data.materials.new("MAT_Backdrop")
    background.use_nodes = True
    nodes = background.node_tree.nodes
    links = background.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    principled = nodes.new("ShaderNodeBsdfPrincipled")
    texcoord = nodes.new("ShaderNodeTexCoord")
    gradient = nodes.new("ShaderNodeTexGradient")
    ramp = nodes.new("ShaderNodeValToRGB")
    noise = nodes.new("ShaderNodeTexNoise")
    mix = nodes.new("ShaderNodeMixRGB")
    set_input(noise, "Scale", 2.0)
    set_input(noise, "Detail", 5.0)
    gradient.gradient_type = "QUADRATIC"
    ramp.color_ramp.elements[0].color = (0.0002, 0.002, 0.0005, 1.0)
    ramp.color_ramp.elements[1].color = (0.003, 0.035, 0.008, 1.0)
    mix.blend_type = "SCREEN"
    mix.inputs["Fac"].default_value = 0.36
    set_input(principled, "Roughness", 0.92)
    links.new(texcoord.outputs["Generated"], gradient.inputs["Vector"])
    links.new(texcoord.outputs["Generated"], noise.inputs["Vector"])
    links.new(gradient.outputs["Color"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], mix.inputs[1])
    links.new(noise.outputs["Color"], mix.inputs[2])
    links.new(mix.outputs["Color"], principled.inputs["Base Color"])
    links.new(principled.outputs["BSDF"], output.inputs["Surface"])
    materials["background"] = background
    return materials


def create_mesh_object(name, vertices, faces, material, collection, location=(0, 0, 0)):
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    collection.objects.link(obj)
    if material:
        obj.data.materials.append(material)
    return obj


def create_disc(name, radius, material, collection, location=(0, 0, 0), segments=64):
    vertices = [(0.0, 0.0, 0.0)]
    faces = []
    for index in range(segments):
        angle = math.tau * index / segments
        vertices.append((math.cos(angle) * radius, math.sin(angle) * radius, 0.0))
    for index in range(segments):
        faces.append((0, index + 1, ((index + 1) % segments) + 1))
    return create_mesh_object(name, vertices, faces, material, collection, location)


def create_plus_mesh(
    name,
    size,
    bar_ratio,
    depth,
    material,
    collection,
    location=(0, 0, 0),
):
    half = size * 0.5
    bar = size * bar_ratio * 0.5
    profile = [
        (-bar, half),
        (bar, half),
        (bar, bar),
        (half, bar),
        (half, -bar),
        (bar, -bar),
        (bar, -half),
        (-bar, -half),
        (-bar, -bar),
        (-half, -bar),
        (-half, bar),
        (-bar, bar),
    ]
    vertices = []
    for y in (-depth * 0.5, depth * 0.5):
        for x, z in profile:
            vertices.append((x, y, z))
    faces = []
    faces.append(tuple(range(11, -1, -1)))
    faces.append(tuple(range(12, 24)))
    for index in range(12):
        next_index = (index + 1) % 12
        faces.append((index, next_index, next_index + 12, index + 12))
    obj = create_mesh_object(name, vertices, faces, material, collection, location)
    bevel = obj.modifiers.new("SoftEdges", "BEVEL")
    bevel.width = max(size * 0.012, 0.006)
    bevel.segments = 2
    return obj


def create_cylinder_from_top(
    name,
    radius,
    height,
    material,
    collection,
    location=(0, 0, 0),
    vertices_count=32,
):
    vertices = []
    for index in range(vertices_count):
        angle = math.tau * index / vertices_count
        vertices.append((math.cos(angle) * radius, math.sin(angle) * radius, 0.0))
    for index in range(vertices_count):
        angle = math.tau * index / vertices_count
        vertices.append((math.cos(angle) * radius, math.sin(angle) * radius, height))
    top_face = tuple(range(vertices_count - 1, -1, -1))
    bottom_face = tuple(range(vertices_count, vertices_count * 2))
    faces = [top_face, bottom_face]
    for index in range(vertices_count):
        next_index = (index + 1) % vertices_count
        faces.append(
            (
                index,
                next_index,
                next_index + vertices_count,
                index + vertices_count,
            )
        )
    return create_mesh_object(name, vertices, faces, material, collection, location)


def create_torus(
    name,
    major_radius,
    minor_radius,
    material,
    collection,
    location=(0, 0, 0),
):
    bpy.ops.mesh.primitive_torus_add(
        major_segments=96,
        minor_segments=8,
        major_radius=major_radius,
        minor_radius=minor_radius,
        location=location,
    )
    obj = bpy.context.object
    obj.name = name
    link_to_collection(obj, collection)
    set_material(obj, material)
    return obj


def create_sphere(name, location, radius, material, collection):
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=12,
        ring_count=6,
        radius=radius,
        location=location,
    )
    obj = bpy.context.object
    obj.name = name
    link_to_collection(obj, collection)
    set_material(obj, material)
    return obj


def create_box(name, location, scale, rotation, material, collection):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    link_to_collection(obj, collection)
    set_material(obj, material)
    return obj


def create_curve(
    name,
    points,
    material,
    collection,
    bevel_depth=0.025,
    cyclic=False,
):
    curve_data = bpy.data.curves.new(name + "_Curve", "CURVE")
    curve_data.dimensions = "3D"
    curve_data.resolution_u = 2
    curve_data.bevel_depth = bevel_depth
    curve_data.bevel_resolution = 3
    spline = curve_data.splines.new("NURBS")
    spline.points.add(len(points) - 1)
    for index, (spline_point, point) in enumerate(zip(spline.points, points)):
        spline_point.co = (point[0], point[1], point[2], 1.0)
        t = index / max(len(points) - 1, 1)
        spline_point.radius = 0.35 + 0.65 * math.sin(math.pi * t) ** 0.55
    spline.order_u = min(4, len(points))
    spline.use_endpoint_u = True
    spline.use_cyclic_u = cyclic
    obj = bpy.data.objects.new(name, curve_data)
    collection.objects.link(obj)
    obj.data.materials.append(material)
    return obj


def set_keyframes_ease(obj, data_paths=("scale", "rotation_euler", "location")):
    if not obj.animation_data or not obj.animation_data.action:
        return
    for fcurve in obj.animation_data.action.fcurves:
        if not any(fcurve.data_path.startswith(path) for path in data_paths):
            continue
        for point in fcurve.keyframe_points:
            point.interpolation = "BEZIER"
            point.handle_left_type = "AUTO_CLAMPED"
            point.handle_right_type = "AUTO_CLAMPED"


def animate_group(group, start, full, end, final_scale=1.0):
    group.scale = (0.001, 0.001, 0.001)
    group.keyframe_insert("scale", frame=start)
    group.scale = (final_scale, final_scale, final_scale)
    group.keyframe_insert("scale", frame=full)
    group.scale = (final_scale, final_scale, final_scale)
    group.keyframe_insert("scale", frame=end - 10)
    group.scale = (0.001, 0.001, 0.001)
    group.keyframe_insert("scale", frame=end)
    set_keyframes_ease(group)


def animate_beam(obj, start, full, end):
    base_z = obj.location.z
    height = max(1.0, obj.dimensions.z)
    rise = min(max(height * 0.56, 1.8), 5.2)

    obj.location = (obj.location.x, obj.location.y, base_z)
    obj.scale = (0.28, 0.28, 0.015)
    obj.keyframe_insert("scale", frame=start)
    obj.keyframe_insert("location", frame=start)
    obj.scale = (1.0, 1.0, 1.0)
    obj.keyframe_insert("scale", frame=full)
    obj.keyframe_insert("location", frame=full)
    obj.scale = (1.04, 1.04, 1.08)
    obj.keyframe_insert("scale", frame=full + 5)
    obj.scale = (0.98, 0.98, 0.98)
    obj.keyframe_insert("scale", frame=full + 10)
    obj.scale = (1.0, 1.0, 1.0)
    obj.keyframe_insert("scale", frame=end - 18)
    obj.location = (obj.location.x, obj.location.y, base_z + rise * 0.58)
    obj.scale = (0.58, 0.58, 0.32)
    obj.keyframe_insert("location", frame=end - 14)
    obj.keyframe_insert("scale", frame=end - 14)
    obj.location = (obj.location.x, obj.location.y, base_z + rise)
    obj.scale = (0.001, 0.001, 0.001)
    obj.keyframe_insert("location", frame=end)
    obj.keyframe_insert("scale", frame=end)
    set_keyframes_ease(obj, ("scale", "location"))


def animate_plus(obj, target_location, start, full, end, drop=1.8):
    target = Vector(target_location)
    start_z = max(0.06, target.z - drop * 0.72)
    rise = max(1.8, drop * 1.35)
    direction = 1.0 if target.x >= 0.0 else -1.0
    obj.location = (target.x, target.y, start_z)
    obj.scale = (0.001, 0.001, 0.001)
    obj.rotation_euler = (0.0, direction * -0.85, 0.0)
    obj.keyframe_insert("location", frame=start)
    obj.keyframe_insert("scale", frame=start)
    obj.keyframe_insert("rotation_euler", frame=start)
    obj.location = target
    obj.scale = (0.88, 0.88, 0.88)
    obj.rotation_euler = (0.0, direction * 0.40, 0.0)
    obj.keyframe_insert("location", frame=full)
    obj.keyframe_insert("scale", frame=full)
    obj.keyframe_insert("rotation_euler", frame=full)
    obj.scale = (1.0, 1.0, 1.0)
    obj.rotation_euler = (0.0, direction * 1.55, 0.0)
    obj.keyframe_insert("scale", frame=end - 16)
    obj.keyframe_insert("rotation_euler", frame=end - 16)
    obj.location = target + Vector((0.0, 0.0, rise))
    obj.rotation_euler = (0.0, direction * math.tau * 1.15, 0.0)
    obj.scale = (0.001, 0.001, 0.001)
    obj.keyframe_insert("location", frame=end)
    obj.keyframe_insert("scale", frame=end)
    obj.keyframe_insert("rotation_euler", frame=end)
    set_keyframes_ease(obj)


def animate_ring(obj, start, full, end, final_scale=1.0):
    obj.scale = (0.04, 0.04, 0.04)
    obj.keyframe_insert("scale", frame=start)
    obj.scale = (final_scale * 0.72, final_scale * 0.72, final_scale * 0.72)
    obj.keyframe_insert("scale", frame=full)
    obj.scale = (final_scale, final_scale, final_scale)
    obj.keyframe_insert("scale", frame=end - 12)
    obj.scale = (final_scale * 1.08, final_scale * 1.08, final_scale * 1.08)
    obj.keyframe_insert("scale", frame=end)
    set_keyframes_ease(obj, ("scale",))


def build_environment(scene, materials):
    collection = bpy.data.collections.new("ENVIRONMENT")
    scene.collection.children.link(collection)
    create_disc("Ground_Disc", 7.2, materials["ground"], collection, (0, 0, -0.025), 96)
    backdrop = create_box(
        "Backdrop",
        (0.0, 5.8, 4.5),
        (18.0, 0.08, 11.0),
        (0, 0, 0),
        materials["background"],
        collection,
    )
    backdrop["role"] = "backdrop"
    return collection


def build_ground_energy(scene, materials):
    collection = bpy.data.collections.new("GROUND_ENERGY")
    scene.collection.children.link(collection)
    root = create_empty("CTRL_GroundEnergy", collection)
    rings = create_empty("CTRL_GroundRings", collection)
    glyphs = create_empty("CTRL_GroundGlyphs", collection)
    rings.parent = root
    glyphs.parent = root

    ring_specs = [
        ("Ground_Ring_01", 1.4, 0.025, materials["lime"], 1, 8, 108),
        ("Ground_Ring_02", 2.25, 0.022, materials["green"], 3, 11, 116),
        ("Ground_Ring_03", 3.25, 0.020, materials["teal"], 6, 15, 124),
        ("Ground_Ring_04", 4.55, 0.018, materials["green"], 9, 19, 132),
        ("Ground_Ring_05", 6.00, 0.015, materials["teal"], 13, 24, 138),
    ]
    for name, radius, minor, material, start, full, end in ring_specs:
        ring = create_torus(name, radius, minor, material, collection, (0, 0, 0.025))
        ring.parent = rings
        animate_ring(ring, start, full, end, 1.0)

    for ring_index, radius in enumerate((2.65, 3.75, 5.0)):
        count = 18 + ring_index * 6
        for index in range(count):
            angle = math.tau * index / count
            x = math.cos(angle) * radius
            y = math.sin(angle) * radius
            mark = create_box(
                f"Ground_Tick_{ring_index}_{index:02d}",
                (x, y, 0.04),
                (0.10 + ring_index * 0.02, 0.018, 0.008),
                (0, 0, angle),
                materials["lime"] if index % 3 == 0 else materials["green"],
                collection,
            )
            mark.parent = glyphs

    arc_specs = [
        (2.8, 0.25, 1.40, materials["lime"]),
        (3.9, 2.30, 3.25, materials["teal"]),
        (4.8, 4.10, 5.55, materials["green"]),
        (5.75, 1.15, 3.55, materials["lime"]),
    ]
    for index, (radius, start_angle, end_angle, material) in enumerate(arc_specs):
        points = []
        samples = 32
        for point_index in range(samples):
            t = point_index / (samples - 1)
            angle = start_angle + (end_angle - start_angle) * t
            points.append(
                (
                    math.cos(angle) * radius,
                    math.sin(angle) * radius,
                    0.045 + math.sin(t * math.pi * 4.0) * 0.008,
                )
            )
        arc = create_curve(
            f"Ground_Arc_{index}",
            points,
            material,
            collection,
            bevel_depth=0.035 if index == 0 else 0.022,
        )
        arc.parent = glyphs

    wavy_points = []
    for index in range(96):
        angle = math.tau * index / 95
        radius = 2.9 + math.sin(angle * 5.0) * 0.16 + math.sin(angle * 11.0) * 0.07
        wavy_points.append((math.cos(angle) * radius, math.sin(angle) * radius, 0.055))
    wavy = create_curve(
        "Ground_WaveRing",
        wavy_points,
        materials["lime"],
        collection,
        bevel_depth=0.030,
        cyclic=True,
    )
    wavy.parent = glyphs
    animate_ring(wavy, 5, 20, 118, 1.0)

    impact = create_disc(
        "Ground_ImpactGlow", 1.15, materials["mist"], collection, (0, 0, 0.065), 64
    )
    impact.parent = root
    impact.scale = (0.02, 0.02, 0.02)
    impact.keyframe_insert("scale", frame=1)
    impact.scale = (1.0, 1.0, 1.0)
    impact.keyframe_insert("scale", frame=9)
    impact.scale = (1.12, 1.12, 1.12)
    impact.keyframe_insert("scale", frame=82)
    impact.scale = (0.02, 0.02, 0.02)
    impact.keyframe_insert("scale", frame=128)
    set_keyframes_ease(impact, ("scale",))

    for index in range(4):
        wave = create_disc(
            f"Ground_ShockDisc_{index}",
            2.2 + index * 0.75,
            materials["mist"] if index % 2 == 0 else materials["beam_shell"],
            collection,
            (0, 0, 0.07 + index * 0.003),
            64,
        )
        wave.parent = root
        start = 10 + index * 7
        full = 19 + index * 8
        end = 112 + index * 7
        wave.scale = (0.03, 0.03, 0.03)
        wave.keyframe_insert("scale", frame=start)
        wave.scale = (1.0, 1.0, 1.0)
        wave.keyframe_insert("scale", frame=full)
        wave.scale = (1.18, 1.18, 1.18)
        wave.keyframe_insert("scale", frame=end)
        wave.scale = (0.001, 0.001, 0.001)
        wave.keyframe_insert("scale", frame=min(end + 18, 158))
        set_keyframes_ease(wave, ("scale",))

    return collection, root


def build_beams(scene, materials):
    collection = bpy.data.collections.new("BEAM_SYSTEM")
    scene.collection.children.link(collection)
    root = create_empty("CTRL_BeamSystem", collection)
    beam_specs = [
        ("Beam_Main", 0.0, 0.0, 8.6, 0.105, 8, 20, 112),
        ("Beam_L_01", -1.25, 0.35, 7.8, 0.075, 12, 24, 116),
        ("Beam_R_01", 1.18, -0.42, 8.0, 0.078, 14, 27, 118),
        ("Beam_L_02", -2.45, -0.55, 7.2, 0.055, 18, 32, 122),
        ("Beam_R_02", 2.55, 0.48, 7.1, 0.058, 20, 34, 124),
        ("Beam_L_03", -3.45, 0.65, 6.5, 0.044, 24, 38, 128),
        ("Beam_R_03", 3.30, -0.70, 6.4, 0.043, 26, 40, 130),
        ("Beam_Back_01", -0.65, 1.55, 6.8, 0.046, 30, 44, 132),
        ("Beam_Back_02", 0.72, -1.50, 6.7, 0.048, 32, 47, 134),
    ]
    beams = []
    for index, spec in enumerate(beam_specs):
        name, x, y, height, radius, start, full, end = spec
        core_material = materials["core"] if index < 3 else materials["lime"]
        core = create_cylinder_from_top(
            name + "_Core",
            radius,
            height,
            core_material,
            collection,
            (x, y, 0.035),
            32,
        )
        shell = create_cylinder_from_top(
            name + "_Shell",
            radius * (2.3 + (index % 3) * 0.25),
            height,
            materials["beam_shell"],
            collection,
            (x, y, 0.035),
            32,
        )
        core.parent = root
        shell.parent = root
        animate_beam(core, start, full, end)
        animate_beam(shell, start - 1, full + 1, end + 1)
        beams.extend((core, shell))

    for index in range(22):
        angle = random.uniform(0, math.tau)
        radius = random.uniform(0.6, 4.4)
        x = math.cos(angle) * radius
        y = math.sin(angle) * radius * 0.58
        height = random.uniform(3.5, 8.2)
        start = random.randint(28, 80)
        full = start + random.randint(12, 26)
        end = random.randint(108, 148)
        streak = create_cylinder_from_top(
            f"Vertical_Streak_{index:02d}",
            random.uniform(0.012, 0.035),
            height,
            materials["lime"] if index % 3 else materials["teal"],
            collection,
            (x, y, 0.04),
            12,
        )
        streak.parent = root
        animate_beam(streak, start, full, end)

    source = create_sphere(
        "Beam_SourceCore",
        (0.0, 0.0, 0.16),
        0.24,
        materials["core"],
        collection,
    )
    source.parent = root
    source.scale = (0.001, 0.001, 0.001)
    source.keyframe_insert("scale", frame=2)
    source.keyframe_insert("location", frame=2)
    source.scale = (1.2, 1.2, 1.2)
    source.keyframe_insert("scale", frame=18)
    source.scale = (1.45, 1.45, 1.45)
    source.keyframe_insert("scale", frame=76)
    source.location = (0.0, 0.0, 3.4)
    source.scale = (0.32, 0.32, 0.32)
    source.keyframe_insert("location", frame=116)
    source.keyframe_insert("scale", frame=116)
    source.location = (0.0, 0.0, 5.4)
    source.scale = (0.001, 0.001, 0.001)
    source.keyframe_insert("location", frame=138)
    source.keyframe_insert("scale", frame=138)
    set_keyframes_ease(source)

    return collection, root, beams


def build_crosses(scene, materials):
    collection = bpy.data.collections.new("CROSS_SIGILS")
    scene.collection.children.link(collection)
    root = create_empty("CTRL_CrossSigils", collection)
    front = create_empty("CTRL_Cross_Front", collection)
    middle = create_empty("CTRL_Cross_Middle", collection)
    back = create_empty("CTRL_Cross_Back", collection)
    front.parent = root
    middle.parent = root
    back.parent = root

    cross_specs = [
        ("Cross_Main_L", (-3.65, 0.85, 4.55), 1.08, 0.42, 22, 38, 136),
        ("Cross_Top_C", (0.15, 0.30, 6.10), 0.70, 0.41, 18, 32, 132),
        ("Cross_Main_R", (3.35, -0.20, 4.35), 0.93, 0.42, 27, 43, 138),
        ("Cross_Mid_L", (-2.05, -0.70, 2.70), 0.62, 0.42, 32, 48, 140),
        ("Cross_Mid_R", (2.00, 0.72, 2.20), 0.60, 0.42, 36, 52, 142),
        ("Cross_Low_L", (-3.45, 0.45, 0.78), 0.53, 0.43, 41, 58, 144),
        ("Cross_Low_R", (3.85, -0.65, 1.25), 0.76, 0.42, 45, 62, 146),
        ("Cross_Front_C", (0.62, -1.05, 1.55), 0.50, 0.42, 50, 67, 148),
        ("Cross_Back_C", (-0.82, 1.05, 5.20), 0.48, 0.40, 54, 72, 150),
    ]
    for index, spec in enumerate(cross_specs):
        name, location, size, ratio, start, full, end = spec
        cross = create_plus_mesh(
            name,
            size,
            ratio,
            0.14 + size * 0.08,
            materials["lime"],
            collection,
            location,
        )
        if index < 2:
            cross.parent = front
        elif index < 6:
            cross.parent = middle
        else:
            cross.parent = back
        animate_plus(cross, location, start, full, end, 1.5 + size)
        if size >= 0.58:
            halo = create_plus_mesh(
                name + "_Halo",
                size * 1.28,
                ratio,
                (0.14 + size * 0.08) * 1.45,
                materials["mist"],
                collection,
            )
            halo.parent = cross
            halo.location = (0, 0, 0)
            halo.scale = (1.0, 1.0, 1.0)

    random_specs = [
        (-4.5, 0.8, 3.1, 0.30, 30, 52),
        (-4.15, -0.6, 5.6, 0.24, 36, 58),
        (-2.80, 1.25, 6.3, 0.27, 42, 66),
        (-1.25, -1.45, 4.10, 0.22, 46, 68),
        (1.20, 1.30, 5.60, 0.26, 49, 71),
        (2.85, 1.10, 3.25, 0.29, 52, 73),
        (4.45, 0.55, 5.45, 0.25, 55, 76),
        (4.20, -1.15, 2.05, 0.31, 58, 79),
        (-1.85, -1.25, 1.30, 0.23, 62, 83),
        (0.10, 1.45, 2.30, 0.20, 66, 87),
        (-3.05, 1.32, 1.80, 0.25, 69, 89),
        (2.35, -1.40, 6.30, 0.21, 72, 92),
    ]
    for index, (x, y, z, size, start, full) in enumerate(random_specs):
        cross = create_plus_mesh(
            f"Cross_Detail_{index:02d}",
            size,
            0.42,
            0.06,
            materials["green"] if index % 3 else materials["lime"],
            collection,
            (x, y, z),
        )
        cross.parent = middle if index % 2 else back
        animate_plus(
            cross,
            (x, y, z),
            start,
            full,
            142 + index % 10,
            1.2 + size * 0.8,
        )

    return collection, root, cross_specs


def build_particles(scene, materials):
    collection = bpy.data.collections.new("PARTICLES")
    scene.collection.children.link(collection)
    root = create_empty("CTRL_Particles", collection)
    rising_sparks = create_empty("CTRL_RisingSparks", collection)
    rising = create_empty("CTRL_RisingMotes", collection)
    bokeh = create_empty("CTRL_Bokeh", collection)
    rising_sparks.parent = root
    rising.parent = root
    bokeh.parent = root

    for index in range(120):
        angle = random.uniform(0, math.tau)
        radius = random.uniform(0.25, 4.8)
        x = math.cos(angle) * radius
        y = math.sin(angle) * radius * 0.58
        start_z = random.uniform(0.08, 0.8)
        end_z = random.uniform(2.8, 7.2)
        start = random.randint(12, 82)
        full = start + random.randint(22, 44)
        size = random.uniform(0.012, 0.055)
        material = materials["core"] if index % 7 == 0 else materials["lime"]
        spark = create_sphere(
            f"Spark_{index:03d}",
            (x, y, start_z),
            size,
            material,
            collection,
        )
        spark.parent = rising_sparks
        spark.scale = (0.001, 0.001, 0.001)
        spark.keyframe_insert("scale", frame=start)
        spark.keyframe_insert("location", frame=start)
        spark.location = (x, y, end_z)
        spark.scale = (1.0, 1.0, 1.0)
        spark.keyframe_insert("location", frame=full)
        spark.keyframe_insert("scale", frame=full)
        spark.scale = (0.72, 0.72, 0.72)
        spark.keyframe_insert("scale", frame=min(full + 18, 148))
        spark.scale = (0.001, 0.001, 0.001)
        spark.keyframe_insert("scale", frame=min(full + 36, 158))
        set_keyframes_ease(spark)

    for index in range(44):
        angle = random.uniform(0, math.tau)
        radius = random.uniform(0.35, 5.6)
        x = math.cos(angle) * radius
        y = math.sin(angle) * radius * 0.62
        start_z = random.uniform(0.15, 1.0)
        end_z = random.uniform(3.5, 7.2)
        start = random.randint(8, 68)
        full = start + random.randint(30, 54)
        mote = create_sphere(
            f"Rising_Mote_{index:03d}",
            (x, y, start_z),
            random.uniform(0.018, 0.065),
            materials["teal"] if index % 4 else materials["lime"],
            collection,
        )
        mote.parent = rising
        mote.scale = (0.001, 0.001, 0.001)
        mote.keyframe_insert("scale", frame=start)
        mote.keyframe_insert("location", frame=start)
        mote.location = (x, y, end_z)
        mote.scale = (1.0, 1.0, 1.0)
        mote.keyframe_insert("location", frame=full)
        mote.keyframe_insert("scale", frame=full)
        mote.scale = (0.001, 0.001, 0.001)
        mote.keyframe_insert("scale", frame=min(full + 30, 152))
        set_keyframes_ease(mote)

    for index in range(24):
        angle = random.uniform(0, math.tau)
        radius = random.uniform(0.8, 4.5)
        x = math.cos(angle) * radius
        y = random.uniform(-1.8, 1.8)
        z = random.uniform(0.8, 7.0)
        start = random.randint(24, 72)
        full = start + random.randint(20, 40)
        orb = create_sphere(
            f"Bokeh_{index:02d}",
            (x, y, z),
            random.uniform(0.09, 0.23),
            materials["mist"],
            collection,
        )
        orb.parent = bokeh
        orb.scale = (0.001, 0.001, 0.001)
        orb.keyframe_insert("scale", frame=start)
        orb.scale = (1.0, 1.0, 1.0)
        orb.keyframe_insert("scale", frame=full)
        orb.scale = (1.18, 1.18, 1.18)
        orb.keyframe_insert("scale", frame=136)
        orb.scale = (0.001, 0.001, 0.001)
        orb.keyframe_insert("scale", frame=156)
        set_keyframes_ease(orb, ("scale",))

    return collection, root


def build_lights(scene, materials):
    collection = bpy.data.collections.new("EFFECT_LIGHTS")
    scene.collection.children.link(collection)
    lights = []
    specs = [
        ("Light_Main", (0.0, 0.0, 3.5), (0.22, 1.0, 0.24), 900, 4.0),
        ("Light_Left", (-2.1, 1.0, 2.0), (0.10, 0.95, 0.15), 420, 3.0),
        ("Light_Right", (2.3, -0.8, 2.2), (0.05, 0.90, 0.30), 500, 3.2),
    ]
    for index, (name, location, color, peak, radius) in enumerate(specs):
        data = bpy.data.lights.new(name, "POINT")
        data.color = color
        data.energy = 0.0
        data.shadow_soft_size = radius
        obj = bpy.data.objects.new(name, data)
        obj.location = location
        collection.objects.link(obj)
        start = 2 + index * 3
        full = 16 + index * 4
        profile = [
            (start, 0.0),
            (full, peak),
            (78, peak * 1.12),
            (112, peak * 0.82),
            (138 - index * 2, 0.0),
        ]
        for frame, energy in profile:
            data.energy = energy
            data.keyframe_insert("energy", frame=frame)
        set_keyframes_ease(obj)
        lights.append(obj)
    return collection, lights


def build_camera(scene, effect_collection):
    camera_data = bpy.data.cameras.new("Green_Effect_Camera")
    camera = bpy.data.objects.new("Green_Effect_Camera", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera.data.lens = 52.0
    camera.data.sensor_width = 36.0
    camera.data.dof.use_dof = True
    camera.data.dof.focus_distance = 14.0
    camera.data.dof.aperture_fstop = 5.6

    target = create_empty(
        "CAM_Green_Target", effect_collection, (0.0, 0.0, 2.05)
    )
    constraint = camera.constraints.new("TRACK_TO")
    constraint.target = target
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"

    camera_moves = [
        (1, (10.0, -14.2, 6.2), (0.0, 0.0, 2.15), 50.0),
        (24, (9.7, -13.7, 5.75), (0.0, 0.0, 2.05), 50.0),
        (34, (9.55, -13.4, 5.55), (0.0, 0.0, 1.90), 51.0),
        (37, (9.72, -13.55, 5.68), (0.08, 0.0, 1.96), 51.0),
        (42, (9.45, -13.30, 5.38), (-0.05, 0.0, 1.82), 52.0),
        (58, (9.30, -13.10, 5.18), (0.0, 0.0, 1.72), 54.0),
        (84, (9.10, -12.85, 5.05), (0.0, 0.0, 1.65), 55.0),
        (112, (9.42, -13.25, 5.32), (0.0, 0.0, 1.80), 53.0),
        (138, (9.85, -13.85, 5.80), (0.0, 0.0, 2.00), 51.0),
        (160, (10.15, -14.35, 6.35), (0.0, 0.0, 2.18), 50.0),
    ]
    for frame, location, target_location, lens in camera_moves:
        camera.location = location
        camera.data.lens = lens
        target.location = target_location
        camera.keyframe_insert("location", frame=frame)
        camera.data.keyframe_insert("lens", frame=frame)
        target.keyframe_insert("location", frame=frame)

    return camera, target


def build_compositor(scene):
    scene.use_nodes = True
    tree = scene.node_tree
    nodes = tree.nodes
    links = tree.links
    nodes.clear()

    render_layers = nodes.new("CompositorNodeRLayers")
    glare_small = nodes.new("CompositorNodeGlare")
    glare_small.glare_type = "FOG_GLOW"
    glare_small.quality = "HIGH"
    glare_small.threshold = 0.58
    glare_small.size = 7
    glare_small.mix = -0.24
    glare_wide = nodes.new("CompositorNodeGlare")
    glare_wide.glare_type = "GHOSTS"
    glare_wide.quality = "HIGH"
    glare_wide.threshold = 0.62
    glare_wide.mix = -0.76
    glare_wide.iterations = 3
    color = nodes.new("CompositorNodeColorBalance")
    color.correction_method = "LIFT_GAMMA_GAIN"
    color.gamma = (0.96, 1.02, 0.98)
    lens = nodes.new("CompositorNodeLensdist")
    lens.inputs["Distortion"].default_value = 0.008
    lens.inputs["Dispersion"].default_value = 0.012
    composite = nodes.new("CompositorNodeComposite")
    links.new(render_layers.outputs["Image"], glare_small.inputs["Image"])
    links.new(glare_small.outputs["Image"], glare_wide.inputs["Image"])
    links.new(glare_wide.outputs["Image"], color.inputs["Image"])
    links.new(color.outputs["Image"], lens.inputs["Image"])
    links.new(lens.outputs["Image"], composite.inputs["Image"])


def configure_scene(scene):
    scene.name = "GreenShootingEffect_V1"
    scene.frame_start = 1
    scene.frame_end = 160
    scene.render.fps = 30
    scene.render.resolution_x = 720
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    scene.render.filepath = os.path.join(PREVIEW_DIR, "green_shooting_")
    scene.render.use_overwrite = True
    scene.render.use_file_extension = True
    try:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    except Exception:
        scene.render.engine = "BLENDER_EEVEE"
    scene.view_settings.view_transform = "AgX"
    try:
        scene.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        pass
    scene.view_settings.exposure = -0.48
    scene.view_settings.gamma = 1.0
    if hasattr(scene, "eevee"):
        for attr in ("taa_render_samples", "taa_samples"):
            if hasattr(scene.eevee, attr):
                setattr(scene.eevee, attr, 32)
    world = scene.world if scene.world else bpy.data.worlds.new("Green_World")
    scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    if background:
        background.inputs["Color"].default_value = (0.0002, 0.0025, 0.0005, 1.0)
        background.inputs["Strength"].default_value = 0.035


def write_manifest(scene):
    manifest = {
        "scene": scene.name,
        "frames": [scene.frame_start, scene.frame_end],
        "fps": scene.render.fps,
        "resolution": [scene.render.resolution_x, scene.render.resolution_y],
        "engine": scene.render.engine,
        "collections": [collection.name for collection in scene.collection.children],
        "phases": {
            "ground_healing_wave": [1, 24],
            "rising_line_energy": [8, 72],
            "cross_follow_rise": [18, 104],
            "healing_sustain": [72, 118],
            "rotate_shrink_dissolve": [104, 160],
        },
        "controls": [
            "CTRL_GroundEnergy",
            "CTRL_BeamSystem",
            "CTRL_CrossSigils",
            "CTRL_Particles",
        ],
    }
    path = os.path.join(OUTPUT_DIR, "GREEN_SHOOTING_EFFECT_V1_MANIFEST.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)


def main():
    ensure_dirs()
    scene = bpy.context.scene
    clear_scene(scene)
    configure_scene(scene)
    materials = build_materials()
    build_environment(scene, materials)
    build_ground_energy(scene, materials)
    build_beams(scene, materials)
    build_crosses(scene, materials)
    build_particles(scene, materials)
    build_lights(scene, materials)
    master = create_empty("GREEN_EFFECT_MASTER", scene.collection)
    master.location = (0, 0, 0)
    build_camera(scene, scene.collection)
    build_compositor(scene)
    for material in materials.values():
        if isinstance(material, bpy.types.Material) and material.get("strength_node"):
            animate_emission_material(material)
    scene.frame_set(1)
    write_manifest(scene)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print("GREEN_EFFECT_BUILD_OK")
    print(BLEND_PATH)
    print("OBJECTS", len(scene.objects))


main()
