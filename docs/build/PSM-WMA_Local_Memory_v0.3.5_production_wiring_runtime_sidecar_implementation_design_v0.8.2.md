# Runtime Owner / Sidecar 实现设计 v0.8.2

**状态**：docs-only remediation；v0.8.1 superseded；child=`5d16b84`。本版仅关闭 v0.8.1 pending identity 与 suffix admission 两项 HIGH；v0.8/v0.8.1 其余白名单和禁止范围不变。

## 1. adapter read-only API 的 identity 语义

```python
def pending(self) -> tuple[SegmentIdentity, LocalMemoryTransaction, SegmentScanResult] | None
def committed_snapshot(self) -> tuple[tuple[SegmentIdentity, ContinualTTTFastState], ...]
```

`pending()` 只读暴露**原始 exact tuple**：返回值 transaction/result 与当前 pending 分别
`is` 相同；不得 clone、detach、reconstruct、clear 或改写 graph-bearing tensor。仅
`committed_snapshot()` 返回 detached fp32 deep-copy。owner 对 pending identity、discard 与
snapshot gate 只经这两个接口，不触私有字段。测试须证明 repeated pending read 无 mutation、
`pending()[1] is exact_transaction`、`pending()[2] is exact_forward.result`，而 substitute/
reconstructed object fail closed。

## 2. attempt-1 suffix 的已 admission 首成员

attempt-0 transient failure 前，failed member 已经由 scheduler admission authority 精确 admit。
`abort(RETRY)` 保留该 failed `SegmentIdentity` 作为 `retry_first_identity`，并清除 old
transaction/forward/pending；它不 rollback scheduler admission。

`begin_retry(retry_plan)` 只消费一次 exact immutable attempt-1 suffix plan，要求
`retry_plan.members[0] == retry_first_identity`，并验证该 identity 已存在 scheduler
`admission_order`/`stable_slots` authority；它**不得调用 `scheduler.admit()`**。它创建新的
attempt-1 transaction，绑定该已 admission identity 并直接进入 `MEMBER_READY`。该 member
commit 后，剩余 suffix members 才走正常 `admit(next)`，且必须不重复任何 admission。

CPU/static tests：attempt-0 failed member→attempt-1 begin 的 scheduler admission order/count
不变；retry scan 使用前一 committed sidecar frontier；old attempt-0 transaction/forward/result
永不可提交；later suffix member正常 admit/commit/finish。无真实 I/O/GPU/training。

请求 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_RUNTIME_OWNER_CPU_STATIC` 或 `REQUEST_CHANGES(file:line)`。
