# PSM-WMA R09-B TTT v0.3.2 config/optimizer/checkpoint design v0.1

**状态**：待三方同 SHA 设计审核；仅冻结 selector/config/checkpoint contract，不授权实现、GPU 或训练。
**基线**：production runtime contract implementation closure root `78bb329` / Gitlink `4f857ea`；算法 authority v0.3.2。

## 1. Config identity

Local TTT 的唯一可配置字段为：`ttt_tbptt_steps`（正整数，默认 16，与 RoboTTT 对齐）、`inner_lr`（有限正标量，默认值须在实现测试中固定）与 `K_local`（正整数，首版支持 1/4/8）。`runtime_evidence_steps` 固定为 1，不得由 `local_history_horizon` 隐式替代；history horizon 不是 fast-state reset 条件。配置解析必须拒绝缺字段、错误类型、非有限值、非正值与未知 Local TTT selector。

## 2. Slow parameter selector contract

普通 optimizer 只允许精确选择以下四组 slow parameters：

```text
local_history_runtime.encoder
local_history_runtime.recurrent_backend
local_memory2llm
local_memory_modality_embed
```

`theta_Q/theta_K/theta_V`、slot query bank 与 learned W0 必须在 `recurrent_backend` 下注册并进入 optimizer；fast `W_t` 是 owner runtime state，不是 parameter/buffer。dormant stateless readout 不得被宽泛 `local_history_runtime` selector 误选。实现必须产生 exact parameter inventory/count，并对 selector 交换、遗漏、额外参数和 disabled path 做 fail-closed fixtures。

## 3. Checkpoint contract

模型 checkpoint 必须保存所有 slow parameters（encoder、Q/K/V、slot queries、W0、Local adapter、modality embedding）及其 config identity；不得保存每个 rollout/owner 的 fast `W_t`、pending transaction、epoch、replay/index 或 inference state。恢复必须 strict-load exact selector/config identity：缺失、额外、shape/dtype 不符、`K_local`/`ttt_tbptt_steps`/`inner_lr` 漂移均拒绝；不得静默 warm-start 或沿用旧 B1/旧 TTT authority。

首版只定义 model-level slow checkpoint；sequence-resume 的 fast-state persistence 不是本 Gate 目标，必须另起设计。warm-start 仅允许显式、逐字段、带报告的迁移 fixture，不得成为默认加载路径。

## 4. 验收与禁止范围

CPU/static implementation 必须覆盖 config schema、exact selector inventory、optimizer membership、strict checkpoint round-trip、missing/extra/shape/dtype/config drift、fast-state exclusion、K=1/4/8 与 `ttt_tbptt_steps=1/16`。本设计不授权 active trainer 修改、真实 checkpoint I/O、GPU/CUDA/torchrun、训练/评测/推理、P4/P5 或 LIBERO4IN1；设计批准后下一 Gate 仅允许上述 contract 的 CPU/static implementation，随后仍需独立 GPU smoke、matched smoke 与正式训练审核。
