# Business Man Character Contract V4

## Asset identity

- Asset type: standalone stylized humanoid character visual
- Version: v4
- Source reference:
  `C:\Users\ZHUANG~1\AppData\Local\Temp\codex-clipboard-6aee020d-3540-4c09-96e2-db9b3da614c1.png`
- Source Blend:
  `I:\工作项目\blender\business_man_tpose_v4.blend`
- Runtime export:
  `I:\工作项目\blender\business_man_tpose_v4.glb`
- Build script:
  `I:\工作项目\blender\build_character_v4.py`
- Audit script:
  `I:\工作项目\blender\audit_character_glb.py`
- Audit report:
  `I:\工作项目\blender\CHARACTER_AUDIT_V4.json`

The supplied reference is a natural-stance front/side/back character sheet.
The asset pose is a requested inferred T-pose; occluded arm and garment
construction was rebuilt conservatively rather than copied from the sheet.

## Runtime contract

- Runtime consumer: none supplied
- Controller, collision, AI, HP, combat, input, animation clips, sockets, and
  equipment slots: not inferred or added
- Import root: `Character_Rig`
- Forward axis: `-Y`
- Up axis: `+Z`
- Creation height target: `1.86 m`
- Runtime visual height: `1.857 m`
- Runtime wrapper scale: `1.0`
- Ground contact: minimum `Z = 0.001 m`
- Rest pose: strict horizontal-arm T-pose

The GLB contains only the character meshes and one armature. Cameras, lights,
ground planes, and presentation helpers are excluded from the runtime export.
Blender's importer helper `Icosphere` in `glTF_not_exported` is not part of the
GLB content and is excluded from character audits.

## Rig contract

- Armature: `Character_Rig`
- Bone count: 20
- Root transform: location `(0, 0, 0)`, rotation `0`, scale `1`
- Central chain: `root`, `pelvis`, `spine`, `chest`, `neck`, `head`
- Arm chains: `clavicle`, `upper_arm`, `forearm`, and `hand`, sided `.L` / `.R`
- Leg chains: `thigh`, `shin`, and `foot`, sided `.L` / `.R`
- Skin: evaluated automatic two-bone weighting with `Preserve Volume`

Maximum measured head-tail vertical error across the upper arm, forearm, and
hand in the exported T-pose is `0.009425 m`, within the `0.01 m` audit limit.

## Asset statistics

- Character meshes: 119
- Vertices: 26,203
- Triangles: 33,352
- Materials: 17
- Bounding dimensions: `1.926 x 0.428331 x 1.857 m`
- GLB SHA256:
  `f8cd4b3c8203b9e18ef6221a5734c850911d7fdb55dfc06e79a72e53734c303b`
- Blend SHA256:
  `fd1501ceba104cec8cfed502b2dfe35aa10bd24f6bd8c84cf5ecbebb0e6d44aa`

## Preview files

- Front:
  `I:\工作项目\blender\business_man_tpose_v4_front.png`
- Side:
  `I:\工作项目\blender\business_man_tpose_v4_side.png`
- Back:
  `I:\工作项目\blender\business_man_tpose_v4_back.png`

## Validation status

- Blender 4.5 clean GLB round-trip: pass
- Export scope: pass, no camera, light, ground, or Tripo object
- Root orientation and scale: pass
- Armature and expected bone families: pass
- T-pose horizontal arm alignment: pass
- Measured bounds and ground contact: pass

This is a complete stylized production blockout suitable for proportion
review, rig testing, gameplay presentation, further sculpting, and
retopology. It is not a photo-real scan, high-detail facial likeness, or
final topology asset.

## Version and rollback

- Current source:
  `I:\工作项目\blender\business_man_tpose_v4.blend`
- Current export:
  `I:\工作项目\blender\business_man_tpose_v4.glb`
- Previous contract:
  `I:\工作项目\blender\CHARACTER_CONTRACT.md` (historical v1, 16-bone record)

Do not overwrite v4. Any subsequent refinement must be created as v5 and must
keep the v4 Blend, GLB, previews, audit report, and this contract unchanged.
