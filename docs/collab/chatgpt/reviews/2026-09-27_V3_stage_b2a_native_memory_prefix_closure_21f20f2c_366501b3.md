# V3 Stage B2-A Native Memory Prefix CPU/Static closure review

- Date: 2026-09-27
- Gate: `V3-STAGE-B2A-NATIVE-MEMORY-PREFIX-CPU-STATIC`
- formal root: `21f20f2c436e9627a938148afca039da6023d145`
- formal child/Gitlink: `366501b3b4626f30f0739d2e5765139a52f2308f`
- design authority: `d57ef855404cabceed9c4190b13d435a98a30206`
- verdict: `APPROVE_TO_CLOSE_V3_STAGE_B2A_NATIVE_MEMORY_PREFIX_CPU_STATIC`

## Fresh review

Exact formal pair was independently synchronized before review. Child diff from the B1 closure child contains 10 files (+799/-2) limited to the B2-A native Local seam; the B0 core/segment/adapter production files are unchanged.

ChatGPT independent CPU rerun on the exact pair:
- B2-A + B0/B1 suite: **153/153 PASS**
- zero skips
- 30.29 s
- only unrelated torchao deprecation warnings.

ds_pro independently executed the 48-item validation checklist and reported **48/48 PASS, 0 hard-fail**.

## Closed contracts

### Local-Memory trainable inventory

At Edge hidden size 2048, `keys_to_select=["local_memory"]` selects exactly:
- LocalEvidenceEncoder: 29,440
- ContinualTTTLocalMemoryCore: 66,240
- local_memory2llm: 67,584
- local_memory_modality_embed: 2,048
- total: **165,312 parameters**.

All selected parameter names contain `local_memory`; host generation/action/reasoner parameters are frozen. Fast state remains ordinary fp32 tensors and is not an optimizer parameter.

### K/V-only native semantics

Local Memory remains out of the native packed-token geometry:
- no Local Q;
- no native sequence index;
- no mRoPE/RoPE on Local K;
- no Local timestep/noise/loss token;
- no change to sequence_length/sample_lens/split_lens/attn_modes or native CE/MSE indexes.

Per decoder layer, Local hidden uses the generator-side input norm, generator K projection + K norm, and generator V projection. It is prepended to K/V only for the two-way generation-query attention path. Causal/reasoner output is unchanged.

Mixed S0/non-S0 samples are isolated by per-sample Local offsets. All-None Local uses the exact ordinary attention path.

### First outer-gradient witness

The bridge uses non-zero fan-in initialization; modality embedding uses the hidden-size initialization scale.

Independent validation exercised the full:
`visual96 + raw15 -> encoder -> TTT core -> Local32 -> bridge -> outer loss`
chain and observed finite non-zero gradients on all 15 tested Local parameter groups, including all B0 fast-weight initial slow parameters, encoder layers, bridge and modality embedding.

One optimizer step changed all 20 selected Local parameter tensors. Sampled frozen host parameters had no gradient and remained bitwise unchanged.

A detached-context negative control eliminated Local/bridge/TTT gradients, proving the positive gradient witness is discriminative rather than vacuous.

### Fail-closed boundary

Wrong Local K/D, duplicate Local authority, three-way attention, context parallelism, CUDA graphs, multiview, inference/no-grad Local use all fail closed before the unsupported native path executes.

This Gate supports only the formal Edge two-way training route.

## Notes accepted for next Gate

- C2.6: B2-A provides per-sample `None` and preserves mixed presence; deciding that S0 specifically supplies `None` belongs to B2-B, where B0 gathered prefixes are attached to real consumer rows.
- C5.9: the repository positive gradient tests already fail on a detached path; ds additionally supplied an independent explicit detach negative control. No code defect is present.

## Scope boundary

`APPROVE_TO_CLOSE_V3_STAGE_B2A_NATIVE_MEMORY_PREFIX_CPU_STATIC`

This closes only the CPU/static native K/V-prefix seam.

It does not approve:
- B1 producer → B0 transaction → native backward/commit integration;
- trainer integration;
- RTX4090 S1/S2 GPU smoke;
- checkpoint/resume;
- inference;
- H100 formal training;
- task-performance/SR claims.
