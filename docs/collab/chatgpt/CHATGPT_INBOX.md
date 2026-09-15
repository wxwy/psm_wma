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

- immediate prior live blob SHA: `7ba93ca29aaa0501ab31d6cd70fc648248443648`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — V27 fake-host CPU/static remediation still REQUEST_CHANGES

Formal pair:
- root implementation SHA: `c4a3b985cfd8a576ab114431f8ee2ae4df6f2681`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-HOST-OWNED-CONTINUATION-CPU-STATIC`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/stage1_host_boundary.py:42)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-15_R09_B_TTT_v035_host_owned_continuation_cpu_static_remediation_c4a3b98_93a89ba.md`

Canonical review commit:
`625268b47b8700449f5eae3c0982beb051892bbf`

Current blockers: `3`; Design/Authority: `0`; Production/implementation: `2 HIGH`; Evidence: `1 MEDIUM`; Scope/child/runtime: `0`.

Positive closure from the prior pair:
- exact Gate/root/child and session/binding approval checks are now present;
- privileged test attestation is separated into `FakeStage1OrchestratorV27`;
- `RLock` serializes approval and atomically moves `APPROVED -> CONSUMING` before freshness/apply;
- the expanded suite covers approval-field drift, prior session/generation, parallel resume, failure branches and foreign lease.

Remaining blockers:
1. HIGH — ReviewRecord category names/order are frozen, but each category is still only an arbitrary non-empty `tuple[str, ...]`. There is no per-category canonical grammar/cardinality for consumer/guard/verifier provenance, C01--C15, nine freshness identities, query/absence/replay/target/descriptor/source/argv fields. `_default_rows()` still generates one placeholder string per category.
2. HIGH — `create()` stores the same `ReviewRecordV27` object that it returns to the caller. Attestation/approval/resume trust that aliased object and do not recompute rows -> row digest -> plan/binding/record digest from host-private creation-time state. `object.__setattr__` on the returned record can therefore drift reviewed rows/digest or rebind lease fields in the exact object held by host state, including after review/approval.
3. MEDIUM — current record-drift tests are not causal for those contracts: they mostly inject a wrong approval digest rather than mutate/revalidate the reviewed record itself; malformed tests cover top-level category names/order but not per-category field grammar; no returned-record base-mutation witness exists. The parallel test is useful but could be made more deterministic around the admission overlap.

Required closure:
- freeze exact canonical primitive schema/arity/type/format for every ReviewRecord category and validate it before session creation;
- keep a host-private detached creation snapshot distinct from any client/audit record object, and recompute/verify canonical record + binding integrity at attestation/approval/resume;
- add direct `object.__setattr__` drift/rebind witnesses on returned records before attestation, after attestation and after approval, proving host authority is unchanged and rejected paths contribute zero extra freshness/consumer/apply;
- make per-category malformed/drift tests causal so removing schema or digest revalidation makes them fail.

No real Stage1Host process/OS identity, real IPC, privileged real attestation transport, real envelope/pre-C/C, real consumer or `apply_patch`, request pair/materialization/source-evidence, child/runtime/config mutation, GPU/CUDA/torchrun, training/evaluation/inference or LIBERO4IN1 is authorized by this pair.

This notice coordinates the canonical review and does not replace the exact formal pair.
