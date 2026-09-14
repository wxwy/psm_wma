# Stage-1 v1.7 request-instance design v0.4

**Gate**：`G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-DESIGN`。
**状态**：docs-only v0.3 remote-observation remediation；与v0.3冲突时以本文为准，其余冻结依赖、two-query allowlist、输出路径、zero-mutation、one-request/no-retry和禁止边界保持不变。

## Remote-query success contract

在v0.3允许的两条且仅两条查询中：

```text
git ls-remote origin refs/heads/V2
git ls-remote origin refs/heads/authority/r09-b-ttt-v035-immutable-source-v1
```

每条查询都必须在冻结超时内以`returncode == 0`完成。canonical request 必须分别绑定命令、return code、stdout 原始bytes的length/SHA和stderr原始bytes的length/SHA；不得以空stdout代替成功状态。

fixed authority ref 的remote absence唯一成立条件为：第二条精确查询成功、stdout bytes长度为零、result lines为零且stderr bytes长度为零。非零return code、timeout、transport/auth/DNS错误、任何stderr、malformed response或非空stdout均为`BLOCKED_AUTHORITY_NOT_CLOSED`，不得解释为absence。V2 query同样只有成功返回才可作为advertised identity。

本修订仍不授权request construction、materialization/retry、launcher/materializer执行、source/checkpoint/manifest/data/cache/runtime I/O、child/runtime mutation、GPU/CUDA/torchrun、训练、评测、推理或LIBERO4IN1。获同pair三方`APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE`后，才仅可构造一份future docs-only exact request；该request仍须独立三方审核。

Requested verdict: `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE` or `REQUEST_CHANGES(file:line)`.
