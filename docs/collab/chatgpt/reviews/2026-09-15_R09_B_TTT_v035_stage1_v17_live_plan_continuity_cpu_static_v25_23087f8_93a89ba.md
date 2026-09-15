# ChatGPT independent review — Stage-1 v1.7 live-plan continuity CPU/static V25

Formal pair:
- root: `23087f8274567a99ee9751a63ba105f48c2f1845`
- child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-LIVE-PLAN-CONTINUITY-CPU-STATIC-V25`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/stage1_v17_pre_c_rehearsal.py:367)`

Blockers: `3`
- Design/Authority document: 0
- Production/implementation: `2 HIGH`
- Evidence: `1 MEDIUM`
- Scope/child/runtime: 0

## Re-lock / target validity

- Latest pre-review `V2` HEAD was request/bookkeeping commit `de47344793aeca38751b74b5d9e63527610a0ad3`, whose parent is the declared formal root.
- Formal root `23087f8274567a99ee9751a63ba105f48c2f1845` resolves `cosmos-framework` as the exact Gitlink `93a89ba61306d840a008813f62f26a34d54850f4`.
- Child `93a89ba61306d840a008813f62f26a34d54850f4` resolves independently in `wxwy/cosmos-framework`.
- Previous reviewed pair was `1e1e2909476dc6b154a37e5ec8592355031ab74a / 93a89ba61306d840a008813f62f26a34d54850f4`; root changed, so this is a fresh technical target.

## Authority chain used

Effective inherited authority remains:
1. V24 `PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_live_plan_continuity_authority_v2.4.md`;
2. V25 `PSM-WMA_Local_Memory_v0.3.5_stage1_v17_live_plan_continuity_cpu_static_implementation_design_v2.5.md`.

V25 explicitly inherits V24 and does not supersede its same-instance/binding requirements. Relevant frozen requirements include:
- unique sealed plan + opaque lease + session are one same-lifetime triple;
- immutable/non-copyable object-token binding of session/plan/lease identity and a binding digest;
- audit/review record carries the triple identities and binding digest and remains read-only/non-reconstructive;
- pending direct consume/resume/copy/serialize/rebind fail closed;
- verified resume checks the live triple binding before handing the original plan object to the sole C path;
- identity drift/replacement/loss/failure is terminal.

## Positive closure

- The prior module-level internal-C/bearer-token bypass remains closed: there is only `consume_once_v05(plan)` as the C implementation path.
- `LivePlanSessionV1` now rejects `copy.copy`, `copy.deepcopy` and pickle/serialization at the production-method level.
- Ordinary assignment to `_plan`, `_lease`, `_approval`, `_state` is rejected while `_locked` remains true.
- `PENDING -> APPROVED -> CONSUMED`, same-lease/exact-approval checks, duplicate-owner rejection and terminal close/retirement remain present.
- Delta stays root-only pure-memory CPU/static; no real pre-C/C, request-pair write, materialization/source-evidence, child/runtime/config mutation, GPU or training is authorized.

## HIGH 1 — sealing is bypassable because the guard bit itself is caller-mutable/deletable

Location: `tools/psm_wma/stage1_v17_pre_c_rehearsal.py:358-369` (root cause at the `__setattr__` guard around line 367).

`__setattr__` protects only `_plan`, `_lease`, `_approval`, `_state`; `_locked` itself is an ordinary writable slot and there is no `__delattr__` guard. An ordinary caller can therefore do, without reflection or private-state monkeypatching:

1. `session._locked = False` (or delete the slot);
2. assign attacker-controlled `_approval` and `_state = "APPROVED"` (and potentially substitute plan/lease too);
3. call `resume_once(session.lease, attacker_identity)`.

That reaches the C path without the independent `approve(...)` transition. The new test only attempts direct `_state` assignment while `_locked` is still true, so it does not witness this bypass.

Violated frozen contract: V25 pending `rebind` fail-close; V24/V25 same live object authority; independent approval before verified resume.

Why current Evidence does not close it: the reported `16/16` suite never mutates/deletes `_locked`, never demonstrates all authority-bearing fields remain sealed after an attempted unlock, and never asserts consumer/apply count remains zero for this attack.

Acceptance:
- remove any caller-writable/deletable switch that can disable sealing, or otherwise make the sealing mechanism itself non-rebindable/non-deletable;
- external set/delete/rebind attempts over every authority/state-bearing field (including any future guard/token field) must fail closed;
- a direct unlock→approval/state/plan/lease substitution attempt must fail before freshness/consumer invocation with apply count `0`;
- legitimate internal transitions may still occur only through the intended production methods.

## HIGH 2 — the frozen session/plan/lease binding digest is not implemented or verified

Locations: `tools/psm_wma/stage1_v17_pre_c_rehearsal.py:359-362, 377-392`.

V24 requires an immutable token binding the session/plan/lease triple and an exact review record containing the three identities plus their binding digest. V25 inherits that requirement and requires resume to verify the triple binding before handing the original plan to C.

Current implementation does not establish that authority:
- `_LIVE_TOKENS[id(plan)] = self._lease._token` binds only plan-id -> lease token; it does not bind session identity or a binding digest;
- `_LIVE_TOKENS` is only inserted/popped and is never consulted by `resume_once()` or `consume_once_v05()`;
- `audit_record()` lists `id(session)`, `id(plan)`, `id(lease)` but contains no binding digest and omits inherited review-record binding fields from V24;
- `resume_once()` validates state, lease object identity and approval identity only; it does not prove the live triple against an immutable creation-time/review-record binding before releasing ownership.

This is not superseded by a later authority document. The V25 design explicitly says it implements V24 and repeats the object-token + binding-digest requirement.

Violated frozen contract: V24 same-lifetime triple/review-record binding and V25 creation-time immutable object-token binding + triple verification before C.

Why current Evidence does not close it: same-lease success and foreign-lease rejection prove only local object comparison, not equality to an independently frozen creation-time/review-record triple binding. No test can regress a missing digest check because no digest authority currently participates in the control flow.

Acceptance:
- create a non-copyable, non-caller-rebindable creation-time authority that binds exact session identity + plan identity + lease identity and a deterministic/frozen binding digest;
- make the read-only audit/review witness expose the exact required triple identities + binding digest and all still-inherited V24 binding fields needed for equality proof, without becoming a reconstruction input;
- `resume_once()` must verify the current live session/plan/lease against that exact binding before it releases live ownership or invokes C;
- plan/lease/session substitution or binding drift must terminalize and keep freshness/consumer/apply count at `0`;
- remove or repurpose dead `_LIVE_TOKENS` state so there is only one real authority rather than a non-enforcing mirror.

## MEDIUM 3 — sealing/binding Evidence remains incomplete and non-causal

Location: `tools/psm_wma/test_stage1_v17_pre_c_rehearsal.py:149-155`.

The new `test_live_session_is_sealed` exercises only:
- `_state` assignment while the guard is still locked;
- `copy.copy(session)`;
- `pickle.dumps(session)`.

It does not directly witness the full required class:
- `copy.deepcopy(session)`;
- `_plan`, `_lease`, `_approval`, `_locked` (or equivalent guard/token) assignment/rebinding;
- deletion/rebinding of authority fields;
- unlock-then-mutate bypass;
- apply count `0` after every rejected mutation/copy/serialization attempt;
- immutable triple-binding digest equality, drift rejection, review-record equality, or plan/lease substitution rejection.

Acceptance: add direct stdlib tests through the production objects/API for the complete sealing and binding class above. The tests must be causal: if the guard/binding check is removed or reordered, they fail, and every pre-resume rejection must prove freshness/consumer/apply was not entered.

## Blocker lifecycle

- Previous pair blocker “session is copyable/serializable/rebindable”: `PARTIALLY REMEDIATED / STILL OPEN` — copy/serialization methods are now present, but rebind sealing remains bypassable.
- New inherited-contract finding: missing enforcing triple binding + binding digest: `OPEN (HIGH)`.
- Evidence completeness for the whole sealing/binding class: `OPEN (MEDIUM)`.

## Scope reminder

This verdict only concerns the exact formal pair above and this CPU/static V25 Gate. It does **not** authorize real pre-C/C, request-pair construction/write, materialization/source-evidence, child/runtime/config mutation, GPU/CUDA/torchrun, training/evaluation/inference or LIBERO4IN1.
