# ChatGPT Independent Review — R09-B TTT v0.3.5 Immutable Source Collection Controlled Execution CPU/static Implementation

**Date:** 2026-09-12  
**Formal root:** `fb9c5e04e811865247e2ed44072af59acc8b93c9`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-IMPLEMENTATION-DESIGN`

## 1. Pair / scope

- Re-locked remote `V2`, re-read live `docs/collab/chatgpt/CODEX_INBOX.md`, and confirmed this exact pair is the current CPU/static implementation request.
- Independently verified formal root `fb9c5e04e811865247e2ed44072af59acc8b93c9` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Incremental baseline is the approved implementation-design pair `97ed73442fc56aa57e4bae27028bc5ffef7897bc` / same child.
- The implementation stays inside the approved two-file technical allowlist: `tools/psm_wma/immutable_source_collection.py` and `tools/psm_wma/test_immutable_source_collection.py`; other changes are review / Inbox / bookkeeping. No child change is present.

## 2. Findings

### HIGH-1 — Evidence — implementation emits a different six-key toy record instead of the approved exact `immutable_source_collection_execution_evidence_v1`

**Location:** `tools/psm_wma/immutable_source_collection.py:70-119`

`MemoryEvidenceSink.emit()` accepts only `{schema_version,phase,status,authority,candidate,snapshot}`, and `collect_synthetic()` emits exactly that reduced shape. The approved evidence contract requires outer exact keys `schema,status,execution,tool,environment,authority,lineage,source_entries,handoff,candidates,collection,receipt,post_checks,push_publication,rollback,evidence_sha256`, with exact nested PASS/FAIL branch typing and canonical SHA-256 semantics.

The current 5/5 tests therefore prove a newly invented CPU_STATIC record, not the reviewed execution-evidence ABI. They also do not exercise FAIL evidence branch typing, `evidence_sha256`, tool/environment identity, post-check/push-publication state, or the exact rollback record.

**Acceptance:** implement the approved exact evidence builder/verifier unchanged in the production executor code path. CPU/static tests may use synthetic values, but the record schema, branch/nullability rules, canonical JSON and `evidence_sha256` must be byte-for-byte the approved contract.

### HIGH-2 — Authority / lineage — the reviewed authority-root and target-lineage contracts are replaced by a four-string toy tuple

**Location:** `tools/psm_wma/immutable_source_collection.py:89-107`

`_exact_authority()` only accepts `{formal_root,formal_child,base,target}` and `collect_synthetic()` only checks `git.resolve("base")` and `git.resolve("target")`. `formal_child` is never verified. There is no execution-authority seven-field tuple, no authority-root parent/path/blob/raw-SHA validation, no fixed selection/config paths, and no target lineage `{target_ref,expected_base_root_revision,expected_child_gitlink,authority_approval_formal_root_revision}` verification.

This does not witness the implementation-design acceptance inventory for authority tuple/parent/path/blob drift or target/base/Gitlink drift.

**Acceptance:** represent and validate the exact approved authority tuple and target-lineage tuple in the same production path. CPU/static Git doubles must independently witness authority parent/path/blob/raw-byte drift and child-Gitlink drift, not merely compare caller labels.

### HIGH-3 — Source-read safety — `read_regular()` twice is not the approved same-opened-FD / fstat contract

**Location:** `tools/psm_wma/immutable_source_collection.py:36-61, 101-111`

The approved execution contract requires rooted directory-FD traversal with symlink rejection, one opened regular-file FD per entry, pre/post `fstat` equality for identity/size/mtime/ctime, rewind, and a second complete hash from that same FD. The implementation exposes only `read_regular(path) -> bytes` and calls it twice. Nothing prevents the two calls from opening or representing different file objects, and there is no fstat/inode/size/mtime/ctime witness at all.

`RacingFd` only changes returned bytes on later calls; it does not test same-FD identity drift or fstat drift. The synthetic map also does not directly witness symlink traversal rejection.

**Acceptance:** freeze a descriptor-level injected seam that models one opened entry handle/FD and exposes the required pre/post stat + rewind/read lifecycle; direct tests must cover symlink/component escape, non-regular final FD, identity/size/mtime/ctime drift, and second-hash drift.

### HIGH-4 — Candidate derivation / one-shot handoff — current handoff is an arbitrary Mapping wrapper, not `immutable_source_collection_preflight_handoff_v1`

**Location:** `tools/psm_wma/immutable_source_collection.py:75-87, 111-119`

`OneShotHandoff.take()` accepts any mapping, can be constructed independently of the source-read producer, and simply returns a dict copy once. In the test it consumes the final synthetic evidence record. It does not bind the reviewed authority tuple, ordered `(ordinal,byte_length,sha256)` entries, five candidate artifact path/schema/raw-SHA values, config digest, or `candidate_handoff_sha256`; nor does it provide the closure candidate raw blobs only through the same-activation one-shot object.

Likewise `candidate` is merely five caller-selected source names with raw file hashes; it does not implement the approved canonical chain `input descriptor -> manifest -> immutable source identifier -> checkpoint descriptor -> collection artifact` plus canonical config.

**Acceptance:** construct the exact five canonical candidate artifacts/config in the production path and create the typed same-activation one-shot handoff only after derivation. The handoff must be non-reconstructable from caller mappings, one-shot, and bind all approved logical fields plus `candidate_handoff_sha256`.

### HIGH-5 — Git transaction / five-plus-one allowlists / rollback — the production `GitTransaction` seam has no transaction capability

**Location:** `tools/psm_wma/immutable_source_collection.py:24-31, 89-132`

`GitTransaction` exposes only `resolve()`. The implementation has no isolated temporary index/tree preflight, no exact five collection output paths, no exact one receipt path, no collection parent/receipt parent construction, no committed-tree re-lookup/post-check, no target-ref/HEAD/index/worktree snapshot construction, and no actual rollback path. `verify_synthetic_rollback()` merely compares two arbitrary mappings and a boolean.

This means the reviewed executor source cannot later perform the approved real controlled transaction merely by swapping dependencies; real execution would require adding production transaction logic and exact `target_snapshot_v1` handling, changing the tool blob after CPU/static closure.

**Acceptance:** the CPU/static implementation must already contain the complete production transaction algorithm behind the injected Git/evidence/FD interfaces. Tests may route it to temporary repositories/sinks only, but must directly witness isolated preflight, exact five-path collection + one-path receipt commits/parents/post-checks, retained exact `target_snapshot_v1`, rollback restoration, and `ROLLBACK_INCOMPLETE`.

## 3. Positive findings

- The formal implementation stays inside the two approved technical file paths and does not modify the child.
- The module uses only stdlib-level constructs and does not itself access real source/checkpoint/cache paths, network, CUDA/GPU, model code, optimizer/scaler or training.
- The explicit Protocol-based DI direction is compatible with the approved design; the blocker is that the production semantics behind those interfaces are still incomplete.
- Existing unit tests do catch simple unknown authority keys, duplicate source paths, path escape/non-bytes, returned-byte drift, second handoff use and a generic rollback mismatch.

## 4. Formal verdict

`REQUEST_CHANGES(tools/psm_wma/immutable_source_collection.py:70)`

Current blockers: **5 HIGH**.  
Evidence-only blockers: **1**.  
Design/Authority blockers: **1**.  
Implementation blockers: **3**.  
Production blockers: **0** only in the sense that no real execution is authorized yet; the implementation is not ready to be identity-bound for production use.

## 5. Scope

This verdict does not reopen the approved controlled-execution / evidence designs or the interpreter-authority remediation. It does not authorize authority-root materialization, real source selection/read/hash, collection/receipt mutation, source-evidence record/package/witness write, publication, real root audit, child/runtime modification, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler/scaler step, sidecar, training, evaluation, inference or LIBERO4IN1.
