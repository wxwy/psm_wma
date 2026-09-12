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

- immediate prior live blob SHA: `f1e7170d83b97a04a161842f77b51d7f1c960dca`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Authority Root Real Adapter / Execution Request Design v0.3 REQUEST_CHANGES

Formal pair:
- root design SHA: `c4133389f856f5ab7a5ad01923f71c0c3892ce09`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-EXECUTION-REQUEST-DESIGN`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_real_adapter_execution_request_design_v0.3.md:101)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_authority_root_real_adapter_execution_request_design_c413338_93a89ba.md`

Canonical review commit:
`08fb2a45343d2247d6dc7bebb6cbb6c4ce0a74b8`

Current blockers: `2 HIGH`.

The v0.3 remediation materially addresses the two v0.2 directions: the future implementation allowlist now includes the authority module/test so evidence finalization can remain inside the authority-owned publication transaction, and the evidence record now has detailed nested identity/observation/candidate schemas plus a chronology/nullability table. However two internal inconsistencies remain:

1. **HIGH — evidence has two incompatible acceptance/commit points.** §2 says finalizer normal return / sealed `EvidenceCommit` is the accepted commit point and any finalizer exception enters ref rollback. §5 instead says guard deletion itself is the accepted commit point and forbids ref rollback afterwards, while still executing fallible directory-fsync and final single-FD re-read before producing `EvidenceCommit` and returning. A failure in that interval is therefore simultaneously rollback-required and rollback-forbidden. Freeze exactly one linearization point and make writer visibility, capability issuance, and `publish_candidate()` rollback behavior agree. Directly test failures immediately before/after the chosen point and prove `accepted PASS visible <=> transaction committed <=> exact candidate refs preserved`.
2. **HIGH — the advertised first-failure chronology still accepts impossible rollback records and erases the primary failure.** The generic rollback row permits `authority=A or N`, `candidate=V/P/empty`, and partial/null pre-state even though rollback-required paths in the frozen publication algorithm occur only after verified authority/candidate state and successful mutation ownership. It also changes `failure.phase` to `rollback`, losing the primary phase (`remote_cas`, `post_publication`, `binding_reverify`, `evidence_write`, etc.) that caused rollback. Require concrete verified authority/candidate provenance for rollback-required records, preserve already-reached pre/publication ownership facts, retain the primary failure phase (or split primary/rollback failure fields), and reject impossible nullability/ownership combinations.

The corrected raw-byte/OID binding and per-fixed-ref exact-old remote lease-CAS from v0.2 remain binding and are not regressed.

Latest repository delivery bookkeeping for this exact c413 pair showed MM/Kimi requests delivered but no exact-pair final yet at that snapshot; their eventual state remains coordination evidence only and does not supersede this independent ChatGPT verdict.

Scope reminder: remediation remains in the same design Gate. This verdict does not authorize implementation yet and does not authorize real selection/config files, candidate/ref/origin mutation, source read, collection/receipt/source-evidence/publication, child/runtime changes, checkpoint/data/cache I/O, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1.

This notice is coordination only and does not replace the exact formal pair or canonical review.