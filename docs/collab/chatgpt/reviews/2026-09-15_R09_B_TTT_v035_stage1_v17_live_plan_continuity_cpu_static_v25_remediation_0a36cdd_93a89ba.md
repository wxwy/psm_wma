# ChatGPT independent review — Stage-1 v1.7 live-plan continuity CPU/static V25 remediation

Formal pair:
- root: `0a36cdd85a97289ec6a2ff6ce0e62d8fe7419090`
- child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-LIVE-PLAN-CONTINUITY-CPU-STATIC-V25-REMEDIATION`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/stage1_v17_pre_c_rehearsal.py:435)`

Blockers: `3`
- Design/Authority document: `0`
- Production/implementation: `2 HIGH`
- Evidence: `1 MEDIUM`
- Scope/child/runtime: `0`

## Re-lock / target validity

- Pre-review `V2` advanced through request/delivery bookkeeping commits, but the declared formal implementation target remains `0a36cdd85a97289ec6a2ff6ce0e62d8fe7419090`.
- Formal root resolves `cosmos-framework` exactly to Gitlink `93a89ba61306d840a008813f62f26a34d54850f4`.
- Child `93a89ba61306d840a008813f62f26a34d54850f4` resolves independently in `wxwy/cosmos-framework`.
- Previous reviewed pair was `23087f8274567a99ee9751a63ba105f48c2f1845 / 93a89ba61306d840a008813f62f26a34d54850f4`; root changed, so this is a fresh technical target.

## Frozen authority used

Effective inherited authority remains V24 + V25:
- session/plan/lease are one same-lifetime triple;
- creation-time immutable object-token binding plus binding digest;
- exact review record carries triple identities/digest and the frozen consumer/guard/verifier, bytes, freshness, paths/environment, remote facts and designated absences;
- review-pending mutation/rebind/copy/serialize/direct consume/resume fail closed;
- verified resume proves current live authority equals the reviewed binding before releasing the original plan to the sole C path;
- identity/state drift, replacement or loss is terminal.

## Positive closure from prior review

The previous pair's three blockers are materially improved:
- caller-writable `_locked` switches are removed from the session/capability/guard/lease objects;
- dead `_LIVE_TOKENS` mirror state is removed;
- `_ContinuationBindingV1` now creates a session/plan/lease triple digest and `resume_once()` consults it;
- `audit_record()` now exposes triple identities plus digest;
- tests now cover normal set/delete, deepcopy/pickle, digest drift, duplicate ownership and apply-count-zero for those rejection paths.

Those changes close the exact `_locked` bypass and dead-token findings from `23087f8`, but they do not yet close the whole frozen authority class.

## HIGH 1 — independent approval can still be forged with the same public mutation primitive used by production

Location: `tools/psm_wma/stage1_v17_pre_c_rehearsal.py:433-435, 448-454`.

`LivePlanSessionV1.__setattr__` rejects ordinary `setattr`, but all legitimate state transitions are implemented with Python's public `object.__setattr__`. That primitive is equally callable by a holder of the session object and bypasses the custom `__setattr__` method.

A caller can therefore perform, before any call to `approve(...)`:

```python
approval = object()
object.__setattr__(session, "_approval", approval)
object.__setattr__(session, "_state", "APPROVED")
session.resume_once(session.lease, approval)
```

The creation-time triple is unchanged, so `_binding.matches(...)` remains true. `resume_once()` then releases `_LIVE_PLANS` and enters `consume_once_v05()` without the independent approval transition.

This is not hypothetical reflection outside the current model: the production code itself relies on `object.__setattr__` for state transitions, and the new test suite also invokes `object.__setattr__` directly to create binding drift.

Violated frozen contract: V25 pending rebind fail-close and separate approval transition; V24 requirement that only the unique verified resume-only authority can release the reviewed live plan.

Acceptance:
1. authorization to resume must not be synthesizable by writing `_state`, `_approval` or equivalent caller-visible session fields with standard Python mutation primitives;
2. use a transition/capability authority created only by the intended `approve(...)` path (or equivalent design) and validate it independently of caller-mutable session state;
3. add a direct causal witness attempting `object.__setattr__`/equivalent base mutation of approval/state before approval and prove terminal rejection with freshness/consumer/apply count `0`;
4. keep legitimate `approve -> exact lease + exact approval -> resume once` success and terminal repeat semantics.

## HIGH 2 — the binding proves object ids, not equality of the live plan authority to the exact review record

Locations: `tools/psm_wma/stage1_v17_pre_c_rehearsal.py:315-350, 436-454`.

`_ContinuationBindingV1` binds only `id(session)`, `id(plan)`, `id(lease)` and a token id. `matches()` recomputes only that tuple/digest. It does not bind or revalidate the authoritative contents of the reviewed plan/capability/guard/verifier.

Therefore authority-bearing content can drift while all three object ids and the binding digest remain unchanged. For example, standard base mutation can replace an existing slotted/dataclass field such as `capability.apply_opaque_v1`, `freshness_guard.guard_opaque_v1`, `plan.post_write_verify`, or other plan authority fields; the current triple binding still matches because the containing object identities did not change. C then consumes authority different from what the review record witnessed.

The read-only `audit_record()` is also still incomplete relative to V24. It includes the triple/digest, raw identities, freshness identities, paths/environment, partial capability/guard provenance and verifier qualname, but V24 explicitly requires the exact record to also bind the full consumer/guard/verifier provider/module/path/source-blob/callable/ABI/transport set plus C01-C15, remote facts and designated absences. The record is not subsequently compared by `resume_once()`.

Violated frozen contract: V24 exact-review-record equality before resume and terminal identity drift; V25 creation-time authority must bind the same reviewed live authority, not merely the outer Python object ids.

Acceptance:
1. create one immutable creation-time/review snapshot that canonically binds the complete still-inherited V24 authority surface, not just the triple ids;
2. include the complete required review fields in the audit/review witness, without reconstruction capability;
3. before ownership release, `resume_once()` must prove both triple identity and current authority/content equality to that creation-time reviewed snapshot;
4. mutations/substitutions of plan, capability, guard, verifier, lease/binding or any authority-bearing field must terminalize before freshness/consumer invocation with apply count `0`;
5. the binding/snapshot itself must not be forgeable by coherently rewriting its stored digest/token/fields.

## MEDIUM 3 — Evidence does not exercise the actual remaining bypass or full exact-record equality

Location: `tools/psm_wma/test_stage1_v17_pre_c_rehearsal.py:153-195`.

The new tests are useful but remain non-causal for the two HIGH findings:
- authority-field sealing is tested only through ordinary `setattr/delattr`, not the same `object.__setattr__` primitive production uses;
- binding drift mutates only `_digest` to an inconsistent value; it does not test coherent state/approval forgery, coherent binding rewrite, or authority-content drift while triple ids remain stable;
- audit testing checks only the three ids, a 64-hex digest and `PATHS`; it does not assert the complete V24 exact-review-record surface;
- no test proves that modifying capability/guard/verifier/plan authority content while preserving outer ids is rejected before C.

Acceptance: add direct production-object/API witnesses for the complete attack class above, with explicit zero freshness/consumer/apply count on every pre-resume rejection and one positive approved same-instance resume path.

## Blocker lifecycle

- Previous HIGH `_locked` caller-write/delete bypass: `CLOSED`.
- Previous HIGH dead `_LIVE_TOKENS` / no triple digest enforcement: `PARTIALLY CLOSED` — triple digest now exists and is checked, but it binds only object ids and is not the complete exact-review authority.
- Previous MEDIUM normal sealing/binding Evidence gap: `PARTIALLY CLOSED`; the remaining causal paths are listed above.
- New direct finding from the completed sealing-class sweep: approval/state forgery via `object.__setattr__`: `OPEN (HIGH)`.

## Scope reminder

This verdict binds only the exact formal pair above and this root-only pure-memory CPU/static remediation Gate. It does not authorize real pre-C/C, request-pair construction/write, materialization/source-evidence, real host/consumer/guard/Git/network/source/data/cache I/O, child/runtime/config mutation, GPU/CUDA/torchrun, training/evaluation/inference or LIBERO4IN1.
