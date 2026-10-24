# PSM-WMA V3 — Flexible Episode Resume / MEDIUM-F01 DS_PRO CPU run1 GREEN Evidence review

审核日期：2026-10-24（CST）。
**GPT formal Evidence verdict: `REQUEST_CHANGES` — EVIDENCE-ONLY / PRIMARY ARTIFACT ACCESS.**
**DS_PRO 自行执行的 CPU Gate 结论：GREEN（按其提交的详细报告）；本轮未发现 Code 逻辑新 blocker。**
这两个状态不得混用：DS 的 GREEN 是已完成的独立运行结果的陈述；GPT 在没有原始 DS JUnit/日志可读时不把它冒充为 GPT 已完成的原始 Evidence 验证。原精确 Pair 的代码审核 `APPROVE` 保持不变。

## 1. 精确身份与原有 Gate

- **Formal Root**: `fe9d537b4a5f82c8ea72a4f8ce182fdcefac6790`
- **Formal Child/Gitlink**: `813a550dab5d6b5b5e3be90d38bb97527956b4dc`
- 冻结 Owner 合同: `cc7820bee1a73bd2bb2078cb7f00239944f66d37`。
- 上轮 GPT Fixture `APPROVE`: `docs/collab/chatgpt/reviews/2026-10-24_V3_fixture_MEDIUM_F01_fe9d537b_813a550d_incremental_review.md`，MEDIUM-F01 CLOSED；本次 root/child 未变，**不重新做技术代码审核**。
- 历史独立 DS 失败属于较旧的生产+fixture pair `6151e071...`，不是此精确 fixture SHA 的新 bug 发现。原批准生产代码 `6151e0712f28ace5d92258a8feb31fa8f1ee81c1`，与本 fixture formal pair 的 `scripts/`, `configs/`, `third_party/`, Child 相同。
- 取证时远端 V3 HEAD 为 `bc398926da119e2252be7700fc9d71dfa4e8620b`（review/inbox bookkeeping），比较 formal root 到该 HEAD **无任何 scripts/tools production/test 差异**，不会改变正式技术 target。

## 2. DS 提交的独立 run1 报告 — 内部一致性审查

DS_PRO 报告正式只读运行：

- Clean detached root `fe9d537b4a5f82c8ea72a4f8ce182fdcefac6790` + Child/Gitlink `813a550dab5d6b5b5e3be90d38bb97527956b4dc`，Root/Child worktree clean；冻结 16 Python 文件 SHA 全部匹配，包含新的 `queue_fixture_watchdog.py`。
- 机器：Linux 共享 CPU，Python3.13.11、pytest9.0.2、Ruff0.12.7；`nice -n 10`，G1/他人训练仍在运行。作者曾使用Python3.12.14，本轮Python小版本不同但没有因此产生测试错误，不构成本轮 blocker。
- 实际测试命令与冻结五组一致（变更工作目录/evidence路径，CPU/GPU禁用及cache外置，`PYTHONPATH=.:scripts:tools/v3`）。DS报告测试结果 `172 passed, 72 subtests passed in 2645.21s`、0 failure/error/skip；说明 JUnit有172 testcase 元素，未把72 successful subtests当单独顶层 case。
- 分组统计：`robocasa_resume_components_test.py`41、`robocasa_resume_store_test.py`32、`robocasa_resume_execution_test.py`22、`robocasa_episode_resume_integration_test.py`26、`eval_robocasa_queue_identity_test.py`51，总计**172**，与该 exact SHA 已审源及作者独立 archived JUnit（同为172 +72，0 fail）一致。
- 八项 `FixtureWatchdogTests` 全部报告PASS，包含原4正/负控制、快照文件写失败仍杀/回收、取证期间新child reaping并避杀foreign、Evidence目录创建失败仍回收，以及 `KeyboardInterrupt` 清理后传播。Frozen source tests `tools/v3/eval_robocasa_queue_identity_test.py:1164-1406` 的验收语义与报告一致。
- DS描述 `snapshot_io_negative` `cleanup.json` 包含 `EVIDENCE_SNAPSHOT_FAILED`、主watchdog.json诊断写入失败、`killed_owned_pids=[150929]`、`cleanup_errors=[]`、`cleanup_final_processes=[]`、`cleanup_remaining_live=[]`、root returncode=-9；符合被审 Watchdog 的设计，未与原代码冲突。
- DS 报告所有原先旧90s/5s失败场景在此新 fixture SHA 上完成，未再次触发 90s watchdog截断；四组/运行态测试未修改生产代码。时长对比作者1661.249s vs DS2645.21s，DS约**1.59倍**。loadavg 31.99–43.31 on192 cores并不单独证明CPU饥饿，但不影响本次测试在共享机器真实执行 GREEN 的声明。
- DS报告 Ruff check/format、16文件compile/保护范围Gitlink/hash检查PASS；逻辑与作者冻结 `static_checks.json` 范围一致。
- GPT已经从GitHub再次读取**作者** JUnit及精确Root/Gitlink/上轮 review；作者源测试172cases+72 subtests。**不能把作者 JUnit 冒充为此次独立DS JUnit。**

## 3. 唯一剩余 Evidence-only 缺口

### MEDIUM-E03 — DS 原始通过证据未能直接被 GPT 读取归档，正式 Evidence closure 尚缺一次 primary-source 回验

**发生位置：** DS独立测试产物，据报告存放在
`/mnt/data1/data_v2_0617/psm_wma_ds_cpu_fe9d537b_813a550d/run1_20261024_115520/`，
包括 `junit.xml`、`pytest.log`、`ruff-check.log`、`ruff-format.log`、`static_checks.{log,json}`、`STATUS.json`、`frozen_source_sha256.json`、`meta.txt`、`ps.log`、`cgroup.log`、`evidence/`、`frozen_final_scenarios/`。

**根因/限制：** 该服务器路径未挂载至本轮容器，也不在GitHub远端。Remote Desktop Commander 本轮为 Offline。GPT因此无法独立打开 DS 原始 `junit.xml`，无法核实其172项case元素及 XML failure/error/skip、实际进程快照中的PID归属和 `cleanup.json` 的原始记录。完整报告可作为 DS 的正式执行陈述，但尚不足以替代本项目要求的独立 raw Evidence 回读。

**冻结合同关联：** Evidence `contract → behavior → evidence`，每次 Gate 需要确切的测试/JUnit、命令、源哈希以及负例和回收见证。此前DS RED与此 run1 GREEN 的结论区分是必要的。测试计数不能独立等价为行为证明。

**精准验收（只补可审核证据，原则上不需要再次运行任何 CPU 测试）：**

1. DS_PRO 在**不改 Formal Root/Child/测试/原始 Evidence**情况下，发布原始 `junit.xml`、`pytest.log`、`STATUS.json`、`meta.txt`、`static_checks.json`、Ruff check/format原始日志、`frozen_source_sha256.json`、完整执行命令及其 SHA256 清单到可供 GPT 读的持久 Evidence 目录（例如GitHub V3 的 `docs/collab/ds_pro/evidence/...`，或直接在会话上传这些文件）。
2. 补充至少 `snapshot_io_negative/cleanup.json`、取证期间新生 child 的 `watchdog.json`/相应 PID/PGID witness、八项 Watchdog 控制的 testcase结果、`scenario_index`或签名清单；113MB视频/媒体与约7万行ps.log可以继续保存在DS只读服务器上，提供已记录的SHA256与精确路径，无需把所有大文件提交GitHub。
3. GPT只做原始 Evidence 与现有 exact pair/DS报告对账：SHA/Gitlink/source hashes、五组方法与172+72统计、零failure/error/skip、STATIC_PASS、cleanup/foreign/snapshot witness。如果一致，**Evidence-only Gate可正式批准，无需新Implementation SHA，也不需要重做代码审核或重跑CPU测试**。文档/Evidence/bookkeeping commit不能替代 formal source SHA。
4. 若原始 Evidence 与报告相矛盾（少组、skip或脚本/source差异），保持 RED 并给出对应反例；不要根据漂亮的总结猜测 PASS。

本 finding **不是生产代码缺陷，也不否定DS已报告的 GREEN**；它仅是正式GPT审核缺少可访问的原始独立产物。故当前可说明“DS independent CPU GREEN (reported)”，但不得表述“GPT independently verified DS JUnit and closed triple Gate”。

## 4. Verdict、权限与后续

**GPT 正式 Evidence verdict：`REQUEST_CHANGES`（EVIDENCE-ONLY，MEDIUM-E03 open）。** 生产Code及Fixture Code Gate保持已批准，不存在新的源码修改需求；DS自报五组已独立GREEN，唯一后续动作是归档/提交可访问原始运行产物供 final Evidence closure。

**不授权**真正GPU/模型/DCP读写、RoboCasa Kitchen/SIM reset/step、训练/Checkpoint、活动G1工作树更新、原20 Episode重跑或历史证据覆盖。Owner对任何真实执行仍需另行批准。
