# PSM-WMA Temporal Local Memory 详细设计补充 v0.3.3

**日期**：2026-09-05  
**状态**：user-directed chronology / TBPTT / microbatch lifecycle clarification；implementation 前仍需按项目 Gate 纪律独立审核  
**适用分支**：根仓 `V2`  
**上游版本**：`docs/build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.2.md`  
**当前根仓参考基线**：`7d57ba03e3669f70d3b5ce7f0d8864b1254d124a`  
**当前 Cosmos Gitlink 参考基线**：`dce279a966b6feef39ceb269cc064f6cd8f2240f`

> 本文件只补充 **Cosmos sample 时间轴与 continual-TTT 时间轴的关系、TTT segment 的 chronology、microbatch packing、past-only 一步错位、fast-state/TBPTT/gradient-accumulation/optimizer 生命周期**。  
> v0.3.1 的 Memory Prefix K/V-only 接入合同，以及 v0.3.2 的 `1 x K/V write + K_local x Q read`、multi-slot Local readout、inner/outer loss 参数职责继续有效。  
> 若旧图、旧 runtime 说明或旧实现假设把一个 Cosmos sample 内的 `z0..z4` 当作 TTT 时间序列，或把 `ttt_tbptt_steps` 当作 Local memory horizon / Cosmos gradient accumulation 次数，以本文为准。  
> 本文件不授权训练、GPU、评测、推理或 runtime/packer/trainer 代码变更。

---

# 0. 本次补充的核心结论

Cosmos 与 TTT 使用的是两个不同的时间轴：

```text
Cosmos 单 sample 内时间轴：
    [ z0(f_t), z1(f_{t+1:t+4}), z2(f_{t+5:t+8}),
      z3(f_{t+9:t+12}), z4(f_{t+13:t+16}) ]

TTT continual 时间轴：
    ... e_{t-2} -> e_{t-1} -> e_t -> e_{t+1} ...
    （跨 Cosmos samples、沿同一 episode 的已完成历史推进）
```

因此：

1. `z1..z4` 是当前 Cosmos sample 的 future/noisy/generated horizon，**禁止作为当前决策的 TTT 历史输入**；
2. TTT 每一步消费一个跨 sample 的 completed causal evidence `e_tau`，不是把一个 Cosmos sample 的五个 temporal latents 当成五个 TTT steps；
3. `ttt_tbptt_steps=16` 表示 **一条 fast-state autograd segment 最多覆盖同一 episode 中连续、有序的 16 个 control/sample steps**；它不是 memory horizon；
4. 若当前 packed micro sample budget 为 `128`，首版 fixed-length chronology packing 应组织为 `B_seg=8, T=16`，即 8 条独立 episode stream × 每条 16 个连续 sample slots；
5. segment 结束只 detach fast-state graph，fast-state 数值继续 carry；只有 episode reset/done 才回到 learned `W0`；
6. `ttt_tbptt_steps` 与 Cosmos `grad_accum_iter` 是两套独立 clock，数值即便碰巧相同也不得混同。

---

# 1. Cosmos sample 时间轴与 TTT 时间轴

## 1.1 Cosmos 原生单 sample

对 decision/sample `t`，Cosmos 原生 temporal latent 结构概念上为：

```text
S_t = [
    z0_t = latent(f_t),
    z1_t = latent(f_{t+1:t+4}),
    z2_t = latent(f_{t+5:t+8}),
    z3_t = latent(f_{t+9:t+12}),
    z4_t = latent(f_{t+13:t+16})
]
```

其中 `z0_t` 对应当前已观测帧；`z1_t..z4_t` 属于当前 sample 的未来预测/生成 horizon。

TTT **不得**采用：

```text
[z0_t, z1_t, z2_t, z3_t, z4_t] -> TTT scan
```

因为这会把当前 sample 的未来 latent 当作历史写入 memory，破坏 past-only causality，并产生 future leakage。

## 1.2 TTT 的 canonical 一步输入

TTT 时间轴沿 dataset/episode 的真实历史推进。每个已完成 step `tau` 构造一条：

```text
e_tau [D_e=256]
```

概念来源为：

```text
historical/current-at-tau observed visual summary
+ executed historical action_tau
+ optional robot state_tau
+ dt / age metadata
        |
        v
LocalEvidenceEncoder
        |
        v
e_tau [256]
```

视觉项只允许来自该历史 step 当时已经可观测的 current observation / `z0_tau` 所对应信息；`z1_tau..z4_tau` 不属于 TTT evidence。当前实现中的 `history_visual_summary` 是否直接由 `z0` latent pool、视觉 encoder summary 或等价 causal feature 得到，由后续 source/runtime contract 冻结；本文冻结的是 **causality 和 chronology**，不是视觉 summary 的具体算子。

---

# 2. Past-only chronology 与一步错位

## 2.1 当前 decision 只能读取过去完成的 evidence

对当前 Cosmos sample `S_t`：

```text
Local Memory M_t 只能依赖 e_{<t}
```

即当前 `S_t` 的 action/future 尚未完成时，不能先把 `e_t` 写入 TTT 再让同一个 `S_t` 使用该写入结果。

v0.3.2 / 当前 TTT core 的 canonical step 是 **update-then-read**：

```text
e_tau
  -> K_tau / V_tau / Q_tau
  -> W_{tau-1} --KVB update--> W_tau
  -> read W_tau with Q_tau
  -> m_tau
```

为了同时保留该算法顺序和 PSM-WMA past-only contract，production 对齐必须采用一格 consumer shift：

```text
TTT step on completed e_{t-1}
        |
        v
updates W_{t-2} -> W_{t-1}
        |
        v
produces Local tokens
        |
        v
attached to Cosmos sample S_t as M_t
```

因此正式索引定义为：

```text
M_t := ReadAfterUpdate(e_{t-1}, W_{t-2})
```

而不是：

```text
M_t := ReadAfterUpdate(e_t, W_{t-1})    # forbidden for same-decision use
```

## 2.2 Episode 第一帧

episode 的第一个 consumer sample `S_0` 没有 `e_{-1}`。首版允许：

```text
Local present = false
Local token   = exact zero / absent according to packed-memory contract
fast state    = learned W0
```

不得伪造上一条 evidence，也不得从下一帧/未来帧补齐。

---

# 3. `ttt_tbptt_steps=16` 的严格语义

`ttt_tbptt_steps=16` 表示：

> 一条 TTT fast-state 的可微计算图，在同一 episode chronology 上最多连续展开 16 个 sample/control steps；第 16 步后截断 autograd graph，但保留 fast-state 数值继续进入下一 segment。

合法 segment 必须满足：

```text
episode_id: E, E, E, ... E          # 相同
step_id:    s, s+1, s+2, ... s+15   # 连续且严格有序
```

若 dataset 使用固定 control stride `d`，则应满足：

```text
step_{i+1} = step_i + d
```

而不是仅仅“16 条样本都来自同一 episode”。以下仍然非法：

```text
E: step 4, 19, 7, 38, ...
```

segment 不允许跨 episode boundary。

## 3.1 TBPTT 不是 memory horizon

正确：

```text
segment 0: W0 -> ... -> W15
                     |
                     +-- detach graph, keep numeric W15
segment 1:           W15 -> ... -> W31
                                  |
                                  +-- detach graph, keep numeric W31
...
```

错误：

```text
每 16 步把 W reset 到 W0
```

因此 continual-TTT 可以在 episode 内记住远超过 16 步的历史；16 只限制 meta-gradient 的反传长度。

---

# 4. Cosmos packed microbatch = 128 时的 chronology layout

当前 Edge 训练口径中，`128` 应理解为 **packed microbatch 的 sample-slot budget / effective Cosmos sample count**，不是把底层 `DataLoader(batch_size=1)` 改写成 128。

当：

```text
N_micro = 128
ttt_tbptt_steps = T = 16
```

首版 fixed-length chronology packing 冻结为：

```text
B_seg = N_micro / T = 8
```

逻辑布局：

```text
microbatch
  stream 0: 16 chronological consumer samples
  stream 1: 16 chronological consumer samples
  ...
  stream 7: 16 chronological consumer samples

logical shape = [B_seg=8, T=16, ...]
flatten for Cosmos = [128, ...]
```

TTT evidence 张量概念 shape：

```text
E_prev       [8,16,256]
valid        [8,16]
M_local      [8,16,K_local,32]
```

随后 Local output 与对应的 128 个 Cosmos consumer samples 一一对齐，再按 Cosmos native packing 需要展平/索引：

```text
[8,16,K_local,32]
  -> map each (stream,time) to its Cosmos sample
  -> 128 x K_local Local tokens
```

## 4.1 每个 consumer row 的 exact 对齐

若一个 stream 的 16 个 Cosmos consumer samples 是：

```text
S_t, S_{t+1}, ..., S_{t+15}
```

那么提供给 TTT scan 的 16 个 completed evidence 是：

```text
e_{t-1}, e_t, ..., e_{t+14}
```

并形成：

```text
e_{t-1} -> M_t      -> S_t
e_t     -> M_{t+1}  -> S_{t+1}
...
e_{t+14}-> M_{t+15} -> S_{t+15}
```

这使 `scan_segment_many()` 的 16 个 update-then-read 输出能够与 16 个 Cosmos consumer samples 对齐，同时不泄漏同一 decision 的未来。

## 4.2 128 必须是 16 的倍数吗

算法上不是绝对数学要求，因为 `valid` mask 可以支持 episode tail / padding；但首版 fixed-length implementation 为减少 packer、state owner 与 loss normalization 的歧义，建议冻结：

```text
N_micro % ttt_tbptt_steps == 0
```

对当前 `128 / 16` 即恰好 8 条 segment streams。

episode 尾部不足 16 个 consumer rows 时允许 padding；invalid rows：

- 不更新 fast state；
- 不产生有效 Local token；
- 不贡献对应 outer loss；
- 不得越过 done 后继续沿旧 fast state 读取另一 episode。

---

# 5. 跨 microbatch 的 stream continuity

因为 TBPTT 只截断 graph、不清除 memory，所以 **同一 episode 的后续 segment 仍必须按 chronology 继续处理**。

若 stream 0 当前 microbatch 处理：

```text
E / S_t ... S_{t+15}
```

且 episode 未结束，则下一 segment 对该 stream 必须继续：

```text
E / S_{t+16} ... S_{t+31}
```

并使用上一 segment detach 后的 fast-state 数值 carry。

因此 sampler/state owner 不能把每个 microbatch 的 8×16 segment 当作彼此随机独立的普通 samples。可接受实现有两类：

1. **stable stream slots**：8 个 stream slot 跨 microbatch 依次推进各自 episode；episode 完成后该 slot reset 到 learned `W0` 再绑定新 episode；
2. **episode-keyed state owner**：以 episode/stream identity 保存和恢复严格前序 segment 的 detached fast state，但不得乱序消费尚未处理前序的 segment。

首版优先 stable stream slots，因为 state ownership 与 chronology 更容易审计。

允许 episode-level shuffle；禁止破坏 episode 内 segment 顺序的 shuffle。

---

# 6. 四套 clock：不要把 TBPTT 与 gradient accumulation 混在一起

完整训练有四个不同生命周期：

```text
Clock 1: control/sample timestep
    每个 valid completed evidence 做一次 TTT KVB fast update

Clock 2: TTT TBPTT segment
    每 16 个 chronological rows 截断 fast-state autograd graph
    数值 state 不 reset

Clock 3: Cosmos gradient accumulation
    多个 outer backward 的 slow gradients 累积在 parameter.grad

Clock 4: optimizer step
    每 grad_accum_iter 个 microbatches/backwards 后
    Adam/FusedAdam 更新 slow parameters
```

因此：

```text
ttt_tbptt_steps = 16
```

不意味着：

```text
grad_accum_iter = 16
```

即使实际配置中两者数值相同，也只是巧合。

## 6.1 Fast update

每个 valid TTT timestep：

```text
L_inner,t = MSE(f_{W_{t-1}}(K_t), V_t)
W_t = W_{t-1} - inner_lr * grad_W L_inner,t
```

这是 forward 内的 runtime fast-state 更新，不经过 Adam/FusedAdam。

## 6.2 Slow update

Cosmos 原生 outer task loss 经 Local readout / differentiable inner update 反传到 slow parameters：

```text
theta_K, theta_V, theta_Q
slot queries r_k
learned W0
LocalEvidenceEncoder
Local adapter / Memory Prefix norm
以及 recipe 明确允许训练的 Cosmos slow parameters
```

每个 microbatch/backward 只累积 `.grad`；达到 Cosmos 原生 `grad_accum_iter` 边界才执行：

```text
clip (if native trainer requires)
optimizer.step()
scheduler.step()    # 按 native trainer contract
optimizer.zero_grad()
```

## 6.3 Optimizer step 前后的 fast state

不得让一个未 detach 的 fast-state graph 跨越 slow optimizer parameter mutation。

因此 optimizer step 前，所有需要继续 carry 的 TTT state 必须已经位于合法 TBPTT detach 边界：

```text
outer backward
 -> detach carried W graph
 -> optimizer.step may mutate slow theta
 -> continue with detached numeric W
```

optimizer.step 后：

- **不 reset fast W**；
- **不从 episode 起点 replay**；
- 保留 detached fast-state 数值继续推进；
- 只有 episode done/reset 才重新 materialize 当前 learned `W0`。

这是标准 TBPTT 的 truncated-training approximation：slow parameters 可在 segment 间变化，fast recurrent state 以 detached 数值连续 carry。

---

# 7. Dataset / sampler / packer 的硬合同

进入 production chronology wiring 前，至少必须能 assert：

```text
A. segment 内 episode_id 完全一致
B. segment 内 step/control index 连续且严格有序
C. segment 不跨 episode boundary
D. consumer S_t 对应的 TTT write input 是 completed e_{t-1}
E. z1..z4 从未进入 TTT evidence path
F. invalid/padding row 不更新 fast state、不贡献 Local/outer loss
G. segment boundary detach graph but preserve numeric fast state
H. episode done reset to learned W0
I. same stream 的下一 segment 紧接上一 segment chronology
J. flatten/packing 后每个 Local output仍映射回正确 Cosmos consumer sample
```

这些 assertion 应优先在 chronology manifest / sampler contract 层证明，而不是仅依赖训练日志推断。

---

# 8. 与 v0.3.2 multi-slot readout 的关系

本文件不改变 multi-slot TTT 数学：

```text
one completed evidence e_tau
        |
        +-> theta_K -> 1 x K_tau
        +-> theta_V -> 1 x V_tau
        +-> theta_Q + r_k -> K_local x Q_tau^k

1 x K/V self-supervised write
        -> W_tau

K_local x Q read from updated W_tau
        -> M_{tau+1} [K_local, D_local]
        -> attached to next Cosmos consumer sample
```

其中：

- inner KVB loss 不含 Q；
- `theta_Q / r_k` 由 Cosmos outer loss 通过 readout 直接训练；
- `theta_K / theta_V / W0` 由 outer loss 经 differentiable inner update/meta-gradient 训练；
- Cosmos 内部 Memory Prefix 仍为 K/V-only，不存在 `Q_MEM`。

本文件新增的只是 **“哪个 e 写、哪个 sample 用”以及“16 步如何被 dataset/trainer 正确组织”**。

---

# 9. Canonical end-to-end chronology

```text
Episode stream
===================================================================

S_t current Cosmos sample
    current z0_t
    future/noisy z1_t..z4_t
        ^
        |
        | consumes
        |
M_t = TTT output after processing completed e_{t-1}
        ^
        |
e_{t-1}: observed historical visual + executed action/state/meta
        |
        +-- K/V write --> W_{t-1}
        +-- Q read ----> M_t

S_t executes / transition completes
        |
        v
construct completed e_t
        |
        v
next row:
e_t -- K/V write --> W_t -- Q read --> M_{t+1} --> S_{t+1}

...

16 chronological consumer rows
        |
        v
outer backward for this packed microbatch path
        |
        v
detach carried fast-state graph at TBPTT boundary
        |
        +-- numeric W persists to next segment
        |
        +-- slow parameter grads continue following Cosmos grad_accum_iter
```

---

# 10. 最终冻结口径

本阶段后续实现、source audit、chronology evidence 与 review 应统一使用以下一句话：

> **Cosmos 的 `z0..z4` 是一个 sample 内的当前+未来预测轴；continual-TTT 的时间轴是跨 samples 的 episode 历史轴。`ttt_tbptt_steps=16` 要求一个 TTT segment 在同一 episode 上包含 16 个连续、有序的 consumer/control sample slots，并以每个 consumer 的上一条 completed evidence 做 update-then-read。当前 packed micro sample budget 128 时，首版组织为 8×16 条 chronology streams；segment 边界只 detach graph、不清 fast-state 数值，episode done 才 reset 到 learned W0；Cosmos gradient accumulation/optimizer step 是独立于 TBPTT 的 slow-parameter 更新生命周期。**
