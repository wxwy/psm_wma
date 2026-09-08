# ChatGPT independent review — R09-B TTT v0.3.5 migration design

- Gate: `G0-R09-B-TTT-V035-MIGRATION-DESIGN`
- Formal root SHA: `a882b1296db8edaad8b2364080c718a61cb4a1ca`
- Formal child/Gitlink SHA: `0fddc27f9c3c463f784be9f528ffbbe123f244ff`
- Requested literal: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_MIGRATION_DESIGN` or `REQUEST_CHANGES`
- Verdict: `REQUEST_CHANGES`

## Scope checked

Fresh docs-only review. No project code/tests, real I/O, GPU, training, evaluation or inference were executed. The no-production-before-three-party-approval boundary is correct and remains in force.

## Blocking finding

1. **HIGH — the requested migration v0.1 is a superseded historical target and would recreate a second implementation authority.**

   - Historical repository truth: `docs/collab/chatgpt/archive/CODEX_INBOX_2026-09-08_de934b7.md:9-18` explicitly records root `6828b55400d49ef82f1eed895fd609bf8179c3a8` as the **superseded review target**, and the v0.3.6 request states that `PSM-WMA_Local_Memory_canonical_training_runtime_contract_v0.3.6.md` was created specifically to remediate that old v0.3.5 migration target's review failures. The later canonical chain continued through v0.3.9 and then through the separately approved CPU/static implementation design/implementation Gates.
   - The current document is still the unchanged historical v0.1 from that target. `docs/build/PSM-WMA_Local_Memory_v0.3.5_supersession_migration_design_v0.1.md:7,11-13,49-76,87-105,118-132` still binds child baseline `80aec09`, defines its own older `SegmentBatch`, calls `scan_segment_many()`, uses a pre-canonical scheduler/GA description, and says this approval opens a new CPU implementation phase.
   - That conflicts with the currently frozen CPU/static contract. `docs/build/PSM-WMA_Local_Memory_v0.3.9_cpu_static_implementation_design_v0.3.md:65-72` requires the canonical route to use `scan_segment_masked_many()`, preserve opaque `consumer_payload` in `SegmentBatch`, and keep `RankLocalSegmentScheduler` / `GAWindowPlan` with suffix-retry and episode-vs-slow-LR semantics. The same design also freezes the construction-time feature-disable owner/inventory; these are not optional migration details.
   - Formal-pair reality has also advanced: the current reviewed child is `0fddc27f9c3c463f784be9f528ffbbe123f244ff`, not the document's `80aec09` baseline.

   **Root cause:** the review request reactivates a pre-remediation migration document as if it were a new implementation authority, instead of treating it as historical input to the already-established canonical contract chain. Approving it would allow two incompatible definitions of SegmentBatch/scan/scheduler/GA and would reopen CPU implementation that has already been specified and closed under later Gates.

   **Acceptance:** create a new migration/handoff document and new formal root SHA that:
   1. explicitly marks `6828b55` / migration v0.1 as historical and superseded, with no implementation authority;
   2. binds the current child/Gitlink and the approved canonical v0.3.9 + closed CPU/static contract as prerequisites/source of truth;
   3. does not redefine stale SegmentBatch/scan/scheduler/GA semantics; either references the canonical definitions or restates them exactly, including shifted previous-evidence/source chronology, opaque `consumer_payload`, invalid-first `scan_segment_masked_many()`, per-slot terminal/rebind/admission authority, `GAWindowPlan` planned==actual checks, suffix-only recovery/retry taxonomy, partial-slow-grad disposition, and frozen state/dt/age owner/inventory;
   4. narrows the next Gate to the **remaining production migration** beyond the already-closed synthetic CPU/static core (for example production adapter/trainer/runtime-sidecar integration design), with an exact whitelist, acceptance, and prohibition boundary;
   5. keeps production code, real I/O, GPU/training/eval/inference prohibited until that new formal pair is independently approved.

## Boundary status

The requested docs-only prohibition itself is sound: this review grants no Local Memory production implementation, real checkpoint/data/cache I/O, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1 authority.
