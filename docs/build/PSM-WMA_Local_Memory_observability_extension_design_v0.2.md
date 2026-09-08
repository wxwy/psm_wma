# PSM-WMA Local Memory Observability Extension Design v0.2

> 状态：设计修订稿 / review-ready draft
>
> 目的：在不重建平行监控框架的前提下，复用 Cosmos-Framework 已有 callback / W&B / device / norm / grad / data-stat / runtime-probe 基础，补齐 PSM-WMA Local Memory / TTT canonical 路径特有的长期训练可观测性与 chronology Evidence。
>
> 本文档不是 implementation approval，不授权新增训练、GPU、真实数据、preflight、staging、record/refreeze、export/compose 或后续 Gate 执行。

## 0. 修订与盘点基线

v0.2 相对 v0.1 主要修正：

1. 删除旧 active-wiring 词汇 `materialize` / `abort` 作为 canonical 必要事件；
2. trace identity 从旧 `owner / epoch / source_timestep` 改为当前 canonical `SegmentIdentity` / `SegmentBatch` 字段；
3. 补充 `(batch_row, t_index, flat_index)`，用于验证 stream-major flatten ABI；
4. 明确 PAD 通过 segment layout / valid bitmap 被 trace 感知，但不得产生 per-row Local encode/update/read 事件；
5. `local/token_vs_consumer_hidden/l2_ratio` 的 consumer-hidden 取点留到 O2 implementation design 冻结，不在本设计中猜测；
6. 刷新盘点基线。

本修订基于：

- root `wxwy/psm_wma` V2 parent HEAD：`07ebe8ef6b36a655d2fc6a76547199d77f34eb60`
- child/Gitlink `wxwy/cosmos-framework`：`f14a0185976cc94fde1be73028417893b68d5ae2`

当前 canonical CPU core 的权威对象为：

- `SegmentBatch`
- `SegmentIdentity`
- `GAWindowPlan`
- `LocalMemoryTransaction`
- `RankLocalSegmentScheduler`

其中 `SegmentIdentity` 冻结字段为：

```text
slot_id
 episode_id
 category
 cursor
 segment_id
 source_digest
 training_stream_end
```

`SegmentBatch` 另提供 consumer/evidence chronology：

```text
consumer_step
 evidence_valid
 evidence_source_step
```

queue 的 `epoch` 仅是 scheduler provenance/configuration，不属于 segment identity。

当前 child 已存在较成熟的通用观测基础：

- `WandBCallback` / `wandb_log.py`：train/val loss、sub-loss、lr、GradScaler、timer；
- `GradClip`：global/per-mesh pre-clip grad norm、finite sanitize、clip diagnostics；
- `NormMonitor`：parameter / gradient / activation norm 与 max；
- `DataStatsCallback` / `TrainingStatsCallback`：dataset/mode/embodiment exposure 与 loss；
- `DeviceMonitor`：CPU/GPU memory、utilization、temperature、power、clock；
- `IterSpeed` / MFU / OFU 等性能统计；
- R07/R08/R09 runtime probe/capture：machine-readable JSON Evidence、optimizer membership、gradient finite/max、state continuation/reset、snapshot isolation。

因此 Local observability 的原则是：**优先复用已有 observer/sink/collective，新增 Local-specific producer 与 contract trace；不复制已有 logging backend。**

## 1. 当前缺口

### 1.1 W&B 基础存在，但当前 LIBERO Edge recipe 默认没有启用 basic callback

`action_policy_libero_edge_all.py` 为 admission/offline smoke 将 callback 组改为：

```text
optimization + job_monitor
```

而不是 `basic`，因此当前长期训练 recipe 不会自然获得完整 W&B loss/norm/data-stat 面板，只额外保留 `StdoutLossLogger`。

这属于**启用策略问题**，不应通过新建第二套 logger 解决。

### 1.2 NormMonitor 存在，但当前 selector 不覆盖 Local

现有 `NormMonitor._should_track_param()` 只跟踪：

```text
moe_gen
k_norm_und_for_gen
```

因此 Local encoder / TTT slow parameters / local_memory2llm 等不会稳定进入现有详细 norm 统计。

需要将 selector 从硬编码改造成可配置 group/selectors，底层 FSDP/DTensor aggregation 与 W&B sink 保持复用。

### 1.3 Dataset frequency 不是 Local 有效 exposure

Local/TTT 训练真正关心：

```text
batch count
!= admitted evidence rows
!= valid consumer count
!= committed segment count
```

因此现有 DataStats 只能回答“取了多少 batch”，不能回答“Local 实际获得多少有效监督/消费机会”。

### 1.4 缺少 canonical chronology trace

已有 R09 probe 主要用于 bounded smoke / Gate Evidence，尚未形成适用于当前 canonical Local/TTT 长期训练的稀疏 transaction trace。

canonical trace 必须围绕现有 authority 字段，而不是重建 `owner/epoch` 体系：

- segment identity：`slot_id / episode_id / category / cursor / segment_id / source_digest`；
- consumer chronology：`consumer_step / evidence_source_step`；
- microbatch position：`batch_row / t_index / flat_index`；
- GA window：`plan_chain_id / member_index / planned_n_valid / actual_n_valid / attempt`；
- scheduler：admission / commit / target-valid exposure / terminal rebind / training stream end；
- transaction：transient failure / suffix retry / scaler skip / slow optimizer step；
- fast-state pre/post scalar/fingerprint。

queue `epoch` 如需记录，只能作为 optional provenance，不得参与 segment identity 判定。

### 1.5 缺少自动离线 trace validator

当前 probe 会产出 JSON Evidence，但缺少一个独立 validator 把 trace 与 frozen canonical contract 自动对照并给出 fail-closed 结果。

## 2. 设计目标

只新增三类 Local-specific 能力：

1. `LocalMemoryTelemetryCallback`
   - 面向长期训练曲线；
   - 低频、可聚合；
   - 输出到现有 W&B / stdout sink；
   - 不改变训练数学语义。

2. `LocalMemoryContractTrace`
   - 面向 chronology / transaction Evidence；
   - 稀疏 JSONL；
   - 默认关闭；
   - 仅 capture 已存在 authority / runtime / scheduler / transaction 状态，不成为新的 authority。

3. `validate_local_memory_trace.py`
   - 纯离线 validator；
   - 读取 trace；
   - 不加载模型，不执行训练；
   - 对 frozen contract 做 deterministic fail-closed 校验。

不新增：

- 新 W&B backend；
- 新 distributed logging framework；
- 新 device monitor；
- 新 global grad-norm 实现；
- 新 dataset statistics framework；
- 任何第二套 Local chronology authority。

## 3. Telemetry 指标

### 3.1 训练基础指标：直接复用

直接复用现有：

```text
train/loss
val/loss
optim/lr
optim/grad_scale
clip_grad_norm/global
timer/*
DeviceMonitor/*
mem/*
MFU / iter speed
```

### 3.2 Local slow-parameter group

需要通过可配置 selector 统计：

```text
local/slow/encoder_param_l2
local/slow/encoder_grad_l2
local/slow/core_param_l2
local/slow/core_grad_l2
local/slow/projector_param_l2
local/slow/projector_grad_l2
local/slow/modality_embed_param_l2
local/slow/modality_embed_grad_l2
```

实现应尽量复用 `NormMonitor` 的 local-shard + all_reduce 逻辑；不得独立 gather full params。

### 3.3 Local token / representation scale

低频统计：

```text
local/token/l2_mean
local/token/l2_max
local/token/abs_max
local/token/present_fraction
```

目的：快速发现 Local token 数值尺度过小、过大、恒零或长期 absent。

候选指标：

```text
local/token_vs_consumer_hidden/l2_ratio
```

但该 ratio **不得在本设计中预设 consumer hidden 取点**。O2 implementation design 必须明确：

- 哪一层；
- Local prefix 注入前还是注入后；
- 是否是 native hidden / normalized hidden；
- 是否会引入额外 forward/read。

在取点未冻结前，该指标不得作为 Gate acceptance 必需项。

默认只记录聚合 scalar，不持久化原始 token。

### 3.4 Fast-state telemetry

只记录 detached scalar/fingerprint：

```text
local/fast/state_l2_mean
local/fast/state_l2_max
local/fast/update_l2_mean
local/fast/update_l2_max
local/fast/finite_fraction
local/fast/initialized_fraction
local/fast/segment_progress_mean
```

禁止：

- telemetry 为统计而额外执行一次 fast update；
- telemetry 触发旧路线 replay/materialize 或任何第二次 canonical compute；
- telemetry 读取本应因 invalid/PAD 而不可读的数据；
- telemetry 改写 fast state。

### 3.5 Exposure / scheduler telemetry

必须区分 batch exposure 与 Local valid exposure：

```text
local/exposure/admitted_segments
local/exposure/valid_consumers
local/exposure/pad_rows
local/exposure/segments_committed
local/exposure/terminal_remainders
local/exposure/by_category/*
local/exposure/by_slot/*
```

直接复用 `RankLocalSegmentScheduler.snapshot()` 中已有 authority 状态：

```text
target_distribution
cumulative_valid_consumer_exposure
admission_order
committed_identities
stable_slots
queue_seed
queue_epoch
queue_permutation
stream_closed
```

可导出：

```text
local/scheduler/target_exposure/*
local/scheduler/actual_valid_exposure/*
local/scheduler/deficit/*
```

其中 deficit 如实现需要计算，只能由 scheduler 提供或调用与 `admit()` 同源、纯只读的 frozen helper；observer 不得复制一份自己的调度算法并将其结果当 authority。

### 3.6 Transaction / retry summary

聚合计数：

```text
local/txn/backward_success
local/txn/commit
local/txn/transient_failure
local/txn/suffix_retry_begin
local/txn/scaler_skip
local/txn/slow_optimizer_step
local/txn/retry_exhausted
local/txn/identity_failure
local/txn/numerical_failure
local/txn/outer_failure
```

这些 key 的语义必须直接来自 canonical `GAWindowPlan` / `LocalMemoryTransaction` / scheduler transition 或 production integration 中对应的 frozen transition，不允许 logger 自己根据异常字符串猜测。

## 4. Contract Trace

### 4.1 Trace schema

每行一个 JSON object。建议 schema：

```json
{
  "schema": "psm_local_trace_v2",
  "event": "scheduler_commit",
  "global_step": 120,
  "microbatch": 7,
  "plan_chain_id": "...",
  "attempt": 0,
  "member_index": 2,
  "slot_id": 3,
  "episode_id_hash": "sha256:...",
  "category": "libero_goal",
  "cursor": 32,
  "segment_id": 17,
  "source_digest": "sha256:...",
  "training_stream_end": false,
  "batch_row": 3,
  "t_index": 5,
  "flat_index": 53,
  "consumer_step": 37,
  "evidence_source_step": 36,
  "consumer_valid": true,
  "evidence_valid": true,
  "planned_n_valid": 128,
  "actual_n_valid": 128,
  "state_before": "sha256:...",
  "state_after": "sha256:..."
}
```

约束：

- `slot_id / category / cursor / segment_id / source_digest / training_stream_end` 必须直接来自 canonical `SegmentIdentity`；
- `consumer_step / evidence_source_step / consumer_valid / evidence_valid` 必须直接来自 `SegmentBatch`；
- `flat_index = batch_row * T + t_index`，其中 `T` 为该 `SegmentBatch` 的 actual segment length；
- `queue_epoch` 仅允许作为 optional provenance 字段，例如 `queue_epoch_provenance`，不得参与 segment identity；
- `episode_id` 默认用稳定 hash，禁止输出原始数据路径、instruction、图像内容等敏感/大 payload；
- state fingerprint 只能来自已存在 fast state 的 detached bytes/scalar view，不得为了 fingerprint 重跑 update。

### 4.2 Segment layout event

为了同时满足：

1. validator 能知道 invalid/PAD 的位置；
2. invalid/PAD 不进入 Local encode/update/read；

每个 segment 应有一个轻量 `segment_layout` 事件，包含：

```text
slot_id
 episode_id_hash
 cursor
 segment_id
 segment_length
 consumer_valid_bitmap
 evidence_valid_bitmap
 consumer_step[]
 evidence_source_step[]
 pad_count
```

`segment_layout` 是 metadata trace，不是 Local row compute event。它不得读取 invalid/PAD 的 visual/action tensor。

因此：

- PAD 可以在 `segment_layout` 中被感知；
- PAD 不得产生 `consumer_read` / `local_encode` / `fast_update` 等 per-row Local 事件；
- Gate/debug 模式如需证明 PAD no-op，可额外记录 bounded `noop_state_fingerprint`，其输入只能是 pre/post fast state，不得读取 PAD payload。

### 4.3 Canonical 必要事件

canonical event namespace：

```text
segment_layout
segment_admit
consumer_read
backward_success
scheduler_commit
transient_failure
suffix_retry_begin
scaler_skip
slow_optimizer_step
terminal_rebind
training_stream_end
failure
```

说明：

- 不再把旧 active-wiring 的 `materialize` / `abort` 放入 canonical 必要事件；
- `segment_admit` 对应 scheduler admission；
- `backward_success` 对应一次 GA member 成功完成 backward 并满足 planned/actual count；
- `scheduler_commit` 对应 `RankLocalSegmentScheduler.commit()` 语义；
- `transient_failure` + `suffix_retry_begin` 对应 `LocalMemoryTransaction.fail_transient()` 与 `GAWindowPlan.suffix_after_failure()`；
- `scaler_skip` 对应 slow side 不前进、已成功 fast chronology 保留的语义；
- `slow_optimizer_step` 仅代表真实 slow optimizer/LR step；
- `terminal_rebind` / `training_stream_end` 对应 scheduler 的同名 authority transition。

事件必须由唯一 authority 发出，或由 observer 对其已发生状态做无歧义只读映射；不得创建第二套状态机。

### 4.4 旧 probe/旧路线兼容映射

历史 R07/R08/R09-A1/B1/B2 probe 可继续保留原 schema 作为历史 Gate Evidence。

如需要统一离线查看，可提供**只读 adapter**：

```text
legacy event/schema -> observability viewer field
```

但：

- legacy adapter 只用于查看历史 Evidence；
- 不得让 canonical producer 伪造 `materialize/abort/owner-epoch`；
- canonical validator 只以 `psm_local_trace_v2` 为正式输入。

### 4.5 采样策略

默认：

- telemetry：每 `logging_iter` 或其整数倍；
- chronology trace：关闭；
- debug/Gate run：可按 `slot_id / category / first-N-segment / deterministic sample` 打开；
- failure：允许强制 flush 最近 bounded ring-buffer，但不能捕获原始大 tensor。

## 5. Offline Validator

`validate_local_memory_trace.py` 至少验证：

### R1 — schema / required fields

- schema 必须是受支持版本；
- unknown event fail closed；
- 每种 event 的 required fields 缺失 fail closed。

### R2 — SegmentIdentity 一致性

同一 segment 的：

```text
slot_id / episode_id_hash / category / cursor / segment_id / source_digest
```

必须一致；queue epoch 不得被当作 identity 成员。

### R3 — flatten ABI

对每个 row position：

```text
flat_index == batch_row * segment_length + t_index
```

并检查 common gather 后 payload / Local / identity 的 stream-major 顺序一致。

### R4 — S0 / previous-evidence chronology

对 valid consumer：

- `consumer_step == 0` 时：`evidence_valid == false` 且 `evidence_source_step == -1`；
- `consumer_step > 0` 时：`evidence_valid == true` 且 `evidence_source_step == consumer_step - 1`；
- S0 Local 必须 absent；
- 非 S0 valid consumer 必须满足 frozen Local presence contract。

### R5 — PAD / invalid no-read

- PAD 位置必须可由 `segment_layout.consumer_valid_bitmap` 感知；
- PAD 不得出现 `consumer_read` 或其他 Local row-compute event；
- evidence invalid 不得产生 encode/project/read/update event；
- Gate-only `noop_state_fingerprint` 如存在，pre/post 必须 byte-identical。

### R6 — GA planned/actual contract

- `actual_n_valid == planned_n_valid` 才允许 `backward_success`；
- member 顺序必须与 frozen `GAWindowPlan.members` 一致；
- attempt 必须属于 `{0,1}`。

### R7 — commit chronology

- 只有 admitted identity 才能 commit；
- 同一 identity 不得重复 commit；
- `scheduler_commit` 必须紧随该 member 的成功 backward 语义；
- committed valid exposure 必须正数并进入正确 category 累计。

### R8 — suffix retry

- transient failure 只允许创建当前未提交 suffix；
- retry `attempt == 1`；
- suffix members 必须与 `GAWindowPlan.suffix_snapshot` 一致；
- 已 committed prefix 不得 replay/再次 commit。

### R9 — retry exhaustion

attempt1 再发生 recoverable transient 时：

```text
LOCAL_MEM_RETRY_EXHAUSTED
```

不得再出现 nested `suffix_retry_begin`。

### R10 — scaler skip / slow side

scaler skip 时：

- 已成功 fast/scheduler chronology 保留；
- slow partial grads 清除；
- slow optimizer step = 0；
- slow LR scheduler step = 0；
- 不得伪装成 `slow_optimizer_step` success。

### R11 — terminal / stream closure

- `training_stream_end` 只能由 `SegmentIdentity.training_stream_end == true` 触发；
- terminal slot replacement 必须走 `terminal_rebind`；
- stream closed 后未经合法 rebind 不得继续 admission；
- replacement identity 的 slot 必须与 terminal stable slot 一致。

### R12 — sequence closure

trace 结束时：

- 不得有悬空 retry；
- 不得有未闭合 attempt；
- failure code 与 transaction terminal state 必须一致。

输出：

```text
PASS
```

或：

```text
FAIL <rule_id> <slot_id> <segment_id> <event_index> <reason>
```

validator 本身不得访问 GPU/模型/真实数据。

## 6. 与现有 probe 的关系

已有 R07/R08/R09 probe/capture 保留，不直接删除或替换。

复用原则：

- R09 probe 的 optimizer membership / gradient finite/max / JSON Evidence 结构可作为 telemetry/trace 设计参考；
- R09-B2 snapshot/hash isolation 可复用为 non-mutating capture acceptance pattern；
- 长期 telemetry 不应直接把 Gate-specific probe 扩成常驻大对象；
- Gate probe 继续回答“某一次 bounded run 是否满足验收”；
- observability extension 回答“长期训练是否稳定、是否偏离 frozen canonical chronology”。

## 7. 推荐实现切分

本设计只冻结：

- observability 总原则；
- telemetry 指标集合与分组；
- canonical trace schema / event namespace；
- validator rule 集；
- O1–O5 实现切分。

不在本设计直接授权任何 implementation。

### O1 — 纯 selector / logging reuse

- 让 `NormMonitor` 支持 configurable selectors/groups；
- 不改 Local runtime；
- 为 Local slow group 增加 norm 曲线；
- CPU/static + callback unit tests。

### O2 — Local telemetry producer

- 新增 `LocalMemoryTelemetryCallback`；
- 只读已存在 output/runtime/scheduler counters；
- W&B 可关闭；
- smoke 下 stdout/JSON scalar evidence 可验收；
- 如需要 `token_vs_consumer_hidden`，在本 Gate 单独冻结 hidden 取点。

### O3 — Contract trace

- 增加 bounded trace sink；
- 先覆盖 synthetic CPU canonical chronology；
- 证明 capture non-mutating、无 authority duplication；
- 首轮只支持 `psm_local_trace_v2`。

### O4 — Offline validator

- 纯 CPU；
- fixture-driven；
- 优先直接复用/参数化 canonical CPU core 现有场景：S0、non-S0、PAD、terminal、GradScaler skip、suffix retry、attempt1 failure、identity mismatch、stream end/rebind；
- 不复制 production runtime 算法来生成“期望结果”。

### O5 — recipe enablement

只有在后续明确 Gate 授权下，才讨论：

- 长期训练是否重新启用 W&B basic subset；
- callback 频率；
- trace sampling；
- multi-rank / production recipe wiring。

## 8. Acceptance 原则

任何 observability implementation 必须满足：

1. **observer 不成为 authority**：不得定义 segment identity / scheduler / retry / terminal semantics；
2. **identity source-of-truth**：segment identity 必须来自 `SegmentIdentity`；queue epoch 仅 provenance；
3. **non-mutating**：打开/关闭 observability 不改变模型参数、buffer、optimizer、scheduler、RNG、fast state、batch metadata；
4. **no extra read on invalid/PAD**：监控不能破坏 frozen fail-before-read 语义；
5. **no duplicate compute**：不得为了统计重新 encode/project/read/update，亦不得调用已 supersede 路线的 replay/materialize；
6. **bounded overhead**：默认 telemetry 为 scalar 聚合，trace 默认关闭；
7. **distributed-safe**：复用已有 collective 语义，避免 callback 自建不对称 collective；
8. **W&B optional**：`wandb.run is None` 时训练仍正常，accumulator 必须正常 flush/reset；
9. **machine-readable evidence**：关键 contract trace 与 validator 输出可离线审计；
10. **trace cannot drive execution**：任何 trace/validator 结果不得在运行时反向决定 admission/commit/retry/reset。

## 9. 推荐 Dashboard 结构

W&B/等价 sink 建议分 6 组，而不是把所有 scalar 混在一页：

### A. Training Health

```text
loss
lr
grad_scale
global_grad_norm
iter_time
GPU memory/utilization
```

### B. Local Slow Learning

```text
encoder/core/projector/modality param norm
encoder/core/projector/modality grad norm
```

### C. Local Fast Memory

```text
state norm
update norm
finite fraction
initialized fraction
segment progress
```

### D. Representation Use

```text
Local token norm
Local present fraction
consumer hidden ratio（O2 冻结后）
```

### E. Exposure / Scheduler

```text
target category exposure
actual valid-consumer exposure
deficit
admitted/committed segments
PAD ratio
terminal remainder ratio
```

### F. Transaction Health

```text
commit count
transient failure
suffix retry
retry exhausted
scaler skip
slow optimizer step
identity/numerical/outer failures
```

## 10. v0.2 结论

当前代码并不缺一套通用监控系统。更合适的工程方向是：

```text
Cosmos existing observability
    + configurable Local selectors
    + Local telemetry producer
    + canonical sparse chronology trace
    + offline validator
```

而不是：

```text
second W&B/logger/device/norm framework
```

本修订明确以当前 canonical `SegmentIdentity / SegmentBatch / GAWindowPlan / LocalMemoryTransaction / RankLocalSegmentScheduler` 为唯一观测语义来源；旧 active-wiring 的 `materialize / abort / owner-epoch` 不再进入 canonical trace contract。

后续仍应按 Gate 拆小：优先 O1，再 O2/O3/O4，最后才讨论 O5 production recipe enablement。