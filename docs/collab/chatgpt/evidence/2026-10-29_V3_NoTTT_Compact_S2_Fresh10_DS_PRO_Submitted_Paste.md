# 归档说明

- 来源：Owner 于 2026-10-29 会话中粘贴的 DS_PRO 独立执行报告。
- 本文件归档该报告正文；不代表 GPT 已取得或独立回读服务器上的 `launch.log`、`train_rank0.jsonl`、identity 或 checkpoint 原件。
- 原报告的相对路径指向 DS 现场证据目录；本次没有把这些路径转换成已上传工件。
- 审核结论另见 [Fresh10 增量审核](../reviews/2026-10-29_V3_NoTTT_Compact_S2_Fresh10_Incremental_Review.md)。原报告的时间与显存表述保留，审核中单独说明其口径限制。

---

# DS_PRO — Compact=1 No-TTT S2 Fresh Rebuild 至总 iter10（独立执行报告）

- 日期：2026-10-29（CST）。DS_PRO 独立执行报告。
- 授权链：ChatGPT 正式授权 `APPROVE_S2_RESUME_TO_ITER10_ONLY`（commit `9cc37557a538d5c9df29923aa069c5c17400f119`）→ DS 执行文件 `2026-10-29_V3_NoTTT_Compact_S2_Resume10_DS_PRO.md` → 原 S2 因 S1 iter1 checkpoint 缺失判 `BLOCKED_BEFORE_RUN` → **Owner 明确回复“被我清理了，授权 fresh 重建”** → Owner 选定新 Job 名 `no_ttt_compact1_corerun_fresh_20261029_world4_ga4`。
- 本报告为 **fresh 重建**执行结果，不是原 `resume` 语义；`resume` 分支的 BLOCKED 报告见 `../2026-10-29_V3_NoTTT_Compact_S2_Resume10_DS_PRO_BLOCKED/report.md`。

## 1. 执行身份与环境（实际现场记录）

- Root / Child：`nott_world4_ga4_source_head_not_verified`（identity 记录的正式身份；4GPU No-TTT profile 按 Owner 授权豁免 Root/Child HEAD/Gitlink 硬门）。
- 工作目录：`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma_v3`
- Python / import 来源：`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/cosmos-framework/.venv/bin/python`；PYTHONPATH 注入 `cosmos-framework` 子目录。
- 实际环境变量（launch.log 首段）：   - `JOB_NAME=no_ttt_compact1_corerun_fresh_20261029_world4_ga4`   - `PHASE=fresh UNTIL=10`   - `OUTPUT_ROOT=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma_v3/outputs/no_ttt_robocasa_raw15`   - `PSM_V3_COMPACT_CACHED_VIDEO=1`   - `CUDA_VISIBLE_DEVICES=4,5,6,7`   - `SOURCE_ROOT=/mnt/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic`   - `CACHE_ROOT=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/datasets/robocasa365-target-atomic-left_wrist-exact_window`   - `DATASET_INDEX_ROOT=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/datasets/robocasa365-target-atomic-verified-index-r1`   - `EDGE_POLICY_CHECKPOINT=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/models/Cosmos3-Edge-Policy-DROID`   - `WAN_VAE_PATH=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/models/Wan2.2-TI2V-5B/Wan2.2_VAE.pth`   - `BASE_CHECKPOINT_PATH=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/models/Cosmos3-Edge-Policy-DROID-dcp`   - `NOTTT_LOADER_WORKERS=0`；prefetch/persistent/timeout 均未设置（workers=0 禁用）。
- 六数据/模型路径从 S1 identity `semantic.source_paths` 读取，全部绝对路径且存在；未修改任何 identity。

## 2. Job / Namespace 与训练语义

- Namespace：`$OUTPUT_ROOT/psm_wma_v3/corrected_phase5/no_ttt_compact1_corerun_fresh_20261029_world4_ga4`
- Launcher 固定参数：`--no-ttt --phase fresh --formal-execution-until 10 --world-size 4 --t 16 --b 8 --ga 4 --k 4 --max-iter 30000 --warmup 500 --save-iter 100 --num-workers 0`（launch.json 确认 `execution_stop_after_iter=10`）。
- 身份摘要：`max_iter=30000`、`warm_up_steps=500`、`save_iter=100`、`grad_accum_iter=4`（GA4）、`distributed_parallelism=fsdp`、`data_parallel_shard_degree=4`（4卡 FSDP2）、`keys_to_select=[moe_gen,time_embedder,vae2llm,llm2vae,action2llm,llm2action,action_modality_embed]`（Generation keys，`requires_grad=False` 之外，共 294 个优化参数）。
- `compact_cached_video=true`、`num_workers=0`（telemetry 每步确认）。
- 启动即从 Base Checkpoint 热启动：`DCP-LOAD … Loaded checkpoint from Cosmos3-Edge-Policy-DROID-dcp (warm-start, local) in iteration 0`（launch.log）；无 S1 checkpoint 可恢复（已由 Owner 清理）。

## 3. 执行结果

- 运行窗口：09:14:38 初始化 → 09:18:12 训练开始 → 09:21:36 iter10 commit → 09:21:52 `SUCCESS Done with training.`
- 提交记录：**iter1–iter10 全部 `optimizer_committed`，共 10 次新增提交**（fresh，无恢复点）。
- `last_completed_iteration = 10`；`last_saved_checkpoint = iter_000000010`（`checkpoints/iter_000000010`，`latest_checkpoint.txt=iter_000000010`，`complete.v1.json`：`complete=true, iteration=10, schema=psm_v3_sync_local_v1, world_size=4`，含 4 rank model/optim/scheduler/trainer distcp sidecar SHA）。
- 进程正常退出于执行上限 iter10，未继续到 100/30000；`pgrep formal-execution-until 10` 为 0 进程。
- Checkpoint 文件大小与 `complete.v1.json` 逐文件核对 `ALL_MATCH`（model/optim/scheduler/trainer 13 个 distcp 文件）。

### 每步健康字段（rank0 本地，`monitor/train_rank0.jsonl`）

| iter | status | outer_loss | action_loss | vision_loss | total_grad_norm | missing | nonfinite | grad_tensors | wall_s | data_prepare_s | peak_reserved_GiB |
| ---- | ------------------- | ---------- | ----------- | ----------- | --------------- | ------- | --------- | ------------ | ------ | -------------- | ----------------- |
| 1 | optimizer_committed | 14.9375 | 1.2276 | 0.2662 | 3.7066 | 0 | 0 | 294 | 21.0 | 6.8 | 29.84 |
| 2 | optimizer_committed | 14.5719 | 1.2242 | 0.2330 | 3.1272 | 0 | 0 | 294 | 20.1 | 5.4 | 32.17 |
| 3 | optimizer_committed | 14.4554 | 1.2130 | 0.2325 | 3.3553 | 0 | 0 | 294 | 22.8 | 5.3 | 32.17 |
| 4 | optimizer_committed | 14.5263 | 1.2263 | 0.2263 | 3.2350 | 0 | 0 | 294 | 19.9 | 5.4 | 32.17 |
| 5 | optimizer_committed | 14.5468 | 1.2249 | 0.2298 | 3.6029 | 0 | 0 | 294 | 19.7 | 5.9 | 32.17 |
| 6 | optimizer_committed | 14.3856 | 1.2188 | 0.2198 | 3.1697 | 0 | 0 | 294 | 23.3 | 5.2 | 32.17 |
| 7 | optimizer_committed | 14.2702 | 1.2135 | 0.2136 | 3.4845 | 0 | 0 | 294 | 17.9 | 5.4 | 32.17 |
| 8 | optimizer_committed | 14.4900 | 1.2111 | 0.2379 | 3.6512 | 0 | 0 | 294 | 19.4 | 5.5 | 32.17 |
| 9 | optimizer_committed | 14.4245 | 1.2083 | 0.2342 | 3.7046 | 0 | 0 | 294 | 20.6 | 4.9 | 32.17 |
| 10 | optimizer_committed | 14.7728 | 1.2256 | 0.2517 | 3.3800 | 0 | 0 | 294 | 18.5 | 5.6 | 32.17 |

- 全部 10 步：`missing_grad_tensors_rank_local=0`、`nonfinite_grad_tensors_rank_local=0`、`telemetry_errors=[]`、`consumer_audit_status=OBSERVED`、`compact_cached_video=true`、`num_workers=0`。
- 未补造未测 Rank 峰值；仅记录 rank0 实测值（iter1 为 29.84 GiB，iter2–10 为 32.17 GiB）。GPU4–7 全程无 OOM（每卡空闲约 43–46 GiB）。
- checkpoint 保存：`[CorrectedV3][checkpoint] {"checkpoint_save_ms": 16257.35, "iteration": 10}`。
- launch.log 无 ERROR / traceback / OOM / NCCL 异常。

## 4. 旧 Job 观测（未被本次触碰）

- 旧正式 No-TTT Job `no_ttt_packed128_droid_fresh_30k_world4_ga4`（pid 1202529–1202532 + launcher 1202385）在 GPU4–7 全程运行，本次未改动/未终止。
- 观察期推进：iter≈7400 → **iter=7622**（09:29:58，epoch=7，`missing=0 nonfinite=0`，峰值 35.66 GiB）。与 S2 fresh 共存，峰值约 32.2 + 35.7 GiB/卡，在 80 GiB 卡内。
- 结论按执行文件要求记录实际推进，不作为“零性能干扰”或稳态性能声明。

## 5. 输入见证状态

- 原执行文件 §4 允许并行补证（非启动前置 Gate）。本轮 fresh 执行未新增输入见证探针；**输入见证保持 OPEN**，未执行。
- 未测字段：aux_loss_gen/und、local memory 相关、memory_inventory、param_norm、state_fingerprint 均按现场 telemetry 为 null/NOT_MEASURED，未补跑。

## 6. 结论

- **S2 = PASS（fresh 重建变体）。** 理由：fresh 从 iter0 热启动连续 commit iter1–iter10，共 10 次新增提交；10 步全部 optimizer_committed、0 missing、0 nonfinite、294 grads；进程在 formal 上限 iter10 正常 `SUCCESS Done with training.` 退出，未继续到 100/30000；checkpoint iter10 完整（4 rank sidecar + complete.v1.json + latest_checkpoint.txt）；未改动/终止旧 Job。
- 保留判定（不因本 PASS 改变）：**历史严格 Gradient Gate 始终 FAIL_PARITY**；**Compact 归因仍 INCONCLUSIVE**。
- 原 `resume` 分支判定不变：`BLOCKED_BEFORE_RUN`（S1 checkpoint 缺失，Owner 确认已清理并授权 fresh 重建）。

## 7. 证据路径

- launch 日志：本目录 `launch.log`（= `/tmp/s2_fresh_launch_20261029T091427Z.log`）
- Job telemetry：`$OUTPUT_ROOT/psm_wma_v3/corrected_phase5/no_ttt_compact1_corerun_fresh_20261029_world4_ga4/monitor/{rank0.log,train_rank0.jsonl}`
- launch.json：`…/no_ttt_compact1_corerun_fresh_20261029_world4_ga4/launches/6bc6ac953cb746629ddafe290b55ead8/launch.json`
- identity：`…/v3_job_identity.json`（`canonical_config_sha256`、`semantic_digest` 见该文件）
- checkpoint：`…/checkpoints/iter_000000010/complete.v1.json` + `latest_checkpoint.txt`

## 8. 后续边界

- 按执行文件：完成本次后停止，不自动进入 100/30k；后续范围依据本轮证据再决定。
- 本地 V3 与 origin/V3 分叉（本地 4 个 evidence commit 未推送）待 Owner 决策。
