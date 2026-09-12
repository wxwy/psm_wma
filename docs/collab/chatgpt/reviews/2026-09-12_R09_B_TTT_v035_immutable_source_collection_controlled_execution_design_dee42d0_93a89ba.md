# ChatGPT Independent Review — R09-B TTT v0.3.5 Controlled Collection Execution Evidence retained rollback-snapshot remediation

**Date:** 2026-09-12  
**Formal root:** `dee42d02a3e40b5da66c8ac96a8a4d5a66066665`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-DESIGN`

## 1. Pair / scope

- Re-locked remote `V2`, re-read live `docs/collab/chatgpt/CODEX_INBOX.md`, and confirmed this exact pair is the current formal remediation request for this Gate.
- Independently verified formal root `dee42d02a3e40b5da66c8ac96a8a4d5a66066665` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Incremental baseline is prior rejected pair `9a3f584f36254e00e9483c170f948cc6614b56fd` / same child and its canonical review.
- Incremental technical scope remains docs-only and limited to the rollback evidence schema in `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_execution_evidence_design_v0.1.md` plus bookkeeping. Child/runtime and the already-closed executor/authority-root progression are unchanged.

## 2. Prior HIGH closure

### Prior HIGH-1 — historical before snapshot had no retained/re-auditable object: CLOSED

The remediation upgrades `rollback` to include exact `before_snapshot` and `after_snapshot` objects as well as their SHA-256 values. It requires the before object to be retained before live mutation and the after object to be compared against it component-by-component. This satisfies the prior acceptance path of retaining canonical snapshot records in the execution evidence rather than keeping only ungrounded digest strings.

### Prior HIGH-2 — target ref / local HEAD / index / worktree were not separately encoded: PARTIALLY CLOSED

The new `target_snapshot_v1` now separately records the approved `target_ref` and resolved revision, local HEAD mode / symbolic ref / revision, and index tree OID. It also replaces the undefined worktree tree OID with an explicit `worktree_entries` array plus `worktree_sha256`. This closes the prior conflation of target-ref state with local HEAD state.

Two exact-schema / deterministic-derivation defects remain below.

## 3. Findings

### HIGH-1 — Evidence-only — early FAIL rollback null-record still uses the superseded 3-key schema

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_execution_evidence_design_v0.1.md:38`

The common exact rollback record is now five keys:

`{before_snapshot,after_snapshot,before_snapshot_sha256,after_snapshot_sha256,verified}`

and the text immediately above the FAIL table correctly defines the PASS / pre-live not-required record with all five keys set to null. However the `tool_identity` / `environment` / `authority` / `lineage` FAIL row still explicitly requires the old three-key literal:

`{before_snapshot_sha256:null,after_snapshot_sha256:null,verified:null}`.

Under this same evidence contract, missing or drifted nested exact keys are FAIL. Therefore these four early failure phases still have no legal canonical evidence record: following the table omits two mandatory keys, while following the common five-key schema violates the row's "精确为" three-key record.

**Acceptance:** replace every residual pre-live rollback literal with the same exact five-key not-required null-record, or reference one single named null-record definition without restating a divergent key set. Unknown/missing/extra-key rejection must remain exact.

### HIGH-2 — Evidence-only — `worktree_entries` is still not uniquely derivable, so `worktree_sha256` is not independently reproducible

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_execution_evidence_design_v0.1.md:47`

The remediation correctly freezes a six-path worktree allowlist and defines absent vs regular-file records, but it leaves the `mode` field without an exact representation or derivation. The same filesystem state can therefore be serialized with different values/encodings (for example Git mode strings vs numeric/stat modes), yielding different canonical bytes and `worktree_sha256` values.

The phrase "超 allowlist path 均 FAIL" is also not tied to one deterministic enumeration of the live worktree state. The evidence schema does not freeze whether this means untracked paths, tracked modifications, staged-vs-worktree deltas, or all filesystem entries, nor the exact Git command / path normalization used to detect such paths. A later independent auditor therefore cannot uniquely reconstruct the claimed worktree snapshot from the repository state.

This remains narrower than the prior blocker: target ref, local HEAD and index derivations are now explicit; only the worktree component is still non-canonical.

**Acceptance:** freeze the exact worktree derivation end-to-end: the fixed repo-relative path set, the exact file-mode representation and allowed values, exact regular-file byte hashing, exact absent representation, and the exact rule/command semantics for detecting any out-of-allowlist dirty/untracked/symlink/directory state. The auditor must have exactly one valid `worktree_entries` array for a given approved worktree state and must recompute the same `worktree_sha256` byte-for-byte.

## 4. Positive findings

- `before_snapshot` / `after_snapshot` objects are now retained in the canonical evidence rather than represented only by hashes.
- Target ref revision and actual local HEAD symbolic/detached identity are separated.
- Index snapshot is deterministically tied to `git write-tree` on the controlled index.
- `verified=true` now requires exact object/key/entry/digest equality; rollback failure still preserves the primary failure phase and maps to `ROLLBACK_INCOMPLETE`.
- Prior push/publication violation encoding and candidate-construction vs post-handoff-verification lifecycle remain closed.
- Formal Gitlink is exact and the child commit is reachable.

## 5. Formal verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_execution_evidence_design_v0.1.md:38)`

Current blockers: **2 HIGH**.  
Design/Authority blockers: **0**.  
Production blockers: **0**.  
Evidence-only blockers: **2**.

## 6. Scope

This verdict does not reopen the already-closed executor implementation/source-identity progression, authority-root materialization/binding, target-ref / local-HEAD separation, retained before/after snapshot concept, failure phase model, push/publication violation encoding, candidate handoff lifecycle, or collection/receipt null-record contracts. It does not authorize executor implementation, real source selection/read/hash, authority-root materialization, collection/receipt mutation, source-evidence record/package/witness creation or write, publication materialization, real root audit, child/runtime modification, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler step, sidecar, training, evaluation, inference or LIBERO4IN1.
