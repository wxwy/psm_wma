# ChatGPT independent review — Stage-1 v1.7 live-plan continuity CPU/static V25

Formal pair:
- root: `9a3c9c3fb2f6184eff8d651fae4f48a624afe040`
- child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`

Gate: `G0-R09-B-TTT-V035-STAGE1-V17-LIVE-PLAN-CONTINUITY-CPU-STATIC-V25`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/stage1_v17_pre_c_rehearsal.py:368)`

Blockers: `1 HIGH`
- Design/Authority: 0
- Production/implementation: 1 HIGH
- Evidence/Scope: 0
- child/runtime: 0

## Positive closure

- formal root resolves and its root tree binds `cosmos-framework` mode `160000`, type `commit`, exactly to the declared reachable child;
- changes are limited to the existing pure-memory pre-C module and stdlib unittest; no real pre-C/C, request pair, materialization/source-evidence, child/runtime/config mutation, GPU or training is in scope;
- direct `consume_once_v05(plan)` is now blocked while a plan id is registered as live-pending;
- continuation lease is non-copyable/non-serializable and foreign/closed lease failure is terminal;
- previous ContractV05/freshness-domain/four-step C/no-retry behavior is otherwise preserved.

## HIGH — approval state and unique plan ownership are not actually encoded

V25 requires a review-pending session to reject ordinary resume/direct consume, and only after independent approval to accept the same live lease plus exact approval identity. The implementation does not contain a pending→approved transition. `LivePlanSessionV1.__init__` creates `_approval = object()` immediately, exposes it through `approval_identity`, and `resume_once()` accepts that same object immediately. The positive test calls `session.resume_once(session.lease, session.approval_identity)` directly after session construction, with no approval action, so the test positively certifies the forbidden pending→C path.

The same continuity class also does not enforce unique ownership of a plan. Creating multiple `LivePlanSessionV1` objects for the same `SealedPreCPlanV1` is allowed because `_LIVE_PLANS` is only a set of `id(plan)`. Closing either session removes that id, potentially reopening the public direct-consume path while another session for the same plan is still pending. This violates V24/V25's one-session/one-plan/one-lease same-lifetime ownership model.

## Required remediation

Close this class-wide in one pass:

1. Encode an explicit terminal state machine, at minimum `PENDING -> APPROVED -> CONSUMED` plus `INVALID/CLOSED`; `resume_once()` while `PENDING` must fail before `_consume_once_v05` and before any consumer call.
2. Do not expose a usable approval credential at construction time. A separate approval transition must install/accept the exact independent approval identity after review; only then may resume consume the same live lease and original plan object.
3. Enforce exactly one live session owner per plan. Constructing a second session over the same plan must fail-close, and closing/invalidating one session must not be able to unprotect a different owner.
4. Preserve public `consume_once_v05(plan)` blocking for every plan owned by a live pending/approved session; only the session's resume-only path may call the internal C primitive.
5. Add direct stdlib witnesses: pending resume rejects with apply count 0; explicit approval then same lease resumes once; foreign approval/lease and duplicate-owner session are terminal; after any invalidation/close no direct-consume bypass or replacement plan path exists.
6. Preserve pure-memory scope and all previously closed freshness/closure/exactly-once/readback/no-retry guarantees.

This review does not authorize real pre-C/C, request-pair write, materialization/source-evidence, child/runtime/config mutation, GPU or training.
