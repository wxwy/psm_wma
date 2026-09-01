# R09-B2 P5 Full Resolved-Config Diff 静态设计 v0.8

**状态**：draft。v0.8 替换 v0.7，仅收紧 review `2026-09-02_R09_B2_P5_v07_design_71a4b9f_7effe67.md` 所要求的 executable grammar；v0.7 的范围、禁止执行、verified lexical loader、attempt 与 P3 resolved-config diff 合同保持不变。

## 1. 唯一前置 Gate 与固定发现

P5 implementation 的唯一 P4 handoff 是独立三方批准并实际产生 `PASS` 的 `G0-R09-B2-P4-V4-EXECUTION-PREFLIGHT`。在该 Gate 的设计、static tooling、record/refreeze、一次性 preflight execution 和 evidence verification 都未完成前，P5 parent/verifier 必须以 `BLOCKED` 停止，绝不根据历史 v2 `p4_launch_d005`、v3 static D005 template 或 caller 参数补推字段。

每个 backend 的证据只能从已绑定且 full-clean 的 `evidence_root` 固定读取：

```text
artifacts/g0/r09/b2/p4_execution_preflight_v4/<backend>/request.json
artifacts/g0/r09/b2/p4_execution_preflight_v4/<backend>/result.json
artifacts/g0/r09/b2/p4_execution_preflight_v4/<backend>/verification.json
```

`backend` 固定有序数组 `["recurrent", "ttt_fast_weight"]`。P5 CLI/request 不含 evidence path、schema、digest、path allowlist 或 backend 枚举；verifier 以自身 Git blob/current bytes 绑定的 literal 发现它们。任一文件不是 regular non-symlink、相对路径不精确、Git blob/current bytes SHA 不等或 evidence/exporter/source Git root（含 submodule）非 tracked+untracked full-clean，均 pre-spawn `FAIL`。

## 2. exact P4-v4 JSON schema 与 SHA 链

所有 JSON 采用 UTF-8、canonical JSON（object key lexicographic、无空白、array order preserved），拒绝重复 key、缺 key 和额外 key。`*_sha256` 若描述文件/目录/manifest，则是该 bytes/tree manifest SHA256；若描述 JSON object 本身，则是删除该 digest 字段后的 canonical SHA256，避免循环自证。每 backend 的对象精确如下。

```text
path_identity = {"root","resolved_root","kind","identity_sha256"}
  kind ∈ {"git_source","run_root","staging_root","git_evidence","git_exporter"}
  root == resolved_root == canonical absolute path

production_source = {"identity","revision","gitlink","submodule_revision","toml"}
toml = {"path","git_blob_sha256","current_sha256"}
p4_run = {"identity","run_token","roster_sha256"}
p4_staging = {"identity","relative_path","readonly","manifest_sha256","payload_import_roots","runtime_sys_path"}
payload_import_roots = [{"relative_root","subtree_manifest_sha256"}] in runtime order; runtime_sys_path is the exact ordered absolute-path array
interpreter = {"lexical_launcher","base_executable","stdlib","lib_dynload","identity_sha256"}
loader_argv = {"argv","request_token_index","loader_literal_sha256","bootstrap_git_blob_sha256","bootstrap_current_sha256"}
environment = {"set","unset","inherit_allowlist","sha256"}
native_closure = [{"path","sha256","elf_interpreter","needed","rpath","runpath","resolved_by"}] sorted by path
roster = {"entries","sha256"}; entries = [{"path","type","mode","sha256"}] sorted by path
tool_identity = {"root_revision","tool_path","git_blob_sha256","current_sha256","sha256"}
```

`request.json` keys 精确为 `{schema_version,backend,production_source,p4_run,p4_staging,request_defaults,interpreter,loader_argv,effective_environment,native_loader_environment,payload_manifest,producer}`；`request_defaults={toml,ordered_overrides,canonical_sha256}`，`payload_manifest={entries,sha256}`，`producer=tool_identity`。

`result.json` keys 精确为 `{schema_version,status,backend,request_sha256,production_source,p4_run,p4_staging,request_defaults,interpreter,loader_argv,effective_environment,native_loader_environment,payload_manifest,native_closure,pre_p5_run_root_roster,producer}`，并要求其除 `status,native_closure,pre_p5_run_root_roster` 外每字段 canonical-equal request；`status=="PASS"`；`request_sha256==SHA256(request.json)`；`pre_p5_run_root_roster=roster`。

`verification.json` keys 精确为 `{schema_version,status,backend,request_sha256,result_sha256,checks,verifier,verification_sha256}`；`status=="PASS"`；前两 digest 分别绑定实际 request/result bytes；`checks` 是固定有序数组 `["request_schema","result_schema","paths","source","staging_manifest","staging_readonly","runtime_sys_path","environment","native_closure","run_root_roster","producer"]` 的 exact `{name,passed}` entries；`verifier=tool_identity`；`verification_sha256` 为删除该字段后的 canonical SHA。parent/pair verifier 自行重算所有三 SHA、每个 nested object、current source/staging/run-root bytes，记录值仅作待比对声明。任何 request/result/verification shared replacement 必因 Git/current binding、fixed discovery或独立再算 FAIL。

## 3. 路径、cwd 与 import authority 的 exact grammar

五个 `path_identity` 必须 `(kind, root)` 一一对应：`production_source.identity.kind="git_source"`，`p4_run.identity.kind="run_root"`，`p4_staging.identity.kind="staging_root"`，外部发现 roots 分别为 `git_evidence/git_exporter`。全部 `resolved_root` 两两不同、无祖先/子孙关系、无 inode/realpath alias；唯一例外是 `p4_staging.relative_path=="import_staging/" + p4_run.run_token` 且其 resolved root 是 `p4_run.resolved_root` 的严格后代。

child `cwd` 精确为 `production_source.identity.resolved_root + "/cosmos-framework"`；`toml.path` 是 source root 内 relative non-symlink path，Git blob/current SHA 都必须相同。它可供读取但永不进入 `sys.path`。child import authority 精确为：

```text
[interpreter.stdlib, interpreter.lib_dynload] + p4_staging.runtime_sys_path
```

其中前二者必须 canonical absolute directory、非 symlink、顺序固定；`runtime_sys_path` 必须逐项等于 `p4_staging.identity.resolved_root + "/" + payload_import_roots.relative_root` 的有序映射，每项是 staging root 的严格后代、directory、无重复，且其 subtree manifest SHA 可从 `payload_manifest.entries` 独立重算。不得出现 cwd/source/site-packages/.pth/zip/ambient path。loader 在验证 request SHA、`loader_argv.argv` 与 bootstrap Git/current bytes 前不得导入项目/第三方；随后将 `sys.path` 覆盖为该数组并断言 exact equality。source/staging interchange、relocation、symlink、extra path、或同 bytes ELF 在不同 `$ORIGIN` resolved path 都 FAIL。

## 4. 空环境与 runtime grammar

`p5_effective_environment` 的 exact construction 是 `env={}` 后按 lexical key order加入：两 backend `effective_environment.set` 完全相同的 entries；P3 contract 唯一允许的 backend-specific entries；再加入 `LC_CTYPE:"C.UTF-8"`。`inherit_allowlist` 必为 `[]`；`effective_environment.unset` 和 `native_loader_environment.unset` 必精确为下列有序数组：

```text
["GLIBC_TUNABLES","LD_AUDIT","LD_ASSUME_KERNEL","LD_BIND_NOT","LD_DEBUG","LD_DEBUG_OUTPUT","LD_LIBRARY_PATH","LD_ORIGIN_PATH","LD_PRELOAD","LD_PROFILE","LD_SHOW_AUXV","LD_TRACE_LOADED_OBJECTS","LD_USE_LOAD_BIAS","MASTER_ADDR","MASTER_PORT","PYTHONPATH","RANK","WORLD_SIZE","LOCAL_RANK"]
```

parent 必以此 `env` 完成 native closure resolve 并 `subprocess(..., env=env)` spawn；child 在 first import 前要求 `os.environ` canonical-equal `env`。任何 inherited/unknown key、unset key 出现、locale drift、site/user site/customize、`.pth`、cwd/source/ambient sys.path 均 FAIL。

## 5. immutable post-preflight roster

`pre_p5_run_root_roster.entries` 只允许如下 exact paths：`import_staging`（directory）、`import_staging/<run_token>`（directory）、其 `payload_manifest.entries` 全部 regular files，以及 `preflight.json`（regular readonly file）。每 directory mode 必为 `0555`，每 file mode 必为 `0444`，没有 symlink、hardlink、socket、device 或 FIFO。`preflight.json` 只含 `{request_relpath,request_sha256,result_relpath,result_sha256,verification_relpath,verification_sha256}`，其相对路径精确为第 1 节三文件的 backend 路径。

P5 parent 和 pair verifier 各自 walk `p4_run_root`、计算 `roster.sha256` 并与 result/verification 比对；任何 checkpoint、weight、stdout/stderr/capture、训练/评测/推理 artifact、模型/数据文件、未知项、extra staging、mode/mutation 或 inode alias 均 pre-spawn FAIL。

## 6. 验收与边界

v0.8 仅请求 `APPROVE_TO_IMPLEMENT_P5_V08_STATIC_TOOLS` 或 `REQUEST_CHANGES`。CPU 标准库 tests 必对以上每个 schema/digest/path/cwd/sys.path/env/roster rule建立正反例，且不调用 compose。即使设计/实现获批，P4-v4 record/refreeze/preflight、P5 export/compose、torchrun/GPU、模型数据、训练/评测/推理、P5 closure、B2-T 与 Local Memory 训练仍分别禁止，须独立三方审核与用户授权。
