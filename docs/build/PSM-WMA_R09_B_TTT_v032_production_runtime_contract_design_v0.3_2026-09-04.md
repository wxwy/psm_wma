# PSM-WMA R09-B TTT v0.3.2 production runtime contract design v0.3

**状态**：v0.2 superseded；待三方同 SHA 设计审核。仅冻结 production runtime contract，不授权实现、GPU 或训练。
**基线**：v0.2（root `9ff48c8`）及已关闭 C5A/C6 synthetic CPU contracts。

## 1. Authority 与输入合同

沿用 v0.2：唯一 production-safe authority 为 `cosmos_framework/model/generator/mot/runtime_authority.py::ProductionRuntimeAuthority`；C5A/C6 保持 test-only facade 并须与共享 authority 做逐项等价验证。每条 evidence 必须标注 `R08_COMPLETED_CAUSAL`、稳定 owner/epoch、owner-global `source_timestep`、segment/row、valid/done/reset；继承 C5A contiguous-prefix 与所有 fail-before-kernel 规则。

## 2. Segment outer-loss 精确归一化（v0.2 HIGH-1 整改）

对一个 native window 的有效行集合 `I = {t | outer_valid[t] = true}`，先冻结窗口级分母：

```text
N_valid_window = |I|
N_valid_window = 0  =>  no backward, no commit, no optimizer step
```

对该窗口切出的每个 segment `s`，令 `I_s = I ∩ rows(s)`，生产 segment scalar 必须为：

```text
L_segment(s) = sum(t in I_s, L_task[t]) / max(N_valid_window, 1)
```

所有 segment scalar 的和必须数值上等于 native unsliced window loss `sum(t in I, L_task[t]) / N_valid_window`；不得使用独立的 `|I_s|` 分母，除非额外乘以严格等价的 `|I_s|/N_valid_window` 权重。`L_task[t]` 继续使用 Cosmos 原生 vision/action target、mask、time weighting 与 recipe scale。每段只 backward 一次、commit 一次，且只覆盖该段 witness 图；padding/context-only 行不进入分子或分母。

实现 Gate 必须加入 CPU/static fixture：至少两个 segment、valid counts 不相等、含 terminal remainder，逐项比较 unsliced native scalar 与切片 scalar 的值及参数梯度；同时断言零分母禁止 backward/commit/optimizer step。

## 3. 其余运行边界与后续 Gate

训练仍为 one-step evidence、`ttt_tbptt_steps` 默认 16 且可配置、跨 segment 只 carry detached 数值 state；推理仍须在最外层 `inference_mode()` 前完成 W-only update，再以 detached `[B,K_local,32]` 进入 K/V-only Memory Prefix。Local-disabled 必须走公开 bypass、`None` payload、零写/零 state 与独立 no-memory baseline parity。

本设计不授权 active runtime 修改、config/optimizer/checkpoint、真实 I/O、P4/P5、GPU/CUDA/torchrun、训练/评测/推理或 LIBERO4IN1。设计批准后下一 Gate 仅允许共享 authority extraction/facade migration、production adapter 与相邻 CPU/static tests；后续 config/checkpoint、GPU smoke、LIBERO4IN1 matched smoke、正式训练仍分别三方同 SHA 审核。

完整继承条款：v0.2 与 v0.1 设计文档；冲突时以本 v0.3 为准。
