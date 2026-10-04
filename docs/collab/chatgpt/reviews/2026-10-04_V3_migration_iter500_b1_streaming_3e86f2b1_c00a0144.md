# V3 migration / iter500 B1 causal streaming fresh review

Date: 2026-10-04

## Formal pair

- root implementation/design SHA: `3e86f2b178b9f1e77603716217a487b18f0c4ee8`
- child/Gitlink SHA: `c00a014444083c7c554fff7626f48cceaf5c5c31`

Canonical design:

`docs/build/PSM-WMA_V3_migration_detailed_design_v1.1_2026-10-04.md`

Verdict:

`REQUEST_CHANGES`

This verdict is **Evidence-only**. Source review found no current production semantic blocker.

## Source-review closure

### CLOSED — V3 is not rebuilt and iter500 is preserved

The V3 branch remains based on the audited latest NVIDIA upstream lineage. No rebase/reset or
checkpoint rewrite was performed.

The H3-F iter500 checkpoint remains valid because its training contract intentionally used:

- official `left|wrist` composite RGB for the native policy outer path; and
- the separate B1 dual-camera causal-endpoint cache for Local-TTT evidence.

The remediation changes online evidence materialization only. It adds/removes no trainable
parameter and changes no H3-F optimizer selector, raw15 width, T16, K4 or checkpoint key.

### CLOSED — wrong per-frame T=1 semantics removed

The rejected child `da6a9b97...` independently encoded every completed frame with T=1.

The new pair instead reproduces the iter500 B1 evidence ABI:

- endpoint 0: one-frame prime;
- endpoint 4,8,12,...: four newly observed frames per camera;
- steps between endpoints reuse the latest causal visual96;
- left/wrist remain independent VAE streams on batch dimension;
- `latent_to_visual96()` remains the sole summary authority.

### CLOSED — episode-length VAE work removed

No full episode RGB history is retained or re-encoded. Online state retains only:

- causal Wan encoder state;
- latest visual96;
- at most three not-yet-encoded RGB frames per camera;
- last committed evidence batch for replay validation.

### CLOSED — duplicated authorities reduced

Current active authorities are centralized for:

- wire/eval contract;
- B1 endpoint vector;
- visual96 transform;
- uint8 normalization;
- Wan stream-state lifecycle;
- completed-evidence chronology.

The B1 builder and real-Wan parity probe reuse those authorities rather than duplicating them.

### CLOSED — evaluation contract matches owner requirement

Required-mode action horizon is no longer hard-coded to 16. The frozen evaluator allows
`1 <= action_horizon <= 16`; common screening settings are 4/8/16.

Only actually executed action-prefix members become evidence.

A persistent 8-GPU screening queue is present at:

`scripts/eval_robocasa_18task_queue.py`

Each GPU owns one persistent model server and simulator worker and pulls tasks from one shared queue.

## Current blockers

### MEDIUM — CPU/static Evidence not executed

- location: `docs/build/PSM-WMA_V3_migration_detailed_design_v1.1_2026-10-04.md:371-384`
- root cause: this ChatGPT environment cannot resolve GitHub for a working checkout, so targeted
  pytest/Ruff execution cannot be claimed.
- frozen contract: endpoint sharing, 4/8/16 chronology, replay/abort/reset, bounded RGB state,
  composite policy path, and unchanged parameter inventory require direct CPU/static Evidence.
- acceptance: run the targeted tests and Ruff/diff checks on this exact formal pair; all must pass.

Production implementation currently has no source-review blocker under this item.

### HIGH — real Wan offline-vs-streaming parity Evidence missing

- location: `docs/build/PSM-WMA_V3_migration_detailed_design_v1.1_2026-10-04.md:386-393`
- root cause: source equivalence of the causal algorithms is not sufficient to claim numerical
  parity on the real Wan2.2 VAE.
- frozen contract: online prime+4 streaming must reproduce the B1 offline endpoint representation
  consumed during iter500 training.
- acceptance:
  1. run `tools/v3/verify_robocasa_b1_streaming_parity.py` on a real frozen train episode;
  2. return per-endpoint fp16 and visual96 differences;
  3. freeze a numeric tolerance from that direct evidence;
  4. rerun with the frozen threshold and obtain PASS.

### HIGH — iter500 closed-loop 4/8/16 Evidence missing

- location: `docs/build/PSM-WMA_V3_migration_detailed_design_v1.1_2026-10-04.md:395-405`
- root cause: the new transactional visual-stream + Local fast-state path has not yet been executed
  against the real checkpoint and simulator.
- frozen contract: for action horizons 4, 8 and 16, completed evidence must advance exactly once,
  prefix must appear after cold start, fast state must remain finite, reset/replay must stay correct,
  and server GPU memory must not grow with episode history length.
- acceptance: run the three required-mode iter500 smokes on this exact pair and return raw logs,
  Local telemetry and GPU-memory observations.

## Downstream behavioral Gate

The 18-task × fixed-seed screening at
`docs/build/PSM-WMA_V3_migration_detailed_design_v1.1_2026-10-04.md:407-415`
is authorized **only after** the three blockers above close.

Use the same iter500 checkpoint. No retraining is requested.

## Supersession

The earlier pair:

- root `fc453ef7967cced3323ddf40ac480538c2a0ec19`
- child `da6a9b972575af829af63e7747fad2fd73ae8157`

and its current-frame T=1 execution Gate are superseded and must not be run.

## Scope

This `REQUEST_CHANGES` blocks runtime/GPU/behavioral closure only.

It does **not** authorize:

- retraining;
- continuing the 30k job;
- changing the iter500 checkpoint;
- changing raw15/T16/K4;
- ds/ds_pro code modifications.

ds/ds_pro are execution/Evidence only.
