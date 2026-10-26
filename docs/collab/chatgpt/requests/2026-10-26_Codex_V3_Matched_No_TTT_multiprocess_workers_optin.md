# CODEX IMPLEMENTATION REQUEST — V3 Matched No-TTT 多进程 DataLoader Workers（Owner 2026-10-26）

## 0. 任务状态、权限和精确基准

**Owner 直接需求：让 Codex 适配 Matched No-TTT，使其具备真正的多 Worker 数据加载能力。**

**本文件是 Codex 实现任务，不是 GPT Code Gate，不代表任何正式验收；不得自行启动正式训练。**

- Base branch: `wxwy/psm_wma:V3`; 基准 **Root `e6ae2084305a8c24d763d82b517984660cc73c30` / Child Gitlink `923d9c3fd392e6bafbdb1771a292c7b313e6b3dc`**。
- Child repository: `wxwy/cosmos-framework`, corresponding V3 branch; Codex 必须在**独立 candidate branches/worktrees** 实现，并最终提交新的精确 Child SHA、Root SHA 和匹配 Gitlink；不要把实现直接合进 V3。
- Existing formal 4GPU No-TTT job: `no_ttt_packed128_droid_fresh_30k_world4_ga4`; `CUDA_VISIBLE_DEVICES=4,5,6,7`; `B=8,T=16,GA=4,world=4`; nominal global 2048 consumers/optimizer update。其原有 Fresh、Resume、DCP、日志及所有 G1 产物均视为不可变。
- **本轮授权仅限设计核对、代码实现、合成 CPU 测试和作者 Evidence/交接。** 不启动 H100/GPU、真实 Model/DCP/Source/Cache IO、训练、RoboCasa 仿真、server 或正式性能对比；DS/Owner 后续另行放行。
- Codex 可参考 NVIDIA 官方 `cosmos_framework/data/generator/joint_dataloader.py` 的 `RankPartitionedDataLoader`、`PackingDataLoader` 和 `action_sft_dataset.py`。但它们的采样与 resume **不能被直接假定与本项目 Exact-Window/Packed128 等价**。

## 1. 需要解决的精确问题

NVIDIA 官方 RoboCasa/DROID Action SFT 使用 PyTorch `DataLoader(num_workers>0, prefetch_factor, persistent_workers)`。当前 No-TTT 虽复用原生 Cosmos 模型、Generation optimizer/outer loss，却在 `examples/psm_wma_robocasa_corrected_phase5.py:main` 用 `GroupedTriggerLoader` 发送空触发，真实数据在 `MatchedNoTTTTrainer.training_step` 内用 `ExactWindowSegmentProducer.produce` **同步获取**。目前：

- `cosmos_framework/trainer/matched_no_ttt.py:198-200` 明确拒绝 `num_workers>0`；
- Phase5 `preflight` 的 No-TTT profile 限制 `args.num_workers==0`；
- `scripts/train_v3_matched_no_ttt_4gpu.sh` 固定传入 `--num-workers 0`。
- G1 的 `AsyncExactWindowRawPrefetcher` 是 **ThreadPoolExecutor**，不是官方 PyTorch 多进程 DataLoader；G1 已观察 workers4/8/16 较 workers0 **Step Wall 约10s→20+s，Data Time 约5s基本不变**。不能直接把该线程池当作完成本任务，也不能假定增加 worker 就更快。

目标：**为 No-TTT 新增可选的真正 CPU 多进程数据加载 / 预取路径**，复用官方 PyTorch DataLoader/Worker 基础设施的安全机制（优先）或明确说明必要的 process-worker adapter；`workers=0` 不变。架构应保持模型/梯度/optimizer与 Exact-Window/Packed128 语义完全一致。不得将“切回官方普通采样+PackingDataLoader”冒充 Matched No-TTT。

## 2. 必须冻结的数据与训练语义

1. 仍使用已验收 RoboCasa Target-Atomic `VerifiedExactWindowIndex` + cached latent，官方 DROID DCP **model-only Fresh 初始化**，raw15/state15、left_wrist、20fps、Action chunk16 / observation frames17。
2. `ExactWindowRankPlanner` 仍是唯一的 rank/slot/episode/GA member 消费顺序 authority；固定 rank shard、slot-major packing，`B8 × T16 = 128` valid upper bound/member；4 ranks × 4 GA × 128 nominal = 2048；terminal partial 时仍按真实 `n_member/n_window` 权重。
3. Native Cosmos `model_ddp.training_step(batch, iteration)` 与其 vision/action/auxiliary outer loss、7个 Generation optimizer selectors、Action LR×5、scheduler 30k/warmup500/save100 全保持。禁止引入 Local-TTT module、prefix、inner loss、fast weight/scan。
4. 原始 `num_workers=0` 的 **样本/Transform/RNG 时序、Batch bytes（必要时按 tensor 值等价）、训练调用路径、已有 Job 的 Fresh/Resume/DCP 行为和身份**不变。可新增隔离的 opt-in worker profile，但不能改变当前正式 Job 默认值，禁止自动迁移旧 Job。
5. Worker 只能持有不可变请求、CPU source/cache reader/必要的原始数据准备工作；不得访问 CUDA、模型、optimizer、planner/live frontier 或更新 Checkpoint。所有 GA member 必须有确定性顺序返回；若 worker 端执行 Transform，必须证明与 legacy global Python/Torch/NumPy RNG、CFG dropout 等全部等价，否则将 Transform 留在 trainer 主线程。
6. 每个 optimizer 成功提交边界才推进 `Frontier` 和保存 DCP。Worker 正在预取、超时、异常、取消、Rank失败或 kill/restart 不得导致跳样/重复、幽灵 pending、partial frontier 被提交、改变原始模型/optimizer/RNG state。4GPU same-job Resume 必须严格恢复 model/optim/scheduler/trainer/RNG/rank0..3 frontier；跨 worker-count Resume 默认禁止或需严格经 Evidence 证明没有语义漂移后经单独设计授权。
7. **不得恢复之前取消的 4GPU No-TTT Root 状态/Root HEAD/Child HEAD/Gitlink admission 检查。** Owner 仅对此 `no_ttt_*_world4_ga4` profile 豁免 Git SHA/Root dirty blocker，现有身份记录为 `nottt_world4_ga4_source_head_not_verified`；G1 和原 world8 No-TTT 维持既有校验。训练代码应继续使用主仓 `psm_wma_v3/cosmos-framework`，不依赖 `data1/dspro_*` 临时工作树。

## 3. 推荐技术实现顺序（由 Codex 根据源码决定具体 adapter）

A. 先对照官方 `RankPartitionedDataLoader` / `PackingDataLoader` / `ActionSFTDataset` 与现有 `MatchedNoTTTTrainer` / `ExactWindowSegmentProducer` / `NoTTTFrontierCallback`。必须书面给出为什么**官方 DataLoader 可或不可直接承接动态 GA window request**，不得凭“继承 ImaginaireTrainer”认为自动生效。

B. 首选使 **真实 PyTorch CPU Worker 子进程**加载冻结的 Raw Segment/Window 请求（实现需明确 worker PID、对象持有与生命周期，`persistent_workers`、`prefetch_factor`、`pin_memory` 行为）；若标准 DataLoader 无法安全对接窗口级请求，可做**有界 CPU process-worker queue**，但需明确是 process-worker adapter 而不是官方 DataLoader，并保留稳定 `PreparedExactWindowSegment` + trainer-thread `materialize` 的决定性次序。**不要只移植 G1 的 `ThreadPoolExecutor` 并改名多进程 Worker。**

C. CLI 清晰区分官方式 CPU data-loader worker 与 G1 的 raw-prefetch thread：建议新 No-TTT-only `--no-ttt-loader-workers` + `--no-ttt-prefetch-factor`（0/1/2/4 起步），4GPU Launcher 暴露 `NOTTT_LOADER_WORKERS` 等 env，默认0；或给出等价且向后兼容的方案。所有非 No-TTT、world8 No-TTT 默认行为不变。旧原 `--num-workers` 语义不得在 G1 静默改变。workers=0 时禁用 persistent_workers/prefetch_factor 并精确维持旧行为。

D. Worker 下 source_reader/LeRobot HF/Arrow/cache 对象必须多进程安全。限制每 worker 的 Episode 缓存、共享内存和 in-flight 个数；避免 4GPU×4worker 多倍复制高达数GB Episode payload、worker 内多线程爆炸或同时对相同 `.pt` 重复反序列化。异常必须 bounded drain/cancel/close，不留子进程或隐性 DataLoader stale batch。

E. 把 Worker 配置纳入新 opt-in 身份/审计（与 Zero Worker 正式 Job 分隔）；原 No-TTT `MatchedNoTTTTrainer` 严格 Resume contract 继续适用，不得仅删 guard 而未接线。记录真实 worker count、PIDs、read wait、prepare、transform、collate 和 step wall 耗时；未定义的计时值不得冒充 GPU 数据等待。

## 4. 必需的可执行 Acceptance & Evidence

- **Baseline parity**：单 Rank/4 Rank、GA4，`workers=0` vs `workers=1,2,4` 的 frozen `ExactWindowRankPlanner` consumer序列、所有 request身份、slot/cursor/episode、action/state/latent mask/transform输出、Packed128张量/排序、terminal partial、每个 member 加权 loss 与 generation 梯度路径一致（对随机 augment 使用相同 RNG 合同和受控 mock）。
- **真正多进程 Evidence**：运行时 worker PID != trainer PID（不能仅测试创建线程或配置被传入），worker lifecycle/prefetch bounds/persistent/stop/crash/timeout/error/cancel/abort/restart；数据没有交叉污染和重复；模型与 CUDA 均不被 worker touch。增加失败注入覆盖。
- **Checkpoint/Resume**：Synthetic full checkpoint & Frontier authoritative restore，Fresh100→Resume101/500 的 CPU高保真路径；严格 live model/optimizer/scheduler/CUDA-RNG/DCP 仍列为 GPU Gate，不能用合成 fixture 声称已完成。
- **Negative cases**：workers参数非法，workers=0 搭配 prefetch/persistent非法，wrong rank/world/GA/seed、bad ordering/ABI/provenance、坏 sidecar/Config/receipt、改变 active Job 并开 Workers、不同 Worker 配置 same-job Resume、错误 official DROID 初始化、G1/local/原8卡 regression，不准假绿。
- **测量计划**：先收集 worker0/1/2/4 在同源同批的数据加载 wall、`data_prepare`、`data_wait`、Transform、Collate、step_wall、Forward/Backward、rank straggler、RSS/IO和CPU占用；性能实验须单独 Owner/DS GPU 授权，不能把“支持 worker”与“已经加速”混为一谈。
- Ruff/format/pytest + source SHA、code diff、完整直接相关回归覆盖；测试/作者 Evidence 原始 JUnit、日志、配置和可复核 commands 存于独立位置，标注 synthetic vs real 限制。

## 5. 保护与交付

- **禁止改动**正在运行的 G1 正式 Job、本机当前 No-TTT 正式 Job、旧 Checkpoint/Identity/评测文件，禁止在训练服务器上 checkout、reset、clean、kill、GPU probe、改真实 Source/Cache/Index 或实际训练。
- 允许最小范围更改：Child `cosmos_framework/trainer/matched_no_ttt.py`、安全的新 CPU worker adapter + tests、`examples/psm_wma_robocasa_corrected_phase5.py` No-TTT-only CLI/构造绑定；Root `scripts/train_v3_matched_no_ttt_4gpu.sh` No-TTT worker选项、对应 CPU tests/runbook/入口和 Child Gitlink。新证据可以追加在 `docs/collab/codex/`；**不要改** G1 trainer、模型代码、官方通用 Trainer/DCP、统一 required-TTT RoboCasa Queue。
- 若要改 Frozen Generation model/optimizer/outer loss、取消 Legacy worker0一致性、改变 Exact-Window planner/数据序列/旧 checkpoint schema、或同一个正式 Job 强制迁移，**停止编码并提交设计 blocker**，不得隐式扩大 scope。
- 在独立 candidate branch 完成 code+CPU 后，交：`Root formal implementation SHA`、`Child/Gitlink SHA`、相对上述 baseline Pair 的最小 diff、使用方式、test matrix/真实 evidence和 known limitations。按旧流程请求 **GPT 独立增量 Implementation Gate**，再由 DS_PRO 独立 CPU，随后 Owner 另行授权 GPU Canary、perf benchmark 和训练。**不得在得到 Gate 前合入 V3或启动 GPU。**

## 6. 必查源文件索引

- Child: `cosmos_framework/trainer/matched_no_ttt.py` — 目前 `bind_grouped_stream(...num_workers=0)`、`training_step` 同步 `producer.produce()`。
- Child: `examples/psm_wma_robocasa_corrected_phase5.py` — `preflight` 限制 worker0，`GroupedTriggerLoader` 只触发空 dict，No-TTT-only Trainer 接线。
- Child: `cosmos_framework/model/generator/mot/robocasa_exact_window_local.py` — `ExactWindowRankPlanner`、`prepare/materialize`。
- Child: `cosmos_framework/model/generator/mot/robocasa_async_segment_prefetch.py` + `cosmos_framework/utils/ordered_prefetch.py` — **现成线程方案，仅供参考，不算真实多进程验收**。
- Child: `cosmos_framework/trainer/local_memory_grouped_resume.py` / `cosmos_framework/trainer/matched_no_ttt_test.py` — immutable checkpoint/same-job Frontier。
- Root: `scripts/train_v3_matched_no_ttt_4gpu.sh`、`tools/v3/matched_no_ttt_entry_test.py`、`docs/build/PSM-WMA_V3_Matched_No_TTT_4GPU_profile_v1.0_2026-10-26.md`。
- NVIDIA official: `cosmos_framework/data/generator/joint_dataloader.py` / `cosmos_framework/data/generator/action/datasets/action_sft_dataset.py`; official `action_policy_robocasa_nano.py` has `num_workers=4,persistent_workers=True,pin_memory=True,prefetch_factor=4`. Official loader can prove framework capability, **not our matched sampler parity**.

**Final requested output: Codex implementation candidate with CPU Evidence, not immediate formal training.**
