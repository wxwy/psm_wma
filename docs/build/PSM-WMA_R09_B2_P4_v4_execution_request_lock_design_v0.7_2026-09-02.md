# R09-B2 P4-v4 Execution-Request Lock 静态设计 v0.7

**状态**：draft，替代 v0.6；仅申请 root static planned-commitment tooling/stdlib CPU tests，禁止 P4/P5 migration implementation及任何真实执行。

保留 review=`065b45f` 已关闭的 planned-only grammar、pair candidate semantics、v2 roster migration、tree OID与same-FD poison。constant/source-root grammar不变。`spec_path` 必是 nonempty relative lexical components，拒绝 absolute、空、`.`、`..`、重复 separator；从 source-root FD 逐 parent component `openat(O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC)` + fstat directory，最终 basename 才以 `O_RDONLY|O_NOFOLLOW|O_CLOEXEC` 打开并 fstat regular，禁止链建立后重解析 pathname。fixture覆盖 intermediate symlink/retarget 和 final nofollow。

lock spec v3/commitment top-level schema不变。输出 `planned.root=spec.planned_candidates.root`、`planned.attempt_id=spec.planned_candidates.attempt_id`；每 backend **构造** `{backend,run_identity,run_token,candidate_root,staging_projection,identity_sha256}`，不是复制 candidate item：backend/candidate_root取 candidate side，run_identity/run_token 分别取 `spec.planned_run.<backend>.identity/run_token` 且强制与 candidate side对应字段相等，projection仅由 manifest+token重建，identity SHA为删除自身后 P4 canonical SHA。两 backend构造完成后，`planned.identity_sha256=SHA256(P4 canonical bytes(planned去除该字段))`。fixture拒绝 direct-copy shortcut、projection遗漏/误绑与任一映射 drift。其余 v0.6 禁止项与验收不变。

请求 `APPROVE_TO_IMPLEMENT_P4_V4_EXECUTION_REQUEST_LOCK_STATIC_TOOLS` 或 `REQUEST_CHANGES`（附 file:line）。
