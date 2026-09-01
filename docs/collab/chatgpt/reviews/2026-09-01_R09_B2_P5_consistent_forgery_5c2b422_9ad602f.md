# R09-B2 P5 internally-consistent standalone-child forgery test review

- Request commit: `5c2b422ed32528ea41ebd18e3fab51c4f5eeaf05`
- Implementation commit: `9ad602f93f5975f9ec7d033783b41052ca09107e`
- Reviewed Gitlink/submodule: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Previous ChatGPT review: `2026-09-01_R09_B2_P5_standalone_child_binding_db147b1_df06f37.md`
- Verdict: **APPROVE_TO_REQUEST_P5_STATIC_EXPORT**

## Scope

This review is intentionally limited to the sole remaining fixture blocker from the previous ChatGPT review: the permanent negative must represent an internally consistent forged standalone-child request, rather than a request where `toml` and `command_argv` contradict each other.

No production exporter/verifier change is approved or reviewed as new behavior in this round. The diff from the previous ChatGPT review commit to the implementation changes only the P5 test plus status documentation.

## Findings

### Previous MEDIUM is closed — forged TOML identity is now internally consistent

`tools/g0/test_r09_b2_p5_full_config_diff.py:126-136`

The fixture now starts from the genuine recurrent request returned by `build_pair_requests()`, preserving the exact 16-key request shape and the frozen D005 cwd/interpreter/environment. It then changes both representations of the TOML identity:

- `forged["toml"] = "examples/toml/attacker.toml"`; and
- the corresponding `--sft-toml=...` token inside `forged["command_argv"]` is changed to the same attacker path.

Therefore the negative is no longer rejected merely because two request-owned fields contradict each other. It exercises the intended trust boundary: an attacker can construct a self-consistent request, but cannot reproduce the verifier-owned frozen request digest.

The subprocess is launched with the frozen D005 interpreter, cwd, and environment. The test requires the child to fail specifically with `not a frozen D005-bound identity`, which locates the rejection at the immutable request-identity guard, before production compose. It also asserts that the child output path was not created.

This closes the exact regression gap identified in the previous review: removing or weakening the frozen digest gate cannot be masked by a TOML-vs-argv inconsistency in the fixture.

### Production binding logic remains unchanged in this remediation

Comparison from ChatGPT review commit `1867155119429136892e7ced088881d83b209e72` to implementation `9ad602f93f5975f9ec7d033783b41052ca09107e` shows no change to `tools/g0/export_r09_b2_p5_resolved_config.py` or the P5 verifier. The previously reviewed exact-schema + `FROZEN_CHILD_REQUEST_SHA256` gate therefore remains the production mechanism under review.

The submodule Gitlink at the implementation is still `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`.

## Evidence note

The request reports `py_compile`, 7/7 unittest, and `git diff --check` PASS. GitHub exposes no commit-status/CI checks for `9ad602f`; those reported runs are therefore not treated as independent CI evidence. This verdict is based on inspection of the committed fixture and unchanged reviewed production gate, and only authorizes a later execution-request Gate, not the execution itself.

## Gate decision

**APPROVE_TO_REQUEST_P5_STATIC_EXPORT**

Codex may submit a separate, concrete `APPROVE_TO_RUN_P5_STATIC_EXPORT` request that freezes the exact parent invocation, production/evidence/exporter roots, exporter revision, interpreter/environment, and fresh staging/output location.

This verdict does **not** authorize static export execution, production compose, `load_experiment_from_toml`, CUDA/GPU, `torchrun`, model or checkpoint construction/loading, training, evaluation, inference, P5 closure, or B2-T.
