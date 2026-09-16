# Source-evidence closure request instance schema v0.1

**Gate**：`G0-R09-B-TTT-V035-SOURCE-EVIDENCE-CLOSURE-REQUEST-INSTANCE-SCHEMA-DESIGN`
**状态**：docs-only；不创建 instance，不执行 source I/O。

## 目的

为已批准的 Stage‑2 source-evidence producer/closure 与 immutable collection executor 冻结一份可独立审核的 canonical request instance schema。本文只解决字段来源与 identity 绑定，不替代 execution approval。

## Exact instance

instance 是 UTF-8 canonical JSON（递归排序、紧凑分隔符、单个 terminal LF），顶层 exact keys：

```text
schema, formal_root, child_gitlink, authority, source, executor, producer,
record, receipt, publication, root_audit, preflight, execution, sha256
```

`schema="root_source_evidence_closure_request_instance_v1"`。所有 path、argv、identity、raw SHA、Git OID 和 ref 均由同轮只读 observation 绑定；禁止从环境、旧 instance 或本文固定值推导。

`sha256` 是删除顶层 `sha256` 字段后的整个 instance canonical JSON（含 terminal LF）SHA-256；不把自身或 detached Markdown 纳入 preimage。顶层与嵌套对象均拒绝未知键、重复语义键和非 canonical bytes。

## 嵌套 exact keys 与权威来源

以下对象的 key 集合固定，字段类型除特别说明外均为 `string`；`sha256` 为 lowercase 64-hex，Git revision/blob/gitlink 为 lowercase 40-hex，`argv`/`paths` 为有序 string array，布尔字段为 JSON boolean：

```text
authority = {fixed_ref,candidate_revision,selection_path,selection_blob_native_oid,
selection_raw_sha256,config_path,config_blob_native_oid,config_raw_sha256,
local_ref_revision,remote_ref_revision}
source = {root_fd,source_kind,selection_raw_sha256,selected_paths,root_identity}
executor = {module_path,module_blob_native_oid,module_raw_sha256,interpreter_path,
interpreter_raw_sha256,git_path,git_raw_sha256,argv,cwd,index_path,evidence_path,
sanitized_env_sha256}
producer = {module_path,module_blob_native_oid,module_raw_sha256,callables,
one_shot_abi}
record = {path,schema,keys,source_digest_receipt_mapping}
receipt = {path,schema,keys,parent_root_revision,child_gitlink,post_commit_boundary}
publication = {package_schema,package_keys,witness_schema,witness_keys,package_path,
witness_path,verifier_identity}
root_audit = {module_path,module_blob_native_oid,module_raw_sha256,argv,pass_predicate}
preflight = {absent_paths,absent_refs,head_revision,index_tree_native_oid,
worktree_snapshot_sha256,zero_mutation}
execution = {order,one_shot,no_retry,pass_hard_stop,failure_rollback}
```

`record.keys` 固定为 `schema,source_kind,immutable_source_identifier,source_manifest_sha256,source_input_sha256,checkpoint_source_descriptor_sha256`；`receipt.keys` 固定为 collection closure v0.1 的 13 键：`schema,collection_formal_root_revision,collection_artifact_path,collection_artifact_schema,collection_artifact_sha256,collection_artifact_blob_native_oid,immutable_source_identifier,source_manifest_sha256,source_input_sha256,checkpoint_source_descriptor_sha256,canonical_model_config_sha256,canonical_model_config_artifact_path,canonical_model_config_artifact_sha256`。`publication.package_keys` 与 `publication.witness_keys` 分别固定为 producer/closure design v0.1 的七键 package/witness 集合；`source_digest_receipt_mapping` 是四个 record 字段到 receipt 同名字段的一一映射，禁止 caller 补值。

schema 权威依次为：producer/closure design formal root=`1d8f103e1dcf119ac8e90abbcbcde0eaced0bb95`、immutable collection execution-evidence design formal root=`2c73ad0bf9f49d1dd13f0803046ac75f3cd9449c`、当前已关闭 producer/closure CPU/static implementation formal root=`7b3bf58b27a55b1220b86eeeccb1db5659dd0500`，child/Gitlink 均为 `93a89ba61306d840a008813f62f26a34d54850f4`。`producer` 只绑定 `tools/psm_wma/immutable_source_collection.py` 在该 implementation root 中的 blob/raw identity，以及四个已关闭 helper 的 callable 名称；不把它们宣称为尚未接入的独立 production entrypoint。

## 资产字段

- `authority`：Stage‑1 fixed ref、candidate revision、selection/config path、blob OID、raw SHA，以及 local/remote ref observation。
- `source`：source-root FD contract、source kind、selection raw SHA、checkpoint source path grammar；只记录 FD identity，不记录 source payload。
- `executor`：唯一 `tools/psm_wma/immutable_source_collection.py` 的 formal-tree blob OID/raw SHA、interpreter/Git identity、完整 argv、cwd/index/evidence path 与 sanitized environment。
- `producer`：`produce_source_evidence_record`、`produce_source_package`、`produce_source_closure`、`verify_source_package_and_witness` 的 callable/module identity 与 raw-byte/one-shot ABI。
- `record`：fixed record path、exact schema/key set、source digest→receipt 字段映射。
- `receipt`：collection receipt constructor/path/schema、parent-root/child identity 与 post-commit receipt-root boundary。
- `publication`：package/witness derived-only schema、唯一 output path/ref、publication verifier identity；本 instance 只绑定 contract，不执行 publication。
- `root_audit`：唯一 audit entrypoint 的 formal-tree identity、argv 与 PASS/FAIL predicate。
- `preflight`：所有 designated output/ref/path 的 same-round absence observations、index/HEAD/worktree snapshot digest 与 zero-mutation predicate。
- `execution`：固定顺序 `collection → producer → record → receipt → root_audit`、one-shot/no-retry、PASS hard-stop 与 failure/rollback semantics。

## Gate 与禁止范围

构造 instance 仅允许同轮读取上述 identities 并生成一份 JSON/detached Markdown sibling；随后必须对 exact instance SHA 重新取得 MM/DS/ChatGPT 三方审核。审核不授权执行；执行仍须另有 `APPROVE_TO_WRITE_SOURCE_EVIDENCE`，PASS 后必须停在独立 receipt-root review。

禁止真实 source/checkpoint/manifest/data/cache payload 读取、record/publication 写入、authority ref/child/runtime 修改、GPU/CUDA/torchrun、训练、评测和推理。

请求 verdict：`APPROVE_TO_DESIGN_R09_B_TTT_V035_SOURCE_EVIDENCE_CLOSURE_REQUEST_INSTANCE_SCHEMA` 或 `REQUEST_CHANGES(file:line)`。
