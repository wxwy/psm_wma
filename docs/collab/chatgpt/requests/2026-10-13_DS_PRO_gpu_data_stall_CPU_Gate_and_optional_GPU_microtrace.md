# DS_PRO — V3 GPU data-stall estimator 定点CPU Gate及后续可选GPU microtrace

**Date:** 2026-10-13
**新Implementation Root:** `e730e3063ee3638f0bafd79473f52a76f851c935`
**Child/Gitlink:** `5ac9a904c46da658e1b3e0816d3a7d95ce99c945`
**Review:** `docs/collab/chatgpt/reviews/2026-10-13_V3_gpu_data_stall_current_stream_estimator_implementation_review_e730e306_5ac9a904.md`
**目标:** 让 `[CorrectedV3][progress] data=`仅显示rank0训练CUDA stream在数据`data_prepare`及`batch_collate`CPU-only阶段的gap估计，不再冒充CPU总数据耗时或异步Future等待。它不是严格全GPU idle测量。

## 1. 立即可做：CPU-only (无GPU训练)

独立目录checkout精确Child `5ac9a904c46da658e1b3e0816d3a7d95ce99c945` 并验证Root Gitlink；**禁止在运行中的Formal30k源码工作树git pull/reset/checkout**，不要操作原job/DCP/stream或启动torchrun。

既有venv中设置`PYTHONPATH`指向新Child与`HF_HUB_OFFLINE=1`，运行：
```bash
python -m pytest -q examples/psm_wma_robocasa_corrected_telemetry_test.py examples/psm_wma_robocasa_formal_monitor_test.py
python -m py_compile examples/psm_wma_robocasa_corrected_telemetry.py examples/psm_wma_robocasa_corrected_telemetry_test.py examples/psm_wma_robocasa_formal_monitor.py examples/psm_wma_robocasa_formal_monitor_test.py
ruff check examples/psm_wma_robocasa_corrected_telemetry.py examples/psm_wma_robocasa_corrected_telemetry_test.py examples/psm_wma_robocasa_formal_monitor.py examples/psm_wma_robocasa_formal_monitor_test.py
```
检查mock`Event.record/query/elapsed_time`配对、ready数值、pending→None无CUDA synchronize、rank0-only、no-stage或disabled→n/a、异常不影响Optimizer提交、record原有data_prepare和data_wait语义/字段无变、JSONL可读、`format_progress`只有ready才有`data=`数值。任何FAIL报告第一堆栈，DS不要自行修改生产代码或GPU训练任务。

## 2. GPU真实性 Gate：另行Owner授权后（不是本CPU许可的一部分）

本地独立、小型单GPU GPU timeline测量，**不能运行完整训练，也不接管正在运行的Formal30k**。选一张获准使用的H100以同一stream:
- 模式A：在CUDA current stream排队足够长的GPU工作，比CPU数据`time.sleep`长，Event起止间应接近0。
- 模式B：先短CUDA backlog，再长CPU `time.sleep`，Event起止应近似CPU剩余未重叠时长。
- 若Nsight Systems/NVTX可用，同步出`CPU数据阶段/GPU kernel/stream event`时间线做交叉核对；不允许将模拟时间直接当成真实Formal GPU stall统计。
- 再匹配正式模型真实`data_prepare/batch_collate`与GPU实际compute stream的record/stream身份，确认per-step`ready`覆盖率、event成本与打断训练风险，才能申请替换正式训练的console`data=`。所有现场原始环境/signal/profiling结果分别报告。

## 3. 输出

`DS_PRO_V3_GPU_DATA_STALL_CPU_ACCEPTANCE_2026-10-13.md`，包含测试SHA、pytest/ruff/py_compile结果，失败第一栈，变更4文件、原Formal job未受扰证据。CPU全绿后GPT仅可关闭CPU gate，**不得宣称GPU真实性通过**；没有明确Owner许可不启动GPU/profiler/torchrun。

**范围外:** 不改nworkers、不改TTT/Local state/Checkpoint/模型、不把旧`data_wait_ms`篡改成GPU wait、不为监控改写当前正式训练工作树。
