# ChatGPT 独立 runtime-owner / sidecar design v0.8.3 review

Formal reviewed pair:
- root design SHA: `f2face62e51c4aef89dff6085fd87bb5441a612b`
- child/Gitlink SHA: `5d16b84fe17a42f128065bf36361f6b1bb93a436`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-WIRING-RUNTIME-SIDECAR-DESIGN`
- request/bookkeeping HEAD observed at review start: `2526146b09bdab6eeb4a44476817c37cedae9137`

Verdict: `REQUEST_CHANGES`

## Incremental scope

Fresh incremental review relative to prior formal design pair `a763c116322e1e360d575d430dc20c0b777a8465` / `5d16b84fe17a42f128065bf36361f6b1bb93a436`. Child is unchanged. v0.8.3 is a docs-only remediation that supersedes v0.8.2 and inherits the v0.8-v0.8.2 whitelist, exact wiring/pending authority, per-member phase machine, snapshot frontier, retry lifecycle and no-real-I/O/GPU/training boundary. Review is based only on the Codex request, the current design chain, the prior ChatGPT review, and the formal child source.

## Prior blocker status

1. **CLOSED — retry plan projection versus full identity is now typed correctly.** `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_wiring_runtime_sidecar_implementation_design_v0.8.3.md:5-17`. v0.8.3 compares `retry_plan.members[0]` to the canonical `(slot_id, episode_id, cursor)` projection, then separately requires the retained full `SegmentIdentity` to remain the exact scheduler `stable_slots[slot_id]` authority, already admitted and not committed. This is compatible with the formal child `GAWindowPlan.members` and `RankLocalSegmentScheduler` types and preserves the no-duplicate-admission rule.

## Current blockers

1. **HIGH — inherited phase machine makes `SCALER_SKIP` permanently kill the rank-local owner, contradicting the frozen GradScaler transaction semantics.** `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_wiring_runtime_sidecar_implementation_design_v0.8.1.md:24-54`; `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_integration_implementation_design_v0.4.md:21-32`; `cosmos_framework/model/generator/mot/local_memory_segment.py:215-260`.

   v0.8.1 freezes `PREPARED --abort(TERMINAL|SCALER_SKIP)--> ABORTED` and then states that `ABORTED` is terminal and cannot `begin`, `retry`, or `snapshot`. v0.8.3 explicitly inherits this phase machine unchanged. But the already-frozen transaction contract treats GradScaler skip as a **slow-side disposition**, not a permanent runtime terminal: existing fast commits are retained, partial slow grads are cleared, and the slow optimizer/LR step is suppressed. The formal child mirrors that distinction: `LocalMemoryTransaction.grad_scaler_skip()` closes only the current transaction and does not set `terminal_failure_code` or suppress future scheduler admissions/transactions.

   Under v0.8.3, one scaler skip therefore strands the single rank-local `CanonicalSegmentRuntimeOwner` in `ABORTED` forever. Since the design also freezes one owner per rank and provides no owner recreation/reset transition, later windows cannot start even though the inherited contract permits execution to continue with a fresh transaction after a skip.

   **Acceptance:** separate `SCALER_SKIP` from true terminal owner failure. Freeze a skip disposition that exact-discards any uncommitted pending capability, clears the current transaction/forward/admitted handles, retains previously committed detached fast state, performs no slow optimizer/LR advancement, and returns the owner to a state from which a subsequent fresh window can be admitted/begun. Preserve `ABORTED` only for genuinely terminal owner failure if desired. Add CPU/static Evidence for `scaler skip -> no pending write/no slow step -> subsequent fresh admit/begin/prepare` while prior committed sidecar state remains readable, plus snapshot behavior at the immediate skip boundary and the next safe committed boundary.

2. **MEDIUM — inherited `abort()` ordering is not fail-closed atomic: transaction disposition is mutated before pending-capability identity is proven/discarded.** `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_wiring_runtime_sidecar_implementation_design_v0.8.md:76-90`; `cosmos_framework/model/generator/mot/local_memory_segment.py:223-254`.

   v0.8 freezes `abort(transaction, forward, disposition)` to execute `terminal_failure()` / `recover_transient()` / `grad_scaler_skip()` first and only then call exact `adapter.discard_pending(identity, transaction, forward.result)`. The same section requires mismatch, already-cleared, or substitute pending results to fail. Those transaction dispositions are irreversible: transient recovery creates/closes the attempt-0 suffix authority, terminal failure closes/suppresses the transaction, and scaler skip closes it.

   Therefore a stale/substitute `forward.result` can make the later `discard_pending()` reject **after** the transaction has already been changed. A failed abort call can leave the owner in a PREPARED-like phase with a closed/recovered transaction and still-live pending capability, violating the design's own exact-capability/fail-closed state ownership.

   **Acceptance:** freeze an owner-level preflight before any transaction mutation: exact current transaction/forward identity and `adapter.pending()` must first prove the same `(identity, transaction, forward.result)` tuple. Only after that validation may the transaction disposition run and the exact pending be discarded. Add negative CPU/static Evidence that substitute transaction/forward/result, stale/cleared pending, or mismatched identity fail with **zero transaction/owner/pending mutation**; add positive terminal/retry/skip cases proving one disposition plus one exact discard.

## Scope boundary

No runtime-owner CPU/static implementation authority is granted for this pair. This remains docs-only. No production model/trainer/packer wiring, persistent sidecar/checkpoint I/O, config/default/registry changes, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T, or LIBERO4IN1 is authorized.
