# ChatGPT Independent Review — R09-B TTT v0.3.5 Immutable Source Collection Controlled Execution CPU/static Implementation remediation

**Date:** 2026-09-12  
**Formal root:** `08afbed4e1843c23a1cc3542f0184a1898c1772c`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-IMPLEMENTATION-DESIGN`

## 1. Pair / scope

- Re-locked remote `V2`, re-read live `docs/collab/chatgpt/CODEX_INBOX.md`, and confirmed this exact pair is the current CPU/static remediation request for this Gate.
- Independently verified formal root `08afbed4e1843c23a1cc3542f0184a1898c1772c` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Incremental baseline is rejected pair `1db0d539fd3d52fa7d521962a47204b578e0f94f` / same child. Technical remediation remains confined to the approved executor/test files plus session/review/Inbox bookkeeping; child/runtime are unchanged.
- I reviewed the formal-tree source and tests rather than treating the stated `29/29` CPU test result as closure evidence by itself.

## 2. Prior HIGH closure

All three blockers from the prior review are materially closed:

1. authority validation now computes the authority commit as an exact two-fixed-path delta over `authority_approval_formal_root_revision`, preserving inherited entries, and the late post-check reuses the same rule;
2. the `EvidenceSink` seam now explicitly requires atomic visibility semantics: successful return means accepted, while an exception guarantees no newly visible/persistent record; the in-memory fixture covers both partial-write and after-write failures and removes staged records before rethrow;
3. rollback/snapshot uncertainty now has a dedicated `RollbackUnavailable("ROLLBACK_INCOMPLETE")` fail-stop carrying the primary phase, and the executor does not manufacture a canonical PASS/FAIL record when an exact after-snapshot cannot be reconstructed.

These are valid remediations of the three previous HIGHs.

## 3. Fresh findings

### HIGH-1 — Design / Authority — tree-delta verification ignores Git tree mode/type identity

**Location:** `tools/psm_wma/immutable_source_collection.py:599`

`GitTransaction.tree_entries()` is still typed as `Mapping[str, str]` and `_authority_tree()` compares parent/root trees only as `path -> object-id` mappings. This detects added/deleted paths and blob-OID changes, but it cannot detect a Git tree entry whose mode/type changes while its object ID remains the same.

That means a mode-only change on an inherited file (for example `100644 -> 100755`) is invisible to the current `changed` set. The same issue applies to the fixed selection/config entries themselves: a regular blob could change mode while retaining the exact bound blob OID/raw bytes, and the implementation would still accept the authority commit as the exact two-path delta.

The frozen transaction is an exact Git-tree delta, not merely a blob-OID delta. The prior acceptance requirement also explicitly required every inherited parent-tree entry to remain object/tree-identical.

**Acceptance:** make the Git-tree inspection seam preserve and compare exact entry identity needed for delta verification — at minimum path + Git mode/type + native OID (or an equivalent canonical raw-tree-entry representation). `_authority_tree()` and its final post-check must reject any mode/type drift on inherited entries or the two fixed authority paths. Apply the same exact-entry semantics wherever parent/child committed-tree preservation is used for the five-path collection and one-path receipt deltas, so a real adapter cannot hide mode/type mutation behind an unchanged blob OID.

### HIGH-2 — Design / Authority — the production seam still does not verify selection-request transport bytes against authority bytes

**Location:** `tools/psm_wma/immutable_source_collection.py:620`

The frozen execution contract requires the caller transport `--selection-request <canonical-json-file>` to be byte-for-byte equal to the reviewed authority selection blob before any source entry is opened. It explicitly rejects caller/default mappings or transport-byte drift.

The current production algorithm receives only `paths: Mapping[str, str]`. `_bound_source_inputs()` reads and validates the authority selection blob from Git, but the caller-side input is reduced to a set/count comparison:

`len(paths) == len(ordered)` and `set(paths.values()) == set(ordered)`.

There is no selection transport raw-byte input and therefore no byte-equality check against `selection_raw_sha256` / the authority blob. The executor can only prove that a caller mapping names the same paths, not that the supplied canonical selection request is the reviewed transport object. Moving this validation later into an external real adapter would recreate exactly the source-identity problem the implementation design was meant to avoid: the reviewed executor blob would no longer contain the frozen transport validation semantics.

**Acceptance:** freeze the transport check inside the same unchanged production executor seam. Either accept the canonical selection-request raw bytes (or an injected descriptor-safe handle that yields those bytes) and require exact byte equality with the authority selection blob before source open, or remove caller selection-request authority entirely and derive the source-entry order exclusively from the reviewed authority blob under a correspondingly reviewed invocation contract. A caller-supplied parsed mapping/set comparison is not sufficient. Add CPU/static witnesses for byte drift that preserves identical semantic paths, non-canonical JSON with the same entries, and exact byte-equal PASS.

## 4. Positive findings

- The previous authority full-tree-versus-delta defect is fixed at the path/OID level and is rechecked after the live transaction.
- The atomic sink contract is now explicit at the DI boundary, and the in-memory sink correctly retracts partial/after-write staged records before propagating failure.
- Unavailable or invalid post-rollback snapshots now fail-stop as non-authoritative `ROLLBACK_INCOMPLETE` diagnostics rather than being silently reclassified as ordinary phase failure.
- Exact evidence ABI, same-opened-handle source reads, canonical candidate derivation, one-shot handoff, five-plus-one transaction, receipt relookup, post-check ordering and rollback paths remain intact.
- No real source/checkpoint/cache/network/GPU/model/training operation is introduced.

## 5. Formal verdict

`REQUEST_CHANGES(tools/psm_wma/immutable_source_collection.py:599)`

Current blockers: **2 HIGH**.  
Design/Authority blockers: **2**.  
Implementation blockers: **0 beyond those authority-seam defects**.  
Evidence-only blockers: **0**.

## 6. Scope

This verdict does not reopen the already-closed evidence ABI, same-FD source-read semantics, candidate derivation/handoff, transaction sequencing, atomic sink remediation, or unavailable-snapshot fail-stop handling. It only states that two remaining authority seams are still weaker than the frozen real-execution contract.

It does not authorize real source selection/read/hash, authority-root materialization, collection/receipt mutation, source-evidence record/package/witness creation or write, publication materialization, real root audit, child/runtime modification, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler/scaler step, sidecar, training, evaluation, inference or LIBERO4IN1.
