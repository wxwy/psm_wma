# PSM-WMA Local Memory Observability Extension Design v0.1

> 状态：初版 / design draft
>
> 目的：在不重建一套平行监控框架的前提下，复用 Cosmos-Framework 已有 callback / W&B / device / norm / grad / data-stat / runtime-probe 基础，补齐 PSM-WMA Local Memory / TTT 路径特有的长期训练可观测性与 chronology Evidence。
>
> 本文档不是 implementation approval，不授权新增训练、GPU、真实数据、preflight、staging、record/refreeze、export/compose 或后续 Gate 执行。

## 0. 盘点基线

本初版基于以下仓库状态盘点：

- root `wxwy/psm_wma` V2 HEAD：`5786a43f94080f360063004dbed62e0dc0f67a82`
- child/Gitlink `wxwy/cosmos-framework`：`f14a0185976cc94fde1be73028417893b68d5ae2`

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

已有 R09 probe 主要用于 bounded smoke / Gate Evidence，尚未形成适用于 canonical Local/TTT 长期训练的稀疏 transaction trace：

- owner/epoch/segment identity；
- source timestep；
- admission/materialize/backward/commit chronology；
- valid/PAD；
- GA window/recovery suffix；
- scaler skip / exception resolution；
- terminal reset；
- fast-state pre/post fingerprints。

### 1.5 缺少自动离线 trace validator

当前 probe 会产出 JSON Evidence，但缺少一个独立 validator 把 trace 与 frozen contract 自动对照并给出 fail-closed 结果。

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
   - 仅 capture 已存在的 authority/lifecycle 状态，不成为新的 authority。

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
local/token_vs_consumer_hidden/l2_ratio
```

目的：快速发现 Local token 数值尺度过小、过大、恒零或长期 absent。

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
- telemetry 触发 replay/materialize；
- telemetry 读取本应因 invalid/PAD 而不可读的数据；
- telemetry 改写 fast state。

### 3.5 Exposure / scheduler telemetry

必须区分 batch exposure 与 Local valid exposure：

```text
local/exposure/admitted_rows
local/exposure/valid_consumers
local/exposure/pad_rows
local/exposure/segments_started
local/exposure/segments_committed
local/exposure/terminal_remainders
local/exposure/by_suite/*
local/exposure/by_owner_bucket/*
```

如果 frozen scheduler 暴露 target/deficit，则可记录：

```text
local/scheduler/target_exposure
local/scheduler/actual_valid_exposure
local/scheduler/deficit
```

observer 只读 scheduler 的既有 snapshot，不自行重新计算/定义调度权威。

### 3.6 Transaction / retry summary

聚合计数：

```text
local/txn/success
local/txn/scaler_skip
local/txn/exception
local/txn/recovery_suffix
local/txn/retry_exhausted
local/txn/identity_failure
local/txn/numerical_failure
local/txn/outer_failure
```

这些 key 的语义必须直接来自现有 canonical lifecycle/runtime resolution，不允许 logger 自己根据异常字符串猜测。

## 4. Contract Trace

### 4.1 Trace 事件模型

建议每行一个 JSON object：

```json
{
  "schema": "psm_local_trace_v1",
  "event": "commit",
  "global_step": 120,
  "microbatch": 7,
  "owner": "...",
  "epoch": 3,
  "segment_id": "...",
  "source_timestep": 47,
  "valid": true,
  "terminal": false,
  "attempt": 0,
  "state_before": "sha256:...",
  "state_after": "sha256:..."
}
```

owner 可使用稳定脱敏 identity/hash；默认禁止把数据路径、原始 instruction、图像内容写入 trace。

### 4.2 必要事件

```text
segment_begin
admit
consumer_read
materialize
backward_observed
commit
abort
terminal_reset
scaler_skip
recovery_begin
recovery_commit
failure
```

事件名必须由唯一 runtime/lifecycle authority 发出或由 observer 对其只读状态映射；不得创建第二套状态机。

### 4.3 采样策略

默认：

- telemetry：每 `logging_iter` 或其整数倍；
- chronology trace：关闭；
- debug/Gate run：可按 owner / first-N-segment / deterministic sample 打开；
- failure：允许强制记录最近 bounded ring-buffer，但不能捕获原始大 tensor。

## 5. Offline Validator

`validate_local_memory_trace.py` 至少验证：

1. owner 内 source timestep 单调且无跨 epoch 污染；
2. S0/首 consumer 不读取未来 evidence；
3. invalid/PAD 不出现 Local encode/update/read/consumer event；
4. materialize/backward/commit chronology 合法；
5. terminal commit/reset 后下一 epoch 从干净 owner state 开始；
6. retry 只允许 frozen contract 的 suffix recovery；
7. attempt1 不允许 nested recovery；
8. scaler skip 不伪装成 slow optimizer success；
9. state fingerprint 在 no-op/invalid path byte-identical；
10. trace 缺关键字段、未知 event/schema、顺序不闭合时 fail closed。

输出：

```text
PASS
```

或：

```text
FAIL <rule_id> <owner> <segment_id> <event_index> <reason>
```

validator 本身不得访问 GPU/模型/真实数据。

## 6. 与现有 probe 的关系

已有 R07/R08/R09 probe/capture 保留，不直接删除或替换。

复用原则：

- R09 probe 的 optimizer membership / gradient finite/max / JSON Evidence 结构可作为 telemetry/trace 设计参考；
- R09-B2 snapshot/hash isolation 可复用为 non-mutating capture acceptance pattern；
- 长期 telemetry 不应直接把 Gate-specific probe 扩成常驻大对象；
- Gate probe 继续回答“某一次 bounded run 是否满足验收”；
- observability extension 回答“长期训练是否稳定、是否偏离 frozen chronology”。

## 7. 推荐实现切分

建议后续实现按最小风险拆分：

### O1 — 纯 selector / logging reuse

- 让 `NormMonitor` 支持 configurable selectors/groups；
- 不改 Local runtime；
- 为 Local slow group 增加 norm 曲线；
- CPU/static + callback unit tests。

### O2 — Local telemetry producer

- 新增 `LocalMemoryTelemetryCallback`；
- 只读已存在的 output/runtime counters；
- W&B 可关闭；
- smoke 下 stdout/JSON scalar evidence 可验收。

### O3 — Contract trace

- 增加 bounded trace sink；
- 先覆盖 synthetic CPU chronology；
- 证明 capture non-mutating、无 authority duplication。

### O4 — Offline validator

- 纯 CPU；
- fixture-driven；
- 覆盖正常、PAD、terminal、scaler skip、retry suffix、attempt1 failure。

### O5 — recipe enablement

只有在后续明确 Gate 授权下，才讨论：

- 长期训练是否重新启用 W&B basic subset；
- callback 频率；
- trace sampling；
- multi-rank / production recipe wiring。

## 8. Acceptance 原则

任何 observability implementation 必须满足：

1. **observer 不成为 authority**：不得定义 owner/epoch/segment/scheduler/retry semantics；
2. **non-mutating**：打开/关闭 observability 不改变模型参数、buffer、optimizer、scheduler、RNG、fast state、batch metadata；
3. **no extra read on invalid/PAD**：监控不能破坏 frozen fail-before-read 语义；
4. **no duplicate compute**：不得为了统计重新 encode/replay/materialize/update；
5. **bounded overhead**：默认 telemetry 为 scalar 聚合，trace 默认关闭；
6. **distributed-safe**：复用已有 collective 语义，避免 callback 自建不对称 collective；
7. **W&B optional**：`wandb.run is None` 时训练仍正常，accumulator 必须正常 flush/reset；
8. **machine-readable evidence**：关键 contract trace 与 validator 输出可离线审计。

## 9. v0.1 结论

当前代码并不缺一套通用监控系统。更合适的工程方向是：

```text
Cosmos existing observability
    + configurable Local selectors
    + Local telemetry producer
    + sparse chronology trace
    + offline validator
```

而不是：

```text
second W&B/logger/device/norm framework
```

初步估计，大多数 logging/distributed/device/norm 基础可复用；主要新增工作集中在 Local/TTT-specific producer、trace schema 与 validator。后续实现应继续按 Gate 拆小，优先 O1/O2，避免 observability 一次性侵入 canonical runtime authority。
