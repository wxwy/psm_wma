# Stage-1 v1.7 v0.5 pre-C rehearsal and consumer implementation design v3.1

**Gate**：`G0-R09-B-TTT-V035-STAGE1-V17-PRE-C-REHEARSAL-CONSUMER-IMPLEMENTATION-DESIGN-V31`。
**状态**：仅 docs-only remediation。它以用户明确的“所有 future C 风险先在一次 non-consuming pre-C rehearsal 完整暴露”指令，对 v0.5 future construction 的 lifecycle 作窄 refreeze；不授权 implementation、v0.5 construction、consumer 调用或任何下游执行。

## v0.5 lifecycle refreeze

仅就新的、不重叠的 v0.5 pair，覆盖继承自已消费 v1.8/v0.4 authority 的“C 必须在首次 live freshness observation 前开始”边界。替代规则是：`rehearse_v05()` 是唯一允许做 live provenance/freshness observation 的 non-consuming phase；其 PASS 必须密封所有 C 所需对象和最终 bytes。它只在未写入、未调用 consumer、未创建 request pair 的条件下完成，任一失败均为 C 前 fail-close、authority 未消费。

此覆盖不复活、修复或重试 v0.3/v0.4；二者永久禁止作为 descriptor、snapshot、patch、consumer input/output、readback、cleanup、residue 或 evidence 的任何部分。它不改变 one-shot/no-retry：v0.5 C 一旦开始，任何失败仍永久消费 v0.5 的 future construction authority。

## 一次完整 non-consuming rehearsal

`rehearse_v05()` 必须在同一受控 invocation 内、按冻结顺序完成并封存以下全部最终对象：

1. 唯一 host-owned `PatchConsumerV1` capability 的 provider/module/path/blob-SHA/callable/ABI/transport identity；不可复制、不可序列化，拒绝 PATH、动态 import、tool-name lookup 或人工重构。
2. 全部 injected source objects 与 literal binding，最终 canonical `json_raw`、`markdown_raw`、`patch_raw`及唯一 strict-UTF-8 `patch_text`，包括 byte identities、line encoder/inverse witness和 Markdown 五字段 binding。
3. v0.5 exact output-pair absences、six-key environment、`.git`/config、local V2、两条 remote queries、authority ref 与 designated absence paths；全部 raw result、identity、query argv、顺序、allowlist 与 predicate 在此刻冻结，禁止 C 再解析、查询、推断或补全。
4. 不调用 consumer 的 add-only dry-run verifier和已经闭合的 post-write verifier；两者只允许 v0.5 pair，拒绝额外路径、删除或修改。

PASS 只返回同进程、不可复制/序列化的 `SealedPreCPlanV1`；不得写 request/receipt/record/cache。任何 live observation 与 sealed identity 不完整或不相符，均在 C 前终止。

## C 的固定最小序列

收到独立 construction authority 后，`consume_once_v05(plan)` 无条件使用已密封 plan，不做名称解析、路径推断、schema/bytes 生成、模块加载、query 或格式化。其唯一顺序是：

```text
1. freshness snapshot：只比较 plan 预冻结的允许对象与 predicates；不发现新对象。
2. 一次 apply_opaque_v1(plan.capability, plan.descriptor, plan.patch_text)。
3. plan.post_write_verifier 对 v0.5 pair byte-for-byte verify。
4. hard stop，等待 v0.5 exact-pair independent review。
```

任一 freshness mismatch 在调用前停止；`REJECTED_NO_WRITE`、`PARTIAL_OR_UNKNOWN`、readback/identity failure 皆 terminal，禁止第二次调用、清理、补写、repair 或 retry。C 不 materialize。

## 一次性 CPU/static implementation 范围

唯一后续实现应一次性覆盖上述四类 rehearsal 输入、sealed plan、C 的固定 sequence 和全部 fail-close matrix；以纯内存 fake capability/adapter 验证，禁止调用真实 consumer、Git/network/source/data/cache、child 或 CUDA。验收必须显式证明 v0.3/v0.4 不进入任何 allowlist、输入、输出、readback、cleanup 或 evidence。

Requested verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_STAGE1_V17_PRE_C_REHEARSAL_CONSUMER_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
