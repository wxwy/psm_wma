# PSM-WMA RoboCasa Local-TTT required-mode evaluation fix

Date: 2026-09-24

Status: IMPLEMENTED / REAL required-mode closed-loop smoke pending

## Trigger

ds_pro reproduced the following on root `1b456944` / child `0661be5`:

- `LOCAL_MEMORY_MODE=off`: RoboCasa closed loop completed 900 env steps / 180 inference calls without runtime error.
- `LOCAL_MEMORY_MODE=required`: failed before usable online TTT due to action10-only online evidence validation and launcher/server startup mismatches.

## Formal fixed pair

- root: `e1a774ce2ed49c9666553631d4f34361e71df116`
- child / gitlink: `1b5951e69f25bec494f64f1502e648175e49e845`

Root remote branch remains `V2`; child remote branch is `v2`.

## Fix 1 — parameterized online evidence width

`cosmos_framework/inference/local_memory_online.py`

- added `evidence_version_for_action_dim(action_dim)`
- retained module `EVIDENCE_VERSION` only as the backward-compatible 10-D default
- `OnlineLocalMemory` now derives `action_dim` from `encoder.action_proj.in_features`
- online request validation uses `[N, action_dim]` instead of hard-coded `[N,10]`
- fingerprint/version uses the instance evidence version
- metadata reports instance `evidence_version` and `action_dim`
- `OnlineRecentHistoryMemory` receives the same parameterization so the duplicated 10-D validation cannot regress later

RoboCasa runtime expectation:

`action_dim=20 -> causal_visual96_executed_action20_v1`

LIBERO remains:

`action_dim=10 -> causal_visual96_executed_action10_v1`

## Fix 2 — policy/runtime contract lock

`cosmos_framework/inference/local_memory_policy.py`

The policy adapter still reads `model.config.local_history_action_dim`, but after creating the online runtime it now compares that configured width against the width derived by the runtime encoder.

Mismatch is fail-closed during adapter initialization.

The adapter adopts the runtime instance evidence version after the check.

## Fix 3 — RoboLab non-EMA DCP loading

`cosmos_framework/scripts/action_policy_server_robolab.py`

RoboCasa Local-TTT training disables EMA. The RoboLab inference server now sets:

`use_ema_weights=False`

inside `OmniSetupOverrides` construction.

The root launcher therefore does not pass the unsupported `--no-use-ema-weights` CLI flag.

## Fix 4 — RoboCasa eval launcher

`scripts/eval_robocasa.sh`

Added / corrected:

- `ROBOCASA_ROOT` default:
  `/mnt/data1/data_v2_0617/robocasa365_v3/robocasa365-target-atomic`
- `ROBOCASA_SUITE=robocasa365_target_atomic`
- fail-fast check for `$ROBOCASA_ROOT/meta/info.json`
- server shim first in PYTHONPATH:
  `$CHILD/examples/_server_shim:$CHILD:...`
- removed unsupported `--no-use-ema-weights`
- changed prompt CLI to explicit:
  `--format-prompt-as-json True`

## Added regression coverage

`cosmos_framework/inference/local_memory_online_test.py`

New action20 case creates a canonical `LocalEvidenceEncoder(action_dim=20)`, verifies:

- inferred `memory.action_dim == 20`
- evidence version is `causal_visual96_executed_action20_v1`
- a 20-D online update is accepted
- a 10-D request against that runtime fails closed

## Static closure

Latest repository inspection confirms:

- no remaining hard-coded `tuple(action.shape) != (n, 10)` in inference online-memory validation
- no remaining `torch.empty(0, 10)` retained-action construction
- launcher contains server shim + RoboCasa root
- launcher contains no unsupported `--no-use-ema-weights`
- launcher uses explicit `--format-prompt-as-json True`
- root gitlink equals child `1b5951e...`

## Required runtime acceptance

Run against a checkpoint such as iter400:

```bash
LOCAL_MEMORY_MODE=required \
MAX_TASKS=1 \
NUM_TRIALS=1 \
REPLAN_STEPS=1 \
SAVE_VIDEOS=1 \
scripts/eval_robocasa.sh <checkpoint>
```

PASS requires:

1. server starts without guardrail network download;
2. config resolves ROBOCASA_ROOT;
3. no CLI parse failure;
4. Local Memory metadata reports action_dim=20 / action20 evidence version;
5. first request initializes W0 at step0;
6. next request accepts completed 20-D evidence;
7. online TTT update/read commits without shape/version error;
8. action generation remains finite;
9. env rollout completes the episode or horizon without infrastructure error;
10. session reset succeeds at episode end.

Success-rate value itself is not the acceptance criterion for this smoke.
