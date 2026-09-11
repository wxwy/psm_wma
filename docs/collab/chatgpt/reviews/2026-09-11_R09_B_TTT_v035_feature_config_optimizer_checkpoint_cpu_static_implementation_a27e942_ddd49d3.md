# ChatGPT Independent Review — R09-B TTT v0.3.5 Feature / Config / Optimizer / Checkpoint CPU/static Implementation

- Date: 2026-09-11
- Formal root implementation SHA: `a27e9425e4f8e05d7e9ef5414a75f103a2f39d3d`
- Child/Gitlink SHA: `ddd49d318a7b2198e024cd013859ca956b57479d`
- Gate: `G0-R09-B-TTT-V035-FEATURE-CONFIG-OPTIMIZER-CHECKPOINT-REFREEZE-CPU-STATIC-IMPLEMENTATION`
- Approved implementation design: `docs/build/PSM-WMA_Local_Memory_v0.3.5_feature_config_optimizer_checkpoint_cpu_static_implementation_design_v0.1.md`
- Prior ChatGPT Design-Gate review: `docs/collab/chatgpt/reviews/2026-09-11_R09_B_TTT_v035_feature_config_optimizer_checkpoint_cpu_static_implementation_design_93529fb_d96406e.md`

## Verdict

`REQUEST_CHANGES(cosmos_framework/model/generator/mot/config_checkpoint_contract.py:215)`

## Current blockers

`3 HIGH + 1 MEDIUM`

The six-file scope is respected and several intended migrations are implemented correctly, but this pair does **not** close the frozen CPU/static contract. The central blocker is that `strict_restore_into()` still begins mutating live slow parameters while fallible optimizer/scheduler restore work remains. In addition, optimizer ownership is not object-bound, and the required real-authority Evidence matrix is not closed.

## HIGH-1 — restore is still not preflight-first atomic

The frozen v0.2/refreeze contract and the approved implementation design require:

`decode/stage -> validate every fallible config/base/inventory/tensor/optimizer/scheduler/iteration contract -> validate fresh/quiescent runtime admission -> mutate existing objects exactly once`.

Current `config_checkpoint_contract.py` does not satisfy that order. `_stage_restore()` checks only shallow optimizer group schema/count and scheduler key-set compatibility. `strict_restore_into()` then starts live slow-parameter mutation at line 215/217 and only afterwards calls:

- `optimizer.load_state_dict(payload["optimizer"])` at line 219;
- `state_scheduler.load_state_dict(payload["scheduler"])` at line 221.

Both are still fallible apply operations. Therefore a payload can pass the current preflight, mutate all slow tensors, then fail while loading optimizer or scheduler state, leaving a partially restored live system. This is exactly the failure mode the prior refreeze remediation prohibited; post-mutation rollback is not an allowed substitute for this first CPU/static implementation.

The optimizer case is not theoretical: the current preflight only requires the saved `param_groups` list to have the same keys and parameter count as the live group. A same-length malformed `params` payload can pass those checks yet still fail inside `Optimizer.load_state_dict()` after the slow parameters have already been copied.

### Exact acceptance

Before the first live mutation:

1. fully decode/stage and validate optimizer state, group schema and loadability without mutating the live optimizer;
2. fully decode/stage and validate scheduler state/loadability without mutating the live scheduler;
3. prove a deliberately late optimizer defect and a deliberately late scheduler defect both reject with slow tensors, optimizer groups/state, scheduler state, iteration and registered object identities byte/object-for-object unchanged;
4. after the first live mutation, no validation/load path may still raise under an admitted payload.

## HIGH-2 — live optimizer membership is not bound to the exact canonical slow Parameter objects

The frozen contract requires optimizer membership to be object-bound to the exact canonical slow inventory. Current `strict_restore_into()` validates `expected` against the canonical inventory, but it never validates that the supplied live `optimizer.param_groups[*]["params"]` are those exact `Parameter` objects.

`_stage_restore()` reads `optimizer.state_dict()` and checks serialized group keys/counts only. Serialized parameter IDs/counts cannot prove Python object identity. An optimizer over foreign parameters with the same number of groups/parameters can therefore pass preflight, even though it is not the optimizer for the registered `local_memory_runtime.evidence_encoder`, `ttt_core`, `local_memory2llm`, and modality parameter objects.

### Exact acceptance

Before mutation, compare the live optimizer's actual parameter objects and frozen group/order schema against the exact canonical slow inventory. Add direct positive and negative witnesses:

- exact registered slow objects -> accepted;
- same-shape/same-count foreign optimizer parameters -> rejected pre-mutation;
- reordered/duplicated/missing group membership -> rejected pre-mutation;
- all rejection witnesses prove zero mutation on slow state and optimizer/scheduler/iteration state.

## HIGH-3 — the required real-authority Evidence matrix is not closed

The approved Design-Gate review explicitly required live-runtime admission evidence to use the real existing adapter/frontier/scheduler/transaction/recovery authority objects, not test-only mirrors or direct private-container edits.

Current `config_checkpoint_contract_test.py` does the opposite for the two main negative witnesses:

- it manually executes `adapter._scan_requests.add(1)` rather than minting a real pending scan/native/commit/retry/suffix authority through the production APIs;
- it manually appends `SimpleNamespace()` to `scheduler._frozen_transitions` rather than creating an actual frozen plan/open transaction/recovery lineage.

The test set also does not directly cover the approved matrix's legal optimizer/scheduler/base/iteration round trip, late optimizer/scheduler/owner defect with zero mutation, committed frontier state, pending native-forward/commit/retry/suffix authority, open transaction/recovery receipt, and fresh success after those negative cases. The 45-pass aggregate therefore does not establish the required contract -> behavior -> evidence chain.

The active-owner test in `omni_mot_model_test.py` also manually constructs a `local_memory_runtime` container; it verifies `_canonical_production_adapter_from_model()` identity binding, but does not directly witness the production active-TTT registration branch that must exclude the legacy registered owner/readout.

### Exact acceptance

Close the nine-item implementation-design acceptance matrix with direct CPU/static witnesses using real production objects and public/typed authority creation paths. In particular:

1. create a real `CanonicalBatchScheduler.freeze_plan()` / transaction lineage;
2. create real adapter scan/native-forward/commit/retry/suffix/recovery authority states rather than editing private sets/dicts;
3. seed a real committed fast-state frontier;
4. prove each live category rejects restore before mutation with unchanged slow/runtime snapshots;
5. prove fresh/quiescent success remains object-identically bound to the registered encoder/core;
6. exercise optimizer state/group, scheduler state, base identity and iteration in the legal round trip and late-defect negatives;
7. add a direct static production-registration witness for the active-TTT `local_memory_runtime` root/children and absence of a legacy registered trainable owner/readout.

## MEDIUM-1 — the frozen `local_memory2llm` 32 -> 2048 production ABI is not enforced

The approved contract freezes per-token projection as `32 -> 2048`. The current helper test fixture creates `nn.Linear(32, 2048)`, but production config/registration does not fail closed on that invariant:

- `OmniMoTModelConfig.local_memory_dim` remains unconstrained to exact 32 for active TTT;
- `Cosmos3VFMNetwork` constructs `local_memory2llm = nn.Linear(config.local_memory_dim, self.hidden_size, ...)`;
- `canonical_slow_inventory()` accepts the projector regardless of its input/output widths.

Thus a non-32 local dimension or non-2048 hidden width can still enter this CPU/static slow inventory/checkpoint contract while all current selector/restore checks pass.

### Exact acceptance

For `local_ttt_enabled=True`, fail closed unless the registered projector is exactly per-token `32 -> 2048` and the modality embedding is width 2048; add a direct production/static witness. Do not concatenate K slots; `k_local=1` remains the first-rollout identity.

## Findings that are closed on this pair

The following portions of the implementation are consistent with the approved design and are not current blockers:

- child diff is exactly one commit ahead of `d96406e...` and modifies only the approved six files;
- formal root `a27e9425...` resolves `cosmos-framework` exactly to reachable child `ddd49d318...`;
- `LocalMemoryConfig` now uses the versioned v0.3.5 identity, removes legacy `runtime_evidence_steps`, narrows `k_local` to exact 1 and freezes feature/dtype/resume values;
- active-TTT model registration migrates from the legacy `local_history_runtime` container to one registered `local_memory_runtime` with `evidence_encoder` and `ttt_core` children;
- `_canonical_production_adapter_from_model()` now binds to those exact registered children;
- the legacy R08/non-TTT registration path remains separate;
- concrete core slow-key names match the approved `w0_fast_*`, K/Q/V projection and `slot_queries` mapping, while runtime fast state remains outside `named_parameters()`;
- public canonical production still stops at the existing unavailable-native-forward hard-stop; this pair does not authorize real runtime activation.

## Scope / execution

This is an independent source/Evidence review. I did not treat the reported `45 passed` count as sufficient by itself and did not use MM/Kimi conclusions as technical authority. I did not execute real checkpoint/filesystem/DCP/remote I/O, public runtime activation, native forward/loss/backward, optimizer/scheduler step, CUDA/GPU, `torchrun`, runtime sidecar, training, evaluation, inference, distributed execution, matched smoke or LIBERO4IN1.

## Authorized next action

Remediate only within the already approved six-file synthetic CPU/static scope, then submit a **new formal root/child pair** for fresh incremental closure review.

Still not authorized: Gate closure, any file outside the six-file whitelist, real checkpoint I/O/backend wiring, public runtime/hard-stop removal, real native forward/loss/backward, real optimizer/scheduler stepping, CUDA/GPU, `torchrun`, runtime sidecar/mid-episode resume, training, evaluation, inference, distributed execution, matched smoke or LIBERO4IN1.
