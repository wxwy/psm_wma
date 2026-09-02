# R09-B2 P4-v4 Execution Request `entry` 静态合同 v0.6

**状态**：draft；只申请 root static parser/validator tooling 与 stdlib CPU tests。

## 1. 目的与边界

本版承接 execution-request validator remediation=`334f544` 的三方静态批准，只冻结顶层 `entry` section 的精确 canonical JSON grammar。它不启动、实现或模拟 P4 preflight；不创建 run/staging/candidate root，也不读取模型、数据或 checkpoint。

本 section 只声明将被后续 `source` section 交叉验证的 preflight entry identity，不能以 request 自身、当前 `HEAD` 或 current bytes 自行授权。后续 source identity 必须独立证明 `root_revision`、Gitlink、Git blob 与当前 bytes；本版不得把该后续验证提前写成已发生事实。

## 2. 精确 grammar

`entry` 必须为下列精确对象，无缺失、额外键或非字符串值：

```json
{
  "tool_path": "tools/g0/r09_b2_p4_v4_execution_preflight.py",
  "root_revision": "<64 lowercase hex>",
  "git_blob_sha256": "<64 lowercase hex>",
  "current_sha256": "<64 lowercase hex>",
  "identity_sha256": "<64 lowercase hex>"
}
```

`identity_sha256` 必须等于删除自身字段后，以项目 canonical JSON（`sort_keys=True`、compact separators、末尾换行）序列化对象的 SHA256。`tool_path` 必须字面精确，拒绝绝对路径、`..`、symlink spelling、替代 entry、direct exporter script 和任意空/大小写不同字符串。四个 digest/revision 只接受小写 64-hex。

本静态步骤只验证 grammar 与 canonical identity。`git_blob_sha256 == current_sha256`、`root_revision` 可解析、entry Git blob/current bytes 以及 root Gitlink 的独立验证属于下一 `source` section，必须使用 source-owned Git authority，不能由 `entry` 单独通过。

## 3. CPU 验收与永久负例

在 `load_execution_request(raw)` 中，已完成顶层 schema/contract 校验后再验证此 `entry` grammar；任一失败均在既有无条件 hard-stop 前 `ValueError`。stdlib CPU tests 至少覆盖：正确 canonical entry、额外 key、非固定路径、非小写 digest、identity digest drift。原有单次 `O_NOFOLLOW` fd read、SHA==解析 raw 与不可变 execution contract 回归必须继续 PASS。

本版不授权真实 preflight、staging/materialize/candidate、record/refreeze、evidence publication、P5 authority/export/compose、torchrun、GPU/CUDA、模型/数据/checkpoint I/O、训练/评测/推理、B2-T 或 Local Memory 训练。

## 4. 请求 verdict

请求 `APPROVE_TO_IMPLEMENT_P4_V4_EXECUTION_REQUEST_ENTRY_STATIC_TOOLS` 或 `REQUEST_CHANGES`（附 `file:line`）。
