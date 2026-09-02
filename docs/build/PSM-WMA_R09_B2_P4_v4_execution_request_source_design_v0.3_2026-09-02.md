# R09-B2 P4-v4 Execution Request `source` 静态合同 v0.3

**状态**：draft；仅申请 root static parser/validator tooling 与 stdlib CPU Git fixtures。本版承接 v0.2 exact-HEAD rule，并补精确 descendant fixture。

`source` 精确键为 `root,root_revision,gitlink,entry_git_blob_sha256,entry_current_sha256,identity_sha256`，全为字符串；root 是 strict-resolved absolute non-symlink directory，revision/gitlink 为 40 lowercase hex，三 SHA 为 64 lowercase hex，identity 为删除自身字段后的 canonical JSON SHA256。source revision/blob/current 必分别等于 entry；request/entry/current bytes 不能自授权。

root 与 `root/cosmos-framework` 必 full-clean（含 untracked），均为 Git root，子模块路径非 symlink。`git -C root rev-parse HEAD` 和 `rev-parse --verify <root_revision>^{commit}` 都必须字面等于 `source.root_revision`：祖先和后继一律拒绝。`git ls-tree <root_revision> cosmos-framework` 的唯一 gitlink 必等于 source 字段及子模块 HEAD。固定 entry 必为 tracked regular non-symlink；其 `git show <revision>:tools/g0/r09_b2_p4_v4_execution_preflight.py` SHA、current bytes SHA、source 声明和 entry cross-binding 均精确相等。任一失败 ValueError，既有 hard-stop 不变。

CPU Git fixture 必覆盖正例、dirty/untracked、Gitlink/submodule drift、blob/current drift、cross-binding drift、symlink root/entry、ancestor。关键永久负例：创建 A 后创建 clean descendant B，B **只修改无关 root 文件**、entry bytes 与 Gitlink 均保持 A 值；request/source 声明 A、checkout HEAD=B 时必须因 checkout revision identity FAIL，不能因 entry bytes 相同而接受。

请求 `APPROVE_TO_IMPLEMENT_P4_V4_EXECUTION_REQUEST_SOURCE_STATIC_TOOLS` 或 `REQUEST_CHANGES`（附 `file:line`）。禁止真实 preflight、staging/materialize/candidate、record/refreeze、P5 authority/export/compose、torchrun、GPU、模型/数据/checkpoint I/O、训练/评测/推理、B2-T、Local Memory 训练。
