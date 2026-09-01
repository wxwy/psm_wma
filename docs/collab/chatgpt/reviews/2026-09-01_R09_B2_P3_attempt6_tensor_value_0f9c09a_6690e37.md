# R09-B2 P3 attempt-6 JSON-safe Tensor metadata review

- Request: `0f9c09a2ef26f1426d1d2fe353622dc2f57ae68d`
- Implementation: `6690e374d828357b39c211175b8b94c98b54292e`
- Evidence anchor: `af68eb78e2dc0fbb3b09dae7ef52053d65a684ab`
- Submodule/Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Verdict: `REQUEST_CHANGES`

## HIGH — scalar Tensor param-group values are serialized without their value

`tools/g0/collect_r09_b2_p3_gpu_inventory.py::_canonical_param_group_value()` now makes capturable optimizer group Tensor metadata JSON-safe, but its Tensor branch returns only `kind/shape/dtype/numel` through `_tensor_metadata()` and drops the actual scalar value.

That means e.g. `torch.tensor(1e-4)` and `torch.tensor(1e-3)` canonicalize to the same record. The new regression explicitly asserts only `{kind:tensor, shape:[], dtype:float32, numel:1}`, so it freezes the information loss rather than detecting it.

This is a gate-integrity issue, not cosmetic serialization: P3 is inventorying actual production optimizer group metadata, and `diff_checks()` compares DCP optimizer metadata fields including `value`. For capturable scalar Tensor `lr`/`weight_decay`, `value` is absent on both sides, so recurrent and TTT can carry different actual hyperparameter values while the verifier still reports shared metadata equal.

### Required fix

1. Keep tensor-valued optimizer **state** schema metadata-only; do not start copying optimizer-state tensor contents.
2. For **param-group metadata only**, canonicalize scalar/one-element Tensor values to deterministic JSON-safe metadata that includes their numeric value, e.g. `{kind:"tensor", shape:[], dtype:"float32", numel:1, value:0.0001}`.
3. Reject non-finite scalar Tensor values fail-closed.
4. For non-scalar Tensor param-group metadata, either define a deterministic bounded value representation or fail-closed; do not silently reduce it to shape/dtype/numel if semantic equality is required.
5. Add a permanent regression proving two scalar Tensor values with identical shape/dtype but different values canonicalize differently.
6. Add/extend a verifier regression proving recurrent-vs-TTT scalar Tensor `lr` (or another shared param-group field) value mismatch makes `shared_dcp_optimizer_schema_metadata` fail.
7. Keep attempt-6 GPU execution prohibited until this static blocker closes. All existing 28 GiB, fresh-output, canonical-FQN, fail-stop, offline/local-only and no-forward/backward/step boundaries remain unchanged.

No GPU authorization is granted by this review.
