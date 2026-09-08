# ChatGPT 独立设计审核 — v0.3.8 recovery plan

日期：2026-09-08

## Verdict

**REQUEST_CHANGES**

Gate：`G0-R09-B-TTT-V035-CANONICAL-SEMANTICS-DESIGN`

- Formal root design SHA：`0dcbd5897381ffa4467ad64f300e010d376f9af9`
- 实际 root tree 的 child/Gitlink：`80aec090688e3c710c41e1dfd86b6500773db2c7`
- 开始时远端 V2 HEAD：`0069b8d87e069f55567388850e32ece91d34cab9`（status/bookkeeping，不是 formal target）
- 前一同 Gate formal root：`b912aab3f9607319d383cee6507796df90cc4130`
- 前序 ChatGPT review：`docs/collab/chatgpt/reviews/2026-09-08_R09_B_TTT_v035_canonical_semantics_v037_b912aab.md`

本次对新 pair 独立 fresh review，不继承上一 SHA 或 MM/DS 的批准。

## 核查范围与证据

读取最新 canonical Inbox、formal commit 实际 diff、上一 formal target 至本 target 的 compare、root Git tree、v0.3.8 全文、直接继承的 v0.3.7/v0.3.6 合同、前一同 Gate ChatGPT review，以及 AGENTS 和执行治理技能。

formal commit 只新增 v0.3.8 并更新 SESSION/TODO；跨 formal pair 的其余改动为 Inbox/prior review bookkeeping。child Gitlink 无变化，无 production/test 修改。本轮是设计合同静态审核，未运行项目代码、测试、GPU 或真实 I/O；以下不是 production bug 判定，也不宣称 CPU fixtures 已执行。

## 增量 closure

- **CLOSED（保持）**：v0.3.6 的 partial GA-window slow gradients / fast chronology 原 HIGH；immutable planned count、actual==planned、保留已提交 fast chronology、丢弃 partial slow window、不 replay 的约束保持。
- **CLOSED（本轮独立核对）**：recovery members 恰为失败快照的未提交 suffix，不追加 admission；GA_effective 与 N_window 只统计 suffix；primary/aux 系数明确；完整 recovery 后只尝试一次 slow step，skip 不推进 slow optimizer/LR，随后恢复普通 GA。
- 新版本第 3–5 行无旧版 trailing whitespace；未要求修改被冻结的旧文件。
- retry taxonomy 已补充，但仍有下列一个未覆盖状态。

## 当前 blocker

### NEW — MEDIUM — recovery 内另一 identity 首次 transient failure 未定义

**file:line**：`docs/build/PSM-WMA_Local_Memory_canonical_training_runtime_contract_v0.3.8.md:99`、`:100`；关联 `:68`、`:119`、`:121`。

**根因**：`recovery.attempt=1` 是 plan 级字段；异常表却将 attempt=1 的 transient failure 终止分支限定为“同一 identity 第二次”。recovery suffix 还包含旧 plan 从未执行的后续 identities，它们首次 load 失败时同样处在 attempt=1，但不是同一 identity 第二次失败。表中没有匹配行，也未冻结默认 terminal 分类/代码。现有新增 fixture 仅覆盖原失败 identity 再次失败。

**可达反例**：普通 GA=4，members=[A,B,C,D]；A 成功 backward/commit，B 首次 LOAD_DECODE_TRANSIENT，recovery=[B,C,D]、attempt=1。B 重送成功并 commit；C 在第一次实际 load 时发生同 digest 的 LOAD_DECODE_TRANSIENT。它既不满足第 99 行 attempt=0，也不满足第 100 行“同一 identity 第二次”。因此此时的终止码及预算归属无法由合同唯一确定。

**违反合同**：v0.3.8 §3 唯一 recovery plan/attempt=1 与 §4 明确冻结异常 taxonomy、retry budget、终止码以消除实现前可观察差异的要求；继承 v0.3.7 §3 的有限、确定性、fail-closed 失败处理不能替代本版缺失的具体分支。此 finding 不主张必须允许第二层 recovery。

**可验收修复条件**：明确 retry budget 是 plan-chain 级还是 identity 级，并对 recovery 中每种 LOAD_DECODE_TRANSIENT（包括后续 identity 首次失败）给出唯一处理和 terminal code，保持现有 suffix-only/no-replay/fast-commit-retain/partial-slow-discard 不变量。补充上述 A/B/C/D 类 CPU/static acceptance fixture，断言已提交 A/B fast chronology 保留、当前 C candidate 不提交、全部 partial slow grads 清空、optimizer/LR 不 step、D 不执行，并验证明确的 terminal code 和 retry 上界。这里只冻结设计与验收条件，不授权现在实现或运行测试。

## Gate 与落盘边界

本 pair 仍有 1 个 MEDIUM design blocker，不能关闭当前 Gate，也不授权下一 CPU/static implementation design。禁止 child/runtime/packer/trainer 修改、GPU/CUDA/torchrun、真实 model/data/cache/checkpoint I/O、训练/评测/推理、P4/P5、B2-T、LIBERO4IN1 及后续 Gate。

本详细 review 与 canonical Inbox entry 均完成后才形成正式 verdict；review/Inbox commit 不改变上述 formal pair。
