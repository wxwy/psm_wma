# R09-B2 P5 verifier child-locale grammar remediation review

- Request commit: `94ced235ff10878e346a904aedbebf1b2c07b286`
- Implementation commit: `9f30ef5054e11f58c60ec54d587924a1d0f2a2a4`
- Reviewed Gitlink/submodule: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Verdict: **APPROVE_TO_REQUEST_P5_STATIC_EXPORT**

## Scope

This review is limited to the two blockers from ChatGPT review `2026-09-01_R09_B2_P5_child_locale_4356416_3a7fc5c.md`:

1. the exporter/verifier mismatch for the Python 3.13 startup locale; and
2. the positive fixture failing to model the exporter-produced effective environment.

It does not authorize a second static export or any later gate.

## Findings

### HIGH blocker closed — verifier now binds the exact locale-adjusted effective environment

`tools/g0/verify_r09_b2_p5_full_config_diff.py` now imports the frozen `PYTHON_CHILD_LOCALE` from the reviewed exporter source and derives `_expected_effective_environment(record)` as the frozen P4 `environment.set` plus the single deterministic startup locale key.

`_bound()` still requires the P4 `environment.set`, `environment.unset`, and `inherit_allowlist` objects to match the frozen record exactly. It additionally requires `environment.effective == _expected_effective_environment(record)` by full dictionary equality. There is no subset/superset acceptance and no arbitrary environment-key allowance.

For the frozen P4 records, which do not contain `LC_CTYPE`, the only accepted effective-environment extension is therefore `LC_CTYPE=C.UTF-8`.

### MEDIUM blocker closed — fixture now exercises the locale-adjusted envelope and fail-closed negatives

`tools/g0/test_r09_b2_p5_full_config_diff.py` now constructs its positive pair with `_expected_effective_environment(record)`, so the PASS case matches the effective-environment shape produced by the reviewed exporter after the `3a7fc5c` locale remediation.

The permanent regression suite also adds two direct negatives:

- adding an otherwise shared `UNEXPECTED=1` key to the effective environment must make `verify_pair()` return `FAIL`; and
- changing `LC_CTYPE` from `C.UTF-8` to `C` must make `verify_pair()` return `FAIL`.

This closes the prior false-positive gap where the test suite exercised the old P4-only environment shape rather than the actual exporter envelope.

### Source and gate boundaries remain narrow

The implementation change from the previous ChatGPT review is limited to the P5 pair verifier and its static test. The exporter-side child locale constant and the two frozen D005-bound request digests remain unchanged from `3a7fc5c`.

The Gitlink remains `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`.

The previously authorized one-shot export has already been consumed and failed closed. This review does not revive that authorization.

## Positive observations

- Exact environment equality remains in force.
- P4 `set`/`unset`/`inherit_allowlist` provenance is not rewritten or relaxed.
- The added negatives directly cover extra-key and locale-value drift.
- No compose, CUDA/GPU, torchrun, model/data, training, evaluation, or inference execution is part of this request.

## Gate decision

**APPROVE_TO_REQUEST_P5_STATIC_EXPORT** is granted.

Codex may prepare a new, separate one-shot `APPROVE_TO_RUN_P5_STATIC_EXPORT` request using the new reviewed exporter/verifier revision `9f30ef5054e11f58c60ec54d587924a1d0f2a2a4`, a new clean exporter root, a new output path, and a complete immutable CPU-only command/bootstrap contract.

This approval does **not** authorize:

- creating or running the new static export before a separate execution approval;
- retrying the previously consumed run;
- `load_experiment_from_toml` / production compose;
- CUDA or GPU use;
- `torchrun` or distributed initialization;
- model, dataloader, optimizer, or checkpoint construction;
- weights/data/MP4 access;
- training, evaluation, or inference;
- P5 closure;
- B2-T or any later gate.
