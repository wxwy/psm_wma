# PSM-WMA v0.3.5 Root Gitlink Authority Source-audit 设计 v0.3

**日期**：2026-09-12
**状态**：docs-only remediation；待三方审核。
**Gate**：`G0-R09-B-TTT-V035-CANONICAL-NATIVE-ROOT-GITLINK-AUTHORITY-SOURCE-AUDIT-DESIGN`

**supersedes**：v0.2 的 §2；v0.1 的范围、只读输入、fail-closed 产物和后续序列继续生效。v0.2 §1 的 native tree OID 与 raw-tree-byte SHA-256 semantics 继续生效。若冲突，以本文件为准。

## 1. 前置与不变边界

前置仍是 synthetic CPU/static checkpoint remediation closure formal `69f028b2395d2f5dc6f36ac27803eb262b537e3c` / child `93a89ba61306d840a008813f62f26a34d54850f4` 的三方 closure；它只证明 synthetic fixture contract，绝不代表 production Git/checkpoint provenance。

本 Gate 只冻结 future **只读** root Gitlink source audit 的 root-owned publication 和证据合同。不得修改 child 或 root 运行时代码；不得读取真实 checkpoint/data/cache，不得 DCP、CUDA/GPU、torchrun、forward/loss/backward、optimizer/scheduler step、sidecar、训练、评测、推理或 LIBERO4IN1。

所有本文件所称 canonical JSON 均严格为 UTF-8、递归 key sort、`separators=(',', ':')`、`ensure_ascii=false`、`allow_nan=false` 的 JSON object bytes；digest 均为这些 bytes 的 SHA-256、64 位 lowercase hex。mapping key set 必须 exact，未知、缺失、重复语义、非 object、非 string、bool masquerading、非有限数、schema/type/value/digest drift 均为 FAIL。

## 2. 保留的 Git tree semantics

`root_tree_native_oid`、`child_tree_native_oid` 是 Git SHA-1 tree object ID（40 位 lowercase hex），不是外部 SHA-256。audit 的 tree byte source 唯一是 `git cat-file tree <native_oid>` 的 stdout 原始 tree-content bytes；不含命令标签、附加换行、JSON 或 API response。`tree_content_sha256=SHA256(raw_tree_content_bytes)`。

每条 tree record 必须 exact 包含：`schema="root_gitlink_tree_record_v1"`、`native_tree_oid`、`tree_content_sha256`、`object_type="tree"`、`byte_length`。其 canonical JSON SHA-256 为 `tree_record_sha256`。唯一关系保持为：`formal root revision -> native tree OID -> raw tree content bytes -> tree_content_sha256 -> canonical tree record -> tree_record_sha256`；任一 OID/type/bytes/length/digest 不匹配即 FAIL。

## 3. 非循环的 root-owned publication

唯一 publication 路径固定为 root tree 内的 `docs/build/PSM-WMA_root_gitlink_authority_publication_v1.json`。该 blob 只表达被发布的 config/source mapping，**不得**表达自身 digest、native blob OID、containing root tree OID、formal revision、verifier schema 或任何派生 audit value。

publication blob 本身必须是 exact 三键 canonical JSON object：

```text
schema = "root_gitlink_authority_publication_v1"
canonical_model_config
checkpoint_source_descriptor
```

因此 blob 的 raw bytes 可先确定并写入 Git；只有在锁定 formal root revision 后，audit 才从已验证 root tree 的固定 path lookup **外部派生**下列 binding，绝不要求 blob 内字段反向声明它们：

```text
formal_root_revision
root_tree_native_oid
publication_path = "docs/build/PSM-WMA_root_gitlink_authority_publication_v1.json"
publication_blob_native_oid
publication_blob_sha256 = SHA256(raw_publication_blob_bytes)
verifier_schema = "root_gitlink_authority_publication_verifier_v1"
```

root ownership 的唯一证明是：已按 §2 验证的 formal root tree 中，固定 path 精确指向该 `publication_blob_native_oid`，且从该 Git blob 读得的 raw bytes SHA-256 精确等于外部 audit record 的 `publication_blob_sha256`。不得接受 caller/env/working-tree/path alias/time 输入，也不得用 publication payload 或 child source 声明的 revision/OID/digest 代替 root-tree lookup。

## 4. `canonical_model_config` 的冻结 schema

publication 的 `canonical_model_config` 必须是 exact `canonical_native_local_ttt_config_v2` object；这是已批准的 `PSM-WMA_Local_Memory_v0.3.5_canonical_native_feature_config_optimizer_checkpoint_refreeze_design_v0.2.md` §2 的 production config identity，在本 Gate 不重新定义或放宽。其 key set 必须严格为：

```text
schema,
local_memory_enabled, local_memory_dim,
local_history_enabled, local_history_backend,
local_history_evidence_dim, local_history_state_enabled,
local_ttt_enabled, enable_input_bias,
ttt_tbptt_steps, ttt_inner_lr, k_local,
local_evidence_feature_version, local_fast_state_dtype,
local_runtime_resume_mode
```

`schema` 必须 exact 为 `canonical_native_local_ttt_config_v2`。五个 `*_enabled`/`enable_input_bias` 字段必须为 JSON bool；`local_memory_dim` exact 为 JSON number `32`；`local_history_backend` exact 为 `"ttt_fast_weight"`；`local_history_evidence_dim`、`ttt_tbptt_steps`、`k_local` 均为 positive JSON integer，不能为 bool；`ttt_inner_lr` 为 finite positive JSON number，不能为 bool；`local_evidence_feature_version`、`local_fast_state_dtype`、`local_runtime_resume_mode` 分别 exact 为 `"causal_visual96_executed_action10_v1"`、`"fp32"`、`"slow_only_no_mid_episode_resume"`。active production mapping 还必须 exact 满足 `local_memory_enabled=true`、`local_history_enabled=true`、`local_history_state_enabled=false`、`local_ttt_enabled=true`；`K_local` 是 published resolved slot count，不得折叠到 hidden dimension。

`canonical_model_config_sha256=SHA256(canonical_json_bytes(canonical_model_config))`。任何 type/value/schema/key/digest drift 必须在产生 authority 前 FAIL。

## 5. `checkpoint_source_descriptor` 的冻结 schema

publication 的 `checkpoint_source_descriptor` 必须是 exact `root_gitlink_checkpoint_source_descriptor_v1` object，key set 严格为：

```text
schema,
source_kind,
immutable_source_identifier,
source_manifest_sha256,
source_input_sha256
```

`schema` 必须 exact 为 `root_gitlink_checkpoint_source_descriptor_v1`；`source_kind` 必须 exact 为 `checkpoint_source_manifest_v1`；`immutable_source_identifier`、`source_manifest_sha256`、`source_input_sha256` 均必须是 64 位 lowercase hex string。前者是 checkpoint source 的 immutable content identifier；后两者分别是 source manifest canonical bytes 与 source-input descriptor canonical bytes的 SHA-256，均不得为空、路径、URL、时间戳、环境变量、caller label 或 mutable ref。该 schema 不承载 checkpoint bytes，也不允许通过 publication path 以外的引用取值。

`checkpoint_source_descriptor_sha256=SHA256(canonical_json_bytes(checkpoint_source_descriptor))`。`source_kind`、schema、key/type/value、任何三项 digest 或 canonical bytes 的 drift 必须在产生 authority 前 FAIL。

## 6. 外部 source-audit record 与 fail-closed authority

future source audit 只能在所有 root/child reachability、§2 tree records、固定 path Git blob lookup、§3 external binding、§4--§5 nested mapping schema 和 digest 都通过后，产生 exact `root_gitlink_source_audit_record_v1`。record key set 必须严格为：

```text
schema,
formal_root_revision, root_tree_native_oid,
submodule_path, child_git_revision, child_tree_native_oid,
publication_path, publication_blob_native_oid, publication_blob_sha256,
verifier_schema, canonical_model_config_sha256,
checkpoint_source_descriptor_sha256,
root_tree_record_sha256, child_tree_record_sha256
```

`schema` exact 为 `root_gitlink_source_audit_record_v1`，`submodule_path` exact 为 `cosmos-framework`，`verifier_schema` exact 为 `root_gitlink_authority_publication_verifier_v1`；formal/child revision 与 native object OID 都是 exact reachable lowercase Git SHA-1；所有 `*_sha256` 都是 64 位 lowercase hex，并须由本次只读 lookup/recompute 得出，不能由 publication payload、child code、caller 或 environment 供给。

成功的 record 仅是 future `root_gitlink_authority_v1` 的唯一可验证输入；其 canonical record SHA-256 必须与生成 authority 一并绑定。任一 Git object/path/blob/schema/key/type/value/digest/reachability/unknown-input failure 或未知结果都必须 FAIL，禁止生成 record/authority，禁止 runtime integration。成功不代表真实 checkpoint restore、GPU 或训练授权。

## 7. 后续序列与 verdict

本设计获三方 `APPROVE_TO_DESIGN_R09_B_TTT_V035_CANONICAL_NATIVE_ROOT_GITLINK_AUTHORITY_SOURCE_AUDIT` 后，才允许创建下一份 docs-only source-audit implementation design。实际只读 audit implementation closure、root-owned authority runtime integration design/implementation、真实-I/O preflight 和 GPU Gate 必须各自重新三方审核。

请求唯一 verdict：

```text
APPROVE_TO_DESIGN_R09_B_TTT_V035_CANONICAL_NATIVE_ROOT_GITLINK_AUTHORITY_SOURCE_AUDIT
```

或 `REQUEST_CHANGES(file:line)`。本设计不授权 child/root 运行时代码、真实 I/O、GPU 或训练。
