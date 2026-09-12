# Immutable Source Collection Executor CPU/static implementation 设计 v0.1

**Gate**：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-IMPLEMENTATION-DESIGN`  
**状态**：docs-only；待三方审核。

## 范围

本设计仅将已批准 controlled-execution v0.2 固化为后续 root CPU/static 实现的文件 allowlist、temporary-fixture tests 和 fail-closed interface。唯一 production executor 为 `tools/psm_wma/immutable_source_collection.py`；仅允许新增该文件及 `tools/psm_wma/test_immutable_source_collection.py`。本设计仅冻结两-path allowlist 与 identity derivation rule；具体 path/Git blob/raw SHA/interpreter 在文件存在后的 CPU/static implementation formal root/closure 从 committed tree 绑定。后续 authority materialization/execution approval 只接受该 implementation formal pair，任何 drift 在 source open 前 FAIL；request/ledger/handoff commit 不得替代它。

禁止真实 source/checkpoint/cache I/O、authority-root materialization、collection/receipt/source-evidence/publication 写入、网络、child、GPU、torchrun、模型/optimizer/scaler 或训练。

## CPU/static seam

生产 executor 实现一次 explicit dependency-injection seam：Git transaction、root-FD opener、evidence sink 均以依赖传入，算法/validation/record construction code path 不因 synthetic 或 approved real execution 而改变。CPU/static tests 仅绑定 `TemporaryGitFixture`、FD shim、temporary/in-memory evidence sink；future real execution 仅在审批后以同一未改源码绑定 approved real Git/FD/controlled evidence directory。fixture 临时目录不得指向项目 root、source transport、checkpoint 或 cache。fixture 覆盖：authority tuple/parent/path/blob drift、target/base/Gitlink drift、root-FD symlink/escape/non-regular 拒绝、same-FD read/hash/fstat race、single-use handoff、five-path/one-path allowlist、retained snapshot equality、rollback success 与 `ROLLBACK_INCOMPLETE`。所有 fixture source bytes 为测试内小型合成 bytes，测试结束自动清理。

## 静态接口与证据

实现必须通过 injected evidence sink 输出 canonical `immutable_source_collection_execution_evidence_v1`；CPU/static tests 只使用 temporary/in-memory sink 并验证 exact key set、phase/null-record、snapshot、candidate 与 path contract，不得把 fixture 证据发布为真实 artifact。未知字段、path/interpreter/allowlist drift、raw source path/URL/secret 字段、或任何未绑定 authority tuple 都 FAIL。

## 验收

CPU-only 标准库测试必须覆盖上述每个负例与一个无真实 I/O 的 PASS-shaped synthetic record；`py_compile` 与 `git diff --check` PASS。完成后仅可提交并三方审核 CPU/static implementation；仍不授权真实 execution。source-evidence 既有闭合完成后，下一路线固定 single-GPU smoke design。

请求 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_CONTROLLED_EXECUTION_CPU_STATIC` 或 `REQUEST_CHANGES(file:line)`。
