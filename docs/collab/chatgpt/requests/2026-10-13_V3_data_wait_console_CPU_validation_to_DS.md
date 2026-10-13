# DS_PRO — V3 进度行 data_wait 输出 CPU窄验收

**Date:** 2026-10-13
**New exact implementation Root:** `22b2ea294504503d367c6e8439d96c804d7a0df0`；**Child/Gitlink:** `50de2ab54f6d1a86b22fa0eaa511c9805011f54b`.
**Review:** `docs/collab/chatgpt/reviews/2026-10-13_V3_nw_prefetch_mechanism_and_data_wait_console_fix_22b2ea_50de2a.md` (`REQUEST_CHANGES` only for pending test evidence).
**范围:** 仅进度行将旧`data_prepare_ms`换为`data_wait_ms`，保证近零毫秒三位精度、nw0 None打印n/a、原JSONL持久化不变。

1. 在隔离checkout/worktree取Child精确`50de2ab54f6d1a86b22fa0eaa511c9805011f54b`，不能对当前运行中的`formal_verified_index_30k` checkout/pull/reset或重启，也不能碰原DCP/monitor JSONL/正式模型。保留新Child`PYTHONPATH`优先级，预置既有 `HF_HUB_OFFLINE=1` 避免已知全局teardown守卫假错误。
2. 用现有venv CPU-only执行：`python -m pytest -q examples/psm_wma_robocasa_formal_monitor_test.py`，`python -m py_compile examples/psm_wma_robocasa_formal_monitor.py examples/psm_wma_robocasa_formal_monitor_test.py`，`ruff check`同两文件。记录实际Git Root/Child/Child唯一2文件diff、退出码和第一失败栈。
3. 确认`nw=0/data_wait_ms=None`→`data=n/a`无ms后缀；`nw=8/0.024`→`data=0.024ms`，`nw=16/0.046`→`data=0.046ms`；原`data_prepare_ms=11500`不能混入console；`nan`→`n/a`；`format_progress`不改变输入Record，真实 `train_rank0.jsonl` Schema/采集路径不改。
4. 静态复查prefetch `iteration_wait_ms` reset/load_member/telemetry绑定的准确口径；`nw0`为None不是0；CPU-only无需新GPU计时/实验，DS勿改任何训练代码。
5. 交一次结果 `DS_PRO_V3_DATA_WAIT_CONSOLE_CPU_ACCEPTANCE_2026-10-13.md`，成功/失败有完整stdout摘要和SHA，并声明不影响当前训练。若失败停机反馈，不自行修改代码、不启动GPU/torchrun/新训练。

**补充性能诊断不属于这次代码 Gate**。DS的其它`nw8/16` forward/backward较慢机制仍是因果待证，若要深入提速先做三run配置/环境归一化及materialize子阶段profiling设计，不自动授权生产修改。
