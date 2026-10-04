# PSM-WMA V3 Corrected — Phase 3.5 Real Cache vs Online Wan VAE Parity Design v1.1

日期：2026-10-05
状态：GPT frozen design authority；允许 cx 实现 read-only parity probe + synthetic CPU/static tests；不授权真实资产执行、Phase4、训练或仿真。

本文是唯一 Phase3.5 parity authority。它吸收了 earlier parity drafts 中“整 episode decode/compose/resize 后再切 exact window”的正确改进；此前未提交的同类 v1.0 草稿均 superseded。

## 1. 目的

Phase3 已正式关闭，但仍未证明：
已有真实 exact_window_v1 cache latent 与 current latest Cosmos/Wan VAE 对同一 source pixels 的 online exact-window encode 数值一致。

本 Gate 必须在 Phase4 Local-TTT integration 之前 PASS。

只读原则：
- 不修改 source
- 不修改/覆盖 cache
- 不重建 cache
- mismatch 不 fallback
- 不训练
- 不进入 Local-TTT

## 2. Parent authority

Phase3 formal implementation：
- root af7d1b7fb3b85a79df8d7f8edc00e6f24bde5874
- child b6707e2c89fe6078e2a0bb4ff7266205b827825e

Phase3 closure：
docs/collab/chatgpt/reviews/2026-10-05_V3_phase3_closure_af7d1b7f_b6707e2c.md

相关 frozen modules：
- RoboCasaExactWindowCacheCatalog / EpisodeReader
- RoboCasaExactWindowSourceReader
- CorrectedRoboCasaPolicyContract
- current RoboCasaLeRobotDataset
- current VideoResize
- current normalize_uint8_item
- current Wan2pt2VAEInterface
- current OmniMoTModel._remove_padding_from_latent

旧 tools/g0 parity/builder 仅作 historical builder-flow reference；其 vision_vae import 已失效，不能作为 runtime authority。

## 3. 实现位置与 scope

child 新增：
- tools/v3/verify_robocasa_exact_window_real_parity.py
- tools/v3/verify_robocasa_exact_window_real_parity_test.py

Phase3.5 不修改任何 production core。

若 cx 判断必须改 dataset/model/tokenizer/trainer 等 production 文件，必须先停止并回报 GPT。

## 4. CLI

至少支持：
- --cache-root PATH
- --source-root PATH
- --vae-path PATH
- --output-json PATH
- --device cuda[:N]
- --task-class STRING 可重复/可选
- --episode-index INT 可选（与显式 task 配合）
- --starts CSV 可选
- --num-task-classes INT，自动模式默认 1
- --video-backend 可选
- --tolerance-s FLOAT，默认1e-4
- --dry-run
- --max-abs-threshold FLOAT 可选
- --hash-vae 可选，仅计算只读 sha256

禁止硬编码服务器路径或从 manifest historical absolute path替代 runtime args。

## 5. cache/source identity

启动必须构造：
- RoboCasaExactWindowCacheCatalog
- RoboCasaExactWindowEpisodeReader
- RoboCasaExactWindowSourceReader
- CorrectedRoboCasaPolicyContract.from_cache_catalog

任何 Phase1A/1B contract mismatch先 fail，不进入视频/VAE。

每个 selected window必须精确使用：
- ExactWindowEpisodeKey
- start_frame
- global_row_indices[17]
- window_frame_indices[17]
- latent_source_frame_indices[5]

禁止 nearest/floor/remap。

## 6. 默认 window selection

Observational 首轮默认只选 1 个 task class / 1 个 eligible episode，降低真实 VAE 成本。

episode必须 window_count >= 3。

默认 starts：
- first = 0
- middle = floor((window_count-1)/2)
- terminal = window_count-1
- 去重

显式 starts必须逐个验证属于 exact cache。

第一次 observational 完成后，GPT/Owner根据差异分布冻结 threshold。

最终 thresholded Gate 要扩展覆盖至少 3 个不同 underlying task class，各1个 episode × first/mid/terminal，至少 9 个 exact windows（除非某 episode 去重后少于3，则换 eligible episode）。

global start mod4不是本 Gate 的必要条件：exact_window_v1 是每个17帧 window 独立 full encode，不是 streaming/global-grid cache。

## 7. 必须复现原 builder 的 episode-level pixel组织

这是 v1.1 的关键冻结点。

对每个 chosen episode：

1. 从 source data parquet 读取整 episode：
   - index
   - timestamp
   - episode_index
2. stable sort by index；
3. 证明 rows 与 Phase1B bound episode identity一致；
4. left camera按整个 episode timestamps只 decode 一次；
5. wrist camera按整个 episode timestamps只 decode 一次；
6. compose entire episode；
7. float-video -> uint8 entire episode；
8. VideoResize entire episode一次；
9. 最后才按 selected start切 [C,17,H,W]；
10. 每个17-frame window独立 current Wan VAE encode。

原因：原 exact cache builder就是 entire episode decode/compose/resize，再按 start 切17帧独立 encode。逐-window视频 seek会把 decoder/backend差异混入 VAE parity。

Formal test必须证明每个 episode每camera decode调用一次，与 selected window数无关。

## 8. source row/timestamp witness

整 episode source rows必须：
- count == bound episode length
- index连续且等于 bound dataset_from_index..dataset_to_index-1
- episode_index全一致
- selected 17 rows exact等于 cache global_row_indices

timestamps必须：
- finite
- 数量等于 episode frame count
- selected timestamps严格来自上述 exact rows

若 source row/timestamp mismatch，先于 decode/VAE fail。

## 9. camera/video decode authority

camera key authority：
current official robocasa_lerobot_dataset._IMAGE_FEATURES
- left
- wrist

使用：
- source_reader.meta.get_video_file_path
- episode metadata videos/<camera>/from_timestamp
- lerobot.datasets.video_utils.decode_video_frames

每camera整 episode一次 decode。

decoded tensor要求：
- [T,3,256,256]
- floating
- finite
- range [0,1]
- T exact等于 source episode length

video file缺失或 decode frame count错误 fail。

## 10. official pixel composite

禁止 probe自己写 active torch.cat。

constructor-free RoboCasaLeRobotDataset proxy：
- _image_features = current official _IMAGE_FEATURES
- _skip_video_loading = False

调用 current：
RoboCasaLeRobotDataset._compose_left_wrist(proxy, sample)

得到 entire episode：
[T,3,256,512]

Formal test必须 spy helper。

## 11. official float-video -> uint8

继续调用 inherited current：
RoboCasaLeRobotDataset._convert_video(proxy, composite)

得到：
[3,T,256,512] uint8

禁止 production probe复制 *255/permute公式。

Formal test必须 spy helper。

## 12. VideoResize

使用 current：
VideoResize(pad_keys=["video"], keep_aspect_ratio=True)
resolution=None

对 entire episode只调用一次。

记录实际：
- composed size
- transformed tensor shape
- image_size = [target_h,target_w,content_h,content_w]

current expected left_wrist geometry约：
- composite 256x512
- target canvas 192x320
- content 160x320
但工具必须从实际 result校验，不只靠硬编码。

要求：
- T不变
- target H/W能被 spatial factor整除
- cache latent H/W == target H/W / spatial factor

## 13. VAE resolved contract

使用同一个 catalog：
CorrectedRoboCasaPolicyContract.from_cache_catalog(catalog)

candidate从 current fixed EDGE_MODEL_CONFIG tokenizer deep copy。

通过 contract.resolve_tokenizer_config(candidate) 冻结：
- full manifest encode_exact_durations
- manifest-compatible encode_chunk_frames
- spatial/temporal compression factors
- current other tokenizer fields

runtime只允许覆盖 asset locator：
- bucket_name = ""
- vae_path = --vae-path

不得改变 exact durations/chunk frames来迁就 current code。

实例化 current：
Wan2pt2VAEInterface

要求：
- causal normal full encode
- use_streaming_encode=False
- no cached encoder
- model eval
- torch.inference_mode()
- torch.backends.cudnn.benchmark=False（manifest builder provenance也是 false）

报告 full resolved contract。

## 14. exact online encode path

selected resized window：
uint8 [3,17,H,W]

1. unsqueeze -> [1,3,17,H,W]
2. current normalize_uint8_item(..., fp32 device kwargs)
3. tokenizer.encode
4. contiguous().float()
5. online model layout [1,48,5,H/16,W/16]
6. comparison layout [5,48,H/16,W/16] via squeeze+permute

必须 exact shape == catalog.latent_shape。

禁止：
- old vision_vae
- streaming encode
- B1 endpoint
- separate-camera VAE

## 15. pre-crop comparison

cache reader：
fp32 [5,48,H,W]

online：
fp32 [5,48,H,W]

结构先验证：
- exact shape
- fp32
- finite

per window metrics：
- exact_equal
- max_abs
- mean_abs
- rmse
- finite
- numel
- per temporal latent index 0..4：max_abs/mean_abs/rmse

aggregate：
- global max_abs
- global mean_abs
- worst task/episode/start
- worst temporal index

不以 max_rel 作为 Gate requirement，避免 near-zero denominator造成无意义放大；可选报告但不用于 PASS。

## 16. native post-crop comparison

禁止自己写 crop。

将 cache/online各转 model layout：
[1,48,5,H,W]

构造 minimal OmniMoT-compatible proxy，仅提供：
tokenizer_vision_gen.spatial_compression_factor

直接调用：
OmniMoTModel._remove_padding_from_latent

使用同一个 VideoResize image_size。

比较 cropped full sequence：
- shape
- max_abs
- mean_abs
- rmse

## 17. current z0 comparison

从 post-crop latent temporal index0取：
[48,Hc,Wc]

输出：
- exact_equal
- max_abs
- mean_abs
- rmse

该 z0 是 Phase4 Local visual唯一允许的 current latent authority。

## 18. dry-run

--dry-run：
- 不实例化 Wan tokenizer
- 不加载 VAE
- 不要求 CUDA
- 完成：
  - catalog/source contract
  - selection
  - full episode row/timestamp
  - video file path存在性
  - resolved VAE config
  - expected geometry/latent shape静态验证
- 可不真正 decode视频

status：
DRY_RUN_PASS

任何 identity/path/contract failure => nonzero。

正式真实 Gate必须 dry-run先PASS。

## 19. observational first run

无 --max-abs-threshold：

结构/identity/finite全部正确后输出：
- status = OBSERVATIONAL_NO_THRESHOLD
- parity_gate_pass = null
- exit 0

数值差异不自动判 PASS/FAIL。

原因：真实 cache可能来自较早执行环境；阈值必须基于真实 Evidence，而不是继承历史 R06/B1 的1e-5/1e-6。

## 20. thresholded Gate

GPT/Owner根据 observational Evidence冻结 X。

第二轮：
--max-abs-threshold X

每个 selected window要求：
- pre-crop max_abs <= X
- post-crop max_abs <= X
- z0 max_abs <= X
- structural checks全部PASS

任一超限：
status FAIL，exit nonzero。

全部通过且最终覆盖>=3 task classes / >=9 windows：
status PASS
parity_gate_pass=true

工具不得自动拟合/提高 tolerance。

## 21. JSON Evidence

schema：
robocasa_exact_window_real_vae_parity_v1

至少记录：

authority：
- cache manifest sha256
- corpus digest
- source binding digest
- runtime source root
- runtime VAE path（display only）
- optional VAE sha256
- current tokenizer class
- full resolved VAE contract
- torch/cuda/device info
- video backend
- cudnn benchmark
- no_fallback=true
- read_only=true

selection：
- task class
- episode index
- starts
- global row witnesses

geometry：
- camera keys
- episode frame count
- composite shape
- resized shape
- image_size
- cached padded latent shape
- cropped shape

metrics：
- per window pre-crop
- temporal[0..4]
- post-crop
- z0
- aggregate worst

gate：
- dry_run
- threshold或null
- status
- parity_gate_pass true/false/null

不嵌入大 tensor。

## 22. read-only filesystem contract

probe唯一允许写：
--output-json

不得：
- torch.save到cache/source
- 写manifest
- 写episode payload
- rename/move asset
- 写online latent debug file

如未来需要debug tensor，另开 Gate。

## 23. CPU/static formal tests

不加载真实VAE/GPU，使用 fake decoder/tokenizer/injection。

至少覆盖：

1. default first/mid/terminal selection；
2. explicit invalid start fail；
3. final coverage validator要求3 task / >=9 windows；
4. entire-episode row/index/timestamp exact；
5. global witness mismatch fail；
6. each episode each camera decode exactly once；
7. official _compose_left_wrist spy；
8. official _convert_video spy；
9. VideoResize entire episode once；
10. T保持；
11. latent/canvas spatial geometry fail-closed；
12. Phase2 full exact-duration list传给 tokenizer config；
13. runtime只覆盖 vae locator；
14. normalize_uint8_item helper被调用；
15. fake tokenizer encode count == selected windows；
16. no streaming/separate-camera path；
17. online model/cache layout conversion正确；
18. pre-crop metrics exact/controlled-diff；
19. temporal五帧 metrics；
20. official _remove_padding_from_latent spy；
21. post-crop metrics；
22. z0 metrics；
23. dry-run不构造 tokenizer、不encode；
24. no-threshold observational + pass null；
25. threshold PASS；
26. threshold FAIL；
27. nonfinite/shape/dtype fail；
28. report schema/no tensor payload；
29. no old vision_vae import；
30. no B1 import；
31. output-json以外无write side effect；
32. relevant Phase1A/1B/2/3 tests不回归。

## 24. cx self-test

child：
- parity tool test
- relevant Phase1A cache/source/policy tests
- Phase3 cached SFT/model cached vision tests
- Ruff check/format parity files
- py_compile parity tool
- git diff --check
- exact scope必须仅两新 tool files

不运行真实 VAE。

## 25. 提交流程

cx：
1. 先全文读本设计；
2. root TODO/SESSION认领；
3. child只新增两 parity files；
4. CPU/static self-test；
5. child commit/push v3-local-ttt；
6. root更新Gitlink/TODO/SESSION/Inbox；
7. root commit/push V3；
8. 不自授批准。

GPT：
fresh source review。
通过后先只授权 ds dry-run。

ds：
- dry-run exact pair
- GPT审核
- observational VAE run
- GPT/Owner冻结 threshold
- thresholded final run

Phase4只有 REAL_PARITY_PASS 后才允许开始。