# R09-B TTT Fast-Weight Preflight Runbook v0.2

**状态**：REVIEW；本版替代 v0.1 的 B0 审核申请，未授权任何代码、CPU 测试、GPU、训练或评测。  
**前置**：R09-A1 已三方关闭；A1 evidence root=`9a79bcf`，submodule/Gitlink=`c0287e2`。  
**复用入口**：`local_evidence.py:202-249` 的 Local history compressor 调用、`omni_mot_model.py:302-313` 的注入点，以及 A1 allowlist `action_policy_libero_edge_all.py:189-195`。

## 1. B0 只冻结设计框架

B0 不是 TTT 算法实现授权，而是为后续实现申请冻结以下不变量：TTT 只替换 temporal compressor；history schema、`LocalEvidenceEncoder`、每 sample 一个 Local token、adapter、native vision/action loss、checkpoint warm-start 与 A1 optimizer scope 不变；不接 shared MoT、packing、mRoPE、数据集或 runtime。

具体 fast-weight 参数化、inner update rule/objective/steps、segment_steps、fast-state dtype/bytes 上限均保持 `[TBD/GATE]`。它们必须在下一份 **B0 source-audit/implementation 申请**中逐项给出候选值、理由、A/B matched 影响和实际 `file:line`；取得 ChatGPT/MM/Kimi 三方批准前不得编码。该申请才请求 `APPROVE_TO_IMPLEMENT_B0`。

RoboTTT 只作为算法参考：借鉴其 per-sample fast-weight、inner update 与 segment/TBPTT 的问题拆解；不引入其第三方实现、包或模型结构，不复制到 Cosmos shared MoT。候选必须先适配本项目的 clean Local contract、A1 optimizer/checkpoint 边界与上述三方审核流程。

## 2. slow/fast state 边界

默认不允许 TTT backend 新增 slow learned parameters。若后续三方明确批准例外，参数只能复用 A1 既有四组 allowlist：`local_history_runtime.encoder.*`、`local_history_runtime.recurrent_backend.cell.*`、`local_memory2llm.*`、`local_memory_modality_embed`；不得增加 allowlist key，外接字段仍为 `recurrent_backend`，只替换其内部实现。

fast state 不是 `nn.Parameter`：按 sample/window 从零开始，只在同一 sample 的已批准 segment 内携带；episode reset 后归零；不得进入 optimizer、DCP model/optimizer/scheduler/trainer state，且不得跨 batch、worker、episode 或 sample 共享、读写或梯度耦合。

`segment_steps` 指一个 fast state 持有的连续 forward step 数（`state_out` 在 reset 前跨越的 step 数）；`inner_steps` 指一个 segment 内的 inner update 次数。后续候选必须满足 `segment_steps >= inner_steps` 且整除 sample 内的 forward step 总数。

## 3. B0 source-audit 后的最小 CPU contract

实现范围只能是独立 backend 与其定向 CPU 测试；实际文件/命令须在 source audit 中以 `file:line` 冻结，不能预设测试路径。计划环境：`/gemini/code/psm_wma/cosmos-framework`、既有 `/root/venvs/psm_wma/bin/python`、CPU、无 GPU/网络/数据集/checkpoint。产物为 `artifacts/g0/r09/b0_ttt_contract.json`。

输入为 `evidence[B,H,D_e]`、`mask[B,H]`，输出为 `tokens[B,1,D_local]`、`state_out`、`local_present[B]`。all-mask 必须 absent 且不 pack；padding 不改 state；masked step 不 update。PASS 还要求 fixed-seed deterministic、finite、fast state 实际有限更新、partial/full reset、two-segment value continuity、detach 前有 graph/后无 graph、detach value exact、batch permutation 和 cross-sample isolation、boundary isolation。boundary 外任何 forward 均不得读取 fast state，boundary 后 state_in 必须为零或重新初始化。

FAIL：任一断言失败、fast state 在 `named_parameters()`、optimizer 或 checkpoint state 中出现，或任何跨 sample inner-gradient/mask/scatter 耦合。失败保持 B0 REVIEW，不允许 runtime/GPU。

## 4. 机器可读 schema 与回填

```json
{
  "schema_version": "r09_b0_ttt_contract_v2",
  "status": "PASS|FAIL",
  "root_revision": "<root>", "submodule_revision": "<submodule>", "gitlink_revision": "<gitlink>",
  "candidate": {
    "fast_weight_parametrization": "<approved>", "update_rule": "<approved>",
    "inner_objective": "<approved>", "inner_steps": "<approved>", "segment_steps": "<approved>",
    "fast_state_dtype": "<approved>", "fast_state_bytes_limit": 0, "slow_learned_parameters": "<approved>"
  },
  "state": {"shape": [], "dtype": "", "bytes": 0, "fast_state_parameter_count": 0},
  "checks": {"finite": false, "fast_state_updated": false, "detach_value_exact": false, "graph_detached": false, "reset": false, "all_mask_absent": false, "cross_sample_isolation": false, "boundary_isolation": false, "optimizer_excluded": false, "checkpoint_excluded": false},
  "command": {"argv": [], "cwd": "", "python": ""}
}
```

全部 8 个 `candidate` 字段及实际 state 数值必须由获批后的运行回填，不得预写为项目事实。

## 5. 禁止项与审核请求

持续禁止 runtime wiring、GPU、A1-style smoke、多卡、长训、matched SR、backend freeze、RoboTTT/shared MoT、Global/Agent/RL，以及 inner update 的跨 sample 梯度耦合或边界外 fast-state 读取。

本 runbook 请求三方给出 `APPROVE_TO_ADVANCE_B0_SOURCE_AUDIT` 或 `REQUEST_CHANGES`；它不请求 `APPROVE_TO_IMPLEMENT_B0`。只有 source audit 冻结具体 8 项 candidate 后，才另发 B0 implementation 申请。
