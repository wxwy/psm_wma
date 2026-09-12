# ChatGPT Independent Review — R09-B TTT v0.3.5 Controlled Collection Execution Evidence rollback-semantics remediation

**Date:** 2026-09-12  
**Formal root:** `9a3f584f36254e00e9483c170f948cc6614b56fd`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-DESIGN`

## 1. Pair / scope

- Re-locked remote `V2`, re-read live `docs/collab/chatgpt/CODEX_INBOX.md`, and confirmed this exact pair is the current formal remediation request for the Gate.
- Independently verified formal root `9a3f584f36254e00e9483c170f948cc6614b56fd` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Incremental baseline is prior rejected pair `9efae217d8c45b7afd651d52e3cb5b8cc63226f9` / same child and its canonical review.
- Incremental technical scope remains docs-only and limited to rollback-evidence semantics in `immutable_source_collection_execution_evidence_design_v0.1.md` plus bookkeeping. Child/runtime and the already-closed executor/authority-root progression are unchanged.

## 2. Prior HIGH closure

### Prior HIGH-1 — PASS path falsely required rollback verification: CLOSED

The remediation now freezes PASS and pre-live FAIL rollback as the exact not-required null-record `{before_snapshot_sha256:null,after_snapshot_sha256:null,verified:null}` and explicitly forbids reusing `verified=true` to mean “not required”. This matches the inherited execution model in which rollback is only a recovery outcome after a live primary failure.

### Prior HIGH-2 — `verified=true` had no equality predicate: PARTIALLY CLOSED

The remediation adds `target_snapshot_v1`, canonical JSON hashing, and requires `before_snapshot_sha256 == after_snapshot_sha256` for `verified=true`. This closes the previous pure-boolean claim. However the evidence is still not independently reconstructable and the snapshot does not exactly encode every inherited recovery dimension, as described below.

## 3. Findings

### HIGH-1 — Evidence-only — rollback equality is not independently re-auditable because the evidence stores only snapshot digests, not the historical canonical snapshot records or an immutable binding to them

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_execution_evidence_design_v0.1.md:49`

The outer evidence still contains only `rollback={before_snapshot_sha256,after_snapshot_sha256,verified}`. The new paragraph defines the logical shape of `target_snapshot_v1`, but neither the exact before/after snapshot objects nor a fixed immutable artifact/receipt identity for them is part of the execution evidence.

A later read-only auditor can recompute the *current/after* state, but it cannot reconstruct the historical pre-live target/index/worktree state merely from a SHA-256 digest after the transaction has executed. Saying that “executor and independent audit both recompute from actual before/after state” does not freeze how a later independent audit obtains the historical `before` object. Two equal digests therefore remain an assertion unless the pre-live snapshot bytes are themselves retained or immutably bound before mutation.

This is especially important because the approved closure contract explicitly accepts a controlled target/index/worktree snapshot handle before live mutation and requires rollback restoration to be independently provable.

**Acceptance:** preserve the exact pre-live snapshot authority in a non-replaceable form before mutation and make it machine-verifiable after the run. Either (a) include exact canonical `before_snapshot` and `after_snapshot` records in the execution evidence and hash them, or (b) bind the before snapshot to an immutable pre-live snapshot artifact/receipt with fixed schema/path/blob/raw-SHA identity and include that binding in the evidence, while the after snapshot is independently recomputed. `verified=true` must require the exact retained/bound before object and independently observed after object to compare equal component-by-component, not merely two ungrounded digest strings.

### HIGH-2 — Evidence-only — `target_snapshot_v1` does not exactly encode the inherited target-ref / HEAD / index / worktree restoration state, and `worktree_tree_native_oid` has no frozen derivation

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_execution_evidence_design_v0.1.md:49`

The approved closure contract freezes and later restores `target ref`, `HEAD`, `index tree`, and `worktree allowlist state` as distinct recovery dimensions. The new four-key snapshot is `{target_ref,head_revision,index_tree_native_oid,worktree_tree_native_oid}`, where `head_revision` is described as “该 ref 当前 40-hex HEAD”. That binds the named target ref to a commit, but it does not freeze the actual local `HEAD` state separately. A local HEAD could be detached or attached to a different ref at the same commit while this record still hashes identically, even though the inherited contract requires HEAD restoration as a separate item.

`worktree_tree_native_oid` is also treated as a 40-hex fact without freezing the deterministic derivation that converts the live worktree allowlist state into that Git tree OID. A normal Git working tree has no intrinsic tree OID independent of a specified temporary-index construction, tracked/untracked allowlist, file-mode/symlink treatment, and canonical path set. Without that derivation, an independent auditor cannot reproduce the field uniquely.

**Acceptance:** freeze an exact snapshot schema that separately captures the approved target ref and its resolved revision, the actual `HEAD` identity/state (including symbolic target vs detached form and revision), the approved index state, and the worktree allowlist state. Freeze the exact deterministic derivation for index/worktree snapshot digests/OIDs, including path allowlist and file-mode/symlink/untracked handling, so independent audit can reconstruct them. `verified=true` must imply exact equality of every inherited recovery component.

## 4. Positive findings

- PASS/pre-live rollback now has a correct exact not-required representation.
- Live primary failure identity remains separate from rollback outcome.
- `push_publication` violations remain representable as observed booleans with at least one `true`.
- Candidate construction remains separated from post-handoff candidate verification and is consistent with the inherited one-shot handoff lifecycle.
- Formal root Gitlink is exact and the child commit is reachable.

## 5. Formal verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_execution_evidence_design_v0.1.md:49)`

Current blockers: **2 HIGH**.  
Design/Authority blockers: **0**.  
Production blockers: **0**.  
Evidence-only blockers: **2**.

## 6. Scope

This verdict does not reopen the already-closed executor implementation/source-identity progression, authority-root materialization/binding, PASS/pre-live rollback null semantics, failure phase model, push/publication violation encoding, candidate handoff lifecycle, or collection/receipt null-record contracts. It does not authorize executor implementation, real source selection/read/hash, authority-root materialization, collection/receipt mutation, source-evidence record/package/witness creation or write, publication materialization, real root audit, child/runtime modification, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler step, sidecar, training, evaluation, inference or LIBERO4IN1.
