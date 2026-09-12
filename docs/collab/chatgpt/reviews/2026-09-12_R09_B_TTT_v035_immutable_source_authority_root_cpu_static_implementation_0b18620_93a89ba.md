# ChatGPT Review — Immutable Source Authority Root synthetic CPU/static Implementation remediation 3

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-CPU-STATIC-IMPLEMENTATION`

## Exact formal pair

- root implementation SHA: `0b18620f84959bf25379f3c227b796edc1097efd`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

This is a fresh review because the formal root changed from `ae52cb313cfafda4eedad600501030f4dc01297c`; the child is unchanged.

The formal root tree was independently checked: `cosmos-framework` is mode `160000`, type `commit`, and points exactly to `93a89ba61306d840a008813f62f26a34d54850f4`. That child commit is reachable in `wxwy/cosmos-framework`.

## Review basis

Reviewed against:

- authority-root materialization/binding design v0.1 + ABI v0.2;
- authority-root CPU/static implementation design v0.1 + v0.2 supersession;
- prior ChatGPT implementation reviews for `8cd1103...`, `fce040f...`, and `ae52cb3...` with the same child;
- current production `tools/psm_wma/immutable_source_collection.py` and its direct stdlib tests;
- the actual pre-source consumer path `_authority_tree()` -> `_bound_source_inputs()` -> `collect_synthetic()`.

MM/Kimi conclusions are coordination clues only and are not inherited as ChatGPT's conclusion.

## Prior blocker closure

The single HIGH from the immediately previous `ae52cb3...` review is **CLOSED**.

### Prior HIGH — real collection consumer did not independently enforce exact authority parent contract: CLOSED

The current implementation now gives the real consumer an exact parent-multiplicity seam:

- `GitTransaction.commit_parents(revision) -> tuple[str, ...]`;
- `TemporaryGitFixture.commit_parents()` preserves the existing fixture constructor while representing zero/one/multiple parents explicitly;
- `_authority_tree()` requires `git.commit_parents(revision) == (authority_approval_formal_root_revision,)`.

The consumer also now rejects a formal parent containing either fixed authority path **before** evaluating the candidate delta:

- `SELECTION_PATH` must be absent from the formal parent;
- `COLLECTION_PATHS[1]` must be absent from the formal parent.

The direct consumer-side tests exercise the real `collect_synthetic()` path with an `Unopened` source sentinel and cover:

- selection path pre-existing in the formal parent;
- config path pre-existing in the formal parent;
- zero-parent authority revision;
- two-parent authority revision.

Each case is rejected before source open and asserts zero synthetic commits. This satisfies the prior acceptance requirement that the collection executor independently rederive and fail closed on the same authority-root parent contract rather than trust the upstream producer/verifier.

## Regression check

The remediation is narrow and does not weaken the previously closed contracts:

- exact seven-key authority ABI remains unchanged;
- fixed `AUTHORITY_REF` local+remote pre-source checks remain in the real executor path;
- producer/verifier exact-parent and fixed-path checks remain stronger and aligned with the consumer;
- full-tree delta, inherited-entry, blob/OID/raw-byte/SHA-256 checks remain present;
- publication ordering, ownership-aware rollback, foreign-ref preservation, and two-endpoint observations remain unchanged;
- typed non-serialization and direct verifier-output -> real executor Evidence remain present;
- the shared public canonical/tree/blob/digest helper surface remains in place; no private helper regression was introduced.

The commit changes only the already-approved collection production/test files plus root bookkeeping. No child/runtime change, real source/ref/remote I/O, GPU, or training scope was introduced.

## Evidence assessment

The reported `47/47 PASS`, Ruff, `py_compile`, and `git diff --check` are useful auxiliary evidence. The approval here does not rely on the count alone: the reviewed source and direct adversarial tests materially witness the exact predicate that was previously missing in the production consumer path.

## Current blocker count

`0`

## Final verdict

`APPROVE_TO_CLOSE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_CPU_STATIC_IMPLEMENTATION`

This verdict binds only the exact formal pair `0b18620f84959bf25379f3c227b796edc1097efd` / `93a89ba61306d840a008813f62f26a34d54850f4` and this Gate.

Closure only means the frozen synthetic CPU/static authority-root implementation is complete. It does **not** authorize real selection/config JSON creation, real authority commit/ref creation or publication, real source/remote I/O, collection/receipt/source-evidence/publication mutation, child/runtime modification, checkpoint/data/cache I/O, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1. The next step remains the separately gated real materialization execution request defined by the approved design chain.