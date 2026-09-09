# Runtime Owner / Sidecar 实现设计 v0.8.5

**状态**：docs-only remediation；v0.8.4 superseded；child=`5d16b84`。本版只关闭 v0.8.4 的 skip scheduler/sidecar chronology HIGH；继承 v0.8--v0.8.4 的 exact wiring、pending preflight 原子性、retry projection、白名单和禁止范围。

## 1. skip 保留态是唯一未提交 admission authority

`SCALER_SKIP` 不得转 `IDLE`。owner 增加内部 `SKIP_READY` phase 与唯一 `skipped_identity` handle：它保存刚才已 admission、尚未 committed 的**同一对象** `SegmentIdentity`。

```text
PREPARED --abort(SCALER_SKIP)--> SKIP_READY
SKIP_READY --resume_skipped(plan)--> MEMBER_READY
```

skip 的 exact-pending preflight 与 v0.8.4 §3 完全不变。preflight 成功后，owner 恰好调用一次 `transaction.grad_scaler_skip()` 与一次 `adapter.discard_pending(...)`，清除 old transaction、forward、result、retry handles，保留 `skipped_identity`；不得 `scheduler.commit()`、`scheduler.admit()`、slow optimizer/LR step、sidecar write/reset 或 scheduler rollback。已 committed sidecar frontier 因而继续停在 cursor `k`，而 scheduler `stable_slots[slot] is skipped_identity` 停在 `k+1`，这是 `SKIP_READY` 的明确、暂时不一致状态，而不是可持久化 frontier。

`SKIP_READY` 禁止 `snapshot()`、normal `admit()`、`begin()`、`begin_retry()`，也禁止第二次 skip。因此 immediate post-skip snapshot 必须 fail closed；不得声称 scheduler/sidecar 已 reconverge。

## 2. 无 duplicate-admission 的 skip resolve

`resume_skipped(plan)` 是 skip 专用路径，不是 retry：只消费一次 owner 保存的 exact `skipped_identity`，并创建新的 normal attempt-0 `LocalMemoryTransaction`；不调用 `scheduler.admit()`，不生成 suffix recovery 或 attempt-1 plan。它必须逐项验证：

```python
plan.members[0] == (
    skipped_identity.slot_id,
    skipped_identity.episode_id,
    skipped_identity.cursor,
)
scheduler.stable_slots[skipped_identity.slot_id] is skipped_identity
skipped_identity in scheduler.admission_order
skipped_identity not in scheduler.committed_identities
adapter.pending() is None
```

同 projection 但 category/source_digest/segment_id/training_stream_end 不同的 reconstructed identity 永久拒绝。验证成功后才把 exact skipped identity 绑定为新 transaction 当前 member，清除 `skipped_identity`，转 `MEMBER_READY`。其 scan 从 sidecar 已 committed `k` 读入，成功 commit `k+1` 后 scheduler 与 sidecar frontier 才 reconverge；此时后继 `k+2` 才能走 normal `scheduler.admit()`。任何 resume preflight 失败必须零 mutation 并留在 `SKIP_READY`。

被 skip 的原 transaction/forward/result 永不可提交；若 resume 后再次失败，只能走既有 terminal/retry taxonomy，绝不重新进入 skip 或重新 admission。multi-member window 中 skip 后未完成成员的 window-level exposure/补偿不在本 Gate 定义，交由后续 model/trainer integration Gate。

## 3. snapshot 与 CPU/static evidence

`snapshot()` 仍仅在 `IDLE`、无 pending、无 admitted-but-uncommitted identity、无 open handles 且 sidecar/scheduler committed frontier 相同才可调用；`SKIP_READY` 是明确负例。新增定向 CPU/static tests 必须证明：

1. committed `k` -> admit/prepare `k+1` -> scaler skip 后，pending 恰清一次、无 slow step/sidecar write/duplicate scheduler admission，且 `SKIP_READY` snapshot 拒绝；
2. exact `resume_skipped` 使用 retained `k+1`，其 read 从 committed `k` 成功，commit `k+1` 后 frontier reconverge，才 normal-admit/commit `k+2` 并允许 snapshot；
3. substitute transaction/forward/result、cleared pending、wrong full identity 或 wrong-metadata same projection 均 fail closed 且 owner/transaction/scheduler/pending/committed snapshots 零 mutation；
4. v0.8--v0.8.4 的 two-member、retry、terminal、legacy/model/trainer non-invocation 不回归。

仅允许下一 Gate 的四文件 CPU/static 白名单：新增 `canonical_segment_runtime.py`、`canonical_segment_runtime_test.py`，修改 `local_memory_segment_adapter.py` 及其 test。禁止改 production wiring/model/trainer/scheduler source/dataset/config/optimizer/checkpoint/callback，禁止真实 I/O、GPU、torchrun、训练、评测、推理、P4/P5、B2-T 或 LIBERO4IN1。

请求 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_RUNTIME_OWNER_CPU_STATIC` 或 `REQUEST_CHANGES(file:line)`。
