# PSM-WMA Temporal Local Memory 详细设计补充 v0.3.2

**日期**：2026-09-03  
**状态**：user-directed multi-slot TTT readout clarification / implementation 前必须独立审核  
**适用分支**：根仓 `V2`  
**上游版本**：`docs/build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.1.md`  
**continual-TTT 算法基础**：v0.2 / v0.2.1 的 persistent fast-state、KVB、TBPTT、outer-task-loss 合同继续有效  
**当前 Cosmos 实现基线 / Gitlink**：`cf52f43dc328d4c8eec51923d66835125664dee5`（含已关闭的 `K_local=1` compatibility CPU core）
**历史 v0.3.1 / pre-CPU-core source baseline**：`21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

> 本文件只更新 Local TTT 的 **multi-slot readout / Q-K-V 数量关系 / self-supervised inner loss 与 outer loss 的参数训练职责**。  
> v0.3.1 的 Memory Prefix K/V-only、无 `Q_MEM`、AR 不读 Memory、DM 读 Memory+AR+DM、Memory 无 attention output/MLP 等 Cosmos 接入合同全部保持不变。  
> 若旧文档、旧图或 CPU-core 设计与本文在 `K_local`、TTT internal Q 数量、multi-slot readout 或 Q/K/V 训练职责上冲突，以 v0.3.2 为准。  
> 本文件不授权代码实现、GPU、训练、评测、推理、optimizer/config refreeze、P4/P5 真实操作或 B2-T。

---

# 0. 本次更新结论

Local TTT 不再把架构接口永久冻结为单个 Local token。正式接口改为：

```text
K_local = configurable positive integer
```

每个 control timestep 的 **写入仍只有一组 K/V**，但读取可以有 `K_local` 组 Q：

```text
1 x K_t
1 x V_t
K_local x Q_t^k
```

即：

```text
current causal evidence e_t
        │
        ├─ theta_K ───────────────> K_t
        ├─ theta_V ───────────────> V_t
        └─ theta_Q + slot queries ─> Q_t^1 ... Q_t^Klocal

K_t,V_t
   │
   └─ one KVB self-supervised write
        W_(t-1) -> W_t

W_t + Q_t^1...Q_t^Klocal
   │
   └─ K_local reads
        -> m_t^1 ... m_t^Klocal
```

因此 multi-slot 只增加 **memory read bandwidth**，不重复把同一 evidence 写入 `K_local` 次。

---

# 1. Canonical shapes

沿用当前已冻结/已审核的主维度：

```text
D_e      = 256
D_ttt    = 64        # 当前 CPU-core candidate
D_local  = 32
D_cosmos = 2048      # Edge hidden size
```

对 batch `B`：

```text
e_t                 [B, 256]
K_t                  [B, 64]
V_t                  [B, 32]
Q_t                  [B, K_local, 64]
M_local              [B, K_local, 32]
```

进入 Cosmos 前：

```text
M_local [B,K_local,32]
 -> local_memory2llm (32 -> 2048)
 -> + local_memory_modality_embed
 -> [B,K_local,2048]
 -> Memory Pre-Attention Norm
 -> [B,K_local,2048]
 -> K_MEM / V_MEM
```

`K_local=1` 是合法兼容特例，但不再是架构永久常量。正式首版 `K_local` 数值必须在后续 implementation/source audit 中冻结；建议至少保留 `1 / 4 / 8` 的小规模 token-budget 消融能力，不在本文强行指定 winner。

---

# 2. 一次写入：K/V 不复制 K_local 份

## 2.1 写入投影

每个新增 causal evidence 只产生一组：

```text
K_t = theta_K(e_t)   in R^D_ttt
V_t = theta_V(e_t)   in R^D_local
```

理由：当前 timestep 只有一条 canonical evidence record。K/V 的职责是：

```text
K_t : 这一条新 evidence 的写入索引
V_t : 这一条新 evidence 需要写入 fast memory 的内容
```

因此首版禁止为了输出多个 Local token而机械构造：

```text
K_t^1...K_t^Klocal
V_t^1...V_t^Klocal
```

除非未来有独立证据证明“单次 K/V 写入容量不足”，多写入 K/V 才作为另一个实验变量另开设计 Gate。

---

# 3. Inner self-supervised loss

## 3.1 KVB loss 不包含 Q

inner self-supervised loss 只负责定义 fast-state write：

```text
V_pred,t = f_(W_(t-1))(K_t)
L_inner,t = mean_feature((V_pred,t - V_t)^2)
W_t = W_(t-1) - eta * grad_W L_inner,t
```

数学上：

```text
L_inner,t = || f_(W_(t-1))(K_t) - V_t ||^2
```

其中 `K_t` 和 `V_t` 都由当前已经可观测的 causal evidence `e_t` 自身产生，所以该 loss 在 inference 也成立，不需要：

- GT action；
- future observation；
- memory label；
- future semantic label。

**Q 不参与 `L_inner`。** 这不是遗漏，而是 KVB 的职责分离：K/V 负责写，Q 负责读。

## 3.2 为什么这仍然是自监督

监督 target：

```text
V_t = theta_V(e_t)
```

来自输入自身的 learned representation，而不是数据集额外标签。

与旧 prototype 的：

```text
V_target = e_t[:32]
```

不同，`theta_V` 是由 outer task objective meta-learn 的，不再人为假设混合 latent 前 32 维就是应记内容。

---

# 4. 多 Q 读取：K_local 个 Local token

## 4.1 Query bank

更新完 `W_t` 后，产生 `K_local` 个 query。canonical 形式为：

```text
q_base,t = theta_Q(e_t)                    [B,D_ttt]
r_k      = learned slot embedding          [D_ttt]
Q_t^k    = q_base,t + r_k                  [B,D_ttt]
```

整体：

```text
Q_t [B,K_local,D_ttt]
```

也允许后续实现采用数学等价的 learned query-bank parameterization，但必须保持：

- `K_local` 个 query 可独立分化；
- 共享当前 evidence-conditioned base query；
- slot 参数属于 slow learned parameters；
- 不人为规定每个 slot 的固定语义。

## 4.2 更新后读取

必须使用本 timestep **更新后的** fast state：

```text
m_t^k = f_(W_t)(Q_t^k)
```

得到：

```text
M_local = [m_t^1,...,m_t^Klocal]
M_local [B,K_local,D_local]
```

禁止用更新前 `W_(t-1)` 做正式 readout。

多个 Local token 的目的不是复制记忆，而是给同一个 persistent fast-weight memory 提供多个 read slots，使后续 DM query 能从不同 memory positions 读取不同内容。

---

# 5. Outer loss 如何训练 Q/K/V

Cosmos 原生 task loss仍是唯一 outer objective：

```text
L_outer = L_Cosmos_original
```

不把 `L_inner` 作为普通加权项直接加入：

```text
L_total != L_outer + lambda_ttt * L_inner
```

而是：

```text
W_t = Update(W_(t-1), L_inner)
M_local = Read(W_t, Q_t^1...Q_t^Klocal)
Cosmos(..., M_local) -> L_outer
```

## 5.1 theta_Q / slot queries

Q 不参与 inner loss，因此由 outer loss通过 readout 路径直接训练：

```text
L_outer
 -> DM attention
 -> Memory K/V
 -> M_local
 -> f_(W_t)(Q_t^k)
 -> Q_t^k
 -> theta_Q / r_k
```

所以 outer loss 学到：

> 当前任务下应该从已经积累的 fast memory 中“查询什么”。

## 5.2 theta_K / theta_V

K/V 虽参与 inner loss，但 canonical meta-training 中它们也由 outer loss通过 **differentiable inner update** 学习：

```text
L_outer
 -> M_local
 -> W_t
 -> W_t = W_(t-1) - eta * grad_W L_inner(K_t,V_t)
 -> theta_K / theta_V
```

因此 outer loss 学到：

> 当前经历应该以什么 key/value 形式写入，才能在后续机器人任务中真正有用。

这要求继续遵守 v0.2/v0.2.1 的 segment 内 higher-order/meta-gradient 合同；不得回退为 `create_graph=False + full detach` 的旧 B0/B1 prototype。

---

# 6. 参数职责表

| 对象 | Inner KVB 中角色 | Outer task loss 训练路径 | Train/Inference 状态 |
| --- | --- | --- | --- |
| `theta_K` | 构造 write key | 经 differentiable inner update | slow / inference frozen |
| `theta_V` | 构造 self-supervised write target | 经 differentiable inner update | slow / inference frozen |
| `theta_Q` | 不参与 inner loss；构造 read query | 经 `m_t=f_W(Q_t)` 直接反传 | slow / inference frozen |
| slot query `r_k` | 不参与 inner loss | 经每个 Local slot readout直接反传 | slow / inference frozen |
| learned `W0` | fast state初始化 | 经 recurrent/meta path | slow / inference frozen |
| runtime `W_t` | 被 inner loss逐步更新 | 不是 ordinary optimizer parameter | fast / train+inference更新 |
| Local adapter / Memory Prefix norm | 不参与 inner update | Cosmos outer loss直接训练 | slow / inference frozen |

---

# 7. Multi-slot collapse 与使用性验证

增加多个 Local token 后必须防止所有 slot 学成相同 readout。正式 runtime/training evidence至少记录：

```text
pairwise cosine similarity(m_t^i, m_t^j)
slot output variance
V_t variance / norm
Memory attention mass per slot (diagnostic only)
```

但 **attention weight本身不能作为“模型使用 Memory”的最终证据**。正式归因仍以 intervention 为准：

```text
No Memory
Normal Local
Zero Local
Shuffle Local
Stale/Truncated (when applicable)
```

并观察 native Action/Future output、loss 与 closed-loop metric 的可归因变化。

若 `K_local>1` 但多个 slot长期完全 collapse，应优先检查 query-bank/outer-gradient/readout，而不是直接增加更多 memory tokens。

---

# 8. 与 v0.3.1 Memory Prefix 的接口保持不变

无论 `K_local=1` 还是 `K_local>1`：

```text
M_local [B,K_local,32]
 -> local_memory2llm
 -> + modality embed
 -> [B,K_local,2048]
 -> Memory Pre-Attention Norm
 -> K_MEM / V_MEM only
```

Cosmos attention contract仍是：

```text
Q_AR -> K_AR only
Q_DM -> K_MEM + K_AR + K_DM
Memory Prefix -> no Q_MEM
```

Memory 自身仍然：

- 无 attention output；
- 无 residual update；
- 无 post-attention norm；
- 无 Memory MLP/FFN；
- 无 decoder / RF/FM target。

这里的 TTT internal `Q_t^k` 与 Cosmos attention `Q_MEM` 仍是完全不同的概念：

```text
TTT internal Q_t^k : 存在，用于从 W_t 读取 K_local 个 Local token
Cosmos Q_MEM       : 不存在，Memory Prefix 在 MoT 中只提供 K/V
```

---

# 9. 与当前 CPU-core design 的关系

当前已推进的 `ContinualTTTLocalMemoryCore` CPU design以单个 query/readout为最小算法核，可继续作为：

```text
K_local = 1 compatibility/sanity contract
```

但它不再足以证明正式 multi-slot Local interface 已实现。

后续若进入 production Local runtime wiring，必须新增/扩展：

```text
read_many(state, Q:[B,K_local,D_ttt])
 -> M_local:[B,K_local,D_local]
```

或数学等价的 vectorized read API，并验证：

- `K_local=1` 与原 single-read exact/tolerance-equivalent；
- slot permutation对应输出 permutation；
- 一个 slot 的 query变化不改变其他 slot query本身；
- 多 slot read不改变 fast state数值；
- multi-slot read不重复执行 KVB write；
- outer gradient可达 `theta_Q` 和所有 `r_k`。

若后续 implementation design 直接把 `K_local>1` 纳入 CPU core，则必须重新对 exact implementation SHA 做独立审核，不得沿用单-query批准自动扩权。

---

# 10. 最终概念数据流

```text
new completed causal evidence e_t [B,256]
        │
        ├──────── theta_K ───────> K_t [B,64] ──────┐
        │                                           │
        ├──────── theta_V ───────> V_t [B,32] ──────┤
        │                                           ▼
        │                              L_inner = KVB self-supervised loss
        │                                           │
        │                              W_(t-1) ─────┴────> W_t
        │
        └──────── theta_Q ───────> q_base [B,64]
                                      │
                        ┌─────────────┼─────────────┐
                       +r_1          +r_2         ... +r_K
                        │              │              │
                       Q_1            Q_2            Q_K
                        │              │              │
                        └──────────── W_t ────────────┘
                                      │
                        m_1, m_2, ... , m_K
                                      │
                           [B,K_local,32]
                                      │
                           local_memory2llm
                                      │
                           [B,K_local,2048]
                                      │
                         Memory Pre-Attn Norm
                                      │
                               K_MEM / V_MEM
                                      │
                                      ▼
                              DM queries consume
                                      │
                                      ▼
                           Cosmos original task loss
```

---

# 11. 一句话 implementation contract

```text
Each new causal evidence performs exactly one self-supervised KVB write using one learned K/V pair; after the fast state is updated, K_local evidence-conditioned learned queries read the same persistent W_t into K_local Local tokens. Q does not participate in the inner KVB loss and is trained directly by the unchanged Cosmos outer task loss; K/V are meta-learned by that outer loss through the differentiable inner update. The resulting Local slots enter the v0.3.1 K/V-only Memory Prefix and never become Cosmos attention queries.
```
