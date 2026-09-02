# Independent Review — R09-B2 P4-v4 Execution-Request Lock v0.7 fixture remediation

- Review anchor: `256192ea32bcdc3e7540bfb0bfb6adc483132e4a`
- Approved design: `671ca0123352b050125f3a413f8e74eeabbe6088`
- Production remediation: `40eda9b58c6bcdd0ea953348fadbd39d55eb50f0`
- Fixture-only remediation: `aebb94f95eef9151c764c6b2f021a07e9363798c`
- Formal request / ledger head: `27faa425750c5b0893986f14268d1b3eb16948d8`
- Gitlink at request head: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Scope: root static planned-commitment implementation/fixtures only. No P4/P5 handoff migration, real request/preflight/materialization/staging/candidate/run-root, record/refreeze, P5 export/compose, GPU, model/data/checkpoint I/O, evaluation/inference/training, B2-T, or Local Memory training.

## Verdict

`REQUEST_CHANGES`

The production remediation at `40eda9b` closes the prior B1-B3 implementation blockers: exact execution-contract validation, planned run/candidate lexical/isolation/reuse checks, and normalized same-FD `NOT_LOCKED` / `POISONED_NOT_LOCKED` writer semantics. The `aebb94f` delta is fixture-only and adds useful coverage for pre-existing intermediate/final symlinks, existing/symlink output targets, short writes, non-regular fstat, and some manifest/self-SHA mutations. Production helper code does not drift in the fixture-only submission.

Static closure is still blocked because the approved v0.7 fixture matrix is not yet proven end-to-end.

## B4-A — HIGH — no non-None authorized end-to-end lock fixture or authority drift matrix

File: `tools/g0/test_r09_b2_p4_v4_execution_preflight.py`, `PlannedRosterCommitmentTest`.

The test suite still only proves `AUTHORIZED_P4_V4_LOCK_SPEC=None` at the public lock entry. There is no permanent positive fixture that supplies one valid temporary authority and drives:

`lock_authorized_planned_roster_commitment()`

through source-root FD anchoring, spec FD walk, source/HEAD/tree/Gitlink/blob/current/raw binding, full spec validation, commitment construction, exclusive write/read-back/chmod/fstat/close, and final path result.

Likewise there is no systematic negative fixture for the verifier-owned authority bindings themselves: `source_commit`, `source_tree_oid`, `gitlink`, `spec_path`, `spec_git_blob_sha256`, `spec_current_sha256`, `spec_raw_sha256`, source-root identity, output-parent identity, and output basename.

Required remediation:

1. Add one positive authorized non-None fixture through the public lock helper, using a complete valid planned spec and exact authority.
2. Assert canonical output bytes, exact spec→commitment mapping, `0444` regular-file state, and absence of final `run` / `candidates` / `roster_sha256` authority.
3. Add per-binding negative mutations for commit/tree/Gitlink/blob/current/raw/path identities that fail before output creation.
4. Keep production constant `None`; fixture authority must be test-local only.

## B4-B — HIGH — v0.7 FD retarget race is still untested

File: same test class, `test_spec_fd_walk_rejects_intermediate_and_final_symlinks`.

`aebb94f` tests symlinks that already exist before traversal. That is useful but does not prove the v0.7 acquisition-window retarget contract. The design explicitly froze intermediate-component `symlink/retarget` behavior.

Required remediation:

- add a race fixture that opens a parent component, then renames/replaces the pathname with a symlink to an external directory before the next component/final basename is opened;
- prove the helper either fails closed or remains bound to the already-open original FD chain;
- prove the external target is not consumed as the spec source;
- retain the existing pre-existing-symlink tests.

A static symlink negative is not equivalent to this TOCTOU fixture.

## B4-C — HIGH — semantic drift fixtures still short-circuit on stale hashes, and full closed-section composition remains mocked

File: same test class, `_build()` and `test_projection_and_self_sha_drift_are_rejected`.

Two issues remain.

First, the manifest order/type mutations added by `aebb94f` do not recompute `payload_manifest.sha256` and the outer `lock_spec_sha256`. Therefore rejection can occur at self-SHA mismatch before the semantic order/type/path/SHA validator is reached. These cases do not prove that a malicious-but-self-consistent manifest is rejected.

Required semantic fixtures should mutate and then recompute every enclosing identity before calling the validator, covering at least:

- manifest order;
- invalid/escaping path grammar;
- type drift;
- malformed/wrong regular-file SHA;
- nested planned/backend identities and outer lock-spec identity.

Second, the positive `_build()` path still mocks `validate_entry`, `validate_host_git`, `validate_source`, `validate_interpreter`, `validate_backends`, and `validate_authorities_pair`. Thus there is still no real composition fixture proving that the planned-only spec composes with the already-closed sections without a schema/cross-binding mismatch.

Required remediation:

- build at least one complete planned spec from the existing full-admission fixture data and run the real closed-section validators; mock only already-approved fixed external I/O at the lowest necessary boundary, not the full validators;
- include hostile ambient `PATH`/`PYTHONPATH`/locale and prove no unapproved child/P5/torch path is invoked while the fixed Git path remains the only allowed subprocess authority.

## Accepted / closed

Do not reopen absent drift:

- `execution_contract` exact validation is closed by `40eda9b`;
- planned run/candidate lexical/source/run overlap and pair reuse checks are closed by `40eda9b`;
- create-before errors are normalized to `NOT_LOCKED`;
- write/short-write/fsync/seek/read/fchmod/fstat/close failures are terminal `POISONED_NOT_LOCKED` and preserve created targets;
- successful output requires regular file + exact `0444`;
- source-root and spec traversal remain FD-relative and nofollow-safe in production;
- `aebb94f` changes no production helper;
- `aebb94f -> 27faa42` is Inbox-only;
- Gitlink remains exactly `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`.

## Gate status

Do not close `G0-R09-B2-P4-V4-EXECUTION-REQUEST-LOCK` yet.

After B4-A/B/C are closed and re-reviewed, the appropriate positive verdict is:

`APPROVE_TO_CLOSE_P4_V4_EXECUTION_REQUEST_LOCK_STATIC_TOOLS`

Even after static closure, P4/P5 handoff migration, final execution request generation, record/refreeze, real CPU preflight, P5 export/compose, B2-T, GPU, and Local Memory training remain separately unauthorized.
