# ChatGPT Independent Review — R09-B2 P4-v4 Preflight Materialization Design v0.3

- Review date: 2026-09-02
- Repository: `wxwy/psm_wma`
- Branch: `V2`
- Reviewed design commit: `6055ee15e6f5c5867c746658975dc5e12d477de6`
- Formal request head: `b3eac75494b2f3c0c2ffd7c6f98abb9fe360bfc9`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Previous ChatGPT anchor: `b7bd62f2b48121a0604ffc600a20e8b84cafa88a`
- Scope: design-only review. No real request/preflight/materialization/P5/GPU/training actions were authorized or executed.

## Verdict

`REQUEST_CHANGES`

The three blockers from the v0.2 review are substantively closed:

1. admission authority is re-bound to canonical raw bytes + request SHA rather than a mutable admitted dict;
2. a per-capability one-shot latch gives a truthful zero-footprint first-mkdir failure terminal state;
3. the required same-backend `run_root -> import_staging -> token` ancestor relation is now explicitly exempted from the unexpected-overlap rejection rule.

One implementation-blocking contract contradiction remains.

## Blocking finding

### B1 — `created_paths` semantics conflict for post-mkdir stat failure

File: `docs/build/PSM-WMA_R09_B2_P4_v4_execution_preflight_materialization_design_v0.3_2026-09-02.md:33-35`

Section 4 first states that a successfully mkdir-created path is appended to `created_paths` **only after the following nofollow stat succeeds**. The next paragraph then requires that if that post-mkdir stat fails, `created_paths` **must already include the just-created path**.

Those two rules cannot both be true. This matters because v0.3 freezes exact `POISONED` prefixes and requires failure injection at every mkdir/stat mutation point; the implementation and fixture need one deterministic definition.

Recommended frozen rule:

- after a mkdir syscall succeeds, immediately append that target to `created_paths`, because the helper has already caused that filesystem mutation;
- then perform the nofollow stat;
- if stat fails, return `POISONED` with that just-created path included in `created_paths`, `failed_path` equal to that path, and the original stat failure type;
- if the mkdir itself fails, do not append that target.

If the project instead wants `created_paths` to mean only stat-verified directories, introduce a separate field for the successful mkdir footprint; do not use one field with both meanings.

## Non-blocking implementation expectations

The existing phrases `unique _admit_execution_request(raw) constructor` and `nofollow mkdir/stat` are treated as normative requirements. Implementation review will reject a directly forgeable authority path that bypasses admission, or a pathname-only check/mkdir sequence that does not preserve the stated nofollow safety semantics.

## Authorization boundary

This review does not reopen the already-closed Execution Request nested/full static admission contracts. It also does not authorize real execution request creation, P4-v4 preflight/materialization, candidate/staging publication, record/refreeze, P5 export/compose, B2-T, GPU/CUDA, model/data/checkpoint I/O, evaluation, inference, or Local Memory training.

After B1 is made internally consistent, the design can be resubmitted for `APPROVE_TO_IMPLEMENT_P4_V4_PREFLIGHT_MATERIALIZATION_STATIC_TOOLS`.
