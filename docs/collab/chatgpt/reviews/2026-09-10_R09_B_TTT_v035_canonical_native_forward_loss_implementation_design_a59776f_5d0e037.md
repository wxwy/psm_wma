# ChatGPT Independent Review — R09-B / TTT v0.3.5 Canonical Native Forward/Loss Implementation Design v0.2

**Date:** 2026-09-10  
**Role:** Independent Design / Code / Evidence / Gate Reviewer  
**Gate:** `G0-R09-B-TTT-V035-CANONICAL-NATIVE-FORWARD-LOSS-IMPLEMENTATION-DESIGN`  
**Formal root design SHA:** `a59776f555d471f1ad9d8b92a2ffa536490632c8`  
**Formal child/Gitlink SHA:** `5d0e037ced559c07081fd4880c633dc03f325efe`  
**Previous same-Gate formal pair:** `6f75365a7a865f42540e987024165faceb981354 / 5d0e037ced559c07081fd4880c633dc03f325efe`  
**Approved source-audit authority:** `d75a3371f48c2b6538e093f5fd693f843b72e1d6 / 5d0e037ced559c07081fd4880c633dc03f325efe`  
**Artifact:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_forward_loss_implementation_design_v0.2.md`  
**Verdict:** `REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_forward_loss_implementation_design_v0.2.md:33)`

## 1. Repository-truth lock

- Latest `origin/V2` observed at review start is request/bookkeeping HEAD `a01523f55b592a0875bfb0e9f7c346e2c48b9dac`; it is not the formal design target.
- Latest canonical request declares exactly formal pair `a59776f555d471f1ad9d8b92a2ffa536490632c8 / 5d0e037ced559c07081fd4880c633dc03f325efe`, Gate `G0-R09-B-TTT-V035-CANONICAL-NATIVE-FORWARD-LOSS-IMPLEMENTATION-DESIGN`, and requests only `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_NATIVE_FORWARD_LOSS_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Formal root tree `b6336240d73c2a93e43869ab9da036b42da32cec` stores `cosmos-framework` exactly at Gitlink `5d0e037ced559c07081fd4880c633dc03f325efe`.
- Child is unchanged from the previous Design review. Root compare `6f75365... -> a59776f...` is docs/review/Inbox/SESSION/TODO remediation only and adds v0.2; no child implementation is part of this Gate.
- No GitHub workflow/status is attached to child `5d0e037...`; this is a docs-only design review and the verdict is source/contract based.

## 2. Previous blocker lifecycle

### HIGH-1 CLOSED — cardinality-preserving native population -> consumer algebra

v0.2 now freezes the missing algebra explicitly. For each native modality population `I_m` with `K_m=|I_m|` and canonical consumer count `N=actual_n_valid`, it defines:

`c[j,m] = (N / K_m) * sum(z_i for owner(i)==j)`

so that:

`mean_j c[j,m] == mean_i z_i`.

This correctly preserves the ordinary native modality means even when multi-vision-item, dense action, or dense sound cardinalities differ from `N`. The existing modality weights and sample-level scale remain outside the per-modality cardinality compensation, while LBL stays separate as auxiliary loss.

The absent/no-valid case is also sufficiently frozen for this Design Gate: it contributes only graph-connected zero terms and must not create fake native items, consumer identities, or denominator entries; the legacy wrapper is required to preserve its public return contract. CPU/static acceptance now explicitly includes unequal `K_m/N`, absent modality, wrapper compatibility, and the algebraic identity.

The prior working-copy ownership watchpoint is also materially closed: v0.2 forbids shallow-dict immutability claims and requires independent working containers/storage for every native-mutated list/tensor/plan/metadata field, with direct non-alias witnesses.

### HIGH-2 PARTIALLY CLOSED — old lifecycle APIs removed, but pre-backward commit-capability minting leaks authority on failure

v0.2 correctly removes the nonexistent/old `transaction.successful_backward(...)` and generic `commit(...)` calls. It now names the current canonical objects and methods: `CanonicalBatchWindowTransaction.mark_backward_started()`, one `CanonicalProductionCommitCapability`, and `CanonicalProductionAdapter.commit_success()`; attempt-1 continues only through `consume_retry()` and no second admission/transition is allowed.

The unsupported enabled-GradScaler / real-optimizer policy is also clarified: this CPU/static route must reject before scan/backward/commit and before optimizer callbacks, leaving canonical committed state untouched.

However one remaining transaction-capability defect prevents implementation approval.

## 3. Current blocker

### HIGH — `prepare_commit()` is minted before backward, but current adapter has no failure disposal for that capability

**Direct blocking location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_forward_loss_implementation_design_v0.2.md:33`

v0.2 freezes the success sequence as:

```text
adapter.scan(request)
capability = adapter.prepare_commit(request, scan_result)
transaction.mark_backward_started(member_index)
grad_scaler.scale(L_member).backward()
adapter.commit_success(capability)
```

The problem is not naming anymore; it is current object lifecycle.

At child `5d0e037...`, `CanonicalProductionAdapter.prepare_commit()` is stateful. After validating the scan result and obtaining a `PreparedCanonicalReconcile`, it creates `CanonicalProductionCommitCapability` and immediately records `id(capability)` in `self._commit_capabilities`.

`abort_scan()` only removes the request/result from `_scan_requests` and `_scan_results`; it does not remove any already-minted `_commit_capabilities`. There is no current `abort_commit()` / discard-prepared-capability API.

Therefore a backward exception after `prepare_commit()` leaves an orphaned one-shot commit authority in the adapter. The same design also does not freeze the exact failure disposition after `transaction.mark_backward_started()` if backward raises: the scan must be disposed, controlled slow gradients must be cleared, and the transaction must become terminal without fast-state/scheduler reconcile, but v0.2 currently specifies only the success path and the pre-scan unsupported-scaler rejection.

This violates the standing failure contract: failure/stale/unsupported paths must not leave a reusable or leaked capability, and success-only state/scheduler reconcile must occur only after successful backward.

**Source facts**

- `prepare_commit()` adds the new capability to `_commit_capabilities` before returning.
- `abort_scan()` removes only `_scan_requests` and `_scan_results`.
- `commit_success()` is the only current path that consumes `_commit_capabilities`.
- `CanonicalBatchWindowTransaction` exposes `mark_backward_started()`, `validate_reconcile()`, `mark_reconciled()` and `terminalize()`; no old `successful_backward()` authority exists.

**Exact closure condition**

Freeze one source-consistent failure-safe lifecycle before implementation. The minimal/current-API option is:

```text
adapter.scan(request)
transaction.mark_backward_started(member_index)
try:
    grad_scaler.scale(L_member).backward()      # once, no /GA
except:
    clear controlled slow grads
    adapter.abort_scan(request, scan_result)
    transaction.terminalize(member_index, exact_failure_code)
    raise
commit_capability = adapter.prepare_commit(request, scan_result)  # exactly once, only after successful backward
adapter.commit_success(commit_capability)
```

If `prepare_commit()` or another post-backward pre-commit validation fails, the design must likewise freeze exact `abort_scan + terminalize + slow-grad-clear` disposition with no frontier/scheduler commit.

Alternatively, if the design insists on pre-backward `prepare_commit()`, it must explicitly authorize and specify a typed exact discard/abort operation for `CanonicalProductionCommitCapability`, including one-shot identity and evidence proving `_commit_capabilities`, scan bookkeeping, frontier, scheduler and transaction cannot retain reusable success authority after failure. Do not leave this to implementation inference.

The capability schema must be aligned with the chosen timing: a pre-forward/native capability cannot claim to contain a commit capability that is intentionally minted only after successful backward unless a separate post-backward typed capability is defined.

Required CPU/static witnesses:

1. backward exception after `mark_backward_started()` leaves no scan/commit capability and no fast-state/scheduler reconcile;
2. `prepare_commit()` failure after successful backward has the same terminal no-commit disposition;
3. successful attempt-0 and consumed attempt-1 each mint exactly one commit capability after successful backward and `commit_success()` consumes it exactly once;
4. enabled scaler / real optimizer rejection remains before scan and before transaction mutation, as v0.2 already requires.

## 4. Non-blocking / retained design authority

- Seven-file CPU/static whitelist remains acceptable.
- No packer/config/optimizer/dataset/dataloader/collate/runtime-sidecar changes are authorized.
- Preparation parity-or-fail-closed, per-camera/resolution/VAE raw-state rules, multi-item/dense source identity, memory-hook order, S0/PAD semantics, old canonical/active supersession, and exact attempt-1 retry lineage remain valid and should not be redesigned.
- `N/K_m` native-population algebra and field-wise non-alias ownership are CLOSED by this revision.
- This review authorizes no real I/O, CUDA/GPU, torchrun, native forward/loss/backward execution, optimizer step, training/evaluation/inference, runtime sidecar, distributed execution, or LIBERO4IN1.

## 5. Blocker lifecycle / authorized next action

Current blockers: **1 HIGH**.

Authorized next action: docs-only remediation of the canonical native forward/loss implementation design on a new formal root SHA, retaining the explicit child SHA if unchanged. Fix only the commit-capability timing/failure-disposal contract; do not reopen the already-closed loss algebra or source-audit decisions unless required by the failure-safe lifecycle.

No CPU/static implementation Gate is authorized yet.

## 6. Exact verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_forward_loss_implementation_design_v0.2.md:33)`
