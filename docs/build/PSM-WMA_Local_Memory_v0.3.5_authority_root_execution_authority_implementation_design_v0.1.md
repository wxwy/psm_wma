# PSM-WMA v0.3.5 Authority-root Execution Authority Implementation 设计 v0.1

**日期**：2026-09-12
**Gate**：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-EXECUTION-AUTHORITY-IMPLEMENTATION-DESIGN`
**状态**：docs-only；待三方审核。
**上游结论**：`d3cd3c9b26cea021814c9f48bcd864183a811293` / `93a89ba61306d840a008813f62f26a34d54850f4` 三方 final 已齐；ChatGPT、Kimi 均 `REQUEST_CHANGES`，MM 批准。

本设计只闭合已批准 source-evidence 链中 real materialization 所必需的执行权威缺口；它不是新增 checkpoint/publication/provenance 子 Gate。依 D024，完成这一 root-tooling CPU/static 收口后直接转入既定 collection/receipt 闭环与 single-GPU TTT smoke 设计，不再横向增加 authority Gate。

## 1. 要解决的精确缺口

现有 `ad9e011...` adapter 只绑定 adapter、authority module 及 remote alias，Evidence-v1 也不能表示 bootstrap、collection/audit identity 或真实 remote endpoint。因而 `d3cd3c9...` 的 prose one-shot request 不可直接执行。实现必须同时满足：

1. 任一项目模块 import 前，由仅用标准库的 bootstrap 验证完整四模块 closure；
2. adapter parser、invocation、Evidence-v1 和 verifier 对 bootstrap 与四模块身份使用同一 exact-key ABI；
3. Git object/ref view 不受 replace、global/system/local ambient config 或 remote alias retarget 影响；
4. 下一份实际 request 可把 bootstrap 字节、完整 argv、FD 协议、输入 bytes/source binding、metadata、sanitized environment、remote endpoint 与所有路径一次性冻结，批准后没有占位值或替换位；
5. 所有新增行为先以 stdlib CPU/static adversarial witness 证明；本 Gate 不运行真实 materialization。

## 2. 允许的最小实现范围

仅允许修改下列两个 root 文件；不得修改 child/Gitlink、Cosmos、训练代码或创建真实 source/candidate/ref/evidence：

```text
tools/psm_wma/materialize_immutable_source_authority_root.py
tools/psm_wma/test_materialize_immutable_source_authority_root.py
```

bootstrap 的 authoritative runtime form 是下一份 actual request 内联的、逐字冻结的 UTF-8 `-c` source；adapter 内只保留同字节的 stdlib fixture builder，供 CPU/static parity test 检查，运行时不得为取得 bootstrap 而 import adapter。不得新增可在 preflight 前 import 的项目模块。bootstrap 的输入只来自冻结 argv、继承 FD 与受控环境；其 source 自身的 raw SHA-256、canonical argv SHA-256、四模块 identities、formal root、clean-root path 与 FD protocol 全部成为 invocation identity 的字段。

## 3. 闭合的 invocation / evidence ABI

`AuthorityAdapterInvocation` 增加 immutable fields：

```text
project_modules = {
  adapter, authority_module, collection_module, audit_module
}
bootstrap_raw_sha256
bootstrap_argv_sha256
bootstrap_protocol_version
remote_endpoint
remote_endpoint_sha256
sanitized_env_sha256
```

`_parser()` 为 collection/audit 增加与现有 module 完全同构的 `path/blob-oid/raw-sha256` 三元组；增加 bootstrap raw SHA、bootstrap argv SHA、protocol version、remote endpoint 与 endpoint SHA。`remote` alias 被删除为执行 authority 输入：所有 `ls-remote` 与 `push` 都只接收同一个 canonical endpoint string。main 在打开 FD 或建立 transaction 前验证所有字段格式、exact endpoint digest 和 argv projection。

Evidence-v1 的 `execution` exact keys 同步增加四模块 identities、bootstrap raw SHA、bootstrap argv SHA、protocol version、remote endpoint SHA 与 Git isolation fingerprint。`_validate_execution()` 必须拒绝缺项、额外项、endpoint/alias 字段混用或任何摘要格式错误。evidence 只记录摘要及公开 endpoint digest，不记录 bootstrap 原文、source raw bytes、FD target、credential、URL query/credential 或 source path。

## 4. Bootstrap 与导入时序

bootstrap source 只使用 `hashlib`、`json`、`os`、`pathlib`、`runpy`、`stat`、`subprocess`、`sys` 等标准库。受控 launcher 以 `python -I -S -B -c` 执行 actual request formal tree 内联并逐字审核的 bootstrap bytes；其 digest 必须同时等于冻结 argv field、adapter evidence field和fixture-builder parity test。它按此顺序 fail-closed：

1. 核验解释器/Git regular non-symlink、raw hash、version，及 clean root `HEAD == formal_root`；
2. 对 adapter、authority、collection、audit 逐一执行 `lstat` regular/non-symlink、raw SHA-256 与 `git --no-replace-objects ls-tree` 的 `100644 blob` 三重比对；
3. 校验 FD number 均为正、不同、inheritable，`fstat` 均为 regular file，且被冻结的 bootstrap argv projection与实际 adapter argv一致；
4. 仅完成前三步后才 `sys.path.insert(0, clean_root)`、`runpy.run_module(...)`；任何失败不得 project import、`hash-object`、`read-tree`、ref mutation 或 evidence write。

bootstrap 不从环境、cwd discovery、shell expansion、remote config 或未审查文件寻找输入。实际 request 必须将 bootstrap raw UTF-8 bytes以 formal-tree blob/path 绑定；若运行时 bootstrap bytes与该 formal binding不一致则在第 1 步前退出。

## 5. Git isolation 与 endpoint 语义

`NativeAuthorityGit` 以最小固定 env 加入：`GIT_NO_REPLACE_OBJECTS=1`、`GIT_CONFIG_NOSYSTEM=1`、`GIT_CONFIG_GLOBAL=/dev/null`、`GIT_CONFIG_SYSTEM=/dev/null`、`GIT_INDEX_FILE`、locale 和唯一冻结 metadata；不得继承其他 `GIT_*`、proxy、credential、HOME 或 config-path 变量。每个 Git invocation 使用 `--no-replace-objects` 并以固定 `-c` 禁用外部 attributes/hooks/filter 语义；本地 repo config 中不允许作为 endpoint 或 object-view authority。

endpoint 必须是无 credential、无 query/fragment、canonical absolute transport endpoint；其 digest由 exact endpoint UTF-8 bytes计算。`ls-remote`、create/delete push 与回读全部使用此 endpoint，Evidence-v1 只保存 endpoint SHA。任何 alias（包括 `origin`）只能是拒绝输入，不能被解析后继续使用。

## 6. CPU/static 直接验收

所有 test 只在临时目录/fixture 与 injected subprocess seam 上运行，不调用真实 remote、真实 commit/ref 或 source。必须覆盖：

1. 四模块 closure 全部正确时 bootstrap 到达受控 `runpy` sentinel；collection 或 audit raw bytes 单独漂移、symlink、shadowing、formal-tree blob mismatch、clean-root HEAD drift 时均在 sentinel 前拒绝，且 project-import、Git mutation/evidence-write counters 都为零；
2. bootstrap bytes/hash、protocol version、argv projection、FD duplicated/not-inheritable/non-regular 与实际 argv 不一致的拒绝；
3. parser/invocation/evidence verifier 对 collection/audit/bootstrap/endpoints 的 exact-key 正负例；任一旧两模块 evidence、额外键或 alias 字段均拒绝；
4. `origin` retarget、credential/query endpoint、endpoint digest mismatch、replace-ref、global/system/local config injection、attributes/filter/hooks injection 均在 first authority Git action 前 fail-stop；
5. 正例仍保持既有 candidate/pass/rollback CPU/static 行为，扩展后的 evidence 可自验；完整既有 unittest、Ruff、py_compile 与 `git diff --check` PASS。

## 7. 下一份实际 one-shot request 的冻结清单

本设计实现并获批准后，才可新建一个直接 executable request。其 formal tree 必须逐字给出：bootstrap bytes与SHA、完整 `python -I -S -B -c` argv canonical JSON与SHA、FD numbers/open/inheritance/close protocol、selection/config exact raw bytes或formal blob binding、author/committer七字段、sanitized env canonical bytes与SHA、canonical remote endpoint与SHA、clean-root/input/index/evidence绝对路径、所有 Git cleanup command semantics、四模块 formal blob/raw identities，以及每一失败的停止/ownership rollback语义。任何“执行前补入”“占位符”“从当前环境读取”都使 request 无效。

## 8. 请求 verdict 与禁止范围

请求唯一 verdict：

```text
APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_AUTHORITY_ROOT_EXECUTION_AUTHORITY_CPU_STATIC
```

或 `REQUEST_CHANGES(file:line)`。三方同一 formal root/child 全批准前，不得改动上述两文件，不得创建或写入 JSON、candidate、ref、evidence、worktree、source，且不得触碰 child、GPU、训练、评测、推理或 LIBERO4IN1。
