# Stage-1 v1.7 request-instance recovery design v1.2

**Gate**：`G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-RECOVERY-DESIGN`。
**状态**：仅 docs-only remediation；本版继承 v1.1，且在 future request identity 与 v1.1 冲突时以本版为准。

## v1.1 review remediation

v1.1 已诚实记录 `9c8b4adc71b92caad5ecaf6fb044f5c01a4f9d9a` 的唯一 construction
authority在 P1 后首次 designated-path observation 时零输出耗尽，且禁止 retry。本版不复用、
重启或重新解释该 authority。

DS 的 v1.1 `REQUEST_CHANGES` 指出：future request output pair 虽已冻结，但 future request
formal parent/child 未被显式冻结。下列 tuple 是未来唯一允许写出的 request 的 design literal：

```text
future_request_formal_parent = 08d5828cdb4c12afa3b798ff01826c91ceb8755a
future_request_child_gitlink = 93a89ba61306d840a008813f62f26a34d54850f4
future_request_json = docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v0.3.json
future_request_markdown = docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v0.3.md
```

`future_request_formal_parent`必须逐字等于 v1.0 canonical `ReplayBinding.formal_parent`；
`future_request_child_gitlink`必须逐字等于 v1.0 binding 中 `--child-gitlink` parser value。任何
HEAD、remote V2 advertised SHA、历史 request root、environment 或工作树状态均不得替代或修改
这两个字段。P0 只从这一 formal parent 的三对象 allowlist 获取 injected bytes，P1 只处理其
结果；future request JSON 和 Markdown 均须把该 parent/child tuple 与 P0/P1 identities写入。

## 保持的 v1.1 lifecycle

future output pair 路径是上述设计字面量，既有 v0.1/v0.2 pair 不是输入、模板、候选或输出。
在新的 exact-pair 三方 `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE` 前，
不得进行 P0/P1 或路径发现。

获得该新批准后，P0 的 closed object acquisition 和 P1 injected-byte projection仍为不消费阶段。
C 仍在**第一次** `.git`、config、local-ref、remote-ref、designated-path 或 environment freshness
observation 前开始，随后唯一消费新的 one-shot authority；任何 C 内失败零输出且 no-retry。C 的
same-round zero-mutation snapshot、两条 remote query、absence contract、six-key environment、
owner-FD/replay/closure identities、canonical JSON 与 detached Markdown whole identity，均不弱化。

成功的 C 只写这一个 docs-only v0.3 pair 并硬停以待独立 request review；不得 materialize 或
运行 launcher/materializer。

## 禁止范围与 verdict

本设计/审核不授权 request construction、materialization、launcher/materializer execution、
source/checkpoint/manifest/data/cache I/O、collection/receipt/record/publication、child/runtime/config
mutation、GPU/CUDA/torchrun、training、evaluation、inference 或 LIBERO4IN1。

Requested verdict: `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE` or
`REQUEST_CHANGES(file:line)`.
