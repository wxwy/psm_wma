# ChatGPT independent review — Stage-1 v1.7 live-plan continuity CPU/static V25 remediation

Formal pair:
- root: `9c027a346320b0cb8e8445ada1e1a277efb0b875`
- child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-LIVE-PLAN-CONTINUITY-CPU-STATIC-V25-REMEDIATION`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/stage1_v17_pre_c_rehearsal.py:484)`

Blockers: `3`
- Design/Authority document: `0`
- Production/implementation: `2 HIGH`
- Evidence: `1 MEDIUM`
- Scope/child/runtime: `0`

## Re-lock / target validity

- Pre-review `V2` HEAD is request/bookkeeping commit `b80cc461d7d4e33936ba0aee1214d685b269d7f4`, whose parent is the declared formal root `9c027a346320b0cb8e8445ada1e1a277efb0b875`.
- `CODEX_INBOX.md` explicitly requests this exact pair and this Gate.
- Formal root resolves `cosmos-framework` exactly to Gitlink `93a89ba61306d840a008813f62f26a34d54850f4`.
- Child `93a89ba61306d840a008813f62f26a34d54850f4` resolves independently in `wxwy/cosmos-framework`.
- Previous reviewed pair was `0a36cdd85a97289ec6a2ff6ce0e62d8fe7419090 / 93a89ba61306d840a008813f62f26a34d54850f4`; root changed, so this is a fresh technical target.

## Frozen authority used

Effective inherited authority remains V24 + V25. The relevant requirements are still:
- session/plan/lease form one same-lifetime reviewed triple;
- pending direct consume/resume/rebind/copy/serialize fail closed;
- approval is a distinct authority transition and cannot be synthesized by ordinary caller mutation;
- the exact review record binds session/plan/lease identities + digest and the complete reviewed consumer/guard/verifier, sealed request identities, C01-C15, nine-entry freshness domain, paths/environment, remote facts and designated absences;
- verified resume proves current live authority equals that exact reviewed record before releasing the original plan to the sole C path;
- any drift/replacement/loss is terminal.

## Positive closure from `0a36cdd...`

The new pair makes real progress:
- `_approval` and `_state` are no longer session slots, so the exact previous `object.__setattr__(session, ...)` forgery path is closed;
- `_authority_snapshot(plan)` now captures substantially more of the live authority surface;
- `_ContinuationBindingV1.matches()` recomputes the snapshot and compares it before resume;
- the new test directly exercises the prior session-slot forgery and one capability-callable drift path with zero apply;
- scope remains root-only pure-memory CPU/static.

Those changes close the exact prior session-slot bypass, but the moved authority is still caller-mutable and the snapshot is still not the complete immutable V24 review record.

## HIGH 1 — live approval/binding/admission authority is stored in caller-mutable module registries

Location: `tools/psm_wma/stage1_v17_pre_c_rehearsal.py:483-485` (root cause), with uses in `approve()`, `resume_once()` and `consume_once_v05()`.

The implementation moves authority out of the session object into three module-level mutable containers:

- `_LIVE_PLANS: set[int]`
- `_LIVE_AUTHORITIES: dict[int, tuple[object | None, str]]`
- `_LIVE_BINDINGS: dict[int, _ContinuationBindingV1]`

These are ordinary Python objects reachable from the module namespace. The test suite itself imports the module and directly accesses `_LIVE_BINDINGS`, so module-level underscore names are demonstrably within the exercised caller surface rather than an opaque host boundary.

This creates multiple direct authority bypasses:

1. **Pending direct-C bypass**
   - create `plan` and `session` normally;
   - call `rehearsal._LIVE_PLANS.discard(id(plan))`;
   - call `consume_once_v05(plan)`.
   - The public C function's pending guard is now cleared without `approve()` or `resume_once()`.

2. **Approval forgery**
   - `approval = object()`;
   - assign `rehearsal._LIVE_AUTHORITIES[id(session)] = (approval, "APPROVED")`;
   - call `session.resume_once(session.lease, approval)`.
   - The untouched creation-time binding still matches, so the forged registry state is sufficient to pass the approval check.

3. **Binding replacement / coherent rewrite**
   - `_LIVE_BINDINGS[id(session)]` can be replaced directly with another binding object, including one created after authority drift.

Therefore the previous HIGH was moved rather than closed: authorization is no longer forgeable via session slots, but it is forgeable through the newly authoritative module registries. This also means `_LIVE_PLANS` remains a caller-controlled gate in front of the sole C path.

Violated frozen contract: V24 pending direct consume fail-close; V25 distinct approval transition; unique verified resume-only release of the reviewed live plan.

Why current Evidence does not close it: the new base-mutation test attacks removed session attributes, but never mutates the actual authoritative registries. No test attempts `_LIVE_PLANS.discard(...)`, `_LIVE_AUTHORITIES[...] = ...`, or `_LIVE_BINDINGS[...] = ...` and proves zero freshness/consumer/apply.

Acceptance — close the whole live-registry class in one pass:
1. no caller-reachable mutable module container may be the authority for pending admission, approval state or reviewed binding;
2. clearing/replacing any externally reachable bookkeeping must not make `consume_once_v05(plan)` or `resume_once(...)` succeed;
3. only the intended `approve(...) -> exact reviewed resume_once(...)` route may release an owned live plan into C;
4. add direct negative witnesses for registry/bookkeeping tamper attempts, including the current module namespace, with freshness/consumer/apply count `0`;
5. preserve duplicate-owner rejection, terminal close/loss/repeat semantics and exactly-once C.

## HIGH 2 — `_authority_snapshot` is not yet the complete immutable V24 exact-review record

Locations: `tools/psm_wma/stage1_v17_pre_c_rehearsal.py:414-432` and `_ContinuationBindingV1.audit_fields()/matches()`.

The new snapshot is materially broader, but it still does not equal the frozen V24 record surface:

- verifier is represented only as `(post_write_qualname, id(post_write_verify))`; V24 explicitly requires the reviewed verifier's provider/module/path/source-blob/callable/ABI/transport identity, and those fields are neither carried nor checked here;
- the audit witness does not explicitly bind/list the inherited `C01-C15` contract set required by V24;
- `local_authority_absence` / `remote_authority_absence` are reduced to byte length/SHA only, omitting the authority target/predicate that V24 requires as part of the reviewed remote/absence truth;
- `plan.descriptor` and `closure.replay_binding` are inserted as object references rather than detached canonical primitive identity tuples. The returned audit record therefore contains live dataclass objects, not a fully detached immutable review witness.

The digest does catch some uncoordinated drift because `repr(snapshot)` changes, but that is not equivalent to exact review-record equality: the complete required fields are not present, and HIGH 1 allows the live binding/registry itself to be coherently replaced after drift.

Violated frozen contract: V24 exact-review-record completeness and equality before resume; V25 requirement that resume prove the same reviewed authority, not only a locally generated partial snapshot.

Why current Evidence does not close it: `test_live_session_close_and_duplicate_owner_fail_closed` checks only the three ids, digest format and one PATHS position. It never asserts the full V24 record. The callable-drift test covers only `capability.apply_opaque_v1`; it does not prove verifier provenance, authority-absence target/predicate, C01-C15, replay-binding canonicalization or full record equality.

Acceptance:
1. define one detached canonical primitive snapshot/record containing the complete still-inherited V24 authority surface;
2. include full consumer + guard + verifier provider/module/path/source-blob/callable/ABI/transport identities, sealed bytes/pair identities, C01-C15, nine-entry freshness identities, paths/environment, remote/query facts, authority absences, designated absences, replay binding and frozen targets;
3. do not place live mutable dataclass/object references in the audit record; use canonical primitive values/digests sufficient for equality but not reconstruction;
4. `resume_once()` must compare current live authority against that exact creation-time reviewed snapshot before ownership release;
5. any authority-field drift must terminalize before freshness/consumer/apply with count `0`.

## MEDIUM 3 — Evidence misses the new real authority surface

Location: `tools/psm_wma/test_stage1_v17_pre_c_rehearsal.py:153-207`.

The new tests correctly close several prior gaps, but they are not causal for the two remaining HIGHs:
- they attack removed session slots rather than `_LIVE_AUTHORITIES`;
- they directly mutate `_LIVE_BINDINGS` only to corrupt its digest, but never replace the registry entry coherently;
- they never clear `_LIVE_PLANS` then call the public C entrypoint;
- they do not assert the complete audit-record field set from V24;
- they do not drift verifier/descriptor/replay/authority-absence fields and prove zero apply;
- the reported `19/19 PASS` therefore does not witness that only the approved reviewed path can enter C.

Acceptance: add direct production-object/module witnesses for all authoritative state actually used by the implementation. Tests must fail if registry protection, full-snapshot comparison or ordering is removed, and every rejected pre-resume path must prove freshness/consumer/apply count remains `0`.

## Blocker lifecycle

- Prior HIGH — session-slot `object.__setattr__` approval forgery: `CLOSED` for that exact path.
- Prior HIGH — complete reviewed authority snapshot: `PARTIALLY CLOSED`; snapshot exists but is incomplete/non-detached and sits behind mutable registry authority.
- Prior MEDIUM — Evidence for authority drift: `PARTIALLY CLOSED`; callable drift is covered, but actual registry tamper and full-record equality are not.
- New completed-class finding — module-level mutable live registries allow direct pending/approval/binding bypass: `OPEN (HIGH)`.

## Scope reminder

This verdict binds only this exact formal pair and the root-only pure-memory CPU/static remediation Gate. It does not authorize real pre-C/C, request-pair construction/write, materialization/source-evidence, real host/consumer/guard/Git/network/source/data/cache I/O, child/runtime/config mutation, GPU/CUDA/torchrun, training/evaluation/inference or LIBERO4IN1.
