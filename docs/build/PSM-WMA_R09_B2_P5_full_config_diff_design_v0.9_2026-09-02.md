# R09-B2 P5 Full Resolved-Config Diff 静态设计 v0.9

**状态**：draft。v0.9 仅澄清 v0.8 第 2、6 节与继承的 v0.3 P3 合同之间的 envelope 承载缺口；未改变 P4-v4 唯一 handoff、禁止执行范围或任何训练参数。

## P3 verifier-owned binding

每个 P5 v4 envelope 的 `provenance` 除 v0.8 的三份 P4 SHA 与 `exporter_source` 外，必须精确增加：

```text
p3_contract = {
  "artifact_sha256": "<frozen P3 artifact bytes SHA256>",
  "verifier_sha256": "<frozen P3 PASS verifier bytes SHA256>",
  "backend_contract": {
    "selector_keys": ["<ordered verifier-owned keys>"],
    "optimizer_membership_sha256": "<verifier-owned SHA256>"
  }
}
```

pair verifier 必从固定 P3 artifact/PASS verifier 独立重算两 backend contract；不得信任 envelope 自报。两 backend 的 artifact/verifier SHA 必相等且等于冻结 bytes；每一侧 `backend_contract` 必与其 backend 的重算值 exact-equal。`resolved_config.optimizer.keys_to_select` 必与同侧 `selector_keys` exact-equal。

允许差异仅为 backend、三份 backend 专属 P4 SHA、`PSM_R09_B1_TTT_ENABLED`、上述两个 backend contract 字段，以及由 selector keys 直接派生的 resolved selector list 与 `local_history_backend`。其余 JSON Pointer 均 FAIL。

## 范围

本版仅申请 `APPROVE_TO_IMPLEMENT_P5_V09_STATIC_TOOLS`。只允许 root P5 exporter/verifier 与标准库 CPU tests；禁止 P4-v4 record/refreeze/preflight、P5 export/compose、torchrun、GPU、模型/数据/checkpoint、训练/评测/推理、B2-T 和 Local Memory 训练。
