# Codex / Evaluation V2 r2 — 最新统一 Owner Contract（D1–D5）

**更新：2026-10-28。请 Codex 在开始 r2 设计与 CPU 原型整改前，先读本文件全文并回复已读取的版本、取代关系和整改范围。本文件是最新需求的唯一汇总入口；早期讨论与 Review 保留证据/来源，但与本文冲突时以本文为准。**

## 0. 当前分支、Formal Pair、权限

- 项目：`wxwy/psm_wma`，当前审计主分支 `V3`。
- **上一轮唯一被审核的 Design + isolated Prototype Formal Pair**：Root `dc750f8e258d10a33e7a195cf907926b1c98bd7f` / Child+Gitlink `746c5cf2f2324104a62fb71510343aa40d3976c5`。
- 候选分支 `v3-eval-v2-design-20261028`；作者 Evidence/Handoff HEAD `23f2d3a1fda08b9c8214c22b12fbb0592c578dcd` **不是**新设计 formal pair。
- GPT 对上述 r1 的正式设计判定为 **`REQUEST_CHANGES`**。作者 CPU 65 passed 属**隔离合成原型**，900条为合成记录，绝非900真实 Episode。其余增量 Owner 决定仅补充 r2 验收要求，不是对 r1 重新审核，不升级其 verdict。
- **当前只要求 r2 设计文档 + 隔离 CPU 原型整改 + 证据 + 新 Formal Root/Child pair 提交审核，提交后 STOP。** 未授权：合并候选到 V3、修改训练、真实 GPU / DCP / Simulator / Canary / 900 Test、删除或迁移历史431集结果。生产入口还没接线。
- 请 Codex **从远端 `origin/V3` 读取本文和 `docs/collab/chatgpt/CODEX_INBOX.md` 最新记录**，不要只根据旧候选分支本地快照实施。此文件为设计需求，不是直接启动 Codex Agent 任务的命令。

## 1. 冻结的总体实验和 SR 口径

1. **从全新独立 Run Namespace 开始**，目标18 Task×50逻辑 Episode=900；旧431集全部不参与，暂不触碰旧文件。输出研究人员可直接读取的 `tasks/<Task>/episodes/ep_NNN/` 核心文件、`summary.json`、`episodes.jsonl`；日志、恢复状态、异常/Attempt 记录分开放入 `_internal`，原始媒体不默认生成两份。
2. **Core SR 唯一正判据**为 RoboCasa 的 `env._check_success()`，在真正完成动作 `env.step()` 后按原 `success_latch=1` 判断；正常执行到官方 Horizon 没成功是有效 `behavioral_failure`，必须计入分母。不能用 reward、`env_done`、视频、生成结果代替环境成功判定。
3. **Core Invalid / Interrupted**（仿真或模型错误、成功谓词异常、必要 Local Session 清理失败、核心证据未成功提交）与 `behavioral_failure` 区分；不得把 Invalid 当失败分母，也不得从正式计划中静默删除。
4. **媒体完全独立（已选 C）**：Rollout MP4 / Generated MP4 / PNG 只作诊断。可继续保存一份，但缺失、损坏、编码或解码失败都不改变已获得的环境成功/行为失败，也不引发重测。禁止在任务完成、source revalidation、最终汇总或 Resume 的 SR 关键路径上自动启动 ffmpeg 严格完整解码；不默认自动复制 `videos_view`。如果视频保存故障阻断动作循环或覆盖有效 Core Outcome，属于未修复生产设计；保留独立媒体错误诊断和有界后台资源，不无限阻塞 Local Cleanup。
5. Core Action / Prediction / Local-TTT chronology、raw15→env12、Checkpoint、模型、任务环境及物理评测判据不因本改造而改动。严格的输入身份、进程所有权/清理、单 Run Lease、原子 Core Result Commit 必须保留。

## 2. D1 — HIGH：Process Fault 生命周期与 Clean Qualification

旧 r1 原型将历史 `process_errors` 永久污染 `results_qualified`。r2 必须给出可执行的**按当前实际 Episode Attempt/Stream/Worker Task 作用域的错误状态与解决机制**：

- 错误原件不可变保存，包含阶段、归属、当前 Attempt/Stream、进程、时序和失败原因。
- 对正常清理后合法完成的新 Retry Attempt：旧 Attempt 的可解决错误不永久阻碍新 900 集 Clean Qualification；所有解决状态有可追溯判据，不能删旧日志或靠刷新 summary 静默清错。
- **当前未解决的错误**及最后一个 Episode Result Commit 后出现的关键进程异常须保持可见，并阻止 clean-qualified，环境成功值本身不因进程错误而被倒写为失败。明确 safe-stop 与可安全再起条件。
- 覆盖旧错误后新有效 Retry、当前错误、结果提交后进程退出故障、多 Task 互不污染等合成测试。

## 3. D2 — MEDIUM：Task / Episode 初始化必须 Crash-Safe

- 旧 r1 `task_state` 先发布、`episodes/` 后创建有 Crash Gap。设计可恢复的原子 claim/init 事务；在能证明从未完成任何有效 Episode 时可安全补完初始化；不确定/冲突数据 fail-closed，不删除历史。
- Episode Attempt 初始状态与结果 Commit 同样要防 crash、重复写入、不同 Worker/Attempt 抢写、异步后到结果写入错误逻辑索引。
- 测试各事务边界（before/after state, directory, result commit, coordinator crash）与有效其他 Task/已完成 Episode 文件字节完整性。

## 4. D3 — HIGH：Episode-Level Resume，原场景**不需要**复现（最新 Owner）

- **Owner 明确**：“Episode 37 中断，就应该从 Episode 37 重新测”，“如何保证 Episode37 的场景采样可复现？**不用复现**。”
- `ep_000..ep_036` 已成功原子 Core Commit 的正常成功/行为失败**不得重跑、改写或删除**；`ep_037` 未有效完成则从该逻辑索引重新采样合法场景继续；之后 `ep_038..ep_049` 依序测试。最终每个 Task Index 只有一个有效 Core Outcome，900个位置不重复、不越界。
- 不需要精确恢复原 Scene、MuJoCo RNG、Policy RNG Snapshot，不需要前36集重放，也**不要求全900集用每 Episode 固定 SHA256 Seed、每 Episode 新建 Env**。正常未中断 Task 可在同一环境下按 Seed 连续 Reset；Resume 新 Stream 采样合法场景并照实记录实际 Seed、Stream/Attempt/Resume 边界。**不得谎称恢复尾段与原 RNG 流逐场景相同或全 Task始终是一个连续 Reset 流**。
- 一个有效 `behavioral_failure` 永不自动重试或“换场景直到成功”。仅 Pending / Invalid / Interrupted / 特别授权补测的 Skipped 可以重新执行；媒体失效不能触发重测。
- 被跳过的 `ep_037` 不得阻止 `ep_038..049` 的原子提交，存储层必须支持**中间未完成槽位 + 后续有效槽位**，按逻辑 Index 合并输出。旧 r1 只允许连续结果前缀的 `Store.rows()` 规则需修改。

## 5. D4 — HIGH：Reset 已成功的退化场景 + 初始化异常四连跳过

在 `env.reset()` 后、**任何模型推理、动作与 Local-TTT Episode begin 之前**，用严格的初始 `env._check_success()`（或同等任务成功谓词）作为 **scene-admission precheck**。此检查仅决定场景是否有效，**不替代执行动作后的环境成功判据**：

- `False`：接纳当前场景，执行正常 Episode；此后 success/failure 根据动作后的 `_check_success()`，不基于“容易/困难”筛选。
- `True`：记录 `DEGENERATE_INITIAL_SUCCESS`（旧 NavigateKitchen 报告 seed695376856，reset后已满足目标），**不占用一个有效 Episode、不查询模型、不执行动作、不更新 Local**，有上限地继续新 Reset 重采。退化场景不是初始化错误，单独统计拒绝率，记录实际 Seed/Stream；整体 admission 次数必须有明确上限，耗尽时 `SCENE_ADMISSION_EXHAUSTED` 作为待处理缺口而非 Success/Failure。此过滤版本化进新900协议；不可宣称与历史未过滤 SR 同口径。
- `env.reset()` / initial-success precheck **异常或返回非法类型**：独立记录每次的异常阶段、类型、时间、当前 Index、Seed/Stream、采样序号；若环境可安全恢复，重新 Reset 或重建环境。Owner 原话：“一个 Episode 初始化错误次数**连续超过3次**就跳过这个 Episode，记录、报告，让我决策是否 Resume。”即**第4次连续错误**后 `SKIPPED_INIT_ERROR`，停止此 Index，**继续后续 Episode（仅在安全恢复后）**。成功完成一次 reset+合法 precheck（即便该场景初始已成功随后被拒）会打断连续错误计数。退化场景总次数和初始化异常连续次数必须分别计数，不能用一个计数器混合。
- 一个 `SKIPPED_INIT_ERROR` 是未完成的逻辑 Index：**不得计 Success/Failure，也不得自动 Resume**；在 Task 结果和最终 summary 列出明确 IDs、四次错误和诊断，待 Owner 看报告单独批准补测缺失位置。只要存在跳过/Invalid/Pending，正式全900 SR 不发布（`sr=null`）；可另行提供明确标注分母的 `partial_sr_valid_only`。
- 原生进程崩溃、清理异常、EGL 上下文失控或硬件不可安全恢复故障不允许简单伪装成普通可重试 reset Exception；必须安全停机并记录 Process Error。失败4次只触发可恢复初始化的单 Episode Skip，不意味着忽略真正资源损坏。
- CPU 必须覆盖 3次报错后成功、4次连续错误 SKIP 并继续 ep38..49、合法 precheck 打断连续错误、初始已完成场景反复重采直到上限、初始化期间 Crash/重试 Ledger 重启复核、正常行为失败不重试、Skip 时正式 SR=null、经 Owner 单独批准后仅补测缺口且之前已完成其他 Index 的内容不变。

## 6. D5 — HIGH：Episode-major Round-Robin 调度 + Resume 已测槽位跳过（最新 Owner）

- **Owner 要求的全局调度顺序**：冻结18 Task的稳定任务序号；外层 `episode_index=0..49`，内层 `task_order_index=0..17`，即 `Task1/Ep1 → Task2/Ep1 → … → Task18/Ep1 → Task1/Ep2 → … → Task18/Ep50`，总共900个逻辑槽位。**原V3按Task运行50集的Task-major FIFO不是此要求**，V2 r1设计/原型亦尚未落实D5。
- **轮次屏障**：在Round k 的全部18个Task槽位有明确处理结果之前，不能向任意GPU派发Round k+1。GPU4/5/6可并行执行同一轮不同Task，Task按冻结顺序**派发**，实际完成时间不要求依序；若需要取消全局执行，持久记录当前轮状态，下一次Resume再从相同排序扫描。
- **Resume从头按同一逻辑顺序扫描、对每槽位判断**：只有经过原子提交、核验身份的有效Core Result（`success` 或正常 `behavioral_failure`）算“已经测试过”，**必须直接跳过且绝不重复推理、仿真、改写原结果**。未提交的`PENDING/INTERRUPTED/INVALID` 按安全条件安排同一逻辑Episode重试；不能靠MP4、目录、`RUNNING`标签或Convenience Summary推断已完成。
- **跳过但未完成**：`SKIPPED_INIT_ERROR`（初始化连续4次异常）与有界退化场景耗尽的Owner-Pending缺口，普通Resume也要跳过并列入报告，**仅在Owner明确指定后才补测**。这类跳过不占合法Episode成功/失败，不构成正式SR完整覆盖；不阻止其他Task和后续轮次正常测试。
- **中间缺口与重复执行保护**：Task3的Ep1若已完成，无论Task1的Ep2是否已完成都按冻结排序扫描并跳过；TaskX的Ep37被Skip以后，已经提交的Ep38不能再测试。存储层支持非连续合法索引和并发多GPU的原子Slot Claim / stale-worker拒绝。
- **同一Task运行流与资源**：D5禁止默默继续Task-major50集Batch来“优化效率”。3GPU×18Task不一定能长期同时保有18个Env和Server；Codex必须在r2设计中解释资源有界的Round调度、模型Server复用与Local-TTT Session隔离、EGL Context寿命、跨轮Task Scene RNG/Seed与实际Stream记录，避免朴素的每Episode一次加载13GB模型或900次不必要EGL重建。Owner已明确**Resume无需重现原Scene**，也不强制为900集创建固定Per-Episode Seed；但如果新轮次使Task的Env/Seed序列不连续，报告不能宣称仍是旧的一Task50次连续Reset流，且Benchmark与此前Task-major采样协议的可比性须标注。
- **CPU设计验收**：900槽位排序Exact；3个异步Worker的Round barrier；在任意轮次/任意slot中断，Resume扫描跳过前后所有已合法完成槽位，只有缺口执行；已完成Behavioral Failure不得重试；Task1/ep37 `SKIPPED_INIT_ERROR`而ep38有效时，普通Resume仅跳过ep37且不重测ep38；第4次初始化错误不能悄然算Success；双GPU抢同一逻辑Slot拒绝；取消/进程故障与Core Commit原子性。
- **完整原始决策与测试基准**：`docs/collab/chatgpt/reviews/2026-10-28_V3_EvalV2_D5_Owner_Episode_Major_RoundRobin_Resume_Skip.md`。这条是新Owner约束，与D1–D4同等必须整改，不改变此前r1 formal pair的`REQUEST_CHANGES`。

## 7. 当前未授权及交付要求

1. Codex 在隔离候选分支修改 **r2 Design / isolated CPU Prototype only**，按 D1–D5 更新 Acceptance Matrix；不能因上一轮65个 CPU PASS 就绕过新 D3/D4。新提交标出**新的 Formal Design Root SHA / Child Gitlink SHA**、与 r1 `dc750f8e` 的真实 diff、Ruff、JUnit/Test，测试脚本和冻结 Evidence；然后 **STOP for GPT incremental review**。
2. 真实生产接线、DS_PRO 独立 CPU、真实 RoboCasa Canary、900集正式测试、合并 V3 均需后续独立授权。任何模型/训练/Vendor/历史431无权改动。
3. 请 Codex 回写交接记录明确 **已读取本文件**、标识 D1/D2/D3/D4/D5 与以上 superseded decisions，避免从本地旧分支设计继续按已经废弃的 Task-level restart 或 fixed Scene Seed 开发。

## 8. 旧文档取代关系（请勿误读）

下列旧版本 Review / Owner 补充仍保留可追溯记录，但**以此文的最新要求为准**：

- r1 正式审核 `docs/collab/chatgpt/reviews/2026-10-28_V3_RoboCasa_EvalV2_r1_dc750f8e_746c5cf2_design_review.md`：D1/D2仍存在；其中 **认可整 Task 重跑的部分已撤销**。
- `docs/collab/chatgpt/reviews/2026-10-28_V3_EvalV2_Owner_Override_Episode_Level_Resume.md`：**Episode37-only Resume 保留**，但其中 §2要求原场景复现/固定Per-Episode Scene Seed **已撤销**。
- `docs/collab/chatgpt/reviews/2026-10-28_V3_EvalV2_Owner_Clarification_No_Scene_Reproduction.md`：无需场景精确复现，仍有效。
- `docs/collab/chatgpt/reviews/2026-10-28_V3_EvalV2_NavigateKitchen_Reset_Already_Success_Evidence_Design_Addendum.md`：reset初始即成功的退化场景过滤仍有效。
- `docs/collab/chatgpt/reviews/2026-10-28_V3_EvalV2_D4_Owner_Init_Error_4_Strikes_Skip_Report.md`：**第4次连续初始化错误跳过**、报告Owner、不自动补测；这是最新D4异常处理，优先于早期泛化的fail-closed初始化描述。

- `docs/collab/chatgpt/reviews/2026-10-28_V3_EvalV2_D5_Owner_Episode_Major_RoundRobin_Resume_Skip.md`：全局 Episode-major Round-Robin + Resume 基于有效 Core 提交的跳过，普通 Resume 不补 Owner-skipped。
