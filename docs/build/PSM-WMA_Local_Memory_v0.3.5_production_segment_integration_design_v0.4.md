# PSM-WMA Production Segment Integration 设计 v0.4

**状态**：docs-only remediation；v0.3 superseded；须重新三方审核。

本版仅关闭 v0.3 的 ChatGPT 两项 HIGH 与 DS 的 pending-phase 意见；其余 v0.3 contract 原样继承。未授权 child 代码、真实 I/O、模型执行、GPU、训练、评测或推理。

## 1. transaction-owned plan 是唯一 authority

`run_member` 仅 initial entry 接受 `initial_plan: GAWindowPlan`，并立即通过 `owner.begin(initial_plan)` 建立 transaction。continuation/retry entry **不得**传入 plan；它们唯一使用 `transaction.plan`：

```python
run_member(owner, identity, segment, native_batch, *, initial_plan=None, prior=None, retry=None)
```

三种互斥入口为：initial（`initial_plan` 且 owner `IDLE`）、continuation（exact `prior`、owner `MEMBER_COMMITTED`）、retained retry（exact `retry`、owner `MEMBER_READY`）。在 initial 后及全部后续路径，`plan = transaction.plan`；任何 reconstructed/substitute plan 都没有 API 位置可进入 callback、objective 或 backward。

`_run_local_memory_bridge_backward` 删除 `plan` 参数，签名只接受 exact `transaction`、`identity`、`member_index`、raw primary/auxiliary 与 `actual_n_valid`；先 `transaction.validate_success`，再只用 `transaction.plan` 调 `CanonicalSegmentRuntimeAdapter.objective`，再一次 backward。CPU/static 必须以当前 member/count 相同但 later counts/order/chain metadata 不同的 substitute plan 证明：桥/纯 seam 在 callback/backward 前拒绝，owner/scheduler/pending/.grad 零 mutation。

## 2. normal finish 的唯一 pending transition

本 bridge 明确 supersede 已关闭 owner 的 normal `finish_window -> IDLE`：

```text
MEMBER_COMMITTED && len(completed_members)==transaction.plan.ga_effective
    -- finish_window(exact transaction) --> SLOW_RESOLUTION_PENDING
```

`finish_window` 不清除 transaction；owner 私有保存 object-identical `_completed_transaction` 与唯一 `CompletedWindowCapability(owner, transaction)`。该 capability 仅由 owner 创建，持有 owner 与该 exact transaction identity；不得由同字段重建。进入 pending 后：`snapshot`、`admit`、`begin`、`admit_next`、`prepare`、retry/skip resume 均 fail-closed 且零 mutation。不存在 detached caller-held transaction resolution。

唯一 post-window API：

```python
resolve_local_memory_slow_window(completed: CompletedWindowCapability, *, scaler_skipped: bool) -> None
```

它要求 owner `SLOW_RESOLUTION_PENDING`、`completed.owner is owner`、`completed.transaction is _completed_transaction`、且 capability 是 owner 私有原对象。substitute、stale、双次消费均在 clear、transaction bookkeeping、scheduler 与 phase 改变前拒绝。

- `scaler_skipped=False`：仅在实际 optimizer step 成功后，恰调用一次 `transaction.slow_optimizer_step_succeeded()`；
- `scaler_skipped=True`：恰调用一次 `wiring.clear_local_slow_grads()`、一次 `transaction.grad_scaler_skip()`，保留已 commit fast frontier，零 Local slow optimizer/LR step。

两种成功消费均只在完成上述操作后清除 pending authority 并转 `IDLE`；随后才允许 snapshot/new initial admission。terminal/retry 的 actual grad-clear/disposition/discard 规则仍按 v0.3。

## 3. 白名单与验收增补

只允许 v0.3 §4 三组路径。`canonical_segment_runtime.py`/test 必须同步覆盖新 pending phase、owner-retained exact capability 和上述禁入矩阵；不得保留 normal finish 直接 IDLE 的 bridge 实现。

除 v0.3 的全部证据外，必须新增：

1. normal final-member finish 到 pending，pending 中 snapshot/admit/begin/prepare 全 fail-closed；
2. exact success 与 scaler-skip resolution 各一次，并在 resolution 后才可 new initial；
3. stale/substitute/reconstructed/double `CompletedWindowCapability` 的零 mutation；
4. substitute plan 的 pre-callback/pre-backward 零 mutation。

仅请求三方同 SHA verdict：

```text
APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_PRODUCTION_SEGMENT_INTEGRATION_CPU_STATIC
```

批准前禁止实现、真实 I/O、GPU、训练、P4/P5、B2-T 与 LIBERO4IN1。
