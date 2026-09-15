# Stage-1 v1.7 request-instance recovery design v2.0

**Gate**：`G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-RECOVERY-DESIGN-V20`。
**状态**：docs-only；它不执行 pre-C、C、request pair 写入或任何下游操作。

## 1. 不可回退的历史与唯一目标

v1.8 的 C 已永久消费且零输出；不得重试、补写、清理或复用其 authority。C995 已关闭纯内存 `ContractV05` CPU/static Gate，但不授权真实 I/O 或 construction。

V20 的唯一目标是为**一份新的 future v0.5 pair**定义一次可审核的 construction authority：在 C 前完成全部 non-consuming pre-C rehearsal；C 仅提交已冻结的 pair。不得为路径、字段、bytes/str 或 consumer 名称再开横向 Gate。

## 2. 冻结对象与 capability ABI

pre-C 使用 C995 的 `ContractV05`/C01--C15 作为完整 typed truth。其 live observation 只允许发生在 pre-C，并被封存为不可复制/序列化的 plan；固定 literal 必须等于 Contract 的 authority，而 live raw observation 只能在 C freshness 时与封存值完全相等。

future host 仅可注入一个 `PatchConsumerV1` opaque capability，字段必须在 pre-C 精确验证：

```text
provider, module, path, blob_sha256, callable_qualname, abi,
transport, apply_opaque_v1(descriptor, patch_text) -> outcome
```

它不是 PATH 名称、动态 import、shell executable、临时文件或字符串工具查找。`patch_text` 必须是 producer 的同一 strict-UTF-8 object；capability 不可复制、不可序列化、不可替换。预期结果只能是 `APPLIED`、`REJECTED_NO_WRITE`、`PARTIAL_OR_UNKNOWN`；后两者以及异常均为终态。

## 3. 一次完整 non-consuming pre-C rehearsal

在未消费 authority、未调用 capability、未写任何 future output 前，单次 pre-C 必须按下列顺序完成并失败即停止：

1. 验证 injected capability ABI/identity，并执行纯内存 no-call probe；不可用即 pre-C fail-close。
2. 以 `ContractV05` 精确验证 C01--C15，获得同轮 `.git`/config/local-V2、两条查询、authority-ref absence、output/designated absence、six-key environment 与 targets 的 typed snapshot。
3. 使用已封存 P0/P1、literal ReplayBinding 和 canonical producer 生成唯一 JSON bytes、Markdown bytes、patch bytes 与同一 `patch_text`；验证 UTF-8、line inverse、add-only、五字段 Markdown 及所有 byte identities。
4. 在内存模拟 capability 结果与 post-write byte-for-byte readback；不得创建 request、record、receipt、cache 或临时文件。
5. 返回唯一 `SealedPreCPlanV1`，其中包含 capability、descriptor、canonical pair、typed closure、post-write verifier 和 freshness identity；其可观察内容以 C995 matrix 为唯一依据。

pre-C PASS 的证据必须同时列出 C01--C15 的 exact expected、同轮 live identity、正向结果及 foreign-but-self-consistent fail-close matrix。任何遗漏均阻止 C，而不是在 C 中补充。

## 4. C 的最小原子事务

独立 construction authority 到位后，C 严格且仅严格执行：

```text
freshness snapshot equality
→ one apply_opaque_v1(descriptor, sealed patch_text)
→ byte-for-byte post-write readback of exact pair
→ hard stop pending independent review
```

C 内禁止 capability/name/path/schema/import/query/patch/identity 决策或格式生成。freshness mismatch 在 call 前终止；任何 call 后的异常、拒绝、partial 或 readback 不符均消费该 authority、禁止 retry、repair、cleanup 或第二次 call。

## 5. request 输出与停止边界

唯一允许的 future outputs 是 `ContractV05.descriptor.paths` 的 JSON/Markdown pair；输出存在前、读回后及 residual path 判据均必须是 pre-C 已封存的 exact paths。C 成功也只产生 request-pair 候选，必须 hard stop 等待独立 pair review；它不授权 materialization、source-evidence、child mutation、GPU、训练、评测、推理或 LIBERO4IN1。

## 6. V20 设计验收

- C995 `ContractV05` C01--C15 全部可逐项映射到本设计的 pre-C/C动作；
- capability ABI 与失败终态在 C 前已冻结，没有 ambient PATH 或 runtime discovery；
- pre-C 覆盖未来 C 会消费的全部对象/bytes/callable/paths/environment/snapshot/readback；
- C 只有四步且无设计决策；
- 纯 docs/static 核验通过后才可申请三方 `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE`。

Requested verdict: `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE` or `REQUEST_CHANGES(file:line)`.

仍禁止：真实 pre-C/C、request pair、materialization、source-evidence、真实 Git/network/source/data/cache I/O、child/runtime/config mutation、GPU/CUDA/torchrun、训练、评测、推理或 LIBERO4IN1。
