# PSM-WMA Temporal Local Memory 详细设计补充 v0.3.5

**日期**：2026-09-07  
**状态**：rolling user-directed canonical training-semantics refinement；**尚未收敛为最终 canonical v1.0**；implementation 前仍需按项目 Gate 纪律独立审核  
**适用分支**：根仓 `V2`  
**上游版本**：`docs/build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.4.md`  
**当前根仓参考基线**：`f55d5f7938bf1232ff338be724b4f125dabfa726`  
**当前 Cosmos Gitlink 参考基线**：`80aec090688e3c710c41e1dfd86b6500773db2c7`

> 本文件继续收紧 v0.3.4 的 `B_stream x T -> Cosmos consumer batch` 训练路线，重点冻结：**时间索引、首轮 evidence feature set、通用 weighted episode-stream scheduler、episode tail/padding、consumer batch/effective batch 口径、valid-consumer loss normalization、flatten ABI、fast-state/slow-optimizer 生命周期、错误事务、checkpoint/resume、distributed 与 inference parity**。  
> v0.3.2 的 multi-slot K/V/Q 数学、v0.3.3 的 Cosmos/TTT 双时间轴与 past-only 原则、v0.3.4 的 fresh episode 从 step 0 开始继续有效；与本文冲突时以本文为准。  
> 当前旧 active-wiring 的 `1 micro-batch = 1 evidence row` / closing-row witness-materialization 路线与本文的 segment-level production training 存在结构差异，后续必须另起 supersession/implementation Gate 显式迁移，禁止静默混用。  
> 本文件仍是**持续修订中的附加说明**；本轮只把用户已经确认的“七及后续”工程口径继续写入 v0.3.5，**暂不收敛、不新建最终 canonical contract**。  
> 本文件不授权 runtime/packer/trainer 代码变更、真实 checkpoint I/O、GPU、训练、评测或推理。

---

# 0. Canonical 训练单位与当前固定值

后续文档、代码、日志必须区分以下单位：

```text
control step t
    episode 中的真实时序位置

Cosmos consumer S_t
    当前 observation/z0 条件 + native future/action target 的一个 Cosmos sample

completed evidence e_t
    step t 已完成后，由当时 causal observation + 实际 executed action 构成的一条 Local evidence

TTT scan block / TBPTT segment
    每条 stream 最多 T 个连续 consumer positions；首版 T=16

packed microbatch
    B_stream 条 stream x T 个 logical consumer positions；首版 8 x 16 = 128 nominal positions

optimizer update
    Cosmos native gradient-accumulation window结束后的一次 slow-parameter optimizer.step()
```

当前首版：

```text
T = ttt_tbptt_steps = 16
N_consumer_nominal_per_micro = 128
B_stream = N_consumer_nominal_per_micro / T = 8
```

重要：`B_stream=8` 不是 Cosmos micro batch size；Cosmos/optimizer 口径中的 nominal micro batch 仍是最多 `128` 个 consumer samples。

---

# 1. 时间索引：只采用一种 canonical notation

为彻底消除 `W0/W1` 的歧义，runtime fast state 下标统一表示“最后已经处理完的 evidence index”。

episode 开始、尚未写入任何 evidence 时：

```text
W_fast[-1] := clone(W_bar_0_current)
```

每当 completed evidence `e_t` 可用：

```text
K_t = theta_K(e_t)
V_t = theta_V(e_t)
Q_t^k = theta_Q(e_t) + r_k

W_fast[t] = Update(W_fast[t-1], K_t, V_t)
M_{t+1}   = Read(W_fast[t], Q_t)
```

因此 consumer `S_t` 的正式关系为：

```text
W_fast[t-1] = Update(W_fast[t-2], e_{t-1})
M_t         = Read(W_fast[t-1], Q_{t-1})
S_t         consumes M_t
```

不得再把 `ReadAfterUpdate(e_{t-1}, W_fast[t-2])` 当作工程 ABI；若数学叙述使用复合函数，必须同时明确 read 发生在 update 后得到的 `W_fast[t-1]` 上。

## 1.1 Fresh episode 第一段的精确 off-by-one

第一段 consumer：

```text
S0  S1  S2  ... S15
```

对应 TTT evidence：

```text
NONE  e0  e1  ... e14
```

即：

```text
S0  : Local absent；W_fast[-1] = clone(W_bar_0)
S1  : e0  -> W_fast[0]  -> M1
S2  : e1  -> W_fast[1]  -> M2
...
S15 : e14 -> W_fast[14] -> M15
```

所以 fresh episode 的第一个 `T=16` scan block 有 16 个 valid Cosmos consumers，但只有 15 次有效 TTT inner update；segment 结束时若 episode 未结束，carry 的 numeric state 是 `W_fast[14]`。

下一段：

```text
S16 ... S31
```

对应：

```text
e15 ... e30
```

从 `W_fast[14]` 继续，完整执行 16 次 update，段尾得到 `W_fast[30]`。

因此 `ttt_tbptt_steps=16` 的正式语义是：

> **一条可微 fast-state graph 最多覆盖 16 个 chronological scan/consumer positions；因 fresh `S0` 没有 `e_-1`，实际有效 inner-update 次数可以少于 16。**

---

# 2. 首轮 canonical evidence：取消 H-history、state、dt、age 神经特征

v0.3.4 后不再为每个 consumer 构造一个长度 `H=16` 的历史窗口。TTT 自身沿 episode 顺序持续携带 memory，因此首轮正式 evidence 简化为：

```text
e_t = LocalEvidenceEncoder_v1(
    visual_summary_t,
    executed_action_t,
)
```

当前固定：

```text
visual_summary_t : required, causal, D_v=96（当前 LIBERO z0 causal summary 路线）
executed_action_t: required, D_action=10
robot state      : OFF for first canonical GPU smoke
dt neural input  : OFF
age neural input : OFF
```

`timestamp`、相邻 timestamp delta、source indices 仍必须保留为 chronology/audit metadata，但首轮不进入神经网络。

原因：在固定 cadence 的同 episode 顺序 traversal 中，每次新增的 evidence 总是相邻 completed step；原 R08 `history_dt_s = timestamp_anchor - timestamp_history` 与 `age_steps` 是 H-window 相对当前 anchor 的历史距离，取消 H-window 后不再携带首轮有效信息。

若未来真实机器人存在丢帧、变控制周期、异步采样，再通过独立设计 Gate 打开 `dt` 特征。

实现约束：当前 `LocalEvidenceEncoder` 仍有 `age_embedding/dt_proj/state` 接口；v0.3.5 production 路径必须显式支持 feature disable，禁止用“给可训练分支喂常数 0/假 age”来伪装关闭。

---

# 3. Dataloader 抽象：Weighted Episode-Stream Scheduler

不得把采样策略写死成 LIBERO 四 suite 的 `2 streams/suite` 或 `1 microbatch/suite`。统一采用：

```text
TargetDistribution
        ↓
WeightedDeficitScheduler
        ↓
EpisodeQueue[category]
        ↓
StableStreamSlot
        ↓
strict episode chronology from step0 to training_stream_end
```

`category` 是配置定义的采样平衡单位，可取：

```text
LIBERO: suite
RoboCasa: task（例如18 tasks）
多数据集训练: dataset
多层训练: (dataset, task)
```

## 3.1 Target distribution

若显式给定权重 `w_c`：

```text
p_c = w_c / sum_j w_j
```

否则允许按 category 的 valid Cosmos consumer 数 `N_c` 做 temperature sampling：

```text
p_c = N_c^alpha / sum_j N_j^alpha
```

其中：

```text
alpha = 0   -> category/task/suite uniform
alpha = 1   -> natural consumer-proportional distribution
0<alpha<1   -> temperature-balanced compromise
```

`N_c` 必须按真实 valid Cosmos consumer anchors 统计，不按 episode 个数统计。

层级采样允许：

```text
p(dataset, task) = p(dataset) * p(task | dataset)
```

## 3.2 Scheduler 决策边界

stable slot 一旦绑定某 episode：

```text
category / episode_id 固定
cursor 严格连续推进
直到 training_stream_end
```

中途不得为了“平衡 batch”切换 category/episode。

只有 episode 结束、且当前 TTT segment 已关闭后，该 slot 才变成 free；下一个 segment 开始前由 weighted-deficit scheduler 根据累计 **valid consumer exposure** 选择下一 category，再从该 category 的 seeded shuffled episode queue 取一个 fresh episode，且从 `step0` 开始。

平衡是长期 soft target；episode continuity 是 hard contract。

## 3.3 与 B_stream / GA / task 数解耦

不要求：

```text
B_stream % N_category == 0
GA % N_category == 0
(B_stream * GA) % N_category == 0
```

当 category 数大于 `B_stream`（例如 RoboCasa 18 tasks vs B_stream=8）时，一个 microbatch 不可能覆盖所有 task；scheduler 只需保证长期累计 valid-consumer exposure 接近 `p_c`。

因此 suite/task balance 不再依赖当前 `GA=16` 或 `B_stream=8` 的整除巧合。

---

# 4. Episode scheduler fail-closed 规则

每个 slot 必须满足：

```text
fresh episode first admission:
    start_step == 0
    W_fast[-1] = clone(current W_bar_0)

continued episode:
    start_step_new == end_step_prev + 1
    same episode_id
    same stream_slot ownership
    state_in == detached numeric state_out of previous segment
```

禁止：

```text
fresh episode + start_step > 0
continued episode重新 clone W_bar_0
episode-internal random start
跨 episode carry old W_fast
```

## 4.1 Stateful path 禁止随机 load-failure resampling

普通 i.i.d. dataset 可以在单 sample load 失败后随机换 index；TTT stateful chronology 路径禁止。

```text
load/decode/cache identity failure
    -> fail segment / fail closed（首版可直接 process-fatal）
```

不得：

```text
E12 step38 load失败 -> 随机换 E99 step7
```

否则会污染 fast-state chronology。

---

# 5. Episode tail：首版保留 logical padding，不做 block 内 episode rebind

从工程可审计性优先，首版继续采用 v0.3.4 tail policy：

```text
一个 stream slot 的一个 T=16 scan block 最多属于一个 episode
```

例如：

```text
slot3:
    E7 step32 ... step40
    PAD
    PAD
    ...
```

对应：

```text
consumer_valid = 1 ... 1 0 ... 0
```

PAD position：

```text
不产生真实 consumer
不生成 evidence
不做 inner update
不改变 W_fast
Local absent
不贡献 Cosmos outer loss
```

segment 结束且 `E7` 已到 training_stream_end：

```text
discard E7 runtime W_fast
slot3 becomes free
```

下一 microbatch/segment 才允许 slot3 由 scheduler rebind 新 category/episode：

```text
new episode must start from step0
W_fast[-1] = clone(current W_bar_0)
```

禁止首版优化：

```text
E7 tail | 同一个T=16 block中立即拼接 E105 step0...
```

因为这会要求 block 内 row-wise reset、多个 episode graph、额外 provenance 与更多 autograd 边界，首版不采用。

---

# 6. Logical padding 与 Cosmos consumer batch

TTT chronology 保持固定 logical shape：

```text
[B_stream=8, T=16]
```

但 PAD 不应强迫 Cosmos 计算虚假 sample。首版优先实现：

```text
TTT logical scan [8,16]
        ↓
M_local [8,16,K_local,32]
consumer_valid [8,16]
        ↓
stream-major flatten
        ↓
gather consumer_valid == True
        ↓
Cosmos real batch N_valid_micro <= 128
```

因此：

```text
N_consumer_nominal_micro = B_stream * T = 128
N_valid_micro            = sum(consumer_valid)
```

正常 full segment 时两者相等；含 episode tail 时实际 Cosmos batch 可以小于128。

如果现有 Cosmos packer 无法 gather variable valid batch，必须另起 implementation design 明确等价 mask 方案；禁止默认为 PAD 构造可训练 zero sample。

---

# 7. Batch-size / effective-batch 口径与 loss normalization

`B_stream x T` 只是原 Cosmos consumer microbatch 的 chronology factorization，不改变 slow optimizer 对 consumer sample 的基本定义。

单 rank：

```text
nominal consumer microbatch = B_stream * T
当前 = 8 * 16 = 128
```

若一个 optimizer update 包含 `GA` 个 microbatches：

```text
nominal consumers/update = 128 * GA                # 仅当全部full时等于实际值
actual consumers/update  = sum_mu N_valid_micro[mu]
segments/update          = B_stream * GA            # nominal stream segments
```

多 rank：

```text
actual global consumers/update
    = sum_rank sum_mu N_valid(rank, mu)
```

实验/日志必须同时报告：

```text
B_stream
T
N_consumer_nominal_micro
N_valid_micro（至少 tail 时）
GA
world_size
actual valid consumers / optimizer update
```

不得只写 `effective batch = B_stream * GA`；`B_stream` 是 episode-stream width，不是 Cosmos sample batch size。

## 7.1 Valid-consumer weighted outer loss

含 tail 时不能把 `103-valid` microbatch 与 `128-valid` microbatch 的 mean loss 等权累积。canonical optimizer-window objective 定义为：

```text
L_window
  = sum_{mu} sum_{i in valid(mu)} l_{mu,i}
    / sum_{mu} N_valid_micro[mu]
```

若 native microbatch loss `L_mu_native` 是该 microbatch valid consumers 的 mean，则单卡每次 backward 的等价 scale 为：

```text
scale_mu = N_valid_micro[mu] / N_valid_window
loss_for_backward = scale_mu * L_mu_native
```

其中：

```text
N_valid_window = sum_{mu=1..GA} N_valid_micro[mu]
```

因此 scheduler/trainer 在一个 GA window 开始 backward 前，必须能得到该 window 的各 microbatch `valid_count`（可先规划 segment metadata，不要求提前加载全部 tensor）。

当所有 microbatch 都是128 valid时：

```text
scale_mu = 1 / GA
```

精确退化为原生固定 microbatch 的 gradient-accumulation 语义。

多 rank 若 DDP 对 rank gradient 做 mean，则为得到全局 valid-consumer mean，rank r / microbatch mu 应使用等价：

```text
scale_{r,mu} = world_size * N_valid[r,mu] / N_valid_global_window
```

其中 `N_valid_global_window` 需由 planned count all-reduce/等价机制得到。首轮单 GPU smoke不需要该多卡实现，但后续 distributed Gate 必须遵守。

`L_inner` 不参与上述 outer loss normalization，也不加入 `L_window`。

---

# 8. Flatten ABI 必须固定

逻辑张量：

```text
consumer [B_stream,T,...]
M_local  [B_stream,T,K_local,32]
consumer_valid [B_stream,T]
```

统一采用 stream-major：

```text
flat_index(b,t) = b * T + t
```

当前 `T=16`：

```text
flat 0..15    <- stream0
flat 16..31   <- stream1
...
flat 112..127 <- stream7
```

`consumer / M_local / consumer_valid / provenance` 必须共享完全相同映射；gather valid consumers 也必须沿该 flat order。

必须有 exact round-trip fixture：

```text
b = flat // T
t = flat % T
```

以及 Local-to-consumer identity fixture，防止 memory token 静默串到别的 Cosmos sample。

---

# 9. Production TTT scan：只保留 shifted-evidence + update-then-read

v0.3.5 segment-level production training 不再采用旧 `1 row/microbatch` 路线为跨 microbatch meta-gradient设计的：

```text
detached candidate
closing-row materialize/replay
pre-write witness
```

新路线直接在一个 microbatch 内拿到：

```text
E_prev [B_stream,T,256]
evidence_valid [B_stream,T]
state_in [B_stream,...]
```

并执行：

```text
scan_segment_many(..., create_graph=True)
```

对每个 valid evidence row：

```text
prediction = f_W(K)
L_inner_per_stream = mean_feature((prediction - V)^2)
W_new = W_old - inner_lr * grad_W(L_inner_per_stream)
M = f_{W_new}(Q)
```

必须是 **update-then-read**；batch 维只做并行，不允许先把不同 stream 的 `L_inner` 做 batch mean 后再定义 shared fast update。

fresh `S0`：

```text
consumer_valid = True
evidence_valid = False
Local present  = False
```

tail PAD：

```text
consumer_valid = False
evidence_valid = False
Local present  = False
```

---

# 10. Fast-state lifecycle、backward 与 optimizer

每个 microbatch 的顺序固定为：

```text
1. state owner assemble state_in
   - fresh row: clone current W_bar_0（保留 autograd path）
   - continued row: previous detached numeric W_fast

2. 16-position differentiable TTT scan
   -> M_local
   -> graph-bearing state_out candidate

3. gather valid consumers -> Cosmos forward

4. native outer loss（按 §7 valid-consumer scale）

5. outer backward

6. backward成功后：
   - continued nonterminal stream: detach(state_out) and commit numeric W
   - terminal stream: discard old/new runtime W after segment closes
   - only now advance committed cursor/state ownership

7. slow .grad 可跨 microbatches累积

8. native optimizer boundary:
   optimizer.step / scheduler / zero_grad
```

Hard rules：

```text
fast-state graph不得跨 microbatch boundary
W_fast 必须在 outer backward 之后才 detach/commit
detach 不改变 numeric W
optimizer.step 不修改任何已存在 runtime W_fast
```

`optimizer.step()` 只更新 slow parameters（含 learned `W_bar_0`、theta_K/V/Q、slot queries、Local adapter等）。已开始 episode 不因 `W_bar_0` 更新而重新初始化；只有 fresh episode first admission 才 clone 当时最新 `W_bar_0`。

## 10.1 Learned W_bar_0 的 TBPTT 梯度范围

fresh episode 第一 segment 的：

```text
state_in = clone(W_bar_0)
```

保留到 `W_bar_0` 的 meta-gradient。

后续 segment 从上一个 segment 的 detached runtime state开始，因此：

```text
L_outer(segment > 0) 不反传穿过历史 segment 回到 episode-start W_bar_0
```

即 `W_bar_0` 主要由各 episode 第一 TBPTT segment 的 outer loss学习。这是 canonical TBPTT 语义，不是 gradient bug。

## 10.2 TBPTT 与 gradient accumulation 的严格关系

v0.3.5 后：

```text
TTT graph 生命周期 = 当前一个 [B_stream,T] microbatch
slow gradient 生命周期 = GA 个 microbatches
```

因此：

```text
TTT graph 不跨 microbatch
slow parameter .grad 可以跨 microbatch accumulate
```

例如 `GA=16`：每个 microbatch 都独立完成 TTT scan → Cosmos → backward → detach/commit 当前 8 条 stream 的 W；到第16个 microbatch 后才执行一次 slow `optimizer.step()`。

不得因为 `GA=16` 与 `T=16` 数值相同而把两者合并成同一个 clock。

---

# 11. Fast-state dtype 与 inner-loss reduction

首轮 canonical GPU smoke：

```text
runtime W_fast persistent/storage dtype = fp32
inner fast-MLP compute                 = fp32
```

原因：fast state 规模很小，fp32 开销低，可避免长 episode 每次 inner update 后 bf16 量化累积。

slow Cosmos/adapter mixed precision继续遵循 native recipe。

Inner loss 定义为每条 stream独立、仅 feature mean：

```text
L_inner,b = mean_j((f_{W_b}(K_b)[j] - V_b[j])^2)
```

`grad_W` 对每个 stream自己的 `W_b` 求导；batch size/B_stream 不得改变单条 stream fast update scale。

`L_inner` 只定义 fast-state transition，**永不作为 ordinary auxiliary loss 加入 `L_outer`**。

---

# 12. Error / GradScaler transaction semantics

state/cursor commit 必须 transactional。

### 12.1 Load / forward / inner non-finite / backward exception

首版 fail closed：

```text
不提交 candidate W_fast
不推进 committed cursor
不 rebind新episode
运行可直接 process-fatal
```

禁止在 chronology 已部分推进后“跳过坏 sample继续”。

### 12.2 GradScaler skip

若：

```text
inner/forward state finite
native outer loss finite
backward完整执行
但 GradScaler判定 slow optimizer step需要 skip
```

沿用 Option-B 语义：

```text
TTT runtime W_fast/cursor commit有效
slow optimizer不 step
scheduler不推进
异常/overflow slow grads清理
```

不回滚已完成的 episode memory progression；否则需要回滚整个 accumulation window 的多 stream state，首版不采用。

---

# 13. Checkpoint / resume

已有 slow checkpoint contract继续：

```text
保存 slow W_bar_0 / theta_K/V/Q / slot queries / Local modules / optimizer/scheduler等
不把 runtime W_fast 当作 model parameter/state_dict slow state
```

## 13.1 Canonical GPU smoke

首轮 smoke 明确：

```text
exact mid-episode resume = UNSUPPORTED
```

若进程重启，不声称能从 slow checkpoint恢复正在运行 episode 的 runtime memory。

## 13.2 正式长训前

必须另起 runtime-sidecar Gate，至少保存：

```text
rank
stream_slot
category/dataset/task
episode_id
cursor
committed detached W_fast
episode-queue epoch/permutation/RNG provenance
optimizer iteration
slow checkpoint/config identity
```

sidecar 只允许在所有当前 segment 已 backward、W 已 detach/commit 的安全边界保存。world_size / config / slow-checkpoint identity不一致时 exact resume fail closed。

---

# 14. Distributed ownership

首轮单 GPU smoke不实现多卡，但 contract提前冻结：

```text
B_stream=8 是 per-rank stream width
runtime W_fast 是 rank-local state
W_fast 不 all-reduce
W_fast 不 FSDP shard
不同 rank 的 episode streams必须不重叠
```

只有 slow parameters通过 DDP/FSDP 正常同步。

多卡 category balance按 global valid-consumer exposure 解释；outer loss normalization按 §7.1 global denominator处理。

world size 改变时不得声称可 exact resume 旧 runtime-sidecar stream ownership。

---

# 15. Train / inference causal parity

训练采用 `8 x 16` 只是 offline packing optimization；推理仍逐 control step在线更新：

```text
episode start:
    W_fast[-1] = clone(W_bar_0)

S0:
    Local absent

执行实际 action0
transition完成 -> e0

e0 -> update W_fast[0] -> M1
S1 consumes M1
...
```

若 policy预测 action chunk 但实际 closed-loop 只执行 `q` 步，evidence 中只能写入真实 executed action interval；predicted but unexecuted suffix 永远禁止进入 Local。

训练与推理必须使用同一：

```text
past-only evidence
update-then-read
W_bar_0 episode init
W_fast episode persistence/reset
```

---

# 16. 首轮 canonical GPU smoke 固定变量

为避免 chronology、multi-slot、state 等变量同时变化，第一轮 canonical GPU smoke固定：

```text
B_stream = 8
T = 16
N_consumer_nominal_micro = 128
K_local = 1
state feature = OFF
dt feature = OFF
age feature = OFF
runtime W_fast = fp32
inner_lr = 0.1
```

`K_local=4/8`、robot state、dt/irregular-cadence、多卡、runtime-sidecar resume 都是后续独立增量 Gate，不与首次 chronology smoke同时切换。

---

# 17. 新增 fail-closed acceptance assertions

在 v0.3.3/v0.3.4 assertions 基础上，后续 canonical implementation 至少必须证明：

```text
A. fresh episode first admission start_step == 0
B. fresh state由 admission时当前 W_bar_0 创建，训练中不 detach W_bar_0 path
C. continued segment start == previous_end + 1
D. continued segment只能使用同 slot 前序 committed detached W_fast
E. fresh/continued episode不得跨 episode泄漏 W_fast
F. S0 consumer valid但 Local/evidence absent，不伪造 e_-1
G. S_t 的 memory只依赖 e_{t-1} 及更早历史
H. z1..z4 不进入 TTT evidence
I. predicted/unexecuted action suffix不进入 TTT evidence
J. 首轮 evidence只用 causal visual summary + executed action；state/dt/age neural feature关闭
K. load failure不得随机 resample到另一 chronology row
L. tail只 logical padding；同一个 T block不 rebind下一episode
M. PAD不 update W、不产生 Local、不进入 Cosmos loss
N. flatten必须 flat=b*T+t，Local/consumer/provenance exact 对齐
O. TTT recurrence只沿同一 stream 的 T 方向，不跨 stream
P. inner update per-stream独立，scale不随 B_stream变化
Q. L_inner 不加入 L_outer
R. outer backward后才 detach/commit runtime W
S. fast-state graph不得跨 microbatch
T. slow gradient可跨 GA microbatches accumulate
U. optimizer.step 不修改既存 runtime W
V. episode done后才 discard旧 W；下一 fresh episode使用当时最新 W_bar_0
W. nominal/actual consumer count必须分别记录
X. tail 下 outer loss按 valid-consumer exposure归一化；full batch时精确退化为 1/GA
Y. sampling balance按 configurable category target p_c 和累计 valid consumer exposure定义，不依赖 B_stream/GA/task数整除
Z. train/inference causal update/read顺序一致
```

---

# 18. 与旧 active-wiring 的迁移边界

当前 child active lifecycle 仍围绕：

```text
1 micro-batch = 1 native window = 1 evidence row
跨 row累计 segment
closing-window replay/materialize witness graph
```

v0.3.5 的 canonical production training改为：

```text
one microbatch already owns [B_stream,T]
TTT graph在该 microbatch 内完整 materialize
flatten/gather valid consumers后一次 Cosmos forward
one backward closes current TTT graph
state detach/commit after backward
```

因此后续实现前必须有明确的 supersession design：指出哪些旧 lifecycle/manifest/terminal transaction代码保留为 provenance/authority，哪些 production row-wise graph materialization逻辑被删除或旁路。未经该 Gate，不得把 v0.3.5 直接解释为已有 active-wiring 的参数变化。

---

# 19. 当前最终口径（rolling，未收敛）

> **首版 canonical TTT training 以 `N_consumer_nominal_micro=128` 为 Cosmos consumer budget，并将其结构化为 `B_stream=8 x T=16`。每个 episode 首次进入 stream 必须从 step0 开始；时间索引统一为 `W_fast[-1]=clone(W_bar_0)`、`W_fast[t]=Update(W_fast[t-1],e_t)`、`M_{t+1}=Read(W_fast[t],Q_t)`。首轮 evidence 仅由 causal visual summary + executed action 构成，不再使用 per-consumer H-history，也关闭 state/dt/age 神经特征。采样采用与 LIBERO/RoboCasa/多数据集兼容的 weighted episode-stream scheduler，按 configurable target distribution 与累计 valid-consumer exposure 做长期平衡；不要求 task/suite 数整除 B_stream 或 GA。episode tail 首版采用 logical padding，不在同一 T block 中途 rebind 新 episode；PAD 不更新 TTT，并优先在 flatten 后 gather 掉，不送入 Cosmos。含 tail 时 outer gradient accumulation按实际 valid consumers加权，full batch时精确退化为原 `micro_bs x GA` 语义。每个 microbatch的 TTT graph在自身 outer backward 后 detach/commit，runtime W 不经过 optimizer.step；只有 fresh episode使用最新 learned W_bar_0。**

---

# 20. 本轮“七及后续”用户确认补充

本节不是新版本收敛，而是把本轮已确认的工程取舍明确登记到同一个 v0.3.5 中，供后续继续逐项审查。

## 20.1 已确认继续采用的工程口径

以下条目在 v0.3.5 内视为当前默认，不再作为开放二选一：

```text
1. flatten ABI = stream-major，flat(b,t)=b*T+t
2. production training = shifted previous evidence + update-then-read
3. 一个 microbatch 内完成完整 TTT TBPTT graph
4. outer backward 完成后才 detach/commit W_fast
5. TTT graph 不跨 microbatch；slow .grad 可以跨 GA microbatches
6. optimizer.step 不修改既存 runtime W_fast
7. runtime W_fast 首轮使用 fp32
8. L_inner per-stream 独立，且不加入 L_outer
9. tail 首版保留 logical padding；不做 block 内 episode rebind
10. PAD 优先在 Cosmos forward 前 gather 掉
11. outer loss按实际 valid consumer exposure归一化
12. weighted episode-stream scheduler按长期 valid-consumer exposure追踪目标分布
13. forward/inner/backward异常 fail closed；GradScaler skip沿用 Option-B
14. canonical smoke 不支持 exact mid-episode resume；正式长训前再设计 runtime sidecar
15. B_stream 是 per-rank；runtime W_fast 不做 DDP/FSDP 同步
16. train/inference 使用同一 causal update/read顺序
17. 首次 canonical GPU smoke 维持 K_local=1、no-state、no-dt、no-age
```

## 20.2 仍保留为后续逐项审查/实现设计的问题

虽然上述工程方向已经确认，但以下内容仍需在 implementation design / GPU smoke Gate 前做源码级落地设计，不应因为写入 v0.3.5 就视为已实现：

```text
A. 当前 Cosmos packer 是否能直接 gather N_valid_micro<128 的 variable batch；若不能，等价 mask ABI 如何实现
B. native loss 的实际 reduction 点在哪里，§7.1 valid-consumer weighting具体接在哪个 trainer seam
C. GA window 的 planned N_valid_count 如何在不提前加载全部 tensor的情况下可靠获得
D. WeightedDeficitScheduler 的精确状态字段、seeded episode queue、epoch rollover 与 provenance schema
E. 当前 R08 LocalEvidenceEncoder 如何最小改造为真正可关闭 state/dt/age branch，而不是喂常数
F. 旧 active-wiring 中哪些 authority/provenance/transaction组件保留，哪些 row-wise witness graph 逻辑 supersede
G. single-GPU canonical smoke 的显存、吞吐、higher-order gradient 与 W_fast fp32实际实现是否满足预算
H. 正式长训 runtime sidecar、distributed ownership 与 world-size change fail-closed 另起 Gate
```

这些仍属于后续实现前需要继续细化的对象；本文件此时**不收敛为最终 Canonical Training & Runtime Contract v1.0**。
