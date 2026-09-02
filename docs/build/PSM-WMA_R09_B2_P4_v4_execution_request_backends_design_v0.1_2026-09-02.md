# R09-B2 P4-v4 Execution Request `backends` 静态合同 v0.1

**状态**：draft。仅设计未来 root parser-validator 与 stdlib CPU fixture；禁止 preflight、candidate/run/staging 创建、P5 export/compose、GPU 或训练。

`backends` exact 为 `{recurrent,ttt_fast_weight,identity_sha256}`，outer identity 为删除自身后的 `canonical_sha256`。每侧 exact `{backend,p3_contract,identity_sha256}`，`backend` 必 byte-exact 为键；record 与 outer 均拒绝 added/missing/retyped/digest drift，且两个 record identity 不得复用。

`p3_contract` exact `{artifact_sha256,verifier_sha256,backend_contract,identity_sha256}`；两个 backend 的 artifact/verifier SHA 必为 lowercase 64-hex 且完全相等。`backend_contract` exact `{selector_keys,optimizer_membership_sha256}`：selector_keys 为非空、无重复、稳定顺序字符串列表，membership 为 lowercase 64-hex。record 的 `p3_contract` 只允许与冻结 P5 v0.9 的同 backend contract canonical-equal；不得信任自报、不得读取 artifact、verifier 或任何输出目录。

两个 backend 的 contract 仅可在 P5 v0.9 明确的 backend-owned selector/membership 字段不同；交换 backend label/contract、第三 backend、复用 record identity 均 FAIL。fixture 覆盖 exact schema/identity、digest grammar、同侧 binding、cross-side artifact/verifier equality、selector order/duplicate/type、swap/reuse 与 ambient independence；无副作用。

若批准，仅修改 `tools/g0/r09_b2_p4_v4_execution_preflight.py` 和其 stdlib CPU test；不得调用 P5 exporter/verifier 或 subprocess。请求 verdict：`APPROVE_TO_IMPLEMENT_P4_V4_EXECUTION_REQUEST_BACKENDS_STATIC_TOOLS` 或 `REQUEST_CHANGES`（附 `file:line`）。
