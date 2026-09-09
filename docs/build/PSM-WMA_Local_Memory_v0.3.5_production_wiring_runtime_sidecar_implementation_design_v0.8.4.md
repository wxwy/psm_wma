# Runtime Owner / Sidecar 实现设计 v0.8.4

**状态**：docs-only remediation；v0.8.3 superseded；child=`5d16b84`。本版只关闭 v0.8.3 的 `SCALER_SKIP` 生命周期 HIGH 与 abort 原子性 MEDIUM；继承 v0.8--v0.8.3 的精确 wiring、pending capability、multi-member、retry projection、snapshot frontier、白名单和禁止范围。

## 1. 范围不变

仅可在下一 Gate 修改：新增 `canonical_segment_runtime.py`、`canonical_segment_runtime_test.py`，以及 `local_memory_segment_adapter.py` 和其 test。`production_segment_wiring.py`、model、trainer、scheduler source、dataset/collator、config、optimizer、checkpoint、callback 均禁止改动；无真实 I/O、GPU、torchrun、训练、评测、推理或 LIBERO4IN1。

`pending()` 必须继续返回原始 graph-bearing exact tuple（transaction/result 均以 `is` 比较，不 clone/detach/reconstruct/clear）；`committed_snapshot()` 才返回 detached fp32 deep-copy。`discard_pending(identity, transaction, result)` 也只接受当前 pending 的 exact 三元组，且仅清除 pending，不得写 sidecar、改 scheduler 或回滚已 committed detached state。

## 2. owner phase 与 GradScaler skip

保留 v0.8.1 的正常路径与真正 terminal 路径，但以独立 `SKIPPED` disposition 替代 `SCALER_SKIP -> ABORTED`：

```text
IDLE -> ADMITTED -> MEMBER_READY -> PREPARED -> MEMBER_COMMITTED -> ... -> IDLE
                                      |                 (finish_window only)
                                      +-- abort(RETRY) --> RETRY_READY
                                      +-- abort(TERMINAL) --> ABORTED
                                      +-- abort(SCALER_SKIP) --> IDLE
```

`ABORTED` 只表示真实 terminal owner failure，仍禁止 begin/retry/snapshot。`SCALER_SKIP` 是单个慢侧 transaction disposition，不是 rank-local owner failure：成功 skip 必须在同一次 owner 操作中精确 discard 当前 pending，调用现有 `transaction.grad_scaler_skip()`，清除 owner 的 current transaction/forward/admitted/retry handles，并回到 `IDLE`。它不得调用 `scheduler.commit()`、`scheduler.admit()`、slow optimizer step 或 slow LR scheduler step；已 committed sidecar detached frontier 必须保持可读。下一 window 只能从该 `IDLE` 经一次新的 `scheduler.admit()` 和 normal `begin()` 开始，不得重用 skip 的 transaction/forward/result。

skip 当下及下一 safe committed boundary 均可 snapshot：前者必须显示没有 pending、没有 admitted identity/open transaction/open forward，且 committed frontier 等于 skip 前最后一次成功 commit；后者仍须满足既有 committed-frontier identity/terminal-slot 一致性。owner 不引入 reset/recreate API。

## 3. abort 的先验 exact-capability 原子性

所有 disposition 共用 owner-level preflight，且 preflight **发生在任何 transaction/owner/scheduler/sidecar mutation 之前**：

```python
require(phase is PREPARED)
require(transaction is owner.current_transaction)
require(forward is owner.current_forward)
pending = adapter.pending()
require(pending is not None)
require(pending[0] is owner.current_identity)
require(pending[1] is transaction)
require(pending[2] is forward.result)
```

identity 的 equality 也必须保持 exact retained `SegmentIdentity` authority；不得用同 projection 的 reconstructed identity 替代。任一 preflight 失败（substitute transaction、forward 或 result，stale/cleared pending，identity mismatch）必须抛错，且 owner phase/handles、transaction snapshot、scheduler snapshot、sidecar committed snapshot 和 pending tuple 均逐项不变。

preflight 成功后，按下列严格顺序恰好执行一次：

1. 对 `RETRY` 调用 `transaction.recover_transient(index)`，对 `TERMINAL` 调用 `transaction.terminal_failure(code)`，对 `SCALER_SKIP` 调用 `transaction.grad_scaler_skip()`；
2. 用同一 exact tuple 调用 `adapter.discard_pending(...)`；若该 call 异常，owner 立即 fail-closed，不得伪称 abort 成功或进入可 begin/snapshot 状态；
3. 只有上述两项均成功，才按 §2/既有 retry contract 变更 owner handles/phase。

因此正向 disposition 是“一次 transaction disposition + 一次 exact discard”；任何 preflight negative case 是零 mutation。RETRY 仍保留 failed full identity，attempt-1 的 `retry_plan.members[0]` 只能与其 `(slot_id, episode_id, cursor)` projection 相等，同时 `stable_slots[slot] is retained_identity`、已 admitted、尚未 committed；不得二次 `admit()`。

## 4. CPU/static evidence

除继承 v0.8--v0.8.3 的 two-member、suffix retry、wrong-metadata projection、snapshot 和 legacy/model/trainer non-invocation 覆盖外，定向 tests 必须证明：

1. prior committed sidecar frontier 后的 `SCALER_SKIP`：pending 恰好清除一次、slow optimizer/LR step 均为零、skip transaction/forward/result 永不可提交；随后 fresh identity 能正常 admit/begin/prepare，且 read 仍读取 prior committed frontier；
2. skip immediate snapshot 与 next successful committed snapshot 均通过 frontier guard，且 terminal/commit identity 与 detached snapshot 不混淆；
3. terminal、retry、skip 每个正例都恰有一次 disposition 与一次 exact discard；
4. substitute transaction/forward/result、stale/cleared pending、mismatched identity 均在 preflight 失败，比较前后 owner、transaction、scheduler、pending 和 committed snapshot，证明 **零 mutation**。

仅运行定向 pytest、target `py_compile` 与 child/root `git diff --check`；无 CUDA、文件、网络、dataset 或 checkpoint I/O。

请求 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_RUNTIME_OWNER_CPU_STATIC` 或 `REQUEST_CHANGES(file:line)`。任何批准仅覆盖 §1 的 CPU/static 白名单，不授权生产 model forward、persistent sidecar、真实 I/O、GPU、torchrun 或 LIBERO4IN1 训练。
