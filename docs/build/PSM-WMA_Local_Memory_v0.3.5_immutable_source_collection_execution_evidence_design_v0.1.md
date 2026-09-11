# Immutable Source Collection Execution Evidence 设计 v0.1

**Gate**：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-DESIGN`  
**状态**：docs-only；待三方审核。

本文件为 controlled-execution v0.2 §4 的 exact override；不运行 executor 或真实 I/O。

## Exact schema

record 必须是 canonical JSON：UTF-8、递归 key sort、`separators=(',', ':')`、`ensure_ascii=false`、`allow_nan=false`。outer exact keys：`schema,status,execution,tool,environment,authority,lineage,source_entries,handoff,candidates,collection,receipt,post_checks,push_publication,rollback,evidence_sha256`；`schema`=`immutable_source_collection_execution_evidence_v1`，`status` 仅 `PASS` 或 `FAIL`。

共同 nested exact keys：

```text
PASS execution={approval_formal_root,command_argv,interpreter,phase}
FAIL execution={approval_formal_root,command_argv,interpreter,phase,failure_code}
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

PASS `source_entries` 为 nonempty ordered array；each entry exact `{ordinal,byte_length,sha256}`，ordinal 为非 bool、`>=0` JSON integer，byte_length 为非 bool、`>0` JSON integer。command_argv 为 string array；FAIL `failure_code` 为非空 stable-identifier string；delta_paths 为 fixed approved path string array；paths 仅允许 approved fixed tool/workdir/authority artifact paths，不得含 source transport/source raw path、raw bytes、URL 或 secret。

FAIL `execution.phase` 必须且只能是下列与固定检查顺序一一对应的有限值：`tool_identity`、`environment`、`authority`、`lineage`、`source_read`、`candidate_construction`、`candidate_verification`、`collection`、`receipt`、`post_check`、`push_publication`。它表示**首个未成功完成的主检查**；rollback 是该主失败后的 recovery outcome，不是可覆盖主失败 identity 的 phase。其前所有 phase 必须按 PASS 类型完整 materialize，其后所有 phase 必须按下表的未到达 null-record materialize。`failure_code` 只说明该 phase 内的失败原因，不得改变 phase 或 nullability。

FAIL 的确定性 partial 规则如下，禁止伪造 digest：

| failure phase | 本 phase 的唯一允许 partial 表示 | 后续字段 |
| --- | --- | --- |
| `tool_identity`、`environment`、`authority`、`lineage` | 本 phase 与其后 section 的 SHA/revision/blob/tree/ref/path/boolean 均为对应 null；`source_entries=[]`；handoff/candidates 全 null；rollback 精确为 `{before_snapshot_sha256:null,after_snapshot_sha256:null,verified:null}`。 | 全部后续 section 的 null-record。 |
| `source_read` | `source_entries` 是已成功 read/hash 的严格 ordered prefix（可为空）；每个已有 entry 完整 typed，失败 entry 不写 placeholder。handoff/candidates 全 null；rollback 为 pre-live null-record。 | collection/receipt null-record，后续 boolean/ref/path 为 null。 |
| `candidate_construction` | `source_entries` 必须完整；handoff 必为全 null。`candidates` 按固定顺序 `input_descriptor_sha256,manifest_sha256,identifier_sha256,checkpoint_descriptor_sha256,collection_sha256,config_sha256` 只允许长度 `0..5` 的完整 64-hex 前缀，余项必须 null；rollback 为 pre-live null-record。 | collection/receipt null-record，post_checks/push_publication 的字段为 null。 |
| `candidate_verification` | source_entries、六个 candidates 与 handoff 均必须完整 concrete；本 phase 表示 complete handoff 对 candidate/config equality、single-use 或 digest re-derivation 的验证失败，不能将已存在 digest 清空。rollback 为 pre-live null-record。 | collection/receipt null-record，post_checks/push_publication 的字段为 null。 |
| `collection` | source_entries、handoff、candidates 必须完整；collection 使用 exact null-record，不得写 partial revision/tree/blob 或 delta path；receipt 亦为 exact null-record。rollback 必须为 concrete live witness：两个 snapshot SHA 均 64-hex，`verified=true`；若不能验证，保留 phase=`collection` 且 failure_code=`ROLLBACK_INCOMPLETE`、`verified=false`。 | post_checks/push_publication 的字段为 null。 |
| `receipt` | source_entries、handoff、candidates、collection 必须完整；receipt 使用 exact null-record，不得写 partial revision/tree/blob 或 delta path。rollback 与 `collection` row 的 concrete live witness 规则相同。 | post_checks/push_publication 的字段为 null。 |
| `post_check` | 之前 collection/receipt 必须完整。`post_checks` 的固定顺序为 `authority,lineage,derivation,collection,receipt`：严格成功前缀为 `true`，首个失败 check 必为 `false`，其后 keys 必为 null。rollback 为 concrete live witness，且 `verified=false` 时 failure_code=`ROLLBACK_INCOMPLETE`，但 phase 仍为 `post_check`。 | push_publication 的字段为 null。 |
| `push_publication` | 之前 collection/receipt 与五个 post_checks 必须完整且均 true；`push_publication` 的两个 observed JSON boolean 均可 concrete，且至少一个必须为 `true`，记录禁止 invariant 的实际违反；该 FAIL-only record绝不授权下游。rollback 为 concrete live witness，`verified=false` 时 failure_code=`ROLLBACK_INCOMPLETE`，phase 仍为 `push_publication`。 | 无后续字段。 |

除上表明确允许的 partial prefix 外，SHA fields 在 FAIL 必须为 64 lowercase hex 或 null；revision/blob/tree fields 必须为 40 lowercase Git SHA-1 或 null；boolean fields 必须为 JSON boolean 或 null；refs/paths 必须为 approved string 或 null。auditor 必须由 `phase` 和该表逐字段导出可接受的 nullability，未知 phase、非前缀 candidates/source entries、或任一不符均 FAIL。

PASS 规则：`execution` 另含 exact `phase="complete"`；collection/receipt revision 非空、`post_checks` 所有值 true、`pushed=false`、`published=false`、rollback `verified=true`。FAIL 规则：`execution` 另含上表的 exact `phase,failure_code`；collection null-record 精确为 `{revision:null,tree_native_oid:null,parent_revision:null,delta_paths:[]}`，receipt null-record 精确为 `{revision:null,tree_native_oid:null,parent_revision:null,delta_paths:[],blob_native_oid:null}`。pre-live null rollback 仅允许 `tool_identity` 至 `candidate_verification`；live rollback witness 仅允许 `collection`、`receipt`、`post_check`、`push_publication`，其 `verified=false` 必须 fail-stop 为 `ROLLBACK_INCOMPLETE` 而不覆盖 execution phase。除表中定义的 null key 外，FAIL 的 handoff、candidates、collection、receipt、post_checks、push_publication、rollback 均不得遗漏 nested exact key。未知/缺失/type drift FAIL。

检查顺序固定：tool identity→environment→authority→lineage→source entries→candidate construction→handoff/candidate verification→collection→receipt→post-check→push/publication；rollback 仅在 live 主失败后执行并记录 outcome，不参与 primary phase 排序。`evidence_sha256` 为去除此字段后的 canonical bytes SHA-256；audit 必须重算并拒绝不一致记录。

请求 `APPROVE_TO_DESIGN_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_CONTROLLED_EXECUTION` 或 `REQUEST_CHANGES(file:line)`。
