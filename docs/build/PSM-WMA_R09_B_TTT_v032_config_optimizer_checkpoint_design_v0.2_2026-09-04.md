# PSM-WMA R09-B TTT v0.3.2 config/optimizer/checkpoint design v0.2

**状态**：v0.1 superseded；待三方同 SHA 设计审核。仅冻结 selector/config/checkpoint contract，不授权实现、GPU 或训练。

## 1. 冻结的 config identity

`ttt_tbptt_steps` 为正整数，默认 `16`（与 RoboTTT 对齐）；`inner_lr` 为有限正标量，默认精确冻结为 `0.1`；`K_local` 为正整数，首版支持 `1/4/8`；`runtime_evidence_steps` 固定为 `1`。缺省字段使用上述默认，错误类型、非有限值、非正值、未知字段或旧 B1 selector 一律拒绝。上述四个值都进入 config identity，漂移必须 strict-load 失败。

## 2. 唯一 slow-module owner 与 selector

模型中只能有一个注册的 `nn.Module` owner：`local_history_runtime`。其 `encoder` 与 `recurrent_backend` 子模块必须是 production runtime/authority 实际引用的同一 Python 对象；禁止 adapter 构造副本或从配置重新实例化第二套 trainable Local module。`local_memory2llm` 与 `local_memory_modality_embed` 为其余两个注册对象，四组精确 optimizer selector 为：

```text
local_history_runtime.encoder
local_history_runtime.recurrent_backend
local_memory2llm
local_memory_modality_embed
```

Q/K/V、slot query bank、W0 必须属于 `recurrent_backend`；dormant stateless readout 不得被宽 selector 误选。实现验收必须证明：`named_parameters()` exact inventory/count、runtime 引用对象与 registered module `is` 相同、无重复 trainable Local module，selector 交换/遗漏/额外参数 fail-closed。

## 3. Checkpoint 与 warm-start

checkpoint 保存上述 slow module 参数及 config identity；fast `W_t`、pending、epoch、replay/index、inference state 不保存。strict-load 必须对缺失/额外/shape/dtype/config drift 失败；不得静默 warm-start、旧 authority 迁移或用未注册 runtime 对象恢复。CPU/static 验收必须对同一对象做 round-trip，并验证恢复后 runtime 仍引用该对象；显式 warm-start 只能是逐字段、带报告的另行 fixture。sequence-resume 的 fast-state persistence 另起 Gate。

## 4. 允许范围与后续 Gate

设计批准后下一 Gate 仅允许 config schema、exact selector/inventory、optimizer membership 与 slow-only checkpoint contract 的 CPU/static implementation 及相邻测试；不得修改 active trainer、执行真实 checkpoint I/O、GPU/CUDA/torchrun、训练/评测/推理、P4/P5 或 LIBERO4IN1。后续 GPU smoke、matched smoke 与正式训练各自独立三方同 SHA审核。

完整继承：v0.1 设计文档；冲突时以本 v0.2 为准。
