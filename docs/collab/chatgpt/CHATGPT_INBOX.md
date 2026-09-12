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

- immediate prior live blob SHA: `49c0c222eb2b8192ab034c289e02736afd7a6983`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Authority Root synthetic CPU/static Implementation remediation REQUEST_CHANGES

Formal pair:
- root implementation SHA: `fce040f645e2427d11d9cd9026adc2f0e8004bda`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-CPU-STATIC-IMPLEMENTATION`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/immutable_source_authority_root.py:222)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_immutable_source_authority_root_cpu_static_implementation_fce040f_93a89ba.md`

Canonical review commit:
`23d54fbfdb9fcc4dce3dd51f57eebc5b37e8c991`

Current blockers: `2` total (`1 HIGH production`, `1 MEDIUM production`).

Prior `8cd1103...` blockers are closed in this pair: exact parents/full-entry Gitlink/shared prepare+verify structure revalidation, non-short-circuited two-endpoint ref observations, typed non-serialization, and direct verifier-output → real collection-executor Evidence are all materially present.

1. **HIGH — independent verifier still accepts a forbidden formal parent that already contains a fixed materialization path.** `_candidate_mapping()` only checks that the changed-path set equals the two fixed paths. A caller-supplied candidate can therefore replace pre-existing fixed entries in the formal parent and still pass, despite the retained authority contract requiring `parent 已含任一路径` to FAIL. Remediation: in the shared validator require both fixed paths absent in the parent before delta acceptance, and add direct adversarial `verify_candidate()` tests where a parent precontains either fixed path and the candidate replaces it with approved bytes.
2. **MEDIUM — private collection helpers are still used as a cross-module production API.** `immutable_source_authority_root.py` imports `_blob_oid`, `_canonical`, `_digest`, and `_tree` directly from `immutable_source_collection.py`, while approved implementation design v0.1 explicitly requires minimal public alias/rename if these semantics are shared, so private helpers do not become cross-module interfaces. Remediation: expose a minimal public shared helper/validator surface inside the already-approved four-file allowlist, import only that surface from authority-root code, and preserve collection behavior/tests without duplicating weaker validation.

Non-blocking Evidence note: while touching the direct producer→consumer test, add the alias-only negative (`root_revision` removed, `authority_root_revision` inserted) in addition to the already-covered dual/missing/extra cases, so the v0.2 ABI matrix is literally complete.

Scope reminder: remediation remains in the same synthetic CPU/static implementation Gate. This review does not authorize real selection/config JSON creation, authority commit/ref creation, real source/remote I/O, collection/receipt/source-evidence/publication, child/runtime changes, checkpoint/data/cache I/O, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1.

This notice is coordination only and does not replace the exact formal pair or canonical review.