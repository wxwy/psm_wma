# Independent Implementation Review — R09-B2 P4/P5 v4 Handoff Migration

- Gate: `G0-R09-B2-P4-P5-V4-HANDOFF-MIGRATION`
- Implementation SHA under review: `3c04c4752d71a6a8003fdb0521f3e2646e9cd4e5`
- Ledger/request SHA observed at review start: `3daaad037b154f5e257565ea28135f29c83e716a`
- Parent / implementation baseline: `260072f854c7876d179c4286f25028bba8974585`
- Approved design SHA: `f16f6e4d260114bb89c102e476a63d590751274e`
- Prior ChatGPT design review: `docs/collab/chatgpt/reviews/2026-09-03_R09_B2_P4_P5_v4_handoff_migration_design_v02_f16f6e4.md`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Repository-state note

This review environment still has no local `wxwy/psm_wma` checkout, so literal shell `git fetch origin V2` could not be executed. I resolved the remote `V2` branch directly through the connected GitHub repository API immediately before review. Remote `V2` HEAD was `3daaad037b154f5e257565ea28135f29c83e716a`; that commit only appends the implementation review request to `docs/collab/chatgpt/CODEX_INBOX.md`, and its parent is exactly the implementation SHA `3c04c4752d71a6a8003fdb0521f3e2646e9cd4e5`.

`260072f -> 3c04c475` is one implementation commit. The technical diff is limited to the root P4/P5 static tooling/tests plus `SESSION.md` / `TODO.md`; no submodule revision change was observed.

## Verdict

`REQUEST_CHANGES`

The nested-directory closure itself is implemented in the intended direction, but two HIGH compatibility/namespace bugs mean this exact implementation SHA does not satisfy the approved v0.2 design.

## HIGH-1 — shared validator silently changes the frozen P4 manifest self-SHA language

**Files:**
- `tools/g0/export_r09_b2_p5_resolved_config.py:61-89`
- `tools/g0/r09_b2_p4_v4_execution_preflight.py:233-243,327-333`
- baseline `260072f`: `tools/g0/r09_b2_p4_v4_execution_preflight.py:327-345`

### Root cause

The approved design requires the v2 shared manifest validator to preserve the already-closed P4 `_validate_payload_manifest()` accepted language exactly.

Before this migration, P4 validated `payload_manifest.sha256` through `_identity_exact(..., key="sha256")`, which uses P4 `canonical_sha256()`:

```python
json.dumps(value, sort_keys=True, separators=(",", ":"))
```

That uses Python's default `ensure_ascii=True`.

The new shared `validate_v2_payload_manifest()` instead calls P5 `_self_sha()`, which calls `sha256_json()` / `canonical_bytes()` with:

```python
json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
```

For ASCII-only paths both spellings happen to produce the same bytes, so the submitted fixtures pass. But the frozen P4 path grammar never required ASCII. A legal manifest path such as `pkg/é.py` therefore had a valid old-P4 manifest SHA under escaped JSON (`\u00e9`) and is rejected by the new shared validator, whose self-SHA is computed over UTF-8 `é` bytes.

This is a real accepted-language / commitment-identity change, directly contradicting design v0.2 §2: the shared validator must use the *same* closed P4 manifest grammar rather than silently redefine it.

### Required acceptance criteria

1. Preserve the frozen P4 `payload_manifest.sha256` canonical spelling exactly. The shared manifest validator used by both P4 and P5 must validate the manifest self-SHA with the old P4 canonicalization semantics.
2. Keep the v2 roster digest unchanged: `d = SHA256(P5 canonical_bytes({"entries": entries}))`. Do not replace the P5 roster/projection digest spelling with the P4 manifest spelling.
3. Add a permanent compatibility regression using a legal non-ASCII manifest path, e.g. `pkg/é.py`:
   - a manifest carrying the old-P4 self-SHA is accepted by both P4 and P5 shared validation;
   - the migration does not silently redefine that self-SHA to the P5 spelling;
   - derived P4 projection and P5 roster still share the P5 `entries` digest `d`.
4. Keep the existing ASCII fixture behavior unchanged.

## HIGH-2 — reserved run-root paths can reappear as derived directories

**Files:**
- `tools/g0/export_r09_b2_p5_resolved_config.py:112-139`
- `tools/g0/test_r09_b2_p5_full_config_diff.py:25-51`

### Root cause

The design freezes these exact run-root paths as permanently reserved:

`preflight.json`, `request.json`, `result.json`, `verification.json`, `candidate_link.json`.

Current implementation checks only:

```python
regular_paths & P5_V2_RESERVED_ROOT_PATHS
```

before deriving ancestor directories.

Therefore a manifest entry such as:

`request.json/payload.py`

passes the regular-path reserved check, and ancestor derivation adds `request.json` as a directory row. The resulting actual run-root now contains the exact reserved path `request.json`, just with type `directory` instead of `regular`.

The current regression matrix only tests the reserved names as exact regular manifest rows; it does not cover a reserved path becoming an ancestor directory.

### Required acceptance criteria

1. Apply the reserved-root prohibition to the complete verifier-derived path set, not only the regular-file set. In particular, after ancestor derivation `directories & P5_V2_RESERVED_ROOT_PATHS` must be empty (or an equivalent verifier-owned check must enforce this).
2. Add permanent negative regressions for at least:
   - `preflight.json/x`
   - `request.json/x`
   - `result.json/x`
   - `verification.json/x`
   - `candidate_link.json/x`
3. Keep the prohibition exact to the run-root reserved path. Do not accidentally reject unrelated nested basenames such as `pkg/request.json` unless a separate reviewed contract explicitly broadens the namespace rule.
4. P5 actual-tree validation must therefore be unable to admit any of those five exact reserved root paths as either regular files or directories.

## MEDIUM — wire-schema regression should assert the exact P4 projection key set

**Files:**
- `tools/g0/r09_b2_p4_v4_execution_preflight.py:70-73,327-333`
- `tools/g0/test_r09_b2_p4_v4_execution_preflight.py:1790-1810`
- `tools/g0/test_r09_b2_p5_full_config_diff.py:25-40`

The implementation currently still returns exactly `{entries, projection_sha256}`, so this is not a production-code failure. However, design v0.2 explicitly requires a permanent regression that `STAGING_PROJECTION_KEYS` and the closed P4 wire schema remain unchanged. The current tests assert the entries and digest fields, but do not fail if a future extra projection key is added.

Before closure, add an exact-key assertion such as:

```python
set(item["staging_projection"]) == STAGING_PROJECTION_KEYS
```

and retain the cross-schema semantic regression: P4 keys `{entries,projection_sha256}` and P5 keys `{entries,sha256}` differ while `entries` and digest value are equal.

## Accepted implementation direction

The following parts are technically sound and should be retained:

- one shared `derive_v2_roster_entries()` is now used by P4 planned projection and P5 roster verification;
- legal deep nested payloads derive their non-root ancestor directory rows;
- regular-vs-directory / strict-ancestor collisions are rejected by the derived-set intersection;
- P5 actual recursive run-root path set must exactly equal the derived set;
- directory/regular modes remain `0555` / `0444`, regular payload SHA and `st_nlink==1` are checked;
- P4 `STAGING_PROJECTION_KEYS` remains `{entries, projection_sha256}` in code;
- P5 roster remains `{entries, sha256}`;
- P4 projection digest is computed with the P5 roster canonical spelling;
- P4 request `p4_run.roster_sha256` is compared with the result roster SHA;
- `AUTHORIZED_P4_V4_LOCK_SPEC` remains `None`;
- `AUTHORIZED_P4_V4_EVIDENCE` remains `None`;
- `run_parent_export()` remains hard-stopped;
- no Cosmos submodule/runtime/GPU/training scope creep was introduced.

## Scope / next Gate

This review does not authorize any runtime behavior. Keep the Gate in `REVIEW` and fix only the root static P4/P5 grammar/tests necessary to close the two HIGHs and the regression gap.

After a new remediation implementation SHA is pushed, it must be independently re-reviewed. The next possible positive verdict is:

`APPROVE_TO_CLOSE_P4_P5_V4_HANDOFF_MIGRATION_STATIC_TOOLS`

Even that verdict would authorize static-tool closure only; it would not authorize real request/preflight/staging/materialization/candidate/run-root creation, record/refreeze/evidence publication, P5 export/compose, child/torch/torchrun, GPU/CUDA, model/data/checkpoint I/O, training/evaluation/inference, B2-T, or Local Memory training.
