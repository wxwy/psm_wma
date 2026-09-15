# ChatGPT independent review — Stage-1 v1.7 host-owned continuation boundary design V26

Formal pair:
- root: `ed5bd4c5a5261ece1950362f8346d8834dd2b990`
- child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-HOST-OWNED-CONTINUATION-BOUNDARY-DESIGN-V26`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_host_owned_continuation_boundary_design_v2.6.md:22)`

Blockers: `3`
- Design/Authority: `3 HIGH`
- Production/implementation: `0`
- Evidence: `0` (implementation evidence is intentionally out of scope for this design Gate)
- Scope/child/runtime: `0`

## Re-lock / target validity

- Pre-review `V2` is on V26 request/delivery bookkeeping descendants; the formal technical target remains `ed5bd4c5a5261ece1950362f8346d8834dd2b990`.
- `CODEX_INBOX.md` explicitly requests this exact formal pair and this Gate.
- Formal root resolves `cosmos-framework` exactly to Gitlink `93a89ba61306d840a008813f62f26a34d54850f4`.
- Child `93a89ba61306d840a008813f62f26a34d54850f4` resolves independently in `wxwy/cosmos-framework`.
- No prior same-Gate ChatGPT review exists for this V26 pair; the immediately relevant prior technical review is V25 remediation pair `9c027a346320b0cb8e8445ada1e1a277efb0b875 / 93a89ba61306d840a008813f62f26a34d54850f4`, which remained `REQUEST_CHANGES` because same-interpreter live registries were caller-mutable and the exact review snapshot was incomplete.

## Authority / supersession chain used

Effective inherited authority is:
1. V24 `PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_live_plan_continuity_authority_v2.4.md`;
2. V25 implementation design, except the V26 document explicitly replaces only the V25 premise that same-interpreter module/session registries can hold execution authority;
3. V26 host-owned boundary design for the proposed replacement trust model.

V24 therefore remains binding except where V26 explicitly supersedes it. In particular, V24 still requires: one reviewed live session/plan/lease authority, exact binding/review identity, review record non-reconstructiveness, loss/restart terminality, no reconstruction from review literals, and exactly one verified resume into C.

## Positive closure / design direction

V26 fixes the right architectural layer rather than continuing Python-object hardening:
- authority is moved to a separate `Stage1Host` process under a distinct low-privilege OS identity;
- project Python is explicitly untrusted and cannot be the authority owner;
- private inherited IPC and owner-only host state are required, with fail-close if OS isolation is unavailable;
- same-interpreter fallback is explicitly forbidden;
- consumer/guard/verifier provenance, C01--C15, nine-entry freshness, environment/query/absence/replay classes are named in the target review surface;
- real host/IPC integration is intentionally deferred to a later independent Gate, while the first implementation is limited to fake-host CPU/static protocol conformance.

This direction closes the root cause of the V25 mutable-registry class, but the protocol/authority contract is not yet precise enough to authorize implementation.

## HIGH 1 — V26 does not explicitly reconcile V24 same-live-plan continuity, and `ReviewRecordV26` becomes reconstructive

Locations: `...host_owned_continuation_boundary_design_v2.6.md:22-24, 32-40`.

V26 says it replaces the V25 same-interpreter registry premise, but it does not explicitly supersede V24's stronger continuity rules. V24 requires the reviewed live session/plan/lease authority to survive from non-consuming pre-C through approval and resume, and requires the review record to be non-reconstructive.

The V26 text currently conflicts with that inherited model in two ways:
- `Create` says the host receives a detached canonical `ReviewRecordV26` and then stores `sealed plan bytes/digest`, but it never freezes where those live execution bytes come from or who created them;
- the declared “complete `ReviewRecordV26`” contains canonical JSON/Markdown **bytes**, while V24 allows the review record to carry identities/digests but explicitly forbids using review record/literals to reconstruct a replacement plan.

At the same time, the V26 record field list omits the exact live session/plan/lease identity + binding digest that V24 requires the reviewer to attest. The design therefore leaves two incompatible implementation readings: either the host reconstructs executable state from the review record, or there is some unstated live plan object/envelope outside the record.

Violated frozen authority: V24 same-live-authority continuity and non-reconstructive review-record requirement. V26 has not explicitly superseded those clauses, only the V25 registry storage premise.

Acceptance:
1. add an explicit V24→V26 supersession map stating exactly which V24 clauses remain binding and, if any same-Python-object wording is intentionally replaced, what host-owned equivalent replaces it;
2. freeze a distinct host-private `LivePlanEnvelopeV26` (or equivalent) created exactly once during host-owned non-consuming pre-C and retained live until terminal state; it holds raw output/patch material and any execution capability needed by C;
3. keep `ReviewRecordV26` detached and non-reconstructive: identities/digests/provenance only, not raw execution bytes or callable/capability material that can recreate the live plan;
4. include in the reviewed identity surface the unique host session identity, host generation/boot identity, live plan identity/digest, lease identity and one binding digest tying them to the exact review record;
5. host loss/restart or envelope loss must make old authority permanently unusable; no record-driven reconstruction is allowed.

## HIGH 2 — approval attestation is not bound to one unique live host session/generation/binding, so replay semantics are under-specified

Location: `...host_owned_continuation_boundary_design_v2.6.md:24` plus the `ReviewRecordV26` field list.

The `Approve` step currently freezes only an approval over exact `root/child/review-record digest`; the record list includes an “approval attestation identity” but does not include the unique live host `session_id`, host boot/generation identity, plan/lease binding digest, or a one-use approval nonce.

That is insufficient to prove V24's terminal-loss/no-retry rule. A fresh `Create` after host restart/loss can reproduce the same root/child/review-record digest while representing a different live session. Unless the attestation itself is session/generation-bound and one-shot, the protocol does not formally prevent an old approval from being replayed or re-delivered to a new host session with the same reviewed record.

The sentence “attestation 与 session creation record 不完全相等即 INVALID” does not close this because the frozen creation record as currently specified does not contain all unique live-session binding identities.

Acceptance:
1. define a canonical `ReviewApprovalV26` (name arbitrary) minted only after the exact host `audit(handle)` output has been reviewed;
2. the attestation must cover at least Gate, formal root, child/Gitlink, review-record digest, host generation/boot nonce, unique session id, live plan identity/digest, lease identity, binding digest, and a unique approval nonce/counter;
3. deliver it only through the privileged orchestration→host attestation channel; project-client IPC must have no method to submit equivalent authority;
4. host consumes the attestation exactly once for that live session; a second Create, host restart, host loss or changed binding requires a new non-consuming pre-C, new audit record and new independent review/attestation;
5. CPU/static protocol tests must explicitly reject prior-session/prior-generation attestation replay with zero freshness/consumer/apply calls.

## HIGH 3 — one-shot latch atomicity and concurrent/replayed `resume` ordering are not frozen

Locations: `...host_owned_continuation_boundary_design_v2.6.md:25-28, 50-54`.

V26 says the host “checks approval, freshness guard and terminal latch” and then, if `FRESH`, performs one write. It does not freeze how the latch is consumed relative to freshness/apply, whether the host loop is strictly serialized, or what happens when the untrusted client pipelines/duplicates concurrent `resume(handle)` requests.

“Single client endpoint” is not sufficient as an exactly-once guarantee: an untrusted client can issue duplicate requests, duplicate a descriptor before a later real-host design closes that path, or simply pipeline two messages over one endpoint. If two handlers can observe an open latch before either marks it terminal, both can reach freshness and potentially apply.

Exactly-once is inherited core authority, not an implementation detail to defer.

Acceptance:
1. freeze a per-session state machine such as `PENDING_REVIEW -> APPROVED -> CONSUMING -> TERMINAL`;
2. `resume` must atomically/serially transition `APPROVED -> CONSUMING` and consume the one-shot admission authority before freshness and before any effectful consumer path; if the transition cannot be proven unique, fail closed;
3. all duplicate/concurrent/replayed resumes that observe `CONSUMING` or `TERMINAL` must reject and can never cause a second freshness/apply/readback sequence;
4. any exception after admission, including freshness `STALE/UNKNOWN`, consumer reject/throw, readback mismatch or IPC failure, goes directly to terminal with no retry;
5. fake-host conformance tests must include two simultaneous/pipelined resumes of the same handle, replayed/foreign handles and failure-at-each-stage cases, proving total apply count is at most one and every losing path has zero additional apply.

## Design Gate conclusion

The host-owned direction is the correct replacement for the V25 trust model, but the current document is not yet a complete authority contract. The next revision should close the three items together: explicit V24→V26 continuity semantics, session-bound one-shot approval, and atomic exactly-once resume admission.

No implementation, real host process, IPC integration, real pre-C/C, request pair, materialization/source-evidence, child/runtime/config mutation, GPU/CUDA/torchrun, training/evaluation/inference or LIBERO4IN1 is authorized by this verdict.
