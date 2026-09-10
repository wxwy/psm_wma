# ChatGPT 独立 Canonical Segment Production ABI Implementation Design Review

Formal reviewed pair:
- root design SHA: `0b5cee1938adde3e1970edfbfba74e91274eaf43`
- child/Gitlink SHA: `3a078f28f3d107bb633c932271f86498f7c427f7`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCTION-ABI-IMPLEMENTATION-DESIGN`
- artifact: `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_abi_implementation_design_v0.1.md`
- direct engineering authority: approved P0 source-ABI audit formal pair `395dadff0b17ed6206887e372718bb166aa63b40 / 3a078f28f3d107bb633c932271f86498f7c427f7`
- frozen algorithm authority: `PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.5.md` §7, §12, §18, §20.1--§20.2.
- request/ledger/session/review-poll commits after the formal root are bookkeeping only and do not replace the formal pair.

Verdict: `REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_abi_implementation_design_v0.1.md:56)`

## Incremental result

The P0 fixes remain valid: consumer loss vs auxiliary loss are separated, the canonical objective is already window-normalized, canonical backward must not divide by GA again, S0 is counted with prefix absent, PAD is excluded, and the old row-wise route is not an implementation authority. The new P1 design, however, does not yet freeze an implementable object-identity/commit chain for P2.

### HIGH-1 — producer/scan/gather ABI is circular and does not own canonical fast-state continuity

- Severity: HIGH
- Location: `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_abi_implementation_design_v0.1.md:54-62`
- Root cause: `CanonicalProductionSegmentInput` already contains gathered `consumer_payloads`, `local_prefixes`, `consumer_identities`, and caller-supplied `actual_n_valid`, while `SegmentBatchProducer.build(input)` is simultaneously required to derive those values by stream-major gather from `segment_batch.consumer_valid`. The stated graph says TTT scan occurs before gather, but this input ABI contains post-scan Local prefixes and has no typed `local_tokens/local_present/state_out` seam.
- Source/contract conflict: current `SegmentBatch` owns logical `[B,T]` `consumer_payload`; `SegmentBatch.gather_consumers(local_tokens, local_present)` derives payloads/prefixes/identities only after the TTT scan. The closed scheduler ABI also already provides `NativeConsumerBatch.from_segment(batch, member, local_tokens, local_present)` to derive the exact stream-major native batch and count. v0.3.5 additionally requires fresh/continuation `W_fast` continuity per stream and success-only detach/commit, but the design freezes no new batch fast-state owner/source for the scan.
- Exact acceptance:
  1. Split the ABI into a pre-scan logical capability and a post-scan gathered capability. The pre-scan input must not accept caller-supplied gathered payloads/prefixes/identities/actual count that the canonical adapter itself is supposed to derive.
  2. Freeze the exact existing scan seam used by P2 (`LocalEvidenceEncoder(CANONICAL_EVIDENCE_FEATURE_CONFIG)` + `ContinualTTTLocalMemoryCore.scan_segment_masked_encoded_many`, or another explicitly named already-approved equivalent) and a typed scan result containing at least `local_tokens`, `local_present`, and candidate `state_out`.
  3. Derive the native gathered batch through the frozen `SegmentBatch`/`NativeConsumerBatch.from_segment` semantics; `actual_n_valid` must be adapter-derived from that result, never trusted from the caller.
  4. Freeze an in-memory CPU/static fast-state authority for all B stream slots: fresh rows use current `W_bar_0`, continuations use only the exact previously committed detached state for the same slot/episode/source/cursor chain, terminal rows retire it, and failures do not mutate it.
  5. Add B>1 continuation evidence proving no cross-slot state leakage and that failed/reordered/foreign members cannot change the committed fast-state frontier.

### HIGH-2 — transaction/scheduler/fast-state commit chain is not object-bound or atomic

- Severity: HIGH
- Location: `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_abi_implementation_design_v0.1.md:71-72,103`
- Root cause: `CanonicalProductionForward` carries a `CanonicalBatchWindowTransaction` plus an arbitrary `adapter_commit: callable`, but no exact scheduler/window owner or typed one-shot commit capability. Section 6 performs backward and then says `adapter_commit -> transaction.mark_reconciled()`, without freezing the required transaction pre-backward transition or the live scheduler reconcile.
- Source/contract conflict:
  - current `CanonicalBatchWindowTransaction.mark_reconciled(member_index)` can succeed only after `mark_backward_started(member_index)` set the exact active member; the design never calls/freezes `mark_backward_started` before backward;
  - current `CanonicalBatchScheduler.reconcile_after_backward(member, actual_n_valid)` is the live/projected scheduler frontier commit and requires the exact frozen member object (`member is frozen`); the design never invokes or binds this scheduler authority;
  - calling an arbitrary `adapter_commit` first can detach/commit fast state and then fail at transaction/scheduler reconciliation, contradicting the same section's requirement that a post-backward commit failure leave both scheduler frontier and fast state uncommitted.
- Exact acceptance:
  1. Replace raw `adapter_commit: callable` with a typed, one-shot, object-identical capability/owner that binds the exact `CanonicalBatchScheduler`, `CanonicalGAWindowPlan`, `CanonicalBatchWindowTransaction`, `MicrobatchPlanMember`, scan result and candidate fast state.
  2. Freeze exact creation/arming: the window authority must originate from the same scheduler `freeze_plan()` result; `transaction.plan is plan`; `plan.members[member_index] is member`; foreign/reconstructed/stale objects fail before model forward/backward.
  3. After all pre-backward identity/count checks, call `transaction.mark_backward_started(member_index)` immediately before the one canonical backward; this transition must be covered by duplicate/reordered failure tests.
  4. After successful backward, perform all fallible commit preflights before the first irreversible mutation. Then commit candidate fast state, `CanonicalBatchScheduler.reconcile_after_backward(member, actual_n_valid)`, and `transaction.mark_reconciled(member_index)` through one fixed owner-controlled sequence in which no later validation can fail after an earlier state has mutated. If the current scheduler API cannot provide such a preflight, explicitly freeze the minimal new public preflight/commit API under the already-listed scheduler whitelist.
  5. Evidence must show exact-once commit, double/stale/foreign rejection, and zero partial mutation when any preflight fails.

### HIGH-3 — activation matrix can silently fall back to the superseded row-wise TTT route

- Severity: HIGH
- Location: `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_abi_implementation_design_v0.1.md:79`
- Root cause: the design activates canonical production only when both `config.local_ttt_enabled` and `canonical_production_segment_input` are present, then says missing capability follows No-Local/ordinary behavior. In the exact child, ordinary `OmniMoTModel.training_step()` falls into `_get_training_inputs()`; `_prepare_training_data()` calls `_inject_local_history()`, and when `local_ttt_enabled=True` that function calls the old `_ttt_local_memory_tokens()` row-wise lifecycle. Therefore a missing canonical capability can silently execute the exact legacy route that §1 says must never be a canonical fallback.
- Exact acceptance:
  1. Freeze an explicit activation truth table. For this Gate, canonical-enabled/expected + missing/malformed capability must fail closed before `_get_training_inputs()` or any legacy history/TTT route.
  2. Capability present while the canonical enable condition is false must also fail closed rather than be ignored.
  3. Only the true No-Local case may enter unchanged ordinary training. If legacy row-wise mode must remain separately runnable, it must be explicitly distinguished from canonical mode; it cannot be an implicit fallback in this Gate.
  4. Reject simultaneous old canonical/active markers or any conflicting legacy capability before forward.
  5. Add trainer/model fixtures proving: canonical exact capability -> new branch; canonical expected but missing/foreign capability -> pre-forward failure; No-Local -> byte/control-flow parity; old row-wise marker never executes through the new route.

### MEDIUM-1 — P2 defers GradScaler Option-B but does not freeze the required runtime hard stop

- Severity: MEDIUM
- Location: `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_abi_implementation_design_v0.1.md:103-105`
- Root cause: P2 explicitly defers real optimizer-step/GradScaler telemetry to P3, yet it modifies the real trainer/model production files and does not state how the new canonical branch is prevented from reaching an enabled GradScaler/real optimizer boundary before P3. In the current trainer, the special active route has dedicated found-inf handling; the ordinary route can advance `scheduler.step()` after `GradScaler.step()` unless a legacy TTT lifecycle intercepts the skip. The new canonical route is forbidden from reusing that legacy lifecycle.
- Exact acceptance:
  1. Since real Option-B is deferred, freeze a P2 fail-closed guard that prevents the canonical production branch from executing an enabled/unsupported real GradScaler optimizer path before P3 authorization, with zero fast-state/scheduler/transaction mutation.
  2. Alternatively, if P2 is intended to implement exact scaler disposition now, expand the design explicitly with its own typed preflight/resolution contract and evidence; do not inherit active/legacy lifecycle authority implicitly.
  3. CPU/static evidence must include an enabled/unsupported-scaler negative and prove No-Local optimizer behavior remains unchanged.

## Verified non-blocking parts

The following parts are acceptable and should be retained in remediation:

- formal child/Gitlink resolves exactly to `3a078f28f3d107bb633c932271f86498f7c427f7`; the current P1 pair is docs-only;
- the P0 source-map and loss split are carried forward correctly;
- `L_member = N_valid_i/N_valid_window * consumer_loss + auxiliary_loss/GA` is correct, and canonical backward correctly avoids a second `/GA`;
- S0 is a counted native consumer with `None` Memory Prefix; PAD produces no native sample;
- stream-major order and actual/planned count equality remain explicit;
- the design keeps `packers.py`, dataset/dataloader, real I/O, config, optimizer selector, checkpoint, GPU/training and runtime sidecar outside P2;
- historical row-wise active/canonical routes are correctly declared non-authoritative in principle; the activation blocker above concerns making that declaration enforceable.

Current blockers: **3 HIGH, 1 MEDIUM**.

No P2 implementation authority is granted. Authorized next action is docs-only remediation of this P1 design on a new formal root SHA with the child SHA stated explicitly. No child implementation, real data/cache/checkpoint I/O, CUDA/GPU, torchrun, runtime sidecar, LIBERO4IN1, training, evaluation or inference is authorized.
