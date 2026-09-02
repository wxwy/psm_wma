# R09-B2 P4-v4 Execution-Request Lock 静态设计 v0.5

**状态**：draft，替代 v0.4；仅申请 root static planned-commitment tooling 与 stdlib CPU fixture，禁止 P4/P5 migration implementation、真实 request/preflight/materialize/staging/candidate/record/refreeze、P5 export/compose、GPU和训练。

## 1. 固定不变项与 authority

保留 ChatGPT=`000b573` 已关闭的 v2 roster migration、P5 canonical roster hash 与 same-FD `O_RDWR → write/fsync/read-back → fchmod(0444)/fstat → close` poison contract。`AUTHORIZED_P4_V4_LOCK_SPEC` 默认 `None`。非空 constant 的 exact key-set 为 `{schema_version,source_commit,source_tree_oid,gitlink,spec_path,spec_git_blob_sha256,spec_current_sha256,spec_raw_sha256,output_parent,output_basename}`：`source_commit` 为 40 lowercase hex；`source_tree_oid` 为 `git -C <source> rev-parse <source_commit>^{tree}` 返回的 40 lowercase hex Git object id（不是 SHA256）；其余 SHA 为 lowercase 64-hex。constant/source/full-clean/Gitlink/tree/blob/current/raw 任一 drift 均 zero-write FAIL。

## 2. exact lock spec 与一对一映射

single-fd canonical spec schema 固定 `r09_b2_p4_v4_lock_spec_v2`，top-level key-set 精确为 `{schema_version,entry,source,interpreter,environment,authorities,backends,execution_contract,run,candidates,payload_manifest,lock_spec_sha256}`；`lock_spec_sha256=SHA256(P4 canonical_bytes(删除该字段后的 object))`。`entry/source/interpreter/environment/authorities/backends/execution_contract` 必逐字节等于已关闭 full-request sections；`run` 必为已关闭 exact `{recurrent,ttt_fast_weight}`；`candidates` 必为已关闭 exact `{root,attempt_id,recurrent,ttt_fast_weight,identity_sha256}`；`payload_manifest` 必为 P5 exact `{entries,sha256}`。不得存在 caller/CLI/env 填充字段。

输出 commitment 的同名 seven closed sections逐字节复制 spec；`planned` 精确为 `{root,attempt_id,recurrent,ttt_fast_weight}`：`root=spec.candidates.root`、`attempt_id=spec.candidates.attempt_id`、且两者直接 canonical-equal。每 backend exact key-set `{backend,run_identity,run_token,candidate_root,staging_projection,identity_sha256}`，其中 `backend` 为 key，`run_identity=spec.run.<backend>.identity`，`run_token=spec.run.<backend>.run_token`，`candidate_root=spec.candidates.<backend>.candidate_root`（string，且必须等于 `<planned.root.root>/<planned.attempt_id>/<backend>`），并保留既有 `attempt_id != run_token`、source/run overlap、backend candidate path/identity reuse rejection。`staging_projection.entries` 只从 `spec.payload_manifest.entries` 与该 run token按 v2 roster grammar重建；`projection_sha256` 仅为该 entries 的 P5 canonical identity，永不得写为 `roster_sha256`。每 backend、planned、commitment 的 self SHA 都是删除自身字段后的 P4 canonical SHA；输出 top-level 仍精确为 v0.4 key-set。

## 3. fixture与边界

fixture 覆盖：spec top/nested/self SHA、constant tree OID command/format drift、每个 spec→output equality、pair-level shared attempt、derived leaf、attempt/token inequality、caller injection、v2 roster projection、旧 pointer/roster SHA拒绝及 FD poison。仍不实施 migration 或生成 final request。

仅请求 `APPROVE_TO_IMPLEMENT_P4_V4_EXECUTION_REQUEST_LOCK_STATIC_TOOLS` 或 `REQUEST_CHANGES`（附 file:line）。
