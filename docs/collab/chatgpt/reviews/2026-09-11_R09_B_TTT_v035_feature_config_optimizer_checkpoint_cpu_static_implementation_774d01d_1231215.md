# ChatGPT Independent Review — R09-B TTT v0.3.5 Feature / Config / Optimizer / Checkpoint CPU/static Implementation Evidence Closure v2

- Date: 2026-09-11
- Formal root implementation SHA: `774d01d43c8a144747ee93014b2c11afe91498b3`
- Child/Gitlink SHA: `1231215fb066142251ce556ba59241ada54ef18a`
- Gate: `G0-R09-B-TTT-V035-FEATURE-CONFIG-OPTIMIZER-CHECKPOINT-REFREEZE-CPU-STATIC-IMPLEMENTATION`
- Approved implementation design: `docs/build/PSM-WMA_Local_Memory_v0.3.5_feature_config_optimizer_checkpoint_cpu_static_implementation_design_v0.1.md`
- Prior formal review: `docs/collab/chatgpt/reviews/2026-09-11_R09_B_TTT_v035_feature_config_optimizer_checkpoint_cpu_static_implementation_d0267a7_fa964ef.md`

## Verdict

`REQUEST_CHANGES(cosmos_framework/model/generator/mot/config_checkpoint_contract_test.py:282)`

## Current blockers

`1 HIGH` — Evidence-only. I found no new production/contract blocker. Most of the prior Evidence matrix is now closed, but two explicitly required authority witnesses are still not directly exercised: pending commit before `commit_success()`, and a real recovery receipt/recovery-lineage admission in isolation.

## Pair / scope verification

- Formal root `774d01d43c8a144747ee93014b2c11afe91498b3` resolves `cosmos-framework` exactly to reachable child `1231215fb066142251ce556ba59241ada54ef18a`.
- The child is three commits ahead of the prior reviewed child `fa964ef3974d5b622081cc1ded89b69d851b9eb5`; the remediation remains inside the previously approved six-file synthetic CPU/static scope and changes only test files.
- Root changes are bookkeeping/Gitlink state for this same Gate.
- MM/Kimi conclusions are not used as technical authority.

## Prior Evidence requirements now CLOSED

### Optimizer reordered / duplicated / missing membership — CLOSED

`test_restore_rejects_reordered_duplicate_and_missing_optimizer_membership_before_mutation()` now directly constructs:

- reversed canonical slow Parameter order;
- missing canonical membership;
- duplicated canonical membership.

Each is rejected by the exact live-optimizer object/order contract before slow mutation, retaining the prior production closure for object-bound optimizer membership.

### Pending native-forward and retry authority — CLOSED

`test_restore_rejects_real_native_forward_commit_and_retry_authorities_before_mutation()` now uses real production/typed paths:

- `scan -> prepare_native_inputs -> attach_native_preparation -> bind_native_forward`, then verifies restore rejects while a real `CanonicalNativeForwardCapability` is live;
- `retry_first_member_pre_backward()` then verifies restore rejects with a real pending retry capability.

This closes the prior native-forward and retry Evidence gaps.

### Suffix recovery capability / consumed suffix request — CLOSED

`test_restore_rejects_real_suffix_recovery_and_receipt_authorities_before_mutation()` now creates a real committed-prefix transaction, declares the typed source transient, derives a real suffix recovery capability, and verifies restore rejects while that capability is live. It then consumes the suffix recovery into exact suffix requests and verifies restore again rejects while those requests remain active.

This closes the direct suffix-capability and consumed-suffix-request Evidence gaps.

### Active-TTT production registration witness — CLOSED

`test_build_net_registers_only_active_ttt_owner()` now enters the actual `OmniMoTModel.build_net()` active-TTT registration branch with lightweight CPU/meta-safe mocks. It proves the resulting registered root has exactly `evidence_encoder` and `ttt_core` children, with no `local_history_runtime` and no legacy readout on the resulting network. This is the direct production-registration witness requested by the prior review.

## Remaining HIGH — two authority states are still not directly witnessed

### 1. Pending commit capability before `commit_success()` is still not tested

The current test name `test_restore_rejects_real_native_forward_commit_and_retry_authorities_before_mutation()` mentions commit, but its body never calls `prepare_commit()`. The separate existing test does call `prepare_commit(request, result)`, but immediately calls `commit_success(capability)` before attempting restore. Therefore that witness proves the committed fast-state frontier, not the pre-mutation pending `CanonicalProductionCommitCapability` state.

This matters because the frozen acceptance matrix explicitly distinguishes pending commit authority from the committed frontier. `validate_runtime_admission()` does enumerate `_commit_capabilities`, so I do not find a production omission; the missing piece is direct Evidence.

### 2. Real recovery receipt / recovery lineage is not directly tested

The suffix test creates a real `CanonicalSuffixRecovery`, which contains a real success receipt, but both restore attempts occur while adapter-level suffix capability/request authority is also still live. They therefore establish fail-closed behavior for `_suffix_recovery_capabilities` / `_suffix_recovery_requests`, not the explicit slow-restore `transaction`/recovery-receipt admission boundary.

The production/static restore contract separately rejects any supplied non-`None` transaction/recovery authority (`restore rejects an open canonical transaction or recovery receipt`). The existing open-transaction witness passes an ordinary transaction; it does not pass the real recovery object or its real success receipt created by `derive_suffix_recovery()`.

## Exact acceptance for closure

No production code change is required if current behavior is preserved. Within the already-approved test scope:

1. Create a real pending commit with `scan -> transaction.mark_backward_started(...) -> adapter.prepare_commit(...)`; before `commit_success()` or `abort_commit()`, call restore and prove pre-mutation rejection plus unchanged slow/runtime snapshots. The test should explicitly prove the typed commit capability is still live at the attempted restore boundary.
2. From a real `derive_suffix_recovery()` lineage, use a fresh/quiescent adapter/scheduler so no other pending adapter collection can mask the result, then pass the real recovery authority and/or its real `success_receipt` through the restore admission argument and prove pre-mutation rejection with unchanged slow/runtime snapshots. This must directly exercise the recovery-receipt/recovery-lineage boundary rather than relying on simultaneous suffix pending state.
3. Retain the newly added optimizer reorder/duplicate/missing, native-forward/retry, suffix capability/request, and `build_net()` registration witnesses, together with all previously accepted round-trip/late-defect/scan/frozen/frontier/open-transaction/config/selector/runtime-key/public-hard-stop coverage.

## Production/contract status

The prior production closures remain accepted on this pair:

- preflight-first synthetic restore compatibility/loadability staging;
- exact live optimizer Parameter object/order binding;
- active-TTT `32 -> 2048` projector and modality width ABI;
- unique active-TTT registered owner and exact adapter binding;
- versioned config identity / K=1 / slow-only payload boundaries;
- `validate_runtime_admission()` enumerates scan/native-forward/commit/retry/suffix/active-recovery collections and rejects explicit transaction/recovery authority;
- public real native-forward hard-stop remains unchanged.

## Evidence / execution scope

I treated the reported `53 passed` as supporting information, not as proof by itself. This is an incremental source/Evidence review of the exact formal pair. No real checkpoint/filesystem/DCP/remote I/O, public runtime activation, native forward/loss/backward, optimizer/scheduler step, CUDA/GPU, `torchrun`, sidecar, training, evaluation, inference, distributed execution, matched smoke or LIBERO4IN1 is authorized by this verdict.

## Authorized next action

Evidence-only remediation in the already-approved six-file synthetic CPU/static scope, followed by a new formal root/child pair for fresh incremental closure review.

Still not authorized: Gate closure, production code expansion outside the existing approved scope, real checkpoint backend/I/O, public runtime or hard-stop removal, real native forward/loss/backward, optimizer/scheduler stepping, CUDA/GPU, `torchrun`, sidecar/mid-episode resume, training, evaluation, inference, distributed execution, matched smoke or LIBERO4IN1.
