# ChatGPT independent review — Local Memory v0.3.5 production integration implementation design v0.5 executable-sidecar remediation

**Date:** 2026-09-08  
**Verdict:** `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_PRODUCTION_INTEGRATION_CPU_STATIC`

Formal reviewed pair:
- root design SHA: `52c5f7d2542b348bf13ad6ada4fde5b5da02aa91`
- child/Gitlink SHA: `8754c96a6bde002269751eca55c01dee694f6caa`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-INTEGRATION-IMPLEMENTATION-DESIGN`
- requested approval literal: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_PRODUCTION_INTEGRATION_CPU_STATIC`
- request/bookkeeping SHA observed at review start: `6cb98fb19e74a2590f3e9ee8caadf41c305c7371`

Fresh incremental review relative to formal pair `19a4d59e0e7535e71c483f3a147a747fee7d5f2a / 8754c96a6bde002269751eca55c01dee694f6caa`. The already-closed v0.4 transaction implementation remains CLOSED and was not technically re-reviewed.

## Prior blocker status

### CLOSED — prior HIGH sidecar / transaction lifecycle blocker

The remediation now freezes an executable order consistent with formal child `8754c96`:

1. `SegmentBatch` is validated and the exact scheduler-admitted `SegmentIdentity` is supplied to the adapter.
2. The sidecar reads only by stable `slot_id` and stores `(last_committed_identity, detached_fast_state)`; it does not derive GA position, consumer step, segment cursor, or any private chronology.
3. Canonical `ContinualTTTLocalMemoryCore.scan_segment_masked_encoded_many(..., create_graph=True)` and `SegmentBatch.gather_consumers()` run before the consumer returns `actual_n_valid`.
4. The existing unique trainer seam alone performs `transaction.validate_success(member_index, identity, actual_n_valid)`, the frozen primary/aux objective, exactly one backward, and `transaction.successful_backward(...)`.
5. Only after successful trainer/transaction commit may the sidecar detach-copy `state_out`.
6. Cross-segment carry is now explicit and non-authoritative: the stable slot maps to the exact last committed canonical identity plus detached state; the sidecar only verifies episode/source continuity and `current.cursor == last.cursor + 1` against those canonical identities and never generates/increments cursor.
7. First segment/no record starts fresh; terminal success performs no carry write and deletes the slot record; terminal rebind therefore starts fresh.

This closes the previous impossible pre-scan `validate_success(actual_n_valid)` order and the unresolved predecessor lookup / terminal carry ambiguity without introducing a second scheduler or chronology authority.

### CLOSED — prior MEDIUM `SegmentScanResult` ABI blocker

The exact whitelist now authorizes a concrete frozen `@dataclass(frozen=True) SegmentScanResult` and freezes:
- `local_tokens: torch.Tensor[B,T,K,32]`;
- `local_present: torch.BoolTensor[B,T]`;
- `state_out: ContinualTTTFastState`;
- `payloads: tuple[Any, ...]`;
- `locals: tuple[torch.Tensor | None, ...]`;
- `identities: tuple[tuple[int,str,int], ...]`.

The result may not detach/copy/materialize or reconstruct opaque consumer payloads; `locals` and `state_out` remain graph-bearing until the successful backward/transaction commit, after which only the sidecar may detach-copy `state_out`. Formal child repository truth is consistent with the frozen Local width: `ContinualTTTLocalMemoryCore` defaults `local_dim=32` and returns `[B,K_local,D_local]` Local reads.

## Current blockers

None.

## Scope / authorization

This approval authorizes only the next CPU/static synthetic implementation inside the exact v0.5 whitelist:
- new `cosmos_framework/model/generator/mot/local_memory_segment_adapter.py` with only `SegmentScanResult`, `CanonicalLocalMemorySegmentAdapter`, and `LocalMemorySegmentSidecar`;
- new `cosmos_framework/model/generator/mot/local_memory_segment_adapter_test.py`;
- existing `cosmos_framework/trainer/__init__.py`, only `ImaginaireTrainer._run_local_memory_segment_backward`;
- existing `cosmos_framework/trainer/trainer_local_memory_integration_test.py`, only adjacent synthetic fixtures.

The implementation must satisfy v0.5 CPU/static acceptance including mixed valid/S0/PAD invalid-first scanning, opaque gather identity, consecutive-segment carry without graph retention, stale/duplicate/source/terminal/rebind fail-closed behavior, unique trainer scaling/backward/transaction ownership, recovery/full-window/no-second-GA scaling, failure/GradScaler semantics, and disabled parity.

This approval does **not** authorize model-forward wiring, registry/default/config changes, `production_runtime_adapter.py`, `runtime_authority.py`, `ttt_lifecycle.py`, `local_evidence.py`, `local_memory_segment.py`, C6 adapter changes, real checkpoint/data/cache I/O, runtime sidecar persistence/resume, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1. Any implementation creates a new formal pair and requires fresh three-party closure review.