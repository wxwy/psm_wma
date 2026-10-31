# V3 No-TTT Issue #13 默认 Progress-only 控制台 — 独立增量 Code Gate

**日期：2026-10-31；正式 Verdict：`APPROVE_CODE`（仅本精确隔离候选 Root 日志/启动器与定向 synthetic-shell Gate）。**

- **Formal Root** `24dbb677f7a60eeab6934c44352c7e00fa6d9b36`；**Child/Gitlink** `0ae313e329d290fc6b8a50fda1112820fb7ac485`（保持Canonical原值）。与任务基线 V3 Root `3332d1825de8778e3d6dbb7e9ba98cbffff487c6` 比较，唯一1个新implementation提交；后续Code Handoff docs SHA `705567eb779493b0f188c62a3d720443eaaa0577` **不是**本轮Formal。
- Owner的冻结要求：No-TTT标准训练默认终端仅显示Rank0 `[CorrectedV3][progress]`，所有Rank/Loader/错误stdout+stderr完整落盘；不得让日志控制层改变torchrun命令、计算、DCP、Checkpoint/Resume或现有C12200 A/B测试。来源：`docs/collab/chatgpt/requests/2026-10-31_V3_NoTTT_Default_Progress_Only_Console_Codex_Implementation_Order.md`。

## 1. Contract → 实际代码 → Evidence

| Contract | 独立源码核验 | 直接Evidence | 判定 |
| --- | --- | --- | --- |
| 默认Progress-only，不需用户开关 | 两份Root标准入口 `scripts/train_v3_matched_no_ttt*.sh` 只将原`exec torchrun`套入 `exec python3 scripts/no_ttt_console.py OUTPUT_ROOT JOB_NAME -- ...`；原训练argv/env/cwd/参数不变。`scripts/no_ttt_console.py` 只接受`[CorrectedV3][progress] `作为完整行，其他行不往console送 | `test_real_standard_launcher_default_split_preserves_original_fake_training_argv_and_env`，`test_entire_training_command_and_key_env_equal_frozen_original`含4/8 GPU与fresh/resume fake命令 | PASS |
| 完整原始stdout/stderr优先落盘 | 包装器用`subprocess.Popen(stdout=PIPE,stderr=STDOUT)`，通过`_write_all(log_fd,raw_chunk)` **先写全部字节，再**过滤完整Progress行；用`mkstemp`在`OUTPUT_ROOT/_launch_logs/JOB_NAME/`为本次生成独立0600 raw log，不提前创建Trainer job namespace；既有`TelemetryJournal` JSONL/raw不改 | 测试normal progress、Rank1、Loader JSON、checkpoint、stderr Traceback、超长/碎片/非法UTF8、无progress、连续resume不覆盖；运行示例只是假训练，不冒充真实训练 | PASS |
| 正确失败传播、真实Ctrl+C/SIGTERM与owned cleanup | wrapper保留child退出码、非零时显示失败/日志路径/末尾字节；log open/write/fsync/close异常fail-closed；Linux `/proc` + `PR_SET_CHILD_SUBREAPER`只扫描自身descendants并用PID starttime guard受控回收跨session rank，不杀foreign；正常运行不在每步扫描/proc、每步不fsync | 失败7、模拟ENOSPC/fsync/selector失败、SIGINT=130、SIGTERM=143、忽略TERM/late child、foreign survival及所有PID回收测试 | PASS（限定合成进程）；Linux `/proc`及系统python3是明确生产环境前提 |
| No-TTT以外源隔离与先前A/B不变 | 子Gitlink未变；生产仅Root两个launcher+一个stdio helper；训练脚本既有命令内容未改、LocalTTT/EvalV2/model/DCP未改；没有启动真实gpu或改旧正式job | root baseline→Formal Diff; `audit.json`(author)与独立Root Tree/Gitlink；不继承另一Issue#12性能Gate | PASS |

## 2. 原始Evidence独立审计

- Codex作者 Evidence 在 `docs/collab/codex/evidence/2026-10-31_nottt_issue13_progress_console_author_cpu/`（Handoff docs commit `705567eb779493b0f188c62a3d720443eaaa0577`）。GPT已直接从GitHub读取真实`final/junit.xml`：**49 unique testcases，0failed、0error、0skipped**；作者报告为21新增+28旧launcher，未把另外两份raw demo加入测试数。
- GPT对该Evidence bundle的`artifact_sha256.json`用独立SHA256实现复核 **3/3 关键原件** `final/junit.xml`、`final/gate.json`、`audit.json`：哈希逐字节匹配。`final/gate.json`确认`bash -n`两入口、ShellCheck0.10.0、Ruff check/format0.12.7、pytest均exit0，synthetic CPU-only。没有使用真实Torch/GPU/DCP，也没有本地重跑这套作者测试。
- 代码中的`_Output.poll`首发无过滤丢字节、`_cleanup`后代回收、unique log/exit code运行控制直接读取审查；本Gate未发现目前Root这三处生产修改的具体blocker。

## 3. Formal verdict与边界

**`APPROVE_CODE`**（Issue#13新Root Formal及unchanged Child，仅默认console日志输出代码+synthetic-shell证据）。不自动授权合并Canonical V3、重启真实NoTTT、修改正式C12200 Checkpoint或做GPU实验。

后续若与NoTTT Async Lazy canonical移植合流，届时形成**新的组合Formal Root/Child Pair**，需确认该Pair继承本日志启动器与已批Lazy child两组精确blob，并对4GPU/8GPU shell入口与async positive-worker runtime做少量合成集成验证；不是要求重跑旧49、43、58、301或matched GPU A/B。

本Review与`CODEX_INBOX.md`一起落盘后才生效；后续docs-only review commit不得替代这里的implementation SHA。