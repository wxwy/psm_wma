# PSM-WMA RoboCasa atomic_seen 18-task smoke — partial run

> SUPERSEDED by `PSM-WMA_RoboCasa_atomic_seen_smoke_full_2026-09-26.md` (18/18 complete).

Date: 2026-09-25

Status: PARTIAL 11/18 COMPLETE / decoder runtime contract PASS on completed tasks / full 18-task closure pending

## Run

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
- 8-slot task queue across 8 GPUs

The user explicitly stopped the run at 16:19 CST. Do not restart the missing seven tasks without a new user instruction.

## Completed tasks

11/18 tasks completed without infrastructure errors:

- CloseBlenderLid
- CloseFridge
- CloseToasterOvenDoor
- PickPlaceDrawerToCounter
- CoffeeSetupMug
- NavigateKitchen
- PickPlaceToasterToCounter
- OpenCabinet
- OpenDrawer
- OpenStandMixerHead
- TurnOnElectricKettle

Seven tasks remained incomplete when stopped.

## Decoder runtime contract verdict

Across all 11 completed tasks:

- `bm3_nonzero_steps == 0`
- `arm_active_nonzero_base_steps == 0`
- no assertion failure
- no infrastructure error
- episodes reached horizon or normal termination

This is sufficient to accept the calibrated decoder's two hard runtime invariants on the completed subset.

It is NOT equivalent to 18/18 task-set completion.

## Base activation observation

Only three completed tasks activated the base:

- NavigateKitchen: 450 base-active steps
- CloseFridge: 116
- OpenCabinet: 44

The remaining completed tasks reported zero base-active steps.

This should not be treated as a decoder failure. The decoder only acts after the policy's canonical control channel crosses the base-active threshold.

The next diagnostic question is therefore the policy control-mode output distribution, not another change to base slot/sign or gain.

Production evaluator now records:

- raw predicted `action20[9]`;
- threshold `0.0`;
- base-active fraction;
- raw control-value mean/std/min/max;
- positive fraction;
- near-threshold fraction `abs(value) < 0.1`.

Do not modify the threshold or retrain based only on this smoke.

## Multi-slot GPU bug found and fixed

The server process was pinned with `CUDA_VISIBLE_DEVICES=$EVAL_GPU`, while the eval client inherited the outer environment and could all land on GPU0.

Production `scripts/eval_robocasa.sh` now also launches the closed-loop eval client with:

`CUDA_VISIBLE_DEVICES="$EVAL_GPU"`

so one invocation is self-contained and both server/client stay on the requested slot GPU.

The temporary ds_pro wrapper workaround is no longer required for this issue.

## Role boundary

ds_pro remains validation-only:

- allowed: run, probe, analyze, produce artifacts/reports and temporary `/tmp` launch scripts;
- prohibited: modify production source, launchers, configs, formal tests, or Gitlink.

If local production-file changes exist on the validation machine, preserve artifacts/reports and restore production files to the current GPT/ChatGPT formal pair before the next run.
