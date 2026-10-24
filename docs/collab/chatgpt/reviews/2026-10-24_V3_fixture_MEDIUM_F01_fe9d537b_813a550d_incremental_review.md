# PSM-WMA V3 Flexible Episode Resume — MEDIUM-F01 fixture-only 增量复审

日期：2026-10-24（CST）。
**VERDICT：`APPROVE` — 仅限此精确 Formal Pair 的 MEDIUM-F01 fixture-only GPT 增量审核；DS_PRO 独立 CPU Gate 仍为 RED/NOT CLOSED。**
本轮未发现新增的严重阻断项。本结论不代表实际 GPU/模型/真实 RoboCasa 验收。

## A. Formal pair、冻结约束与增量范围

- **Formal Root:** `fe9d537b4a5f82c8ea72a4f8ce182fdcefac6790`。
- **Formal Child/Gitlink:** `813a550dab5d6b5b5e3be90d38bb97527956b4dc`（未变化）。
- **Previous fixture-only formal Root:** `dfb8a12140be7bf34584504c47df9042229f5bfb` / unchanged Child。其 MEDIUM-F01 评审 `REQUEST_CHANGES`：`docs/collab/chatgpt/reviews/2026-10-24_V3_flexible_resume_fixture_r3_dfb8a121_813a550d_review.md`。
- **Frozen Owner contract:** `cc7820bee1a73bd2bb2078cb7f00239944f66d37`。
- **已批准生产源代码 Root:** `6151e0712f28ace5d92258a8feb31fa8f1ee81c1` / same Child；原 GPT Production Code `APPROVE` 不继承成为 DS CPU PASS。
- **新源提交基线:** `976f77e7529a11dffef48ea0388ed6454a0b1209`。此次实际测试源码仅有 `tools/v3/queue_fixture_watchdog.py` 和 `tools/v3/eval_robocasa_queue_identity_test.py` 两个文件变化（其它 SESSION/TODO 记账）。GitHub Trees 独立核验 `scripts/` SHA `31ef1a90b6ef1a57ec0d7a5efe88ec8fd6fd06f0`、`configs/` SHA `deab6194fe4a9f766eec1f7f22c9d38966a34b12`、`third_party/` SHA `d01633d083298fc5245b5bc97677c5b297700c31` 及 Child Gitlink 均与生产源 Root `6151e071` 相同。
- 作者 Evidence/交接独立 docs HEAD：`eff79c162131d087b27fab0649d4e139c5e5002a`；不是 Formal Root。原 canonical Inbox 因128KiB上限已归档到 `docs/collab/chatgpt/archive/CODEX_INBOX_20261024_183154_fe9d537.md`，新 live `CODEX_INBOX.md` 以 archive SHA 引用历史。已核对 archive 的原 blob `9a242456d493f60d30298e7a4047a5e5fb5d4ceb` 与保留的旧 Inbox 原 blob 一致，旧结论未丢失。
- 本轮限于上一次 MEDIUM-F01 及其两个指定负例，不重复审查 Model Identity、Episode Resume、Local-TTT 或其它已 APPROVE 的生产代码。

## B. 上次 MEDIUM-F01 两条故障路径已闭合

### 1. 取证失败也进行有界回收 — CLOSED

**位置：** `tools/v3/queue_fixture_watchdog.py:99-185,188-197,199-315`。

- 超时/停滞终态先 `_freeze` 收敛已知子进程，随后执行可能抛错的 `_retain`；`_watch` 的 `except BaseException` 保存 `EVIDENCE_SNAPSHOT_FAILED`，**`finally` 在 `reason` 非空时调用 `_cleanup`**，不再由取证写入成功与否决定是否 SIGKILL/reap。
- 目录分配、证据观察等更早异常由外层 `watch()` 统一调用 `_cleanup`，报告失败；针对 `KeyboardInterrupt` / `SystemExit` 清理后保留原中断传播语义，不静默转成 PASS。
- 清理循环有10秒预算、冻结有界，保留 `cleanup_errors`、`cleanup_remaining_live`；失败记录优先写 `watchdog.json`，不成则尝试 `cleanup.json`，磁盘不可写时走 stderr/exception state。并不声称文件系统完全不可写时仍可成功落盘。
- **确定性负例：** `tools/v3/eval_robocasa_queue_identity_test.py:1296-1386,1391-1406` 强制 `watchdog.json` 抛 OSError、Evidence 目录分配失败和 KeyboardInterrupt，断言 root 退出、foreign 无误杀、原故障诊断存在，终态失败而非假成功。

### 2. 取证期间新生不同 session 后代重新发现与回收 — CLOSED

**位置：** `tools/v3/queue_fixture_watchdog.py:21-53,99-185`。

- `_freeze` 在复制前按 PID/start ticks 停止 root 及递归子进程，复制后 `_cleanup_owned` **重新枚举 /proc 并按 known root/descendant 身份追踪**；逐 PID SIGKILL 前复验 start ticks，避免使用旧 `rows` 快照一杀了之。
- 临时 Linux `PR_SET_CHILD_SUBREAPER` 配合只对已确认 PID `waitpid(pid,WNOHANG)`，不执行全局 `waitpid(-1)`；恢复原 subreaper 标志，清理结果记录 remaining 及 cleanup errors。不同 PGID 的已确认为本 fixture 的后代仍可回收，外部 foreign control 不在归属集合。
- **确定性负例：** `tools/v3/eval_robocasa_queue_identity_test.py:1296-1389` 在 `_retain` hook 中明确 `SIGCONT` 恢复已冻结 root，触发新建独立 session/PGID 的 child，并验证其出生在旧快照之后。回收后要求 child PID 不再出现在 /proc、无 child PGID、root 已回收、`cleanup_remaining_live=[]`、foreign 仍存活且不在 killed 集合。
- 这套边界以 Linux/proc/prctl 和可查询 PID/start ticks 为 fixture 环境前提；极端无法杀死的 D 状态进程只能有界报告 `cleanup_remaining_live`，不能宣称硬件内核层面绝对无进程残留。上述限定不影响本次正常可控制的确定性 F01 反例闭合。

### 3. 旧测试行为未被弱化

- 600s/900s 有限外层硬超时、180s media/core inactivity、120s 真 Task deadline，以及 FFmpeg 解码、C01/Local、Source/Reuse/SR 与三个健康 Task 的断言均未因本次整改放宽。
- `FixtureWatchdogTests` 现在共8项：原4项（持续进展、停滞、CPU busy硬上限、heartbeat排除）+2项 F01 +取证目录失败 +中断传播。测试只在必要时清理自己的控制进程，不访问真实模型、GPU或 RoboCasa。

## C. Evidence 及独立性说明

- Author handoff：`docs/collab/codex/reviews/2026-10-24_fixture_MEDIUM_F01_author_handoff.md`。
- Author Evidence：`docs/collab/codex/evidence/2026-10-24_fixture_MEDIUM_F01_author_cpu/`；包含 red/green 原始压缩日志、完整 JUnit、取证 tar、命令及迭代失败记录，之前修复但 Zombie 未被 reap 的中间失败被单独保留，不计为最终 PASS。
- 仓库最终 `junit.xml` 已读取：suite `tests=244`，实际 **172 `testcase` 元素**、成功 subtests 72、`failures=errors=skipped=0`，elapsed1661.249s。8项 Watchdog 相关 testcases 均可见且为 PASS。Ruff0.12.7 check/format + 16文件 syntax 静态证据作者报告 PASS。
- 作者 Red 2 failed 是将两项新增负例作用于上一版 Watchdog；最终 Green 8 passed。它们是**作者证据**。GPT 独立审核了新源码、测试断言、JUnit、Git Trees 与 Evidence metadata，**没有重新执行作者五组 CPU、没有读取真实 DCP/GPU/Kitchen、没有代替 DS_PRO 独立验收**。不能将其它旧 SHA 的168/164项累加。

## D. 正式 verdict 与下一 Gate

**`APPROVE`（Fixture-only MEDIUM-F01 CLOSED）。** 这是新精确 Formal Root `fe9d537b4a5f82c8ea72a4f8ce182fdcefac6790` / Child `813a550dab5d6b5b5e3be90d38bb97527956b4dc` 的增量 GPT Code Gate。生产源 `6151e071...` 的原 APPROVE 仍只绑定其原 Pair；本次没有生产代码修改与新的 Production Bug 结论。

下一步 DS_PRO 必须在 **clean detached worktree** 锁定本 exact Root/Child，检查根仓/Child clean 和 16文件源码哈希，然后独立运行冻结五组 CPU 测试（包含8个 Watchdog 控制与全部 Queue/Resume 测试）及 Ruff/format/syntax，保留原始 JUnit、完整命令、进程/清理及外部 Evidence。若 RED 立即停止、向 GPT 返回完整日志，不自行修改生产代码。DS CPU Gate 不能凭作者172+72自动变 GREEN。

**没有授权**真实模型加载、GPU/真 RoboCasa 运行、DCP或训练/Checkpoint更改、活动 G1/18-task 工作树调整、历史 Episode 改写或 iter12000 原有20集重新评测。真实执行授权仍由 Owner 单独决定。
