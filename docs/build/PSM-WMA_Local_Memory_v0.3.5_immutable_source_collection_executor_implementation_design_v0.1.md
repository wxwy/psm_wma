# Immutable Source Collection Executor CPU/static implementation 设计 v0.1

**Gate**：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-IMPLEMENTATION-DESIGN`  
**状态**：docs-only；待三方审核。

## 范围

本设计仅将已批准 controlled-execution v0.2 固化为后续 root CPU/static 实现的文件 allowlist、temporary-fixture tests 和 fail-closed interface。唯一 production executor 为 `tools/psm_wma/immutable_source_collection.py`；仅允许新增该文件及 `tools/psm_wma/test_immutable_source_collection.py`。实现前再次冻结 formal root 中两文件的 path/Git blob/raw SHA 与解释器；不匹配即在任何 source open 前 FAIL。

禁止真实 source/checkpoint/cache I/O、authority-root materialization、collection/receipt/source-evidence/publication 写入、网络、child、GPU、torchrun、模型/optimizer/scaler 或训练。

## CPU/static seam

模块只接受 injectable `TemporaryGitFixture`/FD shim；fixture 临时目录不得指向项目 root、source transport、checkpoint 或 cache。fixture 覆盖：authority tuple/parent/path/blob drift、target/base/Gitlink drift、root-FD symlink/escape/non-regular 拒绝、same-FD read/hash/fstat race、single-use handoff、five-path/one-path allowlist、retained snapshot equality、rollback success 与 `ROLLBACK_INCOMPLETE`。所有 fixture source bytes 为测试内小型合成 bytes，测试结束自动清理。

## 静态接口与证据

实现必须只构造 canonical `immutable_source_collection_execution_evidence_v1` 的内存对象并在 tests 验证 exact key set、phase/null-record、snapshot、candidate 与 path contract；不得把临时 fixture 证据发布为真实 artifact。未知字段、path/interpreter/allowlist drift、raw source path/URL/secret 字段、或任何未绑定 authority tuple 都 FAIL。

## 验收

CPU-only 标准库测试必须覆盖上述每个负例与一个无真实 I/O 的 PASS-shaped synthetic record；`py_compile` 与 `git diff --check` PASS。完成后仅可提交并三方审核 CPU/static implementation；仍不授权真实 execution。source-evidence 既有闭合完成后，下一路线固定 single-GPU smoke design。

请求 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_CONTROLLED_EXECUTION_CPU_STATIC` 或 `REQUEST_CHANGES(file:line)`。
