# V3 RoboCasa Flexible Episode Resume — DS_PRO CPU Retry 1 独立 Evidence 审核

日期：2026-10-24（CST）。
**Evidence Gate verdict：`REQUEST_CHANGES` — EVIDENCE-ONLY，维持 RED。**
**原 GPT Implementation Code Gate `APPROVE` 保持有效，formal pair 未变，不重做技术代码审核。**

## 1. Formal identity / Evidence 可及性

- Implementation Root：`6151e0712f28ace5d92258a8feb31fa8f1ee81c1`
- Child/Gitlink：`813a550dab5d6b5b5e3be90d38bb97527956b4dc`
- Frozen Owner contract：`cc7820bee1a73bd2bb2078cb7f00239944f66d37`
- 上轮 GPT Implementation Gate：`docs/collab/chatgpt/reviews/2026-10-24_V3_flexible_episode_resume_progress_r2_6151e071_813a550d_review.md`，`APPROVE`（仅代码/Evidence source review）。
- 上轮 DS Evidence RED：`docs/collab/chatgpt/reviews/2026-10-24_V3_flexible_resume_6151e071_813a550d_DS_CPU_evidence_RED_review.md`。
- 远端 V3 在取证时仍是 docs/review commit `6ed346460efdee17e60732685fba240e902175d2`，不是新的 implementation SHA。
- 本轮新增依据为 DS_PRO 提供的 `retry1_20261024_050347` 摘要，来源为原服务器 `/mnt/data1/data_v2_0617/psm_wma_ds_cpu_6151e071_813a550d/retry/retry1_20261024_050347/`。DS 表示存有 `pytest.log`、`ps.log`、`load.log`、`cgroup.log` 和 19份子进程 `console.log`。**本次 GPT 无法直接读取服务器原件：Remote Desktop Commander 设备离线，日志未作为会话文件或 GitHub blob 提供**。因此以下运行观察明确归属 DS 报告，未将描述冒充 GPT 逐字核对的 raw Evidence。
- 实际独立检查了精确 SHA 的生产测试源码 `tools/v3/eval_robocasa_queue_identity_test.py`，以及此前作者冻结 JUnit 的参考耗时；不重复已批准的 unchanged production semantics 审查。

## 2. Retry 1 运行事实（DS 报告）

- 未改 Root/Child/正式测试；6个失败方法覆盖原9个失败节点，`6 failed, 5 passed, 37 deselected, 12 subtests passed`，1219.79s。
- 复现：`normal workers=8`、`progress_resume`、`resume_missing_progress`、`resume_wrong_attempt`、`resume_failed_cleanup`，共5个90s超时；以及 `task_timeout` 的 `task_failures=4` vs expected1。
- 转绿：`resume_wrong_video`、`resume_wrong_timeout`、`resume_complete` 共3个原失败节点。
- **指定的低干扰条件没有满足**：仍有G1训练、他人训练及其它媒体探针进程。loadavg近30–48，均值约39/192核；`cpu.stat nr_throttled=0` 仅排除了所观察 cgroup 的配额节流，不能排除调度竞争、affinity或I/O竞争；本次使用 `nice -n 10`，会降低进程调度优先级。
- 据DS保留日志：`progress_resume` 第一阶段 COMPLETE、第二阶段全复用计划已打印；停止时存在4个运行中的FFmpeg媒体审计进程，父进程等待子进程。`workers=8` 4 Task 完成而媒体验证/后续收尾尚未结束；3个坏旧证据 Resume 场景再次在完成新 Task 后卡在最终重验。对仍活动的 `--serve`，需以 PPID/PGID、来源 invocation 和进程生存期确认归属，**不能仅凭出现就推断泄漏或无泄漏**。

## 3. 独立因果评估

`tools/v3/eval_robocasa_queue_identity_test.py:40-60,1161-1193` 固定普通场景 watchdog为**90s**，超时杀整进程组并因 `TemporaryDirectory` 清理而丢失未外部保存的原console。真实媒体解码通过 `subprocess.Popen` 走 FFmpeg 核验边界（`:557-561`），正常场景包含多段真实 MP4审计（`:522-526,720-748`），且完整 Task 的 COMPLETE/Resume 重扫都可能验证媒体。`task_timeout` 在 `:853-857` 将**同一个5s任务墙钟预算**施加于故障Task及3个健康Task，`:1443-1468` 又要求只有故障Task失败。

因此，本轮**媒体验证耗时跨越测试预算**这一解释已有合理的阶段证据和三个原失败节点转绿的支持，不能再把所有90s失败简单视为无因果线索的“神秘死锁”。但运行态子进程截图无法证明解码逐帧向前推进，也没有得到低干扰对照组或未经更改预算的完整独立绿色断言。特别是“90s整点超时”只证明 watchdog 截止，不证明纯环境问题；`loadavg=39/192` 与 `nr_throttled=0` 均不能独立证明CPU饥饿。**没有生产逻辑缺陷的确证，也没有足够证据排除所有生产死等可能**。

## 4. Blocker tracking

- **HIGH-E01 — OPEN（诊断改善、行为验收仍缺）**：5个媒体密集场景在原90s固定 watchdog下仍不能给出COMPLETE/source/cleanup/assertion正向独立见证。日志已指向媒体审计阶段，不再缺“最后阶段”线索，但尚缺对应业务行为的独立PASS。
- **MEDIUM-E02 — OPEN（fixture预算敏感性强）**：5s的Task-wide wall限制导致 `task_failures=4`；即便生产正确按deadline拒绝，测试原本的“仅目标1Task失败、其余3个健康Task通过”前置条件并未成立。此项暂不能计作生产错误，更不能放宽生产超时语义来“修复”测试。
- **新 Production blocker：未确认**；旧 Design/Implementation blocker仍CLOSED，不能因原Pair不变而做无意义源代码重审。

## 5. 决定与下一阶段执行

**建议现在进入 Codex fixture-only 修复设计/测试阶段，而不是持续在同一繁忙机器上重复原90s/5s Gate。**

Codex 允许的窄范围：只动 `tools/v3/eval_robocasa_queue_identity_test.py` 和确有必要的测试专用 helper／取证脚本，**不得修改**生产 Queue/Store/Progress、Child、模型/Local-TTT、checkpoint、训练、现有评测数据。

明确的可验收方案：
1. 对媒体密集、两阶段 Resume、多场景测试设置**有证据支持、有限且可解释**的 fixture 总预算，同时保留一个独立的真正停滞/无进展检测与最终硬上限；不能无条件放宽到无限等待，也不能靠 sleep 或禁用媒体验收让测试通过。原实际媒体解码、C01/Local/cleanup、COMPLETE/SR/重用数、不启动新Server等行为断言须原样或等强保留。
2. `task_timeout` 通过测试专用预算/故障刺激隔离，让3个正常Task有足够CPU+媒体审计时间，注入故障Task**必须仍真实超时、SIGKILL并回收子进程组**。确保依然断言只有1个 Task失败、其余3个完成、总计15成功闭合Episode、非零退出和SR为null。禁止更改生产 `task_wall_timeout` 语义。
3. 任何 watchdog 终止之前将 scenario最后阶段、Child PID/PGID、实际媒体文件/进程、source/invocation、console与error持久化到独立Evidence目录；定界区分被测子进程、其它并发 fixture 及外部非Owner进程。保留RED原件、修改后GREEN日志；不能把旁路诊断脚本绿色冒充原测试Pass。
4. 作者提交测试-only新**formal Implementation Root SHA**、Child/Gitlink实际状态及 red/green聚焦日志；再完成冻结五组 CPU组合、Ruff/format/syntax。即使仅fixture变更，也按固定审核规范对**新 exact pair**进行 GPT fresh incremental review；随后 DS_PRO 在 clean detached Pair独立复跑五组，失败即停并上报原Evidence。
5. 如无法安全修改测试仍可选择真低干扰时段的原Pair复验；若未经修改的原测试在同Pair全面转绿，可做纯Evidence closure，不重复技术审查。

## 6. Verdict 与授权边界

**`REQUEST_CHANGES`（Evidence-only），DS CPU Gate仍RED。** 源代码 Git SHA未变，GPT Implementation `APPROVE`不变。对运行观察的归因判断是证据评估，不是生产代码修复承诺。

本结论不授权GPU、真实模型/DCP/Kitchen、真实RoboCasa环境执行、训练、当前G1/18task工作树更新、覆盖历史Episode或重跑iter12000已完成20集。所有真实执行仍需Owner独立授权。
