# PSM-WMA Local Memory v0.3.5 Production Wiring 实现设计 v0.6

**状态**：docs-only remediation；v0.5 superseded；待三方审核。

v0.5 的完整八条 child 白名单、disable-first selector、`plan is transaction.plan`、Local-only grad owner、唯一既有 backward-seam delegation均保持不变。本版只补齐 model→trainer capability/data ABI。

## 1. Frozen marker output ABI

marker `OmniMoTModel.training_step` 返回的 `output_batch` 必须精确含：

```text
canonical_segment_forward: CanonicalSegmentForward
canonical_wiring: CanonicalSegmentWiring
canonical_transaction: LocalMemoryTransaction
canonical_member_index: int
canonical_identity: SegmentIdentity
primary_consumer_mean: Tensor scalar
auxiliary_loss: Tensor scalar
actual_n_valid: int
```

`CanonicalSegmentForward` 是 frozen dataclass，至少含 `result: SegmentScanResult`、payloads/locals/identities；它仅由该 `canonical_wiring.prepare(segment, identity, transaction)` 返回。model helper 对同一 exact wiring 调用 `prepare` 一次、spy 一次；不得复制/reconstruct result 或通过 global/model attribute 查 wiring/adapter。

## 2. Trainer identity contract

canonical trainer branch先 fail-closed 验证：

```text
plan is transaction.plan
wiring is output["canonical_wiring"]
forward is output["canonical_segment_forward"]
forward.result is the adapter pending result created by wiring.adapter.scan
identity/transaction equal the exact prepare inputs
```

缺少任一字段、mismatched wiring/adapter/result/identity/transaction 一律在 delegation/backward/commit 前拒绝。通过后，`_run_canonical_segment_backward` 仅以 `plan=transaction.plan`、输出的三个 loss/count 值和 `wiring.clear_local_slow_grads` 调用既有 `_run_local_memory_segment_backward` 一次；成功后用**同一** `wiring.adapter.commit(identity, forward.result, transaction=transaction)`。不得重建 adapter/result、不得第二 backward。

## 3. 新增验收

除了 v0.5 的 weighted-loss、disable、Local-only-grad、unrelated sentinel 与 failure zero-write，添加 CPU/static fixture：缺 capability、mismatched wiring/adapter、stale/reconstructed result 均 fail closed 且不 backward/commit；exact same wiring/result 则成功 commit。所有八条 full child paths与 v0.5一致，未列路径不得改；禁止真实 I/O、GPU、训练。

请求 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_PRODUCTION_WIRING_CPU_STATIC` 或 `REQUEST_CHANGES(file:line)`；任何批准仍不授权 persistent sidecar、真实 I/O、GPU smoke 或 LIBERO4IN1 training。
