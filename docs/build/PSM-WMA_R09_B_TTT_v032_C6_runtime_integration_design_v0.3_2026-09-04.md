# PSM-WMA R09-B TTT v0.3.2 C6 runtime integration design v0.3

**状态**：v0.2 superseded；仅修正 reset/done 状态机歧义，其他条款逐字继承 v0.2。待三方同 SHA 设计审核；不授权实现、生产接线、GPU 或训练。

权威基线：`docs/build/PSM-WMA_R09_B_TTT_v032_C6_runtime_integration_design_v0.2_2026-09-04.md`。v0.2 的 test-only synthetic adapter、直接委托 `C5AOwnerSegmentCPU`/`AdmissionAuthority`、整段 materialize/backward/commit、segment loss、owner/source/epoch 字段、Memory Prefix 形状、禁止范围和验收矩阵全部保持不变。

## 唯一修正：reset/done 的 pending 规则

C6 adapter 必须直接委托 C5A 的以下确定性转换，不允许自动 abort：

1. `reset(owner)` 或 `done(owner)` 在存在 pending transaction（任意 `COLLECT_RAW` 或 `MATERIALIZED_PENDING`/`BACKWARD_OK`）时**立即拒绝**，不改变 phase、fast state、committed replay、reverse index 或 epoch；该拒绝路径不得产生新 epoch。
2. 调用方若要放弃 pending segment，必须先显式 `abort(owner)`；abort 后再调用 `reset(owner)`/`done(owner)`，成功 reset 才清理 owner state/replay/index 并将 epoch 加一。
3. 无 pending 时，`done(owner)` 与 `reset(owner)` 等价，均执行上述成功 reset；同 owner/source identity/timestep 只能在新 epoch 取得新 capability 后重新 admission。旧 epoch capability 必须 fail-before-C5。
4. terminal `r=0` 仅表示没有 pending rows 的空段关闭；不得把有 pending rows 的 segment 隐式当作 `r=0`，也不得绕过显式 abort/backward 规则。

## 新增验收

synthetic adapter tests 必须直接覆盖：pending 各 phase 调用 reset/done 均 fail 且五类快照与 epoch 不变；显式 abort→reset 成功且 epoch 恰增一；新 epoch 同逻辑键/变更源字节重新 admission；无 pending 的 done/reset 等价；terminal `r=0` 不调用 backward。该 fixture 与 v0.2 继承的 C5A 36 项矩阵一并作为 C6 implementation closure 前置条件。

除此修正外，C6 仍是 test-only synthetic adapter Gate；production Cosmos path、config/optimizer/checkpoint refreeze、GPU/CUDA/torchrun、真实 I/O、P4/P5、B2-T、训练/评测/推理和 LIBERO4IN1 均禁止。
