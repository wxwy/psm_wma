# PSM-WMA V3 — Compact Segment / No-TTT Full CPU Parity：增量 Evidence 审核

- 审核日期：2026-10-28
- 类型：**Evidence-only incremental review**（非新 implementation/design pair，不重新审核未变化的 No-TTT 源码）。
- 对应生产代码 Child/Gitlink：`746c5cf2f2324104a62fb71510343aa40d3976c5`。此前正式生产 Root 的相关代码基线：`49df7f3c2e0ba8ef5871f9dd490e41fbc3dc5da9`；后续 Root 评测及归档提交并非本 Gate 的代码变更。报告上报时 Root V3 `5ea1a3463cd7e7f0de2643f4766c560c26612904`。
- 既有前轮 Review：`docs/collab/chatgpt/reviews/2026-10-27_V3_Compact_Cached_Video_CPU_Parity_Evidence_Review.md`；前轮 E1 (terminal partial) / E2 (full CPU packed route) 为仅缺 Evidence 的 MEDIUM blockers。
- 这轮 DS 报告归档：`docs/collab/chatgpt/DS_PRO_2026-10-27_V3_Compact_Segment_Full_NoTTT_CPU_Loader_Parity.md`；**源自用户粘贴的 DS_PRO 声明**，不是我执行测试的独立原始结果。
- Source: 远端 GitHub V3 / Child v3-local-ttt 核对完成，Child/Gitlink仍一致；没有改生产实现、启动GPU或正式训练。

## 1. DS新增 Evidence：按报告内容逐项核对

### E1：真实 terminal partial —— 报告覆盖达到要求

| UID | window_count | segment_count | last cursor | valid_count | identity |
|---|---:|---:|---:|---:|---|
| CloseBlenderLid/episode_000000 |345|22|21|9|training_stream_end=True|
| CloseBlenderLid/episode_000001 |396|25|24|12|training_stream_end=True|
| CloseBlenderLid/episode_000002 |365|23|22|13|training_stream_end=True|

- 独立验算 `ceil(window_count/16)`、`cursor=segment_count-1`、`window_count-cursor×16` 均一致：9/12/13满足 terminal partial 真正几何；不是把全局 Dataset `N//3` 错当 partial。
- DS 声称各组 `SegmentBatch` tensor / metadata / 逐个 Consumer payload 和随机状态 before/after 一致，逻辑像素全零且形状相同。
- **E1 状态**：报告支持覆盖并解决上次样本类型错误；但是尚未看到原始断言脚本及机器可读输出，记为 **REPORT_VERIFIED / RAW_EVIDENCE_PENDING**，不能独立关闭 formal Evidence Gate。

### E2：真实 CPU Worker → Packed Batch —— 报告覆盖达到要求

- DS 声称实际使用 `NoTTTCpuLoader(workers=1,prefetch=1,persistent=True)`，与 `ExactWindowSegmentProducer` / `MatchedNoTTTWindow.pack` / `collate_grouped_native_batch` 连接；4 Member × 128 消费者合计512；`positions_eq`、`payload_all`、`batch_all`、`batch_video_eq`、`rng_consumed_eq` 全为True。
- 相比上轮的 `sft[idx]` 单Consumer验证，明显覆盖了Worker raw packet和Parent `_materialize` 后的 Segment/Collate真实行为。单 Worker 是此轮缩减成本的授权范围；不应因正式Job用8 Worker自动要求重跑所有8 Worker。
- **RNG 协议修正合理但须审计脚本**：第一次在同一Python进程交错运行两侧而没有对齐 CFG dropout 全局 RNG，`ai_caption/text_token_ids` 不等价；修正为同Member两侧从同一snapshot出发后结果相同。这是合理的测试设定；但必须通过原始脚本确认成功验证 *end-state一致*、在Member间持续推进的基准状态、需覆盖的RNG域。不能仅凭 `rng_consumed_eq=True` 字样断言完整真实训练 Replay 等价。
- **E2 状态**：按报告数据通过；直接原始证据尚未核验，formal Evidence Gate仍需补证据。

### 性能记录：只采用对应口径

- 单 Worker、顺序功能测试：`transform_host_ms` Dense 3541.1ms vs Compact 348.6ms；支持优化热点被消除的方向。`step_window_host_wall_ms` 32905.4ms vs 20145.4ms，但是包含未分解并行/初始化/资源等待等；**不可作为4GPU生产Step或G1对照实测**。
- 上轮固定Consumer单Transform 20.6–28.7× 仍是隔离CPU局部性能证据，不是训练实际加速承诺。
- 输出 Canvas `[3,17,192,320]` 为报告所测真实几何，不再沿用上轮对 `480×832` 的无条件断言。

## 2. 唯一当前 blocker（Evidence-only）

**E3 — MEDIUM / REQUEST_CHANGES / evidence missing on remote**

- **File:line**：`docs/collab/chatgpt/evidence/compact_segment_parity.py`（远端 V3 **NOT_FOUND**）；`docs/collab/chatgpt/evidence/compact_segment_parity_results.json`（远端 V3 **NOT_FOUND**）。DS报告有路径和部分汇总，但不存在可供 GPT 独立读取的 raw artifacts；外部 `/tmp/...` 亦未通过已授权文件通道提供。
- **Root cause**：DS 称复制到训练服务器工作树，但尚未提交/上传到审核可访问的远端或对话附件。此问题只影响 **Evidence provenance & reproducibility**，并非生产代码错误，也不否定报告中的测量。
- **Frozen acceptance contract**：上一轮 E1/E2 要求可追溯脚本+JSON直接证明 terminal partial 和完整 CPU Packed Route parity；不能只凭 DS 的陈述继承测试PASS。
- **关闭条件**：将脚本和JSON的**原始内容**以附件或 evidence-only GitHub 提交提供给 GPT，原样保留；审核脚本包含真正冻结 Requests/三个 terminal partial、Worker Packet path、递归张量/字段/Slot位置/有效Mask、视频逻辑等价、RNG snapshot/restore/before-after、结果 JSON 与报告值逐项一致。若实际脚本/结果已存服务器，只需传递，不得为此重跑昂贵验证。
- **Scope**：不扩大为代码实施问题，不要求重审相同 Child SHAs；E3解决且无新问题后，CPU Evidence Gate 可独立关闭。

## 3. Gate 与下一阶段边界

- E1: `REPORT_COVERAGE_PASS / ORIGINAL_RAW_EVIDENCE_PENDING`。
- E2: `REPORT_COVERAGE_PASS / ORIGINAL_RAW_EVIDENCE_PENDING`。
- **正式增量 Evidence verdict**：`REQUEST_CHANGES`（仅 E3 MEDIUM；不是生产实现 blocker）。无证据表明 Child现有 Compact实现必须改变。
- 真实模型 Forward/Loss/Gradient parity：`NOT_RUN / NOT_AUTHORIZED`。
- GPU H2D / FSDP / DCP / 正式No-TTT Checkpoint上的Compact切换：`NOT_RUN / NOT_AUTHORIZED`。
- 正式 Job继续运行，尚未获得任何停训/重启/改当前环境的授权。
- **下一步最小动作**：提交现成两个 evidence 文件供 GPT 直接审计；没有必要重新运行四Consumer/512Consumer、扫线程数或修改生产代码。

本 Review 只有与 Canonical Inbox 同步追加后才是正式增量 Evidence verdict，不批准正式训练切换或后续GPU Gate。
