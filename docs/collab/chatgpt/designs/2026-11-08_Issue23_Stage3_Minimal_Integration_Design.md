# Issue #23 — Stage3 最小 Policy 接入设计（GPT → Codex）

**状态：DESIGN HANDOFF / IMPLEMENTATION NOT STARTED；不是代码 Gate PASS，也不是 GPU/SR 执行许可。**
日期：2026-11-08。设计负责人：ChatGPT；实施与原始证据：Codex；独立 Code Gate：GPT。
本设计增量细化已独立批准的 Stage0（Child 8a170d56014af937b146b35e2b89753313614785）；不可隐式修改 Stage0 已冻结的实验条件。

## 0. 冻结依据及范围

- 已验证 Stage1 standalone CPU 源码 Root 3ab4578475d8df5ce93b7bde6c4f2073a46f777e / Child+Gitlink 0a2119782fb5078fee3359f9ef7383d788744458。PR #6 尚为 Draft。**从该 Child 真实代码增量实现，不从未合并 PR #4 cherry-pick。**
- 官方 V3（设计时观察 Root 7b8b733e1f585bb44a0eac7c14ad545c29355a86）仍使用 Child 1ca308055fc41fb69efaeb9efaa23808f164a18e。不得修改/合并 V3、PR4/PR5/PR6，也不得切换任何运行中 Source Resume。
- Stage2 已测：B8 RGB 重建 Owner 人眼 PASS；真实 H100 B1/B4/B8 编码吞吐；16 个实际 RoboCasa EGL Sim + 一份真实 Wan BF16 Worker 同 GPU4 运行，并保留严格物理 PCI/current-context 校验。256 帧预热后 Sim+B1 28.051 step/s、B4 50.238、B8 54.520（注意负载是零动作+离线签名特征，**没有 Policy/SR**）。
- **重要未关闭 Gate**：B4/B8 对 B1 的 BF16 完整 Latent/Visual96 不满足原设计 exact0；B8 真实训练 DCP 下的 FastState、Prefix、Action 非零变化（3 组中 Action max_abs=0.0301193；相对 RMS 约0.49%–0.60%，固定合成 raw15）；不能将视觉质量 PASS 当作 Action/SR 不变性验收，不能偷偷降低 exact0。
- 实施只允许 Stage3A **隔离分支代码 + focused CPU 合同、synthetic transaction、no-GPU 演练**。Stage3B 真实 B8 Action/SR 是独立后续 Gate；新代码未通过独立审核不得运行真实模型、仿真或训练。

### 为什么拆两段，而不是一次全接入？

**Stage3A（P0 首要，必须先完成）**：接通最小可靠 C 路线，Worker B1/wait0 严格匹配官方 Encode1 数值，完成 Single 1 Policy Server × 1 Sim 的 A/B/C 实验能力。它回答 Local-TTT 实际多耗多少时间、耗在哪里以及同权重工程改造是否保真；保留原 B 路径与 A No-TTT。

**Stage3B（不阻塞 Stage3A）**：以 Stage3A 同一特征路径把 Worker 参数拓展为 B4/B8，先在受控实验下记录 B8 Visual96→FastWeight/Prefix/Action/SR 效应，确认下游容差与真实配对结果后，才可由 Owner 决定是否以“非逐位等价的新候选配置”上线。不把 B8 标为等价替换，不把其新结果写回旧 B1 exact Gate。

单 Sim C 必须从 B1 完成，不依赖 B4/B8、32 Sim、额外 Server、Agent、RSI、模型训练或新视频模型。这样不是过度架构。

## 1. 重用现有真实权威（不得重建另一套事务框架）

| Authority | 冻结代码和必须保留的事实 |
| --- | --- |
| 真实执行动作来源 | Child cosmos_framework/simulation/robocasa/closed_loop_eval.py：step循环在每次 env.step 前获取 pre_composite，预测 raw15 经 canonicalize_raw15_for_env 转为真正执行动作；只有 env.step **成功返回后** record_completed(pre_composite,canonical_raw15)，actual source_step 从0递增 |
| 当前存量 OnlineLocal | Child cosmos_framework/inference/robocasa_local_memory_policy.py：_parse/prepare/commit_many/abort/reset，原始 B 路径逐一 Encode1 处理连续 source_steps，并调用 model-owned OnlineLocalMemory |
| 原子 FastState | Child cosmos_framework/inference/local_memory_online.py：OnlineMemoryRequest、prepare、候选私有状态、commit/abort；consumer_step 必须对应连续真实完成帧 |
| Native Policy 事务 | Child cosmos_framework/inference/robocasa_session_transactions.py 和 robocasa_batch_transactions.py：既有 SessionLease.identity() 十个 public 字段、Response/ACK、Batch atomic commit、Model Executor；原始 Source Timeout/transaction mode 不改变 |
| Policy current VAE | Child cosmos_framework/scripts/action_policy_server_robocasa.py 与 robocasa_composite_visual.py：当前图像本来就在 Policy get_data_and_condition 路径做 Encode1；**官方版本当前没有实现可靠的 full pre-crop Visual96 boundary 持久捕获**，必须由 Codex 直接实现（PR4 未合入） |
| Stage1 standalone Worker | Child inference/robocasa_vae_protocol.py、robocasa_vae_worker.py、robocasa_vae_client.py、robocasa_vae_encoder.py：严格不可变 Frame、HMAC、Session/capability、B1/4/8 READY、Bounded Queue、End/Quarantine；当前 owner_issue/submit 只支持连续来源序号 |
| 独立真实 Process 管理 | Root scripts/robocasa_eval_v2/runtime.py、resources.py、startup.py、scripts/robocasa_eval_v2_processes.py：Registry 启动/监控和分离 Actor/Server；不可把共享 Worker 作为某个 Sim 的子进程，否则 per-episode cleanup 误杀其他 Sim |
| EGL | 已用原生 configure + verify_current 证明：仅在 Sim 子进程配置 NVIDIA EGL ICD、授权 render 组访问与物理 PCI 校验；不得依靠 ordinal 假定、放弃 context 证明或修改系统全局 vendor 清单 |

Codex 先对这几处直接关联代码做 **最小增量读取**，以实际 HEAD 函数名/签名为准，若本文假定的 seam 与源码不一致，先形成 DESIGN_DELTA 申请 GPT 复核；禁止自己替换整个 LocalMemory、执行框架或编码模型。

## 2. 真实数据流：15 + 1 且严格因果

采用 **真实源帧 source_step s**（不是 Worker 压缩序号）：

- 第一次 Replan（source_step=0）：尚无已执行历史；Policy 按原生路径生成动作，**同一次当前 Encode1** 取完整裁切前 Latent → Visual96，作为该 16-action Chunk 的边界候选。这个 96D 特征仅在原有响应成功/事务 commit 后成为 Session 私有可用缓存。**不可增加第二次当前 Encode1。**
- 当真正 action0 成功执行：可信 Sim 执行 wrapper 记录 pre-action RGB(0)、canonical executed raw15(0)、成功 env.step0；Owner 与 Policy committed 边界缓存(0) 的源 RGB digest/Session/Chunk/request_key 匹配后，通知 Worker **跳过但登记真实 boundary0**。Worker 不对 source0 Encode1，也不制造一份伪 Worker Feature。
- source_step=1..15：每个 env.step 只有成功完成才允许形成 owned RGB+raw15 快照，向同一 Sim GPU 的 Worker 提交 Frame(1..15)，Worker 是独立的 T1 编码，允许跨不同 Session/step 动态聚批；B1/wait0 不等其他 Sim。已完成/签名并验证的结果按真实 source_step 入 Session evidence spool；异步 worker 不能改变 Sim 执行顺序。
- 下一个 Replan（source_step=16，consumer_step=16）：必须取得完整连续的16份已执行历史证据：**Policy boundary Visual96(0)+Worker Visual96(1..15)**，按 source_step 0..15 搭配各自 **执行后的 canonical raw15(0..15)**。调用既有 model-owned LocalTTT 更新，先 private prepare，再同一事务 native Policy generation / response commit。当前 source_step16 的 Visual96 在**这次当前 Policy Encode1** 中捕获，作为下一 Chunk 的 committed boundary 候选；它不属于上一16步的记忆证据。
- 后续周期：boundary16 + Worker17..31 → consumer32；boundary32 + Worker33..47 → consumer48，依此类推。**不能**把 Worker 历史重编号为 0..14 或丢掉每段的首帧；不可把目前 Policy 当前帧再次送给 Worker 重复 Encode1。
- 终止短段：只消费实际成功 env.step 的 source steps，不虚构 future frame、zero action padding 或伪完整16；最后一段无下一 Replan 时只做 bounded End/quiescence，不多更新一次记忆。
- 第一 Replan source0 的模型路径与 No-TTT B1 相比必须保留原始输入、state15、action_horizon16、20Hz **数据语义（非 WallClock 承诺）**，Policy B1 实测无 intentional peer wait。

~~~text
             [Policy Server — 原有 current-frame Encode1]
 Replan0 image0 ──current pre-crop Visual96(0)─┐
       │                                    │ committed private boundary
       ├─ actions0..15                      │
       ▼                                    │
 [Sim env.step0 成功] → executed raw15(0) ─┤
       │                                    ▼
       └── Owner authenticates completed0+cached0 → Worker boundary_skip(0)
 [Sim env.step1..15 成功] → RGB(1..15)+action(1..15) → Worker T1 Encode
                                                       │ signed Visual96(1..15)
                                                       ▼
 Replan16 ── gather [boundary0, Worker1..15] → existing OnlineLocalMemory
                                                       │ prepare (FastState)
                                                       ▼
                           Native Policy generation + current pre-crop Visual96(16)
                                                       │
                                                       ▼
                           existing atomic Response + FastState + boundary commit
                                                       │
                    ACK / Abort / End per Session (not shared Worker kill)
~~~

上述顺序在每个 Session 内严格单调；在不同 Session 间无 time-step barrier；不能让当前 frame16 的结果倒流进 consumer16 的历史。

## 3. Stage1 Worker 的最小 sparse boundary 扩展（生产改动须专项 CPU Gate）

**现状**：Stage1 的 owner_issue / owner_complete / submit / consumed 四套前沿以连续整数递增；C 路线需要在0/16/32处有一个 Policy-owned boundary，但不产生 Worker Job。

**实施建议：新增 Owner-only boundary_advance / boundary_skip 原子操作，不改 Frame.from_wire schema、不改 HMAC，不把 source_step 1..15 改称0..14。** 仅在以下条件全部满足时允许：
1. lease/session/attempt/generation、issued policy request_key、Policy boundary cache RGB digest 和已执行 raw15 digest、实际成功 Step receipt 与 source_step **完全一致**；source_step 必须等于被跳过的真实 boundary，且 %16==0，禁止任意跳步；
2. Worker 当前 issued == completed == submitted == consumed == 此 source_step，之前 Job 已 ACK、没有本 Session 未 drain 的活动编码；本次事件 exact retry 幂等，bytes/sha/身份变化拒绝；
3. 同一次内部锁原子地把这四个前沿推进到 boundary+1，保存一个小型、bounded Policy-owned-boundary tombstone，明确标记 no Worker Feature / no VAE Encode，并保持原 Session capacity/generation/retire 规则；
4. 之后 owner_issue(start=boundary+1,count≤15，request_key=正在执行 Chunk) 可以合法签发；逐一真实 env.step 完成才 owner_complete 增加 frontier；Worker submit 的 header.source_step 保持真实值。
5. 非 Owner 只有自身 Session capability，永远不能调用 skip/issue/complete。Worker restart/late End/变更 digest/跨 epoch/missing step 直接 fail closed；不能因 skip 跳过一个未执行 action。
6. 不能将 owner boundary record 作为 HMAC-produced visual96；Policy 在本地校验边界缓存，只有其他15份 Worker Feature 走 Stage1 HMAC verifier。

实现时若发现 Worker 的四前沿锁与 Policy 原子事务难以在不增加跨进程等待死锁的前提下保持，可建议其他**同等最小**显式 skipped-boundary 状态机，但必须先写下具体不变量/回归用例接受审核。禁止“直接设置 source_start=1 然后把整个 Epoch 起点改掉”及 silent reindex。

## 4. Policy 私有缓存、验证和 Action Path

### 当前帧 boundary 捕获
- 添加一个 bounded per-Session boundary candidate，绑定完整 Lease、Policy request_key/chunk、真实 source_step、原始 RGB SHA256（Stage1 source_digest 相同域）、实际 Loaded Wan model/preprocess/visual96 digest、original Replan Deadline。
- **采样生成内部现成**的完整 pre-crop fp32 Latent 做 adaptive_avg_pool2d(1×2)→96D。不得从后续 cropped latent 或生成视频中近似恢复；不得二次调用 tokenizer.encode。
- 该缓存随既有 response/LocalMemory 快照事务同生同死。超时/失败/Abort/Actor End 不可发布、跨 Session 不可读；重复同身份字节请求只返回同一已提交结果和边界。缓存按最多正在生成+一个已提交边界的有界量保留，后续旧 boundary 按消费进度清理。
- 当前图片的 Policy 侧 RGB digest 必须匹配 Sim env.step 前复制的 RGB digest；不同编码器/预处理身份不相容就不注入局部特征。

### signed feature admission
- 只增加 opt-in 实验接口/证据格式（例如 profile=sim_shared_vae / local_feature_receipts），不改变 legacy server_vae 请求 schema / NoTTT NoWorker。
- 每个 Worker Receipt 运行 Stage1 verify_feature 严格校验 **当前 authoritative** Lease/Worker Epoch/KeyID/Loaded weights + config/profile、真实 source_step、源 RGB digest、raw15_sha256、chunk/request key、原始 Deadline/clock domain，以及 Owner completed evidence frontier。HMAC 是编码字节证明，不是 env.step 证明。
- 独立 Policy Evidence owner 校验顺序及完成性，合成 [N,96] float32 + [N,15] raw15 与连续 source_steps，生成既有 OnlineMemoryRequest；**不要把原16张 PNG 再传到 Policy 跑16次 Encode1**。避免在 Worker 入口重新 decode/re-encode 已验证的 Visual96。
- Full chunk N=16，其余使用真实完成 N≤16；旧 LocalMemory store 仍是单 Session candidate/atomic commit/abort/ack，不添加 parallel FastState 后台提交者。
- C 路线采用 T1 stream16 causal state update，或先以等价实验证明此批次的 T1 累加与原 T16 commit 等价。已有真实 iter15000 T16 vs T1 在另一 Gate 对固定输入 exact0 的证据可作为线索，**新接口仍需 CPU focused parity、同模型 Code Gate 后再真实验证**。
- Native batch executor 和原先严格媒体任务的公平性保持不变；证据未齐全时不得先进入可生成 Action 的 READY 队列。新 profile 的 Policy READY 起点是“历史 Feature 已验证且候选可执行/准备完成”，不能从 HTTP admission 起点或等未来某个 Sim 进入 batch 算；Worker B/W 与 Policy B/W 独立。
- 如 C 的 Worker 缺帧、证据失效或 Deadline 到期：明确错误 + Cancel/Abort，不准**暗中 fallback 到 B 后仍标 C**；评测操作者可显式选择重新启动独立 B 配置。

## 5. 真正 env.step 因果和信任边界（不得虚假证明）

- Stage2 的 Owner mock-complete 已经被明确限制为**性能测试**。Stage3 production-style C 必须移除 mock preauthorization，把 authority 置于真实授权 Actor 的 env.step 成功返回回调：在 action 执行前复制 pre-action RGB、将待执行 raw15 canonicalize；成功返回且命中对应 issued action chunk 时，才由可信 Run Owner 通知 Worker 完成 source frontier，携带单调 source_step 与 SHA。
- **不要把 global Owner token、Worker signing key、Worker control capability 交给 Sim**。若同一 UID 的不可信进程可读取 FDs/IPC/文件/进程内存，Stage1 HMAC **不能**神奇证明 env.step。Stage3A CPU 可以基于“Run Registry 管理的受控 Sim Actor 与 Owner 属于同一可信执行域”的明确威胁模型设计，必须注明边界及其限制；真实 Stage3 功能验收前需要 Owner 批准的受控运行信任假设或实际 OS 进程隔离/授权证明。
- Worker 只签署自己确实编码了、当前有效租约/模型/身份对应的输入，不可签署预执行图像并把它称为 completed。Signed Feature 与实际 Step receipt 必须同时存在，且必须由权威 Owner 对应于已提交 Action Chunk。
- Sim raw15 必须是真实送给 env12 前转换得到的 canonical executed raw15，不能从预期 Action、reward、媒体帧或未来 Observation 伪造。发生 env.step 异常时不得增加任何 completion frontier；不可重试环境动作来伪造新结果。

## 6. Worker 生命周期、EGL 与资源账本

- 新 Worker 为 **run-level Registry peer**（每个 Sim 物理 GPU 一份），不是单个 Sim 的后代，不能因该 Sim 结束 Episode 而误杀其他 Session。NoTTT A/legacy B **零**额外 Worker；C 单 Sim 仅一 Worker，不能要求有16 Sim 或多 Policy。
- Worker 仅加载/持有 Wan BF16；只它允许 CUDA_VISIBLE_DEVICES=assigned physical Sim GPU。Sim 子进程保持 CUDA_VISIBLE_DEVICES=''，并在该 Sim 的 env 内传 NVIDIA-only EGL ICD（上述具体 vendor JSON）；复用原有 configure/verify_current 与 PCI/UUID 物理证明。**不修改系统全局驱动配置、也不简单忽略 duplicate EGL device。**
- Worker 开启时 Root Registry 保存 PID/start-time/PGID、Worker Epoch、loaded checkpoint SHA/配置 SHA、显存与 IPC socket 的实际 owned inode、READY proof。API/control key 要经安全私有通道、不可在 argv/env/manifest/log 显示；不可使用跨 Run 常量 key。Stage1 现有 Unix socket demo 将密钥留于 Python 输入类中可作为本机 prototype，不等于产品级凭据交付。
- Close/Worker crash/timeout：先停止受影响 Session intake → Cancel/End → drain active VAE CUDA 或黏性 quarantine；Worker restart 必须轮换 epoch + signing key + Session，不得复活旧 receipt；Registry owner-only kill/reap 只处理实际 Owned group，非本 Run 和 GPU0–3 进程不能触碰。
- End 是 Session级；Worker run-close 只有在 **所有** Session End 和 Worker drain 后执行。Endpoint/进程崩溃若无法证明排空，Slot 不可继续复用或恢复。
- 资源表报告实际 one Worker model copy + Policy 自带 current VAE copy、GPU VRAM/RSS/Worker queue items+bytes；Stage2 16Sim 实测 GPU4 峰 19043MiB(Sim-only) vs 22602MiB(B8)，但新正式 Profile 必须重新测，不可硬编码成 admission 常量。

## 7. 原始 Deadline、耗时与对照 A/B/C

不可偷偷改变老 Session/Response 幂等和 M/B Resume，未来测量新 Profile 冻结一次原始 Replan 截止时间（**最后一个成功执行动作完成边界**，在 C 的 feature flush/wait/HTTP/TTT 之前）：
- 继承 Episode 原始 deadline；后续 IPC/HTTP/TTT/Policy/generation/ACK 只能取 min，不得在重试时延长；
- Worker 预先生成的历史 Frame 可以继承 Episode deadline，实际 Replan 开始后再收紧 Replan deadline，不倒签一个尚未开始的 Replan；
- 底层状态必须保留第一错误及 drain 异常，不能将超时吞成行为失败或默默切换 B。

**P0 Single：必须优先实现，不依赖大型 EvalV2 系统重构。**
- A Native NoTTT：冻结 checkpoint N / mode off；无 History Worker、无 TTT。
- B Native LocalTTT：冻结 checkpoint L / mode required；Policy 侧 16×独立 Encode1 + 官方 T16 scan。
- C **完全同 B 的 checkpoint L、sampler/dtype/action horizon16/raw15/state15**：Worker Bvae1/wait0，Policy Boundary1 + Worker 15，模型 Local T1 scan，Policy B1/wait0；无 peer等待。
- A↔B/C 不可把不同权重结果归因于 Local-TTT 机制本身；B↔C 才是同权重工程变化对照。Local checkpoint off 的 D 目前仍无合法实现，暂不做。
- 执行三组分开、资源独占且每组 seed/初始状态/task/instruction/max_steps 成对锁定；需要独立同 GPU vs split GPU 地形和是否额外 VAE copy 说明。
- Trace：第一 action/no-history；steady full16 Replan；partial-terminal；Sim step/EGL、拷贝/IPC、Worker READY/queue/encode、verify、TTT scan、Prefix、Policy current Encode1、Policy native prepare/queue/generate、response ACK/commit；P50/P95/P99/mean/CI、GPU显存。**后台和前台临界路径区分，不得简单求和重叠时段。**
- 先做 CPU gate，再独立 Owner GPU Gate 才能做实际 P0 small fixed-input smoke；随后18 underlying task×2 episode fixed-seed 仅验证有效性、不得声称 SR增益；更大例如18×50 的 paired SR需要另一个 Owner Gate。所有 planned invalid/error/unresolved 必须保留，不能静默当失败或丢弃。
- Stage0 freeze 的 18任务、matched种子与 initial_state、00/01/10/11 配对表、equal-task-weight SR + cluster bootstrap CI 继续作为真实 Stage3 后续分析合同。只许比较匹配的任务初始状态；后续闭环动作分叉后不可假称帧逐一相同。

**多 Sim Profile**（在 P0 的真实 Code+CPU/小型 GPU Gate后）：Sim GPU4/5 各16 Sim +各1 Worker，Policy GPU6/7 各1 Server (Bpolicy8)；Bvae∈{1,4,8}及 wait0/2/5 独立于 Bpolicy。Stage2 的 16Sim 共享 GPU4 性能证明不能代替正式 32Sim Policy SR/EP/h。前后对照只能选新鲜 matched baseline，绝不取未合并 PR4 或历史170.37EP/h当本轮对照。

## 8. Codex 实施批次（控制规模）

**P1（先提交，唯一立即授权实施）**：
1. Child：Worker sparse boundary Skip +精确 test；Policy pre-crop Visual96 private capture (不额外 Encode1) + staged signed-Feature admission，接到现有 OnlineMemory prepare/atomic commit/abort，不修改原 B 路径。
2. Child：Sim success callback/source-step digest、Bounded background Worker submit、End/epoch/trace、安全 key seam；Policy READY eligibility/zero peer wait 的必要最小校正。
3. Root：显式单 Worker run-level Registry role、NVIDIA-only Sim EGL env、CPU-only launcher/resource identity/profile opt-in，Single A/B/C config 校验与 trace。**不重写 EvalV2 Scheduler、媒体队列、Checkpoint/训练代码。**
4. 所有源变更在 Codex 自己的 **新隔离候选 Child branch + Root candidate branch**（父代 Root3ab Child0a）下提交 Draft PR；提交完整两仓 formal Pair SHA、diff、focused CPU/JUnit/ruff/源指纹与 zero GPU provenance，等待 GPT 独立 Code Gate。不可直接修改当前 PR6 的既有 HEAD/官方 V3。
5. 正式交接请把申请写入 Root docs/collab/codex/reviews/ 和 docs/collab/chatgpt/CODEX_INBOX.md append-only；**由 GPT 独立审查**，未经 Gate 不得启动真实 GPU/Policy/RoboCasa。

**P2（仅设计，待 P1 Code Gate）**：在新授权真实硬件下跑 A/B/C P0；先 P0 日志与 CPU/小规模 Gate，再18×2 smoke 和独立大规模 SR；有 blocker 则单点修复重新审同一变更范围。**不自动启动**。

**P3（仅设计）**：B4/B8 opt-in 行为差异门禁；先对完整真实 post-step evidence 路径 B1 vs B8 的 Action 差异定阈值/新 holdout，再经授权做 matched closed-loop，不能以人眼重建质量代替 SR；通过后另发独立功能验收申请才准作正式 C-B8 候选。Worker B8可用于继续独立性能研究，但仍保持生产 feature admission disabled。

## 9. Stage3A 必须有的 CPU Gate（Codex 冻结新的 test/evidence）

1. **Sparse真实序号**：0→1..15→16→17..31，重复 boundary幂等；skip任意1/15/32不匹配、缺失动作、source step倒退、跨 Session/epoch、late End、证据变更拒绝，Worker 1..15而非0..14；四frontiers一致不留 ghost jobs。
2. **Policy Boundary**：真正原始 current Encode1 在完整 pre-crop latent 生成 Visual96；cache identity+SHA，严格只编码一次；显式证明抽取结果与官方单次 Encode1 Visual96逐元素一致，后crop feature不能冒充；失败/Abort/End不发布。
3. **15+1 LocalMM**：16个真实 source steps+raw15，Feature Schema/HMAC/文件实际loaded identity/clock/Deadline严格验证；输出 [1,16,96]+[1,16,15]，保持原 OnlineLocalMemory.prepare/commit/abort；T16 vs 16×T1 真实 model-owned graph等价在允许 Gate 范围内单独测；掉一个步骤不得生成 Action。
4. **真实执行证据**：mock Sim Step success/fail，只有真实成功 callback 推进；未经授权 Actor/Owner 的伪成功、chunk换名、PNG中字节变化、pre-action RGB错配拒绝；若复用同 UID threat model，trace明确 same-trust boundary而不是声称强安全。
5. **事务**：Native B1/B8 policy batch（实验全多时）原始请求幂等及 Local response回放；同一个 FastState candidate只有一次 commit；Abort不更改公开快照；ACK/End恢复/Worker死机不导致已撤销 feature再使用。
6. **生命周期**：两 Sim Sessions 共享 Worker，一个 End另一个继续；Worker是Root Registry peer，取消/重启/超时/close不误杀外部；CPU模拟无法证实 CUDA drain 则 sticky quarantine。
7. **原始 Deadline**：包含 frame capture/feature wait/TTT/generation/ACK；复用同一 absolute monotonic ns，重试不续期，超时失败与第一错误不可吞。
8. **Off/B 原样**：A NoTTT Worker进程数=0、历史Encode1=0；B旧 LocalTTT仍16 Encode1和T16，保持 raw15/state15，M/B Resume严格验证不变。
9. **吞吐/调度**：Worker B1/wait0且Policy B1无peer等待；不同源步Session可组成 B8；Policy只对 history READY case入 native Bbatch，不能把未准备数据塞进 batch而重现 PR4 B1 collapse。
10. CPU Gate 证据中所有 tests 0 failure/error/skip，包含真正起停隔离子进程及源指纹 before==after、Root/Child SHA与Gitlink严格匹配；代码检查独立，作者提供的是申请不是 Verdict。

### Stop 条件（不得自作主张扩大范围）

任何假因果 frontier、错位序号、额外边界 Encode1、错误 HMAC/epoch、未排空却 reused Slot、Local candidate 部分提交、超时刷新、off/b 退化、未冻结 Checkpoint N/L、GPU身份不清，均 **REQUEST_CHANGES / NOT RUN**。Codex不得将已有 Stage2 owner B8 视觉通过重新标记为数值/行为等价通过。

**最终交付目标**是新 Draft PR 与 exact formal implementation Root/Child SHA + 可以复验的 CPU evidence，而不是立刻启动训练或900EP。
