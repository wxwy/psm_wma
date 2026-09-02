# R09-B2 P4-v4 Execution Request `source` 静态合同 v0.2

**状态**：draft；仅申请 root static parser/validator tooling 与 stdlib CPU Git fixtures。本版替代未批准 v0.1，整改 Kimi `REQUEST_CHANGES` 的 descendant 语义冲突。

## 1. 精确 source-owned authority

`source` 精确键为 `root,root_revision,gitlink,entry_git_blob_sha256,entry_current_sha256,identity_sha256`，全为字符串；`root` 是 strict-resolved absolute non-symlink directory，`root_revision`/`gitlink` 是 40 lowercase hex，三 SHA 为 64 lowercase hex，`identity_sha256` 为删除自身字段后的 canonical JSON SHA256。

`source.root_revision == entry.root_revision`，且两 entry blob/current SHA 分别相等。request/entry/current bytes 都不自授权。

## 2. exact-HEAD rule（无 descendant 例外）

root 与 `root/cosmos-framework` 必 full-clean（含 untracked），均为 Git root，子模块路径非 symlink。`git -C root rev-parse HEAD` 必字面等于 `source.root_revision`；因此 request revision 必是当前 exact checked-out commit，任何祖先/后继（含 clean descendant）均 FAIL。`git rev-parse --verify <revision>^{commit}` 同样必须字面相等。

`git ls-tree <root_revision> cosmos-framework` 的唯一 gitlink 必等于 `source.gitlink`，且 `git -C root/cosmos-framework rev-parse HEAD` 也相等。固定 entry 路径必须 tracked regular non-symlink；`git show <root_revision>:tools/g0/r09_b2_p4_v4_execution_preflight.py` 的 SHA256 与 current bytes SHA256 必分别等于 source 声明、entry cross-binding，并彼此相等。

任一 Git/路径/cleanliness/Gitlink/blob/current/cross-binding mismatch 均 `ValueError`，随后既有 hard-stop 保持。

## 3. CPU 验收与范围

stdlib 临时 Git fixture 覆盖正例、祖先 revision、clean descendant HEAD、dirty/untracked、Gitlink/submodule drift、blob/current drift、cross-binding drift、symlink root/entry；所有负例 fail-closed。既有 entry 6/6、单 fd SHA==parsed raw、immutable-contract regressions 不回退。

请求 `APPROVE_TO_IMPLEMENT_P4_V4_EXECUTION_REQUEST_SOURCE_STATIC_TOOLS` 或 `REQUEST_CHANGES`（附 `file:line`）。禁止真实 preflight、staging/materialize/candidate、record/refreeze、evidence publication、P5 authority/export/compose、torchrun、GPU、模型/数据/checkpoint I/O、训练/评测/推理、B2-T、Local Memory 训练。
