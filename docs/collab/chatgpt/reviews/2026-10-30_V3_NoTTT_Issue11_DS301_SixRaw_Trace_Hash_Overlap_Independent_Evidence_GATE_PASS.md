# PSM-WMA V3 No-TTT — Issue #11 独立 DS301 CPU Evidence Gate 最终关闭（第六份 Trace 原件）

- 日期：2026-10-30；范围：**仅本次增量 Evidence 关闭，不重新审核同一 Formal Pair 源码**。
- **Formal Root：`e0fe911dfb9fd34957234828195cf051713f6c3d`；Child/Gitlink：`f6a92d47b6dac7998ddc58b3da26ef93f8068dc7`**。前序正式 `APPROVE_CODE` 不变。
- **FINAL EVIDENCE VERDICT：`PASS` — Issue #11 DS_PRO 独立 301 synthetic CPU Gate，六份冻结核心 raw Evidence SHA256 均核验通过**。
- Frozen 依据：`docs/collab/chatgpt/requests/2026-10-29_V3_NoTTT_AsyncOverlap_DS_PRO_Independent_CPU_ExactPair.md`；[Issue #11](https://github.com/wxwy/psm_wma/issues/11)；上轮五文件审核：`docs/collab/chatgpt/reviews/2026-10-30_V3_NoTTT_Issue11_DS301_5Raw_SHA_Verification_Trace_Pending.md`。
- **新输入**：Owner 当前消息上传的三个连续文本部分（同一份 `timelines/overlap_trace.json`，分别为 `粘贴的文本 (1)(20261030-023923).txt`、`粘贴的文本 (2)(3).txt`、`粘贴的文本 (3)(3).txt`）。GPT在当前容器程序化读取3份原始上传字节、按顺序拼接为JSON，再 `json.dumps(obj,indent=2)` 复原冻结文件；并非直接连接 DS 服务器，未在 DS 工作树做任何操作。

## 一、6/6 Raw 字节级 SHA 与测试结果

五份已核原始 `gate.json` / `async.xml` / `regression.xml` / `environment.json` / `source_sha256.json` 的SHA-256及JUnit 301个unique case / 0 failures/errors/skips，已在上轮冻结Review直接解析，本轮不重复该范围。其原件此前汇总于本会话归档，现与第六份一起提供完整6-raw证据包。

**第六份完整 `timelines/overlap_trace.json`**：JSON解析有效，Canonical编码后长度 **117909 bytes**（纯UTF-8、`indent=2`、结尾无换行），SHA-256 **`27357f1034a0b2ea91e887240c6566c1aac2630f37bd5f983123a332e3396c11`**；与DS先前冻结 `evidence_files.sha256` 的第6项**精确匹配**。原三份文本的CRLF和切分边界空格不是原始文件的字节，故仅按原始JSON序列化复原；匹配已冻结SHA解决了原件一致性。

此文件具有异步399事件（96 `cpu_source` + 96 `cpu_transform` +96 `main_thread_wait` +96 `consumer_ready` +12 `fake_gpu_compute` +3 `committed_iter`），串行对照204事件（96 Source+96 Transform+12 fake compute）。2个实际worker PID **551358/551359**，trainer PID **549876**；每个 Window 0/1/2 的四个GA Member各有8个 Source与8个Transform事件，96 Token 的Source/Transform一一对应、先Source后Transform，Worker PID一致。12次fake compute落在主进程；3次 `committed_iter` 均晚于各自Window最后compute结束。

## 二、独立从原始 monotonic 时刻重算

按每对事件交集 `max(0,min(stage_end,compute_end)-max(stage_start,compute_start))*1000`，与原始 JSON 内 aggregate **浮点值完全相等，绝对差0.0ms**：

| 关联 | CPU Source Read | CPU Transform | 正交叠事件对（Source/Transform） |
| --- | ---: | ---: | ---: |
| 下一 GA Member（current window的更高member） | **87.7982173115015 ms** | **128.96525859832764 ms** | 13 / 13 |
| 下一 Window（window+1） | **20.45540139079094 ms** | **32.39326551556587 ms** | 3 / 3 |

- 串行组全部CPU Source/Transform事件与fake compute重叠对数**0**。
- 96个 `main_thread_wait` 时间加和重算 **10376.20665319264ms**，与冻结字段完全相等。三Window分别与当窗main wait的Source/Transform交叠：W0约176.748/242.821ms、W1约210.473/253.675ms、W2约168.546/228.687ms；这是CPU主线程wait，不是GPU Idle。
- 冷启动CPU fake的 `async_window_wall_ms_including_pool_startup=12142.11947657168`，串行 `sync_source_transform_compute_wall_ms=3452.382903546095`。本轮虽已证明真实Worker并行，但**在本CPU短测中异步更慢**；绝对不得当真实CUDA吞吐改善或GPU等待减少的证明。

## 三、冻结状态与权限

- **Issue #11：`DS_CPU=PASS`; `RAW_EVIDENCE=PASS_6_OF_6`; `DIRECT_TRACE_OVERLAP_RECOMPUTE=PASS`；前轮缺失的Trace已关闭，完全不需要再次上传/重跑原CPU301。**
- 原正式训练 Job `no_ttt_packed128_droid_fresh_30k_world4_ga4` 最后已由DS现场报告真实 `NOTTT_LOADER_WORKERS=8`、仍使用旧RAW Loader；本审核**没有在当前时点重新在线确认进程**，也未检查其运行时迭代数。新候选是实际后台Source+Transform/跨Window预取，不能把旧`nw8`当成新能力。
- **`REAL_GPU_PERFORMANCE=NOT_RUN`、`REAL_DCP_RESUME=NOT_RUN`**；Compact0↔1严格GPU Gradient Parity历史 `FAIL_PARITY`，Dense重复性未达冻结阈值、Compact归因`INCONCLUSIVE` 原样保留。CPU合成PASS不能修正这些事实。
- 后续真实资格实验只可在Owner另行明示授权、GPU4–7合法腾出、完整旧Job DCP/4rank sidecar、不同隔离输出namespace的前提下做；此前 `docs/collab/chatgpt/requests/2026-10-29_V3_NoTTT_AsyncCompact_Real_DCP_GPU_Qualification_Proposal.md` 仍为 `PROPOSED_NOT_AUTHORIZED`。**不允许直接合入V3/Child正式分支、触碰当前Job源码/Checkpoints、停止/并发Resume/正式30k训练、GPU实验或磁盘Cleaner**。

本轮只对同 Formal Pair 的**新证据字节和交叠行为**出最终 `PASS`，不是任何新实现 Code Gate、模型数值等价Gate或正式Resume授权。
