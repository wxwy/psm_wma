# PSM-WMA V3 — Flexible Episode Resume 第二阶段生产接线独立审核

日期：2026-10-24（CST）。
**技术 verdict：`REQUEST_CHANGES`**。Scope 为本次精确 Implementation Pair 的源代码及作者 CPU Evidence；不代表真实 GPU / RoboCasa 验收。

## 1. Formal pair 与增量范围

- **Formal Implementation Root**：`252d823cf7f0e65228aa60408d50778c5a13a307`
- **Child / Gitlink**：`813a550dab5d6b5b5e3be90d38bb97527956b4dc`（未改）
- **Frozen Owner contract**：`cc7820bee1a73bd2bb2078cb7f00239944f66d37`，`docs/collab/chatgpt/requests/2026-10-23_Codex_V3_RoboCasa_flexible_episode_resume_contract.md`
- **已通过的 Design Gate**：`1bf88fa624e58e521caa2213f2b1a44bf2f2871d` / unchanged Child。
- **实现基线**：`db4ac8c690ba9f5971899d28768ac3caf7065108`。后续作者 Evidence/docs HEAD `493e9708a1f4db7ae1c8531add1eb24f4e603946` 不是实现 SHA。
- **实际变更**：Root 的 Queue 默认入口、`robocasa_resume_cli.py`、`robocasa_resume_store.py`、`robocasa_resume_execution.py`、`robocasa_episode_resume/`、聚焦 tests 及 runbook；Child 源码 / Gitlink / 模型、TTT、训练和 Vendor 保持不变。

## 2. 无新 blocker 的实现范围

依据精确远端源码及之前冻结契约直接核查：

- `scripts/robocasa_episode_resume/model_identity.py:313-321,396-466` 和 `scripts/robocasa_resume_store.py:196-249,259-300`：四硬参为 Checkpoint（路径+payload身份）、num_steps、action_horizon、guidance；legacy metadata/stat 桥接不伪造历史权重 hash；无 `--resume` 时拒绝占用旧目录，复用旧 Evidence 使用原 digest，基于同一 `.run.lock`。
- `scripts/robocasa_episode_resume/plan.py:134-312`、`scene_sampling.py`、`scripts/robocasa_resume_store.py:557-663`：Task 计划按当前 tasks/episodes/Seed、媒体决策；fresh Task 的 literal Seed 与单环境连续 reset，gap 的稳定派生 Seed 与 physical-to-logical 映射区分；持久 reservation 在 Source 创建之前写入，原来源保留。
- `scripts/robocasa_resume_store.py:466-513,664-688`、`scripts/robocasa_episode_resume/episode_evidence.py:445-690`：使用原 manifest/源 Attempt 的 progress、Local cleanup、action/prediction 与原媒体策略复核；COMPLETE 矛盾来源整项隔离；Catalog 不能替代 fresh verifier。
- `scripts/robocasa_resume_execution.py:208-389`、`scripts/robocasa_resume_cli.py:234-475`：新工作为受保护的模型/配置输入复核、Owner 进程组及 Worker fault handling；最后重扫已验证来源、分离当前 view 与历史 Evidence，保留视频缺口和可比性警告。纯全复用不启动 Server/Simulator，且不冒充新的 runtime probe。

以上是本次**源代码静态审查的局部判断**，不构成真实运行或 DS CPU 通过。

## 3. 当前新 blocker

### HIGH-01 — 失败 Episode 的最终 progress 补算采用非有界/非严格 parser，可能绕过最终 PARTIAL 报告

- **严重级别**：HIGH。
- **位置**：`scripts/robocasa_resume_cli.py:142-184`（`_unfinished_executions`）；`scripts/robocasa_resume_cli.py:443-446`（仅捕获 `OSError`）；`scripts/robocasa_resume_cli.py:405,447-465`（RUNNING 先写、final report 后写）。
- **实际根因**：新任务结果收尾时，`_unfinished_executions` 直接以 `path.read_text().splitlines()` 无界读取未验证的物理 `episode_progress.jsonl`，没有文件/行数上界、没有完整末尾换行检查，也没有复用 C01 的严格 JSONL 时序/身份读取约束。调用方的 `except OSError` 不覆盖 `UnicodeDecodeError`。
- **可核查反例**：新批次进度文件（在进度创建后）出现单字节 `0xFF`，`Path.read_text()` 抛 `UnicodeDecodeError`（`UnicodeError`，不是 `OSError`）。最后的 `store.discover_history()` 可以将原进度不合规记录为 source diagnostic，但随后的 `_unfinished_executions()` 会将该异常继续向外抛出；`_summary()` 与 `store.write_report()` 最终发布步骤被跳过，之前的 latest `RUNNING` 视图可能保持不变。另一个独立反例：无终止换行的完整 JSON `start` 行会被 `splitlines()` 当成已提交的 Episode start，和原始 C01 newline-complete 规则不一致。大文件还可能引起无界内存读取。
- **违反冻结契约**：Owner request 第1/4/5/6节要求真实的 Episode completed/started 证据、损坏源明确诊断、异常时不得伪报完成并必须持久化 PARTIAL/remaining/failed/report，保持原始 Evidence 不变；已批准 r2 设计还要求恢复只凭持久、有证据的逻辑来源，不能把不完整事件当有效 authority。
- **可验收整改**：只在终态 unfinished-start 证据补算与其调用侧做窄范围处理，采用有界（文件字节、单条行长、行数/逻辑 Episode index）、明确换行完成、严格身份/顺序的 C01 read；对 invalid UTF-8、非法/重复字段、截断尾部、超限数据保持 fail-closed。若文件本身不可解析，必须记录明确的 `final_progress_read` 错误并在此前已经分配的 invocation 中持久提交最终 `PARTIAL`、非零 exit_code、正确 remaining；不得覆盖历史文件、不得伪造 executed/failed 次数。
- **必需 CPU 证据**：① 新执行 job 进度包含 invalid UTF-8，经过真实 `prepare_resume` finalization 后不会抛出未处理异常，最终视图为 PARTIAL、非零退出、保留 job/原始错误；② JSON start 没有 terminating newline 不计作已证实的 start；③ oversized source fail-closed 且有界，不发生无界读取；④ 合法 newline-terminated start+中断正例仍准确计入 executed/failed；⑤ 完整正常五组 CPU 组合保持全绿。不得通过 broad `except Exception: pass` 吞掉状态或用人工补造日志通过测试。

## 4. 作者 Evidence 核查、待独立验收

- 作者 Evidence 目录：`docs/collab/codex/evidence/2026-10-24_flexible_episode_resume_production_author_cpu/`，作者 Handoff `docs/collab/codex/reviews/2026-10-24_flexible_episode_resume_production_author_handoff.md`。
- 仓库冻结 JUnit 报告 `<testsuite tests="226" failures="0" errors="0" skipped="0">` 且实际 `<testcase>` 元素 **154**；其余 **72** 为作者报告的 subtests（不应称为 226 个顶层 testcase）。作者附 Ruff0.12.7 / format / syntax PASS。变更源码 hash 及 production scope 已按 commit 核对。**GPT 没有在用户服务器重跑这154项，DS_PRO 独立 CPU 尚未执行。**
- 合成 CPU 中真实调用了 Queue/Store/OwnedProcess/HTTP/Local 客户端，但真实 DCP tensors、GPU Model / RoboCasa physical environment 不在已证明范围；不能用作者测试数量掩盖上述新增 progress-finalization 异常路径。

## 5. 判定、交接与 Gate 边界

**`REQUEST_CHANGES`**，当前生产 Implementation Gate 不关闭；上轮 Design r2 的 HIGH-01/MEDIUM-02/MEDIUM-03 保持 CLOSED，不因新 Gate 重新打开；本轮新出现的 HIGH-01 仅针对生产终态 progress 读取/错误持久化。

Codex 只做本 finding 的定点生产修复与故障注入 + 正例测试，提交**新的精确 Implementation Root SHA / Child-Gitlink SHA**，GPT 做 fresh incremental review。DS_PRO 之后在 clean detached 精确 Pair 上完成独立 CPU Gate；在当前 SOURCE 尚有 blocker 时不应据作者154测试宣称 DS 或生产 Gate 已通过。

**不授权** GPU/真实 RoboCasa/Action Server 模型加载、正式评测启动、Checkpoint 改写、训练、G1 或 iter12000 既有20集重跑；无需更新活动训练/仿真工作树。
