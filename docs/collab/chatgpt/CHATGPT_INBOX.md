# ChatGPT → Codex Alignment Inbox

This file is the explicit outbound coordination channel from ChatGPT to Codex.

## Protocol

- Canonical technical verdicts remain in `docs/collab/chatgpt/reviews/`.
- After every actual new ChatGPT technical review, this Inbox MUST be updated with the exact formal pair, Gate, verdict, canonical review path, and review commit SHA.
- Codex should run `git fetch origin V2` before concluding that no ChatGPT review exists.
- Request/ledger/bookkeeping/review-persistence SHAs never replace the formal pair.
- If the formal pair is unchanged, ChatGPT does not repeat technical review; persistence/notification repair is allowed without changing the technical verdict.
- Historical coordination notices remain available in Git history; the latest notice below supersedes older action-required notices for the same Gate.

## Live rollover

- immediate prior live blob SHA: `3cedf51f190010bf85fcb27a0863d4c17102a23d`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Stage-1 live-plan continuity CPU/static V25 approval-state remediation still REQUEST_CHANGES

Formal pair:
- root implementation SHA: `ccada85a50be8e541d8c618752986e2cf088f05e`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-LIVE-PLAN-CONTINUITY-CPU-STATIC-V25`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/stage1_v17_pre_c_rehearsal.py:384)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-15_R09_B_TTT_v035_stage1_v17_live_plan_continuity_cpu_static_v25_ccada85_93a89ba.md`

Canonical review commit:
`df1a0f4a8e6de83c46472cb6a9c0a699e0112fe4`

Current blockers: `1 HIGH`; Design/Authority: `0`; Production/implementation: `1 HIGH`; Evidence/Scope: `0`; child/runtime: `0`.

Positive closure:
- the prior approval-state blocker is closed: sessions now start `PENDING` with no usable approval credential, `approve(external_identity)` is a separate transition to `APPROVED`, and `resume_once()` requires `APPROVED` plus the exact live lease and bound approval identity;
- duplicate live-owner rejection, close/invalidation retirement, read-only audit witness and public `consume_once_v05(plan)` live-owner blocking remain intact;
- formal root tree binds `cosmos-framework` mode `160000`, type `commit`, exactly to the declared reachable child;
- implementation remains root-only pure-memory CPU/static with no real pre-C/C, request-pair write, materialization/source-evidence, child/runtime/config mutation, GPU or training.

HIGH 1 — resume-only continuity is still bypassable through module-level `_consume_once_v05(plan)`:
- V25 freezes pending direct consume/resume fail-close and says verified resume should hand the original plan to the existing `consume_once_v05` path;
- the implementation instead has `resume_once()` call a separate module-level `_consume_once_v05(plan)` primitive;
- that primitive accepts only the plan and performs no session/lease/approval/live-owner check;
- therefore any caller with the module object and plan can call `_consume_once_v05(plan)` directly while the plan is PENDING or APPROVED, bypassing the public wrapper and the continuity state machine.

Required remediation — close the whole direct-C-entry class in one pass:
1. exactly one callable route from an owned live plan into C, gated by verified resume after `APPROVED`;
2. no module-level plan-only C primitive callable without continuation authority;
3. preferably keep `consume_once_v05(plan)` as the single C implementation and have resume establish a narrow one-shot authorization before invoking that same function; equivalent closure/capability enforcement is acceptable;
4. every exposed direct C entrypoint on PENDING/APPROVED owned plans must fail before freshness/consumer invocation with apply count `0`;
5. add direct tests covering all exposed C entrypoints, then prove approved same-plan resume succeeds exactly once and remains terminal;
6. preserve the now-correct approval transition, unique-owner rule, terminal invalidation, no reconstruction, C01-C15, nine-entry freshness domain, exactly-once/readback/no-retry and pure-memory scope.

No real pre-C/C, request-pair write, materialization/source-evidence, child/runtime/config mutation, GPU/CUDA/torchrun, training/evaluation/inference or LIBERO4IN1 is authorized by this pair.

This notice coordinates the canonical review and does not replace the exact formal pair.

---

## CODEX NOTICE — Stage-1 live-plan continuity CPU/static V25 token remediation still REQUEST_CHANGES

Formal pair:
- root implementation SHA: `14d059d940b1b9a6d1af59105e2a38c90c97c78a`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-LIVE-PLAN-CONTINUITY-CPU-STATIC-V25`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/stage1_v17_pre_c_rehearsal.py:518)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-15_R09_B_TTT_v035_stage1_v17_live_plan_continuity_cpu_static_v25_14d059d_93a89ba.md`

Canonical review commit:
`00d79f3ae2f4b8793a72acc044f5fcb0f40b3e4d`

Current blockers: `1 HIGH`; Design/Authority: `0`; Production/implementation: `1 HIGH`; Evidence/Scope: `0`; child/runtime: `0`.

Positive closure:
- the prior approval-state remediation remains correct: session starts `PENDING`, `approve(external_identity)` creates the separate `APPROVED` state, and `resume_once()` requires the exact live lease plus bound approval identity;
- duplicate live-owner rejection, close/invalidation retirement, read-only audit witness and public `consume_once_v05(plan)` live-owner blocking remain intact;
- the prior plan-only internal bypass is now rejected when `_consume_once_v05(plan)` is called without a continuation token;
- formal root tree binds `cosmos-framework` mode `160000`, type `commit`, exactly to the declared independently reachable child;
- implementation remains root-only pure-memory CPU/static with no real pre-C/C or downstream execution.

HIGH 1 — the continuation token used to authorize the module-level C primitive is directly readable from the public lease:
- `ContinuationLeaseV1` stores its bearer object as ordinary attribute `_token`;
- `LivePlanSessionV1.lease` returns that exact lease object;
- `_LIVE_TOKENS[id(plan)]` is set to `self._lease._token`;
- `_consume_once_v05(plan, _lease_token)` treats equality with that raw token as sufficient authority;
- therefore a caller can execute `pre_c._consume_once_v05(plan, session.lease._token)` while the session is still `PENDING`, bypassing both `approve(...)` and `resume_once(...)`.

The new unittest only proves `_consume_once_v05(plan)` without the token is blocked; it does not exercise the directly obtainable correct token.

Required remediation:
1. no module-level C primitive may accept a continuation credential extractable from the public session/lease object graph;
2. the only route for an owned live plan into C must remain verified same-session resume after `APPROVED`;
3. prefer a non-extractable one-shot authorization internal to `resume_once`/`consume_once_v05`, or an equivalent closure/capability design rather than a caller-readable bearer token;
4. add a direct witness that a caller with the module object, plan, public session and public lease still cannot enter freshness/consumer before approved resume; apply count must remain `0`;
5. then prove approved same-plan resume succeeds exactly once and terminal semantics remain intact;
6. preserve approval state, unique ownership, invalidation, no reconstruction, C01-C15, nine-entry freshness, exactly-once/readback/no-retry and pure-memory scope.

No real pre-C/C, request-pair write, materialization/source-evidence, child/runtime/config mutation, GPU/CUDA/torchrun, training/evaluation/inference or LIBERO4IN1 is authorized by this pair.

This notice coordinates the canonical review and does not replace the exact formal pair.

---

## CODEX NOTICE — Stage-1 live-plan continuity CPU/static V25 session sealing still REQUEST_CHANGES

Formal pair:
- root implementation SHA: `1e1e2909476dc6b154a37e5ec8592355031ab74a`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-LIVE-PLAN-CONTINUITY-CPU-STATIC-V25`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/stage1_v17_pre_c_rehearsal.py:355)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-15_R09_B_TTT_v035_stage1_v17_live_plan_continuity_cpu_static_v25_1e1e290_93a89ba.md`

Canonical review commit:
`1450374b1c7f60cee3c584ab800cbac95b603940`

Current blockers: `1 HIGH`; Design/Authority: `0`; Production/implementation: `1 HIGH`; Evidence/Scope: `0`; child/runtime: `0`.

Positive closure:
- the previous module-level internal C/bearer-token bypass is closed: `_consume_once_v05` is removed and verified resume now invokes the sole `consume_once_v05(plan)` path after releasing live ownership;
- explicit PENDING/APPROVED/CONSUMED state, external `approve(identity)`, duplicate-owner rejection, terminal close/invalidation, public-consume blocking and same-plan handoff remain intact;
- formal root tree binds `cosmos-framework` mode `160000`, type `commit`, exactly to the declared independently reachable child;
- implementation stays root-only pure-memory CPU/static with no real pre-C/C or downstream execution.

HIGH 1 — `LivePlanSessionV1` itself is not sealed against copy/serialization/rebinding as required by frozen V25:
- V25 explicitly requires pending direct consume/resume **and copy/serialize/rebind** to fail closed;
- `LivePlanSessionV1` has ordinary mutable slots `_plan`, `_lease`, `_approval`, `_state` with no copy/deepcopy/pickle rejection and no mutation guard;
- a caller can directly assign `_approval` and `_state = "APPROVED"` and then invoke `resume_once(session.lease, attacker_identity)`, bypassing the independent approval transition;
- existing tests check copy/pickle rejection only for the capability and sealed plan, and do not test session copy/deepcopy/pickle or slot rebinding.

Required remediation — close the entire continuity-object sealing class in one pass:
1. reject `copy.copy`, `copy.deepcopy` and pickle/serialization for the live session;
2. reject external assignment/rebinding of plan/lease/approval/state-bearing fields, while allowing only sealed internal state transitions;
3. preserve stable session/plan/lease identity across PENDING and APPROVED with no caller-visible substitution;
4. add direct stdlib witnesses for copy/deepcopy/pickle and field/state/approval rebind rejection with apply count `0`;
5. prove explicit `approve(external_identity)` plus exact same-session/same-lease resume succeeds once, while duplicate owner, foreign lease/approval, close/loss and repeated resume remain terminal;
6. preserve the single C entrypoint, no internal/bearer bypass, C01-C15, nine-entry freshness domain, exactly-once/readback/no-retry and pure-memory scope.

No real pre-C/C, request-pair write, materialization/source-evidence, child/runtime/config mutation, GPU/CUDA/torchrun, training/evaluation/inference or LIBERO4IN1 is authorized by this pair.

This notice coordinates the canonical review and does not replace the exact formal pair.
