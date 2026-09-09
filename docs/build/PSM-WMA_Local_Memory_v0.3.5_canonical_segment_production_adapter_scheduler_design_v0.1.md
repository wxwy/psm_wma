# PSM-WMA v0.3.5 Canonical Segment Production Adapter 与 Scheduler/GA Metadata 设计 v0.1

**日期**：2026-09-10
**状态**：docs-only design；须三方对同一 formal root/child 批准后才可开始 CPU/static implementation
**任务/Gate**：`G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCTION-ADAPTER-SCHEDULER-DESIGN`

## 1. Authority、目的与边界

本设计的唯一上游是：

1. `docs/build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.5.md` §0--§20.2；
2. `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_supersession_source_audit_v0.1.md`，其 formal audit pair 为 root `032cb6c3e24f66ae8ab25012cfc654e84b89a6e7` / child `f14a8d8e3f0cc453545f3d9b1406af76cea7e151`，并已获 ChatGPT、MM、Kimi 同 SHA `APPROVE_TO_DESIGN_R09_B_TTT_V035_CANONICAL_SEGMENT_SUPERSESSION`；
3. immutable canonical chain：semantics root `e4b2d2f980ce0f038ae1a44ed379d16bbf05b9d9` / child `80aec090688e3c710c41e1dfd86b6500773db2c7`，CPU/static design root `1f6c0bad0faa4aabae1c71b01738ad95a4ea902c` / child `80aec090688e3c710c41e1dfd86b6500773db2c7`，CPU/static closure root `d1f155d9a0cf0cf49055c065defa8119b0ac178f` / child `333792e845fe3b15ba4d8af8f34f704de2a79fa2`。

本设计只闭合 v0.3.5 §20.2 的 A--D、F 的**实现设计**：把一个 `[B_stream,T]` `SegmentBatch` 的 canonical scan、stream-major valid gather、Cosmos native consumer forward、valid-count weighted outer objective，以及 scheduler 在不加载 tensor 前冻结 GA metadata 的职责划清。它不授权实现，不改变现有 child，也不授权真实 cache/checkpoint/data I/O、CUDA/GPU/torchrun、训练、评测、推理或 LIBERO4IN1。

E（production feature-disable binding）、G（single-GPU budget）与 H（runtime sidecar/resume）明确不在本设计范围；它们各自需要后续独立 Gate。旧 `1 row/microbatch` active-wiring 仅保留 provenance、exact failure/transaction vocabulary 的审计价值，绝不得作为本设计的 graph materialization 或 trainer control-flow authority。

## 2. 不变硬合同

每个 future production member 必须先获得完整 `SegmentBatch`：

```text
consumer shape = [B_stream,T]，stream-major flat(b,t)=b*T+t
T <= ttt_tbptt_steps（首版 16）
S0 valid、Local absent；non-S0 valid 必有 e_(t-1)
PAD 不 encode、不 update、不 gather、不进入 native Cosmos loss
```

`SegmentBatch.validate()` 与 `gather_consumers()` 是 ABI owner；`scan_segment_masked_many()` 是 per-stream temporal TTT owner。生产 adapter 不得重新定义 `SegmentBatch`、`EvidenceFeatureConfig`、masked scan、episode continuity、suffix retry 或 GA retry。一次 microbatch 必须在单一 outer backward 前完整 materialize TTT graph；backward 成功后才允许 detach/commit runtime fast state。fast graph 不跨 member；slow `.grad` 可以跨一个 frozen GA window 累积。

## 3. Production adapter 的最小职责

新增的 future adapter 必须是一个**显式 opt-in、fail-closed** production seam，而不是扩展 `_ttt_local_memory_tokens()` 或 `_run_active_local_memory_native_forward()`：

```text
SegmentBatch + admitted SegmentIdentity + frozen GAWindowPlan member
  -> validate chronology/identity/count metadata
  -> canonical encoded masked scan（single [B,T] graph）
  -> project Local tokens only for gathered valid non-S0 consumers
  -> stream-major gather payload/Local/identity
  -> exact native pack + one native model forward
  -> return consumer_loss and auxiliary_loss separately, plus actual_n_valid
```

adapter 入口必须在任何 native forward 前精确验证：

1. `identity` 等于冻结 plan 的当前 member；`actual_n_valid` 尚未知时只接受 `SegmentBatch.consumer_valid.sum()` 作为预期 gathered count；必须正数。
2. `SegmentBatch.validate(ttt_tbptt_steps)` 成功；每个 gathered identity 都是 `(slot_id, episode_id, consumer_step)`，顺序严格为 `b*T+t`。
3. native pack 的输出项目数恰为 `expected_n_valid`，没有隐式 reorder、drop、padding refill 或 secondary sampling。
4. `local_present=False` 只允许 valid `S0`，传给 native consumer 的 Local 是 absent，不得伪造零 token；PAD 永远没有 payload。
5. scan/pack/forward 任一异常发生在 backward 前：不得 commit scheduler/fast state；由 future transaction seam terminalize/discard 当前 member 的 partial slow grads，且不得用另一 chronology row 替换。

native packer 尚未在本 Gate 被证明支持 variable batch。因此 implementation 之前必须由 adapter 的 CPU/static double 证明一个明确的 `NativeConsumerBatch` ABI：它接收按 stream-major 顺序的 `payloads` 和等长 `local_prefixes`，返回 `item_count`；真实 Cosmos packer 的接线只能在后续独立 production-binding/GPU Gate 获准后进行。不能以重排、补回 PAD 或把 `N_valid` 静默改成 nominal 128 来通过测试。

## 4. Native loss 与加权 objective 的边界

`OmniMoTModel._compute_losses()` 是当前 native reduction owner。future adapter 必须要求 native forward 显式返回：

```text
consumer_loss: 标量，已按本 member 的真实 gathered consumers 归一化
auxiliary_loss: 标量，非 consumer-count 线性项
actual_n_valid: int，等于 pack item_count
```

若无法从现有 native loss 获得“每 member valid-consumer mean”的可验证证据，则 fail closed；不得把已经按未知 batch 语义 reduction 的 total loss 当作 `consumer_loss` 再乘权重。

对冻结 `GAWindowPlan` 的第 `i` 个 member，唯一 outer objective 是：

```text
L_i = planned_n_valid[i] / sum(planned_n_valid) * consumer_loss
      + auxiliary_loss / len(plan.members)
```

`actual_n_valid == planned_n_valid[i]` 必须在 backward 前验证；不等即 terminal failure。full batch（所有 member `N_valid=128`）严格退化为现有的 consumer 项 `1/GA` 缩放。`L_inner` 不计入 `L_i`。native sample-level/DDP loss scale 若存在，必须在产生 `consumer_loss` 的 native seam 内完成；不得以本设计绕过或双重应用。

## 5. Scheduler 与 frozen GA metadata

`RankLocalSegmentScheduler` 保持 main-process/rank-local、`num_workers=0`；future production scheduler 在**任何 tensor/latent load 前**必须生成不可变 `GAWindowPlan`。对每个 proposed member，metadata 至少为：

```text
SegmentIdentity(slot_id, episode_id, category, cursor, segment_id,
                source_digest, training_stream_end)
planned_n_valid
SegmentProvenance(manifest_digest, config_digest, source_digest, segment_id)
queue seed / epoch / permutation
target distribution 与 cumulative valid-consumer exposure snapshot
```

`planned_n_valid` 是 scheduler 对该 logical segment 从 chronology metadata（而非已加载 tensor）计算出的 valid consumer 数；值必须等于 `[B,T]` 中的 `consumer_valid` 真值计数，且大于零。episode tail 可小于 nominal `B_stream*T`，但不得跨 episode rebind 填满同一 block。weighted-deficit 仅在 free slot 的新 episode admission 时选择 category；已绑定 slot 必须按同一 episode、同一 source digest、cursor + 1 连续推进。

在 GA window 已冻结后，scheduler 不得因 balance、load failure 或 native count mismatch 调整 member、planned count、queue 或 exposure。load/decode/cache identity failure 为 fail-closed；唯一 retry 仍仅能复用既有 immutable suffix plan，不能生成新的 sample。

## 6. Future CPU/static implementation 白名单与验收

本 design 后续若获批准，仅可先在 child 的现有 canonical synthetic Local-Memory modules及相邻测试新增最小 adapter/scheduler contract double；不得触碰真实 dataset/producer/packer、model production forward、config、optimizer selector、checkpoint 或 active-wiring row route。精确文件白名单必须在 implementation-review request 中按届时源码状态冻结，不能由本文件预授权扩大。

至少需要 CPU/static evidence：

1. `B=2,T=3` mixed `S0/non-S0/PAD` scan，验证 stream-major gather 顺序、S0 absent、PAD 零 pack/forward 影响。
2. variable `N_valid` tail（例如 5 与 3）在同一 frozen GA plan 中，验证 planned/actual exact match、weighted consumer objective 与 auxiliary `1/GA`；full batch matrix 退化为原缩放。
3. pre-load metadata 冻结：queue seed/epoch/permutation、exposure、member identities 和 counts 在 native pack/forward 前可审计；后续 tensor count mismatch、load failure、foreign identity 均 fail-closed，不能 resample/rebind。
4. scan/pack/forward/backward failure 分别证明无 premature fast-state/scheduler commit、partial slow grads discard、未执行 suffix 抑制；成功 backward 后才有一次 commit。
5. legacy no-marker 与旧 row-wise active route 不被隐式调用；本 adapter 未显式 armed 时 fail-closed 或完全不激活，二者不得混用。

验证仅限相关 pytest、`py_compile`、child/root `git diff --check`。通过实现 closure 后仍只关闭 CPU/static contract；feature production binding、single-GPU smoke、LIBERO4IN1 matched smoke、runtime sidecar 和正式训练另起审核。

## 7. 请求 verdict 与禁止范围

请求唯一 verdict：`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_SEGMENT_ADAPTER_SCHEDULER_CPU_STATIC` 或 `REQUEST_CHANGES(file:line)`。

本设计不授权任何代码、真实 I/O、CUDA/GPU、torchrun、训练/评测/推理、P4/P5、B2-T 或 LIBERO4IN1；下一步仅能在三方同 SHA 批准后开始限定的 CPU/static implementation。
