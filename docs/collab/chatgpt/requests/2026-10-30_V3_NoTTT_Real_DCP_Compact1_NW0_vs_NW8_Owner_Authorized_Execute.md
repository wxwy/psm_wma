# OWNER AUTHORIZATION — No-TTT 真实 DCP Resume + Compact1 / nw0-vs-nw8 4GPU 资格实验

- Owner授权时间：2026-10-30。授权来自 Owner 在 Issue#11 六份 raw CPU Gate 全PASS之后，对下一步“真实DCP Resume + 真实GPU性能”明确回复 **「我授权」**。
- **执行人 DS_PRO（独立执行/证据，不改任何生产源码）**；GPT 只负责冻结方案、审核证据。
- **状态：`AUTHORIZED_CONDITIONAL_RESOURCE`。不需再问是否授权这一次限定的 A/B，但每条安全/资源前置条件必须先现场满足；当前活跃正式Job绝不因此暂停。**
- GPU 资格源：Frozen Root `e0fe911dfb9fd34957234828195cf051713f6c3d` / Child+Gitlink `f6a92d47b6dac7998ddc58b3da26ef93f8068dc7`；此前 Code Gate `APPROVE_CODE` + Issue#11 DS独立301CPU、原始Evidence6/6 `PASS`。**不要使用不同 Formal Pair，也不要直接用已推进的 V3/新Child。**
- 原正式Job：`no_ttt_packed128_droid_fresh_30k_world4_ga4`（DS末次实时见证 old RAW Loader，`NOTTT_LOADER_WORKERS=8`，world4/GA4/B8/T16）。同名正式Job的活动训练仍属于另一个进程/输出目录。**绝不停止/kill/relaunch/merge/修改它或清理Checkpoint**。

## 0. 精确目标与完成定义

只测两件事：

1. **真实恢复能力**：旧正式Job `complete` DCP的 `model/optim/scheduler/trainer`、rank0..3 Frontier sidecars + CPU/CUDA RNG，由新候选精确Pair从**同一个迭代C**恢复并正常提交 C+1、持续20个optimizer迭代；4rank均不发生错序、数据错配、训练错误；没有模型-only Fresh 回退。
2. **真实GPU吞吐**：同一个C、同源同模型/超参，`PSM_V3_COMPACT_CACHED_VIDEO=1`：
   - A：`NOTTT_LOADER_WORKERS=0`，旧同步 `producer.produce` 数据路径；
   - B：`NOTTT_LOADER_WORKERS=8, NOTTT_PREFETCH_FACTOR=1, NOTTT_PERSISTENT_WORKERS=1, NOTTT_LOADER_TIMEOUT_S=120`，新 `NoTTTAsyncLoader` 的 worker Source+Cache+Transform/跨Window预取。
   **A、B 各20个 optimizer迭代，顺序串行，不交叠，GPU4–7固定。** 训练合同固定 `max_iter=30000, warmup=500, save_iter=100, world4/B8/T16/GA4, Generation-only, raw15/state15/left_wrist`。`formal-execution-until=C+20` 是绝对optimizer迭代终点，不是新跑30000步。

不测无关配置，不新起Fresh10或30k，不改 Local-TTT、EvalV2、数据集/模型/optimizer、G1/训练主线。不得把旧 Job 的 `nw8`（旧RAW）记成这里B的`nw8`（新Async）。

## 1. DS 现在就可执行的只读 S0 Preflight（不需空闲GPU）

- 只读检查原正式Job的当前 PID/启动命令/当前 source checkout 与真实 `NOTTT_LOADER_WORKERS`/Compact、latest committed optimizer iter、真正 `complete.v1.json`；读 `checkpoints/latest_checkpoint.txt` 后，验证目标 `iter_%09d` 的 DCP `model/optim/scheduler/trainer/.metadata`、4个 `dataloader/rank_{0..3}.pkl`、原 `v3_job_identity.json`、`config.pkl/yaml`、`launch.lock`，若complete标志位位置与原来不同需给出确切路径。不得仅读目录名猜完整DCP。
- 选一个**已写完且不会被Owner/现有Cleaner并发删除**的合法C，需 `C+20 <= 30000`。只读检查DCP与源数据/缓存/索引/正式DROID Edge VAE本地路径可访问、输入SHA/冻结语义；收集 checkpoint完整性与必要文件存在、C对应rank sidecar，原 DCP不可移动/删除/修改。
- 只读检查 GPU4–7的真实占用/对应PID及显存、其他任务；CPU Host可用RAM、交换空间、独立checkpoint双份克隆需用的磁盘空间与配额。**若正式Job仍存活、任一GPU4–7被占、无法安全备份C/Host内存不足或清理竞争**：只报告 `BLOCKED_RESOURCE_OR_CHECKPOINT` 及事实，立即STOP在此，不继续克隆/启动GPU、不安排自动停训。不得拿 GPU0–3 替代。
- DS可先给 GPT/Owner 一份 `S0_READONLY_REPORT`：C、所有绝对数据路径的安全摘要（无secret）、正式/候选Root+Child身份、原Job活跃状态、GPU4–7资源、独立磁盘可用量、是否具备两臂资格。当前阶段可以运行只读shell，不运行torchrun/CUDA模型/真实训练。

## 2. 条件全部绿之后，原 DCP 的隔离完整克隆

- Owner此授权仅当**原Job进程不在运行且GPU4–7确实空闲可独占**时允许进入 GPU 阶段；这个前提是安全约束，不允许DS去停止原Job创造空闲。检测非0残留/暂时GPU空闲但job PID活跃不算空闲。
- 在独立磁盘/路径创建 **`OUTPUT_ROOT_A`、`OUTPUT_ROOT_B` 两套互不相交目录**，都不能位于正式 Job namespace 内；Frozen Root+Child在独立干净 detached worktree。复制同一旧正式Job完整 `iter_C` DCP和所需不可变metadata、4 rank sidecars、`checkpoints/latest_checkpoint.txt`、原Job `config.pkl/yaml`、`v3_job_identity.json`、`launch.lock`；复制后验证完整、hash/size与源相符，不采用硬链接/指向正式目录的符号链接、不共享可变文件。只复制这一个合法 checkpoint，不需要历史全目录。
- **克隆 job_name 必须仍为 `no_ttt_packed128_droid_fresh_30k_world4_ga4`**，但 `OUTPUT_ROOT_A != OUTPUT_ROOT_B != 原OUTPUT_ROOT`；原代码的历史同名 NoTTT4 Resume兼容口需要这样恢复，不能改名伪造另一个新 Job 或重写 identity/digest。若实际当前冻结签名对此不兼容，直接BLOCKED，不能删断言/改源绕过。
- 验证两个克隆的C元数据/Frontier/冻结source完全一致，旧正式目录和 `latest_checkpoint.txt` 不发生变化。clone路径的上级不能是symlink。保留 `CLONE_MANIFEST.json`：C、源/两个目标绝对路径、检查项、hash/size、冻结代码SHA、复制策略、无共享可变inode证据。
- 不覆盖原Job的日志/monitor或Checkpoint，不触碰Cleaner/retention。若Checkpoint克隆完整性FAIL或启动时需修改production身份/断言，直接STOP。

## 3. 冻结的GPU运行入口（只允许两条，按顺序）

在独立干净、exact Root/Child/Gitlink的 `ROOT_CANDIDATE` 启动，不使用V3当前HEAD，**禁止在正式训练工作树执行`git reset/pull/checkout/merge`**。DS应先填入S0实际确认的路径并保存 `RUN_MANIFEST.json`（精确环境、命令、C、输出、风险检查）；这里只列冻结的通用可执行模板，未确认的路径绝不能猜。

公共变量：
```bash
JOB_NAME=no_ttt_packed128_droid_fresh_30k_world4_ga4
STOP_ITER=$((C + 20))
# ROOT_CANDIDATE, OUTPUT_ROOT_A, OUTPUT_ROOT_B, SOURCE_ROOT, CACHE_ROOT,
# DATASET_INDEX_ROOT, EDGE_POLICY_CHECKPOINT, WAN_VAE_PATH, BASE_CHECKPOINT_PATH,
# PYTHON: 均由DS只读S0确定，ROOT_CANDIDATE应为隔离精确Formal Pair。
# 两臂使用同一 PYTHON/数据路径/实体DCP C。GPU必须为独占4,5,6,7。
```

**Arm A（先执行，nw0，Compact1）：**
```bash
env -u NOTTT_PREFETCH_FACTOR -u NOTTT_PERSISTENT_WORKERS -u NOTTT_LOADER_TIMEOUT_S \
  CUDA_VISIBLE_DEVICES=4,5,6,7 PSM_V3_COMPACT_CACHED_VIDEO=1 \
  NOTTT_LOADER_WORKERS=0 JOB_NAME="$JOB_NAME" OUTPUT_ROOT="$OUTPUT_ROOT_A" \
  SOURCE_ROOT="$SOURCE_ROOT" CACHE_ROOT="$CACHE_ROOT" DATASET_INDEX_ROOT="$DATASET_INDEX_ROOT" \
  EDGE_POLICY_CHECKPOINT="$EDGE_POLICY_CHECKPOINT" WAN_VAE_PATH="$WAN_VAE_PATH" \
  BASE_CHECKPOINT_PATH="$BASE_CHECKPOINT_PATH" PYTHON="$PYTHON" \
  bash "$ROOT_CANDIDATE/scripts/train_v3_matched_no_ttt_4gpu.sh" resume "$STOP_ITER"
```

**Arm B（仅A健康完成后执行，nw8新Async，Compact1）：**
```bash
env CUDA_VISIBLE_DEVICES=4,5,6,7 PSM_V3_COMPACT_CACHED_VIDEO=1 \
  NOTTT_LOADER_WORKERS=8 NOTTT_PREFETCH_FACTOR=1 NOTTT_PERSISTENT_WORKERS=1 \
  NOTTT_LOADER_TIMEOUT_S=120 JOB_NAME="$JOB_NAME" OUTPUT_ROOT="$OUTPUT_ROOT_B" \
  SOURCE_ROOT="$SOURCE_ROOT" CACHE_ROOT="$CACHE_ROOT" DATASET_INDEX_ROOT="$DATASET_INDEX_ROOT" \
  EDGE_POLICY_CHECKPOINT="$EDGE_POLICY_CHECKPOINT" WAN_VAE_PATH="$WAN_VAE_PATH" \
  BASE_CHECKPOINT_PATH="$BASE_CHECKPOINT_PATH" PYTHON="$PYTHON" \
  bash "$ROOT_CANDIDATE/scripts/train_v3_matched_no_ttt_4gpu.sh" resume "$STOP_ITER"
```

日志/CPU Worker进程必须只写各自隔离 `OUTPUT_ROOT_X`，每条运行保存stdout/stderr/exit code、Rank0–3原始日志、`monitor/train_rank0.jsonl`、`[NoTTT][cpu_loader]` telemetry、旧DCP第一步恢复记录、外部 host RAM/GPU只读采样及实际producer/loader身份。A/B不得同时运行。**两个真实模型运行（各20步）就是此次唯一授权GPU成本；不能自动扩大到100、30k或添加其他配置。**

## 4. PASS/FAIL / 停止条件

- Resume必须从同一C恢复，下一次optimizer commit必须是 C+1；20个严格连续成功optimizer commits，`trainer._grouped_completed_iteration=C+20`，对照4rank Frontier/slot next_segment_id与saved state正确衔接；原DCP model/optim/scheduler/trainer/RNG完整加载。若任一missing rank sidecar、DCP metadata mismatch、data/CFG/RNG不相容、NaN/Inf、OOM、worker Timeout、进程遗留、GPU串占、来源/输出污染、Trainer意外Fresh/restart，立即STOP并保存Evidence，B失败不得静默回退nw0续训。
- 记录A/B各自前2–4步**冷启动**，以余下至少16步作为**稳态候选样本**；报告 Step Wall P50/P90、valid consumer/s、CPU数据准备、collate/H2D、Forward+Backward/Optimizer stage、`gpu_data_stall_ms`及`gpu_data_stall_status`、NoTTT worker wait/source/transform、CUDA timing字段有实际记录才使用。原Telemetry的 GPU-data-stall是 **current CUDA stream gap estimate，不是整个GPU idle**；sample若 pending 则记 `NOT_MEASURED`，不伪造0。报告所有4rank退出与CPU RAM/Worker RSS/mmap预算、GPU显存/别的任务干扰、进程cleanup。
- `APPROVE_PERFORMANCE` 不能仅以后台CPU overlap为证据；需 **B在匹配DCP、相同GPU/数据前提下稳态 Step Wall明显改善或数据等待显著下降且没有其它显著退化**。若B更慢/异常则实测性能 `FAIL/INCONCLUSIVE`；不得预设加速比，不得用旧不同阶段nw8/Compact0历史直接作A/B证据。
- 既有 Compact严格GPU Gradient parity冻结阈值旧FAIL、Dense重复性失败与归因INCONCLUSIVE继续存在；本新实验**不把旧失败改写为PASS，不引入无依据bitwise gradient固定阈值**。比较至少同step consumer指纹、loss/optimizer健康、native Forward/Backward次数、状态变量和RNG一致性见证，不得把未测项目写PASS。
- 任意阶段FAIL保留原始日志，禁止自动重试、自动切换正式Job、切分额外配置、清理证据或上传敏感Checkpoint。DS只提交脱敏指标/过程/原始日志索引与trace到隔离 Evidence，停止等待GPT独立 Gate Review。

## 5. 明确不授权的操作

**没有正式Job停训/重启/并发Resume/正式30k/Checkpoint或metadata写权限；没有V3/Child生产合并、旧Job迁移/数据清理、GPU0–3/仿真任务、额外实验授权。** 即使两臂全绿，也只能作为受控实验Evidence交由GPT审核；未来要不要在原正式Job上切换代码，Owner需再单独授权。

**本授权是 `TEST_ONLY_NATIVE_GPU_DCP`，不是 `DEPLOY_OR_PROMOTE`。**
