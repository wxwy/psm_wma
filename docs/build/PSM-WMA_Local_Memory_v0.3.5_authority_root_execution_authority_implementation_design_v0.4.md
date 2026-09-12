# Execution-authority implementation 设计 v0.4

替代v0.3，仅关闭 linked-worktree common-config HIGH；保留全部既有两文件CPU/static边界。

production 在第一项 object/ref/transport action前，以已冻结Git executable/env/prefix运行 `git rev-parse --absolute-git-dir` 与 `git rev-parse --git-common-dir`，两个结果必须为absolute、existing directory、lstat non-symlink，`resolve()`后仍在冻结 repository root内；分别作为`git_dir`、`git_common_dir` typed identity。`extensions.worktreeConfig`必须在common config中不存在或为`false`；因此唯一config authority为`git_common_dir/config`，worktree admin dir的`config.worktree`必须absent。其absolute path、same-FD raw SHA、canonical parsed allowlist mapping与fingerprint均进入invocation/Evidence exact keys。

`git config --no-includes --local --null --list`必须在同一resolved common directory执行；其canonical parsed mapping必须逐字等于从same-FD raw config解析的mapping，任一view/path/bytes mismatch fail-closed。allowlist沿用v0.3；空或其合法子集接受。

direct native tests必须创建actual linked/detached temporary worktree：common config含forbidden url/remote/include、per-worktree admin无config时preflight在action前拒绝；minimal accepted common config+absent worktree config正例通过；symlink escape、worktreeConfig true、config.worktree出现、common/raw-vs-Git-view divergence均拒绝。保留bare-remote CAS witness。请求唯一`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_AUTHORITY_ROOT_EXECUTION_AUTHORITY_CPU_STATIC`。
