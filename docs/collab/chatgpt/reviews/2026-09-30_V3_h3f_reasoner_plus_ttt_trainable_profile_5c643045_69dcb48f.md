# PSM-WMA V3 — H3-F formal trainable profile: Reasoner + Local-TTT

- Date: 2026-09-30
- Formal root: `5c643045534fa080612239a6ba752a55226ef6c3`
- Formal child/Gitlink: `69dcb48fa0e188f95d43590300dad7542b6a9ab5`
- Status: **H3F_REASONER_TTT_PROFILE_IMPLEMENTED_PENDING_REVALIDATION**
- H3-E status: unchanged / CLOSED
- H3-F long-run authorization: NOT YET AUTHORIZED

## Formal H3-F trainable profile

H3-F no longer inherits the H3-E integration-smoke optimizer inventory.

Formal H3-F now trains exactly:

- `net.language_model.*` **excluding any parameter whose name contains `_moe_gen`**;
- `net.local_memory*` (including Local-TTT runtime/core/projection parameters).

Everything else is frozen.

This means the following H3-E smoke trainables are now frozen for H3-F:

- `moe_gen`;
- `time_embedder`;
- `vae2llm`;
- `llm2vae`;
- `action2llm`;
- `llm2action`;
- `action_modality_embed`.

## Why the selection is two-stage

The shared optimizer only supports positive substring selection and has no exclusion expression.

H3-F therefore sets:

`config.optimizer.keys_to_select = ["language_model", "local_memory"]`

but before the optimizer is constructed it also rewrites `requires_grad` exactly:

- reasoner: `net.language_model.*` and no `_moe_gen`;
- Local-TTT: `net.local_memory*`;
- all other parameters: frozen.

The optimizer-inventory witness then requires the selected parameter names to equal this exact
expected set. This prevents the `language_model.*_moe_gen` generation duplicates from being
accidentally trained.

## Optimizer / digest changes

- H3-F action-head LR multipliers are cleared.
- Base optimizer LR remains the H3-F inherited 5e-5 unless changed by a separately reviewed contract.
- The formal config digest now binds:
  - trainable profile = `reasoner_without_moe_gen+local_memory`;
  - optimizer keys = `language_model, local_memory`;
  - save cadence;
  - 30k horizon / warmup / evaluation milestones.

A same-job resume with the old H3-E-style selector therefore cannot silently pass as the same H3-F
configuration.

## Runtime inventory evidence

The H3-F optimizer wrapper records:

- selected reasoner tensor count;
- selected reasoner parameter count;
- selected Local parameter count (must remain 165312);
- complete selected names;
- trainable profile identity.

Any selected action/generation host key or any `_moe_gen` parameter is a hard failure.

## Gradient witness

The formal observer now requires both:

- Local gradient witness;
- at least one non-empty, non-zero Reasoner gradient witness.

Thus readiness cannot pass merely because the optimizer inventory looks correct: the Reasoner
branch must actually participate in the native loss backward path.

## Next Gate

Revalidate the exact pair with CPU/static checks and owner-env preflight. Then rerun the short
H3-F readiness smoke. The readiness evidence must explicitly show:

- selector = [language_model, local_memory];
- trainable_profile = reasoner_without_moe_gen+local_memory;
- selected_reasoner_params > 0;
- selected_local_params = 165312;
- no selected `_moe_gen` / action-generation host parameters;
- non-zero Reasoner gradient witness;
- Local gradient witness;
- finite losses / no OOM / complete DCP.

Do not start the 30k formal run before that revalidation closes.
