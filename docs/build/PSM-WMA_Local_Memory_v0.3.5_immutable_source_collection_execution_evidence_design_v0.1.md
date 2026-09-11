# Immutable Source Collection Execution Evidence 设计 v0.1

**Gate**：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-DESIGN`  
**状态**：docs-only；待三方审核。

本文件为 controlled-execution v0.2 §4 的 exact override；不运行 executor 或真实 I/O。

## Exact schema

record 必须是 canonical JSON：UTF-8、递归 key sort、`separators=(',', ':')`、`ensure_ascii=false`、`allow_nan=false`。outer exact keys：`schema,status,execution,tool,environment,authority,lineage,source_entries,handoff,candidates,collection,receipt,post_checks,push_publication,rollback,evidence_sha256`；`schema`=`immutable_source_collection_execution_evidence_v1`，`status` 仅 `PASS` 或 `FAIL`。

共同 nested exact keys：

```text
execution={approval_formal_root,command_argv,interpreter}
tool={path,blob_native_oid,raw_sha256}
environment={workdir,python_executable,cpu_only,no_network,sanitized_env_sha256}
authority={root_revision,selection_path,selection_blob_native_oid,selection_raw_sha256,config_path,config_blob_native_oid,config_raw_sha256}
lineage={target_ref,expected_base_root_revision,expected_child_gitlink,authority_approval_formal_root_revision}
handoff={candidate_handoff_sha256,consumed_once}
candidates={input_descriptor_sha256,manifest_sha256,identifier_sha256,checkpoint_descriptor_sha256,collection_sha256,config_sha256}
collection={revision,tree_native_oid,parent_revision,delta_paths}
receipt={revision,tree_native_oid,parent_revision,delta_paths,blob_native_oid}
post_checks={authority,lineage,derivation,collection,receipt}
push_publication={pushed,published}
rollback={before_snapshot_sha256,after_snapshot_sha256,verified}
```

`source_entries` 为 nonempty ordered array，each exact `{ordinal,byte_length,sha256}`。SHA fields 为 64 lowercase hex，revision/blob/tree fields 为 40 lowercase Git SHA-1；boolean fields为 JSON boolean；paths 仅允许 approved fixed tool/workdir/authority artifact paths，不得含 source transport/source raw path、raw bytes、URL 或 secret。

PASS 规则：`execution` 另含 exact `phase="complete"`；collection/receipt revision 非空、`post_checks` 所有值 true、`pushed=false`、`published=false`、rollback `verified=true`。FAIL 规则：`execution` 另含 exact `phase,failure_code`（非空 stable identifiers）；collection/receipt 可为 null-record `{revision:null,tree_native_oid:null,parent_revision:null,delta_paths:[],blob_native_oid:null}`；rollback 必须有 `verified`，不完整恢复时 failure_code=`ROLLBACK_INCOMPLETE`。未知/缺失/type drift FAIL。

检查顺序固定：tool identity→environment→authority→lineage→source entries/handoff→candidate derivation→collection→receipt→post-check→push/publication→rollback。`evidence_sha256` 为去除此字段后的 canonical bytes SHA-256；audit 必须重算并拒绝不一致记录。

请求 `APPROVE_TO_DESIGN_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_CONTROLLED_EXECUTION` 或 `REQUEST_CHANGES(file:line)`。
