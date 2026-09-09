# ChatGPT 独立 Production Segment Integration CPU/static implementation review

Formal reviewed pair:
- root implementation SHA: `cf328e8ca1f5a50e563a09db89c5e803f986119b`
- child/Gitlink SHA: `7f461eae69015b467c846923c1e92b7096f9f527`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-SEGMENT-INTEGRATION-CPU-STATIC-IMPLEMENTATION`
- approved design authority: `ef8adca6082e41c98dd75cd0c341c9bc91dca454` / `556e278946b506195a57d0798b2b1a2e8b5eb9cc`, v0.3/v0.4
- request/bookkeeping HEAD observed: `552f3a9c1c8f2a0c91a98da6095ba1b44d5ed09f`

Verdict: `REQUEST_CHANGES`

## Incremental scope

Fresh implementation review relative to the approved design pair. Root formal change advances the Gitlink and bookkeeping only. Child is one commit ahead and changes only the six files inside the approved high-level whitelist: `canonical_segment_runtime.py`/test, new `production_segment_bridge.py`/test, `trainer/__init__.py`, and adjacent trainer test.

The request reports owner=`11 passed`, bridge=`2 passed`, trainer=`14 passed`, target `py_compile` PASS and child/root `git diff --check` PASS. The canonical wiring pytest was not reported as PASS because the foreground tool window truncated its completion. These execution claims are request Evidence and were not independently rerun here.

## Correct portions

- `transaction.plan` is now used by the new pure backward seam; continuation/retry no longer accept an external plan argument.
- `SLOW_RESOLUTION_PENDING` and owner-retained exact `CompletedWindowCapability` exist, with reconstructed/double capability rejection and pending snapshot/admission guards.
- post-window scaler skip preserves the already committed fast frontier and performs an actual Local `.grad` clear.
- terminal/retry owner abort paths now perform real Local `.grad` clearing before the one transaction disposition and pending discard.
- retained retry uses the already-admitted attempt-1 transaction without duplicate admission.

These points are not enough to close the Gate because the submitted implementation violates the frozen bridge ABI and regresses a previously closed trainer path.

## Current blockers

1. **HIGH — gathered-valid count authority is incorrectly delegated to the native callback instead of being derived from `forward.payloads`.**
   - implementation: `cosmos_framework/model/generator/mot/production_segment_bridge.py:13-17,46-50,103-114`
   - violated contract: production-segment integration v0.2/v0.3 ABI — `NativeBatchResult` contains only `primary_consumer_mean` and `auxiliary_loss`; `actual_n_valid` is fixed by the bridge as `len(forward.payloads)` and checked against `transaction.plan.planned_n_valid[member_index]`.

   The implementation adds `actual_n_valid` to `NativeBatchResult` and passes that caller-controlled value into `_run_local_memory_bridge_backward()` and `transaction.successful_backward()`. It never proves `result.actual_n_valid == len(forward.payloads)` and does not reject a plan/gather cardinality mismatch before the native callback.

   A one-consumer gathered batch can therefore be paired with a plan count of two while the callback reports `actual_n_valid=2`; transaction validation then passes, the objective uses the false count, and scheduler exposure commits two consumers although only one native consumer was actually processed. This corrupts both GA weighting authority and cumulative valid-consumer exposure.

   **Acceptance:** remove callback ownership of the count. `NativeBatchResult` must contain only the two frozen loss tensors. Immediately after `owner.prepare(segment)`, derive `actual_n_valid = len(forward.payloads)` inside the bridge and fail closed before `native_batch(...)` unless it equals `transaction.plan.planned_n_valid[member_index]`. Pass only this bridge-derived count to the pure backward seam and `successful_backward()`. Add a negative fixture where gathered cardinality differs from the plan and prove zero callback, zero backward, zero scheduler/sidecar/grad mutation.

2. **HIGH — this Gate modifies the previously closed `_run_canonical_segment_backward()` path and regresses its terminal-failure semantics.**
   - implementation: `cosmos_framework/trainer/__init__.py:641-674`
   - previous closed source: child `556e278...`, `_run_canonical_segment_backward()` delegated to `_run_local_memory_segment_backward(...)` with `wiring.clear_local_slow_grads`.
   - violated scope: v0.3 §4 / v0.4 inherited whitelist permits the new pure-backward/post-window bridge seams; it does not authorize changing the already-closed canonical marker/wiring transaction path.

   At the approved base, `_run_canonical_segment_backward()` delegated failure handling to `_run_local_memory_segment_backward()`, which clears Local slow grads and terminalizes the transaction on identity/numerical/backward failure. The submitted version reroutes this old path through `_run_local_memory_bridge_backward()`. When that pure seam returns `terminal_code`, `_run_canonical_segment_backward()` only raises `RuntimeError` and performs no `clear_local_slow_grads()` and no `transaction.terminal_failure(...)`.

   Thus a numerical or backward failure on the previously closed canonical wiring path can now leave partial/pre-existing Local grads live and the transaction open, instead of preserving the already-approved fail-closed behavior. This is both an out-of-scope modification and a semantic regression.

   **Acceptance:** restore `_run_canonical_segment_backward()` to the behavior of the approved base `556e278...` (or an exactly equivalent implementation) and keep `_run_local_memory_bridge_backward()` exclusive to the new production-segment bridge path. Add regression Evidence for canonical identity/numerical/backward failures proving the pre-existing clear/terminal semantics are unchanged. The dedicated `trainer_canonical_segment_wiring_test.py` suite must complete successfully and be reported as PASS.

3. **HIGH — the required Local-disabled/no-Local bridge path is absent.**
   - implementation: `cosmos_framework/model/generator/mot/production_segment_bridge.py:1-119`
   - Evidence: `cosmos_framework/model/generator/mot/production_segment_bridge_test.py:1-50`
   - violated contract: v0.3 §1 and §4 item 6, inherited unchanged by v0.4.

   The frozen design requires a feature-disabled path that constructs no owner/plan/forward, invokes a no-Local native callback on the same opaque payload tuple, and proves payload identity, callback count, loss and slow-parameter gradient parity. The new bridge module exposes only `run_member(...)`; there is no disabled/no-Local bridge API or implementation, and its two tests exercise only enabled initial/continuation and retry-success paths.

   **Acceptance:** implement the frozen disabled/no-Local bridge behavior without constructing or touching `CanonicalSegmentRuntimeOwner`, `GAWindowPlan`, pending scan or Local injection. Add CPU/static parity Evidence using the same opaque payload tuple and deterministic callback, checking payload object identity, exactly-one callback, loss equality and slow-parameter gradient equality against the no-Local baseline.

4. **MEDIUM — closure Evidence does not establish contract→behavior→evidence for the submitted bridge.**
   - `production_segment_bridge_test.py` contains only two happy-path tests.
   - current request reports bridge=`2 passed`; the separately affected canonical wiring suite was not counted as PASS.

   Missing required Evidence includes at least: planned-vs-gathered cardinality rejection before callback; attempt-1 transient -> `LOCAL_MEM_RETRY_EXHAUSTED`; callback exception/malformed outcome terminal cleanup; raw finite and actual backward-exception behavior through the new pure seam; terminal/retry paths with nonzero real Local `.grad` proving exactly one clear/disposition/discard and zero sidecar commit; stale/open capability rejection after continuation; disabled parity; and regression of the existing canonical wiring failure semantics changed in this commit.

   **Acceptance:** after fixing production blockers, extend the public-path CPU/static fixtures to cover the frozen v0.3/v0.4 matrix and rerun all directly affected suites successfully, including `trainer_canonical_segment_wiring_test.py`, bridge, runtime owner, trainer integration, target `py_compile`, and both diff checks. Test counts alone are not sufficient; the fixtures must witness the exact negative-state invariants above.

## Scope boundary

No closure authority is granted for this pair. This `REQUEST_CHANGES` is limited to the CPU/static production-segment-integration implementation Gate. No production model/packer/dataset/config/checkpoint changes, real data/cache/checkpoint I/O, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1 is authorized.

Requested closure literal remains reserved for a corrected formal pair:
`APPROVE_TO_CLOSE_R09_B_TTT_V035_PRODUCTION_SEGMENT_INTEGRATION_CPU_STATIC`
