# PSM-WMA Temporal Local Memory 详细设计补充 v0.3.4

**日期**：2026-09-07  
**状态**：user-directed episode-start / segment-packing clarification；implementation 前仍需按项目 Gate 纪律独立审核  
**适用分支**：根仓 `V2`  
**上游版本**：`docs/build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.3.md`  
**当前根仓参考基线**：`291bc1d5e69e13aefd79b3d0506c6a58960013aa`  
**当前 Cosmos Gitlink 参考基线**：`80aec090688e3c710c41e1dfd86b6500773db2c7`

> 本文件只补充并收紧 v0.3.3 §4/§5 的 **episode 首次进入 stream 必须从 step 0 开始**、`8 x 16 -> 128` 的离线训练布局、slot 内 TTT 串行 / Cosmos flatten 后并行、跨 microbatch fast-state carry 以及 episode tail/rebind 规则。  
> v0.3.3 的双时间轴、past-only 一步错位、TBPTT/gradient-accumulation/optimizer 四套 clock，以及 v0.3.2 的 multi-slot K/V/Q 数学继续有效。  
> 本文件是用户定向设计澄清，不授权 runtime/packer/trainer 实现、GPU、训练、评测或推理。当前已批准的 manifest-route / active-wiring authority 与本文若存在实现结构差异，必须在后续独立设计 Gate 显式对齐，不得静默替换。

---

# 0. 本次新增硬结论

首版 chronology training 采用：

```text
N_micro = 128
ttt_tbptt_steps = T = 16
B_stream = N_micro / T = 8
```

一个训练 microbatch 的逻辑布局为：

```text
[B_stream=8, T=16, ...]
```

其中：

- `B_stream=8`：8 条相互独立的 episode stream；
- `T=16`：每条 stream 内沿 episode chronology 串行推进 16 个 control/sample steps；
- TTT 只在每条 stream 的时间维上递归；8 条 stream 在 batch 维并行；
- 16 步 Local readout 产生后，将 `[8,16,...]` flatten 为 `128` 个 Cosmos samples，Cosmos backbone 对这 128 个 samples 一次并行 forward；
- 因而不是让 Cosmos 在一个 slot 内串行执行 16 次。

最重要的新 hard contract：

> **任何 episode 第一次进入训练 stream 时，其 `start_step` 必须为 `0`，并由当前 learned initialization `W̄0` 创建该 episode 的 runtime fast state。禁止 fresh episode 直接从 `step > 0` 开始。**

---

# 1. 第一个 microbatch：所有 fresh slot 都从 step 0 开始

若 episode queue 经 episode-level shuffle 后首先分配：

```text
E12, E33, E4, E99, ..., E81
```

则 fresh stream 初始化必须是：

```text
microbatch 0
────────────────────────────────
slot 0: E12 step 0~15   <- clone current W̄0
slot 1: E33 step 0~15   <- clone current W̄0
slot 2: E4  step 0~15   <- clone current W̄0
...
slot 7: E81 step 0~15   <- clone current W̄0
```

这里的 `0~15` 是 **同一 slot 内的 chronology scan**：

```text
step0 -> step1 -> ... -> step15
```

TTT 对每个 slot 的 fast state 串行更新；8 个 slot 同时并行执行同一时间位置的 batched KVB/update/read。完成 16 步后得到：

```text
M_local [8,16,K_local,32]
```

然后：

```text
Cosmos samples [8,16,...]
M_local       [8,16,K_local,32]
        |
        +-- flatten stream/time
        v
Cosmos samples [128,...]
M_local       [128,K_local,32]
        |
        v
one Cosmos batch-128 forward
```

因此 `8 x 16` 是为了把 TTT 的 16-step recurrent graph 收在一个 packed microbatch 内，同时保持 Cosmos 的 128-sample 并行度。

---

# 2. 同一 episode 后续 segment：只能严格承接前序 fast state

若 `microbatch 0` 后 episode 未结束，则下一 microbatch 必须继续：

```text
microbatch 1
────────────────────────────────
slot 0: E12 step 16~31  <- carry detach(W_fast after step15)
slot 1: E33 step 16~31  <- carry detach(W_fast after step15)
slot 2: E4  step 16~31  <- carry detach(W_fast after step15)
...
slot 7: E81 step 16~31  <- carry detach(W_fast after step15)
```

再下一轮：

```text
microbatch 2
────────────────────────────────
slot 0: E12 step 32~47
slot 1: E33 step 32~47
...
```

因此，`start_step=16/32/...` 本身不是非法；非法的是：

```text
fresh episode E + start_step > 0 + clone(W̄0)
```

合法的 `start_step>0` 必须同时具备：

```text
same episode_id
previous segment exactly ends at start_step-1
previous fast state provenance exists
previous fast state numeric value is carried after TBPTT detach
```

形式化：

```text
first admission of episode E:
    start_step(E) == 0
    W_fast(E) = clone(W̄0_current)

continued admission of episode E:
    start_step_new == end_step_prev + 1
    W_fast_in == detach(W_fast_out_prev)
```

禁止随机选择 episode 中间位置作为一个新的 fast-state lifecycle 起点。

---

# 3. TBPTT boundary 与 memory lifecycle

对一个足够长的 episode：

```text
segment 0: step 0~15
segment 1: step16~31
segment 2: step32~47
...
```

其中：

```text
step0 admission:
    W_fast <- clone(W̄0_current)

step0~15:
    inner update/read recurrently

end of segment:
    detach graph only
    keep numeric W_fast

step16~31:
    continue from detached numeric W_fast
```

因此：

```text
TBPTT boundary:
    detach(W_fast)
    numeric state persists

Episode boundary:
    terminate/discard old W_fast
    next episode clones current W̄0
```

两者不可混淆。

`optimizer.step()` 也不修改当前 runtime `W_fast`；它只更新 slow parameters，包括 learned `W̄0`、`theta_K/theta_V/theta_Q` 等。一个已经开始的 episode 不会因为 `W̄0` 后续被 optimizer 更新而重新初始化。

---

# 4. Episode tail：首版使用后 padding，不在 segment 中途 rebind 新 episode

若某条 stream 当前 episode 在 16-step segment 中提前结束，例如：

```text
slot 3: E7 step 32~40, then done
```

首版固定采用：

```text
slot 3 segment:
    E7 step32
    ...
    E7 step40  done=True
    PAD
    PAD
    ...
    PAD
```

padding rows：

- `valid=false`；
- 不更新 fast state；
- 不产生有效 Local token；
- 不贡献对应 Cosmos outer loss；
- 不允许在同一个 16-step segment 剩余位置直接绑定下一 episode。

segment 完成后旧 episode 的 `W_fast` 被终止/丢弃。下一 microbatch 才允许该 slot rebind 新 episode：

```text
slot 3: E105 step 0~15
```

并执行：

```text
W_fast(E105) = clone(W̄0_current)
```

训练时此 clone 不得对 `W̄0` 做 detach，否则 outer loss 到 learned initialization 的 meta-gradient 路径会被切断。

---

# 5. Sampler 随机性边界

首版允许：

```text
episode-level shuffle
```

例如新 slot 从等待队列随机/洗牌后选择 `E105`、`E88` 等。

首版禁止：

```text
random episode-internal start offset
```

即禁止：

```text
E105 starts at 37
E88  starts at 12
```

除非未来单独设计并证明 prefix replay / exact state restoration 机制。当前首版统一要求：

```text
Episode-level shuffle
+
Episode-internal strict sequential traversal from step 0 to terminal
```

这保证 learned `W̄0 -> W_fast,1 -> ... -> W_fast,done` 的完整 episodic memory lifecycle 在训练中真实出现，而不是把中间 frame 人为当成新的 memory 起点。

---

# 6. Dataloader / sampler / state-owner 职责

推荐职责边界：

```text
EpisodeStore
    保存完整 episode chronology

EpisodeQueue
    只决定新 episode 的分配顺序 / episode-level shuffle

SegmentSampler / StreamBatcher
    每个 stable slot 维护 episode_id + cursor
    fresh episode -> cursor=0
    continued episode -> cursor=previous_end+1
    每次最多取 T=16 个连续 rows
    tail 不足则 valid padding

TTT state owner
    fresh episode -> clone current learned W̄0
    continued episode -> carry detached previous W_fast
    TBPTT boundary -> detach only
    episode done -> discard old W_fast
```

Dataloader/packer 不应该自己持有或修改 `W_fast` 数值，但必须提供足够 metadata 让 state owner fail-closed 校验 chronology。

至少需要：

```text
episode_id
start_step / step_ids
valid
done / is_episode_end
is_episode_start or equivalent first-admission proof
stream_slot / owner identity
```

---

# 7. 新增 acceptance assertions

在 v0.3.3 §7 A-J 基础上新增：

```text
K. 一个 episode 的 first admission 必须 start_step == 0
L. first admission 必须创建自当前 learned W̄0 的新 W_fast
M. start_step > 0 必须有同 episode 的严格连续前序 segment provenance
N. continued segment 禁止重新 clone W̄0
O. episode tail 首版只 padding，不允许同 segment 中途 rebind 新 episode
P. 新 episode rebind 只能发生在下一 segment，且从 step 0 开始
Q. episode-level shuffle 允许；episode-internal random start 禁止
R. TTT 在 [B_stream,T] 中只沿 T recurrent，Cosmos flatten 后按 B_stream*T 并行
```

任何违反 K-R 的 batch/manifest/packer output 均应 fail closed，而不是自动猜测或修复 chronology。

---

# 8. 最终冻结口径

> **首版训练采用 `B_stream=8, T=16`：每个 fresh episode 第一次进入任意 stream slot 时必须从 step 0 开始，并从当时最新的 learned `W̄0` 创建 runtime fast state；同 episode 后续 segment 只能以严格连续的 step 范围和上一个 segment detach 后的 fast-state 数值继续。TTT 在每个 slot 内沿 16-step chronology 串行、8 个 slot 并行；完成 Local scan 后将 `8 x 16` flatten 为 128 个 Cosmos samples 一次并行 forward。episode 尾部不足 16 步时首版只做 valid padding，下一 episode 只能在下一 segment 从 step 0 重新开始。允许 episode-level shuffle，禁止 fresh episode 从任意 `step>0` 随机起训。**
