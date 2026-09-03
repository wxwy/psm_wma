# ChatGPT Independent Review — R09-B TTT v0.3.2 Memory Prefix Runtime Contract Design @ 5cb43d2

**Date:** 2026-09-03  
**Task/Gate:** `G0-R09-B-TTT-V032-MEMORY-PREFIX-RUNTIME-CONTRACT-DESIGN`

## Review identity

- exact design SHA under verdict: `5cb43d29b4c7806f7c427859bbc96a4c4442911f`
- request/ledger SHA: `0bc961c165a91d6aab65ce17fff6d6a41d5184c8`
- child/Gitlink read-only baseline: `1d90361aeb21db53129ac27ddcaa1285b258fbbc`
- C3 remediation/source authority: `e53fffe22444516ff04523bfccff0d66fccdc75c`

The required literal `git fetch origin V2` was attempted for this review and failed because the reviewer shell cannot resolve `github.com`. Freshness, exact target ancestry/Gitlink, current governance/status, request ledger and pinned child source were therefore re-read through the connected GitHub interface. The target root resolves exactly to child `1d90361...`.

## Verdict

**REQUEST_CHANGES**

The architectural direction remains valid, but the frozen C4 implementation contract is not yet internally implementable against the pinned child. Two HIGH blockers must be resolved in a docs/design-only remediation before child work starts.

## Findings

### HIGH-1 — The contract requires Memory to be absent from the native `[AR,DM]` pack, but simultaneously forbids changing the source that currently inserts Local into that pack

**Design:** `docs/build/PSM-WMA_R09_B_TTT_v032_memory_prefix_runtime_contract_design_v0.1_2026-09-03.md:95-98,191-203`

The design freezes `PackedSequence` as native `[AR,DM]` and explicitly says its `sample_lens`, `split_lens`, GEN indexes, mRoPE IDs and loss indexes do not contain Memory. It then authorizes only five child files and explicitly forbids packer changes.

**Pinned-source contradiction:**

- `cosmos_framework/data/generator/sequence_packing/packers.py:245-259` currently calls `pack_local_memory_tokens()` whenever `has_local_memory`, then increments `sample_len` by `local_split_len`.
- `cosmos_framework/data/generator/sequence_packing/packers.py:536-550` includes `local_split_len` in `combined_split_len` and passes the Local-expanded `sample_len` into `finish_sample()`.
- `cosmos_framework/data/generator/sequence_packing/sequence.py:545-588` creates Local text-style mRoPE IDs and appends a Local span.
- `cosmos_framework/data/generator/sequence_packing/sequence.py:636-652` assigns global sequence indexes, appends those position IDs and advances `current_seq_index` for every appended modality span.

Therefore, by the time `Cosmos3VFMNetwork` receives `PackedSequence`, Local has already changed the native sequence geometry. Merely changing `_encode_local_memory()` from scatter to context construction cannot make the native pack `[AR,DM]`: Local rows and their offsets/index/position contributions already exist. With the current frozen five-file boundary, C4-06 cannot be satisfied without either leaving phantom Local rows in native GEN or performing an unspecified index/metadata surgery inside the network.

**Root cause:** the C4 ownership boundary was frozen one layer too late. C3 correctly identified the old Local GEN packer behavior, but C4 does not freeze how Local is removed from native packing before attention metadata is built.

**Acceptance criteria:** freeze one exact implementable route before child changes:

1. Preferred: authorize the minimal sequence-packing file(s) needed to carry Local payload out-of-band while **not** appending Local sequence rows, `sample_lens`, `split_lens`, native position IDs or GEN indexes; update the C4 file boundary and CPU contracts accordingly; or
2. If packer changes are intentionally avoided, fully specify a model-side depack/remap transform before `build_packed_sequence()`, including remapping every affected text/vision/action/sound index, sample/split length, position ID, prepared metadata invalidation/rebuild, and exact no-Memory parity tests.

In either route, C4-06 must directly prove that a present Prefix does not alter native `[AR,DM]` sequence metadata.

### HIGH-2 — `K_MEM` is frozen to bypass the generator K QK-normalization used by the same DM joint softmax

**Design:** `docs/build/PSM-WMA_R09_B_TTT_v032_memory_prefix_runtime_contract_design_v0.1_2026-09-03.md:102-121`

The design freezes:

```text
K_MEM = k_proj_moe_gen(memory_input_layernorm(hidden))
V_MEM = v_proj_moe_gen(memory_input_layernorm(hidden))
```

and explicitly says Memory does not call native QK norm.

**Pinned-source semantics:**

- `cosmos_framework/model/generator/mot/unified_mot.py:663-664` applies `q_norm_moe_gen` and `k_norm_moe_gen` to native generator Q/K before RoPE.
- `cosmos_framework/model/generator/mot/unified_mot.py:682-695` explicitly introduces a separate normalized UND-key path for GEN attention because, on the Nemotron/Edge configuration (`qk_norm_for_diffusion=True`, `qk_norm_for_text=False`), raw UND K scale can dominate the joint attention.
- `cosmos_framework/model/generator/mot/attention.py:208-213` selects `packed_key_states_normalized` for the generator full-attention path when supplied.
- `cosmos_framework/configs/base/experiment/sft/models/edge_model_config.py:44,160-170` uses `two_way`, sets `qk_norm_for_text=False`, and enables `use_und_k_norm_for_gen`; `qk_norm_for_diffusion` remains the MoT wrapper default `True` (`unified_mot.py:238-261`).

The proposed DM softmax would therefore mix normalized `Q_DM`, normalized generator/AR keys, and an unnormalized `K_MEM`. A hidden-space `memory_input_layernorm` is not equivalent to the existing head-dimension `k_norm_moe_gen` after projection. This recreates exactly the scale mismatch the current Edge source takes special care to prevent.

**Root cause:** the design correctly separates Memory from native RoPE/query/output semantics, but conflates “no native RoPE / no Q_MEM” with “no generator K normalization.” These are independent operations.

**Acceptance criteria:** freeze the Memory K path so it matches generator full-attention key scale while still remaining positionless and K/V-only. The minimal contract is:

```text
mem_h = memory_input_layernorm(hidden)
k_mem = k_proj_moe_gen(mem_h).view(N_mem, num_kv_heads, head_dim)
k_mem = k_norm_moe_gen(k_mem)   # Identity automatically when diffusion QK norm is disabled
v_mem = v_proj_moe_gen(mem_h).view(N_mem, num_kv_heads, head_dim)
# no RoPE on k_mem; no q_proj/q_norm/Q_MEM/o_proj/residual/MLP for Memory
```

The DM joint-softmax contract must also state that native AR keys use the current generator-full normalized-key path when present. Add a CPU fixture/reference proving the one-softmax result uses normalized `K_MEM`, current normalized `K_AR`, and normalized `K_DM`, and that bypassing `k_norm_moe_gen` is rejected or demonstrably not the implemented path.

## Accepted portions

The following are accepted and need not be redesigned unless the remediation changes their assumptions:

- a separate read-only `MemoryPrefixContext`, not `MemoryValue/MemoryState`;
- no `Q_MEM`, Memory attention output, residual, post-attention path or MLP;
- AR causal pass remains Memory-blind;
- DM performs one joint softmax over Memory + native AR + native DM keys/values;
- `K_MEM` may intentionally have no RoPE/native position ID;
- `MemoryPrefixContext is None` must take the exact legacy path;
- Prefix-present unsupported three-way/Flex/multi-control/CP/native-KV-cache/CUDA-graph/replicated-I/O combinations fail closed;
- Prefix-present zero adapter is not claimed to be function-preserving;
- C4 remains synthetic CPU only and does not authorize C5+ runtime, config/checkpoint, GPU, inference or training.

## Required next step

Submit a new **docs/status-only remediation SHA** with the same child baseline (unless the design explicitly changes the source baseline) that closes HIGH-1 and HIGH-2. Do not begin child implementation on `5cb43d2`.

Still prohibited:

- any C4 child implementation under this rejected design SHA;
- C5 causal-history / persistent fast-state runtime integration;
- config/optimizer/checkpoint selector/refreeze/migration;
- GPU/CUDA/torchrun, model/data/cache/checkpoint execution;
- training/evaluation/inference;
- real P4/P5 operations and B2-T.

A new remediation/design SHA requires a fresh same-SHA review.