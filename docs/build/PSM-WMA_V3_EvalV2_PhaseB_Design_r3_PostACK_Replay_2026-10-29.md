# Evaluation V2 Phase B r3 — replay-aware admission after Delivery ACK

Date: 2026-10-29. **DESIGN CANDIDATE; REQUEST B-D3 INCREMENTAL APPROVE_DESIGN.**

## Scope and authority

The exact r2 review of Design Root `8f94b67ef3f049f5905ee35d54083d5f69534975` / Child `d2c1bda62880dbeee196f70945e5bc430b73f4b6` closed B-D1 and B-D2 and raised only B-D3. Review: `docs/collab/chatgpt/reviews/2026-10-29_V3_EvalV2_PhaseB_r2_8f94b67e_d2c1bda6_Incremental_Design_Gate_REQUEST_CHANGES.md`; freshly fetched canonical V3/inbox at `70aebb5cc69f9b2f65b20440d0fa093eb31bcbe8`.

This addendum changes only the symbolic public admission sequence needed to fix B-D3. Frozen r1/r2 designs and evidence remain preserved and normative everywhere else. No TicketRegistry, End/quiescence, model algorithm, source layout, action ABI, D1–D5, media, sampling or training contract is redesigned. Source Phase A Root `fd7e43f6630a436ab3d83edcd3ce9d1516b342d1` and Child/Gitlink remain unchanged; production required-mode Batch stays unsupported. No production code is implemented or merged.

## One replay-aware public admission authority

`ProtocolModel.submit` models the complete public `POST /v2/inference` admission authority. Its result is one of:

| Condition | Public result | Resource effect |
| --- | --- | --- |
| Wrong/closed/stale lease or Server epoch | Reject | No allocation |
| Same committed identity, different payload in bounded cache | Reject before registry admission | No allocation or existing-ticket change |
| Same identity/exact payload still has an unresolved Ticket | Same original Ticket, including committed-but-undelivered or draining | No new count/bytes; no deadline/size renewal; delivery still requires existing fences/quiescence |
| Ticket released, exact committed response retained | Original immutable `Response` | No Ticket, batching, encode/scan/generation, credit or deadline change |
| No retained response and requested Frontier <= committed Frontier | Reject stale/evicted evidence Frontier before admission | No ghost reservation or generation |
| New eligible Frontier | Registry admission under existing bounds | One new Ticket; predecessor's unresolved Slot reservation still blocks it |

The order is lease validation, committed-cache payload validation, existing-Ticket attachment, available-Session check, retained-response replay, stale-Frontier rejection, then new registry allocation. This preserves pending duplicates while a Session is closing without making an action response deliverable after cancellation. The existing `cached()/deliver()` readiness/cancellation checks are unchanged.

Raw `TicketRegistry.submit/add` remain internal allocation primitives with no response-cache authority. A future production HTTP handler must use the complete replay-aware path; it may not expose a parallel queue-only admission bypass. An already-committed `Response` bypasses new queueing entirely. Existing `execute()` cached replay remains valid but is never used to settle a newly allocated replay Ticket, because that Ticket is no longer created.

## ACK and bounded replay semantics

Required continuous sequence: `submit(R0) -> execute(R0) -> DeliveryACK(R0) -> submit(R0) -> same cached response -> DeliveryACK(R0) -> submit(R1)`. R0's original Ticket is released once; all late matching POSTs within the retained response window return the same response. A second R0 ACK is idempotent and cannot release an R1 Ticket, including while R1 is QUEUED. A changed-payload R0 is rejected before calling the allocator, even while R1 owns the physical Slot.

When R1 commits, the existing bounded last-response policy evicts R0. Identical or mutated old R0 POSTs are rejected from the committed Frontier before any registry call, both before and after R1's ACK. No old result is recreated. Outside that retained window, an old ACK still follows the prior r2 fail-closed behavior (`no committed response`) and cannot alter R1's ownership; this does not introduce an unbounded ACK/history store. A next valid R2 remains admissible. Valid retained replay never resets a request budget or delays another Session.

All old End/deferred-ACK, cancelled-response, exact-release and Server-epoch fences remain in force. Response replay is not another action execution: the future native client must still perform the existing request/frontier checks and at-most-once action acceptance.

## Evidence and regression scope

Only `tools/v3/eval_v2_batch_design/protocol_model.py::submit` changes existing protocol code. New `replay_admission_test.py` exercises the full public operation, not a cache-helper-only shortcut:

- ACKed R0 late POST returns identical response, repeated execute does not generate, ACK remains idempotent, and R1 then progresses.
- R0 replay and ACK while R1 is queued leave R1 and another Session's state/response/Ticket/count/bytes unchanged.
- Same-key changed noise/evidence/profile payload after R0 ACK is rejected before allocator invocation, both with and without R1 already queued.
- Identical/mutated evicted R0 is rejected before allocation after R1 advancement, before and after R1 ACK; no obsolete ACK releases R1 and R2 can be admitted.
- Existing unresolved duplicates attach at QUEUED/SEALED/GENERATING/COMMITTED without renewing budgets; closed/restarted leases cannot replay.

The exact same16 new tests are first run against frozen r2 model bytes, yielding11 expected RED failures and5 passing controls, then against the narrow fix. Raw r2 source Blob/SHA256, unchanged test SHA256, commands, JUnit and traces are preserved. Final isolated suite also includes all74 prior tests unchanged. Counts, source SHA and final Design Root are bound in separate author evidence/handoff after committing this design. No existing test is skipped, removed or weakened.

Author commands use `/workspace/.venvs/psm-wma-cpu/bin/python -m pytest --noconftest -c /dev/null --rootdir=/workspace/psm_wma -p no:cacheprovider`, CUDA hidden and model network flags offline, with caches/logs/JUnit under `/tmp/psm-eval-v2-phase-b-r3-20261029`. Inputs are only symbolic tuples/fake clock/fake vector, not Checkpoints, models, datasets or physics. Ruff0.12.7 check/format, AST and protected-source/Gitlink checks remain required. Evidence: `docs/collab/codex/evidence/2026-10-29_eval_v2_phase_b_design_r3_author_cpu/`.

## Gate request and STOP

Request incremental `APPROVE_DESIGN / REQUEST_CHANGES` only for B-D3 on the new Formal Design Root and unchanged Child/Gitlink; do not reopen closed B-D1/B-D2 without new evidence. No symbolic result is native Local-TTT, HTTP, CUDA/EGL, capacity or throughput proof. Phase A source `APPROVE_CODE` remains exact-pair only and its independent DS CPU is pending. Codex stops after isolated candidate publication/readback; Phase B production implementation, V3/Child merge, GPU/model/RoboCasa/DCP/900, DS dispatch and training/history operations remain unauthorized.
