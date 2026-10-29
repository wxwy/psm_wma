# PSM-WMA V3 EvalV2 Phase B — F4-P1 进度字典并发快照窄增量 Code Gate

**审核日期：**2026-10-30（作者受控测试与交接于2026-10-29归档）

**Formal Code verdict：`APPROVE_CODE`（仅 F4-P1 Root 进度 telemetry 快照与确定性 CPU 回归）。** 并非完整作者 CPU / DS CPU / 原 synthetic900 事故根因的最终验收。

| 身份 | 精确 SHA |
| --- | --- |
| 新 Formal Root | `a139b5a35877a79e0a56c2208f3002f731972b11` |
| 未变 Child/Gitlink | `0ae313e329d290fc6b8a50fda1112820fb7ac485` |
| 上一 Formal Root | `9657fb6ab590f228d760362e506d5dd1b626880a` |
| 作者证据 bookkeeping HEAD（非 Formal Root） | `1193e4106026f314ce89ef6ed433a6291e572b47` |
| 候选分支 | `v3-eval-v2-inflight-snapshot-20261029` |

## 1. 版本/范围：实际远端 SHA + GitBlob 验证

读取 GitHub `a139b5a35877a79e0a56c2208f3002f731972b11` commit 与 compare `9657fb6ab590f228d760362e506d5dd1b626880a...a139b5a35877a79e0a56c2208f3002f731972b11`，确认只有两个 Root 文件发生变化：
- `scripts/robocasa_eval_v2/runtime.py`，+3/-1，GitBlob `d0184f4b41de3f4b1e33fa06b9c326d27bd00e85`。
- `tools/v3/eval_v2_production_tests/runtime_progress_test.py`，新增108行，GitBlob `372e4a3aca2987debbe24d48f974860639b7ea72`。

Root `HEAD:cosmos-framework` = `0ae313e329d290fc6b8a50fda1112820fb7ac485`；Child、Batch、LocalTTT、Store、D5 authority、已有F1/F2/F3和READY正式源码未改变；`1193e4106026f314ce89ef6ed433a6291e572b47`是后续原始测试证据提交，不能代替新 Formal Root。证据 `raw/static/proof.json` 两项 GitBlob 与实际 GitHub Commit 文件完全一致，Green 54/54 watched SHA256 在执行前后不变，Root/Child工作树干净。旧RED下原生产Git SHA正确、测试文件哈希与GREEN一致，但测试文件当时为旧 worktree 的 untracked 文件、SESSION/TODO另有未提交文档变动；因此旧RED是受控源代码行为见证，不宣称它是一次完全干净的正式 Gate。

## 2. F4-P1 — 源码问题 CLOSED

旧版 Root `runtime.py:796` 在每5秒进度日志中无锁遍历 `scheduler.inflight.items()`，循环里读取 `progress.json`；Child `RoundScheduler.finish()` 对同字典在 `scheduler._lock` 下 `pop`。读方未持同步锁，实际字典迭代在另线程删除元素后能抛出 `RuntimeError('dictionary changed size during iteration')`，将非权威 telemetry 变成评测中断。

新 Formal Root 代码仅：
```python
with scheduler._lock:
    inflight_snapshot = tuple(scheduler.inflight.items())
for worker, claim in inflight_snapshot:
    # 原progress读取和状态构造均保持在锁外
```

此锁正是 `RoundScheduler.finish/dispatch/cancel` 使用的锁。只在锁内执行短暂复制，所有路径 I/O、progress fallback、日志内容、Core/Resume/D5/SR逻辑保留；诊断快照允许轻微旧值，不是权威状态。未引入新的锁、线程、延时或吞错机制，也未重写 frozen scheduler semantics。核查无需再扩架构或扫无关 code。

## 3. 合同到直接行为 Evidence

直接读取 `1193e4106026f314ce89ef6ed433a6291e572b47` 下 `raw/red/{console.log,junit.xml,execution.json}`、`raw/green/{console.log,junit.xml,execution.json}`、`derived/red_traceback.txt`、`raw/static/{proof.json,check_0.log,check_1.log,check_2.log}`、`instrumentation/run_focused.py`和实际新回归代码：

- **RED：** 将完全相同的新增回归临时应用于旧 Root `9657fb6ab590f228d760362e506d5dd1b626880a`，实际旧 runtime SHA `230fadd591075b4879c3fd4ab1d86031c162ebd5cf3ec975baec9dc073082261`；单例 shell exit1/JUnit 1FAIL，真实 `Runtime.run` 内部栈定位 `scripts/robocasa_eval_v2/runtime.py:796`。 `V2_PROGRESS_SNAPSHOT_WITNESS` 记录 `copy_held_writer_lock=[false]`、两实际 Worker `GPU0/GPU1` 在进度文件 I/O 中完成、错误为 `dictionary changed size during iteration`。
- **GREEN：** 新 Root `a139b5a35877a79e0a56c2208f3002f731972b11`，同一回归SHA `e8a905f1829fbfa6f34136be8adcdd482002a0e14831bdf81b9ebf7e6c8cd73e`，`copy_held_writer_lock=[true]`，两个真实Worker同样在 progress I/O 中完成，error=None、2个有效Core、合格summary、两个Slot CLEAN、DISPATCH按LogicalPlan、FINISH2、ROUND_BARRIER1、无CANCEL。新回归和另两项既有native/Core/Resume及多Worker round barrier测试共 **3PASS/0FAIL/0ERROR/0SKIP**，shell exit0。
- 回归通过实际 `CpuSlotRuntime.run`、`RoundScheduler.finish`，受控 `Barrier/Queue` 强制写入发生在读方进入 progress I/O 后，`Inflight.items` 记录是否已持调度器现有锁；没有 fake Batch2、跳过Core或替换真正 `finish` 的状态突变。锁跨I/O时会让10s有界等待失败；裸未加锁拷贝也会因未持锁见证失败。
- 作者静态日志显示 Ruff check/format 2文件、diff-check、syntax2、AST限定变更全部 exit0。这些日志是作者原件，GPT未在本环境独立执行pytest/Ruff。
- 作者早期 `fixture_debug_not_RED_proof` 属夹具调试失败，已单独归档，**不算有效旧红证据**；当前采用 `raw/red` 的真实throw-site RED。

**Evidence界限：** 已对特定生产风险建立确定性 contract→behavior→source，F4-P1增量源码可以正式批准。但此前完整作者434中 `synthetic900` 随机FAIL的真实抛错行从未保留内部栈，后续单例一次PASS/INCONCLUSIVE。因此本批准**不声称**旧434 FAIL已被完全归因或后续完整434/435必过。

## 4. Gate 与后续唯一工作

- **此 Formal Pair F4-P1 Code Gate：`APPROVE_CODE`，源码 finding CLOSED。**
- **作者完整 CPU Gate：NOT_RUN on this new Pair**；原 `257PASS/1FAIL/176未执行` 为另一旧 Formal Pair 的历史Evidence，不继承为本次PASS。
- **DS_PRO独立CPU：NOT_RUN on new Pair，Evidence Gate仍 OPEN/REQUEST_CHANGES。**
- 只授权作者在干净精确 Root `a139b5a35877a79e0a56c2208f3002f731972b11` + Child `0ae313e329d290fc6b8a50fda1112820fb7ac485` 的隔离worktree，使用全新外部Evidence目录，执行**一次现有统一 CPU Gate**：
```bash
python tools/v3/run_eval_v2_batch_b2_cpu_gate.py \
  --root-worktree '<CLEAN_FORMAL_ROOT_WORKTREE>' \
  --expected-root a139b5a35877a79e0a56c2208f3002f731972b11 \
  --expected-child 0ae313e329d290fc6b8a50fda1112820fb7ac485 \
  --evidence-dir '<NEW_EXTERNAL_EVIDENCE_DIR>'
```
- 预期总数 **435 = inference145 + PhaseA256(原255+新1) + PhaseB34**，实际 collected 为准；要求 shell0、`gate.json.status=PASS`、全组0fail/error/skip、精确identity/import origin、`source_unchanged=true`，并保留完整JUnit、OS原始行为见证。作者一次完整Gate PASS → GPT仅证据核查 → **DS独立新干净Pair一次完整CPU Gate** → 后续Owner单独批准合并/真实1GPU M2B2 Canary/正式900。
- 不授权V3/Child生产合并、真实Cosmos/GPU/RoboCasa/EGL/DCP/900、训练/Checkpoint/Vendor，也不要求再跑随机合成900诊断或新增架构。

## 5. 关键来源

- [Formal Root Diff](https://github.com/wxwy/psm_wma/commit/a139b5a35877a79e0a56c2208f3002f731972b11)
- [回归与原始 RED/GREEN 证据](https://github.com/wxwy/psm_wma/tree/1193e4106026f314ce89ef6ed433a6291e572b47/docs/collab/codex/evidence/2026-10-29_eval_v2_inflight_snapshot_F4_P1)
- [Child调度锁](https://github.com/wxwy/cosmos-framework/blob/0ae313e329d290fc6b8a50fda1112820fb7ac485/cosmos_framework/evaluation/robocasa_v2/scheduler.py#L152-L169)
