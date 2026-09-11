# PSM-WMA v0.3.5 Immutable Source Collection 收口设计 v0.1

**日期**：2026-09-12
**状态**：docs-only；待三方审核。
**Gate**：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-DESIGN`

## 1. 目的、最小化范围与路线终点

本 Gate 是 source-evidence 链的最后一个横向 provenance 设计：只冻结一次 future immutable-source collection 的证据合同，以及由其直接闭合的独立 receipt。它复用但不改写
`PSM-WMA_Local_Memory_v0.3.5_source_evidence_producer_closure_design_v0.1.md` §2--§5、
`PSM-WMA_Local_Memory_v0.3.5_canonical_native_root_gitlink_authority_source_audit_design_v0.3.md` §4--§5 的 canonical JSON 与 nested schema。

本 Gate 后，不得为 checkpoint authority、publication evidence 或相同 source binding 再横向新建 provenance design Gate。唯一剩余 source-evidence 工作是：在本合同下，经一次独立三方批准后完成受控 collection 与 receipt closure；closure 结束即进入 `SINGLE-GPU-SMOKE-DESIGN`，依序解锁真实 optimizer/scaler、1 batch GPU 和 20--100 step TTT smoke 的专用 Gate。

本 Gate 不读取、选择、复制或哈希真实 checkpoint、manifest、数据或 cache；不创建 collection artifact 或 receipt；不修改 child/runtime；不运行 audit、DCP、CUDA/GPU、torchrun、forward/loss/backward、optimizer/scheduler step、训练、评测、推理或 LIBERO4IN1。

## 2. 两个非循环 root 与固定 artifact

future controlled collection 先创建 collection formal root。它的 tree 只能新增下列两个 fixed artifacts，且不得包含任何 receipt、formal-root revision、containing-tree OID、Git blob OID 或由这些值派生的字段：

```text
docs/build/PSM-WMA_immutable_source_collection_v1.json
docs/build/PSM-WMA_immutable_source_canonical_model_config_v1.json
```

第一个 artifact 的 raw blob 必须是 canonical JSON，exact key set 为：

```text
schema,
source_kind,
immutable_source_identifier,
source_manifest_sha256,
source_input_sha256,
checkpoint_source_descriptor_sha256
```

`schema` exact 为 `immutable_source_collection_v1`，`source_kind` exact 为 `checkpoint_source_manifest_v1`；四个 digest 均为 64 位 lowercase hex string。其 raw canonical bytes 的 SHA-256 为 `collection_artifact_sha256`。

第二个 artifact 是 exact `canonical_native_local_ttt_config_v2` mapping，完整继承 source-audit design v0.3 §4；其 raw canonical bytes SHA-256 为 `canonical_model_config_artifact_sha256` 和 `canonical_model_config_sha256`。collection artifact 不得通过路径、URL、mutable ref、时间戳、环境变量、caller label 或 working tree 取代其中任一来源值。

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
immutable_source_identifier,
source_manifest_sha256,
source_input_sha256,
checkpoint_source_descriptor_sha256,
canonical_model_config_sha256,
canonical_model_config_artifact_path,
canonical_model_config_artifact_sha256
```

`schema` exact 为 `immutable_source_collection_receipt_v1`；`collection_formal_root_revision` 和 `collection_artifact_blob_native_oid` 为 40 位 lowercase Git SHA-1；全部 `*_sha256` 为 64 位 lowercase hex。path/schema 固定为本节的精确字符串。receipt-root parent tree 必须以 Git lookup 重算 collection root、两个 artifact blob、raw bytes 与全部 digest；任一 mismatch、未知 key/type、non-canonical bytes 或不可达 object 均 FAIL。

## 3. 单一受控 collection/closure transaction

后续只允许一个合并的 `IMMUTABLE-SOURCE-COLLECTION-CLOSURE` 执行 Gate，而不是再拆分 execution design、closure design 或其他 provenance 子 Gate。该 Gate 的批准范围必须同时明确 collection root、receipt root 与本文件所有固定 paths/schemas。

执行先在 isolated temporary index/tree 中完成：验证 input 的 immutable contract、构造两个 collection blobs、逐 byte 验证 canonical JSON/digest、构造候选 collection tree；任何 preflight FAIL 均保持 live target/index/HEAD/authority 逐 byte/entry 不变。仅 preflight PASS 后才能创建 collection root；随后仅以其 committed tree lookup 构造 receipt blob、候选 receipt tree，并验证 receipt parent 精确等于 collection root。

每一 live mutation 前必须 snapshot target/index/HEAD；失败时 rollback 并验证恢复。rollback 或 HEAD-state verification 不完整/不确定时返回 `ROLLBACK_INCOMPLETE` fail-stop，禁止 authority、publication、runtime、GPU 或自动重试；普通失败同样不得产生 accepted source authority。staged allowlist 仅可含本节两个 collection paths、receipt path 和被执行 Gate 明示的 verifier/evidence 文件；严禁 `cosmos-framework` Gitlink、publication target、checkpoint/cache、训练产物和 Inbox rollover。

closure 成功后，future producer 只能接受经三方 review 绑定的 receipt-root revision、receipt path 和 receipt blob identity；从 receipt 的 collection-root lookup 导出 `immutable_source_identifier`、`source_manifest_sha256`、`source_input_sha256`、`checkpoint_source_descriptor_sha256` 与 `canonical_model_config_sha256`。不得接受 caller/environment/working-tree supplied mapping 或选择性重新计算。

## 4. 验收、失败分流与下游边界

验收必须证明：

1. collection root 与 receipt root 的非循环关系，且 receipt parent 精确等于 collection root；
2. 两个 collection artifact、receipt 的 exact paths、schemas、key/type/value、canonical bytes、raw-byte SHA-256 和 Git object identities 可从相应 committed tree 独立重算；
3. collection artifact 的四项 digest 与 downstream source-evidence record/package 所需字段逐字一致；
4. unknown/missing/extra key、upper-case或长度不符 digest、Git reachability、parent、blob 或 byte drift 在 authority 前 fail-closed；
5. preflight 零 live mutation，live failure rollback，rollback 不完整 fail-stop，且 staged set 不含 Gitlink/publication/training residue。

批准本设计只允许申请上述单一 collection/closure execution Gate；不授权真实 collection 本身、source-evidence record 写入、publication、read-only audit、child 修改、GPU 或训练。该执行 Gate closure 后，下一设计必须是 `G0-R09-B-TTT-V035-SINGLE-GPU-SMOKE-DESIGN`，其范围应集中于真实 optimizer/scaler、单 batch GPU 和 20--100 step TTT smoke；不得再以 provenance 为由插入横向 Gate。

请求唯一 verdict：

```text
APPROVE_TO_DESIGN_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION
```

或 `REQUEST_CHANGES(file:line)`。
