# Stage-1 v1.7 request-instance orchestration consumer-capability design v2.0

**Gate**：`G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-CONSUMER-CAPABILITY-DESIGN`。
**状态**：仅 docs-only future construction design。v1.8 的单次 C 已消费且零输出；不得补写、修复或重试其 v0.4 pair。

## 目的和唯一授权边界

v1.9 已获同一 formal pair 三方批准，但其批准对象只是在任何新的 construction authority 之前设计一个可验证的 consumer capability。本版因此只定义未来 executor 必须提供的 orchestration ABI；它不创建 request JSON/Markdown，不调用 consumer，不读取 C 的 freshness 输入，也不产生任何 authority、candidate、record、receipt 或 publication 产物。

未来 construction 若获得独立同 pair 三方批准，唯一可能的输出仍是此前冻结的两个 v0.4 路径；该未来授权必须显式引用本版 ABI。没有该独立授权时，所有 P0/P1/C、consumer、输出路径、materialization 和下游动作保持闭锁。

## C 前 capability probe

future executor 必须先以其 orchestration host 的**显式能力注册表**取得一个不可序列化的 `PatchConsumerV1` capability；不能以 shell 命令、PATH、环境变量、文件路径、Python import、工具名称查找或人工复制取得。probe 的输入仅是下列 immutable descriptor：

```text
abi = "psm.stage1.request-patch-consumer/v1"
operation = "add_two_exact_files"
paths = (
  "docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v0.4.json",
  "docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v0.4.md",
)
encoding = "utf-8-strict"
transport = "opaque-patch-text-handoff/v1"
```

probe PASS 的唯一结果是 host 返回 `Ready(PatchConsumerV1, descriptor)`，且 capability 的 ABI、operation、ordered paths、encoding 和 transport 与 descriptor 逐字相等。probe 不得读取未来输出路径、`.git`、environment、refs、remote 或任一 Stage-1 source；不得写入、运行 patch parser 或调用 consumer。任何 unavailable、version mismatch、descriptor mismatch、可序列化/copyable capability、或 probe 有 I/O 的结果均为 **C 前 fail-close**：C 没有开始、authority 未消费、也不得降级为别的 consumer。

## opaque producer-to-consumer handoff ABI

在未来获独立 construction approval 后，C 的 producer 仍在内存按既有 canonicalization、strict UTF-8、line encoder/inverse witness 生成 `patch_raw`，并且只作一次 `patch_text = patch_raw.decode("utf-8", "strict")`。它验证 `patch_text.encode("utf-8") == patch_raw` 和既有 byte/text length/SHA-256 bindings 后，将**同一个不可变 `patch_text` object**连同 descriptor 交给 host：

```text
apply_opaque_v1(
    capability: PatchConsumerV1,
    descriptor: DescriptorV1,
    payload: OpaquePatchTextV1(patch_text),
) -> ApplyResultV1
```

`OpaquePatchTextV1` 只能由 producer 创建并由 `PatchConsumerV1` 消费：coordinator、日志、stdout、shell、临时文件、Python 文件 API 和任何 project subprocess 都不能读取、重编码、转义、拆分、拼接或重新构造其内容。host 必须在**同一 orchestration call**内把 payload 的 object identity 传给其受控 patch consumer；host-owned consumer 可使用 orchestration-level `apply_patch`，但 executor 不得把 tool API handle 暴露为 project 层对象，亦不得以 executable 名称解析替代 capability。该 ABI 的静态实现必须证明 payload 并非由 context/stdout 文本重建。

consumer 只允许把该 payload 解释为一个 add-only patch，且只准新增 descriptor 的两个有序路径；不得删除、修改、读取、枚举或触及其他路径，不得访问 network、Git、environment 或 child/runtime。它不得隐式重试。调用次数为恰一；任何第二次调用，不论第一次是否成功，都是 terminal contract violation。

## result、postcondition 与终态

`ApplyResultV1` 必须是以下三类之一，并有 ABI version、descriptor equality、invocation count 和两条路径的逐项状态：

| result | 含义 | 后续规则 |
|---|---|---|
| `APPLIED` | consumer 报告恰一次调用、恰两项 add 成功 | 仅此时允许 C 读取这两条 designated output 路径并逐字验证既有 JSON/Markdown identity；identity 全过才是 construction PASS。 |
| `REJECTED_NO_WRITE` | 调用未产生两条路径中的任一写入 | C terminal fail，禁止 retry；保留 result 作为终态事实。 |
| `PARTIAL_OR_UNKNOWN` | 一条路径存在、状态不完整、consumer 异常或结果不完整 | C terminal fail，禁止 retry；不得清理、补写、修复或再次调用。 |

`APPLIED` 后的 readback 仍只允许两条 designated output 路径，逐字比较 `json_raw`/`markdown_raw`，重序列化 JSON，核验 Markdown 的 filename、length、SHA-256、canonicalization、prospective blob OID 五字段绑定。readback 任一失败同样 terminal，不授予重试；`apply_patch` 不被假定为原子操作。所有 failure 都不能改写为 v1.8 的补救，也不能导向 materialization。

## 静态验收与禁止项

后续对本设计的 implementation design 至少应静态证明：descriptor 精确常量、probe 不含 I/O、capability 不可复制/序列化、payload 的一次 strict UTF-8 conversion 与 object-identity handoff、single invocation、result 穷尽处理、两条路径 allowlist、无 PATH/shell/Python-write/tempfile/stdout reconstruction，以及 partial residue 的 no-retry 终态。它还必须证明任何 host 不提供 `opaque-patch-text-handoff/v1` 时在 C 前停止。

本版不授权 v0.4 补写或 retry、任何 consumer 实现、P0/P1/C、真实 source/checkpoint/manifest/data/cache I/O、collection/receipt/record/publication、child/runtime/config mutation、GPU/CUDA/torchrun、训练、评测、推理或 LIBERO4IN1。

Requested verdict: `APPROVE_TO_DESIGN_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE_CONSUMER_CAPABILITY_IMPLEMENTATION` or `REQUEST_CHANGES(file:line)`.
