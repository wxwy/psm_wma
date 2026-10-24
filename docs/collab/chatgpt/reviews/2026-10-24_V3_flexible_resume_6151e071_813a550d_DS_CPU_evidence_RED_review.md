# V3 Flexible Episode Resume — DS_PRO 独立 CPU Evidence Gate 审核（RED）

日期：2026-10-24（CST）。
**EVIDENCE VERDICT：`REQUEST_CHANGES` — EVIDENCE-ONLY；DS CPU Gate 维持 RED，不关闭。**
**原 GPT Implementation Code Gate `APPROVE` 不变。** 本轮 formal pair 未变化，不重复技术 review，不判定生产源码有新 bug。

## 1. 审核对象、可获取证据及限制

- **Formal Implementation Root**：`6151e0712f28ace5d92258a8feb31fa8f1ee81c1`。
- **Formal Child / Gitlink**：`813a550dab5d6b5b5e3be90d38bb97527956b4dc`（未变）。
- Frozen Owner contract：`cc7820bee1a73bd2bb2078cb7f00239944f66d37`。
- 既有 GPT implementation review：`docs/collab/chatgpt/reviews/2026-10-24_V3_flexible_episode_resume_progress_r2_6151e071_813a550d_review.md`，该 precise pair 的 `APPROVE` 保留。
- 本轮新增信息是 DS_PRO 在独立 clean detached 工作树上的 CPU 测试报告，**不是新的 Implementation/design SHA 或新的生产 diff**；无需重审 6151 源码。
- **DS 自报执行状态**：Root/Child 和 15 文件 SHA 一致；Python3.13.11/pytest9.0.2、多人共享 CPU；`9 failed,162 passed,65 subtests passed`，2225.54s；JUnit 164 testcase elements / 6 failure elements；Ruff0.12.7 check、format、15文件 py_compile 全 PASS。测试已停止、无生产代码或真实模型/GPU/仿真修改。
- **DS 原始证据位置（来自提交报告，当前不可直读）**：`/mnt/data1/data_v2_0617/psm_wma_ds_cpu_6151e071_813a550d/{pytest.log,junit.xml,ruff_check.log,ruff_format.log,STATUS.json}`。当前 GPT 的容器中未挂载该目录，远程 Desktop Commander 设备离线。因此 **DS 的逐案例日志/原始 JUnit 尚未由 GPT 独立读取**，本次核对依据为 DS 报告文本、GitHub 真实冻结测试源码、作者 JUnit/历史基线。不能称 DS 原始日志已经独立验证。
- 远端 V3 在本轮取证时为 docs-only HEAD `04ab1ebdd23755ab3974c6f2716295d27aaa65ec`，并未出现另一个正式实现 Pair。

## 2. 独立判断：环境时序解释可信，但尚未证明

冻结测试源码 `tools/v3/eval_robocasa_queue_identity_test.py`：
- `:40-60`：默认测试子场景 watchdog 固定 **90.0s**，只有少量指定 late scenario 改用 180s；`:1162-1193`：`scenario()` 超时杀死新进程组，并调用 `self.fail`，`TemporaryDirectory` 退出会清理 `console.log`。因此 90.0s `TimeoutExpired` 只能说明**超过测试预算**，不能根据相同截断点断言纯环境延迟，更不能排除被杀进程中的第二次 Resume hang/deadlock。
- `:853-857,1443-1468`：`task_timeout` fixture 强制设置 `--task-wall-timeout-s 5` 并断言仅1 task失败、其它3 task正常完成。共享机器下，非目标 Task 若正常 CPU/media revalidation 总耗时也超过5s，可能按**生产正确 wall-clock 语义**被计为失败，从而出现 `task_failures=4`；这支持 fixture 预算敏感，但仍须凭原始 task/Job 时间证据确认。
- 作者冻结 JUnit 对应 top-level 方法耗时约为：normal 3 worker 组合89.167s；progress_resume50.952s；resume video/timeout 双场景105.232s；corrupt COMPLETE 三场景158.169s；resume_complete50.982s；faults多场景204.686s。DS 报告总时长2225.54s vs 作者1155.14s，约1.93倍，这与共享机器执行减速相容。**但 loadavg=33/192 cores 本身不足以证明 cgroup CPU throttle 或实际 I/O 竞争；需要额外观测。**
- DS 报告的9失败含8个固定90s watchdog截断子场景与1个task_timeout断言；多项是一个 unittest 方法下的 subTest 失败，不能直接称为9个独立生产逻辑缺陷。

## 3. 当前 Evidence-only blockers 与验收

### HIGH-E01 — 8 个 watchdog 场景未得到完成或有因果链的失败证据

- **位置**：`tools/v3/eval_robocasa_queue_identity_test.py:56-60,1162-1193,1213-1261,1639-1650` 等 Resume 场景。
- **原因**：90s 触发外层 watchdog、没有 `QUEUE_WITNESS` 与可保留的子进程 `console.log`；由于报告未提供子进程最后状态，无法独立区分 CPU/IO 迟缓、fixture 超时阈值不合理、或真实生产 Resume stall。
- **违约**：独立 CPU Gate 必须直接证明同一 formal Pair 的 complete Task/Resume/cleanup 行为，不能把未完成的用例计 PASS；Owner 要求异常不能伪装完成或吞掉资源错误。
- **验收**：DS 在精确同一 detached Pair 上，低干扰 CPU 时段先做 **read-only targeted rerun**；逐场景留存耗时、子进程 console/progress、进程存活/资源观测和 watchdog 原因（可在外部持久目录运行诊断命令，未对原测试作补丁时只算诊断而不算原 pytest Gate PASS）。随后必须以**未经修改的正式测试方法和原90s预算**跑出对应正常断言，才能在原 SHA 上关闭该证据；仍 RED 时交 Codex 做 fixture-only 稳定性/保留日志整改并生成新精确 SHA，经 GPT fresh review 后再交 DS。不能只把90改成任意大的超时即视为通过。

### MEDIUM-E02 — task_timeout 测试的5秒预算使非故障Task的成功前提未成立

- **位置**：`tools/v3/eval_robocasa_queue_identity_test.py:853-857,1443-1468`。
- **原因**：测试断言 `task_failures=1`，但同一全局任务 wall timeout=5s 可能让3个健康 Task在拥挤机器上也超时；DS 报告观测为4。
- **违约**：CPU Gate 要求对故障注入执行结果和基础设施错误归因有确定性证据，不能把健康 Task预算不足混作生产正确性回归。
- **验收**：DS 首先在低干扰/明确 CPU quota 的机器上复跑原 `task_timeout` 子场景并提供每Task wall、阶段、exit/cleanup、生产异常来源，证明仅目标Task超时而其余3个正常/15 Episodes 完成。若仍不稳定，由 Codex **只改测试 fixture** 标定预算与故障刺激，必须保持原测试所要求的目标超时、SIGKILL、独立 server回收、3健康Task成功和正式失败计数断言；新SHA独立审核。禁止修改生产超时语义来迎合测试。

## 4. 最小后续执行与停止条件

1. **保留 DS 原始证据**，供 GPT 进一步核验，特别是9失败 traceback/JUnit testcase/subtest、各 Worker 的最后运行阶段、CPU quota/throttle 和I/O负载。DS不修改源代码或活动训练/评测目录。
2. 在负载稳定/有明确可用CPU配额的 detached环境，仅复验前述失败方法及故障子场景；先做轻量场景如 `resume_complete` 和 `progress_resume`，再8-worker/多scenario；保持正式 fixture 原预算并给出真实退出/日志。不要把人工诊断脚本跑绿当作正式 Gate通过。
3. **若所有失败项在完全相同源码和不变测试预算下独立 GREEN**，原 formal pair 未变，只需该 Pair 的新 Evidence closure，不重新技术 review；如需改 fixture，即使 tests-only，新的 Root SHA 仍必须 fresh incremental review。
4. 待有直接可靠的 DS CPU 证据，方可考虑 Evidence Gate `APPROVE`；**当前结果必须保持 RED**，不得开始真实模型/GPU/RoboCasa/Checkpoint/训练或重跑已有 iter12000 20集。

## 5. 当前 verdict

**`REQUEST_CHANGES`（EVIDENCE-ONLY）；DS_PRO CPU Gate RED，非 source blocker 确认。**
既有 GPT Implementation `APPROVE` 仍有效，未获 DS Gate 关闭。本 verdict 只记录并要求证据/fixture定点复验，**没有授权生产代码修改或真实运行**。
