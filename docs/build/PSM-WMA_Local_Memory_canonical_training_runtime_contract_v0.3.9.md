# PSM-WMA Temporal Local Memory Canonical Training & Runtime Contract v0.3.9

**日期**：2026-09-08
**状态**：docs-only remediation design；待同一根仓/child SHA 的独立审核；未授权代码、GPU、真实 checkpoint I/O、训练、评测或推理
**当前 child 基线**：`80aec090688e3c710c41e1dfd86b6500773db2c7`

## 1. 目的与继承关系

本文件只替代 `PSM-WMA_Local_Memory_canonical_training_runtime_contract_v0.3.8.md` 的 transient retry budget owner 与对应 fixture。v0.3.8 的 suffix-only recovery membership、`GA_effective`、`N_window`、slow-step 边界、fast chronology retain、partial slow-gradient discard、禁止 replay/rebind/resample 及全部继承合同保持不变。

本版响应 ChatGPT review=`77a5d37` 的 MEDIUM：attempt 是 recovery-plan 级字段，必须覆盖 recovery suffix 内任意 identity 的 transient failure；它不是每个 identity 各有一次 retry budget。本版仅 docs-only。

## 2. 唯一 transient retry budget

retry budget 属于一个 **plan chain**：一个普通 `GAWindowPlan` 和其最多一个 suffix-only recovery plan。普通 plan `attempt=0`；仅该 plan 任一 member 首次同 digest `LOAD_DECODE_TRANSIENT` 可创建 v0.3.8 §3 的唯一 suffix recovery plan，其 `attempt=1`。

`attempt=1` recovery plan 内的**任一** member（包括旧失败 identity 成功后、此前未实际 load 的后续 identity）发生 `LOAD_DECODE_TRANSIENT`，都禁止 nested recovery、replay、rebind、resample 或换 episode，且唯一结果为：

```text
terminal_code = LOCAL_MEM_RETRY_EXHAUSTED
```

identity/digest 不一致仍为 `LOCAL_MEM_IDENTITY_CONTRACT_FAILURE`；numerical、outer、planned/actual failure 的 v0.3.8 taxonomy 不变。`LOCAL_MEM_RETRY_EXHAUSTED` 保留已成功 fast commit，abort 当前 candidate，清空 recovery partial slow `.grad`，不作 slow optimizer/LR step、不运行余 member，并记录 plan-chain id、identity、attempt、class、terminal code 和 fast/scheduler provenance。

## 3. 补充 CPU/static fixture

必须加入 synthetic CPU A/B/C/D fixture：普通 `GA=4` 的 `[A,B,C,D]` 中 A 成功，B 在 `attempt=0` 首次 transient；recovery 为 `[B,C,D]`，B 重送成功，C 在首次 load transient。断言 A/B fast chronology/cursor/exposure 保留且 byte-identical；C 不 commit、D 不运行；slow `.grad` 为零、optimizer/LR iteration 不变；唯一终止码 `LOCAL_MEM_RETRY_EXHAUSTED`；无 nested/第三次 redelivery，记录 attempt 为 plan-chain `1` 而非 C 的 identity-local attempt。

## 4. Gate

本版是 v0.3.9 docs-only remediation 的唯一审阅对象。只有 ChatGPT、MM、DS 对同一根仓 SHA 和 child Gitlink 均正式批准，才授权新建 CPU/static implementation design；实现、真实 I/O、GPU、训练及后续 Gate 仍禁止。
