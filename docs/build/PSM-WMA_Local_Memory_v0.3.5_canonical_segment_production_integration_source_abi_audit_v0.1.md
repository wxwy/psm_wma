# PSM-WMA Local Memory v0.3.5 Canonical Segment Production Integration Source-ABI Audit v0.1

**日期**：2026-09-10  
**状态**：P0 docs-only source-ABI audit；须三方对本产物的 formal pair 独立审核  
**任务/Gate**：`G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCTION-INTEGRATION-SOURCE-ABI-AUDIT`

## 1. 审计范围与结论

本审计的 authority 是 `PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.5.md` §18、§20.1--§20.2，以及已批准的 production-integration design v0.1（formal root `ce8e3502af5226d42c270dca4d5387cec8bed412` / child `3a078f28f3d107bb633c932271f86498f7c427f7`）。审计只读取 child `3a078f2` 的源码；未修改 child、配置、数据、checkpoint 或运行任何项目代码。

**总体结论：PASS（作为 P1 docs-only production ABI implementation design 的输入），但 A--D 的 segment producer/native forward/weighted-loss 接入均为必须新实现，不能复用旧 row-wise active-wiring。** 已找到真实 Memory Prefix 的 S0-absent 表达与 feature-disable 构造路径；两者可作为 P1 的受限复用 seam。P0 不授权任何实现。

## 2. A：数据、packer、valid gather 与 flatten

| 审计项 | 精确 source map | 结论 / P1 处分 |
| --- | --- | --- |
| collate payload | `cosmos_framework/data/generator/joint_dataloader.py:128-205` 将 `video`、`video_latent`、`action`、`sequence_plan`、`local_memory` 保留为逐样本 list；`local_memory` 的 `None` placeholder 在 `:152-160,195-205` 保持与 plan 一一对齐。 | **可复用**逐 consumer 的 sparse Local payload 对齐规则；不是 `[B_stream,T]` producer，也未给出 segment PAD gather。 |
| plan 与 native batch | `cosmos_framework/model/generator/omni_mot_model.py:948-993` 由 `build_sequence_plans_from_data_batch` 取得一 plan/样本，随后 `get_data_and_condition`；`1456-1544` 将全量 `sequence_plans` 打包、noised、forward、loss。 | **必须新实现** SegmentBatchProducer：在 native pack 前按 stream-major `flat(b,t)=b*T+t` 从 `[B_stream,T]` 只保留 consumer-valid 项；现有路径没有 segment logical PAD 或 `consumer_valid` ABI。 |
| 旧 row list 不能冒充 gather | `omni_mot_model.py:995-1066`、`:4391-4417` 是 history row list 到 `data_batch["local_memory"]` 的旧路径；其输入与 `sequence_plans` 等长。 | **旁路/superseded**；它不能证明 v0.3.5 的 S0/PAD/segment flatten。P1 不得从该 row-wise route 推断 chronology。 |

因此 §20.2-A 的答案是：原生已有可变长度的逐样本 list 打包能力，但**没有** canonical segment 的 variable-valid gather、稳定 stream-major flatten 或 PAD 排除能力；P1 必须新增不可变 producer metadata 与 gather adapter，且在 pack 前断言 gathered identities/count 与冻结 plan 相同。

## 3. B/C：loss reduction、backward seam 与 planned-count authority

| 审计项 | 精确 source map | 结论 / P1 处分 |
| --- | --- | --- |
| native loss owner | `omni_mot_model.py:1530-1544` 产生 `out_net` 后调用 `_compute_losses`；`:1588-1634` 将 modality loss 委托 `compute_flow_matching_loss`；`:1705-1852` 聚合 modality、sample-level 与 auxiliary loss。 | **必须新实现**一个在 native total loss 形成后、`training_step` 返回前的 member weight seam；不得在 forward 之后做 post-hoc scalar patch。 |
| native backward/GA | `cosmos_framework/trainer/__init__.py:520-589` 在 `:521` 使用 native GA 的 DDP sync 边界，普通路径在 `:552` 以 `loss / grad_accum_iter` scale/backward，`:571-588` 在窗口边界 optimizer step/zero-grad。 | **可复用**这一 trainer backward/GA seam；P1 必须把 canonical member weight 编入进入 `:552` 前的 returned loss，并保持一次 native outer backward。 |
| planned count metadata | `canonical_segment_adapter_scheduler.py:114-188` 的 `MicrobatchPlanMember`/`CanonicalGAWindowPlan` 已冻结 row/member/window count 和 objective；`:510-553` 的 `CanonicalBatchScheduler.freeze_plan` 在 projected metadata state 生成 plan，仅 `reconcile_after_backward` 接受实际 count。 | **可复用（metadata only）** freeze/reconcile 语义；**必须新实现** producer 所需 immutable catalog/chronology/count source，且不得 preload 真实 payload tensor。`planned_n_valid` 必须含 valid S0、排除 PAD，实际 gather 后用 `reconcile_after_backward` 精确核对。 |

当前 `CanonicalBatchScheduler` 不触碰 dataset/cache/tensor，故可保持 frozen member-plan authority；producer 只能提供其 immutable source catalog、slot/episode/cursor/provenance/count 元数据，trainer 不得重推 chronology。

## 4. Memory Prefix 与 S0 absent

真实 prefix seam 已存在：

| 项目 | 精确 source map | P1 结论 |
| --- | --- | --- |
| raw Local 投影 | `cosmos_framework/model/generator/mot/cosmos3_vfm_network.py:942-966` 从 `packed_seq.local_memory_prefix` 调用 `build_memory_prefix_context` 与 `local_memory2llm`/modality embed。 | **可复用**；P1 输入应为 gathered consumer 的 `[N_valid,K_local,32]`，首轮 `K_local=1`。 |
| S0 absent | `memory_prefix.py:50-86` 接受 `list[Tensor | None]`；`:71-84` 对 `None` 写零长度 offset 和 `present=False`。`MemoryPrefixContext.validate` 的 `:22-42` 要求 present 与正长度精确匹配。 | **可复用**真实 absent 表达：S0 必须传 `None`，不得填零 token。 |
| attention 插入点 | `cosmos3_vfm_network.py:1045-1064` 在文本/vision/action/sound 编码后建立 prefix，明确拒绝 legacy Local GEN span、CUDA-graph padding 与 native `MemoryState` 共存。 | **可复用但需 P1 明确限制**；P1 必须给出 S0/normal consumer 对应 prefix list，并保留这些 fail-closed 条件。 |

这解决了 ChatGPT P0 interpretation：S0-absent 不是假设，而是现有 `None -> zero-length offset -> present=False` ABI。`[N_valid,1,2048]` 仅适用于 present consumer 的投影后有效片段；整个 batch 的实际表示是 flattened hidden 加 sample offsets，不是将 S0 填为 `[1,2048]` 零向量。

## 5. E：state/dt/age 的真实关闭

`cosmos_framework/model/generator/mot/local_evidence.py:20-83` 定义 `CANONICAL_EVIDENCE_FEATURE_CONFIG = (False,False,False)`，并且只在 feature flag 为真时注册 `age_embedding`、`dt_proj`、state buffers/projection。`:90-155` 对禁用 feature 的非 `None` 输入直接报错，`:142-155` 的 `encode_segment` 要求 canonical config 且只接收 `[B,T,96]` visual summary 与 `[B,T,10]` executed action。

**结论：可复用。** P1 应只构造 `LocalEvidenceEncoder(feature_config=CANONICAL_EVIDENCE_FEATURE_CONFIG)` 并只调用 `encode_segment`；不得使用 `omni_mot_model.py:995-1066` 的 H-history 填零入口，也不得注册后喂常数。

## 6. D：scheduler/producer 边界

`canonical_segment_adapter_scheduler.py:25-110` 冻结 `ChronologyCountRecord` 的 row identity、S0/local-absent 与 consumer-valid count 合同；`:114-188` 将其绑定到 `MicrobatchPlanMember`/window；`:510-553` 使 `freeze_plan` 是 projected-only、`reconcile_after_backward` 是唯一 live commit。`:405-492` 还冻结 stable-slot continuation 优先与 epoch rollover 的 projected semantics。

**结论：可复用为唯一 plan authority，但必须新建 producer adapter。** P1 的 producer 输出不能是旧 `ActiveNativeBatchInputs(payloads, locals, identities)`（`production_active_wiring.py:20-44`），因为后者为 row-wise gathered payload 且没有 `[B_stream,T]`、S0/PAD or source catalog ABI。新 producer 应在数据侧提供 immutable `CatalogRow/ChronologyCountRecord` 输入给 scheduler，随后把 scheduler 已冻结的 member 映射为一次 native gathered consumer batch；trainer 只消费 capability，不重新推导。

## 7. F：旧组件 disposition

| 组件 | source | disposition |
| --- | --- | --- |
| `CanonicalBatchScheduler`、`MicrobatchPlanMember`、`CanonicalGAWindowPlan` | `canonical_segment_adapter_scheduler.py:114-188,510-553` | retain / metadata-only plan、count、projected commit authority。 |
| `LocalEvidenceEncoder.encode_segment` 与 continual TTT core | `local_evidence.py:142-155`；`local_memory_segment_adapter.py:76-102` | retain / 仅算法 scan 与成功 backward 后 detach commit 的 helper；P1 需替换其 row-wise source binding。 |
| Memory Prefix | `memory_prefix.py:14-86`；`cosmos3_vfm_network.py:942-966` | retain / real native prefix seam、S0 absent。 |
| `CanonicalLocalMemorySegmentAdapter` | `local_memory_segment_adapter.py:49-102` | bypass as production owner：其 `scan` 是一个 identity/segment，虽可参考 post-backward commit guard，不拥有新 producer/GA segment ABI。 |
| `CanonicalSegmentRuntimeOwner`、`production_segment_bridge.py` | `canonical_segment_runtime.py:38-229`；`production_segment_bridge.py:62-129` | superseded/bypass for canonical production scheduling：两者按旧 row/member lifecycle 和 callback-native test double 组织。可保留作 provenance/fail-closed 失败语义参考。 |
| `production_active_wiring.py` 与 marker route | `production_active_wiring.py:20-166`；`omni_mot_model.py:1305-1332` | superseded/bypass：native adapter 在 `:1305-1308` 明确 hard-stop；不得接入或扩展为 P1 生产实现。 |

## 8. P1 必须冻结的最小新边界

P1 必须单独设计并审查以下新代码边界：

1. immutable `SegmentBatchProducer`：catalog/count metadata -> scheduler frozen member -> `[B_stream,T]` logical segment -> stream-major gather；无真实 cache/data I/O 在 CPU/static 测试。
2. real native adapter：仅 gathered valid consumers 进入 `OmniMoTModel` 正常 `_prepare_training_data`/pack/forward；S0 prefix=`None`，PAD 不生成 native sample。
3. loss bridge：native total loss 形成后、trainer scale/backward 前乘 `member.planned_n_valid / plan.original_n_valid_window`，实际 gather count 精确一致才允许 atomic reconcile/fast-state commit。
4. strict No-Local path：不创建 scheduler/TTT/prefix payload，保持当前 native data path。

## 9. 验收与禁止范围

P0 验收完成：A--F 均有 source `file:line`、现实 ABI 与 disposition；发现的 native 缺口明确列为 P1 的 new seam，没有以 padding zero sample、常数 feature、loss 后处理或 legacy replay 填补。

本产物不授权 child 改动、真实 data/cache/checkpoint I/O、CUDA/GPU、torchrun、runtime sidecar、LIBERO4IN1、训练、评测或推理。P1 设计必须以新的 formal pair 接受三方审核后才能进入 P2 CPU/static implementation。
