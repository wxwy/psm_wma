# DS_PRO 单轮交付包 — No-TTT Compact GPU Parity + 速度对照 + S2 就绪（2026-10-28）

> **本 md 为唯一可读入口**：A/B/C 三任务的必要证据、原始记录、元数据、结果与结论全部内嵌在此文件。其余文件（`summary.json`、`gpu_paired_harness.py`、rank JSON、raw JSONL、`complete.v1.json` 等）保留在同一目录，仅作为机器可读/可复现原件，内容与本文一致。

- **执行人/角色**: DS_PRO（运行验证；无生产代码修改）
- **请求**: `docs/collab/chatgpt/requests/2026-10-28_V3_NoTTT_Compact_OneRound_GPU_Parity_Perf_S2_Readiness_DS_PRO.md`
- **formal No-TTT Root**: `49df7f3c2e0ba8ef5871f9dd490e41fbc3dc5da9` / Child+Gitlink: `746c5cf2f2324104a62fb71510343aa40d3976c5`。当前 Root HEAD 仅作运行 provenance，不作为 formal implementation。
- **状态**: `A=RECORDED`、`B=FAIL_PARITY`（含 Dense→Dense 重放诊断：差异属固有 bf16 噪声，非 Compact 效应）、`C=READY_BY_STATIC_CHECKS`

---

## 0. 结论先行

1. **A（速度对照，只读）**: 三组 Fresh1 已原样抽取。compact1 两次 `step_wall≈25.5s/23.5s`，compact0 一次 `45.8s`。compact0 的慢主要落在 `data_prepare(30.1s)/gpu_data_stall(29.9s)`。**仅各 1 次 Fresh1/Job + GPU4–7 与旧正式 Job 共存 + 冷启动，属非稳态观测**，不据此断言 Compact=1 稳态加速。
2. **B（GPU Native Parity）**: 真实 4-Rank FSDP2 配对（同权重/同 Batch/同 RNG）。**四 rank 的 loss 在 dense0a / dense0b / compact1 三侧逐位一致**；梯度逐参数 `allclose(rtol=1e-3,atol=1e-5)` 未全通过 → 按冻结 Fail-closed 规则为 **`FAIL_PARITY`**。但 Dense→Dense 重放诊断显示：**同路径跑两次的固有 bf16 噪声本身就有 224–242/548 个参数失败**，Compact 效应失败数（225–245/548）与其统计不可区分（~80% 参数 compact 偏差 ≤ 固有噪声，median ratio=1.0，失败集合重叠 90–98%）→ **未发现 Compact 特有梯度分歧信号**。
3. **C（S2 Resume 静态就绪）**: `no_ttt_compact1_corerun_20261028_world4_ga4` 的 `latest_checkpoint.txt→iter_000000001`、`complete.v1.json`（schema/complete/iteration=1/world_size=4/四组件 metadata）、`dataloader/rank_0..3.pkl`、`v3_job_identity.json`（semantic_digest/config digest/save_iter=100/source_paths 全存在）齐全 → **`READY_BY_STATIC_CHECKS`**。未执行真实 DCP restore 重放，未重做强 hash 验真。

---

## 1. A — 三次 Fresh1 速度对照（只读，iter=1）

### 1.1 身份核对（三 Job 一致）

| 字段 | 值 |
|---|---|
| `config_digest`（launch.json） | `5a67adef628a0c7d91812c525d6d412bf380bf1f381ca4cc3dc4afc7f370fbc7`（三 Job 相同） |
| `semantic_digest` | `a16759f8318c30ab50669f87b1ec5c990be7861fcbb51c66b9c75a70f3516f86`（三 Job 相同） |
| `actual_consumer_identity_sha256` | `9207fc67ae9504387de5b866c60dc5023a0b13ef76ed7109813b41115c3e7830`（三 Job 相同） |
| 基础 checkpoint / source cache index / precision | DROID `Cosmos3-Edge-Policy-DROID-dcp` / verified-index-r1 / bfloat16（三 Job 相同） |
| 有效 world4-GA4 | B8/T16/K4/GA4/world4（三 Job 相同） |
| `PSM_V3_COMPACT_CACHED_VIDEO` | A/C=1、B=0（唯一差异） |
| `num_workers` | 0（三 Job；`no_ttt_loader_workers` 未在 telemetry 记录，launcher 默认 0） |

### 1.2 对照表（monitor/train_rank0.jsonl，iter=1，单位 ms）

| 指标 | A compact1 | B compact0 | C compact1_r2 | 备注 |
|---|---:|---:|---:|---|
| `step_wall_ms` | 25523.09 | 45806.41 | 23482.17 | B vs median(A,C)=24502.63 → **1.87×** |
| `data_prepare_ms` | 9149.39 | 30127.76 | 6888.70 | B vs median(A,C)=8019.04 → **3.76×** |
| `gpu_data_stall_ms` | 8981.40 | 29934.68 | 6704.73 | B vs median(A,C)=7843.07 → **3.82×** |
| `batch_collate_ms` | 60.80 | 36.10 | 48.18 | 记录 |
| `batch_transfer_ms` | 176.11 | 352.13 | 507.67 | 记录 |
| `forward_ms` | 7513.27 | 7944.15 | 8792.42 | 记录 |
| `backward_ms` | 8192.30 | 7060.46 | 6972.70 | 记录 |
| `optimizer_ms` | 51.09 | 42.59 | 43.36 | 记录 |
| `other_host_overhead_ms` | 380.12 | 243.23 | 229.14 | 记录 |
| `source_read_ms` | NOT_RECORDED | NOT_RECORDED | NOT_RECORDED | 未采集 |
| `valid_consumers` | 512 | 512 | 512 | 8任务×64 |
| `native_forward/backward_calls` | 4/4 | 4/4 | 4/4 | 记录 |
| `outer_loss` | 14.937467575073242 | 14.937467575073242 | 14.937467575073242 | 逐位一致 |
| `action_loss` | 1.2275960445404053 | 同 | 同 | 逐位一致 |
| `vision_loss` | 0.2661505937576294 | 同 | 同 | 逐位一致 |
| `total_grad_norm_rank_local` | 3.706259250640869 | 3.7076737880706787 | 3.7086875438690186 | 0.038%/0.065% 漂移 |
| `peak_allocated_gib` | 25.18 | 25.57 | 25.18 | 记录 |
| `peak_reserved_gib` | 29.84 | 30.68 | 29.84 | compact0 略高（保留实像素张量） |
| `telemetry_errors` | [] | [] | [] | 无 |

> **明确边界**: 每 Job 仅一次 Fresh1、GPU4–7 与旧正式 No-TTT 共存、冷启动/竞争存在。**不得**据此得出稳态加速结论；不为取得稳态新启动 10/100 步实验。旧正式 NoTTT 同时间段 Step Wall 分布可另附只读备注，但不能当作同权重 Compact0 对照。

### 1.3 A 三 Job 原始记录（iter=1 全字段原文）

**A = `no_ttt_compact1_gpu_parity_world4_ga4`**（`compact_cached_video=true`，`status=optimizer_committed`，ts `2026-10-28T10:59:03+00:00`）

```json
{
  "iteration": 1, "rank": 0, "epoch": 0,
  "step_wall_ms": 25523.08569289744, "step_wall_s": 25.52308569289744,
  "step_wall_scope": "first_trigger_to_post_commit_excludes_checkpoint",
  "data_prepare_ms": 9149.389371275902,
  "batch_collate_ms": 60.80031022429466, "batch_transfer_ms": 176.1079505085945,
  "forward_ms": 7513.272438198328, "backward_ms": 8192.298652604222,
  "optimizer_ms": 51.09410174190998, "other_host_overhead_ms": 380.12286834418774,
  "gpu_data_stall_ms": 8981.404524803162, "gpu_data_stall_status": "ready",
  "data_pipeline_execution": {"compact_cached_video": true, "num_workers": 0,
    "rank_shared_episode_reader": false, "state_audit_every": 100},
  "data_wait_reason": "synchronous_producer_no_background_dataloader",
  "valid_consumers": 512, "valid_consumers_per_second_rank_local": 20.06,
  "actual_consumer_identity_count": 512,
  "actual_consumer_identity_sha256": "9207fc67ae9504387de5b866c60dc5023a0b13ef76ed7109813b41115c3e7830",
  "native_forward_calls": 4, "native_backward_calls": 4,
  "outer_loss": 14.937467575073242, "action_loss": 1.2275960445404053,
  "vision_loss": 0.2661505937576294,
  "action_contribution": 12.275960445404053, "vision_contribution": 2.661505937576294,
  "flow_matching_loss_action": 1.2275960445404053,
  "flow_matching_loss_vision": 0.2661505937576294,
  "total_grad_norm_rank_local": 3.706259250640869,
  "total_grad_tensor_count_rank_local": 294,
  "generation_grad_norm_rank_local": 3.706259250640869, "generation_grad_tensor_count_rank_local": 294,
  "missing_grad_tensors_rank_local": 0, "nonfinite_grad_tensors_rank_local": 0,
  "peak_allocated_gib": 25.184635162353516, "peak_reserved_gib": 29.83984375,
  "lr_max": 2.5e-10, "lr_min": 5.0e-11, "telemetry_errors": [],
  "task_consumer_counts_rank_local": {"CloseBlenderLid": 64, "CloseFridge": 64,
    "CloseToasterOvenDoor": 64, "CoffeeSetupMug": 64, "NavigateKitchen": 64,
    "OpenCabinet": 64, "OpenDrawer": 64, "OpenStandMixerHead": 64},
  "native_batch_layout": "v2_a2_slot_major_packed_member",
  "local_memory_enabled": false, "full_segment_prefetch": false,
  "training_profile": "matched_no_ttt_v1", "loss_scope": "valid_consumer_weighted",
  "grad_norm_scope": "rank0_local_fsdp_shard", "consumer_audit_status": "OBSERVED"
}
```

**B = `no_ttt_compact0_gpu_parity_world4_ga4`**（`compact_cached_video=false`，`status=optimizer_committed`，ts `2026-10-28T11:06:17+00:00`）

```json
{
  "iteration": 1, "rank": 0, "epoch": 0,
  "step_wall_ms": 45806.40850774944, "step_wall_s": 45.80640850774944,
  "step_wall_scope": "first_trigger_to_post_commit_excludes_checkpoint",
  "data_prepare_ms": 30127.756906673312,
  "batch_collate_ms": 36.09652817249298, "batch_transfer_ms": 352.1300610154867,
  "forward_ms": 7944.145245477557, "backward_ms": 7060.457045212388,
  "optimizer_ms": 42.58906841278076, "other_host_overhead_ms": 243.23365278542042,
  "gpu_data_stall_ms": 29934.68492078781, "gpu_data_stall_status": "ready",
  "data_pipeline_execution": {"compact_cached_video": false, "num_workers": 0,
    "rank_shared_episode_reader": false, "state_audit_every": 100},
  "data_wait_reason": "synchronous_producer_no_background_dataloader",
  "valid_consumers": 512, "valid_consumers_per_second_rank_local": 11.18,
  "actual_consumer_identity_count": 512,
  "actual_consumer_identity_sha256": "9207fc67ae9504387de5b866c60dc5023a0b13ef76ed7109813b41115c3e7830",
  "native_forward_calls": 4, "native_backward_calls": 4,
  "outer_loss": 14.937467575073242, "action_loss": 1.2275960445404053,
  "vision_loss": 0.2661505937576294,
  "action_contribution": 12.275960445404053, "vision_contribution": 2.661505937576294,
  "total_grad_norm_rank_local": 3.7076737880706787,
  "total_grad_tensor_count_rank_local": 294,
  "generation_grad_norm_rank_local": 3.7076737880706787, "generation_grad_tensor_count_rank_local": 294,
  "missing_grad_tensors_rank_local": 0, "nonfinite_grad_tensors_rank_local": 0,
  "peak_allocated_gib": 25.571489334106445, "peak_reserved_gib": 30.6796875,
  "lr_max": 2.5e-10, "lr_min": 5.0e-11, "telemetry_errors": [],
  "task_consumer_counts_rank_local": {"CloseBlenderLid": 64, "CloseFridge": 64,
    "CloseToasterOvenDoor": 64, "CoffeeSetupMug": 64, "NavigateKitchen": 64,
    "OpenCabinet": 64, "OpenDrawer": 64, "OpenStandMixerHead": 64},
  "native_batch_layout": "v2_a2_slot_major_packed_member",
  "local_memory_enabled": false, "full_segment_prefetch": false,
  "training_profile": "matched_no_ttt_v1", "loss_scope": "valid_consumer_weighted",
  "grad_norm_scope": "rank0_local_fsdp_shard", "consumer_audit_status": "OBSERVED"
}
```

**C = `no_ttt_compact1_gpu_parity_r2_world4_ga4`**（`compact_cached_video=true`，`status=optimizer_committed`，ts `2026-10-28T11:13:32+00:00`）

```json
{
  "iteration": 1, "rank": 0, "epoch": 0,
  "step_wall_ms": 23482.16939345002, "step_wall_s": 23.48216939345002,
  "step_wall_scope": "first_trigger_to_post_commit_excludes_checkpoint",
  "data_prepare_ms": 6888.700436800718,
  "batch_collate_ms": 48.18391799926758, "batch_transfer_ms": 507.6713003218174,
  "forward_ms": 8792.424239218235, "backward_ms": 6972.6952612400055,
  "optimizer_ms": 43.35617460310459, "other_host_overhead_ms": 229.13806326687336,
  "gpu_data_stall_ms": 6704.730309963226, "gpu_data_stall_status": "ready",
  "data_pipeline_execution": {"compact_cached_video": true, "num_workers": 0,
    "rank_shared_episode_reader": false, "state_audit_every": 100},
  "data_wait_reason": "synchronous_producer_no_background_dataloader",
  "valid_consumers": 512, "valid_consumers_per_second_rank_local": 21.80,
  "actual_consumer_identity_count": 512,
  "actual_consumer_identity_sha256": "9207fc67ae9504387de5b866c60dc5023a0b13ef76ed7109813b41115c3e7830",
  "native_forward_calls": 4, "native_backward_calls": 4,
  "outer_loss": 14.937467575073242, "action_loss": 1.2275960445404053,
  "vision_loss": 0.2661505937576294,
  "action_contribution": 12.275960445404053, "vision_contribution": 2.661505937576294,
  "total_grad_norm_rank_local": 3.7086875438690186,
  "total_grad_tensor_count_rank_local": 294,
  "generation_grad_norm_rank_local": 3.7086875438690186, "generation_grad_tensor_count_rank_local": 294,
  "missing_grad_tensors_rank_local": 0, "nonfinite_grad_tensors_rank_local": 0,
  "peak_allocated_gib": 25.184635162353516, "peak_reserved_gib": 29.83984375,
  "lr_max": 2.5e-10, "lr_min": 5.0e-11, "telemetry_errors": [],
  "task_consumer_counts_rank_local": {"CloseBlenderLid": 64, "CloseFridge": 64,
    "CloseToasterOvenDoor": 64, "CoffeeSetupMug": 64, "NavigateKitchen": 64,
    "OpenCabinet": 64, "OpenDrawer": 64, "OpenStandMixerHead": 64},
  "native_batch_layout": "v2_a2_slot_major_packed_member",
  "local_memory_enabled": false, "full_segment_prefetch": false,
  "training_profile": "matched_no_ttt_v1", "loss_scope": "valid_consumer_weighted",
  "grad_norm_scope": "rank0_local_fsdp_shard", "consumer_audit_status": "OBSERVED"
}
```

---

## 2. B — 真正 4-Rank FSDP2 配对 Native Parity（本轮唯一 GPU 实验）

### 2.1 环境与合同遵守

- venv: `psm_wma/cosmos-framework/.venv/bin/python`，torch **2.10.0+cu128**，cuda 12.8，H100 80GB×4（`CUDA_VISIBLE_DEVICES=4,5,6,7`，与旧正式 No-TTT **共存**）。
- 真实 Native: `OmniMoTModel`，`local_memory_enabled=False`，FSDP2 `data_parallel_shard_degree=4`，bfloat16，selective activation checkpointing，compile disabled；模型 `train()`；`model.training_step(batch, 1000)`（正式 Native 实现）。
- DROID Base DCP 只读加载（`missing=0/unexpected=0`），单进程生命周期同一权重/缓冲区。
- 冻结计划: `ExactWindowRankPlanner(rank=RANK, world4, B8, T16, GA4, seed=0)` 取 `plan.members[0]`（每 rank 128 valid Consumers，归一权重 ≈ 0.25）；两侧 CPU Native Packed Batch 先冻结（`plan.members_eq=True`）。
- 顺序 **dense0a → dense0b（固有噪声对照）→ compact1（效应）**；每侧前恢复 Python/NumPy/TorchCPU/CUDA per-rank RNG，`zero_grad(set_to_none=True)`，核实权重/缓冲区未变。
- 遍历全部 `GENERATION_KEYS` 可训练参数（rank-local 294，覆盖 7 组：moe_gen 281 / time_embedder 4 / action2llm 2 / llm2action 2 / llm2vae 2 / vae2llm 2 / action_modality_embed 1）；FSDP `DTensor.to_local` 取每 rank 分片；`torch.allclose(rtol=1e-3,atol=1e-5)`，保存 max_abs/rel_l2/worst10/group counts。
- **未执行** `optimizer.step` / `scheduler.step` / `grad_scaler.step` / `checkpointer.save`；不写模型/DCP/Job Identity；不改生产代码。

### 2.2 结果（四 rank 汇总）

| rank | 计划成员一致 | DCP missing/unexpected | dense0a loss | dense0b loss | compact1 loss | loss_eq(noise/effect) | 固有噪声失败 | Compact效应失败 | excess_positive/548 | ratio_med | ratio_max | verdict |
|---:|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---|
| 0 | True | 0/0 | 15.290846 | 15.290846 | 15.290846 | True/True | 224 | 225 | 115 | 1.0 | 4.0 | FAIL_PARITY |
| 1 | True | 0/0 | 15.298787 | 15.298787 | 15.298787 | True/True | 242 | 235 | 98 | 1.0 | 32.0 | FAIL_PARITY |
| 2 | True | 0/0 | 14.900201 | 14.900201 | 14.900201 | True/True | 227 | 229 | 99 | 1.0 | 8.0 | FAIL_PARITY |
| 3 | True | 0/0 | 15.045044 | 15.045044 | 15.045044 | True/True | 238 | 245 | 110 | 1.0 | 8.0 | FAIL_PARITY |

- 梯度张量总数（dense 侧 CPU 收集）: **548**（含 rank-local 294 与 FSDP 全分片计数口径）。
- 每 rank 的 `intrinsic_noise`（dense0a vs dense0b）与 `compact_effect`（dense0a vs compact1）**group-level pass 数完全一致**（rank0 示例: moe_gen 150/281、time_embedder 0/4、vae2llm 0/2、action_modality_embed 0/1、action2llm 2/2、llm2action 2/2、llm2vae 2/2、vae2llm 0/2）。

### 2.3 失败集合重叠（固有噪声 vs Compact 效应，逐 rank）

| rank | 噪声失败(全) | 效应失败(全) | top-50 交集 | 仅效应独有(top-50) | 仅噪声独有(top-50) | 重叠率(top-50) |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 224 | 225 | 49 | 1 | 1 | 98% |
| 1 | 242 | 235 | 45 | 5 | 5 | 90% |
| 2 | 227 | 229 | 46 | 4 | 4 | 92% |
| 3 | 238 | 245 | 47 | 3 | 3 | 94% |

> `failures` 列表在 JSON 中截取 top-50 样本（`failure_count` 为全量真实数）；上表交集按 top-50 样本统计。仅效应独有的参数是随机零星项（如 rank1 的 `layers.0.self_attn.k_proj.weight` 等），不构成系统性模块差异。

### 2.4 量级（rank0 worst10，`max_abs` / `rel_l2`）

| 方向 | worst 参数 | max_abs | rel_l2 |
|---|---:|---:|---:|
| 噪声 | `layers.1.self_attn.v_proj.weight` | 9.766e-04 | 0.0036 |
| 噪声 | `embed_tokens.weight` | 4.883e-04 | 0.0044 |
| 噪声 | `layers.0.self_attn.v_proj.weight` | 4.883e-04 | 0.0039 |
| 噪声 | `layers.1.mlp.down_proj.weight` | 4.883e-04 | 0.0034 |
| 效应 | `embed_tokens.weight` | 9.766e-04 | 0.0061 |
| 效应 | `layers.0.self_attn.v_proj.weight` | 4.883e-04 | 0.0040 |
| 效应 | `layers.1.mlp.down_proj.weight` | 4.883e-04 | 0.0034 |
| 效应 | `layers.1.self_attn.v_proj.weight` | 4.883e-04 | 0.0031 |

> 两侧 worst10 参数集合与量级高度重合（同一批层/同一 ULP 量级），进一步佐证 Compact 效应落在噪声带内。

### 2.5 判定与诊断解读

- 按冻结合同 Fail-closed: 四 rank 全部通过才 `PASS_CANDIDATE`；有 grad 差异即 `FAIL_PARITY`，允许**一次** Dense→Dense 重放诊断（本轮即 `dense0a vs dense0b`）。
- **诊断结论**: 同路径 dense→dense 重放本身就有 224–242/548 参数在严格 allclose 下失败 → **严格 tolerance 在 bf16 backward + FSDP2 下本就不可达**；Compact 效应失败数（225–245）与其重叠在噪声带内；~80% 参数 compact 偏差 ≤ 固有噪声（excess_positive 仅 98–115/548），median ratio=1.0 → **没有 Compact 特有梯度分歧信号**。
- **状态固定**: `B=FAIL_PARITY`（不因诊断自动升级为 PASS_CANDIDATE；不自行宣称 formal Gate CLOSED）。
- 边界: 未做 >1 iter 长程；未在正式 NoTTT Checkpoint 边界切换 Compact；未触碰旧正式 Job / GPU0–3；未停止/修改旧 Job。

---

## 3. C — S2 新 Job Resume 静态就绪检查（只读，不执行 Resume）

- 目标 Job（**正确身份**）: `no_ttt_compact1_corerun_20261028_world4_ga4`（Compact=1，fresh 1 成功，`status=optimizer_committed`）。**不是** 旧的 `no_ttt_packed128_droid_fresh_30k_world4_ga4`。

| 检查项 | 结果 |
|---|---|
| `latest_checkpoint.txt` | `iter_000000001` ✅ |
| `complete.v1.json` | schema=`psm_v3_sync_local_v1`，`complete=true`，`iteration=1`，`world_size=4` ✅ |
| 组件 metadata | model `992cc0da…`(4 files) / optim `08e288ac…`(4) / scheduler `2d8f4527…`(1) / trainer `a34d5080…`(4) ✅ |
| 4-rank sidecar SHA（从文件原样读取） | `0=b0d1d38d…709`, `1=f6566974…622`, `2=47f1657b…24b`, `3=ab1ce5d4…84f`（各 1150B）✅ |
| `dataloader/rank_0..3.pkl` | 4 个均存在（各 1150B）✅ |
| `v3_job_identity.json` | schema=`corrected_phase5_f0_v1`，semantic_digest=`a16759f8…`，`save_iter=100`，config.pkl/yaml sha 记录 ✅ |
| 运行 PYTHON / Compact | psm_wma venv（torch2.10+cu128）；`compact_cached_video=True`（telemetry）✅ |
| `NOTTT_LOADER_WORKERS` | 未在配置/telemetry 记录；launcher 默认 0（`num_workers=0`）✅ |
| `OUTPUT/SOURCE/CACHE/INDEX/EDGE/VAE/BASE` 7 路径 | **全部存在**（source_paths 六项 + OUTPUT）✅ |
| 覆盖旧 Namespace | 未新建 Fresh；无覆盖动作 ✅ |

- **S2_READINESS = `READY_BY_STATIC_CHECKS`**。
- 边界: 只做静态元数据/存在性检查；**未执行真实 DCP restore 重放**、未对 24GB DCP 全量重 hash 验真；不审查磁盘/Cleaner retention；`READY` 不等于许可继续训练。

### 3.1 C 关键元数据原文

**`latest_checkpoint.txt`**: `iter_000000001`

**`complete.v1.json` 全文**:（原样拷贝）

```json
{
  "checkpoint": "iter_000000001",
  "complete": true,
  "components": {
    "model": {
      "files": {"__0_0.distcp": 3370522797, "__1_0.distcp": 3370522797, "__2_0.distcp": 3370522797, "__3_0.distcp": 3370522797},
      "metadata": {"sha256": "992cc0da7d8658cbb8c4aa8e4e23edf4fae549a8f9850d7d86b0a6e5f9e91d84", "size": 513499}
    },
    "optim": {
      "files": {"__0_0.distcp": 2850560422, "__1_0.distcp": 2847686572, "__2_0.distcp": 2847686572, "__3_0.distcp": 2847686572},
      "metadata": {"sha256": "08e288ac8b455f2140e75727444dae4d1e01eb76c64c4d68e29cb8ee39f1abf7", "size": 1390710}
    },
    "scheduler": {
      "files": {"__0_0.distcp": 14506},
      "metadata": {"sha256": "2d8f452761f2d08e008eafe881bc452da2baa820360e0fb4ea6a4a291d4c11df", "size": 2349}
    },
    "trainer": {
      "files": {"__0_0.distcp": 28702, "__1_0.distcp": 27441, "__2_0.distcp": 27441, "__3_0.distcp": 27441},
      "metadata": {"sha256": "a34d5080744619d8f16ad809679b105ff0e58632772404ed5b0a084ee357cac5", "size": 9534}
    }
  },
  "iteration": 1,
  "schema": "psm_v3_sync_local_v1",
  "sidecars": {
    "0": {"sha256": "b0d1d38d0c8d0f49a72e3d2a9d9bb6f337623d8f5e86b9c8b4f9c41464e8c709", "size": 1150},
    "1": {"sha256": "f656697413d2b58b3b101c0c0a48cb5652b5b25c59bfd96d12de9805c71be622", "size": 1150},
    "2": {"sha256": "47f1657b661b5e348c70aae25d8fc5a909cfd97ebf20cc5380bf9b2f738e824b", "size": 1150},
    "3": {"sha256": "ab1ce5d459ce145f461221d99f8e45ba8e994068bac47460cb87c8f959493f84", "size": 1150}
  },
  "world_size": 4
}
```

**`v3_job_identity.json` 关键字段**:（完整原文在同目录 `task_c_s2_resume/v3_job_identity.json`）

```json
{
  "canonical_config_sha256": {"config.pkl": "f69f6dcc911c15c1012cfb5f24d9cd513e58a65b1407ac1189f17ea84b56d979",
    "config.yaml": "e037840679a398fd0671d6a9aed87f0a1714193d9d12235f64c39ea163ba3f5f"},
  "child": "nottt_world4_ga4_source_head_not_verified",
  "diagnostic_only_do_not_resume": false,
  "namespace": ".../outputs/no_ttt_robocasa_raw15/psm_wma_v3/corrected_phase5/no_ttt_compact1_corerun_20261028_world4_ga4",
  "native_batch_layout": "v2_a2_member_packed_slot_major_v1",
  "root": "nottt_world4_ga4_source_head_not_verified",
  "schema": "corrected_phase5_f0_v1",
  "semantic": {
    "authority": {"cache_corpus_digest": "0e0c05d09722dc7e65da868326ded3cc23a0885e4ed8841e3fbad1ab2e41fac3",
      "cache_manifest_sha256": "8e63c73b4e07cdbebd6427d9efdd3f2d8b293ecd10511cae25a55c6566f6db88",
      "model_witnesses": {"base_model_metadata_sha256": "cf0c23404efb0bf78c163a85d3800d6163cbbcd5478401feb6cc93f5715a88fa",
        "edge_config_sha256": "a9381d094679851e1465c6f8236ddc672ba15b54ba93daf8c07115cb93a35553"},
      "source_binding_digest": "f91b0b477a048beb439f1d73e7414f6b1d2a0307eee54c858d6cd8503ea19020",
      "transform_rng_mode": "legacy_global"},
    "checkpoint": {"safety_profile": "psm_v3_sync_local_v1", "save_iter": 100, "strict_resume": true},
    "contract": {"b": 8, "consumer_frames": 17, "ga": 4, "h_pred": 16, "k": 4, "raw_action_dim": 15,
      "state_dim": 15, "t": 16, "world_size": 4},
    "index_receipt_sha256": "247e5a853cbc2ddd007cb4b243b492f8337179276fade9b191f6bb4fe0d5798c",
    "rng": {"deterministic_algorithms": false, "seed_by_rank": true},
    "source_paths": {"base_checkpoint": ".../models/Cosmos3-Edge-Policy-DROID-dcp",
      "cache_root": ".../datasets/robocasa365-target-atomic-left_wrist-exact_window",
      "dataset_index_root": ".../datasets/robocasa365-target-atomic-verified-index-r1",
      "edge": ".../models/Cosmos3-Edge-Policy-DROID",
      "source_root": "/mnt/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic",
      "vae": ".../models/Wan2.2-TI2V-5B/Wan2.2_VAE.pth"},
    "training": {"data_setting": {"qwen_max_video_token_length": 8192},
      "model": {"config": {"local_memory_enabled": false, "precision": "bfloat16",
        "activation_checkpointing": {"mode": "selective", "preserve_rng_state": true},
        "compile": {"enabled": false}, "parallelism": {"data_parallel_shard_degree": 4,
        "fsdp_master_dtype": "float32", "fsdp_reduce_dtype": "bfloat16"},
        "tokenizer": {"vae_path": ".../models/Wan2.2-TI2V-5B/Wan2.2_VAE.pth"}}},
      "optimizer": {"keys_to_select": ["moe_gen", "time_embedder", "vae2llm", "llm2vae",
        "action2llm", "llm2action", "action_modality_embed"], "lr": 5e-05,
        "optimizer_type": "FusedAdam", "weight_decay": 0.05},
      "scheduler": {"lr_scheduler_type": "LambdaLinear", "warm_up_steps": [500],
        "cycle_lengths": [30000]},
      "trainer": {"type": "cosmos_framework.trainer.matched_no_ttt.MatchedNoTTTTrainer",
        "grad_accum_iter": 4, "max_iter": 30000, "seed": 42, "distributed_parallelism": "fsdp",
        "grad_scaler_args": {"enabled": false}}},
    "training_profile": "matched_no_ttt_v1"
  },
  "semantic_digest": "a16759f8318c30ab50669f87b1ec5c990be7861fcbb51c66b9c75a70f3516f86"
}
```

**`dataloader/rank_0..3.pkl`**: 4 文件均存在，各 1150 字节。

### 3.2 Resume 命令草案（**仅供 Owner/GPT 审阅，本轮不执行**）

```bash
PYTHON=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/cosmos-framework/.venv/bin/python
cd /mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma_v3/cosmos-framework
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PSM_V3_COMPACT_CACHED_VIDEO=1 \
CUDA_VISIBLE_DEVICES=4,5,6,7 $PYTHON scripts/train_v3_matched_no_ttt_4gpu.sh \
  --job-name no_ttt_compact1_corerun_20261028_world4_ga4 \
  --phase resume \
  --output-root /mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma_v3/outputs/no_ttt_robocasa_raw15 \
  --source-root /mnt/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic \
  --cache-root /mnt/data/shenzhen/szrobot/logs/.tmp_backup/datasets/robocasa365-target-atomic-left_wrist-exact_window \
  --dataset-index-root /mnt/data/shenzhen/szrobot/logs/.tmp_backup/datasets/robocasa365-target-atomic-verified-index-r1 \
  --edge /mnt/data/shenzhen/szrobot/logs/.tmp_backup/models/Cosmos3-Edge-Policy-DROID \
  --vae /mnt/data/shenzhen/szrobot/logs/.tmp_backup/models/Wan2.2-TI2V-5B/Wan2.2_VAE.pth \
  --base-checkpoint /mnt/data/shenzhen/szrobot/logs/.tmp_backup/models/Cosmos3-Edge-Policy-DROID-dcp
```

> ⚠️ 这是**草案**：launcher 确切 flag 名（`--phase resume` / `--job-name` 等）需 Owner/GPT 依据正式 `scripts/train_v3_matched_no_ttt_4gpu.sh` 复核后再定；本轮**未执行**任何 Resume，也未自行启动 S2 `resume 10/100/30000`。

---

## 4. 交付物清单（本包路径 `docs/collab/chatgpt/evidence/2026-10-28_V3_NoTTT_Compact_OneRound/`）

- `summary.md`（本文件，自包含可读入口）。
- `summary.json`（机器可读：A_perf_rows / B_gpu_parity / C_s2_readiness，与本文一致）。
- `gpu_paired_harness.py`（B 可复现脚本，原样）。
- `gpu_parity_rank_jsonl/v3_gpu_parity_rank{0..3}.json`（B 四 rank 原始结果：worst10 / failures top-50 / group_stats / dcp_load / plan / catalog / diagnostic）+ 分析脚本 `analyze_parity.py`、`analyze_diag.py`。
- `task_a_raw_jsonl/{compact1,compact0,compact1_r2}.jsonl`（A 三 Job 原始 iter=1 记录原文）。
- `task_c_s2_resume/`（`latest_checkpoint.txt`、`complete.v1.json`、`v3_job_identity.json` 原样副本）。
- 顺带归档: `docs/collab/chatgpt/evidence/2026-10-28_nott_compact_corerun_s0_s1.{md,json}`（此前已有，非阻塞项）。

## 5. 剩余问题与后续

1. B 的严格 per-param allclose 在 bf16 下不可达——如需“数值等价”Gate，需 Owner/GPT 决定是否以噪声带校准的统计判据（如本诊断的 excess/ratio）替代严格 allclose，或接受 loss 逐位一致 + 梯度噪声不可区分的结论。
2. C 为静态就绪，真实 DCP restore 可恢复性未实测；Resume 命令 flag 待 Owner/GPT 复核。
3. A 为非稳态单次观测，稳态速度结论需正式 S2 长训的 monitor 数据，本轮未启动。
4. 未自行启动 S2 resume、未切换旧 Job Compact、未停旧 Job、未修改生产代码/配置/Cleaner。