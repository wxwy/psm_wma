# PSM-WMA V3 Corrected — Phase 3 Cached-Latent SFT Transport + OmniMoT Cache-Hit Design v1.0

日期：2026-10-05
状态：GPT frozen Phase3 design authority；允许 cx 实现与 CPU/static tests；不授权 ds/GPU/训练/仿真。

## 1. Phase3 目标

Phase1A/1B/2 已正式关闭。

当前已有：

1. cache catalog / exact-window latent reader；
2. cache identity -> flat RoboCasa v3 source binding；
3. official raw12 -> raw15；
4. official state16 -> state15；
5. [state15; 16×raw15] 的 native action contract；
6. H_pred=16 / obs=17 / full manifest VAE contract。

Phase3 只完成：

cache exact window
+ Phase2 action/state/text
    ->
ActionSFT-compatible cache-driven sample
    ->
ActionTransformPipeline
    ->
current PackingDataLoader/collate
    ->
OmniMoT cached vision seam
    ->
native x0 vision latent / FM path

核心验收：

- training 默认读取 offline latent cache；
- cache-hit 时 VAE encode 调用数 = 0；
- 不存在 cache miss -> online VAE fallback；
- Policy 获得的 current/future latent 与指定 cache exact window一一对应；
- future 4 latent仍只由 native FM/noise/loss消费；
- future Local-TTT 的 current z_t authority 冻结为同一个 cached window 的 latent[0]。

Phase3 不实现 Local visual96、Local inner loop 或 grouped TTT。

## 2. Parent authority

- Corrected V3 detailed design v3.0
- Phase0 mapping
- Phase1A closure
- Phase1B closure
- Phase2 closure:
  - formal root 471b7fec4f50296efb3a328735dc2611b900995f
  - formal child ce07cb6f4a3f7792d85b7583ff6c8bda0bfa0cb0
- Phase2 design:
  docs/build/PSM-WMA_V3_phase2_raw15_state15_hpred16_design_v1.1_2026-10-05.md

V2 donor只作为行为参考，不作为实现 authority。

## 3. V2 可继承与必须删除的部分

### 可以继承

V2 exact-window cached path 的正确思想：

- placeholder pixel video保留 ActionTransformPipeline 的 shape/prompt/SequencePlan 行为；
- video_latent承载真正 VAE output；
- model cache-hit绕过在线 VAE；
- cached latent之后继续走 native crop/temporal/noise/loss。

### 禁止继承

V2 model seam 中以下行为禁止进入 Corrected V3：

- verify_cached_latent mismatch 后 fallback online VAE；
- 自动用 online latent替换 cache；
- production path写 mismatch artifact 后继续训练；
- 将 cache miss 解释为可恢复事件。

Corrected V3：
cache/data contract异常 = fail-closed。

## 4. Cache builder preprocessing authority

现有 exact_window_v1 RoboCasa cache builder真实流程已核实：

left RGB + wrist RGB
-> pixel horizontal composite 256x512
-> to_training_uint8
-> VideoResize(resolution=None, keep_aspect_ratio=True)
-> padded training canvas
-> exact 17-frame Wan VAE
-> fp32 latent [5,48,H_lat,W_lat]

因此 cache不是“原始256x512直接VAE”。

对于当前 VIDEO_RES_SIZE_INFO，256x512 composite会按 auto-tier进入 matching padded canvas。
Phase3不得硬编码 cached spatial size；必须由 transformed placeholder的 target canvas和 catalog.latent_shape互相校验。

## 5. Phase3 不修改 generic collator / packer

这是 Phase3 的冻结决策。

Current custom_collate_fn 没有 video_latent special-case；PackingDataLoader 也没有把 video_latent 放入 _MULTI_ITEM_KEYS。Phase3 **不修改这两个 generic tables**，而是明确冻结两层 transport ABI。

### 5.1 Inner PyTorch DataLoader collate ABI

Phase1A 已要求整个 corpus 的 latent_shape 固定，因此 default_collate 会把 sample latent：

video_latent sample = [5,48,H_lat,W_lat]

stack 成：

video_latent inner batch = Tensor[B,5,48,H_lat,W_lat]

### 5.2 PackingDataLoader final model ABI

JointDataLoader._get_next_sample 对普通 Tensor(B,...) 使用 v[i:i+1]，因此单样本 buffer 中是：

Tensor[1,5,48,H_lat,W_lat]

随后 _update_output_batch 对普通 key 以 list 累积，所以最终送给 model 的唯一 Corrected Phase3 ABI 是：

video_latent = list[B]
每项 Tensor[1,5,48,H_lat,W_lat]

这是有意复用 current generic tensor transport，不是 shape accident。

禁止：
- 把 V2 的 video_latent list_collate patch搬回 current collator；
- 把 video_latent加入 _MULTI_ITEM_KEYS；
- dataset 根据 batch_size 猜 ABI；
- model 接受任意多种未冻结嵌套结构。

Formal tests必须分别证明 inner collate ABI 与 PackingDataLoader final ABI。

## 6. 新 cache-driven raw Action dataset

新增 project module，推荐：

cosmos_framework/data/generator/action/datasets/robocasa_exact_window_cached_sft.py

建议包含：

- RoboCasaExactWindowCachedDataset
- get_action_robocasa_exact_window_cached_sft_dataset
- 必要的 frozen sample geometry/helper

不得修改 official RoboCasaLeRobotDataset 来承载 cache-first corpus。

### 6.1 依赖

RoboCasaExactWindowCachedDataset组合：

- RoboCasaExactWindowCacheCatalog
- RoboCasaExactWindowEpisodeReader
- RoboCasaExactWindowSourceReader
- CorrectedRoboCasaPolicyContract
- OfficialRoboCasaPolicyAdapter

cache catalog仍是 membership authority。

### 6.2 __len__ / index

len == catalog.stats.exact_window_count。

顺序严格继承 Phase1B CacheDrivenFlatWindowIndex：
sorted cache episodes + exact start。

source extra episode不得出现。

### 6.3 get_shuffle_blocks

ActionIterableShuffleDataset需要 list[(flat_start,length)]。

Phase3 wrapper必须把 Phase1B 每个 cache episode block转换为连续 flat-index block：
(start,length)。

每个 block只能对应一个 cache episode。
不允许 raw source重新定义 block。

## 7. Raw sample assembly

对 flat index i：

1. Phase1B source_reader.read_at(i)
2. Phase2 adapter.convert(source_window)
3. cache_reader.read_window(key,start)
4. cache_reader.read_identity(key,start)
5. 严格交叉验证 key/start/global rows/digests一致
6. 组装 native Action raw sample

至少输出：

- ai_caption
- video placeholder
- video_latent
- action
- conditioning_fps
- mode
- domain_id
- viewpoint
- additional_view_description
- idle_frames
- task_class
- episode_index
- start_frame
- window_frame_indices
- latent_source_frame_indices
- cache_corpus_digest
- source_binding_digest

### 7.1 action

action = Phase2 action_with_state15
shape [17,15]
float32 finite contiguous。

不得再次转换或normalize。

### 7.2 video_latent

直接来自 Phase1A exact reader：
shape == catalog.latent_shape
当前 contract前缀 [5,48,...]
float32 finite contiguous。

不得复制、重编码或按 floor/nearest读取。

### 7.3 placeholder video

placeholder只是 transform geometry carrier，不是视觉训练 target。

固定 pre-resize geometry必须与 official left_wrist composite一致：

uint8 [3,17,256,512]
全零允许。

它的职责只有：

- VideoResize
- image_size
- prompt resolution/duration metadata
- SequencePlan logical video_length=17
- temporal position pixel-count metadata

model cache-hit不得编码 placeholder。

### 7.4 domain/viewpoint

保持 latest official RoboCasa host：

- domain_id = get_domain_id("robocasa")，当前30
- viewpoint = "concat_view"
- additional_view_description使用 latest RoboCasa left_wrist exact string：
  left half third-person；right half wrist-mounted。

不得把 B1 camera-major metadata带回 active route。

## 8. idle_frames 保持 official prompt parity

latest get_action_robocasa_sft_dataset 默认 append_idle_frames=True。

Phase3 raw dataset因此必须提供 official idle_frames，而不是静默省略。

使用不运行 constructor 的 RoboCasaLeRobotDataset proxy：

- _use_base_action = True
- _base_encoding = "raw"
- _pose_convention = "backward_framewise"
- _fps = 20.0

对 Phase2 action15 [16,15] 调用：

RoboCasaLeRobotDataset._compute_idle_frames(proxy, action15)

该 helper内部继续使用 official action spec / threshold。

禁止 Phase3复制 idle判定数学。

Formal test必须 spy official helper并和 official proxy直接结果一致。

## 9. 原样复用 ActionSFTDataset + ActionTransformPipeline

Raw cache dataset外层直接使用 current：

ActionSFTDataset(raw_dataset, transform, resolution=None)

transform保持 current official implementation。

Corrected transform配置：

- resolution = None
- max_action_dim = 64
- cfg_dropout_rate = current corrected recipe value，默认0.1
- append_viewpoint_info = True
- append_duration_fps_timestamps = True
- append_resolution_info = True
- append_idle_frames = True
- format_prompt_as_json = True
- action_normalizer = None
- mode = wam

text tokenizer config仍是 VLM tokenizer config。
不要把 Phase2 VAE tokenizer config误传给 TextTokenizerTransform。

## 10. Transform 后硬合同

对一个 sample：

### action
- action_raw exact [17,15]
- raw_action_dim = 15
- action padded [17,64]
- first15 exact
- tail zero
- SequencePlan:
  - vision condition [0]
  - action condition [0]

### video
placeholder经同一 VideoResize。
Formal test必须比较：
- transform后的 target canvas H/W
- image_size [target_h,target_w,content_h,content_w]
- cache builder同 geometry规则

### video_latent
ActionTransformPipeline不得修改：
- tensor值
- dtype
- shape
- exact window identity

缺失或错 window一律 fail。

## 11. Collate / Packing transport ABI

Phase3 不改 custom_collate_fn、_MULTI_ITEM_KEYS 或 _update_output_batch。

必须用 current 实现做 formal transport tests：

### inner collate
- B=1 -> Tensor[1,5,48,H,W]
- B=2 -> Tensor[2,5,48,H,W]

### PackingDataLoader sample split
每个 sample 的 video_latent -> Tensor[1,5,48,H,W]

### PackingDataLoader final output
video_latent -> list[B]
每项 exact Tensor[1,5,48,H,W]

要求：
- sample order 与 video/action/sequence_plan order一致；
- fp32/finite；
- latent值不变；
- identity metadata不串样。

model cache-hit seam只消费 **final model ABI**。

## 12. 唯一必要 host-core seam

只允许修改：

cosmos_framework/model/generator/omni_mot_model.py

位置：
get_data_and_condition 的 vision raw-state / VAE encode preparation。

目标是增加一个 generic optional cached vision input：

data_batch["video_latent"]

当 key不存在：
原路径完全不变。

当 key存在：
严格执行 cache-hit。

不修改：
- training_step主流程
- noise
- loss
- packer
- network forward
- tokenizer实现
- VAE implementation

## 13. Cached vision batch validation

cache-hit只接受 PackingDataLoader final ABI：

video_latent 必须是 list/tuple，长度 == batch_size。
每项必须是：
- Tensor rank5
- shape [1,5,48,H_lat,W_lat]
- dtype float32
- finite

并要求：
- num_vision_items_per_sample is None
- num_views_per_vision_item is None
- no enable_per_camera_vae_encoding
- vision_condition_indexes is None
- media stream必须是 video，不支持 image batch
- data_batch必须有 image_size
- no mixed cached/noncached samples in one batch

这是 standard composite single-vision-item **training packed-batch cache ABI**。
其它模式 fail-closed，不 fallback。

## 14. Cached raw_state_vision placeholder handling

cache-hit时不要调用 _normalize_video_databatch_inplace。

原因：
placeholder不参与 VAE；把整段 zero pixels搬到GPU并normalize没有训练意义。

但要构造与 native metadata helper兼容的 raw_state_vision：

每个 video sample：
- tensor rank4 [C,T,H,W]
- unsqueeze -> [1,C,T,H,W]
- 仅验证 T=17 / expected transformed canvas shape
- 可保持 CPU uint8

它供：
- get_vae_pixel_shapes telemetry
- _get_temporal_positions_vision shape metadata

不得成为 model target。

## 15. Cache latent materialization

对 final video_latent list 中每项：

input item：
[1,5,48,H,W]  # packed sample batch1, T,C,H,W

先验证 leading dim exact1，然后：
- squeeze leading sample batch -> [5,48,H,W]
- permute T,C,H,W -> C,T,H,W
- unsqueeze model item batch -> [1,48,5,H,W]
- move to self.tensor_kwargs_fp32 device/dtype
- contiguous

最终 model x0 item exact：
[1,48,5,H,W]

禁止接受额外 singleton/nested维度并 silent squeeze 多次。

## 16. Canvas / image_size / latent shape一致性

cached latent是 builder 对 padded canvas编码的结果。

在 common crop之前验证：

target_h,target_w来自 image_size的前两项。

要求：
H_lat == target_h / spatial_compression_factor
W_lat == target_w / spatial_compression_factor
且 target_h/w能整除 factor。

不匹配 fail。

然后继续调用现有：

_remove_padding_from_latent(x0_tokens_vision, image_size)

这一步必须保留。

它不是二次错误裁剪，而是 online/native training也使用的 post-VAE content crop。

Formal geometry test要以 left_wrist 256x512 placeholder验证：
- placeholder transform canvas
- cached padded latent spatial
- crop后的 content latent spatial
三者严格匹配 builder语义。

## 17. Cache-hit时 VAE必须完全不运行

当 video_latent存在：

禁止调用：
- _encode_vision_x0_tokens
- _encode_vision_item
- tokenizer_vision_gen.encode
- VAE load-balance offload_encode

balance_vae_encode=True也不能触发任何 VAE collective/encode。

Formal tests用 spy/mock证明 encode count=0。

不存在 verify/fallback mode。

## 18. Native downstream保持不变

cached x0构造后继续使用 current native：

- _remove_padding_from_latent
- _get_temporal_positions_vision
- vision timestep/sigma sampling
- SequencePlan
- packing
- action noising
- vision noising
- flow-matching targets/loss
- Local prefix hook（本阶段不提供 prefix）

future four visual latents仍由 native FM path noise+loss。
Phase3不手写 future loss。

## 19. Future Phase4 current z_t authority

Phase3明确冻结：

一个 exact window cache tensor：
Z = [z0,z1,z2,z3,z4]

Policy：
使用完整 Z（经 common crop后的5 latent frames）。

Local-TTT 在 Phase4：
只能从**同一个 exact-window Z 的 current frame z0**派生。

禁止：
- 另一个 visual cache
- B1 dual-camera latent
- online VAE for Local training
- mean/RMS B1 visual96
- future z1..z4进入 Local evidence

Phase3不计算 visual96，只保证 z0单一 authority可追踪。

## 20. B1/current old grouped route处置

本阶段不删除历史文件，但不得让新 cached SFT route import或调用：

- robocasa_latent_evidence.RoboCasaLatentReader
- B1 H5 cache
- separate-camera visual96
- old robocasa_grouped_segment Stage-A payload binder

Current robocasa_grouped_segment.py 中明确拒绝 video_latent 的旧 guard暂时保留历史，不在 Phase3硬改。
Phase4会用新的 corrected grouped producer替换 active Local data path。

因此 Phase3不是“修旧 H3-F producer”，而是先建立正确的 native cached-policy sample。

## 21. Corpus logging接口

Phase3 factory必须暴露 rank0-ready summary，合并已有：

Phase1A：
- cache_root
- manifest SHA
- corpus digest
- task/episode/window/consumer/frame统计

Phase1B：
- source binding digest
- selected episodes / bound windows
- mismatch counters

Phase2：
- H_pred16
- raw15/state15
- full VAE contract

Phase3增加：
- cached_latent_required = true
- online_vae_fallback = false
- placeholder_geometry
- inner_collate_video_latent_abi = Tensor[B,5,48,H,W]
- model_video_latent_abi = list[B] of Tensor[1,5,48,H,W]
- transformed canvas geometry
- model_cache_hit_required = true

正式训练入口 Phase5必须把该 summary打印到 rank0；Phase3先冻结 API/测试。

## 22. 建议实现文件

新增 child project module：

cosmos_framework/data/generator/action/datasets/robocasa_exact_window_cached_sft.py

新增正式 tests：

robocasa_exact_window_cached_sft_test.py

新增 model seam tests，推荐：

cosmos_framework/model/generator/omni_mot_cached_vision_test.py

唯一允许修改 core：

cosmos_framework/model/generator/omni_mot_model.py

不修改：
- joint_dataloader.py
- ActionSFTDataset
- transforms.py
- RoboCasaLeRobotDataset
- tokenizer/VAE
- packing/loss
- old Edge/Nano recipe
- trainer
- inference/server/eval
- old grouped Local files

若 cx认为还必须改其它 core文件，先停并回报GPT。

## 23. Dataset / transform formal tests

至少覆盖：

1. cache membership唯一决定 len；
2. source extra episode不进入；
3. get_shuffle_blocks exact per cache episode；
4. source/policy/cache exact identity一致；
5. wrong key/start/digest fail；
6. placeholder raw shape exact [3,17,256,512] uint8 zero；
7. raw action exact Phase2 [17,15]；
8. domain_id/viewpoint/additional-view metadata official parity；
9. official idle_frames helper spy + parity；
10. transform resolution=None；
11. transform SequencePlan vision/action condition=[0]；
12. action raw15->pad64 exact；
13. placeholder transform canvas与 builder geometry一致；
14. image_size正确；
15. video_latent transform前后 exact value/shape/dtype；
16. inner custom_collate B=1 ABI Tensor[1,5,48,H,W]；
17. inner custom_collate B=2 ABI Tensor[2,5,48,H,W]；
18. PackingDataLoader split后每样本 Tensor[1,5,48,H,W]；
19. PackingDataLoader final model ABI list[B] of Tensor[1,5,48,H,W]；
20. identity metadata不串样；
21. summary corpus/binding/contract字段完整；
22. no import/use B1 latent reader。

## 24. Model cache-hit formal tests

至少覆盖：

1. no video_latent -> native _encode_vision_x0_tokens被调用；
2. valid cached batch -> encode调用0；
3. balance_vae_encode=True仍encode/collective调用0；
4. wrong rank fail；
5. wrong B fail；
6. wrong T!=5 fail；
7. wrong C!=48 fail；
8. wrong dtype fail；
9. nonfinite fail；
10. image_size缺失 fail；
11. image batch fail；
12. per-camera/multi-vision fail；
13. inference vision_condition_indexes非None fail；
14. canvas spatial vs cached latent mismatch fail；
15. cached tensor转换为 [1,48,5,H,W]；
16. common _remove_padding_from_latent确实执行；
17. crop数值/shape正确；
18. temporal-position helper仍能消费placeholder geometry；
19. returned GenerationDataClean batch/vision/action alignment不变；
20. no fallback：任一cache错误直接raise，不调用encoder。

## 25. Combined regressions

cx formal self-test至少：

- Phase1A cache tests
- Phase1B source tests
- Phase2 policy tests
- Phase3 cached SFT tests
- Phase3 cached model tests
- relevant ActionTransform/ActionProcessor tests
- targeted OmniMoT off-mode test

Ruff check / format --check / diff-check。

CPU only。

## 26. Optional real VAE parity，不属于本阶段 source closure

Phase3 synthetic closure后、正式训练前必须再有 read-only asset Gate：

同一真实 exact cache window：
- builder cached latent
vs
- same source composite + same VideoResize + same resolved Wan VAE online encode

比较：
- pre-crop padded latent
- post-crop native training latent
- current z0
- full 5-latent sequence

该 Gate只做 parity evidence，不允许 fallback或重编码 cache。

具体资产路径由训练/数据服务器执行时指定，不写死到代码。

## 27. Phase3 非目标

禁止：
- Local visual96
- LocalEvidenceEncoder改造
- fast W0/Wt
- B_stream/T/GA
- grouped producer
- trainer/DCP
- optimizer selection
- inference/server/eval
- raw15->env12
- executed-action canonicalization
- cache rebuild
- GPU训练/仿真

## 28. Gate / 提交流程

cx：
1. 全文读本设计 + v3.0 + Phase0 + Phase2 closure；
2. root TODO/SESSION认领 exact files；
3. child实现；
4. formal CPU tests + regressions；
5. child commit/push；
6. root Gitlink + TODO/SESSION + Inbox；
7. root commit/push；
8. 不自授批准。

GPT：
fresh source review。
若通过，只授权 ds CPU/static Evidence。

ds：
严格 exact pair执行；
不改代码；
不访问真实训练资产，除非后续收到单独 real-parity Gate。

Phase3 closure后进入 Phase4：

同一 cached z0 -> V2 adaptive_avg_pool2d((1,2)).flatten() visual96
+ executed raw15 history
+ corrected B_stream batched Local-TTT / configurable T。
