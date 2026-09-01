# R09-B2 P3 flattened optimizer-DCP re-review

- Request: `a3e6c7daa8468e19be7a81af6f3b8865c824f381`
- Implementation: `d46818eafa849bdc53e24cfa1d07164a6f62ce7c`
- Submodule/Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Verdict: **REQUEST_CHANGES**

## Findings

### HIGH — flattened key grammar is corrected, but flattened value grammar is still too restrictive

`tools/g0/collect_r09_b2_p3_gpu_inventory.py::_flattened_optimizer_schema()` now correctly recognizes the production flattened key families `state.<FQN>.<suffix>` and `param_groups.<FQN>.<suffix>` and maps them back to stable parameter owners. This closes the previous key-ownership blocker.

However, after locating the owner, the implementation calls `_state_leaf_metadata(value, flat_key)` and requires `len(metadata) == 1`, raising `RuntimeError("flattened optimizer value must be scalar or tensor")` otherwise.

That assumption is false for the production PyTorch flattened optimizer format. PyTorch's current `_flatten_optim_state_dict()` directly copies every `param_group` value under `param_groups.<FQN>.<key>`; its own documented example includes `param_groups.layer1.weight.betas = (0.9, 0.95)`. Therefore a normal Adam/AdamW/FusedAdam parameter group containing a tuple-valued `betas` entry will produce multiple leaves under `_state_leaf_metadata()` and the P3 worker will fail even though the production optimizer state dict is valid.

The new regression covers float (`lr`) and tensor (`exp_avg`) values, but does not cover the tuple-valued parameter-group metadata that the real optimizer emits.

Required fix:

1. Keep the exact flattened key ownership parser.
2. Treat `state.*` leaf values according to PyTorch's flattened state rules (tensor/int/float after nested dict flattening).
3. Treat `param_groups.*` values as production param-group metadata, not as scalar/tensor-only values. Canonicalize supported structures such as tuple/list/scalar/bool/None into a deterministic JSON-safe representation without changing owner/namespace/suffix identity.
4. Add a permanent regression containing at minimum `param_groups.net.a.betas = (0.9, 0.95)` and verify it parses successfully and participates in recurrent-vs-TTT schema metadata comparison.
5. Keep fail-closed behavior for unsupported/non-deterministically serializable values.

Until this is fixed, a real GPU P3 run is likely to block on ordinary optimizer metadata before the intended inventory can be evaluated.

## Previous blocker status

The previous HIGH around flattened optimizer DCP ownership is substantially addressed: schema owners are checked against `optimizer_parameter_references`, duplicate `(owner, namespace, suffix)` identities are rejected, and owner/namespace/suffix are tied back to `flat_key` in the verifier.

The previous MEDIUM around recurrent-vs-TTT optimizer-DCP schema comparison is also implemented: TTT-only schema is rejected, recurrent-only schema must stay under the verifier-owned recurrent prefix, and shared schema metadata is compared.

## Scope

This review does **not** authorize GPU execution. Continue static implementation/testing only. `APPROVE_TO_REQUEST_GPU_P3_RUN` is not granted yet. Existing prohibitions remain: no GPU worker run, no processor/model/VAE construction, no checkpoint/data I/O, no forward/backward/optimizer/scheduler step, no B2-T/P4/P5/training/eval/inference/closed-loop/SR/multi-GPU/long-training/backend-freeze/Global/Agent/RL.
