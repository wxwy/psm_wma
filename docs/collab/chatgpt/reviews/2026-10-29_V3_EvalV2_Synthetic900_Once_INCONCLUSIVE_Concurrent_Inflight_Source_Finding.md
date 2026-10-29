# V3 EvalV2 Phase B — synthetic900 单次诊断 INCONCLUSIVE 与明确源码并发风险的处置

- 日期：2026-10-29
- **Formal Root**：`9657fb6ab590f228d760362e506d5dd1b626880a`
- **Formal Child / Root Gitlink**：`0ae313e329d290fc6b8a50fda1112820fb7ac485`
- **本轮源代码 Formal Pair 未变**。证据/bookkeeping commit：`f92adc66f3a5f41d5bb71f2c3260ac27ab74fb14`（相对前次FAIL证据 `f65ac07d3fc3e56117dd9192ba77e4b58b5c9934` 新增诊断资料；不替代实施 SHA）
- **Evidence verdict：`REQUEST_CHANGES`（原完整作者434 Gate FAIL且DS独立 Gate尚未开始）。单次诊断判定：`INCONCLUSIVE`（没有复现原异常，不能形成其抛错行鉴定）。**
- 之前 READY-only Code Gate `APPROVE_CODE` 持续有效。本轮仅审新的运行证据和直接相关的生产源码并发安全，不重复 Code Gate、不重审 F1/F2/F3/Store/Batch 架构。

## 1. 独立回读的实际证据

从 GitHub exact `f92adc66f3a5f41d5bb71f2c3260ac27ab74fb14` 读取：
- `docs/collab/codex/evidence/2026-10-29_eval_v2_synthetic900_diagnostic_once/raw/{diagnostic.xml,runtime_return.json,shell-exit.txt,instrumentation.json,source_before.json,source_after.json,wrapper_restored.json,console.log}`
- `instrumentation/{capture_runtime_traceback.py,run_once.sh}`
- `derived/result.json`、README
- 上轮作者完整 Gate 原始 FAIL 仍保持 `f65ac07d3fc3e56117dd9192ba77e4b58b5c9934` 中的独立记录，不予替代。

确证：
- 精确 Root/Child/Gitlink 匹配；诊断前后 Root/Child 都干净、**53/53 watched SHA256 完全相同**，已归档旧失败证据 SHA256 前后相同（校验目录中的哈希对象）。
- 单次原 `scheduler_test.py::test_900_exact_episode_major_dispatch_real_store_path_and_index_no_model_per_episode`：JUnit **1 PASS，0 failures/errors/skips**，shell exit0，测试 wall 293.75s。
- 诊断插件 `Runtime.run` 原方法原样调用**恰好一次**，`(report,error)` 的 `error=None`，实际回报 `valid=900,success=450,failure=450,pending=0,results_qualified=true`，50轮/900 dispatch synthetic witness 在原日志中存在，wrapper已恢复。插件只在 `run()` 返回后采样异常对象，未重写生产方法或测试断言。
- 因无错误对象，**没有新内部 traceback**；本轮无法判定此前 `RuntimeError('dictionary changed size during iteration')` 的精确抛错行。合成900是CPU模拟边界，不是正式900 RoboCasa episodes或真实GPU验证。
- 该单例 PASS **不能与上轮已FAIL的作者完整434 Gate拼接**：上轮保留 **257 PASS/1 FAIL/176未执行**，`Gate.status=FAIL`；独立DS未启动。作者诊断本身也不等于DS独立验收。

## 2. F4-P1 — HIGH 可达生产并发缺陷（源代码确认，原FAIL归因仍未确定）

**生产位置（真实 Formal Root）：** `scripts/robocasa_eval_v2/runtime.py:792–830`，进度日志诊断在约每5s运行：
```python
for worker, claim in scheduler.inflight.items():
    # loop body reads progress.json from disk; may release GIL
```

**并发写入（真实 Formal Child）：** `cosmos_framework/evaluation/robocasa_v2/scheduler.py:158–166`，Worker线程在 `RoundScheduler.finish()` 内持 `scheduler._lock` 后调用 `self.inflight.pop(claim["physical_worker"])`；`Runtime.run_slot()` 成功时直接调用 `scheduler.finish(claim)`（Root `runtime.py:615`）。

因此，在协调器无锁迭代 `dict_items` 且循环体执行文件读取时，另一个线程可以在已持有写锁的情况下移除元素。**读方未持同一锁，写锁不足以阻止迭代期间改变大小；此处是本身可达的真实生产源码竞态**，可能让本应非权威的进度输出触发异常和整个评测停机。

**必须区分：** 这一无锁遍历风险**在代码层面成立**；上轮第11轮 `dictionary changed size during iteration` 的归因**尚未精确确认**，因为当时只存 `repr(error)`，此次诊断无法复现。不能把“来源风险源码确认”误写成“事故抛错行已经证实”。

**严重级别：HIGH**：进度诊断是可达的生产执行路径，潜在无关故障可中断 Episode-major 的正常评测，导致整个正式运行不可达完成。暂无证据说明既有合法Core被覆盖、fast state跨episode泄漏、科学SR被伪造；仍须按 fail-closed 保持原取消/Resume权威。

## 3. 当前选择：不再追随机复现，提议一次最小源修复 + 确定性旧红新绿

同一 Formal Pair 不再重复审代码；建议 Codex 在隔离新 Root 中**仅针对确认的 `runtime.py:796` telemetry迭代做最小同步**。不改变任何 Child/Batch/Store/Local-TTT/训练/任务调度/断言/正式证据。

预期安全形态：
```python
with scheduler._lock:
    inflight_snapshot = tuple(scheduler.inflight.items())
for worker, claim in inflight_snapshot:
    # original read(progress.json), diagnostics stay outside lock
```

- `scheduler._lock` 是 `RoundScheduler.finish` 用的同一锁；快照复制受它保护；**不得**只使用裸 `list(scheduler.inflight.items())` 而不锁住复制，也不得在锁内做文件I/O或网络调用。
- Snapshot可稍旧，但这只是**非权威进度日志**；不得用它重新定义 Core/SR/D5、调用 `scheduler.finish/commit/cancel`，或遮蔽异常。
- 只在必要时补一个同目录生产测试中的**短且确定性的并发交错回归**：旧源在进度迭代时由另一Worker调用真实 `scheduler.finish()` 会得到字典变化错误；新源通过，同时原调度锁约束/round barrier/core/cleanup保持。不能用单纯短合成900的随机“没复现”替代红绿证据。
- 该整改是对独立可证实的生产源码缺陷修复，**不声称100%修复了先前FAIL的未知throw-site**；新候选即使完成其红绿回归，也需作者完整434（新增case则以上实际collection计数）再DS独立434验收。若完整 Gate 再有其它真实首错，必须提供内部异常stack、只定位最新首错，不循环盲跑。

## 4. 权限与步骤

- **当前Formal Pair仍未变；Evidence Gate依旧`REQUEST_CHANGES`，诊断 `INCONCLUSIVE`。**
- 后续仅：Codex最小Root生产竞态修复+针对性回归并提交**新 Root SHA、同 Child/Gitlink** → GPT按新 Pair仅审增量 → 作者一次完整CPU Gate → GPT审核作者证据 → DS独立一次完整CPU Gate。
- 不授权直接合并V3/Child生产，不做新的多轮诊断、真实GPU/Cosmos/RoboCasa/DCP/EGL/900、训练/Checkpoint/Vendor操作。其他已批准项维持原状。
- 此报告仅 V3 docs-only落盘，不是新实施版本，也不批准正式实验。

## 5. References

- [诊断归档（本轮）](https://github.com/wxwy/psm_wma/tree/f92adc66f3a5f41d5bb71f2c3260ac27ab74fb14/docs/collab/codex/evidence/2026-10-29_eval_v2_synthetic900_diagnostic_once)
- [原始作者完整Gate失败归档](https://github.com/wxwy/psm_wma/tree/f65ac07d3fc3e56117dd9192ba77e4b58b5c9934/docs/collab/codex/evidence/2026-10-29_eval_v2_author434_attempt1_FAIL)
- [Root无锁遍历](https://github.com/wxwy/psm_wma/blob/9657fb6ab590f228d760362e506d5dd1b626880a/scripts/robocasa_eval_v2/runtime.py#L792-L830)
- [Child并发finish/popup](https://github.com/wxwy/cosmos-framework/blob/0ae313e329d290fc6b8a50fda1112820fb7ac485/cosmos_framework/evaluation/robocasa_v2/scheduler.py#L158-L166)
