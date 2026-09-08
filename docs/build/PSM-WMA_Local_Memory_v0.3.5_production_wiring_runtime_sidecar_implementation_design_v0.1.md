# PSM-WMA Local Memory v0.3.5 Production Wiring 与 Runtime Sidecar 实现设计 v0.1

**日期**：2026-09-08  
**状态**：docs-only，待独立三方审核；不授权代码、真实 I/O、GPU 或训练  
**任务/Gate**：`G0-R09-B-TTT-V035-PRODUCTION-WIRING-RUNTIME-SIDECAR-DESIGN`

## 1. Authority 与本 Gate 边界

唯一语义 authority 是 detailed addendum v0.3.5 §0--§20、production migration v0.2，以及已关闭的 v0.5 adapter/trainer CPU/static contract（formal root `90e34f4`，child `d05f14e`）。v0.5 只证明孤立 adapter transaction seam；不得误解为 production wiring 已完成。

本文件只申请下一 Gate 的 **CPU/static production-wiring implementation design authority**，仍不授权执行真实训练。任何实现必须先重新三方同 SHA 审核。

## 2. 源码差距（已核对）

1. `cosmos_framework/model/generator/omni_mot_model.py:1031-1115` 的 `local_ttt_enabled` 分支逐 sample 调用 `TTTLifecycle.process_sample()`，仍是旧 one-window/one-evidence 路线；它不接收 canonical `SegmentBatch`，也没有 `[B_stream,T]` scan/gather ABI。
2. `cosmos_framework/trainer/__init__.py:480-508` 对每个 native batch 固定进行一次 `loss / grad_accum_iter` backward；它不知道 v0.3.5 的 `N_valid_micro/N_valid_window`，故 tail 的 weighted objective 尚未接线。
3. `mot/local_memory_segment_adapter.py:49-83` 已拥有唯一可复用的 scan -> result -> post-success detached commit primitive；其 docstring 与 `mot/local_memory_segment.py:27-107` 均明确它无 dataset/model-forward/runtime I/O 依赖。
4. `mot/local_memory_segment.py:27-107` 的 `SegmentBatch` 已冻结 stream-major valid gather、S0 absent 与 PAD zero-payload contract；生产路径必须构造它，而非转换为旧 history-window payload。

## 3. 未来实现的最小分层与白名单

下一份实施设计必须精确冻结下列层，不得在本 Gate 静默扩大：

| 层 | 允许目标 | 不可替代职责 |
|---|---|---|
| segment source/packer | 新的相邻 production bridge 与 CPU synthetic test | 从 canonical manifest provenance 组装 `[B=8,T=16]` `SegmentBatch`；fresh 必为 step0、tail 只 PAD、stream-major flatten。不得做真实 cache/data I/O。 |
| model bridge | `omni_mot_model.py` 的一个显式新 segment-only branch 与相邻测试 | 只消费 adapter 已 gather 的 `(opaque payload, local token)`；一次 native forward；禁用时严格原路径。旧 `_ttt_local_memory_tokens` 不能复用作新路径。 |
| trainer bridge | `trainer/__init__.py` 的显式 plan-aware backward branch 与相邻测试 | 在 backward 前绑定 immutable `GAWindowPlan`，使用 `N_valid_micro/N_valid_window` primary scale；保留 native callback/DDP/one-backward ordering。 |
| runtime owner | 新的 in-memory production coordinator 与 CPU test | 在 forward 前 admit/scan，在 trainer success 后唯一 commit；failure/skip 零写；不含 save/load。 |
| runtime sidecar | **不在此实现 Gate** | 持久化/resume、rank/world-size/config/checkpoint identity 属于后续独立 design/Gate。 |

不得修改 optimizer selector、defaults/recipe、checkpoint schema、registry、dataset implementation、P4/P5。生产 GPU smoke、cache I/O、sidecar persistence、multi-rank 与训练各需独立 Gate。

## 4. 调用序与不可变边界

```text
admitted immutable GAWindowPlan + per-slot SegmentIdentity
 -> segment bridge constructs/validates SegmentBatch [B,T]
 -> CanonicalLocalMemorySegmentAdapter.scan(..., transaction)
 -> exact stream-major valid gather; S0=None; PAD absent
 -> one native Cosmos forward over N_valid_micro payloads
 -> trainer computes primary weighted loss using prebound plan
 -> exactly one native backward
 -> transaction.successful_backward
 -> adapter.commit detached state_out, or terminal delete
```

任何 `ValueError` identity/count、native non-finite、forward/backward exception、suffix retry 或 GradScaler skip 都必须在 commit 之前终止；不得通过旧 lifecycle 的 materialize/replay 或私有 cursor 修补。fast graph 在本 microbatch backward 后才 detach，且绝不跨 microbatch。

## 5. 需在实现前再冻结的未决 ABI

实施设计不得猜测下列点；必须以只读 source audit 的明确函数/字段落定：

1. native Cosmos consumer payload 的真实 batch/pack 输入、输出 loss reduction 和 local token 注入点；验证 variable `N_valid_micro` 是否可直接 forward。
2. dataloader/manifest 如何提供 stable slot、episode/category/cursor、previous evidence、`training_stream_end` 与 `GAWindowPlan` 的 planned counts，而不触碰真实 cache。
3. trainer 如何保留 callbacks、DDP no-sync、GradScaler 与 native loss 的 raw finite predicate，同时替换固定 `/grad_accum_iter` 为 plan-aware primary scaling；auxiliary loss 是否存在及其 owner。
4. model 的 disabled branch 与 old `TTTLifecycle` 的选择条件，确保 `local_ttt_enabled=False` bitwise/gradient parity。

若任一项需要改 config/default、实际 packer/dataset 或 checkpoint 格式，本文件失效并先新建设计。

## 6. CPU/static 验收与禁止

实现仅可运行 `LD_LIBRARY_PATH='' .venv/bin/python -m pytest` 的定向 synthetic tests、指定文件 `py_compile` 与双仓 `git diff --check`。必须证明：

1. `[2,3]` mixed S0/PAD 成员经 bridge 保持 `flat=b*T+t` 和 opaque payload identity，恰好一次 forward，PAD 零 consumer。
2. 不等 valid counts 的一个 synthetic GA plan 产生 `sum_i loss_i / N_valid_window`，而 full batch 精确退化为 native `1/GA`。
3. successful backward 后才 commit carry；forward/backward/count/identity/skip 失败均零写且旧 carry 保留。
4. disabled path 不构造 coordinator/adapter，输出、native loss、input gradient 维持 legacy parity。
5. 无网络、模型、数据、latent cache、checkpoint、CUDA/GPU/torchrun、训练/评测/推理。

## 7. 审核请求

请求三方针对本 docs-only formal root/Gitlink 返回：

`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_PRODUCTION_WIRING_CPU_STATIC` 或带 `file:line` 的 `REQUEST_CHANGES`。

即使获批，也只授权上述最小 CPU/static wiring implementation；runtime-sidecar persistence、真实 I/O、GPU smoke 与 LIBERO4IN1 training 不因此获批。
