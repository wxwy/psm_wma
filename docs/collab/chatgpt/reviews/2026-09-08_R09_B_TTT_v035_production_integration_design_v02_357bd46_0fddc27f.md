# ChatGPT independent review — R09-B TTT v0.3.5 production integration implementation design v0.2

- Gate: `G0-R09-B-TTT-V035-PRODUCTION-INTEGRATION-IMPLEMENTATION-DESIGN`
- Formal root design SHA: `357bd468276b947b5f57d83d5f670e87d634bac7`
- Formal child/Gitlink SHA: `0fddc27f9c3c463f784be9f528ffbbe123f244ff`
- Request/bookkeeping SHA observed: `ab9e49564118fa9c86b4e4585864db1aad4552a4`
- Requested literal: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_PRODUCTION_INTEGRATION_CPU_STATIC` or `REQUEST_CHANGES`
- Verdict: `REQUEST_CHANGES`

## Scope checked

Fresh incremental docs-only review relative to `8697a4c/0fddc27f`. No child code/tests, real I/O, GPU, training, evaluation or inference were executed by this reviewer.

## Closure status

CLOSED — prior HIGH failure-taxonomy blocker: v0.2 now preserves canonical v0.3.8/v0.3.9 semantics. Only same-digest `LOAD_DECODE_TRANSIENT` at attempt=0 may create the unique suffix recovery plan; attempt=1 exhausts with `LOCAL_MEM_RETRY_EXHAUSTED`; identity/planned mismatch, numerical and outer failures are terminal and never redeliver.

CLOSED — prior HIGH loss-partition blocker: v0.2 freezes a structured `(primary_consumer_mean, auxiliary_loss)` ABI, raw-native finiteness, normal `(N_valid_mu/N_window)*primary + (1/GA)*auxiliary`, recovery `GA_effective`, and forbids valid-ratio scaling of total loss or a second `/grad_accum_iter`.

## Current blocker

1. **MEDIUM — `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_integration_implementation_design_v0.2.md:9`: the whitelist is path-complete but still not implementation-exact.**

   Repository truth at child `0fddc27f` shows both `cosmos_framework/model/generator/mot/local_memory_segment_test.py` and `cosmos_framework/model/generator/mot/c6_runtime_adapter_test.py` already exist, while v0.2 labels them as files to be newly created. Only `cosmos_framework/trainer/trainer_local_memory_integration_test.py` is absent. In addition, the allowed changes in `c6_runtime_adapter.py` and `trainer/__init__.py` are described only as “新增 canonical adapter facade” and “唯一 Local loss/backward seam”, without freezing the exact new symbol/function/class names or the exact existing symbols that may be modified. Because this Gate literal directly authorizes implementation, that leaves the edit surface ambiguous and does not fully satisfy the previous acceptance condition to mark each file new-vs-existing and identify exact symbols/seams before approval.

   **Acceptance:** revise the whitelist so that (a) `local_memory_segment_test.py` and `c6_runtime_adapter_test.py` are explicitly marked existing/modified, while `trainer_local_memory_integration_test.py` is explicitly new; (b) freeze the exact canonical adapter class/function name(s) to be added in `c6_runtime_adapter.py`; (c) freeze the exact trainer Local loss/backward function/seam symbol(s) that may be added/modified in `trainer/__init__.py`; and (d) state that all other existing symbols in those files, including the historical `C6SyntheticRuntimeAdapter`, remain behaviorally unchanged unless individually named. Keep the already-correct taxonomy, loss formulas, tests and prohibition boundary unchanged.

## Boundary status

The docs-only boundary is sound. This verdict authorizes no production-integration implementation, real checkpoint/data/cache I/O, registry/defaults, model-forward wiring, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1. Review/Inbox bookkeeping does not change the formal pair.
