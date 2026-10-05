# Business Man Character Contract V5

## Asset identity

- Asset type: standalone stylized humanoid character visual
- Version: v5
- Source reference:
  `C:\Users\ZHUANG~1\AppData\Local\Temp\codex-clipboard-6aee020d-3540-4c09-96e2-db9b3da614c1.png`
- Source Blend:
  `I:\工作项目\blender\business_man_tpose_v5.blend`
- Runtime export:
  `I:\工作项目\blender\business_man_tpose_v5.glb`
- Build script:
  `I:\工作项目\blender\build_character_v5.py`
- Audit script:
  `I:\工作项目\blender\audit_character_glb.py`
- Audit report:
  `I:\工作项目\blender\CHARACTER_AUDIT_V5.json`
- Pose test script:
  `I:\工作项目\blender\pose_test_character_v4.py`
- Pose test report:
  `I:\工作项目\blender\CHARACTER_POSE_AUDIT_V5.json`

The supplied reference is a natural-stance front/side/back character sheet.
The asset pose is an inferred strict T-pose. Occluded arm and garment
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
- Skin: layered deterministic weights with `Preserve Volume`
- Shoulder supports: `Shoulder_L` and `Shoulder_R`, each with a valid
  `ARMATURE` modifier targeting `Character_Rig`

Maximum measured head-tail vertical error across the upper arm, forearm, and
hand in the exported T-pose is `0.009425 m`, within the `0.01 m` audit limit.

## Asset statistics

- Character meshes: 121
- Vertices: 27,585
- Triangles: 35,784
- Materials: 17
- Bounding dimensions: `1.926 x 0.428331 x 1.857 m`
- GLB SHA256:
  `fabb6c0d87dc3a22c43e87ce3b181c24e33ed56c3e63aab88e1bf33842543131`
- Blend SHA256:
  `0fb13d83457cacba3a8d6cf0338d028f7654220c44a430d64fdc49456ace24c7`

## Preview files

- Front:
  `I:\工作项目\blender\business_man_tpose_v5_front.png`
- Side:
  `I:\工作项目\blender\business_man_tpose_v5_side.png`
- Back:
  `I:\工作项目\blender\business_man_tpose_v5_back.png`
- Pose stress test:
  `I:\工作项目\blender\business_man_tpose_v5_pose_test.png`

## Validation status

- Blender 4.5 clean GLB round-trip: pass
- Export scope: pass, no camera, light, ground, or Tripo object
- Root orientation and scale: pass
- Armature and expected bone families: pass
- T-pose horizontal arm alignment: pass
- Measured bounds and ground contact: pass
- Shoulder support binding and upper-arm follow-through: pass in pose stress test
- Finite evaluated geometry in rest and tested animation pose: pass

This is a complete stylized production blockout suitable for proportion
review, rig testing, gameplay presentation, further sculpting, and
retopology. It is not a photo-real scan, high-detail facial likeness, or
final topology asset. The pose stress test verifies rig attachment and
finite deformation; it is not a cloth-simulation quality proof.

## Version and rollback

- Current source:
  `I:\工作项目\blender\business_man_tpose_v5.blend`
- Current export:
  `I:\工作项目\blender\business_man_tpose_v5.glb`
- Previous contract:
  `I:\工作项目\blender\CHARACTER_CONTRACT_V4.md`
- Previous source:
  `I:\工作项目\blender\business_man_tpose_v4.blend`
- Previous export:
  `I:\工作项目\blender\business_man_tpose_v4.glb`

Do not overwrite v4 or v5. Any subsequent refinement must use v6 or later and
must keep the v5 Blend, GLB, previews, audit reports, and this contract
unchanged.
