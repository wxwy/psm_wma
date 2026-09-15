# Stage-1 v1.7 request-instance orchestration consumer-capability design v2.1

**Gate**：`G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-CONSUMER-CAPABILITY-DESIGN-V21`。
**状态**：仅 docs-only remediation。v1.8 的 C 和其 v0.4 pair 均为永久终态；本版绝不将 capability ABI 解释为对该终态的补写、修复、完成或重试。

## v2.0 override：future tuple 必须新鲜且不重叠

v2.0 的 pre-C capability probe、opaque same-object handoff、single add-only invocation、三态 result、byte-exact readback 与 terminal no-retry 保持不变。本版只替换其错误的 future output tuple：任何以后独立获批的 construction **只能**面向下列全新 v0.5 pair，不能读取、写入、比较、修复或以任何方式复用 v0.3/v0.4 pair：

```text
docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v0.5.json
docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v0.5.md
```

`v0.4.json` 和 `v0.4.md` 虽经实测 absent，仍属于已消费 C 的 designated outputs；absence 不是重新开放其名称的许可。future C 的 snapshot、descriptor、patch、result、readback 和 evidence 均不得把 v0.4 作为 input、output 或 residue-cleanup target。v0.5 是新的 versioned request tuple，未来需由一个新 formal construction authority 单独指定、三方同pair审核后才能成为 C 的唯一 target；本版本身不授予该 authority。

## C 前 capability probe（保留并重新绑定 v0.5）

future executor 必须在 P0/P1/C 之前从 orchestration host 的显式能力注册表获得不可复制、不可序列化的 `PatchConsumerV1`。不能依赖 shell/PATH、环境、文件路径、Python import、工具名解析或人工复制。probe 唯一输入是 immutable descriptor：

```text
abi = "psm.stage1.request-patch-consumer/v1"
operation = "add_two_exact_files"
paths = (
  "docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v0.5.json",
  "docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v0.5.md",
)
encoding = "utf-8-strict"
transport = "opaque-patch-text-handoff/v1"
```

PASS 只可返回 `Ready(PatchConsumerV1, descriptor)`，且 ABI、operation、ordered paths、encoding、transport 全部逐字相等。probe 不得读写 future outputs、`.git`、environment、refs、remote 或任一 Stage-1 source；不得运行 parser 或 consumer。任何不可用、mismatch、可复制/序列化、I/O 或结果不完整均是 C 前 fail-close，且不得切换 consumer。

## opaque handoff、result 与终态（保留）

在新 construction authority 获批后，producer 在内存生成既有 canonical `patch_raw` 并只作一次 strict UTF-8 conversion 为 `patch_text`；它先验证 byte/text identity，再在同一个 orchestration call 中执行：

```text
apply_opaque_v1(PatchConsumerV1, DescriptorV1, OpaquePatchTextV1(patch_text)) -> ApplyResultV1
```

payload 是 producer 的同一不可变 object；coordinator、日志、stdout、shell、临时文件、Python 文件 API 和 project subprocess 均不能读取或重构它。host-owned consumer 可内部调用 orchestration-level `apply_patch`，但不向 project 层暴露 tool handle，且不能以 executable 名称解析代替 capability。consumer 只可把 payload 解释为 add-only patch，且只准新增 descriptor 的两个 v0.5 有序路径；不得读、写、枚举其他路径，不得访问 network/Git/environment/child，也不得重试。

`ApplyResultV1` 必须逐项携带 ABI、descriptor equality、invocation count 与两个 v0.5 path 状态：`APPLIED`（恰一调用且两 add 成功）才允许逐字 readback v0.5；`REJECTED_NO_WRITE` 或 `PARTIAL_OR_UNKNOWN` 均是 terminal fail。`APPLIED` 后仍须逐字比较 producer raws、重序列化 JSON、核验 Markdown 五字段 sibling binding。任何 identity/readback/partial failure 都禁止 second invocation、清理、补写或再次 construction。

## 静态验收与禁止项

后续 implementation design 必须证明 descriptor 只含 v0.5 pair；v0.3/v0.4 不出现在它的 allowlist、consumer input、output、readback 或 cleanup 逻辑中；probe 无 I/O；capability 不可复制/序列化；payload 一次 conversion、same-object handoff、single invocation、result 穷尽和 no-retry 都可静态验证。host 未提供 `opaque-patch-text-handoff/v1` 时必须在 C 前停止。

本版不创建或调用 consumer，不执行 P0/P1/C，不创建 v0.5 pair，不授权 materialization、真实 source/checkpoint/manifest/data/cache I/O、collection/receipt/record/publication、child/runtime/config mutation、GPU/CUDA/torchrun、训练、评测、推理或 LIBERO4IN1。

Requested verdict: `APPROVE_TO_DESIGN_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE_CONSUMER_CAPABILITY_IMPLEMENTATION` or `REQUEST_CHANGES(file:line)`.
