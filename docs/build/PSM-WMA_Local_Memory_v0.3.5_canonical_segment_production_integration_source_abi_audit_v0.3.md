# PSM-WMA Local Memory v0.3.5 Canonical Segment Production Integration Source-ABI Audit v0.3

**日期**：2026-09-10  
**状态**：P0 docs-only remediation；显式 supersede v0.2 的 trainer ordinary-loss-seam/GA 表述；须新 formal pair 三方审核  
**任务/Gate**：`G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCTION-INTEGRATION-SOURCE-ABI-AUDIT`

## 1. Authority 与本次整改范围

本文件以 v0.3.5 addendum §18、§20.1--§20.2、approved production-integration design v0.1，以及 `CanonicalGAWindowPlan.objective()` 为 authority。它只整改 ChatGPT 对 v0.2 formal pair `e0cc97e/3a078f2` 的 HIGH：v0.2 已正确关闭 v0.1 的 whole-`total_loss` valid-count weighting 与 packer/loss source-map 缺口；但将已 window-normalized 的 `L_member` 送入 ordinary trainer `loss / grad_accum_iter` seam 会造成第二次 GA 除法。除本文件的 GA seam/验收澄清外，v0.2 结论保持生效。

本审计只读取 child `3a078f2` 源码，不改 child、配置、数据、checkpoint，也不执行项目代码、真实 I/O、GPU、训练或推理。

## 2. 更正后的 B/C：consumer 与 auxiliary 必须在 native seam 分离

### 2.1 冻结目标公式

`cosmos_framework/model/generator/mot/canonical_segment_adapter_scheduler.py:190-199` 已冻结唯一 member objective：

```text
L_member = planned_n_valid / original_n_valid_window * consumer_loss
         + auxiliary_loss / original_ga_effective
```

并在同一处先断言 `actual_n_valid == member.planned_n_valid`。因此 P1 不得将 native `total_loss` 乘 `planned_n_valid / original_n_valid_window`，且不得对这个已按窗口归一化的 `L_member` 再除 GA。

### 2.2 真实 native consumer-loss source map 与 GA boundary

1. `cosmos_framework/model/generator/algorithm/loss/flow_matching.py:18-90`：`compute_flow_matching_loss` 的输入是 per-sample `pred/target/condition_mask`；`:61-84` 构造 `noisy_mask=1-condition_mask` 并计算 masked per-instance loss，`:86-90` stack 后以 `mean()` 返回 scalar flow consumer mean。该 mask 不是 canonical segment `consumer_valid` mask。
2. `cosmos_framework/model/generator/omni_mot_model.py:1732-1819`：vision/action/sound flow means 分别经原配置 loss scale 汇入 **consumer_loss**（保持现有 modality scale 与 dummy graph 语义）。
3. `omni_mot_model.py:1821-1833`：可选 sample-level averaging 只对全部 flow consumer terms 统一缩放一次；P1 不得重复此缩放。
4. `omni_mot_model.py:1835-1850`：load-balancing 项在 consumer sample-level scaling 后独立加入；这是 **auxiliary_loss**，不可随 valid-count 加权。
5. `cosmos_framework/trainer/__init__.py:520-589`：native DDP sync、GA member clock 与 optimizer/zero-grad cadence 仍以现有 `grad_accum_iter` window 为准；ordinary No-Local path 保持 `:552` 的 `loss / grad_accum_iter`。但 canonical production branch 必须在同一 DDP/GA clock 下绕过该 scalar 除法：它对已由 `CanonicalGAWindowPlan.objective()` window-normalized 的 `L_member` 恰执行一次 `grad_scaler.scale(L_member).backward()`。现有 special canonical/active branches 仅证明这种 scaling shape，不得复用为新 segment-level authority。

### 2.3 P1 fail-closed seam

P1 必须在真实 `OmniMoTModel` normal path 中、`_compute_losses()` 已辨认 consumer/auxiliary 后、普通 trainer `:552` scalar division 前，构造：

```text
consumer_loss      # 已含原 flow modality scale 与可选一次 sample-level scale
auxiliary_loss     # 仅 :1835-1850 的 load-balancing 项
actual_n_valid     # gathered native consumer 样本数
L_member           # CanonicalGAWindowPlan.objective(...) 的已 window-normalized 标量
```

只有 `actual_n_valid == frozen member.planned_n_valid` 时，canonical branch 才可执行一次 scaled backward；否则 fail closed，且不 commit fast state/scheduler frontier。该 branch 保留 native DDP sync boundary 与 optimizer-step cadence，但不再额外 `/grad_accum_iter`。No-Local/ordinary training 必须仍走原始 `/grad_accum_iter` 行为。若 production path 无法可靠保持该分解、exact count 或单次 sample/DDP/GA scaling，P1 必须再拆 design Gate，不得回退到 total-loss weighting 或二次 GA 除法。

## 3. 不变的 A：真实 native packer、ordering、prefix 和 loss mask

| source map | 现有语义 | canonical disposition |
| --- | --- | --- |
| `joint_dataloader.py:128-205` | collate 保留逐样本 `sequence_plan`、payload、sparse `local_memory=None` 的 1:1 对齐。 | 可复用 sparse alignment；不是 `[B_stream,T]` logical batch。 |
| `omni_mot_model.py:948-993,1456-1544` | 每 native training call 建 plan、pack、noise、denoise、loss。 | 可复用 normal native call chain；必须新增 segment producer/gather。 |
| `packers.py:76-210` | `pack_input_sequence` 以 caller `sequence_plans` 顺序 enumerate。 | P1 producer 调用前冻结 stream-major gathered order，随后不得重排。 |
| `packers.py:244-255` | 每 native sample 一次 prefix payload；`has_local_memory=False` 传 `None`。 | S0 为 `None`；PAD 不产生 plan/payload。 |
| `packers.py:257-365` | modality idx counters 按 plan 顺序消费。 | P1 建立并验证 `flat(b,t)=b*T+t` gather identity/order。 |
| `flow_matching.py:61-90` + `omni_mot_model.py:1732-1852` | native token mask、per-instance mean、consumer mean 与独立 auxiliary 加法。 | 不代表 logical PAD/`consumer_valid`；producer/gather 前排除 PAD并 exact-check。 |

现有 packer 没有 `[B_stream,T]`、`consumer_valid`、logical PAD 或 segment-level stream-major gather ABI。P1 必须新建 immutable `SegmentBatchProducer`，以 scheduler frozen member identities/count 为唯一 authority；只产生 gathered valid consumers，PAD 无 native sample，S0 有 plan 但 prefix 为 `None`。

## 4. 不变的 D/E/F disposition

- Memory Prefix `None -> zero-length offset -> present=False` ABI（`memory_prefix.py:22-86`、`cosmos3_vfm_network.py:942-966`）继续保留；S0 不填 zero token。
- `LocalEvidenceEncoder(feature_config=CANONICAL_EVIDENCE_FEATURE_CONFIG).encode_segment`（`local_evidence.py:31,61-83,142-155`）继续是真关闭 seam。
- `CanonicalBatchScheduler.freeze_plan/reconcile_after_backward`（`canonical_segment_adapter_scheduler.py:510-553`）继续是 metadata-only plan/count authority；trainer 不重推 chronology。
- 历史 adapter/runtime owner/bridge/active marker 仅保留 provenance/fail-closed 参考，不能成为新 production adapter authority。

## 5. P1 设计必须冻结的验收

1. exact `consumer_loss` / `auxiliary_loss` decomposition 与唯一 objective；full-valid algebra fixture 证明 consumer 和 auxiliary 均为 `1/GA`，绝非 `1/GA^2`；unequal-valid consumer 为 `N_valid_i/N_valid_window`，auxiliary 恒为 `1/GA`。
2. canonical branch 恰一次 scaled backward、无额外 `/GA`；No-Local ordinary branch 保持 native `/GA`；DDP sync 与 optimizer cadence 不变，且无第二次 sample/DDP/GA scaling。
3. producer -> frozen scheduler member -> stream-major gathered `sequence_plans` 的 identity/order/count witness；PAD 无 native sample、S0 prefix `None`。
4. actual count 在 backward 前核验，只有 successful backward 后才 reconcile/commit；No-Local 不创建 producer/TTT/prefix state。

P0 仅在本修订产物得到新 formal pair 的三方批准后才可结束；批准仅授权创建 P1 docs-only production ABI implementation design，不授权 child implementation 或任何真实执行。
