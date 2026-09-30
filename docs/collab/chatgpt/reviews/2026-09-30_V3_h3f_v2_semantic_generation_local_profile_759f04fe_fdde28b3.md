# PSM-WMA V3 — H3-F V2-semantic generation + Local-TTT profile

- Date: 2026-09-30
- Formal root: `759f04fe2321dae27ac02d07eb80df0e6bb5d138`
- Formal child/Gitlink: `fdde28b37b25fe29b1dd550b41ec7b37845ba371`
- Status: **H3F_V2_SEMANTIC_GENERATION_LOCAL_IMPLEMENTED_PENDING_REVALIDATION**
- 30k long-run authorization: **NOT YET AUTHORIZED**

## Owner decision

H3-F formal training must match the V2 RoboCasa Local-TTT run in **trainable-module semantics**:

- generation pathway;
- action heads;
- Local-TTT slow parameters.

The owner explicitly decided **not** to align the H3-F dataset/action contract with V2.

## Formal H3-F trainables

Generation/action keys:

- `moe_gen`
- `time_embedder`
- `vae2llm`
- `llm2vae`
- `action2llm`
- `llm2action`
- `action_modality_embed`

V2 Local names are mapped onto the current V3 runtime structure:

- V2 `local_memory_runtime.evidence_encoder.*`
  -> V3 `local_memory_runtime.encoder.*`
- V2 `local_memory_runtime.ttt_core.*`
  -> V3 `local_memory_runtime.core.*`
- `local_memory2llm.*`
- `local_memory_modality_embed`

The resulting H3-F optimizer selector is therefore the V2 semantic equivalent using V3 parameter names.

The reasoner/understanding path is frozen.

## Requires-grad policy

H3-F does not retain the previous custom Reasoner-only pre-filter.

The shared optimizer applies the explicit `keys_to_select` allowlist and freezes every
non-selected parameter as part of optimizer construction. The post-build inventory check then
requires:

- selected names exactly equal generation + V3 Local expected names;
- no non-`_moe_gen` `net.language_model.*` reasoner parameter selected;
- `requires_grad` exactly matches optimizer ownership;
- raw15 Local slow parameter count = 165312.

This stays close to V2 optimizer semantics while preserving a fail-closed V3 inventory.

## Optimizer

- base LR = 5e-5
- optimizer = FusedAdam
- weight_decay = 0.05
- 5x LR multiplier:
  - action2llm
  - action_modality_embed
  - llm2action

## Dataset/action contract — intentionally NOT aligned to V2

H3-F keeps the current V3 authorities:

- source = `robocasa365_official_v30`
- train catalog = 9036 episodes
- manifest =
  `a8cad3f053232b348ea155f15bf79c2c9cf807dedcf39b89e246b17e43f283df`
- camera_set = left_wrist
- base_encoding = raw
- action = raw15
- local_memory_action_dim = 15
- chunk_length = 32 native action chunk
- TTT segment length = 16

No migration to V2 `robocasa365_v3`, ego20D, or a new manifest is part of this profile switch.

The V3 Local parameter count is 165312 rather than the V2 166592 because the Local evidence
action projection consumes raw15 instead of V2 ego20D; the 1280-parameter difference is exactly
5 action dimensions x 256 projection outputs.

## Mesh — intentionally NOT restored to V2

H3-F keeps the already validated H100 topology:

- data_parallel_shard_degree = 8
- data_parallel_replicate_degree = 1
- generation and Local slow parameters use the current dp_shard path.

We do not restore V2's Local default-replicated mesh. H3-D/H3-E grouped state, DCP, optimizer
resume and 8-H100 integration were validated on the current V3 mesh, and changing parameter
ownership would create a second independent systems change with no benefit to the requested
trainable-module alignment.

Profile id:

`v2_semantic_generation+local_v3_raw15`

Mesh id:

`dp_shard8_generation_and_local`

Data id:

`official_v30_raw15`

These identities are included in the H3-F formal config digest.

## Runtime evidence requirements

The FormalObserver no longer requires a Reasoner gradient witness.

Every optimizer iteration must instead prove finite/non-zero witnesses for:

1. generation core (moe_gen / time_embedder / vae2llm / llm2vae);
2. action heads (action2llm / llm2action / action_modality_embed);
3. Local-TTT.

Evidence fields include:

- generation_grad_nonempty_shards
- generation_grad_nonzero_shards
- action_grad_nonempty_shards
- action_grad_nonzero_shards
- local_grad_nonempty_shards
- local_grad_nonzero_shards

The optimizer evidence records:

- selected_generation_tensors / params;
- selected_local_tensors;
- selected_local_params = 165312;
- selected_reasoner_params = 0;
- complete selected_names.

## Gate impact

All readiness evidence from the intermediate Reasoner+Local profile is invalid for formal
authorization after this trainable-profile change.

Re-run on this exact pair:

1. CPU/static;
2. owner-env exact preflight;
3. 10-step 8×H100 readiness;
4. fail-closed matrix.

Do not start the formal 30k run until this new profile closes readiness.
