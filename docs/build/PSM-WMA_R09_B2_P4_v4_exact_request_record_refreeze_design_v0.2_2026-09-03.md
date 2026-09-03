# R09-B2 P4-v4 Exact Request / Record-Refreeze 设计 v0.2

**状态**：draft，替代未获实现批准的 v0.1；仅申请 root static tooling/stdlib fixtures，禁止真实 request/preflight/staging/candidate/record/P5/GPU/训练。

## 1. 不变前置与 final-request mapping

前置为 P4 request static=`8535a8c`、planned-lock=`4108eb6`、materialization=`bda9737`、handoff=`28b8592`/ChatGPT=`90cb466`，Gitlink=`21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`。既有 P4 request wire key-set 永远保持 `{schema_version,entry,source,interpreter,environment,run,candidates,backends,authorities,execution_contract}`，不得加入 command/path/SHA。

final request 仅由 verified planned commitment 构造：所有 closed `entry/source/interpreter/environment/backends/authorities/execution_contract` semantic-identical；每 backend `run.identity/run_token`、`candidates.root/attempt_id` exact 取 commitment planned side；`run.roster_sha256` exact 等于同侧 `staging_projection.projection_sha256`；任何 caller run/root/token/roster 值拒绝。

## 2. Execution freeze authority

新增 verifier-owned `execution_authority_v1`，exact keys `{schema_version,planned_raw_sha256,planned_source,request_raw_sha256,request_path,source,command,cwd,environment,resources,logs,stop,sha256}`；`sha256=SHA256(P4 canonical bytes(without sha256))`。`planned_source` 与 `source` 各冻结 repo root/revision/tree/Gitlink/blob/current bytes；`command` 是 exact argv，`resources/logs/stop` 是 closed schemas。生产 `AUTHORIZED_P4_V4_EXECUTION_AUTHORITY=None`。未来 executable 必按 authority single-read raw/path/SHA/argv/cwd/environment逐项比较，不能信任 caller `--request`/`--request-sha256`；None 必 fail-before-create/execute。

fixtures覆盖 alternate-valid request、command/path/SHA substitution、planned→final每字段 drift及 None。

## 3. Candidate binding 与 record authority

`record_authority_v1` production default `None`，exact绑定 parent request raw/SHA、planned SHA、attempt/candidate root、两 backend run roots/tokens/rosters、六 payload SHA256、以及 cross-pair contract SHA。candidate request/result/verification必须由 parent request deterministic mapping复验；不同 request/attempt/token/root 的完整有效 pair拒绝。candidate link只验证、不发布。

cross-pair contract固定：source/interpreter/entry/authorities/execution_contract、planned SHA、attempt/candidate root相同；backend/run identity/token/roster、P3 selector与唯一 `PSM_R09_B1_TTT_ENABLED` 是 backend-owned；其他 environment/effective launch字段 exact-equal。每个绑定均有 mutation fixture。

## 4. Git record publication authority / CAS

`record_publication_authority_v1` default `None` 精确含 evidence repo identity、target ref、base commit/tree/Gitlink、six fixed paths、six raw SHA及自身 digest。发布前 root/submodule full-clean、index==base、HEAD/ref==base、目标均 absent/non-symlink；构造 new tree 并验证 `diff(base_tree,new_tree)` 恰为六个 `100644` regular blobs、Gitlink及其他 tree entries不变。仅 `update-ref <ref> <new> <base>` CAS 可发布；任何失败在最终 CAS 前均无 authoritative ref publication，允许的 dangling object非权威，worktree/index partial永不被 P5 接受。ref race/dirty/staged/untracked/base/Gitlink/target/symlink/unrelated injection/blob failure/六路径 diff均须 fixture。

record 不得写 `AUTHORIZED_P4_V4_EVIDENCE`；仅后续独立 reviewed P5 verifier revision可冻结 resulting commit/tree/blobs。

## 5. Verdict

请求 `APPROVE_TO_IMPLEMENT_P4_V4_EXACT_REQUEST_RECORD_REFREEZE_STATIC_TOOLS` 或 `REQUEST_CHANGES`（附 `file:line`）。本 Gate绝不授权真实执行。
