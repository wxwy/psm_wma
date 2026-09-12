# ChatGPT Review — Immutable Source Authority Root synthetic CPU/static Implementation remediation 2

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-CPU-STATIC-IMPLEMENTATION`

## Exact formal pair

- root implementation SHA: `ae52cb313cfafda4eedad600501030f4dc01297c`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

This is a fresh review because the formal root changed from `fce040f645e2427d11d9cd9026adc2f0e8004bda`; the child is unchanged.

The formal root tree was independently checked: `cosmos-framework` is mode `160000`, type `commit`, and points exactly to `93a89ba61306d840a008813f62f26a34d54850f4`. That child commit is reachable in `wxwy/cosmos-framework`.

## Review basis

Reviewed against:

- authority-root materialization/binding design v0.1 + ABI v0.2;
- authority-root CPU/static implementation design v0.1 + v0.2 supersession;
- prior ChatGPT implementation reviews for `8cd1103... / 93a89ba...` and `fce040f... / 93a89ba...`;
- the current production files `immutable_source_authority_root.py` and `immutable_source_collection.py` plus direct stdlib tests;
- the actual source-open path `_bound_source_inputs()` / `collect_synthetic()`.

MM/Kimi conclusions are coordination clues only and are not inherited as ChatGPT's technical conclusion.

## Prior blocker closure

The two blockers from the immediately previous `fce040f...` review are closed:

1. **Prior HIGH — verifier accepted a parent that already contained a fixed path: CLOSED.** `_candidate_mapping()` now rejects either fixed path being present in the formal parent, and the direct verifier test constructs adversarial parents for both selection and config paths.
2. **Prior MEDIUM — private collection helpers used as a cross-module API: CLOSED.** `immutable_source_collection.py` now exposes the explicit public aliases `canonical_json_bytes`, `sha256_digest`, `validated_git_tree`, and `git_blob_oid`; the authority module consumes only those public names.

The earlier structural-parent/Gitlink, two-endpoint observation, typed non-serialization, and verifier→real-executor Evidence remediations remain present.

## Current blocker

### HIGH-1 — the real collection executor still does not independently enforce the same authority-root parent contract before source open

**Location:** `tools/psm_wma/immutable_source_collection.py:627` (`_authority_tree` / `GitTransaction.parent`)

**Root cause**

The current remediation hardens the producer/verifier, but the production consumer still uses the older weaker authority-tree check:

- `GitTransaction.parent(revision) -> str` exposes only one parent value, so `_authority_tree()` cannot independently prove **exactly one** parent;
- `_authority_tree()` does not require the two fixed authority paths to be absent from the formal parent.

Consequently an invalid authority root can still pass the real collection executor even though the upstream verifier would reject it. A concrete counterexample is:

1. the formal parent already contains both fixed paths as ordinary `100644/blob` entries with old bytes;
2. the candidate authority commit replaces those two entries with the approved raw bytes;
3. `changed == {selection_path, config_path}` remains true;
4. mode/type checks remain true;
5. the supplied seven-key tuple, blob OIDs/raw SHA-256, and fixed local/remote authority ref all match the candidate.

Under the current `_authority_tree()` this reaches the remainder of `_bound_source_inputs()` and can proceed toward source open. The valid authority contract, however, requires the formal parent to contain neither fixed path and requires the authority commit to be exact single-parent.

This is not cured by the stronger upstream `verify_candidate()`: the frozen architecture explicitly requires the collection executor to rederive authority state from Git objects before source open rather than trust that every caller/ref arrived through the approved producer path.

**Violated frozen contract**

- Materialization/binding design v0.1 §3: parent already containing either fixed path is a FAIL; authority commit has exactly one parent equal to the materialization formal root.
- Materialization/binding design v0.1 §4: the collection executor must independently recompute the authority root's parent/delta/object binding before source open.
- CPU/static implementation design v0.2 §1: the real `_bound_source_inputs()` / `collect_synthetic()` path is part of the implementation allowlist and must fail closed pre-source, not rely on a caller-side or upstream-only validator.

**Why current Evidence is insufficient**

The new test correctly proves the upstream verifier rejects pre-existing fixed paths, but `test_immutable_source_collection.py` still initializes a valid parent with both fixed paths absent and has no adversarial consumer-side witness for:

- authority parent already containing selection/config fixed paths;
- zero/multiple authority parents hidden by a singular `parent()` API.

Thus `47/47 PASS` does not witness the production consumer predicate that is still missing.

**Exact acceptance**

Keep remediation in this same implementation Gate and within the already-approved four-file allowlist:

1. strengthen the collection `GitTransaction` authority lookup so the executor can prove exact parent multiplicity (`parents(revision) -> tuple[...]` or an equivalent fail-closed exact-single-parent API);
2. in `_authority_tree()`, require the authority revision to have exactly one parent equal to `lineage["authority_approval_formal_root_revision"]`;
3. before evaluating the two-path delta, require `SELECTION_PATH` and `COLLECTION_PATHS[1]` to be absent from the formal parent tree;
4. retain the existing exact full-entry delta, blob/raw-byte/OID/SHA-256, lineage, fixed-ref local/remote, and pre-source ordering checks;
5. add direct `collect_synthetic()` / `_bound_source_inputs()` adversarial tests for each fixed path pre-existing in the formal parent and for zero/two-parent authority roots, using a source-open sentinel that must never be reached and asserting zero Git/ref/source mutation;
6. preserve all currently passing producer/verifier, rollback/race, typed-boundary, and verifier→executor tests.

## Blocker summary

- production/contract blockers: `1 HIGH`
- Evidence-only blockers: `0`
- total blockers: `1`

The reported `47/47 PASS`, Ruff, `py_compile`, and `git diff --check` are useful auxiliary evidence, but they do not close this remaining consumer-side authority predicate.

## Final verdict

`REQUEST_CHANGES(tools/psm_wma/immutable_source_collection.py:627)`

This verdict binds only the exact formal pair `ae52cb313cfafda4eedad600501030f4dc01297c` / `93a89ba61306d840a008813f62f26a34d54850f4`.

Remediation remains in the same authority-root synthetic CPU/static implementation Gate. This verdict does **not** authorize real selection/config JSON creation, authority commit/ref creation, real source or remote I/O, collection/receipt/source-evidence/publication, child/runtime modification, checkpoint/data/cache I/O, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1.
