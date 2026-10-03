# V3 RoboCasa Local-TTT current-frame evidence remediation

Date: 2026-10-04

## Formal implementation target

- root implementation SHA: `fc453ef7967cced3323ddf40ac480538c2a0ec19`
- child/Gitlink SHA: `da6a9b972575af829af63e7747fad2fd73ae8157`
- previous pair: root `d671edae8c6fb6ff48c0f30bf8be18477e0592a6` / child `dfc705f074a6eb6185b7c1108e9d3f7fe8a7bbf6`

## Scope

Fix only the V3 RoboCasa online Local-TTT visual-evidence construction.

Frozen semantics for this remediation:

- completed evidence is the pre-action **current observation** plus the actually executed raw15 action;
- the four 4-frame future latents used by training are labels and are not reconstructed at inference;
- Local-TTT may consume 4 / 8 / 16 completed steps according to the evaluator replan horizon;
- policy generation occurs only at the normal replan boundary;
- trainer, dataset, Local-TTT core, action decode and rollout chronology are out of scope.

## Implementation review

### CLOSED — full-history VAE encoding removed

Previous code accumulated episode RGB history and re-encoded `frames[:max_endpoint+1]`.
That caused VAE work to scale with episode length and did not match the owner-frozen inference contract.

The new implementation:

- deletes episode-long left/wrist frame storage;
- batches completed current frames on **B**, never on temporal history;
- calls the existing `OmniMoTModel._encode_vision_item` authority with shape
  `[2N,3,1,256,256]`, where `N` is the number of newly completed steps;
- keeps temporal length exactly `T=1`;
- reuses the existing `latent_to_visual96` authority;
- retains only the last committed batch visual summary, raw15 actions and visual digest for exact replay validation.

No second VAE normalization/encoding implementation was introduced.

### CLOSED — stale evidence contract cannot silently mix

Evidence protocol was bumped to:

- `current_frame_visual96_executed_action15_v4`
- `robocasa_current_left_wrist_raw15_v2`

Client and server adapter use the same new literals.

### CLOSED — replan horizon coverage

The adapter tests now explicitly cover completed evidence counts:

- 4
- 8
- 16

and require the VAE input temporal dimension to remain one.

### CLOSED — replay semantics preserved without historical RGB retention

Exact committed replay still reuses the cached visual summary and performs no second VAE encode.
Changed visual evidence and changed raw15 evidence both fail closed.

## Static evidence

Reviewed child diff `da6a9b972575af829af63e7747fad2fd73ae8157` after commit.

Confirmed statically:

- no `_encode_camera_prefix` remains in the adapter;
- no `previous.left_frames` / `previous.wrist_frames` history dependency remains;
- current-frame path reuses `model._encode_vision_item`;
- tests encode independent current frames with T=1;
- server comment and client protocol literals were updated consistently.

The current ChatGPT execution environment could not clone GitHub to execute pytest/GPU runtime.
Therefore runtime evidence is intentionally not claimed.

## Status

Production implementation: **no static blocker found**.

Runtime / behavioral evidence: **OPEN**.

This is not yet a runtime approval. ds/ds_pro may only execute the Gate below and must not modify code.

## Authorized Gate

1. Sync exact formal pair above.
2. Run relevant CPU/static tests, especially:
   - `cosmos_framework/inference/robocasa_local_memory_policy_test.py`
   - `cosmos_framework/inference/local_memory_online_test.py`
   - `cosmos_framework/simulation/robocasa/local_memory_client_test.py`
3. Run a minimal real RoboCasa Local-TTT smoke with iter500.
4. Verify 4/8/16 replan horizons can advance `adapted_steps` by the corresponding number of completed steps.
5. Record server GPU memory after model load and across increasing replans; memory must not scale with episode history length.
6. If the smoke is green, rerun the same 18 target-atomic × seed0 screening on iter500 and save all rollout MP4s.

Do not continue training, patch code, change dataset/action semantics, or add RL/planner/FSM before this Gate returns.
