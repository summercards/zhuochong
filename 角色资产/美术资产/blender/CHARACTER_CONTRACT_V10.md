# Character Contract v10

## Change Summary

Version v10 inherits the complete v9 character and animation contract, with one
visual change: the two glasses lens meshes now use a semi-transparent glass
material. The glasses frame remains opaque.

- Source version: `I:\工作项目\blender\business_man_tpose_v9.blend`
- Source GLB: `I:\工作项目\blender\business_man_tpose_v9.glb`
- v10 Blend: `I:\工作项目\blender\business_man_tpose_v10.blend`
- v10 GLB: `I:\工作项目\blender\business_man_tpose_v10.glb`
- v9 contract:
  `I:\工作项目\blender\CHARACTER_CONTRACT_V9.md`
- Rollback version:
  `I:\工作项目\blender\business_man_tpose_v9.blend`

The v9 files were not overwritten.

## Glasses Material

- Lens objects: `Glasses_Lens_L`, `Glasses_Lens_R`
- Lens material: `Glasses Lens`
- Frame material: `Glasses Frame`
- Lens alpha mode in GLB: `BLEND`
- Lens alpha: `0.32`
- Lens base color: blue-gray `(0.22, 0.38, 0.44, 0.32)`
- Lens roughness: `0.08`
- Lens IOR: `1.47`
- Lens transmission: `0.35`
- Lens clearcoat: `0.20`
- Frame alpha mode: `OPAQUE`
- Blender lens render method: `BLENDED`

Both lens nodes use only `Glasses Lens`; the bridge, frame, and temple meshes
continue to use `Glasses Frame`.

## Inherited Contract

- Armature: `Character_Rig`
- Bone count: `56`
- Mesh count: `121`
- Armature count: `1`
- Runtime root scale: `1`
- Animation rate: `30 fps`
- Animation clips:
  `idle`, `walk`, `run`, `talk`, `attack`, `jump`, `hit`, `crouch`,
  `jump_up`, `defeat`
- Facial controls, both-hand finger controls, in-place root motion, clip
  durations, loop settings, and state-machine usage are unchanged from v9.

## Verification

- Material audit:
  `I:\工作项目\blender\GLASSES_MATERIAL_AUDIT_V10.json`
- Material audit result: `pass: true`
- Animation audit:
  `I:\工作项目\blender\CHARACTER_ANIMATION_AUDIT_V10.json`
- Animation audit result: `pass: true`
- Glasses close-up:
  `I:\工作项目\blender\business_man_tpose_v10_glasses_preview.png`

The close-up was rendered from the exported v10 GLB. The eye, brow, skin, and
frame are visible through the lens, while the lens keeps a restrained
blue-gray glass tint.

## Hashes

- v10 Blend SHA256:
  `1D3D24A2F3E794C56286DFC5155D92AA8EADEEED42BF2BE08D5272C9EDFFA45E`
- v10 GLB SHA256:
  `2E0D207D6424BC1E1E6D5D317F013A140FD6059F3E0AAF1472C13F06FBA92D57`
