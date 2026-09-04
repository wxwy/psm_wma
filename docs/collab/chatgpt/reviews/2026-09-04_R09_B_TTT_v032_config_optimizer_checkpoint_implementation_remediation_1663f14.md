# ChatGPT independent re-review — R09-B TTT v0.3.2 config/optimizer/checkpoint implementation remediation

- Gate: `G0-R09-B-TTT-V032-CONFIG-OPTIMIZER-CHECKPOINT-IMPLEMENTATION`
- Formal root implementation SHA: `1663f14a2d22415bbf9bd3b68b2ed7ae567e1f03`
- Child/Gitlink: `c7902fbdee6c147679a14086b2836754ba0f94e4`
- Frozen design authority: `93c9974266a58a2cd54ab3e524bd2d8e0c2ab6d0`
- Prior blocked implementation: `b3efa4a5e50395ecbc8748d60b745d8fad8c9ff8` / `e54fba4c3b71993f1d1af299392ab5f32c6a45db`
- Verdict: `REQUEST_CHANGES`

## Prior finding status

- Prior HIGH-1 (exact selector / optimizer membership missing): **PARTIALLY CLOSED, remains blocking**.
- Prior HIGH-2 (strict-load checkpoint restore missing): **PARTIALLY CLOSED, remains blocking**.
- Prior MEDIUM (bool / K_local validation): **PARTIALLY CLOSED**. `K_local` is now restricted to `{1,4,8}` and bool is rejected for `ttt_tbptt_steps` / `k_local`, but bool / non-integral aliasing remains for other config fields.

## HIGH-1 — optimizer membership validator is group-presence, not exact parameter membership

**Location**
- `cosmos_framework/model/generator/mot/config_checkpoint_contract.py:47-55`
- `cosmos_framework/model/generator/mot/config_checkpoint_contract_test.py:54-62`

**Root cause**

`validate_optimizer_membership()` accepts any set of names as long as every name falls under one of the four allowed prefixes and each prefix appears at least once. It does not compare the candidate optimizer membership against the exact parameter inventory derived from the registered `local_history_runtime` module plus the two external registered Local objects. Therefore an optimizer selector can silently omit arbitrary encoder/backend parameters while still passing, provided at least one parameter remains in each group. It also does not prove parameter-object identity/no duplication for the actual optimizer membership.

**Frozen-contract violation**

Design v0.2 requires exact `named_parameters()` inventory/count, exact four-group optimizer membership, runtime/registered object identity, no duplicate trainable Local module, and fail-closed selector omission/extra cases. Group-prefix presence is weaker than exact membership.

**Acceptance**

Derive one canonical expected slow-parameter mapping from the registered `local_history_runtime.encoder`, `local_history_runtime.recurrent_backend`, `local_memory2llm`, and `local_memory_modality_embed`; require candidate optimizer parameter names and parameter object identities to match it exactly (no missing, no extra, no duplicate object). Add a negative fixture that removes one non-last parameter from a multi-parameter encoder/backend while leaving all four groups present, and prove rejection.

## HIGH-2 — `strict_restore()` validates a dict but does not perform the frozen same-object checkpoint round-trip

**Location**
- `cosmos_framework/model/generator/mot/config_checkpoint_contract.py:65-78`
- `cosmos_framework/model/generator/mot/config_checkpoint_contract_test.py:43-53`

**Root cause**

`strict_restore()` checks key/config/shape/dtype equality and returns detached tensor clones. It never restores those tensors into the registered slow `nn.Module` objects, never proves a strict module/state-dict round-trip, and never verifies after restore that the production runtime/authority still references the same registered encoder/backend objects. The test is a one-entry dictionary round-trip, not the frozen same-object runtime round-trip.

**Frozen-contract violation**

Design v0.2 explicitly requires CPU/static checkpoint round-trip on the same registered objects and verification that runtime still references those objects after restore. A clone-return helper does not close that contract.

**Acceptance**

Implement a CPU/static strict restore path over the canonical slow registered objects (or an equivalent explicit state-dict owner) that mutates/restores the same objects, rejects missing/extra/shape/dtype/config drift before accepting closure, and proves `runtime.encoder is local_history_runtime.encoder` plus `runtime.backend/core is local_history_runtime.recurrent_backend` after round-trip. Include multi-parameter round-trip evidence, not a single tensor dictionary.

## MEDIUM — config type fail-closed remains incomplete

**Location**
- `cosmos_framework/model/generator/mot/config_checkpoint_contract.py:27-35`
- `cosmos_framework/model/generator/mot/config_checkpoint_contract_test.py:18-24`

**Root cause**

`inner_lr=True` passes because `bool` is an `int`, and `runtime_evidence_steps=True` / `1.0` pass equality with integer `1`. The frozen design requires wrong types to reject; only `ttt_tbptt_steps` and `k_local` currently have explicit bool rejection.

**Acceptance**

Reject bool for `inner_lr`; require `runtime_evidence_steps` to be an actual non-bool integer equal to `1`; add direct negative fixtures. Keep `K_local in {1,4,8}` and the existing positive/finite checks.

## Scope

Child delta remains limited to the approved CPU/static contract and adjacent tests; no active trainer, real checkpoint I/O, GPU/CUDA/torchrun, training/evaluation/inference, P4/P5 or LIBERO4IN1 scope drift was found.

Remediation should remain limited to `config_checkpoint_contract.py`, its adjacent test, and root bookkeeping/status. No active trainer or real checkpoint path changes are authorized by this verdict.
