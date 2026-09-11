# Root Gitlink Source-audit Implementation Design v0.3

**状态**：docs-only bootstrap remediation；待三方审核。
**Gate**：`G0-R09-B-TTT-V035-CANONICAL-NATIVE-ROOT-GITLINK-AUTHORITY-SOURCE-AUDIT-IMPLEMENTATION-DESIGN`

**supersedes**：v0.2 的 bootstrap failure representation；其余 v0.1/v0.2 合同不变。

Git identity establishment 先产生 exact `root_gitlink_git_bootstrap_v1`，keys 为 `schema,status,reason,git_executable,git_executable_sha256,git_version`。`status` 仅 `READY/FAIL`；READY 时后三字段为 exact full command identity inputs；FAIL 时后三字段必须 JSON null，`reason` 仅 `GIT_MISSING`、`GIT_NOT_REGULAR_EXECUTABLE`、`GIT_UNREADABLE`、`GIT_VERSION_INVALID`。bootstrap FAIL 的 stdout exact failure object 增加 `bootstrap`，而 `command_identity` exact 为 null；exit=3、零 output mutation。只有 bootstrap READY 才构造 v0.2 full `root_gitlink_git_command_identity_v1`；之后所有 result 仍必须携带 full identity，不能为 null。

temporary-fixture unittest 必须独立覆盖 missing、non-executable、unreadable Git 与 invalid/multi-line version：分别断言 bootstrap exact fields/reason、failure stdout、`command_identity=null`、exit 3、pre-existing output bytes不变；READY case 断言 bootstrap 与 full command identity exact consistency。仍不授权代码、真实 audit、I/O、GPU或训练。

请求 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_NATIVE_ROOT_GITLINK_AUTHORITY_SOURCE_AUDIT` 或 `REQUEST_CHANGES(file:line)`。
