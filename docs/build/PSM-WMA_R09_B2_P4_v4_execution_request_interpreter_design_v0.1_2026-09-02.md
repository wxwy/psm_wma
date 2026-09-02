# R09-B2 P4-v4 Execution Request `interpreter` 静态合同 v0.1

**状态**：draft；仅申请 root static parser/validator tooling 与 stdlib CPU fixtures。前置为 source closure root=`b0581d8`、ChatGPT review=`a9c2eb3`、Gitlink=`21d064f`，并复用 interpreter provenance v1.3 的 lexical-loader 边界。

`interpreter` 精确键为 `python_path,python_git_blob_sha256,python_current_sha256,git_path,git_git_blob_sha256,git_current_sha256,loader_args,identity_sha256`；均为字符串，identity 为删除自身字段后的 canonical JSON SHA256。两个 path 均为绝对、strict-resolved、non-symlink regular file；所有 SHA 为 64 lowercase hex。

`python_path` 必为 source root 下固定 venv lexical interpreter，`git_path` 必为 source root 下已冻结 Git executable；两者都以单 fd `O_NOFOLLOW`、同 fd `fstat`、单次 raw read 验证 current SHA，且以 source revision `git show` bytes 验证 blob SHA。禁止 ambient `PATH`、`which`、shell lookup、相对路径、shebang 或任何未绑定 executable。

`loader_args` 必精确为 `-I,-S,-B,-c,<64-hex bootstrap digest>,<absolute request path>,<64-hex request SHA>` 的有序 JSON-string encoding；bootstrap digest 必绑定 provenance v1.3 的 Git/current-byte verified loader。永久拒绝 direct exporter script、`-m`、缺失/重排 isolation flags、额外 argv、非 lexical python/git。

CPU fixture 必覆盖正例、python/git blob-current drift、symlink/replacement、ambient PATH shadow、loader argv reorder/extra/direct exporter、bootstrap/request SHA drift，以及无 pathname reopen。任何失败 ValueError；既有 unconditional hard-stop 不变。

请求 `APPROVE_TO_IMPLEMENT_P4_V4_EXECUTION_REQUEST_INTERPRETER_STATIC_TOOLS` 或 `REQUEST_CHANGES`（附 `file:line`）。禁止真实 preflight、staging/materialize、record/refreeze、P5 export/compose、torchrun、GPU、模型/数据/checkpoint I/O、训练/评测/推理、B2-T 或 Local Memory 训练。
