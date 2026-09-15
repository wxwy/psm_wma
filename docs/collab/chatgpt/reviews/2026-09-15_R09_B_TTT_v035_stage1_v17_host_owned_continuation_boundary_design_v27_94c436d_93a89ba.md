# ChatGPT independent review — Stage-1 v1.7 host-owned continuation boundary design V27

Formal pair:
- root: `94c436d50d2caded43410052e720fbdbf3f37b7b`
- child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-HOST-OWNED-CONTINUATION-BOUNDARY-DESIGN-V27`

Verdict:
`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_HOST_OWNED_CONTINUATION_CPU_STATIC`

Blockers: `0`
- Design/Authority: `0`
- Production/implementation: `0` (implementation is intentionally out of scope for this design Gate)
- Evidence: `0` (implementation evidence is intentionally out of scope for this design Gate)
- Scope/child/runtime: `0`

## Re-lock / target validity

- Pre-review `V2` HEAD is a V27 request/delivery bookkeeping descendant; the declared formal technical target remains `94c436d50d2caded43410052e720fbdbf3f37b7b`.
- `CODEX_INBOX.md` explicitly requests this exact formal pair and Gate.
- Formal root resolves `cosmos-framework` exactly to Gitlink `93a89ba61306d840a008813f62f26a34d54850f4`.
- Child `93a89ba61306d840a008813f62f26a34d54850f4` resolves independently in `wxwy/cosmos-framework`.
- The immediately relevant prior design target was V26 `ed5bd4c5a5261ece1950362f8346d8834dd2b990 / 93a89ba61306d840a008813f62f26a34d54850f4`, which received ChatGPT `REQUEST_CHANGES` with three HIGH Design/Authority blockers. V27 is a new formal root and is therefore freshly reviewed.

## Authority / supersession chain used

The effective chain for this review is:
1. V24 live-plan continuity authority remains binding for unique reviewed authority, non-consuming pre-C to verified-resume continuity, non-reconstructive review witness, terminal loss/restart, exactly-once C and no retry;
2. V26 supplies the host-owned architectural replacement for the rejected same-interpreter registry trust premise and the staged fake-host -> real-host split;
3. V27 is the normative remediation layer for the three V26 blockers and explicitly maps V24 live authority into host-owned equivalents.

For this exact Gate, V27 is read together with the non-conflicting V26 host-boundary baseline; V27 supersedes the conflicting V26 clauses identified by the prior review.

## Incremental review result

V27 closes all three V26 HIGH blockers at the design level.

### V26 HIGH 1 — V24 same-live authority / non-reconstructive record

Status: `CLOSED`.

V27 explicitly preserves V24 semantics and replaces project-Python object wording with one host-generation-owned triple:
- `HostSessionV27`;
- `LivePlanEnvelopeV27`;
- `HostLeaseV27`.

`LivePlanEnvelopeV27` is created exactly once by host-owned non-consuming pre-C and retains the raw execution material required by C. It is explicitly forbidden to reconstruct the envelope from review fields, logs, IPC payloads or client objects. Restart/generation change or loss is terminal.

`ReviewRecordV27` is explicitly detached and non-reconstructive: it carries canonical identities/digests/provenance and audit literals, but excludes JSON/Markdown/patch raw bytes, callable/capability material, secrets and envelope contents. It additionally binds `host_generation_id`, `host_session_id`, `live_plan_id`, `live_plan_digest`, `host_lease_id` and `binding_digest`.

This is an adequate host-owned equivalent of the V24 same-live authority model while preserving V24's prohibition on record-driven reconstruction.

### V26 HIGH 2 — session/generation-bound one-shot approval

Status: `CLOSED`.

V27 defines canonical `ReviewApprovalV27` and binds it to:
- Gate;
- exact formal root and child/Gitlink;
- exact review-record digest;
- host generation;
- host session;
- live plan id/digest;
- host lease;
- binding digest;
- one-use approval nonce;
- approval counter.

Only the independent orchestration -> host attestation channel can mint/submit approval; project-client IPC has no approval operation. Host accepts only the exact current generation/session/envelope/lease/binding attestation, consumes the nonce at acceptance, and rejects prior-session/prior-generation/different-binding/duplicate/counter-mismatch/restart/loss reuse. A new session requires a new non-consuming pre-C, audit, review and attestation.

This closes the prior replay ambiguity.

### V26 HIGH 3 — atomic one-shot resume admission

Status: `CLOSED`.

V27 freezes the per-session state machine:

`PENDING_REVIEW -> APPROVED -> CONSUMING -> TERMINAL`

and requires one serial host event loop/lock. The first exact resume atomically performs `APPROVED -> CONSUMING` inside the host critical section before any freshness, consumer or readback work. Concurrent, pipelined, replayed, foreign or second resumes can only observe `CONSUMING`/`TERMINAL` and must cause zero freshness/consumer/apply work. Every post-admission outcome, including STALE/UNKNOWN, consumer rejection/exception, readback mismatch, IPC failure or host failure, terminates permanently with no transition back to APPROVED and no retry.

The design therefore freezes at-most-one effectful C admission before implementation.

## Implementation authorization and limits

This approval authorizes only the next CPU/static protocol-conformance implementation described by V27:
- stdlib fake-host only;
- no process launch;
- no socket/real IPC;
- no filesystem I/O;
- no real consumer or `apply_patch`;
- no real pre-C/C;
- no request pair/materialization/source-evidence;
- no child/runtime/config mutation;
- no GPU/CUDA/torchrun/training/evaluation/inference/LIBERO4IN1.

The fake-host implementation must directly witness:
- drift rejection for every inherited ReviewRecord category, including consumer/guard/verifier provenance, C01--C15, freshness/query/absence/replay identities and the V27 host-session/binding identities;
- prior-session/prior-generation approval replay rejection;
- duplicate and pipelined resume rejection;
- every `CONSUMING` failure branch terminalizes;
- total apply count is at most one, and every losing/rejected path contributes zero apply;
- exact approved current-session success remains one-shot.

Real Stage1Host OS identity, anonymous inherited IPC, privileged attestation transport, real envelope/pre-C and real consumer integration remain a separate future design/review Gate. If that isolation cannot be provided, the design requires fail-close rather than fallback to V25/same-interpreter authority.

## Conclusion

V27 is sufficiently precise to authorize the limited fake-host CPU/static protocol-conformance implementation. The three V26 Design/Authority blockers are closed for this exact formal pair. This approval does not close any implementation or real-host integration Gate.