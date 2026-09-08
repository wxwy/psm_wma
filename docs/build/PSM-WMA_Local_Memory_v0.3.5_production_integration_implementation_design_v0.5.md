# PSM-WMA Local Memory v0.3.5 Production Integration Implementation Design v0.5

**日期**：2026-09-08
**状态**：docs-only implementation design；未授权代码、真实 I/O、GPU 或训练
**任务/Gate**：`G0-R09-B-TTT-V035-PRODUCTION-INTEGRATION-IMPLEMENTATION-DESIGN`

## 1. Authority、前置与边界

本文件以 `PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.5.md`、canonical v0.3.6--v0.3.9、已关闭的 v0.3.9 CPU/static core、v0.4 transaction closure，及 production-migration v0.2 为唯一 authority。旧 `6828b55` migration v0.1、`TTTLifecycle.process_sample()`、`ProductionLocalMemoryRuntime.materialize()` 的单 evidence/closing-row replay 路线均不得接入新生产路径。

本 Gate 只授权下一步 CPU/static **segment adapter + trainer seam** 实现；不是 model forward、registry/default/config、真实 runtime、checkpoint sidecar I/O 或训练接线授权。

## 2. 精确白名单

| 路径 | 状态 | 唯一允许变更 |
|---|---|---|
| `cosmos_framework/model/generator/mot/local_memory_segment_adapter.py` | new | frozen `@dataclass(frozen=True) SegmentScanResult`：`local_tokens: torch.Tensor[B,T,K,32]`、`local_present: torch.BoolTensor[B,T]`、`state_out: ContinualTTTFastState`、`payloads: tuple[Any, ...]`、`locals: tuple[torch.Tensor | None, ...]`、`identities: tuple[tuple[int,str,int], ...]`；`CanonicalLocalMemorySegmentAdapter`、不可序列化的 in-memory `LocalMemorySegmentSidecar`。result 不复制/reconstruct opaque payload；`locals/state_out` 保持 graph-bearing，result 内不得 detach/copy/materialize。 |
| `cosmos_framework/model/generator/mot/local_memory_segment_adapter_test.py` | new | adapter CPU/static synthetic fixtures。 |
| `cosmos_framework/trainer/__init__.py` | existing/modified | 仅 `ImaginaireTrainer._run_local_memory_segment_backward`；维持其为 primary/aux scaling、raw finite predicate、single backward 与 transaction commit 的唯一 owner。 |
| `cosmos_framework/trainer/trainer_local_memory_integration_test.py` | existing/modified | 仅该 trainer seam 的 synthetic fixtures。 |

不得修改 `production_runtime_adapter.py`、`runtime_authority.py`、`ttt_lifecycle.py`、`local_evidence.py`、`local_memory_segment.py`、C6 adapter、model forward、packer/dataset/manifest/config/optimizer/checkpoint；历史路径必须保持可用但不得被新 adapter 调用。

## 3. Adapter ABI 与调用序

`CanonicalLocalMemorySegmentAdapter.scan(segment, *, identity: SegmentIdentity, transaction: LocalMemoryTransaction)` 只接受已 `SegmentBatch.validate()` 的 canonical segment、已由 `RankLocalSegmentScheduler.admit()` 产生的 exact `SegmentIdentity` 与该 plan 的 transaction；返回不可变 `SegmentScanResult(local_tokens, local_present, state_out, payloads, locals, identities)`。其中 `payloads/locals/identities` 必须唯一来自既有 `SegmentBatch.gather_consumers()`，保持 stream-major valid gather 与 opaque payload identity；S0 Local 为 `None`，PAD 不存在于三元组。

固定顺序：

```text
validate SegmentBatch + scheduler-admitted exact SegmentIdentity
-> sidecar read using that same identity
-> ContinualTTTLocalMemoryCore.scan_segment_masked_encoded_many(
     canonical LocalEvidenceEncoder, visual_summary, executed_action, evidence_valid,
     state_in, create_graph=True)
-> SegmentBatch.gather_consumers(...)
-> synthetic consumer spy(payloads, locals, identities)
-> trainer unique primary/aux loss seam + exactly one backward
-> trainer seam alone performs transaction.validate_success(member_index, identity, actual_n_valid), objective/backward and transaction.successful_backward()
-> sidecar detach-copy state_out only after successful backward/commit
```

`LocalMemorySegmentSidecar` 以 stable `slot_id` 为 lookup，值是 `(last_committed_identity, detached_fast_state)`；其中 `last_committed_identity` 是 admitted `SegmentIdentity` 的完整 immutable projection：`slot_id`、`episode_id`、`category`、`cursor`、`segment_id`、`source_digest`、`training_stream_end`。它仅验证新 admitted identity 与此 canonical previous identity 的 episode/source 一致且 `current.cursor == last.cursor + 1`，不得生成、递增或从 consumer step/scan index/private counter 推断 cursor。首段无记录时返回 fresh state；terminal success 不写入且删除 slot record，terminal rebind 因无记录从 fresh state 开始。它只在 trainer seam 成功 commit 后 detach-copy `state_out`；不得保存 autograd graph、slow optimizer state 或 checkpoint payload。该对象不实现 load/save；runtime-sidecar 持久化及 resume 是后续独立 Gate。

## 4. Loss、异常与事务

consumer spy 返回结构化 `(primary_consumer_mean, auxiliary_loss, actual_n_valid)`；adapter 禁止自行缩放或 backward。trainer 是唯一公式 owner：

```text
L_backward = (planned_N_valid / N_window) * primary_consumer_mean
             + auxiliary_loss / GA_effective
```

必须在任何缩放前检查原生 primary loss 有限。`actual_n_valid != planned`、identity mismatch、non-finite、backward exception、attempt-1 transient 都进入既有 terminal taxonomy；只有 attempt-0 `LOAD_DECODE_TRANSIENT` 可产生一次 immutable suffix。terminal/retry/GradScaler skip 均不写 sidecar、不回滚已提交 fast chronology、清理 partial slow grads、禁止 slow optimizer/LR。正常 transaction commit 后，adapter 才能 detach-copy `state_out`。

## 5. CPU/static 验收

1. `B=2,T=3` mixed valid/S0/PAD fixture 证明 masked scan 未读 invalid bytes，gather 顺序与 opaque payload/identity 精确一致。
2. 两个连续 scheduler-admitted segment fixture 证明仅 exact canonical `SegmentIdentity` 在 successful backward 后 carry numeric state；第二段图不引用第一段 graph；stale/duplicate cursor、source mismatch、terminal/rebind fresh state 均 fail closed，且没有 sidecar-private cursor。
3. consumer spy 证明只被 valid gathered rows 调用一次，S0 receives `None`，PAD 零调用；`state/dt/age` 无构造/传递/读取。
4. unequal valid count + nonzero aux normal 与 derived attempt-1 suffix 经唯一 trainer seam，验证 full-window formula/no second GA division。
5. raw non-finite、backward exception、GradScaler skip、attempt-1 exhaustion和 identity mismatch：保留既有 committed fast state，sidecar 不新增，slow grads 清理、remaining suppression/slow step 禁止。
6. disabled parity：不构造 adapter 时输入 payload、native loss、梯度及输出与 legacy disabled path 等价；新 adapter 不调用旧 `ProductionLocalMemoryRuntime`、`TTTLifecycle`、C6 adapter。

运行仅限 CPU synthetic pytest、指定文件 `py_compile`、child/root `git diff --check`。所有测试必须明确 `LD_LIBRARY_PATH=''`，不访问网络、模型、数据、cache、checkpoint 或 GPU。

## 6. Gate 与禁止

仅当 ChatGPT、MM、DS 三方对同一 docs-only formal root/Gitlink 给出 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_PRODUCTION_INTEGRATION_CPU_STATIC` 后，才可改动第 2 节的精确 surface。实现 SHA 必须重新三方 closure review。

本批准绝不授权 model forward 接线、registry/default/config、真实 checkpoint/data/cache I/O、CUDA/GPU/torchrun、训练/评测/推理、P4/P5、B2-T 或 LIBERO4IN1；这些均另立 Gate。
