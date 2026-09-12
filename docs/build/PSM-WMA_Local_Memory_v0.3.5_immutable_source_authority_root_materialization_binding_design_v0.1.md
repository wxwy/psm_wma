# PSM-WMA v0.3.5 Immutable Source Authority Root Materialization/Binding 设计 v0.1

**日期**：2026-09-12  
**状态**：docs-only；待三方审核。  
**Gate**：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-BINDING-DESIGN`

## 1. 目的、继承与边界

本 Gate 只冻结已批准 controlled-execution v0.2 §3 所要求的 execution-authority root 的构造、独立核验与三方 binding。它严格位于已关闭的 root CPU/static executor 之后、任何真实 source entry 打开之前；属于既有 collection/source-evidence 闭环，不新增横向 provenance Gate。

本设计不创建 authority root 或两个 JSON，不选择、resolve、打开、读取、复制或 hash 真实 source；不触碰 collection/receipt/source-evidence/publication；不修改 child/runtime；不运行 checkpoint/data/cache I/O、网络、CUDA/GPU、`torchrun`、forward/loss/backward、optimizer/scheduler/scaler step、训练、评测、推理或 LIBERO4IN1。

## 2. 输入 authority 与 canonical bytes

materializer 只接受显式、经本 Gate 后续 materialization request 审核的两个 raw-byte inputs；环境变量、stdin、working-tree discovery、caller mapping、已有 digest、mutable ref 和默认配置都不是 authority：

1. selection raw bytes：exact canonical `immutable_source_selection_request_v1`，outer key set=`schema,source_kind,entries`，`source_kind="checkpoint_source_manifest_v1"`；`entries` nonempty，每项 exact `ordinal,relative_path`，ordinal 从 0 连续递增，relative path 为 UTF-8 bytewise 严格排序的 POSIX relative normal path，禁止绝对路径、空值、`.`/`..`、NUL、重复或 symlink 语义。它仅批准 future source traversal，不能证明任何 source 当前存在或其 bytes。
2. config raw bytes：exact resolved 15-key `canonical_native_local_ttt_config_v2`，逐字段继承 canonical-native root Gitlink source-audit design v0.3 §4；不得含 default/unresolved placeholder、运行时观察值、路径、checkpoint revision、训练产物或 authority root 自身 identity。

两项均须为 UTF-8 canonical JSON：递归 key sort、`separators=(',', ':')`、`ensure_ascii=false`、`allow_nan=false`，且 parse 后重新 canonicalize 必须逐 byte 等于输入。materializer 在 Git mutation 前计算 raw SHA-256 与 native Git blob OID；这些值只作 observation，不能替代 raw bytes。任一 unknown/missing key、类型、ordinal/order/path、canonical-byte 或 schema drift 均在 commit creation 前 FAIL，并保持所有 refs、index、worktree 与 object publication state 不变。

## 3. 非循环 authority commit 与固定 tree delta

authority root 必须由受控 temporary index/`git commit-tree` 等价 plumbing 从已审核的 **materialization formal root** 构造；不得从当前 `HEAD`、ambient index/worktree 或 post-review ledger head 推导 parent。其唯一 parent 精确等于该 formal root，完整 tree 相对 parent 的 changed-path set 必须恰为：

```text
docs/build/PSM-WMA_immutable_source_selection_request_v1.json
docs/build/PSM-WMA_immutable_source_canonical_model_config_v1.json
```

两个 entry 必须分别为 `100644 blob <native OID>`；除这两项外，parent tree 的每个 path、mode、type、OID（包括 `cosmos-framework` Gitlink）必须完整保留。若 parent 已含任一路径、存在额外 delta、mode/type drift、merge parent、非 canonical commit metadata policy、或 materialized blob 与批准 raw bytes不一致，则 FAIL。两个 JSON 禁止包含 authority revision/tree/blob OID、review/receipt、source raw bytes或其绝对/相对路径之外的调用方元数据，从而避免自引用。

materialization commit 不直接推进 `V2`，也不把随后产生的 review/ledger commit 当作 parent；它先作为未发布候选 object 由 verifier 读取。唯一允许的 publication ref 固定为 `refs/heads/authority/r09-b-ttt-v035-immutable-source-v1`。只有 verifier PASS 后，才可在后续 materialization execution approval 下以 expected-zero compare-and-swap 创建该 ref；它必须事前在 local/remote 都不存在，不允许覆盖、force、delete/recreate 或改名。CAS 失败、同名 ref 已存在、任何非该 ref 的 remote side effect、或无法证明 candidate/ref object相同均 fail-stop，不自动重建或改用新的 parent。

## 4. 独立 verifier 与七字段 binding

verifier 不接受 materializer 自报 tuple。它从候选 authority revision 及其 parent/tree/blob lookup 独立重算：单 parent、exact two-path full-entry delta、两个 `100644/blob` entry、raw bytes、canonical schema、native OID 与 raw SHA-256；并核对 formal root 的 child Gitlink 精确等于本 Gate 审核时绑定的 child/Gitlink。materializer 与 verifier 必须是同一后续审核 allowlist 内的 root 标准库工具；其 path/Git blob/raw SHA、解释器 executable path/raw SHA/`--version`、sanitized environment、工作目录和完整 argv 由下一 execution request 显式冻结，不能取 caller/PATH/default。

唯一可交给 collection executor 的 authority 是三方 review 对 exact root/child 明示批准的七字段 tuple：

```text
(authority_root_revision,
 selection_path,
 selection_blob_native_oid,
 selection_raw_sha256,
 config_path,
 config_blob_native_oid,
 config_raw_sha256)
```

review 必须同时引用 materialization formal root、child/Gitlink、authority candidate revision、固定 ref `refs/heads/authority/r09-b-ttt-v035-immutable-source-v1` 的 exact CAS result、两工具 identity、解释器 identity和 verifier PASS evidence。tuple 内 revision/OID 为 40 位 lowercase Git SHA-1，raw digest 为 64 位 lowercase SHA-256，path 必须逐字等于固定两路径。review/ledger/evidence commit 均不能替代 authority root 或七字段 tuple。collection executor 在 source open 前必须从 Git object database 再次重算全部字段与 parent/delta，并以 `git ls-remote` 核对固定 ref 仍精确指向该 authority revision；任一 drift 即 FAIL。

## 5. 事务证据、判据与后续路线

后续 CPU/static implementation 先使用 temporary Git object database 证明：canonical PASS、unknown/missing/type/order/path拒绝、parent/merge-parent/额外 delta/继承 mode-type-OID/Gitlink漂移、固定 entry mode/type/blob/raw drift、self-reference、ambient HEAD/index/worktree无关性、专用 ref CAS 冲突、verifier 不信任自报 tuple。fixture 不得引用真实 source、checkpoint、cache 或项目 live refs。

真实 materialization execution 必须另获三方批准，执行前向用户展示完整命令、cwd、环境、输入 raw-byte文件、candidate/ref/evidence路径和 PASS/FAIL/rollback 判据。PASS 只证明 authority root 与七字段 tuple已生成并获 review；不授权 source read、collection/receipt mutation或后续 publication。FAIL 保留最小、不含 source paths/raw bytes/secrets的诊断；若发生 ref mutation而无法证明 exact rollback，返回 `ROLLBACK_INCOMPLETE` 并停止。

本设计若获批准，只允许下一步 root-only materializer/verifier CPU/static implementation design；待其实现与三方 closure 后，才申请一次真实 authority-root materialization/binding execution。authority tuple获三方批准后进入既有 controlled collection execution approval；source-evidence/publication闭环完成后，下一设计固定为 `G0-R09-B-TTT-V035-SINGLE-GPU-SMOKE-DESIGN`，不得插入新的横向 provenance Gate。

请求唯一 verdict：

```text
APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_MATERIALIZATION_BINDING_CPU_STATIC
```

或 `REQUEST_CHANGES(file:line)`。本申请不请求真实 materialization、source I/O、collection/receipt/source-evidence/publication、child、GPU或训练授权。
