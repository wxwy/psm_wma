# R09-B2 P5 complete static-export contract remediation review

- Request: `53a481d89e8bbbd81089280001aaaa841d4e6fbd`
- Implementation: `97bf5beacd9a621155183900afe31ed106f5c56c`
- Reviewed Gitlink/submodule: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Verdict: **REQUEST_CHANGES**

## Findings

### HIGH — one `root` cannot simultaneously satisfy P4 recorded-source verification and host the P5 implementation/evidence

`tools/g0/export_r09_b2_p5_resolved_config.py:142-186`
`tools/g0/verify_r09_b2_p5_full_config_diff.py:88-138`
`tools/g0/verify_r09_b2_p4_d005.py:80-94`

`run_parent_export()` and `build_pair_requests()` use one `root` for all of the following:

1. P4 `verify_pair(..., root)`;
2. P5 child cwd binding (`root/cosmos-framework`);
3. P5 verifier `_expected(root)`, which loads committed P4 D005 records from `root/artifacts/.../p4_launch_d005`;
4. P1/P3 frozen-input loading.

But the frozen P4 records have `source.root_revision=ddb4e0e...`, while the reviewed P5 implementation is at `97bf5be...` and the P4 D005 evidence was committed only after `ddb4e0e`.

The P4 verifier's `_source_ok()` requires the checkout HEAD to equal the record's source revision. Therefore:

- using a `97bf5be` checkout gives access to the P5 implementation/P4 evidence, but P4 source verification fails because HEAD != `ddb4e0e`;
- using a clean `ddb4e0e` checkout can satisfy P4 source semantics, but `_expected(root)` cannot rely on P4 evidence committed later, and the reviewed P5 implementation is not that checkout.

No single real root can satisfy the current contract. Static export must separate at least:

- `production_root`: clean checkout of recorded P4 source `ddb4e0e` + Gitlink `21d064f`;
- `evidence_root` or immutable evidence inputs: committed P4 recurrent/TTT/verification artifacts;
- `exporter_root`: clean checkout containing the approved P5 exporter/verifier implementation.

P4 verification should use the immutable D005 records supplied read-only together with `production_root`; P5 verifier/tool provenance must use `exporter_root`; evidence paths/hashes must be independently bound.

### HIGH — exporter provenance is caller-owned and exact nested envelope schema is still not verifier-owned

`tools/g0/export_r09_b2_p5_resolved_config.py:151-184`
`tools/g0/verify_r09_b2_p5_full_config_diff.py:97-138`

`run_parent_export()` accepts `tool_sha256` and `exporter_root_revision` as caller parameters and `assemble_envelope()` copies them into `provenance.exporter_source`. The verifier does not validate `provenance.exporter_source` at all and does not enforce an exact nested schema for `provenance`, `provenance.inputs`, `effective_launch`, `environment`, or `p1_p3_d005_bindings`.

The positive CPU fixture still omits `exporter_source` entirely and passes, proving this part of the approved v0.2 envelope is not fail-closed.

Required:

- derive exporter root revision/clean status from the actual exporter checkout;
- hash the actual exporter/verifier source files internally;
- independently bind `provenance.exporter_source` in the verifier;
- enforce exact nested field sets, not only top-level keys;
- include and bind the approved provenance inputs omitted today, notably the committed P4 `verification.json` SHA and P1 manifest SHA/evidence identity;
- add common-forgery/omission negatives where both sides carry the same bogus exporter source or omit the same required nested field and must FAIL.

### HIGH — fresh child bootstrap is not self-contained under the exact D005 environment

`tools/g0/export_r09_b2_p5_resolved_config.py:1-18, 169-209`

The parent launches the P5 exporter script from the exporter worktree using the D005 canonical interpreter, D005 cwd, and exact sanitized D005 environment. That environment's `PYTHONPATH` points to the production `cosmos-framework`, not to the P5 exporter repo root.

However the exporter module imports `tools.g0.verify_r09_b2_p4_d005` at module import time. Under normal Python script execution, `sys.path[0]` is the script directory (`.../tools/g0`), not the repository root, while D005 `PYTHONPATH` does not add the exporter root. The fresh child can therefore fail before compose because the root-side `tools.g0` package is not importable under the exact D005 environment.

Required: make the child entrypoint demonstrably self-contained under the frozen D005 environment, for example by moving parent-only root imports out of child startup and using a reviewed bootstrap that does not mutate the semantic environment. Add a CPU fixture/subprocess smoke that proves the child entrypoint reaches its pre-compose guard under the exact constructed cwd/env/interpreter shape without performing real compose.

### MEDIUM — failed export leaves a non-fresh partial output directory

`tools/g0/export_r09_b2_p5_resolved_config.py:174-188`

`output_dir` is created before child execution and accumulates request/tree files before pair verification. If a child or verifier fails, the directory remains. A subsequent approved rerun with `exist_ok=False` is then blocked, and the path is no longer fresh.

Use a fresh staging/attempt directory and atomically promote only a PASS result, or preserve failed attempts under distinct immutable attempt names while keeping the canonical success destination fresh.

## What improved

The remediation meaningfully closes prior trust gaps:

- parent orchestration now exists;
- child requests are gated through the P4 pair verifier before construction;
- command/interpreter/TOML/ordered overrides, environment set/unset/inherit/effective, world/budget, P1/P3 launch bindings, derived output path, P4 record digest, frozen P3 verifier digest, local-history backend, and full selector list are checked per side;
- P3 backend contracts are no longer caller-owned.

Those improvements are substantial, but the remaining root/provenance/bootstrap issues make the reviewed execution path non-replayable or self-reported in important places.

## Decision

`APPROVE_TO_REQUEST_P5_STATIC_EXPORT` is **not granted**.

No config export, `load_experiment_from_toml`, launch/validate/instantiate, CUDA, torchrun, GPU, training, evaluation, inference, P5 closure, or B2-T is authorized by this review.
