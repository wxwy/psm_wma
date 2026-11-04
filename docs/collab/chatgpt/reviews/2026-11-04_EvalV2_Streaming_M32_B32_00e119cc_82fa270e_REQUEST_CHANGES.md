# GPT 独立 Code Gate — Issue #17 EvalV2 Streaming M32/B32

**日期：2026-11-04**
**技术 Verdict：`REQUEST_CHANGES`**
**范围：仅当前精确候选实现／CPU Evidence 的独立源码审核；不授权 DS Gate、真实 GPU/H100、64 OS Sim、V3 promotion 或 G2 merge。**

## 1. Formal Pair 与上游基线

| 对象 | SHA |
|---|---|
| Root formal implementation | `00e119cc20cabe082974bd3495474b589c4b46b6` |
| Child formal implementation / Root Gitlink | `82fa270e8cdb76b3e1a4e94adf0c7ce2b497884e` |
| V3 root baseline | `ea0828c7d45a443cc74ae2582419f14e7782a17e` |
| Child baseline | `1069fe78841228cadbbfbe6afbd767eaed6225da` |
| Bookkeeping/evidence commit (not implementation authority) | `1c6f66ab14eabcd3d1637ebcf5af8d77c8c60188` |

通过 GitHub 实际读取 Root 及 Child commits/tree/compare，核实 Root gitlink 对应精确 Child，Root 比 V3 baseline ahead5、Child ahead1。独立候选未进入 V3。用户当前明确要求 **M/B Resume 一致性限制保持不变**。

阅读范围：Owner Issue#17 与 `docs/collab/chatgpt/requests/2026-11-04_V3_EvalV2_WorkConserving_M32_B32_Codex.md`；Codex handoff、minimal design、implementation notes；Root `config.py,cli.py,runtime.py,resources.py,startup.py` 实际 diff、Streaming CPU tests；Child `contract.py,scheduler.py,store.py,robocasa_{session,batch}_transactions.py,robocasa_transaction_client.py,action_policy_server_robocasa.py,eval_v2_{slot,worker,transactions,adapter}.py` diff/相关原代码；作者 `final_summary.json`、`gate.json`。

## 2. 当前 blocker

### HIGH / NEW-F01 — 并发 StartupBudget 释放预约时未重新计算其他 in-flight 预约的剩余负债

**Root：`scripts/robocasa_eval_v2/startup.py:26–65`，关键行56–65。**
[源码链接](https://github.com/wxwy/psm_wma/blob/00e119cc20cabe082974bd3495474b589c4b46b6/scripts/robocasa_eval_v2/startup.py#L26-L65)

**实际行为：** `reserve()` 在准入时用 `measured["rss_bytes"] + sum(self.pending)` 和逐GPU `measured owned_gpu_bytes + pending` 比预算；但是启动完成进入 `yield` 后仅执行 `self.measure()`。这个 `measure()` 只拒绝「实际RSS/VRAM已超过总上限」，**不会把其他尚未完成的 reservation 加回去**。随后 `finally` 无条件 `self.pending.pop(key)`，使当前启动超额使用的空间立即被视作已安全兑现，尽管剩余预约已与实际占用之和超出上限。

**可达并发交错：** 假定RSS上限100GiB、A/B各预留40GiB，两个预约在实际使用为0时均通过。A实际成长到70GiB、B仍为40GiB in-flight reservation。A的末尾 `self.measure()` 只看到70<100，正常退出并释放其预约；此时真实占用70+未兑现预约40=110GiB，超出预约上限，B可继续按有效预约启动。GPU预算具有同型缺口。另一个交错是测量完成与另一个 startup 的实际RSS增长之间，`version` 未变化，不足以为测量提供持续有效性；至少必须在完成/释放预约边界强制对账。

**违反冻结要求：** 新.streaming资源保护明确要求 `M32` 同时启动/切换时使用有界真实owned RSS/VRAM + outstanding reservation，不能在并发任务中超卖；本缺口直接破坏「有限资源准入」和启动后转移所有权的正确性。R04先前因RSS默认128GiB主动中断，恰说明本项目不能只在超预算之后被动停止。

**现有 Evidence 不足：** `tools/v3/eval_v2_streaming_tests/resource_test.py` 覆盖“静态零测量、两预约相加超过上限”和“单个预约失败释放”；没有覆盖“一个startup实际占用比其reservation高、另一个startup尚未完成”的并发完成/转移交错。作者846 PASS不关闭此缺口。

**可验收整改：**
1. 在 `StartupBudget` 完成启动、释放 reservation 前，保证 **owned actual + 其他全部 outstanding reservation** 的RSS和逐GPU VRAM预算仍然可核验；必须防止在核验与版本/预约状态变更之间出现无保护的窗口。超限 fail-closed，不得默默放行/无界等待；清理必须保证已注册owned进程终结、未完成请求不假DONE。
2. 增加确定性CPU并发测试，控制 A/B 预留与真实增长，覆盖两种资源（RSS和GPU）、两种完成次序、测量/提交交错、超限失败与恢复后的清理；通过实际公开 `StartupBudget.reserve` 而非只检查配置字段。
3. 保留原配置/Manifest/Session/Resume语义和已有正向测试，不能靠静默加大Owner预算、删掉资源门或仅改测试断言关闭此项。

## 3. 已核对、当前没有独立新增 blocker 的范围

- **M/B Resume：** Root `config.execution()` 仍在`execution`冻结M/B；`cli.py` dry-run/Resume与`identity.prepare()`完整 manifest 相等检查未删除；Child `contract.build_manifest()/validate_manifest()` 区分旧 `ROUND_SCHEDULE` 与显式 `STREAMING_SCHEDULE`；CPU CLI测试更改M后拒绝Resume。**本轮不建议改动或放宽M/B Resume一致性限制**。注意新streaming同时将RSS/startup budget也冻结到manifest；这比原legacy RSS可调策略更严格，若未来仍需“只调资源预算恢复”，须另行由Owner定义，不可本Gate静默变更。
- **64 Slot与调度：** Root `physical_slots()` 在显式streaming模式不再按18Task截断，Child `StreamingScheduler`以task/episode唯一key claim、每物理worker一个inflight，允许同Task不同EP并行；旧`RoundScheduler`仍使用原Barrier，未发现旧运行被静默切协议。
- **会话/Batch：** 新`streaming32` profile贯穿Server preflight、Client、事务Session owner与native microbatch cap；Session/Frontier、ACK与Result路由结构沿用原事务路径。作者CPU提供32Session/B32 carrier及Local fast-state隔离证据，但**不等价H100 B32显存/吞吐证明**。
- **生产边界：** 局部`worker_locks`和逐GPU Server锁减少旧`setup_lock`全局锁范围；Store metadata RLock 包围声明的短事务；closed gate/owned process registry/Session reset/媒体all完成边界未在已读diff中发现另外一个确认的HIGH。`none`跳过无用逐step frame callback；Model所需观测仍保留。
- **性能待测：** 新streaming在`runtime.py`每秒执行`identity.guard(...,source=True)`，涉及多次Git和Model校验；与真正64 Sim/H100下的启动瓶颈、GPU/CPU负载、Batch分布及实际等待比需DS后续测量，不依据CPU虚拟900集或R04短窗口推断加速倍数。
- **资源/Resume适用性：** 若用户期望像R04一样只提高RSS就能Resume，新.streaming将`max_rss_bytes`和`streaming_resources`一并冻结，属于新的部署语义，必须在正式投产前对照Owner需求确认；当前不将它误写成已经获准动态调整。

## 4. 作者 Evidence 位置与审核边界

[作者交接](https://github.com/wxwy/psm_wma/blob/1c6f66ab14eabcd3d1637ebcf5af8d77c8c60188/docs/collab/codex/reviews/2026-11-04_EvalV2_Streaming_M32_B32_Author_Handoff.md) 及 `artifacts/eval_v2_streaming_m32/2026-11-04_author_cpu`：`final_summary.json`显示 inference182、PhaseA278、PhaseB234、media89、streaming63，合计846/846 PASS；shell0，89源码unchanged。**这是作者自测记录，GPT本轮未独立执行完整846项或真实H100测试。** 64Sim/900 uniqueCore在作者报告中为CPU physics/process doubles；4 OS Sim只验证少量启动交叠及owned cleanup。不能替代DS独立CPU Gate/随后另行授权的GPU Canary。

## 5. Verdict 与下一步

**技术 Verdict：`REQUEST_CHANGES` — NEW-F01 HIGH production blocker + 相应Evidence缺失。**

仅整改并发资源预约完成/释放边界及必要回归；**禁止为修复此 finding 改变 M/B Resume 一致性限制**。Codex提交新的Formal Root SHA（如Child无变化应明确Child/Gitlink不变）后按本finding做独立增量复审。此前846 PASS及G2并行工作不被否定，但不能用来替代新Pair的审核。**本轮不授权合并V3、不授权DS独立验收的推进令牌，也不授权GPU/真实模型/训练/评测执行。**

该review属于docs-only审核记录，不改变Formal implementation pair；未来若该pair不变，禁止重复技术审核，只需处理审查记录与canonical ledger。
