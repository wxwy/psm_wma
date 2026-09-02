# R09-B2 P4-v4 Execution-Request Lock 静态设计 v0.6

**状态**：draft，替代 v0.5；只申请 root static planned-commitment tooling 与 stdlib CPU tests。禁止 P4/P5 migration implementation、真实 request/preflight/materialize/staging/candidate/record/refreeze、P5 export/compose、GPU和训练。

## 1. retained contracts 与 authority source root

保留 ChatGPT=`82c567c` 已接受的 v2 roster migration、P5 canonical hash、pair candidate namespace、Git `source_tree_oid` 与 same-FD poison contract。`AUTHORIZED_P4_V4_LOCK_SPEC` 默认 `None`；非空 constant key-set 变为 `{schema_version,source_root,source_commit,source_tree_oid,gitlink,spec_path,spec_git_blob_sha256,spec_current_sha256,spec_raw_sha256,output_parent,output_basename}`。`source_root` 是 absolute lexical string，逐 `/` component 以 `O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC` openat/fstat 锚定，所有 component 必为 directory、无 symlink；该 FD 是唯一 spec relative path `openat(..., O_NOFOLLOW)` 的 root。其 Git top-level、HEAD、`rev-parse <source_commit>^{tree}`、Gitlink、tracked blob/current/raw SHA 都必须与 constant 相等；任何失败 zero-write。

## 2. exact planned-only spec / commitment

lock spec schema 固定 `r09_b2_p4_v4_lock_spec_v3`，key-set 精确为 `{schema_version,entry,source,interpreter,environment,authorities,backends,execution_contract,planned_run,planned_candidates,payload_manifest,lock_spec_sha256}`，self SHA 为删除该字段后的 P4 canonical SHA。前七 closed sections逐字节使用 full-request grammar；没有 `run`、`candidates`、`roster_sha256` 字段。

`planned_run` 精确为 `{recurrent,ttt_fast_weight}`；每 backend key-set `{identity,run_token,identity_sha256}`，identity 是 closed `RUN_IDENTITY_KEYS` kind=`run_root`、run_token 64 lowercase hex、identity SHA为删除自身字段的 P4 canonical SHA。pair identity/token均不 reuse。

`planned_candidates` 精确为 `{root,attempt_id,recurrent,ttt_fast_weight,identity_sha256}`：root 是 closed candidate-root identity、attempt_id 为 shared 64 lowercase hex且不等于任一 planned run token；每 backend key-set `{backend,candidate_root,run_identity,run_token,identity_sha256}`，candidate_root 是唯一 string `<root.root>/<attempt_id>/<backend>`，run fields exact equal planned_run side，self SHA按同一 rule。所有已关闭 source/run overlap、future lexical、derived leaf与reuse规则沿用。

输出 `r09_b2_p4_v4_planned_roster_commitment_v1` top-level key-set 精确为 `{schema_version,entry,source,interpreter,environment,authorities,backends,execution_contract,planned,commitment_sha256}`。同名 seven closed sections逐字节复制；`planned` key-set 精确为 `{root,attempt_id,recurrent,ttt_fast_weight,identity_sha256}`，前四项逐字节复制 `planned_candidates`，`identity_sha256=SHA256(P4 canonical_bytes(planned without identity_sha256))`。每 backend key-set `{backend,run_identity,run_token,candidate_root,staging_projection,identity_sha256}`，前四字段唯一映射 planned fields；projection只从 payload manifest+token构建 v2 rows，永不带 `roster_sha256`。

## 3. fixtures与边界

fixtures覆盖 source-root lexical/ancestor/symlink/FD retarget、spec nofollow及每 constant Git binding；所有 planned-only key/mapping/self-SHA drift；注入 final run/candidate/roster SHA拒绝；shared attempt/derived leaf；v2 roster projection和same-FD poison。不得实现 migration或产生 final request。

请求 `APPROVE_TO_IMPLEMENT_P4_V4_EXECUTION_REQUEST_LOCK_STATIC_TOOLS` 或 `REQUEST_CHANGES`（附 file:line）。
