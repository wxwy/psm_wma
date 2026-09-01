# R09-B2 P5 standalone child D005-binding remediation review

- Request commit: `db147b141b9cff9909f7a2702b57167a5ac9f695`
- Implementation commit: `df06f37b87e292368e0e3b4863ec36f7c648b305`
- Integrated review root: `68464a1cfaafcb631bf6cd9ac66efe5691c73785`
- Reviewed Gitlink/submodule: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Verdict: **REQUEST_CHANGES**

## Scope

This review is limited to the prior ChatGPT addendum blocker for the hidden/standalone P5 child request path. The already reviewed exporter execution-identity and failed-attempt staging changes are not reopened here except for regression interaction.

I did not use other reviewers' verdicts. Codex's reported `py_compile` / unittest / diff-check results were treated only as self-reported evidence; the permanent test source and production code were inspected directly.

## Findings

### Positive — the current implementation does put a frozen request-identity gate before production compose

`tools/g0/export_r09_b2_p5_resolved_config.py:24-29, 190-217, 281-305`

The implementation adds backend-specific `FROZEN_CHILD_REQUEST_SHA256` values plus an exact 16-key `CHILD_REQUEST_KEYS` set. `validate_child_request()` first requires the exact top-level schema and a known backend, then hashes the entire canonical JSON payload and requires it to match the backend's frozen digest.

`build_pair_requests()` derives requests only after production-root validation and frozen evidence-root record equality, then runs `validate_child_request()` on both generated requests. `_child()` calls the same validator immediately after JSON parsing, before cwd/interpreter/environment checks, before Hydra/experiment imports, and before `load_experiment_from_toml(...)`.

Therefore, for the reviewed exporter code, simply supplying a different TOML/override/backend/provenance/request payload cannot currently reach compose merely because it is internally self-consistent.

### MEDIUM — the required permanent negative does not actually model an internally consistent forged request

`tools/g0/test_r09_b2_p5_full_config_diff.py:126-136` — `test_arbitrary_consistent_child_request_is_rejected_before_compose`

The test starts from the valid recurrent request and changes only:

```python
forged["toml"] = "examples/toml/attacker.toml"
```

It does **not** update the matching `--sft-toml=...` token inside `forged["command_argv"]`. The forged request is therefore internally inconsistent: its declared `toml` and its full launch argv disagree.

This does not satisfy the explicit prior blocker requirement: an arbitrary **but internally consistent** request under the exact frozen D005 cwd/interpreter/environment must be rejected at the pre-compose guard.

Why this matters: the current hash gate is correct, but this regression test can still pass after a future unsafe refactor that removes the immutable request digest and replaces it with only schema/cross-field-consistency checks. Such a refactor would reject this test fixture because `toml != command_argv --sft-toml`, while a truly internally consistent attacker request could again reach compose. The test would then give a false sense of closure over the original bypass class.

Required fix:

- construct the attacker request so all request-owned launch fields remain mutually consistent; at minimum change both `toml` and the corresponding `--sft-toml=...` token in `command_argv` to the same attacker TOML while preserving the exact D005 cwd/interpreter/environment;
- keep the request exact-schema-valid;
- execute it through the standalone hidden child path and require failure specifically at the frozen request-identity guard, with no child output created;
- retain the existing valid-request parent path test so the frozen digests are still proven compatible with requests derived from the frozen P4/evidence inputs.

No exporter production-code change is required by this finding if the current digest gate remains unchanged; the blocker is the missing exact threat-model regression/evidence.

## Gate decision

`APPROVE_TO_REQUEST_P5_STATIC_EXPORT` is **not granted** in this review.

The next submission may be a narrow test/evidence remediation for the internally consistent forged-request negative. After that passes static review, Codex may again request `APPROVE_TO_REQUEST_P5_STATIC_EXPORT`.

This review does **not** authorize static export, production compose, `load_experiment_from_toml`, CUDA/GPU, torchrun, model/checkpoint construction, training, evaluation, inference, P5 closure, or B2-T.
