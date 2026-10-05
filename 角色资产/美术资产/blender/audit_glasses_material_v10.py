import hashlib
import json
import math
import os
import struct
import sys


ROOT = os.path.abspath(os.path.dirname(__file__))
DEFAULT_GLB = os.path.join(ROOT, "business_man_tpose_v10.glb")
DEFAULT_REPORT = os.path.join(ROOT, "GLASSES_MATERIAL_AUDIT_V10.json")
LENS_NODE_NAMES = {"Glasses_Lens_L", "Glasses_Lens_R"}


def parse_paths():
    if "--" not in sys.argv:
        return DEFAULT_GLB, DEFAULT_REPORT
    values = sys.argv[sys.argv.index("--") + 1 :]
    if len(values) != 2:
        raise ValueError("Expected GLB and report paths after --")
    return tuple(os.path.abspath(value) for value in values)


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_glb_json(path):
    with open(path, "rb") as handle:
        data = handle.read()
    magic, version, total_length = struct.unpack_from("<4sII", data, 0)
    if magic != b"glTF" or version != 2 or total_length != len(data):
        raise RuntimeError("Invalid GLB header")
    json_length, json_type = struct.unpack_from("<II", data, 12)
    if json_type != 0x4E4F534A:
        raise RuntimeError("First GLB chunk is not JSON")
    return json.loads(data[20 : 20 + json_length].decode("utf-8"))


def close(value, expected, tolerance=1e-6):
    return math.isclose(float(value), expected, abs_tol=tolerance)


def main():
    glb_path, report_path = parse_paths()
    gltf = read_glb_json(glb_path)

    materials = {
        material["name"]: material for material in gltf.get("materials", [])
    }
    lens = materials.get("Glasses Lens")
    frame = materials.get("Glasses Frame")
    if lens is None or frame is None:
        raise RuntimeError("Glasses materials are missing")

    pbr = lens.get("pbrMetallicRoughness", {})
    base_color = pbr.get("baseColorFactor", [1.0, 1.0, 1.0, 1.0])
    extensions = lens.get("extensions", {})
    transmission = extensions.get("KHR_materials_transmission", {})
    clearcoat = extensions.get("KHR_materials_clearcoat", {})

    lens_nodes = {}
    for node in gltf.get("nodes", []):
        if node.get("name") not in LENS_NODE_NAMES:
            continue
        mesh_index = node.get("mesh")
        if mesh_index is None:
            continue
        mesh = gltf["meshes"][mesh_index]
        material_names = []
        for primitive in mesh.get("primitives", []):
            material_index = primitive.get("material")
            if material_index is not None:
                material_names.append(gltf["materials"][material_index]["name"])
        lens_nodes[node["name"]] = {
            "mesh": mesh.get("name"),
            "materials": material_names,
        }

    checks = {
        "lens_alpha_mode_is_blend": lens.get("alphaMode") == "BLEND",
        "lens_alpha_is_semi_transparent": 0.20 <= base_color[3] <= 0.50,
        "lens_base_color_is_blue_gray": (
            base_color[0] < base_color[1] < base_color[2]
            and base_color[2] <= 0.55
        ),
        "lens_roughness_is_low": 0.0 <= pbr.get("roughnessFactor", 1.0) <= 0.12,
        "lens_transmission_is_present": float(
            transmission.get("transmissionFactor", 0.0)
        )
        >= 0.30,
        "lens_clearcoat_is_present": float(clearcoat.get("clearcoatFactor", 0.0))
        >= 0.15,
        "frame_is_opaque": frame.get("alphaMode", "OPAQUE") == "OPAQUE",
        "both_lens_nodes_use_lens_material": (
            set(lens_nodes) == LENS_NODE_NAMES
            and all(
                node["materials"] == ["Glasses Lens"]
                for node in lens_nodes.values()
            )
        ),
    }

    report = {
        "glb_path": glb_path,
        "glb_sha256": sha256_file(glb_path),
        "glb_size_bytes": os.path.getsize(glb_path),
        "lens_material": {
            "name": "Glasses Lens",
            "alpha_mode": lens.get("alphaMode", "OPAQUE"),
            "base_color_factor": base_color,
            "metallic_factor": pbr.get("metallicFactor", 1.0),
            "roughness_factor": pbr.get("roughnessFactor", 1.0),
            "transmission_factor": transmission.get("transmissionFactor", 0.0),
            "clearcoat_factor": clearcoat.get("clearcoatFactor", 0.0),
            "nodes": lens_nodes,
        },
        "frame_material": {
            "name": "Glasses Frame",
            "alpha_mode": frame.get("alphaMode", "OPAQUE"),
        },
        "checks": checks,
        "pass": all(checks.values()),
    }

    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    print("GLASSES_MATERIAL_AUDIT_PASS", report["pass"])
    print("GLASSES_MATERIAL_AUDIT_REPORT", report_path)
    if not report["pass"]:
        raise RuntimeError("Glasses material audit failed")


if __name__ == "__main__":
    main()
