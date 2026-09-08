# ChatGPT independent review — Local Memory v0.3.5 production integration v0.5 CPU/static remediation

**Date:** 2026-09-08  
**Verdict:** `REQUEST_CHANGES`

Formal reviewed pair:
- root implementation SHA: `77ccd13f81d0c17823e4b254a3407ee07b2a854a`
- child/Gitlink SHA: `11c0fa4cbe6f2a04171b8a598ef0028638805d07`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-INTEGRATION-CPU-STATIC`
- requested closure literal: `APPROVE_TO_CLOSE_R09_B_TTT_V035_PRODUCTION_INTEGRATION_CPU_STATIC`
- request/bookkeeping SHA observed at review start: `6a22f10dbc4b4e7f1b283e632e015abe7779f6af`

Fresh incremental review relative to prior implementation pair `2ce4bef4300e432131ac62aea374b45a9cbe1d55 / 8bf00b05803fcf901dc9b09f3208c4fff811a245`. The already-closed v0.4 transaction implementation remains CLOSED and was not technically re-reviewed. Repository scope remains clean: child delta relative to `8bf00b0` modifies only the approved `local_memory_segment_adapter.py` and adjacent `local_memory_segment_adapter_test.py`; no trainer/core/runtime/registry/model-forward/real-I/O/GPU/training wiring changed.

## Prior blocker status

### CLOSED — prior HIGH sidecar mutation was not transaction-authorized/fail-closed

The remediation materially closes the prior HIGH. `CanonicalLocalMemorySegmentAdapter.commit(..., transaction=...)` now rejects terminal-failed, retry/slow-cleared and GradScaler-skipped transactions, requires a successful completed member, and requires the last completed member to equal the exact `SegmentIdentity` being carried. The main carry fixture now performs the real trainer seam before adapter commit; a pre-transaction call without `transaction` fails; terminal failure cannot replace the previously committed carry; and terminal success deletes carry only after the trainer transaction succeeds. This restores trainer/`LocalMemoryTransaction.successful_backward()` as the sidecar-write prerequisite rather than allowing a direct scan→commit authority path.

## Current blockers

### 1. MEDIUM — implementation still violates the frozen adapter ABI/admission order

**Locations:**
- `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_integration_implementation_design_v0.5.md:26-43`
- `cosmos_framework/model/generator/mot/local_memory_segment_adapter.py:53-69`
- `cosmos_framework/model/generator/mot/local_memory_segment_adapter_test.py:46-82`

**Root cause:** the approved v0.5 ABI is explicitly `CanonicalLocalMemorySegmentAdapter.scan(segment, *, identity: SegmentIdentity, transaction: LocalMemoryTransaction)` and freezes the order `scheduler-admitted exact SegmentIdentity -> sidecar read -> masked scan/gather -> trainer seam`. Formal implementation still exposes `scan(segment, *, identity)` only. Its primary fixture calls `adapter.scan(...)` before the scheduler and transaction are even created, then performs `scheduler.admit(...)` afterward.

The post-scan commit guard is now correct, but that does not make the scan ABI equivalent: the adapter can still read previous sidecar state and build a graph for an identity that has not yet been bound to the same admitted/planned transaction context required by the approved design. This is an exact implementation-contract mismatch, even though it does not currently create a second sidecar mutation path.

**Acceptance:** preserve the already-correct post-success commit guard, and make the implementation/test call surface match the approved ABI/order exactly: create/admit the canonical identity and transaction before scan; pass that transaction into `scan()` as frozen by v0.5; do not move `validate_success(actual_n_valid)` before gather or duplicate trainer transaction authority. No new path/symbol or private chronology is authorized.

### 2. MEDIUM — mandatory v0.5 contract→behavior→Evidence matrix remains incomplete

**Locations:**
- `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_integration_implementation_design_v0.5.md:50-61`
- `cosmos_framework/model/generator/mot/local_memory_segment_adapter_test.py:23-159`
- `cosmos_framework/trainer/trainer_local_memory_integration_test.py`

**Root cause:** the remediation improves Evidence substantially: the adapter fixture is now `B=2,T=3`, uses the actual trainer seam before successful carry, checks source mismatch, GradScaler no-write, terminal-failure prior-carry retention and terminal-success deletion. However the frozen acceptance is broader than the reported `5 passed` adapter file:
- the B=2 mixed-mask fixture uses ordinary finite random values in invalid/PAD positions; it does not provide the invalid-byte/NaN-sentinel witness required to prove invalid-first masked scan at the adapter boundary;
- there is no consumer-spy witness proving exactly one call over valid gathered rows, S0 `None`, PAD zero-call and no `state/dt/age` construction/read at this integration seam;
- GradScaler and terminal failure adapter tests directly mutate `LocalMemoryTransaction` state rather than driving the real trainer failure/skip path and then proving adapter zero-write, so the failure→transaction→sidecar chain is not established end-to-end;
- disabled parity remains absent;
- the current request reports only `local_memory_segment_adapter_test.py = 5 passed`, target `py_compile`, and diff-check; it does not report a readable same-pair PASS for the existing trainer seam suite that owns normal/recovery scaling, backward exception, retry/exhaustion and no-second-GA behavior.

**Acceptance:** after the ABI fix above, extend only approved synthetic fixtures to close the remaining v0.5 matrix: invalid-byte sentinel at adapter scan, consumer-spy valid-row/S0/PAD semantics and disabled feature absence, real trainer failure/GradScaler→adapter no-write integration, disabled parity, plus a readable PASS for both the adapter/segment target suite and existing trainer seam suite. Preserve the already-closed v0.4 transaction semantics and the current terminal/carry guards.

## Non-blocking confirmations

- The prior HIGH transaction-authorized sidecar-write defect is CLOSED.
- Exact child file scope is clean: only the two approved adapter files changed relative to `8bf00b0`.
- `SegmentScanResult` remains frozen and graph-bearing through scan; sidecar stores detach-cloned fast state.
- Canonical masked encoded scan and `SegmentBatch.gather_consumers()` remain in use; opaque payload objects are not reconstructed.
- Stable-slot carry verifies canonical episode/source/cursor continuity and does not generate cursor.
- No model-forward wiring, registry/default/config, production runtime/lifecycle/C6 wiring, real checkpoint/data/cache I/O, runtime persistence/resume, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1 authority is introduced.

No v0.5 CPU/static closure is authorized by this verdict. A remediation implementation forms a new formal pair and requires fresh review.
