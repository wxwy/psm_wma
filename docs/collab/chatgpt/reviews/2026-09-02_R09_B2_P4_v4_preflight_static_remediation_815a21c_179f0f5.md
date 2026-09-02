# R09-B2 P4-v4 preflight static tooling remediation review

## Request / implementation

- Request commit: `815a21ccca992c3c7e4a854037c43df9d81095ae`
- Implementation commit: `179f0f5445ddbf2c65419145b7ed8d27b44c6d4d`
- Approved design: `5de996bf2c1e5b5b8ac11300b190d76eae8a21dd`
- Previous ChatGPT review: `dd22d3fe711b9d40da6b20893b7e1011fb67b6a7`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Verdict

`REQUEST_CHANGES`

`APPROVE_TO_CLOSE_P4_V4_PREFLIGHT_STATIC_TOOLS` is not authorized.

## Findings

### HIGH — failure poison still permits partial identity reuse

`tools/g0/r09_b2_p4_v4_static_contract.py::_reject_failed_identity_reuse()` records admitted identities as `(backend, token, run_root)` and rejects history only when that entire tuple matches a prior FAIL.

The frozen one-shot lifecycle requires a new attempt to use a new token **and** a new run-root. The current implementation therefore still admits both false cases:

1. prior FAIL uses token `A`, run-root `R`; later PASS uses token `B`, the same run-root `R`;
2. prior FAIL uses token `A`, run-root `R`; later PASS reuses token `A` with a new run-root `S`.

Both must fail closed. Poisoned token identities and poisoned run-root identities need independent rejection (and the attempt directory itself remains poisoned). Add permanent CPU negatives for token-only reuse and run-root-only reuse.

### HIGH — pair admission does not enforce all invariants required by the sole P5 consumer

The remediation correctly reuses `load_p4_v4_preflight()` in `_validate_final_pair()`, closing the previous fake/minimal-payload false PASS. It then adds explicit equality only for `production_source`, `request_defaults`, and `interpreter`.

However the frozen P5 pair verifier allows no difference for `effective_launch.loader_argv` or `effective_launch.runtime_sys_path`; `build_v4_pair_requests()` derives both directly from the two P4-v4 records. A recurrent candidate and TTT candidate can therefore each be individually P4-v4 valid, share source/default/interpreter, but use different `loader_argv` or `runtime_sys_path`. `stage_atomic_publication()` currently accepts that pair, while the only downstream P5 pair verifier must later reject it.

This violates the approved v0.4 requirement that existing cross-backend invariants hold before six-blob publication. Required fix: derive the pair contract from the frozen P5 child requests (or an equivalent verifier-owned projection), and exact-bind every common effective-launch field. At minimum `cwd`, `toml`, `overrides`, `interpreter`, `loader_argv`, and `runtime_sys_path` must be equal; environment may differ only by the already frozen P3-owned key. If any additional backend-specific difference is intended, it requires a separate design change rather than a static-tooling exception.

### MEDIUM — permanent tests bypass the two new admission checks

`tools/g0/test_r09_b2_p4_v4_static_contract.py::test_pass_payload_is_byte_bound()` and `test_rejects_extra_payload_key_and_fail_schema()` monkeypatch both `_validate_final_pair` and `_reject_failed_identity_reuse`.

Consequently the submitted static regression suite does not execute the exact-P5 final grammar integration, the pair invariants, or failure-poison logic that this remediation claims to close. The separate P5 tests validate P5 grammar itself, but do not prove the P4 candidate admission calls it correctly or that poison history is enforced.

Required permanent tests should include, without patching the admission checks:

- a full P5-valid recurrent/TTT candidate pair that passes `stage_atomic_publication()`;
- malformed/incomplete final P4-v4 payload => FAIL;
- pair `loader_argv` drift => FAIL;
- pair `runtime_sys_path` drift => FAIL;
- prior FAIL then token-only reuse => FAIL;
- prior FAIL then run-root-only reuse => FAIL.

## Positive observations

- The previous minimal/fake P4 payload false PASS is structurally addressed by reusing `load_p4_v4_preflight()` on byte-preserved candidate payloads.
- PASS link token is now strict lowercase 64-hex and candidate directory symlinks are rejected.
- FAIL candidates now bind an exact top-level request schema, production source, run-root identity, token, failure schema/stage, and non-empty error metadata.
- Implementation remains static-only: no CLI, materialization, staging, preflight execution, record/refreeze, evidence publication, P5 export/compose, GPU, training, evaluation, or inference path was added.

## Gate decision

Remediation is authorized only in the existing root static contract helper and stdlib CPU tests. No real P4-v4 execution or publication operation is authorized.
