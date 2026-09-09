# ChatGPT 独立 runtime-owner / sidecar design v0.8.7 review

Formal reviewed pair:
- root design SHA: `c31eecbf40f38ab0b6b4d277cd425c5b45e66744`
- child/Gitlink SHA: `5d16b84fe17a42f128065bf36361f6b1bb93a436`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-WIRING-RUNTIME-SIDECAR-DESIGN`
- request/bookkeeping HEAD observed at review start: `1ee055efa8f46cbc584894022652635593127661`

Verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_RUNTIME_OWNER_CPU_STATIC`

## Incremental scope

Fresh incremental review relative to prior formal design pair `660df88e37ea530e09d39c8ab8b1032da1b26177` / `5d16b84fe17a42f128065bf36361f6b1bb93a436`. Child is unchanged. v0.8.7 is docs-only and inherits the v0.8-v0.8.6 exact wiring/pending authority, retained-plan skip chronology, zero-mutation abort preflight, retry projection, snapshot frontier, four-file CPU/static whitelist, and no-real-I/O/GPU/training boundary.

## Prior-gap closure

**CLOSED — attempt-1 / later-member `SCALER_SKIP` can no longer enter an unrecoverable `SKIP_READY` state.**

v0.8.6 allowed the supported skip-resume path only for an exact retained attempt-0 plan whose first unresolved member is index 0, but the inherited `abort(SCALER_SKIP)` surface did not yet explicitly reject attempt-1 before mutation. v0.8.7 adds an owner preflight, after exact pending-capability validation and before any transaction/owner/scheduler/sidecar mutation, requiring both `transaction.plan.attempt == 0` and `len(transaction.completed_members) == 0`.

If either condition fails, the owner remains `PREPARED` and all exact capability/state objects remain unchanged. This is compatible with the narrow Gate: attempt-1 or later-member scaler-skip handling is intentionally unsupported here rather than being silently converted into another retry/resume path. No new attempt-1 loop, replacement plan, scheduler rollback, or weighting semantics are introduced.

## Contract consistency

- The supported first-member attempt-0 skip path still retains the exact already-admitted `SegmentIdentity` and exact original immutable `GAWindowPlan` object.
- `resume_skipped()` remains parameter-free and must create a new transaction whose `.plan is` the retained original plan, preserving `members`, `planned_n_valid`, `n_window`, `ga_effective`, attempt, chain identity, ordering, and objective authority.
- Unsupported attempt-1/later-member skip fails before `grad_scaler_skip()` or `discard_pending()`, so the negative case is zero mutation and cannot strand partially-mutated owner/transaction state.
- Existing retry/terminal taxonomy remains outside this Gate's new surface; v0.8.7 does not redefine it.
- Child production/model/trainer/scheduler code is unchanged and no production execution is authorized.

## Current blockers

None.

## Approval scope

`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_RUNTIME_OWNER_CPU_STATIC`

This approval authorizes only the next CPU/static implementation Gate on the frozen four-file whitelist: new `canonical_segment_runtime.py`, new `canonical_segment_runtime_test.py`, and the narrowly allowed helper/test changes in `local_memory_segment_adapter.py` and `local_memory_segment_adapter_test.py`. It does not authorize production wiring/model/trainer/scheduler-source changes, persistent sidecar/checkpoint I/O, config/default/registry changes, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T, or LIBERO4IN1. Any implementation root SHA or child SHA change requires a fresh independent implementation review before closure.
