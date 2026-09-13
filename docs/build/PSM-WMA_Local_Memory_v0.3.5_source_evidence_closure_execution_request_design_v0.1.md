# PSM-WMA Local Memory v0.3.5 Source-Evidence 闭环受控执行请求设计 v0.1

**日期**：2026-09-13
**状态**：docs-only；待三方审核。
**Gate**：`G0-R09-B-TTT-V035-SOURCE-EVIDENCE-CLOSURE-EXECUTION-REQUEST-DESIGN`

## 1. 目的与范围收敛

这是进入 single-GPU smoke 前唯一尚未完成的 source-evidence 闭环请求设计。它不再新增任何横向
provenance 子 Gate：后续只有一份受控 execution request，按既批准的 immutable-source authority、
collection/receipt、source-evidence producer/record/receipt、publication verifier 与 root audit 合同顺序
完成或 fail-stop。成功才提供 smoke request instance 所要求的 post-commit receipt。

本 Gate 只冻结该 future request 的输入、transaction 边界、输出和停止条件；不创建 authority root，
不打开 source/checkpoint/manifest/data/cache，不写 collection/receipt/record/package/publication，不改 child，
不探测 GPU，也不执行训练、评测、推理或 LIBERO4IN1。

## 2. 单次 request 的准入输入

future request 只能由已审核的 immutable-source authority materializer 导出的 immutable input-FD bundle
构造；不得由工作树扫描、环境变量、默认路径、stdin、缓存或调用者 digest 补齐。request 在 source open
前必须绑定下列不可变身份：

1. approved authority-materializer formal root/child、tool path/blob/raw SHA-256、解释器 identity；
2. execution-authority root 的 parent、两 path、两 blob OID 与 raw SHA-256 的七字段 tuple；
3. 目标 root ref、expected base root、expected child Gitlink 与 approved target-lineage identity；
4. 受控 evidence directory 的 pre-existence/allowlist snapshot，以及 publication target identity。

缺任一项，唯一结果为 `BLOCKED_AUTHORITY_NOT_CLOSED`，且零 source open、零 Git mutation、零网络
publication。request 不得提前填入 source raw bytes、source path、URL、secret、checkpoint bytes、cache bytes
或 smoke instance 字段。

## 3. 固定执行顺序与不可合并的停止点

通过后续独立审核的 request 必须以单 activation 完成下列顺序，任何失败立即停止；不得跳过、重排、
自动重试或把部分结果交给 smoke：

1. materializer 用绑定输入建立 execution-authority root，并从已提交 tree 重算其 parent/path/blob/raw-byte
   tuple；
2. collection executor 在 root-FD、same-FD double-hash 与 one-shot handoff 合同下，preflight 后只提交五个
   collection artifact，再只从 collection tree 提交唯一 collection receipt；
3. source-evidence producer 只消费已提交 collection receipt，通过既批准 record/receipt/witness 及
   publication verifier 形成 post-commit receipt；
4. root audit 仅从已发布 Git objects 复算 post-commit receipt、root tree 与 child Gitlink。只有此步 PASS
   才可将 `(receipt_root_revision, receipt_path, receipt_blob_native_oid)` 作为后续 smoke instance Gate 的
   输入。

每个 transaction 都必须在 live write 前重验 target ref/base/Gitlink/authority；失败时恢复其已记录 snapshot。
任一 rollback 不能逐项证明时终态必须为 `ROLLBACK_INCOMPLETE`。任何 FAIL、BLOCKED 或
`ROLLBACK_INCOMPLETE` 都不得产生 accepted authority、publication 或 smoke 输入。

## 4. 输出、验收与明确禁止

未来 execution PASS 的唯一下游交接是 immutable Git blob 中的 post-commit source-evidence receipt；它必须
能导出 smoke ABI 所需十字段 `authority_tuple`，并与 receipt root tree、child Gitlink、五 collection artifact
和 canonical model-config digest exact match。execution evidence 仅记录 approved identity、阶段、transaction
identity、digest、状态与 rollback 事实；不得记录 raw source bytes、秘密、路径或 URL。

本设计的验收是：

- request 不含未绑定真实输入或 smoke instance；
- 每个阶段均有 pre-bind、post-commit lookup 与 fail-stop 条件；
- 成功只释放 receipt triple，下一步仅为已批准的 `INSTANCE-CONSTRUCTION-AND-REVIEW` Gate；
- 失败不释放任何 authority，也不进入 GPU。

即使本设计获批，仍须先对 exact request instance 进行三方审核，才可执行一次 source-evidence 闭环；
该 request 也不授权 single-GPU smoke、CUDA、torchrun 或训练。

## 5. 审核请求

请求最终 verdict：

```text
APPROVE_TO_DESIGN_R09_B_TTT_V035_SOURCE_EVIDENCE_CLOSURE_EXECUTION_REQUEST
```

或 `REQUEST_CHANGES(file:line)`。批准仅允许后续独立 Gate 构造并审核一份 exact source-evidence closure
execution request；不授权执行该 request、真实 I/O、child/GPU/训练。
