# PSM-WMA v0.3.5 Source-evidence Producer / Closure 设计 v0.1

**日期**：2026-09-12  
**状态**：docs-only；待三方审核。  
**Gate**：`G0-R09-B-TTT-V035-SOURCE-EVIDENCE-PRODUCER-CLOSURE-DESIGN`

## 1. 目的与边界

本 Gate 只冻结 future root-owned source-evidence record、publication input package 和外部 witness 的 producer/closure 合同。它是
`PSM-WMA_Local_Memory_v0.3.5_root_publication_freeze_design_v0.1.md` §2--§5 的唯一前置 Gate，复用但不改写其 nested schemas、唯一 publication path 和 transaction 规则。

本 Gate 不创建 record/package/witness，不选择或读取真实 checkpoint、manifest、data 或 cache，不修改 child/runtime，不运行 source audit、DCP、CUDA/GPU、torchrun、forward/loss/backward、optimizer/scheduler step、训练、评测、推理或 LIBERO4IN1。

## 2. 固定对象与唯一来源

future closure 只能在一个已批准的 source-evidence root commit tree 内写入下列唯一 record path：

```text
docs/build/PSM-WMA_root_checkpoint_source_evidence_record_v1.json
```

该 path 的 raw blob bytes 必须为 canonical JSON，且 object key set exact 为：

```text
schema,
source_kind,
immutable_source_identifier,
source_manifest_sha256,
source_input_sha256,
checkpoint_source_descriptor_sha256
```

`schema="root_checkpoint_source_evidence_record_v1"`，`source_kind="checkpoint_source_manifest_v1"`；其余四项均为 64 位 lowercase hex string。`source_evidence_record_sha256` 只定义为该 raw canonical bytes 的 SHA-256。未知/缺失 key、重复语义、非 string、upper-case hex、路径、URL、mutable ref、时间戳、环境变量、caller label、bool 或非 canonical bytes 均为 FAIL。

record 的四项 digest 必须由独立、已批准的 immutable source-evidence collection Gate 的 formal output 导出；producer 不得从 current working tree、child、环境、caller 参数或 publication payload 补值、选择或替换来源。该 collection Gate 的 formal root revision 与 record blob 均须能从 future closure 的 formal root tree lookup 重新得到。

## 3. package 与 witness 的闭合关系

record 成功固定后，closure 才可从同一 formal root tree 的 fixed record blob 和已冻结 `canonical_model_config` / `checkpoint_source_descriptor` 构造 exact 七键 canonical package：

```text
schema,
canonical_model_config,
checkpoint_source_descriptor,
source_evidence_root_revision,
source_evidence_record_path,
source_evidence_record_sha256,
source_evidence_record_schema
```

值必须分别为 `root_publication_input_package_v1`、该 closure formal root 的 reachable lowercase Git SHA-1、固定 path、record raw-bytes SHA-256 和 `root_checkpoint_source_evidence_record_v1`。nested object 完整继承 source-audit design v0.3 §4--§5；package 内 descriptor canonical digest 必须等于 record 的 `checkpoint_source_descriptor_sha256`。

同一 package 必须生成 exact 七键 external witness：

```text
schema,
input_package_sha256,
canonical_model_config_sha256,
checkpoint_source_descriptor_sha256,
source_evidence_root_revision,
source_evidence_record_sha256,
source_evidence_record_schema
```

`schema="root_publication_input_witness_v1"`；三个 digest 必须逐字等于各 canonical bytes 的 SHA-256，revision/schema 必须与 package 一致。witness raw bytes SHA-256 和 Git blob OID 必须由 closure formal root 外部记录；不得写入 record、package 或 future publication payload，避免 self-reference。

## 4. future controlled closure transaction

获独立 `APPROVE_TO_WRITE_SOURCE_EVIDENCE` 后，producer 必须先在 isolated temporary file/index/tree 中验证 immutable collection binding、schemas、canonical bytes、record/path、package/witness relationships 和 candidate index blob byte equality；任一 preflight FAIL 时 live target/index/HEAD/authority 逐 byte/entry 不变。

仅 preflight 全通过才能开始 live transaction：snapshot target 与 index entries，atomic replace fixed record path，stage record，重读 index blob 并逐 byte 验证，创建 root commit；该 commit 的 staged allowlist 仅可含 fixed record path 与该 execution Gate 明示的 verifier/evidence files，绝不含 `cosmos-framework` Gitlink、publication path、checkpoint/cache、训练产物或 Inbox rollover。每一 live failure 必须以 snapshot rollback target/index 并验证恢复；rollback 或 HEAD-state verification 不完整/不确定时返回 `ROLLBACK_INCOMPLETE` fail-stop，保留最小失败证据、禁止 authority/audit/runtime/自动重试，且不得声称零 mutation。

提交成功后，只允许由该 new formal root tree 重新读取 fixed record，外部生成 package/witness binding，并申请下一 Gate；不得以 parent、working tree 或预提交 bytes 作为 authority。

## 5. 验收、序列与 verdict

本设计只验收 record 的唯一来源与 schema、package/witness 的非循环 canonical binding、两阶段失败语义及 staged-set/Gitlink 禁令。后续顺序固定为：

```text
三方 APPROVE_TO_DESIGN
  -> 独立 source-evidence controlled-write execution design
  -> 三方 APPROVE_TO_WRITE_SOURCE_EVIDENCE
  -> 一次受控 record closure
  -> docs-only publication materializer/verifier implementation design
```

本 Gate 批准不授权真实 collection、record 写入、publication、read-only audit、child 修改、真实 I/O、GPU 或训练。

请求唯一 verdict：

```text
APPROVE_TO_DESIGN_R09_B_TTT_V035_SOURCE_EVIDENCE_PRODUCER_CLOSURE
```

或 `REQUEST_CHANGES(file:line)`。
