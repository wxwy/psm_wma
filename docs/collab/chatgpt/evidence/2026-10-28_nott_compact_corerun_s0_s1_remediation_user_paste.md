# S0/S1 证据补交 — Evidence-only remediation（GPT REQUEST_CHANGES E1/E2/R1）

- **Gate**: `V3_NOTTT_COMPACT_CORESIDENT_SECOND_JOB`
- **关联 review**: `docs/collab/chatgpt/reviews/2026-10-28_V3_NoTTT_Compact_Coresident_S0_S1_Evidence_Review.md`（verdict=`REQUEST_CHANGES`；E1/E2 MEDIUM、R1 HIGH）
- **本文件性质**: 仅补交/归档**现有原始证据**；不重跑 S1、不启动 S2、不删除任何文件（只读检查 + git 提交）
- **原始证据**: `docs/collab/chatgpt/evidence/2026-10-28_nott_compact_corerun_s0_s1.{md,json}`（本轮同步提交）
- **新 Job 命名空间（只读）**: `outputs/no_ttt_robocasa_raw15/psm_wma_v3/corrected_phase5/no_ttt_compact1_corerun_20261028_world4_ga4/`

---

## E1 — 原始证据补交（launch.json / config / env / rank0 日志）

### launch.json（完整，`launches/40ec80f5c0684bdfb5150888daae25ad/launch.json`）

```json
{
  "config_digest": "5a67adef628a0c7d91812c525d6d412bf380bf1f381ca4cc3dc4afc7f370fbc7",
  "execution_stop_after_iter": 1,
  "formal_execution_until": 1,
  "phase": "fresh",
  "semantic_digest": "a16759f8318c30ab50669f87b1ec5c990be7861fcbb51c66b9c75a70f3516f86",
  "effective_data_source": {
    "schema": "corrected_phase5_effective_data_v1",
    "observation_frames": 17, "chunk_length": 16, "action_horizon": 16, "consumer_block_steps": 16,
    "fps": 20.0, "raw_action_dim": 15, "state_dim": 15, "camera_set": "left_wrist",
    "base_encoding": "raw", "mode": "wam", "use_base_action": true, "use_state": true,
    "producer_chain": [
      "cosmos_framework.data.generator.action.datasets.robocasa_exact_window_cached_sft.get_action_robocasa_exact_window_cached_sft_dataset",
      "cosmos_framework.model.generator.mot.robocasa_exact_window_local.ExactWindowSegmentProducer",
      "cosmos_framework.trainer.matched_no_ttt.MatchedNoTTTTrainer.bind_grouped_stream"
    ]
  }
}
```

### v3_job_identity.json（关键字段）

```json
{
  "schema": "corrected_phase5_f0_v1",
  "namespace": "/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma_v3/outputs/no_ttt_robocasa_raw15/psm_wma_v3/corrected_phase5/no_ttt_compact1_corerun_20261028_world4_ga4",
  "canonical_config_sha256": {
    "config.pkl": "f69f6dcc911c15c1012cfb5f24d9cd513e58a65b1407ac1189f17ea84b56d979",
    "config.yaml": "e037840679a398fd0671d6a9aed87f0a1714193d9d12235f64c39ea163ba3f5f"
  },
  "semantic_digest": "a16759f8318c30ab50669f87b1ec5c990be7861fcbb51c66b9c75a70f3516f86",
  "semantic.contract": {"b": 8, "ga": 4, "t": 16, "k": 4, "world_size": 4, "h_pred": 16,
                        "consumer_frames": 17, "raw_action_dim": 15, "state_dim": 15},
  "semantic.training.trainer": {"max_iter": 30000, "grad_accum_iter": 4, "seed": 42,
                                "distributed_parallelism": "fsdp", "save_zero_checkpoint": false,
                                "logging_iter": 1, "validation_iter": 100, "type": "matched_no_ttt"},
  "semantic.training.scheduler": {"lr_scheduler_type": "LambdaLinear", "cycle_lengths": [30000],
                                  "warm_up_steps": [500], "f_start": [1e-06], "f_max": [1.0], "f_min": [0.0]},
  "semantic.authority.source_binding_digest": "f91b0b477a048beb439f1d73e7414f6b1d2a0307eee54c858d6cd8503ea19020",
  "semantic.authority.cache_corpus_digest": "0e0c05d09722dc7e65da868326ded3cc23a0885e4ed8841e3fbad1ab2e41fac3",
  "semantic.authority.index_receipt_sha256": "247e5a853cbc2ddd007cb4b243b492f8337179276fade9b191f6bb4fe0d5798c",
  "semantic.checkpoint": {"safety_profile": "psm_v3_sync_local_v1", "save_iter": 100, "strict_resume": true}
}
```

### rank0.log — progress + checkpoint 行（`monitor/rank0.log`）

```
[CorrectedV3][progress] [2026-10-28T08:25:22+00:00] iter=1/30000 epoch=0 LOSS outer=14.9375 action=1.2276 vision=0.2662 GRAD[rank0-shard] total=3.7072 missing=0 nonfinite=0 LOCAL slots=8 inner=n/a fast_update=n/a LR=2.500e-10 data=8.3s wall=27.2s peak=29.84GiB optimizer_committed
[CorrectedV3][checkpoint] {"checkpoint_save_ms": 14846.841583028436, "iteration": 1}
```

### train_rank0.jsonl（单行全量 telemetry，`monitor/train_rank0.jsonl`）

| 字段 | 值 |
|------|----|
| iteration / status | 1 / `optimizer_committed` |
| outer_loss / action_loss / vision_loss | 14.9374676 / 1.2275960 / 0.2661506 |
| total_grad_norm_rank_local | 3.7072084 |
| nonfinite / missing (rank0 local) | 0 / 0 |
| peak_allocated_gib / peak_reserved_gib | 25.1846352 / 29.8398438 |
| step_wall_ms / step_wall_s | 27182.9303 / 27.1829 |
| data_prepare_ms / gpu_data_stall_ms | 8629.6332 / 8292.7451（首 step 同步 producer 计时） |
| num_workers / data_wait_reason | 0 / `synchronous_producer_no_background_dataloader` |
| data_pipeline_execution | `{"compact_cached_video": true, "num_workers": 0, "state_audit_every": 100}` |
| training_profile / grad_norm_scope / loss_scope | `matched_no_ttt_v1` / rank0_local_fsdp_shard / valid_consumer_weighted |
| valid_consumers / active_slots | 512 / 8 |
| task_consumer_counts_rank_local | 8 任务 × 64（CloseBlenderLid, CloseFridge, CloseToasterOvenDoor, CoffeeSetupMug, NavigateKitchen, OpenCabinet, OpenDrawer, OpenStandMixerHead） |
| telemetry_errors | `[]` |
| ts_local | 2026-10-28T08:25:22+00:00 |

---

## E2 — 4 Rank DCP / 组件元数据 / 旧 Job 健康日志

### 每 Rank 显存峰值

- rank0: `peak_reserved_gib = 29.8398438`（telemetry 记录）
- rank1 / rank2 / rank3: **`NOT_MEASURED`** — S1 未配置 NVML/per-rank 显存采样，monitor/ 下仅有 `rank0.log` + `train_rank0.jsonl`（无 rank1-3 日志）。历史峰值不补造。

### DCP `checkpoints/iter_000000001/complete.v1.json`（完整）

```json
{
  "checkpoint": "iter_000000001", "complete": true, "schema": "psm_v3_sync_local_v1",
  "iteration": 1,
  "components": {
    "model":     {"files": {"__0_0.distcp": 3370522797, "__1_0.distcp": 3370522797, "__2_0.distcp": 3370522797, "__3_0.distcp": 3370522797},
                  "metadata": {"sha256": "992cc0da7d8658cbb8c4aa8e4e23edf4fae549a8f9850d7d86b0a6e5f9e91d84", "size": 513499}},
    "optim":     {"files": {"__0_0.distcp": 2850560422, "__1_0.distcp": 2847686572, "__2_0.distcp": 2847686572, "__3_0.distcp": 2847686572},
                  "metadata": {"sha256": "08e288ac8b455f2140e75727444dae4d1e01eb76c64c4d68e29cb8ee39f1abf7", "size": 1390710}},
    "scheduler": {"files": {"__0_0.distcp": 14506},
                  "metadata": {"sha256": "2d8f452761f2d08e008eafe881bc452da2baa820360e0fb4ea6a4a291d4c11df", "size": 2349}},
    "trainer":   {"files": {"__0_0.distcp": 28702, "__1_0.distcp": 27441, "__2_0.distcp": 27441, "__3_0.distcp": 27441},
                  "metadata": {"sha256": "a34d5080744619d8f16ad809679b105ff0e58632772404ed5b0a084ee357cac5", "size": 9534}}
  },
  "sidecars": {
    "0": {"sha256": "b0d1d38d0c8d0f49a72e3d2a9d9bb6f337623d8f5e86b9c8b4f9c41464e8c709", "size": 1150},
    "1": {"sha256": "f656697413d2b58b3b101c0c0a48cb5652b5b25c59bfd96d12de9805c71be622", "size": 1150},
    "2": {"sha256": "47f1657b661b5e348c70aae25d8fc5a909cfd97ebf20cc5380bf9b2f738e824b", "size": 1150},
    "3": {"sha256": "read_from_complete_v1_json", "size": 1150}
  },
  "world_size": 4
}
```

> 注：sidecar sha256 仅列出 0-2，rank3 项在原始文件中为完整 64 位；4 个 dataloader `rank_0..3.pkl` 各 1150B（与 sidecar size 一致）。

### 组件落盘文件（ls -la 实际大小）

| 组件 | 文件（字节） |
|------|------|
| model/ | `__0_0.distcp` 3370522797 ×4 + `.metadata` 513499 |
| optim/ | `__0_0.distcp` 2850560422 + `__1_0/2_0/3_0.distcp` 2847686572 ×3 + `.metadata` 1390710 |
| scheduler/ | `__0_0.distcp` 14506 + `__1_0/2_0/3_0.distcp` 0 ×3 + `.metadata` 2349 |
| trainer/ | `__0_0.distcp` 28702 + `__1_0/2_0/3_0.distcp` 27441 ×3 + `.metadata` 9534 |
| dataloader/ | `rank_0.pkl` 1150 ×4 |

### 旧正式 Job 健康日志（`no_ttt_packed128_droid_fresh_30k_world4_ga4/monitor/train_rank0.jsonl`，共 4955 行）

| 阶段 | iter | status | outer | peak_reserved GiB | wall_s | ts_local | telemetry_errors |
|------|------|--------|-------|-------------------|--------|----------|------------------|
| S1 前 | 4826 | optimizer_committed | 1.0401 | 35.658 | 32.8 | 08:11:14 | [] |
| S1 前 | 4827 | optimizer_committed | 1.0991 | 35.658 | 31.9 | 08:11:46 | [] |
| S1 前 | 4828 | optimizer_committed | 1.1629 | 35.658 | 32.4 | 08:12:18 | [] |
| S1 后 | 4856 | optimizer_committed | 1.1226 | 35.658 | 31.5 | 08:27:35 | [] |
| S1 后 | 4857 | optimizer_committed | 1.0361 | 35.658 | 32.5 | 08:28:08 | [] |
| S1 后 | 4858 | optimizer_committed | 1.0669 | 35.658 | 32.3 | 08:28:40 | [] |
| 当前 | 4900 | optimizer_committed | 1.0354 | 35.658 | 32.3 | 08:51:17 | [] |
| 当前 | 4926 | optimizer_committed | 1.0827 | 35.658 | 33.5 | 09:05:36 | [] |
| 当前 | 4927 | optimizer_committed | 1.1224 | 35.658 | 33.1 | 09:06:09 | [] |
| 当前 | 4928 | optimizer_committed | 0.9128 | 35.658 | 32.8 | 09:06:42 | [] |

（旧 Job 无 NaN/非有限/缺失梯度/NCCL 错误；峰值稳定 35.66GiB，与 S1 共存前后一致）

---

## R1 — 磁盘容量 / 保留 / 回退（只读检查，2026-10-28 检查时刻）

### df 现状

```
Filesystem      Size  Used Avail Use% Mounted on
/dev/nvme0n1p1  7.0T  6.5T   97G  99% /mnt/data
/dev/nvme1n1p1  7.0T  6.5T  105G  99% /mnt/data1
inodes: 234422272 total, 13320266 used, 221102006 free (6%)
```

### 两个 Job 命名空间占用

| Job | 大小 | checkpoint 现状 |
|-----|------|-----------------|
| 旧 `no_ttt_packed128_droid_fresh_30k_world4_ga4` | **93G** | `iter_000002000/3000/4000/4900`（4 个完整；latest=`iter_000004900`） |
| 新 `no_ttt_compact1_corerun_20261028_world4_ga4` | **24G** | `iter_000000001`（1 个完整） |

### Checkpoint 保留机制（已存在，当前正在运行）

- `nottt_ckpt_cleaner_loop.sh`：**运行中**（pid 2654855，每 30 分钟一轮）
- 保留规则：**latest + 整千（1000…30000）+ 未完成**，删除其余完整 checkpoint
- 已生效：旧 Job 由 6 个（2000/3000/4000/4700/4800/4900）裁剪为 4 个（2000/3000/4000/4900），删除 iter_4700/4800，释放约 47G；这正是 /mnt/data avail 由 ~51G 回升至 97G 的原因
- 配套脚本：`nottt_ckpt_cleaner.sh`（单轮，同规则）

### 容量 / 回退方案（建议，待 Owner/GPT 定夺，本文件不执行）

1. **维持 cleaner 运行**（现状）：新 Job S2 每 100 iter 约 24G/checkpoint；30k 全程按 cleaner 规则仅保留整千 ≈ 300 个 × 24G ≈ 7.2T —— **超出当前 97G avail，不可行**。长期 S2 前必须另行规划（如下）。
2. **回退选项**（只读建议，未经授权不执行）：
   - a) 新 Job 改为 `save_iter` 更大（如每 1000 iter）或将 checkpoint 写入 `/mnt/data1`（同 99%，avail 105G）；
   - b) 明确授权 cleaner 对新 Job 采用更激进保留（latest + 每 N 千）；
   - c) S2 以 10/100 阶段验证（各 1-2 个 checkpoint，增量 <48G）可先行，30k 前必须解决容量。
3. **硬边界**：旧 Job 4 个 checkpoint（93G）未获 Owner 明确授权前**不得删除**；新 Job 目前仅 1 个 checkpoint（24G），无清理需求。

---

## 约束遵守

- 全程只读检查 + git 提交证据；未启动/停止任何训练、未删改任何 Job 文件、未碰 GPU
- 未重跑 S1；未启动 S2（S2 需 GPT 复审 + Owner 明确同意）
- rank1-3 显存峰值标 `NOT_MEASURED`，未补造历史数据
- 未执行 `git reset --hard` / `checkout` / `clean` / `git -c http.sslVerify=false`