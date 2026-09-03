# PSM-WMA Temporal Local Memory 详细设计补充 v0.3.1

**日期**：2026-09-03  
**状态**：user-directed architecture clarification / implementation 前必须独立审核  
**适用分支**：根仓 `V2`  
**上游版本**：`docs/build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.md`  
**continual-TTT 算法 authority**：`v0.2` / `v0.2.1` 与已审核 CPU-core 设计继续有效  
**当前 Cosmos 实现基线 / Gitlink**：`21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

> 本文件是 v0.3 的定向澄清版。它不改变 continual-TTT 的 KVB、persistent fast-state、TBPTT、outer-loss 等算法合同，只进一步冻结 **Memory Prefix 在 Cosmos attention 中是 K/V-only、无 query、无 attention output、无 post-attention MLP 的只读条件上下文**。  
> 若 v0.3、旧图或旧 runtime 说明与本文在 `Q_MEM`、Memory attention output、Memory MLP、Memory hidden-state update、Local-to-DM 归属上存在冲突，以 v0.3.1 为准。  
> 本文件不授权代码实现、GPU、训练、评测、推理、optimizer/config refreeze、P4/P5 真实操作或 B2-T。

---

# 0. 最终概念结构

Cosmos 侧逻辑布局仍为：

```text
[ Memory Prefix ] [ Native AR subsequence ] [ Native DM subsequence ]
```

Memory Prefix 顺序固定为：

```text
[ Global Memory (future) ] [ Local Memory (current) ]
```

当前只实现 Local；未来 Global 加入时放在 Local 前面。

三域职责冻结为：

```text
Memory Prefix : clean read-only conditioning context; K/V only
AR            : native causal query/key/value stream
DM            : native generator query/key/value stream; may read Memory + AR + DM
```

---

# 1. Memory Prefix 不产生 Transformer 输出

这是 v0.3.1 相比所有旧图示最重要的澄清。

Memory Prefix 只执行：

```text
Global/Local memory token
        ↓
Memory modality adapter / embed
        ↓
Memory Pre-Attention Norm
        ↓
K_MEM / V_MEM
        ↓
供 DM query 读取
```

到 `K_MEM / V_MEM` 为止，Memory branch 在 Cosmos block 内结束。

明确不存在：

```text
Q_MEM
Memory self-attention query row
Memory attention output
Memory residual attention update
Memory post-attention LayerNorm
Memory post-attention MLP / FFN
updated Memory hidden states
Memory decoder
Memory RF/FM prediction target
Memory prediction loss
```

因此 Memory 不是第三条 Transformer token-processing tower，而是一个外部 clean memory bank 在每层 attention 中提供只读 K/V context。

---

# 2. Attention contract

## 2.1 Memory

```text
M_prefix
  ↓
MemoryPreAttentionNorm
  ↓
K_MEM = K_proj_mem(...)
V_MEM = V_proj_mem(...)
```

Memory **不生成 Cosmos-attention 的 Q**。

注意：Local TTT 内部仍保留自己的：

```text
Q_t / K_t / V_t
```

其中 `Q_t` 用于从更新后的 fast model 读取 `m_t`；它与 Cosmos attention 的 `Q_MEM` 完全不是一回事。

## 2.2 AR

AR 完全保持原生：

```text
Attn_AR = Attn(Q_AR ; K_AR, V_AR)
```

并继续使用 native causal mask。

硬约束：

```text
Q_AR -> K_MEM : DENY
Q_AR -> K_DM  : DENY
```

Memory present/absent/content 不得改变 Reasoner/AR 的原生 causal chain。

## 2.3 DM / Generator

DM query 的 key/value context 扩展为：

```text
K_allowed = [K_MEM, K_AR, K_DM]
V_allowed = [V_MEM, V_AR, V_DM]

Attn_DM = Attn(Q_DM ; K_allowed, V_allowed)
```

因此 attention matrix 只有两类 query row：

| Query \ Key | Memory Prefix | AR | DM |
| --- | --- | --- | --- |
| **AR** | **DENY** | **native causal** | **DENY** |
| **DM** | **ALLOW** | **ALLOW** | **ALLOW / native full** |

**不再存在 `Q_MEM` 行。**

---

# 3. Normalization contract

Memory 虽然不产生 attention output，但在生成 `K_MEM / V_MEM` 前仍需要 pre-attention normalization：

```text
[Global, Local]
      ↓
Memory modality adapter / embed
      ↓
Memory Pre-Attention Norm
      ↓
K_MEM / V_MEM
```

首版原则：

- Global/Local 进入 Cosmos hidden size 后组成统一 Memory Prefix；
- 首版共用一个 Memory Prefix pre-attention norm 语义，不为 Global/Local 各自额外引入独立 post-adapter norm tower；
- norm family、epsilon、参数共享粒度必须由后续 exact Cosmos source audit 基于真实 block API 冻结；
- 不允许因为 Memory prefix 的存在改变 AR/DM 原生 norm 参数或行为；
- Memory **没有 post-attention norm**，因为它没有 attention output。

---

# 4. Local TTT 到 Cosmos 的最终接口

Local branch 本身继续按照 continual-TTT 设计：

```text
new completed causal evidence e_t
        ↓
LocalEvidenceEncoder
        ↓
theta_Q / theta_K / theta_V       # TTT internal projections
        ↓
KVB self-supervised inner update
W_(t-1) -> W_t
        ↓
m_t = f_(W_t)(Q_t)
        ↓
Local token [B,1,D_local]
```

Local token 的 Cosmos 归属必须写成：

```text
m_t
 -> local_memory2llm
 -> + local_memory_modality_embed
 -> Memory Prefix
 -> Memory Pre-Attention Norm
 -> K_MEM / V_MEM
 -> DM queries consume
```

禁止再写成：

```text
m_t -> DM subsequence ordinary token
```

或：

```text
m_t -> Generator query stream
```

Local TTT 的持续状态仍是 backbone 外的 `W_t`；Cosmos block 不负责“更新 memory token”。

---

# 5. Global Memory 的未来接口

Global 尚未实现，但 Cosmos 侧接口已经冻结：

```text
Global Spatial Memory
 -> global adapter / modality embed
 -> g_t token(s)
 -> prepend before Local within Memory Prefix
```

随后统一：

```text
[Global tokens, Local tokens]
 -> Memory Pre-Attention Norm
 -> K_MEM / V_MEM
```

Global 与 Local 可以拥有不同的内部算法、更新频率、token budget；但 Cosmos attention 侧都只是 Memory Prefix 的 K/V provider。

未来若要让 Local 显式读取 Global、让 AR/Reasoner 读取 Memory、或让 Memory 产生自己的 Transformer output，都必须另开独立设计 Gate。

---

# 6. Position / mRoPE 与顺序

“Memory 在 AR 前面”只定义逻辑布局，不得简单通过原生 token prepend 改变 native position authority。

继续冻结：

- Memory token 不推进 AR position/mRoPE cursor；
- Memory token 不推进 native DM Vision/Action temporal/spatial cursor；
- Memory present/absent 时，native AR/DM position ids 必须保持与 No-Memory baseline 对齐；
- Memory 使用独立的 position/type semantics；
- Global 位于 Local 前面不应重新定义 AR/DM mask。

---

# 7. Gradient / loss 语义

Memory 没有自己的 Transformer output，不等于训练时没有梯度。

训练期 outer gradient 仍可通过 DM 对 Memory K/V 的读取回传：

```text
Cosmos native task loss
 -> DM attention output
 -> K_MEM / V_MEM
 -> Memory Pre-Attention Norm
 -> local_memory2llm / modality embed
 -> Local TTT read/update/QKV/W0/encoder
```

因此：

- Cosmos 原有 Vision/Action task loss保持不变；
- Memory 无独立 RF/FM target；
- TTT KVB inner loss只用于 fast-state transition，不直接以 `lambda * L_inner` 加到 outer loss；
- continual-TTT segment 内 meta-gradient / TBPTT contract继续以 v0.2/v0.2.1 为准。

---

# 8. Current implementation gap

当前 Gitlink `21d064f...` 的 Local wiring 仍是旧实现：

```text
local_memory2llm(local) + local_memory_modality_embed
 -> scatter into packed_sequence
 -> local sequence indexes included in GEN indexes
```

因此当前实现仍把 Local 当普通 GEN/DM token，而不是 v0.3.1 的 K/V-only Memory Prefix。

正式 runtime wiring 至少需要解决：

1. Local 从 ordinary GEN query stream 中移除；
2. attention builder/metadata/dispatch 支持额外 Memory K/V context；
3. Memory 不生成 query row；
4. Memory 没有 post-attention output / MLP path；
5. 增加 Memory pre-attention normalization；
6. AR 原生 causal path和position/mRoPE exact-preserving；
7. DM query能够读取 `[K_MEM,K_AR,K_DM]`；
8. No-Memory fast path保持旧行为不回归。

旧 B1 runtime smoke 只能证明 superseded GEN-token wiring 曾工作，不能证明 v0.3.1 已实现。

---

# 9. 必须新增/修正的验证

后续 runtime/attention implementation Gate 至少证明：

- `Q_MEM` 结构上不存在/不执行；
- Memory token 不出现在 attention query stream；
- Memory 不经过 post-attention residual/MLP；
- attention matrix 实际只有 AR/DM 两类 query authority；
- `Q_AR` 只能读 `K_AR`；
- `Q_DM` 能读 `K_MEM + K_AR + K_DM`；
- Memory present/absent/zero/shuffle 不改变 AR hidden/output；
- 修改 DM noisy/future token不改变给定相同历史下的 Local state / Local token / Memory K/V；
- native AR/DM position/mRoPE 不因 Memory Prefix 发生偏移；
- Local TTT outer-gradient path通过 K/V context可达；
- Global absent 时当前 Local path成立，未来插入 Global 时无需重写 AR/DM mask。

---

# 10. 最终架构合同

```text
GLOBAL (future) ─┐
                 ├─> Memory adapters / modality embeds
LOCAL TTT ───────┘
                      │
                      ▼
               [Global, Local]
                Memory Prefix
                      │
             Memory Pre-Attn Norm
                      │
                 K_MEM / V_MEM
                      │
                      └────────────────────────────────┐
                                                       │
AR native tokens                                      │        DM native tokens
      │                                                │              │
AR pre-attn norm                                      │       DM pre-attn norm
      │                                                │              │
Q_AR/K_AR/V_AR                                        │       Q_DM/K_DM/V_DM
      │                                                │              │
      ▼                                                │              ▼
AR causal attention                                   │       DM full attention
(K_AR only)                                           │ (K_MEM + K_AR + K_DM)
      │                                                │              │
 native AR residual / MLP                             │       native DM residual / MLP
      │                                                │              │
   Reasoner                                            │          Generator

Memory itself has:
  NO Q_MEM
  NO attention output
  NO residual update
  NO post-attention norm
  NO MLP/FFN
  NO decoder/loss target
```

---

# 11. 一句话 implementation contract

```text
Global(future)+Local(TTT) form a clean Memory Prefix before AR in logical layout; after Memory pre-attention normalization they provide K/V only and terminate as a Transformer-side branch. AR remains native causal and cannot read Memory; DM queries may attend Memory+AR+DM. Local TTT keeps its own internal Q/K/V and persistent fast state outside the backbone, while Cosmos native task loss and AR/DM processing stacks remain unchanged.
```
