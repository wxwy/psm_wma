# PSM-WMA Local Memory v0.3.5 Source-Evidence 闭环受控执行请求设计 v0.2

**日期**：2026-09-13
**状态**：docs-only；待三方审核。
**Gate**：`G0-R09-B-TTT-V035-SOURCE-EVIDENCE-CLOSURE-EXECUTION-REQUEST-DESIGN`

本版替代 v0.1；除本版明确修改外，v0.1 的绑定输入、禁止范围、transaction 重验、rollback/fail-stop 与
真实 I/O/GPU/训练均未获授权等约束保持有效。

## 1. 目的与范围

future request 只能按已批准的 immutable-source authority、collection/receipt、source-evidence
producer/record/receipt、publication verifier 与 root-audit 合同顺序执行。它不把新生成的 post-commit
receipt root 当作已审核 authority，也不直接把 receipt triple 交给 smoke。

本 Gate 仅冻结 future request 的输入、transaction 边界和停止条件；不创建 authority root，不打开真实
source/checkpoint/manifest/data/cache，不写 collection/receipt/record/package/publication，不改 child，不探测
GPU，也不执行训练、评测、推理或 LIBERO4IN1。

## 2. 准入输入

request 仅可由已审核 authority materializer 导出的 immutable input-FD bundle 构造，且 source open 前绑定：

1. approved authority-materializer formal root/child、tool path/blob/raw SHA-256、解释器 identity；
2. execution-authority root 的 parent、两 path、两 blob OID 与 raw SHA-256 的七字段 tuple；
3. target root ref、expected base root、expected child Gitlink 与 approved target-lineage identity；
4. evidence directory pre-existence/allowlist snapshot 与 publication target identity。

缺任一项唯一结果为 `BLOCKED_AUTHORITY_NOT_CLOSED`，零 source open、零 Git mutation、零网络 publication；
不得预填 raw source/path/URL/secret/checkpoint/cache 或 smoke instance 字段。

## 3. 执行顺序及 receipt-root 审核互锁

经后续 exact request-instance 三方审核后，一次 activation 必须按以下顺序运行，失败即停止、不可跳过、
重排或自动重试：

1. materializer 建立并从已提交 tree 重算 execution-authority tuple；
2. collection executor 按 root-FD、same-FD double-hash、one-shot handoff 合同提交五 artifact 与唯一 collection receipt；
3. producer 仅消费已提交 collection receipt，按 record/receipt/witness/publication-verifier 合同生成
   source-evidence formal root，随后生成**其下一独立 receipt root**中的 post-commit receipt；
4. root audit 只从已发布 Git objects 复算 source-evidence formal root、next receipt root、receipt path/blob、
   root tree 与 child Gitlink。

第 4 步 PASS 后 activation 必须停止：不释放 `(receipt_root_revision, receipt_path, receipt_blob_native_oid)`，不构造
smoke request instance。随后必须单独对该 exact receipt root 三方审核，审核绑定
`parent=source-evidence formal root` 以及 exact receipt path/blob identity。仅该独立审核全批准后，receipt triple
才成为后续 `INSTANCE-CONSTRUCTION-AND-REVIEW` Gate 的可消费输入。

所有 transaction live write 前均重验 target ref/base/Gitlink/authority，并在失败时恢复记录的 snapshot；任一
rollback 无法逐项证明即为 `ROLLBACK_INCOMPLETE`。任何 FAIL、BLOCKED、`ROLLBACK_INCOMPLETE` 或 receipt-root
审核未批准均不得产生 accepted authority、publication 或 smoke 输入。

## 4. 验收与禁止

- request 不含未绑定真实输入或 smoke instance；
- activation 成功的唯一产物是待独立审核的 immutable receipt root，不是 smoke authority；
- exact receipt-root 三方批准前，receipt triple 不可导出、不可 materialize、不可进入 smoke；
- 不授权真实 I/O、child 修改、GPU/CUDA/torchrun、训练、评测、推理或 LIBERO4IN1。

## 5. 审核请求

请求最终 verdict：

```text
APPROVE_TO_DESIGN_R09_B_TTT_V035_SOURCE_EVIDENCE_CLOSURE_EXECUTION_REQUEST
```

批准仅允许构造并审核 exact closure request instance；不授权执行该 request 或任何下游运行。
