# PSM-WMA v0.3.5 Root Publication Freeze 设计 v0.1

**日期**：2026-09-12
**状态**：docs-only；待三方审核。
**Gate**：`G0-R09-B-TTT-V035-ROOT-PUBLICATION-FREEZE-DESIGN`

## 1. 目的与严格边界

本 Gate 只冻结未来将 root-owned authority publication 写入 Git 前的输入、提交边界和 fail-closed 验证顺序。唯一 future publication 路径仍是：

```text
docs/build/PSM-WMA_root_gitlink_authority_publication_v1.json
```

本文件复用并不改写
`PSM-WMA_Local_Memory_v0.3.5_canonical_native_root_gitlink_authority_source_audit_design_v0.3.md`
第 3--6 节的 publication schema、canonical JSON、tree/blob 与 authority 语义。

本 Gate 不创建 publication，不修改 child 或 root runtime，不读取 checkpoint、模型、数据或 cache，不运行 source audit、DCP、CUDA/GPU、torchrun、forward/loss/backward、optimizer/scheduler step、训练、评测、推理或 LIBERO4IN1。

## 2. 必须先冻结的 publication 输入

未来 materialization Gate 开始前，必须由独立、已批准的 source-evidence closure 在 root tree 内固定下列 exact source-evidence record；其唯一 future path 为 `docs/build/PSM-WMA_root_checkpoint_source_evidence_record_v1.json`，不是 publication target：

```text
schema,
source_kind,
immutable_source_identifier,
source_manifest_sha256,
source_input_sha256,
checkpoint_source_descriptor_sha256
```

`schema` 必须为 `root_checkpoint_source_evidence_record_v1`，`source_kind` 必须为 `checkpoint_source_manifest_v1`；其余四项均为 64 位 lowercase hex。该 record 的 canonical bytes SHA-256 是 `source_evidence_record_sha256`。该 source-evidence producer/closure Gate 必须在任何 real materialization execution Gate **之前**关闭；本 Gate 不授权创建、读取或选择该 record。

仅当 source-evidence root revision、该 fixed-path blob 与其 raw bytes 已由上述 closure 固定时，才可从它构造 exact 七键 canonical **publication input package**：

```text
schema,
canonical_model_config,
checkpoint_source_descriptor,
source_evidence_root_revision,
source_evidence_record_path,
source_evidence_record_sha256,
source_evidence_record_schema
```

其中 `schema="root_publication_input_package_v1"`，`source_evidence_root_revision` 是 40 位 lowercase reachable Git SHA-1，`source_evidence_record_path` exact 为上述固定 path，`source_evidence_record_schema` exact 为 `root_checkpoint_source_evidence_record_v1`。package 的 `checkpoint_source_descriptor` canonical SHA-256 必须等于 record 的 `checkpoint_source_descriptor_sha256`。输入包本身不是 publication，也不得写入 publication target path。

每个 package 必须有一个外部、exact 七键 canonical **publication input witness**：

```text
schema,
input_package_sha256,
canonical_model_config_sha256,
checkpoint_source_descriptor_sha256,
source_evidence_root_revision,
source_evidence_record_sha256,
source_evidence_record_schema
```

其中 `schema="root_publication_input_witness_v1"`；三个 `*_sha256` 是 64 位 lowercase hex；revision/schema 必须与 package 相同。witness 的 raw canonical bytes SHA-256 与其 Git blob OID 由 source-evidence closure 的 formal root 外部记录。future materialization execution design 必须把该 formal source-evidence root、fixed record path、input-package bytes digest 与 witness bytes digest 逐字冻结；production materializer/verifier 不得接收 caller supplied witness、source-evidence root、path、environment 或 working-tree selection。纯 CPU/static 函数可仅在 temporary fixture 中接受显式 object，以证明 schema/relationship 拒绝行为，不能构成 production authority。

```text
canonical_model_config
checkpoint_source_descriptor
```

两 object 的 exact key/type/value 规则完全继承 source-audit design v0.3 §4--§5。特别是：

- `canonical_model_config` 必须是 exact 15-key
  `canonical_native_local_ttt_config_v2`；resolved `ttt_tbptt_steps`、`ttt_inner_lr` 与 `k_local`
  必须是实际将被训练配置消费的值，不能在 publication 时猜测、补默认值或从环境读取。
- `checkpoint_source_descriptor` 必须是 exact 5-key
  `root_gitlink_checkpoint_source_descriptor_v1`；三个 identifier/digest 都必须来自已批准的 immutable source evidence，不能填路径、URL、分支名、时间戳、环境变量或人工标签。
- future materializer 必须对两 object 分别重新 canonicalize、计算 SHA-256，并要求其结果与输入包预声明的独立 witness 一致；任何 unknown、重复语义、非有限值、bool masquerading、key/type/value/digest drift 均 FAIL。

这样 publication 写入时不会把“当前工作树可见内容”或 caller 自选的 self-consistent package/witness 误当作 checkpoint provenance。

## 3. future materialization 的单次提交合同

获独立批准后，materializer 只可在一个新的 root commit 中新增或替换上述唯一 publication path。该提交的暂存区必须满足：

1. `git diff --cached --name-only` 只包含 publication path，或包含该 Gate 明确列出的同次 verifier/测试/运行记录文件；不得夹带 `cosmos-framework` Gitlink、训练产物、cache、checkpoint、Inbox rollover 或无关文档。
2. 写入前可从 index 观察 Gitlink，仅作为 non-authoritative mutation guard：`cosmos-framework` 的 staged entry 必须与 transaction 开始前 index entry逐 byte相同，且 staged-file allowlist 不得包含该 path。不得把 child revision 写入任何 audit invocation input。post-commit read-only audit 只能接收新 formal root revision，并从该 formal root tree 自行导出 Gitlink；child Git directory 只可作 Git object transport。publication payload 仍不得声明 child SHA、root SHA、tree/blob OID 或任何 self-derived digest。
3. target path 的父目录必须已存在且为 root-tracked normal directory；拒绝 symlink、相对路径、路径别名、工作树外路径和 caller 选择的替代输出路径。
4. 所有 package/witness/schema/path/staged-set/blob-byte 验证必须先在 isolated temporary file 与 isolated temporary Git index/tree 中完成。bytes 必须由唯一 canonical JSON encoder 一次性产生，严格 UTF-8、递归 key sort、`separators=(',', ':')`、`ensure_ascii=false`、`allow_nan=false`；isolated index blob 必须逐 byte 等于候选 bytes，不能只比较 Python object。
5. 提交完成后才允许以该新 formal root revision 为输入申请 future read-only source audit；不得用 parent、working-tree HEAD 或预提交 blob SHA 代替 formal root tree lookup。

preflight 失败必须不创建或替换 live target，不变更 live index/HEAD，不生成 authority。只有 isolated preflight 全通过后才能进入 live transaction：先 snapshot live target type/mode/raw bytes 与 target/Gitlink index entries，再 atomic replace target、stage target、重读 live index blob逐 byte校验，最后创建 root commit。live transaction 中 write/stage/index-blob/commit 任一步失败，必须以 snapshots rollback target 与 index，并逐 byte/entry复核；rollback 失败或 HEAD 语义不确定时必须 `ROLLBACK_INCOMPLETE` fail-stop、禁止 authority/audit/runtime，不能宣称零 mutation 或自动重试。失败日志不得包含 checkpoint bytes、数据、密钥或环境变量内容。

## 4. future CPU/static implementation 的最小范围

下一份 implementation-design 可以且只能授权 root-owned、stdlib-only temporary-fixture tooling：

- `build_publication_bytes(input_package, input_witness)`：只在 temporary fixture 中接受这两个 explicit object，严格拒绝 package/witness/record relationship drift，返回 canonical publication bytes 和两项 nested digest；无文件、Git、child、checkpoint 或环境读取。
- `verify_publication_bytes(raw_bytes, input_package, input_witness)`：严格 parse/canonical round-trip、exact three-key outer schema、nested schema、七键 package/witness 与 source-evidence binding；production wrapper 不得将这些对象作为 caller supplied authority。
- temporary Git fixture tests：证明 fixed source-evidence path/record/package/witness schemas、only-target staged-file contract、path/symlink/alias 拒绝、isolated index blob byte equality、preflight 零 live mutation及 live transaction rollback；root/child SHA 与 audit bindings 必须留给 materialization/audit Gate。

该 implementation 不得创建真实 target path，不得对真实 root 或 child 调用 audit，也不得读取任何真实 checkpoint/data/cache。测试输入只可为临时目录中人工构造的非真实字符串与 bytes。

## 5. 逐级 Gate 序列

```text
本 docs-only freeze design
  -> 三方 APPROVE_TO_DESIGN
  -> 独立 source-evidence producer / closure Gate（冻结 record、package 与 witness）
  -> docs-only publication materializer/verifier implementation design
  -> 三方 APPROVE_TO_IMPLEMENT
  -> root CPU/static temporary-fixture implementation + closure review
  -> 独立真实 publication materialization execution design
  -> 三方 APPROVE_TO_WRITE_PUBLICATION
  -> 一次受控 root publication 写入/提交
  -> 独立 read-only root Gitlink source audit Gate
  -> 后续 runtime / real-I/O preflight / GPU / training Gates
```

任何后续 Gate 都不得由本 Gate 的批准自动获得。尤其是 publication 写入成功不是 checkpoint restore、LIBERO4IN1 cache 使用、GPU 或训练授权。

## 6. 本 Gate 的验收与 verdict

本 Gate 只验收本设计是否：

1. 没有实际 publication 或真实 source I/O；
2. 唯一 target path、nested schema 来源及 self-reference 禁令明确；
3. 将输入来源证明、bytes、index、formal root 和 audit 分成不可替代的阶段；
4. 对失败采用 §3 的两阶段合同：live transaction 前任一失败必须令 target、index、HEAD 与 authority 逐 byte/entry 不变；live mutation 开始后任一失败必须按 snapshot rollback target/index 并逐 byte/entry 核验恢复后才返回普通失败；rollback 或 HEAD-state verification 不完整/不确定时必须返回 `ROLLBACK_INCOMPLETE`、保留证据、禁止 authority/audit/runtime 推进和自动重试，且不得声称零 mutation；任何失败均不得产生已接受的 publication authority 或进入 read-only source audit；
5. 没有放宽任何 v0.3 source-audit contract。

请求唯一 verdict：

```text
APPROVE_TO_DESIGN_R09_B_TTT_V035_ROOT_PUBLICATION_FREEZE
```

或 `REQUEST_CHANGES(file:line)`。本文件不授权 publication 写入、真实 audit、child 修改、真实 I/O、GPU 或训练。
