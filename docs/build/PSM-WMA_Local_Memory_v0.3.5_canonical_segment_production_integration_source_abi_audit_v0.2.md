# PSM-WMA Local Memory v0.3.5 Canonical Segment Production Integration Source-ABI Audit v0.2

**日期**：2026-09-10  
**状态**：P0 docs-only remediation；显式 supersede v0.1 的 loss-weighting 与 packer/loss source-map 结论；须新 formal pair 三方审核  
**任务/Gate**：`G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCTION-INTEGRATION-SOURCE-ABI-AUDIT`

## 1. Authority 与本次整改范围

本文件以 v0.3.5 addendum §18、§20.1--§20.2、approved production-integration design v0.1，以及 `CanonicalGAWindowPlan.objective()` 为 authority。它仅整改 ChatGPT 对 v0.1 formal pair `2d34eed/3a078f2` 的 HIGH/MEDIUM：v0.1 中“按 valid-count 重权 native total loss”的表述被撤销；A 的高层 source map 被补至真实 packer 和 flow-loss reduction。

本审计仍只读取 child `3a078f2` 源码，不改 child、配置、数据、checkpoint，也不执行项目代码、真实 I/O、GPU、训练或推理。

## 2. 更正后的 B/C：consumer 与 auxiliary 必须在 native seam 分离

### 2.1 冻结目标公式

`cosmos_framework/model/generator/mot/canonical_segment_adapter_scheduler.py:190-199` 已冻结唯一 member objective：

```text
L_member = planned_n_valid / original_n_valid_window * consumer_loss
         + auxiliary_loss / original_ga_effective
```

并在同一处先断言 `actual_n_valid == member.planned_n_valid`。因此 P1 **不得**将 native `total_loss` 乘 `planned_n_valid / original_n_valid_window`：那会错误重权非 count-linear auxiliary 项。

### 2.2 真实 native consumer-loss source map

1. `cosmos_framework/model/generator/algorithm/loss/flow_matching.py:18-90`：`compute_flow_matching_loss` 的输入是 per-sample `pred/target/condition_mask`；`:61-84` 对每个 sample 构造 `noisy_mask=1-condition_mask` 并计算 masked per-instance loss，`:86-90` stack 后以 `mean()` 返回 scalar flow consumer mean。该 mask 是 native consumer generation-token mask，而不是 canonical segment `consumer_valid` mask。
2. `cosmos_framework/model/generator/omni_mot_model.py:1732-1819`：vision/action/sound flow means 分别经原配置 loss scale 汇入 `total_loss`；这是 P1 必须显式收集的 **consumer_loss**（含原有 modality scale 与其现有 dummy graph 保持语义）。
3. `omni_mot_model.py:1821-1833`：若启用 sample-level averaging，所有 flow consumer terms 仅在此处统一乘 `_sample_level_loss_scale()` 一次；P1 不能在此之前或之后重复此缩放。
4. `omni_mot_model.py:1835-1850`：load-balancing 项在 sample-level consumer scaling **之后**独立加入 `total_loss`；这是 P1 必须单独暴露的 **auxiliary_loss**，不可随 consumer valid-count 加权。
5. `cosmos_framework/trainer/__init__.py:520-589`：native DDP sync 取决于 GA member 边界，普通路径在 `:552` 执行 `grad_scaler.scale(loss / grad_accum_iter).backward()`，并在 `:571-588` 执行 optimizer/zero-grad。因此 P1 只把上式得到的 `L_member` 作为 returned loss 传入现有 seam；native `/grad_accum_iter` 与 DDP scaling 保持一次、无第二层 GA 除法。

### 2.3 P1 fail-closed seam

P1 必须在真实 `OmniMoTModel` normal path 中、`_compute_losses()` 已辨认 consumer/auxiliary 后、trainer `:552` 前公开/构造：

```text
consumer_loss      # 已含原 flow modality scale 与可选一次 sample-level scale
auxiliary_loss     # 仅 :1835-1850 的 load-balancing 项
actual_n_valid     # gathered native consumer 样本数
```

只有 `actual_n_valid == frozen member.planned_n_valid` 时，才允许计算 `CanonicalGAWindowPlan.objective(...)` 并进入 outer backward；否则 fail closed，且不 commit fast state/scheduler frontier。若 production path 无法可靠保持该分解或明确一次的 sample/DDP scaling，P1 必须再拆 design Gate，不得回退到 total-loss 重权。

## 3. 补齐 A：真实 native packer、ordering、prefix 和 loss mask

| source map | 现有语义 | canonical disposition |
| --- | --- | --- |
| `cosmos_framework/data/generator/joint_dataloader.py:128-205` | collate 保留 `sequence_plan`、`video`、`action`、`local_memory` 的逐样本 list；`:152-160,195-205` 对 sparse `local_memory=None` 保持 1:1 对齐。 | 可复用逐 consumer payload/prefix sparse alignment；不是 `[B_stream,T]` logical batch。 |
| `cosmos_framework/model/generator/omni_mot_model.py:948-993,1456-1544` | 每 native training call 由 `build_sequence_plans_from_data_batch` 得到 plans，随后 pack、noise、denoise、loss。 | 可复用 normal native call chain；必须新增 segment producer/gather，不能让 trainer 重推 chronology。 |
| `cosmos_framework/data/generator/sequence_packing/packers.py:76-210` | `pack_input_sequence` 以 caller `sequence_plans` 顺序 `enumerate`；每个 plan 调用 `begin_sample` 并以同一 `sample_idx` 取 timestep。 | **可复用 native per-plan ordering**；P1 producer 必须在调用前将 canonical stream-major gathered order冻结为该 list，随后不得重排。 |
| `packers.py:244-255` | 每个 native sample 恰好调用一次 `pack_local_memory_prefix_payload`；`has_local_memory=False` 传 `None`，不改变 native geometry。 | **可复用 S0 absent**：S0 必须为 `None`；PAD 根本不得出现在 plans。 |
| `packers.py:257-365`（及后续同一 plan 的 modality loops） | vision/action payload 通过独立 idx counters 按 plan 顺序消费，sample 内可有多 item。 | 证明 native packing 的 consumer order 是传入 plan list，而非 `B_stream,T` 维度；P1 要在 producer 处建立并验证 `flat(b,t)=b*T+t` gather identity/order。 |
| `flow_matching.py:61-90` + `omni_mot_model.py:1732-1852` | native noisy `condition_mask` 决定 generation loss 的 token mask、per-instance mean、flow consumer mean 与独立 auxiliary 加法。 | 可复用 native generation-token masking/reduction；不足以代表 canonical logical PAD 或 segment `consumer_valid`，二者必须在 producer/gather 前排除并用 metadata exact-check。 |

**A 的明确结论：**现有 packer 支持 caller 决定的可变长度逐样本 `sequence_plans` list、按该 list 的稳定顺序打包、并可表达 S0 prefix absence；它没有 `[B_stream,T]` input、`consumer_valid`、logical PAD 或 segment-level stream-major gather ABI。P1 必须新建 immutable `SegmentBatchProducer`，以 scheduler frozen member 的 identities/count 为唯一 authority，产生仅包含 gathered valid consumers 的 native list；PAD 不产生 plan/payload，S0 产生 plan 但 prefix 为 `None`。

## 4. 不变的 D/E/F disposition

- Memory Prefix 的 `None -> zero-length offset -> present=False` ABI（`memory_prefix.py:22-86`、`cosmos3_vfm_network.py:942-966`）继续保留；S0 绝不填 zero token。
- `LocalEvidenceEncoder(feature_config=CANONICAL_EVIDENCE_FEATURE_CONFIG).encode_segment`（`local_evidence.py:31,61-83,142-155`）继续是 state/dt/age 的真关闭 seam。
- `CanonicalBatchScheduler.freeze_plan/reconcile_after_backward`（`canonical_segment_adapter_scheduler.py:510-553`）继续是 metadata-only plan/count authority；producer 只提供 immutable catalog/count，trainer 不重推 chronology。
- `CanonicalLocalMemorySegmentAdapter`、runtime owner、bridge、active marker route 继续只保留 provenance/fail-closed 参考；`omni_mot_model.py:1305-1332` 的 native adapter hard-stop 证明它们不能成为新 production adapter。

## 5. P1 设计必须冻结的验收

1. exact `consumer_loss` / `auxiliary_loss` decomposition 与上述唯一 objective；带 unequal-valid GA CPU/static algebra test，证明 auxiliary 系数恒为 `1/GA`。
2. native sample-level/DDP scaling 的唯一位置；禁止 total-loss count weighting 和第二次 `/GA`。
3. producer -> frozen scheduler member -> stream-major gathered `sequence_plans` 的 identity/order/count witness，且 PAD 无 native sample、S0 prefix `None`。
4. actual count 在 backward 前核验，只有成功 backward 后才 reconcile/commit；No-Local path 不创建 producer/TTT/prefix state。

P0 仅在本修订产物得到新 formal pair 的三方批准后才可结束；批准仅授权创建 P1 docs-only production ABI implementation design，不授权 child implementation 或任何真实执行。
