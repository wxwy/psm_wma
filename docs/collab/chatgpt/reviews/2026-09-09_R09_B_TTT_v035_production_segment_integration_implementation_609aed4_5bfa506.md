# ChatGPT 独立 Production Segment Integration CPU/static implementation remediation review

Formal reviewed pair:
- root implementation SHA: `609aed4864e5b884467174615910a99861df4784`
- child/Gitlink SHA: `5bfa506b0200f5cbd11049378690dcef90af8f30`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-SEGMENT-INTEGRATION-CPU-STATIC-IMPLEMENTATION`
- previous formal pair: `cf328e8ca1f5a50e563a09db89c5e803f986119b` / `7f461eae69015b467c846923c1e92b7096f9f527`
- approved design authority: `ef8adca6082e41c98dd75cd0c341c9bc91dca454` / `556e278946b506195a57d0798b2b1a2e8b5eb9cc`, v0.3/v0.4
- request/bookkeeping HEAD observed: `d7a11b94e164ed546fc435a1cf90caf4ef7bec96`

Verdict: `REQUEST_CHANGES`

## Incremental scope

Fresh remediation review relative to `cf328e8 / 7f461ea`. Root formal change advances the Gitlink and SESSION bookkeeping. Child is one commit ahead of the previous implementation pair and changes only `production_segment_bridge.py`, its test, and `trainer/__init__.py`; relative to the approved design base, the full implementation remains within the six-file CPU/static whitelist.

The request reports only bridge=`4 passed` for this remediation. Earlier owner/trainer/py_compile/diff-check results belong to the previous child SHA and do not automatically transfer to `5bfa506...`.

## Prior blocker status

1. **CLOSED — native callback no longer owns `actual_n_valid`.** `NativeBatchResult` again contains only the two frozen loss tensors. The bridge derives `actual_n_valid = len(forward.payloads)` and uses that bridge-derived value for the pure backward seam and `transaction.successful_backward()`.

2. **CLOSED — previously closed canonical wiring backward path restored.** `_run_canonical_segment_backward()` again delegates to `_run_local_memory_segment_backward(..., clear_slow_grads=wiring.clear_local_slow_grads)` and no longer routes the old canonical marker path through the new pure bridge seam.

3. **CLOSED IN IMPLEMENTATION — Local-disabled bridge surface now exists.** `run_disabled(payloads, native_batch)` performs no owner/plan/scan/Local mutation and forwards the exact opaque payload tuple once to a no-Local callback.

4. **NOT CLOSED — Evidence matrix remains incomplete.** See current MEDIUM blocker below.

## Current blockers

1. **HIGH — gathered-count mismatch is detected after `owner.prepare()` but the bridge raises without terminalizing or discarding the exact pending capability, leaving the owner stuck in `PREPARED`.**
   - implementation: `cosmos_framework/model/generator/mot/production_segment_bridge.py:89-96`
   - Evidence: `cosmos_framework/model/generator/mot/production_segment_bridge_test.py:51-62`
   - violated contract: production-segment integration v0.3 §§1-3 and v0.4 inherited fail-closed transaction ownership.

   The remediation correctly derives `actual_n_valid` from `len(forward.payloads)`, but it does so after `owner.prepare(segment)`. At that point the owner is already `PREPARED`, `owner.forward` is live, and the adapter owns the exact pending `(identity, transaction, result)` tuple. If the gathered count differs from `transaction.plan.planned_n_valid[member_index]`, the bridge currently executes only:

   ```python
   raise RuntimeError("gathered consumer count does not match frozen plan")
   ```

   It does not call `owner.abort_terminal(...)`, does not call the exact pending discard, does not terminalize the transaction, and does not clear accumulated Local slow grads from earlier members in the same GA transaction. The new negative fixture explicitly asserts `owner.adapter.pending() is not None`, confirming that the failure leaves the graph-bearing pending capability live.

   This is not a harmless pre-callback rejection. After the exception, the public bridge cannot start a new initial member (`owner` is not `IDLE`), cannot continue (`owner` is not `MEMBER_COMMITTED`), and cannot enter retained retry (`owner` is not `MEMBER_READY`). A later-member mismatch can also leave previously accumulated slow grads live, contrary to the frozen terminal/fail-closed cleanup semantics.

   **Acceptance:** preserve bridge-derived count authority, but when the post-prepare count check fails, resolve the exact prepared capability through the owner before returning/raising. A compatible implementation is to classify it as `LOCAL_MEM_IDENTITY_CONTRACT_FAILURE`, invoke exactly one `owner.abort_terminal(transaction, forward, code)` (or an exactly equivalent owner-owned cleanup), and return `TerminalMemberResult(code)`. Required invariants: zero native callback, zero backward, zero new scheduler commit, zero sidecar commit; exact pending becomes `None`; transaction is terminal/suffix-suppressed; owner enters the terminal phase; any live Local slow grads are cleared exactly once; prior already-committed fast frontier is preserved. Add both first-member and later-member count-mismatch fixtures, the latter with nonzero accumulated Local `.grad`.

2. **MEDIUM — closure Evidence still does not establish the full frozen bridge contract for this new SHA.**
   - current request Evidence: bridge=`4 passed` only.
   - current bridge tests: four fixtures, with the count-mismatch fixture currently witnessing the wrong live-pending behavior.

   The remediation adds useful count-authority and disabled-path fixtures, but the required `contract -> behavior -> evidence` matrix is still incomplete. In particular:

   - disabled Evidence checks payload identity, callback count and returned scalar only; it does not prove frozen loss parity and slow-parameter gradient parity against the no-Local baseline;
   - there is no public bridge fixture for attempt-1 `LOAD_DECODE_TRANSIENT -> LOCAL_MEM_RETRY_EXHAUSTED`;
   - there is no callback-exception or malformed-outcome terminal fixture proving one real grad-clear + one disposition + one exact discard + zero sidecar commit;
   - there is no public bridge numerical/non-finite or actual backward-exception fixture with nonzero Local grads;
   - stale/open capability rejection after continuation/retry is not witnessed at the bridge surface;
   - the restored `_run_canonical_segment_backward()` path has not been accompanied by the requested canonical identity/numerical/backward failure regression Evidence;
   - the request does not report the directly affected `trainer_canonical_segment_wiring_test.py`, runtime-owner, trainer integration, target `py_compile`, or child/root `git diff --check` as PASS for this exact child/root pair.

   **Acceptance:** after fixing the HIGH blocker, add public-path CPU/static fixtures for the missing negative cases above, including disabled loss/grad parity and canonical failure regression. Rerun and report PASS for all directly affected suites on `5bfa506...`, including bridge, runtime owner, trainer integration, canonical wiring, target `py_compile`, child `git diff --check`, and root `git diff --check`. Test counts alone are insufficient; the fixtures must witness exact capability/pending/grad/frontier invariants.

## Scope boundary

No closure authority is granted for this pair. This `REQUEST_CHANGES` is limited to the CPU/static production-segment-integration implementation Gate. No production model/packer/dataset/config/checkpoint changes, real data/cache/checkpoint I/O, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1 is authorized.

Requested closure literal remains reserved for a corrected formal pair:
`APPROVE_TO_CLOSE_R09_B_TTT_V035_PRODUCTION_SEGMENT_INTEGRATION_CPU_STATIC`
