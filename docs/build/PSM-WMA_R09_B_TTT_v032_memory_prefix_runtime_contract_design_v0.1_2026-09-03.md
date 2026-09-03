# R09-B TTT v0.3.2 Memory Prefix runtime contract design v0.1

**日期**：2026-09-03  
**状态**：待三方对同一根仓 SHA 审核；审核前不得修改子模块  
**任务**：`G0-R09-B-TTT-V032-MEMORY-PREFIX-RUNTIME-CONTRACT-DESIGN`  
**设计 authority**：

- `docs/build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.1.md`
- `docs/build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.2.md`
- `docs/build/PSM-WMA_R09_B_TTT_v032_memory_prefix_source_abi_audit_v0.1_2026-09-03.md`

**冻结的子模块只读基线 / Gitlink**：
`cosmos-framework@1d90361aeb21db53129ac27ddcaa1285b258fbbc`。

本文件把 C3 的 source/ABI 审计收敛为 C4 的 CPU-only implementation
contract。它只冻结设计、最小文件边界和测试判据；不修改 child，不执行
torch/GPU/训练，也不授权 C5 及以后 Gate。

## 1. 不变的算法和注意力合同

每个已完成的因果 evidence 只进行一次 K/V KVB write，之后以 `K_local`
个 TTT internal Q 从更新后的 persistent `W_t` 读取：

```text
M_local: [B, K_local, 32]
  -> local_memory2llm(32 -> 2048) + local_memory_modality_embed
  -> Memory Prefix hidden: [B, K_local, 2048]
  -> per-block Memory pre-attention RMSNorm
  -> K_MEM / V_MEM only
```

`K_local` 是正整数、可配置；本 Gate 的 CPU contract 至少覆盖 `1` 和 `4`。
TTT internal `Q_t^k` 不是 Cosmos attention query：不存在 `Q_MEM`。原生
Cosmos outer loss、AR/DM native query、native AR/DM hidden/loss/index/
mRoPE cursor 都不因 Prefix 而改变。

```text
Q_AR -> [K_AR, V_AR]                       # 原路径，逐位 parity 目标
Q_DM -> [K_MEM, K_AR, K_DM]/[V_MEM,V_AR,V_DM]  # 一次联合 softmax
```

Memory 不产生 attention output，不经 `o_proj_moe_gen`、residual、
post-attention norm 或 MLP/FFN。

## 2. 现有 seam 与排除项

在 pinned child 中：

- `cosmos_framework/model/generator/mot/cosmos3_vfm_network.py:941-962`
  当前 `_encode_local_memory()` 将 `local_memory2llm` 后的 token scatter 到
  native packed GEN stream；C4 必须改为仅构造独立 Prefix payload，绝不能
  scatter。
- `cosmos_framework/data/generator/sequence_packing/sequence.py:545-588`
  当前 Local packer 能接收 `[K_local,D_local]`，但会创建普通 GEN span 和
  text-style mRoPE；该路径不再用于 Memory Prefix。
- `cosmos_framework/model/generator/mot/unified_mot.py:629-711` 现有
  `PackedAttentionMoT` 同时投影 native UND/GEN 的 Q/K/V 并对二者施加
  native RoPE；Memory K/V 必须在这条 native pack 之外生成。
- `cosmos_framework/model/generator/mot/attention.py:179-317` 的 dense
  `two_way_attention()` 已把 AR causal pass 和 DM full pass 分开；只扩展
  后者的 KV。
- `cosmos_framework/model/generator/utils/memory.py:1-93` 的
  `MemoryState/MemoryValue` 是 native KV-cache 的读回/写回契约。Prefix
  不能借用它：Local Prefix 不产生 `KVToStore`，不回写 native cache，也不把
  fast state `W_t` 伪装成 KV cache。

因此 `memory_value` 这个既有参数、inference text-KV cache、AR generation
cache、context-parallel cache 均不属于 C4 的 Prefix ABI。

## 3. 精确 ownership 与数据 ABI

### 3.1 独立 `MemoryPrefixContext`

后续 child implementation 必须定义一个与 `MemoryValue` 不同名、只读的
轻量 context（建议 `MemoryPrefixContext`），只承载本 forward 的 Prefix
hidden 和样本边界：

```text
hidden              Tensor [N_mem, H]      # H=2048；按 batch sample 顺序平铺
sample_offsets      LongTensor [B + 1]     # 0 开始、单调非降、末项=N_mem
present             BoolTensor [B]         # present[i] <=> offsets[i+1] > offsets[i]
```

约束：

1. `hidden.shape[0] == sample_offsets[-1]`，`hidden.shape[1] == config.hidden_size`；
   offsets 与 hidden 同 device，offset dtype 必须为 `torch.long`。
2. present sample 的长度是该 sample 的 `K_local`，首版只接受同 batch
   的所有 present sample 使用同一 `K_local >= 1`；absent sample 的长度为 0。
3. context 为 `None` 表示本 batch 无 Prefix。不得以零长度伪 token 代替
   `None`，不得添加 native query/index/position/loss/state 字段。
4. Global 尚未实现；若 future Gate 需要 Global，顺序固定为 `[Global,Local]`，
   另行冻结，不在 C4 偷渡。

Model-level owner 是 `Cosmos3VFMNetwork`：它将 Local `[B,K_local,32]`
投影和加 modality embed 后生成 context。`PackedSequence` 保持 native
`[AR,DM]`，其 `sample_lens`、`split_lens`、GEN indexes、mRoPE IDs 和 loss
indexes 不包含 Memory。

### 3.2 每层 owner

`UnifiedMoTDecoderLayer` 每层新增独立的：

```text
memory_input_layernorm = layer_types.rms_norm(
    config.hidden_size, eps=config.rms_norm_eps
)
```

它只处理 `context.hidden`。随后由同层 `PackedAttentionMoT` **复用已有**
generator `k_proj_moe_gen` 和 `v_proj_moe_gen`：

```text
K_MEM = k_proj_moe_gen(memory_input_layernorm(hidden))
V_MEM = v_proj_moe_gen(memory_input_layernorm(hidden))
```

不新增独立 K/V projection；也不调用 `q_proj_moe_gen`、native QK norm、
`_apply_rotary_pos_emb` 或任何 output projection。这样新增 slow 参数仅是每层
`memory_input_layernorm`；adapter 与 modality embed 仍由 model owner 持有。
config/optimizer/checkpoint selector、旧 checkpoint 迁移和初始化 policy 不属于 C4。

### 3.3 position 与 RoPE

`K_MEM` 不拥有 native mRoPE position id，且 **不施加 RoPE**。它是无位置的
per-sample KV prefix；AR/DM 的 Q/K 继续以现有 native position embeddings
和 RoPE 原样产生。这是有意与普通 Local GEN packer 的 text-style mRoPE 行为
隔离，而不是遗漏 position。

## 4. two-way dense attention ABI

仅当 `MemoryPrefixContext is not None` 时启用 C4 分支；`None` 必须调用现有
无 Prefix dispatch 分支，不能只要求数值近似。

对每个 sample `i`，令 `m_i = sample_offsets[i+1]-sample_offsets[i]`，其 DM
query 的 one-call KV layout 是：

```text
Q_i      = Q_DM_i
K_i      = concat(K_MEM_i, K_AR_i, K_DM_i)  # length m_i + ar_i + dm_i
V_i      = concat(V_MEM_i, V_AR_i, V_DM_i)
```

实现必须构造新的 cumulative KV offsets：

```text
prefix_kv_offsets[0] = 0
prefix_kv_offsets[i+1] = prefix_kv_offsets[i] + m_i + native_sample_len_i
```

DM 只调用一次 varlen dense attention，不能将 `MEM` 和 native attention 分开
softmax 后相加。`Q` offsets 是原 `full_q_offsets`；Memory 不加入 native
`sample_lens`、full query 数、causal offsets 或 `from_mode_splits` 的 output。
AR pass 保持 `two_way_attention()` 当前 causal q/k/v 调用与 offsets 完全不变。

## 5. 首版 fail-closed 范围

context 为 `None` 时任何 backend 继续原行为。context present 时 C4 只支持：

```text
joint_attn_implementation == "two_way"
flex_block_mask is None
attention_mask.control_stream_token_ranges is None
pack["is_sharded"] is False
memory_value is None
```

其他组合必须在进入 attention kernel 前抛出含具体 feature 名称的 `ValueError`：
three-way、FlexAttention、multi-control、context parallel/Ulysses、native KV-cache
memory、CUDA graph/replicated attention I/O。C4 不允许 fallback 成把 Prefix
scatter 为 GEN token，也不允许忽略 Prefix 静默运行。

## 6. warm-start 语义

`local_memory2llm` 现有零初始化不是 Prefix-present parity 的证明：即使
`K_MEM/V_MEM` 为零，新 key 的 softmax 分母也会改变 DM 输出。C4 唯一承诺：

```text
MemoryPrefixContext is None  => exact existing path parity
```

Prefix present 的 zero adapter case 只要求 shape/dtype/device 正确、输出有限、
无跨 sample 泄漏；不得标注为 function-preserving。若要 gate/logit prior 或
warm-start preservation，须新开设计 Gate。

## 7. C4 允许的最小 child 文件边界

在本文件获三方同 SHA `APPROVE_TO_IMPLEMENT_R09_B_TTT_V032_MEMORY_PREFIX_CPU_CONTRACT`
后，才允许在 child 的下列边界内工作：

1. `cosmos_framework/model/generator/mot/memory_prefix.py`：新增 context、
   validation、per-sample concat/offset helper；禁止修改 `utils/memory.py`。
2. `cosmos_framework/model/generator/mot/cosmos3_vfm_network.py`：从 Local
   payload 产出 context，停止 Local GEN scatter。
3. `cosmos_framework/model/generator/mot/unified_mot.py`：每层 norm、K/V
   projection 与 context 透传。
4. `cosmos_framework/model/generator/mot/attention.py`：two-way dense DM
   one-call prefix KV 分支与 fail-closed guards。
5. `cosmos_framework/model/generator/mot/memory_prefix_test.py`：synthetic CPU
   定向测试。

不得修改 packer、runtime chronology、`local_evidence.py`、config、optimizer、
checkpoint、trainer、inference、parallelization 文件；若实现发现必须触及它们，
立即停止并新开 design Gate。

## 8. CPU 验收合同

仅 synthetic CPU tensors，禁止模型/数据/checkpoint runtime。每项均必须在进入
flash/flex kernel 前可复现：

| ID | 断言 |
| --- | --- |
| C4-01 | `None` 走原 dispatch path；输出和原 two-way reference exact equal。 |
| C4-02 | `K_local=1/4` 的 context shape、offsets、dtype/device 正确；坏 shape/offset/present 组合 fail before attention。 |
| C4-03 | AR output 对任意 Memory hidden perturbation exact unchanged。 |
| C4-04 | DM output 对非零 Memory perturbation 可变化，且与逐 sample reference 的单一联合 softmax 一致。 |
| C4-05 | two sample（含 one absent row）不发生 cross-sample KV leakage；permutation 保持 sample ownership。 |
| C4-06 | Memory 不进入 native full/causal count、native mRoPE/index/loss metadata；没有 Q_MEM/output/residual/MLP 调用。 |
| C4-07 | three-way、Flex、multi-control、sharded/CP、native `MemoryValue`、CUDA graph/replicated flags 在 Prefix present 时 fail closed。 |
| C4-08 | zero adapter Prefix present 有限但不要求 parity；`None` parity 不受影响。 |

验证命令和实际产物路径在 implementation Gate 冻结后再写入 runbook；本设计阶段不运行项目代码。

## 9. 后续 Gate 与本轮 verdict

本轮只请求：

```text
APPROVE_TO_IMPLEMENT_R09_B_TTT_V032_MEMORY_PREFIX_CPU_CONTRACT
```

或 `REQUEST_CHANGES`（必须包含 severity、`file:line`、对 exact root SHA 和
Gitlink 的绑定）。批准仅允许第 7 节的 child CPU implementation 与第 8 节测试。
它不批准 C5 causal history/fast-state runtime、C6 config/optimizer/checkpoint、
C7 closure、GPU smoke、inference、P4/P5 或 LIBERO4IN1 训练。
