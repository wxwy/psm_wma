# ChatGPT Independent Re-Review — R09-B TTT v0.3.2 Memory Prefix Runtime Contract Remediation @ 73d592a

**Date:** 2026-09-03  
**Task/Gate:** `G0-R09-B-TTT-V032-MEMORY-PREFIX-RUNTIME-CONTRACT-DESIGN`

## Review identity

- exact remediation/design SHA under verdict: `73d592a90c93897ca6f9be681801b87617e0a7a9`
- request/ledger state observed during review: `817b2f360b91809e4bb685255edd0ee44223d821`
- child/Gitlink read-only baseline: `1d90361aeb21db53129ac27ddcaa1285b258fbbc`
- prior blocked design SHA: `5cb43d29b4c7806f7c427859bbc96a4c4442911f`
- prior ChatGPT review: `bbc09189814dfbc974a373db14c3e3d184b78ccd`

The required literal `git fetch origin V2` was attempted for this review and failed because the reviewer shell cannot resolve `github.com`. Freshness, target ancestry/Gitlink, governance/status, request ledger and pinned child source were therefore re-read through the connected GitHub interface. The exact target root resolves `cosmos-framework` to `1d90361...`.

## Verdict

**APPROVE_TO_IMPLEMENT_R09_B_TTT_V032_MEMORY_PREFIX_CPU_CONTRACT**

No new design blocker was found. The v0.2 remediation closes both HIGH findings from the v0.1 review and is implementable against the pinned child within the newly frozen seven-file boundary.

## Closure of prior findings

### HIGH-1 — CLOSED: Local is now removed from native geometry before packing metadata is constructed

**Remediation:** `docs/build/PSM-WMA_R09_B_TTT_v032_memory_prefix_runtime_contract_design_v0.2_2026-09-03.md:38-89,125-144`

The design now makes `sequence_packing` the owner of the separation. Local is carried as an out-of-band `tokens_by_sample` payload and the Prefix route must not call the legacy `pack_local_memory_tokens()` span packer. Local contributes no native `sample_len`, `combined_split_len`, `sequence_length`, `attn_modes`, position IDs, UND/GEN indexes, EOV decision, loss indexes or prepared sequence-pack metadata. Mixed batches preserve sample ownership with `None` for absent rows.

This directly resolves the pinned-source contradiction identified in v0.1: the current child otherwise calls `pack_local_memory_tokens()` before `Cosmos3VFMNetwork` and therefore changes sequence geometry before model-side scatter. The implementation boundary now correctly includes `packers.py` and `sequence.py` so the separation happens at the actual owner rather than by later depacking/index surgery.

C4-P01/P02/P03 are sufficient acceptance fixtures: same native inputs with/without Prefix must have exact native geometry/metadata parity, mixed ownership must remain exact, and the legacy Local span packer must be unreachable from the Prefix route.

### HIGH-2 — CLOSED: K_MEM now matches generator-full key normalization while remaining positionless

**Remediation:** `docs/build/PSM-WMA_R09_B_TTT_v032_memory_prefix_runtime_contract_design_v0.2_2026-09-03.md:92-122,157-164`

The Memory key contract is now:

```text
mem_h   = memory_input_layernorm(context.hidden)
k_mem_0 = k_proj_moe_gen(mem_h)
k_mem   = k_norm_moe_gen(k_mem_0.view(N_mem, num_kv_heads, head_dim))
v_mem   = v_proj_moe_gen(mem_h).view(N_mem, num_kv_heads, head_dim)
```

`K_MEM` does not receive native position IDs or RoPE and still has no query/output/residual/MLP path. This is compatible with the pinned Edge path, where generator Q/K use `q_norm_moe_gen` / `k_norm_moe_gen` and generator-full AR keys use the existing normalized-key path when required. The remediation therefore avoids mixing an unnormalized Memory key with normalized native keys in the same DM softmax.

C4-K01/K02 explicitly require a non-Identity normalization fixture and a reference one-softmax using normalized `K_MEM`, so an accidental K-norm bypass is detectable.

## Accepted contract

The following are accepted for C4:

- independent read-only `MemoryPrefixContext`, distinct from native `MemoryValue/MemoryState` KV cache;
- model-level `[B,K_local,32] -> local_memory2llm -> [B,K_local,2048]` Prefix construction;
- per-block `memory_input_layernorm`, reused generator K/V projections, `k_norm_moe_gen` on K only, no Memory RoPE;
- no `Q_MEM`, Memory attention output, output projection, residual, post-attention norm or MLP;
- AR causal path remains Memory-blind and unchanged;
- DM performs one joint dense varlen softmax over `[K_MEM,K_AR,K_DM]` / `[V_MEM,V_AR,V_DM]`, using the current generator-full native key policy;
- `MemoryPrefixContext is None` takes the exact legacy dispatch path;
- Prefix-present three-way/Flex/multi-control/CP-Ulysses/native KV-cache/CUDA-graph/replicated-I/O combinations fail closed before the attention kernel;
- zero-initialized adapter with Prefix present is not claimed to be function-preserving;
- the exact child implementation boundary is seven files: `packers.py`, `sequence.py`, `memory_prefix.py`, `cosmos3_vfm_network.py`, `unified_mot.py`, `attention.py`, and `memory_prefix_test.py`.

## Authorized next step only

After all required reviewers approve this exact root/Gitlink pair, C4 may implement and validate the frozen **synthetic CPU Memory Prefix contract only** in the seven listed child files, including C4-P01..P03, C4-K01..K02, C4-A01 and C4-F01 plus the retained v0.1 C4-01..08 requirements.

Still prohibited:

- C5 causal-history / persistent fast-state runtime integration;
- changes to `local_evidence.py`, `utils/memory.py`, config, optimizer, checkpoint, trainer, inference or parallelization;
- GPU/CUDA/torchrun, training, evaluation or inference;
- real model/data/latent-cache/checkpoint runtime access;
- P4/P5 real operations, B2-T and LIBERO4IN1 training.

Any new remediation/design SHA or child implementation SHA requires a fresh same-SHA review.
