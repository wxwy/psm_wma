# DS_PRO 单轮交付包 — No-TTT Compact GPU Parity + 速度对照 + S2 就绪（2026-10-28）

> 
> **本 md 为唯一可读入口**：A/B/C 三任务的必要证据、原始记录、元数据、结果与结论全部内嵌在此文件。其余文件（`summary.json`、`gpu_paired_harness.py`、rank JSON、raw JSONL、`complete.v1.json` 等）保留在同一目录，仅作为机器可读/可复现原件，内容与本文一致。

- **执行人/角色**: DS_PRO（运行验证；无生产代码修改）
- **请求**: `docs/collab/chatgpt/requests/2026-10-28_V3_NoTTT_Compact_OneRound_GPU_Parity_Perf_S2_Readiness_DS_PRO.md`
- **formal No-TTT Root**: `49df7f3c2e0ba8ef5871f9dd490e41fbc3dc5da9` / Child+Gitlink: `746c5cf2f2324104a62fb71510343aa40d3976c5`。当前 Root HEAD 仅作运行 provenance，不作为 formal implementation。
- **状态**: `A=RECORDED`、`B=FAIL_PARITY`（含 Dense→Dense 重放诊断：差异属固有 bf16 噪声，非 Compact 效应）、`C=READY_BY_STATIC_CHECKS`

---

## 0. 结论先行

1. **A（速度对照，只读）**: 三组 Fresh1 已原样抽取。compact1 两次 `step_wall≈25.5s/23.5s`，compact0 一次 `45.8s`。compact0 的慢主要落在 `data_prepare(30.1s)/gpu_data_stall(29.9s)`。**仅各 1 次 Fresh1/Job + GPU4–7 与旧正式 Job 共存 + 冷启动，属非稳态观测**，不据此断言 Compact=1 稳态加速。
2. **B（GPU Native Parity）**: 真实 4-Rank FSDP2 配对（同权重/同 Batch/同 RNG）。**四 rank 的 loss 在 dense0a / dense0b / compact1 三侧逐位一致**；梯度逐参数 `allclose(rtol=1e-3,atol=1e-5)` 未全通过 → 按冻结 Fail-closed 规则为 **`FAIL_PARITY`**。但 Dense→Dense 重放诊断显示：**同路径跑两次的固有 bf16 噪声本身就有 224–242/548 个参数失败**，Compact 效应失败数（225–245/548）与其统计不可区分（~80% 参数 compact 偏差 ≤ 固有噪声，median ratio=1.0，失败集合重叠 90–98%）→ **未发现 Compact 特有梯度分歧信号**（⚠️ 18%–21% 对象 Compact 偏差>Dense 重放偏差，此仅为统计支持的假设，非已验证严格结论，见 §2.5）。
3. **C（S2 Resume 静态就绪）**: `no_ttt_compact1_corerun_20261028_world4_ga4` 的 `latest_checkpoint.txt→iter_000000001`、`complete.v1.json`（schema/complete/iteration=1/world_size=4/四组件 metadata）、`dataloader/rank_0..3.pkl`、`v3_job_identity.json`（semantic_digest/config digest/save_iter=100/source_paths 全存在）齐全 → **`READY_BY_STATIC_CHECKS`**。未执行真实 DCP restore 重放，未重做强 hash 验真。

---

## 1. A — 三次 Fresh1 速度对照（只读，iter=1）

### 1.1 身份核对（三 Job 一致）

| 字段 | 值 |
| --- | --- |
| `config_digest`（launch.json） | `5a67adef628a0c7d91812c525d6d412bf380bf1f381ca4cc3dc4afc7f370fbc7`（三 Job 相同） |
| `semantic_digest` | `a16759f8318c30ab50669f87b1ec5c990be7861fcbb51c66b9c75a70f3516f86`（三 Job 相同） |
| `actual_consumer_identity_sha256` | `9207fc67ae9504387de5b866c60dc5023a0b13ef76ed7109813b41115c3e7830`（三 Job 相同） |
| 基础 checkpoint / source cache index / precision | DROID `Cosmos3-Edge-Policy-DROID-dcp` / verified-index-r1 / bfloat16（三 Job 相同） |
| 有效 world4-GA4 | B8/T16/K4/GA4/world4（三 Job 相同） |
| `PSM_V3_COMPACT_CACHED_VIDEO` | A/C=1、B=0（唯一差异） |
| `num_workers` | 0（三 Job；`no_ttt_loader_workers` 未在 telemetry 记录，launcher 默认 0） |

### 1.2 对照表（monitor/train_rank0.jsonl，iter=1，单位 ms）

| 指标 | A compact1 | B compact0 | C compact1_r2 | 备注 |
| --- | --- | --- | --- | --- |
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

> 
> **明确边界**: 每 Job 仅一次 Fresh1、GPU4–7 与旧正式 No-TTT 共存、冷启动/竞争存在。**不得**据此得出稳态加速结论；不为取得稳态新启动 10/100 步实验。旧正式 NoTTT 同时间段 Step Wall 分布可另附只读备注，但不能当作同权重 Compact0 对照。

### 1.3 A 三 Job 原始记录（iter=1 全字段原文）

**A = `no_ttt_compact1_gpu_parity_world4_ga4`**（`compact_cached_video=true`，`status=optimizer_committed`，ts `2026-10-28T10:59:03+00:00`）

```
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

```
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

```
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
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | True | 0/0 | 15.290846 | 15.290846 | 15.290846 | True/True | 224 | 225 | 115 | 1.0 | 4.0 | FAIL_PARITY |
| 1 | True | 0/0 | 15.298787 | 15.298787 | 15.298787 | True/True | 242 | 235 | 98 | 1.0 | 32.0 | FAIL_PARITY |
| 2 | True | 0/0 | 14.900201 | 14.900201 | 14.900201 | True/True | 227 | 229 | 99 | 1.0 | 8.0 | FAIL_PARITY |
| 3 | True | 0/0 | 15.045044 | 15.045044 | 15.045044 | True/True | 238 | 245 | 110 | 1.0 | 8.0 | FAIL_PARITY |

- 梯度张量总数（dense 侧 CPU 收集）: **548**（含 rank-local 294 与 FSDP 全分片计数口径）。
- 每 rank 的 `intrinsic_noise`（dense0a vs dense0b）与 `compact_effect`（dense0a vs compact1）**group-level pass 数完全一致**（rank0 示例: moe_gen 150/281、time_embedder 0/4、vae2llm 0/2、action_modality_embed 0/1、action2llm 2/2、llm2action 2/2、llm2vae 2/2、vae2llm 0/2）。

### 2.2a 统计口径说明（294 vs 548，回应审核）

- **294** = 优化器实际选中的可训练参数（`keys_to_select = GENERATION_KEYS`，`optimizer.py:303` 子串 allowlist；harness `selected_params.count`）。这是合同要求"遍历全部 optimizer selected trainable parameters"的**最小集合**，四 rank 均为 294，覆盖 7 组。
- **548** = 反向传播后 `param.grad is not None` 的**全部**可训练参数（harness `run_side` 对 `model.named_parameters()` 全量收集，无任何过滤；`compare()` 取两侧交集）。四 rank 均为 548。
- **254 = 548 − 294** = 收到梯度但**不在优化器 allowlist 内**的参数，即 **VLM reasoner 骨干**（`net.language_model.model.embed_tokens.weight`、`net.language_model.model.layers.N.*` 的 norm/attn/mlp 等；`requires_grad=True`、参与 backward、但不匹配任何 GENERATION_KEYS，故优化器不更新）。四 rank 一致。
- **结论**：548 是 294 的**严格超集**。梯度逐参数统计**完整覆盖了合同要求的全部 294 个 optimizer-selected 参数**，还额外多比较了 254 个骨干参数——覆盖是**保守/偏严**的，不是缺失。所有"需要训练的参数"无一漏检。
- **294 子集内失败率更高**（非被 548 稀释）：

| rank | 294 子集失败 | 294 失败率 | 额外 254 失败 | 254 失败率 | 全量 548 失败率 |
| --- | --- | --- | --- | --- | --- |
| 0 | 138 | 46.9% | 87 | 34.3% | 41.1% |
| 1 | 141 | 48.0% | 94 | 37.0% | 42.9% |
| 2 | 138 | 46.9% | 91 | 35.8% | 41.8% |
| 3 | 153 | 52.0% | 92 | 36.2% | 44.7% |

> 
> 即：即便只统计合同要求的 294 个 optimizer-selected 参数，严格 `allclose(rtol=1e-3,atol=1e-5)` 在 bf16 backward + FSDP2 下的失败率仍高达 **46.9%–52.0%**，且与额外 254 个骨干参数（34.3%–37.0%）同属噪声带内。因此"严格 per-param 等价在 bf16 下不可达"的结论**不依赖 548 分母**，在 294 子集内同样成立。

### 2.3 失败集合重叠（固有噪声 vs Compact 效应，逐 rank）

| rank | 噪声失败(全) | 效应失败(全) | top-50 交集 | 仅效应独有(top-50) | 仅噪声独有(top-50) | 重叠率(top-50) |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 224 | 225 | 49 | 1 | 1 | 98% |
| 1 | 242 | 235 | 45 | 5 | 5 | 90% |
| 2 | 227 | 229 | 46 | 4 | 4 | 92% |
| 3 | 238 | 245 | 47 | 3 | 3 | 94% |

> 
> `failures` 列表在 JSON 中截取 top-50 样本（`failure_count` 为全量真实数）；上表交集按 top-50 样本统计。仅效应独有的参数是随机零星项（如 rank1 的 `layers.0.self_attn.k_proj.weight` 等），不构成系统性模块差异。

### 2.4 量级（rank0 worst10，`max_abs` / `rel_l2`）

| 方向 | worst 参数 | max_abs | rel_l2 |
| --- | --- | --- | --- |
| 噪声 | `layers.1.self_attn.v_proj.weight` | 9.766e-04 | 0.0036 |
| 噪声 | `embed_tokens.weight` | 4.883e-04 | 0.0044 |
| 噪声 | `layers.0.self_attn.v_proj.weight` | 4.883e-04 | 0.0039 |
| 噪声 | `layers.1.mlp.down_proj.weight` | 4.883e-04 | 0.0034 |
| 效应 | `embed_tokens.weight` | 9.766e-04 | 0.0061 |
| 效应 | `layers.0.self_attn.v_proj.weight` | 4.883e-04 | 0.0040 |
| 效应 | `layers.1.mlp.down_proj.weight` | 4.883e-04 | 0.0034 |
| 效应 | `layers.1.self_attn.v_proj.weight` | 4.883e-04 | 0.0031 |

> 
> 两侧 worst10 参数集合与量级高度重合（同一批层/同一 ULP 量级），进一步佐证 Compact 效应落在噪声带内。

### 2.5 判定与诊断解读

- 按冻结合同 Fail-closed: 四 rank 全部通过才 `PASS_CANDIDATE`；有 grad 差异即 `FAIL_PARITY`，允许**一次** Dense→Dense 重放诊断（本轮即 `dense0a vs dense0b`）。
- **诊断结论（假设，非已验证结论）**: 同路径 dense→dense 重放本身就有 224–242/548 参数在严格 allclose 下失败 → **严格 tolerance 在 bf16 backward + FSDP2 下本就不可达**；Compact 效应失败数（225–245）与其重叠在噪声带内；~80% 参数 compact 偏差 ≤ 固有噪声（excess_positive 仅 98–115/548 = 18%–21%），median ratio=1.0。**⚠️ 审核提示：约 18%–21% 对象出现 Compact 偏差 > Dense 重放偏差，故"没有 Compact 特有梯度分歧"目前只是假设（基于统计不可区分的支持性证据），尚未达到可验证的严格结论**；严格 Parity 未通过，但尚无证据证明 Compact 本身导致梯度错误。
- **状态固定**: `B=FAIL_PARITY`（不因诊断自动升级为 PASS_CANDIDATE；不自行宣称 formal Gate CLOSED）。
- 边界: 未做 >1 iter 长程；未在正式 NoTTT Checkpoint 边界切换 Compact；未触碰旧正式 Job / GPU0–3；未停止/修改旧 Job。

### 2.6 v2 生产冻结复测（2026-10-29，GPU4–7，回应复审后唯一 GPU 实验）

v2 harness 按 ChatGPT 六文件复审修复后执行最小 GPU 复测（`CUDA_VISIBLE_DEVICES=4,5,6,7`，torch 2.10.0+cu128）。**三个 HIGH/MEDIUM 项全部闭环**，但严格 per-param parity 结论不变：

- **生产冻结精确复现**：v2 用 `model.init_optimizer_scheduler(config.optimizer, config.scheduler)` 构建**真实** Optimizer。日志：`_build_params_with_metadata` → `Total tensors: 549, trainable tensors: 549, selected tensors: 294`；`validate_optimizer_inventory(no_ttt=True)` 返回 `{generation_tensors: 294, local_tensors: 0}`（无 ValueError）→ 选中集合恰好 294。`requires_grad_counts = {frozen: 255, trainable: 294}`（255+294=549）。
- **全程 `grads=294`**（dense0a / dense0b / compact1 三侧均打印 294，而非 v1 的 548）→ HIGH-1「Harness 未复现生产冻结」已修复。
- **结构见证全通过（MEDIUM 已闭环）**：`plan.members_eq=True`（每 rank 128）、`dcp_load missing=0/unexpected=0`、`grad_none_mask_eq.dense0a_vs_compact1=True`、`grad_dtype_eq.mismatch_count=0`、`weight_buffer_invariance`（549 checked, drift_count=0）、`intrinsic/effect loss_eq=True`（dense0a/dense0b/compact1 逐位一致）。
- **梯度 per-param 严格 allclose 仍失败（294 子集内）**：

| rank | 固有噪声 D→D 失败 | 失败率 | Compact 效应 D→C 失败 | 失败率 | excess_positive/294 | ratio_med | ratio_max | only_a/only_b |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 139 | 47.3% | 135 | 45.9% | 54 | 1.0 | 4.0 | 0/0 |
| 1 | 149 | 50.7% | 142 | 48.3% | 40 | 1.0 | 8.0 | 0/0 |
| 2 | 140 | 47.6% | 148 | 50.3% | 49 | 1.0 | 8.0 | 0/0 |
| 3 | 154 | 52.4% | 156 | 53.1% | 61 | 1.0 | 16.0 | 0/0 |

- **解读**：复现生产冻结后，**同路径 Dense→Dense 重放本身即在 294 子集内有 47.3%–52.4% 失败率**（bf16 backward + FSDP2 固有非确定性）；Compact 效应失败率（45.9%–53.1%）与其**统计不可区分**；`only_a/only_b=0` 无任何梯度存在性结构差异；`ratio_median=1.0`，个别 ratio 达 4–16 的对象均为 ULP 级偏差（max_abs ≈ 1e-4–2e-4），其中 `noise_ok=True 但 compact_ok=False` 的零星项（如 rank1 `layers.16.input_layernorm`、rank3 `layers.14.self_attn.q_proj`）仍是"Compact 偏差 > Dense 重放偏差"的证据，故**"无 Compact 特有梯度分歧"依旧是假设（统计不可区分），不是已验证的严格结论**。
- **结论**：v1 的"严格 per-param 等价在 bf16 下不可达"结论**不依赖 v1 缺失生产冻结**——在精确复现生产冻结（294/255）后同样成立。四 rank 均 `FAIL_PARITY`（fail-closed 正式判据），但结构见证全通过 + loss 逐位一致 + 无梯度存在性差异 → **无证据证明 Compact 引入系统性梯度错误**。
- 产物：`v2_gpu_parity_rank_jsonl/v3_gpu_parity_rank{0..3}_v2.json` + `v2_run.log`。

---

## 3. C — S2 新 Job Resume 静态就绪检查（只读，不执行 Resume）

- 目标 Job（**正确身份**）: `no_ttt_compact1_corerun_20261028_world4_ga4`（Compact=1，fresh 1 成功，`status=optimizer_committed`）。**不是** 旧的 `no_ttt_packed128_droid_fresh_30k_world4_ga4`。

| 检查项 | 结果 |
| --- | --- |
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

```
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

```
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

### 3.2 Resume 命令（**按 ChatGPT 2026-10-29 审核修正；仅供 Owner/GPT 审阅，本轮不执行**）

正式 launcher 是 **Bash 脚本**，只接受两个位置参数：`<phase> <iter>`。Resume 10 的正确调用（从 Root 仓库目录运行）：

```
# 从 Root 仓库目录运行（Root 仓库根目录，不是 cosmos-framework/）
cd /mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma_v3

# 按审核修正：Bash 脚本 + 两个位置参数
bash scripts/train_v3_matched_no_ttt_4gpu.sh resume 10
```

脚本内部约定（审核确认）：预先设置 `JOB_NAME`、`PYTHON`、`OUTPUT_ROOT`、数据路径（source/cache/index）、`PSM_V3_COMPACT_CACHED_VIDEO=1`；`save_iter=100` 不变。

```
# 环境变量示例（具体取值以正式脚本内部 preset 为准）
export JOB_NAME=no_ttt_compact1_corerun_20261028_world4_ga4
export PYTHON=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/cosmos-framework/.venv/bin/python
export OUTPUT_ROOT=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma_v3/outputs/no_ttt_robocasa_raw15
export PSM_V3_COMPACT_CACHED_VIDEO=1
bash scripts/train_v3_matched_no_ttt_4gpu.sh resume 10
```

> 
> ⚠️ 本轮**未执行**任何 Resume；`save_iter=100` 不变；`resume 10` 表示从 iter=10 恢复（非旧草案中的 `--phase resume --job-name ...` 长参数形式，后者已按审核作废）。

---

## 4. 交付物清单（本包路径 `docs/collab/chatgpt/evidence/2026-10-28_V3_NoTTT_Compact_OneRound/`）

- `summary.md`（本文件，自包含可读入口）。
- `summary.json`（机器可读：A_perf_rows / B_gpu_parity / C_s2_readiness，与本文一致）。
- `gpu_paired_harness.py`（B v1 可复现脚本，原样，与 `/tmp/v3_nott_compact_gpu_parity.py` 逐字节一致；本地无 `__version__`/`__name__` 损坏，ChatGPT 侧损坏源自其 Markdown 渲染通道）。
- `gpu_paired_harness_v2_freeze_formalpass_fullwitness.py`（**B v2 修复版**，2026-10-29 回应六文件复审：①真实构建 Optimizer 复现生产冻结 `keys_to_select=GENERATION_KEYS`→`requires_grad=False`，并用 `validate_optimizer_inventory(no_ttt=True)` 断言恰好 294；②正式 PASS 判据仅冻结 per-param allclose（`failure_count==0`+loss_eq+plan/dcp/None-mask/dtype/weight-buffer 不变），移除 v1 启发式 `local_pass`；③补完整输入/输出/梯度 dtype/None-mask/权重 Buffer 见证。已 py_compile+ruff 通过，并已在 GPU4–7 完成最小复测，结果见 §2.6）。
- `gpu_parity_rank_jsonl/v3_gpu_parity_rank{0..3}.json`（B v1 四 rank 原始结果：worst10 / failures top-50 / group_stats / dcp_load / plan / catalog / diagnostic）+ 分析脚本 `analyze_parity.py`、`analyze_diag.py`。
- `v2_gpu_parity_rank_jsonl/`（B v2 复测产物：`v3_gpu_parity_rank{0..3}_v2.json` + `v2_run.log`；结果见 §2.6）。
- `task_a_raw_jsonl/{compact1,compact0,compact1_r2}.jsonl`（A 三 Job 原始 iter=1 记录原文）。
- `task_c_s2_resume/`（`latest_checkpoint.txt`、`complete.v1.json`、`v3_job_identity.json` 原样副本）。
- 顺带归档: `docs/collab/chatgpt/evidence/2026-10-28_nott_compact_corerun_s0_s1.{md,json}`（此前已有，非阻塞项）。

## 5. 剩余问题与后续

1. **2026-10-29 六文件独立复审 = `REQUEST_CHANGES`（Evidence-only）**：294/548 口径已查清（548 为超集，非漏检）；新增 **HIGH「Harness 未复现生产参数冻结」**（v1 给 548 个参数算梯度而非生产的 294）+ **HIGH「潜在伪 PASS」**（v1 `local_pass` 用 `failure_count≤intrinsic_noise`/`ratio_max≤2` 启发式）+ **MEDIUM「见证不完整」**。**v2 修复版 harness 已按用户授权在 GPU4–7 完成最小复测**（§2.6）：生产冻结精确复现（294/255、inventory 通过、全程 grads=294）、全部结构见证通过、loss 逐位一致；但 294 子集内 Dense→Dense 自身失败率 47.3%–52.4%、Dense→Compact 45.9%–53.1%，统计不可区分 → 严格 per-param parity 在 bf16 下不可达的结论**不依赖 v1 缺失生产冻结**。
2. 结论边界（v1/v2 一致）：严格判据无法区分 Compact 效应与重复运行差异；`noise_ok=True 但 compact_ok=False` 的零星 ULP 级对象（每 rank 极少数）说明“无 Compact 特有梯度分歧”**仍是假设（统计不可区分），非已验证的严格结论**；四 rank `FAIL_PARITY`（fail-closed），但无证据证明 Compact 引入系统性梯度错误。
3. C 为静态就绪，真实 DCP restore 可恢复性未实测；Resume 命令已按审核修正为 `bash scripts/train_v3_matched_no_ttt_4gpu.sh resume 10`（见 §3.2），仍待 Owner/GPT 最终确认后执行。
4. A 为非稳态单次观测，稳态速度结论需正式 S2 长训的 monitor 数据，本轮未启动。
5. 本轮 v2 复测**未**：执行 `optimizer.step`/`scheduler.step`/`checkpointer.save`、写模型/DCP/Job Identity、切换旧 Job Compact、停旧 Job、修改生产代码/配置/Cleaner。下一动作按审核与用户授权 = 汇总 v2 复测证据、向 ChatGPT 回执复测结论（可复跑、判据 fail-closed、结构全通过），是否需再提交审核/启动 S2 由 Owner 决定。

{
 "package": "2026-10-28_V3_NoTTT_Compact_OneRound",
 "date": "2026-10-28",
 "role": "ds_pro",
 "root_note": "formal No-TTT Root historical implementation 49df7f3c2e0ba8ef5871f9dd490e41fbc3dc5da9; Child/Gitlink 746c5cf2f2324104a62fb71510343aa40d3976c5; current Root HEAD recorded as run provenance only, not as formal implementation",
 "request": "docs/collab/chatgpt/requests/2026-10-28_V3_NoTTT_Compact_OneRound_GPU_Parity_Perf_S2_Readiness_DS_PRO.md",
 "A_perf_rows": [
  {
   "job": "no_ttt_compact1_gpu_parity_world4_ga4",
   "tag": "A_compact1",
   "compact_cached_video": true,
   "iteration": 1,
   "step_wall_ms": 25523.08569289744,
   "data_prepare_ms": 9149.389371275902,
   "batch_collate_ms": 60.80031022429466,
   "batch_transfer_ms": 176.1079505085945,
   "forward_ms": 7513.272438198328,
   "backward_ms": 8192.298652604222,
   "optimizer_ms": 51.09410174190998,
   "other_host_overhead_ms": 380.12286834418774,
   "gpu_data_stall_ms": 8981.404524803162,
   "source_read_ms": "NOT_RECORDED",
   "valid_consumers": 512,
   "native_forward_calls": 4,
   "native_backward_calls": 4,
   "batch_identity_sha256": "NOT_RECORDED",
   "actual_consumer_identity_sha256": "9207fc67ae9504387de5b866c60dc5023a0b13ef76ed7109813b41115c3e7830",
   "outer_loss": 14.937467575073242,
   "action_loss": 1.2275960445404053,
   "vision_loss": 0.2661505937576294,
   "total_grad_norm_rank_local": 3.706259250640869,
   "num_workers": 0,
   "no_ttt_loader_workers": "NOT_RECORDED",
   "peak_allocated_gib": 25.184635162353516,
   "peak_reserved_gib": 29.83984375,
   "telemetry_errors": [],
   "config_digest": "5a67adef628a0c7d91812c525d6d412bf380bf1f381ca4cc3dc4afc7f370fbc7",
   "semantic_digest": "a16759f8318c30ab50669f87b1ec5c990be7861fcbb51c66b9c75a70f3516f86",
   "status": "optimizer_committed"
  },
  {
   "job": "no_ttt_compact0_gpu_parity_world4_ga4",
   "tag": "B_compact0",
   "compact_cached_video": false,
   "iteration": 1,
   "step_wall_ms": 45806.40850774944,
   "data_prepare_ms": 30127.756906673312,
   "batch_collate_ms": 36.09652817249298,
   "batch_transfer_ms": 352.1300610154867,
   "forward_ms": 7944.145245477557,
   "backward_ms": 7060.457045212388,
   "optimizer_ms": 42.58906841278076,
   "other_host_overhead_ms": 243.23365278542042,
   "gpu_data_stall_ms": 29934.68492078781,
   "source_read_ms": "NOT_RECORDED",
   "valid_consumers": 512,
   "native_forward_calls": 4,
   "native_backward_calls": 4,
   "batch_identity_sha256": "NOT_RECORDED",
   "actual_consumer_identity_sha256": "9207fc67ae9504387de5b866c60dc5023a0b13ef76ed7109813b41115c3e7830",
   "outer_loss": 14.937467575073242,
   "action_loss": 1.2275960445404053,
   "vision_loss": 0.2661505937576294,
   "total_grad_norm_rank_local": 3.7076737880706787,
   "num_workers": 0,
   "no_ttt_loader_workers": "NOT_RECORDED",
   "peak_allocated_gib": 25.571489334106445,
   "peak_reserved_gib": 30.6796875,
   "telemetry_errors": [],
   "config_digest": "5a67adef628a0c7d91812c525d6d412bf380bf1f381ca4cc3dc4afc7f370fbc7",
   "semantic_digest": "a16759f8318c30ab50669f87b1ec5c990be7861fcbb51c66b9c75a70f3516f86",
   "status": "optimizer_committed"
  },
  {
   "job": "no_ttt_compact1_gpu_parity_r2_world4_ga4",
   "tag": "C_compact1_r2",
   "compact_cached_video": true,
   "iteration": 1,
   "step_wall_ms": 23482.16939345002,
   "data_prepare_ms": 6888.700436800718,
   "batch_collate_ms": 48.18391799926758,
   "batch_transfer_ms": 507.6713003218174,
   "forward_ms": 8792.424239218235,
   "backward_ms": 6972.6952612400055,
   "optimizer_ms": 43.35617460310459,
   "other_host_overhead_ms": 229.13806326687336,
   "gpu_data_stall_ms": 6704.730309963226,
   "source_read_ms": "NOT_RECORDED",
   "valid_consumers": 512,
   "native_forward_calls": 4,
   "native_backward_calls": 4,
   "batch_identity_sha256": "NOT_RECORDED",
   "actual_consumer_identity_sha256": "9207fc67ae9504387de5b866c60dc5023a0b13ef76ed7109813b41115c3e7830",
   "outer_loss": 14.937467575073242,
   "action_loss": 1.2275960445404053,
   "vision_loss": 0.2661505937576294,
   "total_grad_norm_rank_local": 3.7086875438690186,
   "num_workers": 0,
   "no_ttt_loader_workers": "NOT_RECORDED",
   "peak_allocated_gib": 25.184635162353516,
   "peak_reserved_gib": 29.83984375,
   "telemetry_errors": [],
   "config_digest": "5a67adef628a0c7d91812c525d6d412bf380bf1f381ca4cc3dc4afc7f370fbc7",
   "semantic_digest": "a16759f8318c30ab50669f87b1ec5c990be7861fcbb51c66b9c75a70f3516f86",
   "status": "optimizer_committed"
  }
 ],
 "A_observation": {
  "note": "single fresh1 per Job; GPU4-7 co-resident with old formal No-TTT job; cold start + contention; NOT a steady-state acceleration conclusion",
  "compact0_vs_median_compact1_step_wall": {
   "B_step_wall_ms": 45806.41,
   "median_AC_step_wall_ms": 24502.63,
   "ratio": 1.87
  },
  "compact0_vs_median_compact1_data_prepare": {
   "B_data_prepare_ms": 30127.76,
   "median_AC_data_prepare_ms": 8019.04,
   "ratio": 3.76
  },
  "compact0_vs_median_compact1_gpu_data_stall": {
   "B_gpu_data_stall_ms": 29934.68,
   "median_AC_gpu_data_stall_ms": 7843.07,
   "ratio": 3.82
  },
  "identity": "config_digest 5a67adef identical across 3 Jobs; semantic_digest a16759f8 identical; batch identity sha identical; only PSM_V3_COMPACT_CACHED_VIDEO differs; same DROID base checkpoint / source cache index / precision bfloat16 / effective world4-GA4 per launch.json",
  "caveat": "compact0 run slower on step_wall dominated by data_prepare/gpu_data_stall; single-observation, co-resident contention, cannot attribute speed difference to Compact flag alone"
 },
 "B_gpu_parity": {
  "status": "FAIL_PARITY",
  "verdict_rule": "fail-closed: all 4 ranks must pass per-param allclose(rtol=1e-3,atol=1e-5); any rank fail -> FAIL_PARITY; one Dense->Dense replay diagnostic allowed (done)",
  "interpretation": "Loss bit-identical across dense0a/dense0b/compact1 on all 4 ranks. Per-param gradient failures at strict allclose are dominated by intrinsic bf16 GPU backward non-determinism (dense0a-vs-dense0b same-path rerun already fails 224-242/548 params). Compact effect failures (225-245/548) are statistically indistinguishable from intrinsic noise; ~80% of params have compact divergence <= intrinsic noise divergence (excess_positive 98-115/548); ratio_median=1.0. No compact-specific gradient divergence signal (HYPOTHESIS, not verified strict conclusion: 18-21% of params show compact divergence > dense-rerun divergence; strict parity not passed but no evidence compact itself causes gradient errors).",
  "environment": {
   "python": "psm_wma/cosmos-framework/.venv/bin/python",
   "torch": "2.10.0+cu128",
   "cuda": "12.8",
   "device": "NVIDIA H100 80GB HBM3",
   "gpus": "CUDA_VISIBLE_DEVICES=4,5,6,7 (co-resident with old formal No-TTT)",
   "world_size": 4,
   "model": "OmniMoTModel local_memory_enabled=False, FSDP2 shard_degree=4, bfloat16, selective activation checkpointing, compile disabled",
   "base_checkpoint": "read-only DROID Cosmos3-Edge-Policy-DROID-dcp",
   "data": "same frozen plan: ExactWindowRankPlanner(rank=RANK,world4,B8,T16,GA4,seed=0) member[0], 128 valid consumers/rank, normalized weight ~0.25, iteration=1000",
   "sides": "dense0a -> dense0b (intrinsic noise) -> compact1 (effect), RNG restored before each side, zero_grad(set_to_none=True), no optimizer/scheduler/checkpointer"
  },
  "selected_params": {
   "count_rank_local": 294,
   "groups": {
    "action2llm": 2,
    "action_modality_embed": 1,
    "llm2action": 2,
    "llm2vae": 2,
    "moe_gen": 281,
    "time_embedder": 4,
    "vae2llm": 2
   },
   "grad_params_total_dense": 548,
   "statistical_denominator": "548 = ALL grad-bearing trainable params (param.grad is not None, no filter) = STRICT SUPERSET of the 294 optimizer-selected GENERATION_KEYS params required by contract. 254 extra = VLM reasoner backbone (embed_tokens.weight + language_model.layers.* norms/attn/mlp): requires_grad=True, receive grads, but not in optimizer keys_to_select allowlist. Coverage therefore COMPLETE and conservative (covers all 294 + 254 more); failures within the 294 subset are 46.9-52.0% (higher than overall 41.1-44.7%), so the bf16 non-determinism conclusion does NOT depend on the 548 denominator."
  },
  "by_rank": [
   {
    "rank": 0,
    "verdict": "FAIL_PARITY",
    "local_pass": false,
    "plan_members_eq": true,
    "dcp_missing": 0,
    "dcp_unexpected": 0,
    "loss_dense0a": 15.290846,
    "loss_dense0b": 15.290846,
    "loss_compact1": 15.290846,
    "loss_eq_noise": true,
    "loss_eq_effect": true,
    "intrinsic_noise_failures": 224,
    "compact_effect_failures": 225,
    "excess_positive_params": 115,
    "common_params": 548,
    "ratio_median": 1.0,
    "ratio_max": 4.0
   },
   {
    "rank": 1,
    "verdict": "FAIL_PARITY",
    "local_pass": false,
    "plan_members_eq": true,
    "dcp_missing": 0,
    "dcp_unexpected": 0,
    "loss_dense0a": 15.298787,
    "loss_dense0b": 15.298787,
    "loss_compact1": 15.298787,
    "loss_eq_noise": true,
    "loss_eq_effect": true,
    "intrinsic_noise_failures": 242,
    "compact_effect_failures": 235,
    "excess_positive_params": 98,
    "common_params": 548,
    "ratio_median": 1.0,
    "ratio_max": 32.0
   },
   {
    "rank": 2,
    "verdict": "FAIL_PARITY",
    "local_pass": false,
    "plan_members_eq": true,
    "dcp_missing": 0,
    "dcp_unexpected": 0,
    "loss_dense0a": 14.900201,
    "loss_dense0b": 14.900201,
    "loss_compact1": 14.900201,
    "loss_eq_noise": true,
    "loss_eq_effect": true,
    "intrinsic_noise_failures": 227,
    "compact_effect_failures": 229,
    "excess_positive_params": 99,
    "common_params": 548,
    "ratio_median": 1.0,
    "ratio_max": 8.0
   },
   {
    "rank": 3,
    "verdict": "FAIL_PARITY",
    "local_pass": false,
    "plan_members_eq": true,
    "dcp_missing": 0,
    "dcp_unexpected": 0,
    "loss_dense0a": 15.045044,
    "loss_dense0b": 15.045044,
    "loss_compact1": 15.045044,
    "loss_eq_noise": true,
    "loss_eq_effect": true,
    "intrinsic_noise_failures": 238,
    "compact_effect_failures": 245,
    "excess_positive_params": 110,
    "common_params": 548,
    "ratio_median": 1.0,
    "ratio_max": 8.0
   }
  ],
  "harness": "gpu_paired_harness_v2_freeze_formalpass_fullwitness.py (v2, production-freeze reproduced; ran on GPU 2026-10-29); rank JSONs in v2_gpu_parity_rank_jsonl/",
  "boundaries": [
   "strict allclose(rtol=1e-3,atol=1e-5) is unreachable even for dense-vs-dense same-path rerun under bf16 backward -> FAIL_PARITY is the fail-closed contract outcome, not evidence of compact-specific bug",
   "no optimizer.step / scheduler.step / grad_scaler.step / checkpointer.save executed",
   "no production code modified; no formal Gate CLOSED declared"
  ],
  "retest_v2": {
   "date": "2026-10-29",
   "gpus": "CUDA_VISIBLE_DEVICES=4,5,6,7",
   "torch": "2.10.0+cu128",
   "cuda": "12.8",
   "production_freeze_reproduced": true,
   "notes": "v2 harness builds the REAL optimizer via model.init_optimizer_scheduler(config.optimizer, config.scheduler); _build_params_with_metadata log shows Total tensors 549 / trainable 549 / selected 294; validate_optimizer_inventory(no_ttt=True) returned {generation_tensors:294, local_tensors:0}; requires_grad_counts={frozen:255, trainable:294}. All structural witnesses pass (plan members_eq, dcp missing/unexpected=0/0, grad none-mask eq dense-vs-compact True, grad dtype mismatch=0, weight/buffer drift=0). Loss bit-identical dense0a/dense0b/compact1 on all ranks. Per-param strict allclose STILL fails at ~46-53% on the 294 subset for BOTH intrinsic (dense0a-vs-dense0b) and compact effect (dense0a-vs-compact1), statistically indistinguishable; only_a/only_b=0 (no structural grad-presence difference). Verdict FAIL_PARITY on all 4 ranks under fail-closed formal criterion. This confirms the v1 conclusion (strict per-param parity unreachable in bf16 backward + FSDP2) is NOT an artifact of v1 lacking production freeze.",
   "by_rank": [
    {
     "rank": 0,
     "verdict": "FAIL_PARITY",
     "formal_pass": false,
     "plan_members_eq": true,
     "dcp_missing": 0,
     "dcp_unexpected": 0,
     "optimizer_inventory": {
      "generation_params": 1423379648,
      "generation_tensors": 294,
      "local_params": 0,
      "local_tensors": 0
     },
     "requires_grad_counts": {
      "frozen": 255,
      "trainable": 294
     },
     "selected_count": 294,
     "loss_dense0a": 15.290846,
     "loss_dense0b": 15.290846,
     "loss_compact1": 15.290846,
     "loss_eq_noise": true,
     "loss_eq_effect": true,
     "intrinsic_noise_failures": 139,
     "compact_effect_failures": 135,
     "only_a_noise": 0,
     "only_b_noise": 0,
     "only_a_effect": 0,
     "only_b_effect": 0,
     "grad_none_mask_eq_dc": true,
     "grad_dtype_mismatch": 0,
     "weight_buffer_drift": 0,
     "common_params": 294,
     "excess_positive_params": 54,
     "ratio_median": 1.0,
     "ratio_max": 4.0
    },
    {
     "rank": 1,
     "verdict": "FAIL_PARITY",
     "formal_pass": false,
     "plan_members_eq": true,
     "dcp_missing": 0,
     "dcp_unexpected": 0,
     "optimizer_inventory": {
      "generation_params": 1423379648,
      "generation_tensors": 294,
      "local_params": 0,
      "local_tensors": 0
     },
     "requires_grad_counts": {
      "frozen": 255,
      "trainable": 294
     },
     "selected_count": 294,
     "loss_dense0a": 15.298787,
     "loss_dense0b": 15.298787,
     "loss_compact1": 15.298787,
     "loss_eq_noise": true,
     "loss_eq_effect": true,
     "intrinsic_noise_failures": 149,
     "compact_effect_failures": 142,
     "only_a_noise": 0,
     "only_b_noise": 0,
     "only_a_effect": 0,
     "only_b_effect": 0,
     "grad_none_mask_eq_dc": true,
     "grad_dtype_mismatch": 0,
     "weight_buffer_drift": 0,
     "common_params": 294,
     "excess_positive_params": 40,
     "ratio_median": 1.0,
     "ratio_max": 8.0
    },
    {
     "rank": 2,
     "verdict": "FAIL_PARITY",
     "formal_pass": false,
     "plan_members_eq": true,
     "dcp_missing": 0,
     "dcp_unexpected": 0,
     "optimizer_inventory": {
      "generation_params": 1423379648,
      "generation_tensors": 294,
      "local_params": 0,
      "local_tensors": 0
     },
     "requires_grad_counts": {
      "frozen": 255,
      "trainable": 294
     },
     "selected_count": 294,
     "loss_dense0a": 14.900201,
     "loss_dense0b": 14.900201,
     "loss_compact1": 14.900201,
     "loss_eq_noise": true,
     "loss_eq_effect": true,
     "intrinsic_noise_failures": 140,
     "compact_effect_failures": 148,
     "only_a_noise": 0,
     "only_b_noise": 0,
     "only_a_effect": 0,
     "only_b_effect": 0,
     "grad_none_mask_eq_dc": true,
     "grad_dtype_mismatch": 0,
     "weight_buffer_drift": 0,
     "common_params": 294,
     "excess_positive_params": 49,
     "ratio_median": 1.0,
     "ratio_max": 8.0
    },
    {
     "rank": 3,
     "verdict": "FAIL_PARITY",
     "formal_pass": false,
     "plan_members_eq": true,
     "dcp_missing": 0,
     "dcp_unexpected": 0,
     "optimizer_inventory": {
      "generation_params": 1423379648,
      "generation_tensors": 294,
      "local_params": 0,
      "local_tensors": 0
     },
     "requires_grad_counts": {
      "frozen": 255,
      "trainable": 294
     },
     "selected_count": 294,
     "loss_dense0a": 15.045044,
     "loss_dense0b": 15.045044,
     "loss_compact1": 15.045044,
     "loss_eq_noise": true,
     "loss_eq_effect": true,
     "intrinsic_noise_failures": 154,
     "compact_effect_failures": 156,
     "only_a_noise": 0,
     "only_b_noise": 0,
     "only_a_effect": 0,
     "only_b_effect": 0,
     "grad_none_mask_eq_dc": true,
     "grad_dtype_mismatch": 0,
     "weight_buffer_drift": 0,
     "common_params": 294,
     "excess_positive_params": 61,
     "ratio_median": 1.0,
     "ratio_max": 16.0
    }
   ]
  }
 },
 "C_s2_readiness": {
  "status": "READY_BY_STATIC_CHECKS",
  "job": "no_ttt_compact1_corerun_20261028_world4_ga4 (Compact=1, fresh 1 succeeded, status optimizer_committed)",
  "latest_checkpoint_txt": "iter_000000001",
  "complete_v1_json": {
   "schema": "psm_v3_sync_local_v1",
   "complete": true,
   "iteration": 1,
   "world_size": 4,
   "model": {
    "metadata_sha256": "992cc0da7d8658cbb8c4aa8e4e23edf4fae549a8f9850d7d86b0a6e5f9e91d84",
    "files": 4
   },
   "optim": {
    "metadata_sha256": "08e288ac8b455f2140e75727444dae4d1e01eb76c64c4d68e29cb8ee39f1abf7",
    "files": 4
   },
   "scheduler": {
    "metadata_sha256": "2d8f452761f2d08e008eafe881bc452da2baa820360e0fb4ea6a4a291d4c11df",
    "files": 1
   },
   "trainer": {
    "metadata_sha256": "a34d5080744619d8f16ad809679b105ff0e58632772404ed5b0a084ee357cac5",
    "files": 4
   },
   "sidecar_shas": {
    "0": "b0d1d38d0c8d0f49a72e3d2a9d9bb6f337623d8f5e86b9c8b4f9c41464e8c709",
    "1": "f656697413d2b58b3b101c0c0a48cb5652b5b25c59bfd96d12de9805c71be622",
    "2": "47f1657b661b5e348c70aae25d8fc5a909cfd97ebf20cc5380bf9b2f738e824b",
    "3": "ab1ce5d459ce145f461221d99f8e45ba8e994068bac47460cb87c8f959493f84"
   }
  },
  "dataloader_pkls": {
   "rank_0.pkl": 1150,
   "rank_1.pkl": 1150,
   "rank_2.pkl": 1150,
   "rank_3.pkl": 1150,
   "present": true
  },
  "v3_job_identity": {
   "schema": "corrected_phase5_f0_v1",
   "semantic_digest": "a16759f8318c30ab50669f87b1ec5c990be7861fcbb51c66b9c75a70f3516f86",
   "save_iter": 100,
   "config.pkl_sha256": "f69f6dcc911c15c1012cfb5f24d9cd513e58a65b1407ac1189f17ea84b56d979",
   "config.yaml_sha256": "e037840679a398fd0671d6a9aed87f0a1714193d9d12235f64c39ea163ba3f5f",
   "compact_cached_video": true,
   "num_workers": 0,
   "no_ttt_loader_workers": "NOT_RECORDED (launcher default 0)",
   "native_batch_layout": "v2_a2_member_packed_slot_major_v1",
   "world4_ga4": {
    "b": 8,
    "t": 16,
    "k": 4,
    "ga": 4,
    "world_size": 4,
    "consumer_frames": 17,
    "h_pred": 16
   }
  },
  "source_paths_all_exist": true,
  "source_paths": [
   "/mnt/data/shenzhen/szrobot/logs/.tmp_backup/models/Cosmos3-Edge-Policy-DROID-dcp",
   "/mnt/data/shenzhen/szrobot/logs/.tmp_backup/datasets/robocasa365-target-atomic-left_wrist-exact_window",
   "/mnt/data/shenzhen/szrobot/logs/.tmp_backup/datasets/robocasa365-target-atomic-verified-index-r1",
   "/mnt/data/shenzhen/szrobot/logs/.tmp_backup/models/Cosmos3-Edge-Policy-DROID",
   "/mnt/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic",
   "/mnt/data/shenzhen/szrobot/logs/.tmp_backup/models/Wan2.2-TI2V-5B/Wan2.2_VAE.pth"
  ],
  "boundaries": [
   "static checks only; real DCP restore was NOT re-executed and full 24GB DCP hash was NOT redone",
   "READY_BY_STATIC_CHECKS != license to continue training",
   "resume command draft in summary.md; NOT executed"
  ]
 }
}

---

Setting OMP_NUM_THREADS environment variable for each process to be 1 in default, to avoid your system being overloaded, please further tune the variable for optimal performance in your application as needed. 

---

[10-29 04:10:53|CRITICAL|../../psm_wma_v3/cosmos-framework/cosmos_framework/utils/distributed.py:105:init] [RANK 1] Initialized distributed training with local rank 1 using nccl with timeout 1800
[10-29 04:10:55|CRITICAL|../../psm_wma_v3/cosmos-framework/cosmos_framework/utils/distributed.py:105:init] [RANK 3] Initialized distributed training with local rank 3 using nccl with timeout 1800
[10-29 04:10:55|CRITICAL|../../psm_wma_v3/cosmos-framework/cosmos_framework/utils/distributed.py:105:init] [RANK 0] Initialized distributed training with local rank 0 using nccl with timeout 1800
[10-29 04:10:55|INFO|../../psm_wma_v3/cosmos-framework/cosmos_framework/utils/distributed.py:117:init] Training with 4 GPUs.
/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/cosmos-framework/.venv/lib/python3.13/site-packages/torch/distributed/c10d_logger.py:83: UserWarning: barrier(): using the device under current context. You can specify `device_id` in `init_process_group` to mute this warning.
  return func(*args, **kwargs)
[rank0]:[W1029 04:10:55.067099694 ProcessGroupNCCL.cpp:5138] Guessing device ID based on global rank. This can cause a hang if rank to GPU mapping is heterogeneous. You can specify device_id in init_process_group()
[10-29 04:10:56|CRITICAL|../../psm_wma_v3/cosmos-framework/cosmos_framework/utils/distributed.py:105:init] [RANK 2] Initialized distributed training with local rank 2 using nccl with timeout 1800
2026-10-29 04:10:59.696 | DEBUG    | cosmos_framework.utils.config:_load_py_config:607 - get_config_module: took 0.04ms
2026-10-29 04:10:59.738 | DEBUG    | cosmos_framework.utils.config:_load_py_config:607 - get_config_module: took 0.04ms
2026-10-29 04:10:59.777 | DEBUG    | cosmos_framework.utils.config:_load_py_config:607 - get_config_module: took 0.06ms
2026-10-29 04:10:59.788 | DEBUG    | cosmos_framework.utils.config:_load_py_config:607 - get_config_module: took 0.06ms
2026-10-29 04:11:01.689 | DEBUG    | cosmos_framework.utils.config:_load_py_config:625 - importlib.import_module: took 1993.58ms
2026-10-29 04:11:01.761 | DEBUG    | cosmos_framework.utils.config:_load_py_config:625 - importlib.import_module: took 2022.59ms
2026-10-29 04:11:01.930 | DEBUG    | cosmos_framework.utils.config:_load_py_config:630 - override: took 240.34ms
2026-10-29 04:11:01.931 | DEBUG    | cosmos_framework.utils.config:load_config:591 - total time to load config: 2235.79ms
2026-10-29 04:11:02.007 | DEBUG    | cosmos_framework.utils.config:_load_py_config:630 - override: took 245.52ms
2026-10-29 04:11:02.008 | DEBUG    | cosmos_framework.utils.config:load_config:591 - total time to load config: 2269.88ms
2026-10-29 04:11:02.139 | DEBUG    | cosmos_framework.utils.config:_load_py_config:625 - importlib.import_module: took 2362.11ms
2026-10-29 04:11:02.349 | DEBUG    | cosmos_framework.utils.config:_load_py_config:625 - importlib.import_module: took 2559.99ms
2026-10-29 04:11:02.474 | DEBUG    | cosmos_framework.utils.config:_load_py_config:630 - override: took 334.71ms
2026-10-29 04:11:02.475 | DEBUG    | cosmos_framework.utils.config:load_config:591 - total time to load config: 2698.83ms
2026-10-29 04:11:02.685 | DEBUG    | cosmos_framework.utils.config:_load_py_config:630 - override: took 335.90ms
2026-10-29 04:11:02.686 | DEBUG    | cosmos_framework.utils.config:load_config:591 - total time to load config: 2898.31ms
This processor does not use the `size` parameter. It will be ignored.
This processor does not use the `size` parameter. It will be ignored.
This processor does not use the `size` parameter. It will be ignored.
[10-29 04:14:13|INFO|../../psm_wma_v3/cosmos-framework/cosmos_framework/data/generator/processors/base.py:169:**init**] Successfully loaded processor from local cache
This processor does not use the `size` parameter. It will be ignored.
[10-29 04:17:19|INFO|../../psm_wma_v3/cosmos-framework/cosmos_framework/data/generator/processors/base.py:169:**init**] Successfully loaded processor from local cache
[10-29 04:17:19|INFO|../../psm_wma_v3/cosmos-framework/cosmos_framework/model/generator/omni_mot_model.py:297:**init**] OmniMoTModel: config {'tokenizer': {'bucket_name': '', 'object_store_credential_path_pretrained': '', 'vae_path': '/mnt/data/shenzhen/szrobot/logs/.tmp_backup/models/Wan2.2-TI2V-5B/Wan2.2_VAE.pth', 'chunk_duration': 93, 'keep_decoder_cache': False, 'use_streaming_encode': False, 'encode_chunk_frames': {'256': 68, '480': 24, '720': 8, '768': 8}, 'encode_exact_durations': [17, 61, 73], 'spatial_compression_factor': 16, 'temporal_compression_factor': 4, 'temporal_window': None, 'encode_bucket_multiple': None, 'causal': True, '*target*': <class 'cosmos_framework.model.generator.tokenizers.wan2pt2_vae_4x16x16.Wan2pt2VAEInterface'>}, 'load_vision_tokenizer': True, 'lidar_tokenizer': None, 'radar_tokenizer': None, 'lidar_state_ch': None, 'lidar_fps': None, 'radar_state_ch': None, 'radar_fps': None, 'net': None, 'ema': {'enabled': False, 'rate': 0.1, 'iteration_shift': 0}, 'parallelism': {'data_parallel_shard_degree': 4, 'data_parallel_replicate_degree': 1, 'context_parallel_shard_degree': 1, 'cfg_parallel_shard_degree': 1, 'vae_load_balance_group_size': 1, 'enable_inference_mode': False, 'fsdp_cpu_offload': False, 'fsdp_master_dtype': 'float32', 'fsdp_reduce_dtype': 'bfloat16'}, 'attention_io_layout': 'sequence_sharded', 'correct_cp_gradients': False, 'compile': {'enabled': False, 'compiled_region': 'language', 'compile_dynamic': True, 'use_cuda_graphs': False, 'cuda_graph_scope': 'block', 'ar_post_saturation_mode': 'default', 'max_autotune_pointwise': False, 'coordinate_descent_tuning': False, 'mark_unbacked': False}, 'quantization': {'method': None, 'fp8_granularity': 'per_row', 'include_regex': [], 'exclude_regex': [], 'modelopt_fp8_checkpoint_path': None, 'modelopt_fp8_target_fqns': [], 'mixed_precision_first_steps': 0, 'mixed_precision_last_steps': 0, 'mixed_precision_reasoner_policy': 'high_precision', 'mixed_precision_w8a16_cache': 'none'}, 'activation_checkpointing': {'mode': 'selective', 'save_ops_regex': ['fmha_forward', '_flash_attn_varlen_forward', '_flash_attn_forward'], 'save_only_marked_ops': False, 'preserve_rng_state': True, 'determinism_check': 'default'}, 'precision': 'bfloat16', 'lora_enabled': False, 'lora_rank': 16, 'lora_alpha': 32, 'lora_target_modules': 'q_proj_moe_gen,k_proj_moe_gen,v_proj_moe_gen,o_proj_moe_gen', 'rectified_flow_training_config': {'shift': {'256': 3, '480': 5, '720': 10}, 'shift_image': None, 'shift_lidar': None, 'use_dynamic_shift': False, 'train_time_image_distribution': 'logitnormal', 'train_time_video_distribution': 'waver', 'train_time_action_distribution': 'logitnormal', 'train_time_sound_distribution': 'logitnormal', 'train_time_weight': 'uniform', 'loss_scale': 10.0, 'image_loss_scale': None, 'sound_loss_scale': 2.0, 'lidar_loss_scale': None, 'radar_loss_scale': None, 'use_discrete_rf': False, 'action_loss_weight': 10.0, 'independent_action_schedule': False, 'shift_action': None, 'independent_sound_schedule': False, 'shift_sound': None, 'normalize_loss_by_active': False, 'exclude_fully_conditioned_items': None, 'sample_level_loss_averaging': False}, 'rectified_flow_inference_config': {'scheduler_type': 'unipc', 'num_train_timesteps': 1000, 'shift': 1, 'use_dynamic_shifting': False}, 'fixed_step_sampler_config': None, 'vlm_config': {'model_name': '/mnt/data/shenzhen/szrobot/logs/.tmp_backup/models/Cosmos3-Edge-Policy-DROID', 'safetensors_path': '', 'pretrained_weights': {'enabled': False, 'backbone_path': 's3://bucket/cosmos3/pretrained/huggingface/nvidia/Cosmos3-Edge-Reasoner-590c1c0/', 'credentials_path': '', 'enable_gcs_patch_in_boto3': True, 'checkpoint_format': None}, 'model_instance': {'config': {'base_config': {'json_file': 'cosmos_framework/model/generator/reasoner/nemotron_3_dense_vl/configs/Nemotron-2B-Dense-VL.json', '*target*': <bound method _MoTConfigBase.from_json_file of <class 'cosmos_framework.model.generator.mot.unified_mot.Nemotron3DenseVLMoTConfig'>>}, 'freeze_und': False, 'layer_module': 'MoTDecoderLayer', 'qk_norm_for_text': False, 'use_und_k_norm_for_gen': True, 'include_visual': None, 'tie_word_embeddings': True, '*target*': <function create_vlm_config at 0x7040bccd5760>}, '*target*': <class 'cosmos_framework.model.generator.mot.unified_mot.Nemotron3DenseVLTextForCausalLM'>}, 'tokenizer': {'repository': None, 'revision': None, 'subdir': '', '*target*': <function build_processor_lazy at 0x703d84b31e40>, 'tokenizer_type': '/mnt/data/shenzhen/szrobot/logs/.tmp_backup/models/Cosmos3-Edge-Policy-DROID'}, 'layer_module': None, 'qk_norm': False, 'tie_word_embeddings': False, 'use_system_prompt': False}, 'diffusion_expert_config': {'timestep_range': 1.0, 'load_weights_from_pretrained': False, 'enable_vision_modality_embeddings': False, 'enable_media_modality_embedding': False, 'enable_action_modality_embedding': True, 'enable_sound_modality_embedding': True, 'num_view_embeddings': 0, 'patch_spatial': 2, 'lidar_patch_spatial_hw': None, 'radar_patch_spatial_hw': None, 'max_vae_latent_side_after_patchify': 20, 'enable_fps_modulation': True, 'base_fps': 24, 'sound_base_temporal_compression_factor': None, 'vision_temporal_position_mode': 'latent_index', 'unified_3d_mrope_reset_spatial_ids': True, 'unified_3d_mrope_temporal_modality_margin': 15000}, 'input_video_key': 'video', 'input_image_key': 'images', 'input_caption_key': 'ai_caption', 'state_ch': 48, 'state_t': 300, 'latent_downsample_factor': 16, 'resolution': '480', 'max_num_tokens_after_packing': 74000, 'joint_attn_implementation': 'two_way', 'multiview_attention': {'backend': 'auto', 'mask': {'attention_scope': 'all_views', 'decomposed_temporal_window_seconds': None, 'control_attends_sensor': False, 'lidar_attends_captions': True, 'radar_attends_captions': True}}, 'natten_parameter_list': None, 'video_temporal_causal': False, 'causal_training_strategy': 'none', 'lbl': {'method': 'local', 'coeff_und': None, 'coeff_gen': None}, 'vision_gen': True, 'action_gen': True, 'max_action_dim': 64, 'local_memory_enabled': False, 'local_memory_dim': 32, 'local_memory_evidence_dim': 256, 'local_memory_action_dim': 15, 'local_memory_ttt_dim': 64, 'local_memory_fast_hidden_dim': 256, 'local_memory_inner_lr': 0.1, 'local_memory_ttt_tbptt_steps': 16, 'local_memory_k_local': 4, 'num_embodiment_domains': 32, 'action_io_projector_type': 'domain_aware', 'sound_gen': False, 'sound_tokenizer': None, 'sound_dim': None, 'sound_latent_fps': 25, 'sr_latent_condition_noise': None, 'enable_input_bias': True, 'exclude_reasoner_weights_from_checkpoint': False}
[10-29 04:17:19|WARNING|../../psm_wma_v3/cosmos-framework/cosmos_framework/model/generator/omni_mot_model.py:321:set_precision] OmniMoTModel: precision torch.bfloat16
[10-29 04:17:19|INFO|../../psm_wma_v3/cosmos-framework/cosmos_framework/data/generator/processors/base.py:169:**init**] Successfully loaded processor from local cache
[10-29 04:17:22|INFO|../../psm_wma_v3/cosmos-framework/cosmos_framework/model/generator/tokenizers/wan2pt2_vae_4x16x16.py:1165:_video_vae] loading /mnt/data/shenzhen/szrobot/logs/.tmp_backup/models/Wan2.2-TI2V-5B/Wan2.2_VAE.pth
[10-29 04:17:22|INFO|../../psm_wma_v3/cosmos-framework/cosmos_framework/utils/distributed.py:672:sync_model_states] Synchronizing model states from rank 0 to all ranks in process group [0, 1, 2, 3].
`torch_dtype` is deprecated! Use `dtype` instead!
`torch_dtype` is deprecated! Use `dtype` instead!
`torch_dtype` is deprecated! Use `dtype` instead!
[10-29 04:17:25|INFO|../../psm_wma_v3/cosmos-framework/cosmos_framework/utils/timer.py:138:_log] Time spent on OmniMoTModel: set_up_tokenizers: 6.05 s
[10-29 04:17:25|INFO|../../psm_wma_v3/cosmos-framework/cosmos_framework/utils/generator/parallelism.py:177:_build_mesh] Building 2-D device mesh with ['dp_replicate', 'dp_shard'], [1, 4]
`torch_dtype` is deprecated! Use `dtype` instead!
[10-29 04:17:27|INFO|../../psm_wma_v3/cosmos-framework/cosmos_framework/utils/timer.py:138:_log] Time spent on meta to cuda and broadcast model states: 1.28 s
[10-29 04:17:27|INFO|../../psm_wma_v3/cosmos-framework/cosmos_framework/utils/timer.py:138:_log] Time spent on Creating PyTorch model and ema if enabled: 1.58 s
[10-29 04:17:27|INFO|../../psm_wma_v3/cosmos-framework/cosmos_framework/utils/timer.py:138:_log] Time spent on OmniMoTModel: set_up_model: 1.58 s
[10-29 04:17:27|INFO|../../psm_wma_v3/cosmos-framework/cosmos_framework/utils/timer.py:138:_log] Time spent on init_model: 7.64 s
/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/cosmos-framework/.venv/lib/python3.13/site-packages/torch/distributed/c10d_logger.py:83: UserWarning: barrier(): using the device under current context. You can specify `device_id` in `init_process_group` to mute this warning.
  return func(*args, **kwargs)
[10-29 04:17:27|WARNING|../../psm_wma_v3/cosmos-framework/cosmos_framework/checkpoint/dcp.py:397:**init**] keys_to_skip_loading=['net_ema.', 'local_memory']; checkpoint parameters matching these patterns will not be loaded. Set keys_to_skip_loading=[] to load all matching modules.
/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/cosmos-framework/.venv/lib/python3.13/site-packages/torch/distributed/checkpoint/utils.py:483: UserWarning: torch.distributed is disabled, unavailable or uninitialized, assuming the intent is to load in a single process.
  return func(*args, **kwargs)
/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/cosmos-framework/.venv/lib/python3.13/site-packages/torch/distributed/checkpoint/utils.py:483: UserWarning: torch.distributed is disabled, unavailable or uninitialized, assuming the intent is to load in a single process.
  return func(*args, **kwargs)
/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/cosmos-framework/.venv/lib/python3.13/site-packages/torch/distributed/checkpoint/utils.py:483: UserWarning: torch.distributed is disabled, unavailable or uninitialized, assuming the intent is to load in a single process.
  return func(*args, **kwargs)
/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/cosmos-framework/.venv/lib/python3.13/site-packages/torch/distributed/checkpoint/utils.py:483: UserWarning: torch.distributed is disabled, unavailable or uninitialized, assuming the intent is to load in a single process.
  return func(*args, **kwargs)
[10-29 04:17:27|INFO|../../psm_wma_v3/cosmos-framework/cosmos_framework/checkpoint/dcp.py:475:_skip_keys_if_found] [RANK 0] [DCP-LOAD-SKIP-KEYS] kept_keys=549 dropped_keys=0
[10-29 04:17:27|INFO|../../psm_wma_v3/cosmos-framework/cosmos_framework/checkpoint/dcp.py:475:_skip_keys_if_found] [RANK 1] [DCP-LOAD-SKIP-KEYS] kept_keys=549 dropped_keys=0
[10-29 04:17:27|INFO|../../psm_wma_v3/cosmos-framework/cosmos_framework/checkpoint/dcp.py:475:_skip_keys_if_found] [RANK 2] [DCP-LOAD-SKIP-KEYS] kept_keys=549 dropped_keys=0
[10-29 04:17:27|INFO|../../psm_wma_v3/cosmos-framework/cosmos_framework/checkpoint/dcp.py:475:_skip_keys_if_found] [RANK 3] [DCP-LOAD-SKIP-KEYS] kept_keys=549 dropped_keys=0
[10-29 04:17:29|INFO|../../psm_wma_v3/cosmos-framework/cosmos_framework/utils/generator/optimizer.py:364:_build_params_with_metadata] Total tensors: 549, trainable tensors: 549, selected tensors: 294
[10-29 04:17:29|INFO|../../psm_wma_v3/cosmos-framework/cosmos_framework/utils/generator/optimizer.py:569:**init**] Building optimizer for mesh 'dp_shard'
[10-29 04:17:29|INFO|../../psm_wma_v3/cosmos-framework/cosmos_framework/utils/generator/optimizer.py:404:_build_optimizer_internal] Param group (lr=5e-05, weight_decay=0.05): 289 tensors, 1,414,921,408 elements
[10-29 04:17:29|INFO|../../psm_wma_v3/cosmos-framework/cosmos_framework/utils/generator/optimizer.py:404:_build_optimizer_internal] Param group (lr=0.00025, weight_decay=0.0): 4 tensors, 8,456,192 elements
[10-29 04:17:29|INFO|../../psm_wma_v3/cosmos-framework/cosmos_framework/utils/generator/optimizer.py:404:_build_optimizer_internal] Param group (lr=0.00025, weight_decay=0.05): 1 tensors, 2,048 elements
[10-29 04:17:29|INFO|../../psm_wma_v3/cosmos-framework/cosmos_framework/utils/generator/optimizer.py:154:_optimizer_cls] FusedAdam: master_weights=False (derived from parameter dtypes)
[10-29 04:17:29|INFO|../../psm_wma_v3/cosmos-framework/cosmos_framework/utils/generator/fused_adam.py:91:**init**] FusedAdam master_weights: False capturable: True
[10-29 04:17:29|INFO|../../psm_wma_v3/cosmos-framework/cosmos_framework/utils/generator/optimizer.py:583:**init**] Created 1 optimizers
[10-29 04:17:29|INFO|../../psm_wma_v3/cosmos-framework/cosmos_framework/utils/generator/optimizer.py:784:**init**] Created 1 schedulers
[dense0a] rank=1 loss=15.298787117 weighted=3.824696779 n=128 grads=294
[dense0a] rank=2 loss=14.900200844 weighted=3.725050211 n=128 grads=294
[dense0a] rank=0 loss=15.290845871 weighted=3.822711468 n=128 grads=294
[dense0a] rank=3 loss=15.045043945 weighted=3.761260986 n=128 grads=294
[dense0b] rank=1 loss=15.298787117 weighted=3.824696779 n=128 grads=294
[dense0b] rank=2 loss=14.900200844 weighted=3.725050211 n=128 grads=294
[dense0b] rank=3 loss=15.045043945 weighted=3.761260986 n=128 grads=294
[dense0b] rank=0 loss=15.290845871 weighted=3.822711468 n=128 grads=294
[compact1] rank=2 loss=14.900200844 weighted=3.725050211 n=128 grads=294
[compact1] rank=1 loss=15.298787117 weighted=3.824696779 n=128 grads=294
[compact1] rank=0 loss=15.290845871 weighted=3.822711468 n=128 grads=294
[compact1] rank=3 loss=15.045043945 weighted=3.761260986 n=128 grads=294
[rank3] verdict=FAIL_PARITY formal_pass=False -> /tmp/v3_gpu_parity_rank3_v2.json[rank0] verdict=FAIL_PARITY formal_pass=False -> /tmp/v3_gpu_parity_rank0_v2.json
[rank2] verdict=FAIL_PARITY formal_pass=False -> /tmp/v3_gpu_parity_rank2_v2.json

[rank1] verdict=FAIL_PARITY formal_pass=False -> /tmp/v3_gpu_parity_rank1_v2.json
[rank0]:[W1029 04:18:49.141643271 ProcessGroupNCCL.cpp:1553] Warning: WARNING: destroy_process_group() was not called before program exit, which can leak resources. For more info, please see [https://pytorch.org/docs/stable/distributed.html#shutdown](https://pytorch.org/docs/stable/distributed.html#shutdown) (function operator())
[rank1]:[W1029 04:18:50.379140291 ProcessGroupNCCL.cpp:1553] Warning: WARNING: destroy_process_group() was not called before program exit, which can leak resources. For more info, please see [https://pytorch.org/docs/stable/distributed.html#shutdown](https://pytorch.org/docs/stable/distributed.html#shutdown) (function operator())
[rank2]:[W1029 04:18:50.414795785 ProcessGroupNCCL.cpp:1553] Warning: WARNING: destroy_process_group() was not called before program exit, which can leak resources. For more info, please see [https://pytorch.org/docs/stable/distributed.html#shutdown](https://pytorch.org/docs/stable/distributed.html#shutdown) (function operator())
[rank3]:[W1029 04:18:50.419607238 ProcessGroupNCCL.cpp:1553] Warning: WARNING: destroy_process_group() was not called before program exit, which can leak resources. For more info, please see [https://pytorch.org/docs/stable/distributed.html#shutdown](https://pytorch.org/docs/stable/distributed.html#shutdown) (function operator())