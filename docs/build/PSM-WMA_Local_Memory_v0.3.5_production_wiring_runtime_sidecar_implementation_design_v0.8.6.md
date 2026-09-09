# Runtime Owner / Sidecar 实现设计 v0.8.6

**状态**：docs-only remediation；v0.8.5 superseded；child=`5d16b84`。本版仅关闭 v0.8.5 的 arbitrary skip-resume plan HIGH，继承 v0.8--v0.8.5 的 exact capability、skip chronology、snapshot、白名单和禁止范围。

## 1. skip-resume 的冻结 plan authority

`abort(SCALER_SKIP)` 在 v0.8.5 既有 exact-pending preflight 成功后，除 retained exact `skipped_identity` 外，必须以对象 identity 保存 `skipped_plan is transaction.plan` 与 `skipped_member_index = len(transaction.completed_members)`。本 Gate 只支持 `skipped_member_index == 0`；若首个 member 以外发生 skip，owner 必须在 disposition 前 fail closed，transaction/owner/scheduler/pending/sidecar 均零 mutation。该未定义 multi-member case 与 exposure/补偿一并留给后续 model/trainer integration Gate。

因此成功 `SCALER_SKIP` 后只有：`SKIP_READY(skipped_identity, skipped_plan)`；`skipped_plan` 是原 frozen `GAWindowPlan` 对象，含完整 `members`、`planned_n_valid`、`attempt==0`、`plan_chain_id`、`suffix_snapshot` 及其原 `objective()` 的 `n_window/ga_effective` 语义。禁止 clone、reconstruct、slice、caller replacement 或改变任一 plan 字段。

## 2. 无参数 resume 与 exact transaction

API 固定为无 caller plan 参数的 `resume_skipped()`。它只消费一次 retained handles，并在 mutation 前验证：

```python
owner.phase is SKIP_READY
owner.skipped_member_index == 0
owner.skipped_plan is retained_original_plan
owner.skipped_plan.attempt == 0
owner.skipped_plan.members[0] == (
    owner.skipped_identity.slot_id,
    owner.skipped_identity.episode_id,
    owner.skipped_identity.cursor,
)
scheduler.stable_slots[owner.skipped_identity.slot_id] is owner.skipped_identity
owner.skipped_identity in scheduler.admission_order
owner.skipped_identity not in scheduler.committed_identities
adapter.pending() is None
```

随后创建 `LocalMemoryTransaction(owner.skipped_plan, scheduler)`，其 `.plan is owner.skipped_plan` 必须为真；不调用 `scheduler.admit()`，不产生 attempt-1/suffix plan，也不允许 caller 提供替代 plan。该 transaction 从原 plan 的 index 0 执行，因而 `validate_success()` 与 `objective()` 保持原成员、`planned_n_valid`、`n_window`、`ga_effective`、attempt/chain identity 完全不变。任何验证失败均零 mutation 且继续 `SKIP_READY`。

`k+1` 成功 commit 后 frontier 才 reconverge，后继 `k+2` 才 normal admit；immediate `SKIP_READY` snapshot 仍 fail closed。recovered original transaction/forward/result 永不可提交；重复 skip、later-member skip、replacement plan、same-first-member altered counts/order/attempt/chain metadata 均拒绝。

## 3. CPU/static evidence 与边界

定向 tests 必须覆盖：

1. 单-member/first-member `k -> k+1 skip -> resume_skipped -> k+1 commit -> k+2 normal admit`，证明 resume transaction `.plan is` original retained plan、objective weighting 未变、无 duplicate admission；
2. same-first-member replacement plan（counts、remaining members、attempt、chain、order 任一变更）不可注入；first-member 之外的 skip fail closed，二者均逐项证明 owner/transaction/scheduler/pending/committed snapshot 零 mutation；
3. v0.8.5 的 `SKIP_READY` snapshot reject、frontier reconvergence 后 snapshot pass、wrong full identity/cleared pending/old capability reject，以及此前 retry/terminal/two-member coverage不回归。

仅授权下一 Gate 的四文件 CPU/static 白名单：新增 `canonical_segment_runtime.py`、`canonical_segment_runtime_test.py`，修改 `local_memory_segment_adapter.py` 及其 test。禁止 production wiring/model/trainer/scheduler source/dataset/config/optimizer/checkpoint/callback；无真实 I/O、GPU、torchrun、训练、评测、推理、P4/P5、B2-T 或 LIBERO4IN1。

请求 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_RUNTIME_OWNER_CPU_STATIC` 或 `REQUEST_CHANGES(file:line)`。
