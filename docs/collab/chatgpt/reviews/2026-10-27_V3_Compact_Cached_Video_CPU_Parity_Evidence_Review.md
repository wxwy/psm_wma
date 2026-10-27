# PSM-WMA V3 — Compact Cached Video 0/1 CPU 证据审核（2026-10-27）

## 1. 审核身份与范围

- 审核角色：独立 Evidence reviewer；不承担生产实现、不执行真实训练。
- 本轮 No-TTT 所针对的 Child/Gitlink：`746c5cf2f2324104a62fb71510343aa40d3976c5`；DS 报告提交时的 Root V3：`083a4914aa8785f445ccf7ee9fab13d87c39c761`（随后仅因证据/Review 持久化会有新的 bookkeeping HEAD）。
- 冻结的前序记录：`docs/collab/chatgpt/reviews/2026-10-27_V3_G1_NoTTT_CPU_Performance_Evidence_Review.md`。
- DS 原始新增 Evidence：`docs/collab/chatgpt/DS_PRO_2026-10-27_V3_Compact_Cached_Video_CPU_Parity.md`（来自用户上报，GPT 尚未取得并独立校验其 `/tmp/compact_parity.py`、`results.json`、`log` 实际文件）。
- 审核对象仅为 **本轮 CPU 采样和 Microbenchmark Evidence**；Child/No-TTT 生产实现未变，不重复进行相同代码 SHA 的 implementation review。**此记录不授权 GPU/真实 DCP/重启/修改正式训练。**

## 2. 有效证据和已确认结果

- DS 固定四个全局 Dataset 索引 `[0,1042665,695110,2085330]`，逐字段比较 `COMPACT=0/1`；报告记录：`video_latent`、`action/action_raw`、`text_token_ids`、`sequence_plan`、`image_size`、source indices、`cached_latent_required` 相同；Dense/Proxy Video 逻辑全零、形状相同；Python `random` 和 PyTorch CPU RNG 前后状态相同。
- 独立 CPU 环境：同一 VerifiedExactWindowIndex/catalog/source_reader，torch2.10 cu128，未使用 GPU；Transform 8 PyTorch intra-op threads，重复30次、warm3。
- DS 所测单 Consumer Transform：Dense median 12.646–13.661ms、Compact median 0.455–0.661ms，**局部纯 Transform 20.6–28.7×**。是 **SUPPORTED sampled CPU performance**，不能外推至真实 Full Step 倍速。
- Child `cached_pixel_geometry.py` 的 Compact 模式使用 stride0 一字节逻辑全零代理；`CachedGeometryResize` 替换真实像素 Resize/Pad；`move_cached_native_batch` 对已验证代理有不同 Host→Device 路径。该实现能解释 CPU 单 Consumer 加速，但并不能单凭 `torch.equal` 断言真实 Native 模型的设备与内存布局语义等价。
- 本轮结果仅表明所测 *4个样本 SFT 输出* CPU 值/部分 RNG 等价，不支持报告中“全部模型输入字段完全一致”的更大范围断言。

## 3. 尚未关闭的 Evidence 缺口（Evidence-only；非生产 Bug）

### E1 — MEDIUM：所谓 partial/terminal 样本的时序身份没有证明

- 报告只使用 `CONSUMERS=[0,N//2,N//3,N-1]` 并把 `N//3` 标为 partial、`N-1` 标为 terminal；没有报告 Episode UID / `window_count` / `cursor` / `valid_count` / `training_stream_end`。
- 依据现有 Child `cosmos_framework/model/generator/mot/robocasa_exact_window_local.py:269-295`，**terminal partial** 是 `request.identity.training_stream_end is True` 且 `0 < request.valid_count < 16`，不是由全局数据集索引自动决定的。
- 验收条件：用真实 Catalog 选择并打印一个符合上述谓词的 `ExactWindowSegmentRequest`，再用相同请求跑 Compact0/1 CPU对照；另有一个满长 `valid_count=16` 和跨 Episode Slot 绑定案例。分别记录具体 UID/cursor/window_count/segment_count/valid_count。无需全量跑Dataset或重新扫线程数。

### E2 — MEDIUM：没有覆盖 No-TTT 真实 CPU Loader → Segment → Native Packed Batch

- 报告所述实验主要是两套 `sft[idx]` + 纯 `time_transform`；未提供 `NoTTTCpuLoader.begin/materialize`、`RawDataset.__getitem__` packet decode、`ExactWindowSegmentProducer.materialize`、`MatchedNoTTTWindow.pack` 和 `collate_grouped_native_batch` 级别的成功输出证据。
- 这里的生产分支正好会在 Worker 返回后，根据 `producer.catalog.raw.compact_cached_video` 重建 dense/proxy，且后续 Packed Batch 是按 Slot/Segment index 冻结顺序创建，不能靠4个孤立Consumer替代。
- 验收条件：在隔离 CPU 环境对冻结、确定性的 *同一组 request* 运行 COMPACT0/1，经过 NoTTT 的真实 `NoTTTCpuLoader`（建议限制1 Worker/Prefetch1首先做可用性 smoke，若需要8 Worker parity则独立说明CPU资源边界）→ `SegmentBatch` → `MatchedNoTTTWindow.pack` → `collate_grouped_native_batch`；逐个比较 Consumer 次序/有效Mask/Slot与Segment identity、action、latent、text tokens、SequencePlan、image_size、逻辑零 Video 和 RNG。只允许 Video Storage/stride 不同。不要实例化正式模型或 GPU，不写 Job/DCP，不改生产代码。
- 原始 `/tmp/compact_parity.py`、`/tmp/compact_parity_results.json`、`/tmp/compact_parity.log` 还应归档可追溯摘要或拷贝到 Evidence 目录；当前只拿到 DS 上报文本。

### E3 — INFO：两次审计 Canvas 几何不一致，历史 Pad 表述需更正

- 早前 DS G1/No-TTT CPU审计报告按`480×832`和“只有 reflect pad 无 resize”叙述；本轮实际值为 video输出 `(3,17,192,320)`、`image_size=[192,320,160,320]`。实际 Child `RoboCasaExactWindowCachedDataset.__init__` 调 `VideoResize()` 推导对应 Canvas；`transforms.py` 同时可能有 Bicubic Resize 和 Reflection Padding。
- 以真实同一 Config 的此次几何为有效的新证据，不再沿用历史 `480×832`；确认 `video` 是否发生 resize+pad（而不只是pad）。该条可在 E2 的同一任务中记录，**不另外要求全套大实验**。

## 4. 当前 Evidence Gate 状态

- **单 Consumer CPU sampled parity：PASS（DS报告范围内，尚缺原始运行文件独立核验）**。
- **单 Consumer纯 Transform Microbenchmark：PASS（DS报告范围内，8线程/四样本）**。
- **完整 Compact CPU Route 与真正 terminal partial 覆盖：REQUEST_CHANGES（Evidence-only）**。
- **Native real model forward/loss/gradient parity：NOT RUN / 未授权**。
- **真实 DCP/CUDA Resume 或正式 Job Compact 切换：NOT RUN / 未授权**。
- **正式训练：保持运行，不停不重启，不改当前环境变量。**

当前未发现需修改 Child 生产代码的 blocker；当前 blocker 都是 **tests/Evidence-only**。不要重复进行 No-TTT nw0/nw8 完整审计。

## 5. 下一步（仅补 E1/E2 的最小 CPU Gate）

请 DS_PRO **不要再做开放式调查**。直接从现有 verified index/catalog 中构造满长和 terminal partial Segment，使用现有生产 NoTTTCpuLoader 路径，比较 compact0/1 完整 CPU Packed Batch 值/次序/RNG，保存可复现脚本/结果。无需再次重新构建整个索引的 cold scan，不运行 GPU/真实模型/DCP，不修改训练产物。完成后 GPT 只审核新 Evidence；formal implementation/design pair 未变不重审代码。

注意：即使 CPU Route Gate 完成，也不自动授权下一 GPU Parity Gate；需 Owner 单独放行。
