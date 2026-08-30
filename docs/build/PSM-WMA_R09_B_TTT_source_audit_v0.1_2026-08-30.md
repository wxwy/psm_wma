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
| `update_rule` | 纯 per-sample SGD：`W <- W - 0.1 * grad_W(inner_loss)`；不用 momentum/Adam state | 每个完整 4-valid-timestep segment 只更新一次，不引入 optimizer/DCP state。 |
| `inner_objective` | backend-local、无参数目标：`MSE(W @ evidence_t, stopgrad(evidence_t[:D_local]))` | `evidence` 已由 `replay(evidence, mask, state)` 提供；不依赖 readout/teacher 或 runtime 接口，不新增 slow parameter。 |
| `inner_steps` | 每个 replay segment 1 次 SGD update | 与 segment temporal span 解耦，减少 B0 graph/state 复杂度。 |
| `segment_steps` | 4 个有效 causal evidence timesteps；仅沿单 sample/window 的 `H` 轴分段 | 默认 `H=16` 时形成四段；终端 1--3 valid remainder 是 pending terminal remainder，不构成更新 segment；每个 sample/window `state_start=zeros`，绝不跨 outer trainer/policy/control forward carry。 |
| `fast_state_dtype` | `torch.bfloat16` | 与 Local runtime 的 bf16 测试路径兼容；inner loss/gradient 的临时计算可提升到 fp32，但不得持久化为 fast state。 |
| `fast_state_bytes_limit` | 每 sample 18,953 bytes | `W=32*256*2=16,384`、`pending_evidence=4*256*2=2,048`、`last_evidence=256*2=512`、`initialized=1`、`segment_progress=int64=8`；临时 fp32 gradient 不持久化、不计入 state。 |
| `slow_learned_parameters` | 零新增 | 新 backend 不得注册 `nn.Parameter`；既有 encoder/readout/adapter 参数、optimizer scope 与 checkpoint contract 不变。 |

完整 fast runtime state 为 `W[B,32,256]`、`pending_evidence[B,4,256]`、`last_evidence[B,256]`、`initialized[B]`、`segment_progress[B]`。最终 token 为每 sample 的 `W @ last_evidence`，shape 固定 `[B,1,32]`；all-mask 且未 initialized 时返回 zero token 与 `present=false`，all-mask continuation 保持既有 `present` 与 token。每个 inner update 只读取/写入本 sample 的 state，以禁止跨 sample 的梯度、mask 或 scatter 耦合。

### 2.1 精确 segment 数学、dtype 与图边界

对 sample `b`，只将 valid evidence 的 `e_{b,j}` 以到达顺序写入 `pending_evidence`；masked/padding 不读写 state、不会推进 `segment_progress`。当且仅当 progress 到 4 时，以同一个 update 前 `\tilde W_b = W_b.detach().float().requires_grad_(True)` 计算：

```text
t_{b,j} = stopgrad(e_{b,j}[:32].float())
p_{b,j} = tilde_W_b @ e_{b,j}.detach().float()
L_b = mean_{j=1..4}(mean_{d=1..32}((p_{b,j,d} - t_{b,j,d})^2))
g_b = autograd.grad(L_b, tilde_W_b, create_graph=False)[0]
W_b' = (tilde_W_b - 0.1 * g_b).to(bfloat16).detach()
```

随后清零该 sample 的 `pending_evidence`、将 progress 置零；zero-valid replay 不计算 loss/gradient、不更新 `W`。逻辑 sample/window 结束时，终端 1--3 valid remainder 保留在 returned state、更新 `last_evidence`/`present`/token，但**永不更新 `W`**，也没有 B0 `finalize` API。故对 `N_valid`，更新次数严格为 `floor(N_valid / 4)`；CPU contract 必须覆盖 `N_valid=1,2,3,5,6,7`。普通 replay call boundary 不 finalize，任意 two-segment split 与一次 full replay 使用相同 update 边界。`last_evidence` 在每个 valid timestep保存 `e.detach().to(bfloat16)`；`initialized` 在首个 valid timestep后为 true。partial/full reset 必须同时清零全部五个 state 成员。

inner update 仅作一阶、全量 detach：`create_graph=False`，update 后 `W` detach，缓存 evidence detach，最终 token 从 detached state 产生。故 native vision/action loss 不得通过 adaptation 或更早 history evidence 回传；CPU contract 必须断言 `graph_detached=true`，且只验证该 first-order detached 行为。

### 2.2 复合 state 的机器可读 artifact 扩展

`artifacts/g0/r09/b0_ttt_contract.json` 在既有 `state` 下追加以下向后兼容字段；`bytes` 指 logical tensor payload，不是 allocator/VRAM footprint。verifier 必须逐成员独立计算 `numel * element_size` 并硬断言总数与 limit。

```json
"state": {
  "members": {
    "W": {"shape_per_sample": [32, 256], "dtype": "bfloat16", "bytes_per_sample": 16384},
    "pending_evidence": {"shape_per_sample": [4, 256], "dtype": "bfloat16", "bytes_per_sample": 2048},
    "last_evidence": {"shape_per_sample": [256], "dtype": "bfloat16", "bytes_per_sample": 512},
    "initialized": {"shape_per_sample": [], "dtype": "bool", "bytes_per_sample": 1},
    "segment_progress": {"shape_per_sample": [], "dtype": "int64", "bytes_per_sample": 8}
  },
  "logical_bytes_per_sample": 18953,
  "fast_state_parameter_count": 0,
  "bytes_limit": 18953,
  "bytes_limit_pass": false
}
```

## 3. A/B matched 影响

- 参数量：A 为当前 `GRUCell` 的 slow 参数；B 新增 slow parameter=0，取而代之的是每 sample ephemeral 8,192-element fast `W`，不出现在 `named_parameters()`、optimizer 或 checkpoint。
- 接口：B 保持 `LocalEvidenceEncoder` 输出 `[B,H,256]`、Local token `[B,1,32]`、`present[B]`、history schema、单 Local token budget 和 `recurrent_backend` 外接字段不变。
- 训练：B 的 inner loss 与 native vision/action loss 隔离，且其 first-order detached state/token 明确禁止后者经 adaptation 回传到 history evidence；B 不改变 A1 四个 optimizer prefix，也不新增 fifth key。任何未来 nonzero slow parameter 必须列出 exact name/count 并重新申请三方豁免。
- 数值：CPU contract 的 deterministic、任意（含未对齐）two-segment state/token/present equivalence 统一要求 `tolerance=0.0`；pending buffer 使 call 切分不改变 4-valid-timestep update 次序。

## 4. 拟议实现与 CPU 测试锚点（未创建）

- 实现锚点：仅在 `cosmos_framework/model/generator/mot/local_evidence.py:156-200` 的现有 backend 位置新增独立 `TTTLocalMemoryBackend`，实现上述五成员 state 的 `initial_state`/`replay`/`reset_mask`；B0 不修改 `LocalHistoryRuntime.forward` 的 `:244-249`。
- B0 明确不改 `cosmos_framework/model/generator/omni_mot_model.py`、模型配置、注入、packing 或训练 recipe；production `recurrent_backend` 继续是 A1 GRU。把 TTT backend 接入 `omni_mot_model.py` 只能由后续 B1/runtime-integration Gate 另行审核。
- 测试锚点：在 `cosmos_framework/model/generator/mot/local_evidence_test.py:92-114` 后新增 `test_r09_b0_ttt_backend_contract`，直接实例化 `TTTLocalMemoryBackend`，覆盖 fixed-seed deterministic、`N_valid=1,2,3,5,6,7` 的 `floor(N/4)` 更新次数、finite、`fast_state_updated`、masked/padding inert、all-mask、batch permutation/cross-sample isolation、partial/full reset、boundary zero、未对齐 two-segment `state/token/present` exact equivalence 与 `segment_present_equal`、逐成员 logical-bytes、`named_parameters`/optimizer/checkpoint exclusion，以及 detached graph。
- 现有可复用断言：`local_evidence_test.py:92-114` 已覆盖 recurrent presence/reset/segment 的形状；`local_history_runtime_test.py:174-220` 已冻结 optimizer prefixes；`callbacks/r09_a1_runtime_probe.py:71-76` 已展示 state bytes/segment max-abs 的产物字段模式。

## 5. 实施前审核请求

本 source audit 仅请求 `APPROVE_TO_IMPLEMENT_B0` 或 `REQUEST_CHANGES`。允许范围仅为获批后在一个独立 backend 实现锚点与一个 CPU 测试锚点内的最小改动，并产出 machine-readable artifact/verifier；生产 runtime wiring 不是 B0 范围。持续禁止 runtime wiring、GPU、A1-style smoke、多卡、长训、matched SR、backend freeze、RoboTTT/shared-MoT code import、Global/Agent/RL。
