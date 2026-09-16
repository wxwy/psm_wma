# Source-evidence Production Entrypoints 实现设计 v0.1

**Gate**：`G0-R09-B-TTT-V035-SOURCE-EVIDENCE-PRODUCTION-ENTRYPOINTS-IMPLEMENTATION-DESIGN`
**状态**：docs-only；仅请求 CPU/static implementation 授权。

## 1. 目的与前置

本设计回应 `source_evidence_closure_execution_request_design_v0.3` §1 的 HIGH-1：Stage-2
source-evidence closure 的 exact request 只能在 source-evidence producer / record / receipt / root-audit
production entrypoints 已另行实现并关闭后构造。当前 `tools/psm_wma/immutable_source_collection.py` 只提供了：

- producer/closure 的 library helper：`produce_source_evidence_record`、`verify_source_evidence_record`、
  `produce_source_package`、`produce_source_closure`、`verify_source_package_and_witness`；
- collection executor 的单一 production 入口 `main()`（collection → receipt → candidate commit）。

四个 source-evidence production entrypoint 尚未作为可独立执行的入口存在，因此不能把仅有的 collection
executor 伪称为 v0.3 要求的全 transaction entrypoint 集合。

本设计把已关闭的 library helper 与 `collect_synthetic` 内的 receipt / commit / post-check seam 提升为四个
最小 production entrypoint，均通过 argv 子命令分派，任一绑定缺失即 fail-closed。本设计只授权
CPU/static 实现与 stdlib 测试，不授权接线、真实 source/checkpoint/manifest/data/cache I/O、record 写入、
publication、child/runtime 修改、GPU、CUDA、torchrun、训练、评测或推理。

## 2. 范围

只修改 `tools/psm_wma/immutable_source_collection.py` 与其对应单元测试；不修改 Cosmos 子模块、训练入口、
配置、数据集或缓存。

## 3. 四个 production entrypoint 合同

四个 entrypoint 不新增 source I/O 或 Git mutation 能力，只把已存在的能力接成独立入口；每个入口只完成其
阶段并 fail-closed 返回，接线顺序（collection → producer → receipt root → root audit）留给后续 Stage-2
execution request Gate。

### 3.1 producer

- 复用 `produce_source_evidence_record` 与 `produce_source_closure`。
- 输入（全部来自 argv + FD）：receipt mapping（canonical JSON FD）、config_raw、descriptor_raw、
  `formal_root`、`child_gitlink`、record_raw。
- 输出：一次性 `SourceEvidenceHandoff`（package / witness canonical bytes）；不得序列化或从路径重读。

### 3.2 record

- 复用 `NativeCollectionGit.commit` / `lookup` 底层 seam；把 producer 输出的 source-evidence record raw
  bytes 写入冻结路径 `SOURCE_RECORD_PATH`，提交到目标 Git tree。
- 输入：已验证 receipt + record_raw + Git 事务 + 目标 parent revision。
- 输出：`{revision, tree_native_oid, blob_native_oid}`；提交失败时 rollback 到 preflight 前快照。

### 3.3 receipt

- 复用 `_receipt_from_collection`。
- 输入：collection revision + blobs + Git 事务。
- 输出：canonical collection receipt mapping（仅内存返回，不回写、不 push）。

### 3.4 root-audit

- 复用 `verify_source_package_and_witness` 与 `collect_synthetic` 的 post-check seam；不包含 push/publication。
- 输入：package_raw / witness_raw / receipt / config_raw / descriptor_raw / `formal_root` / `child_gitlink` /
  record_raw + publication state。
- 输出：audit verdict（PASS/FAIL）；任何 publication 状态为真即 `BLOCKED_PUBLICATION_FORBIDDEN`。

## 4. argv 分派与 fail-closed

- `main()` 扩展为子命令分派：`--entrypoint {producer,record,receipt,root-audit}`；缺省保持现有 collection
  行为不变，不改变已关闭 executor 的 argv grammar。
- 每个子命令拥有独立 argv grammar；所有 hex identity 经与 `_native_binding` 同款的 lowercase 40/64-hex 校验。
- 任一绑定缺失、过期或漂移 → `BLOCKED_AUTHORITY_NOT_CLOSED`，零 mutation。

## 5. 最小验收

- 覆盖四个 entrypoint 的 canonical round-trip、exact key/schema、缺字段/错误大小写/错误 digest/路径与
  ref 注入的 fail-closed 负例。
- `/opt/conda/bin/python3 -m unittest tools.psm_wma.test_immutable_source_collection -q` 及新增定向测试全部 PASS。
- 目标文件 `py_compile` 与根仓库 `git diff --check` PASS。

## 6. 禁止范围与后续顺序

本设计不接线四个 entrypoint、不构造 Stage-2 request instance、不运行真实 collection/record/publication、
不生成 receipt root、不启动 single-GPU smoke 或 LIBERO4IN1 训练。顺序固定为：本设计审核 →
CPU/static implementation → implementation closure 审核 → fresh Stage-2 request instance construction/review →
一次受控 source-evidence closure → receipt-root review → smoke/训练 Gate。

## 7. 审核请求

请求 verdict：

```text
APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_SOURCE_EVIDENCE_PRODUCTION_ENTRYPOINTS_CPU_STATIC
```

或 `REQUEST_CHANGES(file:line)`。
