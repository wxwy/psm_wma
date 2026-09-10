# Canonical Native Forward/Loss Implementation 设计 v0.4

**状态**：docs-only remediation；supersede v0.3 failure disposal；须三方新 SHA 批准
**Gate**：`G0-R09-B-TTT-V035-CANONICAL-NATIVE-FORWARD-LOSS-IMPLEMENTATION-DESIGN`

本文件只关闭 v0.3 formal `40c00a4/5d0e037` 的 commit-success pre-mutation failure HIGH。v0.2 的 loss algebra/ownership和 v0.3 的 post-backward minting、retry、pre-scan scaler rejection保持有效；未改 child。

## Exact typed commit disposal

CPU/static implementation 在 `CanonicalProductionAdapter` 新增唯一 `abort_commit(capability)`：它要求 exact registered `CanonicalProductionCommitCapability`、其 request/result 仍为该 adapter exact pending scan pair、prepared reconcile/scheduler identity仍匹配；它只可消费一次。它首先从 `_commit_capabilities` 移除该 exact id，再调用/执行 exact scan abort；不得 frontier commit、scheduler consume、`mark_reconciled` 或重建 capability。foreign/stale/double abort fail closed、零 mutation。

trainer failure disposition 固定：

```text
backward exception: clear controlled slow grads -> abort_scan -> terminalize
prepare_commit exception: clear controlled slow grads -> abort_scan -> terminalize
commit_success pre-mutation exception:
    clear controlled slow grads -> adapter.abort_commit(capability) -> terminalize
```

`abort_commit` 只处理 adapter capability/scan bookkeeping；transaction terminalization仍由 exact trainer owner以当前 `transaction.terminalize(member_index, code)` 完成。若 `commit_success` 已跨过任何 frontier/scheduler/transaction irreversible mutation，视为 unsupported terminal bug：不得自动调用 disposal、不得重跑，必须保留证据；CPU/static injection 仅允许在其已知 pre-mutation validations中触发。

成功路径不变：post-backward `prepare_commit` 一次，`commit_success` 一次消费；attempt-0/consumed attempt-1 同样严格。新增 tests 必证明 pre-mutation commit failure后 `_commit_capabilities`、scan bookkeeping为空、frontier/scheduler/transaction无 reconcile；double/foreign disposal拒绝；成功 capability仅能 commit一次。

```text
APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_NATIVE_FORWARD_LOSS_CPU_STATIC
```
