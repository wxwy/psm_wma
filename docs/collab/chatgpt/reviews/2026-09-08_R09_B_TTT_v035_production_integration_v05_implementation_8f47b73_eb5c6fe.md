# ChatGPT independent review — Local Memory v0.3.5 production integration v0.5 CPU/static remediation

**Date:** 2026-09-08  
**Verdict:** `REQUEST_CHANGES`

Formal reviewed pair:
- root implementation SHA: `8f47b73f58ec00c110ba47496f62110035ea244a`
- child/Gitlink SHA: `eb5c6fe254c0999285f22ec8f797e81b6f5db411`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-INTEGRATION-CPU-STATIC`
- requested closure literal: `APPROVE_TO_CLOSE_R09_B_TTT_V035_PRODUCTION_INTEGRATION_CPU_STATIC`

Fresh incremental review relative to prior implementation pair `77ccd13f81d0c17823e4b254a3407ee07b2a854a / 11c0fa4cbe6f2a04171b8a598ef0028638805d07`. The already-closed v0.4 transaction implementation remains CLOSED and was not technically re-reviewed.

Repository scope remains clean: child compare `11c0fa4..eb5c6fe` modifies only the approved `cosmos_framework/model/generator/mot/local_memory_segment_adapter.py` and adjacent `local_memory_segment_adapter_test.py`; no trainer/core/runtime/registry/model-forward/real-I/O/GPU/training wiring changed.

## Prior blocker status

### CLOSED — prior MEDIUM exact adapter ABI / scheduler-admission order

The remediation now exposes the frozen `scan(segment, *, identity, transaction)` surface, checks that the exact identity was scheduler-admitted and belongs to the transaction plan before sidecar read/scan, and keeps `validate_success(member_index, identity, actual_n_valid)` solely in the existing trainer seam after gather. The primary B=2,T=3 fixture creates/admit/binds the transaction before scan. This closes the prior ABI/order mismatch.

### PARTIALLY CLOSED — prior MEDIUM Evidence matrix

The remediation adds meaningful Evidence:
- B=2,T=3 mixed S0/PAD now uses NaN sentinels for all invalid evidence bytes and finite values only on the compact valid evidence row;
- GradScaler skip is driven through `ImaginaireTrainer._run_local_memory_segment_backward` before asserting adapter sidecar zero-write;
- the request reports readable same-pair CPU results: adapter suite `5 passed`, trainer seam suite `12 passed`, plus target `py_compile` and child/root diff-check PASS.

Those close the invalid-byte, real GradScaler chain and readable trainer-suite sub-gaps, but not the full frozen v0.5 Evidence matrix below.

## Current blockers

### 1. HIGH — transaction/identity pending guard is not bound to the exact `SegmentScanResult`; an unbackwarded fabricated or stale state can still be committed

**Locations:**
- `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_integration_implementation_design_v0.5.md:26-43`
- `cosmos_framework/model/generator/mot/local_memory_segment_adapter.py:50-79`
- `cosmos_framework/model/generator/mot/local_memory_segment.py:184-226`

**Root cause:** v0.5 freezes one causal chain: one admitted segment scan produces `SegmentScanResult`; gathered locals from that result feed the unique trainer seam; the same member's successful backward/`transaction.successful_backward()` then authorizes detach-copy of **that scan's `state_out`**.

The implementation stores `_pending_scan = (identity, transaction)` only. `commit(identity, result, transaction=...)` checks that tuple and the transaction's last completed identity, but never checks that `result` is the exact object/result produced by the pending scan. `LocalMemoryTransaction.successful_backward()` also does not close a successfully completed transaction.

Therefore the following invalid sequences are accepted by the current guard:
1. `result_a = scan(...)`; run the trainer seam to successful transaction commit using `result_a.locals`; then call `adapter.commit(identity, fabricated_result, transaction=transaction)` where `fabricated_result.state_out` never participated in the backward path. The guard passes because identity/transaction match.
2. Call `scan(...)` twice with the same identity/transaction before adapter commit. The second call overwrites `_pending_scan` with the same tuple, so either old or new `SegmentScanResult` can be passed to commit after one successful trainer backward; the guard cannot distinguish which result produced the loss.

This recreates a fast-state mutation path that is transaction-success-gated only at identity level, not at the actual scan/result level, and can carry a `state_out` that is not causally tied to the successful trainer transaction.

**Violated contract:** v0.5 §3/§4 fixed scan→gather→trainer→successful transaction→detach-copy sequence; sidecar carry must be the state from the exact scan whose consumer path was successfully backwarded, with no second or stale result authority.

**Acceptance:** within the existing approved adapter/test surface, make the pending operation one-shot and exact-result-bound without moving `validate_success(actual_n_valid)` out of the trainer seam:
1. reject a second scan while an uncommitted pending scan exists for that adapter/transaction;
2. bind the exact returned `SegmentScanResult` (or an equally immutable one-shot token uniquely tied to that result) to the pending scan;
3. `commit()` must reject any fabricated/stale/different result even when identity and transaction are otherwise valid;
4. exact pending result + matching successful transaction may commit once; duplicate commit remains fail-closed;
5. terminal/retry/GradScaler paths must clear or render the pending operation permanently non-committable, preserving prior carry.
Add adjacent negative fixtures for fabricated-result commit, repeated scan before commit, and duplicate commit.

### 2. MEDIUM — remaining mandatory v0.5 contract→behavior→Evidence is still incomplete

**Locations:**
- `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_integration_implementation_design_v0.5.md:50-61`
- `cosmos_framework/model/generator/mot/local_memory_segment_adapter_test.py:1-190`
- `cosmos_framework/trainer/trainer_local_memory_integration_test.py`

The new NaN sentinel and real GradScaler path are correct, and the request now reports adapter=`5 passed` and trainer seam=`12 passed`. Remaining mandatory Evidence is still absent:
- no synthetic consumer-spy witness proves exactly one call over the valid gathered rows, S0 receives `None`, PAD produces zero call, and no `state/dt/age` feature is constructed/passed/read at this integration seam;
- terminal failure adapter coverage still directly calls `transaction.terminal_failure(...)` rather than driving an actual trainer identity/numerical/backward failure and then proving sidecar zero-write/prior-carry retention end-to-end;
- disabled parity remains absent: no fixture proves that when the adapter is not constructed, payload/native loss/gradients/output match the legacy disabled path and old `ProductionLocalMemoryRuntime` / `TTTLifecycle` / C6 routes are uncalled;
- after closing HIGH #1, Evidence must also prove exact pending-result binding, repeated-scan rejection and duplicate/fabricated commit rejection.

**Acceptance:** add only adjacent CPU/static fixtures to close those exact gaps, preserve the current NaN sentinel, real GradScaler and trainer `12 passed` evidence, and rerun the adapter/segment and trainer seam suites with readable PASS plus specified `py_compile` and child/root diff-check.

## Non-blocking confirmations

- Prior ABI/order MEDIUM is CLOSED.
- Prior transaction-authorized sidecar-write HIGH from `2ce4bef/8bf00b0` remains closed at the identity/transaction level; the current HIGH is the newly identified missing exact-result binding within that boundary.
- Exact child file scope is clean.
- `SegmentScanResult` remains frozen and graph-bearing through scan; sidecar stores detach-cloned fast state.
- Canonical masked encoded scan and `SegmentBatch.gather_consumers()` remain in use; opaque payloads are not reconstructed.
- No model-forward wiring, registry/default/config, production runtime/lifecycle/C6 wiring, real checkpoint/data/cache I/O, runtime persistence/resume, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1 authority is introduced.

No v0.5 CPU/static closure is authorized by this verdict. A remediation implementation forms a new formal pair and requires fresh review.
