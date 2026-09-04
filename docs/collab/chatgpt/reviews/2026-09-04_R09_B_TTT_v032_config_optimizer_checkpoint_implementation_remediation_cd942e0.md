# ChatGPT independent re-review — R09-B TTT v0.3.2 config/optimizer/checkpoint implementation remediation

- Gate: `G0-R09-B-TTT-V032-CONFIG-OPTIMIZER-CHECKPOINT-IMPLEMENTATION`
- Formal root/remediation SHA: `cd942e01a894b2f952e8ea6e1785d918db86b25d`
- Child/Gitlink: `86890bc7ebe8b68ebc241c407f0654373f3e92e2`
- Frozen design authority: `93c9974266a58a2cd54ab3e524bd2d8e0c2ab6d0`
- Verdict: `REQUEST_CHANGES`

## Prior finding closure

- Prior HIGH-1 (optimizer membership only proved group-prefix presence): **CLOSED**. `canonical_slow_inventory()` now builds the canonical four-group slow inventory and `validate_exact_optimizer_membership()` requires exact key set, exact Python object identity for every tensor, and no duplicate objects.
- Prior MEDIUM (bool / runtime_evidence type fail-closed): **CLOSED**. `inner_lr` rejects bool and `runtime_evidence_steps` requires a non-bool integer exactly equal to 1; `K_local` remains restricted to 1/4/8.

## HIGH-1 — strict checkpoint round-trip still restores only `local_history_runtime`, not all four frozen slow groups

**Location**
- `cosmos_framework/model/generator/mot/config_checkpoint_contract.py` — `strict_restore_into()`
- `cosmos_framework/model/generator/mot/config_checkpoint_contract_test.py` — `test_checkpoint_is_slow_only_and_cloned()`

**Root cause**

The frozen v0.2 design requires checkpoint round-trip over all four slow groups: `local_history_runtime.encoder`, `local_history_runtime.recurrent_backend`, `local_memory2llm`, and `local_memory_modality_embed`, while preserving runtime/registered-object identity.

The remediation correctly adds `canonical_slow_inventory()` containing all four groups, but `strict_restore_into()` accepts only the `local_history_runtime` owner module, strips only the `local_history_runtime.` prefix, and calls `module.load_state_dict(..., strict=True)`. It has no destination arguments or restore path for `local_memory2llm` or `local_memory_modality_embed`.

The current round-trip fixture correspondingly builds `own_expected` only from `owner.named_parameters()` and never mutates/restores the external projector or modality embedding. Thus the implementation can pass while those two frozen slow groups are absent from actual restore.

**Frozen-contract violation**

Design v0.2 §3 requires slow-only strict checkpoint round-trip of the registered slow state and post-restore same-object runtime identity. A helper that validates/clones all names but loads only one owner submodule is insufficient to close that contract.

**Acceptance**

Within the existing CPU/static two-file boundary, add one strict restore surface/fixture that:
1. snapshots the canonical four-group inventory from the same registered objects;
2. mutates all four groups after snapshot;
3. restores all four groups into those same objects, using strict name/shape/dtype/config identity checks;
4. proves every parameter value is restored and the `local_history_runtime.encoder/recurrent_backend` object identities are unchanged;
5. retains missing/extra/shape/dtype/config-drift failures and fast-state exclusion.

No active trainer, real checkpoint I/O, GPU, training, evaluation or inference is authorized.

## Scope

Child delta from prior reviewed `c7902fb...` stays confined to `config_checkpoint_contract.py` and its adjacent test; no active trainer/GPU/training scope drift found.
