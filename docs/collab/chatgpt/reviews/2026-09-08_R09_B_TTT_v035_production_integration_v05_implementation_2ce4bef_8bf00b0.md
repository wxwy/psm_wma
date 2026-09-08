# ChatGPT independent review — Local Memory v0.3.5 production integration v0.5 CPU/static implementation

**Date:** 2026-09-08  
**Verdict:** `REQUEST_CHANGES`

Formal reviewed pair:
- root implementation SHA: `2ce4bef4300e432131ac62aea374b45a9cbe1d55`
- child/Gitlink SHA: `8bf00b05803fcf901dc9b09f3208c4fff811a245`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-INTEGRATION-CPU-STATIC`
- requested closure literal: `APPROVE_TO_CLOSE_R09_B_TTT_V035_PRODUCTION_INTEGRATION_CPU_STATIC`
- request/bookkeeping SHA observed at review start: `fa34c9e16a61b4b68c323b16afc746eaf4a71068`

Fresh incremental implementation review relative to approved v0.5 design pair `52c5f7d2542b348bf13ad6ada4fde5b5da02aa91 / 8754c96a6bde002269751eca55c01dee694f6caa`. The already-closed v0.4 transaction implementation remains CLOSED and was not technically re-reviewed.

Repository scope is clean: child compare `8754c96..8bf00b0` adds only the approved new `local_memory_segment_adapter.py` and adjacent `local_memory_segment_adapter_test.py`; no trainer/core/runtime/registry/model-forward/real-I/O/GPU/training wiring changed.

## Current blockers

### 1. HIGH — sidecar mutation is not transaction-authorized/fail-closed; the implementation can commit fast state before any successful trainer transaction

**Locations:**
- `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_integration_implementation_design_v0.5.md:26-43,50-58`
- `cosmos_framework/model/generator/mot/local_memory_segment_adapter.py:39-43,53-65`
- `cosmos_framework/model/generator/mot/local_memory_segment_adapter_test.py:54-61`

**Root cause:** the frozen v0.5 order requires the unique trainer seam to perform `transaction.validate_success(member_index, identity, actual_n_valid)`, the canonical objective/backward and `transaction.successful_backward(...)`, and only **after that successful transaction commit** may the sidecar detach-copy `state_out`. It also freezes terminal/retry/GradScaler paths as sidecar-no-write.

The implementation does not bind sidecar mutation to that authority. `CanonicalLocalMemorySegmentAdapter.scan()` drops the design's transaction context and only accepts `identity`; `CanonicalLocalMemorySegmentAdapter.commit()` blindly calls `sidecar.commit(identity, result.state_out)`; and `LocalMemorySegmentSidecar.commit()` blindly writes/deletes the slot. There is no proof that the matching member was validated/backwarded/committed, no transaction-success token/state check, and no guard preventing a terminal/retry/GradScaler path from calling the same mutation method.

The adjacent fixture demonstrates the violation directly: it calls `adapter.scan(...)` and then `adapter.commit(identity, result)` without invoking `ImaginaireTrainer._run_local_memory_segment_backward` or `transaction.successful_backward()` at all, yet the next segment successfully reads the carried detached state. This establishes a second fast-state commit path outside the canonical transaction owner.

**Violated contract:** v0.5 §3/§4 and the approved review require trainer/transaction success to be the unique commit authority; sidecar is only a post-success detached cache and must not write on terminal/retry/GradScaler outcomes.

**Acceptance:** within the already-approved exact whitelist, make sidecar mutation provably post-transaction and fail-closed:
1. the same planned member identity/count must be validated through the existing trainer seam, exactly one backward must succeed, and `transaction.successful_backward(...)` must complete before any sidecar write/delete is possible;
2. identity/planned mismatch, raw non-finite, backward exception, transient recovery/exhaustion and GradScaler skip must produce zero sidecar writes for the failed member while preserving previously committed fast chronology;
3. terminal success may delete/suppress carry only after that terminal member's successful transaction commit; rebind then starts fresh;
4. a direct pre-transaction adapter/sidecar commit for a scanned result must fail closed rather than carry state;
5. preserve the existing trainer seam as the unique validation/objective/backward/transaction owner; do not create a second transaction implementation in the adapter.

### 2. MEDIUM — mandatory v0.5 contract→behavior→Evidence matrix is incomplete

**Locations:**
- `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_integration_implementation_design_v0.5.md:50-61`
- `cosmos_framework/model/generator/mot/local_memory_segment_adapter_test.py:23-61`
- `cosmos_framework/trainer/trainer_local_memory_integration_test.py:1-260`

**Root cause:** the request reports adapter+segment CPU suite=`12 passed`, adapter `py_compile` PASS and child/root diff-check PASS, but explicitly states that the trainer seam suite did not return a terminal result and must not be treated as PASS. More importantly, the two new adapter fixtures do not establish the frozen v0.5 integration matrix:
- adapter scan fixture is `B=1,T=3`, not the required `B=2,T=3` mixed valid/S0/PAD witness;
- identities are manually constructed; no fixture proves two consecutive **scheduler-admitted** segments carry state only after successful trainer transaction commit;
- no adjacent adapter fixture covers duplicate/stale cursor and source mismatch separately, terminal/rebind through the actual adapter+transaction path, or absence of adapter-private chronology;
- no failure/GradScaler/retry fixture proves sidecar remains unchanged while the existing trainer transaction takes the frozen terminal/recovery disposition;
- no disabled-parity fixture proves that not constructing the adapter leaves payload/native loss/gradients/output unchanged and that old `ProductionLocalMemoryRuntime`/`TTTLifecycle`/C6 paths are uncalled;
- the current carry fixture proves only a direct manual commit/read, which is precisely the HIGH violation above rather than Evidence of post-transaction carry.

**Acceptance:** after closing the HIGH, add/extend only approved synthetic fixtures to prove the full v0.5 matrix through the actual adapter + existing trainer transaction seam: required `B=2,T=3` invalid-first/gather identity, two scheduler-admitted consecutive segments with no graph retention, stale/duplicate/source/terminal/rebind behavior, consumer-spy valid-row semantics, normal/recovery weighted objective invariants, all terminal/GradScaler no-sidecar-write cases, and disabled parity. Re-run the adapter/segment suite **and** the existing trainer seam suite with a readable PASS result, plus target `py_compile` and child/root `git diff --check`.

## Non-blocking confirmations

- Exact scope/whitelist is clean: only the two approved new adapter files changed relative to the approved child baseline.
- `SegmentScanResult` is a frozen dataclass; `state_out` remains graph-bearing through scan and sidecar writes detach-copy state.
- The adapter uses canonical `scan_segment_masked_encoded_many(..., create_graph=True)` and `SegmentBatch.gather_consumers()`; opaque payload objects are not reconstructed.
- Stable-slot carry stores the last canonical `SegmentIdentity` and detached state; cursor is verified, not generated.
- No model forward, registry/default/config, production runtime/lifecycle/C6 wiring, real checkpoint/data/cache I/O, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1 authority was introduced.

No v0.5 CPU/static closure is authorized by this verdict. A remediation implementation forms a new formal pair and requires fresh review.