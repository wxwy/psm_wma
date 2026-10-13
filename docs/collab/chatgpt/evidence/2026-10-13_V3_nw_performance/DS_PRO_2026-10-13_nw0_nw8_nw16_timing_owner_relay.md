# DS_PRO → GPT — V3 Formal30k num_workers 性能诊断与data_wait显示诉求：用户转交证据

**日期:** 2026-10-13 UTC
**证据范围:** DS_PRO只读提取 `monitor/train_rank0.jsonl` 数据，由Owner转交GPT。GPT已直接审核固定Child源码，但**未直接读取DS训练服务器本地JSONL、rank日志、GPU profiler或实时进程**。结论需要区别用户转交观测与源码可证机制。
**原监控runs:** `f88c457c` (nw0), `81d8861f` (nw8), `4727c46d` (nw16). DS称当前生产run `ab50c423-e042-421c-8c94-ff26ac9dfafa` 已恢复nw0并在iter1317+健康。

## Rank0 DS稳定窗口观察

| metric | nw0 iter1340–1344 | nw8 iter1303–1307 | nw16 iter1302–1305 |
|---|---:|---:|---:|
| step_wall_s | 40.0s | 60.7s | 61.9s |
| data_prepare_ms | 11.5s | 10.9s | 12.3s |
| data_wait_ms | None | 0.024–0.082ms | 0.030–0.046ms |
| forward_ms | 13.5s | 24.0s | 24.8s |
| backward_ms | 11.9s | 15.8s | 15.8s |
| batch_collate_ms | 17ms | 30ms | ~30ms |
| batch_transfer_ms | 125ms | 270ms | 330ms |
| other_host_overhead_ms | 1450ms | 1900ms | 1900ms |

`num_workers` 是V3专用 `raw` prefetch thread pool，不是旧的JointDataLoader num_workers/进程。DS认为`raw` Future基本无需等待，但主线程`materialize`约11s，`nw8/16`的forward/backward wall慢20s，推测线程CPU争抢；提出保留`nw0`基线、做transform profile和独立流水线方案。并明确 Owner 要求 `[CorrectedV3][progress]` 中`data=`从`data_prepare_ms`改为`data_wait_ms`，`nw0`显示`n/a`，nw8/16保留小数毫秒精度。

## 独立源码复核对DS归因的精确边界

- `cosmos_framework/trainer/local_memory_grouped.py`: `data_prepare`含GA0同步`producer.prepare`和`producer.materialize`、GA1 `prefetcher.load_member`+同步`producer.materialize`。异步仅提前`GA1` raw；只有GA0 materialize后才schedule GA1，后与GA0`window.run_member`计算重叠。
- `cosmos_framework/utils/ordered_prefetch.py`: `ThreadPoolExecutor`, `iteration_wait_ms`是每次`load_member` 从`time.perf_counter()`起，到`future.result`和身份验证完成的累计耗时，而不是整段raw生产/transform总时长；sync`nw0`没有prefetcher，因此None。DS数据中`data_wait`极小只证明GA1消费等待极小。
- `cosmos_framework/model/generator/mot/robocasa_exact_window_local.py`: `producer.prepare`逐个raw`getitem`，`materialize`逐index `_transform`并装配visual/action/evidence/SegmentBatch；VAE latent来自cache，不在线编码。
- **不能从原证据证明**全部11s=materialize，GA0 sync prepare也计时；也无法从host forward/backward wall直接证明瓶颈=CPU争抢，未记录每段CPU profiler/GPU events对应值、外部GPU占用、相同数据成员/任务及两个缓存flag的跨run一致性。PCIe/HBM/NCCL/Page cache根因仍未被独立定位。
- 机制性潜在CPU流量：Dense`[3,17,256,512]` uint8零视频每个6.375MiB；T16/B8/GA2每Rank约256–272 raw item调用，对应单Rank约1.594–1.693GiB**累计分配/零填充**，8 rank约12.75–13.55GiB/step，不等于同时驻留内存或实际cache磁盘字节流量；真实模式和物理带宽等待仍待采样证实。

**实现目标:** `22b2ea294504503d367c6e8439d96c804d7a0df0` / `50de2ab54f6d1a86b22fa0eaa511c9805011f54b`，只修改进度格式函数和一处CPU测试；Review `docs/collab/chatgpt/reviews/2026-10-13_V3_nw_prefetch_mechanism_and_data_wait_console_fix_22b2ea_50de2a.md`。
