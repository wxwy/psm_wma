# R09-B TTT B0 Source Audit v0.1

**状态**：REVIEW；本文件是三方已批准的只读 source audit 产物，不授权实现、CPU contract、runtime、GPU、训练或评测。  
**前置**：`G0-R09-B-RUNBOOK-PREFLIGHT` 已由 ChatGPT/MM/Kimi 批准 `APPROVE_TO_ADVANCE_B0_SOURCE_AUDIT`；整改 root=`e372aa0`，当前审核状态 root=`d8b0e97`，submodule/Gitlink=`c0287e2`。  
**审核请求目标**：本文件冻结 B0 的具体候选；后续必须独立取得三方 `APPROVE_TO_IMPLEMENT_B0` 后才能写任何 TTT 代码或执行 CPU contract。

## 1. 已核验的现有边界

- 当前 temporal compressor 是 `RecurrentLocalMemoryBackend`：其 slow `nn.GRUCell` 位于 `cosmos_framework/model/generator/mot/local_evidence.py:156-200`，`LocalHistoryRuntime` 在 `:202-249` 调用其 `replay`。
- 模型构造仅将该 backend 作为 `recurrent_backend` 外接字段注入，保持 encoder/readout/Local token 维度不变，见 `cosmos_framework/model/generator/omni_mot_model.py:302-313`；实际消费只接受一个 `[B,1,D_local]` token，见 `:990-1002`。
- 默认配置为 `H=16`、`D_e=256`，Local token `D_local=32`，见 `cosmos_framework/configs/base/defaults/model_config.py:300-308` 与 `cosmos_framework/configs/base/experiment/action/posttrain_config/action_policy_libero_edge_all.py:64-69`。
- A1 optimizer selection 精确冻结为 `encoder`、`recurrent_backend`、`local_memory2llm`、`local_memory_modality_embed` 四个 prefix，见 `action_policy_libero_edge_all.py:189-195`；不得增加第五个 key。

## 2. B0 concrete candidate（提案，未实现）

| 字段 | 冻结候选 | 理由与边界 |
| --- | --- | --- |
| `fast_weight_parametrization` | 每 sample/window 的全秩 `W[B,D_local,D_e]`；初始全零、不是 `nn.Parameter` | `D_local=32`、`D_e=256` 与现有 encoder/token 接口相接；没有共享 state。 |
| `update_rule` | 纯 per-sample SGD：`W <- W - 0.1 * grad_W(inner_loss)`；不用 momentum/Adam state | 只保存一个 fast tensor，不引入 optimizer/DCP state。 |
| `inner_objective` | 对每个 valid causal prefix，`MSE(W @ evidence_t, stopgrad(readout(prefix)_token))`；masked/padding 不参与 target、loss 或 update | target 复用现有 `StatelessLocalReplayReadout`（`local_evidence.py:106-153`）且 stop-gradient；不新增 teacher/slow parameter，不修改 native vision/action loss。 |
| `inner_steps` | 每个 replay segment 1 次 SGD update | 与 segment temporal span 解耦，减少 B0 graph/state 复杂度。 |
| `segment_steps` | 4 个有效 causal evidence timesteps；仅沿单 sample/window 的 `H` 轴分段，尾段可短于 4 | 默认 `H=16` 时形成四段；每个 sample/window `state_start=zeros`，绝不跨 outer trainer/policy/control forward carry。 |
| `fast_state_dtype` | `torch.bfloat16` | 与 Local runtime 的 bf16 测试路径兼容；inner loss/gradient 的临时计算可提升到 fp32，但不得持久化为 fast state。 |
| `fast_state_bytes_limit` | 每 sample 16,384 bytes | `32 * 256 * 2`；只计持久 `W`，不把临时 gradient 计为 state。 |
| `slow_learned_parameters` | 零新增 | 新 backend 不得注册 `nn.Parameter`；既有 encoder/readout/adapter 参数、optimizer scope 与 checkpoint contract 不变。 |

最终 token 为每 sample 最后一个 valid evidence 的 `W @ evidence_t`，shape 固定 `[B,1,32]`；all-mask 返回 zero token 且 `present=false`。每个 inner update 只读取/写入本 sample 的 `W`，以禁止跨 sample 的梯度、mask 或 scatter 耦合。

## 3. A/B matched 影响

- 参数量：A 为当前 `GRUCell` 的 slow 参数；B 新增 slow parameter=0，取而代之的是每 sample ephemeral 8,192-element fast `W`，不出现在 `named_parameters()`、optimizer 或 checkpoint。
- 接口：B 保持 `LocalEvidenceEncoder` 输出 `[B,H,256]`、Local token `[B,1,32]`、`present[B]`、history schema、单 Local token budget 和 `recurrent_backend` 外接字段不变。
- 训练：B 的 inner loss 与 native vision/action loss 隔离；B 不改变 A1 四个 optimizer prefix，也不新增 fifth key。任何未来 nonzero slow parameter 必须列出 exact name/count 并重新申请三方豁免。
- 数值：CPU contract 的 deterministic、two-segment state/token/present equivalence 统一要求 `tolerance=0.0`；full replay 必须按相同 4-step segment 切分，避免因不同 update 次序引入差异。

## 4. 拟议实现与 CPU 测试锚点（未创建）

- 实现锚点：在 `cosmos_framework/model/generator/mot/local_evidence.py:156-200` 的现有 backend 位置新增独立 `TTTLocalMemoryBackend`，实现 `initial_state`/`replay`/`reset_mask` 的同形接口；`LocalHistoryRuntime.forward` 的调用点保持 `:244-249` 的现有三元返回 contract。
- 构造锚点：仅在获批准的后续实现提交中，将 `cosmos_framework/model/generator/omni_mot_model.py:309-312` 的 backend 实例替换为新类；不得修改 `:945-1002` 注入、packing、模型配置或训练 recipe。
- 测试锚点：在 `cosmos_framework/model/generator/mot/local_evidence_test.py:92-114` 后新增 `test_r09_b0_ttt_backend_contract`，覆盖 fixed-seed deterministic、finite、masked/padding inert、all-mask、batch permutation/cross-sample isolation、partial/full reset、boundary zero、two-segment `state/token/present` exact equivalence、`named_parameters`/optimizer/checkpoint exclusion。
- 现有可复用断言：`local_evidence_test.py:92-114` 已覆盖 recurrent presence/reset/segment 的形状；`local_history_runtime_test.py:174-220` 已冻结 optimizer prefixes；`callbacks/r09_a1_runtime_probe.py:71-76` 已展示 state bytes/segment max-abs 的产物字段模式。

## 5. 实施前审核请求

本 source audit 仅请求 `APPROVE_TO_IMPLEMENT_B0` 或 `REQUEST_CHANGES`。允许范围仅为获批后在上述两个实现锚点与一个 CPU 测试锚点内的最小改动。持续禁止 runtime wiring、GPU、A1-style smoke、多卡、长训、matched SR、backend freeze、RoboTTT/shared-MoT code import、Global/Agent/RL。
