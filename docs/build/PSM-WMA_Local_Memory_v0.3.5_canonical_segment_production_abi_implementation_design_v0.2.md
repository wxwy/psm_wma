# PSM-WMA Local Memory v0.3.5 Canonical Segment Production ABI Implementation 设计 v0.2

**日期**：2026-09-10
**状态**：P1 docs-only remediation；须以本文件的新 formal root/child pair 获三方同 SHA 批准后才可进入 P2 CPU/static implementation
**任务/Gate**：`G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCTION-ABI-IMPLEMENTATION-DESIGN`

## 1. Authority、supersession 与范围

本文件以 v0.3.5 addendum §7、§12、§18、§20.1--§20.2 及三方关闭的 P0 audit v0.3（`395dadf/3a078f2`）为 authority。它显式 supersede 本 Gate v0.1 的 §2--§7：修复 P1 三方已齐意见中的 scan/gather circular ABI、fast-state/transaction commit 链、activation fallback 与 GradScaler boundary。v0.1 只保留历史；其余未冲突的禁止范围继续生效。

本轮仍只冻结 P2 CPU/static implementation design，绝不授权 child、真实 cache/data/checkpoint I/O、CUDA/GPU、torchrun、runtime sidecar、LIBERO4IN1、训练、评测或推理。P2 代码及测试须以新 pair 再次三方审核；P2 closure 亦不授权 GPU。

历史 row-wise `canonical_segment_forward`、active marker、`_inject_local_history()` / `_ttt_local_memory_tokens()` lifecycle 与 owner/bridge routes 一律不可成为 canonical v0.3.5 fallback、commit authority 或 scan authority。

## 2. P2 graph、白名单与明确 scan owner

唯一 P2 graph 为：

```text
CanonicalBatchScheduler.freeze_plan() -> exact plan/member/transaction
  -> CanonicalProductionSegmentRequest (pre-scan, no gathered fields)
  -> CanonicalProductionAdapter.arm_scan() owns fast-state lookup
  -> LocalEvidenceEncoder(CANONICAL_EVIDENCE_FEATURE_CONFIG)
     + ContinualTTTLocalMemoryCore.scan_segment_masked_encoded_many(..., create_graph=True)
  -> CanonicalProductionScanResult(local_tokens, local_present, candidate_state_out)
  -> NativeConsumerBatch.from_segment(segment_batch, member, local_tokens, local_present)
  -> existing _pack_input_sequence() / one native forward
  -> separated consumer_loss, auxiliary_loss, adapter-derived actual_n_valid
  -> typed one-shot CanonicalProductionCommitCapability
  -> transaction.mark_backward_started(member_index)
  -> exactly one grad_scaler.scale(L_member).backward()
  -> preflighted atomic fast-state + scheduler + transaction commit
```

scan owner 是新 `canonical_segment_production_adapter.py::CanonicalProductionAdapter`，不是 caller、dataset、producer 或 `OmniMoTModel` 临时逻辑。它在 model canonical-production forward 分支中、native forward 前、启用 autograd 的同一 graph 内调用**既有、不得修改**的 `LocalEvidenceEncoder(CANONICAL_EVIDENCE_FEATURE_CONFIG)` 和 `ContinualTTTLocalMemoryCore.scan_segment_masked_encoded_many()`。`local_tokens` 继续连至 outer loss；只能在成功 commit 后按 addendum TBPTT 语义 detach numeric `candidate_state_out`。不得在 `torch.no_grad()`、producer caller 或 legacy lifecycle 中 scan。

P2 精确白名单仅为：

1. `mot/canonical_segment_adapter_scheduler.py`：只增 scheduler reconcile preflight/one-shot prepared-commit public ABI；
2. `mot/canonical_segment_production_adapter.py`（新）：request/scan/gather/fast-state/typed commit owner；
3. `model/generator/omni_mot_model.py`：独立 activation 与 native forward/loss split；
4. `trainer/__init__.py`：独立 canonical-production backward/CPU-static guard；
5. `mot/canonical_segment_production_adapter_test.py`（新）；
6. `mot/canonical_segment_production_integration_test.py`（新）。

不得修改 `local_evidence.py`、`local_memory_segment.py`、`packers.py`、dataset/dataloader/manifest/cache loader/config/optimizer selector/checkpoint 或任何旧 row route。若现有 public scan/packer seam 无法满足此设计，P2 fail closed 并新建设计 Gate。

## 3. 分层 typed ABI：pre-scan、scan、gather

`CanonicalProductionSegmentRequest` 是唯一 pre-scan capability：

```text
scheduler: CanonicalBatchScheduler                 # live object identity
plan: CanonicalGAWindowPlan                         # scheduler.freeze_plan() 的 exact result
transaction: CanonicalBatchWindowTransaction        # transaction.plan is plan
member: MicrobatchPlanMember                        # plan.members[index] is member
member_index: int
segment_batch: SegmentBatch                         # [B_stream,T]
```

它**不得**接受 payloads、prefixes、identities、actual count、local tokens/presence 或 caller-supplied state。arm 前断言 plan/member/transaction object identity、`member.validate_batch(segment_batch)`、没有旧 marker/capability，且 scheduler live frontier 与 exact frozen transition 匹配；foreign/reconstructed/stale/reordered request 必在 scan/forward 前拒绝。

`CanonicalProductionScanResult` 只能由 adapter 生成，字段为：

```text
local_tokens: Tensor [B,T,K_local,D_local]
local_present: BoolTensor [B,T]
candidate_state_out: ContinualTTTFastState
slot_chain: tuple[(slot_id, episode_id, source_digest, cursor), ...]
```

adapter 用 `SegmentBatch` 的视觉/action/evidence fields 和有效 mask 构建 scan；S0 `consumer_valid=True` 但 `local_present=False`，PAD 永不 update/read。`NativeConsumerBatch.from_segment(segment_batch, member, local_tokens, local_present)` 是唯一 gather primitive；其 `item_count` 是唯一 `actual_n_valid` 来源。由此固定五方相等：planned count、actual count、payload count、prefix count、identity count。不得信任 caller count，也不得直接调用 `SegmentBatch.gather_consumers()` 绕过 `NativeConsumerBatch` validation。

## 4. CPU/static fast-state frontier

`CanonicalProductionFastStateFrontier` 是新 adapter 私有的 in-memory authority，按所有 `B_stream` slot 保存 `(slot_id, episode_id, source_digest, cursor) -> detached ContinualTTTFastState`。它不读 runtime sidecar、不跨 rank 同步、不做 checkpoint persistence。

- fresh row 只从当前 learned `W_bar_0` clone 出 state；
- continuation 只取同 slot、同 episode/source、精确 `cursor-1` 已成功 detached committed state；任何缺失、歧义、foreign、reordered 或 terminal continuation 在 scan 前失败；
- terminal success retire 对应 slot；非 terminal success 保存 candidate state 的 detached numeric copy；
- scan/backward/non-finite/GradScaler guard/preflight/commit 任一失败都不改 frontier；不同 slot 的 state 不得 alias。

adapter arm 时 snapshot exact slot-chain/state references，scan 只产生 candidate；只有 typed commit capability 消费该 snapshot。B>1 fixture 必证明 continuation 不跨槽泄漏、同槽 cursor 精确推进、foreign/reordered/failed member 不改变任何 committed slot。

## 5. Object-bound transaction 与原子 commit

`CanonicalProductionCommitCapability` 是 adapter 创建的单次消费对象，捕获**相同 Python 对象**：scheduler、plan、transaction、member、member_index、request slot-chain、scan result、candidate fast-state 和 native gathered batch。它不暴露 arbitrary callable。

创建/arming 必满足：

```text
plan is scheduler.freeze_plan(...) result
transaction.plan is plan
member is plan.members[member_index]
gathered.item_count == member.planned_n_valid
```

在 model forward 后、backward 前，它先验证 scalar finite、native count、capability 未消费和全部上述 identity，再调用 `transaction.mark_backward_started(member_index)`；该调用紧邻唯一 canonical backward。duplicate/reordered member、double arm、foreign/stale capability均在 backward 前失败。

P2 scheduler whitelist 必新增最小 `prepare_reconcile_after_backward(member, actual_n_valid)`：它在**不修改** live scheduler 的前提下验证 exact queued frozen transition、count、member identity 与 live `before` frontier，并返回 opaque one-shot prepared reconcile capability。adapter 在 backward 前取得该 prepared capability及 fast-state commit preflight；任一 preflight 失败均 terminalize/clear/suppress，零 frontier mutation。

successful backward 后 `CanonicalProductionCommitCapability.commit_success()` 是唯一 owner-controlled sequence：

```text
consume preflighted fast-state update
consume preflighted scheduler reconcile capability
transaction.mark_reconciled(member_index)
mark capability consumed
```

prepared capabilities 绑定同一 exclusive owner，消费前不再做可失败的外部 validation；任一 identity/preflight失效须在第一项 mutation 前拒绝。tests 必证明 exact-once、double/stale/foreign rejection，及任一 preflight failure 时 fast-state、scheduler frontier、transaction completed members 都零变化。

## 6. Activation truth table 与 native model seam

定义 `canonical_expected := config.local_ttt_enabled and data_batch contains canonical-production mode declaration`；mode declaration 与 exact `CanonicalProductionSegmentRequest` 均为 canonical route 必需 capability。

| canonical expected | exact request | old canonical/active/row-wise marker | 行为 |
| --- | --- | --- | --- |
| false | absent | absent | 唯一允许的 No-Local，进入原 ordinary path，不改变行为。 |
| false | present | 任意 | pre-forward fail closed。 |
| true | exact | absent | 新 canonical-production branch。 |
| true | absent/malformed/foreign | 任意 | pre-forward fail closed，绝不调用 `_get_training_inputs()`。 |
| true | exact | present | pre-forward fail closed。 |

因此 canonical mode 缺 request 永不可落到 `_inject_local_history()` / `_ttt_local_memory_tokens()`。如果未来需要独立 legacy row-wise mode，必须另有显式且互斥 mode declaration，本 Gate 不实现也不授权它。

canonical model branch 只将 `NativeConsumerBatch` 以原顺序适配到现有 `_pack_input_sequence()`；不改 packer。S0 prefix 使用 `None`，PAD 无 native item。`_compute_losses()` 在 flow terms 已完成原 modality/sample scale 后，显式提供 `consumer_loss`；load-balancing 项单独为 `auxiliary_loss`，不得 total-loss weighting 或重复 sample/DDP scaling。

## 7. Backward、GradScaler hard stop 与失败

在现有 DDP sync context，typed capability 仅在所有 pre-backward validation 后计算：

```text
L_member = plan.objective(member_index, consumer_loss, auxiliary_loss, actual_n_valid)
grad_scaler.scale(L_member).backward()  # exactly once; no /grad_accum_iter
```

No-Local ordinary branch 保持原 `/grad_accum_iter`。full-valid consumer/auxiliary 均为 `1/GA` 而非 `1/GA²`；不等 member consumer 为 `N_i/N_window`，auxiliary 为 `1/GA`。

P2 未获 P3 的 Option-B/real optimizer authorization。因此 trainer 的 canonical-production dispatcher 在任何 enabled GradScaler 或真实 canonical optimizer boundary 前必须 fail closed：terminalize current transaction、clear current window slow grads、丢弃 typed capability，且不 commit fast-state/scheduler/transaction。该 guard 不调用 legacy lifecycle，No-Local optimizer 行为不变。P2 CPU/static 只允许 disabled/scaffold scaler path；真实 scaler skip/step telemetry 留给 P3 design。

backward exception/non-finite、loss/count mismatch、prepared capability failure、duplicate commit 或任何 guard failure均执行同一 terminal+clear+suppress disposition；仅 member 0 pre-backward explicit transient 可使用现有 attempt-1，later/post-backward 不得 suffix retry。

## 8. P2 CPU/static evidence

1. `B=2,T=3` pre-scan -> named encoder/core scan -> typed scan result -> `NativeConsumerBatch.from_segment`：S0 counted/None prefix、PAD zero item、stream-major identity/count。
2. scan 发生于 outer graph，local token 对 consumer loss 可求梯度；pre-scan request 无 gathered fields，caller actual count 不可注入。
3. B>1 fresh/continuation：exact slot/episode/source/cursor state chain，跨槽隔离；failure/foreign/reordered 不改变 detached frontier。
4. scheduler/plan/transaction/member/capability object identity、duplicate/reordered `mark_backward_started`、prepared reconcile和one-shot commit negatives。
5. prepared commit 的 preflight failure 零 partial mutation；success 的 fast-state+scheduler+transaction exact-once sequence。
6. full/unequal GA algebra、consumer/aux split、single scaled backward、No-Local `/GA` parity。
7. activation matrix：canonical exact request 新 branch；canonical missing/malformed/foreign 或 conflict marker pre-forward fail；No-Local control-flow parity；old row route zero-call。
8. enabled/unsupported scaler negative：在 real optimizer boundary 前 terminal+clear且三种 canonical state 不变；No-Local optimizer control 不变。

验证仅限定向 CPU pytest、目标 Ruff/`py_compile`、child/root `git diff --check`。P2 禁止真实 data/cache/checkpoint I/O、CUDA/GPU。

## 9. Verdict

请求唯一 verdict：`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_SEGMENT_PRODUCTION_ABI_CPU_STATIC` 或 `REQUEST_CHANGES(file:line)`。

本 P1 v0.2 只为 docs-only remediation；不授权 child、真实 I/O、CUDA/GPU、torchrun、runtime sidecar、LIBERO4IN1、训练、评测或推理。
