# No-TTT Issue #12 — 候选真实 RoboCasa CPU 单Worker首包 Evidence Gate

**日期：2026-10-31（审阅DS的2026-10-30运行结果）**  
**Formal Root：`fd9021b0908b4b2763b3d02508b1f34df377dc97`；Child/Gitlink：`224c5f3c0bd6911bb49cb6bb0895ba7da53ff822`**  
**正式 Verdict：`PASS`（严格限定真实数据 CPU-only、1个spawn Worker、rank0代表性初始请求、首个有效Segment；原始实测由DS报告，GPT直接核对既有生产校验逻辑）**

## 1. 证据范围与不可替代边界

- Owner转交 DS_PRO《Issue #12 — Candidate First-Packet Acceptance: PASS》完整报告，DS确认本次真实数据实验已由Owner授权并执行；对应外部 `issue12_candidate_first_packet_probe.py`、`probe_result.json`、stdout/stderr保存在 DS 训练服务器 `/mnt/data/shenzhen/szrobot/logs/issue12_candidate_acceptance_20261030/`。这批原始文件**并未在GPT容器/连接的仓库中可直接获取**；本review对数值采用 `DS_REPORTED`证据级别，**未声称独立复算真实日志原件SHA、没有复跑CPU/GPU**。用户此前说明无法转运服务器ZIP和原件，不重复要求文件上传。
- **Formal Pair完全未变**，既有 [Issue12 Code Gate APPROVE_CODE](https://github.com/wxwy/psm_wma/blob/aaf953268c26d6f28ab36e77874a8f54021bb23e/docs/collab/chatgpt/reviews/2026-10-30_V3_NoTTT_Issue12_WorkerColdStart_fd9021b_224c5f3_Incremental_Code_Gate_APPROVE_CODE.md)保留，**不重新审核生产代码、不重跑旧58/301 CPU**；本轮单独审核新真实运行Evidence。
- 旧NoTTT frozen formal Root `e0fe911dfb9fd34957234828195cf051713f6c3d` / Child `f6a92d47b6dac7998ddc58b3da26ef93f8068dc7`仍是历史对照；旧Arm B首次120秒超时/0 optimizer commits记录不变。新候选仍隔离、未合并到V3，EvalV2技术线不受影响。

## 2. 真实运行数据（DS reported；实测量纲逐项明确）

| Gate量 | 新正式候选 | 旧代码对照 | 结果语义 |
| --- | ---: | ---: | --- |
| `loader_construct_s` | 0.002 s | 0.004 s | 新旧相近 |
| `worker_startup_s` | 0.013 s | 0.013 s | 含创建iterator/spawn入口的父进程耗时 |
| `first_materialize_s` | **14.421 s** | 120.249 s / DataLoader Timeout | 新候选真实第一包**返回成功**，不是仅等到Timeout |
| `first_packet_total_s` | **14.436 s** | 120.266 s / Timeout | 低于**原始**120s，且未提高超时 |
| Scope A `source_reader_ms` | 6526.9 ms | 192970.6 ms | **进程内模拟Worker构造**，下降96.62%，不能冒充真实Worker内部逐阶段计时 |
| Scope A `total_build_ms` | 7203.5 ms | 193652.7 ms | **进程内模拟**，下降96.28% |
| Scope A `lerobot_init_ms` | 2298.0 ms | 188782.1 ms | 避免全量LeRobot Dataset构造，仍包括轻量metadata等 |
| Scope A `worker_prepare_ms.wall` | 271.4 ms | 224.5 ms | 不要求准备阶段本身更快；瓶颈来自初始化 |
| Parent传统`parent_sft_dataset_ms` | 192206 ms | 约192569 ms | Parent eager初始化**仍然存在**，非本轮改动目标 |

**原因链（直接核对早前冻结Child源码，Formal代码未变）：** 旧 `PreparedDataset.__getitem__()`第一次调用 `AsyncRecipe.build()`；新 `AsyncRecipe.build`通过 `RoboCasaExactWindowSourceReader(dataset_factory=partial(VerifiedWorkerLeRobotDataset,...))`建立轻量 VerifiedIndex/Episode spans，读取当前Episode时才做Parquet row-group/列投影与有界LRU。官方LeRobot `__getitem__`/Delta/Caption和原SourceReader逐窗严格验证都保留。效果来自**真实工作量减少**，不是调大120秒、遮蔽timeout或偷偷把Source移到Parent。

## 3. Segment 与摘要交叉核对

- DS回报通过了公开 `NoTTTAsyncLoader.materialize()`并且没有异常；代码中`_materialize`验证：generation/window/token、Worker PID、file versions、CFG caption/token键、Segment尺寸与`validate(t)`、Episode UID、Config/Manifest/Request Source摘要、Segment身份、Slot/Consumer step/Valid Count，最后才返回Segment并做原父进程CFG RNG draw。
- 返回对象 `CloseBlenderLid/episode_000116`，`segment_id=0`、`slot_id=[0]`、`valid_count=16`；对应**rank0 initial_frontier first member**，不是iter9600恢复后的首个Request。此身份范围符合本Gate。
- 报告中的Recipe `source_digest=f91b0b47…`是整个源 `source_binding_digest`，而Segment的`source_digest=36ce5e79…`是 `ExactWindowLocalEpisode.source_digest`（将SourceBinding等字段与具体Episode/first/terminal row witness一起散列）。两者在代码定义上属于**不同摘要域**，不能因为值不同而判漂移。`_materialize()`比较Segment与 `request.identity.source_digest`成功；DS回报manifest/cache/config digest无漂移。
- 这不是原始`iter_000009600`完整DCP/optimizer/sidecar/Frontier Resume验证；不得据本条声称新正式训练C+1连续性PASS。

## 4. 资源和并发风险必须保留

- DS报告 Worker `worker_maxrss_kib=5,917,056`，在Linux`ru_maxrss`语义下是 **5778.375 MiB≈5.643 GiB峰值RSS**；Parent 5778 MiB≈5.642 GiB。Source/Arrow/HF/Tokenizer/进程runtime及既有cache都计入RSS；1 Worker不能直接替代32 Worker资源结论。
- `cache_mapped_bytes=59,339,603 bytes≈56.59 MiB`来自 `PreparedDataset.__getitem__`对 `state.cache_reader._mapped_sizes` 的求和——对应既有**Episode/Latent mmap cache**，**不是**新增 `VerifiedWorkerLeRobotDataset._VerifiedRows.cache_bytes` 的测量，不可据此推断Source Arrow LRU仅56MiB。
- 粗算若32Worker各达到当前5.643GiB RSS，累计Worker RSS计数约181GiB，**RSS含共享/文件映射，不能视为物理独占内存估计**；另有4个Parent、临时Arrow批次和IO争用。真实多Worker并发可能显著放大启动耗时。DS所谓`~25× concurrency headroom`不能从单Worker的7s近似构建成本数学推出。
- `resource_tracker`有1条loky semaphore退出时被清理的warning；DS报告own Worker/Parent进程已退出、无残留。这不单独触发新Code Gate，但新多进程GPU试验仍应核对owned PID回收。

## 5. Gate closure / 下一步

- **`CPU_REAL_DATA_SINGLE_WORKER_FIRST_PACKET=PASS`**，仅覆盖一次Owner授权、CPU-only、1Worker、真实Cache/VerifiedIndex、120秒Timeout内得到有效Segment。此Scope应立即冻结，不重复要求DS同一探针、重传ZIP或重跑历史CPU301。此前`APPROVE_CODE`同样保留，不扩大到GPU或V3合并。
- **`REAL_4RANK_8WORKER_STARTUP=NOT_RUN`；`REAL_DCP_C+1=NOT_RUN`；`GPU_STEADY_STATE_PERFORMANCE=INCONCLUSIVE`；`V3_PROMOTION=NOT_AUTHORIZED`。**
- **下一步建议（待Owner独立授权）**：先由DS只读确认正式30k是否仍占用GPU4–7、host可用RAM/IO、同一真实DCP C9600可读且完整、独立A/B输出路径和新候选exact Root/Child import origin；若4×GPU无法排他使用则不启动性能比较。在明确授权且资源空闲后，从相同完整DCP分别对`nw0 Compact1`和`nw8 Compact1`做隔离**少量matched commits**：先确保B真实C+1与4Rank32Worker首包无OOM/Timeout，再测A/B相同独占条件下稳态step wall/数据等待与current-stream `gpu_data_stall_ms`；不可把单Worker P50或旧共享GPU A作为真实speedup。
- **禁止**未经Owner单独批准启动GPU实验、停止/改变活跃30k任务、覆盖原DCP/Checkpoint、合并整棵旧候选覆盖V3当前EvalV2 Child、更改120秒Timeout或对训练损失进行无授权修改。

**本Review只关闭当前CPU真实数据首包Evidence Gate，不授权后续GPU/生产行为。**
