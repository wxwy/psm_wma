# PSM-WMA V3 — Flexible Episode Resume Progress HIGH-01 r2 独立增量复审

日期：2026-10-24（CST）。
**VERDICT: `APPROVE` — GPT Implementation HIGH-01 增量代码/Evidence Gate。**
仅表示本次精确 Root/Child 上前轮 blocker 已闭合，可交 DS_PRO 独立 CPU；**不代表 DS CPU、实际模型或真实 RoboCasa 运行 Gate 已关闭。**

## A. 精确身份和冻结范围

- Formal Implementation Root: `6151e0712f28ace5d92258a8feb31fa8f1ee81c1`。
- Formal Child/Gitlink: `813a550dab5d6b5b5e3be90d38bb97527956b4dc`，未变。
- 上轮 formal Root `252d823cf7f0e65228aa60408d50778c5a13a307` / 相同 Child：独立审查 `REQUEST_CHANGES`，当前唯一生产 blocker **HIGH-01**。
- 本次源代码提交直接 parent：`6e10c8d461ecc5f49e05da932a2d925e9ad62ef3`（上轮 detailed review + canonical Inbox 持久化）；本文档/作者证据 HEAD `236c8a18dfbef5c74b587ac94954524663ce4a41` 不是正式 implementation SHA。
- Frozen Owner contract：`cc7820bee1a73bd2bb2078cb7f00239944f66d37`，`docs/collab/chatgpt/requests/2026-10-23_Codex_V3_RoboCasa_flexible_episode_resume_contract.md`。
- 已批准 Design r2 Root `1bf88fa624e58e521caa2213f2b1a44bf2f2871d`，Child 相同；对应旧设计 blocker 继续标记 CLOSED，不重新审核。
- 对上轮 implementation 的增量修改仅 `scripts/robocasa_resume_cli.py`、`tools/v3/robocasa_episode_resume_integration_test.py` 及 SESSION/TODO。无 Child、Store、Executor、TTT、Checkpoint、训练、Vendor 或现有运行工作树新改动。

## B. HIGH-01 — CLOSED

**问题**：旧 `_unfinished_executions()` 使用无界 `read_text().splitlines()`，既可以把无换行的伪 start 计入执行数，也会因 UTF-8 损坏抛出未捕获 `UnicodeDecodeError`，跳过最终持久化 PARTIAL 的收尾代码。

**修正源码（精确实现）**：

1. `scripts/robocasa_resume_cli.py:144-198`：新增 `_progress_starts(job)`。原始 `episode_progress.jsonl` 使用二进制逐行 `readline(4097)`，在打开前拒绝非普通文件及超过 `MAX_RECOVERY_BYTES`（64MiB）的文件；限制单行 4096 字节、总字节、最多 `2 * reserved_episodes` 行、逻辑 Episode ID 不越界。
2. 同段要求每条 `\n` 终结、严格 UTF-8、无重复 JSON 键和非有限数；校验源 manifest digest、`task/attempt`、物理 Episode 顺序和 start/end 交替；读前和读后 `dev/inode/size/mtime/ctime` 一致。遇到任何损坏，不发布此前的部分计数。完整合法而未闭合的 start 可以贡献 **已启动但未完成**的计数。
3. `scripts/robocasa_resume_cli.py:201-232`：`_unfinished_executions(jobs, completed, *, errors)` 针对每个 job 捕获 `OSError, ValueError, RecursionError`。Python 的 `UnicodeDecodeError` 是 `ValueError` 子类；记录有 task、path、异常类型/原因的 `final_progress_read`，然后继续处理其他 job。无进度文件（尚未开始仿真）不伪造 start；合法 starts 按批次物理→逻辑映射，只补未在最终已核实来源中闭合的项。
4. `scripts/robocasa_resume_cli.py:476-509`：最终扫描、模型输入重核、选中来源重核之后，显式把该 progress 读取错误并入 `final_errors`，继续 `_summary → publish_catalog → write_report`。故障使完成状态为 `PARTIAL`、SR 为空、exit_code 非零；保留 Worker/cleanup 和原始 Evidence。未引入 `except Exception: pass` 代替报告持久化。

**来源→行为→证据**：

- `tools/v3/robocasa_episode_resume_integration_test.py:632-691` 新增 9 种真正通过默认 CLI 终态路径的故障注入：invalid UTF-8、无结束换行、64MiB 文件超限、4096B 行超限、重复键、错误 Attempt、错序事件、NaN 以及合法但未闭合的 `start` 正例。断言 `latest_invocation` 当前报告与保留快照均是最终 `PARTIAL`，`remaining=5`、`exit_code=1`、正确 executed/failed、`final_progress_read` 诊断、原 Job 错误及进程清理证明，同时检查损坏后的原文件不被本次终态处理进一步改写。
- `tools/v3/robocasa_episode_resume_integration_test.py:694-706` 单独证明超限文件在 `Path.open` 之前因 stat 被拒绝。
- 上轮准则的「合法 start 仍计执行」对应新参数化测试 `valid_start`，且原16项集成与其余四组保留。
- 本次只读源码审计确认 `UnicodeDecodeError` 等异常不会绕过原先已成功启动 invocation 的最终报告写入路径。该范围没有发现新的 HIGH/MEDIUM blockers。

## C. 作者测试与独立性边界

- 作者证据：`docs/collab/codex/evidence/2026-10-24_flexible_episode_resume_progress_r2_author_cpu/`；handoff `docs/collab/codex/reviews/2026-10-24_flexible_episode_resume_progress_r2_author_handoff.md`。
- 已读取冻结 JUnit：`<testsuite tests="236" failures="0" errors="0" skipped="0" time="1155.140">`；实有 **164 个 `<testcase>`**，另外 **72 个通过的 subtests** 不单列 testcase。Ruff0.12.7 check/format15文件和语法/源码 SHA 静态记录 PASS。
- 作者声称红基线 8 failed/1 passed、绿测试10 passed；提交了原始压缩日志/XML，且正式 JUnit 中实际包含全部9个 `test_final_progress_fault...` 参数化 case。
- 这些是 **Codex 作者 CPU 证据**，GPT 只独立查看远端代码和 Evidence，**没有执行作者五组 CPU、真实 DCP/model/Kitchen/GPU**。不能合并上一 SHA 的 154+72、r2设计185等数字凑成本轮通过数量。

## D. 判定与后续授权

**`APPROVE` — HIGH-01 CLOSED，当前精确 Implementation Pair 的 GPT 增量代码 Gate 通过。** 未发现新阻断项。

下一阶段：DS_PRO 在新的 clean detached Root `6151e0712f28ace5d92258a8feb31fa8f1ee81c1` 与 Child/Gitlink `813a550dab5d6b5b5e3be90d38bb97527956b4dc` 上独立运行冻结五组 CPU 测试与对应 Ruff/格式/语法/源哈希检查，保存原始执行命令/JUnit/log/真实 SHA。任何失败向 GPT 返回证据并停止，不改生产代码。DS 结果经独立 Evidence 裁决后才考虑后续 Gate。

**本 verdict 仅关闭本轮 GPT 增量审核。** 不授权活动 G1/18task 工作树同步，不授权真实模型、GPU、RoboCasa 构建/reset/step、真实 DCP读写/训练/评测，不要求重跑 iter12000 已完成的4任务×5集。Owner 保留所有真实执行授权。
