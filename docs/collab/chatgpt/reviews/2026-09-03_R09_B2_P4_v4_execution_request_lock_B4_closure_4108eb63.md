# Independent Review — R09-B2 P4-v4 Execution-Request Lock B4 fixture closure

- Gate: `G0-R09-B2-P4-V4-EXECUTION-REQUEST-LOCK`
- Implementation SHA under review: `4108eb63f4b65835b860352b1633767df3fab58a`
- Baseline fixture SHA: `aebb94f95eef9151c764c6b2f021a07e9363798c`
- Prior ChatGPT review: `be76950c4c084bd5decfec9400bf16f35b10dcb5`
- Approved design: `671ca0123352b050125f3a413f8e74eeabbe6088`
- Submodule/Gitlink at implementation SHA: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Remote `V2` snapshot before this review write: `4a6ddefdffc88a38e158b5865b317ffa2a0c05d7`
- Ledger/request SHA at that snapshot: `4a6ddefdffc88a38e158b5865b317ffa2a0c05d7` (bookkeeping only; not the implementation verdict target)

## Repository-state note

The current review environment does not contain a local checkout of `wxwy/psm_wma`, and the container cannot resolve `github.com`, so a literal shell `git fetch origin V2` cannot be executed here. I therefore resolved the authoritative remote `V2` branch directly through the connected GitHub repository API before reviewing. The remote branch snapshot was `4a6ddef...`, whose parent is exactly the implementation SHA `4108eb63...`. A direct compare of `4108eb63... -> 4a6ddef...` shows only `SESSION.md`, `TODO.md`, and `docs/collab/chatgpt/CODEX_INBOX.md` changes; there is no newer implementation/test/config/submodule change to substitute for the requested implementation SHA.

If a future review session has a local checkout, the required first step remains literal `git fetch origin V2` followed by review against the fetched `origin/V2` state.

## Scope checked

This review is limited to root static planned-lock tooling/fixtures. It does **not** authorize P4/P5 migration, real execution-request generation, real preflight, materialization, staging, candidates/run roots, record/refreeze/evidence publication, P5 export/compose, torchrun, GPU/CUDA, model/data/checkpoint I/O, training, evaluation, inference, B2-T, or Local Memory training.

## Prior blockers

The prior review at `be76950...` left exactly three HIGH fixture blockers:

- B4-A: no non-None public authorized-lock end-to-end fixture and no authority-binding drift matrix;
- B4-B: no parent-FD retarget/TOCTOU fixture;
- B4-C: semantic negatives could short-circuit on stale hashes, and the positive composition path still mocked whole closed-section validators.

## Findings

### B4-A — CLOSED

`test_authorized_public_lock_runs_real_closed_sections_and_rejects_each_binding` now uses a **test-local** non-None authority and calls the public `lock_authorized_planned_roster_commitment()` path.

The fixture exercises the real planned-lock composition while controlling only fixed external facts at narrow boundaries. It covers:

- source-root FD anchoring and relative spec FD walk;
- source HEAD / commit-tree / Gitlink bindings;
- committed spec blob / current bytes / raw SHA bindings;
- the already-closed entry/source/interpreter/backends/authorities/execution-contract validators through the public builder path;
- same-FD create/write/fsync/seek/read-back/fchmod/fstat/close output path;
- exact canonical output bytes;
- final file regular + mode `0444`;
- absence of final `run`, `candidates`, and `roster_sha256` fields;
- per-binding negative mutations for source root, commit, tree, Gitlink, spec path, spec blob/current/raw SHA, output parent, and output basename, with no output created on rejection;
- production `AUTHORIZED_P4_V4_LOCK_SPEC` remains `None` after the fixture.

The hostile ambient environment fixture additionally constrains subprocess execution to the fixture-bound Git executable; no child/P5/torch execution path is introduced.

### B4-B — CLOSED

The parent-FD retarget fixture opens the original parent component, then renames/replaces the pathname with an external-directory symlink before the final spec lookup. `_read_lock_spec_at()` continues to return the original spec bytes through the already-open FD chain, and the external target is not consumed.

This directly closes the v0.7 acquisition-window retarget requirement rather than merely testing a pre-existing symlink.

### B4-C — CLOSED

The semantic negative matrix now mutates the planned spec and, except for the outer-SHA test itself, recomputes all enclosing identities via `_relock()` before validation. The suite therefore reaches semantic validators with self-consistent hashes for:

- manifest ordering;
- escaping path grammar;
- type drift;
- malformed regular-file SHA;
- nested planned run-token drift;
- outer lock-spec SHA drift.

The new `_planned_spec()` fixture derives the planned-only spec from the existing full-admission closed-section fixture data. The public authorized-lock test then runs the real closed validators instead of mocking entire validator functions. Only controlled Git/loader I/O facts are patched to make the test hermetic.

## Production drift

The B4 closure commit is fixture/test oriented. No new production helper change was identified in the `aebb94f... -> 4108eb63...` closure delta beyond the already-reviewed production state. The public production authority constant remains fail-closed at `None`.

## Evidence boundary

Repository bookkeeping reports `86/86 PASS`, `py_compile` PASS, and `git diff --check` PASS. I reviewed the committed code/diff and fixture semantics, but this session did **not** independently execute those 86 tests or the compile/diff commands, and the exact implementation SHA has no independent CI attestation available to this reviewer. This verdict is therefore a static code/diff/fixture Gate verdict, not a CI attestation.

## Verdict

`APPROVE_TO_CLOSE_P4_V4_EXECUTION_REQUEST_LOCK_STATIC_TOOLS`

All three prior B4 HIGH blockers are closed for implementation SHA `4108eb63f4b65835b860352b1633767df3fab58a`.

This verdict applies **only** to that implementation SHA. The later `4a6ddef...` commit is a ledger/request bookkeeping commit and does not replace or broaden this implementation verdict.

## Gate boundary after approval

Static lock tooling may be marked closed on the ChatGPT side. This approval does **not** authorize any real request, preflight, staging/materialization, candidate/run-root creation, record/refreeze/evidence publication, P5 authority update/export/compose, GPU/CUDA, model/data/checkpoint I/O, training, evaluation, inference, B2-T, or Local Memory training. Any such step requires its own independently frozen Gate and same-SHA reviewer approval.
