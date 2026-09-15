# ChatGPT independent review — V27 host-owned continuation CPU/static fake-host implementation

Formal pair:
- root: `2b7429f2a1eb6cd50f5c5da15e3691a5128f50c1`
- child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-HOST-OWNED-CONTINUATION-CPU-STATIC`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/stage1_host_boundary.py:54)`

Blockers: `4`
- Design/Authority: `0`
- Production/implementation: `3 HIGH`
- Evidence: `1 MEDIUM`
- Scope/child/runtime: `0`

## Re-lock / target validity

- Pre-review `V2` HEAD is request/bookkeeping commit `5a299c9e530f3148a71833e3246d19589fe12b1c`, whose parent is the declared formal implementation root `2b7429f2a1eb6cd50f5c5da15e3691a5128f50c1`.
- `CODEX_INBOX.md` explicitly requests this exact pair for the V27 fake-host CPU/static closure Gate.
- Formal root resolves `cosmos-framework` exactly to Gitlink `93a89ba61306d840a008813f62f26a34d54850f4`.
- Child `93a89ba61306d840a008813f62f26a34d54850f4` resolves independently in `wxwy/cosmos-framework`.
- The immediately preceding authority is the approved V27 design pair `94c436d50d2caded43410052e720fbdbf3f37b7b / 93a89ba61306d840a008813f62f26a34d54850f4`, with verdict `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_HOST_OWNED_CONTINUATION_CPU_STATIC`. This is a new implementation pair, so fresh technical review is required.

## Frozen implementation contract used

The approved V27 design requires the fake-host CPU/static conformance model to preserve, at minimum:
- a detached, canonical, non-reconstructive `ReviewRecordV27` covering every inherited reviewed authority category, including consumer/guard/verifier provenance, C01--C15, nine-entry freshness, query/absence/replay identities and the host generation/session/plan/lease/binding identities;
- `ReviewApprovalV27` bound to the exact Gate, exact formal root, exact child/Gitlink, review-record digest, host generation/session, live plan id/digest, host lease, binding digest, one-use nonce and approval counter;
- a protocol distinction where only the orchestration->host attestation path can mint/submit approval; project-client behavior cannot synthesize equivalent authority;
- a serial/atomic per-session `PENDING_REVIEW -> APPROVED -> CONSUMING -> TERMINAL` state machine, with `APPROVED -> CONSUMING` consumed before freshness/apply;
- duplicate/pipelined/replayed/foreign resumes must contribute zero additional freshness/consumer/apply work;
- every post-admission failure terminalizes with no retry;
- direct behavioral evidence for complete record drift rejection, prior-session/prior-generation approval replay, duplicate/pipelined resume, every CONSUMING failure branch, total apply <= 1, zero apply on losing paths, and one exact success.

The scope remains stdlib fake-host only. Real process/IPC/filesystem/consumer/pre-C/C and downstream work remain forbidden.

## Positive closure

- The implementation stays root-only and does not introduce process launch, socket/IPC, filesystem I/O, real consumer, `apply_patch`, child/runtime/config mutation, GPU or training.
- The host model has explicit `PENDING_REVIEW`, `APPROVED`, `CONSUMING`, `TERMINAL` states.
- Session, lease and live-plan identifiers are host-generated; approval carries generation/session/plan/lease/binding fields plus nonce/counter.
- Foreign lease and stale-before-apply paths terminalize with zero apply in the current tests.
- Sequential exact success followed by repeat resume yields one apply in the current tests.

These are useful partial witnesses, but they do not close the V27 contract.

## HIGH 1 — `ReviewRecordV27` collapses the complete reviewed authority into one free-form string digest

Location: `tools/psm_wma/stage1_host_boundary.py:20-28,54-72`.

The approved design requires a detached canonical record whose typed field surface covers the inherited review categories. The implementation instead defines `ReviewRecordV27` with only seven outer identity/digest fields and constructs it from a single caller-supplied `review_identity: str`:

- `live_plan_digest = sha256(review_identity)`;
- `record.digest = sha256(review_identity + binding)`.

There is no typed/canonical representation or host validation for consumer/guard/verifier provenance, C01--C15, freshness identities, query stdout/stderr/predicate identities, authority/designated absences, replay binding, frozen targets, descriptor/source/argv rows, or the exact formal pair/Gate inside the record.

This means the implementation cannot causally reject drift in those categories: any arbitrary string can stand for an allegedly reviewed record, and the host has no category-level semantics to compare. A digest over an opaque input string is not the V27 complete ReviewRecord contract.

Violated frozen contract: V27 complete detached ReviewRecord plus the explicit implementation-evidence requirement for every inherited record category.

Acceptance:
1. define a canonical primitive `ReviewRecordV27` schema that explicitly carries the complete inherited identity/provenance categories authorized by V27, while remaining non-reconstructive;
2. create/validate its canonical digest from those typed ordered fields, rejecting missing/extra/reordered/malformed fields;
3. bind Gate + exact formal root + exact child/Gitlink into the reviewed record/authority surface rather than accepting an opaque `review_identity` string;
4. add one direct drift witness for every required record category, each proving zero freshness/consumer/apply.

## HIGH 2 — approval does not enforce the exact formal root/child authority, and the fake-host exposes its approval secret through the same host object

Location: `tools/psm_wma/stage1_host_boundary.py:74-91`.

`ReviewApprovalV27` contains `root` and `child`, but `approve()` never compares either field against host-owned expected values. The validated tuple contains only record/generation/session/plan/lease/binding fields. Therefore an approval created with an arbitrary or stale root/child is accepted so long as the remaining fields and nonce match.

A direct witness is already constructible from the production API:
- call `approval_for_test(record, "wrong-root", "wrong-child")`;
- `approve()` still succeeds because root/child are ignored.

The Gate check is also reduced to the short literal `"V27"`, not the exact frozen Gate literal.

In addition, `approval_for_test()` is a public method on the same object and returns the host-owned nonce embedded in a valid approval. For a protocol-conformance implementation, that fails to model the V27 separation between untrusted client operations and the privileged orchestration attestation path: any caller with the fake-host object can mint a valid approval for the current session.

Violated frozen contract: exact Gate/formal root/child binding and orchestration-only approval authority.

Acceptance:
1. store the expected exact Gate, formal root and child/Gitlink in host-owned session authority and compare all three on approval;
2. model the privileged attestation side separately from the untrusted client API; no client-facing helper may reveal/mint the nonce-bearing approval;
3. add causal wrong-Gate, wrong-root, wrong-child, wrong-record, prior-session, prior-generation, duplicate-nonce and counter-mismatch witnesses, all terminal/zero-apply;
4. preserve exactly one valid current-session attestation path for tests through a clearly privileged harness/API.

## HIGH 3 — `APPROVED -> CONSUMING` is not serialized/atomic; no host lock/event loop exists

Location: `tools/psm_wma/stage1_host_boundary.py:93-108`.

V27 explicitly freezes a single serial host event loop/lock and requires the first exact resume to atomically consume admission before freshness/apply. The implementation performs:

1. read `_sessions[session_id]`;
2. test `entry["state"] is APPROVED`;
3. later assign `entry["state"] = CONSUMING`;

with no lock, event loop, compare-and-swap or other serialized critical section. The check and transition are separate Python operations. The implementation therefore does not establish the design's concurrency invariant; two concurrent/pipelined handlers are not formally prevented from observing APPROVED before either transition is committed.

The current sequential repeat test is not evidence for this contract.

Violated frozen contract: V27 atomic one-shot admission and concurrent/pipelined loser-zero semantics.

Acceptance:
1. implement a per-session or host-wide stdlib synchronization primitive / serialized dispatcher that makes `APPROVED -> CONSUMING` one critical-section admission step;
2. consume the admission state before freshness or any simulated apply/readback stage;
3. add a direct concurrent/pipelined same-handle test that forces overlapping resume attempts and proves total apply <= 1 and every loser contributes zero freshness/consumer/apply;
4. preserve terminal behavior for all post-admission failures.

## MEDIUM 4 — the reported `4/4 PASS` evidence does not cover the approved closure matrix

Location: `tools/psm_wma/test_stage1_host_boundary.py:6-31`.

The suite currently covers only:
- sequential exact success + sequential repeat;
- one wrong generation field;
- foreign lease;
- stale freshness.

It does not directly witness:
- any inherited ReviewRecord category drift;
- wrong Gate/root/child;
- wrong record digest / plan digest / binding digest / nonce / counter;
- prior-session approval replay or a real prior-generation/new-host replay;
- duplicate/pipelined/concurrent resume;
- apply rejection/throw equivalent;
- verify/readback failure;
- all CONSUMING terminal branches;
- privileged orchestration-vs-client separation.

`py_compile`, diff-check and a small passing suite cannot close behavioral contracts that are not exercised.

Acceptance: add direct causal tests for the entire V27 CPU/static evidence matrix. Removing the record validator, exact approval checks, or atomic admission must make those tests fail.

## Blocker lifecycle

- V26/V27 design blockers: `CLOSED at design level`; this review does not reopen the approved V27 design.
- V27 complete ReviewRecord implementation: `OPEN (HIGH)`.
- V27 exact/session-bound privileged approval implementation: `OPEN (HIGH)`.
- V27 atomic one-shot resume implementation: `OPEN (HIGH)`.
- Required CPU/static behavioral evidence: `OPEN (MEDIUM)`.

## Scope reminder

This verdict binds only the exact formal pair above and `G0-R09-B-TTT-V035-HOST-OWNED-CONTINUATION-CPU-STATIC`. It does not authorize real Stage1Host process/OS identity, socket/IPC, privileged real attestation transport, real envelope/pre-C/C, real consumer or `apply_patch`, request pair/materialization/source-evidence, child/runtime/config mutation, GPU/CUDA/torchrun, training/evaluation/inference or LIBERO4IN1.
