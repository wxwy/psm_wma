# ChatGPT Independent Review — R09-B TTT v0.3.5 Immutable Source Collection Design authority remediation

**Date:** 2026-09-12  
**Formal root:** `885956cb6cddf57f04b3ed5097cf87a176779403`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-DESIGN`

## 1. Pair / scope

- Re-locked remote `V2` and re-read the live `docs/collab/chatgpt/CODEX_INBOX.md` request.
- Independently verified formal root `885956cb6cddf57f04b3ed5097cf87a176779403` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Incremental authority is the prior rejected pair `9b9b516132806369718361b0e1b7b54c15c0483d` / `93a89ba61306d840a008813f62f26a34d54850f4` and its canonical review.
- This remediation remains docs-only. No real source collection, source-evidence write, publication, read-only audit, child/runtime modification, real checkpoint/data/cache I/O, GPU or training execution is authorized here.

## 2. Prior HIGH closure

### HIGH-1 — approved downstream progression was rewritten: CLOSED

The design now explicitly states that it does not delete or replace the approved source-evidence/publication sequence. The inherited progression remains binding: immutable collection design/execution/closure, source-evidence controlled-write execution and `APPROVE_TO_WRITE_SOURCE_EVIDENCE`, record closure, independent post-commit receipt closure/review, publication materializer/verifier, and later read-only root audit. GPU priority is moved after completion of that already-approved provenance loop rather than being used to bypass it.

The design also restores the separately frozen `IMMUTABLE-SOURCE-COLLECTION-EXECUTION-DESIGN` and `IMMUTABLE-SOURCE-COLLECTION-CLOSURE` stages instead of merging them into a new one-shot execution Gate.

### HIGH-2 — collection values lacked frozen immutable-source derivation: CLOSED

The collection formal root now freezes five exact root-owned artifacts. In addition to the collection and canonical-config artifacts, it adds fixed input-descriptor, manifest, and checkpoint-descriptor artifacts. The design freezes:

- exact input-descriptor schema/key set and ordered `source_entries` with ordinal, byte length and raw-byte SHA-256;
- exact manifest schema and equality relationship to the input descriptor;
- `source_input_sha256` and `source_manifest_sha256` as SHA-256 of the respective canonical artifact bytes;
- `immutable_source_identifier` as the SHA-256 of an exact three-key canonical derivation object;
- the collection artifact's four identity/digest fields as values recomputed only from those candidate artifacts, explicitly rejecting caller/environment/working-tree supplied precomputed values.

This converts the previous self-consistent-digest-only model into a frozen canonical derivation chain. Actual selection/read of the real source bytes remains correctly deferred to the separately reviewed collection execution design/Gate.

### HIGH-3 — exact five-key checkpoint-source descriptor bytes were absent: CLOSED

A fixed root-owned `docs/build/PSM-WMA_immutable_source_checkpoint_descriptor_v1.json` artifact is now mandatory. It is the exact five-key `root_gitlink_checkpoint_source_descriptor_v1` canonical object inherited from source-audit design v0.3 §5. Its fields are tied to the derived immutable-source identifier, manifest digest and input digest, and its canonical SHA-256 is `checkpoint_source_descriptor_sha256`.

The receipt schema now binds its exact artifact path/schema/raw SHA-256/blob OID, along with the corresponding identities for the collection, input descriptor, manifest and canonical model config. Receipt verification is required to re-read the collection-root tree/blobs and recompute the full input-descriptor -> manifest -> identifier -> descriptor -> collection chain before authority is accepted.

## 3. Fresh audit / remaining scope

No new Design/Authority blocker was found in the remediation.

The next `IMMUTABLE-SOURCE-COLLECTION-EXECUTION-DESIGN` still must freeze the concrete approved real-source selection/read contract before any real source bytes are read. This approval does not itself authorize source selection, checkpoint/data/cache I/O, or any live collection mutation.

The non-circular two-root model, receipt parent constraint, canonical-byte rules, Git object binding, isolated preflight, rollback, `ROLLBACK_INCOMPLETE`, and staged-set exclusions remain fail-closed.

## 4. Formal verdict

`APPROVE_TO_DESIGN_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION`

Current blockers: **0**.  
Design/Authority blockers: **0**.  
Production blockers: **0**.  
Evidence-only blockers: **0**.

## 5. Scope

Approval authorizes only the next docs-only `IMMUTABLE-SOURCE-COLLECTION-EXECUTION-DESIGN` in the already-approved progression. It does not authorize real immutable-source collection, source-evidence record/package/witness creation or write, publication materialization, real root source-audit execution, child/runtime modification, real checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler step, sidecar, training, evaluation, inference or LIBERO4IN1.
