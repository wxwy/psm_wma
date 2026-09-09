# PSM-WMA Local Memory Runtime Owner / Sidecar 实现设计 v0.8.1

**状态**：docs-only remediation；v0.8 superseded；child context=`5d16b84`。  
**Gate**：`G0-R09-B-TTT-V035-PRODUCTION-WIRING-RUNTIME-SIDECAR-DESIGN`。

本版继承 v0.8 的 exact `CanonicalSegmentWiring` owner、strict `discard_pending`、只读
adapter snapshot 接口和 owner-derived snapshot frontier；只关闭 ChatGPT v0.8 的
multi-member GA / suffix-retry HIGH。白名单、禁止真实 I/O/GPU/training 的范围不变。

## 1. 冻结的 adapter 只读接口

`local_memory_segment_adapter.py` 除 v0.8 的 `discard_pending(identity, transaction,
result)` 外，只允许新增：

```python
def pending(self) -> tuple[SegmentIdentity, LocalMemoryTransaction, SegmentScanResult] | None
def committed_snapshot(self) -> tuple[tuple[SegmentIdentity, ContinualTTTFastState], ...]
```

两者均返回 detached deep-copy/read-only view；owner 不得读取 `_pending_scan` 或
sidecar `_records` 私有字段。`pending()` 不得清除或构造 capability。

## 2. per-member/window phase machine

owner 保持一个 exact `LocalMemoryTransaction` 直到 entire `GAWindowPlan` 完成：

```text
IDLE --admit(i0)--> ADMITTED --begin(plan)--> MEMBER_READY
MEMBER_READY --prepare(i)--> PREPARED --commit(i)--> MEMBER_COMMITTED
MEMBER_COMMITTED --admit(next)--> MEMBER_READY       (same transaction)
MEMBER_COMMITTED --finish_window--> IDLE             (all members only)
PREPARED --abort(RETRY)--> RETRY_READY --begin(suffix plan)--> MEMBER_READY
PREPARED --abort(TERMINAL|SCALER_SKIP)--> ABORTED
```

`admit(next)` from `MEMBER_COMMITTED` is legal only when `next` is the exact next
`transaction.plan.members[len(completed_members)]`; it preserves the same transaction and
clears the prior forward handle (adapter pending 已由 successful commit 清除)。任何 skip,
reorder, second transaction 或旧 forward 重用 fail closed。

`finish_window(transaction)` only accepts `MEMBER_COMMITTED`, exact transaction, all plan
members complete, no pending, and no admitted residue; then clears transaction/forward/admitted
fields and enters `IDLE`，这是唯一 normal snapshot boundary。

## 3. suffix retry

`abort(RETRY, member_index)` 先调用 existing `transaction.recover_transient(member_index)`，
then exact-discard pending，清除 old forward/admitted/transaction references but retain only the
returned immutable attempt-1 `GAWindowPlan` as `retry_plan`; phase=`RETRY_READY`。
`begin_retry(retry_plan)` consumes the identical object once, creates one new
`LocalMemoryTransaction(retry_plan, same scheduler)`, admits its first suffix member, and enters
`MEMBER_READY`。attempt-0 transaction/result/forward 永远不可提交；attempt-1 retry 后再次
failure由现有 taxonomy fail closed。

`ABORTED` is terminal for terminal/scaler dispositions and cannot begin/retry/snapshot。

## 4. 验收增补

CPU/static tests 必须覆盖：

1. two-member plan：member0 commit 后 same transaction admits/prepares/commits member1，才
   `finish_window`；old forward cannot commit twice。
2. attempt-0 second member transient abort→exact pending discard→attempt-1 suffix begin→suffix
   commit/finish；old transaction/forward/result cannot regain authority。
3. every `IDLE` snapshot verifies v0.8 committed frontier；all MEMBER/RETRY/ABORTED phases reject。
4. `pending()` / `committed_snapshot()` clone isolation、mismatch discard、disabled/legacy/model/
   trainer non-invocation；pytest、py_compile、双仓 diff-check PASS。

请求 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_RUNTIME_OWNER_CPU_STATIC` 或
`REQUEST_CHANGES(file:line)`。不授权 production wiring、persistent checkpoint、真实 I/O、GPU、
torchrun、训练、评测、推理或 LIBERO4IN1。
