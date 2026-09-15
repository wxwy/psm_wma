# Stage-1 v1.7 v0.5 pre-C rehearsal and consumer implementation design v3.0

**Gate**：`G0-R09-B-TTT-V035-STAGE1-V17-PRE-C-REHEARSAL-CONSUMER-IMPLEMENTATION-DESIGN`。
**状态**：仅 docs-only implementation design。它把后续 construction 的所有可失败解析、canonicalization、identity、path 和 consumer 条件收敛到一次 non-consuming rehearsal；不创建 v0.5 pair，不进入 C。

## 单一收敛原则

future C 不再解析名称、查找 callable、推断路径、导入模块、补全 schema、生成格式或重新计算任何 request bytes。所有这些工作只能在 C 前的 `rehearse_v05()` 一次完成并密封为不可复制的 `SealedPreCPlanV1`；其任何失败都在 C 前停止且不消费 authority。只有已密封计划可进入 C，C 的固定序列仅为：

```text
freshness snapshot against sealed plan → one opaque add-only write → byte-for-byte verify → hard stop
```

本设计替代继续拆分 path、字段、patch encoder、bytes/str 或 consumer 名称的串行 Gate；这些均是同一 rehearsal 的验收项。

## `rehearse_v05()` 的完整 non-consuming 输入与产物

rehearsal 只接受显式 injected inputs：冻结的 Stage-1 source-object set、完整 literal `ReplayBinding`、v0.5 output tuple、six-key environment、orchestration capability registry 和只读 snapshot adapters。它不得接受 PATH、ambient import、stdout、临时文件或人工字符串作为输入。

在不创建输出、不会调用 consumer 的前提下，它必须一次性完成并将每项 raw bytes/length/SHA-256、顺序和失败原因写入内存 `SealedPreCPlanV1`：

1. 解析唯一 host-owned `PatchConsumerV1` capability，并冻结 `provider_id`、`module_id`、`module_path`、module blob SHA-256、`callable_qualname`、ABI、ordered add-only v0.5 paths 与 `opaque-patch-text-handoff/v1` transport。capability 必须不可复制、不可序列化；解析或 ABI 不一致即 fail-close。
2. 对被冻结的对象完成 P0/P1-equivalent injected-byte replay，生成最终 canonical `json_raw`、`markdown_raw`、`patch_raw` 和一次 strict UTF-8 `patch_text`；冻结四者 identity，执行 line encoder/inverse witness，并验证 Markdown 五字段 sibling binding。C 不得再格式化或转换。
3. 读取并冻结 v0.5 两输出路径的 exact absence、six-key environment、`.git`/config、local V2、两条 remote V2/authority-ref query、designated absence paths和全部 required raw results；所有路径和 query 均须为显式 ordered allowlist，禁止在 C 推断。
4. 用**不调用 consumer 的 dry-run identity verifier**验证计划中 `patch_text` 对应的仅两条 add-file operation、无额外路径、无删除/修改；并构造 post-write verifier closure。该 verifier 只能读取两条 v0.5 paths、逐字比较 sealed raws、重序列化 JSON 并核验五字段 binding。

rehearsal PASS 只返回同进程内 opaque `SealedPreCPlanV1`，不得写 request pair、receipt、record 或 cache。任一项目失败、不完整、identity drift、额外 I/O 或 capability 不可验证均 C 前失败，永不消费 one-shot authority。

## C 的最小执行 ABI

`consume_once_v05(plan: SealedPreCPlanV1)` 首先只重做由 plan 定义的 freshness snapshot；它只比较已经冻结的对象、raw identities、absence predicates和capability identity，不能重新解析或选择任何值。比较失败则 terminal、零 consumer invocation。

比较 PASS 后，它在同一个 orchestration call 把 plan 保存的**同一不可变** `patch_text` object 交给 plan 保存的 capability：

```text
apply_opaque_v1(plan.capability, plan.descriptor, plan.patch_text) -> ApplyResultV1
```

调用次数严格为一。`APPLIED` 才执行已密封 post-write verifier；`REJECTED_NO_WRITE`、`PARTIAL_OR_UNKNOWN`、identity mismatch 或 verifier failure 全部 terminal、无清理、无第二次调用、无补写/repair/retry。PASS 后硬停，等待 v0.5 exact-pair 独立审核；不 materialize。

## 计划中的 CPU/static implementation

后续唯一 implementation 一次性新增 root-only stdlib rehearsal module 与 CPU tests，覆盖：capability descriptor/callable identity drift、复制/序列化拒绝、全部 injected source/remote/environment/absence identity drift、canonical bytes/line witness、v0.5 path allowlist、consumer dry-run、sealed-plan immutability、freshness mismatch 零调用，以及三类 terminal result。tests 可用纯内存 fake capability，绝不调用真实 `apply_patch`、Git/network/remote/source/data/cache、child 或 CUDA。

本版不授权该 implementation、v0.5 construction、P0/P1/C、consumer invocation、materialization、source-evidence、child/runtime/config mutation、GPU/CUDA/torchrun、训练、评测、推理或 LIBERO4IN1。

Requested verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_STAGE1_V17_PRE_C_REHEARSAL_CONSUMER_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
