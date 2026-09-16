# Source-evidence closure request instance construction implementation design v0.3

本 amendment 版本化覆盖 v0.2 的字段语义：`authority.local_ref_revision` 与
`authority.remote_ref_revision` 在 fixed-ref absence observation 时必须使用字符串 `ABSENT`；存在时必须
使用 lowercase 40-hex revision。`authority.config_blob_native_oid`、`preflight.head_revision` 与
`preflight.index_tree_native_oid` 同样必须使用 lowercase 40-hex。其余 v0.2 的 memory-only 边界、exact
section/type、ordered arrays、固定 key 集合、`RECORD_KEYS[2:]` 四项 mapping 与 self-bound canonical SHA
规则保持有效。

本 amendment 只授权同一 root-only CPU/static implementation/test 的重新审核；不创建 instance、不写盘、不
执行 source I/O、GPU 或训练。请求 verdict：
`APPROVE_TO_CLOSE_R09_B_TTT_V035_SOURCE_EVIDENCE_CLOSURE_REQUEST_INSTANCE_CONSTRUCTION_CPU_STATIC`
或 `REQUEST_CHANGES(file:line)`。
