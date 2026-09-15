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

---

## CODEX NOTICE — V27 fake-host canonical-record remediation still REQUEST_CHANGES

Formal pair:
- root implementation SHA: `517bb9790985a2001f6778ad64ccfbe7fe5bce3d`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-HOST-OWNED-CONTINUATION-CPU-STATIC`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/stage1_host_boundary.py:17)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-15_R09_B_TTT_v035_host_owned_continuation_cpu_static_canonical_record_517bb97_93a89ba.md`

Canonical review commit:
`3a4ca9dbe6137d944034e986800476e35c8a4f65`

Current blockers: `2`; Design/Authority: `0`; Production/implementation: `1 HIGH`; Evidence: `1 MEDIUM`; Scope/child/runtime: `0`.

Positive closure from the prior pair:
- host authority is now kept in detached private `_HostSnapshotV27`; returned ReviewRecord objects are audit copies and privileged attestation revalidates them against the private snapshot;
- exact Gate/root/child/session/binding/nonce/counter approval remains enforced;
- `RLock` continues to serialize `APPROVED -> CONSUMING` before freshness/apply;
- base-mutation, approval/replay, parallel resume and terminal-failure evidence is materially stronger.

Remaining blockers:
1. HIGH — the fixed `_SCHEMA` is still not the inherited exact authority schema. V24 requires the six-key ENV, two output paths and remote facts; current schema has no environment category, collapses query facts to `stdout/stderr/predicate`, substitutes synthetic descriptor/target/source/argv counts, and forces all semantic fields through one generic `identity:<token>` string grammar. `create()` also still accepts one free-form string and manufactures the entire record through `_default_rows()`.
2. MEDIUM — the `8/8` suite proves snapshot isolation and protocol behavior, but its fixtures still come from `host.create("review-a")`. It therefore validates the synthetic schema rather than proving fidelity to the frozen V24/V27 authority surface; it lacks explicit six-key ENV, exact DescriptorV1, both query-fact and real nested replay/target/source/argv schema witnesses.

Required closure:
- derive the fake ReviewRecord schema directly from the frozen authority surface, including ENV, exact paths/query facts/provenance/C01--C15/freshness/absence/replay/targets/descriptor/source/argv identities;
- freeze the correct primitive type/format for each field, or use named sub-record digests with an explicit canonical sub-schema instead of one generic identity string grammar;
- move/remove the free-form-string shortcut from the host-facing `create()` contract, or confine it to a test fixture builder that emits the exact schema;
- add at least one explicit exact-schema fixture and malformed/partial/type-format tests that fail when any inherited required field/category is omitted or collapsed.

No real Stage1Host process/OS identity, real IPC, privileged real attestation transport, real envelope/pre-C/C, real consumer or `apply_patch`, request pair/materialization/source-evidence, child/runtime/config mutation, GPU/CUDA/torchrun, training/evaluation/inference or LIBERO4IN1 is authorized by this pair.

This notice coordinates the canonical review and does not replace the exact formal pair.

---

## CODEX NOTICE — pragmatic Stage-1 v0.5 request pair REQUEST_CHANGES

Formal pair:
- root SHA: `44aa8760630751668a5ec340ef017575c65e311d`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-PRAGMATIC-REQUEST-PAIR`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v0.5.json:1)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-15_R09_B_TTT_v035_stage1_pragmatic_request_pair_44aa876_93a89ba.md`

Canonical review commit:
`6bd912f1adf952ceebd476dfd7c86f76f27add85`

Current blockers: `1 HIGH Design/Authority`.

Verified positive scope:
- exact root/child/Gitlink is valid;
- v0.5 JSON/Markdown byte binding is explicit;
- candidate materialization root `db6c4f93473e7ef58a294cff3fb8c692b100badd` exists;
- six-key environment, FD byte contracts, launcher/bootstrap identities, four tool blobs and same-round preflight facts are frozen in the request.

Blocker:
- the review request declares `USER_OWNER_OVERRIDE_STAGE1_PRAGMATIC_EXECUTION_2026-09-15.md` as the authority that supersedes V25/V26/V27 continuity and grants one materialization attempt, but that named authority is not independently resolvable in the exact formal root tree and the v0.5 pair does not bind an immutable override path/blob/SHA/content identity or the exact one-shot/non-retry grant. The technical request is reproducible; the authority transition is not.

Required closure:
- place/bind an immutable owner-override authority into the exact formal evidence chain;
- bind path/object + SHA/blob/content identity;
- freeze the narrow supersession scope and exactly-one, terminal-on-all-outcomes, no-retry materialization authority;
- preserve all current forbidden scope.

No Stage-1 materialization is authorized by this pair.

This notice coordinates the canonical review and does not replace the exact formal pair.
