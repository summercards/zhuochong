import math
import os

import bpy
from mathutils import Vector


ROOT = os.path.abspath(os.path.dirname(__file__))
BLEND_PATH = os.path.join(ROOT, "business_man_tpose_v3.blend")
GLB_PATH = os.path.join(ROOT, "business_man_tpose_v3.glb")
FRONT_PATH = os.path.join(ROOT, "business_man_tpose_v3_front.png")
SIDE_PATH = os.path.join(ROOT, "business_man_tpose_v3_side.png")
BACK_PATH = os.path.join(ROOT, "business_man_tpose_v3_back.png")


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (
        bpy.data.meshes,
        bpy.data.curves,
        bpy.data.armatures,
        bpy.data.cameras,
        bpy.data.lights,
        bpy.data.materials,
    ):
        for datablock in list(datablocks):
            if datablock.users == 0:
                datablocks.remove(datablock)


def make_collection(name):
    collection = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(collection)
    return collection


def move_to_collection(obj, collection):
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    collection.objects.link(obj)
    return obj


def assign_material(obj, material):
    if obj.data and hasattr(obj.data, "materials"):
        obj.data.materials.append(material)
    return obj


def set_smooth(obj, smooth=True, bevel=None):
    if obj.type == "MESH":
        for polygon in obj.data.polygons:
            polygon.use_smooth = smooth
    if bevel is not None:
        modifier = obj.modifiers.new("Soft tailored edges", "BEVEL")
        modifier.width = bevel
        modifier.segments = 3
        modifier.limit_method = "ANGLE"
    return obj


def create_material(
    name,
    color,
    roughness=0.45,
    metallic=0.0,
    fabric=False,
    sheen=0.0,
    coat=0.0,
    transmission=0.0,
):
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*color, 1.0)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (420, 0)
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    shader.location = (120, 0)
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic
    if "Sheen Weight" in shader.inputs:
        shader.inputs["Sheen Weight"].default_value = sheen
    if "Coat Weight" in shader.inputs:
        shader.inputs["Coat Weight"].default_value = coat
    if "Coat Roughness" in shader.inputs:
        shader.inputs["Coat Roughness"].default_value = max(0.04, roughness * 0.45)
    if "Transmission Weight" in shader.inputs:
        shader.inputs["Transmission Weight"].default_value = transmission

    material.node_tree.links.new(shader.outputs["BSDF"], output.inputs["Surface"])

    if fabric:
        texture = nodes.new("ShaderNodeTexNoise")
        texture.inputs["Scale"].default_value = 155.0
        texture.inputs["Detail"].default_value = 3.0
        texture.inputs["Roughness"].default_value = 0.72
        texture.location = (-620, -110)
        bump = nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.135
        bump.inputs["Distance"].default_value = 0.0017
        bump.location = (-160, -110)
        material.node_tree.links.new(texture.outputs["Fac"], bump.inputs["Height"])
        material.node_tree.links.new(bump.outputs["Normal"], shader.inputs["Normal"])

    return material


def mesh_object(name, vertices, faces, material, collection):
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    assign_material(obj, material)
    return set_smooth(obj)


def ellipsoid(name, location, scale, material, collection, segments=40, rings=24):
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=segments,
        ring_count=rings,
        location=location,
    )
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign_material(obj, material)
    move_to_collection(obj, collection)
    return set_smooth(obj)


def rounded_box(
    name,
    location,
    scale,
    material,
    collection,
    bevel=0.01,
    rotation=(0.0, 0.0, 0.0),
):
    bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign_material(obj, material)
    move_to_collection(obj, collection)
    return set_smooth(obj, smooth=False, bevel=bevel)


def loft_z(
    name,
    sections,
    material,
    collection,
    radial_segments=28,
    start_angle=0.0,
    end_angle=360.0,
    closed=True,
    caps=True,
):
    count = radial_segments if closed else radial_segments + 1
    vertices = []
    faces = []

    for section in sections:
        z = section["z"]
        for index in range(count):
            t = index / (radial_segments if closed else radial_segments)
            angle = math.radians(start_angle + (end_angle - start_angle) * t)
            sine = math.sin(angle)
            cosine = math.cos(angle)
            depth = section.get("front", section["rx"]) if sine < 0 else section.get("back", section["rx"])
            vertices.append(
                (
                    section.get("x", 0.0) + section["rx"] * cosine,
                    section.get("y", 0.0) + depth * sine,
                    z,
                )
            )

    ring_count = len(sections)
    span = count if closed else count - 1
    for ring in range(ring_count - 1):
        for index in range(span):
            next_index = (index + 1) % count
            a = ring * count + index
            b = ring * count + next_index
            c = (ring + 1) * count + next_index
            d = (ring + 1) * count + index
            faces.append((a, b, c, d))

    if caps and closed:
        bottom_center = len(vertices)
        bottom = sections[0]
        vertices.append((bottom.get("x", 0.0), bottom.get("y", 0.0), bottom["z"]))
        top_center = len(vertices)
        top = sections[-1]
        vertices.append((top.get("x", 0.0), top.get("y", 0.0), top["z"]))
        for index in range(count):
            next_index = (index + 1) % count
            faces.append((bottom_center, next_index, index))
            faces.append((top_center, (ring_count - 1) * count + index, (ring_count - 1) * count + next_index))

    return mesh_object(name, vertices, faces, material, collection)


def loft_x(
    name,
    sections,
    material,
    collection,
    radial_segments=24,
    caps=True,
):
    vertices = []
    faces = []
    for section in sections:
        for index in range(radial_segments):
            angle = math.tau * index / radial_segments
            vertices.append(
                (
                    section["x"],
                    section.get("y", 0.0) + section["ry"] * math.cos(angle),
                    section.get("z", 0.0) + section["rz"] * math.sin(angle),
                )
            )

    for ring in range(len(sections) - 1):
        for index in range(radial_segments):
            next_index = (index + 1) % radial_segments
            a = ring * radial_segments + index
            b = ring * radial_segments + next_index
            c = (ring + 1) * radial_segments + next_index
            d = (ring + 1) * radial_segments + index
            faces.append((a, b, c, d))

    if caps:
        first_center = len(vertices)
        first = sections[0]
        vertices.append((first["x"], first.get("y", 0.0), first.get("z", 0.0)))
        last_center = len(vertices)
        last = sections[-1]
        vertices.append((last["x"], last.get("y", 0.0), last.get("z", 0.0)))
        for index in range(radial_segments):
            next_index = (index + 1) % radial_segments
            faces.append((first_center, next_index, index))
            faces.append(
                (
                    last_center,
                    (len(sections) - 1) * radial_segments + index,
                    (len(sections) - 1) * radial_segments + next_index,
                )
            )

    return mesh_object(name, vertices, faces, material, collection)


def tapered_capsule_x(
    name,
    x_start,
    x_end,
    y,
    z,
    radius_start,
    radius_end,
    material,
    collection,
    radial_segments=16,
):
    sections = []
    steps = 6
    for index in range(steps + 1):
        t = index / steps
        sections.append(
            {
                "x": x_start + (x_end - x_start) * t,
                "y": y,
                "z": z,
                "ry": radius_start + (radius_end - radius_start) * t,
                "rz": radius_start + (radius_end - radius_start) * t,
            }
        )
    return loft_x(name, sections, material, collection, radial_segments=radial_segments)


def tapered_capsule_profile_x(
    name,
    x_start,
    x_end,
    y,
    z,
    ry_start,
    ry_end,
    rz_start,
    rz_end,
    material,
    collection,
    radial_segments=16,
):
    sections = []
    steps = 6
    for index in range(steps + 1):
        t = index / steps
        sections.append(
            {
                "x": x_start + (x_end - x_start) * t,
                "y": y,
                "z": z,
                "ry": ry_start + (ry_end - ry_start) * t,
                "rz": rz_start + (rz_end - rz_start) * t,
            }
        )
    return loft_x(name, sections, material, collection, radial_segments=radial_segments)


def prism_patch(name, points, y, depth, material, collection):
    vertices = []
    for point in points:
        vertices.append((point[0], y - depth * 0.5, point[1]))
    for point in points:
        vertices.append((point[0], y + depth * 0.5, point[1]))

    count = len(points)
    faces = []
    faces.append(tuple(range(count - 1, -1, -1)))
    faces.append(tuple(range(count, count * 2)))
    for index in range(count):
        next_index = (index + 1) % count
        faces.append((index, next_index, count + next_index, count + index))
    return mesh_object(name, vertices, faces, material, collection)


def shoe_mesh(name, center_x, material, collection):
    sections = [
        (-0.275, 0.032, 0.010, 0.043),
        (-0.245, 0.058, 0.010, 0.058),
        (-0.150, 0.066, 0.010, 0.081),
        (-0.040, 0.061, 0.010, 0.113),
        (0.058, 0.054, 0.010, 0.104),
        (0.112, 0.046, 0.010, 0.063),
    ]
    vertices = []
    for y, half_width, bottom, top in sections:
        vertices.extend(
            [
                (center_x - half_width, y, bottom),
                (center_x + half_width, y, bottom),
                (center_x + half_width * 0.90, y, bottom + (top - bottom) * 0.46),
                (center_x + half_width * 0.70, y, top),
                (center_x - half_width * 0.70, y, top),
                (center_x - half_width * 0.90, y, bottom + (top - bottom) * 0.46),
            ]
        )

    faces = []
    ring_size = 6
    for ring in range(len(sections) - 1):
        for index in range(ring_size):
            next_index = (index + 1) % ring_size
            a = ring * ring_size + index
            b = ring * ring_size + next_index
            c = (ring + 1) * ring_size + next_index
            d = (ring + 1) * ring_size + index
            faces.append((a, b, c, d))
    faces.append(tuple(range(ring_size - 1, -1, -1)))
    last = (len(sections) - 1) * ring_size
    faces.append(tuple(last + index for index in range(ring_size)))
    return mesh_object(name, vertices, faces, material, collection)


def curve_line(name, points, bevel_depth, material, collection, resolution=2):
    curve = bpy.data.curves.new(name + "_Curve", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = resolution
    curve.bevel_depth = bevel_depth
    curve.bevel_resolution = 3
    curve.resolution_u = 5
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for bezier_point, coordinate in zip(spline.bezier_points, points):
        bezier_point.co = coordinate
        bezier_point.handle_left_type = "AUTO"
        bezier_point.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve)
    collection.objects.link(obj)
    assign_material(obj, material)
    return obj


def rounded_rect_curve(name, center_x, center_z, width, height, y, material, collection):
    hx = width * 0.5
    hz = height * 0.5
    radius = min(width, height) * 0.18
    points = [
        (center_x - hx + radius, y, center_z + hz),
        (center_x + hx - radius, y, center_z + hz),
        (center_x + hx, y, center_z + hz - radius),
        (center_x + hx, y, center_z - hz + radius),
        (center_x + hx - radius, y, center_z - hz),
        (center_x - hx + radius, y, center_z - hz),
        (center_x - hx, y, center_z - hz + radius),
        (center_x - hx, y, center_z + hz - radius),
        (center_x - hx + radius, y, center_z + hz),
    ]
    return curve_line(name, points, 0.0035, material, collection)


def build_materials():
    return {
        "suit": create_material("Suit Cobalt Wool", (0.018, 0.055, 0.42), 0.52, fabric=True, sheen=0.12),
        "suit_dark": create_material("Suit Seams", (0.005, 0.014, 0.105), 0.58, fabric=True, sheen=0.07),
        "suit_light": create_material("Suit Highlights", (0.025, 0.082, 0.53), 0.50, fabric=True, sheen=0.12),
        "shirt": create_material("Crisp White Shirt", (0.70, 0.77, 0.86), 0.62, fabric=True, sheen=0.05),
        "skin": create_material("Warm Skin", (0.39, 0.19, 0.12), 0.58),
        "skin_light": create_material("Skin Highlights", (0.48, 0.24, 0.15), 0.56),
        "skin_dark": create_material("Skin Creases", (0.12, 0.035, 0.022), 0.64),
        "hair": create_material("Near Black Hair", (0.0025, 0.003, 0.0045), 0.42, sheen=0.025),
        "shoe": create_material("Polished Black Leather", (0.0025, 0.003, 0.0045), 0.26, metallic=0.04, coat=0.32),
        "shoe_edge": create_material("Shoe Edge", (0.008, 0.009, 0.012), 0.38),
        "frame": create_material("Glasses Frame", (0.002, 0.002, 0.0025), 0.30, metallic=0.42),
        "lens": create_material("Glasses Lens", (0.035, 0.065, 0.085), 0.20, metallic=0.08, transmission=0.10),
        "eye_white": create_material("Eye White", (0.70, 0.73, 0.76), 0.38),
        "iris": create_material("Dark Brown Iris", (0.045, 0.018, 0.010), 0.40),
        "pupil": create_material("Pupil", (0.0007, 0.0007, 0.0007), 0.34),
        "lip": create_material("Muted Lips", (0.20, 0.065, 0.052), 0.62),
        "button": create_material("Dark Suit Buttons", (0.004, 0.006, 0.012), 0.34, metallic=0.18, coat=0.08),
        "ground": create_material("Studio Ground", (0.14, 0.155, 0.18), 0.86),
    }


def build_body(materials, character):
    # Neck and torso base form.
    loft_z(
        "Neck",
        [
            {"z": 1.445, "rx": 0.059, "front": 0.056, "back": 0.060},
            {"z": 1.500, "rx": 0.055, "front": 0.052, "back": 0.057},
            {"z": 1.585, "rx": 0.050, "front": 0.049, "back": 0.052},
        ],
        materials["skin"],
        character,
    )
    loft_z(
        "Shirt_Body",
        [
            {"z": 0.86, "rx": 0.205, "front": 0.124, "back": 0.116},
            {"z": 1.02, "rx": 0.214, "front": 0.130, "back": 0.121},
            {"z": 1.22, "rx": 0.228, "front": 0.140, "back": 0.130},
            {"z": 1.38, "rx": 0.256, "front": 0.150, "back": 0.138},
            {"z": 1.48, "rx": 0.266, "front": 0.143, "back": 0.135},
        ],
        materials["shirt"],
        character,
    )

    # Tapered trouser legs with a small central crease and a fly overlap.
    for side, sign in (("L", 1), ("R", -1)):
        loft_z(
            "Trouser_Leg_" + side,
            [
                {"x": sign * 0.096, "z": 0.145, "rx": 0.066, "front": 0.061, "back": 0.057},
                {"x": sign * 0.098, "z": 0.285, "rx": 0.073, "front": 0.068, "back": 0.064},
                {"x": sign * 0.102, "z": 0.505, "rx": 0.082, "front": 0.074, "back": 0.070},
                {"x": sign * 0.108, "z": 0.71, "rx": 0.098, "front": 0.083, "back": 0.079},
                {"x": sign * 0.112, "z": 0.91, "rx": 0.119, "front": 0.094, "back": 0.092},
            ],
            materials["suit"],
            character,
        )
        curve_line(
            "Trouser_Crease_" + side,
            [
                (sign * 0.115, -0.078, 0.18),
                (sign * 0.102, -0.080, 0.50),
                (sign * 0.108, -0.098, 0.90),
            ],
            0.0017,
            materials["suit_light"],
            character,
        )

    loft_z(
        "Trouser_Waist",
        [
            {"z": 0.86, "rx": 0.218, "front": 0.126, "back": 0.122},
            {"z": 0.95, "rx": 0.228, "front": 0.132, "back": 0.126},
            {"z": 1.01, "rx": 0.215, "front": 0.128, "back": 0.123},
        ],
        materials["suit"],
        character,
    )
    prism_patch(
        "Trouser_Fly",
        [(-0.012, 0.96), (0.055, 0.93), (0.050, 0.84), (-0.010, 0.87)],
        -0.132,
        0.004,
        materials["suit_dark"],
        character,
    )


def build_jacket(materials, character):
    jacket_sections = [
        {"z": 0.84, "rx": 0.220, "front": 0.132, "back": 0.128},
        {"z": 0.94, "rx": 0.227, "front": 0.137, "back": 0.133},
        {"z": 1.08, "rx": 0.224, "front": 0.139, "back": 0.134},
        {"z": 1.23, "rx": 0.237, "front": 0.145, "back": 0.140},
        {"z": 1.37, "rx": 0.261, "front": 0.153, "back": 0.148},
        {"z": 1.47, "rx": 0.284, "front": 0.151, "back": 0.147},
    ]
    loft_z(
        "Jacket_Shell",
        jacket_sections,
        materials["suit"],
        character,
        radial_segments=40,
    )

    # The visible shirt opening and lapels sit on top of a closed tailored shell.
    prism_patch(
        "Shirt_V",
        [
            (-0.061, 1.455),
            (0.061, 1.455),
            (0.048, 1.382),
            (0.018, 1.315),
            (0.000, 1.295),
            (-0.018, 1.315),
            (-0.048, 1.382),
        ],
        -0.151,
        0.006,
        materials["shirt"],
        character,
    )

    # Broad, low-notch lapels define the character's suit silhouette.
    for side, sign in (("L", 1), ("R", -1)):
        prism_patch(
            "Jacket_Lapel_" + side,
            [
                (sign * 0.010, 1.462),
                (sign * 0.088, 1.432),
                (sign * 0.119, 1.350),
                (sign * 0.082, 1.315),
                (sign * 0.022, 1.255),
                (sign * 0.010, 1.295),
            ],
            -0.157,
            0.010,
            materials["suit_light"],
            character,
        )
        prism_patch(
            "Jacket_Pocket_" + side,
            [
                (sign * 0.095, 1.082),
                (sign * 0.199, 1.082),
                (sign * 0.204, 1.057),
                (sign * 0.098, 1.057),
            ],
            -0.143,
            0.009,
            materials["suit_dark"],
            character,
        )
        prism_patch(
            "Jacket_Pocket_Flap_" + side,
            [
                (sign * 0.094, 1.097),
                (sign * 0.201, 1.097),
                (sign * 0.204, 1.076),
                (sign * 0.097, 1.076),
            ],
            -0.148,
            0.011,
            materials["suit"],
            character,
        )
        prism_patch(
            "Jacket_Side_Vent_" + side,
            [
                (sign * 0.204, 0.875),
                (sign * 0.218, 0.955),
                (sign * 0.215, 0.990),
                (sign * 0.201, 0.955),
            ],
            -0.090,
            0.004,
            materials["suit_dark"],
            character,
        )

    # The jacket closes below the V, so buttons sit on the front center.
    for index, z in enumerate((1.135, 1.020)):
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=24,
            radius=0.010,
            depth=0.006,
            location=(0.0, -0.143, z),
            rotation=(math.radians(90), 0.0, 0.0),
        )
        obj = bpy.context.object
        obj.name = "Jacket_Button_%02d" % (index + 1)
        assign_material(obj, materials["button"])
        move_to_collection(obj, character)
        set_smooth(obj, bevel=0.0015)

    # Sleeve button details on each cuff.
    for side, sign in (("L", 1), ("R", -1)):
        for index, x in enumerate((0.700, 0.718, 0.736)):
            bpy.ops.mesh.primitive_cylinder_add(
                vertices=16,
                radius=0.0065,
                depth=0.005,
                location=(sign * x, -0.058, 1.457),
                rotation=(0.0, math.radians(90), 0.0),
            )
            obj = bpy.context.object
            obj.name = "Cuff_Button_%s_%02d" % (side, index + 1)
            assign_material(obj, materials["button"])
            move_to_collection(obj, character)
            set_smooth(obj, bevel=0.001)

    # Shirt collar leaves and a restrained center seam.
    for side, sign in (("L", 1), ("R", -1)):
        prism_patch(
            "Shirt_Collar_" + side,
            [
                (sign * 0.002, 1.515),
                (sign * 0.046, 1.480),
                (sign * 0.036, 1.412),
                (sign * 0.008, 1.450),
            ],
            -0.148,
            0.007,
            materials["shirt"],
            character,
        )
    curve_line(
        "Shirt_Center_Seam",
        [(0.0, -0.145, 1.36), (0.0, -0.153, 1.15), (0.0, -0.136, 0.89)],
        0.0010,
        materials["suit_dark"],
        character,
    )
    curve_line(
        "Jacket_Back_Seam",
        [(0.0, 0.130, 0.86), (0.0, 0.143, 1.18), (0.0, 0.149, 1.47)],
        0.0014,
        materials["suit_dark"],
        character,
    )
    curve_line(
        "Jacket_Hem",
        [(-0.216, -0.018, 0.842), (0.0, -0.122, 0.842), (0.216, -0.018, 0.842)],
        0.0050,
        materials["suit_dark"],
        character,
    )


def build_arms_and_hands(materials, character):
    for side, sign in (("L", 1), ("R", -1)):
        loft_x(
            "Sleeve_" + side,
            [
                {"x": sign * 0.235, "y": 0.0, "z": 1.451, "ry": 0.102, "rz": 0.105},
                {"x": sign * 0.305, "y": -0.002, "z": 1.450, "ry": 0.111, "rz": 0.106},
                {"x": sign * 0.465, "y": -0.003, "z": 1.448, "ry": 0.096, "rz": 0.094},
                {"x": sign * 0.605, "y": -0.003, "z": 1.447, "ry": 0.083, "rz": 0.082},
                {"x": sign * 0.710, "y": -0.002, "z": 1.446, "ry": 0.073, "rz": 0.074},
                {"x": sign * 0.750, "y": 0.0, "z": 1.446, "ry": 0.070, "rz": 0.071},
            ],
            materials["suit"],
            character,
            radial_segments=28,
        )
        loft_x(
            "Shirt_Cuff_" + side,
            [
                {"x": sign * 0.748, "y": -0.002, "z": 1.446, "ry": 0.070, "rz": 0.072},
                {"x": sign * 0.782, "y": -0.002, "z": 1.446, "ry": 0.067, "rz": 0.068},
                {"x": sign * 0.797, "y": -0.002, "z": 1.445, "ry": 0.064, "rz": 0.065},
            ],
            materials["shirt"],
            character,
            radial_segments=24,
        )

        loft_x(
            "Palm_" + side,
            [
                {"x": sign * 0.792, "y": -0.002, "z": 1.446, "ry": 0.043, "rz": 0.025},
                {"x": sign * 0.818, "y": -0.004, "z": 1.445, "ry": 0.055, "rz": 0.027},
                {"x": sign * 0.850, "y": -0.004, "z": 1.444, "ry": 0.058, "rz": 0.024},
                {"x": sign * 0.878, "y": -0.003, "z": 1.443, "ry": 0.052, "rz": 0.020},
            ],
            materials["skin_light"],
            character,
            radial_segments=24,
        )
        finger_offsets = (-0.034, -0.011, 0.012, 0.035)
        finger_lengths = (0.076, 0.090, 0.083, 0.066)
        finger_radii = (0.0105, 0.0115, 0.0105, 0.0090)
        for index, (offset_y, length) in enumerate(zip(finger_offsets, finger_lengths)):
            base = sign * 0.873
            tip = sign * (0.873 + length)
            finger_radius = finger_radii[index]
            tapered_capsule_profile_x(
                "Finger_%s_%d" % (side, index + 1),
                base,
                tip,
                -0.003 + offset_y,
                1.444 - (0.0012 * index),
                finger_radius,
                finger_radius * 0.82,
                0.0125,
                0.0100,
                materials["skin_light"],
                character,
                radial_segments=16,
            )
        curve_line(
            "Thumb_" + side,
            [
                (sign * 0.806, -0.043, 1.441),
                (sign * 0.825, -0.066, 1.435),
                (sign * 0.846, -0.083, 1.429),
            ],
            0.0125,
            materials["skin_light"],
            character,
        )
        ellipsoid(
            "Thumb_Tip_" + side,
            (sign * 0.849, -0.086, 1.428),
            (0.011, 0.012, 0.010),
            materials["skin_light"],
            character,
            20,
            12,
        )

        # Fine knuckle breaks keep the hand readable without changing the rest pose.
        for index, y in enumerate(finger_offsets):
            curve_line(
                "Knuckle_%s_%d" % (side, index + 1),
                [
                    (sign * 0.879, y - 0.009, 1.454),
                    (sign * 0.879, y + 0.009, 1.454),
                ],
                0.0010,
                materials["skin_dark"],
                character,
            )


def build_head(materials, character):
    loft_z(
        "Head",
        [
            {"z": 1.610, "rx": 0.041, "front": 0.049, "back": 0.055},
            {"z": 1.645, "rx": 0.059, "front": 0.064, "back": 0.070},
            {"z": 1.690, "rx": 0.071, "front": 0.071, "back": 0.081},
            {"z": 1.745, "rx": 0.078, "front": 0.072, "back": 0.085},
            {"z": 1.790, "rx": 0.072, "front": 0.064, "back": 0.079},
            {"z": 1.820, "rx": 0.055, "front": 0.050, "back": 0.063},
        ],
        materials["skin"],
        character,
        radial_segments=40,
    )
    ellipsoid("Jaw", (0.0, -0.006, 1.647), (0.060, 0.064, 0.051), materials["skin"], character, 36, 22)
    ellipsoid("Chin", (0.0, -0.047, 1.638), (0.037, 0.024, 0.026), materials["skin"], character, 28, 18)
    ellipsoid("Ear_L", (0.078, 0.004, 1.717), (0.014, 0.020, 0.030), materials["skin"], character, 24, 16)
    ellipsoid("Ear_R", (-0.078, 0.004, 1.717), (0.014, 0.020, 0.030), materials["skin"], character, 24, 16)

    for side, sign in (("L", 1), ("R", -1)):
        ellipsoid(
            "Eye_White_" + side,
            (sign * 0.029, -0.0730, 1.741),
            (0.017, 0.005, 0.0080),
            materials["eye_white"],
            character,
            24,
            16,
        )
        ellipsoid(
            "Iris_" + side,
            (sign * 0.029, -0.0774, 1.741),
            (0.0062, 0.0019, 0.0062),
            materials["iris"],
            character,
            24,
            16,
        )
        ellipsoid(
            "Pupil_" + side,
            (sign * 0.029, -0.0785, 1.741),
            (0.0024, 0.0010, 0.0024),
            materials["pupil"],
            character,
            20,
            12,
        )
        rounded_box(
            "Eyebrow_" + side,
            (sign * 0.030, -0.074, 1.763),
            (0.023, 0.0037, 0.0034),
            materials["hair"],
            character,
            bevel=0.0025,
            rotation=(0.0, sign * math.radians(-7), sign * math.radians(4)),
        )

    nose_vertices = [
        (-0.007, -0.073, 1.741),
        (0.007, -0.073, 1.741),
        (-0.012, -0.087, 1.704),
        (0.012, -0.087, 1.704),
        (-0.010, -0.088, 1.693),
        (0.010, -0.088, 1.693),
        (0.0, -0.098, 1.695),
    ]
    nose_faces = [
        (0, 1, 3, 2),
        (2, 3, 6),
        (0, 2, 4),
        (1, 5, 3),
        (4, 6, 5),
        (4, 5, 3, 2),
    ]
    mesh_object("Nose", nose_vertices, nose_faces, materials["skin_light"], character)
    ellipsoid("Upper_Lip", (0.0, -0.088, 1.670), (0.022, 0.0040, 0.0045), materials["lip"], character, 24, 14)
    ellipsoid("Lower_Lip", (0.0, -0.087, 1.663), (0.020, 0.0042, 0.0050), materials["lip"], character, 24, 14)
    curve_line(
        "Mouth_Line",
        [(-0.021, -0.091, 1.666), (0.0, -0.094, 1.664), (0.021, -0.091, 1.666)],
        0.0009,
        materials["skin_dark"],
        character,
    )
    for sign in (-1, 1):
        curve_line(
            "Face_Line_%s" % ("L" if sign > 0 else "R"),
            [
                (sign * 0.042, -0.066, 1.713),
                (sign * 0.047, -0.074, 1.677),
                (sign * 0.037, -0.078, 1.648),
            ],
            0.00085,
            materials["skin_dark"],
            character,
        )

    ellipsoid("Hair_Cap", (0.0, 0.009, 1.807), (0.090, 0.083, 0.062), materials["hair"], character, 44, 28)
    rounded_box(
        "Hair_Back",
        (0.0, 0.058, 1.774),
        (0.076, 0.027, 0.050),
        materials["hair"],
        character,
        bevel=0.013,
    )
    lock_data = [
        (-0.067, -0.052, 1.805, 0.021, 0.014, 0.037, -0.16),
        (-0.045, -0.058, 1.812, 0.022, 0.015, 0.040, -0.10),
        (-0.021, -0.061, 1.816, 0.021, 0.015, 0.042, -0.05),
        (0.003, -0.062, 1.818, 0.021, 0.015, 0.043, 0.02),
        (0.027, -0.061, 1.816, 0.021, 0.015, 0.042, 0.07),
        (0.050, -0.057, 1.812, 0.022, 0.015, 0.040, 0.12),
        (0.070, -0.050, 1.805, 0.020, 0.014, 0.037, 0.18),
    ]
    for index, (x, y, z, sx, sy, sz, tilt) in enumerate(lock_data):
        rounded_box(
            "Hair_Lock_%02d" % (index + 1),
            (x, y, z),
            (sx, sy, sz),
            materials["hair"],
            character,
            bevel=0.007,
            rotation=(math.radians(6.0), math.radians(tilt * 42.0), math.radians(tilt * 12.0)),
        )
    for index, (x, y, z, sx, sy, sz, tilt) in enumerate(
        [
            (-0.064, -0.024, 1.811, 0.025, 0.018, 0.048, -0.25),
            (-0.034, -0.020, 1.825, 0.026, 0.018, 0.053, -0.13),
            (0.000, -0.018, 1.831, 0.027, 0.018, 0.055, 0.00),
            (0.034, -0.020, 1.825, 0.026, 0.018, 0.053, 0.13),
            (0.064, -0.024, 1.811, 0.025, 0.018, 0.048, 0.25),
        ]
    ):
        rounded_box(
            "Hair_Top_%02d" % (index + 1),
            (x, y, z),
            (sx, sy, sz),
            materials["hair"],
            character,
            bevel=0.008,
            rotation=(math.radians(3.0), math.radians(tilt * 35.0), 0.0),
        )
    for side, sign in (("L", 1), ("R", -1)):
        rounded_box(
            "Sideburn_" + side,
            (sign * 0.073, -0.020, 1.746),
            (0.009, 0.012, 0.026),
            materials["hair"],
            character,
            bevel=0.005,
        )


def build_glasses(materials, character):
    for side, sign in (("L", 1), ("R", -1)):
        rounded_rect_curve(
            "Glasses_Frame_" + side,
            sign * 0.031,
            1.741,
            0.055,
            0.035,
            -0.084,
            materials["frame"],
            character,
        )
        rounded_box(
            "Glasses_Lens_" + side,
            (sign * 0.031, -0.082, 1.741),
            (0.022, 0.0018, 0.0125),
            materials["lens"],
            character,
            bevel=0.004,
        )
    curve_line(
        "Glasses_Bridge",
        [(-0.006, -0.086, 1.744), (0.0, -0.089, 1.748), (0.006, -0.086, 1.744)],
        0.0021,
        materials["frame"],
        character,
    )
    curve_line(
        "Glasses_Temple_L",
        [(0.058, -0.084, 1.744), (0.076, -0.045, 1.744), (0.078, 0.019, 1.744)],
        0.0019,
        materials["frame"],
        character,
    )
    curve_line(
        "Glasses_Temple_R",
        [(-0.058, -0.084, 1.744), (-0.076, -0.045, 1.744), (-0.078, 0.019, 1.744)],
        0.0019,
        materials["frame"],
        character,
    )


def build_shoes(materials, character):
    for side, sign in (("L", 1), ("R", -1)):
        shoe = shoe_mesh("Shoe_" + side, sign * 0.100, materials["shoe"], character)
        set_smooth(shoe, bevel=0.006)
        rounded_box(
            "Shoe_Sole_" + side,
            (sign * 0.100, -0.078, 0.016),
            (0.069, 0.200, 0.012),
            materials["shoe_edge"],
            character,
            bevel=0.010,
        )
        rounded_box(
            "Shoe_Heel_" + side,
            (sign * 0.100, 0.094, 0.030),
            (0.056, 0.032, 0.029),
            materials["shoe_edge"],
            character,
            bevel=0.006,
        )
        curve_line(
            "Shoe_Lace_%s_A" % side,
            [
                (sign * 0.068, -0.100, 0.087),
                (sign * 0.100, -0.092, 0.098),
                (sign * 0.132, -0.100, 0.087),
            ],
            0.0016,
            materials["shoe_edge"],
            character,
        )
        curve_line(
            "Shoe_Lace_%s_B" % side,
            [
                (sign * 0.070, -0.058, 0.108),
                (sign * 0.100, -0.050, 0.120),
                (sign * 0.130, -0.058, 0.108),
            ],
            0.0016,
            materials["shoe_edge"],
            character,
        )
        rounded_box(
            "Shoe_Tongue_" + side,
            (sign * 0.100, -0.050, 0.111),
            (0.039, 0.040, 0.009),
            materials["shoe"],
            character,
            bevel=0.005,
            rotation=(math.radians(-14.0), 0.0, 0.0),
        )
        for index, y in enumerate((-0.075, -0.038)):
            for x_offset in (-0.032, 0.032):
                ellipsoid(
                    "Shoe_Eyelet_%s_%d_%s" % (side, index + 1, "A" if x_offset < 0 else "B"),
                    (sign * (0.100 + x_offset), y, 0.116 - index * 0.008),
                    (0.0038, 0.0038, 0.0022),
                    materials["shoe_edge"],
                    character,
                    14,
                    10,
                )


def convert_curves(collection):
    curves = [obj for obj in list(collection.objects) if obj.type == "CURVE"]
    for obj in curves:
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.convert(target="MESH")
        set_smooth(obj)


def build_armature(character):
    bpy.ops.object.armature_add(enter_editmode=True, location=(0.0, 0.0, 0.0))
    armature = bpy.context.object
    armature.name = "Character_Rig"
    armature.data.name = "Character_Rig"
    armature.data.display_type = "OCTAHEDRAL"
    for bone in list(armature.data.edit_bones):
        armature.data.edit_bones.remove(bone)

    def bone(name, head, tail, parent=None, connected=False):
        edit_bone = armature.data.edit_bones.new(name)
        edit_bone.head = head
        edit_bone.tail = tail
        if parent:
            edit_bone.parent = armature.data.edit_bones[parent]
            edit_bone.use_connect = connected
        return edit_bone

    bone("root", (0.0, 0.0, 0.0), (0.0, 0.0, 0.08))
    bone("pelvis", (0.0, 0.0, 0.84), (0.0, 0.0, 1.00), "root")
    bone("spine", (0.0, 0.0, 1.00), (0.0, 0.0, 1.24), "pelvis", True)
    bone("chest", (0.0, 0.0, 1.24), (0.0, 0.0, 1.46), "spine", True)
    bone("neck", (0.0, 0.0, 1.46), (0.0, 0.0, 1.59), "chest", True)
    bone("head", (0.0, 0.0, 1.59), (0.0, 0.0, 1.84), "neck", True)

    for side, sign in (("L", 1), ("R", -1)):
        bone("clavicle." + side, (sign * 0.055, 0.0, 1.455), (sign * 0.235, 0.0, 1.451), "chest")
        bone("upper_arm." + side, (sign * 0.235, 0.0, 1.451), (sign * 0.530, 0.0, 1.448), "clavicle." + side, True)
        bone("forearm." + side, (sign * 0.530, 0.0, 1.448), (sign * 0.760, 0.0, 1.446), "upper_arm." + side, True)
        bone("hand." + side, (sign * 0.760, 0.0, 1.446), (sign * 0.955, -0.005, 1.438), "forearm." + side, True)
        bone("thigh." + side, (sign * 0.112, 0.0, 0.91), (sign * 0.102, 0.0, 0.505), "pelvis")
        bone("shin." + side, (sign * 0.102, 0.0, 0.505), (sign * 0.096, 0.0, 0.145), "thigh." + side, True)
        bone("foot." + side, (sign * 0.096, 0.0, 0.145), (sign * 0.100, -0.20, 0.055), "shin." + side, True)

    bpy.ops.object.mode_set(mode="OBJECT")
    armature.show_in_front = True
    armature.data.pose_position = "POSE"
    armature["asset_type"] = "character"
    armature["pose"] = "T-pose"
    armature["height_m"] = 1.86
    armature["forward_axis"] = "-Y"
    armature["up_axis"] = "+Z"
    move_to_collection(armature, character)
    return armature


def point_segment_distance(point, start, end):
    direction = end - start
    length_squared = direction.length_squared
    if length_squared == 0.0:
        return (point - start).length
    t = max(0.0, min(1.0, (point - start).dot(direction) / length_squared))
    closest = start + direction * t
    return (point - closest).length


def bind_meshes_to_armature(character, armature):
    weight_bones = [
        "pelvis",
        "spine",
        "chest",
        "neck",
        "head",
        "clavicle.L",
        "upper_arm.L",
        "forearm.L",
        "hand.L",
        "clavicle.R",
        "upper_arm.R",
        "forearm.R",
        "hand.R",
        "thigh.L",
        "shin.L",
        "foot.L",
        "thigh.R",
        "shin.R",
        "foot.R",
    ]
    bones = []
    for name in weight_bones:
        bone = armature.data.bones[name]
        bones.append((name, bone.head_local.copy(), bone.tail_local.copy()))

    for obj in list(character.objects):
        if obj.type != "MESH":
            continue
        groups = {}
        for name, _, _ in bones:
            groups[name] = obj.vertex_groups.new(name=name)

        world_matrix = obj.matrix_world
        for vertex in obj.data.vertices:
            point = world_matrix @ vertex.co
            distances = []
            for name, head, tail in bones:
                distance = point_segment_distance(point, head, tail)
                if name.startswith(("thigh.", "shin.", "foot.")) and abs(point.x) < 0.035:
                    distance += 0.12
                if name.startswith(("upper_arm.", "forearm.", "hand.", "clavicle.")) and "L" in name and point.x < -0.03:
                    distance += 0.18
                if name.startswith(("upper_arm.", "forearm.", "hand.", "clavicle.")) and "R" in name and point.x > 0.03:
                    distance += 0.18
                if name in {"pelvis", "spine", "chest"} and abs(point.x) > 0.38 and point.z > 1.30:
                    distance += 0.12
                distances.append((distance, name))
            distances.sort(key=lambda item: item[0])
            closest = distances[:2]
            if closest[0][0] < 0.0001 or closest[1][0] > closest[0][0] * 1.9:
                groups[closest[0][1]].add([vertex.index], 1.0, "REPLACE")
            else:
                raw = [(1.0 / max(distance, 0.0002) ** 4.0, name) for distance, name in closest]
                total = sum(weight for weight, _ in raw)
                for weight, name in raw:
                    groups[name].add([vertex.index], weight / total, "REPLACE")

        modifier = obj.modifiers.new("Character skin", "ARMATURE")
        modifier.object = armature
        modifier.use_deform_preserve_volume = True
        obj.parent = armature
        obj.matrix_parent_inverse = armature.matrix_world.inverted()


def build_presentation(materials, presentation):
    bpy.ops.mesh.primitive_plane_add(size=8.0, location=(0.0, 0.0, -0.001))
    floor = bpy.context.object
    floor.name = "Presentation_Ground"
    assign_material(floor, materials["ground"])
    move_to_collection(floor, presentation)

    def track(obj, target):
        obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()

    bpy.ops.object.camera_add(location=(0.0, -5.0, 1.02))
    camera = bpy.context.object
    camera.name = "Presentation_Camera"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 2.20
    camera.data.sensor_width = 36.0
    track(camera, (0.0, 0.0, 0.96))
    bpy.context.scene.camera = camera
    move_to_collection(camera, presentation)

    light_settings = [
        ("Key_Light", "AREA", (3.0, -4.0, 4.8), 620.0, 2.6, (1.0, 0.91, 0.80)),
        ("Fill_Light", "AREA", (-3.0, -2.2, 2.8), 310.0, 3.0, (0.72, 0.84, 1.0)),
        ("Rim_Light", "AREA", (1.5, 3.4, 3.7), 430.0, 2.0, (0.68, 0.80, 1.0)),
        ("Top_Softbox", "AREA", (0.0, -0.5, 4.0), 220.0, 3.2, (0.92, 0.95, 1.0)),
    ]
    for light_name, light_type, location, energy, size, color in light_settings:
        bpy.ops.object.light_add(type=light_type, location=location)
        light = bpy.context.object
        light.name = light_name
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        light.data.color = color
        track(light, (0.0, 0.0, 1.0))
        move_to_collection(light, presentation)


def configure_scene():
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 1000
    scene.render.resolution_y = 1050
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.105, 0.125, 0.165, 1.0)
    background.inputs["Strength"].default_value = 0.72


def render_view(camera, output_path, location, target, ortho_scale=2.20):
    camera.location = location
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = ortho_scale
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)


def export_character(character, armature):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in character.objects:
        if obj.type in {"MESH", "ARMATURE"}:
            obj.select_set(True)
    bpy.context.view_layer.objects.active = armature
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


def main():
    clear_scene()
    character = make_collection("CHARACTER")
    presentation = make_collection("PRESENTATION")
    materials = build_materials()

    build_body(materials, character)
    build_jacket(materials, character)
    build_arms_and_hands(materials, character)
    build_head(materials, character)
    build_glasses(materials, character)
    build_shoes(materials, character)
    convert_curves(character)

    armature = build_armature(character)
    bind_meshes_to_armature(character, armature)
    build_presentation(materials, presentation)
    configure_scene()

    camera = bpy.data.objects["Presentation_Camera"]
    render_view(camera, FRONT_PATH, (0.0, -5.0, 0.97), (0.0, 0.0, 0.97), 2.24)
    render_view(camera, SIDE_PATH, (5.0, 0.0, 0.97), (0.0, 0.0, 0.97), 2.12)
    render_view(camera, BACK_PATH, (0.0, 5.0, 0.97), (0.0, 0.0, 0.97), 2.24)

    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    export_character(character, armature)
    print("CHARACTER_V2_COMPLETE", BLEND_PATH, GLB_PATH)


if __name__ == "__main__":
    main()
