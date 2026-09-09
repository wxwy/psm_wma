# PSM-WMA Production Segment Integration 设计 v0.3

**状态**：docs-only remediation；v0.2 superseded；须重新三方审核。

本版逐项关闭 v0.2 的 ChatGPT 三项 HIGH 与 DS 的 exact-capability/finish 意见。它不授权任何 child 代码、真实 I/O、模型执行、配置、checkpoint、CUDA/GPU、torchrun、训练、评测或推理。

## 1. 唯一成员调用、显式 capability 与结束

bridge 的一条调用只尝试一个 `GAWindowPlan` member，且只可进行一次 native batch callback。公开 API 不再使用有歧义的 `first_member: bool`：

```python
run_member(
    owner: CanonicalSegmentRuntimeOwner,
    plan: GAWindowPlan,
    identity: SegmentIdentity,
    segment: SegmentBatch,
    native_batch: Callable[[tuple[Any, ...], tuple[Tensor | None, ...]], NativeBatchOutcome],
    *,
    prior: OpenMemberCapability | None = None,
    retry: RetryMemberCapability | None = None,
) -> MemberBridgeResult
```

恰有一种入口合法；`prior` 与 `retry` 不得同时给出：

| 入口 | 进入前 exact 状态 | bridge 的唯一 admission 动作 |
|---|---|---|
| initial | `prior is retry is None`，owner `IDLE` | `admit((identity,)) -> begin(plan)` |
| continuation | `prior.owner is owner`、`prior.transaction is owner.transaction`、`owner.phase == MEMBER_COMMITTED` | `admit_next((identity,))` |
| retained retry | `retry.owner is owner`、`retry.transaction is owner.transaction`、`owner.phase == MEMBER_READY` | 无 admission、无 `begin()`，直接 `prepare(segment)` |

每个入口均须在 `prepare` 后断言：`member_index == len(transaction.completed_members)`、`identity is owner.identity`、计划成员与 identity 完全一致，以及 `actual_n_valid == plan.planned_n_valid[member_index]`。只对完整的 `(forward.payloads, forward.locals)` 调用 `native_batch` **一次**；两个 valid consumer 表示该一次 callback 内的两个 entry，零 PAD entry。

`NativeBatchOutcome` 是显式 tagged union：

```text
success(NativeBatchResult(primary_consumer_mean, auxiliary_loss))
source_failure("LOAD_DECODE_TRANSIENT")
```

callback 抛出的任何异常都为 terminal `LOCAL_MEM_OUTER_FAILURE`；不得把 exception 猜为 transient。除上表的唯一 source failure 外，没有其他 transient 来源。

`MemberBridgeResult` 只有下列不可伪造结果：

```text
OpenMemberCapability(owner, transaction)       # 成功但仍有未完成 member
CompletedWindowCapability(owner, transaction)  # 最后 member 成功，待 slow-window resolution
RetryMemberCapability(owner, transaction)      # attempt-0 transient 后的 exact suffix
TerminalMemberResult(code)                      # terminal，不能继续该 transaction
```

success 的 owner-only 顺序固定为：纯 backward `SUCCESS` → `transaction.successful_backward(...)` → `owner.commit(...)`。若仍有成员，返回 `OpenMemberCapability`；若 `len(transaction.completed_members) == transaction.plan.ga_effective`，bridge 在同一调用内调用 `owner.finish_window(transaction)`，并只返回 `CompletedWindowCapability`。调用方不能遗漏或另行调用 `finish_window()`。

transient 的 owner-only 顺序固定为：实际 Local grad clear → `owner.abort_retry(...)`（一次 transaction disposition、一次 pending discard）→ `owner.begin_retry(exact_suffix)` → 返回 `RetryMemberCapability`。下一次 retained-retry 调用是新的一次单-member/单-callback 尝试；禁止复用 attempt-0 forward、prior 或 pending capability，也禁止重复 admission。

## 2. 纯 backward seam：顺序、结果与分类

新增 whitelist 中的 trainer seam 签名冻结为：

```python
_run_local_memory_bridge_backward(
    plan, member_index, primary_consumer_mean, auxiliary_loss, actual_n_valid,
    *, transaction, identity,
) -> BridgeBackwardResult
```

它严格按以下顺序执行：

1. `transaction.validate_success(member_index, identity, actual_n_valid)`；失败映射 `TERMINAL("LOCAL_MEM_IDENTITY_CONTRACT_FAILURE")`，此时零 backward、零 transaction disposition；
2. `CanonicalSegmentRuntimeAdapter.objective(...)`，它是唯一 primary/auxiliary raw finite predicate 与唯一 scaling owner；非有限映射 `TERMINAL("LOCAL_MEM_NUMERICAL_FAILURE")`，此时零 backward、零 transaction disposition；
3. 对该唯一 objective 调用一次 `backward()`；其任何异常映射 `TERMINAL("LOCAL_MEM_OUTER_FAILURE")`，不在 seam 内清 grad 或 disposition；
4. 正常返回 `SUCCESS(loss)`。

该 seam 不接受 `failure_kind`、`grad_scaler_skip`、native callback 或 GradScaler；它绝不调用 `successful_backward`、`recover_transient`、`terminal_failure`、`grad_scaler_skip`、`clear_local_slow_grads`、owner 或 adapter。故它不可能产生 `transient` 或 `scaler_skip`，也不隐含第二个 `/grad_accum_iter`。

bridge 仅在 seam 返回 `TERMINAL(code)` 后调用 owner terminal disposition。source failure 仅在 callback 已返回 `source_failure("LOAD_DECODE_TRANSIENT")` 时走 retry；attempt-1 的相同 source failure 经既有 `classify_failure` 映射为 terminal `LOCAL_MEM_RETRY_EXHAUSTED`。

## 3. post-window GradScaler 与真实 grad-clear owner

GradScaler 判定不属于 member bridge 或纯 backward seam。最后成功 member 产生的 `CompletedWindowCapability` 使 owner 进入 `SLOW_RESOLUTION_PENDING`；该 capability 必须在本 GA window 的实际 `grad_scaler.step/update` 后由唯一 post-window seam 消费：

```python
resolve_local_memory_slow_window(
    completed: CompletedWindowCapability, *, scaler_skipped: bool,
) -> None
```

`scaler_skipped=True` 的唯一含义是实际 optimizer boundary 已证明 `found_inf`，不是 synthetic member failure：owner 调用一次 `wiring.clear_local_slow_grads()`，再调用一次 `transaction.grad_scaler_skip()`，不执行 Local slow optimizer/LR 记账，保留已 commit 的 fast-state/cursor frontier，最后转为 `IDLE`。`scaler_skipped=False` 仅在真实 optimizer step 已成功时调用一次 `transaction.slow_optimizer_step_succeeded()` 并转为 `IDLE`。

在 terminal 与 transient source failure 路径中，owner 的 `abort_terminal`/`abort_retry` 在 exact capability preflight 成功后、transaction disposition 前，调用且仅调用一次 `wiring.clear_local_slow_grads()`；之后才执行一次 transaction disposition 与一次 pending discard。这样 `.grad` 的真实清理不再仅依赖 `slow_grads_cleared` 布尔字段。任何 preflight 失败、callback/identity/finite/backward failure 之外的异常都不得产生第二次 clear、disposition 或 discard。

旧的 `abort_scaler_skip` 仅适用于它已关闭的 prepared-first-member CPU contract；v0.3 production bridge 不调用它，也不在 `PREPARED` 时回滚已完成 fast commit。

## 4. 允许 surface 与 CPU/static 验收

允许新增 `production_segment_bridge.py`/相邻 test，且只修改：

| 路径 | 允许行为 |
|---|---|
| `canonical_segment_runtime.py`/test | 上述 exact capability、retry entry、`SLOW_RESOLUTION_PENDING`、owner-only clear/disposition/finish/slow-window resolution |
| `trainer/__init__.py`/相邻 test | 上述纯 backward seam 与 post-window resolution seam；不改通用训练循环 |
| `production_segment_bridge.py`/test | one-member bridge、tagged native outcome、capability identity guards |

CPU/static evidence 至少覆盖：

1. initial→continuation 两 member 的同一 transaction、每 member 一 callback、最后 member 内部 finish，且 caller 无法用 stale/open capability 继续；
2. attempt-0 `LOAD_DECODE_TRANSIENT`→exact suffix `begin_retry`→retained-retry prepare/callback/backward success，以及 attempt-1 terminal；两者均无 duplicate admission/stale forward；
3. identity-before-backward、raw finite-before-backward、唯一 objective scaling、backward exception 的 deterministic terminal code；
4. terminal/retry 的 nonzero partial Local `.grad`：恰一次实际 clear、恰一次 transaction disposition、恰一次 pending discard、零 sidecar commit；
5. successful final member 后的 post-window scaler skip：已 commit fast frontier 保留、实际 Local grad 恰清一次、零 slow optimizer/LR step；success boundary 恰一次 slow step；
6. disabled path 不构造 owner/plan/forward，使用同一 opaque payload tuple 的 no-Local callback，并逐项证明 payload identity、callback count、loss 和 slow parameter grad parity。

dataset/packer/model/config/checkpoint、真实 I/O、CUDA/GPU、torchrun、训练、评测、推理、P4/P5、B2-T 与 LIBERO4IN1 均不在本 Gate 范围。

## 5. Gate

本版仅请求三方对同一 formal pair 给出：

```text
APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_PRODUCTION_SEGMENT_INTEGRATION_CPU_STATIC
```

收到该批准前禁止修改 child；实现提交仍须三方 fresh closure review。
