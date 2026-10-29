# Evaluation V2 Phase B r2 — Ticket ownership and Session End quiescence

Date: 2026-10-29. **DESIGN CANDIDATE; REQUEST INCREMENTAL APPROVE_DESIGN.**

## 1. Scope and exact authority

This r2 changes only the executable design/protocol representation of **B-D1 and B-D2**. All other r1 design sections remain as written in `PSM-WMA_V3_EvalV2_PhaseB_MultiSim_Transactional_Batch_Design_r1_2026-10-29.md`. This addendum takes precedence for Ticket ownership, cancellation, delivery ACK, Session End and resource release. The r1 frozen document and its evidence remain unchanged.

- Reviewed r1 Design Root: `fac029c83eb94fdafcc26d030ca5942542d740a3`.
- Unchanged production Root: `fd7e43f6630a436ab3d83edcd3ce9d1516b342d1`.
- Unchanged Child/Gitlink: `d2c1bda62880dbeee196f70945e5bc430b73f4b6`.
- Formal detailed review: `docs/collab/chatgpt/reviews/2026-10-29_V3_EvalV2_PhaseB_r1_fac029c8_d2c1bda6_Design_Gate_REQUEST_CHANGES.md`, `REQUEST_CHANGES`, fetched/read with matching latest canonical Inbox at V3 `b4cd955ab5b139ce344afd5e9a34750db215ca6d`.
- Isolated branch: `v3-eval-v2-batch-b-design-20261029`; the new Design Root is recorded in the separate author handoff/evidence once this source is committed. Evidence/documentation HEAD never substitutes for that Design Root.

No production code, model algorithm, generator, Local-TTT math, Child, Gitlink, training, checkpoint, Vendor, old431 or existing real evaluation is modified. Phase A source `APPROVE_CODE` is unchanged; independent DS CPU is still pending. No Phase B production implementation/merge/GPU/real model/RoboCasa/900/DS dispatch is authorized.

## 2. One lifecycle authority, including work no longer in the queue

`TicketRegistry` is the **same object** used by `BatchQueue`, `ProtocolModel.submit/execute` and Session End. It retains one canonical Request/payload, per-Slot reservation, encoded size, original arrival/deadline, batch membership, cancellation flag and quiescence state for each unresolved Ticket. `rows` is only a view of QUEUED entries; it is never a capacity or idle authority.

| Ticket state | Owner / allowed operation | Slot and byte credit |
| --- | --- | --- |
| QUEUED | Bounded admission; same-key/exact-payload attaches; new Frontier for same Slot rejected | Held |
| SEALED | Queue pop or exact complete ordered batch adoption; no subset/reordered batch adoption | Held |
| PREPARED | Model-owner Local candidates only; no published Fast State | Held |
| GENERATING | One model executor owns fake/native call; cancel only records intent | Held |
| GENERATED / VALIDATED | Full cardinality/finite/mapping/serialization validation and final cancellation fence | Held |
| COMMITTED, nonquiescent | Fast+visual+frontier+response bundle published; executor has not yet returned/unwound its ownership | Held; End/HTTP cannot release |
| COMMITTED, quiescent | Executor `finish(COMMITTED)` proves owned work returned; frozen response can be delivered/replayed unless cancelled | Held until client delivery ACK or owned End discard |
| ABORTED, quiescent | Executor `finish(ABORTED)` after no generation was entered or after its call returned/raised/unwound | Held until exact abort release |
| RELEASED | Exact terminal/quiescent Ticket released once; remove its registry-owned payload/reference | Returned once; replay response remains bounded in Session bundle |

Generation call return alone is not a caller-issued release. The conceptual model executor owns all `advance/finish` events; HTTP, timeout and Session End only request cancellation. A real implementation must use its actual model-owner task completion/CUDA drain proof or quarantine/decommission the owned Server; a Python flag or timeout is not native quiescence proof. The CPU model does not implement CUDA kernels or prove they have stopped.

`pop()` changes selected Tickets to SEALED and leaves them in the registry. Admission, count and bytes include **Queued + Sealed + all executor stages + Committed-undelivered**. Same-key/exact-payload duplicates return the same Ticket object and do not renew arrival, deadline or encoded-byte accounting, at every unresolved stage. Changed payload is rejected. A new Frontier waits until release of its predecessor; increasing a retry's deadline does not evade this restriction. Aggregate byte pressure still includes a popped batch.

Only the original complete ordered sealed group can be adopted by the executor. A failed seal/admission cleans up newly created QUEUED entries only, preserving every pre-existing sealed/inflight Ticket and its credits. Per-member release drops registry references immediately; a co-member waiting for delivery must not retain the released member's large request while its credit is already reissued. Final member release removes batch bookkeeping. Repeated release of the same exact receipt is a no-op and cannot release a newer Ticket; foreign owner/epoch/capability release is rejected.

## 3. Cancellation intent is not Session cleanup ACK

Session lifecycle is `OPEN -> CLOSING(cancel requested) -> WAIT_OWNERS -> CLOSED_ACK`. `request_cancel(lease)` returns no ACK and cannot delete state or free a reservation. `request_end(lease)` returns an explicit `EndReply(acknowledged=False)` while waiting. The reply is false in boolean context. `reset()` is retained only as a compatibility spelling returning that acknowledged flag; it no longer means unconditional success.

1. Validate exact Server epoch, Slot generation, Session/Episode ownership; mark this Session closing and cancel its outstanding Ticket, if any.
2. **Do not** complete, finish, release or delete an executing batch from End. If the single model executor is busy, or the Session has any nonquiescent Ticket, return deferred. Deferring even an unrelated idle Session's state cleanup while the model owner is busy prevents concurrent bundle replacement from invalidating another batch.
3. Cancellation before commit aborts the complete sealed batch. Candidates, Fast/visual/frontier and replay responses stay unchanged for every member. The executor releases aborted Tickets only after it has returned/unwound all owned work. An already queued cancelled Ticket can be aborted without invoking generation, but still needs an explicit executor drain event.
4. Cancellation after commit never rolls back committed co-members. Wait for executor quiescence. Then End may discard **its own** undelivered response/Ticket and remove **its own** Session state; other members' state, response and reservations remain intact. A cancelled Ticket must not be delivered even if its response was previously committed.
5. Only after the Session has zero unresolved ownership may cleanup close its generation and return positive ACK. The model demonstrates this with an explicit `poll_end`; native code can complete the pending End future on the same event, under its original bounded deadline.
6. Retain the exact closed-generation ACK receipt so its network loss can be retried. Replaying it does not open a Session, free another Ticket or close a newer generation. Root cannot assign another Episode/Task to this Slot before the positive ACK.

An uninterruptible/stalled generation cannot produce positive End ACK by expiring a request. Mark cancellation/quarantine and preserve reservations until authoritative owner completion or bounded owned-process decommission proof. Existing Root cleanup/epoch recovery remains the future production authority; this design does not substitute CPU symbolic state for that proof. A new Server epoch rejects old requests, End receipts and release capabilities.

## 4. Commit, delivery and credit release are distinct

The native transaction remains all-or-none before commit; the one publication owner remains responsible for Fast+Visual+Frontier+Response. Committing an action response does **not** prove HTTP delivery or execution. The r2 model's `execute()` commits and finishes the executor, while retaining Ticket credit. `deliver()` exposes the frozen reply only after quiescence, active lease checks and cancellation checks. `acknowledge()` represents client acceptance and releases that exact committed Ticket once.

Future Phase B transport adds a versioned response-acceptance ACK to the r1 data-plane specification: exact inference identity, unchanged payload binding, current lease/epoch. The client checks response identity and fences, sends/retries this bounded idempotent ACK, and executes actions at most once. This is a resource/ownership handshake, not a new inference or a change to policy actions. Root still requires Session End ACK before Slot reuse.

- Lost response: duplicate HTTP/poll attaches to the same committed Ticket or bounded replay cache, never regenerates or rescans. Its count/bytes stay reserved until accepted or explicitly discarded.
- Lost delivery ACK: retry the same ACK; repeated release does not corrupt credit or affect a later Frontier. Bounded last-response cache still supports exact replay after release. An evicted old Frontier is rejected, never regenerated.
- Timeout at any unresolved stage: mark cancellation, retain reservations, preserve diagnostic; no credit return and no cleanup ACK from the timer. A registry-originated cancellation after commit must also prevent `cached()/deliver()` or execute-replay from exposing that response. It cannot be ignored merely because Fast State was committed.
- After commit/before delivery: a new Frontier for the same physical Slot is rejected. The old duplicate still attaches. After delivery ACK, a legitimate next Frontier may be admitted; the previous response remains in bounded cache until advancement.

Encoded-request credits apply to live registry-owned payload. Batch metadata cannot retain a freed payload secretly; candidate tensors, decoded inputs, actions/cache and optional media remain separate bounded allocations from r1. The limits cannot be presented as proof of actual H100 memory capacity.

## 5. Deterministic design evidence

Old r1 is frozen and preserved. Three expected RED tests import only `git show fac029c8:.../protocol_model.py` copied to an external temporary directory:

1. End ACK and new Slot assignment inside prepublication while old batch is still owned.
2. Same request after pop treated as a new ticket instead of attachment.
3. New Frontier admitted for a popped, still unresolved physical Slot.

The raw old-source Git/SHA256 binding, counterexample source, JUnit, command and logs are archived separately as expected failing **r1** evidence. They are not a failing r2 Gate and are not production experiments.

The final r2 isolated suite retains r1's29 test cases with explicit delivery ACKs and replaces its incorrect reset-as-cancel witness with a dedicated cancellation request. Additional tests exercise:

- Queued End/drain; after pop before prepare using the **same registry**; each prepared item, all prepared, before/inside/after Generation, validated/prepublication, postcommit/nonquiescent and final quiescence.
- Deferred End denies new assignment/frontier; no cleanup/state deletion before drain; cancellation cannot return credit. Abort preserves co-member Fast/visual/frontier/cache state. Postcommit End discards only its own reply and does not damage the co-member.
- Client response/ACK loss, closed End ACK loss, old-generation/epoch/foreign ownership, timeout during Generation without fabricated drain, and registry-originated timeout after commit without late delivery.
- Duplicates at every unresolved stage, unchanged arrival/deadline/size, aggregate queued+inflight bytes, new Frontier denial, partial B1/2/3/B>M, exact seal adoption, terminal reason checks, exact-once credit return and no retained freed-member payload in live batch metadata.
- Single vector call/sample mapping, cold/hot symbolic prefixes, immutable W0/independent symbolic fast values and literal seed mapping remain existing design witnesses. These are not real torch/CUDA/Local-TTT/HTTP/physics tests.

Final counts and exact new Design Root are in the author handoff and raw JUnit, not predeclared as a native pass. No Phase A255 rerun is needed because no production code changes. A later production implementation still needs its own actual-module CPU tests, exact implementation Pair, GPT Code Gate, DS independent CPU and separately authorized native Canary.

## 6. Reproduction and Gate decision request

Working directory `/workspace/psm_wma`. No Checkpoint, model, dataset or simulator input. All Python files in `tools/v3/eval_v2_batch_design/` are isolated stdlib/pytest design artifacts with no production import path. Full author commands/environment/hashes are archived under `docs/collab/codex/evidence/2026-10-29_eval_v2_phase_b_design_r2_author_cpu/`.

```bash
env CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  PYTHONDONTWRITEBYTECODE=1 \
  HF_HOME=/tmp/psm-eval-v2-phase-b-r2-20261029/cache/hf \
  MPLCONFIGDIR=/tmp/psm-eval-v2-phase-b-r2-20261029/cache/mpl \
  XDG_CACHE_HOME=/tmp/psm-eval-v2-phase-b-r2-20261029/cache/xdg \
  /workspace/.venvs/psm-wma-cpu/bin/python -m pytest \
  --noconftest -c /dev/null --rootdir=/workspace/psm_wma \
  -p no:cacheprovider -q tools/v3/eval_v2_batch_design \
  --junitxml=/tmp/psm-eval-v2-phase-b-r2-20261029/final/junit.xml
```

PASS requires final zero failures/errors/skips, Ruff0.12.7 check/format, AST checks, production tree/Gitlink/Child unchanged and source/artifact hash verification. Review request is **incremental APPROVE_DESIGN / REQUEST_CHANGES for B-D1/B-D2**, not source Code or GPU approval. Codex stops after isolated candidate publication/readback. Phase A independent DS CPU remains a separate unchanged-pair task.
