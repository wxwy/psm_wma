# DS_PRO — V3 Compact Cached Video 0 vs 1 等价性与耗时对比（隔离 CPU 验证）

- **日期**: 2026-10-27
- **角色**: ds_pro（只读验证实验；不改生产代码、不停训练、无 GPU、无高负载）
- **对应审核结论**: `docs/collab/chatgpt/reviews/2026-10-27_V3_G1_NoTTT_CPU_Performance_Evidence_Review.md`（`COMPACT_PARITY_PENDING`）
- **正式 Root**: `083a4914aa87`（当前 HEAD）
- **正式 Child / Gitlink**: `746c5cf2f2324104a62fb71510343aa40d3976c5`
- **执行边界**: 纯 CPU（`CUDA_VISIBLE_DEVICES=''`、`COSMOS_DEVICE=cpu`、HF offline）；共享同一 `source_reader`/catalog，仅切换 `PSM_V3_COMPACT_CACHED_VIDEO` env 构造 compact=0/1 两套 dataset；生产 No-TTT 训练全程未动（PID 1202529-1202532 持续运行）。

---

## 0. 结论先行

**等价性通过**：4 个相同 Consumer（start / middle / partial / terminal）下，compact=0 与 compact=1 的**全部模型输入字段、数据顺序、SequencePlan、RNG（transform 前/后状态）完全一致**；`cached_latent_required` 均为 True；`video` 形状一致且逻辑像素双零（compact1 为 1 字节 stride-0 proxy，compact0 为实张量）。

**耗时**：per-consumer Transform 在 8 线程下 median 从 **~12.6–13.7ms（compact=0）降到 ~0.46–0.66ms（compact=1）**，中位加速 **20.6–28.7×**；P90 同量级。

**结论**：Compact=1 在 CPU 侧对 Native 模型输入是**数值等价**的，且消除了常量零视频的逐 consumer 冗余 resize+pad 热点（对应审核记录 `REJECT` 之外已证实的 pad 热点）。**真实模型 Loss/Gradient parity 与正式 No-TTT Checkpoint 边界切换不在本次范围**，需按用户指令单独授权。

---

## 1. 实验设计

- **隔离环境**：OLD venv `/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/cosmos-framework/.venv/bin/python`（torch 2.10.0+cu128 + torchvision 0.25.0，与生产 No-TTT 相同 venv），指向 V3 源码 `/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma_v3/cosmos-framework`。
- **共享读路径**：同一 `VerifiedExactWindowIndex`（verify_files=False, trusted）、同一 `RoboCasaExactWindowCacheCatalog`、同一 `RoboCasaExactWindowSourceReader`（构造 182–190s 一次）。
- **只切一个变量**：`PSM_V3_COMPACT_CACHED_VIDEO=0/1` → `RoboCasaExactWindowCachedDataset` 的 `compact_cached_video` → `cached_pixel_placeholder(compact=...)` + `CachedGeometryResize` 替换 `video_resize`（与生产构造一致，`get_action_robocasa_exact_window_cached_sft_dataset` 同路径）。
- **相同 Consumer**：`CONSUMERS = [0, N//2, N//3, N-1]`，N=2,085,331（start / middle / partial / terminal）。
- **RNG 控制**：每个 Consumer 先 `set_seed(1000+idx)`，再分别取 compact0/1，比较 `random.getstate()` + `torch.random.get_rng_state()` 的 before/after（CFG dropout 0.1 消耗 RNG 的路径）。
- **计时口径**：同一 raw 样本浅拷贝上 `time_transform` 30 次（warm 3），隔离纯 Transform（不含 source_read/latent 读），`statistics.median` / P90 / mean。
- **脚本**：`/tmp/compact_parity.py`；产物 `/tmp/compact_parity_results.json`、`/tmp/compact_parity.log`。

## 2. 等价性结果（4 Consumer 全部一致）

| 检查项 | 结果 |
|---|---|
| Tensor 字段 `video_latent / action / action_raw / text_token_ids / image_size` | ✅ 全部 `torch.equal` |
| Tensor 字段 `conditioning_fps / domain_id / global_row_indices / window_frame_indices / latent_source_frame_indices` | ✅ 全部 `torch.equal` |
| `video`（形状 + 逻辑像素全零） | ✅ 形状 `(3,17,192,320)` 一致；双零；compact1 为 proxy |
| `sequence_plan`（has_text/has_vision/has_action/condition_frame_indexes_vision/condition_frame_indexes_action/action_start_frame_offset） | ✅ 6 字段一致 |
| `cached_latent_required` | ✅ 两侧均 True |
| 其余字段（union 键：无 missing、无 mismatch） | ✅ 全部一致 |
| RNG before / after（`random` + `torch`） | ✅ 两侧一致（CFG dropout 路径不变） |
| 数据顺序（global_row_indices / window_frame_indices / latent_source_frame_indices） | ✅ 一致 |
| `image_size` | ✅ 两侧 `[192, 320, 160, 320]` |

注：canvas 几何实测 `[192,320,160,320]`（latent 分辨率归一后），两 run 一致，不影响等价性结论。

## 3. 计时结果（per-consumer Transform，8 线程，30 次）

| Consumer | compact=0 median / P90 (ms) | compact=1 median / P90 (ms) | 中位加速 |
|---|---|---|---|
| 0 (start) | 13.649 / 13.797 | 0.661 / 0.687 | 20.6× |
| 1042665 (middle) | 13.661 / 13.825 | 0.476 / 0.491 | 28.7× |
| 695110 (partial) | 12.651 / 12.694 | 0.455 / 0.473 | 27.8× |
| 2085330 (terminal) | 12.646 / 12.756 | 0.461 / 0.480 | 27.5× |

- compact=0 的 transform 主导项仍是常量零视频的 resize+reflect-pad（与审计 `4 一致，此处 8 线程 ≈ 12.6–13.7ms/consumer）。
- compact=1 走 `CachedGeometryResize` 直接设 canvas proxy，跳过 resize/pad，剩余 ~0.46–0.66ms 为 prompt 格式化 + tokenize + SequencePlan + action pad。
- 本次为**单进程 8 线程隔离口径**；生产 No-TTT 主进程为 1 线程、且含 source_read（~4.8s/window），因此绝对数字不能直接外推到 Step Wall（该点审核记录已 REJECT 类似外推，不重复）。

## 4. 证据与局限

**证据**：`/tmp/compact_parity_results.json`（完整逐字段）；`/tmp/compact_parity.log`（4 Consumer 逐行 all_field_eq/seq/cached/other/rng + timing）。

**局限（明确不覆盖）**：

1. 只验证 CPU 数据管线输出等价；**未做真实模型 Forward/Loss/Gradient parity**——按用户指令单独授权后进行。
2. 未在正式 No-TTT Checkpoint 边界切换 `compact_cached_video`——按用户指令最后才考虑。
3. 共享 `source_reader` 但 dataset 为两个实例；`sft[idx]` 为确定性读路径（同一 key/start），顺序等价已由三个 indices 张量字段 + `episode_index/start_frame` 一致证明。
4. 线程数为固定 8；未扫线程轴（审计已测 1/4/8/16/32/96，不重复）。

## 5. 结论状态

- **等价性**：`PASS`（CPU 数据管线 0 vs 1 数值等价 + 顺序等价 + RNG 等价）。
- **耗时**：`PASS`（Transform median 20.6–28.7× 加速；热点消除与审计结论一致）。
- **生产影响**：`NONE`（只读实验；训练未动、无代码改动、无提交）。
- **待办（需单独授权）**：真实模型 Loss/Gradient parity；正式 Checkpoint 边界切换评估。
