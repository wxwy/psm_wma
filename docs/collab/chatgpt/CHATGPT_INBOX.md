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

- immediate prior live blob SHA: `603cb07e8465f3e42a2711fd0ee9ea0d41c24015`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Source-evidence Producer / Closure Design authority remediation REQUEST_CHANGES

Formal pair:
- root design SHA: `180038024ae2b4cc2e436bddafbcc01018087b0c`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-SOURCE-EVIDENCE-PRODUCER-CLOSURE-DESIGN`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_source_evidence_producer_closure_design_v0.1.md:35)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_source_evidence_producer_closure_design_1800380_93a89ba.md`

Canonical review commit:
`2918ad2eb21c64a7f70b43e762c28706cb54f9cd`

Current blockers: `2 HIGH`; Design/Authority `2`; Production `0`; Evidence-only `0`.

Closure from prior review:
- the independent immutable-source collection design/execution/closure progression is now explicit and precedes source-evidence controlled write;
- resolved `canonical_model_config` is now bound to a reviewed collection authority artifact rather than an arbitrary schema-valid caller mapping;
- a separate next-root post-commit closure receipt now exists for package/witness binding;
- staged Gitlink/publication exclusions, isolated preflight, rollback and `ROLLBACK_INCOMPLETE` semantics remain intact.

Remaining blockers:
1. `immutable_source_collection_receipt_v1` is self-referential as written: the receipt lives in the collection closure formal root but itself contains `collection_formal_root_revision`, while that formal revision is required to be recomputed from the same root. A normal Git commit cannot contain its own final SHA in bytes that determine that SHA. Use a non-circular two-root model: collection formal root first, then a separate receipt root whose parent is exactly that collection root and whose fixed-path receipt binds the collection root/artifact/config identities. Freeze exact 40-hex revision/OID, exact reviewed path/schema strings, and 64-hex digest constraints.
2. `source_evidence_postcommit_closure_receipt_v1` retains `witness_blob_native_oid` but defines no fixed witness path/tree ownership. Therefore the OID cannot be uniquely recomputed from the receipt-root tree. Either persist the witness at one fixed receipt-root path and bind path/blob/raw bytes/SHA-256 exactly, or remove the blob-OID claim and define the witness as deterministically reconstructed canonical bytes/digest only.

Still not authorized: real immutable-source collection, source-evidence record/package/witness creation or write, publication materialization, real root source-audit execution, child/runtime modification, real checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler step, sidecar, training, evaluation, inference or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair or canonical review.
