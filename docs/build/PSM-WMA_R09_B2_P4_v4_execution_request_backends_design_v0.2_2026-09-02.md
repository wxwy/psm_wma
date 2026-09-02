# R09-B2 P4-v4 Execution Request `backends` 静态合同 v0.2

**状态**：draft；替代未批准的 v0.1。仅设计未来 root parser-validator 与 stdlib CPU fixture；禁止 preflight、candidate/run/staging 创建、P5 export/compose、GPU 或训练。

`backends` exact 为 `{recurrent,ttt_fast_weight,identity_sha256}`，outer identity 为删除自身后的 `canonical_sha256`。每侧 exact `{backend,p3_contract,identity_sha256}`，`backend` 必 byte-exact 为键；record 与 outer 均拒绝 added/missing/retyped/digest drift，且两个 record identity 不得复用。

为避免把 P4 wrapper 与 P5 v0.9 的三字段 provenance 混同，本节定义概念投影 `p3_core={artifact_sha256,verifier_sha256,backend_contract}`。`p3_contract` exact 为 `{artifact_sha256,verifier_sha256,backend_contract,identity_sha256}`，且其 `identity_sha256=canonical_sha256(p3_core)`；只有 `p3_core`（不是带 identity 的 wrapper）与 P5 v0.9 同 backend 三字段 contract exact-equal。`backend_contract` exact 为 `{selector_keys,optimizer_membership_sha256}`：selector_keys 为非空、无重复、稳定顺序字符串列表，membership 为 lowercase 64-hex。两个 backend 的 artifact/verifier SHA 均为 lowercase 64-hex，且跨侧完全相等。

本 static section 采用 verifier-owned snapshot authority，**不**读取 P3 artifact/verifier、任何输出目录，**不**调用 P5 exporter/verifier，且不信任 request 自报。实现冻结下列只读代码常量（常量本身不由 request 提供）：

```text
P3_SNAPSHOT_AUTHORITY = {
  historical_d005_revision: "ddb4e0eae97fb545d5239c1ddb6d4387170f3780",
  historical_d005_verifier_blob_sha256: "2c94f28a7779f7e74a2798124a0d85e57bafa8aab739b6072ef6790a91c9a4e6",
  recurrent_d005_sha256: "2d04c5040c5836249bcab78e7904c2cf8a475c4fcf5925942ebb496985cd3190",
  ttt_fast_weight_d005_sha256: "8890bbec61a808d5964657806cf01166c893ff66abc2fdf64ea3cd201a03274e",
  p3_artifact_sha256: "5dd5253cabaa5efa54f3ddc8891f632e3b05e515bf91c8055108e037f69b684d",
  p3_verifier_sha256: "e9700cd63e9626ce88969b2d21682c186af7dfe0c7489f88795de1301d5b64f8"
}
P3_CORE_SNAPSHOTS = {
  recurrent: {
    artifact_sha256: P3_SNAPSHOT_AUTHORITY.p3_artifact_sha256,
    verifier_sha256: P3_SNAPSHOT_AUTHORITY.p3_verifier_sha256,
    backend_contract: {
      selector_keys: ["moe_gen", "time_embedder", "vae2llm", "llm2vae", "action2llm", "llm2action", "action_modality_embed", "local_memory2llm", "local_memory_modality_embed", "local_history_runtime"],
      optimizer_membership_sha256: "31f5e455485b2c471c47da2d2c1819214372967ad1c76311e79bfe7865ec15fd"
    }
  },
  ttt_fast_weight: {
    artifact_sha256: P3_SNAPSHOT_AUTHORITY.p3_artifact_sha256,
    verifier_sha256: P3_SNAPSHOT_AUTHORITY.p3_verifier_sha256,
    backend_contract: {
      selector_keys: ["local_history_runtime.encoder", "local_memory2llm", "local_memory_modality_embed"],
      optimizer_membership_sha256: "379abd364d8a741adeafca441736c034fc3d93250d5ca8685630d18872867404"
    }
  }
}
```

该 snapshot 的来源是已关闭 `authorities` 链中固定历史 D005 raw record 的 `inputs.p3_inventory.backend_contract`、同一 D005 verifier blob 与已经 byte-bound 的 P3 artifact/PASS verifier；它与 P5 v0.9 的 `p3_contract` 仅共享三字段 wire contract，不把仍在独立 Gate 的 P5 implementation 当作 runtime authority。实现接口固定为 `validate_backends(value: object) -> None`：先校验 exact schema/identity/label 与 digest grammar，投影每侧 `p3_core`，再与对应 `P3_CORE_SNAPSHOTS[backend]` exact-compare，并检查 cross-side artifact/verifier equality、record identity non-reuse；不接收 path、root、request、authorities 或 artifact 参数，故无文件 I/O、subprocess 或 ambient 输入通路。

两个 backend 的 contract 仅可在上述 verifier-owned snapshot 明确的 selector/membership 字段不同；交换 backend label/contract、第三 backend、伪造相等 artifact/verifier SHA、复用 record identity 均 FAIL。fixture 覆盖 exact schema/identity、P3 core/wrapper distinction、每个 frozen field（含每个 selector 与 membership）drift、artifact/verifier cross-side equality、selector order/duplicate/type、swap/reuse 与 hostile ambient independence；无副作用。

若批准，仅修改 `tools/g0/r09_b2_p4_v4_execution_preflight.py` 和其 stdlib CPU test；不得调用 P5 exporter/verifier 或 subprocess。请求 verdict：`APPROVE_TO_IMPLEMENT_P4_V4_EXECUTION_REQUEST_BACKENDS_STATIC_TOOLS` 或 `REQUEST_CHANGES`（附 `file:line`）。
