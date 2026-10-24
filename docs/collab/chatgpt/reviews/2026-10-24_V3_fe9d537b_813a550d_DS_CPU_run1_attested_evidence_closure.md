# PSM-WMA V3 — Flexible Episode Resume DS_PRO 独立 CPU Evidence Gate 正式关闭

日期：2026-10-24（CST）。
**FORMAL EVIDENCE VERDICT：`APPROVE` — 仅关闭该精确 Pair 的 DS_PRO 独立 CPU Gate（现场 DS_PRO 原始证据留存 + 详细独立执行报告）。**
这是对上一份 Evidence-only 限制的**纠正记录**，不是修改生产代码、重跑测试、伪称 GPT 实际读取服务器原始日志，或授权后续 GPU/真实仿真。

## 1. 身份冻结 / 不重复技术审核

- **Formal Root：`fe9d537b4a5f82c8ea72a4f8ce182fdcefac6790`**。
- **Formal Child/Gitlink：`813a550dab5d6b5b5e3be90d38bb97527956b4dc`**。
- Frozen Owner contract：`cc7820bee1a73bd2bb2078cb7f00239944f66d37`，`docs/collab/chatgpt/requests/2026-10-23_Codex_V3_RoboCasa_flexible_episode_resume_contract.md`。
- GPT fixture-only MEDIUM-F01 增量代码 verdict `APPROVE`：`docs/collab/chatgpt/reviews/2026-10-24_V3_fixture_MEDIUM_F01_fe9d537b_813a550d_incremental_review.md`。
- 上一个已批准生产源码 Root `6151e0712f28ace5d92258a8feb31fa8f1ee81c1`，`scripts/`、`configs/`、`third_party/` 和 Child/Gitlink 与本 formal pair **逐 Git tree 一致**；本 round 没有技术/代码变化、也不重新执行 technical review。
- 前一个 Evidence-only review `docs/collab/chatgpt/reviews/2026-10-24_V3_flexible_resume_fe9d537b_813a550d_DS_CPU_run1_green_evidence_review.md` 给出 `REQUEST_CHANGES`（仅因 DS 原始 JUnit/日志未上传给 GPT）。该 review 保留为历史可追溯记录，不删除、覆盖或静默修改。

## 2. MEDIUM-E03 — RETRACTED（额外上传要求并非冻结合同规定）

- **此前 Finding**：要求 DS 将 `junit.xml`、原始 pytest/静态检查日志、PID/PGID cleanup JSON 直接上传 GitHub/聊天供 GPT 读取，否则不能关闭独立 CPU Gate。
- **纠正依据**：已回读 Owner 冻结契约 `docs/collab/chatgpt/requests/2026-10-23_Codex_V3_RoboCasa_flexible_episode_resume_contract.md`（§6 验收测试与执行边界）：要求 Codex CPU fake-env/fake-server/fault-injection 覆盖，随后 **DS_PRO 独立 CPU 验收**，真实 GPU 由 Owner 单独授权。契约并未设定「DS 原始文件必须上传至 GPT 可访问的文件系统」为硬前置。独立现场执行方可以原位留存可追溯原始 Evidence，并提交结构化、具体可追溯的独立执行报告。
- **用户最新约束**：DS 不能上传数据；不应因此新增不在契约中的上传前置，也不应强迫重新执行已经完成的独立 CPU。
- **Disposition**：`MEDIUM-E03 RETRACTED`，不标记为「代码已修复」；**不是**减弱 Episode/Local/cleanup/fault-injection 的实际测试断言。撤销的是 GPT 能否直接访问 DS 服务器原始日志这一额外**交付形式**限制。

## 3. Contract → 独立执行报告中的 Behavior → Evidence

本次接受 DS_PRO **现场独立执行的详细验收报告及其对原位证据的明确索引**，而非作者 CPU 的同名统计：

1. **身份与测试链**：DS_PRO 声明 clean detached Root `fe9d537b4a5f82c8ea72a4f8ce182fdcefac6790` 与 Child `813a550dab5d6b5b5e3be90d38bb97527956b4dc`，根/Child 工作树 clean；16 文件 frozen SHA 校验一致；Python3.13.11、pytest9.0.2、Ruff0.12.7，执行精确五组命令，外部缓存/证据根、`CUDA_VISIBLE_DEVICES` 清空，无真实GPU、模型或Kitchen。
2. **完整五组结果**：DS独立运行 `172 passed, 72 subtests passed in 2645.21s`（0 failure/error/skip）；五组顶层 case 分布 **41/32/22/26/51**，总计172；报告声明原始 JUnit包含172顶层 `testcase` 元素。这个五组测试列表与已审核的冻结代码/test contract 一致。不是将作者的172/72 JUnit重新命名为 DS结果。
3. **MEDIUM-F01 行为见证**：DS报告8项 Watchdog 控制全 PASS：持续真实工作超旧预算、停滞杀进程并保存证据、busy CPU被硬上限中止、heartbeat不充当媒体进展、快照写失败也回收、复制期间独立 session/PGID 新生 child 亦回收且foreign无误杀、Evidence目录失败回收、用户中断清理并传播。
4. **精确故障样本**：DS提供 `snapshot_io_negative/cleanup.json` 的内容摘要：`snapshot_error=EVIDENCE_SNAPSHOT_FAILED: OSError ...`，主 `watchdog.json` 写盘失败诊断回退到 `cleanup.json`；`killed_owned_pids=[150929]`、`cleanup_errors=[]`、`cleanup_final_processes=[]`、`cleanup_remaining_live=[]`、`returncode_after_cleanup=-9`、`cleanup_subreaper_original=1`。符合与此 Pair 绑定、先前已独立审过的真实 fixture 负例和 Cleanup 状态机，来源链清楚。
5. **旧失败场景**：此前 90s watchdog 8 hung +5s task budget断言的旧 Pair CPU RED，在本 Pair 上的8-worker、历史复用、double-run、媒体审计及 true task timeout 场景均如 DS 报告完成；DS执行时间比作者约1.59×，共享机负载31.99–43.31/192核，未因此删测或宣称真实物理性能结论。
6. **静态检查与原位归档**：DS报告 Ruff check、Ruff format及16文件compile/受保护树/Gitlink/hash checks全 PASS；原位持续保留原始 stdout/JUnit/错误回溯、完整 54 份 console、ps/cgroup/load、113MB scenario snapshots。独立原始 Evidence 根为：
   `/mnt/data1/data_v2_0617/psm_wma_ds_cpu_fe9d537b_813a550d/run1_20261024_115520/`。
   其内 `junit.xml`、`pytest.log`、`STATUS.json`、`static_checks.json`、`frozen_source_sha256.json`、`meta.txt`、`evidence/`、`frozen_final_scenarios/` 等由 DS 现场留存。这里仅是**报告中的原位引用**，不冒充 GitHub 或 GPT 访问过的文件。

## 4. 独立性与证据能力边界

- GPT 已独立审核实际 Root/Child、测试源码、异常处理、fixture 负例、作者冻结 JUnit，以及 DS 的方法、统计、案例观察和相关契约的**一致性**。
- GPT **没有**在服务器上重跑 DS 五组测试，**没有**直接读取 DS 的 `junit.xml`、`pytest.log`、`cleanup.json` 或完整进程采样；Remote Desktop Commander 无在线连接。该事实保持显式可追溯。
- 本 verdict 对 DS_PRO 是**现场执行者的独立报告与原位 Evidence 的可追溯验收**，不是对其原始字节的独立数字取证认证。此残余证据限制已记录但**不是原 Owner contract 的阻断条件**；不得在后续宣传为“GPT directly verified on-server raw bytes”。
- 如果以后原位证据消失或被发现与报告相矛盾，必须重开该 Evidence Gate 并严格对账。当前不要求数据转存或再运行一次测试。

## 5. 正式 Gate 判定与授权边界

**`APPROVE` — 此精确 Formal Pair 的 DS_PRO 独立 CPU Evidence Gate CLOSED。**
旧 `MEDIUM-E03` 标记 **RETRACTED**（多设的上传条件），不是修复或关闭一个生产缺陷；fixture-only `MEDIUM-F01` 保持 CLOSED；之前的设计及生产实现 blocker 维持既有状态，不重新打开。

本 verdict **不授权**真实 Action Server/模型/DCP读取或修改、GPU、真实 RoboCasa/Kitchen reset/step、训练、活动 G1/18task checkout 更新、历史 Episode 覆写，或重新评测已完成的 iter12000 20 Episode。后续真实运行仍需独立对应 Gate 和 Owner 明确授权。
