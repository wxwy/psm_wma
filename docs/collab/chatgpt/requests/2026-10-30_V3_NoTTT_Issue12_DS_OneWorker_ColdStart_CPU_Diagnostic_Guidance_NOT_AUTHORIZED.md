# DS_PRO — Issue #12 No-TTT 首包120秒超时：冷启动定位指导

日期：2026-10-30。Frozen Formal Root `e0fe911dfb9fd34957234828195cf051713f6c3d`，Child/Gitlink `f6a92d47b6dac7998ddc58b3da26ef93f8068dc7`。原 Issue#11 CPU301/6raw PASS 与源码 APPROVE_CODE 不重审。Issue#12真实B DCP加载后0个commit、首个`next(self.iterator)`120秒超时，性能 INCONCLUSIVE。

**权限严格分两段**：Phase R = 原有日志只读核对，**现在可做**。Phase P = 新真实数据 CPU-only 冷启动探针，**仅准备设计/脚本/完整命令，`PENDING_OWNER_AUTHORIZATION`，禁止运行**。该指导不是实验授权，不授权停止正式Job、修改Checkpoint、生产代码、V3、Gitlink、Cleaner，或启动CUDA/torchrun/训练、仿真、再次301项CPU Gate。

## Phase R — 只读回看已存在证据（现在做）

1. 针对同一次 Arm B 失败，整理各Rank现存日志时间线：DCP loaded → iterator创建 → torch DataLoader worker spawn PID和实际PPID（如有）→ 首次materialize等待 → 120秒异常 → 仅本实验Worker清理。每个实测事件标`file:line`和UTC时间。没有记录就填`NOT_MEASURED`。
2. 明确区分 PyTorch DataLoader Worker 与 loky/LeRobot内层进程：仅32个loky PID和42条W1030警告**不能**当作32个DataLoader Worker已完成`recipe.build`的证据。
3. 检查日志是否曾记录Worker内`recipe.build`开始/结束、`VerifiedIndex/Cache`、`RoboCasaExactWindowSourceReader`、`LeRobotDataset`初始化、首个Source/Transform、首个packet返回。主进程Preflight约186秒不是Worker阶段的实测。如果都没有，结论`FIRST_PACKET_STAGE_NOT_MEASURED`，不循环索取不存在的日志。
4. 保存`ISSUE12_PHASE_R_TIMELINE.md`，仅现有记录，不运行GPU/新真实数据CPU探针，不改任何目录。

## Phase P — 只设计单Worker真实数据 CPU 探针，不执行

在独立`/tmp/dspro_issue12_worker_coldstart_...`设计**仓库外的临时脚本**（DS不改prod/tests；不需要Codex修源）。冻结代码/数据来源仍是同一Root+Child+已验VerifiedIndex、缓存与已staged本地Tokenizer。只用一个合法真实Segment Request，一次Worker spawn和一次首包，无模型/梯度/optimizer/DCP加载、无其他并发参数扫描。

运行设计必须具备：
- `CUDA_VISIBLE_DEVICES="" COSMOS_DEVICE=cpu HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1`，worker数恰为1、`prefetch_factor=1`、Compact=1；原则上沿用真实`AsyncRecipe`/PyTorch DataLoader路径而不是模拟值。只读原始数据；所有脚本、cache、log和输出放独立`/tmp`，限线程、内存、运行wall，异常只清理由此脚本创建的子进程。
- 计时节点尽量覆盖`parent construction → worker import/init → PreparedDataset.__getitem__ → AsyncRecipe.build → VerifiedIndex/Cache/LeRobotDataset init → first source/transform/packet encode → parent next() return`。无法用外部临时包装取得的阶段必须标`NOT_INSTRUMENTABLE`，不复制/修改生产逻辑制造假结果。**保持原120秒取数deadline作为测量基线**，不能以直接调大生产Timeout替代归因。
- 提交`CPU_PROBE_PLAN.md`及拟执行的外部脚本/完整命令、真实数据与候选源码来源、隔离输出、资源上限、异常退出和证据格式，**先STOP等待Owner另行授权**。未授权不得运行该脚本、更换nw2/4/8重试或恢复任何GPU训练。

诊断若日后获授权，一次结果按证据区分`WORKER_BUILD_GE_120S`/`FIRST_PACKET_PREP_GE_120S`/`SINGLE_WORKER_FIRST_PACKET_LT_120S`/`INCONCLUSIVE`。单worker快不代表4rank×8worker并发不超时。后续代码修复归Codex；任何新Formal Pair需增量Code Gate，不重审旧301。
