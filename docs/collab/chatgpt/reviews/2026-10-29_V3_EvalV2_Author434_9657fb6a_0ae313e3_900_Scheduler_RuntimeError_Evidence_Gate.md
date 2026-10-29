# PSM-WMA V3 EvalV2 Phase B — Author Unified CPU 434 Attempt 1 Evidence Gate

**日期**：2026-10-29。**Formal Source Pair 未变**：Root `9657fb6ab590f228d760362e506d5dd1b626880a`，Child/Gitlink `0ae313e329d290fc6b8a50fda1112820fb7ac485`。此次只审核新的作者运行证据，**不重新给同一 Formal Pair 进行 Code Gate**。作者归档证据 commit `f65ac07d3fc3e56117dd9192ba77e4b58b5c9934` 是后续 bookkeeping HEAD，不是新的实现 SHA。

**正式 Evidence verdict：`REQUEST_CHANGES`（完整作者 Gate FAIL；新发生的 synthetic900 运行问题未定位）；DS 独立 Gate 维持 OPEN。** 以前 READY-only `APPROVE_CODE` 保持有效，原 F1/F2/F3、Store mkdir 和 Batch 架构不重复审核。

## 一、直接回读的原始证据

直接读取 GitHub `f65ac07d3fc3e56117dd9192ba77e4b58b5c9934` 内 `raw/gate.json`、`raw/phase_a_regression.xml`、`raw/phase_a_regression.log`、`derived/failure_traceback.txt`、`raw/failed_case/{summary.json,_internal/last_failure.json,_internal/scheduler/.../000425-000428.json}`、`derived/{result.json,triage_readonly.json,source_bindings.json,source_after_independent.json}`；审核非仅复述作者报告。

| group | 本次执行 | PASS | FAIL | 备注 |
| --- | ---: | ---: | ---: | --- |
| inference | 145 | 145 | 0 | 独立 Source/Gate 的 import/Ruff/format 也 exit0 |
| phase_a_regression | 113 | 112 | 1 | 第113例停于synthetic900测试，-x |
| phase_b_runtime | 0 | 0 | 0 | **未执行** |
| 总计 | **258/434** | **257** | **1** | 176项未执行；shell exit1/gate FAIL |

READY `test_stalled_actor_request_is_bounded_and_unrelated_process_survives`在本次完整运行中PASS，不是本轮失败。两侧三项身份与正式Root/Child/Gitlink一致；原 Gate `source_unchanged`在FAIL短路时不存在，但独立事后检查称53 watched SHA256均与before相等、Root/Child均干净。**这不是原Gate最终 source_unchanged=true 的替代**。

唯一真实FAIL：`tools/v3/eval_v2_production_tests/scheduler_test.py:61-100::test_900_exact_episode_major_dispatch_real_store_path_and_index_no_model_per_episode`。测试调用真实 `CpuSlotRuntime.run()` 之后在第95行要求 `error is None`，实际得 `RuntimeError('dictionary changed size during iteration')`。

- 运行期 summary：`valid=208`，`success=104`、`failure=104`，`pending=692`，`unresolved_process_errors=3`（Task03/05/07 `coordinator_stop`），`results_qualified=false`。
- Scheduler原件序列 `000425/426/427` 是第11轮三个worker的 `FINISH`，`000428` 为 `CANCEL`，其 `inflight=[]` 且 reason 为上述 RuntimeError。说明生产Runtime确实触发fail-closed停止，不能以部分有效结果代替合成900通过。
- 归档故障对象只保留了`repr(error)`。`derived/failure_traceback.txt` 是 pytest 外层 `assert error is None` 栈，**不包含异常在Runtime内生成的Python栈帧**。故本次具体抛错行尚未证实；不把作者候选归因自动升格为已确认根因。当前记录也不能证明既有有效 Core 被覆盖或污染。

## 二、最值得优先排除的生产并发窗口（未确认本次抛错行）

**Candidate C1：Root `scripts/robocasa_eval_v2/runtime.py:792-830` 进度诊断在 `:796` 直接 `for worker, claim in scheduler.inflight.items()`，每条循环中读取磁盘 `progress.json`；而 Child `cosmos_framework/evaluation/robocasa_v2/scheduler.py:158-166` 的 `RoundScheduler.finish` 由并发Worker调用，获得`scheduler._lock`后在`:165` `self.inflight.pop(...)`。进度遍历未持相同锁，读取或I/O期间字典可被另一线程修改，确实构成源码层面的并发风险，与本次异常文案相容。**

- 该 source risk 存在于未修改的生产代码，而非 READY-only 新Diff 或 Store.mkdir 新Patch。
- **证据边界**：原运行没有保存 `error.__traceback__`，无法仅凭异常字符串及 FINISH/CANCEL 时序证明抛错一定在 `runtime.py:796`，也不排除其他无锁字典遍历。此次将 C1 登记为 **HIGH-priority candidate，尚非已确认 throw-site**。禁止仅凭猜测修改生产源、吞掉 RuntimeError、跳过 synthetic900 或修改冻结D5语义。

## 三、精确下一步：只做一次单用例、外部Trace捕获

**建议Owner授权Codex一次限定范围的作者诊断**，在与本 Formal Pair完全一致的隔离CPU worktree，**只执行原失败的这一项 synthetic900 CPU test**，不执行434整套，也不启动真实900 episodes/GPU/RoboCasa/训练；新、外部Evidence目录，不覆盖原 FAIL。

不需要改生产或测试源文件。可使用外置Pytest插件/包装器，在`pytest_runtest_setup`后对`robocasa_eval_v2.runtime.Runtime.run`做**测试期间的透明包装（delegates exactly once）**：若返回`(report,error)`且error非None，则原样输出`''.join(traceback.format_exception(type(error),error,error.__traceback__))`并写入外部日志；随后原样返回同一tuple给原测试，**不吞错、不重试、不修改assert、不改变线程或调度行为**。插件与证据脚本位于worktree之外；Gate标准测试与冻结源码保持原样。必要时可用Python`sys.settrace`替代，但不能让instrumentation本身改变结果。交付：精确Pair、shell/JUnit、原始内部栈（或证明本次无法复现的记录）、OS/scheduler末尾事件、源码/工作树不变。

- 如果实际栈定位到 `runtime.py:796`，由Codex提一个**最小生产原子snapshot**整改：在与`RoundScheduler.finish`一致的scheduler锁下只复制`inflight`的items，再在锁外做磁盘进度读取/诊断；不能只`list(scheduler.inflight.items())`却不保护复制、不能改D5 round/commit/cancel authority，也不要关闭进度或忽略异常。新增能够控制并发交错的短回归，旧红新绿；交新Root/Child精确SHA后GPT只审窄Diff。
- 如果栈指向另一位置，**只按实际首错**提出对应最小修复；如这唯一诊断运行未复现，明确`INCONCLUSIVE`并保留原FAIL，而非报PASS/将全434重新启动。
- 生产候选修复的**新Formal Pair**先GPT fresh narrow Code Gate，再作者一轮完整CPU434（若新增测试总数上升以真实collection为准），再由DS_PRO独立执行一次完整CPU。中间不要重复完整Gate直到最小原因得到证据支持。

## 四、权限/归档边界

此次是相同 Formal Pair **新运行 Evidence Gate**，不是新的Code Gate。原 `APPROVE_CODE`不撤销，**作者 Unified CPU Evidence = `REQUEST_CHANGES`**；DS Gate仍未执行/关闭。禁止V3生产/Child合并、GPU/Cosmos/DCP/RoboCasa/Canary/900真实评测、训练/checkpoint/vendor改动；冻结Source和新证据不互相覆盖。

- 原 [JUnit](https://github.com/wxwy/psm_wma/blob/f65ac07d3fc3e56117dd9192ba77e4b58b5c9934/docs/collab/codex/evidence/2026-10-29_eval_v2_author434_attempt1_FAIL/raw/phase_a_regression.xml)
- [外层错误栈](https://github.com/wxwy/psm_wma/blob/f65ac07d3fc3e56117dd9192ba77e4b58b5c9934/docs/collab/codex/evidence/2026-10-29_eval_v2_author434_attempt1_FAIL/derived/failure_traceback.txt)
- [真实 Runtime 对活动调度字典无锁遍历](https://github.com/wxwy/psm_wma/blob/9657fb6ab590f228d760362e506d5dd1b626880a/scripts/robocasa_eval_v2/runtime.py#L792-L830)
- [Child 调度器并发变更同字典](https://github.com/wxwy/cosmos-framework/blob/0ae313e329d290fc6b8a50fda1112820fb7ac485/cosmos_framework/evaluation/robocasa_v2/scheduler.py#L158-L166)
