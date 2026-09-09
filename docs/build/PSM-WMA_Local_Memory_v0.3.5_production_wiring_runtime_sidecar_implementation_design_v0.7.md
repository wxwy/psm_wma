# PSM-WMA Local Memory v0.3.5 Production Runtime Owner / Sidecar 实现设计 v0.7

**状态**：docs-only；请求独立 CPU/static implementation authority。  
**Gate**：`G0-R09-B-TTT-V035-PRODUCTION-WIRING-RUNTIME-SIDECAR-DESIGN`。  
**继承并不改写**：v0.3.5 §1--§17、production-wiring v0.6，以及 formal closure pair root `593fa24d71887ea0213ff406d222957ba10285b5` / child `5d16b84fe17a42f128065bf36361f6b1bb93a436`。

本文件只冻结下一步的纯 Python/CPU runtime-owner contract，目的在于把已经关闭的
`CanonicalSegmentWiring` synthetic graph contract 接到一个可审计的 **rank-local
in-memory** owner。它不授权真实 dataloader、latent-cache 读取、checkpoint sidecar
文件、配置/默认值/registry、GPU、torchrun、训练、评测或推理。

## 1. 已核对的生产缺口

当前实现不能直接启动 v0.3.5 训练：

1. `OmniMoTModel._canonical_local_memory_segment_forward` 只接受
   `canonical_local_memory_segment=True` 的 fixture capability，且其 docstring 明确为
   test-only；它调用 `run_native_forward_for_test`，不是 Cosmos native forward
   （`cosmos_framework/model/generator/omni_mot_model.py:1265-1298`）。
2. 正常 `local_ttt_enabled` 路径仍逐 batch sample 调用
   `TTTLifecycle.process_sample()`（同文件 `1063-1122`），与 v0.3.5 的单个
   `[B_stream,T]` scan、logical padding、flatten/gather 和 valid-consumer 权重语义冲突。
3. 已有 `CanonicalLocalMemorySegmentAdapter` 已具备 in-memory sidecar 的 continuation
   与 commit-after-success contract，但它不拥有 admission、GA member 顺序或安全
   checkpoint 边界（`mot/local_memory_segment_adapter.py:20-100`）。
4. trainer 当前仅在 marker output 含 `canonical_segment_forward` 时走 exact-once
   delegated backward/commit（`trainer/__init__.py:494-498,602-642`）；该分支不能靠
   复制/reconstruct capability 扩展到未来 runtime。

因此下一步不是开启训练，也不是给旧 lifecycle 增补 patch，而是先建立唯一
runtime-owner seam，使后续 packer/model/trainer/sidecar 的 ownership 可被静态验证。

## 2. 本 Gate 的精确实现范围

获批准后只允许下列 child 路径的 CPU/static 实现；未列路径不可修改：

| 路径 | 允许符号/行为 |
|---|---|
| `cosmos_framework/model/generator/mot/canonical_segment_runtime.py` | 新建 `CanonicalSegmentRuntimeOwner`、不可变 `CanonicalRuntimeSnapshot`、`RuntimeBoundary`；只持有 `RankLocalSegmentScheduler`、`CanonicalLocalMemorySegmentAdapter` 和当前 `LocalMemoryTransaction`。不得做文件/网络/数据集 I/O。 |
| `cosmos_framework/model/generator/mot/canonical_segment_runtime_test.py` | 新建 synthetic CPU contract tests。 |
| `cosmos_framework/model/generator/mot/local_memory_segment_adapter.py` | 仅添加 owner 所需的无 I/O、只读/snapshot helper；不得改变 scan/commit 成功条件。 |
| `cosmos_framework/model/generator/mot/local_memory_segment_adapter_test.py` | 覆盖上述 helper。 |

`omni_mot_model.py`、trainer、dataset、collator、config、optimizer、checkpoint 与
callback 在本 Gate 均禁止修改。这保证本阶段不会把 synthetic marker 伪装为真实训练。

## 3. 唯一 owner 与 API

每个 rank 恰有一个 `CanonicalSegmentRuntimeOwner`；它在构造时接收已经创建的
`RankLocalSegmentScheduler` 与 `CanonicalLocalMemorySegmentAdapter`，不创建或持有
slow optimizer、DDP/FSDP module、dataloader 或 filesystem handle。

它只公开以下 API：

```python
admit(identity: SegmentIdentity) -> SegmentIdentity
begin(plan: GAWindowPlan) -> LocalMemoryTransaction
prepare(segment: SegmentBatch, identity: SegmentIdentity, transaction: LocalMemoryTransaction) -> CanonicalSegmentForward
commit(identity: SegmentIdentity, forward: CanonicalSegmentForward, transaction: LocalMemoryTransaction) -> None
abort(transaction: LocalMemoryTransaction, code: str) -> None
snapshot(boundary: RuntimeBoundary) -> CanonicalRuntimeSnapshot
```

规则：

1. `admit` 唯一委托 scheduler；fresh identity 必须 cursor=0，continued identity 必须是
   同 slot/same episode/same source 的精确 `cursor+1`。
2. `begin` 只能在无 open transaction 时接受一个 plan；该 plan 的 members 必须已按
   owner 的 admitted order 出现，且不得跨 rank/slot 重排。owner 保存 **同一对象**，
   绝不复制 plan。
3. `prepare` 必须使用 owner 的 exact adapter 和 exact transaction 调用现有
   `CanonicalSegmentWiring.prepare`；返回 capability 的 identity 与 pending scan
   identity 必须一致。不得构造第二 wiring、adapter、result 或 transaction。
4. `commit` 仅在 transaction 已由 trainer seam `successful_backward` 成功登记、且
   exact `forward.result` 仍为 pending result 时委托 adapter commit。任何 terminal
   failure、GradScaler skip、stale forward、mismatched owner/transaction/identity 都
   fail closed，且不写 sidecar。
5. `abort` 只走现有 terminal/retry taxonomy，不回滚已完成 consumer 的 detached
   runtime state；它清空 owner 的 open transaction handle，禁止后续同一 capability
   commit。

这里的 `prepare` 只提供 capability ownership，不改变已关闭的 trainer objective、
native-loss finite predicate、valid-consumer weight 或 `loss / GA` 规则；这些继续由
后续 production model/trainer Gate 绑定到真实 Cosmos loss。

## 4. Runtime sidecar 的内存语义

`CanonicalRuntimeSnapshot` 是纯 Python/torch in-memory 值，不是 `state_dict`，也
不是 checkpoint 文件格式。它至少包含：

```text
rank
owner_generation
scheduler.snapshot()
adapter sidecar 的每 slot (SegmentIdentity, detached fp32 ContinualTTTFastState)
open_transaction = None
boundary = AFTER_BACKWARD_COMMIT | TERMINAL_DISCARD
```

约束：

- snapshot 只能在 `open_transaction is None` 且所有 pending scan 已清除时产生；
  `BEFORE_BACKWARD`、`AFTER_PREPARE`、GradScaler-skip、terminal failure 和 suffix
  recovery 都必须拒绝 snapshot。
- state tensor 必须 detached、clone、fp32；snapshot 改写不能回写 live sidecar。
- terminal `training_stream_end=True` 在 successful commit 后丢弃该 slot 的 state；
  snapshot 不得保留该 terminal slot。
- restore API **不在本 Gate 实现**。未来持久化 Gate 必须将 rank、world-size、slow
  checkpoint identity、config digest、queue RNG/epoch/permutation 与 manifest/source
  provenance 加入外层 envelope，并以任一不匹配 fail closed。这个 requirement 不可由
  当前 in-memory snapshot 伪称已实现 exact resume。

## 5. CPU/static 验收

所有测试只构造小型 tensor 与现有 segment fixture，不读取 latent cache、不创建
checkpoint 文件、不调用 CUDA。最小断言：

1. fresh→continued 的同 slot segment 读取前一 committed detached state；cross-episode、
   cursor gap、source mismatch、未 admit 和 double begin 全部在 scan 前失败。
2. owner 返回的 forward、wiring、adapter、transaction 和 pending result 均保持对象
   identity；reconstructed/stale object 不能 commit。
3. success 后 state 可见且 snapshot 深拷贝；terminal success 删除 slot state。
4. terminal failure、suffix recovery、GradScaler skip、pending scan 及 open transaction
   均拒绝 snapshot，且不发生额外 fast-state write。
5. disabled/legacy 路径未被调用；本 Gate 不为 marker 或普通 `training_step` 新增行为。
6. 定向 pytest、目标 `py_compile`、child/root `git diff --check` 全部 PASS。

## 6. 明确后续 Gate 切分

本 Gate 关闭后仍须按顺序另起并独立审核：

1. **production SegmentBatch packer/source ABI design**：冻结真实 latent-cache manifest
   到 `[B_stream,T]`、`consumer_payload`、shifted evidence、logical PAD 和 terminal
   provenance 的唯一来源；不得复用 old H-history route。
2. **native Cosmos forward/loss integration design**：以真正的 gathered consumer payload
   调 `OmniMoTModel._get_training_inputs`/native forward，绑定 valid-consumer weighted
   primary/aux loss 与 trainer GA；废除 test marker 的生产可达性。
3. **persistent runtime-sidecar/checkpoint design**：在 checkpoint save/load 的安全边界
   持久化并严格 restore 第 4 节外层 envelope；先 CPU I/O tests，再单 GPU smoke。
4. 只有上述设计与实现分别获得 ChatGPT、MM、DS 同 SHA 批准，且 GPU smoke 独立通过后，
   才能申请 LIBERO4IN1 latent-cache 正式训练。

请求 verdict：`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_RUNTIME_OWNER_CPU_STATIC` 或
`REQUEST_CHANGES(file:line)`。任何批准不授权真实 I/O、checkpoint、GPU、torchrun、
训练、评测、推理或 LIBERO4IN1 操作。
