#!/usr/bin/env bash
# G0-R06 formal action-only LIBERO SFT baseline (loss_scale=0.0).
# 唯一变量 vs R06 joint = vision loss 开关(10.0 -> 0.0)。task0 全量 + latent cache + 1000 步。
set -euo pipefail
cd /gemini/code/psm_wma/cosmos-framework

export PYTHONPATH=/gemini/code/psm_wma/cosmos-framework:/gemini/code/psm_wma
export LIBERO_ROOT=/gemini/code/data/libero/libero_10_no_noops_1.0.0_lerobot
export WAN_VAE_PATH=/gemini/code/models/Wan2.2-TI2V-5B/Wan2.2_VAE.pth
export BASE_CHECKPOINT_PATH=/gemini/code/models/Cosmos3-Edge-Policy-DROID-dcp
export EDGE_POLICY_CHECKPOINT=/gemini/code/models/Cosmos3-Edge-Policy-DROID
export LIBERO_LATENT_CACHE_ROOT=/gemini/code/data/libero/libero_10_no_noops_1.0.0_lerobot_cosmos_exact_window_v1
export LIBERO_LATENT_CACHE_PARITY=/gemini/code/psm_wma/artifacts/g0/r06/exact_window_v1/smoke_parity.json
export IMAGINAIRE_OUTPUT_ROOT=/gemini/code/psm_wma/artifacts/g0/r06/action_only_formal_128x2_1000step
export CUDA_VISIBLE_DEVICES=0

/root/venvs/psm_wma_py313_cu128/bin/python -m torch.distributed.run --nproc_per_node=1 \
  -m cosmos_framework.scripts.train \
  --sft-toml=examples/toml/sft_config/action_policy_libero_edge_r06.toml \
  -- optimizer.optimizer_type=AdamW optimizer.fused=false \
  trainer.max_iter=1000 trainer.grad_accum_iter=2 \
  'scheduler.cycle_lengths=[1000]' \
  model.config.rectified_flow_training_config.loss_scale=0.0 \
  dataloader_train.max_samples_per_batch=128 \
  dataloader_train.dataloader.num_workers=4 dataloader_train.dataloader.persistent_workers=true dataloader_train.dataloader.prefetch_factor=1 \
  +trainer.callbacks.r06_metrics._target_=tools.g0.r05_tiny_overfit_metrics.R05TinyOverfitMetricsCallback \
  +trainer.callbacks.r06_metrics.output_path=/gemini/code/psm_wma/artifacts/g0/r06/action_only_formal_128x2_1000step/step_metrics.jsonl \
  +trainer.callbacks.r06_metrics.optimizer_type=AdamW \
  +trainer.callbacks.r06_metrics.fused=false \
  2>&1 | tee -a /gemini/code/psm_wma/artifacts/g0/r06/action_only_formal_128x2_1000step/train.log
