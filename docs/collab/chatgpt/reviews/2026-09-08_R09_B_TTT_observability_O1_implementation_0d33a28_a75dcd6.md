# ChatGPT independent review — R09-B TTT Observability O1 CPU/static implementation

- Gate: `G0-R09-B-TTT-OBSERVABILITY-O1-IMPLEMENTATION`
- Formal root implementation SHA: `0d33a28ec462d21e02600cf5f82456b995feef3c`
- Formal child/Gitlink SHA: `a75dcd612add5779956286fc8df12afcdd858070`
- Approved O1 design baseline: root `9a65bed8c5260d6e2981dcc659b1f3abf4602a80` / child `333792e845fe3b15ba4d8af8f34f704de2a79fa2`
- Verdict: `REQUEST_CHANGES`

## Incremental scope

The child delta from `333792e` to `a75dcd6` is limited to the two approved files:
- `cosmos_framework/callbacks/norm_monitor.py`
- `cosmos_framework/callbacks/norm_monitor_test.py`

The implementation correctly preserves the main O1 semantics: selector roots derive from `config_checkpoint_contract.SELECTORS`; the modality embedding is exact-leaf matched; legacy predicate/EMA exclusion remain separate; custom groups build float32 `[param_sq_sum, grad_sq_sum, grad_present_count]`; exactly one `SUM` all-reduce is issued per group in the implementation; rank0 omits the grad key only when reduced presence is zero and emits exact `0.0` for present-but-zero grad.

## Blocking finding

1. **MEDIUM — tests/Evidence only — `cosmos_framework/callbacks/norm_monitor.py:334-350`; `cosmos_framework/callbacks/norm_monitor_test.py:1-54`.** The frozen v0.2 CPU/static acceptance requires synthetic per-rank packed-payload coverage plus evidence for the per-group single-SUM helper/input-output and no duplicate parameter counting. The implementation constructs the local packed payload and invokes `dist.all_reduce` inline in `_compute_and_log_stats()`, but the 7 committed tests only feed already-reduced tensors into `_group_metric_values()`. They therefore do not exercise or prove: local payload construction from selected parameters/`param.grad is not None`; summation of `grad_present_count` across synthetic ranks; exactly one group SUM; or absence of duplicate parameter contribution. The claimed mixed-rank case is represented only as a pre-reduced payload, so it cannot catch an error in the pack/reduce path.

Acceptance: add a pure CPU/static testable seam (or equivalent monkeypatched collective seam that initializes no distributed process group/CUDA) covering local payload construction, synthetic rank SUM, no-grad, zero-grad, mixed-rank presence, nonzero grad, exactly one SUM per group, and unique parameter contribution. Keep production behavior unchanged. Relevant pytest, both-file `py_compile`, and child/root `diff --check` must pass.

This is not a production-semantic blocker in the reviewed code path; it is a mandatory acceptance/Evidence gap. The reported `7 passed`, `py_compile`, and root/child `diff --check` were read from the request and were not independently executed.

No callback defaults/recipes/trainer/model/runtime/optimizer/checkpoint/dataset/W&B backend/production wiring, real I/O, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1 is authorized by this verdict.
