# PROPOSAL ONLY — V3 No-TTT Async+Compact 同一DCP的真实GPU与Resume资格验证

- 日期：2026-10-29；**状态 `PROPOSED_NOT_AUTHORIZED`**。这是待 Owner 决策的实验设计，不是可直接执行的GPU命令。
- 正式异步候选：Root `e0fe911dfb9fd34957234828195cf051713f6c3d`、Child/Gitlink `f6a92d47b6dac7998ddc58b3da26ef93f8068dc7`，Code Gate `APPROVE_CODE`；DS独立CPU301报告 PASS，原始文件待GPT直接回读。No-TTT当前正式Job `no_ttt_packed128_droid_fresh_30k_world4_ga4` **已在旧Loader `NOTTT_LOADER_WORKERS=8` 模式继续训练**，而不是nw0。
- 目标：证明 **旧正式NoTTT完整Checkpoint** 可在新候选代码里严格恢复；真实 Source/Cache/Index/Tokenize、4Rank Frontier、native模型/optimizer/scheduler和CUDA RNG正常；在 GPU4–7 的真实模型运行中，新 async Source+Transform跨GA/Window预取能够改善数据等待和Steady-State Step Wall，且不会因CPU/RAM/IO拥塞反而退化。

## 资格前置 — Owner与环境

1. **不能在现有Job仍活跃/占用GPU4–7时启动任何新训练或直接Resume**。Owner决定何时安排空闲的独占GPU4–7（不触碰GPU0–3），以及管理隔离DCP复制的磁盘/retention。DS只能只读确认现有 Job 实际source/import、`nw8`、当前latest complete、4rank sidecars；不可擅停、擅清理。
2. 只使用原正式Job最新冻结的**完整且已committed** checkpoint，带`complete.v1.json`、rank sidecars、model/optim/scheduler/trainer/RNG；禁止模型only Fresh、用不同数据源/seed、跳到旧进度或用文件名冒充DCP完整性。Owner许可后才可制作独立隔离Clone；原Job的`latest_checkpoint.txt`和identity绝不修改。
3. 需记录新候选代码实际Root/Child/import来源、DataLoader实际工作模式和本地staged processor是否支持 `AsyncRecipe`，以及可用Host RAM、worker启动及Cache mmap、GPU并发资源。任何不匹配应fail-closed，不改身份/digest去绕过。
4. 新 Candidate Root+Child不合并V3、不改活动训练server工作树，命令需经 Owner/GPT依据现场路径定稿（此提案没有可授权的实际启动payload）。

## 一个最小匹配比较（不是再建立新的30k训练）

在 GPU资源释放后，使用来自**同一个真实DCP点 C**的两个独立隔离输出namespace，**同一数据/模型/训练合同**顺序运行：

- 对照A：`Compact=1, NOTTT_LOADER_WORKERS=0`，实际老同步 `producer.produce` 路径。
- 候选B：`Compact=1, NOTTT_LOADER_WORKERS=8, NOTTT_PREFETCH_FACTOR=1, NOTTT_PERSISTENT_WORKERS=1, NOTTT_LOADER_TIMEOUT_S=120`，新真正异步 `NoTTTAsyncLoader`。
- 两臂都用 `world4/B8/T16/GA4/Generation-only/30k-warmup500/save100`，共享同一固定C与来源但**不同隔离OutputRoot**；真实DCP/Rank边界恢复必须先通过，新增的第一 optimizer commit=C+1。应选择足以覆盖Worker warm-up/稳态的**少量连续Step**，依据Owner授权和资源决定明确步数（例如每臂10–20，首个冷启动窗口分开报告）。日志必须分开且防止数据/Checkpoint/Job互写。
- 对比 **全训练Step wall P50/P90及有效窗口数、GPU等待数据时长/同步间隙、CPU Read+Transform的真实时间交叉、forward/backward、worker各PID/生命周期、Host RAM(RSS+mmap说明)、I/O拥塞、GPU显存、Rank0–3 tail和异常**。必须使用与CUDA计算关联的测量定义，不能把CPU `raw_wait_host_ms` 当成真实GPU idle。
- 同时验证新候选 `nw8` 第C+1步的成功恢复健康与后续正常optimizer提交、所有rank Frontier/iteration、RNG/sidecar/worker异常路径；失败保存证据，**不自动回退旧Job/重新Fresh**。不以旧Dense0→Dense0本来就失败的严格GPU bitwise gradient allclose作为硬性新Gate。
- 历史旧实际Job `nw8,Compact0`（不同训练阶段）可用作方向性背景，不可声称为相同Checkpoint对照或与A/B直接相减归因。若Owner希望分离Compact整体效果，可在已有许可时间与GPU预算内增补第三个oldLoader对照，但不是本提案自动授权。
- A/B匹配后 **B真实稳态壁钟与等待有可观改善、且Resume数据/数值健康无回归** 才能宣称优化带来真实训练吞吐收益；若B更慢，即便CPU并发存在也不得称性能Gate PASS。

## 权限和最终切换

- 先收齐DS CPU原始文件做最小原件核验，再由Owner决定是否批准此一次隔离GPU/DCP Qualification及资源窗口；GPT审核固定现场命令后交DS执行。不能以此Proposal作为自动授权。
- 原正式Job仍在运行。即使资格验证PASS，也必须 **Owner另行授权** 在完整已保存optimizer边界结束旧进程、确认无并发Trainer与正常Checkpoint，再用同一正式Job名/源数据/训练状态继续到总iter30000；不是从 DROID Fresh，不是新独立Fresh10 Job继续到30k。
- 不变更旧Job的存储Cleaner策略、不清理任何 checkpoint、不改旧identity文件、不合并其它仿真技术线。本路线只处理 No-TTT 训练。
