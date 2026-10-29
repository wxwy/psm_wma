# Phase B increment 1 — Session transaction and B=1 integration

Date2026-10-29. **Isolated implementation candidate; REQUEST SOURCE CODE GATE.**

## Frozen authority and scope

- Approved design: Root `b9c7cf1607ffd38f6e3349bdde0b35703a6d7684` / Child `d2c1bda62880dbeee196f70945e5bc430b73f4b6`; r1 design plus r2/r3 addenda. Exact `APPROVE_DESIGN` was fetched/read at V3 `3f37df1fdda858482387f0f5db2c50be65a2f695` with detailed review and canonical Inbox. B-D1/B-D2/B-D3 are closed design findings, not inherited implementation approval.
- Production baseline: Phase A Root `fd7e43f6630a436ab3d83edcd3ce9d1516b342d1` / same Child, `APPROVE_CODE` source only. Its independent DS CPU remains pending.
- New Root/Child branch: `v3-eval-v2-transactions-b1-20261029`. Exact implementation SHAs are bound in separate author handoff/evidence after commits; later docs HEAD is never the Formal Implementation Root.
- This is **increment1 only**: real inference state publication, owned Session/Ticket lifecycle, B1 native service adapter and bounded RPC client. No M>1 Sim runtime, microbatch/native B>1, media jobs or complete evaluation-launcher integration. Those remain increment2 after this Code Gate.

Training, optimizer, DCP, scheduler/RNG, official generator/attention equations, Vendor/physics, dataset, G1, old431 and prior results are untouched. No merge-to-V3/Child, GPU/model load/real RoboCasa/EGL/DCP/900 or DS dispatch is authorized or performed.

## Production source architecture

| Component | Responsibility |
| --- | --- |
| Child `inference/local_memory_state.py` | Immutable snapshot of Fast records, visual records and bounded serialized last responses; one pointer publication under shared lock |
| Child `inference/local_memory_online.py` | Existing model-owned scan and validation; prepared state clones prevent aliasing with committed state; standalone API preserved; paired fast-only commit/reset rejected |
| Child `inference/robocasa_local_memory_policy.py` | Existing corrected composite encode/evidence parsing; one atomic Fast+visual+response commit, exact pending capabilities, whole-Session reset |
| Child `inference/robocasa_session_transactions.py` | One model-owner thread, per-physical-Slot reservation through queued/inflight/committed-undelivered, lease epoch/generation/capability, replay-aware admission, deferred End, error evidence and fail-closed quarantine |
| Child `inference/robocasa_transaction_client.py` | Versioned register/submit/poll/delivery-ACK/end; immutable retry payload, absolute original deadlines, response/Local/H16/raw15 validation; transport loss retries without recompute |
| Child `scripts/action_policy_server_robocasa.py` | Explicit opt-in profile, bounded HTTP dispatch, calls existing native preprocessing/action-processing/generation with one prefix entry and literal seed, performs device drain |
| Root `tools/v3/run_eval_v2_transactions_b1_cpu_gate.py` | Read-only exact-pair static/author-or-DS CPU replay; no training/native commands |

The state owner preallocates all maps/response bytes before publication. Fast state, visual cache and response cannot become separately committed. Existing legacy `commit(update)` still publishes Fast+visual atomically, without storing a v2 response. A paired low-level `OnlineLocalMemory.commit/reset_session` cannot bypass the visual owner. Standalone online-memory callers retain their old API and numerical scan.

Only completed evidence affects the proper Session. Slow W0 parameters are never updated; cold state is lazy None until the model-owned scan materializes W0. Fast candidates and tokens detach/clone, including previous state passed into a scan. Legacy preprocessing, normalization, raw15/state15 and H16 native inputs are reused; no Local update equation or outer model implementation is replaced.

## B1 service and ownership flow

Default `transaction_profile=legacy` preserves existing endpoints/Launcher behavior. The new profile must be **explicit** `transaction_profile=b1`, required Local-TTT, max_sessions1, explicit action_chunk_size16, complete run/manifest/Slot identity and a private bounded owner-capability file. Loaded model must resolve raw15/state15/K4/local32, one visible GPU and a single model rank. Developer training validation is rejected in this profile. Unknown/missing profile identity or unsupported modes fail closed; no fallback.

1. After external D4 admission, the trusted Root coordinator registers exact run lease, manifest digest, physical Slot/generation and Task/Episode/Attempt. It authenticates with a private per-Server owner token. The Server allocates fresh epoch-bound session_id/episode_id/assignment capability; duplicate identical registration returns the same assignment.
2. Public inference carries that exact assignment and corrected policy payload. The service freezes canonical JSON, validates ids and bounded contiguous chronology before materializing evidence ranges, computes canonical request/payload identities and checks committed replay before allocating.
3. One bounded Ticket owns the Slot and encoded bytes. Queued/popped/executing/committed-undelivered work keeps ownership. Duplicate submissions attach; changed payload, old evicted frontier or another outstanding frontier rejects. ACKed retained replay returns identical serialized bytes without a new Ticket, encode, scan or generation.
4. The single executor prepares real Local state, calls existing `model.generate_samples_from_batch` **once with batch1**, validates finite `[16,15]` externalized actions, serializes response and proves device work complete. The final lease/deadline/cancel fence and atomic snapshot publication run under the transaction lock.
5. Executor quiescence is marked only **after leaving the model mutex**. No action response is deliverable before then. Delivery ACK releases that exact Ticket once; last-response cache stays bounded per Session and supports lost-response/ACK replay. Duplicate ACK never frees a later frontier.
6. End marks closing/cancel intent and returns202/acknowledged=false while any owned work/model owner remains nonquiescent. After commit/abort/drain, it discards only its own undelivered response, resets its own Session and returns an exact positive ACK; lost ACK can replay, old ACK cannot close a newer assignment.

Failure before commit aborts pending candidates and preserves the prior snapshot. The accepted Episode becomes failed and needs End/new Attempt; it cannot silently retry a generation. Error type/stage/message/bounded traceback are retained and returned as409 to the owned client. Failed abort or unproven device drain quarantines the actor, retains ownership/candidates, refuses new work and never issues positive End ACK. External owned-Server decommission/new epoch is then required; no timeout pretends to kill a CUDA kernel. No automatic process killing or recovery job is performed by Codex.

## Versioned endpoints and bounds

| Operation | Binding / result |
| --- | --- |
| POST `/v2/session/register` | `X-Cosmos-Owner` plus exact registration; returns fresh assignment or identical registration replay |
| POST `/v2/inference` | `{lease,payload}`;202 owned Ticket or200 immutable committed response |
| GET `/v2/inference/<request_key>` | Assignment JSON header and payload-SHA header;202 pending,200 committed,409 diagnostic failure; no legacy numeric request_id authority |
| POST `/v2/inference/ack` | Exact lease/key/payload SHA; idempotent positive delivery ACK only after committed/quiescent |
| POST `/v2/session/end` | Exact lease; deferred202 or proven200 ACK |
| GET `/info` | Actual transaction profile/epoch/run/manifest/slots/bounds/queue health, alongside existing model/Checkpoint/config info; no secret tokens |

New profile allows only a single physical Slot and native batch1 at the server CLI. The generic transaction owner is tested with two sequential B1 Sessions to demonstrate real Fast State isolation; this is **not** two native Sim environments or B>1 support. Existing Root Eval V2 config still rejects M!=1/B!=1, and its Sim/Launcher wiring still uses Phase A's default legacy profile. Calling a legacy `/predict` on a transaction-enabled service is rejected, so it cannot bypass Session ownership. No automatic evaluation profile switch is added.

Request <=32 MiB, <=16 completed evidence rows, queue+inflight encoded bytes <=128 MiB, serialized response <=1 MiB/Session; HTTP parsing concurrency is bounded (2 handlers for this CLI profile) with bounded read deadline. Actor request deadline default600s, explicit finite bound <=6000s; duplicate requests do not renew it. Client retries and polling share one original absolute deadline. Closed-generation receipts, failure diagnostics, leases and responses are bounded by configured physical Slots. No full model/Checkpoint hashing per request.

Generated media is explicitly **off/unsupported in this increment's new profile**. Its B1 action response does not call optional decode/PNG encoding. Legacy media behavior is unchanged. Asynchronous media/Task runtime/native batches remain increment2. The RPC client validates and ACKs a response but is not an environment action executor; D4/at-most-once env.step/Core/SR wiring stays with the existing/future Root+Sim path, not this client library.

## Author CPU and exact-pair replay

Tests use real CPU Local encoder/core/model-owned scan, actual Tensor Fast States, composite preprocessing and native policy carrier construction. Wan and diffusion model boundaries are faithful doubles; the client/dispatcher/HTTP parser are tested in process with no model weights, real service binding or RoboCasa/EGL. Coverage includes W_A!=W_B and disjoint storage, W0 unchanged/grad-free, fresh/reset, failed generation/nonfinite/shape/serialization/publication, malicious in-place scan candidate, input mutation, huge-frontier bounds, pending/committed byte credit, deadline cancellation, lost register/infer/ACK/end responses, replay-after-ACK and exact old/new identity. CPU B1 actions/Fast State compare exactly to legacy on identical evidence; this is not native GPU numeric parity.

After locking clean exact worktrees, use the existing Python environment:

```bash
python tools/v3/run_eval_v2_transactions_b1_cpu_gate.py \
  --root-worktree '<EXACT_ROOT_WORKTREE>' \
  --expected-root '<FORMAL_IMPLEMENTATION_ROOT_FROM_HANDOFF>' \
  --expected-child '<FORMAL_CHILD_FROM_HANDOFF>' \
  --evidence-dir '<NEW_EXTERNAL_EVIDENCE_DIR>'
```

The tool verifies complete Root/Child/Gitlink, clean worktrees, correct import origin and Ruff0.12.7 before tests. CUDA is hidden, model-network flags offline, caches/temp outputs external. It runs new inference/legacy B1 tests and all unchanged Phase A CPU regressions in separate subprocesses, retains raw per-group JUnit/logs/temp evidence, creates combined `junit.xml`, `gate.json`, source SHA256 and explicit commands/environment. Any failure/error/skip/source drift stops without modifying source; no package install or remote job. PASS means the **caller's** CPU replay passed, not automatically DS or GPT approval. Wrong pair is BLOCKED before test execution.

## Handoff, Code Gate and STOP

Publish new Child first, then Root Gitlink and formal implementation; raw author CPU/static/diff/source binding evidence follows in a separate bookkeeping commit. Request fresh GPT **Code Gate** on the full delta from Phase A fd7/d2 and the new formal pair, not just the final Root commit. Author checks are not independent DS acceptance. Phase A DS CPU remains a separate pending task; this new author replay does not close it. Stop after publication/readback. Do not enter increment2, merge, run GPU/real Cosmos/RoboCasa/DCP/900, dispatch DS or modify training/history before the required separate approvals.
