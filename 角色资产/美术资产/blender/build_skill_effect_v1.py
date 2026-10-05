import bpy
import json
import math
import os
import random
from mathutils import Vector


OUTPUT_DIR = r"I:\工作项目\blender\skill_effect_v1"
BLEND_PATH = os.path.join(OUTPUT_DIR, "skill_effect_v1.blend")
PREVIEW_DIR = os.path.join(OUTPUT_DIR, "previews")
random.seed(20260915)


def ensure_dirs():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(PREVIEW_DIR, exist_ok=True)


def clear_scene():
    scene = bpy.context.scene
    for collection in list(scene.collection.children):
        for obj in list(collection.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        scene.collection.children.unlink(collection)
        bpy.data.collections.remove(collection)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (
        bpy.data.curves,
        bpy.data.meshes,
        bpy.data.materials,
        bpy.data.cameras,
        bpy.data.lights,
    ):
        for datablock in list(datablocks):
            if datablock.users == 0:
                datablocks.remove(datablock)


def set_input(node, name, value):
    socket = node.inputs.get(name)
    if socket is not None:
        socket.default_value = value


def set_principled(material, base_color, metallic=0.0, roughness=0.35, alpha=1.0):
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    principled = nodes.new("ShaderNodeBsdfPrincipled")
    principled.inputs["Base Color"].default_value = base_color
    principled.inputs["Metallic"].default_value = metallic
    principled.inputs["Roughness"].default_value = roughness
    if principled.inputs.get("Alpha"):
        principled.inputs["Alpha"].default_value = alpha
    material.node_tree.links.new(principled.outputs["BSDF"], output.inputs["Surface"])
    if alpha < 1.0:
        try:
            material.surface_render_method = "DITHERED"
        except Exception:
            pass
        try:
            material.blend_method = "BLEND"
        except Exception:
            pass
    return material


def make_emission_material(name, color, strength=8.0, secondary=None, noise_scale=4.0):
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

    noise.inputs["Scale"].default_value = noise_scale
    noise.inputs["Detail"].default_value = 4.0
    noise.inputs["Roughness"].default_value = 0.65
    ramp.color_ramp.elements[0].position = 0.18
    ramp.color_ramp.elements[0].color = color
    ramp.color_ramp.elements[1].position = 0.82
    ramp.color_ramp.elements[1].color = secondary if secondary else color

    emission.inputs["Strength"].default_value = strength
    links.new(texcoord.outputs["Generated"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], emission.inputs["Color"])
    links.new(emission.outputs["Emission"], output.inputs["Surface"])
    return material


def make_translucent_glow_material(name, color, strength=5.0, alpha=0.45):
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
    ramp = nodes.new("ShaderNodeValToRGB")
    noise = nodes.new("ShaderNodeTexNoise")
    texcoord = nodes.new("ShaderNodeTexCoord")

    emission.inputs["Color"].default_value = color
    emission.inputs["Strength"].default_value = strength
    noise.inputs["Scale"].default_value = 5.0
    noise.inputs["Detail"].default_value = 5.0
    fresnel.inputs["IOR"].default_value = 1.45
    ramp.color_ramp.elements[0].position = 0.08
    ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    ramp.color_ramp.elements[1].position = 0.88
    ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

    links.new(texcoord.outputs["Generated"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], mix.inputs[0])
    links.new(fresnel.outputs["Fac"], mix.inputs[0])
    links.new(transparent.outputs["BSDF"], mix.inputs[1])
    links.new(emission.outputs["Emission"], mix.inputs[2])
    links.new(mix.outputs["Shader"], output.inputs["Surface"])

    try:
        material.surface_render_method = "DITHERED"
    except Exception:
        pass
    try:
        material.blend_method = "BLEND"
    except Exception:
        pass
    return material


def link_object(obj, collection=None):
    if collection is not None:
        for old_collection in list(obj.users_collection):
            old_collection.objects.unlink(obj)
        collection.objects.link(obj)
    return obj


def create_empty(name, collection, location=(0.0, 0.0, 0.0)):
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_type = "PLAIN_AXES"
    obj.empty_display_size = 0.4
    obj.location = location
    collection.objects.link(obj)
    return obj


def set_material(obj, material):
    if obj.data and hasattr(obj.data, "materials"):
        obj.data.materials.append(material)


def create_poly_curve(
    name,
    points,
    material,
    collection,
    bevel_depth=0.05,
    cyclic=False,
    bevel_resolution=2,
):
    curve = bpy.data.curves.new(name + "_Curve", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 2
    curve.bevel_depth = bevel_depth
    curve.bevel_resolution = bevel_resolution
    curve.resolution_u = 4
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for bezier_point, point in zip(spline.bezier_points, points):
        bezier_point.co = point
        bezier_point.handle_left_type = "AUTO"
        bezier_point.handle_right_type = "AUTO"
    spline.use_cyclic_u = cyclic
    obj = bpy.data.objects.new(name, curve)
    collection.objects.link(obj)
    obj.data.materials.append(material)
    return obj


def create_smooth_curve(
    name,
    points,
    material,
    collection,
    bevel_depth=0.05,
    cyclic=False,
):
    curve = bpy.data.curves.new(name + "_Curve", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 2
    curve.bevel_depth = bevel_depth
    curve.bevel_resolution = 3
    spline = curve.splines.new("NURBS")
    spline.points.add(len(points) - 1)
    for index, (spline_point, point) in enumerate(zip(spline.points, points)):
        spline_point.co = (point[0], point[1], point[2], 1.0)
        t = index / max(len(points) - 1, 1)
        spline_point.radius = 0.16 + 0.84 * (math.sin(math.pi * t) ** 0.65)
    spline.order_u = min(4, len(points))
    spline.use_endpoint_u = True
    spline.use_cyclic_u = cyclic
    obj = bpy.data.objects.new(name, curve)
    collection.objects.link(obj)
    obj.data.materials.append(material)
    return obj


def create_ellipse_curve(
    name,
    center,
    radius_x,
    radius_z,
    material,
    collection,
    bevel_depth=0.05,
    segments=32,
):
    points = []
    for index in range(segments):
        angle = 2.0 * math.pi * index / segments
        points.append(
            (
                center[0] + math.cos(angle) * radius_x,
                center[1],
                center[2] + math.sin(angle) * radius_z,
            )
        )
    return create_poly_curve(
        name,
        points,
        material,
        collection,
        bevel_depth=bevel_depth,
        cyclic=True,
    )


def create_spiral_points(phase, turns, radius_min, radius_max, depth=0.0, samples=64):
    points = []
    for index in range(samples):
        t = index / (samples - 1)
        angle = phase + turns * 2.0 * math.pi * t
        radius = radius_min + (radius_max - radius_min) * (t ** 0.78)
        x = math.cos(angle) * radius
        z = math.sin(angle) * radius * 0.72
        y = depth * math.sin(t * math.pi * 3.0 + phase) + depth * 0.25
        points.append((x, y, z))
    return points


def create_spiral(
    name,
    phase,
    turns,
    radius_min,
    radius_max,
    bevel_depth,
    material,
    collection,
    depth=0.0,
    samples=64,
):
    return create_smooth_curve(
        name,
        create_spiral_points(phase, turns, radius_min, radius_max, depth, samples),
        material,
        collection,
        bevel_depth,
    )


def create_disc_mesh(name, radius_x, radius_z, material, collection, segments=64):
    vertices = []
    faces = []
    vertices.append((0.0, 0.0, 0.0))
    for index in range(segments):
        angle = 2.0 * math.pi * index / segments
        vertices.append((math.cos(angle) * radius_x, 0.0, math.sin(angle) * radius_z))
    for index in range(segments):
        faces.append((0, index + 1, ((index + 1) % segments) + 1))
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj.data.materials.append(material)
    return obj


def create_log_spiral(
    name,
    center,
    direction,
    material,
    collection,
    turns=2.7,
    radius_max=0.62,
    bevel_depth=0.07,
    samples=48,
):
    points = []
    for index in range(samples):
        t = index / (samples - 1)
        angle = direction * turns * 2.0 * math.pi * t
        radius = 0.035 + radius_max * (1.0 - t) ** 0.82
        points.append(
            (
                center[0] + math.cos(angle) * radius,
                center[1],
                center[2] + math.sin(angle) * radius,
            )
        )
    return create_smooth_curve(
        name,
        points,
        material,
        collection,
        bevel_depth=bevel_depth,
    )


def animate_group(
    group,
    start,
    full,
    initial_scale=0.001,
    peak_scale=1.0,
    spin=0.0,
    pulse=0.0,
):
    group.scale = (initial_scale, initial_scale, initial_scale)
    group.rotation_euler[1] = -spin
    group.keyframe_insert("scale", frame=start)
    group.keyframe_insert("rotation_euler", frame=start)

    group.scale = (peak_scale * 0.86, peak_scale * 0.86, peak_scale * 0.86)
    group.rotation_euler[1] = spin * 0.42
    group.keyframe_insert("scale", frame=full)
    group.keyframe_insert("rotation_euler", frame=full)

    group.scale = (peak_scale, peak_scale, peak_scale)
    group.rotation_euler[1] = spin
    group.keyframe_insert("scale", frame=min(full + 18, 160))
    group.keyframe_insert("rotation_euler", frame=min(full + 18, 160))

    if pulse:
        group.scale = (
            peak_scale * (1.0 + pulse),
            peak_scale * (1.0 + pulse),
            peak_scale * (1.0 + pulse),
        )
        group.keyframe_insert("scale", frame=132)
        group.scale = (peak_scale, peak_scale, peak_scale)
        group.keyframe_insert("scale", frame=160)

    if group.animation_data and group.animation_data.action:
        for fcurve in group.animation_data.action.fcurves:
            for keyframe in fcurve.keyframe_points:
                keyframe.interpolation = "BEZIER"


def animate_parented_start(obj, start, full, peak_scale=1.0):
    obj.scale = (0.001, 0.001, 0.001)
    obj.keyframe_insert("scale", frame=start)
    obj.scale = (peak_scale * 0.90, peak_scale * 0.90, peak_scale * 0.90)
    obj.keyframe_insert("scale", frame=full)
    obj.scale = (peak_scale, peak_scale, peak_scale)
    obj.keyframe_insert("scale", frame=min(full + 16, 160))


def create_uv_sphere(name, location, radius, material, collection, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=24,
        ring_count=12,
        radius=radius,
        location=location,
    )
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    link_object(obj, collection)
    set_material(obj, material)
    return obj


def create_torus(
    name,
    location,
    major_radius,
    minor_radius,
    material,
    collection,
    rotation=(math.radians(90), 0, 0),
):
    bpy.ops.mesh.primitive_torus_add(
        major_segments=64,
        minor_segments=8,
        major_radius=major_radius,
        minor_radius=minor_radius,
        location=location,
        rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    link_object(obj, collection)
    set_material(obj, material)
    return obj


def create_box(name, location, scale, rotation, material, collection):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    link_object(obj, collection)
    set_material(obj, material)
    return obj


def create_plane(name, location, rotation, scale, material, collection):
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    link_object(obj, collection)
    set_material(obj, material)
    return obj


def build_materials():
    materials = {}
    materials["void"] = set_principled(
        bpy.data.materials.new("MAT_Void"),
        (0.0005, 0.0008, 0.002, 1.0),
        metallic=0.25,
        roughness=0.2,
    )
    materials["violet"] = make_emission_material(
        "MAT_VioletEnergy", (0.025, 0.003, 0.09, 1.0), 1.8, (0.46, 0.05, 1.0, 1.0), 5.0
    )
    materials["indigo"] = make_emission_material(
        "MAT_IndigoEnergy", (0.015, 0.015, 0.12, 1.0), 1.9, (0.15, 0.11, 1.0, 1.0), 7.0
    )
    materials["cyan"] = make_emission_material(
        "MAT_CyanEnergy", (0.02, 0.65, 1.0, 1.0), 2.8, (0.48, 1.0, 1.0, 1.0), 9.0
    )
    materials["pink"] = make_emission_material(
        "MAT_PinkEnergy", (0.8, 0.025, 1.0, 1.0), 2.8, (1.0, 0.20, 0.72, 1.0), 8.0
    )
    materials["white"] = make_emission_material(
        "MAT_WhiteCore", (0.72, 0.95, 1.0, 1.0), 3.6, (1.0, 0.96, 1.0, 1.0), 4.0
    )
    materials["gold"] = make_emission_material(
        "MAT_GoldRune", (1.0, 0.42, 0.035, 1.0), 3.0, (1.0, 0.92, 0.52, 1.0), 3.0
    )
    materials["ribbon_purple"] = make_translucent_glow_material(
        "MAT_RibbonPurple", (0.15, 0.015, 0.48, 1.0), 1.6, 0.45
    )
    materials["ribbon_cyan"] = make_translucent_glow_material(
        "MAT_RibbonCyan", (0.02, 0.38, 1.0, 1.0), 1.8, 0.38
    )
    materials["smoke"] = make_translucent_glow_material(
        "MAT_SmokeViolet", (0.09, 0.004, 0.24, 1.0), 1.1, 0.20
    )
    materials["shard"] = set_principled(
        bpy.data.materials.new("MAT_OpaqueShard"),
        (0.015, 0.002, 0.035, 1.0),
        metallic=0.22,
        roughness=0.28,
    )
    materials["face_backing"] = set_principled(
        bpy.data.materials.new("MAT_FaceBacking"),
        (0.002, 0.006, 0.025, 1.0),
        metallic=0.0,
        roughness=0.72,
        alpha=0.78,
    )
    materials["star"] = make_emission_material(
        "MAT_Star", (0.6, 0.2, 1.0, 1.0), 3.0, (0.9, 0.95, 1.0, 1.0), 2.0
    )
    return materials


def build_background(scene, materials):
    collection = bpy.data.collections.new("BG")
    scene.collection.children.link(collection)

    mat = bpy.data.materials.new("MAT_Backdrop")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    principled = nodes.new("ShaderNodeBsdfPrincipled")
    texcoord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    noise = nodes.new("ShaderNodeTexNoise")
    ramp = nodes.new("ShaderNodeValToRGB")
    separate = nodes.new("ShaderNodeSeparateXYZ")
    vector_math = nodes.new("ShaderNodeVectorMath")
    radial_ramp = nodes.new("ShaderNodeValToRGB")
    mix = nodes.new("ShaderNodeMixRGB")

    mapping.inputs["Scale"].default_value = (1.2, 1.2, 1.2)
    noise.inputs["Scale"].default_value = 1.8
    noise.inputs["Detail"].default_value = 5.0
    ramp.color_ramp.elements[0].position = 0.20
    ramp.color_ramp.elements[0].color = (0.002, 0.002, 0.015, 1.0)
    ramp.color_ramp.elements[1].position = 0.82
    ramp.color_ramp.elements[1].color = (0.055, 0.006, 0.13, 1.0)
    radial_ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    radial_ramp.color_ramp.elements[1].color = (0.48, 0.18, 1.0, 1.0)
    vector_math.operation = "DISTANCE"
    vector_math.inputs[1].default_value = (0.5, 0.5, 0.5)
    mix.blend_type = "ADD"
    mix.inputs["Fac"].default_value = 0.32
    principled.inputs["Roughness"].default_value = 0.82

    links.new(texcoord.outputs["Generated"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(texcoord.outputs["Generated"], vector_math.inputs[0])
    links.new(vector_math.outputs["Value"], radial_ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], mix.inputs[1])
    links.new(radial_ramp.outputs["Color"], mix.inputs[2])
    links.new(mix.outputs["Color"], principled.inputs["Base Color"])
    links.new(principled.outputs["BSDF"], output.inputs["Surface"])

    backdrop = create_plane(
        "BG_SpacePlane",
        (0.0, 5.0, 0.0),
        (math.radians(90), 0.0, 0.0),
        (26.0, 18.0, 1.0),
        mat,
        collection,
    )
    backdrop.is_shadow_catcher = False

    for index in range(160):
        angle = random.uniform(0.0, math.tau)
        radius = random.uniform(1.0, 11.0)
        x = math.cos(angle) * radius * 1.75
        z = math.sin(angle) * radius
        y = random.uniform(2.8, 4.6)
        size = random.uniform(0.008, 0.035)
        material = materials["cyan"] if index % 5 == 0 else materials["star"]
        star = create_uv_sphere(
            f"BG_Star_{index:03d}",
            (x, y, z),
            size,
            material,
            collection,
            scale=(1.0, 0.45, 1.0),
        )
        star["is_background_star"] = True

    return collection, backdrop


def build_effect(scene, materials):
    effect = bpy.data.collections.new("SKILL_EFFECT")
    scene.collection.children.link(effect)

    controls = {}
    for name in (
        "CTRL_Stars",
        "CTRL_Vortex",
        "CTRL_Core",
        "CTRL_Face",
        "CTRL_Burst",
        "CTRL_Shards",
    ):
        controls[name] = create_empty(name, effect)

    stars = create_empty("CTRL_FarStars", effect)
    stars.parent = controls["CTRL_Stars"]
    for index in range(90):
        angle = random.uniform(0.0, math.tau)
        radius = random.uniform(4.2, 11.5)
        x = math.cos(angle) * radius
        z = math.sin(angle) * radius * 0.68
        y = random.uniform(-0.6, 1.8)
        star = create_uv_sphere(
            f"FX_Star_{index:03d}",
            (x, y, z),
            random.uniform(0.012, 0.055),
            materials["star"] if index % 4 else materials["cyan"],
            effect,
            scale=(1.0, 0.45, 1.0),
        )
        star.parent = stars

    vortex = create_empty("CTRL_MainVortex", effect)
    vortex.parent = controls["CTRL_Vortex"]
    arm_specs = [
        ("Arm_Cyan", -0.55, 1.08, 0.42, 8.7, 0.130, materials["cyan"], -0.34),
        ("Arm_Pink", 1.42, 0.88, 0.54, 9.1, 0.115, materials["pink"], -0.25),
        ("Arm_White", 0.45, 1.18, 0.30, 7.8, 0.092, materials["white"], -0.18),
        ("Arm_Indigo", -2.05, 0.86, 0.66, 10.0, 0.108, materials["indigo"], -0.12),
        ("Arm_Violet", 2.92, 0.72, 0.50, 8.4, 0.122, materials["violet"], 0.18),
    ]
    for index, spec in enumerate(arm_specs):
        name, phase, turns, rmin, rmax, depth, material, delay = spec
        arm_control = create_empty(f"CTRL_{name}", effect)
        arm_control.parent = vortex
        arm = create_spiral(
            name,
            phase,
            turns,
            rmin,
            rmax,
            depth,
            material,
            effect,
            depth=0.55,
            samples=96,
        )
        arm.parent = arm_control
        core_arm = create_spiral(
            name + "_Core",
            phase + 0.06,
            turns,
            rmin * 0.65,
            rmax * 0.72,
            0.036,
            materials["white"],
            effect,
            depth=0.30,
            samples=72,
        )
        core_arm.parent = arm_control
        animate_parented_start(arm_control, 7 + index * 6, 37 + index * 7)

    for index, spec in enumerate(arm_specs):
        name, phase, turns, rmin, rmax, depth, material, delay = spec
        ribbon_control = create_empty(f"CTRL_Ribbon_{index}", effect)
        ribbon_control.parent = vortex
        ribbon_mat = materials["ribbon_cyan"] if index % 2 == 0 else materials["ribbon_purple"]
        ribbon = create_spiral(
            f"Ribbon_{index}",
            phase - 0.28,
            turns * 0.76,
            rmin * 0.55,
            rmax * 1.12,
            0.18 + 0.025 * index,
            ribbon_mat,
            effect,
            depth=1.15,
            samples=72,
        )
        ribbon.parent = ribbon_control
        animate_parented_start(ribbon_control, 14 + index * 5, 50 + index * 6, 0.92)

    for index, spec in enumerate(arm_specs):
        name, phase, turns, rmin, rmax, depth, material, delay = spec
        haze_control = create_empty(f"CTRL_Haze_{index}", effect)
        haze_control.parent = vortex
        haze = create_spiral(
            f"Haze_{index}",
            phase + 0.34,
            turns * 0.84,
            rmin * 0.50,
            rmax * 1.02,
            0.28 + 0.035 * index,
            materials["smoke"],
            effect,
            depth=1.45,
            samples=64,
        )
        haze.parent = haze_control
        animate_parented_start(haze_control, 20 + index * 5, 58 + index * 7, 0.96)

    for index in range(84):
        angle = random.uniform(0.0, math.tau)
        radius = random.uniform(0.7, 8.8)
        x = math.cos(angle) * radius
        z = math.sin(angle) * radius * 0.68
        y = random.uniform(-0.5, 1.2)
        size = random.uniform(0.015, 0.075)
        particle = create_uv_sphere(
            f"Orbit_Dot_{index:03d}",
            (x, y, z),
            size,
            [materials["cyan"], materials["pink"], materials["white"]][index % 3],
            effect,
            scale=(1.0, 0.55, 1.0),
        )
        particle.parent = vortex

    streaks = create_empty("CTRL_Streaks", effect)
    streaks.parent = vortex
    for index in range(48):
        angle = random.uniform(0.0, math.tau)
        radius = random.uniform(0.65, 8.2)
        x = math.cos(angle) * radius
        z = math.sin(angle) * radius * 0.68
        y = random.uniform(-0.55, 1.1)
        tangent = angle + math.pi * 0.5
        length = random.uniform(0.18, 0.82)
        material = materials["cyan"] if index % 3 == 0 else materials["pink"]
        streak = create_box(
            f"Streak_{index:03d}",
            (x, y, z),
            (length, 0.012, random.uniform(0.008, 0.022)),
            (0.0, tangent, 0.0),
            material,
            effect,
        )
        streak.parent = streaks

    core = create_empty("CTRL_CoreAssembly", effect)
    core.parent = controls["CTRL_Core"]
    core_void = create_uv_sphere(
        "Core_Void",
        (0.0, -0.34, 0.0),
        1.0,
        materials["void"],
        effect,
        scale=(0.72, 0.23, 0.72),
    )
    core_void.parent = core
    core_void.scale = (0.72, 0.23, 0.72)
    core_void.keyframe_insert("scale", frame=80)
    core_void.scale = (0.26, 0.12, 0.26)
    core_void.keyframe_insert("scale", frame=101)
    core_void.scale = (0.075, 0.055, 0.075)
    core_void.keyframe_insert("scale", frame=115)
    core_void.scale = (0.060, 0.045, 0.060)
    core_void.keyframe_insert("scale", frame=160)
    for index, (major, minor, mat, scale) in enumerate(
        [
            (0.72, 0.07, materials["white"], 1.00),
            (0.99, 0.055, materials["cyan"], 1.04),
            (1.25, 0.045, materials["pink"], 1.08),
            (1.56, 0.032, materials["violet"], 1.12),
        ]
    ):
        ring = create_torus(
            f"Core_Ring_{index}",
            (0.0, -0.22 + index * 0.035, 0.0),
            major,
            minor,
            mat,
            effect,
        )
        ring.parent = core
        ring.scale = (scale, scale, scale)

    core_cross_h = create_poly_curve(
        "Core_Flare_Horizontal",
        [(-2.6, -0.16, 0.0), (0.0, -0.16, 0.0), (2.6, -0.16, 0.0)],
        materials["white"],
        effect,
        bevel_depth=0.022,
    )
    core_cross_h.parent = core
    core_cross_v = create_poly_curve(
        "Core_Flare_Vertical",
        [(0.0, -0.16, -1.8), (0.0, -0.16, 0.0), (0.0, -0.16, 1.8)],
        materials["cyan"],
        effect,
        bevel_depth=0.018,
    )
    core_cross_v.parent = core

    face = create_empty("CTRL_FaceAssembly", effect)
    face.parent = controls["CTRL_Face"]
    face.location = (0.0, -0.28, 0.10)

    face_backing = create_disc_mesh(
        "Face_Backing", 2.42, 1.58, materials["face_backing"], effect
    )
    face_backing.parent = face
    face_backing.location = (0.0, 0.21, 0.0)

    face_fill = create_disc_mesh(
        "Face_EnergyField", 2.55, 1.72, materials["ribbon_cyan"], effect
    )
    face_fill.parent = face
    face_fill.location = (0.0, 0.14, 0.0)

    muzzle = create_disc_mesh(
        "Face_MuzzleGlow", 1.32, 0.62, materials["ribbon_cyan"], effect
    )
    muzzle.parent = face
    muzzle.location = (0.0, 0.05, -0.62)

    core_glow = create_disc_mesh(
        "Face_CoreGlow", 0.62, 0.48, materials["white"], effect
    )
    core_glow.parent = face
    core_glow.location = (0.0, -0.02, -0.16)

    head_outline = create_ellipse_curve(
        "Face_Outline",
        (0.0, -0.06, 0.0),
        2.30,
        1.62,
        materials["pink"],
        effect,
        bevel_depth=0.105,
    )
    head_outline.parent = face

    head_inner = create_ellipse_curve(
        "Face_Inline",
        (0.0, -0.14, 0.0),
        2.08,
        1.44,
        materials["cyan"],
        effect,
        bevel_depth=0.035,
    )
    head_inner.parent = face

    ear_outer_left = create_ellipse_curve(
        "Face_Ear_Outer_L",
        (-1.53, -0.03, 1.25),
        0.76,
        0.83,
        materials["pink"],
        effect,
        bevel_depth=0.105,
    )
    ear_outer_left.parent = face
    ear_outer_right = create_ellipse_curve(
        "Face_Ear_Outer_R",
        (1.53, -0.03, 1.25),
        0.76,
        0.83,
        materials["pink"],
        effect,
        bevel_depth=0.105,
    )
    ear_outer_right.parent = face
    ear_inner_left = create_ellipse_curve(
        "Face_Ear_Inner_L",
        (-1.53, -0.15, 1.25),
        0.50,
        0.57,
        materials["cyan"],
        effect,
        bevel_depth=0.045,
    )
    ear_inner_left.parent = face
    ear_inner_right = create_ellipse_curve(
        "Face_Ear_Inner_R",
        (1.53, -0.15, 1.25),
        0.50,
        0.57,
        materials["cyan"],
        effect,
        bevel_depth=0.045,
    )
    ear_inner_right.parent = face

    left_eye = create_log_spiral(
        "Face_Eye_L",
        (-0.88, -0.26, 0.26),
        -1.0,
        materials["gold"],
        effect,
        turns=2.6,
        radius_max=0.55,
        bevel_depth=0.072,
    )
    left_eye.parent = face
    right_eye = create_log_spiral(
        "Face_Eye_R",
        (0.88, -0.26, 0.26),
        1.0,
        materials["gold"],
        effect,
        turns=2.6,
        radius_max=0.55,
        bevel_depth=0.072,
    )
    right_eye.parent = face

    left_eye_halo = create_log_spiral(
        "Face_Eye_Halo_L",
        (-0.88, -0.22, 0.26),
        -1.0,
        materials["cyan"],
        effect,
        turns=2.55,
        radius_max=0.66,
        bevel_depth=0.035,
    )
    left_eye_halo.parent = face
    right_eye_halo = create_log_spiral(
        "Face_Eye_Halo_R",
        (0.88, -0.22, 0.26),
        1.0,
        materials["cyan"],
        effect,
        turns=2.55,
        radius_max=0.66,
        bevel_depth=0.035,
    )
    right_eye_halo.parent = face

    mouth_loop = create_poly_curve(
        "Face_Mouth_Loop",
        [
            (-0.38, -0.30, -0.36),
            (-0.42, -0.30, -1.05),
            (0.0, -0.30, -1.48),
            (0.42, -0.30, -1.05),
            (0.38, -0.30, -0.36),
        ],
        materials["cyan"],
        effect,
        bevel_depth=0.075,
    )
    mouth_loop.parent = face
    mouth_mid = create_poly_curve(
        "Face_Mouth_Center",
        [(0.0, -0.34, -0.22), (0.0, -0.34, -0.70)],
        materials["white"],
        effect,
        bevel_depth=0.055,
    )
    mouth_mid.parent = face
    smile_left = create_poly_curve(
        "Face_Smile_L",
        [
            (0.0, -0.34, -0.62),
            (-0.44, -0.34, -0.98),
            (-0.95, -0.34, -0.76),
        ],
        materials["pink"],
        effect,
        bevel_depth=0.045,
    )
    smile_left.parent = face
    smile_right = create_poly_curve(
        "Face_Smile_R",
        [
            (0.0, -0.34, -0.62),
            (0.44, -0.34, -0.98),
            (0.95, -0.34, -0.76),
        ],
        materials["pink"],
        effect,
        bevel_depth=0.045,
    )
    smile_right.parent = face

    for index, (x, z, radius) in enumerate(
        [(-1.93, 0.72, 0.18), (1.93, 0.72, 0.18), (-2.12, 0.18, 0.12), (2.12, 0.18, 0.12)]
    ):
        spark = create_uv_sphere(
            f"Face_Spark_{index}",
            (x, -0.26, z),
            radius,
            materials["white"] if index % 2 == 0 else materials["pink"],
            effect,
        )
        spark.parent = face

    burst = create_empty("CTRL_BurstAssembly", effect)
    burst.parent = controls["CTRL_Burst"]
    for index, (major, minor, mat) in enumerate(
        [
            (2.8, 0.045, materials["cyan"]),
            (4.0, 0.030, materials["pink"]),
            (5.6, 0.022, materials["violet"]),
            (7.2, 0.018, materials["indigo"]),
        ]
    ):
        ring = create_torus(
            f"Shockwave_{index}",
            (0.0, 0.25 + index * 0.08, -0.10),
            major,
            minor,
            mat,
            effect,
        )
        ring.parent = burst
        ring["shockwave_index"] = index

    for index in range(26):
        angle = 0.5 + index * 0.37
        radius = 3.2 + (index % 6) * 0.72
        x = math.cos(angle) * radius
        z = math.sin(angle) * radius * 0.58
        shard = create_box(
            f"Burst_Shard_{index:02d}",
            (x, 0.25 + (index % 3) * 0.18, z),
            (
                random.uniform(0.15, 0.65),
                random.uniform(0.05, 0.22),
                random.uniform(0.08, 0.30),
            ),
            (random.uniform(-0.5, 0.5), angle, random.uniform(-0.5, 0.5)),
            materials["shard"],
            effect,
        )
        shard.parent = controls["CTRL_Shards"]

    controls["CTRL_Stars"].rotation_euler[1] = -0.10
    controls["CTRL_Vortex"].rotation_euler[1] = -0.16
    controls["CTRL_Face"].rotation_euler[1] = 0.025
    controls["CTRL_Burst"].rotation_euler[1] = 0.08

    animate_group(controls["CTRL_Stars"], 1, 18, spin=0.18)
    animate_group(controls["CTRL_Vortex"], 5, 48, spin=0.50, pulse=0.025)
    animate_group(controls["CTRL_Core"], 24, 62, spin=0.28, pulse=0.04)
    animate_group(controls["CTRL_Face"], 52, 94, spin=0.08, pulse=0.035)
    animate_group(controls["CTRL_Burst"], 92, 119, spin=0.18, pulse=0.06)
    animate_group(controls["CTRL_Shards"], 94, 122, spin=0.75)

    controls["CTRL_Face"].scale = (0.82, 0.82, 0.82)
    controls["CTRL_Face"].keyframe_insert("scale", frame=102)
    controls["CTRL_Face"].scale = (1.12, 1.12, 1.12)
    controls["CTRL_Face"].keyframe_insert("scale", frame=119)
    controls["CTRL_Face"].scale = (0.98, 0.98, 0.98)
    controls["CTRL_Face"].keyframe_insert("scale", frame=130)
    controls["CTRL_Face"].scale = (1.055, 1.055, 1.055)
    controls["CTRL_Face"].keyframe_insert("scale", frame=143)
    controls["CTRL_Face"].scale = (1.0, 1.0, 1.0)
    controls["CTRL_Face"].keyframe_insert("scale", frame=160)

    for index, ring in enumerate(
        obj for obj in effect.objects if obj.name.startswith("Shockwave_")
    ):
        start = 92 + index * 7
        ring.scale = (0.08, 0.08, 0.08)
        ring.keyframe_insert("scale", frame=start)
        ring.scale = (1.4 + index * 0.3, 1.4 + index * 0.3, 1.4 + index * 0.3)
        ring.keyframe_insert("scale", frame=122 + index * 8)
        ring.scale = (2.2 + index * 0.4, 2.2 + index * 0.4, 2.2 + index * 0.4)
        ring.keyframe_insert("scale", frame=160)

    for obj in effect.objects:
        if obj.name.startswith("Face_") or obj.name in {
        "Face_EnergyField",
            "Face_MuzzleGlow",
            "Face_Outline",
            "Face_Inline",
        }:
            if obj.parent == face:
                obj.rotation_euler[1] = math.radians(random.uniform(-4.0, 4.0))

    return effect


def build_camera(scene, effect):
    camera_data = bpy.data.cameras.new("Skill_Camera")
    camera = bpy.data.objects.new("Skill_Camera", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera.data.lens = 55.0
    camera.data.sensor_width = 36.0
    camera.data.dof.use_dof = True
    camera.data.dof.focus_distance = 12.0
    camera.data.dof.aperture_fstop = 4.0
    camera.location = (0.0, -14.8, 3.2)
    camera.rotation_euler = (math.radians(82.0), 0.0, 0.0)
    target = create_empty("CAM_Target", effect, (0.0, 0.0, 0.25))
    constraint = camera.constraints.new("TRACK_TO")
    constraint.target = target
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"

    camera_positions = [
        (1, (0.0, -14.8, 3.2), (0.0, 0.0, 0.62), 54.0),
        (38, (-0.9, -13.7, 2.4), (0.0, 0.0, 0.45), 51.0),
        (78, (0.8, -11.9, -0.25), (0.0, 0.0, 0.08), 48.0),
        (118, (0.0, -13.2, 0.45), (0.0, 0.0, 0.18), 50.0),
        (160, (0.0, -14.1, 0.78), (0.0, 0.0, 0.26), 52.0),
    ]
    for frame, location, target_location, lens in camera_positions:
        camera.location = location
        target.location = target_location
        camera.data.lens = lens
        camera.keyframe_insert("location", frame=frame)
        camera.data.keyframe_insert("lens", frame=frame)
        target.keyframe_insert("location", frame=frame)

    return camera, target


def build_lights(scene):
    lights = []
    light_specs = [
        ("Light_Cyan", (0.0, 1.0, 1.0), 280.0, (-4.5, -3.0, 4.5), 4.0),
        ("Light_Magenta", (1.0, 0.05, 0.85), 320.0, (4.8, -2.5, 2.0), 4.5),
        ("Light_Violet", (0.20, 0.03, 0.85), 220.0, (0.0, -4.0, -4.5), 5.0),
    ]
    for name, color, energy, location, size in light_specs:
        data = bpy.data.lights.new(name, "AREA")
        data.energy = energy
        data.color = color
        data.shape = "DISK"
        data.size = size
        obj = bpy.data.objects.new(name, data)
        obj.location = location
        scene.collection.objects.link(obj)
        lights.append(obj)
    return lights


def build_compositor(scene):
    scene.use_nodes = True
    node_tree = scene.node_tree
    nodes = node_tree.nodes
    links = node_tree.links
    nodes.clear()
    render_layers = nodes.new("CompositorNodeRLayers")
    glare = nodes.new("CompositorNodeGlare")
    glare.glare_type = "FOG_GLOW"
    glare.quality = "HIGH"
    glare.threshold = 0.75
    glare.size = 7
    glare.mix = -0.12
    lens = nodes.new("CompositorNodeLensdist")
    lens.inputs["Distortion"].default_value = 0.012
    lens.inputs["Dispersion"].default_value = 0.018
    color = nodes.new("CompositorNodeColorBalance")
    color.correction_method = "LIFT_GAMMA_GAIN"
    color.gamma = (0.98, 0.96, 1.05)
    composite = nodes.new("CompositorNodeComposite")
    links.new(render_layers.outputs["Image"], glare.inputs["Image"])
    links.new(glare.outputs["Image"], lens.inputs["Image"])
    links.new(lens.outputs["Image"], color.inputs["Image"])
    links.new(color.outputs["Image"], composite.inputs["Image"])


def configure_scene(scene):
    scene.name = "SkillEffect_V1"
    scene.frame_start = 1
    scene.frame_end = 160
    scene.render.fps = 30
    scene.render.resolution_x = 720
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    scene.render.filepath = os.path.join(PREVIEW_DIR, "skill_effect_v1_")
    scene.render.use_file_extension = True
    scene.render.use_overwrite = True
    try:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    except Exception:
        scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.color_depth = "8"
    scene.view_settings.view_transform = "AgX"
    try:
        scene.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        pass
    scene.view_settings.exposure = -0.35
    scene.view_settings.gamma = 1.0
    world = bpy.data.worlds.new("Skill_World") if not scene.world else scene.world
    scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    if background:
        background.inputs["Color"].default_value = (0.0005, 0.0008, 0.008, 1.0)
        background.inputs["Strength"].default_value = 0.08


def write_manifest(scene, effect):
    manifest = {
        "scene": scene.name,
        "frames": [scene.frame_start, scene.frame_end],
        "fps": scene.render.fps,
        "resolution": [scene.render.resolution_x, scene.render.resolution_y],
        "engine": scene.render.engine,
        "collections": [collection.name for collection in scene.collection.children],
        "effect_objects": len(effect.objects),
        "animation_phases": {
            "awaken": [1, 30],
            "vortex": [25, 70],
            "sigil_form": [62, 104],
            "burst": [92, 138],
            "settle": [138, 160],
        },
        "main_objects": [
            "CTRL_CoreAssembly",
            "CTRL_MainVortex",
            "CTRL_FaceAssembly",
            "CTRL_BurstAssembly",
            "CTRL_Shards",
        ],
    }
    with open(os.path.join(OUTPUT_DIR, "SKILL_EFFECT_V1_MANIFEST.json"), "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)


def main():
    ensure_dirs()
    clear_scene()
    scene = bpy.context.scene
    configure_scene(scene)
    materials = build_materials()
    build_background(scene, materials)
    effect = build_effect(scene, materials)
    build_camera(scene, effect)
    build_lights(scene)
    build_compositor(scene)
    scene.frame_set(1)
    write_manifest(scene, effect)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print("BUILD_OK")
    print(BLEND_PATH)
    print("EFFECT_OBJECTS", len(effect.objects))


main()
