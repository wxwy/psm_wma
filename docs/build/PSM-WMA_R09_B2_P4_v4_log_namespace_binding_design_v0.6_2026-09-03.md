# R09-B2 P4-v4 Log Namespace Binding 设计 v0.6

**状态**：draft；仅修复 log-namespace static slice authority binding。生产 execution/record/publication authority仍 `None`，不创建或执行真实 request/preflight/log/candidate/record/P5/GPU/训练。

## 1. Opaque verifier-issued binding

`validate_logs(logs, binding)` 不再接收 mapping/tuple/path 或任何 caller namespace。binding 只能由 module-private factory `issue_log_namespace_binding(final_request, planned_commitment, p5_publication_authority)` 产生；公开构造、复制、pickle、dict/mapping 代替、可变字段与二次签发均拒绝。factory 首先调用已关闭的 final-request/planned/source/run/candidates validators 与 P5 publication-authority validator；任一 production authority为 `None` 或任一 nested identity/digest/path不匹配时 fail-before-create。

factory 从**已验证对象**唯一推导 exact namespace：source root=`final_request.source.root`，submodule root=`source root/cosmos-framework`（同时必须等于 frozen Gitlink identity），ordered run roots=`final_request.run.recurrent.identity.resolved_root`、`final_request.run.ttt_fast_weight.identity.resolved_root`，candidate root=`final_request.candidates.root.resolved_root`，six P5 paths=`p5_publication_authority.six_paths` 在其 evidence root 下的 resolved absolute paths。binding 只保存这些 verifier-derived immutable paths与其 parent request/planned/P5 raw SHA；每次 consume 重新比较 raw SHA、identity/digest与路径，不信任 caller supplied equivalent path。

## 2. Logs consume 与 fixtures

`validate_logs` 继续验证 P4 canonical self-digest、absolute lexical root、fixed `stdout.log`/`stderr.log` children与 symmetric overlap；全部 forbidden paths仅从 opaque binding取得。fixtures使用 test-local non-None mock authorities：逐一替换 source/submodule/recurrent-run/TTT-run/candidate/P5-six-path为不同但 lexical-valid identity，同时把 log root 置入真实 namespace，重算 logs SHA 后仍必须拒绝；binding reuse/forgery/mutable reset、None authority、raw-SHA/identity drift均拒绝。不得创建任何真实目录、日志或 Git publication。

## 3. Verdict

请求 `APPROVE_TO_IMPLEMENT_P4_V4_LOG_NAMESPACE_BINDING_STATIC_SLICE` 或 `REQUEST_CHANGES`（file:line）。完整 record/refreeze/CAS static-tools Gate继续 `IN_PROGRESS`。
