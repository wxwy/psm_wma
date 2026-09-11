# PSM-WMA v0.3.5 Immutable Source Collection Controlled Execution 设计 v0.2

**日期**：2026-09-12
**状态**：docs-only；待三方审核。
**Gate**：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-DESIGN`

## 1. v0.1 override 与边界

本版本覆盖 v0.1 中 future executor、authority root 和 execution evidence 未落地的部分。它只冻结后续设计/CPU-static 实现的顺序与可验证合同；不创建 authority root、不读取 source、不写 collection/receipt、不运行项目代码、child/GPU/训练。

真实 execution approval 前必须依序完成并获独立三方批准：executor implementation design → root CPU/static implementation closure → authority-root materialization/binding → controlled execution approval。该顺序属于现有 collection/source-evidence 闭环，不增加横向 provenance Gate。

## 2. Executor source identity 与 CPU/static witnesses

唯一 executor 路径固定为 `tools/psm_wma/immutable_source_collection.py`；后续 implementation design 必须冻结该文件及直接 stdlib test 文件的 allowlist、formal root/path/Git blob OID/raw SHA-256。任何路径、source blob、interpreter 或 allowlist drift 在 source open 前 FAIL。

CPU/static closure 必须以 temporary fixtures 直接见证：authority tuple/path/blob drift、authority-parent drift、target/base/Gitlink drift、root-FD symlink/escape/regular-file rejection、same-FD 双 hash/fstat race、single-use handoff、five-path/one-path allowlists、rollback 成功和 `ROLLBACK_INCOMPLETE`。不得使用真实 source、checkpoint、cache、网络、GPU 或 live Git target。

## 3. Authority-root materialization/binding

在任何 source entry 打开前，独立 materialization transaction 创建唯一 execution-authority root：其 parent 精确等于经审核的 authority formal root，delta 恰为：

```text
docs/build/PSM-WMA_immutable_source_selection_request_v1.json
docs/build/PSM-WMA_immutable_source_canonical_model_config_v1.json
```

从 committed tree 独立重算 parent、两个 path、schema、Git blob OID 和 raw SHA-256；三方 review 明示绑定七字段 tuple `(authority_root_revision, selection_path, selection_blob_native_oid, selection_raw_sha256, config_path, config_blob_native_oid, config_raw_sha256)`。未知/额外 path、parent/blob/bytes drift 或未绑定 tuple 均 FAIL；executor 只接受该 tuple。

## 4. Canonical execution evidence

future executor 对每次 PASS/FAIL 输出 canonical `immutable_source_collection_execution_evidence_v1`，由已绑定 tool identity 写入受控 failure-evidence directory；未知/缺失/drift 字段 FAIL。它必须含 execution approval/formal root、tool path/blob/raw SHA、interpreter/command、sanitized env/workdir/CPU-only/no-network identity、authority tuple、target lineage、ordered `(ordinal,byte_length,sha256)`、`candidate_handoff_sha256`、candidate digests、collection/receipt root/tree/parent/delta、post-check、push/publication state。

FAIL 还必须含 phase/stable code、before/after snapshot、rollback verification 或 `ROLLBACK_INCOMPLETE`；不得含 raw source bytes、路径、URL、secret。evidence 由后续 read-only audit 从 committed binding/recomputed values独立核验，不能替代 source-evidence record/package/witness。

## 5. 后续授权

批准本设计只允许新建 executor implementation design；不授权真实 source I/O、authority materialization、collection/receipt、publication、child、GPU 或训练。既有 source-evidence → record/receipt → publication verifier → root audit 闭合后，下一设计固定为 single-GPU smoke。

请求唯一 verdict：`APPROVE_TO_DESIGN_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_CONTROLLED_EXECUTION` 或 `REQUEST_CHANGES(file:line)`。
