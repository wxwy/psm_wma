# R09-B2 Matched Training Preflight Runbook v0.1

**状态**：DRAFT；仅用于三方方案审核。不得据此启动训练、GPU、评测、推理或修改 `cosmos-framework`。  
**前置事实**：R09-A1 recurrent bounded smoke 与 R09-B1 TTT bounded smoke 均已关闭；二者都只是 runtime 合同证据，不是收敛、吞吐、SR 或 backend selection 证据。

## 1. 目的与边界

R09-B2 的唯一目的，是在同一训练数据和同一训练预算下比较 `recurrent` 与 `ttt_fast_weight` 两个 Local temporal backend 的**训练期工程合同**。它不进行 closed-loop、SR、inference 或 deployment；B1 的 training-only no-grad fail-fast 仍然生效，因此不能把 B2 的训练 loss 解释为仿真表现。

本 Gate 不冻结 backend winner。正式 backend freeze 仍必须在 matched training、独立 inference-runtime Gate、同一评测预算的 intervention/SR、资源和复杂度审计都完成后另行决策。

## 2. 必须保持 matched 的变量

两侧必须由同一冻结的启动记录导出，除下表“允许差异”外逐项相等：

| 类别 | 必须一致 |
| --- | --- |
| 起点 | 同一 model-only base checkpoint；禁止从 B1 5-step DCP warm-start recurrent 或反向 warm-start TTT。 |
| 数据 | 同一四-suite LIBERO source、exact-window cache root/manifest、sample stride、suite mixture、epoch/stream 顺序、`LIBERO_LATENT_CACHE_VERIFY_RATIO=0`。 |
| 随机性 | 同一 seed、deterministic/cudnn 设置、rank/world size、数据 worker/prefetch、noise schedule；任一不可逐位确定因素须写入 D005。 |
| 训练 | 同一 precision、optimizer 类型与除 backend 专属 selector 外的超参、scheduler、EMA、max steps、microbatch、grad accumulation、clip、save/log cadence。 |
| 模型 | 相同 base model、Local evidence encoder、adapter、token budget、native vision/action loss、packing/mRoPE、history horizon、history mode=`normal`。 |
| 资源 | 同一 GPU 型号/数量、VRAM 上限、CPU/RAM 水位、网络策略与输出根；禁止同时运行其他训练/评测。 |

唯一允许差异是 `local_history_backend=recurrent|ttt_fast_weight` 及它不可避免的 optimizer membership：recurrent 记录既有 recurrent backend slow parameters；TTT 记录 B1 冻结的三条 exact selector，且 fast-weight backend 的 parameter/optimizer/DCP state 均为空。两侧均必须列出实际 name/count，不得用 prefix 假设替代。

## 3. 分轮前置与冻结命令

### B2-P0：只读资产/预算审计

在任何实现或运行前，产生一个 machine-readable plan artifact，至少记录：

1. 两侧 base checkpoint、root/submodule/Gitlink、cache manifest、dataset/config SHA256；
2. 两侧完整 resolved config diff，且 diff 只能落在 backend selector 与允许的 optimizer membership；
3. 当前单卡/多卡可用 GPU、CPU RAM、水位和与其他作业的互斥状态；
4. 两侧 launcher 的精确 argv、sanitized environment、D005 output/log/checkpoint 路径；
5. 训练-only 限制：TTT 不得进入 `no_grad`、inference、closed-loop 或 evaluation；
6. 100 optimizer steps 是 Runtime Plan v0.6 的最低连续稳定性阈值。实际 microbatch/world-size/时限须基于 P0 预算冻结，不能沿用 B1 的 2/5-step bounded profile。

P0 PASS 只表示方案可审，不代表授权实现或训练。

### B2-T：matched training（需独立运行批准）

仅在 P0 的三方审核及用户 GPU 授权后，分别执行 recurrent 与 TTT 各一次。每次运行的唯一输入是 P0 冻结的命令；不得基于中间 loss、OOM 或吞吐结果调整另一侧预算。任一 FAIL 立即停止整个比较，保留该侧日志/D005/checkpoint，禁止自动重跑。

每一侧至少保存：step 0、step 100（或明确冻结的最终 step）完整 DCP；每个 optimizer step 的 finite loss、grad norm、host timing、peak VRAM；TTT 还保存五成员 state/segment/reset/detach 事实。DCP 不能包含 TTT fast state。

## 4. 机器可读输出与 PASS/FAIL

最终输出拟为 `artifacts/g0/r09/b2/matched_training_contract.json`，不得覆盖 A1/B0/B1 artifact。其 schema 必须含：

```json
{
  "schema_version": "r09_b2_matched_training_v1",
  "status": "PASS|FAIL",
  "common": {"source": {}, "checkpoint": {}, "data_cache": {}, "resolved_config_sha256": "", "environment": {}, "resource": {}},
  "recurrent": {"d005": {}, "optimizer": {}, "checkpoints": {}, "stability": {}, "intervention": {}},
  "ttt_fast_weight": {"d005": {}, "optimizer": {}, "fast_state": {}, "checkpoints": {}, "stability": {}, "intervention": {}},
  "matched_diff": {"allowed_only": false, "same_step_budget": false, "same_data_stream": false, "same_resource_class": false},
  "limitations": []
}
```

PASS 必须同时满足：

- 两侧达到相同冻结 step budget，连续 100 steps 无 NaN/Inf/OOM/SIGTERM/SIGKILL；
- D005 与 resolved-config diff 证明仅存在允许差异；
- cache-only，无 online-VAE fallback；
- Local history Normal/Zero/Shuffle 的训练期 capture 满足 non-history invariants exact，并记录 future world 与 action sensitivity；
- recurrent state 与 TTT five-member state 都通过各自 reset/isolation/detach 合同；
- 两侧 checkpoint schema、optimizer membership、frozen common tensors、DCP reload 都可审计；
- 资源、step latency、state bytes、save/load/reset 成本均记录，但不以单项吞吐或短跑 loss 决定 winner。

FAIL 包括：输入/seed/数据流不一致、隐式 VAE fallback、任何未允许 config diff、TTT fast state持久化、inference/no-grad 路径、任意不稳定终止、缺失 D005/JSON/完整 DCP，或以短跑 SR 宣称 backend winner。

## 5. 审核请求与禁止范围

本版只请求 `APPROVE_TO_PLAN_B2_P0` 或 `REQUEST_CHANGES`。即使通过，也最多允许实现 P0 的只读资产/配置审计和其 JSON verifier；不授权 matched training、GPU、多卡、长训、eval/inference/closed-loop、SR、backend freeze、RoboTTT/shared-MoT、Global、Agent 或 RL。
