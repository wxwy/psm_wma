# ChatGPT Independent Review — R09-B TTT v0.3.5 Controlled Collection Execution Evidence untracked-path snapshot remediation

**Date:** 2026-09-12  
**Formal root:** `2c73ad0bf9f49d1dd13f0803046ac75f3cd9449c`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-DESIGN`

## 1. Pair / scope

- Re-locked remote `V2`, re-read live `docs/collab/chatgpt/CODEX_INBOX.md`, and confirmed this exact pair is the current formal request for this Gate.
- Independently verified formal root `2c73ad0bf9f49d1dd13f0803046ac75f3cd9449c` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Incremental baseline is prior ChatGPT-approved pair `981f89873263f5c10fcfc8c30740bf5ce014eb2d` / same child. The new formal root changes only one technical line in `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_execution_evidence_design_v0.1.md`; remaining changes between the pairs are review/Inbox bookkeeping.
- This remains docs-only. No executor implementation, real source selection/read/hash, authority-root materialization, collection/receipt mutation, publication/audit, child/runtime, GPU, or training is authorized by this review.

## 2. Remediation audit

The remediation is a monotonic fail-closed tightening of the already-approved canonical worktree snapshot contract.

It now states that any one of the six fixed allowlist paths that is present in the worktree but not tracked by Git — explicitly including porcelain `??` — is an immediate FAIL and cannot be serialized as a valid worktree snapshot entry. The same condition is also included in the fixed `git status --porcelain=v1 -z --untracked-files=all` plus `find -P` validation rule.

This removes the prior ambiguity in which an untracked-present path could have `mode=null` while the only legal present record required `mode="100644"|"100755"`. After remediation, admissible worktree snapshot states remain uniquely limited to:

- exact absent record for an absent fixed path; or
- exact tracked regular-file record with frozen Git mode and raw-byte SHA-256.

Untracked-present, symlink, directory, other filesystem type, path-normalization drift, and any porcelain entry outside the six-path allowlist all fail closed before such a state can become accepted rollback evidence.

The change does not weaken any previously approved rollback/evidence invariant: the retained before/after snapshot objects, target-ref and local-HEAD separation, controlled-index tree identity, five-key rollback null record, primary-failure identity, `ROLLBACK_INCOMPLETE`, push/publication violation encoding, and candidate-construction / post-handoff-verification split remain intact.

## 3. Fresh audit

No new blocking contradiction was found.

The amended untracked-path rule is consistent with the inherited transaction contract that forbids overwriting pre-existing collection/receipt target paths and restricts the live delta to the five collection paths plus the one receipt path. It narrows the admissible pre-live/worktree states rather than enlarging authority.

## 4. Formal verdict

`APPROVE_TO_DESIGN_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_CONTROLLED_EXECUTION`

Current blockers: **0**.  
Design/Authority blockers: **0**.  
Production blockers: **0**.  
Evidence-only blockers: **0**.

## 5. Scope

This approval closes only the docs-only controlled-execution design remediation for the exact formal pair above. It does not authorize executor implementation, real source selection/read/hash, authority-root materialization, collection/receipt mutation, source-evidence record/package/witness creation or write, publication materialization, real root audit, child/runtime modification, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler step, sidecar, training, evaluation, inference or LIBERO4IN1. Downstream progression remains the already frozen source-evidence/publication closure sequence before any GPU work.
