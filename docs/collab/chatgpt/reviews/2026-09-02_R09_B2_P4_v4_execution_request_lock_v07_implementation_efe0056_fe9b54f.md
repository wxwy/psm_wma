# Independent Review — R09-B2 P4-v4 Execution-Request Lock v0.7 implementation

- Review anchor: `8b09979c0c44907f843ee7da9c5d7c2b1557ff56`
- Approved design: `671ca0123352b050125f3a413f8e74eeabbe6088`
- Implementation: `efe0056f6c1dce788c4c450a429d8ee089e05fb2`
- Formal request / ledger head: `fe9b54fa8da66cf10b9e3f5dd81337a125ae1670`
- Gitlink at request head: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Scope: root static planned-commitment implementation and stdlib CPU fixtures only. No P4/P5 handoff migration, real request/preflight/materialization/staging/candidate/run-root, record/refreeze, P5 export/compose, GPU, model/data/checkpoint I/O, evaluation/inference/training, B2-T, or Local Memory training.

## Verdict

`REQUEST_CHANGES`

The implementation correctly preserves `AUTHORIZED_P4_V4_LOCK_SPEC = None`, implements the v0.7 source/spec component-wise `openat(..., O_NOFOLLOW)` chain, constructs planned backend objects rather than direct-copying candidate items, uses the existing P5 canonical JSON spelling for the v2 staging projection, and does not modify P4/P5 migration code. However, the static closure is not yet complete.

## B1 — HIGH — frozen `execution_contract` is not validated

File: `tools/g0/r09_b2_p4_v4_execution_preflight.py`, `build_planned_roster_commitment()`.

The v0.7 design says the seven inherited closed sections, including `execution_contract`, must retain the already-closed full-request grammar. The implementation validates entry/source/interpreter/environment-through-authorities/backends, but never checks:

`spec["execution_contract"] == dict(_EXECUTION_CONTRACT_ITEMS)`.

The value is then copied verbatim into the commitment. Therefore a canonical lock spec can flip `gpu`, `torch`, `one_shot`, `cleanup_retry_repair`, remove a required member, or otherwise change the execution contract, recompute `lock_spec_sha256`, and still reach a valid commitment.

Required remediation:

1. Validate the exact execution-contract key/value object before constructing any commitment/output.
2. Prefer a small shared validator used by both `load_execution_request()` and the lock-spec path so the two grammars cannot drift.
3. Add negative fixtures for each boolean drift, missing member, and unexpected member.

## B2 — HIGH — planned run/candidate path, isolation, and reuse rules are only partially enforced

File: same implementation, `build_planned_roster_commitment()`.

The planned-only grammar was intentionally split from final `run/candidates`, but v0.6/v0.7 retained the already-closed future lexical/source-overlap/derived-leaf/reuse semantics. The implementation currently validates identity SHA/kind/token, but does not apply the closed path/isolation checks to each planned run identity.

Examples currently admitted after recomputing self-SHAs:

- a planned run identity whose `root` / `resolved_root` is relative, non-canonical, or different;
- a run root overlapping the source root or `source_root/cosmos-framework`;
- both backends reusing the same run identity with different tokens;
- a candidate namespace overlapping source or a run root.

`seen` currently contains tokens, derived candidate paths, and newly constructed output-item identities; it does not establish the closed run-identity/source/candidate isolation contract.

Required remediation:

1. For every planned run identity, apply the same future lexical check as `_validate_run_item()`, require `root == resolved_root`, kind=`run_root`, and reject source/submodule overlap.
2. Reject pair reuse of run identity and run token as frozen by the planned contract.
3. Apply the closed candidate-root source-overlap rule.
4. Reject candidate root / derived candidate path overlap with either run root using the same lexical-overlap definition as `validate_candidates()`.
5. Add explicit negative fixtures for all of the above.

## B3 — HIGH — output terminal-state implementation does not fully implement the frozen same-FD poison contract

File: same implementation, `lock_authorized_planned_roster_commitment()`.

The frozen design requires every create-before error to be `NOT_LOCKED`, and every create-after write/fsync/seek/read-back/fchmod/fstat/close error to be terminal `POISONED_NOT_LOCKED`, preserving the target and never retrying/repairing.

Current gaps:

1. `os.close(descriptor)` is executed in `finally` outside the inner exception translation. A close failure propagates as its raw exception instead of `POISONED_NOT_LOCKED`.
2. Output-create failures other than `FileExistsError` are not normalized to the create-before `NOT_LOCKED` state.
3. The post-`fchmod` `fstat` only checks mode `0444`; the design also froze regular-file verification.

Required remediation:

- make close success part of the success condition and translate close failure to `POISONED_NOT_LOCKED`;
- normalize every output-create failure before successful creation to `NOT_LOCKED` while preserving zero-write semantics;
- require `stat.S_ISREG(fstat.st_mode)` and exact `0444` before success;
- retain the created path on every post-create failure, with no cleanup/overwrite/retry.

## B4 — HIGH — the submitted fixtures do not cover the v0.7 closure matrix

File: `tools/g0/test_r09_b2_p4_v4_execution_preflight.py`, `PlannedRosterCommitmentTest`.

Only three new lock tests are present:

1. one planned-commitment construction test;
2. one small final-field/candidate mapping drift test;
3. one default-`None` authority test.

The positive `_build()` test mocks `validate_entry`, `validate_host_git`, `validate_source`, `validate_interpreter`, `validate_backends`, and `validate_authorities_pair`, so it does not prove composition with the already-closed sections. The claimed aggregate `79/79 PASS` therefore does not exercise most of the v0.7 design matrix.

Missing permanent fixtures include, at minimum:

- exact execution-contract drift;
- planned run lexical/resolved/source-overlap and pair reuse;
- candidate source/run overlap;
- source-root/spec intermediate-component symlink and retarget behavior;
- constant commit/tree/Gitlink/blob/current/raw binding drift;
- a positive authorized lock path with exact spec→commitment mapping;
- output existing/symlink/create failure;
- short-write/write/fsync/seek/read-back/fchmod/fstat/close poison faults;
- exact post-failure preserved-path semantics;
- projection row/order/path/type/mode/SHA drift and self-SHA drift.

The static closure should include a real composition fixture built from valid closed sections rather than relying only on mocked validators.

## Accepted implementation portions

Do not reopen these absent drift:

- production authority remains `None` and fail-closed;
- `source_root` is opened from `/` by component with directory + nofollow checks;
- multi-component `spec_path` parent components are opened FD-relative with `O_DIRECTORY|O_NOFOLLOW`, final basename with `O_RDONLY|O_NOFOLLOW` + regular-file fstat;
- planned spec has no final `run`, `candidates`, or `roster_sha256` field;
- planned output backend objects are newly constructed with deterministic staging projection;
- P5 projection serializer matches `export_r09_b2_p5_resolved_config.canonical_bytes()` spelling;
- implementation commit → request head is Inbox-only;
- Gitlink remains exactly `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`.

## Gate status

Do not close `G0-R09-B2-P4-V4-EXECUTION-REQUEST-LOCK` implementation yet.

After B1-B4 are remediated and independently re-reviewed, the appropriate positive verdict is:

`APPROVE_TO_CLOSE_P4_V4_EXECUTION_REQUEST_LOCK_STATIC_TOOLS`

Even after static closure, P4/P5 handoff migration, final execution request generation, record/refreeze, real CPU preflight, P5 export/compose, B2-T, GPU, and Local Memory training remain separately unauthorized.
