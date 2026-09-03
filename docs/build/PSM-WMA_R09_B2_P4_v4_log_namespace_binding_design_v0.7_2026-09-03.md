# R09-B2 P4-v4 Log Namespace Binding 设计 v0.7

**状态**：draft；仅修复 log-namespace static slice 的 pre-execution authority binding。production execution/record/publication authority仍 `None`；不创建或执行真实 request/preflight/log/candidate/record/P5/GPU/训练。

## 1. Pre-execution P5 namespace plan

新增本 slice 自己的纯 `p5_namespace_plan_v1` validator 与 verifier-owned authority。exact object 是 `{schema_version,evidence_root,ref,six_relative_paths,sha256}`：`evidence_root` 为 canonical absolute lexical non-symlink path；`ref` 为 lowercase 40-hex identity；`six_relative_paths` 是 fixed backend/file-name grammar 导出的有序六条 nonempty relative lexical path，均在 `evidence_root` 下、无重叠；`sha256` 为 P4 canonical self-digest。它**不含且不依赖** candidate `payload_sha256`、record commit/tree/CAS 或任何 post-preflight observation。production `P5_NAMESPACE_PLAN_AUTHORITY=None`，所以 production issuance 继续 fail-closed。

该 plan 是 preflight 前已有的 namespace identity；将来 `record_publication_authority_v1` 可独立重验同一六路径并额外绑定 verified payload bytes/record/CAS，但绝不反向成为本 binding 的前置。

## 2. Opaque verifier-issued binding

`validate_logs(logs, binding)` 不接收 mapping/tuple/path 或 caller namespace。binding 只能由 module-private `issue_log_namespace_binding(final_request, planned_commitment, p5_namespace_plan)` 产生；公开构造、复制、pickle、dict/mapping 代替、可变字段与二次签发均拒绝。factory 仅调用已关闭的 final-request/planned/source/run/candidates validators以及本 slice 新的 `p5_namespace_plan_v1` validator；production authority为 `None`、任何 pre-execution identity/digest/path drift均 fail-before-create。

factory 唯一派生 forbidden namespace：source root=`final_request.source.root`；submodule root path必须精确为`source_root / "cosmos-framework"`，且独立 `gitlink` 必须等于 `validated_source.gitlink` 的 lowercase 40-hex identity（filesystem/Git verification范围内再单独交叉检查 submodule HEAD/Gitlink）；ordered run roots为 recurrent、TTT `identity.resolved_root`；candidate root为 `candidates.root.resolved_root`；P5 six paths为 `p5_namespace_plan.evidence_root / six_relative_paths`。binding 仅保存上述 immutable verifier-derived paths，以及 final-request/planned/source/run/candidate/P5-plan raw SHA/digest；consume 每次重验这些 pre-execution identities，不信任 caller supplied equivalent path，绝不读取 record payload SHA。

## 3. Fixtures、范围与 verdict

fixtures使用 test-local non-None pre-execution plan，证明无 candidate payload 时仍可签发；逐一替换 source/submodule/recurrent-run/TTT-run/candidate/P5-six-path为 lexical-valid identity并重算 logs SHA仍拒绝；wrong plan digest/path-set、post-preflight record/publication authority缺失或出现均不得影响 issuance；binding forge/copy/reuse/reset、plan/production-None以及 raw-SHA/identity drift均 fail-closed。不得创建真实目录、日志、Git publication或运行 child。

请求 `APPROVE_TO_IMPLEMENT_P4_V4_LOG_NAMESPACE_BINDING_STATIC_SLICE` 或 `REQUEST_CHANGES`（file:line）。完整 record/refreeze/CAS static-tools Gate继续 `IN_PROGRESS`。
