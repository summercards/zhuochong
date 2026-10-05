import math
import os

import bpy
from mathutils import Vector


ROOT = os.path.abspath(os.path.dirname(__file__))
BLEND_PATH = os.path.join(ROOT, "business_man_tpose_v2.blend")
GLB_PATH = os.path.join(ROOT, "business_man_tpose_v2.glb")
FRONT_PATH = os.path.join(ROOT, "business_man_tpose_v2_front.png")
SIDE_PATH = os.path.join(ROOT, "business_man_tpose_v2_side.png")
BACK_PATH = os.path.join(ROOT, "business_man_tpose_v2_back.png")


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
        (-0.238, 0.036, 0.008, 0.050),
        (-0.205, 0.071, 0.008, 0.067),
        (-0.095, 0.077, 0.008, 0.098),
        (-0.008, 0.070, 0.008, 0.144),
        (0.075, 0.061, 0.008, 0.128),
        (0.112, 0.052, 0.008, 0.070),
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
        "suit": create_material("Suit Cobalt Wool", (0.018, 0.065, 0.50), 0.34, fabric=True, sheen=0.18),
        "suit_dark": create_material("Suit Seams", (0.006, 0.020, 0.160), 0.38, fabric=True, sheen=0.10),
        "suit_light": create_material("Suit Highlights", (0.025, 0.10, 0.62), 0.32, fabric=True, sheen=0.18),
        "shirt": create_material("Crisp White Shirt", (0.72, 0.80, 0.91), 0.52, fabric=True, sheen=0.08),
        "skin": create_material("Warm Skin", (0.44, 0.20, 0.12), 0.45),
        "skin_light": create_material("Skin Highlights", (0.58, 0.28, 0.17), 0.43),
        "skin_dark": create_material("Skin Creases", (0.18, 0.055, 0.035), 0.52),
        "hair": create_material("Near Black Hair", (0.004, 0.005, 0.008), 0.26, sheen=0.05),
        "shoe": create_material("Polished Black Leather", (0.003, 0.004, 0.006), 0.15, metallic=0.08, coat=0.65),
        "shoe_edge": create_material("Shoe Edge", (0.012, 0.014, 0.018), 0.24),
        "frame": create_material("Glasses Frame", (0.004, 0.004, 0.005), 0.18, metallic=0.65),
        "lens": create_material("Glasses Lens", (0.055, 0.11, 0.16), 0.12, metallic=0.15, transmission=0.15),
        "eye_white": create_material("Eye White", (0.76, 0.79, 0.82), 0.28),
        "iris": create_material("Dark Brown Iris", (0.060, 0.025, 0.014), 0.30),
        "pupil": create_material("Pupil", (0.001, 0.001, 0.001), 0.24),
        "lip": create_material("Muted Lips", (0.28, 0.095, 0.075), 0.50),
        "button": create_material("Dark Suit Buttons", (0.006, 0.010, 0.020), 0.22, metallic=0.25, coat=0.15),
        "ground": create_material("Studio Ground", (0.035, 0.045, 0.065), 0.78),
    }


def build_body(materials, character):
    # Neck and torso base form.
    loft_z(
        "Neck",
        [
            {"z": 1.45, "rx": 0.071, "front": 0.065, "back": 0.064},
            {"z": 1.50, "rx": 0.068, "front": 0.064, "back": 0.063},
            {"z": 1.59, "rx": 0.061, "front": 0.060, "back": 0.060},
        ],
        materials["skin"],
        character,
    )
    loft_z(
        "Shirt_Body",
        [
            {"z": 0.88, "rx": 0.245, "front": 0.145, "back": 0.125},
            {"z": 1.02, "rx": 0.255, "front": 0.150, "back": 0.132},
            {"z": 1.23, "rx": 0.275, "front": 0.163, "back": 0.142},
            {"z": 1.42, "rx": 0.325, "front": 0.178, "back": 0.153},
            {"z": 1.49, "rx": 0.340, "front": 0.173, "back": 0.150},
        ],
        materials["shirt"],
        character,
    )

    # Tapered trouser legs with a small central crease and a fly overlap.
    for side, sign in (("L", 1), ("R", -1)):
        loft_z(
            "Trouser_Leg_" + side,
            [
                {"x": sign * 0.115, "z": 0.155, "rx": 0.082, "front": 0.076, "back": 0.071},
                {"x": sign * 0.115, "z": 0.30, "rx": 0.091, "front": 0.081, "back": 0.078},
                {"x": sign * 0.115, "z": 0.51, "rx": 0.101, "front": 0.090, "back": 0.087},
                {"x": sign * 0.120, "z": 0.72, "rx": 0.124, "front": 0.105, "back": 0.102},
                {"x": sign * 0.120, "z": 0.92, "rx": 0.139, "front": 0.113, "back": 0.110},
            ],
            materials["suit"],
            character,
        )
        curve_line(
            "Trouser_Crease_" + side,
            [
                (sign * 0.115, -0.078, 0.18),
                (sign * 0.115, -0.094, 0.50),
                (sign * 0.120, -0.109, 0.90),
            ],
            0.0021,
            materials["suit_light"],
            character,
        )

    loft_z(
        "Trouser_Waist",
        [
            {"z": 0.87, "rx": 0.250, "front": 0.135, "back": 0.130},
            {"z": 0.95, "rx": 0.266, "front": 0.145, "back": 0.137},
            {"z": 1.03, "rx": 0.250, "front": 0.140, "back": 0.135},
        ],
        materials["suit"],
        character,
    )
    prism_patch(
        "Trouser_Fly",
        [(-0.012, 0.96), (0.055, 0.93), (0.050, 0.84), (-0.010, 0.87)],
        -0.144,
        0.004,
        materials["suit_dark"],
        character,
    )


def build_jacket(materials, character):
    jacket_sections = [
        {"z": 0.88, "rx": 0.275, "front": 0.152, "back": 0.138},
        {"z": 0.98, "rx": 0.285, "front": 0.158, "back": 0.145},
        {"z": 1.14, "rx": 0.292, "front": 0.164, "back": 0.151},
        {"z": 1.31, "rx": 0.335, "front": 0.178, "back": 0.160},
        {"z": 1.44, "rx": 0.405, "front": 0.184, "back": 0.166},
        {"z": 1.49, "rx": 0.410, "front": 0.176, "back": 0.160},
    ]
    jacket = loft_z(
        "Jacket_Shell",
        jacket_sections,
        materials["suit"],
        character,
        radial_segments=34,
        start_angle=292.0,
        end_angle=608.0,
        closed=False,
        caps=False,
    )
    solidify = jacket.modifiers.new("Jacket thickness", "SOLIDIFY")
    solidify.thickness = 0.009
    solidify.offset = 0.0
    set_smooth(jacket, bevel=0.003)

    # Lapels are broad and bent slightly outward like the source art.
    for side, sign in (("L", 1), ("R", -1)):
        prism_patch(
            "Jacket_Lapel_" + side,
            [
                (sign * 0.025, 1.455),
                (sign * 0.146, 1.410),
                (sign * 0.117, 1.245),
                (sign * 0.032, 1.125),
                (sign * 0.010, 1.205),
            ],
            -0.174,
            0.012,
            materials["suit_light"],
            character,
        )
        prism_patch(
            "Jacket_Pocket_" + side,
            [
                (sign * 0.115, 1.205),
                (sign * 0.245, 1.205),
                (sign * 0.255, 1.176),
                (sign * 0.118, 1.176),
            ],
            -0.157,
            0.009,
            materials["suit_dark"],
            character,
        )

    # The jacket closes below the V, so buttons sit on the front center.
    for index, z in enumerate((1.225, 1.112)):
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=24,
            radius=0.014,
            depth=0.009,
            location=(0.0, -0.173, z),
            rotation=(math.radians(90), 0.0, 0.0),
        )
        obj = bpy.context.object
        obj.name = "Jacket_Button_%02d" % (index + 1)
        assign_material(obj, materials["button"])
        move_to_collection(obj, character)
        set_smooth(obj, bevel=0.0015)

    # Sleeve button details on each cuff.
    for side, sign in (("L", 1), ("R", -1)):
        for index, x in enumerate((0.930, 0.947, 0.964)):
            bpy.ops.mesh.primitive_cylinder_add(
                vertices=16,
                radius=0.009,
                depth=0.007,
                location=(sign * x, -0.074, 1.455),
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
                (sign * 0.004, 1.485),
                (sign * 0.072, 1.440),
                (sign * 0.045, 1.390),
                (sign * 0.012, 1.424),
            ],
            -0.184,
            0.008,
            materials["shirt"],
            character,
        )
    curve_line(
        "Shirt_Center_Seam",
        [(0.0, -0.164, 1.38), (0.0, -0.178, 1.15), (0.0, -0.150, 0.92)],
        0.0012,
        materials["suit_dark"],
        character,
    )
    curve_line(
        "Jacket_Back_Seam",
        [(0.0, 0.154, 0.93), (0.0, 0.166, 1.20), (0.0, 0.164, 1.46)],
        0.0017,
        materials["suit_dark"],
        character,
    )


def build_arms_and_hands(materials, character):
    for side, sign in (("L", 1), ("R", -1)):
        ellipsoid(
            "Shoulder_" + side,
            (sign * 0.382, 0.0, 1.442),
            (0.115, 0.108, 0.108),
            materials["suit"],
            character,
        )
        loft_x(
            "Sleeve_" + side,
            [
                {"x": sign * 0.365, "y": 0.0, "z": 1.442, "ry": 0.111, "rz": 0.112},
                {"x": sign * 0.585, "y": -0.003, "z": 1.440, "ry": 0.101, "rz": 0.103},
                {"x": sign * 0.755, "y": -0.003, "z": 1.438, "ry": 0.087, "rz": 0.090},
                {"x": sign * 0.900, "y": -0.002, "z": 1.438, "ry": 0.071, "rz": 0.074},
                {"x": sign * 0.948, "y": -0.001, "z": 1.438, "ry": 0.068, "rz": 0.070},
            ],
            materials["suit"],
            character,
        )
        loft_x(
            "Shirt_Cuff_" + side,
            [
                {"x": sign * 0.944, "ry": 0.070, "rz": 0.073},
                {"x": sign * 0.997, "ry": 0.068, "rz": 0.070},
                {"x": sign * 1.012, "ry": 0.066, "rz": 0.068},
            ],
            materials["shirt"],
            character,
        )

        palm_center = sign * 1.078
        rounded_box(
            "Palm_" + side,
            (palm_center, -0.004, 1.438),
            (0.074, 0.071, 0.044),
            materials["skin_light"],
            character,
            bevel=0.024,
        )
        finger_offsets = (-0.048, -0.016, 0.016, 0.047)
        finger_lengths = (0.118, 0.135, 0.128, 0.105)
        for index, (offset_y, length) in enumerate(zip(finger_offsets, finger_lengths)):
            base = sign * 1.142
            tip = sign * (1.142 + length)
            tapered_capsule_x(
                "Finger_%s_%d" % (side, index + 1),
                base,
                tip,
                -0.004 + offset_y,
                1.438 - (0.001 * index),
                0.0145,
                0.0115,
                materials["skin_light"],
                character,
                radial_segments=14,
            )
        tapered_capsule_x(
            "Thumb_" + side,
            sign * 1.042,
            sign * 1.125,
            -0.072,
            1.431,
            0.019,
            0.014,
            materials["skin_light"],
            character,
            radial_segments=14,
        )


def build_head(materials, character):
    ellipsoid("Head", (0.0, 0.0, 1.710), (0.112, 0.086, 0.141), materials["skin"], character, 48, 30)
    ellipsoid("Jaw", (0.0, -0.021, 1.630), (0.094, 0.077, 0.066), materials["skin"], character, 40, 24)
    ellipsoid("Ear_L", (0.108, 0.0, 1.700), (0.020, 0.026, 0.043), materials["skin"], character, 24, 16)
    ellipsoid("Ear_R", (-0.108, 0.0, 1.700), (0.020, 0.026, 0.043), materials["skin"], character, 24, 16)

    for side, sign in (("L", 1), ("R", -1)):
        ellipsoid(
            "Eye_White_" + side,
            (sign * 0.038, -0.078, 1.738),
            (0.022, 0.007, 0.012),
            materials["eye_white"],
            character,
            24,
            16,
        )
        ellipsoid(
            "Iris_" + side,
            (sign * 0.038, -0.0851, 1.738),
            (0.0085, 0.0027, 0.0085),
            materials["iris"],
            character,
            24,
            16,
        )
        ellipsoid(
            "Pupil_" + side,
            (sign * 0.038, -0.0873, 1.738),
            (0.0032, 0.0015, 0.0032),
            materials["pupil"],
            character,
            20,
            12,
        )
        rounded_box(
            "Eyebrow_" + side,
            (sign * 0.040, -0.083, 1.769),
            (0.032, 0.006, 0.0055),
            materials["hair"],
            character,
            bevel=0.004,
            rotation=(0.0, sign * math.radians(-10), sign * math.radians(5)),
        )

    nose_vertices = [
        (-0.010, -0.078, 1.751),
        (0.010, -0.078, 1.751),
        (-0.018, -0.103, 1.704),
        (0.018, -0.103, 1.704),
        (-0.014, -0.100, 1.684),
        (0.014, -0.100, 1.684),
        (0.0, -0.116, 1.686),
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
    ellipsoid("Upper_Lip", (0.0, -0.097, 1.651), (0.031, 0.006, 0.006), materials["lip"], character, 24, 14)
    ellipsoid("Lower_Lip", (0.0, -0.096, 1.641), (0.028, 0.006, 0.007), materials["lip"], character, 24, 14)
    curve_line(
        "Mouth_Line",
        [(-0.028, -0.101, 1.646), (0.0, -0.104, 1.644), (0.028, -0.101, 1.646)],
        0.00125,
        materials["skin_dark"],
        character,
    )
    for sign in (-1, 1):
        curve_line(
            "Face_Line_%s" % ("L" if sign > 0 else "R"),
            [
                (sign * 0.051, -0.081, 1.695),
                (sign * 0.057, -0.090, 1.654),
                (sign * 0.045, -0.094, 1.630),
            ],
            0.00115,
            materials["skin_dark"],
            character,
        )

    ellipsoid("Hair_Cap", (0.0, 0.010, 1.811), (0.123, 0.095, 0.077), materials["hair"], character, 48, 28)
    ellipsoid("Hair_Front", (0.0, -0.066, 1.801), (0.103, 0.026, 0.046), materials["hair"], character, 40, 24)
    bang_data = [
        (-0.085, -0.074, 1.827, -0.100, -0.089, 1.758, 0.013),
        (-0.058, -0.080, 1.842, -0.068, -0.094, 1.747, 0.015),
        (-0.030, -0.084, 1.848, -0.034, -0.097, 1.758, 0.014),
        (0.000, -0.086, 1.851, -0.001, -0.099, 1.741, 0.016),
        (0.030, -0.084, 1.848, 0.033, -0.097, 1.756, 0.015),
        (0.060, -0.080, 1.841, 0.067, -0.093, 1.746, 0.014),
        (0.086, -0.073, 1.826, 0.099, -0.087, 1.757, 0.013),
    ]
    for index, values in enumerate(bang_data):
        curve_line(
            "Hair_Bang_%02d" % (index + 1),
            [
                (values[0], values[1], values[2]),
                ((values[0] + values[3]) * 0.5, values[4] - 0.010, values[2] * 0.50 + values[5] * 0.50 + 0.008),
                (values[3], values[4], values[5]),
            ],
            values[6],
            materials["hair"],
            character,
        )
    for side, sign in (("L", 1), ("R", -1)):
        rounded_box(
            "Sideburn_" + side,
            (sign * 0.096, -0.028, 1.757),
            (0.012, 0.016, 0.034),
            materials["hair"],
            character,
            bevel=0.007,
        )


def build_glasses(materials, character):
    for side, sign in (("L", 1), ("R", -1)):
        rounded_rect_curve(
            "Glasses_Frame_" + side,
            sign * 0.042,
            1.738,
            0.079,
            0.050,
            -0.103,
            materials["frame"],
            character,
        )
        rounded_box(
            "Glasses_Lens_" + side,
            (sign * 0.042, -0.100, 1.738),
            (0.031, 0.0025, 0.018),
            materials["lens"],
            character,
            bevel=0.008,
        )
    curve_line(
        "Glasses_Bridge",
        [(-0.013, -0.105, 1.742), (0.0, -0.109, 1.747), (0.013, -0.105, 1.742)],
        0.0032,
        materials["frame"],
        character,
    )
    curve_line(
        "Glasses_Temple_L",
        [(0.079, -0.103, 1.742), (0.112, -0.050, 1.744), (0.113, 0.025, 1.744)],
        0.0030,
        materials["frame"],
        character,
    )
    curve_line(
        "Glasses_Temple_R",
        [(-0.079, -0.103, 1.742), (-0.112, -0.050, 1.744), (-0.113, 0.025, 1.744)],
        0.0030,
        materials["frame"],
        character,
    )


def build_shoes(materials, character):
    for side, sign in (("L", 1), ("R", -1)):
        shoe = shoe_mesh("Shoe_" + side, sign * 0.115, materials["shoe"], character)
        set_smooth(shoe, bevel=0.006)
        rounded_box(
            "Shoe_Sole_" + side,
            (sign * 0.115, -0.058, 0.018),
            (0.078, 0.180, 0.015),
            materials["shoe_edge"],
            character,
            bevel=0.012,
        )
        rounded_box(
            "Shoe_Heel_" + side,
            (sign * 0.115, 0.094, 0.036),
            (0.064, 0.036, 0.035),
            materials["shoe_edge"],
            character,
            bevel=0.008,
        )
        curve_line(
            "Shoe_Lace_%s_A" % side,
            [
                (sign * 0.075, -0.080, 0.102),
                (sign * 0.115, -0.070, 0.114),
                (sign * 0.154, -0.080, 0.102),
            ],
            0.0021,
            materials["shoe_edge"],
            character,
        )
        curve_line(
            "Shoe_Lace_%s_B" % side,
            [
                (sign * 0.078, -0.040, 0.120),
                (sign * 0.115, -0.030, 0.132),
                (sign * 0.152, -0.040, 0.120),
            ],
            0.0021,
            materials["shoe_edge"],
            character,
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
    bone("pelvis", (0.0, 0.0, 0.84), (0.0, 0.0, 1.02), "root")
    bone("spine", (0.0, 0.0, 1.02), (0.0, 0.0, 1.30), "pelvis", True)
    bone("chest", (0.0, 0.0, 1.30), (0.0, 0.0, 1.49), "spine", True)
    bone("neck", (0.0, 0.0, 1.49), (0.0, 0.0, 1.59), "chest", True)
    bone("head", (0.0, 0.0, 1.59), (0.0, 0.0, 1.84), "neck", True)

    for side, sign in (("L", 1), ("R", -1)):
        bone("clavicle." + side, (sign * 0.07, 0.0, 1.445), (sign * 0.34, 0.0, 1.443), "chest")
        bone("upper_arm." + side, (sign * 0.34, 0.0, 1.443), (sign * 0.70, 0.0, 1.440), "clavicle." + side, True)
        bone("forearm." + side, (sign * 0.70, 0.0, 1.440), (sign * 0.98, 0.0, 1.438), "upper_arm." + side, True)
        bone("hand." + side, (sign * 0.98, 0.0, 1.438), (sign * 1.22, -0.005, 1.436), "forearm." + side, True)
        bone("thigh." + side, (sign * 0.115, 0.0, 0.92), (sign * 0.115, 0.0, 0.51), "pelvis")
        bone("shin." + side, (sign * 0.115, 0.0, 0.51), (sign * 0.115, 0.0, 0.18), "thigh." + side, True)
        bone("foot." + side, (sign * 0.115, 0.0, 0.18), (sign * 0.115, -0.20, 0.07), "shin." + side, True)

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

    bpy.ops.object.camera_add(location=(2.5, -4.6, 1.55))
    camera = bpy.context.object
    camera.name = "Presentation_Camera"
    camera.data.lens = 72.0
    camera.data.sensor_width = 36.0
    track(camera, (0.0, 0.0, 1.00))
    bpy.context.scene.camera = camera
    move_to_collection(camera, presentation)

    light_settings = [
        ("Key_Light", "AREA", (2.6, -3.5, 3.8), 950.0, 1.8, (1.0, 0.88, 0.72)),
        ("Fill_Light", "AREA", (-2.7, -2.0, 2.4), 600.0, 2.3, (0.70, 0.82, 1.0)),
        ("Rim_Light", "AREA", (1.7, 3.4, 3.1), 850.0, 1.6, (0.70, 0.82, 1.0)),
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
    scene.render.resolution_x = 900
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.008, 0.012, 0.025, 1.0)
    background.inputs["Strength"].default_value = 0.34


def render_view(camera, output_path, location, target, lens=72.0):
    camera.location = location
    camera.data.lens = lens
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
    render_view(camera, FRONT_PATH, (0.0, -4.7, 1.06), (0.0, 0.0, 1.02), 72.0)
    render_view(camera, SIDE_PATH, (3.75, -0.15, 1.07), (0.0, -0.01, 1.00), 78.0)
    render_view(camera, BACK_PATH, (0.0, 4.7, 1.06), (0.0, 0.0, 1.02), 72.0)

    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    export_character(character, armature)
    print("CHARACTER_V2_COMPLETE", BLEND_PATH, GLB_PATH)


if __name__ == "__main__":
    main()
