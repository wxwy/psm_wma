# ChatGPT review — Stage-1 v1.7 live-plan continuity CPU/static V25 remediation

Formal pair:
- root: `079186e4c9b6ce1c221447119397c03ae11a8188`
- child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-LIVE-PLAN-CONTINUITY-CPU-STATIC-V25`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/stage1_v17_pre_c_rehearsal.py:366)`

## Result

Blockers: `1 HIGH`.

- Design/Authority: `0`
- Production/implementation: `1 HIGH`
- Evidence/Scope: `0`
- child/runtime: `0`

## Positive closure

- Formal root resolves and its root tree binds `cosmos-framework` mode `160000`, type `commit`, exactly to the declared child `93a89ba61306d840a008813f62f26a34d54850f4`; the child independently resolves.
- This pair remains root-only CPU/static continuity remediation; no real pre-C/C, request-pair write, materialization/source-evidence, child/runtime/config mutation, GPU or training is in scope.
- The prior duplicate-owner / close-retirement defect is partially closed: constructing a second live session for the same plan now fails `continuation_owner`, and `close()` retires the plan so the public consume path later fails `already_consumed`.
- A read-only `audit_record()` witness was added and is not used as a reconstruction input.

## HIGH 1 — the required PENDING → APPROVED transition still does not exist

The prior V25 review required an explicit state machine: `PENDING → APPROVED → CONSUMED`, with `INVALID/CLOSED` terminal states. A session that has merely been created must not be able to enter C until a distinct approval transition has occurred.

At the formal root, however:

- `__init__()` still creates `self._approval = object()` immediately;
- `approval_identity` still exposes that same object immediately while the session is review-pending;
- there is no `approve(...)` / authorization transition or `_state` field distinguishing PENDING from APPROVED;
- `resume_once()` only tests `lease is self._lease` and `approval_identity is self._approval`, then removes the pending marker and calls `_consume_once_v05(self._plan)`.

Therefore a caller can still perform, immediately after constructing the session:

`session.resume_once(session.lease, session.approval_identity)`

and enter the internal C path without any independent approval event. The remediation commit changed duplicate ownership and close retirement, but did not change this bypass.

The existing earlier positive test also encoded this forbidden behavior: create session → obtain `approval_identity` → resume directly, with no approval transition. The new remediation test does not replace that behavior with a PENDING rejection / explicit APPROVED witness.

## Required remediation

Close the full session-state class in one change:

1. Encode a real terminal state machine, e.g. `PENDING`, `APPROVED`, `CONSUMED`, `INVALID/CLOSED`.
2. Session creation must produce only PENDING state. No credential available at construction time may satisfy `resume_once()`.
3. Add one explicit approval transition that binds an independently supplied exact approval identity to the already-live session/plan/lease; invalid or repeated approval is terminal/fail-close.
4. `resume_once()` while PENDING must fail before `_consume_once_v05` with consumer/apply count `0`; only APPROVED may resume exactly once.
5. Preserve unique live-owner rejection, public `consume_once_v05(plan)` blocking while the owner is live, terminal retirement on close/mismatch/loss, no reconstruction, same live plan handoff and all inherited C01-C15/freshness/readback/no-retry semantics.
6. Add direct stdlib tests for: PENDING resume rejected with apply=0; explicit approval then same-plan resume once; foreign/repeated approval rejected; duplicate owner rejected; close/invalidation cannot reopen the public consume path.

No real pre-C/C, request pair, materialization/source-evidence, child/runtime/config mutation, GPU/CUDA/torchrun, training/evaluation/inference or LIBERO4IN1 is authorized by this pair.
