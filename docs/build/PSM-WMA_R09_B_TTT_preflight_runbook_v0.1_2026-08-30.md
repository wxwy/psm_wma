# R09-B TTT Fast-Weight Preflight Runbook v0.1

**状态**：REVIEW；仅实施前置核查与审核申请，未授权代码、CPU 实现验证、GPU、训练或评测。  
**前置关闭**：R09-A1 已由 ChatGPT、MM、Kimi 三方 `APPROVE_TO_CLOSE_A1`；A1 evidence root=`9a79bcf`，submodule/Gitlink=`c0287e2`，状态收口 root=`30c571e`。  
**权威边界**：`PSM-WMA_R09_preflight_runbook_v0.1_2026-08-29.md` §R09-B 与 `PSM-WMA_Local_Memory_detailed_design_addendum_v0.1.md` §11/12/18/20。

## 1. 目的与范围

R09-B 仅将 R09-A 已验证的 `recurrent_latent` temporal compressor 替换为 `ttt_fast_weight`。它不创建第二套 Local 系统，也不改变 causal history schema、`LocalEvidenceEncoder`、每 sample 一个 Local token、`local_memory2llm`、native vision/action loss、A1 trainable scope 或 checkpoint warm-start。

本 runbook 只请求批准 **B0 设计冻结 + CPU contract 实现**。在 B0 独立审核通过前，禁止接入 runtime、GPU、A1-style 100-step smoke、R09-B matched SR、TTT backend freeze、多卡及长训。

## 2. 已核验入口与不变量

- 生产 Local path：`cosmos_framework/model/generator/mot/local_evidence.py:202-249`，当前由 `LocalHistoryRuntime` 编码 history，再调用 recurrent `replay()`；B 只能替换该 compressor 调用。
- A1 注入点：`cosmos_framework/model/generator/omni_mot_model.py:302-313`；不得改 shared MoT、packing、mRoPE 或 Local adapter 位置。
- A1 optimizer allowlist：`cosmos_framework/configs/base/experiment/action/posttrain_config/action_policy_libero_edge_all.py:189-195`；B 必须保持 encoder、backend、`local_memory2llm`、`local_memory_modality_embed` 的相同范围，且 fast runtime state 不得成为 optimizer parameter。
- 输入/输出契约：`evidence[B,H,D_e]`、`mask[B,H]`，输出 `tokens[B,1,D_local]`、`state_out`、`local_present[B]`。all-mask 样本 absent 且不得被 pack；masked timestep 不改变 state。

## 3. 未冻结决策（必须先审核）

以下均为 `[TBD/GATE]`，不得在编码时默选：fast-weight 参数化、inner update rule、inner objective、inner step 数、segment 长度、fast-state dtype/bytes 上限，以及 B0 是否允许 slow learned backend 参数。审核申请必须逐项给出候选值、理由和 A/B matched 影响。

无论候选为何，slow learned parameters（若有）与 runtime fast state 必须分离：只有 slow learned parameters 可以进入 A1 对应 optimizer/checkpoint；fast state 必须按 sample/window 起零、只在同 sample segment 间携带、episode reset 归零，且不进入 optimizer state、DCP model/optimizer/scheduler/trainer state。

## 4. 分轮 Gate 与精确命令

### B0：CPU contract（待三方批准后）

最小改动仅限新增独立 TTT backend 及其 CPU tests；不得修改 `omni_mot_model.py`、数据集、Cosmos shared MoT 或训练 recipe。建议入口为现有 `local_evidence.py` 的独立 backend 类与同目录定向测试，具体文件/符号必须在 B0 source audit 中以实际 `file:line` 冻结。

计划验证命令（尚未执行）：

```bash
cd /gemini/code/psm_wma/cosmos-framework
PYTHONPATH=. /root/venvs/psm_wma/bin/python -m pytest -q \
  cosmos_framework/model/generator/mot/local_evidence_test.py
```

不需要 GPU；不访问外网；产物计划为 `artifacts/g0/r09/b0_ttt_contract.json`。PASS：固定 seed 确定、finite、all-mask absent、padding inert、batch permutation isolation、partial/full reset、两段 carry 的 value 连续且 graph 在边界 detach、fast state 有实际有限更新、fast state 不在 `named_parameters()`/optimizer/checkpoint state。任一失败为 FAIL，保持 B0 REVIEW。

### B1：runtime/A1-style smoke（另行申请）

仅 B0 三方关闭后，才单独审查 runtime wiring 和单卡 bounded smoke。该轮必须复用 A1 的 Gate-A warm-start、数据/cache、loss、batch、allowlist、Normal/Zero/Shuffle capture 与 fixed-weight invariants；任何改变须作为新变量拒绝。GPU 命令、资源、checkpoint、日志和 JSON 路径届时按 D005 在启动前单独公布，不在本 runbook 中预授权。

## 5. 机器可读产物 schema

`b0_ttt_contract.json` 至少包含：

```json
{
  "schema_version": "r09_b0_ttt_contract_v1",
  "status": "PASS|FAIL",
  "root_revision": "<root>",
  "submodule_revision": "<submodule>",
  "gitlink_revision": "<gitlink>",
  "candidate": {"update_rule": "<approved>", "inner_steps": "<approved>", "segment_steps": "<approved>"},
  "state": {"shape": [], "dtype": "", "bytes": 0, "fast_state_parameter_count": 0},
  "checks": {"finite": false, "fast_state_updated": false, "detach_value_exact": false, "graph_detached": false, "reset": false, "all_mask_absent": false, "optimizer_excluded": false, "checkpoint_excluded": false},
  "command": {"argv": [], "cwd": "", "python": ""}
}
```

运行得到的尺寸、bytes、参数数和候选超参数必须由 artifact 回填；不得预写为事实。

## 6. 审核请求与禁止范围

本 v0.1 请求 ChatGPT、MM、Kimi 给出 `APPROVE_TO_IMPLEMENT_B0` 或 `REQUEST_CHANGES`，并明确批准的 update rule/inner objective 边界。未获得三方批准前，R09-B 继续 BLOCKED。

始终禁止：RoboTTT 原结构进入 shared Cosmos MoT、修改 native vision/action loss、读取 raw RGB/parquet、改变 causal alignment、跨 batch/worker/episode 隐式 state、fast state 写入 DCP/optimizer、GPU、多卡、长训、matched SR、backend freeze、Global/Agent/RL。
