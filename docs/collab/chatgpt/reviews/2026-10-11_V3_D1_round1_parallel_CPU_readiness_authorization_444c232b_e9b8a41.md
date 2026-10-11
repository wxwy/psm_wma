# DS_PRO — V3 D1 第一轮：GPU 数值/性能 Gate 的并行 CPU Readiness

**日期:** 2026-10-11
**正式实现:** Root `444c232b976e80ac68cde9e7370e73b9f6410f0e` / Child+Gitlink `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`
**依据:** `docs/collab/chatgpt/reviews/2026-10-11_V3_C1_FINAL_restore_pass_444c232b_e9b8a41.md` （C1_RESTORE_PASS）；`D1_ROUND1_CPU_READINESS_ONLY`。
**目标 D1:** 在 iter800 same-job 状态上，比较 reference OFF/OFF 与 optimized ON/ON 的真实 Policy/Local-TTT Loss、Gradient 和 GPU 资源/效率，明确数值一致性与性能收益的边界，而不是复测 B1/B2/B3/C0/D0/C1。
**正式原作业:** `formal_verified_index_30k` 仍 STOPPED，原 DCP、latest、配置及训练日志禁止改写。

## 本轮只授权 3 项 CPU-only / metadata-only 任务并行执行

### D1-R1-A：真实数值对照契约设计（CPU/static）

- 只读跟踪当前 Child `GroupedLocalMemoryTrainer.training_step`、`GroupedLocalMemoryWindow.run_member`、`ExactWindowSegmentProducer`、`collate_grouped_native_batch`、`move_cached_native_batch`、`model_ddp.training_step` 的真实输入、计损与 FSDP2 Gradient 路径（**不重复源代码全面技术审核**）。
- 固定 **matched pair** 两个输入开关：`PSM_V3_COMPACT_CACHED_VIDEO=0, PSM_V3_SHARED_EPISODE_CACHE=0` vs `=1,=1`。所有其他参数相同：full config digest、真实 Edge/DROID、`raw15`、`left_wrist`、`use_state`、T16/B8/GA2/K4、H_pred16、`cfg_dropout_rate=0.1`、world_size8、`num_workers=0`。除改变测试的环境优化开关外，不改变训练 recipe。
- 两路径从**独立但同源的 iter800 Shadow Checkpoint 状态**开始，要求匹配模型/Optimizer/Scheduler、各 rank RNG、Local fast-state/frontier、相同 GA member/slot/segment/request/valid count；随机变换按各 rank 相同 RNG 流重放。列出哪些身份和数值来自已有 P2/P4，哪些需下一阶段真实 GPU 证明。不得继承测试 A 路径产生的更新状态去跑路径 B。
- 制定实际 `outer/action/vision/inner` Loss、已选中 Generation/Action/Local(特别四个 `w0_fast_*`) 梯度存在性与 shard 对照、数值范围/NaN、相同消费顺序的结果 Schema。确切字段以当前生产模型返回值为准，不能虚构辅助 loss。FSDP2 每 rank local shard ≠ global grad，需要原地按 rank/param 对齐并说明 limit。
- 提前冻结 deterministic 比较策略和容差来源（dtype、数值累积顺序、精度环境）；不要事后因结果不匹配扩大容差。若没有已知确定性能力，既记录 bitwise 是否一致也记录 max_abs/max_rel/ULP（若可），并将不可比情形明确标记而非硬宣称 PASS。
- **关键：** 检查真实 `GroupedLocalMemoryWindow.finish` 会执行 slow Optimizer Step/Local 发布，是否能设计只跑 matched forward+backward 而不调用 `finish`，以及其与真实梯度目标是否等价。若必须真实执行一次 step 才能得到完整参考目标，明确独立的 Shadow-only bounded optimizer-step 方案并保留 `D1_GPU_HOLD`，本轮不可执行。
- 产出冻结 D1 数值比较计划和一份详细列名的预期证据格式，指出最小一个或两个 GA Window 足以覆盖何种 fresh/continuing/remainder 场景，不能把一个窗口结论泛化到长程。

### D1-R1-B：GPU 资源与性能测量安全预算（CPU-only nvidia-smi/日志）

- 仅读取 8×H100 当前可用显存、已有 `robotwin_server` PID/使用量、正式历史 telemetry 和前次 C1 的真实 load-only 背景数据；不得运行 CUDA 模型、torchrun 或 kill 任何进程。
- **C1 仅 Load-only 的设备 total-used peak ≈52–54GiB/卡（包含外部 robotwin_server ≈46GiB），不能当成真实 Policy forward/backward 的峰值。** 明确列出可用显存、模型参数/优化器/梯度/activation/Local scan/prepared raw buffer 和并发外部工作负载的不确定项；不得凭空认定 30GiB free 可跑 D1。
- 给出下一 GPU 试验允许启动的**有证据依据的**显存/并发 guard、实时 monitor 与首次 OOM/资源变化后的 fail-stop，且绝不能因为 robotwin_server util=0 就认定没有冲突。任何资源不足 => `D1_RESOURCE_BLOCKED`，不自动驱逐第三方作业，不改网络/模型/训练规模偷过关。
- 区分单次热/冷缓存 CPU prepare 与 GPU full-step throughput，设计测量 wall、CUDA events、H2D、forward/backward、step/Local scan、per-rank peak allocated/reserved、设备 global used、cache stats；D0 的 CPU 结果不能宣称 GPU 性能收益。
- 允许重用现有历史 GPU 数值/显存日志用于预算，但不得跑新的 8 卡验证。

### D1-R1-C：诊断 Harness/输出隔离与复现安全方案（CPU/static）

- 复用 **C1 已验收的物理独立 Shadow** 与已有 P2/P4 checkpoint/RNG/fast-state身份，不创建新的训练 job 到原 Formal30k。若对照需要两个独立诊断输出，提交实际 Path/JobName/realpath/inode 隔离设计及所需磁盘空间，**此轮仅设计，不复制大型 shard，也不启动模型**。
- 明确各模式的进程全局 flags 必须在 Dataset Factory 实例化**之前**设置。计划逐 rank capture input identity/seed/RNG load-state and any CFG dropout, Model/Optimizer parameter state, Local frontier, next GA window; compare before/after每条路径，防止跨模式状态污染。
- 利用 `GroupedLocalMemoryTrainer.__init__` 会向 `JobConfig.path_local` 写配置、Checkpointer same-job priority 依赖 `save_dirname/latest_checkpoint.txt`、`restore_grouped_local_state` 的机制设计无污染恢复。不许同一个可写目录与原 Job 共用 symlink/hardlink；不能把更改 `load_path` 当成 same-job。
- 对任何实验中途中止设定**一次性 fail-stop**：保存首异常/每 rank logs 和监视器证据、退出。**本 Gate 不允许**像 C1 那样先跑四次再补充记录；诊断 Harness 语法/依赖问题应事先在 CPU static gate 消除，若下一实际 GPU 运行出错，等待 GPT 重新明确授权后再执行。
- 明确此前 C1 8-rank successful load-only **不包含 forward/backward/optimizer**；后续 D1 仍需自己的 GPU 授权。

## 通用约束 / 并行调度

- A/B/C 可并行，独立 /tmp Evidence 目录，复用原有 trusted metadata 和日志；不要求彼此完成再启动另一项，最后统一交付。
- 不修改 Production/Test/Launcher 代码，不安装/降级库；不重建 dataset/verified index/VAE，不重做 Batch1/C1，不增加新的 8×H100 Load/Test。
- **本轮不得** CUDA model init、`torchrun`、实际 `checkpointer.load()`、forward/backward、Optimizer/Scheduler Step、DCP Save、Fresh/Resume、Policy Simulator、18-task Screening；原 Formal30k 继续 STOPPED。
- B 和 C 为 CPU/文件轻量操作；不要同时进行大量磁盘 I/O 或额外拷贝超过 24GB 的 Shadow。

## 一次性 DS 交付

文件：`DS_PRO_V3_D1_ROUND1_PARALLEL_CPU_READINESS_2026-10-11.md`。

分别报告 `D1_R1_A_PASS/FAIL/BLOCKED`、`D1_R1_B_PASS/FAIL/BLOCKED`、`D1_R1_C_PASS/FAIL/BLOCKED`，包含：
- Pinned Formal Pair / 根-Child-Gitlink 状态与 freeze 训练参数；
- Match-up 数值对照契约与是否需要 slow optimizer step 的明确判断；
- GPU resource headroom / known historical peak / quantified unknowns；
- 两模式独立 Shadow 及运行记录计划，首异常持久化机制；
- 精确 Evidence 路径与本轮 skipped GPU 行为；
- 下一 GPU 真正可以启动的前提及任何资源/技术 blocker。

DS 不提交 GitHub。A/B/C 全部执行完即停止，并通过 owner 将报告交 GPT。下一轮 GPU 数值验证是否允许、允许哪些 step，由 GPT 根据本报告单独冻结并授权；**不得自动启动**。