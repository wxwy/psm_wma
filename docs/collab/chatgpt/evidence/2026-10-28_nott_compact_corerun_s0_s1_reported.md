# DS_PRO — No-TTT Compact=1 第二套共存 Job：S0/S1 结果记录（报告原文摘要）

- 日期：2026-10-28 CST。
- Gate：`V3_NOTTT_COMPACT_CORESIDENT_SECOND_JOB`。
- **来源与等级**：用户于会话中完整粘贴 DS_PRO 的 S0/S1 报告。本文件保留全部关键数值与执行语义，但并非实际 rank 日志、DCP manifest、NVML时序或原生机器生成JSON；远端 V3 当前**未找到**报告自称的 `docs/collab/chatgpt/evidence/2026-10-28_nott_compact_corerun_s0_s1.{json,md}`。禁止冒充独立复现。
- 执行令：`docs/collab/chatgpt/requests/2026-10-28_V3_NoTTT_Compact_Coresident_Second_Job_StagePlan.md`。
- 测试时 Root：`4cf90fb486db9c8e2a4b93aaa7d9f5438296f642`；Child/Gitlink：`746c5cf2f2324104a62fb71510343aa40d3976c5`。
- 旧 Job：`no_ttt_packed128_droid_fresh_30k_world4_ga4`。
- 新 Job：`no_ttt_compact1_corerun_20261028_world4_ga4`。

## S0 报告：PASS_1_STEP_ADMISSION

S0 时间：2026-10-28 08:13:57 UTC。

| GPU | total MiB | existing used MiB | projected margin=total−2×used MiB | criterion ≥4096MiB |
|---|---:|---:|---:|---|
| 4 | 81559 | 38177 | 5205 | PASS |
| 5 | 81559 | 35591 | 10377 | PASS |
| 6 | 81559 | 35885 | 9789 | PASS |
| 7 | 81559 | 35551 | 10457 | PASS |

- RAM：总2015GiB、free268GiB、available1626GiB（按 DS 报告单位）。
- CPU：192 cores、load 11.18。
- /mnt/data 磁盘 99% used，准入前报告 free97GiB。
- 旧 Job 基线 iter4828，`optimizer_committed`、`telemetry_errors=[]`、`peak_reserved=35.66GiB`，报告写`num_workers=0`；**此字段不等同 `NOTTT_LOADER_WORKERS`，不能仅凭这个值推断旧 Job 0 CPU spawn workers**。

## S1 报告：1 个真实完整训练 optimizer step 成功

- 命令：`bash scripts/train_v3_matched_no_ttt_4gpu.sh fresh 1`。
- 环境：`JOB_NAME=no_ttt_compact1_corerun_20261028_world4_ga4`、`PSM_V3_COMPACT_CACHED_VIDEO=1`、`NOTTT_LOADER_WORKERS=0`、`CUDA_VISIBLE_DEVICES=4,5,6,7`；prefetch/persistent/timeout 环境参数未设置。
- 虚拟环境：与旧 No-TTT 相同的 `psm_wma/cosmos-framework/.venv/bin/python`（torch2.10.0+cu128；msc0.44.0）。第一次因 child `.venv` 的 torch2.14.1+cu130 / 驱动 cu128 和缺 multistorageclient 失败；改用旧环境成功，未改生产源码。
- 输入：只读 DROID Base `Cosmos3-Edge-Policy-DROID-dcp`；RoboCasa accepted Cache + Verified Index；新 Job独立 namespace。
- Rank0 记录：`iteration=1`；`status=optimizer_committed`；`outer_loss=14.9375`；`action_loss=1.2276`；`vision_loss=0.2662`；`total_grad_norm_rank_local=3.7072`；`nonfinite=0`；`missing=0`；`telemetry_errors=[]`。
- Rank0内存：`peak_allocated=25.18GiB`，`peak_reserved=29.84GiB`。
- `step_wall_s=27.18`，`data_prepare_ms=8629.6`，`num_workers=0`，`data_wait_reason=synchronous_producer_no_background_dataloader`。这只是新 Job 的首次 Step，不是稳态性能Benchmark。
- 新 Job Checkpoint：`checkpoints/iter_000000001/` 报告24GiB，含 `trainer/dataloader/model/optim/scheduler`；`latest_checkpoint.txt=iter_000000001`；`v3_job_identity.json` schema `corrected_phase5_f0_v1`；4 rank进程在完成后退出。
- 旧 Job在S1前后从 iter4828→4858，报告未发现NaN/OOM/NCCL或停滞；**只能表述“继续推进且无报告错误”，不能证明同时运行时的吞吐“零影响”**。
- /mnt/data报告首个Checkpoint后剩余74GiB；训练后续每新 DCP 约24GiB，若无保留/清理方案继续跑10/100/30k有严重耗尽磁盘风险。
- DS 初算：GPU4剩余`81559−38177−29840`。实际内存单位换算：`29.84GiB=30556MiB`，如果Rank0即GPU4且按对应峰值估算，余量≈`12826MiB=12.53GiB`；不能将Rank0 `max_memory_reserved` 与同一时刻 NVML 实测混为一谈。其它 Rank peak 尚缺原始数据。
- GPU0–3 外部 wzy任务未被触碰；旧正式Job进程/Checkpoint/Job identity 未修改（按 DS 报告）。

## 当前审核状态和后续边界

- S0/S1 报告数据**支持 1-step 运行成功**，但还不是独立核验了全部原始 Evidence 的正式 PASS。
- 应补齐现存 S0/S1 JSON/MD，rank0原始`optimizer_committed`行/Checkpoint保存行，4Rank进程退出与GPU peak、实际DCP结构和rank sidecar、旧 Job前后对应日志及资源；**不重复运行S1**。
- 上述数据只许可结束S0/S1 Evidence Gate，不许可自动跑S2 10/100/30k，也不代替同权重同冻结Batch的Compact0/1 GPU Loss/Gradient parity。
- 原独占GPU Parity S0 `BLOCKED_RESOURCE` 是当时正确结果；新共存实验的S0/S1不能倒推独占资源Gate已经通过。
