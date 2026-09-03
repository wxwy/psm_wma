# PSM-WMA Temporal Local Memory 详细设计补充 v0.2.1

**日期**：2026-09-03

**状态**：design remediation / implementation 前必须重新独立审核

**适用分支**：根仓 `V2`

**被整改设计**：`docs/build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.2.md`

**设计锚点**：`a2ed6bac747a4f65868bb4aee5bb7070e083b625`

**审核意见**：`docs/collab/chatgpt/reviews/2026-09-03_R09_B_TTT_v02_design_a2ed6ba.md`

**Cosmos 实现基线 / Gitlink**：`21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

> 本文件只关闭 v0.2 审核指出的数学 shape、逐 sample update、sequence outer-loss/noise、inference autograd 以及后续 source-audit 交付合同缺口。除本文明确覆盖处外，v0.2 全部语义继续有效；若二者冲突，以 v0.2.1 为准。
>
> 本文件不授权 Cosmos 子模块实现、GPU、训练、评测、推理、optimizer/config refreeze、P4/P5 真实操作或 B2-T。下一阶段申请范围仍仅为只读/static source audit。

---

# 1. 保留且不得回滚的 v0.2 结论

以下结论不因本轮整改改变：

1. decision `t` 只写入最新已完成的 causal evidence `e_(t-1)`；首步没有历史时 `local_present=false`；
2. runtime logical write length 为 1，训练 `[B,T,...]` 只是 chronological scan wrapper；
3. fast state 跨 control timestep 和 TBPTT segment 持续 carry，仅 episode/env/done reset；
4. `tbptt_steps=16` 只截断 graph，不重置数值 state；
5. 每个 valid timestep 做一次 KVB fast update，并用更新后的 state read；
6. learned Q/K/V 与 learned W0 是 slow learned objects，runtime `W_t` 是 fast state；
7. canonical training 在 segment 内保留 differentiable inner update / higher-order meta-gradient；
8. inference 只更新 fast state，Cosmos、encoder、QKV、W0 和 Local adapter slow weights不更新；
9. TTT 只位于独立 clean Local modality branch，不插入 Cosmos shared MoT/backbone；
10. matched GRU baseline 同样使用 chronological persistent state 与 TBPTT，而不是每 window reset；
11. 旧 B0/B1 prototype 及其 B2/P3/P4/P5 algorithm-bound optimizer/config authority 继续失效。

---

# 2. 冻结的 KVB shape 与 fast-state topology

## 2.1 Canonical Option A

首个正式实现采用 value 位于 Local output space 的 Option A；不得在 source audit 或实现时静默切换成额外 slow readout 的 Option B：

```text
e_b,t                         ∈ R^D_e,       D_e = 256
K_b,t = theta_K(e_b,t)        ∈ R^D_ttt
Q_b,t = theta_Q(e_b,t)        ∈ R^D_ttt
V_b,t = theta_V(e_b,t)        ∈ R^D_local,   D_local = 32

f_W: R^D_ttt -> R^D_ff -> R^D_local
f_W(K_b,t), V_b,t             ∈ R^32
m_b,t = f_W_updated(Q_b,t)    ∈ R^32
local token                   ∈ R^[B,1,32]
```

因此 KVB loss 两端始终同为 `D_local=32`，不要求 `D_ttt == D_local`。

`D_ttt` 与 `D_ff` 必须为正整数、config-driven，并由获批后的 source audit 根据当前接口、参数/显存预算和实现扩展点提出一个明确首版值；在其后 implementation design Gate 中冻结数值。不得复用旧 `W[32,256]` prototype 的维度作为未经审计的默认事实。

## 2.2 Fast-state pytree 的规范结构

canonical fast model 为两层 MLP，完整 fast-state pytree 恰为：

```text
W.fast_in.weight   [D_ff, D_ttt]
W.fast_in.bias     [D_ff]
W.fast_out.weight  [32, D_ff]
W.fast_out.bias    [32]
```

其计算为：

```text
f_W(x) = linear_2(activation(linear_1(x)))
```

每个 sample 持有该 pytree 的独立数值副本。learned `W0` 与上述四个 member 一一同 shape 映射；episode 初始化或选择性 reset 是从 slow `W0` 复制完整四成员，而不是只重置矩阵或遗漏 bias。

activation、`D_ttt`、`D_ff`、参数 dtype 与 inner compute precision 必须由 source audit 显式列出并在后续 implementation design 中冻结。线性 fast model 只允许作为另行命名和审核的 ablation。

---

# 3. 冻结的逐 sample KVB update

## 3.1 Feature-only loss reduction

对每个 sample `b` 和 timestep `t` 独立定义：

```text
r_b,t,j = f_(W_b,t-1)(K_b,t)[j] - V_b,t[j]

L_inner,b,t = (1 / D_local) * sum_(j=1..D_local) r_b,t,j^2
            = mean_over_local_feature_only(r_b,t^2)
```

feature reduction 固定为 `mean`，不是 `sum`。`inner_lr` 的含义固定为乘在这个 feature-mean gradient 上；不得再除以 batch size、valid sample 数、sequence length、gradient-accumulation steps 或 rank 数。

首个 canonical implementation 的 `inner_lr` 是 config 中一个有限、严格大于零、所有 sample/timestep 共享的非 optimizer scalar。learned/per-layer/per-step eta 仅可作为未来独立设计和实验变量，不得静默进入首版。

## 3.2 独立 gradient 与 valid mask

对完整 fast-state pytree 中每个 member `p`：

```text
g_b,t[p] = d L_inner,b,t / d W_b,t-1[p]

if valid_b,t:
    W_b,t[p] = W_b,t-1[p] - inner_lr * g_b,t[p]
else:
    W_b,t[p] = W_b,t-1[p]
```

硬约束：

- `g_b,t` 只能由 `L_inner,b,t` 对 `W_b,t-1` 求得，不得先对 batch 或 valid sample 求均值再更新；
- 改变同 batch 中其他 sample 的内容、mask 或数量，不得改变 sample `b` 的 update；
- invalid/masked sample 的完整 fast-state pytree逐 member、逐 bit 保持不变，且 `present=false`、不产生伪 Local token；
- partial episode reset 只把目标 sample 的完整 pytree复制为 learned W0，其他 sample 不变；
- TBPTT boundary 对每个 member执行 `detach(value)`，保留完整数值，不调用 W0 初始化；
- 任意 vectorized/vmap 实现必须与逐 sample reference 等价。首个 CPU float32 contract 使用 `atol=1e-6, rtol=1e-5`；生产 dtype 的容差须在后续 implementation design 中另行冻结。

训练时 canonical reference 等价于对每个 `L_inner,b,t` 调用只面向该 sample pytree 的 `autograd.grad(..., create_graph=True)`；不得以 batch-reduced scalar 的一次普通 parameter gradient 替代 per-sample fast update。

## 3.3 更新后读取

仅对 `valid_b,t=true`：

```text
m_b,t = f_(W_b,t)(Q_b,t) ∈ R^32
present_b,t = true
```

读取必须使用本 timestep 更新后的 `W_b,t`。invalid/no-history sample 不读取 learned W0 伪装为历史 token。

---

# 4. Chronological sequence 的 native outer-loss/noise 合同

v0.2 将原 single-step training path 扩成 `[B,T]` chronological supervision 时，不改变 Cosmos 原生 loss 定义，但冻结其应用单位和归一化：

1. 每个有效、受监督的 `(sample b, control timestep t)` 是一个独立 native action/future training item；
2. flow/noise timestep 与 noise 必须为每个该 item 独立采样。不得把一个 segment 的同一 noise level/noise 广播到多个 action chunk；
3. Local history-only、padding、invalid 或仅用于 state carry 的 timestep 不贡献 native action/future loss；
4. 先由现有 Cosmos loss 得到每个有效 item 的 native scalar loss（其内部 target/channel reduction 保持原 recipe）；再在一次 slow optimizer accumulation group 内按所有有效受监督 timestep作加权全局 mean：

```text
outer_numerator   = sum native_loss_b,t over valid supervised (b,t)
outer_denominator = count valid supervised (b,t)
L_outer           = outer_numerator / outer_denominator
```

5. padding 数、batch packing、microbatch 切分、gradient accumulation 或 rank 划分不得改变同一有效 item 集合的归一化权重；实现若分 microbatch/rank，必须累计 numerator/denominator 或采用数学等价的权重；
6. `outer_denominator == 0` 的 segment/microbatch 不得产生 slow optimizer step，也不得伪造 zero loss；fast state 是否前进只由本 timestep 是否存在 valid completed evidence 决定，与是否存在 outer supervision 分开判定；
7. KVB inner loss只定义 state transition，不作为 `lambda * L_inner` 直接加到 Cosmos outer loss。

获批后的 source audit 必须沿实际生产训练入口回答：

- 当前 noise/time sampler 在 flatten/scan 后的随机张量 shape，是否已做到每 `(b,t)` 独立；
- 当前 native loss 在何处完成 item 内 reduction、batch reduction、DDP reduction和 grad-accum scaling；
- 为满足上述合同，能否只做 reshape/权重适配；若不能，最小 sequence adapter 的准确插入点；
- 哪个 mask 是有效监督 authority，以及 history-only/padding 怎样被排除。

source audit 只记录事实和差距，不得在本 Gate 修改 loss/trainer/sampler。

---

# 5. Inference autograd 边界

`torch.enable_grad()` 只能覆盖 `torch.no_grad()`，不能被假定为可以恢复任意外层 `torch.inference_mode()` 产生的 inference tensor。正式 runtime 顺序冻结为：

```text
outside torch.inference_mode():
    with torch.no_grad():
        e = frozen_encoder(new_completed_history)
        K, V, Q = frozen_qkv(e)
    K, V, Q = detached ordinary tensors

    with torch.enable_grad():
        W_leaf = detached fast-state pytree with requires_grad_(True)
        L_inner_per_sample = feature_mean_kvb(W_leaf, K, V)
        W_updated = W_leaf - inner_lr * per_sample_grad

    local_token = detach(f_W_updated(Q))

with torch.no_grad() or torch.inference_mode():
    action = cosmos_policy(current_observation, local_token)
```

硬约束：

- Local encoder/QKV/adapter slow parameters保持 frozen，不接收或累积 `.grad`；
- K/V/Q 的产生及 fast update 不能位于包围它们的 production `torch.inference_mode()` 内；如当前顶层入口使用 inference mode，必须在调用它之前完成 Local update并传入普通 detached token；
- 只有每个 sample 的 fast-state pytree leaf 临时 `requires_grad=true`；
- update 后 state 和 Local token 在进入 Cosmos inference 前 detach；
- action 生成可继续使用 Cosmos 原有 no-grad/inference policy；
- episode done 只 reset 对应 sample 的完整 state。

source audit 必须从真实 production inference/closed-loop 调用入口向下跟踪 context manager，而不是只检查 backend 单元函数。后续 CPU/runtime fixture 必须从该真实入口的最小替身开始，证明外层 inference policy 不会封死 W-only autograd。

---

# 6. 获批后 static source audit 的强制交付物

下一阶段只允许生成审计事实，不允许实现。审计文档至少包含以下六张 exact 表及 `file:line` 证据。

## 6.1 Current implementation/gap map

- production training entry、inference/closed-loop entry、Local runtime、TTT backend、evidence encoder、adapter、loss/noise sampler、dataloader/sampler 的实际函数/类；
- 每个入口当前 input/output shape、state 是否跨 call carry、当前 detach/reset位置；
- v0.2.1 每条合同对应的现状：可复用、需替换、需新增或无入口。

## 6.2 Full fast-state pytree inventory

对 `fast_in.weight`、`fast_in.bias`、`fast_out.weight`、`fast_out.bias` 逐项输出：

```text
canonical member name
proposed registered W0 name
shape
storage dtype
inner compute dtype
fast or slow classification
ordinary optimizer membership
checkpoint membership
episode init mapping
partial-reset behavior
TBPTT-detach behavior
bytes per sample
```

并输出整个 pytree 的参数元素数与 `state_bytes_per_sample`。任何额外 buffer、normalization state、activation parameter 或 eta 参数都必须显式列出；未列成员不得进入实现。

## 6.3 Slow parameter inventory proposal

逐项列出 encoder、theta_Q/K/V、四个 learned W0、Local adapter，以及任何审计后确需的 slow parameter的拟议 exact registered name、shape、dtype、optimizer/checkpoint归属。不得沿用旧 P3 selector/count 作为证据。

## 6.4 Sequence action-forcing/loss audit

输出第 4 节四个实际 authority：per-item noise/time shape、native item loss位置、valid-supervision mask、跨 microbatch/rank 的 numerator/denominator 归一化路径，并给出最小 adapter 插入点或“无需 adapter”的代码证据。

## 6.5 Inference context audit

从真实 production inference入口输出 `no_grad`/`inference_mode` 嵌套图、Local update可插入边界、普通 tensor形成位置、W-only grad scope以及进入 Cosmos 前的 detach位置。

## 6.6 Chronological sampler/state ownership audit

至少输出：

```text
episode_id / env_id / rollout_slot 的真实来源
segment 的 start/end/done/valid authority
同 episode segment 的排序与连续性保证
dataloader shuffle / sampler / batch packing 行为
num_workers 下 state owner 与 sample handoff
DDP rank partition 与同 episode 唯一 owner
gradient accumulation 内 state 前进次数和 optimizer-step边界
epoch boundary、drop/retry/replay 对 state 的影响
partial done/reset 行为
checkpoint/resume 当前能力与明确非目标
```

必须证明同一 episode 的同一 transition 不会被两个独立 fast state 同时推进，也不会因 grad accumulation 重放而更新两次。若当前 pipeline 无法保证，审计只记录阻塞点和最小 future design seam，不得现场改实现。

---

# 7. 下一阶段 Gate 与验收

v0.2.1 重新获得 ChatGPT、Kimi、MM 对同一 SHA 的：

```text
APPROVE_TO_IMPLEMENT_R09_B_TTT_V02_STATIC_SOURCE_AUDIT
```

后，只允许：

- 只读检查 `cosmos-framework@21d064f2...` 与根仓生产入口；
- 编写版本化 source-audit 文档和必要的 stdlib/static inspection helper；
- 运行不导入 torch、不读取模型/数据/checkpoint、不使用 GPU 的静态核验。

仍禁止：

- 修改 Cosmos 子模块实现；
- 构造或运行新 TTT backend；
- GPU/CUDA、torchrun、训练、评测、推理或 inference smoke；
- optimizer/resolved-config refreeze；
- P4/P5 真实 preflight、record、refreeze、export或compose；
- B2-T 或 Local Memory 正式训练。

source audit 完成并独立审核后，才可另起 CPU algorithm/gradient implementation design Gate。

---

# 8. 一句话闭合合同

```text
K,Q: 256 -> D_ttt; V: 256 -> 32; two-layer fast MLP: D_ttt -> D_ff -> 32
-> feature-mean per-sample KVB gradient with no batch coupling
-> valid-only whole-pytree update, persistent value carry, selected whole-pytree reset
-> independent native flow/noise supervision per valid control step and global valid-step mean
-> W-only autograd outside inference_mode, then detached Local token into frozen Cosmos inference
-> source audit must freeze exact pytree, dtype/bytes, loss/noise path and sampler/rank ownership
```
