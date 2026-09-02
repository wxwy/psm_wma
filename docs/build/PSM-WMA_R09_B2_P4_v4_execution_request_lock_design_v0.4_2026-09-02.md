# R09-B2 P4-v4 Execution-Request Lock 静态设计 v0.4

**状态**：draft，替代未获实现授权的 v0.3。仅申请 root static planned-commitment tooling 与 stdlib CPU fixture；本文件冻结 P4/P5 handoff migration contract，但不授权修改或执行 P4/P5、真实 request/preflight/materialize/staging/candidate/record/refreeze、P5 export/compose、torchrun、GPU 或训练。

## 1. v0.3 review、authority 与范围

本版处理 ChatGPT review=`ef8f9e8` B1--B2；Kimi/MM 对 v0.3=`de20246` 均 `APPROVE_TO_IMPLEMENT_P4_V4_EXECUTION_REQUEST_LOCK_STATIC_TOOLS`。保留 v0.3 已关闭的 `O_RDWR|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC` single-FD output：write、fsync、same-FD seek/read-back/SHA、`fchmod(0444)`、regular+`0444` fstat、close全部成功才 `FROZEN_NOT_EXECUTABLE`；create 后任一失败为不清理/不重试的 `POISONED_NOT_LOCKED`。

`AUTHORIZED_P4_V4_LOCK_SPEC` 默认 `None`，zero-write fail-closed。未来 reviewed constant 精确为 `{schema_version,source_commit,source_tree_sha256,gitlink,spec_path,spec_git_blob_sha256,spec_current_sha256,spec_raw_sha256,output_parent,output_basename}`；只读 single-fd spec raw 同时完成 canonical parse、raw SHA、Git/blob/current equality。constant、spec、caller、CLI、cwd、环境均不得决定其他 authority。

## 2. P4/P5 handoff migration：消除 hash fixed point

现行 P5 `_validate_roster()` 将 `preflight.json` 列为 run-root regular entry；而其内容包含 result/verification SHA，后两者又包含 run roster SHA，故形成不可解的 `preflight.json -> result.json -> roster -> preflight.json` 固定点。后续 record/refreeze 不会解除该环，必须先迁移 grammar。

后续独立 reviewed **P4/P5 handoff migration Gate** 的唯一允许变更为 `r09_b2_p5_run_root_roster_v2`：`pre_p5_run_root_roster` 仍精确为 `{entries,sha256}`、`sha256=SHA256(P5 canonical_bytes({"entries":entries}))`，但 entries 的 exact path set 改为仅 `{import_staging, import_staging/<run_token>} ∪ payload_manifest.entries`；永久排除 `preflight.json` 与任何其他 P4 evidence/pointer 文件。目录 row 仍 `{path,type,mode,sha256}`=`directory/0555/""`，regular row 为 `regular/0444/<manifest SHA>`，entries 按 `path` byte lexical ascending，canonical serializer 与现有 P5 `canonical_bytes` 完全相同。

P4 request 的 `run.<backend>.roster_sha256` 在该 migration 后只绑定上述完全 pre-execution 可决定的 v2 roster SHA；P4 result 的同名 `pre_p5_run_root_roster` 与其 exact equal。`request.json`、`result.json`、`verification.json` 仍只由 P5 evidence authority 的固定路径/commit/blob binding消费；不得在 run root 写 `preflight.json` 或含 result/verification SHA 的替代 pointer。migration Gate 必同时更新 P4 producer、P5 loader/verifier、P5 design、fixture 与 evidence-authority验证，且以独立三方同 SHA review关闭；本 Gate 不实施该 migration。

## 3. exact planned commitment schema

本 Gate 输出的唯一 artifact 为 canonical `r09_b2_p4_v4_planned_roster_commitment_v1`。其 top-level key-set 精确为 `{schema_version,entry,source,interpreter,environment,authorities,backends,execution_contract,planned,commitment_sha256}`；除 `schema_version`/`commitment_sha256` 外，`entry`、`source`、`interpreter`、`environment`、`authorities`、`backends`、`execution_contract` 必为已关闭 `r09_b2_p4_v4_execution_request_v1` 的逐字节 canonical section values，使用原 validator 的 exact nested grammar及 identity SHA。`schema_version` 固定为上述字符串，`commitment_sha256=SHA256(canonical_bytes(删除该字段后的 top-level object))`。

`planned` key-set 精确为 `{recurrent,ttt_fast_weight}`，顺序固定为该 tuple。每 backend object key-set 精确为 `{backend,run_identity,run_token,candidate_root,attempt_id,staging_projection,identity_sha256}`：`backend` 为该 key；`run_identity`/`candidate_root` 均为既有 `RUN_IDENTITY_KEYS`、kind 分别 `run_root`/`candidate_root`；`run_token`/`attempt_id` 均为 lowercase 64-hex；两 backend 任一 identity/token/attempt 不得 reuse；`identity_sha256=SHA256(canonical_bytes(删除该字段后的该 backend object))`。`staging_projection` key-set 精确为 `{entries,projection_sha256}`，`projection_sha256=SHA256(P5 canonical_bytes({"entries":entries}))`，但它仅标识 projection，永久不得命名或作为 `roster_sha256` 使用。

每个 projection `entries` 必恰为第 2 节 v2 roster 的 ordered P5 row array；因此在 migration Gate 未独立关闭前，lock helper 只允许 fixture-temporary reviewed authority，production constant仍为 `None`，不得产生 final request或声称 v2 roster 已获执行资格。

## 4. static fixtures、后续门与禁止项

stdlib CPU fixtures覆盖：default authority zero-write；authority/spec所有 digest/path/identity drift；top-level、section、planned/backend、projection row/order/path/type/mode/SHA、self SHA、pair reuse与caller injection；旧 `preflight.json` row及任何 `roster_sha256` 字段拒绝；P5 v1 cycle 的构造性负例与 v2 pre-execution roster deterministic proof；same-FD write/fsync/seek/read-back/fchmod/fstat/close poison；symlink/existing target、ambient isolation、禁用 subprocess/P5 child/torch与CLI hard-stop。

本设计仅请求 `APPROVE_TO_IMPLEMENT_P4_V4_EXECUTION_REQUEST_LOCK_STATIC_TOOLS` 或 `REQUEST_CHANGES`（附 file:line）。即使 closure，P4/P5 migration、final request、record/refreeze及真实 CPU preflight都仍是独立 Gate；P5 export/compose、GPU和训练均未授权。
