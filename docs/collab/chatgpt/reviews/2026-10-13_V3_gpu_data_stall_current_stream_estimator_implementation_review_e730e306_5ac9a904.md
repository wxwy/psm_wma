# PSM-WMA V3 — Owner GPU因数据等待的`data=`定义：current-stream event gap新实现增量评审

**Date:** 2026-10-13
**Formal implementation target:** Root `e730e3063ee3638f0bafd79473f52a76f851c935` / Child+Gitlink `5ac9a904c46da658e1b3e0816d3a7d95ce99c945`.
**Diff base:** Root `948046a4cdb033e9d7ab3ce3975f71225981038c` / Child `b72eed79fa56fadd1115fcf93a06a8055ad3b3ed`.
**Verdict:** **`REQUEST_CHANGES / IMPLEMENTED_BUT_CPU_AND_REAL_GPU_MEASUREMENT_EVIDENCE_PENDING`**，仅因完整环境测试和真实H100测量准确性尚未验证；不是已发现训练数值bug。实现代码已提交，不能因为“显示一个数值”就声称精准GPU全设备idle。
**Code evidence:** `docs/collab/chatgpt/evidence/2026-10-13_V3_gpu_data_stall/2026-10-13_GPU_stall_instrumentation_source_diff_receipt_e730e306_5ac9a904.md`。
**DS handoff:** `docs/collab/chatgpt/requests/2026-10-13_DS_PRO_gpu_data_stall_CPU_Gate_and_optional_GPU_microtrace.md`。

## 1. 目标定义与旧指标不等价

Owner明确仅需通过`data=`回答“训练CUDA计算流是否因等数据而卡住，增加workers有没有减少实际stall”，不是CPU总数据准备时长。
- `data_prepare_ms`来自主线程`time.perf_counter`累计的各GA `prepare/materialize`阶段，可能与先前GPU计算部分重叠，不应直接归因 GPU idle。
- `data_wait_ms`仅`ThreadPoolExecutor` Future消费时的 host blocking，nw0无prefetcher所以None；GA0同步准备及两个GA materialize不在其中。
- 新字段`gpu_data_stall_ms`通过当前训练CUDA流event时间戳差估算当stream没有队列工作且CPU正准备数据的时间。输入阶段为`data_prepare`+每次`batch_collate`，其余不能被这个字段自动解释的延迟明确排除。即使未来显示`0ms`，也只是**所监测阶段训练stream没有可测量的数据相关gap**，不证明全H100 GPU活跃100%或Data完全隐藏。

## 2. Implementation diff 审核

- 新Child仅4文件（2 telemetry/monitor production和其各自CPU测试）；当前已有`GroupedPlanObserver.time_stage` rank0-only context用于host统计。对两个CPU-only数据阶段添加非侵入Event pair，`data_stall_sample_interval=1`默认每个optimizer迭代rank0采样。
- `_sample_gpu_data_stall()`查询event`end.query()`是否完成，不强制`torch.cuda.synchronize()`。只有全部pair ready且elapsed finite nonnegative才输出sum，反之`None`，用status区分`not_sampled/no_data_stages/pending_cuda_event/event_error/invalid_cuda_duration`。
- Event读发生在`post_commit`之后；采样导致开销不可武断归零，必须单独验证并报告。原每100步GPU compute events仍使用其已有`torch.cuda.synchronize()`，本次新数据stall路径**不新增**每步同步，但不声称整个训练没有其他同步点。
- JSONL additive fields `gpu_data_stall_ms/status/scope/sampled`保留 `data_prepare_ms`+`data_wait_ms`、旧Loss/Grad/Local telemetry；`format_progress`只在有`ready`数值时显示，任何None/pending不会造0。旧历史JSONL无新字段时显示n/a且`read_train_records`保持回读兼容。
- 没有改Group planner、Sampler、`num_workers`、Local memory、Forward/Backward/Optimizer、模型/Batch/Checkpoint，Root本次implementation提交只改Gitlink。未添加Job名称特殊条件。

## 3. Accuracy limitations与GPU Acceptance Gate

`gpu_data_stall_ms`当前**只是CUDA training current-stream gap estimator**，不等价实际GPU硬件全部SM idle，也不覆盖H2D传输、GPU其它stream活动、`gather_exact_window_same_index`及非标记主线程阶段。它是当前低侵入条件下最接近Owner希望每步看到的 proxy，但**必须先真实GPU profiling验证**；否则不能把`data=0.000ms`用来认定workers完全隐藏数据。
**GPU Gate 必须先有CPU通过，再经Owner许可独立低风险单GPU微测**（不能触碰Formal30k、Checkpoint或改变正在运行的GPU计算），用含模拟CUDA backlog与CPU sleep的两个例子对照Nsight/实际stream gap：
1. 先一段CUDA backlog≥CPU数据准备，gap应近0。
2. 先短CUDA backlog、CPU数据阶段更长，gap应约剩余CPU时间。
再做一份真正项目data stages/trace spot-check，确认Event当前stream与Model实际训练Compute stream一致、按GA0/GA1正确关联，观察`ready`覆盖率及Event开销。无同卡真实GPU Trace时不能给“精确全GPU stall”认证。
指标只在完成以上真实GPU验收后由GPT发`APPROVE`；缺少数据则`REQUEST_CHANGES`，不得擅自应用到正式训练进程。

## 4. perf问题判断与策略

此前DS nw0/8/16显示：nw0 host step wall≈40s，nw8≈60.7s，nw16≈61.9s；异步 raw prefetch Future等待≈0不能说明GPU无data stall。DS直觉“data_prepare≈11s必等于GPU idle”也不成立（要扣先前GPU backlog的重叠）。**现阶段保留`--num-workers=0`作为Formal基线**，不追加未经核实的性能优化，不会仅凭新proxy改变worker数或训练源Pair。

## 5. Formal运行安全

DS最后一次报告原Formal30k nw0正在iter1317+，本GPT无训练机实时进程视图。**绝不能在它的冻结工作树pull最新V3**；此新Child不是旧Job当前runtime字节相同；新Feature不自动部署或重启。无需打断现有训练观察旧指标，Future是否适用新Pair需要另外明确源/Resume安排。

**Status: `IMPLEMENTED_ON_V3 / CPU_MOCK_PENDING / GPU_TRACE_PENDING / FORMAL_UNCHANGED`.**