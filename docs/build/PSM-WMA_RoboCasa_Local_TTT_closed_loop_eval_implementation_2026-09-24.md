# PSM-WMA RoboCasa Local-TTT Closed-Loop Evaluation Implementation

Date: 2026-09-24

Status: CODE COMPLETE / REAL ROB0CASA RUNTIME SMOKE PENDING

## Scope

This implementation adds the RoboCasa closed-loop evaluation path corresponding to the existing LIBERO evaluation path.

Implemented components:

- RoboCasa Gym task rollout using the official task registry and task horizons.
- task-set / task-index / trial selection.
- official success semantics: info["success"].
- left_wrist observation composition matching current training.
- state16 construction matching the EMBER v3 training schema.
- active Local-TTT session / evidence / acknowledgement / episode reset.
- canonical model action20 -> RoboCasa env action12 decoding.
- completed Local-TTT evidence based on the actual executed environment transition.
- actions / predictions / per-episode JSON / per-task summary / aggregate SR.
- rollout MP4 output.
- root one-command launcher: scripts/eval_robocasa.sh.

## Child implementation

Key files:

- cosmos_framework/scripts/action_policy_server_robolab.py
- cosmos_framework/inference/local_memory_policy.py
- cosmos_framework/simulation/robocasa/local_memory_client.py
- cosmos_framework/simulation/robocasa/closed_loop_eval.py
- cosmos_framework/simulation/robocasa/closed_loop_eval_test.py

The RoboLab server now supports action_space=robocasa_ego and the active Local-TTT inference adapter.

RoboCasa Local-TTT evidence contract:

- evidence version: causal_visual96_executed_action20_v1
- evidence format: robocasa_rgb_action20_v1
- pre-action image: left|wrist
- action: completed canonical 20-D evidence
- fast state persists through one episode/session
- episode boundary explicitly resets server state

## Evaluation action contract

The trained model uses:

base ego delta9 + control_mode1 + arm/gripper10 = 20D

RoboCasa Gym consumes the official flat controller action:

EEF xyz3 + EEF axis-angle3 + gripper1 + base_motion4 + control_mode1 = 12D

The evaluator converts EEF rot6d back to axis-angle and discretizes control_mode to -1/+1.

For Local-TTT completed evidence, the base 9D block is NOT copied from the prediction. It is recomputed from the observed pre/post base pose with the same ego-relative delta construction used by RoboCasaLeRobotDataset._build_base_delta.

## Mobile-base decoding caveat

The training base representation is an observed per-step state delta, while PandaOmron's simulator base controller is velocity controlled.

The evaluator exposes:

- velocity: delta * 20 Hz (default)
- delta: send the per-step delta directly
- zero: disable base motion for manipulation-only smoke

The code path is ready, but official benchmark parity for navigation/base-active tasks requires one real simulator calibration smoke before treating velocity as frozen.

Arm-active tasks do not depend on this ambiguity because control_mode=-1 disables base motion.

## Intended first smoke

Use one task and one trial:

MAX_TASKS=1 NUM_TRIALS=1 REPLAN_STEPS=1 SAVE_VIDEOS=1 \
scripts/eval_robocasa.sh /absolute/path/to/checkpoint

Required evidence:

1. server loads the DCP checkpoint;
2. server reports Local-TTT enabled and action20;
3. RoboCasa environment resets;
4. left|wrist observation and state16 reach the server;
5. action chunk [T,20] is returned;
6. one action is decoded and executed;
7. completed evidence is accepted on the next query;
8. Local-TTT acknowledgement frontier advances;
9. episode reset removes the session;
10. episode JSON and video are written.

## Runtime status

The current connected execution device is offline, so a real MuJoCo/GPU smoke could not be executed from this chat. Do not report the closed-loop path as runtime-validated until the above smoke passes.
