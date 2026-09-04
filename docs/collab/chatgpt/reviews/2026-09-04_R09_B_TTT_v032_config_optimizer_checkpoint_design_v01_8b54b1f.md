# ChatGPT independent review — R09-B TTT v0.3.2 config/optimizer/checkpoint design v0.1

- Gate: `G0-R09-B-TTT-V032-CONFIG-OPTIMIZER-CHECKPOINT-DESIGN`
- Formal root/design SHA: `8b54b1f9a5f759ececa42098337a4ae9cc2e2a57`
- Child/Gitlink: `4f857ea430d6fb3c35ccbadc3933d552f8f9af8a`
- Request/bookkeeping SHA observed at review start: `d54c8249e6aeb9d029375f538e0c5e4a6390d5eb`
- Verdict: `REQUEST_CHANGES`

## HIGH-1 — `inner_lr` default is not frozen by the design

**Location**
- `docs/build/PSM-WMA_R09_B_TTT_v032_config_optimizer_checkpoint_design_v0.1_2026-09-04.md:8`
- `cosmos_framework/model/generator/mot/local_evidence.py` — `ContinualTTTLocalMemoryCore.__init__` currently freezes `inner_lr: float = 0.1`.

**Root cause**

The design makes `inner_lr` part of config/checkpoint identity, but states only that its default "must be fixed in implementation tests". That leaves an algorithmically material hyperparameter to be chosen by the implementation Gate. The current closed v0.3.2 core already has `inner_lr=0.1`; a config/checkpoint design must either explicitly inherit/freeze `0.1` or separately authorize an algorithm-authority change.

**Acceptance**

Freeze the exact default in the design (normally `inner_lr=0.1` to preserve current authority), and make the missing-field/default semantics unambiguous. Implementation tests may verify the frozen value, not choose it.

## HIGH-2 — optimizer/checkpoint module ownership is not bound to the exact runtime objects

**Location**
- `docs/build/PSM-WMA_R09_B_TTT_v032_config_optimizer_checkpoint_design_v0.1_2026-09-04.md:12-21`
- `cosmos_framework/model/generator/mot/production_runtime_adapter.py:13-15`

**Root cause**

The design freezes optimizer paths `local_history_runtime.encoder` and `local_history_runtime.recurrent_backend`, but the closed production runtime seam is a plain Python controller: `ProductionLocalMemoryRuntime` receives `encoder`/`core` objects and passes them into `ProductionRuntimeAuthority`. The design does not freeze that the objects registered under the model's optimizer/checkpoint tree are the exact same objects used by the runtime authority. An implementation can therefore satisfy the named-parameter inventory while accidentally constructing a second encoder/core for runtime, causing optimizer/checkpoint to train/save one copy while Local runtime executes another.

**Acceptance**

Freeze one slow-parameter `nn.Module` owner (e.g. `local_history_runtime`) containing exactly `encoder` and `recurrent_backend`, and require the production runtime/authority to reference those exact registered objects rather than constructing copies. Add CPU/static evidence proving object identity/no duplicate trainable Local modules, exact `named_parameters()` inventory, and checkpoint round-trip of the same objects used by the runtime seam.

## Scope

No other blocker found in the reviewed design delta. This verdict does not authorize config/optimizer/checkpoint implementation, active trainer changes, real checkpoint I/O, GPU/CUDA/torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1.
