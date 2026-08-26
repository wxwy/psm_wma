---
name: cache-5suite-merge-build
description: 5-suite（4in1 + libero_90）合并跑 cache build 的最小修改与资源评估
metadata:
  type: project
---

**场景**：把 libero_90 作为第 5 suite 加入 `launch_parallel_cache_build.sh`，与 4in1 4 suite 合并同波跑 cache。

**libero_90 真实规模**（2026-08-25 实测 `/disk/rl/data/LIBERO_LeRobot_v3/libero_90`）：
- **3,921 episodes / 569,249 frames / 73 unique tasks**（不是 90 task，meta/tasks.parquet 实际 73 行）
- v3.0 布局齐全（`meta/tasks.parquet` + `meta/episodes/chunk-000/file-*.parquet` + `data/chunk-000/file-*.parquet`）
- meta/episodes parquet 与 data parquet schema 不同：前者是元数据（不含 frame_index），后者是帧数据（含 frame_index/task_index/episode_index）
- 是 4in1 任一 suite 的 **8.6~10.3×**
- libero_90 与 libero_10 重叠 7 task（LIBERO-10 ⊂ LIBERO-90）→ SFT 训练阶段需决策是否去重叠

**最小修改清单**（仅 1 行）：

```diff
# tools/g0/launch_parallel_cache_build.sh:13
- for suite in libero_spatial libero_object libero_goal libero_10; do
+ for suite in libero_spatial libero_object libero_goal libero_10 libero_90; do
```

**零改动**：
- `tools/g0/build_cosmos_libero_latent_dataset.py`：`--suite` 默认 `dataset_root.name`（line 206, 210-211），无 ALLOWED 校验
- `tools/g0/merge_latent_cache_shards.py`：自动 `glob("dataset_manifest_shard_*.json")` + 按 `episode_index` 去重

**shard 切分**：`build_cosmos_libero_latent_dataset.py:88` `episode_ids[shard::num_shards]` mod 切片。libero_90 3,921/5 ≈ 784 ep/shard，与 4in1 79-91 ep/shard 同量级。

**资源评估**：

| 项 | 4in1 已交付 | + libero_90 |
|---|---|---|
| 总 episodes | 1,693 | 5,614 |
| 磁盘 | 54GB | ~180GB（libero_90 ~125GB） |
| 并发进程 | 4×5=20 | 5×5=25 |
| 时间（~10 ep/min/进程） | ~85min | ~80-90min |
| GPU | **RTX 4090 24GB**（本机实情，Codex 2026-08-25 更正；不是 A100-80GB） | 同 |
| CPU | 13 cores / 20 proc → ~0.65 proc/core | 13 cores / 25 proc → ~0.5 proc/core |
| 磁盘余 | `/disk/rl` 还 139TB，充足 | 同 |

**风险点**：
1. libero_90 与 libero_10 重叠 7 task → SFT 阶段决策是否去重叠（cache build 不受影响）
2. 启动前需确认 `tmux sft_4in1` 是否仍在跑；25 cache 进程会争 GPU/IO
3. 触发时机：等 ckpt_2800 上传 HF 完成（#24 in_progress）后再启动
4. shard 切分 mod 余数处理：3921 % 5 = 1，最后一片多 1 ep，可忽略

**Codex 触发条件**（2026-08-25 更新）：
1. **必须等 #24 ckpt_2800 上传明确完成**（当前 6/8 distcp 已传，剩 3 个，约 25%；后台 `/tmp/hf_upload_ckpt2800_v2.sh` pid 3389240 仍在跑）
2. **sft/eval 必须全部停**（当前 sft_4in1 + spatial_cfg_4090 session 已停，GPU 24GB 完全空闲 ✓）
3. **不能用 A100 经验直接套到 4090**：25 进程共享 cuda:0 在 4090 24GB 上行不通

**Codex 4090 限流构建建议**：
- **单 VAE 进程起步**（不是 25 进程）
- **workers=0**（不是默认 36）
- **OMP_NUM_THREADS=1、MKL_NUM_THREADS=1** 起步
- **先 tiny parity 测峰值**（取 libero_90 1-2 个 episode 验证水位）
- 通过水位后再决定并发（单卡 4090 上限估计 2-4 进程，单进程 VAE encode 峰值 2-4GB，剩余给验收 server）
- GPU/IO 与验收 server **不可并发**（Codex 明确）

**Why**：cache build 必须等 ckpt_2800 上传 HF 完成（避免 GPU/IO 抢占），上传正在 30% 进度。

**How to apply**：把这一行 patch 应用到 `tools/g0/launch_parallel_cache_build.sh`，启动命令 `bash tools/g0/launch_parallel_cache_build.sh`，监控 `artifacts/g0/cache_build_shared_vae_v1_libero_90_shard_*.log`，全部完成后 `python3 tools/g0/merge_latent_cache_shards.py --output-root /disk/rl/data/LIBERO_LeRobot_v3_cosmos_exact_window_shared_vae_v1/libero_90`。

**Codex 同步**：
- 第一次（确认脚本位置）✓
- 第二次（只读审查 + 最小修改清单）✓
- 第三次（关键更正：4090 24GB + 限流建议 + 等 #24 + sft/eval 停）✓ 2026-08-25 进入 working 状态

**Why**：本机实际是 RTX 4090 24GB，不能套用 SESSION.md 里的 A100 80GB 经验。
**How to apply**：cache build 启动必须先验证 GPU 空闲 + #24 完成，然后单进程 OMP=1 + workers=0 tiny parity，水位通过后再决定并发；4in1 cache 已有 54GB，libero_90 增量约 125GB。