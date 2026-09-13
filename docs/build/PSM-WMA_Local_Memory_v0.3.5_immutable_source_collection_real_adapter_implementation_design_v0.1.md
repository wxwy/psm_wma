# PSM-WMA v0.3.5 Immutable Source Collection Real Adapter 实现设计 v0.1

**日期**：2026-09-13
**状态**：docs-only；待三方审核。
**Gate**：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-REAL-ADAPTER-IMPLEMENTATION-DESIGN`

## 1. 缺口与范围

已关闭的 collection CPU/static Gate 只实现了
`tools/psm_wma/immutable_source_collection.py::collect_synthetic` 及 injected
`GitTransaction`、`RootFdOpener`、`EvidenceSink` seams。它没有 production CLI、native Git
transaction、FD-root opener 或 controlled evidence sink；因此它不能形成 v0.2 closure request 所需的
exact non-shell argv，也不能被误称为可执行 executor。

本 Gate 只为已冻结的 collection executor seam 补齐一个 root-owned real adapter 的实现设计；它不是新的
source identity、checkpoint authority 或 publication provenance Gate。其完成后仍必须经过独立 CPU/static
implementation closure，才可重新构造并审核闭环 execution request。

本 Gate 不创建/打开真实 source、checkpoint、manifest、data 或 cache；不创建 authority/collection/receipt/
record/package/publication；不修改 child/runtime/config；不执行 GPU/CUDA/torchrun、训练、评测、推理或
LIBERO4IN1。

## 2. 最小 allowlist 与复用边界

后续 implementation 仅允许新增以下 root 文件：

```text
tools/psm_wma/execute_immutable_source_collection.py
tools/psm_wma/test_execute_immutable_source_collection.py
```

它必须复用而不得复制或改变 `immutable_source_collection.py` 的 canonical validation、candidate construction、
one-shot handoff、receipt 及 rollback semantics。adapter 只实现它已有的三个 injected protocol：

1. `NativeCollectionGit`：以绝对、身份绑定的 Git executable，`shell=False`、sanitized environment、
   temporary index 与显式 argv 实现 `GitTransaction`；不得从 ambient `HEAD`、index、worktree 或 `PATH`
   推导 authority。
2. `FdRootOpener`：只从已冻结 directory FD 经 `openat`/`O_NOFOLLOW` 打开 selection 所列的 normal relative
   regular file；每次 read 前后验证 descriptor、regular-file 类型与 identity，拒绝 symlink、escape、目录和
   race。
3. `AtomicCollectionEvidenceSink`：只向 future request 冻结的 fresh destination 写入 canonical evidence；
   失败时不留下可见 partial record，且永不记录 raw source bytes、absolute source path、URL、secret 或
   credential。

adapter 不得引入 shell、glob、stdin/caller mapping、环境默认值、网络配置、代理、credential 或新的 source
selection grammar。selection/config 仍只能由已审核 authority-root 的 exact blob 通过 regular non-symlink FD
transport；source root 只能是 future request 明示并由 directory FD 身份绑定的 transport capability，不能写入
authority blob 或 evidence。

## 3. Future CLI 与 fail-closed admission

future CLI 必须采用 import-free stdlib bootstrap，唯一形态为：

```text
<interpreter> -I -S -B -c <frozen-stdlib-bootstrap> -- <adapter argv>
```

完整 argv 在将来的 execution request 才冻结；本 Gate 只冻结其 required categories：formal root/child Gitlink、
approved authority seven-tuple、target ref/base/lineage, selection/config FD 与 raw SHA-256、source-root directory
FD、Git/interpreter/module identities、temporary index、evidence destination、sanitized environment digest、commit
metadata、以及 source-evidence closure 的 transaction/rollback policy。任何类别缺失、FD 非 regular/directory、
formal-tree identity drift、authority tuple drift、target/base/Gitlink drift、local/remote ref drift、evidence path
非 fresh 或 bootstrap/import drift 均必须在任何 source entry open 或 Git mutation 前以
`BLOCKED_AUTHORITY_NOT_CLOSED` 或 `FAIL` 终止。

adapter 只可在 preflight 完整通过后，将 `collect_synthetic` 的现有 algorithm 与 native protocol 实例连接一次。
source entry handoff 保持同进程、不可序列化、不可重放；任何 source read 后的错误均按既有 snapshot/ownership
rollback 语义处理，无法逐项证明 rollback 时唯一终态为 `ROLLBACK_INCOMPLETE`。

## 4. CPU/static 验收

实现及测试只使用 `TemporaryDirectory`、synthetic byte fixtures 与 local/bare temporary Git remote。至少验证：

- exact non-shell argv、sanitized env、module/Git/interpreter identity 与 bootstrap allowlist；
- authority parent/path/blob/raw-SHA、target/base/Gitlink、local/remote CAS 与 fresh evidence drift 的 pre-mutation
  rejection；
- directory-FD normal-path/regular-file/no-follow discipline、same-FD double hash/fstat race、single-use handoff；
- collection/receipt transaction、source-evidence input handoff、atomic evidence failure、rollback 与
  `ROLLBACK_INCOMPLETE`；
- no project root, real source/checkpoint/cache, origin remote, GPU or child worktree access.

`python -m unittest`、`py_compile` 与 `git diff --check` 必须 PASS。测试通过不构成真实 collection、request
execution、GPU 或训练授权。

## 5. 后续顺序

三方对本 Gate 同 pair 批准后，仅允许上述两文件的 temporary CPU/static implementation 与复核。该 closure 完成后，
才可在已批准 source-evidence v0.2 规则下构造一份 exact closure execution request instance 并重新三方审核；
request 执行仍须独立批准，并且其生成的独立 receipt root 仍须单独三方审核。

请求最终 verdict：

```text
APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_REAL_ADAPTER_CPU_STATIC
```

或 `REQUEST_CHANGES(file:line)`。
