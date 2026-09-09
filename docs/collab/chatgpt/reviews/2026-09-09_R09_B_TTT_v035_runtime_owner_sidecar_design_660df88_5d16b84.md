# ChatGPT 独立 runtime-owner / sidecar design v0.8.6 review

Formal reviewed pair:
- root design SHA: `660df88e37ea530e09d39c8ab8b1032da1b26177`
- child/Gitlink SHA: `5d16b84fe17a42f128065bf36361f6b1bb93a436`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-WIRING-RUNTIME-SIDECAR-DESIGN`
- request/bookkeeping HEAD observed at review time: `ba3a22ff958c0f5d44752fbabb0c82f3924c1710`

Verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_RUNTIME_OWNER_CPU_STATIC`

## Incremental scope

Fresh incremental review relative to prior formal pair `28828aaa03d7550e08d6f865216dcaa198b2f369` / `5d16b84fe17a42f128065bf36361f6b1bb93a436`. Child is unchanged. v0.8.6 is docs-only and inherits the v0.8-v0.8.5 exact wiring/pending authority, per-member runtime phase machine, retry projection, SKIP_READY chronology, snapshot frontier, abort preflight atomicity, four-file CPU/static whitelist, and no-real-I/O/GPU/training boundary.

## Prior blocker closure

**CLOSED — skip-resume GA plan authority is now exact and non-replaceable.** `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_wiring_runtime_sidecar_implementation_design_v0.8.6.md:5-35`.

v0.8.6 captures `skipped_plan is transaction.plan` before scaler-skip disposition and retains that exact immutable `GAWindowPlan` together with the exact already-admitted `skipped_identity`. `resume_skipped()` takes no caller plan argument and creates the new attempt-0 `LocalMemoryTransaction` from the retained exact plan, requiring `.plan is owner.skipped_plan`. This preserves the original `members`, `planned_n_valid`, `n_window`, `ga_effective`, attempt, chain identity, ordering and objective authority rather than allowing a replacement plan to change weighting after skip.

The design also narrows the unsupported case correctly: this Gate only permits scaler skip when `skipped_member_index == 0`; a later-member skip must fail closed before disposition with zero transaction/owner/scheduler/pending/sidecar mutation. That is compatible with deferring undefined mid-window exposure/compensation semantics to a later model/trainer integration Gate rather than silently inventing them here.

## Contract consistency

- `resume_skipped()` reuses the exact already-admitted identity without a second `scheduler.admit()`, so scheduler and sidecar chronology reconverge only after the skipped identity successfully commits.
- The retained original plan keeps `LocalMemoryTransaction.validate_success()` member/count authority and `GAWindowPlan.objective()` weighting unchanged.
- `SKIP_READY` remains non-snapshotable until the admitted-but-uncommitted identity resolves; after commit, the inherited committed-frontier snapshot guard applies again.
- Old skipped transaction/forward/result are permanently non-authoritative; replacement plans, later-member skip, repeated skip, wrong full identity and altered plan metadata are explicitly negative cases.
- No child production path, trainer/model/scheduler source, persistent sidecar/checkpoint I/O, configuration, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1 is authorized by this approval.

## Current blockers

None.

## Approval scope

`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_RUNTIME_OWNER_CPU_STATIC`

This approval authorizes only the next CPU/static implementation Gate on the frozen four-file whitelist: new `canonical_segment_runtime.py`, new `canonical_segment_runtime_test.py`, and the narrowly allowed helper/test changes in `local_memory_segment_adapter.py` and `local_memory_segment_adapter_test.py`. Any implementation root SHA or child SHA change requires a fresh independent implementation review before closure.
