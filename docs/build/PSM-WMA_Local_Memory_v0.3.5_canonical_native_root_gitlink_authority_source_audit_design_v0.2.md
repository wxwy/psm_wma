# PSM-WMA v0.3.5 Root Gitlink Authority Source-audit 设计 v0.2

**日期**：2026-09-12
**状态**：docs-only remediation；待三方审核。
**Gate**：`G0-R09-B-TTT-V035-CANONICAL-NATIVE-ROOT-GITLINK-AUTHORITY-SOURCE-AUDIT-DESIGN`

**supersedes**：v0.1 的 tree digest 与 root-owned publication 未冻结表述；其他范围与禁止项不变。

## 1. Native tree OID 与外部 SHA-256 的 exact semantics

`root_tree_native_oid`、`child_tree_native_oid` 是 Git SHA-1 tree object ID（40 位 lowercase hex），绝不是 `root_tree_sha256`/`child_tree_sha256`。audit 使用 Git object database 的原始 tree content bytes：`git cat-file tree <native_oid>` 的 stdout 原始字节（不含命令输出标签、换行追加、JSON 或 API 响应）。外部 digest 是 `SHA256(raw_tree_content_bytes)`。

每条 tree record 必须 exact 包含：`schema="root_gitlink_tree_record_v1"`、`native_tree_oid`、`tree_content_sha256`、`object_type="tree"`、`byte_length`。canonical record bytes 为 UTF-8 JSON、recursive key sort、separators `(',', ':')`、`allow_nan=false`；其 SHA-256 另记为 `tree_record_sha256`。唯一关系为 `formal revision -> native tree OID -> raw tree content bytes -> tree_content_sha256 -> canonical record -> tree_record_sha256`。任一 OID/type/bytes/length/digest 不匹配即 FAIL。

## 2. Root-owned publication trust root

config/source authority 只能来自 root tree 内固定路径 `docs/build/PSM-WMA_root_gitlink_authority_publication_v1.json` 的 immutable blob。其 envelope exact schema=`root_gitlink_authority_publication_v1`，keys 为 `schema,canonical_model_config,checkpoint_source_descriptor,publication_root_tree_native_oid,publication_blob_sha256,verifier_schema`；两 mapping 都须 exact versioned schema，并用 §1 canonical JSON bytes SHA-256 计算 digest。`publication_root_tree_native_oid` 必须等于 audited root tree native OID；`publication_blob_sha256` 必须等于该 blob 原始 bytes SHA-256；`verifier_schema="root_gitlink_authority_publication_verifier_v1"`。

“signature-equivalent”信任根仅是：该 immutable blob 被 audited root tree 内容精确引用，root formal revision/tree 已通过 §1 验证，且 blob path、bytes、envelope keyset/schema/digest 全部 exact；无外部 caller、env、working tree 或时间输入。缺 publication/path/blob/schema/key/digest/owner 任何一项均 FAIL，禁止产生 `root_gitlink_authority_v1`。

## 3. Verdict

请求 `APPROVE_TO_DESIGN_R09_B_TTT_V035_CANONICAL_NATIVE_ROOT_GITLINK_AUTHORITY_SOURCE_AUDIT` 或 `REQUEST_CHANGES(file:line)`。批准仍只允许下一 docs-only implementation design，不授权代码、真实 I/O、GPU 或训练。
