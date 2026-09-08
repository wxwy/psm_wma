# ChatGPT 独立设计复审 — v0.3.9 plan-chain retry

日期：2026-09-08

## Verdict

**APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_CPU_DESIGN**

Gate：`G0-R09-B-TTT-V035-CANONICAL-SEMANTICS-DESIGN`

- Formal root design SHA：`e4b2d2f980ce0f038ae1a44ed379d16bbf05b9d9`
- 实际 root tree child/Gitlink：`80aec090688e3c710c41e1dfd86b6500773db2c7`
- 审核开始远端 V2 HEAD：`96d1be25348c93263422aa9fa10b4428742468b5`，仅 request/bookkeeping，不是 formal target。
- 前序 formal root：`0dcbd5897381ffa4467ad64f300e010d376f9af9`
- 前序 review：`docs/collab/chatgpt/reviews/2026-09-08_R09_B_TTT_v035_canonical_semantics_v038_0dcbd58.md`，review commit `77a5d37913bdfe2db90dbdd5fcf13148361d428f`。

## 增量范围与核验

通过 GitHub connector 核对最新 V2/canonical Inbox、完整 formal root commit、实际 root Git tree、前后 formal target compare 以及 v0.3.9 全文。沿用本会话已实际读取且 compare 证明未变的 v0.3.8/v0.3.7/v0.3.6 继承合同、前序 detailed review、AGENTS 与执行治理技能。

本次 formal commit 仅新增 31 行 v0.3.9 设计并更新 SESSION/TODO；跨 formal pair 的其余改动是既有 review/Inbox bookkeeping。child 无变化，production/test/generated implementation 无变化。独立审核新 pair，不继承旧批准或其他 reviewer 结论。

## Blocker closure

**CLOSED — 前序唯一 MEDIUM：recovery 后续 identity 首次 transient failure 未定义。**

直接证据位于 `docs/build/PSM-WMA_Local_Memory_canonical_training_runtime_contract_v0.3.9.md`：

- 第 15 行：budget 明确归属于 normal plan + 最多一个 suffix recovery 的 plan chain；attempt 不按 identity 重置。
- 第 17–21 行：attempt=1 内任一 member 的 transient，包括此前从未实际 load 的后续 identity，唯一 terminal 为 `LOCAL_MEM_RETRY_EXHAUSTED`；明确禁止 nested recovery/replay/rebind/resample/换 episode。
- 第 23 行：保留成功 fast commits、abort 当前 candidate、清除全部 recovery partial slow gradients、不作 optimizer/LR step、不运行余 member；失败证据包含 chain id、identity、attempt、class、code、fast/scheduler provenance。identity mismatch 与其他既有 failure taxonomy 保持。
- 第 27 行：冻结原反例 A/B/C/D synthetic fixture；A/B chronology/cursor/exposure 保留，C 不提交、D 不执行、slow grads 清空、optimizer/LR 不变，且断言唯一 code、无 nested/第三次 redelivery、plan-chain attempt=1。

第 9 行明确窄范围 supersession；suffix-only membership、GA_effective/N_window、primary/aux objective、完整 recovery 才尝试 slow step、fast-commit-retain/partial-slow-discard 不变。本次未发现新的 contract violation 或 scope 越界。

当前 blocker：**无**。

## Evidence 与授权边界

这是设计 Gate 的合同与 fixture 规格审核；未运行项目代码/测试，未声称上述 fixture 已实现或通过。实际 CPU behavioral Evidence 由后续独立 Gate 验收。

本 verdict 只批准当前精确 pair 的设计；本 verdict 只关闭当前 Gate 的 ChatGPT 审核，不授权后续 Gate 或生产行为。只有 ChatGPT、MM、DS 对同一 pair 均正式批准，才按冻结 scope 新建下一 CPU/static implementation design；本 review 不替其他 reviewer 宣布 Gate closure。

不授权 child/runtime/packer/trainer 实现、config/optimizer/checkpoint 接线、GPU/CUDA/torchrun、真实 model/data/cache/checkpoint I/O、preflight/staging/record/refreeze/export/compose、训练/评测/推理、P4/P5、B2-T、LIBERO4IN1 或其他后续执行。

Detailed review 与 canonical Inbox 均持久化后才形成正式 verdict；其提交始终属于 bookkeeping，不改变 formal pair。
