# Codex 请求：V3 RoboCasa 评测 Resume 简化为当前计划 + Episode 级复用（Owner 2026-10-23 定稿）

类型：Owner 需求契约 / 待 Codex 设计实现与 CPU 测试，非审核 verdict。
范围：Root RoboCasa 评测调度、结果聚合、Resume、CLI 与测试；必要时 Child 评测证据/episode 索引极小接线。
约束：只由 Codex 编码；GPT 独立审核；DS_PRO 只执行独立证据；Owner 亲自启动 GPU。不得修改当前运行的18任务评测工作树、模型、Local-TTT、action path 或 Vendor，不得自动启动 GPU。

## 0. 核心决定

**Resume 的严格不变模型参数只有四项**：
1. `checkpoint`：同一个实际 DCP（路径及已有模型权重元数据；同路径被替换不算相同）。
2. `num_steps`：去噪采样步数。
3. `action_horizon`：每轮预测16个动作后实际执行的长度 R。
4. `guidance`：采样引导强度。

这四项只要任一不同：**在调度、写新 attempt、加载模型之前明确报错停止**；不可「自动开新实验」并在同名输出目录混写，不接受降级为 warning。报错要指出 old/new 值。

**其余当前任务计划参数以本次命令为准**：tasks、episodes_per_task、seed。禁止把它们放入硬 Resume 相等检查。允许增加/减少任务、增加/减少 Episode 数、改变 seed。

**媒体选项可变更**：`save_rollout_mp4`、`save_generated_video`（none/first/all）、`save_init_png`。新要求高于历史保存范围时，不重跑旧 Episode、不自动生成不存在的历史视频；对当前新执行的 Episode 才生效。缺失媒体必须明确标注，不得虚报完整覆盖。

## 1. 当前计划与完成数的精确定义

- 本次请求的 `tasks` 是本次统计与调度的任务集合；之前完成但未在本次选择的任务保留原文件，不计入本次汇总。
- 对每个当前任务，用完整可验证的 **Episode** 作为最小复用单位；这取代目前以整个Task COMPLETE判定复用的逻辑。
- `completed` 包含 `success` 与正常跑到 horizon 的 `behavioral_failure`；不包含 runtime_error、运行中被打断、缺失必要 actions/predictions evidence/Local-TTT cleanup 的 Episode。禁止以目录、视频数、`event=start` 代替证据。
- 计数规则：`reuse_count=min(requested_episodes, verified_completed_episodes)`，`new_count=requested_episodes-reuse_count`。历史多余 Episode **原位保留，不计入当前 SR 分子分母**；完成顺序/优先级必须确定性，且避免把不同 attempts 的重复索引双计。
- `requested=5, old_completed=3`：复用3，补2（逻辑 episode index 3、4），不从旧第0集重复。未完成的当集必须作为新 attempt 重跑，不复用半成品。
- `requested=5, old_completed=8`：不再运行，当前 summary 只包含所选择的5集，打印 old=8, requested=5, reused=5, excluded=3；文件不删除、不覆盖、不改名。
- `tasks` 从4扩展到18：旧4按 Episode 复用，只补新任务的 Episode。缩小则新 summary 排除非选任务。
- 同一 task 存在多个旧 attempt 时，按明确/稳定的规则挑选已验证 Episode；出现冲突/重复不得静默双计或覆盖，需在诊断中解释。
- 继续运行新 Episode 必须保障场景抽样/episode index 可追踪：不能因为新 simulator 进程从同一 seed 重新初始化，悄悄把前几集场景再次作为第N集。实现应记录有效 episode seed/reset 轨迹，并给出真实 CPU/可控 fake-env 覆盖；无法恢复历史随机流时明确标记其限制与本次新增采样语义，不能伪称同一次不间断 rollout 的第N集。

## 2. Seed 灵活但保证实际来源真实

- `--seed` 只决定**本次新执行**的 Episode。已完成 Episode 不因 seed 更改而重跑，原 seed 不可追溯性篡改。
- 若 old seed=0 已有5集、新 `--seed 1 --episodes 8`：旧5集保留 seed0、新3集按 seed1 执行，输出 `MIXED_SEED` 标志与逐集 `effective_seed`，汇总可作便捷统计但不得标注为纯 seed1 的官方可比较 SR。
- 若 old seed=0 已有8集、新 `--seed 1 --episodes 5`：全复用、0新执行；必须醒目打印“本次未在seed1下执行任何Episode，结果全部来自历史seed0”，不能冒称 seed1 评测完成。
- `--seed` 值与 `effective_seed`、执行计划、实际已复用引用须写入每次 invocation 的只增记录和任务/Episode 来源索引。
- 模型端 policy seed 当前固定为0，勿将环境seed误当作用户要求控制的四项模型参数。

## 3. 媒体保存策略不作为复用阻断条件

- 历史 Episode 没有视频但有可验证的**核心 Episode 证据**时，允许复用。新 `--save-generated-video all` 不得迫使旧 `first/none` Episode 重跑；也不能伪造此前没保存的 replan MP4。
- 对历史**真实存在且历史要求保存**的媒体，保持原有文件完整性检查；腐败/不可信证据与“新策略要求额外媒体但旧时未录制”必须区分。
- `video_coverage` 按每 Episode 给出：`available_rollout`、`available_generated`、`expected_generated_per_original_policy`、`requested_policy`、`missing_requested_media` 等；`videos_view` 只展示实际存在的文件。
- 新 Episode 按当前视频策略写出；保留旧 Attempt 的媒体命名、生成manifest、证据哈希、动作/预测 JSONL 与关联，禁止就地重命名和补写历史。
- 切换视频策略不能影响模型推理、Local-TTT、成功判定和动作队列。

## 4. 运行参数放宽与自动安全

- GPU 列表/数量、base port、worker 调度、日志/进度间隔、超时允许在同输出目录 Resume 时改变；在本次 invocation 中记录，**不要因为这些执行设置变化拒绝复用**。
- Root/Child 的纯文档、测试、输出进度代码变化不应把已有 Episode 全部失效。保留 provenance；若执行行为/物理环境发生变化必须在汇总里给出明显混合条件警告，不得冒充单一固定协议 benchmark。
- 仍拒绝损坏模型权重、无法验证的历史证据、非法路径、并发写同目录、ABI 不兼容或运行安全基础条件失败；这是最小安全/完整性约束，不得转化成大量额外参数等价要求。
- 若同目录属于旧 `evaluation_manifest.json` 严格格式，必须提供明确且**非破坏性的 legacy ingest/migration 方案**，复用其中合法完成的 Episode；不要直接覆盖/改写旧 digest 对应的历史证据，把它们误包装为新 digest。
- 设计应拆分稳定的 `model_identity` 四参数与 `invocation_plan`（tasks/episodes/seed/媒体/执行配置）；Episode 自带原始 Attempt、原始 runtime / source / seed / save-policy provenance。旧证据仍由其原始 identity 进行校验，新增跨 invocation 的汇总是视图而非改写。
- 显式 `--resume` 仍需保留；同名目录不指定 `--resume` 不得默认覆盖旧数据；已有 `.run.lock` 互斥机制保持。

## 5. 启动、结束、日志三处必须报告变化和复用

- **启动时**：终端和 `_invocations/<id>/resume_plan.json` 展示模型四参相等检查、当前 tasks 数和具体任务名、requested seed/episodes、每Task old_verified/reuse/new/excluded、seed混合警告、媒体缺失覆盖预估、GPU映射/端口/当前视频策略。
- **运行时**：保留/改进 Worker、task、episode、action step、replan、预测延迟进度；至少在每个 Episode 开始/结束记录 `reused` 或 `executed`，日志明确原路径/attempt。
- **结束时**：终端和 `_invocations/<id>/resume_report.json`、`screening_summary.json`（或 versioned view）写入本次 requested/reused/executed/excluded/failed、逐任务/全局 SR **仅按当前选中的 Episode 计算**、混合 Seed / 混合环境标识、历史媒体缺失数量和覆盖率。
- 示例：`CloseFridge requested=5 previous_completed=8 reused=5 executed=0 excluded=3`；`NavigateKitchen requested=8 previous_completed=3 reused=3 executed=5`。
- 发生异常时不能伪报 COMPLETE；明确本次请求尚差几个 Episode，保留所有历史文件与新增中间证据。
- 任何 `MIXED_SEED` 或 `MIXED_RUNTIME` 指标必须显式标识“便利性合并，不是同条件 benchmark”。

## 6. 验收测试与执行边界

Codex 必须补 CPU fake-env / fake-server / fault-injection tests，至少覆盖：
1. 四参数各单独变更：启动前 fail，无新 attempt/无更改历史。
2. tasks 增/减、episodes 3→5、8→5、5→5：当前汇总分子分母正确；过量保留不计入。
3. seed 0→1：旧值不改、新 Episode 使用新值；全复用时显示“未跑seed1”；混合标识和来源一致。
4. 媒体 none→all、first→all、all→none：已完成 Episode 不重跑，新 Episode 采用新策略；历史缺失明确报出；现有实际媒体破损处理可靠。
5. Task 旧 attempt 2/5 完成、第三集中断、task RUNNING/FAILED：前2有效复用，补齐3–5，不借用部分 Episode；Local-TTT cleanup 证据、progress 和 Attempt identity 不串线。
6. 两次 Resume 任务重排/不同 GPU、端口、timeout：不因非行为参数变化被拒绝；并发 writer 仍拒绝。
7. 旧版 run directory 迁移：历史不改写，验证原始身份后可复用 Episode；旧结果损坏/来源歧义必须有明确错误/警告，不跨 Attempt 伪造。
8. 真实生成统计与视图：SUCCESS/behavioral_failure counted, runtime_error excluded, extra episodes excluded; summary PARTIAL/COMPLETE 正确。
9. Episode RNG：重启后的新增 Episode 不得无提示重复已完成的首批场景；如无法严格证明则在设计中说明可实现替代方案与 provenance。
10. Fail-closed 资源与安全契约：互斥锁、外部进程不可清理、JSONL证据、Local-TTT required 不回归。

建议两步交付：先**设计/迁移方案冻结和假数据 CPU Gate**，再最小实施与独立 DS CPU 验收；GPU 真机验证须 Owner 单独执行。不要趁机修改训练或模型语义。

## 7. 当前源码限制（请求来源）

旧 `scripts/v3_evaluation_identity.py:claim_evaluation_run` 与 `scripts/eval_robocasa_18task_queue.py:check_destination` 比较整份 manifest；旧 `execute` 只选择完整 Task 完成的 attempt；旧 `scripts/robocasa_eval_results.py:validate_attempt` 将视频策略绑定媒体验证。需设计身份/复用/新汇总路径，而不是简单注释掉这些比较。
