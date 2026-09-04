# PSM-WMA R09-B TTT v0.3.2 production runtime contract design v0.2

**状态**：v0.1 superseded；待三方同 SHA 设计审核。仅冻结 production runtime contract，不授权实现、GPU 或训练。
**基线**：v0.1（root `1e73c00`）及已关闭 C5A/C6 synthetic CPU contracts。

## 1. Authority owner（v0.1 HIGH-1 整改）

生产路径的唯一 chronology/admission/replay/reset authority 必须是新建的 production-safe 共享模块：

```text
cosmos_framework/model/generator/mot/runtime_authority.py
    └─ ProductionRuntimeAuthority
```

该模块承载 C5A 已关闭的 owner epoch、contiguous source timestep、capability authenticity、pending phase、exact-once materialize/backward/commit、abort/reset、replay/index 与 fail-before-work 语义。它是唯一可被 production adapter 调用的 authority；不得在 adapter、trainer 或 inference server 另建 chronology/replay 状态。

`C5AOwnerSegmentCPU` 与 `C6SyntheticRuntimeAdapter` 继续保持 test-only：它们必须改为委托该共享 authority（或由共享 authority 提供等价的 test facade），不得被 production runtime import。实现 Gate 必须提供 C5A/C6 与 production facade 的逐项等价 fixtures，证明没有第二套 divergent authority；未完成 extraction/promotion 与等价证据，不得实现 production adapter。

## 2. 继承的运行合同

除本节 authority owner 修订外，v0.1 全部条款继续有效：每个 causal timestep 只写一组 K/V；更新后 fast state 用 `K_local` 个 Q 读取并输出 `[B,K_local,32]`；输入携带 `R08_COMPLETED_CAUSAL` provenance、稳定 owner key、owner epoch、全局 `source_timestep`、segment/row 坐标、valid/done/reset；C5A contiguous-prefix 规则、skip/duplicate/changed-byte/stale-epoch fail-before-kernel、pending 只能 abort 后 reset 均为强制合同。

## 3. 训练 segment loss 的精确定义

对 segment `s` 的有效行集合 `I_s = {t | outer_valid[t] = true}`，生产 outer loss 必须是该 segment window task loss 的切片：

```text
L_segment(s) = sum(t in I_s, L_task[t]) / max(|I_s|, 1)
```

`L_task[t]` 保持 Cosmos 原生 vision/action target、mask、time weighting 与 recipe scale；padding/context-only 行不进入分子或分母。每段只对该切片 scalar backward 一次并提交一次；`|I_s|=0` 时不 backward、不 commit。该定义与 materialized witness 的 segment 图路径一一对应，不得使用整窗 loss 替代。

## 4. 范围与后续 Gate

本设计仍不授权 active runtime 修改、config/optimizer/checkpoint、真实模型/数据/cache/checkpoint I/O、P4/P5、GPU/CUDA/torchrun、训练/评测/推理或 LIBERO4IN1。设计批准后下一 Gate 只允许实现 `runtime_authority.py`、C5A/C6 facade migration、production adapter 及相邻 CPU/static tests；随后仍需独立 config/checkpoint、GPU smoke、LIBERO4IN1 matched smoke 和正式训练 Gate，均须三方同 SHA 审核。

完整继承条款：`docs/build/PSM-WMA_R09_B_TTT_v032_production_runtime_contract_design_v0.1_2026-09-04.md`。若两版冲突，以本 v0.2 为准。
