# R09-B2 P3 GPU inventory worker static implementation review

- Review request root: `d27d117255763f14c696fb0e3d0e4ba45ff4b0f4`
- Reviewed implementation root: `0d3af2eefa22d449fac1d0a49d6a075b34ec95b6`
- Submodule/Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Requested verdict: `APPROVE_TO_REQUEST_GPU_P3_RUN` or `REQUEST_CHANGES`
- Scope reviewed: static worker / collector / verifier / tests only. No GPU execution authorization.

## Verdict

**REQUEST_CHANGES**

The worker is substantially closer to the frozen P3 contract: it uses the shared production VLM processor primitive, constructs the production model/optimizer with only the explicit `load_vision_tokenizer=False` inventory override, invokes `ModelWrapper.state_dict()` and `OptimizersContainer.state_dict()`, records group metadata and model-DCP membership, keeps the recurrent-only allowlist verifier-owned, and preserves the no-forward/no-backward/no-step boundary.

However the implementation is not ready for a GPU run request because the production optimizer-DCP membership parser does not match the flattened production schema it is supposed to inspect.

## HIGH — `_stable_parameter_references()` cannot parse the production flattened optimizer state-dict

File: `tools/g0/collect_r09_b2_p3_gpu_inventory.py`, helper `_stable_parameter_references()` and `_worker_inventory()`.

The worker calls the real production API:

```python
optimizer_dcp = optimizer.state_dict()
optimizer_references = _stable_parameter_references(optimizer_dcp, set(parameters))
if optimizer_references != selected:
    raise RuntimeError(...)
```

`OptimizersContainer.state_dict()` in the reviewed submodule delegates to `get_optimizer_state_dict(..., StateDictOptions(flatten_optimizer_state_dict=True))`.

But `_stable_parameter_references()` only recognizes a string when the **entire string**, after optionally removing a leading `net.`, equals one stable parameter name:

```python
candidate = value.removeprefix("net.")
if candidate in stable_names:
    references.add(candidate)
```

That is incompatible with a flattened optimizer state-dict, where a parameter FQN is embedded inside flattened state/param-group paths (for example a state leaf or param-group field contains the parameter FQN plus surrounding path/suffix). The current parser therefore cannot reliably recover membership from the actual production object it invokes. For a non-empty optimizer selection, this can make `optimizer_references != selected` even when the production state-dict is correct, blocking the worker before it can produce a valid P3 artifact.

The committed test does not catch this because it feeds the helper a hand-built **unflattened** fixture:

```python
{"state": {"net.a": {...}}, "param_groups": [{"params": ["net.a"]}]}
```

That tests a schema different from the production `flatten_optimizer_state_dict=True` path.

### Required fix

1. Parse the actual flattened optimizer state-dict schema, extracting the exact stable parameter FQN from flattened `state.*` / `param_groups.*` keys without substring ambiguity.
2. Prefer a parser driven by the actual PyTorch production output rather than ad-hoc string containment.
3. Add a permanent regression that obtains or faithfully mirrors the real flattened schema and proves:
   - selected stable names are recovered exactly;
   - a prefix/suffix lookalike does not false-match;
   - one omitted selected parameter causes FAIL;
   - one extra/unmapped parameter causes FAIL.
4. Keep the production `OptimizersContainer.state_dict()` call as the source of truth; do not fall back to the already-known optimizer param groups to fabricate DCP membership.

## MEDIUM — matched recurrent-vs-TTT diff does not cover optimizer-DCP schema itself

File: `tools/g0/verify_r09_b2_p3_gpu_inventory.py`, `diff_checks()`.

The verifier compares:
- resolved selector membership;
- optimizer membership;
- model parameter names/metadata;
- named buffers;
- model DCP keys.

But it does not compare the production optimizer-DCP flattened schema (`optimizer_state_schema`) between recurrent and TTT. Once the membership parser is fixed, a backend-specific optimizer-DCP key/schema drift outside `local_history_runtime.recurrent_backend.` could still escape the matched-diff gate while model-DCP keys remain clean.

### Required fix

Normalize optimizer-DCP flattened keys to stable parameter ownership plus state/group suffix, then require recurrent-vs-TTT differences to be empty except for entries owned by the verifier-controlled recurrent-only prefix. Shared entries should have compatible schema/metadata.

Add a negative regression with a TTT-only optimizer-DCP state/group key outside the recurrent prefix and require final verifier `FAIL`.

## Accepted from this round

- Shared production processor primitive `build_vlm_processor(vlm_config)` remains the construction source of truth.
- Validated tokenizer binding and actual construction input are cross-checked before construction.
- Only declared inventory model override is `load_vision_tokenizer: True -> False`.
- Production model and optimizer constructors are used.
- `ModelWrapper.state_dict()` and `OptimizersContainer.state_dict()` are actually invoked rather than represented by symbolic strings alone.
- Optimizer param-group membership is reverse-mapped from actual parameter objects.
- Model-DCP selected membership is checked by stable parameter names.
- Full model parameter/buffer/model-DCP matched diff is bounded by verifier-owned recurrent-only prefix.
- No forward/backward/optimizer-step/scheduler-step/checkpoint save/load is introduced by the reviewed worker code.
- GPU run remains separately gated by the exact run token.

## Scope

This verdict authorizes only continued static correction and tests.

Still not authorized:
- GPU execution;
- HF/processor/model construction in an actual run;
- VAE, checkpoint/model-weight, data or dataloader loading;
- forward/backward/optimizer/scheduler step;
- DCP save/load;
- B2-T / P4 / P5;
- training/eval/inference/closed-loop/SR;
- multi-GPU/long training/backend freeze/Global/Agent/RL.
