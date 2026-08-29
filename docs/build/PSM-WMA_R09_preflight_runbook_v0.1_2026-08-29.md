# R09 Local Backend Preflight Runbook v0.1

**状态**：REVIEW；仅计划，未授权实现或 GPU。  
**前置**：R08 Gate B 已三方关闭；输入仅为 R08 `LocalEvidenceBatch`，不得重读 raw RGB/parquet 或改变时间对齐。

## 固定边界

- A 先于 B：先做 `recurrent_latent` 的 sample-internal window replay；A 未通过不得实现 `ttt_fast_weight`。
- 首轮不做跨 batch/worker/episode 状态携带；`M_start=zeros`，每样本 replay `[max(0,t-H),...,t-1]`。
- 不改 Cosmos shared MoT、native vision/action loss、R08 encoder、Local token budget、canonical checkpoint 或训练范围。
- 禁止 GPU、长训、多卡、matched SR、backend freeze，直到本 runbook 三方审核通过。

## R09-A0：CPU contract（最小实现前）

复用 `LocalEvidenceEncoder`，新增独立 recurrent compressor 与现有 Local readout 的最小适配。输入 `evidence[B,H,D_e]`、`mask[B,H]`；输出 `tokens[B,1,D_local]`、可审计 state。断言：mask padding inert/exact-zero、all-mask absent、finite、同输入确定、episode reset、batch permutation isolation、Normal/Zero/Shuffle/Stale/Truncated 均可前向。产物：`artifacts/g0/r09/a0_contract.json`。

## R09-A1：单卡 fwd/bwd smoke（待审核后）

固定 Gate-A canonical checkpoint、同一批次和 R08 history schema；只训练 Local encoder/compressor/readout/adapter。记录 100 optimizer steps 的 finite loss、Local gradients、冻结 Cosmos gradients=0、peak VRAM、step latency、state bytes；每 step 对 state detach/reset 记录。FAIL：任何 NaN、跨 episode/batch 泄漏、冻结参数梯度、干预改变 packing/index，或无 nonzero future/action sensitivity。产物：`R09_local_backend_selection_smoke.json`。

## R09-B：TTT fast-weight（A 通过后另审）

仅替换 A 的 temporal compressor，保持其余 schema、token budget、batch、checkpoint、loss 与 trainable scope 完全相同。额外断言：fast state 每 episode 实际有限更新；segment 边界数值连续而 autograd graph detach；reset 正确；fast state 不进入 slow-weight optimizer/checkpoint。不得把 RoboTTT 原结构插入 shared MoT。

## 审核/推进

本 v0.1 审核通过后只执行 A0；A0 单独送审后才执行 A1；A1 三方通过后才提出 B 的实施申请。backend 选择不得由短跑 SR 决定，比较 future/action sensitivity、稳定性、状态保持、VRAM/latency 与 state-management 成本。
