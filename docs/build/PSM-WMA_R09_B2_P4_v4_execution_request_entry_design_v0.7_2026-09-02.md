# R09-B2 P4-v4 Execution Request `entry` 静态合同 v0.7

**状态**：draft；仅申请 root static parser/validator tooling 与 stdlib CPU tests。

本版替代未批准的 v0.6，专门整改 ChatGPT review=`1bf0d3b` 的 revision 宽度错误；其余非自授权边界不变。`entry` 精确为：

```json
{"tool_path":"tools/g0/r09_b2_p4_v4_execution_preflight.py","root_revision":"<40 lowercase hex>","git_blob_sha256":"<64 lowercase hex>","current_sha256":"<64 lowercase hex>","identity_sha256":"<64 lowercase hex>"}
```

键集精确、全为字符串。`identity_sha256` 是删除自身字段后 canonical JSON（sort_keys、compact separators、末尾换行）的 SHA256。`tool_path` 必须字面精确，拒绝绝对路径、`..`、symlink spelling、替代 entry 与 direct exporter script。`root_revision` 只接受本仓当前 Git object 格式的 40 小写 hex；三个 SHA 字段各只接受 64 小写 hex。

本步仅验证 grammar/canonical identity；40-hex grammar 接受不是 Git authority。后续 `source` section 必须独立证明 revision 可解析、root Gitlink、entry Git blob/current bytes 和二者相等，entry/request/current HEAD 均不得自授权。

CPU 永久测试：正确 40-hex 接受；64-hex、39/41-char、uppercase/non-hex revision 均拒绝；额外键、非固定路径、SHA/identity drift 均拒绝。既有 single `O_NOFOLLOW` fd read、SHA==parsed raw、不可变 contract 回归继续 PASS。禁止一切真实 preflight/staging/candidate/record/refreeze/P5 export/compose/GPU/训练。

请求 `APPROVE_TO_IMPLEMENT_P4_V4_EXECUTION_REQUEST_ENTRY_STATIC_TOOLS` 或 `REQUEST_CHANGES`（附 `file:line`）。
