# Canonical Native Forward/Loss Implementation 设计 v0.3

**状态**：docs-only remediation；supersede v0.2 §3；须三方新 SHA 批准
**Gate**：`G0-R09-B-TTT-V035-CANONICAL-NATIVE-FORWARD-LOSS-IMPLEMENTATION-DESIGN`

本版本只关闭 v0.2 formal `a59776f/5d0e037` 的 commit-capability failure-safe HIGH。v0.2 的 `N/K_m` algebra、absent graph semantics、field-wise ownership、白名单与禁止范围保持不变；未改 child。

## Exact failure-safe lifecycle

`CanonicalNativeForwardCapability` 在 forward 时只绑定 exact adapter、request、scan result、transaction、loss split；**不**携带 pre-minted commit capability。成功和失败顺序唯一如下：

```text
preflight enabled-scaler/real-optimizer boundary; reject before scan
scan_result = adapter.scan(request)
transaction.mark_backward_started(member_index)
try:
    grad_scaler.scale(L_member).backward()       # exactly once; never /GA
except Exception:
    clear controlled slow grads
    adapter.abort_scan(request, scan_result)
    transaction.terminalize(member_index, exact_failure_code)
    raise
try:
    commit_capability = adapter.prepare_commit(request, scan_result)  # once, post-backward only
    adapter.commit_success(commit_capability)                          # once
except Exception:
    clear controlled slow grads
    adapter.abort_scan(request, scan_result)
    transaction.terminalize(member_index, exact_failure_code)
    raise
```

`prepare_commit()` only follows successful backward, so its stateful `_commit_capabilities` registry never receives an authority for a backward failure. `commit_success()` remains the only consumer and performs exact reconcile. On post-backward preparation failure, no capability exists; on `commit_success()` failure the implementation must only permit it before its irreversible frontier/scheduler mutation, otherwise treat as terminal bug and preserve evidence—CPU/static witnesses must prove the intended pre-mutation failure injection only. No old `successful_backward()`/generic `commit()` authority exists.

Attempt-1 uses exact `consume_retry()` request and the same sequence; no retry reconstruction, re-freeze, admission, second prepare or second transition. Enabled scaler/real optimizer rejection remains before scan, transaction mutation, callbacks, `unscale_`, step, scheduler, update and zero-grad.

Required CPU/static witnesses: backward exception after `mark_backward_started` leaves no scan/capability/frontier/scheduler reconcile; post-backward `prepare_commit` exception has identical terminal disposition; attempt-0 and consumed attempt-1 mint exactly one post-backward capability and consume it once; enabled scaler rejection happens before scan.

```text
APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_NATIVE_FORWARD_LOSS_CPU_STATIC
```
