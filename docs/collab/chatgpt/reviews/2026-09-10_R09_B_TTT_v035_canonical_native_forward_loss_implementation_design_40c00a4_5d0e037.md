# ChatGPT Independent Review — R09-B / TTT v0.3.5 Canonical Native Forward/Loss Implementation Design v0.3

**Date:** 2026-09-10  
**Role:** Independent Design / Code / Evidence / Gate Reviewer  
**Gate:** `G0-R09-B-TTT-V035-CANONICAL-NATIVE-FORWARD-LOSS-IMPLEMENTATION-DESIGN`  
**Formal root design SHA:** `40c00a45baedc7e1cd3fded051486f8f8734af31`  
**Formal child/Gitlink SHA:** `5d0e037ced559c07081fd4880c633dc03f325efe`  
**Previous same-Gate formal pair:** `a59776f555d471f1ad9d8b92a2ffa536490632c8 / 5d0e037ced559c07081fd4880c633dc03f325efe`  
**Artifact:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_forward_loss_implementation_design_v0.3.md`  
**Verdict:** `REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_forward_loss_implementation_design_v0.3.md:25)`

## 1. Repository-truth lock

- Latest `origin/V2` observed at review start is request/bookkeeping HEAD `38e2ba1a42c63e0dc102c3a424692370fbe2efbf`; it is not the formal design target.
- Latest canonical request declares exactly `40c00a45baedc7e1cd3fded051486f8f8734af31 / 5d0e037ced559c07081fd4880c633dc03f325efe`, the same Design Gate, and requests only `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_NATIVE_FORWARD_LOSS_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Formal root tree `94975e4770eb8666e8a9248d005da434cc15eacd` stores `cosmos-framework` exactly at Gitlink `5d0e037ced559c07081fd4880c633dc03f325efe`.
- Child is unchanged. This remediation changes only the docs-only failure lifecycle and inherits the already-closed v0.2 `N/K_m` loss algebra, absent/no-valid graph semantics, field-wise non-alias ownership, whitelist, parity/hook/source-map rules and retry lineage.

## 2. Previous blocker lifecycle

### CLOSED — native population / consumer loss algebra

The v0.2 cardinality-preserving transform remains valid and is not reopened. Multi-item vision and dense action/sound native populations retain their native mean through the explicit `N/K_m` transform; sample-level scaling and LBL placement remain frozen; absent/no-valid modalities retain graph-zero semantics without fake consumer identities.

### PARTIALLY CLOSED — commit-capability failure lifecycle

v0.3 fixes the main timing defect from v0.2:

- no `CanonicalProductionCommitCapability` is minted before backward;
- backward exception after `mark_backward_started()` clears controlled slow grads, aborts the exact scan and terminalizes the transaction;
- `prepare_commit()` is now post-backward only;
- enabled GradScaler / real optimizer remains rejected before scan and transaction mutation;
- attempt-1 still comes only from exact `consume_retry()` lineage.

One failure branch still leaks the stateful commit capability.

## 3. Current blocker

### HIGH — `commit_success()` pre-mutation failure leaves the already-minted commit capability registered

**Direct blocking location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_forward_loss_implementation_design_v0.3.md:25`

v0.3 freezes:

```text
commit_capability = adapter.prepare_commit(request, scan_result)
adapter.commit_success(commit_capability)
except Exception:
    clear controlled slow grads
    adapter.abort_scan(request, scan_result)
    transaction.terminalize(...)
```

At current child `5d0e037...`, `prepare_commit()` is stateful: once it succeeds, it inserts `id(capability)` into `adapter._commit_capabilities` before returning. `abort_scan()` removes only `_scan_requests` and `_scan_results`; it does not remove `_commit_capabilities`. `commit_success()` is currently the only consumer that removes that capability id, and it performs several pre-mutation validations before frontier/scheduler/transaction mutation.

Therefore, if `commit_success()` raises in one of those intended pre-mutation validation points, v0.3's catch block aborts the scan and terminalizes the transaction but leaves the exact one-shot commit capability registered. The capability is stale after scan abort, but it is still leaked authority/state, contradicting the required failure-safe lifecycle and the previous review's exact closure requirement that failure leave no scan/commit capability.

The text explicitly says CPU/static should exercise a pre-mutation `commit_success()` failure, so this is not merely an unreachable defensive branch; the design currently asks implementation to test a path it has no disposal API for.

**Source facts:**

- `CanonicalProductionAdapter.prepare_commit()` creates `CanonicalProductionCommitCapability` and immediately adds `id(capability)` to `_commit_capabilities`.
- `abort_scan()` removes only the exact scan request/result bookkeeping.
- `commit_success()` checks registered capability identity, scan-result identity, scheduler ownership, candidate dtype, prepared scheduler reconcile and transaction reconcile before irreversible mutation, and only removes `_commit_capabilities` on successful completion.

**Exact closure condition:** freeze exactly one source-consistent disposition for an already-minted capability when `commit_success()` fails before irreversible mutation. Acceptable approaches include:

1. add an exact typed `abort_commit` / `discard_commit_capability` operation that validates the exact capability/request/result identity, consumes `_commit_capabilities` once, then performs `abort_scan + terminalize + slow-grad-clear`; or
2. redesign the adapter lifecycle so every fallible commit validation occurs before a capability is registered, and prove that once registration occurs `commit_success()` cannot fail before/within the supported mutation sequence.

Do not rely on `abort_scan()` alone because current source does not clear commit-capability registry state.

Required CPU/static witnesses must include:

- backward exception: no scan/commit capability and zero frontier/scheduler reconcile;
- `prepare_commit()` exception: same no-capability disposition;
- `commit_success()` pre-mutation validation failure after successful `prepare_commit()`: exact capability is disposed, scan is aborted, transaction terminalized, slow grads cleared, zero frontier/scheduler reconcile;
- successful attempt-0 and consumed attempt-1: exactly one post-backward capability is minted and consumed once;
- enabled scaler/real optimizer rejection remains before scan.

## 4. Retained design authority / scope

No other blocker is opened. v0.2 `N/K_m` algebra, graph-zero semantics, field-wise non-alias working ownership, seven-file CPU/static whitelist, preparation parity-or-fail-closed, hook order, S0/PAD semantics, old canonical/active supersession, and exact attempt-1 retry lineage remain valid.

Current blockers: **1 HIGH**.

Authorized next action is docs-only remediation on a new formal root SHA. No child code, packer/model/trainer/config/optimizer implementation, real data/cache/checkpoint I/O, CUDA/GPU, torchrun, native forward/loss/backward execution, optimizer step, training/evaluation/inference, runtime sidecar, distributed execution, or LIBERO4IN1 is authorized.
