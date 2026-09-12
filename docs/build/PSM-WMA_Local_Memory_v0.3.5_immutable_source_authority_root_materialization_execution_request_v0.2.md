# PSM-WMA Authority Root One-shot Materialization Execution Request v0.2

**日期**：2026-09-12  
**Gate**：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`  
**状态**：docs-only replacement request；待独立三方执行批准。

## 1. 目的与替代关系

本文件替代
`PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_materialization_execution_request_v0.1.md`。
v0.1 绑定的 adapter formal parent 为 `ad9e011...`，不包含已关闭的 linked-worktree routing-authority
保护；它不得用于任何执行。仅 v0.1 的单次事务、证据、PASS/FAIL、rollback 和禁止范围继续生效。
v0.1 的运行时路径、工具 identity、remote、环境、metadata、input、bootstrap 与 argv 声明均不再是
authority；它们只可由 §4 annex 的单一冻结值替代。

本文件仍只请求一次 authority-root materialization：两个 canonical JSON、一个 detached candidate、
fixed ref 的 expected-zero local/remote CAS 与一个 canonical materialization evidence。它不打开
checkpoint source，不进入 collection/receipt/controlled write/publication/root audit，不修改 child，
不使用 GPU 或启动训练。

## 2. 唯一有效 formal authority

| 项目 | v0.2 固定值 |
| --- | --- |
| materialization formal parent | `9dd2fb8b63ccd6a3193eec7ab6584cc24a68a4a5` |
| required child/Gitlink | `93a89ba61306d840a008813f62f26a34d54850f4` |
| fixed ref | `refs/heads/authority/r09-b-ttt-v035-immutable-source-v1`；local/remote 均必须 expected-zero |
| adapter path/blob/raw SHA-256 | `tools/psm_wma/materialize_immutable_source_authority_root.py` / `da782754b8e8efa0f3cae973aa68602dcda1c237` / `091ea62d0a8b48429c67100c1395e62a300dc47a8d8f65c7046ba00f8205b5e9` |
| authority path/blob/raw SHA-256 | `tools/psm_wma/immutable_source_authority_root.py` / `9937f74c49b14d489823c731aa2856b00c1a3d06` / `4ebf9fb8b0605bc30c45800bdfa7d367444ff97daee69926eba9aa5c9817f5d0` |
| collection path/blob/raw SHA-256 | `tools/psm_wma/immutable_source_collection.py` / `eefde4e5b5a0965bbdcaa5390b9286a4c77f2665` / `1b3353b0bd1342f1685062f962a7cbc1ba0dbf699bdc72c099ca470cb09cc340` |
| audit path/blob/raw SHA-256 | `tools/g0/audit_r09_b_ttt_root_gitlink_authority.py` / `d0020f067badfe591152fafa6336e20b485eb5ba` / `3db6376b35141d8ca5dc72c1bb38359943961db92545a88f320603121db4c39e` |

candidate 的唯一 parent 必须是本节 formal parent；review、ledger、request 文档或随后提交绝不是
candidate parent。bootstrap 仍在任何 project import 前，对上表四模块执行 regular/non-symlink、
raw SHA-256、formal-tree `100644 blob <oid>` 三重验证。

## 3. routing-authority 追加硬合同

执行只可使用上表 adapter 的 `python -I -S -B -c` frozen stdlib bootstrap。除 v0.1 所列
interpreter/Git/module/input 检查外，bootstrap 每次 native Git observation 前后必须同时重验：

1. primary worktree 的 `.git` directory，或 linked worktree 的 `.git` marker、`gitdir`、
   `commondir` 的 no-follow FD identity/raw bytes；
2. linked `git_dir` 与 common Git directory 的 no-follow directory identity；
3. actual `<git_dir>/config.worktree` 的持续 absence；
4. common `config` 的 pathname identity 与 retained-FD raw bytes。

任一 drift 必须在 project import、callback、candidate/ref/evidence mutation 前 fail closed。不得以
v0.1 的旧 adapter、旧 module hash 或“review 已通过”绕开上述核验。

## 4. 执行前 snapshot annex（不可省略）

三方对本文件的批准只允许由构建者创建一次**只读** snapshot annex。annex 是其枚举的每一个运行时
字段的唯一 authority，必须冻结并展示：fresh absolute clean-worktree/index/evidence 与`.pending`路径、
Python/Git absolute path/raw-SHA/version、canonical sanitized environment raw bytes/digest、exact
credential-free canonical HTTPS endpoint string及其SHA-256、commit metadata、exact selection/config
canonical bytes/raw SHA/native blob OID、bootstrap raw bytes/SHA、complete argv canonical bytes/SHA，以及
当前parser/launcher ABI 所需的所有 FD/open/inheritance 语义。remote alias（包括`origin`）不可替代
endpoint string。annex 必须引用本节 formal parent，不能替换 §2 formal parent/Gitlink/fixed ref/
four-module identity 或 §3 routing-authority contract；annex 批准后其中任何值不得改变。annex 本身和
完整执行命令必须再获同一三方
`APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT` 后才能执行。

在此之前，不创建 JSON、clean worktree、temporary index、candidate、ref、evidence 或 source handle；
不调用 collection/receipt/publication、child、GPU、训练、评测、推理或 LIBERO4IN1。

## 5. verdict

本文件请求唯一 verdict：

```text
APPROVE_TO_PREPARE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_EXECUTION_SNAPSHOT
```

或 `REQUEST_CHANGES(file:line)`。批准范围仅为 §4 的只读 snapshot annex；不授权 materialization。
