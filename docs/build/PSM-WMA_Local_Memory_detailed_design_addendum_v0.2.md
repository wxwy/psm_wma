# PSM-WMA Temporal Local Memory 详细设计补充 v0.2

**日期**：2026-09-03  
**状态**：user-directed design correction / implementation 前必须独立审核  
**适用分支**：根仓 `V2`  
**当前实现基线**：`wxwy/cosmos-framework@21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`  
**上游冻结文档**：`docs/build/PSM-WMA_02_detailed_design_v2.1_frozen.md`  
**前版补充**：`docs/build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.1.md`  
**R08 补充**：`docs/build/PSM-WMA_R08_Causal_Local_Evidence_Stream_Implementation_Supplement_v0.1.md`  
**参考工作**：RoboTTT, arXiv:2607.15275, https://research.nvidia.com/labs/gear/robottt/

> 本文件是对 R09-B TTT Local Memory 算法语义的正式纠偏说明。它不修改 `PSM-WMA_02_detailed_design_v2.1_frozen.md` 的项目级冻结边界，也不重开 R07 Local clean modality / R08 causal evidence 的已关闭合同。  
> **若旧文档与本文件在 R09-B 的 fast-weight state lifecycle、inner objective、gradient path、history horizon、optimizer membership、train/inference 语义上冲突，以本文件为准。**  
> 本文件本身不授权代码实现、GPU、训练、评测或 B2-T；任何实现仍必须走项目现有独立审核 Gate。

---

# 0. 本次设计纠偏的结论

R09-B 的正式研究对象不再是：

```text
H=16 sliding history
→ 每次 outer forward 从 W=0 重新 replay
→ 每 4 valid steps 用 MSE(W @ e, e[:32]) 更新一次
→ detached Local token
```

而是：

```text
每个 control timestep 只消费 1 个新增 causal evidence
                    │
                    ▼
              persistent fast state
              W_(t-1) → W_t
                    │
                    ▼
               Local token
                    │
                    ▼
              Cosmos3 原生主干
```

其中：

1. **Runtime history input length = 1**：每次只写入新增的一步 causal evidence，不再重复 replay 最近 H 步；
2. **W 每个有效 timestep 更新一次并跨 timestep 持续 carry**；
3. **16 只作为首版 TBPTT segment length，不是 memory horizon**；
4. **inner objective 改为 RoboTTT-style TTT-KVB**，删除 `evidence[:32]` 人为 target；
5. **Cosmos 原有 Vision/Action rectified-flow / flow-matching loss 保持不变，作为 outer task loss**；
6. **训练时 outer loss 必须能够 meta-learn TTT slow parameters / update dynamics**；
7. **推理时只更新 fast state W，不更新 Cosmos / encoder / QKV 等 slow parameters**；
8. **不把 TTT 插入 Cosmos shared MoT/backbone**，TTT 只存在于独立 Local Memory 模态支路。

一句话：

> **R09-B 从“16-step TTT-like window compressor”改为“RoboTTT-style continual fast-weight Local Memory branch”。**

---

# 1. 不变的项目边界

以下合同继续有效，不因 v0.2 改变：

- Cosmos3 backbone / shared MoT topology 不改；
- Local / Global Memory 继续是独立 optional clean modality；
- Local 不作为 RF/FM prediction target；
- Local 无 decoder、无 Local `mse_loss_indexes`、无 Local noise timestep；
- Local 通过既有 `local_memory2llm + local_memory_modality_embed` 进入 Cosmos packed sequence；
- native Future Vision / Action path 可以 attend Local；
- Policy/WAM 的原生 Vision/Action target、loss 定义和基础数据语义不因 TTT 改变；
- R08 已冻结的 past-only / executed-action / episode-boundary / source-index causality 继续有效；
- 不引入 Global Memory、Agent、Planner、RL 或 shared-MoT TTT 作为本次变量。

因此本次改动只发生在：

```text
causal Local evidence stream
        ↓
Temporal Local Memory backend
        ↓
Local token
```

这一段。

---

# 2. 时间与因果语义

## 2.1 Local 继续只写“已完成的历史”

沿用 v0.1/R08 的严格因果合同。对当前 policy decision anchor `t`：

```text
... obs_(t-2) --executed action--> obs_(t-1) | obs_t | future
              newest completed history          current policy obs
```

本次决策使用的 Local state 只能由 `<= t-1` 的历史构造：

```text
M_local(t) = F(history <= t-1)
```

因此 streaming 后，每个 decision step 新进入 Local branch 的不是“重新取最近 16 步”，而是**恰好一个新增的、已经完成 causality closure 的 evidence record**：

```text
e_new(t) := e_(t-1)
```

第一步没有历史时：

```text
local_present = false
```

不得为了使用 learned W0 而伪造历史 token。

## 2.2 与 RoboTTT 的一个有意差异

RoboTTT 可在当前 timestep 内以当前 token 更新 fast weights；PSM-WMA 的 Local branch 是“recent-history modality”，且已经冻结 `current Policy observation != 本次 history write`。

因此本项目采用一个明确的一步因果 shift：

```text
completed evidence e_(t-1)
→ update W_(t-1) to W_t
→ produce Local token for decision t
```

这是为了保持 R08 的 past-only attribution，不是实现遗漏。

---

# 3. 新的 runtime 数据流

## 3.1 每一步只消费一个新增 evidence

逻辑接口从：

```text
E_history [B,H,D_e]
```

收敛为 streaming 语义：

```text
e_new [B,1,D_e]
```

首版继承当前 evidence width：

```text
D_e = 256
```

但 `1` 是算法语义，不要求所有训练 tensor 在物理存储上只能是 `[B,1,...]`；训练可以一次提供 `[B,T,...]` segment，再由 backend 沿时间维逐步 scan。

## 3.2 Persistent fast state

对有效 sample：

```text
W0
 │ e1
 ▼
W1
 │ e2
 ▼
W2
 │ e3
 ▼
...
 │ et
 ▼
Wt
```

只允许在以下事件 reset：

```text
episode start / env reset / explicit done mask
```

禁止：

```text
每个 model.forward() reset W
每个 H=16 window reset W
每个 dataloader item 无条件 reset W
```

并行 env / batch 的 state ownership 必须至少由：

```text
(env_id or rollout_slot, episode_id)
```

唯一确定，禁止跨 sample / episode 共享 fast state。

---

# 4. LocalEvidenceEncoder

R08 已实现/冻结的 causal evidence 构造继续复用。概念上每步：

```text
historical visual summary
+ executed action information
+ robot state (when enabled)
+ delta-time / age information if retained
        ↓
LocalEvidenceEncoder
        ↓
e_t ∈ R^256
```

v0.2 不要求重做视觉 backbone，也不要求修改 Cosmos Policy 的 native observation representation。

但语义需要从：

```text
“先构造 H=16 历史窗口，再一次性编码”
```

改为：

```text
“每个完成的历史 timestep 产生一条 canonical e_t，按时间流式写入 memory”
```

历史缓存可以继续作为离线数据源，但不得再把“缓存窗口长度”解释成 memory horizon。

---

# 5. TTT-KVB inner update

## 5.1 删除旧 inner target

以下旧目标从正式算法中删除：

```text
prediction = W @ evidence
 target    = evidence[:D_local]
 L_inner   = MSE(prediction, target)
```

原因：

- `evidence[:32]` 只是混合 latent 的前 32 个坐标，无语义依据；
- 存在 `W = [I_32 | 0]` 的平凡解；
- 无法说明 fast weights 学到的是任务相关历史，而不是自投影；
- 当前实现还通过 detach 将该 update 与 Cosmos task loss 隔离。

旧 objective 只保留为 B0 CPU fast-weight smoke 的历史记录，不得再作为正式 TTT training algorithm。

## 5.2 新 inner objective

对每个新增 evidence：

```text
K_t = theta_K(e_t)
V_t = theta_V(e_t)
Q_t = theta_Q(e_t)
```

TTT fast model：

```text
f_W(.)
```

inner self-supervised loss：

```text
L_inner,t = || f_(W_(t-1))(K_t) - V_t ||^2
```

每个有效 timestep 做一次 fast update：

```text
W_t = W_(t-1) - eta_t * grad_W L_inner,t
```

再使用**更新后的** fast model read：

```text
m_t = f_(W_t)(Q_t)
```

最终：

```text
m_t [B,1,D_local]
→ local_memory2llm
→ local_memory_modality_embed
→ Cosmos Local clean token
```

`K/V/Q` 都由已经可观测的 causal evidence 自身产生，因此同一个 inner update 在 inference 也成立，不需要 GT action / future observation / memory label。

---

# 6. Fast model topology

正式方向对齐 RoboTTT：fast state 应是一个**小型模型的权重**，而不是人为固定的 `32 x 256` self-projection matrix。

首版建议：

```text
K/Q/V projection: D_e=256 → D_ttt
fast model f_W: 2-layer MLP, D_ttt → D_ff → D_local
Local output: D_local=32
```

其中：

- `D_local=32` 继续保持当前 Local token interface；
- `D_ttt` / `D_ff` 必须 config-driven；
- 2-layer MLP 是正式 RoboTTT-aligned candidate；
- exact hidden width / activation / bias / eta parameterization 需在 implementation source audit 中冻结；
- 若保留线性 fast model，只能作为明确标注的简化 ablation，不得冒充完整 RoboTTT-style backend。

---

# 7. Learned initialization W0 与 slow/fast 参数边界

## 7.1 W0

旧 B0：

```text
W0 = zeros
```

正式方案：

```text
W0 = learned initialization
```

训练时 `W0` 是 slow learned parameter；每个 episode 的 fast state 从 `W0` 派生：

```text
W_fast,0 = clone/functionalize(W0)
```

推理时只复制已训练好的 W0 数值作为 episode 初始 fast state，不更新 W0 本身。

## 7.2 参数分类

**Slow parameters（optimizer/checkpoint）**：

```text
LocalEvidenceEncoder
theta_Q / theta_K / theta_V
learned W0 / fast-model meta parameters
optional learned inner step-size / modulation
local_memory2llm
local_memory_modality_embed
```

**Fast state（inner update，不进入普通 slow optimizer）**：

```text
W_t
```

fast state 不是普通 `nn.Parameter` optimizer state。训练/推理 rollout 中其数值随时间更新。

若需要训练中断后的严格 sequence resume，可以单独设计 detached runtime-state resume artifact；不得把 `W_t` 混入 model weight / Adam optimizer state，并需另行 Gate。

---

# 8. Cosmos outer loss 保持原样

TTT 不新增人工 memory supervision，也不改变 Cosmos 原任务定义。

继续使用当前 Cosmos native loss，例如：

```text
L_outer = L_Cosmos_original
        = lambda_v * L_vision_flow + lambda_a * L_action_flow
          (+ 当前 recipe 已有且 matched 的其它原生项)
```

关键点：

```text
L_inner 不是以 lambda_ttt * L_inner 的形式简单加进 L_total
```

其角色是**定义 fast-state transition**：

```text
W_t = Update(W_(t-1), L_inner,t)
```

然后 outer loss 评价使用 `W_t` 后的 Cosmos 输出：

```text
W_t
 ↓
Local token
 ↓
Cosmos
 ↓
原生 Vision/Action loss
```

因此“保持 Cosmos 原有 loss 设定”与“TTT 有 inner loss”并不矛盾：

- inner loss：每步怎样写 fast state；
- outer Cosmos loss：怎样学习一套对机器人任务真正有用的写入/读取规则。

---

# 9. 训练期 gradient contract

这是 v0.2 相比当前 prototype 的核心变化之一。

## 9.1 segment 内必须允许 outer meta-gradient

当前 prototype 存在：

```text
evidence.detach()
W update create_graph=False
W.detach()
Local token.detach()
```

这会切断：

```text
Cosmos task loss
  X
TTT update / theta_K / theta_V / W0 / earlier evidence
```

正式训练路径要求一个 TBPTT segment 内：

```text
L_Cosmos
  ↓
Local token
  ↓
f_W(Q)
  ↓
W_t update
  ↓
theta_Q / theta_K / theta_V / W0 / EvidenceEncoder
```

可微。

为真正 meta-learn K/V/update dynamics/W0，canonical implementation 必须支持 update 的 higher-order gradient（等价于 inner `grad_W` 在 outer backward 时可微）。不能继续用 `create_graph=False + 全量 detach` 作为正式训练语义。

如果后续因显存/速度尝试 first-order approximation，必须：

- 单独配置；
- 单独实验；
- 明确标记与 canonical meta-gradient TTT 不同；
- 不得静默替换正式方案。

## 9.2 TBPTT boundary

首版：

```text
ttt_tbptt_steps = 16
```

其含义只有：

```text
每 16 个 temporal updates 截断 outer computational graph
```

例如：

```text
e1  → W1
...
e16 → W16
       │
       └─ detach graph only
          keep numerical W16

e17 → W17
...
```

严格禁止：

```text
detach(W16) == reset(W16)
```

二者不是一回事。

---

# 10. 训练数据与 sequence contract

旧 B2 以独立 sliding windows 为核心的数据流不足以证明 continual memory，因为它允许每个 outer sample 自己从零 replay。

正式 TTT meta-training 必须能够表达：

```text
episode chronological stream
segment 0: t=1..16
segment 1: t=17..32
segment 2: t=33..48
...
```

并满足：

1. 同一 episode 内 segment 按时间顺序；
2. `W_end(segment n)` 数值传给 `segment n+1`；
3. segment boundary 只 detach graph；
4. episode boundary 才 reset 到 learned W0；
5. 不允许 random shuffled independent windows 假装 state carry；
6. 多 worker / 多 rank 必须有唯一 state owner，禁止同 episode 被两个独立 state 同时推进；
7. 训练 tensor 可以一次包含 `[B,T,D_e]`，但 backend 的语义仍是逐 timestep `e_t` update。

可实现为：

```text
A. stateful chronological segment sampler
```

或：

```text
B. episode/long-sequence sample + backend internal TBPTT scan
```

具体选择需独立 source audit；**不能继续把 `history_horizon=16` 的独立 window sampler 当正式 continual-TTT training contract。**

---

# 11. Inference contract

推理时没有 GT action / outer task loss，但仍执行 KVB inner update。

每个 control step：

```text
new completed evidence e_t
        ↓
K_t / V_t / Q_t     (slow params frozen)
        ↓
L_inner,t
        ↓
只对 fast W 求 inner gradient
        ↓
W_(t-1) → W_t
        ↓
f_Wt(Q_t)
        ↓
Local token
        ↓
Cosmos normal inference
```

推理时：

**不更新**：

```text
Cosmos weights
LocalEvidenceEncoder slow weights
theta_Q/K/V
W0
local_memory2llm
```

**只更新**：

```text
runtime fast state W_t
```

因此 inference 不能简单把整个 Local runtime 放进 `torch.no_grad()`。正确 graph policy 是：

```text
slow feature/projection: frozen
TTT inner update: local enable_grad, only W requires grad
Cosmos inference: normal no-grad/inference path
```

当前 `TTTLocalMemoryBackend supports training grad-mode only` 的 fail-fast 不是最终 inference contract，必须在正式 runtime Gate 中替换。

---

# 12. GRU matched baseline 的同步修正

为了公平 A/B，R09-A recurrent baseline 也不能继续用：

```text
每个 outer sample 从 h=0 replay 最近 H=16
```

正式 matched baseline 应为：

```text
h_(t-1) + e_t → GRUCell → h_t
```

并且：

```text
h_t 跨 timestep/segment carry
every 16 steps detach graph
only episode reset clears h
```

于是 A/B 的唯一核心差异才是：

```text
A: vector recurrent state updated by learned recurrence
B: fast-weight recurrent state updated by self-supervised gradient descent
```

其余保持 matched：

- evidence；
- streaming sequence；
- TBPTT length；
- Local output dim/token budget；
- Cosmos backbone；
- native loss；
- training/eval budget。

---

# 13. 推荐接口与 shape

## 13.1 Logical step API

推荐 backend contract 概念上收敛为：

```python
step(
    evidence_t: Tensor[B, D_e],
    state_in: FastState,
    valid: Tensor[B],
    *,
    training: bool,
) -> (
    local_token: Tensor[B, 1, D_local],
    state_out: FastState,
    present: Tensor[B],
)
```

训练可额外提供 sequence scan wrapper：

```python
scan(
    evidence: Tensor[B, T, D_e],
    mask: Tensor[B, T],
    state_in,
    tbptt_steps=16,
)
```

但 `scan()` 只是效率/训练封装，不应重新定义 sliding-window memory。

## 13.2 Current inherited dimensions

当前接口事实继续：

```text
D_e      = 256
D_local  = 32
K_local  = 1
```

`D_ttt / D_ff` 为新 TTT fast model 的 implementation Gate 参数。

---

# 14. Config 语义调整

旧配置容易把 history window 和 TBPTT 混在一起。正式配置应显式拆名：

```yaml
local_history:
  enabled: true
  backend: ttt_fast_weight

  # runtime streaming semantics
  runtime_evidence_steps: 1
  persistent_state: true
  reset_on_episode_done: true

  # training graph semantics
  tbptt_steps: 16

  # evidence/local interface
  evidence_dim: 256
  local_dim: 32
  token_budget: 1

  # TTT
  inner_objective: kv_binding
  update_every_valid_step: true
  learned_initialization: true
  fast_model: mlp2
  ttt_dim: TBD
  ttt_ff_dim: TBD
  inner_lr: TBD
  meta_gradient: exact
```

以下旧字段不得继续承担正式算法含义：

```text
local_history_horizon=16   # 不再表示 TTT memory horizon
segment_steps=4            # 不再表示每4步才更新一次 W
```

若为兼容 loader 暂时保留旧字段，必须清楚标记为 legacy/data-building 字段，不能进入论文/实验口径。

---

# 15. 当前代码与新设计的差距

以 `cosmos-framework@21d064f2...` 为基线，当前 `TTTLocalMemoryBackend` 仍是 B0/B1 prototype：

| 项目 | 当前实现 | v0.2 正式方案 |
| --- | --- | --- |
| runtime 输入 | `[B,H,256]` replay | 每步新增 `[B,1,256]` |
| state carry | outer forward 默认不 carry | 跨 control timestep carry |
| reset | replay 无 state 时从零 | 只在 episode reset |
| update frequency | 每 4 valid steps | 每 valid timestep |
| inner target | `e[:32]` | learned `V=theta_V(e)` |
| write key | `e` | learned `K=theta_K(e)` |
| read query | `last evidence` | learned `Q=theta_Q(e)` |
| fast model | linear `W[32,256]` | RoboTTT-style small model，首选 2-layer MLP |
| W0 | zero | learned initialization |
| outer gradient | detach 阻断 | segment 内 meta-gradient 连通 |
| TBPTT | 无真正 cross-step carry | 16-step detach, state value carry |
| inference | no-grad fail-fast | inference inner update fast W |
| slow TTT params | 0 | QKV/W0/meta params 存在 |

因此当前 B1 runtime smoke 可以保留为“旧 prototype 工程路径曾可运行”的历史 evidence，但**不能作为 v0.2 正式 TTT 算法已经实现的证据**。

---

# 16. 与旧文档/旧 Gate 的冲突处理

## 16.1 保留有效、不重开的部分

以下旧结论继续有效：

- `PSM-WMA_02_detailed_design_v2.1_frozen.md` 的项目级 Cosmos/Local/Global 边界；
- `PSM-WMA_Local_Memory_detailed_design_addendum_v0.1.md` 的 R07 clean Local contract、R08 causal history原则、Local 与 Global 分离、native task loss、matched attribution原则；
- `PSM-WMA_R08_Causal_Local_Evidence_Stream_Implementation_Supplement_v0.1.md` 的 source index / no future leakage / executed action / evidence stream合同；
- 已关闭的 R07/R08 plumbing / causality evidence，除非新实现直接改动对应代码。

## 16.2 被 v0.2 supersede 的旧算法语义

以下旧设计仅保留历史记录，不再是 R09-B 正式算法 authority：

### `PSM-WMA_Local_Memory_detailed_design_addendum_v0.1.md`

被 supersede 的内容包括：

- R09 smoke 以固定 H-window 从零 replay 作为 TTT 正式语义；
- 将 `history_steps/H` 作为最终 memory horizon；
- TTT update rule 完全留给旧 B0 surrogate 而不要求 KVB/meta-gradient。

### `PSM-WMA_R09_B_TTT_preflight_runbook_v0.2_2026-08-30.md`

被 supersede 的内容包括：

- 每 sample/window `state_start=zeros`；
- fast state 只在单 window 内 carry；
- 默认禁止 TTT backend slow learned parameters；
- boundary 外不得读取 state。

### `PSM-WMA_R09_B_TTT_source_audit_v0.1_2026-08-30.md`

其 B0 concrete candidate 整体降级为历史 prototype contract，尤其：

```text
W[B,32,256] zero init
MSE(W @ e, e[:32])
segment_steps=4
SGD lr=0.1 hardcode
create_graph=False
final token detach
zero new slow params
no outer/control-forward state carry
```

这些值不得进入新的正式 TTT training config。

### `PSM-WMA_R09_B2_matched_training_preflight_runbook_v0.1_2026-08-31.md`

旧 B2 matched contract 中以下假设失效：

- recurrent/TTT 都比较独立 H=16 window replay；
- TTT 没有 backend slow parameters；
- TTT optimizer selector 少于 recurrent；
- B1 training-only/no-grad fail-fast 可直接沿用到正式 B2-T；
- 当前 window-ID manifest 足以代表 continual sequence training。

## 16.3 对现有 P3/P4/P5/B2 资产的处理

现有 B2 P3/P4/P5 设计、fixture、artifact 不删除，保留 provenance 和历史审计价值。

但凡其内容绑定了以下旧算法事实：

```text
TTT zero slow parameters
TTT 3-selector optimizer membership
window-local state
segment_steps=4
old B1 no-grad inference prohibition
old resolved TTT config
```

都**不得再作为新 B2-T 的训练 authority**。

处理原则：

1. 算法无关的 static tooling / canonical JSON / provenance / fail-closed machinery 可以复用；
2. backend contract、optimizer inventory、resolved config、pair diff、request authority 必须在 v0.2 实现关闭后重新生成/重新冻结；
3. 当前任何 P4/P5 静态批准不自动授权旧 TTT config 进入 B2-T；
4. 在新 backend implementation + CPU/GPU runtime + optimizer/source audit 关闭前，B2-T 保持 BLOCKED。

---

# 17. 新 optimizer membership 预期

旧 TTT 因“零 slow learned parameter”而使用与 recurrent 不同的 selector。v0.2 不再成立。

如果 Q/K/V、W0、fast-model meta parameters 都注册在：

```text
local_history_runtime.recurrent_backend.*
```

则首选恢复与 recurrent 相同的四类 Local optimizer prefix：

```text
local_history_runtime.encoder.*
local_history_runtime.recurrent_backend.*
local_memory2llm.*
local_memory_modality_embed
```

这只是 v0.2 的**结构期望**；实际 exact parameter names/counts 必须由新的 source audit / optimizer inventory 实证，不能直接沿用旧 P3。

---

# 18. Training / inference 伪代码

## 18.1 Training

```python
state = init_from_learned_W0(batch)

for segment in chronological_episode_segments:
    for t in segment:  # e.g. 16 steps
        e_t = local_evidence_encoder(step_t)
        k_t = theta_k(e_t)
        v_t = theta_v(e_t)
        q_t = theta_q(e_t)

        inner_loss = mse(f(state, k_t), v_t)
        state = differentiable_inner_update(state, inner_loss)

        local_t = f(state, q_t)
        pred_t = cosmos_with_local(step_t.policy_input, local_t)
        outer_loss += cosmos_original_loss(pred_t, step_t.targets)

    outer_loss.backward()
    slow_optimizer.step()
    slow_optimizer.zero_grad()

    state = detach_value_keep_state(state)  # TBPTT only
```

实际 optimizer-step / segment aggregation 要适配 Cosmos trainer，但算法语义必须等价。

## 18.2 Inference

```python
state = clone_learned_W0()

for control_step in episode:
    if newest_completed_history_exists:
        e = frozen_local_evidence_encoder(new_history)
        k, v, q = frozen_qkv(e)

        with enable_grad_only_for_fast_state():
            inner_loss = mse(f(state, k), v)
            state = inner_update(state, inner_loss)

        local_token = read_frozen_fast_state(state, q)
    else:
        local_token = None

    with no_grad():
        action = cosmos_policy(current_observation, local_token)

    execute(action)

    if done:
        state = clone_learned_W0()
```

---

# 19. 必须新增的验证项

正式 implementation Gate 至少覆盖：

## 19.1 Algorithm contract

- `runtime_evidence_steps == 1`；
- 每个 valid timestep fast state 都更新；
- full chronological scan 与任意 segment split 后的 numerical state/readout 一致（在声明 tolerance 内）；
- segment boundary detach 后 state value 保持；
- episode reset 只重置目标 sample；
- cross-sample / cross-episode isolation；
- all-mask / no-history 不产生伪 Local token。

## 19.2 Gradient contract

训练模式至少证明：

```text
Cosmos original task loss
→ local_memory2llm
→ TTT read
→ Q projection
→ differentiable inner update
→ K/V projection
→ learned W0 (first segment)
```

存在 finite/nonzero 的预期 gradient。

不得继续把 `graph_detached=true` 作为正式 TTT PASS 条件；正式 PASS 应区分：

```text
within-segment meta-gradient connected = true
segment-boundary state graph detached = true
```

## 19.3 Inference contract

- 整个 Cosmos 保持 frozen/no slow update；
- `torch.no_grad()` 外层存在时，Local inner update 能局部开启 fast-state gradient；
- Q/K/V/W0/encoder 参数值前后 exact unchanged；
- W_t 随新 evidence 变化；
- W_t 跨多个 control steps 持续 carry；
- episode done 后只清对应 state。

## 19.4 Matched A/B contract

recurrent 与 TTT 必须使用相同：

- chronological stream；
- TBPTT steps；
- evidence；
- Local token dim/count；
- Cosmos checkpoint；
- native loss；
- optimizer-step budget；
- evaluation seed / closed-loop protocol。

不得再比较“persistent TTT”对“每-window-reset GRU”或反之。

---

# 20. 新 Gate 顺序建议

现有 B2-T 在旧 backend contract 下继续 BLOCKED。v0.2 推荐重新经过：

```text
R09-B-v0.2 Design Review
        ↓
TTT source/implementation audit
        ↓
CPU contract: KVB + state carry + gradient semantics
        ↓
streaming/sequence sampler audit
        ↓
GPU bounded training smoke
        ↓
inference persistent-state smoke
        ↓
optimizer inventory / resolved-config refreeze
        ↓
matched recurrent vs TTT training
        ↓
closed-loop intervention / SR
```

其中：

- 不需要重开 R07/R08，除非 implementation 实际破坏其冻结代码/合同；
- 不允许从旧 B1 bounded smoke 直接跳到新 B2-T；
- 旧 P4/P5 static machinery可复用的部分先保留，但算法绑定数据必须重算。

---

# 21. 论文/项目口径

在 v0.2 正式实现和验证前，不应宣称：

```text
“PSM-WMA 已实现 RoboTTT continual memory”
```

当前准确表述：

> **已有一个 window-local、detached fast-weight prototype；v0.2 将其纠偏为 RoboTTT-style continual fast-weight Local Memory，并保持 Cosmos backbone 不变。**

v0.2 实现通过后，可表述为：

> **RoboTTT-style continual fast-weight memory is integrated as an independent clean Local modality branch for Cosmos3, with per-step KVB updates, cross-timestep fast-state carry, TBPTT, and the native Cosmos task loss as the outer objective.**

但仍应注明与 RoboTTT 原论文 topology 的差异：

```text
RoboTTT: TTT layers inserted inside the policy backbone/action-head stack
PSM-WMA: TTT only in the independent Local Memory modality branch
```

---

# 22. 一句话 implementation contract

```text
one newly completed causal evidence per control step
→ learned Q/K/V
→ KVB self-supervised fast-weight update every step
→ persistent W carried across the episode
→ detach graph only every 16 training steps
→ read Local token from updated W
→ unchanged Cosmos3 backbone and native task loss
→ outer loss meta-learns how Local memory should write/read
→ only episode reset clears fast state
```
