# PSM-WMA Production Segment Integration 设计 v0.2

**状态**：docs-only remediation；v0.1 superseded；须重新三方审核。

本版只关闭 v0.1 ABI/事务 owner 歧义，继承其禁止范围。

## 1. 唯一执行单位与 API

一次 bridge 调用恰好处理一个 `GAWindowPlan` member，公开 API 为：

```python
run_member(
    owner: CanonicalSegmentRuntimeOwner,
    plan: GAWindowPlan,
    identity: SegmentIdentity,
    segment: SegmentBatch,
    native_batch: Callable[[tuple[Any, ...], tuple[Tensor | None, ...]], NativeBatchResult],
    *, first_member: bool,
) -> None
```

`NativeBatchResult` 仅含 `primary_consumer_mean: Tensor`、`auxiliary_loss: Tensor`。`actual_n_valid` 固定为 `len(forward.payloads)`；在调用 trainer 前要求其等于 `plan.planned_n_valid[member_index]`。`member_index` 唯一由 `len(transaction.completed_members)` 得出，调用者不得传入。

若 `first_member=True`，bridge 仅允许 `owner.admit((identity,)) -> owner.begin(plan)`；若为 false，要求同一 open transaction、`owner.phase == MEMBER_COMMITTED`，仅 `owner.admit_next((identity,))`，绝不再次 `begin()`。随后均调用 `owner.prepare(segment)`，并对 **整个** `(forward.payloads, forward.locals)` 调用 `native_batch` 一次。两个 valid consumer 的验收是一次 batch callback、两个并行 entry、零 PAD entry，不是两次 forward。

disabled path 不构造 owner/plan/forward；它调用独立 no-Local native callback，接受同一 payload tuple、无 Local tuple，并与 frozen baseline 比较。

## 2. 唯一失败 disposition owner

implementation 新增 whitelist 中的 trainer bridge seam，名称为 `_run_local_memory_bridge_backward`。它只：检查 planned/actual、计算 `plan.objective`、执行一次 backward；**不**调用 `transaction.successful_backward/recover_transient/terminal_failure/grad_scaler_skip`，也不 clear grad 或抛 taxonomy。它以返回 `BridgeBackwardResult(success | scaler_skip | transient | terminal)` 报告结果。

`CanonicalSegmentRuntimeOwner` 是所有 disposition 的唯一 owner：

```text
success       -> transaction.successful_backward -> owner.commit
scaler_skip   -> owner.abort_scaler_skip
transient     -> owner.abort_retry -> begin_retry(exact suffix)
terminal      -> owner.abort_terminal
```

每条失败路径要求恰一次 transaction disposition、恰一次 exact pending discard、零 sidecar commit；任何 callback exception 分类为 terminal，且不得复用 stale forward。retry 仅由 owner 得到 exact suffix；attempt-1 skip 仍 fail-closed。

## 3. 更新后的白名单与验收

允许新增 `production_segment_bridge.py`/test，修改 `canonical_segment_runtime.py`/test 以承接无重复 disposition 的结果，以及 `trainer/__init__.py`/相邻 test 新增上述 pure backward seam；不得改 dataset/packer/model/config/checkpoint。

CPU 测试必须证明：first/continuation 的一 transaction 多 member；每 member 一次 batched callback；S0=None、non-S0 visible、PAD 零 entry；success 的一次 backward+commit；四种 disposition 的一次 mutation/一次 discard/零 sidecar；disabled baseline 由相同 opaque payload 与确定性 no-Local callback 产生，并逐项断言 payload identity、callback count、loss、slow parameter grad 相等。

真实 I/O、模型 execution、GPU/训练仍禁止。
