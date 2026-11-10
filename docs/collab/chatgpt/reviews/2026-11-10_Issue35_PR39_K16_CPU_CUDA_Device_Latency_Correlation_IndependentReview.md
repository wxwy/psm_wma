# Issue #35 — PR #39 K16/source64 首次慢段和长尾：GPT 独立 CPU/CUDA/设备关联诊断

**2026-11-10，Asia/Shanghai。结论：`APPROVE_DIAGNOSTIC_TOOL_SCOPED / K16_TRACE_RECORDED / PARTIAL_ALLOCATOR_TAIL_MECHANISM_SUPPORTED / LATENCY_STABILITY_GATE_OPEN`。**

## 1. 不变的正式生产配对与本次工具范围

- **已获限域生产代码批准的 Formal Pair 不变**：Root `1b184204e301a51a7a20ed4dde1a11689589cf2d` / Child+Gitlink `d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2`。本次 Root [Draft PR #39](https://github.com/wxwy/psm_wma/pull/39) 的诊断文档工具 HEAD `5a52f021216e98611f0f10890a9add592c7ab98b` **不是**新正式生产 SHA。
- [Root Draft #38](https://github.com/wxwy/psm_wma/pull/38) / [Child Draft #14](https://github.com/wxwy/cosmos-framework/pull/14) 的代码数值限域 `APPROVE_CODE` 不变；本轮没有改生产、Memory Prefix注入、Attention/编译选项、训练、FastState或权重；没有合并 V3。
- GPT从 GitHub 精确 `5a52f021` 提取 `latency_probe.py` 与 `probe_test.py` 到**独立工作树外目录**，未把文档HEAD覆盖生产工作树。工具内容SHA256分别 `c4ba2686a1f33897e2c916fc01ef96c201524f8767fa8bd7566ed919d0c4753b` / `28f746b9f0a70fb3845e33a13a5f27f7354748bbdd9d9a165e77e1ebb9e024f7`。
- GPT独立在授权 data 服务器重跑**探针 CPU 34/34 PASS，0 fail/error/skip**；未重复之前已经批准的生产 314项CPU Gate。回放仅 **K16/source64**，没有K1、NoTTT、仿真、SR、900EP或其他GPU。

## 2. GPT真实执行一次低扰动外部观测：54个原生调用和GPU6设备遥测

原版 `benchmark_new_on_dynamo.py`、K16/source64 真实冻结请求及独立批准的原始 Local Action/Vision参考不变，Local iter15000 DCP、BF16、B1/guidance1/30-UniPC、GPU6 H100；原模型runner继续完成每次真实输出严格校验。

工具仅在 `generate_samples_from_batch` 边界外观测；**4 warmup + 50 measured，54/54 generation与CUDA异步event span均有结果**、无缺失或probe error；`metadata.json=status RECORDED`、`source_unchanged=true`、`runner_unchanged=true`、原生runner exit0。GPU6设备状态采样每200ms，取得**676条记录**；只关闭本次创建的遥测进程。

| 50次原生generation事件计时（包括当帧VAE，不含FW/HTTP/Sim） | 值 |
|---|---:|
| mean | **672.167ms** |
| P50 | **668.577ms** |
| P95 | **673.502ms** |
| 本轮有限50样本插值P99 | **761.605ms** |
| max | **844.737ms** |

首次约22轮890–900ms慢段**这次未复现**。该统计附带边界探针和设备采样扰动；只用于诊断，不替代历史未插桩生产性能基线，更不能当作生产P99通过。

第8次正式测量（`call=12`, `measured_index=7`）出现唯一明显长尾，细粒度证据同时发生：

| 同一调用证据 | 典型 | `call=12`异常 |
|---|---:|---:|
| 原生GPU事件跨度 | ≈668ms | **844.737ms** |
| 外部探针CUDA event span | ≈668ms | **844.128ms** |
| Host generation wall | ≈668ms | **844.117ms** |
| 主线程CPU执行 | ≈668ms | **666.513ms** |
| Linux线程调度等待（schedstat） | ≈0.01ms | **0.065ms** |
| Python GC | 0ms | **0ms，0事件** |
| PyTorch CUDA设备新分配计数 | 0 | **+1** |
| CUDACachingAllocator `reserved_bytes` | 不变 | **+2,097,152字节（2MiB）** |
| allocator retry/OOM/`sync_all_streams` 新增 | 0 | **全部0** |
| GPU P-state / SM时钟 | P0 /1980MHz | **P0 /1980MHz** |
| 活跃时钟限制原因 | 0 | **0** |

这里主线程约**177.6ms**既没有执行CPU计算，也并非线程runqueue排队；GPU event span覆盖该停顿，但GPU event包含Device Idle，不能将它误当做Kernel计算时间。与长尾精确对齐的+1次设备分配和+2MiB reserved是重要线索，不是仅凭统计已证明CUDA API阻塞。

## 3. GPT再做一次侵入式 Nsight CUDA API/OSRuntime 证据交叉验证

由于第2节发现设备分配相关长尾，使用服务器已有 **Nsight Systems 2024.4.2** 执行一轮独立K16/source64原版回放，**4 warmup +25 measured**，启用 CUDA API/Kernel、OS runtime与CUDA内存使用事件追踪；未修改生产或原始runner。独立 trace `.nsys-rep` 约51MB，SQLite约123MB，**均只留服务器**。该模式会显著改变时延（P50约865.395ms、max1350.767ms）；其绝对速度**不可用于性能Gate**。

Nsight CUDA API 汇总：`cudaMalloc_v3020`共 **174** 次，最大耗时**248.184ms**；`cudaFree_v3020`21次最大137.429ms；`cudaStreamSynchronize`最大约0.042ms，`cudaDeviceSynchronize`最大约0.209ms。174次是整段模型初始化/编译/采样过程合计，**不是每个generation都发生分配**。

已从SQLite直接确认**同一 CUDA correlation ID 3674223**：

- `cudaMalloc_v3020` 于 **2026-11-10 08:46:49.268618 UTC** 开始，持续 **248.184251ms**，返回码0。
- `CUDA_GPU_MEMORY_USAGE_EVENTS` 关联到上述correlation ID的**2,097,152字节（2MiB）**内存分配事件，时间 `08:46:49.516796 UTC`。
- 该UTC秒与原生runner日志中的一次慢生成匹配：`MEASURE 16 11`（源K16、measured_idx7），GPU事件计时 **1142.483ms**，比周边约850–870ms高约270–290ms。日志秒级关联**不能当成毫秒级独立sample标记**，但配合同一correlation ID，支持“该次慢调用包含高耗时分配”。

因此：另一轮独立硬件追踪证明**2MiB CUDA设备分配API本身可以阻塞248ms**，与第2节无Nsight轮次中“额外2MiB保留 + 主线程未运行约177ms”的特征高度一致。**可把`CUDA allocator device allocation latency`列为部分长尾的优先机制；不能认定全部长尾或首次慢22次都由它引起**。同一Nsight运行的另一次约1350.767ms慢生成在对应UTC窗口没有同类长`cudaMalloc`，仍需查其他机制。

## 4. 证据不足与下一步最小行动

**探针本身已通过限定审核，GPU采集成功；性能稳定性与首次慢段根因仍为`OPEN`。** 不能把高优先级机制直接转换成修复授权。建议后续Codex只做一个基于**K16**且可关闭的外部调查：追踪这次2MiB分配到底由哪个请求级张量/allocator pool增长触发（必要时使用独立内存历史/allocator trace；必须标明观测扰动）。同时保留首次慢段与其它无`cudaMalloc`长尾为**独立未解项**；不改Memory注入、Attention路径、编译、模型训练，也不放宽严格数值Gate。

任何下一步代码候选都需固定新Formal Pair、先验证真实K16/source64 30步Velocity+raw15/Action/Vision exact，再单独做GPU性能；不做K1/NoTTT复测，不根据未复现就宣布问题消失，不任意增长warmup/删慢样本，不合并V3。

## 5. 原始证据身份

授权 data 服务器私有根目录：

`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/_gpt_independent_gates_20261104/issue35_prefix_projection_independent_20261110/latency_diagnostic01/`

其下保留：`probe_cpu_junit.xml`、`observer/metadata.json`、`observer/generation.jsonl`、`native/result.json`、`gpu.csv`、`derived_timeline_summary.json`、`nsys_diagnostic/k16_cuda_api.nsys-rep`、`nsys_diagnostic/k16_cuda_api.sqlite`、`nsys_diagnostic/native/result.json`以及最终**`independent_final_diagnostic_audit.json` SHA256 `083b08561ad16c860541f23fb3b21e2a54099b3eb2ed5023ac550e10c9a44004`**。Nsight原始Trace SHA256 `2acde337981b2ddf8c168fc74843afdb99d379e93e5f79c1947eaf69b721d62e`。源代码、权重、原始请求、Trace及原生Action均未外传GitHub。

本轮服务器最终核对Formal Root/Child/Gitlink仍一致且tracked clean，相关owned进程已退出，GPU4–7显存0MiB。本review和Inbox属于docs-only bookkeeping，**不产生新的正式实现 SHA**。