# PSM-WMA V3 — Flexible Episode Resume fixture-only r3 独立增量审核

日期：2026-10-24（CST）。
**VERDICT: `REQUEST_CHANGES`（fixture-only Implementation/CPU-Evidence Gate）。**
原批准的生产源码 `6151e071...` 未出现新缺陷判定；DS_PRO 独立 CPU 仍然 RED。此结论不批准真实 GPU、模型或 RoboCasa 仿真。

## A. 审核对象与范围

- Formal Root：`dfb8a12140be7bf34584504c47df9042229f5bfb`
- Formal Child/Gitlink：`813a550dab5d6b5b5e3be90d38bb97527956b4dc`
- 基线：`22b0abcbf08316d576ef2d56c55af6151a6060e5`；旧生产 formal Root：`6151e0712f28ace5d92258a8feb31fa8f1ee81c1`，原 GPT Implementation code Gate `APPROVE` 仅对其原 pair 有效。
- Frozen Owner contract：`cc7820bee1a73bd2bb2078cb7f00239944f66d37`；上一 DS retry1 Evidence-only `REQUEST_CHANGES`：`docs/collab/chatgpt/reviews/2026-10-24_V3_flexible_resume_6151e071_813a550d_DS_CPU_retry1_evidence_RED_review.md`。
- 本次单一源提交的业务文件差异仅 `tools/v3/eval_robocasa_queue_identity_test.py`（modified）及 `tools/v3/queue_fixture_watchdog.py`（new），其余为 SESSION/TODO。GitHub formal trees 对比：`scripts/` 两版 tree SHA 均 `31ef1a90b6ef1a57ec0d7a5efe88ec8fd6fd06f0`、`configs/` 均 `deab6194fe4a9f766eec1f7f22c9d38966a34b12`、`third_party/` 均 `d01633d083298fc5245b5bc97677c5b297700c31`，Child/Gitlink 完全未变。没有新生产接线/模型/Local-TTT 算法修改。
- 作者交接/Evidence HEAD `72b664388ec62fe7af42781ca7c02ff8d128e3a8`，**不是 formal root**。交接 `docs/collab/codex/reviews/2026-10-24_flexible_resume_fixture_r3_author_handoff.md`，Evidence `docs/collab/codex/evidence/2026-10-24_flexible_resume_fixture_r3_author_cpu/`。
- 独立核查范围为精确远端 diff、新 Watchdog 源码/四个控制测试、冻结 Queue fault assertions、作者 JUnit/静态检查/场景索引；没有在 DS 服务器或 GPT 环境重跑完整五组 CPU，也没有直接读取 DS retry1 远端原始日志。

## B. 本轮可确认的正确改动

1. `tools/v3/eval_robocasa_queue_identity_test.py:42-61,1296-1325`：普通场景600秒、task_timeout900秒独立硬上限；`watch(...,media_only=True)` 以媒体/核心证据变化与媒体解码 CPU 记录喂给180秒 stall 计时，不依赖 UI/Server heartbeat；不把 CPU tick 视作无限进度，另有硬上限。实际生产媒体校验和源证据复用测试路径并未绕过。
2. `tools/v3/eval_robocasa_queue_identity_test.py:713-716,856-860,1575-1606`：测试级 task_wall 从5秒标定为120秒，故障模拟器与子进程的真实挂起延伸到3600秒。仍按真实生产 Task wall deadline，断言仅一项失败、其它3个Task闭合合计15个Episode、`PARTIAL`、`SR=None`、错误原因为 `task wall timeout`、`SIGKILL` 和 owned cleanup。
3. `tools/v3/queue_fixture_watchdog.py:17-62,95-151`：PID/PPID/PGID/start ticks 与文件/媒体CPU活动的归属观测；超时前的有界原始文件和进程快照可保留于独立 Evidence 目录，文件单个32MiB、合计128MiB，记录 snapshot skipped。 `FixtureWatchdogTests` 4项覆盖真进展超过旧短预算、简单停滞、CPU忙循环仍触及硬上限，以及 UI heartbeat 不能喂给 media stall。
4. 作者冻结五组 `junit.xml`：`tests="240"`，实际 **168 个顶层 `<testcase>`**，另72个 successful subtests，0 failure/error/skip，elapsed1399.805s。Ruff0.12.7/format16文件与syntax static PASS；作者受控 RED 只演示旧短预算的等待失败，**不是 DS 90s 源故障复现**。证据索引包含 focused/full/controls 场景，不可将作者测试等同独立 DS CPU Gate。

## C. 新 finding — MEDIUM-F01，OPEN

**标题：Watchdog 清理依赖取证成功且使用取证前的陈旧进程快照，无法保证 timeout 资源回收。**

- **严重级别：MEDIUM（fixture-only safety/evidence blocker，不是 production Resume bug）。**
- **文件与行：** `tools/v3/queue_fixture_watchdog.py:65-93,112-120,137-168`，核心为 `:152` 先调用 `_retain(destination, source, state)`，之后 `:153-167` 才按 `rows` 清理 PID。
- **根因 A（取证失败跳过清理）：** `_retain()` 的 `destination/watchdog.json.write_text(...)` 等 I/O 未被 `watch()` 的 `try/finally` 保护。若 evidence 卷写满、写入出错或保存过程中出现未捕获异常，执行从 `:152` 抛出，后面的 `SIGKILL` / `process.wait()` 完全不执行。测试场景及其媒体子进程可能继续运行；对共享 CPU 机器的原本90秒 abort 故障尤其不安全。
- **根因 B（取证期间新建子进程漏清理）：** `:112` 每轮构造的 `rows` 是 capture 前的 PID/PPID/start 快照，`_retain()` 在 `:152` 可能复制多个真实媒体文件；场景此时仍运行，能在复制期间启动新的 FFmpeg/decoder 子进程。之后 `:155` 仅循环 `reversed(rows)`，且对每个既有 PID 单独 `os.kill`，不是重新确认全部 post-snapshot owned descendants。新生 child（特别是不同 session/process group）若未在旧 rows 中出现，可能在 root 被 SIGKILL 后成为存活孤儿。仅验证 start ticks 可以阻止误杀重用 PID，却不能弥补 PID 列表遗漏。
- **冻结要求冲突：** 本轮授权明确要求“有限硬限 + 取证前后归属明确 + 终止前证据留存 + 不污染其它测试/用户进程”；正确错误收尾和洁净 owned-process 回收是该 fixture Gate 的必要行为。当前只覆盖快照成功、静态已有 PID 被杀和无关外部 PID 幸存；没有证据证明快照失败/并发创建 descendant 时 fail-closed 清理仍成立。
- **验收条件：**
  1. 只对 `tools/v3/queue_fixture_watchdog.py` 及其测试做窄修复。对 bounded snapshot 抛出的 `OSError`/其它不可恢复保存异常，仍须有界地中止并回收本场景拥有的 root/decoders/child groups，保留或报告 `EVIDENCE_SNAPSHOT_FAILED` 及原始 `hard_limit`/`no_cpu_or_file_progress`，不改成 PASS，不使用全系统 indiscriminate group kill。
  2. 处理 snapshot 前后子进程集合变化，保证 timeout cleanup 不只依赖 snapshot 前的 `rows`。可通过冻结场景新建进程、再次确认 owner identity 并补回收、或其它有界可靠策略；不得误杀无关用户进程，须保留 start-ticks/pid/ppid/pgid 证据。
  3. 增加确定性 CPU 负例：在 `_retain` 中注入证据写盘异常、另一个负例在 snapshot 期间让 scenario 创建**新的不同 session/PGID 的 owned child**。两个负例都要断言 root/新增 child 清理完毕、非 owner 的 foreign control 仍活着、可读的错误证据与非成功结果。保留四项旧 watchdog 控制、完整 Queue 五组与真实 FFmpeg 媒体校验不变。
  4. 新正式 fixture Root SHA/Child pair + targeted RED/GREEN/最终五组 CPU 作者 Evidence 重新提交 GPT 增量审核。任何 GPU/真实模型、改变生产 timeouts/media validator/Local-TTT/G1/iter12000 的整改均不授权。

## D. Gate 判定

旧 DS Evidence HIGH-E01/MEDIUM-E02 的预算/诊断性整改方向正确，但本新 formal pair 的 **MEDIUM-F01 仍 OPEN**，因此仅凭作者168+72不能正式批准 fixture-only Gate 交 DS closure。

**`REQUEST_CHANGES`**（限测试Watchdog异常收尾与安全回收）。生产脚本/Child未变，原生产 Code Gate `APPROVE` 继续只绑定 6151 原 pair；DS_PRO 独立 CPU Gate 保持 RED。无需恢复对原 production 的技术重复审核。

**禁止本轮批准真实 GPU、真实 RoboCasa/Action Server/DCP、训练、活动G1、历史运行数据修改或既有 iter12000 20 Episode 重跑。**
