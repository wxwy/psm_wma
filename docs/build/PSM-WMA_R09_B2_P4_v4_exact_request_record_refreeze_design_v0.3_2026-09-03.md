# R09-B2 P4-v4 Exact Request / Record-Refreeze 设计 v0.3

**状态**：draft，替代未获实现批准的 v0.2；仅 root static tooling/stdlib fixtures，绝不创建或执行真实 request/preflight/candidate/record/P5/GPU/训练。

## 1. Canonical authorities与final request

所有本 Gate 新 digest 均为 `SHA256(P4 canonical JSON bytes: sort_keys=True,separators=(",",":"),ensure_ascii=True, trailing newline)`；production execution/record/publication authority均 `None`。

`source_binding_v1={root,resolved_root,revision,tree_sha256,gitlink,paths,sha256}`，`paths`为 ordered `{path,git_blob_sha256,current_sha256}`，所有 key exact、路径 relative lexical。`command_v1={argv,cwd,environment,sha256}`；`resources_v1={cpu_max,wall_seconds,network,gpu,torch,torchrun,sha256}`，后五值固定 false；`logs_v1={stdout,stderr,json,sha256}`；`stop_v1={fail_on,one_shot,cleanup_retry_repair,sha256}`，one_shot true且 cleanup_retry_repair false。`execution_authority_v1` exact `{schema_version,planned_raw_sha256,planned_source,request_raw_sha256,request_path,source,command,resources,logs,stop,sha256}`。

final P4 request仍仅旧 key-set。逐 backend：run identity/token/roster取 planned `run_identity/run_token/staging_projection.projection_sha256`；candidates root/attempt取 planned root/attempt；candidate item exact `{backend,candidate_root,run,identity_sha256}`，backend固定、candidate_root取 planned、run为 final run，item SHA由去自身 P4 canonical重算；outer candidates SHA同法重算。无 caller field可存活。

## 2. Candidate provenance与record authority

`candidate_expectation_v1` exact `{parent_request_raw_sha256,planned_raw_sha256,backend,request_fields,result_chain,verification_chain,cross_pair,sha256}`。request_fields 对每个 request.json key指定唯一 authority：backend/p4_run/p4_staging来自 final/planned；production_source/request_defaults/interpreter/loader_argv/environments/producer来自 closed source/interpreter/environment/authority validators；payload_manifest为 finalized staging runtime observation并由 v2 manifest validator复验。result_chain要求 request SHA及所有 request-owned fields exact、native_closure/roster为 named runtime observations并经 closed validators；verification_chain要求 request/result SHA、exact verifier identity/check set。cross_pair是 exact `{shared,backend_owned,sha256}`，shared含 source/interpreter/entry/authorities/execution contract/planned/attempt/root，backend_owned仅 backend/run/token/roster/P3 selector/TTT env。

`record_authority_v1` exact `{schema_version,parent_request_raw_sha256,planned_raw_sha256,attempt_id,candidate_root,expectations,payload_sha256,cross_pair_sha256,sha256}`；仅由已验证 expectations及六 raw bytes生成，绝不接收 caller payload SHA。不同但自身有效的 pair 必在 parent join拒绝；link永不发布。

## 3. Record commit与checked-out CAS

`record_publication_authority_v1` exact `{schema_version,evidence_source,ref,base_commit,base_tree_sha256,base_gitlink,six_paths,payload_sha256,sha256}`。仅 checked-out target-ref 模型：CAS前 worktree/index精确准备 verified new_tree，root/submodule full-clean，HEAD==ref==base、write-tree==base；new commit必须 exact new_tree、单一 parent且 parent==base（metadata记录为待后续review输出，非 authority）。CAS仅 `update-ref ref new base`。

CAS成功后立即验证 HEAD==ref==new、commit tree==new_tree、sole parent==base、write-tree==new_tree、root/submodule full-clean、六 current bytes/100644精确且无其余 diff。失败前无权威发布；CAS失败不自动 repair/retry。fixtures覆盖所有 nested key drift、final candidates dimensions、foreign valid pair parent join、wrong-parent/merge/correct-tree、race及成功后 index/worktree clean。

## 4. Verdict

请求 `APPROVE_TO_IMPLEMENT_P4_V4_EXACT_REQUEST_RECORD_REFREEZE_STATIC_TOOLS` 或 `REQUEST_CHANGES`（file:line）。不授权真实副作用或 P5 authority。
