# DS_PRO — V3 Batch 1 定向补证（B1 附注 / B3 / D0）

**报告日期：** 2026-10-10；**GPT 保存日期：** 2026-10-11。
**来源边界：** 以下为用户转交的 DS_PRO 报告之忠实结构化记录，不是原始训练服务器 JSON，也不代表 GPT 直接读取了服务器 /tmp 文件。DS 表示不修改生产代码、数据集、DCP；没有 GPU、Trainer、Fresh/Resume 或模拟器执行。

**固定 Formal Pair：** Root 444c232b976e80ac68cde9e7370e73b9f6410f0e；Child/Gitlink e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c。
**原 Batch1 Evidence：** docs/collab/chatgpt/evidence/2026-10-11_V3_Batch1_DS/DS_PRO_2026-10-10_V3_B1_B2_B3_C0_D0_combined_report.md。
**本次补证：** /tmp/probe_b3d0_supp.py (323.3 s)；输出 /tmp/psm_wma_v3_batch1_b3d0_supp_report.json。既有 /tmp/psm_wma_v3_batch1_b1b2_report.json、/tmp/psm_wma_v3_batch1_b3d0_report.json、/tmp/psm_wma_v3_batch1_c0_inventory.json 保持不变。

## DS 原报告的子项结果

| 子项 | DS Verdict | 新增实测 |
|---|---|---|
| B1 | PASS 维持 | 4 个 flat index 的 task class/episode/start；纠正 OFF dense 视频的 uint8/字节数 |
| B3 | PASS 维持 | 3 episode × 3 cursors 共 9 段 OFF/OFF 与 ON/ON 全等；原生 gather same-index 顺序 witness |
| D0 | PASS 维持 | workers 0/2/4 48 段完整指纹对齐；独立冷 reader 性能/缓存计数 |
| B2/C0 | 不变 | 此轮未重新执行 |

## B1 — task class 与视频物理存储更正

| flat_idx | task_class | episode_index | start |
|---:|---|---:|---:|
| 0 | CloseBlenderLid | 0 | 0 |
| 7 | CloseBlenderLid | 0 | 7 |
| 1042665 | PickPlaceCounterToCabinet | 4498 | 221 |
| 2085330 | TurnOnSinkFaucet | 9125 | 281 |

3 个 task classes；覆盖 corpus 首、中、尾真实窗口。

- Compact OFF：torch.uint8，shape [3,17,192,320]，dense storage **3,133,440 bytes**，非 proxy。
- Compact ON：torch.uint8，同一逻辑 shape，zero-stride proxy，physical backing **1 byte**。
- 原生未 resize zero video：torch.uint8，[3,17,256,512]，6,684,672 bytes。
- DS 更正此前写作“dense fp32 / 3,129,600 bytes”的错误标签；这不是实测 tensor 的 dtype/bytes。仅占位视频的物理 layout 不同，不能由存储节省推导真实 Policy 的视觉 token 等价。

## B3 — 9 段跨配置真实数据 parity

真实 Episode：
- CoffeeSetupMug/episode_001744：209 windows / 14 segments，cursor {0,7,13}，尾段 valid=1。
- CloseBlenderLid/episode_000000：345 windows / 22 segments，cursor {0,11,21}，尾段 valid=9。
- CloseBlenderLid/episode_000457：697 windows / 44 segments，cursor {0,22,43}，尾段 valid=9。

DS 使用实际 ExactWindowLocalCatalog / ExactWindowRankPlanner / ExactWindowSegmentProducer.prepare/materialize，T=16，并报告：
- OFF/OFF 对 ON/ON：9/9 段 all_equal=true、all_payload_non_video_equal=true、payload_frame_wise_equal=true、payload_len=true。
- SegmentBatch 的 identity (slot_id、episode_id、category、segment_provenance)、consumer_valid / step / visual_summary、evidence_valid / source_step / visual_summary_prev / executed_action_prev 均逐项相同。
- payload_per_key 24 个 key 全部按值比较；23 个非 video key 相同，包括 video_latent、action、action_raw、action_processing_record、sequence_plan、text_token_ids、global_row_indices、window_frame_indices、latent_source_frame_indices、source/cache digests、mode、idle_frames 等。video 仅存在设计规定的 dense vs 1-byte proxy storage 差异；无效 PAD 的 None/None 相同。
- native gather_exact_window_same_index 在 GA 首窗 member0 的 index 0/7/15 均使用 slots [0,1,2,3,4,5,6,7]、各 index 上相应 consumer_steps [index×8]、n_payloads=8；跨配置 index0 slot_ids_equal=true、consumer_steps_equal=true。
- **补证使用 cfg_dropout_rate=0.0**，DS 明确说明这是为了“消除随机混淆，做字节级 parity”。此参数记录为本次测试条件，不能据此声称已验证正式训练随机 CFG 配方。
- config_digest 70e9867f… 为报告携带的前缀，非经真实训练恢复重新测量的完整冻结配置摘要。

## D0 — 48 段全指纹与冷/热 reader

实际 AsyncExactWindowRawPrefetcher(producer, num_workers=0/2/4)；3 GA windows × 2 GA members × 8 slots = 48 segments/配置。

**Warm：** all_order_ok=true，order0_2_equal=true，order0_4_equal=true；fp0_2_equal=true、fp0_4_equal=true、fp2_4_equal=true、fp0_unique=true，n=48。first_fp 前缀 477d81a4bbc7b1ab，last_fp 前缀 d4640ac09df2。各组 cache 2406 hits / 0 loads / 0 misses。

| workers | wall_s | segments/s |
|---:|---:|---:|
| 0 | 8.138 | 5.90 |
| 2 | 13.118 | 3.66 |
| 4 | 33.467 | 1.43 |

**Cold：** 每个 worker 配置重新构造 dataset/reader/catalog/planner，空 LRU 冷启动；每配置 2398 hits / 8 loads / 8 misses，8 个 Episode，总 cached_bytes=421972248、cached_entries=8、0 evictions/failures/oversized。cold_all_48_fp_aligned_with_warm_nw0=true。

| workers | wall_s | segments/s | iteration_wait_ms | reported peak_rss_kb | reported rss_delta_kb |
|---:|---:|---:|---:|---:|---:|
| 0 | 11.356 | 4.23 | sync | 6020060 | 0 |
| 2 | 14.620 | 3.28 | 2055.42 | 6020060 | 0 |
| 4 | 39.579 | 1.21 | 6690.18 | 6020060 | 0 |

DS 观察本次负载下 workers=0 快于 2/4；此为 CPU/缓存/同机特定测量，不代表 H100 实际模型吞吐。相同 peak RSS 数字是报告值，不单独证明三种 workers 具有相同独立进程内存峰值。

## DS 断言与原始文件边界

DS 声明补证无新 FAIL/BLOCKED，原 Batch1 B1/B2/C0 不变；原始 JSON 与脚本仍留在 DS 训练服务器 /tmp，本文件没有收到原始 JSON 的全部字段、hash witness 或脚本字节。DS 声明训练正式作业 formal_verified_index_30k 维持 STOPPED。**上述 PASS 均为 DS 的报告裁决；GPT 独立最终 Gate 裁决见关联 Review。**
