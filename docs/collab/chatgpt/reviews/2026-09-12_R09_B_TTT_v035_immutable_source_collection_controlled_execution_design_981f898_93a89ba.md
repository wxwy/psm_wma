# ChatGPT Independent Review — R09-B TTT v0.3.5 Controlled Collection Execution Evidence canonical worktree-snapshot remediation

**Date:** 2026-09-12  
**Formal root:** `981f89873263f5c10fcfc8c30740bf5ce014eb2d`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-DESIGN`

## 1. Pair / scope

- Re-locked remote `V2`, re-read live `docs/collab/chatgpt/CODEX_INBOX.md`, and confirmed this exact pair is the current formal remediation request for this Gate.
- Independently verified formal root `981f89873263f5c10fcfc8c30740bf5ce014eb2d` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Incremental baseline is prior rejected pair `dee42d02a3e40b5da66c8ac96a8a4d5a66066665` / same child and its canonical review.
- Incremental technical scope remains docs-only and is limited to two evidence-schema corrections in `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_execution_evidence_design_v0.1.md` plus review/Inbox bookkeeping. Child/runtime and previously closed executor / authority-root progression are unchanged.

## 2. Prior HIGH closure

### Prior HIGH-1 — early FAIL rollback used the superseded three-key null-record: CLOSED

The remediation no longer restates the old three-key literal. The `tool_identity` / `environment` / `authority` / `lineage` row now explicitly refers to the one canonical five-key not-required rollback record already frozen above:

`{before_snapshot:null,after_snapshot:null,before_snapshot_sha256:null,after_snapshot_sha256:null,verified:null}`.

This removes the missing-key contradiction while preserving exact unknown/missing/extra-key rejection.

### Prior HIGH-2 — worktree snapshot was not uniquely derivable: CLOSED

The remediation now freezes the worktree derivation end-to-end for this transaction scope:

- exact fixed six repo-relative POSIX paths: the five collection paths plus the single receipt path;
- deterministic UTF-8 byte path ordering;
- exact entry key set `{path,mode,kind,sha256}`;
- `mode` as JSON string `100644` or `100755`, derived from `git ls-files --stage -- <path>` for tracked paths; untracked paths have null mode and therefore cannot masquerade as an allowed present regular-file entry;
- exact absent record `{path,mode:null,kind:"absent",sha256:null}`;
- exact present regular-file record with raw-byte SHA-256;
- symlink, directory, other type, normalization drift, and any porcelain entry outside the six-path allowlist fail closed;
- live dirty/untracked enumeration is fixed to `git status --porcelain=v1 -z --untracked-files=all`, while each allowlist path's filesystem type is independently checked with `find -P <path> -maxdepth 0 -printf '%y'`;
- staged/index state remains independently represented by `index_tree_native_oid`, so staged-vs-worktree differences cannot be hidden inside the worktree digest;
- `worktree_sha256` is the SHA-256 of the canonical ordered six-entry array.

Given the inherited transaction contract already forbids overwriting existing target paths and limits live mutation to these fixed paths, this yields one deterministic worktree snapshot representation for every admissible state and fails closed for non-admissible states.

## 3. Fresh audit

No new blocking contradiction was found in the remediated evidence contract.

The retained `before_snapshot` / `after_snapshot` objects, target-ref revision, local HEAD symbolic/detached identity, index tree OID, canonical worktree entry array and snapshot digest equality now together provide a machine-checkable rollback witness consistent with the approved closure contract. PASS and pre-live FAIL still use the exact not-required rollback record; live FAIL still preserves the primary failure phase and maps incomplete restoration to `ROLLBACK_INCOMPLETE`.

The existing push/publication violation encoding, candidate-construction versus post-handoff verification split, source-read prefix semantics, collection/receipt null-records, and post-check prefix semantics remain intact.

## 4. Formal verdict

`APPROVE_TO_DESIGN_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_CONTROLLED_EXECUTION`

Current blockers: **0**.  
Design/Authority blockers: **0**.  
Production blockers: **0**.  
Evidence-only blockers: **0**.

## 5. Scope

This approval closes only the docs-only controlled-execution design Gate for the exact formal pair above. It does not authorize executor implementation, real source selection/read/hash, authority-root materialization, collection/receipt mutation, source-evidence record/package/witness creation or write, publication materialization, real root audit, child/runtime modification, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler step, sidecar, training, evaluation, inference or LIBERO4IN1. Downstream progression remains the already frozen source-evidence/publication closure sequence before any GPU work.
