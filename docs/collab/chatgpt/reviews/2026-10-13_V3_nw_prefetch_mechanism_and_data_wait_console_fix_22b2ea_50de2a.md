# PSM-WMA V3 — nw多线程Prefetch性能复核 + Console data_wait计时输出修改：增量Gate

**Date:** 2026-10-13
**New implementation Root:** `22b2ea294504503d367c6e8439d96c804d7a0df0`; **Child+Gitlink:** `50de2ab54f6d1a86b22fa0eaa511c9805011f54b`.
**Previous Child:** `937066ffd90f2bf783ad4fbb4909e9c0b8922982` (前一轮Dense默认关闭+quiet-console CPU APPROVE，旧ChildSHA).
**Scope:** `NW_PREFETCH_MECHANISM_REVIEW_AND_PROGRESS_WAIT_METRIC_FORMAT`.
**技术裁决分离：** `NW0_CURRENT_FORMAL_BASELINE_RETAIN`；`ASYNC_CAUSAL_SLOWDOWN_UNVERIFIED`；Console代码 `SOURCE_DIFF_SCOPED`，**`REQUEST_CHANGES`（仅CPU测试Evidence缺失）**，暂不形成正式新代码实现Gate APPROVE。
**User-relayed DS telemetry:** `docs/collab/chatgpt/evidence/2026-10-13_V3_nw_performance/DS_PRO_2026-10-13_nw0_nw8_nw16_timing_owner_relay.md`。
**Owner明确授权的代码需求:** 用准确的`data_wait_ms`替换进度`data=`来源（当前`data_prepare_ms`），同步nw0自然`n/a`，不更改JSONL。
**CPU测试交接:** `docs/collab/chatgpt/requests/2026-10-13_V3_data_wait_console_CPU_validation_to_DS.md`。

## 1. nw机制：可被当前源码独立证明的范围

### num_workers并非全链路异步

`cosmos_framework/trainer/local_memory_grouped.py::training_step` 的`data_prepare`:
- nw0：GA0与GA1都`producer.produce(request) = materialize(prepare())`，完整同步。
- nw>0：GA0在主线程同步`producer.prepare`+同步`materialize`；该数据段结束前schedule GA1 raw requests，然后GA0`window.run_member`进行native forward/backward。worker threads在期间异步运行GA1`prepare`；GA1进入data段时只`load_member`+主线程`materialize`。因此预取**仅GA1 raw read部分**，T16的transform及Group/Local更新并未在线程pool中。
- `ordered_prefetch.py::load_member` `iteration_wait_ms`计量`future.result`+对应request/result校验的host耗时，`reset_iteration`每optimizer iteration清零；nw0无prefetcher记录None。`0.024–0.082ms`准确表达**GA1 raw Future被消费时的阻塞很小**；不能证明GA0 raw或整体data time为零。
- `data_prepare_ms`在主线程累积包括GA0同步raw读取、GA0/1`materialize`、GA1 Future、schedule和基础逻辑；不能仅凭`data_wait`将全部11s证明为`materialize`。

### nw8/16 +20s wall机制：**尚无因果证明**

- DS rank0观测：nw0 wall40.0s, nw8 60.7s, nw16 61.9s，主要增量落在`forward_ms`和`backward_ms`。说明在这些run中扩大prefetch线程**未加速端到端**，支持短期nw0基线。没有任何证据说明worker仍是CPU争抢的独立确定因：不同进程/run/迭代、外部共享GPU负载、缓存模式flags是否匹配、`native_forward_calls`/valid-consumer不同和任务分布等均可能混杂。
- 当前`_telemetry_stage`用`time.perf_counter`记录**host-wall**，其中可能包含GPU同步、FSDP/NCCL等待、调度争抢，非纯GPU kernel execution；已有`*_cuda_event_ms`每100步rank0短采样也只覆盖当前stream，需一起对齐。
- 与模式代码结合优先排查的假设：8rank×8–16 raw worker同时 `get_item`，每个Dense零视频6.375MiB、每rank单step raw累计约1.6–1.7GiB分配/零填充（非磁盘读量），可能冲击host DRAM带宽/NUMA/页分配/C++ torch线程；HF/Arrow metadata、Torch加载/page cache/allocator锁亦可能贡献。若开启Compact/Shared，数量级不同，**必须先确认三组run实际0/0或1/1一致**。
- 数据RAW和CPU内存并发不是H100 HBM3直接争抢；H100 SXM GPU本地HBM为3.35TB/s（NVIDIA官方），而CPU-side allocation、Host→Device拷贝、同步/通信和外部GPU负载属于不同路径。不能凭host forward变慢断言是PCIe、HBM或CPU某一个因素。

## 2. 推荐执行方案（未授权生产优化实现）

**P0 — 仅做按阶段Profile与matched对照，不贸然引入Async Materialize。**
- 核对3 run的Root/Child+Dataset/Index、`PSM_V3_COMPACT_CACHED_VIDEO`/`PSM_V3_SHARED_EPISODE_CACHE`真实有效值、`native_forward_calls`、valid_consumers、任务覆盖、其它GPU作业/CPU负载及同源checkpoint/迭代。若任一不同，不以现有20s因果结论申请代码优化。
- 不动训练功能时，在隔离诊断或GPU允许的短诊断中将`data_prepare`分为GA0 `prepare`、GA0/GA1 `materialize`、`_transform`(含VideoResize、TextTokenizer等)、`Segment.validate`、GA1 future wait、collect/pinned copies；统计每index p50/p95。观察CPU time、RSS/内存带宽、soft/hard page faults、NUMA亲和性以及 torch intra/inter-op线程。
- 匹配GPU阶段对照`forward_ms/backward_ms` vs 定点CUDA事件时间、NCCL超时/等待、其他负载，避免直接把host wall作为GPU计算时间。只有归因后再设单变量、少量(<=3条件 nw0/8/16)实验。

**P1 — 优先消除确定性CPU重复工作，后谈流水化。**
- 按profiling识别`materialize`中的纯确定性几何/已缓存latent摘要/重复prompt元数据/zero frame产生与Resize等，考虑数据构造中的不变部分离线预计算或batch化；任何共享大视频缓存不得让可变张量跨sample alias。需要保持raw15/video/latent/CFG和按slot/index的payload ABI、输出值严格对照、数据集源校验不减。
- 对`_transform`存在的随机CFG/dropout/prompt jitter，强制保持原主线程顺序与RNG状态；只有证明纯函数/确定性部分，才允许移入worker或ProcessPool；不能让独立worker任意消费torch/python RNG并改变序列。Local fast state只能在训练线程消费/更新，不能在异步准备阶段提前commit或污染复原。
- 进程池或GA跨步异步`materialize`由于复制巨大Dense视频、序列化与RNG风险大，**当前不是首选**。若未来必须做：一member边界、有限inflight/无跨迭代猜测、request/order身份验证、abort-drain、strict resume+DCP/Local parity、外部GPU负载变化监控；与当前Dense合同的完整数值比对是单独严格Gate，旧D1 OFF/ON gradient failure不能被忽略。

**工程结论:** 正式运行保持`--num-workers 0`，未授权对正在运行的Formal Job注入profiling或替换数据路径。加线程在本次被测run中没有性能收益，但真正因果瓶颈需profile确定。

## 3. 直接实现的Console展示范围

- 受Owner明确请求，`examples/psm_wma_robocasa_formal_monitor.py::format_progress`中`data=`现绑定`data_wait_ms`，不再展示`data_prepare_ms`。为避免 `0.024–0.082ms`按整数毫秒显示0，独立`_milliseconds`保留**3位小数**；`None/nonfinite`显示**`n/a`且不附ms单位**，避免错误 `n/ams`。
- `nw0`有同步data_prepare CPU处理但`data=n/a`（正确地表示「无异步Future wait」，**绝不表示data cost为零**）；原完整JSONL仍有`data_prepare_ms`、`data_wait_ms`、`data_wait_reason`以供归因，JSONL Schema、TelemetryJournal持久化/原raw日志不变。
- 添加`examples/psm_wma_robocasa_formal_monitor_test.py`新参数化CPU单测（nw0的None, 0.024,0.082,0.0,nan和仍有11.5s prepare，不应该打印11,500ms）；不碰`_telemetry_stage`/`prefetch`/`data`计算、模型、loss、Local state、Optimizer、DCP、flags、Hyperparam、config_digest。
- 远端旧Child`937066ffd90f2bf783ad4fbb4909e9c0b8922982`→新Child`50de2ab54f6d1a86b22fa0eaa511c9805011f54b`仅改上述**2个文件**；Root实现commit`22b2ea294504503d367c6e8439d96c804d7a0df0`仅gitlink改动。源码检视符合小范围Owner要求。
- **当前限制：** ChatGPT未在完整项目CUDA/LeRobot虚拟环境执行CPU pytest+ruff；因此本次代码差异**无生产阻断发现但tests Evidence仍缺**。按独立审核规范 verdict `REQUEST_CHANGES`（仅验收Evidence不足，非生产代码已知bug），收悉DS在隔离工作树执行测试和SHA证据后即可关闭，不重复Review前一Pair的Dense/quiet-console Gate。

## 4. 当前运行保护

- DS报告目前真实训练run `ab50c423-e042-421c-8c94-ff26ac9dfafa` 已nw0在iter1317+，此为用户转交证据，GPT不可见实时训练状态。不能在训练锁定Worktree `git pull`以应用新显示功能，不应因日志小改动停止Formal30k。
- 旧版本进程不热更新；正式后续切换实现Pair前必须由Owner确认时机与当前DCP来源。CPU代码Gate审批不等于新Pair训练Resume授权。
