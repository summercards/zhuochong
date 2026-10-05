# Character Contract v9

## Deliverable

- Source blend: `I:\工作项目\blender\business_man_tpose_v9.blend`
- Runtime GLB: `I:\工作项目\blender\business_man_tpose_v9.glb`
- Build script: `I:\工作项目\blender\build_character_animations_v9.py`
- Audit report: `I:\工作项目\blender\CHARACTER_ANIMATION_AUDIT_V9.json`
- Audit result: `pass: true`
- Blender version: `4.5.0`
- Animation rate: `30 fps`
- Rollback source:
  - `I:\工作项目\blender\business_man_tpose_v8.blend`
  - `I:\工作项目\blender\business_man_tpose_v8.glb`

The v8 files were used as the source and were not overwritten.

## Runtime Contract

- Armature object: `Character_Rig`
- Bone count: `56`
- Mesh count in exported scene: `121`
- Armature count: `1`
- Camera count: `0`
- Light count: `0`
- Source coordinate system: Blender Z-up
- GLB coordinate system: Y-up, exported with `export_yup=True`
- Root scale contract: `1`
- Animation ownership: the character GLB contains visual meshes, skeleton,
  animation clips, and facial/finger bones. The game controller owns movement,
  collision, HP, input, AI, attacks, damage timing, and state transitions.
- Root motion: all clips are in-place. The `root` bone stays at zero location;
  vertical motion and body offsets are authored on `pelvis` and body bones.

## Facial And Finger Controls

The rig includes the following animation controls:

- Mouth and face: `jaw`, `upper_lip`, `lower_lip`
- Eyes and eyewear: `eye.L`, `eye.R`, `glasses`
- Neck and head: `neck`, `head`
- Fingers, each side: `finger_index_01..03`, `finger_middle_01..03`,
  `finger_ring_01..03`, `finger_pinky_01..03`, `thumb_01..03`

`jaw` rotation drives the primary open/close mouth motion in `talk`.
`upper_lip` and `lower_lip` provide separate upper and lower lip movement.
The `talk` audit sample measures a `15.000031` degree jaw opening,
`0.005 m` upper-lip movement, and `0.010 m` lower-lip movement.

Both hands have independent finger chains. The `attack` clip closes the right
hand fingers; the sampled first finger joints are approximately
`77.9 degrees` per finger. Other clips use relaxed hand poses.

## Action Set

| Action | Frames | Duration | Playback | State-machine use |
| --- | ---: | ---: | --- | --- |
| `idle` | 0-60 | 2.000 s | loop | Default standing state |
| `walk` | 0-32 | 1.066667 s | loop | Grounded locomotion |
| `run` | 0-24 | 0.800 s | loop | Fast locomotion |
| `talk` | 0-60 | 2.000 s | loop | Conversation state |
| `attack` | 0-24 | 0.800 s | one-shot | Attack state; return to locomotion/idle |
| `jump` | 0-36 | 1.200 s | one-shot | Full jump arc with takeoff and landing |
| `hit` | 0-20 | 0.666667 s | one-shot | Hit reaction |
| `crouch` | 0-30 | 1.000 s | loop | Crouched movement or held crouch state |
| `jump_up` | 0-18 | 0.600 s | one-shot | Takeoff/launch transition |
| `defeat` | 0-60 | 2.000 s | one-shot | Defeated state |

`defeat` must clamp on its final pose after playback. Do not loop it. Keep the
character in a dedicated defeated state until the game explicitly resets or
revives it.

`run` has a larger opposed arm swing than `walk`. The audited GLB hand travel
is `0.511373 m` on the left and `0.511372 m` on the right, with opposite phase.

`defeat` finishes with the pelvis rotated approximately `88.005143` degrees
and lowered `0.680 m`. Its final minimum Z is `0.028495 m`, leaving positive
ground clearance.

## Verification

The v9 audit verifies:

- exact action names and durations;
- finite keyframe times and values;
- in-place root behavior;
- loop endpoint continuity for looping clips;
- finite evaluated mesh bounds for every clip;
- ground clearance samples;
- talk jaw and lip motion;
- attack finger closure;
- crouch, jump, and jump-up pelvis offsets;
- hit chest and head rotation;
- walk/run half-cycle leg motion;
- run opposed arm swing;
- defeat fall angle, pelvis drop, final height, and ground clearance;
- imported preview generation for all ten clips.

The final audit file reports `pass: true` with no failed checks.

## Hashes

- v9 Blend SHA256:
  `67ECE5A479900068498181E495891CA0751D0005660116A2668BCB6D7C09CD99`
- v9 GLB SHA256:
  `D47302E4315AB9750C34A835F02D8760F4EA4B70B9940D79D1A6FD21F79BFAF1`
- v8 Blend SHA256:
  `111A0B59AE5C5C7754F2774FCC2068C968B6DF7164BA266981AE5BFAFDCD3210`
- v8 GLB SHA256:
  `954BDA3243AEFD3690E25E0901FC370912A9BC715E76524075666ABA8BE7AF45`
