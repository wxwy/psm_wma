# Batch C r2 — 完成等待夹具整改及定向交接

日期：2026-10-23（Asia/Shanghai）。作者：Codex。**状态：REVIEW；作者定向 CPU 通过，尚非 GPT 增量批准或 DS 整体 CPU Gate PASS。**

## 1. 新旧身份及修改范围

| 对象 | 身份 |
| --- | --- |
| 新 test-only Implementation Root | `ee53cbe1c25ff174f0d92a92e51e901ec6436c18` |
| 开发基线 V3 HEAD | `4a1ab5faf54adfff8be460f850f132c86a3a46d7` |
| 原 Batch C r2 production Root | `a4b22b929175e462b6a8db57ad2abee7e220dd37` |
| Child / Gitlink，未变 | `c9f21040f462a114d597fc83773cb9b6a9e96214` |
| Vendor 可重建产物，未变 | `1ac174585293ed998ffc9cf73e47439798cf6f6c` |
| 旧测试 Git Blob | `b38b238a6f15f7f70df039ecade54490165b77b9` |
| 新测试 Git Blob | `a29513aa10ccfac01a3dab2283f1d3afbc910cf7` |
| 新测试 SHA256 | `1cbe51e37b0174f4303a0685b6a7a142183787d96ad262b0c4c080105a8236b3` |

执行 Owner/GPT 指令：`docs/collab/chatgpt/requests/2026-10-23_Codex_BatchC_fixture_wait_budget_and_DS_delta_recheck.md`。新 Root source commit 只有一个测试文件及 SESSION/TODO；后续报告/Evidence/Inbox 是文档提交，不替代新 Implementation SHA。

唯一代码变更：`tools/v3/eval_robocasa_queue_identity_test.py`。生产 Queue/Process/结果校验、Child、Vendor、训练超时、Local-TTT、G1 Config/Identity/DCP 均未变。没有实施另一次六项扫描的整改。

## 2. 夹具行为变化

旧等待基于真实 Summary，但限12秒；`init_faults` 在等待前追加，超时先抛 AssertionError，原定 mkdir/log_open OSError 未发生。DS原181通过+2失败+72subtests按原 Pair 保留，不重计为本新 Root 的全量通过；原生产 C01/C02 不重审。

新 `_raise_after_completed` 继续读取实际 Queue 的 Summary，要求目标20/15条、4/3个各5条且无错误的 Task、无 Worker 错误，以及对应 COMPLETE/INCOMPLETE 状态。满足前不记录注入，也不构造成功结果。

- 测试完成等待上限120秒；相关场景外层 watchdog180秒。等待截止还受 scenario 起点+watchdog−30秒约束，为清理和报告留余量；其他场景仍是原90秒。生产 Task/Episode/request/terminate 参数不变。
- 等待 witness 记录起点、截止、完成时刻、实际 trial 数、Task 集合和 Summary 状态。
- 真正 `raise OSError` 后在 except 中记录类型/消息/注入时间，再原样 re-raise；只有这时才更新 `init_faults`。断言完成时刻≤注入时刻，且 Queue 保存准确 OSError 内容。
- 原 mkdir/log_open 的20条、4Task、4Server+4Sim、RC1、INCOMPLETE、sr=null、Worker1准确错误及无残留检查全部保留并加强。late-launch仍等待15条，不改成20。
- 新慢正例：健康首个合成 Sim 等待 guard 开始后故意延迟13秒；随后仍由**实际完成条件**触发异常，不是睡满13秒即注入。实际等待22.816954秒，超过旧门槛；观察20条完成后才注入指定 mkdir OSError。
- 新负例：Summary始终不存在，共用 guard 在0.15秒预算后抛专用 `FixtureCompletionTimeout`；没有创建/伪造 Summary，无 OSError/`init_faults` 记录。另有30秒子进程 watchdog兜底。这验证等待前置条件永久未满足时的有界失败，不声称执行真实卡死 Simulator。

## 3. 作者定向验证

只执行以下5项，最终 JUnit **5 passed，0 failure/error/skip**，32项 deselected，53.98秒。只统计最终最小 diff 的一次结果，不累计中间重复执行。

| 测试/场景 | 关键观察 |
| --- | --- |
| `test_worker_mkdir_failure_after_healthy_worker_completes_all_tasks_is_preserved` | 实际20条先完成，随后准确 mkdir OSError；4Server/4Sim，错误保全 |
| `test_worker_log_open_failure_after_healthy_worker_completes_all_tasks_is_preserved` | 同上，准确 log_open OSError |
| `test_server_launch_error_after_other_tasks_does_not_disappear` | 实际15条完成后启动 OSError，保留原15条语义 |
| `test_slow_healthy_worker_exceeds_old_wait_before_real_initialization_fault` | 13秒真实慢刺激；实际等待22.816954秒后观察20条，再注入 OSError |
| `test_completion_wait_timeout_cannot_inject_or_fake_completion` | 前置条件超时、无 Summary、无注入，子进程有独立 watchdog |

所有场景父测试继续验证无 `robocasa-gpu-*` 线程，已启动 Server 均退出；正常错误路径调用原生产 OwnedProcess 清理。合成 HTTP/PID、Git、真实微型媒体及原有解码验证在 CPU 执行；模型、RoboCasa Kitchen/物理运行和 Local 算法边界为原显式 doubles。

- Python3.12.14，现有 `/workspace/.venvs/psm-wma-cpu/bin/python`；不冒称与 DS 的Python3.13.11同环境。
- Ruff0.12.7 check、format --check 使用既有 `cosmos-framework/.ruff.toml`；AST语法及 diff-check通过。没有全仓 Ruff/pytest，也未重跑原148项/整套183项。
- 空 CUDA、HF/Transformers offline；缓存、JUnit、日志全部外置至 `/tmp/psm-v3-batch-c-fixture-wait-20261023`。未读取真实数据、Checkpoint 或活动 G1 工作树，未启动 GPU、真实 Action Server 或仿真。

完整最终日志/JUnit、实际命令、旧新 Blob/源 SHA256、test-only patch 和精简时序 witness：[Evidence](../evidence/2026-10-23_BatchC_fixture_wait_author_cpu/)。`source_checks.json` 对新提交的测试字节进行绑定；`gate.json` 明确仅 AUTHOR_DELTA_PASS。

## 4. 请求的复核和 DS 最小复验

请 GPT 只审核新 Root/原 Child 的上述 fixture diff 和证据，不重新审核不变的生产 C01/C02。通过后 DS 在新 clean detached worktree 自行拉取精确新 Root/Child，只运行上述5项与该测试文件 Ruff/格式/语法，不重新安装 Vendor或重复旧通过套件。

```bash
"$CPU_PYTHON" -m pytest --noconftest -c /dev/null -p no:cacheprovider -q -s \
  tools/v3/eval_robocasa_queue_identity_test.py::QueueIntegrationTests::test_worker_mkdir_failure_after_healthy_worker_completes_all_tasks_is_preserved \
  tools/v3/eval_robocasa_queue_identity_test.py::QueueIntegrationTests::test_worker_log_open_failure_after_healthy_worker_completes_all_tasks_is_preserved \
  tools/v3/eval_robocasa_queue_identity_test.py::QueueIntegrationTests::test_server_launch_error_after_other_tasks_does_not_disappear \
  tools/v3/eval_robocasa_queue_identity_test.py::QueueIntegrationTests::test_slow_healthy_worker_exceeds_old_wait_before_real_initialization_fault \
  tools/v3/eval_robocasa_queue_identity_test.py::QueueIntegrationTests::test_completion_wait_timeout_cannot_inject_or_fake_completion \
  --junitxml="$EVIDENCE/fixture_delta.xml" > "$EVIDENCE/fixture_delta.log" 2>&1
```

DS返回真实新 Pair、前后clean、命令/RC/JUnit、完成先于指定异常的 witness、无残留线程/自有进程。失败时停止，不改断言或生产超时。旧181+72记录与新定向结果分开，最终整体 CPU Gate 由 GPT 根据组合证据裁决。

Codex提交后停止；无新 GPU、真实 Kitchen/模型、正式Benchmark或G1操作授权。源同步阻塞已关闭，旧离线转运要求已由2026-10-23环境补充取代。
