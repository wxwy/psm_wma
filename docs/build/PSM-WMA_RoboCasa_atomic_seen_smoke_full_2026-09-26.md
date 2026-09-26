# PSM-WMA RoboCasa atomic_seen 18-task smoke — full run

Date: 2026-09-26

Status: 18/18 COMPLETE / calibrated20 + required Local-TTT runtime contract PASS

## Scope

This is a runtime smoke, not an official SR benchmark.

Checkpoint:

`iter_000003300`

Evaluation contract:

- `BASE_DECODE_MODE=calibrated`
- `LOCAL_MEMORY_MODE=required`
- `REPLAN_STEPS=1`
- `NUM_TRIALS=1`
- `SAVE_VIDEOS=1`
- `SAVE_PRED_MP4=1`
- task set: `atomic_seen`
- 8-slot queue across 8 GPUs

The production launcher includes the GPT-side client GPU pin fix, so both policy server and simulator client stay on the requested slot GPU.

## Coverage

All 18 atomic_seen tasks completed.

No task reported an infrastructure error.

Episodes reached the task horizon or normal episode termination.

## Hard runtime invariants

Across all 18 completed tasks:

- `bm3_nonzero_steps == 0`
- `arm_active_nonzero_base_steps == 0`
- assertion failures: 0

Therefore the calibrated decoder runtime invariants are accepted as runtime-validated for the full 18-task smoke.

This closes the previous 11/18 partial smoke.

## Control-mode distribution

The new control diagnostics show a clear bimodal policy output rather than threshold jitter.

### Arm-only tasks

16/18 tasks had zero base-active steps.

For those tasks, raw predicted control values stayed saturated near -1:

- per-task mean approximately -0.997 to -0.991;
- standard deviation approximately 0.004 to 0.005;
- no steps near threshold 0;
- `near_threshold_fraction_abs_lt_0p1 = 0.0`.

### Fully base-active task

NavigateKitchen:

- base-active steps: 450 / 450;
- control mean: +0.9763;
- min: +0.8118;
- max: +1.0852;
- base-active fraction: 1.0.

### Mixed task

CloseFridge:

- base-active steps: 116 / 900;
- base-active fraction: 0.129;
- control mean: -0.7367;
- min: -1.0112;
- max: +1.0735.

The distribution crosses from the negative mode to the positive mode in distinct intervals rather than hovering around zero.

## Interpretation

The full smoke does not support a control-threshold or decoder-gating bug.

When the predicted control channel is negative, the calibrated decoder correctly zeros all base commands.

When the predicted control channel is positive, base motion is enabled.

The observation that many tasks never activate the base is therefore a policy/training-behavior finding, not evidence that the evaluator suppresses valid base commands.

Do not change the control threshold on this evidence.

## Success rate

All 18 single-trial episodes had SR=0 in this smoke.

SR is not an acceptance criterion for this runtime run because:

- there is only one rollout per task;
- `REPLAN_STEPS=1` is diagnostic rather than benchmark-style;
- this run was designed to validate infrastructure, Local-TTT online execution, decoder invariants, and diagnostics.

Do not report this as the RoboCasa benchmark result.

## Validation ownership

ds_pro only executed validation, collected statistics, and produced temporary scripts/artifacts.

Production source remained under GPT/ChatGPT ownership.
