# PSM-WMA G0-R05 LIBERO Tiny Overfit Runbook v0.1

- 状态：`reviewed`
- 日期：2026-08-15
- 前置：G0-R04 `PASS`；R01-R04 期间 PSM/Memory/EMA 均关闭

## 1. 目的与 PASS 边界

在固定的 4 个 LIBERO 窗口上连续训练 100 optimizer steps，验证 Edge-Policy-DROID → LIBERO
适配具有可学习性；另用第 5 个窗口做 held-out finite 与 checkpoint reload 一致性检查。本 Gate
不评价 closed-loop SR，R06 前不得把 tiny-overfit 结果解释为任务成功率。

PASS 必须同时满足：

1. 本地 action stats sanity 为 `PASS`；
2. 100/100 steps 连续完成，total/action/action-x0/vision loss 与梯度全部 finite；
3. 前 10 步与后 10 步中位数相比，total/action/action-x0 ratio 均 `<=0.80`；
4. vision loss 后 10 步中位数不超过前 10 步的 `1.10`；
5. held-out forward 全部 finite；
6. `iter_000000100` 完整恢复后，在相同 iteration、固定样本和 deterministic noise 下，四项
   held-out 指标满足 `rtol=1e-5, atol=1e-6`；
7. checkpoint 的 `model/optim/scheduler/trainer` 四部分齐全，无 OOM/SIGKILL/异常。

## 2. 前置资产

- 代码仓库：`/gemini/code/psm_wma`
- Cosmos：`/gemini/code/psm_wma/cosmos-framework`
- 环境：`/root/venvs/psm_wma_py313_cu128`
- DCP：`/gemini/code/models/Cosmos3-Edge-Policy-DROID-dcp`
- VAE：`/gemini/code/models/Wan2.2-TI2V-5B/Wan2.2_VAE.pth`
- 数据：`/gemini/code/data/libero/libero_10_no_noops_1.0.0_lerobot`
- stats：`cosmos-framework/cosmos_framework/data/generator/action/normalizer_stats/libero_native_frame_wise_relative_rot6d.json`

不访问外网。需要单张 40GB GPU；在线 VAE 路径预计 GPU 分配峰值约 35GB、RSS 小于 32GB
容器上限。固定样本降低数据随机性，但当前仍受 CPU 视频解码限制。

## 3. 复用入口与最小改动

- 复用 `action_policy_libero_edge_warmstart` 的 Edge、selector、domain 5、weight-decay 行保护和
  EMA-off 配置；新增 `action_policy_libero_edge_tiny_overfit`，不改 R04 配置。
- `ActionFixedSubsetCycleDataset` 只在显式 `tiny_overfit_num_samples` 时启用；默认数据路径不变。
- `action_x0_reconstruction_mae` 由 rectified-flow 恒等式
  `x0_hat - x0 = sigma * (pred_velocity - target_velocity)` 得到，只作为 detached 诊断量，不参与 loss。
- `R05TinyOverfitMetricsCallback` 经 CLI 注入，每步输出 JSONL，不初始化 W&B。
- trainer 的 `run_validation_on_start` 对 fresh/resumed run 都生效；默认值为 false，其他 recipe 行为不变。

## 4. Phase A：action stats sanity

工作目录：`/gemini/code/psm_wma`。

```bash
PYTHONPATH=/gemini/code/psm_wma/cosmos-framework \
/root/venvs/psm_wma_py313_cu128/bin/python tools/g0/audit_r05_action_stats.py \
  --dataset /gemini/code/data/libero/libero_10_no_noops_1.0.0_lerobot \
  --stats /gemini/code/psm_wma/cosmos-framework/cosmos_framework/data/generator/action/normalizer_stats/libero_native_frame_wise_relative_rot6d.json \
  --output /gemini/code/psm_wma/artifacts/g0/r05/R05_action_stats_sanity.json
```

已得到的前置事实：101,469 帧、379 parquet，10D 全 finite，最大 normalized-unit 外尾比例
`0.0306892 < 0.10`，状态 `PASS`。Kimi 必须独立重跑或核对 JSON provenance 后才可启动 Phase B。

## 5. Phase B：固定 4 样本训练 100 steps

工作目录：`/gemini/code/psm_wma/cosmos-framework`。完整启动命令：

```bash
source /root/venvs/psm_wma_py313_cu128/bin/activate
export PYTHONHASHSEED=42
export PYTHONPATH=/gemini/code/psm_wma/cosmos-framework:/gemini/code/psm_wma
export LIBERO_ROOT=/gemini/code/data/libero/libero_10_no_noops_1.0.0_lerobot
export BASE_CHECKPOINT_PATH=/gemini/code/models/Cosmos3-Edge-Policy-DROID-dcp
export EDGE_POLICY_CHECKPOINT=/gemini/code/models/Cosmos3-Edge-Policy-DROID
export WAN_VAE_PATH=/gemini/code/models/Wan2.2-TI2V-5B/Wan2.2_VAE.pth
export IMAGINAIRE_OUTPUT_ROOT=/gemini/code/psm_wma/artifacts/g0/r05/tiny_overfit_100step

torchrun --standalone --nproc-per-node=1 -m cosmos_framework.scripts.train \
  --deterministic \
  --sft-toml=examples/toml/sft_config/action_policy_libero_edge_r05.toml -- \
  optimizer.optimizer_type=AdamW optimizer.fused=false \
  dataloader_train.dataloader.num_workers=0 \
  dataloader_train.dataloader.persistent_workers=false \
  dataloader_train.dataloader.prefetch_factor=null \
  dataloader_val.dataloader.num_workers=0 \
  dataloader_val.dataloader.persistent_workers=false \
  dataloader_val.dataloader.prefetch_factor=null \
  +trainer.callbacks.r05_metrics._target_=tools.g0.r05_tiny_overfit_metrics.R05TinyOverfitMetricsCallback \
  +trainer.callbacks.r05_metrics.output_path=/gemini/code/psm_wma/artifacts/g0/r05/tiny_overfit_100step/step_metrics.jsonl \
  +trainer.callbacks.r05_metrics.validation_output_path=/gemini/code/psm_wma/artifacts/g0/r05/tiny_overfit_100step/held_out_metrics.jsonl \
  +trainer.callbacks.r05_metrics.optimizer_type=AdamW \
  +trainer.callbacks.r05_metrics.fused=false \
  2>&1 | tee /gemini/code/psm_wma/artifacts/g0/r05/tiny_overfit_100step/train.log
```

训练 subset 为 flat index `[0,1,2,3]` 循环；held-out 为 index `4`。启动前必须断言五个窗口属于
同一 episode/task，且 train 与 held-out index 不重叠。

## 6. Phase C：checkpoint reload consistency

使用独立输出根，完整恢复 `iter_000000100` 的 model/optim/scheduler/trainer。恢复得到 iteration 100，
`run_validation_on_start=true` 立即执行同一个 held-out index 4，`max_iter=100` 因而不会新增训练步。

```bash
export IMAGINAIRE_OUTPUT_ROOT=/gemini/code/psm_wma/artifacts/g0/r05/tiny_overfit_reload
export R05_CHECKPOINT=/gemini/code/psm_wma/artifacts/g0/r05/tiny_overfit_100step/psm_wma/g0_r05/edge_libero_tiny_overfit/checkpoints/iter_000000100

torchrun --standalone --nproc-per-node=1 -m cosmos_framework.scripts.train \
  --deterministic \
  --sft-toml=examples/toml/sft_config/action_policy_libero_edge_r05.toml -- \
  optimizer.optimizer_type=AdamW optimizer.fused=false \
  checkpoint.load_path=${R05_CHECKPOINT} checkpoint.load_training_state=true checkpoint.strict_resume=true \
  trainer.run_validation_on_start=true trainer.max_iter=100 \
  dataloader_train.dataloader.num_workers=0 \
  dataloader_train.dataloader.persistent_workers=false \
  dataloader_train.dataloader.prefetch_factor=null \
  dataloader_val.dataloader.num_workers=0 \
  dataloader_val.dataloader.persistent_workers=false \
  dataloader_val.dataloader.prefetch_factor=null \
  +trainer.callbacks.r05_metrics._target_=tools.g0.r05_tiny_overfit_metrics.R05TinyOverfitMetricsCallback \
  +trainer.callbacks.r05_metrics.output_path=/gemini/code/psm_wma/artifacts/g0/r05/tiny_overfit_reload/step_metrics.jsonl \
  +trainer.callbacks.r05_metrics.validation_output_path=/gemini/code/psm_wma/artifacts/g0/r05/tiny_overfit_reload/held_out_metrics.jsonl \
  +trainer.callbacks.r05_metrics.optimizer_type=AdamW \
  +trainer.callbacks.r05_metrics.fused=false \
  2>&1 | tee /gemini/code/psm_wma/artifacts/g0/r05/tiny_overfit_reload/reload.log
```

## 7. Phase D：Gate 汇总

```bash
cd /gemini/code/psm_wma
PYTHONPATH=/gemini/code/psm_wma/cosmos-framework \
/root/venvs/psm_wma_py313_cu128/bin/python tools/g0/collect_r05_gate.py \
  --stats artifacts/g0/r05/R05_action_stats_sanity.json \
  --metrics artifacts/g0/r05/tiny_overfit_100step/step_metrics.jsonl \
  --held-out artifacts/g0/r05/tiny_overfit_100step/held_out_metrics.jsonl \
  --reload-held-out artifacts/g0/r05/tiny_overfit_reload/held_out_metrics.jsonl \
  --checkpoint artifacts/g0/r05/tiny_overfit_100step/psm_wma/g0_r05/edge_libero_tiny_overfit/checkpoints/iter_000000100 \
  --output artifacts/g0/r05/R05_libero_tiny_overfit.json
```

## 8. Schema 与失败分流

- `step_metrics.jsonl`：iteration、total/action/action-x0/vision loss 及 finite、grad、GPU peak、RSS、optimizer/fused。
- held-out JSONL：iteration 与四项 loss/finite；训练后和 reload 各一条。
- Gate JSON：stats sanity、100 步连续性、四项趋势、held-out/reload 对比、checkpoint 完整性、失败码。

失败分流：

- stats FAIL：停止训练，重算本地 stats 或确认数据版本；
- OOM/SIGKILL：记 `BLOCKED_RESOURCE`，不得降为代码 FAIL；
- action/total 不降：检查固定 subset、学习率、domain 5 与 normalization；
- vision 爆炸：检查 joint loss scale 与输入图像/latent parity；
- reload mismatch：确认完整恢复 iteration 100、deterministic 模式、held-out index 与 checkpoint 路径；
- held-out nonfinite：R05 `FAIL`，不得进入 R06。

## 9. 回填字段

完成后更新 `SESSION.md`、`TODO.md`，记录 stats SHA-256、代码/数据/checkpoint 路径、100 步耗时、
四项趋势 ratio、held-out/reload 最大差、GPU/RSS 峰值、Gate 状态、Kimi 审查结论与对应提交哈希。
