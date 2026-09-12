# ChatGPT Review — Immutable Source Authority Root synthetic CPU/static Implementation remediation

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-CPU-STATIC-IMPLEMENTATION`

## Exact formal pair

- root implementation SHA: `fce040f645e2427d11d9cd9026adc2f0e8004bda`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

This is a fresh review because the formal root changed from the prior reviewed `8cd1103deecc0720b7168e9e2b86b576e818b2bd`; the child is unchanged. The formal root tree was independently checked: `cosmos-framework` is mode `160000`, type `commit`, and points exactly to `93a89ba61306d840a008813f62f26a34d54850f4`. That child commit is reachable in `wxwy/cosmos-framework`.

## Prior blockers closure

All four blockers from the `8cd1103... / 93a89ba...` review are materially closed in this pair:

1. exact parent multiplicity is now observable through `parents()`, `_candidate_mapping()` requires exactly `(materialization_formal_root,)`, formal-root Gitlink is checked as the full `("160000", "commit", expected)` entry, and the same structural validator runs both immediately after create and independently in `verify_candidate()`;
2. pre/post publication observation uses `_observe_refs()` to read local and remote independently, and rollback always independently performs final local and remote observations before aggregation;
3. request, candidate, binding, and publication witness now reject copy/deepcopy/pickle as frozen typed boundaries;
4. direct CPU/static Evidence now passes the exact verifier-produced seven-key mapping into real `collect_synthetic()`, after the approved synthetic publication state, with direct pre-source negative cases.

The reported `46/46 PASS`, Ruff, `py_compile`, and `git diff --check` are useful auxiliary Evidence, but the current pair still has the blockers below.

## Current blockers

### HIGH-1 — independent verifier still accepts a forbidden authority parent that already contains a fixed materialization path

**Location:** `tools/psm_wma/immutable_source_authority_root.py:222-229` (`_candidate_mapping`)

**Root cause**

The retained authority materialization contract explicitly requires failure if the materialization formal parent already contains either fixed authority artifact path. `prepare_candidate()` enforces that predicate before creation, but the independent verifier path does not.

`_candidate_mapping()` loads `before` and `after` and only requires the changed-path set to equal the two fixed paths. Therefore a caller-supplied candidate can still pass independent verification when:

- the formal parent already contains one or both fixed paths with different bytes/OIDs;
- the candidate replaces those existing entries with the requested canonical bytes;
- the only changed paths are still exactly the two fixed paths.

That state satisfies the current `changed == set(paths)` predicate even though the frozen authority contract says a parent that already contains either path is invalid. Because `AuthorityCandidate` is intentionally a typed input to an independent verifier, `verify_candidate()` may not trust that the candidate necessarily came through the current `prepare_candidate()` call.

**Violated frozen contract**

`PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_materialization_binding_design_v0.1.md` §3: `若 parent 已含任一路径 ... 则 FAIL`; §4 requires an independent verifier rather than trust in the materializer. The implementation design v0.1 likewise requires the verifier to independently recompute the exact authority structure.

**Why current Evidence is insufficient**

`test_noncanonical_and_parent_fixed_path_fail_before_commit` witnesses the prepare-stage rejection only. There is no adversarial verifier test where the formal parent already contains a fixed path and a separately supplied candidate replaces it.

**Exact acceptance**

Within this same implementation Gate:

1. in the shared independent candidate-structure validator, before accepting the delta, require both fixed authority paths to be absent from the formal parent tree;
2. keep the current exact two-path changed-set, `100644/blob`, raw-byte/OID, inherited-entry and Gitlink checks unchanged;
3. add a direct `verify_candidate()` negative test with a formal parent that already contains one fixed path, plus a candidate that replaces it with the approved raw bytes while otherwise satisfying the two-path delta; it must fail;
4. cover both fixed paths (individually or table-driven), and preserve the existing prepare-stage fail-before-create test.

### MEDIUM-2 — current authority module turns collection-private helpers into a cross-module production API, contrary to the frozen reuse boundary

**Location:** `tools/psm_wma/immutable_source_authority_root.py:14-24`

**Root cause**

The approved implementation design v0.1 deliberately froze a reuse boundary: authority-root code must reuse the collection executor's canonical JSON/full-tree/OID/digest semantics, but private helpers must not become a cross-module interface. If shared helpers are needed, the approved remedy is a minimal public alias/rename in `immutable_source_collection.py` within the now-approved four-file allowlist.

The current production module directly imports `_blob_oid`, `_canonical`, `_digest`, and `_tree` from `immutable_source_collection.py`. This gets the current semantics right, but violates the explicitly frozen module/API boundary and makes the authority implementation depend on collection internals that the design forbade as a production interface.

**Violated frozen contract**

Implementation design v0.1 §1: `为避免私有函数成为跨模块接口，仅允许把上述已存在纯validator做最小同文件公开别名/重命名并保持现有executor与32个测试行为不变`.

**Exact acceptance**

Within the existing four-file allowlist:

1. expose the required canonical/tree/blob/digest validation semantics through minimal public helper names or a public shared validator surface in `immutable_source_collection.py`;
2. update the authority-root module to import/use only that public surface, without copying a second weaker validation implementation;
3. preserve the existing collection executor acceptance/rejection behavior and direct tests;
4. keep all four-file CPU/static tests passing and show the implementation delta remains limited to the approved allowlist plus bookkeeping.

## Non-blocking Evidence note

The new direct producer -> consumer test closes the prior HIGH Evidence gap. While touching the test, add an alias-only negative (`root_revision` removed and `authority_root_revision` inserted) in addition to the already-covered dual-key, missing-key and extra-key cases, so the v0.2 ABI matrix is literally complete. Production already rejects it through the exact key-set predicate, so this is not counted as an additional blocker here.

## Blocker summary

- production/contract blockers: `2` (`1 HIGH`, `1 MEDIUM`)
- Evidence-only blockers: `0`
- total blockers: `2`

## Final verdict

`REQUEST_CHANGES(tools/psm_wma/immutable_source_authority_root.py:222)`

This verdict binds only the exact formal pair `fce040f645e2427d11d9cd9026adc2f0e8004bda` / `93a89ba61306d840a008813f62f26a34d54850f4`.

Remediation stays in the same authority-root synthetic CPU/static implementation Gate. This verdict does **not** authorize real selection/config JSON creation, authority commit/ref creation, real source or remote I/O, collection/receipt/source-evidence/publication, child/runtime modification, checkpoint/data/cache I/O, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1.
