# R09-B2 P4-v4 Execution Request `source` 静态合同 v0.1

**状态**：draft；仅申请 root static parser/validator tooling 与 stdlib CPU Git fixtures。

## 1. 目的与非自授权边界

本版承接已关闭的 `entry` grammar=`ad2bfcc`，为其 `root_revision`、Gitlink、Git blob 与 current-byte 提供独立 source-owned authority。request、`entry`、current `HEAD` 或 current bytes 都不能自证；验证只接受 request 声明的精确 revision，不接受 descendant。

## 2. 精确 schema 与 cross-binding

`source` 键集精确为：

```json
{"root":"<canonical absolute path>","root_revision":"<40 lowercase hex>","gitlink":"<40 lowercase hex>","entry_git_blob_sha256":"<64 lowercase hex>","entry_current_sha256":"<64 lowercase hex>","identity_sha256":"<64 lowercase hex>"}
```

所有值为字符串。`identity_sha256` 是删除自身字段后的 canonical JSON SHA256。`root` 必为 absolute、`Path.resolve(strict=True)` 后字面相等、directory、非 symlink。40/64 位字段按 v0.7 的 Git/SHA256 宽度分别验证。

`source.root_revision == entry.root_revision`、`source.entry_git_blob_sha256 == entry.git_blob_sha256`、`source.entry_current_sha256 == entry.current_sha256` 均为精确交叉绑定。

## 3. 独立 Git/current-byte authority

静态 validator 在任何 runtime 副作用前，使用 `source.root`：

1. 要求 root 与 `root/cosmos-framework` 都 full-clean（含 untracked）；两者均 Git root，子模块路径不是 symlink。
2. `git -C root rev-parse --verify <root_revision>^{commit}` 的完整输出必须字面等于 `root_revision`；`HEAD` 是否相等不作为接受条件。
3. `git -C root ls-tree <root_revision> cosmos-framework` 的唯一 gitlink 必等于 `source.gitlink`；`git -C root/cosmos-framework rev-parse HEAD` 也必须相等。
4. 固定 entry 路径必须为 root 下 tracked regular non-symlink file。`git show <root_revision>:tools/g0/r09_b2_p4_v4_execution_preflight.py` 的 bytes SHA256 必等于 `entry_git_blob_sha256`；同一路径 current bytes SHA256 必等于 `entry_current_sha256`；两项必须相等。

任何 Git 命令失败、revision 不可解析/非精确、dirty/untracked、Gitlink/submodule drift、blob/current drift、symlink/非 regular、或 cross-binding drift 均 `ValueError`，且随后既有 hard-stop 保持。

## 4. CPU 验收与范围

stdlib 临时 Git fixture 至少覆盖正例、descendant revision、dirty/untracked root、Gitlink/submodule drift、Git blob/current drift、entry/source cross-binding drift、symlink entry/root。既有 entry 6/6、single fd SHA==parsed raw 与 immutable contract regressions不得回退。

请求 `APPROVE_TO_IMPLEMENT_P4_V4_EXECUTION_REQUEST_SOURCE_STATIC_TOOLS` 或 `REQUEST_CHANGES`（附 `file:line`）。禁止真实 preflight、staging/materialize/candidate、record/refreeze、evidence publication、P5 authority/export/compose、torchrun、GPU、模型/数据/checkpoint I/O、训练/评测/推理、B2-T、Local Memory 训练。
