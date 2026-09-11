# ChatGPT Independent Review — R09-B TTT v0.3.5 Canonical Native Runtime CPU/static Implementation Design v0.1

- Date: 2026-09-11
- Formal root design SHA: `9d2c67c9481747dca23cb72f4822e6047e743543`
- Child/Gitlink SHA: `c0e6e55cbab00b7d40eccacc0de1c4c91b66f9d9`
- Request/ledger commit: `2c70ea456c2fb2f85944abeb2375ffa438e79b0a` (not part of the formal pair)
- Gate: `G0-R09-B-TTT-V035-CANONICAL-NATIVE-RUNTIME-CPU-STATIC-IMPLEMENTATION-DESIGN`
- Review object: `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_runtime_cpu_static_implementation_design_v0.1.md`
- Prior approved formal pair: `5fd23a289c4197a7a8887ec61d318c769f7c90e8 / c0e6e55cbab00b7d40eccacc0de1c4c91b66f9d9`
- Prior ChatGPT review: `docs/collab/chatgpt/reviews/2026-09-11_R09_B_TTT_v035_canonical_native_runtime_implementation_design_5fd23a2_c0e6e55.md`
- Inherited frozen authority: `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_runtime_implementation_design_v0.2.md`, especially §§2-4.

## Verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_runtime_cpu_static_implementation_design_v0.1.md:60-61)`

## Current blockers

`2 HIGH`.

## HIGH-1 — suffix recovery has no authorized implementable ABI under the frozen six-file whitelist

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_runtime_cpu_static_implementation_design_v0.1.md:60-61` (with the six-file whitelist at §1).

The design requires the only retry path to occur after an attempt-0 transient source failure, to derive the **unconsumed suffix** from the original frozen transaction, and to do so by calling the "existing exact retry capability" once.

That is not what the exact child currently exposes:

- `canonical_segment_production_adapter.py`'s `retry_first_member_pre_backward()` accepts only attempt-0 `member_index == 0`, the exact first member, and an unscanned request; `consume_retry()` additionally requires the attempt-1 plan to contain the same full `members` tuple as the original plan, preserve `member_index == 0`, and preserve the first member object.
- `canonical_segment_adapter_scheduler.py`'s `CanonicalBatchWindowTransaction.retry_first_member_pre_backward()` rejects retry once `backward_started` is true or `completed_members` is non-empty. It only promotes an **unstarted full window** to attempt-1.
- The inherited v0.2 contract, however, requires the recovery witness specifically after at least one earlier member has already succeeded/committed, with recovery owning only the unconsumed suffix and its own `N_window` / `GA_effective`.

Therefore the current public retry/transaction ABI cannot legally represent the required suffix-only attempt-1 after a committed prefix. The current design also explicitly excludes `canonical_segment_adapter_scheduler.py` from the implementation whitelist and does not freeze any alternative adapter-owned typed recovery plan/request/transaction ABI that can satisfy `CanonicalProductionSegmentRequest`, scan ordering, objective ownership, commit ordering, and original-transition reconciliation without private-state mutation or authority reconstruction.

This is a Design-Gate blocker: approving implementation now would force the implementation to invent an unreviewed recovery authority or silently weaken the inherited suffix-only contract.

**Exact acceptance condition:** before implementation is authorized, the design must freeze one implementable public ownership path for suffix recovery. It must prove how an attempt-1 recovery plan/transaction is derived from the exact original frozen transaction **after a committed prefix**, how exact suffix member identity/order/count and lineage are preserved, how recovery-specific `N_window` and `GA_effective=len(recovery.members)` are owned, how the suffix can enter scan/backward/commit in legal order, and how the original transition is reconciled exactly once, all without second admission/refreeze/resample or private authority reconstruction. If that requires a scheduler contract change, the Design Gate must explicitly expand the whitelist/authority before any code change.

## HIGH-2 — the mandatory scaling witness was weakened and can pass with a degenerate fixture

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_runtime_cpu_static_implementation_design_v0.1.md:93-97`.

The inherited v0.2 design §4 item 3 makes a stronger witness mandatory: **both normal and recovery** must exercise **non-equal valid counts and non-zero auxiliary loss**, and prove the exact formula with no second `/GA`.

The current v0.1 matrix only requires generic normal `valid count/formula` coverage plus recovery `N_window/GA_effective`. It does not require unequal per-member valid counts or non-zero auxiliary terms for both paths. An implementation could therefore use equal counts and/or `auxiliary_loss == 0`, allowing an incorrect primary ratio, incorrect auxiliary divisor, or accidental second GA scaling to remain invisible while still satisfying the written matrix.

**Exact acceptance condition:** restore the inherited mandatory witness literally enough that the implementation Gate cannot satisfy it with a degenerate fixture: normal and recovery must each include non-equal planned valid counts and non-zero auxiliary loss, assert the exact numeric objective `planned_N_valid[mu] / N_window * primary_consumer_mean + auxiliary_loss / GA_effective`, and prove no ordinary trainer division or second `/GA` is applied. The existing full-valid normal reduction witness may remain as an additional invariant, not as a substitute.

## Checks that pass in this pair

- The formal root tree resolves `cosmos-framework` exactly to `c0e6e55cbab00b7d40eccacc0de1c4c91b66f9d9`; the child commit is reachable and unchanged from the prior approved pair.
- The root delta from the prior formal design pair is docs/review bookkeeping plus the new 114-line CPU/static design; no child code changed in this formal pair.
- The predecessor pair/verdict is recorded correctly as `5fd23a289c4197a7a8887ec61d318c769f7c90e8 / c0e6e55cbab00b7d40eccacc0de1c4c91b66f9d9` with `APPROVE_TO_DESIGN_R09_B_TTT_V035_CANONICAL_NATIVE_RUNTIME_CPU_STATIC_IMPLEMENTATION`.
- The design correctly keeps the candidate native seam and current trainer hard-stop fail-closed; it does not claim real native runtime/scaler/optimizer/sidecar support.
- The normal immutable window, S0/continued/PAD, stream-major identity, post-backward-only fast commit, partial slow-grad discard, terminal attempt-1 behavior, and forbidden real-runtime scope are otherwise preserved at the design level.

## Incremental / evidence scope

This was a fresh incremental **Design Gate** review because the formal root changed while the child stayed fixed. The review independently inspected the new design, the prior frozen v0.2 authority, the exact formal root Gitlink, and the directly relevant child retry/window source ABI.

No project Python, real data/cache/checkpoint I/O, CUDA/GPU, `torchrun`, real native forward/loss/backward, optimizer/scheduler step, training, evaluation, inference, runtime sidecar, distributed execution, matched smoke, or LIBERO4IN1 was executed. No implementation/test execution result is claimed as independently rerun.

## Authorized next action

Docs-only remediation on a new formal root. The child should remain unchanged unless a separately reviewed Design-Gate authority explicitly expands the required implementation whitelist.

Not authorized by this verdict: the six-file implementation itself, scheduler/code changes, hard-stop removal, real I/O, GPU, real native runtime, optimizer/scheduler stepping, checkpoint/sidecar work, training, evaluation, inference, distributed execution, matched smoke, or LIBERO4IN1.

Any new formal root or child SHA requires a fresh incremental review.