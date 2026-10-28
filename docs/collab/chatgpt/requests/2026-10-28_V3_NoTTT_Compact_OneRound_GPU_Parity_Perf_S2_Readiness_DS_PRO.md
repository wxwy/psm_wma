# DS_PRO 单轮执行包 — No-TTT Compact=0/1 GPU Native Parity + 现有速度对照 + S2 就绪检查

- 日期：2026-10-28。执行人 DS_PRO，审核人 GPT。**本轮只提交一份最终汇总，不必每做完一个 Task 就回复/等待 GPT。**
- formal No-TTT Root historical implementation: `49df7f3c2e0ba8ef5871f9dd490e41fbc3dc5da9`；Child/Gitlink: `746c5cf2f2324104a62fb71510343aa40d3976c5`。当前 Root HEAD 仅当运行 provenance 记录，不得拿 bookkeeping SHA 当 formal implementation。Child/Gitlink不同则 B 不执行；A/C 已有资料仍可交付。
- 权威数值 Gate 合同（保持不变）：`docs/collab/chatgpt/requests/2026-10-28_V3_NoTTT_Compact_GPU_Native_Parity_DS_PRO.md`；现有 `REQUEST_CHANGES` finding: `docs/collab/chatgpt/reviews/2026-10-28_V3_NoTTT_Compact_GPU_Forward_Loss_Gradient_Parity_Evidence_Review.md`。
- Owner 已接受 GPU4–7 **co-resident** 的模型实验（不需4张完全空闲卡）；仅替代旧合同“必须完全空闲”的资源准入条件。严格执行其余**同权重/同Batch/同RNG/逐参数梯度/无Optimizer/DCP**条件。
- 存储/Checkpoint保留与自动清理由Owner管理，不再作为GPT/DS Gate检查范围；`save_iter=100` 永久保持，除非Owner后来单独修改。禁止本轮任何文件删除/清理、修改Cleaner、改生产配置/代码、改旧Job或动GPU0–3。
- **并行关系**：A读取已有日志；C核对现有Job Resume readiness；B为独立新 GPU Harness。A/C无须等 B，彼此不依赖。DS可以先做轻量只读A/C再做B，也可以在B期间低负载读取，不准为并行制造CPU/IO争用。**B的成败不影响A/C交付**。

## A — 只读一次抽取现有三组 Fresh1 的速度数据

**不得重新训练、不得创建新Namespace、不得跑CPU Benchmark。**

从这三Job已保留的 `monitor/train_rank0.jsonl`、`monitor/rank0.log` 和 `launch/config` 读取 iteration=1：

- A: `no_ttt_compact1_gpu_parity_world4_ga4` （Compact1）
- B: `no_ttt_compact0_gpu_parity_world4_ga4` （Compact0）
- C: `no_ttt_compact1_gpu_parity_r2_world4_ga4` （Compact1 repeat）

对三行分别原样提取，不能用不同口径的历史NoTTT旧Job代填：

1. `step_wall_ms`、`data_prepare_ms`、`batch_collate_ms`、`batch_transfer_ms`、`forward_ms`、`backward_ms`、`optimizer_ms`、`other_host_overhead_ms`，以及 available 的 `gpu_data_stall_ms`、`source_read_ms`/CPU loader stats。缺项记 `NOT_RECORDED`。
2. `valid_consumers`、`native_forward_calls/backward_calls`、`batch identity SHA (full if available)`，`action/vision/outer loss`，`num_workers` 与 **`no_ttt_loader_workers` 分别注明**（不能拿一个代替另一个）。
3. `peak_allocated_gib` / `peak_reserved_gib`、`compact_cached_video`、`telemetry_errors`。
4. 三个Job实验起点的 `config_digest / model checkpoint / source cache index / precision / effective world4-GA4` 是否相同。存在身份不一致，给出差异，不把速度归咎于Compact。

**统一结果**：A/B/C对照表 + `B vs median(A,C)` 的观察差值，至少分 `data_prepare` 与 `step_wall`。精确标注“仅一次Fresh1/Job，GPU4–7与旧Job共存、存在竞争/冷启动，**非稳态加速结论**”；不要为取得稳态而新启动10/100步实验。能从旧NoTTT已有监控取到同一时间段Step Wall分布时附在备注（只读），不能误当相同权重的Compact0对照。

## B — 唯一 GPU 实验：真正4Rank FSDP2 配对 Native Parity

**本任务可以与A/C独立执行；但必须单独做S0共存安全预检。**

- GPU严格`4,5,6,7`，不碰`0–3`；记录旧Job运行进度/错误状态和新GPU已用显存。参考先前 Compact1 Fresh1 peak≈29.84GiB/rank0，实际每rank状态以本轮新鲜NVML为准。允许现存正式NoTTT占卡；没有足够实测余量（建议≥8GiB/卡在预计探针峰值以上）、旧Job有OOM/卡住/额外陌生进程入侵时：`BLOCKED_CORESIDENCY`，**不开始torchrun**；仍完整交付A/C。模型运行期间发现旧Job受伤害或新Job显存异常，只停止新Harness，不许杀停旧正式Job。
- 只创建 **独立临时`/tmp` Harness**（亦可提交 `docs/collab/chatgpt/evidence` 的测试脚本），不能调用正式`train_v3_matched_no_ttt_4gpu.sh`或`corrected_phase5.main()/trainer.train()`，不能调用任何Optimizer/Scheduler Step、写DCP/Job Identity、保存正式checkpoint。**不再重复三套 Fresh1**。
- 必须用训练同款 `psm_wma/cosmos-framework/.venv/bin/python`（torch2.10+cu128），而非Child不兼容`.venv`；HF offline。
- 真实`world_size=4` / Native Model/`local_memory_enabled=False` / FSDP2 sharded model，模型训练态 train()，沿用NoTTT`overlay_config`的precision、激活Checkpoint和compile设置；DROID Base checkpoint只读加载，禁止读旧NoTTT正在运行的DCP。
- 同一张冻结计划：`ExactWindowRankPlanner(rank=RANK,world4,B8,T16,GA4,seed=0)`；只取`plan.members[0]`（每rank128 valid Consumers，归一权重约`128/512=0.25`），两种模式输出Native Packed Batch在CPU先逐项比较并冻结。复用已关闭的`CPU parity`结构，不重跑其全套512/partial Benchmark；对真实Native input经`move_cached_native_batch`后的非Video Tensor再比较shape/dtype/value/device，Video允许Compact代理在CPU保留且逻辑全零。
- 相同已加载**模型权重和buffers**，单个进程生命周期中按 **Dense0→Compact1** 分别执行`model.training_step(native_batch,same_iteration)`与`weighted_loss.backward()`，两侧前恢复相同`Python/NumPy/TorchCPU/CUDA per-rank RNG`、清理上一侧gradient，核实权重/Buffer未变化；必要warmup后确保A/B同一数学状态。
- 遍历 **全部 optimizer selected trainable parameters**（`GENERATION_KEYS`，action与video generation全覆盖），FSDP `DTensor.to_local` 取**每rank分片**。Dense侧梯度仅存内存CPU用于比较，不写模型/Gradient DCP。Compact侧逐参数比：相同名称/分组、`None mask`、local shape/dtype、finite、`torch.allclose(rtol=1e-3,atol=1e-5)`，保存`max_abs, relative_L2, worst10, selected/covered/group counts`。不能只比较整体`grad norm`。
- Compare所有可见`output` key set、Tensor shape/dtype、标量`outer/weighted/action/vision loss`用`rtol=1e-4,atol=1e-5`；其它Tensor输出按适合其数学语义的逐值对照，不能只核三个scalar。
- **一次明确的Fail-closed规则**：四rank全部真正通过方可`PASS_CANDIDATE`；若有grad/输出差异按冻结`FAIL_PARITY`，可以仅一次Dense→Dense重放诊断GPU随机性（不放宽tolerance、不切推理mode）；若运行错误/OOM/安全风险则`FAIL_RUNTIME`或`BLOCKED_CORESIDENCY`；若不能无写入正确构建真实模型`BLOCKED_HARNESS`。不得绕过限制改生产代码，不能自行宣称formal Gate CLOSED。
- 特别注意：三次`fresh1`旧报告的`model sha/optim sha`来自DCP `.metadata`，与参数数值等价无关，**本轮完全不要再以其差异证明backward噪声**。

## C — S2 新Job Resume Readiness 只读检查（不执行Resume）

- 目标：`no_ttt_compact1_corerun_20261028_world4_ga4`（`Compact=1`那一个已经 `fresh 1` 成功的新Job）；不得误指旧`no_ttt_packed128_droid_fresh_30k_world4_ga4`。
- 检查`latest_checkpoint.txt`指向`iter_000000001`，`complete.v1.json`的`schema/complete/iteration/world_size=4`、model/optim/scheduler/trainer metadata、`dataloader/rank_0..3.pkl`，`v3_job_identity.json` `training_semantic/config_digest/save_iter=100`，以及绝不能新建Fresh覆盖已有Namespace。**完整rank3-sidecar SHA只读拷贝原文，不能使用之前粘贴的占位符`read_from_complete_v1_json`**。
- 如果新的 Job Checkpoint已被Owner的正常本地清理程序清理：标记`CHECKPOINT_NOT_PRESENT`，停止本Task，不猜测能Resume，也不请求Owner更改清理规则。
- 检查运行同款`PYTHON`、`PSM_V3_COMPACT_CACHED_VIDEO=1`、`NOTTT_LOADER_WORKERS`及必需的`OUTPUT_ROOT/SOURCE_ROOT/CACHE_ROOT/DATASET_INDEX_ROOT/EDGE_POLICY_CHECKPOINT/WAN_VAE_PATH/BASE_CHECKPOINT_PATH`路径契约；只输出待Owner/GPT以后审阅的 `resume 命令草案`，**不得执行**。
- 不审查磁盘可用空间、Cleaner的retention规则、不强制列Owner保留点，不需要为此再对24GB DCP全量hash。Checkpoint若已由`complete.v1.json`声明，读取/验证元数据及存在性并明确“未重做强hash验真”的边界即可；不能虚称完成真实DCP可恢复测试。
- 输出：`S2_READINESS=READY_BY_STATIC_CHECKS / CHECKPOINT_NOT_PRESENT / BLOCKED_SEMANTIC / NOT_VERIFIED` + gap；不等于许可继续训练。

## 一次性交付包（合并后只向GPT报告一次）

统一路径 `docs/collab/chatgpt/evidence/2026-10-28_V3_NoTTT_Compact_OneRound/`：

- `summary.md`：A/B/C三任务状态、最重要结论、准确旧/新Job身份、模型/数据/SourceSHA、报告边界、现有正式Job健康状态、剩余问题。
- `summary.json`：`A_perf_rows`（3 Jobs真实全量时间字段和可用性标记）、`B_gpu_parity`（各Rank各参数group/worst10/allclose、总 verdict及代码环境）、`C_s2_readiness`（摘要）。
- `gpu_paired_harness.py`：B实验**原样可复现脚本**；必要时单独Rank日志。只归档轻量report，不上传完整模型、Grad Tensor、大DCP、用户数据。
- A的原始`train_rank0.jsonl`三条对应记录（可脱敏）、`C`现成原始`complete.v1.json`与rank-sidecar摘要，如存在并可访问；没有就标`NOT_PRESENT`，不补造。此前`2026-10-28_nott_compact_corerun_s0_s1.{md,json}`若DS本地已有，顺便提交，**但不单独阻塞B验收或要求额外会话**。
- 结果状态固定：`A=RECORDED/INCOMPLETE`、`B=PASS_CANDIDATE/FAIL_PARITY/FAIL_RUNTIME/BLOCKED_CORESIDENCY/BLOCKED_HARNESS/BLOCKED_SOURCE`、`C=READY_BY_STATIC_CHECKS/CHECKPOINT_NOT_PRESENT/BLOCKED_SEMANTIC/NOT_VERIFIED`。不得把A非稳态速度差、C静态就绪或B`PASS_CANDIDATE`自动升级为下一Gate的Owner授权。
- DS在这一轮过程中**不要中途问GPT或把每个小阶段拆成多轮**，只有触发无法安全继续的阻断条件时停止B；A/C仍应独立完成。提交后停止等待GPT一次性 Review。**不允许自行启动 S2 `resume 10/100/30000`、原正式Job Compact切换、旧Job停训、生产代码修改或资源抢占。**
