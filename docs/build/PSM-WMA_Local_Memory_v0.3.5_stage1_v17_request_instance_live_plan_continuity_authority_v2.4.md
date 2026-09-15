# Stage-1 v1.7 live-plan continuity authority v2.4

**Gate**：`G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-LIVE-PLAN-CONTINUITY-AUTHORITY-V24`。
**状态**：docs-only；收敛 V23 同实例连续性 HIGH。

## 唯一模型

一次真实 non-consuming pre-C 在一个 host-owned session 内创建唯一、不可复制的 `SealedPreCPlanV1` 与唯一 opaque continuation lease。session、plan、lease 的三元 identity 在创建时以不可变 object token 成对绑定；它们同生共灭。pre-C 不调用 consumer、不写任何 request/receipt/cache/sidecar/evidence 路径。

plan 的 exact review record 必须同时列出：session identity、plan identity、lease identity、三者的绑定 digest；PatchConsumerV1/FreshnessGuardV1/verifier 的 provider/module/path/source-blob/callable/ABI/transport；sealed pair/patch bytes identity、C01--C15、九条 freshness identity、two paths、six-key environment、remote facts 和 designated absences。record 只读，不能作为重建输入。

## review-pending 与恢复

审核期间 host session 只能保持三元组 quiescent：lease 不暴露 consumer，plan 不接受 mutation/rebind/copy/serialize，任何普通 resume 或直接 `consume_once_v05` 入口均拒绝。三方 exact-plan approval 只能由唯一 resume-only entrypoint 接收该 live lease；它先证明 session/plan/lease identities 与review record完全相等，才把同一个内存 plan 传入 C。

process death、session/handle/lease loss、plan replacement、任何 identity drift、无法证明 binding、或任何 C 前异常，均永久使该 authority invalid。禁止从 review record 或 literals reconstruct/import/resolve/deserialize 新 plan；重新尝试只能以新的 non-consuming pre-C、新 record 和新的三方 exact-plan review 开始。

## future C（本 Gate 不授权）

在同一 live plan verified resume 后，C 仍仅为：`FRESH guard → one opaque apply → exact byte readback → hard stop`。C 不做名称解析、import、query、bytes/path 生成或对象替换；call 后任一失败消费 authority且禁止 retry/repair/cleanup/second call。

## 请求 verdict

本 Gate 只请求批准上述 live-plan continuity model 的后续 exact-plan pre-C authority design；不授权真实 pre-C、C、request pair、materialization/source-evidence、child/runtime/config、GPU/CUDA/torchrun、训练/评测/推理/LIBERO4IN1。

Requested verdict: `APPROVE_TO_DESIGN_R09_B_TTT_V035_STAGE1_V17_LIVE_PLAN_CONTINUITY` or `REQUEST_CHANGES(file:line)`.
