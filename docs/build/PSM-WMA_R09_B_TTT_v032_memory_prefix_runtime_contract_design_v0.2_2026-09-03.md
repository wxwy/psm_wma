# R09-B TTT v0.3.2 Memory Prefix runtime contract design v0.2

**日期**：2026-09-03
**状态**：C4 v0.1 三方审核后的 docs-only remediation，待对新 SHA 独立审核
**任务**：`G0-R09-B-TTT-V032-MEMORY-PREFIX-RUNTIME-CONTRACT-DESIGN`
**supersedes**：`...runtime_contract_design_v0.1_2026-09-03.md` 中与 native
packing owner、Memory K normalization 和 C4 文件边界冲突的内容。

**authority**：v0.3.1、v0.3.2、C3 source/ABI audit 均保持有效。
**冻结 child baseline/Gitlink**：
`cosmos-framework@1d90361aeb21db53129ac27ddcaa1285b258fbbc`。

本版本只关闭 v0.1 的两项 HIGH 设计缺口。它不修改 child，不授权项目代码、
GPU、训练、推理或 C5+。

## 1. v0.1 审核结论与本次覆盖

对 v0.1 target `5cb43d2`：Kimi/MM 认可总体架构；ChatGPT 的 HIGH-1/HIGH-2
被采纳为本版必须关闭的实现性约束：

1. Local 必须在 **native packing 前** 从 `[AR,DM]` geometry 分离，不能等
   `_encode_local_memory()` scatter 时才移除；
2. `K_MEM` 必须经过 generator head-dimension `k_norm_moe_gen`，但不能获得
   native position 或 RoPE。

除上述覆盖外，以下不变：每 timestep 仅一次 K/V TTT write、`K_local` post-update
reads、`[B,K_local,32] -> [B,K_local,2048]`、独立只读 Prefix context、无
`Q_MEM`、AR memory-blind、DM 的 `[MEM,AR,DM]` 一次联合 softmax、`None` exact
legacy path、Prefix-present unsupported mode fail-closed，以及不把 zero-adapter
称作 Prefix-present function parity。

## 2. native packing 前的 out-of-band Local payload

### 2.1 exact owner 和 schema

`sequence_packing` 是 Local/native geometry 的唯一 owner。后续 C4 实现必须在
`sequence.py` 定义并在 `PackedSequence` 保存独立 payload（建议
`LocalMemoryPrefixData`，名称可有等价变体但字段/语义不变）：

```text
tokens_by_sample: list[Tensor | None], len == B
  present i: Tensor [K_local, D_local]
  absent  i: None
```

它不是 `ModalityData`：没有 `sequence_indexes`、span、`token_shapes`、position
IDs、condition mask、noisy indexes、timestep 或 loss index。`PackedSequence.to_cuda()`
必须仅搬运其中 present payload tensor，不能借此创建 native span/index/metadata；
它只保存 caller 已提供的 clean Local payload 及 sample ownership。

`MemoryPrefixContext` 仍在 model side 产生：将每个 present payload 依 batch
顺序投影 `32 -> 2048`、加 `local_memory_modality_embed`，再平铺为：

```text
hidden         [N_mem, H]
sample_offsets [B+1] long
present        [B] bool
```

其中 `H=config.hidden_size`；`sample_offsets` 从 0 开始、单调非降、末项
`N_mem`，且 `present[i] == (offset[i+1] > offset[i])`。本 batch 的所有 present
rows 必须有相同正 `K_local`；不满足即在 projector 前 `ValueError`。

### 2.2 packer 的精确改动

以下是 C4 允许的唯一 packer 路径替换，直接关闭 native phantom rows：

1. `packers.py` 仍按 `SequencePlan.has_local_memory` 消费
   `gen_data_clean.x0_tokens_local_memory[idx_local_memory]` 并递增该索引，但仅
   调用 `seq_builder.pack_local_memory_prefix_payload(...)` 保存
   `tokens_by_sample`；**不得**调用 `pack_local_memory_tokens()`。
2. 该 helper 只验证 rank-2 `[K_local,D_local]`、`K_local>0` 并 append payload；
   不调用 `_append_modality_span()`，不追加 position IDs，不改变
   `current_seq_index` 或 mRoPE temporal cursor。
3. `local_split_len` 永远为零；Local 不得计入 `sample_len`、
   `combined_split_len`、`finish_sample()` 的 split、`sequence_length`、native
   `attn_modes`、`packed_und_token_indexes`、`packed_gen_token_indexes`、loss
   indexes 或 prepared sequence-pack metadata。
4. Local 是 KV-only condition，不是 native generation modality：它必须从
   `has_generation_for_sample` 与 `has_any_generation` 的 native structural
   判定中移除，且不得仅因 Local 添加 EOV token。现有 vision/action/sound/text
   的 Native no-Memory geometry 因而逐项不变。
5. payload list 必须含 B 个 entries；没有 Local 的 sample append `None`。此
   规则避免 mixed batch 的 index shift，且不允许零长度 token 替代 absence。

现有 `pack_local_memory_tokens()` 可在 C4 后保留为被正式路径禁止调用的 legacy
helper；它的 GEN span/text-style mRoPE 行为不再代表 Local Memory Prefix。若
implementation 无法使它 unreachable，必须 fail closed 而非留兼容 fallback。

### 2.3 native metadata parity

对相同 native text/vision/action/sound 输入，Prefix-present pack 与 No-Memory
pack 的以下字段必须 exact equal：`sample_lens`、`split_lens`、`attn_modes`、
`sequence_length`、`position_ids`、text indexes、所有 native modality indexes、
所有 CE/MSE loss indexes、native prepared metadata 与 `build_packed_sequence()`
输入。两者唯一允许不同的是 out-of-band Local payload/随后产生的 Prefix context。

这不是仅 model-side output parity；必须在 attention metadata 建立前由 CPU
fixture直接验证。

## 3. 每层 K/V path：K normalization 与 position 解耦

每层保持独立：

```text
mem_h   = block.memory_input_layernorm(context.hidden)
k_mem_0 = self_attn.k_proj_moe_gen(mem_h)
k_mem   = self_attn.k_norm_moe_gen(
              k_mem_0.view(N_mem, num_kv_heads, head_dim)
          )
v_mem   = self_attn.v_proj_moe_gen(mem_h).view(N_mem, num_kv_heads, head_dim)
```

`k_norm_moe_gen` 在 diffusion QK norm 关闭时是既有 `Identity`，因此以上代码
无需 feature-specific special case。`K_MEM` **不得**传给 `_apply_rotary_pos_emb`，
没有 native mRoPE position；也不调用 `q_proj_moe_gen`、`q_norm_moe_gen`、
`o_proj_moe_gen`、residual、post-attention norm 或 MLP。

DM one-softmax 使用的 native key path必须是当前 generator-full key policy：

```text
K_native_for_DM = get_all_seq(packed_key_states_normalized)
                  if packed_key_states_normalized is not None
                  else get_all_seq(packed_key_states)
K_DM component  = k_norm_moe_gen + native RoPE
K_AR component  = current k_norm_und_for_gen + native RoPE when supplied,
                  otherwise current native AR key path
K_MEM component = k_norm_moe_gen, no RoPE
```

因此“不使用 RoPE”绝不等于“绕过 generator key normalization”。

## 4. attention layout 和 fail-closed 范围

对 sample `i`，DM query 与 K/V 是：

```text
Q_i = Q_DM_i
K_i = concat(K_MEM_i, K_AR_for_DM_i, K_DM_i)
V_i = concat(V_MEM_i, V_AR_i, V_DM_i)
```

用一次 dense varlen attention 和 new `prefix_kv_offsets`；AR causal call、AR
offsets、AR Q/K/V 和 outputs 不读、不接触、不依赖 Prefix。Memory 不加入 native
query/output splits。`MemoryPrefixContext is None` 必须直接调用原 dispatch。

Prefix present 时仅支持 `two_way`、non-Flex、non-multi-control、unsharded、
`memory_value is None` 且无 CUDA-graph/replicated I/O。three-way、Flex、
multi-control、CP/Ulysses、native KV cache、CUDA graph、replicated I/O 必须在
attention kernel 前带 feature 名的 `ValueError`，不得 fallback 为 Local GEN
token 或忽略 Prefix。

## 5. 更新后的最小 child 文件边界

仅在本版获三方同 SHA
`APPROVE_TO_IMPLEMENT_R09_B_TTT_V032_MEMORY_PREFIX_CPU_CONTRACT` 后，允许：

1. `cosmos_framework/data/generator/sequence_packing/packers.py`：out-of-band
   Local payload 的消费和 native length/EOV 排除；
2. `cosmos_framework/data/generator/sequence_packing/sequence.py`：payload
   schema、builder/finalize 与 `PackedSequence` 字段；
3. `cosmos_framework/model/generator/mot/memory_prefix.py`：context validation、
   projection helper 与 per-sample concat/offset helper；
4. `cosmos_framework/model/generator/mot/cosmos3_vfm_network.py`：由 payload
   产生 context，删除 Local native scatter；
5. `cosmos_framework/model/generator/mot/unified_mot.py`：per-block norm、
   normalized no-RoPE K_MEM/V_MEM 与 context 透传；
6. `cosmos_framework/model/generator/mot/attention.py`：two-way DM one-call
   prefix KV 和 guards；
7. `cosmos_framework/model/generator/mot/memory_prefix_test.py`：synthetic CPU
   tests。

禁止 `utils/memory.py`、chronology/`local_evidence.py`、config、optimizer、
checkpoint、trainer、inference、parallelization 和其他 packer 文件。若实现发现
必须突破这七文件，停止并新开 design Gate。

## 6. 更新后的 C4 CPU contracts

除 v0.1 C4-01~08 外，以下是强制、不得只用 mock metadata 的细化：

| ID | 断言 |
| --- | --- |
| C4-P01 | Prefix-present packing 对同 native input 的 AR/DM geometry 与 No-Memory pack exact equal，唯 out-of-band payload 不同。 |
| C4-P02 | mixed batch 的 `tokens_by_sample`/`present`/offsets 精确保留 ownership；absent row 不造零 token，且无 cross-sample leakage。 |
| C4-P03 | legacy `pack_local_memory_tokens()` 不在 Prefix route 被调用；Prefix 无 native span/index/mRoPE/loss metadata。 |
| C4-K01 | `K_MEM` 经 `k_norm_moe_gen`、不经 RoPE；CPU reference 的 one-softmax 使用 normalized K_MEM 与当前 native generator-full K path。 |
| C4-K02 | 构造一个非 Identity `k_norm_moe_gen` fixture，证明 bypass normalization 会与 reference 不同且被测试捕获。 |
| C4-A01 | AR outputs 对 Memory hidden perturbation exact unchanged；DM output 与 per-sample normalized-K joint-softmax reference 一致。 |
| C4-F01 | `None` 走原 dispatch exact path；Prefix present 的 unsupported modes 在 kernel 前 fail closed。 |

zero adapter present 只要求 finite；不要求 no-Memory numerical parity。所有测试均为
synthetic CPU，不访问 checkpoint、latent cache、模型或数据。

## 7. 审核请求

请求新的同 SHA verdict：

```text
APPROVE_TO_IMPLEMENT_R09_B_TTT_V032_MEMORY_PREFIX_CPU_CONTRACT
```

或 `REQUEST_CHANGES`（severity + exact `file:line`）。批准仅允许第 5 节七文件
synthetic CPU C4 implementation 和第 6 节测试；仍禁止 C5 fast-state/chronology、
config/optimizer/checkpoint、GPU/训练/评测/推理、P4/P5 与 LIBERO4IN1 training。
