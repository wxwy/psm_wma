# DS_PRO — V3 新 Child `937066ffd90f2bf783ad4fbb4909e9c0b8922982` CPU定点验证请求（不可动运行中训练工作树）

**Date:** 2026-10-12
**新 Implementation Pair:** Root `b159f45906f7261d028aecc226ab7f2bb9807eb9`, Child/Gitlink `937066ffd90f2bf783ad4fbb4909e9c0b8922982`.
**Implementation Review:** `docs/collab/chatgpt/reviews/2026-10-12_V3_console_only_progress_dense_defaults_implementation_review_b159f459_937066ff.md`.
**范围:** 默认Dense/非Shared、默认屏蔽train JSON控制台回显；不包括训练/性能/Checkpoint或D1数值一致性。

执行方DS_PRO只做**CPU-only**，必须与仍然指向旧 `444c232b976e80ac68cde9e7370e73b9f6410f0e`/`e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c` 的训练服务器正式工作树隔离。

1. 在独立CPU sandbox/worktree取得精确 Child `937066ffd90f2bf783ad4fbb4909e9c0b8922982`，不能 `git pull`原锁定训练仓、不能触碰 `formal_verified_index_30k`、源DCP、运行进程。
2. `PYTHONPATH=<新Child独立路径>`，使用依赖齐全的现成虚拟环境执行：
   - `python -m pytest -q cosmos_framework/data/generator/action/datasets/robocasa_exact_window_cached_sft_test.py`
   - `python -m pytest -q examples/psm_wma_robocasa_formal_monitor_test.py`
   - 对3个变更production文件和2个tests运行`py_compile`、如可用运行ruff（不要因已有文件原先风格偶有不同误报此次新增行）。
3. 核对两个开关unset时为Dense/非shared，显式1/1时为Compact/Shared，非法值仍失败；含一次真正dataset封装/Video尺寸和缓存reader source身份确认。
4. 核对JSONL具有原完整字段/仍能 read_train_records；console只有progress/checkpoint/error/warning，没有完整train JSON；日志断开不会改变已成功Optimizer Commit或破坏记录。
5. 核对生产代码没有 Job-name/phase 特判，训练参数、`config_digest()`及Formal原受限Root没有变化。记录实际测试子仓 SHA、退出状态、失败第一栈、是否有新文件写到原正式目录。
6. **任何FAIL即停止并上报**；不要DS擅自修代码/自动重试或启动 GPU。成功汇总：`DS_PRO_V3_DENSE_DEFAULTS_CONSOLE_CPU_ACCEPTANCE_2026-10-12.md` + logs SHA，交GPT审查实施Gate。

此前Torchrun `--tee 3` 是原生参数，Owner已取消专用命名Logger wrapper，**不要让cx继续实现以前的老request**。
