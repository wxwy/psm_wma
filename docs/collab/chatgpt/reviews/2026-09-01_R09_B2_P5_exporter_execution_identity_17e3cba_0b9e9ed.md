# R09-B2 P5 exporter execution identity / failed-attempt remediation review

- Request commit: `17e3cba6fe891e719103ca1f8d714d792709ece3`
- Implementation commit: `0b9e9edbe152800bec541636b4627433daee9518`
- Reviewed Gitlink/submodule: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Verdict: **APPROVE_TO_REQUEST_P5_STATIC_EXPORT**

## Scope

This review is intentionally limited to the two remediation items named in the request:

1. binding the actual executing P5 exporter and imported P5 verifier to `exporter_root`; and
2. retaining a fail-closed staging record without promoting a canonical result when the parent export path raises.

It does not authorize the static export itself, production compose, GPU work, or training.

## Findings

### Execution identity is now internally derived and checked before any child compose

`tools/g0/export_r09_b2_p5_resolved_config.py:198-217`

`bound_exporter_source()` now:

- derives the canonical exporter and verifier paths from `exporter_root`;
- requires the currently executing exporter module's `__file__` to equal the exporter-root-owned path;
- requires the actually imported P5 verifier module's `__file__` to equal the exporter-root-owned verifier path;
- obtains the exporter revision and tool digests from the exporter-root verifier rather than caller-supplied provenance; and
- cross-checks both on-disk file SHA256 values before returning the verifier function used by the parent.

`run_parent_export()` no longer accepts caller-owned `tool_sha256` or `exporter_root_revision`. It invokes `bound_exporter_source()` before entering the child loop and launches each child through the exporter script located under the validated `exporter_root` (`tools/g0/export_r09_b2_p5_resolved_config.py:233-250`). Thus an A-process/B-exporter-root mismatch fails before `load_experiment_from_toml` can be reached.

### Failed attempts are retained and cannot be promoted as canonical evidence

`tools/g0/export_r09_b2_p5_resolved_config.py:233-266`

The parent creates a unique attempt directory, performs child execution, envelope assembly, and pair verification inside a `try` block, and renames the attempt directory to the canonical output only after the pair verifier returns `PASS`. Any ordinary exception after attempt creation writes a canonical `failure.json` containing `schema_version`, `status=FAIL`, stage, exception type, and message, then re-raises. The canonical output path is not created on that failure path.

The permanent CPU fixture covers both relevant regressions:

- executing implementation A while claiming exporter root B is rejected; and
- a forced child failure leaves exactly one failed attempt with `failure.json` while the canonical output remains absent (`tools/g0/test_r09_b2_p5_full_config_diff.py:100-117`).

## Decision

No blocking issue was found within the explicitly requested remediation scope. The implementation may proceed to submit a separate, concrete `APPROVE_TO_RUN_P5_STATIC_EXPORT` request.

That execution request must freeze the exact parent invocation in a fresh interpreter, `exporter_root` at `0b9e9edbe152800bec541636b4627433daee9518`, the already reviewed production/evidence roots, and a fresh output/staging location outside all three roots. Any exporter/verifier code change requires another static review.

This approval does **not** execute or authorize `load_experiment_from_toml`, config export, `torchrun`, CUDA/GPU, model construction, checkpoint loading, training, evaluation, inference, P5 closure, or B2-T.
