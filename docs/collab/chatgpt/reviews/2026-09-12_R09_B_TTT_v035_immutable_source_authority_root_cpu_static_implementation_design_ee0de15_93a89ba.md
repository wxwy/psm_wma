# ChatGPT Review — Immutable Source Authority Root CPU/static Implementation Design v0.2

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-CPU-STATIC-IMPLEMENTATION-DESIGN`

## Exact formal pair

- root design SHA: `ee0de157d337bc85bf3d8d1c9e4957c31aa03c07`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

This is a fresh review because the root formal SHA changed from the previously reviewed `c61f32f3a99688043f2dfdb3d69480e11b1811dd`; the child is unchanged. Request/ledger/bookkeeping HEADs are coordination state only and are not substituted for this formal pair.

The formal root tree was independently checked: `cosmos-framework` is mode `160000`, type `commit`, and points exactly to `93a89ba61306d840a008813f62f26a34d54850f4`. That child commit is reachable in `wxwy/cosmos-framework`.

## Incremental review basis

Reviewed against:

- current v0.2 design at the exact formal root;
- prior ChatGPT review on `c61f32f3a99688043f2dfdb3d69480e11b1811dd` / `93a89ba61306d840a008813f62f26a34d54850f4`;
- retained authority-root materialization/binding v0.1 + v0.2 contracts;
- the actual approved collection executor seam in `tools/psm_wma/immutable_source_collection.py` and its direct tests;
- the formal commit delta and actual Gitlink entry.

The formal commit is docs-only: it adds the v0.2 supersession and updates `SESSION.md` / `TODO.md`; it does not modify runtime, child, source, authority refs, collection artifacts, GPU, or training code.

## Prior blocker closure

### CLOSED — HIGH-1 / pre-source fixed authority-ref check

The prior blocker required the retained fixed authority ref to be revalidated by the actual collection executor path before any source open, rather than by a caller/wrapper.

v0.2 closes this directly:

1. the implementation allowlist is expanded to the authority-root tool/test plus `immutable_source_collection.py` and its direct test;
2. `GitTransaction` is required to expose typed local and remote fixed-ref read observations;
3. `_bound_source_inputs()` must perform both fresh observations after the existing object/parent/tree/blob/raw-byte and lineage checks but before source open;
4. both endpoints must resolve exactly to `authority["root_revision"]`;
5. absent, wrong-target, disagreement, or observation error must fail before the source-open sentinel with zero ref/source mutation;
6. acceptance explicitly requires exercising the real `_bound_source_inputs()` / `collect_synthetic()` path, not a wrapper or key-set-only test.

This satisfies the prior acceptance condition and preserves the exact seven-key executor ABI.

### CLOSED — HIGH-2 / ownership-aware publication rollback

The prior blocker required publication/rollback to preserve concurrent foreign refs and prove endpoint ownership before deletion.

v0.2 closes this by freezing an explicit state machine:

1. fresh local+remote absent observation;
2. local expected-absent → exact-candidate CAS, then activation-owned `local_created` witness;
3. remote expected-absent → exact-candidate CAS, then activation-owned `remote_created` witness;
4. fresh post-CAS local+remote exact-candidate relookup followed by committed-binding re-verification;
5. fail-stop rollback in reverse endpoint order, with no publication retry;
6. rollback may mutate only endpoints created by the same activation and only by conditional exact-candidate → absent compare-and-delete;
7. foreign revisions, unreadable state, failed compare-delete, or unprovable ownership are preserved and force `ROLLBACK_INCOMPLETE`;
8. rollback success requires fresh independent local+remote observations proving both absent.

The CPU/static race matrix now directly covers first-CAS races, post-CAS drift, rollback-time drift, partial success/conflict combinations, unreadable observations, missing witnesses, compare-delete failures, foreign-ref preservation, and clean reverse-order rollback.

This satisfies the prior concurrency-safety acceptance condition.

## Retained contract review

No new blocker was found in the retained design contract:

- canonical selection/config byte/schema validation remains inherited;
- authority parent, exact two-path full-entry delta, inherited entry/Gitlink preservation and candidate distrust remain unchanged;
- fixed paths/ref remain non-overridable;
- the verified authority mapping remains the exact seven-key `root_revision` ABI;
- one-shot same-activation capability and copy/pickle/reconstruct/cross-request rejection remain inherited;
- the prior selection-validator reuse note is now implementable within the explicit four-file allowlist while requiring unchanged existing acceptance/rejection semantics;
- the Gate remains CPU/static synthetic only. Real Git/remote adapters and real authority materialization/execution remain separately gated.

## Current blockers

`0`

## Final verdict

`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_CPU_STATIC`

This verdict closes only the current docs-only implementation-design Gate and authorizes only the frozen four-file synthetic CPU/static implementation plus stdlib CPU/static tests after the required same-pair reviewer closure. It does **not** authorize real selection/config JSON creation, authority commit/ref creation or publication, real source or remote I/O, collection/receipt/source-evidence/publication mutation, child/runtime modification, checkpoint/data/cache I/O, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler/scaler steps, training, evaluation, inference, or LIBERO4IN1.
