# Codex / DS — Batch C r2两项时序夹具失败的最小整改

日期：2026-10-23。
审核依据：`docs/collab/chatgpt/reviews/2026-10-23_BatchC_r2_DS_CPU_acceptance_fixture_timeout_disposition.md`。
原Formal Root `a4b22b929175e462b6a8db57ad2abee7e220dd37` / Child `c9f21040f462a114d597fc83773cb9b6a9e96214`。
DS现场181顶层测试+72subtests已通过，2失败；不是183项全部PASS。源码已由DS自行成功拉取，停止此前离线交付要求。

## Codex：仅修复测试，不改生产超时

允许范围：`tools/v3/eval_robocasa_queue_identity_test.py` 的 `wait_completed()`、`fail_initialization()`、共用该等待的fixture、对应最窄新增测试和Evidence。不要修改 `scripts/` 生产实现、Child/Gitlink、模型/Local-TTT/Vendor/训练资产。

实际问题：wait_completed已轮询真实summary，但12秒预算在DS环境耗尽；预期mkdir/log_open OSError尚未注入，只有fixture AssertionError。不能降低到仅断言RC1/INCOMPLETE，也不能把“已准备注入”视为“已经注入”。

验收合同：
1. 等到健康Worker真实完成指定20 trials之后，才能注入指定OSError。可使用有界完成事件或现有summary条件轮询，取消“健康流程必须12秒内完成”的隐含性能要求。单纯sleep固定时间不等价。
2. 等待预算要和外层scenario watchdog协调，给清理/保存报告留出余量；保留有界失败与自有进程组回收，禁止无限等、修改生产Task/Episode timeout或抢占训练。
3. 记录completion满足时的trial数、观察顺序/单调时间和确实执行的异常类型/消息。`init_faults.append()`位于guard之前不能独自作为故障已发生的证据。
4. 原postconditions不得删改：20条完整记录、4个Task、4次Server+4次Sim、RC1、INCOMPLETE、sr=null、worker_errors含指定worker1 mkdir/log_open异常、无残留线程/自有进程。
5. 加慢健康Worker正例（故意延迟/受控时钟，证明不依赖原12秒门槛）和未完成负例（永不到目标则有界失败且不能假注入/假PASS）。测试同步不应伪造生产summary或mock掉要验证的错误传播。
6. 共用helper的late_launch_failure目标为15 trials而非20，必须保留该语义，运行相邻用例回归。无需开展全仓测试/新增框架。
7. 提交新Root实现SHA、旧/新test blob、最小diff、作者正反例命令/JUnit/退出码、Ruff/格式/语法。Child保持原c9f21040，不制造无意义Child提交。仅docs提交不是新的实现Pair；test-only源码提交是新Pair，交GPT窄范围复核。

## DS：修复后只做定向复验

此时不要继续重跑原失败fixture，也不要本地改断言或改12秒常量。
收到经复核的新Root后，自行从V3拉取到新的隔离clean工作树，Child按Gitlink固定；不更新活动G1工作树。
使用原已验CPU环境，CUDA_VISIBLE_DEVICES=''、离线依赖、Evidence/缓存外置；先验证精确新Root/Child和clean状态。

最小回归包含：

```bash
"$CPU_PYTHON" -m pytest --noconftest -c /dev/null -p no:cacheprovider -q -s \
  tools/v3/eval_robocasa_queue_identity_test.py::QueueIntegrationTests::test_worker_mkdir_failure_after_healthy_worker_completes_all_tasks_is_preserved \
  tools/v3/eval_robocasa_queue_identity_test.py::QueueIntegrationTests::test_worker_log_open_failure_after_healthy_worker_completes_all_tasks_is_preserved \
  tools/v3/eval_robocasa_queue_identity_test.py::QueueIntegrationTests::test_server_launch_error_after_other_tasks_does_not_disappear \
  --junitxml="$EVIDENCE/late_worker_delta.xml" \
  > "$EVIDENCE/late_worker_delta.log" 2>&1
```

另执行作者新增的等待同步/有界timeout正反例，实际名称依新提交列出。只需对实际改动文件做Ruff0.12.7、format和语法检查，不重跑148项或整套183项，不重新安装Vendor。

返回新的实际Pair、命令/RC、真实OSError注入顺序witness、JUnit、无残留进程线程、前后clean。已通过旧181+72记录保留其原SHA；新增证据单独绑定新Root。

失败停止并报告，不削弱测试求绿。成功后回GPT关闭本测试/Evidence blocker；真实环境/模型/仿真放行仍由Owner另行决定。慢动作统计、G1训练与本任务无关，全部保持不动。