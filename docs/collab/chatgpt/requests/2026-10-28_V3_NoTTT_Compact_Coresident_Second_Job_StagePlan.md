# Owner 更新：V3 GPU4–7 共存第二套完整 No-TTT Compact=1 — 受控分阶段方案

- 日期：2026-10-28。
- **Owner 明确表态**：除小型 GPU Parity Harness 外，**再启动一套完整 No-TTT 训练也可以接受**；不必一开始停止当前正式 No-TTT。该许可为新的可选执行路线，非“已经启动第二套”。
- 目标：独立 `Compact=1` No-TTT，使用 GPU4–7 与当前 `Compact=0` 正式 No-TTT **共存**；GPU0–3 为他人任务，绝不碰。
- 最重要的安全边界：原正式 Job `no_ttt_packed128_droid_fresh_30k_world4_ga4`、其运行进程/Checkpoint/Job identity/数据均保持不变；所有测试写入**独立新 Job namespace**，绝不能以旧 Job 的 `resume` 为测试方法。
- **本条只授权按 Gate 分阶段推进**：先运行资源/风险准入，符合条件才启动 **1 个 full-configuration optimizer step 的独立新 Job**。先获取 Evidence 并交给 GPT 审核，**不授权未经审核连续运行至30k**。后续真正的30k可在数值/资源 Gate PASS 后继续同一新 Job的正式训练。
- 当前 Child/Gitlink：`746c5cf2f2324104a62fb71510343aa40d3976c5`；Owner决定不修改生产代码。原独占-GPU Gate S0 `BLOCKED_RESOURCE` 对当时执行令仍成立。新方案仅替代本**新共存实验**的“4张必须完全空闲”规则，不追溯更改旧证据或旧Gate结论。

## 1. 正确区分两个任务（DS 不可合并判据）

A. **正式数值等价 Gate（Compact0/1 GPU parity）**：同一权重、同一 Frozen Batch、同一 RNG，真实 Native loss/grad；不执行 optimizer。旧 Gate `docs/collab/chatgpt/requests/2026-10-28_V3_NoTTT_Compact_GPU_Native_Parity_DS_PRO.md` 的模型和数学验收要求仍保留，资源准入可以依据 Owner 的新共存许可另行更新，但**不自动判PASS**。

B. **第二套完整 No-TTT Fresh Job**：`Compact=1` 从已验收 DROID Base 开始，完全匹配4卡 FSDP2/GA4/T16/B8/K4、真实 Forward/Backward/Optimizer，新的独立 Job，初期只跑到 iteration1。能运行和收敛只是功能 Smoke，**不是 Compact0/1 Grad Parity 的替代品**。独立 Fresh、后续 Resume 不得误指当前原正式 Job。

## 2. S0 — 共存资源准入（DS 当前唯一可立即执行的无训练动作）

在服务器**只读**检查：

- `nvidia-smi --query-gpu=index,uuid,memory.used,memory.total,utilization.gpu --format=csv,noheader`
- `nvidia-smi --query-compute-apps=gpu_uuid,pid,used_gpu_memory --format=csv,noheader`
- `free -h`，`df -h "$OUTPUT_ROOT"`；如安全可查 `df -i "$OUTPUT_ROOT"`
- 读取既有正式 No-TTT rank0 最后稳定 Step 和最近 checkpoint（**只读**）。确认原四进程仍在运行、推进、没有 OOM/NaN/NCCL 报错；不可擅停。
- 当前 V3 Root/Child/Gitlink、`scripts/train_v3_matched_no_ttt_4gpu.sh` 和必要数据来源的**只读** SHA/路径；禁止 `git reset --hard`、`git checkout`、`git clean`、`git -c http.sslVerify=false`。

显存准入采取**保守估算**：对每卡 `free_i=total_i-used_i`；用当前同模型 `used_i` 作为第二套复制工作量的初步**估算值，不是新 Compact 实测峰值**，得 `projected_margin_i=total_i-2*used_i`。按先前上报快照 GPU4 预估只有 **约5GiB剩余**，潜在 OOM/原作业受害风险真实存在；不能写“确保安全”。

- **1-step admission**：四卡 `projected_margin_i ≥ 4GiB`，GPU旧任务没有突发增长，主机 RAM 有可用余量且有容量保存**新 Job**至少一个独立模型+DCP完整检查点；无法证实其中任一项，返回 `BLOCKED_CORESIDENCY`，不启动 CUDA/torchrun。
- 准入边界 4GiB **只是实验条件，不是无风险保证**。无权代表Owner承担破坏原正式Job风险；检测到源作业卡住、GPU余量危险/新进程OOM，立即终止**仅新作业**并登记，原正式作业禁止触碰。
- **持续30k admission** 更严格：须取得新Compact Job实测每 Rank `peak_reserved_gib`/NVML峰值（至少取最大Rank/最大Card）、确认稳定吞吐与磁盘/CPU资源、现存原正式训练不恶化，并为最差卡保留建议`≥8GiB`运行余量；无法证明时不许自动升级长时间训练。
- 如果当前任一GPU同时被非允许的第三个Job占用，或CPU/disk严重不足，返回 `BLOCKED_CORESIDENCY`。DS不可自行挪GPU0–3或杀别人任务。

## 3. S1 — 单 Step、完整真实训练配置的新 Job Smoke（仅S0准入后）

经审核的现有脚本 `scripts/train_v3_matched_no_ttt_4gpu.sh` 接受 `fresh EXECUTION_UNTIL`；例如 `fresh 1` 保留 `max_iter=30000`、`warmup=500`、`save_iter=100`、`world4/GA4`，但在真实 committed step1 停止并保存**新 Job**的 DCP。不能把这叫作单纯无写入的 GPU Parity。

- 使用独立的新 Job名：`no_ttt_compact1_corerun_20261028_world4_ga4`。检查对应 `$OUTPUT_ROOT/psm_wma_v3/corrected_phase5/$JOB_NAME` **完全不存在**；存在时`BLOCKED_NAMESPACE`，不得删除/覆盖/Resume。
- 冻结启动条件：`PSM_V3_COMPACT_CACHED_VIDEO=1`，`CUDA_VISIBLE_DEVICES=4,5,6,7`，原已验收 `OUTPUT_ROOT/SOURCE_ROOT/CACHE_ROOT/DATASET_INDEX_ROOT/EDGE_POLICY_CHECKPOINT/WAN_VAE_PATH/BASE_CHECKPOINT_PATH`，DROID Base而非在运行Job的DCP。
- 首次 S1 推荐 `NOTTT_LOADER_WORKERS=0` 以免在现有旧 Job的 32 CPU Workers 外再并发32个 Workers；**此设置是环境/性能保护，不是下一步严格的 Worker8性能对照**。启动后不可据新旧训练数据时间差声称“只有 Compact 不同”；后续恢复需再次确认 CPU Worker 配置，避免无意变更实验对照。
- 不更改`OMP_NUM_THREADS`、`GA`、`T`、`B`、`max_iter`、`warmup`、`save_iter`、`model config`、`source/latent/index`。新 Job的 Trainer同真实训练路径，不允许跳过 optimizer 模拟。
- 唯一授权的首个 Step 命令（在 repo Root 执行，且上述必需环境变量已设置）：

```bash
export JOB_NAME=no_ttt_compact1_corerun_20261028_world4_ga4
export PSM_V3_COMPACT_CACHED_VIDEO=1
export NOTTT_LOADER_WORKERS=0
unset NOTTT_PREFETCH_FACTOR NOTTT_PERSISTENT_WORKERS NOTTT_LOADER_TIMEOUT_S
bash scripts/train_v3_matched_no_ttt_4gpu.sh fresh 1
```

- 由`--formal-execution-until 1` 限制真实 committed iteration=1；**允许**写新 Job的隔离 model/optim/scheduler/trainer/rank-sidecar DCP 和监控；严格禁止写旧 Job任何文件。
- 每次启动前重新检查4张 GPU 的资源状态。观察新旧 Job的显存和进程；如果旧任务报错或明显停止推进，**只终止新 Job**，不要杀旧训练进程；报告`BLOCKED_CORESIDENCY`或`FAIL_RUNTIME`（按具体故障）。
- 新 Job在iteration1成功写下完整Checkpoint、输出有限Native loss、四个Rank无OOM/NCCL错误，且旧Job保持健康，交付`S1_PASS_CANDIDATE`；不延伸到10/100/30k Step，提交 Evidence 后STOP等待GPT。

## 4. S2 — 后续再做，不属于 S1 自主范围

- GPT审核 S1，并决定是否先完成**同权重同Frozen Batch的Compact0/1 GPU Forward/Loss/Grad parity**；新Job S1成功不是等价证明。
- 仅在相应 Gate通过、Owner明确同意后，才从**新Job**`resume 10`、`resume 100`直至`resume 30000`；有明确更高GPU内存安全余量、CPU/IO、原作业损害监测、Checkpoint保留与可回滚方案。
- 并发情况下的 `step_wall` 只表示与旧NoTTT争抢100% GPU 的共存性能，不是 Compact单独训练吞吐；不能据此直接宣称10s/Step或正式新baseline性能。
- 想把Compact=1应用到**原来的30k Job**，必须另外完成原Job的Resume/数值语义和正式Checkpoint切换Gate；两套Job绝不互相Resume/复用DCP。

## 5. Evidence与执行纪律

- S0未通过：只提交 `BLOCKED_CORESIDENCY` + 每卡内存/进程、RAM/disk、预测余量和旧Job健康摘要；不做GPU加载。
- S1执行：提供真实 Job名、Source SHA、Command、Compact环境与有效Effective配置、每Rank CUDA used/peak 和CPU worker count、最终迭代、Loss有限性、DCP组件完整性、新旧Job的进度对照、Job隔离检查、异常日志。
- 下一次 DS_PRO 交付`docs/collab/chatgpt/evidence/2026-10-28_nott_compact_corerun_s0_s1.{md,json}`（如执行成功可另附日志摘要；真实日志路径不复制敏感信息）；只做新 S0/S1，不重跑旧CPU Evidence、不改生产代码、Git、数据或模型。
- **S0/1 不是GPU Parity结论，也不是完整30k授权。** 不得宣称原独占S0历史 `BLOCKED_RESOURCE` 被追溯否决。新旧Owner授权如冲突，以本请求限定的新共存Job路线为准，仅覆盖此路线。
