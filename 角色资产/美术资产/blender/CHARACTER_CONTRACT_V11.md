# Character Contract v11

## Change Summary

Version v11 inherits the complete v10 character, including the semi-transparent
glasses lenses, and adds one looping street-dance animation clip.

- Source Blend: `I:\工作项目\blender\business_man_tpose_v10.blend`
- Source GLB: `I:\工作项目\blender\business_man_tpose_v10.glb`
- v11 Blend: `I:\工作项目\blender\business_man_tpose_v11.blend`
- v11 GLB: `I:\工作项目\blender\business_man_tpose_v11.glb`
- v10 contract: `I:\工作项目\blender\CHARACTER_CONTRACT_V10.md`
- Rollback Blend: `I:\工作项目\blender\business_man_tpose_v10.blend`

The v10 files and the earlier v9 animation set were not overwritten.

## Dance Clip

- Action name: `dance`
- State-machine use: looped emote or dance state
- Frame rate: `30 fps`
- Frame range: `0-60`
- Duration: `2.0 s`
- Loop: `true`
- Musical structure: four rhythmic beats with off-beat pops
- Beat frames: `0, 8, 15, 23, 30, 38, 45, 53, 60`
- Motion: knee bounce, pelvis bounce and sway, torso twist, head groove,
  alternating large arm swings, open-hand/point/fist gestures, jaw and lip
  percussion, and animated eye/glasses controls
- Pelvis vertical range: `0.066 m`
- Minimum ground clearance: `-0.018469 m`
- Maximum ground clearance during pops: `0.050282 m`
- `root` maximum local displacement: `0.0 m`
- Endpoint loop delta: `0.0`

All body movement and weight transfer are authored on `pelvis`; the runtime
root remains stationary so the character controller owns horizontal movement
and state transitions.

## Inherited Contract

- Armature: `Character_Rig`
- Bone count: `56`
- Mesh count: `121`
- Armature count: `1`
- Runtime root scale: `1`
- Animation rate: `30 fps`
- Animation clips:
  `idle`, `walk`, `run`, `talk`, `attack`, `jump`, `hit`, `crouch`,
  `jump_up`, `defeat`, `dance`
- Facial controls: `jaw`, `upper_lip`, `lower_lip`, `eye.L`, `eye.R`,
  `glasses`
- Finger controls: both hands retain thumb, index, middle, ring, and pinky
  finger chains
- Gameplay ownership remains outside the character asset: movement, collision,
  HP, input, AI, attack timing, and state-machine transitions belong to the
  runtime controller
- Transparent glasses lens material: `Glasses Lens`
- Opaque glasses frame material: `Glasses Frame`

## Verification

- Animation audit:
  `I:\工作项目\blender\CHARACTER_ANIMATION_AUDIT_V11.json`
- Animation audit result: `pass: true`
- Imported action count: `11`
- Glasses material audit:
  `I:\工作项目\blender\GLASSES_MATERIAL_AUDIT_V11.json`
- Glasses material audit result: `pass: true`
- Dance storyboard:
  `I:\工作项目\blender\v11_dance_storyboard\dance_00.png` through
  `I:\工作项目\blender\v11_dance_storyboard\dance_53.png`
- Dance overview:
  `I:\工作项目\blender\business_man_tpose_v11_dance_preview.png`

The animation audit imports the exported v11 GLB and verifies action names,
durations, loop endpoints, finite curves, root motion, pose range, ground
contact, and rendered previews.

## Hashes

- v11 Blend SHA256:
  `BF3DBDD0F91CC6C069DA94C6183CC48E711FEF2E710F7F713384BDAE54ED3106`
- v11 GLB SHA256:
  `AA9004595C8BFD28D9ECF93E662CD3D97412FE7C7048DF306790FF8ABE2575A3`
