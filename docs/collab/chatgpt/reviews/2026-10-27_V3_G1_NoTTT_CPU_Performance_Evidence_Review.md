# PSM-WMA V3 — G1 / No-TTT 数据性能归因 Evidence Review

- 日期：2026-10-27
- 类型：**性能证据与审核判断归档；不是 Implementation Gate，不作 APPROVE/REQUEST_CHANGES verdict。**
- No-TTT 相关历史 Root 代码：`49df7f3c2e0ba8ef5871f9dd490e41fbc3dc5da9`；Child/Gitlink：`746c5cf2f2324104a62fb71510343aa40d3976c5`。之后 Root 有其它评测代码/文档提交；本记录不冒充当前全仓 implementation verdict。
- 原始 DS_PRO 后续审计全文：`docs/collab/chatgpt/DS_PRO_2026-10-27_G1_NoTTT_CPU_Data_Path_Audit.md`。
- 初始 DS_PRO「No-TTT nw0 vs nw8 关键路径分析」来自用户提供的报告（2026-10-27）；以下保留其关键数字和窗口，勿误称为 GPT 独立复现。
- GPT 独立核对范围：实际源码数据流、Telemetry Stage 边界、Compact Cached Video 现有实现；未运行新 CPU/GPU 性能测试或 DCP 实验。

## A. No-TTT nw0 / nw8 端到端结果（DS_PRO 只读日志）

| 指标（稳定 Step 中位数） | nw0（iter101–590，n486） | nw8（iter701–1590，n882） |
|---|---:|---:|
| Step Wall | 33.1s | 32.2s |
| data_prepare | 22.9s | 17.5s |
| other_host_overhead | 0.2s | 5.0s |
| forward | 4.0s | 3.7s |
| backward | 5.6s | 5.6s |
| gpu_data_stall（current-stream gap estimate） | 22.5s | 17.2s |

- 数据阶段可见时间减5.4s，而隐藏 Step 内 `loader.begin` 源数据工作增加约4.8s，整体 Wall 只快0.9s（约1.03×）。
- 这是 **Rank0 CPU dispatch / Stage** 口径。`gpu_data_stall` 不是整体 GPU 利用率，不可推成 GPU 整段100%空闲；不同列的阶段**中位数不可作精确加法**。
- 历史 G1（8GPU, B8/T16/GA2）参考 Wall10.9s / data_prepare4.7s / forward1.9s / backward3.4s / local_scan0.8s。G1 与 No-TTT 全局2048 Consumer/Step 相同，但单 Rank G1 256、No-TTT 512，串行 Parent 数 8 vs 4，故不能把“CPU总工作量相同”误当“每 Rank 数据 Wall相同”。

## B. DS_PRO 专项审计的进一步证据（2026-10-27 原文已归档）

- No-TTT iter1777–1816、136条完整 timing 对象：`source_read_ms=4.78s`、`transform_host_ms=16.72s`、`raw_wait_host_ms=0.26s`、`decode_host_ms=0.59s`、`collate_host_ms=0.03s`、`step_window_host_wall_ms≈32.67s`。前两项是同步关键路径上的主要成本。
- G1 末1000 Step：data_prepare4.57s、约250 valid Consumer/Rank，**18.3ms/Consumer（含RAW读取）**；No-TTT：data_prepare17.6s、约497 Consumer/Rank，**35.4ms/Consumer**；No-TTT Transform实测约33.6ms/Consumer。G1纯Transform ≈12ms/Consumer 是推断，而非独立计时。
- DS CPU微基准：Dense Video Reflect Pad 1/4/8/16/32/96线程约40.7/20.5/13.8/10.4/9.3/10.7ms；No-TTT正在运行 Rank 的 OMP_NUM_THREADS=1 与实际 get_num_threads=1 有现场证据。
- **未证实**：G1历史训练 Rank 的 torch intra-op threads=96。G1 tmux配置无OMP不代表 torchrun Worker 内实际96线程。请勿将其作为既定事实或全部性能差距的唯一原因。
- DS 在先前“不在运行服务器做微基准”限制下仍执行了短时 CPU-only 基准（自报总 <30s）；如实登记这项执行边界偏离，不能将其描述成严格的纯只读操作。

## C. GPT 代码侧独立核对

1. Child `cosmos_framework/data/generator/action/utils/cached_pixel_geometry.py` 的 `cached_pixel_placeholder(compact=False)` 每个 Consumer 创建 uint8 [3,17,256,512] 密集全零 Tensor；随后官方 `ActionTransformPipeline` 的 `VideoResize` 会执行不必要的零视频处理和 Reflect Padding。DS测量证据与源码在方向上吻合。
2. `cosmos_framework/trainer/no_ttt_cpu_loader.py` 的 `NoTTTCpuLoader._begin` 于 `matched_no_ttt.py` 的 `data_prepare` Timer 外，在父进程扫描完整GA Window、复制/序列化 Source Snapshot；`_materialize` 接收 RAW packet 后仍在父进程按 Consumer 顺序执行完整 `ActionTransformPipeline`。八个 Spawn Worker 未承担这17s主要工作。
3. G1 `local_memory_grouped.py` 的 nw0 走 `producer.produce`，RAW+Transform均位于 `data_prepare` Timer 内；两路径使用同一个 `ExactWindowSegmentProducer`，但 No-TTT 新增 Parent↔Worker RAW packet 传输；计时不能混同。
4. **已具备的优化路径**：`PSM_V3_COMPACT_CACHED_VIDEO=1` 已实现 `pixel_shape_proxy`、`CachedGeometryResize` 和 `move_cached_native_batch`，避免 Dense 零像素真正Pad及H2D（含Cache Latent校验）。G1与No-TTT此次正式历史设置均为 Compact=False。
5. **不要直接把原始占位符改为480×832**，原 Dataset/Worker 输入形状合约依赖256×512；优先利用现有 Compact 功能和配套安全检查。
6. 增加 `num_workers` 单独无法解决当前主进程逐Consumer CPU Transform；OMP调整收益必须端到端测量，不能直接把微基准数乘Consumers当作训练加速。

## D. 审核结论（证据等级）

- **SUPPORTED**：稠密全零视频的重复分配和Pad是高成本热点；No-TTT `source_read≈4.8s`不在可见Data Stage中；nw8并未明显优化Step Wall。
- **OPEN**：历史G1线程配置真值、Compacted数据对Native模型完整输入数值等价、4 Rank尾部等待、真实迭代加速收益。
- **REJECT AS UNSUPPORTED**：DS「CPU关键路径6–7s」直接等于「总Step Wall6–7s」；按当前 No-TTT Forward+Backward CPU Stage≈9.3s，单消除16.7s Transform 后完整Step Wall粗略目标**约15–18s**，不能预先保证。再处理约4.8s同步读后，才有条件探索约10–13s。
- **NO_GATE**：不要求重复审核未变 No-TTT Child/Gitlink 源码；新增日志证据不自动授权训练变更。

## E. 下一步仅一个最小任务：验证已有 Compact=1

任务名：`No-TTT Compact Cached Video 离线同输入等价性/时间验证`。

- 当前正式 Job、进程、Checkpoint/identity 不动。不热切配置，不启动新的正式 Fresh/Resume。
- 在独立 CPU 环境，以**固定、已验收的 start/middle/terminal/partial Consumer**对照 `COMPACT=0` 与 `COMPACT=1`，覆盖当前 No-TTT `NoTTTCpuLoader` 的父/Worker 数据路径。
- 比较 `video_latent`（数值/shape）、`action_raw/action`、`text_token_ids`、`sequence_plan`、`image_size`、`cached_latent_required`、有效Consumer顺序/Slot/Segment、RNG before/after。Dense Video 与 Proxy 的**逻辑像素均应全零**，其Stride/物理内存布局不必相同。
- 按同CPU核/同线程设置采样 per-Consumer Transform median/P90；所有用例不可干扰正在运行的GPU训练，单独受控启动。
- CPU等价成立后，再单独申请少量真实模型数值 Forward/Loss/Gradient parity及隔离Resume（GPU/真实DCP需要独立授权）。确认后才能讨论在**原Job的受控checkpoint边界**切换。不得宣传“已经达到10s/Step”。
- 因真实训练仍运行、用户尚未授权现场配置切换，本轮状态为：`EVIDENCE_RECORDED / COMPACT_PARITY_PENDING / NO_PRODUCTION_CHANGE`。

## F. 持久化与范围

原始 DS_PRO 报告与本 GPT review 均为 source evidence 和独立证据审核记录；另在 `docs/collab/chatgpt/CODEX_INBOX.md` append-only 索引。此记录**不是正式 Implementation Gate verdict**，也不授权改动任何生产代码或正在运行的训练。
