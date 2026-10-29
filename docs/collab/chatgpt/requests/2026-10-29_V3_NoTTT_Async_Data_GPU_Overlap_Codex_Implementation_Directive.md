# CODEX 实现任务 — V3 No-TTT nw>0 真异步数据准备与 GPU 计算重叠

- 日期：2026-10-29；Owner 指令；任务入口 **[Issue #9](https://github.com/wxwy/psm_wma/issues/9)**。
- **性质：隔离候选实现 + 作者 CPU/静态 Evidence 授权；不是生产 Code Gate、不是 DS/GPU/正式训练授权。**
- 关联旧任务：[Issue #4](https://github.com/wxwy/psm_wma/issues/4)（已实现 spawn worker，但**没有覆盖本轮全流程 overlap 的验收目标**）；不要重复既有独立 CPU Parity、Dense/Compact GPU strict parity 或10步 Fresh。
- 目标正式 Job：`no_ttt_packed128_droid_fresh_30k_world4_ga4`（Owner 2026-10-29 报告 iter7600+ 且正在训练）。最终只考虑该 Job 在合法完整 checkpoint 边界同 namespace Resume，**当前不可停止、改动、覆盖、拉取运行工作树或并发 Resume**。
- 上次审阅的 V3 Child Gitlink `746c5cf2f2324104a62fb71510343aa40d3976c5`；相关源文件 Child `matched_no_ttt.py` blob `3e56f65d860f3c761cfe2dd02e78d6369ac5e1a2`、`no_ttt_cpu_loader.py` blob `2d608415e5f669d9005fc0ad903f0e9e799588c9`。Codex 开始前重新锁定最新 `origin/V3`/Child Gitlink，**本指令对应的 request/doc SHA 不是 Formal implementation SHA**。
- 当前任务认领标识：`V3-NOTTT-ASYNC-OVERLAP-NWPOS-20261029`，Codex 应在独立候选工作树的 TODO/SESSION 中登记认领、计划文件、原始代码身份与实施阶段。

## 1. 不再混淆的行为需求

用户最终冻结：

1. `NOTTT_LOADER_WORKERS=0`：沿用当前原生 **同步、串行** 数据准备路径，确保现存训练/Checkpoint 兼容、Consumer/Transform/RNG 语义不变。
2. `NOTTT_LOADER_WORKERS>0`：必须真正利用 CPU 后台工作与当前 GPU forward/backward **重叠**，使下一 GA Member、并在安全前提下下一 GA Window 的 Source/Cache/Transform 等准备在 GPU 工作时提前进行。目标是消除 GPU 等待数据的同步关键路径，**不是只增加 PID 数量或缩短单个 CPU Transform 时间**。父进程允许保留必须串行的短暂消费、collate、H2D、事务检查，但不能仍把主要 Source Snapshot 和整段 `ActionTransformPipeline` 同步压在 GPU 前后而声称并行优化完成。
3. `PSM_V3_COMPACT_CACHED_VIDEO=1` 是另一个独立优化：避免零 RGB Dense 视频冗余 Transform，不能把 Compact 带来的20.32s/Step 直接记作 `nw>0` 的 GPU/CPU overlap 收益。优先目标验证为 **Compact1 + nw8**；保留 nw1/2/4/8 合法值，**默认 nw0 不变**。nw8 非强制最优，也不根据单步经验预先写性能结论。
4. 现正式 Job 的 worker-count 是运行时设置，不进入 training identity/digest/Frontier；No-TTT `world4/FSDP2/B8/T16/GA4`、Global2048 Consumer/step、Generation-only optimizer、No Local、`max_iter30000/warmup500/save_iter100`、旧 Job name/namespace 都不能变更。

## 2. 当前源码级问题（在新候选中修复，非凭空抽象设计）

- `cosmos_framework/trainer/matched_no_ttt.py:265–269`：`grad_accum_iter==0` 才 `window.begin()` 并 `_no_ttt_loader.begin(window.plan)`。因此开始每个当前 GA Window 前，需要先做一次同步准备。
- `cosmos_framework/trainer/no_ttt_cpu_loader.py:401–436`：`_begin` 在 Trainer 主进程对该 Window **所有 Member/Request** 同步执行 `producer.prepare(... source_reader.read_at)` 并 pickle Source Snapshot；执行完才创建 DataLoader iterator。这项 Source Read 不是 Worker 并发预取。
- `no_ttt_cpu_loader.py:445–497`：`materialize` 等 RAW Worker 结果后，Trainer 主进程再做 `producer.prepare(...)` 和 `producer.materialize`，`wrapped._transform` 仍同步在主进程。
- `matched_no_ttt.py:269–325`：每 Member 主进程 materialize/collate/H2D 后才开始 native forward/backward；`:341–357` 完成 optimizer 后才 `window.finish()` / Loader finish。当前仅可部分重叠 GA 内 RAW Worker IO，没有真实跨 Window 数据双缓冲的见证。
- 旧 DS 性能报告 `docs/collab/chatgpt/reviews/2026-10-27_V3_G1_NoTTT_CPU_Performance_Evidence_Review.md`：旧正式 Job 在不同阶段的 nw0/nw8 稳态 Step Wall median33.1/32.2s，RAW source_read≈4.78s、Parent Transform≈16.72s；改用 Compact1 后 nw0 Fresh10 mean20.32s（**不是 nw8 测量**）。

Codex 第一件事：审计并提交简明 **Stage/Owner/RNG/Frontier 时间线和修改计划**。确认哪些调用可以在 CPU worker/process 中完成，哪些状态必须保留 Trainer 主进程；不要依据 `DataLoader(num_workers>0)` 的存在就宣布完成目标。

## 3. 最小实施约束和方案边界

- 可以在 Child 候选中集中修改 `cosmos_framework/trainer/no_ttt_cpu_loader.py`、`cosmos_framework/trainer/matched_no_ttt.py`、必要的 `no_ttt_loader_profile.py` 与相邻测试；如需改变 source/cache adapter 或 Root launcher，必须在 TODO/SESSION 明确文件与原因并保留 workers0 老路，**不得顺手改 G1/Local-TTT、Cosmos 通用 Trainer/optimizer 或数据集采样**。
- 采用**有界 CPU 后台生产者 + 两级/跨 Window 预取**，或等价可执行架构。提交明确的持有关系：哪个进程/线程负责 plan preview、Source Read、Cache、Transform、Packed Batch、消费、取消和清理。必须证明实际出现在 GPU-forward/backward 期间的 CPU 工作，而不只是把 `begin` 名称改成 `async_begin`。设计需支持最多8 worker/rank、每一 rank有界 in-flight/字节/缓存/CPU+RAM 占用，不能让每 worker 拿整份模型或无界 Episode 张量。
- 为跨 Step 预取，允许从**当前冻结 Window 的 candidate frontier 只读预览**下一 Window 的请求；这只是 speculative planning，**不能提前把该 frontier 设为 live/committed**。严格区分 active/prepared/speculative 状态：optimizer 成功且全部 GA 成员 backward 后才 commit。GPU/Optimizer/Checkpoint/Rank Frontier owner 始终为主进程。
- 重叠方案不得无证明地改变 caption/CFG dropout、Python/NumPy/Torch RNG、Transform 实际调用序列或最终 Batch；如果需要把随机 Transform 移到 Worker，必须设计显式 RNG 隔离、按消费顺序发布、主流状态恢复/前进并给出 bitwise/value + RNG consumption Evidence。**不能偷偷改成 per-sample seed 或重设 RNG 训练语义**；若无法保持历史效果，STOP 给出设计冲突，而不是把近似当 exact pass。
- Checkpoint DCP `model/optim/scheduler/trainer` + rank0..3 dataloader/frontier 原始 schema/identity 严格保留。正在预取的候选 Window/Random State 不应被当作已提交样本；checkpoint 边界须能 drain/隔离 speculative work 而不阻断合法保存。失败/timeout/NaN/Skipped optimizer、取消或进程崩溃：丢弃未提交包、不修改正式 Frontier 或 RNG 进度，恢复后下一 Consumer 必须与不中断路径一致。
- Worker 本身禁止 CUDA、模型、optimizer、frontier 变更、torchrun rank 环境继承、外部网络访问；失败时 bounded stop/reap，所有异常保留源因，不允许悬挂僵尸 worker 或回退到静默同步路径冒充性能 PASS。
- 原正式 Job 的 Source/Cache/Index/DROID 基线不重建、不改文件，不改 `v3_job_identity.json`，不触碰原 Job 任何 checkpoint/monitor。新测试全部在隔离候选、小型合成或此前已授权的只读 CPU fixture 上运行；**本阶段不运行真实数据/真实模型/GPU/训练**。不得覆盖其它 EvalV2 正在开发的分支或历史 review。

## 4. 冻结 CPU 测试 / 可审计输出

单次集中交付，而不是反复送几份旧数据：

1. **行为与数值**：nw0 vs nw1/2/4/8 全部 CPU 快照/数据对照；覆盖4 Rank/GA4、full、terminal partial、slot/episode/cursor、request/consumer index、action/state/text/video_latent/mask/sequence_plan、Packed Native Batch、RNG before/after/consumed，冻结 token/配置、Generation-only 与新旧同 Job Frontier 合同。现成已 CLOSED 的 Compact CPU Gate 只复用，不重新测试无关部分。
2. **关键重叠时间线**：用可控的合成慢 Source Read + 慢 Transform + 假 GPU compute callback（仅 CPU fake）运行至少连续三个 optimizer Window；记录 `cpu_source_start/end`、`cpu_transform_start/end`、`fake_gpu_compute_start/end`、`consumer_ready`、`main_thread_wait`、`committed_iter` 的同一 monotonic-clock 时刻。断言 nw0 依序串行，nw>0 **下一 Member 且下一 Window 的真实 Source/Transform work** 至少在当前 compute interval 内有非零交叠；提前准备没有提前 commit。不得用只启动 worker、`sleep` 主进程或 RAW-only overlap 代替。报告 overlap_ms、main_wait_ms、end-to-end wall，保留完整 trace JSON。
3. **异常/恢复**：worker crash/timeout/延迟完成/乱序/重复/错误 identity/Cache 改变/撤销时 speculative frontier/共享 RNG 不污染，进程有界回收；同 job nw0↔nw8、8→8 CPU checkpoint Resume 与不断训 next consumer/value/optimizer scheduler/trainer/RNG/frontier parity；保留非法参数/schema/source/Rank/GA 的 fail-closed。
4. **静态与版本**：run scoped pytest/JUnit、Ruff0.12.7、format、py_compile/AST、bash -n（若修改launcher）、Root/Child diff/hash + actual worker PID/IPC 内存上限。保留失败前版本的负例和最终 GREEN，禁止为了通过删减已有断言；清楚标注 mock/fake GPU，**不得冒称真实GPU性能或DCP Resume通过**。

实际 4xGPU 性能 Gate（后续 DS、Owner 单独授权）须对**同模型/同起点/相同数据**的 Compact1 `nw0` 与目标 `nw8`，记录 CUDA forward/backward 时间、CPU准备 interval、data wait/gpu idle interval、Step Wall/P50/P90、RAM/显存/worker error，并验证目标配置不会恶化吞吐；**仅有 CPU 测试不能提前关闭该 Gate**。若等价成立但真实系统没有 measured overlap 或吞吐提升，优化目标仍不能判 PASS。

## 5. 交付/停止条件

- 开发在隔离 Root+Child candidate branch/worktree，不直接 merge V3/Child v3-local-ttt，不修改/停止/Resume 当前正式 Job，不碰 GPU0–7 实验、真实 DCP 或现场设备、磁盘 cleaner，也不运行正式 No-TTT 30k/100/10。
- 交付源码变更前后功能清单、Plan/Owner/RNG 方案、精确 Formal Root/Child/Gitlink SHA、真实 Github Git Blob 绑定、作者 CPU Test 原始 JUnit+timelines/negative cases、完整 diff、剩余风险。新正式 Code Gate 由 GPT 对新 pair 独立增量审核，合格后另行 DS_PRO **独立 CPU**，之后 Owner 单独授权 **隔离真实DCP/GPU Canary**、最后才决定正式 Job 合法 Checkpoint 边界切换。
- 如遇旧 RNG / 跨 Window checkpoint / cpu worker import 机制无法同时满足本合同，**给出可复现的设计 BLOCKER 和最小选择，不要静默缩小为 RAW-only overlap**。仅设计冲突可先停于 Design Gate；否则完成上述候选实现和 CPU Evidence 再交。
- Codex 请在 [Issue #9](https://github.com/wxwy/psm_wma/issues/9) 回复 **ACK + exact baseline + 拟改文件**，随后按此合同编码；**GitHub issue 发布不证明 Codex 会话自动启动**。
