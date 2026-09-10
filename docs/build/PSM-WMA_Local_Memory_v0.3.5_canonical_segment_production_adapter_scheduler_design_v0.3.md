# PSM-WMA v0.3.5 Canonical Segment Production Adapter 与 Scheduler/GA Metadata 设计 v0.3

**日期**：2026-09-10
**状态**：docs-only count-semantics remediation；须三方对同一 formal root/child 批准后才可开始 CPU/static implementation
**任务/Gate**：`G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCTION-ADAPTER-SCHEDULER-DESIGN`
**替代关系**：本文件替代 `PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_adapter_scheduler_design_v0.2.md` 的 §1、§4、§5、§7、§8；除下述明确 override 外，v0.2 的全部 batch-level member、pure projected planning、atomic reconcile、first-member-only retry、queue rollover、CPU/static-only 白名单和禁止范围继续为 authority。v0.1/v0.2 仅保留历史审核依据。

## 1. Authority、范围与不变合同

继承 v0.2 的三段 immutable canonical chain、已批准 source audit pair root `032cb6c3e24f66ae8ab25012cfc654e84b89a6e7` / child `f14a8d8e3f0cc453545f3d9b1406af76cea7e151`，以及 v0.3.5 addendum §0--§20.2。本文件只关闭 v0.2 formal root `7cfa68eadd0f72d66e01b198c5d2c279d35fff54` / child `f14a8d8e3f0cc453545f3d9b1406af76cea7e151` 的 count-semantics blocker 与 queue digest byte-level LOW；不授权任何 child 代码、真实 I/O、GPU、torchrun、训练、评测、推理或 LIBERO4IN1。

`SegmentBatch` 的每个 `consumer_valid=True` cell 都是 native consumer，包含 `consumer_step==0` 的 S0；S0 仅为 Local absent，绝不是 PAD。PAD 唯一不 encode、不 update、不 gather、不计入 native loss/count 的 cell。`[B_stream,T]` batch、stream-major `flat(b,t)=b*T+t`、一个 native member 的 all-row atomic transaction，以及 v0.2 既有 `MicrobatchPlanMember`/`CanonicalGAWindowPlan` 定义不变。

## 2. 唯一 native-consumer count semantics

`ChronologyCountRecord` 在 tensor/latent load 前从 immutable manifest/chronology metadata 绑定：`slot_id`、`episode_id`、`category`、`source_digest`、`consumer_step_start`、`consumer_step_stop_exclusive`、`training_stream_end`、`manifest_digest`。该半开区间是该 row 的**全部 valid native consumer** chronology range：

```text
row_planned_n_valid = cardinality(
    [consumer_step_start, consumer_step_stop_exclusive)
    中将成为 consumer_valid=True 的 timestep
)
```

该 cardinality **含 S0**（当区间包含 `consumer_step==0`），只排除 PAD；它不得以 `consumer_step > 0` 过滤。load 后每 row 必须满足：

```text
row_planned_n_valid == SegmentBatch.consumer_valid[b].sum()
```

一个 `MicrobatchPlanMember` 的 `planned_n_valid` 必为所有 row count 之和，并严格等于 stream-major `gather_consumers()` 的 payload 数、`NativeConsumerBatch.item_count` 和 native forward 返回的 `actual_n_valid`。`original_n_valid_window` 及每 member consumer-loss 权重使用同一个 native-consumer count；S0 排除规则只存在于 Local token 投影：S0 payload 被 gather、Local prefix absent，non-S0 才投影 Local token。

任何 range/identity/provenance、row count、aggregate count、gather order 或 `actual_n_valid` 不等，均在 backward 前 terminal/fail-closed；不得把 S0 改 PAD、补零 Local token、resample、rebind 或改变已冻结 GA plan。

## 3. Deterministic queue digest bytes

v0.2 §5 的 SHA-256 permutation algorithm 使用以下唯一 preimage bytes，杜绝实现差异：

```text
UTF-8("PSM-WMA/queue/v1") || 0x00
|| ASCII(decimal(queue_seed, no leading zero)) || 0x00
|| ASCII(decimal(epoch, no leading zero)) || 0x00
|| UTF-8(category as immutable catalog string, no normalization) || 0x00
|| ASCII(decimal(canonical_index, no leading zero))
```

`0x00` 是单一 NUL byte，不是字符序列 `\\0`；所有非负整数的零值编码为 ASCII `0`。按 `(sha256(preimage).digest(), canonical_index)` 升序得到该 category/epoch permutation。v0.2 的 exhaustion 安全边界、bound-slot continuation 优先、terminal-slot release、epoch increment、projected/live separation 与 exposure 永不归零不变。

## 4. 补充 CPU/static acceptance

除 v0.2 §7 的七项证据外，必须新增或明确：

1. 一个 row 含 `S0 + non-S0 + PAD`，证明 `row_planned_n_valid == consumer_valid.sum() == gathered payload count == NativeConsumerBatch.item_count == actual_n_valid`；同时证明 S0 的 Local prefix absent、非 S0 投影、PAD 不 gather。
2. 上述含 S0 的 row 位于不等 valid-count 的 GA window，证明 `original_n_valid_window` 与 weighted `consumer_loss` 使用含 S0 的 native-consumer denominator，full-valid batch 仍退化为 `1/GA`。
3. 两个独立 fresh scheduler state 用相同 `queue_seed/epoch/category/canonical_index` 生成 byte-identical SHA preimage、相同 permutation 与同一 provenance；改变任一字段必须可审计地改变 preimage provenance，不使用 ambient RNG/Python hash。

验证仍仅限相关 CPU/static pytest、`py_compile`、child/root `git diff --check`。真实 packer binding、production feature binding、GPU smoke、runtime sidecar、LIBERO4IN1 smoke 与正式训练保持独立 Gate。

## 5. 请求 verdict 与禁止范围

请求唯一 verdict：`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_SEGMENT_ADAPTER_SCHEDULER_CPU_STATIC` 或 `REQUEST_CHANGES(file:line)`。

本文件仅 docs-only remediation。禁止 child 代码、producer/packer/dataset/manifest/config/optimizer-selector/checkpoint、真实 I/O、CUDA/GPU、torchrun、训练/评测/推理、P4/P5、B2-T 与 LIBERO4IN1；只有 ChatGPT、MM、Kimi 对同一新 root SHA 和精确 child/Gitlink 批准后，才可开始限定 CPU/static implementation。
