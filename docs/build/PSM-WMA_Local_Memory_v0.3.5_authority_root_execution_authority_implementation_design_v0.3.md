# Authority-root Execution Authority Implementation 设计 v0.3

本版替代 v0.2，仅补 ChatGPT 对 `e69d78c` 的 local-config HIGH；其他合同与两文件 CPU/static 边界不变。

## 冻结 local-config authority ABI

parser/invocation/Evidence-v1 新增 exact-key `git_dir`、`git_config_path`、`git_config_raw_sha256`、`git_config_allowlist`。`git_dir` 只由 `git rev-parse --git-dir` 的绝对路径经 lstat regular/non-symlink Git-dir marker 和 `Path.resolve()`后得到；`git_config_path` 必须精确为`git_dir/config`，不得由alias、环境或config指定。运行时在首个 object/ref/transport action前以同一打开文件的 raw SHA复算，并以canonical JSON字节比较allowlist。

allowlist是唯一固定 mapping：`core.repositoryformatversion`值`"0"`、`core.filemode`值`"true"|"false"`、`core.bare`值`"false"`、`core.logallrefupdates`值`"true"|"false"`、`core.worktree`等于冻结 cwd、`extensions.worktreeconfig`值`"false"`。空config亦允许。所有重复key、include/includeIf、url、remote、protocol、alias、filter、core.hooksPath、core.attributesFile及任何未列 key一律拒绝。`git config --no-includes --local --null --list`的解析结果必须与冻结allowlist一一相等。

`git_isolation_fingerprint`由production code计算为`sha256(canonical_json({exact_env,exact_prefix,endpoint_grammar,git_dir,git_config_raw_sha256,git_config_allowlist}))`；不得由caller传入。Evidence verifier exact-check四个ABI字段、fingerprint与运行时重算值。

existing test须经temporary repo/native Git path覆盖：空config、每个allowlist正例；extra key、重复key、changed SHA、symlink config、include/url rewrite/remote alias等负例均在首个authority action前拒绝；保留temporary bare remote真实CAS witness。未获三方批准前不得实现或真实执行。

请求唯一`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_AUTHORITY_ROOT_EXECUTION_AUTHORITY_CPU_STATIC`或`REQUEST_CHANGES(file:line)`。
