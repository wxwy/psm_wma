# ChatGPT independent review — Local Memory v0.3.5 production integration v0.5 CPU/static remediation

**Date:** 2026-09-08  
**Verdict:** `REQUEST_CHANGES`

Formal reviewed pair:
- root implementation SHA: `f5f3d7b2591a55d6bf0e0bda22f4f3f4e17da0d3`
- child/Gitlink SHA: `92d1638143f0ef334f1a93c251fcf5140d3296bc`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-INTEGRATION-CPU-STATIC`
- requested closure literal: `APPROVE_TO_CLOSE_R09_B_TTT_V035_PRODUCTION_INTEGRATION_CPU_STATIC`

Fresh incremental review relative to formal pair `8f47b73f58ec00c110ba47496f62110035ea244a / eb5c6fe254c0999285f22ec8f797e81b6f5db411`. Prior verdict is not inherited. The already-closed v0.4 transaction implementation and already-closed v0.5 ABI/admission-order remediation were not technically re-reviewed.

Repository scope is clean. Root formal commit changes only the child Gitlink. Child compare `eb5c6fe..92d1638` modifies only approved `local_memory_segment_adapter.py` and adjacent `local_memory_segment_adapter_test.py`; no trainer/core/runtime/registry/model-forward/real-I/O/GPU/training wiring changes.

## Prior blocker status

### CLOSED — exact pending scan result was not bound to commit authorization

The remediation accurately closes the prior HIGH. `CanonicalLocalMemorySegmentAdapter._pending_scan` now stores `(SegmentIdentity, LocalMemoryTransaction, SegmentScanResult)`. `commit()` requires exact identity equality, transaction object identity, and `pending_result is result` before sidecar mutation. The adjacent fixture creates two results from repeated scans under the same identity/transaction and verifies that the stale first result is rejected while the current exact result succeeds. A fabricated or stale result can therefore no longer borrow a successful transaction's authorization merely by sharing identity/transaction metadata.

## Current blocker

### MEDIUM — tests/Evidence-only — mandatory v0.5 adapter integration Evidence remains incomplete

**Locations:**
- `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_integration_implementation_design_v0.5.md:50-61`
- `cosmos_framework/model/generator/mot/local_memory_segment_adapter_test.py:1-190`

**Root cause:** this formal child is a narrow exact-result-binding remediation. Relative to `eb5c6fe`, its test delta adds only the stale-result negative witness. The prior remaining mandatory Evidence gaps are therefore unchanged:
1. no consumer-spy witness proving exactly one invocation over valid gathered rows, S0 receives `None`, PAD receives zero calls, and no `state/dt/age` feature is constructed/passed/read at the adapter integration seam;
2. no real trainer terminal-failure/backward-exception path followed by an adapter commit attempt proving sidecar zero-write while prior committed carry is retained — the existing terminal-failure adapter fixture directly mutates transaction terminal state rather than driving the unique trainer seam;
3. no disabled-parity fixture proving that when the adapter is not constructed, payload/native loss/gradients/output are equivalent to the legacy-disabled path and the old `ProductionLocalMemoryRuntime`/`TTTLifecycle`/C6 routes are uncalled.

The request reports adapter pytest=`5 passed`, target `py_compile`, and child/root diff-check PASS. Those results do not establish the missing mandatory contract→behavior→Evidence witnesses above.

**Acceptance:** tests/Evidence-only remediation within the already-approved test surface. Add adjacent CPU/static fixtures for the three missing witnesses above. Preserve production code unless a new fixture exposes a real semantic defect. Re-run the adapter/segment target suite and the existing trainer seam suite with readable PASS results, plus target `py_compile` and child/root `git diff --check`.

## Non-blocking confirmations

- Previous v0.5 ABI/admission-order mismatch remains CLOSED: `scan(segment, *, identity, transaction)` requires scheduler admission and plan membership before scan.
- Invalid evidence bytes are NaN-sentinel covered at the adapter boundary.
- GradScaler skip is driven through the real trainer seam before adapter zero-write is asserted.
- Exact pending-result identity/transaction/result-object binding is now fail-closed.
- No model-forward wiring, registry/default/config, production runtime/lifecycle/C6 wiring, real checkpoint/data/cache I/O, runtime persistence/resume, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1 authority is introduced.

No v0.5 CPU/static closure is authorized by this verdict. A remediation implementation creates a new formal pair and requires fresh independent review.
