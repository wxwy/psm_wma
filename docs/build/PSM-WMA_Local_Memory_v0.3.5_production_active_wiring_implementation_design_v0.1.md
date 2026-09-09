# PSM-WMA Local Memory v0.3.5 Production Active Wiring 实现设计 v0.1

**日期**：2026-09-09  
**状态**：docs-only；须三方同 SHA 审核后才可实现  
**任务/Gate**：`G0-R09-B-TTT-V035-PRODUCTION-ACTIVE-WIRING-DESIGN`

## 1. Authority 与 supersession

唯一语义 authority 是 `PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.5.md` §0--§20，以及已关闭的 production-segment integration formal pair `1c6c9ec` / `78b8c9c`。本设计只处理其未覆盖的真实 MoT/trainer 接线。

旧 `TTTLifecycle.process_sample()` / `ProductionLocalMemoryRuntime.materialize()` 的“一个 native microbatch 一条 evidence、closing-row replay witness”路线被本 Gate 的 Local-enabled 生产路径 supersede；它可保留给历史测试与 disabled/旧配置兼容，但不得由新路径调用。依据是其逐行调用位于 `omni_mot_model.py:_ttt_local_memory_tokens`，而 v0.3.5 要求一个 microbatch 已拥有完整 `[B_stream,T]` TTT graph。

本设计不授权 packer/dataset/config/checkpoint、真实 cache I/O、CUDA/GPU、torchrun、训练/评测/推理或 LIBERO4IN1。

## 2. 必须冻结的生产数据合同

Local-enabled 输入不是旧 history window。数据侧未来必须提供一个已验证的 `SegmentBatch`，含 stream-major `[B_stream,T]` 的 visual summary、executed action、evidence-valid、consumer payload、episode/category/cursor/terminal provenance；`flat(b,t)=b*T+t`，PAD 在 native forward 前 gather 掉，S0 consumer 合法但 Local token 为 `None`。

本 Gate 不实现数据侧 producer。若现有 packer 不能构造 variable-valid gathered consumer batch，必须 fail closed 并另立 packer ABI design，不能以 PAD zero sample 替代。每个 GA window 的 `planned_n_valid` 必须在 native tensor forward 前由 metadata authority 冻结；不得由 callback、loss 或已加载 tensor 反推。

## 3. 目标调用序与唯一 owner

对每个 Local-enabled microbatch，生产接线必须严格执行：

```text
admit/begin 或 retained continuation/retry
-> owner.prepare(SegmentBatch): scan [B_stream,T], create_graph=True
-> gather exact opaque valid consumer payloads 与 Local prefix tokens
-> 原生 Cosmos forward（每个 gathered consumer 恰一次）
-> bridge-owned raw finite predicate / transaction-plan weighted objective / exactly one backward
-> backward 成功后 owner.commit：仅此处 detach-copy runtime W_fast、推进 cursor
-> final member owner.finish_window -> SLOW_RESOLUTION_PENDING
-> native optimizer boundary 的实际 GradScaler verdict -> exact one-shot slow-window resolution
```

`actual_n_valid` 只能由 gathered payload tuple 长度导出并等于 frozen plan。任何 source/forward/finite/backward/identity failure 都必须 owner-owned abort/retry，零 native duplicate callback、零未授权 sidecar commit。既有 `CanonicalSegmentRuntimeOwner`、`CanonicalSegmentWiring`、`production_segment_bridge.run_member` 与 `CompletedWindowCapability` 是唯一 transaction/capability authority；生产调用方不得重建、替换或持久化它们。

## 4. Model 与 trainer 接缝

`OmniMoTModel._canonical_local_memory_segment_forward` 是 test-only marker，`run_native_forward_for_test` 绝不得进入 production。新 model seam 必须在普通 `training_step` 的原生 sequence/forward 路径中将 gathered Local tokens 注入已存在 Memory Prefix ABI，调用真正 native loss；它不得改变 no-Local 路径输入、loss、梯度或输出。

trainer 不能用当前“发现 `canonical_segment_forward` 即调用 test seam”的分支作为生产协议。它必须只在 production marker 的 exact owner capability 存在时调用 bridge pure-backward；普通 native batch 保持原有 `grad_scaler.scale(loss / grad_accum_iter).backward()`。optimizer boundary 必须消费 owner-retained `CompletedWindowCapability`：成功 slow step 恰一次；found-inf 仅 clear Local slow grads、保留已 commit fast frontier、零 Local scheduler step。不得让 `TTTLifecycleCallback` 对新路径 observe/commit/abort。

## 5. 精确 implementation 白名单（待批准）

| 路径 | 允许变更 |
|---|---|
| `cosmos_framework/model/generator/omni_mot_model.py` / 相邻 test | 仅新增 production marker/normal-forward Local injection seam；旁路旧 row-wise lifecycle。 |
| `cosmos_framework/trainer/__init__.py` / 相邻 test | 仅 production marker backward 与 optimizer-boundary completed-capability resolution。 |
| `cosmos_framework/model/generator/mot/production_segment_bridge.py` / 相邻 test | 仅生产 native-forward adapter 的 exact capability glue，不改 CPU contract。 |
| 新增 `production_active_wiring.py` / 相邻 test | 无 I/O 的 marker schema、owner registry 和 disabled parity facade。 |

不得修改 dataset/packer/manifest/config/optimizer selector/checkpoint、`ttt_lifecycle.py`、`production_runtime_adapter.py`、`runtime_authority.py`，或模型权重定义。

## 6. CPU/static 验收与 Gate

实现后必须以 synthetic opaque payload fixture证明：initial/continuation/retry、one native callback per gathered consumer、S0/PAD、disabled exact loss/slow-grad parity、post-backward detach/commit、terminal/retry/no-finite/backward exception、final `SLOW_RESOLUTION_PENDING` 与 GradScaler success/skip 的 exact one-shot resolution；不得运行真实 model/data/cache/GPU。

还必须覆盖普通 native batch 未带 marker 时不进入新 bridge，及旧 `TTTLifecycle` 未被调用。执行范围限 CPU pytest、target `py_compile`、child/root `git diff --check`。

只有 ChatGPT、MM、DS 对同一 formal root/Gitlink 给出 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_PRODUCTION_ACTIVE_WIRING_CPU_STATIC` 后，才可修改第 5 节白名单。实现 SHA 必须重新三方 closure review；生产 packer、真实 GPU smoke、runtime-sidecar persistence 与正式 LIBERO4IN1 训练仍分别需要独立 Gate。
