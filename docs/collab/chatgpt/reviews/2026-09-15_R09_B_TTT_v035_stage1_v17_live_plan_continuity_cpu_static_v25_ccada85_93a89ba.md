# ChatGPT independent review — Stage-1 v1.7 live-plan continuity CPU/static V25

- Formal root: `ccada85a50be8e541d8c618752986e2cf088f05e`
- Formal child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-LIVE-PLAN-CONTINUITY-CPU-STATIC-V25`
- Verdict: `REQUEST_CHANGES(tools/psm_wma/stage1_v17_pre_c_rehearsal.py:384)`
- Blockers: `1 HIGH`
  - Design/Authority: `0`
  - Production/implementation: `1 HIGH`
  - Evidence/Scope: `0`
  - child/runtime: `0`

## Formal validity

PASS. The root resolves. Its tree binds `cosmos-framework` as mode `160000`, type `commit`, exactly to `93a89ba61306d840a008813f62f26a34d54850f4`; the child resolves independently.

## Positive closure

The prior approval-state blocker is materially remediated:

- `LivePlanSessionV1` now starts with `_state = "PENDING"` and no usable approval credential;
- `approve(approval_identity)` is a distinct transition that binds a non-`None` external identity and moves the session to `APPROVED`;
- `resume_once()` requires `APPROVED`, the exact live lease and the exact bound approval identity before proceeding;
- duplicate live owners are rejected;
- close/invalidation retires the plan;
- public `consume_once_v05(plan)` remains blocked while the plan is registered as live;
- the root-only CPU/static scope remains intact and no real pre-C/C, pair write, child/runtime/config mutation, GPU or training execution is introduced.

## HIGH 1 — resume-only authority can still be bypassed through module-level `_consume_once_v05(plan)`

V25's frozen contract requires pending direct consume/resume to fail-close and states that, after approval, the resume-only entrypoint should hand the exact original plan to the existing `consume_once_v05` path. The implementation instead introduces/retains a separate module-level `_consume_once_v05(plan)` primitive and has `resume_once()` call it directly.

That private-by-naming function has no session, lease, approval or ownership argument and performs no `_LIVE_PLANS`/continuation-state check. Any caller with the module object and plan can therefore call `_consume_once_v05(plan)` directly while the plan is `PENDING` or `APPROVED`, bypassing the public `consume_once_v05(plan)` continuation barrier and the entire resume-only authority state machine.

This is a production continuity/authority bypass, not a naming/style concern: Python underscore naming does not make a module-level function uncallable, and the frozen contract requires the authority restriction to be enforced by the implementation.

## Required remediation

Close the whole direct-C-entry class in one pass:

1. There must be exactly one callable route from an owned live plan into C, and it must be the verified resume-only path after `APPROVED`.
2. Do not leave a module-level plan-only C primitive that can be called without continuation authority.
3. Preferred shape: keep `consume_once_v05(plan)` as the single C implementation and have the session establish a narrowly scoped one-shot resume authorization before invoking that same function; `consume_once_v05` must validate that authorization for owned plans. An equivalent closure/capability design is acceptable if no external caller can invoke the raw C primitive with only a plan.
4. PENDING and APPROVED direct calls outside `resume_once()` must fail before freshness/consumer invocation with apply count `0`.
5. Add direct CPU/static witnesses that attempt every exposed C entrypoint on a pending/approved owned plan and prove there is no plan-only bypass; then prove approved same-plan resume succeeds once and remains terminal afterward.
6. Preserve the now-correct explicit approval transition, unique-owner rule, close/invalidation retirement, no reconstruction, C01-C15, nine-entry freshness domain, exactly-once/readback/no-retry semantics and pure-memory scope.

No real pre-C/C, request-pair write, materialization/source-evidence, child/runtime/config mutation, GPU/CUDA/torchrun, training/evaluation/inference/LIBERO4IN1 is authorized by this review.
