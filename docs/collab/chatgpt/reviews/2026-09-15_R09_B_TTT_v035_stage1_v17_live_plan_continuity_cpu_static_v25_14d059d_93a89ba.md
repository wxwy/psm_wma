# ChatGPT independent review — Stage-1 v1.7 live-plan continuity CPU/static V25

Formal pair:
- root: `14d059d940b1b9a6d1af59105e2a38c90c97c78a`
- child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-LIVE-PLAN-CONTINUITY-CPU-STATIC-V25`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/stage1_v17_pre_c_rehearsal.py:518)`

Blockers: `1 HIGH`; Design/Authority: `0`; Production/implementation: `1 HIGH`; Evidence/Scope: `0`; child/runtime: `0`.

## Positive closure

- The prior approval-state remediation remains correct: sessions start `PENDING`, `approve(external_identity)` transitions to `APPROVED`, and `resume_once()` requires the exact live lease plus bound approval identity.
- Duplicate live-owner rejection, terminal close/invalidation, read-only audit witness, and the public `consume_once_v05(plan)` live-owner block remain intact.
- The formal root tree binds `cosmos-framework` as mode `160000`, type `commit`, exactly to the declared independently reachable child.
- Scope remains root-only pure-memory CPU/static; no real pre-C/C, request-pair write, materialization/source-evidence, child/runtime/config mutation, GPU or training is executed or authorized.

## HIGH 1 — the new internal-entry token is directly readable and remains a bearer bypass

The prior review required that every C route for a live owned plan be gated by verified resume authority and that no module-level C primitive be callable using caller-obtainable continuation material.

This root changes `_consume_once_v05` to accept `_lease_token` and verifies it against `_LIVE_TOKENS[id(plan)]`. However:

- `ContinuationLeaseV1` stores the token as ordinary slot `_token`;
- `LivePlanSessionV1.lease` publicly returns the exact lease object;
- session construction stores `self._lease._token` in `_LIVE_TOKENS`;
- `_consume_once_v05(plan, _lease_token)` accepts that same raw object as sufficient continuation authority;
- therefore a caller holding `session` and `plan` can execute `pre_c._consume_once_v05(plan, session.lease._token)` while the session is still `PENDING`, bypassing `approve(...)` and `resume_once(...)` entirely.

Python underscore naming is not access control, so the bearer token is caller-obtainable. The added test only proves `_consume_once_v05(plan)` without a token rejects; it does not test the directly obtainable correct token.

## Required remediation

Close this direct-C-entry class without another caller-obtainable bearer credential:

1. No module-level C primitive may accept continuation authority that an ordinary caller can extract from the public session/lease object graph.
2. The only route for an owned live plan into C must be the verified `APPROVED` same-session resume path.
3. Prefer keeping one C implementation behind `consume_once_v05` and granting a non-extractable, one-shot authorization internal to the session/resume call; an equivalent closure/capability construction is acceptable.
4. Add a direct negative witness that even with access to the public `session`, `session.lease`, `plan`, and module object, no direct call can enter freshness/consumer before approved resume; apply count must remain `0`.
5. Then prove approved same-plan resume succeeds exactly once and remains terminal.
6. Preserve the already-correct approval transition, unique-owner rule, terminal invalidation, no reconstruction, C01-C15, nine-entry freshness domain, exactly-once/readback/no-retry and pure-memory scope.

This review does not authorize real pre-C/C, request-pair writing, materialization/source-evidence, child/runtime/config mutation, GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1.
