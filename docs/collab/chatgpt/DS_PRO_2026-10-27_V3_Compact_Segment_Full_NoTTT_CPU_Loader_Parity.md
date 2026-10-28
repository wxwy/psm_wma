# DS_PRO — Compact Cached Video 0 vs 1：Terminal Partial Segment + Full No-TTT CPU Loader Parity

> 本记录是**用户提供的 DS_PRO 报告的结构化归档**（含完整关键测量和复现实验协议），不是 GPT 独立运行报告。DS 报告称原始复现脚本与 JSON 已复制到训练服务器的相对路径；截至本次 GitHub 远端核查，该两个 evidence 文件**未在 V3 分支找到**。不要把本记录冒充已审核的 raw artifact。

- 日期：2026-10-27（CST）
- DS角色：只读 / 运行验证 / 证据产出，无生产代码修改，无训练/GPU执行
- 范围：补上轮 Evidence Gate 的 Task1（真实 terminal partial）与 Task2（完整 No-TTT CPU loader 路径）；**未重跑**已通过的四 Consumer 和 Transform 微基准
- 当次实验代码 Child/Gitlink：`746c5cf2f2324104a62fb71510343aa40d3976c5`
- DS 自报原始脚本：`/tmp/compact_segment_parity.py`，server repo working tree 副本 `docs/collab/chatgpt/evidence/compact_segment_parity.py`
- DS 自报结果：`/tmp/compact_segment_parity_results.json`，server repo working tree 副本 `docs/collab/chatgpt/evidence/compact_segment_parity_results.json`
- DS 自报运行日志：`/tmp/compact_segment_parity.log`
- CPU-only：`CUDA_VISIBLE_DEVICES=''`，`COSMOS_DEVICE=cpu`，HF/Transformers offline；torch2.10.0+cu128；8个 Torch线程
- Data：`robocasa365-target-atomic-verified-index-r1`，`robocasa365-target-atomic-left_wrist-exact_window`，`robocasa365_v3_flat/robocasa365-target-atomic`；T=16，Cosmos3-Edge-Policy-DROID tokenizer
- 正式 No-TTT：DS报告 PID 1202529–1202532 持续运行，world4/GA4/nw8，测试没有触碰

## 0. DS_PRO 声称的结果

**Task1 PASS**：三个真实 terminal partial episode 的 SegmentBatch、逐有效 Consumer payload、RNG before/after 一致；valid_count 分别为9、12、13。

**Task2 PASS**：相同冻结 Requests，经 `NoTTTCpuLoader(workers=1,prefetch=1,persistent=True) → SegmentBatch → MatchedNoTTTWindow.pack → collate_grouped_native_batch`，4个 GA Member 各128个有效 Consumer（共512），positions/payloads/native batch/RNG 消费一致。

Compact0 Dense Video 与 Compact1 stride0/1-byte proxy 的**逻辑 shape + 全零值相同**；物理 Storage、stride 不要求一致。此为 CPU Evidence，**不覆盖真实模型 Loss/Gradient、GPU H2D、真实 DCP Resume 或正式训练环境切换**。

## 1. 复现环境与构造

- Index：`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/datasets/robocasa365-target-atomic-verified-index-r1`
- Cache：`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/datasets/robocasa365-target-atomic-left_wrist-exact_window`
- Source：`/mnt/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic`
- EDGE：`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/models/Cosmos3-Edge-Policy-DROID`
- `build_raw`：构建 `RoboCasaExactWindowCachedDataset(cat,source_reader,contract)`；通过环境变量 `PSM_V3_COMPACT_CACHED_VIDEO=0/1` 选择模式。
- `build_sft`：`ActionTransformPipeline(tokenizer_config=EDGE,cfg_dropout_rate=0.1,max_action_dim=contract.max_action_dim,append_viewpoint_info=True,append_duration_fps_timestamps=True,append_resolution_info=True,append_idle_frames=True,format_prompt_as_json=True)`；Compact1 安装 `CachedGeometryResize(...,raw._canvas_geometry)`。
- `ExactWindowLocalCatalog(sft,ttt_tbptt_steps=16)`，`ExactWindowSegmentProducer(catalog,config_digest='compact_parity_v1')`。
- Task2：`ExactWindowRankPlanner(rank=0,world_size=4,b_stream=8,active_ga=4,seed=0)`，`MatchedNoTTTWindow(_StubModel(local_memory_enabled=False),planner)`，`LoaderProfile(workers=1,prefetch_factor=1,persistent_workers=True,timeout_s=120)`。
- Source: `robocasa_exact_window_local.py` Catalog/Planner/SegmentProducer；`no_ttt_cpu_loader.py` RawRecipe、RawDataset、Parent materialization；`local_memory_grouped.py:40` Native Collate。
- 每个 catalog 的 Request 由**其自身 episode 对象**构造，满足 `producer.prepare` 的对象 identity 检查。

## 2. Task1：真实 Terminal Partial Segment（3 episodes）

| Episode UID | window_count | segment_count | cursor | valid_count | tensor_eq | payload_eq | RNG before | RNG after |
|---|---:|---:|---:|---:|---|---|---|---|
| CloseBlenderLid/episode_000000 | 345 | 22 | 21 | 9 | True | True | True | True |
| CloseBlenderLid/episode_000001 | 396 | 25 | 24 | 12 | True | True | True | True |
| CloseBlenderLid/episode_000002 | 365 | 23 | 22 | 13 | True | True | True | True |

- 均 `training_stream_end=True`，`1<=valid_count<16`。
- SegmentBatch tensor 等价字段：`consumer_visual_summary`、`consumer_valid`、`consumer_step`、`evidence_visual_summary_prev`、`evidence_executed_action_prev`、`evidence_valid`、`evidence_source_step`、`slot_id`。
- 逐有效 Consumer payload 相等字段：`ai_caption/action/action_raw/text_token_ids/sequence_plan/video/video_latent/image_size/cached_latent_required/conditioning_fps/mode/domain_id/viewpoint/episode_index/start_frame/global_row_indices/window_frame_indices/latent_source_frame_indices/cache_corpus_digest/source_binding_digest/task_class/idle_frames/raw_action_dim/action_processing_record`。
- `meta_eq`：episode_id/category/segment_provenance=True；Video 逻辑形状`[3,17,192,320]`、全零，Compact0非proxy、Compact1是proxy。

## 3. Task2：完整 No-TTT CPU 路径（4×128=512）

- `frozen plan equality=True`；`member_counts=[128,128,128,128]`。
- 4个 Member 均：`positions_eq=True`、`rng_consumed_eq=True`、`payload_all=True`、`batch_all=True`、`batch_video_eq=True`。
- `batch_video_proxy0=False`，`batch_video_proxy1=True`，其逻辑 Video shape/value 等价。
- Native Batch字段相等：`_worker_id/action/action_raw/text_token_ids/ai_caption/video/video_latent/image_size/sequence_plan/cached_latent_required/conditioning_fps/mode/domain_id/viewpoint/episode_index/start_frame/global_row_indices/window_frame_indices/latent_source_frame_indices/cache_corpus_digest/source_binding_digest/task_class/idle_frames/raw_action_dim/action_processing_record`；`batch_video_latent_count=128`。

### CFG RNG 比较协议修正（必须保留此执行细节）

初版脚本在同一Python进程对 loader0/loader1 逐 Member 交错执行，先前调用已消耗 Python 全局 RNG；`TextTokenizerTransform` 的 CFG dropout 使用随机抽样（`transform_random.py`）。所以初版 `ai_caption/text_token_ids` 不一致属于**比较起始 RNG 未对齐的协议伪差**。修正为每 Member 在 loader0 开始前 snapshot RNG，loader1 开始前 restore相同 snapshot，并新增 `rng_consumed_eq` 断言；随后全部 payload/text tokens 等价。

当前报告不含原始脚本/JSON，故上述是否在 Member 间正确延续、是否包括完整所需 RNG 域仍需后续 raw evidence 直接检验；不能仅凭报告“PASS”代替独立验证。

### 非基准性质的 Host 时间记录（ms）

| metric | loader0 Dense | loader1 Compact |
|---|---:|---:|
| source_read_ms | 5384.8 | 4901.0 |
| worker_prepare_ms_sum | 2333.2 | 2395.8 |
| raw_wait_host_ms | 239.2 | 1605.7 |
| decode_host_ms | 357.6 | 347.0 |
| transform_host_ms | 3541.1 | 348.6 |
| materialize_host_ms_incl_transform | 3662.8 | 500.7 |
| step_window_host_wall_ms_before_telemetry | 32905.4 | 20145.4 |

以上是同一进程内依次跑两个Loader、单worker的CPU功能验证时序；**不能外推成4GPU完整 Step加速**，各阶段时间也并非互斥/穷举。

## 4. 断言与局限

- DS PASS判据：上述元数据/tensor/payload/RNG/顺序等价，并且Worker启动、队列、Collate流程无异常。
- 未进行GPU、真实模型 Forward/Loss/Gradient、DCP/Checkpoint边界切换。
- 未重跑前一轮四Consumer/Transform benchmark。
- 报告自称原始脚本和JSON已保存至工作树相对路径，**当前远端 GitHub 尚未出现**；这只是 Evidence 持久化缺口，不能当作生产代码缺陷。

## 5. 需要 GPT 审核的下一步

1. 上传/提交确切的 `compact_segment_parity.py` 和 `compact_segment_parity_results.json`，不需要重新跑已通过实验；若有 `compact_segment_parity.log` 同步附上更好。
2. GPT 校验 script 的 RNG snapshot/restore、两分支Consumer与Metadata递归比较、真实Loader/Producer/Planner的精确调用、JSON结果确实覆盖3个partial和4个Member。
3. 此后仅关闭 CPU Evidence Gate；真实模型 Loss/Gradient GPU parity、真实训练Checkpoint切换另行授权。
