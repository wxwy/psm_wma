# V3 — GPU data stall current-stream telemetry: commit + source diff evidence

**Date:** 2026-10-13
**Owner request:** 确定控制台 `data=` 是 GPU 因数据准备阻塞而无法继续训练计算的空闲时间，不接受将 `data_prepare_ms` 或 `data_wait_ms` 重新命名作为GPU等待。
**Previous implementation:** Root `948046a4cdb033e9d7ab3ce3975f71225981038c`, Child/Gitlink `b72eed79fa56fadd1115fcf93a06a8055ad3b3ed`.
**New implementation:** Root `e730e3063ee3638f0bafd79473f52a76f851c935`, Child/Gitlink `5ac9a904c46da658e1b3e0816d3a7d95ce99c945`.
**Source commit:** https://github.com/wxwy/cosmos-framework/commit/5ac9a904c46da658e1b3e0816d3a7d95ce99c945
**Gitlink-only root implementation commit:** https://github.com/wxwy/psm_wma/commit/e730e3063ee3638f0bafd79473f52a76f851c935
**Scope:** 新加rank0 CUDA stream event gap estimator + console display + CPU mock acceptance tests only. GPT 未访问正在运行的Formal30k服务器、没有GPU profile原始trace，没有跑真实H100。

## Exact code scope

Child `b72eed79fa56fadd1115fcf93a06a8055ad3b3ed`→`5ac9a904c46da658e1b3e0816d3a7d95ce99c945`只修改4个源：
- `examples/psm_wma_robocasa_corrected_telemetry.py`：observer每迭代rank0在主线程纯CPU数据阶段`data_prepare`和`batch_collate`前/后（现有`_telemetry_stage` context）在当前CUDA stream插入CUDA Event对。前一GPU工作未完成时，开始event在GPU排队直至前一stream工作结束，后event在CPU完成相关stage时才提交；差值是**训练CUDA stream在该数据阶段发生的gap估算**。结束时`Event.query()`+ `Event.elapsed_time()`无新增同步；未完成事件返回`None,pending_cuda_event`，不得假造0。
- 按优化步汇总新增JSON字段`gpu_data_stall_ms`, `gpu_data_stall_status`, `gpu_data_stall_scope`, `gpu_data_stall_sampled`。其它已有`data_prepare_ms`、`data_wait_ms`、`data_wait_reason`、forward/backward/optimizer指标保留原含义与记录，记录只在Optimizer成功提交后写。
- `examples/psm_wma_robocasa_formal_monitor.py::format_progress()`：原主线程prepare计时字段`data_prepare_ms`改为只显示`gpu_data_stall_ms`且仅status=`ready`时打印。数值>=1s用s，<1ms保留三位小数，readiness失败/未采样/旧JSONL记录一律`data=n/a`而不是0。
- `examples/psm_wma_robocasa_corrected_telemetry_test.py`与`examples/psm_wma_robocasa_formal_monitor_test.py`：新增fake CUDA Events/wiring、非阻塞query/pending、禁用、不同数值/状态和不改变入参回归。

**源码静态 Diff可追溯:** https://github.com/wxwy/cosmos-framework/compare/b72eed79fa56fadd1115fcf93a06a8055ad3b3ed...5ac9a904c46da658e1b3e0816d3a7d95ce99c945
**Root source diff:** gitlink `cosmos-framework` only。无训练生产参数、Local state、FSDP、DCP、loader顺序、optimizer、config digest、缓存flag变化。

## 关键安全边界

- CUDA Event的`elapsed_time`**不等于整张H100 GPU 全部计算引擎的真实 idle time**；它仅测一条当前CUDA stream两个event marker之间的墙钟型GPU时间戳间隔。其它stream（如NCCL）、CPU提交路径及GPU外部作业可能同时活动；也不能完整覆盖`gather`、H2D等未被包围阶段。所以字段严格标注 `rank0_current_cuda_stream_gap_during_cpu_data_prepare_and_batch_collate_estimate`，是性能诊断proxy，不是“绝对GPU闲置”的物理测量。
- 每步rank0 event约多条，虽不插入显式`torch.cuda.synchronize()`，仍可能有插桩host/stream开销或影响rank0与其它rank进程的相对时序。上线必须先量化CPU脚本行为和实际GPU overhead/GPU Trace近似对照，不能将mock测试当作真正测量成功。
- 本次没有自动部署到运行工作树：DS报告的Formal30k当前nw0 run与新Child不同；不能在训练机live checkout做`git pull`，也不以本docs变更替代真实Formal固定Pair验证。

**Review:** `docs/collab/chatgpt/reviews/2026-10-13_V3_gpu_data_stall_current_stream_estimator_implementation_review_e730e306_5ac9a904.md`。
