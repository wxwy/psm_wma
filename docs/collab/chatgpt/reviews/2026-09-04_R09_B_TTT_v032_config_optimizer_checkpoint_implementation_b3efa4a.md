# ChatGPT independent review — R09-B TTT v0.3.2 config/optimizer/checkpoint implementation

- Gate: `G0-R09-B-TTT-V032-CONFIG-OPTIMIZER-CHECKPOINT-IMPLEMENTATION`
- Formal root implementation SHA: `b3efa4a5e50395ecbc8748d60b745d8fad8c9ff8`
- Child/Gitlink: `e54fba4c3b71993f1d1af299392ab5f32c6a45db`
- Frozen design authority: `93c9974266a58a2cd54ab3e524bd2d8e0c2ab6d0`
- Verdict: `REQUEST_CHANGES`

## HIGH-1 — exact selector / optimizer-membership contract is not implemented

**Location**
- `cosmos_framework/model/generator/mot/config_checkpoint_contract.py:12-18,39-45`
- `cosmos_framework/model/generator/mot/config_checkpoint_contract_test.py:26-40`

**Root cause**

The implementation declares the four frozen `SELECTORS`, but no code consumes them. `validate_slow_inventory()` only checks that `module.encoder` / `module.recurrent_backend` are the same objects as two runtime references, rejects a `readout.*` parameter, and returns every remaining `named_parameters()` entry. It does not validate the exact four selector groups, does not include/check `local_memory2llm` or `local_memory_modality_embed`, and does not build or validate optimizer membership. Selector swap/omission/extra membership therefore cannot fail closed.

**Acceptance**

Implement a public CPU/static selector contract that resolves exactly the four frozen groups, proves exact inventory/count and no duplicate trainable Local object, and validates optimizer membership. Add direct negative fixtures for selector swap, missing group, extra parameter/group, dormant readout, disabled path, and runtime object identity.

## HIGH-2 — strict-load checkpoint contract is absent

**Location**
- `cosmos_framework/model/generator/mot/config_checkpoint_contract.py:48-52`
- `cosmos_framework/model/generator/mot/config_checkpoint_contract_test.py:43-48`

**Root cause**

`slow_checkpoint_payload()` only clones a supplied parameter mapping and stores a `LocalMemoryConfig`. There is no load/restore path at all, so the frozen contract cannot reject missing/extra keys, shape mismatch, dtype mismatch, config drift, or verify that restored production runtime still references the same registered objects. The single checkpoint test proves only cloning plus one `fast_state` name rejection, not strict round-trip semantics.

**Acceptance**

Add CPU/static strict-load/restore logic over the frozen slow-module inventory and config identity. Directly prove round-trip plus rejection of missing, extra, shape, dtype and each config-identity drift; prove fast runtime state exclusion and post-restore runtime-object `is` identity. No real checkpoint I/O is required or authorized.

## MEDIUM-1 — config validator is weaker than the frozen schema

**Location**
- `cosmos_framework/model/generator/mot/config_checkpoint_contract.py:28-36`
- `cosmos_framework/model/generator/mot/config_checkpoint_contract_test.py:14-24`

**Root cause**

`isinstance(True, int)` is true, so boolean `ttt_tbptt_steps` / `k_local` values are accepted. `k_local` accepts any positive integer even though v0.2 freezes first-version support to `1/4/8`. Current negative fixtures do not cover either case.

**Acceptance**

Reject bool for integer fields and reject unsupported `K_local` values outside `{1,4,8}`; add direct fixtures including `True`, `False`, and `K_local=2`.

## Scope

Child delta from `4f857ea...` to `e54fba4...` is exactly two new CPU/static files: `config_checkpoint_contract.py` and its adjacent test. No active trainer, real checkpoint I/O, GPU, training/eval/inference scope drift found. Repository-recorded evidence says related suite `68 passed`, py_compile and child diff-check PASS; this does not close the missing frozen behaviors above.

Allowed remediation remains this CPU/static config/selector/checkpoint contract and adjacent tests plus root bookkeeping only. Active trainer, real checkpoint I/O, GPU/CUDA/torchrun, training/eval/inference, P4/P5 and LIBERO4IN1 remain prohibited.
