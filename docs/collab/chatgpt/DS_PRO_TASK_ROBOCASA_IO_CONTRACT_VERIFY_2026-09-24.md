# DS_PRO Task — RoboCasa action / observation contract verification

Date: 2026-09-24

Purpose: prove, dimension by dimension, that the current PSM-WMA RoboCasa evaluation I/O contract matches the exact RoboCasa365 v3 training contract and the live RoboCasa simulator. Do not accept "the rollout runs" as proof.

## Already-established source contracts

EMBER RoboCasa365 v3 flat schema used by current training:

- observation.state[16] =
  - [0:3] base_pos
  - [3:7] base_quat xyzw
  - [7:10] eef_pos_rel
  - [10:14] eef_quat_rel xyzw
  - [14:16] gripper_qpos
- raw action[12] =
  - [0:4] base_motion
  - [4] control_mode
  - [5:8] eef_delta_pos
  - [8:11] eef_delta_axisangle
  - [11] gripper
- control_mode: -1 arm-active, +1 base-active
- cameras: agentview_left / agentview_right / eye_in_hand, each 256x256.

Current PSM-WMA training canonical action[20]:

- [0:3] observed ego-frame base translation delta
- [3:9] observed relative base rotation as rot6d
- [9] raw control_mode
- [10:13] eef delta translation
- [13:19] eef delta rotation rot6d
- [19] gripper

Current runtime simulator flat action expected by official robocasa.utils.env_utils.convert_action:

- [0:3] eef position
- [3:6] eef axis-angle rotation
- [6] gripper
- [7:11] base_motion
- [11] control_mode

## Critical unresolved item

The arm/gripper branch has an algebraic inverse:
axisangle -> matrix -> rot6d during training, then rot6d -> axisangle at eval.

The base branch does NOT have a purely algebraic inverse:
training converts raw base_motion(4) into the observed next-state transition
(base ego translation3 + relative rotation6 = 9D). The evaluator currently
maps that observed delta back to base velocity heuristically.

Therefore the mobile-base decoder must be empirically verified against the real dataset/controller before it is frozen.

Also verify the meaning of raw base_motion[3]. Do not assume it is base-z/torso. Measure its dataset distribution and inspect the live controller action split. If it is the torso slot and is zero in the dataset, the evaluator should explicitly emit zero rather than map base z delta into it.

## Gate A — dataset schema and statistics

Use the actual current target-atomic root:

`/mnt/data1/data_v2_0617/robocasa365_v3/robocasa365-target-atomic`

Read real rows from LeRobot v3. Record:

1. action shape and state shape;
2. per-action-dimension min/max/mean/std;
3. exact/near-exact unique values for action[4] control_mode;
4. fraction control_mode < 0 and > 0;
5. action[0:4] stats separately for arm-active and base-active frames;
6. especially action[3] (fourth base_motion slot): std, nonzero fraction, min/max;
7. state base z (state[2]) std and one-step delta std;
8. base quaternion roll/pitch change magnitudes vs yaw change.

Acceptance:
- control_mode must agree with -1 arm / +1 base;
- establish whether base_motion[3] is actually used;
- establish whether observed base motion is planar.

## Gate B — offline raw12 -> canonical20 -> env12 round-trip

For at least 10,000 valid consecutive frame pairs from the actual training dataset:

1. take raw action_t[12], state_t[16], state_t+1[16];
2. construct canonical20 exactly as RoboCasaLeRobotDataset does:
   - base delta from state_t -> state_t+1;
   - raw control_mode;
   - eef pos + axisangle->rot6d + gripper;
3. decode canonical20 with the current evaluation canonical20_to_env12;
4. construct the ground-truth official simulator command by reordering raw12:
   `[raw[5:8], raw[8:11], raw[11], raw[0:4], raw[4]]`;
5. report per-dimension MAE / RMSE / max error / correlation.

Report separately:

- arm-active frames (control_mode < 0):
  - env dims 0:7 and dim11 must round-trip numerically (rotation tolerance allowed);
- base-active frames (control_mode > 0):
  - env dims 7:11 are the critical comparison;
  - report each of the four base dimensions separately.

Do not hide errors by averaging all 12 dimensions.

## Gate C — live simulator action split

Create one official RoboCasa target env with PandaOmron and print:

- env.action_space;
- env.unwrapped.robots[0] action info / controller action split, using print_action_info/get_action_info if available;
- controller type for base and torso;
- control frequency.

Verify official convert_action maps:
- 0:3 -> action.end_effector_position
- 3:6 -> action.end_effector_rotation
- 6 -> action.gripper_close
- 7:11 -> action.base_motion
- 11 -> action.control_mode

Then run bounded basis probes with fresh reset for every probe:

- arm-active (-1): perturb one EEF dimension at a time;
- base-active (+1): perturb each base_motion dimension 7,8,9,10 separately.

Record pre/post:
- state.base_position
- state.base_rotation
- state.end_effector_position_relative
- state.end_effector_rotation_relative
- state.gripper_qpos

This establishes what each base_motion slot physically drives. No inference model is needed for this gate.

## Gate D — observation parity

Training v3 contract to verify:

- left image source: observation.images.robot0_agentview_left
- wrist source: observation.images.robot0_eye_in_hand
- each source 256x256 RGB
- left_wrist composition: horizontal left | wrist -> 256x512
- ActionTransformPipeline resolution=None auto-resolves 256 tier; expected padded training geometry must match eval transform.

Runtime contract to verify:

- obs["video.robot0_agentview_left"] is HWC RGB 256x256
- obs["video.robot0_eye_in_hand"] is HWC RGB 256x256
- compose_left_wrist yields HWC RGB 256x512 in exactly left | wrist order
- eval server transform produces exactly the same final spatial size as one real training sample.

State parity:
construct runtime state as
`base_pos + base_quat + eef_pos_rel + eef_quat_rel + gripper_qpos`
and confirm [16] ordering exactly matches the EMBER v3 schema.

Prompt parity:
- training uses LeRobot `sample["task"]`;
- runtime uses `obs["annotation.human.task_description"]`.
Verify on real metadata / environment that both are the intended natural-language task-description field (not underlying task-class id), and record example strings.

Camera orientation:
compare one runtime left/wrist frame visually against the dataset convention. If possible, replay one source episode; otherwise explicitly record that exact pixel-level replay parity was not proven. Do not silently introduce vertical/180-degree flips.

## Required verdict

Return a table with every field:

- TRAIN source
- canonical model field
- EVAL decoded field
- simulator key
- status: EXACT / EMPIRICALLY CALIBRATED / MISMATCH / UNVERIFIED

At minimum include:
- base dx/dy/dz + base rot6d six channels
- control_mode
- eef dx/dy/dz
- eef rot6d six channels
- gripper
- both camera views
- all five state groups
- language prompt.

If any base-active dimension is not demonstrably aligned, stop and report before changing the decoder.

Do not modify the running formal training process.
