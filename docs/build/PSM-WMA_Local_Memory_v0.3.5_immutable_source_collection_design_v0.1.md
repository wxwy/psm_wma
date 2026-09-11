# PSM-WMA v0.3.5 Immutable Source Collection 收口设计 v0.1

**日期**：2026-09-12
**状态**：docs-only；待三方审核。
**Gate**：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-DESIGN`

## 1. 目的、最小化范围与路线终点

本 Gate 是 source-evidence 链中唯一的 immutable collection design：只冻结 future immutable-source collection 的证据合同，以及由其直接闭合的独立 receipt。它复用且不得改写
`PSM-WMA_Local_Memory_v0.3.5_source_evidence_producer_closure_design_v0.1.md` §2--§5、
`PSM-WMA_Local_Memory_v0.3.5_canonical_native_root_gitlink_authority_source_audit_design_v0.3.md` §4--§5 的 canonical JSON 与 nested schema。

本 Gate 不删除已批准 source-evidence producer/closure 与 Root Publication Freeze 的既有顺序：collection design/execution/closure、source-evidence controlled-write execution、`APPROVE_TO_WRITE_SOURCE_EVIDENCE`、record closure、独立 post-commit receipt closure/review、publication materializer/verifier、read-only root audit 仍逐项生效。用户的 GPU 优先级仅约束为：上述已批准闭环完成后，不得再为 checkpoint authority、publication evidence 或相同 source binding 横向新建 Gate；下一设计直接为 `SINGLE-GPU-SMOKE-DESIGN`，再依序处理真实 optimizer/scaler、1 batch GPU 与 20--100 step TTT smoke。

本 Gate 不读取、选择、复制或哈希真实 checkpoint、manifest、数据或 cache；不创建 collection artifact 或 receipt；不修改 child/runtime；不运行 audit、DCP、CUDA/GPU、torchrun、forward/loss/backward、optimizer/scheduler step、训练、评测、推理或 LIBERO4IN1。

## 2. 两个非循环 root 与固定 artifact

future controlled collection 先创建 collection formal root。它的 tree 只能新增下列五个 fixed artifacts，且不得包含任何 receipt、formal-root revision、containing-tree OID、Git blob OID 或由这些值派生的字段：

```text
docs/build/PSM-WMA_immutable_source_collection_v1.json
docs/build/PSM-WMA_immutable_source_canonical_model_config_v1.json
docs/build/PSM-WMA_immutable_source_input_descriptor_v1.json
docs/build/PSM-WMA_immutable_source_manifest_v1.json
docs/build/PSM-WMA_immutable_source_checkpoint_descriptor_v1.json
```

input descriptor 是 canonical JSON，exact schema=`immutable_source_input_descriptor_v1`，key set 为 `schema,source_kind,source_entries`；`source_kind="checkpoint_source_manifest_v1"`。`source_entries` 是按 `ordinal` 严格递增的 nonempty array，每项 exact key set=`ordinal,byte_length,sha256`，其中 ordinal 为从 0 开始的 JSON integer，byte_length 为 positive JSON integer，sha256 为对应 source raw bytes 的 64 位 lowercase hex。它不含路径、URL、mutable ref、时间戳、环境变量或 caller label。其 canonical bytes SHA-256 为 `source_input_sha256`。

manifest 是 canonical JSON，exact schema=`immutable_source_manifest_v1`，key set 为 `schema,source_kind,source_input_sha256,source_entries`；`source_kind` 与 input descriptor 相同，`source_entries` 必须逐项逐字等于 input descriptor。其 canonical bytes SHA-256 为 `source_manifest_sha256`。`immutable_source_identifier=SHA256(canonical_json_bytes({"schema":"immutable_source_identifier_v1","source_manifest_sha256":source_manifest_sha256,"source_input_sha256":source_input_sha256}))`；此 exact three-key object 是唯一计算式。

checkpoint descriptor 是 raw canonical bytes 的 exact five-key `root_gitlink_checkpoint_source_descriptor_v1` object，完整继承 source-audit design v0.3 §5；其三个 digest 必须分别等于上述 `immutable_source_identifier`、`source_manifest_sha256`、`source_input_sha256`，其 canonical bytes SHA-256 为 `checkpoint_source_descriptor_sha256`。collection/artifact 或 receipt 不得只绑定 descriptor digest 而省略该 fixed path/blob。

collection artifact 的 raw blob 必须是 canonical JSON，exact key set 为：

```text
schema,
source_kind,
immutable_source_identifier,
source_manifest_sha256,
source_input_sha256,
checkpoint_source_descriptor_sha256
```

`schema` exact 为 `immutable_source_collection_v1`，`source_kind` exact 为 `checkpoint_source_manifest_v1`；四个 digest 均为 64 位 lowercase hex string。其 raw canonical bytes 的 SHA-256 为 `collection_artifact_sha256`。

canonical model config artifact 是 exact `canonical_native_local_ttt_config_v2` mapping，完整继承 source-audit design v0.3 §4；其 raw canonical bytes SHA-256 为 `canonical_model_config_artifact_sha256` 和 `canonical_model_config_sha256`。collection artifact 的四项 digest 必须仅由前述 committed candidate blobs 重算，禁止 caller/environment/working-tree supplied precomputed values。

只有 collection root 已提交后，才可创建 parent **精确等于该 collection formal root** 的独立 collection-receipt root。其 tree 的唯一新增 receipt path 为：

```text
docs/build/PSM-WMA_immutable_source_collection_receipt_v1.json
```

receipt raw blob 必须为 canonical JSON，exact key set 为：

```text
schema,
collection_formal_root_revision,
collection_artifact_path,
collection_artifact_schema,
collection_artifact_sha256,
collection_artifact_blob_native_oid,
source_input_artifact_path,
source_input_artifact_schema,
source_input_artifact_sha256,
source_input_artifact_blob_native_oid,
source_manifest_artifact_path,
source_manifest_artifact_schema,
source_manifest_artifact_sha256,
source_manifest_artifact_blob_native_oid,
checkpoint_source_descriptor_artifact_path,
checkpoint_source_descriptor_artifact_schema,
checkpoint_source_descriptor_artifact_sha256,
checkpoint_source_descriptor_artifact_blob_native_oid,
immutable_source_identifier,
source_manifest_sha256,
source_input_sha256,
checkpoint_source_descriptor_sha256,
canonical_model_config_sha256,
canonical_model_config_artifact_path,
canonical_model_config_artifact_sha256,
canonical_model_config_artifact_blob_native_oid
```

`schema` exact 为 `immutable_source_collection_receipt_v1`；`collection_formal_root_revision` 与全部 `*_blob_native_oid` 为 40 位 lowercase Git SHA-1；全部 `*_sha256` 为 64 位 lowercase hex。五个 path/schema 固定为本节的精确字符串及各自 exact schema。receipt-root parent tree 必须以 Git lookup 重算 collection root、五个 artifact blob、raw bytes 与全部 digest；并从 input descriptor→manifest→identifier→exact descriptor→collection artifact 逐项重算。任一 mismatch、未知 key/type、non-canonical bytes 或不可达 object 均 FAIL。

## 3. 既有 collection execution/closure transaction

后续严格遵循已批准的 `IMMUTABLE-SOURCE-COLLECTION-EXECUTION-DESIGN` 与 `IMMUTABLE-SOURCE-COLLECTION-CLOSURE` 两个 Gate；本设计不合并、删除或替代它们。两 Gate 的批准范围必须共同覆盖 collection root、receipt root 与本文件所有 fixed paths/schemas。

execution 先在 isolated temporary index/tree 中读取 source raw bytes 并构造 input descriptor、manifest、identifier、exact descriptor、collection/config blobs，逐 byte 验证 canonical JSON、derivation 和 digest，再构造候选 collection tree；任何 preflight FAIL 均保持 live target/index/HEAD/authority 逐 byte/entry 不变。仅 preflight PASS 后才能创建 collection root。closure Gate 随后只以其 committed tree lookup 构造 receipt blob、候选 receipt tree，并验证 receipt parent 精确等于 collection root。

每一 live mutation 前必须 snapshot target/index/HEAD；失败时 rollback 并验证恢复。rollback 或 HEAD-state verification 不完整/不确定时返回 `ROLLBACK_INCOMPLETE` fail-stop，禁止 authority、publication、runtime、GPU 或自动重试；普通失败同样不得产生 accepted source authority。staged allowlist 仅可含本节五个 collection paths、receipt path 和被执行 Gate 明示的 verifier/evidence 文件；严禁 `cosmos-framework` Gitlink、publication target、checkpoint/cache、训练产物和 Inbox rollover。

closure 成功后，future producer 只能接受经三方 review 绑定的 receipt-root revision、receipt path 和 receipt blob identity；从 receipt 的 collection-root lookup 导出 `immutable_source_identifier`、`source_manifest_sha256`、`source_input_sha256`、`checkpoint_source_descriptor_sha256` 与 `canonical_model_config_sha256`。不得接受 caller/environment/working-tree supplied mapping 或选择性重新计算。

## 4. 验收、失败分流与下游边界

验收必须证明：

1. collection root 与 receipt root 的非循环关系，且 receipt parent 精确等于 collection root；
2. 五个 collection artifact、receipt 的 exact paths、schemas、key/type/value、canonical bytes、raw-byte SHA-256 和 Git object identities 可从相应 committed tree 独立重算；
3. input descriptor→manifest→identifier→exact checkpoint descriptor→collection artifact 的四项 digest derivation 与 downstream source-evidence record/package 所需字段逐字一致；
4. unknown/missing/extra key、upper-case或长度不符 digest、Git reachability、parent、blob 或 byte drift 在 authority 前 fail-closed；
5. preflight 零 live mutation，live failure rollback，rollback 不完整 fail-stop，且 staged set 不含 Gitlink/publication/training residue。

批准本设计只允许按既有顺序申请 immutable-source collection execution design，随后 collection closure、source-evidence controlled-write、record/receipt closure、publication materializer/verifier 和 read-only root audit；不授权真实 collection 本身、source-evidence record 写入、publication、read-only audit、child 修改、GPU 或训练。该既有 source-evidence/publication 闭环结束后，下一设计必须是 `G0-R09-B-TTT-V035-SINGLE-GPU-SMOKE-DESIGN`，其范围应集中于真实 optimizer/scaler、单 batch GPU 和 20--100 step TTT smoke；不得再以 provenance 为由插入闭环外的横向 Gate。

请求唯一 verdict：

```text
APPROVE_TO_DESIGN_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION
```

或 `REQUEST_CHANGES(file:line)`。
