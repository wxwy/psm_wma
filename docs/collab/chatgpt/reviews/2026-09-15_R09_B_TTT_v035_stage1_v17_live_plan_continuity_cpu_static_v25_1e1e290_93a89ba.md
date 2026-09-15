# ChatGPT independent review — Stage-1 v1.7 live-plan continuity CPU/static V25

Formal pair:
- root: `1e1e2909476dc6b154a37e5ec8592355031ab74a`
- child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-LIVE-PLAN-CONTINUITY-CPU-STATIC-V25`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/stage1_v17_pre_c_rehearsal.py:355)`

Blockers: `1 HIGH`
- Design/Authority: 0
- Production/implementation: 1 HIGH
- Evidence/Scope: 0
- child/runtime: 0

## Positive closure

- Formal root resolves and binds `cosmos-framework` as mode `160000`, type `commit`, exactly to the declared child; the child resolves independently.
- The previous internal-C/bearer-token bypass is closed: module-level `_consume_once_v05` is removed, and verified `resume_once()` now releases the live-owner marker and invokes the sole `consume_once_v05(plan)` path.
- Explicit `PENDING -> APPROVED -> CONSUMED` state, separate `approve(external_identity)`, duplicate-owner rejection, close/invalidation retirement, public-consume blocking and same-plan handoff remain intact.
- Scope remains root-only pure-memory CPU/static; no real pre-C/C, request-pair write, materialization/source-evidence, child/runtime/config mutation, GPU or training is performed or authorized.

## HIGH 1 — `LivePlanSessionV1` is still copyable/serializable/rebindable despite the frozen V25 contract

The frozen V25 design requires that while review is pending, direct consume/resume **and copy/serialize/rebind** all fail closed. The current `LivePlanSessionV1` only declares ordinary mutable slots (`_plan`, `_lease`, `_approval`, `_state`) and does not implement copy/deepcopy/pickle rejection or a mutation/rebind guard.

This is authority-relevant, not cosmetic. A caller can mutate the live review-pending object graph directly, for example by assigning `_approval` and `_state = "APPROVED"`, then calling `resume_once(session.lease, attacker_identity)` without the independent approval transition. Existing tests check copy/pickle rejection only for the capability and sealed plan, not for the live session, and do not directly attempt slot rebinding.

## Required remediation

Close this whole continuity-object sealing class in one pass:

1. `LivePlanSessionV1` must reject `copy.copy`, `copy.deepcopy` and pickle/serialization while preserving the same live object as the only continuation owner.
2. External assignment/rebinding of `_plan`, `_lease`, `_approval`, `_state` (or any equivalent identity/state-bearing fields) must fail closed; legitimate internal transitions must use a sealed/private mechanism that cannot be reproduced by ordinary caller mutation.
3. The lease/session/plan binding must remain stable across PENDING and APPROVED states; no caller-visible mutation may substitute plan, lease or approval identity.
4. Add direct stdlib witnesses showing copy/deepcopy/pickle rejection and attempted field/state/approval rebind rejection with consumer/apply count `0`.
5. Then prove explicit `approve(external_identity)` followed by exact same-session/same-lease resume succeeds once, while duplicate owner, foreign lease/approval, close/loss and repeated resume remain terminal.
6. Preserve the now-correct single C entrypoint, no bearer-token/internal bypass, C01-C15, nine-entry freshness domain, exactly-once/readback/no-retry and pure-memory scope.

This review does not authorize real pre-C/C, request-pair construction, materialization/source-evidence, child/runtime/config mutation, GPU/CUDA/torchrun, training/evaluation/inference or LIBERO4IN1.
