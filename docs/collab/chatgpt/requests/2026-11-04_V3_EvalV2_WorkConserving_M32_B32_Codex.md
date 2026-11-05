# Codex 实现任务：V3 EvalV2 Work-Conserving Sim–Policy 流水线（M/B 独立上限 32）

**Owner 指令：2026-11-04。优先修复真实吞吐瓶颈，不做无关框架重构。**
**状态：Owner 需求 / Codex 待实现；不是完成的代码、审核结论或 GPU 运行授权。**

## 0. 基线、分支与并行协作（必须遵守）

- Root：`wxwy/psm_wma`，最新 `origin/V3` 在本任务创建时为 `ea0828c7d45a443cc74ae2582419f14e7782a17e`。
- Child/Gitlink：`wxwy/cosmos-framework`，基线 `1069fe78841228cadbbfbe6afbd767eaed6225da`。
- 两仓候选分支均已建立：`v3-evalv2-streaming-m32-b32-20261104`。Codex 开工前**再次 fetch 最新 origin/V3、确认 Gitlink**；V3 若已快进则将候选分支无损 rebase/merge 到最新基线，不以过期 SHA 为新工作的权威。子模块必须从正确 Child 分支提交，Root Gitlink 指向最终 Child formal implementation SHA。
- G2 同期在 `v3-g2-spatial-policy-20261104` 等候选分支开发 `tools/g2/**`。经检查目前没有直接修改 EvalV2 生产路径或 Child Gitlink。**不要覆盖、回滚、修改或擅自合入 G2 未批准候选**；两条线在独立分支工作。提交审核通过后，以当时最新 `origin/V3` 为基线整合，保留两边提交、测试并解决文档/账本冲突；不要 force push V3。
- 不在正在运行 R04 的服务器生产 checkout 修改代码；不停止/重启/Resume R04，不动 R03/R04 原有实验目录、checkpoint、训练及数据集。此任务默认仅实现代码、CPU tests、静态检查与文档证据；后续真实 H100 Canary/900EP、V3 promotion 需要相应审核及 Owner 运行授权。
- 遵守 `AGENTS.md` 与 Child `AGENTS.md`，由 Codex 写实现、ChatGPT 独立审核、DS 独立执行验证。**不要提交只改数值上限而没有真实并发的“假修复”。**

## 1. Owner 想达到的实际行为

`sims_per_gpu=M` 表示每张 Policy GPU 配套的**实际运行的可复用 Sim Slot 数**，`max_infer_batch_size=B` 是该 Policy GPU 单次 Native Generate 的**独立上限**。二者应可分别在 `1..32` 显式配置、受资源预算和执行 profile 约束，**不要求 M=B**，`Phase A` 保留既有 `M=B=1`。

目标运行示例：`gpu_ids: [6,7]`、`render_gpu_ids: [4,5]`、`sims_per_gpu: 32`、`max_infer_batch_size: 8` 或 `16`、`save_rollout_mp4: false`、`save_generated_video: none`。若正式任务仍是18 Task×50EP，该计划理论上需要 **2×32=64 个真实 Sim Slot**（不只是 YAML 写32），每张 GPU 一个 Policy/Session owner；每个可执行 Sim 最多一个 outstanding action request。

需要的**非屏障、持续流水线**：

```text
GPU4: 32个有独立环境/Session的Sim ──各自产生下一次Observation/State──┐
                                                                       ├── GPU6 单Policy owner
GPU5: 32个有独立环境/Session的Sim ──各自产生下一次Observation/State──┐   │   Ready请求队列
                                                                     │   │
GPU6/7 各自独立：Ready即入队 → 尽早聚成至多 B=8/16 的 microbatch → generate_many
    → 同批各结果按 Session/RequestKey/Frontier 独立返还 → 收到结果的Sim立即执行16步
    → 执行完立即再次 Ready入队；Policy 不等待其余Sim/下一轮/全局同步。
```

不得等**全部32个Sim**都就绪才启动Batch。凑不满B时按有限 `batch_wait_ms` 及时发较小Batch；不能让快Sim等慢Sim、不能把CPU Sim创建或某Task切换放在全局 Policy 推理锁内。B只是上限不是一次必达数。目标是**工作保守（work conserving）**：有Sim可执行就继续，有Ready请求且Policy空闲就调度，低占用时允许小Batch及时响应；显存/时延实测决定使用B8还是B16，B32仅要求链路正确支持，不宣称高效或安全可用。

## 2. 已确认的真实代码障碍：须成套整改

### P0-A. M32/B32 上限的“端到端”支持

现有以下层明确限制8，必须同一原子语义统一修改，含负向验证、协议绑定和运行时回读：

- Root `scripts/robocasa_eval_v2/config.py`：CLI/YAML 解析、`M/B>8` 校验、Phase A 边界、`execution()` manifest 身份；
- Child `cosmos_framework/evaluation/robocasa_v2/contract.py`：`execution.sims_per_gpu`、`max_infer_batch_size` 1..8、冻结 manifest；
- Child `cosmos_framework/inference/robocasa_transaction_client.py`：客户端 Batch 上限验证及响应 `native_batch.size` 证明；
- Child `cosmos_framework/inference/robocasa_batch_transactions.py`：实际 Native microbatch cap 和完整 Session/Batch/Request 身份、排队与返回；
- Root `runtime.py`：Server启动参数 `--transaction-max-batch-size`、Session cap、`/info` 生效回验、进程/内存资源限制，检查所有其他未列出的隐性 8/16/task_count 常量。
- **不允许静默clamp**：用户配置32实际只运行8/18/16要明确失败或有可验证的真实Slot数；不支持时应在启动前 fail-closed。

### P0-B. 真正可同时运行64 Sim，而非当前“Task数封顶”

Root `scripts/robocasa_eval_v2/resources.py:physical_slots()` 当前 `pairs[:task_count]`：18 Task时即使 M32 也最多18个物理Slot。现有 Child `RoundScheduler` 每轮每Task只派一个EP，并在一轮结束前不派下一轮（`scheduler.py:99–142`）。两者必须一起解决，否则M32只是配置伪扩容。

- 引入**显式版本化的新 work-conserving 调度协议**（建议 `streaming_task_affinity_v2`，精确名称可由实现确定）；旧 `episode_major_frozen_order_round_barrier_v1` 的 manifest/Resume 行为必须不变。不要静默把历史Run切到新协议。
- 新协议中 Idle Slot 立即从900个逻辑 `(task,episode)` 工作项领取下一个，不等Round Barrier；允许同一Task的不同Episode同时in-flight，**同一个Task+Episode不得并发/重复执行**。可优先复用当前Slot的Task环境以降低 `make_env()` 成本，但不得长期饿死其他Task。
- 必须重新检查 Store 的 `active_tasks`（一个任务Stream）、`active_attempts[(task,ep)]`、`dispatch_tickets`、`begin_task/begin_episode`、`allocate_environment`、`bind_sampling`、`commit`、`cleanup_stream`：并行同Task下 Stream/physical-slot/seed/grant/attempt/End/Reset/provenance 的所有权与原子性仍正确。同步仅围绕小的元数据提交/分配临界区，**不得把耗时 Sim 构建/运行时哈希/HTTP/推理放在 Task 全局锁内**。
- 真实计划满足：2 GPU×M32、18 Task×50EP → dry-run/CPU模拟报告 **64个互异真实物理Slot身份与至多64个并行占位**，同Task允许多EP并行完成，900唯一EP最终恰好900条有效/授权Owner-pending结论。不能通过复制虚假任务名称凑满64。
- 每个物理Slot绑定独立环境seed grant与完整环境/场景证据；并行后的场景采样/调度可能与R03/R04不同，必须**在新Run的 manifest 明确新调度/采样语义与比较边界**，绝不声称跨新旧Run逐EP场景完全匹配。
- 运行故障/中断：完成的Core不可重跑，未完成可依现有Owner授权Resume/安全清理协议恢复；同Task并发不能让一条失败污染其他Task/Session、也不能绕过当前 fail-closed 规则。重复/迟到结果/跨Slot错误响应必须拒绝。

### P0-C. 去除启动及Task切换的无意义串行阻塞

Root `runtime.py:_actor()` 的 `with self.setup_lock:` 当前横跨 `_server()`、Worker创建、`actor._receive()`、`_start_assignment()`，其中还有原生环境切换、`native.make_env()`；实际观察每个Sim约85–90秒依次出现。Child `eval_v2_worker.serve()` 在 `READY` 之前重复 `native.verify_runtime()` 和Vendor hash/asset审计，耗时较高。

- Codex 先以窄范围 timing markers 精确区分 `server startup / Worker import / render proof / vendor attestation / READY / make_env / reset / Session register`，再最小化锁粒度。
- 单GPU Server一实例的并发创建必须 exactly-once；其他Sim可并发初始化，shared actor/slot/stream/seed/proofs/ports/registry 锁和所有权不破坏。允许任务环境切换并发，不允许两个请求同时操作同一物理Slot。
- 优化或复用重复 attestation 时保留源码、资产、Runtime Digest 与实机EGL上下文的**真实身份核验与变化检测**；不可简单删安全检查、缓存伪证或绕过clean-source校验。若既有冻结证据contract不允许等价优化，先给Reviewer精确设计差异，不硬改。
- 新Run并发初始化达到真实加速；旧v1 Resume/Manifest仍可使用原路径。

### P0-D. Sim–Policy 真正异步、低等待microbatch

Child `BatchedSessionTransactions` 已支持多Session `generate_many`，应**优先复用此实现**，而不是新增独立Policy/FSM/高层planner。

- 每GPU单模型Owner、多Session并行；每Session严格按 frontier/seq 顺序，一个outstanding请求；Ready请求按到达流入有界队列；Policy按 B上限 + 有界 `batch_wait_ms` 生成并路由，结果一到立刻释放对应Sim继续执行，不等待一批Sim全部完成Episode。
- 测试单GPU同时32个Session、2GPU64个Session的注册、队列、分组、返回/继续、背压、超时、取消、重复/迟到request、Session reset。必须证明Batch B8/B16/B32契约能穿透Client→Server→Native `generate_many`→Response，而非仅输入可解析。
- 避免大Batch高尾延迟/显存暴涨；无忙等、无无界缓存、无跨Session Fast State泄漏、无其他Session的End或media解码堵死所有Policy。请求队列和临界区应有真实timing/计数器以诊断是否Policy空闲但有Ready请求。
- 保留 `save_generated_video=all` 的严格Media ACK/落盘/End时序、`none/first` 原语义。**当 `save_rollout_mp4=false` 且 `save_generated_video=none` 时，不要每step为no-op `on_frame` 额外执行 `compose(obs)` 或启动Encoder**；不能跳过Policy自身需要的相机观测与未来生成。

### P1. 资源门和性能观测（只做必要部分）

- `max_rss_bytes` 当前常用约128GiB，64个真实Sim可能超过它；必须以实际owned RSS和GPU显存作有界准入，**不得静默提高/绕过预算**。支持用户针对新Run显式配置较大内存预算；超额预检/运行报明确 `BLOCKED_RESOURCE` 并安全清理。 `M32` 是**能力上限，不是强制默认值或保证任一H100必可跑满**。
- 在原生Stats/日志中少量新增（或扩展现有）`active_sim_slots / initializing / ready / executing / waiting_policy / idle`、per-GPU `queued / queue_wait_p50,p95 / batch_histogram / batch_generate_time / requests_finished / active_sessions`、Round/EP completions和吞吐；只读 telemetry 不能成为调度全局锁瓶颈。
- 测试配置参考 `M∈{8,16,32}`, `B∈{4,8,16}`，另 `B32` 作为API/CPU shape/显存门能力验证，**默认不用B32正式评测**；保留 `batch_wait_ms` 可配置（例如5/20/50ms做有限对照），勿先实现复杂自动调参框架。
- 不把不同ckpt、媒体开关、任务场景之间的速度差异直接归因于M/B。

## 3. 真实背景数据（说明问题，不能充当新代码的验收）

- R03 `iter20000`：M1/B1，18×50共900EP，`SR=454/900=50.4444%`，保存900段Rollout+28,464段Generated MP4；全程约58 EP/h，推理p50约1348ms。
- R04 `iter27700`：M8/B8，16个Sim启动严重串行，约85–90秒一个；无Rollout/Generated MP4。北京时间16:02–16:07五分钟实测50→71 EP（窗口等效252 EP/h），但GPUs 4/5/6/7平均Util只有约11.6%/12.7%/21.3%/19.4%，Batch大多为1–5，Batch6出现长尾。**短窗口吞吐不是全程速度**；当前R04仍在运行，禁止碰它。
- 障碍定位：`runtime._actor().setup_lock` 范围过大、每Worker重复runtime probe、`physical_slots`受Task数限制、`RoundScheduler`的严格轮次屏障、Batch上限8分布在根/子多处、禁视频时无用`on_frame`拼图。

## 4. 必须交付的Acceptance Evidence

**A. CPU deterministic Gate（Codex可以执行；无GPU/模型/数据）：**
1. Root/Child上限统一：M/B `1,8,16,32`接受；0、33、非整数拒绝；Phase A非1/1拒绝；effective Native Batch与Manifest/YAML/CLI/Server/Client一致，禁止silent clamp。
2. 对18 Task×50EP、2 GPU、M32/B8与M32/B16，模拟64独立Sim / 64独立Session（当资源预算允许），动态归还继续，严格900唯一Core；B32完成CPU端到端形状/路由/防错验证，不能声称GPU B32已验收。
3. 无Round Barrier新模式：受控慢Sim不会阻止另一个Slot处理后续EP；跨Task公平、同Task多EP并行，禁止同 `(task,ep)` 重复或串改；旧v1按原Round Barrier语义回归。
4. 并发启动Gate：伪Slow READY/Slow make_env：多个Worker能重叠初始化，Server exactly-once，原生Slot/Proof/Grant/Task Stream一致；异常/超时/OOM清理不污染其他进程与GPU。
5. 状态正确性：Action/TTT `Session/Frontier/fast weight`分离，结果正确路由；超时/Retry/Resume/Replay、Owner-pending、任务失败/成功、清理/stop均具备真实公开API层级行为证据，不只Helper模拟。
6. Media回归：`none`确实无Encoder和额外逐步拼图；`first/all`原来的严格及诊断语义、成功SR和媒体失败解耦都不回归。
7. Ruff/format/py_compile/定向pytest、真实Full Diff/Source SHA绑定、JUnit与可复现完整命令；保留当前单GPU M1/B1、M8/B8 的原有测试结果和schema，禁止删改旧断言来拿PASS。

**B. 后续DS实机Gate（本任务不自动授权）：**
- 独立、短时CPU→H100小规模Canary；确认两张Action GPU+两张Render GPU真实设备/进程、并发64Slot方案的实际RSS、VRAM、EGL、Batch分布、Session reset、ep结果/媒体none。
- 在**同ckpt、同数据与媒体配置、同评测协议语义**下测M8/B8、M16/B8、M32/B8、M32/B16，记录warmup后 per-EP/每轮wall、吞吐EP/h、CPU/GPU利用率、B分布、request p50/p95/p99与OOM/timeout；性能是否提速是实证而非先验保证。
- 不承诺B32一定可在H100安全推理，失败时必须在边界明确上报且资源回收，不中断其他任务。正式900EP新Run须Owner再授权。

## 5. 实施顺序与停止点

1. 先写一页`gap & minimal design`：列出待改文件、需要版本化的科学/调度契约、锁粒度方案，避免一次性跨系统大重构；Codex选最小实施。
2. 依次提交：P0-A联动上限+配置回归 → P0-C并发初始化 → P0-B新Scheduler/多同Task Episode → P0-D Policy microbatch异步+Media none轻量化 → P1 telemetry。每步必要CPU证据；可以合并相邻步骤，但不能省掉真实64Slot gate。
3. 两仓提交**独立候选**，Root Gitlink精确绑定Child；更新当前任务专用的实现说明和evidence（不覆盖G2 docs、旧SESSION/Inbox），提供新 formal Root SHA/Child SHA、diff、reproduction命令、CPU证据。
4. Codex将候选提交送给ChatGPT做**fresh independent Code Gate**，随后DS独立CPU/必要硬件Gate；**未经该轮Gate不得把新代码自动promote到V3，更不得更新正在执行的R04工作区**。
5. G2代码如在此期间进入V3，从**合并时最新V3 HEAD**处理祖先变化；合并只在双方各自审核通过后，验证无交叉代码/仓库Gitlink冲突并执行新Pair最小回归。不得使用`--ours/--theirs`粗暴覆盖其他人的G2成果。

**任务不是“做新框架”，核心验证是：M32真实扩64Sim、B8/16作为独立可选上限、Ready→Policy→Result→Sim持续流水、不再全局串行初始化或被Round Barrier拖住，且旧科学/TTT/Resume/媒体合同不回归。**
