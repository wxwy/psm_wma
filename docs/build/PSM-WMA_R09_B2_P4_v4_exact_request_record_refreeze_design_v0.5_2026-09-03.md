# R09-B2 P4-v4 Exact Request / Record-Refreeze 设计 v0.5

**状态**：draft，替代未获实现批准的 v0.4；仅 root static tooling/stdlib fixtures，绝不创建或执行真实 request/preflight/candidate/record/P5/GPU/训练。

## 1. Canonical identity、authority 与 final request

所有本 Gate JSON self-digest 均为 `SHA256(P4 canonical JSON bytes: sort_keys=True,separators=(",",":"),ensure_ascii=True, trailing newline)`，且仅覆盖去除自身 `sha256` 后的 exact object。`tree_sha256` 不属于该规则：它始终是 `SHA256(raw bytes from git cat-file tree <commit-or-tree-oid>)`；Git tree OID 是独立的 40 位 lowercase hex identity，必要时仅由 verifier 从对应 commit 推导，绝不以 OID 冒充 `tree_sha256`。production execution/record/publication authority均 `None`。

`source_binding_v1={root,resolved_root,revision,tree_sha256,gitlink,paths,sha256}`。root/resolved_root为相同的 canonical absolute lexical、non-symlink repository root；revision/gitlink为 lowercase 40 位 hex；tree_sha256、git_blob_sha256、current_sha256为 lowercase 64 位 hex；`paths`为 path 升序 ordered list，每一项 exact `{path,git_blob_sha256,current_sha256}`，path 为 nonempty relative lexical、无 `.`/`..`/空 segment/absolute form，且不重叠。所有 current bytes、Git blob 与 source tree raw-byte SHA 均须由 verifier single-read/rederive。

`command_v1={argv,cwd,environment,sha256}`：argv 为 nonempty ordered `list[str]`，每项 nonempty、无 NUL；cwd 为 source resolved_root 内 canonical absolute lexical non-symlink directory；environment 为 key 升序 mapping，key 匹配 `[A-Z_][A-Z0-9_]*`、value 为无 NUL string，且仅 frozen P3 backend delta 可不同。`resources_v1={cpu_max,wall_seconds,network,gpu,torch,torchrun,sha256}`：cpu_max 为整数 core 上限 `1..64`，wall_seconds 为整数 seconds 上限 `1..86400`；仅 network/gpu/torch/torchrun 四个 boolean 固定 false。

`logs_v1={root,stdout,stderr,sha256}`：root 为 caller-independent、canonical absolute lexical non-symlink path，pre-execution 必须 absent，且与 source root/`cosmos-framework`、两个 run root、`candidates.root` 及其所有 attempt/backend descendants、固定 P5 evidence publication 六路径两两 non-overlap；stdout/stderr 是 root 下 exact basenames `stdout.log`/`stderr.log`，不接受别名或 json target。verifier 单次创建 root（mode `0700`）并唯一拥有其生命周期；after-execution root 必为 non-symlink directory，且仅含 stdout/stderr 两个 non-symlink regular files（mode `0600`）。任何创建、写入、失败或日志保留都不得在 candidate namespace 新增/替换文件。candidate `result.json` 仅是既有 request/result/verification chain 的 canonical payload：logging layer 不创建、不替换、不重序列化它。`stop_v1={fail_on,one_shot,cleanup_retry_repair,sha256}`：fail_on 为 exact ordered list `["nonzero_exit","timeout","signal","output_contract_violation"]`，one_shot=true，cleanup_retry_repair=false。`execution_authority_v1` exact `{schema_version,planned_raw_sha256,planned_source,request_raw_sha256,request_path,source,command,resources,logs,stop,sha256}`；每一 nested object 都必须满足前述 key、type、range、path、order 与 self-digest grammar。

final P4 request仍仅旧 key-set。逐 backend：run identity/token/roster取 planned `run_identity/run_token/staging_projection.projection_sha256`；candidates root/attempt取 planned root/attempt；candidate item exact `{backend,candidate_root,run,identity_sha256}`，backend固定、candidate_root取 planned、run为 final run，item SHA由去自身 P4 canonical重算；outer candidates SHA同法重算。无 caller field可存活。

## 2. Candidate provenance与record authority

`candidate_expectation_v1` exact `{parent_request_raw_sha256,planned_raw_sha256,backend,request_fields,result_chain,verification_chain,cross_pair,sha256}`。request_fields 对每个 request.json key指定唯一 authority：backend/p4_run/p4_staging来自 final/planned；production_source/request_defaults/interpreter/loader_argv/environments/producer来自 closed source/interpreter/environment/authority validators；payload_manifest为 finalized staging runtime observation并由 v2 manifest validator复验。result_chain要求 request SHA及所有 request-owned fields exact、native_closure/roster为 named runtime observations并经 closed validators；verification_chain要求 request/result SHA、exact verifier identity/check set。cross_pair是 exact `{shared,backend_owned,sha256}`，shared含 source/interpreter/entry/authorities/execution contract/planned/attempt/root，backend_owned仅 backend/run/token/roster/P3 selector/TTT env。

`record_authority_v1` exact `{schema_version,parent_request_raw_sha256,planned_raw_sha256,attempt_id,candidate_root,expectations,payload_sha256,cross_pair_sha256,sha256}`；仅由已验证 expectations及六 raw bytes生成，绝不接收 caller payload SHA。不同但自身有效的 pair 必在 parent join拒绝；link永不发布。

## 3. Record commit、clean-base CAS与post-CAS materialize

`record_publication_authority_v1` exact `{schema_version,evidence_source,ref,base_commit,base_tree_sha256,base_gitlink,six_paths,payload_sha256,sha256}`。base_commit/base_gitlink为 lowercase 40 位 hex；base_tree_sha256采用第 1 节 raw Git-tree bytes 定义；six_paths 为 exact six relative lexical paths，payload_sha256仅由 six verified raw bytes rederive。

唯一模型是 checked-out target-ref 的 clean-base plumbing model。Pre-CAS 必须验证 root/submodule full-clean、`HEAD==ref==base_commit`、current index `write-tree==base_tree_oid`、base raw-tree SHA等于 base_tree_sha256、六 target paths absent/non-symlink。随后仅使用 verifier-owned temporary index（不得修改 current checkout/index/worktree）由六个 verified 100644 blobs构造 new_tree；其与 base tree 的 diff 精确为该六路径、Gitlink与其余 entries不变。仅在 temporary index 中创建 new commit，并验证其 tree==new_tree、sole parent==base_commit、new_tree raw bytes SHA 与 verifier rederive值一致。唯一 publication primitive 为一次 `update-ref ref new_commit base_commit` CAS。

CAS 成功后，verifier 必须执行一次、不可重试的 checked-out materialize：`git read-tree --reset -u new_tree`，不得使用 ambient/manual reset、checkout 或 repair。随后验证 `HEAD==ref==new_commit`、commit tree==new_tree、sole parent==base、current `write-tree==new_tree`、root/submodule full-clean、六 current bytes/100644/blob精确且无其余 diff。CAS 前失败无权威发布；CAS 失败不自动 repair/retry。CAS 成功而 materialize 或最终验证失败时，状态永久为 `POISONED_PUBLISHED`：不得 retry/repair、不得生成 P5 authority、不得以该 ref/commit 继续执行。

fixtures永久覆盖：所有 nested extra/missing/type/range/unit/boolean/value drift，argv/env/log-root path substitution、overlap/symlink/ambient redirect，pre/post log lifecycle，logged PASS candidate exact four-file set，candidate namespace 任意 stdout/stderr injection拒绝，final candidates dimensions，tree OID 替代 raw-tree SHA、correct OID 配错误 raw-tree SHA、错误 tree bytes，foreign valid pair parent join，dirty/staged/untracked/base/Gitlink/target/symlink/unrelated injection/blob failure，wrong-parent/merge/correct-tree，CAS race，post-CAS materialize failure与最终 clean verification failure。不得修改 `r09_b2_p4_v4_static_contract.py` 的 closed candidate file-set semantics。

## 4. Verdict

请求 `APPROVE_TO_IMPLEMENT_P4_V4_EXACT_REQUEST_RECORD_REFREEZE_STATIC_TOOLS` 或 `REQUEST_CHANGES`（file:line）。不授权真实副作用或 P5 authority。
