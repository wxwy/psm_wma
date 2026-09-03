# PSM-WMA Temporal Local Memory 详细设计补充 v0.3

**日期**：2026-09-03  
**状态**：user-directed architecture integration update / implementation 前必须独立审核  
**适用分支**：根仓 `V2`  
**当前 Cosmos 实现基线 / Gitlink**：`21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`  
**上游项目设计**：`docs/build/PSM-WMA_02_detailed_design_v2.1_frozen.md`  
**算法设计前版**：`docs/build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.2.md`  
**算法整改前版**：`docs/build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.2.1.md`  
**CPU core 设计**：`docs/build/PSM-WMA_R09_B_TTT_CPU_algorithm_implementation_design_v0.1_2026-09-03.md`  

> 本文件在 **不回滚 v0.2 / v0.2.1 continual-TTT 算法合同** 的前提下，进一步冻结 Local/Global Memory 与 Cosmos3 shared multimodal attention 的接入语义。  
> **若旧文档与本文在 Memory Prefix 排列、Memory/AR/DM attention domain、Memory pre-attention normalization、Memory query、position/mRoPE 或 Local-as-GEN-token 语义上冲突，以 v0.3 为准。**  
> 本文件不授权代码实现、GPU、训练、评测、推理、optimizer/config refreeze、P4/P5 真实操作或 B2-T。当前正在推进的 backbone-independent continual-TTT CPU functional core 设计不因本文失效；本文只约束后续 runtime/attention wiring。

---

# 0. 执行摘要

v0.3 将 Cosmos3 输入逻辑明确拆成三个域：

```text
[ Memory Prefix ] [ Native AR subsequence ] [ Native DM subsequence ]
```

其中 Memory Prefix 的逻辑顺序固定为：

```text
[ Global Memory (future) ] [ Local Memory (current) ]
```

当前只实现 Local；Global 仅预留同类接口，后续加入时位于 Local 之前。

Memory Prefix **不是 AR subsequence 的一部分，也不是 DM subsequence 的普通 full-attention token**。它是独立的 clean conditioning context：

```text
Memory Prefix  -> only K_MEM / V_MEM
AR             -> native Q_AR / K_AR / V_AR
DM             -> native Q_DM / K_DM / V_DM
```

attention 规则冻结为：

```text
Q_AR -> K_AR only                  # 原生 causal AR，完全不读 Memory/DM
Q_DM -> K_MEM + K_AR + K_DM        # Generator 可读 Memory + AR + DM
Memory Prefix -> no Q_MEM          # 只提供 K/V，不作为 query stream
```

因此本文核心目标是：

> **把 Memory 放在语义上的最前方，同时不把它并入 AR 因果链；Memory 只作为 Generator 可读取的 clean K/V prefix，从而保住原生 AR 行为并避免 DM/future 信息反向污染 Memory。**

---

# 1. 不变的 continual-TTT 算法合同

以下内容完全继承 v0.2/v0.2.1 与已审核 CPU-core 设计，本文件不重新设计：

1. decision `t` 只写最新已完成的 causal evidence `e_(t-1)`；
2. runtime logical evidence write length = 1；
3. fast state 跨 control timestep / TBPTT segment carry，仅 episode reset；
4. `tbptt_steps=16` 只截断 graph，不清空 fast state 数值；
5. TTT 内部保留 learned `Q/K/V`：`K/V` 用于 KVB write，`Q` 用于更新后 read；
6. 每个 valid timestep 做一次 KVB inner update；
7. learned W0 / QKV / encoder / adapter 为 slow parameters；runtime W_t 为 fast state；
8. canonical training 保留 segment 内 higher-order/meta-gradient；
9. inference 只更新 W_t，不更新 slow weights；
10. Cosmos 原生 Vision/Action task loss 继续作为 outer objective，不直接加 `lambda * L_inner`。

特别说明：

```text
TTT internal Q_t  !=  Cosmos attention Q_MEM
```

前者必须保留；后者在 v0.3 **明确不存在**。

---

# 2. 三域架构与逻辑排列

## 2.1 Logical sequence order

概念/文档/机器可读 layout 统一按：

```text
Global Memory -> Local Memory -> AR -> DM
```

当前没有 Global 时：

```text
Local Memory -> AR -> DM
```

这个顺序表达从长期到近期、当前上下文再到生成目标的层级：

```text
long-term spatial/world state
        -> recent temporal state
        -> current/native clean context
        -> future/action generation
```

## 2.2 Memory Prefix 不属于 AR

即使 Memory 在 layout 上位于 AR 左侧/前方，也不得：

- 纳入 AR causal token chain；
- 改变 AR 的 token count / causal order；
- 改变 AR 原生 position / mRoPE ids；
- 让 `Q_AR` 读取 `K_MEM`；
- 让 Reasoner 的 native decoding 依赖 Memory，除非未来另开独立设计 Gate。

因此：

```text
AR_with_memory_present == native_AR_path
```

在相同 native AR 输入/权重/随机条件下，Memory 的 present/absent/content 不得改变 AR hidden/output。

## 2.3 Memory Prefix 不属于普通 DM token stream

Memory 也不得继续作为普通 GEN/DM token参与对称 full attention。尤其禁止：

```text
Q_MEM -> K_DM
```

否则训练时 noisy future/action target-derived information 可污染 memory hidden，再被后续 DM 读取，形成泄漏回路。

---

# 3. Memory Prefix projection 与 normalization

## 3.1 Local 输出

Local TTT branch 继续输出：

```text
m_local [B, K_local, D_local]
```

首版继承：

```text
D_local = 32
K_local = 1   # 当前接口；未来 token budget 可独立实验
```

然后：

```text
m_local
 -> local_memory2llm
 -> + local_memory_modality_embed
 -> hidden-size Local memory token(s)
```

## 3.2 Global 输出（未来）

Global 后续采用独立 encoder/adapter，不复用 Local TTT backend：

```text
Global Spatial State
 -> Global Encoder / Readout
 -> global_memory2llm
 -> + global_memory_modality_embed
 -> hidden-size Global memory token(s)
```

Global 的具体算法不在本文冻结；这里只冻结其进入 Memory Prefix 时位于 Local 之前。

## 3.3 Shared Memory Prefix normalization

Global/Local 投影到 Cosmos hidden size 后，先形成：

```text
M_prefix = concat([M_global, M_local], dim=sequence)
```

当前无 Global：

```text
M_prefix = M_local
```

进入 attention K/V projection 前必须有明确 normalization：

```text
M_prefix
 -> MemoryPreAttentionNorm
 -> K_MEM / V_MEM
```

v0.3 冻结以下语义：

- Global 与 Local **不各自增加一套独立 norm**；首版共用一个 Memory Prefix normalization；
- norm 发生在 modality adapter/embed 之后、attention K/V 之前；
- norm family 应与 Cosmos native block 使用的 normalization family 对齐；
- 为避免影响原生 AR/DM norm 参数，首版优先采用 **独立的 Memory Prefix norm 参数/模块**，identity/function-preserving 初始化；
- exact class、epsilon、dtype、是否每 block 独立或共享一次，由后续 source audit 基于真实 Cosmos block API 冻结；不得凭图直接硬编码 `nn.LayerNorm`。

注意：本文中的“LayerNorm”是概念级 pre-attention normalization 名称；实现必须以当前 Cosmos 实际 norm 类型为准。

---

# 4. Attention contract

## 4.1 Memory 只提供 K/V

Memory Prefix 不生成 Cosmos attention query：

```text
Q_MEM = none
K_MEM = theta_K_attn(Norm(M_prefix))
V_MEM = theta_V_attn(Norm(M_prefix))
```

Memory Prefix 不需要：

- self-attention output；
- residual attention update；
- post-attention Memory MLP；
- Memory decoder；
- Memory FM/RF loss。

它在每个需要 memory context 的 Generator attention block 中只作为 clean K/V context 被读取。

## 4.2 AR attention 完全保持原生

```text
Attn_AR = Attn(Q_AR ; K_AR, V_AR)
```

并继续使用 Cosmos 原生 causal mask。

硬约束：

```text
Q_AR -> K_MEM : MASKED / not in key set
Q_AR -> K_DM  : MASKED / native behavior
```

Memory 的 presence/content 不得推进 AR mRoPE/position cursor，也不得改变 AR causal matrix。

## 4.3 DM / Generator attention

Generator query 的 key/value 集合扩展为：

```text
K_allowed = [K_MEM, K_AR, K_DM]
V_allowed = [V_MEM, V_AR, V_DM]
```

即：

```text
Attn_DM = Attn(Q_DM ; [K_MEM,K_AR,K_DM], [V_MEM,V_AR,V_DM])
```

在 native DM 原本允许的范围内仍保持 full attention；v0.3 只新增 Memory Prefix K/V，不改变 Vision/Audio/Action 的原生生成语义。

## 4.4 Attention matrix

规范矩阵不再给 Memory 分配 query row：

| Query \ Key | Memory Prefix | AR | DM |
| --- | --- | --- | --- |
| **AR** | **DENY** | **native causal** | **DENY** |
| **DM** | **ALLOW** | **ALLOW** | **ALLOW / native full** |

Memory Prefix 只有 key/value role，不存在 `Q_MEM` 行。

---

# 5. Position / mRoPE contract

“Memory 放最前面”不得通过简单 prepend 造成 native position shift。

冻结要求：

1. Memory Prefix 使用独立 memory position/type semantics；
2. Memory token 不推进 AR position/mRoPE cursor；
3. Memory token 不推进 native Vision/Action temporal/spatial cursor；
4. Memory absent 时 native AR/DM position ids 与 No-Memory baseline exact-equal；
5. Memory present 时 native AR/DM position ids 仍必须与同一 native sample 的 No-Memory baseline exact-equal；
6. Memory 的 exact position representation（constant/independent slot/zeroed mRoPE/other）由 source audit 选择，但不得伪装成 AR vision/text 或 DM spatial patch。

因此逻辑 layout 的：

```text
[MEM][AR][DM]
```

不等价于把 MEM 计入 AR/DM 原生位置计数。

---

# 6. Local TTT branch 与 Memory Prefix 的接口

Local branch 数据流保持：

```text
new completed causal evidence e_t
 -> LocalEvidenceEncoder
 -> theta_Q / theta_K / theta_V              # TTT internal projections
 -> KVB self-supervised fast-weight update
 -> W_(t-1) -> W_t
 -> f_(W_t)(Q_t)
 -> local readout m_t [D_local]
 -> local_memory2llm + modality embed
 -> Memory Prefix token
 -> MemoryPreAttentionNorm
 -> Cosmos attention K_MEM / V_MEM
 -> DM queries consume memory
```

TTT internal `Q_t` 只用于读取 fast model；不会成为 Cosmos `Q_MEM`。

Outer task gradient 在训练时必须仍可沿：

```text
Cosmos native loss
 -> DM attention output
 -> K_MEM / V_MEM
 -> Memory Prefix token
 -> local_memory2llm
 -> TTT read/update/QKV/W0/encoder   # 在允许的 TBPTT graph 内
```

回传，从而 meta-learn“怎样写/读 Local Memory 才有利于任务”。

---

# 7. Current implementation gap（Gitlink 21d064f）

当前实现仍是旧 R07/B1 wiring：

```text
local_memory2llm(local) + local_memory_modality_embed
 -> scatter into packed_sequence
```

且 Local `sequence_indexes` 被加入 `all_gen_indexes`，因此当前 Local 实际上仍被路由成 GEN stream token。当前 `_encode_local_memory` 也没有独立 Memory Prefix pre-attention norm。

这与 v0.3 正式接入语义有三个关键差距：

1. **Local-as-GEN-token 必须取消**：Local 不再进入普通 DM query stream；
2. **需要独立 Memory K/V context**：attention builder/metadata/dispatch 必须能够把 Memory 作为额外 K/V 提供给 DM，而不给 AR；
3. **需要 Memory pre-attention normalization**：在 adapter/embed 后、Memory K/V projection 前明确实现。

因此现有 B1 runtime smoke 继续只证明旧 Local GEN-token path 曾可运行，不证明 v0.3 Memory Prefix 已实现。

---

# 8. “Backbone unchanged”的准确边界

v0.3 所谓“不改 Cosmos3 backbone”准确含义是：

**保持不变**：

- Transformer block 数量；
- native AR tower/MLP/causal behavior；
- native DM tower/MLP/full-attention behavior；
- Vision/Audio/Action encoder/head；
- 原生 action/future target 与 loss；
- Reasoner decoding contract。

**允许的最小扩展**：

- 新增 Memory Prefix modality/context；
- Memory adapter/embed；
- Memory pre-attention norm；
- shared attention 的额外 Memory K/V input；
- asymmetric key-set/mask metadata。

因此它不是“零代码修改 backbone”，而是：

> **不改变 native layer stack / AR-DM computation topology，仅扩展 attention context contract，使 Generator 多读一个 clean Memory K/V prefix。**

---

# 9. Global Memory 的未来接入规则

Global 尚未实现。未来加入时不允许重新改变 AR/DM 主结构，只做：

```text
Global branch -> Global tokens
             -> concat before Local tokens
             -> same Memory Prefix norm
             -> same K_MEM / V_MEM context
```

规范顺序：

```text
K_MEM = [K_GLOBAL, K_LOCAL]
V_MEM = [V_GLOBAL, V_LOCAL]
```

Global/Local 算法、更新频率、token 数可不同，但在 Cosmos 侧共享同一个 Memory Prefix attention contract。

若未来要让 Local 显式读取 Global、或 Reasoner/AR 读取 Memory，必须另开设计 Gate；v0.3 当前不允许。

---

# 10. Loss / training / inference 边界

## 10.1 Loss

保持：

```text
L_outer = Cosmos original native task loss
```

Memory 无独立 RF/FM target，无 Memory decoder loss；TTT KVB inner loss只用于 fast-state transition。

## 10.2 Training

- DM task loss可以通过 attention K/V 路径训练 Memory slow parameters；
- AR output/AR loss（若当前 recipe 有）不得经 Memory 改变；
- TTT fast state按 v0.2.1 chronological/TBPTT contract持续 carry；
- Memory Prefix 本身不产生 query/output branch，因此没有额外 Memory attention/MLP loss。

## 10.3 Inference

- Local TTT 先在 Cosmos inference-mode 外完成 W-only inner update并生成 detached Local token；
- Memory Prefix token经 adapter/norm转为 clean K/V context；
- Cosmos slow weights不更新；
- AR不读 Memory；
- DM读取 Memory K/V；
- episode reset才重置 Local fast state到 learned W0。

---

# 11. 必须新增的验证合同

后续 implementation/runtime Gate 至少新增以下验证。

## 11.1 AR invariance

在相同 native input/seed/weights 下：

```text
Memory absent
Memory present-normal
Memory present-zero
Memory present-shuffle
```

AR token ids / position ids / mRoPE / causal mask 必须相同；AR hidden/output应保持 exact 或由 kernel contract冻结的严格 tolerance 内等价。若 Memory 改变 Reasoner 输出，直接 FAIL。

## 11.2 Memory no-query contract

必须证明：

```text
Q_MEM does not exist / is never executed
Memory tokens are excluded from query stream
Memory tokens are excluded from post-attention Memory MLP path
```

不得只靠 mask 后“结果碰巧接近零”代替结构断言。

## 11.3 DM reads Memory

训练后/非零 adapter 后，Normal vs Zero/Shuffle Local Memory 必须能对 native Action/Future output产生非零、可归因 sensitivity；No-Memory baseline保持 parity。

## 11.4 No future leakage

改变同一 timestep 的 noisy/future DM target-derived token内容，不得改变：

- Local TTT state；
- Local token；
- Memory Prefix K/V（在给定相同 historical evidence 时）。

## 11.5 Position parity

Memory present/absent 时，所有 native AR/DM token 的 position/mRoPE authority必须逐项对比并证明不被 prefix insertion偏移。

## 11.6 Global-ready ordering

即使当前 `K_global=0`，schema/layout 必须允许未来：

```text
[Global][Local]
```

而无需重新定义 AR/DM mask。

---

# 12. 推荐 source-audit 问题

进入 implementation 前，必须从 exact Gitlink 回答：

1. Cosmos 每层真实 pre-attention norm class/参数归属是什么；
2. two-way/three-way attention builder是否能表达“extra K/V only, no Q”的第三 context；
3. `build_packed_sequence` / `SplitInfo` / dispatch_attention` 最小扩展点在哪；
4. AR/DM Q/K/V 当前如何形成，是否能不改变 native AR split而附加 Memory K/V；
5. mRoPE/position ids由哪一层生成，怎样让 Memory 不推进 native cursor；
6. FSDP/AC/compile 对独立 Memory norm和 extra K/V 的参数/graph约束；
7. CP/Ulysses 下 Memory K/V应该复制、分片还是随 DM key sequence sharding；
8. no-memory fast path能否做到旧路径 exact；
9. current `local_memory.sequence_indexes` / `all_gen_indexes` 哪些代码必须删除或改义；
10. Global slot如何以 `0 token`/absent schema预留而不污染当前 Local 实验。

source audit只能记录事实与候选 patch，不得直接实现。

---

# 13. 与当前 Gate 的关系

当前 branch 已在推进 backbone-independent `ContinualTTTLocalMemoryCore` CPU algorithm/gradient design。v0.3 不推翻其：

- KVB math；
- Q/K/V internal projections；
- learned W0；
- 2-layer fast MLP；
- per-sample update；
- higher-order gradient；
- TBPTT state-carry semantics。

因此该 CPU core Gate 可继续按既有批准流程推进。

但是以下后续工作必须以 v0.3 为新 authority重新审核：

```text
Local -> Cosmos runtime wiring
attention mask / attention metadata
Memory norm
position/mRoPE integration
optimizer inventory of new Memory-prefix params
resolved config refreeze
GPU runtime smoke
matched training / inference / B2-T
```

旧的“Local 是 GEN/DM ordinary token”相关 runtime/P3/P4/P5 algorithm binding不得授权新的正式训练。

---

# 14. 最终架构合同

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
                      ├────────────────────────────┐
                      │                            │
AR native tokens      │                       DM native tokens
      │               │                            │
AR pre-attn norm      │                       DM pre-attn norm
      │               │                            │
Q_AR/K_AR/V_AR        │                      Q_DM/K_DM/V_DM
      │               │                            │
      ▼               │                            ▼
AR causal attention   │                   DM full attention
(K_AR only)           │              (K_MEM + K_AR + K_DM)
      │               │                            │
 native AR MLP        │                       native DM MLP
      │               │                            │
   Reasoner           │                        Generator
                      │
            Memory itself has NO Q,
            NO attention output,
            NO post-attention MLP.
```

---

# 15. 一句话 implementation contract

```text
Global(future) + Local(TTT) are ordered as a clean Memory Prefix before AR in the logical layout,
but are not part of the AR causal chain: after a shared Memory pre-attention norm they provide K/V only;
AR queries remain native causal and cannot read Memory, while DM queries may attend Memory + AR + DM;
Local TTT keeps its own internal Q/K/V KVB update and persistent fast state, and Cosmos native task loss/backbone stack remain unchanged.
```
